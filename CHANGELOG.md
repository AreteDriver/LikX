# Changelog

All notable changes to LikX are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.24.0] - 2026-01-10

### Added
- Wayland scroll capture support with ydotool and wtype
- GIF dithering options: none, Bayer, Floyd-Steinberg, Sierra
- Configurable GIF loop count (infinite, once, 2x, 3x)
- Optional gifsicle optimization for smaller GIF files
- 6 new translations: French, German, Portuguese, Italian, Russian, Japanese
- 33 new tests (955 total)

### Changed
- Full GIF settings tab in Settings dialog
- Improved code formatting with ruff

## [3.23.0] - 2026-01-10

### Added
- Full internationalization (i18n) with gettext-based translation system
- Spanish (Español) translation
- GIF recording with configurable FPS and quality
- Scrolling screenshots with OpenCV template matching
- Multi-monitor quick-select with number keys (1-9)
- Customizable hotkeys in Settings
- Cloud upload providers: Amazon S3, Dropbox, Google Drive

### Changed
- 891 tests passing with full coverage for new modules

## [3.22.0] - 2026-01-08

### Added
- Flatpak packaging support
- CI/CD pipeline with test coverage
- Command palette (Ctrl+Shift+P)
- Radial menu (right-click)
- OCR text extraction via Tesseract
- Pin to desktop (always-on-top floating window)
- Visual effects: shadow, border, rounded corners
- History browser with thumbnails
- Cloud upload (Imgur)

### Changed
- 780 tests passing
- Professional release with feature parity to ShareX/CleanShot

## [3.21.0] - 2026-01-06

### Changed
- Sidebar and context bar UI refactor
- Improved annotation tool organization

## [3.11.0] - 2026-01-06

### Added
- GIF screen recording (ffmpeg on X11, wf-recorder on Wayland)

## [3.10.0] - 2026-01-06

### Changed
- Project structure cleanup
- Cursor alignment and UI improvements

## [3.9.0] - 2026-01-06

### Added
- Comprehensive unit tests for core modules

## [3.2.0] - 2026-01-06

### Added
- Hybrid dark theme with improved usability

## [3.1.0] - 2026-01-06

### Added
- .deb packaging for Ubuntu/Debian installation

## [3.0.0] - 2026-01-06

### Added
- Initial LikX release (renamed from Linux_SnipTool)
- Fullscreen, region, and window capture
- X11 and Wayland support (GNOME, KDE, Sway)
- 10 annotation tools: pen, highlighter, line, arrow, rectangle, ellipse, text, blur, pixelate, eraser
- Undo/redo, selection, alignment guides
- Grid snap, grouping, z-ordering
- Opacity control and transformations
- Professional CI/CD pipeline with linting
- Application launcher and icons
- MIT License

[3.24.0]: https://github.com/AreteDriver/LikX/compare/v3.23.0...v3.24.0
[3.23.0]: https://github.com/AreteDriver/LikX/compare/v3.22.0...v3.23.0
[3.22.0]: https://github.com/AreteDriver/LikX/compare/v3.21.0...v3.22.0
[3.21.0]: https://github.com/AreteDriver/LikX/compare/v3.11.0...v3.21.0
[3.11.0]: https://github.com/AreteDriver/LikX/compare/v3.10.0...v3.11.0
[3.10.0]: https://github.com/AreteDriver/LikX/compare/v3.9.0...v3.10.0
[3.9.0]: https://github.com/AreteDriver/LikX/compare/v3.2.0...v3.9.0
[3.2.0]: https://github.com/AreteDriver/LikX/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/AreteDriver/LikX/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/AreteDriver/LikX/commits/v3.0.0
