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
