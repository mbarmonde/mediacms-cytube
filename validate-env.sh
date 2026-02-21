#!/bin/bash
# dev-v0.3.0 - Added ENCODING_BACKEND and ENCODING_GPU_PRESET validation

#####
# CHANGELOG
# v0.3.0 - GPU ENCODING BACKEND VALIDATION
#   - Added ENCODING_BACKEND validation (cpu|gpu)
#   - Added ENCODING_GPU_PRESET validation (p1-p7, only checked when ENCODING_BACKEND=gpu)
#   - GPU mode emits a HOST REQUIREMENTS warning (nvidia-container-toolkit, docker-compose.gpu.yml)
#   - CPU mode: zero behavior change, no new warnings
#   - Added ENCODING_BACKEND line to configuration summary
# v0.2.0 - FFMPEG ENCODING CONFIGURATION VALIDATION
#   - Added validation for new FFMPEG_* environment variables
#   - Conditional validation for OpenSubtitles (only when OPENSUBTITLES_ENABLED=true)
#   - Validates FFMPEG_RESOLUTIONS format (comma-separated, valid values)
#   - Validates FFMPEG_PRESET (must be valid FFmpeg preset)
#   - Validates FFMPEG_CRF values (H.264: 18-28, H.265: 20-32, VP9: 24-40)
#   - Validates FFMPEG_AUDIO_BITRATE format (must end with 'k')
#   - Validates HLS_SEGMENT_TIME range (2-10 seconds)
#   - Enhanced error messages with recommendations
#   - Provides configuration summary at end
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
echo "v0.3.0 - with GPU Encoding Validation"
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

# Track validation errors and warnings
VALIDATION_FAILED=0
WARNING_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "REQUIRED CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# VALIDATE DOMAIN
# ============================================
echo -n "Checking DOMAIN... "
if [ -z "$DOMAIN" ]; then
    echo "❌ MISSING"
    echo "   ERROR: DOMAIN is required in .env file"
    echo "   Example: DOMAIN=dev02.420grindhouseserver.com"
    VALIDATION_FAILED=1
elif [[ "$DOMAIN" == *"YOUR.DOMAIN.NAME"* ]] || [[ "$DOMAIN" == *"YOUR DOMAIN NAME"* ]]; then
    echo "❌ NOT CONFIGURED"
    echo "   ERROR: DOMAIN still contains placeholder text"
    echo "   Please replace 'YOUR.DOMAIN.NAME' with your actual domain"
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
    WARNING_COUNT=$((WARNING_COUNT + 1))
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
# CONDITIONAL: OPENSUBTITLES VALIDATION
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPENSUBTITLES CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -n "Checking OPENSUBTITLES_ENABLED... "
OPENSUBTITLES_ENABLED_LOWER=$(echo "$OPENSUBTITLES_ENABLED" | tr '[:upper:]' '[:lower:]')

if [ -z "$OPENSUBTITLES_ENABLED" ]; then
    echo "⚠️  Not set (defaulting to false)"
    OPENSUBTITLES_ENABLED_LOWER="false"
    WARNING_COUNT=$((WARNING_COUNT + 1))
elif [ "$OPENSUBTITLES_ENABLED_LOWER" = "true" ]; then
    echo "✅ Enabled"

    # Validate API Key
    echo -n "Checking OPENSUBTITLES_API_KEY... "
    if [ -z "$OPENSUBTITLES_API_KEY" ]; then
        echo "❌ MISSING"
        echo "   ERROR: OPENSUBTITLES_API_KEY is required when OPENSUBTITLES_ENABLED=true"
        echo "   Get your API key from: https://www.opensubtitles.com/api"
        VALIDATION_FAILED=1
    elif [[ "$OPENSUBTITLES_API_KEY" == *"YOU_API_KEY"* ]] || [[ "$OPENSUBTITLES_API_KEY" == *"YOUR_API_KEY"* ]]; then
        echo "❌ NOT CONFIGURED"
        echo "   ERROR: OPENSUBTITLES_API_KEY still contains placeholder text"
        echo "   Please replace with your actual OpenSubtitles API key"
        VALIDATION_FAILED=1
    else
        echo "✅ Configured"
    fi

    # Validate JWT Token
    echo -n "Checking OPENSUBTITLES_JWT_TOKEN... "
    if [ -z "$OPENSUBTITLES_JWT_TOKEN" ]; then
        echo "❌ MISSING"
        echo "   ERROR: OPENSUBTITLES_JWT_TOKEN is required when OPENSUBTITLES_ENABLED=true"
        echo "   Get your JWT token from: https://www.opensubtitles.com (Settings/API section)"
        VALIDATION_FAILED=1
    elif [[ "$OPENSUBTITLES_JWT_TOKEN" == *"YOUR_PERMANENT_JWT_TOKEN_HERE"* ]]; then
        echo "❌ NOT CONFIGURED"
        echo "   ERROR: OPENSUBTITLES_JWT_TOKEN still contains placeholder text"
        echo "   Please replace with your actual OpenSubtitles JWT token"
        VALIDATION_FAILED=1
    else
        echo "✅ Configured"
    fi

elif [ "$OPENSUBTITLES_ENABLED_LOWER" = "false" ]; then
    echo "✅ Disabled (API keys not required)"
else
    echo "⚠️  Invalid value: $OPENSUBTITLES_ENABLED"
    echo "   WARNING: Should be 'true' or 'false' (defaulting to false)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi

# ============================================
# OPTIONAL VARIABLES
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPTIONAL CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# VALIDATE CYTUBE_DESCRIPTION
# ============================================
echo -n "Checking CYTUBE_DESCRIPTION... "
if [ -z "$CYTUBE_DESCRIPTION" ]; then
    echo "⚠️  Using default: 'Custom MediaCMS streaming server'"
else
    if grep -q '^CYTUBE_DESCRIPTION=[^"].*[[:space:]]' .env 2>/dev/null; then
        echo "⚠️  WARNING"
        echo "   Value contains spaces but may be missing quotes in .env"
        echo "   Current .env line: $(grep '^CYTUBE_DESCRIPTION=' .env)"
        echo "   Recommended format: CYTUBE_DESCRIPTION=\"Your description here\""
        echo "   Loaded value: $CYTUBE_DESCRIPTION"
        WARNING_COUNT=$((WARNING_COUNT + 1))
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
    if grep -q '^CYTUBE_ORGANIZATION=[^"].*[[:space:]]' .env 2>/dev/null; then
        echo "⚠️  WARNING"
        echo "   Value contains spaces but may be missing quotes in .env"
        echo "   Current .env line: $(grep '^CYTUBE_ORGANIZATION=' .env)"
        echo "   Recommended format: CYTUBE_ORGANIZATION=\"Your org name\""
        echo "   Loaded value: $CYTUBE_ORGANIZATION"
        WARNING_COUNT=$((WARNING_COUNT + 1))
    else
        echo "✅ Custom: $CYTUBE_ORGANIZATION"
    fi
fi

# ============================================
# FFMPEG ENCODING CONFIGURATION VALIDATION
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FFMPEG ENCODING CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# VALIDATE FFMPEG_TRANSCODE_ENABLED
# ============================================
echo -n "Checking FFMPEG_TRANSCODE_ENABLED... "
FFMPEG_TRANSCODE_LOWER=$(echo "$FFMPEG_TRANSCODE_ENABLED" | tr '[:upper:]' '[:lower:]')
if [ "$FFMPEG_TRANSCODE_LOWER" = "true" ] || [ "$FFMPEG_TRANSCODE_LOWER" = "false" ]; then
    echo "✅ $FFMPEG_TRANSCODE_ENABLED"
else
    echo "⚠️  Invalid: $FFMPEG_TRANSCODE_ENABLED (defaulting to true)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi

# ============================================
# VALIDATE FFMPEG_RESOLUTIONS
# ============================================
echo -n "Checking FFMPEG_RESOLUTIONS... "
if [ -z "$FFMPEG_RESOLUTIONS" ]; then
    echo "⚠️  Using default: 480,720,1080"
else
    VALID_RESOLUTIONS="144 240 360 480 720 1080 1440 2160"
    INVALID_RES=0
    IFS=',' read -ra RES_ARRAY <<< "$FFMPEG_RESOLUTIONS"
    for res in "${RES_ARRAY[@]}"; do
        res=$(echo "$res" | xargs)
        if [[ ! " $VALID_RESOLUTIONS " =~ " $res " ]]; then
            if [ $INVALID_RES -eq 0 ]; then
                echo "❌ INVALID"
                echo "   ERROR: Invalid resolution: $res"
                INVALID_RES=1
            else
                echo "   ERROR: Invalid resolution: $res"
            fi
            VALIDATION_FAILED=1
        fi
    done

    if [ $INVALID_RES -eq 0 ]; then
        echo "✅ Valid: $FFMPEG_RESOLUTIONS"
    else
        echo "   Valid resolutions: 144, 240, 360, 480, 720, 1080, 1440, 2160"
        echo "   Recommended for movies: 480,720,1080"
    fi
fi

# ============================================
# VALIDATE FFMPEG_PRESET (CPU only)
# ============================================
echo -n "Checking FFMPEG_PRESET (CPU)... "
VALID_PRESETS="ultrafast superfast veryfast faster fast medium slow slower veryslow"
if [ -z "$FFMPEG_PRESET" ]; then
    echo "⚠️  Using default: faster"
elif [[ ! " $VALID_PRESETS " =~ " $FFMPEG_PRESET " ]]; then
    echo "❌ INVALID"
    echo "   ERROR: Invalid preset: $FFMPEG_PRESET"
    echo "   Valid options: $VALID_PRESETS"
    echo "   Recommended: faster (best quality/speed balance)"
    echo "   NOTE: For GPU preset see ENCODING_GPU_PRESET below"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $FFMPEG_PRESET"
fi

# ============================================
# VALIDATE FFMPEG_H264_PROFILE
# ============================================
echo -n "Checking FFMPEG_H264_PROFILE... "
VALID_PROFILES="baseline main high"
if [ -z "$FFMPEG_H264_PROFILE" ]; then
    echo "⚠️  Using default: main"
elif [[ ! " $VALID_PROFILES " =~ " $FFMPEG_H264_PROFILE " ]]; then
    echo "❌ INVALID"
    echo "   ERROR: Invalid H.264 profile: $FFMPEG_H264_PROFILE"
    echo "   Valid options: baseline, main, high"
    echo "   Recommended: main (best compatibility/compression balance)"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $FFMPEG_H264_PROFILE"
fi

# ============================================
# VALIDATE FFMPEG_CRF_H264
# ============================================
echo -n "Checking FFMPEG_CRF_H264... "
if [ -z "$FFMPEG_CRF_H264" ]; then
    echo "⚠️  Using default: 22"
elif ! [[ "$FFMPEG_CRF_H264" =~ ^[0-9]+$ ]]; then
    echo "❌ INVALID"
    echo "   ERROR: CRF must be a number: $FFMPEG_CRF_H264"
    VALIDATION_FAILED=1
elif [ "$FFMPEG_CRF_H264" -lt 18 ] || [ "$FFMPEG_CRF_H264" -gt 28 ]; then
    echo "⚠️  OUT OF RANGE"
    echo "   WARNING: H.264 CRF should be 18-28 (got $FFMPEG_CRF_H264)"
    echo "   Lower = better quality, larger files"
    echo "   Recommended for movies: 22"
    echo "   NOTE: Maps to -cq $FFMPEG_CRF_H264 when ENCODING_BACKEND=gpu"
    WARNING_COUNT=$((WARNING_COUNT + 1))
    echo "✅ Accepted: $FFMPEG_CRF_H264"
else
    echo "✅ Valid: $FFMPEG_CRF_H264"
fi

# ============================================
# VALIDATE FFMPEG_CRF_H265
# ============================================
echo -n "Checking FFMPEG_CRF_H265... "
if [ -z "$FFMPEG_CRF_H265" ]; then
    echo "⚠️  Using default: 28"
elif ! [[ "$FFMPEG_CRF_H265" =~ ^[0-9]+$ ]]; then
    echo "❌ INVALID"
    echo "   ERROR: CRF must be a number: $FFMPEG_CRF_H265"
    VALIDATION_FAILED=1
elif [ "$FFMPEG_CRF_H265" -lt 20 ] || [ "$FFMPEG_CRF_H265" -gt 32 ]; then
    echo "⚠️  OUT OF RANGE"
    echo "   WARNING: H.265 CRF should be 20-32 (got $FFMPEG_CRF_H265)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
    echo "✅ Accepted: $FFMPEG_CRF_H265"
else
    echo "✅ Valid: $FFMPEG_CRF_H265"
fi

# ============================================
# VALIDATE FFMPEG_CRF_VP9
# ============================================
echo -n "Checking FFMPEG_CRF_VP9... "
if [ -z "$FFMPEG_CRF_VP9" ]; then
    echo "⚠️  Using default: 32"
elif ! [[ "$FFMPEG_CRF_VP9" =~ ^[0-9]+$ ]]; then
    echo "❌ INVALID"
    echo "   ERROR: CRF must be a number: $FFMPEG_CRF_VP9"
    VALIDATION_FAILED=1
elif [ "$FFMPEG_CRF_VP9" -lt 24 ] || [ "$FFMPEG_CRF_VP9" -gt 40 ]; then
    echo "⚠️  OUT OF RANGE"
    echo "   WARNING: VP9 CRF should be 24-40 (got $FFMPEG_CRF_VP9)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
    echo "✅ Accepted: $FFMPEG_CRF_VP9"
else
    echo "✅ Valid: $FFMPEG_CRF_VP9"
fi

# ============================================
# VALIDATE FFMPEG_AUDIO_CODEC
# ============================================
echo -n "Checking FFMPEG_AUDIO_CODEC... "
VALID_AUDIO_CODECS="aac opus mp3"
if [ -z "$FFMPEG_AUDIO_CODEC" ]; then
    echo "⚠️  Using default: aac"
elif [[ ! " $VALID_AUDIO_CODECS " =~ " $FFMPEG_AUDIO_CODEC " ]]; then
    echo "⚠️  UNEXPECTED VALUE"
    echo "   WARNING: Uncommon audio codec: $FFMPEG_AUDIO_CODEC"
    echo "   Valid options: aac, opus, mp3"
    echo "   Recommended: aac (required for HLS)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
    echo "✅ Accepted: $FFMPEG_AUDIO_CODEC"
else
    echo "✅ Valid: $FFMPEG_AUDIO_CODEC"
fi

# ============================================
# VALIDATE FFMPEG_AUDIO_BITRATE
# ============================================
echo -n "Checking FFMPEG_AUDIO_BITRATE... "
if [ -z "$FFMPEG_AUDIO_BITRATE" ]; then
    echo "⚠️  Using default: 128k"
elif [[ ! "$FFMPEG_AUDIO_BITRATE" =~ ^[0-9]+k$ ]]; then
    echo "❌ INVALID FORMAT"
    echo "   ERROR: Audio bitrate must end with 'k': $FFMPEG_AUDIO_BITRATE"
    echo "   Valid examples: 96k, 128k, 192k, 256k"
    echo "   Recommended: 128k"
    VALIDATION_FAILED=1
else
    echo "✅ Valid: $FFMPEG_AUDIO_BITRATE"
fi

# ============================================
# dev-v0.3.0: ENCODING BACKEND VALIDATION
# New section — inserted between FFMPEG and HLS sections
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ENCODING BACKEND CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# VALIDATE ENCODING_BACKEND
echo -n "Checking ENCODING_BACKEND... "
ENCODING_BACKEND_LOWER=$(echo "${ENCODING_BACKEND:-cpu}" | tr '[:upper:]' '[:lower:]')

if [ -z "$ENCODING_BACKEND" ]; then
    echo "⚠️  Not set (defaulting to cpu)"
    ENCODING_BACKEND_LOWER="cpu"
    WARNING_COUNT=$((WARNING_COUNT + 1))
elif [ "$ENCODING_BACKEND_LOWER" = "cpu" ]; then
    echo "✅ cpu (software encoding via libx264)"
elif [ "$ENCODING_BACKEND_LOWER" = "gpu" ]; then
    echo "✅ gpu (hardware encoding via h264_nvenc)"
    echo ""
    echo "   ⚠️  GPU MODE ACTIVE — Host requirements:"
    echo "   1. NVIDIA GPU must be installed on the host"
    echo "   2. nvidia-container-toolkit must be installed:"
    echo "      https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    echo "   3. Start with GPU override:"
    echo "      docker compose -f docker-compose.yaml -f docker-compose.gpu.yml up -d"
    echo "   4. Verify GPU available to container:"
    echo "      docker exec mediacms_celery_worker nvidia-smi"
    echo ""
    WARNING_COUNT=$((WARNING_COUNT + 1))
else
    echo "❌ INVALID"
    echo "   ERROR: Invalid ENCODING_BACKEND: $ENCODING_BACKEND"
    echo "   Valid options: cpu, gpu"
    echo "   Recommended: cpu (default, works on all servers)"
    VALIDATION_FAILED=1
fi

# VALIDATE ENCODING_GPU_PRESET (only enforced when ENCODING_BACKEND=gpu)
echo -n "Checking ENCODING_GPU_PRESET... "
VALID_GPU_PRESETS="p1 p2 p3 p4 p5 p6 p7"
if [ -z "$ENCODING_GPU_PRESET" ]; then
    echo "⚠️  Not set (defaulting to p4)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
elif [[ ! " $VALID_GPU_PRESETS " =~ " $ENCODING_GPU_PRESET " ]]; then
    if [ "$ENCODING_BACKEND_LOWER" = "gpu" ]; then
        echo "❌ INVALID"
        echo "   ERROR: Invalid GPU preset: $ENCODING_GPU_PRESET"
        echo "   Valid options: p1 (fastest) to p7 (highest quality)"
        echo "   Recommended: p4 (equivalent to CPU preset 'faster')"
        VALIDATION_FAILED=1
    else
        echo "⚠️  Invalid value: $ENCODING_GPU_PRESET (not active — ENCODING_BACKEND=cpu)"
        echo "   Valid options when GPU active: p1 (fastest) to p7 (highest quality)"
        WARNING_COUNT=$((WARNING_COUNT + 1))
    fi
else
    if [ "$ENCODING_BACKEND_LOWER" = "gpu" ]; then
        echo "✅ Valid: $ENCODING_GPU_PRESET (active — ENCODING_BACKEND=gpu)"
    else
        echo "✅ Valid: $ENCODING_GPU_PRESET (not active — ENCODING_BACKEND=cpu)"
    fi
fi

# ============================================
# HLS STREAMING CONFIGURATION VALIDATION
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "HLS STREAMING CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# VALIDATE HLS_ENABLED
# ============================================
echo -n "Checking HLS_ENABLED... "
HLS_ENABLED_LOWER=$(echo "$HLS_ENABLED" | tr '[:upper:]' '[:lower:]')
if [ "$HLS_ENABLED_LOWER" = "true" ]; then
    echo "✅ Enabled (required for CyTube)"
elif [ "$HLS_ENABLED_LOWER" = "false" ]; then
    echo "⚠️  DISABLED"
    echo "   WARNING: HLS is required for CyTube integration!"
    echo "   CyTube needs HLS (application/x-mpegURL) for streaming"
    echo "   Recommended: HLS_ENABLED=true"
    WARNING_COUNT=$((WARNING_COUNT + 1))
else
    echo "⚠️  Invalid: $HLS_ENABLED (defaulting to true)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi

# ============================================
# VALIDATE HLS_SEGMENT_TIME
# ============================================
echo -n "Checking HLS_SEGMENT_TIME... "
if [ -z "$HLS_SEGMENT_TIME" ]; then
    echo "⚠️  Using default: 6"
elif ! [[ "$HLS_SEGMENT_TIME" =~ ^[0-9]+$ ]]; then
    echo "❌ INVALID"
    echo "   ERROR: Segment time must be a number: $HLS_SEGMENT_TIME"
    VALIDATION_FAILED=1
elif [ "$HLS_SEGMENT_TIME" -lt 2 ] || [ "$HLS_SEGMENT_TIME" -gt 10 ]; then
    echo "⚠️  OUT OF RANGE"
    echo "   WARNING: HLS segment time should be 2-10 seconds (got $HLS_SEGMENT_TIME)"
    echo "   Recommended: 6 (Apple HLS standard)"
    WARNING_COUNT=$((WARNING_COUNT + 1))
    echo "✅ Accepted: $HLS_SEGMENT_TIME"
else
    echo "✅ Valid: $HLS_SEGMENT_TIME seconds"
fi

# ============================================
# VALIDATE HLS_FLAGS
# ============================================
echo -n "Checking HLS_FLAGS... "
if [ -z "$HLS_FLAGS" ]; then
    echo "⚠️  Using default: independent_segments"
else
    echo "✅ Custom: $HLS_FLAGS"
fi

# ============================================
# CRITICAL SYSTEM VARIABLES
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CRITICAL SYSTEM VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

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
    WARNING_COUNT=$((WARNING_COUNT + 1))
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
    if [ $WARNING_COUNT -gt 0 ]; then
        echo "Also found $WARNING_COUNT warning(s) - review recommended"
    fi
    echo ""
    exit 1
else
    echo "✅ VALIDATION PASSED"
    if [ $WARNING_COUNT -gt 0 ]; then
        echo "⚠️  Found $WARNING_COUNT warning(s)"
    fi
    echo "========================================"
    echo ""
    echo "📋 CONFIGURATION SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Deployment:"
    echo "   Domain:       $DOMAIN"
    echo "   Admin User:   $ADMIN_USER"
    echo "   Admin Email:  $ADMIN_EMAIL"
    echo ""
    echo "🎬 FFmpeg Encoding:"
    echo "   Backend:      ${ENCODING_BACKEND:-cpu}"
    if [ "$ENCODING_BACKEND_LOWER" = "gpu" ]; then
        echo "   GPU Preset:   ${ENCODING_GPU_PRESET:-p4} (h264_nvenc)"
    else
        echo "   CPU Preset:   ${FFMPEG_PRESET:-faster} (libx264)"
    fi
    echo "   Transcoding:  ${FFMPEG_TRANSCODE_ENABLED:-true}"
    echo "   Resolutions:  ${FFMPEG_RESOLUTIONS:-480,720,1080}"
    echo "   H.264 Profile:${FFMPEG_H264_PROFILE:-main}"
    echo "   H.264 CRF:    ${FFMPEG_CRF_H264:-22}"
    echo "   Audio:        ${FFMPEG_AUDIO_CODEC:-aac} @ ${FFMPEG_AUDIO_BITRATE:-128k}"
    echo ""
    echo "📺 HLS Streaming:"
    echo "   Enabled:      ${HLS_ENABLED:-true}"
    echo "   Segment Time: ${HLS_SEGMENT_TIME:-6}s"
    echo ""
    echo "📝 OpenSubtitles:"
    echo "   Enabled:      ${OPENSUBTITLES_ENABLED:-false}"
    if [ "$OPENSUBTITLES_ENABLED_LOWER" = "true" ]; then
        echo "   API Key:      Configured ✅"
        echo "   JWT Token:    Configured ✅"
    fi
    echo ""
    echo "🎭 CyTube Integration:"
    echo "   Description:  ${CYTUBE_DESCRIPTION:-Default}"
    echo "   Organization: ${CYTUBE_ORGANIZATION:-Default}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    if [ $WARNING_COUNT -gt 0 ]; then
        echo "⚠️  Please review the $WARNING_COUNT warning(s) above"
        echo ""
    fi
    echo "✅ Ready to deploy!"
    echo ""
    if [ "$ENCODING_BACKEND_LOWER" = "gpu" ]; then
        echo "GPU MODE — Start command:"
        echo "  docker compose -f docker-compose.yaml -f docker-compose.gpu.yml up -d"
    else
        echo "Next steps:"
        echo "  1. ./cytube-execute-all-sh-and-storage-init.sh"
        echo "  2. Or manually: docker-compose up -d"
    fi
    echo ""
    exit 0
fi