# Linux SnipTool 2.0 - Quick Start Guide

## Installation (60 seconds)

```bash
git clone https://github.com/AreteDriver/Linux_SnipTool.git
cd Linux_SnipTool
./setup.sh
```

That's it! The script handles everything.

## First Run

```bash
python3 main.py
```

Or search for "Linux SnipTool" in your application menu.

## Quick Captures

### From GUI
1. Launch app
2. Click "Capture Fullscreen", "Capture Region", or "Capture Window"
3. Editor opens automatically
4. Annotate and save

### From Command Line
```bash
# Fullscreen (quick save, no editor)
python3 main.py --fullscreen --no-edit

# Region selection
python3 main.py --region

# Window capture
python3 main.py --window
```

### Using Global Hotkeys (GNOME)
After first run, these work anywhere:
- **Ctrl+Shift+F** - Fullscreen
- **Ctrl+Shift+R** - Region  
- **Ctrl+Shift+W** - Window

## Editor Tools

### Drawing
- **Pen** ✏️ - Freehand drawing
- **Highlighter** 🖍️ - Transparent highlight
- **Line** 📏 - Straight lines
- **Arrow** ➡️ - Directional arrows
- **Rectangle** ⬜ - Boxes
- **Ellipse** ⭕ - Circles/ovals
- **Text** 📝 - Add text (opens dialog)
- **Eraser** 🗑️ - Remove annotations

### Privacy Tools
- **Blur** 🔍 - Blur sensitive areas
- **Pixelate** ◼️ - Block out text/faces

### Colors
10 preset colors: Red, Green, Blue, Yellow, Orange, Purple, Black, White, Cyan, Pink

### Size
Adjust stroke width: 1-50 pixels

### Actions
- **Undo/Redo** - Ctrl+Z / Ctrl+Y
- **Save** - Ctrl+S or 💾 button
- **Upload** - ☁️ button (uploads to Imgur)
- **Copy** - Ctrl+C or 📋 button
- **Clear All** - 🗑️ Clear All button

## Common Workflows

### Quick Screenshot
```bash
python3 main.py --fullscreen --no-edit
```
Screenshot auto-saved to ~/Pictures/Screenshots/

### Annotate and Share
1. Capture screenshot (any method)
2. Use Blur tool on sensitive info
3. Add arrows and text to highlight
4. Click Upload ☁️
5. URL auto-copied to clipboard
6. Paste URL anywhere

### Documentation
1. Capture window
2. Add arrows pointing to UI elements
3. Add text labels
4. Save as PNG
5. Insert in docs

## Troubleshooting

### Window capture not working
**X11:** Install xdotool: `sudo apt install xdotool`
**Wayland:** Install gnome-screenshot: `sudo apt install gnome-screenshot`

### Upload fails
Install curl: `sudo apt install curl`

### Blank screenshots on Wayland
Install: `sudo apt install grim gnome-screenshot`

### Hotkeys don't work
Currently GNOME only. Use command line or app launcher on other DEs.

## Settings

Click ⚙️ Settings to configure:
- Save directory
- Default image format
- Auto-save mode
- Clipboard behavior
- Notifications
- Capture delay
- Upload service

## Need Help?

- Read full README.md for details
- Check IMPLEMENTATION_SUMMARY.md for technical info
- Report issues on GitHub
- All features are documented

**Enjoy your new screenshot tool! 📸✨**
