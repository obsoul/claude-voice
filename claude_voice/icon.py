from PIL import Image, ImageDraw


def make_icon(recording: bool = False) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    bg = (220, 50, 50) if recording else (40, 120, 200)
    draw.ellipse([2, 2, size - 2, size - 2], fill=bg)

    # Microphone body
    mic_w, mic_h = 16, 22
    x0 = (size - mic_w) // 2
    y0 = 10
    draw.rounded_rectangle([x0, y0, x0 + mic_w, y0 + mic_h], radius=8, fill="white")

    # Mic stand arc
    arc_box = [x0 - 6, y0 + 10, x0 + mic_w + 6, y0 + mic_h + 14]
    draw.arc(arc_box, start=0, end=180, fill="white", width=3)

    # Stand line
    cx = size // 2
    draw.line([cx, y0 + mic_h + 14, cx, y0 + mic_h + 18], fill="white", width=3)
    draw.line([cx - 6, y0 + mic_h + 18, cx + 6, y0 + mic_h + 18], fill="white", width=3)

    return img
