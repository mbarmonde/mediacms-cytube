#!/bin/bash
# dev-v1.0.3

#####
# v1.0.3 - FIXED: Use direct SQL command instead of heredoc
#   - Heredoc wasn't properly passing SQL to psql
#   - Now uses psql -c with full SQL string
# v1.0.2 - Added error checking and debug output
# v1.0.1 - Auto-detect DB container name
# v1.0.0 - Initial release
#####

# Stored at: /mediacms/scripts/init_subtitle_languages.sh

set -e

echo "🌐 Initializing subtitle language support..."

# Auto-detect database container name
if docker ps --format '{{.Names}}' | grep -q "^mediacms-db-1$"; then
    DB_CONTAINER="mediacms-db-1"
elif docker ps --format '{{.Names}}' | grep -q "^mediacms_db$"; then
    DB_CONTAINER="mediacms_db"
elif docker ps --format '{{.Names}}' | grep -q "mediacms.*db"; then
    DB_CONTAINER=$(docker ps --format '{{.Names}}' | grep "mediacms.*db" | head -n1)
else
    echo "   ❌ Error: Could not find MediaCMS database container"
    echo "   Available containers:"
    docker ps --format '{{.Names}}'
    exit 1
fi

echo "   Using database container: $DB_CONTAINER"

# Check current language count
LANG_COUNT=$(docker exec "$DB_CONTAINER" psql -U mediacms -d mediacms -t -c "SELECT COUNT(*) FROM files_language;" | xargs)

echo "   Current languages in database: $LANG_COUNT"

if [ "$LANG_COUNT" -ge "20" ]; then
    echo "   ✅ Languages already populated (found $LANG_COUNT languages)"
    exit 0
fi

echo "   📝 Populating language table..."

# Insert each language individually for reliability
declare -a LANGUAGES=(
    "en:English"
    "es:Spanish"
    "fr:French"
    "de:German"
    "it:Italian"
    "pt:Portuguese"
    "ru:Russian"
    "ja:Japanese"
    "zh:Chinese"
    "ar:Arabic"
    "ko:Korean"
    "nl:Dutch"
    "pl:Polish"
    "sv:Swedish"
    "tr:Turkish"
    "hi:Hindi"
    "th:Thai"
    "vi:Vietnamese"
    "cs:Czech"
    "da:Danish"
)

INSERTED=0
for lang in "${LANGUAGES[@]}"; do
    CODE="${lang%%:*}"
    TITLE="${lang##*:}"

    # Check if language already exists
    EXISTS=$(docker exec "$DB_CONTAINER" psql -U mediacms -d mediacms -t -c "SELECT COUNT(*) FROM files_language WHERE code='$CODE';" | xargs)

    if [ "$EXISTS" -eq "0" ]; then
        docker exec "$DB_CONTAINER" psql -U mediacms -d mediacms -c "INSERT INTO files_language (code, title) VALUES ('$CODE', '$TITLE');" > /dev/null
        echo "      ✓ Added: $TITLE ($CODE)"
        INSERTED=$((INSERTED + 1))
    else
        echo "      - Skipped: $TITLE ($CODE) - already exists"
    fi
done

# Verify final count
NEW_LANG_COUNT=$(docker exec "$DB_CONTAINER" psql -U mediacms -d mediacms -t -c "SELECT COUNT(*) FROM files_language;" | xargs)

echo ""
echo "   ✅ Language initialization complete!"
echo "   📊 Languages added: $INSERTED"
echo "   📊 Total languages available: $NEW_LANG_COUNT"

# Display all languages
echo ""
echo "   Available subtitle languages:"
docker exec "$DB_CONTAINER" psql -U mediacms -d mediacms -c "SELECT code, title FROM files_language ORDER BY title;"