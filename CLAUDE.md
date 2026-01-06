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
| `src/command_palette.py` | Ctrl+Shift+P searchable command interface |
| `src/commands.py` | Command registry for palette |
| `src/radial_menu.py` | Right-click radial tool selector |

## Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Command Palette (search all commands) |
| `Ctrl+S` | Save |
| `Ctrl+C` | Copy to clipboard |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `+` / `-` / `0` | Zoom in / out / reset |
| `Delete` / `Backspace` | Delete selected annotation |
| `Arrow keys` | Nudge selected annotation 1px |
| `Shift+Arrow keys` | Nudge selected annotation 10px |
| `Escape` | Deselect / Cancel |
| `V` | Select tool (move/resize with snap guides) |
| `Shift+Click` | Add to / toggle selection (multi-select) |
| `P` | Pen tool |
| `H` | Highlighter |
| `L` | Line |
| `A` | Arrow (select style from toolbar: open/filled/double) |
| `R` | Rectangle |
| `E` | Ellipse |
| `T` | Text (use toolbar for bold/italic/font) |
| `B` | Blur |
| `X` | Pixelate |
| `M` | Measure |
| `N` | Number marker |
| `I` | Color picker (eyedropper) |
| `S` | Stamp tool |
| `Z` | Zoom tool (scroll to zoom) |
| `K` | Callout/speech bubble |
| `C` | Crop (hold Shift for 1:1 square) |
| Right-click | Radial menu for quick tool selection |

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
