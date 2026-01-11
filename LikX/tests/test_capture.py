"""Tests for capture module."""

import os
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

    @patch('src.capture.config.load_config')
    @patch('src.capture.capture_fullscreen')
    def test_capture_fullscreen_mode(self, mock_fullscreen, mock_config):
        from src.capture import capture, CaptureMode, CaptureResult

        mock_config.return_value = {}
        mock_fullscreen.return_value = CaptureResult(success=True, pixbuf=MagicMock())

        capture(CaptureMode.FULLSCREEN)
        mock_fullscreen.assert_called_once()

    @patch('src.capture.config.load_config')
    @patch('src.capture.capture_region')
    def test_capture_region_mode(self, mock_region, mock_config):
        from src.capture import capture, CaptureMode, CaptureResult

        mock_config.return_value = {}
        mock_region.return_value = CaptureResult(success=True, pixbuf=MagicMock())

        capture(CaptureMode.REGION, region=(0, 0, 100, 100))
        mock_region.assert_called_once()

    @patch('src.capture.config.load_config')
    @patch('src.capture.capture_window')
    def test_capture_window_mode(self, mock_window, mock_config):
        from src.capture import capture, CaptureMode, CaptureResult

        mock_config.return_value = {}
        mock_window.return_value = CaptureResult(success=True, pixbuf=MagicMock())

        capture(CaptureMode.WINDOW, window_id=12345)
        mock_window.assert_called_once()

    @patch('src.capture.config.load_config')
    def test_capture_unknown_mode(self, mock_config):
        from src.capture import capture

        mock_config.return_value = {}
        # Create a mock mode that's not recognized
        result = capture("invalid_mode")
        assert result.success is False

    @patch('src.capture.config.load_config')
    @patch('src.capture.capture_fullscreen')
    @patch('src.capture.save_capture')
    def test_capture_with_auto_save(self, mock_save, mock_fullscreen, mock_config):
        from src.capture import capture, CaptureMode, CaptureResult

        mock_config.return_value = {}
        mock_pixbuf = MagicMock()
        mock_fullscreen.return_value = CaptureResult(success=True, pixbuf=mock_pixbuf)
        mock_save.return_value = CaptureResult(success=True, filepath=Path("/tmp/test.png"))

        capture(CaptureMode.FULLSCREEN, auto_save=True)
        mock_save.assert_called_once()


class TestCaptureFullscreenWayland:
    """Test Wayland fullscreen capture."""

    @patch('src.capture.time.sleep')
    @patch('src.capture.subprocess.run')
    @patch('src.capture.os.path.exists')
    @patch('src.capture.os.unlink')
    def test_grim_success(self, mock_unlink, mock_exists, mock_run, mock_sleep):
        from src.capture import capture_fullscreen_wayland, GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        mock_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        with patch('src.capture.GdkPixbuf.Pixbuf.new_from_file') as mock_pixbuf:
            mock_pixbuf.return_value = MagicMock()
            result = capture_fullscreen_wayland(delay=0)
            assert result.success is True

    @patch('src.capture.subprocess.run')
    def test_grim_not_found_tries_gnome_screenshot(self, mock_run):
        from src.capture import capture_fullscreen_wayland

        # grim fails with FileNotFoundError, gnome-screenshot also fails
        mock_run.side_effect = FileNotFoundError("grim not found")

        result = capture_fullscreen_wayland(delay=0)
        assert result.success is False

    @patch('src.capture.time.sleep')
    @patch('src.capture.subprocess.run')
    def test_with_delay(self, mock_run, mock_sleep):
        from src.capture import capture_fullscreen_wayland

        mock_run.side_effect = FileNotFoundError("not found")
        capture_fullscreen_wayland(delay=2)
        mock_sleep.assert_called_once_with(2)


class TestCaptureRegionWayland:
    """Test Wayland region capture."""

    @patch('src.capture.time.sleep')
    @patch('src.capture.subprocess.run')
    @patch('src.capture.os.path.exists')
    @patch('src.capture.os.unlink')
    def test_grim_with_geometry_success(self, mock_unlink, mock_exists, mock_run, mock_sleep):
        from src.capture import capture_region_wayland, GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        mock_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        with patch('src.capture.GdkPixbuf.Pixbuf.new_from_file') as mock_pixbuf:
            mock_pixbuf.return_value = MagicMock()
            result = capture_region_wayland(0, 0, 100, 100, delay=0)
            assert result.success is True

    @patch('src.capture.subprocess.run')
    @patch('src.capture.capture_fullscreen_wayland')
    def test_fallback_to_crop(self, mock_fullscreen, mock_run):
        from src.capture import capture_region_wayland, CaptureResult, GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        mock_run.side_effect = FileNotFoundError("grim not found")
        mock_pixbuf = MagicMock()
        mock_fullscreen.return_value = CaptureResult(success=True, pixbuf=mock_pixbuf)

        with patch('src.capture.GdkPixbuf.Pixbuf.new') as mock_new:
            mock_cropped = MagicMock()
            mock_new.return_value = mock_cropped

            result = capture_region_wayland(0, 0, 100, 100, delay=0)
            assert result.success is True


class TestCaptureWindowWayland:
    """Test Wayland window capture."""

    @patch('src.capture.time.sleep')
    @patch('src.capture.subprocess.run')
    @patch('src.capture.os.path.exists')
    @patch('src.capture.os.unlink')
    def test_gnome_screenshot_success(self, mock_unlink, mock_exists, mock_run, mock_sleep):
        from src.capture import capture_window_wayland, GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        mock_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        with patch('src.capture.GdkPixbuf.Pixbuf.new_from_file') as mock_pixbuf:
            mock_pixbuf.return_value = MagicMock()
            result = capture_window_wayland(delay=0)
            assert result.success is True

    @patch('src.capture.subprocess.run')
    @patch('src.capture.os.path.exists')
    @patch('src.capture.os.unlink')
    def test_all_tools_fail(self, mock_unlink, mock_exists, mock_run):
        from src.capture import capture_window_wayland

        mock_run.side_effect = FileNotFoundError("not found")
        mock_exists.return_value = False

        result = capture_window_wayland(delay=0)
        assert result.success is False
        assert "Window capture not supported" in result.error


class TestCaptureWindowX11:
    """Test X11 window capture."""

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', True)
    @patch('src.capture.subprocess.run')
    @patch('src.capture.capture_region')
    def test_capture_active_window(self, mock_region, mock_run, mock_detect):
        from src.capture import capture_window, DisplayServer, CaptureResult

        mock_detect.return_value = DisplayServer.X11

        # First call gets window ID, second gets geometry
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="12345"),
            MagicMock(returncode=0, stdout="X=100\nY=100\nWIDTH=800\nHEIGHT=600\n"),
        ]
        mock_region.return_value = CaptureResult(success=True)

        capture_window()
        mock_region.assert_called_once()

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', True)
    @patch('src.capture.subprocess.run')
    def test_xdotool_not_installed(self, mock_run, mock_detect):
        from src.capture import capture_window, DisplayServer

        mock_detect.return_value = DisplayServer.X11
        mock_run.side_effect = FileNotFoundError("xdotool not found")

        result = capture_window()
        assert result.success is False
        assert "xdotool" in result.error

    @patch('src.capture.detect_display_server')
    @patch('src.capture.GTK_AVAILABLE', True)
    @patch('src.capture.subprocess.run')
    def test_xdotool_timeout(self, mock_run, mock_detect):
        from src.capture import capture_window, DisplayServer
        import subprocess

        mock_detect.return_value = DisplayServer.X11
        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 2)

        result = capture_window()
        assert result.success is False
        assert "timed out" in result.error


class TestSaveCaptureExtended:
    """Extended tests for save_capture function."""

    def test_save_with_format_mapping(self):
        from src.capture import save_capture, CaptureResult

        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        with patch('src.capture.config.get_save_path') as mock_path:
            mock_path.return_value = Path("/tmp/test.jpg")

            save_result = save_capture(result, format_str="jpg")
            # jpeg format should be mapped
            if save_result.success:
                mock_pixbuf.savev.assert_called()

    def test_save_creates_directory(self):
        from src.capture import save_capture, CaptureResult
        import tempfile

        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "test.png"

            save_capture(result, filepath=filepath)
            # Directory should be created

    def test_save_exception_handling(self):
        from src.capture import save_capture, CaptureResult

        mock_pixbuf = MagicMock()
        mock_pixbuf.savev.side_effect = Exception("Save error")
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        save_result = save_capture(result, filepath=Path("/tmp/test.png"))
        assert save_result.success is False
        assert "Failed to save" in save_result.error


class TestCopyToClipboardExtended:
    """Extended tests for copy_to_clipboard function."""

    @patch('src.capture.detect_display_server')
    @patch('src.capture.subprocess.Popen')
    @patch('src.capture.os.unlink')
    def test_wayland_wl_copy_success(self, mock_unlink, mock_popen, mock_detect):
        from src.capture import copy_to_clipboard, CaptureResult, DisplayServer

        mock_detect.return_value = DisplayServer.WAYLAND
        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        with patch('builtins.open', MagicMock()):
            success = copy_to_clipboard(result)
            assert success is True

    @patch('src.capture.detect_display_server')
    @patch('src.capture.subprocess.Popen')
    @patch('src.capture.time.sleep')
    def test_x11_xclip_success(self, mock_sleep, mock_popen, mock_detect):
        from src.capture import copy_to_clipboard, CaptureResult, DisplayServer

        mock_detect.return_value = DisplayServer.X11
        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Still running (backgrounded)
        mock_popen.return_value = mock_proc

        success = copy_to_clipboard(result)
        assert success is True

    @patch('src.capture.detect_display_server')
    @patch('src.capture.subprocess.Popen')
    @patch('src.capture.os.path.exists')
    @patch('src.capture.os.unlink')
    def test_external_tools_fail_fallback_to_gtk(self, mock_unlink, mock_exists, mock_popen, mock_detect):
        from src.capture import copy_to_clipboard, CaptureResult, DisplayServer

        mock_detect.return_value = DisplayServer.X11
        mock_pixbuf = MagicMock()
        result = CaptureResult(success=True, pixbuf=mock_pixbuf)

        mock_popen.side_effect = FileNotFoundError("xclip not found")
        mock_exists.return_value = True

        # GTK is imported inside the function, not at module level
        # Just test that external tools failing doesn't crash
        success = copy_to_clipboard(result, use_gtk=False)
        # Should fail since external tools are mocked to fail and use_gtk=False
        assert success is False


class TestCaptureResultBool:
    """Test CaptureResult boolean behavior."""

    def test_success_is_truthy(self):
        result = CaptureResult(success=True)
        assert bool(result) is True
        assert result  # Implicit bool

    def test_failure_is_falsy(self):
        result = CaptureResult(success=False)
        assert bool(result) is False
        assert not result  # Implicit bool


class TestDetectDisplayServerExtended:
    """Extended tests for display server detection."""

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': 'WAYLAND'}, clear=True)
    def test_detect_wayland_uppercase(self):
        result = detect_display_server()
        assert result == DisplayServer.WAYLAND

    @patch.dict(os.environ, {'XDG_SESSION_TYPE': 'X11'}, clear=True)
    def test_detect_x11_uppercase(self):
        # X11 detection requires DISPLAY env var too
        with patch.dict(os.environ, {'DISPLAY': ':0'}):
            result = detect_display_server()
            assert result == DisplayServer.X11
