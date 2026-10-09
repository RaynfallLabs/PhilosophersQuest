"""Prime cuts, boss trophies and dungeon-foraged ingredients.

Every monster yields a "prime cut" (`<monster>_prime`). They never had
pictures of their own: all 516 showed one shared meat icon. What a cut
looks like depends on what it came from (`family`), tinted by the monster's
own colour, with a few shapes per family chosen by the id.
"""
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import Sprite, shade, BONE, GOLD, IRON, STEEL, DARK  # noqa: E402

_MON = None


def _monster_color(rec):
    global _MON
    if _MON is None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
        with open(os.path.join(root, 'data', 'monsters.json'), encoding='utf-8') as f:
            _MON = json.load(f)
    m = _MON.get(rec.get('source_monster') or '', {})
    c = m.get('color') if isinstance(m, dict) else None
    return tuple(int(v) for v in c[:3]) if c else None


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _steak(s, meat, fat, v):
    if v == 0:                                   # T-bone
        s.poly([(6, 10), (16, 5), (25, 9), (26, 19), (18, 26), (8, 23), (5, 16)], fat)
        s.poly([(8, 11), (16, 7), (23, 10), (24, 18), (17, 24), (9, 21), (7, 16)], meat)
        s.line([(15, 8), (16, 15), (12, 21)], BONE, 2); s.line([(16, 15), (21, 16)], BONE, 2)
    elif v == 1:                                 # drumstick
        s.ell(5, 5, 21, 21, meat); s.ell(8, 8, 14, 13, _mix(meat, (255, 255, 255), 0.25))
        s.line([(18, 18), (25, 25)], BONE, 3); s.ell(23, 22, 28, 27, BONE)
    elif v == 2:                                 # rack of ribs
        s.poly([(5, 9), (26, 7), (27, 22), (6, 24)], meat)
        for x in (9, 14, 19, 24):
            s.line([(x, 5), (x, 26)], BONE, 2)
        s.line([(5, 9), (26, 7)], fat)
    else:                                        # rolled fillet, tied
        s.ell(4, 9, 27, 24, meat); s.ell(4, 9, 12, 24, _mix(meat, (255, 220, 200), 0.35))
        s.ell(6, 13, 10, 20, fat)
        for x in (15, 20, 24):
            s.line([(x, 10), (x, 23)], (230, 220, 190))


def _parcel(s, tint, v):
    paper = (206, 186, 150)
    s.poly([(5, 11), (26, 9), (27, 23), (6, 25)], paper)
    s.poly([(5, 11), (16, 15), (26, 9)], _mix(paper, (255, 255, 255), 0.2))
    s.line([(16, 10), (16, 24)], (150, 60, 50)); s.line([(5, 17), (27, 16)], (150, 60, 50))
    s.rect(14, 14, 18, 18, tint)                 # a wax seal in the creature's colour
    if v % 2:
        s.px([(13, 8), (19, 8), (12, 7), (20, 7)], (150, 60, 50))


def _bone(s, glow, v):
    g = s.lit(glow)
    if v % 2 == 0:
        s.line([(8, 23), (23, 8)], BONE, 4)
        s.ell(4, 20, 10, 26, BONE); s.ell(7, 23, 12, 28, BONE)
        s.ell(20, 4, 26, 10, BONE); s.ell(23, 7, 28, 12, BONE)
        s.px([(13, 17), (17, 13), (15, 15)], g)
    else:                                        # a jar of something that was never flesh
        s.rect(9, 9, 22, 26, (176, 196, 204)); s.rect(11, 5, 20, 9, (150, 110, 70))
        s.ell(11, 13, 20, 23, g); s.px([(14, 16), (17, 16)], DARK)
    s.px([(5, 8), (26, 22)], g)


def _demon(s, hide, v):
    ember = s.lit((255, 140, 40))
    s.poly([(6, 12), (15, 6), (24, 10), (26, 20), (18, 26), (8, 23)], hide)
    s.poly([(9, 13), (15, 9), (22, 12), (23, 19), (17, 23), (10, 21)], shade(hide, -1))
    s.line([(11, 15), (15, 18), (20, 14)], ember); s.px([(14, 21), (19, 19)], ember)
    if v % 2:
        s.poly([(20, 8), (26, 3), (24, 10)], BONE)
    else:
        s.line([(18, 24), (24, 28)], BONE, 3)


def _tentacle(s, col, v):
    pale = _mix(col, (255, 230, 240), 0.5)
    s.line([(6, 25), (10, 15), (17, 11), (23, 14), (23, 20), (18, 22), (16, 18)], col, 5)
    for x, y in ((8, 21), (10, 16), (14, 13), (19, 12), (22, 16)):
        s.px([(x, y)], pale)
    if v % 2:
        s.ell(20, 4, 26, 10, (236, 236, 226)); s.ell(22, 6, 24, 8, s.lit((120, 220, 120)))


def _construct(s, col, v):
    core = s.lit(_mix(col, (120, 230, 255), 0.6))
    s.poly([(6, 12), (14, 6), (25, 9), (26, 21), (17, 26), (7, 22)], _mix(IRON, col, 0.35))
    s.px([(9, 13), (22, 11), (23, 20), (10, 21)], STEEL)
    if v % 2 == 0:
        s.ell(12, 12, 20, 20, DARK); s.ell(14, 14, 18, 18, core)
    else:
        s.line([(10, 16), (22, 14)], DARK); s.line([(15, 8), (17, 24)], DARK); s.px([(16, 15)], core)


def _elemental(s, col, v):
    lit = s.lit(_mix(col, (255, 255, 255), 0.35))
    s.poly([(16, 3), (23, 11), (20, 27), (12, 27), (8, 12)], shade(col, -1))
    s.poly([(16, 6), (20, 12), (18, 24), (13, 24), (11, 12)], lit)
    s.poly([(24, 16), (28, 21), (25, 27), (22, 22)], shade(col, -1))
    if v % 2:
        s.poly([(5, 18), (9, 22), (7, 27), (3, 23)], shade(col, -1))
    s.px([(15, 9), (16, 9), (14, 14)], (255, 255, 255))


def _dragon(s, col, v):
    belly = _mix(col, (240, 220, 160), 0.6)
    s.poly([(5, 13), (14, 7), (24, 9), (27, 18), (19, 26), (8, 24)], col)
    for x, y in ((10, 12), (15, 10), (20, 12), (12, 16), (17, 15), (22, 17), (10, 20), (15, 20), (19, 22)):
        s.line([(x, y), (x + 2, y + 1)], shade(col, -1))
    s.poly([(8, 22), (14, 20), (18, 25), (10, 25)], belly)
    s.poly([(24, 10), (29, 6), (27, 13)], BONE)
    if v % 2:
        s.px([(7, 9), (9, 7)], s.lit((255, 170, 60)))


def _plant(s, col, v):
    leaf = (86, 150, 70)
    if v % 2 == 0:                               # a bulb
        s.ell(8, 13, 23, 27, _mix(col, (220, 190, 150), 0.5))
        s.line([(12, 16), (11, 25)], shade(col, -1)); s.line([(18, 16), (19, 25)], shade(col, -1))
        s.poly([(15, 13), (12, 4), (16, 9), (20, 3), (17, 13)], leaf)
    else:                                        # a root
        s.poly([(10, 8), (20, 8), (18, 20), (15, 28), (13, 20)], _mix(col, (200, 150, 90), 0.5))
        s.line([(11, 13), (19, 13)], shade(col, -1)); s.line([(12, 18), (18, 18)], shade(col, -1))
        s.poly([(13, 8), (9, 2), (15, 6), (17, 1), (18, 6), (23, 3), (18, 8)], leaf)


def _reptile(s, col, v):
    meat = (236, 220, 200)
    s.poly([(4, 20), (12, 11), (22, 8), (27, 12), (25, 19), (15, 24), (7, 26)], col)
    for x, y in ((11, 15), (15, 13), (19, 12), (13, 19), (18, 17), (22, 15)):
        s.px([(x, y), (x + 1, y)], shade(col, -1))
    s.ell(21, 9, 28, 18, meat); s.ell(23, 11, 26, 15, (226, 150, 140))


def _celestial(s, col, v):
    light = s.lit((255, 244, 190))
    s.ell(6, 8, 25, 25, (250, 246, 232)); s.ell(11, 12, 20, 21, light)
    s.px([(15, 4), (16, 4), (4, 16), (27, 16), (15, 28), (8, 8), (24, 9)], light)


FAMILY = {'beast': None, 'humanoid': _parcel, 'fey': _parcel, 'undead': _bone, 'demon': _demon,
          'aberration': _tentacle, 'construct': _construct, 'elemental': _elemental, 'dragon': _dragon,
          'plant': _plant, 'reptile': _reptile, 'celestial': _celestial}


def _trophy(s, col):
    gem = s.lit(_mix(col, (255, 255, 255), 0.2))
    s.rect(11, 25, 20, 28, (110, 78, 46)); s.rect(14, 20, 17, 25, GOLD)
    s.poly([(8, 6), (23, 6), (21, 17), (16, 21), (15, 21), (10, 17)], GOLD)
    s.line([(8, 8), (4, 9), (5, 14), (9, 15)], GOLD); s.line([(23, 8), (27, 9), (26, 14), (22, 15)], GOLD)
    s.ell(13, 9, 18, 14, gem)
    s.px([(11, 4), (20, 3), (6, 4)], s.lit((255, 244, 190)))


def _dungeon(s, rid, col):
    if rid == 'crystal_shard':
        _elemental(s, col, 0)
    elif rid == 'holy_water':
        w = s.lit((200, 232, 255))
        s.rect(13, 4, 18, 8, (150, 110, 70)); s.poly([(13, 8), (18, 8), (23, 20), (20, 27), (11, 27), (8, 20)], (176, 200, 214))
        s.poly([(11, 16), (20, 16), (21, 21), (19, 25), (12, 25), (10, 21)], w)
        s.rect(15, 18, 16, 23, GOLD); s.rect(13, 19, 18, 20, GOLD)
    elif rid == 'swamp_moss':
        s.ell(5, 14, 26, 27, col); s.ell(8, 10, 18, 20, shade(col, 1)); s.ell(16, 12, 24, 21, col)
        s.px([(10, 14), (19, 16), (13, 22), (22, 23), (8, 20)], (150, 190, 100))
    elif rid == 'deep_iron':
        s.poly([(6, 14), (13, 7), (24, 10), (27, 20), (18, 27), (8, 24)], col)
        s.px([(11, 13), (12, 13), (20, 14), (16, 20), (17, 20), (22, 21)], STEEL)
        s.line([(13, 9), (17, 16), (14, 24)], DARK)
    elif rid == 'altar_incense':
        smoke = (210, 206, 214)
        s.poly([(9, 18), (22, 18), (20, 27), (11, 27)], GOLD); s.rect(8, 16, 23, 18, GOLD)
        s.px([(12, 21), (15, 23), (18, 21)], DARK); s.px([(15, 15), (16, 15)], s.lit((255, 150, 60)))
        s.line([(15, 13), (13, 10), (16, 7), (14, 3)], smoke); s.line([(18, 12), (20, 8)], smoke)
    elif rid == 'abyssal_kelp':
        s.line([(10, 28), (8, 20), (12, 13), (9, 5)], col, 3); s.line([(19, 28), (22, 19), (18, 12), (21, 4)], col, 3)
        s.px([(7, 16), (13, 9), (23, 15), (17, 8)], s.lit((120, 230, 220)))
    else:
        return False
    return True


def draw(rec):
    """A picture for a prime cut, trophy or dungeon ingredient, or None to
    let the general ingredient rigs handle it."""
    rid = rec['id']
    role = rec.get('tier_role')
    if role not in ('prime', 'trophy', 'dungeon'):
        return None
    seed = zlib.crc32(rid.encode())
    mon = _monster_color(rec)
    s = Sprite()
    s.shadow = False
    if role == 'dungeon':
        if not _dungeon(s, rid, tuple(rec.get('color') or (160, 160, 170))):
            return None
    elif role == 'trophy':
        _trophy(s, mon or (220, 60, 60))
    else:
        fam = rec.get('family') or 'beast'
        fn = FAMILY.get(fam)
        if fn is None:
            meat = _mix((178, 58, 54), mon or (178, 58, 54), 0.22)
            _steak(s, meat, (240, 222, 196), seed % 4)
        else:
            fn(s, mon or (150, 110, 150), seed % 4)
    return s.finish()
