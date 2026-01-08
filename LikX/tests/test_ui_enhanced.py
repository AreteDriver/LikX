"""Tests for ui_enhanced module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestUiEnhancedModuleAvailability:
    """Test ui_enhanced module can be imported."""

    def test_ui_enhanced_module_imports(self):
        from src import ui_enhanced
        assert ui_enhanced is not None

    def test_gtk_available_flag_exists(self):
        from src.ui_enhanced import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)

    def test_add_advanced_features_function_exists(self):
        from src.ui_enhanced import add_advanced_features_to_editor
        assert callable(add_advanced_features_to_editor)

    def test_editor_window_enhancements_class_exists(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert EditorWindowEnhancements is not None

    def test_main_window_enhancements_class_exists(self):
        from src.ui_enhanced import MainWindowEnhancements
        assert MainWindowEnhancements is not None

    def test_quick_actions_dialog_class_exists(self):
        from src.ui_enhanced import QuickActionsDialog
        assert QuickActionsDialog is not None


class TestAddAdvancedFeatures:
    """Test add_advanced_features_to_editor function."""

    def test_returns_tuple_of_buttons(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import add_advanced_features_to_editor

        mock_editor = MagicMock()
        result = add_advanced_features_to_editor(mock_editor)

        assert isinstance(result, tuple)
        assert len(result) == 3  # ocr_btn, pin_btn, effects_btn


class TestEditorWindowEnhancementsAttributes:
    """Test EditorWindowEnhancements class attributes."""

    def test_has_init_enhanced_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "__init_enhanced__")

    def test_has_extract_text_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_extract_text")

    def test_has_pin_to_desktop_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_pin_to_desktop")

    def test_has_apply_shadow_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_apply_shadow")

    def test_has_apply_border_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_apply_border")

    def test_has_apply_background_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_apply_background")

    def test_has_apply_round_corners_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_apply_round_corners")

    def test_has_save_to_history_method(self):
        from src.ui_enhanced import EditorWindowEnhancements
        assert hasattr(EditorWindowEnhancements, "_save_to_history")


class TestEditorWindowEnhancementsInitEnhanced:
    """Test __init_enhanced__ method."""

    def test_init_enhanced_creates_ocr_engine(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.__init_enhanced__()

        assert hasattr(editor, "ocr_engine")

    def test_init_enhanced_creates_history_manager(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.__init_enhanced__()

        assert hasattr(editor, "history_manager")


class TestEditorWindowEnhancementsExtractText:
    """Test _extract_text method."""

    def test_extract_text_shows_error_when_ocr_unavailable(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.ocr_engine = MagicMock()
        editor.ocr_engine.available = False
        editor.window = None

        # Should not raise when OCR is unavailable
        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.MessageDialog.return_value = mock_dialog
            mock_dialog.run.return_value = None

            editor._extract_text()

            mock_gtk.MessageDialog.assert_called_once()

    def test_extract_text_success(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.ocr_engine = MagicMock()
        editor.ocr_engine.available = True
        editor.ocr_engine.extract_text.return_value = (True, "test text", None)
        editor.window = None
        editor.result = MagicMock()
        editor.result.pixbuf = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.MessageDialog.return_value = mock_dialog
            mock_dialog.run.return_value = mock_gtk.ResponseType.CLOSE
            mock_dialog.get_content_area.return_value = MagicMock()

            editor._extract_text()

            editor.ocr_engine.extract_text.assert_called_once()

    def test_extract_text_failure(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.ocr_engine = MagicMock()
        editor.ocr_engine.available = True
        editor.ocr_engine.extract_text.return_value = (False, None, "OCR error")
        editor.window = None
        editor.result = MagicMock()
        editor.result.pixbuf = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            editor._extract_text()

            mock_notify.assert_called_once()
            assert "OCR Failed" in mock_notify.call_args[0][0]


class TestEditorWindowEnhancementsPinToDesktop:
    """Test _pin_to_desktop method."""

    def test_pin_to_desktop_success(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        editor.result.pixbuf = MagicMock()
        editor.result.pixbuf.get_width.return_value = 100
        editor.result.pixbuf.get_height.return_value = 100
        editor.editor_state = MagicMock()
        editor.editor_state.elements = []
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        # cairo is imported inside the method, so patch it at the module where it's used
        with patch.dict('sys.modules', {'cairo': MagicMock()}):
            import sys
            mock_cairo = sys.modules['cairo']
            mock_surface = MagicMock()
            mock_cairo.ImageSurface.return_value = mock_surface
            mock_cairo.FORMAT_ARGB32 = 0
            mock_surface.get_data.return_value = b"\x00" * 40000
            mock_cairo.Context.return_value = MagicMock()

            with patch("src.ui_enhanced.Gdk") as mock_gdk:
                with patch("src.ui_enhanced.PinnedWindow") as mock_pinned:
                    with patch("src.ui_enhanced.show_notification") as mock_notify:
                        # Patch GdkPixbuf in gi.repository
                        with patch.dict('sys.modules', {'gi.repository.GdkPixbuf': MagicMock()}):
                            editor._pin_to_desktop()

                            mock_pinned.assert_called_once()
                            mock_notify.assert_called()

    def test_pin_to_desktop_exception(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        editor.result.pixbuf = MagicMock()
        editor.result.pixbuf.get_width.side_effect = Exception("Test error")
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        # Should not raise
        editor._pin_to_desktop()
        editor.statusbar.push.assert_called()


class TestEditorWindowEnhancementsApplyEffects:
    """Test effect application methods."""

    def test_apply_shadow(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        mock_pixbuf = MagicMock()
        editor.result.pixbuf = mock_pixbuf
        editor.editor_state = MagicMock()
        editor.drawing_area = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        with patch("src.ui_enhanced.add_shadow") as mock_shadow:
            mock_shadow.return_value = mock_pixbuf
            mock_pixbuf.get_width.return_value = 100
            mock_pixbuf.get_height.return_value = 100

            editor._apply_shadow()

            mock_shadow.assert_called_once_with(mock_pixbuf)
            editor.drawing_area.queue_draw.assert_called_once()

    def test_apply_border_ok(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        mock_pixbuf = MagicMock()
        editor.result.pixbuf = mock_pixbuf
        editor.editor_state = MagicMock()
        editor.drawing_area = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0
        editor.window = None

        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.ColorChooserDialog.return_value = mock_dialog
            mock_dialog.run.return_value = mock_gtk.ResponseType.OK
            mock_rgba = MagicMock()
            mock_rgba.red = 1.0
            mock_rgba.green = 0.0
            mock_rgba.blue = 0.0
            mock_rgba.alpha = 1.0
            mock_dialog.get_rgba.return_value = mock_rgba

            with patch("src.ui_enhanced.add_border") as mock_border:
                mock_border.return_value = mock_pixbuf
                mock_pixbuf.get_width.return_value = 110
                mock_pixbuf.get_height.return_value = 110

                editor._apply_border()

                mock_border.assert_called_once()
                mock_dialog.destroy.assert_called_once()

    def test_apply_border_cancel(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.window = None

        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.ColorChooserDialog.return_value = mock_dialog
            mock_dialog.run.return_value = mock_gtk.ResponseType.CANCEL

            with patch("src.ui_enhanced.add_border") as mock_border:
                editor._apply_border()

                mock_border.assert_not_called()
                mock_dialog.destroy.assert_called_once()

    def test_apply_background_ok(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        mock_pixbuf = MagicMock()
        editor.result.pixbuf = mock_pixbuf
        editor.editor_state = MagicMock()
        editor.drawing_area = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0
        editor.window = None

        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.ColorChooserDialog.return_value = mock_dialog
            mock_dialog.run.return_value = mock_gtk.ResponseType.OK
            mock_rgba = MagicMock()
            mock_rgba.red = 0.5
            mock_rgba.green = 0.5
            mock_rgba.blue = 0.5
            mock_rgba.alpha = 1.0
            mock_dialog.get_rgba.return_value = mock_rgba

            with patch("src.ui_enhanced.add_background") as mock_bg:
                mock_bg.return_value = mock_pixbuf
                mock_pixbuf.get_width.return_value = 140
                mock_pixbuf.get_height.return_value = 140

                editor._apply_background()

                mock_bg.assert_called_once()
                mock_dialog.destroy.assert_called_once()

    def test_apply_round_corners(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.result = MagicMock()
        mock_pixbuf = MagicMock()
        editor.result.pixbuf = mock_pixbuf
        editor.editor_state = MagicMock()
        editor.drawing_area = MagicMock()
        editor.statusbar = MagicMock()
        editor.statusbar_context = 0

        with patch("src.ui_enhanced.round_corners") as mock_round:
            mock_round.return_value = mock_pixbuf

            editor._apply_round_corners()

            mock_round.assert_called_once_with(mock_pixbuf)
            editor.drawing_area.queue_draw.assert_called_once()


class TestEditorWindowEnhancementsSaveToHistory:
    """Test _save_to_history method."""

    def test_save_to_history(self):
        from src.ui_enhanced import EditorWindowEnhancements

        class MockEditor(EditorWindowEnhancements):
            pass

        editor = MockEditor()
        editor.history_manager = MagicMock()
        editor.capture_mode = "fullscreen"

        filepath = Path("/tmp/test.png")
        editor._save_to_history(filepath)

        editor.history_manager.add.assert_called_once_with(filepath, mode="fullscreen")


class TestMainWindowEnhancementsAttributes:
    """Test MainWindowEnhancements class attributes."""

    def test_has_add_history_button_method(self):
        from src.ui_enhanced import MainWindowEnhancements
        assert hasattr(MainWindowEnhancements, "add_history_button")

    def test_has_on_history_method(self):
        from src.ui_enhanced import MainWindowEnhancements
        assert hasattr(MainWindowEnhancements, "_on_history")


class TestMainWindowEnhancementsOnHistory:
    """Test _on_history method."""

    def test_on_history_success(self):
        from src.ui_enhanced import MainWindowEnhancements

        class MockMainWindow(MainWindowEnhancements):
            pass

        window = MockMainWindow()
        window.window = MagicMock()

        with patch("src.ui_enhanced.HistoryWindow") as mock_history:
            window._on_history(None)
            mock_history.assert_called_once_with(window.window)

    def test_on_history_exception(self):
        from src.ui_enhanced import MainWindowEnhancements

        class MockMainWindow(MainWindowEnhancements):
            pass

        window = MockMainWindow()
        window.window = MagicMock()

        with patch("src.ui_enhanced.HistoryWindow") as mock_history:
            mock_history.side_effect = Exception("Test error")

            with patch("src.ui_enhanced.show_notification") as mock_notify:
                window._on_history(None)
                mock_notify.assert_called_once()


class TestQuickActionsDialogAttributes:
    """Test QuickActionsDialog class attributes."""

    def test_has_quick_screenshot_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_quick_screenshot")

    def test_has_screenshot_ocr_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_screenshot_ocr")

    def test_has_screenshot_upload_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_screenshot_upload")

    def test_has_screenshot_pin_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_screenshot_pin")

    def test_has_screenshot_blur_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_screenshot_blur")

    def test_has_recent_screenshots_method(self):
        from src.ui_enhanced import QuickActionsDialog
        assert hasattr(QuickActionsDialog, "_recent_screenshots")


class TestQuickActionsDialogMethods:
    """Test QuickActionsDialog methods."""

    def test_quick_screenshot_shows_notification(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            # Directly test the instance method
            dialog = object.__new__(QuickActionsDialog)
            dialog._quick_screenshot()
            mock_notify.assert_called_once()

    def test_screenshot_ocr_shows_notification(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            dialog = object.__new__(QuickActionsDialog)
            dialog._screenshot_ocr()
            mock_notify.assert_called_once()

    def test_screenshot_upload_shows_notification(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            dialog = object.__new__(QuickActionsDialog)
            dialog._screenshot_upload()
            mock_notify.assert_called_once()

    def test_screenshot_pin_shows_notification(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            dialog = object.__new__(QuickActionsDialog)
            dialog._screenshot_pin()
            mock_notify.assert_called_once()

    def test_screenshot_blur_shows_notification(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.show_notification") as mock_notify:
            dialog = object.__new__(QuickActionsDialog)
            dialog._screenshot_blur()
            mock_notify.assert_called_once()

    def test_recent_screenshots_opens_history(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.HistoryWindow") as mock_history:
            dialog = object.__new__(QuickActionsDialog)
            dialog._recent_screenshots()
            mock_history.assert_called_once()

    def test_recent_screenshots_handles_exception(self):
        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.HistoryWindow") as mock_history:
            mock_history.side_effect = Exception("Test error")

            with patch("src.ui_enhanced.show_notification") as mock_notify:
                dialog = object.__new__(QuickActionsDialog)
                dialog._recent_screenshots()
                mock_notify.assert_called_once()


class TestQuickActionsDialogInit:
    """Test QuickActionsDialog initialization."""

    def test_init_creates_dialog(self):
        from src.ui_enhanced import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui_enhanced import QuickActionsDialog

        with patch("src.ui_enhanced.Gtk") as mock_gtk:
            mock_dialog = MagicMock()
            mock_gtk.Dialog.return_value = mock_dialog
            mock_dialog.get_content_area.return_value = MagicMock()
            mock_dialog.run.return_value = None

            QuickActionsDialog(None)

            mock_gtk.Dialog.assert_called_once()
            mock_dialog.run.assert_called_once()
            mock_dialog.destroy.assert_called_once()
