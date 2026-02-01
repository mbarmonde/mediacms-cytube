  # MediaCMS for CyTube (MediaCMS 7.2)

  This clone of MediaCMS features integration into Cytube, including:
  - HLS Streaming at 480p - MediaCMS encodes all uploads to H.264 480p HLS with 6-second segments using veryfast preset
  - CyTube Integration - Custom API generates CyTube-compatible JSON manifests with application/x-mpegURL content type per CyTube best practices
  - Real-time Encoding Status Widget - JavaScript widget (v1.7) displays encoding progress with ETA calculation, auto-updates every 3 seconds, shows "Ready for Export to CyTube!" when complete
  - One-click Export Button - Floating button on video pages copies CyTube manifest URL to clipboard
  - Block Storage Integration - All media stored on with proper volume mounts
  - Automated Container Health - Healthcheck script automatically configures nginx (removes CORS conflicts, sets upload timeouts) and activates only h264-480 + preview encoding profiles on every restart
  - Large File Upload Support - Handles 2-8GB files with 10GB max size, 2-hour timeout for chunk finalization

  # Original MediaCMS

  The original project can be located here: https://github.com/mediacms-io/mediacms


  MediaCMS is a modern, fully featured open source video and media CMS. It is developed to meet the needs of modern web platforms for viewing and sharing media. It can be used to build a small to medium video and media portal within minutes.

  It is built mostly using the modern stack Django + React and includes a REST API.

  ## (TBD) Will be featured at some point at
  - [Show and tell](https://github.com/mediacms-io/mediacms/discussions/categories/show-and-tell) how you are using the project
  - Star the project
  - Add functionality, work on a PR, fix an issue!

  ## Contact

  info@mediacms.io
