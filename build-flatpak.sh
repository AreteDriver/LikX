#!/bin/bash
# Build LikX Flatpak package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_ID="com.github.aretedriver.likx"
MANIFEST="${APP_ID}.yml"

echo "=== LikX Flatpak Builder ==="

# Check for flatpak-builder
if ! command -v flatpak-builder &> /dev/null; then
    echo "Error: flatpak-builder not found"
    echo "Install with: sudo apt install flatpak-builder"
    exit 1
fi

# Install runtime and SDK if needed
echo "Ensuring GNOME runtime is available..."
flatpak install -y --user flathub org.gnome.Platform//47 org.gnome.Sdk//47 2>/dev/null || true

# Clean previous build
echo "Cleaning previous build..."
rm -rf build-dir repo

# Build the flatpak
echo "Building Flatpak..."
flatpak-builder --user --force-clean build-dir "$MANIFEST"

# Create repository
echo "Creating repository..."
flatpak-builder --user --repo=repo --force-clean build-dir "$MANIFEST"

# Build bundle for distribution
echo "Creating bundle..."
flatpak build-bundle repo "${APP_ID}.flatpak" "$APP_ID"

echo ""
echo "=== Build Complete ==="
echo "Bundle: ${APP_ID}.flatpak"
echo ""
echo "To install locally:"
echo "  flatpak install --user ${APP_ID}.flatpak"
echo ""
echo "To run:"
echo "  flatpak run ${APP_ID}"
