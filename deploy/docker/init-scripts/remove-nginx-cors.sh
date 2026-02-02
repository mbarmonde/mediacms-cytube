#!/bin/bash

# dev-v0.1.0

#####
# v0.1.0 - Created
#####

# Remove nginx CORS headers on container startup
# Letting Caddy handle all CORS

set -e

echo "🔧 Removing nginx CORS headers..."

# Backup original config (if not already backed up)
if [ ! -f /etc/nginx/sites-enabled/default.original ]; then
    cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.original
fi

# Comment out CORS headers
sed -i 's/^[[:space:]]*add_header.*Access-Control/# &/' /etc/nginx/sites-enabled/default

# Reload nginx
nginx -t && nginx -s reload

echo "✅ Nginx CORS headers removed"
