# dev-v0.1.3

#####
# v0.1.3 - Fixed import for root-level custom_api
# v0.1.2 - Fixed import path for custom_api
# v0.1.1 - Fixed import (absolute instead of relative)
# v0.1.0 - Added encoding status endpoint
# v0.0.1 - Initial release
#####

# Stored at: /mediacms/custom_urls.py
# This file should help route the JSON manifest

from django.urls import path
import custom_api  # Both files are at /mediacms/ root level

urlpatterns = [
    # Generate and save CyTube manifest
    path('api/v1/media/<str:friendly_token>/cytube-manifest/',
         custom_api.generate_cytube_manifest,
         name='cytube_manifest'),
    
    # Serve saved CyTube manifest file
    path('api/v1/media/<str:friendly_token>/cytube-manifest/<str:filename>',
         custom_api.serve_cytube_manifest,
         name='serve_cytube_manifest'),
    
    # Get encoding status (NEW)
    path('api/encoding-status/<str:friendly_token>/',
         custom_api.get_encoding_status,
         name='encoding_status'),
]
