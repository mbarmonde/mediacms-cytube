# dev-v0.3.0 - Django settings - centralized configuration via .env

#####
# v0.3.0 - FFMPEG ENCODING CONFIGURATION CENTRALIZATION
# - All encoding settings now read from .env file
# - Added validation for FFMPEG_* environment variables
# - Fixes bug where FFMPEG_CRF was ignored (hardcoded in helpers.py)
# - New settings: FFMPEG_TRANSCODE_ENABLED, FFMPEG_RESOLUTIONS, FFMPEG_PRESET
# - New settings: FFMPEG_H264_PROFILE, FFMPEG_CRF_H264, FFMPEG_CRF_H265, FFMPEG_CRF_VP9
# - New settings: FFMPEG_AUDIO_CODEC, FFMPEG_AUDIO_BITRATE
# - New settings: HLS_ENABLED, HLS_SEGMENT_TIME, HLS_FLAGS
# - Backward compatible: Falls back to sensible defaults if .env values missing
# - Comprehensive logging of encoding configuration on startup
# v0.2.4 - Modified the OpenSubtitles storage location to OPENSUBTITLES_DOWNLOAD_PATH = '/home/mediacms.io/mediacms/media_files/original/subtitles'
# v0.2.3 - Modified the OpenSubtitles storage location to a hardcoded location: /mnt/ebs/mediacms_media/original/subtitles/
# v0.2.2 - JWT TOKEN ENABLED
# - OPENSUBTITLES_JWT_TOKEN = os.environ.get('OPENSUBTITLES_JWT_TOKEN', '')
# v0.2.1 - OPENSUBTITLES API INTEGRATION + FFMPEG CHANGE
# - Changed from veryfast to faster (next setting down)
# - Added OpenSubtitles.com REST API configuration
# - New settings: OPENSUBTITLES_* variables from .env
# - Subtitle storage path aligned with existing /mnt/ebs structure
# v0.2.0 - CENTRALIZED CONFIGURATION
# - Replaced hardcoded domain with os.environ.get('DOMAIN')
# - FRONTEND_HOST now constructed as https://{DOMAIN}
# - PORTAL_NAME and PORTAL_DESCRIPTION now use CYTUBE_DESCRIPTION from .env
# - Added environment variable validation
# - Removed manual Find/Replace requirement for domain and description
# v0.1.3 - Changed and added to MINIMUM_RESOLUTIONS_TO_ENCODE = [480, 720, 1080]
# v0.1.2 - Better search logic for YOUR.DOMAIN.COM and YOUR SERVER DESCRIPTION counts
# v0.1.1 - Chunk fixes for uploads
# - UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024 # 10GB
# - FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024 # 100MB
# - DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
# - UPLOAD_CHUNKS = True
# - UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024 # 50MB chunks
# - CHUNK_UPLOAD_TIMEOUT = 7200 # 2 hours
# v0.1.0 - MAJOR UPDATE: Enabled HLS streaming for CyTube
# - Set HLS_ENABLE = True (CyTube supports HLS via application/x-mpegURL)
# - Set HLS_TIME = 6 (standard 6-second segments)
# - Set MINIMUM_RESOLUTIONS_TO_ENCODE = [480] (single quality for storage)
# - Set FFMPEG_DEFAULT_PRESET = "veryfast" (CPU efficiency)
# - Set FFMPEG_H264_PROFILE = "main" (better compression)
# - Set FFMPEG_AUDIO_CODEC = "aac" (required for HLS)
# - Configured for HTTPS delivery (CyTube requirement)
# v0.0.3 - Added FFMPEG_DEFAULT_PRESET = "veryfast"; added 360 to resolutions
# v0.0.2 - Added MINIMUM_RESOLUTIONS_TO_ENCODE to [480]
# v0.0.1 - Changed DO_NOT_TRANSCODE_VIDEO to False
#####

# Stored at: /mediacms/deploy/docker/local_settings.py
# Configuration now centralized in .env file (DOMAIN, CYTUBE_DESCRIPTION, OPENSUBTITLES_*, FFMPEG_*)

import os

# ============================================
# ENVIRONMENT VARIABLE VALIDATION
# ============================================
# Validate required environment variables on module load

DOMAIN = os.environ.get('DOMAIN')
if not DOMAIN:
    raise EnvironmentError(
        "❌ CRITICAL: Missing required environment variable 'DOMAIN' in .env\n"
        "   Please configure DOMAIN in your .env file before starting MediaCMS.\n"
        "   Example: DOMAIN=dev02.420grindhouseserver.com\n"
        "   See .env file MANUAL CONFIGURATION SECTION."
    )

# Validate domain format (basic check)
if DOMAIN.startswith('http://') or DOMAIN.startswith('https://'):
    raise ValueError(
        f"❌ DOMAIN should not include protocol (http:// or https://)\n"
        f"   Current value: {DOMAIN}\n"
        f"   Correct format: example.com or subdomain.example.com"
    )

print(f"✅ Local settings initialized with DOMAIN: {DOMAIN}")

# ============================================
# CORE DJANGO SETTINGS
# ============================================
# Construct FRONTEND_HOST from DOMAIN (HTTPS-only project)
FRONTEND_HOST = os.getenv('FRONTEND_HOST', f'https://{DOMAIN}')

# Load portal name/description from environment
CYTUBE_DESCRIPTION = os.environ.get('CYTUBE_DESCRIPTION', 'Custom MediaCMS streaming server')
PORTAL_NAME = os.getenv('PORTAL_NAME', CYTUBE_DESCRIPTION)

SECRET_KEY = os.getenv('SECRET_KEY', 'ma!s3^b-cw!f#7s6s0m3*jx77a@riw(7701**(r=ww%w!2+yk2')
REDIS_LOCATION = os.getenv('REDIS_LOCATION', 'redis://redis:6379/1')

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('POSTGRES_NAME', 'mediacms'),
        "HOST": os.getenv('POSTGRES_HOST', 'db'),
        "PORT": os.getenv('POSTGRES_PORT', '5432'),
        "USER": os.getenv('POSTGRES_USER', 'mediacms'),
        "PASSWORD": os.getenv('POSTGRES_PASSWORD', 'mediacms'),
        "OPTIONS": {'pool': True},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# CELERY STUFF
BROKER_URL = REDIS_LOCATION
CELERY_RESULT_BACKEND = BROKER_URL

MP4HLS_COMMAND = "/home/mediacms.io/bento4/bin/mp4hls"

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ============================================
# CUSTOM SETTINGS FOR CYTUBE
# ============================================
PORTAL_DESCRIPTION = CYTUBE_DESCRIPTION
TIME_ZONE = "America/Los_Angeles"
DEFAULT_THEME = "dark"
REGISTER_ALLOWED = False
CAN_LIKE_MEDIA = False
CAN_DISLIKE_MEDIA = False
CAN_REPORT_MEDIA = False
MAX_MEDIA_PER_PLAYLIST = 500
ALLOW_MENTION_IN_COMMENTS = True

# django-allauth settings
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
USERS_CAN_SELF_REGISTER = False
GLOBAL_LOGIN_REQUIRED = True

# ============================================
# VIDEO ENCODING SETTINGS (FROM .ENV)
# ============================================
# All encoding settings now centralized in .env file
# These settings normalize all uploads to a consistent streaming format

# CRITICAL: Enable/disable transcoding
# Reads from FFMPEG_TRANSCODE_ENABLED in .env (default: true)
_transcode_enabled = os.environ.get('FFMPEG_TRANSCODE_ENABLED', 'true').lower()
DO_NOT_TRANSCODE_VIDEO = _transcode_enabled != 'true'

# Parse resolution list from .env
# Reads from FFMPEG_RESOLUTIONS in .env (default: 480,720,1080)
_resolutions_str = os.environ.get('FFMPEG_RESOLUTIONS', '480,720,1080')
try:
    MINIMUM_RESOLUTIONS_TO_ENCODE = [int(r.strip()) for r in _resolutions_str.split(',') if r.strip()]
    # Validate resolutions are in acceptable range
    valid_resolutions = [144, 240, 360, 480, 720, 1080, 1440, 2160]
    MINIMUM_RESOLUTIONS_TO_ENCODE = [r for r in MINIMUM_RESOLUTIONS_TO_ENCODE if r in valid_resolutions]
    if not MINIMUM_RESOLUTIONS_TO_ENCODE:
        raise ValueError("No valid resolutions found")
except (ValueError, AttributeError) as e:
    print(f"⚠️  WARNING: Invalid FFMPEG_RESOLUTIONS in .env: {_resolutions_str}")
    print(f"   Error: {e}")
    print(f"   Falling back to default: [480, 720, 1080]")
    MINIMUM_RESOLUTIONS_TO_ENCODE = [480, 720, 1080]

# FFmpeg preset for encoding speed vs quality
# Reads from FFMPEG_PRESET in .env (default: faster)
FFMPEG_DEFAULT_PRESET = os.environ.get('FFMPEG_PRESET', 'faster')
valid_presets = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']
if FFMPEG_DEFAULT_PRESET not in valid_presets:
    print(f"⚠️  WARNING: Invalid FFMPEG_PRESET in .env: {FFMPEG_DEFAULT_PRESET}")
    print(f"   Valid options: {', '.join(valid_presets)}")
    print(f"   Falling back to default: faster")
    FFMPEG_DEFAULT_PRESET = 'faster'

# H.264 profile for compression/compatibility balance
# Reads from FFMPEG_H264_PROFILE in .env (default: main)
FFMPEG_H264_PROFILE = os.environ.get('FFMPEG_H264_PROFILE', 'main')
valid_profiles = ['baseline', 'main', 'high']
if FFMPEG_H264_PROFILE not in valid_profiles:
    print(f"⚠️  WARNING: Invalid FFMPEG_H264_PROFILE in .env: {FFMPEG_H264_PROFILE}")
    print(f"   Valid options: {', '.join(valid_profiles)}")
    print(f"   Falling back to default: main")
    FFMPEG_H264_PROFILE = 'main'

# CRF (Constant Rate Factor) for quality control
# Reads from FFMPEG_CRF_H264 in .env (default: 22)
try:
    FFMPEG_CRF_H264 = int(os.environ.get('FFMPEG_CRF_H264', '22'))
    if not (18 <= FFMPEG_CRF_H264 <= 28):
        raise ValueError(f"CRF must be between 18-28, got {FFMPEG_CRF_H264}")
except (ValueError, TypeError) as e:
    print(f"⚠️  WARNING: Invalid FFMPEG_CRF_H264 in .env: {os.environ.get('FFMPEG_CRF_H264')}")
    print(f"   Error: {e}")
    print(f"   Falling back to default: 22")
    FFMPEG_CRF_H264 = 22

# H.265/HEVC CRF (future codec support)
try:
    FFMPEG_CRF_H265 = int(os.environ.get('FFMPEG_CRF_H265', '28'))
    if not (20 <= FFMPEG_CRF_H265 <= 32):
        raise ValueError(f"H.265 CRF must be between 20-32, got {FFMPEG_CRF_H265}")
except (ValueError, TypeError) as e:
    print(f"⚠️  WARNING: Invalid FFMPEG_CRF_H265 in .env: {os.environ.get('FFMPEG_CRF_H265')}")
    print(f"   Falling back to default: 28")
    FFMPEG_CRF_H265 = 28

# VP9 CRF (future codec support)
try:
    FFMPEG_CRF_VP9 = int(os.environ.get('FFMPEG_CRF_VP9', '32'))
    if not (24 <= FFMPEG_CRF_VP9 <= 40):
        raise ValueError(f"VP9 CRF must be between 24-40, got {FFMPEG_CRF_VP9}")
except (ValueError, TypeError) as e:
    print(f"⚠️  WARNING: Invalid FFMPEG_CRF_VP9 in .env: {os.environ.get('FFMPEG_CRF_VP9')}")
    print(f"   Falling back to default: 32")
    FFMPEG_CRF_VP9 = 32

# CRITICAL: Force AAC audio codec (required for HLS)
# Reads from FFMPEG_AUDIO_CODEC in .env (default: aac)
FFMPEG_AUDIO_CODEC = os.environ.get('FFMPEG_AUDIO_CODEC', 'aac')
valid_audio_codecs = ['aac', 'opus', 'mp3']
if FFMPEG_AUDIO_CODEC not in valid_audio_codecs:
    print(f"⚠️  WARNING: Invalid FFMPEG_AUDIO_CODEC in .env: {FFMPEG_AUDIO_CODEC}")
    print(f"   Valid options: {', '.join(valid_audio_codecs)}")
    print(f"   Falling back to default: aac (required for HLS)")
    FFMPEG_AUDIO_CODEC = 'aac'

# Audio bitrate
# Reads from FFMPEG_AUDIO_BITRATE in .env (default: 128k)
FFMPEG_AUDIO_BITRATE = os.environ.get('FFMPEG_AUDIO_BITRATE', '128k')
# Validate format (must end with 'k')
if not FFMPEG_AUDIO_BITRATE.endswith('k'):
    print(f"⚠️  WARNING: Invalid FFMPEG_AUDIO_BITRATE format in .env: {FFMPEG_AUDIO_BITRATE}")
    print(f"   Format must be: 96k, 128k, 192k, or 256k")
    print(f"   Falling back to default: 128k")
    FFMPEG_AUDIO_BITRATE = '128k'

# ============================================
# HLS STREAMING SETTINGS (FROM .ENV)
# ============================================
# Enable HLS for adaptive streaming with segment-based delivery
# CyTube supports HLS via application/x-mpegURL content type

# CRITICAL: Enable HLS transcoding
# Reads from HLS_ENABLED in .env (default: true)
_hls_enabled = os.environ.get('HLS_ENABLED', 'true').lower()
HLS_ENABLE = _hls_enabled == 'true'

# HLS segment duration in seconds
# Reads from HLS_SEGMENT_TIME in .env (default: 6)
try:
    HLS_TIME = int(os.environ.get('HLS_SEGMENT_TIME', '6'))
    if not (2 <= HLS_TIME <= 10):
        raise ValueError(f"HLS segment time must be between 2-10 seconds, got {HLS_TIME}")
except (ValueError, TypeError) as e:
    print(f"⚠️  WARNING: Invalid HLS_SEGMENT_TIME in .env: {os.environ.get('HLS_SEGMENT_TIME')}")
    print(f"   Error: {e}")
    print(f"   Falling back to default: 6")
    HLS_TIME = 6

# Additional HLS optimization flags
# Reads from HLS_FLAGS in .env (default: independent_segments)
FFMPEG_HLS_FLAGS = os.environ.get('HLS_FLAGS', 'independent_segments')

# ============================================
# ENCODING CONFIGURATION SUMMARY (LOGGING)
# ============================================
# Log the complete encoding configuration on startup for troubleshooting
print("\n" + "="*80)
print("🎬 FFMPEG ENCODING CONFIGURATION (from .env)")
print("="*80)
print(f"Transcoding Enabled: {not DO_NOT_TRANSCODE_VIDEO}")
print(f"Target Resolutions: {MINIMUM_RESOLUTIONS_TO_ENCODE}")
print(f"Encoding Preset: {FFMPEG_DEFAULT_PRESET}")
print(f"H.264 Profile: {FFMPEG_H264_PROFILE}")
print(f"H.264 CRF: {FFMPEG_CRF_H264} (lower = better quality, larger files)")
print(f"H.265 CRF: {FFMPEG_CRF_H265} (future codec support)")
print(f"VP9 CRF: {FFMPEG_CRF_VP9} (future codec support)")
print(f"Audio Codec: {FFMPEG_AUDIO_CODEC}")
print(f"Audio Bitrate: {FFMPEG_AUDIO_BITRATE}")
print(f"\n📺 HLS STREAMING CONFIGURATION")
print(f"HLS Enabled: {HLS_ENABLE}")
print(f"Segment Duration: {HLS_TIME} seconds")
print(f"HLS Flags: {FFMPEG_HLS_FLAGS}")
print("="*80 + "\n")

# ============================================
# UPLOAD SETTINGS
# ============================================
# Maximum number of media a user can upload
NUMBER_OF_MEDIA_USER_CAN_UPLOAD = 1000
USER_CAN_TRANSCRIBE_VIDEO = True

# Chunked upload settings for large files (2-8GB videos)
UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
UPLOAD_CHUNKS = True
UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks
CHUNK_UPLOAD_TIMEOUT = 7200  # 2 hours

# ============================================
# OPENSUBTITLES API CONFIGURATION
# ============================================
# Automatic subtitle fetching from OpenSubtitles.com REST API
# Triggered after video encoding completes via Django post_save signal

# API Authentication (JWT Token Method - RECOMMENDED)
OPENSUBTITLES_API_KEY = os.environ.get('OPENSUBTITLES_API_KEY', '')
OPENSUBTITLES_JWT_TOKEN = os.environ.get('OPENSUBTITLES_JWT_TOKEN', '')
OPENSUBTITLES_API_URL = os.environ.get('OPENSUBTITLES_API_URL', 'https://api.opensubtitles.com/api/v1')
OPENSUBTITLES_USER_AGENT = os.environ.get('OPENSUBTITLES_USER_AGENT', 'MediaCMS-CyTube/1.0')

# Feature Toggles
OPENSUBTITLES_ENABLED = os.environ.get('OPENSUBTITLES_ENABLED', 'false').lower() == 'true'
OPENSUBTITLES_AUTO_DOWNLOAD = os.environ.get('OPENSUBTITLES_AUTO_DOWNLOAD', 'true').lower() == 'true'

# Search Configuration
OPENSUBTITLES_LANGUAGES = os.environ.get('OPENSUBTITLES_LANGUAGES', 'en').split(',')
OPENSUBTITLES_MAX_RESULTS = int(os.environ.get('OPENSUBTITLES_MAX_RESULTS', '10'))

# Subtitle Storage Path - MUST use container path, not host path
# Host path: /mnt/ebs/mediacms_media/original/subtitles
# Container path: /home/mediacms.io/mediacms/media_files/original/subtitles
# MediaCMS serves from /media/original/subtitles/ URL
OPENSUBTITLES_DOWNLOAD_PATH = '/home/mediacms.io/mediacms/media_files/original/subtitles'
