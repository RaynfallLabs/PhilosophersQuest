"""Shared helpers for the monster_C slice (animals, dragons, reptiles, plants, pets)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core  # noqa: E402
from core import shade, BONE, IVORY, STEEL, IRON, WOOD, LEATHER, DARK, GOLD, STRING  # noqa: E402,F401


class Sprite(core.Sprite):
    """core.Sprite plus a safety net: nothing painted may sit on the outermost ring,
    so the 1px outline always fits inside the tile."""

    def finish(self):
        px = self.img.load()
        for i in range(core.S):
            for x, y in ((i, 0), (i, core.S - 1), (0, i), (core.S - 1, i)):
                px[x, y] = (0, 0, 0, 0)
        return super().finish()

REG = {}


def reg(*ids):
    def deco(fn):
        for i in ids:
            REG[i] = fn
        return fn
    return deco


sh = shade
WHITE = (240, 240, 236)
PINK = (226, 140, 150)
RED = (200, 50, 44)
FIRE = (255, 150, 40)
FIRE2 = (255, 220, 90)
ICE = (170, 225, 255)
BOLT = (255, 240, 110)
VENOM = (150, 240, 90)
SKIN = (222, 176, 136)
WATER = (60, 120, 200)
FOAM = (200, 230, 250)


def tup(c, default=(150, 120, 90)):
    return tuple(c) if c else default


def vivid(c, vmin=0.45, smin=0.0, vmax=1.0):
    """Lift a muddy/near-black data colour into something that shades well."""
    import colorsys
    r, g, b = [v / 255 for v in c]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = max(vmin, min(vmax, v)); s = max(smin, s)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def smooth(pts, n=8):
    """Catmull-Rom through the points."""
    if len(pts) < 3:
        out = []
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        for i in range(n + 1):
            t = i / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        return out
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b[k]) + (-a[k] + c[k]) * t + (2 * a[k] - 5 * b[k] + 4 * c[k] - d[k]) * t2
                                    + (-a[k] + 3 * b[k] - 3 * c[k] + d[k]) * t3) for k in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def tube(s, pts, c, w0=3.0, w1=None, bands=None, belly=None, n=8):
    """A tapering round tube along a smooth curve: snakes, necks, tails, vines.
    w0/w1 are diameters. bands=(colour, period, width). belly=colour paints the underside."""
    if w1 is None:
        w1 = w0
    sp = smooth(pts, n)
    m = len(sp) - 1

    def dot(x, y, w, col):
        if w <= 1.2:
            s.px([(int(round(x)), int(round(y)))], col)
        elif w <= 2.2:
            xi, yi = int(round(x - 0.5)), int(round(y - 0.5))
            s.rect(xi, yi, xi + 1, yi + 1, col)
        else:
            r = w / 2
            s.ell(int(round(x - r)), int(round(y - r)), int(round(x + r)), int(round(y + r)), col)
    for i, (x, y) in enumerate(sp):
        w = w0 + (w1 - w0) * i / max(1, m)
        dot(x, y, w, c)
    if belly:
        for i, (x, y) in enumerate(sp):
            w = w0 + (w1 - w0) * i / max(1, m)
            if w >= 3:
                dot(x, y + w / 2 - 0.6, max(1.0, w / 2 - 0.5), belly)
    if bands:
        bc, per, bw = bands
        for i, (x, y) in enumerate(sp):
            w = w0 + (w1 - w0) * i / max(1, m)
            if i % per < bw and w > 1.2:
                dot(x, y - 0.5, max(1.0, w - 2), bc)
    return sp


def flame(s, x, y, h=5, c1=None, c2=None):
    """A small flame rising from (x, y) as its base centre."""
    c1 = s.lit(c1 or FIRE); c2 = s.lit(c2 or FIRE2)
    s.poly([(x - 2, y), (x - 1, y - h + 2), (x, y - h), (x + 1, y - h + 3), (x + 2, y)], c1)
    s.line([(x, y), (x, y - max(1, h - 3))], c2)


def breath(s, x, y, c, n=3, dx=1, dy=1):
    """A puff of breath weapon heading right-down from the mouth."""
    c = s.lit(c)
    for i in range(n):
        s.px([(x + i * dx, y + i * dy), (x + i * dx + 1, y + i * dy)], c)


def spark(s, pts, c):
    c = s.lit(c)
    s.px(pts, c)


def bolt(s, x, y, c=BOLT, flip=False):
    c = s.lit(c)
    d = -1 if flip else 1
    s.px([(x, y), (x + d, y + 1), (x, y + 2), (x - d, y + 2), (x, y + 3), (x + d, y + 4)], c)
