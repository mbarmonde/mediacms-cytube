# Dev-Branch MediaCMS for CyTube (MediaCMS 7.7) - Updated 2/21/2026

[![GitHub license](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://raw.githubusercontent.com/mediacms-io/mediacms/main/LICENSE.txt)
[![Releases](https://img.shields.io/github/v/release/mediacms-io/mediacms?color=green)](https://github.com/mediacms-io/mediacms/releases/)
[![DockerHub](https://img.shields.io/docker/pulls/mediacms/mediacms)](https://hub.docker.com/r/mediacms/mediacms)

[Main branch that's validated for MediaCMS 7.7 is here](https://github.com/mbarmonde/mediacms-cytube/tree/main)

## Table of Contents

- [Dev-Branch MediaCMS for CyTube (MediaCMS 7.7) - Updated 2/21/2026](#dev-branch-mediacms-for-cytube-mediacms-77-updated-2212026)
- [What is MediaCMS for CyTube?](#what-is-mediacms-for-cytube)
- [MediaCMS for CyTube Quick Start](#mediacms-for-cytube-quick-start)
  - [Deployment Checklist](#deployment-checklist)
- [Help, Troubleshooting, General Information](#help-troubleshooting-general-information)
  - [MediaCMS for CyTube Key Changes](#mediacms-for-cytube-key-changes)
  - [Video Workflow for CyTube](#video-workflow-for-cytube)
  - [First Video Upload Test](#-first-video-upload-test)
  - [Verify Subtitle Languages](#verify-subtitle-languages)
  - [Example JSON Payload](#example-json-payload)
  - [System Architecture](#system-architecture)
  - [MediaCMS for CyTube Stack](#mediacms-for-cytube-stack)
  - [MediaCMS for CyTube Change-File List](#mediacms-for-cytube-change-file-list)
  - [MediaCMS for CyTube Storage Architecture for Block Storage](#mediacms-for-cytube-storage-architecture-for-block-storage)
  - [Common Operations](#common-operations)
  - [Troubleshooting](#troubleshooting)
  - [Performance Tuning](#performance-tuning)
  - [Enable Huge Files (>5GB)](#enable-huge-files-5gb)
  - [Security Best Practices](#security-best-practices)
- [Dev Session Logs](#dev-session-logs)
  - [Session: Feb 21, 2026 — Missing Migration Fix + Deploy-Time Drift Guard](#session-feb-21-2026--missing-migration-fix--deploy-time-drift-guard)
  - [Session: Feb 17, 2026 — Storage Hardcode Fix + GPU Encoding Infrastructure](#session-feb-17-2026--storage-hardcode-fix--gpu-encoding-infrastructure)

  Infrastructure](#session-feb-17-2026--storage-hardcode-fix--gpu-encoding-infrastructure)
- [Looking for the Original MediaCMS?](#looking-for-the-original-mediacms)
  - [Plug in!](#plug-in)
  - [Contact](#contact)

---

# What is MediaCMS for CyTube?

[CyTube](https://github.com/calzoneman/sync) is a Reddit-like series of user-registered channels where connected viewers watch videos from different video hosts (e.g., YouTube, Twitch, Customer server) and the playback is synchronized for all the viewers in the channel. Each channel has a playlist where users can queue up videos to play, as well as an integrated chatroom for discussion. Channel capabilities includes owners and moderators in various roles with emotes (gifs), and CSS customization.

[MediaCMS](https://github.com/mediacms-io/mediacms) provides a private repository for video content used as a YouTube replacement to stream, manage, and encode videos with RBAC and various features.

**MediaCMS for CyTube** modifies MediaCMS for instant sharing of video content to CyTube via an accepted .JSON file for CyTube playlists. In one click, an encoded video in MediaCMS can be copied and pasted in a playlist to start showing.

---

# MediaCMS for CyTube Quick Start

> **Note:** The default storage path is `/mnt/ebs/mediacms_media`. If using a different path, update `MEDIA_FILES_PATH` in `.env`. The database is stored at `/postgres_data`. Removing these files and the `/mediacms` directory completely cleans the server.

1. Clone the repo branch of your choice to a root folder called `/mediacms`

**Main:**
```bash
git clone https://github.com/mbarmonde/mediacms-cytube /mediacms
```

**Dev:**
```bash
git clone --branch dev https://github.com/mbarmonde/mediacms-cytube /mediacms
```

2. Modify `.env` and find/replace the values below (note the optional inputs)

```bash
nano .env

# ============================================
# DEPLOYMENT CONFIGURATION (HTTPS-ONLY)
# ============================================
# Find and Replace YOUR DOMAIN NAME, 1ea
# Example: dev02.420grindhouseserver.com (no https:// prefix)
DOMAIN=YOUR.DOMAIN.NAME

# ============================================
# ADMIN CREDENTIALS
# ============================================
# Find and Replace SUPERADMIN USERNAME, 1ea
# Find and Replace SUPERADMIN EMAIL, 1ea
# Find and Replace SUPERADMIN PASSWORD, 1ea
ADMIN_USER=SUPERADMIN USERNAME
ADMIN_EMAIL=SUPERADMIN EMAIL
ADMIN_PASSWORD=SUPERADMIN PASSWORD

# ============================================
# CYTUBE INTEGRATION METADATA
# ============================================
# Find and Replace CYTUBE DESCRIPTION, 1ea (optional - has default)
# NOTE: Use quotes for values containing spaces
CYTUBE_DESCRIPTION="Custom MediaCMS streaming server for CyTube integration"
CYTUBE_ORGANIZATION="MediaCMS-CyTube"

# ============================================
# OPENSUBTITLES.COM API CONFIGURATION
# ============================================

# Enable/disable automatic subtitle fetching (true/false)
# Set to false to disable entire feature without code changes
OPENSUBTITLES_ENABLED=true

# API Key from opensubtitles.com (consumer key)
OPENSUBTITLES_API_KEY=YOU_API_KEY

# Personal JWT token from OpenSubtitles.com profile (REQUIRED)
# Get from: https://www.opensubtitles.com (Settings/API section)
OPENSUBTITLES_JWT_TOKEN=YOUR_PERMANENT_JWT_TOKEN_HERE

# ============================================
# STORAGE PATHS
# ============================================
# Where videos, subtitles, and encoded movies are stored - usually a large extent
MEDIA_FILES_PATH=/mnt/ebs/mediacms_media
```

3. Make the validate script executable and run validation. If validation fails, fix the errors shown and run again.

```bash
chmod +x validate-env.sh
./validate-env.sh
```

4. Run the init script — starts Docker containers and makes all scripts executable

```bash
chmod +x cytube-execute-all-sh-and-storage-init.sh
./cytube-execute-all-sh-and-storage-init.sh

# This script:
# ✅ Validates your configuration
# ✅ Makes all scripts executable
# ✅ Initializes storage structure
# ✅ Starts Docker containers
# ✅ Waits for database to be ready
# ✅ Populates 20 subtitle languages
```

5. Check for running, healthy containers and access your site:

```bash
docker-compose ps

# NAME                     STATUS
# media_cms                Up (healthy)
# mediacms_caddy           Up
# mediacms_celery_beat     Up
# mediacms_celery_worker   Up
# mediacms_db              Up (healthy)
# mediacms_redis           Up (healthy)

curl -I https://yourdomain.com
# Expected: HTTP/2 200 or HTTP/2 302
```

## Deployment Checklist

Before going live, verify:

- DNS resolves correctly (`nslookup yourdomain.com`)
- Ports 80/443 are open
- `.env` file configured with real values
- `validate-env.sh` passes
- Extended mount point configured at `/mnt/ebs` (or custom path set via `MEDIA_FILES_PATH` in `.env`) — size guideline: multiply expected uploaded video size by 3 (original + encoded + HLS)
- All containers show `Up` status
- HTTPS certificate generated (check browser)
- Can login to web interface
- Test video uploads and encodes successfully
- CyTube manifest generates and plays
- Subtitle languages populated (20 languages)
- Firewall rules configured
- Backup script created and tested

---

# Help, Troubleshooting, General Information

## MediaCMS for CyTube Key Changes

This fork of MediaCMS features integration for CyTube, including:

- **GPU Encoding Infrastructure (Forward-Looking)** — Added `ENCODING_BACKEND` toggle (`cpu`|`gpu`) and `docker-compose.gpu.yml` compose overlay for NVIDIA NVENC hardware encoding. GPU path is fully dormant by default (`ENCODING_BACKEND=cpu`). CPU encoding behavior is unchanged. — Added 02/17/2026
- **Storage Path Fully Configurable via `.env`** — `init_validate_storage.sh` now reads `MEDIA_FILES_PATH` from `.env` with `/mnt/ebs/mediacms_media` as fallback. All `/mnt/ebs` hardcodes removed. Any host path is supported. — Added 02/17/2026
- **Subtitles Offset in UI** — (edit video > Captions) Subtitle Timing Offset (seconds) — Adjust subtitle timing: negative delays subtitles (e.g., -4.5), positive advances them. Changes auto-refresh subtitles. — Added 02/15/2026
- **Subtitles from OpenSubtitles.com Dev API** — Use `.env` file to set variables, upload a movie, rename it to ensure it's found (`movie-name.year`) — Added 02/14/2026
- **Auto Subtitles from OpenSubtitles.com** — Use `.env` file to set variables, upload a movie, rename it to ensure it's found (`movie-name.year`) — Added 02/14/2026
- **All-in-One Setup Script** — Use `.env` file to set variables for the project and run a single script to get things going — Added 02/09/2026
- **Subtitle Inclusion** — Via native MediaCMS processes and included with the JSON payload for CyTube — Added 02/09/2026
- **Adaptive Bitrate Streaming** — Enabled 480p, 720p, and 1080p encoding with adaptive bitrate streaming for CyTube. MediaCMS encodes all uploads to H.264 HLS with 6-second segments using `veryfast` preset — Added 02/06/2026
- **Smart Encode** — Dynamically enable/disable encoding profiles based on source video resolution to prevent unnecessary upscaling and optimize storage/CPU usage — Added 02/06/2026
- **CyTube Integration** — Custom API generates CyTube-compatible JSON manifests with `application/x-mpegURL` content type per [CyTube best practices](https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md)
- **Real-time Encoding Status Widget** — JavaScript widget (v1.7) displays encoding progress with ETA calculation, auto-updates every 3 seconds, shows "Ready for Export to CyTube!" when complete
- **Automated Encoding Profile Setup** — Enables only 480p, 720p, 1080p and Preview encoding profiles, disabling the rest, but uses Smart Encode to save space
- **One-click Export Button** — Floating button on video pages copies CyTube manifest URL to clipboard
- **Block Storage Integration** — All media stored with proper volume mounts (configurable via `MEDIA_FILES_PATH` in `.env`)
- **Automated Container Health** — Healthcheck script automatically configures nginx (removes CORS conflicts, sets upload timeouts) and activates encoding profiles on every Docker restart/recreation — self-healing
- **Large File Upload Support** — Handles 2–8GB files with 10GB max size, 2-hour timeout for chunk finalization

## Video Workflow for CyTube

```
1. User uploads video.mkv to MediaCMS web interface
   ↓
2. Celery worker detects new upload
   ↓
3. FFmpeg encoding begins (Smart Encode checks source resolution)
   ├─→ Source 480p: Encodes only 480p (saves space)
   ├─→ Source 720p: Encodes 480p + 720p
   └─→ Source 1080p: Encodes 480p + 720p + 1080p
   ↓
4. HLS segments generated (6-second chunks)
   ├─→ Saved to: /mnt/ebs/mediacms_media/hls/{hash}/
   └─→ Creates: master.m3u8 + variant playlists
   ↓
5. Auto subtitle fetch based on title name from OpenSubtitles.com*
   ├─→ Fetches and creates: {hash}.vtt
   └─→ Saved to: /mnt/ebs/mediacms_media/original/subtitles/user/(username)/{hash}.vtt
   ↓
6. User clicks "Export to CyTube" button on video page
   ↓
7. custom_api.py generates CyTube manifest JSON
   ├─→ Detects available resolutions
   ├─→ Includes subtitle tracks (if uploaded)
   └─→ Saves to: /mnt/ebs/mediacms_media/cytube_manifests/
   ↓
8. User pastes manifest URL in CyTube
   ↓
9. CyTube fetches JSON, parses sources array
   ↓
10. Video player loads HLS stream with quality selector
    ├─→ Users can switch between 480p/720p/1080p in real-time
    └─→ Users can choose to turn on subtitles

*Can be disabled via .env: OPENSUBTITLES_AUTO_DOWNLOAD=false
```

## 🎬 First Video Upload Test

- **Upload a Test Video**
  Navigate to: `https://yourdomain.com/upload`
  Upload a video file (MP4, MKV, AVI, etc.)
  Wait for encoding to complete (check progress bar)

- **Generate CyTube Manifest**
  Once encoding completes:
  - Go to the video page
  - Click the "Export to CyTube" button (floating blue button)
  - Manifest URL is copied to clipboard
  - Manifest URL format: `https://yourdomain.com/media/custom/XXXXX_VideoTitle.json`

- **Test in CyTube**
  - Click Add Video from URL
  - Paste the manifest URL
  - Video should play with quality selector (480p/720p/1080p)

## Verify Subtitle Languages

```bash
docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT COUNT(*) FROM files_language;"
```

## Example JSON Payload

Here is an example `.json` manifest file encoded dynamically based on native resolutions for CyTube, publicly accessible at `https://YOUR.DOMAIN.COM/media/custom/(manifest).json`:

```json
{
  "title": "Moonraker.(1979)",
  "duration": 7589,
  "live": false,
  "thumbnail": "https://YOUR.DOMAIN.COM/media/original/thumbnails/user/superadmin02/979a61dd99a14e8f9924d3857f2ea422_xjNM67n.Moonraker.1979.mkv.jpg",
  "sources": [
    {
      "url": "https://YOUR.DOMAIN.COM/media/hls/979a61dd99a14e8f9924d3857f2ea422/master.m3u8",
      "contentType": "application/x-mpegURL",
      "quality": 480
    },
    {
      "url": "https://YOUR.DOMAIN.COM/media/hls/979a61dd99a14e8f9924d3857f2ea422/master.m3u8",
      "contentType": "application/x-mpegURL",
      "quality": 720
    }
  ],
  "textTracks": [
    {
      "url": "https://YOUR.DOMAIN.COM/media/original/subtitles/user/superadmin02/Moonraker.1979.720p.BRRip.x264.AAC-ViSiON.srt",
      "contentType": "text/vtt",
      "name": "English"
    }
  ],
  "meta": {
    "description": "",
    "streaming_method": "hls_adaptive_2_resolutions",
    "media_hash": "979a61dd99a14e8f9924d3857f2ea422",
    "subtitle_count": 1
  }
}
```

## System Architecture

```
User Request (HTTPS)
  ↓
Caddy Reverse Proxy (Port 443)
  ├─→ Static Files → /media/* files
  ├─→ HLS Streams → /media/hls/* (adaptive bitrate)
  ├─→ Subtitles → /media/original/subtitles/*
  ├─→ Manifests → /media/custom/*.json
  └─→ Django Web App (uWSGI)
       ├─→ PostgreSQL Database (metadata)
       ├─→ Redis Cache (sessions)
       └─→ Celery Workers (encoding)
            └─→ FFmpeg (video transcoding)
```

## MediaCMS for CyTube Stack

| Component | Version | Purpose |
|---|---|---|
| MediaCMS | 7.7 | Video management & encoding platform |
| Celery | Latest | Distributed task queue for async background processing |
| Caddy | 2.10.2 | Reverse proxy with HLS optimization |
| PostgreSQL | 17.2 | Database |
| Redis | Alpine | Caching & Celery broker |
| Docker Compose | Latest | Container orchestration |

## MediaCMS for CyTube Change-File List

```
=== DEVELOPMENT VERSIONS (dev-vX.X.X) ===

├── .env                                          # dev-v0.4.0
caddy/
│   ├── Caddyfile                                 # dev-v0.4.0
cms/
│   ├── urls.py                                   # dev-v0.1.0
├── custom_api.py                                 # dev-v0.6.0
├── custom_urls.py                                # dev-v0.1.3
├── cytube-execute-all-sh-and-storage-init.sh     # dev-v0.3.0
deploy/
│   ├── docker/
│   │   ├── local_settings.py                     # dev-v0.4.0
│   │   ├── nginx_http_only.conf                  # dev-v0.1.0
├── docker-compose.gpu.yml                        # dev-v0.1.0  ← NEW
├── docker-compose.yaml                           # dev-v0.4.1
files/
│   ├── forms.py                                  # dev-v0.1.3
│   ├── helpers.py                                # dev-v0.2.0
│   ├── models/
│   │   ├── media.py                              # dev-v0.1.9
│   ├── tasks.py                                  # dev-v0.1.3
│   ├── views/
│   │   ├── pages.py                              # dev-v0.1.0
├── monitor-mediacms-uploads.sh                   # dev-v0.2.0
scripts/
│   ├── docker-healthcheck.sh                     # dev-v0.5.3
│   ├── init_subtitle_languages.sh                # dev-v0.1.3
│   ├── init_validate_storage.sh                  # dev-v0.1.2
static/
│   ├── js/
│   │   ├── cytube-export.js                      # dev-v0.1.0
│   │   ├── encoding-status.js                    # dev-v0.1.7
├── subtitle_fetcher.py                           # dev-v0.1.7
templates/
│   ├── root.html                                 # dev-v0.1.0
├── test_opensubtitles.py                         # dev-v0.1.2
├── test_subtitle_fetcher_standalone.py           # dev-v0.1.0
├── validate-env.sh                               # dev-v0.3.0
```

## MediaCMS for CyTube Storage Architecture for Block Storage

> **Note:** The default is `/mnt/ebs/mediacms_media`. If using a different path, update `MEDIA_FILES_PATH` in `.env`.

```
Host: /mnt/ebs/mediacms_media/     ← or custom MEDIA_FILES_PATH value
  ├── chunks/             # Temp encoded chunks
  ├── cytube_manifests/   # Generated JSON manifests
  ├── encoded/            # Encoded video files
  ├── encodings/          # Temp encoded video files
  ├── hls/                # HLS segments (hash-based directories)
  ├── original/           # Uploaded files / subtitles
  ├── thumbnails/         # Video thumbnails
  ├── uploads/            # Temp uploaded content
  └── userlogos/          # User avatars

Container: /home/mediacms.io/mediacms/media_files/ (mounted from above via docker-compose.yaml)
```

## Common Operations

**View Logs**
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f media_cms
docker-compose logs -f mediacms_celery_worker
docker-compose logs -f mediacms_caddy
```

**Restart Services**
```bash
# Restart all containers
docker-compose restart

# Restart specific container
docker-compose restart media_cms
```

**Stop Services**
```bash
docker-compose down
```

**Update MediaCMS**
```bash
# Stop containers
docker-compose down

# Pull latest images
docker-compose pull

# Restart with new images
./cytube-execute-all-sh-and-storage-init.sh
```

**Check Storage Usage**
```bash
# Media files
du -sh /mnt/ebs/mediacms_media/*

# Database
docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT pg_size_pretty(pg_database_size('mediacms'));"
```

## Troubleshooting

**Problem: Caddy won't start — "unrecognized global option"**
Cause: `DOMAIN` environment variable not passed to Caddy container
```bash
# Check docker-compose.yaml has environment section for caddy
grep -A 3 "caddy:" docker-compose.yaml | grep -A 2 "environment:"
# Should show:
# environment:
#   - DOMAIN=${DOMAIN}

docker-compose down && docker-compose up -d
```

**Problem: Python containers fail with "Missing required environment variable 'DOMAIN'"**
Cause: `DOMAIN` not passed to web/celery containers
```bash
# Verify docker-compose.yaml v0.3.9+
head -n 1 docker-compose.yaml
# Should show: # dev-v0.3.9

docker-compose down && docker-compose up -d
```

**Problem: SSL certificate not generating**
Cause: DNS not propagated or ports 80/443 blocked
```bash
nslookup yourdomain.com
sudo netstat -tulpn | grep -E ':80|:443'
docker-compose logs caddy | grep -i "certificate"
# Wait 5-10 minutes for Let's Encrypt retry
```

**Problem: Videos not encoding**
Cause: Celery worker not running or encoding profiles disabled
```bash
docker-compose logs mediacms_celery_worker | tail -20
docker-compose restart mediacms_celery_worker
```

**Problem: Upload fails with timeout**
Cause: File too large or network timeout
```bash
docker exec media_cms grep "UPLOAD_MAX_SIZE" /home/mediacms.io/mediacms/deploy/docker/local_settings.py
# Should show: UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

# If uploading >8GB, increase timeouts in Caddyfile
nano caddy/Caddyfile
```

**Problem: Subtitle languages missing**
Cause: Database initialization didn't run
```bash
./scripts/init_subtitle_languages.sh

# Verify
docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT code, title FROM files_language ORDER BY title;"
# Should show 20 languages
```

**Problem: CyTube manifest returns 404**
Cause: Video encoding not complete or manifest not generated
```bash
docker-compose logs media_cms | grep "Encoding status"

# Check if manifest file exists
ls -la /mnt/ebs/mediacms_media/cytube_manifests/
```

## Performance Tuning

**For High Traffic (100+ concurrent users)**

Edit `docker-compose.yaml`:
```yaml
web:
  deploy:
    replicas: 2

celery_worker:
  deploy:
    replicas: 2
```

Then restart:
```bash
docker-compose up -d --scale web=2 --scale celery_worker=2
```

## Enable Huge Files (>5GB)

Edit `caddy/Caddyfile`:
```
# Increase timeouts
read_timeout 7200s
write_timeout 7200s
response_header_timeout 7200s
```

Then restart:
```bash
docker-compose restart caddy
```

## Security Best Practices

**1. Change Default Passwords**
```bash
nano .env
# Change ADMIN_PASSWORD to 16+ character password
```

**2. Restrict User Registration**

Already configured in `local_settings.py`:
```python
REGISTER_ALLOWED = False
USERS_CAN_SELF_REGISTER = False
GLOBAL_LOGIN_REQUIRED = True
```

**3. Enable Firewall**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**4. Regular Backups**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/mediacms"
mkdir -p $BACKUP_DIR

# Backup database
docker exec mediacms_db pg_dump -U mediacms mediacms | gzip > $BACKUP_DIR/db-$DATE.sql.gz

# Backup .env
cp /mediacms/.env $BACKUP_DIR/env-$DATE

# Backup media (incremental)
rsync -av --progress /mnt/ebs/mediacms_media/ $BACKUP_DIR/media/

echo "Backup complete: $BACKUP_DIR"
```

---

# Dev Session Logs

Full implementation notes for each development session. Most recent first.

---

## Session: Feb 21, 2026 — Missing Migration Fix + Deploy-Time Drift Guard

> **Scope:** Production bug fix — upload 500 error caused by uncommitted migration. Added permanent structural guard to prevent recurrence on all future deploys.
> **Severity:** P0 — uploads completely broken on affected instance.

### Root Cause

```
ERROR: column files_media.subtitle_timing_offset does not exist
```

`subtitle_timing_offset` was added to `files/models/media.py` (dev-v0.1.3) but `makemigrations` was never run, so no migration file was generated or committed. On the running instance the column existed (added manually at some point), but any fresh deploy would hit the same crash immediately.

The failure chain:
```
Django queries files_media including subtitle_timing_offset
  → Postgres: column does not exist → 500
  → Fine Uploader: POST /fu/upload/?done returns 500
  → Fine Uploader retries 3x → 400 (duplicate finalize attempt)
  → Upload fails with "Error with File Uploading"
```

The 400s and Fine Uploader stack traces in the browser console were noise — the only signal that mattered was the single Postgres line in `docker-compose logs`.

### Diagnosis Steps

```bash
# Step 1: Confirmed all existing migrations were applied (no unapplied boxes)
docker exec media_cms python manage.py showmigrations files
# Result: 0001-0014 all [X] — State B (migration file simply didn't exist)

# Step 2: Confirmed column was present in DB (added outside Django's knowledge)
docker exec mediacms_db psql -U mediacms -d mediacms \
  -c "\d files_media" | grep subtitle
# Result: subtitle_timing_offset | double precision | not null
```

### Fix

```bash
# Generate the missing migration
docker exec media_cms python manage.py makemigrations files \
  --name "add_subtitle_timing_offset"
# Result: files/migrations/0015_add_subtitle_timing_offset.py created

# Apply it (marks it as applied in Django's migration history)
docker exec media_cms python manage.py migrate files
# Result: No migrations to apply (column already existed — correct)

# Copy migration file out of container into working tree
docker cp media_cms:/home/mediacms.io/mediacms/files/migrations/0015_add_subtitle_timing_offset.py \
  /mediacms/files/migrations/0015_add_subtitle_timing_offset.py

# Restart web container
docker-compose restart media_cms
```

### Permanent Guard — `cytube-execute-all-sh-and-storage-init.sh` dev-v0.4.0

A new **Step 5.5** was added between container health checks and subtitle initialization. It runs `makemigrations --check` inside the running `media_cms` container. This command exits non-zero if any model change exists without a corresponding migration file, and zero if everything is in sync.

**On a clean deploy (normal case):**
```
STEP 5.5: Checking for missing migrations...
✅ All model migrations are present and accounted for
```

**On drift detected (model changed, migration not committed):**
```
STEP 5.5: Checking for missing migrations...

========================================
❌ MIGRATION DRIFT DETECTED
========================================

One or more model changes have no corresponding migration file.
This will cause 500 errors at runtime when the missing column is queried.

To fix:
  1. Generate the missing migration:
     docker exec media_cms python manage.py makemigrations

  2. Copy it out of the container:
     docker cp media_cms:/home/mediacms.io/mediacms/<app>/migrations/<file>.py \
       /mediacms/<app>/migrations/<file>.py

  3. Apply it:
     docker exec media_cms python manage.py migrate

  4. Commit the migration file to the repo before next deploy

Startup aborted. Fix migration drift and re-run this script.
```

Startup is fully blocked — the server never goes live in a broken state.

### Files Changed

| File | From | To | Type |
|---|---|---|---|
| `files/migrations/0015_add_subtitle_timing_offset.py` | *(missing)* | **new file** | Bug fix |
| `cytube-execute-all-sh-and-storage-init.sh` | dev-v0.3.0 | **dev-v0.4.0** | Guard added |

### Migration Workflow — Correct Process Going Forward

Any time a new field is added to any model, this sequence must be followed before committing:

```
1. Add field to model file
2. Generate migration:
   docker exec media_cms python manage.py makemigrations
3. Copy migration file out of container:
   docker cp media_cms:/home/mediacms.io/mediacms/<app>/migrations/<new_file>.py \
     /mediacms/<app>/migrations/<new_file>.py
4. Commit BOTH the model change AND the migration file in the same commit
5. On fresh deploy: migrate runs automatically on container startup,
   Step 5.5 confirms sync before any schema-dependent code runs
```

If step 4 is skipped, Step 5.5 will catch it on the next deploy and block startup with instructions.

---

## Session: Feb 17, 2026 — Storage Hardcode Fix + GPU Encoding Infrastructure

> **Scope:** Bug fix in `init_validate_storage.sh` + forward-looking GPU encoding infrastructure across 5 files + 1 new file.
> **Server state at time of session:** No GPU present. CPU encoding active. All GPU code dormant by default (`ENCODING_BACKEND=cpu`).

### Files Changed

| File | From | To | Type |
|---|---|---|---|
| `scripts/init_validate_storage.sh` | dev-v0.1.1 | **dev-v0.1.2** | Bug fix |
| `.env` | dev-v0.3.0 | **dev-v0.4.0** | New variables |
| `deploy/docker/local_settings.py` | dev-v0.3.0 | **dev-v0.4.0** | New settings |
| `files/helpers.py` | dev-v0.1.0 | **dev-v0.2.0** | GPU encoder path |
| `validate-env.sh` | dev-v0.2.0 | **dev-v0.3.0** | New validation section |
| `docker-compose.gpu.yml` | *(new)* | **dev-v0.1.0** | New file |

---

### Part A — `init_validate_storage.sh` dev-v0.1.2

#### Bug: `tr` Quote-Strip Crash

`tr -d '"'"'"'` multi-layer quoting was corrupted on copy, producing:

```
tr: extra operand '})\\n    echo "   Total size: $TOTAL_SIZE"...'
/mediacms/scripts/init_validate_storage.sh: line 294: syntax error near unexpected token `fi'
```

**Fix:** Replaced with a `sed` pipeline requiring no nested quoting:

```bash
# Before (broken)
VALUE=$(grep '^KEY=' .env | cut -d'=' -f2- | tr -d '"'"'"')

# After (fixed)
VALUE=$(grep -E '^KEY=' .env | head -1 | cut -d'=' -f2- \
    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//')
```

This pattern is used for both `MEDIA_FILES_PATH` and `DOMAIN` reads in the script.

#### Additional Changes in dev-v0.1.2

- `EBS_PATH` now sourced from `MEDIA_FILES_PATH` in `.env` (falls back to `/mnt/ebs/mediacms_media`)
- `df -h /mnt/ebs` (hardcoded) replaced with `df -h "$EBS_PATH"` (filesystem-aware)
- `/mnt/ebs` no longer appears anywhere as a hardcoded value
- `DOMAIN` for the `curl` check now sourced dynamically from `.env`
- Unicode box-drawing characters (`═══`) replaced with standard `=` lines for terminal compatibility

#### Validation Output (Confirmed Working)

```
[config] Using MEDIA_FILES_PATH from .env: /mnt/ebs/mediacms_media
===========================================================
MediaCMS Structure Validation
Storage Path: /mnt/ebs/mediacms_media
===========================================================

1. Host System Paths
--------------------
Storage path exists (/mnt/ebs/mediacms_media): ✅
Storage path has content: ✅
Host media_files is empty placeholder: ✅
Ownership is correct (1000:1000): ⚠️ (current: 33:0)

5. Storage Status
-----------------
/dev/sdb1       2.0T   28G  1.8T   2% /mnt/ebs

6. Content Statistics
---------------------
Original files: 75
Videos with HLS: 10
Thumbnails: 0
CyTube manifests: 7
```

#### Known Pre-existing Condition

`--init` mode sets `chown 1000:1000` on `$EBS_PATH`, but the MediaCMS container runs as `www-data` (uid `33`). Not breaking — 28G of working media confirms it. Will be addressed in a future hardening pass.

---

### Part B — GPU Encoding Infrastructure

#### Architecture Decision: Separate GPU Preset Variable

| Option | Approach | Decision |
|---|---|---|
| A | Reuse `FFMPEG_PRESET`, internal table maps `faster` → `p4` | ❌ Rejected — opaque, lossy, invisible when debugging |
| B | Separate `ENCODING_GPU_PRESET`, independently tunable | ✅ Chosen — explicit, self-documenting, no future refactor |

CPU and GPU presets operate on different scales (`ultrafast`→`veryslow` vs `p1`→`p7`). Keeping them separate allows setting `FFMPEG_PRESET=veryslow` for archival CPU encodes while running `ENCODING_GPU_PRESET=p4` for GPU, with neither overriding the other.

#### New `.env` Variables (dev-v0.4.0)

Added to `SYSTEM CONFIGURATION → ENCODING BACKEND CONFIGURATION`:

```bash
# Options: cpu (default, works on all servers) | gpu (requires NVIDIA + nvidia-container-toolkit)
ENCODING_BACKEND=cpu

# NVENC preset — only active when ENCODING_BACKEND=gpu
# p1 (fastest) to p7 (highest quality) — p4 ≈ CPU preset 'faster'
ENCODING_GPU_PRESET=p4
```

#### `local_settings.py` Changes (dev-v0.4.0)

Both variables are read, range-validated, and printed in the startup log. Invalid values fall back to safe defaults with a `⚠️ WARNING`. The startup summary now shows the active backend:

```
================================================================================
🎬 FFMPEG ENCODING CONFIGURATION (from .env)
================================================================================
Encoding Backend:    CPU
CPU Preset:          faster (libx264)
...
```

When `ENCODING_BACKEND=gpu`:
```
Encoding Backend:    GPU
GPU Preset:          p4 (NVENC h264_nvenc)
⚠️  GPU MODE ACTIVE - Requires NVIDIA GPU + nvidia-container-toolkit
```

#### `files/helpers.py` Changes (dev-v0.2.0)

Only `produce_ffmpeg_commands()` and `get_base_ffmpeg_command()` changed. All other functions are byte-for-byte identical to dev-v0.1.0.

**Encoder selection in `produce_ffmpeg_commands()`:**

```python
if codec == "h264":
    encoding_backend = getattr(settings, "ENCODING_BACKEND", "cpu").lower()
    if encoding_backend == "gpu":
        encoder = "h264_nvenc"
        use_gpu = True
    else:
        encoder = "libx264"    # unchanged CPU path
elif codec in ["h265", "hevc"]:
    encoder = "libx265"        # always CPU
elif codec == "vp9":
    encoder = "libvpx-vp9"     # always CPU
```

`vp9` and `h265` always use CPU encoders regardless of `ENCODING_BACKEND`.

**Flag differences between CPU and GPU paths:**

| Flag | CPU (`libx264`) | GPU (`h264_nvenc`) | Reason |
|---|---|---|---|
| Quality | `-crf VALUE` | `-cq VALUE` | NVENC uses Constant Quality, not CRF |
| Preset | `-preset faster` | `-preset p4` | Different preset scales |
| Keyframe (inline) | `-x264-params keyint=...:keyint_min=...` | **Removed** | Fatal error with `h264_nvenc` — not supported |
| Keyframe (standalone) | Not present | `-g KEYINT -keyint_min KEYINT_MIN` | NVENC equivalent |
| `-maxrate` / `-bufsize` | ✅ | ✅ | Both support |
| `-force_key_frames` | ✅ | ✅ | Both support |
| `-profile:v` / `-level` | ✅ | ✅ | Identical |
| Two-pass | Supported via passlogfile | Forced to CRF | NVENC twopass ≠ libx264 twopass mechanism |

The two-pass guard (in practice never triggers since `CRF_ENCODING_NUM_SECONDS=2` means all real videos use `enc_type="crf"` already):

```python
if use_gpu and enc_type == "twopass":
    logger.warning("GPU mode does not support passlogfile two-pass. Forcing enc_type=crf.")
    enc_type = "crf"
```

#### `validate-env.sh` Changes (dev-v0.3.0)

New `ENCODING BACKEND CONFIGURATION` section inserted between `FFMPEG ENCODING` and `HLS STREAMING` sections. All existing checks unchanged.

- `ENCODING_BACKEND=cpu` → ✅ silent pass
- `ENCODING_BACKEND=gpu` → ✅ pass + ⚠️ warning listing all 4 host requirements
- Invalid value → ❌ fail, blocks deploy
- `ENCODING_GPU_PRESET` invalid with `ENCODING_BACKEND=gpu` → ❌ fail
- `ENCODING_GPU_PRESET` invalid with `ENCODING_BACKEND=cpu` → ⚠️ warn only (not active)

Configuration summary updated to show active backend and preset. When GPU mode is active, the "Next steps" section replaces the standard deploy command with:

```
GPU MODE — Start command:
  docker compose -f docker-compose.yaml -f docker-compose.gpu.yml up -d
```

#### `docker-compose.gpu.yml` — New File (dev-v0.1.0)

Compose overlay file. `docker-compose.yaml` is **not modified**. CPU deployments are completely unaffected.

```yaml
services:
  celery_worker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu, video]
```

Only `celery_worker` gets GPU access — all encoding runs in that container. `web`, `db`, `redis`, and `caddy` are unchanged.

**Usage:**

```bash
# CPU (default — unchanged behavior)
docker-compose up -d

# GPU
docker compose -f docker-compose.yaml -f docker-compose.gpu.yml up -d
```

**Host requirements for GPU mode:**

1. NVIDIA GPU installed on host
2. `nvidia-container-toolkit` installed:
   `https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html`
3. Docker daemon configured for NVIDIA runtime:
   ```bash
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```
4. `.env` updated: `ENCODING_BACKEND=gpu`

**Verify GPU is accessible after starting:**

```bash
docker exec ${CELERY_WORKER_CONTAINER_NAME} nvidia-smi
docker exec ${CELERY_WORKER_CONTAINER_NAME} ffmpeg -encoders 2>/dev/null | grep nvenc
```

---

# Looking for the Original MediaCMS?

## Plug in!

- MediaCMS for CyTube is part of the MediaCMS [Show and tell discussion here](https://github.com/mediacms-io/mediacms/discussions/1486)
- Add functionality, work on a PR, fix an issue!

The original project can be located here: [https://github.com/mediacms-io/mediacms](https://github.com/mediacms-io/mediacms)

MediaCMS is a modern, fully featured open source video and media CMS. It is developed to meet the needs of modern web platforms for viewing and sharing media. It can be used to build a small to medium video and media portal within minutes.

It is built mostly using the modern stack Django + React and includes a REST API.

## Contact

[info@mediacms.io](mailto:info@mediacms.io)
