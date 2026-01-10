"""Recording overlay - minimal stop button during GIF capture."""

from typing import Callable, Optional

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config


class RecordingOverlay:
    """Minimal floating overlay with stop button and timer.

    Appears during recording with:
    - Red pulsing recording indicator
    - Elapsed time display
    - Stop button
    - Optional region border highlight
    """

    def __init__(
        self,
        on_stop: Callable[[], None],
        region: Optional[tuple] = None,  # (x, y, width, height) for border highlight
    ):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available")

        self.on_stop = on_stop
        self.region = region
        self.elapsed_seconds = 0
        self.timer_id: Optional[int] = None
        self.pulse_id: Optional[int] = None
        self.pulse_state = True
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
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_start(12)
        hbox.set_margin_end(12)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        hbox.get_style_context().add_class("recording-overlay")
        self.window.add(hbox)

        # Recording indicator (pulsing red dot)
        self.indicator = Gtk.Label(label="REC")
        self.indicator.get_style_context().add_class("recording-indicator")
        hbox.pack_start(self.indicator, False, False, 0)

        # Timer label
        self.timer_label = Gtk.Label(label="00:00")
        self.timer_label.get_style_context().add_class("recording-timer")
        hbox.pack_start(self.timer_label, False, False, 0)

        # Stop button
        stop_btn = Gtk.Button(label="Stop")
        stop_btn.get_style_context().add_class("recording-stop")
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

        # Start timer
        self.timer_id = GLib.timeout_add(1000, self._update_timer)

        # Start indicator pulse
        self.pulse_id = GLib.timeout_add(500, self._pulse_indicator)

        # If region provided, create border overlay
        if region:
            self._create_region_border(region)

    def _load_css(self) -> None:
        """Load recording overlay CSS."""
        css = b"""
        .recording-overlay {
            background: rgba(40, 40, 40, 0.9);
            border-radius: 20px;
            border: 2px solid rgba(255, 60, 60, 0.8);
        }
        .recording-indicator {
            color: #ff4444;
            font-size: 14px;
            font-weight: bold;
        }
        .recording-indicator-dim {
            color: #aa2222;
        }
        .recording-timer {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            font-family: monospace;
            min-width: 50px;
        }
        .recording-stop {
            background: #cc3333;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-weight: bold;
        }
        .recording-stop:hover {
            background: #ff4444;
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
        """Create a transparent window with border around recording region."""
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

        # Draw border
        drawing_area = Gtk.DrawingArea()
        drawing_area.connect(
            "draw", self._draw_border, width, height, border_width
        )
        self.border_window.add(drawing_area)

        self.border_window.show_all()

    def _draw_border(
        self, widget, cr, width: int, height: int, border_width: int
    ) -> bool:
        """Draw recording border around region."""
        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        # Red dashed border
        cr.set_source_rgba(1, 0.2, 0.2, 0.9)
        cr.set_line_width(border_width)
        cr.set_dash([8, 4])
        cr.rectangle(
            border_width / 2,
            border_width / 2,
            width + border_width,
            height + border_width,
        )
        cr.stroke()

        return True

    def _update_timer(self) -> bool:
        """Update elapsed time display."""
        self.elapsed_seconds += 1
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        self.timer_label.set_text(f"{minutes:02d}:{seconds:02d}")

        # Check max duration safety limit
        cfg = config.load_config()
        max_duration = cfg.get("gif_max_duration", 60)

        if self.elapsed_seconds >= max_duration:
            self._on_stop_clicked(None)
            return False

        return True

    def _pulse_indicator(self) -> bool:
        """Pulse recording indicator."""
        ctx = self.indicator.get_style_context()
        if self.pulse_state:
            ctx.add_class("recording-indicator-dim")
        else:
            ctx.remove_class("recording-indicator-dim")
        self.pulse_state = not self.pulse_state
        return True

    def _on_stop_clicked(self, button) -> None:
        """Handle stop button click."""
        self.destroy()
        self.on_stop()

    def destroy(self) -> None:
        """Clean up overlay."""
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        if self.pulse_id:
            GLib.source_remove(self.pulse_id)
            self.pulse_id = None

        if self.border_window:
            self.border_window.destroy()

        self.window.destroy()
