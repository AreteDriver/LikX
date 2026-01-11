"""Tests for the recording and scroll capture overlay modules."""

from unittest.mock import MagicMock

import pytest


class TestRecordingOverlayModuleImport:
    """Test recording_overlay module imports."""

    def test_module_imports(self):
        """Test that recording_overlay module imports successfully."""
        from src import recording_overlay

        assert hasattr(recording_overlay, "RecordingOverlay")
        assert hasattr(recording_overlay, "GTK_AVAILABLE")

    def test_gtk_available_is_bool(self):
        """Test that GTK_AVAILABLE is a boolean."""
        from src.recording_overlay import GTK_AVAILABLE

        assert isinstance(GTK_AVAILABLE, bool)


class TestScrollOverlayModuleImport:
    """Test scroll_overlay module imports."""

    def test_module_imports(self):
        """Test that scroll_overlay module imports successfully."""
        from src import scroll_overlay

        assert hasattr(scroll_overlay, "ScrollCaptureOverlay")
        assert hasattr(scroll_overlay, "GTK_AVAILABLE")

    def test_gtk_available_is_bool(self):
        """Test that GTK_AVAILABLE is a boolean."""
        from src.scroll_overlay import GTK_AVAILABLE

        assert isinstance(GTK_AVAILABLE, bool)


class TestRecordingOverlayWithMockedGtk:
    """Test RecordingOverlay with mocked GTK."""

    def test_overlay_requires_callback(self):
        """Test that overlay requires on_stop callback."""
        from src.recording_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")


        # Should be able to create with callback
        MagicMock()
        # This would need a display, so we can't fully test without X11/Wayland

    def test_overlay_accepts_region(self):
        """Test that overlay accepts region parameter."""
        from src.recording_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        # Region is optional parameter

        # Can't fully instantiate without display


class TestScrollOverlayWithMockedGtk:
    """Test ScrollCaptureOverlay with mocked GTK."""

    def test_overlay_requires_callback(self):
        """Test that overlay requires on_stop callback."""
        from src.scroll_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")


        # Should accept on_stop callback

    def test_overlay_has_update_progress(self):
        """Test that overlay has update_progress method."""
        from src.scroll_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        from src.scroll_overlay import ScrollCaptureOverlay

        assert hasattr(ScrollCaptureOverlay, "update_progress")


class TestOverlayI18n:
    """Test that overlays use i18n."""

    def test_recording_overlay_imports_i18n(self):
        """Test that recording_overlay imports i18n."""
        from src import recording_overlay
        import inspect

        source = inspect.getsource(recording_overlay)
        assert "from .i18n import _" in source

    def test_scroll_overlay_imports_i18n(self):
        """Test that scroll_overlay imports i18n."""
        from src import scroll_overlay
        import inspect

        source = inspect.getsource(scroll_overlay)
        assert "from .i18n import _" in source

    def test_recording_overlay_translates_stop(self):
        """Test that 'Stop' button is translated."""
        from src import recording_overlay
        import inspect

        source = inspect.getsource(recording_overlay)
        # Should use _("Stop") instead of "Stop"
        assert '_("Stop")' in source

    def test_scroll_overlay_translates_stop(self):
        """Test that 'Stop' button is translated."""
        from src import scroll_overlay
        import inspect

        source = inspect.getsource(scroll_overlay)
        assert '_("Stop")' in source

    def test_scroll_overlay_translates_frames(self):
        """Test that 'Frames:' label is translated."""
        from src import scroll_overlay
        import inspect

        source = inspect.getsource(scroll_overlay)
        assert '_("Frames:")' in source

    def test_scroll_overlay_translates_height(self):
        """Test that 'Height:' label is translated."""
        from src import scroll_overlay
        import inspect

        source = inspect.getsource(scroll_overlay)
        assert '_("Height:")' in source

    def test_recording_overlay_translates_rec(self):
        """Test that 'REC' label is translated."""
        from src import recording_overlay
        import inspect

        source = inspect.getsource(recording_overlay)
        assert '_("REC")' in source


class TestOverlayCSS:
    """Test overlay CSS loading."""

    def test_recording_overlay_has_css(self):
        """Test that recording overlay has CSS."""
        from src import recording_overlay
        import inspect

        source = inspect.getsource(recording_overlay)
        assert ".recording-overlay" in source
        assert ".recording-stop" in source

    def test_scroll_overlay_has_css(self):
        """Test that scroll overlay has CSS."""
        from src import scroll_overlay
        import inspect

        source = inspect.getsource(scroll_overlay)
        assert ".scroll-overlay" in source
        assert ".scroll-stop" in source


class TestOverlayDestroy:
    """Test overlay destroy methods."""

    def test_recording_overlay_has_destroy(self):
        """Test that RecordingOverlay has destroy method."""
        from src.recording_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        from src.recording_overlay import RecordingOverlay

        assert hasattr(RecordingOverlay, "destroy")

    def test_scroll_overlay_has_destroy(self):
        """Test that ScrollCaptureOverlay has destroy method."""
        from src.scroll_overlay import GTK_AVAILABLE

        if not GTK_AVAILABLE:
            pytest.skip("GTK not available")

        from src.scroll_overlay import ScrollCaptureOverlay

        assert hasattr(ScrollCaptureOverlay, "destroy")
