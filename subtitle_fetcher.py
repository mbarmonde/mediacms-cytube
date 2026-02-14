# dev-v0.1.5 - OpenSubtitles.com API Integration for MediaCMS

#!/usr/bin/env python3
# subtitle_fetcher.py - OpenSubtitles.com API Integration for MediaCMS
# v0.1.5 - Fixed Language model to use .title instead of .name (versions v0.1.3, and v0.1.4 didnt work)
# v0.1.2 - Corrected the subtitle path to be exact based on MediaCMs defaults
# v0.1.1 - Changed the subtitle path to be exact based on MediaCMs defaults
# v0.1.0 - Initial Release
# Purpose: Automatically fetch and download subtitles for uploaded videos
# Dependencies: requests, Django settings (from Local_settings.py)

"""
OpenSubtitles.com Integration Module

This module provides automated subtitle fetching for MediaCMS videos using
the OpenSubtitles.com REST API. It extracts movie metadata from filenames,
searches for matching subtitles, and downloads the best match.

Workflow:
1. parse_filename() - Extract title, year from "Movie.Name.2023.1080p.mkv"
2. search_subtitles() - Query OpenSubtitles API for matches
3. download_subtitle() - Download best match and save to storage
4. fetch_subtitle_for_media() - Main entry point (called by Django signal)

Authentication:
- Uses permanent JWT token from OpenSubtitles.com user profile
- Requires both API_KEY (consumer) and JWT_TOKEN (user authentication)

Configuration:
All settings loaded from deploy/docker/local_settings.py via Django settings
"""

import os
import re
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Django imports - must be imported after Django is configured
try:
    from django.conf import settings
except Exception:
    # Gracefully handle if Django isn't configured yet
    settings = None

# Setup logging
logger = logging.getLogger(__name__)

# API Configuration from Django settings (with safe defaults)
def get_setting(name, default):
    """Safely get setting from Django conf"""
    if settings and hasattr(settings, name):
        return getattr(settings, name)
    return default

API_URL = get_setting('OPENSUBTITLES_API_URL', 'https://api.opensubtitles.com/api/v1')
API_KEY = get_setting('OPENSUBTITLES_API_KEY', '')
JWT_TOKEN = get_setting('OPENSUBTITLES_JWT_TOKEN', '')
USER_AGENT = get_setting('OPENSUBTITLES_USER_AGENT', 'MediaCMS-CyTube/1.0')
ENABLED = get_setting('OPENSUBTITLES_ENABLED', False)
AUTO_DOWNLOAD = get_setting('OPENSUBTITLES_AUTO_DOWNLOAD', True)
LANGUAGES = get_setting('OPENSUBTITLES_LANGUAGES', ['en'])
MAX_RESULTS = get_setting('OPENSUBTITLES_MAX_RESULTS', 10)
DOWNLOAD_PATH = get_setting('OPENSUBTITLES_DOWNLOAD_PATH', '/home/mediacms.io/mediacms/media_files/original/subtitles')


class OpenSubtitlesError(Exception):
    """Base exception for OpenSubtitles API errors"""
    pass


class AuthenticationError(OpenSubtitlesError):
    """Raised when API authentication fails"""
    pass


class QuotaExceededError(OpenSubtitlesError):
    """Raised when daily download quota is exceeded"""
    pass


def parse_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract movie/show title and year from filename.
    
    Handles common naming patterns:
    - Moonraker.1979.1080p.BluRay.x264.mkv -> ("Moonraker", "1979")
    - The.Matrix.1999.mkv -> ("The Matrix", "1999")
    - Movie.Name.2023.WEBRip.mp4 -> ("Movie Name", "2023")
    - Some.Movie.mkv -> ("Some Movie", None)
    
    Args:
        filename: Original uploaded filename
        
    Returns:
        Tuple of (title, year) where year may be None if not found
    """
    # Remove file extension
    name = Path(filename).stem
    
    # Pattern 1: Find year (4 digits between 1900-2099)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    year = year_match.group(1) if year_match else None
    
    # Pattern 2: Extract title (everything before year or quality markers)
    quality_markers = r'\b(1080p|2160p|720p|480p|360p|BluRay|BRRip|WEBRip|WEB-DL|HDTV|DVDRip|x264|x265|HEVC|AAC|AC3)\b'
    
    if year:
        # Split at year
        title_part = name.split(year)[0]
    else:
        # Split at quality marker
        quality_split = re.split(quality_markers, name, flags=re.IGNORECASE)
        title_part = quality_split[0]
    
    # Clean title: replace dots/underscores with spaces, strip whitespace
    title = re.sub(r'[._]', ' ', title_part).strip()
    
    # Remove common release group tags in brackets
    title = re.sub(r'\[.*?\]', '', title).strip()
    
    logger.info(f"Parsed filename '{filename}' -> Title: '{title}', Year: {year}")
    
    return (title if title else None, year)


def get_api_headers() -> Dict[str, str]:
    """
    Build headers for OpenSubtitles API requests.
    
    Returns:
        Dictionary of HTTP headers including authentication
        
    Raises:
        AuthenticationError: If API_KEY or JWT_TOKEN is missing
    """
    if not API_KEY:
        raise AuthenticationError("OPENSUBTITLES_API_KEY not configured in settings")
    
    if not JWT_TOKEN:
        raise AuthenticationError("OPENSUBTITLES_JWT_TOKEN not configured in settings")
    
    return {
        'Api-Key': API_KEY,
        'Authorization': f'Bearer {JWT_TOKEN}',
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json'
    }


def search_subtitles(title: str, year: Optional[str] = None, language: str = 'en') -> List[Dict]:
    """
    Search OpenSubtitles.com for matching subtitles.
    
    Args:
        title: Movie or show title
        year: Release year (optional, improves accuracy)
        language: ISO 639-1 language code (default: 'en')
        
    Returns:
        List of subtitle results, sorted by download count (most popular first)
        Empty list if no results found
        
    Raises:
        OpenSubtitlesError: If API request fails
        AuthenticationError: If authentication is invalid
    """
    try:
        headers = get_api_headers()
        
        params = {
            'query': title,
            'languages': language
        }
        
        if year:
            params['year'] = year
        
        logger.info(f"Searching OpenSubtitles for: '{title}' ({year or 'no year'}) in language '{language}'")
        
        response = requests.get(
            f"{API_URL}/subtitles",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API credentials - check API_KEY and JWT_TOKEN")
        
        response.raise_for_status()
        
        data = response.json()
        results = data.get('data', [])
        total = data.get('total_count', 0)
        
        logger.info(f"Found {total} total results, returned {len(results)} results")
        
        # Sort by download count (most popular first)
        sorted_results = sorted(
            results,
            key=lambda x: x.get('attributes', {}).get('download_count', 0),
            reverse=True
        )
        
        return sorted_results[:MAX_RESULTS]
        
    except requests.exceptions.Timeout:
        logger.error("OpenSubtitles API request timed out")
        raise OpenSubtitlesError("API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenSubtitles API request failed: {e}")
        raise OpenSubtitlesError(f"API request failed: {e}")


def download_subtitle(file_id: str, destination_dir: str, filename_prefix: str) -> Optional[str]:
    """
    Download subtitle file from OpenSubtitles.com.
    
    Args:
        file_id: OpenSubtitles file ID from search results
        destination_dir: Directory to save subtitle
        filename_prefix: Prefix for saved file (usually original video filename)
        
    Returns:
        Full path to downloaded subtitle file, or None if download fails
        
    Raises:
        QuotaExceededError: If daily download quota exceeded
        OpenSubtitlesError: If download fails
    """
    try:
        headers = get_api_headers()
        
        payload = {'file_id': file_id}
        
        logger.info(f"Requesting download link for file_id: {file_id}")
        
        response = requests.post(
            f"{API_URL}/download",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 406:
            raise QuotaExceededError("Daily download quota exceeded")
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API credentials during download")
        
        response.raise_for_status()
        
        data = response.json()
        download_url = data.get('link')
        original_filename = data.get('file_name', 'subtitle.srt')
        remaining = data.get('remaining', 'unknown')
        
        logger.info(f"Download link obtained. Remaining downloads: {remaining}")
        
        if not download_url:
            raise OpenSubtitlesError("No download link in API response")
        
        # Download the actual subtitle file
        file_response = requests.get(download_url, timeout=30)
        file_response.raise_for_status()
        
        # Determine file extension from original filename
        ext = Path(original_filename).suffix or '.srt'
        
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Save file with prefix from original video
        dest_filename = f"{filename_prefix}{ext}"
        dest_path = os.path.join(destination_dir, dest_filename)
        
        with open(dest_path, 'wb') as f:
            f.write(file_response.content)
        
        file_size = len(file_response.content)
        logger.info(f"Subtitle downloaded successfully: {dest_path} ({file_size} bytes)")
        
        return dest_path
        
    except requests.exceptions.Timeout:
        logger.error("Subtitle download timed out")
        raise OpenSubtitlesError("Download timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Subtitle download failed: {e}")
        raise OpenSubtitlesError(f"Download failed: {e}")
    except IOError as e:
        logger.error(f"Failed to save subtitle file: {e}")
        raise OpenSubtitlesError(f"Failed to save file: {e}")


def fetch_subtitle_for_media(media_object) -> Optional[Dict[str, str]]:
    """
    Main entry point: Fetch and download subtitle for a MediaCMS media object.
    
    This function is called by Django post_save signal after video encoding completes.
    
    Args:
        media_object: MediaCMS Media model instance
        
    Returns:
        Dictionary with subtitle info if successful, None otherwise
    """
    # Check if feature is enabled
    if not ENABLED:
        logger.debug("OpenSubtitles integration is disabled in settings")
        return None
    
    # Check if auto-download is enabled
    if not AUTO_DOWNLOAD:
        logger.debug("Auto-download is disabled in settings")
        return None
    
    # Check if media already has subtitles (skip to avoid duplicates)
    if hasattr(media_object, 'subtitles') and media_object.subtitles.exists():
        logger.info(f"Media '{media_object.title}' already has subtitles, skipping OpenSubtitles fetch")
        return None
    
    try:
        # Extract title and year from filename
        original_filename = media_object.media_file.name if hasattr(media_object, 'media_file') else media_object.title
        title, year = parse_filename(original_filename)
        
        if not title:
            logger.warning(f"Could not extract title from filename: {original_filename}")
            return None
        
        # Search for subtitles
        language = LANGUAGES[0] if LANGUAGES else 'en'
        results = search_subtitles(title, year, language)
        
        if not results:
            logger.info(f"No subtitles found for '{title}' ({year or 'no year'})")
            return None
        
        # Get best match
        best_match = results[0]
        attrs = best_match.get('attributes', {})
        files = attrs.get('files', [])
        
        if not files:
            logger.warning(f"Best match has no files: {attrs.get('release', 'unknown')}")
            return None
        
        file_id = files[0].get('file_id')
        release_name = attrs.get('release', 'unknown')
        download_count = attrs.get('download_count', 0)
        
        logger.info(f"Selected subtitle: '{release_name}' (downloads: {download_count})")
        
        # Determine destination directory
        user = media_object.user
        dest_dir = os.path.join(DOWNLOAD_PATH, 'user', user.username)
        
        # Use media hash as filename prefix
        filename_prefix = str(media_object.uid).replace('-', '')
        
        # Download subtitle
        subtitle_path = download_subtitle(file_id, dest_dir, filename_prefix)
        
        if not subtitle_path:
            logger.error("Download returned no path")
            return None
        
        # Create Subtitle database entry to link with Media
        try:
            from files.models import Subtitle, Language
            
            # Get Language object
            try:
                language_obj = Language.objects.get(code=language)
                logger.info(f"Found Language object: {language_obj.code} - {language_obj.title}")
            except Language.DoesNotExist:
                logger.warning(f"Language '{language}' not found, using first available")
                language_obj = Language.objects.first()
                if not language_obj:
                    raise OpenSubtitlesError("No Language objects exist in database")
            
            # Create relative path for MediaCMS
            relative_path = subtitle_path.replace('/home/mediacms.io/mediacms/media_files/', '')
            
            # Create Subtitle entry
            subtitle_obj, created = Subtitle.objects.get_or_create(
                media=media_object,
                language=language_obj,
                defaults={
                    'subtitle_file': relative_path,
                    'user': media_object.user
                }
            )
            
            if created:
                logger.info(f"✅ Created Subtitle database entry: {subtitle_obj.id}")
            else:
                logger.info(f"⚠️ Subtitle entry already exists: {subtitle_obj.id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create Subtitle database entry: {e}", exc_info=True)
        
        # Return subtitle info
        return {
            'path': subtitle_path,
            'language': language,
            'filename': os.path.basename(subtitle_path),
            'source': 'opensubtitles.com',
            'release': release_name
        }
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return None
    except QuotaExceededError as e:
        logger.warning(f"Download quota exceeded: {e}")
        return None
    except OpenSubtitlesError as e:
        logger.error(f"OpenSubtitles error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching subtitle: {e}", exc_info=True)
        return None
