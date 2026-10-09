"""Armor and shield rigs: material palettes, surfaces and one drawer per template.
Offline tooling (not loaded at runtime)."""
import math
import os
import random
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Sprite, shade, GOLD, STEEL, IRON, DARK  # noqa: E402

LEATHER = (112, 74, 46)
T0 = (0, 0, 0, 0)


class A(Sprite):
    """Sprite with mirror helpers (mirror axis x = 15.5) and pixel queries."""

    def __init__(self):
        super().__init__()
        self.shadow = False

    def sym(self, pts, c):
        self.poly(pts + [(31 - x, y) for x, y in reversed(pts)], c)

    def mpoly(self, pts, c):
        self.poly(pts, c); self.poly([(31 - x, y) for x, y in pts], c)

    def mrect(self, x0, y0, x1, y1, c):
        self.rect(x0, y0, x1, y1, c); self.rect(31 - x1, y0, 31 - x0, y1, c)

    def mell(self, x0, y0, x1, y1, c):
        self.ell(x0, y0, x1, y1, c); self.ell(31 - x1, y0, 31 - x0, y1, c)

    def mline(self, pts, c, w=1):
        self.line(pts, c, w); self.line([(31 - x, y) for x, y in pts], c, w)

    def mpx(self, pts, c):
        self.px(pts, c); self.px([(31 - x, y) for x, y in pts], c)

    def cell(self, x0, y0, x1, y1): self.d.ellipse([x0, y0, x1, y1], fill=T0)
    def crect(self, x0, y0, x1, y1): self.d.rectangle([x0, y0, x1, y1], fill=T0)
    def cpoly(self, pts): self.d.polygon(pts, fill=T0)
    def cpx(self, pts):
        for x, y in pts:
            if 0 <= x < 32 and 0 <= y < 32:
                self.img.putpixel((x, y), T0)

    def get(self, x, y):
        if not (0 <= x < 32 and 0 <= y < 32):
            return None
        p = self.img.getpixel((x, y))
        return p[:3] if p[3] else None

    def pts(self, *cols):
        px = self.img.load()
        return [(x, y) for y in range(32) for x in range(32) if px[x, y][3] and px[x, y][:3] in cols]

    def over(self, cols, fn):
        if not isinstance(cols, (list, tuple, set)) or (cols and isinstance(cols[0], int)):
            cols = [cols]
        for x, y in self.pts(*cols):
            c = fn(x, y)
            if c:
                self.img.putpixel((x, y), c + (255,))

    def clip(self):
        """Keep the 1px outline inside the tile."""
        px = self.img.load()
        for i in range(32):
            px[i, 0] = T0; px[i, 31] = T0; px[0, i] = T0; px[31, i] = T0


# ------------------------------------------------------------ materials
#            base              trim              class      surface      glow
MATS = {
    'linen':            ((224, 214, 186), (150, 118, 80), 'cloth', 'weave', None),
    'canvas':           ((178, 160, 110), (100, 82, 54), 'cloth', 'hatch', None),
    'silk':             ((236, 196, 96), (176, 56, 66), 'cloth', 'sheen', None),
    'elven_silk':       ((140, 218, 222), (236, 244, 246), 'cloth', 'sheen', (232, 255, 250)),
    'spider_silk':      ((198, 192, 226), (90, 80, 130), 'cloth', 'web', None),
    'leather':          ((164, 106, 56), (92, 56, 32), 'leather', 'stitch', None),
    'studded_leather':  ((104, 66, 46), (190, 194, 204), 'leather', 'studs', None),
    'hide':             ((140, 100, 66), (226, 208, 172), 'leather', 'fur', None),
    'rawhide':          ((210, 176, 128), (118, 82, 54), 'leather', 'lace', None),
    'dragonhide':       ((208, 92, 54), (250, 192, 84), 'leather', 'pebble', None),
    'ash':              ((216, 198, 152), (150, 124, 84), 'wood', 'grain', None),
    'oak':              ((152, 104, 56), (86, 58, 34), 'wood', 'knot', None),
    'yew':              ((198, 126, 66), (242, 210, 150), 'wood', 'twotone', None),
    'ironwood':         ((84, 72, 68), (156, 156, 168), 'wood', 'grain', None),
    'dragonwood':       ((126, 50, 46), (62, 24, 28), 'wood', 'ember', (255, 156, 40)),
    'silverbark':       ((224, 226, 216), (68, 68, 76), 'wood', 'birch', None),
    'petrified_wood':   ((152, 118, 100), (94, 88, 96), 'wood', 'bands', None),
    'worldtree':        ((238, 224, 160), (104, 166, 78), 'wood', 'leaf', (150, 240, 120)),
    'copper':           ((208, 112, 66), (86, 164, 132), 'metal', 'verdigris', None),
    'bronze':           ((192, 142, 58), (108, 72, 34), 'metal', 'streak', None),
    'tempered_bronze':  ((168, 92, 50), (236, 194, 98), 'metal', 'streak', None),
    'iron':             ((140, 142, 148), (84, 84, 92), 'metal', 'streak', None),
    'ring_iron':        ((120, 116, 114), (176, 92, 48), 'metal', 'rust', None),
    'chain_steel':      ((166, 172, 186), (94, 98, 116), 'metal', 'streak', None),
    'steel':            ((198, 208, 222), (108, 118, 150), 'metal', 'streak2', None),
    'cold_iron':        ((100, 116, 148), (214, 230, 244), 'metal', 'frost', None),
    'cobalt_steel':     ((66, 112, 208), (192, 212, 242), 'metal', 'streak', None),
    'damascus_steel':   ((180, 182, 202), (92, 92, 122), 'metal', 'wavy', None),
    'dwarven_plate':    ((112, 122, 142), (228, 180, 62), 'metal', 'streak', None),
    'tungsten':         ((96, 100, 96), (58, 60, 62), 'metal', 'dull', None),
    'hematite':         ((118, 46, 52), (214, 128, 128), 'metal', 'glint', None),
    'adamantine':       ((58, 80, 106), (96, 226, 204), 'metal', 'edge', None),
    'mithril':          ((172, 208, 234), (252, 254, 255), 'metal', 'sparkle', (255, 255, 255)),
    'silver':           ((224, 226, 234), (138, 144, 170), 'metal', 'streak2', None),
    'hardened_gold':    ((228, 182, 56), (150, 94, 28), 'metal', 'sparkle', (255, 250, 210)),
    'orichalcum':       ((238, 132, 46), (255, 222, 120), 'metal', 'veins', (255, 226, 130)),
    'quicksilver':      ((196, 220, 232), (116, 146, 168), 'metal', 'mirror', None),
    'shadowiron':       ((48, 44, 68), (124, 92, 176), 'metal', 'shadow', None),
    'starmetal':        ((146, 162, 232), (255, 255, 255), 'metal', 'stars', (255, 255, 255)),
    'sunsteel':         ((250, 206, 90), (255, 250, 204), 'metal', 'sun', (255, 250, 204)),
    'soulsteel':        ((146, 194, 186), (196, 255, 232), 'metal', 'wisps', (196, 255, 232)),
    'void_touched':     ((66, 24, 90), (232, 92, 250), 'metal', 'void', (232, 92, 250)),
    'glassteel':        ((186, 220, 242), (250, 255, 255), 'crystal', 'facet', (250, 255, 255)),
    'obsidian':         ((36, 28, 48), (152, 110, 204), 'crystal', 'flake', None),
    'dragonscale':      ((186, 54, 44), (242, 172, 70), 'scale', 'scales', None),
    'petrified_dragon': ((82, 66, 98), (154, 142, 164), 'scale', 'scales', None),
    'dragonbone':       ((238, 228, 198), (150, 130, 100), 'bone', 'pits', None),
}


class P:
    """A resolved palette for one drawing."""

    def __init__(self, s, base, trim, cls='metal', fx='streak', glow=None, seed=0):
        self.b = tuple(base); self.t = tuple(trim); self.cls = cls; self.fx = fx
        self.d = shade(self.b, -1); self.dd = shade(self.b, -2); self.l = shade(self.b, 1)
        self.td = shade(self.t, -1); self.tl = shade(self.t, 1)
        self.g = s.lit(tuple(glow)) if glow else None
        self.seed = seed
        lum = sum(self.b) / 3
        # a colour for rivets/studs that always shows on the base
        self.riv = shade(self.b, 2) if lum < 150 else shade(self.b, -2)
        if cls in ('metal', 'crystal', 'scale', 'bone'):
            self.strap = LEATHER
        elif cls == 'leather':
            self.strap = self.dd
        elif cls == 'wood':
            self.strap = (92, 62, 40)
        else:
            self.strap = self.t
        self.back = LEATHER if cls in ('metal', 'crystal', 'scale', 'bone', 'wood') else self.dd
        if abs(self.back[0] - self.b[0]) + abs(self.back[1] - self.b[1]) + abs(self.back[2] - self.b[2]) < 70:
            self.back = shade(self.back, -1)
        self.dark = (34, 28, 38)
        # clasp / buckle colour that is not the base
        yellowish = self.b[0] > 190 and self.b[1] > 150 and self.b[2] < 140
        self.clasp = (200, 204, 214) if yellowish else GOLD


def mat_palette(s, name, color=None, seed=0):
    if name in MATS:
        b, t, cls, fx, g = MATS[name]
    else:
        b = tuple(color) if color else (150, 150, 160)
        t, cls, fx, g = shade(b, -2), 'metal', 'streak', None
    return P(s, b, t, cls, fx, g, seed)


def h2(x, y, k=0):
    return zlib.crc32(('%d,%d,%d' % (x, y, k)).encode())


# ------------------------------------------------------------ surfaces
def surface(s, p, cols=None):
    """Material surface painted over the base-coloured pixels."""
    b = p.b
    pts = s.pts(*(cols or [b]))
    if len(pts) < 6:
        return
    S = set(pts)
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    fx, lt, dk, t = p.fx, p.l, p.d, p.t
    put = s.img.putpixel
    sd = p.seed

    def P_(x, y, c):
        if (x, y) in S:
            put((x, y), c + (255,))

    def inner(x, y):
        return all(q in S for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

    def streak(off=0.36, wd=2, c=lt):
        c0 = int(x0 + y0 + (w + h) * off)
        for x, y in pts:
            if 0 <= x + y - c0 < wd and inner(x, y):
                put((x, y), c + (255,))

    def specks(c, n, k=1, need_inner=True):
        for x, y in pts:
            if h2(x, y, sd + k) % n == 0 and (inner(x, y) or not need_inner):
                put((x, y), c + (255,))

    if fx in ('streak', 'rivet'):
        streak()
    elif fx == 'streak2':
        streak(0.30, 2); streak(0.44, 1)
    elif fx == 'weave':
        for x, y in pts:
            if y % 2 == 0 and (x + y // 2) % 3 == 0 and inner(x, y):
                put((x, y), dk + (255,))
    elif fx == 'hatch':
        for x, y in pts:
            if not inner(x, y):
                continue
            if (x + y) % 5 == 0:
                put((x, y), dk + (255,))
            elif (x - y) % 5 == 0:
                put((x, y), lt + (255,))
    elif fx == 'sheen':
        for x, y in pts:
            if (x + 2 * y) % 11 < 2 and inner(x, y):
                put((x, y), lt + (255,))
    elif fx == 'web':
        cx, cy = (x0 + x1) / 2, y0 + h * 0.35
        for x, y in pts:
            if not inner(x, y):
                continue
            r = math.hypot(x - cx, y - cy); a = math.atan2(y - cy, x - cx)
            spoke = abs(((a * 8 / (2 * math.pi)) % 1) - 0.5) > 0.5 - 0.5 / max(2.0, r)
            if spoke or int(r + 0.5) % 5 == 4:
                put((x, y), shade(b, 2) + (255,))
    elif fx in ('stitch', 'lace'):
        c = shade(b, 2) if fx == 'stitch' else t
        for x, y in pts:
            if inner(x, y) and any(q not in S for q in ((x - 2, y), (x + 2, y), (x, y - 2), (x, y + 2))):
                if (x + y) % 2 == 0:
                    put((x, y), c + (255,))
        if fx == 'lace':
            specks(dk, 9)
    elif fx == 'studs':
        for x, y in pts:
            if y % 4 == 1 and (x + 2 * ((y // 4) % 2)) % 4 == 1 and inner(x, y):
                put((x, y), t + (255,))
    elif fx == 'fur':
        for x, y in pts:
            k = h2(x, y, sd) % 9
            if k == 0 and inner(x, y):
                put((x, y), dk + (255,)); P_(x, y + 1, dk)
            elif (x, y + 1) not in S and (x + y) % 2 == 0:
                put((x, y), t + (255,))
    elif fx == 'pebble':
        for x, y in pts:
            if y % 3 == 0 and (x + (y // 3 % 2) * 2) % 3 == 0 and inner(x, y):
                put((x, y), dk + (255,))
    elif fx in ('grain', 'knot', 'twotone', 'ember', 'leaf'):
        if fx == 'twotone':
            for x, y in pts:
                if x - x0 < w * 0.38:
                    put((x, y), t + (255,))
        gc = dk
        for x, y in pts:
            if (x - x0) % 3 == 1 and h2(x, y // 4, sd) % 5 and inner(x, y):
                if fx == 'twotone' and x - x0 < w * 0.38:
                    put((x, y), shade(t, -1) + (255,))
                else:
                    put((x, y), gc + (255,))
        if fx == 'knot':
            kx, ky = x0 + w * 2 // 3, y0 + h * 2 // 5
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                P_(kx + dx, ky + dy, p.dd)
            P_(kx, ky, lt)
        if fx == 'ember':
            x = x0 + w // 2
            for y in range(y0 + 2, y1 - 1):
                x += (h2(x, y, sd) % 3) - 1
                x = max(x0 + 1, min(x1 - 1, x))
                if h2(y, 7, sd) % 3:
                    P_(x, y, p.g)
    elif fx == 'birch':
        for x, y in pts:
            if y % 4 == 1 and h2(x // 3, y, sd) % 3 == 0 and inner(x, y):
                put((x, y), t + (255,))
    elif fx == 'bands':
        for x, y in pts:
            if not inner(x, y):
                continue
            k = (y + (x // 6)) % 5
            if k == 0:
                put((x, y), t + (255,))
            elif k == 2:
                put((x, y), lt + (255,))
    elif fx == 'verdigris':
        streak()
        for x, y in pts:
            if ((x + 1, y) not in S or (x, y + 1) not in S) and h2(x, y, sd) % 2:
                put((x, y), t + (255,))
        specks(t, 13)
    elif fx == 'rust':
        specks(t, 7); specks(dk, 11, 3)
    elif fx == 'frost':
        streak(0.4, 1)
        for x, y in pts:
            if (x, y - 1) not in S and (x + y) % 2 == 0:
                put((x, y), t + (255,))
        specks(t, 17)
    elif fx == 'wavy':
        for x, y in pts:
            if (y + int(round(1.6 * math.sin(x * 0.9)))) % 3 == 0 and inner(x, y):
                put((x, y), t + (255,))
    elif fx == 'dull':
        specks(dk, 6); specks(lt, 13, 2)
    elif fx == 'glint':
        streak(0.34, 1, t); streak(0.52, 1, t)
    elif fx == 'edge':
        for x, y in pts:
            if (x - 1, y) not in S or (x, y - 1) not in S:
                put((x, y), t + (255,))
        streak(0.5, 1)
    elif fx == 'sparkle':
        streak(0.36, 2)
    elif fx == 'veins':
        for k in range(2):
            x = x0 + w * (1 + 2 * k) // 4
            for y in range(y0 + 1, y1):
                x += (h2(x, y, sd + k) % 3) - 1
                x = max(x0 + 1, min(x1 - 1, x))
                P_(x, y, p.g)
    elif fx == 'mirror':
        streak(0.30, 3, shade(b, 2)); streak(0.46, 1, dk); streak(0.62, 1, shade(b, 2))
    elif fx == 'shadow':
        specks(dk, 5)
        for x, y in pts:
            if ((x + 1, y) not in S or (x, y + 1) not in S) and (x + y) % 2:
                put((x, y), t + (255,))
    elif fx == 'stars':
        streak(0.36, 1)
    elif fx == 'sun':
        streak(0.34, 2, p.g)
    elif fx == 'wisps':
        for k in range(2):
            xa = x0 + w * (1 + 2 * k) // 4
            for y in range(y0 + 1, y1):
                x = xa + int(round(1.5 * math.sin(y * 0.8 + k * 2)))
                if (y + k) % 4:
                    P_(x, y, p.g)
    elif fx == 'void':
        specks(dk, 4)
    elif fx == 'facet':
        for x, y in pts:
            if not inner(x, y):
                continue
            if (x - y) % 6 == 0:
                put((x, y), shade(b, 2) + (255,))
            elif (x + y) % 9 == 0:
                put((x, y), dk + (255,))
    elif fx == 'flake':
        streak(0.30, 1, t); streak(0.36, 1, shade(t, -1))
        for x, y in pts:
            if h2(x // 3, y // 3, sd) % 7 == 0 and (x + y) % 3 == 0 and inner(x, y):
                put((x, y), shade(t, -1) + (255,))
    elif fx == 'scales':
        for x, y in pts:
            if not inner(x, y):
                continue
            r = y // 3; xo = (x + 2 * (r % 2)) % 4; yo = y % 3
            if (yo == 0 and xo == 0) or (yo == 1 and xo in (1, 3)) or (yo == 2 and xo == 2):
                put((x, y), dk + (255,))
            elif yo == 0 and xo == 2:
                put((x, y), t + (255,))
    elif fx == 'pits':
        specks(t, 9); specks(dk, 14, 4)
    elif fx == 'spots':
        for x, y in pts:
            if h2(x // 2, y // 2, sd) % 5 == 0 and inner(x, y):
                put((x, y), t + (255,))
    elif fx == 'stripes':
        for x, y in pts:
            if (y + abs(x - (x0 + x1) // 2) // 2) % 4 == 0 and abs(x - (x0 + x1) // 2) > 1:
                put((x, y), t + (255,))
    elif fx == 'warts':
        specks(t, 8); specks(dk, 9, 2)
    elif fx == 'plain':
        pass


def sparks(s, p, cols=None, n=None):
    """Glowing specks, painted last so construction lines do not hide them."""
    if not p.g:
        return
    pts = s.pts(*(cols or [p.b, p.d, p.l]))
    if len(pts) < 8:
        return
    S = set(pts)
    rnd = random.Random(p.seed * 7 + 13)
    inner = [q for q in pts if all(n_ in S for n_ in ((q[0] - 1, q[1]), (q[0] + 1, q[1]), (q[0], q[1] - 1), (q[0], q[1] + 1)))]
    if not inner:
        return
    n = n or {'stars': 6, 'void': 6, 'sparkle': 1, 'facet': 3, 'leaf': 5, 'sheen': 4, 'sun': 2,
              'wisps': 2, 'veins': 0, 'ember': 2}.get(p.fx, 3)
    for _ in range(n):
        x, y = rnd.choice(inner)
        s.px([(x, y)], p.g)
        if p.fx in ('sparkle', 'facet') or (p.fx == 'stars' and rnd.random() < 0.34):
            for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if q in S:
                    s.px([q], p.g)


def mail(s, p, cols=None):
    s.over(cols or [p.b], lambda x, y: p.d if (x + y) % 2 == 0 else None)


def big_scales(s, p, cols=None):
    def f(x, y):
        r = y // 4; xo = (x + 2 * (r % 2)) % 4; yo = y % 4
        if (yo < 3 and xo == 0) or (yo == 3 and xo in (1, 3)):
            return p.d
        if yo == 1 and xo == 2:
            return p.l
    s.over(cols or [p.b], f)


def quilt(s, p, cols=None):
    s.over(cols or [p.b], lambda x, y: p.d if (x + y) % 5 == 0 or (x - y) % 5 == 0 else None)


def buckle(s, p, x, y):
    s.rect(x, y, x + 1, y + 1, p.clasp)


# ------------------------------------------------------------ body armor
def t_padded(s, p):
    s.sym([(12, 5), (5, 9), (4, 17), (8, 17), (9, 13), (9, 28)], p.b)
    surface(s, p); quilt(s, p)
    s.rect(13, 3, 18, 5, p.t)
    s.mrect(4, 16, 8, 17, p.t)
    s.rect(9, 19, 22, 20, p.strap); buckle(s, p, 15, 19)
    s.rect(9, 27, 22, 28, p.d)


def t_padded_shirt(s, p):
    s.sym([(15, 7), (13, 5), (10, 6), (5, 11), (8, 14), (10, 12), (10, 26)], p.b)
    surface(s, p)
    s.over(p.b, lambda x, y: p.d if x % 3 == 0 and 9 < x < 22 and y > 8 else None)
    s.mline([(5, 11), (8, 14)], p.t)
    s.rect(15, 8, 16, 13, p.dd); s.px([(14, 9), (17, 9), (14, 11), (17, 11)], p.tl)
    s.rect(10, 25, 21, 26, p.t)


def _vest(s, c, top=4):
    s.sym([(12, top), (9, top), (7, top + 3), (8, 12), (8, 26), (15, 27)], c)
    s.cell(12, top - 3, 19, top + 2)


def t_leather(s, p):
    _vest(s, p.b)
    s.mpoly([(9, 4), (6, 5), (4, 9), (8, 10)], p.d)
    surface(s, p)
    s.rect(15, 7, 16, 27, p.dd)
    for y in (9, 12, 15):
        s.px([(14, y), (17, y), (15, y + 1), (16, y + 1)], p.tl)
    s.rect(8, 19, 23, 20, p.strap); buckle(s, p, 15, 19)
    s.cpx([(11, 27), (11, 26), (20, 27), (20, 26)])


def t_studded_leather(s, p):
    _vest(s, p.b, 5)
    surface(s, p)
    stud = p.t if p.fx == 'studs' else p.riv
    s.over(p.b, lambda x, y: stud if y % 4 == 1 and (x + 2 * ((y // 4) % 2)) % 4 == 1 and s.get(x, y + 1) == p.b
           and s.get(x + 1, y) == p.b and s.get(x - 1, y) == p.b else None)
    s.mpoly([(3, 7), (10, 4), (12, 9), (5, 12)], p.d); s.mpx([(7, 7), (9, 9), (6, 10)], stud)
    s.rect(8, 25, 23, 26, p.d)
    s.rect(8, 20, 23, 20, p.strap); buckle(s, p, 15, 20)


def t_hide(s, p):
    s.sym([(11, 5), (5, 7), (3, 12), (7, 14), (8, 11), (8, 22), (5, 27), (9, 26), (11, 29), (13, 25), (15, 28)], p.b)
    s.cell(12, 2, 19, 7)
    surface(s, p)
    fur = p.t if p.fx == 'fur' else shade(p.b, 2)
    for x, y in s.pts(p.b):
        if h2(x, y, 5) % 9 == 0 and s.get(x, y + 1) == p.b:
            s.px([(x, y), (x, y + 1)], p.d)
    s.sym([(11, 4), (4, 7), (3, 10), (9, 9), (13, 8), (15, 10)], fur)
    s.cell(13, 2, 18, 6)
    s.mpx([(5, 10), (8, 10), (11, 10), (14, 11)], fur)
    s.line([(8, 18), (23, 19)], p.strap); s.px([(13, 20), (13, 21), (14, 22)], p.strap)
    s.px([(12, 14), (19, 16), (17, 22), (11, 23)], p.dd)



def _tee(s, c, long=26):
    s.sym([(15, 6), (13, 4), (10, 5), (4, 10), (7, 14), (10, 12), (10, long)], c)


def t_ringmail(s, p):
    back = (92, 60, 40) if p.cls in ('metal', 'crystal', 'scale', 'bone') else p.dd
    _tee(s, back, 27)
    hi = shade(p.b, 1)
    for j, cy in enumerate(range(10, 26, 5)):
        for cx in range(3 + (3 if j % 2 else 0), 29, 5):
            ring = [(cx + 1, cy), (cx + 2, cy), (cx, cy + 1), (cx + 3, cy + 1), (cx, cy + 2), (cx + 3, cy + 2), (cx + 1, cy + 3), (cx + 2, cy + 3)]
            if all(s.get(x, y) in (back, p.b, hi) for x, y in ring):
                s.px(ring, p.b); s.px(ring[:3], hi)
    s.sym([(15, 6), (13, 4), (10, 5), (4, 10), (6, 12), (11, 8), (15, 9)], p.b)      # solid yoke
    s.rect(10, 25, 21, 27, p.b)
    surface(s, p)



def t_chain_shirt(s, p):
    _tee(s, p.b, 25)
    surface(s, p); mail(s, p, [p.b, p.l])
    s.rect(10, 24, 21, 25, p.t if p.cls == 'metal' else p.d)
    s.mline([(4, 10), (7, 14)], p.l)
    s.line([(13, 4), (15, 6), (16, 6), (18, 4)], p.l)


def t_chainmail(s, p):
    s.sym([(12, 3), (10, 5), (4, 10), (3, 18), (8, 18), (9, 13), (9, 21), (6, 28), (9, 29), (11, 27), (13, 29), (15, 27)], p.b)
    surface(s, p); mail(s, p, [p.b, p.l])
    s.rect(12, 2, 19, 5, p.l); s.cell(13, 0, 18, 4)
    s.rect(9, 19, 22, 20, p.strap); buckle(s, p, 15, 19)
    s.mrect(3, 17, 8, 18, p.l)




def t_scale(s, p):
    s.sym([(12, 4), (9, 5), (4, 8), (5, 13), (9, 12), (8, 25), (10, 28), (12, 25), (14, 28), (15, 25)], p.b)
    s.cell(12, 1, 19, 6)
    big_scales(s, p)
    s.sym([(12, 5), (11, 6), (15, 9)], p.t if p.cls != 'cloth' else p.d)
    s.cell(13, 2, 18, 6)


def t_banded(s, p):
    s.sym([(11, 6), (9, 8), (8, 24), (9, 27), (15, 27)], p.b)
    s.cell(12, 3, 19, 8)
    surface(s, p)
    s.over([p.b, p.l], lambda x, y: p.d if y % 3 == 0 and y > 9 else None)
    s.mell(3, 4, 12, 12, p.b)
    s.mline([(4, 8), (11, 7)], p.d); s.mline([(4, 10), (10, 10)], p.d)
    s.rect(15, 9, 16, 27, p.dd)
    for y in (11, 14, 17, 20, 23, 26):
        s.px([(14, y), (17, y)], p.clasp if p.fx != 'plain' else p.riv)


def t_splint(s, p):
    s.sym([(12, 5), (8, 6), (8, 26), (10, 28), (15, 28)], p.back)
    s.cell(12, 2, 19, 7)
    for x in (9, 12, 15, 18, 21):
        top = 8 if x in (15,) else 7
        s.rect(x, top, x + 1, 27, p.b)
        s.px([(x, top + 1), (x, 26)], p.riv)
    surface(s, p)
    s.mrect(3, 6, 7, 13, p.b)
    s.mline([(3, 8), (7, 8)], p.d); s.mline([(3, 11), (7, 11)], p.d)
    s.rect(8, 19, 23, 20, p.strap); buckle(s, p, 15, 19)


def t_breastplate(s, p):
    s.sym([(12, 5), (9, 5), (8, 9), (9, 13), (8, 19), (10, 25), (15, 28)], p.b)
    s.cell(12, 1, 19, 8)
    surface(s, p)
    s.mline([(9, 14), (12, 16), (14, 15)], p.d)
    s.rect(15, 9, 16, 25, p.l)
    s.sym([(10, 24), (10, 25), (15, 28)], p.d)
    s.mrect(9, 2, 10, 4, p.strap); s.mpx([(9, 4), (10, 4)], p.clasp)
    s.mpx([(8, 18), (8, 19)], p.strap)


def t_plate(s, p):
    s.sym([(12, 6), (10, 7), (10, 20), (15, 21)], p.b)
    s.mpoly([(9, 21), (15, 21), (15, 28), (10, 29), (7, 26)], p.b)
    surface(s, p)
    s.rect(12, 4, 19, 6, p.d)
    s.mell(2, 5, 11, 13, p.b)
    s.mline([(3, 10), (6, 12), (10, 11)], p.d); s.mpx([(6, 8)], p.riv)
    s.rect(15, 8, 16, 19, p.l)
    s.rect(9, 20, 22, 21, p.d); buckle(s, p, 15, 20)
    s.mline([(8, 24), (14, 24)], p.d); s.mline([(8, 27), (14, 27)], p.d)
    s.crect(15, 23, 16, 30)


def t_full_plate(s, p):
    s.mrect(5, 10, 8, 19, p.b)
    s.rect(11, 8, 20, 17, p.b)
    s.mrect(10, 22, 14, 28, p.b)
    surface(s, p)
    s.ell(12, 1, 19, 8, p.b); s.rect(13, 4, 18, 4, p.dark); s.rect(15, 5, 16, 7, p.d)
    s.rect(13, 8, 18, 8, p.d)
    s.mell(5, 7, 12, 12, p.l)
    s.rect(15, 10, 16, 16, p.l)
    s.mline([(5, 15), (8, 15)], p.d); s.mrect(5, 20, 8, 22, p.d)
    s.sym([(10, 18), (9, 21)], p.d); s.rect(15, 18, 16, 19, p.clasp)
    s.mrect(10, 24, 14, 25, p.l)
    s.mrect(8, 28, 14, 29, p.d)


def t_cloak(s, p):
    s.sym([(10, 6), (6, 12), (3, 26), (6, 28), (9, 26), (12, 29), (15, 27)], p.b)
    surface(s, p)
    for a, b_ in (((11, 9), (8, 26)), ((14, 9), (13, 27)), ((18, 9), (19, 27)), ((21, 10), (24, 26))):
        s.line([a, b_], p.d)
    s.line([(9, 12), (6, 25)], p.l)
    s.sym([(11, 3), (8, 7), (12, 9), (15, 8)], p.d)
    s.ell(13, 4, 18, 9, p.clasp); s.px([(15, 6)], shade(p.clasp, 2))


# ------------------------------------------------------------ legs
def t_cloth_leggings(s, p):
    s.poly([(8, 4), (23, 4), (24, 14), (22, 28), (17, 28), (16, 12), (15, 12), (14, 28), (9, 28), (7, 14)], p.b)
    surface(s, p)
    s.line([(10, 9), (11, 26)], p.d); s.line([(21, 9), (20, 26)], p.d); s.line([(13, 8), (12, 16)], p.d)
    s.rect(8, 4, 23, 6, p.t)
    s.px([(14, 7), (13, 8), (13, 9), (17, 7), (18, 8)], p.tl)
    s.rect(9, 27, 14, 28, p.d); s.rect(17, 27, 22, 28, p.d)


def t_leather_leggings(s, p):
    s.poly([(8, 3), (23, 3), (23, 28), (17, 28), (16, 11), (15, 11), (14, 28), (8, 28)], p.b)
    surface(s, p)
    s.mrect(9, 15, 13, 19, p.d); s.mpx([(9, 15), (13, 15), (9, 19), (13, 19)], p.l)
    s.rect(8, 3, 23, 5, p.strap); buckle(s, p, 15, 3); s.px([(15, 5), (16, 5)], p.clasp)
    s.mpx([(8, 8), (8, 10), (8, 12), (8, 22), (8, 24)], p.l)
    s.mrect(8, 27, 14, 28, p.dd)


def t_chain_chausses(s, p):
    s.mpoly([(7, 6), (13, 6), (13, 24), (14, 27), (14, 29), (4, 29), (4, 27), (8, 24)], p.b)
    surface(s, p); mail(s, p, [p.b, p.l])
    s.mrect(7, 6, 13, 7, p.strap); s.mline([(10, 2), (10, 5)], p.strap); s.mpx([(10, 6)], p.clasp)
    s.mrect(4, 29, 14, 29, p.dd)


def t_plate_greaves(s, p):
    for ox in (0, 12):
        s.poly([(6 + ox, 7), (13 + ox, 7), (13 + ox, 24), (15 + ox, 28), (4 + ox, 28), (6 + ox, 24)], p.b)
    surface(s, p)
    for ox in (0, 12):
        s.ell(5 + ox, 2, 14 + ox, 10, p.l)
        s.rect(9 + ox, 4, 10 + ox, 26, shade(p.b, 2))
        s.line([(6 + ox, 15), (13 + ox, 15)], p.strap); s.line([(6 + ox, 21), (13 + ox, 21)], p.strap)
        s.px([(7 + ox, 15), (12 + ox, 21)], p.clasp)
        s.line([(4 + ox, 28), (15 + ox, 28)], p.d)


# ------------------------------------------------------------ feet
def _boot(s, p, ox, oy, kind, c):
    b, d, l = c
    if kind == 'leather':
        s.poly([(ox + 1, oy + 7), (ox + 7, oy + 7), (ox + 7, oy + 19), (ox + 12, oy + 21), (ox + 13, oy + 25), (ox + 1, oy + 25)], b)
    elif kind == 'iron':
        s.poly([(ox + 1, oy + 8), (ox + 8, oy + 8), (ox + 8, oy + 17), (ox + 12, oy + 18), (ox + 14, oy + 24), (ox + 1, oy + 24)], b)
    else:
        s.poly([(ox, oy + 4), (ox + 9, oy + 4), (ox + 7, oy + 8), (ox + 7, oy + 19), (ox + 12, oy + 21), (ox + 15, oy + 25), (ox + 1, oy + 25)], b)


def _boot_trim(s, p, ox, oy, kind, c):
    b, d, l = c
    if kind == 'leather':
        s.rect(ox, oy + 6, ox + 8, oy + 9, l if p.cls != 'cloth' else p.t)
        s.line([(ox + 1, oy + 18), (ox + 7, oy + 18)], p.strap); s.px([(ox + 5, oy + 18)], p.clasp)
        s.rect(ox + 1, oy + 26, ox + 13, oy + 26, p.dark)
    elif kind == 'iron':
        s.rect(ox, oy + 8, ox + 9, oy + 10, d); s.px([(ox + 2, oy + 9), (ox + 6, oy + 9)], p.riv)
        s.rect(ox + 1, oy + 15, ox + 8, oy + 16, d); s.px([(ox + 2, oy + 15), (ox + 6, oy + 15)], p.riv)
        s.poly([(ox + 9, oy + 19), (ox + 12, oy + 19), (ox + 14, oy + 24), (ox + 9, oy + 24)], l)
        s.rect(ox, oy + 25, ox + 14, oy + 26, p.dark)
    else:
        s.line([(ox, oy + 4), (ox + 9, oy + 4)], l); s.line([(ox + 2, oy + 8), (ox + 7, oy + 8)], d)
        s.line([(ox + 4, oy + 9), (ox + 4, oy + 18)], shade(b, 2))
        for k in (7, 9, 11, 13):
            s.line([(ox + k, oy + 21 + (k - 7) // 3), (ox + k - 1, oy + 25)], d)
        s.line([(ox + 1, oy + 19), (ox + 7, oy + 19)], d)
        s.rect(ox + 1, oy + 26, ox + 15, oy + 26, p.dark)


def _boots(s, p, kind):
    back = (p.d, p.dd, p.b)
    front = (p.b, p.d, p.l)
    bx = 14 if kind != 'plate' else 14
    _boot(s, p, bx, 0, kind, back)
    _boot_trim(s, p, bx, 0, kind, back)
    _boot(s, p, 2, 2, kind, front)
    surface(s, p)
    _boot_trim(s, p, 2, 2, kind, front)


def t_leather_boots(s, p): _boots(s, p, 'leather')
def t_iron_boots(s, p): _boots(s, p, 'iron')
def t_plate_boots(s, p): _boots(s, p, 'plate')


# ------------------------------------------------------------ arms
def t_leather_bracers(s, p):
    for ox in (0, 14):
        s.poly([(3 + ox, 5), (14 + ox, 5), (12 + ox, 26), (5 + ox, 26)], p.b)
    surface(s, p)
    for ox in (0, 14):
        s.rect(3 + ox, 5, 14 + ox, 7, p.d); s.rect(5 + ox, 24, 12 + ox, 26, p.d)
        for y in range(9, 23, 3):
            s.px([(7 + ox, y), (8 + ox, y + 1), (9 + ox, y + 1), (10 + ox, y)], p.tl if p.cls == 'leather' else p.riv)
            s.px([(8 + ox, y + 2), (9 + ox, y + 2)], p.dd)



def t_iron_vambraces(s, p):
    s.mpoly([(2, 5), (11, 3), (14, 26), (9, 27)], p.b)
    surface(s, p)
    s.mline([(3, 8), (11, 6)], p.d, 2); s.mline([(8, 22), (13, 21)], p.d, 2)
    s.mpx([(5, 8), (9, 7), (10, 22), (12, 21)], p.riv)
    s.mline([(6, 15), (12, 14)], p.strap)



def t_steel_vambraces(s, p):
    s.mpoly([(4, 8), (11, 7), (14, 25), (9, 26)], p.b)
    surface(s, p)
    s.mpoly([(1, 3), (12, 1), (12, 8), (3, 10)], p.l)
    s.mline([(2, 8), (12, 6)], p.d); s.mpx([(4, 5), (10, 4)], p.riv)
    s.mline([(8, 11), (11, 24)], shade(p.b, 2))
    s.mpoly([(8, 25), (14, 24), (15, 27), (9, 28)], p.d)
    s.mline([(6, 17), (12, 16)], p.strap)



def t_plate_vambraces(s, p):
    s.mpoly([(4, 10), (11, 9), (14, 23), (9, 24)], p.b)
    surface(s, p)
    s.mline([(6, 15), (12, 14)], p.d); s.mline([(8, 19), (13, 18)], p.d)
    s.mell(1, 2, 12, 13, p.l); s.mell(4, 5, 9, 10, p.b); s.mpx([(6, 7), (7, 7)], p.riv)
    s.mpoly([(8, 24), (14, 23), (15, 28), (8, 29)], p.d)
    s.mline([(8, 29), (15, 28)], p.l)



# ------------------------------------------------------------ hands
def t_leather_gloves(s, p):
    for x, top in ((7, 7), (11, 4), (15, 3), (19, 6)):
        s.rect(x, top + 1, x + 2, 14, p.b); s.rect(x, top, x + 2, top, p.b)
    s.rect(7, 13, 21, 22, p.b)
    s.poly([(21, 15), (25, 11), (27, 13), (22, 21)], p.b)
    surface(s, p)
    s.poly([(8, 22), (20, 22), (22, 28), (6, 28)], p.d)
    s.line([(6, 28), (22, 28)], p.t if p.cls in ('cloth', 'leather') else p.l)
    s.line([(8, 22), (20, 22)], p.dd)
    s.px([(10, 15), (14, 15), (18, 15)], p.d)


def t_plate_gauntlets(s, p):
    s.rect(9, 10, 22, 19, p.b)
    for x0, y0 in ((9, 5), (12, 3), (16, 3), (19, 5)):
        s.rect(x0, y0, x0 + 2, 10, p.b)
    s.poly([(22, 12), (26, 10), (27, 13), (23, 17)], p.b)
    surface(s, p)
    s.poly([(10, 20), (21, 20), (24, 28), (7, 28)], p.d)
    s.line([(9, 20), (22, 20)], p.l); s.line([(7, 28), (24, 28)], p.l)
    s.px([(11, 24), (15, 24), (19, 24)], p.riv)
    s.line([(9, 10), (22, 10)], p.l); s.line([(9, 14), (22, 14)], p.d)
    s.px([(11, 7), (14, 6), (18, 6), (21, 7)], p.d)


def t_gauntlets(s, p):
    s.ell(9, 2, 23, 15, p.b); s.rect(9, 9, 23, 17, p.b)
    s.poly([(9, 11), (5, 8), (3, 11), (6, 16), (9, 18)], p.b)
    s.poly([(10, 17), (22, 17), (21, 21), (25, 28), (6, 28), (11, 21)], p.b)
    surface(s, p)
    for y in (6, 9, 12):
        s.line([(10, y + 1), (13, y), (19, y), (22, y + 1)], p.d)
    s.rect(10, 17, 22, 18, p.d); s.px([(12, 17), (16, 17), (20, 17)], p.riv)
    s.line([(6, 28), (25, 28)], p.l); s.line([(7, 27), (24, 27)], p.d)
    s.line([(16, 20), (16, 26)], p.l)


# ------------------------------------------------------------ head
def t_leather_cap(s, p):
    s.ell(7, 5, 24, 26, p.b); s.crect(0, 17, 31, 31)
    s.mpoly([(7, 15), (11, 15), (11, 21), (9, 24), (7, 21)], p.b)
    surface(s, p)
    s.rect(7, 14, 24, 16, p.d)
    s.line([(15, 6), (15, 13)], p.d); s.line([(16, 6), (16, 13)], p.l)
    s.rect(15, 4, 16, 5, p.t if p.cls in ('cloth', 'leather') else p.riv)
    s.mline([(9, 24), (12, 27), (15, 28)], p.strap)
    s.px([(15, 28), (16, 28)], p.clasp)


def t_iron_helm(s, p):
    s.ell(6, 4, 25, 30, p.b); s.crect(0, 20, 31, 31)
    s.sym([(15, 2), (12, 5), (15, 8)], p.b)
    s.mpoly([(6, 19), (11, 19), (11, 26), (8, 26), (6, 23)], p.b)
    surface(s, p)
    s.mline([(13, 6), (10, 17)], p.d)
    s.rect(15, 4, 16, 16, p.l)
    s.rect(5, 17, 26, 19, p.d); s.px([(7, 18), (11, 18), (20, 18), (24, 18)], p.riv)
    s.rect(15, 20, 16, 25, p.d); s.rect(14, 20, 17, 21, p.d)
    s.mline([(11, 20), (11, 26)], p.d)
    s.rect(15, 1, 16, 2, p.riv)




def t_steel_helm(s, p):
    s.ell(6, 3, 25, 22, p.b); s.poly([(6, 12), (25, 12), (26, 27), (5, 27)], p.b)
    surface(s, p)
    s.rect(10, 13, 21, 15, p.dark); s.rect(14, 15, 17, 28, p.dark)
    s.crect(14, 27, 17, 28)
    s.mline([(10, 12), (10, 16), (13, 16), (13, 27)], p.l)
    s.line([(15, 3), (15, 11)], p.l); s.line([(16, 3), (16, 11)], p.d)
    s.mpx([(7, 25), (9, 25)], p.riv)


def t_plate_helm(s, p):
    plume = p.t if p.cls != 'metal' or p.fx not in ('streak', 'streak2', 'dull', 'rust') else (176, 44, 52)
    s.poly([(13, 5), (9, 1), (4, 2), (1, 8), (4, 7), (7, 6), (9, 9)], plume)
    s.ell(5, 4, 23, 23, p.b); s.poly([(7, 17), (22, 19), (22, 27), (8, 27)], p.b)
    surface(s, p)
    s.poly([(12, 11), (24, 11), (29, 16), (24, 20), (12, 20)], p.l)
    s.line([(14, 13), (25, 13)], p.dark)
    s.px([(18, 16), (20, 16), (22, 16), (19, 18), (21, 18)], p.dark)
    s.ell(9, 13, 12, 16, p.d)
    s.rect(8, 25, 22, 27, p.d); s.px([(10, 26), (15, 26), (20, 26)], p.riv)
    s.line([(9, 6), (18, 5)], shade(p.b, 2))


def t_great_helm(s, p):
    s.poly([(7, 5), (24, 5), (25, 27), (6, 27)], p.b)
    surface(s, p)
    bar = p.t if p.cls == 'metal' and sum(p.t) > sum(p.b) else p.l
    s.rect(6, 3, 25, 5, p.l)
    s.rect(15, 6, 16, 27, bar); s.rect(7, 11, 24, 14, bar)
    s.rect(9, 12, 13, 13, p.dark); s.rect(18, 12, 22, 13, p.dark)
    s.px([(19, 18), (21, 18), (20, 20), (22, 20), (19, 22), (21, 22), (10, 18), (12, 18), (11, 20), (9, 20), (10, 22), (12, 22)], p.dark)
    s.line([(6, 27), (25, 27)], p.d)


def t_helm(s, p):
    """Kettle hat: dome over a wide brim."""
    s.ell(2, 15, 29, 24, p.d)
    s.ell(8, 4, 23, 22, p.b); s.crect(0, 20, 31, 20) if False else None
    surface(s, p)
    s.ell(2, 16, 29, 24, p.d); s.ell(8, 4, 23, 22, p.b) if False else None
    s.line([(4, 19), (27, 19)], p.l)
    s.rect(15, 5, 16, 15, p.l)
    s.mpx([(6, 21), (10, 22)], p.riv)
    s.mline([(8, 24), (11, 27), (15, 28)], p.strap)


# ------------------------------------------------------------ shields
def _rim(p):
    if p.cls == 'wood':
        return (118, 122, 136), (190, 196, 208)
    if p.cls == 'leather':
        return p.dd, (190, 196, 208)
    if p.cls == 'cloth':
        return p.td, p.t
    if p.cls == 'bone':
        return p.t, p.l
    return p.d, p.l


def _rivet(p):
    return p.t if p.fx in ('rivet',) or p.t == MATS['dwarven_plate'][1] else p.riv


def t_buckler(s, p):
    rim, boss = _rim(p)
    s.ell(5, 5, 26, 26, rim); s.ell(7, 7, 24, 24, p.b)
    surface(s, p)
    s.ell(11, 11, 20, 20, p.dd); s.ell(12, 12, 19, 19, boss); s.ell(14, 14, 17, 17, shade(boss, 1))
    s.px([(15, 6), (16, 6), (15, 25), (16, 25), (6, 15), (6, 16), (25, 15), (25, 16)], shade(rim, 2))


def t_light_wooden(s, p):
    rim, boss = _rim(p)
    s.ell(2, 2, 29, 29, rim); s.ell(4, 4, 27, 27, p.b)
    surface(s, p)
    for x in (9, 15, 21):
        s.over([p.b, p.d, p.l], lambda x_, y: p.dd if x_ == x else None)
    s.ell(12, 12, 19, 19, boss); s.px([(14, 14)], shade(boss, 2))
    s.px([(15, 6), (15, 25), (6, 15), (25, 15), (9, 9), (22, 9), (9, 22), (22, 22)], shade(rim, 2))


def t_heavy_wooden(s, p):
    rim, boss = _rim(p)
    s.sym([(4, 3), (4, 18), (8, 25), (15, 29)], rim)
    s.sym([(6, 5), (6, 17), (9, 23), (15, 27)], p.b)
    surface(s, p)
    for x in (10, 15, 21):
        s.over([p.b, p.d, p.l], lambda x_, y: p.dd if x_ == x else None)
    for y in (9, 19):
        s.rect(5, y, 26, y + 1, rim)
        s.px([(8, y), (13, y), (18, y), (23, y)], shade(rim, 2))
    s.ell(13, 12, 18, 17, boss)


def t_kite_shield(s, p):
    rim, boss = _rim(p)
    s.ell(5, 1, 26, 17, rim); s.poly([(5, 9), (26, 9), (16, 30), (15, 30)], rim)
    s.ell(7, 3, 24, 15, p.b); s.poly([(7, 9), (24, 9), (16, 27), (15, 27)], p.b)
    surface(s, p)
    stripe = p.t if p.cls in ('cloth', 'leather', 'wood') else p.l
    s.over([p.b, p.d, p.l, p.t], lambda x, y: stripe if x in (15, 16) else None)
    s.over([p.b, p.d, p.l, p.t], lambda x, y: stripe if y in (9, 10) else None)
    s.ell(13, 7, 18, 12, boss)


def t_tower_shield(s, p):
    rim, boss = _rim(p)
    s.ell(7, 1, 24, 8, rim); s.rect(7, 4, 24, 29, rim)
    s.ell(9, 3, 22, 9, p.b); s.rect(9, 6, 22, 27, p.b)
    surface(s, p)
    s.rect(8, 10, 23, 11, rim); s.rect(8, 22, 23, 23, rim)
    s.px([(10, 10), (15, 10), (21, 10), (10, 22), (15, 22), (21, 22)], shade(rim, 2))
    s.poly([(15, 13), (16, 13), (19, 16), (16, 20), (15, 20), (12, 16)], boss)


def t_shield(s, p):
    """Heater."""
    rim, boss = _rim(p)
    s.sym([(5, 3), (5, 14), (9, 23), (15, 29)], rim)
    s.sym([(7, 5), (7, 14), (10, 21), (15, 26)], p.b)
    surface(s, p)
    c = p.t if p.cls != 'metal' else p.l
    s.over([p.b, p.d, p.l], lambda x, y: c if (y - 8 + abs(x - 15.5)) // 1 in (6, 7, 8) else None)
    s.mpx([(6, 4), (6, 13)], shade(rim, 2))


def t_armor(s, p):
    """Old generic armor: harness with a tabard / reinforced jerkin / spiked scale."""
    if p.cls in SOFT:
        t_leather(s, p)
        s.mpoly([(3, 8), (9, 4), (11, 9), (5, 12)], p.d); s.mpx([(6, 8), (8, 7)], p.riv)
        for x in (9, 12, 18, 21):
            s.rect(x, 27, x + 1, 29, p.d)
    elif p.cls == 'scale':
        t_scale(s, p)
        s.mpoly([(4, 9), (2, 3), (7, 6)], p.t); s.rect(8, 18, 23, 19, p.strap); buckle(s, p, 15, 18)
    else:
        t_plate(s, p)
        tab = p.t if abs(sum(p.t) - sum(p.b)) > 120 else (160, 40, 50)
        s.rect(12, 8, 19, 20, tab); s.poly([(12, 21), (19, 21), (19, 28), (16, 30), (15, 30), (12, 28)], tab)
        s.rect(15, 10, 16, 16, p.clasp); s.rect(13, 12, 18, 13, p.clasp)
        s.rect(12, 20, 19, 21, p.strap)


def t_shirt(s, p):
    s.sym([(15, 7), (13, 5), (10, 6), (3, 13), (3, 22), (7, 22), (9, 14), (10, 27)], p.b)
    surface(s, p)
    if p.cls not in SOFT:
        mail(s, p, [p.b, p.l])
    s.mrect(3, 21, 7, 22, p.t if p.cls in SOFT else p.l)
    s.rect(15, 8, 16, 14, p.dd); s.px([(14, 9), (17, 9), (14, 11), (17, 11), (14, 13), (17, 13)], p.tl if p.cls in SOFT else p.l)
    s.rect(10, 26, 21, 27, p.d)


def t_bracers(s, p):
    for ox in (0, 14):
        s.poly([(4 + ox, 4), (13 + ox, 4), (12 + ox, 27), (6 + ox, 27)], p.b)
    surface(s, p)
    if p.cls == 'scale':
        big_scales(s, p)
    for ox in (0, 14):
        s.rect(4 + ox, 4, 13 + ox, 5, p.l); s.rect(6 + ox, 26, 12 + ox, 27, p.d)
        for y in (10, 17):
            s.line([(4 + ox, y), (13 + ox, y)], p.strap, 2); s.px([(8 + ox, y), (9 + ox, y)], p.clasp)


def t_greaves(s, p):
    for ox in (0, 12):
        s.poly([(6 + ox, 3), (13 + ox, 3), (14 + ox, 9), (13 + ox, 24), (15 + ox, 28), (4 + ox, 28), (6 + ox, 24), (5 + ox, 9)], p.b)
    surface(s, p)
    for ox in (0, 12):
        for y in (9, 15, 21):
            s.line([(6 + ox, y), (13 + ox, y)], p.d)
        s.rect(9 + ox, 4, 10 + ox, 26, p.l)
        s.line([(6 + ox, 3), (13 + ox, 3)], shade(p.b, 2)); s.line([(4 + ox, 28), (15 + ox, 28)], p.d)
        s.px([(7 + ox, 12), (12 + ox, 12), (7 + ox, 18), (12 + ox, 18)], p.riv)


def t_leggings(s, p):
    if p.cls not in SOFT:
        return t_chain_chausses(s, p)
    s.poly([(8, 3), (23, 3), (24, 28), (17, 28), (16, 11), (15, 11), (14, 28), (7, 28)], p.b)
    surface(s, p)
    s.rect(8, 3, 23, 4, p.strap)
    for y in range(7, 26, 3):
        s.mpx([(9, y), (10, y + 1)], p.tl); s.mpx([(10, y), (9, y + 1)], p.dd)
    s.mrect(7, 25, 14, 28, p.d); s.mpx([(8, 26), (13, 26)], p.riv)
    s.px([(15, 6), (16, 6), (15, 8), (16, 8)], p.dd)


def t_boots(s, p):
    if p.cls not in SOFT:
        t_iron_boots(s, p)
        for ox, oy in ((14, 0), (2, 2)):
            s.line([(ox + 2, oy + 11), (ox + 7, oy + 14)], p.riv); s.line([(ox + 7, oy + 11), (ox + 2, oy + 14)], p.riv)
        return
    back = (p.d, p.dd, p.b); front = (p.b, p.d, p.l)
    _boot(s, p, 14, 0, 'leather', back); _boot(s, p, 2, 2, 'leather', front)
    surface(s, p)
    for ox, oy, c in ((14, 0, back), (2, 2, front)):
        for y in range(9, 19, 3):
            s.px([(ox + 5, oy + y), (ox + 6, oy + y + 1)], p.tl); s.px([(ox + 6, oy + y), (ox + 5, oy + y + 1)], p.dd)
        s.poly([(ox + 9, oy + 21), (ox + 12, oy + 21), (ox + 13, oy + 25), (ox + 9, oy + 25)], c[1])
        s.rect(ox + 1, oy + 26, ox + 13, oy + 27, p.dark)


def t_cap(s, p):
    s.ell(6, 5, 23, 28, p.b); s.crect(0, 19, 31, 31)
    surface(s, p)
    s.poly([(6, 18), (24, 17), (29, 20), (27, 22), (6, 21)], p.d)
    s.line([(7, 21), (27, 22)], p.dd)
    s.line([(10, 8), (9, 17)], p.d); s.line([(19, 8), (20, 17)], p.d)
    s.rect(14, 4, 15, 5, p.t if p.cls in SOFT else p.riv)


def t_gloves(s, p):
    for ox, m in ((1, 1), (16, -1)):
        s.rect(ox + 3, 9, ox + 11, 21, p.b)
        for i, top in enumerate((7, 5, 4, 6)):
            s.rect(ox + 3 + i * 2 + (1 if i > 1 else 0), top, ox + 4 + i * 2 + (1 if i > 1 else 0), 10, p.b)
        if m == 1:
            s.poly([(ox + 11, 14), (ox + 14, 11), (ox + 15, 13), (ox + 12, 19)], p.b)
        else:
            s.poly([(ox + 3, 14), (ox, 11), (ox - 1, 13), (ox + 2, 19)], p.b)
    surface(s, p)
    for ox in (1, 16):
        s.px([(ox + 5, 10), (ox + 5, 11), (ox + 7, 10), (ox + 7, 11), (ox + 9, 10), (ox + 9, 11)], p.d)
        s.poly([(ox + 3, 21), (ox + 11, 21), (ox + 13, 27), (ox + 1, 27)], p.d)
        s.line([(ox + 1, 27), (ox + 13, 27)], p.t if p.cls in SOFT else p.l)


def t_hide_strip(s, p):
    s.poly([(2, 12), (6, 7), (12, 9), (20, 14), (27, 17), (29, 22), (26, 26), (22, 22), (14, 19), (8, 16), (4, 17)], p.b)
    surface(s, p)
    fur = shade(p.b, 2)
    for x, y in s.pts(p.b, p.l, p.d):
        if s.get(x, y - 1) is None and x % 2:
            s.px([(x, y)], fur)
    s.line([(7, 10), (25, 21)], p.d)
    s.line([(13, 9), (11, 18)], p.strap, 2); s.px([(10, 19), (9, 21), (12, 20)], p.strap)


TEMPLATES = {
    'padded': t_padded, 'padded_shirt': t_padded_shirt, 'leather': t_leather,
    'studded_leather': t_studded_leather, 'hide': t_hide, 'ringmail': t_ringmail,
    'chain_shirt': t_chain_shirt, 'chainmail': t_chainmail, 'scale': t_scale, 'banded': t_banded,
    'splint': t_splint, 'breastplate': t_breastplate, 'plate': t_plate, 'full_plate': t_full_plate,
    'cloak': t_cloak, 'cloth_leggings': t_cloth_leggings, 'leather_leggings': t_leather_leggings,
    'chain_chausses': t_chain_chausses, 'plate_greaves': t_plate_greaves,
    'leather_boots': t_leather_boots, 'iron_boots': t_iron_boots, 'plate_boots': t_plate_boots,
    'leather_bracers': t_leather_bracers, 'iron_vambraces': t_iron_vambraces,
    'steel_vambraces': t_steel_vambraces, 'plate_vambraces': t_plate_vambraces,
    'leather_gloves': t_leather_gloves, 'plate_gauntlets': t_plate_gauntlets, 'gauntlets': t_gauntlets,
    'leather_cap': t_leather_cap, 'iron_helm': t_iron_helm, 'steel_helm': t_steel_helm,
    'plate_helm': t_plate_helm, 'great_helm': t_great_helm, 'helm': t_helm,
    'buckler': t_buckler, 'light_wooden': t_light_wooden, 'heavy_wooden': t_heavy_wooden,
    'kite_shield': t_kite_shield, 'tower_shield': t_tower_shield, 'shield': t_shield,
    'armor': t_armor, 'shirt': t_shirt, 'bracers': t_bracers, 'greaves': t_greaves, 'leggings': t_leggings,
    'boots': t_boots, 'cap': t_cap, 'gloves': t_gloves, 'hide_strip': t_hide_strip,
}

SOFT = ('cloth', 'leather')


def legacy(template, cls):
    """Old template names have their own rigs now; kept for callers."""
    return template


def render(template, p, s=None, extra=None):
    s = s or A()
    TEMPLATES[template](s, p)
    if extra:
        extra(s, p)
    sparks(s, p)
    s.clip()
    return s.finish()
