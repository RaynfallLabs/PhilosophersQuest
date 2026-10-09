"""Map objects that are defined in code, not in the data files, and so never
had a picture: Death, the ghost of a fallen hero, a pile of gold, the gnome
trader, the abyss shimmer, and the fourteen mystery shrines with their keys.
They used to show as a letter or a coloured square.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import Sprite, BONE, GOLD, IRON, STEEL, WOOD, DARK, LEATHER  # noqa: E402

STONE = (146, 142, 156)
D = {}


def art(folder, shadow=False):
    def deco(fn):
        def run(rec=None):
            s = Sprite()
            s.shadow = shadow
            fn(s)
            return s.finish()
        D[fn.__name__] = (folder, run)
        return fn
    return deco


# ---------------------------------------------------------------- beings
@art('monsters', shadow=True)
def death(s):
    robe = (38, 34, 48)
    eye = s.lit((170, 220, 255))
    s.poly([(10, 12), (21, 12), (25, 29), (6, 29)], robe)
    s.ell(10, 3, 21, 14, robe); s.poly([(10, 9), (15, 1), (16, 1), (21, 9)], robe)
    s.ell(12, 6, 19, 13, BONE); s.px([(14, 9), (17, 9)], eye); s.px([(15, 12), (16, 12)], DARK)
    s.poly([(9, 15), (5, 21), (8, 22), (11, 17)], robe); s.rect(5, 21, 7, 22, BONE)
    s.line([(26, 4), (26, 29)], WOOD)
    s.poly([(26, 4), (20, 2), (14, 4), (19, 5), (26, 7)], STEEL)


@art('monsters', shadow=True)
def player_ghost(s):
    pale = (176, 206, 226)
    eye = s.lit((120, 240, 220))
    s.ell(9, 4, 22, 17, pale)
    s.poly([(9, 11), (22, 11), (24, 27), (21, 24), (18, 28), (15, 24), (12, 28), (9, 24), (7, 27)], pale)
    s.px([(13, 9), (14, 9), (17, 9), (18, 9)], eye); s.line([(14, 13), (17, 13)], DARK)
    s.line([(23, 12), (26, 5)], STEEL); s.rect(22, 12, 25, 13, (140, 160, 180))   # the sword it died holding


@art('monsters')
def abyssal_shimmer(s):
    w = s.lit((255, 255, 255)); g = s.lit((216, 216, 226))
    s.ell(9, 9, 22, 22, g); s.ell(12, 12, 19, 19, w)
    s.px([(15, 3), (16, 3), (15, 28), (16, 28), (3, 15), (3, 16), (28, 15), (28, 16),
          (7, 7), (24, 7), (7, 24), (24, 24)], w)


@art('items', shadow=True)
def merchant_npc(s):
    skin, coat, pack = (168, 172, 206), (86, 70, 110), (140, 104, 62)
    lamp = s.lit((255, 214, 110))
    s.ell(15, 6, 28, 22, pack); s.rect(17, 3, 26, 7, (176, 136, 84)); s.line([(16, 12), (27, 12)], LEATHER)
    s.rect(11, 24, 13, 28, DARK); s.rect(16, 24, 18, 28, DARK)
    s.poly([(8, 15), (20, 15), (21, 25), (8, 25)], coat); s.line([(9, 21), (20, 21)], GOLD)
    s.ell(8, 6, 19, 16, skin); s.poly([(8, 9), (5, 7), (9, 12)], skin); s.poly([(19, 9), (22, 7), (18, 12)], skin)
    s.px([(11, 10), (15, 10)], DARK); s.poly([(11, 13), (16, 13), (13, 18)], (226, 226, 236))   # white beard
    s.poly([(8, 7), (13, 2), (19, 7)], (150, 50, 50))
    s.line([(5, 16), (5, 20)], IRON); s.rect(3, 20, 7, 25, IRON); s.rect(4, 21, 6, 24, lamp)


@art('items')
def gold_pile(s):
    dk = (186, 136, 36)
    glint = s.lit((255, 246, 190))
    s.ell(4, 18, 27, 29, dk)
    for x, y in ((6, 19), (13, 16), (20, 19), (9, 22), (17, 22), (12, 12), (16, 13)):
        s.ell(x, y, x + 7, y + 4, GOLD)
    s.px([(9, 20), (15, 17), (22, 20), (14, 13), (19, 23)], glint)
    s.px([(5, 13), (25, 14)], glint)


# ---------------------------------------------------------------- the mystery shrines
def _plinth(s):
    s.rect(6, 23, 25, 28, (112, 108, 122)); s.rect(8, 19, 23, 23, STONE)


@art('items')
def mystery_altar_sphinx(s):
    _plinth(s)
    s.poly([(9, 19), (22, 19), (22, 13), (14, 12), (9, 15)], GOLD)
    s.ell(15, 3, 23, 12, GOLD); s.poly([(14, 5), (12, 12), (16, 12)], (40, 80, 170)); s.poly([(24, 5), (25, 12), (22, 12)], (40, 80, 170))
    s.px([(17, 7), (21, 7)], s.lit((120, 230, 255)))


@art('items')
def mystery_altar_pandora(s):
    red = (160, 34, 38)
    leak = s.lit((200, 120, 255))
    s.rect(6, 14, 25, 27, red); s.poly([(6, 14), (9, 9), (22, 9), (25, 14)], red)
    s.rect(6, 17, 25, 18, GOLD); s.rect(14, 15, 17, 21, GOLD); s.px([(15, 18), (16, 19)], DARK)
    s.px([(10, 8), (13, 6), (20, 7), (23, 5), (16, 4)], leak)


@art('items')
def mystery_altar_grail(s):
    glow = s.lit((255, 244, 190))
    _plinth(s)
    s.rect(11, 17, 20, 19, (236, 232, 240))
    s.poly([(11, 6), (20, 6), (18, 12), (13, 12)], GOLD); s.rect(15, 12, 16, 15, GOLD); s.rect(13, 15, 18, 16, GOLD)
    s.px([(15, 3), (16, 3), (9, 5), (22, 5), (15, 8)], glow)


@art('items')
def mystery_altar_fleece(s):
    _plinth(s)
    fleece = (232, 184, 60)
    s.ell(7, 8, 24, 21, fleece); s.ell(9, 5, 15, 11, fleece); s.poly([(8, 18), (6, 24), (11, 21)], fleece)
    s.poly([(23, 18), (25, 24), (20, 21)], fleece)
    s.px([(11, 12), (15, 10), (19, 13), (13, 16), (18, 17), (21, 11)], (255, 226, 130))
    s.px([(10, 7), (11, 7)], DARK)


@art('items')
def mystery_altar_mimir(s):
    water = s.lit((90, 170, 250))
    s.ell(4, 13, 27, 29, STONE); s.ell(7, 15, 24, 26, (30, 60, 120)); s.ell(10, 17, 21, 24, water)
    s.rect(5, 5, 6, 16, WOOD); s.rect(25, 5, 26, 16, WOOD); s.rect(5, 4, 26, 5, WOOD)
    s.line([(15, 5), (15, 11)], (190, 190, 180)); s.rect(13, 11, 17, 14, WOOD)
    s.px([(14, 19), (17, 21)], (220, 240, 255))


@art('items')
def mystery_altar_mjolnir(s):
    hot = s.lit((255, 150, 40))
    s.rect(11, 22, 20, 28, (70, 66, 80)); s.poly([(5, 12), (26, 12), (22, 17), (20, 22), (11, 22), (9, 17)], IRON)
    s.poly([(26, 12), (30, 14), (26, 16)], IRON); s.line([(6, 12), (25, 12)], STEEL)
    s.rect(12, 8, 18, 11, hot); s.px([(10, 6), (20, 5), (15, 4), (22, 8)], hot)


@art('items')
def mystery_altar_crucible(s):
    fire = s.lit((255, 140, 40)); melt = s.lit((255, 226, 110))
    s.line([(9, 18), (6, 29)], IRON); s.line([(22, 18), (25, 29)], IRON); s.line([(15, 20), (15, 29)], IRON)
    s.poly([(7, 9), (24, 9), (21, 20), (10, 20)], (150, 150, 160)); s.ell(9, 8, 22, 12, melt)
    s.poly([(12, 28), (15, 22), (16, 25), (18, 21), (20, 28)], fire)


@art('items')
def mystery_altar_oracle(s):
    rift = s.lit((190, 110, 250)); mist = (150, 120, 190)
    s.poly([(4, 26), (12, 20), (15, 23), (20, 19), (28, 26), (28, 29), (4, 29)], (84, 78, 96))
    s.poly([(13, 26), (15, 14), (17, 20), (19, 12), (20, 26)], rift)
    s.ell(9, 6, 16, 12, mist); s.ell(15, 3, 23, 10, mist); s.px([(12, 8), (19, 6)], (220, 200, 250))


@art('items')
def mystery_altar_solomon(s):
    s.rect(7, 26, 24, 28, (112, 108, 122)); s.rect(14, 8, 17, 26, GOLD); s.ell(13, 4, 18, 9, GOLD)
    s.rect(5, 9, 26, 10, GOLD)
    s.line([(6, 10), (4, 17)], (190, 190, 180)); s.line([(6, 10), (9, 17)], (190, 190, 180))
    s.line([(25, 10), (22, 17)], (190, 190, 180)); s.line([(25, 10), (27, 17)], (190, 190, 180))
    s.poly([(3, 17), (10, 17), (8, 20), (5, 20)], GOLD); s.poly([(21, 17), (28, 17), (26, 20), (23, 20)], GOLD)
    s.px([(15, 6), (16, 6)], s.lit((255, 244, 190)))


@art('items')
def mystery_altar_fisher_king(s):
    green = (60, 150, 80)
    s.rect(9, 5, 22, 22, (120, 96, 66)); s.rect(11, 8, 20, 20, green)
    s.rect(6, 16, 9, 26, (120, 96, 66)); s.rect(22, 16, 25, 26, (120, 96, 66)); s.rect(8, 22, 23, 27, green)
    s.poly([(11, 5), (13, 2), (15, 5), (16, 2), (18, 5), (20, 2), (21, 5)], GOLD)
    s.line([(26, 4), (29, 20)], WOOD); s.line([(29, 20), (27, 26)], (200, 200, 190))
    s.poly([(25, 26), (29, 25), (28, 29)], (120, 170, 210))


@art('items')
def mystery_altar_sisyphus(s):
    s.poly([(2, 29), (29, 29), (29, 12)], (112, 96, 80)); s.poly([(8, 29), (29, 29), (29, 17)], (92, 78, 66))
    s.ell(11, 7, 23, 19, (150, 148, 150)); s.px([(14, 10), (15, 10), (19, 14)], (190, 188, 190))
    s.line([(15, 12), (18, 16)], (96, 94, 100))


@art('items')
def mystery_altar_brendan(s):
    hull, sail = (132, 92, 52), (232, 226, 206)
    s.poly([(3, 20), (28, 20), (24, 27), (7, 27)], hull); s.line([(3, 20), (28, 20)], (176, 136, 84))
    s.line([(15, 3), (15, 20)], WOOD); s.poly([(16, 4), (26, 16), (16, 17)], sail); s.poly([(14, 6), (6, 17), (14, 17)], sail)
    s.rect(20, 9, 20, 14, (176, 50, 50)); s.rect(18, 11, 22, 11, (176, 50, 50))
    s.px([(4, 28), (10, 29), (20, 29), (27, 28)], (120, 170, 220))


@art('items')
def mystery_altar_jerome(s):
    page = (238, 228, 200)
    lamp = s.lit((255, 214, 110))
    s.rect(4, 17, 27, 20, WOOD); s.rect(6, 20, 8, 28, WOOD); s.rect(23, 20, 25, 28, WOOD)
    s.poly([(8, 16), (15, 13), (15, 17), (8, 17)], page); s.poly([(16, 13), (23, 16), (23, 17), (16, 17)], page)
    s.line([(10, 15), (13, 14)], DARK); s.line([(18, 14), (21, 15)], DARK)
    s.line([(22, 12), (26, 5)], (236, 236, 240)); s.rect(4, 12, 6, 16, IRON); s.px([(5, 10), (5, 11)], lamp)
    s.ell(24, 10, 28, 15, BONE); s.px([(25, 12), (27, 12)], DARK)


@art('items')
def mystery_altar_cauldron(s):
    brew = s.lit((80, 220, 150))
    s.ell(5, 11, 26, 28, (34, 32, 40)); s.ell(7, 9, 24, 15, (54, 50, 62)); s.ell(9, 10, 22, 14, brew)
    s.rect(8, 27, 10, 29, (34, 32, 40)); s.rect(21, 27, 23, 29, (34, 32, 40))
    s.px([(12, 6), (17, 4), (20, 7), (14, 2)], brew)


# ---------------------------------------------------------------- and their keys
@art('items')
def mystery_key_pandora(s):
    red = (176, 40, 44)
    s.ell(4, 4, 13, 13, red); s.ell(7, 7, 10, 10, DARK)
    s.line([(11, 11), (25, 25)], red, 3); s.rect(21, 25, 22, 28, red); s.rect(25, 21, 28, 22, red)
    s.px([(6, 6)], s.lit((255, 200, 200)))


@art('items')
def mystery_key_grail(s):
    tarn = (150, 146, 120)
    s.poly([(8, 5), (23, 5), (20, 15), (11, 15)], tarn); s.rect(14, 15, 17, 22, tarn); s.rect(10, 22, 21, 25, tarn)
    s.px([(11, 8), (18, 11), (13, 23)], (104, 110, 90)); s.px([(20, 7)], (210, 206, 180))


@art('items')
def mystery_key_fleece(s):
    fleece = (232, 184, 60)
    s.ell(5, 8, 26, 24, fleece); s.ell(4, 5, 12, 12, fleece)
    s.poly([(7, 22), (5, 28), (11, 24)], fleece); s.poly([(24, 22), (26, 28), (20, 24)], fleece)
    s.px([(10, 13), (15, 11), (20, 14), (13, 18), (19, 19), (23, 12)], (255, 226, 130)); s.px([(6, 8)], DARK)


@art('items')
def mystery_key_mjolnir(s):
    hot = s.lit((255, 150, 40))
    s.poly([(6, 10), (25, 10), (27, 14), (27, 20), (25, 23), (6, 23), (4, 19), (4, 14)], IRON)
    s.rect(14, 14, 17, 19, DARK); s.px([(8, 12), (22, 12), (9, 21), (23, 21)], STEEL)
    s.px([(5, 11), (26, 22), (15, 13), (16, 20)], hot)


@art('items')
def mystery_key_crucible(s):
    lead = (120, 122, 136)
    s.poly([(6, 14), (11, 9), (26, 9), (22, 14)], (150, 152, 166)); s.poly([(6, 14), (22, 14), (22, 22), (6, 22)], lead)
    s.poly([(22, 14), (26, 9), (26, 17), (22, 22)], (92, 94, 108))
    s.line([(9, 18), (19, 18)], (92, 94, 108))


@art('items')
def mystery_key_solomon(s):
    star = s.lit((255, 244, 170))
    s.ell(5, 5, 26, 26, GOLD); s.ell(8, 8, 23, 23, (186, 136, 36))
    s.poly([(15, 9), (21, 20), (10, 20)], star); s.poly([(15, 23), (10, 12), (21, 12)], star)


@art('items')
def mystery_key_fisher_king(s):
    leaf = (90, 200, 100)
    s.line([(15, 28), (15, 12)], (60, 120, 60), 2)
    s.poly([(15, 14), (8, 9), (7, 15)], leaf); s.poly([(16, 12), (23, 6), (24, 13)], leaf)
    s.poly([(15, 21), (9, 18), (9, 23)], leaf); s.poly([(16, 20), (22, 17), (22, 22)], leaf)
    s.ell(13, 4, 18, 9, (240, 240, 250)); s.px([(15, 6), (16, 6)], s.lit((255, 240, 150)))


@art('items')
def mystery_key_sisyphus(s):
    s.ell(4, 6, 27, 28, (140, 140, 142)); s.ell(8, 9, 18, 16, (170, 170, 172))
    s.line([(13, 14), (18, 20), (16, 26)], (92, 92, 98)); s.line([(18, 20), (24, 18)], (92, 92, 98))
    s.px([(9, 22), (22, 24)], (112, 112, 116))


# ---------------------------------------------------------------- not yet identified
# Six looks for each kind of thing that hides what it is. The look follows the
# item's unidentified name, so "a fizzy blue potion" always looks the same and
# two different unknown potions look different, but no look says what the
# thing does. (Before this an unidentified item was drawn with its true
# picture: the healing wand showed its green cross.)
UNKNOWN_LOOKS = 6
_HUES = ((70, 130, 220), (200, 70, 70), (90, 180, 90), (190, 150, 60), (150, 90, 190), (90, 180, 190))


def _unknown(kind, k):
    c = _HUES[k]

    def potion(s):
        glass = (188, 204, 214)
        if k % 3 == 0:
            s.rect(13, 4, 18, 9, (150, 110, 70)); s.ell(7, 9, 24, 28, glass); s.ell(9, 15, 22, 26, c)
        elif k % 3 == 1:
            s.rect(13, 3, 18, 8, (150, 110, 70))
            s.poly([(13, 8), (18, 8), (25, 26), (22, 29), (9, 29), (6, 26)], glass)
            s.poly([(10, 19), (21, 19), (23, 26), (21, 28), (10, 28), (8, 26)], c)
        else:
            s.rect(13, 3, 18, 7, (150, 110, 70)); s.rect(10, 7, 21, 29, glass); s.rect(12, 14, 19, 27, c)
        s.px([(11, 13), (11, 14)], (240, 248, 255))

    def wand(s):
        s.line([(6, 26), (25, 7)], (112, 80, 52), 3)
        s.line([(11, 21), (14, 18)], c, 3); s.ell(23, 4, 28, 9, (190, 190, 200))
        s.px([(6, 27), (7, 26)], (70, 50, 34))

    def scroll(s):
        page = (232, 220, 186)
        s.rect(7, 8, 24, 23, page); s.ell(5, 5, 26, 11, page); s.ell(5, 20, 26, 26, page)
        s.rect(14, 12, 17, 19, c); s.ell(13, 13, 18, 18, c)
        s.line([(9, 14), (12, 14)], (150, 138, 110)); s.line([(19, 17), (22, 17)], (150, 138, 110))

    def spellbook(s):
        s.rect(7, 5, 24, 27, c); s.rect(7, 5, 9, 27, tuple(v * 6 // 10 for v in c))
        s.rect(22, 7, 24, 25, (232, 224, 200)); s.rect(12, 12, 19, 19, tuple(min(255, v + 50) for v in c))
        s.px([(10, 7), (21, 7), (10, 25), (21, 25)], GOLD)

    def ring(s):
        band = ((196, 170, 90), (176, 180, 190), (150, 110, 80))[k % 3]
        s.ell(7, 11, 24, 27, band); s.ell(11, 15, 20, 23, DARK)
        s.ell(12, 6, 19, 13, c); s.px([(14, 8)], (240, 248, 255))

    def amulet(s):
        s.line([(8, 3), (15, 14)], (176, 180, 190)); s.line([(23, 3), (16, 14)], (176, 180, 190))
        if k % 2:
            s.ell(9, 13, 22, 27, (196, 170, 90)); s.ell(12, 16, 19, 24, c)
        else:
            s.poly([(15, 13), (22, 20), (15, 28), (9, 20)], (196, 170, 90)); s.poly([(15, 16), (19, 20), (15, 25), (12, 20)], c)

    return {'potion': potion, 'wand': wand, 'scroll': scroll, 'spellbook': spellbook,
            'ring': ring, 'amulet': amulet}[kind]


for _kind in ('potion', 'wand', 'scroll', 'spellbook', 'ring', 'amulet'):
    for _k in range(UNKNOWN_LOOKS):
        def _run(rec=None, _fn=_unknown(_kind, _k)):
            s = Sprite()
            s.shadow = False
            _fn(s)
            return s.finish()
        D[f'unknown_{_kind}_{_k}'] = ('items', _run)


# ---------------------------------------------------------------- the duck that hatches
@art('monsters', shadow=True)
def waddlekind(s):
    yel = (250, 214, 70)
    s.ell(8, 14, 23, 27, yel); s.ell(9, 6, 19, 16, yel)
    s.poly([(9, 11), (4, 12), (9, 14)], (240, 140, 40)); s.px([(12, 10)], DARK)
    s.poly([(14, 19), (20, 18), (20, 23)], (236, 190, 40)); s.rect(11, 27, 13, 29, (240, 140, 40)); s.rect(17, 27, 19, 29, (240, 140, 40))


@art('monsters', shadow=True)
def drake_of_the_covenant(s):
    green, white = (40, 120, 70), (236, 236, 226)
    s.ell(6, 13, 24, 27, (150, 110, 80)); s.poly([(21, 14), (28, 10), (25, 20)], (120, 86, 60))
    s.rect(10, 8, 14, 16, white); s.ell(8, 2, 18, 11, green)
    s.poly([(8, 6), (3, 7), (8, 9)], (240, 190, 50)); s.px([(11, 5)], DARK); s.line([(10, 11), (14, 11)], white)
    s.poly([(12, 17), (21, 16), (22, 23), (14, 24)], (110, 150, 200))
    s.rect(11, 27, 13, 29, (240, 140, 40)); s.rect(18, 27, 20, 29, (240, 140, 40))


@art('monsters', shadow=True)
def seraphimallard(s):
    light = s.lit((255, 244, 180)); white = (244, 244, 236)
    for pts in ([(10, 14), (1, 6), (4, 16)], [(10, 17), (0, 14), (5, 21)], [(11, 20), (2, 23), (8, 25)],
                [(21, 14), (30, 6), (27, 16)], [(21, 17), (31, 14), (26, 21)], [(20, 20), (29, 23), (23, 25)]):
        s.poly(pts, light)
    s.ell(9, 13, 22, 27, white); s.ell(11, 5, 20, 14, white)
    s.poly([(11, 9), (6, 10), (11, 12)], (240, 170, 40)); s.px([(14, 8)], DARK)
    s.ell(11, 1, 20, 4, light); s.rect(12, 27, 14, 29, (240, 170, 40)); s.rect(17, 27, 19, 29, (240, 170, 40))


def draw(rec):
    return D[rec['id']][1](rec)


def records():
    return [{'folder': folder, 'id': name, 'kind': 'extras'} for name, (folder, _) in D.items()]
