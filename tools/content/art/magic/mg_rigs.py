"""Parametric rigs: wands, potions, scrolls, spellbooks, chests."""
import re
from mg_common import *

COLORS = {}   # id -> data colour, filled by magic.py (lets tier variants borrow the base colour)

GLOWING = {'flame', 'flame2', 'ember', 'burst', 'meteor', 'snow', 'shard', 'bolt', 'star4', 'star6', 'sun', 'portal',
           'spiral', 'plus', 'heart', 'moon', 'dart', 'drop', 'hollow', 'swap', 'leaf', 'ankh', 'wing', 'cross_x'}

WOODS = {'jet': (50, 48, 62), 'crystal': (170, 215, 240), 'cedar': (160, 86, 56), 'bronze': BRONZE, 'iron': IRON,
         'tin': (176, 182, 186), 'ivory': IVORY, 'oak': (150, 108, 60), 'steel': STEEL, 'antler': (214, 196, 160),
         'rowan': (176, 112, 76), 'cherry': (150, 60, 50), 'beech': (200, 164, 112), 'elm': (128, 100, 70),
         'silver': SILVER, 'blackthorn': (62, 48, 50), 'walnut': (96, 66, 46), 'porcelain': (236, 236, 244),
         'twisted': (120, 92, 60), 'agate': (150, 96, 70), 'violet': (120, 96, 150), 'grave': (112, 104, 100)}
WOOD_LIST = [(132, 92, 52), (96, 66, 46), (160, 86, 56), (200, 164, 112), (62, 48, 50), (150, 60, 50),
             IVORY, IRON, (176, 112, 76), (110, 120, 96), SILVER, (90, 70, 110)]


def shaft_colour(rec):
    u = (rec.get('unidentified_name') or '').lower()
    for k, c in WOODS.items():
        if k in u:
            return c
    return WOOD_LIST[seed(rec, 'w') % len(WOOD_LIST)]


def stick(s, c, x0=5, y0=27, n=17, w=2):
    for i in range(n):
        s.px([(x0 + i + k, y0 - i) for k in range(w)], c)


def wand(rec):
    s = new()
    key = rec['id'].replace('wand_of_', '')
    key2 = key + ' ' + (rec.get('effect') or '')
    motif, c, c2, c3 = family(key2)
    sh = shaft_colour(rec)
    sd = seed(rec)
    stick(s, sh)
    # grip
    grip = shade(sh, -1) if sum(sh) > 300 else shade(sh, 2)
    for i in range(0, 6):
        s.px([(5 + i + k, 27 - i) for k in (-1, 0, 1, 2)], grip)
    trim = (GOLD, SILVER, BRONZE, (90, 80, 110))[sd % 4]
    s.px([(4, 28), (5, 28), (4, 29), (3, 28), (3, 29), (5, 29)], trim)          # pommel
    for i in (6, 7):
        s.px([(5 + i + k, 27 - i) for k in (-1, 0, 1, 2)], trim)               # guard band
    style = (sd >> 4) % 3
    if style == 1:
        s.px([(15, 18), (16, 17), (16, 18)], trim)                                # mid ring
    elif style == 2:
        s.px([(13, 20), (14, 19), (17, 16), (18, 15)], shade(sh, -2))            # knots / twist
    # mount under the tip
    s.px([(20, 12), (21, 12), (21, 11), (22, 11)], trim)
    glow = motif in GLOWING
    cc = s.lit(c) if glow else c
    cc2 = s.lit(c2 or shade(c, 2)) if glow else (c2 or shade(c, 2))
    big = len(MOTIFS[motif]) <= 7 and len(MOTIFS[motif][0]) <= 7
    M(s, motif, 24 if not big else 23, 7 if not big else 8, cc, cc2, c3, scale=1.5 if big else 1)
    mst = (sd >> 12) % 3
    if mst == 1: s.px([(18, 12), (17, 11), (17, 10), (22, 14), (23, 15), (24, 15)], trim)
    elif mst == 2: s.px([(19, 14), (20, 14), (19, 13)], trim)
    tier = rec.get('tier') or (1 + (sd >> 8) % 3)
    if glow and tier >= 3:
        s.px([(17, 4), (29, 13)], cc2)
    if tier >= 4:
        s.px([(9, 24), (10, 23)], s.lit((255, 240, 170)))
    return s.finish()


# ------------------------------------------------------------------ potions
POTION = {  # effect key -> (flask shape, fx)
    'blindness': ('vial', 'smoke'), 'brilliance': ('diamond', 'spark'), 'cold_resistance': ('square', 'flame'),
    'confusion': ('gourd', 'swirl'), 'cure_all': ('round', 'spark'), 'cure_disease': ('square', None),
    'cure_poison': ('vial', 'fizz'), 'drain_constitution': ('cone', None), 'drain_intelligence': ('cone', 'spots'),
    'drain_strength': ('cone', 'smoke'), 'drain_wisdom': ('gourd', 'patch'), 'extra_healing': ('round', 'heart'),
    'fear': ('cone', 'skull'), 'fire_resistance': ('square', 'frost'), 'full_healing': ('heart', 'spark'),
    'fumbling': ('gourd', None), 'gain_level': ('diamond', 'stars'), 'hallucination': ('gourd', 'rainbow'),
    'haste': ('vial', 'fizz'), 'healing': ('round', 'fizz'), 'heroism': ('jar', 'spark'),
    'invisibility': ('vial', 'spark'), 'levitation': ('tear', 'mist'), 'mana': ('tear', 'spark'),
    'paralysis': ('jar', None), 'poison': ('cone', 'ooze'), 'regeneration': ('heart', None),
    'restore_strength': ('jar', 'fizz'), 'shock_resistance': ('square', 'bolt'), 'sickness': ('cone', 'fizz'),
    'sleep': ('jar', 'moon'), 'slow': ('tear', None), 'stamina': ('jar', 'ooze'),
    'teleportation': ('diamond', 'swirl'), 'weakness': ('jar', 'smoke'),
}
ROMAN = {'ii': 2, 'iii': 3, 'iv': 4, 'v': 5}


def flask(s, shape, liquid, level=18, glass=GLASS, cork=CORK):
    """paint glass + liquid; returns the liquid pixel list"""
    g = glass
    neck = True
    if shape == 'round': s.ell(7, 11, 24, 28, g)
    elif shape == 'cone': s.poly([(14, 12), (17, 12), (25, 26), (25, 28), (6, 28), (6, 26)], g)
    elif shape == 'vial':
        s.rect(11, 6, 20, 25, g); s.ell(11, 20, 20, 29, g); neck = False
    elif shape == 'square': s.rect(8, 13, 23, 28, g)
    elif shape == 'heart':
        s.ell(6, 11, 16, 21, g); s.ell(15, 11, 25, 21, g); s.poly([(7, 18), (24, 18), (16, 29), (15, 29)], g)
    elif shape == 'gourd':
        s.ell(11, 9, 20, 18, g); s.ell(7, 16, 24, 29, g)
    elif shape == 'jar':
        s.rect(7, 13, 24, 27, g); s.rect(8, 12, 23, 28, g); neck = False
    elif shape == 'tear':
        s.poly([(15, 9), (16, 9), (24, 21), (23, 26), (19, 29), (12, 29), (8, 26), (7, 21)], g)
    elif shape == 'diamond':
        s.poly([(15, 11), (16, 11), (25, 19), (25, 20), (16, 29), (15, 29), (6, 20), (6, 19)], g)
    px = s.img.load()
    inside = {(x, y) for y in range(32) for x in range(32) if px[x, y][3]}
    liq = [(x, y) for (x, y) in inside if y >= level and all(n in inside for n in ((x - 1, y), (x + 1, y), (x, y + 1)))]
    s.px(liq, liquid)
    if shape == 'vial':
        s.rect(10, 5, 21, 6, shade(g, -1)); s.rect(12, 2, 19, 4, cork)
    elif shape == 'jar':
        s.rect(11, 9, 20, 11, g); s.rect(10, 8, 21, 9, shade(g, -1)); s.rect(11, 4, 20, 7, cork)
    elif neck:
        top = 6 if shape not in ('tear', 'diamond') else 5
        s.rect(14, top + 1, 17, 12 if shape != 'gourd' else 9, g)
        s.rect(13, top, 18, top + 1, shade(g, -1)); s.rect(14, top - 3, 17, top - 1, cork)
    return liq


def potion_fx(s, fx, liq, liquid, sd):
    if not liq: return
    ys = sorted({y for _, y in liq}); top = ys[0]
    xs = sorted(x for x, y in liq if y == top + 2) or [15, 16]
    cx = (xs[0] + xs[-1]) // 2
    hi = shade(liquid, 2)
    if fx == 'fizz':
        s.px([(cx - 2, top - 2), (cx + 1, top - 3), (cx + 3, top - 1), (cx - 1, top + 3), (cx + 2, top + 5)], WHITE)
    elif fx == 'spark':
        c = s.lit((255, 255, 235)); s.px([(cx, top + 3), (cx - 1, top + 4), (cx + 1, top + 4), (cx, top + 5), (cx + 3, top + 1)], c)
    elif fx == 'stars':
        c = s.lit((255, 250, 200)); s.px([(cx - 3, top + 2), (cx + 2, top + 1), (cx, top + 4), (cx + 3, top + 5), (cx - 2, top + 6)], c)
    elif fx == 'smoke':
        c = shade(liquid, 1); s.px([(cx - 1, top - 1), (cx, top - 2), (cx + 1, top - 3), (cx, top - 4)], c)
    elif fx == 'swirl':
        s.px([(cx - 2, top + 2), (cx - 1, top + 1), (cx, top + 1), (cx + 1, top + 2), (cx + 1, top + 3), (cx, top + 4), (cx - 1, top + 4)], hi)
    elif fx == 'rainbow':
        for i, c in enumerate(((255, 90, 90), (255, 220, 80), (90, 220, 120), (90, 170, 255), (255, 255, 255))):
            s.px([(cx - 3 + (i * 5 + sd) % 7, top + 1 + (i * 3) % 6)], s.lit(c))
    elif fx == 'mist':
        s.px([(cx - 2, top - 1), (cx - 1, top - 2), (cx + 1, top - 1), (cx + 2, top - 2), (cx - 1, top + 2), (cx, top + 3), (cx + 1, top + 2)], hi)
    elif fx == 'ooze':
        s.px([(cx - 3, top - 1), (cx - 3, top - 2), (cx + 2, top - 1), (cx, top + 3), (cx + 2, top + 4)], hi)
    elif fx == 'spots':
        s.px([(cx - 2, top + 2), (cx + 1, top + 4), (cx + 2, top + 1), (cx - 1, top + 5)], (120, 150, 70))
    elif fx == 'patch':
        s.rect(cx - 3, top + 2, cx - 1, top + 4, (120, 150, 90)); s.rect(cx + 1, top + 4, cx + 3, top + 6, (190, 90, 70))
    elif fx == 'heart':
        M(s, 'heart', cx, top + 4, (255, 170, 170), WHITE)
    elif fx == 'skull':
        s.px([(cx - 2, top + 2), (cx + 1, top + 2), (cx - 2, top + 3), (cx + 1, top + 3)], (20, 10, 20))
    elif fx == 'frost':
        M(s, 'snow', cx, top + 4, WHITE, WHITE)
    elif fx == 'flame':
        M(s, 'ember', cx, top + 4, s.lit((255, 220, 110)), s.lit((255, 250, 210)))
    elif fx == 'bolt':
        s.px([(cx + 1, top + 1), (cx, top + 2), (cx - 1, top + 3), (cx, top + 3), (cx + 1, top + 3), (cx, top + 4), (cx - 1, top + 5)], s.lit((255, 240, 120)))
    elif fx == 'moon':
        s.px([(cx, top + 1), (cx - 1, top + 2), (cx - 1, top + 3), (cx - 1, top + 4), (cx, top + 5), (cx + 1, top + 5)], WHITE)


def potion(rec):
    s = new()
    pid = rec['id'].replace('potion_of_', '')
    m = re.match(r'(.*)_(ii|iii|iv|v)$', pid)
    tier = 1
    if m: pid, tier = m.group(1), ROMAN[m.group(2)]
    shape, fx = POTION.get(pid, ('round', None))
    c = COLORS.get('potion_of_' + pid) or rec.get('color') or (120, 160, 220)
    liquid = vivid(tuple(c), 80)
    if tier >= 3: liquid = mix(liquid, shade(liquid, 1), 0.5)
    cork = CORK if tier < 4 else (190, 50, 50)
    cork = cork if tier < 5 else GOLD
    liq = flask(s, shape, liquid, level=int(22.5 - 2.5 * tier), cork=cork)
    potion_fx(s, fx, liq, liquid, seed(rec))
    # tier ornament
    nb = {'vial': (10, 8, 21, 9), 'jar': (10, 10, 21, 11)}.get(shape, (13, 9, 18, 10))
    if tier >= 2: s.rect(*nb, SILVER if tier == 2 else GOLD)
    if tier >= 3:
        b = s.lit(shade(liquid, 3))
        ys = sorted({y for _, y in liq}); xs = [x for x, y in liq if y == ys[-3]]
        s.px([(xs[0] + 1, ys[-3]), (xs[-1] - 1, ys[-5])], b)
    if tier >= 4:
        x0 = nb[0]; s.px([(x0 + 1, nb[1] - 1), (x0, nb[3] + 1), (x0, nb[3] + 2)], (190, 50, 50))   # wax drip
    if tier >= 5:
        s.px([(5, 9), (26, 8), (4, 22), (27, 24)], s.lit((255, 245, 180)))
    if tier == 4:
        s.px([(5, 10), (27, 22)], s.lit((255, 245, 180)))
    # glass highlight
    ys = sorted({y for _, y in liq}); xs = sorted(x for x, y in liq if y == ys[len(ys) // 2])
    s.px([(xs[0] + 1, ys[1]), (xs[0] + 1, ys[1] + 1), (xs[0] + 1, ys[1] + 2), (xs[0] + 2, ys[1])], WHITE)
    return s.finish()


# ------------------------------------------------------------------ scrolls
BOSS = {  # id -> (motif, colour, seal colour)
    'anansi': ('spider', (60, 40, 30), (230, 170, 40)), 'arachne': ('web', (90, 80, 110), (150, 80, 200)),
    'baba_yaga': ('hut', (110, 70, 40), (120, 160, 80)), 'cacus': ('flame', (230, 90, 30), (200, 60, 30)),
    'camazotz': ('bat', (60, 40, 70), (90, 50, 120)), 'charybdis': ('whirl', (40, 110, 190), (40, 140, 200)),
    'echidna': ('snake', (110, 60, 130), (160, 70, 160)), 'jormungandr': ('snake', (40, 130, 110), (40, 160, 140)),
    'lamia': ('snake', (190, 60, 70), (220, 110, 130)), 'nidhoggr': ('dragon', (70, 60, 60), (110, 90, 60)),
    'ragnarok': ('flame2', (90, 130, 220), (120, 160, 240)), 'rangda': ('mask', (200, 50, 50), (240, 240, 230)),
    'ravana': ('crown', (200, 150, 30), (220, 60, 40)), 'set': ('horns', (170, 60, 30), (200, 110, 40)),
    'talos': ('gear', (170, 110, 50), (190, 126, 66)), 'the_abyss': ('void', (60, 30, 100), (130, 60, 200)),
    'the_erlking': ('antler', (60, 90, 50), (80, 130, 70)), 'the_gorgon': ('snake', (50, 130, 60), (70, 170, 80)),
    'the_green': ('axe', (40, 130, 60), (50, 160, 70)), 'the_hoard': ('coin', (220, 160, 40), (210, 90, 30)),
    'the_hunt': ('horn', (120, 80, 50), (70, 90, 150)), 'the_labyrinth': ('maze', (150, 70, 45), (180, 80, 50)),
    'the_lion': ('paw', (190, 130, 50), (220, 170, 60)), 'the_pasture': ('horns', (110, 80, 50), (120, 170, 80)),
    'the_sphinx': ('pyramid', (190, 150, 80), (60, 150, 200)), 'the_wendigo': ('antler', (190, 200, 215), (150, 200, 235)),
    'thoth': ('eye', (40, 90, 150), (230, 190, 70)),
}


def scroll(rec):
    s = new()
    key = rec['id'].replace('scroll_of_', '').replace('scroll_', '')
    u = (rec.get('unidentified_name') or '').lower()
    sd = seed(rec)
    boss = key in BOSS
    par = PARCH
    for k, c in (('tea', (196, 160, 110)), ('blood', (216, 110, 100)), ('scorch', (206, 180, 130)), ('calf', (236, 222, 190)),
                 ('onion', (240, 236, 214)), ('silver', (222, 222, 214)), ('water', (206, 206, 176)), ('moth', (214, 200, 150)),
                 ('thumb', (210, 190, 140)), ('copper', (226, 196, 150)), ('gleam', (240, 228, 180))):
        if k in u: par = c
    if boss: par = (238, 222, 170)
    rod = (GOLD if boss else shade(par, -1))
    # parchment
    s.rect(7, 6, 24, 25, par)
    if boss:
        s.rect(4, 3, 27, 6, rod); s.rect(4, 25, 27, 28, rod)
        knob = shade(BOSS[key][2], -1)
        for x in (2, 28):
            s.rect(x, 3, x + 1, 6, knob); s.rect(x, 25, x + 1, 28, knob)
    else:
        s.rect(5, 3, 26, 6, rod); s.rect(5, 25, 26, 28, rod)
        s.px([(5, 4), (5, 5), (26, 4), (26, 5), (5, 26), (5, 27), (26, 26), (26, 27)], shade(par, -2))
    ink = INK
    if boss:
        motif, c, seal = BOSS[key]
        M(s, motif, 15, 13, c, shade(c, 2), None)
        s.px([(10, 20), (11, 20), (12, 20), (14, 20), (15, 20), (17, 20), (18, 20), (19, 20)], ink)
        # ribbon + wax seal
        s.rect(20, 19, 21, 24, shade(seal, -1)); s.ell(18, 21, 24, 27, seal); s.px([(21, 24)], shade(seal, 2))
    else:
        motif, c, c2, c3 = family(key + ' ' + (rec.get('effect') or ''))
        if key == 'dead_sea':
            motif, c, c2, c3 = 'wave', (70, 120, 170), None, None
        dc = mix(c, (60, 40, 40), 0.25) if sum(c) > 520 else c
        M(s, motif, 15, 12, dc, c2 and mix(c2, par, 0.2), c3)
        # glyph lines
        for row, y in enumerate((19, 21, 23)):
            x = 9
            while x < 22:
                ln = 1 + (sd >> (row * 5 + x)) % 3
                s.px([(xx, y) for xx in range(x, min(22, x + ln))], ink); x += ln + 1
        ribbon = vivid(col(rec, c), 90)
        s.rect(22, 1, 24, 8, ribbon); s.px([(22, 9), (24, 9)], ribbon)
        if 'torn' in u: clear(s, 'poly', [(24, 14), (21, 16), (24, 18)]); clear(s, 'poly', [(7, 20), (9, 21), (7, 23)])
        if 'moth' in u: clear(s, 'rect', [9, 9, 10, 10]); clear(s, 'rect', [20, 17, 21, 17]); clear(s, 'rect', [10, 16, 10, 16])
        if 'scorch' in u: s.px([(7, 6), (7, 7), (8, 6), (24, 24), (23, 25), (24, 25), (24, 23), (7, 25), (24, 7)], (60, 40, 30))
        if 'water' in u: s.px([(8, 9), (9, 9), (8, 10), (9, 10), (10, 10), (21, 16), (22, 16), (22, 17)], (150, 180, 200))
        if 'margin' in u: s.px([(8, y) for y in (10, 12, 14, 16)], (170, 60, 50))
    return s.finish()


def dead_sea_scroll(rec):
    s = new()
    clay, par = (176, 110, 72), (214, 196, 150)
    s.ell(5, 12, 20, 29, clay); s.rect(9, 9, 16, 13, clay); s.rect(8, 7, 17, 9, shade(clay, -1))
    s.line([(7, 18), (18, 18)], shade(clay, -1)); s.line([(8, 24), (17, 24)], shade(clay, -1))
    s.px([(9, 15), (9, 16), (10, 14)], shade(clay, 2))
    # scroll leaning out
    s.poly([(17, 3), (21, 2), (28, 20), (24, 22)], par)
    s.rect(15, 2, 22, 4, shade(par, -1))
    s.px([(21, 8), (22, 10), (22, 12), (23, 14), (24, 16), (25, 18)], INK)
    s.px([(20, 6), (22, 7), (24, 13), (25, 15)], (70, 120, 170))
    return s.finish()


# ------------------------------------------------------------------ spellbooks
def book(rec, cover=None, motif=None, mc=None, mc2=None, mc3=None, trim=None, glow=True, slim=False):
    s = new()
    key = rec['id'].replace('spellbook_', '')
    u = (rec.get('unidentified_name') or '').lower()
    sd = seed(rec)
    fm, fc, fc2, fc3 = family(key)
    motif = motif or fm
    if mc is None: mc, mc2, mc3 = fc, fc2, fc3
    if cover is None:
        if rec.get('color'):
            cover = col(rec, None)
            cover = mix(cover, (60, 40, 70), 0.42) if sum(cover) > 420 else vivid(cover, 90)
        else:
            cover = mix(fc, ((50, 40, 70), (70, 40, 40), (40, 60, 60))[sd % 3], 0.6)
        if 'elder' in key: cover = (46, 70, 62)
    if abs(sum(mc) - sum(cover)) < 200:          # keep the emblem readable against the cover
        cover = shade(cover, -1) if sum(mc) > 300 else shade(cover, 1)
        if abs(sum(mc) - sum(cover)) < 160: cover = shade(cover, -1) if sum(mc) > 300 else shade(cover, 1)
    slim = slim or 'slim' in u or 'thin' in u
    x0, x1 = (8, 22) if slim else (6, 24)
    s.rect(x0 + 3, 5, x1 + 2, 29, IVORY)                                # page block
    s.px([(x1 + 2, y) for y in range(7, 29, 2)], shade(IVORY, -2))
    s.rect(x0, 3, x1, 27, cover)
    spine = shade(cover, -1)
    s.rect(x0, 3, x0 + 2, 27, spine)
    metal = GOLD
    if any(k in u for k in ('iron', 'nail', 'hasp', 'chain', 'silver', 'steel')): metal = STEEL
    if 'brass' in u: metal = (214, 170, 80)
    s.line([(x0, 7), (x0 + 2, 7)], metal); s.line([(x0, 23), (x0 + 2, 23)], metal)
    if trim is None:
        for k, t in (('clasp', 'clasp'), ('hasp', 'clasp'), ('chain', 'chain'), ('nail', 'studs'), ('stud', 'studs'),
                     ('gold-edged', 'corners'), ('horn', 'corners'), ('ribbon', 'ribbon'), ('sigil', 'studs'),
                     ('claw', 'claws'), ('twine', 'stitch'), ('ward', 'frame'), ('box', 'frame'), ('rough', 'stitch'),
                     ('crystal', 'spark'), ('prismatic', 'spark'), ('shimmer', 'spark'), ('radiant', 'spark'),
                     ('veined', 'veins'), ('marbled', 'veins'), ('flecked', 'veins'), ('wormholed', 'holes')):
            if k in u: trim = t; break
        else:
            trim = ('frame', 'corners', 'clasp', 'plain', 'studs', 'ribbon')[(sd >> 3) % 6]
    cx = (x0 + 3 + x1) // 2 + 0
    a, b = x0 + 4, x1 - 1
    if trim == 'corners':
        for px_, py_, dx, dy in ((b, 4, -1, 1), (b, 26, -1, -1), (a, 4, 1, 1), (a, 26, 1, -1)):
            s.px([(px_, py_), (px_ + dx, py_), (px_, py_ + dy), (px_ + 2 * dx, py_), (px_, py_ + 2 * dy)], metal)
    elif trim == 'frame':
        lc = shade(cover, 2)
        s.line([(a, 5), (b, 5)], lc); s.line([(a, 25), (b, 25)], lc); s.line([(a, 5), (a, 25)], lc); s.line([(b, 5), (b, 25)], lc)
    elif trim == 'studs':
        s.px([(a, 5), (b, 5), (a, 25), (b, 25), (cx, 5), (cx, 25)], metal)
    elif trim == 'stitch':
        s.px([(a, y) for y in range(5, 26, 3)] + [(b, y) for y in range(6, 26, 3)], PARCH)
    elif trim == 'claws':
        for dx in (0, 3, 6): s.line([(a + dx + 3, 19), (a + dx, 25)], shade(cover, -2))
    elif trim == 'veins':
        v = shade(mc, 0)
        s.px([(a, 6), (a + 1, 7), (a + 1, 8), (b, 22), (b - 1, 23), (b - 1, 24), (b - 2, 25), (b, 7), (a + 1, 23), (a, 24)], v)
    elif trim == 'holes':
        s.px([(a, 6), (b, 9), (a + 1, 23), (b - 1, 24), (b, 20)], shade(cover, -2))
    elif trim == 'spark':
        s.px([(a, 5), (b, 8), (a + 1, 24), (b - 1, 22)], s.lit((255, 255, 240)))
    em = s.lit(mc) if glow else mc
    em2 = s.lit(mc2 or shade(mc, 2)) if glow else (mc2 or shade(mc, 2))
    M(s, motif, cx + 1, 14, em, em2, mc3)
    if trim == 'clasp':
        s.rect(x1 - 2, 19, x1 + 2, 21, LEATHER); s.rect(x1 - 1, 19, x1, 21, metal)
    elif trim == 'chain':
        chain(s, [(x0, 20), (x1 + 2, 20)], STEEL, IRON); chain(s, [(x0, 9), (x1 + 2, 9)], STEEL, IRON)
        s.rect(cx, 19, cx + 2, 22, metal)
    elif trim == 'ribbon':
        rc = (200, 50, 70) if 'plum' not in u else (150, 60, 150)
        s.rect(cx + 3, 27, cx + 4, 30, rc)
    return s.finish()


# ------------------------------------------------------------------ chests
def chest(rec):
    s = new()
    i = rec['id']
    wood = col(rec, WOOD)
    band, lockc = IRON, GOLD
    if i == 'dragon_hoard':
        gold, red = (240, 190, 50), (150, 50, 40)
        s.poly([(2, 28), (6, 20), (11, 15), (16, 12), (22, 15), (27, 21), (29, 28)], gold)
        s.rect(10, 8, 22, 16, red); s.rect(10, 6, 22, 9, shade(red, -1)); s.rect(15, 11, 17, 14, GOLD)
        for x, y in ((5, 24), (9, 20), (13, 24), (19, 20), (23, 25), (17, 26), (25, 22), (8, 26)):
            s.ell(x, y, x + 2, y + 2, (255, 225, 110))
        s.rect(20, 23, 22, 25, s.lit((90, 220, 255))); s.rect(11, 18, 12, 19, s.lit((255, 80, 120)))
        s.px([(4, 27), (27, 26), (15, 22)], s.lit((255, 255, 220)))
        return s.finish()
    vault = 'vault' in i
    if vault:
        body = (120, 150, 180) if i == 'steel_vault' else (100, 104, 130)
        s.rect(4, 5, 27, 28, body); s.rect(7, 8, 24, 25, shade(body, 1))
        s.px([(5, 6), (26, 6), (5, 27), (26, 27), (5, 16), (26, 16)], STEEL)
        s.rect(3, 10, 4, 13, IRON); s.rect(3, 20, 4, 23, IRON)
        s.ell(11, 12, 20, 21, IRON); s.ell(13, 14, 18, 19, STEEL)
        s.line([(9, 16), (22, 16)], IRON); s.line([(15, 10), (15, 23)], IRON); s.rect(15, 16, 16, 17, GOLD)
        if 'shock' in i:
            b = s.lit((150, 200, 255)); w = s.lit((240, 250, 255))
            s.line([(6, 2), (9, 6), (7, 8), (10, 12)], b); s.line([(25, 3), (22, 8), (25, 10), (22, 14)], b)
            s.line([(20, 24), (24, 27), (22, 29)], b); s.px([(9, 6), (22, 8), (24, 27)], w)
        return s.finish()
    if i == 'iron_chest': wood, band = (140, 144, 160), (90, 94, 110)
    if i == 'cursed_coffer': wood, band, lockc = (70, 50, 90), (40, 34, 50), s.lit((190, 90, 255))
    if i == 'enchanted_coffer': wood, band, lockc = (120, 80, 170), GOLD, s.lit((140, 240, 255))
    if i == 'inferno_chest': wood, band = (120, 50, 40), (60, 40, 40)
    small = 'coffer' in i
    x0, x1, y0 = (6, 25, 10) if small else (3, 28, 8)
    s.rect(x0, y0 + 7, x1, 27, wood)                                   # body
    lid = shade(wood, 1) if sum(wood) < 500 else shade(wood, -1)
    s.rect(x0, y0 + 2, x1, y0 + 6, lid); s.rect(x0 + 2, y0, x1 - 2, y0 + 2, lid)   # arched lid
    if i in ('wooden_chest', 'trapped_chest', 'spiked_chest'):
        for y in (y0 + 11, y0 + 15): s.line([(x0 + 1, y), (x1 - 1, y)], shade(wood, -1))
    for x in (x0 + 3, x1 - 4):
        s.rect(x, y0, x + 1, 27, band)
    s.line([(x0, y0 + 7), (x1, y0 + 7)], band)
    s.rect(14, y0 + 6, 17, y0 + 10, lockc); s.px([(15, y0 + 8), (16, y0 + 8), (15, y0 + 9)], DARK if lockc not in s.glow else WHITE)
    s.rect(x0, 28, x0 + 2, 29, band); s.rect(x1 - 2, 28, x1, 29, band)
    if i == 'spiked_chest':
        for x in (6, 11, 16, 21, 25):
            s.poly([(x - 1, y0 - 1), (x, y0 - 5), (x + 1, y0 - 1)], STEEL)
        for y in (17, 22):
            s.poly([(x0 - 1, y), (x0 - 3, y + 1), (x0 - 1, y + 2)], STEEL); s.poly([(x1 + 1, y), (x1 + 3, y + 1), (x1 + 1, y + 2)], STEEL)
    if i == 'trapped_chest':
        s.line([(18, y0 + 8), (27, y0 + 3)], (220, 210, 190)); s.px([(28, y0 + 2), (29, y0 + 2)], RED)
        s.px([(8, 20), (9, 20), (22, 22), (23, 22)], DARK)     # dart holes
    if i == 'inferno_chest':
        f = s.lit((255, 130, 40)); h = s.lit((255, 230, 110))
        s.rect(x0 + 1, y0 + 6, x1 - 1, y0 + 6, f)
        for x in (6, 11, 20, 25):
            s.poly([(x - 2, y0 - 1), (x, y0 - 6), (x + 2, y0 - 1)], f); s.px([(x, y0 - 2), (x, y0 - 3)], h)
        s.px([(8, 20), (22, 22), (12, 24), (19, 18)], f)
    if i == 'cursed_coffer':
        g = lockc; s.px([(4, 8), (3, 12), (27, 9), (28, 14), (9, 6), (22, 5), (16, 4)], g)
        s.px([(10, 21), (11, 21), (20, 21), (21, 21)], g)
    if i == 'enchanted_coffer':
        g = lockc; M(s, 'star4', 9, 5, g, s.lit(WHITE)); s.px([(24, 5), (27, 12), (3, 16), (22, 3)], g)
    return s.finish()
