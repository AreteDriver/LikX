"""Capture queue manager for batch screenshot editing."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import gi

    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config
from .capture import CaptureMode, CaptureResult


@dataclass
class QueuedCapture:
    """A capture waiting in the queue."""

    result: CaptureResult
    timestamp: datetime
    mode: CaptureMode
    temp_path: Optional[Path] = None


class CaptureQueue:
    """Manages queued screenshots for batch editing."""

    def __init__(self, persist_dir: Optional[Path] = None):
        """Initialize capture queue.

        Args:
            persist_dir: Optional directory for persisting captures across restarts.
                        If None, captures are only held in memory.
        """
        self._queue: List[QueuedCapture] = []
        self._persist_dir = persist_dir
        self._max_queue_size = config.get_setting("queue_max_size", 50)

        if persist_dir:
            self._load_persisted()

    def add(
        self, result: CaptureResult, mode: CaptureMode = CaptureMode.REGION
    ) -> int:
        """Add capture to queue.

        Args:
            result: The capture result to queue.
            mode: The capture mode used.

        Returns:
            Queue position of the added capture.
        """
        if len(self._queue) >= self._max_queue_size:
            self._remove_at(0)

        queued = QueuedCapture(
            result=result,
            timestamp=datetime.now(),
            mode=mode,
        )

        if self._persist_dir:
            queued.temp_path = self._persist_capture(queued)

        self._queue.append(queued)
        return len(self._queue) - 1

    def get_all(self) -> List[CaptureResult]:
        """Get all queued captures as CaptureResults."""
        return [q.result for q in self._queue]

    def pop_all(self) -> List[CaptureResult]:
        """Get all captures and clear queue."""
        results = self.get_all()
        self.clear()
        return results

    def get_at(self, index: int) -> Optional[CaptureResult]:
        """Get capture at index without removing it."""
        if 0 <= index < len(self._queue):
            return self._queue[index].result
        return None

    def clear(self) -> None:
        """Clear the queue."""
        if self._persist_dir:
            for q in self._queue:
                if q.temp_path and q.temp_path.exists():
                    try:
                        q.temp_path.unlink()
                    except OSError:
                        pass
        self._queue.clear()

    def remove(self, index: int) -> bool:
        """Remove item at index.

        Returns:
            True if removed, False if index invalid.
        """
        if 0 <= index < len(self._queue):
            return self._remove_at(index)
        return False

    def _remove_at(self, index: int) -> bool:
        """Remove item at index (internal)."""
        q = self._queue.pop(index)
        if q.temp_path and q.temp_path.exists():
            try:
                q.temp_path.unlink()
            except OSError:
                pass
        return True

    @property
    def count(self) -> int:
        """Number of items in queue."""
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Whether queue is empty."""
        return len(self._queue) == 0

    def _persist_capture(self, queued: QueuedCapture) -> Path:
        """Save capture to temp file for persistence."""
        if not self._persist_dir:
            raise ValueError("Persist directory not set")

        self._persist_dir.mkdir(parents=True, exist_ok=True)
        filename = f"queue_{queued.timestamp.strftime('%Y%m%d_%H%M%S_%f')}.png"
        path = self._persist_dir / filename

        try:
            queued.result.pixbuf.savev(str(path), "png", [], [])
        except Exception:
            return None

        return path

    def _load_persisted(self) -> None:
        """Load persisted captures on startup."""
        if not self._persist_dir or not self._persist_dir.exists():
            return

        if not GTK_AVAILABLE:
            return

        for png_file in sorted(self._persist_dir.glob("queue_*.png")):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(png_file))
                result = CaptureResult(success=True, pixbuf=pixbuf)

                # Parse timestamp from filename
                ts_str = png_file.stem.replace("queue_", "")
                timestamp = datetime.strptime(ts_str, "%Y%m%d_%H%M%S_%f")

                queued = QueuedCapture(
                    result=result,
                    timestamp=timestamp,
                    mode=CaptureMode.REGION,
                    temp_path=png_file,
                )
                self._queue.append(queued)
            except Exception:
                # Skip corrupted files
                try:
                    png_file.unlink()
                except OSError:
                    pass
