  # MediaCMS for CyTube (MediaCMS 7.7)
  
  ## What's this for?
  
  [CyTube](https://github.com/calzoneman/sync) is a Reddit-like series of user-registered channels where connected viewers watch videos from different video hosts (e.g., YouTube, Twitch, Customer server) and the playback is synchronized for all the viewers in the channel. Each channel has a playlist where users can queue up videos to play, as well as an integrated chatroom for discussion. Channel capabilities includes owners and moderators in various roles with emotes (gifs), and CSS customization.
  
  [MediaCMS](https://github.com/mediacms-io/mediacms) provides a private repository for video content used as a YouTube replacement to stream, manage, and encode videos with RBAC and various features.
  
  **MediaCMS for CyTube** modifies MediaCMS for instant sharing of video content to CyTube via an accepted .JSON file for CyTube playlists. In one click, an encoded video in MediaCMS can be copied and pasted in a play list to start showing.

  ## MediaCMS for CyTube Key Changes

  This fork of MediaCMS features integration for CyTube, including:
  - **HLS Streaming at 480p** - MediaCMS encodes all uploads to H.264 480p HLS with 6-second segments using veryfast preset
  - **CyTube Integration** - Custom API generates CyTube-compatible JSON manifests with application/x-mpegURL content type per [CyTube best practices](https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md)
  - **Real-time Encoding Status Widget** - JavaScript widget (v1.7) displays encoding progress with ETA calculation, auto-updates every 3 seconds, shows "Ready for Export to CyTube!" when complete
  - **Automated Encoding Profile Setup** - Enables only 480p and Preview encoding profiles, disabling the rest; require initial docker compose start / stop; includes lock mechanism for incremental changes)
  - **One-click Export Button** - Floating button on video pages copies CyTube manifest URL to clipboard
  - **Block Storage Integration** - All media stored on with proper volume mounts (required at /mnt/ebs universally)
  - **Automated Container Health** - Healthcheck script automatically configures nginx (removes CORS conflicts, sets upload timeouts) and activates only h264-480 + preview encoding profiles on every restart
  - **Large File Upload Support** - Handles 2-8GB files with 10GB max size, 2-hour timeout for chunk finalization

  ## Plug in!

  - [Show and tell discussion here](https://github.com/mediacms-io/mediacms/discussions/1486) on how you are using the project
  - Add functionality, work on a PR, fix an issue!
  
  ## MediaCMS for CyTube Get Started
  
  1. Clone the repo to a root folder called mediacms:
```
git clone https://github.com/mbarmonde/mediacms-cytube /mediacms
```
  
  2. Modify then save each of the following files with your settings and info:
```
# Find and Replace LOGON SUPERADMIN USERNAME, 1ea
# Find and Replace LOGON SUPERADMIN EMAIL, 1ea
# Find and Replace LOGON SUPERADMIN PASSWORD, 1ea
nano /mediacms/.env
```

```
# Find Replace YOUR.DOMAIN.COM, 1ea
# Find Replace YOUR SERVER DESCRIPTION, 2ea
nano /mediacms/deploy/docker/local_settings.py
```

```
# Find Replace YOUR.DOMAIN.COM, 1ea 
nano /mediacms/caddy/Caddyfile
```

```
# Find Replace YOUR.DOMAIN.COM, 1ea
 nano /mediacms/custom_api.py
 ```
 
 3. Make the Init script executable
 ```
 chmod +x /mediacms/cytube-execute-all-sh-and-storage-init.sh
 ```
 
 4. Run the init script and pay attention to the output
 ```
/mediacms/cytube-execute-all-sh-and-storage-init.sh
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
  D = Domain, Email or Password change required
  
```
/mediacms/
├── .env                                       D - # dev-v0.1.2 - .env for docker-compose.yaml - >>> User, Pass, Email changes, 1 count ea
├── docker-compose.yaml                        # dev-v0.3.2 - Container orchestration
├── deploy/docker/
│   └── Local_settings.py                      D - # dev-v0.1.2 - Django settings (HLS, 480p) - >>> Domain / Descrip changes, 1 count, 2 counts
├── scripts/
│   ├── docker-healthcheck.sh                  # dev-v4.4.0 - changes nginx defaults for CORS serving and encoding profiles
│   └── init_validate_storage.sh               # dev-v0.1.1 - init-config for all CyTube custom files and storage setup
├── caddy/
│   └── Caddyfile                              D - # dev-v0.2.5 - Reverse proxy config - >>> Domain changes, 1 count
│   └── *caddy*                              
│       └── *certificates*                     *# OPTIONAL - where certificates go for caddy via Let's Encrypt if testing*
├── cms/
│   └── urls.py                                # dev-v0.1.0 - Django URL routing - >>>>>>> Changes if non-HTTPS
├── custom_api.py                              D - # dev-v0.3.1 - CyTube manifest API - >>> Domain changes, 1 count
├── custom_urls.py                             # dev-v0.1.3 - Custom API URLs
├── static/js/
│   ├── cytube-export.js                       # dev-v0.1.0 - CyTube export button via media page
│   └── encoding-status.js                     # dev-v0.1.7 - Real-time encoding widget status
├── templates/
│   └── root.html                              # dev-v0.1.0 - Custom UI templates
├── cytube-execute-all-sh-and-storage-init.sh  # dev-v0.1.3 - Custom API URLs
```

  ## MediaCMS for CyTube Storage Architecture for Block Storage
  
```
Host: /mnt/ebs/mediacms_media/
  ├── original/           # Uploaded files
  ├── hls/                # HLS segments (hash-based directories)
  ├── thumbnails/         # Video thumbnails
  ├── cytube_manifests/   # Generated JSON manifests
  ├── userlogos/          # User avatars
  └── encodings/          # Encoded video files


Container: /home/mediacms.io/mediacms/media_files/ (mounted from above via docker-compose.yaml)
```

  # Looking for the Original MediaCMS?

  The original project can be located here: https://github.com/mediacms-io/mediacms

  MediaCMS is a modern, fully featured open source video and media CMS. It is developed to meet the needs of modern web platforms for viewing and sharing media. It can be used to build a small to medium video and media portal within minutes.

  It is built mostly using the modern stack Django + React and includes a REST API.

  ## Contact

  info@mediacms.io
