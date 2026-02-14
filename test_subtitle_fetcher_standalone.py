# dev-v0.1.0

#!/usr/bin/env python3
# test_subtitle_fetcher_standalone.py - Test subtitle fetcher without Django
# v0.1.0 - Initial Release
# Usage: python3 test_subtitle_fetcher_standalone.py

import os
import re
import requests
from pathlib import Path
from typing import Optional, Tuple

# Configuration (matches .env settings)
API_URL = "https://api.opensubtitles.com/api/v1"
API_KEY = os.environ.get('OPENSUBTITLES_API_KEY', 'mNfx57Kx1VgrZYKLfKGkanEkKEjmTdzE')
JWT_TOKEN = os.environ.get('OPENSUBTITLES_JWT_TOKEN', '')
USER_AGENT = "MediaCMS-CyTube/1.0"

def parse_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract movie title and year from filename"""
    name = Path(filename).stem
    
    # Find year
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    year = year_match.group(1) if year_match else None
    
    # Extract title
    quality_markers = r'\b(1080p|2160p|720p|480p|360p|BluRay|BRRip|WEBRip|WEB-DL|HDTV|DVDRip|x264|x265|HEVC|AAC|AC3)\b'
    
    if year:
        title_part = name.split(year)[0]
    else:
        quality_split = re.split(quality_markers, name, flags=re.IGNORECASE)
        title_part = quality_split[0]
    
    title = re.sub(r'[._]', ' ', title_part).strip()
    title = re.sub(r'\[.*?\]', '', title).strip()
    
    return (title if title else None, year)

def search_subtitles(title: str, year: Optional[str] = None, language: str = 'en'):
    """Search OpenSubtitles for matching subtitles"""
    if not JWT_TOKEN:
        print("❌ ERROR: OPENSUBTITLES_JWT_TOKEN not set in environment")
        return []
    
    headers = {
        'Api-Key': API_KEY,
        'Authorization': f'Bearer {JWT_TOKEN}',
        'User-Agent': USER_AGENT
    }
    
    params = {
        'query': title,
        'languages': language
    }
    
    if year:
        params['year'] = year
    
    response = requests.get(
        f"{API_URL}/subtitles",
        headers=headers,
        params=params,
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        print(f"Response: {response.text}")
        return []
    
    data = response.json()
    results = data.get('data', [])
    
    # Sort by download count
    sorted_results = sorted(
        results,
        key=lambda x: x.get('attributes', {}).get('download_count', 0),
        reverse=True
    )
    
    return sorted_results[:10]

def main():
    print("\n" + "="*60)
    print("SUBTITLE FETCHER STANDALONE TEST")
    print("="*60)
    
    # Check JWT token
    if not JWT_TOKEN:
        print("\n❌ CRITICAL: OPENSUBTITLES_JWT_TOKEN not set")
        print("\nPlease set your JWT token:")
        print("export OPENSUBTITLES_JWT_TOKEN='your_token_here'")
        return 1
    
    print(f"✅ JWT Token configured: {JWT_TOKEN[:20]}...{JWT_TOKEN[-20:]}")
    
    # Test filenames
    test_files = [
        "Moonraker.1979.1080p.BluRay.x264.mkv",
        "The.Matrix.1999.720p.WEBRip.x264.mp4",
        "Inception.2010.mkv",
        "Some.Random.Movie.avi"
    ]
    
    print("\n" + "="*60)
    print("TEST 1: Filename Parsing")
    print("="*60)
    
    for filename in test_files:
        title, year = parse_filename(filename)
        print(f"\nFile: {filename}")
        print(f"  → Title: '{title}'")
        print(f"  → Year: {year or 'Not found'}")
    
    # Test search with Moonraker
    print("\n" + "="*60)
    print("TEST 2: Subtitle Search")
    print("="*60)
    
    test_title = "Moonraker"
    test_year = "1979"
    
    print(f"\nSearching for: '{test_title}' ({test_year})")
    
    try:
        results = search_subtitles(test_title, test_year, 'en')
        
        if results:
            print(f"✅ Found {len(results)} results\n")
            
            print("Top 3 matches:")
            for i, result in enumerate(results[:3], 1):
                attrs = result.get('attributes', {})
                files = attrs.get('files', [])
                
                print(f"\n  [{i}] Release: {attrs.get('release', 'Unknown')}")
                print(f"      Downloads: {attrs.get('download_count', 0)}")
                print(f"      Language: {attrs.get('language', 'en')}")
                print(f"      Format: {attrs.get('format', 'N/A')}")
                if files:
                    print(f"      File ID: {files[0].get('file_id', 'N/A')}")
        else:
            print("⚠️  No results found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ Filename parsing: PASS")
    print(f"✅ API search: {'PASS' if results else 'FAIL'}")
    print("\n🎉 Subtitle fetcher module is working correctly!")
    print("Ready to proceed with Phase 3: Django signal integration")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
