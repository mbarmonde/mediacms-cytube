#!/bin/bash

# dev-v5.3.0

#####
# CHANGELOG:
# v5.3.0 - Added profile verification with self-healing
#        - Deactivates ALL profiles before activating target ones
#        - Checks profile correctness even when lock file exists
#        - Auto-reconfigures if profile mismatch detected
# v5.2.0 - CORS removal now runs on EVERY healthcheck (not just first time)
#        - Ensures CORS headers stay removed even if config gets reverted
# v5.1.0 - Added nginx CORS header removal
# v5.0.0 - Removed nginx configuration section
#####

set -e

SCRIPT_VERSION="5.3.0"
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
# ENCODING PROFILES - WITH VERIFICATION & SELF-HEALING
# ═══════════════════════════════════════════════════════════

should_configure_profiles() {
    # Returns 0 (true) if profiles need configuration, 1 (false) if they're correct
    
    # If no lock file exists, definitely need to configure
    if [ ! -f "$ENCODING_LOCK_FILE" ]; then
        log "🔍 No lock file found, will configure profiles"
        return 0
    fi
    
    # Lock file exists - verify profiles are still correct
    log "🔍 Verifying encoding profile configuration..."
    
    # Wait briefly for Django to be ready (shorter timeout for verification)
    counter=0
    max_wait=30
    while [ $counter -lt $max_wait ]; do
        if python manage.py shell -c "from files.models import EncodeProfile; import sys; sys.exit(0)" 2>/dev/null; then
            break
        fi
        sleep 1
        counter=$((counter + 1))
    done
    
    if [ $counter -ge $max_wait ]; then
        log "⚠️  Django not ready for verification, skipping check"
        return 1  # Assume correct if we can't verify
    fi
    
    # Build profile list for query
    PROFILES_LIST=$(printf "'%s'," "${ENCODING_PROFILES_TO_ACTIVATE[@]}" | sed 's/,$//')
    
    # Count how many of our target profiles are active
    ACTIVE_COUNT=$(python manage.py shell -c "
from files.models import EncodeProfile
print(EncodeProfile.objects.filter(active=True, name__in=[${PROFILES_LIST}]).count())
" 2>/dev/null || echo "0")
    
    # Count total active profiles (should match expected count)
    TOTAL_ACTIVE=$(python manage.py shell -c "
from files.models import EncodeProfile
print(EncodeProfile.objects.filter(active=True).count())
" 2>/dev/null || echo "0")
    
    EXPECTED_COUNT=${#ENCODING_PROFILES_TO_ACTIVATE[@]}
    
    # Check if configuration is correct
    if [ "$ACTIVE_COUNT" != "$EXPECTED_COUNT" ] || [ "$TOTAL_ACTIVE" != "$EXPECTED_COUNT" ]; then
        log "⚠️  Profile mismatch detected!"
        log "    Expected: $EXPECTED_COUNT active profiles"
        log "    Target profiles active: $ACTIVE_COUNT"
        log "    Total profiles active: $TOTAL_ACTIVE"
        log "🔧 Will reconfigure profiles..."
        
        # Remove lock file to force reconfiguration
        rm -f "$ENCODING_LOCK_FILE"
        return 0  # Need to configure
    fi
    
    log "✅ Profile verification passed ($EXPECTED_COUNT profiles correct)"
    return 1  # Profiles are correct, skip configuration
}

if should_configure_profiles; then
    log "🔧 Configuring encoding profiles (v${ENCODING_PROFILES_VERSION})..."
    
    # Remove old version lock files
    find /tmp -maxdepth 1 -name "encoding-profiles-v*.lock" -not -name "$(basename "$ENCODING_LOCK_FILE")" -delete 2>/dev/null
    
    # Wait for Django to be ready
    counter=0
    max_wait=180
    log "⏳ Waiting for Django ORM..."
    while [ $counter -lt $max_wait ]; do
        if python manage.py shell -c "from files.models import EncodeProfile; import sys; sys.exit(0)" 2>/dev/null; then
            log "✅ Django ready (${counter}s)"
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done

    if [ $counter -ge $max_wait ]; then
        log "⚠️  Django timeout after ${max_wait}s"
        exit 0
    fi

    # Build profile list for SQL query
    PROFILES_LIST=$(printf "'%s'," "${ENCODING_PROFILES_TO_ACTIVATE[@]}" | sed 's/,$//')

    log "📝 Applying profile configuration..."
    if python manage.py shell -c "
from files.models import EncodeProfile

# Step 1: Deactivate ALL profiles for clean state
total_profiles = EncodeProfile.objects.count()
EncodeProfile.objects.all().update(active=False)
print(f'   Deactivated all {total_profiles} profiles')

# Step 2: Activate only specified profiles
activated = EncodeProfile.objects.filter(name__in=[${PROFILES_LIST}]).update(active=True)
print(f'   Activated {activated} target profiles')

# Step 3: Verify and list active profiles
active_profiles = EncodeProfile.objects.filter(active=True).order_by('name')
print(f'   ✅ Configuration complete!')
print(f'   Active profiles:')
for p in active_profiles:
    res = f'{p.resolution}p' if p.resolution else 'N/A'
    print(f'      - {p.name} ({res})')
" 2>&1 | tee -a "$LOG_FILE"; then
        touch "$ENCODING_LOCK_FILE"
        log "✅ Encoding profiles configured and locked (v${ENCODING_PROFILES_VERSION})"
    else
        log "❌ ERROR: Profile configuration failed"
    fi
else
    log "⏭️  Encoding profiles already configured (v${ENCODING_PROFILES_VERSION})"
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
