"""The arsenal's tools, drawn from the game's own art (winning-build plan
2026-11-13, slice 5).

Every coating, flask and named counter gets its own sprite (item art is the
item: never a letter glyph). Each is made from an existing approved sprite of
the same kind of thing, recoloured and marked so it reads as itself on the
40 px map tile: a potion bottle becomes a flask of fire oil with a flame at
its neck, a heap of grave dust becomes silver dust with a glint on it, a
buckler is polished into a mirror shield. Nothing approved is overwritten:
every file written here is new.

    assets/tiles/items/<id>.png            the twelve coatings and flasks,
                                           beeswax_earplugs, cold_iron_charm
    assets/tiles/items/iron_mirror_shield.png   the mirror shield (the
                                           renderer's stand-in for every metal's
                                           <material>_mirror_shield)
    ARSENAL_ART_SHEET.png (repo root)      review sheet

The sprites are 64 px, so their ids are listed in installed_items.json
(tests/test_art_pass.py: an item sprite is 64 px only when listed there).

Plain Pillow and numpy:

    py tools/content/genart/arsenal_art.py           write every file above
    py tools/content/genart/arsenal_art.py --sheet   the review sheet only
"""
from __future__ import annotations

import colorsys
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ITEMS = os.path.join(ROOT, 'assets', 'tiles', 'items')
N = 64


def _load(name: str) -> Image.Image:
    im = Image.open(os.path.join(ITEMS, f"{name}.png")).convert('RGBA')
    if im.size != (N, N):
        im = im.resize((N, N), Image.NEAREST)
    return im


def _recolour(im: Image.Image, hue: float, sat: float | None = None,
              light: float = 1.0, keep_dark: float = 0.12) -> Image.Image:
    """Every coloured pixel to ``hue`` (0-1), its lightness kept (times
    ``light``); near-black outline pixels kept as they are."""
    a = np.array(im).astype(np.float32) / 255.0
    out = a.copy()
    h, w = a.shape[:2]
    for y in range(h):
        for x in range(w):
            r, g, b, al = a[y, x]
            if al <= 0.01:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
            if ll < keep_dark:
                continue
            ss2 = ss if sat is None else sat * (0.35 + 0.65 * ss)
            r2, g2, b2 = colorsys.hls_to_rgb(hue, min(1.0, ll * light), min(1.0, ss2))
            out[y, x, :3] = (r2, g2, b2)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def _grey(im: Image.Image, light: float = 1.0, tint=(1.0, 1.0, 1.0)) -> Image.Image:
    a = np.array(im).astype(np.float32)
    lum = (0.30 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]) * light
    for i in range(3):
        a[..., i] = np.where(a[..., 3] > 0, np.clip(lum * tint[i], 0, 255), a[..., i])
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def _top_of(im: Image.Image) -> tuple:
    """(x, y) of the topmost opaque pixel's column centre: the neck."""
    a = np.array(im)[..., 3]
    ys, xs = np.nonzero(a > 40)
    if not len(ys):
        return N // 2, 8
    y0 = int(ys.min())
    row = xs[ys == y0]
    return int(row.mean()), y0


def _flame(im: Image.Image, colours=((255, 236, 140), (255, 170, 50), (220, 80, 20)),
           size: int = 9) -> Image.Image:
    """A small flame on the flask's neck (a lit rag)."""
    out = im.copy()
    d = ImageDraw.Draw(out)
    cx, top = _top_of(im)
    base = max(size + 1, top + 2)
    for k, col in enumerate(reversed(colours)):
        s = size - k * 3
        if s <= 1:
            continue
        d.polygon([(cx - s // 2 - 1, base), (cx + s // 2 + 1, base), (cx, base - s - 3)],
                  fill=col + (255,))
    return out


def _glints(im: Image.Image, pts, col=(255, 255, 255)) -> Image.Image:
    out = im.copy()
    d = ImageDraw.Draw(out)
    for x, y in pts:
        d.line([(x - 2, y), (x + 2, y)], fill=col + (255,))
        d.line([(x, y - 2), (x, y + 2)], fill=col + (255,))
    return out


def _fumes(im: Image.Image, col=(200, 240, 120)) -> Image.Image:
    out = im.copy()
    d = ImageDraw.Draw(out)
    cx, top = _top_of(im)
    for i, (dx, dy) in enumerate(((-3, -3), (2, -7), (-1, -11))):
        r = 2 + (i % 2)
        y = max(1, top + dy)
        d.ellipse([cx + dx - r, y - r, cx + dx + r, y + r], fill=col + (150,))
    return out


def _glow(im: Image.Image, col=(255, 240, 170), alpha: int = 70) -> Image.Image:
    """A soft halo behind the sprite."""
    a = np.array(im)[..., 3] > 30
    halo = np.zeros((N, N), dtype=bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                halo |= np.roll(np.roll(a, dy, 0), dx, 1)
    under = np.zeros((N, N, 4), dtype=np.uint8)
    under[halo & ~a] = col + (alpha,)
    base = Image.fromarray(under, 'RGBA')
    base.alpha_composite(im)
    return base


def _hue(deg: float) -> float:
    return (deg % 360) / 360.0


# ------------------------------------------------------------- the sprites

def silver_dust():
    im = _grey(_load('crypt_dust'), light=1.25, tint=(1.0, 1.02, 1.08))
    return _glints(im, [(30, 26), (40, 33)], (255, 255, 255))


def frost_salts():
    im = _recolour(_load('dragon_salt'), _hue(198), sat=0.55, light=1.05)
    return _glints(im, [(28, 24), (38, 30)], (230, 250, 255))


def viper_venom():
    return _recolour(_load('potion_of_poison'), _hue(82), sat=0.75)


def flask_of_holy_water():
    return _load('holy_water')


def water_of_siloam():
    return _glints(_recolour(_load('holy_water'), _hue(205), sat=0.35, light=1.0), [(44, 20)])


def water_of_life():
    im = _recolour(_load('potion_of_invisibility'), _hue(48), sat=0.5, light=1.12)
    return _glints(im, [(22, 20), (44, 30)], (255, 250, 220))


def flask_of_fire_oil():
    return _flame(_recolour(_load('potion_of_restore_strength'), _hue(30), sat=0.85))


def greek_fire():
    return _flame(_recolour(_load('potion_of_regeneration'), _hue(14), sat=0.6, light=0.85), size=11)


def medeas_fire():
    im = _recolour(_load('potion_of_fear'), _hue(10), sat=0.4, light=0.55)
    return _flame(im, size=11)


def flask_of_acid():
    return _fumes(_recolour(_load('potion_of_stamina'), _hue(78), sat=0.85), (190, 240, 90))


def aqua_regia():
    return _fumes(_recolour(_load('potion_of_heroism'), _hue(38), sat=0.9), (240, 200, 90))


def alkahest():
    return _fumes(_recolour(_load('potion_of_invisibility'), _hue(150), sat=0.45, light=1.05),
                  (200, 255, 225))


def beeswax_earplugs():
    """Two lumps of yellow wax on a twist of cloth."""
    up = 4
    im = Image.new('RGBA', (N * up, N * up), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    line = (60, 40, 20, 255)
    d.polygon([(40 * 1, 150), (210, 130), (225, 175), (55, 200)], fill=(196, 186, 160, 255),
              outline=line, width=6)
    for cx, cy in ((95, 140), (160, 128)):
        d.ellipse([cx - 34, cy - 30, cx + 34, cy + 30], fill=(214, 160, 40, 255), outline=line, width=6)
        d.ellipse([cx - 22, cy - 20, cx + 8, cy - 4], fill=(250, 214, 110, 255))
        d.ellipse([cx - 12, cy - 16, cx - 2, cy - 8], fill=(255, 240, 190, 255))
    return im.resize((N, N), Image.LANCZOS)


def cold_iron_charm():
    """A horseshoe nail of cold iron hung on a red thread."""
    up = 4
    im = Image.new('RGBA', (N * up, N * up), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    line = (24, 24, 30, 255)
    d.line([(70, 30), (128, 70), (186, 30)], fill=(190, 30, 40, 255), width=10)
    d.line([(70, 30), (128, 70), (186, 30)], fill=(120, 10, 20, 255), width=3)
    d.ellipse([110, 58, 146, 86], fill=(150, 150, 158, 255), outline=line, width=6)
    d.polygon([(110, 80), (146, 80), (138, 210), (128, 236), (118, 210)],
              fill=(122, 126, 136, 255), outline=line, width=6)
    d.line([(122, 92), (124, 200)], fill=(196, 200, 210, 255), width=5)
    return im.resize((N, N), Image.LANCZOS)


def iron_mirror_shield():
    """The buckler polished to a mirror: bright, with a streak of reflection."""
    im = _grey(_load('iron_buckler'), light=1.35, tint=(1.0, 1.03, 1.08))
    a = np.array(im)
    d = ImageDraw.Draw(im)
    ys, xs = np.nonzero(a[..., 3] > 40)
    if len(xs):
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        for k in range(3):
            d.line([(x0 + 10 + 4 * k, y1 - 14), (x1 - 14 + 4 * k, y0 + 10)],
                   fill=(255, 255, 255, 170 - 40 * k), width=2)
    return im


SPRITES = {
    'silver_dust': silver_dust, 'frost_salts': frost_salts, 'viper_venom': viper_venom,
    'flask_of_holy_water': flask_of_holy_water, 'water_of_siloam': water_of_siloam,
    'water_of_life': water_of_life, 'flask_of_fire_oil': flask_of_fire_oil,
    'greek_fire': greek_fire, 'medeas_fire': medeas_fire, 'flask_of_acid': flask_of_acid,
    'aqua_regia': aqua_regia, 'alkahest': alkahest,
    'beeswax_earplugs': beeswax_earplugs, 'cold_iron_charm': cold_iron_charm,
    'iron_mirror_shield': iron_mirror_shield,
}


def sheet(images: dict) -> Image.Image:
    cols = 5
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


def main(argv) -> None:
    images = {k: f() for k, f in SPRITES.items()}
    if '--sheet' not in argv:
        for k, im in images.items():
            path = os.path.join(ITEMS, f"{k}.png")
            im.save(path)
    sheet(images).save(os.path.join(ROOT, 'ARSENAL_ART_SHEET.png'))
    print(f"{len(images)} sprites")


if __name__ == '__main__':
    main(sys.argv[1:])
