"""
Generate assets/icon.ico — a multi-resolution Windows icon for Philosopher's Quest.

Theme: golden Phi (Φ) glyph on a deep-navy radial-gradient background,
surrounded by a warm glow and four small star-sparks at the corners.
Sizes baked in: 16, 24, 32, 48, 64, 128, 256 px.

Run from the project root:
    python data/gen_icon.py
"""

import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
SIZES = [256, 128, 64, 48, 32, 24, 16]


# ── colour palette ──────────────────────────────────────────────────────────
BG_OUTER  = (10,  8, 28)          # near-black navy
BG_INNER  = (30, 22, 70)          # deep purple-navy at centre
GLOW_COL  = (200, 155, 30, 180)   # warm amber glow (RGBA)
GOLD_LT   = (255, 230, 100)       # bright highlight
GOLD_MID  = (220, 175,  40)       # mid-gold
GOLD_DRK  = (160, 110,  10)       # shadow side of glyph
STAR_COL  = (255, 245, 180)       # tiny sparkle colour


def _radial_bg(size: int) -> Image.Image:
    """Deep navy radial gradient, lighter at centre."""
    img = Image.new('RGBA', (size, size))
    cx = cy = size / 2
    r_max = size * 0.72
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / r_max
            t = min(1.0, d)
            r = int(BG_OUTER[0] + (BG_INNER[0] - BG_OUTER[0]) * (1 - t))
            g = int(BG_OUTER[1] + (BG_INNER[1] - BG_OUTER[1]) * (1 - t))
            b = int(BG_OUTER[2] + (BG_INNER[2] - BG_OUTER[2]) * (1 - t))
            img.putpixel((x, y), (r, g, b, 255))
    return img


def _draw_glow(draw: ImageDraw.ImageDraw, size: int):
    """Soft amber ellipse glow behind the glyph."""
    cx = cy = size / 2
    rw = size * 0.38
    rh = size * 0.42
    for i in range(6, 0, -1):
        alpha = int(30 + i * 12)
        ex = rw + i * size * 0.022
        ey = rh + i * size * 0.025
        draw.ellipse(
            [cx - ex, cy - ey, cx + ex, cy + ey],
            fill=(*GLOW_COL[:3], alpha),
        )


def _draw_phi(draw: ImageDraw.ImageDraw, size: int):
    """
    Hand-drawn Phi (Φ) glyph using thick arcs and a vertical bar.
    Scales cleanly from 16 px to 256 px.
    """
    cx = cy = size / 2
    # The circle part of Phi
    r_outer = size * 0.30
    r_inner = size * 0.19
    lw = max(1, int(size * 0.065))   # stroke width

    # Outer ring — gradient from light to dark around the arc
    for angle_deg in range(0, 360, 2):
        a = math.radians(angle_deg)
        # shade: bright at top-left, dark at bottom-right
        shade_t = (math.sin(a + math.pi * 0.75) + 1) / 2
        r = int(GOLD_DRK[0] + (GOLD_LT[0] - GOLD_DRK[0]) * shade_t)
        g = int(GOLD_DRK[1] + (GOLD_LT[1] - GOLD_DRK[1]) * shade_t)
        b = int(GOLD_DRK[2] + (GOLD_LT[2] - GOLD_DRK[2]) * shade_t)
        px = cx + r_outer * math.cos(a)
        py = cy + r_outer * math.sin(a)
        hw = max(1, lw // 2)
        draw.ellipse([px - hw, py - hw, px + hw, py + hw], fill=(r, g, b, 255))

    # Filled interior disc (dark, so Phi looks like a ring)
    draw.ellipse(
        [cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
        fill=(*BG_INNER, 255),
    )

    # Vertical bar of Phi, extends above and below the circle
    bar_h   = r_outer * 1.40
    bar_w   = max(1, int(size * 0.060))
    # Draw bar with a highlight on the left edge
    draw.rectangle(
        [cx - bar_w, cy - bar_h, cx + bar_w, cy + bar_h],
        fill=GOLD_MID,
    )
    # Highlight strip
    draw.rectangle(
        [cx - bar_w, cy - bar_h, cx - bar_w + max(1, bar_w // 2), cy + bar_h],
        fill=GOLD_LT,
    )
    # Shadow strip on right
    draw.rectangle(
        [cx + bar_w - max(1, bar_w // 2), cy - bar_h, cx + bar_w, cy + bar_h],
        fill=GOLD_DRK,
    )


def _draw_stars(draw: ImageDraw.ImageDraw, size: int):
    """Four tiny four-pointed star sparks near the corners of the glyph."""
    if size < 32:
        return   # too small — skip
    cx = cy = size / 2
    offsets = [(-0.34, -0.38), (0.36, -0.33), (-0.30, 0.37), (0.33, 0.34)]
    for ox, oy in offsets:
        sx = cx + ox * size
        sy = cy + oy * size
        r  = max(1, size * 0.025)
        # horizontal and vertical bars of star
        draw.line([sx - r * 2.5, sy, sx + r * 2.5, sy], fill=STAR_COL, width=max(1, int(r * 0.7)))
        draw.line([sx, sy - r * 2.5, sx, sy + r * 2.5], fill=STAR_COL, width=max(1, int(r * 0.7)))
        # diagonal bars (shorter)
        d = r * 1.4
        draw.line([sx - d, sy - d, sx + d, sy + d], fill=STAR_COL, width=max(1, int(r * 0.4)))
        draw.line([sx + d, sy - d, sx - d, sy + d], fill=STAR_COL, width=max(1, int(r * 0.4)))
        # bright centre dot
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=STAR_COL)


def _make_frame(size: int) -> Image.Image:
    img  = _radial_bg(size)
    draw = ImageDraw.Draw(img, 'RGBA')
    _draw_glow(draw, size)
    _draw_phi(draw, size)
    _draw_stars(draw, size)
    # Very light edge vignette
    if size >= 48:
        vignette = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vignette)
        for i in range(5):
            alpha = 20 + i * 10
            vd.rectangle([i, i, size - 1 - i, size - 1 - i],
                         outline=(0, 0, 0, alpha), width=1)
        img = Image.alpha_composite(img, vignette)
    return img


def main():
    frames = [_make_frame(s) for s in SIZES]
    # PIL needs RGBA for .ico with transparency
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    frames[0].save(
        OUT,
        format='ICO',
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Icon written: {OUT}  ({len(SIZES)} sizes: {SIZES})")


if __name__ == '__main__':
    main()
