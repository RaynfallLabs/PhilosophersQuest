"""Individually designed things: described rings/amulets, legend accessories, artifacts, named wands/potions/books."""
from mg_common import *
from mg_jewel import ring, amu, pendant
from mg_rigs import book, flask, stick, potion_fx

NAMED = {}


def named(*ids):
    def deco(f):
        for i in ids: NAMED[i] = f
        return f
    return deco


def R(i, *a, post=None, **k):
    if post is None and len(a) > 1 and a[1] in MOTIFS:
        k.setdefault('ts', 1.5); k.setdefault('low', True)

    def f(rec):
        s = ring(*a, **k)
        if post: post(s)
        return s.finish()
    NAMED[i] = f


def A(i, shape, body, motif=None, mc=None, mc2=None, mc3=None, chain_c=SILVER, cord=False, glow=False, mglow=False,
      rim=None, post=None, cy=20):
    def f(rec):
        s = amu(chain_c, cord)
        pendant(s, shape, body, rim, glow)
        if motif:
            c = s.lit(mc) if mglow else mc
            M(s, motif, 16, cy, c, s.lit(mc2) if (mglow and mc2) else mc2, mc3)
        if post: post(s)
        return s.finish()
    NAMED[i] = f


RG = (232, 150, 110)      # red-gold
BRASS = (214, 170, 70)
OBS = (46, 42, 62)
JADE = (100, 190, 130)
CLAY = (176, 120, 84)

# ---- described rings ---------------------------------------------------
R('aesops_quill', GOLD, 'feather', (250, 246, 230), tc3=(90, 70, 50), ts=1.5, low=True)
R('andvaranaut', (255, 215, 80), None, style='thick', deco='shine', post=lambda s: s.px([(22, 12), (23, 11), (24, 12), (23, 13), (23, 10), (23, 14)], s.lit((255, 250, 190))))
R('anklet_of_atalanta', (206, 232, 214), 'wing', (245, 250, 245), style='thin', post=lambda s: s.px([(3, 19), (2, 21), (4, 23)], (245, 250, 245)))
R('crown_of_croesus', GOLD, 'crown', (240, 200, 70), (230, 60, 80), post=lambda s: s.px([(7, 22), (8, 24), (23, 24)], shade(GOLD, -2)))
R('dragonslayer_ring', (220, 170, 60), 'dragon', (220, 70, 40), (255, 230, 120), deco='moss', dc=(60, 44, 40))
R('elaras_silver_ring', (196, 198, 214), None, deco='shine', post=lambda s: M(s, 'heart', 16, 26, (150, 152, 172), (150, 152, 172)))
R('officers_signet', (222, 182, 60), 'signet', (170, 40, 40), style='thick', post=lambda s: M(s, 'crown', 16, 10, (240, 210, 100), (240, 210, 100)))
R('philosophers_ring', (220, 210, 130), 'small', (210, 50, 50), deco='notch', glow=True)
R('philosophers_ring_legendary', (150, 150, 190), 'eye', (70, 60, 110), (240, 240, 255), (190, 130, 255), deco='fleck', dc=(200, 180, 255))
R('ring_clairvoy', (50, 46, 64), 'eye', (30, 28, 40), (240, 240, 235), (120, 110, 200), deco='banded', dc=(220, 220, 225))
R('ring_constitution_diamond', SILVER, 'diamond', (206, 245, 255), glow=True)
R('ring_curse_aggravate', BRASS, 'round', (230, 50, 70), style='thick',
  post=lambda s: (s.ell(6, 8, 10, 12, (60, 200, 110)), s.ell(21, 8, 25, 12, (70, 130, 240)), s.px([(7, 9), (22, 9)], WHITE)))
R('ring_curse_drain', (110, 60, 160), 'small', (200, 220, 255), style='thin', glow=True)
R('ring_curse_fumble', (112, 114, 126), None, style='thick', post=lambda s: s.px([(8, 25), (9, 26), (22, 26), (13, 28)], (84, 86, 98)))
R('ring_curse_slow', (58, 56, 70), None, style='thick', post=lambda s: s.px([(7, 21), (12, 26), (19, 26), (24, 21), (15, 14), (16, 14)], STEEL))
R('ring_curse_teleport', (176, 110, 84), 'oval', (200, 130, 100), deco='banded', dc=(226, 190, 160),
  post=lambda s: s.line([(13, 8), (15, 10), (14, 12), (17, 13)], DARK))
R('ring_displace', OBS, None, deco='shine', post=lambda s: (clear(s, 'poly', [(22, 13), (26, 16), (23, 18)]), s.px([(12, 14), (13, 14), (14, 13)], (150, 140, 200))))
R('ring_drain_res_a', (176, 62, 50), None, style='thick', deco='fleck', dc=(110, 30, 30))
R('ring_hasted', (230, 110, 150), None, deco='banded', dc=(90, 200, 120), post=lambda s: s.px([(2, 16), (3, 16), (1, 20), (2, 20), (3, 24), (4, 24)], (240, 230, 80)))
R('ring_intellect_prismatic_deep', (120, 110, 170), 'burst', (255, 255, 255), (190, 150, 255), style='thick', deco='rainbow', glow=True, low=True)
R('ring_invisible', (206, 232, 244), None, style='thin', post=lambda s: s.px([(8, 17), (12, 26), (22, 15), (26, 11), (5, 11)], s.lit((255, 255, 255))))
R('ring_levitate', (206, 208, 236), None, style='hollow', post=lambda s: s.px([(11, 30), (16, 30), (20, 30), (13, 10), (18, 9)], (170, 190, 240)))
R('ring_magic_res_a', (146, 140, 170), None, deco='notch', post=lambda s: s.px([(7, 18), (8, 19), (22, 25), (23, 24)], (220, 215, 235)))
R('ring_of_command', (255, 220, 60), 'crown', (255, 220, 60), (60, 120, 230), style='thick')
R('ring_of_displacement', SILVER, 'oval', (170, 172, 186), post=lambda s: s.px([(12, 9), (13, 10), (15, 10), (16, 9), (18, 10), (19, 11)], (225, 228, 240)))
R('ring_of_eluned', (90, 160, 100), 'leaf', (130, 210, 120), tc3=(60, 110, 70), deco='twist')
R('ring_of_far_sight', GOLD, 'eye', (120, 90, 40), (240, 250, 230), (60, 200, 110))
R('ring_of_gawain', (90, 170, 110), 'sun', (255, 215, 90), (255, 240, 170), glow=True)
R('ring_of_gyges', (160, 160, 184), None, post=lambda s: [s.px([p], (200, 200, 220)) for k, p in enumerate(
    [(3, 17), (3, 21), (4, 24), (27, 15), (28, 19), (28, 23), (9, 30), (14, 30), (20, 30), (10, 11), (16, 11), (21, 11)])])
R('ring_of_hypatia', BRONZE, 'tri', (226, 190, 110), style='thin', post=lambda s: s.px([(15, 11), (16, 11), (16, 12)], DARK))
R('ring_of_iron_grip', (96, 92, 100), 'fist', (120, 116, 126), style='thick', post=lambda s: s.px([(8, 26), (23, 25)], (170, 80, 60)))
R('ring_of_lancelot', RG, 'signet', (250, 205, 195), post=lambda s: M(s, 'tower', 16, 8, (170, 60, 60), WHITE))
R('ring_of_odysseus', (160, 120, 70), 'signet', (200, 220, 230), post=lambda s: M(s, 'ship', 16, 8, (110, 70, 40), (110, 70, 40)))
R('ring_of_percival', (214, 224, 240), 'cup', (236, 242, 252), (255, 255, 255))
R('ring_of_pythia', BRONZE, 'leaf', (120, 170, 90), tc3=(80, 110, 60), post=lambda s: s.px([(20, 5), (21, 3), (22, 2), (12, 4), (11, 2)], (210, 210, 200)))
R('ring_of_scheherazade', GOLD, 'round', (170, 200, 255), glow=True, post=lambda s: s.px([(14, 8), (15, 7), (16, 7), (17, 8), (17, 9), (16, 10), (15, 10)], s.lit((240, 245, 255))))
R('ring_of_the_assassin', (50, 50, 70), 'signet', (30, 30, 46), post=lambda s: M(s, 'dagger', 16, 8, (210, 214, 230), None, (170, 60, 60)))
R('ring_of_the_deep', (40, 110, 190), 'drop', (110, 210, 255), (230, 250, 255), glow=True, deco='stripe', dc=(70, 160, 230))
R('ring_of_the_nibelung', (214, 160, 50), None, style='thick', post=lambda s: s.px([(15, 13), (15, 14), (15, 15), (16, 14), (17, 13), (16, 16)], s.lit((255, 90, 60))))
R('ring_of_thunder', IRON, 'square', (150, 150, 160), post=lambda s: (s.px([(14, 9), (16, 8), (17, 11)], (110, 110, 122)),
  s.line([(22, 3), (24, 6), (23, 7), (25, 10)], s.lit((180, 210, 255))), s.line([(9, 2), (7, 5), (9, 6)], s.lit((180, 210, 255)))))
R('ring_protection_adamantine', (88, 68, 178), 'shield', (120, 100, 210), (190, 180, 250), style='thick')
R('ring_protection_gold', (226, 204, 84), 'shield', (240, 220, 110), (255, 250, 200))
R('ring_protection_iron', (150, 152, 162), 'shield', (120, 122, 134), (200, 204, 214), deco='banded', dc=(96, 98, 110))
R('ring_protection_silver', (220, 222, 240), 'shield', (200, 204, 226), (255, 255, 255), style='thin')
R('ring_speed_quicksilver', (196, 214, 226), 'wing', (236, 244, 252), glow=True, post=lambda s: s.px([(2, 18), (3, 18), (1, 22), (2, 22), (3, 22)], (236, 244, 252)))
R('ring_strength_dragonbone', (214, 204, 176), 'fang', (232, 224, 200), tc3=(150, 140, 120), style='thick', deco='notch')
R('ring_sustenance_amber', (200, 140, 50), 'round', (246, 176, 60), glow=True, post=lambda s: s.px([(15, 9), (16, 10)], (150, 90, 30)))
R('scales_of_maat', (206, 180, 80), 'scales', (240, 210, 100))
R('seal_of_solomon', BRONZE, 'signet', (214, 160, 90), post=lambda s: M(s, 'star6', 16, 8, (150, 90, 200), None))
R('ring_of_solomon', GOLD, 'signet', (40, 60, 150), style='thick', post=lambda s: M(s, 'star6', 16, 7, s.lit((150, 220, 255)), None))
R('shadow_walker_ring', (44, 44, 64), 'signet', (26, 26, 40), post=lambda s: M(s, 'moon', 16, 8, (130, 130, 180), None))
R('tablet_of_gilgamesh', (176, 146, 104), None, style='thick', post=lambda s: s.px(
    [(8, 14), (9, 15), (12, 13), (13, 14), (17, 13), (18, 14), (22, 15), (23, 16), (6, 22), (7, 23), (10, 26), (11, 27), (15, 27), (16, 28), (20, 26), (21, 27), (24, 23)], (100, 76, 50)))


@named('scarab_of_khepri')
def _scarab(rec):
    s = ring((90, 180, 110), None)
    g, d = (60, 160, 90), (36, 100, 60)
    s.ell(10, 4, 21, 15, g); s.rect(13, 2, 18, 5, d); s.line([(15, 7), (15, 14)], d); s.line([(16, 7), (16, 14)], d)
    s.line([(11, 7), (20, 7)], d)
    s.px([(9, 6), (8, 5), (22, 6), (23, 5), (9, 11), (8, 12), (22, 11), (23, 12)], d)
    s.px([(12, 9), (12, 10)], (170, 240, 180)); s.ell(14, 0, 17, 2, s.lit((255, 200, 70)))
    return s.finish()


@named('draupnir')
def _draupnir(rec):
    s = ring((255, 215, 40), None, style='thick', deco='notch')
    g = (255, 225, 90)
    for x, y in ((3, 4), (12, 2), (22, 4)):
        s.ell(x, y, x + 6, y + 5, g); clear(s, 'ell', [x + 2, y + 2, x + 4, y + 3])
    s.px([(8, 10), (16, 9), (25, 11)], s.lit((255, 250, 190)))
    return s.finish()


# ---- described amulets -------------------------------------------------
A('amulet_archmage_intellect', 'crystal', (176, 130, 255), glow=True)
A('amulet_clairvoyant', 'disc', (80, 64, 104), 'eye', (40, 30, 56), (240, 236, 245), (170, 120, 255))
A('amulet_cold_res', 'locket', (240, 244, 250), 'snow', (110, 190, 250), (110, 190, 250), rim=SILVER)
A('amulet_curse_slow', 'bigdisc', (120, 120, 132), None, rim=(90, 90, 102), cord=True, chain_c=(120, 100, 80),
  post=lambda s: (s.ell(14, 17, 17, 21, (60, 60, 72)), s.px([(10, 16), (20, 23), (12, 24), (21, 15)], (150, 150, 162))))
A('amulet_curse_teleport', 'disc', (196, 200, 214), None, rim=(150, 154, 172),
  post=lambda s: (clear(s, 'poly', [(15, 13), (17, 13), (15, 19), (17, 21), (15, 26), (14, 26), (15, 21), (13, 19)]), s.px([(12, 17), (19, 22)], (150, 90, 170))))
A('amulet_displace', 'crystal', (126, 116, 130), None, post=lambda s: s.px([(22, 15), (24, 18), (23, 22), (8, 16), (7, 20)], (190, 190, 230)))
A('amulet_fire_res', 'tear', (44, 40, 46), 'ember', (255, 130, 40), (255, 230, 120), mglow=True, cy=22, chain_c=IRON)
A('amulet_hasted', 'tooth', (236, 228, 200), 'wing', (120, 100, 80), cord=True, chain_c=LEATHER, cy=18)
A('amulet_invis', 'phial', (214, 240, 250), None, post=lambda s: s.px([(15, 22), (16, 23), (16, 21)], s.lit((250, 255, 220))))
A('amulet_levitate', 'locket', (120, 130, 156), 'star4', (220, 230, 255), post=lambda s: s.px([(12, 15), (19, 17), (13, 24), (18, 25), (11, 20)], (80, 88, 110)))
A('amulet_life_saving', 'disc', (255, 226, 90), 'heart', (230, 70, 70), (255, 180, 170), glow=True, rim=GOLD, chain_c=GOLD)
A('amulet_of_fortitude', 'disc', BRONZE, 'snake', (70, 190, 110), (240, 240, 200), chain_c=BRONZE)
A('amulet_of_insight', 'disc', (150, 110, 64), 'diamond', (225, 250, 255), (255, 255, 255), mglow=True, cord=True, chain_c=(90, 140, 70))
A('amulet_of_merlin', 'tear', (70, 80, 200), 'star4', (240, 245, 255), (255, 255, 255), mglow=True, cy=21)
A('amulet_of_protection', 'square', (190, 84, 60), 'dragon', (120, 44, 34), (240, 200, 120), cord=True, chain_c=LEATHER, rim=(150, 60, 44))
A('amulet_of_the_archmage', 'disc', (76, 60, 52), None, rim=(50, 40, 38), chain_c=BRONZE, post=lambda s: (
    s.px([(15, 16), (16, 16)], s.lit((255, 110, 50))), s.px([(12, 19), (12, 20)], s.lit((90, 170, 255))),
    s.px([(19, 19), (19, 20)], s.lit((120, 220, 110))), s.px([(15, 23), (16, 23)], s.lit((240, 240, 250))), s.px([(15, 19), (16, 20)], (150, 110, 70))))
A('amulet_of_the_titan', 'rock', (70, 62, 66), None, chain_c=IRON, post=lambda s: (s.px([(13, 17), (14, 17), (18, 21), (12, 23), (19, 16)], (226, 160, 80)), s.px([(16, 24)], s.lit((255, 200, 110)))))
A('amulet_poison_res', 'tooth', (236, 232, 210), None, cord=True, chain_c=LEATHER, rim=(60, 150, 80), post=lambda s: s.px([(15, 28), (14, 30)], (90, 210, 90)))
A('amulet_reflection', 'bigdisc', (206, 228, 250), None, rim=SILVER, post=lambda s: (s.line([(11, 20), (16, 15)], WHITE), s.line([(14, 23), (20, 17)], WHITE)))
A('amulet_shock_res', 'disc', (60, 50, 50), 'spiral', COPPER, chain_c=COPPER, rim=COPPER, post=lambda s: s.px([(24, 14), (25, 12), (7, 25), (6, 27)], s.lit((250, 240, 120))))
A('amulet_sleep_res', 'bell', (150, 150, 226), None, rim=(100, 100, 170), post=lambda s: s.px([(13, 17), (13, 18), (14, 16)], (220, 220, 255)))
A('amulet_spell_turning', 'bigdisc', (150, 130, 220), 'spiral', (230, 220, 255), rim=(110, 90, 180))
A('amulet_titan_constitution', 'gem', (196, 30, 44), None, chain_c=GOLD, post=lambda s: (s.rect(11, 11, 20, 13, GOLD), s.px([(8, 17), (23, 17), (15, 28), (16, 28)], GOLD)))
A('amulet_truesight', 'gem', (210, 250, 220), 'eye', (60, 110, 80), (255, 255, 255), (60, 170, 110), glow=True, cy=19)
A('heart_of_ahriman', 'heart', (150, 0, 50), None, chain_c=(70, 60, 70), post=lambda s: (s.ell(13, 17, 18, 22, s.lit((255, 40, 90))), s.px([(15, 19), (16, 20)], s.lit((255, 170, 190)))))
A('obsidian_talisman', 'shard', (50, 40, 70), None, cord=True, chain_c=LEATHER, post=lambda s: s.px([(13, 17), (13, 18), (18, 24)], (150, 110, 200)))
A('prophets_amulet', 'bigdisc', (196, 198, 220), 'eye', (70, 70, 110), (255, 255, 255), (120, 200, 255), mglow=False, rim=(140, 144, 170),
  post=lambda s: s.px([(6, 12), (25, 12), (5, 27), (26, 27), (16, 9)], s.lit((190, 230, 255))))
A('rands_heart', 'heart', (200, 204, 222), None, cord=True, chain_c=LEATHER, post=lambda s: (s.line([(15, 16), (15, 27)], (140, 144, 166)), s.px([(18, 20)], GOLD)))
A('sailors_amulet', 'square', (150, 130, 110), 'wave', (40, 110, 200), cord=True, chain_c=(60, 120, 180), rim=(120, 100, 84))
A('seal_of_agrippa', 'bigdisc', (170, 50, 60), 'sun', (240, 200, 200), (255, 230, 200), rim=(130, 34, 46), cord=True, chain_c=(100, 100, 150),
  post=lambda s: (s.px([(6, 18), (25, 22), (14, 29), (20, 11)], (130, 34, 46)), s.px([(11, 15), (20, 24), (20, 15), (11, 24)], (240, 200, 200))))
A('silverlight_pendant', 'tear', (210, 214, 240), 'star4', (255, 255, 255), mglow=True, glow=False, cy=21)
A('tablet_of_hammurabi', 'square', (150, 124, 84), None, cord=True, chain_c=LEATHER, rim=(120, 96, 64), post=lambda s: (
    s.ell(9, 10, 22, 18, (120, 96, 64)), s.ell(11, 12, 20, 18, (150, 124, 84)),
    [s.px([(x, y), (x + 1, y + 1)], (84, 64, 44)) for y in (16, 19, 22) for x in (12, 15, 18)]))


@named('amulet_curse_drain')
def _damocles(rec):
    s = new()
    chain(s, [(15, 1), (15, 6)], (150, 150, 170), (150, 150, 170))
    s.rect(14, 6, 17, 8, (70, 40, 90)); s.rect(10, 9, 21, 10, GOLD); s.rect(15, 5, 16, 6, GOLD)
    s.poly([(14, 11), (17, 11), (17, 25), (16, 29), (15, 29), (14, 25)], (190, 190, 210))
    s.line([(15, 12), (15, 26)], (120, 100, 160))
    return s.finish()


@named('amulet_drain_res')
def _braid(rec):
    s = new()
    c, d = (206, 208, 224), (140, 100, 170)
    pts = [(6, 2), (5, 10), (7, 18), (11, 24), (16, 27), (21, 24), (25, 18), (27, 10), (26, 2)]
    s.line(pts, c, 3)
    n = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for k in range(0, 8, 3):
            s.px([(round(x0 + (x1 - x0) * k / 8), round(y0 + (y1 - y0) * k / 8))], shade(c, -2)); n += 1
    s.ell(13, 24, 19, 30, d); s.px([(15, 26)], WHITE)
    return s.finish()


@named('amulet_magic_res')
def _moly(rec):
    s = amu((120, 100, 80), cord=True, low=9)
    r = (40, 34, 40)
    s.poly([(14, 10), (18, 10), (19, 16), (17, 20), (15, 20), (13, 16)], r)
    s.line([(15, 20), (13, 25), (10, 28)], r); s.line([(17, 20), (18, 25), (22, 28)], r); s.line([(16, 20), (16, 29)], r)
    s.line([(13, 16), (9, 20)], r); s.line([(19, 16), (23, 21)], r)
    w = s.lit((250, 250, 240)); s.px([(15, 8), (17, 8), (16, 7), (16, 9), (14, 6), (18, 6)], w); s.px([(16, 8)], (240, 210, 90))
    return s.finish()


@named('amulet_regen_jade')
def _jadeleaf(rec):
    s = amu(GOLD, low=9)
    j, d = (40, 190, 90), (20, 120, 60)
    s.poly([(16, 9), (21, 13), (23, 19), (21, 25), (16, 29), (11, 25), (9, 19), (11, 13)], j)
    s.line([(16, 11), (16, 28)], d)
    for y in (15, 19, 23): s.line([(16, y), (12, y - 3)], d); s.line([(16, y), (20, y - 3)], d)
    s.px([(12, 20), (12, 21)], (170, 250, 190))
    return s.finish()


def ankh(s, c, c2=None):
    s.ell(10, 2, 21, 14, c); clear(s, 'ell', [13, 5, 18, 11])
    s.rect(14, 14, 17, 29, c); s.rect(7, 15, 24, 18, c)
    if c2: s.px([(14, 16), (17, 16), (15, 22), (16, 22), (9, 16), (22, 17)], c2)


@named('ankh_of_isis')
def _ankh1(rec):
    s = new(); ankh(s, (226, 186, 60), (60, 150, 200)); s.px([(15, 16), (16, 17)], (60, 150, 200))
    return s.finish()


@named('ankh_of_ra')
def _ankh2(rec):
    s = new(); ankh(s, (214, 160, 70)); s.ell(13, 5, 18, 11, s.lit((255, 120, 50))); s.px([(15, 7), (16, 8)], s.lit((255, 230, 130)))
    return s.finish()


@named('tyet_of_isis')
def _tyet(rec):
    s = new(); r, d = (214, 56, 70), (150, 30, 46)
    s.ell(11, 2, 20, 12, r); clear(s, 'ell', [14, 5, 17, 9])
    s.rect(12, 12, 19, 14, d)
    s.poly([(12, 14), (8, 17), (7, 24), (10, 25), (12, 18)], r); s.poly([(19, 14), (23, 17), (24, 24), (21, 25), (19, 18)], r)
    s.rect(14, 14, 17, 29, r); s.line([(15, 16), (15, 28)], d)
    return s.finish()


def balance(s, c, post_c=None, glow=None):
    post_c = post_c or c
    s.rect(15, 5, 16, 26, post_c); s.rect(11, 26, 20, 28, c); s.rect(4, 7, 27, 8, c); s.ell(14, 2, 17, 5, c)
    for x in (5, 26):
        s.line([(x, 9), (x - 3, 17)], shade(c, -1)); s.line([(x, 9), (x + 3, 17)], shade(c, -1))
    s.poly([(1, 17), (9, 17), (7, 20), (3, 20)], c); s.poly([(22, 17), (30, 17), (28, 20), (24, 20)], c)


@named('anubis_scales')
def _anubis(rec):
    s = new(); balance(s, (226, 180, 60), (60, 50, 60))
    s.poly([(13, 4), (13, 1), (15, 3), (17, 3), (19, 1), (19, 4), (17, 6), (15, 6)], (40, 34, 46))   # jackal ears/head
    s.px([(4, 16), (5, 15), (5, 16)], RED); s.px([(25, 16), (26, 15), (26, 14), (27, 16)], WHITE)     # heart vs feather
    return s.finish()


@named('scales_of_michael')
def _michael(rec):
    s = new(); g = (255, 236, 170)
    balance(s, g, (220, 224, 236))
    s.rect(12, 9, 19, 10, GOLD); s.poly([(15, 26), (16, 26), (16, 30), (15, 30)], (220, 224, 236))
    s.ell(14, 2, 17, 5, s.lit((255, 250, 210))); s.px([(4, 16), (5, 16), (26, 16), (25, 16)], s.lit((255, 250, 210)))
    return s.finish()


def necklace(s, c, pts=None):
    pts = pts or [(4, 2), (4, 10), (7, 16), (12, 20), (16, 21), (20, 20), (25, 16), (28, 10), (28, 2)]
    chain(s, pts, c)
    return pts


@named('brisingamen')
def _bris(rec):
    s = new(); g = (255, 205, 80)
    necklace(s, g)
    for x, y in ((3, 15), (9, 19), (16, 19), (22, 15)):
        s.ell(x, y, x + 7, y + 7, g); clear(s, 'ell', [x + 2, y + 2, x + 5, y + 5])
    f = s.lit((255, 110, 150))
    s.px([(6, 18), (7, 19), (12, 22), (13, 23), (19, 22), (20, 23), (25, 18), (26, 19)], f)
    return s.finish()


@named('necklace_of_harmonia')
def _harm(rec):
    s = new(); g = (236, 190, 70)
    s.line([(5, 2), (5, 10), (8, 16), (12, 19)], g, 2); s.line([(27, 2), (27, 10), (24, 16), (20, 19)], g, 2)
    s.px([(5, 5), (6, 9), (8, 14), (27, 5), (26, 9), (24, 14)], (120, 200, 120))
    s.rect(11, 18, 13, 20, g); s.rect(19, 18, 21, 20, g); s.px([(12, 18), (20, 18)], RED)        # serpent heads
    s.poly([(15, 19), (17, 19), (20, 23), (16, 28), (12, 23)], s.lit((200, 110, 220))); s.px([(15, 22), (16, 21)], s.lit((250, 210, 255)))
    return s.finish()


@named('collar_of_njord')
def _njord(rec):
    s = new()
    pts = [(4, 3), (5, 9), (8, 14), (12, 18), (16, 19), (20, 18), (24, 14), (27, 9), (28, 3)]
    for k, (x, y) in enumerate(pts):
        c = (240, 160, 40) if k % 2 == 0 else (238, 232, 214)
        s.ell(x - 2, y - 2, x + 1, y + 1, c)
    s.poly([(14, 21), (18, 21), (17, 26), (15, 30)], (238, 232, 214)); s.px([(16, 23)], (80, 170, 215))
    return s.finish()


@named('menat_of_hathor')
def _menat(rec):
    s = new()
    s.ell(2, -10, 29, 21, (232, 110, 60)); s.ell(5, -10, 26, 17, (70, 170, 200)); s.ell(8, -10, 23, 13, (236, 190, 80))
    clear(s, 'ell', [11, -10, 20, 9]); clear(s, 'rect', [0, 0, 31, 0])
    for x, y in ((4, 9), (8, 16), (15, 20), (23, 16), (27, 9)): s.px([(x, y)], (255, 220, 170))
    s.rect(15, 22, 16, 25, (236, 190, 80)); s.ell(12, 25, 19, 30, (70, 170, 200)); s.px([(15, 27), (16, 27)], (236, 190, 80))
    return s.finish()


@named('pectoral_of_amun')
def _pect(rec):
    s = amu(GOLD, low=8, wide=True); g, l = (226, 180, 70), (40, 70, 170)
    s.poly([(6, 9), (25, 9), (28, 27), (3, 27)], g)
    for x in (7, 11, 19, 23): s.rect(x, 12, x + 1, 24, l)
    s.rect(4, 25, 27, 26, l); s.ell(13, 13, 18, 18, s.lit((255, 140, 60))); s.px([(11, 21), (20, 21), (12, 22), (19, 22), (13, 21), (18, 21)], (90, 200, 220))
    return s.finish()


@named('kavacha_kundala')
def _kavacha(rec):
    s = new(); g, d = (232, 196, 60), (176, 130, 40)
    s.poly([(8, 9), (12, 7), (16, 10), (20, 7), (24, 9), (25, 17), (22, 28), (10, 28), (7, 17)], g)
    s.line([(16, 11), (16, 27)], d); s.line([(10, 18), (22, 18)], d); s.line([(11, 23), (21, 23)], d)
    s.px([(12, 13), (13, 13), (19, 13), (20, 13)], s.lit((255, 250, 190)))
    for x in (2, 26):
        s.ell(x, 2, x + 4, 7, g); clear(s, 'rect', [x + 2, 4, x + 2, 5]); s.px([(x + 2, 8), (x + 2, 9)], s.lit((255, 120, 60)))
    return s.finish()


def torc(s, c, term, tw=14):
    s.ell(3, 3, 28, 27, c); clear(s, 'ell', [7, 7, 24, 23]); clear(s, 'rect', [12, 22, 19, 29])
    import math
    for k in range(tw):
        a = math.pi * (0.62 + 1.76 * k / (tw - 1))
        x, y = round(15.5 + 10.6 * math.cos(a)), round(15 + 10.2 * math.sin(a))
        s.px([(x, y), (x + 1, y - 1)], shade(c, -2))
    s.ell(7, 22, 12, 27, term); s.ell(19, 22, 24, 27, term)


@named('torc_of_boudicca')
def _torc1(rec):
    s = new(); torc(s, (206, 160, 56), (236, 196, 90)); s.px([(9, 24), (21, 24)], RED)
    return s.finish()


@named('torque_of_lugh')
def _torc2(rec):
    s = new(); torc(s, (250, 204, 84), s.lit((255, 244, 170)), 9)
    M(s, 'sun', 16, 14, s.lit((255, 230, 120)), s.lit((255, 250, 210)))
    return s.finish()


@named('lyre_of_orpheus')
def _lyre(rec):
    s = amu(GOLD, low=4); w, g = (180, 140, 220), (240, 210, 110)
    s.line([(11, 22), (8, 15), (9, 8), (12, 5)], w, 2); s.line([(20, 22), (23, 15), (22, 8), (19, 5)], w, 2)
    s.rect(9, 7, 22, 8, g); s.ell(10, 20, 21, 29, w)
    for x in (13, 15, 17, 18): s.line([(x, 9), (x, 23)], s.lit((255, 240, 170)))
    return s.finish()


@named('hamsa_hand')
def _hamsa(rec):
    s = amu(SILVER, low=3); c = (206, 186, 146)
    s.ell(8, 13, 23, 28, c)
    for x, y in ((10, 6), (14, 4), (18, 6)): s.rect(x, y, x + 3, 16, c)
    s.poly([(8, 18), (5, 13), (7, 11), (10, 15)], c); s.poly([(23, 18), (26, 13), (24, 11), (21, 15)], c)
    M(s, 'eye', 16, 21, (70, 60, 90), (250, 250, 245), (50, 130, 220))
    s.px([(11, 8), (15, 6), (19, 8)], (60, 150, 200))
    return s.finish()


@named('eye_of_horus')
def _horus(rec):
    s = new(); b, d = (50, 150, 204), (24, 70, 130)
    s.poly([(3, 7), (16, 4), (28, 7), (28, 9), (16, 7), (3, 9)], d)
    s.ell(6, 10, 25, 20, b); s.ell(9, 12, 22, 18, (240, 244, 240)); s.ell(13, 12, 18, 18, d); s.px([(14, 13)], WHITE)
    s.poly([(25, 14), (30, 15), (25, 17)], b)
    s.line([(13, 20), (12, 28)], d, 2)
    s.line([(18, 20), (21, 25), (25, 27), (28, 25), (27, 22)], b, 2)
    return s.finish()


@named('eponas_charm')
def _epona(rec):
    s = amu(LEATHER, cord=True, low=9); c, d = (184, 144, 100), (110, 80, 54)
    s.rect(8, 16, 21, 21, c)
    s.poly([(18, 17), (21, 11), (25, 10), (27, 13), (24, 15), (22, 19)], c)
    for x in (9, 12, 18, 20): s.rect(x, 21, x + 1, 28, c)
    s.line([(8, 16), (5, 19), (5, 24)], d, 2); s.line([(20, 11), (18, 15)], d); s.px([(25, 11)], DARK)
    s.rect(8, 28, 22, 29, d)
    return s.finish()


@named('idunn_apple_charm')
def _apple(rec):
    s = amu(SILVER, low=8); c = (150, 224, 110)
    s.ell(8, 12, 17, 27, c); s.ell(14, 12, 23, 27, c); s.rect(15, 8, 16, 13, (110, 80, 50))
    s.poly([(17, 9), (21, 7), (22, 10), (18, 11)], (70, 160, 80))
    s.px([(11, 16), (11, 17), (12, 15)], s.lit((240, 255, 200))); s.px([(15, 13), (16, 13)], shade(c, -2))
    return s.finish()


@named('jade_cicada')
def _cicada(rec):
    s = amu(LEATHER, cord=True, low=6); j, d = (110, 200, 130), (50, 130, 80)
    s.poly([(12, 7), (19, 7), (21, 11), (19, 22), (16, 28), (15, 28), (12, 22), (10, 11)], j)
    s.poly([(10, 12), (7, 20), (9, 27), (14, 22), (13, 13)], (190, 236, 200)); s.poly([(21, 12), (24, 20), (22, 27), (17, 22), (18, 13)], (190, 236, 200))
    s.line([(11, 11), (20, 11)], d); s.px([(11, 8), (20, 8)], DARK); s.line([(9, 24), (12, 16)], d); s.line([(22, 24), (19, 16)], d)
    return s.finish()


@named('ouroboros_pendant')
def _ouro(rec):
    s = amu(SILVER, low=8); c, d = (170, 200, 150), (90, 130, 80)
    s.ell(6, 9, 25, 28, c); clear(s, 'ell', [10, 13, 21, 24])
    import math
    for k in range(12):
        a = 2 * math.pi * k / 12 + 0.3
        s.px([(round(15.5 + 7.6 * math.cos(a)), round(18.5 + 7.6 * math.sin(a)))], d)
    s.rect(13, 8, 19, 12, d); s.px([(14, 9)], s.lit((255, 90, 70))); s.px([(20, 11), (21, 12)], c)
    return s.finish()


@named('caduceus_charm', 'caduceus_wand')
def _cad(rec):
    wand_ = rec['id'].endswith('wand')
    s = new() if wand_ else amu(SILVER, low=3)
    g = (226, 190, 80) if wand_ else (170, 220, 190)
    a, b = ((70, 170, 90), (190, 90, 60)) if wand_ else ((110, 150, 220), (230, 230, 240))
    y0 = 6 if wand_ else 8
    s.rect(15, y0, 16, 29, g); s.ell(14, y0 - 4, 17, y0 - 1, g)
    wc = (245, 245, 235)
    for sx in (-1, 1):
        s.poly([(15 + (sx > 0), y0), (15 + (sx > 0) + sx * 9, y0 - 3), (15 + (sx > 0) + sx * 10, y0), (15 + (sx > 0) + sx * 5, y0 + 4), (15 + (sx > 0), y0 + 3)], wc)
    pat = [2, 3, 3, 2, 0, -2, -3, -3, -2, 0]
    for k, y in enumerate(range(y0 + 5, 28)):
        o = pat[k % 10]
        s.px([(15 + o, y), (16 + o, y)], a); s.px([(15 - o, y), (16 - o, y)], b)
    s.rect(15, y0, 16, y0 + 4, g)
    if wand_: s.px([(15, y0 - 3)], s.lit((200, 255, 210)))
    return s.finish()


@named('saints_reliquary')
def _reliq(rec):
    s = amu(SILVER, low=7); c = (206, 200, 180)
    s.rect(11, 9, 20, 27, c); s.poly([(11, 9), (15, 5), (16, 5), (20, 9)], c); s.rect(10, 27, 21, 28, shade(c, -1))
    s.rect(13, 13, 18, 23, (60, 50, 70)); M(s, 'bone', 16, 18, IVORY, IVORY)
    s.px([(15, 7), (16, 7)], GOLD)
    return s.finish()


@named('sphinx_crown')
def _sphinx(rec):
    s = new(); g, l = (226, 190, 80), (40, 80, 180)
    s.poly([(5, 14), (8, 6), (12, 13), (16, 3), (20, 13), (24, 6), (27, 14), (27, 24), (5, 24)], g)
    s.rect(5, 20, 27, 23, l); s.px([(x, y) for x in range(6, 27, 3) for y in (21, 22)], g)
    s.ell(14, 12, 18, 17, s.lit((90, 200, 255))); s.px([(8, 8), (24, 8)], RED); s.rect(4, 24, 28, 26, shade(g, -1))
    return s.finish()


def athena(s, wood, y0=3, cord=False):
    d = shade(wood, -2)
    s.poly([(13, y0 + 3), (15, y0), (18, y0), (20, y0 + 3)], (190, 60, 60))                    # crest
    s.ell(12, y0 + 2, 19, y0 + 9, wood); s.px([(14, y0 + 6), (17, y0 + 6)], d)
    s.poly([(12, y0 + 10), (19, y0 + 10), (21, 27), (10, 27)], wood)
    s.line([(15, y0 + 12), (15, 26)], d); s.line([(18, y0 + 13), (19, 26)], d)
    s.rect(24, 2, 24, 28, (200, 190, 150)); s.poly([(23, 4), (24, 1), (25, 4)], STEEL)       # spear
    s.line([(19, y0 + 12), (24, y0 + 14)], wood, 2)
    s.ell(3, 13, 12, 22, (176, 150, 96)); s.ell(6, 16, 9, 19, GOLD)                              # shield
    s.rect(9, 27, 22, 29, d)


@named('talisman_of_troy')
def _troy(rec):
    s = new(); chain(s, [(13, 1), (15, 4)], LEATHER); chain(s, [(19, 1), (16, 4)], LEATHER)
    athena(s, (200, 200, 250), 4)
    return s.finish()


@named('palladium')
def _pallad(rec):
    s = new(); athena(s, (160, 116, 70), 2); s.px([(14, 8), (17, 8)], s.lit((200, 230, 255)))
    return s.finish()


# ---- belts / oddities --------------------------------------------------
@named('megingjord')
def _megin(rec):
    s = new(); l, i = (160, 60, 40), (110, 112, 128)
    s.poly([(1, 11), (30, 11), (30, 21), (1, 21)], l)
    for x in (3, 7, 24, 28): s.px([(x, 13), (x, 19)], GOLD)
    s.rect(9, 7, 22, 25, i); s.rect(11, 9, 20, 23, shade(i, -1))
    s.px([(10, 8), (21, 8), (10, 24), (21, 24)], STEEL)
    b = s.lit((150, 210, 255)); s.line([(17, 11), (14, 16), (17, 16), (14, 21)], b)
    return s.finish()


@named('anansis_thread')
def _anansi(rec):
    s = new(); g, d = (250, 210, 60), (190, 140, 30)
    for y in (6, 11, 16):
        s.ell(4, y, 27, y + 8, g); clear(s, 'ell', [7, y + 2, 24, y + 5])
    for x in range(6, 26, 3): s.px([(x, 7), (x + 1, 13), (x, 23)], d)
    s.line([(22, 22), (22, 26)], (230, 230, 220))
    M(s, 'spider', 22, 27, (50, 36, 30), None)
    return s.finish()


@named('ariadnes_thread')
def _ariadne(rec):
    s = new(); c, d = (214, 216, 245), (150, 154, 196)
    s.line([(13, 2), (18, 2), (18, 6), (15, 8)], IRON, 2)                 # belt hook
    s.ell(6, 8, 25, 27, c)
    for k in (0, 4, 8): s.line([(8, 14 + k), (22, 10 + k)], d); s.line([(10 + k, 10), (14 + k, 26)], shade(c, 2))
    s.line([(22, 24), (26, 27), (24, 30), (29, 29)], s.lit((235, 235, 255)))
    return s.finish()


@named('rope_of_izanagi')
def _shime(rec):
    s = new(); r, d = (226, 206, 130), (160, 130, 70)
    s.poly([(1, 9), (8, 7), (16, 6), (24, 7), (30, 9), (30, 14), (24, 13), (16, 12), (8, 13), (1, 14)], r)
    for x in range(3, 30, 4): s.line([(x, 13), (x + 2, 7)], d)
    w = s.lit((255, 255, 240))
    for x in (7, 15, 23):
        s.poly([(x, 13), (x + 2, 13), (x + 3, 17), (x + 1, 17)], w); s.poly([(x - 1, 18), (x + 1, 18), (x + 2, 22), (x, 22)], w)
        s.poly([(x, 23), (x + 2, 23), (x + 3, 27), (x + 1, 27)], w)
    for x in (3, 11, 19, 27): s.line([(x, 14), (x, 19)], d)
    return s.finish()


@named('charmander_stuffie')
def _stuffie(rec):
    s = new(); o, cr, gr = (250, 150, 60), (250, 226, 170), (90, 180, 120)
    s.poly([(6, 14), (2, 10), (5, 18)], gr); s.poly([(25, 14), (29, 10), (26, 18)], gr)            # felt wings
    s.line([(21, 25), (26, 24), (28, 20)], o, 3); M(s, 'star4', 27, 17, (255, 226, 90), (255, 250, 200))   # tail + felt star
    s.ell(9, 14, 22, 28, o); s.ell(12, 18, 19, 27, cr)
    s.ell(6, 16, 10, 22, o); s.ell(21, 16, 25, 22, o)                                              # arms
    s.ell(8, 25, 14, 30, o); s.ell(17, 25, 23, 30, o); s.px([(10, 28), (12, 28), (19, 28), (21, 28)], cr)
    s.ell(8, 2, 23, 15, o)
    s.poly([(10, 4), (9, 1), (13, 3)], gr); s.poly([(21, 4), (22, 1), (18, 3)], gr)                # horn nubs
    s.rect(12, 8, 13, 9, DARK); s.rect(18, 8, 19, 9, DARK); s.px([(12, 8), (18, 8)], WHITE)        # button eyes
    s.line([(14, 12), (17, 12)], (150, 70, 40)); s.px([(13, 11), (18, 11)], (150, 70, 40))
    s.px([(15, 19), (15, 21), (15, 23), (15, 25)], (190, 150, 110))                                # belly seam
    s.rect(19, 20, 20, 21, (120, 190, 230))                                                        # patch
    return s.finish()


@named('dreamspun_sketchbook')
def _sketch(rec):
    s = new(); c, p = (190, 160, 236), (244, 240, 226)
    s.rect(7, 6, 25, 29, p); s.rect(5, 5, 23, 27, c)
    for x in range(7, 23, 3): s.rect(x, 3, x, 6, STEEL)
    M(s, 'star4', 13, 15, (255, 240, 170), WHITE); s.px([(18, 21), (19, 20), (20, 21), (19, 22), (9, 22), (10, 23)], (255, 190, 220))
    clear(s, 'poly', [(23, 27), (20, 27), (23, 24)])
    s.line([(18, 26), (28, 12)], (240, 200, 70), 2); s.px([(29, 11), (28, 11), (29, 10)], (240, 200, 180)); s.px([(17, 27)], DARK)
    return s.finish()


# ---- artifacts ---------------------------------------------------------
SEALS = {'death': ((200, 200, 214), 'skull', (60, 60, 84)), 'earthquake': ((150, 140, 132), 'rock', (96, 70, 50)),
         'famine': ((190, 170, 110), 'wheat', (110, 90, 50)), 'pestilence': ((130, 170, 60), 'drop', (60, 90, 30)),
         'silence': ((206, 208, 228), 'hollow', (130, 134, 164)), 'war': ((176, 60, 46), 'cross_x', (70, 24, 24)),
         'wrath': ((214, 50, 50), 'flame', (255, 200, 90))}


def seal(rec):
    k = rec['id'].replace('seal_of_', '')
    face, motif, mc = SEALS[k]
    s = new()
    s.ell(3, 3, 28, 28, shade(face, -1)); s.ell(6, 6, 25, 25, face)
    lit = k == 'wrath'
    M(s, motif, 16, 15, s.lit(mc) if lit else mc, s.lit((255, 250, 200)) if lit else shade(mc, 2), None)
    if k == 'war':
        s.px([(11, 10), (21, 10), (11, 21), (21, 21)], (220, 220, 230))
    if k == 'earthquake':
        s.line([(8, 8), (12, 12), (11, 15)], DARK); s.line([(24, 22), (20, 20), (21, 17)], DARK); clear(s, 'poly', [(26, 9), (22, 11), (27, 13)])
    if k == 'pestilence':
        s.px([(9, 26), (9, 27), (9, 29), (22, 27), (22, 28), (16, 29)], (150, 200, 60)); s.px([(10, 11), (21, 19), (11, 19)], (90, 120, 40))
    if k == 'famine':
        clear(s, 'poly', [(3, 20), (7, 22), (5, 26)]); s.px([(9, 9), (22, 21), (10, 20)], (150, 130, 80))
    if k == 'death':
        for p in ((16, 4), (27, 15), (16, 27), (4, 15)): s.px([p], (60, 60, 84))
    if k == 'silence':
        s.line([(11, 15), (21, 15)], (130, 134, 164)); s.px([(2, 8), (29, 23)], (230, 232, 250))
    if k == 'wrath':
        s.px([(9, 9), (22, 9), (9, 22), (22, 22)], s.lit((255, 200, 90)))
    return s.finish()


for _k in SEALS: NAMED['seal_of_' + _k] = seal


@named('bear_sinew')
def _sinew(rec):
    s = new(); c, d = (226, 190, 160), (176, 130, 110)
    for x, y in ((4, 8), (9, 11)):
        s.ell(x, y, x + 17, y + 14, c); clear(s, 'ell', [x + 3, y + 3, x + 14, y + 11])
    s.line([(22, 12), (27, 6), (29, 8)], c, 2); s.line([(8, 22), (4, 27), (7, 29)], c, 2)
    s.px([(6, 12), (20, 9), (12, 24), (24, 22), (15, 12)], d)
    return s.finish()


@named('bird_spittle')
def _spit(rec):
    s = new(); c = s.lit((236, 240, 200)); w = s.lit((255, 255, 250))
    s.poly([(16, 4), (22, 15), (23, 21), (20, 26), (16, 28), (12, 26), (9, 21), (10, 15)], c)
    s.px([(13, 17), (13, 18), (13, 19), (14, 15), (14, 21)], w)
    s.px([(5, 8), (26, 7), (27, 26), (4, 24)], w)
    return s.finish()


@named('cats_footstep')
def _cat(rec):
    s = new()
    s.rect(10, 8, 21, 28, GLASS); s.rect(9, 6, 22, 8, shade(GLASS, -1)); s.rect(12, 2, 19, 5, CORK)
    M(s, 'paw', 16, 19, (176, 150, 204), None); s.px([(12, 11), (12, 12), (12, 13)], WHITE)
    c = (176, 160, 210)
    s.px([(5, 14), (4, 16), (4, 18), (5, 20), (26, 14), (27, 16), (27, 18), (26, 20), (2, 15), (2, 19), (29, 15), (29, 19)], c)
    return s.finish()


@named('fish_breath')
def _fish(rec):
    s = new(); c = (150, 210, 230)
    s.ell(4, 4, 27, 27, c); s.ell(6, 6, 25, 25, (196, 232, 244))
    f = (60, 130, 170)
    s.ell(11, 14, 19, 19, f); s.poly([(19, 16), (23, 13), (23, 20)], f); s.px([(13, 16)], WHITE)
    s.px([(9, 10), (10, 9), (11, 8), (9, 11)], WHITE); s.px([(22, 23), (21, 24)], (230, 246, 250)); s.px([(8, 22), (9, 23), (7, 20)], (240, 250, 255))
    return s.finish()


@named('gleipnir')
def _gleip(rec):
    s = new(); c = s.lit((222, 222, 255)); d = (160, 160, 226)
    s.line([(3, 6), (9, 4), (14, 8), (12, 14), (7, 17), (8, 23), (15, 26), (22, 24), (25, 18), (20, 13), (22, 7), (28, 5)], c, 2)
    s.line([(14, 8), (20, 13)], d, 2); s.line([(12, 14), (25, 18)], d)
    s.px([(5, 27), (27, 27), (16, 2), (29, 12)], s.lit((255, 255, 255)))
    return s.finish()


@named('mountain_root')
def _root(rec):
    s = new(); c, d = (146, 138, 130), (96, 90, 90)
    s.poly([(8, 3), (22, 2), (26, 8), (22, 12), (10, 12), (5, 8)], c); s.px([(11, 5), (12, 5), (18, 8), (20, 6)], d)
    s.line([(14, 12), (12, 18), (14, 23), (10, 29)], c, 3); s.line([(18, 12), (21, 18), (19, 24), (23, 29)], c, 2)
    s.line([(12, 18), (6, 21), (4, 26)], c, 2); s.line([(21, 18), (26, 20), (28, 25)], c, 2)
    s.px([(13, 15), (20, 15), (13, 21), (20, 22)], d)
    return s.finish()


@named('womans_beard')
def _beard(rec):
    s = new(); cs = [(214, 180, 144), (184, 150, 116), (236, 210, 176)]
    for k, x in enumerate((9, 11, 13, 15, 17, 19, 21)):
        o = (k % 3) - 1
        s.line([(15 + (k - 3) // 2, 8), (x - o, 14), (x + o * 2, 20), (x - o, 26), (x + o, 29)], cs[k % 3])
    s.rect(12, 5, 19, 8, (150, 60, 80)); s.px([(13, 4), (18, 4), (11, 6), (20, 6)], (150, 60, 80))
    return s.finish()


@named('leather_scrap')
def _scrap(rec):
    s = new(); c, d = (140, 100, 64), (90, 62, 40)
    s.poly([(5, 9), (17, 6), (27, 10), (25, 18), (28, 25), (15, 27), (6, 23), (8, 16)], c)
    s.px([(8, 11), (11, 10), (14, 9), (17, 9), (20, 10), (23, 11)], d); s.line([(12, 16), (20, 20)], d); s.px([(10, 21), (22, 15)], shade(c, 2))
    return s.finish()


@named('bronze_bull')
def _bull(rec):
    s = new(); b, d = (190, 130, 66), (126, 80, 44)
    s.rect(3, 27, 28, 29, d)
    s.rect(7, 13, 23, 21, b); s.ell(5, 12, 12, 22, b)
    for x in (8, 12, 18, 21): s.rect(x, 21, x + 2, 26, b)
    s.ell(18, 7, 28, 17, b); s.rect(24, 13, 29, 17, b); s.px([(27, 15), (29, 15)], d); s.px([(23, 11)], s.lit((255, 200, 90)))
    s.line([(20, 8), (18, 4), (20, 2)], IVORY, 2); s.line([(26, 8), (28, 4), (27, 2)], IVORY, 2)
    s.line([(6, 14), (3, 17), (3, 22)], d, 2); s.line([(10, 16), (20, 16)], d)
    return s.finish()


@named('cursed_lodestone')
def _lode(rec):
    s = new(); c = (62, 62, 84)
    s.poly([(9, 8), (19, 5), (26, 11), (27, 20), (20, 27), (9, 26), (4, 18)], c)
    g = s.lit((170, 90, 230)); s.line([(11, 11), (15, 15), (13, 20), (17, 23)], g); s.line([(15, 15), (21, 14)], g)
    for (x0, y0, x1, y1) in ((27, 5, 24, 9), (3, 8, 6, 12), (28, 26, 24, 23), (3, 27, 7, 24)):
        s.line([(x0, y0), (x1, y1)], STEEL)
    return s.finish()


@named('eye_of_graeae')
def _graeae(rec):
    s = new(); w = (224, 226, 236)
    s.ell(4, 5, 27, 27, w); s.ell(10, 10, 21, 21, (130, 150, 180)); s.ell(13, 13, 18, 18, (30, 30, 50))
    s.px([(12, 12), (13, 12), (12, 13)], s.lit((255, 255, 255)))
    s.px([(6, 14), (7, 15), (8, 15), (24, 19), (25, 20), (22, 23), (8, 21), (7, 22)], (210, 140, 150))
    return s.finish()


@named('philosophers_stone')
def _pstone(rec):
    s = new(); r = (200, 40, 50); g = s.lit((255, 215, 60)); w = s.lit((255, 250, 200))
    s.poly([(11, 6), (21, 6), (27, 14), (22, 26), (10, 26), (5, 14)], r)
    s.poly([(12, 10), (20, 10), (23, 15), (19, 22), (13, 22), (9, 15)], (236, 80, 60))
    s.poly([(14, 13), (18, 13), (19, 16), (17, 19), (15, 19), (13, 16)], g); s.px([(15, 15), (16, 15)], w)
    s.px([(16, 2), (3, 8), (28, 7), (2, 22), (29, 23), (16, 30)], g)
    return s.finish()


@named('sealed_dispatch')
def _dispatch(rec):
    s = new(); l = (124, 92, 64)
    s.poly([(3, 20), (22, 5), (28, 11), (9, 27)], l)
    for t in (0.05, 0.5, 0.92):
        x, y = 3 + 19 * t, 20 - 15 * t
        s.line([(x, y), (x + 6, y + 6.5)], IRON, 2)
    s.ell(11, 11, 20, 20, (190, 40, 40)); s.px([(14, 14), (15, 13)], (240, 120, 110)); M(s, 'crown', 16, 17, (130, 20, 30), (130, 20, 30))
    s.line([(18, 20), (20, 26)], (150, 30, 40), 2)
    return s.finish()


def sphere(rec, a, b, core):
    s = new()
    s.ell(4, 4, 27, 27, a)
    s.poly([(7, 9), (13, 6), (20, 8), (22, 13), (18, 17), (12, 17), (10, 20), (13, 24), (20, 25), (25, 21), (23, 26), (16, 28), (8, 25), (5, 19), (8, 14), (14, 13), (17, 11), (13, 9)], b)
    c = s.lit(core)
    s.px([(15, 11), (16, 10), (14, 21), (15, 22), (21, 17), (9, 12), (22, 22)], c)
    s.px([(9, 7), (10, 6)], WHITE)
    return s.finish()


NAMED['soul_sphere'] = lambda rec: sphere(rec, (210, 50, 60), (240, 232, 214), (255, 230, 160))
NAMED['unusual_soul_sphere'] = lambda rec: sphere(rec, (46, 44, 60), (190, 194, 214), (150, 230, 255))


@named('tablet_of_destinies')
def _tod(rec):
    s = new(); c, d = (176, 150, 104), (104, 80, 52)
    s.poly([(7, 4), (23, 3), (26, 7), (25, 28), (6, 28), (6, 8)], c)
    for y in (7, 10, 20, 23, 26):
        for x in range(9, 23, 3): s.px([(x, y), (x + 1, y)] if (x + y) % 2 else [(x, y), (x, y + 1)], d)
    M(s, 'star6', 16, 15, s.lit((120, 230, 255)), None)
    return s.finish()


@named('vidars_sandal')
def _sandal(rec):
    s = new(); a, b, c = (170, 136, 84), (120, 84, 50), (200, 170, 120)
    s.poly([(2, 23), (8, 20), (24, 20), (30, 23), (29, 27), (3, 27)], b)
    s.rect(3, 24, 9, 25, a); s.rect(11, 22, 17, 23, c); s.rect(19, 24, 26, 25, a); s.rect(12, 25, 17, 26, (150, 90, 60))
    s.px([(10, 23), (18, 23), (10, 26), (27, 23)], STRING)
    s.line([(6, 20), (10, 11), (16, 9)], a, 2); s.line([(22, 20), (16, 9)], a, 2); s.line([(10, 15), (20, 15)], c, 2)
    s.line([(24, 20), (27, 14), (24, 12)], a, 2); s.px([(16, 10)], GOLD)
    return s.finish()


@named('lockpick', 'master_lockpick')
def _pick(rec):
    s = new(); m = rec['id'].startswith('master')
    c = (250, 226, 90) if m else (196, 196, 180)
    s.ell(2, 21, 9, 28, c); clear(s, 'ell', [4, 23, 7, 26])
    s.line([(8, 22), (23, 7)], c, 2); s.line([(23, 7), (26, 7), (27, 4)], c)
    s.line([(9, 26), (26, 20), (26, 16)], shade(c, -1), 2 if m else 1)
    if m:
        s.line([(8, 21), (17, 4), (19, 5), (20, 3)], c)
        s.px([(28, 2), (29, 9), (24, 3)], s.lit((255, 255, 210)))
    return s.finish()


# ---- named wands ---------------------------------------------------------
@named('aarons_rod')
def _aaron(rec):
    s = new(); w = (170, 116, 76)
    stick(s, w, 4, 28, 22, 2); s.px([(3, 29), (4, 29)], shade(w, -1))
    pink, gr = (255, 226, 232), (110, 180, 90)
    for x, y in ((24, 5), (20, 7), (17, 13), (25, 10)):
        s.px([(x, y), (x + 1, y), (x, y - 1), (x - 1, y), (x, y + 1)], pink); s.px([(x, y)], (240, 190, 80))
    s.px([(13, 16), (12, 15), (15, 20), (16, 21), (21, 13), (22, 14), (10, 20), (9, 19)], gr)
    s.ell(27, 2, 29, 5, (150, 190, 100))
    return s.finish()


@named('circes_wand')
def _circe(rec):
    s = new(); w = (238, 230, 204)
    stick(s, w, 5, 27, 17, 1); stick(s, w, 5, 28, 8, 2); s.px([(4, 29), (5, 29), (4, 28)], (200, 180, 220))
    M(s, 'spiral', 24, 7, s.lit((230, 130, 250)), None)
    s.px([(17, 5), (28, 14), (19, 2)], s.lit((255, 220, 255)))
    return s.finish()


@named('indras_vajra')
def _vajra(rec):
    s = new(); g, i = (236, 200, 80), (120, 122, 138)
    stick(s, i, 12, 20, 9, 2); s.ell(13, 13, 18, 18, g)
    for (cx, cy, sx) in ((8, 24, -1), (23, 9, 1)):
        s.poly([(cx - 3, cy), (cx, cy - 3), (cx + 3, cy), (cx, cy + 3)], g)
        s.line([(cx - 2 * sx, cy - 3 * sx), (cx + 2 * sx, cy - 5 * sx), (cx + 5 * sx, cy - 5 * sx)], g, 1)
        s.line([(cx + 3 * sx, cy + 2 * sx), (cx + 5 * sx, cy - 2 * sx), (cx + 5 * sx, cy - 5 * sx)], g, 1)
        s.px([(cx + 5 * sx, cy - 5 * sx), (cx + 6 * sx, cy - 6 * sx)], s.lit((255, 255, 200)))
    b = s.lit((250, 245, 110))
    s.line([(4, 5), (7, 9), (5, 10), (8, 14)], b); s.line([(22, 18), (25, 21), (23, 23), (27, 27)], b)
    return s.finish()


@named('iron_mortar_wand')
def _mortar(rec):
    s = new(); i, d = (112, 110, 122), (70, 68, 82)
    s.line([(14, 16), (25, 4)], (150, 112, 76), 3); s.ell(23, 2, 28, 7, (150, 112, 76))
    s.poly([(4, 13), (27, 13), (24, 26), (7, 26)], i); s.rect(3, 11, 28, 13, d); s.rect(9, 26, 22, 28, d)
    s.line([(8, 17), (22, 17)], d); s.px([(7, 15), (8, 16)], STEEL)
    s.px([(5, 9), (9, 7), (4, 5)], s.lit((150, 230, 140)))
    return s.finish()


@named('lantern_of_diogenes')
def _lantern(rec):
    s = new(); b, d = (176, 126, 60), (110, 76, 40)
    s.ell(11, 1, 20, 8, b); clear(s, 'ell', [13, 3, 18, 7])
    s.poly([(10, 10), (15, 6), (16, 6), (21, 10)], b); s.rect(8, 10, 23, 12, d)
    s.rect(9, 12, 22, 25, b)
    f = s.lit((255, 226, 110)); s.rect(11, 13, 14, 24, f); s.rect(17, 13, 20, 24, f)
    s.px([(12, 18), (13, 17), (13, 19), (18, 18), (19, 17), (18, 19)], s.lit((255, 255, 230)))
    s.rect(7, 25, 24, 27, d); s.rect(9, 28, 22, 29, b); s.px([(10, 16), (21, 21)], d)
    return s.finish()


# ---- named potions -------------------------------------------------------
@named('elixir_of_gilgamesh')
def _gilg(rec):
    s = new(); g = (60, 170, 70)
    liq = flask(s, 'round', g, 17, glass=(150, 210, 160))
    t = (40, 110, 50)
    s.line([(20, 2), (18, 6), (21, 10), (23, 15), (22, 20)], t); s.px([(21, 5), (17, 8), (23, 12), (24, 17), (20, 13), (19, 3)], t)
    s.ell(21, 0, 24, 3, (240, 220, 240)); s.px([(11, 19), (11, 20), (12, 18)], WHITE)
    return s.finish()


@named('fafnirs_blood')
def _faf(rec):
    s = new(); r = s.lit((255, 70, 30))
    liq = flask(s, 'heart', (255, 70, 30), 15, glass=(90, 70, 76), cork=(60, 50, 56))
    s.px(liq, r); s.px([(12, 19), (13, 20), (17, 22), (18, 18)], s.lit((255, 190, 90)))
    s.rect(13, 9, 18, 10, GOLD); M(s, 'dragon', 16, 2, (60, 120, 70), (255, 220, 100))
    return s.finish()


@named('soma')
def _soma(rec):
    s = new(); g = s.lit((255, 222, 110)); c = (226, 226, 240)
    s.poly([(5, 8), (26, 8), (23, 17), (18, 20), (13, 20), (8, 17)], c); s.rect(14, 20, 17, 25, c); s.rect(9, 26, 22, 28, c)
    s.rect(7, 9, 24, 12, g); s.px([(11, 10), (17, 11)], s.lit((255, 255, 230)))
    M(s, 'moon', 16, 4, s.lit((235, 240, 255)), None); s.px([(8, 14), (9, 15)], WHITE)
    s.line([(10, 23), (21, 23)], GOLD)
    return s.finish()


@named('water_of_lethe')
def _lethe(rec):
    s = new(); c, d = (60, 66, 96), (40, 44, 70)
    s.poly([(13, 3), (18, 3), (18, 8), (23, 13), (23, 22), (19, 28), (12, 28), (8, 22), (8, 13), (13, 8)], c)
    s.rect(12, 2, 19, 3, d); s.rect(12, 28, 19, 29, d)
    s.line([(12, 6), (7, 8), (8, 13)], d, 2); s.line([(19, 6), (24, 8), (23, 13)], d, 2)
    w = s.lit((206, 226, 255)); s.line([(10, 17), (13, 16), (16, 17), (19, 16), (21, 17)], w); s.line([(11, 21), (14, 20), (17, 21), (20, 20)], w)
    return s.finish()


# ---- named books ---------------------------------------------------------
NAMED['book_of_thoth'] = lambda r: book(r, cover=(90, 130, 90), motif='eye', mc=(240, 200, 80), mc2=(255, 250, 220), mc3=(60, 150, 220), trim='corners')
NAMED['lemegeton'] = lambda r: book(r, cover=(44, 36, 54), motif='star6', mc=(230, 50, 60), trim='studs')
NAMED['necronomicon'] = lambda r: book(r, cover=(150, 100, 84), motif='mask', mc=(110, 64, 56), mc2=(255, 230, 90), mc3=(60, 30, 30), trim='stitch', glow=False)
NAMED['picatrix'] = lambda r: book(r, cover=(120, 70, 150), motif='sun', mc=(250, 220, 110), mc2=(255, 250, 210), trim='corners')
NAMED['sefer_yetzirah'] = lambda r: book(r, cover=(206, 204, 226), motif='tree', mc=(60, 90, 190), mc2=(60, 90, 190), mc3=(120, 90, 60), trim='frame', glow=False)


@named('amulet_of_pythagoras')
def _pyth(rec):
    s = amu(BRONZE, low=8); b = (170, 150, 110)
    s.poly([(15, 8), (16, 8), (27, 28), (4, 28)], b)
    c = s.lit((170, 225, 245))
    for row, n in enumerate((1, 2, 3, 4)):
        y = 13 + row * 4
        for k in range(n): s.px([(16 - (n - 1) * 2 + k * 4, y), (15 - (n - 1) * 2 + k * 4, y)], c)
    return s.finish()
