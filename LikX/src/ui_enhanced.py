"""Enhanced UI with all premium features integrated."""

# This file extends the base UI with premium features
# Import and merge with existing ui.py

from pathlib import Path

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from .effects import add_background, add_border, add_shadow, round_corners
from .history import HistoryManager, HistoryWindow
from .notification import show_notification
from .ocr import OCREngine
from .pinned import PinnedWindow


def add_advanced_features_to_editor(editor_window):
    """Add advanced features to existing editor window."""

    # Add Effects menu
    effects_menu = Gtk.Menu()

    shadow_item = Gtk.MenuItem(label="Add Shadow")
    shadow_item.connect("activate", lambda i: editor_window._apply_shadow())
    effects_menu.append(shadow_item)

    border_item = Gtk.MenuItem(label="Add Border")
    border_item.connect("activate", lambda i: editor_window._apply_border())
    effects_menu.append(border_item)

    background_item = Gtk.MenuItem(label="Add Background")
    background_item.connect("activate", lambda i: editor_window._apply_background())
    effects_menu.append(background_item)

    corners_item = Gtk.MenuItem(label="Round Corners")
    corners_item.connect("activate", lambda i: editor_window._apply_round_corners())
    effects_menu.append(corners_item)

    effects_menu.show_all()

    # Add OCR button to toolbar
    ocr_btn = Gtk.ToolButton(label="📝 OCR")
    ocr_btn.set_tooltip_text("Extract text from image")
    ocr_btn.connect("clicked", lambda b: editor_window._extract_text())

    # Add Pin button
    pin_btn = Gtk.ToolButton(label="📌 Pin")
    pin_btn.set_tooltip_text("Pin screenshot to desktop")
    pin_btn.connect("clicked", lambda b: editor_window._pin_to_desktop())

    # Add Effects menu button
    effects_btn = Gtk.MenuToolButton(label="✨ Effects")
    effects_btn.set_tooltip_text("Apply visual effects")
    effects_btn.set_menu(effects_menu)
    effects_btn.connect(
        "clicked",
        lambda b: effects_menu.popup_at_widget(
            b, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
        ),
    )

    return ocr_btn, pin_btn, effects_btn


# Enhanced EditorWindow methods to add
class EditorWindowEnhancements:
    """Mixin class with enhanced features."""

    def __init_enhanced__(self):
        """Initialize enhanced features."""
        self.ocr_engine = OCREngine()
        self.history_manager = HistoryManager()

    def _extract_text(self):
        """Extract text using OCR."""
        if not self.ocr_engine.available:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Tesseract OCR not installed",
                secondary_text="Install with: sudo apt install tesseract-ocr",
            )
            dialog.run()
            dialog.destroy()
            return

        self.statusbar.push(self.statusbar_context, "Extracting text...")

        # Extract from current pixbuf
        success, text, error = self.ocr_engine.extract_text(self.result.pixbuf)

        if success:
            # Show text in dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text="Extracted Text",
            )
            dialog.add_buttons("Copy", 1, "Close", Gtk.ResponseType.CLOSE)

            # Add scrolled text view
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_size_request(500, 300)
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

            text_view = Gtk.TextView()
            text_view.set_editable(False)
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            text_view.get_buffer().set_text(text)

            scrolled.add(text_view)
            dialog.get_content_area().pack_start(scrolled, True, True, 10)
            dialog.show_all()

            response = dialog.run()
            if response == 1:  # Copy button
                self.ocr_engine.copy_text_to_clipboard(text)
                show_notification("Text Copied", "Extracted text copied to clipboard")

            dialog.destroy()
            self.statusbar.push(
                self.statusbar_context, f"Extracted {len(text)} characters"
            )
        else:
            self.statusbar.push(self.statusbar_context, f"OCR failed: {error}")
            show_notification("OCR Failed", error, icon="dialog-error")

    def _pin_to_desktop(self):
        """Pin current screenshot to desktop."""
        try:
            # Render with annotations
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

            # Convert to pixbuf
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

            # Create pinned window
            PinnedWindow(pinned_pixbuf, "Pinned Screenshot")
            self.statusbar.push(self.statusbar_context, "Pinned to desktop")
            show_notification("Pinned", "Screenshot pinned to desktop (always on top)")

        except Exception as e:
            self.statusbar.push(self.statusbar_context, f"Pin failed: {e}")

    def _apply_shadow(self):
        """Apply shadow effect."""
        self.result.pixbuf = add_shadow(self.result.pixbuf)
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.set_size_request(
            self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
        )
        self.drawing_area.queue_draw()
        self.statusbar.push(self.statusbar_context, "Shadow applied")

    def _apply_border(self):
        """Apply border effect."""
        # Show color chooser
        dialog = Gtk.ColorChooserDialog(
            title="Choose Border Color", transient_for=self.window
        )
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
            self.result.pixbuf = add_border(
                self.result.pixbuf, border_width=5, color=color
            )
            self.editor_state.set_pixbuf(self.result.pixbuf)
            self.drawing_area.set_size_request(
                self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
            )
            self.drawing_area.queue_draw()
            self.statusbar.push(self.statusbar_context, "Border applied")

        dialog.destroy()

    def _apply_background(self):
        """Apply background effect."""
        dialog = Gtk.ColorChooserDialog(
            title="Choose Background Color", transient_for=self.window
        )
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)
            self.result.pixbuf = add_background(self.result.pixbuf, bg_color=color)
            self.editor_state.set_pixbuf(self.result.pixbuf)
            self.drawing_area.set_size_request(
                self.result.pixbuf.get_width(), self.result.pixbuf.get_height()
            )
            self.drawing_area.queue_draw()
            self.statusbar.push(self.statusbar_context, "Background applied")

        dialog.destroy()

    def _apply_round_corners(self):
        """Apply rounded corners."""
        self.result.pixbuf = round_corners(self.result.pixbuf)
        self.editor_state.set_pixbuf(self.result.pixbuf)
        self.drawing_area.queue_draw()
        self.statusbar.push(self.statusbar_context, "Corners rounded")

    def _save_to_history(self, filepath: Path):
        """Save screenshot to history."""
        self.history_manager.add(filepath, mode=str(self.capture_mode))


# Enhanced MainWindow methods
class MainWindowEnhancements:
    """Mixin for enhanced main window features."""

    def add_history_button(self, button_box):
        """Add history browser button."""
        history_btn = self._create_big_button(
            "📚 Browse History", "View and manage past screenshots", self._on_history
        )
        button_box.pack_start(history_btn, False, False, 0)

    def _on_history(self, button):
        """Open history window."""
        try:
            HistoryWindow(self.window)
        except Exception as e:
            show_notification("History Failed", str(e), icon="dialog-error")


# Quick Actions - Common workflows
class QuickActionsDialog:
    """Dialog for quick common actions."""

    def __init__(self, parent=None):
        self.dialog = Gtk.Dialog(
            title="Quick Actions", transient_for=parent, flags=Gtk.DialogFlags.MODAL
        )
        self.dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.dialog.set_default_size(400, 500)

        content = self.dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(10)

        # Title
        title = Gtk.Label()
        title.set_markup("<span size='large' weight='bold'>⚡ Quick Actions</span>")
        content.pack_start(title, False, False, 0)

        # Actions grid
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_column_homogeneous(True)

        actions = [
            ("📷 Quick Screenshot", "Capture → Auto-save", self._quick_screenshot),
            ("📝 Screenshot + OCR", "Capture → Extract text", self._screenshot_ocr),
            (
                "☁️ Screenshot + Upload",
                "Capture → Upload → Copy URL",
                self._screenshot_upload,
            ),
            ("📌 Screenshot + Pin", "Capture → Pin to desktop", self._screenshot_pin),
            ("🎨 Blur Screenshot", "Capture → Auto-blur → Save", self._screenshot_blur),
            ("📚 Last 10 Screenshots", "Quick view recent", self._recent_screenshots),
        ]

        row = 0
        for title, desc, callback in actions:
            frame = Gtk.Frame()
            frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            box.set_border_width(10)

            btn = Gtk.Button(label=title)
            btn.connect("clicked", lambda b, cb=callback: cb())

            desc_label = Gtk.Label(label=desc)
            desc_label.set_line_wrap(True)

            box.pack_start(btn, False, False, 0)
            box.pack_start(desc_label, False, False, 0)

            frame.add(box)
            grid.attach(frame, row % 2, row // 2, 1, 1)
            row += 1

        content.pack_start(grid, True, True, 0)

        self.dialog.show_all()
        self.dialog.run()
        self.dialog.destroy()

    def _quick_screenshot(self):
        """Quick screenshot workflow."""
        show_notification(
            "Quick Screenshot",
            "Press Ctrl+Shift+F for fullscreen\nor Ctrl+Shift+R for region",
        )

    def _screenshot_ocr(self):
        """Screenshot then OCR workflow."""
        show_notification(
            "Screenshot + OCR",
            "Capture a screenshot, then use the OCR button in the editor",
        )

    def _screenshot_upload(self):
        """Screenshot then upload workflow."""
        show_notification(
            "Screenshot + Upload", "Capture, then click the ☁️ Upload button"
        )

    def _screenshot_pin(self):
        """Screenshot then pin workflow."""
        show_notification("Screenshot + Pin", "Capture, then click the 📌 Pin button")

    def _screenshot_blur(self):
        """Screenshot with auto blur workflow."""
        show_notification("Blur Screenshot", "Capture, use Blur tool, then save")

    def _recent_screenshots(self):
        """View recent screenshots."""
        try:
            HistoryWindow()
        except Exception as e:
            show_notification("History Failed", str(e))
