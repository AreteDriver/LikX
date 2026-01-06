"""Tests for editor module."""

from unittest.mock import MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.editor import (
    ToolType,
    ArrowStyle,
    Point,
    Color,
    COLORS,
    DrawingElement,
    EditorState,
)


class TestPoint:
    """Test Point dataclass."""

    def test_point_creation(self):
        p = Point(10.5, 20.5)
        assert p.x == 10.5
        assert p.y == 20.5

    def test_point_with_integers(self):
        p = Point(100, 200)
        assert p.x == 100
        assert p.y == 200

    def test_point_with_negative_values(self):
        p = Point(-10, -20)
        assert p.x == -10
        assert p.y == -20


class TestColor:
    """Test Color dataclass."""

    def test_color_default_red(self):
        c = Color()
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert c.a == 1.0

    def test_color_custom_values(self):
        c = Color(0.5, 0.6, 0.7, 0.8)
        assert c.r == 0.5
        assert c.g == 0.6
        assert c.b == 0.7
        assert c.a == 0.8

    def test_color_to_tuple(self):
        c = Color(0.1, 0.2, 0.3, 0.4)
        assert c.to_tuple() == (0.1, 0.2, 0.3, 0.4)

    def test_color_from_hex_6_digit(self):
        c = Color.from_hex("#FF0000")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert c.a == 1.0

    def test_color_from_hex_8_digit(self):
        c = Color.from_hex("#FF000080")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert abs(c.a - 0.502) < 0.01  # 128/255 ≈ 0.502

    def test_color_from_hex_without_hash(self):
        c = Color.from_hex("00FF00")
        assert c.r == 0.0
        assert c.g == 1.0
        assert c.b == 0.0

    def test_color_from_hex_invalid_returns_default(self):
        c = Color.from_hex("invalid")
        # Should return default red
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0


class TestPredefinedColors:
    """Test predefined colors dictionary."""

    def test_colors_has_expected_keys(self):
        expected = ["red", "green", "blue", "yellow", "orange",
                    "purple", "black", "white", "cyan", "pink"]
        for color_name in expected:
            assert color_name in COLORS

    def test_red_color(self):
        c = COLORS["red"]
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0

    def test_green_color(self):
        c = COLORS["green"]
        assert c.r == 0.0
        assert c.g == 1.0
        assert c.b == 0.0

    def test_blue_color(self):
        c = COLORS["blue"]
        assert c.r == 0.0
        assert c.g == 0.0
        assert c.b == 1.0


class TestToolType:
    """Test ToolType enum."""

    def test_tool_types_exist(self):
        assert ToolType.SELECT.value == "select"
        assert ToolType.PEN.value == "pen"
        assert ToolType.HIGHLIGHTER.value == "highlighter"
        assert ToolType.LINE.value == "line"
        assert ToolType.ARROW.value == "arrow"
        assert ToolType.RECTANGLE.value == "rectangle"
        assert ToolType.ELLIPSE.value == "ellipse"
        assert ToolType.TEXT.value == "text"
        assert ToolType.BLUR.value == "blur"
        assert ToolType.PIXELATE.value == "pixelate"
        assert ToolType.CROP.value == "crop"
        assert ToolType.ERASER.value == "eraser"


class TestDrawingElement:
    """Test DrawingElement dataclass."""

    def test_drawing_element_defaults(self):
        elem = DrawingElement(tool=ToolType.PEN)
        assert elem.tool == ToolType.PEN
        assert elem.stroke_width == 2.0
        assert elem.points == []
        assert elem.text == ""
        assert elem.filled is False
        assert elem.font_size == 16

    def test_drawing_element_with_points(self):
        points = [Point(0, 0), Point(10, 10)]
        elem = DrawingElement(tool=ToolType.LINE, points=points)
        assert len(elem.points) == 2
        assert elem.points[0].x == 0
        assert elem.points[1].x == 10

    def test_drawing_element_with_text(self):
        elem = DrawingElement(tool=ToolType.TEXT, text="Hello", font_size=24)
        assert elem.text == "Hello"
        assert elem.font_size == 24


class TestEditorState:
    """Test EditorState class."""

    def test_init_without_pixbuf(self):
        state = EditorState()
        assert state.original_pixbuf is None
        assert state.current_pixbuf is None
        assert state.elements == []
        assert state.current_tool == ToolType.PEN
        assert state.stroke_width == 2.0
        assert state.is_drawing is False

    def test_init_with_pixbuf(self):
        mock_pixbuf = MagicMock()
        state = EditorState(pixbuf=mock_pixbuf)
        assert state.original_pixbuf == mock_pixbuf
        assert state.current_pixbuf == mock_pixbuf

    def test_set_tool(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        assert state.current_tool == ToolType.RECTANGLE

    def test_set_color(self):
        state = EditorState()
        new_color = Color(0.5, 0.5, 0.5)
        state.set_color(new_color)
        assert state.current_color == new_color

    def test_set_stroke_width_valid(self):
        state = EditorState()
        state.set_stroke_width(10.0)
        assert state.stroke_width == 10.0

    def test_set_stroke_width_clamped_min(self):
        state = EditorState()
        state.set_stroke_width(0.5)
        assert state.stroke_width == 1.0

    def test_set_stroke_width_clamped_max(self):
        state = EditorState()
        state.set_stroke_width(100.0)
        assert state.stroke_width == 50.0

    def test_set_font_size_valid(self):
        state = EditorState()
        state.set_font_size(24)
        assert state.font_size == 24

    def test_set_font_size_clamped_min(self):
        state = EditorState()
        state.set_font_size(4)
        assert state.font_size == 8

    def test_set_font_size_clamped_max(self):
        state = EditorState()
        state.set_font_size(100)
        assert state.font_size == 72

    def test_start_drawing(self):
        state = EditorState()
        state.start_drawing(10.0, 20.0)
        assert state.is_drawing is True
        assert state.current_element is not None
        assert len(state.current_element.points) == 1
        assert state.current_element.points[0].x == 10.0
        assert state.current_element.points[0].y == 20.0

    def test_continue_drawing_pen(self):
        state = EditorState()
        state.set_tool(ToolType.PEN)
        state.start_drawing(0, 0)
        state.continue_drawing(10, 10)
        state.continue_drawing(20, 20)
        assert len(state.current_element.points) == 3

    def test_continue_drawing_shape(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.continue_drawing(10, 10)
        state.continue_drawing(20, 20)
        # Shapes only have start and end points
        assert len(state.current_element.points) == 2
        assert state.current_element.points[-1].x == 20

    def test_finish_drawing(self):
        state = EditorState()
        state.start_drawing(0, 0)
        state.finish_drawing(100, 100)
        assert state.is_drawing is False
        assert state.current_element is None
        assert len(state.elements) == 1

    def test_undo_empty(self):
        state = EditorState()
        result = state.undo()
        assert result is False

    def test_undo_success(self):
        state = EditorState()
        state.start_drawing(0, 0)
        state.finish_drawing(10, 10)
        assert len(state.elements) == 1
        result = state.undo()
        assert result is True
        assert len(state.elements) == 0

    def test_redo_empty(self):
        state = EditorState()
        result = state.redo()
        assert result is False

    def test_redo_success(self):
        state = EditorState()
        state.start_drawing(0, 0)
        state.finish_drawing(10, 10)
        state.undo()
        assert len(state.elements) == 0
        result = state.redo()
        assert result is True
        assert len(state.elements) == 1

    def test_add_text_empty(self):
        state = EditorState()
        state.add_text(10, 20, "")
        assert len(state.elements) == 0

    def test_add_text_valid(self):
        state = EditorState()
        state.add_text(10, 20, "Hello World")
        assert len(state.elements) == 1
        assert state.elements[0].text == "Hello World"
        assert state.elements[0].tool == ToolType.TEXT

    def test_clear(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        state.add_text(30, 40, "Test2")
        assert len(state.elements) == 2
        state.clear()
        assert len(state.elements) == 0

    def test_clear_creates_undo_entry(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        state.clear()
        result = state.undo()
        assert result is True
        assert len(state.elements) == 1

    def test_get_elements_without_current(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        elements = state.get_elements()
        assert len(elements) == 1

    def test_get_elements_with_current(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        state.start_drawing(0, 0)
        elements = state.get_elements()
        assert len(elements) == 2

    def test_has_changes_false(self):
        state = EditorState()
        assert state.has_changes() is False

    def test_has_changes_with_elements(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        assert state.has_changes() is True

    def test_has_changes_while_drawing(self):
        state = EditorState()
        state.start_drawing(0, 0)
        assert state.has_changes() is True

    def test_set_pixbuf_clears_state(self):
        state = EditorState()
        state.add_text(10, 20, "Test")
        mock_pixbuf = MagicMock()
        state.set_pixbuf(mock_pixbuf)
        assert len(state.elements) == 0
        assert len(state.undo_stack) == 0
        assert state.original_pixbuf == mock_pixbuf


class TestEditorStateNewTools:
    """Test EditorState methods for new tools (v3.3-3.5)."""

    def test_add_number_creates_element(self):
        state = EditorState()
        state.add_number(100, 200)
        assert len(state.elements) == 1
        assert state.elements[0].tool == ToolType.NUMBER
        assert state.elements[0].number == 1

    def test_add_number_increments(self):
        state = EditorState()
        state.add_number(100, 200)
        state.add_number(150, 250)
        state.add_number(200, 300)
        assert state.elements[0].number == 1
        assert state.elements[1].number == 2
        assert state.elements[2].number == 3

    def test_add_stamp_creates_element(self):
        state = EditorState()
        state.add_stamp(50, 50)
        assert len(state.elements) == 1
        assert state.elements[0].tool == ToolType.STAMP
        assert state.elements[0].stamp == state.current_stamp

    def test_add_stamp_uses_current_stamp(self):
        state = EditorState()
        state.current_stamp = "✗"
        state.add_stamp(50, 50)
        assert state.elements[0].stamp == "✗"

    def test_add_callout_creates_element(self):
        state = EditorState()
        state.add_callout(100, 200, 150, 100, "Hello World")
        assert len(state.elements) == 1
        assert state.elements[0].tool == ToolType.CALLOUT
        assert state.elements[0].text == "Hello World"
        assert state.elements[0].fill_color is not None

    def test_add_callout_empty_text_ignored(self):
        state = EditorState()
        state.add_callout(100, 200, 150, 100, "")
        assert len(state.elements) == 0

    def test_add_callout_stores_two_points(self):
        state = EditorState()
        state.add_callout(100, 200, 150, 100, "Test")
        assert len(state.elements[0].points) == 2
        assert state.elements[0].points[0].x == 100  # tail
        assert state.elements[0].points[0].y == 200
        assert state.elements[0].points[1].x == 150  # box
        assert state.elements[0].points[1].y == 100


class TestEditorStateZoom:
    """Test zoom functionality."""

    def test_initial_zoom_level(self):
        state = EditorState()
        assert state.zoom_level == 1.0

    def test_zoom_in(self):
        state = EditorState()
        state.zoom_in()
        assert state.zoom_level > 1.0

    def test_zoom_out(self):
        state = EditorState()
        state.zoom_out()
        assert state.zoom_level < 1.0

    def test_reset_zoom(self):
        state = EditorState()
        state.zoom_in()
        state.zoom_in()
        state.reset_zoom()
        assert state.zoom_level == 1.0

    def test_zoom_level_capped_at_max(self):
        state = EditorState()
        for _ in range(20):  # Zoom in a lot
            state.zoom_in()
        assert state.zoom_level <= 8.0

    def test_zoom_level_capped_at_min(self):
        state = EditorState()
        for _ in range(20):  # Zoom out a lot
            state.zoom_out()
        assert state.zoom_level >= 0.25


class TestToolTypeNewTools:
    """Test new tool types."""

    def test_number_tool_exists(self):
        assert ToolType.NUMBER.value == "number"

    def test_colorpicker_tool_exists(self):
        assert ToolType.COLORPICKER.value == "colorpicker"

    def test_stamp_tool_exists(self):
        assert ToolType.STAMP.value == "stamp"

    def test_zoom_tool_exists(self):
        assert ToolType.ZOOM.value == "zoom"

    def test_callout_tool_exists(self):
        assert ToolType.CALLOUT.value == "callout"

    def test_measure_tool_exists(self):
        assert ToolType.MEASURE.value == "measure"

    def test_select_tool_exists(self):
        assert ToolType.SELECT.value == "select"


class TestEditorStateSelection:
    """Test selection functionality."""

    def test_initial_selection_state(self):
        state = EditorState()
        assert state.selected_index is None
        assert state._drag_start is None
        assert state._resize_handle is None

    def test_select_empty_returns_false(self):
        state = EditorState()
        result = state.select_at(50, 50)
        assert result is False
        assert state.selected_index is None

    def test_select_element_returns_true(self):
        state = EditorState()
        # Add a rectangle element
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        # Click inside the element
        result = state.select_at(50, 50)
        assert result is True
        assert state.selected_index == 0

    def test_select_outside_element_deselects(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        # Select the element
        state.select_at(50, 50)
        assert state.selected_index == 0

        # Click outside
        state.select_at(500, 500)
        assert state.selected_index is None

    def test_deselect(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        assert state.selected_index == 0

        state.deselect()
        assert state.selected_index is None

    def test_get_selected_none(self):
        state = EditorState()
        assert state.get_selected() is None

    def test_get_selected_returns_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        selected = state.get_selected()
        assert selected is not None
        assert selected.tool == ToolType.RECTANGLE

    def test_delete_selected_empty(self):
        state = EditorState()
        result = state.delete_selected()
        assert result is False

    def test_delete_selected_success(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        assert len(state.elements) == 1

        state.select_at(50, 50)
        result = state.delete_selected()
        assert result is True
        assert len(state.elements) == 0
        assert state.selected_index is None

    def test_move_selected_updates_position(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        original_x = state.elements[0].points[0].x

        # Move to new position
        state.move_selected(60, 60)
        new_x = state.elements[0].points[0].x

        # Position should have changed
        assert new_x != original_x

    def test_finish_move_clears_drag_state(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        state.finish_move()
        assert state._drag_start is None
        assert state._resize_handle is None

    def test_get_element_bbox(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 20)
        state.finish_drawing(100, 150)

        bbox = state._get_element_bbox(state.elements[0])
        assert bbox is not None
        x1, y1, x2, y2 = bbox
        assert x1 == 10
        assert y1 == 20
        assert x2 == 100
        assert y2 == 150


class TestResizeHandles:
    """Test resize handle functionality."""

    def test_hit_test_handles_no_selection(self):
        state = EditorState()
        assert state._hit_test_handles(50, 50) is None

    def test_hit_test_handles_nw_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click near top-left corner (10, 10)
        handle = state._hit_test_handles(12, 12)
        assert handle == 'nw'

    def test_hit_test_handles_se_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click near bottom-right corner (100, 100)
        handle = state._hit_test_handles(98, 98)
        assert handle == 'se'

    def test_hit_test_handles_ne_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click near top-right corner (100, 10)
        handle = state._hit_test_handles(98, 12)
        assert handle == 'ne'

    def test_hit_test_handles_sw_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click near bottom-left corner (10, 100)
        handle = state._hit_test_handles(12, 98)
        assert handle == 'sw'

    def test_hit_test_handles_miss(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click in center (not on handle)
        handle = state._hit_test_handles(55, 55)
        assert handle is None

    def test_select_at_starts_resize_mode(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Click on resize handle
        state.select_at(12, 12)  # nw corner
        assert state._resize_handle == 'nw'
        assert state._drag_start is not None

    def test_resize_selected_changes_size(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Start resize from se corner
        state.select_at(98, 98)  # se corner
        assert state._resize_handle == 'se'

        # Drag to expand
        state.move_selected(150, 150)

        # Element should be larger
        bbox = state._get_element_bbox(state.elements[0])
        assert bbox is not None
        x1, y1, x2, y2 = bbox
        assert x2 == 150
        assert y2 == 150

    def test_resize_enforces_minimum_size(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Start resize from se corner
        state.select_at(98, 98)

        # Try to make it too small (should be prevented)
        result = state._resize_selected(15, 15)  # Try to shrink to < 10px
        assert result is False  # Should reject too-small resize

    def test_finish_move_clears_resize_handle(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.select_at(50, 50)

        # Start resize
        state.select_at(98, 98)  # se corner
        assert state._resize_handle == 'se'

        # Finish
        state.finish_move()
        assert state._resize_handle is None

    def test_resize_nw_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(50, 50)
        state.finish_drawing(150, 150)
        state.select_at(100, 100)

        # Start resize from nw corner
        state.select_at(52, 52)
        assert state._resize_handle == 'nw'

        # Drag to move top-left corner
        state.move_selected(20, 30)

        bbox = state._get_element_bbox(state.elements[0])
        x1, y1, x2, y2 = bbox
        assert x1 == 20
        assert y1 == 30
        assert x2 == 150  # Right edge unchanged
        assert y2 == 150  # Bottom edge unchanged


class TestMultiSelect:
    """Test multi-select functionality."""

    def test_initial_selected_indices_empty(self):
        state = EditorState()
        assert state.selected_indices == set()

    def test_select_adds_to_indices(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        assert state.selected_indices == {0}

    def test_shift_click_adds_to_selection(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create two elements
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        # Select first
        state.select_at(50, 50)
        assert state.selected_indices == {0}

        # Shift+click second
        state.select_at(250, 50, add_to_selection=True)
        assert state.selected_indices == {0, 1}

    def test_shift_click_toggles_selection(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        assert 0 in state.selected_indices

        # Shift+click same element removes it
        state.select_at(50, 50, add_to_selection=True)
        assert 0 not in state.selected_indices

    def test_click_without_shift_replaces_selection(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        # Select first
        state.select_at(50, 50)
        # Shift+click second
        state.select_at(250, 50, add_to_selection=True)
        assert state.selected_indices == {0, 1}

        # Click first without shift - should replace selection
        state.select_at(50, 50, add_to_selection=False)
        assert state.selected_indices == {0}

    def test_get_all_selected_returns_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        state.select_at(50, 50)
        state.select_at(250, 50, add_to_selection=True)

        selected = state.get_all_selected()
        assert len(selected) == 2

    def test_move_selected_moves_all(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        # Select both
        state.select_at(50, 50)
        state.select_at(250, 50, add_to_selection=True)

        # Move
        state.move_selected(60, 60)

        # Both should have moved
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        assert bbox0[0] != 10  # x1 changed
        assert bbox1[0] != 200  # x1 changed

    def test_delete_selected_deletes_all(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)
        state.start_drawing(400, 10)
        state.finish_drawing(500, 100)

        assert len(state.elements) == 3

        # Select first and third
        state.select_at(50, 50)
        state.select_at(450, 50, add_to_selection=True)
        assert state.selected_indices == {0, 2}

        # Delete
        result = state.delete_selected()
        assert result is True
        assert len(state.elements) == 1
        assert state.selected_indices == set()

    def test_deselect_clears_all(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        state.select_at(50, 50)
        state.select_at(250, 50, add_to_selection=True)
        assert len(state.selected_indices) == 2

        state.deselect()
        assert state.selected_indices == set()

    def test_resize_handles_only_for_single_selection(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        # Single selection - handles visible
        state.select_at(50, 50)
        assert state._hit_test_handles(12, 12) == 'nw'

        # Multi-selection - no handles
        state.select_at(250, 50, add_to_selection=True)
        assert state._hit_test_handles(12, 12) is None

    def test_selected_index_property_backwards_compat(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        # selected_index property should work for single selection
        assert state.selected_index == 0

    def test_selected_index_none_for_multi(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        state.start_drawing(200, 10)
        state.finish_drawing(300, 100)

        state.select_at(50, 50)
        state.select_at(250, 50, add_to_selection=True)
        # selected_index should be None for multi-selection
        assert state.selected_index is None


class TestArrowStyle:
    """Test ArrowStyle enum and arrow style functionality."""

    def test_arrow_style_open_exists(self):
        assert ArrowStyle.OPEN.value == "open"

    def test_arrow_style_filled_exists(self):
        assert ArrowStyle.FILLED.value == "filled"

    def test_arrow_style_double_exists(self):
        assert ArrowStyle.DOUBLE.value == "double"

    def test_editor_state_initial_arrow_style(self):
        state = EditorState()
        assert state.arrow_style == ArrowStyle.OPEN

    def test_set_arrow_style(self):
        state = EditorState()
        state.set_arrow_style(ArrowStyle.FILLED)
        assert state.arrow_style == ArrowStyle.FILLED

    def test_set_arrow_style_double(self):
        state = EditorState()
        state.set_arrow_style(ArrowStyle.DOUBLE)
        assert state.arrow_style == ArrowStyle.DOUBLE

    def test_drawing_element_default_arrow_style(self):
        element = DrawingElement(tool=ToolType.ARROW)
        assert element.arrow_style == ArrowStyle.OPEN

    def test_drawing_element_custom_arrow_style(self):
        element = DrawingElement(tool=ToolType.ARROW, arrow_style=ArrowStyle.FILLED)
        assert element.arrow_style == ArrowStyle.FILLED

    def test_start_drawing_arrow_includes_style(self):
        state = EditorState()
        state.set_tool(ToolType.ARROW)
        state.set_arrow_style(ArrowStyle.DOUBLE)
        state.start_drawing(10, 10)
        assert state.current_element is not None
        assert state.current_element.arrow_style == ArrowStyle.DOUBLE

    def test_arrow_element_preserves_style_after_finish(self):
        state = EditorState()
        state.set_tool(ToolType.ARROW)
        state.set_arrow_style(ArrowStyle.FILLED)
        state.start_drawing(10, 10)
        state.finish_drawing(100, 100)
        assert len(state.elements) == 1
        assert state.elements[0].arrow_style == ArrowStyle.FILLED


class TestTextFormatting:
    """Test text formatting functionality."""

    def test_editor_state_initial_font_bold(self):
        state = EditorState()
        assert state.font_bold is False

    def test_editor_state_initial_font_italic(self):
        state = EditorState()
        assert state.font_italic is False

    def test_editor_state_initial_font_family(self):
        state = EditorState()
        assert state.font_family == "Sans"

    def test_set_font_bold(self):
        state = EditorState()
        state.set_font_bold(True)
        assert state.font_bold is True

    def test_set_font_italic(self):
        state = EditorState()
        state.set_font_italic(True)
        assert state.font_italic is True

    def test_set_font_family(self):
        state = EditorState()
        state.set_font_family("Monospace")
        assert state.font_family == "Monospace"

    def test_drawing_element_default_font_bold(self):
        element = DrawingElement(tool=ToolType.TEXT)
        assert element.font_bold is False

    def test_drawing_element_default_font_italic(self):
        element = DrawingElement(tool=ToolType.TEXT)
        assert element.font_italic is False

    def test_drawing_element_default_font_family(self):
        element = DrawingElement(tool=ToolType.TEXT)
        assert element.font_family == "Sans"

    def test_drawing_element_custom_font_styles(self):
        element = DrawingElement(
            tool=ToolType.TEXT,
            font_bold=True,
            font_italic=True,
            font_family="Serif",
        )
        assert element.font_bold is True
        assert element.font_italic is True
        assert element.font_family == "Serif"

    def test_add_text_includes_font_styles(self):
        state = EditorState()
        state.set_font_bold(True)
        state.set_font_italic(True)
        state.set_font_family("Monospace")
        state.add_text(50, 50, "Hello")
        assert len(state.elements) == 1
        assert state.elements[0].font_bold is True
        assert state.elements[0].font_italic is True
        assert state.elements[0].font_family == "Monospace"

    def test_start_drawing_includes_font_styles(self):
        state = EditorState()
        state.set_tool(ToolType.TEXT)
        state.set_font_bold(True)
        state.set_font_italic(True)
        state.set_font_family("Serif")
        state.start_drawing(10, 10)
        assert state.current_element is not None
        assert state.current_element.font_bold is True
        assert state.current_element.font_italic is True
        assert state.current_element.font_family == "Serif"


class TestAnnotationSnapping:
    """Test annotation snapping functionality."""

    def test_initial_snap_enabled(self):
        state = EditorState()
        assert state.snap_enabled is True

    def test_initial_snap_threshold(self):
        state = EditorState()
        assert state.snap_threshold == 10.0

    def test_initial_snap_guides_empty(self):
        state = EditorState()
        assert state.active_snap_guides == []

    def test_set_snap_enabled_false(self):
        state = EditorState()
        state.set_snap_enabled(False)
        assert state.snap_enabled is False

    def test_set_snap_enabled_true(self):
        state = EditorState()
        state.set_snap_enabled(False)
        state.set_snap_enabled(True)
        assert state.snap_enabled is True

    def test_get_snap_lines_empty(self):
        state = EditorState()
        h_lines, v_lines = state._get_snap_lines()
        assert h_lines == []
        assert v_lines == []

    def test_get_snap_lines_with_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 20)
        state.finish_drawing(100, 80)

        h_lines, v_lines = state._get_snap_lines()
        # Element at (10,20)-(100,80) gives:
        # h_lines: top=20, bottom=80, center=50
        # v_lines: left=10, right=100, center=55
        assert 20 in h_lines
        assert 80 in h_lines
        assert 50 in h_lines  # center y
        assert 10 in v_lines
        assert 100 in v_lines
        assert 55 in v_lines  # center x

    def test_get_snap_lines_excludes_selected(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 20)
        state.finish_drawing(100, 80)
        state.select_at(50, 50)
        assert state.selected_index == 0

        # With the only element selected, snap lines should be empty
        h_lines, v_lines = state._get_snap_lines()
        assert h_lines == []
        assert v_lines == []

    def test_apply_snap_disabled(self):
        state = EditorState()
        state.set_snap_enabled(False)
        snap_dx, snap_dy = state._apply_snap((10, 20, 100, 80))
        assert snap_dx == 0.0
        assert snap_dy == 0.0

    def test_apply_snap_no_elements(self):
        state = EditorState()
        snap_dx, snap_dy = state._apply_snap((10, 20, 100, 80))
        assert snap_dx == 0.0
        assert snap_dy == 0.0

    def test_apply_snap_clears_guides_first(self):
        state = EditorState()
        state.active_snap_guides = [('h', 50)]
        state._apply_snap((10, 20, 100, 80))
        # Even with no elements, guides should be cleared
        assert state.active_snap_guides == []

    def test_finish_move_clears_snap_guides(self):
        state = EditorState()
        state.active_snap_guides = [('h', 50), ('v', 100)]
        state.finish_move()
        assert state.active_snap_guides == []

    def test_snap_horizontal_alignment(self):
        state = EditorState()
        # Create first element at y=100
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 100)
        state.finish_drawing(50, 150)

        # Create second element near y=100 (within threshold)
        state.start_drawing(200, 95)
        state.finish_drawing(250, 145)

        # Select second element and move it
        state.select_at(225, 120)
        assert state.selected_index == 1

        # Get snap for element near y=100
        bbox = state._get_element_bbox(state.elements[1])
        snap_dx, snap_dy = state._apply_snap(bbox)

        # Should snap to y=100 (dy = 100 - 95 = 5)
        assert snap_dy == 5.0
        assert ('h', 100) in state.active_snap_guides

    def test_snap_vertical_alignment(self):
        state = EditorState()
        # Create first element at x=100
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        # Create second element near x=100 (within threshold)
        state.start_drawing(95, 200)
        state.finish_drawing(145, 250)

        # Select second element
        state.select_at(120, 225)
        assert state.selected_index == 1

        bbox = state._get_element_bbox(state.elements[1])
        snap_dx, snap_dy = state._apply_snap(bbox)

        # Should snap to x=100 (dx = 100 - 95 = 5)
        assert snap_dx == 5.0
        assert ('v', 100) in state.active_snap_guides


class TestKeyboardNudge:
    """Test keyboard nudge functionality."""

    def test_nudge_no_selection_returns_false(self):
        state = EditorState()
        result = state.nudge_selected(10, 0)
        assert result is False

    def test_nudge_moves_single_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        original_points = [(p.x, p.y) for p in state.elements[0].points]

        state.nudge_selected(5, 0)
        new_points = [(p.x, p.y) for p in state.elements[0].points]

        assert new_points[0] == (original_points[0][0] + 5, original_points[0][1])
        assert new_points[1] == (original_points[1][0] + 5, original_points[1][1])

    def test_nudge_moves_multiple_selected(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First element
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        # Second element
        state.start_drawing(100, 100)
        state.finish_drawing(150, 150)

        # Select both
        state.select_at(30, 30)
        state.select_at(125, 125, add_to_selection=True)
        assert len(state.selected_indices) == 2

        orig_elem0 = [(p.x, p.y) for p in state.elements[0].points]
        orig_elem1 = [(p.x, p.y) for p in state.elements[1].points]

        state.nudge_selected(0, -10)

        # Both elements moved up by 10
        for i, p in enumerate(state.elements[0].points):
            assert p.y == orig_elem0[i][1] - 10
        for i, p in enumerate(state.elements[1].points):
            assert p.y == orig_elem1[i][1] - 10

    def test_nudge_saves_undo_state(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        undo_count_before = len(state.undo_stack)

        state.nudge_selected(5, 5)
        assert len(state.undo_stack) == undo_count_before + 1

    def test_nudge_clears_redo_stack(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.select_at(30, 30)

        # Create redo state
        state.nudge_selected(5, 0)
        state.undo()
        assert len(state.redo_stack) > 0

        # Nudge should clear redo
        state.select_at(30, 30)
        state.nudge_selected(0, 5)
        assert len(state.redo_stack) == 0

    def test_nudge_negative_direction(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(100, 100)
        state.finish_drawing(150, 150)

        state.select_at(125, 125)
        orig = [(p.x, p.y) for p in state.elements[0].points]

        state.nudge_selected(-20, -15)

        for i, p in enumerate(state.elements[0].points):
            assert p.x == orig[i][0] - 20
            assert p.y == orig[i][1] - 15

    def test_nudge_returns_true_on_success(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.select_at(30, 30)

        result = state.nudge_selected(1, 1)
        assert result is True


class TestCopyPaste:
    """Test copy/paste annotation functionality."""

    def test_initial_clipboard_empty(self):
        state = EditorState()
        assert state.has_clipboard() is False
        assert state._clipboard == []

    def test_copy_no_selection_returns_false(self):
        state = EditorState()
        result = state.copy_selected()
        assert result is False

    def test_copy_selected_returns_true(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        result = state.copy_selected()
        assert result is True
        assert state.has_clipboard() is True

    def test_copy_creates_deep_copy(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.copy_selected()

        # Modify original
        state.elements[0].points[0].x = 999

        # Clipboard should be unchanged
        assert state._clipboard[0].points[0].x == 10

    def test_paste_no_clipboard_returns_false(self):
        state = EditorState()
        result = state.paste_annotations()
        assert result is False

    def test_paste_creates_new_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.copy_selected()
        assert len(state.elements) == 1

        state.paste_annotations()
        assert len(state.elements) == 2

    def test_paste_applies_offset(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.copy_selected()
        state.paste_annotations(offset=20.0)

        # Original element
        assert state.elements[0].points[0].x == 10
        assert state.elements[0].points[0].y == 10

        # Pasted element should be offset
        assert state.elements[1].points[0].x == 30  # 10 + 20
        assert state.elements[1].points[0].y == 30  # 10 + 20

    def test_paste_selects_new_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.copy_selected()
        state.paste_annotations()

        # Should have selected the pasted element (index 1)
        assert state.selected_indices == {1}

    def test_paste_saves_undo_state(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.copy_selected()
        undo_count_before = len(state.undo_stack)

        state.paste_annotations()
        assert len(state.undo_stack) == undo_count_before + 1

    def test_paste_clears_redo_stack(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.select_at(30, 30)
        state.copy_selected()

        # Create redo state
        state.paste_annotations()
        state.undo()
        assert len(state.redo_stack) > 0

        # Paste again should clear redo
        state.paste_annotations()
        assert len(state.redo_stack) == 0

    def test_copy_multiple_selected(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 100)
        state.finish_drawing(150, 150)

        state.select_at(30, 30)
        state.select_at(125, 125, add_to_selection=True)
        assert len(state.selected_indices) == 2

        state.copy_selected()
        assert len(state._clipboard) == 2

    def test_paste_multiple_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 100)
        state.finish_drawing(150, 150)

        state.select_at(30, 30)
        state.select_at(125, 125, add_to_selection=True)
        state.copy_selected()

        state.paste_annotations()
        assert len(state.elements) == 4
        assert len(state.selected_indices) == 2
        assert state.selected_indices == {2, 3}


class TestRecentColors:
    """Test recent colors functionality."""

    def test_initial_recent_colors_empty(self):
        state = EditorState()
        assert state.recent_colors == []
        assert state.get_recent_colors() == []

    def test_set_color_adds_to_recent(self):
        state = EditorState()
        state.set_color(Color(1.0, 0.0, 0.0))
        assert len(state.recent_colors) == 1
        assert state.recent_colors[0].r == 1.0

    def test_recent_colors_most_recent_first(self):
        state = EditorState()
        state.set_color(Color(1.0, 0.0, 0.0))  # Red
        state.set_color(Color(0.0, 1.0, 0.0))  # Green
        state.set_color(Color(0.0, 0.0, 1.0))  # Blue

        assert len(state.recent_colors) == 3
        assert state.recent_colors[0].b == 1.0  # Blue is most recent
        assert state.recent_colors[1].g == 1.0  # Green
        assert state.recent_colors[2].r == 1.0  # Red

    def test_max_recent_colors_limit(self):
        state = EditorState()
        state.max_recent_colors = 3

        state.set_color(Color(1.0, 0.0, 0.0))
        state.set_color(Color(0.0, 1.0, 0.0))
        state.set_color(Color(0.0, 0.0, 1.0))
        state.set_color(Color(1.0, 1.0, 0.0))  # Should push red out

        assert len(state.recent_colors) == 3
        # Red should be gone, yellow is first
        assert state.recent_colors[0].r == 1.0 and state.recent_colors[0].g == 1.0

    def test_duplicate_color_moves_to_front(self):
        state = EditorState()
        state.set_color(Color(1.0, 0.0, 0.0))  # Red
        state.set_color(Color(0.0, 1.0, 0.0))  # Green
        state.set_color(Color(1.0, 0.0, 0.0))  # Red again

        # Should have 2 colors, red first
        assert len(state.recent_colors) == 2
        assert state.recent_colors[0].r == 1.0 and state.recent_colors[0].g == 0.0
        assert state.recent_colors[1].g == 1.0

    def test_get_recent_colors_returns_copy(self):
        state = EditorState()
        state.set_color(Color(1.0, 0.0, 0.0))

        colors = state.get_recent_colors()
        colors.clear()  # Modify the returned list

        # Original should be unchanged
        assert len(state.recent_colors) == 1

    def test_recent_colors_default_max_is_8(self):
        state = EditorState()
        assert state.max_recent_colors == 8

    def test_add_recent_color_creates_deep_copy(self):
        state = EditorState()
        original = Color(1.0, 0.0, 0.0)
        state.set_color(original)

        # Modify original
        original.r = 0.5

        # Recent color should be unchanged
        assert state.recent_colors[0].r == 1.0


class TestLayerOrdering:
    """Test layer ordering functionality."""

    def test_bring_to_front_no_selection_returns_false(self):
        state = EditorState()
        result = state.bring_to_front()
        assert result is False

    def test_send_to_back_no_selection_returns_false(self):
        state = EditorState()
        result = state.send_to_back()
        assert result is False

    def test_bring_to_front_moves_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 3 elements
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # Index 0
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)  # Index 1
        state.start_drawing(110, 110)
        state.finish_drawing(150, 150)  # Index 2

        # Select first element (index 0)
        state.select_at(30, 30)
        assert state.selected_index == 0

        # Bring to front
        state.bring_to_front()

        # First element should now be at index 2 (last)
        assert 2 in state.selected_indices
        # The moved element should have its original points
        assert state.elements[2].points[0].x == 10

    def test_send_to_back_moves_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 3 elements
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # Index 0
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)  # Index 1
        state.start_drawing(110, 110)
        state.finish_drawing(150, 150)  # Index 2

        # Select last element (index 2)
        state.select_at(130, 130)
        assert state.selected_index == 2

        # Send to back
        state.send_to_back()

        # Last element should now be at index 0 (first)
        assert 0 in state.selected_indices
        # The moved element should have its original points
        assert state.elements[0].points[0].x == 110

    def test_bring_to_front_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)

        state.select_at(30, 30)
        undo_count_before = len(state.undo_stack)

        state.bring_to_front()
        assert len(state.undo_stack) == undo_count_before + 1

    def test_send_to_back_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)

        state.select_at(80, 80)
        undo_count_before = len(state.undo_stack)

        state.send_to_back()
        assert len(state.undo_stack) == undo_count_before + 1

    def test_bring_to_front_clears_redo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)

        state.select_at(30, 30)
        state.bring_to_front()
        state.undo()
        assert len(state.redo_stack) > 0

        state.select_at(30, 30)
        state.bring_to_front()
        assert len(state.redo_stack) == 0

    def test_bring_to_front_multi_select(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 4 elements
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # 0
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)  # 1
        state.start_drawing(110, 110)
        state.finish_drawing(150, 150)  # 2
        state.start_drawing(160, 160)
        state.finish_drawing(200, 200)  # 3

        # Select elements 0 and 1
        state.select_at(30, 30)
        state.select_at(80, 80, add_to_selection=True)
        assert len(state.selected_indices) == 2

        state.bring_to_front()

        # Elements 0 and 1 should now be at indices 2 and 3
        assert state.selected_indices == {2, 3}

    def test_send_to_back_multi_select(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 4 elements
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # 0
        state.start_drawing(60, 60)
        state.finish_drawing(100, 100)  # 1
        state.start_drawing(110, 110)
        state.finish_drawing(150, 150)  # 2
        state.start_drawing(160, 160)
        state.finish_drawing(200, 200)  # 3

        # Select elements 2 and 3
        state.select_at(130, 130)
        state.select_at(180, 180, add_to_selection=True)
        assert len(state.selected_indices) == 2

        state.send_to_back()

        # Elements 2 and 3 should now be at indices 0 and 1
        assert state.selected_indices == {0, 1}


class TestDuplicate:
    """Test duplicate functionality."""

    def test_duplicate_no_selection_returns_false(self):
        state = EditorState()
        result = state.duplicate_selected()
        assert result is False

    def test_duplicate_creates_new_element(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        assert len(state.elements) == 1

        state.duplicate_selected()
        assert len(state.elements) == 2

    def test_duplicate_applies_offset(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.duplicate_selected(offset=15.0)

        # Original
        assert state.elements[0].points[0].x == 10
        # Duplicate with offset
        assert state.elements[1].points[0].x == 25  # 10 + 15

    def test_duplicate_selects_new_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        assert state.selected_indices == {0}

        state.duplicate_selected()
        assert state.selected_indices == {1}

    def test_duplicate_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        undo_count_before = len(state.undo_stack)

        state.duplicate_selected()
        assert len(state.undo_stack) == undo_count_before + 1

    def test_duplicate_clears_redo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.duplicate_selected()
        state.undo()
        assert len(state.redo_stack) > 0

        # Deselect first (undo doesn't reset selection indices)
        state.deselect()
        state.select_at(30, 30)
        state.duplicate_selected()
        assert len(state.redo_stack) == 0

    def test_duplicate_multiple_selected(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 100)
        state.finish_drawing(150, 150)

        state.select_at(30, 30)
        state.select_at(125, 125, add_to_selection=True)
        assert len(state.selected_indices) == 2

        state.duplicate_selected()
        assert len(state.elements) == 4
        assert state.selected_indices == {2, 3}

    def test_duplicate_creates_deep_copy(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        state.duplicate_selected()

        # Modify original
        state.elements[0].points[0].x = 999

        # Duplicate should be unchanged (except for offset)
        assert state.elements[1].points[0].x == 30  # 10 + 20 offset


class TestDistribute:
    """Test distribute horizontal/vertical methods."""

    def test_distribute_horizontal_requires_3_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Only 2 elements
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(140, 50)

        state.select_at(30, 30)
        state.select_at(120, 30, add_to_selection=True)

        result = state.distribute_horizontal()
        assert result is False  # Need at least 3

    def test_distribute_horizontal_with_3_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 3 rectangles at x=10, x=50, x=200 (uneven spacing)
        state.start_drawing(10, 10)
        state.finish_drawing(30, 50)  # center at x=20
        state.start_drawing(50, 10)
        state.finish_drawing(70, 50)  # center at x=60
        state.start_drawing(200, 10)
        state.finish_drawing(220, 50)  # center at x=210

        # Select all 3
        state.select_at(20, 30)
        state.select_at(60, 30, add_to_selection=True)
        state.select_at(210, 30, add_to_selection=True)

        result = state.distribute_horizontal()
        assert result is True

        # First and last should stay in place, middle should be centered
        # Total span: 210 - 20 = 190, spacing = 95
        # Middle should be at x = 20 + 95 = 115 (center)
        # Middle rect points should be at x = 105, 125 (was 50, 70)
        middle = state.elements[1]
        middle_center = (middle.points[0].x + middle.points[1].x) / 2
        assert abs(middle_center - 115) < 1

    def test_distribute_horizontal_preserves_first_last(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First at x=0, last at x=300
        state.start_drawing(0, 0)
        state.finish_drawing(20, 20)
        state.start_drawing(100, 0)
        state.finish_drawing(120, 20)
        state.start_drawing(300, 0)
        state.finish_drawing(320, 20)

        state.select_at(10, 10)
        state.select_at(110, 10, add_to_selection=True)
        state.select_at(310, 10, add_to_selection=True)

        first_center_before = 10
        last_center_before = 310

        state.distribute_horizontal()

        # First and last should be unchanged
        first_center_after = (state.elements[0].points[0].x + state.elements[0].points[1].x) / 2
        last_center_after = (state.elements[2].points[0].x + state.elements[2].points[1].x) / 2
        assert abs(first_center_after - first_center_before) < 0.1
        assert abs(last_center_after - last_center_before) < 0.1

    def test_distribute_vertical_requires_3_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(10, 100)
        state.finish_drawing(50, 140)

        state.select_at(30, 30)
        state.select_at(30, 120, add_to_selection=True)

        result = state.distribute_vertical()
        assert result is False

    def test_distribute_vertical_with_3_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 3 rectangles at y=10, y=50, y=200 (uneven spacing)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 30)  # center at y=20
        state.start_drawing(10, 50)
        state.finish_drawing(50, 70)  # center at y=60
        state.start_drawing(10, 200)
        state.finish_drawing(50, 220)  # center at y=210

        state.select_at(30, 20)
        state.select_at(30, 60, add_to_selection=True)
        state.select_at(30, 210, add_to_selection=True)

        result = state.distribute_vertical()
        assert result is True

        # Middle should be at y = 20 + 95 = 115 (center)
        middle = state.elements[1]
        middle_center = (middle.points[0].y + middle.points[1].y) / 2
        assert abs(middle_center - 115) < 1

    def test_distribute_horizontal_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        for x in [0, 100, 300]:
            state.start_drawing(x, 0)
            state.finish_drawing(x + 20, 20)

        state.select_at(10, 10)
        state.select_at(110, 10, add_to_selection=True)
        state.select_at(310, 10, add_to_selection=True)

        undo_count = len(state.undo_stack)
        state.distribute_horizontal()
        assert len(state.undo_stack) == undo_count + 1

    def test_distribute_vertical_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        for y in [0, 100, 300]:
            state.start_drawing(0, y)
            state.finish_drawing(20, y + 20)

        state.select_at(10, 10)
        state.select_at(10, 110, add_to_selection=True)
        state.select_at(10, 310, add_to_selection=True)

        undo_count = len(state.undo_stack)
        state.distribute_vertical()
        assert len(state.undo_stack) == undo_count + 1

    def test_distribute_horizontal_clears_redo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        for x in [0, 100, 300]:
            state.start_drawing(x, 0)
            state.finish_drawing(x + 20, 20)

        state.select_at(10, 10)
        state.select_at(110, 10, add_to_selection=True)
        state.select_at(310, 10, add_to_selection=True)

        state.distribute_horizontal()
        state.undo()
        assert len(state.redo_stack) > 0

        state.distribute_horizontal()
        assert len(state.redo_stack) == 0

    def test_distribute_no_selection_returns_false(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        for x in [0, 100, 300]:
            state.start_drawing(x, 0)
            state.finish_drawing(x + 20, 20)

        # No selection
        assert state.distribute_horizontal() is False
        assert state.distribute_vertical() is False


class TestAlignment:
    """Test alignment methods."""

    def test_align_left_requires_2_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        assert state.align_left() is False  # Need at least 2

    def test_align_left_moves_to_leftmost(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First at x=10, second at x=100
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(140, 50)

        state.select_at(30, 30)
        state.select_at(120, 30, add_to_selection=True)

        result = state.align_left()
        assert result is True

        # Both should now have left edge at x=10
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        assert abs(bbox0[0] - 10) < 0.1
        assert abs(bbox1[0] - 10) < 0.1

    def test_align_right_moves_to_rightmost(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(200, 50)

        state.select_at(30, 30)
        state.select_at(150, 30, add_to_selection=True)

        result = state.align_right()
        assert result is True

        # Both should now have right edge at x=200
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        assert abs(bbox0[2] - 200) < 0.1
        assert abs(bbox1[2] - 200) < 0.1

    def test_align_top_moves_to_topmost(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(10, 100)
        state.finish_drawing(50, 150)

        state.select_at(30, 30)
        state.select_at(30, 125, add_to_selection=True)

        result = state.align_top()
        assert result is True

        # Both should now have top edge at y=10
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        assert abs(bbox0[1] - 10) < 0.1
        assert abs(bbox1[1] - 10) < 0.1

    def test_align_bottom_moves_to_bottommost(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(10, 100)
        state.finish_drawing(50, 200)

        state.select_at(30, 30)
        state.select_at(30, 150, add_to_selection=True)

        result = state.align_bottom()
        assert result is True

        # Both should now have bottom edge at y=200
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        assert abs(bbox0[3] - 200) < 0.1
        assert abs(bbox1[3] - 200) < 0.1

    def test_align_center_horizontal(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First centered at x=30, second at x=170
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # center x = 30
        state.start_drawing(150, 10)
        state.finish_drawing(190, 50)  # center x = 170

        state.select_at(30, 30)
        state.select_at(170, 30, add_to_selection=True)

        result = state.align_center_horizontal()
        assert result is True

        # Both should now have same center X (average = 100)
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        center0 = (bbox0[0] + bbox0[2]) / 2
        center1 = (bbox1[0] + bbox1[2]) / 2
        assert abs(center0 - center1) < 0.1

    def test_align_center_vertical(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First centered at y=30, second at y=170
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)  # center y = 30
        state.start_drawing(10, 150)
        state.finish_drawing(50, 190)  # center y = 170

        state.select_at(30, 30)
        state.select_at(30, 170, add_to_selection=True)

        result = state.align_center_vertical()
        assert result is True

        # Both should now have same center Y (average = 100)
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        center0 = (bbox0[1] + bbox0[3]) / 2
        center1 = (bbox1[1] + bbox1[3]) / 2
        assert abs(center0 - center1) < 0.1

    def test_align_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(140, 50)

        state.select_at(30, 30)
        state.select_at(120, 30, add_to_selection=True)

        undo_count = len(state.undo_stack)
        state.align_left()
        assert len(state.undo_stack) == undo_count + 1

    def test_align_clears_redo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(140, 50)

        state.select_at(30, 30)
        state.select_at(120, 30, add_to_selection=True)

        state.align_left()
        state.undo()
        assert len(state.redo_stack) > 0

        state.align_right()
        assert len(state.redo_stack) == 0

    def test_align_no_selection_returns_false(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(140, 50)

        # No selection
        assert state.align_left() is False
        assert state.align_right() is False
        assert state.align_top() is False
        assert state.align_bottom() is False
        assert state.align_center_horizontal() is False
        assert state.align_center_vertical() is False


class TestAspectLockResize:
    """Test aspect-locked resize functionality."""

    def test_resize_without_aspect_lock(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)  # 2:1 aspect ratio

        state.select_at(50, 25)
        # Simulate resize handle grab (SE corner)
        state._resize_handle = 'se'
        state._drag_start = Point(50, 25)

        # Resize without aspect lock - can change proportions
        result = state._resize_selected(150, 150, aspect_locked=False)
        assert result is True

        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        # Without lock, aspect ratio can change
        assert abs(width - 150) < 1
        assert abs(height - 150) < 1

    def test_resize_with_aspect_lock_corner(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)  # 2:1 aspect ratio

        state.select_at(50, 25)
        state._resize_handle = 'se'
        state._drag_start = Point(50, 25)

        # Get original aspect ratio
        orig_bbox = state._get_element_bbox(state.elements[0])
        orig_ratio = (orig_bbox[2] - orig_bbox[0]) / (orig_bbox[3] - orig_bbox[1])

        # Resize with aspect lock
        result = state._resize_selected(200, 200, aspect_locked=True)
        assert result is True

        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        new_ratio = width / height

        # With lock, aspect ratio should be preserved
        assert abs(new_ratio - orig_ratio) < 0.1

    def test_resize_with_aspect_lock_horizontal_edge(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)  # 2:1 aspect ratio

        state.select_at(50, 25)
        state._resize_handle = 'e'  # East (right edge)
        state._drag_start = Point(50, 25)

        orig_bbox = state._get_element_bbox(state.elements[0])
        orig_ratio = (orig_bbox[2] - orig_bbox[0]) / (orig_bbox[3] - orig_bbox[1])

        # Resize east edge with aspect lock - should also change height
        result = state._resize_selected(200, 25, aspect_locked=True)
        assert result is True

        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        new_ratio = width / height

        # With lock, aspect ratio should be preserved
        assert abs(new_ratio - orig_ratio) < 0.1

    def test_resize_with_aspect_lock_vertical_edge(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)  # 2:1 aspect ratio

        state.select_at(50, 25)
        state._resize_handle = 's'  # South (bottom edge)
        state._drag_start = Point(50, 25)

        orig_bbox = state._get_element_bbox(state.elements[0])
        orig_ratio = (orig_bbox[2] - orig_bbox[0]) / (orig_bbox[3] - orig_bbox[1])

        # Resize south edge with aspect lock - should also change width
        result = state._resize_selected(50, 100, aspect_locked=True)
        assert result is True

        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        new_ratio = width / height

        # With lock, aspect ratio should be preserved
        assert abs(new_ratio - orig_ratio) < 0.1

    def test_move_selected_passes_aspect_lock(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.select_at(50, 25)
        state._resize_handle = 'se'
        state._drag_start = Point(50, 25)

        # Call move_selected with aspect_locked=True
        result = state.move_selected(200, 200, aspect_locked=True)
        assert result is True

        # Should maintain 2:1 ratio
        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        ratio = width / height
        assert abs(ratio - 2.0) < 0.1

    def test_resize_minimum_size_still_enforced(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        state._resize_handle = 'se'
        state._drag_start = Point(50, 50)

        # Try to resize to very small size
        result = state._resize_selected(5, 5, aspect_locked=True)
        assert result is False  # Should fail due to minimum size

    def test_resize_nw_corner_with_aspect_lock(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(100, 50)
        state.finish_drawing(200, 100)  # 2:1 ratio

        state.select_at(150, 75)
        state._resize_handle = 'nw'
        state._drag_start = Point(150, 75)

        orig_bbox = state._get_element_bbox(state.elements[0])
        orig_ratio = (orig_bbox[2] - orig_bbox[0]) / (orig_bbox[3] - orig_bbox[1])

        # Resize NW corner with aspect lock
        result = state._resize_selected(0, 0, aspect_locked=True)
        assert result is True

        bbox = state._get_element_bbox(state.elements[0])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        new_ratio = width / height

        # SE corner should stay anchored, ratio preserved
        assert abs(bbox[2] - 200) < 1  # Right edge unchanged
        assert abs(bbox[3] - 100) < 1  # Bottom edge unchanged
        assert abs(new_ratio - orig_ratio) < 0.1


class TestGroupUngroup:
    """Test group/ungroup functionality."""

    def test_group_requires_2_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        assert state.group_selected() is False  # Need at least 2

    def test_group_assigns_same_id(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        state.select_at(30, 30)
        state.select_at(125, 30, add_to_selection=True)

        result = state.group_selected()
        assert result is True

        # Both elements should have same group_id
        gid0 = state.elements[0].group_id
        gid1 = state.elements[1].group_id
        assert gid0 is not None
        assert gid0 == gid1

    def test_group_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        state.select_at(30, 30)
        state.select_at(125, 30, add_to_selection=True)

        undo_count = len(state.undo_stack)
        state.group_selected()
        assert len(state.undo_stack) == undo_count + 1

    def test_ungroup_removes_group_id(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        state.select_at(30, 30)
        state.select_at(125, 30, add_to_selection=True)
        state.group_selected()

        # Both should have group_id
        assert state.elements[0].group_id is not None

        result = state.ungroup_selected()
        assert result is True

        # Both should now have no group_id
        assert state.elements[0].group_id is None
        assert state.elements[1].group_id is None

    def test_ungroup_no_groups_returns_false(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)

        state.select_at(30, 30)
        assert state.ungroup_selected() is False

    def test_ungroup_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        state.select_at(30, 30)
        state.select_at(125, 30, add_to_selection=True)
        state.group_selected()

        undo_count = len(state.undo_stack)
        state.ungroup_selected()
        assert len(state.undo_stack) == undo_count + 1

    def test_select_grouped_element_selects_all(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        # Group them
        state.select_at(30, 30)
        state.select_at(125, 30, add_to_selection=True)
        state.group_selected()

        # Deselect
        state.deselect()
        assert len(state.selected_indices) == 0

        # Select just one element - should select both
        state.select_at(30, 30)
        assert len(state.selected_indices) == 2
        assert 0 in state.selected_indices
        assert 1 in state.selected_indices

    def test_select_ungrouped_selects_single(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(10, 10)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 10)
        state.finish_drawing(150, 50)

        # Select just one (not grouped)
        state.select_at(30, 30)
        assert len(state.selected_indices) == 1
        assert 0 in state.selected_indices

    def test_group_move_moves_all(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 0)
        state.finish_drawing(150, 50)

        # Group them
        state.select_at(25, 25)
        state.select_at(125, 25, add_to_selection=True)
        state.group_selected()

        # Deselect and re-select just one
        state.deselect()
        state.select_at(25, 25)

        # Both should be selected due to grouping
        assert len(state.selected_indices) == 2

        # Move
        state.move_selected(50, 50)

        # Both should have moved
        bbox0 = state._get_element_bbox(state.elements[0])
        bbox1 = state._get_element_bbox(state.elements[1])
        # Element 0 should have moved by 25,25 (from center 25,25 to 50,50)
        assert bbox0[0] > 0  # Left edge should have moved right
        assert bbox1[0] > 100  # Element 1 should also have moved

    def test_multiple_groups_independent(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # Create 4 elements
        state.start_drawing(0, 0)
        state.finish_drawing(50, 50)
        state.start_drawing(100, 0)
        state.finish_drawing(150, 50)
        state.start_drawing(200, 0)
        state.finish_drawing(250, 50)
        state.start_drawing(300, 0)
        state.finish_drawing(350, 50)

        # Group 0 and 1
        state.select_at(25, 25)
        state.select_at(125, 25, add_to_selection=True)
        state.group_selected()
        gid_a = state.elements[0].group_id

        # Group 2 and 3
        state.deselect()
        state.select_at(225, 25)
        state.select_at(325, 25, add_to_selection=True)
        state.group_selected()
        gid_b = state.elements[2].group_id

        # Group IDs should be different
        assert gid_a != gid_b

        # Selecting element 0 should select 0 and 1, but not 2 and 3
        state.deselect()
        state.select_at(25, 25)
        assert state.selected_indices == {0, 1}


class TestMatchSize:
    """Test match width/height/size methods."""

    def test_match_width_requires_2_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)
        state.select_at(50, 25)
        assert not state.match_width()

    def test_match_width_resizes_to_first(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First element: 100px wide
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)
        # Second element: 50px wide
        state.start_drawing(200, 0)
        state.finish_drawing(250, 50)

        state.select_at(50, 25)
        state.select_at(225, 25, add_to_selection=True)
        assert state.match_width()

        bbox1 = state._get_element_bbox(state.elements[1])
        width1 = bbox1[2] - bbox1[0]
        assert abs(width1 - 100) < 1  # Should be 100px wide now

    def test_match_height_requires_2_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)
        state.select_at(50, 25)
        assert not state.match_height()

    def test_match_height_resizes_to_first(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First element: 100px tall
        state.start_drawing(0, 0)
        state.finish_drawing(50, 100)
        # Second element: 50px tall
        state.start_drawing(100, 0)
        state.finish_drawing(150, 50)

        state.select_at(25, 50)
        state.select_at(125, 25, add_to_selection=True)
        assert state.match_height()

        bbox1 = state._get_element_bbox(state.elements[1])
        height1 = bbox1[3] - bbox1[1]
        assert abs(height1 - 100) < 1  # Should be 100px tall now

    def test_match_size_requires_2_elements(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)
        state.select_at(50, 25)
        assert not state.match_size()

    def test_match_size_resizes_both_dimensions(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        # First element: 100x80
        state.start_drawing(0, 0)
        state.finish_drawing(100, 80)
        # Second element: 50x50
        state.start_drawing(200, 0)
        state.finish_drawing(250, 50)

        state.select_at(50, 40)
        state.select_at(225, 25, add_to_selection=True)
        assert state.match_size()

        bbox1 = state._get_element_bbox(state.elements[1])
        width1 = bbox1[2] - bbox1[0]
        height1 = bbox1[3] - bbox1[1]
        assert abs(width1 - 100) < 1
        assert abs(height1 - 80) < 1

    def test_match_width_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)
        state.start_drawing(200, 0)
        state.finish_drawing(250, 50)

        initial_undo_count = len(state.undo_stack)
        state.select_at(50, 25)
        state.select_at(225, 25, add_to_selection=True)
        state.match_width()
        assert len(state.undo_stack) == initial_undo_count + 1

    def test_match_width_skips_locked(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)  # 100px wide
        state.start_drawing(200, 0)
        state.finish_drawing(250, 50)  # 50px wide

        # Lock the second element
        state.elements[1].locked = True

        state.select_at(50, 25)
        state.select_at(225, 25, add_to_selection=True)
        state.match_width()

        # Second element should still be 50px wide (locked)
        bbox1 = state._get_element_bbox(state.elements[1])
        width1 = bbox1[2] - bbox1[0]
        assert abs(width1 - 50) < 1


class TestFlip:
    """Test flip horizontal/vertical methods."""

    def test_flip_horizontal_no_selection(self):
        state = EditorState()
        assert not state.flip_horizontal()

    def test_flip_horizontal_mirrors_points(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.select_at(50, 25)
        original_x0 = state.elements[0].points[0].x
        original_x1 = state.elements[0].points[1].x

        assert state.flip_horizontal()

        # Points should be mirrored around center
        new_x0 = state.elements[0].points[0].x
        new_x1 = state.elements[0].points[1].x
        center = (original_x0 + original_x1) / 2
        assert abs(new_x0 - (2 * center - original_x0)) < 0.1
        assert abs(new_x1 - (2 * center - original_x1)) < 0.1

    def test_flip_vertical_no_selection(self):
        state = EditorState()
        assert not state.flip_vertical()

    def test_flip_vertical_mirrors_points(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(50, 100)

        state.select_at(25, 50)
        original_y0 = state.elements[0].points[0].y
        original_y1 = state.elements[0].points[1].y

        assert state.flip_vertical()

        # Points should be mirrored around center
        new_y0 = state.elements[0].points[0].y
        new_y1 = state.elements[0].points[1].y
        center = (original_y0 + original_y1) / 2
        assert abs(new_y0 - (2 * center - original_y0)) < 0.1
        assert abs(new_y1 - (2 * center - original_y1)) < 0.1

    def test_flip_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        initial_undo_count = len(state.undo_stack)
        state.select_at(50, 25)
        state.flip_horizontal()
        assert len(state.undo_stack) == initial_undo_count + 1

    def test_flip_skips_locked(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        # Should return False because all selected are locked
        assert not state.flip_horizontal()


class TestRotate:
    """Test rotation functionality."""

    def test_rotate_no_selection(self):
        state = EditorState()
        assert not state.rotate_selected(90)

    def test_rotate_90_clockwise(self):
        state = EditorState()
        state.set_tool(ToolType.LINE)
        # Horizontal line from (0, 50) to (100, 50)
        state.start_drawing(0, 50)
        state.finish_drawing(100, 50)

        state.select_at(50, 50)
        assert state.rotate_selected(90)

        # After 90° clockwise rotation around center (50, 50):
        # In screen coords (Y-down), clockwise: (0, 50) -> (50, 100), (100, 50) -> (50, 0)
        p0 = state.elements[0].points[0]
        p1 = state.elements[0].points[1]
        assert abs(p0.x - 50) < 0.1
        assert abs(p0.y - 100) < 0.1
        assert abs(p1.x - 50) < 0.1
        assert abs(p1.y - 0) < 0.1

    def test_rotate_90_counter_clockwise(self):
        state = EditorState()
        state.set_tool(ToolType.LINE)
        # Horizontal line from (0, 50) to (100, 50)
        state.start_drawing(0, 50)
        state.finish_drawing(100, 50)

        state.select_at(50, 50)
        assert state.rotate_selected(-90)

        # After 90° counter-clockwise rotation around center (50, 50):
        # In screen coords (Y-down), counter-clockwise: (0, 50) -> (50, 0), (100, 50) -> (50, 100)
        p0 = state.elements[0].points[0]
        p1 = state.elements[0].points[1]
        assert abs(p0.x - 50) < 0.1
        assert abs(p0.y - 0) < 0.1
        assert abs(p1.x - 50) < 0.1
        assert abs(p1.y - 100) < 0.1

    def test_rotate_180(self):
        state = EditorState()
        state.set_tool(ToolType.LINE)
        # Line from (0, 0) to (100, 100)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 100)

        state.select_at(50, 50)
        assert state.rotate_selected(180)

        # After 180° rotation around center (50, 50):
        # (0, 0) -> (100, 100), (100, 100) -> (0, 0)
        p0 = state.elements[0].points[0]
        p1 = state.elements[0].points[1]
        assert abs(p0.x - 100) < 0.1
        assert abs(p0.y - 100) < 0.1
        assert abs(p1.x - 0) < 0.1
        assert abs(p1.y - 0) < 0.1

    def test_rotate_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        initial_undo_count = len(state.undo_stack)
        state.select_at(50, 25)
        state.rotate_selected(45)
        assert len(state.undo_stack) == initial_undo_count + 1

    def test_rotate_skips_locked(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        # Should return False because all selected are locked
        assert not state.rotate_selected(90)


class TestLock:
    """Test lock/unlock functionality."""

    def test_toggle_lock_no_selection(self):
        state = EditorState()
        assert not state.toggle_lock_selected()

    def test_toggle_lock_locks_unlocked(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.select_at(50, 25)
        assert not state.elements[0].locked

        assert state.toggle_lock_selected()
        assert state.elements[0].locked

    def test_toggle_lock_unlocks_locked(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        assert state.toggle_lock_selected()
        assert not state.elements[0].locked

    def test_is_selection_locked_true(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        assert state.is_selection_locked()

    def test_is_selection_locked_false(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.select_at(50, 25)
        assert not state.is_selection_locked()

    def test_locked_element_cannot_be_moved(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)
        state._drag_start = Point(50, 25)

        original_x = state.elements[0].points[0].x
        result = state.move_selected(100, 100)

        assert not result
        assert state.elements[0].points[0].x == original_x

    def test_locked_element_cannot_be_deleted(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        result = state.delete_selected()
        assert not result
        assert len(state.elements) == 1

    def test_locked_element_cannot_be_nudged(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        state.elements[0].locked = True
        state.select_at(50, 25)

        original_x = state.elements[0].points[0].x
        result = state.nudge_selected(10, 10)

        assert not result
        assert state.elements[0].points[0].x == original_x

    def test_toggle_lock_saves_undo(self):
        state = EditorState()
        state.set_tool(ToolType.RECTANGLE)
        state.start_drawing(0, 0)
        state.finish_drawing(100, 50)

        initial_undo_count = len(state.undo_stack)
        state.select_at(50, 25)
        state.toggle_lock_selected()
        assert len(state.undo_stack) == initial_undo_count + 1


class TestGridSnap:
    """Test grid snapping functionality."""

    def test_grid_snap_default_disabled(self):
        state = EditorState()
        assert not state.grid_snap_enabled
        assert state.grid_size == 20

    def test_set_grid_snap_enables(self):
        state = EditorState()
        state.set_grid_snap(True, 25)
        assert state.grid_snap_enabled
        assert state.grid_size == 25

    def test_set_grid_snap_clamps_size(self):
        state = EditorState()
        state.set_grid_snap(True, 1)
        assert state.grid_size == 5  # Minimum

        state.set_grid_snap(True, 200)
        assert state.grid_size == 100  # Maximum

    def test_snap_to_grid_when_disabled(self):
        state = EditorState()
        state.grid_snap_enabled = False
        x, y = state._snap_to_grid(17, 23)
        assert x == 17
        assert y == 23

    def test_snap_to_grid_when_enabled(self):
        state = EditorState()
        state.grid_snap_enabled = True
        state.grid_size = 20

        x, y = state._snap_to_grid(17, 23)
        assert x == 20  # Rounds to nearest 20
        assert y == 20

        x, y = state._snap_to_grid(31, 38)
        assert x == 40
        assert y == 40

    def test_snap_to_grid_exact_values(self):
        state = EditorState()
        state.grid_snap_enabled = True
        state.grid_size = 20

        x, y = state._snap_to_grid(40, 60)
        assert x == 40
        assert y == 60
