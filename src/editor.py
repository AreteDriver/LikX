"""Enhanced image editor module for LikX with full annotation support."""

from enum import Enum
from typing import Optional, List, Tuple, Any, Set
from dataclasses import dataclass, field
import copy
import math

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


class ToolType(Enum):
    """Available editing tools."""

    SELECT = "select"
    PEN = "pen"
    HIGHLIGHTER = "highlighter"
    LINE = "line"
    ARROW = "arrow"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    TEXT = "text"
    BLUR = "blur"
    PIXELATE = "pixelate"
    CROP = "crop"
    ERASER = "eraser"
    MEASURE = "measure"
    NUMBER = "number"
    COLORPICKER = "colorpicker"
    STAMP = "stamp"
    ZOOM = "zoom"
    CALLOUT = "callout"


class ArrowStyle(Enum):
    """Arrow head styles."""

    OPEN = "open"  # Simple open arrowhead (default, current)
    FILLED = "filled"  # Filled/solid arrowhead
    DOUBLE = "double"  # Arrowheads on both ends


@dataclass
class Point:
    """Represents a 2D point."""

    x: float
    y: float


@dataclass
class Color:
    """Represents an RGBA color."""

    r: float = 1.0
    g: float = 0.0
    b: float = 0.0
    a: float = 1.0

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to tuple format."""
        return (self.r, self.g, self.b, self.a)

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        """Create a Color from hex string (e.g., '#FF0000')."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return cls(r, g, b, 1.0)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            a = int(hex_color[6:8], 16) / 255.0
            return cls(r, g, b, a)
        return cls()


# Predefined colors
COLORS = {
    "red": Color(1.0, 0.0, 0.0),
    "green": Color(0.0, 1.0, 0.0),
    "blue": Color(0.0, 0.0, 1.0),
    "yellow": Color(1.0, 1.0, 0.0),
    "orange": Color(1.0, 0.5, 0.0),
    "purple": Color(0.5, 0.0, 0.5),
    "black": Color(0.0, 0.0, 0.0),
    "white": Color(1.0, 1.0, 1.0),
    "cyan": Color(0.0, 1.0, 1.0),
    "pink": Color(1.0, 0.0, 1.0),
}


@dataclass
class DrawingElement:
    """Base class for drawing elements."""

    tool: ToolType
    color: Color = field(default_factory=lambda: Color())
    stroke_width: float = 2.0
    points: List[Point] = field(default_factory=list)
    text: str = ""
    filled: bool = False
    font_size: int = 16
    font_bold: bool = False  # For TEXT tool
    font_italic: bool = False  # For TEXT tool
    font_family: str = "Sans"  # For TEXT tool
    number: int = 0  # For NUMBER tool
    stamp: str = ""  # For STAMP tool
    fill_color: Optional[Color] = None  # For CALLOUT background
    arrow_style: ArrowStyle = ArrowStyle.OPEN  # For ARROW tool


class EditorState:
    """Manages the state of the image editor."""

    def __init__(self, pixbuf: Optional[Any] = None):
        """Initialize the editor state.

        Args:
            pixbuf: Optional GdkPixbuf to edit.
        """
        self.original_pixbuf = pixbuf
        self.current_pixbuf = pixbuf
        self.elements: List[DrawingElement] = []
        self.undo_stack: List[List[DrawingElement]] = []
        self.redo_stack: List[List[DrawingElement]] = []
        self.current_tool = ToolType.PEN
        self.current_color = COLORS["red"]
        self.recent_colors: List[Color] = []  # Last 8 used colors
        self.max_recent_colors = 8
        self.stroke_width = 2.0
        self.is_drawing = False
        self.current_element: Optional[DrawingElement] = None
        self.font_size = 16
        self.font_bold = False  # For TEXT tool
        self.font_italic = False  # For TEXT tool
        self.font_family = "Sans"  # For TEXT tool
        self.number_counter = 1  # For NUMBER tool
        self.current_stamp = "✓"  # Default stamp
        self.arrow_style = ArrowStyle.OPEN  # Default arrow style
        # Zoom state
        self.zoom_level = 1.0  # 1.0 = 100%
        self.pan_offset_x = 0.0  # Pan offset in image coordinates
        self.pan_offset_y = 0.0
        # Selection state (multi-select support)
        self.selected_indices: Set[int] = set()
        self._drag_start: Optional[Point] = None
        self._resize_handle: Optional[str] = None  # 'nw', 'ne', 'sw', 'se', None
        # Clipboard for copy/paste annotations
        self._clipboard: List[DrawingElement] = []
        # Snapping state
        self.snap_enabled = True
        self.snap_threshold = 10.0  # Pixels to trigger snap
        self.active_snap_guides: List[Tuple[str, float]] = []  # ('h', y) or ('v', x)

    def set_pixbuf(self, pixbuf: Any) -> None:
        """Set the pixbuf to edit."""
        self.original_pixbuf = pixbuf
        self.current_pixbuf = pixbuf
        self.elements.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def set_tool(self, tool: ToolType) -> None:
        """Set the current drawing tool."""
        self.current_tool = tool

    def set_color(self, color: Color) -> None:
        """Set the current drawing color and add to recent colors."""
        self.current_color = color
        self._add_recent_color(color)

    def _add_recent_color(self, color: Color) -> None:
        """Add a color to recent colors list (most recent first)."""
        # Check if color already exists (by value comparison)
        for i, c in enumerate(self.recent_colors):
            if (c.r == color.r and c.g == color.g and
                c.b == color.b and c.a == color.a):
                # Move to front
                self.recent_colors.pop(i)
                break

        # Add to front
        self.recent_colors.insert(0, copy.deepcopy(color))

        # Trim to max size
        if len(self.recent_colors) > self.max_recent_colors:
            self.recent_colors = self.recent_colors[:self.max_recent_colors]

    def get_recent_colors(self) -> List[Color]:
        """Get list of recently used colors (most recent first)."""
        return self.recent_colors.copy()

    def set_stroke_width(self, width: float) -> None:
        """Set the stroke width."""
        self.stroke_width = max(1.0, min(50.0, width))

    def set_font_size(self, size: int) -> None:
        """Set the font size for text tool."""
        self.font_size = max(8, min(72, size))

    def set_font_bold(self, bold: bool) -> None:
        """Set bold font style for text tool."""
        self.font_bold = bold

    def set_font_italic(self, italic: bool) -> None:
        """Set italic font style for text tool."""
        self.font_italic = italic

    def set_font_family(self, family: str) -> None:
        """Set font family for text tool."""
        self.font_family = family

    def start_drawing(self, x: float, y: float) -> None:
        """Start a new drawing element at the given position."""
        self.is_drawing = True
        self.current_element = DrawingElement(
            tool=self.current_tool,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(x, y)],
            font_size=self.font_size,
            font_bold=self.font_bold,
            font_italic=self.font_italic,
            font_family=self.font_family,
            arrow_style=self.arrow_style,
        )

    def continue_drawing(self, x: float, y: float) -> None:
        """Continue the current drawing element."""
        if self.is_drawing and self.current_element is not None:
            # For pen and highlighter, add all points
            if self.current_element.tool in [
                ToolType.PEN,
                ToolType.HIGHLIGHTER,
                ToolType.ERASER,
            ]:
                self.current_element.points.append(Point(x, y))
            # For shapes, just update the end point
            elif len(self.current_element.points) == 1:
                self.current_element.points.append(Point(x, y))
            else:
                self.current_element.points[-1] = Point(x, y)

    def finish_drawing(self, x: float, y: float) -> None:
        """Finish the current drawing element."""
        if self.is_drawing and self.current_element is not None:
            if len(self.current_element.points) == 1:
                self.current_element.points.append(Point(x, y))
            else:
                self.current_element.points[-1] = Point(x, y)

            # Save state for undo
            self.undo_stack.append(self.elements.copy())
            self.redo_stack.clear()

            self.elements.append(self.current_element)
            self.current_element = None
            self.is_drawing = False

    def cancel_drawing(self) -> None:
        """Cancel the current drawing operation without saving."""
        self.current_element = None
        self.is_drawing = False

    def add_text(self, x: float, y: float, text: str) -> None:
        """Add a text element at the given position."""
        if not text:
            return

        element = DrawingElement(
            tool=ToolType.TEXT,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(x, y)],
            text=text,
            font_size=self.font_size,
            font_bold=self.font_bold,
            font_italic=self.font_italic,
            font_family=self.font_family,
        )

        self.undo_stack.append(self.elements.copy())
        self.redo_stack.clear()
        self.elements.append(element)

    def add_number(self, x: float, y: float) -> None:
        """Add a numbered marker at the given position."""
        element = DrawingElement(
            tool=ToolType.NUMBER,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(x, y)],
            number=self.number_counter,
            font_size=self.font_size,
        )

        self.undo_stack.append(self.elements.copy())
        self.redo_stack.clear()
        self.elements.append(element)
        self.number_counter += 1

    def reset_number_counter(self) -> None:
        """Reset the number counter to 1."""
        self.number_counter = 1

    def set_stamp(self, stamp: str) -> None:
        """Set the current stamp emoji."""
        self.current_stamp = stamp

    def set_arrow_style(self, style: ArrowStyle) -> None:
        """Set the current arrow style."""
        self.arrow_style = style

    def add_stamp(self, x: float, y: float) -> None:
        """Add a stamp/emoji at the given position."""
        element = DrawingElement(
            tool=ToolType.STAMP,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(x, y)],
            stamp=self.current_stamp,
            font_size=self.font_size,
        )

        self.undo_stack.append(self.elements.copy())
        self.redo_stack.clear()
        self.elements.append(element)

    def add_callout(
        self, tail_x: float, tail_y: float, box_x: float, box_y: float, text: str
    ) -> None:
        """Add a callout/speech bubble annotation.

        Args:
            tail_x, tail_y: Position where the tail points to.
            box_x, box_y: Position of the callout box center.
            text: Text content of the callout.
        """
        if not text:
            return

        element = DrawingElement(
            tool=ToolType.CALLOUT,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(tail_x, tail_y), Point(box_x, box_y)],
            text=text,
            font_size=self.font_size,
            fill_color=Color(1.0, 1.0, 0.9, 0.95),  # Light yellow
        )

        self.undo_stack.append(self.elements.copy())
        self.redo_stack.clear()
        self.elements.append(element)

    def pick_color(self, x: float, y: float) -> Optional[Color]:
        """Pick color from the current pixbuf at given position.

        Returns:
            Color at position, or None if out of bounds.
        """
        if self.current_pixbuf is None:
            return None

        px = int(x)
        py = int(y)
        width = self.current_pixbuf.get_width()
        height = self.current_pixbuf.get_height()

        if px < 0 or px >= width or py < 0 or py >= height:
            return None

        n_channels = self.current_pixbuf.get_n_channels()
        rowstride = self.current_pixbuf.get_rowstride()
        pixels = self.current_pixbuf.get_pixels()

        offset = py * rowstride + px * n_channels
        r = pixels[offset] / 255.0
        g = pixels[offset + 1] / 255.0
        b = pixels[offset + 2] / 255.0

        return Color(r, g, b, 1.0)

    def zoom_in(self, factor: float = 1.25) -> None:
        """Increase zoom level."""
        self.zoom_level = min(8.0, self.zoom_level * factor)

    def zoom_out(self, factor: float = 1.25) -> None:
        """Decrease zoom level."""
        self.zoom_level = max(0.25, self.zoom_level / factor)

    def reset_zoom(self) -> None:
        """Reset zoom to 100% and center pan."""
        self.zoom_level = 1.0
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0

    def pan(self, dx: float, dy: float) -> None:
        """Pan the view by given offset."""
        self.pan_offset_x += dx / self.zoom_level
        self.pan_offset_y += dy / self.zoom_level

    def zoom_at(self, x: float, y: float, factor: float) -> None:
        """Zoom centered on a specific point."""
        old_zoom = self.zoom_level
        if factor > 1:
            self.zoom_in(factor)
        else:
            self.zoom_out(1.0 / factor)

        # Adjust pan to keep the mouse position fixed
        new_zoom = self.zoom_level
        if new_zoom != old_zoom:
            # Calculate how the point position changes
            zoom_ratio = new_zoom / old_zoom
            self.pan_offset_x = x - (x - self.pan_offset_x) * zoom_ratio
            self.pan_offset_y = y - (y - self.pan_offset_y) * zoom_ratio

    # === Selection Methods ===

    @property
    def selected_index(self) -> Optional[int]:
        """Get single selected index (for backwards compatibility)."""
        if len(self.selected_indices) == 1:
            return next(iter(self.selected_indices))
        return None

    @selected_index.setter
    def selected_index(self, value: Optional[int]) -> None:
        """Set single selected index (for backwards compatibility)."""
        self.selected_indices.clear()
        if value is not None:
            self.selected_indices.add(value)

    def select_at(
        self, x: float, y: float, add_to_selection: bool = False, handle_margin: float = 8.0
    ) -> bool:
        """Try to select an element at the given position.

        Args:
            x, y: Click position
            add_to_selection: If True (Shift+click), add to existing selection
            handle_margin: Margin for resize handle hit testing

        Returns True if an element was selected.
        """
        # Check if clicking on a resize handle of already selected element (single selection only)
        if len(self.selected_indices) == 1:
            handle = self._hit_test_handles(x, y, handle_margin)
            if handle:
                self._resize_handle = handle
                self._drag_start = Point(x, y)
                return True

        # Search elements in reverse order (top-most first)
        for i in range(len(self.elements) - 1, -1, -1):
            if self._hit_test_element(self.elements[i], x, y):
                if add_to_selection:
                    # Toggle selection
                    if i in self.selected_indices:
                        self.selected_indices.discard(i)
                    else:
                        self.selected_indices.add(i)
                else:
                    # Replace selection
                    self.selected_indices.clear()
                    self.selected_indices.add(i)
                self._drag_start = Point(x, y)
                self._resize_handle = None
                return True

        # Clicked on empty space - deselect (unless adding to selection)
        if not add_to_selection:
            self.deselect()
        return False

    def _hit_test_element(self, elem: DrawingElement, x: float, y: float) -> bool:
        """Check if point (x, y) hits the element."""
        if not elem.points:
            return False

        bbox = self._get_element_bbox(elem)
        if not bbox:
            return False

        x1, y1, x2, y2 = bbox
        margin = max(5, elem.stroke_width / 2)
        return (x1 - margin <= x <= x2 + margin and
                y1 - margin <= y <= y2 + margin)

    def _get_element_bbox(self, elem: DrawingElement) -> Optional[tuple]:
        """Get bounding box (x1, y1, x2, y2) for an element."""
        if not elem.points:
            return None

        xs = [p.x for p in elem.points]
        ys = [p.y for p in elem.points]

        # For text/stamps, estimate size
        if elem.tool in (ToolType.TEXT, ToolType.STAMP, ToolType.NUMBER):
            # Approximate text size based on font size
            width = elem.font_size * max(len(elem.text), 1) * 0.6
            height = elem.font_size * 1.2
            return (xs[0], ys[0] - height, xs[0] + width, ys[0])

        return (min(xs), min(ys), max(xs), max(ys))

    def _hit_test_handles(self, x: float, y: float, margin: float = 8.0) -> Optional[str]:
        """Check if point hits a resize handle. Returns handle name or None."""
        # Only show resize handles for single selection
        if len(self.selected_indices) != 1:
            return None

        idx = next(iter(self.selected_indices))
        elem = self.elements[idx]
        bbox = self._get_element_bbox(elem)
        if not bbox:
            return None

        x1, y1, x2, y2 = bbox
        handles = {
            'nw': (x1, y1),
            'ne': (x2, y1),
            'sw': (x1, y2),
            'se': (x2, y2),
        }

        for name, (hx, hy) in handles.items():
            if abs(x - hx) <= margin and abs(y - hy) <= margin:
                return name
        return None

    def move_selected(self, x: float, y: float) -> bool:
        """Move selected elements to follow mouse at (x, y).

        Returns True if elements were moved.
        """
        if not self.selected_indices or self._drag_start is None:
            return False

        # Resize only works for single selection
        if self._resize_handle and len(self.selected_indices) == 1:
            return self._resize_selected(x, y)

        # Moving all selected elements
        dx = x - self._drag_start.x
        dy = y - self._drag_start.y

        # Move all selected elements
        for idx in self.selected_indices:
            elem = self.elements[idx]
            for p in elem.points:
                p.x += dx
                p.y += dy

        # Apply snapping (based on first selected element)
        if self.selected_indices:
            first_idx = min(self.selected_indices)
            first_elem = self.elements[first_idx]
            bbox = self._get_element_bbox(first_elem)
            if bbox:
                snap_dx, snap_dy = self._apply_snap(bbox)
                if snap_dx != 0 or snap_dy != 0:
                    # Apply snap offset to all selected elements
                    for idx in self.selected_indices:
                        elem = self.elements[idx]
                        for p in elem.points:
                            p.x += snap_dx
                            p.y += snap_dy

        self._drag_start = Point(x, y)
        return True

    def _resize_selected(self, x: float, y: float) -> bool:
        """Resize the selected element based on drag position."""
        if self.selected_index is None or not self._resize_handle:
            return False

        elem = self.elements[self.selected_index]
        if len(elem.points) < 2:
            return False

        # For shapes with 2 points (start/end), resize by moving the appropriate corner
        handle = self._resize_handle

        # Get current bbox
        xs = [p.x for p in elem.points]
        ys = [p.y for p in elem.points]
        x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)

        # Update corner based on handle
        if 'n' in handle:
            y1 = y
        if 's' in handle:
            y2 = y
        if 'w' in handle:
            x1 = x
        if 'e' in handle:
            x2 = x

        # Ensure minimum size
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            return False

        # Update element points
        if len(elem.points) == 2:
            elem.points[0] = Point(x1, y1)
            elem.points[1] = Point(x2, y2)

        return True

    def finish_move(self) -> None:
        """Finish moving/resizing and save undo state."""
        if self.selected_indices and self._drag_start is not None:
            # Save state for undo (we modified in place, so save current state)
            pass  # Already tracking via elements list
        self._drag_start = None
        self._resize_handle = None
        self.active_snap_guides.clear()  # Clear snap guides

    def delete_selected(self) -> bool:
        """Delete all selected elements.

        Returns True if any elements were deleted.
        """
        if not self.selected_indices:
            return False

        # Save for undo
        self.undo_stack.append([e for e in self.elements])
        self.redo_stack.clear()

        # Remove elements in reverse index order to maintain correct indices
        for idx in sorted(self.selected_indices, reverse=True):
            if 0 <= idx < len(self.elements):
                del self.elements[idx]

        self.selected_indices.clear()
        return True

    def deselect(self) -> None:
        """Clear the current selection."""
        self.selected_indices.clear()
        self._drag_start = None
        self._resize_handle = None

    def get_selected(self) -> Optional[DrawingElement]:
        """Get the first selected element (for single selection compatibility)."""
        if self.selected_indices:
            idx = min(self.selected_indices)
            if 0 <= idx < len(self.elements):
                return self.elements[idx]
        return None

    def get_all_selected(self) -> List[DrawingElement]:
        """Get all selected elements."""
        return [self.elements[idx] for idx in sorted(self.selected_indices)
                if 0 <= idx < len(self.elements)]

    def nudge_selected(self, dx: float, dy: float) -> bool:
        """Move all selected elements by (dx, dy) pixels.

        Args:
            dx: Horizontal offset (positive = right)
            dy: Vertical offset (positive = down)

        Returns:
            True if any elements were moved.
        """
        if not self.selected_indices:
            return False

        # Save for undo
        self.undo_stack.append([e for e in self.elements])
        self.redo_stack.clear()

        # Move all selected elements
        for idx in self.selected_indices:
            if 0 <= idx < len(self.elements):
                elem = self.elements[idx]
                for p in elem.points:
                    p.x += dx
                    p.y += dy

        return True

    def copy_selected(self) -> bool:
        """Copy selected elements to internal clipboard.

        Returns:
            True if any elements were copied.
        """
        if not self.selected_indices:
            return False

        # Deep copy selected elements to clipboard
        self._clipboard = []
        for idx in sorted(self.selected_indices):
            if 0 <= idx < len(self.elements):
                self._clipboard.append(copy.deepcopy(self.elements[idx]))

        return len(self._clipboard) > 0

    def paste_annotations(self, offset: float = 20.0) -> bool:
        """Paste elements from clipboard with offset.

        Args:
            offset: Pixel offset to apply to pasted elements (avoids overlap).

        Returns:
            True if any elements were pasted.
        """
        if not self._clipboard:
            return False

        # Save for undo
        self.undo_stack.append([e for e in self.elements])
        self.redo_stack.clear()

        # Paste copies with offset
        new_indices = []
        for elem in self._clipboard:
            new_elem = copy.deepcopy(elem)
            # Apply offset to all points
            for p in new_elem.points:
                p.x += offset
                p.y += offset
            self.elements.append(new_elem)
            new_indices.append(len(self.elements) - 1)

        # Select the newly pasted elements
        self.selected_indices = set(new_indices)

        return True

    def has_clipboard(self) -> bool:
        """Check if clipboard has content."""
        return len(self._clipboard) > 0

    def bring_to_front(self) -> bool:
        """Move selected elements to front (top of stack).

        Returns:
            True if any elements were moved.
        """
        if not self.selected_indices:
            return False

        # Save for undo
        self.undo_stack.append([e for e in self.elements])
        self.redo_stack.clear()

        # Extract selected elements (in order)
        selected = []
        remaining = []
        for i, elem in enumerate(self.elements):
            if i in self.selected_indices:
                selected.append(elem)
            else:
                remaining.append(elem)

        # Rebuild: remaining first, then selected (on top)
        self.elements = remaining + selected

        # Update selection indices to new positions
        new_start = len(remaining)
        self.selected_indices = set(range(new_start, new_start + len(selected)))

        return True

    def send_to_back(self) -> bool:
        """Move selected elements to back (bottom of stack).

        Returns:
            True if any elements were moved.
        """
        if not self.selected_indices:
            return False

        # Save for undo
        self.undo_stack.append([e for e in self.elements])
        self.redo_stack.clear()

        # Extract selected elements (in order)
        selected = []
        remaining = []
        for i, elem in enumerate(self.elements):
            if i in self.selected_indices:
                selected.append(elem)
            else:
                remaining.append(elem)

        # Rebuild: selected first (at back), then remaining
        self.elements = selected + remaining

        # Update selection indices to new positions (starting from 0)
        self.selected_indices = set(range(len(selected)))

        return True

    def set_snap_enabled(self, enabled: bool) -> None:
        """Enable or disable snapping."""
        self.snap_enabled = enabled

    def _get_snap_lines(self) -> Tuple[List[float], List[float]]:
        """Get all horizontal and vertical snap lines from other elements.

        Returns:
            Tuple of (horizontal_lines, vertical_lines) where each is a list of y/x coordinates.
        """
        h_lines: List[float] = []
        v_lines: List[float] = []

        for i, elem in enumerate(self.elements):
            if i in self.selected_indices:
                continue  # Skip selected elements
            bbox = self._get_element_bbox(elem)
            if bbox:
                x1, y1, x2, y2 = bbox
                # Add edges
                h_lines.extend([y1, y2])  # Top and bottom
                v_lines.extend([x1, x2])  # Left and right
                # Add center
                h_lines.append((y1 + y2) / 2)
                v_lines.append((x1 + x2) / 2)

        return h_lines, v_lines

    def _apply_snap(self, elem_bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Calculate snap offset for the element.

        Args:
            elem_bbox: Bounding box of element being moved (x1, y1, x2, y2).

        Returns:
            Tuple of (dx, dy) offset to apply for snapping.
        """
        self.active_snap_guides.clear()

        if not self.snap_enabled:
            return 0.0, 0.0

        x1, y1, x2, y2 = elem_bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        h_lines, v_lines = self._get_snap_lines()

        snap_dx = 0.0
        snap_dy = 0.0

        # Check horizontal snapping (y values)
        elem_y_points = [y1, cy, y2]  # Top, center, bottom
        for elem_y in elem_y_points:
            for snap_y in h_lines:
                if abs(elem_y - snap_y) < self.snap_threshold:
                    snap_dy = snap_y - elem_y
                    self.active_snap_guides.append(('h', snap_y))
                    break
            if snap_dy != 0:
                break

        # Check vertical snapping (x values)
        elem_x_points = [x1, cx, x2]  # Left, center, right
        for elem_x in elem_x_points:
            for snap_x in v_lines:
                if abs(elem_x - snap_x) < self.snap_threshold:
                    snap_dx = snap_x - elem_x
                    self.active_snap_guides.append(('v', snap_x))
                    break
            if snap_dx != 0:
                break

        return snap_dx, snap_dy

    def undo(self) -> bool:
        """Undo the last drawing action.

        Returns:
            True if undo was successful, False if nothing to undo.
        """
        if not self.undo_stack:
            return False

        self.redo_stack.append(self.elements.copy())
        self.elements = self.undo_stack.pop()
        return True

    def redo(self) -> bool:
        """Redo the last undone action.

        Returns:
            True if redo was successful, False if nothing to redo.
        """
        if not self.redo_stack:
            return False

        self.undo_stack.append(self.elements.copy())
        self.elements = self.redo_stack.pop()
        return True

    def clear(self) -> None:
        """Clear all drawing elements."""
        if self.elements:
            self.undo_stack.append(self.elements.copy())
            self.redo_stack.clear()
        self.elements.clear()

    def get_elements(self) -> List[DrawingElement]:
        """Get all drawing elements including the current one."""
        elements = self.elements.copy()
        if self.current_element is not None:
            elements.append(self.current_element)
        return elements

    def has_changes(self) -> bool:
        """Check if there are any drawing elements."""
        return len(self.elements) > 0 or self.current_element is not None


def apply_blur_region(
    pixbuf: Any, x: int, y: int, width: int, height: int, radius: int = 10
) -> Any:
    """Apply blur effect to a region of the pixbuf.

    Args:
        pixbuf: Source GdkPixbuf.
        x, y: Top-left corner of region.
        width, height: Size of region.
        radius: Blur radius.

    Returns:
        Modified pixbuf with blur applied.
    """
    # Simple box blur implementation
    # Extract region
    has_alpha = pixbuf.get_has_alpha()
    n_channels = pixbuf.get_n_channels()
    rowstride = pixbuf.get_rowstride()
    pixels = pixbuf.get_pixels()

    img_width = pixbuf.get_width()
    img_height = pixbuf.get_height()

    # Clamp region to image bounds
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(img_width, x + width)
    y2 = min(img_height, y + height)

    # Create a copy of the pixels array for the region
    import array

    new_pixels = array.array("B", pixels)

    # Apply box blur
    for py in range(y1, y2):
        for px in range(x1, x2):
            r_sum, g_sum, b_sum, count = 0, 0, 0, 0

            # Average pixels in radius
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    sample_x = max(0, min(img_width - 1, px + dx))
                    sample_y = max(0, min(img_height - 1, py + dy))

                    offset = sample_y * rowstride + sample_x * n_channels
                    r_sum += pixels[offset]
                    g_sum += pixels[offset + 1]
                    b_sum += pixels[offset + 2]
                    count += 1

            # Write averaged color
            offset = py * rowstride + px * n_channels
            new_pixels[offset] = r_sum // count
            new_pixels[offset + 1] = g_sum // count
            new_pixels[offset + 2] = b_sum // count

    # Create new pixbuf with blurred pixels
    new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
        new_pixels.tobytes(),
        pixbuf.get_colorspace(),
        has_alpha,
        pixbuf.get_bits_per_sample(),
        img_width,
        img_height,
        rowstride,
    )

    return new_pixbuf


def apply_pixelate_region(
    pixbuf: Any, x: int, y: int, width: int, height: int, pixel_size: int = 10
) -> Any:
    """Apply pixelate effect to a region of the pixbuf.

    Args:
        pixbuf: Source GdkPixbuf.
        x, y: Top-left corner of region.
        width, height: Size of region.
        pixel_size: Size of pixelation blocks.

    Returns:
        Modified pixbuf with pixelation applied.
    """
    has_alpha = pixbuf.get_has_alpha()
    n_channels = pixbuf.get_n_channels()
    rowstride = pixbuf.get_rowstride()
    pixels = pixbuf.get_pixels()

    img_width = pixbuf.get_width()
    img_height = pixbuf.get_height()

    # Clamp region to image bounds
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(img_width, x + width)
    y2 = min(img_height, y + height)

    import array

    new_pixels = array.array("B", pixels)

    # Process in blocks
    for block_y in range(y1, y2, pixel_size):
        for block_x in range(x1, x2, pixel_size):
            # Calculate average color for this block
            r_sum, g_sum, b_sum, count = 0, 0, 0, 0

            for py in range(block_y, min(block_y + pixel_size, y2)):
                for px in range(block_x, min(block_x + pixel_size, x2)):
                    offset = py * rowstride + px * n_channels
                    r_sum += pixels[offset]
                    g_sum += pixels[offset + 1]
                    b_sum += pixels[offset + 2]
                    count += 1

            if count > 0:
                avg_r = r_sum // count
                avg_g = g_sum // count
                avg_b = b_sum // count

                # Fill the block with average color
                for py in range(block_y, min(block_y + pixel_size, y2)):
                    for px in range(block_x, min(block_x + pixel_size, x2)):
                        offset = py * rowstride + px * n_channels
                        new_pixels[offset] = avg_r
                        new_pixels[offset + 1] = avg_g
                        new_pixels[offset + 2] = avg_b

    # Create new pixbuf
    new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
        new_pixels.tobytes(),
        pixbuf.get_colorspace(),
        has_alpha,
        pixbuf.get_bits_per_sample(),
        img_width,
        img_height,
        rowstride,
    )

    return new_pixbuf


def render_elements(
    surface_or_ctx: Any,
    elements: List[DrawingElement],
    base_pixbuf: Optional[Any] = None,
) -> None:
    """Render drawing elements to a Cairo surface or context.

    Args:
        surface_or_ctx: Cairo surface or context to render to.
        elements: List of DrawingElement objects to render.
        base_pixbuf: Optional base pixbuf for blur/pixelate operations.
    """
    try:
        import cairo
    except ImportError:
        return

    # Accept either a surface or an existing context
    if isinstance(surface_or_ctx, cairo.Context):
        ctx = surface_or_ctx
    else:
        ctx = cairo.Context(surface_or_ctx)

    for element in elements:
        if not element.points:
            continue

        r, g, b, a = element.color.to_tuple()
        ctx.set_source_rgba(r, g, b, a)
        ctx.set_line_width(element.stroke_width)

        if element.tool == ToolType.PEN:
            _render_freehand(ctx, element)
        elif element.tool == ToolType.HIGHLIGHTER:
            ctx.set_source_rgba(r, g, b, 0.3)
            ctx.set_line_width(element.stroke_width * 3)
            _render_freehand(ctx, element)
        elif element.tool == ToolType.LINE:
            _render_line(ctx, element)
        elif element.tool == ToolType.ARROW:
            _render_arrow(ctx, element)
        elif element.tool == ToolType.RECTANGLE:
            _render_rectangle(ctx, element)
        elif element.tool == ToolType.ELLIPSE:
            _render_ellipse(ctx, element)
        elif element.tool == ToolType.TEXT:
            _render_text(ctx, element)
        elif element.tool == ToolType.ERASER:
            _render_eraser(ctx, element)
        elif element.tool == ToolType.BLUR and base_pixbuf:
            _render_blur(ctx, element, base_pixbuf)
        elif element.tool == ToolType.PIXELATE and base_pixbuf:
            _render_pixelate(ctx, element, base_pixbuf)
        elif element.tool == ToolType.MEASURE:
            _render_measure(ctx, element)
        elif element.tool == ToolType.NUMBER:
            _render_number(ctx, element)
        elif element.tool == ToolType.STAMP:
            _render_stamp(ctx, element)
        elif element.tool == ToolType.CALLOUT:
            _render_callout(ctx, element)


def _render_freehand(ctx: Any, element: DrawingElement) -> None:
    """Render a freehand drawing."""
    if len(element.points) < 2:
        return

    ctx.set_line_cap(1)  # Round caps
    ctx.set_line_join(1)  # Round joins

    ctx.move_to(element.points[0].x, element.points[0].y)
    for point in element.points[1:]:
        ctx.line_to(point.x, point.y)
    ctx.stroke()


def _render_line(ctx: Any, element: DrawingElement) -> None:
    """Render a straight line."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]
    ctx.move_to(start.x, start.y)
    ctx.line_to(end.x, end.y)
    ctx.stroke()


def _draw_arrowhead(
    ctx: Any, tip_x: float, tip_y: float, angle: float, length: float, style: ArrowStyle
) -> None:
    """Draw a single arrowhead at the specified position and angle.

    Args:
        ctx: Cairo context
        tip_x, tip_y: Position of the arrow tip
        angle: Direction the arrow points (radians)
        length: Length of the arrowhead
        style: ArrowStyle (OPEN or FILLED)
    """
    arrow_angle = math.pi / 6  # 30 degrees

    x1 = tip_x - length * math.cos(angle - arrow_angle)
    y1 = tip_y - length * math.sin(angle - arrow_angle)
    x2 = tip_x - length * math.cos(angle + arrow_angle)
    y2 = tip_y - length * math.sin(angle + arrow_angle)

    if style == ArrowStyle.FILLED:
        # Filled triangle arrowhead
        ctx.move_to(tip_x, tip_y)
        ctx.line_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.close_path()
        ctx.fill()
    else:
        # Open arrowhead (two lines forming V)
        ctx.move_to(tip_x, tip_y)
        ctx.line_to(x1, y1)
        ctx.move_to(tip_x, tip_y)
        ctx.line_to(x2, y2)
        ctx.stroke()


def _render_arrow(ctx: Any, element: DrawingElement) -> None:
    """Render an arrow with configurable head style."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]
    style = element.arrow_style

    # Draw the line
    ctx.move_to(start.x, start.y)
    ctx.line_to(end.x, end.y)
    ctx.stroke()

    # Calculate arrow parameters
    angle = math.atan2(end.y - start.y, end.x - start.x)
    arrow_length = element.stroke_width * 4

    # Draw arrowhead at end
    _draw_arrowhead(ctx, end.x, end.y, angle, arrow_length, style)

    # For DOUBLE style, also draw arrowhead at start (pointing backward)
    if style == ArrowStyle.DOUBLE:
        reverse_angle = angle + math.pi  # Point in opposite direction
        _draw_arrowhead(ctx, start.x, start.y, reverse_angle, arrow_length, ArrowStyle.OPEN)


def _render_rectangle(ctx: Any, element: DrawingElement) -> None:
    """Render a rectangle."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    x = min(start.x, end.x)
    y = min(start.y, end.y)
    width = abs(end.x - start.x)
    height = abs(end.y - start.y)

    ctx.rectangle(x, y, width, height)
    if element.filled:
        ctx.fill()
    else:
        ctx.stroke()


def _render_ellipse(ctx: Any, element: DrawingElement) -> None:
    """Render an ellipse."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    cx = (start.x + end.x) / 2
    cy = (start.y + end.y) / 2
    rx = abs(end.x - start.x) / 2
    ry = abs(end.y - start.y) / 2

    if rx > 0 and ry > 0:
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        if element.filled:
            ctx.fill()
        else:
            ctx.stroke()


def _render_text(ctx: Any, element: DrawingElement) -> None:
    """Render text with optional bold/italic styles."""
    if not element.points or not element.text:
        return

    point = element.points[0]
    # Cairo font slant: 0=normal, 1=italic, 2=oblique
    # Cairo font weight: 0=normal, 1=bold
    slant = 1 if element.font_italic else 0
    weight = 1 if element.font_bold else 0
    ctx.select_font_face(element.font_family, slant, weight)
    ctx.set_font_size(element.font_size)
    ctx.move_to(point.x, point.y)
    ctx.show_text(element.text)


def _render_eraser(ctx: Any, element: DrawingElement) -> None:
    """Render eraser (white thick line)."""
    if len(element.points) < 2:
        return

    ctx.set_source_rgba(1, 1, 1, 1)  # White
    ctx.set_line_width(element.stroke_width * 3)
    ctx.set_line_cap(1)  # Round

    ctx.move_to(element.points[0].x, element.points[0].y)
    for point in element.points[1:]:
        ctx.line_to(point.x, point.y)
    ctx.stroke()


def _render_blur(ctx: Any, element: DrawingElement, base_pixbuf: Any) -> None:
    """Render blur effect."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    x = int(min(start.x, end.x))
    y = int(min(start.y, end.y))
    width = int(abs(end.x - start.x))
    height = int(abs(end.y - start.y))

    # Apply blur to base pixbuf region
    blurred = apply_blur_region(base_pixbuf, x, y, width, height, radius=10)

    # Draw blurred region
    try:
        from gi.repository import Gdk

        Gdk.cairo_set_source_pixbuf(ctx, blurred, 0, 0)
        ctx.rectangle(x, y, width, height)
        ctx.fill()
    except Exception:
        pass


def _render_pixelate(ctx: Any, element: DrawingElement, base_pixbuf: Any) -> None:
    """Render pixelate effect."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    x = int(min(start.x, end.x))
    y = int(min(start.y, end.y))
    width = int(abs(end.x - start.x))
    height = int(abs(end.y - start.y))

    # Apply pixelation to base pixbuf region
    pixelated = apply_pixelate_region(base_pixbuf, x, y, width, height, pixel_size=15)

    # Draw pixelated region
    try:
        from gi.repository import Gdk

        Gdk.cairo_set_source_pixbuf(ctx, pixelated, 0, 0)
        ctx.rectangle(x, y, width, height)
        ctx.fill()
    except Exception:
        pass


def _render_measure(ctx: Any, element: DrawingElement) -> None:
    """Render a measurement line with pixel distance and dimensions."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    # Calculate measurements
    dx = end.x - start.x
    dy = end.y - start.y
    distance = math.sqrt(dx * dx + dy * dy)
    width = abs(dx)
    height = abs(dy)

    # Line angle for perpendicular end markers
    line_angle = math.atan2(dy, dx)
    perp_angle = line_angle + math.pi / 2
    marker_size = 6

    # Draw the main measurement line
    r, g, b, a = element.color.to_tuple()
    ctx.set_source_rgba(r, g, b, a)
    ctx.set_line_width(element.stroke_width)
    ctx.move_to(start.x, start.y)
    ctx.line_to(end.x, end.y)
    ctx.stroke()

    # Draw perpendicular end markers
    for point in [start, end]:
        px1 = point.x + marker_size * math.cos(perp_angle)
        py1 = point.y + marker_size * math.sin(perp_angle)
        px2 = point.x - marker_size * math.cos(perp_angle)
        py2 = point.y - marker_size * math.sin(perp_angle)
        ctx.move_to(px1, py1)
        ctx.line_to(px2, py2)
        ctx.stroke()

    # Prepare text label
    ctx.select_font_face("Sans", 0, 1)  # Normal, Bold
    font_size = max(12, min(16, element.stroke_width * 4))
    ctx.set_font_size(font_size)

    # Build label text
    label = f"{distance:.0f}px"
    if width > 10 and height > 10:
        label += f" ({width:.0f}×{height:.0f})"

    # Get text extents for background
    extents = ctx.text_extents(label)
    text_width = extents.width
    text_height = extents.height

    # Position label at midpoint of line
    mid_x = (start.x + end.x) / 2
    mid_y = (start.y + end.y) / 2

    # Offset text perpendicular to line to avoid overlap
    offset = 12
    text_x = mid_x + offset * math.cos(perp_angle) - text_width / 2
    text_y = mid_y + offset * math.sin(perp_angle) + text_height / 2

    # Draw semi-transparent background behind text
    padding = 4
    ctx.set_source_rgba(0, 0, 0, 0.7)
    ctx.rectangle(
        text_x - padding,
        text_y - text_height - padding,
        text_width + padding * 2,
        text_height + padding * 2,
    )
    ctx.fill()

    # Draw the text
    ctx.set_source_rgba(1, 1, 1, 1)  # White text
    ctx.move_to(text_x, text_y)
    ctx.show_text(label)


def _render_number(ctx: Any, element: DrawingElement) -> None:
    """Render a numbered circle marker."""
    if not element.points:
        return

    point = element.points[0]
    r, g, b, a = element.color.to_tuple()

    # Circle radius based on number of digits
    num_str = str(element.number)
    radius = max(14, 10 + len(num_str) * 4)

    # Draw filled circle background
    ctx.arc(point.x, point.y, radius, 0, 2 * math.pi)
    ctx.set_source_rgba(r, g, b, a)
    ctx.fill_preserve()

    # Draw circle border (slightly darker)
    ctx.set_source_rgba(r * 0.7, g * 0.7, b * 0.7, a)
    ctx.set_line_width(2)
    ctx.stroke()

    # Draw the number text (white)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.select_font_face("Sans", 0, 1)  # Normal, Bold
    font_size = max(12, radius - 2)
    ctx.set_font_size(font_size)

    # Center the text
    extents = ctx.text_extents(num_str)
    text_x = point.x - extents.width / 2 - extents.x_bearing
    text_y = point.y - extents.height / 2 - extents.y_bearing

    ctx.move_to(text_x, text_y)
    ctx.show_text(num_str)


def _render_stamp(ctx: Any, element: DrawingElement) -> None:
    """Render a stamp/emoji."""
    if not element.points or not element.stamp:
        return

    point = element.points[0]

    # Use larger font size for stamps
    font_size = max(24, element.font_size * 2)
    ctx.select_font_face("Sans", 0, 0)  # Normal weight
    ctx.set_font_size(font_size)

    # Get text extents to center the stamp
    extents = ctx.text_extents(element.stamp)
    text_x = point.x - extents.width / 2 - extents.x_bearing
    text_y = point.y - extents.height / 2 - extents.y_bearing

    # Draw the stamp
    ctx.move_to(text_x, text_y)
    ctx.show_text(element.stamp)


def _render_callout(ctx: Any, element: DrawingElement) -> None:
    """Render a callout/speech bubble with tail pointer."""
    if len(element.points) < 2 or not element.text:
        return

    tail_tip = element.points[0]  # Where the pointer points
    box_pos = element.points[1]  # Box position

    # Calculate text dimensions
    ctx.select_font_face("Sans", 0, 0)
    ctx.set_font_size(element.font_size)

    # Split text into lines and calculate box size
    lines = element.text.split("\n")
    line_height = element.font_size * 1.3
    max_width = 0
    for line in lines:
        extents = ctx.text_extents(line)
        max_width = max(max_width, extents.width)

    padding = 10
    box_width = max_width + padding * 2
    box_height = len(lines) * line_height + padding * 2
    corner_radius = 8

    # Box position (centered on box_pos)
    box_x = box_pos.x - box_width / 2
    box_y = box_pos.y - box_height / 2

    # Draw rounded rectangle with tail
    ctx.new_path()

    # Determine which side the tail should come from
    dx = tail_tip.x - box_pos.x
    dy = tail_tip.y - box_pos.y

    # Draw rounded rectangle
    # Top-left corner
    ctx.move_to(box_x + corner_radius, box_y)

    # Top edge
    ctx.line_to(box_x + box_width - corner_radius, box_y)
    ctx.arc(
        box_x + box_width - corner_radius,
        box_y + corner_radius,
        corner_radius,
        -math.pi / 2,
        0,
    )

    # Right edge
    ctx.line_to(box_x + box_width, box_y + box_height - corner_radius)
    ctx.arc(
        box_x + box_width - corner_radius,
        box_y + box_height - corner_radius,
        corner_radius,
        0,
        math.pi / 2,
    )

    # Bottom edge
    ctx.line_to(box_x + corner_radius, box_y + box_height)
    ctx.arc(
        box_x + corner_radius,
        box_y + box_height - corner_radius,
        corner_radius,
        math.pi / 2,
        math.pi,
    )

    # Left edge
    ctx.line_to(box_x, box_y + corner_radius)
    ctx.arc(box_x + corner_radius, box_y + corner_radius, corner_radius, math.pi, 3 * math.pi / 2)

    ctx.close_path()

    # Fill background
    fill = element.fill_color or Color(1.0, 1.0, 0.9, 0.95)  # Light yellow default
    ctx.set_source_rgba(*fill.to_tuple())
    ctx.fill_preserve()

    # Draw border
    ctx.set_source_rgba(*element.color.to_tuple())
    ctx.set_line_width(element.stroke_width)
    ctx.stroke()

    # Draw tail (triangle pointer)
    ctx.new_path()
    # Find edge point closest to tail
    edge_x = max(box_x + 15, min(box_x + box_width - 15, tail_tip.x))
    if abs(dy) > abs(dx):  # Tail is more vertical
        if tail_tip.y > box_y + box_height:  # Tail below box
            edge_y = box_y + box_height
        else:  # Tail above box
            edge_y = box_y
    else:  # Tail is more horizontal
        edge_y = max(box_y + 15, min(box_y + box_height - 15, tail_tip.y))
        if tail_tip.x > box_x + box_width:  # Tail right of box
            edge_x = box_x + box_width
        else:  # Tail left of box
            edge_x = box_x

    # Draw tail triangle
    tail_width = 12
    ctx.move_to(tail_tip.x, tail_tip.y)
    if abs(dy) > abs(dx):  # Vertical tail
        ctx.line_to(edge_x - tail_width / 2, edge_y)
        ctx.line_to(edge_x + tail_width / 2, edge_y)
    else:  # Horizontal tail
        ctx.line_to(edge_x, edge_y - tail_width / 2)
        ctx.line_to(edge_x, edge_y + tail_width / 2)
    ctx.close_path()

    ctx.set_source_rgba(*fill.to_tuple())
    ctx.fill_preserve()
    ctx.set_source_rgba(*element.color.to_tuple())
    ctx.stroke()

    # Draw text
    ctx.set_source_rgba(*element.color.to_tuple())
    text_x = box_x + padding
    text_y = box_y + padding + element.font_size

    for line in lines:
        ctx.move_to(text_x, text_y)
        ctx.show_text(line)
        text_y += line_height
