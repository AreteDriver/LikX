"""Tests for the screenshot history module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestHistoryEntry:
    """Test HistoryEntry dataclass."""

    def test_entry_creation(self):
        """Test creating a history entry."""
        from src.history import HistoryEntry

        path = Path("/tmp/test.png")
        timestamp = datetime.now()
        entry = HistoryEntry(path, timestamp, "region")

        assert entry.filepath == path
        assert entry.timestamp == timestamp
        assert entry.mode == "region"
        assert entry.thumbnail is None

    def test_entry_default_mode(self):
        """Test entry with default mode."""
        from src.history import HistoryEntry

        entry = HistoryEntry(Path("/tmp/test.png"), datetime.now())
        assert entry.mode == "unknown"

    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        from src.history import HistoryEntry

        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry = HistoryEntry(Path("/tmp/test.png"), timestamp, "fullscreen")

        d = entry.to_dict()
        assert d["filepath"] == "/tmp/test.png"
        assert d["timestamp"] == "2024-01-15T10:30:00"
        assert d["mode"] == "fullscreen"

    def test_entry_from_dict(self):
        """Test creating entry from dictionary."""
        from src.history import HistoryEntry

        data = {
            "filepath": "/tmp/test.png",
            "timestamp": "2024-01-15T10:30:00",
            "mode": "window"
        }
        entry = HistoryEntry.from_dict(data)

        assert entry.filepath == Path("/tmp/test.png")
        assert entry.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert entry.mode == "window"

    def test_entry_from_dict_default_mode(self):
        """Test creating entry from dict without mode."""
        from src.history import HistoryEntry

        data = {
            "filepath": "/tmp/test.png",
            "timestamp": "2024-01-15T10:30:00"
        }
        entry = HistoryEntry.from_dict(data)
        assert entry.mode == "unknown"


class TestHistoryManager:
    """Test HistoryManager class."""

    def test_manager_creation(self):
        """Test creating a history manager."""
        from src.history import HistoryManager

        with patch.object(HistoryManager, "load"):
            manager = HistoryManager()
            assert isinstance(manager.entries, list)

    def test_manager_history_file_path(self):
        """Test history file path is in config dir."""
        from src.history import HistoryManager
        from src import config

        with patch.object(HistoryManager, "load"):
            manager = HistoryManager()
            assert manager.history_file.parent == config.get_config_dir()
            assert manager.history_file.name == "history.json"

    def test_load_empty_history(self):
        """Test loading when no history file exists."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                assert manager.entries == []

    def test_load_history_from_file(self):
        """Test loading history from file."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image file
            test_image = Path(tmpdir) / "test.png"
            test_image.write_bytes(b"fake png data")

            # Create history file
            history_data = [
                {
                    "filepath": str(test_image),
                    "timestamp": "2024-01-15T10:30:00",
                    "mode": "region"
                }
            ]
            history_file = Path(tmpdir) / "history.json"
            history_file.write_text(json.dumps(history_data))

            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                assert len(manager.entries) == 1
                assert manager.entries[0].mode == "region"

    def test_load_filters_deleted_files(self):
        """Test that load filters out deleted files."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create history with non-existent file
            history_data = [
                {
                    "filepath": "/nonexistent/file.png",
                    "timestamp": "2024-01-15T10:30:00",
                    "mode": "region"
                }
            ]
            history_file = Path(tmpdir) / "history.json"
            history_file.write_text(json.dumps(history_data))

            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                assert len(manager.entries) == 0

    def test_load_handles_invalid_json(self):
        """Test that load handles invalid JSON gracefully."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            history_file.write_text("not valid json {{{")

            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                assert manager.entries == []

    def test_save_history(self):
        """Test saving history to file."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    manager.entries = [
                        HistoryEntry(
                            Path("/tmp/test.png"),
                            datetime(2024, 1, 15, 10, 30, 0),
                            "region"
                        )
                    ]
                    manager.save()

                    history_file = Path(tmpdir) / "history.json"
                    assert history_file.exists()
                    data = json.loads(history_file.read_text())
                    assert len(data) == 1
                    assert data[0]["mode"] == "region"

    def test_save_handles_io_error(self):
        """Test that save handles IO errors gracefully."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                # Make directory read-only to cause IO error
                with patch("builtins.open", side_effect=IOError("Permission denied")):
                    with patch("src.history.config.ensure_config_dir"):
                        # Should not raise
                        manager.save()

    def test_add_entry(self):
        """Test adding an entry."""
        from src.history import HistoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    test_path = Path(tmpdir) / "test.png"
                    manager.add(test_path, "fullscreen")

                    assert len(manager.entries) == 1
                    assert manager.entries[0].filepath == test_path
                    assert manager.entries[0].mode == "fullscreen"

    def test_add_inserts_at_beginning(self):
        """Test that new entries are inserted at beginning."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    manager.entries = [
                        HistoryEntry(Path("/old.png"), datetime.now(), "old")
                    ]
                    new_path = Path(tmpdir) / "new.png"
                    manager.add(new_path, "new")

                    assert manager.entries[0].mode == "new"
                    assert manager.entries[1].mode == "old"

    def test_add_limits_to_100_entries(self):
        """Test that history is limited to 100 entries."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    # Add 105 entries
                    manager.entries = [
                        HistoryEntry(Path(f"/{i}.png"), datetime.now(), "test")
                        for i in range(100)
                    ]
                    manager.add(Path("/new.png"), "new")

                    assert len(manager.entries) == 100
                    assert manager.entries[0].mode == "new"

    def test_remove_entry(self):
        """Test removing an entry."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    entry = HistoryEntry(Path("/test.png"), datetime.now(), "test")
                    manager.entries = [entry]

                    manager.remove(entry)
                    assert len(manager.entries) == 0

    def test_remove_nonexistent_entry(self):
        """Test removing entry that doesn't exist."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                entry = HistoryEntry(Path("/test.png"), datetime.now(), "test")
                # Should not raise
                manager.remove(entry)

    def test_clear_history(self):
        """Test clearing all history."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                with patch("src.history.config.ensure_config_dir"):
                    manager = HistoryManager()
                    manager.entries = [
                        HistoryEntry(Path("/test.png"), datetime.now(), "test")
                    ]
                    manager.clear()
                    assert len(manager.entries) == 0

    def test_get_recent(self):
        """Test getting recent entries."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                manager.entries = [
                    HistoryEntry(Path(f"/{i}.png"), datetime.now(), f"mode{i}")
                    for i in range(30)
                ]

                recent = manager.get_recent()
                assert len(recent) == 20  # Default limit

    def test_get_recent_with_custom_limit(self):
        """Test getting recent entries with custom limit."""
        from src.history import HistoryManager, HistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.history.config.get_config_dir", return_value=Path(tmpdir)):
                manager = HistoryManager()
                manager.entries = [
                    HistoryEntry(Path(f"/{i}.png"), datetime.now(), f"mode{i}")
                    for i in range(30)
                ]

                recent = manager.get_recent(limit=5)
                assert len(recent) == 5


class TestHistoryWindowCreation:
    """Test HistoryWindow creation."""

    def test_window_creation(self):
        """Test creating history window."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()
            assert window.window is not None
            window.window.destroy()

    def test_window_with_parent(self):
        """Test creating history window with parent."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except (ImportError, ValueError):
            pytest.skip("GTK not available")

        parent = Gtk.Window()
        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow(parent=parent)
            assert window.window.get_transient_for() == parent
            window.window.destroy()
            parent.destroy()

    def test_window_default_size(self):
        """Test window has correct default size."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()
            width, height = window.window.get_default_size()
            assert width == 800
            assert height == 600
            window.window.destroy()


class TestHistoryWindowToolbar:
    """Test HistoryWindow toolbar."""

    def test_toolbar_created(self):
        """Test toolbar is created."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()
            # Toolbar should exist
            toolbar = window._create_toolbar()
            assert toolbar is not None
            window.window.destroy()


class TestHistoryWindowLoadHistory:
    """Test _load_history method."""

    def test_load_history_populates_store(self):
        """Test that load_history populates icon store."""
        from src.history import HistoryWindow, HistoryEntry, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image using GdkPixbuf to ensure it's valid
            try:
                import gi
                gi.require_version("GdkPixbuf", "2.0")
                from gi.repository import GdkPixbuf
            except (ImportError, ValueError):
                pytest.skip("GdkPixbuf not available")

            test_image = Path(tmpdir) / "test.png"
            # Create a valid 10x10 pixbuf and save it
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 10, 10)
            pixbuf.fill(0xFF0000FF)  # Red with alpha
            pixbuf.savev(str(test_image), "png", [], [])

            entry = HistoryEntry(test_image, datetime.now(), "region")

            with patch("src.history.HistoryManager") as mock_manager:
                mock_instance = mock_manager.return_value
                mock_instance.get_recent.return_value = [entry]
                mock_instance.load = MagicMock()

                window = HistoryWindow()
                # Store should have one item
                assert len(window.store) == 1
                window.window.destroy()

    def test_load_history_handles_missing_files(self):
        """Test that load_history skips missing files."""
        from src.history import HistoryWindow, HistoryEntry, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        entry = HistoryEntry(Path("/nonexistent/file.png"), datetime.now(), "region")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_recent.return_value = [entry]
            mock_instance.load = MagicMock()

            window = HistoryWindow()
            # Store should be empty
            assert len(window.store) == 0
            window.window.destroy()


class TestHistoryWindowCallbacks:
    """Test HistoryWindow callback methods."""

    def test_on_item_activated(self):
        """Test item activation opens file."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()

            # Add a mock item to the store
            try:
                import gi
                gi.require_version("GdkPixbuf", "2.0")
                from gi.repository import GdkPixbuf

                pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
                window.store.append([pixbuf, "test", "/tmp/test.png", None])

                with patch("subprocess.Popen") as mock_popen:
                    # Create a TreePath pointing to first item
                    from gi.repository import Gtk
                    path = Gtk.TreePath.new_first()
                    window._on_item_activated(window.icon_view, path)
                    mock_popen.assert_called_once_with(["xdg-open", "/tmp/test.png"])
            finally:
                window.window.destroy()

    def test_on_item_activated_handles_error(self):
        """Test item activation handles subprocess errors."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()

            try:
                import gi
                gi.require_version("GdkPixbuf", "2.0")
                from gi.repository import GdkPixbuf, Gtk

                pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
                window.store.append([pixbuf, "test", "/tmp/test.png", None])

                with patch("subprocess.Popen", side_effect=Exception("test error")):
                    path = Gtk.TreePath.new_first()
                    # Should not raise
                    window._on_item_activated(window.icon_view, path)
            finally:
                window.window.destroy()

    def test_on_delete_no_selection(self):
        """Test delete with no selection does nothing."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()

            # Should not raise with no selection
            window._on_delete(None)
            window.window.destroy()

    def test_on_open_folder(self):
        """Test open folder opens file manager."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()

            with patch("subprocess.Popen") as mock_popen:
                with patch("src.history.config.load_config", return_value={"save_directory": "/tmp/screenshots"}):
                    window._on_open_folder(None)
                    mock_popen.assert_called_once()
                    call_args = mock_popen.call_args[0][0]
                    assert call_args[0] == "xdg-open"

            window.window.destroy()

    def test_on_open_folder_handles_error(self):
        """Test open folder handles subprocess errors."""
        from src.history import HistoryWindow, GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        with patch("src.history.HistoryManager") as mock_manager:
            mock_manager.return_value.get_recent.return_value = []
            window = HistoryWindow()

            with patch("subprocess.Popen", side_effect=Exception("test error")):
                with patch("src.history.config.load_config", return_value={"save_directory": "/tmp"}):
                    # Should not raise
                    window._on_open_folder(None)

            window.window.destroy()


class TestGTKNotAvailable:
    """Test behavior when GTK is not available."""

    def test_history_window_raises_without_gtk(self):
        """Test HistoryWindow raises error without GTK."""
        import src.history as history_module

        original_gtk = history_module.GTK_AVAILABLE
        try:
            history_module.GTK_AVAILABLE = False

            with pytest.raises(RuntimeError, match="GTK not available"):
                history_module.HistoryWindow()
        finally:
            history_module.GTK_AVAILABLE = original_gtk
