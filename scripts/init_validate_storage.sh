#!/bin/bash

# dev-v0.1.1

#####
# v0.1.1 - changed all EIGHT_TB_PATH references to EBS_PATH, and all 8TB to EBS references
# MediaCMS Storage Setup and Validation Script
# Usage: ./scripts/setup_storage.sh [--init|--validate|--full]
#   --init      : Initialize EBS structure only
#   --validate  : Validate existing structure only
#   --full      : Initialize AND validate (default)
#####

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
EBS_PATH="/mnt/ebs/mediacms_media"
MEDIACMS_ROOT="/mediacms"
OLD_MEDIA_FILES="$MEDIACMS_ROOT/media_files.old.20260125"

# Parse arguments
MODE="full"
if [ "$1" == "--init" ]; then
    MODE="init"
elif [ "$1" == "--validate" ]; then
    MODE="validate"
elif [ "$1" == "--full" ] || [ -z "$1" ]; then
    MODE="full"
else
    echo "Usage: $0 [--init|--validate|--full]"
    exit 1
fi

#═══════════════════════════════════════════════════════════════════
# INITIALIZATION SECTION
#═══════════════════════════════════════════════════════════════════

initialize_storage() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}MediaCMS EBS Storage Initialization${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Step 1: Stop services
    echo -e "${YELLOW}[1/7]${NC} Stopping Docker services..."
    cd "$MEDIACMS_ROOT"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
    echo ""
    
    # Step 2: Create directory structure
    echo -e "${YELLOW}[2/7]${NC} Creating directory structure on EBS..."
    mkdir -p "$EBS_PATH"/{original,hls,thumbnails,cytube_manifests,userlogos,encodings}
    
    if [ -d "$EBS_PATH/original" ]; then
        echo -e "${GREEN}✅ Directory structure created${NC}"
        echo "   Created: original/, hls/, thumbnails/, cytube_manifests/, userlogos/, encodings/"
    else
        echo -e "${RED}❌ Failed to create directories${NC}"
        exit 1
    fi
    echo ""
    
    # Step 3: Set ownership
    echo -e "${YELLOW}[3/7]${NC} Setting ownership (uid:gid 1000:1000)..."
    sudo chown -R 1000:1000 "$EBS_PATH/"
    
    OWNER=$(stat -c '%u:%g' "$EBS_PATH")
    if [ "$OWNER" == "1000:1000" ]; then
        echo -e "${GREEN}✅ Ownership set correctly${NC}"
    else
        echo -e "${YELLOW}⚠️  Ownership is $OWNER (expected 1000:1000)${NC}"
    fi
    echo ""
    
    # Step 4: Copy old media files if they exist
    echo -e "${YELLOW}[4/7]${NC} Checking for old media files..."
    if [ -d "$OLD_MEDIA_FILES" ]; then
        echo "   Found: $OLD_MEDIA_FILES"
        echo "   Starting rsync (this may take a while)..."
        rsync -avh --progress "$OLD_MEDIA_FILES/" "$EBS_PATH/"
        echo -e "${GREEN}✅ Copy complete${NC}"
    else
        echo -e "${YELLOW}⚠️  No old media files found at $OLD_MEDIA_FILES${NC}"
        echo "   Skipping copy step"
    fi
    echo ""
    
    # Step 5: Create placeholder media_files directory
    echo -e "${YELLOW}[5/7]${NC} Setting up host-side placeholder..."
    if [ -d "$MEDIACMS_ROOT/media_files" ]; then
        # Check if it's the old directory
        if [ -n "$(ls -A $MEDIACMS_ROOT/media_files 2>/dev/null)" ] && [ ! -d "$OLD_MEDIA_FILES" ]; then
            echo "   Moving existing media_files to backup..."
            mv "$MEDIACMS_ROOT/media_files" "$MEDIACMS_ROOT/media_files.old.$(date +%Y%m%d_%H%M%S)"
        else
            rm -rf "$MEDIACMS_ROOT/media_files"
        fi
    fi
    
    mkdir -p "$MEDIACMS_ROOT/media_files"
    echo -e "${GREEN}✅ Placeholder directory created${NC}"
    echo ""
    
    # Step 6: Setup static files
    echo -e "${YELLOW}[6/7]${NC} Setting up static files..."
    mkdir -p "$MEDIACMS_ROOT/static/js"
    
    # Create default user logo if missing
    if [ ! -f "$EBS_PATH/userlogos/user.jpg" ]; then
        echo "   Creating default user logo..."
        mkdir -p "$EBS_PATH/userlogos"
        wget -q -O "$EBS_PATH/userlogos/user.jpg" \
            "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y" 2>/dev/null || \
            echo "   (wget failed, skipping default logo)"
    fi
    echo -e "${GREEN}✅ Static files configured${NC}"
    echo ""
    
    # Step 7: Display structure
    echo -e "${YELLOW}[7/7]${NC} Verifying created structure..."
    echo "   EBS directory contents:"
    ls -lah "$EBS_PATH/" | tail -n +4 | head -10
    echo ""
    
    # Calculate size
    TOTAL_SIZE=$(du -sh "$EBS_PATH" 2>/dev/null | awk '{print $1}')
    echo "   Total size: $TOTAL_SIZE"
    echo ""
    
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Initialization Complete${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

#═══════════════════════════════════════════════════════════════════
# VALIDATION SECTION
#═══════════════════════════════════════════════════════════════════

validate_storage() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}MediaCMS Structure Validation${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Check if services are running
    SERVICES_RUNNING=false
    if docker ps | grep -q media_cms; then
        SERVICES_RUNNING=true
    fi
    
    # Section 1: Host System Paths
    echo -e "${YELLOW}1. Host System Paths${NC}"
    echo "--------------------"
    
    echo -n "EBS mount exists: "
    if [ -d "$EBS_PATH" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -n "EBS has content: "
    if [ "$(ls -A $EBS_PATH 2>/dev/null)" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -n "Host media_files is empty placeholder: "
    if [ -d "$MEDIACMS_ROOT/media_files" ] && [ -z "$(ls -A $MEDIACMS_ROOT/media_files 2>/dev/null)" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️${NC}"
    fi
    
    echo -n "Ownership is correct (1000:1000): "
    OWNER=$(stat -c '%u:%g' "$EBS_PATH" 2>/dev/null)
    if [ "$OWNER" == "1000:1000" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️ (current: $OWNER)${NC}"
    fi
    echo ""
    
    # Section 2: Container Paths (only if services running)
    echo -e "${YELLOW}2. Container Paths${NC}"
    echo "------------------"
    
    if [ "$SERVICES_RUNNING" = true ]; then
        docker exec media_cms bash -c "
        echo -n 'media_files mounted: '
        mountpoint -q /home/mediacms.io/mediacms/media_files && echo -e '${GREEN}✅${NC}' || echo -e '${RED}❌${NC}'
        
        echo -n 'media_files has content: '
        [ \"\$(ls -A /home/mediacms.io/mediacms/media_files)\" ] && echo -e '${GREEN}✅${NC}' || echo -e '${RED}❌${NC}'
        
        echo -n 'HLS directory exists: '
        [ -d /home/mediacms.io/mediacms/media_files/hls ] && echo -e '${GREEN}✅${NC}' || echo -e '${YELLOW}⚠️${NC}'
        
        echo -n 'Original files directory exists: '
        [ -d /home/mediacms.io/mediacms/media_files/original ] && echo -e '${GREEN}✅${NC}' || echo -e '${RED}❌${NC}'
        
        echo -n 'Thumbnails directory exists: '
        [ -d /home/mediacms.io/mediacms/media_files/thumbnails ] && echo -e '${GREEN}✅${NC}' || echo -e '${RED}❌${NC}'
        
        echo -n 'CyTube manifests directory exists: '
        [ -d /home/mediacms.io/mediacms/media_files/cytube_manifests ] && echo -e '${GREEN}✅${NC}' || echo -e '${YELLOW}⚠️${NC}'
        "
    else
        echo -e "${YELLOW}⚠️  Services not running - skipping container checks${NC}"
        echo "   Run: docker-compose up -d"
    fi
    echo ""
    
    # Section 3: Required Files
    echo -e "${YELLOW}3. Required Files${NC}"
    echo "-----------------"
    
    echo -n "userlogos directory exists: "
    if [ -d "$EBS_PATH/userlogos" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -n "user.jpg exists: "
    if [ -f "$EBS_PATH/userlogos/user.jpg" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️${NC}"
    fi
    
    if [ "$SERVICES_RUNNING" = true ]; then
        echo -n "cytube-export.js accessible: "
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://dev.420grindhouseserver.com/static/js/cytube-export.js 2>/dev/null)
        if [ "$HTTP_CODE" == "200" ]; then
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${RED}❌ (HTTP $HTTP_CODE)${NC}"
        fi
    fi
    echo ""
    
    # Section 4: Django Configuration (only if services running)
    if [ "$SERVICES_RUNNING" = true ]; then
        echo -e "${YELLOW}4. Django Configuration${NC}"
        echo "-----------------------"
        docker exec media_cms python manage.py shell -c "
from django.conf import settings
print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')
print(f'MEDIA_URL: {settings.MEDIA_URL}')
print(f'STATIC_URL: {settings.STATIC_URL}')
print(f'HLS_ENABLE: {getattr(settings, \"HLS_ENABLE\", \"NOT SET\")}')
" 2>/dev/null
        echo ""
    fi
    
    # Section 5: Storage Status
    echo -e "${YELLOW}5. Storage Status${NC}"
    echo "-----------------"
    echo "EBS Usage:"
    df -h /mnt/ebs 2>/dev/null | tail -1
    echo ""
    
    echo "EBS media_files size:"
    du -sh "$EBS_PATH" 2>/dev/null
    echo ""
    
    if [ "$SERVICES_RUNNING" = true ]; then
        echo "Container media_files view:"
        docker exec media_cms df -h /home/mediacms.io/mediacms/media_files 2>/dev/null | tail -1
        echo ""
    fi
    
    # Section 6: File counts
    echo -e "${YELLOW}6. Content Statistics${NC}"
    echo "---------------------"
    
    if [ -d "$EBS_PATH/original" ]; then
        ORIGINAL_COUNT=$(find "$EBS_PATH/original" -type f 2>/dev/null | wc -l)
        echo "Original files: $ORIGINAL_COUNT"
    fi
    
    if [ -d "$EBS_PATH/hls" ]; then
        HLS_COUNT=$(ls -1 "$EBS_PATH/hls" 2>/dev/null | wc -l)
        echo "Videos with HLS: $HLS_COUNT"
    fi
    
    if [ -d "$EBS_PATH/thumbnails" ]; then
        THUMB_COUNT=$(find "$EBS_PATH/thumbnails" -type f 2>/dev/null | wc -l)
        echo "Thumbnails: $THUMB_COUNT"
    fi
    
    if [ -d "$EBS_PATH/cytube_manifests" ]; then
        MANIFEST_COUNT=$(ls -1 "$EBS_PATH/cytube_manifests"/*.json 2>/dev/null | wc -l)
        echo "CyTube manifests: $MANIFEST_COUNT"
    fi
    echo ""
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Validation Complete${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

#═══════════════════════════════════════════════════════════════════
# MAIN EXECUTION
#═══════════════════════════════════════════════════════════════════

main() {
    # Check if running as root or with sudo for ownership changes
    if [ "$MODE" == "init" ] || [ "$MODE" == "full" ]; then
        if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
            echo -e "${YELLOW}⚠️  This script needs sudo access for ownership changes${NC}"
            echo "Please enter your password when prompted"
            echo ""
        fi
    fi
    
    case $MODE in
        init)
            initialize_storage
            ;;
        validate)
            validate_storage
            ;;
        full)
            initialize_storage
            echo ""
            echo -e "${BLUE}Starting services for validation...${NC}"
            cd "$MEDIACMS_ROOT"
            docker-compose up -d
            echo "Waiting 60 seconds for services to start..."
            sleep 60
            echo ""
            validate_storage
            ;;
    esac
    
    # Final recommendations
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    if [ "$MODE" == "init" ]; then
        echo "1. Start services: cd $MEDIACMS_ROOT && docker-compose up -d"
        echo "2. Run validation: $0 --validate"
    elif [ "$MODE" == "validate" ]; then
        if [ "$SERVICES_RUNNING" = false ]; then
            echo "⚠️  Services are not running"
            echo "Start with: cd $MEDIACMS_ROOT && docker-compose up -d"
        else
            echo "✅ Everything looks good!"
            echo "Monitor encoding: docker logs -f mediacms-celery_worker-1"
        fi
    else
        echo "✅ Setup complete! Your system is ready."
        echo ""
        echo "Useful commands:"
        echo "  - Monitor encoding: docker logs -f mediacms-celery_worker-1"
        echo "  - Check storage: df -h /mnt/ebs"
        echo "  - Run validation anytime: $0 --validate"
    fi
    echo ""
}

# Run main
main
