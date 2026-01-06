#!/bin/bash
# Build .deb package for Linux SnipTool (simple dpkg-deb method)
set -e

VERSION="2.0.0"
PKGNAME="linux-sniptool"
ARCH="all"
BUILDDIR="build-deb"

echo "=== Building Linux SnipTool ${VERSION} .deb package ==="

# Clean previous builds
rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}/DEBIAN"
mkdir -p "${BUILDDIR}/opt/linux-sniptool/src"
mkdir -p "${BUILDDIR}/opt/linux-sniptool/resources"
mkdir -p "${BUILDDIR}/usr/bin"
mkdir -p "${BUILDDIR}/usr/share/applications"
mkdir -p "${BUILDDIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILDDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
echo "Copying application files..."
cp main.py "${BUILDDIR}/opt/linux-sniptool/"
cp src/*.py "${BUILDDIR}/opt/linux-sniptool/src/"
cp -r resources/* "${BUILDDIR}/opt/linux-sniptool/resources/"

# Create launcher script
cat > "${BUILDDIR}/usr/bin/linux-sniptool" << 'EOF'
#!/bin/bash
cd /opt/linux-sniptool && exec python3 main.py "$@"
EOF
chmod 755 "${BUILDDIR}/usr/bin/linux-sniptool"

# Desktop entry
cp debian/linux-sniptool.desktop "${BUILDDIR}/usr/share/applications/"

# Icons
cp resources/icons/app_icon.svg "${BUILDDIR}/usr/share/icons/hicolor/scalable/apps/linux-sniptool.svg"
cp resources/icons/sniptool-256.png "${BUILDDIR}/usr/share/icons/hicolor/256x256/apps/linux-sniptool.png"

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
Homepage: https://github.com/AreteDriver/Linux_SnipTool
Description: Screenshot utility with annotation and OCR
 Linux SnipTool is a comprehensive screenshot tool for Linux desktops.
 Features: capture modes (fullscreen, region, window), annotation tools
 (pen, highlighter, arrows, shapes, text), privacy tools (blur, pixelate),
 OCR text extraction, pin-to-desktop, and cloud upload.
EOF

# Set proper permissions
find "${BUILDDIR}" -type d -exec chmod 755 {} \;
find "${BUILDDIR}/opt" -type f -exec chmod 644 {} \;
chmod 755 "${BUILDDIR}/usr/bin/linux-sniptool"

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
