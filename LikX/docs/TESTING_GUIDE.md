# LikX 2.0 - Testing Guide

## ✅ Feature Testing Checklist

### 1. Window Capture (Previously Broken)

**X11 Testing:**
```bash
# Install xdotool if not present
sudo apt install xdotool

# Test window capture
python3 main.py --window
```
**Expected:** Should capture the active window, not fullscreen

**Wayland Testing:**
```bash
# Install gnome-screenshot
sudo apt install gnome-screenshot

# Test window capture
python3 main.py --window
```
**Expected:** Should prompt for window selection and capture it

**Verification:**
- Captured image should be sized to the window, not fullscreen
- Window decorations may or may not be included depending on compositor
- Error message should be helpful if tools not installed

---

### 2. Wayland Support (Previously Missing)

**Test Display Detection:**
```bash
# Check your session type
echo $XDG_SESSION_TYPE

# Or check for Wayland display
echo $WAYLAND_DISPLAY
```

**Test Fullscreen on Wayland:**
```bash
python3 main.py --fullscreen --no-edit
```
**Expected:** Should capture screen using grim or gnome-screenshot

**Test Region on Wayland:**
```bash
python3 main.py --region --no-edit
```
**Expected:** Should show selection overlay and capture selected region

**Verification:**
- Check ~/Pictures/Screenshots/ for saved images
- Images should be properly captured, not blank
- Should work without errors on Wayland

---

### 3. Blur Tool (New Feature)

**Test Blur:**
1. Launch: `python3 main.py --fullscreen`
2. Click "🔍 Blur" tool
3. Draw rectangle over sensitive area
4. Release mouse

**Expected:**
- Area should be blurred immediately
- Blur radius about 10 pixels
- Should work on any part of image

**Verification:**
- Text should be unreadable in blurred area
- Save and check that blur is permanent in saved file

---

### 4. Pixelate Tool (New Feature)

**Test Pixelate:**
1. Launch: `python3 main.py --fullscreen`
2. Click "◼️ Pixelate" tool
3. Draw rectangle over face/text
4. Release mouse

**Expected:**
- Area should be pixelated in blocks
- Block size about 15 pixels
- Should work on any part of image

**Verification:**
- Details should be completely hidden
- Save and check that pixelation is permanent

---

### 5. Cloud Upload (New Feature)

**Test Imgur Upload:**
```bash
# Install curl first
sudo apt install curl

# Capture and upload
python3 main.py --fullscreen
# In editor, click ☁️ Upload button
```

**Expected:**
- Status bar shows "Uploading..."
- After 2-10 seconds, URL appears
- URL automatically copied to clipboard
- Desktop notification shows success
- Can paste URL in browser to verify

**Verification:**
- Open imgur URL in browser
- Image should be viewable
- Image should match what was captured

---

### 6. Global Hotkeys (New Feature - GNOME only)

**Test Hotkey Registration:**
```bash
# First run the app to register hotkeys
python3 main.py
# Close the app

# Check if registered (GNOME)
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```
**Expected:** Should see likx path in output

**Test Hotkeys:**
1. Press `Ctrl+Shift+F` anywhere
2. Should trigger fullscreen capture

3. Press `Ctrl+Shift+R` anywhere
4. Should show region selector

5. Press `Ctrl+Shift+W` anywhere
6. Should capture active window

**Verification:**
- Works from any application
- No need to have SnipTool window open
- Screenshots saved automatically

---

### 7. Full Annotation Save (Previously Broken)

**Test Annotation Persistence:**
1. Capture: `python3 main.py --fullscreen`
2. Draw with Pen (red line)
3. Add Text annotation
4. Draw Arrow
5. Apply Blur to an area
6. Press Ctrl+S
7. Save as test.png

**Verification:**
```bash
# Open saved file
xdg-open ~/Pictures/Screenshots/test.png
```
- ALL annotations should be visible in saved file
- Blur should be permanent
- Text should be readable
- Arrows should have proper heads

---

### 8. Desktop Notifications (New Feature)

**Test Notifications:**
```bash
# Make sure notify-send is installed
which notify-send

# Test save notification
python3 main.py --fullscreen --no-edit
```

**Expected:**
- Notification appears: "Screenshot Saved"
- Shows file path
- Has camera icon

**Test Upload Notification:**
1. Upload screenshot via editor
2. Should see "Upload Successful" notification
3. Shows URL

**Verification:**
- Notifications appear in top-right (GNOME) or appropriate area
- Disappear after ~5 seconds
- Have appropriate icons

---

### 9. Enhanced Editor Tools

**Test Each Tool:**

1. **Pen ✏️:**
   - Draw freehand
   - Should follow mouse smoothly
   - Adjustable width (1-50)

2. **Highlighter 🖍️:**
   - Draw over text
   - Should be semi-transparent
   - 3x width of pen

3. **Line 📏:**
   - Click start, drag, release
   - Should be perfectly straight

4. **Arrow ➡️:**
   - Like line but with arrowhead
   - Arrowhead points in drag direction

5. **Rectangle ⬜:**
   - Click corner, drag, release
   - Should form perfect rectangle

6. **Ellipse ⭕:**
   - Click corner, drag, release
   - Should form ellipse/circle

7. **Text 📝:**
   - Click location
   - Dialog opens for text input
   - Text appears at click location

8. **Eraser 🗑️:**
   - Draw over annotations
   - Should remove with white stroke

**Verification:**
- All tools work smoothly
- No crashes
- Undo/Redo works for all
- Can mix multiple tools

---

### 10. Undo/Redo (Improved)

**Test Undo:**
1. Draw something
2. Press Ctrl+Z
3. Drawing disappears

**Test Redo:**
1. After undo
2. Press Ctrl+Y
3. Drawing reappears

**Test Multiple Undo:**
1. Draw 5 different annotations
2. Press Ctrl+Z five times
3. All should disappear in reverse order

**Verification:**
- Full history preserved
- Can undo/redo any number of times
- No crashes
- Works with all tools

---

## Performance Tests

### Large Image Handling
```bash
# Capture 4K screen if available
python3 main.py --fullscreen
```
**Expected:** Should handle large images smoothly

### Multiple Annotations
1. Add 50+ annotations (lines, arrows, etc.)
2. Editor should remain responsive
3. Saving should work without crashes

### Memory Usage
```bash
# Monitor memory while using
python3 main.py &
PID=$!
watch -n 1 "ps aux | grep $PID | grep -v grep"
```
**Expected:** Reasonable memory usage (<500MB for most cases)

---

## Error Handling Tests

### Missing Dependencies

**Test without xdotool (X11):**
```bash
# Uninstall temporarily
sudo apt remove xdotool

# Try window capture
python3 main.py --window
```
**Expected:** Helpful error message mentioning xdotool

**Test without curl:**
```bash
# Try upload without curl
# Should show error about curl not installed
```

### Invalid Configurations

**Test bad save directory:**
1. Edit ~/.config/likx/config.json
2. Set save_directory to "/root/invalid"
3. Try to capture
**Expected:** Should create directory or show error

---

## Integration Tests

### Complete Workflow 1: Documentation
1. Capture window (Ctrl+Shift+W)
2. Add arrow pointing to button
3. Add text label
4. Blur sensitive info
5. Save
6. Upload
7. Share URL

### Complete Workflow 2: Bug Report
1. Capture region (Ctrl+Shift+R)
2. Highlight error message
3. Add arrow to cause
4. Pixelate user data
5. Save locally
6. Attach to bug report

### Complete Workflow 3: Tutorial
1. Capture fullscreen
2. Add multiple annotations
3. Use different colors
4. Add text steps
5. Save as PNG
6. Use in presentation

---

## Automated Tests

**Quick Test All Features:**
```bash
cd LikX

# Test imports
python3 -c "from src import capture, editor, ui, uploader, hotkeys, notification; print('✅ All imports OK')"

# Test capture modes
python3 main.py --fullscreen --no-edit --delay 0
python3 main.py --window --no-edit --delay 0

# Test config
python3 -c "from src.config import load_config; print('Config:', load_config())"

# Test display detection  
python3 -c "from src.capture import detect_display_server; print('Display:', detect_display_server())"
```

**Expected:** All commands succeed without errors

---

## What to Look For

### ✅ Success Indicators
- No Python exceptions/crashes
- Features work as described
- Saved files contain annotations
- Uploads return valid URLs
- Hotkeys work system-wide
- Notifications appear
- UI is responsive
- Error messages are helpful

### ❌ Failure Indicators
- Python tracebacks
- Blank saved images
- Missing annotations in saved files
- Upload timeouts
- Hotkeys don't register
- UI freezes
- Cryptic error messages

---

## Reporting Issues

If you find problems:

1. Note your system:
   - Linux distribution
   - Display server (X11/Wayland)
   - Desktop environment
   - Python version

2. Exact steps to reproduce

3. Error messages (full traceback)

4. Expected vs actual behavior

5. Screenshots if applicable

---

## Test Results Template

```
LikX 2.0 Test Results
================================

System Information:
- Distro: Ubuntu 24.04
- Display: Wayland
- DE: GNOME 46
- Python: 3.12

Feature Tests:
[ ] Window Capture
[ ] Wayland Support  
[ ] Blur Tool
[ ] Pixelate Tool
[ ] Cloud Upload
[ ] Global Hotkeys
[ ] Annotation Save
[ ] Notifications
[ ] Editor Tools
[ ] Undo/Redo

Notes:
[Your observations here]
```

---

**All features have been implemented and should pass these tests! 🎉**
