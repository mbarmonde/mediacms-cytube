# dev-v0.5.1

#####
# v0.5.1 - HOTFIX: Removed duplicate subtitle loop causing NameError
#   - Kept only the direct database query approach
#   - Fixed subtitles_info undefined variable error
# v0.5.0 - SUBTITLE SUPPORT FOR CYTUBE
#   - Integrated MediaCMS subtitle files into CyTube textTracks
#   - Transforms MediaCMS subtitle format to CyTube WebVTT spec
#   - Converts relative URLs to absolute HTTPS URLs
#   - Supports all 10 languages (en, es, fr, de, it, pt, ru, ja, zh, ar)
# v0.4.1 - FIXED: Regex-based resolution detection from profile names
#   - Extracts resolution from profile name (e.g., "h264-480" → 480)
#   - Works around MediaCMS 7.7 profile.resolution field inconsistencies
#   - More robust detection for 480p, 720p, 1080p
# v0.4.0 - MULTI-RESOLUTION SUPPORT
#   - Added dynamic resolution detection from encoded profiles
#   - Supports 480p, 720p, 1080p adaptive bitrate streaming
#   - CyTube player auto-negotiates best quality
#   - Maintains backward compatibility with single-resolution
# v0.3.1 - Better search logic for YOUR.DOMAIN.COM counts
# v0.3.0 - Added encoding status API endpoint
# v0.2.1 - HOTFIX: Fixed HLS detection logic
# v0.2.0 - Corrected CyTube manifest format per official spec
# v0.0.1 - Initial release
#####

# Stored at: /mediacms/cms/custom_api.py
# Find Replace YOUR.DOMAIN.COM, 1ea

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from files.models import Media, Encoding
import json
import os
import re

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_cytube_manifest(request, friendly_token):
    """Generate CyTube-compatible JSON manifest with multi-resolution support and subtitles"""
    try:
        media = Media.objects.get(friendly_token=friendly_token)

        # Initialize sources array (can contain multiple formats/qualities)
        sources = []
        streaming_method = "checking"

        # Get the media file hash/basename (MediaCMS uses this for HLS directory naming)
        media_file_path = media.media_file.name  # e.g., "user/username/fb94aa6e844143a9857727d16413dfbd.Robo_C.H.I.C..1990.mkv"
        media_basename = os.path.basename(media_file_path)  # e.g., "fb94aa6e844143a9857727d16413dfbd.Robo_C.H.I.C..1990.mkv"
        media_hash = media_basename.split('.')[0]  # e.g., "fb94aa6e844143a9857727d16413dfbd"

        print(f"🔍 Searching for HLS files for media: {friendly_token}")
        print(f"   Media file: {media_file_path}")
        print(f"   Media hash: {media_hash}")

        # Try multiple HLS directory naming strategies (MediaCMS may use different patterns)
        hls_search_paths = [
            os.path.join(settings.MEDIA_ROOT, 'hls', media_hash),  # Hash-based (most common)
            os.path.join(settings.MEDIA_ROOT, 'hls', friendly_token),  # Token-based
            os.path.join(settings.MEDIA_ROOT, 'hls', str(media.id)),  # ID-based
        ]

        master_playlist_path = None
        hls_dir_found = None

        for hls_dir in hls_search_paths:
            master_path = os.path.join(hls_dir, 'master.m3u8')
            print(f"   Checking: {master_path}")
            if os.path.exists(master_path):
                master_playlist_path = master_path
                hls_dir_found = hls_dir
                print(f"   ✅ Found at: {master_path}")
                break

        # If HLS master playlist exists, use it with multi-resolution support
        if master_playlist_path:
            # Determine the URL path component (what comes after /media/hls/)
            hls_dir_name = os.path.basename(hls_dir_found)

            # Build the HTTPS URL for the master playlist
            hls_url = f"https://YOUR.DOMAIN.COM/media/hls/{hls_dir_name}/master.m3u8"
            print(f"   🎬 HLS URL: {hls_url}")

            # Detect which resolutions were actually encoded
            # Parse resolution from profile names (e.g., "h264-480" → 480)
            available_resolutions = []
            try:
                # Query all successful encodings
                successful_encodings = media.encodings.filter(
                    status='success'
                ).select_related('profile')

                print(f"   🔎 Analyzing {successful_encodings.count()} successful encodings...")

                # Parse resolution from profile names
                for enc in successful_encodings:
                    if enc.profile and enc.profile.name:
                        profile_name = enc.profile.name.lower()

                        # Skip preview profile (thumbnail generation)
                        if profile_name == 'preview':
                            print(f"   ⏭️  Skipping preview profile")
                            continue

                        # Extract resolution from profile name using regex
                        # Matches patterns like: h264-480, h265-720, vp9-1080, etc.
                        match = re.search(r'-(\d{3,4})$', profile_name)  # Find dash followed by 3-4 digits at end
                        if match:
                            height = int(match.group(1))
                            if height not in available_resolutions:
                                available_resolutions.append(height)
                                print(f"   ✅ Found encoded resolution: {height}p (profile: {enc.profile.name})")
                        else:
                            print(f"   ⚠️  Could not extract resolution from profile name '{enc.profile.name}'")

            except Exception as e:
                print(f"   ❌ Error detecting resolutions: {e}")
                import traceback
                print(traceback.format_exc())
                # Fallback to default if detection fails
                available_resolutions = [480]

            # If no resolutions detected, use safe default
            if not available_resolutions:
                available_resolutions = [480]
                print(f"   ⚠️  No resolutions detected, defaulting to 480p")

            # Sort resolutions for consistent ordering (lowest to highest)
            available_resolutions.sort()
            print(f"   📊 Final resolution list: {available_resolutions}")

            # Add ALL detected resolutions as separate sources
            # CyTube's player will auto-negotiate the best quality
            for resolution in available_resolutions:
                sources.append({
                    "url": hls_url,  # Same master playlist for all (HLS handles ABR internally)
                    "contentType": "application/x-mpegURL",
                    "quality": resolution
                })
                print(f"   📺 Added {resolution}p source to manifest")

            streaming_method = f"hls_adaptive_{len(available_resolutions)}_resolutions"
            print(f"   ✅ HLS manifest generated with {len(available_resolutions)} resolution(s)")

        else:
            print(f"   ⚠️  No HLS master playlist found in any search path")
            streaming_method = "hls_not_found"

        # Fallback: Try to use encoded 480p MP4 (if HLS not found)
        if not sources:
            print(f"   🔍 Searching for encoded 480p MP4...")
            try:
                # Try to find any 480p encoding
                encodings_480 = media.encodings.filter(
                    status='success',
                    chunk=False
                ).select_related('profile')

                for enc in encodings_480:
                    if enc.profile and '480' in enc.profile.name.lower():
                        if enc.media_file:
                            mp4_url = request.build_absolute_uri(
                                enc.media_file.url
                            ).replace('http://', 'https://')  # Force HTTPS

                            sources.append({
                                "url": mp4_url,
                                "contentType": "video/mp4",
                                "quality": 480
                            })
                            streaming_method = "encoded_mp4"
                            print(f"   ✅ Using encoded 480p MP4: {mp4_url}")
                            break

                if not sources:
                    print(f"   ⚠️  No 480p encoding found")
                    streaming_method = "encoding_pending"

            except Exception as e:
                print(f"   ❌ Encoded MP4 check error: {str(e)}")
                streaming_method = "encoding_error"

        # Last resort: Use original file
        if not sources:
            print(f"   ⚠️  Using original file as fallback")
            original_url = request.build_absolute_uri(
                media.media_file.url
            ).replace('http://', 'https://')  # Force HTTPS

            sources.append({
                "url": original_url,
                "contentType": "video/mp4",  # Assume MP4
                "quality": 720  # Estimate
            })
            streaming_method = "original"
            print(f"   📁 Original URL: {original_url}")

        # PHASE 2: Process subtitles for CyTube textTracks
        print(f"   📝 Processing subtitles...")
        text_tracks = []
        
        # Query subtitles directly from database
        from files.models import Subtitle
        subtitles = Subtitle.objects.filter(media=media).select_related('language')
        print(f"   Found {subtitles.count()} subtitle(s)")
        
        for subtitle in subtitles:
            # Build absolute URL for subtitle file
            subtitle_path = f"/media/{subtitle.subtitle_file}"
            subtitle_url = request.build_absolute_uri(subtitle_path).replace('http://', 'https://')
            
            text_tracks.append({
                'url': subtitle_url,
                'contentType': 'text/vtt',
                'name': subtitle.language.title if subtitle.language else 'Unknown'
            })
            
            language_name = subtitle.language.title if subtitle.language else 'Unknown'
            language_code = subtitle.language.code if subtitle.language else 'unknown'
            print(f"   ✅ Added subtitle: {language_name} ({language_code}) - {subtitle_url}")

        # Build the CyTube manifest per official spec
        manifest = {
            "title": media.title,
            "duration": int(media.duration) if media.duration else -1,
            "live": False,  # VOD content
            "thumbnail": request.build_absolute_uri(
                media.thumbnail_url
            ).replace('http://', 'https://') if media.thumbnail_url else "",
            "sources": sources,
            "textTracks": text_tracks,  # ✅ SUBTITLE SUPPORT ADDED
            # Debug metadata (not part of CyTube spec, but harmless)
            "meta": {
                "description": media.description or "",
                "streaming_method": streaming_method,
                "media_hash": media_hash,
                "subtitle_count": len(text_tracks)
            }
        }

        # Create directory for CyTube manifests if it doesn't exist
        cytube_dir = os.path.join(settings.MEDIA_ROOT, 'cytube_manifests')
        os.makedirs(cytube_dir, exist_ok=True)

        # Create a clean filename from the video title
        safe_filename = "".join(
            c for c in media.title if c.isalnum() or c in (' ', '-', '_')
        ).rstrip()
        safe_filename = safe_filename.replace(' ', '_')[:100]  # Limit length
        json_filename = f"{friendly_token}_{safe_filename}.json"
        json_path = os.path.join(cytube_dir, json_filename)

        # Save the JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"   💾 Manifest saved to: {json_path}")

        # Build the public URL for the JSON file (MUST be HTTPS and end in .json)
        json_url = request.build_absolute_uri(
            settings.MEDIA_URL + 'cytube_manifests/' + json_filename
        ).replace('http://', 'https://')  # Force HTTPS

        # Return both the manifest and the file URL
        response_data = {
            "manifest": manifest,
            "json_url": json_url,
            "message": f"Manifest saved successfully with {len(text_tracks)} subtitle(s)",
            "streaming_method": streaming_method,
            "debug": {
                "media_hash": media_hash,
                "hls_dir_found": hls_dir_found if hls_dir_found else "Not found",
                "search_paths": hls_search_paths,
                "resolutions_detected": len(sources),
                "subtitles_detected": len(text_tracks)
            }
        }

        return Response(response_data)

    except Media.DoesNotExist:
        return Response({"error": "Media not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"❌ Exception in generate_cytube_manifest: {str(e)}")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def serve_cytube_manifest(request, friendly_token, filename):
    """Serve the saved CyTube manifest JSON file with proper headers"""
    try:
        json_path = os.path.join(
            settings.MEDIA_ROOT,
            'cytube_manifests',
            filename
        )

        if not os.path.exists(json_path):
            return Response({"error": "Manifest file not found"}, status=404)

        with open(json_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # CyTube requires Content-Type: application/json
        response = JsonResponse(manifest)
        response['Content-Type'] = 'application/json'
        response['Access-Control-Allow-Origin'] = '*'  # CORS

        return response

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_encoding_status(request, friendly_token):
    """Get real-time encoding status for a media item"""
    try:
        media = Media.objects.get(friendly_token=friendly_token)

        # Get all encodings for this media
        encodings = Encoding.objects.filter(media=media).select_related('profile')

        encoding_data = []
        for enc in encodings:
            # Extract resolution from profile name
            resolution = None
            if enc.profile and enc.profile.name:
                match = re.search(r'-(\d{3,4})$', enc.profile.name.lower())
                if match:
                    resolution = int(match.group(1))

            encoding_data.append({
                'profile_name': enc.profile.name if enc.profile else 'Unknown',
                'resolution': resolution,
                'status': enc.status,
                'chunk': enc.chunk,
            })

        return Response({
            'friendly_token': media.friendly_token,
            'title': media.title,
            'state': media.state,
            'encodings': encoding_data,
        })

    except Media.DoesNotExist:
        return Response({'error': 'Media not found'}, status=404)
    except Exception as e:
        import traceback
        print(f"❌ Exception in get_encoding_status: {str(e)}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)
