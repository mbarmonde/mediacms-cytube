# MediaCMS 7.7 for CyTube

**Self-hosted video streaming platform optimized for CyTube integration with adaptive bitrate HLS streaming**

[![MediaCMS](https://img.shields.io/badge/MediaCMS-7.7-blue)](https://github.com/mediacms-io/mediacms)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-Django-092E20?logo=django)](https://www.djangoproject.com/)
[![Caddy](https://img.shields.io/badge/Caddy-2.10.2-1F88C0)](https://caddyserver.com/)

> **Production-ready fork** of MediaCMS 7.7 with custom API endpoints, multi-resolution HLS encoding, and real-time status widgets designed specifically for CyTube synchronous viewing.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
  - [Container Stack](#container-stack)
  - [Storage Architecture](#storage-architecture)
- [Project Files](#project-files)
  - [Core Configuration](#core-configuration)
  - [Custom API & Routing](#custom-api--routing)
  - [Frontend JavaScript](#frontend-javascript)
  - [Backend & Scripts](#backend--scripts)
- [Technical Specifications](#technical-specifications)
  - [Adaptive Bitrate Streaming](#adaptive-bitrate-streaming)
  - [CyTube Integration API](#cytube-integration-api)
  - [Smart Encode Logic](#smart-encode-logic)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Initial Setup](#initial-setup)
  - [Configuration](#configuration)
- [Deployment](#deployment)
  - [Starting Services](#starting-services)
  - [Monitoring](#monitoring)
  - [Validation](#validation)
- [Usage](#usage)
  - [Admin Workflow](#admin-workflow)
  - [CyTube Integration](#cytube-integration)
- [Debugging](#debugging)
  - [Log Locations](#log-locations)
  - [Common Issues](#common-issues)
- [Server Requirements](#server-requirements)
- [Development](#development)
  - [File Versioning](#file-versioning)
  - [Contributing](#contributing)
- [Lessons Learned](#lessons-learned)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Overview

MediaCMS 7.7 for CyTube is a production-ready Docker-based video streaming platform that extends [MediaCMS](https://github.com/mediacms-io/mediacms) with:

- **Custom CyTube API** - JSON manifest generation following [CyTube Custom Media specification](https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md)
- **Adaptive Bitrate HLS** - Multi-resolution streaming (480p/720p/1080p) with H.264/AAC
- **Real-time Status Widgets** - Live encoding progress with ETA calculation
- **One-click Export** - Automatic manifest URL generation and clipboard copy
- **Automated Health Management** - Self-healing CORS configuration and encoding profiles

**Designed for**: Communities running CyTube rooms serving 50-200 concurrent viewers with 2-8GB video files.

---

## Key Features

### ✨ Core Capabilities

| Feature | Description | Version |
|---------|-------------|---------|
| **Multi-Resolution HLS** | Adaptive bitrate streaming with 480p, 720p, 1080p profiles | custom_api.py v0.4.1 |
| **Smart Encode** | Prevents upscaling - only encodes resolutions ≤ source | local_settings.py v0.1.3 |
| **CyTube Manifests** | Auto-generates JSON with `application/x-mpegURL` content type | custom_api.py v0.4.1 |
| **Real-time Status** | Widget updates every 3s with progress bars and ETA | encoding-status.js v0.1.7 |
| **One-click Export** | Floating button copies manifest URL to clipboard | cytube-export.js v0.1.0 |
| **Large File Support** | Handles 2-8GB uploads with 10GB max size | local_settings.py v0.1.1 |
| **Automated Health** | Removes CORS conflicts, activates profiles on every restart | docker-healthcheck.sh v5.2.0 |
| **Block Storage** | External EBS mount for scalable media storage | docker-compose.yaml v0.3.4 |

---

## Architecture

### Container Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Caddy Reverse Proxy (Port 80/443)                          │
│ ├─ HLS Streaming (.m3u8, .ts files)                        │
│ ├─ JSON Manifest serving                                    │
│ ├─ CORS headers for cross-origin playback                   │
│ └─ Extended timeouts (1hr) for large uploads                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ MediaCMS Web Container (media_cms)                          │
│ ├─ Django 4.x + uWSGI                                       │
│ ├─ Custom CyTube API endpoints                              │
│ ├─ Nginx (internal routing)                                 │
│ ├─ Healthcheck automation                                   │
│ └─ Media files: /mnt/ebs/mediacms_media → /media_files      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┬──────────────────┬───────────────────────┐
│ Celery Workers   │ PostgreSQL 17.2  │ Redis Alpine          │
│ - Video Encoding │ - Media Metadata │ - Task Queue          │
│ - HLS Generation │ - User Auth      │ - Django Cache        │
└──────────────────┴──────────────────┴───────────────────────┘
```

### Storage Architecture

**Host System**:
```
/mnt/ebs/mediacms_media/
├── original/          # Source uploads (user/username/hash.filename)
├── hls/              # HLS playlists and segments (hash/master.m3u8)
├── thumbnails/       # Auto-generated thumbnails
├── cytube_manifests/ # Generated JSON files for CyTube
├── userlogos/        # User profile images
├── encodings/        # Temporary encoding files
├── chunks/           # Chunked upload storage
├── encoded/          # Completed encoding outputs
└── uploads/          # Pre-processing uploads
```

**Container Mount**:
- Host: `/mnt/ebs/mediacms_media/`
- Container: `/home/mediacms.io/mediacms/media_files/`

---

## Project Files

### Core Configuration

| File | Version | Location | Purpose |
|------|---------|----------|---------|
| `local_settings.py` | v0.1.3 | `/mediacms/deploy/docker/` | Django encoding, HLS, upload settings |
| `docker-compose.yaml` | v0.3.4 | `/mediacms/` | Container orchestration with healthcheck |
| `.env` | v0.1.2 | `/mediacms/` | Environment variables (credentials, paths) |
| `Caddyfile` | v0.2.5 | `/mediacms/caddy/` | Reverse proxy with timeout handling |

### Custom API & Routing

| File | Version | Location | Purpose |
|------|---------|----------|---------|
| `custom_api.py` | v0.4.1 | `/mediacms/cms/` | CyTube manifest generation with multi-resolution |
| `custom_urls.py` | v0.1.3 | `/mediacms/` | URL routing for custom endpoints |
| `urls.py` | v0.0.1 | `/mediacms/cms/` | Main Django URL configuration |

### Frontend JavaScript

| File | Version | Location | Purpose |
|------|---------|----------|---------|
| `cytube-export.js` | v0.1.0 | `/mediacms/static/js/` | Floating "Export for CyTube" button |
| `encoding-status.js` | v0.1.7 | `/mediacms/static/js/` | Real-time encoding progress widget with ETA |

### Backend & Scripts

| File | Version | Location | Purpose |
|------|---------|----------|---------|
| `media.py` | v1.0.0 | `/mediacms/files/models/` | Core Media model (baseline) |
| `docker-healthcheck.sh` | v5.2.0 | `/mediacms/scripts/` | CORS removal + profile activation |
| `init_validate_storage.sh` | v0.1.1 | `/mediacms/scripts/` | EBS storage initialization/validation |
| `cytube-execute-all-sh-and-storage-init.sh` | v0.1.6 | `/mediacms/` | Deployment helper script |

---

## Technical Specifications

### Adaptive Bitrate Streaming

**Encoding Configuration** (local_settings.py):
- **Profiles**: 480p, 720p, 1080p (H.264 + AAC audio)
- **Segment Duration**: 6 seconds (Apple HLS standard)
- **FFmpeg Preset**: `veryfast` (35% CPU reduction vs `medium`)
- **CRF**: 21 (quality-based encoding)
- **H.264 Profile**: `main` (10-15% bitrate savings vs `baseline`)
- **Audio Codec**: AAC @ 128k (HLS requirement)

### CyTube Integration API

**Endpoints**:

```
GET /api/v1/media/<friendly_token>/cytube-manifest/
→ Generates and saves CyTube JSON manifest

GET /api/v1/media/<friendly_token>/cytube-manifest/<filename>
→ Serves saved JSON file with proper headers

GET /api/encoding-status/<friendly_token>/
→ Returns real-time encoding progress
```

**Manifest Format**:
```json
{
  "title": "Video Title",
  "duration": 6103,
  "live": false,
  "thumbnail": "https://domain.com/media/original/thumbnails/...",
  "sources": [
    {
      "url": "https://domain.com/media/hls/hash/master.m3u8",
      "contentType": "application/x-mpegURL",
      "quality": 480
    },
    {
      "url": "https://domain.com/media/hls/hash/master.m3u8",
      "contentType": "application/x-mpegURL",
      "quality": 720
    },
    {
      "url": "https://domain.com/media/hls/hash/master.m3u8",
      "contentType": "application/x-mpegURL",
      "quality": 1080
    }
  ],
  "textTracks": []
}
```

### Smart Encode Logic

**Resolution Detection**:
1. Queries all successful encodings for the media
2. Extracts resolution from profile names using regex: `-(\d{3,4})$`
   - Example: `h264-480` → 480p
3. Filters out `preview` profile (thumbnail generation)
4. Only includes resolutions where encoding succeeded
5. Defaults to 480p if detection fails

**Prevents Upscaling**:
- Source video at 720p → Only encodes 480p and 720p
- Source video at 1080p → Encodes all three (480p, 720p, 1080p)
- Configured via `MINIMUM_RESOLUTIONS_TO_ENCODE` in local_settings.py

---

## Installation

### Prerequisites

- **OS**: Linux (tested on Ubuntu/Debian)
- **Docker**: v20.10+
- **Docker Compose**: v2.0+
- **Storage**: 
  - 140GB NVMe (local)
  - 2TB block storage mounted at `/mnt/ebs`
- **Network**: Public-facing domain with HTTPS

### Initial Setup

1. **Clone Repository**:
```bash
cd /
git clone https://github.com/mbarmonde/mediacms-cytube.git mediacms
cd /mediacms
```

2. **Make Scripts Executable**:
```bash
chmod +x cytube-execute-all-sh-and-storage-init.sh
chmod +x scripts/*.sh
```

3. **Configure Environment Variables**:
```bash
cp file.env .env
nano .env
```

Edit the following in `.env`:
```bash
# Admin account credentials
ADMIN_USER=your_admin_username
ADMIN_EMAIL=your_admin@email.com
ADMIN_PASSWORD=your_secure_password

# Storage paths (default is fine for most setups)
MEDIA_FILES_PATH=/mnt/ebs/mediacms_media
```

### Configuration

**Required Find/Replace Operations**:

1. **Domain Configuration** (3 files):

   In `local_settings.py`:
   ```python
   FRONTEND_HOST = os.getenv('FRONTEND_HOST', 'https://YOUR.DOMAIN.COM')
   ```
   Replace `YOUR.DOMAIN.COM` with your domain.

   In `Caddyfile`:
   ```
   YOUR.DOMAIN.COM {
   ```
   Replace `YOUR.DOMAIN.COM` with your domain.

   In `custom_api.py` (2 occurrences):
   ```python
   hls_url = f"https://YOUR.DOMAIN.COM/media/hls/{hls_dir_name}/master.m3u8"
   ```
   Replace `YOUR.DOMAIN.COM` with your domain.

2. **Server Description** (2 occurrences in `local_settings.py`):
   ```python
   PORTAL_NAME = os.getenv('PORTAL_NAME', 'YOUR SERVER DESCRIPTION')
   PORTAL_DESCRIPTION = "YOUR SERVER DESCRIPTION"
   ```

---

## Deployment

### Starting Services

1. **Initialize Storage**:
```bash
sudo ./scripts/init_validate_storage.sh --full
```

This will:
- Create directory structure on `/mnt/ebs/mediacms_media`
- Set correct ownership (1000:1000)
- Start services
- Run validation checks

2. **Start Containers**:
```bash
docker-compose up -d
```

3. **Verify Services**:
```bash
docker ps
```

Expected containers:
- `caddy_reverse_proxy`
- `media_cms`
- `mediacms-celery_worker-1`
- `mediacms-celery_beat-1`
- `mediacms-db-1`
- `mediacms-redis-1`

### Monitoring

**Encoding Progress**:
```bash
docker logs -f mediacms-celery_worker-1
```

**Healthcheck Status**:
```bash
docker exec media_cms cat /var/log/mediacms-healthcheck.log
```

**Container Health**:
```bash
docker-compose ps
```

### Validation

**Run Storage Validation**:
```bash
./scripts/init_validate_storage.sh --validate
```

Expected output:
```
✅ EBS mount exists
✅ EBS has content
✅ Host media_files is empty placeholder
✅ Ownership is correct (1000:1000)
✅ Container media_files mounted
✅ HLS directory exists
✅ CyTube manifests directory exists
```

---

## Usage

### Admin Workflow

1. **Upload Video**:
   - Log in to MediaCMS web interface
   - Navigate to "Add Media"
   - Upload video file (supports up to 10GB)

2. **Monitor Encoding**:
   - Real-time widget appears on video page
   - Shows progress bars for each resolution
   - Displays ETA (updates every 3 seconds)

3. **Export to CyTube**:
   - When widget shows "Ready for Export to CyTube!"
   - Click floating "📥 Export for CyTube" button (bottom right)
   - Manifest URL automatically copied to clipboard

4. **Verify Manifest**:
   ```bash
   # Example URL format:
   https://domain.com/media/custom/abc123_Video_Title.json
   ```

### CyTube Integration

1. **In CyTube Room**:
   - Click "Add" → "Custom Media"
   - Paste manifest URL
   - Click "Add"

2. **Player Behavior**:
   - CyTube automatically fetches JSON manifest
   - Video.js player loads HLS stream
   - Adaptive bitrate adjusts quality based on bandwidth
   - Users can manually select resolution if needed

---

## Debugging

### Log Locations

**Healthcheck**:
```bash
docker exec media_cms cat /var/log/mediacms-healthcheck.log
```

**Celery Encoding**:
```bash
docker logs mediacms-celery_worker-1
```

**Nginx**:
```bash
docker exec media_cms cat /var/log/nginx/error.log
docker exec media_cms cat /var/log/nginx/access.log
```

**Django Debug Mode**:
```bash
# In .env or local_settings.py
DEBUG=True
```

### Common Issues

**Problem**: CORS errors in browser console

**Solution**: 
```bash
# Healthcheck should fix automatically every 60s
# Force immediate fix:
docker restart media_cms

# Verify CORS removal:
docker exec media_cms grep "Access-Control" /etc/nginx/sites-enabled/default
# (Should return nothing)
```

---

**Problem**: No HLS files found for video

**Solution**:
```bash
# Check if HLS files exist:
docker exec media_cms ls -la /home/mediacms.io/mediacms/media_files/hls/

# Verify encoding profiles are active:
docker exec media_cms python manage.py shell -c \
  "from files.models import EncodeProfile; \
   print(EncodeProfile.objects.filter(active=True).values_list('name', flat=True))"

# Expected output: ['preview', 'h264-480', 'h264-720', 'h264-1080']
```

---

**Problem**: Upload fails or times out

**Solution**:
```bash
# Check Caddy timeouts in Caddyfile:
grep "timeout" caddy/Caddyfile
# Should show 3600s (1 hour) for read/write/response_header

# Check MediaCMS upload settings:
docker exec media_cms python manage.py shell -c \
  "from django.conf import settings; \
   print(f'Max size: {settings.UPLOAD_MAX_SIZE}'); \
   print(f'Chunk timeout: {settings.CHUNK_UPLOAD_TIMEOUT}')"
```

---

**Problem**: Encoding widget not appearing

**Solution**:
```bash
# Verify JavaScript is served:
curl -I https://your-domain.com/static/js/encoding-status.js
# Should return HTTP 200

# Check browser console for errors
# Widget only loads on /view?m=<token> pages
```

---

## Server Requirements

**Minimum Production Specs** (50-70 concurrent users):
- **CPU**: 4 vCPUs
- **RAM**: 8GB
- **Local Storage**: 140GB NVMe (OS + Docker images)
- **Block Storage**: 2TB+ (media files)
- **Network**: 1Gbps+ (10Gbps recommended for 100+ users)
- **GPU**: Optional (CPU encoding with `veryfast` preset is sufficient)

**Bandwidth Calculation**:
- 100 users × 300kb/s = 30Mbps sustained
- 200 users × 300kb/s = 60Mbps sustained
- Recommend 10Gbps port with burst capacity

**Storage Growth Estimate**:
- 1080p source (8GB) → ~24GB after 3-resolution encoding
- Average 3x storage multiplier
- 2TB storage ≈ 80-100 full-length movies

---

## Development

### File Versioning

All custom/modified files use `dev-v` prefix for easy tracking:

```bash
# Find all versioned files:
grep -rl "dev-v" /mediacms

# Check specific file version:
head -n 5 /mediacms/cms/custom_api.py
```

**Version Format**: `# dev-v<major>.<minor>.<patch>`

Example:
```python
# dev-v0.4.1
#####
# v0.4.1 - FIXED: Regex-based resolution detection
# v0.4.0 - MULTI-RESOLUTION SUPPORT
# v0.3.1 - Better search logic
#####
```

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Update file version headers with changelog
4. Test in production-like environment
5. Submit pull request with detailed description

**Development Principles**:
- Document all changes in file headers
- Use semantic versioning
- Test with real 8GB video files
- Verify with 50+ concurrent CyTube users
- Prioritize production stability over features

---

## Lessons Learned

### ✅ Successful Implementations

1. **Healthcheck Automation** - CORS removal and profile activation survive container restarts without manual intervention

2. **Regex Resolution Detection** - Works around MediaCMS 7.7 `profile.resolution` field inconsistencies by parsing profile names

3. **Multi-Resolution HLS** - CyTube's video.js player handles adaptive bitrate seamlessly; users get automatic quality switching

4. **Extended Caddy Timeouts** - Critical for 8GB file processing; 1-hour timeout prevents chunked upload failures

5. **React-Resistant Button** - 2-second delay + monitoring loop prevents React from removing custom UI elements

### ⚠️ Gotchas to Avoid

1. **MediaCMS Hash-Based HLS** - HLS directories use media file hash, not friendly_token; must extract from `media.media_file.name`

2. **Profile Name Variations** - MediaCMS doesn't standardize profile names; use regex `-(\d{3,4})$` for reliable resolution extraction

3. **CORS Duplication** - Both nginx and Caddy add CORS headers; must remove nginx's to prevent browser conflicts

4. **Button Positioning** - CSS `translateZ(0)` required to prevent transform stacking context issues

5. **Lock File Versioning** - Encoding profile lock file must include version number to allow automated reconfiguration

---

## Future Enhancements

*Planned for future releases*:

1. **Subtitle Support** - Add `textTracks` array to CyTube manifest with WebVTT support

2. **Thumbnail Sprites** - Generate sprite sheets for video scrubbing preview in CyTube player

3. **Multi-Audio Tracks** - Language selection for international content

4. **CDN Integration** - CloudFlare or similar for reduced origin bandwidth

5. **GPU Encoding** - NVENC hardware acceleration for faster transcoding

6. **Kubernetes Deployment** - Horizontal scaling for 500+ concurrent users

7. **Automated Testing** - CI/CD pipeline with encoding verification

---

## License

This project is a fork of [MediaCMS](https://github.com/mediacms-io/mediacms) which is licensed under the AGPL v3.0 license.

**MediaCMS License**: [AGPL v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html)

Custom modifications in this repository (CyTube integration, custom API, widgets) maintain the same AGPL v3.0 license.

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/mbarmonde/mediacms-cytube/issues)
- **MediaCMS Documentation**: [docs.mediacms.io](https://docs.mediacms.io)
- **CyTube Custom Media Spec**: [calzoneman/sync](https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md)

---

**Last Updated**: February 8, 2026  
**Project Status**: Production-Ready  
**MediaCMS Version**: 7.7  
**Docker Compose Version**: 2.x
