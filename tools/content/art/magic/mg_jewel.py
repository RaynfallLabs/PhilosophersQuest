"""Ring and amulet rigs + the spec tables for stat/resist families and described accessories."""
import math, re
from mg_common import *

# material -> (band colour, gem colour or None, glow, style)
MAT = {
    'adamantine': ((92, 72, 184), None, False, 'thick'), 'iron': (IRON, None, False, 'plain'),
    'mithril': ((196, 226, 244), None, True, 'plain'), 'steel': (STEEL, None, False, 'plain'),
    'dragonbone': ((214, 204, 176), None, False, 'thick'), 'gold': (GOLD, None, False, 'plain'),
    'carnelian': (GOLD, (226, 96, 50), False, 'plain'), 'coral': (SILVER, (250, 134, 124), False, 'plain'),
    'garnet': (BRONZE, (150, 30, 54), False, 'plain'), 'ruby': (GOLD, (232, 40, 64), True, 'plain'),
    'diamond': (SILVER, (210, 245, 255), True, 'plain'),
    'featherweight': ((236, 236, 244), None, False, 'thin'), 'quicksilver': ((200, 214, 224), (236, 244, 252), True, 'plain'),
    'spun_glass': ((176, 226, 236), (226, 250, 255), False, 'thin'), 'thin_wire': (COPPER, None, False, 'thin'),
    'amethyst': (SILVER, (170, 90, 224), False, 'plain'), 'arcane_pewter': ((130, 130, 152), (160, 130, 255), True, 'plain'),
    'prismatic': (SILVER, (255, 255, 255), True, 'rainbow'), 'purple_glass': (BRONZE, (196, 130, 236), False, 'plain'),
    'amber': (BRONZE, (242, 164, 44), False, 'plain'), 'citrine': (GOLD, (250, 228, 96), False, 'plain'),
    'hawks_eye': (IRON, (196, 154, 64), False, 'plain'), 'topaz': (SILVER, (255, 190, 96), False, 'plain'),
    'eagle_eye': (GOLD, (240, 200, 60), False, 'plain'), 'hawk_feather': (LEATHER, (190, 150, 100), False, 'plain'),
    'emerald': (GOLD, (40, 204, 104), True, 'plain'), 'living_wood': ((124, 92, 52), (116, 204, 84), False, 'twist'),
    'peridot': (SILVER, (176, 232, 74), False, 'plain'), 'serpentine': ((84, 132, 92), (160, 200, 120), False, 'twist'),
    'verdant_jade': ((96, 184, 124), (150, 230, 160), False, 'plain'), 'jade': ((96, 184, 124), (150, 230, 160), False, 'plain'),
    'carved_jade': ((110, 190, 140), None, False, 'notch'),
    'engraved_pewter': ((140, 142, 158), None, False, 'notch'), 'gleaming_iron': ((156, 162, 180), None, False, 'plain'),
    'malachite': ((40, 150, 112), None, False, 'banded'), 'mossy_stone': ((124, 130, 116), (110, 170, 70), False, 'moss'),
    'pale_ivory': (IVORY, None, False, 'plain'), 'polished_crystal': ((190, 230, 246), (235, 250, 255), True, 'plain'),
    'silver': (SILVER, None, False, 'plain'), 'cobalt_blue': ((44, 84, 204), None, False, 'plain'),
    'dark_obsidian': ((44, 40, 60), (120, 100, 190), False, 'plain'), 'lapis_lazuli': ((40, 72, 172), (230, 190, 70), False, 'fleck'),
    'moonstone': (SILVER, (224, 234, 255), True, 'plain'), 'sapphire': (SILVER, (54, 114, 242), True, 'plain'),
    'twilight_crystal': ((112, 92, 172), (176, 146, 255), True, 'plain'),
    'ancient_copper': (COPPER, (90, 180, 150), False, 'moss'), 'copper': (COPPER, None, False, 'plain'),
    'bone': (BONE, None, False, 'notch'), 'bronze': (BRONZE, None, False, 'plain'),
    'grey_granite': ((136, 136, 146), None, False, 'fleck'), 'oak': ((150, 108, 60), None, False, 'twist'),
    'rough_stone': ((120, 112, 104), None, False, 'thick'), 'runed_metal': ((110, 116, 140), (120, 230, 255), True, 'runes'),
    'twisted_iron': ((96, 100, 114), None, False, 'twist'),
    'sage_ivory': (IVORY, (150, 200, 130), False, 'plain'), 'ivory': (IVORY, None, False, 'plain'),
    'opal': (SILVER, (224, 242, 236), True, 'plain'), 'pearl': (GOLD, (246, 240, 236), False, 'plain'),
    'white_quartz': ((232, 234, 242), None, False, 'plain'),
    'air_light': ((226, 240, 250), (255, 255, 255), False, 'thin'), 'crystal': (SILVER, (200, 240, 255), True, 'plain'),
    'titan_iron': ((84, 88, 104), None, False, 'thick'),
    'fire_res_a': (GOLD, (255, 120, 40), True, 'plain'), 'fire_res_b': (IRON, (255, 90, 60), True, 'plain'),
    'cold_res_a': (SILVER, (150, 215, 255), True, 'plain'), 'cold_res_b': ((80, 110, 170), (230, 245, 255), True, 'plain'),
    'shock_res_a': (COPPER, (250, 236, 96), True, 'plain'), 'shock_res_b': (STEEL, (150, 200, 255), True, 'plain'),
    'poison_res_a': (SILVER, (110, 210, 90), False, 'plain'), 'poison_res_b': (BRONZE, (170, 80, 210), False, 'plain'),
    'sleep_res_a': (GOLD, (240, 240, 200), True, 'plain'), 'sleep_res_b': ((70, 70, 130), (180, 190, 255), True, 'plain'),
}
MAT_KEYS = sorted(MAT, key=len, reverse=True)

# power -> (motif, default colour or None=band)
POWER = {'strength': ('fist', None), 'constitution': ('heart', (220, 60, 70)), 'dexterity': ('feather', (240, 240, 245)),
         'intellect': ('star4', (190, 150, 255)), 'perception': ('cateye', (90, 170, 220)), 'wisdom': ('sun', (250, 240, 190)),
         'regen': ('leaf', (110, 210, 100)), 'searching': ('lens', None), 'telepathy': ('spiral', (150, 170, 255)),
         'warning': ('bell', None), 'fire_res': ('flame', (255, 120, 40)), 'cold_res': ('snow', (170, 220, 255)),
         'shock_res': ('bolt', (250, 236, 96)), 'poison_res': ('drop', (110, 210, 90)), 'sleep_res': ('moon', (200, 200, 255)),
         'protection': ('shield', None), 'speed': ('wing', (240, 240, 250)), 'sustenance': ('wheat', (240, 200, 90))}

GEO = {'plain': ((6, 13, 25, 28), (9, 16, 22, 24)), 'thick': ((5, 12, 26, 29), (10, 17, 21, 23)),
       'thin': ((7, 14, 24, 27), (9, 15, 22, 25)),
       'low': ((7, 16, 24, 29), (10, 19, 21, 25)), 'lowthick': ((6, 15, 25, 29), (11, 20, 20, 24)),
       'lowthin': ((7, 17, 24, 29), (9, 19, 22, 27))}


_G = [None]


def band_pts(n, rx=None, ry=None, cx=None, cy=None):
    o, h = _G[0]
    cx = (o[0] + o[2]) / 2; cy = (o[1] + o[3]) / 2 + 0.1
    rx = rx or ((o[2] - o[0]) + (h[2] - h[0])) / 4; ry = ry or ((o[3] - o[1]) + (h[3] - h[1])) / 4
    return [(round(cx + rx * math.cos(2 * math.pi * k / n)), round(cy + ry * math.sin(2 * math.pi * k / n))) for k in range(n)]


def ring(band, top=None, tc=None, tc2=None, tc3=None, style='plain', glow=False, bezel=True, deco=None, dc=None, ts=1, low=False):
    s = new()
    g = GEO['thick' if style in ('thick',) else 'thin' if style in ('thin', 'hollow') else 'plain']
    if low: g = GEO['lowthick' if style == 'thick' else 'lowthin' if style in ('thin', 'hollow') else 'low']
    _G[0] = g
    s.ell(*g[0], band)
    clear(s, 'ell', list(g[1]))
    px = s.img.load()
    onband = lambda p: 0 <= p[0] < 32 and 0 <= p[1] < 32 and px[p[0], p[1]][3]
    deco = deco or style
    if deco == 'twist':
        for x, y in band_pts(14):
            if onband((x, y)): s.px([(x, y)], shade(band, -2))
    elif deco in ('banded', 'stripe'):
        c2 = dc or shade(band, 2)
        for k, (x, y) in enumerate(band_pts(40)):
            if (k // 4) % 2 == 0:
                for p in ((x, y), (x, y + 1), (x, y - 1)):
                    if onband(p): s.px([p], c2)
    elif deco == 'rainbow':
        cs = [(255, 100, 100), (255, 200, 90), (120, 230, 120), (100, 190, 255), (190, 130, 255)]
        for k, (x, y) in enumerate(band_pts(60)):
            for p in ((x, y), (x, y + 1), (x, y - 1), (x + 1, y)):
                if onband(p): s.px([p], cs[(k // 6) % 5])
    elif deco == 'notch':
        for x, y in band_pts(10)[1:5] + band_pts(10)[6:]:
            if onband((x, y)): s.px([(x, y)], shade(band, -2))
    elif deco == 'moss':
        c2 = dc or (110, 170, 70)
        for x, y in band_pts(9)[0:5]:
            for p in ((x, y), (x + 1, y)):
                if onband(p): s.px([p], c2)
    elif deco == 'fleck':
        c2 = dc or shade(band, 3)
        for x, y in band_pts(7):
            if onband((x, y)): s.px([(x, y)], c2)
    elif deco == 'runes':
        c2 = s.lit(dc or (120, 230, 255))
        for x, y in band_pts(8)[0:5]:
            if onband((x, y + 1)): s.px([(x, y + 1)], c2)
    elif deco == 'hollow':
        for x, y in band_pts(24):
            if onband((x, y)) and y > 20: s.px([(x, y)], shade(band, -2))
    elif deco == 'crack':
        s.px([(8, 22), (9, 23), (9, 24), (10, 25), (22, 24), (23, 23)], dc or DARK)
    elif deco == 'shine':
        s.px([(9, 23), (10, 24), (11, 25)], WHITE)
    top_y = g[0][1]
    if top is None:
        return s
    gc = tc or shade(band, 1)
    if glow: gc = s.lit(gc)
    g2 = tc2 or shade(gc, 2)
    if glow: g2 = s.lit(g2)
    if top in ('round', 'square', 'diamond', 'oval', 'small'):
        if bezel: s.rect(12, top_y - 1, 19, top_y + 1, band)
        if top == 'round': s.ell(12, top_y - 8, 19, top_y - 1, gc)
        elif top == 'square': s.rect(12, top_y - 7, 19, top_y - 1, gc)
        elif top == 'oval': s.ell(10, top_y - 6, 21, top_y, gc)
        elif top == 'small': s.ell(13, top_y - 5, 18, top_y, gc)
        else: s.poly([(15, top_y - 9), (16, top_y - 9), (20, top_y - 5), (16, top_y), (15, top_y), (11, top_y - 5)], gc)
        s.px([(14, top_y - 5), (14, top_y - 4), (15, top_y - 6)] if top != 'small' else [(15, top_y - 3)], g2 if glow else WHITE)
    elif top == 'signet':
        s.ell(9, top_y - 7, 22, top_y + 3, band)
        s.ell(11, top_y - 5, 20, top_y + 1, gc)
    else:
        h = round(len(MOTIFS[top]) * ts)
        if bezel: s.rect(13, top_y, 18, top_y + 1, band)
        M(s, top, 16, top_y - h + h // 2, gc, g2, tc3, scale=ts)
    return s


def stat_ring(rec):
    i = rec['id'][5:]
    power = next((p for p in sorted(POWER, key=len, reverse=True) if i.startswith(p)), None)
    rest = i[len(power) + 1:] if power else i
    mk = next((k for k in MAT_KEYS if k in i), None)
    band, gem, glow, style = MAT.get(mk, (GOLD, None, False, 'plain'))
    motif, pc = POWER.get(power, ('round', None))
    tc = gem or pc or shade(band, 1)
    tc2 = tc3 = None
    if motif == 'cateye': tc3 = (30, 24, 30)
    if motif == 'lens': tc, tc2, tc3 = shade(band, 1), (176, 226, 250), shade(band, -1)
    if motif == 'feather': tc3 = shade(band, -1)
    if motif == 'leaf': tc3 = shade(band, -1)
    if motif == 'fist' and style == 'plain': style = 'thick'
    deco = style if style not in ('thick', 'thin', 'plain') else None
    if mk in ('lapis_lazuli', 'mossy_stone', 'ancient_copper') : deco = MAT[mk][3]
    dc = gem if deco in ('moss', 'fleck', 'runes') else None
    if deco in ('moss', 'fleck') and not pc: tc = shade(band, 1)
    s = ring(band, motif, tc, tc2, tc3, style=style if style in GEO else 'plain', glow=glow and motif not in ('cateye', 'lens', 'fist', 'bell', 'shield'),
             deco=deco, dc=dc, ts=1.5, low=True)
    if mk == 'opal': s.px([(14, 9), (18, 12)], (255, 150, 190)); s.px([(17, 8), (13, 12)], (130, 200, 255))
    return s.finish()


# ------------------------------------------------------------------ amulets
FORMS = {'locket': 'locket', 'pendant': 'tear', 'charm': 'disc', 'talisman': 'tri', 'medallion': 'disc'}


def amu(chain_c=SILVER, cord=False, low=12, wide=False):
    s = new()
    a, b = ((5, 1), (26, 1)) if wide else ((8, 1), (23, 1))
    if cord:
        s.line([a, (15, low)], chain_c); s.line([b, (16, low)], chain_c)
    else:
        chain(s, [a, (15, low)], chain_c); chain(s, [b, (16, low)], chain_c)
    return s


def pendant(s, shape, body, rim=None, glow=False):
    c = s.lit(body) if glow else body
    rim = rim or shade(body, -1)
    if shape == 'disc':
        s.ell(9, 13, 22, 26, rim); s.ell(11, 15, 20, 24, c)
    elif shape == 'bigdisc':
        s.ell(7, 11, 24, 28, rim); s.ell(9, 13, 22, 26, c)
    elif shape == 'locket':
        s.ell(10, 12, 21, 27, c); s.px([(10, 19), (10, 20), (21, 19), (21, 20)], rim); s.rect(15, 11, 16, 12, rim)
    elif shape == 'tear':
        s.poly([(15, 12), (16, 12), (21, 21), (20, 25), (17, 27), (14, 27), (11, 25), (10, 21)], c)
        s.px([(15, 11), (16, 11)], rim); s.px([(13, 20), (13, 21), (14, 18)], shade(body, 3))
    elif shape == 'gem':
        s.poly([(11, 13), (20, 13), (23, 17), (16, 27), (15, 27), (8, 17)], c)
        s.line([(9, 17), (22, 17)], shade(body, 2) if not glow else s.lit(shade(body, 2)))
        s.px([(12, 15), (13, 15)], WHITE)
    elif shape == 'crystal':
        s.poly([(14, 12), (17, 12), (20, 16), (20, 23), (16, 28), (15, 28), (11, 23), (11, 16)], c)
        s.line([(15, 13), (15, 26)], s.lit(shade(body, 2)) if glow else shade(body, 2)); s.px([(13, 16), (13, 17)], WHITE)
    elif shape == 'tri':
        s.poly([(15, 12), (16, 12), (24, 26), (7, 26)], c)
    elif shape == 'square':
        s.rect(9, 13, 22, 27, rim); s.rect(11, 15, 20, 25, c)
    elif shape == 'heart':
        s.ell(8, 13, 16, 21, c); s.ell(15, 13, 23, 21, c); s.poly([(9, 19), (22, 19), (16, 28), (15, 28)], c)
        s.px([(11, 16), (11, 17), (12, 15)], shade(body, 3))
    elif shape == 'shard':
        s.poly([(14, 12), (18, 13), (22, 19), (19, 22), (20, 28), (14, 25), (10, 20), (12, 16)], c)
        s.line([(15, 14), (17, 20), (16, 25)], shade(body, 2))
    elif shape == 'rock':
        s.poly([(12, 13), (19, 12), (23, 17), (22, 24), (17, 28), (11, 26), (8, 20)], c)
    elif shape == 'tooth':
        s.poly([(12, 12), (19, 12), (20, 17), (18, 23), (15, 29), (14, 24), (12, 18)], c); s.rect(12, 11, 19, 13, rim)
    elif shape == 'bell':
        s.poly([(14, 12), (17, 12), (20, 16), (21, 23), (23, 25), (8, 25), (10, 23), (11, 16)], c)
        s.rect(14, 26, 17, 28, rim); s.line([(9, 24), (22, 24)], rim)
    elif shape == 'phial':
        s.rect(12, 14, 19, 27, GLASS); s.rect(13, 19, 18, 26, c); s.rect(13, 11, 18, 13, CORK); s.px([(13, 16), (13, 17)], WHITE)
    return c


def stat_amulet(rec):
    i = rec['id'][7:]
    power = next((p for p in sorted(POWER, key=len, reverse=True) if i.startswith(p)), None)
    mk = next((k for k in MAT_KEYS if k in i), None)
    band, gem, glow, _ = MAT.get(mk, (GOLD, None, False, 'plain'))
    form = next((FORMS[f] for f in FORMS if i.endswith(f)), None)
    if form is None:
        form = ('disc', 'square', 'tri', 'tear', 'locket')[seed(rec) % 5]
    motif, pc = POWER.get(power, ('star4', None))
    chain_c = band if sum(band) > 380 else SILVER
    if mk in ('bone', 'hawk_feather', 'jade'): chain_c = LEATHER
    s = amu(chain_c, cord=chain_c == LEATHER)
    body = band if form in ('disc', 'locket', 'square', 'tri') else (gem or band)
    pendant(s, form, body, glow=glow and form in ('tear', 'gem'))
    mc = gem or pc or shade(band, 2)
    if form in ('tear', 'gem'): mc = pc and mix(pc, WHITE, 0.5) or WHITE
    if sum(mc) - sum(body) < 90 and sum(mc) > sum(body) - 90: mc = shade(body, -2) if sum(body) > 380 else shade(body, 3)
    c2 = c3 = None
    if motif == 'cateye': motif = 'eye'
    if motif == 'eye': mc, c2, c3 = shade(body, -2), (250, 248, 236), gem or pc
    if motif == 'lens': c2, c3 = (176, 226, 250), shade(body, -2)
    cy = 20 if form != 'tri' else 22
    if form == 'tri' and len(MOTIFS[motif][0]) > 7: cy = 23
    M(s, motif, 16, cy, mc, c2, c3)
    return s.finish()
