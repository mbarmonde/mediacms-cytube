  # Dev-Branch MediaCMS for CyTube (MediaCMS 7.7) - Updated 2/09/2026
  
  [Main branch that's validated for MediaCMS 7.7 is here](https://github.com/mbarmonde/mediacms-cytube/tree/main)
  
  ## What's this for?
  
  [CyTube](https://github.com/calzoneman/sync) is a Reddit-like series of user-registered channels where connected viewers watch videos from different video hosts (e.g., YouTube, Twitch, Customer server) and the playback is synchronized for all the viewers in the channel. Each channel has a playlist where users can queue up videos to play, as well as an integrated chatroom for discussion. Channel capabilities includes owners and moderators in various roles with emotes (gifs), and CSS customization.
  
  [MediaCMS](https://github.com/mediacms-io/mediacms) provides a private repository for video content used as a YouTube replacement to stream, manage, and encode videos with RBAC and various features.
  
  **MediaCMS for CyTube** modifies MediaCMS for instant sharing of video content to CyTube via an accepted .JSON file for CyTube playlists. In one click, an encoded video in MediaCMS can be copied and pasted in a play list to start showing.

  ## MediaCMS for CyTube Key Changes

  This fork of MediaCMS features integration for CyTube, including:
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

  ## Plug in!

  - MediaCMS for CyTube is part of the MediaCMS [Show and tell discussion here](https://github.com/mediacms-io/mediacms/discussions/1486) 
  - Add functionality, work on a PR, fix an issue!
  
  ## MediaCMS for CyTube Quick Start
  
  1. Clone the repo branch of your choice to a root folder called /mediacms
  
Main:
```
git clone https://github.com/mbarmonde/mediacms-cytube /mediacms
```
Dev:
```
git clone --branch dev https://github.com/mbarmonde/mediacms-cytube /mediacms
```
  
  2. Modify then save each of the following files with your settings and info - also used for Let's Encrypt
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
 
 4. Run the init script and pay attention to the output - starts the docker containers, and makes all scripts executable
 ```
/mediacms/cytube-execute-all-sh-and-storage-init.sh
 ```
 
 5. Inject 20 languages for subtitle output (no docker restart required)
 ```
/mediacms/scripts/init_subtitle_languages.sh
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
├── .env                                   		D - # dev-v0.1.4 - .env for docker-compose.yaml - >>> User, Pass, Email changes, 1
├── cytube-execute-all-sh-and-storage-init.sh  		# dev-v0.1.6 - Initializes storage file system, starts containers
├── docker-compose.yaml                        		# dev-v0.3.7 - Container orchestration
├── custom_api.py                         		D - # dev-v0.5.1 - CyTube manifest API - >>> Domain changes, 1
├── custom_urls.py                          	    # dev-v0.1.3 - Custom API URLs
├── deploy/docker/
│   └── Local_settings.py                  		D - # dev-v0.1.3 - Django settings (HLS, 480p) - >>> Domain / Descrip changes, 1
│   └── nginx_http_only.conf				  		# dev-v1.0.0 - large file timeouts, CORS removal
├── scripts/
│   ├── docker-healthcheck.sh                 		# dev-v5.3.0 - changes nginx defaults for CORS serving and encoding profiles
│   └── init_validate_storage.sh              		# dev-v0.1.1 - init-config for all CyTube custom files and storage setup
│   └── init_subtitle_languages.sh         			# dev-v1.0.3 - subtitles
├── caddy/
│   └── Caddyfile                          		D - # dev-v0.3.1 - Reverse proxy config - >>> Domain changes, 1
│   └── *caddy*                              
│       └── *certificates*             		       *# OPTIONAL - where certificates go for caddy via Let's Encrypt if testing*
├── cms/
│   └── urls.py                             	    # dev-v0.1.0 - Django URL routing - >>>>>>> Changes if non-HTTPS
├── files/models/
│   └── media.py							   		# dev-v1.0.0 - Smart encode modifications
├── static/js/
│   ├── cytube-export.js                    		# dev-v0.1.0 - CyTube export button via media page
│   └── encoding-status.js                  		# dev-v0.1.7 - Real-time encoding widget status
├── templates/
│   └── root.html                           	    # dev-v0.1.0 - Custom UI templates
```



  ## MediaCMS for CyTube Storage Architecture for Block Storage
  
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
  └──userlogos/          # User avatars

Container: /home/mediacms.io/mediacms/media_files/ (mounted from above via docker-compose.yaml)
```

  # Looking for the Original MediaCMS?

  The original project can be located here: https://github.com/mediacms-io/mediacms

  MediaCMS is a modern, fully featured open source video and media CMS. It is developed to meet the needs of modern web platforms for viewing and sharing media. It can be used to build a small to medium video and media portal within minutes.

  It is built mostly using the modern stack Django + React and includes a REST API.

  ## Contact

  info@mediacms.io
