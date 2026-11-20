"""Stand-in sprites for the carried lights (lights.py, 2026-11-19).

Each light gets its OWN picture (item art is the item: never a borrowed
one, never a letter glyph), made in code from an approved painted sprite of
the same kind of thing: the painted torch, the painted lantern, the painted
oil lamp, the painted ember, recoloured and marked so each reads as itself
on the 40 px map tile. Nothing approved is overwritten: every file written
here is new.

These are STAND-INS. Code-made icons were retired for the arsenal on
2026-11-16 (Brandon: "looks like the old art we had"), so the real pictures
should be painted by the pipeline from briefs/lights_2026_11_19.json when
ComfyUI is running; installing those replaces these files.

    assets/tiles/items/<id>.png      the eight lights (data/items/light.json)
    LIGHTS_ART_SHEET.png (repo root) review sheet

The sprites are 64 px, so their ids are listed in installed_items.json
(tests/test_art_pass.py: an item sprite is 64 px only when listed there).

    py tools/content/genart/lights_art.py            write every file above
    py tools/content/genart/lights_art.py --sheet    the review sheet only
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ITEMS = os.path.join(ROOT, 'assets', 'tiles', 'items')
sys.path.insert(0, HERE)

from arsenal_art import N, _glow, _grey, _hue, _load, _recolour  # noqa: E402


def _bbox(im: Image.Image):
    a = np.array(im)[..., 3]
    ys, xs = np.nonzero(a > 40)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _flame_at(im: Image.Image, cx: int, base: int, size: int = 9,
              colours=((255, 240, 170), (255, 180, 60), (225, 90, 25))) -> Image.Image:
    out = im.copy()
    d = ImageDraw.Draw(out)
    for k, col in enumerate(reversed(colours)):
        s = size - k * 3
        if s <= 1:
            continue
        d.polygon([(cx - s // 2 - 1, base), (cx + s // 2 + 1, base), (cx, base - s - 3)],
                  fill=col + (255,))
    return out


def _recolour_warm(im: Image.Image, lo_hue: float, hi_hue: float, hue: float,
                   sat=None, light=1.0) -> Image.Image:
    """Recolour only the pixels whose hue lies in [lo_hue, hi_hue] (0-1):
    a flame kept, a handle changed."""
    import colorsys
    a = np.array(im).astype(np.float32) / 255.0
    out = a.copy()
    for y in range(N):
        for x in range(N):
            r, g, b, al = a[y, x]
            if al <= 0.01:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
            if not (lo_hue <= hh <= hi_hue) or ll < 0.1:
                continue
            ss2 = ss if sat is None else sat * (0.35 + 0.65 * ss)
            r2, g2, b2 = colorsys.hls_to_rgb(hue, min(1.0, ll * light), min(1.0, ss2))
            out[y, x, :3] = (r2, g2, b2)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def _shutter(im: Image.Image, share: float = 0.5, dark=(28, 26, 26)) -> Image.Image:
    """Close the right part of a lantern: its iron shutter."""
    a = np.array(im)
    x0, y0, x1, y1 = _bbox(im)
    cut = int(x0 + (x1 - x0) * (1.0 - share))
    for y in range(y0 + 6, y1 - 2):
        for x in range(cut, x1 + 1):
            if a[y, x, 3] > 40:
                a[y, x, :3] = (np.array(a[y, x, :3], dtype=np.float32) * 0.25
                               + np.array(dark, dtype=np.float32) * 0.75).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


# ------------------------------------------------------------- the sprites

def torch():
    """A plain pitch torch: the painted torch, its stick a raw pine brown."""
    im = _recolour_warm(_load('wand_of_torch_light'), 0.0, 0.07, _hue(28), sat=0.55, light=1.1)
    return _glow(im, (255, 200, 120), 55)


def horn_lantern():
    """A tin lantern with pale horn windows."""
    im = _recolour(_load('lantern_of_diogenes'), _hue(40), sat=0.35, light=1.05)
    return _glow(im, (255, 225, 150), 60)


def dark_lantern():
    """An iron lantern, its shutter half closed over the light."""
    src = _load('lantern_of_diogenes')
    im = _grey(src, light=0.7, tint=(1.0, 0.97, 0.92))
    # The one window still open glows warm: the painted lantern's own light,
    # kept on the open side.
    s = np.array(src).astype(np.int32)
    a = np.array(im)
    x0, _y0, x1, _y1 = _bbox(src)
    mid = (x0 + x1) // 2
    warm = (s[..., 0] > 200) & (s[..., 1] > 120) & (s[..., 2] < 120) & (s[..., 3] > 40)
    warm[:, mid:] = False
    a[warm] = s[warm].astype(np.uint8)
    return _shutter(Image.fromarray(a, 'RGBA'), 0.5, dark=(18, 16, 16))


def everburning_lamp():
    """A pale silver oil lamp with a steady white flame."""
    im = _grey(_load('aladdins_lamp'), light=1.3, tint=(1.0, 1.0, 0.95))
    x0, y0, x1, y1 = _bbox(im)
    im = _flame_at(im, x1 - 3, y0 + (y1 - y0) // 3, 9,
                   ((255, 255, 245), (235, 240, 255), (190, 205, 255)))
    return _glow(im, (240, 240, 255), 60)


def jacks_lantern():
    """A pale turnip, purple at the top, with a hellfire ember in it."""
    im = _recolour(_load('amon_wrath_ember'), _hue(285), sat=0.25, light=1.9, keep_dark=0.05)
    a = np.array(im).astype(np.float32)
    src = np.array(_load('amon_wrath_ember')).astype(np.float32)
    # The glowing cracks stay the ember's own orange: the coal inside.
    hot = (src[..., 0] > 180) & (src[..., 1] > 60) & (src[..., 2] < 90) & (src[..., 3] > 40)
    a[hot] = src[hot]
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = _bbox(im)
    cx = (x0 + x1) // 2
    for dx, h in ((-4, 9), (0, 12), (4, 8)):
        d.line([(cx, y0 + 2), (cx + dx, y0 - h + 4)], fill=(70, 140, 50, 255), width=2)
    return _glow(im, (255, 150, 60), 45)


def psyches_lamp():
    """A small terracotta oil lamp, lit."""
    im = _recolour(_load('aladdins_lamp'), _hue(16), sat=0.6, light=0.95)
    x0, y0, x1, y1 = _bbox(im)
    im = _flame_at(im, x1 - 3, y0 + (y1 - y0) // 3, 8)
    return _glow(im, (255, 210, 140), 50)


def heros_lamp():
    """A bronze window lamp hung on a chain."""
    im = _recolour(_load('lantern_of_diogenes'), _hue(26), sat=0.65, light=0.85)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = _bbox(im)
    cx = (x0 + x1) // 2
    for y in range(1, max(2, y0), 3):
        d.ellipse([cx - 1, y, cx + 1, y + 2], outline=(150, 110, 60, 255))
    return _glow(im, (255, 215, 140), 60)


def hecates_torch():
    """A black torch with a pale, smokeless flame."""
    base = _load('prometheus_torch')
    im = _grey(base, light=0.32, tint=(0.95, 0.95, 1.05))
    src = np.array(base).astype(np.float32)
    a = np.array(im).astype(np.float32)
    # The flame: the saturated orange at the head (the shaft's bands are not:
    # only the top of the sprite).
    flame = ((src[..., 0] > 170) & (src[..., 3] > 40) & (src[..., 2] < 90)
             & (src[..., 0] - src[..., 2] > 120))
    _x0, y0, _x1, _y1 = _bbox(base)
    flame[y0 + 18:, :] = False
    lum = (0.3 * src[..., 0] + 0.59 * src[..., 1] + 0.11 * src[..., 2])
    for i, t in enumerate((0.88, 0.93, 1.05)):
        a[..., i] = np.where(flame, np.clip(lum * t + 40, 0, 255), a[..., i])
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return _glow(im, (210, 225, 255), 70)


SPRITES = {
    'torch': torch, 'horn_lantern': horn_lantern, 'dark_lantern': dark_lantern,
    'everburning_lamp': everburning_lamp, 'jacks_lantern': jacks_lantern,
    'psyches_lamp': psyches_lamp, 'heros_lamp': heros_lamp, 'hecates_torch': hecates_torch,
}


def sheet(images: dict) -> Image.Image:
    cols = 4
    rows = (len(images) + cols - 1) // cols
    cell = 140
    out = Image.new('RGBA', (cols * cell, rows * (cell + 20)), (34, 36, 48, 255))
    d = ImageDraw.Draw(out)
    for i, (name, im) in enumerate(images.items()):
        x, y = (i % cols) * cell, (i // cols) * (cell + 20)
        out.alpha_composite(im.resize((128, 128), Image.NEAREST), (x + 6, y + 4))
        out.alpha_composite(im.resize((40, 40), Image.LANCZOS), (x + 96, y + 92))
        d.text((x + 6, y + cell - 4), name, fill=(240, 240, 240, 255))
    return out


def _install(ids) -> None:
    """List the new 64 px sprites in installed_items.json (test_art_pass)."""
    path = os.path.join(HERE, 'installed_items.json')
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    have = set(d.get('items', []))
    d['items'] = sorted(have | set(ids))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)
        f.write('\n')


def main(argv) -> None:
    images = {k: f() for k, f in SPRITES.items()}
    if '--sheet' not in argv:
        for k, im in images.items():
            im.save(os.path.join(ITEMS, f"{k}.png"))
        _install(images)
    sheet(images).save(os.path.join(ROOT, 'LIGHTS_ART_SHEET.png'))
    print(f"{len(images)} sprites")


if __name__ == '__main__':
    main(sys.argv[1:])
