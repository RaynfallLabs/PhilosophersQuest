"""Dungeon tiles: ground, walls, features and traps.

Ground tiles fill the whole square and are kept low in contrast, because
creatures and items are drawn on top of them. A feature (altar, grave, trap)
is a shaded sprite laid over the floor tile.
"""
import json
import os
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image, ImageDraw  # noqa: E402
from core import Sprite, shade, GOLD, IRON, STEEL, WOOD, DARK, BONE  # noqa: E402

S = 32


def _rng(name):
    state = [zlib.crc32(name.encode()) or 1]

    def nxt(n):
        state[0] = (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return (state[0] >> 8) % n
    return nxt


def _stones(name, base, mortar, blocks, speck=10, bevel=True):
    """A square of fitted stones: each block gets a slightly different tone,
    a lit top-left edge and a shaded bottom-right edge."""
    im = Image.new('RGBA', (S, S), mortar + (255,))
    px = im.load()
    r = _rng(name)
    for (x0, y0, x1, y1) in blocks:
        tone = shade(base, 0)
        d = r(3) - 1
        col = tuple(max(0, min(255, c + d * 5)) for c in tone)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                c = col
                if bevel and (y == y0 or x == x0):
                    c = tuple(min(255, v + 12) for v in col)
                elif bevel and (y == y1 or x == x1):
                    c = tuple(max(0, v - 12) for v in col)
                px[x % S, y % S] = c + (255,)
        for _ in range(speck * (x1 - x0 + 1) * (y1 - y0 + 1) // 100):
            x, y = x0 + 1 + r(max(1, x1 - x0 - 1)), y0 + 1 + r(max(1, y1 - y0 - 1))
            k = 8 if r(2) else -8
            px[x % S, y % S] = tuple(max(0, min(255, v + k)) for v in col) + (255,)
    return im


def floor():
    blocks = [(0, 0, 14, 12), (16, 0, 31, 9), (16, 11, 31, 20), (0, 14, 9, 31),
              (11, 14, 14, 20), (11, 22, 24, 31), (26, 22, 31, 31)]
    return _stones('floor', (62, 58, 62), (40, 37, 43), blocks, speck=6)


def wall():
    blocks = []
    for row, y in enumerate((0, 8, 16, 24)):
        off = 0 if row % 2 == 0 else -8
        for x in range(off, S, 16):
            blocks.append((max(0, x), y, min(31, x + 14), y + 6))
    im = _stones('wall', (104, 99, 112), (50, 47, 58), blocks, speck=8)
    px = im.load()
    for x in range(S):                       # a lit cap and a dark foot give it height
        r, g, b, a = px[x, 0]
        px[x, 0] = (min(255, r + 22), min(255, g + 22), min(255, b + 22), 255)
        px[x, 31] = (34, 31, 40, 255)
    for x, y in ((3, 13), (4, 13), (4, 14), (26, 29), (27, 29), (20, 6)):   # moss in the joints
        px[x, y] = (74, 104, 70, 255)
    return im


def rock():
    """Solid rock away from any room or passage: dark and quiet, so the
    rooms stand out and the brickwork only shows where a wall faces a floor."""
    im = Image.new('RGBA', (S, S), (24, 22, 28, 255))
    px = im.load()
    r = _rng('rock')
    for _ in range(70):
        x, y = r(S), r(S)
        k = (30, 28, 35) if r(3) else (19, 17, 22)
        px[x, y] = k + (255,)
    for (x0, y0, x1, y1) in ((3, 5, 9, 6), (20, 11, 27, 12), (8, 22, 15, 23), (22, 26, 28, 27)):
        for x in range(x0, x1 + 1):
            px[x, y0] = (34, 31, 40, 255)
            px[x, y1] = (17, 15, 20, 255)
    return im


def _over(bg, sprite_fn):
    s = Sprite()
    s.shadow = False
    sprite_fn(s)
    return Image.alpha_composite(bg, s.finish())


def door():
    bg = wall()

    def f(s):
        plank, band = (128, 86, 48), IRON
        s.rect(4, 2, 27, 31, plank)
        for x in (10, 16, 22):
            s.line([(x, 3), (x, 30)], (96, 62, 34))
        s.rect(4, 7, 27, 9, band); s.rect(4, 23, 27, 25, band)
        s.px([(6, 8), (13, 8), (19, 8), (25, 8), (6, 24), (13, 24), (19, 24), (25, 24)], STEEL)
        s.ell(21, 14, 25, 18, GOLD); s.px([(23, 16)], (96, 62, 34))
    return _over(bg, f)


def _stairs(down):
    im = Image.new('RGBA', (S, S), (30, 27, 34, 255))
    d = ImageDraw.Draw(im)
    stone = (132, 126, 136)
    n = 6
    for i in range(n):
        # down: steps shrink and darken toward the bottom; up: toward the top
        t = i / (n - 1)
        k = t if down else 1 - t
        inset = int(2 + 9 * k)
        col = tuple(int(c * (1 - 0.72 * k)) for c in stone)
        y0 = 2 + i * 5
        d.rectangle([inset, y0, 31 - inset, y0 + 3], fill=col + (255,))
        d.line([(inset, y0), (31 - inset, y0)], fill=tuple(min(255, c + 26) for c in col) + (255,))
        d.line([(inset, y0 + 4), (31 - inset, y0 + 4)], fill=(18, 16, 22, 255))
    d.rectangle([0, 0, 31, 31], outline=(70, 66, 78, 255))
    # an arrow of light says which way it goes
    a = (236, 200, 90, 255)
    if down:
        d.polygon([(13, 24), (18, 24), (16, 28), (15, 28)], fill=a)
    else:
        d.polygon([(15, 2), (16, 2), (19, 6), (12, 6)], fill=a)
    return im


def stairs_down(): return _stairs(True)
def stairs_up(): return _stairs(False)


def altar():
    def f(s):
        stone, cloth = (150, 146, 158), (150, 36, 44)
        flame = s.lit((255, 214, 96))
        s.rect(4, 22, 27, 29, (112, 108, 122)); s.rect(6, 14, 25, 22, stone)
        s.rect(4, 11, 27, 14, stone)
        s.rect(11, 11, 20, 20, cloth); s.line([(11, 20), (20, 20)], GOLD)
        s.rect(15, 13, 16, 18, GOLD); s.rect(13, 14, 18, 15, GOLD)
        s.rect(6, 6, 7, 10, BONE); s.rect(24, 6, 25, 10, BONE)
        s.px([(6, 4), (7, 4), (6, 5), (24, 4), (25, 4), (25, 5)], flame)
    return _over(floor(), f)


def fountain():
    def f(s):
        stone = (146, 142, 156)
        water = (60, 132, 214)
        spray = s.lit((170, 226, 255))
        s.ell(3, 17, 28, 30, stone); s.ell(6, 19, 25, 27, water)
        s.rect(14, 9, 17, 22, stone); s.ell(11, 7, 20, 11, stone)
        s.px([(15, 5), (16, 5), (15, 3), (13, 6), (18, 6), (12, 9), (19, 9)], spray)
        s.px([(9, 22), (21, 23), (12, 25), (18, 21)], (150, 200, 240))
    return _over(floor(), f)


def grave():
    def f(s):
        stone, dirt = (142, 140, 150), (92, 66, 46)
        s.ell(5, 23, 26, 30, dirt)
        s.rect(10, 9, 21, 26, stone); s.ell(10, 4, 21, 14, stone)
        s.rect(15, 10, 16, 20, (84, 82, 96)); s.rect(12, 13, 19, 14, (84, 82, 96))
        s.px([(11, 24), (12, 25), (20, 22)], (78, 112, 72))
        s.px([(7, 26), (23, 27), (13, 28)], (120, 90, 64))
    return _over(floor(), f)


def throne():
    def f(s):
        gold, velvet = GOLD, (150, 30, 50)
        gem = s.lit((110, 220, 255))
        s.rect(8, 3, 23, 22, gold); s.rect(10, 6, 21, 20, velvet)
        s.poly([(8, 3), (10, 0), (12, 3), (14, 0), (16, 2), (17, 0), (19, 3), (21, 0), (23, 3)], gold)
        s.rect(5, 15, 8, 26, gold); s.rect(23, 15, 26, 26, gold)
        s.rect(8, 21, 23, 25, velvet); s.rect(6, 26, 25, 29, gold)
        s.px([(15, 4), (16, 4)], gem); s.px([(6, 15), (25, 15)], (250, 240, 200))
    return _over(floor(), f)


def ice():
    im = _stones('ice', (176, 214, 236), (150, 196, 226),
                 [(0, 0, 31, 31)], speck=4, bevel=False)
    d = ImageDraw.Draw(im)
    crack = (120, 170, 210, 255)
    d.line([(3, 6), (9, 10), (8, 16), (14, 20)], fill=crack)
    d.line([(9, 10), (16, 8)], fill=crack)
    d.line([(20, 22), (26, 19), (29, 24)], fill=crack)
    d.line([(22, 4), (25, 9)], fill=crack)
    for x, y in ((4, 3), (5, 3), (4, 4), (18, 13), (19, 13), (27, 28), (11, 26), (12, 26)):
        im.putpixel((x, y), (244, 252, 255, 255))
    return im


def lava():
    im = Image.new('RGBA', (S, S), (238, 106, 26, 255))
    d = ImageDraw.Draw(im)
    r = _rng('lava')
    hot, crust, edge = (255, 198, 70, 255), (74, 40, 36, 255), (150, 56, 30, 255)
    # drifting plates of cooled crust, each an uneven slab, with the melt
    # showing bright between them
    for pts in ([(1, 2), (8, 0), (12, 4), (10, 9), (3, 8)],
                [(16, 1), (26, 2), (29, 6), (22, 9), (15, 6)],
                [(3, 13), (10, 11), (14, 16), (11, 22), (5, 21), (2, 17)],
                [(18, 12), (27, 11), (31, 15), (28, 20), (20, 19)],
                [(0, 25), (7, 24), (10, 28), (6, 31), (0, 31)],
                [(13, 25), (21, 23), (25, 27), (22, 31), (14, 31)],
                [(28, 24), (31, 23), (31, 30), (28, 29)]):
        d.polygon(pts, fill=crust, outline=edge)
        d.line([pts[0], pts[1]], fill=(104, 62, 54, 255))
    for _ in range(26):
        x, y = r(S), r(S)
        if im.getpixel((x, y)) == (238, 106, 26, 255):
            im.putpixel((x, y), hot)
    return im


def water():
    im = Image.new('RGBA', (S, S), (34, 78, 150, 255))
    d = ImageDraw.Draw(im)
    deep, lite, foam = (26, 60, 124, 255), (70, 126, 200, 255), (168, 208, 240, 255)
    for y, off in ((3, 2), (9, 14), (15, 6), (21, 18), (27, 9)):
        for x0 in (off, off + 16):
            d.line([((x0) % S, y), ((x0 + 6) % S if (x0 + 6) % S > x0 % S else 31, y)], fill=lite)
            d.line([((x0 + 1) % S, y + 1), ((x0 + 4) % S if (x0 + 4) % S > (x0 + 1) % S else 31, y + 1)], fill=deep)
    for x, y in ((5, 3), (18, 9), (9, 15), (22, 21), (12, 27), (28, 14)):
        im.putpixel((x, y), foam)
    return im


# ---------------------------------------------------------------- traps (floor + a plain sign of the danger)
def _trap(fn):
    return _over(floor(), fn)


def trap_acid():
    def f(s):
        acid = s.lit((150, 236, 60)); pale = s.lit((220, 255, 150))
        s.ell(5, 14, 26, 27, (70, 120, 40)); s.ell(7, 15, 24, 25, acid)
        s.px([(11, 18), (12, 18), (19, 21), (15, 22)], pale)
        s.ell(13, 8, 16, 11, acid); s.ell(20, 10, 22, 12, acid); s.px([(9, 11)], acid)
    return _trap(f)


def trap_alarm():
    def f(s):
        ring = s.lit((255, 236, 150))
        s.rect(14, 4, 17, 6, IRON)
        s.poly([(12, 8), (19, 8), (22, 21), (9, 21)], GOLD); s.rect(8, 21, 23, 23, GOLD)
        s.ell(14, 23, 17, 26, IRON)
        s.px([(5, 10), (4, 14), (5, 18), (26, 10), (27, 14), (26, 18)], ring)
    return _trap(f)


def trap_arrow():
    def f(s):
        s.rect(3, 12, 9, 20, IRON); s.rect(5, 15, 8, 17, DARK)
        s.line([(10, 16), (24, 16)], WOOD); s.poly([(24, 13), (29, 16), (24, 19)], STEEL)
        s.poly([(10, 16), (12, 13), (14, 16)], (200, 60, 50)); s.poly([(10, 16), (12, 19), (14, 16)], (200, 60, 50))
    return _trap(f)


def trap_bear_trap():
    def f(s):
        s.ell(5, 16, 26, 28, IRON); s.ell(8, 18, 23, 26, DARK)
        for x in (7, 11, 15, 19, 23):
            s.poly([(x, 17), (x + 1, 11), (x + 2, 17)], STEEL)
        s.rect(14, 21, 17, 23, (150, 60, 50))
        s.line([(26, 22), (30, 26)], IRON)
    return _trap(f)


def trap_fire():
    def f(s):
        fl = s.lit((255, 128, 36)); core = s.lit((255, 224, 96))
        s.rect(6, 22, 25, 28, IRON)
        for x in (9, 13, 17, 21):
            s.rect(x, 23, x + 1, 27, DARK)
        s.poly([(10, 22), (12, 12), (15, 17), (16, 6), (19, 15), (21, 11), (22, 22)], fl)
        s.poly([(14, 22), (15, 16), (16, 13), (18, 18), (18, 22)], core)
    return _trap(f)


def trap_pit():
    def f(s):
        s.ell(4, 8, 27, 27, (84, 62, 46)); s.ell(6, 10, 25, 25, (22, 18, 24))
        s.ell(9, 14, 22, 24, (8, 6, 10))
        s.px([(8, 11), (22, 10), (26, 18)], (120, 92, 70))
        s.poly([(12, 22), (13, 18), (14, 22)], STEEL); s.poly([(17, 23), (18, 19), (19, 23)], STEEL)
    return _trap(f)


def trap_polymorph():
    def f(s):
        a = s.lit((250, 110, 220)); b = s.lit((110, 220, 250)); c = s.lit((250, 230, 110))
        s.ell(5, 6, 26, 27, (70, 40, 96))
        s.line([(16, 16), (20, 13), (22, 17), (19, 22), (12, 22), (9, 16), (12, 9), (20, 8)], a)
        s.px([(16, 16), (15, 16), (16, 15)], c)
        s.px([(8, 20), (23, 11), (11, 12), (21, 22), (14, 25), (18, 6)], b)
    return _trap(f)


def trap_rust():
    def f(s):
        rust, deep = (176, 96, 44), (112, 56, 34)
        s.rect(5, 7, 26, 26, IRON)
        for x in (10, 16, 21):
            s.line([(x, 8), (x, 25)], DARK)
        s.ell(6, 8, 14, 15, rust); s.ell(17, 15, 25, 24, rust); s.ell(8, 19, 13, 24, deep)
        s.px([(20, 10), (22, 11), (12, 17), (15, 22)], rust)
        s.px([(11, 27), (11, 28), (21, 27)], rust)
    return _trap(f)


def trap_sleep_gas():
    def f(s):
        gas = (166, 150, 220)
        z = s.lit((236, 230, 255))
        s.rect(11, 24, 20, 28, IRON); s.rect(13, 25, 14, 27, DARK); s.rect(17, 25, 18, 27, DARK)
        s.ell(6, 12, 17, 22, gas); s.ell(13, 8, 25, 19, gas); s.ell(9, 6, 18, 14, gas)
        s.px([(12, 11), (13, 11), (19, 13), (20, 13), (15, 17)], z)
    return _trap(f)


def trap_squeaky_board():
    def f(s):
        plank = (146, 104, 62)
        s.poly([(4, 12), (27, 9), (28, 20), (5, 23)], plank)
        s.line([(5, 16), (27, 13)], (104, 70, 40)); s.line([(5, 20), (27, 17)], (104, 70, 40))
        s.px([(7, 14), (25, 12), (7, 21), (25, 18)], IRON)
        s.line([(12, 6), (14, 3)], BONE); s.line([(17, 5), (17, 2)], BONE); s.line([(22, 5), (24, 2)], BONE)
    return _trap(f)


def trap_teleport():
    def f(s):
        ring = s.lit((170, 120, 255)); core = s.lit((236, 220, 255))
        s.ell(4, 6, 27, 27, (50, 34, 86)); s.ell(7, 9, 24, 24, ring)
        s.ell(10, 12, 21, 21, (36, 22, 66)); s.ell(13, 15, 18, 18, core)
        s.px([(15, 4), (16, 29), (2, 16), (29, 17)], ring)
    return _trap(f)


TILES = {f.__name__: f for f in (
    altar, door, floor, fountain, grave, ice, lava, stairs_down, stairs_up, throne, trap_acid,
    trap_alarm, trap_arrow, trap_bear_trap, trap_fire, trap_pit, trap_polymorph, trap_rust,
    trap_sleep_gas, trap_squeaky_board, trap_teleport, wall, water, rock)}


def draw(rec):
    return TILES[rec['id']]()


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    recs = json.load(open(os.path.join(here, 'slice.json'), encoding='utf-8'))
    n = 0
    for r in recs:
        d = os.path.join(here, 'out', r['folder'])
        os.makedirs(d, exist_ok=True)
        draw(r).save(os.path.join(d, r['id'] + '.png'))
        n += 1
    # a little room, to judge how the tiles sit together
    room = Image.new('RGBA', (S * 9, S * 5), (0, 0, 0, 255))
    lay = ['WWWWDWWWW', 'W..a..~~W', 'W<.f.g~LW', 'W.t>..iLW', 'WWWWWWWWW']
    key = {'W': wall, '.': floor, 'D': door, 'a': altar, 'f': fountain, 'g': grave, '~': water,
           'L': lava, '<': stairs_up, '>': stairs_down, 't': throne, 'i': ice}
    for y, row in enumerate(lay):
        for x, ch in enumerate(row):
            room.paste(key[ch](), (x * S, y * S))
    room.resize((S * 9 * 3, S * 5 * 3), Image.NEAREST).save(os.path.join(here, 'room.png'))
    print('wrote', n)
