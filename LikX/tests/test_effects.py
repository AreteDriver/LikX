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


class TestEffectsModuleLevel:
    """Test module-level properties."""

    def test_module_has_gtk_available(self):
        """Test module has GTK_AVAILABLE flag."""
        from src import effects
        assert hasattr(effects, "GTK_AVAILABLE")
        assert isinstance(effects.GTK_AVAILABLE, bool)

    def test_all_functions_defined(self):
        """Test all expected functions are defined."""
        from src import effects
        assert hasattr(effects, "add_shadow")
        assert hasattr(effects, "add_border")
        assert hasattr(effects, "add_background")
        assert hasattr(effects, "round_corners")
        assert hasattr(effects, "adjust_brightness_contrast")
        assert hasattr(effects, "invert_colors")
        assert hasattr(effects, "grayscale")


class TestEffectsSierraAndSierra2Dither:
    """Test sierra dither options."""

    def test_add_shadow_callable(self):
        """Test add_shadow is callable."""
        from src.effects import add_shadow
        assert callable(add_shadow)

    def test_add_border_callable(self):
        """Test add_border is callable."""
        from src.effects import add_border
        assert callable(add_border)

    def test_add_background_callable(self):
        """Test add_background is callable."""
        from src.effects import add_background
        assert callable(add_background)

    def test_round_corners_callable(self):
        """Test round_corners is callable."""
        from src.effects import round_corners
        assert callable(round_corners)

    def test_adjust_brightness_contrast_callable(self):
        """Test adjust_brightness_contrast is callable."""
        from src.effects import adjust_brightness_contrast
        assert callable(adjust_brightness_contrast)

    def test_invert_colors_callable(self):
        """Test invert_colors is callable."""
        from src.effects import invert_colors
        assert callable(invert_colors)

    def test_grayscale_callable(self):
        """Test grayscale is callable."""
        from src.effects import grayscale
        assert callable(grayscale)


import pytest


def _create_test_pixbuf(width=100, height=100, color=(128, 64, 192)):
    """Create a test pixbuf with a solid color."""
    try:
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf

        # Create RGBA pixbuf
        pixbuf = GdkPixbuf.Pixbuf.new(
            GdkPixbuf.Colorspace.RGB, True, 8, width, height
        )
        # Fill with color
        r, g, b = color
        pixel = (r << 24) | (g << 16) | (b << 8) | 255  # RGBA
        pixbuf.fill(pixel)
        return pixbuf
    except Exception:
        return None


class TestEffectsWithRealPixbuf:
    """Test effects with real GTK pixbufs."""

    @pytest.fixture
    def pixbuf(self):
        """Create a test pixbuf."""
        pb = _create_test_pixbuf(100, 100, (128, 64, 192))
        if pb is None:
            pytest.skip("GTK not available")
        return pb

    def test_add_shadow_increases_dimensions(self, pixbuf):
        """Test add_shadow increases image dimensions."""
        from src.effects import add_shadow
        result = add_shadow(pixbuf, shadow_size=10, opacity=0.5)
        # Shadow adds padding on all sides
        assert result.get_width() == pixbuf.get_width() + 20
        assert result.get_height() == pixbuf.get_height() + 20

    def test_add_shadow_with_different_sizes(self, pixbuf):
        """Test add_shadow with various shadow sizes."""
        from src.effects import add_shadow
        for size in [5, 15, 25]:
            result = add_shadow(pixbuf, shadow_size=size, opacity=0.5)
            assert result.get_width() == pixbuf.get_width() + size * 2
            assert result.get_height() == pixbuf.get_height() + size * 2

    def test_add_border_increases_dimensions(self, pixbuf):
        """Test add_border increases image dimensions."""
        from src.effects import add_border
        result = add_border(pixbuf, border_width=5, color=(0, 0, 0, 1))
        assert result.get_width() == pixbuf.get_width() + 10
        assert result.get_height() == pixbuf.get_height() + 10

    def test_add_border_with_different_widths(self, pixbuf):
        """Test add_border with various border widths."""
        from src.effects import add_border
        for width in [2, 10, 20]:
            result = add_border(pixbuf, border_width=width)
            assert result.get_width() == pixbuf.get_width() + width * 2
            assert result.get_height() == pixbuf.get_height() + width * 2

    def test_add_background_increases_dimensions(self, pixbuf):
        """Test add_background increases image dimensions."""
        from src.effects import add_background
        result = add_background(pixbuf, bg_color=(1, 1, 1, 1), padding=20)
        assert result.get_width() == pixbuf.get_width() + 40
        assert result.get_height() == pixbuf.get_height() + 40

    def test_add_background_with_different_padding(self, pixbuf):
        """Test add_background with various padding values."""
        from src.effects import add_background
        for pad in [10, 30, 50]:
            result = add_background(pixbuf, padding=pad)
            assert result.get_width() == pixbuf.get_width() + pad * 2
            assert result.get_height() == pixbuf.get_height() + pad * 2

    def test_round_corners_preserves_dimensions(self, pixbuf):
        """Test round_corners preserves image dimensions."""
        from src.effects import round_corners
        result = round_corners(pixbuf, radius=10)
        assert result.get_width() == pixbuf.get_width()
        assert result.get_height() == pixbuf.get_height()

    def test_round_corners_with_different_radii(self, pixbuf):
        """Test round_corners with various radii."""
        from src.effects import round_corners
        for radius in [5, 20, 40]:
            result = round_corners(pixbuf, radius=radius)
            assert result.get_width() == pixbuf.get_width()
            assert result.get_height() == pixbuf.get_height()

    def test_adjust_brightness_contrast_preserves_dimensions(self, pixbuf):
        """Test adjust_brightness_contrast preserves dimensions."""
        from src.effects import adjust_brightness_contrast
        result = adjust_brightness_contrast(pixbuf, brightness=0.5, contrast=0.5)
        assert result.get_width() == pixbuf.get_width()
        assert result.get_height() == pixbuf.get_height()

    def test_adjust_brightness_modifies_pixels(self, pixbuf):
        """Test that brightness adjustment modifies pixel values."""
        from src.effects import adjust_brightness_contrast
        original_pixels = bytes(pixbuf.get_pixels())
        result = adjust_brightness_contrast(pixbuf, brightness=0.5, contrast=0.0)
        result_pixels = bytes(result.get_pixels())
        # Pixels should be different after brightness adjustment
        assert original_pixels != result_pixels

    def test_adjust_contrast_modifies_pixels(self, pixbuf):
        """Test that contrast adjustment modifies pixel values."""
        from src.effects import adjust_brightness_contrast
        original_pixels = bytes(pixbuf.get_pixels())
        result = adjust_brightness_contrast(pixbuf, brightness=0.0, contrast=0.5)
        result_pixels = bytes(result.get_pixels())
        assert original_pixels != result_pixels

    def test_invert_colors_preserves_dimensions(self, pixbuf):
        """Test invert_colors preserves dimensions."""
        from src.effects import invert_colors
        result = invert_colors(pixbuf)
        assert result.get_width() == pixbuf.get_width()
        assert result.get_height() == pixbuf.get_height()

    def test_invert_colors_modifies_pixels(self, pixbuf):
        """Test that invert_colors modifies pixel values."""
        from src.effects import invert_colors
        original_pixels = bytes(pixbuf.get_pixels())
        result = invert_colors(pixbuf)
        result_pixels = bytes(result.get_pixels())
        assert original_pixels != result_pixels

    def test_grayscale_preserves_dimensions(self, pixbuf):
        """Test grayscale preserves dimensions."""
        from src.effects import grayscale
        result = grayscale(pixbuf)
        assert result.get_width() == pixbuf.get_width()
        assert result.get_height() == pixbuf.get_height()

    def test_grayscale_modifies_pixels(self, pixbuf):
        """Test that grayscale modifies pixel values."""
        from src.effects import grayscale
        original_pixels = bytes(pixbuf.get_pixels())
        result = grayscale(pixbuf)
        result_pixels = bytes(result.get_pixels())
        assert original_pixels != result_pixels


class TestEffectsChaining:
    """Test chaining multiple effects together."""

    @pytest.fixture
    def pixbuf(self):
        """Create a test pixbuf."""
        pb = _create_test_pixbuf(80, 60, (100, 150, 200))
        if pb is None:
            pytest.skip("GTK not available")
        return pb

    def test_shadow_then_border(self, pixbuf):
        """Test applying shadow then border."""
        from src.effects import add_shadow, add_border
        shadow_size = 10
        border_width = 5
        result = add_shadow(pixbuf, shadow_size=shadow_size)
        result = add_border(result, border_width=border_width)
        expected_w = pixbuf.get_width() + shadow_size * 2 + border_width * 2
        expected_h = pixbuf.get_height() + shadow_size * 2 + border_width * 2
        assert result.get_width() == expected_w
        assert result.get_height() == expected_h

    def test_grayscale_then_invert(self, pixbuf):
        """Test applying grayscale then invert."""
        from src.effects import grayscale, invert_colors
        result = grayscale(pixbuf)
        result = invert_colors(result)
        assert result.get_width() == pixbuf.get_width()
        assert result.get_height() == pixbuf.get_height()

    def test_all_effects_combined(self, pixbuf):
        """Test applying multiple effects in sequence."""
        from src.effects import (
            add_shadow, add_border, add_background,
            round_corners, adjust_brightness_contrast
        )
        # Start with original
        result = pixbuf
        original_w, original_h = result.get_width(), result.get_height()

        # Apply brightness/contrast (preserves size)
        result = adjust_brightness_contrast(result, brightness=0.1, contrast=0.2)
        assert result.get_width() == original_w

        # Apply round corners (preserves size)
        result = round_corners(result, radius=5)
        assert result.get_width() == original_w

        # Apply shadow (increases size)
        shadow_size = 8
        result = add_shadow(result, shadow_size=shadow_size)
        assert result.get_width() == original_w + shadow_size * 2

        # Apply border (increases size further)
        border_width = 3
        result = add_border(result, border_width=border_width)
        expected_w = original_w + shadow_size * 2 + border_width * 2
        assert result.get_width() == expected_w


class TestEffectsPixelValues:
    """Test specific pixel value transformations."""

    @pytest.fixture
    def small_pixbuf(self):
        """Create a small 2x2 pixbuf for precise testing."""
        pb = _create_test_pixbuf(2, 2, (100, 150, 200))
        if pb is None:
            pytest.skip("GTK not available")
        return pb

    def test_brightness_increase_brightens_pixels(self, small_pixbuf):
        """Test that positive brightness makes pixels brighter."""
        from src.effects import adjust_brightness_contrast
        original = small_pixbuf.get_pixels()[0]  # First red value
        result = adjust_brightness_contrast(small_pixbuf, brightness=0.5, contrast=0.0)
        modified = result.get_pixels()[0]  # First red value after
        # Brightness 0.5 adds 127 to values (clamped to 255)
        assert modified > original or modified == 255

    def test_brightness_decrease_darkens_pixels(self, small_pixbuf):
        """Test that negative brightness makes pixels darker."""
        from src.effects import adjust_brightness_contrast
        original = small_pixbuf.get_pixels()[0]
        result = adjust_brightness_contrast(small_pixbuf, brightness=-0.5, contrast=0.0)
        modified = result.get_pixels()[0]
        assert modified < original or modified == 0

    def test_invert_colors_inverts_rgb(self, small_pixbuf):
        """Test that invert_colors inverts RGB values."""
        from src.effects import invert_colors
        original_r = small_pixbuf.get_pixels()[0]
        result = invert_colors(small_pixbuf)
        inverted_r = result.get_pixels()[0]
        # Inversion: new = 255 - old
        assert inverted_r == 255 - original_r

    def test_grayscale_equalizes_rgb(self, small_pixbuf):
        """Test that grayscale makes R=G=B."""
        from src.effects import grayscale
        result = grayscale(small_pixbuf)
        pixels = result.get_pixels()
        # For RGBA, check first pixel's RGB are equal
        r, g, b = pixels[0], pixels[1], pixels[2]
        assert r == g == b
