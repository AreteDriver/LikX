#!/bin/bash
# LikX - Application Installer
# Installs desktop entry and icons for system-wide access

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON_DIR="$SCRIPT_DIR/resources/icons"

echo "Installing LikX..."

# Install icons to user icon directory
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
mkdir -p ~/.local/share/icons/hicolor/128x128/apps
mkdir -p ~/.local/share/icons/hicolor/64x64/apps
mkdir -p ~/.local/share/icons/hicolor/48x48/apps
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

cp "$ICON_DIR/likx-256.png" ~/.local/share/icons/hicolor/256x256/apps/likx.png
cp "$ICON_DIR/likx-128.png" ~/.local/share/icons/hicolor/128x128/apps/likx.png
cp "$ICON_DIR/likx-64.png" ~/.local/share/icons/hicolor/64x64/apps/likx.png
cp "$ICON_DIR/likx-48.png" ~/.local/share/icons/hicolor/48x48/apps/likx.png
cp "$ICON_DIR/app_icon.svg" ~/.local/share/icons/hicolor/scalable/apps/likx.svg

echo "  Icons installed"

# Update desktop file with correct path
mkdir -p ~/.local/share/applications
sed "s|/home/arete/projects/LikX/LikX|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/likx.desktop" > ~/.local/share/applications/likx.desktop

echo "  Desktop entry installed"

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

echo ""
echo "Installation complete!"
echo "LikX should now appear in your application menu."
echo ""
echo "You can also run it from the terminal:"
echo "  python3 $SCRIPT_DIR/main.py"
