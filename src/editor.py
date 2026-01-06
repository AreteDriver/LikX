"""Enhanced image editor module for LikX with full annotation support."""

from enum import Enum
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass, field
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
    number: int = 0  # For NUMBER tool
    stamp: str = ""  # For STAMP tool


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
        self.stroke_width = 2.0
        self.is_drawing = False
        self.current_element: Optional[DrawingElement] = None
        self.font_size = 16
        self.number_counter = 1  # For NUMBER tool
        self.current_stamp = "✓"  # Default stamp
        # Zoom state
        self.zoom_level = 1.0  # 1.0 = 100%
        self.pan_offset_x = 0.0  # Pan offset in image coordinates
        self.pan_offset_y = 0.0

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
        """Set the current drawing color."""
        self.current_color = color

    def set_stroke_width(self, width: float) -> None:
        """Set the stroke width."""
        self.stroke_width = max(1.0, min(50.0, width))

    def set_font_size(self, size: int) -> None:
        """Set the font size for text tool."""
        self.font_size = max(8, min(72, size))

    def start_drawing(self, x: float, y: float) -> None:
        """Start a new drawing element at the given position."""
        self.is_drawing = True
        self.current_element = DrawingElement(
            tool=self.current_tool,
            color=self.current_color,
            stroke_width=self.stroke_width,
            points=[Point(x, y)],
            font_size=self.font_size,
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


def _render_arrow(ctx: Any, element: DrawingElement) -> None:
    """Render an arrow."""
    if len(element.points) < 2:
        return

    start = element.points[0]
    end = element.points[-1]

    # Draw the line
    ctx.move_to(start.x, start.y)
    ctx.line_to(end.x, end.y)
    ctx.stroke()

    # Draw the arrowhead
    angle = math.atan2(end.y - start.y, end.x - start.x)
    arrow_length = element.stroke_width * 4
    arrow_angle = math.pi / 6

    x1 = end.x - arrow_length * math.cos(angle - arrow_angle)
    y1 = end.y - arrow_length * math.sin(angle - arrow_angle)
    x2 = end.x - arrow_length * math.cos(angle + arrow_angle)
    y2 = end.y - arrow_length * math.sin(angle + arrow_angle)

    ctx.move_to(end.x, end.y)
    ctx.line_to(x1, y1)
    ctx.move_to(end.x, end.y)
    ctx.line_to(x2, y2)
    ctx.stroke()


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
    """Render text."""
    if not element.points or not element.text:
        return

    point = element.points[0]
    ctx.select_font_face("Sans", 0, 1)  # Normal, Bold
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
