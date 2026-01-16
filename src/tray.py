"""System tray integration for LikX using AppIndicator3."""

from pathlib import Path
from typing import Callable, Optional

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

# Try AppIndicator3 first (Ubuntu standard)
APPINDICATOR_AVAILABLE = False
AppIndicator3 = None

if GTK_AVAILABLE:
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3

        APPINDICATOR_AVAILABLE = True
    except (ValueError, ImportError):
        # Fall back to AyatanaAppIndicator3 (newer systems)
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3

            APPINDICATOR_AVAILABLE = True
        except (ValueError, ImportError):
            pass

from .i18n import _


class SystemTray:
    """System tray icon with menu for LikX."""

    def __init__(
        self,
        on_show_window: Callable[[], None],
        on_fullscreen: Callable[[], None],
        on_region: Callable[[], None],
        on_window: Callable[[], None],
        on_quit: Callable[[], None],
        get_queue_count: Optional[Callable[[], int]] = None,
        on_edit_queue: Optional[Callable[[], None]] = None,
    ):
        """Initialize system tray.

        Args:
            on_show_window: Callback to show/hide main window.
            on_fullscreen: Callback for fullscreen capture.
            on_region: Callback for region capture.
            on_window: Callback for window capture.
            on_quit: Callback to quit application.
            get_queue_count: Optional callback to get queue count.
            on_edit_queue: Optional callback to edit queue.
        """
        if not APPINDICATOR_AVAILABLE:
            raise RuntimeError("AppIndicator3 not available")

        self._on_show_window = on_show_window
        self._on_fullscreen = on_fullscreen
        self._on_region = on_region
        self._on_window = on_window
        self._on_quit = on_quit
        self._get_queue_count = get_queue_count
        self._on_edit_queue = on_edit_queue

        self._indicator = None
        self._menu = None
        self._queue_item = None
        self._show_item = None
        self._window_visible = True

        self._create_indicator()

    def _create_indicator(self) -> None:
        """Create the AppIndicator."""
        icon_path = self._get_icon_path()

        self._indicator = AppIndicator3.Indicator.new(
            "likx",
            icon_path or "camera-photo",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_title("LikX Screenshot Tool")

        # Create menu
        self._menu = self._create_menu()
        self._indicator.set_menu(self._menu)

    def _get_icon_path(self) -> Optional[str]:
        """Get path to tray icon."""
        locations = [
            Path(__file__).parent.parent / "resources" / "likx-tray.png",
            Path(__file__).parent.parent / "resources" / "likx.png",
            Path(__file__).parent.parent / "resources" / "icon.png",
            Path("/usr/share/icons/hicolor/48x48/apps/likx.png"),
            Path("/usr/share/pixmaps/likx.png"),
        ]
        for loc in locations:
            if loc.exists():
                return str(loc)
        return None

    def _create_menu(self) -> Gtk.Menu:
        """Create the tray menu."""
        menu = Gtk.Menu()

        # Show/Hide window
        self._show_item = Gtk.MenuItem(label=_("Hide LikX"))
        self._show_item.connect("activate", lambda _: self._on_show_window())
        menu.append(self._show_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Capture options
        fullscreen_item = Gtk.MenuItem(label=_("Fullscreen Capture"))
        fullscreen_item.connect("activate", lambda _: self._on_fullscreen())
        menu.append(fullscreen_item)

        region_item = Gtk.MenuItem(label=_("Region Capture"))
        region_item.connect("activate", lambda _: self._on_region())
        menu.append(region_item)

        window_item = Gtk.MenuItem(label=_("Window Capture"))
        window_item.connect("activate", lambda _: self._on_window())
        menu.append(window_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Queue status (if queue functions provided)
        if self._get_queue_count and self._on_edit_queue:
            self._queue_item = Gtk.MenuItem(label=_("Queue: 0 captures"))
            self._queue_item.connect("activate", lambda _: self._on_edit_queue())
            self._queue_item.set_sensitive(False)
            menu.append(self._queue_item)
            menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label=_("Quit"))
        quit_item.connect("activate", lambda _: self._on_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu

    def update_queue_count(self, count: int) -> None:
        """Update queue item label."""
        if self._queue_item:
            self._queue_item.set_label(_("Queue: {} captures").format(count))
            self._queue_item.set_sensitive(count > 0)

    def update_visibility(self, window_visible: bool) -> None:
        """Update show/hide menu item based on window visibility."""
        self._window_visible = window_visible
        if self._show_item:
            if window_visible:
                self._show_item.set_label(_("Hide LikX"))
            else:
                self._show_item.set_label(_("Show LikX"))

    def set_active(self, active: bool) -> None:
        """Show or hide the tray icon."""
        if self._indicator:
            if active:
                self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            else:
                self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    @staticmethod
    def is_available() -> bool:
        """Check if system tray is available."""
        return APPINDICATOR_AVAILABLE
