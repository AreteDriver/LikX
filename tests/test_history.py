"""Tests for history module."""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHistoryModuleAvailability:
    """Test history module can be imported."""

    def test_history_module_imports(self):
        from src import history
        assert history is not None

    def test_history_entry_class_exists(self):
        from src.history import HistoryEntry
        assert HistoryEntry is not None

    def test_history_manager_class_exists(self):
        from src.history import HistoryManager
        assert HistoryManager is not None

    def test_gtk_available_flag_exists(self):
        from src.history import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)


class TestHistoryEntry:
    """Test HistoryEntry class."""

    def test_create_entry(self):
        from src.history import HistoryEntry

        filepath = Path("/path/to/image.png")
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry = HistoryEntry(filepath, timestamp, mode="fullscreen")

        assert entry.filepath == filepath
        assert entry.timestamp == timestamp
        assert entry.mode == "fullscreen"

    def test_default_mode(self):
        from src.history import HistoryEntry

        entry = HistoryEntry(Path("/test.png"), datetime.now())
        # Default mode is "unknown"
        assert entry.mode == "unknown"

    def test_to_dict(self):
        from src.history import HistoryEntry

        filepath = Path("/path/to/image.png")
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry = HistoryEntry(filepath, timestamp, "region")

        d = entry.to_dict()

        assert isinstance(d, dict)
        assert d["filepath"] == "/path/to/image.png"
        assert d["timestamp"] == "2024-01-15T10:30:00"
        assert d["mode"] == "region"

    def test_from_dict(self):
        from src.history import HistoryEntry

        data = {
            "filepath": "/path/to/image.png",
            "timestamp": "2024-01-15T10:30:00",
            "mode": "window"
        }

        entry = HistoryEntry.from_dict(data)

        assert entry.filepath == Path("/path/to/image.png")
        assert entry.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert entry.mode == "window"

    def test_from_dict_default_mode(self):
        from src.history import HistoryEntry

        data = {
            "filepath": "/path/to/image.png",
            "timestamp": "2024-01-15T10:30:00"
        }

        entry = HistoryEntry.from_dict(data)

        assert entry.mode == "unknown"

    def test_thumbnail_attribute(self):
        from src.history import HistoryEntry

        entry = HistoryEntry(Path("/test.png"), datetime.now())
        assert entry.thumbnail is None


class TestHistoryManager:
    """Test HistoryManager class."""

    @patch("src.history.config.get_config_dir")
    def test_init(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            assert manager is not None
            assert isinstance(manager.entries, list)

    @patch("src.history.config.get_config_dir")
    def test_load_empty_history(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            assert manager.entries == []

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_entry(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            # Create a fake screenshot file
            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()

            manager.add(fake_file, "fullscreen")

            assert len(manager.entries) == 1
            assert manager.entries[0].filepath == fake_file
            assert manager.entries[0].mode == "fullscreen"

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_multiple_entries(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            for i in range(5):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            assert len(manager.entries) == 5

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_entries_ordered_most_recent_first(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            for i in range(3):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            # Most recent should be first (test2.png)
            assert "test2" in str(manager.entries[0].filepath)

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_remove_entry(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "fullscreen")

            entry = manager.entries[0]
            manager.remove(entry)

            assert len(manager.entries) == 0

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_remove_nonexistent_entry(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager, HistoryEntry
            manager = HistoryManager()

            # Create entry that's not in the list
            fake_entry = HistoryEntry(Path("/nonexistent.png"), datetime.now())

            # Should not raise
            manager.remove(fake_entry)

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_clear_all(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            for i in range(5):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            manager.clear()

            assert len(manager.entries) == 0

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_get_recent(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            for i in range(10):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            recent = manager.get_recent(5)
            assert len(recent) == 5

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_get_recent_default_limit(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            for i in range(30):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            recent = manager.get_recent()  # Default is 20
            assert len(recent) == 20

    @patch("src.history.config.get_config_dir")
    def test_load_corrupted_file(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            # Create corrupted history file
            history_file = Path(tmpdir) / "history.json"
            history_file.write_text("not valid json {{{")

            from src.history import HistoryManager
            manager = HistoryManager()

            # Should handle gracefully
            assert manager.entries == []

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_max_entries_limit(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            # Add more than 100 entries
            for i in range(150):
                fake_file = Path(tmpdir) / f"test{i}.png"
                fake_file.touch()
                manager.add(fake_file, "fullscreen")

            # Should be limited to 100
            assert len(manager.entries) == 100

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_persistence(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager

            # Add with first manager
            manager1 = HistoryManager()
            manager1.add(fake_file, "fullscreen")

            # Create new manager - should load existing
            manager2 = HistoryManager()

            assert len(manager2.entries) == 1
            assert manager2.entries[0].filepath == fake_file


class TestHistoryManagerEdgeCases:
    """Test edge cases for HistoryManager."""

    @patch("src.history.config.get_config_dir")
    def test_filters_deleted_files_on_load(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            # Create history with non-existent file reference
            history_file = Path(tmpdir) / "history.json"
            history_data = [
                {
                    "filepath": "/nonexistent/file.png",
                    "timestamp": "2024-01-15T10:30:00",
                    "mode": "fullscreen"
                }
            ]
            history_file.write_text(json.dumps(history_data))

            from src.history import HistoryManager
            manager = HistoryManager()

            # Should filter out non-existent files
            assert len(manager.entries) == 0


class TestHistoryWindowAvailability:
    """Test HistoryWindow class availability."""

    def test_history_window_class_exists(self):
        from src.history import HistoryWindow
        assert HistoryWindow is not None

    def test_history_window_has_required_methods(self):
        from src.history import HistoryWindow
        assert hasattr(HistoryWindow, "__init__")
        assert hasattr(HistoryWindow, "_create_toolbar")
        assert hasattr(HistoryWindow, "_load_history")

    def test_history_window_has_event_handlers(self):
        from src.history import HistoryWindow
        assert hasattr(HistoryWindow, "_on_item_activated")
        assert hasattr(HistoryWindow, "_on_delete")
        assert hasattr(HistoryWindow, "_on_clear_all")
        assert hasattr(HistoryWindow, "_on_open_folder")


class TestHistoryManagerSaveLoad:
    """Test HistoryManager save/load cycle."""

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_save_creates_file(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "fullscreen")

            history_file = Path(tmpdir) / "history.json"
            assert history_file.exists()

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_save_valid_json(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "region")

            history_file = Path(tmpdir) / "history.json"
            with open(history_file) as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["mode"] == "region"

    @patch("src.history.config.get_config_dir")
    def test_load_with_missing_mode_key(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            # Create a file for the history entry
            test_file = Path(tmpdir) / "test.png"
            test_file.touch()

            # Create history with missing mode key
            history_file = Path(tmpdir) / "history.json"
            history_data = [
                {
                    "filepath": str(test_file),
                    "timestamp": "2024-01-15T10:30:00"
                    # mode is missing
                }
            ]
            history_file.write_text(json.dumps(history_data))

            from src.history import HistoryManager
            manager = HistoryManager()

            # Should load with default mode
            assert len(manager.entries) == 1
            assert manager.entries[0].mode == "unknown"


class TestHistoryEntryRoundTrip:
    """Test HistoryEntry serialization round trip."""

    def test_to_dict_from_dict_roundtrip(self):
        from src.history import HistoryEntry

        original = HistoryEntry(
            Path("/path/to/image.png"),
            datetime(2024, 3, 15, 14, 30, 45),
            "window"
        )

        # Round trip
        data = original.to_dict()
        restored = HistoryEntry.from_dict(data)

        assert restored.filepath == original.filepath
        assert restored.timestamp == original.timestamp
        assert restored.mode == original.mode


class TestHistoryManagerModes:
    """Test different capture modes in history."""

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_fullscreen_mode(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "fullscreen")

            assert manager.entries[0].mode == "fullscreen"

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_region_mode(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "region")

            assert manager.entries[0].mode == "region"

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_window_mode(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "window")

            assert manager.entries[0].mode == "window"

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_gif_mode(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.gif"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "gif")

            assert manager.entries[0].mode == "gif"

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_add_scroll_mode(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            fake_file = Path(tmpdir) / "test.png"
            fake_file.touch()

            from src.history import HistoryManager
            manager = HistoryManager()
            manager.add(fake_file, "scroll")

            assert manager.entries[0].mode == "scroll"


class TestHistoryManagerIOErrors:
    """Test HistoryManager IO error handling."""

    @patch("src.history.config.get_config_dir")
    @patch("src.history.config.ensure_config_dir")
    def test_save_handles_io_error(self, mock_ensure, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            from src.history import HistoryManager
            manager = HistoryManager()

            # Make the history file path a directory to cause IOError
            history_file = Path(tmpdir) / "history.json"
            history_file.mkdir()

            # Should not raise, just silently fail
            manager.save()

    @patch("src.history.config.get_config_dir")
    def test_load_handles_key_error(self, mock_config_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config_dir.return_value = Path(tmpdir)

            # Create history with missing required key
            history_file = Path(tmpdir) / "history.json"
            history_data = [
                {
                    # Missing filepath key
                    "timestamp": "2024-01-15T10:30:00",
                    "mode": "fullscreen"
                }
            ]
            history_file.write_text(json.dumps(history_data))

            from src.history import HistoryManager
            manager = HistoryManager()

            # Should handle gracefully
            assert manager.entries == []
