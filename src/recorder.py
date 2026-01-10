"""GIF screen recording module for LikX."""

import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Tuple

from . import config
from .capture import DisplayServer, detect_display_server


class RecordingState(Enum):
    """Recording state machine."""

    IDLE = "idle"
    RECORDING = "recording"
    ENCODING = "encoding"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class RecordingResult:
    """Result of a recording operation."""

    success: bool
    filepath: Optional[Path] = None
    error: Optional[str] = None
    duration: float = 0.0


class GifRecorder:
    """Handles screen region recording to GIF using ffmpeg or wf-recorder."""

    def __init__(self):
        self.state = RecordingState.IDLE
        self.process: Optional[subprocess.Popen] = None
        self.temp_video: Optional[Path] = None
        self.start_time: float = 0
        self.region: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self._on_state_change: Optional[Callable[[RecordingState], None]] = None

        # Check available tools
        self.display_server = detect_display_server()
        self.ffmpeg_available = self._check_ffmpeg()
        self.wf_recorder_available = self._check_wf_recorder()
        self.gifsicle_available = self._check_gifsicle()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_wf_recorder(self) -> bool:
        """Check if wf-recorder is available (for wlroots Wayland)."""
        try:
            result = subprocess.run(
                ["wf-recorder", "--help"], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_gifsicle(self) -> bool:
        """Check if gifsicle is available for GIF optimization."""
        try:
            result = subprocess.run(
                ["gifsicle", "--version"], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> Tuple[bool, Optional[str]]:
        """Check if recording is available on this system."""
        if self.display_server == DisplayServer.X11:
            if self.ffmpeg_available:
                return True, None
            return (
                False,
                "ffmpeg not installed. Install with: sudo apt install ffmpeg",
            )

        elif self.display_server == DisplayServer.WAYLAND:
            if self.wf_recorder_available:
                return True, None
            if self.ffmpeg_available:
                # ffmpeg can work on some Wayland setups via pipewire
                return True, None
            return (
                False,
                "wf-recorder or ffmpeg not installed. "
                "Install with: sudo apt install wf-recorder",
            )

        return False, "Unknown display server"

    def start_recording(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        on_state_change: Optional[Callable[[RecordingState], None]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Start recording the specified region.

        Args:
            x, y: Top-left corner coordinates
            width, height: Region dimensions
            on_state_change: Callback for state changes

        Returns:
            Tuple of (success, error_message)
        """
        if self.state == RecordingState.RECORDING:
            return False, "Already recording"

        available, error = self.is_available()
        if not available:
            return False, error

        # Enforce minimum region size
        if width < 50 or height < 50:
            return False, "Region too small (minimum 50x50 pixels)"

        self.region = (x, y, width, height)
        self._on_state_change = on_state_change

        # Create temp file for raw video capture
        self.temp_video = Path(tempfile.mktemp(suffix=".mp4"))

        cfg = config.load_config()
        fps = cfg.get("gif_fps", 15)

        try:
            if self.display_server == DisplayServer.X11:
                self.process = self._start_x11_recording(x, y, width, height, fps)
            else:
                self.process = self._start_wayland_recording(x, y, width, height, fps)

            self.state = RecordingState.RECORDING
            self.start_time = time.time()
            self._notify_state_change()
            return True, None

        except Exception as e:
            self.state = RecordingState.ERROR
            return False, str(e)

    def _start_x11_recording(
        self, x: int, y: int, width: int, height: int, fps: int
    ) -> subprocess.Popen:
        """Start ffmpeg x11grab recording."""
        # Ensure even dimensions (required by many codecs)
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        display = os.environ.get("DISPLAY", ":0")

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f",
            "x11grab",
            "-framerate",
            str(fps),
            "-video_size",
            f"{width}x{height}",
            "-i",
            f"{display}+{x},{y}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "18",
            str(self.temp_video),
        ]

        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

    def _start_wayland_recording(
        self, x: int, y: int, width: int, height: int, fps: int
    ) -> subprocess.Popen:
        """Start wf-recorder for Wayland."""
        # Ensure even dimensions
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        if self.wf_recorder_available:
            geometry = f"{x},{y} {width}x{height}"
            cmd = [
                "wf-recorder",
                "-g",
                geometry,
                "-r",
                str(fps),
                "-c",
                "libx264",
                "-f",
                str(self.temp_video),
            ]
        else:
            # Fallback to ffmpeg with pipewire (experimental)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "pipewire",
                "-framerate",
                str(fps),
                "-i",
                "default",
                "-vf",
                f"crop={width}:{height}:{x}:{y}",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                str(self.temp_video),
            ]

        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

    def stop_recording(self) -> RecordingResult:
        """Stop recording and encode to GIF.

        Returns:
            RecordingResult with the output filepath or error.
        """
        if self.state != RecordingState.RECORDING or self.process is None:
            return RecordingResult(False, error="Not currently recording")

        duration = time.time() - self.start_time

        # Send SIGINT to gracefully stop recording
        try:
            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        except Exception as e:
            return RecordingResult(False, error=f"Failed to stop recording: {e}")

        # Verify temp video exists
        if not self.temp_video or not self.temp_video.exists():
            self.state = RecordingState.ERROR
            return RecordingResult(False, error="Recording file not created")

        # Encode to GIF
        self.state = RecordingState.ENCODING
        self._notify_state_change()

        result = self._encode_to_gif(duration)

        # Cleanup temp video
        if self.temp_video and self.temp_video.exists():
            self.temp_video.unlink()

        if result.success:
            self.state = RecordingState.COMPLETED
        else:
            self.state = RecordingState.ERROR
        self._notify_state_change()

        return result

    def _encode_to_gif(self, duration: float) -> RecordingResult:
        """Encode temp video to optimized GIF using ffmpeg palette generation."""
        cfg = config.load_config()
        quality = cfg.get("gif_quality", "medium")
        colors = cfg.get("gif_colors", 256)
        scale = cfg.get("gif_scale_factor", 1.0)
        fps = cfg.get("gif_fps", 15)
        dither = cfg.get("gif_dither", "bayer")
        loop_count = cfg.get("gif_loop", 0)
        optimize = cfg.get("gif_optimize", True)

        # Apply quality presets
        if quality == "low":
            fps, colors, scale = 10, 128, 0.75
        elif quality == "high":
            fps, colors, scale = 24, 256, 1.0

        # Generate output path
        output_path = config.get_save_path(format_str="gif")

        # Build filter for scaling
        filters = []
        if scale < 1.0:
            width = self.region[2]
            new_w = int(width * scale)
            new_w = new_w if new_w % 2 == 0 else new_w - 1
            filters.append(f"scale={new_w}:-1:flags=lanczos")

        filters.append(f"fps={fps}")
        filter_str = ",".join(filters) if filters else f"fps={fps}"

        # Build dither string for paletteuse
        dither_opts = self._get_dither_options(dither)

        # Two-pass encoding for optimal GIF quality with palette
        palette_path = Path(tempfile.mktemp(suffix=".png"))

        try:
            # Pass 1: Generate palette
            palette_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(self.temp_video),
                "-vf",
                f"{filter_str},palettegen=max_colors={colors}:stats_mode=diff",
                str(palette_path),
            ]

            result = subprocess.run(palette_cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                return RecordingResult(
                    False,
                    error=f"Palette generation failed: {result.stderr.decode()[:200]}",
                )

            # Pass 2: Encode GIF with palette
            gif_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(self.temp_video),
                "-i",
                str(palette_path),
                "-lavfi",
                f"{filter_str} [x]; [x][1:v] paletteuse={dither_opts}",
                "-loop",
                str(loop_count),
                str(output_path),
            ]

            result = subprocess.run(gif_cmd, capture_output=True, timeout=120)
            if result.returncode != 0:
                return RecordingResult(
                    False,
                    error=f"GIF encoding failed: {result.stderr.decode()[:200]}",
                )

            # Optional: Optimize with gifsicle
            if optimize and self.gifsicle_available:
                self._optimize_gif(output_path)

            return RecordingResult(True, filepath=output_path, duration=duration)

        except subprocess.TimeoutExpired:
            return RecordingResult(False, error="GIF encoding timed out")
        except Exception as e:
            return RecordingResult(False, error=f"Encoding error: {e}")
        finally:
            if palette_path.exists():
                palette_path.unlink()

    def _get_dither_options(self, dither: str) -> str:
        """Get ffmpeg paletteuse dither options string."""
        dither_map = {
            "none": "dither=none",
            "bayer": "dither=bayer:bayer_scale=5",
            "floyd_steinberg": "dither=floyd_steinberg",
            "sierra2": "dither=sierra2",
            "sierra2_4a": "dither=sierra2_4a",
        }
        return dither_map.get(dither, "dither=bayer:bayer_scale=5")

    def _optimize_gif(self, gif_path: Path) -> bool:
        """Optimize GIF file size using gifsicle."""
        try:
            # gifsicle optimization: -O3 for best compression
            temp_optimized = gif_path.with_suffix(".opt.gif")
            cmd = [
                "gifsicle",
                "-O3",
                "--colors",
                "256",
                "-o",
                str(temp_optimized),
                str(gif_path),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and temp_optimized.exists():
                # Replace original with optimized version
                temp_optimized.replace(gif_path)
                return True
            # Clean up on failure
            if temp_optimized.exists():
                temp_optimized.unlink()
            return False
        except Exception:
            return False

    def cancel(self) -> None:
        """Cancel recording without saving."""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=2)
            except Exception:
                pass

        if self.temp_video and self.temp_video.exists():
            self.temp_video.unlink()

        self.state = RecordingState.IDLE
        self._notify_state_change()

    def get_elapsed_time(self) -> float:
        """Get current recording duration in seconds."""
        if self.state == RecordingState.RECORDING:
            return time.time() - self.start_time
        return 0.0

    def _notify_state_change(self) -> None:
        """Notify state change callback."""
        if self._on_state_change:
            try:
                self._on_state_change(self.state)
            except Exception:
                pass
