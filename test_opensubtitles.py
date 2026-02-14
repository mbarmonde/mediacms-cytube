# dev-v0.1.2 - TESTING ONLY - OpenSubtitles API Connection Test

#!/usr/bin/env python3
# test_opensubtitles.py - OpenSubtitles API Connection Test
# v0.1.2 - Supports both permanent JWT token and username/password login
# v0.1.1 - Fixed authentication to use login + JWT token
# v0.1.0 - Initial Release
# Purpose: Verify API key and test search/download functionality
# Usage: python3 test_opensubtitles.py

import requests
import json
import sys
import os

# Test Configuration
API_KEY = os.environ.get('OPENSUBTITLES_API_KEY', 'mNfx57Kx1VgrZYKLfKGkanEkKEjmTdzE')
API_URL = "https://api.opensubtitles.com/api/v1"
USER_AGENT = "MediaCMS-CyTube/1.0"

# Authentication Methods (in order of preference)
# Method 1: Permanent JWT token from user profile (RECOMMENDED)
OPENSUBTITLES_JWT_TOKEN = os.environ.get('OPENSUBTITLES_JWT_TOKEN', '')

# Method 2: Username/password login (fallback)
OPENSUBTITLES_USERNAME = os.environ.get('OPENSUBTITLES_USERNAME', '')
OPENSUBTITLES_PASSWORD = os.environ.get('OPENSUBTITLES_PASSWORD', '')

# Test movie for search (your example from foundational docs)
TEST_QUERY = "Moonraker"
TEST_YEAR = "1979"

def get_jwt_token():
    """Get JWT token - either from env var or via login"""
    print("\n" + "="*60)
    print("AUTHENTICATION: Getting JWT Token")
    print("="*60)
    
    # Method 1: Use permanent token if available
    if OPENSUBTITLES_JWT_TOKEN:
        print("✅ Using permanent JWT token from environment")
        print(f"Token: {OPENSUBTITLES_JWT_TOKEN[:20]}...{OPENSUBTITLES_JWT_TOKEN[-20:]}")
        return OPENSUBTITLES_JWT_TOKEN
    
    # Method 2: Login with username/password
    if not OPENSUBTITLES_USERNAME or not OPENSUBTITLES_PASSWORD:
        print("❌ CRITICAL: No authentication credentials found")
        print("\nOpenSubtitles API requires either:")
        print("  1. OPENSUBTITLES_JWT_TOKEN (permanent token from profile) - RECOMMENDED")
        print("     Get from: https://www.opensubtitles.com/en/users/YOUR_USERNAME")
        print("\n  2. OPENSUBTITLES_USERNAME + OPENSUBTITLES_PASSWORD")
        print("\nPlease set one of these methods in environment variables or .env file")
        return None
    
    print(f"Using username/password login")
    print(f"Username: {OPENSUBTITLES_USERNAME}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    
    headers = {
        'Api-Key': API_KEY,
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'username': OPENSUBTITLES_USERNAME,
        'password': OPENSUBTITLES_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{API_URL}/login",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            user_info = data.get('user', {})
            
            print("✅ Login successful!")
            print(f"User ID: {user_info.get('user_id', 'N/A')}")
            print(f"Allowed downloads: {user_info.get('allowed_downloads', 'N/A')}")
            print(f"Remaining downloads: {user_info.get('remaining_downloads', 'N/A')}")
            print(f"JWT Token: {token[:20]}...{token[-20:] if token else ''}")
            
            return token
        elif response.status_code == 401:
            print("❌ Login failed - Invalid username or password")
            print(f"Response: {response.text}")
            return None
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def test_subtitle_search(jwt_token):
    """Test: Search for subtitles using API Key + JWT"""
    print("\n" + "="*60)
    print("TEST 1: Subtitle Search")
    print("="*60)
    print(f"Searching for: {TEST_QUERY} ({TEST_YEAR})")
    
    headers = {
        'Api-Key': API_KEY,
        'Authorization': f'Bearer {jwt_token}',
        'User-Agent': USER_AGENT
    }
    
    params = {
        'query': TEST_QUERY,
        'year': TEST_YEAR,
        'languages': 'en'
    }
    
    try:
        response = requests.get(
            f"{API_URL}/subtitles",
            headers=headers,
            params=params,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            results = data.get('data', [])
            
            print(f"✅ Search successful!")
            print(f"Total results: {total}")
            print(f"Results returned: {len(results)}")
            
            if results:
                print("\nTop 3 Results:")
                for i, subtitle in enumerate(results[:3], 1):
                    attrs = subtitle.get('attributes', {})
                    files = attrs.get('files', [])
                    file_id = files[0].get('file_id') if files else 'N/A'
                    
                    print(f"\n  [{i}] Release: {attrs.get('release', 'Unknown')}")
                    print(f"      Downloads: {attrs.get('download_count', 0)}")
                    print(f"      File ID: {file_id}")
                    print(f"      Language: {attrs.get('language', 'en')}")
                    print(f"      Format: {attrs.get('format', 'N/A')}")
                
                # Return first file_id for download test
                if files:
                    return files[0].get('file_id')
            else:
                print("⚠️  No subtitles found for this query")
                
            return None
        else:
            print(f"❌ Search failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def test_subtitle_download(jwt_token, file_id):
    """Test: Download subtitle file"""
    print("\n" + "="*60)
    print("TEST 2: Subtitle Download")
    print("="*60)
    
    if not file_id:
        print("⚠️  Skipped - No file_id from search test")
        return False
    
    print(f"Downloading file_id: {file_id}")
    
    headers = {
        'Api-Key': API_KEY,
        'Authorization': f'Bearer {jwt_token}',
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'file_id': file_id
    }
    
    try:
        response = requests.post(
            f"{API_URL}/download",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get('link')
            file_name = data.get('file_name')
            remaining = data.get('remaining')
            
            print("✅ Download link retrieved successfully!")
            print(f"File name: {file_name}")
            print(f"Download URL: {download_url[:50]}..." if download_url else "N/A")
            print(f"Remaining downloads today: {remaining}")
            
            # Test actual file download
            if download_url:
                print("\nTesting actual file download...")
                file_response = requests.get(download_url, timeout=10)
                
                if file_response.status_code == 200:
                    content_length = len(file_response.content)
                    print(f"✅ File downloaded successfully! Size: {content_length} bytes")
                    
                    # Show first 200 characters of subtitle content
                    content_preview = file_response.text[:200]
                    print(f"\nContent preview:\n{content_preview}...")
                    return True
                else:
                    print(f"❌ File download failed: {file_response.status_code}")
                    return False
        elif response.status_code == 406:
            print("❌ Download failed - Quota exceeded or rate limited")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ Download failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("OPENSUBTITLES API TEST SUITE")
    print("MediaCMS-CyTube Integration v1.2.0")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    print(f"User-Agent: {USER_AGENT}")
    
    # Run tests
    test_results = {
        'authentication': False,
        'search': False,
        'download': False
    }
    
    # Get JWT token (either permanent or via login)
    jwt_token = get_jwt_token()
    test_results['authentication'] = jwt_token is not None
    
    if not jwt_token:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with other tests.")
        print("\nPlease provide either:")
        print("  1. OPENSUBTITLES_JWT_TOKEN (from your profile)")
        print("  2. OPENSUBTITLES_USERNAME + OPENSUBTITLES_PASSWORD")
        sys.exit(1)
    
    # Test 1: Search
    file_id = test_subtitle_search(jwt_token)
    test_results['search'] = file_id is not None
    
    # Test 2: Download
    if file_id:
        test_results['download'] = test_subtitle_download(jwt_token, file_id)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Authentication: {'✅ PASS' if test_results['authentication'] else '❌ FAIL'}")
    print(f"Search:         {'✅ PASS' if test_results['search'] else '❌ FAIL'}")
    print(f"Download:       {'✅ PASS' if test_results['download'] else '❌ FAIL'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! OpenSubtitles API integration is ready.")
        print("You can proceed with Phase 2: Creating subtitle_fetcher.py")
    else:
        print("\n⚠️  Some tests failed. Please review errors above before proceeding.")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
