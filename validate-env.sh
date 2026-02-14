#!/bin/bash
# dev-v0.1.1 - TESTING ONLY - validates contents in the .env file

#####
# CHANGELOG
# v0.1.1 - Added validation for quoted values with spaces
#   - Warns if CYTUBE_DESCRIPTION/ORGANIZATION have spaces but missing quotes
#   - Enhanced error messages for common .env syntax issues
# v0.1.0 - Initial release
#   - Validates required environment variables from .env
#   - Checks DOMAIN format (no protocol, valid characters)
#   - Provides clear error messages for missing/invalid values
#   - Exit codes: 0 = valid, 1 = validation failed
#####

# Stored at: /mediacms/validate-env.sh
# Run before docker-compose up to validate configuration

set -e

echo "========================================"
echo "MediaCMS-CyTube Environment Validator"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found in current directory"
    echo "   Please create .env file from .env.example or template"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Source the .env file to load variables
set -a
source .env
set +a

# Track validation errors
VALIDATION_FAILED=0

echo "Validating required variables..."
echo "----------------------------------------"

# ============================================
# VALIDATE DOMAIN
# ============================================
echo -n "Checking DOMAIN... "
if [ -z "$DOMAIN" ]; then
    echo "❌ MISSING"
    echo "   ERROR: DOMAIN is required in .env file"
    echo "   Example: DOMAIN=dev02.420grindhouseserver.com"
    VALIDATION_FAILED=1
elif [[ "$DOMAIN" == *"YOUR DOMAIN NAME"* ]]; then
    echo "❌ NOT CONFIGURED"
    echo "   ERROR: DOMAIN still contains placeholder text"
    echo "   Please replace 'YOUR DOMAIN NAME' with your actual domain"
    VALIDATION_FAILED=1
elif [[ "$DOMAIN" =~ ^https?:// ]]; then
    echo "❌ INVALID FORMAT"
    echo "   ERROR: DOMAIN should not include http:// or https://"
    echo "   Current: $DOMAIN"
    echo "   Correct: ${DOMAIN#*://}"
    VALIDATION_FAILED=1
elif [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]]; then
    echo "❌ INVALID CHARACTERS"
    echo "   ERROR: DOMAIN contains invalid characters"
    echo "   Current: $DOMAIN"
    echo "   Allowed: letters, numbers, dots, hyphens"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $DOMAIN"
fi

# ============================================
# VALIDATE ADMIN_USER
# ============================================
echo -n "Checking ADMIN_USER... "
if [ -z "$ADMIN_USER" ]; then
    echo "❌ MISSING"
    echo "   ERROR: ADMIN_USER is required in .env file"
    VALIDATION_FAILED=1
elif [[ "$ADMIN_USER" == *"SUPERADMIN USERNAME"* ]]; then
    echo "❌ NOT CONFIGURED"
    echo "   ERROR: ADMIN_USER still contains placeholder text"
    echo "   Please replace 'SUPERADMIN USERNAME' with your admin username"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $ADMIN_USER"
fi

# ============================================
# VALIDATE ADMIN_EMAIL
# ============================================
echo -n "Checking ADMIN_EMAIL... "
if [ -z "$ADMIN_EMAIL" ]; then
    echo "❌ MISSING"
    echo "   ERROR: ADMIN_EMAIL is required in .env file"
    VALIDATION_FAILED=1
elif [[ "$ADMIN_EMAIL" == *"SUPERADMIN EMAIL"* ]]; then
    echo "❌ NOT CONFIGURED"
    echo "   ERROR: ADMIN_EMAIL still contains placeholder text"
    echo "   Please replace 'SUPERADMIN EMAIL' with your admin email"
    VALIDATION_FAILED=1
elif [[ ! "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "⚠️  POTENTIALLY INVALID"
    echo "   WARNING: Email format may be incorrect: $ADMIN_EMAIL"
    echo "   (Continuing anyway - Django will validate on first run)"
    echo "✅ Accepted: $ADMIN_EMAIL"
else
    echo "✅ Valid: $ADMIN_EMAIL"
fi

# ============================================
# VALIDATE ADMIN_PASSWORD
# ============================================
echo -n "Checking ADMIN_PASSWORD... "
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "❌ MISSING"
    echo "   ERROR: ADMIN_PASSWORD is required in .env file"
    VALIDATION_FAILED=1
elif [[ "$ADMIN_PASSWORD" == *"SUPERADMIN PASSWORD"* ]]; then
    echo "❌ NOT CONFIGURED"
    echo "   ERROR: ADMIN_PASSWORD still contains placeholder text"
    echo "   Please replace 'SUPERADMIN PASSWORD' with a secure password"
    VALIDATION_FAILED=1
else
    echo "✅ Valid (hidden for security)"
fi

# ============================================
# VALIDATE OPTIONAL VARIABLES
# ============================================
echo ""
echo "Checking optional variables..."
echo "----------------------------------------"

# ============================================
# VALIDATE CYTUBE_DESCRIPTION
# ============================================
echo -n "Checking CYTUBE_DESCRIPTION... "
if [ -z "$CYTUBE_DESCRIPTION" ]; then
    echo "⚠️  Using default: 'Custom MediaCMS streaming server'"
else
    # Check if .env file line has spaces but no quotes
    if grep -q '^CYTUBE_DESCRIPTION=[^"].*[[:space:]]' .env 2>/dev/null; then
        echo "⚠️  WARNING"
        echo "   Value contains spaces but may be missing quotes in .env"
        echo "   Current .env line: $(grep '^CYTUBE_DESCRIPTION=' .env)"
        echo "   Recommended format: CYTUBE_DESCRIPTION=\"Your description here\""
        echo "   Loaded value: $CYTUBE_DESCRIPTION"
    else
        echo "✅ Custom: $CYTUBE_DESCRIPTION"
    fi
fi

# ============================================
# VALIDATE CYTUBE_ORGANIZATION
# ============================================
echo -n "Checking CYTUBE_ORGANIZATION... "
if [ -z "$CYTUBE_ORGANIZATION" ]; then
    echo "⚠️  Using default: 'MediaCMS-CyTube'"
else
    # Check if .env file line has spaces but no quotes
    if grep -q '^CYTUBE_ORGANIZATION=[^"].*[[:space:]]' .env 2>/dev/null; then
        echo "⚠️  WARNING"
        echo "   Value contains spaces but may be missing quotes in .env"
        echo "   Current .env line: $(grep '^CYTUBE_ORGANIZATION=' .env)"
        echo "   Recommended format: CYTUBE_ORGANIZATION=\"Your org name\""
        echo "   Loaded value: $CYTUBE_ORGANIZATION"
    else
        echo "✅ Custom: $CYTUBE_ORGANIZATION"
    fi
fi

# ============================================
# VALIDATE CRITICAL SYSTEM VARIABLES
# ============================================
echo ""
echo "Checking critical system variables..."
echo "----------------------------------------"

echo -n "Checking MEDIA_FILES_PATH... "
if [ -z "$MEDIA_FILES_PATH" ]; then
    echo "❌ MISSING"
    echo "   ERROR: MEDIA_FILES_PATH is required"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $MEDIA_FILES_PATH"
fi

echo -n "Checking WEB_CONTAINER_NAME... "
if [ "$WEB_CONTAINER_NAME" != "media_cms" ]; then
    echo "⚠️  WARNING"
    echo "   WEB_CONTAINER_NAME should be 'media_cms' due to hardcoded MediaCMS conflicts"
    echo "   Current: $WEB_CONTAINER_NAME"
    echo "   Recommended: media_cms"
else
    echo "✅ Valid: $WEB_CONTAINER_NAME"
fi

# ============================================
# FINAL RESULT
# ============================================
echo ""
echo "========================================"
if [ $VALIDATION_FAILED -eq 1 ]; then
    echo "❌ VALIDATION FAILED"
    echo "========================================"
    echo ""
    echo "Please fix the errors above in your .env file"
    echo "Then run this script again before starting Docker"
    echo ""
    exit 1
else
    echo "✅ VALIDATION PASSED"
    echo "========================================"
    echo ""
    echo "Your .env configuration is valid!"
    echo ""
    echo "Configuration Summary:"
    echo "  Domain:       $DOMAIN"
    echo "  Admin User:   $ADMIN_USER"
    echo "  Admin Email:  $ADMIN_EMAIL"
    echo "  Description:  ${CYTUBE_DESCRIPTION:-Default}"
    echo "  Organization: ${CYTUBE_ORGANIZATION:-Default}"
    echo ""
    echo "You can now run: ./cytube-execute-all-sh-and-storage-init.sh"
    echo "Or manually: docker-compose up -d"
    echo ""
    exit 0
fi
