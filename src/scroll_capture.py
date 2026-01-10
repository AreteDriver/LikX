"""Scrolling screenshot capture module for LikX."""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

# Lazy-loaded imports for performance (numpy/cv2 add ~70ms startup)
np = None
cv2 = None
OPENCV_AVAILABLE = None


def _ensure_opencv():
    """Lazy-load numpy and opencv when needed."""
    global np, cv2, OPENCV_AVAILABLE
    if OPENCV_AVAILABLE is None:
        try:
            import numpy as _np
            import cv2 as _cv2
            np = _np
            cv2 = _cv2
            OPENCV_AVAILABLE = True
        except ImportError:
            OPENCV_AVAILABLE = False
    return OPENCV_AVAILABLE

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gdk, GdkPixbuf

    import cairo

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config
from .capture import DisplayServer, capture_region, detect_display_server


class ScrollState(Enum):
    """Scroll capture state machine."""

    IDLE = "idle"
    CAPTURING = "capturing"
    STITCHING = "stitching"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ScrollCaptureResult:
    """Result of a scroll capture operation."""

    success: bool
    pixbuf: Optional[object] = None
    filepath: Optional[Path] = None
    error: Optional[str] = None
    frame_count: int = 0
    total_height: int = 0


class ScrollCaptureManager:
    """Manages scrolling screenshot capture with auto-scroll and stitching."""

    def __init__(self):
        self.state = ScrollState.IDLE
        self.frames: List[object] = []  # List of GdkPixbuf
        self.overlaps: List[int] = []  # Overlap pixels for each frame pair
        self.region: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.stop_requested = False
        self._on_progress: Optional[Callable[[int, int], None]] = None
        self._on_complete: Optional[Callable[[ScrollCaptureResult], None]] = None

        # Detect display server
        self.display_server = detect_display_server()

        # Check tool availability based on display server
        self.xdotool_available = self._check_xdotool()
        self.ydotool_available = self._check_ydotool()
        self.wtype_available = self._check_wtype()

    def _check_xdotool(self) -> bool:
        """Check if xdotool is available (X11)."""
        try:
            result = subprocess.run(
                ["xdotool", "--version"], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_ydotool(self) -> bool:
        """Check if ydotool is available (Wayland)."""
        try:
            result = subprocess.run(
                ["ydotool", "--help"], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_wtype(self) -> bool:
        """Check if wtype is available (Wayland/wlroots)."""
        try:
            subprocess.run(["wtype", "--help"], capture_output=True, timeout=2)
            # wtype returns 0 on --help
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> Tuple[bool, Optional[str]]:
        """Check if scroll capture is available on this system."""
        if not GTK_AVAILABLE:
            return False, "GTK not available"

        if not _ensure_opencv():
            return (
                False,
                "OpenCV not installed. "
                "Install with: pip install opencv-python-headless",
            )

        # Check for scroll tool based on display server
        if self.display_server == DisplayServer.X11:
            if not self.xdotool_available:
                return (
                    False,
                    "xdotool not installed. Install with: sudo apt install xdotool",
                )
        elif self.display_server == DisplayServer.WAYLAND:
            if not self.ydotool_available and not self.wtype_available:
                return (
                    False,
                    "No Wayland scroll tool found. Install ydotool or wtype:\n"
                    "  sudo apt install ydotool  # Universal Wayland\n"
                    "  sudo apt install wtype    # wlroots/Sway",
                )
        else:
            # Unknown display server - try X11 tools
            if not self.xdotool_available:
                return (
                    False,
                    "xdotool not installed. Install with: sudo apt install xdotool",
                )

        return True, None

    def start_capture(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[ScrollCaptureResult], None]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Start scroll capture for the specified region.

        Args:
            x, y: Top-left corner coordinates
            width, height: Region dimensions
            on_progress: Callback(frame_count, estimated_height)
            on_complete: Callback(ScrollCaptureResult)

        Returns:
            Tuple of (success, error_message)
        """
        if self.state == ScrollState.CAPTURING:
            return False, "Already capturing"

        available, error = self.is_available()
        if not available:
            return False, error

        if width < 50 or height < 50:
            return False, "Region too small (minimum 50x50 pixels)"

        self.region = (x, y, width, height)
        self.frames = []
        self.overlaps = []
        self.stop_requested = False
        self._on_progress = on_progress
        self._on_complete = on_complete

        self.state = ScrollState.CAPTURING
        return True, None

    def capture_frame(self) -> Tuple[bool, Optional[str]]:
        """Capture a single frame at the current scroll position.

        Returns:
            Tuple of (should_continue, error_message)
        """
        if self.state != ScrollState.CAPTURING:
            return False, "Not in capturing state"

        if self.stop_requested:
            return False, None

        cfg = config.load_config()
        max_frames = cfg.get("scroll_max_frames", 50)

        if len(self.frames) >= max_frames:
            return False, None  # Max frames reached, stop normally

        x, y, width, height = self.region

        # Capture the region
        result = capture_region(region=(x, y, width, height), delay=0)
        if not result.success:
            return False, f"Capture failed: {result.error}"

        pixbuf = result.pixbuf

        if len(self.frames) == 0:
            # First frame - just store it
            self.frames.append(pixbuf)
        else:
            # Find overlap with previous frame
            overlap = self._find_overlap(self.frames[-1], pixbuf)

            if overlap == 0:
                # No overlap found - likely reached end of content
                return False, None

            # Check if we're seeing the same content (no scroll happened)
            if overlap >= height * 0.9:
                return False, None  # Content didn't change, end reached

            self.overlaps.append(overlap)
            self.frames.append(pixbuf)

        # Notify progress
        if self._on_progress:
            estimated_height = self._estimate_total_height()
            self._on_progress(len(self.frames), estimated_height)

        return True, None  # Continue capturing

    def scroll_down(self) -> bool:
        """Scroll down using appropriate tool for the display server.

        Returns:
            True if scroll was successful
        """
        if self.display_server == DisplayServer.X11:
            return self._scroll_x11()
        elif self.display_server == DisplayServer.WAYLAND:
            return self._scroll_wayland()
        else:
            # Unknown - try X11
            return self._scroll_x11()

    def _scroll_x11(self) -> bool:
        """Scroll down using xdotool (X11)."""
        try:
            # Use mouse wheel scroll (button 5 = scroll down)
            # Multiple clicks for more scroll distance
            for _ in range(3):
                subprocess.run(
                    ["xdotool", "click", "5"],
                    capture_output=True,
                    timeout=1,
                )
            return True
        except (subprocess.TimeoutExpired, Exception):
            return False

    def _scroll_wayland(self) -> bool:
        """Scroll down using ydotool or wtype (Wayland)."""
        # Try ydotool first (most universal)
        if self.ydotool_available:
            try:
                # ydotool uses mouse wheel events
                # -120 is one scroll down step (negative = down)
                for _ in range(3):
                    subprocess.run(
                        ["ydotool", "mousemove", "--wheel", "--", "-3"],
                        capture_output=True,
                        timeout=1,
                    )
                return True
            except (subprocess.TimeoutExpired, Exception):
                pass

        # Fall back to wtype (wlroots/Sway) using Page_Down
        if self.wtype_available:
            try:
                subprocess.run(
                    ["wtype", "-k", "Page_Down"],
                    capture_output=True,
                    timeout=1,
                )
                return True
            except (subprocess.TimeoutExpired, Exception):
                pass

        return False

    def stop_capture(self) -> None:
        """Request stop of the capture loop."""
        self.stop_requested = True

    def finish_capture(self) -> ScrollCaptureResult:
        """Finish capture and stitch frames together.

        Returns:
            ScrollCaptureResult with stitched image
        """
        if len(self.frames) == 0:
            self.state = ScrollState.ERROR
            return ScrollCaptureResult(False, error="No frames captured")

        if len(self.frames) == 1:
            # Only one frame, no stitching needed
            self.state = ScrollState.COMPLETED
            return ScrollCaptureResult(
                True,
                pixbuf=self.frames[0],
                frame_count=1,
                total_height=self.frames[0].get_height(),
            )

        self.state = ScrollState.STITCHING

        try:
            stitched = self._stitch_frames()
            self.state = ScrollState.COMPLETED
            return ScrollCaptureResult(
                True,
                pixbuf=stitched,
                frame_count=len(self.frames),
                total_height=stitched.get_height(),
            )
        except Exception as e:
            self.state = ScrollState.ERROR
            return ScrollCaptureResult(False, error=f"Stitching failed: {e}")

    def _find_overlap(self, prev_pixbuf, new_pixbuf) -> int:
        """Find vertical overlap between two frames using template matching.

        Args:
            prev_pixbuf: Previous frame (GdkPixbuf)
            new_pixbuf: New frame (GdkPixbuf)

        Returns:
            Number of overlapping pixels, or 0 if no match found
        """
        if not _ensure_opencv():
            return 0

        cfg = config.load_config()
        search_range = cfg.get("scroll_overlap_search", 150)
        ignore_top = cfg.get("scroll_ignore_top", 0.15)
        ignore_bottom = cfg.get("scroll_ignore_bottom", 0.15)
        confidence_threshold = cfg.get("scroll_confidence", 0.7)

        # Convert pixbufs to numpy arrays
        prev_arr = self._pixbuf_to_numpy(prev_pixbuf)
        new_arr = self._pixbuf_to_numpy(new_pixbuf)

        # Convert to grayscale
        gray1 = cv2.cvtColor(prev_arr, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(new_arr, cv2.COLOR_RGB2GRAY)

        # Apply Sobel edge detection (horizontal edges)
        edges1 = cv2.Sobel(gray1, cv2.CV_64F, 0, 1, ksize=3)
        edges2 = cv2.Sobel(gray2, cv2.CV_64F, 0, 1, ksize=3)

        # Normalize edges for template matching
        edges1 = np.abs(edges1).astype(np.float32)
        edges2 = np.abs(edges2).astype(np.float32)

        h = edges1.shape[0]
        ignore_px_top = int(h * ignore_top)
        ignore_px_bottom = int(h * ignore_bottom)

        # Template from bottom portion of prev_frame (excluding ignored region)
        template_start = max(0, h - search_range - ignore_px_bottom)
        template_end = h - ignore_px_bottom
        if template_end <= template_start:
            return 0

        template = edges1[template_start:template_end, :]

        # Search area in top portion of new_frame
        search_end = min(search_range + ignore_px_top, edges2.shape[0])
        search_area = edges2[ignore_px_top:search_end, :]

        if template.shape[0] == 0 or search_area.shape[0] < template.shape[0]:
            return 0

        # Template matching
        result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence_threshold:
            # Calculate overlap: where in new frame the template was found
            match_y = max_loc[1] + ignore_px_top
            overlap = h - template_start + match_y
            return min(overlap, h)

        return 0

    def _pixbuf_to_numpy(self, pixbuf):
        """Convert GdkPixbuf to numpy array."""
        _ensure_opencv()  # Ensure numpy is loaded
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        rowstride = pixbuf.get_rowstride()
        n_channels = pixbuf.get_n_channels()

        # Get pixel data
        pixels = pixbuf.get_pixels()
        arr = np.frombuffer(pixels, dtype=np.uint8)

        # Reshape accounting for rowstride padding
        if rowstride == width * n_channels:
            arr = arr.reshape((height, width, n_channels))
        else:
            # Handle rowstride padding
            arr = arr.reshape((height, rowstride))
            arr = arr[:, : width * n_channels]
            arr = arr.reshape((height, width, n_channels))

        # Return RGB (drop alpha if present)
        return arr[:, :, :3].copy()

    def _stitch_frames(self) -> object:
        """Stitch all frames together into one tall image.

        Returns:
            Stitched GdkPixbuf
        """
        if len(self.frames) == 0:
            raise ValueError("No frames to stitch")

        if len(self.frames) == 1:
            return self.frames[0]

        # Calculate total height
        width = self.frames[0].get_width()
        total_height = self.frames[0].get_height()
        for i, frame in enumerate(self.frames[1:]):
            overlap = self.overlaps[i] if i < len(self.overlaps) else 0
            total_height += frame.get_height() - overlap

        # Create cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, total_height)
        ctx = cairo.Context(surface)

        # Draw first frame
        Gdk.cairo_set_source_pixbuf(ctx, self.frames[0], 0, 0)
        ctx.paint()

        # Draw subsequent frames with overlap offset
        y_offset = self.frames[0].get_height()
        for i, frame in enumerate(self.frames[1:]):
            overlap = self.overlaps[i] if i < len(self.overlaps) else 0
            y_offset -= overlap
            Gdk.cairo_set_source_pixbuf(ctx, frame, 0, y_offset)
            ctx.paint()
            y_offset += frame.get_height()

        # Convert surface to pixbuf
        return self._surface_to_pixbuf(surface)

    def _surface_to_pixbuf(self, surface: cairo.ImageSurface) -> object:
        """Convert cairo surface to GdkPixbuf."""
        _ensure_opencv()  # Ensure numpy is loaded
        width = surface.get_width()
        height = surface.get_height()

        # Get surface data
        data = bytes(surface.get_data())

        # Cairo uses BGRA, GdkPixbuf uses RGBA - need to swap channels
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4)).copy()
        # Swap B and R channels (BGRA -> RGBA)
        arr[:, :, [0, 2]] = arr[:, :, [2, 0]]

        # Create pixbuf from data
        return GdkPixbuf.Pixbuf.new_from_data(
            arr.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            True,  # has_alpha
            8,  # bits_per_sample
            width,
            height,
            width * 4,  # rowstride
        )

    def _estimate_total_height(self) -> int:
        """Estimate total height based on captured frames."""
        if len(self.frames) == 0:
            return 0

        total = self.frames[0].get_height()
        for i, frame in enumerate(self.frames[1:]):
            overlap = self.overlaps[i] if i < len(self.overlaps) else 0
            total += frame.get_height() - overlap

        return total

    def reset(self) -> None:
        """Reset the capture manager to initial state."""
        self.state = ScrollState.IDLE
        self.frames = []
        self.overlaps = []
        self.stop_requested = False
