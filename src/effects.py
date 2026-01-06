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
        import cairo
        import math

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
