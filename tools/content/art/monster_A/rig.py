"""People-shaped rig for the monster_A slice: one parametric figure (sizes,
heads, hair, hats, clothes, held things) plus small shared helpers.
Offline tooling."""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import (Sprite, shade, S, BONE, IVORY, STEEL, IRON, WOOD, LEATHER,  # noqa: E402
                  DARK, GOLD, STRING)

SKIN = (222, 174, 134)
PALE = (238, 208, 180)
TAN = (198, 142, 98)
DUSK = (140, 94, 62)
WHITE = (236, 234, 226)
GREY = (150, 150, 158)
BLACK = (46, 42, 54)
RED = (184, 46, 44)
BLUE = (62, 98, 172)
GREEN = (72, 132, 70)
PURPLE = (112, 62, 152)
BROWN = (112, 74, 46)
BLOND = (228, 192, 98)
BRONZE = (198, 144, 70)
FIRE = (255, 130, 30)
HOT = (255, 226, 90)
VOID = (26, 16, 34)


def dk(c, k=1): return shade(c, -k)
def lt(c, k=1): return shade(c, k)


_ELL = {}


def ell_pts(x0, y0, x1, y1):
    key = (x0, y0, x1, y1)
    if key not in _ELL:
        im = Image.new('1', (S, S), 0)
        ImageDraw.Draw(im).ellipse([x0, y0, x1, y1], fill=1)
        p = im.load()
        _ELL[key] = [(x, y) for y in range(S) for x in range(S) if p[x, y]]
    return _ELL[key]


def fin(s):
    """Clip paint to 1..30 so the outline fits, then run the shared finish."""
    p = s.img.load()
    for i in range(S):
        for j in (0, S - 1):
            p[i, j] = (0, 0, 0, 0)
            p[j, i] = (0, 0, 0, 0)
    return s.finish()


SIZES = {
    'child': dict(head=(11, 11, 20, 19), sh=19, tw=3, bw=3, waist=25, aw=2, arm=(20, 23), lw=2, foot=29),
    'small': dict(head=(11, 8, 20, 16), sh=16, tw=4, bw=4, waist=23, aw=3, arm=(17, 20), lw=2, foot=28),
    'stout': dict(head=(11, 8, 20, 16), sh=16, tw=6, bw=6, waist=24, aw=3, arm=(17, 22), lw=4, foot=29),
    'med': dict(head=(11, 4, 20, 13), sh=13, tw=6, bw=5, waist=23, aw=3, arm=(14, 21), lw=3, foot=29),
    'robed': dict(head=(11, 7, 20, 15), sh=15, tw=5, bw=5, waist=24, aw=3, arm=(16, 22), lw=3, foot=29),
    'large': dict(head=(11, 4, 20, 12), sh=12, tw=7, bw=6, waist=23, aw=4, arm=(13, 21), lw=4, foot=29),
    'giant': dict(head=(12, 2, 19, 9), sh=9, tw=9, bw=7, waist=21, aw=4, arm=(10, 20), lw=5, foot=29),
    'kneel': dict(head=(11, 9, 20, 18), sh=18, tw=6, bw=5, waist=27, aw=3, arm=(19, 25), lw=3, foot=29),
}

DEF = dict(size='med', skin=SKIN, head='human', eye=DARK, hair=None, hairc=BROWN, beard=None, beardc=None,
           hat=None, hatc=IRON, hat2=GOLD, torso='tunic', tc=(92, 86, 80), tc2=LEATHER, legs='pants',
           lc=DARK, boots=LEATHER, cloak=None, lh=None, rh=None, arms=('down', 'down'), sleeve='auto',
           tail=None, wings=None, pauldron=None, geo=None, lit=(), mask=None, blind=None, void=False,
           brow=False, mouth=False, muzzle=None, heads=1, crest=None, trim=True, hands=None, belly=None,
           horns=None, ears=None)


def PX(s, pts, c):
    s.px([(x, y) for x, y in pts if 1 <= x <= 30 and 1 <= y <= 30], c)


# ------------------------------------------------------------------ held things
BACK_ITEMS = ('banner', 'sack', 'pack')


def item(s, spec, hx, hy, side):
    """Draw a held thing. hx, hy is the hand; side -1 = viewer's left."""
    if not spec:
        return
    k, a = spec[0], spec[1:]

    def A(i, d):
        return a[i] if len(a) > i and a[i] is not None else d
    x = max(2, min(29, hx + side * 2))
    xa, xb = min(x, x + side), max(x, x + side)          # a 2px column
    xa, xb = max(1, xa), min(30, xb)
    inn = -side if (x >= 26 or x <= 5) else side
    inn = a[-1] * side if a and a[-1] in (-1, 1) and k in ('axe', 'greataxe', 'cleaver', 'glaive') else inn          # heads face inward near the edge
    top = lambda L: max(1, hy - L)                         # noqa: E731
    if k == 'sword':
        c = A(0, STEEL); L = A(1, 12)
        s.rect(xa, top(L), xb, hy - 1, c); PX(s, [(xa if side < 0 else xb, top(L) - 1)], c)
        s.line([(xa - 1, hy), (xb + 1, hy)], A(2, GOLD)); s.rect(xa, hy + 1, xb, hy + 2, DARK)
    elif k == 'dagger':
        c = A(0, STEEL)
        s.rect(x, hy - 5, x, hy - 1, c); s.line([(x - 1, hy), (x + 1, hy)], A(1, GOLD)); PX(s, [(x, hy + 1)], DARK)
    elif k == 'saber':
        c = A(0, STEEL)
        s.rect(xa, hy - 8, xb, hy - 1, c)
        s.poly([(x, hy - 8), (x + side, hy - 8), (x + side * 3, hy - 12), (x + side * 2, hy - 13)], c)
        s.line([(xa - 1, hy), (xb + 1, hy)], GOLD); s.rect(xa, hy + 1, xb, hy + 2, DARK)
    elif k == 'khopesh':
        c = A(0, BRONZE)
        s.rect(x, hy - 5, x, hy - 1, c)
        s.poly([(x, hy - 5), (x + side * 3, hy - 8), (x + side * 3, hy - 12), (x + side, hy - 13),
                (x + side * 2, hy - 11), (x + side * 2, hy - 8), (x, hy - 6)], c)
        s.line([(x - 1, hy), (x + 1, hy)], GOLD); PX(s, [(x, hy + 1)], DARK)
    elif k == 'katana':
        c = A(0, (214, 220, 230))
        s.line([(x, hy - 1), (x + side, hy - 7), (x + side * 2, hy - 13)], c)
        s.line([(x - 1, hy), (x + 1, hy)], DARK); s.rect(x, hy + 1, x, hy + 3, A(1, RED))
    elif k in ('axe', 'greataxe', 'cleaver'):
        c = A(0, STEEL); L = 11 if k == 'axe' else 13
        t = top(L)
        s.rect(x, t, x, min(29, hy + 4), A(1, WOOD))
        if k == 'cleaver':
            s.poly([(x, t), (x + inn * 5, t), (x + inn * 5, t + 8), (x, t + 6)], c)
        else:
            s.poly([(x, t + 1), (x + inn * 4, t - 1), (x + inn * 5, t + 3), (x + inn * 4, t + 7), (x, t + 5)], c)
            if k == 'greataxe':
                s.poly([(x, t + 1), (x - inn * 3, t), (x - inn * 3, t + 6), (x, t + 5)], c)
    elif k == 'club':
        c = A(0, WOOD)
        s.rect(x, hy - 5, x, hy + 2, c); s.rect(xa - (1 if side > 0 else 0), top(13), xb + (1 if side < 0 else 0), hy - 5, c)
        PX(s, [(x, hy - 11), (x + side, hy - 8), (x - side, hy - 7)], A(1, IRON))
    elif k == 'greatclub':
        c = A(0, WOOD)
        s.rect(x, hy - 4, x, hy + 2, c); s.ell(x - 2, top(15), x + 2, hy - 4, c)
        PX(s, [(x - 1, hy - 12), (x + 1, hy - 9), (x, hy - 7)], A(1, dk(c)))
    elif k in ('mace', 'morningstar'):
        c = A(0, IRON)
        s.rect(x, hy - 8, x, hy + 2, A(1, WOOD)); s.ell(x - 2, hy - 13, x + 2, hy - 9, c)
        if k == 'morningstar':
            PX(s, [(x, hy - 14), (x - 3, hy - 11), (x + 3, hy - 11), (x - 2, hy - 13), (x + 2, hy - 13),
                   (x - 2, hy - 9), (x + 2, hy - 9)], STEEL)
    elif k in ('hammer', 'maul'):
        c = A(0, IRON); w = 3 if k == 'hammer' else 4
        t = top(13)
        s.rect(x, t, x, min(29, hy + 3), A(1, WOOD))
        cx = x + inn * (1 if (x >= 26 or x <= 5) else 0)
        s.rect(cx - w, t, cx + w, t + (4 if k == 'hammer' else 5), c)
    elif k in ('spear', 'glaive', 'trident', 'pike'):
        t = max(2, hy - 17)
        s.rect(x, t + 2, x, 29, A(1, WOOD))
        c = A(0, STEEL)
        if k == 'spear' or k == 'pike':
            s.poly([(x, t - 1), (x - 1, t + 2), (x + 1, t + 2)], c); PX(s, [(x, t - 1), (x, t)], c)
        elif k == 'glaive':
            s.poly([(x, t - 1), (x + inn * 2, t + 1), (x + inn * 2, t + 5), (x, t + 6)], c)
        else:
            s.line([(x - 2, t + 2), (x + 2, t + 2)], c); PX(s, [(x - 2, t), (x - 2, t + 1), (x, t - 1), (x, t), (x, t + 1), (x + 2, t), (x + 2, t + 1)], c)
    elif k == 'staff':
        t = max(5, hy - 14)
        s.rect(x, t, x, 29, A(2, WOOD))
        o = A(0, None); kind = A(1, 'orb')
        if kind == 'orb' and o:
            s.ell(x - 2, t - 4, x + 2, t, s.lit(o))
        elif kind == 'skull':
            s.ell(x - 2, t - 4, x + 2, t, BONE); PX(s, [(x - 1, t - 2), (x + 1, t - 2)], s.lit(o) if o else DARK)
        elif kind == 'crook':
            PX(s, [(x, t - 1), (x, t - 2), (x + inn, t - 3), (x + inn * 2, t - 3), (x + inn * 3, t - 2), (x + inn * 3, t - 1)], A(2, WOOD))
        elif kind == 'snake':
            c = o or GREEN
            PX(s, [(x - 1, t + 6), (x + 1, t + 4), (x - 1, t + 2), (x + 1, t), (x, t - 1), (x - 1, t - 2), (x, t - 3), (x + 1, t - 3)], c)
        elif kind == 'feather':
            PX(s, [(x, t - 1), (x, t - 2)], A(2, WOOD))
            PX(s, [(x - 1, t + 1), (x - 2, t + 2), (x - 2, t + 3), (x + 1, t + 1), (x + 2, t + 2), (x + 2, t + 3)], o or RED)
            s.ell(x - 1, t - 3, x + 1, t - 1, BONE)
        elif kind == 'knob':
            s.ell(x - 1, t - 2, x + 1, t, A(2, WOOD))
        elif kind == 'cross':
            s.rect(x, t - 4, x, t, o or GOLD); s.line([(x - 2, t - 2), (x + 2, t - 2)], o or GOLD)
        elif kind == 'star':
            c = s.lit(o or HOT)
            PX(s, [(x, t - 1), (x, t - 2), (x, t - 3), (x - 1, t - 2), (x + 1, t - 2), (x - 2, t - 2), (x + 2, t - 2), (x, t - 4)], c)
    elif k == 'bow':
        c = A(0, WOOD)
        t, b = max(2, hy - 10), min(29, hy + 9)
        m = (t + b) // 2
        s.line([(x, t), (x + side * 2, t + 4), (x + side * 3, m), (x + side * 2, b - 4), (x, b)], c)
        s.line([(x, t + 1), (x, b - 1)], A(1, STRING))
    elif k == 'crossbow':
        s.line([(hx, hy), (hx + side * 5, hy)], WOOD); s.line([(hx + side * 4, hy - 3), (hx + side * 5, hy), (hx + side * 4, hy + 3)], IRON)
        PX(s, [(hx + side * 6, hy)], STEEL)
    elif k == 'shield':
        c = A(0, IRON); e = A(1, GOLD); kind = A(2, 'round'); rim = A(3, dk(c))
        cx, cy = hx + (0 if abs(hx - 15.5) > 8 else side), hy - 3
        if kind == 'round':
            s.ell(cx - 4, cy - 4, cx + 4, cy + 4, rim); s.ell(cx - 3, cy - 3, cx + 3, cy + 3, c)
            s.rect(cx, cy, cx, cy, e); PX(s, [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)], e)
        elif kind == 'lambda':
            s.ell(cx - 5, cy - 5, cx + 5, cy + 5, rim); s.ell(cx - 4, cy - 4, cx + 4, cy + 4, c)
            s.line([(cx - 2, cy + 3), (cx, cy - 3), (cx + 2, cy + 3)], e)
        elif kind == 'kite':
            s.poly([(cx - 4, cy - 5), (cx + 4, cy - 5), (cx + 4, cy + 1), (cx, cy + 7), (cx - 4, cy + 1)], rim)
            s.poly([(cx - 3, cy - 4), (cx + 3, cy - 4), (cx + 3, cy + 1), (cx, cy + 5), (cx - 3, cy + 1)], c)
            s.rect(cx, cy - 3, cx, cy + 3, e); s.line([(cx - 2, cy - 1), (cx + 2, cy - 1)], e)
        elif kind == 'spiked':
            s.ell(cx - 4, cy - 4, cx + 4, cy + 4, rim); s.ell(cx - 3, cy - 3, cx + 3, cy + 3, c)
            PX(s, [(cx, cy), (cx - 2, cy - 2), (cx + 2, cy - 2), (cx - 2, cy + 2), (cx + 2, cy + 2), (cx, cy - 5), (cx, cy + 5), (cx - 5, cy), (cx + 5, cy)], STEEL)
        elif kind == 'tower':
            s.rect(cx - 4, cy - 6, cx + 4, cy + 7, rim); s.rect(cx - 3, cy - 5, cx + 3, cy + 6, c)
            for yy in (cy - 3, cy, cy + 3):
                PX(s, [(cx - 2, yy), (cx, yy + 1), (cx + 2, yy)], e)
    elif k == 'banner':
        c = A(0, WHITE)
        s.rect(x, 2, x, 29, WOOD); PX(s, [(x, 1)], GOLD)
        s.poly([(x - side, 2), (x - side * 7, 3), (x - side * 6, 5), (x - side * 7, 8), (x - side, 8)], c)
        if A(1, None):
            PX(s, [(x - side * 3, 4), (x - side * 3, 5), (x - side * 3, 6), (x - side * 2, 5), (x - side * 4, 5)], A(1, GOLD))
    elif k == 'torch':
        f = s.lit(A(0, FIRE)); h = s.lit(HOT)
        q = 6 if hy >= 14 else 2
        s.rect(x, hy - q, x, hy + 2, WOOD)
        s.poly([(x - 2, hy - q - 1), (x, hy - q - 5), (x + 2, hy - q - 1)], f); s.rect(x - 1, hy - q - 2, x + 1, hy - q - 1, f)
        PX(s, [(x, hy - q - 2), (x, hy - q - 3)], h)
    elif k == 'flame':
        f = s.lit(A(0, FIRE)); h = s.lit(A(1, HOT))
        s.poly([(hx - 2, hy - 1), (hx, hy - 6), (hx + 2, hy - 1)], f); s.rect(hx - 1, hy - 2, hx + 1, hy, f); PX(s, [(hx, hy - 1), (hx, hy - 2)], h)
    elif k == 'orb':
        c = s.lit(A(0, (130, 200, 255)))
        s.ell(hx - 2, hy - 3, hx + 2, hy + 1, c); PX(s, [(hx - 1, hy - 2)], s.lit((255, 255, 255)))
    elif k == 'book':
        c = A(0, RED)
        s.rect(hx - 2, hy - 3, hx + 2, hy + 1, c); s.rect(hx - 1, hy - 2, hx + 2, hy, WHITE); s.rect(hx - 2, hy - 3, hx - 2, hy + 1, c)
    elif k == 'scroll':
        s.rect(hx - 1, hy - 4, hx + 1, hy + 2, WHITE); PX(s, [(hx - 1, hy - 4), (hx + 1, hy - 4), (hx - 1, hy + 2), (hx + 1, hy + 2)], A(0, (200, 170, 110)))
    elif k == 'lantern':
        c = s.lit(A(0, HOT))
        s.line([(hx, hy), (hx, hy + 1)], IRON); s.rect(hx - 2, hy + 2, hx + 2, hy + 6, IRON); s.rect(hx - 1, hy + 3, hx + 1, hy + 5, c)
    elif k == 'sack':
        c = A(0, (150, 128, 90))
        s.ell(hx - 4, hy - 9, hx + 3, hy - 1, c); PX(s, [(hx - 1, hy - 9), (hx, hy - 9)], DARK)
    elif k == 'pack':
        c = A(0, LEATHER)
        s.rect(hx - 3, hy - 8, hx + 3, hy, c)
    elif k == 'wand':
        s.line([(hx, hy), (hx + side * 2, hy - 5)], WOOD); PX(s, [(hx + side * 2, hy - 6)], s.lit(A(0, HOT)))
    elif k == 'whip':
        c = A(0, LEATHER)
        s.line([(hx, hy), (x, hy - 4), (x + side, hy - 9), (x - side, hy - 12), (x + side, hy - 14)], c)
    elif k == 'flail':
        s.rect(x, hy - 6, x, hy + 2, WOOD)
        PX(s, [(x + side, hy - 7), (x + side, hy - 9), (x, hy - 8)], STEEL)
        s.ell(x - 1, hy - 14, x + 2, hy - 10, A(0, IRON)); PX(s, [(x, hy - 15), (x + 3, hy - 12), (x - 2, hy - 12)], STEEL)
    elif k == 'scythe':
        s.rect(x, 4, x, 29, WOOD); s.poly([(x, 4), (x - side * 7, 6), (x - side * 4, 3), (x, 2)], A(0, STEEL))
    elif k == 'censer':
        PX(s, [(hx, hy + 1), (hx, hy + 2), (hx, hy + 3)], GOLD)
        s.rect(hx - 1, hy + 4, hx + 1, hy + 6, A(0, GOLD)); PX(s, [(hx, hy + 5)], s.lit(A(1, FIRE)))
        sm = A(2, (190, 190, 200))
        PX(s, [(hx + side, hy + 2), (hx + side * 2, hy), (hx + side, hy - 2), (hx + side * 2, hy - 4)], sm)
    elif k == 'horn':
        s.poly([(hx, hy - 1), (hx + side * 4, hy - 4), (hx + side * 4, hy - 1), (hx + side, hy + 1)], A(0, IVORY))
        PX(s, [(hx + side * 4, hy - 4), (hx + side * 4, hy - 1)], GOLD)
    elif k == 'boulder':
        c = A(0, GREY)
        s.ell(hx - 4, hy - 8, hx + 4, hy - 1, c); PX(s, [(hx - 1, hy - 5), (hx + 2, hy - 3)], dk(c))
    elif k == 'claws':
        c = A(0, IVORY)
        PX(s, [(hx - 1, hy + 1), (hx, hy + 1), (hx + 1, hy + 1), (hx - 1, hy + 2), (hx + 1, hy + 2)], c)
    elif k == 'pipes':
        for i in range(4):
            s.rect(hx - 2 + i, hy - 4 + i // 2, hx - 2 + i, hy, A(0, (214, 190, 120)))
    elif k == 'cup':
        c = A(0, GOLD)
        s.rect(hx - 1, hy - 3, hx + 1, hy - 1, c); PX(s, [(hx, hy)], c); s.line([(hx - 1, hy + 1), (hx + 1, hy + 1)], c)
    elif k == 'mug':
        s.rect(hx - 1, hy - 3, hx + 1, hy, A(0, WHITE)); PX(s, [(hx + side * 2, hy - 2), (hx + side * 2, hy - 1)], A(0, WHITE))
        PX(s, [(hx, hy - 5), (hx + 1, hy - 6)], (200, 200, 205))
    elif k == 'pistol':
        s.rect(hx, hy - 1, hx + side * 4, hy, IRON) if side > 0 else s.rect(hx - 4, hy - 1, hx, hy, IRON)
        PX(s, [(hx, hy + 1), (hx, hy + 2)], WOOD)
    elif k == 'ball':
        s.ell(hx - 2, hy - 2, hx + 2, hy + 2, A(0, RED))
    elif k == 'triangle':
        c = A(0, GOLD)
        s.line([(hx - 3, hy + 1), (hx + 3, hy + 1), (hx + 3, hy - 5), (hx - 3, hy + 1)], c)
    elif k == 'herbs':
        s.rect(hx - 2, hy, hx + 2, hy + 3, WOOD); PX(s, [(hx - 2, hy - 1), (hx, hy - 2), (hx + 2, hy - 1), (hx - 1, hy - 1), (hx + 1, hy - 2)], A(0, GREEN))
    elif k == 'bottle':
        s.rect(hx - 1, hy - 3, hx + 1, hy, s.lit(A(0, (120, 220, 140)))); PX(s, [(hx, hy - 4), (hx, hy - 5)], GREY)
    elif k == 'pick':
        s.rect(x, hy - 9, x, hy + 3, WOOD); s.line([(x - 3, hy - 7), (x, hy - 10), (x + 3, hy - 7)], A(0, STEEL))
    elif k == 'bindle':
        s.line([(hx, hy), (hx + side * 3, hy - 11)], WOOD); s.ell(hx + side * 3 - 2, hy - 14, hx + side * 3 + 2, hy - 10, A(0, RED))


# ------------------------------------------------------------------ heads
def head_base(s, o, box):
    x0, y0, x1, y1 = box
    ey = y0 + (y1 - y0) // 2
    k, skin = o['head'], o['skin']
    if k == 'goblin':
        s.poly([(x0, ey), (x0 - 6, ey - 4), (x0 - 1, ey + 2)], skin); s.poly([(x1, ey), (x1 + 6, ey - 4), (x1 + 1, ey + 2)], skin)
    elif k in ('hob', 'elf', 'hag'):
        s.poly([(x0, ey - 1), (x0 - 3, ey - 3), (x0, ey + 1)], skin); s.poly([(x1, ey - 1), (x1 + 3, ey - 3), (x1, ey + 1)], skin)
    elif k in ('bugbear', 'bear', 'tiger'):
        s.ell(x0 - 1, y0 - 1, x0 + 3, y0 + 3, skin); s.ell(x1 - 3, y0 - 1, x1 + 1, y0 + 3, skin)
    elif k in ('gnoll', 'wolf'):
        s.poly([(x0 + 1, y0 + 3), (x0, y0 - 3), (x0 + 4, y0)], skin); s.poly([(x1 - 1, y0 + 3), (x1, y0 - 3), (x1 - 4, y0)], skin)
    elif k == 'rat':
        e = o.get('ears') or (226, 150, 150)
        s.ell(x0 - 2, y0 - 1, x0 + 3, y0 + 4, skin); s.ell(x1 - 3, y0 - 1, x1 + 2, y0 + 4, skin)
        s.ell(x0 - 1, y0, x0 + 2, y0 + 3, e); s.ell(x1 - 2, y0, x1 + 1, y0 + 3, e)
    elif k == 'bull':
        h = o.get('horns') or IVORY
        s.poly([(x0, y0 + 2), (x0 - 5, y0 + 1), (x0 - 8, y0 - 3), (x0 - 4, y0 - 1), (x0 + 1, y0)], h)
        s.poly([(x1, y0 + 2), (x1 + 5, y0 + 1), (x1 + 8, y0 - 3), (x1 + 4, y0 - 1), (x1 - 1, y0)], h)
    elif k == 'fish':
        f = o.get('crest') or dk(skin)
        s.poly([(x0 + 2, y0 + 1), (15, y0 - 3), (17, y0 - 2), (x1 - 2, y0 + 1)], f)
        s.poly([(x0, ey), (x0 - 3, ey - 2), (x0 - 3, ey + 3)], f); s.poly([(x1, ey), (x1 + 3, ey - 2), (x1 + 3, ey + 3)], f)
    if k == 'orc':
        s.ell(x0, y0, x1, y1, skin); s.rect(x0 + 1, y1 - 2, x1 - 1, y1 + 1, skin)
    elif k == 'frog':
        s.ell(x0 - 1, y0 + 2, x1 + 1, y1, skin); s.ell(x0, y0, x0 + 4, y0 + 4, skin); s.ell(x1 - 4, y0, x1, y0 + 4, skin)
    elif k in ('reptile', 'croc'):
        n = 4 if k == 'reptile' else 6
        s.ell(x0, y0, x1 - 1, y1 - 1, skin); s.rect(x1 - 3, ey, x1 + n, ey + 3, skin)
        if o.get('crest'):
            s.poly([(x0 + 1, y0 + 2), (x0 + 3, y0 - 2), (x0 + 5, y0), (x0 + 7, y0 - 2), (x1 - 2, y0 + 1)], o['crest'])
        if o.get('horns'):
            PX(s, [(x0 + 1, y0), (x0, y0 - 1), (x0 - 1, y0 - 2), (x0 + 4, y0 - 1), (x0 + 4, y0 - 2)], o['horns'])
    elif k != 'none':
        s.ell(x0, y0, x1, y1, skin)


def head_face(s, o, box):
    x0, y0, x1, y1 = box
    ey = y0 + (y1 - y0) // 2
    k, skin, eye = o['head'], o['skin'], o['eye']
    ex0, ex1 = x0 + 3, x1 - 3
    if k in ('human', 'elf'):
        PX(s, [(ex0, ey), (ex1, ey)], eye)
        if o['brow']:
            s.line([(ex0 - 1, ey - 1), (ex0 + 1, ey - 1)], DARK); s.line([(ex1 - 1, ey - 1), (ex1 + 1, ey - 1)], DARK)
        if o['mouth']:
            PX(s, [(15, ey + 3), (16, ey + 3)], o['mouth'] if isinstance(o['mouth'], tuple) else dk(skin, 2))
    elif k == 'hag':
        PX(s, [(ex0, ey), (ex1, ey)], eye)
        PX(s, [(15, ey), (15, ey + 1), (15, ey + 2), (14, ey + 2)], dk(skin))
        s.line([(14, ey + 4), (17, ey + 4)], DARK); PX(s, [(15, ey + 4)], o.get('teeth') or IVORY)
    elif k == 'cyclops':
        s.ell(13, ey - 2, 18, ey + 1, WHITE); s.rect(15, ey - 1, 16, ey, eye); s.line([(13, ey - 3), (18, ey - 3)], dk(skin, 2))
        s.line([(14, ey + 3), (17, ey + 3)], DARK)
    elif k == 'goblin':
        PX(s, [(ex0, ey), (ex1 + 1, ey)], eye); s.line([(15, ey + 2), (17, ey + 2)], DARK); PX(s, [(16, ey + 1)], dk(skin))
    elif k == 'orc':
        s.line([(x0 + 2, ey - 2), (x1 - 2, ey - 2)], DARK); PX(s, [(ex0, ey - 1), (ex1, ey - 1)], eye)
        PX(s, [(x0 + 2, y1 - 1), (x0 + 2, y1 - 2), (x1 - 2, y1 - 1), (x1 - 2, y1 - 2)], IVORY)
        s.line([(14, y1), (17, y1)], DARK)
    elif k == 'hob':
        s.line([(x0 + 2, ey - 1), (x1 - 2, ey - 1)], DARK); PX(s, [(ex0, ey), (ex1, ey)], eye)
        PX(s, [(15, ey + 1), (16, ey + 1)], o.get('nose') or (70, 90, 150)); s.line([(14, ey + 3), (17, ey + 3)], DARK)
        PX(s, [(14, ey + 2), (17, ey + 2)], IVORY)
    elif k in ('bugbear', 'gnoll', 'wolf', 'bear', 'tiger'):
        m = o['muzzle'] or lt(skin)
        s.ell(13, ey, 18, y1 + 1, m)
        PX(s, [(15, ey + 1), (16, ey + 1)], DARK); PX(s, [(ex0, ey - 1), (ex1, ey - 1)], eye)
        s.line([(14, y1), (17, y1)], DARK); PX(s, [(14, y1 + 1), (17, y1 + 1)], IVORY)
        if k == 'tiger':
            PX(s, [(15, y0 + 1), (16, y0 + 2), (x0 + 1, ey), (x0 + 2, ey + 1), (x1 - 1, ey), (x1 - 2, ey + 1), (13, y0 + 1), (18, y0 + 1)], DARK)
        if k == 'gnoll':
            PX(s, [(x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 1, ey + 1), (x1 - 1, ey + 1)], dk(skin, 2))
    elif k == 'rat':
        m = o['muzzle'] or lt(skin)
        s.poly([(13, ey), (18, ey), (16, y1 + 2), (15, y1 + 2)], m); PX(s, [(15, y1 + 2), (16, y1 + 2)], (226, 130, 140))
        PX(s, [(ex0, ey - 1), (ex1, ey - 1)], eye); PX(s, [(15, y1 + 3)], IVORY)
        PX(s, [(12, ey + 2), (11, ey + 3), (19, ey + 2), (20, ey + 3)], lt(skin, 2))
    elif k == 'bull':
        m = o['muzzle'] or lt(skin)
        s.ell(x0 + 1, ey, x1 - 1, y1 + 1, m)
        PX(s, [(x0 + 2, ey - 1), (x1 - 2, ey - 1)], eye)
        s.line([(x0 + 1, ey - 2), (x0 + 3, ey - 2)], DARK); s.line([(x1 - 3, ey - 2), (x1 - 1, ey - 2)], DARK)
        PX(s, [(14, y1 - 2), (17, y1 - 2)], DARK)
        if o.get('ring', True):
            PX(s, [(15, y1), (16, y1)], GOLD)
    elif k == 'crow':
        bk = o.get('beak') or (226, 178, 62)
        s.poly([(13, ey + 1), (18, ey + 1), (16, y1 + 3), (15, y1 + 3)], bk)
        PX(s, [(ex0, ey - 1), (ex1, ey - 1)], eye)
    elif k == 'fish':
        s.ell(x0, ey - 3, x0 + 3, ey, o.get('eyeball') or (240, 230, 150)); s.ell(x1 - 3, ey - 3, x1, ey, o.get('eyeball') or (240, 230, 150))
        PX(s, [(x0 + 2, ey - 1), (x1 - 2, ey - 1)], DARK)
        s.line([(x0 + 3, y1 - 2), (x1 - 3, y1 - 2)], DARK); PX(s, [(x0 + 2, y1 - 3), (x1 - 2, y1 - 3)], DARK)
    elif k == 'frog':
        PX(s, [(x0 + 2, y0 + 2), (x1 - 2, y0 + 2)], eye)
        PX(s, [(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], o.get('eyeball') or (240, 230, 120))
        s.line([(x0 + 1, y1 - 3), (x1 - 1, y1 - 3)], DARK)
        s.rect(x0 + 2, y1 - 2, x1 - 2, y1, o['belly'] or lt(skin))
    elif k in ('reptile', 'croc'):
        n = 4 if k == 'reptile' else 6
        PX(s, [(x1 - 4, ey - 1)], eye); PX(s, [(x1 + n, ey)], DARK)
        s.line([(x1 - 2, ey + 2), (x1 + n, ey + 2)], DARK)
        if k == 'croc':
            PX(s, [(x1, ey + 3), (x1 + 2, ey + 3), (x1 + 4, ey + 3), (x1 + 1, ey + 1), (x1 + 3, ey + 1), (x1 + 5, ey + 1)], IVORY)


def hair(s, o, box, sh):
    k, c = o['hair'], o['hairc']
    if not k:
        return
    x0, y0, x1, y1 = box
    ey = y0 + (y1 - y0) // 2
    E = ell_pts(*box)
    if k in ('short', 'long', 'wild', 'topknot', 'pony', 'bun', 'fringe', 'curly', 'pigtails', 'part'):
        PX(s, [(x, y) for x, y in E if y <= y0 + 2 or ((x <= x0 + 1 or x >= x1 - 1) and y <= ey)], c)
    if k == 'fringe':
        PX(s, [(x, y) for x, y in E if y <= y0 + 3], c)
    if k == 'part':
        PX(s, [(x, y) for x, y in E if y <= y0 + 3 and x <= 15], c); PX(s, [(16, y0 + 1), (16, y0 + 2)], dk(c))
    if k == 'long':
        s.rect(x0 - 1, y0 + 3, x0, sh + 4, c); s.rect(x1, y0 + 3, x1 + 1, sh + 4, c)
    if k == 'wild':
        PX(s, [(x0 + 1, y0 - 1), (x0 + 3, y0 - 2), (15, y0 - 1), (x1 - 3, y0 - 2), (x1 - 1, y0 - 1), (x0 - 1, y0 + 2), (x1 + 1, y0 + 2)], c)
        s.rect(x0 - 1, y0 + 3, x0, sh + 2, c); s.rect(x1, y0 + 3, x1 + 1, sh + 2, c)
    if k == 'curly':
        PX(s, [(x0 + 2, y0 - 1), (x0 + 4, y0 - 1), (x1 - 4, y0 - 1), (x1 - 2, y0 - 1), (x0 - 1, ey - 1), (x1 + 1, ey - 1), (x0 - 1, ey - 3), (x1 + 1, ey - 3)], c)
    if k == 'topknot':
        s.rect(15, y0 - 3, 16, y0 - 1, c); PX(s, [(14, y0 - 3), (17, y0 - 3)], c)
    if k == 'bun':
        s.ell(14, y0 - 3, 17, y0, c)
    if k == 'pony':
        s.rect(x1, y0 + 2, x1 + 2, y0 + 4, c); s.rect(x1 + 1, y0 + 4, x1 + 2, sh + 4, c)
    if k == 'mohawk':
        s.rect(15, max(1, y0 - 3), 16, y0 + 2, c)
    if k == 'bald_fringe':
        PX(s, [(x, y) for x, y in E if (x <= x0 + 1 or x >= x1 - 1) and y0 + 2 <= y <= ey + 1], c)
    if k == 'tuft':
        PX(s, [(15, y0 - 1), (16, y0 - 2), (14, y0), (17, y0 - 1), (16, y0 - 1)], c)
    if k == 'pigtails':
        s.rect(x0 - 2, ey - 1, x0 - 1, ey + 4, c); s.rect(x1 + 1, ey - 1, x1 + 2, ey + 4, c)


def beard(s, o, box):
    b = o['beard']
    if not b:
        return
    c = o['beardc'] or o['hairc']
    x0, y0, x1, y1 = box
    ey = y0 + (y1 - y0) // 2
    E = ell_pts(*box)
    if b in ('short', 'long', 'huge'):
        PX(s, [(x, y) for x, y in E if y >= ey + 2], c)
        PX(s, [(15, ey + 3), (16, ey + 3)], dk(c, 2))
    if b == 'long':
        s.poly([(x0 + 2, y1), (x1 - 2, y1), (16, y1 + 5), (15, y1 + 5)], c)
    if b == 'huge':
        s.poly([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1), (x1 - 2, y1 + 5), (16, y1 + 8), (15, y1 + 8), (x0 + 2, y1 + 5)], c)
    if b == 'stache':
        s.line([(x0 + 3, ey + 2), (x1 - 3, ey + 2)], c)
    if b == 'bigstache':
        s.rect(x0 + 2, ey + 2, x1 - 2, ey + 3, c); PX(s, [(x0 + 1, ey + 4), (x1 - 1, ey + 4), (x0 + 2, ey + 4), (x1 - 2, ey + 4), (x0 + 1, ey + 3), (x1 - 1, ey + 3)], c)
    if b == 'goatee':
        s.rect(15, ey + 3, 16, y1 + 1, c); s.line([(x0 + 3, ey + 2), (x1 - 3, ey + 2)], c)
    if b == 'stubble':
        sk = o['skin']
        PX(s, [(x, y) for x, y in E if y >= ey + 2], (sk[0] * 5 // 6, sk[1] * 4 // 5, sk[2] * 4 // 5))


def hat(s, o, box, sh):
    """Returns True when the hat hides the face."""
    k, c, c2 = o['hat'], o['hatc'], o['hat2']
    if not k:
        return False
    x0, y0, x1, y1 = box
    ey = y0 + (y1 - y0) // 2
    E = ell_pts(*box)
    face = o['skin'] if not o['void'] else VOID
    if k in ('hood', 'cowl', 'wimple'):
        if k == 'cowl':
            s.poly([(x0, y0 + 5), (15, max(1, y0 - 3)), (16, max(1, y0 - 3)), (x1, y0 + 5)], c)
        PX(s, ell_pts(x0 - 1, y0 - 1, x1 + 1, y1), c)
        s.poly([(x0, y1 - 1), (x1, y1 - 1), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)], c)
        if k == 'wimple':
            s.rect(x0 + 1, y0 + 2, x1 - 1, y1 + 1, c2)
        s.rect(x0 + 2, y0 + 3, x1 - 2, y1 - 1, face)
        if o['hair'] == 'fringe':
            s.rect(x0 + 2, y0 + 3, x1 - 2, y0 + 3, o['hairc'])
    elif k in ('helm', 'horned', 'kettle', 'winged', 'spike'):
        PX(s, [(x, y) for x, y in E if y <= ey - 2], c)
        s.line([(x0, ey - 2), (x1, ey - 2)], dk(c)); s.rect(15, ey - 1, 16, ey, c)
        if k == 'horned':
            h = c2 if c2 != GOLD else IVORY
            s.poly([(x0, ey - 3), (x0 - 3, max(1, y0 - 2)), (x0 - 1, y0 + 1), (x0 + 1, y0 + 1)], h)
            s.poly([(x1, ey - 3), (x1 + 3, max(1, y0 - 2)), (x1 + 1, y0 + 1), (x1 - 1, y0 + 1)], h)
        if k == 'kettle':
            s.rect(x0 - 2, ey - 2, x1 + 2, ey - 2, c)
        if k == 'winged':
            s.poly([(x0, ey - 2), (x0 - 3, y0 - 2), (x0 - 1, y0 - 2), (x0 + 1, y0 + 1)], WHITE)
            s.poly([(x1, ey - 2), (x1 + 3, y0 - 2), (x1 + 1, y0 - 2), (x1 - 1, y0 + 1)], WHITE)
        if k == 'spike':
            s.rect(15, max(1, y0 - 3), 16, y0, c2)
    elif k in ('fullhelm', 'corinth', 'plume'):
        if o['crest']:
            s.ell(x0 + 1, max(1, y0 - 3), x1 - 1, y0 + 4, o['crest'])
            if k == 'plume':
                s.rect(15, max(1, y0 - 3), 16, y0, o['crest'])
        PX(s, E, c)
        s.rect(x0 + 1, y1 - 2, x1 - 1, y1, c)
        if k == 'corinth':
            s.rect(x0 + 2, ey - 1, x1 - 2, ey, DARK); s.rect(15, ey, 16, y1, DARK)
            PX(s, [(x0 + 3, ey), (x1 - 3, ey)], o['eye'] if o['eye'] != DARK else WHITE)
        else:
            s.line([(x0 + 2, ey), (x1 - 2, ey)], DARK); PX(s, [(15, ey + 2), (16, ey + 2), (15, ey + 4), (16, ey + 4)], dk(c, 2))
            if o['eye'] != DARK:
                PX(s, [(x0 + 3, ey), (x1 - 3, ey)], o['eye'])
        return True
    elif k == 'crown':
        h = min(2, y0 - 1)
        s.rect(x0 + 1, y0, x1 - 1, y0 + 1, c)
        for xx in (x0 + 1, x0 + 2, 15, 16, x1 - 2, x1 - 1):
            s.rect(xx, y0 - h, xx, y0, c)
        PX(s, [(15, y0 + 1), (16, y0 + 1)], c2 if c2 != GOLD else RED)
    elif k == 'circlet':
        s.line([(x0 + 1, y0 + 2), (x1 - 1, y0 + 2)], c); PX(s, [(15, y0 + 2), (16, y0 + 2)], c2)
    elif k == 'wizard':
        s.poly([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (17, y0 - 3), (18, y0 - 6), (16, y0 - 5), (14, y0 - 2)], c)
        s.rect(x0 - 2, y0 + 1, x1 + 2, y0 + 2, c); s.line([(x0 + 1, y0), (x1 - 1, y0)], c2)
    elif k in ('cap', 'peak', 'beret', 'feather', 'deerstalker'):
        PX(s, [(x, y) for x, y in E if y <= y0 + 2], c)
        if k == 'peak':
            s.rect(x0, y0 + 3, x1 + 2, y0 + 3, c2); PX(s, [(x, y) for x, y in E if y <= y0 + 2 and 13 <= x <= 18], WHITE)
        if k == 'beret':
            s.ell(x0 - 1, y0 - 2, x1 - 1, y0 + 2, c)
        if k == 'feather':
            s.poly([(x0 - 1, y0 + 3), (x1 + 3, y0 + 3), (x1, y0 + 1), (x0, y0 + 1)], c)
            s.line([(x0 + 2, y0), (x0 - 1, y0 - 3)], c2)
        if k == 'deerstalker':
            s.rect(x0 - 1, y0 + 3, x1 + 1, y0 + 3, c); PX(s, [(15, y0 - 1), (16, y0 - 1)], c2)
            s.rect(x0, y0 + 1, x0 + 1, y0 + 2, c2); s.rect(x1 - 1, y0 + 1, x1, y0 + 2, c2)
    elif k == 'bandana':
        s.rect(x0, y0 + 2, x1, y0 + 3, c); PX(s, [(x, y) for x, y in E if y < y0 + 2], c)
        PX(s, [(x1 + 1, y0 + 3), (x1 + 2, y0 + 4), (x1 + 1, y0 + 5)], c)
    elif k == 'headband':
        s.rect(x0, y0 + 2, x1, y0 + 2, c)
    elif k == 'turban':
        s.ell(x0 - 1, y0 - 2, x1 + 1, y0 + 4, c); s.line([(x0 + 1, y0 + 2), (x1 - 2, y0 - 1)], dk(c)); PX(s, [(15, y0 + 1), (16, y0 + 1)], c2)
    elif k == 'veil':
        PX(s, ell_pts(x0 - 1, y0 - 1, x1 + 1, y1), c); s.poly([(x0 - 1, y0 + 4), (x1 + 1, y0 + 4), (x1 + 2, y1 + 3), (x0 - 2, y1 + 3)], c)
        s.rect(x0 + 2, y0 + 3, x1 - 2, y1, c2)
        return True
    elif k == 'mitre':
        s.poly([(x0 + 1, y0 + 2), (x0 + 1, y0 - 2), (15, y0 - 6), (16, y0 - 6), (x1 - 1, y0 - 2), (x1 - 1, y0 + 2)], c)
        s.rect(15, y0 - 4, 16, y0 + 1, c2); s.line([(x0 + 1, y0 + 2), (x1 - 1, y0 + 2)], c2)
    elif k == 'tricorn':
        s.rect(x0 + 2, y0 - 2, x1 - 2, y0, c); s.rect(x0 - 2, y0 + 1, x1 + 2, y0 + 2, c)
        PX(s, [(x0 - 2, y0), (x1 + 2, y0)], c); s.line([(x0 - 1, y0 + 1), (x1 + 1, y0 + 1)], c2)
    elif k == 'pilos':
        s.poly([(x0 + 1, y0 + 2), (x1 - 1, y0 + 2), (16, y0 - 2), (15, y0 - 2)], c)
    elif k == 'laurel':
        PX(s, [(x0, y0 + 3), (x0 + 1, y0 + 2), (x0 + 2, y0 + 1), (x0 + 4, y0), (x1, y0 + 3), (x1 - 1, y0 + 2), (x1 - 2, y0 + 1), (x1 - 4, y0)], c)
    elif k == 'antlers':
        for sd, bx in ((-1, x0 + 2), (1, x1 - 2)):
            s.line([(bx, y0 + 1), (bx + sd * 2, y0 - 2), (bx + sd * 4, max(1, y0 - 5))], c)
            s.line([(bx + sd * 2, y0 - 2), (bx + sd * 1, max(1, y0 - 5))], c)
            s.line([(bx + sd * 3, y0 - 3), (bx + sd * 5, y0 - 3)], c)
    elif k == 'headdress':
        cols = [c, c2, c, c2, c]
        for i, xx in enumerate((x0 + 1, x0 + 3, 15, x1 - 3, x1 - 1)):
            s.line([(xx, y0 + 1), (xx + (i - 2), max(1, y0 - 4 + abs(i - 2)))], cols[i]); s.line([(xx + 1, y0 + 1), (xx + 1 + (i - 2), max(1, y0 - 4 + abs(i - 2)))], cols[i])
        s.line([(x0 + 1, y0 + 2), (x1 - 1, y0 + 2)], LEATHER)
    elif k == 'skullmask':
        PX(s, [(x, y) for x, y in E if y <= ey + 1], BONE)
        s.rect(x0 + 2, ey - 1, x0 + 4, ey, DARK); s.rect(x1 - 4, ey - 1, x1 - 2, ey, DARK)
        PX(s, [(x0 + 1, y0 - 1), (x0, y0 - 2), (x1 - 1, y0 - 1), (x1, y0 - 2)], BONE)
    elif k == 'halo':
        g = s.lit(c)
        s.line([(x0 + 1, max(1, y0 - 2)), (x1 - 1, max(1, y0 - 2))], g); PX(s, [(x0, max(2, y0 - 1)), (x1, max(2, y0 - 1))], g)
    return False


def draw_head(s, ob, box, sh):
    head_base(s, ob, box)
    hair(s, ob, box, sh)
    hid = hat(s, ob, box, sh)
    if not hid:
        bx0, by0, bx1, by1 = box
        ey = by0 + (by1 - by0) // 2
        head_face(s, ob, box)
        if ob['blind']:
            s.rect(bx0 + 1, ey - 1, bx1 - 1, ey, ob['blind'])
        if ob['mask']:
            s.rect(bx0 + 2, ey + 1, bx1 - 2, by1 - 1, ob['mask'])
        beard(s, ob, box)


def nudge(c):
    return (max(0, c[0] - 8), max(0, c[1] - 8), max(0, c[2] - 5))


# ------------------------------------------------------------------ the figure
def fig(s, **kw):
    o = dict(DEF)
    o.update(kw)
    g = dict(SIZES[o['size']])
    g.update(o['geo'] or {})
    for c in o['lit']:
        s.lit(c)
    x0, y0, x1, y1 = g['head']
    sh, tw, bw, waist, aw, lw, foot = g['sh'], g['tw'], g['bw'], g['waist'], g['aw'], g['lw'], g['foot']
    a0, a1 = g['arm']
    skin, tc, tc2, lc = o['skin'], o['tc'], o['tc2'], o['lc']
    tl, tr = 16 - tw, 15 + tw
    lax, rax = (tl - aw, tl - 1), (tr + 1, tr + aw)
    tt, lt_ = o['torso'], o['legs']
    if tt in ('robe', 'toga', 'dress'):
        lt_ = 'robe'
    # behind the body
    if o['cloak']:
        s.poly([(tl - 1, sh), (tr + 1, sh), (tr + 3, foot - 2), (tl - 3, foot - 2)], o['cloak'])
    if o['wings']:
        wc = o['wings']
        s.poly([(tl, sh + 1), (tl - 7, sh - 5), (tl - 9, sh + 2), (tl - 7, sh + 9), (tl - 2, sh + 6)], wc)
        s.poly([(tr, sh + 1), (tr + 7, sh - 5), (tr + 9, sh + 2), (tr + 7, sh + 9), (tr + 2, sh + 6)], wc)
    if o['tail']:
        tcol = o['tail'] if isinstance(o['tail'], tuple) else skin
        s.poly([(14, waist - 2), (8, waist + 3), (4, waist + 1), (3, waist + 3), (7, waist + 6), (15, waist + 1)], tcol)
    hands = {}
    for sp, ax, side in ((o['lh'], lax, -1), (o['rh'], rax, 1)):
        if sp and sp[0] in BACK_ITEMS:
            pose = o['arms'][0 if side < 0 else 1]
            hy = a1 if pose == 'down' else sh - 6
            item(s, sp, (ax[0] + ax[1]) // 2, hy, side)
    # legs
    L0, L1, R0, R1 = 15 - lw, 14, 17, 16 + lw
    bt = o['boots'] if o['boots'] else (skin if lt_ == 'bare' else lc)
    if lt_ in ('pants', 'bare', 'greaves'):
        c = skin if lt_ == 'bare' else lc
        s.rect(L0, waist - 1, L1, foot - 1, c); s.rect(R0, waist - 1, R1, foot - 1, c)
        if lt_ == 'greaves':
            s.rect(L0, foot - 5, L1, foot - 2, o['boots']); s.rect(R0, foot - 5, R1, foot - 2, o['boots'])
        s.rect(L0 - 1, foot - 1, L1, foot, bt); s.rect(R0, foot - 1, R1 + 1, foot, bt)
    elif lt_ == 'goat':
        s.rect(L0, waist - 1, L1, foot - 4, lc); s.rect(R0, waist - 1, R1, foot - 4, lc)
        s.rect(L0 + 1, foot - 4, L1, foot - 1, lc); s.rect(R0, foot - 4, R1 - 1, foot - 1, lc)
        s.rect(L0, foot - 1, L1, foot, DARK); s.rect(R0, foot - 1, R1, foot, DARK)
    elif lt_ == 'kneel':
        s.rect(16 - bw, waist - 1, 15 + bw + 3, foot - 1, lc); s.rect(15 + bw + 2, foot - 2, 15 + bw + 4, foot, bt)
        s.rect(16 - bw, foot, 15 + bw, foot, lc)
    elif lt_ == 'snake':
        s.ell(8, waist - 1, 23, 29, lc)
        s.poly([(21, 27), (27, 26), (29, 21), (30, 24), (28, 29), (20, 29)], lc)
        b = o['belly'] or lt(lc)
        s.ell(12, waist + 2, 19, 28, b); s.line([(12, waist + 4), (19, waist + 4)], lc); s.line([(12, waist + 6), (19, waist + 6)], lc)
    elif lt_ == 'robe':
        s.rect(L0, foot, L1, foot, bt); s.rect(R0, foot, R1, foot, bt)
    # torso
    if tt in ('robe', 'toga', 'dress'):
        s.poly([(tl, sh), (tr, sh), (15 + bw + 3, foot - 1), (16 - bw - 3, foot - 1)], tc)
        if tt == 'robe' and o['trim']:
            s.rect(15, sh + 1, 16, foot - 2, tc2); s.line([(16 - bw - 2, foot - 2), (15 + bw + 2, foot - 2)], tc2)
        if tt == 'toga':
            s.poly([(tl, sh), (tl + 5, sh), (tl, sh + 5)], skin)
            s.line([(tr, sh + 1), (tl + 1, waist - 1)], tc2); s.line([(tr - 1, sh + 5), (tl + 3, waist + 3)], tc2)
        if tt == 'dress':
            s.line([(16 - bw, waist - 3), (15 + bw, waist - 3)], tc2)
            s.line([(16 - bw - 2, foot - 2), (15 + bw + 2, foot - 2)], tc2)
    else:
        body = skin if tt in ('bare', 'vest', 'top') else tc
        s.poly([(tl, sh), (tr, sh), (15 + bw, waist), (16 - bw, waist)], body)
        if tt == 'tunic':
            s.line([(16 - bw, waist - 2), (15 + bw, waist - 2)], tc2); PX(s, [(15, waist - 2), (16, waist - 2)], GOLD)
        elif tt == 'armor':
            s.line([(tl + 1, sh + 4), (tr - 1, sh + 4)], tc2); s.line([(16 - bw, waist - 2), (15 + bw, waist - 2)], DARK)
            s.rect(15, sh + 1, 16, sh + 3, tc2)
        elif tt == 'tabard':
            s.rect(13, sh, 18, waist, tc2); s.line([(16 - bw, waist - 2), (15 + bw, waist - 2)], DARK)
        elif tt in ('bare', 'vest'):
            if o['belly']:
                s.ell(tl + 3, sh + 1, tr - 3, waist - 2, o['belly'])
            else:
                s.line([(tl + 2, sh + 4), (14, sh + 4)], dk(skin)); s.line([(17, sh + 4), (tr - 2, sh + 4)], dk(skin))
                s.rect(15, sh + 1, 15, waist - 4, dk(skin))
            if tt == 'vest':
                s.poly([(tl, sh), (tl + 3, sh), (16 - bw + 2, waist), (16 - bw, waist)], tc)
                s.poly([(tr, sh), (tr - 3, sh), (15 + bw - 2, waist), (15 + bw, waist)], tc)
            s.poly([(16 - bw, waist - 2), (15 + bw, waist - 2), (15 + bw - 1, waist + 3), (16 - bw + 1, waist + 3)], tc)
            s.line([(16 - bw, waist - 2), (15 + bw, waist - 2)], tc2)
        elif tt == 'top':
            s.rect(tl + 1, sh + 1, tr - 1, sh + 4, tc); s.line([(16 - bw, waist - 1), (15 + bw, waist - 1)], tc2)
        elif tt == 'suit':
            s.poly([(14, sh), (17, sh), (16, sh + 4), (15, sh + 4)], WHITE); s.rect(15, sh + 1, 16, sh + 3, tc2)
            PX(s, [(15, sh + 6), (15, sh + 8)], dk(tc, 2))
        elif tt == 'skirt':
            s.poly([(16 - bw, waist - 2), (15 + bw, waist - 2), (15 + bw + 1, waist + 3), (16 - bw - 1, waist + 3)], tc)
            s.line([(16 - bw, waist - 2), (15 + bw, waist - 2)], tc2)
            if o['trim']:
                s.line([(16 - bw - 1, waist + 3), (15 + bw + 1, waist + 3)], tc2)
        elif tt == 'fur':
            PX(s, [(x, waist + 1) for x in range(16 - bw, 16 + bw, 2)], tc)
            s.line([(tl + 1, sh + 1), (tr - 2, waist - 2)], tc2)
        elif tt == 'scale':
            for y in range(sh + 1, waist, 2):
                PX(s, [(x, y) for x in range(tl + 1 + (y % 4) // 2, tr, 2) if abs(x - 15.5) < tw - (y - sh) * (tw - bw) / max(1, waist - sh)], tc2)
            s.line([(16 - bw, waist - 1), (15 + bw, waist - 1)], DARK)
    # arms
    sl = o['sleeve']
    if sl == 'auto':
        sl = nudge(skin) if tt in ('bare', 'vest', 'toga', 'top') else tc
    hc = o['hands'] or skin
    for i, (ax, side) in enumerate(((lax, -1), (rax, 1))):
        pose = o['arms'][i]
        cx = (ax[0] + ax[1]) // 2
        if pose == 'down':
            s.rect(ax[0], a0, ax[1], a1, sl); s.rect(ax[0], a1 - 1, ax[1], a1, hc)
            hands[side] = (cx, a1)
        elif pose == 'up':
            s.rect(ax[0], sh - 5, ax[1], sh + 2, sl); s.rect(ax[0], sh - 6, ax[1], sh - 5, hc)
            hands[side] = (cx, sh - 6)
        elif pose == 'fwd':
            inner = tl + 3 if side < 0 else tr - 3
            s.rect(ax[0], a0, ax[1], a0 + 5, sl)
            s.rect(min(ax[0], inner), a0 + 4, max(ax[1], inner), a0 + 6, sl)
            s.rect(inner - (0 if side < 0 else 1), a0 + 4, inner + (1 if side < 0 else 0), a0 + 6, hc)
            hands[side] = (inner, a0 + 5)
        else:
            hands[side] = (cx, a1)
    if o['pauldron']:
        s.ell(lax[0], sh - 1, tl + 1, sh + 3, o['pauldron']); s.ell(tr - 1, sh - 1, rax[1], sh + 3, o['pauldron'])
    # head(s)
    if o['heads'] == 2:
        w = (x1 - x0 + 1) // 2
        for dx, extra in ((-w, None), (w, o.get('head2'))):
            ob = dict(o)
            if extra:
                ob.update(extra)
            t = Sprite(); t.glow = s.glow
            draw_head(t, ob, g['head'], sh)
            sh_img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
            sh_img.paste(t.img, (dx, 0))
            s.img.paste(sh_img, (0, 0), sh_img)
    else:
        draw_head(s, o, g['head'], sh)
    # held things
    for sp, side in ((o['lh'], -1), (o['rh'], 1)):
        if sp and sp[0] not in BACK_ITEMS:
            item(s, sp, hands[side][0], hands[side][1], side)
    g.update(hands=hands, tl=tl, tr=tr, lax=lax, rax=rax, ey=y0 + (y1 - y0) // 2, o=o)
    return g
