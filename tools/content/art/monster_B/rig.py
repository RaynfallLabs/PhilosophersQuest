"""Shared helpers for the monster_B slice (unnatural creatures)."""
import os
import sys
import zlib
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Sprite, shade, S, BONE, IVORY, STEEL, IRON, WOOD, LEATHER, DARK, GOLD, STRING  # noqa

WHITE = (240, 240, 235)
BLACK = (22, 18, 26)
RED = (190, 40, 40)
RUST = (150, 100, 76)
CLOTH = (110, 96, 84)


def mul(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def M(x):
    return 31 - x


class Sp(Sprite):
    """Sprite with short names, mirrored painting and optional translucency."""

    def __init__(self, rec=None):
        super().__init__()
        self.fade = None       # (alpha_top, alpha_bottom) for ghosts
        self.rng = random.Random(zlib.crc32((rec or {}).get('id', 'x').encode()))

    def r(self, x0, y0, x1, y1, c): self.rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), c)
    def e(self, x0, y0, x1, y1, c): self.ell(x0, y0, x1, y1, c)
    def p(self, pts, c): self.poly(pts, c)
    def l(self, pts, c, w=1): self.line(pts, c, w)

    def mr(self, x0, y0, x1, y1, c):
        self.r(x0, y0, x1, y1, c); self.r(M(x1), y0, M(x0), y1, c)

    def me(self, x0, y0, x1, y1, c):
        self.e(x0, y0, x1, y1, c); self.e(M(x1), y0, M(x0), y1, c)

    def mp(self, pts, c):
        self.p(pts, c); self.p([(M(x), y) for x, y in pts], c)

    def ml(self, pts, c, w=1):
        self.l(pts, c, w); self.l([(M(x), y) for x, y in pts], c, w)

    def mpx(self, pts, c):
        self.px(pts, c); self.px([(M(x), y) for x, y in pts], c)

    def dots(self, n, box, c, avoid_empty=True):
        """n seeded pixels of colour c inside box, only on painted pixels."""
        x0, y0, x1, y1 = box
        tries = 0
        while n > 0 and tries < 400:
            tries += 1
            x, y = self.rng.randint(x0, x1), self.rng.randint(y0, y1)
            if avoid_empty and self.img.getpixel((x, y))[3] == 0:
                continue
            self.px([(x, y)], c); n -= 1

    def air(self, n, box, c):
        """n seeded pixels on EMPTY space (embers, motes, stars)."""
        x0, y0, x1, y1 = box
        tries = 0
        while n > 0 and tries < 400:
            tries += 1
            x, y = self.rng.randint(x0, x1), self.rng.randint(y0, y1)
            if self.img.getpixel((x, y))[3] != 0:
                continue
            self.px([(x, y)], c); n -= 1

    def fit(self):
        """Nudge the drawing so painted pixels sit inside 1..30 where there is room."""
        bb = self.img.getbbox()
        if not bb:
            return
        x0, y0, x1, y1 = bb[0], bb[1], bb[2] - 1, bb[3] - 1
        dx = 1 - x0 if x0 < 1 and x1 < 30 else (30 - x1 if x1 > 30 and x0 > 1 else 0)
        dy = 1 - y0 if y0 < 1 and y1 < 30 else (30 - y1 if y1 > 30 and y0 > 1 else 0)
        if dx or dy:
            from PIL import Image, ImageDraw
            n = Image.new('RGBA', (S, S), (0, 0, 0, 0)); n.paste(self.img, (dx, dy))
            self.img = n; self.d = ImageDraw.Draw(n)

    def done(self):
        self.fit()
        # keep the outermost ring free so the outline is never cut by the tile edge
        for k in range(S):
            for xy in ((k, 0), (k, S - 1), (0, k), (S - 1, k)):
                self.img.putpixel(xy, (0, 0, 0, 0))
        img = self.finish()
        if self.fade:
            top, bot = self.fade
            px = img.load()
            for y in range(S):
                t = max(0.0, min(1.0, (y - 4) / 25.0))
                k = (top + (bot - top) * t) / 255.0
                for x in range(S):
                    r, g, b, a = px[x, y]
                    if a == 0 or ((r, g, b) in self.glow and a == 255):
                        continue
                    px[x, y] = (r, g, b, int(a * k))
        return img


# ------------------------------------------------------------ body parts
def man(s, skin, top, legs=None, boots=DARK, *, arms='down', sleeve=None, hy=3,
        belt=None, w=0, head=True, feet=True):
    """Plain standing humanoid. Returns hand anchors."""
    legs = legs or mul(top, 0.8)
    sl = sleeve or mul(top, 0.86)
    if feet:
        s.mr(12 - w, 22, 14, 27, legs)
        s.mr(11 - w, 28, 14, 29, boots)
    s.r(11 - w, 12, 20 + w, 22, top)
    if belt:
        s.r(11 - w, 20, 20 + w, 20, belt)
    if arms == 'down':
        s.mr(8 - w, 12, 10 - w, 19, sl); s.mr(8 - w, 20, 10 - w, 21, skin)
    elif arms == 'up':
        s.mr(7 - w, 7, 9 - w, 14, sl); s.mr(7 - w, 5, 9 - w, 6, skin)
        s.mr(9 - w, 12, 10 - w, 14, sl)
    elif arms == 'out':
        s.mr(4 - w, 13, 10 - w, 15, sl); s.mr(2 - w, 13, 3 - w, 15, skin)
    elif arms == 'reach':      # both arms stretched to the viewer's left
        s.r(4, 13, 11, 15, sl); s.r(2, 13, 3, 15, skin)
        s.r(5, 17, 11, 19, sl); s.r(3, 17, 4, 19, skin)
    if head:
        s.r(14, hy + 7, 17, 12, skin)
        s.e(11, hy, 20, hy + 8, skin)
    return {'l': (9 - w, 20), 'r': (22 + w, 20)}


def face(s, eye, hy=3, mouth=DARK, wide=False):
    y = hy + 4
    if wide:
        s.mpx([(13, y), (14, y)], eye)
    else:
        s.mpx([(13, y)], eye)
    if mouth:
        s.l([(14, hy + 7), (17, hy + 7)], mouth)


def skull(s, bone, x=11, y=2, eye=None, jaw=True, w=10, h=9):
    """Skull with sockets; (x,y) is top-left of the cranium box."""
    s.e(x, y, x + w - 1, y + h - 1, bone)
    if jaw:
        s.r(x + 2, y + h - 2, x + w - 3, y + h, bone)
        s.px([(x + 3, y + h), (x + 5, y + h), (x + 7, y + h)] if w >= 10 else [(x + 3, y + h)], DARK)
    ex = x + 2
    s.r(ex, y + 3, ex + 1, y + 5, DARK); s.r(x + w - 4, y + 3, x + w - 3, y + 5, DARK)
    s.px([(x + w // 2 - 1, y + 6), (x + w // 2, y + 6)], DARK)
    if eye:
        s.px([(ex + 1, y + 4), (x + w - 4, y + 4)], eye)


def bat_wings(s, c, mem=None, y=12, span=13, drop=9, root=11):
    """Mirrored bat wings spreading up and out from the shoulders."""
    mem = mem or mul(c, 0.72)
    x0 = max(1, root - span)
    top = max(1, y - 8)
    s.mp([(root, y), (x0 + 2, top), (x0, top + 3), (x0, y + drop - 2), (x0 + 3, y + drop - 4),
          (x0 + 5, y + drop), (x0 + 7, y + drop - 3), (root, y + 5)], mem)
    s.ml([(root, y), (x0 + 2, top), (x0, top + 3)], c)
    s.ml([(x0 + 2, top), (x0 + 4, y + drop - 3)], c)
    s.ml([(x0 + 2, top), (x0 + 7, y + drop - 3)], c)


def feather_wings(s, c, y=11, span=13, drop=12, root=11, tip=None):
    tip = tip or mul(c, 0.8)
    x0 = max(1, root - span)
    top = max(1, y - 8)
    s.mp([(root, y), (x0 + 3, top), (x0, top + 2), (x0, y + drop - 5), (x0 + 2, y + drop),
          (x0 + 4, y + drop - 2), (x0 + 6, y + drop - 1), (root, y + 6)], c)
    for i in range(3):
        s.ml([(x0 + 2 + i * 2, y + drop - 6), (x0 + 2 + i * 2, y + drop - 2)], tip)
    s.ml([(root - 1, y + 1), (x0 + 3, top + 2)], tip)


def horns(s, c, style='up', hy=3, x=12):
    """Mirrored horns springing from the head top; x is the left root."""
    if style == 'up':
        s.mp([(x, hy + 2), (x - 1, hy - 2), (x + 2, hy + 1)], c)
    elif style == 'long':
        s.mp([(x, hy + 2), (x - 3, hy), (x - 4, hy - 3), (x - 2, hy - 1), (x + 2, hy + 1)], c)
    elif style == 'bull':
        s.mp([(x + 1, hy + 2), (x - 5, hy + 2), (x - 7, hy - 1), (x - 4, hy), (x + 1, hy)], c)
    elif style == 'ram':
        s.mp([(x + 1, hy + 1), (x - 2, hy), (x - 4, hy + 2), (x - 4, hy + 5), (x - 2, hy + 6),
              (x - 2, hy + 4), (x - 1, hy + 3), (x + 1, hy + 3)], c)
    elif style == 'tall':
        s.mp([(x, hy + 2), (x - 2, hy - 1), (x - 1, hy - 3), (x + 1, hy - 1), (x + 2, hy + 1)], c)
    elif style == 'stub':
        s.mpx([(x, hy), (x, hy - 1), (x + 1, hy)], c)


def tail(s, c, side=1, y=24, tip='barb', length=8):
    """Tail curling out to one side from the hips."""
    x = 20 if side > 0 else 11
    d = side
    pts = [(x, y), (x + 3 * d, y + 2), (x + (length - 2) * d, y + 1), (x + length * d, y - 3)]
    s.l(pts, c)
    s.l([(x, y + 1), (x + 3 * d, y + 3), (x + (length - 2) * d, y + 2)], c)
    ex, ey = pts[-1]
    if tip == 'barb':
        s.p([(ex, ey - 3), (ex - 2, ey), (ex + 2, ey)], c)
    elif tip == 'sting':
        s.px([(ex, ey - 1), (ex - d, ey - 2), (ex - 2 * d, ey - 2)], c)
    elif tip == 'tuft':
        s.e(ex - 1, ey - 3, ex + 1, ey, c)
    return ex, ey


def weapon(s, kind, x, y0=5, y1=22, c=STEEL, c2=WOOD, glow=None):
    """Held upright at column x (hand near y1-2). glow replaces blade/head colour."""
    g = glow or c
    if kind == 'sword':
        s.r(x, y0, x + 1, y1 - 3, g); s.px([(x, y0 - 1)], g)
        s.r(x - 2, y1 - 2, x + 3, y1 - 2, GOLD if c2 == WOOD else c2); s.r(x, y1 - 1, x + 1, y1 + 1, DARK)
    elif kind == 'great':
        s.r(x - 1, y0, x + 1, y1 - 3, g); s.px([(x, y0 - 1)], g)
        s.r(x - 3, y1 - 2, x + 3, y1 - 2, c2 if c2 != WOOD else IRON); s.r(x, y1 - 1, x, y1 + 2, DARK)
    elif kind == 'axe':
        s.r(x, y0, x, y1 + 2, c2)
        s.p([(x + 1, y0), (x + 4, y0 - 1), (x + 5, y0 + 3), (x + 4, y0 + 6), (x + 1, y0 + 5)], g)
    elif kind == 'daxe':
        s.r(x, y0, x, y1 + 2, c2)
        s.p([(x + 1, y0), (x + 4, y0 - 1), (x + 4, y0 + 6), (x + 1, y0 + 5)], g)
        s.p([(x - 1, y0), (x - 4, y0 - 1), (x - 4, y0 + 6), (x - 1, y0 + 5)], g)
    elif kind == 'staff':
        s.r(x, y0 + 4, x, 29, c2); s.e(x - 2, y0, x + 2, y0 + 4, g)
    elif kind == 'skullstaff':
        s.r(x, y0 + 5, x, 29, c2); s.e(x - 2, y0, x + 2, y0 + 4, BONE)
        s.px([(x - 1, y0 + 2), (x + 1, y0 + 2)], glow or DARK); s.px([(x, y0 + 5)], BONE)
    elif kind == 'crook':
        s.r(x, y0 + 2, x, 29, c2); s.l([(x, y0 + 2), (x + 1, y0), (x + 3, y0), (x + 4, y0 + 2), (x + 3, y0 + 4)], c2)
        s.px([(x + 2, y0 + 2)], g)
    elif kind == 'spear':
        s.r(x, y0 + 3, x, 29, c2); s.p([(x, y0 - 1), (x - 1, y0 + 3), (x + 1, y0 + 3)], g)
    elif kind == 'scythe':
        s.r(x, y0 + 1, x, 29, c2)
        s.p([(x, y0), (x - 5, y0), (x - 9, y0 + 3), (x - 5, y0 + 2), (x, y0 + 3)], g)
    elif kind == 'glaive':
        s.r(x, y0 + 5, x, 29, c2)
        s.p([(x, y0 - 1), (x + 3, y0 + 2), (x + 2, y0 + 6), (x, y0 + 6)], g)
        s.px([(x + 3, y0 + 4), (x + 3, y0 + 6)], g)
    elif kind == 'trident':
        s.r(x, y0 + 3, x, 29, c2); s.r(x - 2, y0 + 3, x + 2, y0 + 3, g)
        s.r(x - 2, y0, x - 2, y0 + 3, g); s.r(x + 2, y0, x + 2, y0 + 3, g); s.r(x, y0 - 1, x, y0 + 3, g)
    elif kind == 'mace':
        s.r(x, y0 + 4, x, y1 + 2, c2); s.e(x - 2, y0, x + 2, y0 + 4, g)
        s.px([(x - 3, y0 + 2), (x + 3, y0 + 2), (x, y0 - 1)], g)
    elif kind == 'club':
        s.p([(x - 1, y0), (x + 2, y0), (x + 1, y1 + 1), (x, y1 + 1)], c2)
        s.px([(x + 2, y0 + 2), (x - 1, y0 + 4)], g)
    elif kind == 'bow':
        s.l([(x, y0), (x + 2, y0 + 4), (x + 3, (y0 + y1) // 2), (x + 2, y1 - 4), (x, y1)], c2)
        s.l([(x, y0 + 1), (x, y1 - 1)], STRING)
    elif kind == 'whip':
        s.l([(x, y1), (x + 2, y1 - 6), (x + 1, y1 - 11), (x - 2, y1 - 14), (x - 5, y1 - 12), (x - 6, y1 - 9)], g)
    elif kind == 'flame':   # flaming sword
        s.r(x, y0, x + 1, y1 - 3, g); s.px([(x, y0 - 1), (x + 2, y0 + 3), (x - 1, y0 + 6), (x + 2, y0 + 9), (x + 1, y0 - 2)], g)
        s.r(x - 2, y1 - 2, x + 3, y1 - 2, GOLD); s.r(x, y1 - 1, x + 1, y1 + 1, DARK)
    elif kind == 'wand':
        s.l([(x, y1), (x + 1, y1 - 7)], c2); s.px([(x + 1, y1 - 8)], g)
    elif kind == 'trumpet':
        s.l([(x, y1 - 2), (x + 3, y1 - 8)], GOLD, 2); s.p([(x + 2, y1 - 9), (x + 6, y1 - 10), (x + 5, y1 - 6)], GOLD)


def shield(s, x, y, c=IRON, boss=STEEL, round_=True, big=False):
    w = 6 if big else 5
    if round_:
        s.e(x, y, x + w, y + w + 1, c)
    else:
        s.p([(x, y), (x + w, y), (x + w, y + w - 1), (x + w // 2, y + w + 3), (x, y + w - 1)], c)
    s.px([(x + w // 2, y + w // 2), (x + w // 2 + 1, y + w // 2)], boss)


def crown(s, c=GOLD, hy=3, gem=None, style='points', x0=12, x1=19):
    y = hy
    s.r(x0, y, x1, y + 1, c)
    if style == 'points':
        for x in range(x0, x1 + 1, 2):
            s.px([(x, y - 1)], c)
        s.px([(x0, y - 2), (x1, y - 2), ((x0 + x1) // 2, y - 2), ((x0 + x1) // 2 + 1, y - 2)], c)
    elif style == 'tall':
        for x in (x0, x0 + 2, x1 - 2, x1):
            s.r(x, y - 3, x, y - 1, c)
        s.r((x0 + x1) // 2, y - 4, (x0 + x1) // 2 + 1, y - 1, c)
    elif style == 'spike':
        for x in (x0, x0 + 3, x1 - 3, x1):
            s.l([(x, y), (x + (-1 if x < 16 else 1), y - 4)], c)
    elif style == 'circlet':
        pass
    if gem:
        s.px([((x0 + x1) // 2, y), ((x0 + x1) // 2 + 1, y)], gem)


def flames(s, pts, lava, hot, h=4):
    """Small tongues of fire rising from each (x, y) base point."""
    for i, (x, y) in enumerate(pts):
        hh = h - (i % 2)
        s.p([(x - 1, y), (x + 1, y), (x + (i % 2), y - hh)], lava)
        s.px([(x, y)], hot)


def horse(s, c, mane=None, hoof=DARK, eye=None, armor=None, wing=None, horn=None, bones=False):
    """Horse in profile facing left; the back is at y=14, x 10..23."""
    mane = mane or mul(c, 0.6)
    for x in (9, 13, 20, 23):
        s.r(x, 21, x + 1, 27, c if x in (9, 20) else mul(c, 0.8)); s.r(x, 28, x + 1, 29, hoof)
    s.e(7, 13, 25, 22, c)
    s.p([(9, 16), (6, 8), (10, 6), (14, 14)], c)
    s.p([(10, 6), (7, 5), (2, 10), (3, 13), (6, 12), (9, 10)], c)
    s.px([(8, 4), (9, 4), (9, 3)], c)
    s.l([(10, 5), (13, 9), (14, 13)], mane, 2)
    s.l([(25, 15), (28, 17), (28, 24)], mane, 2)
    s.px([(6, 8)], eye or DARK); s.px([(3, 11)], DARK)
    if bones:
        for x in (12, 15, 18, 21):
            s.l([(x, 15), (x, 20)], DARK)
    if armor:
        s.p([(10, 6), (7, 5), (3, 9), (6, 9), (9, 8)], armor)
        s.r(11, 14, 22, 17, armor); s.l([(11, 18), (22, 18)], mul(armor, 0.7))
    if horn:
        s.l([(8, 5), (5, 0)], horn); s.l([(8, 4), (6, 1)], horn)
    if wing:
        s.p([(13, 14), (15, 4), (20, 1), (27, 2), (29, 6), (24, 8), (27, 10), (22, 11), (24, 13), (18, 15)], wing)
        s.l([(16, 6), (25, 4)], mul(wing, 0.78)); s.l([(17, 9), (24, 9)], mul(wing, 0.78))
        s.l([(17, 12), (22, 12)], mul(wing, 0.78))


def hound(s, c, eye, heads=1, ribs=None, ear=True, tailc=None, big=False, jaw=WHITE, spikes=None):
    """Dog in profile facing left."""
    dy = -2 if big else 0
    for x in (9, 12, 20, 23):
        s.r(x, 21 + dy, x + 1, 28, c if x in (9, 20) else mul(c, 0.75)); s.px([(x - 1, 28)], c)
    s.e(8, 14 + dy, 26, 22 + dy, c)
    s.l([(25, 16 + dy), (28, 13 + dy), (29, 9 + dy)], tailc or c, 2)
    hs = [(0, 0)] if heads == 1 else [(1, -6), (-1, 3), (0, -1)]
    if heads == 3:
        hs = [(4, -7), (1, 3), (0, -2)]
    for hx, hyy in hs:
        y = 12 + dy + hyy
        s.p([(11 + hx, y + 6), (8 + hx, y - 1), (12 + hx, y)], c) if heads == 1 else None
        s.e(5 + hx, y - 1, 12 + hx, y + 5, c)
        s.r(2 + hx, y + 2, 7 + hx, y + 4, c)
        s.r(3 + hx, y + 5, 7 + hx, y + 5, DARK); s.px([(3 + hx, y + 5), (5 + hx, y + 5)], jaw)
        s.px([(7 + hx, y + 1)], eye)
        if ear:
            s.p([(9 + hx, y), (10 + hx, y - 4), (12 + hx, y)], c)
        s.px([(2 + hx, y + 2)], DARK)
    if ribs:
        for x in (13, 16, 19):
            s.l([(x, 16 + dy), (x, 20 + dy)], ribs)
    if spikes:
        for x in (12, 15, 18, 21):
            s.p([(x, 14 + dy), (x + 1, 11 + dy), (x + 2, 14 + dy)], spikes)


REG = {}


def reg(*ids):
    def deco(f):
        for i in ids:
            REG[i] = f
        return f
    return deco


def brute(s, skin, eye=None, cloth=None, hy=2, headc=None, arms=True):
    """Hulking wide body with long heavy arms."""
    s.mr(10, 22, 14, 27, mul(skin, 0.82)); s.mr(9, 28, 14, 29, mul(skin, 0.7))
    s.p([(6, 10), (25, 10), (22, 22), (9, 22)], skin)
    if arms:
        s.mr(2, 11, 6, 22, mul(skin, 0.9)); s.mr(2, 23, 7, 26, skin)
    if cloth:
        s.p([(10, 20), (21, 20), (20, 25), (11, 25)], cloth)
    s.e(12, hy, 19, hy + 8, headc or skin)
    if eye:
        s.mpx([(14, hy + 4)], eye)


def mini(s, x, y, body, head, eye=None, wpn=None, legs=None):
    """Tiny 6x13 figure, top-left (x, y), for hordes and legions."""
    s.r(x + 1, y + 9, x + 2, y + 12, legs or body); s.r(x + 4, y + 9, x + 5, y + 12, legs or body)
    s.r(x + 1, y + 5, x + 5, y + 9, body)
    s.r(x, y + 5, x, y + 8, body); s.r(x + 6, y + 5, x + 6, y + 8, body)
    s.e(x + 1, y, x + 5, y + 4, head)
    if eye:
        s.px([(x + 2, y + 2), (x + 4, y + 2)], eye)
    if wpn:
        s.r(x + 7, y - 1, x + 7, y + 7, wpn)
