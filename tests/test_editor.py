"""Tests for editor module."""

import pytest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.editor import (
    ToolType,
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
