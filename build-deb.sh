#!/bin/bash
# Build .deb package for LikX (simple dpkg-deb method)
set -e

VERSION="3.0.0"
PKGNAME="likx"
ARCH="all"
BUILDDIR="build-deb"

echo "=== Building LikX ${VERSION} .deb package ==="

# Clean previous builds
rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}/DEBIAN"
mkdir -p "${BUILDDIR}/opt/likx/src"
mkdir -p "${BUILDDIR}/opt/likx/resources"
mkdir -p "${BUILDDIR}/usr/bin"
mkdir -p "${BUILDDIR}/usr/share/applications"
mkdir -p "${BUILDDIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILDDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
echo "Copying application files..."
cp main.py "${BUILDDIR}/opt/likx/"
cp src/*.py "${BUILDDIR}/opt/likx/src/"
cp -r resources/* "${BUILDDIR}/opt/likx/resources/"

# Create launcher script
cat > "${BUILDDIR}/usr/bin/likx" << 'EOF'
#!/bin/bash
cd /opt/likx && exec python3 main.py "$@"
EOF
chmod 755 "${BUILDDIR}/usr/bin/likx"

# Desktop entry
cp debian/likx.desktop "${BUILDDIR}/usr/share/applications/"

# Icons
cp resources/icons/likx.svg "${BUILDDIR}/usr/share/icons/hicolor/scalable/apps/likx.svg"
cp resources/icons/likx-256.png "${BUILDDIR}/usr/share/icons/hicolor/256x256/apps/likx.png"

# Create control file
cat > "${BUILDDIR}/DEBIAN/control" << EOF
Package: ${PKGNAME}
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.8), python3-gi, python3-gi-cairo, python3-cairo, gir1.2-gtk-3.0, gir1.2-gdkpixbuf-2.0, xdotool
Recommends: tesseract-ocr, xclip
Suggests: tesseract-ocr-eng
Maintainer: AreteDriver <aretedriver@users.noreply.github.com>
Homepage: https://github.com/AreteDriver/LikX
Description: Screenshot utility with annotation and OCR
 LikX is a comprehensive screenshot tool for Linux desktops.
 Features: capture modes (fullscreen, region, window), annotation tools
 (pen, highlighter, arrows, shapes, text), privacy tools (blur, pixelate),
 OCR text extraction, pin-to-desktop, and cloud upload.
EOF

# Set proper permissions
find "${BUILDDIR}" -type d -exec chmod 755 {} \;
find "${BUILDDIR}/opt" -type f -exec chmod 644 {} \;
chmod 755 "${BUILDDIR}/usr/bin/likx"

# Build the package
echo "Building .deb package..."
dpkg-deb --build --root-owner-group "${BUILDDIR}" "${PKGNAME}_${VERSION}_${ARCH}.deb"

# Cleanup
rm -rf "${BUILDDIR}"

echo ""
echo "=== Build complete ==="
ls -lh "${PKGNAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Install with: sudo dpkg -i ${PKGNAME}_${VERSION}_${ARCH}.deb"
echo "Fix deps:     sudo apt-get install -f"
