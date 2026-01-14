# LikX

**Polished screenshot utility for Ubuntu** — Region capture, annotation, OCR, and pin-to-desktop with production-grade UX.

[![CI](https://github.com/AreteDriver/LikX/actions/workflows/ci.yml/badge.svg)](https://github.com/AreteDriver/LikX/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![GTK: 3.0](https://img.shields.io/badge/GTK-3.0-orange.svg)](https://www.gtk.org/)

```
23,000+ lines of Python | 955 tests | 8 languages | X11 + Wayland
```

---

## Installation

### AppImage (Recommended)

Download and run — no installation required:

```bash
# Download latest AppImage
wget https://github.com/AreteDriver/LikX/releases/latest/download/LikX-3.22.0-x86_64.AppImage

# Make executable
chmod +x LikX-3.22.0-x86_64.AppImage

# Run
./LikX-3.22.0-x86_64.AppImage
```

### Snap Store

```bash
sudo snap install likx
```

### Debian/Ubuntu (.deb)

```bash
# Download .deb package
wget https://github.com/AreteDriver/LikX/releases/latest/download/likx_3.22.0_all.deb

# Install
sudo dpkg -i likx_3.22.0_all.deb
sudo apt-get install -f  # Install dependencies if needed
```

### From Source

```bash
git clone https://github.com/AreteDriver/LikX.git
cd LikX/LikX
./setup.sh
python3 main.py
```

---

## Screenshots

| Capture | Editor | Settings |
|---------|--------|----------|
| ![Capture](assets/screenshots/capture.png) | ![Editor](assets/screenshots/editor.png) | ![Settings](assets/screenshots/settings.png) |

*Screenshots coming soon — run `python3 main.py` to see the full UI*

---

## What It Does

LikX fills the gap in Linux desktop tooling, providing feature parity with Windows/Mac tools like ShareX and CleanShot while supporting both X11 and Wayland.

### Capture Modes
- **Fullscreen** — Capture entire screen
- **Region** — Click and drag to select area
- **Window** — Click to capture specific window
- **Scrolling** — Capture long pages automatically
- **GIF Recording** — Record screen as animated GIF

### Editor Tools
- **Drawing** — Pen, highlighter, shapes, arrows
- **Text** — Add labels and annotations
- **Privacy** — Blur and pixelate sensitive data
- **Effects** — Shadow, border, rounded corners
- **OCR** — Extract text from screenshots

### Workflow Features
- **Pin to Desktop** — Keep screenshots visible while working
- **History Browser** — Visual thumbnail browser
- **Cloud Upload** — One-click Imgur sharing
- **Hotkeys** — Global shortcuts for quick capture

---

## Global Hotkeys (GNOME)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+F` | Fullscreen capture |
| `Ctrl+Shift+R` | Region capture |
| `Ctrl+Shift+W` | Window capture |

Configure in GNOME Settings → Keyboard → Custom Shortcuts.

---

## Feature Comparison

| Feature | LikX | Flameshot | Ksnip | Shutter |
|---------|:----:|:---------:|:-----:|:-------:|
| Wayland | ✓ | Partial | ✓ | ✗ |
| X11 | ✓ | ✓ | ✓ | ✓ |
| GIF Recording | ✓ | ✗ | ✗ | ✗ |
| Scrolling Capture | ✓ | ✗ | ✗ | ✓ |
| OCR | ✓ | ✗ | ✓ | ✗ |
| Pin to Desktop | ✓ | ✗ | ✗ | ✗ |
| Visual Effects | ✓ | ✗ | ✗ | ✓ |
| Blur/Pixelate | ✓ | ✓ | ✓ | ✓ |
| Cloud Upload | ✓ | ✓ | ✓ | ✓ |
| Multi-language | ✓ | ✓ | ✓ | ✓ |
| AppImage | ✓ | ✓ | ✓ | ✗ |

---

## Supported Languages

- English
- French (Français)
- German (Deutsch)
- Spanish (Español)
- Portuguese (Português)
- Italian (Italiano)
- Russian (Русский)
- Japanese (日本語)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GTK3 Window Manager                       │
├─────────────────────────────────────────────────────────────┤
│  Capture Module                                              │
│  ├── X11: xdotool, scrot                                    │
│  └── Wayland: grim, gnome-screenshot, spectacle             │
├─────────────────────────────────────────────────────────────┤
│  Editor Module                                               │
│  ├── Cairo drawing surface                                  │
│  ├── Annotation tools (pen, shapes, text, arrows)           │
│  └── Undo/redo stack                                        │
├─────────────────────────────────────────────────────────────┤
│  Feature Modules                                             │
│  ├── OCR: Tesseract integration                             │
│  ├── Effects: Shadow, border, corners                       │
│  ├── Pin: Always-on-top floating window                     │
│  ├── History: Thumbnail browser with search                 │
│  ├── GIF: Recording with dithering options                  │
│  └── Upload: Imgur API integration                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Development

```bash
# Clone and setup
git clone https://github.com/AreteDriver/LikX.git
cd LikX/LikX
./setup.sh

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src/
ruff format src/
```

---

## Requirements

### Runtime
- Python 3.8+
- GTK 3.0 (`python3-gi`, `gir1.2-gtk-3.0`)
- Cairo (`python3-cairo`)
- Tesseract (optional, for OCR)

### Wayland-specific
- `grim` or `gnome-screenshot` or `spectacle`
- `slurp` (for region selection)
- `ydotool` or `wtype` (for scroll capture)

### X11-specific
- `xdotool`
- `scrot` or `maim`

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Links

- **Releases**: [GitHub Releases](https://github.com/AreteDriver/LikX/releases)
- **Issues**: [GitHub Issues](https://github.com/AreteDriver/LikX/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
