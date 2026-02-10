#!/bin/bash

# dev-v0.3.0

#####
# v0.3.0 - SUBTITLE LANGUAGE AUTO-INITIALIZATION
# - Added automatic subtitle language population after container startup
# - Added container health checks with retry logic
# - Waits for database to be fully ready before language initialization
# - Integrated init_subtitle_languages.sh execution
# v0.2.0 - CENTRALIZED CONFIGURATION VALIDATION
# - Added environment validation before container startup
# - Validates .env file for DOMAIN, ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD
# - Prevents startup with invalid/missing configuration
# - Exits with clear error messages if validation fails
# v0.1.6 - fixed path issues by commenting out folder locations
# v0.1.5 - Integrated all files into GitHub pull - Only for chmod all files to execute and storage config
# v0.1.4 - Final script for alt root folder copy
##### Run Flow
#Step 1: Validate .env configuration
#  ↓ (exits if invalid)
#Step 2: Make all .sh files executable
#  ↓
#Step 3: Run storage initialization
#  ↓
#Step 4: Start Docker containers
#  ↓
#Step 5: Wait for containers to be healthy
#  ├─ Wait for database container (30s timeout)
#  ├─ Wait for web container (30s timeout)
#  └─ Wait for database migrations (120s timeout)
#  ↓
#Step 6: Initialize subtitle languages (automatic)
#  ├─ Detects database container
#  ├─ Checks if languages already exist
#  └─ Inserts 20 languages if needed
#  ↓
#✅ Success message with URL and credentials
#####

# chmod +x (filename).sh to make executable
#./(filename) to run in CLI

## Define destination directory
DEST_DIR="/mediacms"

echo "========================================"
echo "MediaCMS-CyTube Startup Script"
echo "========================================"
echo ""

# ============================================
# STEP 1: VALIDATE ENVIRONMENT CONFIGURATION
# ============================================
echo "STEP 1: Validating environment configuration..."
echo "----------------------------------------"

ENV_VALIDATION_SCRIPT="$DEST_DIR/validate-env.sh"

if [ -f "$ENV_VALIDATION_SCRIPT" ]; then
    echo "Running environment validation..."
    if "$ENV_VALIDATION_SCRIPT"; then
        echo "✅ Environment validation passed"
        echo ""
    else
        echo ""
        echo "❌ Environment validation failed!"
        echo "Please fix the errors above before continuing."
        echo ""
        exit 1
    fi
else
    echo "⚠️  Warning: validate-env.sh not found at $ENV_VALIDATION_SCRIPT"
    echo "Skipping environment validation (not recommended)"
    echo ""
fi

# ============================================
# STEP 2: MAKE ALL SCRIPTS EXECUTABLE
# ============================================
echo "STEP 2: Making all .sh files executable..."
echo "----------------------------------------"
find "$DEST_DIR" -type f -name "*.sh" -exec chmod +x {} \;
echo "✅ All .sh files are now executable"
echo ""

# ============================================
# STEP 3: RUN STORAGE VALIDATION
# ============================================
echo "STEP 3: Running storage initialization..."
echo "----------------------------------------"

STORAGE_VALIDATION_SCRIPT="$DEST_DIR/scripts/init_validate_storage.sh"

if [ -f "$STORAGE_VALIDATION_SCRIPT" ]; then
    echo "Running storage validation..."
    "$STORAGE_VALIDATION_SCRIPT"
    echo "✅ Storage validation complete"
    echo ""
else
    echo "⚠️  Warning: init_validate_storage.sh not found at $STORAGE_VALIDATION_SCRIPT"
    echo "Skipping storage validation"
    echo ""
fi

# ============================================
# STEP 4: START DOCKER CONTAINERS
# ============================================
echo "STEP 4: Starting Docker containers..."
echo "----------------------------------------"

cd "$DEST_DIR"

# Check if docker-compose.yaml exists
if [ ! -f "docker-compose.yaml" ]; then
    echo "❌ ERROR: docker-compose.yaml not found in $DEST_DIR"
    exit 1
fi

# Start containers
echo "Running: docker-compose up -d"
docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "❌ Docker Compose Failed to Start"
    echo "========================================"
    echo ""
    echo "Check the error messages above for details."
    echo "Common issues:"
    echo "  - Port 80/443 already in use"
    echo "  - Invalid docker-compose.yaml syntax"
    echo "  - Missing Docker network"
    echo ""
    exit 1
fi

echo "✅ Containers started successfully"
echo ""

# ============================================
# STEP 5: WAIT FOR CONTAINERS TO BE HEALTHY
# ============================================
echo "STEP 5: Waiting for containers to be ready..."
echo "----------------------------------------"

# Function to check if a container is running
check_container() {
    local container_name=$1
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Wait for database container
echo -n "Waiting for database container"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if check_container "mediacms_db" || check_container "mediacms-db-1"; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo " ❌"
    echo "ERROR: Database container failed to start within 60 seconds"
    exit 1
fi

# Wait for web container
echo -n "Waiting for web container"
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if check_container "media_cms"; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo " ❌"
    echo "ERROR: Web container failed to start within 60 seconds"
    exit 1
fi

# Wait for database to be ready (accepting connections)
echo -n "Waiting for database migrations to complete"
RETRY_COUNT=0
MAX_DB_RETRIES=60  # 2 minutes for migrations

while [ $RETRY_COUNT -lt $MAX_DB_RETRIES ]; do
    # Try to connect to database
    if docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT 1;" > /dev/null 2>&1 || \
       docker exec mediacms-db-1 psql -U mediacms -d mediacms -c "SELECT 1;" > /dev/null 2>&1; then
        # Check if files_language table exists (indicates migrations are done)
        if docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT 1 FROM files_language LIMIT 1;" > /dev/null 2>&1 || \
           docker exec mediacms-db-1 psql -U mediacms -d mediacms -c "SELECT 1 FROM files_language LIMIT 1;" > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_DB_RETRIES ]; then
    echo " ⚠️"
    echo "WARNING: Database migrations may not be complete"
    echo "Subtitle language initialization might fail - you can run it manually later"
    echo ""
else
    echo ""
fi

# ============================================
# STEP 6: INITIALIZE SUBTITLE LANGUAGES
# ============================================
echo "STEP 6: Initializing subtitle languages..."
echo "----------------------------------------"

SUBTITLE_INIT_SCRIPT="$DEST_DIR/scripts/init_subtitle_languages.sh"

if [ -f "$SUBTITLE_INIT_SCRIPT" ]; then
    # Run subtitle initialization
    if "$SUBTITLE_INIT_SCRIPT"; then
        echo ""
    else
        echo "⚠️  Warning: Subtitle language initialization failed"
        echo "You can run it manually later with:"
        echo "  $SUBTITLE_INIT_SCRIPT"
        echo ""
    fi
else
    echo "⚠️  Warning: init_subtitle_languages.sh not found at $SUBTITLE_INIT_SCRIPT"
    echo "Skipping subtitle language initialization"
    echo ""
fi

# ============================================
# SUCCESS MESSAGE
# ============================================
echo ""
echo "========================================"
echo "✅ MediaCMS-CyTube Started Successfully"
echo "========================================"
echo ""

# Load DOMAIN from .env for display
if [ -f "$DEST_DIR/.env" ]; then
    set -a
    source "$DEST_DIR/.env"
    set +a
fi

echo "Your MediaCMS instance should be available at:"
echo "  https://${DOMAIN:-your-domain.com}"
echo ""
echo "Useful commands:"
echo "  Check status:  docker-compose ps"
echo "  View logs:     docker-compose logs -f"
echo "  Stop:          docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo "Admin credentials:"
echo "  Username: ${ADMIN_USER:-[see .env file]}"
echo "  Email:    ${ADMIN_EMAIL:-[see .env file]}"
echo ""
