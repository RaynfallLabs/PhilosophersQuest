"""Named armor and shields (one drawing each) and the stray ids.
Offline tooling (not loaded at runtime)."""
import math
import zlib

import rigs
from rigs import A, P, TEMPLATES, MATS, shade, surface, sparks, mail, big_scales, quilt, h2, GOLD, STEEL, IRON, DARK, LEATHER

NAMED = {}
STRAY = {}
WHITE = (240, 240, 244)
RED = (190, 44, 48)
BRONZE = (196, 146, 66)
IVORY = (238, 230, 200)


def named(fn):
    def run(rec):
        s = A()
        fn(s)
        s.clip()
        return s.finish()
    NAMED[fn.__name__] = run
    return fn


def pal(s, base, trim, cls='metal', fx='streak', glow=None, seed=3):
    return P(s, base, trim, cls, fx, glow, seed)


def rig(name, tpl, base, trim, cls='metal', fx='streak', glow=None, extra=None, table=None, pre=None):
    def run(rec):
        s = A()
        p = pal(s, base, trim, cls, fx, glow, zlib.crc32(name.encode()) & 0xfff)
        if pre:
            pre(s, p)
        TEMPLATES[tpl](s, p)
        if extra:
            extra(s, p)
        sparks(s, p)
        s.clip()
        return s.finish()
    (NAMED if table is None else table)[name] = run


def disc(s, r, c, cx=16, cy=16):
    s.ell(cx - r, cy - r, cx + r - 1, cy + r - 1, c)


def round_shield(s, rim, face, r=13, band=2):
    disc(s, r, rim); disc(s, r - band, face)


def heater(s, rim, face):
    s.sym([(5, 3), (5, 14), (9, 23), (15, 29)], rim)
    s.sym([(7, 5), (7, 14), (10, 21), (15, 26)], face)


def kite(s, rim, face):
    s.ell(5, 1, 26, 17, rim); s.poly([(5, 9), (26, 9), (16, 30), (15, 30)], rim)
    s.ell(7, 3, 24, 15, face); s.poly([(7, 9), (24, 9), (16, 27), (15, 27)], face)


def streak(s, col, c, off=0.34, wd=2):
    pts = s.pts(col)
    if not pts:
        return
    x0 = min(q[0] for q in pts); y0 = min(q[1] for q in pts)
    w = max(q[0] for q in pts) - x0; h = max(q[1] for q in pts) - y0
    c0 = int(x0 + y0 + (w + h) * off)
    for x, y in pts:
        if 0 <= x + y - c0 < wd:
            s.px([(x, y)], c)


def speck(s, col, c, n, k=0):
    for x, y in s.pts(col):
        if h2(x, y, k) % n == 0:
            s.px([(x, y)], c)


def wing(s, x, y, d, c, big=1):
    """Small feathered wing rooted at (x, y), sweeping up and out in direction d."""
    k = big
    s.poly([(x, y), (x + d * 5 * k, y - 6 * k), (x + d * 5 * k, y - 3 * k), (x + d * 7 * k, y - 3 * k),
            (x + d * 5 * k, y - 1), (x + d * 6 * k, y + 1), (x + d * 3, y + 2), (x, y + 2)], c)
    s.line([(x + d, y), (x + d * 4 * k, y - 4 * k)], shade(c, -1))


def gorgon(s, cx, cy, skin, snake, eye):
    for a in range(0, 360, 45):
        dx, dy = math.cos(math.radians(a + 22)), math.sin(math.radians(a + 22))
        s.line([(cx + dx * 3, cy + dy * 3), (cx + dx * 6, cy + dy * 6), (cx + dx * 7 + dy * 2, cy + dy * 7 - dx * 2)], snake, 2)
    s.ell(cx - 4, cy - 4, cx + 3, cy + 4, skin)
    s.rect(cx - 3, cy - 1, cx - 2, cy - 1, eye); s.rect(cx + 1, cy - 1, cx + 2, cy - 1, eye)
    s.rect(cx - 2, cy + 2, cx + 1, cy + 2, (60, 40, 50)); s.px([(cx - 1, cy + 3), (cx, cy + 3)], (190, 50, 60))


# =============================================================== SHIELDS
@named
def aegis_of_athena(s):
    rim, face = (178, 132, 52), (238, 216, 150)
    round_shield(s, rim, face)
    streak(s, face, (255, 248, 216), 0.25, 2); streak(s, face, (255, 248, 216), 0.36, 1)
    gorgon(s, 16, 16, (128, 168, 104), (70, 120, 70), s.lit((255, 230, 90)))


@named
def greater_aegis_of_athena(s):
    rim, face = (226, 190, 80), (196, 214, 248)
    for a in range(0, 360, 30):
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        s.line([(16 + dx * 11, 16 + dy * 11), (15.5 + dx * 14.4, 15.5 + dy * 14.4)], GOLD, 2)
    round_shield(s, rim, face, 12, 2)
    disc(s, 7, shade(face, -1))
    gorgon(s, 16, 16, (214, 226, 200), (60, 140, 110), s.lit((120, 240, 255)))


@named
def ancile(s):
    rim, face = (150, 104, 46), (200, 150, 70)
    s.ell(7, 1, 24, 16, rim); s.ell(7, 15, 24, 30, rim)
    s.ell(9, 3, 22, 14, face); s.ell(9, 17, 22, 28, face); s.rect(12, 12, 19, 19, face)
    s.cpoly([(6, 15), (10, 13), (10, 18)]); s.cpoly([(25, 15), (21, 13), (21, 18)])
    s.rect(15, 4, 16, 27, (180, 44, 44))
    s.ell(13, 13, 18, 18, (232, 196, 110)); s.px([(15, 15)], (255, 240, 190))
    s.px([(12, 7), (19, 7), (12, 23), (19, 23)], (120, 76, 36))


@named
def assyrian_siege_pavise(s):
    a, b, iron = (176, 134, 84), (126, 90, 56), (96, 98, 110)
    s.poly([(8, 8), (9, 3), (15, 1), (22, 2), (25, 6), (23, 9), (23, 29), (8, 29)], a)
    s.over(a, lambda x, y: b if ((x // 2) + (y // 2)) % 2 else None)
    for y in (10, 18, 26):
        s.rect(8, y, 23, y + 1, iron); s.px([(10, y), (15, y), (21, y)], STEEL)
    s.poly([(9, 3), (15, 1), (22, 2), (25, 6), (22, 5), (15, 4)], shade(a, 1))


@named
def battersea_votive_shield(s):
    rim, face, red = (150, 116, 50), (206, 172, 88), s.lit((232, 50, 50))
    s.ell(8, 1, 23, 10, rim); s.ell(8, 21, 23, 30, rim); s.rect(8, 6, 23, 25, rim)
    s.ell(10, 3, 21, 10, face); s.ell(10, 21, 21, 28, face); s.rect(10, 7, 21, 24, face)
    for cy, r in ((7, 3), (16, 4), (25, 3)):
        disc(s, r, rim, 16, cy); disc(s, r - 1, shade(face, 1), 16, cy)
        s.px([(15, cy - 1), (16, cy - 1), (15, cy), (16, cy)], red)
    s.px([(13, 15), (18, 15), (13, 16), (18, 16)], red)
    s.line([(12, 11), (14, 12)], rim); s.line([(19, 11), (17, 12)], rim); s.line([(12, 21), (14, 20)], rim); s.line([(19, 21), (17, 20)], rim)


@named
def bronze_aegis(s):
    rim, face, verd = (128, 96, 48), (182, 142, 72), (96, 170, 136)
    round_shield(s, rim, face)
    speck(s, face, verd, 5, 1); speck(s, rim, verd, 3, 2)
    s.poly([(8, 16), (12, 12), (19, 12), (23, 16), (19, 20), (12, 20)], IVORY)
    disc(s, 3, (60, 110, 120)); s.rect(15, 15, 16, 16, DARK)
    s.line([(8, 10), (12, 9), (19, 9), (23, 10)], rim)


@named
def buckler_of_the_sumerian_lugal(s):
    rim, face = (140, 100, 44), (206, 164, 84)
    round_shield(s, rim, face, 10, 2)
    for x, y in ((11, 11), (15, 10), (19, 11), (10, 15), (20, 15), (11, 19), (15, 20), (19, 19)):
        s.px([(x, y), (x + 1, y), (x, y + 1)], (104, 70, 30))
    disc(s, 3, (232, 200, 120)); s.px([(15, 15)], (255, 244, 200))


@named
def carolingian_kite(s):
    rim, a, b = (112, 116, 130), (168, 60, 50), (222, 206, 160)
    kite(s, rim, a)
    s.over(a, lambda x, y: b if x > 15 else None)
    for q in ((7, 6), (24, 6), (10, 20), (21, 20), (16, 26)):
        s.line([(16, 9), q], rim)
    disc(s, 3, STEEL, 16, 9); s.px([(15, 8)], WHITE)


@named
def celtic_oval_shield(s):
    rim, face, cream = (150, 110, 60), (104, 142, 96), (236, 226, 180)
    s.ell(7, 1, 24, 30, rim); s.ell(9, 3, 22, 28, face)
    s.rect(15, 3, 16, 28, rim)
    for cy, d in ((8, 1), (23, -1)):
        s.line([(12, cy), (14, cy - 2 * d), (18, cy - 2 * d), (19, cy), (18, cy + 2 * d), (15, cy + d)], cream)
    s.ell(12, 12, 19, 19, (120, 124, 138)); s.line([(14, 14), (17, 14), (17, 17), (15, 17), (15, 16)], STEEL)


@named
def etruscan_round_shield(s):
    rim, face = (130, 94, 40), (196, 150, 64)
    round_shield(s, rim, face)
    disc(s, 9, rim); disc(s, 8, face); disc(s, 6, rim); disc(s, 5, shade(face, 1))
    s.ell(12, 12, 19, 19, IVORY); s.px([(13, 14), (18, 14)], DARK)
    s.rect(14, 17, 17, 17, DARK); s.px([(15, 18), (16, 18)], RED)
    s.px([(12, 11), (14, 10), (17, 10), (19, 11)], (80, 120, 70))


@named
def germanic_kriegsschild(s):
    fur, a, b = (214, 196, 160), (60, 84, 150), (226, 220, 200)
    disc(s, 13, fur)
    for ang in range(0, 360, 20):
        x = 15.5 + 12.6 * math.cos(math.radians(ang)); y = 15.5 + 12.6 * math.sin(math.radians(ang))
        s.px([(int(round(x)), int(round(y)))], (150, 120, 84))
    disc(s, 11, a)
    s.over(a, lambda x, y: b if (x + y) > 31 else None)
    for x in (10, 16, 21):
        s.over([a, b], lambda x_, y: shade(a if (x_ + y) <= 31 else b, -1) if x_ == x else None)
    disc(s, 3, (110, 112, 124)); s.px([(15, 15)], STEEL)


@named
def heater_of_the_black_prince(s):
    heater(s, (150, 154, 170), (38, 36, 46))
    for x, top in ((10, 8), (15, 6), (20, 8)):
        s.rect(x, top + 2, x + 1, top + 9, WHITE)
        s.px([(x - 1, top), (x, top), (x + 1, top - 1), (x + 2, top), (x + 2, top + 1), (x - 1, top + 1), (x - 1, top + 3), (x + 2, top + 3)], WHITE)
        s.px([(x, top + 10), (x + 1, top + 11)], (200, 200, 210))
    s.line([(9, 19), (22, 19)], (226, 190, 80))


@named
def hittite_chariot_guard(s):
    rim, face = (176, 140, 96), (104, 70, 46)
    s.sym([(15, 2), (9, 2), (5, 7), (10, 15), (5, 24), (9, 29)], rim)
    s.sym([(15, 4), (10, 4), (7, 7), (12, 15), (7, 24), (10, 27)], face)
    speck(s, face, shade(face, -1), 6)
    s.rect(15, 4, 16, 27, rim)
    s.mpx([(9, 7), (9, 24), (12, 11), (12, 20)], (220, 190, 130))
    s.rect(14, 14, 17, 17, (200, 150, 70))


@named
def horse_armor_of_the_norns(s):
    rim, face, pale = (120, 130, 160), (176, 190, 216), (240, 244, 255)
    thread = s.lit((255, 236, 150))
    kite(s, rim, face)
    for x in (10, 15, 20):
        s.rect(x, 7, x + 1, 8, pale); s.poly([(x, 9), (x + 1, 9), (x + 2, 14), (x - 1, 14)], shade(face, -2))
        s.px([(x, 9), (x + 1, 9)], pale)
    s.ell(12, 16, 19, 21, rim); s.ell(13, 17, 18, 20, (60, 90, 150))
    s.line([(11, 12), (15, 15), (20, 12)], thread); s.line([(15, 15), (16, 25)], thread)


@named
def khopesh_breaker_of_thebes(s):
    rim, hide, patch = (150, 96, 54), (236, 222, 190), (132, 84, 50)
    s.ell(7, 1, 24, 18, rim); s.rect(7, 9, 24, 29, rim)
    s.ell(9, 3, 22, 16, hide); s.rect(9, 9, 22, 27, hide)
    for cx, cy, r in ((12, 8, 3), (19, 13, 3), (12, 19, 4), (20, 23, 3), (15, 26, 2)):
        s.ell(cx - r, cy - r + 1, cx + r, cy + r - 1, patch)
    s.over([patch], lambda x, y: hide if not (9 <= x <= 22 and y <= 27) else None)
    s.ell(7, 1, 24, 18, rim) if False else None
    s.rect(14, 12, 17, 15, rim); s.px([(15, 13), (16, 14)], DARK)


@named
def lendings_of_beowulf(s):
    iron, blue = (96, 98, 112), (74, 96, 190)
    fire = s.lit((255, 160, 50))
    round_shield(s, blue, iron, 13, 3)
    speck(s, blue, (130, 90, 190), 3, 1)
    streak(s, iron, (150, 152, 166), 0.3, 2)
    disc(s, 4, (70, 72, 86)); disc(s, 2, (150, 152, 166))
    s.px([(8, 25), (10, 27), (13, 28), (19, 28), (23, 25), (5, 20), (26, 21)], fire)
    s.px([(15, 5), (16, 5), (5, 15), (26, 15), (15, 26)], STEEL)


@named
def lionheart_shield(s):
    steel, gold, mane = (170, 176, 192), (236, 190, 70), (176, 120, 40)
    heater(s, (110, 114, 132), steel)
    streak(s, steel, (214, 220, 232), 0.28, 2)
    s.px([(9, 8), (22, 17), (10, 15), (20, 7), (12, 22)], (120, 124, 142))
    s.ell(10, 7, 21, 19, mane)
    for a in range(0, 360, 40):
        s.px([(int(15.5 + 6.4 * math.cos(math.radians(a))), int(13.5 + 6.4 * math.sin(math.radians(a))))], mane)
    s.ell(12, 9, 19, 17, gold)
    s.px([(13, 12), (18, 12)], DARK); s.rect(15, 14, 16, 15, DARK); s.px([(14, 16), (17, 16)], DARK)
    s.mpx([(12, 8)], gold)


@named
def macedonian_aspis_of_philip(s):
    rim, face, sun = (150, 110, 44), (206, 168, 80), (255, 236, 160)
    round_shield(s, rim, face, 11, 2)
    disc(s, 8, rim); disc(s, 7, face)
    for a in range(0, 360, 45):
        dx, dy = math.cos(math.radians(a + 22)), math.sin(math.radians(a + 22))
        s.line([(15.5 + dx * 3, 15.5 + dy * 3), (15.5 + dx * 6.6, 15.5 + dy * 6.6)], sun)
    disc(s, 2, sun); s.px([(15, 15)], WHITE)
    for a in range(0, 360, 45):
        s.px([(int(round(15.5 + 8.6 * math.cos(math.radians(a)))), int(round(15.5 + 8.6 * math.sin(math.radians(a)))))], sun)


@named
def mameluke_targe(s):
    rim, face, gold = (206, 164, 60), (52, 62, 92), (240, 200, 90)
    s.line([(15, 26), (15, 30)], RED, 2); s.px([(14, 30), (17, 30)], RED)
    round_shield(s, rim, face, 11, 2)
    for a in (45, 135, 225, 315):
        cx = 15.5 + 5 * math.cos(math.radians(a)); cy = 15.5 + 5 * math.sin(math.radians(a))
        s.ell(cx - 1.4, cy - 1.4, cx + 1.4, cy + 1.4, gold)
    s.line([(15, 8), (17, 10), (15, 12), (16, 14)], gold); s.line([(16, 23), (14, 21), (16, 19), (15, 17)], gold)
    s.line([(8, 16), (10, 14), (12, 16)], gold); s.line([(23, 15), (21, 17), (19, 15)], gold)
    disc(s, 2, gold); s.px([(15, 15)], WHITE)


@named
def mycenaean_tower_of_telamon(s):
    rim, hide, patch = (116, 80, 50), (224, 206, 168), (150, 100, 60)
    s.ell(6, 1, 25, 14, rim); s.rect(6, 7, 25, 30, rim)
    s.ell(8, 3, 23, 13, hide); s.rect(8, 8, 23, 28, hide)
    for cx, cy, rx, ry in ((12, 9, 3, 3), (20, 15, 3, 4), (11, 20, 3, 3), (18, 25, 4, 2)):
        s.ell(cx - rx, cy - ry, cx + rx, cy + ry, patch)
    s.over([patch], lambda x, y: rim if not (8 <= x <= 23 and y <= 28) else None)
    s.line([(8, 17), (23, 17)], rim)
    for x in range(9, 23, 2):
        s.px([(x, 16), (x + 1, 18)], IVORY)
    s.rect(15, 3, 16, 28, shade(rim, -1))


@named
def o_tate_of_the_samurai(s):
    wood, dk, red = (96, 58, 36), (56, 34, 26), (196, 50, 44)
    s.line([(21, 12), (27, 29)], (130, 90, 54), 2)
    s.rect(6, 3, 21, 28, wood)
    for x in (10, 14, 18):
        s.line([(x, 4), (x, 28)], dk)
    s.rect(5, 2, 22, 4, dk); s.rect(6, 12, 21, 13, dk); s.rect(6, 23, 21, 24, dk)
    s.px([(8, 12), (19, 12), (8, 23), (19, 23)], GOLD)
    s.ell(10, 15, 17, 22, (30, 26, 30)); s.ell(12, 17, 15, 20, red)
    s.rect(11, 6, 16, 9, red)


@named
def pelte_of_the_thracian(s):
    a, b, rim = (214, 190, 134), (160, 130, 84), (120, 84, 54)
    s.ell(3, 5, 28, 29, rim); s.ell(5, 7, 26, 27, a)
    s.over(a, lambda x, y: b if ((x // 2) + (y // 2)) % 2 else None)
    s.cell(8, -3, 23, 14)
    for x, y in s.pts(a, b):
        if s.get(x, y - 1) is None and 7 < x < 24:
            s.px([(x, y)], rim)
    s.ell(13, 18, 18, 23, rim); s.px([(15, 20)], a)


@named
def pridwen(s):
    rim, face, blue = (226, 190, 90), (238, 238, 250), (60, 90, 190)
    halo = s.lit((255, 236, 150))
    round_shield(s, rim, face)
    s.ell(12, 5, 19, 12, halo)
    s.poly([(13, 12), (18, 12), (22, 24), (9, 24)], blue)
    s.ell(13, 6, 18, 11, blue); s.rect(14, 8, 17, 11, (240, 206, 170))
    s.px([(14, 9), (17, 9)], DARK)
    s.line([(15, 14), (15, 23)], shade(blue, -1)); s.line([(12, 18), (10, 23)], shade(blue, 1))
    s.px([(15, 16), (16, 16), (15, 17), (16, 17)], (240, 206, 170))


@named
def scarab_of_apophis_binding(s):
    rim, g, dk = (226, 186, 70), (70, 184, 120), (30, 110, 80)
    sun = s.lit((255, 120, 50))
    for y, d in ((9, -1), (15, 0), (21, 1)):
        s.mline([(6, y), (2, y + d * 3)], dk, 1)
    round_shield(s, rim, g, 12, 1)
    s.ell(10, 4, 21, 12, dk); s.ell(12, 6, 19, 11, (50, 150, 100))
    s.line([(5, 13), (26, 13)], dk); s.rect(15, 13, 16, 27, dk)
    s.line([(9, 16), (11, 23)], shade(g, 1)); s.line([(22, 16), (20, 23)], shade(g, 1))
    s.line([(12, 16), (13, 24)], dk); s.line([(19, 16), (18, 24)], dk)
    s.rect(14, 1, 17, 4, sun)
    s.px([(13, 8), (18, 8)], rim)


@named
def scutum_of_aeneas(s):
    rim, face, sil = (176, 130, 50), (228, 196, 110), (236, 240, 250)
    g = s.lit((255, 250, 200))
    s.ell(6, 1, 25, 8, rim); s.ell(6, 24, 25, 31, rim); s.rect(6, 4, 25, 27, rim)
    s.ell(8, 3, 23, 8, face); s.ell(8, 24, 23, 29, face); s.rect(8, 5, 23, 26, face)
    s.rect(8, 10, 23, 10, rim); s.rect(8, 21, 23, 21, rim)
    disc(s, 3, rim); disc(s, 2, sil); s.px([(15, 15)], g)
    # tiny scenes: a wolf, a ship, soldiers
    s.px([(10, 7), (11, 7), (12, 7), (13, 6), (10, 8), (12, 8)], sil)
    s.px([(18, 7), (19, 7), (20, 7), (21, 6), (19, 5), (19, 6)], sil)
    for x in (10, 13, 18, 21):
        s.px([(x, 23), (x, 24), (x, 25)], sil); s.px([(x + 1, 24)], rim)
    s.px([(10, 14), (10, 17), (21, 14), (21, 17)], sil)
    s.px([(9, 4), (22, 27), (22, 12)], g)


@named
def scutum_of_the_legio(s):
    red, gold, boss = (184, 46, 36), (240, 196, 70), (190, 196, 210)
    s.ell(6, 1, 25, 8, gold); s.ell(6, 24, 25, 31, gold); s.rect(6, 4, 25, 27, gold)
    s.ell(7, 2, 24, 8, red); s.ell(7, 24, 24, 30, red); s.rect(7, 5, 24, 26, red)
    s.mpoly([(13, 13), (8, 9), (8, 12), (10, 14), (8, 15), (13, 16)], gold)
    s.mpoly([(13, 17), (9, 21), (11, 21), (13, 19)], gold)
    s.line([(15, 4), (17, 7), (14, 9), (16, 11)], gold); s.line([(16, 27), (14, 24), (17, 22), (15, 20)], gold)
    s.rect(13, 12, 18, 19, boss); s.ell(14, 14, 17, 17, shade(boss, 1))


@named
def shield_of_the_spartans(s):
    round_shield(s, (146, 104, 44), (204, 158, 76), 13, 2)
    streak(s, (204, 158, 76), (236, 204, 130), 0.24, 2)
    s.line([(15, 7), (8, 23)], RED, 3); s.line([(16, 7), (23, 23)], RED, 3)


@named
def spartan_aspis_of_leonidas(s):
    gold = s.lit((255, 220, 100))
    round_shield(s, (206, 160, 70), (150, 34, 44), 13, 3)
    s.line([(15, 8), (9, 22)], gold, 2); s.line([(16, 8), (22, 22)], gold, 2)
    s.px([(15, 3), (16, 3), (3, 15), (28, 16), (15, 28), (7, 7), (24, 7), (7, 24), (24, 24)], (120, 84, 36))


@named
def sigurds_handshield(s):
    rim, face, snake = (170, 120, 40), (238, 200, 84), (150, 44, 40)
    round_shield(s, rim, face, 10, 2)
    disc(s, 6, snake); disc(s, 4, face)
    s.rect(15, 14, 17, 16, snake); s.px([(14, 15), (15, 17)], snake)          # the coil turns in
    s.ell(19, 8, 23, 12, snake); s.px([(21, 9)], s.lit((255, 240, 120))); s.px([(24, 8), (25, 7)], snake)


@named
def skidbladnir_aegis(s):
    heater(s, (150, 156, 180), (226, 228, 246))
    hull, sail = (150, 100, 54), (206, 60, 56)
    s.poly([(8, 16), (23, 16), (20, 20), (11, 20)], hull); s.px([(7, 15), (7, 14), (24, 15), (24, 14)], hull)
    s.rect(15, 7, 15, 16, (96, 64, 40)); s.rect(11, 8, 20, 13, sail)
    s.over(sail, lambda x, y: WHITE if x % 4 < 2 else None)
    for x in range(9, 23, 3):
        s.px([(x, 22), (x + 1, 21)], (70, 120, 200))
    s.px([(13, 24), (14, 23), (17, 24), (18, 23)], (70, 120, 200))


@named
def smoking_mirror_of_tezcatlipoca(s):
    rim, obs, tq = (214, 170, 60), (26, 22, 36), (60, 200, 190)
    smoke = s.lit((150, 150, 190))
    s.line([(12, 6), (10, 4), (12, 2), (11, 1)], smoke); s.line([(18, 6), (20, 3), (18, 1)], smoke)
    s.line([(15, 5), (15, 3), (16, 2)], smoke)
    disc(s, 11, rim, 16, 18); disc(s, 9, obs, 16, 18)
    for a in range(0, 360, 45):
        s.px([(int(round(15.5 + 10 * math.cos(math.radians(a)))), int(round(17.5 + 10 * math.sin(math.radians(a)))))], tq)
    s.line([(10, 17), (14, 12)], (120, 100, 170), 2); s.line([(13, 20), (16, 16)], (70, 60, 110))
    s.px([(19, 22), (20, 21), (21, 19)], (70, 60, 110))


@named
def svalinn(s):
    gold = (240, 176, 50); core = s.lit((255, 244, 170)); hot = s.lit((255, 206, 90))
    for a in range(0, 360, 30):
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        px_, py = -dy, dx
        s.poly([(15.5 + dx * 9 + px_ * 2.4, 15.5 + dy * 9 + py * 2.4), (15.5 + dx * 14, 15.5 + dy * 14),
                (15.5 + dx * 9 - px_ * 2.4, 15.5 + dy * 9 - py * 2.4)], hot if a % 60 else gold)
    disc(s, 10, (196, 130, 36)); disc(s, 8, gold); disc(s, 5, hot); disc(s, 3, core)


NAMED['svalinn_shield'] = NAMED['svalinn']


@named
def tower_shield_of_ajax(s):
    rim, br = (176, 130, 56), (212, 170, 90)
    s.ell(5, 1, 26, 10, rim); s.ell(5, 22, 26, 31, rim); s.rect(5, 5, 26, 26, rim)
    s.rect(7, 4, 24, 27, (120, 80, 50))
    hides = [(150, 100, 60), (196, 160, 116), (120, 80, 50), (176, 130, 84), (150, 100, 60), (210, 180, 136), (130, 88, 54)]
    for i, c in enumerate(hides):
        s.rect(7, 4 + i * 3 + (1 if i else 0), 24, 6 + i * 3 + 1, c)
    s.rect(7, 25, 24, 27, br)
    s.ell(11, 11, 20, 20, rim); s.ell(12, 12, 19, 19, br); s.px([(14, 14)], (255, 236, 180))
    s.mpx([(8, 5), (8, 26)], br)


@named
def vajra_paramita(s):
    rim, face = (176, 120, 40), (240, 200, 80)
    v = s.lit((190, 240, 255))
    round_shield(s, rim, face, 11, 2)
    s.rect(15, 9, 16, 22, v); disc(s, 2, v)
    for d in (-1, 1):
        y = 16 + d * 5
        s.line([(13, y - d * 2), (12, y), (13, y + d * 2), (15, y + d * 3)], v)
        s.line([(18, y - d * 2), (19, y), (18, y + d * 2), (16, y + d * 3)], v)
    s.px([(15, 15), (16, 16)], WHITE)


@named
def yamas_dharma_watch(s):
    rim, face, horn = (120, 36, 40), (44, 32, 40), (226, 214, 180)
    eye = s.lit((255, 70, 50))
    s.mpoly([(11, 6), (6, 5), (3, 1), (2, 5), (5, 9), (11, 9)], horn)
    s.ell(6, 5, 25, 19, rim); s.poly([(6, 12), (25, 12), (16, 30), (15, 30)], rim)
    s.ell(8, 7, 23, 17, face); s.poly([(8, 12), (23, 12), (16, 27), (15, 27)], face)
    s.ell(11, 10, 20, 18, (90, 80, 90)); s.rect(13, 17, 18, 20, (90, 80, 90))
    s.px([(13, 13), (14, 13), (17, 13), (18, 13)], eye); s.px([(15, 16), (16, 16)], DARK)
    s.px([(14, 20), (16, 20), (18, 20)], DARK)


@named
def sarmatian_lamellar_targe(s):
    rim = (220, 180, 80)
    p = pal(s, (156, 58, 44), rim)
    round_shield(s, rim, p.b, 11, 2)
    big_scales(s, p)
    s.over(p.l, lambda x, y: (232, 150, 110))
    disc(s, 2, rim)


@named
def saxon_round_shield(s):
    rim, face, gold, iron = (110, 112, 126), (208, 182, 132), (240, 196, 70), (140, 144, 158)
    round_shield(s, rim, face)
    for x in (9, 15, 22):
        s.over(face, lambda x_, y: shade(face, -1) if x_ == x else None)
    disc(s, 4, (84, 86, 100)); disc(s, 3, iron); s.px([(15, 14)], WHITE)
    s.poly([(6, 12), (10, 10), (9, 13), (11, 16), (8, 15), (7, 19)], gold)        # bird of prey
    s.line([(20, 9), (23, 11), (22, 14), (24, 17), (22, 21), (19, 22)], gold, 2)  # dragon
    s.px([(20, 8), (19, 9)], gold); s.px([(21, 9)], RED)
    for a in range(15, 360, 45):
        s.px([(int(round(15.5 + 12 * math.cos(math.radians(a)))), int(round(15.5 + 12 * math.sin(math.radians(a)))))], gold)


@named
def hrungnirs_stone_shield(s):
    stone, crack, moss = (150, 150, 152), (62, 60, 70), (96, 130, 80)
    rune = s.lit((130, 200, 255))
    s.poly([(8, 4), (22, 3), (27, 8), (28, 20), (23, 28), (11, 29), (5, 23), (4, 10)], stone)
    s.line([(14, 4), (16, 10), (13, 15), (17, 22), (15, 28)], crack)
    s.line([(16, 10), (22, 13)], crack); s.line([(13, 15), (7, 17)], crack)
    s.px([(9, 8), (10, 8), (9, 9), (22, 22), (23, 22), (21, 23), (8, 21)], moss)
    s.px([(20, 7), (21, 8), (20, 9), (9, 13), (10, 12), (19, 17), (20, 18), (19, 19)], rune)
    s.px([(11, 24), (24, 15), (7, 12), (25, 10), (9, 26)], (184, 184, 190))
    s.cpoly([(27, 14), (29, 12), (29, 16)])


# =============================================================== HEAD
def star8(s, cx, cy, c, r=4):
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        s.line([(cx - dx * r, cy - dy * r), (cx + dx * r, cy + dy * r)], c)
        if dx and dy:
            s.line([(cx - dx * (r - 1), cy - dy * (r - 1)), (cx + dx * (r - 1), cy + dy * (r - 1))], c)


@named
def aegishjalmr(s):
    p = pal(s, (84, 90, 130), (50, 54, 90))
    rune = s.lit((170, 232, 255))
    s.ell(5, 4, 26, 32, p.b); s.crect(0, 22, 31, 31)
    s.mpoly([(5, 21), (11, 21), (11, 27), (7, 27), (5, 24)], p.b)
    surface(s, p)
    s.rect(4, 19, 27, 21, p.d); s.rect(15, 21, 16, 27, p.d)
    s.px([(7, 20), (11, 20), (20, 20), (24, 20)], p.riv)
    cx, cy = 15, 11
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        r = 5 if not (dx and dy) else 4
        s.line([(cx - dx * r, cy - dy * r), (cx + 1 + dx * r, cy + dy * r)], rune)
    s.px([(cx - 5, cy - 1), (cx - 5, cy + 1), (cx + 6, cy - 1), (cx + 6, cy + 1), (cx - 1, cy - 5), (cx + 2, cy - 5),
          (cx - 1, cy + 5), (cx + 2, cy + 5)], rune)


@named
def blindfold(s):
    c, d = (58, 56, 76), (36, 34, 50)
    s.poly([(2, 11), (10, 9), (22, 9), (26, 11), (26, 16), (22, 17), (10, 17), (2, 16)], c)
    s.poly([(24, 14), (29, 20), (28, 27), (25, 22), (23, 17)], c)
    s.poly([(22, 15), (24, 22), (21, 28), (20, 21)], d)
    s.ell(22, 9, 27, 16, d)
    s.line([(4, 13), (20, 12)], shade(c, 1)); s.line([(5, 15), (20, 15)], d)
    s.px([(24, 12), (25, 13)], shade(c, 1))


@named
def coif_of_beowulf(s):
    p = pal(s, (150, 152, 172), (96, 98, 118))
    gold = (236, 190, 70)
    s.ell(6, 3, 25, 24, p.b); s.poly([(7, 15), (24, 15), (28, 28), (3, 28)], p.b)
    mail(s, p)
    s.ell(11, 10, 20, 21, (30, 26, 36))
    s.rect(7, 8, 24, 10, p.d); s.px([(9, 9), (13, 9), (18, 9), (22, 9)], gold)
    s.rect(15, 10, 16, 15, p.d)
    # boar on the brow crest
    s.rect(12, 3, 18, 5, gold); s.px([(19, 4), (20, 5), (11, 3), (12, 2), (14, 2), (16, 2)], gold)
    s.px([(13, 6), (17, 6)], gold); s.px([(18, 4)], DARK)
    s.line([(3, 28), (28, 28)], p.l)


@named
def cow_kings_horns(s):
    gold, hi, red = (240, 196, 50), s.lit((255, 244, 170)), (200, 40, 50)
    s.mpoly([(9, 20), (6, 15), (3, 8), (4, 2), (7, 7), (10, 12), (13, 19)], gold)
    s.mline([(5, 5), (7, 11), (10, 16)], shade(gold, 1))
    s.rect(7, 19, 24, 25, gold); s.rect(7, 24, 24, 25, shade(gold, -1))
    s.sym([(8, 19), (10, 16), (12, 19)], gold); s.poly([(13, 19), (15, 15), (16, 15), (18, 19)], gold)
    s.rect(15, 20, 16, 22, red); s.mpx([(10, 21), (11, 21)], (60, 110, 200))
    s.px([(4, 3), (27, 3), (15, 16)], hi)
    s.mpoly([(7, 25), (5, 27), (8, 28), (10, 25)], (230, 220, 200))


@named
def crown_of_brahma(s):
    gold, face, dk = (236, 190, 70), (252, 226, 150), (160, 110, 36)
    lotus = s.lit((255, 170, 200))
    s.mell(1, 15, 9, 27, shade(face, -1))
    s.mpx([(3, 20), (6, 20)], DARK); s.mpx([(4, 24), (5, 24)], dk)
    s.ell(10, 14, 21, 29, face)
    s.rect(12, 20, 13, 20, DARK); s.rect(18, 20, 19, 20, DARK); s.rect(14, 25, 17, 25, dk); s.px([(15, 22), (16, 22)], dk)
    s.px([(15, 17), (16, 17)], RED)
    s.rect(1, 12, 30, 15, gold); s.rect(5, 8, 26, 11, gold); s.rect(9, 5, 22, 7, gold); s.rect(13, 2, 18, 4, gold)
    s.line([(1, 15), (30, 15)], dk); s.line([(5, 11), (26, 11)], dk); s.line([(9, 7), (22, 7)], dk)
    s.rect(15, 0, 16, 2, lotus); s.px([(14, 1), (17, 1)], lotus)
    s.px([(4, 13), (15, 13), (16, 13), (27, 13), (9, 9), (22, 9)], RED); s.px([(9, 13), (22, 13), (15, 6), (16, 6), (15, 9), (16, 9)], (60, 110, 210))


def _galahad(s, p):
    s.rect(9, 17, 11, 19, RED); s.px([(10, 16), (10, 20), (8, 18), (12, 18)], RED)


rig('great_helm_of_galahad', 'great_helm', (244, 244, 236), (228, 190, 80), 'metal', 'streak', (255, 255, 240), _galahad)


@named
def helm_of_achilles(s):
    b, d, hair = (226, 204, 92), (156, 124, 44), s.lit((255, 226, 90))
    s.poly([(13, 8), (12, 3), (14, 0), (18, 0), (23, 3), (27, 9), (29, 17), (26, 21), (25, 13), (21, 8)], hair)
    s.line([(15, 2), (15, 7)], (226, 160, 40)); s.line([(19, 2), (20, 7)], (226, 160, 40)); s.line([(24, 7), (27, 16)], (226, 160, 40))
    _corinth(s, b, d)
    for x in (9, 12, 19, 22):                                 # the four ridges
        s.line([(x + (2 if x < 15 else -2), 5), (x, 12)], d)
        s.line([(x + (3 if x < 15 else -1), 5), (x + 1, 12)], (255, 240, 170))
    s.mpx([(8, 25), (10, 26)], d)


@named
def helm_of_aragorn(s):
    w, sil, gem = (236, 232, 214), (176, 190, 214), s.lit((200, 255, 250))
    s.mpoly([(9, 16), (6, 12), (3, 5), (2, 1), (6, 4), (8, 8), (11, 11)], sil)
    s.mline([(3, 3), (6, 9), (9, 13)], WHITE); s.mline([(5, 5), (8, 11)], (140, 150, 180))
    s.sym([(15, 1), (12, 4), (10, 10), (9, 22), (10, 26)], w)
    s.rect(9, 20, 22, 22, sil); s.rect(15, 3, 16, 19, sil)
    s.rect(14, 12, 17, 15, GOLD); s.rect(15, 13, 16, 14, gem)
    s.mpx([(11, 21), (13, 21)], WHITE)
    s.mpoly([(10, 22), (12, 22), (12, 26), (10, 27)], w)
    for x in (11, 13, 18, 20):
        s.px([(x, 17)], (190, 180, 150))


@named
def helm_of_gilgamesh(s):
    g, d, hi = (226, 186, 80), (160, 116, 40), (255, 232, 150)
    s.ell(22, 12, 29, 20, g); s.line([(24, 14), (27, 18)], d); s.line([(26, 13), (28, 16)], d)   # chignon bun
    s.ell(5, 3, 24, 24, g); s.poly([(5, 14), (12, 14), (11, 27), (7, 26), (5, 22)], g)
    s.poly([(18, 14), (24, 14), (23, 24), (19, 26)], g)
    for i in range(6):
        y = 5 + i * 2
        s.line([(7 + (i % 2), y + 3), (11, y), (16, y + 1), (21, y), (23, y + 2)], d if i % 2 else hi)
    s.rect(5, 15, 24, 17, d); s.line([(5, 16), (24, 16)], hi)
    s.ell(19, 18, 22, 22, d); s.px([(20, 20)], DARK)
    s.rect(12, 18, 17, 27, (30, 26, 36)); s.crect(12, 25, 17, 31)
    s.px([(8, 20), (9, 22), (8, 24)], d)


def _corinth(s, b, d):
    s.ell(6, 3, 25, 24, b); s.poly([(6, 13), (25, 13), (24, 27), (19, 29), (12, 29), (7, 27)], b)
    s.poly([(9, 14), (14, 14), (14, 17), (10, 17)], DARK); s.poly([(17, 14), (22, 14), (21, 17), (17, 17)], DARK)
    s.rect(15, 20, 16, 30, DARK); s.crect(15, 28, 16, 31)
    s.rect(15, 13, 16, 19, d)
    s.mline([(14, 20), (14, 28)], shade(b, 1))


@named
def helm_of_hades(s):
    b, d = (52, 48, 76), (30, 28, 48)
    eye = s.lit((176, 120, 255))
    _corinth(s, b, d)
    s.line([(9, 6), (14, 4)], (96, 90, 136)); s.line([(8, 9), (9, 7)], (96, 90, 136))
    s.px([(11, 15), (12, 15), (19, 15), (20, 15)], eye)
    # the eye keeps sliding away from it: the right side dissolves
    for x, y in s.pts(b, d, DARK, (96, 90, 136)):
        k = (x - 17) + (y - 14) // 3
        if k > 0 and h2(x, y, 9) % 9 < k:
            s.cpx([(x, y)])
    s.px([(27, 9), (28, 17), (26, 24), (29, 12)], s.lit((110, 80, 170)))


@named
def helm_of_leonidas(s):
    b, d, red = (204, 164, 76), (140, 100, 40), (196, 44, 44)
    s.poly([(2, 12), (4, 5), (10, 1), (21, 1), (27, 5), (29, 12), (25, 8), (16, 6), (15, 6), (6, 8)], red)
    for x in (5, 9, 13, 18, 22, 26):
        s.line([(x, 3 + abs(x - 15) // 4), (x + (1 if x < 15 else -1), 7)], (130, 24, 34))
    s.line([(6, 9), (15, 7), (16, 7), (25, 9)], DARK)
    _corinth(s, b, d)
    s.crect(0, 0, 31, 0)
    s.line([(9, 8), (13, 6)], (244, 214, 140)); s.px([(8, 11)], (244, 214, 140))
    s.mpx([(8, 25), (10, 26)], d)


@named
def tarnhelm(s):
    b, d, l = (124, 126, 146), (84, 86, 106), (176, 180, 200)
    g = s.lit((210, 230, 255))
    s.ell(6, 4, 25, 26, b); s.crect(0, 18, 31, 31)
    s.poly([(6, 17), (25, 17), (26, 27), (21, 25), (16, 28), (15, 28), (10, 25), (5, 27)], b)
    s.over(b, lambda x, y: l if (x + y) % 2 == 0 else (d if (x - y) % 4 == 1 else None))
    s.rect(6, 15, 25, 17, d); s.px([(8, 16), (12, 16), (16, 16), (20, 16), (23, 16)], l)
    s.ell(11, 18, 20, 26, (30, 28, 40)); s.crect(11, 25, 20, 31)
    for x, y in s.pts(b, d, l):
        if y > 18 and h2(x, y, 4) % 14 < (y - 18):
            s.cpx([(x, y)])
    s.px([(4, 22), (27, 20), (8, 29), (22, 29), (16, 2)], g)


@named
def trainers_cap(s):
    red, white, dk = (228, 44, 44), (244, 244, 244), (150, 24, 34)
    s.ell(5, 5, 24, 30, red); s.crect(0, 19, 31, 31)
    s.poly([(10, 19), (9, 10), (13, 7), (19, 7), (22, 11), (22, 19)], white)
    s.poly([(12, 18), (28, 18), (30, 21), (27, 23), (13, 22)], red)
    s.line([(13, 22), (27, 23)], dk); s.rect(5, 17, 12, 19, dk)
    s.rect(14, 4, 16, 5, dk)
    s.poly([(13, 14), (16, 11), (19, 14), (16, 15)], (60, 170, 90))
    s.line([(6, 12), (8, 8)], (255, 130, 120))


# =============================================================== BODY
def _ragnarok(s, p):
    bone = IVORY
    for y in (10, 13, 16):
        s.mline([(11, y + 1), (14, y)], bone, 1)
    s.mpoly([(3, 6), (1, 1), (6, 4)], bone); s.mpoly([(7, 5), (8, 1), (10, 5)], bone)
    s.px([(12, 8), (18, 17), (11, 23), (20, 25), (13, 18)], p.g)
    s.line([(18, 9), (19, 12), (18, 14)], p.g)


rig('armor_of_ragnarok', 'plate', (86, 70, 62), (150, 80, 40), 'metal', 'rust', (255, 140, 40), _ragnarok)


@named
def babr_e_bayan(s):
    o, st, w = (222, 150, 54), (50, 34, 30), (244, 236, 214)
    s.sym([(12, 4), (5, 8), (3, 18), (7, 19), (9, 13), (8, 29)], o)
    for y in range(8, 29, 3):
        s.mline([(8 if y > 12 else 5, y), (11, y + 1), (13, y)], st)
    s.mline([(4, 14), (7, 15)], st); s.mline([(5, 11), (8, 11)], st)
    s.rect(15, 5, 16, 29, shade(o, -1))
    s.sym([(12, 3), (10, 5), (13, 9), (15, 7)], w)
    s.mrect(3, 18, 7, 19, w); s.rect(8, 28, 23, 29, w)
    s.rect(9, 19, 22, 20, (120, 70, 40)); s.rect(15, 19, 16, 20, GOLD)


def _joan(s, p):
    g = (232, 190, 70)
    s.px([(15, 12), (16, 12), (15, 13), (16, 13), (14, 14), (17, 14), (13, 13), (18, 13), (15, 15), (16, 15), (15, 16), (16, 16), (14, 17), (17, 17)], g)
    s.px([(11, 9), (10, 10)], p.g)


rig('breastplate_of_joan', 'breastplate', (226, 230, 238), (150, 160, 190), 'metal', 'streak2', (255, 255, 255), _joan)


def _wallace(s, p):
    blue = (50, 90, 190)
    s.poly([(8, 8), (11, 6), (24, 22), (22, 25)], blue)
    s.line([(12, 10), (20, 20)], WHITE)
    s.px([(15, 13), (17, 13), (15, 15), (17, 15)], WHITE)


rig('brigandine_of_william_wallace', 'studded_leather', (176, 140, 96), (170, 176, 190), 'leather', 'studs', None, _wallace)


def _hydra(s, p):
    s.px([(9, 29), (9, 30), (13, 29), (18, 30), (22, 29), (22, 30), (18, 29)], p.g)
    s.mpoly([(5, 8), (3, 3), (7, 5), (8, 2), (10, 6)], (50, 130, 80))
    s.mpx([(4, 4), (8, 3)], (190, 60, 50))


rig('carapace_of_the_hydra', 'scale', (74, 172, 100), (196, 220, 96), 'scale', 'plain', (150, 255, 90), _hydra)


@named
def cloth_of_penelope(s):
    c, pu, g = (228, 208, 166), (120, 60, 140), (226, 180, 70)
    s.sym([(12, 4), (5, 8), (3, 19), (7, 20), (9, 13), (8, 29)], c)
    s.cell(13, 1, 18, 6)
    for y in (10, 22, 26):
        s.over(c, lambda x, yy: pu if yy == y and 8 < x < 23 else (g if yy == y + 1 and 8 < x < 23 and x % 2 else None))
    for x in range(10, 22, 4):
        s.px([(x, 15), (x + 1, 15), (x + 1, 16), (x + 2, 16), (x + 2, 17)], pu)
    s.mrect(3, 18, 7, 19, pu)
    s.line([(11, 6), (15, 9), (16, 9), (20, 6)], g)
    # the unpicked corner and its loose thread
    s.cpoly([(23, 31), (23, 26), (18, 31)])
    s.line([(22, 26), (25, 28), (24, 30), (27, 30)], pu)


@named
def coat_of_cu_chulainn(s):
    r, d, fur = (182, 46, 46), (120, 26, 36), (70, 50, 44)
    warm = s.lit((255, 170, 70))
    s.sym([(12, 4), (5, 8), (3, 18), (7, 19), (9, 13), (7, 29), (11, 27), (13, 29), (15, 27)], r)
    speck(s, r, d, 7, 2)
    s.rect(15, 6, 16, 28, d)
    s.sym([(12, 3), (8, 5), (11, 9), (15, 8)], fur); s.mpx([(9, 7), (12, 8)], (120, 96, 84))
    s.mrect(3, 17, 7, 19, fur)
    s.rect(9, 18, 22, 19, (60, 40, 36))
    s.ell(12, 9, 16, 13, GOLD); s.px([(14, 11)], r); s.line([(13, 13), (17, 9)], GOLD)
    s.px([(10, 15), (20, 22), (11, 24), (21, 14)], warm)


@named
def cuirass_of_hannibal(s):
    b, d, l = (176, 140, 70), (120, 84, 40), (232, 204, 130)
    s.sym([(12, 5), (9, 4), (7, 8), (8, 13), (8, 21), (15, 23)], b)
    s.cell(12, 1, 19, 7)
    for i, x in enumerate(range(8, 24, 3)):
        s.rect(x, 23, x + 1, 28, (150, 44, 44) if i % 2 else (196, 170, 120))
    s.mline([(9, 12), (12, 14), (14, 13)], d); s.mline([(10, 17), (14, 18)], d); s.line([(15, 9), (15, 20)], d)
    # horse (left) and palm (right)
    s.px([(9, 9), (10, 9), (11, 9), (12, 8), (13, 7), (9, 10), (11, 10), (12, 9)], l)
    s.px([(20, 8), (20, 9), (20, 10), (20, 11), (18, 7), (19, 6), (20, 7), (21, 6), (22, 7), (19, 8), (21, 8)], l)
    s.mrect(9, 2, 10, 4, (110, 72, 44))
    s.rect(8, 21, 23, 22, d)


def _sigurd(s, p):
    for x, y in s.pts(p.b):
        k = h2(x // 2, y // 2, 3) % 7
        if k == 0:
            s.px([(x, y)], (90, 200, 190))
        elif k == 1:
            s.px([(x, y)], (170, 130, 220))
    s.rect(10, 24, 21, 25, GOLD)


rig('dragon_mail_of_sigurd', 'chain_shirt', (104, 164, 84), (226, 190, 80), 'metal', 'plain', (220, 255, 200), _sigurd)


@named
def haramaki_of_yoshitsune(s):
    lac, red, g = (58, 42, 56), (190, 40, 60), (226, 186, 80)
    s.rect(8, 6, 23, 19, lac)
    s.mrect(9, 2, 11, 6, red); s.mpx([(9, 2), (10, 2), (11, 2)], g)
    for y in range(8, 19, 3):
        s.over(lac, lambda x, yy: red if yy == y and x % 2 == 0 else None)
        s.line([(8, y + 1), (23, y + 1)], shade(lac, 1))
    s.rect(8, 5, 23, 6, g)
    for i, x in enumerate((6, 12, 18)):
        s.poly([(x + 2, 20), (x + 6, 20), (x + 7, 28), (x + 1, 28)], lac)
        for y in (22, 25):
            s.px([(x + 2, y), (x + 4, y), (x + 6, y)], red)
        s.line([(x + 1, 28), (x + 7, 28)], g)
    s.rect(8, 19, 23, 19, red)
    s.px([(15, 11), (16, 11), (15, 12), (16, 12)], g)


@named
def hide_of_nemean_lion(s):
    a, mane, cream = (216, 172, 78), (150, 100, 44), (244, 226, 170)
    s.sym([(12, 12), (6, 14), (2, 22), (3, 26), (6, 24), (8, 19), (9, 27), (12, 30), (15, 28)], a)
    s.mpx([(2, 26), (3, 27), (4, 26)], cream)
    s.line([(15, 16), (15, 27)], shade(a, -1)); s.mline([(10, 17), (11, 26)], shade(a, -1))
    s.ell(7, 1, 24, 17, mane)
    for ang in range(0, 360, 30):
        s.px([(int(round(15.5 + 9 * math.cos(math.radians(ang)))), int(round(9 + 8.6 * math.sin(math.radians(ang)))))], mane)
    s.mrect(9, 1, 11, 3, a)
    s.ell(10, 4, 21, 15, a)
    s.ell(13, 9, 18, 14, cream)
    s.mpx([(12, 8), (13, 8)], DARK); s.rect(15, 10, 16, 11, (90, 50, 40)); s.px([(14, 13), (17, 13), (15, 12), (16, 12)], (90, 50, 40))
    s.mpx([(13, 15)], WHITE)


@named
def linothorax_of_alexander(s):
    w, d, red, g = (238, 228, 200), (176, 160, 124), (176, 44, 48), (226, 186, 80)
    s.rect(8, 8, 23, 21, w)
    s.mpoly([(8, 3), (12, 3), (13, 12), (9, 12)], w); s.mrect(8, 3, 12, 4, red)
    s.mpx([(11, 12), (12, 13), (13, 14)], red)
    for x in range(8, 24, 3):
        s.rect(x, 22, x + 1, 28, w); s.px([(x, 28), (x + 1, 28)], red)
    s.rect(8, 16, 23, 17, red); s.rect(8, 21, 23, 21, d)
    s.line([(8, 19), (23, 19)], d)
    s.ell(13, 9, 18, 14, g); s.px([(14, 11), (17, 11)], DARK); s.px([(15, 13), (16, 13)], red)
    s.line([(9, 9), (9, 15)], d)


def _caesar(s, p):
    s.sym([(13, 4), (10, 5), (5, 9), (8, 12), (12, 9), (15, 12)], p.l)
    s.over(p.l, lambda x, y: p.b if (x + y) % 2 else None)
    s.px([(14, 11), (17, 11), (15, 12), (16, 12)], (226, 180, 70))
    s.rect(10, 23, 21, 25, (176, 50, 46)); s.px([(11, 25), (14, 25), (17, 25), (20, 25)], (120, 30, 36))


rig('lorica_hamata_of_caesar', 'chain_shirt', (176, 178, 170), (120, 120, 130), 'metal', 'plain', None, _caesar)


def _orichalcum(s, p):
    for r in (2, 4):
        for a in range(0, 360, 20):
            s.px([(int(round(15.5 + r * math.cos(math.radians(a)))), int(round(15 + r * math.sin(math.radians(a)))))], p.g)


rig('orichalcum_breastplate', 'breastplate', (244, 150, 70), (255, 226, 130), 'metal', 'streak', (255, 232, 150), _orichalcum)


def _hephaestus(s, p):
    s.poly([(15, 2), (13, 0), (18, 0), (20, 3), (17, 2)], (200, 50, 44))
    s.rect(13, 4, 18, 4, p.g); s.px([(15, 12), (16, 12), (15, 13), (16, 13)], p.g)
    s.mpx([(6, 15), (7, 15), (11, 24), (13, 24)], p.g)
    s.mpx([(7, 9), (9, 8)], (255, 244, 200))


rig('panoply_of_hephaestus', 'full_plate', (214, 178, 100), (255, 230, 150), 'metal', 'streak2', (255, 170, 60), _hephaestus)


def _dilmun(s, p):
    verd = (90, 176, 146)
    for x, y in s.pts(p.b, p.d, p.l):
        if (s.get(x + 1, y) is None or s.get(x, y + 1) is None or s.get(x - 1, y) is None) and h2(x, y) % 3:
            s.px([(x, y)], verd)
    s.px([(11, 14), (19, 19), (13, 22)], verd)
    s.px([(15, 7), (16, 7)], (240, 244, 250))


rig('scale_of_dilmun', 'scale', (190, 152, 84), (232, 232, 250), 'metal', 'plain', None, _dilmun)


@named
def serpent_scale_mail(s):
    g, d, l, gold = (60, 160, 100), (30, 96, 70), (140, 220, 150), (226, 190, 80)
    s.sym([(12, 4), (6, 6), (3, 12), (7, 15), (9, 12), (8, 26), (11, 30), (13, 26), (15, 30)], g)
    s.cell(12, 1, 19, 6)

    def f(x, y):
        r = y // 6; xo = (x + 3 * (r % 2)) % 6; yo = y % 6
        if (yo < 4 and xo == 0) or (yo == 4 and xo in (1, 5)) or (yo == 5 and xo in (2, 3, 4)):
            return d
        if yo == 1 and xo in (2, 3):
            return l
    s.over(g, f)
    s.sym([(12, 5), (11, 7), (15, 10)], gold); s.cell(13, 2, 18, 6)
    s.px([(15, 8), (16, 8)], (200, 40, 50))


# =============================================================== the duck
@named
def duck_of_doom(s):
    """A yellow rubber duck. It sits on the head and will not come off."""
    yel, bill = (250, 210, 50), (240, 130, 40)
    s.ell(6, 14, 25, 27, yel)                       # body
    s.poly([(21, 15), (28, 11), (26, 19)], yel)     # tail
    s.ell(7, 5, 18, 16, yel)                        # head
    s.poly([(7, 10), (2, 11), (2, 13), (8, 14)], bill)
    s.px([(11, 9), (11, 10)], (30, 24, 30)); s.px([(12, 8)], (255, 255, 255))
    s.poly([(13, 19), (20, 18), (21, 22), (15, 24)], (236, 184, 36))   # wing
    s.px([(9, 6), (10, 4), (12, 3)], s.lit((255, 70, 50)))             # a doomed glint


# =============================================================== SHIRTS
@named
def hair_shirt_of_becket(s):
    hair, rope = (128, 104, 80), (206, 184, 130)
    s.poly([(10, 6), (13, 5), (15, 7), (17, 7), (19, 5), (22, 6), (27, 11), (24, 14), (22, 12),
            (22, 27), (10, 27), (10, 12), (8, 14), (5, 11)], hair)
    for x, y in s.pts(hair):
        k = (x * 7 + y * 13) % 11
        if k == 0:
            s.px([(x, y)], shade(hair, -1))
        elif k == 5:
            s.px([(x, y)], shade(hair, 1))
    for x in range(10, 23, 2):
        s.px([(x, 28)], shade(hair, -1))
    s.line([(14, 7), (16, 9), (18, 7)], DARK)
    s.line([(10, 20), (22, 20)], rope); s.px([(15, 21), (15, 22), (17, 21), (17, 23), (15, 23)], rope)


def _robe(s, c, wide=True):
    s.sym([(12, 3), (5, 7), (2, 19), (7, 21), (9, 13), (7, 29)], c)
    s.cell(13, 0, 18, 5)


@named
def robe_of_the_magus(s):
    b, sil = (64, 54, 160), (210, 216, 236)
    star = s.lit((255, 255, 230))
    _robe(s, b)
    s.line([(11, 5), (15, 9), (16, 9), (20, 5)], sil); s.rect(15, 9, 16, 29, shade(b, -1))
    s.mrect(2, 18, 7, 20, sil); s.rect(7, 28, 24, 29, sil)
    s.ell(9, 13, 13, 17, sil); s.ell(10, 12, 14, 16, b)                    # crescent
    s.ell(18, 19, 22, 23, shade(b, 1)); s.px([(20, 21)], star)               # an orbit
    s.px([(20, 11), (11, 22), (19, 15), (12, 26), (22, 26), (5, 13), (26, 12)], star)
    s.px([(19, 11), (21, 11), (20, 10), (20, 12)], star)


@named
def robes_of_solomon(s):
    g, d, pu = (226, 186, 56), (150, 104, 30), (110, 50, 140)
    _robe(s, g)
    for y in range(9, 28, 3):
        s.over(g, lambda x, yy: d if yy == y and 8 < x < 23 and (x * 7 + y) % 5 < 3 else None)
    s.rect(8, 18, 23, 20, pu); s.rect(14, 18, 17, 21, (240, 220, 130)); s.px([(15, 19), (16, 20)], pu)
    s.mrect(2, 18, 7, 20, pu); s.line([(11, 5), (15, 9), (16, 9), (20, 5)], pu)
    s.px([(10, 7), (21, 12)], s.lit((255, 250, 200)))


@named
def seamless_tunic(s):
    c, d = (232, 222, 200), (190, 176, 150)
    glow = s.lit((255, 250, 226))
    s.sym([(13, 4), (10, 4), (4, 9), (7, 13), (9, 11), (8, 29)], c)
    s.cell(13, 1, 18, 6)
    s.line([(12, 12), (11, 28)], d); s.line([(19, 12), (21, 28)], d); s.line([(15, 16), (16, 28)], d)
    s.line([(8, 29), (23, 29)], d)
    s.px([(14, 9), (20, 20)], glow)


@named
def shirt_of_aslaug(s):
    c, d, l = (150, 150, 168), (104, 104, 126), (206, 206, 222)
    glint = s.lit((236, 240, 255))
    s.sym([(15, 7), (13, 5), (10, 6), (4, 12), (4, 20), (7, 20), (9, 14), (10, 27)], c)
    s.over(c, lambda x, y: l if (x + 3 * y) % 7 == 0 else (d if (x * 3 + y) % 11 == 0 else None))
    s.line([(13, 5), (15, 7), (16, 7), (18, 5)], d)
    s.mrect(4, 19, 7, 20, d); s.rect(10, 26, 21, 27, d)
    s.px([(12, 11), (19, 17), (13, 22)], glint)
    # a turned blade's scratch that did not cut
    s.line([(17, 10), (21, 14)], l)


# =============================================================== CLOAKS
def _cloak(s, c, d, collar=None, hem=None):
    s.sym(hem or [(10, 6), (6, 12), (3, 26), (6, 28), (9, 26), (12, 29), (15, 27)], c)
    for a, b_ in (((11, 9), (8, 26)), ((14, 9), (13, 27)), ((18, 9), (19, 27)), ((21, 10), (24, 26))):
        s.line([a, b_], d)
    s.sym([(11, 3), (8, 7), (12, 9), (15, 8)], collar or d)


@named
def anansi_web_cloak(s):
    g, d, web = (226, 180, 44), (160, 110, 24), (255, 240, 170)
    _cloak(s, g, d)
    snap = s.img.copy()
    cx, cy = 16, 17
    for a in range(0, 360, 45):
        s.line([(cx, cy), (cx + 16 * math.cos(math.radians(a + 22)), cy + 16 * math.sin(math.radians(a + 22)))], web)
    for r in (4, 8, 12):
        s.line([(cx + r * math.cos(math.radians(a + 22)), cy + r * math.sin(math.radians(a + 22))) for a in range(0, 361, 45)], web)
    for x in range(32):          # keep the web on the cloth only
        for y in range(32):
            if snap.getpixel((x, y))[3] == 0:
                s.img.putpixel((x, y), (0, 0, 0, 0))
    s.ell(13, 4, 18, 8, d)
    s.rect(15, 15, 16, 17, (30, 24, 30)); s.px([(14, 14), (17, 14), (13, 16), (18, 16), (14, 18), (17, 18), (13, 15), (18, 15)], (30, 24, 30))


@named
def arachne_silk_cloak(s):
    c, d, pu, g = (226, 226, 240), (176, 178, 204), (130, 70, 150), (226, 186, 80)
    _cloak(s, c, d, collar=(190, 192, 220))
    s.line([(8, 12), (5, 24)], WHITE); s.line([(16, 10), (16, 25)], WHITE)
    for x, y in s.pts(c, d, WHITE):
        if s.get(x, y + 2) is None or s.get(x, y + 1) is None:
            s.px([(x, y)], pu if x % 2 else g)
        elif s.get(x, y + 3) is None and x % 3 == 0:
            s.px([(x, y)], pu)
    s.ell(13, 4, 18, 8, g); s.px([(15, 6)], pu)
    s.line([(22, 12), (22, 18)], (150, 150, 170))                       # a spider on a thread
    s.rect(21, 19, 23, 21, (40, 30, 44)); s.px([(20, 18), (24, 18), (20, 20), (24, 20), (20, 22), (24, 22)], (40, 30, 44))


@named
def cloak_of_mulan(s):
    r, d, frost, fur = (166, 56, 66), (110, 30, 46), (236, 240, 250), (240, 236, 226)
    _cloak(s, r, d)
    for bx in (7, 13, 19, 24):
        s.line([(bx, 25), (bx, 20)], frost); s.px([(bx - 1, 22), (bx + 1, 21), (bx - 1, 19), (bx + 1, 18)], frost)
    s.sym([(11, 2), (7, 6), (11, 9), (15, 8)], fur); s.mpx([(9, 5), (12, 7)], (200, 192, 180))
    s.ell(14, 5, 17, 8, (250, 170, 190)); s.px([(15, 6)], s.lit((255, 240, 200)))


@named
def cloak_of_odin(s):
    b, d = (70, 74, 132), (42, 44, 90)
    eye = s.lit((170, 220, 255))
    s.sym([(10, 10), (6, 14), (3, 27), (7, 29), (10, 27), (13, 29), (15, 27)], b)
    s.poly([(16, 1), (20, 2), (23, 6), (24, 12), (20, 14), (11, 14), (7, 12), (8, 6), (11, 2)], b)
    s.ell(11, 5, 20, 14, (20, 20, 36))
    s.px([(13, 9), (14, 9)], eye)
    for a, b_ in (((10, 15), (7, 27)), ((14, 15), (13, 27)), ((18, 15), (19, 27)), ((22, 15), (25, 27))):
        s.line([a, b_], d)
    s.line([(9, 4), (11, 2)], shade(b, 1))
    for x in (9, 12, 18, 21):                      # eyelets; one is missing
        s.px([(x, 16)], (200, 200, 216))
    s.rect(14, 14, 17, 16, (120, 124, 140))


@named
def cloak_of_sun_wukong(s):
    g, d, red = (252, 190, 44), (196, 124, 20), (200, 40, 44)
    shim = s.lit((255, 250, 190))
    _cloak(s, g, d, collar=red)
    for cx, cy in ((9, 20), (20, 16), (16, 24)):
        s.line([(cx - 2, cy), (cx - 1, cy - 2), (cx + 1, cy - 2), (cx + 2, cy), (cx, cy + 1), (cx, cy - 1)], (255, 240, 200))
    for x, y in s.pts(g, d):
        if s.get(x, y + 1) is None:
            s.px([(x, y)], red)
    s.ell(13, 4, 18, 8, (255, 220, 90)); s.px([(15, 6)], red)
    s.px([(7, 14), (23, 22), (13, 13)], shim)


@named
def cloak_of_the_morrigan(s):
    b, d, v, bone = (58, 40, 74), (34, 24, 46), (130, 90, 190), (232, 226, 204)
    s.sym([(10, 6), (5, 12), (2, 24), (4, 28), (6, 24), (8, 29), (10, 25), (12, 30), (14, 26), (15, 29)], b)

    def f(x, y):
        r = y // 4; xo = (x + 2 * (r % 2)) % 4; yo = y % 4
        if yo == 3 and xo in (1, 3) or (yo < 3 and xo == 0):
            return d
        if yo == 0 and xo == 2:
            return v
    s.over(b, f)
    s.sym([(11, 3), (7, 7), (12, 9), (15, 8)], d)
    s.poly([(14, 4), (17, 4), (18, 7), (16, 10), (15, 10), (13, 7)], bone); s.px([(14, 6), (17, 6)], DARK)
    s.px([(15, 10), (16, 11)], (150, 140, 120))


@named
def erlking_mantle(s):
    g, d, twig, leaf = (72, 110, 86), (40, 70, 60), (110, 76, 50), (120, 170, 90)
    mist = s.lit((200, 240, 226))
    s.sym([(10, 6), (5, 12), (2, 23), (4, 28), (7, 24), (9, 29), (11, 25), (13, 30), (15, 26)], g)
    for a, b_ in (((11, 9), (7, 24)), ((14, 9), (13, 27)), ((18, 9), (19, 27)), ((21, 10), (25, 24))):
        s.line([a, b_], d)
    for x, y in ((8, 16), (22, 14), (16, 20), (11, 22), (21, 22)):
        s.px([(x, y), (x + 1, y - 1), (x + 1, y)], shade(g, 1))
    s.line([(6, 7), (10, 4), (15, 5), (16, 5), (21, 4), (25, 7)], twig, 2)
    s.px([(5, 5), (8, 3), (12, 2), (19, 2), (23, 3), (26, 5), (15, 3)], leaf)
    s.px([(7, 4), (24, 4), (11, 3), (20, 3)], twig)
    s.px([(4, 18), (27, 20), (13, 15), (19, 24)], mist)


@named
def falcon_cloak_of_freyja(s):
    brown, bar, tip = (154, 114, 72), (96, 66, 42), (236, 218, 172)
    s.poly([(16, 4), (22, 6), (28, 13), (29, 22), (27, 27), (24, 23), (22, 25), (19, 23), (16, 30), (15, 30),
            (12, 23), (9, 25), (7, 23), (4, 27), (2, 22), (3, 13), (9, 6), (15, 4)], brown)
    for y in (10, 15, 20):
        for x in range(2, 30):
            if s.get(x, y) and (x + y) % 3:
                s.px([(x, y)], bar)
            if s.get(x, y + 1) and (x + y) % 3 == 0:
                s.px([(x, y + 1)], tip)
    for x, y in s.pts(brown, bar):
        if s.get(x, y + 1) is None and y > 20:
            s.px([(x, y)], tip)
    s.line([(15, 8), (15, 28)], bar); s.line([(16, 8), (16, 28)], shade(brown, 1))
    s.ell(13, 3, 18, 8, GOLD); s.px([(15, 5), (16, 5)], s.lit((120, 220, 255)))


@named
def half_cloak_of_martin(s):
    red, fold, fray = (180, 44, 44), (120, 26, 34), (236, 156, 136)
    s.poly([(8, 5), (22, 5), (26, 9), (26, 13), (8, 29), (5, 11)], red)
    for x in (9, 12, 16, 20):
        s.line([(x, 8), (x - 1, 8 + max(2, 36 - 2 * x))], fold)
    for x, y in s.pts(red, fold):                      # the clean cut edge
        if s.get(x + 1, y) is None and y > 12:
            s.px([(x, y)], fray if (x + y) % 2 else WHITE)
    s.line([(22, 20), (25, 23)], (200, 204, 216)); s.px([(26, 24), (27, 25)], (120, 84, 50))   # the blade that cut it
    s.rect(13, 3, 18, 6, GOLD); s.px([(15, 4), (16, 4)], (250, 240, 200))


@named
def mantle_of_elijah(s):
    c, d, l = (170, 132, 92), (112, 82, 58), (212, 180, 136)
    fire = s.lit((255, 170, 60)); f2 = s.lit((255, 236, 140))
    s.sym([(11, 4), (6, 10), (3, 26), (15, 27)], c)
    speck(s, c, d, 5, 1); speck(s, c, l, 7, 2)
    for a, b_ in (((11, 9), (8, 26)), ((14, 8), (13, 26)), ((18, 8), (19, 26)), ((21, 9), (24, 26))):
        s.line([a, b_], d)
    for x in range(3, 29, 2):
        s.px([(x, 28), (x, 29)], l)
    s.sym([(11, 3), (8, 7), (13, 8), (15, 6)], d)
    s.line([(13, 7), (15, 10), (17, 7)], l); s.px([(14, 11), (17, 11), (15, 12)], l)     # a plain knot, no clasp
    s.px([(25, 4), (27, 2), (28, 6), (24, 1)], fire); s.px([(26, 4)], f2)


@named
def mantle_of_muspelheim(s):
    c, d = (96, 40, 36), (56, 22, 28)
    e1 = s.lit((255, 110, 30)); e2 = s.lit((255, 200, 70))
    s.sym([(10, 6), (6, 12), (3, 24), (5, 29), (7, 25), (9, 30), (11, 25), (13, 30), (15, 26)], c)
    for a, b_ in (((11, 9), (8, 22)), ((14, 9), (13, 22)), ((18, 9), (19, 22)), ((21, 10), (24, 22))):
        s.line([a, b_], d)
    for x, y in s.pts(c, d):
        if y >= 26 or (y >= 23 and (x + y) % 2 == 0) or (y >= 21 and h2(x, y) % 4 == 0):
            s.px([(x, y)], e2 if y >= 27 else e1)
    s.sym([(11, 3), (8, 7), (12, 9), (15, 8)], d)
    s.ell(13, 4, 18, 8, (60, 50, 56)); s.px([(15, 6), (16, 6)], e2)
    s.px([(8, 17), (22, 15)], e1)


@named
def nidhoggr_scale(s):
    g, d, l = (34, 104, 62), (16, 60, 46), (96, 190, 110)
    venom = s.lit((170, 255, 90))
    s.poly([(4, 3), (27, 3), (29, 9), (27, 18), (21, 26), (16, 30), (15, 30), (10, 26), (4, 18), (2, 9)], g)
    for k, y0 in enumerate((8, 13, 18, 23)):
        w = 12 - k * 3
        s.line([(15.5 - w, y0 - 3), (15.5 - w * 0.6, y0), (15.5, y0 + 1), (15.5 + w * 0.6, y0), (15.5 + w, y0 - 3)], d)
    s.line([(6, 5), (25, 5)], l); s.line([(5, 7), (8, 6)], l); s.line([(6, 10), (9, 15)], l)
    s.rect(4, 3, 27, 3, d)
    s.cpoly([(1, 12), (6, 14), (2, 17)])                # gnawed
    s.px([(14, 30), (17, 29), (13, 28)], venom); s.px([(22, 12), (20, 19)], l)


# =============================================================== LEGS
@named
def breeches_of_ragnar(s):
    c, d, l, tar = (72, 58, 46), (40, 32, 30), (120, 98, 76), (20, 18, 24)
    s.poly([(8, 4), (23, 4), (25, 14), (23, 28), (17, 28), (16, 13), (15, 13), (14, 28), (8, 28), (6, 14)], c)
    for x, y in s.pts(c):
        k = h2(x, y, 2) % 6
        if k == 0:
            s.px([(x, y)], l)
        elif k in (1, 2) and y % 2:
            s.px([(x, y)], d)
    for x, y in s.pts(c, d, l):
        if (s.get(x, y + 1) is None or s.get(x - 1, y) is None or s.get(x + 1, y) is None) and (x + y) % 2:
            s.px([(x, y)], l)
    s.rect(8, 4, 23, 5, (176, 150, 100)); s.px([(15, 6), (15, 7), (17, 6), (17, 8)], (176, 150, 100))
    s.line([(10, 12), (10, 16)], tar); s.line([(20, 18), (20, 23)], tar); s.px([(12, 22), (12, 23), (19, 10), (10, 17), (20, 24)], tar)
    s.px([(11, 13), (21, 19)], (150, 150, 170))


def _belt_loop(s, c, d):
    s.ell(3, 8, 28, 22, c); s.cell(6, 11, 25, 19)
    s.ell(5, 10, 26, 13, d); s.cell(6, 11, 25, 19)
    s.ell(3, 8, 28, 22, c) if False else None


@named
def girdle_of_hippolyta(s):
    c, d, br = (204, 104, 124), (140, 60, 84), (226, 180, 80)
    s.ell(3, 7, 28, 21, d); s.ell(3, 9, 28, 23, c); s.cell(7, 9, 24, 17)
    s.ell(6, 8, 25, 12, d); s.cell(8, 9, 23, 12) if False else None
    for x, y in s.pts(c):
        if (x + y) % 3 == 0:
            s.px([(x, y)], shade(c, 1))
        elif (x - y) % 3 == 0:
            s.px([(x, y)], d)
    for x in (8, 12, 19, 23):
        s.rect(x, 22 - (1 if x in (8, 23) else 0), x + 1, 27, c); s.px([(x, 28), (x + 1, 28)], br)
    s.ell(12, 16, 19, 24, br); s.ell(14, 18, 17, 22, shade(br, -1)); s.px([(15, 19)], (255, 240, 190))


@named
def greaves_of_goliath(s):
    bronze, strap, hi = (198, 142, 66), (90, 56, 36), (238, 196, 116)
    for ox in (0, 13):
        s.poly([(5 + ox, 6), (13 + ox, 6), (13 + ox, 25), (15 + ox, 29), (3 + ox, 29), (5 + ox, 25)], bronze)
        s.ell(4 + ox, 1, 14 + ox, 10, bronze)
        s.rect(8 + ox, 3, 9 + ox, 27, hi)
        s.line([(5 + ox, 14), (13 + ox, 14)], strap); s.line([(5 + ox, 21), (13 + ox, 21)], strap)
        s.px([(6 + ox, 14), (12 + ox, 21)], GOLD)
        s.px([(6 + ox, 5), (11 + ox, 5)], (120, 80, 40))
        s.line([(3 + ox, 29), (15 + ox, 29)], (140, 96, 44))


@named
def greaves_of_qin(s):
    c, d, red = (136, 92, 60), (86, 54, 40), (200, 50, 44)
    for ox in (0, 14):
        s.poly([(4 + ox, 4), (13 + ox, 4), (13 + ox, 26), (11 + ox, 28), (6 + ox, 28), (4 + ox, 26)], c)
        for y in range(8, 27, 4):
            s.line([(4 + ox, y), (13 + ox, y)], d)
        for x in (7, 10):
            s.line([(x + ox, 5), (x + ox, 27)], d)
        for y in range(6, 27, 4):
            s.px([(5 + ox, y), (8 + ox, y), (11 + ox, y)], red)
        s.rect(4 + ox, 3, 13 + ox, 4, (40, 34, 40))
        s.px([(6 + ox, 3), (11 + ox, 3)], GOLD)


@named
def green_girdle(s):
    g, d, gold = (70, 172, 84), (36, 110, 60), (236, 196, 80)
    s.ell(3, 5, 28, 17, d); s.ell(3, 7, 28, 19, g); s.cell(7, 7, 24, 14)
    for x, y in s.pts(g):
        if (x + 2 * y) % 5 == 0:
            s.px([(x, y)], gold)
    s.poly([(13, 17), (11, 27), (14, 28), (16, 19)], g); s.poly([(17, 17), (21, 26), (18, 28), (15, 19)], g)
    s.line([(13, 20), (12, 26)], gold); s.line([(18, 20), (19, 26)], gold)
    s.px([(11, 28), (12, 29), (13, 28), (19, 28), (20, 29), (21, 27)], gold)
    s.ell(13, 14, 18, 19, d); s.px([(15, 16), (16, 16)], gold)


@named
def kilt_of_the_pharaoh(s):
    w, d, gold, blue = (244, 234, 196), (196, 176, 130), (232, 190, 70), (44, 86, 186)
    s.poly([(7, 6), (24, 6), (27, 26), (16, 28), (4, 26)], w)
    for x in range(6, 27, 2):
        s.line([(8 + (x - 6) * 15 // 20, 9), (x, 26)], d)
    s.rect(7, 5, 24, 8, gold); s.px([(9, 6), (9, 7), (13, 6), (13, 7), (18, 6), (18, 7), (22, 6), (22, 7)], blue)
    s.poly([(13, 9), (18, 9), (20, 24), (16, 27), (15, 27), (11, 24)], gold)
    for y in (12, 16, 20):
        s.line([(13 - (y - 9) // 6, y), (18 + (y - 9) // 6, y)], blue)
    s.px([(15, 24), (16, 24)], (200, 40, 50))
    s.px([(5, 22), (25, 14)], s.lit((255, 244, 170)))


@named
def leggings_of_enkidu(s):
    c, d, sinew, fur = (146, 118, 78), (96, 74, 50), (236, 222, 180), (96, 70, 46)
    for ox, sk in ((0, -1), (14, 1)):
        s.poly([(4 + ox, 5), (14 + ox, 5), (13 + ox, 27), (10 + ox, 29), (6 + ox, 28), (5 + ox, 20)], c)
        for y in range(8, 27, 3):
            x = 9 + ox
            s.px([(x - 1, y), (x + 1, y), (x, y + 1), (x - 1, y + 2), (x + 1, y + 2)], sinew)
        s.rect(3 + ox, 4, 14 + ox, 6, fur)
        for x in range(3 + ox, 15 + ox, 2):
            s.px([(x, 7), (x + 1, 3)], fur)
    speck(s, c, d, 6, 3)
    s.px([(6, 16), (22, 21), (25, 12)], d)


# =============================================================== FEET
def _sandal(s, ox, oy, sole, strap, stud=None, high=False, buckle=None):
    s.poly([(ox, oy + 23), (ox + 14, oy + 23), (ox + 16, oy + 24), (ox + 15, oy + 26), (ox, oy + 26)], sole)
    s.line([(ox, oy + 26), (ox + 15, oy + 26)], shade(sole, -2))
    s.rect(ox, oy + 14, ox + 1, oy + 22, strap)                                      # heel cup
    s.rect(ox, oy + 14, ox + 7, oy + 15, strap)                                      # ankle strap
    s.line([(ox + 7, oy + 15), (ox + 12, oy + 22)], strap, 2)                        # instep
    s.line([(ox + 2, oy + 18), (ox + 9, oy + 22)], strap)
    s.rect(ox + 12, oy + 20, ox + 13, oy + 22, strap)                                # toe strap
    if high:
        for y in (10, 6):
            s.rect(ox, oy + y, ox + 6, oy + y, strap)
            s.line([(ox, oy + y + 1), (ox + 6, oy + y + 3)], strap)
    if stud:
        s.px([(ox + 1, oy + 14), (ox + 4, oy + 14), (ox + 7, oy + 15), (ox + 9, oy + 18), (ox + 11, oy + 21), (ox + 1, oy + 19), (ox + 13, oy + 21)], stud)
    if buckle:
        s.rect(ox + 6, oy + 13, ox + 7, oy + 16, buckle)


@named
def winged_sandals_of_hermes(s):
    g, d = (244, 200, 50), (176, 124, 24)
    f = s.lit((255, 255, 240))
    for ox, oy in ((13, -8), (4, 3)):
        wing(s, ox + 1, oy + 13, -1, WHITE, 0.8) if oy > 0 else wing(s, ox + 1, oy + 12, -1, WHITE, 1)
        _sandal(s, ox, oy, d, g, buckle=(255, 240, 150))
        s.px([(ox + 17, oy + 19)], f)


@named
def hermes_sandals_early(s):
    tan, strap, br = (176, 140, 96), (206, 180, 140), (200, 150, 70)
    for ox, oy in ((13, -8), (2, 3)):
        _sandal(s, ox, oy, (120, 84, 54), strap)
        s.poly([(ox + 1, oy + 13), (ox - 1, oy + 8), (ox + 2, oy + 10), (ox + 4, oy + 8), (ox + 5, oy + 13)], br)
        s.px([(ox + 3, oy + 13)], (110, 112, 124))


@named
def sandals_of_perseus(s):
    rope, strap, br = (206, 180, 120), (150, 104, 60), (214, 164, 70)
    for ox, oy in ((13, -8), (2, 3)):
        _sandal(s, ox, oy, rope, strap, buckle=br)
        for x in range(ox + 1, ox + 15, 2):
            s.px([(x, oy + 24)], (150, 124, 76))
        s.line([(ox + 2, oy + 20), (ox + 9, oy + 17)], strap); s.px([(ox + 12, oy + 20)], br)


@named
def sandals_of_theseus(s):
    sole, strap, br = (104, 70, 44), (170, 124, 76), (226, 176, 80)
    for ox, oy in ((13, -8), (2, 3)):
        _sandal(s, ox, oy, sole, strap, stud=br, high=True)
        s.px([(ox + 3, oy + 7), (ox + 4, oy + 11)], br)


def _seven(s, p):
    f = s.lit((255, 244, 180))
    for y in (12, 17, 22):
        s.line([(0, y + 1), (1, y + 1)], f)
    s.px([(1, 8), (12, 6), (29, 9)], f)
    s.rect(5, 16, 7, 18, p.d); s.px([(5, 16), (7, 18)], (226, 206, 160))
    s.px([(11, 26), (12, 27)], p.dark)


rig('boots_of_seven_leagues', 'leather_boots', (166, 104, 58), (96, 60, 36), 'leather', 'stitch', None, _seven)


def _thor(s, p):
    bolt = s.lit((150, 220, 255)); core = s.lit((250, 250, 210))
    s.line([(5, 1), (8, 5), (6, 6), (9, 10)], bolt); s.px([(8, 5), (6, 6)], core)
    s.line([(24, 0), (22, 4), (25, 5), (23, 8)], bolt); s.px([(22, 4)], core)
    s.px([(6, 17), (7, 18), (6, 19), (20, 14), (19, 15)], bolt)


rig('boots_of_thor', 'iron_boots', (104, 106, 122), (60, 62, 78), 'metal', 'dull', None, _thor)


def _hermes_greaves(s, p):
    for d, x in ((-1, 5), (1, 26)):
        wing(s, x, 23, d, WHITE, 0.8)


def _hermes_pre(s, p):
    for d, x in ((-1, 6), (1, 25)):
        wing(s, x, 22, d, WHITE, 1)


rig('greaves_of_hermes', 'plate_greaves', (204, 196, 120), (255, 255, 255), 'metal', 'streak', (255, 255, 230), None, pre=_hermes_pre)


# =============================================================== ARMS
def _arjuna(s, p):
    brass = (236, 196, 80)
    for ox in (0, 14):
        s.px([(5 + ox, 9), (12 + ox, 9), (5 + ox, 22), (11 + ox, 22), (5 + ox, 15), (12 + ox, 15)], brass)
        s.line([(6 + ox, 11), (4 + ox, 15), (6 + ox, 20)], brass)        # a little bow


rig('bracers_of_arjuna', 'leather_bracers', (186, 142, 88), (110, 74, 44), 'leather', 'plain', None, _arjuna)


def _atalanta(s, p):
    vine, apple = (70, 140, 70), s.lit((255, 214, 70))
    for ox in (0, 14):
        s.line([(4 + ox, 10), (9 + ox, 13), (12 + ox, 17), (6 + ox, 21), (11 + ox, 24)], vine)
        s.px([(5 + ox, 9), (10 + ox, 12), (11 + ox, 18), (7 + ox, 22)], (40, 96, 50))
        s.px([(6 + ox, 13), (11 + ox, 21)], (226, 206, 170))
    s.rect(21, 14, 22, 15, apple)


rig('bracers_of_atalanta', 'leather_bracers', (176, 146, 98), (110, 84, 54), 'leather', 'plain', None, _atalanta)


def _cu(s, p):
    cut, br = (236, 200, 170), (226, 170, 70)
    for ox in (0, 14):
        s.line([(5 + ox, 10), (9 + ox, 14)], cut); s.line([(8 + ox, 17), (12 + ox, 21)], cut); s.line([(11 + ox, 9), (12 + ox, 12)], cut)
        s.rect(3 + ox, 5, 14 + ox, 6, br); s.rect(5 + ox, 25, 12 + ox, 26, br)
    s.px([(6, 19), (20, 12)], (150, 30, 36))


rig('bracers_of_cu_chulainn', 'leather_bracers', (128, 64, 40), (70, 36, 28), 'leather', 'plain', None, _cu)


def _achilles_v(s, p):
    sil, gold = (240, 244, 250), (255, 236, 150)
    for m in (0, 1):
        f = (lambda x: x) if not m else (lambda x: 31 - x)
        s.px([(f(6), 12), (f(7), 12), (f(8), 12), (f(8), 11), (f(6), 13), (f(8), 13)], sil)   # an ox
        s.px([(f(9), 17), (f(10), 17), (f(10), 16), (f(11), 18)], gold)                         # a plough
        s.px([(f(10), 20), (f(11), 20), (f(12), 20)], sil)
    s.mline([(3, 8), (11, 6)], (140, 100, 44))


rig('vambraces_of_achilles', 'iron_vambraces', (212, 190, 110), (150, 110, 50), 'metal', 'streak', (255, 250, 210), _achilles_v)


def _roland(s, p):
    for m in (0, 1):
        f = (lambda x: x) if not m else (lambda x: 31 - x)
        s.rect(min(f(8), f(9)), 13, max(f(8), f(9)), 19, RED)
        s.rect(min(f(6), f(11)), 15, max(f(6), f(11)), 16, RED)
    s.px([(5, 11), (12, 21), (25, 10), (20, 22), (10, 23)], p.dd)
    s.px([(6, 11), (26, 10)], p.l)


rig('vambraces_of_roland', 'steel_vambraces', (184, 186, 204), (110, 114, 140), 'metal', 'streak', None, _roland)


@named
def vambraces_of_the_first_winter(s):
    ice, d, l = (150, 204, 238), (84, 140, 204), (226, 244, 255)
    g = s.lit((240, 252, 255))
    s.mpoly([(2, 5), (6, 2), (11, 3), (14, 24), (12, 26), (9, 25)], ice)
    s.mpoly([(9, 25), (10, 30), (11, 26)], l); s.mpoly([(12, 25), (13, 29), (14, 24)], l); s.mpoly([(5, 14), (4, 19), (7, 17)], l)
    s.mline([(6, 3), (9, 12), (11, 24)], l); s.mline([(3, 6), (9, 12)], d); s.mline([(9, 12), (13, 14)], d)
    s.mline([(7, 18), (12, 19)], d)
    s.mpx([(5, 5), (10, 16), (8, 22)], g)
    s.px([(15, 8), (16, 12), (1, 22), (30, 26)], g)


# =============================================================== HANDS
@named
def jarngreipr_gauntlets(s):
    iron, dk = (114, 116, 134), (72, 74, 92)
    spark = s.lit((150, 220, 255)); core = s.lit((250, 250, 200))
    s.poly([(10, 20), (22, 20), (24, 28), (8, 28)], dk)
    s.line([(9, 20), (23, 20)], STEEL); s.line([(8, 28), (24, 28)], STEEL)
    s.px([(11, 24), (15, 24), (19, 24), (13, 26), (17, 26), (21, 26)], STEEL)
    s.rect(9, 10, 22, 19, iron)
    for x0, y0 in ((9, 5), (12, 3), (16, 3), (19, 5)):
        s.rect(x0, y0, x0 + 2, 10, iron)
    s.line([(9, 10), (22, 10)], STEEL); s.line([(9, 14), (22, 14)], dk)
    s.poly([(22, 12), (26, 10), (27, 13), (23, 17)], iron)
    s.px([(14, 16), (15, 17), (16, 16), (17, 17)], dk)
    s.line([(4, 4), (6, 8), (5, 10), (7, 13)], spark); s.px([(6, 8), (5, 10)], core)
    s.line([(26, 1), (28, 5), (27, 7)], spark); s.px([(28, 5)], core)
    s.px([(3, 16), (29, 18)], spark)


@named
def cestus_of_polydeuces(s):
    hide, d, l, skin = (156, 104, 60), (96, 60, 36), (206, 160, 110), (226, 180, 140)
    s.rect(9, 8, 22, 20, skin)                       # a wrapped fist
    for x in (9, 13, 17):
        s.rect(x, 5, x + 3, 9, skin)
    s.rect(21, 6, 23, 9, skin)
    s.poly([(22, 12), (26, 11), (27, 15), (23, 19)], skin)
    s.rect(10, 20, 21, 28, skin)
    s.rect(8, 9, 23, 13, hide); s.line([(8, 11), (23, 11)], d); s.px([(10, 9), (14, 9), (18, 9), (22, 9)], l)
    for y in (15, 18, 21, 24):
        s.line([(9, y + 2), (22, y)], hide, 2)
    s.line([(9, 16), (22, 20)], d); s.line([(10, 22), (21, 26)], d)
    s.rect(10, 26, 21, 28, hide); s.line([(10, 27), (21, 27)], d)
    s.line([(10, 28), (6, 30), (3, 27)], hide)       # the loose end
    s.px([(11, 6), (15, 6), (19, 6)], (200, 150, 120))


def _mars(s, p):
    w = (236, 220, 200)
    s.poly([(13, 22), (14, 24), (17, 24), (18, 22), (17, 27), (14, 27)], w)      # wolf head on the cuff
    s.px([(13, 21), (18, 21)], w); s.px([(14, 25), (17, 25)], DARK); s.px([(15, 27), (16, 27)], DARK)
    s.line([(9, 10), (22, 10)], (226, 180, 80))


rig('gauntlets_of_mars', 'plate_gauntlets', (166, 84, 62), (226, 180, 80), 'metal', 'streak', None, _mars)


@named
def glove_of_tyr(s):
    p = pal(s, (118, 132, 160), (70, 80, 110), 'leather', 'stitch')
    # a LEFT glove: thumb on the right when seen from the back is a right hand, so mirror it
    for x, top in ((22, 7), (18, 4), (14, 3), (10, 6)):
        s.rect(x, top, x + 2, 14, p.b)
    s.rect(10, 13, 24, 22, p.b)
    s.poly([(10, 15), (6, 11), (4, 13), (9, 21)], p.b)
    surface(s, p)
    s.poly([(11, 22), (23, 22), (25, 28), (9, 28)], p.d)
    # the wolf's bite at the wrist
    tooth = (236, 232, 220)
    for x in (10, 13, 16, 19, 22):
        s.px([(x, 22), (x + 1, 23)], tooth)
    s.px([(11, 26), (14, 27), (17, 26), (20, 27), (23, 26)], tooth)
    s.px([(12, 24), (18, 24), (21, 25)], (150, 40, 46))
    s.px([(15, 17), (16, 16), (17, 17), (16, 18), (16, 19)], p.dd)


def _wayland(s, p):
    soot = (30, 26, 30); em = s.lit((255, 150, 50))
    for x, top in ((7, 7), (11, 4), (15, 3), (19, 6)):
        s.rect(x, top, x + 2, top + 3, soot)
    s.px([(8, 11), (12, 8), (16, 7), (20, 10), (26, 12)], soot)
    s.rect(10, 16, 18, 20, p.dd); s.px([(10, 16), (18, 16), (10, 20), (18, 20)], (176, 150, 110))
    s.px([(12, 5), (20, 8), (8, 9)], em)
    s.px([(25, 4), (4, 12), (27, 8)], em)


rig('gloves_of_wayland', 'leather_gloves', (104, 80, 62), (60, 44, 36), 'leather', 'stitch', None, _wayland)


# =============================================================== STRAYS
def stray(name, tpl, base, trim, cls='metal', fx='streak', glow=None, extra=None):
    rig(name, tpl, base, trim, cls, fx, glow, extra, table=STRAY)


def x_mail(s, p): mail(s, p, [p.b, p.l])
def x_quilt(s, p): quilt(s, p, [p.b, p.l])
def x_scale(s, p): big_scales(s, p, [p.b, p.l])


def x_spikes(s, p):
    s.mpoly([(4, 9), (2, 3), (7, 6)], p.t); s.mpoly([(8, 5), (9, 1), (11, 5)], p.t)


def dragon(extra2=None):
    def f(s, p):
        x_spikes(s, p)
        if extra2:
            extra2(s, p)
    return f


def x_runes(c):
    def f(s, p):
        s.px([(12, 10), (12, 11), (13, 12), (19, 10), (18, 11), (19, 12), (15, 15), (16, 16), (15, 17)], p.g)
    return f


def x_eyes(s, p):
    s.px([(12, 12), (13, 12), (18, 12), (19, 12)], p.g); s.px([(11, 11), (20, 11)], p.dd)
    s.line([(12, 17), (14, 18), (17, 18), (19, 17)], (236, 232, 214))


def x_fur_collar(s, p):
    fur = p.t
    s.sym([(11, 2), (6, 6), (9, 10), (15, 9)], fur)
    for x in range(6, 26, 2):
        s.px([(x, 10 if 9 < x < 22 else 8)], fur)


def x_rings(s, p):
    for cy in range(11, 26, 5):
        for cx in range(6, 25, 5):
            ring = [(cx + 1, cy), (cx + 2, cy), (cx, cy + 1), (cx + 3, cy + 1), (cx + 1, cy + 2), (cx + 2, cy + 2)]
            if all(s.get(x, y) in (p.b, p.d, p.l) for x, y in ring):
                s.px(ring, p.t)


S_ = (176, 182, 196)
stray('armet', 'plate_helm', (188, 194, 208), (60, 90, 190), 'metal', 'streak2')
stray('banded_mail', 'banded', (150, 152, 160), (90, 90, 100), 'metal', 'streak')
stray('brigandine', 'studded_leather', (124, 50, 54), (196, 200, 210), 'cloth', 'studs')
stray('chain_boots', 'leather_boots', S_, (100, 104, 120), 'metal', 'plain', None, x_mail)
stray('chain_bracers', 'leather_bracers', S_, (100, 104, 120), 'metal', 'plain', None, x_mail)
stray('chain_gauntlets', 'leather_gloves', S_, (100, 104, 120), 'metal', 'plain', None, x_mail)
stray('chain_leggings', 'chain_chausses', S_, (100, 104, 120), 'metal', 'plain')
stray('chain_mail', 'chainmail', (150, 154, 166), (90, 94, 110), 'metal', 'plain')
stray('chain_shirt', 'chain_shirt', S_, (100, 104, 120), 'metal', 'plain')
stray('hauberk', 'chainmail', (190, 196, 210), (226, 180, 70), 'metal', 'streak')
stray('cloth_armor', 'padded', (190, 176, 150), (120, 96, 70), 'cloth', 'weave')
stray('cloth_cloak', 'cloak', (120, 132, 160), (70, 80, 110), 'cloth', 'weave')
stray('cloth_gloves', 'leather_gloves', (214, 204, 180), (140, 110, 80), 'cloth', 'weave')
stray('cloth_leggings', 'cloth_leggings', (176, 164, 140), (110, 88, 64), 'cloth', 'weave')
stray('cloth_shirt', 'padded_shirt', (222, 214, 196), (120, 130, 170), 'cloth', 'plain')
stray('wool_shirt', 'padded_shirt', (128, 140, 120), (226, 220, 200), 'cloth', 'hatch')
stray('wool_cloak', 'cloak', (110, 124, 104), (70, 80, 66), 'cloth', 'hatch')
stray('elven_shirt', 'padded_shirt', (150, 214, 190), (236, 244, 230), 'cloth', 'sheen', (236, 255, 240))
stray('padded_armor', 'padded', (170, 150, 110), (100, 80, 56), 'cloth', 'plain')
stray('padded_shirt', 'padded_shirt', (186, 166, 122), (110, 86, 58), 'cloth', 'plain', None, x_quilt)
stray('padded_leggings', 'cloth_leggings', (180, 160, 118), (104, 82, 56), 'cloth', 'plain', None, x_quilt)
stray('padded_boots', 'leather_boots', (180, 160, 118), (104, 82, 56), 'cloth', 'plain', None, x_quilt)
stray('padded_bracers', 'leather_bracers', (180, 160, 118), (104, 82, 56), 'cloth', 'plain', None, x_quilt)
stray('fur_cloak', 'cloak', (130, 96, 66), (226, 210, 180), 'leather', 'fur', None, x_fur_collar)
stray('ring_cloak', 'cloak', (96, 80, 110), (226, 190, 80), 'cloth', 'plain', None, x_rings)
stray('shadowweave_cloak', 'cloak', (40, 34, 58), (120, 80, 180), 'cloth', 'shadow', (190, 120, 255))
stray('crystal_cloak', 'cloak', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_boots', 'plate_boots', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_bracers', 'plate_vambraces', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_greaves', 'plate_greaves', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_helm', 'steel_helm', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_plate', 'plate', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('crystal_shield', 'kite_shield', (150, 214, 236), (250, 255, 255), 'crystal', 'facet', (250, 255, 255))
stray('full_plate', 'full_plate', (190, 196, 210), (110, 116, 140), 'metal', 'streak2')
stray('half_plate', 'plate', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('great_helm', 'great_helm', (176, 182, 196), (226, 186, 80), 'metal', 'streak')
stray('plate_boots', 'plate_boots', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('plate_bracers', 'plate_vambraces', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('plate_gauntlets', 'plate_gauntlets', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('plate_greaves', 'plate_greaves', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('plate_helm', 'plate_helm', (176, 182, 196), (110, 116, 140), 'metal', 'streak')
stray('ring_mail', 'ringmail', (170, 174, 186), (100, 104, 120), 'metal', 'plain')
stray('splint_mail', 'splint', (160, 164, 176), (100, 104, 120), 'metal', 'streak')
stray('scale_mail', 'scale', (160, 166, 180), (226, 186, 80), 'metal', 'plain')
stray('scale_shirt', 'chain_shirt', (190, 150, 80), (120, 84, 40), 'metal', 'plain', None, x_scale)
stray('scale_bracers', 'iron_vambraces', (160, 166, 180), (100, 104, 120), 'metal', 'plain', None, x_scale)
stray('scale_greaves', 'plate_greaves', (160, 166, 180), (100, 104, 120), 'metal', 'plain', None, x_scale)
stray('wooden_shield', 'light_wooden', (160, 110, 60), (90, 60, 36), 'wood', 'knot')
stray('dread_plate', 'full_plate', (50, 44, 60), (150, 30, 40), 'metal', 'shadow', (255, 60, 50),
      lambda s, p: (s.rect(13, 4, 18, 4, p.g), s.mpoly([(6, 8), (3, 3), (9, 7)], p.dd), s.px([(15, 12), (16, 12)], p.g)))
stray('enchanted_plate', 'plate', (170, 184, 220), (120, 200, 255), 'metal', 'streak', (130, 220, 255), x_runes(None))
stray('green_knights_plate', 'full_plate', (60, 140, 76), (236, 196, 80), 'metal', 'streak', None,
      lambda s, p: (s.mell(5, 7, 12, 12, p.t), s.rect(15, 10, 16, 16, p.t), s.mrect(10, 24, 14, 25, p.t), s.px([(14, 0), (17, 0), (15, 1), (16, 1)], (120, 200, 90))))
stray('sentinel_plate', 'full_plate', (150, 146, 136), (226, 190, 90), 'metal', 'dull', (255, 220, 110),
      lambda s, p: (s.rect(13, 4, 18, 4, p.g), s.rect(15, 12, 16, 13, p.g), s.mrect(10, 24, 14, 25, p.t)))
# dragon and monster scale armour
stray('dragon_scale', 'scale', (70, 150, 80), (226, 200, 110), 'scale', 'plain', None, dragon())
stray('red_dragon_scale', 'scale', (196, 50, 40), (250, 180, 70), 'scale', 'plain', (255, 190, 60), dragon())
stray('blue_dragon_scale', 'scale', (54, 104, 214), (240, 226, 120), 'scale', 'plain', (200, 240, 255), dragon())
stray('black_dragon_scale', 'scale', (44, 44, 56), (140, 210, 90), 'scale', 'plain', (160, 240, 90), dragon())
stray('sea_dragon_scale', 'scale', (60, 180, 190), (236, 250, 240), 'scale', 'plain', None,
      lambda s, p: (s.mpoly([(4, 9), (1, 4), (4, 6), (5, 2), (8, 6)], p.t), s.mline([(2, 5), (5, 8)], (40, 120, 150))))
stray('lich_dragon_scale', 'scale', (214, 210, 190), (110, 100, 96), 'bone', 'plain', (130, 255, 150), dragon())
stray('behir_scale', 'scale', (70, 110, 196), (40, 50, 110), 'scale', 'plain', (180, 230, 255),
      lambda s, p: (s.line([(10, 10), (13, 13), (11, 15), (14, 19)], p.g), s.line([(21, 12), (19, 16), (21, 18)], p.g)))
stray('kobold_scale', 'scale', (176, 104, 60), (90, 56, 40), 'scale', 'plain', None,
      lambda s, p: s.mpx([(9, 26), (12, 23)], (226, 200, 150)))
stray('lizardfolk_scale', 'scale', (120, 146, 70), (226, 210, 160), 'scale', 'plain', None,
      lambda s, p: (s.rect(15, 9, 16, 24, (80, 100, 50)), s.px([(15, 8), (16, 12), (15, 16), (16, 20)], (226, 210, 160))))
stray('naga_scale', 'scale', (40, 150, 140), (236, 196, 80), 'scale', 'plain', None,
      lambda s, p: (s.rect(8, 16, 23, 17, p.t), s.px([(15, 16), (16, 17)], (200, 40, 60))))
stray('pit_fiend_scale', 'scale', (120, 30, 34), (40, 20, 26), 'scale', 'plain', (255, 150, 40),
      lambda s, p: (s.mpoly([(5, 8), (2, 5), (1, 0), (4, 3), (8, 5)], (50, 34, 40)), s.px([(11, 12), (20, 15), (13, 20), (18, 9), (10, 22), (21, 22)], p.g)))
stray('corruption_scale', 'scale', (96, 60, 120), (60, 30, 80), 'scale', 'plain', (150, 255, 90),
      lambda s, p: (s.px([(11, 11), (12, 12), (11, 13), (19, 17), (20, 18), (14, 22)], p.g), s.px([(10, 29), (17, 30)], p.g)))
stray('jormungandr_scale', 'scale', (30, 104, 96), (150, 220, 190), 'scale', 'plain', None, dragon())
stray('world_serpent_scale', 'scale', (36, 70, 110), (226, 190, 90), 'scale', 'plain', (150, 230, 255), dragon())
# hides
stray('troll_hide', 'hide', (96, 140, 84), (60, 90, 60), 'leather', 'warts')
stray('ogre_hide', 'hide', (160, 144, 116), (110, 96, 80), 'leather', 'warts')
stray('gnoll_hide', 'hide', (196, 160, 96), (86, 60, 40), 'leather', 'spots')
stray('grick_hide', 'hide', (130, 116, 140), (80, 70, 96), 'leather', 'pebble')
stray('mud_crawler_hide', 'hide', (110, 84, 60), (70, 52, 40), 'leather', 'warts')
stray('crocodile_hide', 'hide', (70, 104, 66), (40, 66, 44), 'leather', 'scales')
stray('displacer_hide', 'hide', (44, 40, 70), (20, 18, 40), 'leather', 'plain', (190, 120, 255),
      lambda s, p: s.px([(11, 15), (20, 21), (12, 24)], p.g))
stray('cloaker_hide', 'cloak', (60, 50, 70), (30, 24, 40), 'leather', 'pebble', (255, 70, 60),
      lambda s, p: (s.rect(13, 4, 18, 8, p.dd), s.px([(13, 13), (14, 13), (17, 13), (18, 13)], p.g), s.px([(12, 17), (14, 18), (16, 17), (18, 18), (20, 17)], (236, 232, 214))))


def _hood(base, trim, kind):
    def run(rec):
        s = A()
        p = pal(s, base, trim, 'cloth' if kind != 'mail' else 'metal', 'plain')
        s.ell(6, 3, 25, 24, p.b); s.poly([(7, 15), (24, 15), (28, 28), (3, 28)], p.b)
        if kind == 'cowl':
            s.poly([(15, 1), (19, 2), (16, 5), (12, 5)], p.b)
        if kind == 'mail':
            mail(s, p)
        elif kind == 'quilt':
            quilt(s, p)
        else:
            s.mline([(8, 12), (6, 26)], p.d); s.mline([(10, 22), (9, 27)], p.d)
        s.ell(11, 9, 20, 21, (26, 22, 32))
        s.ell(10, 8, 21, 22, p.d) if False else None
        if kind == 'cowl':
            s.poly([(11, 14), (20, 14), (20, 21), (11, 21)], p.dd)       # face mask
            s.px([(13, 12), (14, 12), (17, 12), (18, 12)], (236, 236, 240))
            s.line([(3, 28), (28, 28)], p.t)
        else:
            s.line([(3, 28), (28, 28)], p.t)
            s.line([(11, 22), (15, 24), (16, 24), (20, 22)], p.t)
        s.clip()
        return s.finish()
    return run


STRAY['assassin_cowl'] = _hood((52, 48, 64), (150, 36, 44), 'cowl')
STRAY['cloth_hood'] = _hood((120, 110, 90), (190, 176, 140), 'cloth')
STRAY['chain_coif'] = _hood((170, 176, 190), (110, 114, 134), 'mail')
STRAY['padded_coif'] = _hood((190, 170, 126), (110, 86, 58), 'quilt')


def _bascinet(rec):
    s = A()
    p = pal(s, (176, 182, 198), (100, 106, 126))
    s.sym([(15, 1), (11, 5), (8, 12), (8, 20)], p.b)
    surface(s, p)
    s.poly([(8, 19), (23, 19), (26, 28), (5, 28)], p.d); mail(s, P(s, p.d, p.dd, 'metal', 'plain'))
    s.poly([(10, 12), (21, 12), (22, 17), (16, 23), (15, 23), (9, 17)], p.l)       # hounskull snout
    s.rect(11, 13, 14, 13, p.dark); s.rect(17, 13, 20, 13, p.dark)
    s.px([(17, 16), (19, 16), (18, 18), (17, 20), (16, 18)], p.dark)
    s.mpx([(9, 13)], p.riv)
    s.clip(); return s.finish()


def _sallet(rec):
    s = A()
    p = pal(s, (170, 176, 192), (100, 106, 126))
    s.poly([(3, 20), (2, 23), (8, 22), (26, 22), (28, 19), (27, 12), (22, 6), (15, 4), (9, 6), (6, 11)], p.b)
    surface(s, p)
    s.line([(16, 15), (27, 15)], p.dark); s.line([(2, 23), (8, 22), (26, 22)], p.d)
    s.line([(10, 6), (20, 5)], shade(p.b, 2))
    s.px([(12, 19), (16, 19), (20, 19), (24, 19)], p.riv)
    s.poly([(12, 23), (25, 23), (23, 28), (15, 28)], p.d); s.line([(15, 28), (23, 28)], p.l)   # bevor
    s.clip(); return s.finish()


STRAY['bascinet'] = _bascinet
STRAY['sallet'] = _sallet


def _cloth_sandals(rec):
    s = A()
    for ox, oy in ((13, -8), (2, 3)):
        _sandal(s, ox, oy, (150, 124, 84), (214, 204, 176))
        s.line([(ox + 3, oy + 20), (ox + 10, oy + 20)], (176, 164, 136))
    s.clip(); return s.finish()


STRAY['cloth_sandals'] = _cloth_sandals


def _mushroom(cap, spot, glow=None, crown=False):
    def run(rec):
        s = A()
        g = s.lit(glow) if glow else spot
        s.ell(2, 4, 29, 26, cap); s.crect(0, 18, 31, 31)
        s.poly([(3, 17), (28, 17), (26, 20), (5, 20)], shade(cap, -1))
        for x in range(6, 27, 2):
            s.px([(x, 19), (x, 20)], (236, 226, 206))
        s.ell(8, 8, 12, 11, spot); s.ell(17, 6, 21, 9, spot); s.ell(21, 12, 24, 15, spot); s.ell(12, 13, 15, 15, spot)
        s.poly([(10, 21), (21, 21), (20, 26), (11, 26)], (40, 34, 44))            # the hollow you wear
        s.line([(10, 21), (21, 21)], (236, 226, 206))
        if crown:
            for x in (11, 15, 19):
                s.poly([(x, 4), (x + 1, 0), (x + 2, 4)], (236, 196, 80))
        s.px([(6, 14), (26, 10), (15, 3)], g)
        s.clip(); return s.finish()
    return run


STRAY['sovereign_spore_cap'] = _mushroom((176, 60, 70), (244, 236, 214), (220, 255, 170), True)
STRAY['violet_fungus_cap'] = _mushroom((120, 70, 170), (214, 170, 240), (226, 150, 255))


def _amulet(rec):
    s = A()
    cord, plate = (130, 84, 50), (150, 100, 60)
    eye = s.lit((255, 90, 60))
    s.line([(16, 16), (8, 9), (7, 4), (12, 1), (19, 1), (24, 4), (23, 9), (16, 16)], cord)
    s.poly([(15, 14), (16, 14), (22, 21), (16, 29), (15, 29), (9, 21)], plate)
    s.poly([(15, 17), (16, 17), (19, 21), (16, 25), (15, 25), (12, 21)], (90, 58, 36))
    s.rect(15, 20, 16, 22, eye); s.px([(14, 21), (17, 21)], eye)
    s.px([(11, 21), (20, 21), (15, 27)], (226, 196, 150))
    s.clip(); return s.finish()


STRAY['amulet_warning_leather'] = _amulet


def _shield_core(rec):
    s = A()
    g1 = s.lit((120, 220, 255)); g2 = s.lit((240, 252, 255))
    disc(s, 11, (90, 96, 120)); disc(s, 9, (50, 56, 80)); disc(s, 6, g1); disc(s, 3, g2)
    for a in range(0, 360, 60):
        s.line([(15.5 + 7 * math.cos(math.radians(a)), 15.5 + 7 * math.sin(math.radians(a))),
                (15.5 + 10 * math.cos(math.radians(a)), 15.5 + 10 * math.sin(math.radians(a)))], (176, 182, 200), 2)
    s.clip(); return s.finish()


STRAY['shield_core'] = _shield_core


def _spellbook_shield(rec):
    s = A()
    cover, page, g = (60, 80, 160), (236, 226, 200), s.lit((150, 220, 255))
    s.rect(6, 4, 25, 28, cover); s.rect(23, 6, 25, 27, page); s.rect(6, 4, 8, 28, shade(cover, -1))
    s.px([(9, 5), (22, 5), (9, 27), (22, 27)], GOLD)
    s.sym([(11, 9), (11, 16), (13, 20), (15, 23)], GOLD)
    s.sym([(13, 11), (13, 16), (14, 19), (15, 20)], g)
    s.clip(); return s.finish()


STRAY['spellbook_shield'] = _spellbook_shield


def _wand_shield(c1, c2, fire):
    def run(rec):
        s = A()
        g1 = s.lit(c1); g2 = s.lit(c2)
        s.line([(5, 27), (17, 15)], (110, 76, 50), 2); s.px([(4, 28), (5, 28)], GOLD); s.px([(16, 15), (17, 14)], GOLD)
        s.poly([(15, 4), (27, 4), (27, 11), (21, 17), (15, 11)], g1)
        s.poly([(18, 6), (24, 6), (24, 10), (21, 13), (18, 10)], g2)
        if fire:
            s.px([(14, 2), (17, 1), (21, 2), (25, 1), (28, 3), (29, 7)], g1)
        else:
            s.px([(13, 6), (29, 8), (21, 19), (21, 1), (19, 2), (23, 2)], g2)
        s.clip(); return s.finish()
    return run


STRAY['wand_of_cold_shield'] = _wand_shield((120, 200, 255), (236, 250, 255), False)
STRAY['wand_of_fire_shield'] = _wand_shield((255, 120, 40), (255, 226, 110), True)
