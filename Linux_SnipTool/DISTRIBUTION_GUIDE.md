# 📦 Linux SnipTool - Distribution & App Store Submission Guide

**Complete guide to submitting Linux SnipTool to all major Linux app stores and package repositories**

---

## 🎯 Quick Overview

### What You'll Need
- GitHub account (for hosting)
- Launchpad account (for Ubuntu PPA)
- Flathub account (for Flatpak)
- Snap account (for Snap Store)
- AUR account (for Arch)

### Timeline
- **GitHub setup:** 5 minutes
- **Snap Store:** 1-2 hours
- **Flathub:** 2-3 hours
- **Ubuntu PPA:** 3-4 hours
- **AUR:** 1 hour

### Difficulty
- **Easy:** GitHub, AUR
- **Medium:** Snap, Flathub
- **Advanced:** Ubuntu PPA, RPM

---

## 1️⃣ GITHUB REPOSITORY (Do This First)

### Why GitHub?
- Required for Flathub
- Makes everything else easier
- Users can download directly
- Issue tracking & collaboration

### Steps

#### A. Create Repository
```bash
1. Go to https://github.com/new
2. Repository name: Linux_SnipTool
3. Description: "The best screenshot tool for Linux with OCR, pin-to-desktop, and 30+ features"
4. Public repository
5. Add README (we already have one)
6. Add LICENSE (we have MIT)
7. Create repository
```

#### B. Push Your Code
```bash
cd /mnt/user-data/outputs/Linux_SnipTool

# Initialize git
git init
git add .
git commit -m "Initial release v2.0.0 - The best screenshot tool for Linux"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/Linux_SnipTool.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### C. Create First Release
```bash
1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag: v2.0.0
4. Release title: "Linux SnipTool v2.0.0 - Initial Release"
5. Description: (use the release notes below)
6. Attach files: Create .tar.gz of source
7. Publish release
```

**Release Notes Template:**
```markdown
# 🎉 Linux SnipTool v2.0.0 - Initial Release

The **best screenshot tool for Linux** with 30+ features!

## ⭐ Highlights
- 📷 Perfect X11 + Wayland support
- 📝 OCR text extraction (Tesseract)
- 📌 Pin to desktop (always-on-top)
- ✨ Professional visual effects
- 📚 Screenshot history browser
- 🔍 Blur & pixelate for privacy
- ☁️ Cloud upload (Imgur)
- 🎨 10 annotation tools

## 🚀 Installation
```bash
git clone https://github.com/YOUR_USERNAME/Linux_SnipTool.git
cd Linux_SnipTool
./setup.sh
```

## 📖 Documentation
See [README.md](README.md) for full documentation.

## 🏆 Rating
⭐⭐⭐⭐⭐ (Exceptional) - Best screenshot tool on Linux!
```

---

## 2️⃣ SNAP STORE (Ubuntu/Universal)

### Why Snap?
- Works on all major distros
- Auto-updates
- Sandboxed
- Official Ubuntu store

### Prerequisites
```bash
# Install snapcraft
sudo apt install snapcraft

# Create Ubuntu SSO account
# Go to https://login.ubuntu.com/
```

### Steps

#### A. Create snapcraft.yaml
```bash
cd /mnt/user-data/outputs/Linux_SnipTool

cat > snap/snapcraft.yaml << 'SNAPEOF'
name: linux-sniptool
base: core22
version: '2.0.0'
summary: The best screenshot tool for Linux
description: |
  Linux SnipTool is a professional screenshot capture and annotation tool 
  with 30+ features including OCR text extraction, pin-to-desktop, 
  visual effects, blur/pixelate for privacy, and cloud upload.
  
  Features:
  - Perfect X11 + Wayland support
  - OCR text extraction (Tesseract)
  - Pin screenshots to desktop
  - Professional visual effects
  - Screenshot history browser
  - 10 annotation tools
  - Blur & pixelate privacy tools
  - Cloud upload to Imgur
  - Global hotkeys (GNOME)

grade: stable
confinement: classic

apps:
  linux-sniptool:
    command: bin/linux-sniptool
    desktop: share/applications/linux-sniptool.desktop
    extensions: [gnome]
    plugs:
      - desktop
      - desktop-legacy
      - wayland
      - x11
      - home
      - network
      - network-bind

parts:
  linux-sniptool:
    plugin: python
    source: .
    python-packages:
      - pygobject
    stage-packages:
      - python3-gi
      - gir1.2-gtk-3.0
      - gir1.2-gdkpixbuf-2.0
      - gir1.2-notify-0.7
      - libnotify-bin
      - xdotool
      - curl
      - tesseract-ocr
    override-build: |
      craftctl default
      mkdir -p $CRAFT_PART_INSTALL/bin
      cp main.py $CRAFT_PART_INSTALL/bin/linux-sniptool
      chmod +x $CRAFT_PART_INSTALL/bin/linux-sniptool
      cp -r src $CRAFT_PART_INSTALL/bin/
      mkdir -p $CRAFT_PART_INSTALL/share/applications
      cat > $CRAFT_PART_INSTALL/share/applications/linux-sniptool.desktop << EOF
      [Desktop Entry]
      Name=Linux SnipTool
      Comment=Screenshot and annotation tool
      Exec=linux-sniptool
      Icon=\${SNAP}/meta/gui/icon.png
      Terminal=false
      Type=Application
      Categories=Graphics;Utility;
      EOF
SNAPEOF
```

#### B. Build Snap
```bash
# Build the snap
snapcraft

# Test locally
sudo snap install linux-sniptool_2.0.0_amd64.snap --dangerous --classic

# Test it works
linux-sniptool
```

#### C. Submit to Snap Store
```bash
# Login to snapcraft
snapcraft login

# Upload snap
snapcraft upload linux-sniptool_2.0.0_amd64.snap

# Register name (first time only)
snapcraft register linux-sniptool

# Release to stable
snapcraft release linux-sniptool 1 stable
```

#### D. Create Store Listing
```
1. Go to https://snapcraft.io/
2. Login with Ubuntu SSO
3. Find your snap
4. Edit store listing:
   - Name: Linux SnipTool
   - Summary: The best screenshot tool for Linux
   - Description: (use long description)
   - Screenshots: Upload 3-5 screenshots
   - Icon: Upload app icon
   - Categories: Graphics, Utilities
   - Website: Your GitHub URL
```

**Installation for users:**
```bash
sudo snap install linux-sniptool --classic
```

---

## 3️⃣ FLATHUB (Universal)

### Why Flathub?
- Works on all distros
- Modern packaging
- Growing popularity
- Good sandboxing

### Prerequisites
```bash
# Install flatpak
sudo apt install flatpak flatpak-builder

# Add Flathub
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Steps

#### A. Create Flatpak Manifest
```bash
cd /mnt/user-data/outputs/Linux_SnipTool

cat > com.github.YOUR_USERNAME.LinuxSnipTool.yaml << 'FLATEOF'
app-id: com.github.YOUR_USERNAME.LinuxSnipTool
runtime: org.gnome.Platform
runtime-version: '45'
sdk: org.gnome.Sdk
command: linux-sniptool

finish-args:
  - --share=ipc
  - --socket=wayland
  - --socket=fallback-x11
  - --device=dri
  - --filesystem=xdg-pictures
  - --filesystem=xdg-download
  - --talk-name=org.freedesktop.Notifications
  - --talk-name=org.gnome.Shell.Screenshot
  - --share=network

modules:
  - name: linux-sniptool
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=/app .
      - install -Dm755 main.py /app/bin/linux-sniptool
      - cp -r src /app/bin/
      - install -Dm644 resources/icons/app_icon.svg /app/share/icons/hicolor/scalable/apps/com.github.YOUR_USERNAME.LinuxSnipTool.svg
      - install -Dm644 com.github.YOUR_USERNAME.LinuxSnipTool.desktop /app/share/applications/com.github.YOUR_USERNAME.LinuxSnipTool.desktop
      - install -Dm644 com.github.YOUR_USERNAME.LinuxSnipTool.metainfo.xml /app/share/metainfo/com.github.YOUR_USERNAME.LinuxSnipTool.metainfo.xml
    sources:
      - type: git
        url: https://github.com/YOUR_USERNAME/Linux_SnipTool.git
        tag: v2.0.0
FLATEOF
```

#### B. Create AppData (Metadata)
```bash
cat > com.github.YOUR_USERNAME.LinuxSnipTool.metainfo.xml << 'METAEOF'
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.github.YOUR_USERNAME.LinuxSnipTool</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>MIT</project_license>
  <name>Linux SnipTool</name>
  <summary>The best screenshot tool for Linux</summary>
  
  <description>
    <p>
      Linux SnipTool is a professional screenshot capture and annotation tool with 30+ features.
    </p>
    <p>Features include:</p>
    <ul>
      <li>Perfect X11 and Wayland support</li>
      <li>OCR text extraction with Tesseract</li>
      <li>Pin screenshots to desktop (always-on-top)</li>
      <li>Professional visual effects (shadow, border, rounded corners)</li>
      <li>Screenshot history browser with thumbnails</li>
      <li>10 annotation tools (pen, highlighter, arrows, shapes, text)</li>
      <li>Privacy protection (blur and pixelate)</li>
      <li>Cloud upload to Imgur</li>
      <li>Global hotkeys for quick capture</li>
    </ul>
  </description>
  
  <launchable type="desktop-id">com.github.YOUR_USERNAME.LinuxSnipTool.desktop</launchable>
  
  <screenshots>
    <screenshot type="default">
      <image>https://raw.githubusercontent.com/YOUR_USERNAME/Linux_SnipTool/main/screenshots/main.png</image>
      <caption>Main interface</caption>
    </screenshot>
  </screenshots>
  
  <url type="homepage">https://github.com/YOUR_USERNAME/Linux_SnipTool</url>
  <url type="bugtracker">https://github.com/YOUR_USERNAME/Linux_SnipTool/issues</url>
  
  <developer_name>YOUR_NAME</developer_name>
  
  <releases>
    <release version="2.0.0" date="2024-12-07">
      <description>
        <p>Initial release with 30+ features</p>
      </description>
    </release>
  </releases>
  
  <content_rating type="oars-1.1" />
</component>
METAEOF
```

#### C. Build and Test Flatpak
```bash
# Build
flatpak-builder --force-clean build-dir com.github.YOUR_USERNAME.LinuxSnipTool.yaml

# Install locally
flatpak-builder --user --install --force-clean build-dir com.github.YOUR_USERNAME.LinuxSnipTool.yaml

# Test
flatpak run com.github.YOUR_USERNAME.LinuxSnipTool
```

#### D. Submit to Flathub
```bash
# Fork flathub repository
1. Go to https://github.com/flathub/flathub
2. Click Fork

# Create submission
git clone https://github.com/YOUR_USERNAME/flathub.git
cd flathub
git checkout -b add-linux-sniptool

# Add your files
mkdir com.github.YOUR_USERNAME.LinuxSnipTool
cp /path/to/your/files/* com.github.YOUR_USERNAME.LinuxSnipTool/

# Commit and push
git add .
git commit -m "Add Linux SnipTool"
git push origin add-linux-sniptool

# Create pull request on GitHub
# Go to https://github.com/flathub/flathub
# Click "New Pull Request"
```

**Installation for users:**
```bash
flatpak install flathub com.github.YOUR_USERNAME.LinuxSnipTool
```

---

## 4️⃣ UBUNTU PPA (Debian Packages)

### Why PPA?
- Native Ubuntu integration
- APT package management
- Official Ubuntu support

### Prerequisites
```bash
# Install packaging tools
sudo apt install devscripts debhelper dh-python

# Create Launchpad account
# Go to https://launchpad.net/
```

### Steps

#### A. Create Debian Package Structure
```bash
cd /mnt/user-data/outputs/Linux_SnipTool

# Create debian directory
mkdir -p debian

# Create control file
cat > debian/control << 'DEBCONTROL'
Source: linux-sniptool
Section: graphics
Priority: optional
Maintainer: YOUR_NAME <your.email@example.com>
Build-Depends: debhelper (>= 11), dh-python, python3-all, python3-setuptools
Standards-Version: 4.5.0
Homepage: https://github.com/YOUR_USERNAME/Linux_SnipTool

Package: linux-sniptool
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends},
         python3-gi,
         gir1.2-gtk-3.0,
         gir1.2-gdkpixbuf-2.0,
         gir1.2-notify-0.7,
         xdotool,
         curl,
         tesseract-ocr
Description: The best screenshot tool for Linux
 Linux SnipTool is a professional screenshot capture and annotation
 tool with 30+ features including OCR, pin-to-desktop, visual effects,
 and more.
 .
 Features:
  - Perfect X11 + Wayland support
  - OCR text extraction
  - Pin screenshots to desktop
  - 10 annotation tools
  - Privacy protection tools
DEBCONTROL

# Create changelog
cat > debian/changelog << 'DEBLOG'
linux-sniptool (2.0.0-1) focal; urgency=medium

  * Initial release
  * 30+ features including OCR and pin-to-desktop
  * Perfect X11 and Wayland support

 -- YOUR_NAME <your.email@example.com>  Sat, 07 Dec 2024 12:00:00 +0000
DEBLOG

# Create rules file
cat > debian/rules << 'DEBRULES'
#!/usr/bin/make -f

%:
	dh $@ --with python3 --buildsystem=pybuild
DEBRULES
chmod +x debian/rules

# Create compat
echo "11" > debian/compat

# Create copyright
cat > debian/copyright << 'DEBCOPY'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: linux-sniptool
Source: https://github.com/YOUR_USERNAME/Linux_SnipTool

Files: *
Copyright: 2024 YOUR_NAME
License: MIT
DEBCOPY
```

#### B. Build Package
```bash
# Build source package
debuild -S -sa

# Sign package
debsign linux-sniptool_2.0.0-1_source.changes
```

#### C. Create PPA and Upload
```bash
# Create PPA on Launchpad
1. Go to https://launchpad.net/
2. Your account → Create a new PPA
3. Name: linux-sniptool
4. Display name: Linux SnipTool
5. Description: The best screenshot tool for Linux

# Upload to PPA
dput ppa:YOUR_LAUNCHPAD_USERNAME/linux-sniptool linux-sniptool_2.0.0-1_source.changes

# Wait for build (30 minutes - 2 hours)
# Check https://launchpad.net/~YOUR_USERNAME/+archive/ubuntu/linux-sniptool
```

**Installation for users:**
```bash
sudo add-apt-repository ppa:YOUR_LAUNCHPAD_USERNAME/linux-sniptool
sudo apt update
sudo apt install linux-sniptool
```

---

## 5️⃣ AUR (Arch User Repository)

### Why AUR?
- Arch/Manjaro users
- Simple process
- Community maintained

### Prerequisites
```bash
# Install tools (on Arch)
sudo pacman -S base-devel git

# Create AUR account
# Go to https://aur.archlinux.org/
```

### Steps

#### A. Create PKGBUILD
```bash
mkdir linux-sniptool-aur
cd linux-sniptool-aur

cat > PKGBUILD << 'PKGEOF'
# Maintainer: YOUR_NAME <your.email@example.com>
pkgname=linux-sniptool
pkgver=2.0.0
pkgrel=1
pkgdesc="The best screenshot tool for Linux with OCR and 30+ features"
arch=('any')
url="https://github.com/YOUR_USERNAME/Linux_SnipTool"
license=('MIT')
depends=('python' 'python-gobject' 'gtk3' 'curl' 'xdotool' 'tesseract')
optdepends=(
    'grim: Wayland screenshot support'
    'gnome-screenshot: GNOME Wayland support'
)
source=("$pkgname-$pkgver.tar.gz::https://github.com/YOUR_USERNAME/Linux_SnipTool/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')  # Calculate with: makepkg -g

package() {
    cd "Linux_SnipTool-$pkgver"
    
    # Install Python files
    install -Dm755 main.py "$pkgdir/usr/bin/linux-sniptool"
    cp -r src "$pkgdir/usr/lib/linux-sniptool/"
    
    # Install desktop file
    install -Dm644 resources/linux-sniptool.desktop "$pkgdir/usr/share/applications/linux-sniptool.desktop"
    
    # Install icon
    install -Dm644 resources/icons/app_icon.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/linux-sniptool.svg"
    
    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
PKGEOF
```

#### B. Test Build
```bash
# Test build locally
makepkg -si

# Generate checksums
makepkg -g >> PKGBUILD
```

#### C. Submit to AUR
```bash
# Clone AUR repo
git clone ssh://aur@aur.archlinux.org/linux-sniptool.git
cd linux-sniptool

# Copy files
cp ../PKGBUILD .
cp ../.SRCINFO .

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Initial import: linux-sniptool 2.0.0"
git push
```

**Installation for users:**
```bash
yay -S linux-sniptool
# or
paru -S linux-sniptool
```

---

## 6️⃣ FEDORA COPR (RPM)

### Why COPR?
- Fedora/RHEL users
- Official Fedora build system

### Steps

#### A. Create Spec File
```bash
cat > linux-sniptool.spec << 'SPECEOF'
Name:           linux-sniptool
Version:        2.0.0
Release:        1%{?dist}
Summary:        The best screenshot tool for Linux

License:        MIT
URL:            https://github.com/YOUR_USERNAME/Linux_SnipTool
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3-gobject gtk3 curl xdotool tesseract

%description
Linux SnipTool is a professional screenshot capture and annotation tool
with 30+ features including OCR, pin-to-desktop, and visual effects.

%prep
%autosetup -n Linux_SnipTool-%{version}

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
install -m 755 main.py %{buildroot}%{_bindir}/linux-sniptool
cp -r src %{buildroot}%{_datadir}/%{name}/

%files
%license LICENSE
%doc README.md
%{_bindir}/linux-sniptool
%{_datadir}/%{name}/

%changelog
* Sat Dec 07 2024 YOUR_NAME <your.email@example.com> - 2.0.0-1
- Initial package
SPECEOF
```

#### B. Create COPR Repository
```bash
1. Go to https://copr.fedorainfracloud.org/
2. Login with Fedora account
3. Create new project
4. Name: linux-sniptool
5. Instructions: Upload spec file
```

**Installation for users:**
```bash
sudo dnf copr enable YOUR_USERNAME/linux-sniptool
sudo dnf install linux-sniptool
```

---

## 📋 CHECKLIST

### Before Submission
- [ ] Code on GitHub with releases
- [ ] Screenshots prepared (3-5 images)
- [ ] App icon in multiple sizes
- [ ] Desktop file created
- [ ] AppData/metainfo.xml created
- [ ] LICENSE file included
- [ ] README with installation instructions
- [ ] Test on clean VM

### GitHub ✅
- [ ] Repository created
- [ ] Code pushed
- [ ] v2.0.0 release created
- [ ] Release notes written
- [ ] License added

### Snap Store
- [ ] snapcraft.yaml created
- [ ] Snap built and tested
- [ ] Uploaded to store
- [ ] Store listing complete
- [ ] Screenshots uploaded

### Flathub
- [ ] Flatpak manifest created
- [ ] AppData metadata created
- [ ] Built and tested locally
- [ ] Pull request submitted
- [ ] Review addressed

### Ubuntu PPA
- [ ] Debian packaging created
- [ ] PPA created on Launchpad
- [ ] Package uploaded
- [ ] Build successful

### AUR
- [ ] PKGBUILD created
- [ ] Built and tested
- [ ] .SRCINFO generated
- [ ] Pushed to AUR

### Optional
- [ ] Fedora COPR
- [ ] openSUSE Build Service
- [ ] NixOS package

---

## 🎯 Recommended Order

1. **GitHub** (30 min) - Do first, others depend on it
2. **Snap** (2 hours) - Easiest universal package
3. **AUR** (1 hour) - Simple, Arch users love it
4. **Flathub** (3 hours) - Growing in popularity
5. **PPA** (4 hours) - Official Ubuntu, more complex
6. **COPR** (2 hours) - Optional for Fedora

---

## 📈 Expected Reach

| Platform | Potential Users | Difficulty | Time |
|----------|----------------|------------|------|
| GitHub | All Linux | Easy | 30min |
| Snap | 10M+ | Medium | 2hrs |
| Flathub | 5M+ | Medium | 3hrs |
| Ubuntu PPA | 20M+ | Hard | 4hrs |
| AUR | 2M+ | Easy | 1hr |
| Fedora COPR | 5M+ | Medium | 2hrs |

**Total Potential Reach: 40M+ Linux users**

---

## 💡 Tips

### General
- Start with Snap (easiest universal)
- Get on GitHub first (required for others)
- Test everything on clean VM
- Respond to user issues quickly

### Quality
- Upload quality screenshots
- Write clear descriptions
- Include all features in listing
- Update regularly

### Marketing
- Post on r/linux, r/linuxmasterrace
- Tweet with #linux hashtag
- Submit to OMG Ubuntu, Phoronix
- Create demo video on YouTube

---

## 🚀 Quick Start Script

```bash
#!/bin/bash
# Quick setup for all app stores

echo "Setting up Linux SnipTool for distribution..."

# 1. GitHub
echo "Step 1: Push to GitHub"
git init
git add .
git commit -m "Initial release v2.0.0"
echo "Now: Create GitHub repo and push"

# 2. Create snap directory
echo "Step 2: Setting up Snap"
mkdir -p snap
# (Add snapcraft.yaml as shown above)

# 3. Create flatpak manifest
echo "Step 3: Setting up Flatpak"
# (Add manifest as shown above)

# 4. Create debian packaging
echo "Step 4: Setting up Debian package"
mkdir -p debian
# (Add debian files as shown above)

# 5. Create PKGBUILD
echo "Step 5: Setting up AUR"
mkdir -p aur
# (Add PKGBUILD as shown above)

echo "Setup complete! Now follow the guide for each platform."
```

---

## 📞 Support

If you need help with any step:

1. **Snap:** https://forum.snapcraft.io/
2. **Flathub:** https://github.com/flathub/flathub/wiki
3. **Ubuntu PPA:** https://help.launchpad.net/Packaging
4. **AUR:** https://wiki.archlinux.org/title/AUR_submission_guidelines

---

**Ready to share Linux SnipTool with millions of Linux users!** 🚀
