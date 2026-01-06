"""Tests for effects module.

Note: Most effects functions use Cairo/GTK which require a real display.
These tests focus on edge cases and error handling that can be tested
without GTK.
"""

from unittest.mock import MagicMock

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


class TestNewEffectsFunctionSignatures:
    """Test new effect functions added in v3.4."""

    def test_adjust_brightness_contrast_signature(self):
        from src.effects import adjust_brightness_contrast
        import inspect
        sig = inspect.signature(adjust_brightness_contrast)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params
        assert 'brightness' in params
        assert 'contrast' in params

    def test_invert_colors_signature(self):
        from src.effects import invert_colors
        import inspect
        sig = inspect.signature(invert_colors)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params

    def test_grayscale_signature(self):
        from src.effects import grayscale
        import inspect
        sig = inspect.signature(grayscale)
        params = list(sig.parameters.keys())
        assert 'pixbuf' in params


class TestNewEffectsDefaultValues:
    """Test default parameter values for new effects."""

    def test_adjust_brightness_contrast_defaults(self):
        from src.effects import adjust_brightness_contrast
        import inspect
        sig = inspect.signature(adjust_brightness_contrast)
        assert sig.parameters['brightness'].default == 0.0
        assert sig.parameters['contrast'].default == 0.0


class TestEffectsErrorHandling:
    """Test that effects gracefully handle errors."""

    def test_adjust_brightness_contrast_returns_original_on_error(self):
        from src.effects import adjust_brightness_contrast
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = adjust_brightness_contrast(mock_pixbuf, 0.5, 0.5)
        assert result == mock_pixbuf  # Returns original on error

    def test_invert_colors_returns_original_on_error(self):
        from src.effects import invert_colors
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = invert_colors(mock_pixbuf)
        assert result == mock_pixbuf  # Returns original on error

    def test_grayscale_returns_original_on_error(self):
        from src.effects import grayscale
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = grayscale(mock_pixbuf)
        assert result == mock_pixbuf  # Returns original on error

    def test_add_shadow_returns_original_on_error(self):
        from src.effects import add_shadow
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = add_shadow(mock_pixbuf, 10, 0.5)
        assert result == mock_pixbuf

    def test_add_border_returns_original_on_error(self):
        from src.effects import add_border
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = add_border(mock_pixbuf, 5, (0, 0, 0, 1))
        assert result == mock_pixbuf

    def test_add_background_returns_original_on_error(self):
        from src.effects import add_background
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = add_background(mock_pixbuf, (1, 1, 1, 1), 20)
        assert result == mock_pixbuf

    def test_round_corners_returns_original_on_error(self):
        from src.effects import round_corners
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")
        result = round_corners(mock_pixbuf, 10)
        assert result == mock_pixbuf


class TestEffectsEdgeCases:
    """Test edge cases for effect functions."""

    def test_adjust_brightness_contrast_extreme_brightness(self):
        """Test with extreme brightness values."""
        from src.effects import adjust_brightness_contrast
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        # Should not raise with extreme values
        result = adjust_brightness_contrast(mock_pixbuf, brightness=1.0, contrast=0.0)
        assert result == mock_pixbuf

        result = adjust_brightness_contrast(mock_pixbuf, brightness=-1.0, contrast=0.0)
        assert result == mock_pixbuf

    def test_adjust_brightness_contrast_extreme_contrast(self):
        """Test with extreme contrast values."""
        from src.effects import adjust_brightness_contrast
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = adjust_brightness_contrast(mock_pixbuf, brightness=0.0, contrast=1.0)
        assert result == mock_pixbuf

        result = adjust_brightness_contrast(mock_pixbuf, brightness=0.0, contrast=-1.0)
        assert result == mock_pixbuf

    def test_add_shadow_zero_size(self):
        """Test shadow with zero size."""
        from src.effects import add_shadow
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_shadow(mock_pixbuf, shadow_size=0, opacity=0.5)
        assert result == mock_pixbuf

    def test_add_shadow_zero_opacity(self):
        """Test shadow with zero opacity."""
        from src.effects import add_shadow
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_shadow(mock_pixbuf, shadow_size=10, opacity=0.0)
        assert result == mock_pixbuf

    def test_add_border_zero_width(self):
        """Test border with zero width."""
        from src.effects import add_border
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_border(mock_pixbuf, border_width=0)
        assert result == mock_pixbuf

    def test_add_border_custom_color(self):
        """Test border with custom color."""
        from src.effects import add_border
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_border(mock_pixbuf, border_width=5, color=(1, 0, 0, 1))
        assert result == mock_pixbuf

    def test_add_background_zero_padding(self):
        """Test background with zero padding."""
        from src.effects import add_background
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_background(mock_pixbuf, padding=0)
        assert result == mock_pixbuf

    def test_add_background_custom_color(self):
        """Test background with custom color."""
        from src.effects import add_background
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = add_background(mock_pixbuf, bg_color=(0.5, 0.5, 0.5, 1), padding=10)
        assert result == mock_pixbuf

    def test_round_corners_zero_radius(self):
        """Test round corners with zero radius."""
        from src.effects import round_corners
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = round_corners(mock_pixbuf, radius=0)
        assert result == mock_pixbuf

    def test_round_corners_large_radius(self):
        """Test round corners with large radius."""
        from src.effects import round_corners
        mock_pixbuf = MagicMock()
        mock_pixbuf.get_width.side_effect = Exception("test error")

        result = round_corners(mock_pixbuf, radius=100)
        assert result == mock_pixbuf
