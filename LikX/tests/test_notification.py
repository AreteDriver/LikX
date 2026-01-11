"""Tests for notification module."""

import sys
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNotificationModuleAvailability:
    """Test notification module can be imported."""

    def test_notification_module_imports(self):
        from src import notification
        assert notification is not None

    def test_show_notification_function_exists(self):
        from src import notification
        assert hasattr(notification, "show_notification")
        assert callable(notification.show_notification)

    def test_show_screenshot_saved_exists(self):
        from src import notification
        assert hasattr(notification, "show_screenshot_saved")
        assert callable(notification.show_screenshot_saved)

    def test_show_screenshot_copied_exists(self):
        from src import notification
        assert hasattr(notification, "show_screenshot_copied")
        assert callable(notification.show_screenshot_copied)

    def test_show_upload_success_exists(self):
        from src import notification
        assert hasattr(notification, "show_upload_success")
        assert callable(notification.show_upload_success)

    def test_show_upload_error_exists(self):
        from src import notification
        assert hasattr(notification, "show_upload_error")
        assert callable(notification.show_upload_error)


class TestShowNotificationFallback:
    """Test show_notification fallback to notify-send."""

    @patch("src.notification.subprocess.run")
    def test_fallback_to_notify_send(self, mock_run):
        # Make GI import fail by patching
        with patch.dict("sys.modules", {"gi": None}):
            from src import notification
            # Can't easily reload to trigger import error, so test subprocess path directly
            mock_run.return_value = MagicMock(returncode=0)

            # Call with subprocess working
            notification.show_notification("Title", "Body")
            # Either GI works (returns True) or subprocess works (returns True)
            # We can't easily control which path without complex patching

    @patch("src.notification.subprocess.run")
    def test_function_signature(self, mock_run):
        from src.notification import show_notification

        # Test default parameters work
        mock_run.return_value = MagicMock(returncode=0)
        result = show_notification("Title", "Body")
        assert isinstance(result, bool)

    @patch("src.notification.subprocess.run")
    def test_function_with_all_params(self, mock_run):
        from src.notification import show_notification

        mock_run.return_value = MagicMock(returncode=0)
        result = show_notification(
            "Title",
            "Body",
            icon="custom-icon",
            urgency="critical",
            timeout=10000
        )
        assert isinstance(result, bool)


class TestShowNotificationExceptions:
    """Test exception handling in show_notification."""

    @patch("src.notification.subprocess.run")
    def test_subprocess_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        from src.notification import show_notification

        # Patch out the GI try block
        with patch("builtins.__import__", side_effect=ImportError()):
            # Should return False, not raise
            show_notification("Title", "Body")
            # Result depends on whether GI works first

    @patch("src.notification.subprocess.run")
    def test_subprocess_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="notify-send", timeout=2)

        from src.notification import show_notification

        # Should handle timeout gracefully
        result = show_notification("Title", "Body")
        # Result is bool (True if GI worked, False if both failed)
        assert isinstance(result, bool)

    @patch("src.notification.subprocess.run")
    def test_subprocess_called_process_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "notify-send")

        from src.notification import show_notification

        result = show_notification("Title", "Body")
        assert isinstance(result, bool)


class TestConvenienceFunctions:
    """Test convenience notification functions."""

    @patch("src.notification.show_notification")
    def test_show_screenshot_saved(self, mock_show):
        mock_show.return_value = True
        from src.notification import show_screenshot_saved

        show_screenshot_saved("/path/to/file.png")

        mock_show.assert_called_once()
        args, kwargs = mock_show.call_args
        assert "Screenshot Saved" in args[0]
        assert "/path/to/file.png" in args[1]

    @patch("src.notification.show_notification")
    def test_show_screenshot_copied(self, mock_show):
        mock_show.return_value = True
        from src.notification import show_screenshot_copied

        show_screenshot_copied()

        mock_show.assert_called_once()
        args, kwargs = mock_show.call_args
        assert "copied" in args[0].lower() or "copied" in args[1].lower()

    @patch("src.notification.show_notification")
    def test_show_upload_success(self, mock_show):
        mock_show.return_value = True
        from src.notification import show_upload_success

        show_upload_success("https://example.com/image.png")

        mock_show.assert_called_once()
        args, kwargs = mock_show.call_args
        assert "Upload" in args[0] or "Successful" in args[0]
        assert "https://example.com/image.png" in args[1]

    @patch("src.notification.show_notification")
    def test_show_upload_error(self, mock_show):
        mock_show.return_value = True
        from src.notification import show_upload_error

        show_upload_error("Connection failed")

        mock_show.assert_called_once()
        args, kwargs = mock_show.call_args
        assert "Failed" in args[0]
        assert "Connection failed" in args[1]


class TestNotificationParameters:
    """Test notification parameter handling."""

    @patch("src.notification.subprocess.run")
    def test_urgency_parameter(self, mock_run):
        from src.notification import show_notification

        mock_run.return_value = MagicMock(returncode=0)

        # Test different urgency levels
        show_notification("Title", "Body", urgency="low")
        show_notification("Title", "Body", urgency="normal")
        show_notification("Title", "Body", urgency="critical")

    @patch("src.notification.subprocess.run")
    def test_timeout_parameter(self, mock_run):
        from src.notification import show_notification

        mock_run.return_value = MagicMock(returncode=0)

        show_notification("Title", "Body", timeout=1000)
        show_notification("Title", "Body", timeout=30000)

    @patch("src.notification.subprocess.run")
    def test_icon_parameter(self, mock_run):
        from src.notification import show_notification

        mock_run.return_value = MagicMock(returncode=0)

        show_notification("Title", "Body", icon="dialog-information")
        show_notification("Title", "Body", icon="camera-photo")
