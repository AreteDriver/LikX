"""Enhanced image editor module for Linux SnipTool with full annotation support."""

from enum import Enum
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass, field
import math

try:
    import gi
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gdk, GdkPixbuf
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
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create a Color from hex string (e.g., '#FF0000')."""
        hex_color = hex_color.lstrip('#')
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
            font_size=self.font_size
        )
    
    def continue_drawing(self, x: float, y: float) -> None:
        """Continue the current drawing element."""
        if self.is_drawing and self.current_element is not None:
            # For pen and highlighter, add all points
            if self.current_element.tool in [ToolType.PEN, ToolType.HIGHLIGHTER, ToolType.ERASER]:
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
            font_size=self.font_size
        )
        
        self.undo_stack.append(self.elements.copy())
        self.redo_stack.clear()
        self.elements.append(element)
    
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


def apply_blur_region(pixbuf: Any, x: int, y: int, width: int, height: int, radius: int = 10) -> Any:
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
    new_pixels = array.array('B', pixels)
    
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
        rowstride
    )
    
    return new_pixbuf


def apply_pixelate_region(pixbuf: Any, x: int, y: int, width: int, height: int, pixel_size: int = 10) -> Any:
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
    new_pixels = array.array('B', pixels)
    
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
        rowstride
    )
    
    return new_pixbuf


def render_elements(surface_or_ctx: Any, elements: List[DrawingElement], base_pixbuf: Optional[Any] = None) -> None:
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
    except:
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
    except:
        pass
