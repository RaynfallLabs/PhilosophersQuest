"""The Bloomleaf Cloak, drawn in code (winning-build plan 2026-11-13, section 3.8).

A cloak of broad green leaves torn from a young Bloomsaur's back, beaded with
rain. It is drawn once as the item, and laid over existing sprites so the
creature under it stays exactly himself (Brandon: the fire line's art is
approved; it is never overwritten, a cloaked copy is a NEW file):

  * assets/tiles/items/bloomleaf_cloak.png           the cloak itself
  * assets/tiles/monsters/old_nickel.png             the kobold who wears it (kobold.png + cloak)
  * assets/tiles/monsters/npc_abandoned_emberpup_sheltered.png   the pup on his rock, cloak left over him
  * assets/tiles/monsters/emberpup_cloaked.png       the special Emberpup, every stage
  * assets/tiles/monsters/flamescale_cloaked.png
  * assets/tiles/monsters/infernodrake_cloaked.png
  * EMBERPUP_CLOAK_ART_SHEET.png (repo root)         review sheet: each sprite before and after

Each leaf is an almond drawn at 4x, shaded from the upper left, with a dark
midrib; the cloak is cut down to 64 px, its colours snapped to a small green
palette, and outlined where it meets anything else, so it reads on the
40 px map tile. A few pale beads of water sit on the leaves.

Plain Pillow and numpy (no ComfyUI, no scipy):

    py tools/content/genart/bloomleaf.py            write every file above
    py tools/content/genart/bloomleaf.py --sheet    the review sheet only
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MON = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
ITEMS = os.path.join(ROOT, 'assets', 'tiles', 'items')

N = 64
UP = 4                                   # drawn at 4x, cut down to 64

# The Bloomsaur's own greens (bloomsaur.png), light to dark, and the outline.
PALETTE = {
    'hi':   (168, 222, 92),
    'lite': (122, 190, 66),
    'mid':  (82, 152, 50),
    'dark': (50, 108, 38),
    'deep': (34, 76, 30),
    'line': (18, 40, 18),
    'bead': (214, 240, 255),
    'beadd': (120, 178, 214),
    'stem': (112, 92, 52),
}
_SNAP = [PALETTE[k] for k in ('hi', 'lite', 'mid', 'dark', 'deep')]


def _leaf(draw, cx, cy, ang, length, width, shade=0.0):
    """One leaf: base at (cx, cy) in 64 px units, pointing along `ang`
    (degrees, 0 = straight down, positive = toward +x), at 4x."""
    a = math.radians(ang)
    dx, dy = math.sin(a), math.cos(a)            # along the leaf
    px, py = dy, -dx                             # across it (to its left)
    steps = 14
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        w = width * 0.5 * math.sin(math.pi * min(1.0, t ** 0.75)) * (1.0 - 0.15 * t)
        x = cx + dx * length * t
        y = cy + dy * length * t
        left.append(((x + px * w) * UP, (y + py * w) * UP))
        right.append(((x - px * w) * UP, (y - py * w) * UP))
    # Two halves: the half toward the light (upper left) a step brighter.
    lit_left = (px * -1 + py * -1) > 0           # is the leaf's left side toward the upper left?
    spine = [((cx + dx * length * t) * UP, (cy + dy * length * t) * UP)
             for t in (i / steps for i in range(steps + 1))]
    light, dim = ('lite', 'mid') if shade <= 0.3 else ('mid', 'dark')
    if shade < -0.3:
        light, dim = 'hi', 'lite'
    a_col, b_col = (light, dim) if lit_left else (dim, light)
    draw.polygon(left + spine[::-1], fill=PALETTE[a_col] + (255,))
    draw.polygon(right + spine[::-1], fill=PALETTE[b_col] + (255,))
    # the midrib, two thirds of the way down
    draw.line(spine[2:int(steps * 0.65)], fill=PALETTE['dark'] + (255,), width=max(1, UP - 1))


def _bead(draw, x, y):
    draw.rectangle([x * UP, y * UP, x * UP + UP - 1, y * UP + UP - 1], fill=PALETTE['bead'] + (255,))
    draw.rectangle([x * UP, (y + 1) * UP, x * UP + UP - 1, (y + 1) * UP + UP - 1],
                   fill=PALETTE['beadd'] + (255,))


def cape(rows, beads=(), stems=()):
    """The cloak layer, 64 px RGBA. `rows` is a list of leaves
    (x, y, angle, length, width, shade) drawn in order: the first are the
    lowest, the last overlap them like shingles. `beads` are (x, y) water
    drops; `stems` are (x0, y0, x1, y1) grass twists at the clasp."""
    big = Image.new('RGBA', (N * UP, N * UP), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for leaf in rows:
        _leaf(d, *leaf)
    for x0, y0, x1, y1 in stems:
        d.line([(x0 * UP, y0 * UP), (x1 * UP, y1 * UP)], fill=PALETTE['stem'] + (255,), width=UP)
    small = big.resize((N, N), Image.BOX)
    a = np.asarray(small).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    keep = al >= 110
    out = np.zeros((N, N, 4), np.uint8)
    # un-premultiply what the box filter mixed with the empty corners
    safe = np.maximum(al, 1)[..., None] / 255.0
    rgb = np.clip(rgb / safe, 0, 255)
    pal = np.array(_SNAP + [PALETTE['stem']], np.float32)
    dist = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
    snapped = pal[dist.argmin(-1)]
    out[..., :3] = snapped.astype(np.uint8)
    out[..., 3] = np.where(keep, 255, 0)
    img = Image.fromarray(out, 'RGBA').copy()
    px = img.load()
    for x, y in beads:
        if 0 <= x < N and 0 <= y + 1 < N and px[x, y][3] and px[x, y + 1][3]:
            px[x, y] = PALETTE['bead'] + (255,)
            px[x, y + 1] = PALETTE['beadd'] + (255,)
    return img


def outline(layer, under=None):
    """A one-pixel dark line round the cloak: on its own edge pixels that
    touch anything that is not cloak (the empty tile or the creature)."""
    a = np.asarray(layer).copy()
    m = a[..., 3] > 0
    edge = np.zeros_like(m)
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(np.roll(m, sy, 0), sx, 1)
        if sx == 1:
            sh[:, 0] = False
        if sx == -1:
            sh[:, -1] = False
        if sy == 1:
            sh[0, :] = False
        if sy == -1:
            sh[-1, :] = False
        edge |= m & ~sh
    # Water beads keep their light pixel; everything else on the edge goes dark.
    bead = (a[..., 0] == PALETTE['bead'][0]) & (a[..., 1] == PALETTE['bead'][1])
    line = edge & ~bead
    a[line, :3] = PALETTE['line']
    return Image.fromarray(a, 'RGBA')


def wear(base_path, layer, out_path=None, ring=True):
    """The creature with the cloak laid over him. Outside the cloak the
    picture is untouched; a dark ring is drawn where the cloak's edge stands
    on the empty tile, so the new silhouette has the house outline."""
    base = Image.open(base_path).convert('RGBA')
    lay = outline(layer)
    out = base.copy()
    out.alpha_composite(lay)
    if ring:
        a = np.asarray(out).copy()
        cm = np.asarray(lay)[..., 3] > 0
        empty = a[..., 3] == 0
        grow = np.zeros_like(cm)
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            grow |= np.roll(np.roll(cm, sy, 0), sx, 1)
        rim = grow & empty
        a[rim] = PALETTE['line'] + (255,)
        out = Image.fromarray(a, 'RGBA')
    if out_path:
        out.save(out_path)
    return out


# ------------------------------------------------------------------ layouts
# Leaves: (x, y, angle, length, width, shade); shade < 0 lighter, > 0.3 darker.

def _drape(top, bottom, wt, wb, rows, per, length, width, fan=18, lean=0.0, shade_by_row=True):
    """A cape of `rows` rows of leaves hanging from `top` toward `bottom`
    (64 px points), `wt` and `wb` half-widths at the top and the hem. Rows
    are listed hem first so the upper ones overlap them."""
    out = []
    (x0, y0), (x1, y1) = top, bottom
    for r in range(rows - 1, -1, -1):
        t = r / max(1, rows - 1)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        hw = wt + (wb - wt) * t
        k = per if r else max(2, per - 1)
        for i in range(k):
            u = (i / (k - 1) - 0.5) * 2 if k > 1 else 0.0       # -1 .. 1 across the row
            x = cx + u * hw
            ang = lean + u * fan
            shade = (0.4 if (shade_by_row and r == rows - 1) else 0.0) + (0.35 if u > 0.4 else 0.0) \
                - (0.4 if u < -0.4 and r < rows - 1 else 0.0)
            if (i + r) % 2:
                shade += 0.35                    # every other leaf a shade darker: each one reads
            out.append((x, cy, ang, length, width, shade))
    return out


def item_layout():
    """The cloak on its own: a hanging cloak, a leaf collar at the throat."""
    rows = _drape((32, 10), (32, 40), 7, 15, rows=5, per=5, length=15, width=10, fan=26)
    collar = [(25, 8, -70, 9, 7, -0.5), (39, 8, 70, 9, 7, 0.4), (29, 7, -25, 9, 7, -0.5),
              (35, 7, 25, 9, 7, 0.0)]
    beads = [(24, 22), (36, 26), (30, 34), (41, 37), (22, 39), (33, 46), (27, 15), (38, 15)]
    stems = [(28, 7, 36, 7)]
    return rows + collar, beads, stems


def emberpup_layout():
    """Stage 1: a small pup facing left; the cloak at his neck, down his back."""
    rows = _drape((35, 21), (40, 38), 3, 5, rows=4, per=2, length=10, width=7, fan=18, lean=16)
    collar = [(27, 20, -50, 6, 5, -0.5), (31, 19, -10, 7, 6, -0.4), (35, 19, 30, 8, 6, 0.0)]
    beads = [(37, 26), (40, 32), (36, 36), (42, 40), (29, 22)]
    stems = [(28, 19, 35, 18)]
    return rows + collar, beads, stems


def flamescale_layout():
    """Stage 2: taller, facing left; cloak from the neck down his back."""
    rows = _drape((34, 18), (38, 38), 3, 5, rows=5, per=2, length=10, width=7, fan=16, lean=14)
    collar = [(26, 17, -50, 6, 5, -0.5), (30, 16, -10, 7, 6, -0.4), (34, 16, 30, 8, 6, 0.0)]
    beads = [(36, 23), (39, 29), (35, 33), (40, 38), (28, 19)]
    stems = [(27, 16, 34, 15)]
    return rows + collar, beads, stems


def infernodrake_layout():
    """Stage 3: front-facing, wings spread; a mantle of leaves on both
    shoulders, clasped at the throat, the chest and the wings left clear."""
    left = _drape((24, 15), (21, 26), 1, 3, rows=3, per=2, length=8, width=6, fan=14, lean=-18)
    right = _drape((34, 15), (37, 26), 1, 3, rows=3, per=2, length=8, width=6, fan=14, lean=18)
    collar = [(25, 13, -70, 6, 5, -0.5), (33, 13, 70, 6, 5, 0.3)]
    beads = [(22, 19), (36, 20), (20, 25), (38, 26)]
    stems = [(26, 13, 32, 13)]
    return left + right + collar, beads, stems


def sheltered_pup_layout():
    """The pup on his rock with the cloak left over his back."""
    rows = _drape((33, 30), (29, 43), 3, 6, rows=3, per=2, length=10, width=7, fan=20, lean=-14)
    collar = [(31, 29, -40, 7, 6, -0.4), (36, 28, 0, 7, 6, -0.3), (40, 29, 35, 6, 5, 0.3)]
    beads = [(30, 34), (34, 37), (27, 40), (32, 44), (37, 31)]
    stems = [(32, 28, 40, 28)]
    return rows + collar, beads, stems


def nickel_layout():
    """Old Nickel: the kobold (facing right, spear in hand) with the stolen
    cloak hanging from his shoulders down his back."""
    rows = _drape((25, 26), (19, 46), 5, 9, rows=4, per=3, length=11, width=8, fan=24, lean=-10)
    collar = [(19, 25, -50, 8, 6, -0.5), (24, 24, -15, 9, 6, -0.4), (30, 24, 25, 8, 6, 0.0)]
    beads = [(18, 30), (24, 34), (15, 40), (22, 44), (28, 28)]
    stems = [(20, 24, 30, 23)]
    return rows + collar, beads, stems


TARGETS = [
    # (base sprite in monsters/, output path, layout)
    ('kobold', os.path.join(MON, 'old_nickel.png'), nickel_layout),
    ('npc_abandoned_emberpup', os.path.join(MON, 'npc_abandoned_emberpup_sheltered.png'), sheltered_pup_layout),
    ('emberpup', os.path.join(MON, 'emberpup_cloaked.png'), emberpup_layout),
    ('flamescale', os.path.join(MON, 'flamescale_cloaked.png'), flamescale_layout),
    ('infernodrake', os.path.join(MON, 'infernodrake_cloaked.png'), infernodrake_layout),
]


def make_item():
    rows, beads, stems = item_layout()
    lay = outline(cape(rows, beads, stems))
    lay.save(os.path.join(ITEMS, 'bloomleaf_cloak.png'))
    return lay


def make_all(write=True):
    pairs = []
    item = make_item() if write else Image.open(os.path.join(ITEMS, 'bloomleaf_cloak.png')).convert('RGBA')
    pairs.append((None, item, 'Bloomleaf Cloak (item)'))
    for base, out, layout in TARGETS:
        rows, beads, stems = layout()
        before = Image.open(os.path.join(MON, base + '.png')).convert('RGBA')
        after = wear(os.path.join(MON, base + '.png'), cape(rows, beads, stems),
                     out if write else None)
        pairs.append((before, after, os.path.basename(out)[:-4]))
    return pairs


def sheet(pairs, path):
    """Each sprite before and after, at 6x and at map size (40 px), on the
    floor colour."""
    Z = 6
    cell = N * Z
    w = 2 * cell + 40 * 2 + 80
    h = len(pairs) * (cell + 34) + 20
    s = Image.new('RGBA', (w, h), (34, 34, 42, 255))
    d = ImageDraw.Draw(s)
    y = 10
    for before, after, label in pairs:
        d.text((10, y), label, fill=(240, 220, 150, 255))
        y += 16
        x = 10
        for img in (before, after):
            if img is not None:
                s.alpha_composite(img.resize((cell, cell), Image.NEAREST), (x, y))
            x += cell + 10
        for img in (before, after):
            if img is not None:
                s.alpha_composite(img.resize((40, 40), Image.LANCZOS), (x, y + cell // 2 - 20))
            x += 50
        y += cell + 18
    s.save(path)


def main(argv):
    write = '--sheet' not in argv
    pairs = make_all(write=write)
    path = os.path.join(ROOT, 'EMBERPUP_CLOAK_ART_SHEET.png')
    sheet(pairs, path)
    print('wrote' if write else 'sheet only:', path)


if __name__ == '__main__':
    main(sys.argv[1:])
