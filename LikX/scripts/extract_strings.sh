#!/bin/bash
# Extract translatable strings from LikX source files
# Creates/updates locale/likx.pot template file

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOCALE_DIR="$PROJECT_DIR/locale"
POT_FILE="$LOCALE_DIR/likx.pot"

# Create locale directory if it doesn't exist
mkdir -p "$LOCALE_DIR"

echo "Extracting translatable strings from LikX..."

# Extract strings using xgettext
xgettext \
    --language=Python \
    --keyword=_ \
    --keyword=ngettext:1,2 \
    --from-code=UTF-8 \
    --output="$POT_FILE" \
    --package-name="LikX" \
    --package-version="3.0.0" \
    --copyright-holder="LikX Contributors" \
    --msgid-bugs-address="https://github.com/AreteDriver/LikX/issues" \
    --add-comments=TRANSLATORS \
    "$PROJECT_DIR"/src/*.py \
    "$PROJECT_DIR"/main.py

# Count extracted strings
STRING_COUNT=$(grep -c '^msgid "' "$POT_FILE" 2>/dev/null || echo 0)
# Subtract 1 for the empty msgid at the top
STRING_COUNT=$((STRING_COUNT - 1))

echo "Extracted $STRING_COUNT translatable strings to $POT_FILE"

# Instructions
echo ""
echo "To create a new translation:"
echo "  msginit -i $POT_FILE -o locale/<lang>/LC_MESSAGES/likx.po -l <lang>"
echo ""
echo "To update an existing translation:"
echo "  msgmerge -U locale/<lang>/LC_MESSAGES/likx.po $POT_FILE"
echo ""
echo "To compile a translation:"
echo "  msgfmt locale/<lang>/LC_MESSAGES/likx.po -o locale/<lang>/LC_MESSAGES/likx.mo"
