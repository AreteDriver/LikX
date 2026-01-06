"""Enhanced user interface module for LikX with full features."""

import sys
from typing import Optional, Callable
from pathlib import Path

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config
from .capture import CaptureMode, CaptureResult, capture, save_capture
from .editor import EditorState, ToolType, Color, ArrowStyle, render_elements
from .notification import (
    show_notification,
    show_screenshot_saved,
    show_screenshot_copied,
    show_upload_success,
    show_upload_error,
)
from .uploader import Uploader
from .hotkeys import HotkeyManager
from .ocr import OCREngine
from .pinned import PinnedWindow
from .history import HistoryManager
from .effects import (
    add_shadow,
    add_border,
    add_background,
    round_corners,
    adjust_brightness_contrast,
    invert_colors,
    grayscale,
)


class RegionSelector:
    """Overlay window for selecting a screen region."""

    def __init__(self, callback: Callable[[int, int, int, int], None]):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK is not available")

        self.callback = callback
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.is_selecting = False
        self.scale_factor = 1  # Will be set after window is realized

        self.window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.window.set_app_paintable(True)
        self.window.set_decorated(False)

        screen = Gdk.Screen.get_default()
        self.window.set_default_size(screen.get_width(), screen.get_height())
        self.window.move(0, 0)

        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        self.drawing_area = Gtk.DrawingArea()
        self.window.add(self.drawing_area)

        self.window.connect("key-press-event", self._on_key_press)
        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.connect("button-press-event", self._on_button_press)
        self.drawing_area.connect("button-release-event", self._on_button_release)
        self.drawing_area.connect("motion-notify-event", self._on_motion)
        self.drawing_area.connect("scroll-event", self._on_scroll)

        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        self.window.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        self.window.show_all()

        # Create custom crosshair cursor with centered hotspot
        display = Gdk.Display.get_default()
        cursor = self._create_crosshair_cursor(display)
        self.window.get_window().set_cursor(cursor)

        # Get scale factor for HiDPI displays
        self.scale_factor = self.window.get_scale_factor()

    def _create_crosshair_cursor(self, display: Gdk.Display) -> Gdk.Cursor:
        """Create a crosshair cursor with hotspot at exact center."""
        try:
            import cairo
        except ImportError:
            # Fall back to system crosshair if cairo unavailable
            return Gdk.Cursor.new_from_name(display, "crosshair")

        size = 32
        center = size // 2

        # Create crosshair using cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        cr = cairo.Context(surface)

        # Draw black outline for visibility
        cr.set_source_rgba(0, 0, 0, 1)
        cr.set_line_width(3)
        cr.move_to(center, 2)
        cr.line_to(center, size - 2)
        cr.stroke()
        cr.move_to(2, center)
        cr.line_to(size - 2, center)
        cr.stroke()

        # Draw white center lines
        cr.set_source_rgba(1, 1, 1, 1)
        cr.set_line_width(1)
        cr.move_to(center, 2)
        cr.line_to(center, size - 2)
        cr.stroke()
        cr.move_to(2, center)
        cr.line_to(size - 2, center)
        cr.stroke()

        # Convert cairo surface to pixbuf
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, size, size)

        # Create cursor with hotspot at exact center
        return Gdk.Cursor.new_from_pixbuf(display, pixbuf, center, center)

    def _on_key_press(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.window.destroy()
            return True
        return False

    def _on_draw(self, widget: Gtk.Widget, cr) -> bool:
        cr.set_source_rgba(0, 0, 0, 0.3)
        cr.paint()

        if self.is_selecting:
            x = min(self.start_x, self.end_x)
            y = min(self.start_y, self.end_y)
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            try:
                import cairo

                cr.set_operator(cairo.OPERATOR_CLEAR)
            except ImportError:
                cr.set_operator(1)
            cr.rectangle(x, y, width, height)
            cr.fill()

            try:
                import cairo

                cr.set_operator(cairo.OPERATOR_OVER)
            except ImportError:
                cr.set_operator(0)
            cr.set_source_rgba(0.2, 0.6, 1.0, 1.0)
            cr.set_line_width(2)
            cr.rectangle(x, y, width, height)
            cr.stroke()

            cr.set_source_rgba(1, 1, 1, 1)
            cr.select_font_face("Sans")
            cr.set_font_size(14)
            text = f"{width} × {height}"
            cr.move_to(x + 5, y - 5)
            cr.show_text(text)

        return True

    def _on_button_press(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        if event.button == 1:
            self.start_x = int(event.x)
            self.start_y = int(event.y)
            self.end_x = self.start_x
            self.end_y = self.start_y
            self.is_selecting = True
        return True

    def _on_button_release(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        if event.button == 1 and self.is_selecting:
            self.end_x = int(event.x)
            self.end_y = int(event.y)
            self.is_selecting = False

            x = min(self.start_x, self.end_x)
            y = min(self.start_y, self.end_y)
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            self.window.destroy()

            if width > 10 and height > 10:
                # Apply scale factor for HiDPI displays
                sf = self.scale_factor
                self.callback(x * sf, y * sf, width * sf, height * sf)
        return True

    def _on_motion(self, widget: Gtk.Widget, event: Gdk.EventMotion) -> bool:
        if self.is_selecting:
            self.end_x = int(event.x)
            self.end_y = int(event.y)
            self.drawing_area.queue_draw()
        return True


class EditorWindow:
    """Enhanced screenshot editor window with all annotation tools."""

    def __init__(self, result: CaptureResult):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK is not available")

        if not result.success or result.pixbuf is None:
            raise ValueError("Invalid capture result")

        self.result = result
        self.editor_state = EditorState(result.pixbuf)
        self.uploader = Uploader()
        self._crosshair_cursor = None
        self._arrow_cursor = None

        self.window = Gtk.Window(title="LikX - Editor")
        self.window.set_default_size(900, 700)
        self.window.connect("destroy", self._on_destroy)
        self.window.connect("key-press-event", self._on_key_press)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_box)

        # Horizontal ribbon toolbar
        self.ribbon = self._create_ribbon_toolbar()
        main_box.pack_start(self.ribbon, False, False, 0)

        # Drawing area with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(
            result.pixbuf.get_width(), result.pixbuf.get_height()
        )

        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.connect("button-press-event", self._on_button_press)
        self.drawing_area.connect("button-release-event", self._on_button_release)
        self.drawing_area.connect("motion-notify-event", self._on_motion)
        self.drawing_area.connect("scroll-event", self._on_scroll)

        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
        )

        scrolled.add(self.drawing_area)
        main_box.pack_start(scrolled, True, True, 0)

        # Status bar with zoom indicator
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.statusbar = Gtk.Statusbar()
        self.statusbar_context = self.statusbar.get_context_id("editor")
        self.statusbar.push(self.statusbar_context, "Ready")
        status_box.pack_start(self.statusbar, True, True, 0)

        # Zoom label
        self.zoom_label = Gtk.Label(label="100%")
        self.zoom_label.set_size_request(60, -1)
        status_box.pack_end(self.zoom_label, False, False, 4)
        main_box.pack_start(status_box, False, False, 0)

        self.window.show_all()

        # Create cursors for drawing tools
        self._init_cursors()
        self._update_cursor()

    def _init_cursors(self) -> None:
        """Initialize cursors for drawing tools."""
        display = Gdk.Display.get_default()
        self._arrow_cursor = Gdk.Cursor.new_from_name(display, "default")

        # Create crosshair cursor with centered hotspot
        try:
            import cairo

            size = 24
            center = size // 2

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
            cr = cairo.Context(surface)

            # Black outline
            cr.set_source_rgba(0, 0, 0, 1)
            cr.set_line_width(3)
            cr.move_to(center, 2)
            cr.line_to(center, size - 2)
            cr.stroke()
            cr.move_to(2, center)
            cr.line_to(size - 2, center)
            cr.stroke()

            # White center
            cr.set_source_rgba(1, 1, 1, 1)
            cr.set_line_width(1)
            cr.move_to(center, 2)
            cr.line_to(center, size - 2)
            cr.stroke()
            cr.move_to(2, center)
            cr.line_to(size - 2, center)
            cr.stroke()

            pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, size, size)
            self._crosshair_cursor = Gdk.Cursor.new_from_pixbuf(
                display, pixbuf, center, center
            )
        except ImportError:
            self._crosshair_cursor = Gdk.Cursor.new_from_name(display, "crosshair")

    def _update_cursor(self) -> None:
        """Update cursor based on current tool."""
        if not hasattr(self, "drawing_area") or not self.drawing_area.get_window():
            return

        drawing_tools = {
            ToolType.PEN,
            ToolType.HIGHLIGHTER,
            ToolType.LINE,
            ToolType.ARROW,
            ToolType.RECTANGLE,
            ToolType.ELLIPSE,
            ToolType.BLUR,
            ToolType.PIXELATE,
            ToolType.ERASER,
            ToolType.CALLOUT,
            ToolType.CROP,
        }

        if self.editor_state.current_tool in drawing_tools:
            self.drawing_area.get_window().set_cursor(self._crosshair_cursor)
        else:
            self.drawing_area.get_window().set_cursor(self._arrow_cursor)

    def _create_ribbon_toolbar(self) -> Gtk.Box:
        """Create a hybrid dark/practical ribbon toolbar."""
        css = b"""
        /* === HYBRID DARK THEME (Aesthetic + Practical) === */
        .hybrid-ribbon {
            background: linear-gradient(180deg, #252536 0%, #1e1e2e 100%);
            border-bottom: 1px solid #3d3d5c;
            padding: 4px 6px;
            min-height: 52px;
        }

        /* Clean panel groups */
        .tool-panel {
            background: rgba(40, 40, 60, 0.5);
            border: 1px solid rgba(80, 80, 120, 0.3);
            border-radius: 8px;
            padding: 4px 8px;
            margin: 0 2px;
        }

        /* Readable group labels */
        .panel-label {
            font-size: 9px;
            font-weight: 600;
            color: #8888aa;
            margin-top: 2px;
        }

        /* Tool buttons - clear and clickable */
        .tool-btn {
            min-width: 28px;
            min-height: 28px;
            padding: 3px;
            border: 1px solid transparent;
            border-radius: 6px;
            background: transparent;
            color: #c0c0d0;
            font-size: 13px;
        }
        .tool-btn:hover {
            background: rgba(100, 100, 180, 0.2);
            border-color: rgba(130, 130, 200, 0.4);
            color: #ffffff;
        }
        .tool-btn:checked {
            background: rgba(100, 130, 220, 0.35);
            border-color: #6688dd;
            color: #ffffff;
        }

        /* Action buttons (save, copy, upload) */
        .action-btn {
            min-width: 28px;
            min-height: 28px;
            padding: 3px 6px;
            border: 1px solid rgba(100, 180, 100, 0.4);
            border-radius: 6px;
            background: rgba(80, 160, 80, 0.15);
            color: #90d090;
            font-size: 13px;
        }
        .action-btn:hover {
            background: rgba(80, 180, 80, 0.3);
            border-color: rgba(100, 200, 100, 0.6);
            color: #ffffff;
        }

        /* Color swatches - clear circles */
        .color-swatch {
            min-width: 16px;
            min-height: 16px;
            border-radius: 8px;
            border: 1px solid rgba(60, 60, 80, 0.8);
        }
        .color-swatch:hover {
            border-color: #8888cc;
            border-width: 2px;
        }

        /* Vertical separator */
        .panel-sep {
            background: rgba(100, 100, 140, 0.3);
            min-width: 1px;
            margin: 4px 4px;
        }

        /* Size spinner - readable */
        .size-spin {
            background: rgba(35, 35, 50, 0.9);
            border: 1px solid rgba(80, 80, 120, 0.5);
            border-radius: 4px;
            color: #d0d0e0;
            padding: 2px 4px;
            min-width: 45px;
        }
        .size-spin:focus {
            border-color: #7788cc;
        }

        /* Color picker button */
        .color-picker {
            border-radius: 6px;
            border: 2px solid rgba(80, 80, 120, 0.5);
        }
        .color-picker:hover {
            border-color: #8888cc;
        }
        """
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self._load_css(css),
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        ribbon = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        ribbon.get_style_context().add_class("hybrid-ribbon")

        # === TOOLS GROUP ===
        tools_group = self._create_tool_panel("Tools")
        tools_grid = Gtk.Grid(row_spacing=1, column_spacing=1)
        self.tool_buttons = {}
        # Clear icons with text tooltips
        tool_icons = [
            ("⊹", ToolType.SELECT, "Select (V) - Move/resize", 0, 0),
            ("✎", ToolType.PEN, "Pen (P)", 1, 0),
            ("—", ToolType.LINE, "Line (L)", 2, 0),
            ("▭", ToolType.RECTANGLE, "Rectangle (R)", 3, 0),
            ("A", ToolType.TEXT, "Text (T)", 4, 0),
            ("▓", ToolType.HIGHLIGHTER, "Highlighter (H)", 0, 1),
            ("→", ToolType.ARROW, "Arrow (A)", 1, 1),
            ("○", ToolType.ELLIPSE, "Ellipse (E)", 2, 1),
            ("✕", ToolType.ERASER, "Eraser", 3, 1),
            ("💬", ToolType.CALLOUT, "Callout (K)", 4, 1),
            ("📏", ToolType.MEASURE, "Measure (M)", 0, 2),
            ("①", ToolType.NUMBER, "Number Marker (N)", 1, 2),
            ("💧", ToolType.COLORPICKER, "Color Picker (I)", 2, 2),
            ("✓", ToolType.STAMP, "Stamp (S)", 3, 2),
            ("✂", ToolType.CROP, "Crop (C) - Shift for 1:1", 4, 2),
            ("🔍", ToolType.ZOOM, "Zoom (Z) - Scroll to zoom", 0, 3),
        ]
        for icon, tool, tip, col, row in tool_icons:
            btn = Gtk.ToggleButton(label=icon)
            btn.set_tooltip_text(tip)
            btn.get_style_context().add_class("tool-btn")
            btn.connect("toggled", self._on_tool_toggled, tool)
            self.tool_buttons[tool] = btn
            tools_grid.attach(btn, col, row, 1, 1)
        self.tool_buttons[ToolType.PEN].set_active(True)
        tools_group.pack_start(tools_grid, False, False, 0)
        ribbon.pack_start(tools_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === PRIVACY GROUP ===
        priv_group = self._create_tool_panel("Privacy")
        priv_grid = Gtk.Grid(row_spacing=1, column_spacing=1)
        for icon, tool, tip, col in [
            ("▦", ToolType.BLUR, "Blur (B)", 0),
            ("▤", ToolType.PIXELATE, "Pixelate (X)", 1),
        ]:
            btn = Gtk.ToggleButton(label=icon)
            btn.set_tooltip_text(tip)
            btn.get_style_context().add_class("tool-btn")
            btn.connect("toggled", self._on_tool_toggled, tool)
            self.tool_buttons[tool] = btn
            priv_grid.attach(btn, col, 0, 1, 1)
        priv_group.pack_start(priv_grid, False, False, 0)
        ribbon.pack_start(priv_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === STAMPS GROUP ===
        stamps_group = self._create_tool_panel("Stamps")
        stamps_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.stamp_buttons = {}
        stamps = ["✓", "✗", "⚠", "❓", "⭐", "❤", "👍", "👎"]
        for stamp in stamps:
            btn = Gtk.ToggleButton(label=stamp)
            btn.set_tooltip_text(f"Stamp: {stamp}")
            btn.get_style_context().add_class("stamp-btn")
            btn.connect("toggled", self._on_stamp_toggled, stamp)
            self.stamp_buttons[stamp] = btn
            stamps_box.pack_start(btn, False, False, 0)
        self.stamp_buttons["✓"].set_active(True)
        stamps_group.pack_start(stamps_box, False, False, 0)
        ribbon.pack_start(stamps_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === ARROW STYLES GROUP ===
        arrow_group = self._create_tool_panel("Arrow Style")
        arrow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.arrow_style_buttons = {}
        arrow_styles = [
            ("→", ArrowStyle.OPEN, "Open arrowhead"),
            ("▶", ArrowStyle.FILLED, "Filled arrowhead"),
            ("⟷", ArrowStyle.DOUBLE, "Double arrowhead"),
        ]
        for label, style, tooltip in arrow_styles:
            btn = Gtk.ToggleButton(label=label)
            btn.set_tooltip_text(tooltip)
            btn.get_style_context().add_class("arrow-style-btn")
            btn.connect("toggled", self._on_arrow_style_toggled, style)
            self.arrow_style_buttons[style] = btn
            arrow_box.pack_start(btn, False, False, 0)
        self.arrow_style_buttons[ArrowStyle.OPEN].set_active(True)
        arrow_group.pack_start(arrow_box, False, False, 0)
        ribbon.pack_start(arrow_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === FONT FORMAT GROUP ===
        font_group = self._create_tool_panel("Text Style")
        font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Bold button
        self.bold_btn = Gtk.ToggleButton(label="B")
        self.bold_btn.set_tooltip_text("Bold (for text tool)")
        self.bold_btn.get_style_context().add_class("font-style-btn")
        self.bold_btn.connect("toggled", self._on_bold_toggled)
        font_box.pack_start(self.bold_btn, False, False, 0)

        # Italic button
        self.italic_btn = Gtk.ToggleButton(label="I")
        self.italic_btn.set_tooltip_text("Italic (for text tool)")
        self.italic_btn.get_style_context().add_class("font-style-btn")
        self.italic_btn.connect("toggled", self._on_italic_toggled)
        font_box.pack_start(self.italic_btn, False, False, 0)

        # Font family dropdown
        self.font_combo = Gtk.ComboBoxText()
        fonts = ["Sans", "Serif", "Monospace", "Ubuntu", "DejaVu Sans"]
        for font in fonts:
            self.font_combo.append_text(font)
        self.font_combo.set_active(0)
        self.font_combo.set_tooltip_text("Font family")
        self.font_combo.connect("changed", self._on_font_family_changed)
        font_box.pack_start(self.font_combo, False, False, 0)

        font_group.pack_start(font_box, False, False, 0)
        ribbon.pack_start(font_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === SIZE GROUP ===
        size_group = self._create_tool_panel("Size")
        self.size_spin = Gtk.SpinButton()
        self.size_spin.set_range(1, 50)
        self.size_spin.set_value(3)
        self.size_spin.set_increments(1, 5)
        self.size_spin.set_tooltip_text("Brush size")
        self.size_spin.get_style_context().add_class("size-spin")
        self.size_spin.connect("value-changed", self._on_size_changed)
        size_group.pack_start(self.size_spin, False, False, 0)
        ribbon.pack_start(size_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === COLORS GROUP (Standard 20-color palette) ===
        colors_group = self._create_tool_panel("Colors")
        colors_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        # Standard practical palette - 20 colors
        palette = [
            # Row 1: Dark shades
            (0, 0, 0),
            (0.4, 0.4, 0.4),
            (0.5, 0, 0),
            (0.5, 0.25, 0),
            (0.5, 0.5, 0),
            (0, 0.4, 0),
            (0, 0.4, 0.4),
            (0, 0, 0.5),
            (0.3, 0, 0.5),
            (0.5, 0, 0.3),
            # Row 2: Bright shades
            (1, 1, 1),
            (0.75, 0.75, 0.75),
            (1, 0, 0),
            (1, 0.5, 0),
            (1, 1, 0),
            (0, 0.8, 0),
            (0, 0.8, 0.8),
            (0, 0, 1),
            (0.6, 0.3, 1),
            (1, 0.4, 0.7),
        ]
        color_grid = Gtk.Grid(row_spacing=2, column_spacing=2)
        for i, (r, g, b) in enumerate(palette):
            btn = Gtk.Button()
            btn.get_style_context().add_class("color-swatch")
            da = Gtk.DrawingArea()
            da.set_size_request(16, 16)
            da.connect(
                "draw", lambda w, cr, r=r, g=g, b=b: self._draw_color_dot(cr, r, g, b)
            )
            btn.add(da)
            btn.set_tooltip_text(f"RGB({int(r * 255)},{int(g * 255)},{int(b * 255)})")
            btn.connect(
                "clicked", lambda b, r=r, g=g, bl=b: self._set_color_rgb(r, g, bl)
            )
            color_grid.attach(btn, i % 10, i // 10, 1, 1)
        colors_box.pack_start(color_grid, False, False, 0)
        # Custom color picker
        self.color_btn = Gtk.ColorButton()
        self.color_btn.set_rgba(Gdk.RGBA(1, 0, 0, 1))  # Default red
        self.color_btn.set_tooltip_text("Custom color")
        self.color_btn.get_style_context().add_class("color-picker")
        self.color_btn.connect("color-set", self._on_color_chosen)
        colors_box.pack_start(self.color_btn, False, False, 4)
        colors_group.pack_start(colors_box, False, False, 0)
        ribbon.pack_start(colors_group, False, False, 0)
        ribbon.pack_start(self._create_panel_sep(), False, False, 0)

        # === EDIT GROUP ===
        edit_group = self._create_tool_panel("Edit")
        edit_box = Gtk.Box(spacing=2)
        for icon, cb, tip in [
            ("↶", self._undo, "Undo (Ctrl+Z)"),
            ("↷", self._redo, "Redo (Ctrl+Y)"),
            ("✕", self._clear, "Clear All"),
        ]:
            btn = Gtk.Button(label=icon)
            btn.set_tooltip_text(tip)
            btn.get_style_context().add_class("tool-btn")
            btn.connect("clicked", lambda b, c=cb: c())
            edit_box.pack_start(btn, False, False, 0)
        edit_group.pack_start(edit_box, False, False, 0)
        ribbon.pack_start(edit_group, False, False, 0)

        # Spacer
        ribbon.pack_start(Gtk.Box(), True, True, 0)

        # === OUTPUT GROUP ===
        out_group = self._create_tool_panel("Output")
        out_box = Gtk.Box(spacing=3)
        for icon, cb, tip in [
            ("📋", self._copy_to_clipboard, "Copy"),
            ("💾", self._save, "Save"),
            ("☁", self._upload, "Upload"),
        ]:
            btn = Gtk.Button(label=icon)
            btn.set_tooltip_text(tip)
            btn.get_style_context().add_class("action-btn")
            btn.connect("clicked", lambda b, c=cb: c())
            out_box.pack_start(btn, False, False, 0)
        out_group.pack_start(out_box, False, False, 0)
        ribbon.pack_start(out_group, False, False, 0)

        return ribbon

    def _load_css(self, css: bytes) -> Gtk.CssProvider:
        """Load CSS into a provider."""
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        return provider

    def _create_glass_panel(self, label: str) -> Gtk.Box:
        """Create a futuristic glass panel group with label."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("glass-panel")
        lbl = Gtk.Label(label=label)
        lbl.get_style_context().add_class("glass-label")
        box.pack_end(lbl, False, False, 0)
        return box

    def _create_tool_panel(self, label: str) -> Gtk.Box:
        """Create a hybrid tool panel group with readable label."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("tool-panel")
        lbl = Gtk.Label(label=label)
        lbl.get_style_context().add_class("panel-label")
        box.pack_end(lbl, False, False, 0)
        return box

    def _create_panel_sep(self) -> Gtk.Separator:
        """Create panel separator for hybrid theme."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(4)
        sep.set_margin_end(4)
        return sep

    def _create_ribbon_group(self, label: str) -> Gtk.Box:
        """Create a ribbon group with label (legacy)."""
        return self._create_glass_panel(label)

    def _create_ribbon_sep(self) -> Gtk.Separator:
        """Create ribbon separator."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.get_style_context().add_class("neo-sep")
        return sep

    def _draw_color_dot(self, cr, r: float, g: float, b: float) -> bool:
        """Draw a color dot (legacy)."""
        return self._draw_neo_color(cr, r, g, b)

    def _draw_neo_color(self, cr, r: float, g: float, b: float) -> bool:
        """Draw a futuristic color circle with glow effect."""
        # Outer glow
        cr.set_source_rgba(r, g, b, 0.3)
        cr.arc(9, 9, 9, 0, 3.14159 * 2)
        cr.fill()
        # Main color
        cr.set_source_rgb(r, g, b)
        cr.arc(9, 9, 7, 0, 3.14159 * 2)
        cr.fill()
        # Inner highlight
        cr.set_source_rgba(1, 1, 1, 0.3)
        cr.arc(7, 7, 3, 0, 3.14159 * 2)
        cr.fill()
        return True

    def _set_color_rgb(self, r: float, g: float, b: float) -> None:
        """Set color from RGB and update button."""
        self.editor_state.set_color(Color(r, g, b, 1.0))
        self.color_btn.set_rgba(Gdk.RGBA(r, g, b, 1.0))

    def _create_separator(self) -> Gtk.Separator:
        """Create a vertical separator."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.get_style_context().add_class("toolbar-separator")
        return sep

    def _on_tool_toggled(self, button: Gtk.ToggleButton, tool: ToolType) -> None:
        """Handle tool toggle button."""
        if button.get_active():
            # Deactivate other tool buttons
            for t, btn in self.tool_buttons.items():
                if t != tool and btn.get_active():
                    btn.set_active(False)
            self._set_tool(tool)
        elif not any(btn.get_active() for btn in self.tool_buttons.values()):
            # Ensure at least one tool is always selected
            button.set_active(True)

    def _on_stamp_toggled(self, button: Gtk.ToggleButton, stamp: str) -> None:
        """Handle stamp selection toggle."""
        if button.get_active():
            # Deactivate other stamp buttons
            for s, btn in self.stamp_buttons.items():
                if s != stamp and btn.get_active():
                    btn.set_active(False)
            self.editor_state.set_stamp(stamp)
        elif not any(btn.get_active() for btn in self.stamp_buttons.values()):
            # Ensure at least one stamp is always selected
            button.set_active(True)

    def _on_arrow_style_toggled(
        self, button: Gtk.ToggleButton, style: ArrowStyle
    ) -> None:
        """Handle arrow style selection toggle."""
        if button.get_active():
            # Deactivate other arrow style buttons
            for s, btn in self.arrow_style_buttons.items():
                if s != style and btn.get_active():
                    btn.set_active(False)
            self.editor_state.set_arrow_style(style)
        elif not any(btn.get_active() for btn in self.arrow_style_buttons.values()):
            # Ensure at least one style is always selected
            button.set_active(True)

    def _on_bold_toggled(self, button: Gtk.ToggleButton) -> None:
        """Handle bold toggle."""
        self.editor_state.set_font_bold(button.get_active())

    def _on_italic_toggled(self, button: Gtk.ToggleButton) -> None:
        """Handle italic toggle."""
        self.editor_state.set_font_italic(button.get_active())

    def _on_font_family_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle font family change."""
        font = combo.get_active_text()
        if font:
            self.editor_state.set_font_family(font)

    def _on_color_chosen(self, button: Gtk.ColorButton) -> None:
        """Handle color picker selection."""
        rgba = button.get_rgba()
        self._set_color(Color(rgba.red, rgba.green, rgba.blue, rgba.alpha))

    def _set_tool(self, tool: ToolType) -> None:
        """Set the current drawing tool."""
        self.editor_state.set_tool(tool)
        self._update_cursor()
        if hasattr(self, "statusbar"):
            self.statusbar.push(self.statusbar_context, f"Tool: {tool.value}")

    def _set_color(self, color: Color) -> None:
        """Set the current drawing color."""
        self.editor_state.set_color(color)

    def _on_size_changed(self, spin: Gtk.SpinButton) -> None:
        """Handle size change."""
        self.editor_state.set_stroke_width(spin.get_value())

    def _undo(self) -> None:
        """Undo the last action."""
        if self.editor_state.undo():
            self.drawing_area.queue_draw()
            self.statusbar.push(self.statusbar_context, "Undone")

    def _redo(self) -> None:
        """Redo the last undone action."""
        if self.editor_state.redo():
            self.drawing_area.queue_draw()
            self.statusbar.push(self.statusbar_context, "Redone")

    def _clear(self) -> None:
        """Clear all drawings."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all annotations?",
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.editor_state.clear()
            self.drawing_area.queue_draw()
            self.statusbar.push(self.statusbar_context, "Cleared")

    def _show_command_palette(self) -> None:
        """Show the command palette for quick command access."""
        if not hasattr(self, "_command_palette") or self._command_palette is None:
            from .commands import build_command_registry
            from .command_palette import CommandPalette

            commands = build_command_registry(self)
            self._command_palette = CommandPalette(commands, self.window)

        self._command_palette.show_centered(self.window)

    def _show_radial_menu(self, x: float, y: float) -> None:
        """Show the radial menu for quick tool selection."""
        if not hasattr(self, "_radial_menu") or self._radial_menu is None:
            from .radial_menu import RadialMenu

            self._radial_menu = RadialMenu(self._on_radial_select)

        self._radial_menu.show_at(int(x), int(y))

    def _on_radial_select(self, tool_type) -> None:
        """Handle tool selection from radial menu."""
        if tool_type is not None:
            self._set_tool(tool_type)
            # Update toggle buttons if they exist
            if hasattr(self, "tool_buttons") and tool_type in self.tool_buttons:
                self.tool_buttons[tool_type].set_active(True)

    def _save_with_annotations(self, filepath: Path) -> bool:
        """Save the image with annotations rendered."""
        try:
            import cairo

            # Create surface
            width = self.result.pixbuf.get_width()
            height = self.result.pixbuf.get_height()

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            ctx = cairo.Context(surface)

            # Draw original image
            Gdk.cairo_set_source_pixbuf(ctx, self.result.pixbuf, 0, 0)
            ctx.paint()

            # Render annotations
            elements = self.editor_state.elements
            if elements:
                render_elements(surface, elements, self.result.pixbuf)

            # Convert to pixbuf and save
            data = surface.get_data()
            new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                data,
                GdkPixbuf.Colorspace.RGB,
                True,
                8,
                width,
                height,
                cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width),
            )

            # Determine format
            format_str = filepath.suffix.lstrip(".").lower()
            format_map = {
                "jpg": "jpeg",
                "jpeg": "jpeg",
                "png": "png",
                "bmp": "bmp",
                "gif": "gif",
            }
            pixbuf_format = format_map.get(format_str, "png")

            filepath.parent.mkdir(parents=True, exist_ok=True)
            new_pixbuf.savev(str(filepath), pixbuf_format, [], [])

            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def _save(self) -> None:
        """Save the edited screenshot."""
        dialog = Gtk.FileChooserDialog(
            title="Save Screenshot",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )
        dialog.set_do_overwrite_confirmation(True)

        # Add filters
        for fmt_name, fmt_ext in [
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("BMP", "*.bmp"),
            ("GIF", "*.gif"),
        ]:
            filter_fmt = Gtk.FileFilter()
            filter_fmt.set_name(f"{fmt_name} images")
            filter_fmt.add_pattern(fmt_ext)
            dialog.add_filter(filter_fmt)

        # Set default filename
        default_path = config.get_save_path()
        dialog.set_current_folder(str(default_path.parent))
        dialog.set_current_name(default_path.name)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = Path(dialog.get_filename())
            if self._save_with_annotations(filepath):
                self.statusbar.push(self.statusbar_context, f"Saved to {filepath.name}")
                cfg = config.load_config()
                if cfg.get("show_notification", True):
                    show_screenshot_saved(str(filepath))

        dialog.destroy()

    def _upload(self) -> None:
        """Upload the screenshot to cloud service."""
        # Save to temp file first
        import tempfile

        temp_file = Path(tempfile.mktemp(suffix=".png"))

        if not self._save_with_annotations(temp_file):
            show_upload_error("Failed to prepare image for upload")
            return

        self.statusbar.push(self.statusbar_context, "Uploading...")

        # Upload
        success, url, error = self.uploader.upload_to_imgur(temp_file)

        # Cleanup
        if temp_file.exists():
            temp_file.unlink()

        if success:
            self.uploader.copy_url_to_clipboard(url)
            self.statusbar.push(self.statusbar_context, f"Uploaded: {url}")
            show_upload_success(url)
        else:
            self.statusbar.push(self.statusbar_context, f"Upload failed: {error}")
            show_upload_error(error)

    def _copy_to_clipboard(self) -> None:
        """Copy the edited screenshot to clipboard."""
        try:
            import cairo

            # Create surface with annotations
            width = self.result.pixbuf.get_width()
            height = self.result.pixbuf.get_height()

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            ctx = cairo.Context(surface)

            Gdk.cairo_set_source_pixbuf(ctx, self.result.pixbuf, 0, 0)
            ctx.paint()

            if self.editor_state.elements:
                render_elements(surface, self.editor_state.elements, self.result.pixbuf)

            # Convert to pixbuf
            data = surface.get_data()
            new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                data,
                GdkPixbuf.Colorspace.RGB,
                True,
                8,
                width,
                height,
                cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width),
            )

            # Copy to clipboard
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_image(new_pixbuf)
            clipboard.store()

            self.statusbar.push(self.statusbar_context, "Copied to clipboard")
            cfg = config.load_config()
            if cfg.get("show_notification", True):
                show_screenshot_copied()
        except Exception as e:
            self.statusbar.push(self.statusbar_context, f"Copy failed: {e}")

    def _on_draw(self, widget: Gtk.Widget, cr) -> bool:
        """Draw the screenshot and annotations with zoom support."""
        zoom = self.editor_state.zoom_level

        # Update drawing area size based on zoom
        base_width = self.result.pixbuf.get_width()
        base_height = self.result.pixbuf.get_height()
        new_width = int(base_width * zoom)
        new_height = int(base_height * zoom)
        self.drawing_area.set_size_request(new_width, new_height)

        # Apply zoom transform
        cr.scale(zoom, zoom)

        # Draw the image
        Gdk.cairo_set_source_pixbuf(cr, self.result.pixbuf, 0, 0)
        cr.paint()

        # Draw annotations (also scaled)
        elements = self.editor_state.get_elements()
        if elements:
            render_elements(cr, elements, self.result.pixbuf)

        # Draw callout preview during drag
        if (
            self.editor_state.is_drawing
            and self.editor_state.current_tool == ToolType.CALLOUT
            and hasattr(self, "_callout_tail")
            and hasattr(self, "_callout_box")
        ):
            self._draw_callout_preview(cr)

        # Draw crop selection preview
        if (
            self.editor_state.is_drawing
            and self.editor_state.current_tool == ToolType.CROP
            and hasattr(self, "_crop_start")
            and hasattr(self, "_crop_end")
        ):
            self._draw_crop_preview(cr)

        # Draw selection handles if an element is selected
        if self.editor_state.selected_index is not None:
            self._draw_selection_handles(cr)
            self._draw_snap_guides(cr)

        return True

    def _draw_callout_preview(self, cr) -> None:
        """Draw a preview of the callout being created."""
        tail_x, tail_y = self._callout_tail
        box_x, box_y = self._callout_box

        # Draw a simple preview box and line
        preview_text = "Click & drag to position"
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(14)
        extents = cr.text_extents(preview_text)

        padding = 10
        box_width = extents.width + padding * 2
        box_height = extents.height + padding * 2
        corner_radius = 8

        # Box position (centered on box position)
        bx = box_x - box_width / 2
        by = box_y - box_height / 2

        # Draw rounded rectangle
        cr.new_path()
        cr.move_to(bx + corner_radius, by)
        cr.line_to(bx + box_width - corner_radius, by)
        cr.arc(bx + box_width - corner_radius, by + corner_radius, corner_radius, -3.14159 / 2, 0)
        cr.line_to(bx + box_width, by + box_height - corner_radius)
        cr.arc(bx + box_width - corner_radius, by + box_height - corner_radius, corner_radius, 0, 3.14159 / 2)
        cr.line_to(bx + corner_radius, by + box_height)
        cr.arc(bx + corner_radius, by + box_height - corner_radius, corner_radius, 3.14159 / 2, 3.14159)
        cr.line_to(bx, by + corner_radius)
        cr.arc(bx + corner_radius, by + corner_radius, corner_radius, 3.14159, 3 * 3.14159 / 2)
        cr.close_path()

        # Fill with light yellow (preview)
        cr.set_source_rgba(1.0, 1.0, 0.9, 0.8)
        cr.fill_preserve()

        # Border
        r, g, b, a = self.editor_state.current_color.to_tuple()
        cr.set_source_rgba(r, g, b, 0.8)
        cr.set_line_width(2)
        cr.stroke()

        # Draw tail line from box to point
        cr.move_to(box_x, box_y)
        cr.line_to(tail_x, tail_y)
        cr.stroke()

        # Draw a small circle at tail tip
        cr.arc(tail_x, tail_y, 4, 0, 2 * 3.14159)
        cr.fill()

        # Draw preview text
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.8)
        cr.move_to(bx + padding, by + padding + extents.height)
        cr.show_text(preview_text)

    def _draw_crop_preview(self, cr) -> None:
        """Draw the crop selection rectangle with darkened outside area."""
        x1, y1 = self._crop_start
        x2, y2 = self._crop_end

        # Normalize coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        width = right - left
        height = bottom - top

        if width < 2 or height < 2:
            return

        # Get image dimensions
        img_w = self.result.pixbuf.get_width()
        img_h = self.result.pixbuf.get_height()

        # Darken areas outside selection
        cr.set_source_rgba(0, 0, 0, 0.5)
        # Top
        cr.rectangle(0, 0, img_w, top)
        cr.fill()
        # Bottom
        cr.rectangle(0, bottom, img_w, img_h - bottom)
        cr.fill()
        # Left
        cr.rectangle(0, top, left, height)
        cr.fill()
        # Right
        cr.rectangle(right, top, img_w - right, height)
        cr.fill()

        # Draw selection border
        cr.set_source_rgba(1, 1, 1, 0.9)
        cr.set_line_width(2)
        cr.rectangle(left, top, width, height)
        cr.stroke()

        # Draw corner handles
        handle_size = 8
        cr.set_source_rgba(1, 1, 1, 1)
        for hx, hy in [(left, top), (right, top), (left, bottom), (right, bottom)]:
            cr.rectangle(hx - handle_size / 2, hy - handle_size / 2, handle_size, handle_size)
            cr.fill()

        # Draw dimension text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        dim_text = f"{int(width)} × {int(height)}"
        extents = cr.text_extents(dim_text)

        # Position below selection
        tx = left + (width - extents.width) / 2
        ty = bottom + 20

        # Background for text
        cr.set_source_rgba(0, 0, 0, 0.7)
        cr.rectangle(tx - 4, ty - extents.height - 2, extents.width + 8, extents.height + 6)
        cr.fill()

        # Text
        cr.set_source_rgba(1, 1, 1, 1)
        cr.move_to(tx, ty)
        cr.show_text(dim_text)

    def _draw_selection_handles(self, cr) -> None:
        """Draw selection bounding box and resize handles for selected element."""
        selected = self.editor_state.get_selected()
        if not selected:
            return

        bbox = self.editor_state._get_element_bbox(selected)
        if not bbox:
            return

        x1, y1, x2, y2 = bbox

        # Draw selection rectangle (dashed blue)
        cr.set_source_rgba(0.2, 0.5, 1.0, 0.8)
        cr.set_line_width(1.5)
        cr.set_dash([4, 4])
        cr.rectangle(x1, y1, x2 - x1, y2 - y1)
        cr.stroke()
        cr.set_dash([])  # Reset dash

        # Draw resize handles at corners
        handle_size = 8
        handles = [
            (x1, y1),  # nw
            (x2, y1),  # ne
            (x1, y2),  # sw
            (x2, y2),  # se
        ]

        for hx, hy in handles:
            # White fill with blue border
            cr.set_source_rgba(1, 1, 1, 1)
            cr.rectangle(
                hx - handle_size / 2,
                hy - handle_size / 2,
                handle_size,
                handle_size,
            )
            cr.fill_preserve()
            cr.set_source_rgba(0.2, 0.5, 1.0, 1)
            cr.set_line_width(1)
            cr.stroke()

    def _draw_snap_guides(self, cr) -> None:
        """Draw visual snap guides when dragging an element."""
        if not self.editor_state.active_snap_guides:
            return

        # Get drawing area size for guide lines
        width = self.drawing_area.get_allocated_width()
        height = self.drawing_area.get_allocated_height()

        # Draw snap guides in cyan dashed lines
        cr.set_source_rgba(0.0, 0.8, 0.8, 0.9)
        cr.set_line_width(1)
        cr.set_dash([6, 4])

        for guide_type, value in self.editor_state.active_snap_guides:
            if guide_type == 'h':
                # Horizontal line at y=value
                cr.move_to(0, value)
                cr.line_to(width, value)
                cr.stroke()
            elif guide_type == 'v':
                # Vertical line at x=value
                cr.move_to(value, 0)
                cr.line_to(value, height)
                cr.stroke()

        cr.set_dash([])  # Reset dash

    def _apply_crop(self) -> None:
        """Apply the crop operation to the image."""
        if not hasattr(self, "_crop_start") or not hasattr(self, "_crop_end"):
            return

        x1, y1 = self._crop_start
        x2, y2 = self._crop_end

        # Normalize coordinates
        left = int(min(x1, x2))
        top = int(min(y1, y2))
        right = int(max(x1, x2))
        bottom = int(max(y1, y2))
        width = right - left
        height = bottom - top

        # Minimum crop size
        if width < 10 or height < 10:
            self.statusbar.push(
                self.statusbar_context, "Crop area too small (min 10×10)"
            )
            # Clean up
            if hasattr(self, "_crop_start"):
                del self._crop_start
            if hasattr(self, "_crop_end"):
                del self._crop_end
            self.drawing_area.queue_draw()
            return

        # Clamp to image bounds
        img_w = self.result.pixbuf.get_width()
        img_h = self.result.pixbuf.get_height()
        left = max(0, left)
        top = max(0, top)
        width = min(width, img_w - left)
        height = min(height, img_h - top)

        # Create cropped pixbuf
        cropped = GdkPixbuf.Pixbuf.new(
            GdkPixbuf.Colorspace.RGB,
            self.result.pixbuf.get_has_alpha(),
            8,
            width,
            height,
        )
        self.result.pixbuf.copy_area(left, top, width, height, cropped, 0, 0)
        self.result.pixbuf = cropped

        # Clear annotations (they're now outside the image)
        self.editor_state.clear()

        # Clean up
        del self._crop_start
        del self._crop_end

        self.statusbar.push(
            self.statusbar_context, f"Cropped to {width}×{height}"
        )
        self.drawing_area.queue_draw()

    def _screen_to_image(self, x: float, y: float) -> tuple:
        """Convert screen coordinates to image coordinates (accounting for zoom)."""
        zoom = self.editor_state.zoom_level
        return x / zoom, y / zoom

    def _on_button_press(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle mouse button press."""
        # Convert screen coords to image coords
        img_x, img_y = self._screen_to_image(event.x, event.y)

        if event.button == 1:
            if self.editor_state.current_tool == ToolType.SELECT:
                # Try to select an element at this position
                self.editor_state.select_at(img_x, img_y)
                self.drawing_area.queue_draw()
            elif self.editor_state.current_tool == ToolType.TEXT:
                # Show text input dialog
                self._show_text_dialog(img_x, img_y)
            elif self.editor_state.current_tool == ToolType.NUMBER:
                # Place number marker on click
                self.editor_state.add_number(img_x, img_y)
                self.drawing_area.queue_draw()
            elif self.editor_state.current_tool == ToolType.COLORPICKER:
                # Pick color from image
                self._pick_color(img_x, img_y)
            elif self.editor_state.current_tool == ToolType.STAMP:
                # Place stamp on click
                self.editor_state.add_stamp(img_x, img_y)
                self.drawing_area.queue_draw()
            elif self.editor_state.current_tool == ToolType.CALLOUT:
                # Start callout: first point is tail tip
                self._callout_tail = (img_x, img_y)
                self._callout_box = (img_x + 50, img_y - 50)  # Initial offset
                self.editor_state.is_drawing = True
            elif self.editor_state.current_tool == ToolType.CROP:
                # Start crop selection
                self._crop_start = (img_x, img_y)
                self._crop_end = (img_x, img_y)
                self._crop_shift = event.state & Gdk.ModifierType.SHIFT_MASK
                self.editor_state.is_drawing = True
            else:
                self.editor_state.start_drawing(img_x, img_y)
        elif event.button == 3:
            # Right-click: show radial menu
            self._show_radial_menu(event.x_root, event.y_root)
        return True

    def _on_button_release(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle mouse button release."""
        img_x, img_y = self._screen_to_image(event.x, event.y)
        if event.button == 1:
            if self.editor_state.current_tool == ToolType.SELECT:
                # Finish moving/resizing
                self.editor_state.finish_move()
                self.drawing_area.queue_draw()
            elif self.editor_state.current_tool == ToolType.CALLOUT:
                # Finish callout: show text dialog
                if hasattr(self, "_callout_tail"):
                    self._callout_box = (img_x, img_y)
                    self.editor_state.is_drawing = False
                    self._show_callout_dialog()
            elif self.editor_state.current_tool == ToolType.CROP:
                # Apply crop
                if hasattr(self, "_crop_start") and hasattr(self, "_crop_end"):
                    self.editor_state.is_drawing = False
                    self._apply_crop()
            elif self.editor_state.current_tool != ToolType.TEXT:
                self.editor_state.finish_drawing(img_x, img_y)
                self.drawing_area.queue_draw()
        return True

    def _on_motion(self, widget: Gtk.Widget, event: Gdk.EventMotion) -> bool:
        """Handle mouse motion."""
        img_x, img_y = self._screen_to_image(event.x, event.y)

        # Handle SELECT tool dragging (move/resize)
        if self.editor_state.current_tool == ToolType.SELECT:
            if self.editor_state._drag_start is not None:
                if self.editor_state.move_selected(img_x, img_y):
                    self.drawing_area.queue_draw()
            return True

        if self.editor_state.is_drawing:
            if self.editor_state.current_tool == ToolType.CALLOUT:
                # Update callout box position during drag
                if hasattr(self, "_callout_tail"):
                    self._callout_box = (img_x, img_y)
                    self.drawing_area.queue_draw()
            elif self.editor_state.current_tool == ToolType.CROP:
                # Update crop selection with aspect ratio lock
                if hasattr(self, "_crop_start"):
                    # Check if shift is held for 1:1 aspect ratio
                    shift = event.state & Gdk.ModifierType.SHIFT_MASK
                    if shift:
                        # Lock to 1:1 (square)
                        dx = img_x - self._crop_start[0]
                        dy = img_y - self._crop_start[1]
                        size = max(abs(dx), abs(dy))
                        self._crop_end = (
                            self._crop_start[0] + (size if dx >= 0 else -size),
                            self._crop_start[1] + (size if dy >= 0 else -size),
                        )
                    else:
                        self._crop_end = (img_x, img_y)
                    self.drawing_area.queue_draw()
            elif self.editor_state.current_tool != ToolType.TEXT:
                self.editor_state.continue_drawing(img_x, img_y)
                self.drawing_area.queue_draw()
        return True

    def _on_scroll(self, widget: Gtk.Widget, event: Gdk.EventScroll) -> bool:
        """Handle scroll events for zooming."""
        # Only zoom when Ctrl is held or when Zoom tool is active
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        is_zoom_tool = self.editor_state.current_tool == ToolType.ZOOM

        if ctrl or is_zoom_tool:
            if event.direction == Gdk.ScrollDirection.UP:
                self.editor_state.zoom_in()
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.editor_state.zoom_out()
            elif event.direction == Gdk.ScrollDirection.SMOOTH:
                # Handle smooth scrolling (trackpads)
                _, dx, dy = event.get_scroll_deltas()
                if dy < 0:
                    self.editor_state.zoom_in(1.1)
                elif dy > 0:
                    self.editor_state.zoom_out(1.1)

            self._update_zoom_label()
            self.drawing_area.queue_draw()
            return True
        return False

    def _update_zoom_label(self) -> None:
        """Update the zoom percentage label."""
        if hasattr(self, "zoom_label"):
            percent = int(self.editor_state.zoom_level * 100)
            self.zoom_label.set_text(f"{percent}%")

    def _show_text_dialog(self, x: float, y: float) -> None:
        """Show dialog to input text."""
        dialog = Gtk.Dialog(
            title="Add Text",
            parent=self.window,
            flags=0,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(10)

        label = Gtk.Label(label="Enter text:")
        content.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        text = entry.get_text()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and text:
            self.editor_state.add_text(x, y, text)
            self.drawing_area.queue_draw()

    def _show_callout_dialog(self) -> None:
        """Show dialog to input callout text."""
        if not hasattr(self, "_callout_tail") or not hasattr(self, "_callout_box"):
            return

        dialog = Gtk.Dialog(
            title="Add Callout",
            parent=self.window,
            flags=0,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(10)

        label = Gtk.Label(label="Enter callout text:")
        content.pack_start(label, False, False, 0)

        # Text view for multiline input
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(300, 100)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(text_view)
        content.pack_start(scrolled, True, True, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        buffer = text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        dialog.destroy()

        if response == Gtk.ResponseType.OK and text.strip():
            tail_x, tail_y = self._callout_tail
            box_x, box_y = self._callout_box
            self.editor_state.add_callout(tail_x, tail_y, box_x, box_y, text.strip())
            self.drawing_area.queue_draw()

        # Clean up
        if hasattr(self, "_callout_tail"):
            del self._callout_tail
        if hasattr(self, "_callout_box"):
            del self._callout_box

    def _pick_color(self, x: float, y: float) -> None:
        """Pick color from image and set as current color."""
        color = self.editor_state.pick_color(x, y)
        if color:
            self.editor_state.set_color(color)
            # Update UI color button if it exists
            if hasattr(self, "color_buttons"):
                # Deselect all preset colors
                for btn in self.color_buttons.values():
                    btn.set_active(False)
            # Show feedback
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(color.r * 255), int(color.g * 255), int(color.b * 255)
            )
            self._show_toast(f"Color picked: {hex_color}")

    def _show_toast(self, message: str) -> None:
        """Show a brief toast notification."""
        # Use statusbar if available, otherwise just print
        if hasattr(self, "statusbar"):
            ctx = self.statusbar.get_context_id("toast")
            self.statusbar.push(ctx, message)
            # Auto-clear after 2 seconds
            GLib.timeout_add(2000, lambda: self.statusbar.pop(ctx))

    def _on_key_press(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle keyboard shortcuts."""
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        shift = event.state & Gdk.ModifierType.SHIFT_MASK

        # Ctrl+Shift+P - Command Palette
        if ctrl and shift and event.keyval in (Gdk.KEY_p, Gdk.KEY_P):
            self._show_command_palette()
            return True

        # Ctrl shortcuts
        if ctrl:
            if event.keyval == Gdk.KEY_s:
                self._save()
                return True
            elif event.keyval == Gdk.KEY_c:
                self._copy_to_clipboard()
                return True
            elif event.keyval == Gdk.KEY_z:
                self._undo()
                return True
            elif event.keyval == Gdk.KEY_y:
                self._redo()
                return True

        # Tool shortcuts (no modifier)
        tool_shortcuts = {
            Gdk.KEY_p: ToolType.PEN,
            Gdk.KEY_h: ToolType.HIGHLIGHTER,
            Gdk.KEY_l: ToolType.LINE,
            Gdk.KEY_a: ToolType.ARROW,
            Gdk.KEY_r: ToolType.RECTANGLE,
            Gdk.KEY_e: ToolType.ELLIPSE,
            Gdk.KEY_t: ToolType.TEXT,
            Gdk.KEY_b: ToolType.BLUR,
            Gdk.KEY_x: ToolType.PIXELATE,
            Gdk.KEY_m: ToolType.MEASURE,
            Gdk.KEY_n: ToolType.NUMBER,
            Gdk.KEY_i: ToolType.COLORPICKER,
            Gdk.KEY_s: ToolType.STAMP,
            Gdk.KEY_z: ToolType.ZOOM,
            Gdk.KEY_k: ToolType.CALLOUT,
            Gdk.KEY_c: ToolType.CROP,
            Gdk.KEY_v: ToolType.SELECT,
        }
        if event.keyval in tool_shortcuts:
            tool = tool_shortcuts[event.keyval]
            self._set_tool(tool)
            # Update toggle buttons if they exist
            if hasattr(self, "tool_buttons") and tool in self.tool_buttons:
                self.tool_buttons[tool].set_active(True)
            return True

        # Zoom shortcuts (no modifier)
        if event.keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self.editor_state.zoom_in()
            self._update_zoom_label()
            self.drawing_area.queue_draw()
            return True
        if event.keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self.editor_state.zoom_out()
            self._update_zoom_label()
            self.drawing_area.queue_draw()
            return True
        if event.keyval == Gdk.KEY_0:
            self.editor_state.reset_zoom()
            self._update_zoom_label()
            self.drawing_area.queue_draw()
            return True

        # Delete/Backspace to delete selected element
        if event.keyval in (Gdk.KEY_Delete, Gdk.KEY_BackSpace):
            if self.editor_state.delete_selected():
                self.statusbar.push(self.statusbar_context, "Element deleted")
                self.drawing_area.queue_draw()
                return True

        # Escape to deselect/cancel
        if event.keyval == Gdk.KEY_Escape:
            if self.editor_state.selected_index is not None:
                self.editor_state.deselect()
                self.drawing_area.queue_draw()
                return True
            self.editor_state.cancel_drawing()
            self.drawing_area.queue_draw()
            return True

        return False

    def _on_destroy(self, widget: Gtk.Widget) -> None:
        """Handle window destruction."""
        Gtk.main_quit()


class MainWindow:
    """Main application window with hotkey support."""

    def __init__(self):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK is not available")

        # Load CSS styling
        self._load_css()

        self.window = Gtk.Window(title="LikX")
        self.window.set_default_size(420, 480)
        self.window.set_border_width(24)
        self.window.set_resizable(False)
        self.window.connect("destroy", self._on_quit)

        # Center window on screen
        self.window.set_position(Gtk.WindowPosition.CENTER)

        self.hotkey_manager = HotkeyManager()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window.add(main_box)

        # Header with icon and title
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header_box.set_margin_bottom(16)
        main_box.pack_start(header_box, False, False, 0)

        # Title
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>LikX</span>")
        title.get_style_context().add_class("title-label")
        header_box.pack_start(title, False, False, 0)

        # Subtitle/Description
        desc = Gtk.Label(label="Capture • Annotate • Share")
        desc.get_style_context().add_class("desc-label")
        header_box.pack_start(desc, False, False, 0)

        # Capture buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        button_box.set_margin_top(8)
        main_box.pack_start(button_box, True, False, 0)

        fullscreen_btn = self._create_big_button(
            "📷  Capture Fullscreen",
            "Capture your entire screen\nCtrl+Shift+F",
            self._on_fullscreen,
            "fullscreen",
        )
        button_box.pack_start(fullscreen_btn, False, False, 0)

        region_btn = self._create_big_button(
            "⬚  Capture Region",
            "Select and capture a screen region\nCtrl+Shift+R",
            self._on_region,
            "region",
        )
        button_box.pack_start(region_btn, False, False, 0)

        window_btn = self._create_big_button(
            "🪟  Capture Window",
            "Capture the active window\nCtrl+Shift+W",
            self._on_window,
            "window",
        )
        button_box.pack_start(window_btn, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        main_box.pack_start(spacer, True, True, 0)

        # Bottom buttons
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_box.set_margin_top(16)
        main_box.pack_start(bottom_box, False, False, 0)

        settings_btn = Gtk.Button(label="⚙️ Settings")
        settings_btn.get_style_context().add_class("action-button")
        settings_btn.connect("clicked", self._on_settings)
        bottom_box.pack_start(settings_btn, True, True, 0)

        about_btn = Gtk.Button(label="ℹ️ About")
        about_btn.get_style_context().add_class("action-button")
        about_btn.connect("clicked", self._on_about)
        bottom_box.pack_start(about_btn, True, True, 0)

        self.window.show_all()

        # Register hotkeys
        self._register_global_hotkeys()

    def _load_css(self) -> None:
        """Load custom CSS styling."""
        css_provider = Gtk.CssProvider()
        css_path = Path(__file__).parent.parent / "resources" / "style.css"

        if css_path.exists():
            try:
                css_provider.load_from_path(str(css_path))
                screen = Gdk.Screen.get_default()
                Gtk.StyleContext.add_provider_for_screen(
                    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"Warning: Could not load CSS: {e}")

    def _create_big_button(
        self, text: str, tooltip: str, callback, style_class: str = ""
    ) -> Gtk.Button:
        """Create a large styled button."""
        button = Gtk.Button(label=text)
        button.set_tooltip_text(tooltip)
        button.set_size_request(-1, 64)
        button.get_style_context().add_class("capture-button")
        if style_class:
            button.get_style_context().add_class(style_class)
        button.connect("clicked", callback)
        return button

    def _on_history(self, button: Gtk.Button) -> None:
        """Open screenshot folder in file manager."""
        import subprocess

        cfg = config.load_config()
        folder = Path(
            cfg.get("save_directory", str(Path.home() / "Pictures" / "Screenshots"))
        )
        folder.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error",
                secondary_text=f"Could not open folder: {e}",
            )
            dialog.run()
            dialog.destroy()

    def _register_global_hotkeys(self) -> None:
        """Register global keyboard shortcuts."""
        cfg = config.load_config()
        import sys
        import os

        script_path = os.path.abspath(sys.argv[0])

        self.hotkey_manager.register_hotkey(
            cfg.get("hotkey_fullscreen", "<Control><Shift>F"),
            self._on_fullscreen,
            f"python3 {script_path} --fullscreen --no-edit",
        )
        self.hotkey_manager.register_hotkey(
            cfg.get("hotkey_region", "<Control><Shift>R"),
            self._on_region,
            f"python3 {script_path} --region --no-edit",
        )
        self.hotkey_manager.register_hotkey(
            cfg.get("hotkey_window", "<Control><Shift>W"),
            self._on_window,
            f"python3 {script_path} --window --no-edit",
        )

    def _on_fullscreen(self, button: Optional[Gtk.Button] = None) -> None:
        """Handle fullscreen capture button click."""
        self.window.iconify()
        GLib.timeout_add(300, self._capture_fullscreen)

    def _capture_fullscreen(self) -> bool:
        """Capture fullscreen after delay."""
        result = capture(CaptureMode.FULLSCREEN)
        if result.success:
            cfg = config.load_config()
            if cfg.get("editor_enabled", True):
                EditorWindow(result)
            else:
                filepath = save_capture(result)
                if filepath.success and cfg.get("show_notification", True):
                    show_screenshot_saved(str(filepath.filepath))
        else:
            show_notification("Capture Failed", result.error, icon="dialog-error")
        self.window.deiconify()
        return False

    def _on_region(self, button: Optional[Gtk.Button] = None) -> None:
        """Handle region capture button click."""
        self.window.iconify()
        GLib.timeout_add(300, self._start_region_selection)

    def _start_region_selection(self) -> bool:
        """Start region selection."""
        try:
            RegionSelector(self._on_region_selected)
        except Exception as e:
            show_notification("Region Selection Failed", str(e), icon="dialog-error")
            self.window.deiconify()
        return False

    def _on_region_selected(self, x: int, y: int, width: int, height: int) -> None:
        """Handle region selection completion."""
        result = capture(CaptureMode.REGION, region=(x, y, width, height))
        if result.success:
            cfg = config.load_config()
            if cfg.get("editor_enabled", True):
                EditorWindow(result)
            else:
                filepath = save_capture(result)
                if filepath.success and cfg.get("show_notification", True):
                    show_screenshot_saved(str(filepath.filepath))
        else:
            show_notification("Capture Failed", result.error, icon="dialog-error")
        self.window.deiconify()

    def _on_window(self, button: Optional[Gtk.Button] = None) -> None:
        """Handle window capture button click."""
        self.window.iconify()
        GLib.timeout_add(300, self._capture_window)

    def _capture_window(self) -> bool:
        """Capture active window."""
        result = capture(CaptureMode.WINDOW)
        if result.success:
            cfg = config.load_config()
            if cfg.get("editor_enabled", True):
                EditorWindow(result)
            else:
                filepath = save_capture(result)
                if filepath.success and cfg.get("show_notification", True):
                    show_screenshot_saved(str(filepath.filepath))
        else:
            show_notification("Capture Failed", result.error, icon="dialog-error")
        self.window.deiconify()
        return False

    def _on_settings(self, button: Gtk.Button) -> None:
        """Handle settings button click."""
        SettingsDialog(self.window)

    def _on_about(self, button: Gtk.Button) -> None:
        """Show about dialog."""
        from . import __version__

        dialog = Gtk.AboutDialog(transient_for=self.window)
        dialog.set_program_name("LikX")
        dialog.set_version(__version__)
        dialog.set_comments(
            "A powerful screenshot capture and annotation tool for Linux"
        )
        dialog.set_website("https://github.com/AreteDriver/LikX")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_authors(["LikX Contributors"])

        from .capture import detect_display_server

        display = detect_display_server()
        dialog.set_system_information(f"Display Server: {display.value}")

        dialog.run()
        dialog.destroy()

    def _on_quit(self, widget: Gtk.Widget) -> None:
        """Handle application quit."""
        self.hotkey_manager.unregister_all()
        Gtk.main_quit()

    def run(self) -> None:
        """Run the main application loop."""
        Gtk.main()


class SettingsDialog:
    """Settings dialog window with all options."""

    def __init__(self, parent: Gtk.Window):
        self.dialog = Gtk.Dialog(
            title="Settings", parent=parent, flags=Gtk.DialogFlags.MODAL
        )
        self.dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            "Reset to Defaults",
            Gtk.ResponseType.REJECT,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        self.dialog.set_default_size(500, 400)

        content = self.dialog.get_content_area()
        content.set_border_width(10)
        content.set_spacing(10)

        self.cfg = config.load_config()

        # Create notebook for tabs
        notebook = Gtk.Notebook()
        content.pack_start(notebook, True, True, 0)

        # General settings tab
        general_box = self._create_general_settings()
        notebook.append_page(general_box, Gtk.Label(label="General"))

        # Capture settings tab
        capture_box = self._create_capture_settings()
        notebook.append_page(capture_box, Gtk.Label(label="Capture"))

        # Upload settings tab
        upload_box = self._create_upload_settings()
        notebook.append_page(upload_box, Gtk.Label(label="Upload"))

        self.dialog.show_all()

        response = self.dialog.run()
        if response == Gtk.ResponseType.OK:
            self._save_settings()
        elif response == Gtk.ResponseType.REJECT:
            self._reset_to_defaults()

        self.dialog.destroy()

    def _create_general_settings(self) -> Gtk.Box:
        """Create general settings tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)

        # Save directory
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dir_label = Gtk.Label(label="Save directory:", xalign=0)
        dir_label.set_size_request(150, -1)
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_text(str(self.cfg.get("save_directory", "")))
        dir_button = Gtk.Button(label="Browse...")
        dir_button.connect("clicked", self._browse_directory)
        dir_box.pack_start(dir_label, False, False, 0)
        dir_box.pack_start(self.dir_entry, True, True, 0)
        dir_box.pack_start(dir_button, False, False, 0)
        box.pack_start(dir_box, False, False, 0)

        # Default format
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        format_label = Gtk.Label(label="Default format:", xalign=0)
        format_label.set_size_request(150, -1)
        self.format_combo = Gtk.ComboBoxText()
        for fmt in ["png", "jpg", "bmp", "gif"]:
            self.format_combo.append_text(fmt)
        current_fmt = self.cfg.get("default_format", "png")
        self.format_combo.set_active(["png", "jpg", "bmp", "gif"].index(current_fmt))
        format_box.pack_start(format_label, False, False, 0)
        format_box.pack_start(self.format_combo, False, False, 0)
        box.pack_start(format_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 5)

        # Checkboxes
        self.auto_save_check = Gtk.CheckButton(
            label="Auto-save screenshots (skip editor)"
        )
        self.auto_save_check.set_active(self.cfg.get("auto_save", False))
        box.pack_start(self.auto_save_check, False, False, 0)

        self.clipboard_check = Gtk.CheckButton(label="Copy to clipboard automatically")
        self.clipboard_check.set_active(self.cfg.get("copy_to_clipboard", True))
        box.pack_start(self.clipboard_check, False, False, 0)

        self.notification_check = Gtk.CheckButton(label="Show desktop notifications")
        self.notification_check.set_active(self.cfg.get("show_notification", True))
        box.pack_start(self.notification_check, False, False, 0)

        self.editor_check = Gtk.CheckButton(label="Open editor after capture")
        self.editor_check.set_active(self.cfg.get("editor_enabled", True))
        box.pack_start(self.editor_check, False, False, 0)

        return box

    def _create_capture_settings(self) -> Gtk.Box:
        """Create capture settings tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)

        # Delay
        delay_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        delay_label = Gtk.Label(label="Capture delay (seconds):", xalign=0)
        delay_label.set_size_request(200, -1)
        self.delay_spin = Gtk.SpinButton()
        self.delay_spin.set_range(0, 10)
        self.delay_spin.set_value(self.cfg.get("delay_seconds", 0))
        self.delay_spin.set_increments(1, 1)
        delay_box.pack_start(delay_label, False, False, 0)
        delay_box.pack_start(self.delay_spin, False, False, 0)
        box.pack_start(delay_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 5)

        self.cursor_check = Gtk.CheckButton(label="Include mouse cursor in screenshots")
        self.cursor_check.set_active(self.cfg.get("include_cursor", False))
        box.pack_start(self.cursor_check, False, False, 0)

        # Hotkeys info
        box.pack_start(Gtk.Separator(), False, False, 5)
        hotkey_label = Gtk.Label(xalign=0)
        hotkey_label.set_markup(
            "<b>Global Hotkeys:</b>\n\n"
            + f"Fullscreen: {self.cfg.get('hotkey_fullscreen', 'Ctrl+Shift+F')}\n"
            + f"Region: {self.cfg.get('hotkey_region', 'Ctrl+Shift+R')}\n"
            + f"Window: {self.cfg.get('hotkey_window', 'Ctrl+Shift+W')}\n\n"
            + "<i>(Hotkeys work on GNOME desktop)</i>"
        )
        box.pack_start(hotkey_label, False, False, 0)

        return box

    def _create_upload_settings(self) -> Gtk.Box:
        """Create upload settings tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)

        # Upload service
        service_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        service_label = Gtk.Label(label="Upload service:", xalign=0)
        service_label.set_size_request(150, -1)
        self.service_combo = Gtk.ComboBoxText()
        for service in ["none", "imgur"]:
            self.service_combo.append_text(service)
        current_service = self.cfg.get("upload_service", "imgur")
        self.service_combo.set_active(["none", "imgur"].index(current_service))
        service_box.pack_start(service_label, False, False, 0)
        service_box.pack_start(self.service_combo, False, False, 0)
        box.pack_start(service_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 5)

        self.auto_upload_check = Gtk.CheckButton(
            label="Automatically upload after save"
        )
        self.auto_upload_check.set_active(self.cfg.get("auto_upload", False))
        box.pack_start(self.auto_upload_check, False, False, 0)

        # Info
        info_label = Gtk.Label(xalign=0)
        info_label.set_markup(
            "<b>About Upload Services:</b>\n\n"
            + "• <b>Imgur</b>: Free anonymous image hosting\n"
            + "  URL is copied to clipboard automatically\n\n"
            + "<i>Requires: curl</i>"
        )
        info_label.set_line_wrap(True)
        box.pack_start(info_label, False, False, 0)

        return box

    def _browse_directory(self, button: Gtk.Button) -> None:
        """Browse for save directory."""
        dialog = Gtk.FileChooserDialog(
            title="Select Save Directory",
            parent=self.dialog,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        current_dir = Path(self.dir_entry.get_text()).expanduser()
        if current_dir.exists():
            dialog.set_current_folder(str(current_dir))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.dir_entry.set_text(dialog.get_filename())

        dialog.destroy()

    def _save_settings(self) -> None:
        """Save the settings."""
        self.cfg["save_directory"] = self.dir_entry.get_text()
        self.cfg["default_format"] = self.format_combo.get_active_text() or "png"
        self.cfg["auto_save"] = self.auto_save_check.get_active()
        self.cfg["copy_to_clipboard"] = self.clipboard_check.get_active()
        self.cfg["show_notification"] = self.notification_check.get_active()
        self.cfg["editor_enabled"] = self.editor_check.get_active()
        self.cfg["delay_seconds"] = int(self.delay_spin.get_value())
        self.cfg["include_cursor"] = self.cursor_check.get_active()
        self.cfg["upload_service"] = self.service_combo.get_active_text() or "imgur"
        self.cfg["auto_upload"] = self.auto_upload_check.get_active()

        if config.save_config(self.cfg):
            show_notification("Settings Saved", "Your preferences have been saved")

    def _reset_to_defaults(self) -> None:
        """Reset settings to defaults."""
        if config.reset_config():
            show_notification("Settings Reset", "All settings reset to defaults")


def run_app() -> None:
    """Run the LikX application."""
    if not GTK_AVAILABLE:
        print("Error: GTK 3.0 is required but not available.")
        print("Please install GTK 3.0 and PyGObject:")
        print("  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        sys.exit(1)

    app = MainWindow()
    app.run()


# ==========================================
# PREMIUM FEATURES INTEGRATION
# ==========================================

# Enhance EditorWindow with premium features
_EditorWindow_init_original = EditorWindow.__init__


def _EditorWindow_init_enhanced(self, result):
    """Enhanced init with premium features."""
    _EditorWindow_init_original(self, result)

    # Initialize premium features
    self.ocr_engine = OCREngine()
    self.history_manager = HistoryManager()

    # Find the spacer in the toolbar to insert before it
    toolbar_children = self.ribbon.get_children()
    spacer_index = len(toolbar_children) - 2  # Before Clear button

    # Add separator
    sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    sep.get_style_context().add_class("toolbar-separator")
    self.ribbon.pack_start(sep, False, False, 0)
    self.ribbon.reorder_child(sep, spacer_index)

    # === OCR Button ===
    ocr_btn = Gtk.Button(label="OCR")
    ocr_btn.set_tooltip_text("Extract text from image (Tesseract)")
    ocr_btn.get_style_context().add_class("tool-button")
    ocr_btn.connect("clicked", lambda b: self._extract_text())
    self.ribbon.pack_start(ocr_btn, False, False, 0)
    self.ribbon.reorder_child(ocr_btn, spacer_index + 1)

    # === Pin Button ===
    pin_btn = Gtk.Button(label="📌")
    pin_btn.set_tooltip_text("Pin to desktop (always on top)")
    pin_btn.get_style_context().add_class("tool-button")
    pin_btn.connect("clicked", lambda b: self._pin_to_desktop())
    self.ribbon.pack_start(pin_btn, False, False, 0)
    self.ribbon.reorder_child(pin_btn, spacer_index + 2)

    # === Effects Popover Button ===
    effects_btn = Gtk.Button(label="FX ▾")
    effects_btn.set_tooltip_text("Image Effects")
    effects_btn.get_style_context().add_class("tool-button")

    effects_popover = Gtk.Popover()
    effects_popover.set_relative_to(effects_btn)
    effects_grid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    effects_grid.set_margin_start(8)
    effects_grid.set_margin_end(8)
    effects_grid.set_margin_top(8)
    effects_grid.set_margin_bottom(8)

    effects_items = [
        ("✨ Drop Shadow", self._apply_shadow),
        ("🖼 Add Border", self._apply_border),
        ("🎨 Background", self._apply_background),
        ("◐ Round Corners", self._apply_round_corners),
        ("☀ Adjust Brightness/Contrast", self._show_adjust_dialog),
        ("🔲 Grayscale", self._apply_grayscale),
        ("🔄 Invert Colors", self._apply_invert),
    ]
    for label, callback in effects_items:
        row = Gtk.Button(label=label)
        row.set_relief(Gtk.ReliefStyle.NONE)
        row.connect(
            "clicked", lambda b, cb=callback, p=effects_popover: (cb(), p.popdown())
        )
        effects_grid.pack_start(row, False, False, 0)

    effects_popover.add(effects_grid)
    effects_btn.connect("clicked", lambda b: effects_popover.show_all())
    self.ribbon.pack_start(effects_btn, False, False, 0)
    self.ribbon.reorder_child(effects_btn, spacer_index + 3)

    self.window.show_all()


# Add premium methods to EditorWindow
def _extract_text(self):
    """Extract text using OCR."""
    if not self.ocr_engine.available:
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Tesseract OCR not installed",
            secondary_text="Install with: sudo apt install tesseract-ocr\n\nThen restart the application.",
        )
        dialog.run()
        dialog.destroy()
        return

    self.statusbar.push(self.statusbar_context, "Extracting text...")

    success, text, error = self.ocr_engine.extract_text(self.result.pixbuf)

    if success and text:
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Extracted Text ({len(text)} characters)",
        )
        dialog.add_buttons("📋 Copy & Close", 1, "Close", Gtk.ResponseType.CLOSE)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(500, 300)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_border_width(10)
        text_view.get_buffer().set_text(text)

        scrolled.add(text_view)
        dialog.get_content_area().pack_start(scrolled, True, True, 10)
        dialog.show_all()

        response = dialog.run()
        if response == 1:
            if self.ocr_engine.copy_text_to_clipboard(text):
                show_notification(
                    "Text Copied", f"Copied {len(text)} characters to clipboard"
                )
            else:
                show_notification(
                    "Copy Failed", "Could not copy to clipboard", icon="dialog-warning"
                )

        dialog.destroy()
        self.statusbar.push(self.statusbar_context, f"Extracted {len(text)} characters")
    else:
        self.statusbar.push(self.statusbar_context, f"OCR: {error or 'No text found'}")
        show_notification(
            "OCR Result", error or "No text found in image", icon="dialog-information"
        )


def _pin_to_desktop(self):
    """Pin screenshot to desktop."""
    try:
        import cairo

        width = self.result.pixbuf.get_width()
        height = self.result.pixbuf.get_height()

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        Gdk.cairo_set_source_pixbuf(ctx, self.result.pixbuf, 0, 0)
        ctx.paint()

        if self.editor_state.elements:
            from .editor import render_elements

            render_elements(surface, self.editor_state.elements, self.result.pixbuf)

        from gi.repository import GdkPixbuf

        data = surface.get_data()
        pinned_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            width,
            height,
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width),
        )

        PinnedWindow(pinned_pixbuf, "Pinned Screenshot")
        self.statusbar.push(self.statusbar_context, "Pinned to desktop")
        show_notification(
            "Pinned to Desktop",
            "Screenshot is now always on top. Use controls to adjust.",
        )

    except Exception as e:
        self.statusbar.push(self.statusbar_context, f"Pin failed: {e}")
        show_notification("Pin Failed", str(e), icon="dialog-error")


def _apply_shadow(self):
    """Apply shadow effect."""
    self.result.pixbuf = add_shadow(self.result.pixbuf, shadow_size=15, opacity=0.3)
    self.editor_state.set_pixbuf(self.result.pixbuf)
    self.drawing_area.set_size_request(
        self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
    )
    self.drawing_area.queue_draw()
    self.statusbar.push(self.statusbar_context, "Shadow effect applied")


def _apply_border(self):
    """Apply border effect."""
    dialog = Gtk.ColorChooserDialog(
        title="Choose Border Color", transient_for=self.window
    )
    dialog.set_rgba(Gdk.RGBA(0, 0, 0, 1))
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        rgba = dialog.get_rgba()
        color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        self.result.pixbuf = add_border(self.result.pixbuf, border_width=8, color=color)
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.set_size_request(
            self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
        )
        self.drawing_area.queue_draw()
        self.statusbar.push(self.statusbar_context, "Border added")

    dialog.destroy()


def _apply_background(self):
    """Apply background effect."""
    dialog = Gtk.ColorChooserDialog(
        title="Choose Background Color", transient_for=self.window
    )
    dialog.set_rgba(Gdk.RGBA(1, 1, 1, 1))
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        rgba = dialog.get_rgba()
        color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        self.result.pixbuf = add_background(
            self.result.pixbuf, bg_color=color, padding=25
        )
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.set_size_request(
            self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
        )
        self.drawing_area.queue_draw()
        self.statusbar.push(self.statusbar_context, "Background added")

    dialog.destroy()


def _apply_round_corners(self):
    """Apply rounded corners."""
    self.result.pixbuf = round_corners(self.result.pixbuf, radius=20)
    self.editor_state.set_pixbuf(self.result.pixbuf)
    self.drawing_area.queue_draw()
    self.statusbar.push(self.statusbar_context, "Corners rounded")


# Inject methods into EditorWindow
EditorWindow.__init__ = _EditorWindow_init_enhanced
EditorWindow._extract_text = _extract_text
EditorWindow._pin_to_desktop = _pin_to_desktop
EditorWindow._apply_shadow = _apply_shadow
EditorWindow._apply_border = _apply_border
EditorWindow._apply_background = _apply_background
EditorWindow._apply_round_corners = _apply_round_corners


# Enhance MainWindow
_MainWindow_init_original = MainWindow.__init__


def _MainWindow_init_enhanced(self):
    """Enhanced main window."""
    _MainWindow_init_original(self)

    # Add quick actions button
    children = self.window.get_children()[0].get_children()
    button_box = children[2]  # The button box
    quick_btn = self._create_big_button(
        "⚡ Quick Actions", "Common screenshot workflows", self._on_quick_actions
    )
    button_box.pack_start(quick_btn, False, False, 0)
    button_box.reorder_child(quick_btn, 3)

    self.window.show_all()


def _on_history(self, button):
    """Open screenshot folder in file manager."""
    import subprocess

    cfg = config.load_config()
    folder = Path(
        cfg.get("save_directory", str(Path.home() / "Pictures" / "Screenshots"))
    )
    folder.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.Popen(["xdg-open", str(folder)])
    except Exception as e:
        show_notification("Error", f"Could not open folder: {e}", icon="dialog-error")


def _on_quick_actions(self, button):
    """Show quick actions dialog."""
    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.CLOSE,
        text="⚡ Quick Actions",
    )
    dialog.format_secondary_text(
        "Features:\n\n"
        + "• 📝 OCR: Extract text from screenshots\n"
        + "• 📌 Pin: Keep screenshots always on top\n"
        + "• ✨ Effects: Add shadows, borders, backgrounds\n"
        + "• 🔍 Blur/Pixelate: Privacy protection\n"
        + "• ☁️ Upload: Share via Imgur\n\n"
        + "All features available in the editor!"
    )
    dialog.run()
    dialog.destroy()


def _show_adjust_dialog(self):
    """Show brightness/contrast adjustment dialog."""
    dialog = Gtk.Dialog(
        title="Adjust Image",
        transient_for=self.window,
        flags=Gtk.DialogFlags.MODAL,
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL,
        Gtk.ResponseType.CANCEL,
        Gtk.STOCK_APPLY,
        Gtk.ResponseType.OK,
    )
    dialog.set_default_size(350, 200)

    content = dialog.get_content_area()
    content.set_border_width(15)
    content.set_spacing(15)

    # Brightness slider
    brightness_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    brightness_label = Gtk.Label(label="Brightness:")
    brightness_label.set_size_request(100, -1)
    brightness_label.set_xalign(0)
    brightness_scale = Gtk.Scale.new_with_range(
        Gtk.Orientation.HORIZONTAL, -100, 100, 5
    )
    brightness_scale.set_value(0)
    brightness_scale.set_hexpand(True)
    brightness_box.pack_start(brightness_label, False, False, 0)
    brightness_box.pack_start(brightness_scale, True, True, 0)
    content.pack_start(brightness_box, False, False, 0)

    # Contrast slider
    contrast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    contrast_label = Gtk.Label(label="Contrast:")
    contrast_label.set_size_request(100, -1)
    contrast_label.set_xalign(0)
    contrast_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -100, 100, 5)
    contrast_scale.set_value(0)
    contrast_scale.set_hexpand(True)
    contrast_box.pack_start(contrast_label, False, False, 0)
    contrast_box.pack_start(contrast_scale, True, True, 0)
    content.pack_start(contrast_box, False, False, 0)

    dialog.show_all()
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        brightness = brightness_scale.get_value() / 100.0
        contrast = contrast_scale.get_value() / 100.0

        if brightness != 0 or contrast != 0:
            self.result.pixbuf = adjust_brightness_contrast(
                self.result.pixbuf, brightness, contrast
            )
            self.editor_state.set_pixbuf(self.result.pixbuf)
            self.drawing_area.queue_draw()
            self.statusbar.push(
                self.statusbar_context,
                f"Adjusted: brightness={int(brightness * 100)}%, contrast={int(contrast * 100)}%",
            )

    dialog.destroy()


def _apply_grayscale(self):
    """Convert image to grayscale."""
    self.result.pixbuf = grayscale(self.result.pixbuf)
    self.editor_state.set_pixbuf(self.result.pixbuf)
    self.drawing_area.queue_draw()
    self.statusbar.push(self.statusbar_context, "Converted to grayscale")


def _apply_invert(self):
    """Invert image colors."""
    self.result.pixbuf = invert_colors(self.result.pixbuf)
    self.editor_state.set_pixbuf(self.result.pixbuf)
    self.drawing_area.queue_draw()
    self.statusbar.push(self.statusbar_context, "Colors inverted")


# Inject adjustment methods
EditorWindow._show_adjust_dialog = _show_adjust_dialog
EditorWindow._apply_grayscale = _apply_grayscale
EditorWindow._apply_invert = _apply_invert


# Inject enhanced methods
MainWindow.__init__ = _MainWindow_init_enhanced
MainWindow._on_history = _on_history
MainWindow._on_quick_actions = _on_quick_actions
