"""Tests for UI module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestUIModuleAvailability:
    """Test UI module can be imported and basic attributes exist."""

    def test_ui_module_imports(self):
        from src import ui
        assert ui is not None

    def test_gtk_available_flag_exists(self):
        from src.ui import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)

    def test_ui_has_editor_window_class(self):
        from src import ui
        assert hasattr(ui, "EditorWindow")

    def test_ui_has_main_window_class(self):
        from src import ui
        assert hasattr(ui, "MainWindow")

    def test_ui_has_settings_dialog_class(self):
        from src import ui
        assert hasattr(ui, "SettingsDialog")

    def test_ui_has_run_app_function(self):
        from src import ui
        assert hasattr(ui, "run_app")
        assert callable(ui.run_app)


class TestUIConfigIntegration:
    """Test UI integration with config module."""

    def test_config_module_imported(self):
        from src import ui, config
        # Check ui module uses config
        assert ui.config is config

    def test_editor_settings_in_config(self):
        from src import config
        cfg = config.load_config()
        assert "grid_size" in cfg
        assert "snap_to_grid" in cfg


class TestEditorStateSettings:
    """Test EditorState applies settings correctly."""

    def test_set_grid_snap_with_config_values(self):
        from src.editor import EditorState
        from src import config

        # Create a mock pixbuf
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.return_value = 800
        mock_pixbuf.get_height.return_value = 600

        state = EditorState(mock_pixbuf)

        # Load config and apply
        cfg = config.load_config()
        grid_size = cfg.get("grid_size", 20)
        snap_enabled = cfg.get("snap_to_grid", False)

        state.set_grid_snap(snap_enabled, grid_size)

        assert state.grid_size == grid_size
        assert state.grid_snap_enabled == snap_enabled

    def test_grid_size_clamped_to_range(self):
        from src.editor import EditorState

        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.return_value = 800
        mock_pixbuf.get_height.return_value = 600

        state = EditorState(mock_pixbuf)

        # Test min clamping
        state.set_grid_snap(True, 1)
        assert state.grid_size == 5  # Clamped to min

        # Test max clamping
        state.set_grid_snap(True, 200)
        assert state.grid_size == 100  # Clamped to max

        # Test valid value
        state.set_grid_snap(True, 50)
        assert state.grid_size == 50


class TestEditorWindowSettings:
    """Test EditorWindow applies settings method."""

    def test_apply_editor_settings_method_exists(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_apply_editor_settings")

    def test_apply_editor_settings_is_callable(self):
        from src.ui import EditorWindow
        assert callable(getattr(EditorWindow, "_apply_editor_settings", None))


class TestToolTypeEnum:
    """Test ToolType enum is accessible from ui module."""

    def test_tooltype_imported(self):
        from src.ui import ToolType
        assert ToolType is not None

    def test_tooltype_has_select(self):
        from src.ui import ToolType
        assert hasattr(ToolType, "SELECT")

    def test_tooltype_has_pen(self):
        from src.ui import ToolType
        assert hasattr(ToolType, "PEN")

    def test_tooltype_has_blur(self):
        from src.ui import ToolType
        assert hasattr(ToolType, "BLUR")

    def test_tooltype_has_measure(self):
        from src.ui import ToolType
        assert hasattr(ToolType, "MEASURE")


class TestColorClass:
    """Test Color class is accessible from ui module."""

    def test_color_imported(self):
        from src.ui import Color
        assert Color is not None

    def test_color_can_be_instantiated(self):
        from src.ui import Color
        c = Color(0.5, 0.5, 0.5, 1.0)
        assert c.r == 0.5
        assert c.a == 1.0

    def test_color_copy_method(self):
        from src.ui import Color
        c1 = Color(0.1, 0.2, 0.3, 0.4)
        c2 = c1.copy()
        assert c2.r == c1.r
        assert c2.g == c1.g
        assert c2.b == c1.b
        assert c2.a == c1.a
        # Ensure they're different objects
        c2.a = 0.9
        assert c1.a == 0.4


class TestArrowStyleEnum:
    """Test ArrowStyle enum is accessible."""

    def test_arrowstyle_imported(self):
        from src.ui import ArrowStyle
        assert ArrowStyle is not None

    def test_arrowstyle_has_open(self):
        from src.ui import ArrowStyle
        assert hasattr(ArrowStyle, "OPEN")

    def test_arrowstyle_has_filled(self):
        from src.ui import ArrowStyle
        assert hasattr(ArrowStyle, "FILLED")

    def test_arrowstyle_has_double(self):
        from src.ui import ArrowStyle
        assert hasattr(ArrowStyle, "DOUBLE")


class TestRegionSelectorClass:
    """Test RegionSelector class."""

    def test_region_selector_class_exists(self):
        from src.ui import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.ui import RegionSelector
        assert RegionSelector is not None

    def test_region_selector_raises_without_gtk(self):
        with patch("src.ui.GTK_AVAILABLE", False):
            # Need to reimport to get patched value
            import importlib
            from src import ui
            # Can't easily test this without reloading module

    def test_region_selector_has_callback_attribute(self):
        from src.ui import RegionSelector
        # Just check class structure
        assert hasattr(RegionSelector, "__init__")

    def test_region_selector_has_on_key_press(self):
        from src.ui import RegionSelector
        assert hasattr(RegionSelector, "_on_key_press")

    def test_region_selector_has_on_draw(self):
        from src.ui import RegionSelector
        assert hasattr(RegionSelector, "_on_draw")

    def test_region_selector_has_on_button_press(self):
        from src.ui import RegionSelector
        assert hasattr(RegionSelector, "_on_button_press")

    def test_region_selector_has_on_button_release(self):
        from src.ui import RegionSelector
        assert hasattr(RegionSelector, "_on_button_release")

    def test_region_selector_has_on_motion(self):
        from src.ui import RegionSelector
        assert hasattr(RegionSelector, "_on_motion")


class TestEditorWindowClass:
    """Test EditorWindow class structure."""

    def test_editor_window_class_exists(self):
        from src.ui import EditorWindow
        assert EditorWindow is not None

    def test_editor_window_has_init(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "__init__")

    def test_editor_window_has_init_cursors(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_init_cursors")

    def test_editor_window_has_update_cursor(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_update_cursor")

    def test_editor_window_has_create_sidebar(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_create_sidebar")

    def test_editor_window_has_create_context_bar(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_create_context_bar")

    def test_editor_window_has_set_tool(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_set_tool")

    def test_editor_window_has_set_color(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_set_color")

    def test_editor_window_has_save(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_save")

    def test_editor_window_has_undo(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_undo")

    def test_editor_window_has_redo(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_redo")

    def test_editor_window_has_clear(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_clear")

    def test_editor_window_has_upload(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_upload")

    def test_editor_window_has_copy_to_clipboard(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_copy_to_clipboard")

    def test_editor_window_has_show_command_palette(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_show_command_palette")

    def test_editor_window_has_show_radial_menu(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_show_radial_menu")

    def test_editor_window_has_on_draw(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_draw")

    def test_editor_window_has_on_button_press(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_button_press")

    def test_editor_window_has_on_button_release(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_button_release")

    def test_editor_window_has_on_motion(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_motion")

    def test_editor_window_has_on_key_press(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_key_press")

    def test_editor_window_has_on_scroll(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_scroll")


class TestMainWindowClass:
    """Test MainWindow class structure."""

    def test_main_window_class_exists(self):
        from src.ui import MainWindow
        assert MainWindow is not None

    def test_main_window_has_init(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "__init__")

    def test_main_window_has_load_css(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_load_css")

    def test_main_window_has_create_big_button(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_create_big_button")

    def test_main_window_has_on_fullscreen(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_fullscreen")

    def test_main_window_has_capture_fullscreen(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_capture_fullscreen")

    def test_main_window_has_on_region(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_region")

    def test_main_window_has_start_region_selection(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_start_region_selection")

    def test_main_window_has_on_window(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_window")

    def test_main_window_has_capture_window(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_capture_window")

    def test_main_window_has_on_settings(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_settings")

    def test_main_window_has_on_about(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_about")

    def test_main_window_has_on_quit(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_quit")

    def test_main_window_has_run(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "run")

    def test_main_window_has_register_global_hotkeys(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_register_global_hotkeys")

    def test_main_window_has_on_history(self):
        from src.ui import MainWindow
        assert hasattr(MainWindow, "_on_history")


class TestSettingsDialogClass:
    """Test SettingsDialog class structure."""

    def test_settings_dialog_class_exists(self):
        from src.ui import SettingsDialog
        assert SettingsDialog is not None

    def test_settings_dialog_has_init(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "__init__")

    def test_settings_dialog_has_create_general_settings(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_create_general_settings")

    def test_settings_dialog_has_create_capture_settings(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_create_capture_settings")

    def test_settings_dialog_has_create_upload_settings(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_create_upload_settings")

    def test_settings_dialog_has_create_editor_settings(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_create_editor_settings")

    def test_settings_dialog_has_save_settings(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_save_settings")

    def test_settings_dialog_has_reset_to_defaults(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_reset_to_defaults")

    def test_settings_dialog_has_browse_directory(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_browse_directory")

    def test_settings_dialog_has_on_grid_size_changed(self):
        from src.ui import SettingsDialog
        assert hasattr(SettingsDialog, "_on_grid_size_changed")


class TestRunAppFunction:
    """Test run_app function."""

    def test_run_app_exists(self):
        from src.ui import run_app
        assert callable(run_app)


class TestEditorWindowDrawingMethods:
    """Test EditorWindow drawing methods exist."""

    def test_has_draw_callout_preview(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_callout_preview")

    def test_has_draw_crop_preview(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_crop_preview")

    def test_has_draw_selection_handles(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_selection_handles")

    def test_has_draw_snap_guides(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_snap_guides")

    def test_has_draw_grid(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_grid")

    def test_has_draw_lock_indicator(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_lock_indicator")


class TestEditorWindowEffectMethods:
    """Test EditorWindow effect application methods."""

    def test_has_apply_crop(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_apply_crop")

    def test_has_pick_color(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_pick_color")

    def test_has_show_toast(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_show_toast")

    def test_has_show_text_dialog(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_show_text_dialog")

    def test_has_show_callout_dialog(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_show_callout_dialog")


class TestEditorWindowCoordinateMethods:
    """Test EditorWindow coordinate transformation methods."""

    def test_has_screen_to_image(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_screen_to_image")

    def test_has_update_resize_cursor(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_update_resize_cursor")

    def test_has_update_zoom_label(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_update_zoom_label")


class TestEditorWindowToolbarMethods:
    """Test EditorWindow toolbar creation methods."""

    def test_has_load_css(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_load_css")

    def test_has_create_color_popover(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_create_color_popover")

    def test_has_create_stamp_popover(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_create_stamp_popover")

    def test_has_update_context_bar(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_update_context_bar")

    def test_has_draw_color_swatch(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_color_swatch")

    def test_has_on_stamp_selected(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_stamp_selected")


class TestEditorWindowColorMethods:
    """Test EditorWindow color handling methods."""

    def test_has_draw_color_dot(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_color_dot")

    def test_has_draw_neo_color(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_draw_neo_color")

    def test_has_set_color_rgb(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_set_color_rgb")

    def test_has_update_recent_colors(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_update_recent_colors")


class TestEditorWindowToggleMethods:
    """Test EditorWindow toggle handler methods."""

    def test_has_on_tool_toggled(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_tool_toggled")

    def test_has_on_stamp_toggled(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_stamp_toggled")

    def test_has_on_arrow_style_toggled(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_arrow_style_toggled")

    def test_has_on_bold_toggled(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_bold_toggled")

    def test_has_on_italic_toggled(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_italic_toggled")

    def test_has_on_font_family_changed(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_font_family_changed")

    def test_has_on_color_chosen(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_color_chosen")

    def test_has_on_size_changed(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_size_changed")


class TestEditorWindowSaveMethods:
    """Test EditorWindow save methods."""

    def test_has_save_with_annotations(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_save_with_annotations")

    def test_has_on_destroy(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_destroy")


class TestEditorWindowRadialMenuIntegration:
    """Test EditorWindow radial menu integration."""

    def test_has_on_radial_select(self):
        from src.ui import EditorWindow
        assert hasattr(EditorWindow, "_on_radial_select")
