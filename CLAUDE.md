# LikX - Claude Code Instructions

## Project Overview
LikX is a GTK3/Python screenshot tool for Linux with annotation, OCR, and cloud upload.

## Architecture
- **Entry point**: `main.py`
- **Core modules**: `src/*.py`
- **GUI**: GTK3 via PyGObject (python3-gi)
- **Config**: `~/.config/likx/config.json`

## Development Commands

```bash
# Run application
python3 main.py

# Lint and format
ruff check src/ main.py
ruff format src/ main.py

# Build packages
./build-deb.sh          # Debian package
./build-appimage.sh     # AppImage

# Snap build (requires snapcraft)
cd snap && snapcraft
```

## Key Files
| File | Purpose |
|------|---------|
| `src/capture.py` | Screenshot capture (X11/Wayland) |
| `src/editor.py` | Annotation drawing tools |
| `src/ui.py` | Main window and dialogs |
| `src/ocr.py` | Tesseract OCR integration |
| `src/pinned.py` | Pin-to-desktop floating window |
| `src/effects.py` | Shadow, border, round corners |
| `src/config.py` | User settings persistence |
| `src/uploader.py` | Imgur cloud upload |

## Packaging
- **Snap**: `snap/snapcraft.yaml` - builds with `snapcraft`
- **AppImage**: `AppDir/` + `build-appimage.sh`
- **Debian**: `debian/` + `build-deb.sh`

## Code Conventions
- Python 3.8+ compatibility
- Type hints encouraged
- GTK signal handlers: `_on_<widget>_<signal>`
- Use `src/config.py` for all settings

## Testing
```bash
pytest tests/ -v
```

## Release Process
1. Update version in `src/__init__.py`, `debian/changelog`, `snap/snapcraft.yaml`, `build-*.sh`
2. Commit and tag: `git tag v3.0.0`
3. Push tag: `git push origin v3.0.0`
4. CI builds and uploads to GitHub Releases
5. Snap auto-publishes to Snap Store (requires SNAP_STORE_TOKEN secret)
