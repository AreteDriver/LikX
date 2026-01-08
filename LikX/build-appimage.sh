#!/bin/bash
# Build script for LikX AppImage
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="LikX"
VERSION="3.22.0"
ARCH="x86_64"
APPDIR="AppDir"

echo "=== Building $APP_NAME AppImage v$VERSION ==="

# Clean previous build
rm -rf "${APPDIR}/opt" "${APPDIR}/usr"
mkdir -p "${APPDIR}/opt/likx/src" "${APPDIR}/opt/likx/resources"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
echo "Copying application files..."
cp main.py "${APPDIR}/opt/likx/"
cp -r src/* "${APPDIR}/opt/likx/src/"
cp -r resources/* "${APPDIR}/opt/likx/resources/"

# Copy desktop file and icon
cp "${APPDIR}/likx.desktop" "${APPDIR}/usr/share/applications/"
cp resources/icons/likx-256.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/likx.png"
cp resources/icons/likx-256.png "${APPDIR}/likx.png"

# Make AppRun executable
chmod +x "${APPDIR}/AppRun"

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage (use --appimage-extract-and-run to work without FUSE)
echo "Building AppImage..."
ARCH=$ARCH APPIMAGE_EXTRACT_AND_RUN=1 ./appimagetool-x86_64.AppImage --no-appstream "${APPDIR}" "${APP_NAME}-${VERSION}-${ARCH}.AppImage"

echo "=== Build complete: ${APP_NAME}-${VERSION}-${ARCH}.AppImage ==="
ls -lh "${APP_NAME}-${VERSION}-${ARCH}.AppImage"
