"""
Icon generator for system tray and Mac menu bar.

Mac menu bar : black on transparent (template image — macOS inverts for dark/light mode)
Windows tray : white mic on colored circle
"""

from PIL import Image, ImageDraw


def make_icon(recording: bool = False, platform: str | None = None) -> Image.Image:
    import sys
    plat = platform or sys.platform
    if plat == "darwin":
        return _make_mac_icon(recording)
    return _make_windows_icon(recording)


# ------------------------------------------------------------------
# Mac — monochrome template image (22x22, black on transparent)
# ------------------------------------------------------------------

def _make_mac_icon(recording: bool = False) -> Image.Image:
    SCALE = 4
    S = 22 * SCALE  # draw at 88x88, scale to 22x22

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx = S // 2
    color = (180, 40, 40, 255) if recording else (0, 0, 0, 255)
    lw = max(2, SCALE - 1)

    # --- Mic capsule body ---
    body_w = int(S * 0.30)
    body_h = int(S * 0.40)
    bx0 = cx - body_w // 2
    by0 = int(S * 0.08)
    bx1 = cx + body_w // 2
    by1 = by0 + body_h
    radius = body_w // 2
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=radius, fill=color)

    # --- Stand arc ---
    arc_margin = int(S * 0.18)
    arc_top    = int(S * 0.40)
    arc_bottom = int(S * 0.68)
    d.arc(
        [arc_margin, arc_top, S - arc_margin, arc_bottom],
        start=0, end=180,
        fill=color, width=lw,
    )

    # --- Stem ---
    stem_top    = arc_bottom - lw
    stem_bottom = int(S * 0.80)
    d.rectangle([cx - lw // 2, stem_top, cx + lw // 2, stem_bottom], fill=color)

    # --- Base ---
    base_w  = int(S * 0.36)
    base_y  = stem_bottom
    base_lw = lw
    d.rectangle(
        [cx - base_w // 2, base_y, cx + base_w // 2, base_y + base_lw],
        fill=color,
    )

    # Scale down with antialiasing
    return img.resize((22, 22), Image.LANCZOS)


# ------------------------------------------------------------------
# Windows — white mic on coloured circle (64x64)
# ------------------------------------------------------------------

def _make_windows_icon(recording: bool = False) -> Image.Image:
    SCALE = 4
    BASE = 64
    S = BASE * SCALE

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background circle
    bg = (210, 45, 45, 255) if recording else (37, 99, 235, 255)
    pad = SCALE * 2
    d.ellipse([pad, pad, S - pad, S - pad], fill=bg)

    cx = S // 2
    white = (255, 255, 255, 255)
    lw = SCALE

    # --- Mic capsule body ---
    body_w = int(S * 0.22)
    body_h = int(S * 0.32)
    bx0 = cx - body_w // 2
    by0 = int(S * 0.14)
    bx1 = cx + body_w // 2
    by1 = by0 + body_h
    radius = body_w // 2
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=radius, fill=white)

    # --- Stand arc ---
    arc_margin = int(S * 0.22)
    arc_top    = int(S * 0.34)
    arc_bottom = int(S * 0.58)
    d.arc(
        [arc_margin, arc_top, S - arc_margin, arc_bottom],
        start=0, end=180,
        fill=white, width=lw,
    )

    # --- Stem ---
    stem_top    = arc_bottom - lw
    stem_bottom = int(S * 0.70)
    d.rectangle([cx - lw // 2, stem_top, cx + lw // 2, stem_bottom], fill=white)

    # --- Base ---
    base_w = int(S * 0.28)
    base_y = stem_bottom
    d.rectangle(
        [cx - base_w // 2, base_y, cx + base_w // 2, base_y + lw],
        fill=white,
    )

    return img.resize((BASE, BASE), Image.LANCZOS)


# ------------------------------------------------------------------
# Save pre-rendered assets (run this file directly to regenerate)
# ------------------------------------------------------------------

if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).parent.parent / "assets"
    out.mkdir(exist_ok=True)

    _make_mac_icon(recording=False).save(out / "menubar_idle.png")
    _make_mac_icon(recording=True).save(out / "menubar_recording.png")
    _make_windows_icon(recording=False).save(out / "tray_idle.png")
    _make_windows_icon(recording=True).save(out / "tray_recording.png")
    print("Icons saved to assets/")
