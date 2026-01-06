"""Tests for effects module.

Note: Most effects functions use Cairo/GTK which require a real display.
These tests focus on edge cases and error handling that can be tested
without GTK.
"""

import pytest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEffectsAvailability:
    """Test GTK availability detection."""

    def test_gtk_available_flag_exists(self):
        from src import effects
        assert hasattr(effects, 'GTK_AVAILABLE')

    def test_gtk_available_is_boolean(self):
        from src import effects
        assert isinstance(effects.GTK_AVAILABLE, bool)


class TestEffectsFunctionSignatures:
    """Test that effect functions have correct signatures."""

    def test_add_shadow_signature(self):
        from src.effects import add_shadow
        import inspect
        sig = inspect.signature(add_shadow)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params
        assert 'shadow_size' in params
        assert 'opacity' in params

    def test_add_border_signature(self):
        from src.effects import add_border
        import inspect
        sig = inspect.signature(add_border)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params
        assert 'border_width' in params
        assert 'color' in params

    def test_add_background_signature(self):
        from src.effects import add_background
        import inspect
        sig = inspect.signature(add_background)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params
        assert 'bg_color' in params
        assert 'padding' in params

    def test_round_corners_signature(self):
        from src.effects import round_corners
        import inspect
        sig = inspect.signature(round_corners)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params
        assert 'radius' in params


class TestEffectsDefaultValues:
    """Test default parameter values."""

    def test_add_shadow_defaults(self):
        from src.effects import add_shadow
        import inspect
        sig = inspect.signature(add_shadow)
        assert sig.parameters['shadow_size'].default == 10
        assert sig.parameters['opacity'].default == 0.5

    def test_add_border_defaults(self):
        from src.effects import add_border
        import inspect
        sig = inspect.signature(add_border)
        assert sig.parameters['border_width'].default == 5
        assert sig.parameters['color'].default == (0, 0, 0, 1)

    def test_add_background_defaults(self):
        from src.effects import add_background
        import inspect
        sig = inspect.signature(add_background)
        assert sig.parameters['bg_color'].default == (1, 1, 1, 1)
        assert sig.parameters['padding'].default == 20

    def test_round_corners_defaults(self):
        from src.effects import round_corners
        import inspect
        sig = inspect.signature(round_corners)
        assert sig.parameters['radius'].default == 10
