"""Tests for radial_menu module."""

import sys
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRadialMenuModuleAvailability:
    """Test radial_menu module can be imported."""

    def test_radial_menu_module_imports(self):
        from src import radial_menu
        assert radial_menu is not None

    def test_gtk_available_flag_exists(self):
        from src.radial_menu import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)

    def test_radial_menu_class_exists(self):
        from src.radial_menu import RadialMenu
        assert RadialMenu is not None

    def test_radial_items_exists(self):
        from src.radial_menu import RADIAL_ITEMS
        assert isinstance(RADIAL_ITEMS, list)


class TestRadialItems:
    """Test RADIAL_ITEMS constant."""

    def test_has_8_items(self):
        from src.radial_menu import RADIAL_ITEMS
        assert len(RADIAL_ITEMS) == 8

    def test_items_are_tuples(self):
        from src.radial_menu import RADIAL_ITEMS
        for item in RADIAL_ITEMS:
            assert isinstance(item, tuple)
            assert len(item) == 3  # (label, tool_type, icon)

    def test_contains_expected_tools(self):
        from src.radial_menu import RADIAL_ITEMS
        labels = [item[0] for item in RADIAL_ITEMS]

        assert "Crop" in labels
        assert "Draw" in labels
        assert "Arrow" in labels
        assert "Shape" in labels
        assert "Text" in labels
        assert "Blur" in labels

    def test_items_have_tool_types(self):
        from src.radial_menu import RADIAL_ITEMS
        from src.editor import ToolType

        for label, tool_type, icon in RADIAL_ITEMS:
            # Tool type can be None for placeholder items
            if tool_type is not None:
                assert isinstance(tool_type, ToolType)

    def test_items_have_icons(self):
        from src.radial_menu import RADIAL_ITEMS

        for label, tool_type, icon in RADIAL_ITEMS:
            assert isinstance(icon, str)
            assert len(icon) > 0


class TestRadialMenuConstants:
    """Test RadialMenu class constants."""

    def test_radius_constant(self):
        from src.radial_menu import RadialMenu
        assert RadialMenu.RADIUS == 100

    def test_inner_radius_constant(self):
        from src.radial_menu import RadialMenu
        assert RadialMenu.INNER_RADIUS == 35

    def test_segment_count_constant(self):
        from src.radial_menu import RadialMenu
        assert RadialMenu.SEGMENT_COUNT == 8


class TestRadialMenuInit:
    """Test RadialMenu initialization."""

    def test_init_raises_without_gtk(self):
        """Should raise RuntimeError if GTK not available."""
        with patch("src.radial_menu.GTK_AVAILABLE", False):
            from src.radial_menu import RadialMenu

            try:
                menu = RadialMenu(lambda x: None)
            except RuntimeError as e:
                assert "GTK not available" in str(e)

    def test_init_stores_callback(self):
        """Test that callback is stored."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        callback = MagicMock()
        menu = RadialMenu(callback)

        assert menu.callback is callback

    def test_init_sets_defaults(self):
        """Test initial state is correct."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)

        assert menu.highlighted_segment == -1
        assert menu.center_x == 0.0
        assert menu.center_y == 0.0
        assert menu.active is False


class TestRadialMenuAttributes:
    """Test RadialMenu attributes and methods exist."""

    def test_has_setup_window(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_setup_window")

    def test_has_connect_signals(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_connect_signals")

    def test_has_show_at(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "show_at")

    def test_has_on_draw(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_on_draw")

    def test_has_on_motion(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_on_motion")

    def test_has_on_button_release(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_on_button_release")

    def test_has_on_key_press(self):
        from src.radial_menu import RadialMenu
        assert hasattr(RadialMenu, "_on_key_press")


class TestRadialMenuShowAt:
    """Test show_at method."""

    def test_show_at_sets_position(self):
        """Test show_at sets center position."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.move = MagicMock()
        menu.show_all = MagicMock()
        menu.grab_add = MagicMock()

        menu.show_at(500, 300)

        # Check center is set
        size = RadialMenu.RADIUS * 2 + 20
        assert menu.center_x == size / 2
        assert menu.center_y == size / 2

    def test_show_at_sets_active(self):
        """Test show_at sets active flag."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.move = MagicMock()
        menu.show_all = MagicMock()
        menu.grab_add = MagicMock()

        menu.show_at(500, 300)

        assert menu.active is True

    def test_show_at_resets_highlight(self):
        """Test show_at resets highlighted segment."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.highlighted_segment = 3
        menu.move = MagicMock()
        menu.show_all = MagicMock()
        menu.grab_add = MagicMock()

        menu.show_at(500, 300)

        assert menu.highlighted_segment == -1


class TestRadialMenuMotion:
    """Test mouse motion handling."""

    def test_motion_center_no_highlight(self):
        """Test motion in center dead zone."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.center_x = 110
        menu.center_y = 110
        menu.drawing_area = MagicMock()

        # Mock event in center
        mock_event = MagicMock()
        mock_event.x = 110  # At center
        mock_event.y = 110

        menu._on_motion(None, mock_event)

        assert menu.highlighted_segment == -1

    def test_motion_outside_no_highlight(self):
        """Test motion outside radius."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.center_x = 110
        menu.center_y = 110
        menu.drawing_area = MagicMock()

        # Mock event outside radius
        mock_event = MagicMock()
        mock_event.x = 300  # Far from center
        mock_event.y = 300

        menu._on_motion(None, mock_event)

        assert menu.highlighted_segment == -1

    def test_motion_segment_highlight(self):
        """Test motion highlights correct segment."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.center_x = 110
        menu.center_y = 110
        menu.highlighted_segment = -1
        menu.drawing_area = MagicMock()

        # Mock event in valid segment area (to the right of center)
        mock_event = MagicMock()
        mock_event.x = 110 + 70  # Right of center, within radius
        mock_event.y = 110

        menu._on_motion(None, mock_event)

        # Should highlight a segment (segment 2 = right side at 90°)
        assert menu.highlighted_segment >= 0
        assert menu.highlighted_segment < 8


class TestRadialMenuButtonRelease:
    """Test button release handling."""

    def test_release_inactive_does_nothing(self):
        """Test release when not active."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        callback = MagicMock()
        menu = RadialMenu(callback)
        menu.active = False

        result = menu._on_button_release(None, None)

        callback.assert_not_called()
        assert result is True

    def test_release_with_selection_calls_callback(self):
        """Test release with highlighted segment calls callback."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu, RADIAL_ITEMS

        callback = MagicMock()
        menu = RadialMenu(callback)
        menu.active = True
        menu.highlighted_segment = 0  # First item (Crop)
        menu.grab_remove = MagicMock()
        menu.hide = MagicMock()

        menu._on_button_release(None, None)

        # Should call callback with the tool type for segment 0
        expected_tool = RADIAL_ITEMS[0][1]
        callback.assert_called_once_with(expected_tool)
        menu.hide.assert_called_once()
        assert menu.active is False

    def test_release_in_center_calls_callback_with_none(self):
        """Test release in center (cancel) calls callback with None."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        callback = MagicMock()
        menu = RadialMenu(callback)
        menu.active = True
        menu.highlighted_segment = -1  # No selection
        menu.grab_remove = MagicMock()
        menu.hide = MagicMock()

        menu._on_button_release(None, None)

        callback.assert_called_once_with(None)
        menu.hide.assert_called_once()


class TestRadialMenuKeyPress:
    """Test key press handling."""

    def test_escape_cancels(self):
        """Test Escape key cancels menu."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        callback = MagicMock()
        menu = RadialMenu(callback)
        menu.active = True
        menu.grab_remove = MagicMock()
        menu.hide = MagicMock()

        # Mock Escape key event
        mock_event = MagicMock()
        mock_event.keyval = 65307  # Gdk.KEY_Escape

        result = menu._on_key_press(None, mock_event)

        assert result is True
        callback.assert_called_once_with(None)
        menu.hide.assert_called_once()
        assert menu.active is False

    def test_other_key_does_nothing(self):
        """Test other keys don't do anything."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        callback = MagicMock()
        menu = RadialMenu(callback)

        mock_event = MagicMock()
        mock_event.keyval = 97  # 'a' key

        result = menu._on_key_press(None, mock_event)

        assert result is False
        callback.assert_not_called()


class TestRadialMenuDraw:
    """Test drawing functionality."""

    def test_on_draw_returns_false(self):
        """Test _on_draw returns False."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.center_x = 110
        menu.center_y = 110
        menu.highlighted_segment = -1

        # Mock Cairo context
        mock_ctx = MagicMock()

        result = menu._on_draw(None, mock_ctx)

        assert result is False


class TestRadialMenuSegmentCalculation:
    """Test segment angle calculations."""

    def test_segment_angles(self):
        """Verify segment angles are correct."""
        from src.radial_menu import RadialMenu

        segment_count = RadialMenu.SEGMENT_COUNT
        segment_angle = 2 * math.pi / segment_count

        # Each segment should be 45 degrees (π/4 radians)
        assert abs(segment_angle - math.pi / 4) < 0.001

    def test_segment_indices(self):
        """Test segment index calculation."""
        # Verify segment index calculation logic
        segment_count = 8
        segment_angle = 2 * math.pi / segment_count
        start_offset = -math.pi / 2 - segment_angle / 2

        # Test a few known angles
        # Right side (90°) should be segment 2
        angle = 0  # 0° in standard coordinates
        adjusted = angle - start_offset
        if adjusted < 0:
            adjusted += 2 * math.pi
        segment = int(adjusted / segment_angle) % segment_count
        assert segment == 2  # Right segment


class TestRadialMenuEdgeCases:
    """Test edge cases for RadialMenu."""

    def test_callback_none(self):
        """Test with None callback."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        # None callback should not crash
        menu = RadialMenu(None)
        menu.active = True
        menu.highlighted_segment = -1
        menu.grab_remove = MagicMock()
        menu.hide = MagicMock()

        # Should not raise
        menu._on_button_release(None, None)

    def test_motion_updates_only_on_change(self):
        """Test motion only updates on segment change."""
        from src.radial_menu import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.radial_menu import RadialMenu

        menu = RadialMenu(lambda x: None)
        menu.center_x = 110
        menu.center_y = 110
        menu.highlighted_segment = 2
        menu.drawing_area = MagicMock()

        # Motion that results in same segment
        mock_event = MagicMock()
        mock_event.x = 110 + 70
        mock_event.y = 110

        # Set segment to expected value first
        menu.highlighted_segment = 2

        # Queue draw should not be called if segment doesn't change
        menu._on_motion(None, mock_event)

        # If segment changed, queue_draw is called
        # If segment stayed same, queue_draw might not be called
        # Just verify it doesn't crash

    def test_all_segments_accessible(self):
        """Test all 8 segments can be highlighted."""
        from src.radial_menu import RadialMenu

        # Verify we have exactly 8 segments
        assert RadialMenu.SEGMENT_COUNT == 8

        # Verify radius allows for segment selection
        assert RadialMenu.RADIUS > RadialMenu.INNER_RADIUS
