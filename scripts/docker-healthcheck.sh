#!/bin/bash

# dev-v4.4.0

#####
# v4.4.0 - FIXED: Lock file cleanup only removes OLD versions, not current
#####

# Stored at: /mediacms/scripts/

set -e

# ═══════════════════════════════════════════════════════════
# CONFIGURATION - UPDATE THESE WHEN CHANGING BEHAVIOR
# ═══════════════════════════════════════════════════════════
SCRIPT_VERSION="4.4"
NGINX_CONFIG_VERSION="1.0"  # Increment to force nginx reconfiguration
ENCODING_PROFILES_VERSION="1.0"  # Increment to force profile reconfiguration
ENCODING_PROFILES_TO_ACTIVATE=("h264-480" "preview")  # Change this array to modify profiles

# File paths
CONF=/etc/nginx/sites-enabled/default
NGINX_LOCK_FILE="/tmp/nginx-fixes-v${NGINX_CONFIG_VERSION}.lock"
ENCODING_LOCK_FILE="/tmp/encoding-profiles-v${ENCODING_PROFILES_VERSION}.lock"
LOG_FILE=/var/log/mediacms-healthcheck.log

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════════"
log "MediaCMS Healthcheck v${SCRIPT_VERSION} Starting"
log "═══════════════════════════════════════════════"

# Wait for nginx process to start
log "Waiting for nginx to start..."
timeout=90
counter=0
while ! pgrep nginx > /dev/null; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        log "❌ ERROR: Nginx did not start within ${timeout}s"
        exit 1
    fi
done
log "✅ Nginx process found after ${counter}s"

# Wait for config file to exist
log "Waiting for nginx config file..."
counter=0
while [ ! -f "$CONF" ]; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge 30 ]; then
        log "⚠️ WARNING: Config file not found after 30s, skipping nginx fixes"
        exit 0
    fi
done
log "✅ Nginx config file exists"

# ═══════════════════════════════════════════════════════════
# NGINX CONFIGURATION FIXES
# ═══════════════════════════════════════════════════════════
if [ ! -f "$NGINX_LOCK_FILE" ]; then
    log "🔧 Applying nginx configuration (version ${NGINX_CONFIG_VERSION})..."
    
    # Clean up OLD version lock files (but not current version)
    for old_lock in /tmp/nginx-fixes-v*.lock; do
        if [ -f "$old_lock" ] && [ "$old_lock" != "$NGINX_LOCK_FILE" ]; then
            rm -f "$old_lock"
            log "   Removed old lock: $(basename $old_lock)"
        fi
    done
    # Also remove old non-versioned lock
    if [ -f "/tmp/nginx-fixes-applied.lock" ]; then
        rm -f /tmp/nginx-fixes-applied.lock
        log "   Removed legacy lock file"
    fi
    
    # Backup original config (only once)
    if [ ! -f "${CONF}.original" ]; then
        cp "$CONF" "${CONF}.original"
        log "   Backup created: ${CONF}.original"
    fi
    
    # Apply new configuration
    cat > "$CONF" << 'NGINX_EOF'
server {
    listen 80;
    client_max_body_size 10G;
    client_body_timeout 3600s;
    keepalive_timeout 600s;
    uwsgi_read_timeout 3600s;
    uwsgi_send_timeout 3600s;
    uwsgi_connect_timeout 300s;
    gzip on;
    access_log /var/log/nginx/mediacms.io.access.log;
    error_log  /var/log/nginx/mediacms.io.error.log  warn;

    location /static {
        alias /home/mediacms.io/mediacms/static;
    }

    location /media/original {
        alias /home/mediacms.io/mediacms/media_files/original;
    }

    location /media {
        alias /home/mediacms.io/mediacms/media_files;
    }

    location /fu/upload/ {
        uwsgi_read_timeout 7200s;
        uwsgi_send_timeout 7200s;
        uwsgi_connect_timeout 300s;
        include /etc/nginx/sites-enabled/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }

    location / {
        include /etc/nginx/sites-enabled/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }
}
NGINX_EOF

    # Test configuration
    if nginx -t 2>&1 | grep -q "successful"; then
        nginx -s reload 2>/dev/null || true
        touch "$NGINX_LOCK_FILE"
        log "✅ Nginx config v${NGINX_CONFIG_VERSION} applied and reloaded"
    else
        log "❌ ERROR: Nginx config test failed, restoring backup"
        cp "${CONF}.original" "$CONF"
        nginx -t 2>&1 | tee -a "$LOG_FILE"
    fi
else
    log "⏭️  Nginx already configured (v${NGINX_CONFIG_VERSION})"
fi

# ═══════════════════════════════════════════════════════════
# ENCODING PROFILES CONFIGURATION
# ═══════════════════════════════════════════════════════════
if [ ! -f "$ENCODING_LOCK_FILE" ]; then
    log "🔧 Configuring encoding profiles (version ${ENCODING_PROFILES_VERSION})..."
    log "   Target profiles: ${ENCODING_PROFILES_TO_ACTIVATE[*]}"
    
    # Clean up OLD version lock files (but not current version)
    for old_lock in /tmp/encoding-profiles-v*.lock; do
        if [ -f "$old_lock" ] && [ "$old_lock" != "$ENCODING_LOCK_FILE" ]; then
            rm -f "$old_lock"
            log "   Removed old lock: $(basename $old_lock)"
        fi
    done
    # Also remove old non-versioned lock
    if [ -f "/tmp/encoding-profiles-configured.lock" ]; then
        rm -f /tmp/encoding-profiles-configured.lock
        log "   Removed legacy lock file"
    fi
    
    # Wait for Django to be fully ready
    log "   Waiting for Django initialization..."
    counter=0
    max_wait=180  # 3 minutes
    
    while [ $counter -lt $max_wait ]; do
        if python manage.py shell -c "from files.models import EncodeProfile; import sys; sys.exit(0)" 2>/dev/null; then
            log "   ✅ Django ORM ready after ${counter}s"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        
        # Progress indicator every 20 seconds
        if [ $((counter % 20)) -eq 0 ]; then
            log "   ⏳ Still waiting for Django... (${counter}s / ${max_wait}s)"
        fi
    done
    
    if [ $counter -ge $max_wait ]; then
        log "⚠️ WARNING: Django not ready after ${max_wait}s, encoding profile config will retry on next restart"
        exit 0  # Don't fail healthcheck, just skip encoding config
    fi
    
    # Build Python list from bash array
    PROFILES_LIST=$(printf "'%s'," "${ENCODING_PROFILES_TO_ACTIVATE[@]}" | sed 's/,$//')
    
    # Configure encoding profiles
    log "   Running encoding profile configuration..."
    if python manage.py shell -c "
from files.models import EncodeProfile
try:
    # Deactivate all profiles first
    total_profiles = EncodeProfile.objects.count()
    EncodeProfile.objects.all().update(active=False)
    
    # Activate target profiles
    target_profiles = [${PROFILES_LIST}]
    activated = EncodeProfile.objects.filter(name__in=target_profiles).update(active=True)
    
    print(f'✅ Encoding profiles configured successfully')
    print(f'   Total profiles: {total_profiles}')
    print(f'   Activated: {activated} profiles ({', '.join(target_profiles)})')
    
    import sys
    sys.exit(0)
except Exception as e:
    print(f'❌ ERROR: {e}')
    import sys
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"; then
        touch "$ENCODING_LOCK_FILE"
        log "✅ Encoding profiles v${ENCODING_PROFILES_VERSION} configured"
    else
        log "⚠️ WARNING: Encoding profile configuration failed (will retry on next restart)"
    fi
else
    log "⏭️  Encoding profiles already configured (v${ENCODING_PROFILES_VERSION})"
fi

# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════
log "🏥 Running health check..."

if pgrep nginx > /dev/null && pgrep uwsgi > /dev/null; then
    log "✅ Health check PASSED: nginx + uwsgi running"
    log "═══════════════════════════════════════════════"
    exit 0
else
    log "❌ Health check FAILED: Missing processes"
    log "   nginx: $(pgrep nginx > /dev/null && echo 'running' || echo 'NOT RUNNING')"
    log "   uwsgi: $(pgrep uwsgi > /dev/null && echo 'running' || echo 'NOT RUNNING')"
    log "═══════════════════════════════════════════════"
    exit 1
fi
