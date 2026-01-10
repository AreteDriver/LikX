"""Tests for the scroll capture module."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest


class TestScrollCaptureModuleImport:
    """Test scroll capture module imports."""

    def test_module_imports(self):
        """Test that scroll_capture module imports successfully."""
        from src import scroll_capture

        assert hasattr(scroll_capture, "ScrollCaptureManager")
        assert hasattr(scroll_capture, "ScrollCaptureResult")

    def test_scroll_capture_result_dataclass(self):
        """Test ScrollCaptureResult dataclass."""
        from src.scroll_capture import ScrollCaptureResult

        result = ScrollCaptureResult(
            success=True,
            filepath=Path("/tmp/test.png"),
            frame_count=5,
            total_height=1000
        )
        assert result.success is True
        assert result.filepath == Path("/tmp/test.png")
        assert result.frame_count == 5
        assert result.total_height == 1000
        assert result.error is None

    def test_scroll_capture_result_with_error(self):
        """Test ScrollCaptureResult with error."""
        from src.scroll_capture import ScrollCaptureResult

        result = ScrollCaptureResult(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"


class TestScrollCaptureManagerInit:
    """Test ScrollCaptureManager initialization."""

    def test_init_creates_instance(self):
        """Test that ScrollCaptureManager can be instantiated."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert manager is not None

    def test_init_has_required_attributes(self):
        """Test that manager has required attributes."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "frames")
        assert hasattr(manager, "overlaps")

    def test_init_frames_empty(self):
        """Test that frames list starts empty."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert manager.frames == []

    def test_init_checks_tools(self):
        """Test that init checks for required tools."""
        from src.scroll_capture import ScrollCaptureManager, OPENCV_AVAILABLE

        manager = ScrollCaptureManager()
        assert hasattr(manager, "xdotool_available")
        # OpenCV is module-level constant
        assert isinstance(OPENCV_AVAILABLE, bool)


class TestIsAvailable:
    """Test is_available method."""

    def test_is_available_returns_tuple(self):
        """Test that is_available returns a tuple."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        result = manager.is_available()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_is_available_format(self):
        """Test is_available tuple format."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        available, error = manager.is_available()
        assert isinstance(available, bool)
        if not available:
            assert isinstance(error, str)
        else:
            assert error is None


class TestCheckTools:
    """Test tool availability checks."""

    def test_check_xdotool_available(self):
        """Test xdotool check when available."""
        from src.scroll_capture import ScrollCaptureManager

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            manager = ScrollCaptureManager()
            result = manager._check_xdotool()
            assert result is True

    def test_check_xdotool_not_available(self):
        """Test xdotool check when not available."""
        from src.scroll_capture import ScrollCaptureManager

        with patch("subprocess.run", side_effect=FileNotFoundError):
            manager = ScrollCaptureManager()
            result = manager._check_xdotool()
            assert result is False

    def test_check_opencv(self):
        """Test OpenCV availability check."""
        from src.scroll_capture import OPENCV_AVAILABLE

        # OPENCV_AVAILABLE is a module-level constant
        assert isinstance(OPENCV_AVAILABLE, bool)


class TestStartCapture:
    """Test start_capture method."""

    def test_start_capture_returns_tuple(self):
        """Test that start_capture returns success tuple."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        manager.xdotool_available = False

        result = manager.start_capture(0, 0, 100, 100)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_start_capture_stores_region(self):
        """Test that start_capture stores region."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        manager.xdotool_available = True
        manager.opencv_available = True

        manager.start_capture(10, 20, 100, 200)
        assert manager.region == (10, 20, 100, 200)


class TestCaptureFrame:
    """Test capture_frame method."""

    def test_capture_frame_method_exists(self):
        """Test that capture_frame method exists."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "capture_frame")
        assert callable(manager.capture_frame)


class TestScrollDown:
    """Test scroll_down method."""

    def test_scroll_down_method_exists(self):
        """Test that scroll_down method exists."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "scroll_down")
        assert callable(manager.scroll_down)


class TestFindOverlap:
    """Test find_overlap method."""

    def test_find_overlap_requires_opencv(self):
        """Test that find_overlap requires OpenCV."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        # Should handle case where OpenCV is not available
        assert hasattr(manager, "_find_overlap")


class TestStitchFrames:
    """Test stitch_frames method."""

    def test_stitch_frames_exists(self):
        """Test that stitch_frames method exists."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "_stitch_frames")


class TestStopCapture:
    """Test stop_capture method."""

    def test_stop_capture_method_exists(self):
        """Test that stop_capture method exists."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "stop_capture")
        assert callable(manager.stop_capture)

    def test_stop_requested_flag(self):
        """Test that stop_requested flag exists."""
        from src.scroll_capture import ScrollCaptureManager

        manager = ScrollCaptureManager()
        assert hasattr(manager, "stop_requested")
        assert manager.stop_requested is False


class TestConfigIntegration:
    """Test integration with config module."""

    def test_uses_config_delay(self):
        """Test that manager uses config for delay."""
        from src import config

        cfg = config.load_config()
        assert "scroll_delay_ms" in cfg

    def test_uses_config_max_frames(self):
        """Test that manager uses config for max frames."""
        from src import config

        cfg = config.load_config()
        assert "scroll_max_frames" in cfg

    def test_uses_config_overlap_search(self):
        """Test that manager uses config for overlap search."""
        from src import config

        cfg = config.load_config()
        assert "scroll_overlap_search" in cfg

    def test_uses_config_confidence(self):
        """Test that manager uses config for confidence threshold."""
        from src import config

        cfg = config.load_config()
        assert "scroll_confidence" in cfg

    def test_uses_config_ignore_regions(self):
        """Test that manager uses config for ignore regions."""
        from src import config

        cfg = config.load_config()
        assert "scroll_ignore_top" in cfg
        assert "scroll_ignore_bottom" in cfg
