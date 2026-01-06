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
