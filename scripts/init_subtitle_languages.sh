#!/bin/bash
# dev-v1.0.0

#####
# v1.0.0 - Initial release
# Populates the files_language table with standard languages for subtitle support
# Safe to run multiple times (uses ON CONFLICT DO NOTHING)
# Designed to run from HOST (not inside container)
#####

# Stored at: /mediacms/scripts/init_subtitle_languages.sh

set -e

echo "🌐 Initializing subtitle language support..."

# Check current language count via docker exec to db container
LANG_COUNT=$(docker exec mediacms-db-1 psql -U mediacms -t -c "SELECT COUNT(*) FROM files_language;" 2>/dev/null | xargs || echo "0")

echo "   Current languages in database: $LANG_COUNT"

if [ "$LANG_COUNT" -ge "20" ]; then
    echo "   ✅ Languages already populated (found $LANG_COUNT languages)"
    exit 0
fi

echo "   📝 Populating language table..."

# Insert languages via docker exec to db container
docker exec mediacms-db-1 psql -U mediacms << 'EOF'
INSERT INTO files_language (code, title) VALUES 
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
    ('ru', 'Russian'),
    ('ja', 'Japanese'),
    ('zh', 'Chinese'),
    ('ar', 'Arabic'),
    ('ko', 'Korean'),
    ('nl', 'Dutch'),
    ('pl', 'Polish'),
    ('sv', 'Swedish'),
    ('tr', 'Turkish'),
    ('hi', 'Hindi'),
    ('th', 'Thai'),
    ('vi', 'Vietnamese'),
    ('cs', 'Czech'),
    ('da', 'Danish')
ON CONFLICT (code) DO NOTHING;
EOF

# Verify
NEW_LANG_COUNT=$(docker exec mediacms-db-1 psql -U mediacms -t -c "SELECT COUNT(*) FROM files_language;" | xargs)

echo "   ✅ Language initialization complete!"
echo "   📊 Total languages available: $NEW_LANG_COUNT"

# Display languages
echo ""
echo "   Available subtitle languages:"
docker exec mediacms-db-1 psql -U mediacms -c "SELECT code, title FROM files_language ORDER BY title;"
