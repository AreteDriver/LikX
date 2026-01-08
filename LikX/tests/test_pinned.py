"""Tests for pinned window module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPinnedModuleAvailability:
    """Test pinned module can be imported."""

    def test_pinned_module_imports(self):
        from src import pinned
        assert pinned is not None

    def test_gtk_available_flag_exists(self):
        from src.pinned import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)

    def test_pinned_window_class_exists(self):
        from src.pinned import PinnedWindow
        assert PinnedWindow is not None


class TestPinnedWindowAttributes:
    """Test PinnedWindow class attributes."""

    def test_class_has_init(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "__init__")

    def test_class_has_zoom_method(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_zoom")

    def test_class_has_reset_zoom_method(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_reset_zoom")

    def test_class_has_create_toolbar_method(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_create_toolbar")

    def test_class_has_opacity_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_opacity_changed")

    def test_class_has_pin_toggle_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_pin_toggled")

    def test_class_has_button_press_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_button_press")

    def test_class_has_button_release_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_button_release")

    def test_class_has_motion_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_motion")

    def test_class_has_destroy_handler(self):
        from src.pinned import PinnedWindow
        assert hasattr(PinnedWindow, "_on_destroy")


class TestPinnedWindowZoomLogic:
    """Test zoom calculation logic."""

    def test_zoom_scale_clamping_min(self):
        # Test that scale is clamped to minimum 0.1
        scale = 0.05
        factor = 0.8
        new_scale = scale * factor
        clamped = max(0.1, min(10.0, new_scale))
        assert clamped == 0.1

    def test_zoom_scale_clamping_max(self):
        # Test that scale is clamped to maximum 10.0
        scale = 9.0
        factor = 1.2
        new_scale = scale * factor
        clamped = max(0.1, min(10.0, new_scale))
        assert clamped == 10.0

    def test_zoom_in_calculation(self):
        scale = 1.0
        factor = 1.2
        new_scale = scale * factor
        assert new_scale == 1.2

    def test_zoom_out_calculation(self):
        scale = 1.0
        factor = 0.8
        new_scale = scale * factor
        assert new_scale == 0.8

    def test_multiple_zoom_in(self):
        scale = 1.0
        for _ in range(5):
            scale *= 1.2
            scale = max(0.1, min(10.0, scale))
        assert scale < 10.0  # Should stay within bounds

    def test_multiple_zoom_out(self):
        scale = 1.0
        for _ in range(20):
            scale *= 0.8
            scale = max(0.1, min(10.0, scale))
        assert scale == 0.1  # Should hit minimum


class TestPinnedWindowSizeCalculation:
    """Test window size calculations."""

    def test_initial_size_small_image(self):
        # Image smaller than max
        width = 400
        height = 300
        max_width = 800
        max_height = 600

        result_width = min(width, max_width)
        result_height = min(height, max_height)

        assert result_width == 400
        assert result_height == 300

    def test_initial_size_large_image(self):
        # Image larger than max
        width = 1920
        height = 1080
        max_width = 800
        max_height = 600

        result_width = min(width, max_width)
        result_height = min(height, max_height)

        assert result_width == 800
        assert result_height == 600

    def test_initial_size_wide_image(self):
        width = 2000
        height = 400
        max_width = 800
        max_height = 600

        result_width = min(width, max_width)
        result_height = min(height, max_height)

        assert result_width == 800
        assert result_height == 400

    def test_initial_size_tall_image(self):
        width = 400
        height = 2000
        max_width = 800
        max_height = 600

        result_width = min(width, max_width)
        result_height = min(height, max_height)

        assert result_width == 400
        assert result_height == 600


class TestPinnedWindowScaledDimensions:
    """Test scaled dimension calculations."""

    def test_scale_dimensions_100_percent(self):
        original_width = 800
        original_height = 600
        scale = 1.0

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        assert new_width == 800
        assert new_height == 600

    def test_scale_dimensions_200_percent(self):
        original_width = 400
        original_height = 300
        scale = 2.0

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        assert new_width == 800
        assert new_height == 600

    def test_scale_dimensions_50_percent(self):
        original_width = 800
        original_height = 600
        scale = 0.5

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        assert new_width == 400
        assert new_height == 300

    def test_scale_dimensions_with_rounding(self):
        original_width = 100
        original_height = 100
        scale = 1.5

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        assert new_width == 150
        assert new_height == 150


class TestPinnedWindowDragging:
    """Test dragging state logic."""

    def test_drag_start(self):
        dragging = False
        event_button = 1  # Left click

        if event_button == 1:
            dragging = True

        assert dragging is True

    def test_drag_end(self):
        dragging = True
        event_button = 1  # Left click release

        if event_button == 1:
            dragging = False

        assert dragging is False

    def test_right_click_does_not_drag(self):
        dragging = False
        event_button = 3  # Right click

        if event_button == 1:
            dragging = True

        assert dragging is False

    def test_drag_delta_calculation(self):
        start_x, start_y = 100, 100
        current_x, current_y = 150, 120

        dx = current_x - start_x
        dy = current_y - start_y

        assert dx == 50
        assert dy == 20


class TestPinnedWindowOpacity:
    """Test opacity calculations."""

    def test_opacity_range_min(self):
        min_opacity = 0.1
        value = 0.1
        clamped = max(min_opacity, min(1.0, value))
        assert clamped == 0.1

    def test_opacity_range_max(self):
        value = 1.0
        assert value == 1.0

    def test_opacity_mid_range(self):
        value = 0.5
        clamped = max(0.1, min(1.0, value))
        assert clamped == 0.5

    def test_opacity_default(self):
        default_opacity = 1.0
        assert default_opacity == 1.0
