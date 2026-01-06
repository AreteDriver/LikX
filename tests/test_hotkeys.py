"""Tests for hotkeys module."""

import sys
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHotkeysModuleAvailability:
    """Test hotkeys module can be imported."""

    def test_hotkeys_module_imports(self):
        from src import hotkeys
        assert hotkeys is not None

    def test_hotkey_manager_class_exists(self):
        from src.hotkeys import HotkeyManager
        assert HotkeyManager is not None


class TestHotkeyManagerInit:
    """Test HotkeyManager initialization."""

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_init(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        assert manager is not None
        assert hasattr(manager, "hotkeys")
        assert hasattr(manager, "desktop_env")

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_init_stores_desktop_env(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        assert manager.desktop_env == "kde"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_init_creates_hotkeys_dict(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        assert isinstance(manager.hotkeys, dict)


class TestDetectDesktopEnvironment:
    """Test desktop environment detection."""

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_detect_gnome(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "gnome"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_detect_kde(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "kde"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "plasma"})
    def test_detect_plasma(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "kde"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "XFCE"})
    def test_detect_xfce(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "xfce"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "MATE"})
    def test_detect_mate(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "mate"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": ""}, clear=True)
    def test_detect_unknown(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "unknown"

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "SOME_OTHER_DE"})
    def test_detect_other(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        assert manager.desktop_env == "unknown"


class TestRegisterHotkey:
    """Test hotkey registration."""

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_register_gnome_hotkey_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="@as []")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("<Super>Print", callback, "likx --capture")

        assert result is True
        assert "<Super>Print" in manager.hotkeys

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_register_stores_callback(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="@as []")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: "test"

        manager.register_hotkey("<Control>s", callback, "likx --save")

        assert manager.hotkeys["<Control>s"] is callback

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_register_kde_hotkey_returns_false(self, mock_run):
        # KDE hotkey registration is not implemented
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("Meta+Print", callback, "likx --capture")

        # KDE returns False as it's not implemented
        assert result is False

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "UNKNOWN"})
    def test_register_unsupported_desktop_returns_false(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("<Super>s", callback, "likx")

        assert result is False


class TestGnomeHotkeyRegistration:
    """Test GNOME-specific hotkey registration."""

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_gnome_adds_to_empty_list(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="@as []")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("<Super>Print", callback, "likx --capture")

        assert result is True
        # Check gsettings was called
        assert mock_run.call_count >= 1

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_gnome_adds_to_existing_list(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="['/existing/path/']"
        )

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("<Super>Print", callback, "likx --capture")

        assert result is True

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_gnome_handles_exception(self, mock_run):
        mock_run.side_effect = Exception("gsettings error")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        result = manager.register_hotkey("<Super>Print", callback, "likx --capture")

        # Should return False on exception
        assert result is False


class TestUnregisterHotkey:
    """Test hotkey unregistration."""

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_unregister_all_gnome(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="['/some/path/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/likx/']"
        )

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        # Should not raise
        manager.unregister_all()

        # Should call gsettings
        assert mock_run.called

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_unregister_all_no_likx_path(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="['/some/other/path/']"
        )

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        # Should not raise
        manager.unregister_all()

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_unregister_handles_exception(self, mock_run):
        mock_run.side_effect = Exception("gsettings error")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        # Should not raise
        manager.unregister_all()

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_unregister_kde_does_nothing(self):
        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()

        # Should not raise for unsupported desktop
        manager.unregister_all()


class TestHotkeyManagerAttributes:
    """Test HotkeyManager attributes and methods."""

    def test_has_register_hotkey(self):
        from src.hotkeys import HotkeyManager
        assert hasattr(HotkeyManager, "register_hotkey")

    def test_has_unregister_all(self):
        from src.hotkeys import HotkeyManager
        assert hasattr(HotkeyManager, "unregister_all")

    def test_has_detect_desktop_environment(self):
        from src.hotkeys import HotkeyManager
        assert hasattr(HotkeyManager, "_detect_desktop_environment")

    def test_has_register_gnome_hotkey(self):
        from src.hotkeys import HotkeyManager
        assert hasattr(HotkeyManager, "_register_gnome_hotkey")

    def test_has_register_kde_hotkey(self):
        from src.hotkeys import HotkeyManager
        assert hasattr(HotkeyManager, "_register_kde_hotkey")


class TestHotkeyEdgeCases:
    """Test edge cases."""

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_empty_key_combo(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="@as []")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        # Empty key combo - implementation may accept or reject
        result = manager.register_hotkey("", callback, "likx")
        # Just verify it doesn't crash

    @patch("src.hotkeys.subprocess.run")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_empty_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="@as []")

        from src.hotkeys import HotkeyManager
        manager = HotkeyManager()
        callback = lambda: None

        # Empty command - implementation may accept or reject
        result = manager.register_hotkey("<Super>s", callback, "")
        # Just verify it doesn't crash
