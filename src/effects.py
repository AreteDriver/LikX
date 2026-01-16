"""Advanced effects for screenshots - shadows, borders, backgrounds."""

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gdk, GdkPixbuf

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


def add_shadow(pixbuf, shadow_size: int = 10, opacity: float = 0.5):
    """Add drop shadow to image."""
    try:
        import cairo

        old_width = pixbuf.get_width()
        old_height = pixbuf.get_height()
        new_width = old_width + shadow_size * 2
        new_height = old_height + shadow_size * 2

        # Create new surface with room for shadow
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, new_width, new_height)
        ctx = cairo.Context(surface)

        # Draw shadow (simple blur approximation)
        for i in range(shadow_size, 0, -1):
            alpha = (opacity / shadow_size) * (shadow_size - i + 1)
            ctx.set_source_rgba(0, 0, 0, alpha)
            ctx.rectangle(
                shadow_size - i + shadow_size,
                shadow_size - i + shadow_size,
                old_width + i * 2,
                old_height + i * 2,
            )
            ctx.fill()

        # Draw original image on top
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, shadow_size, shadow_size)
        ctx.paint()

        # Convert back to pixbuf
        data = surface.get_data()
        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            new_width,
            new_height,
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, new_width),
        )

        return new_pixbuf
    except Exception as e:
        print(f"Shadow effect failed: {e}")
        return pixbuf


def add_border(pixbuf, border_width: int = 5, color: tuple = (0, 0, 0, 1)):
    """Add colored border to image."""
    try:
        import cairo

        old_width = pixbuf.get_width()
        old_height = pixbuf.get_height()
        new_width = old_width + border_width * 2
        new_height = old_height + border_width * 2

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, new_width, new_height)
        ctx = cairo.Context(surface)

        # Draw border
        ctx.set_source_rgba(*color)
        ctx.rectangle(0, 0, new_width, new_height)
        ctx.fill()

        # Draw image
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, border_width, border_width)
        ctx.paint()

        data = surface.get_data()
        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            new_width,
            new_height,
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, new_width),
        )

        return new_pixbuf
    except Exception as e:
        print(f"Border effect failed: {e}")
        return pixbuf


def add_background(pixbuf, bg_color: tuple = (1, 1, 1, 1), padding: int = 20):
    """Add colored background with padding."""
    try:
        import cairo

        old_width = pixbuf.get_width()
        old_height = pixbuf.get_height()
        new_width = old_width + padding * 2
        new_height = old_height + padding * 2

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, new_width, new_height)
        ctx = cairo.Context(surface)

        # Draw background
        ctx.set_source_rgba(*bg_color)
        ctx.rectangle(0, 0, new_width, new_height)
        ctx.fill()

        # Draw image
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, padding, padding)
        ctx.paint()

        data = surface.get_data()
        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            new_width,
            new_height,
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, new_width),
        )

        return new_pixbuf
    except Exception as e:
        print(f"Background effect failed: {e}")
        return pixbuf


def round_corners(pixbuf, radius: int = 10):
    """Round the corners of an image."""
    try:
        import math

        import cairo

        width = pixbuf.get_width()
        height = pixbuf.get_height()

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        # Create rounded rectangle path
        ctx.new_sub_path()
        ctx.arc(width - radius, radius, radius, -math.pi / 2, 0)
        ctx.arc(width - radius, height - radius, radius, 0, math.pi / 2)
        ctx.arc(radius, height - radius, radius, math.pi / 2, math.pi)
        ctx.arc(radius, radius, radius, math.pi, 3 * math.pi / 2)
        ctx.close_path()

        # Clip to rounded rectangle
        ctx.clip()

        # Draw image
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        ctx.paint()

        data = surface.get_data()
        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            width,
            height,
            cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width),
        )

        return new_pixbuf
    except Exception as e:
        print(f"Round corners failed: {e}")
        return pixbuf


def adjust_brightness_contrast(pixbuf, brightness: float = 0.0, contrast: float = 0.0):
    """Adjust brightness and contrast of an image.

    Args:
        pixbuf: Source GdkPixbuf.
        brightness: Brightness adjustment (-1.0 to 1.0, 0 = no change).
        contrast: Contrast adjustment (-1.0 to 1.0, 0 = no change).

    Returns:
        Adjusted pixbuf.
    """
    try:
        import array

        width = pixbuf.get_width()
        height = pixbuf.get_height()
        has_alpha = pixbuf.get_has_alpha()
        n_channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()

        new_pixels = array.array("B", pixels)

        # Convert brightness/contrast to usable factors
        # Brightness: shift values (add/subtract)
        # Contrast: multiply around midpoint
        brightness_offset = int(brightness * 255)
        contrast_factor = 1.0 + contrast  # 0 -> 1.0, 1.0 -> 2.0, -1.0 -> 0.0

        for y in range(height):
            for x in range(width):
                offset = y * rowstride + x * n_channels

                for c in range(3):  # RGB only, not alpha
                    val = pixels[offset + c]

                    # Apply contrast (around 128)
                    val = int((val - 128) * contrast_factor + 128)

                    # Apply brightness
                    val = val + brightness_offset

                    # Clamp to 0-255
                    new_pixels[offset + c] = max(0, min(255, val))

        # Create new pixbuf
        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            new_pixels.tobytes(),
            pixbuf.get_colorspace(),
            has_alpha,
            pixbuf.get_bits_per_sample(),
            width,
            height,
            rowstride,
        )

        return new_pixbuf
    except Exception as e:
        print(f"Brightness/contrast adjustment failed: {e}")
        return pixbuf


def invert_colors(pixbuf):
    """Invert the colors of an image (negative effect)."""
    try:
        import array

        width = pixbuf.get_width()
        height = pixbuf.get_height()
        has_alpha = pixbuf.get_has_alpha()
        n_channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()

        new_pixels = array.array("B", pixels)

        for y in range(height):
            for x in range(width):
                offset = y * rowstride + x * n_channels

                for c in range(3):  # RGB only, not alpha
                    new_pixels[offset + c] = 255 - pixels[offset + c]

        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            new_pixels.tobytes(),
            pixbuf.get_colorspace(),
            has_alpha,
            pixbuf.get_bits_per_sample(),
            width,
            height,
            rowstride,
        )

        return new_pixbuf
    except Exception as e:
        print(f"Invert colors failed: {e}")
        return pixbuf


def grayscale(pixbuf):
    """Convert image to grayscale."""
    try:
        import array

        width = pixbuf.get_width()
        height = pixbuf.get_height()
        has_alpha = pixbuf.get_has_alpha()
        n_channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()

        new_pixels = array.array("B", pixels)

        for y in range(height):
            for x in range(width):
                offset = y * rowstride + x * n_channels

                # Weighted grayscale (human perception)
                r = pixels[offset]
                g = pixels[offset + 1]
                b = pixels[offset + 2]
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)

                new_pixels[offset] = gray
                new_pixels[offset + 1] = gray
                new_pixels[offset + 2] = gray

        new_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            new_pixels.tobytes(),
            pixbuf.get_colorspace(),
            has_alpha,
            pixbuf.get_bits_per_sample(),
            width,
            height,
            rowstride,
        )

        return new_pixbuf
    except Exception as e:
        print(f"Grayscale conversion failed: {e}")
        return pixbuf
