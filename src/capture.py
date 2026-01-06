"""Screenshot capture module for LikX with Wayland and X11 support."""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gdk, GdkPixbuf

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config


class CaptureMode(Enum):
    """Screenshot capture modes."""

    FULLSCREEN = "fullscreen"
    REGION = "region"
    WINDOW = "window"


class DisplayServer(Enum):
    """Display server types."""

    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class CaptureResult:
    """Result of a screenshot capture operation."""

    def __init__(
        self,
        success: bool,
        filepath: Optional[Path] = None,
        error: Optional[str] = None,
        pixbuf: Optional[object] = None,
    ):
        self.success = success
        self.filepath = filepath
        self.error = error
        self.pixbuf = pixbuf

    def __bool__(self) -> bool:
        return self.success


def detect_display_server() -> DisplayServer:
    """Detect the current display server (X11 or Wayland).

    Returns:
        DisplayServer enum indicating the detected server.
    """
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")

    if "wayland" in session_type or wayland_display:
        return DisplayServer.WAYLAND
    elif os.environ.get("DISPLAY"):
        return DisplayServer.X11
    return DisplayServer.UNKNOWN


def capture_fullscreen_wayland(delay: int = 0) -> CaptureResult:
    """Capture fullscreen on Wayland using available tools.

    Args:
        delay: Delay in seconds before capturing.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    temp_file = f"/tmp/likx_{int(time.time())}.png"

    # Try grim (wlroots compositors like Sway)
    try:
        result = subprocess.run(["grim", temp_file], capture_output=True, timeout=5)
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Try gnome-screenshot
    try:
        result = subprocess.run(
            ["gnome-screenshot", "-f", temp_file], capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Try spectacle (KDE)
    try:
        result = subprocess.run(
            ["spectacle", "-b", "-n", "-o", temp_file], capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Cleanup temp file if it exists
    if os.path.exists(temp_file):
        os.unlink(temp_file)

    return CaptureResult(
        False,
        error="No Wayland screenshot tool found. Install grim, gnome-screenshot, or spectacle.",
    )


def capture_fullscreen(delay: int = 0, include_cursor: bool = False) -> CaptureResult:
    """Capture the entire screen.

    Args:
        delay: Delay in seconds before capturing.
        include_cursor: Whether to include the mouse cursor.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    # Check display server
    display_server = detect_display_server()

    if display_server == DisplayServer.WAYLAND:
        return capture_fullscreen_wayland(0)

    if not GTK_AVAILABLE:
        return CaptureResult(False, error="GTK not available")

    try:
        # Get the default screen
        screen = Gdk.Screen.get_default()
        if screen is None:
            return CaptureResult(False, error="Could not get default screen")

        # Get the root window
        root_window = screen.get_root_window()
        if root_window is None:
            return CaptureResult(False, error="Could not get root window")

        # Get screen dimensions
        width = screen.get_width()
        height = screen.get_height()

        # Capture the screenshot
        pixbuf = Gdk.pixbuf_get_from_window(root_window, 0, 0, width, height)

        if pixbuf is None:
            return CaptureResult(False, error="Failed to capture screenshot")

        return CaptureResult(True, pixbuf=pixbuf)

    except Exception as e:
        return CaptureResult(False, error=str(e))


def capture_region_wayland(
    x: int, y: int, width: int, height: int, delay: int = 0
) -> CaptureResult:
    """Capture a region on Wayland.

    Args:
        x: X coordinate of the region.
        y: Y coordinate of the region.
        width: Width of the region.
        height: Height of the region.
        delay: Delay in seconds before capturing.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    temp_file = f"/tmp/likx_{int(time.time())}.png"

    # Try grim with geometry
    try:
        geometry = f"{x},{y} {width}x{height}"
        result = subprocess.run(
            ["grim", "-g", geometry, temp_file], capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Fallback: capture full screen and crop
    full_result = capture_fullscreen_wayland(0)
    if full_result.success and full_result.pixbuf:
        try:
            cropped = GdkPixbuf.Pixbuf.new(
                GdkPixbuf.Colorspace.RGB, True, 8, width, height
            )
            full_result.pixbuf.copy_area(x, y, width, height, cropped, 0, 0)
            return CaptureResult(True, pixbuf=cropped)
        except Exception as e:
            return CaptureResult(False, error=f"Failed to crop: {str(e)}")

    if os.path.exists(temp_file):
        os.unlink(temp_file)

    return CaptureResult(False, error="Region capture failed on Wayland")


def capture_region(
    x: int, y: int, width: int, height: int, delay: int = 0
) -> CaptureResult:
    """Capture a specific region of the screen.

    Args:
        x: X coordinate of the region.
        y: Y coordinate of the region.
        width: Width of the region.
        height: Height of the region.
        delay: Delay in seconds before capturing.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    # Check display server
    display_server = detect_display_server()

    if display_server == DisplayServer.WAYLAND:
        return capture_region_wayland(x, y, width, height, 0)

    if not GTK_AVAILABLE:
        return CaptureResult(False, error="GTK not available")

    try:
        screen = Gdk.Screen.get_default()
        if screen is None:
            return CaptureResult(False, error="Could not get default screen")

        root_window = screen.get_root_window()
        if root_window is None:
            return CaptureResult(False, error="Could not get root window")

        # Ensure coordinates are within screen bounds
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        width = min(width, screen_width - x)
        height = min(height, screen_height - y)

        if width <= 0 or height <= 0:
            return CaptureResult(False, error="Invalid region dimensions")

        pixbuf = Gdk.pixbuf_get_from_window(root_window, x, y, width, height)

        if pixbuf is None:
            return CaptureResult(False, error="Failed to capture region")

        return CaptureResult(True, pixbuf=pixbuf)

    except Exception as e:
        return CaptureResult(False, error=str(e))


def capture_window_wayland(delay: int = 0) -> CaptureResult:
    """Capture active window on Wayland.

    Args:
        delay: Delay in seconds before capturing.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    temp_file = f"/tmp/likx_{int(time.time())}.png"

    # Try gnome-screenshot with window flag
    try:
        result = subprocess.run(
            ["gnome-screenshot", "-w", "-f", temp_file], capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Try spectacle window mode
    try:
        result = subprocess.run(
            ["spectacle", "-a", "-b", "-n", "-o", temp_file],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and os.path.exists(temp_file):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_file)
            os.unlink(temp_file)
            return CaptureResult(True, pixbuf=pixbuf)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    if os.path.exists(temp_file):
        os.unlink(temp_file)

    return CaptureResult(
        False,
        error="Window capture not supported on Wayland without gnome-screenshot or spectacle",
    )


def capture_window(window_id: Optional[int] = None, delay: int = 0) -> CaptureResult:
    """Capture a specific window.

    Args:
        window_id: X11 window ID (if None, captures active window).
        delay: Delay in seconds before capturing.

    Returns:
        CaptureResult with the captured screenshot.
    """
    if delay > 0:
        time.sleep(delay)

    # Check display server
    display_server = detect_display_server()

    if display_server == DisplayServer.WAYLAND:
        return capture_window_wayland(0)

    if not GTK_AVAILABLE:
        return CaptureResult(False, error="GTK not available")

    try:
        # Get active window ID using xdotool if not specified
        if window_id is None:
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0:
                return CaptureResult(
                    False, error="Could not get active window. Is xdotool installed?"
                )
            window_id = result.stdout.strip()

        # Get window geometry using xdotool
        result = subprocess.run(
            ["xdotool", "getwindowgeometry", "--shell", str(window_id)],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode != 0:
            return CaptureResult(False, error="Could not get window geometry")

        # Parse geometry output
        geometry = {}
        for line in result.stdout.split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                try:
                    geometry[key.strip()] = int(value.strip())
                except ValueError:
                    pass

        if "X" not in geometry or "Y" not in geometry:
            return CaptureResult(False, error="Invalid geometry data")

        # Capture the window region
        return capture_region(
            geometry["X"], geometry["Y"], geometry["WIDTH"], geometry["HEIGHT"], delay=0
        )

    except FileNotFoundError:
        return CaptureResult(
            False,
            error="xdotool not installed. Install it with: sudo apt install xdotool",
        )
    except subprocess.TimeoutExpired:
        return CaptureResult(False, error="Window capture timed out")
    except Exception as e:
        return CaptureResult(False, error=f"Window capture failed: {str(e)}")


def save_capture(
    result: CaptureResult,
    filepath: Optional[Path] = None,
    format_str: Optional[str] = None,
) -> CaptureResult:
    """Save a captured screenshot to file.

    Args:
        result: The CaptureResult containing the pixbuf.
        filepath: Path to save the file (auto-generated if None).
        format_str: Image format (uses config default if None).

    Returns:
        CaptureResult with the filepath set.
    """
    if not result.success or result.pixbuf is None:
        return CaptureResult(False, error="No screenshot to save")

    if filepath is None:
        filepath = config.get_save_path(format_str=format_str)
    else:
        filepath = Path(filepath)

    if format_str is None:
        format_str = filepath.suffix.lstrip(".").lower()
        if not format_str:
            format_str = config.get_setting("default_format", "png")

    # Map format strings to GdkPixbuf format names
    format_map = {
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "png": "png",
        "bmp": "bmp",
        "gif": "gif",
    }

    pixbuf_format = format_map.get(format_str.lower(), "png")

    try:
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        result.pixbuf.savev(str(filepath), pixbuf_format, [], [])
        return CaptureResult(True, filepath=filepath, pixbuf=result.pixbuf)

    except Exception as e:
        return CaptureResult(False, error=f"Failed to save: {str(e)}")


def copy_to_clipboard(result: CaptureResult, use_gtk: bool = True) -> bool:
    """Copy a captured screenshot to the clipboard.

    Args:
        result: The CaptureResult containing the pixbuf.
        use_gtk: If True, try GTK clipboard first. Set False for CLI mode.

    Returns:
        True if successful, False otherwise.
    """
    if not result.success or result.pixbuf is None:
        return False

    # Try external clipboard tools first (they persist after exit)
    display_server = detect_display_server()
    temp_file = f"/tmp/likx_clip_{int(time.time())}.png"

    try:
        if result.pixbuf:
            result.pixbuf.savev(temp_file, "png", [], [])

        if display_server == DisplayServer.WAYLAND:
            # wl-copy for Wayland
            with open(temp_file, "rb") as f:
                proc = subprocess.Popen(
                    ["wl-copy", "--type", "image/png"],
                    stdin=f,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                proc.wait(timeout=5)
                if proc.returncode == 0:
                    os.unlink(temp_file)
                    return True
        else:
            # xclip for X11 - use background mode to persist
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard", "-t", "image/png", temp_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Don't wait - xclip forks to background
            time.sleep(0.1)  # Brief wait for xclip to read file
            if proc.poll() is None or proc.returncode == 0:
                # Keep temp file for xclip to serve (it will be cleaned up by /tmp)
                return True

    except FileNotFoundError:
        pass  # External tool not found, fall through to GTK
    except Exception:
        pass

    # Cleanup temp file if external tools failed
    if os.path.exists(temp_file):
        os.unlink(temp_file)

    # Fallback to GTK clipboard (works when running in GUI context)
    if use_gtk and GTK_AVAILABLE:
        try:
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk

            if not Gtk.init_check()[0]:
                Gtk.init([])

            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_image(result.pixbuf)
            clipboard.store()

            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

            return True
        except Exception:
            pass

    return False


def capture(
    mode: CaptureMode,
    delay: int = 0,
    region: Optional[Tuple[int, int, int, int]] = None,
    window_id: Optional[int] = None,
    auto_save: bool = False,
    copy_clipboard: bool = True,
) -> CaptureResult:
    """Main capture function that handles all capture modes.

    Args:
        mode: The capture mode (fullscreen, region, window).
        delay: Delay in seconds before capturing.
        region: Tuple of (x, y, width, height) for region capture.
        window_id: Window ID for window capture.
        auto_save: Whether to automatically save the screenshot.
        copy_clipboard: Whether to copy to clipboard.

    Returns:
        CaptureResult with the captured screenshot.
    """
    cfg = config.load_config()

    # Use config values if not specified
    if delay == 0:
        delay = cfg.get("delay_seconds", 0)

    include_cursor = cfg.get("include_cursor", False)

    # Capture based on mode
    if mode == CaptureMode.FULLSCREEN:
        result = capture_fullscreen(delay=delay, include_cursor=include_cursor)
    elif mode == CaptureMode.REGION:
        if region is None:
            return CaptureResult(False, error="Region not specified")
        x, y, width, height = region
        result = capture_region(x, y, width, height, delay=delay)
    elif mode == CaptureMode.WINDOW:
        result = capture_window(window_id=window_id, delay=delay)
    else:
        return CaptureResult(False, error="Unknown capture mode")

    if not result.success:
        return result

    # Copy to clipboard if requested
    if copy_clipboard or cfg.get("copy_to_clipboard", True):
        copy_to_clipboard(result)

    # Auto-save if requested
    if auto_save or cfg.get("auto_save", False):
        result = save_capture(result)

    return result
