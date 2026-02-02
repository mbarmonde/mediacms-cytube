# dev-v0.1.1

#####
# v0.1.1 - Chunk fixes for uploads
# -  UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
#  - FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
#  - DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
#  - UPLOAD_CHUNKS = True
#  - UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks
#  - CHUNK_UPLOAD_TIMEOUT = 7200  # 2 hours
# v0.1.0 - MAJOR UPDATE: Enabled HLS streaming for CyTube
#   - Set HLS_ENABLE = True (CyTube supports HLS via application/x-mpegURL)
#   - Set HLS_TIME = 6 (standard 6-second segments)
#   - Set MINIMUM_RESOLUTIONS_TO_ENCODE = [480] (single quality for storage)
#   - Set FFMPEG_DEFAULT_PRESET = "veryfast" (CPU efficiency)
#   - Set FFMPEG_H264_PROFILE = "main" (better compression)
#   - Set FFMPEG_AUDIO_CODEC = "aac" (required for HLS)
#   - Configured for HTTPS delivery (CyTube requirement)
# v0.0.3 - Added FFMPEG_DEFAULT_PRESET = "veryfast"; added 360 to resolutions
# v0.0.2 - Added MINIMUM_RESOLUTIONS_TO_ENCODE to [480]
# v0.0.1 - Changed DO_NOT_TRANSCODE_VIDEO to False
#####

# Stored at: /mediacms/deploy/docker/local_settings.py
# Find Replace dev.420grindhouseserver.com
# Find Replace 420 Grindhouse Dev Server

import os

FRONTEND_HOST = os.getenv('FRONTEND_HOST', 'https://dev.420grindhouseserver.com')  # HTTPS required
PORTAL_NAME = os.getenv('PORTAL_NAME', '420 Grindhouse Dev Server')
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

# Custom Settings for CyTube via cms/settings.py
PORTAL_DESCRIPTION = "420 Grindhouse Dev Server"
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

# ===== VIDEO ENCODING SETTINGS =====
# These settings normalize all uploads to a consistent streaming format

# CRITICAL: Enable transcoding for HLS generation
DO_NOT_TRANSCODE_VIDEO = False

# Encode only 480p to save storage and CPU resources
# With 140GB storage and 100+ users, single quality is optimal
MINIMUM_RESOLUTIONS_TO_ENCODE = [480]

# Use veryfast preset for CPU efficiency (reduces CPU usage ~35%)
# veryfast is recommended for streaming; medium and slower use too much CPU
FFMPEG_DEFAULT_PRESET = "veryfast"

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

# ===== HLS STREAMING SETTINGS =====
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

# Maximum number of media a user can upload
NUMBER_OF_MEDIA_USER_CAN_UPLOAD = 1000
USER_CAN_TRANSCRIBE_VIDEO = True

# Chunked upload timeout fix
#CHUNK_UPLOAD_TIMEOUT = 7200
#UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024
#FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
UPLOAD_CHUNKS = True
UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks
CHUNK_UPLOAD_TIMEOUT = 7200  # 2 hours
