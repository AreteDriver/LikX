"""Tests for the GIF recorder module."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest


class TestRecorderModuleImport:
    """Test recorder module imports."""

    def test_module_imports(self):
        """Test that recorder module imports successfully."""
        from src import recorder

        assert hasattr(recorder, "GifRecorder")
        assert hasattr(recorder, "RecordingState")
        assert hasattr(recorder, "RecordingResult")

    def test_recording_state_enum(self):
        """Test RecordingState enum values."""
        from src.recorder import RecordingState

        assert RecordingState.IDLE.value == "idle"
        assert RecordingState.RECORDING.value == "recording"
        assert RecordingState.ENCODING.value == "encoding"
        assert RecordingState.COMPLETED.value == "completed"
        assert RecordingState.ERROR.value == "error"

    def test_recording_result_dataclass(self):
        """Test RecordingResult dataclass."""
        from src.recorder import RecordingResult

        result = RecordingResult(success=True, filepath=Path("/tmp/test.gif"))
        assert result.success is True
        assert result.filepath == Path("/tmp/test.gif")
        assert result.error is None
        assert result.duration == 0.0

    def test_recording_result_with_error(self):
        """Test RecordingResult with error."""
        from src.recorder import RecordingResult

        result = RecordingResult(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"


class TestGifRecorderInit:
    """Test GifRecorder initialization."""

    def test_init_creates_instance(self):
        """Test that GifRecorder can be instantiated."""
        from src.recorder import GifRecorder, RecordingState

        recorder = GifRecorder()
        assert recorder.state == RecordingState.IDLE
        assert recorder.process is None
        assert recorder.temp_video is None

    def test_init_checks_tools(self):
        """Test that init checks for available tools."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "ffmpeg_available")
        assert hasattr(recorder, "wf_recorder_available")
        assert isinstance(recorder.ffmpeg_available, bool)
        assert isinstance(recorder.wf_recorder_available, bool)

    def test_init_detects_display_server(self):
        """Test that init detects display server."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "display_server")


class TestCheckTools:
    """Test tool availability checks."""

    def test_check_ffmpeg_available(self):
        """Test ffmpeg check when available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            recorder = GifRecorder()
            # Force recheck
            result = recorder._check_ffmpeg()
            assert result is True

    def test_check_ffmpeg_not_available(self):
        """Test ffmpeg check when not available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run", side_effect=FileNotFoundError):
            recorder = GifRecorder()
            result = recorder._check_ffmpeg()
            assert result is False

    def test_check_ffmpeg_timeout(self):
        """Test ffmpeg check on timeout."""
        from src.recorder import GifRecorder

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 2)):
            recorder = GifRecorder()
            result = recorder._check_ffmpeg()
            assert result is False

    def test_check_wf_recorder_available(self):
        """Test wf-recorder check when available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            recorder = GifRecorder()
            result = recorder._check_wf_recorder()
            assert result is True

    def test_check_wf_recorder_not_available(self):
        """Test wf-recorder check when not available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run", side_effect=FileNotFoundError):
            recorder = GifRecorder()
            result = recorder._check_wf_recorder()
            assert result is False


class TestIsAvailable:
    """Test is_available method."""

    def test_is_available_returns_tuple(self):
        """Test that is_available returns a tuple."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder.is_available()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_is_available_with_ffmpeg_on_x11(self):
        """Test availability with ffmpeg on X11."""
        from src.recorder import GifRecorder
        from src.capture import DisplayServer

        recorder = GifRecorder()
        recorder.display_server = DisplayServer.X11
        recorder.ffmpeg_available = True

        available, error = recorder.is_available()
        assert available is True
        assert error is None

    def test_is_available_without_ffmpeg_on_x11(self):
        """Test availability without ffmpeg on X11."""
        from src.recorder import GifRecorder
        from src.capture import DisplayServer

        recorder = GifRecorder()
        recorder.display_server = DisplayServer.X11
        recorder.ffmpeg_available = False

        available, error = recorder.is_available()
        assert available is False
        assert "ffmpeg" in error.lower()


class TestRecordingStateTransitions:
    """Test recording state transitions."""

    def test_initial_state_is_idle(self):
        """Test that initial state is IDLE."""
        from src.recorder import GifRecorder, RecordingState

        recorder = GifRecorder()
        assert recorder.state == RecordingState.IDLE

    def test_state_change_callback(self):
        """Test that state change callback is stored."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        callback = MagicMock()

        # The callback is set via start_recording
        recorder._on_state_change = callback
        assert recorder._on_state_change == callback


class TestStartRecording:
    """Test start_recording method."""

    def test_start_recording_returns_tuple(self):
        """Test that start_recording returns success tuple."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        recorder.ffmpeg_available = False
        recorder.wf_recorder_available = False

        result = recorder.start_recording(0, 0, 100, 100)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_start_recording_fails_without_tools(self):
        """Test that start_recording fails without tools."""
        from src.recorder import GifRecorder
        from src.capture import DisplayServer

        recorder = GifRecorder()
        recorder.display_server = DisplayServer.X11
        recorder.ffmpeg_available = False

        success, error = recorder.start_recording(0, 0, 100, 100)
        assert success is False
        assert error is not None


class TestStopRecording:
    """Test stop_recording method."""

    def test_stop_recording_when_not_recording(self):
        """Test stop_recording when not recording."""
        from src.recorder import GifRecorder, RecordingState, RecordingResult

        recorder = GifRecorder()
        recorder.state = RecordingState.IDLE

        result = recorder.stop_recording()
        assert isinstance(result, RecordingResult)
        assert result.success is False

    def test_stop_recording_returns_result(self):
        """Test that stop_recording returns RecordingResult."""
        from src.recorder import GifRecorder, RecordingResult

        recorder = GifRecorder()
        result = recorder.stop_recording()
        assert isinstance(result, RecordingResult)


class TestRecordingRegion:
    """Test recording region handling."""

    def test_region_stored(self):
        """Test that region is stored."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert recorder.region == (0, 0, 0, 0)

    def test_region_tuple_format(self):
        """Test region tuple format."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        # Region should be (x, y, width, height)
        assert len(recorder.region) == 4


class TestConfigIntegration:
    """Test integration with config module."""

    def test_uses_config_fps(self):
        """Test that recorder uses config for FPS."""
        from src.recorder import GifRecorder
        from src import config

        cfg = config.load_config()
        assert "gif_fps" in cfg

    def test_uses_config_quality(self):
        """Test that recorder uses config for quality."""
        from src import config

        cfg = config.load_config()
        assert "gif_quality" in cfg

    def test_uses_config_max_duration(self):
        """Test that recorder uses config for max duration."""
        from src import config

        cfg = config.load_config()
        assert "gif_max_duration" in cfg

    def test_uses_config_dither(self):
        """Test that config has dither setting."""
        from src import config

        cfg = config.load_config()
        assert "gif_dither" in cfg
        assert cfg["gif_dither"] in ["none", "bayer", "floyd_steinberg", "sierra2", "sierra2_4a"]

    def test_uses_config_loop(self):
        """Test that config has loop setting."""
        from src import config

        cfg = config.load_config()
        assert "gif_loop" in cfg
        assert isinstance(cfg["gif_loop"], int)
        assert cfg["gif_loop"] >= 0

    def test_uses_config_optimize(self):
        """Test that config has optimize setting."""
        from src import config

        cfg = config.load_config()
        assert "gif_optimize" in cfg
        assert isinstance(cfg["gif_optimize"], bool)

    def test_uses_config_colors(self):
        """Test that config has colors setting."""
        from src import config

        cfg = config.load_config()
        assert "gif_colors" in cfg
        assert cfg["gif_colors"] in [64, 128, 192, 256]

    def test_uses_config_scale_factor(self):
        """Test that config has scale_factor setting."""
        from src import config

        cfg = config.load_config()
        assert "gif_scale_factor" in cfg
        assert 0.25 <= cfg["gif_scale_factor"] <= 1.0


class TestGifsicleCheck:
    """Test gifsicle availability check."""

    def test_check_gifsicle_method_exists(self):
        """Test that _check_gifsicle method exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "_check_gifsicle")
        assert callable(recorder._check_gifsicle)

    def test_gifsicle_available_attribute(self):
        """Test that gifsicle_available attribute exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "gifsicle_available")
        assert isinstance(recorder.gifsicle_available, bool)

    def test_check_gifsicle_available(self):
        """Test gifsicle check when available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            recorder = GifRecorder()
            result = recorder._check_gifsicle()
            assert result is True

    def test_check_gifsicle_not_available(self):
        """Test gifsicle check when not available."""
        from src.recorder import GifRecorder

        with patch("subprocess.run", side_effect=FileNotFoundError):
            recorder = GifRecorder()
            result = recorder._check_gifsicle()
            assert result is False


class TestDitherOptions:
    """Test dither options helper method."""

    def test_get_dither_options_method_exists(self):
        """Test that _get_dither_options method exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "_get_dither_options")
        assert callable(recorder._get_dither_options)

    def test_get_dither_none(self):
        """Test dither option: none."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("none")
        assert "dither=none" in result

    def test_get_dither_bayer(self):
        """Test dither option: bayer."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("bayer")
        assert "dither=bayer" in result

    def test_get_dither_floyd_steinberg(self):
        """Test dither option: floyd_steinberg."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("floyd_steinberg")
        assert "dither=floyd_steinberg" in result

    def test_get_dither_unknown_defaults_to_bayer(self):
        """Test that unknown dither defaults to bayer."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("unknown_dither")
        assert "dither=bayer" in result


class TestOptimizeGif:
    """Test GIF optimization method."""

    def test_optimize_gif_method_exists(self):
        """Test that _optimize_gif method exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "_optimize_gif")
        assert callable(recorder._optimize_gif)

    def test_optimize_gif_returns_bool(self):
        """Test that _optimize_gif returns boolean."""
        from src.recorder import GifRecorder
        from pathlib import Path

        recorder = GifRecorder()
        recorder.gifsicle_available = False

        # Should return False when gifsicle not available
        result = recorder._optimize_gif(Path("/nonexistent.gif"))
        assert result is False

    def test_optimize_gif_with_gifsicle_not_available(self):
        """Test optimization when gifsicle is not available."""
        from src.recorder import GifRecorder
        from pathlib import Path

        recorder = GifRecorder()
        recorder.gifsicle_available = False

        result = recorder._optimize_gif(Path("/tmp/test.gif"))
        assert result is False


class TestDitherOptionsSierra:
    """Test sierra dither options."""

    def test_get_dither_sierra2(self):
        """Test dither option: sierra2."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("sierra2")
        assert "dither=sierra2" in result

    def test_get_dither_sierra2_4a(self):
        """Test dither option: sierra2_4a."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        result = recorder._get_dither_options("sierra2_4a")
        assert "dither=sierra2_4a" in result


class TestRecorderTempFiles:
    """Test temp file handling."""

    def test_temp_video_attribute(self):
        """Test temp_video attribute exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "temp_video")
        assert recorder.temp_video is None


class TestRecorderWaylandSupport:
    """Test Wayland support detection."""

    def test_display_server_attribute(self):
        """Test display_server attribute exists."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "display_server")

    def test_wf_recorder_availability_check(self):
        """Test wf-recorder availability is checked."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        assert hasattr(recorder, "wf_recorder_available")
        assert isinstance(recorder.wf_recorder_available, bool)


class TestRecordingResultAttributes:
    """Test RecordingResult dataclass attributes."""

    def test_recording_result_with_duration(self):
        """Test RecordingResult with duration."""
        from src.recorder import RecordingResult
        from pathlib import Path

        result = RecordingResult(
            success=True,
            filepath=Path("/tmp/test.gif"),
            duration=5.0
        )
        assert result.duration == 5.0

    def test_recording_result_defaults(self):
        """Test RecordingResult default values."""
        from src.recorder import RecordingResult

        result = RecordingResult(success=False)
        assert result.filepath is None
        assert result.error is None
        assert result.duration == 0.0


class TestRecorderStateCallbacks:
    """Test state change callbacks."""

    def test_on_state_change_callback(self):
        """Test _on_state_change callback can be set."""
        from src.recorder import GifRecorder

        recorder = GifRecorder()
        callback = MagicMock()
        recorder._on_state_change = callback

        assert recorder._on_state_change is callback


class TestRecorderConfigValues:
    """Test config value usage."""

    def test_config_gif_dither_values(self):
        """Test valid dither config values."""
        from src import config

        cfg = config.load_config()
        valid_dithers = ["none", "bayer", "floyd_steinberg", "sierra2", "sierra2_4a"]
        assert cfg["gif_dither"] in valid_dithers

    def test_config_gif_loop_zero_is_infinite(self):
        """Test that loop=0 means infinite."""
        from src import config

        cfg = config.load_config()
        # 0 = infinite loop in GIF spec
        assert cfg["gif_loop"] >= 0
