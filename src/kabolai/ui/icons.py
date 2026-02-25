"""Generate system tray icons using PIL."""

from PIL import Image, ImageDraw


def create_icon(active: bool = True, size: int = 64) -> Image.Image:
    """Create a system tray icon.

    Args:
        active: True = green (active), False = red (inactive)
        size: Icon size in pixels

    Returns:
        PIL Image object.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    bg_color = (34, 139, 34, 230) if active else (178, 34, 34, 230)
    draw.ellipse([2, 2, size - 2, size - 2], fill=bg_color)

    # Inner "K" letter
    center = size // 2
    color = (255, 255, 255, 255)
    line_width = max(2, size // 16)

    # K letter shape
    x_start = size // 4
    x_end = size * 3 // 4
    y_top = size // 4
    y_bot = size * 3 // 4
    y_mid = center

    # Vertical line of K
    draw.line([(x_start, y_top), (x_start, y_bot)], fill=color, width=line_width)
    # Upper diagonal
    draw.line([(x_start, y_mid), (x_end, y_top)], fill=color, width=line_width)
    # Lower diagonal
    draw.line([(x_start, y_mid), (x_end, y_bot)], fill=color, width=line_width)

    return img


def create_listening_icon(size: int = 64) -> Image.Image:
    """Create a pulsing blue icon for listening state."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=(30, 100, 200, 230))

    # Microphone shape
    center = size // 2
    mic_w = size // 6
    mic_h = size // 3
    color = (255, 255, 255, 255)
    line_width = max(2, size // 16)

    # Mic body (rounded rect approximated with ellipse + rect)
    draw.ellipse(
        [center - mic_w, size // 4, center + mic_w, size // 4 + mic_h],
        fill=color,
    )
    # Mic stand
    draw.line(
        [(center, size // 4 + mic_h), (center, size * 3 // 4)],
        fill=color, width=line_width,
    )
    # Mic base
    draw.line(
        [(center - mic_w, size * 3 // 4), (center + mic_w, size * 3 // 4)],
        fill=color, width=line_width,
    )

    return img
