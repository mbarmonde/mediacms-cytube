  # MediaCMS for CyTube (MediaCMS 7.2)

  ## MediaCMS for CyTube Key Changes

  This fork of MediaCMS features integration for CyTube, including:
  - **HLS Streaming at 480p** - MediaCMS encodes all uploads to H.264 480p HLS with 6-second segments using veryfast preset
  - **CyTube Integration** - Custom API generates CyTube-compatible JSON manifests with application/x-mpegURL content type per [CyTube best practices](https://github.com/calzoneman/sync/blob/3.0/docs/custom-media.md)
  - **Real-time Encoding Status Widget** - JavaScript widget (v1.7) displays encoding progress with ETA calculation, auto-updates every 3 seconds, shows "Ready for Export to CyTube!" when complete
  - **One-click Export Button** - Floating button on video pages copies CyTube manifest URL to clipboard
  - **Block Storage Integration** - All media stored on with proper volume mounts
  - **Automated Container Health** - Healthcheck script automatically configures nginx (removes CORS conflicts, sets upload timeouts) and activates only h264-480 + preview encoding profiles on every restart
  - **Large File Upload Support** - Handles 2-8GB files with 10GB max size, 2-hour timeout for chunk finalization

  ## MediaCMS for CyTube Stack

  | Component | Version | Purpose |
|-----------|---------|---------|
| MediaCMS | 7.2 | Video management & encoding platform |
| Celery | Latest | Distributed task queue system that handles asynchronous background processing for media operations.
| Caddy | 2.10.2 | Reverse proxy with HLS optimization |
| PostgreSQL | 17.2 | Database |
| Redis | Alpine | Caching & Celery broker |
| Docker Compose | Latest | Container orchestration |

  ## MediaCMS for CyTube Change-File List
  
```
/mediacms/
├── docker-compose.yaml                    # v0.3.1 - Container orchestration
├── deploy/docker/
│   ├── local_settings.py                  # v0.1.1 - Django settings (HLS, 480p)
│   ├── nginx/mediacms.conf                # Nginx config (no CORS)
│   └── init-scripts/remove-nginx-cors.sh  # Startup script
├── scripts/
│   ├── docker-healthcheck.sh              # v4.4 - Version-based config
│   ├── init_validate_storage.sh           # v1.0.0 - Storage setup
│   └── (backup files with timestamps)
├── caddy/
│   └── Caddyfile                          # v0.2.4 - Reverse proxy config
├── cms/
│   ├── urls.py                            # v0.0.1 - Django URL routing
│   └── custom_api.py                      # v0.3.0 - CyTube manifest API
├── custom_urls.py                         # v0.1.3 - Custom API URLs
├── static/js/
│   ├── cytube-export.js                   # CyTube export button
│   └── encoding-status.js                 # v1.7.0 - Real-time encoding widget
├── templates/
│   └── root.html                          # Custom UI templates
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

  ## (TBD) Will be featured at some point at
  - [Show and tell](https://github.com/mediacms-io/mediacms/discussions/categories/show-and-tell) how you are using the project
  - Star the project
  - Add functionality, work on a PR, fix an issue!

  ## Contact

  info@mediacms.io
