  # Dev-Branch MediaCMS for CyTube (MediaCMS 7.7) - Updated 2/09/2026
  
  [Main branch that's validated for MediaCMS 7.7 is here](https://github.com/mbarmonde/mediacms-cytube/tree/main)
  
  # What is MediaCMS for CyTube?
  
  [CyTube](https://github.com/calzoneman/sync) is a Reddit-like series of user-registered channels where connected viewers watch videos from different video hosts (e.g., YouTube, Twitch, Customer server) and the playback is synchronized for all the viewers in the channel. Each channel has a playlist where users can queue up videos to play, as well as an integrated chatroom for discussion. Channel capabilities includes owners and moderators in various roles with emotes (gifs), and CSS customization.
  
  [MediaCMS](https://github.com/mediacms-io/mediacms) provides a private repository for video content used as a YouTube replacement to stream, manage, and encode videos with RBAC and various features.
  
  **MediaCMS for CyTube** modifies MediaCMS for instant sharing of video content to CyTube via an accepted .JSON file for CyTube playlists. In one click, an encoded video in MediaCMS can be copied and pasted in a play list to start showing.

  # MediaCMS for CyTube Quick Start
  Note: The default is /mnt/ebs/mediacms_media. If using a different path, update MEDIA_FILES_PATH in .env
  
  1. Clone the repo branch of your choice to a root folder called /mediacms
  
Main:
```
git clone https://github.com/mbarmonde/mediacms-cytube /mediacms
```
Dev:
```
git clone --branch dev https://github.com/mbarmonde/mediacms-cytube /mediacms
```
  
  2. Modify .env, and find and replace the values below (note the optional inputs)
 ```
 nano .env
 
# ============================================
# DEPLOYMENT CONFIGURATION (HTTPS-ONLY)
# ============================================
DOMAIN=yourdomain.com                    # ← Your actual domain (no http:// or https://)

# ============================================
# ADMIN CREDENTIALS
# ============================================
ADMIN_USER=yourusername                  # ← Your admin username
ADMIN_EMAIL=your@email.com               # ← Your admin email
ADMIN_PASSWORD=YourSecurePassword123     # ← Your secure password (8+ chars)

# ============================================
# CYTUBE INTEGRATION METADATA (Optional)
# ============================================
# NOTE: Use quotes for values containing spaces
CYTUBE_DESCRIPTION="Custom MediaCMS streaming server for CyTube integration"
CYTUBE_ORGANIZATION="MediaCMS-CyTube"
 ```
 
 3. Make the validate script executable and run the validation. If validation fails, fix the errors shown and run again.
 ```
 chmod +x validate-env.sh
 ./validate-env.sh
 ```
 
 4. Run the init script - starts the docker containers, and makes all scripts executable
 ```
 chmod +x cytube-execute-all-sh-and-storage-init.sh
./cytube-execute-all-sh-and-storage-init.sh

# This script:
#✅ Validates your configuration
#✅ Makes all scripts executable
#✅ Initializes storage structure
#✅ Starts Docker containers
#✅ Waits for database to be ready
#✅ Populates 20 subtitle languages
 ```
 
 5. Check for running, healthly containers, and access your MediaCMS for CyTube site:
 ```
docker-compose ps

#NAME                     STATUS
#media_cms                Up (healthy)
#mediacms_caddy           Up
#mediacms_celery_beat     Up
#mediacms_celery_worker   Up
#mediacms_db              Up (healthy)
#mediacms_redis           Up (healthy)

curl -I https://yourdomain.com
# Expected: HTTP/2 200 or HTTP/2 302
 ```
 
 ## Deployment Checklist
 
 ✅ Deployment Checklist
Before going live, verify:

- DNS resolves correctly (nslookup yourdomain.com)
- Ports 80/443 are open
- env file configured with real values
- validate-env.sh passes
- All containers show Up status
- HTTPS certificate generated (check browser)
- Can login to web interface
- Test video uploads and encodes successfully
- CyTube manifest generates and plays
- Subtitle languages populated (20 languages)
- Firewall rules configured
- Backup script created and tested


 # Help, Troubleshooting, General Information
 
 ## MediaCMS for CyTube Key Changes

  This fork of MediaCMS features integration for CyTube, including:
- **All-in-One Setup Script** - Use .env file to set variables for the project and run a single script to get things going - Added 02/09/2026
- **Subtitle Inclusion** - Via native MediaCMS processes and included with the JSON payload for CyTube - Added 02/09/2026
- **Adaptive Bitrate streaming** - Enabled 480p, 720p, and 1080p encoding with adaptive bitrate streaming for CyTube. MediaCMS encodes all uploads to H.264 HLS with 6-second segments using veryfast preset - Added 02/06/2026
- **Smart Encode** - Dynamically enable/disable encoding profiles based on source video resolution to prevent unnecessary upscaling and optimize storage/CPU usage. - Added 02/06/2026
- **CyTube Integration** - Custom API generates CyTube-compatible JSON manifests with application/x-mpegURL content type per CyTube best practices: https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md
- **Real-time Encoding Status Widget** - JavaScript widget (v1.7) displays encoding progress with ETA calculation, auto-updates every 3 seconds, shows "Ready for Export to CyTube!" when complete
- **Automated Encoding Profile Setup** - Enables only 480p, 720p, 1080p and Preview encoding profiles, disabling the rest, but uses Smart Encode to save space  
- **One-click Export Button** - Floating button on video pages copies CyTube manifest URL to clipboard
- **Block Storage Integration** - All media stored on with proper volume mounts (required at /mnt/ebs universally)
- **Automated Container Health** - Healthcheck script automatically configures nginx (removes CORS conflicts, sets upload timeouts) and activates encoding profiles on every docker restart/recreation - self-healing
- **Large File Upload Support** - Handles 2-8GB files with 10GB max size, 2-hour timeout for chunk finalization

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
5. User clicks "Export to CyTube" button on video page
   ↓
6. custom_api.py generates CyTube manifest JSON
   ├─→ Detects available resolutions
   ├─→ Includes subtitle tracks (if uploaded)
   └─→ Saves to: /mnt/ebs/mediacms_media/cytube_manifests/
   ↓
7. User pastes manifest URL in CyTube
   ↓
8. CyTube fetches JSON, parses sources array
   ↓
9. Video player loads HLS stream with quality selector
   └─→ Users can switch between 480p/720p/1080p in real-time
```

 ## 📹 First Video Upload Test
- Upload a Test Video
Navigate to: https://yourdomain.com/upload

- Upload a video file (MP4, MKV, AVI, etc.)

- Wait for encoding to complete (check progress bar)

- Generate CyTube Manifest
Once encoding completes:
  - Go to the video page
  - Click the "Export to CyTube" button (floating blue button)
  - Manifest URL is copied to clipboard
  - Manifest URL format:
    - text 
    - https://yourdomain.com/media/custom/XXXXX_VideoTitle.json
    - Test in CyTube
  
- In your CyTube room:

  - Click Add Video from URL

  - Paste the manifest URL

  - Video should play with quality selector (480p/720p/1080p)

 ## Verify Subtitle Languages
 ```
 docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT COUNT(*) FROM files_language;"
 ```
 
 ## Example JSON Payload
**Here is a result of a .json example file** encoded dynamically based on native resoltions for CyTube that's publicly accessibly at: https://YOUR.DOMAIN.COM/media/custom/(manifest).json which I can play in CyTube via Caddy to MediaCMS:

```
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
|-----------|---------|---------|
| MediaCMS | 7.7 | Video management & encoding platform |
| Celery | Latest | Distributed task queue system that handles asynchronous background processing for media operations.
| Caddy | 2.10.2 | Reverse proxy with HLS optimization |
| PostgreSQL | 17.2 | Database |
| Redis | Alpine | Caching & Celery broker |
| Docker Compose | Latest | Container orchestration |

  ## MediaCMS for CyTube Change-File List
  Updated 2/09/2026
  
```
/mediacms/
├── .env                                   			# dev-v0.2.1 - .env for docker-compose.yaml and other files across the project
├── cytube-execute-all-sh-and-storage-init.sh  		# dev-v0.3.0 - Initializes storage file system, starts containers, creates subtitle languages
├── docker-compose.yaml                        		# dev-v0.3.8 - Container orchestration tied to .env for inputs
├── custom_api.py                         			# dev-v0.6.0 - CyTube manifest API - tied to .env for inputs
├── custom_urls.py                          	    # dev-v0.1.3 - Custom API URLs
├── validate-env.sh   	                            # dev-v1.0.0 - validates contents in the .env file
├── caddy/
│   └── Caddyfile                          		    # dev-v0.4.0 - Reverse proxy config - tied to .env for inputs
│   └── *caddy*                              
│       └── *certificates*             		        ###### OPTIONAL - where certificates go for caddy via Let's Encrypt if testing #####
├── cms/
│   └── urls.py                             	    # dev-v0.1.0 - Django URL routing
├── deploy/docker/
│   └── Local_settings.py                  			# dev-v0.2.0 - Django settings (HLS, 480p) - tied to .env for inputs
│   └── nginx_http_only.conf				  		# dev-v1.0.0 - large file timeouts, CORS removal
├── files/models/
│   └── media.py							   		# dev-v1.0.0 - Smart encode modifications
├── scripts/
│   ├── docker-healthcheck.sh                 		# dev-v5.3.0 - changes nginx defaults for CORS serving and encoding profiles
│   └── init_validate_storage.sh              		# dev-v0.1.1 - init-config for all CyTube custom files and storage setup
│   └── init_subtitle_languages.sh         			# dev-v1.0.3 - subtitles
├── static/js/
│   ├── cytube-export.js                    		# dev-v0.1.0 - CyTube export button via media page
│   └── encoding-status.js                  		# dev-v0.1.7 - Real-time encoding widget status
├── templates/
│   └── root.html                           	    # dev-v0.1.0 - Custom UI templates
```

  ## MediaCMS for CyTube Storage Architecture for Block Storage
  Note: The default is /mnt/ebs/mediacms_media. If using a different path, update MEDIA_FILES_PATH in .env
  
```
Host: /mnt/ebs/mediacms_media/
  ├── chunks/             # Temp encoded chunks
  ├── cytube_manifests/   # Generated JSON manifests
  ├── encoded/			  # Encoded video files
  ├── encodings/          # Temp Encoded video files
  ├── hls/                # HLS segments (hash-based directories)
  ├── original/           # Uploaded files / subtitles
  ├── thumbnails/         # Video thumbnails
  ├── uploaded/			  # Temp uploaded content
  └── userlogos/          # User avatars

Container: /home/mediacms.io/mediacms/media_files/ (mounted from above via docker-compose.yaml)
```

 ## Common Operations

View Logs
``` 
 # All containers
docker-compose logs -f

# Specific container
docker-compose logs -f media_cms
docker-compose logs -f mediacms_celery_worker
docker-compose logs -f mediacms_caddy
```

Restart Services
```
bash
# Restart all containers
docker-compose restart

# Restart specific container
docker-compose restart media_cms
```

Stop Services
```
bash
docker-compose down
```

Update MediaCMS
```
bash
# Stop containers
docker-compose down

# Pull latest images
docker-compose pull

# Restart with new images
./cytube-execute-all-sh-and-storage-init.sh
```

Check Storage Usage
```
bash
# Media files
du -sh /mnt/ebs/mediacms_media/*

# Database
docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT pg_size_pretty(pg_database_size('mediacms'));"
```

 ## Troubleshooting
Problem: Caddy won't start - "unrecognized global option"
Cause: DOMAIN environment variable not passed to Caddy container

Fix:
```
bash
# Check docker-compose.yaml has environment section for caddy
grep -A 3 "caddy:" docker-compose.yaml | grep -A 2 "environment:"

# Should show:
# environment:
#   - DOMAIN=${DOMAIN}

# If missing, update docker-compose.yaml and restart
docker-compose down
docker-compose up -d
```

Problem: Python containers fail with "Missing required environment variable 'DOMAIN'"
Cause: DOMAIN not passed to web/celery containers

Fix:
```
bash
# Verify docker-compose.yaml v0.3.9+
head -n 1 docker-compose.yaml

# Should show: # dev-v0.3.9

# Check web container has DOMAIN
grep -A 10 "^  web:" docker-compose.yaml | grep "DOMAIN:"

# If missing, update to docker-compose.yaml v0.3.9
docker-compose down
docker-compose up -d
```

Problem: SSL certificate not generating
Cause: DNS not propagated or port 80/443 blocked

Fix:
```
bash
# Check DNS resolution
nslookup yourdomain.com

# Check ports are open
sudo netstat -tulpn | grep -E ':80|:443'

# Check Caddy logs
docker-compose logs caddy | grep -i "certificate"

# Wait 5-10 minutes for Let's Encrypt retry
```

Problem: Videos not encoding
Cause: Celery worker not running or encoding profiles disabled

Fix:
```
bash
# Check celery worker status
docker-compose logs mediacms_celery_worker | tail -20

# Check encoding profiles (should auto-enable on startup)
docker exec media_cms cat /home/mediacms.io/mediacms/cms/settings.py | grep -A 5 "MINIMUM_RESOLUTIONS"

# Should show: 

# Restart celery worker
docker-compose restart mediacms_celery_worker
```

Problem: Upload fails with timeout
Cause: File too large or network timeout

Fix:
```
bash
# Check upload limits in Local_settings.py
docker exec media_cms grep "UPLOAD_MAX_SIZE" /home/mediacms.io/mediacms/deploy/docker/local_settings.py

# Should show: UPLOAD_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

# If uploading >8GB, increase timeouts in Caddyfile
nano caddy/Caddyfile
# Increase read_timeout, write_timeout, response_header_timeout
```

Problem: Subtitle languages missing
Cause: Database initialization didn't run

Fix:
```
bash
# Run subtitle initialization manually
./scripts/init_subtitle_languages.sh

# Verify
docker exec mediacms_db psql -U mediacms -d mediacms -c "SELECT code, title FROM files_language ORDER BY title;"

# Should show 20 languages
```

Problem: CyTube manifest returns 404
Cause: Video encoding not complete or manifest not generated

Fix:
```
bash
# Check encoding status
docker-compose logs media_cms | grep "Encoding status"

# Manually trigger manifest generation (replace TOKEN with video's friendly_token)
curl https://yourdomain.com/media/custom/TOKEN

# Check if file exists
ls -la /mnt/ebs/mediacms_media/cytube_manifests/
```

 ## Performance Tuning
For High Traffic (100+ concurrent users)
Edit docker-compose.yaml:
```
  web:
    deploy:
      replicas: 2  # Increase from 1

  celery_worker:
    deploy:
      replicas: 2  # Increase from 1
```

Then restart:
```
bash
docker-compose up -d --scale web=2 --scale celery_worker=2
```

 ## Enable Huge Files (>5GB)
Edit caddy/Caddyfile:

```
# Increase timeouts (line ~120)
read_timeout 7200s        # 2 hours
write_timeout 7200s       # 2 hours
response_header_timeout 7200s  # 2 hours
```

Then restart:
```
bash
docker-compose restart caddy
```

 ## Security Best Practices
1. Change Default Passwords
```
bash
# Update .env with strong passwords
nano .env


# Change ADMIN_PASSWORD to 16+ character password
# Use password manager to generate
```

2. Restrict User Registration
Already configured in Local_settings.py:
```
REGISTER_ALLOWED = False
USERS_CAN_SELF_REGISTER = False
GLOBAL_LOGIN_REQUIRED = True
```

3. Enable Firewall
```
bash
# Allow only SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

4. Regular Backups
```
bash
# Backup script (save as backup-mediacms.sh)
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

  # Looking for the Original MediaCMS?
  
  ## Plug in!

  - MediaCMS for CyTube is part of the MediaCMS [Show and tell discussion here](https://github.com/mediacms-io/mediacms/discussions/1486) 
  - Add functionality, work on a PR, fix an issue!

  The original project can be located here: https://github.com/mediacms-io/mediacms

  MediaCMS is a modern, fully featured open source video and media CMS. It is developed to meet the needs of modern web platforms for viewing and sharing media. It can be used to build a small to medium video and media portal within minutes.

  It is built mostly using the modern stack Django + React and includes a REST API.

  ## Contact

  info@mediacms.io
