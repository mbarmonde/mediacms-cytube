# dev-v0.2.4

#####
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
# Configuration now centralized in .env file (DOMAIN, CYTUBE_DESCRIPTION, OPENSUBTITLES_*)

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
# VIDEO ENCODING SETTINGS
# ============================================
# These settings normalize all uploads to a consistent streaming format

# CRITICAL: Enable transcoding for HLS generation
DO_NOT_TRANSCODE_VIDEO = False

# Encode 480p, 720p, and 1080p for adaptive bitrate streaming
# Smart encode will skip resolutions higher than source resolution
MINIMUM_RESOLUTIONS_TO_ENCODE = [480, 720, 1080]

# Use faster or veryfast preset for CPU efficiency (reduces CPU usage ~35%)
# faster or veryfast is recommended for streaming; medium and slower use too much CPU; https://superuser.com/questions/490683/cheat-sheets-and-preset-settings-that-actually-work-with-ffmpeg-1-0/1825118#1825118
FFMPEG_DEFAULT_PRESET = "faster"

# Use 'main' profile for better compression than 'baseline'
# Main profile works on all modern devices and saves ~10-15% bitrate
FFMPEG_H264_PROFILE = "main"

# Use CRF (Constant Rate Factor) for quality-based encoding
# CRF 23 is the default - good quality with reasonable file sizes
FFMPEG_CRF = 21

# CRITICAL: Force AAC audio codec (required for HLS)
# This ensures all videos have compatible audio regardless of source
FFMPEG_AUDIO_CODEC = "aac"

# Audio bitrate (128k is standard for streaming)
FFMPEG_AUDIO_BITRATE = "128k"

# ============================================
# HLS STREAMING SETTINGS
# ============================================
# Enable HLS for adaptive streaming with segment-based delivery
# CyTube supports HLS via application/x-mpegURL content type

# CRITICAL: Enable HLS transcoding
# CyTube accepts HLS VOD (video on demand) streams
HLS_ENABLE = True

# Standard 6-second segments per Apple HLS specifications
# Shorter segments = faster startup and quality switching
HLS_TIME = 6

# Additional HLS optimization flags
# These ensure proper segment boundaries and playlist generation
FFMPEG_HLS_FLAGS = "independent_segments"

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


