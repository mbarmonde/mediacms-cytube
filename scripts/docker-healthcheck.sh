#!/bin/bash

# dev-v5.2.0

#####
# CHANGELOG:
# v5.2.0 - CORS removal now runs on EVERY healthcheck (not just first time)
#        - Ensures CORS headers stay removed even if config gets reverted
# v5.1.0 - Added nginx CORS header removal
# v5.0.0 - Removed nginx configuration section
#####

set -e

SCRIPT_VERSION="5.2.0"
ENCODING_PROFILES_VERSION="3.0"

ENCODING_PROFILES_TO_ACTIVATE=(
    "preview"
    "h264-480"
    "h264-720"
    "h264-1080"
)

NGINX_CONF="/etc/nginx/sites-enabled/default"
ENCODING_LOCK_FILE="/tmp/encoding-profiles-v${ENCODING_PROFILES_VERSION}.lock"
LOG_FILE="/var/log/mediacms-healthcheck.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "════════════════════════════════════════════════════════"
log "MediaCMS Healthcheck v${SCRIPT_VERSION} Starting"
log "════════════════════════════════════════════════════════"

# Wait for nginx
log "⏳ Waiting for nginx..."
timeout=90
counter=0
while ! pgrep nginx > /dev/null; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        log "❌ ERROR: Nginx timeout"
        exit 1
    fi
done
log "✅ Nginx started (${counter}s)"

# ═══════════════════════════════════════════════════════════
# CORS REMOVAL - RUNS EVERY TIME
# ═══════════════════════════════════════════════════════════

if [ -f "$NGINX_CONF" ]; then
    # Check if CORS headers exist
    if grep -q "add_header.*Access-Control" "$NGINX_CONF"; then
        log "🔧 Removing CORS headers from nginx..."

        # Backup (only once)
        if [ ! -f "${NGINX_CONF}.cors-backup" ]; then
            cp "$NGINX_CONF" "${NGINX_CONF}.cors-backup"
        fi

        # Remove CORS headers
        sed -i "/add_header.*Access-Control/d" "$NGINX_CONF"

        # Reload
        if nginx -t 2>&1 | grep -q "successful"; then
            nginx -s reload 2>/dev/null || true
            log "✅ CORS headers removed, nginx reloaded"
        else
            log "❌ ERROR: Nginx config test failed"
        fi
    else
        log "✅ CORS headers already clean"
    fi
fi

# ═══════════════════════════════════════════════════════════
# ENCODING PROFILES
# ═══════════════════════════════════════════════════════════

if [ ! -f "$ENCODING_LOCK_FILE" ]; then
    log "🔧 Configuring encoding profiles (v${ENCODING_PROFILES_VERSION})..."

    find /tmp -maxdepth 1 -name "encoding-profiles-v*.lock" -not -name "$(basename "$ENCODING_LOCK_FILE")" -delete 2>/dev/null

    counter=0
    max_wait=180
    while [ $counter -lt $max_wait ]; do
        if python manage.py shell -c "from files.models import EncodeProfile; import sys; sys.exit(0)" 2>/dev/null; then
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done

    if [ $counter -ge $max_wait ]; then
        log "⚠️  Django timeout"
        exit 0
    fi

    PROFILES_LIST=$(printf "'%s'," "${ENCODING_PROFILES_TO_ACTIVATE[@]}" | sed 's/,$//')

    if python manage.py shell -c "
from files.models import EncodeProfile
EncodeProfile.objects.all().update(active=False)
EncodeProfile.objects.filter(name__in=[${PROFILES_LIST}]).update(active=True)
print('✅ Profiles configured')
" 2>&1 | tee -a "$LOG_FILE"; then
        touch "$ENCODING_LOCK_FILE"
    fi
else
    log "⏭️  Encoding profiles configured"
fi

# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════

if pgrep nginx > /dev/null && pgrep uwsgi > /dev/null; then
    log "✅ Health check PASSED"
    log "════════════════════════════════════════════════════════"
    exit 0
else
    log "❌ Health check FAILED"
    exit 1
fi