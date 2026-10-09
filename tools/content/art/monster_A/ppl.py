"""People of the monster_A slice: the friendly characters met in the dungeon
and the hero sprites. Offline tooling."""
from rig import *  # noqa: F401,F403
from rig import fig, item, PX, dk, lt, Sprite, ell_pts
from mon import reg, R, YEL, GRN, CYAN, ICE  # noqa: F401

GHOSTS = {'npc_ghost', 'npc_ghost_edwin', 'npc_weeping_ghost'}
PAINTED = ('player', 'player_ranger', 'player_robyn', 'player_wizard_f')


# =================================================================== friendly characters
@reg('npc_blind_seer')
def _(s, r):
    fig(s, size='robed', hair='bald_fringe', hairc=WHITE, beard='long', beardc=WHITE, blind=(236, 232, 220),
        torso='robe', tc=(120, 132, 164), tc2=(84, 92, 124), rh=('staff', None, 'knob'), arms=('fwd', 'down'), skin=TAN)


@reg('npc_blinded_soldier')
def _(s, r):
    g = fig(s, size='kneel', hair='short', hairc=BROWN, blind=(236, 232, 220), torso='armor', tc=(130, 134, 150),
            tc2=(90, 94, 110), legs='kneel', lc=(80, 70, 60), arms=('fwd', 'fwd'), beard='stubble')
    PX(s, [(18, 13)], (190, 70, 60))
    s.ell(2, 24, 8, 29, IRON); s.line([(3, 26), (7, 26)], DARK)


@reg('npc_bound_demon')
def _(s, r):
    sk = (196, 64, 54)
    g = fig(s, size='kneel', skin=sk, eye=s.lit((255, 230, 90)), torso='bare', tc=(70, 40, 50), tc2=DARK, legs='kneel',
            lc=(150, 44, 44), boots=(150, 44, 44), brow=True, arms=('up', 'up'), geo=dict(head=(11, 9, 20, 17)))
    s.poly([(12, 11), (9, 5), (14, 9)], (60, 44, 50)); s.poly([(19, 11), (22, 5), (17, 9)], (60, 44, 50))
    for hx in (8, 23):
        s.rect(hx - 1, 13, hx + 1, 14, IRON)
        PX(s, [(hx, 11), (hx, 9), (hx, 7), (hx, 5), (hx, 3), (hx, 1)], STEEL)
    s.line([(10, 21), (21, 24)], STEEL); s.line([(21, 21), (10, 24)], STEEL)
    PX(s, [(15, 15), (16, 15)], IVORY)


@reg('npc_burdened_knight')
def _(s, r):
    s.ell(5, 3, 26, 17, (130, 96, 60)); s.rect(8, 1, 23, 6, (150, 128, 90)); s.line([(6, 10), (25, 10)], (90, 60, 40))
    s.rect(24, 8, 27, 15, (120, 120, 130)); PX(s, [(4, 12), (4, 14), (3, 16)], STRING)
    fig(s, size='kneel', hat='fullhelm', hatc=(150, 154, 170), torso='armor', tc=(150, 154, 170), tc2=(100, 104, 124),
        legs='pants', lc=(100, 104, 124), boots=(150, 154, 170), hands=(150, 154, 170), lh=('staff', None, 'knob'),
        geo=dict(head=(11, 9, 20, 17), sh=17, waist=25, arm=(18, 23), lw=3, tw=6, bw=5))


@reg('npc_caged_angel')
def _(s, r):
    s.shadow = False
    g = fig(s, size='robed', hair='long', hairc=BLOND, hat='halo', hatc=(255, 240, 150), torso='robe', tc=(240, 238, 228),
            tc2=GOLD, wings=(236, 240, 250), arms=('fwd', 'fwd'), boots=SKIN,
            geo=dict(head=(11, 8, 20, 16), sh=16, arm=(17, 23)))
    bar = (84, 86, 100)
    for x in (3, 9, 15, 16, 22, 28):
        s.rect(x, 4, x, 29, bar)
    s.rect(2, 3, 29, 4, bar); s.rect(2, 29, 29, 30, bar); s.poly([(10, 3), (15, 1), (16, 1), (21, 3)], bar)


@reg('npc_chained_priest')
def _(s, r):
    g = fig(s, size='robed', hair='bald_fringe', hairc=GREY, torso='robe', tc=(56, 52, 64), tc2=(236, 232, 220),
            trim=False, arms=('up', 'up'), mouth=True)
    s.rect(14, 15, 17, 16, WHITE); s.rect(15, 18, 16, 23, GOLD); s.line([(14, 20), (17, 20)], GOLD)
    for hx in (9, 22):
        s.rect(hx - 1, 10, hx + 1, 11, IRON)
        PX(s, [(hx, 8), (hx, 6), (hx, 4), (hx, 2)], STEEL)


@reg('npc_child')
def _(s, r):
    fig(s, size='child', hair='short', hairc=BLOND, tc=(80, 130, 190), tc2=LEATHER, lc=(110, 84, 60), mouth=True)


@reg('npc_creature')
def _(s, r):
    f = (150, 170, 200)
    s.poly([(9, 22), (4, 18), (3, 23), (8, 26)], f)
    s.poly([(11, 13), (10, 6), (15, 12)], f); s.poly([(20, 13), (22, 6), (17, 12)], f)
    PX(s, [(11, 9), (12, 11), (21, 9), (20, 11)], (236, 180, 190))
    s.ell(8, 11, 23, 28, f); s.ell(11, 18, 20, 27, (226, 232, 240))
    s.ell(11, 14, 14, 18, WHITE); s.ell(17, 14, 20, 18, WHITE); s.rect(12, 16, 13, 17, DARK); s.rect(18, 16, 19, 17, DARK)
    PX(s, [(15, 19), (16, 19)], (236, 150, 160)); s.line([(14, 21), (17, 21)], DARK)
    s.rect(10, 28, 13, 29, f); s.rect(18, 28, 21, 29, f)


@reg('npc_cursed_scholar')
def _(s, r):
    v = s.lit((210, 110, 255))
    g = fig(s, size='robed', hair='wild', hairc=GREY, skin=(214, 196, 200), torso='robe', tc=(60, 110, 120),
            tc2=(40, 76, 90), lh=('book', (110, 60, 150)), arms=('fwd', 'down'), eye=v)
    PX(s, [(12, 13), (19, 12), (22, 19), (9, 24), (20, 26), (13, 22), (6, 9), (26, 12), (25, 5), (5, 17)], v)


@reg('npc_deadite_woman')
def _(s, r):
    w = s.lit((255, 255, 236))
    sk = (190, 204, 186)
    g = fig(s, skin=sk, hair='long', hairc=BLACK, eye=w, torso='dress', tc=(170, 170, 196), tc2=(110, 110, 146),
            sleeve=sk, arms=('down', 'up'), boots=sk, lh=('claws', sk))
    s.rect(13, 7, 14, 8, DARK); s.rect(17, 7, 18, 8, DARK); PX(s, [(14, 8), (17, 8)], w)
    PX(s, [(15, 11), (16, 11)], DARK)
    PX(s, [(9, 28), (12, 27), (16, 28), (20, 27), (22, 28), (12, 19), (19, 22), (14, 24)], (110, 110, 146))
    PX(s, [(21, 6), (23, 5), (25, 6)], sk)


@reg('npc_deserter')
def _(s, r):
    g = fig(s, hair='short', hairc=BROWN, beard='stubble', torso='tabard', tc=(120, 110, 96), tc2=(150, 60, 56),
            lc=(80, 70, 60), arms=('up', 'up'), mouth=True)
    PX(s, [(14, 20), (16, 22), (17, 19)], (120, 110, 96))
    s.ell(22, 23, 29, 29, (150, 128, 90)); PX(s, [(25, 23), (26, 23)], DARK)


@reg('npc_divine')
def _(s, r):
    glow = s.lit((255, 244, 170))
    s.ell(3, 2, 28, 26, (255, 250, 214))
    g = fig(s, size='robed', skin=(250, 232, 200), hair='long', hairc=(250, 220, 120), hat='halo', hatc=(255, 244, 170),
            torso='robe', tc=(250, 248, 238), tc2=GOLD, wings=(236, 240, 252), arms=('fwd', 'fwd'), eye=(90, 150, 220),
            boots=GOLD, geo=dict(head=(11, 8, 20, 16), sh=16, arm=(17, 23)))
    PX(s, [(2, 6), (29, 4), (4, 26), (28, 24), (15, 3)], glow)
    s.shadow = False


@reg('npc_dwarf')
def _(s, r):
    fig(s, size='stout', hat='horned', hatc=IRON, beard='huge', beardc=(206, 110, 50), torso='armor', tc=(110, 100, 110),
        tc2=GOLD, lc=(90, 64, 44), rh=('pick',), brow=True, skin=(226, 170, 134))


def lying(s, body, legs, skin, hairc, boots, head_extra=None):
    s.rect(18, 24, 26, 27, legs); s.rect(26, 23, 28, 27, boots)
    s.rect(9, 22, 18, 27, body)
    s.rect(11, 20, 16, 22, body); s.rect(15, 19, 17, 20, skin)
    s.ell(2, 19, 9, 27, skin)
    PX(s, [(x, y) for x, y in ell_pts(2, 19, 9, 27) if x <= 3 or y <= 20], hairc)
    PX(s, [(5, 22), (5, 24)], DARK)


@reg('npc_dying_courier')
def _(s, r):
    lying(s, (70, 110, 150), (90, 70, 56), SKIN, BROWN, LEATHER)
    s.ell(12, 14, 18, 20, (150, 110, 70)); s.line([(9, 22), (15, 15)], (110, 80, 50))
    s.rect(18, 15, 23, 19, WHITE); PX(s, [(20, 17), (21, 17)], (200, 50, 50))
    s.line([(9, 24), (17, 24)], LEATHER)


@reg('npc_dying_knight')
def _(s, r):
    st = (156, 160, 178)
    lying(s, st, (116, 120, 140), SKIN, BLOND, st)
    s.line([(9, 24), (17, 24)], (110, 114, 134)); s.rect(12, 23, 14, 25, (180, 50, 50))
    s.ell(20, 14, 27, 20, st); s.line([(22, 17), (26, 17)], DARK); s.rect(23, 11, 24, 14, (180, 50, 50))
    s.line([(4, 29), (22, 29)], STEEL); s.line([(7, 28), (7, 30)], GOLD)


@reg('npc_dying_monk')
def _(s, r):
    g = fig(s, size='kneel', hair='bald_fringe', hairc=BROWN, torso='robe', tc=(124, 88, 56), tc2=(90, 60, 40),
            trim=False, arms=('fwd', 'fwd'), boots=SKIN, skin=PALE)
    s.line([(11, 25), (20, 25)], (214, 200, 150)); PX(s, [(15, 26), (15, 27), (15, 28)], (214, 200, 150))
    PX(s, [(14, 10), (15, 9), (16, 9), (17, 10)], PALE)
    PX(s, [(16, 24), (16, 26)], GOLD)


@reg('npc_dying_prophet')
def _(s, r):
    g = fig(s, size='kneel', hair='long', hairc=WHITE, beard='huge', beardc=WHITE, torso='robe', tc=(214, 204, 176),
            tc2=(170, 150, 110), trim=False, arms=('down', 'up'), boots=TAN, skin=TAN, rh=('scroll',))
    PX(s, [(26, 6), (28, 9), (20, 5)], s.lit((255, 240, 160)))


@reg('npc_fallen_paladin')
def _(s, r):
    gd = (176, 160, 110)
    g = fig(s, size='kneel', hair='short', hairc=(96, 80, 60), torso='armor', tc=gd, tc2=(120, 104, 70), legs='kneel',
            lc=(120, 110, 96), boots=gd, cloak=(206, 200, 190), pauldron=gd, hands=gd, beard='stubble',
            rh=('sword', STEEL, 5), hat='halo', hatc=(150, 146, 130))
    s.glow.discard((150, 146, 130))
    s.line([(3, 29), (8, 27)], STEEL); PX(s, [(2, 29)], STEEL)


@reg('npc_forgotten_prisoner')
def _(s, r):
    g = fig(s, skin=PALE, hair='wild', hairc=GREY, beard='huge', beardc=GREY, tc=(150, 140, 116), tc2=(110, 100, 84),
            lc=(120, 110, 96), boots=PALE, geo=dict(tw=5, bw=4, lw=2, aw=2))
    for hx in (9, 22):
        s.rect(hx - 1, 19, hx + 1, 20, IRON)
    PX(s, [(9, 22), (8, 24), (9, 26), (10, 28), (22, 22), (23, 24), (24, 26)], STEEL)
    PX(s, [(13, 27), (18, 26), (12, 24)], (110, 100, 84))
    s.ell(24, 26, 28, 30, IRON)


def ghost_tail(s, c, y=22):
    s.poly([(9, y), (22, y), (21, 26), (23, 29), (19, 27), (17, 30), (14, 27), (11, 30), (10, 26)], c)


@reg('npc_ghost')
def _(s, r):
    s.shadow = False
    c = (206, 226, 240)
    s.ell(8, 3, 23, 20, c); s.rect(8, 11, 23, 22, c); ghost_tail(s, c)
    s.poly([(8, 13), (3, 15), (2, 19), (5, 18), (8, 18)], c); s.poly([(23, 13), (28, 11), (30, 7), (27, 8), (23, 9)], c)
    s.ell(11, 8, 14, 13, DARK); s.ell(17, 8, 20, 13, DARK); s.ell(14, 15, 17, 19, DARK)
    PX(s, [(12, 9), (18, 9)], s.lit((170, 230, 255)))


@reg('npc_ghost_edwin')
def _(s, r):
    s.shadow = False
    a, b, c = (206, 228, 244), (124, 160, 206), (70, 100, 156)
    g = fig(s, skin=a, hair='part', hairc=c, beard='stache', beardc=c, torso='suit', tc=b, tc2=c, legs='robe', boots=b,
            eye=c, lh=('book', c), arms=('fwd', 'down'), hands=a)
    ghost_tail(s, b, 22)
    PX(s, [(4, 12), (27, 9), (6, 22)], s.lit((200, 240, 255)))


@reg('npc_weeping_ghost')
def _(s, r):
    s.shadow = False
    a, b, c = (240, 228, 246), (170, 140, 206), (96, 74, 144)
    t = s.lit((130, 226, 255))
    s.poly([(10, 13), (21, 13), (23, 24), (8, 24)], b); ghost_tail(s, b, 23)
    s.ell(9, 3, 22, 14, c); s.rect(9, 8, 11, 20, c); s.rect(20, 8, 22, 20, c)
    s.ell(12, 5, 19, 13, a)
    s.line([(13, 9), (14, 9)], DARK); s.line([(17, 9), (18, 9)], DARK); PX(s, [(15, 12), (16, 12)], c)
    s.rect(13, 16, 18, 18, a); s.line([(15, 16), (15, 18)], b)
    PX(s, [(13, 10), (13, 12), (18, 10), (18, 12), (18, 14), (13, 14)], t)


@reg('npc_grieving_father')
def _(s, r):
    g = fig(s, size='kneel', hair='short', hairc=(70, 54, 44), beard='short', beardc=(70, 54, 44), tc=(110, 84, 60),
            tc2=DARK, legs='kneel', lc=(70, 64, 70), arms=('fwd', 'fwd'), brow=True)
    s.ell(14, 19, 17, 22, (236, 200, 170)); s.rect(14, 22, 17, 25, (200, 90, 110)); PX(s, [(14, 19), (17, 19)], (226, 190, 96))
    PX(s, [(14, 15)], s.lit((150, 220, 255)))


@reg('npc_injured_scholar')
def _(s, r):
    g = fig(s, size='kneel', hair='short', hairc=BROWN, hat='headband', hatc=WHITE, tc=(70, 100, 150), tc2=LEATHER,
            legs='kneel', lc=(70, 100, 150), arms=('down', 'fwd'), beard='goatee')
    PX(s, [(18, 11)], (200, 60, 60))
    s.poly([(12, 18), (20, 18), (20, 24), (13, 24)], WHITE); s.line([(12, 18), (20, 24)], (200, 200, 196))
    s.rect(1, 25, 7, 29, (150, 50, 50)); s.rect(2, 26, 7, 28, WHITE)
    PX(s, [(13, 14), (14, 14), (17, 14), (18, 14)], GOLD)


@reg('npc_lost_girl')
def _(s, r):
    g = fig(s, size='child', hair='pigtails', hairc=(150, 90, 50), torso='dress', tc=(220, 110, 130), tc2=WHITE,
            sleeve=(220, 110, 130), boots=DARK, arms=('down', 'fwd'), mouth=True)
    PX(s, [(9, 14), (10, 14), (21, 14), (22, 14)], (230, 60, 60))
    s.ell(15, 21, 19, 25, (160, 110, 70)); s.ell(15, 19, 18, 22, (160, 110, 70)); PX(s, [(15, 19), (18, 19)], (160, 110, 70))
    PX(s, [(16, 21), (17, 21)], DARK)
    PX(s, [(14, 17)], s.lit((150, 220, 255)))


@reg('npc_lost_merchant')
def _(s, r):
    g = fig(s, hair='short', hairc=BROWN, beard='short', hat='feather', hatc=(150, 96, 50), hat2=(230, 70, 60),
            tc=(190, 120, 60), tc2=DARK, lc=(90, 70, 56), rh=('lantern',), lh=('pack', (120, 84, 56)), mouth=True,
            geo=dict(tw=6, bw=6))
    s.rect(3, 9, 9, 20, (130, 92, 60)); s.rect(3, 7, 9, 9, (190, 170, 120)); s.line([(3, 14), (9, 14)], DARK)
    PX(s, [(20, 3), (22, 2), (21, 1), (20, 1)], WHITE)


@reg('npc_merchant')
def _(s, r):
    s.rect(5, 6, 26, 19, (140, 96, 60)); s.rect(6, 3, 25, 6, (200, 80, 70)); s.rect(3, 10, 5, 16, (90, 130, 190))
    s.rect(26, 9, 28, 15, (210, 180, 90)); s.line([(5, 12), (26, 12)], DARK)
    g = fig(s, hat='turban', hatc=(130, 70, 160), hat2=(120, 220, 230), beard='bigstache', beardc=DARK, skin=TAN,
            torso='robe', tc=(60, 140, 96), tc2=GOLD, mouth=True, arms=('down', 'fwd'), boots=(130, 70, 160),
            geo=dict(head=(11, 7, 20, 15), sh=15, arm=(16, 22), tw=6, bw=6))
    s.ell(15, 21, 19, 25, (170, 130, 70)); PX(s, [(17, 20)], DARK); PX(s, [(16, 23), (18, 23)], s.lit((255, 226, 90)))


@reg('npc_mystic')
def _(s, r):
    st = s.lit((255, 240, 160))
    g = fig(s, size='robed', skin=DUSK, hat='turban', hatc=(110, 60, 170), hat2=(255, 220, 90), torso='robe',
            tc=(50, 50, 120), tc2=(170, 120, 220), arms=('fwd', 'fwd'), eye=WHITE)
    s.ell(13, 18, 18, 23, s.lit((150, 220, 255))); PX(s, [(14, 19), (15, 19)], s.lit((240, 255, 255)))
    PX(s, [(10, 25), (21, 26), (12, 27), (19, 24), (9, 20), (22, 21)], st)


@reg('npc_old_warrior')
def _(s, r):
    g = fig(s, hair='long', hairc=GREY, beard='short', beardc=GREY, torso='armor', tc=(120, 100, 80), tc2=(84, 70, 56),
            lc=(80, 70, 64), cloak=(96, 60, 50), brow=True, skin=TAN, pauldron=IRON)
    s.rect(25, 12, 26, 29, STEEL); s.line([(23, 12), (28, 12)], GOLD); s.rect(25, 8, 26, 11, DARK); s.rect(22, 10, 25, 12, TAN)
    s.line([(18, 6), (19, 10)], (160, 90, 80))


@reg('npc_penitent')
def _(s, r):
    g = fig(s, size='kneel', hat='hood', hatc=(170, 150, 110), torso='robe', tc=(170, 150, 110), tc2=(120, 104, 76),
            trim=False, arms=('fwd', 'fwd'), boots=SKIN)
    s.line([(10, 25), (21, 25)], (110, 84, 60)); PX(s, [(18, 26), (18, 27), (18, 28)], (110, 84, 60))
    PX(s, [(12, 21), (19, 22), (14, 27), (11, 24)], (120, 104, 76))


@reg('npc_poisoned_herbalist')
def _(s, r):
    b = s.lit((170, 240, 110))
    g = fig(s, size='kneel', skin=(186, 206, 150), hair='short', hairc=(110, 70, 44), hat='bandana', hatc=(226, 214, 180), torso='tunic', tc=(96, 140, 80),
            tc2=(200, 190, 150), legs='kneel', lc=(120, 96, 70), arms=('fwd', 'down'), mouth=(90, 140, 70))
    s.rect(23, 23, 29, 28, (150, 110, 60)); s.line([(23, 23), (29, 23)], (110, 80, 44))
    PX(s, [(24, 22), (26, 21), (28, 22), (25, 21), (27, 20)], (90, 180, 80)); PX(s, [(26, 20)], (230, 120, 200))
    PX(s, [(8, 12), (6, 8), (23, 9), (9, 6)], b)


@reg('npc_rat_catcher')
def _(s, r):
    g = fig(s, hair='short', hairc=DARK, beard='stubble', hat='kettle', hatc=(110, 84, 60), tc=(120, 110, 96),
            tc2=DARK, lc=(70, 64, 60), cloak=(96, 86, 76), rh=('staff', None, 'knob'), geo=dict(tw=6))
    s.line([(22, 7), (29, 7)], WOOD)
    for x, y in ((23, 8), (27, 8)):
        s.rect(x, y, x + 1, y + 4, (130, 124, 124)); PX(s, [(x, y + 5), (x, y + 6), (x + 1, y + 7)], (226, 150, 150))
    s.rect(1, 23, 7, 29, IRON); s.rect(2, 24, 6, 28, (60, 56, 60)); PX(s, [(3, 24), (5, 24), (3, 26), (5, 26)], IRON)
    PX(s, [(4, 27)], (226, 150, 150))


@reg('npc_scholar')
def _(s, r):
    g = fig(s, size='robed', hair='short', hairc=GREY, beard='short', beardc=GREY, hat='beret', hatc=(60, 80, 130),
            torso='robe', tc=(80, 104, 150), tc2=(214, 200, 150), lh=('book', (150, 50, 50)), rh=('scroll',),
            arms=('fwd', 'down'))
    PX(s, [(13, 11), (15, 11), (16, 11), (18, 11), (13, 12), (18, 12)], GOLD)


@reg('npc_small_shrine')
def _(s, r):
    s.shadow = False
    st, sd = (150, 150, 156), (110, 110, 122)
    f = s.lit((255, 200, 90)); h = s.lit((255, 250, 200))
    s.rect(5, 26, 26, 29, sd); s.rect(7, 23, 24, 26, st)
    s.rect(8, 9, 23, 23, st); s.poly([(6, 10), (15, 2), (16, 2), (25, 10)], sd)
    s.rect(11, 12, 20, 22, (60, 56, 70)); s.ell(11, 10, 20, 16, (60, 56, 70))
    s.rect(15, 13, 16, 20, GOLD); s.line([(13, 15), (18, 15)], GOLD)
    s.rect(12, 19, 13, 22, WHITE); PX(s, [(12, 18), (13, 17), (12, 17)], f); PX(s, [(12, 18)], h)
    s.rect(18, 20, 19, 22, WHITE); PX(s, [(18, 19), (19, 18), (18, 18)], f); PX(s, [(18, 19)], h)
    PX(s, [(8, 22), (9, 21), (22, 22), (23, 21)], (90, 150, 80)); PX(s, [(9, 22), (22, 21)], (230, 120, 160))
    PX(s, [(9, 12), (22, 17), (10, 25), (20, 24)], (120, 150, 100))


@reg('npc_starving_nun')
def _(s, r):
    g = fig(s, size='kneel', skin=PALE, hat='wimple', hatc=(50, 48, 60), hat2=WHITE, torso='robe', tc=(50, 48, 60),
            tc2=WHITE, trim=False, arms=('fwd', 'fwd'), geo=dict(tw=5, bw=4))
    s.rect(14, 18, 17, 19, WHITE); PX(s, [(15, 21), (15, 22), (15, 23), (14, 22), (16, 22)], BROWN)
    s.poly([(23, 26), (29, 26), (28, 29), (24, 29)], (150, 110, 70)); s.line([(24, 26), (28, 26)], (80, 56, 40))


@reg('npc_stone_statue')
def _(s, r):
    a, b, c = (158, 158, 164), (136, 136, 146), (112, 112, 124)
    s.rect(6, 26, 25, 29, c); s.rect(8, 24, 23, 26, b)
    g = fig(s, skin=a, eye=c, hat='helm', hatc=b, torso='armor', tc=b, tc2=c, legs='pants', lc=c, boots=b, hands=a,
            arms=('fwd', 'fwd'), cloak=c, pauldron=a,
            geo=dict(head=(11, 1, 20, 9), sh=9, waist=19, arm=(10, 16), foot=24))
    s.rect(15, 14, 16, 24, a); s.line([(13, 14), (18, 14)], a)
    PX(s, [(9, 12), (21, 18), (10, 25), (22, 27), (7, 28)], (110, 140, 90))
    s.line([(18, 3), (20, 6)], c)


@reg('npc_trapped_fairy')
def _(s, r):
    s.shadow = False
    glass, rim = (170, 206, 214), (130, 96, 60)
    f = s.lit((255, 240, 150)); w = s.lit((220, 250, 255))
    s.rect(11, 3, 20, 6, rim); s.rect(13, 1, 18, 3, (160, 120, 76))
    s.ell(6, 6, 25, 29, glass); s.ell(8, 8, 23, 27, (50, 70, 96))
    s.poly([(14, 16), (11, 12), (11, 17), (13, 18)], w); s.poly([(17, 16), (20, 12), (20, 17), (18, 18)], w)
    s.rect(15, 16, 16, 21, f); s.ell(14, 12, 17, 15, (250, 220, 190)); PX(s, [(15, 11), (16, 11), (14, 12), (17, 12)], (240, 150, 90))
    PX(s, [(15, 22), (16, 23)], f); PX(s, [(10, 23), (21, 22), (12, 9), (20, 25)], f)
    s.line([(9, 10), (9, 14)], (226, 240, 244)); s.rect(8, 28, 23, 29, glass)


@reg('npc_traveler')
def _(s, r):
    fig(s, hat='hood', hatc=(96, 110, 80), beard='short', beardc=BROWN, tc=(150, 120, 84), tc2=DARK, lc=(90, 70, 56),
        cloak=(84, 96, 70), sleeve=(96, 110, 80), rh=('bindle', (190, 60, 60)), lh=('staff', None, 'knob'))


@reg('npc_warrior')
def _(s, r):
    fig(s, hat='helm', hatc=STEEL, beard='short', beardc=BROWN, torso='armor', tc=(150, 156, 176), tc2=(104, 108, 130),
        lc=(84, 70, 60), rh=('sword',), lh=('shield', (180, 50, 50), GOLD, 'round'), pauldron=STEEL)


@reg('npc_young_knight')
def _(s, r):
    st = (200, 206, 224)
    fig(s, hair='short', hairc=BLOND, torso='tabard', tc=st, tc2=(70, 130, 200), legs='greaves', lc=(130, 136, 160),
        boots=st, rh=('sword', (226, 230, 240), 10), lh=('banner', (70, 130, 200), GOLD), pauldron=st, mouth=True,
        sleeve=(170, 176, 200), hands=st)


@reg('npc_young_thief')
def _(s, r):
    fig(s, size='small', skin=SKIN, hat='hood', hatc=(120, 50, 56), hair='fringe', hairc=DARK, tc=(84, 76, 80), tc2=DARK,
        lc=(60, 54, 60), rh=('dagger',), lh=('sack', (170, 150, 100)), mouth=True)


# =================================================================== heroes
@reg('player')
def _(s, r):
    fig(s, hair='short', hairc=BROWN, tc=(62, 104, 180), tc2=LEATHER, lc=(96, 76, 60), cloak=(160, 50, 50),
        rh=('sword',), lh=('shield', (140, 100, 60), STEEL, 'round'), mouth=True)


@reg('player_ranger')
def _(s, r):
    g = fig(s, hat='hood', hatc=(60, 110, 66), hair='fringe', hairc=BROWN, tc=(130, 96, 60), tc2=DARK, sleeve=(60, 110, 66),
            lc=(84, 70, 56), boots=(96, 66, 44), cloak=(50, 96, 58), lh=('bow', (160, 120, 70)), rh=('dagger',))
    s.rect(21, 8, 22, 14, LEATHER); PX(s, [(21, 7), (22, 6), (23, 7)], (236, 232, 220))


@reg('player_robyn')
def _(s, r):
    g = fig(s, hair='pony', hairc=(170, 90, 50), tc=(60, 140, 136), tc2=LEATHER, lc=(96, 76, 70), boots=(110, 76, 50),
            lh=('bow', (150, 130, 80)), rh=('book', (90, 70, 170)), mouth=True, eye=(60, 110, 70),
            geo=dict(head=(11, 6, 20, 15), sh=15, tw=5, bw=4, arm=(16, 22), aw=2))
    s.rect(8, 10, 9, 15, LEATHER); PX(s, [(8, 9), (9, 8)], (236, 232, 220))
    PX(s, [(x, 6) for x in range(13, 19)], (170, 90, 50))


@reg('player_wizard_f')
def _(s, r):
    fig(s, size='robed', hair='long', hairc=(190, 80, 50), hat='wizard', hatc=(110, 60, 160), hat2=GOLD, torso='robe',
        tc=(124, 70, 176), tc2=GOLD, rh=('staff', (255, 230, 120), 'star'), lh=('orb', (150, 220, 255)), arms=('up', 'down'),
        eye=(70, 120, 90), mouth=(200, 90, 100))


@reg('player_achilles')
def _(s, r):
    g = fig(s, hat='corinth', hatc=GOLD, crest=(60, 100, 190), torso='armor', tc=GOLD, tc2=(170, 124, 40), sleeve=SKIN,
            legs='greaves', lc=SKIN, boots=GOLD, rh=('spear', STEEL), lh=('shield', BRONZE, (60, 100, 190), 'round', GOLD),
            geo=dict(head=(11, 5, 20, 13)))
    s.poly([(11, 21), (20, 21), (21, 25), (10, 25)], (236, 232, 220))
    for x in (12, 15, 18):
        s.rect(x, 22, x, 25, (190, 50, 50))
    s.rect(15, 1, 16, 3, (60, 100, 190))


@reg('player_leonidas')
def _(s, r):
    g = fig(s, hat='corinth', hatc=BRONZE, crest=(200, 40, 40), torso='bare', tc=(110, 30, 34), tc2=LEATHER,
            legs='greaves', lc=SKIN, boots=BRONZE, cloak=(196, 40, 40), rh=('spear', STEEL),
            lh=('shield', BRONZE, (150, 30, 30), 'lambda', (150, 100, 44)), skin=TAN, geo=dict(head=(11, 5, 20, 13)))
    s.poly([(21, 13), (25, 13), (27, 26), (23, 27), (22, 22)], (196, 40, 40))
    s.rect(13, 14, 18, 14, BLACK)


@reg('player_alexander')
def _(s, r):
    g = fig(s, hair='curly', hairc=BLOND, hat='circlet', hatc=GOLD, hat2=WHITE, torso='armor', tc=(236, 232, 220),
            tc2=GOLD, sleeve=SKIN, legs='greaves', lc=SKIN, boots=GOLD, cloak=(124, 50, 150), rh=('sword', (226, 230, 240), 12),
            pauldron=GOLD, mouth=True, eye=(70, 110, 170))
    s.poly([(11, 21), (20, 21), (21, 25), (10, 25)], (236, 232, 220))
    for x in (12, 15, 18):
        s.rect(x, 22, x, 25, (124, 50, 150))
    s.poly([(7, 13), (10, 13), (9, 26), (5, 27)], (124, 50, 150))
    PX(s, [(15, 17), (16, 17), (15, 18), (16, 18)], (190, 60, 60))


@reg('player_aristotle')
def _(s, r):
    fig(s, hair='short', hairc=BROWN, beard='short', beardc=BROWN, torso='toga', tc=(84, 130, 184), tc2=(56, 96, 150),
        boots=LEATHER, lh=('scroll',), arms=('fwd', 'down'), rh=('staff', None, 'knob'))


@reg('player_plato')
def _(s, r):
    fig(s, hair='short', hairc=(90, 84, 90), beard='long', beardc=(90, 84, 90), torso='toga', tc=(150, 84, 150),
        tc2=(110, 56, 116), boots=LEATHER, rh=('book', (150, 110, 60)), arms=('down', 'fwd'), hat='headband', hatc=GOLD,
        geo=dict(tw=7, bw=6), brow=True)


@reg('player_socrates')
def _(s, r):
    fig(s, hair='bald_fringe', hairc=WHITE, beard='short', beardc=WHITE, torso='toga', tc=(240, 238, 228),
        tc2=(196, 192, 180), boots=SKIN, rh=('cup', (150, 110, 70)), arms=('down', 'up'), mouth=True,
        geo=dict(bw=6, head=(11, 5, 20, 13)))


@reg('player_pythagoras')
def _(s, r):
    g = fig(s, hat='turban', hatc=(240, 238, 228), hat2=GOLD, beard='long', beardc=WHITE, torso='robe', tc=(240, 238, 228),
            tc2=GOLD, boots=LEATHER, arms=('down', 'up'), skin=TAN, geo=dict(head=(11, 6, 20, 14), sh=14, arm=(15, 21)))
    t = s.lit((255, 220, 90))
    s.line([(22, 7), (29, 7), (29, 1), (22, 7)], t)


@reg('player_diogenes')
def _(s, r):
    s.ell(1, 12, 12, 29, (170, 110, 70)); s.ell(3, 12, 10, 16, (70, 44, 36)); s.line([(1, 21), (12, 21)], (120, 76, 50))
    fig(s, hair='bald_fringe', hairc=GREY, beard='huge', beardc=GREY, torso='bare', tc=(170, 150, 110), tc2=(120, 104, 76),
        legs='bare', boots=None, skin=TAN, rh=('lantern',), lh=('staff', None, 'knob'), arms=('down', 'up'),
        geo=dict(tw=5, bw=4, head=(12, 5, 21, 14), sh=14))


@reg('player_da_vinci')
def _(s, r):
    g = fig(s, size='robed', hair='long', hairc=(226, 222, 214), beard='huge', beardc=(236, 232, 224), hat='beret',
            hatc=(110, 40, 44), torso='robe', tc=(160, 76, 80), tc2=(110, 44, 50), lh=('book', (214, 190, 140)),
            arms=('fwd', 'up'), brow=True)
    s.line([(23, 9), (26, 3)], WOOD); PX(s, [(26, 2), (27, 1)], s.lit((90, 190, 255)))


@reg('player_hermes')
def _(s, r):
    g = fig(s, hair='curly', hairc=BROWN, hat='winged', hatc=GOLD, torso='skirt', tc=(240, 238, 228), tc2=GOLD,
            sleeve=SKIN, legs='bare', boots=GOLD, cloak=(110, 170, 220), mouth=True, rh=('staff', (90, 190, 100), 'snake', GOLD),
            geo=dict(tw=5, bw=4))
    PX(s, [(10, 27), (9, 26), (9, 27), (21, 27), (22, 26), (22, 27)], WHITE)
    hx = g['hands'][1][0] + 2
    PX(s, [(hx - 2, 8), (hx - 3, 7), (hx + 2, 8), (hx + 3, 7), (hx - 1, 8), (hx + 1, 8)], WHITE)


@reg('player_prometheus')
def _(s, r):
    g = fig(s, size='large', hair='wild', hairc=(60, 44, 40), beard='short', beardc=(60, 44, 40), torso='bare',
            tc=(236, 232, 220), tc2=GOLD, legs='bare', boots=None, skin=TAN, arms=('down', 'up'), rh=('torch',),
            brow=True, geo=dict(head=(11, 6, 20, 14), sh=14, arm=(15, 22), tw=6, aw=3))
    s.rect(6, 20, 8, 21, IRON); PX(s, [(6, 23), (5, 25), (6, 27)], STEEL)
    s.rect(23, 11, 25, 12, IRON)


@reg('player_theseus')
def _(s, r):
    g = fig(s, hair='short', hairc=DARK, hat='headband', hatc=(200, 50, 50), torso='skirt', tc=(70, 116, 190), tc2=GOLD,
            sleeve=SKIN, legs='bare', boots=LEATHER, rh=('sword', BRONZE, 9), lh=('ball', (210, 50, 50)), mouth=True)
    s.line([(8, 24), (6, 27), (9, 29), (13, 30)], (210, 50, 50))


@reg('player_odysseus')
def _(s, r):
    g = fig(s, hair='short', hairc=BROWN, hat='pilos', hatc=(190, 160, 110), beard='short', beardc=BROWN, torso='skirt',
            tc=(160, 70, 54), tc2=LEATHER, sleeve=SKIN, legs='bare', boots=LEATHER, cloak=(50, 96, 130),
            lh=('bow', (120, 84, 50)), rh=('sword', STEEL, 7), brow=True)


@reg('player_boudicca')
def _(s, r):
    red = (206, 80, 36)
    g = fig(s, hair='long', hairc=red, torso='dress', tc=(60, 130, 90), tc2=GOLD, sleeve=SKIN, cloak=(60, 84, 150),
            rh=('spear', STEEL), boots=LEATHER, brow=True, lh=('shield', (60, 84, 150), GOLD, 'round'), eye=(60, 110, 70))
    s.rect(9, 7, 10, 22, red); s.rect(21, 7, 22, 22, red)
    for y in (17, 20, 24, 27):
        PX(s, [(x, y) for x in range(9, 23, 3) if s.img.getpixel((x, y))[:3] == (60, 130, 90)], (50, 90, 150))
    s.rect(13, 13, 18, 13, GOLD); PX(s, [(13, 10), (18, 10)], (70, 110, 200))


@reg('player_joan')
def _(s, r):
    st = (190, 196, 214)
    g = fig(s, hair='short', hairc=(70, 50, 44), torso='armor', tc=st, tc2=(130, 136, 160), legs='greaves',
            lc=(130, 136, 160), boots=st, lh=('banner', (244, 242, 232), GOLD), rh=('sword', (226, 230, 240), 10),
            pauldron=st, sleeve=(160, 166, 190), hands=st, mouth=True)
    s.rect(11, 9, 12, 12, (70, 50, 44)); s.rect(19, 9, 20, 12, (70, 50, 44))


@reg('player_musashi')
def _(s, r):
    g = fig(s, hair='topknot', hairc=BLACK, beard='stubble', torso='tunic', tc=(64, 76, 110), tc2=(40, 44, 60),
            lc=(50, 50, 64), boots=(214, 190, 140), rh=('katana', None, (230, 226, 214)), lh=('katana', None, (230, 226, 214)),
            brow=True, skin=TAN)
    s.poly([(13, 13), (18, 13), (16, 17), (15, 17)], WHITE)
    s.rect(11, 22, 20, 26, (50, 50, 64)); s.rect(15, 23, 16, 28, (36, 36, 48))


@reg('player_hildegard')
def _(s, r):
    f = s.lit((255, 220, 110))
    g = fig(s, size='robed', hat='wimple', hatc=(50, 48, 60), hat2=WHITE, torso='robe', tc=(56, 54, 68), tc2=WHITE,
            lh=('book', (150, 50, 50)), rh=('staff', None, 'cross'), arms=('fwd', 'down'), mouth=True)
    PX(s, [(15, 3), (16, 3), (15, 4), (16, 4), (15, 1), (12, 3), (19, 3), (13, 1), (18, 1)], f)


@reg('player_merlin')
def _(s, r):
    st = s.lit((255, 240, 150))
    g = fig(s, size='robed', hair='long', hairc=WHITE, beard='huge', beardc=WHITE, hat='wizard', hatc=(50, 76, 170),
            hat2=GOLD, torso='robe', tc=(56, 84, 180), tc2=(36, 56, 130), trim=False,
            rh=('staff', (130, 230, 255), 'orb'), brow=True)
    PX(s, [(15, 4), (17, 2), (10, 22), (20, 24), (12, 27), (21, 19), (9, 26)], st)


@reg('player_sherlock')
def _(s, r):
    tw_ = (150, 120, 84)
    g = fig(s, hair='short', hairc=DARK, hat='deerstalker', hatc=tw_, hat2=(110, 84, 56), torso='suit', tc=tw_,
            tc2=(60, 50, 60), lc=(70, 60, 56), boots=DARK, cloak=(120, 92, 62), geo=dict(head=(11, 5, 20, 13)))
    s.poly([(9, 13), (22, 13), (24, 18), (7, 18)], (130, 100, 68)); s.poly([(14, 13), (17, 13), (16, 16), (15, 16)], WHITE)
    s.line([(17, 12), (20, 13)], BROWN); s.rect(20, 11, 21, 13, BROWN); PX(s, [(21, 9), (22, 7)], (200, 200, 206))
    s.ell(24, 14, 29, 19, GOLD); s.ell(25, 15, 28, 18, s.lit((180, 230, 250))); s.line([(24, 20), (23, 22)], GOLD)
    PX(s, [(13, 5), (16, 6), (18, 5), (14, 7)], (110, 84, 56))


@reg('player_tesla')
def _(s, r):
    z = s.lit((150, 210, 255)); w = s.lit((240, 250, 255))
    g = fig(s, hair='part', hairc=BLACK, beard='stache', beardc=BLACK, torso='suit', tc=(54, 56, 76), tc2=(40, 40, 50),
            lc=(44, 46, 62), boots=DARK, arms=('up', 'up'), geo=dict(head=(11, 7, 20, 15), sh=15, waist=24, arm=(16, 22)))
    s.line([(8, 8), (10, 5), (12, 6), (14, 3), (17, 5), (19, 2), (21, 5), (23, 8)], z, 2)
    s.line([(10, 5), (12, 6), (14, 3), (17, 5), (19, 2), (21, 5)], w)
    PX(s, [(5, 6), (26, 5), (7, 3), (24, 2), (4, 10), (27, 10)], z)


@reg('player_nietzsche')
def _(s, r):
    st = (124, 86, 54)
    fig(s, hair='part', hairc=(60, 44, 36), torso='suit', tc=(84, 70, 64),
        tc2=(120, 40, 44), lc=(60, 52, 50), boots=DARK, lh=('book', (120, 40, 44)), arms=('fwd', 'down'), brow=True,
        rh=('staff', None, 'knob', DARK))
    s.rect(12, 10, 19, 11, st); PX(s, [(11, 11), (20, 11), (11, 12), (12, 12), (19, 12), (20, 12), (12, 13), (19, 13)], st)


@reg('player_lovelace')
def _(s, r):
    g = fig(s, hair='short', hairc=(60, 40, 40), torso='dress', tc=(130, 72, 156), tc2=GOLD, lh=('book', (214, 200, 150)),
            arms=('fwd', 'down'), mouth=(200, 90, 100), geo=dict(tw=5, bw=5, head=(11, 5, 20, 14), sh=14))
    s.rect(9, 8, 11, 13, (60, 40, 40)); s.rect(20, 8, 22, 13, (60, 40, 40)); s.rect(15, 5, 16, 7, SKIN)
    PX(s, [(13, 5), (18, 5)], (240, 150, 170))
    s.poly([(12, 14), (19, 14), (17, 16), (14, 16)], WHITE)
    PX(s, [(13, 19), (15, 19), (14, 21)], DARK)
    s.ell(22, 19, 27, 24, BRONZE); PX(s, [(24, 18), (25, 18), (24, 25), (25, 25), (21, 21), (21, 22), (28, 21), (28, 22)], BRONZE)
    s.rect(24, 21, 25, 22, DARK)


@reg('player_geralt')
def _(s, r):
    e = s.lit((255, 200, 60))
    s.line([(17, 12), (24, 3)], STEEL, 2); s.line([(20, 13), (27, 5)], (200, 204, 220), 2)
    PX(s, [(25, 2), (28, 4)], GOLD)
    g = fig(s, hair='long', hairc=WHITE, beard='short', beardc=WHITE, torso='armor', tc=(64, 62, 74), tc2=(110, 104, 110),
            lc=(50, 48, 58), boots=DARK, lh=('sword', (220, 224, 236), 11), eye=e, brow=True, pauldron=(90, 86, 96))
    PX(s, [(15, 17), (16, 17)], STEEL); s.line([(10, 14), (21, 20)], LEATHER)
    s.line([(13, 6), (13, 9)], (190, 120, 110))


@reg('player_ciri')
def _(s, r):
    e = s.lit((120, 240, 170))
    s.line([(18, 13), (25, 4)], STEEL, 2); PX(s, [(26, 3)], GOLD)
    g = fig(s, hair='pony', hairc=(210, 206, 196), tc=(236, 232, 220), tc2=(110, 76, 50), lc=(96, 70, 50), boots=(70, 50, 40),
            eye=(60, 150, 100), rh=('sword', (200, 230, 230), 10), geo=dict(tw=5, bw=4, head=(11, 5, 20, 14), sh=14, arm=(15, 21)))
    s.rect(11, 17, 20, 21, (110, 76, 50)); PX(s, [(15, 18), (15, 20)], (236, 232, 220))
    s.line([(13, 11), (13, 12)], (190, 110, 110)); s.rect(7, 19, 9, 20, (60, 50, 50))
    PX(s, [(27, 9), (29, 12), (25, 13)], e)


@reg('player_ash_ketchum')
def _(s, r):
    g = fig(s, hair='short', hairc=BLACK, hat='peak', hatc=(214, 50, 50), hat2=(214, 50, 50), torso='tunic', tc=(60, 104, 196),
            tc2=DARK, sleeve=WHITE, hands=(70, 150, 90), lc=(110, 150, 214), boots=(40, 40, 50), mouth=True,
            arms=('down', 'up'), geo=dict(head=(11, 6, 20, 15), sh=15, waist=24, arm=(16, 22)))
    s.rect(15, 16, 16, 22, (236, 220, 110))
    PX(s, [(12, 12), (19, 12)], (150, 90, 70)); PX(s, [(10, 10), (10, 12), (21, 10), (21, 12), (11, 11), (20, 11)], BLACK)
    s.ell(21, 3, 27, 9, WHITE); PX(s, [(x, y) for x, y in ell_pts(21, 3, 27, 9) if y <= 5], (220, 50, 50))
    s.line([(21, 6), (27, 6)], DARK); PX(s, [(24, 6)], WHITE)


@reg('player_ash_williams')
def _(s, r):
    g = fig(s, hair='short', hairc=(60, 44, 40), beard='stubble', tc=(70, 110, 180), tc2=LEATHER, lc=(110, 84, 60),
            boots=(60, 44, 40), brow=True, arms=('up', 'down'), geo=dict(head=(11, 5, 20, 13)))
    # boomstick over the left shoulder, chainsaw for a right hand
    s.rect(7, 1, 8, 7, (70, 70, 80)); s.rect(7, 7, 9, 10, WOOD)
    s.rect(22, 18, 27, 23, (200, 60, 50)); s.rect(23, 19, 25, 20, (60, 60, 70))
    s.rect(24, 23, 27, 30, (190, 194, 206)); s.rect(25, 24, 26, 29, (120, 124, 140))
    PX(s, [(23, 24), (23, 26), (23, 28), (28, 25), (28, 27), (28, 29)], (90, 90, 100))
    s.line([(11, 14), (20, 22)], LEATHER); s.line([(17, 6), (18, 9)], (190, 90, 80))


@reg('player_dad')
def _(s, r):
    polo = (70, 160, 140)
    g = fig(s, hair='short', hairc=(110, 80, 56), beard='stache', beardc=(110, 80, 56), tc=polo, tc2=(110, 84, 60),
            sleeve=SKIN, lc=(196, 176, 130), boots=WHITE, mouth=WHITE, lh=('mug', WHITE), arms=('up', 'down'),
            geo=dict(tw=6, bw=6, head=(11, 5, 20, 14), sh=14, arm=(15, 21)))
    s.rect(7, 13, 9, 15, polo); s.rect(22, 15, 24, 17, polo)
    s.poly([(13, 14), (18, 14), (16, 16), (15, 16)], WHITE)
    s.rect(12, 25, 14, 27, SKIN); s.rect(17, 25, 19, 27, SKIN)
    PX(s, [(14, 12), (17, 12)], (190, 110, 100))
    s.rect(22, 20, 24, 22, SKIN); s.rect(23, 18, 23, 20, SKIN)
