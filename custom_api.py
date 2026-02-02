# dev-v0.3.0

#####
# v0.3.0 - Added encoding status API endpoint
# - New get_encoding_status function for real-time encoding progress
# - Added Encoding model import
# v0.2.1 - HOTFIX: Fixed HLS detection logic
# - Changed to search for HLS files by media file basename (hash)
# - Added multiple path search strategies
# - Better error logging for debugging
# - Handles Bento4's actual directory structure
# v0.2.0 - Corrected CyTube manifest format per official spec
# v0.0.1 - Initial release
#####

# Stored at: /mediacms/cms/custom_api.py
# Find Replace YOUR.DOMAIN.COM

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from files.models import Media, Encoding  # Added Encoding
import json
import os

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_cytube_manifest(request, friendly_token):
    """Generate CyTube-compatible JSON manifest per official spec"""
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
        
        # If HLS master playlist exists, use it
        if master_playlist_path:
            # Determine the URL path component (what comes after /media/hls/)
            # Extract just the directory name (hash, token, or id)
            hls_dir_name = os.path.basename(hls_dir_found)
            
            # Build the HTTPS URL for the master playlist
            hls_url = f"https://YOUR.DOMAIN.COM/media/hls/{hls_dir_name}/master.m3u8"
            print(f"   🎬 HLS URL: {hls_url}")
            
            # Add HLS source with correct CyTube format
            sources.append({
                "url": hls_url,
                "contentType": "application/x-mpegURL",  # HLS MIME type
                "quality": 480  # Our configured resolution
            })
            streaming_method = "hls"
            print(f"   ✅ HLS source added to manifest")
        else:
            print(f"   ⚠️ No HLS master playlist found in any search path")
            streaming_method = "hls_not_found"
        
        # Fallback: Try to use encoded 480p MP4 (if HLS not found)
        if not sources:
            print(f"   🔍 Searching for encoded 480p MP4...")
            try:
                encodings = media.encodings.filter(
                    height=480,
                    status='success',
                    chunk=False
                ).first()
                
                if encodings and encodings.media_file:
                    mp4_url = request.build_absolute_uri(
                        encodings.media_file.url
                    ).replace('http://', 'https://')  # Force HTTPS
                    
                    sources.append({
                        "url": mp4_url,
                        "contentType": "video/mp4",
                        "quality": 480
                    })
                    streaming_method = "encoded_mp4"
                    print(f"   ✅ Using encoded 480p MP4: {mp4_url}")
                else:
                    print(f"   ⚠️ No 480p encoding found")
                    streaming_method = "encoding_pending"
            except Exception as e:
                print(f"   ❌ Encoded MP4 check error: {str(e)}")
                streaming_method = "encoding_error"
        
        # Last resort: Use original file
        if not sources:
            print(f"   ⚠️ Using original file as fallback")
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
        
        # Build the CyTube manifest per official spec
        # Note: No "type" field - CyTube determines player from contentType
        manifest = {
            "title": media.title,
            "duration": int(media.duration) if media.duration else -1,
            "live": False,  # VOD content
            "thumbnail": request.build_absolute_uri(
                media.thumbnail_url
            ).replace('http://', 'https://') if media.thumbnail_url else "",
            "sources": sources,
            "textTracks": [],  # Can add subtitle support later
            # Debug metadata (not part of CyTube spec, but harmless)
            "meta": {
                "description": media.description or "",
                "streaming_method": streaming_method,  # For debugging
                "media_hash": media_hash  # For debugging
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
            "message": f"Manifest saved successfully",
            "streaming_method": streaming_method,
            "debug": {
                "media_hash": media_hash,
                "hls_dir_found": hls_dir_found if hls_dir_found else "Not found",
                "search_paths": hls_search_paths
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
            encoding_data.append({
                'profile_name': enc.profile.name if enc.profile else 'Unknown',
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
