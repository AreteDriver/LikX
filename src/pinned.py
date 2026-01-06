"""Pin screenshot to desktop - always on top floating window."""

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, GdkPixbuf
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


class PinnedWindow:
    """Floating window that displays a screenshot on top of all windows."""
    
    def __init__(self, pixbuf, title="Pinned Screenshot"):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available - install python3-gi")
        
        self.pixbuf = pixbuf
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Create window
        self.window = Gtk.Window()
        self.window.set_title(title)
        self.window.set_decorated(True)
        self.window.set_keep_above(True)  # Always on top
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        
        # Set initial size
        width = min(pixbuf.get_width(), 800)
        height = min(pixbuf.get_height(), 600)
        self.window.set_default_size(width, height)
        
        # Create main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(vbox)
        
        # Toolbar
        toolbar = self._create_toolbar()
        vbox.pack_start(toolbar, False, False, 0)
        
        # Scrolled window for image
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.image = Gtk.Image()
        self.image.set_from_pixbuf(pixbuf)
        scrolled.add(self.image)
        
        vbox.pack_start(scrolled, True, True, 0)
        
        # Connect events
        self.window.connect("destroy", self._on_destroy)
        self.image.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                             Gdk.EventMask.BUTTON_RELEASE_MASK |
                             Gdk.EventMask.POINTER_MOTION_MASK)
        self.image.connect("button-press-event", self._on_button_press)
        self.image.connect("button-release-event", self._on_button_release)
        self.image.connect("motion-notify-event", self._on_motion)
        
        self.window.show_all()
    
    def _create_toolbar(self):
        """Create toolbar with pin controls."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Zoom in
        zoom_in = Gtk.ToolButton(label="🔍+")
        zoom_in.set_tooltip_text("Zoom In")
        zoom_in.connect("clicked", lambda b: self._zoom(1.2))
        toolbar.insert(zoom_in, -1)
        
        # Zoom out
        zoom_out = Gtk.ToolButton(label="🔍-")
        zoom_out.set_tooltip_text("Zoom Out")
        zoom_out.connect("clicked", lambda b: self._zoom(0.8))
        toolbar.insert(zoom_out, -1)
        
        # Reset zoom
        zoom_reset = Gtk.ToolButton(label="⚖️")
        zoom_reset.set_tooltip_text("Reset Zoom")
        zoom_reset.connect("clicked", lambda b: self._reset_zoom())
        toolbar.insert(zoom_reset, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Always on top toggle
        self.pin_toggle = Gtk.ToggleToolButton(label="📌")
        self.pin_toggle.set_tooltip_text("Keep on Top")
        self.pin_toggle.set_active(True)
        self.pin_toggle.connect("toggled", self._on_pin_toggled)
        toolbar.insert(self.pin_toggle, -1)
        
        # Opacity
        opacity_item = Gtk.ToolItem()
        opacity_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        opacity_label = Gtk.Label(label="Opacity:")
        self.opacity_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.1, 1.0, 0.1
        )
        self.opacity_scale.set_value(1.0)
        self.opacity_scale.set_size_request(100, -1)
        self.opacity_scale.connect("value-changed", self._on_opacity_changed)
        opacity_box.pack_start(opacity_label, False, False, 0)
        opacity_box.pack_start(self.opacity_scale, False, False, 0)
        opacity_item.add(opacity_box)
        toolbar.insert(opacity_item, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Close button
        close_btn = Gtk.ToolButton(label="❌")
        close_btn.set_tooltip_text("Close")
        close_btn.connect("clicked", lambda b: self.window.destroy())
        toolbar.insert(close_btn, -1)
        
        return toolbar
    
    def _zoom(self, factor):
        """Zoom the image."""
        self.scale *= factor
        self.scale = max(0.1, min(10.0, self.scale))
        
        new_width = int(self.pixbuf.get_width() * self.scale)
        new_height = int(self.pixbuf.get_height() * self.scale)
        
        scaled = self.pixbuf.scale_simple(new_width, new_height, 
                                         GdkPixbuf.InterpType.BILINEAR)
        self.image.set_from_pixbuf(scaled)
    
    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.scale = 1.0
        self.image.set_from_pixbuf(self.pixbuf)
    
    def _on_pin_toggled(self, button):
        """Toggle always-on-top."""
        self.window.set_keep_above(button.get_active())
    
    def _on_opacity_changed(self, scale):
        """Change window opacity."""
        self.window.set_opacity(scale.get_value())
    
    def _on_button_press(self, widget, event):
        """Start dragging."""
        if event.button == 1:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        return True
    
    def _on_button_release(self, widget, event):
        """Stop dragging."""
        if event.button == 1:
            self.dragging = False
        return True
    
    def _on_motion(self, widget, event):
        """Handle dragging."""
        if self.dragging:
            # dx, dy available if pan is implemented
            _ = event.x - self.drag_start_x
            _ = event.y - self.drag_start_y
        return True
    
    def _on_destroy(self, widget):
        """Handle window destruction."""
        pass
