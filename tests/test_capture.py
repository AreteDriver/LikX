"""Tests for capture module."""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capture import (
    CaptureMode,
    DisplayServer,
    CaptureResult,
    detect_display_server,
)


class TestCaptureMode:
    """Test CaptureMode enum."""

    def test_fullscreen_mode(self):
        assert CaptureMode.FULLSCREEN.value == "fullscreen"

    def test_region_mode(self):
        assert CaptureMode.REGION.value == "region"

    def test_window_mode(self):
        assert CaptureMode.WINDOW.value == "window"


class TestDisplayServer:
    """Test DisplayServer enum."""

    def test_x11_server(self):
        assert DisplayServer.X11.value == "x11"

    def test_wayland_server(self):
        assert DisplayServer.WAYLAND.value == "wayland"

    def test_unknown_server(self):
        assert DisplayServer.UNKNOWN.value == "unknown"


class TestCaptureResult:
    """Test CaptureResult class."""

    def test_success_result(self):
        result = CaptureResult(success=True)
        assert result.success is True
        assert bool(result) is True

    def test_failure_result(self):
        result = CaptureResult(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"
        assert bool(result) is False

    def test_result_with_filepath(self):
        path = Path("/tmp/test.png")
        result = CaptureResult(success=True, filepath=path)
        assert result.filepath == path

    def test_result_with_pixbuf(self):
        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)
        assert result.pixbuf == mock_pixbuf


class TestDetectDisplayServer:
    """Test display server detection."""

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland', 'WAYLAND_DISPLAY': 'wayland-0'}, clear=True)
    def test_detect_wayland_from_session_type(self):
        result = detect_display_server()
        assert result == DisplayServer.WAYLAND

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': '', 'WAYLAND_DISPLAY': 'wayland-0'}, clear=True)
    def test_detect_wayland_from_display(self):
        result = detect_display_server()
        assert result == DisplayServer.WAYLAND

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11', 'DISPLAY': ':0'}, clear=True)
    def test_detect_x11(self):
        result = detect_display_server()
        assert result == DisplayServer.X11

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': '', 'WAYLAND_DISPLAY': '', 'DISPLAY': ''}, clear=True)
    def test_detect_unknown(self):
        result = detect_display_server()
        assert result == DisplayServer.UNKNOWN


class TestCaptureFullscreen:
    """Test fullscreen capture."""

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', False)
    def test_capture_returns_error_without_gtk(self, mock_detect):
        from src.capture import capture_fullscreen
        mock_detect.return_value = DisplayServer.X11

        result = capture_fullscreen()
        assert result.success is False
        assert "GTK not available" in result.error


class TestCaptureRegion:
    """Test region capture."""

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', False)
    def test_capture_region_without_gtk(self, mock_detect):
        from src.capture import capture_region
        mock_detect.return_value = DisplayServer.X11

        result = capture_region(0, 0, 100, 100)
        assert result.success is False


class TestCaptureWindow:
    """Test window capture."""

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', False)
    def test_capture_window_without_gtk(self, mock_detect):
        from src.capture import capture_window
        mock_detect.return_value = DisplayServer.X11

        result = capture_window()
        assert result.success is False


class TestSaveCapture:
    """Test save_capture function."""

    def test_save_capture_failed_result(self):
        from src.capture import save_capture

        failed_result = CaptureResult(success=False, error="No screenshot")
        result = save_capture(failed_result)
        assert result.success is False
        assert "No screenshot to save" in result.error

    def test_save_capture_no_pixbuf(self):
        from src.capture import save_capture

        result = CaptureResult(success=True, pixbuf=None)
        save_result = save_capture(result)
        assert save_result.success is False


class TestCopyToClipboard:
    """Test clipboard copy function."""

    def test_copy_failed_result(self):
        from src.capture import copy_to_clipboard

        failed_result = CaptureResult(success=False)
        result = copy_to_clipboard(failed_result)
        assert result is False

    def test_copy_no_pixbuf(self):
        from src.capture import copy_to_clipboard

        result = CaptureResult(success=True, pixbuf=None)
        copy_result = copy_to_clipboard(result)
        assert copy_result is False


class TestCaptureMainFunction:
    """Test main capture function."""

    @patch('src.capture.config.load_config')
    def test_capture_region_without_coordinates(self, mock_config):
        from src.capture import capture, CaptureMode

        mock_config.return_value = {}
        result = capture(CaptureMode.REGION, region=None)
        assert result.success is False
        assert "Region not specified" in result.error
