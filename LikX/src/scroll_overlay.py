"""Scroll capture overlay - progress indicator during capture."""

from typing import Callable, Optional

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from .i18n import _


class ScrollCaptureOverlay:
    """Floating overlay showing scroll capture progress.

    Displays:
    - Frame counter
    - Estimated total height
    - Stop button
    - Visual border around capture region
    """

    def __init__(
        self,
        on_stop: Callable[[], None],
        region: Optional[tuple] = None,  # (x, y, width, height)
    ):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available")

        self.on_stop = on_stop
        self.region = region
        self.frame_count = 0
        self.estimated_height = 0
        self.border_window: Optional[Gtk.Window] = None

        # Create floating window
        self.window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.window.set_decorated(False)
        self.window.set_keep_above(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        # Make window semi-transparent
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        self.window.set_app_paintable(True)

        # Load CSS
        self._load_css()

        # Create layout
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_start(16)
        hbox.set_margin_end(16)
        hbox.set_margin_top(10)
        hbox.set_margin_bottom(10)
        hbox.get_style_context().add_class("scroll-overlay")
        self.window.add(hbox)

        # Scroll icon
        icon_label = Gtk.Label(label="📜")
        icon_label.get_style_context().add_class("scroll-icon")
        hbox.pack_start(icon_label, False, False, 0)

        # Info box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hbox.pack_start(info_box, False, False, 0)

        # Frame counter
        self.frame_label = Gtk.Label(label=_("Frames:") + " 0")
        self.frame_label.set_xalign(0)
        self.frame_label.get_style_context().add_class("scroll-info")
        info_box.pack_start(self.frame_label, False, False, 0)

        # Height estimate
        self.height_label = Gtk.Label(label=_("Height:") + " 0px")
        self.height_label.set_xalign(0)
        self.height_label.get_style_context().add_class("scroll-info-dim")
        info_box.pack_start(self.height_label, False, False, 0)

        # Stop button
        stop_btn = Gtk.Button(label=_("Stop"))
        stop_btn.get_style_context().add_class("scroll-stop")
        stop_btn.connect("clicked", self._on_stop_clicked)
        hbox.pack_start(stop_btn, False, False, 0)

        # Position at top-center of screen
        self.window.show_all()

        # Get actual window size after show
        self.window.realize()
        allocation = self.window.get_allocation()
        screen = Gdk.Screen.get_default()
        x = (screen.get_width() - allocation.width) // 2
        self.window.move(x, 20)

        # Create region border if provided
        if region:
            self._create_region_border(region)

    def _load_css(self) -> None:
        """Load scroll overlay CSS."""
        css = b"""
        .scroll-overlay {
            background: rgba(30, 60, 90, 0.92);
            border-radius: 12px;
            border: 2px solid rgba(100, 180, 255, 0.8);
        }
        .scroll-icon {
            font-size: 28px;
        }
        .scroll-info {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        }
        .scroll-info-dim {
            color: #aaccff;
            font-size: 12px;
        }
        .scroll-stop {
            background: #3366aa;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        .scroll-stop:hover {
            background: #4488cc;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _create_region_border(self, region: tuple) -> None:
        """Create a transparent window with border around capture region."""
        x, y, width, height = region

        self.border_window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.border_window.set_decorated(False)
        self.border_window.set_keep_above(True)

        screen = self.border_window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.border_window.set_visual(visual)
        self.border_window.set_app_paintable(True)

        # Size to fit around region with border
        border_width = 3
        self.border_window.set_default_size(
            width + border_width * 2, height + border_width * 2
        )
        self.border_window.move(x - border_width, y - border_width)

        # Store dimensions for drawing
        self._border_width = border_width
        self._region_width = width
        self._region_height = height

        # Draw border
        drawing_area = Gtk.DrawingArea()
        drawing_area.connect("draw", self._draw_border)
        self.border_window.add(drawing_area)

        self.border_window.show_all()

    def _draw_border(self, widget, cr) -> bool:
        """Draw capture region border."""
        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        # Blue dashed border
        cr.set_source_rgba(0.4, 0.7, 1.0, 0.9)
        cr.set_line_width(self._border_width)
        cr.set_dash([10, 5])
        cr.rectangle(
            self._border_width / 2,
            self._border_width / 2,
            self._region_width + self._border_width,
            self._region_height + self._border_width,
        )
        cr.stroke()

        return True

    def update_progress(self, frame_count: int, estimated_height: int) -> None:
        """Update the progress display.

        Args:
            frame_count: Number of frames captured
            estimated_height: Estimated total image height in pixels
        """
        self.frame_count = frame_count
        self.estimated_height = estimated_height

        self.frame_label.set_text(_("Frames:") + f" {frame_count}")

        if estimated_height >= 1000:
            height_str = f"{estimated_height / 1000:.1f}k px"
        else:
            height_str = f"{estimated_height} px"
        self.height_label.set_text(_("Height:") + f" {height_str}")

    def _on_stop_clicked(self, button) -> None:
        """Handle stop button click."""
        self.on_stop()

    def destroy(self) -> None:
        """Clean up overlay."""
        if self.border_window:
            self.border_window.destroy()

        self.window.destroy()
