"""Radial menu for quick tool selection in LikX."""

import math
from typing import Callable, List, Optional, Tuple

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from .editor import ToolType


# Menu item definition: (label, tool_type, icon)
RADIAL_ITEMS: List[Tuple[str, Optional[ToolType], str]] = [
    ("Crop", ToolType.CROP, "✂️"),  # Top (0°)
    ("Draw", ToolType.PEN, "✏️"),  # Top-right (45°)
    ("Arrow", ToolType.ARROW, "➡️"),  # Right (90°)
    ("Shape", ToolType.RECTANGLE, "⬜"),  # Bottom-right (135°)
    ("Eraser", ToolType.ERASER, "🧹"),  # Bottom (180°)
    ("Measure", ToolType.MEASURE, "📏"),  # Bottom-left (225°)
    ("Text", ToolType.TEXT, "📝"),  # Left (270°)
    ("Blur", ToolType.BLUR, "🔍"),  # Top-left (315°)
]


class RadialMenu(Gtk.Window):
    """Floating radial menu for quick tool access."""

    RADIUS = 100  # Outer radius
    INNER_RADIUS = 35  # Inner dead zone
    SEGMENT_COUNT = 8

    def __init__(self, callback: Callable[[Optional[ToolType]], None]):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available")

        super().__init__(type=Gtk.WindowType.POPUP)

        self.callback = callback
        self.highlighted_segment = -1  # -1 = none, 0-7 = segment index
        self.center_x = 0.0
        self.center_y = 0.0
        self.active = False

        self._setup_window()
        self._connect_signals()

    def _setup_window(self):
        """Configure window properties."""
        size = self.RADIUS * 2 + 20
        self.set_default_size(size, size)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)

        # Enable transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        # Drawing area fills the window
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(size, size)
        self.add(self.drawing_area)

        # Enable events on drawing area
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )

    def _connect_signals(self):
        """Connect event handlers."""
        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.connect("motion-notify-event", self._on_motion)
        self.drawing_area.connect("button-release-event", self._on_button_release)
        self.connect("key-press-event", self._on_key_press)

    def show_at(self, x: int, y: int):
        """Show the menu centered at the given screen coordinates."""
        size = self.RADIUS * 2 + 20
        self.center_x = size / 2
        self.center_y = size / 2

        # Position centered on cursor
        self.move(int(x - size / 2), int(y - size / 2))
        self.highlighted_segment = -1
        self.active = True
        self.show_all()

        # Grab pointer to track mouse outside window
        self.grab_add()

    def _on_draw(self, widget, ctx):
        """Draw the radial menu using Cairo."""
        # Clear with transparency
        ctx.set_operator(0)  # CAIRO_OPERATOR_CLEAR
        ctx.paint()
        ctx.set_operator(2)  # CAIRO_OPERATOR_OVER

        cx, cy = self.center_x, self.center_y

        # Draw background circle
        ctx.arc(cx, cy, self.RADIUS, 0, 2 * math.pi)
        ctx.set_source_rgba(0.1, 0.1, 0.1, 0.92)
        ctx.fill()

        # Draw segments
        segment_angle = 2 * math.pi / self.SEGMENT_COUNT
        start_offset = -math.pi / 2 - segment_angle / 2  # Start at top

        for i, (label, tool_type, icon) in enumerate(RADIAL_ITEMS):
            start_angle = start_offset + i * segment_angle
            end_angle = start_angle + segment_angle

            # Draw segment background if highlighted
            if i == self.highlighted_segment:
                ctx.new_path()
                ctx.arc(cx, cy, self.RADIUS - 2, start_angle, end_angle)
                ctx.arc_negative(cx, cy, self.INNER_RADIUS + 2, end_angle, start_angle)
                ctx.close_path()
                ctx.set_source_rgba(0.2, 0.5, 0.8, 0.7)
                ctx.fill()

            # Draw segment border
            ctx.new_path()
            ctx.arc(cx, cy, self.RADIUS - 2, start_angle, end_angle)
            ctx.arc_negative(cx, cy, self.INNER_RADIUS + 2, end_angle, start_angle)
            ctx.close_path()
            ctx.set_source_rgba(0.3, 0.3, 0.3, 1.0)
            ctx.set_line_width(1)
            ctx.stroke()

            # Calculate position for icon/label (middle of segment)
            mid_angle = start_angle + segment_angle / 2
            mid_radius = (self.RADIUS + self.INNER_RADIUS) / 2
            ix = cx + mid_radius * math.cos(mid_angle)
            iy = cy + mid_radius * math.sin(mid_angle)

            # Draw icon
            ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ctx.select_font_face("Sans", 0, 0)
            ctx.set_font_size(18)
            extents = ctx.text_extents(icon)
            ctx.move_to(ix - extents.width / 2, iy + extents.height / 4)
            ctx.show_text(icon)

            # Draw label below icon
            ctx.set_font_size(10)
            label_extents = ctx.text_extents(label)
            label_radius = mid_radius + 18
            lx = cx + label_radius * math.cos(mid_angle)
            ly = cy + label_radius * math.sin(mid_angle)
            ctx.move_to(lx - label_extents.width / 2, ly + label_extents.height / 4)
            ctx.set_source_rgba(0.8, 0.8, 0.8, 1.0)
            ctx.show_text(label)

        # Draw center circle (cancel zone)
        ctx.arc(cx, cy, self.INNER_RADIUS, 0, 2 * math.pi)
        ctx.set_source_rgba(0.15, 0.15, 0.15, 1.0)
        ctx.fill()

        # Draw X in center
        ctx.set_source_rgba(0.5, 0.5, 0.5, 1.0)
        ctx.set_font_size(20)
        ctx.move_to(cx - 7, cy + 7)
        ctx.show_text("×")

        return False

    def _on_motion(self, widget, event):
        """Update highlighted segment based on mouse position."""
        # Calculate angle and distance from center
        dx = event.x - self.center_x
        dy = event.y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < self.INNER_RADIUS:
            # In center dead zone
            new_segment = -1
        elif distance > self.RADIUS:
            # Outside menu
            new_segment = -1
        else:
            # Calculate which segment
            angle = math.atan2(dy, dx)
            # Adjust for our starting offset
            segment_angle = 2 * math.pi / self.SEGMENT_COUNT
            start_offset = -math.pi / 2 - segment_angle / 2

            # Normalize angle
            adjusted = angle - start_offset
            if adjusted < 0:
                adjusted += 2 * math.pi

            new_segment = int(adjusted / segment_angle) % self.SEGMENT_COUNT

        if new_segment != self.highlighted_segment:
            self.highlighted_segment = new_segment
            self.drawing_area.queue_draw()

        return True

    def _on_button_release(self, widget, event):
        """Handle mouse release - select tool or cancel."""
        if not self.active:
            return True

        self.active = False
        self.grab_remove()
        self.hide()

        if self.highlighted_segment >= 0:
            _, tool_type, _ = RADIAL_ITEMS[self.highlighted_segment]
            if self.callback:
                self.callback(tool_type)
        else:
            # Released in center or outside - cancel
            if self.callback:
                self.callback(None)

        return True

    def _on_key_press(self, widget, event):
        """Handle escape to cancel."""
        if event.keyval == Gdk.KEY_Escape:
            self.active = False
            self.grab_remove()
            self.hide()
            if self.callback:
                self.callback(None)
            return True
        return False
