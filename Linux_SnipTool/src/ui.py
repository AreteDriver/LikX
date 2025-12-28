"""Enhanced user interface module for Linux SnipTool with full features."""

import sys
from typing import Optional, Callable
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config
from .capture import CaptureMode, CaptureResult, capture, save_capture
from .editor import EditorState, ToolType, COLORS, Color, render_elements
from .notification import show_notification, show_screenshot_saved, show_screenshot_copied, show_upload_success, show_upload_error
from .uploader import Uploader
from .hotkeys import HotkeyManager


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
        
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.window.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_from_name(display, "crosshair")
        
        self.window.show_all()
        self.window.get_window().set_cursor(cursor)
    
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
                self.callback(x, y, width, height)
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
        
        self.window = Gtk.Window(title="Linux SnipTool - Editor")
        self.window.set_default_size(900, 700)
        self.window.connect("destroy", self._on_destroy)
        self.window.connect("key-press-event", self._on_key_press)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_box)
        
        # Top toolbar - tools
        self.toolbar = self._create_toolbar()
        main_box.pack_start(self.toolbar, False, False, 0)
        
        # Color toolbar
        self.color_toolbar = self._create_color_toolbar()
        main_box.pack_start(self.color_toolbar, False, False, 0)
        
        # Drawing area with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(
            result.pixbuf.get_width(),
            result.pixbuf.get_height()
        )
        
        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.connect("button-press-event", self._on_button_press)
        self.drawing_area.connect("button-release-event", self._on_button_release)
        self.drawing_area.connect("motion-notify-event", self._on_motion)
        
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        scrolled.add(self.drawing_area)
        main_box.pack_start(scrolled, True, True, 0)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        self.statusbar_context = self.statusbar.get_context_id("editor")
        self.statusbar.push(self.statusbar_context, "Ready")
        main_box.pack_start(self.statusbar, False, False, 0)
        
        self.window.show_all()
    
    def _create_toolbar(self) -> Gtk.Toolbar:
        """Create the main tool toolbar."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        
        tools = [
            ("✏️ Pen", ToolType.PEN, "Draw freehand"),
            ("🖍️ Highlighter", ToolType.HIGHLIGHTER, "Highlight areas"),
            ("📏 Line", ToolType.LINE, "Draw straight line"),
            ("➡️ Arrow", ToolType.ARROW, "Draw arrow"),
            ("⬜ Rectangle", ToolType.RECTANGLE, "Draw rectangle"),
            ("⭕ Ellipse", ToolType.ELLIPSE, "Draw ellipse"),
            ("📝 Text", ToolType.TEXT, "Add text"),
            ("🔍 Blur", ToolType.BLUR, "Blur region"),
            ("◼️ Pixelate", ToolType.PIXELATE, "Pixelate region"),
            ("🗑️ Eraser", ToolType.ERASER, "Erase"),
        ]
        
        for label, tool, tooltip in tools:
            button = Gtk.ToolButton(label=label)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda b, t=tool: self._set_tool(t))
            toolbar.insert(button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Size controls
        size_item = Gtk.ToolItem()
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        size_label = Gtk.Label(label="Size:")
        self.size_spin = Gtk.SpinButton()
        self.size_spin.set_range(1, 50)
        self.size_spin.set_value(2)
        self.size_spin.set_increments(1, 5)
        self.size_spin.connect("value-changed", self._on_size_changed)
        size_box.pack_start(size_label, False, False, 0)
        size_box.pack_start(self.size_spin, False, False, 0)
        size_item.add(size_box)
        toolbar.insert(size_item, -1)
        
        return toolbar
    
    def _create_color_toolbar(self) -> Gtk.Toolbar:
        """Create the color selection toolbar."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        
        for color_name, color in COLORS.items():
            button = Gtk.ToolButton()
            button.set_tooltip_text(color_name.capitalize())
            
            # Create colored icon
            box = Gtk.Box()
            box.set_size_request(24, 24)
            box.override_background_color(
                Gtk.StateFlags.NORMAL,
                Gdk.RGBA(color.r, color.g, color.b, color.a)
            )
            button.set_icon_widget(box)
            
            button.connect("clicked", lambda b, c=color: self._set_color(c))
            toolbar.insert(button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Action buttons
        undo_btn = Gtk.ToolButton(label="↶ Undo")
        undo_btn.set_tooltip_text("Undo last action (Ctrl+Z)")
        undo_btn.connect("clicked", lambda b: self._undo())
        toolbar.insert(undo_btn, -1)
        
        redo_btn = Gtk.ToolButton(label="↷ Redo")
        redo_btn.set_tooltip_text("Redo (Ctrl+Y)")
        redo_btn.connect("clicked", lambda b: self._redo())
        toolbar.insert(redo_btn, -1)
        
        clear_btn = Gtk.ToolButton(label="🗑️ Clear All")
        clear_btn.set_tooltip_text("Clear all annotations")
        clear_btn.connect("clicked", lambda b: self._clear())
        toolbar.insert(clear_btn, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Save/Upload buttons
        save_btn = Gtk.ToolButton(label="💾 Save")
        save_btn.set_tooltip_text("Save to file (Ctrl+S)")
        save_btn.connect("clicked", lambda b: self._save())
        toolbar.insert(save_btn, -1)
        
        upload_btn = Gtk.ToolButton(label="☁️ Upload")
        upload_btn.set_tooltip_text("Upload to cloud")
        upload_btn.connect("clicked", lambda b: self._upload())
        toolbar.insert(upload_btn, -1)
        
        copy_btn = Gtk.ToolButton(label="📋 Copy")
        copy_btn.set_tooltip_text("Copy to clipboard (Ctrl+C)")
        copy_btn.connect("clicked", lambda b: self._copy_to_clipboard())
        toolbar.insert(copy_btn, -1)
        
        return toolbar
    
    def _set_tool(self, tool: ToolType) -> None:
        """Set the current drawing tool."""
        self.editor_state.set_tool(tool)
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
                cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width)
            )
            
            # Determine format
            format_str = filepath.suffix.lstrip('.').lower()
            format_map = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'bmp': 'bmp', 'gif': 'gif'}
            pixbuf_format = format_map.get(format_str, 'png')
            
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
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        
        # Add filters
        for fmt_name, fmt_ext in [("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("GIF", "*.gif")]:
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
        temp_file = Path(tempfile.mktemp(suffix='.png'))
        
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
                cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width)
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
        """Draw the screenshot and annotations."""
        Gdk.cairo_set_source_pixbuf(cr, self.result.pixbuf, 0, 0)
        cr.paint()
        
        elements = self.editor_state.get_elements()
        if elements:
            render_elements(cr.get_target(), elements, self.result.pixbuf)
        
        return True
    
    def _on_button_press(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle mouse button press."""
        if event.button == 1:
            if self.editor_state.current_tool == ToolType.TEXT:
                # Show text input dialog
                self._show_text_dialog(event.x, event.y)
            else:
                self.editor_state.start_drawing(event.x, event.y)
        return True
    
    def _on_button_release(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle mouse button release."""
        if event.button == 1:
            if self.editor_state.current_tool != ToolType.TEXT:
                self.editor_state.finish_drawing(event.x, event.y)
                self.drawing_area.queue_draw()
        return True
    
    def _on_motion(self, widget: Gtk.Widget, event: Gdk.EventMotion) -> bool:
        """Handle mouse motion."""
        if self.editor_state.current_tool != ToolType.TEXT:
            self.editor_state.continue_drawing(event.x, event.y)
            self.drawing_area.queue_draw()
        return True
    
    def _show_text_dialog(self, x: float, y: float) -> None:
        """Show dialog to input text."""
        dialog = Gtk.Dialog(
            title="Add Text",
            parent=self.window,
            flags=0,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
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
    
    def _on_key_press(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle keyboard shortcuts."""
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        
        if ctrl and event.keyval == Gdk.KEY_s:
            self._save()
            return True
        elif ctrl and event.keyval == Gdk.KEY_c:
            self._copy_to_clipboard()
            return True
        elif ctrl and event.keyval == Gdk.KEY_z:
            self._undo()
            return True
        elif ctrl and event.keyval == Gdk.KEY_y:
            self._redo()
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

        self.window = Gtk.Window(title="Linux SnipTool")
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
        title.set_markup("<span size='xx-large' weight='bold'>Linux SnipTool</span>")
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
            "fullscreen"
        )
        button_box.pack_start(fullscreen_btn, False, False, 0)

        region_btn = self._create_big_button(
            "⬚  Capture Region",
            "Select and capture a screen region\nCtrl+Shift+R",
            self._on_region,
            "region"
        )
        button_box.pack_start(region_btn, False, False, 0)

        window_btn = self._create_big_button(
            "🪟  Capture Window",
            "Capture the active window\nCtrl+Shift+W",
            self._on_window,
            "window"
        )
        button_box.pack_start(window_btn, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        main_box.pack_start(spacer, True, True, 0)

        # Bottom buttons
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_box.set_margin_top(16)
        main_box.pack_start(bottom_box, False, False, 0)

        history_btn = Gtk.Button(label="📚 History")
        history_btn.get_style_context().add_class("action-button")
        history_btn.connect("clicked", self._on_history)
        bottom_box.pack_start(history_btn, True, True, 0)

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
                    screen,
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"Warning: Could not load CSS: {e}")
    
    def _create_big_button(self, text: str, tooltip: str, callback, style_class: str = "") -> Gtk.Button:
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
        """Show screenshot history browser."""
        try:
            from .history import HistoryWindow
            HistoryWindow()
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="History",
                secondary_text=f"Could not open history: {e}"
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
            f"python3 {script_path} --fullscreen --no-edit"
        )
        self.hotkey_manager.register_hotkey(
            cfg.get("hotkey_region", "<Control><Shift>R"),
            self._on_region,
            f"python3 {script_path} --region --no-edit"
        )
        self.hotkey_manager.register_hotkey(
            cfg.get("hotkey_window", "<Control><Shift>W"),
            self._on_window,
            f"python3 {script_path} --window --no-edit"
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
        dialog.set_program_name("Linux SnipTool")
        dialog.set_version(__version__)
        dialog.set_comments("A powerful screenshot capture and annotation tool for Linux")
        dialog.set_website("https://github.com/AreteDriver/Linux_SnipTool")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_authors(["Linux SnipTool Contributors"])
        
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
            title="Settings",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL
        )
        self.dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Reset to Defaults", Gtk.ResponseType.REJECT,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
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
        self.auto_save_check = Gtk.CheckButton(label="Auto-save screenshots (skip editor)")
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
        hotkey_label.set_markup("<b>Global Hotkeys:</b>\n\n" +
                               f"Fullscreen: {self.cfg.get('hotkey_fullscreen', 'Ctrl+Shift+F')}\n" +
                               f"Region: {self.cfg.get('hotkey_region', 'Ctrl+Shift+R')}\n" +
                               f"Window: {self.cfg.get('hotkey_window', 'Ctrl+Shift+W')}\n\n" +
                               "<i>(Hotkeys work on GNOME desktop)</i>")
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
        
        self.auto_upload_check = Gtk.CheckButton(label="Automatically upload after save")
        self.auto_upload_check.set_active(self.cfg.get("auto_upload", False))
        box.pack_start(self.auto_upload_check, False, False, 0)
        
        # Info
        info_label = Gtk.Label(xalign=0)
        info_label.set_markup("<b>About Upload Services:</b>\n\n" +
                             "• <b>Imgur</b>: Free anonymous image hosting\n" +
                             "  URL is copied to clipboard automatically\n\n" +
                             "<i>Requires: curl</i>")
        info_label.set_line_wrap(True)
        box.pack_start(info_label, False, False, 0)
        
        return box
    
    def _browse_directory(self, button: Gtk.Button) -> None:
        """Browse for save directory."""
        dialog = Gtk.FileChooserDialog(
            title="Select Save Directory",
            parent=self.dialog,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
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
    """Run the Linux SnipTool application."""
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

from .ocr import OCREngine
from .pinned import PinnedWindow  
from .history import HistoryWindow, HistoryManager
from .effects import add_shadow, add_border, add_background, round_corners


# Enhance EditorWindow with premium features
_EditorWindow_init_original = EditorWindow.__init__

def _EditorWindow_init_enhanced(self, result):
    """Enhanced init with premium features."""
    _EditorWindow_init_original(self, result)
    
    # Initialize premium features
    self.ocr_engine = OCREngine()
    self.history_manager = HistoryManager()
    
    # Add premium buttons to toolbar
    separator = Gtk.SeparatorToolItem()
    self.color_toolbar.insert(separator, -1)
    
    # OCR button
    ocr_btn = Gtk.ToolButton(label="📝 OCR")
    ocr_btn.set_tooltip_text("Extract text from image (Tesseract)")
    ocr_btn.connect("clicked", lambda b: self._extract_text())
    self.color_toolbar.insert(ocr_btn, -1)
    
    # Pin button  
    pin_btn = Gtk.ToolButton(label="📌 Pin")
    pin_btn.set_tooltip_text("Pin to desktop (always on top)")
    pin_btn.connect("clicked", lambda b: self._pin_to_desktop())
    self.color_toolbar.insert(pin_btn, -1)
    
    # Effects menu
    effects_menu = Gtk.Menu()
    
    shadow_item = Gtk.MenuItem(label="✨ Add Shadow")
    shadow_item.connect("activate", lambda i: self._apply_shadow())
    effects_menu.append(shadow_item)
    
    border_item = Gtk.MenuItem(label="🖼️ Add Border")
    border_item.connect("activate", lambda i: self._apply_border())
    effects_menu.append(border_item)
    
    background_item = Gtk.MenuItem(label="🎨 Add Background")
    background_item.connect("activate", lambda i: self._apply_background())
    effects_menu.append(background_item)
    
    corners_item = Gtk.MenuItem(label="⚪ Round Corners")
    corners_item.connect("activate", lambda i: self._apply_round_corners())
    effects_menu.append(corners_item)
    
    effects_menu.show_all()
    
    effects_btn = Gtk.MenuToolButton(label="✨ Effects")
    effects_btn.set_tooltip_text("Apply visual effects")
    effects_btn.set_menu(effects_menu)
    self.color_toolbar.insert(effects_btn, -1)
    
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
            secondary_text="Install with: sudo apt install tesseract-ocr\n\nThen restart the application."
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
            text=f"Extracted Text ({len(text)} characters)"
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
                show_notification("Text Copied", f"Copied {len(text)} characters to clipboard")
            else:
                show_notification("Copy Failed", "Could not copy to clipboard", icon="dialog-warning")
        
        dialog.destroy()
        self.statusbar.push(self.statusbar_context, f"Extracted {len(text)} characters")
    else:
        self.statusbar.push(self.statusbar_context, f"OCR: {error or 'No text found'}")
        show_notification("OCR Result", error or "No text found in image", icon="dialog-information")


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
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width)
        )
        
        PinnedWindow(pinned_pixbuf, "Pinned Screenshot")
        self.statusbar.push(self.statusbar_context, "Pinned to desktop")
        show_notification("Pinned to Desktop", "Screenshot is now always on top. Use controls to adjust.")
        
    except Exception as e:
        self.statusbar.push(self.statusbar_context, f"Pin failed: {e}")
        show_notification("Pin Failed", str(e), icon="dialog-error")


def _apply_shadow(self):
    """Apply shadow effect."""
    self.result.pixbuf = add_shadow(self.result.pixbuf, shadow_size=15, opacity=0.3)
    self.editor_state.set_pixbuf(self.result.pixbuf)
    self.drawing_area.set_size_request(
        self.result.pixbuf.get_width(),
        self.result.pixbuf.get_height()
    )
    self.drawing_area.queue_draw()
    self.statusbar.push(self.statusbar_context, "Shadow effect applied")


def _apply_border(self):
    """Apply border effect."""
    dialog = Gtk.ColorChooserDialog(
        title="Choose Border Color",
        transient_for=self.window
    )
    dialog.set_rgba(Gdk.RGBA(0, 0, 0, 1))
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        rgba = dialog.get_rgba()
        color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        self.result.pixbuf = add_border(self.result.pixbuf, border_width=8, color=color)
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.set_size_request(
            self.result.pixbuf.get_width(),
            self.result.pixbuf.get_height()
        )
        self.drawing_area.queue_draw()
        self.statusbar.push(self.statusbar_context, "Border added")
    
    dialog.destroy()


def _apply_background(self):
    """Apply background effect."""
    dialog = Gtk.ColorChooserDialog(
        title="Choose Background Color",
        transient_for=self.window
    )
    dialog.set_rgba(Gdk.RGBA(1, 1, 1, 1))
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        rgba = dialog.get_rgba()
        color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        self.result.pixbuf = add_background(self.result.pixbuf, bg_color=color, padding=25)
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.set_size_request(
            self.result.pixbuf.get_width(),
            self.result.pixbuf.get_height()
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
    """Enhanced main window with history."""
    _MainWindow_init_original(self)
    
    # Add history button
    history_btn = self._create_big_button(
        "📚 Browse History",
        "View and manage past screenshots",
        self._on_history
    )
    
    # Insert before settings button
    children = self.window.get_children()[0].get_children()
    button_box = children[2]  # The button box
    button_box.pack_start(history_btn, False, False, 0)
    button_box.reorder_child(history_btn, 3)  # After window capture
    
    # Add quick actions button
    quick_btn = self._create_big_button(
        "⚡ Quick Actions",
        "Common screenshot workflows",
        self._on_quick_actions
    )
    button_box.pack_start(quick_btn, False, False, 0)
    button_box.reorder_child(quick_btn, 4)
    
    self.window.show_all()


def _on_history(self, button):
    """Open history browser."""
    try:
        HistoryWindow(self.window)
    except Exception as e:
        show_notification("History Browser", str(e), icon="dialog-error")


def _on_quick_actions(self, button):
    """Show quick actions dialog."""
    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.CLOSE,
        text="⚡ Quick Actions",
    )
    dialog.format_secondary_text(
        "Premium Features:\n\n" +
        "• 📝 OCR: Extract text from screenshots\n" +
        "• 📌 Pin: Keep screenshots always on top\n" +
        "• ✨ Effects: Add shadows, borders, backgrounds\n" +
        "• 📚 History: Browse all past screenshots\n" +
        "• 🔍 Blur/Pixelate: Privacy protection\n" +
        "• ☁️ Upload: Share via Imgur\n\n" +
        "All features available in the editor!"
    )
    dialog.run()
    dialog.destroy()


# Inject enhanced methods
MainWindow.__init__ = _MainWindow_init_enhanced
MainWindow._on_history = _on_history
MainWindow._on_quick_actions = _on_quick_actions

