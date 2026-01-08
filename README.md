# LikX

**Polished screenshot utility for Ubuntu** — Region capture, annotation, OCR, and pin-to-desktop with production-grade UX.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LikX/LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![GTK: 3.0](https://img.shields.io/badge/GTK-3.0-orange.svg)](https://www.gtk.org/)

---

## What It Is

LikX is a comprehensive screenshot tool designed to fill the gap in Linux desktop tooling. It provides feature parity with Windows/Mac tools like ShareX and CleanShot while supporting both X11 and Wayland display servers.

Beyond basic capture, the editor includes annotation tools (pen, highlighter, arrows, shapes, text), privacy features (blur, pixelate), OCR text extraction, and a pin-to-desktop mode for reference screenshots.

---

## Problem / Solution / Impact

**Problem**: Linux screenshot tools lag behind Windows/Mac equivalents. Existing options either lack features, don't support Wayland, or have dated UX.

**Solution**: LikX provides:
- Full X11 + Wayland support (GNOME, KDE, Sway)
- 10 annotation tools with professional quality
- OCR text extraction via Tesseract
- Pin-to-desktop for reference while working
- Visual effects (shadow, border, rounded corners)
- History browser with thumbnails
- One-click cloud upload (Imgur)

**Impact** (Intended Outcomes):
- Eliminate context-switching to Windows/Mac for screenshot workflows
- Reduce time spent on documentation with annotation tools
- Enable quick text extraction from images with OCR
- Provide reference screenshots without window clutter via pin mode

---

## Quick Start

### Prerequisites
- Python 3.8+
- GTK 3.0
- X11 or Wayland (GNOME, KDE, or Sway)

### Install

```bash
git clone https://github.com/AreteDriver/LikX.git
cd LikX/LikX
./setup.sh
```

### Run

```bash
python3 main.py
```

### Global Hotkeys (GNOME)
- `Ctrl+Shift+F` — Fullscreen capture
- `Ctrl+Shift+R` — Region capture
- `Ctrl+Shift+W` — Window capture

---

## Architecture

```
[GTK Window Manager Interface]
        |
        v
[Capture Module]  ←── X11 (xdotool) | Wayland (grim/gnome-screenshot/spectacle)
        |
        v
[Editor Module]   ←── Cairo drawing, annotation tools, undo/redo
        |
        ├──> [OCR Module]      ←── Tesseract OCR
        ├──> [Effects Module]  ←── Shadow, border, corners
        ├──> [Pin Module]      ←── Always-on-top floating window
        └──> [Uploader]        ←── Imgur API
```

### Project Structure

```
LikX/
├── LikX/
│   ├── main.py          # Entry point
│   ├── src/
│   │   ├── capture.py   # X11 + Wayland capture
│   │   ├── editor.py    # Annotation suite
│   │   ├── ocr.py       # Text extraction
│   │   ├── pinned.py    # Pin to desktop
│   │   ├── effects.py   # Visual effects
│   │   └── history.py   # History browser
│   ├── resources/       # Icons and assets
│   └── setup.sh         # Installation script
└── README.md
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Capture** | Fullscreen, region, window capture on X11 and Wayland |
| **Annotation** | Pen, highlighter, line, arrow, rectangle, ellipse, text |
| **Privacy** | Blur and pixelate tools for sensitive data |
| **OCR** | Extract text from screenshots via Tesseract |
| **Pin to Desktop** | Keep screenshots visible while working |
| **Effects** | Shadow, border, background, rounded corners |
| **History** | Visual thumbnail browser for all captures |
| **Cloud Upload** | One-click Imgur sharing with auto-copied URL |

---

## Roadmap

- [ ] Native .deb and .rpm packaging
- [ ] Flatpak distribution
- [ ] Additional cloud providers (S3, custom endpoints)
- [ ] Video/GIF recording mode
- [ ] Keyboard shortcut customization UI
- [ ] Multi-monitor support improvements

---

## Demo

<!-- TODO: Add demo GIF showing capture, annotation, and OCR -->
*Demo placeholder: Record capturing a region, adding annotations, and extracting text via OCR*

---

## Contributing

```bash
cd LikX/LikX
./setup.sh
python3 main.py
```

See [LikX/CONTRIBUTING.md](LikX/CONTRIBUTING.md) for guidelines.

---

## License

MIT License — see [LikX/LICENSE](LikX/LICENSE)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/AreteDriver/LikX/issues)
- **Docs**: [LikX/QUICK_START.md](LikX/QUICK_START.md)
