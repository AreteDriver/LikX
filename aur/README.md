# LikX AUR Package

This directory contains files for submitting LikX to the [Arch User Repository (AUR)](https://aur.archlinux.org/).

## Files

- `PKGBUILD` - Package build script
- `.SRCINFO` - Package metadata (auto-generated from PKGBUILD)

## Submission Steps

### First-time submission

1. **Create AUR account** at https://aur.archlinux.org/register/

2. **Add SSH key** to your AUR account at https://aur.archlinux.org/account/

3. **Clone the AUR package repo**:
   ```bash
   git clone ssh://aur@aur.archlinux.org/likx.git aur-likx
   cd aur-likx
   ```

4. **Copy files**:
   ```bash
   cp /path/to/LikX/aur/PKGBUILD .
   cp /path/to/LikX/aur/.SRCINFO .
   ```

5. **Commit and push**:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Initial upload: likx 3.24.0"
   git push
   ```

### Updating the package

1. **Update version** in `PKGBUILD` (`pkgver` and reset `pkgrel` to 1)

2. **Update sha256sums** (get from release tarball):
   ```bash
   curl -sL https://github.com/AreteDriver/LikX/archive/refs/tags/v3.24.0.tar.gz | sha256sum
   ```

3. **Regenerate .SRCINFO**:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

4. **Test locally**:
   ```bash
   makepkg -si
   ```

5. **Commit and push**:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to 3.25.0"
   git push
   ```

## Testing Locally

```bash
# Build package
makepkg -s

# Install built package
makepkg -si

# Or install without building
makepkg -si --noconfirm
```

## Dependencies

The package requires these Arch packages:
- `python-gobject` - PyGObject for GTK bindings
- `python-cairo` - Cairo bindings
- `python-numpy` - Numerical computing
- `python-opencv` - Computer vision (scroll capture)
- `python-pillow` - Image processing
- `gtk3` - GTK3 libraries
- `libnotify` - Desktop notifications

Optional (for full functionality):
- `xdotool`, `xclip` - X11 support
- `ffmpeg` - GIF recording
- `tesseract` - OCR
- `grim`, `slurp`, `wf-recorder` - Wayland/wlroots support
