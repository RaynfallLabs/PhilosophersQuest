"""Monsters of the monster_A slice: goblinoids, orcs, gnolls, kobolds, trolls,
giants, bandits, cultists, fey and the named ones. Offline tooling."""
from rig import *  # noqa: F401,F403
from rig import fig, item, PX, dk, lt, Sprite

R = {}


def reg(*ids):
    def deco(f):
        for i in ids:
            R[i] = f
        return f
    return deco


YEL = (250, 220, 60)
REDEYE = (240, 70, 50)
GRN = (130, 240, 110)
VIO = (210, 120, 255)
CYAN = (130, 220, 255)
ICE = (190, 235, 255)


# =================================================================== goblins
def gob(s, **k):
    d = dict(size='small', head='goblin', skin=(104, 160, 70), eye=YEL, lit=(YEL,), tc=(124, 84, 50), lc=DARK)
    d.update(k)
    return fig(s, **d)


@reg('goblin')
def _(s, r):
    gob(s, skin=(110, 168, 62), rh=('dagger', (176, 130, 100)), hair='tuft', hairc=DARK)


@reg('goblin_king')
def _(s, r):
    gob(s, skin=(70, 160, 86), hat='crown', hatc=GOLD, cloak=(170, 40, 44), tc=(110, 60, 140), tc2=GOLD,
        rh=('staff', (255, 90, 90), 'orb', GOLD), geo=dict(tw=5, bw=5))


@reg('goblin_kingslayer')
def _(s, r):
    g = gob(s, skin=(120, 140, 110), hat='hood', hatc=(96, 62, 160), tc=(60, 46, 84), tc2=(96, 62, 160),
            cloak=(50, 38, 70), eye=GRN, lit=(GRN,), rh=('sword', s.lit((150, 240, 120)), 8), lh=('dagger',))
    PX(s, [(22, 21), (23, 23)], s.lit((150, 240, 120)))


@reg('goblin_shaman')
def _(s, r):
    gob(s, skin=(90, 190, 112), hat='headdress', hatc=(230, 80, 60), hat2=(250, 200, 70), torso='fur',
        tc=(130, 110, 80), tc2=BONE, rh=('staff', GRN, 'skull'), eye=GRN, lit=(GRN,))
    PX(s, [(13, 18), (15, 19), (17, 19), (19, 18)], BONE)


@reg('goblin_sniper')
def _(s, r):
    skin, hood, tunic = (104, 160, 70), (58, 84, 52), (124, 84, 50)
    eye = s.lit((250, 220, 60))
    s.rect(13, 23, 14, 27, DARK); s.rect(17, 23, 18, 27, DARK)
    s.rect(12, 28, 14, 28, LEATHER); s.rect(17, 28, 19, 28, LEATHER)
    s.rect(12, 16, 19, 23, tunic); s.line([(12, 21), (19, 21)], DARK)
    s.poly([(11, 12), (5, 8), (10, 14)], skin); s.poly([(20, 12), (26, 8), (21, 14)], skin)
    s.ell(11, 8, 20, 16, skin)
    s.poly([(10, 11), (12, 7), (15, 5), (17, 5), (20, 7), (21, 11), (18, 9), (13, 9)], hood)
    s.px([(14, 12), (18, 12)], eye); s.line([(15, 14), (17, 14)], DARK)
    s.rect(9, 17, 11, 19, skin); s.rect(20, 17, 22, 20, skin)
    s.line([(8, 9), (6, 13), (5, 18), (6, 23), (8, 27)], WOOD)
    s.line([(8, 10), (8, 26)], STRING)
    s.line([(9, 18), (15, 18)], WOOD); s.px([(15, 18), (16, 18)], STEEL)


@reg('goblin_warpriest')
def _(s, r):
    gob(s, skin=(120, 150, 70), hat='mitre', hatc=(170, 60, 44), hat2=GOLD, torso='robe', tc=(170, 70, 48),
        tc2=GOLD, rh=('censer', GOLD, FIRE), lh=('mace', IRON), arms=('down', 'down'))


@reg('redcap')
def _(s, r):
    g = fig(s, size='small', head='hob', skin=(170, 180, 150), eye=REDEYE, lit=(REDEYE,), beard='long',
            beardc=WHITE, hat='cap', hatc=(200, 30, 34), tc=(90, 80, 70), lc=(70, 60, 54), boots=IRON,
            rh=('pike', STEEL))
    s.poly([(11, 10), (20, 10), (22, 6), (17, 5), (12, 6)], (200, 30, 34))
    s.rect(11, 27, 14, 28, IRON); s.rect(17, 27, 20, 28, IRON)


def lep(s, coat, angry, **k):
    g = fig(s, size='small', skin=SKIN, hair='short', hairc=(210, 96, 40), beard='short', beardc=(210, 96, 40),
            tc=coat, tc2=DARK, lc=(230, 226, 210), boots=DARK, brow=angry, **k)
    x0, y0, x1, y1 = g['head']
    s.rect(x0 - 1, y0 + 1, x1 + 1, y0 + 2, coat); s.rect(x0 + 2, y0 - 4, x1 - 2, y0, coat)
    s.rect(x0 + 2, y0 - 1, x1 - 2, y0, DARK); s.rect(15, y0 - 1, 16, y0, GOLD)
    return g


@reg('leprechaun')
def _(s, r):
    lep(s, (60, 170, 80), False)
    s.rect(3, 23, 8, 28, (60, 56, 70)); s.rect(2, 23, 9, 23, (60, 56, 70)); s.rect(3, 21, 8, 22, s.lit((255, 220, 80)))
    PX(s, [(5, 20), (6, 20)], s.lit((255, 220, 80)))


@reg('leprechaun_hostile')
def _(s, r):
    lep(s, (36, 120, 50), True, rh=('greatclub', (90, 60, 40)), eye=REDEYE, lit=(REDEYE,))


@reg('boggart')
def _(s, r):
    g = fig(s, size='small', head='bugbear', skin=(104, 76, 50), muzzle=(150, 116, 80), eye=YEL, lit=(YEL,),
            torso='bare', belly=(140, 106, 72), tc=(70, 50, 36), tc2=(70, 50, 36), legs='bare', boots=None,
            hair='wild', hairc=(70, 50, 36), lh=('claws',), rh=('claws',), geo=dict(arm=(17, 23), aw=2))
    PX(s, [(13, 12), (14, 12), (17, 12), (18, 12)], YEL)


@reg('changeling')
def _(s, r):
    g = fig(s, size='child', skin=(176, 196, 160), hair='long', hairc=(220, 226, 200), tc=(200, 200, 190),
            tc2=(150, 150, 140), legs='bare', boots=None, torso='tunic', geo=dict(head=(10, 8, 21, 19)))
    s.rect(13, 13, 14, 15, DARK); s.rect(17, 13, 18, 15, DARK); PX(s, [(13, 13), (17, 13)], s.lit((200, 160, 255)))
    PX(s, [(15, 17), (16, 17)], dk((176, 196, 160), 2))
    PX(s, [(9, 12), (22, 12), (8, 11), (23, 11)], (176, 196, 160))


@reg('spriggan')
def _(s, r):
    bark = (104, 120, 74)
    g = fig(s, size='stout', skin=bark, eye=GRN, lit=(GRN,), torso='bare', belly=(140, 150, 96), tc=(70, 84, 50),
            tc2=(70, 84, 50), legs='bare', boots=None, hat='antlers', hatc=(90, 70, 44), brow=True,
            geo=dict(head=(10, 6, 21, 16), aw=4, arm=(17, 25)))
    s.ell(5, 22, 10, 27, (96, 110, 68)); s.ell(21, 22, 26, 27, (96, 110, 68))
    s.line([(13, 14), (18, 14)], DARK)
    PX(s, [(12, 8), (19, 9), (14, 19), (18, 21), (7, 19), (24, 18)], (70, 84, 50))
    PX(s, [(9, 5), (22, 4), (16, 5)], (90, 190, 80))


@reg('pixie_swarm')
def _(s, r):
    s.shadow = False
    cols = [(255, 150, 255), (200, 120, 255), (140, 220, 255), (255, 230, 140)]
    wing = (236, 226, 255)
    spots = [(8, 8, 0), (20, 6, 1), (14, 14, 2), (24, 16, 0), (7, 20, 3), (17, 23, 1), (26, 25, 2), (11, 27, 0)]
    for x, y, i in spots:
        c = s.lit(cols[i])
        s.poly([(x - 1, y), (x - 4, y - 3), (x - 3, y + 1)], wing); s.poly([(x + 2, y), (x + 5, y - 3), (x + 4, y + 1)], wing)
        s.rect(x, y - 1, x + 1, y + 2, c); PX(s, [(x, y - 2), (x + 1, y - 2)], SKIN)
    PX(s, [(4, 13), (28, 9), (21, 12), (12, 20), (22, 29), (3, 27), (15, 3)], s.lit((255, 250, 210)))


# =================================================================== hobgoblins / bugbears
HOB = (206, 122, 64)


def hob(s, **k):
    d = dict(size='med', head='hob', skin=HOB, eye=YEL, lit=(YEL,), torso='armor', lc=(60, 50, 50), boots=DARK)
    d.update(k)
    return fig(s, **d)


@reg('hobgoblin')
def _(s, r):
    hob(s, tc=(70, 110, 60), tc2=(44, 70, 44), hat='helm', hatc=IRON, rh=('sword',), hair='topknot', hairc=DARK)


@reg('hobgoblin_captain')
def _(s, r):
    hob(s, tc=(84, 134, 60), tc2=(50, 84, 44), hat='spike', hatc=STEEL, hat2=(200, 50, 50), rh=('sword',),
        lh=('shield', (150, 50, 46), GOLD, 'kite'), pauldron=STEEL)


@reg('hobgoblin_marshal')
def _(s, r):
    hob(s, tc=(180, 60, 60), tc2=GOLD, hat='spike', hatc=GOLD, hat2=(240, 240, 230), rh=('sword', STEEL, 13),
        cloak=(120, 30, 40), pauldron=GOLD, lh=('banner', (180, 50, 50), GOLD))


@reg('hobgoblin_warlord')
def _(s, r):
    hob(s, size='large', tc=(160, 90, 30), tc2=(96, 50, 20), hat='horned', hatc=IRON, rh=('greataxe',),
        cloak=(96, 70, 50), pauldron=IRON)


@reg('bugbear')
def _(s, r):
    f = (160, 120, 66)
    fig(s, size='large', head='bugbear', skin=f, eye=YEL, lit=(YEL,), torso='bare', belly=(196, 160, 100),
        tc=(96, 66, 44), tc2=DARK, legs='bare', boots=None, rh=('club',), lh=('claws',))


@reg('bugbear_chieftain')
def _(s, r):
    f = (176, 96, 46)
    g = fig(s, size='large', head='bugbear', skin=f, eye=REDEYE, lit=(REDEYE,), torso='bare', belly=(214, 150, 96),
            tc=(90, 50, 36), tc2=GOLD, legs='bare', boots=None, rh=('morningstar',), pauldron=BONE,
            hat='headband', hatc=(200, 40, 40), cloak=(80, 60, 50))
    for x in (11, 15, 19):
        s.ell(x, 22, x + 2, 24, BONE); PX(s, [(x + 1, 23)], DARK)


# =================================================================== orcs
ORC = (96, 128, 92)


def orc(s, **k):
    d = dict(size='large', head='orc', skin=ORC, eye=REDEYE, lit=(REDEYE,), tc=(112, 78, 52), lc=DARK)
    d.update(k)
    return fig(s, **d)


@reg('orc_archer')
def _(s, r):
    skin, hide = (96, 128, 92), (112, 78, 52)
    eye = s.lit((240, 70, 50))
    s.rect(11, 22, 14, 28, DARK); s.rect(17, 22, 20, 28, DARK)
    s.rect(10, 28, 14, 29, LEATHER); s.rect(17, 28, 21, 29, LEATHER)
    s.poly([(9, 13), (22, 13), (21, 23), (10, 23)], hide)
    s.line([(10, 14), (21, 22)], DARK); s.line([(10, 21), (21, 21)], LEATHER)
    s.rect(6, 14, 9, 21, skin); s.rect(22, 14, 25, 21, skin)
    s.ell(5, 12, 10, 16, IRON)
    s.ell(11, 5, 20, 13, skin); s.rect(12, 11, 19, 14, skin)
    s.line([(13, 7), (18, 7)], DARK); s.px([(14, 8), (17, 8)], eye)
    s.px([(13, 12), (13, 11), (18, 12), (18, 11)], IVORY)
    s.line([(14, 13), (17, 13)], DARK)
    s.rect(15, 2, 16, 5, DARK)
    s.line([(26, 6), (28, 11), (29, 16), (28, 21), (26, 26)], WOOD)
    s.line([(26, 7), (26, 25)], STRING)


@reg('orc_berserker')
def _(s, r):
    g = orc(s, skin=(110, 140, 90), torso='bare', tc=(120, 60, 40), tc2=DARK, hair='mohawk', hairc=(220, 70, 30),
            rh=('axe', STEEL, WOOD, 1), lh=('axe', STEEL, WOOD, 1), geo=dict(tw=6, aw=3))
    red = (214, 60, 40)
    s.line([(11, 15), (14, 18)], red); s.line([(20, 15), (17, 18)], red); PX(s, [(12, 7), (19, 7), (13, 20), (18, 20)], red)


@reg('orc_marauder')
def _(s, r):
    orc(s, skin=(104, 124, 84), torso='armor', tc=(150, 70, 44), tc2=(96, 44, 30), hat='helm', hatc=IRON,
        rh=('axe', STEEL, WOOD, 1), lh=('shield', (110, 76, 50), STEEL, 'spiked'), pauldron=IRON, geo=dict(tw=6, aw=3))


@reg('orc_priest')
def _(s, r):
    orc(s, torso='robe', tc=(166, 62, 50), tc2=BONE, hat='skullmask', rh=('greatclub', BONE), geo=dict(tw=6, aw=3),
        lh=('orb', (255, 90, 90)))


@reg('orc_scout')
def _(s, r):
    orc(s, size='med', skin=(110, 150, 80), hat='hood', hatc=(74, 96, 56), tc=(120, 96, 60), rh=('sword', STEEL, 8),
        cloak=(64, 84, 50))


@reg('orc_shaman')
def _(s, r):
    orc(s, skin=(100, 130, 100), torso='robe', tc=(112, 72, 170), tc2=BONE, hat='headdress', hatc=(230, 90, 60),
        hat2=(120, 200, 230), rh=('staff', VIO, 'skull'), eye=VIO, lit=(VIO,), geo=dict(tw=6, aw=3))


@reg('orc_warbringer')
def _(s, r):
    g = orc(s, torso='armor', tc=(190, 76, 40), tc2=(110, 44, 30), lh=('banner', (200, 50, 36), BONE),
            rh=('horn',), hair='topknot', hairc=DARK, pauldron=BONE, geo=dict(tw=6, aw=3), arms=('down', 'down'))


@reg('orc_warchief')
def _(s, r):
    g = orc(s, skin=(100, 124, 84), torso='armor', tc=(80, 70, 74), tc2=(210, 60, 30), hat='horned', hatc=IRON,
            rh=('hammer',), cloak=(130, 100, 70), pauldron=IRON)
    PX(s, [(13, 9), (18, 9), (13, 10), (18, 10)], (220, 60, 30))


@reg('orc_warlord')
def _(s, r):
    g = orc(s, size='giant', skin=(90, 116, 80), torso='armor', tc=(56, 50, 60), tc2=GOLD, hat='crown', hatc=IRON,
            hat2=(240, 60, 40), rh=('greataxe', STEEL, DARK), cloak=(190, 40, 30), pauldron=(56, 50, 60),
            geo=dict(head=(11, 3, 20, 11), sh=11, arm=(12, 21), waist=22, tw=8, bw=7))
    PX(s, [(7, 10), (6, 9), (24, 10), (25, 9)], STEEL)


@reg('orc_warrior')
def _(s, r):
    g = orc(s, skin=(92, 132, 70), torso='armor', tc=(104, 100, 96), tc2=(70, 66, 66), rh=('axe', STEEL, WOOD, 1),
            hair='topknot', hairc=DARK, geo=dict(tw=6, aw=3))
    s.ell(6, 11, 11, 15, (150, 110, 60))


@reg('dread_orc_champion')
def _(s, r):
    g = orc(s, size='giant', skin=(128, 70, 60), torso='armor', tc=(44, 40, 50), tc2=(220, 44, 30), hat='horned',
            hatc=(44, 40, 50), hat2=(220, 44, 30), rh=('cleaver', (190, 60, 50), DARK), pauldron=(44, 40, 50),
            eye=s.lit((255, 120, 40)), geo=dict(head=(11, 3, 20, 11), sh=11, arm=(12, 21), waist=22, tw=8, bw=7))
    PX(s, [(6, 9), (5, 8), (25, 9), (26, 8), (8, 9), (23, 9)], STEEL)
    PX(s, [(5, 22), (5, 24), (6, 26), (7, 27), (9, 28)], STEEL)


# =================================================================== gnolls
def gnoll(s, **k):
    f = k.get('skin', (196, 156, 96))
    d = dict(size='med', head='gnoll', skin=f, muzzle=(70, 56, 50), eye=YEL, lit=(YEL,), torso='bare',
             belly=lt(f), tc=(110, 72, 46), tc2=DARK, legs='bare', boots=None, hair='mohawk', hairc=(70, 50, 40),
             tail=True)
    d.update(k)
    g = fig(s, **d)
    sp = dk(f, 2)
    a0 = g['arm'][0]
    PX(s, [(g['lax'][0], a0 + 1), (g['lax'][1], a0 + 4), (g['rax'][1], a0 + 2), (g['rax'][0], a0 + 5),
           (g['tl'] + 1, g['sh'] + 2), (g['tr'] - 1, g['sh'] + 3), (12, g['waist'] + 2), (19, g['waist'] + 3)], sp)
    return g


@reg('gnoll')
def _(s, r):
    gnoll(s, lh=('claws',), rh=('claws',))


@reg('gnoll_archer')
def _(s, r):
    gnoll(s, skin=(204, 172, 108), rh=('bow', (150, 110, 60)), torso='vest', tc=(120, 84, 54), lh=('claws',))
    s.rect(9, 9, 10, 14, LEATHER); PX(s, [(9, 8), (10, 7)], (220, 60, 50))


@reg('gnoll_fang_of_yeenoghu')
def _(s, r):
    gnoll(s, skin=(200, 116, 62), rh=('flail', IRON), hat='headband', hatc=(220, 40, 40), eye=REDEYE, lit=(REDEYE,),
          pauldron=BONE)


@reg('gnoll_pack_lord')
def _(s, r):
    gnoll(s, size='large', skin=(206, 136, 60), rh=('glaive',), cloak=(120, 44, 36), torso='vest', tc=(96, 60, 44),
          pauldron=IRON)


@reg('gnoll_alpha_of_yeenoghu')
def _(s, r):
    g = gnoll(s, size='giant', skin=(124, 50, 44), muzzle=(40, 30, 36), belly=(170, 80, 60), eye=s.lit((255, 200, 60)),
              rh=('greataxe', BONE, (120, 100, 80)), hairc=(30, 24, 30), pauldron=BONE, tc=(50, 40, 44),
              geo=dict(head=(11, 3, 20, 11), sh=11, arm=(12, 21), waist=22, tw=8, bw=7))
    PX(s, [(12, 13), (14, 14), (17, 14), (19, 13)], BONE)


# =================================================================== kobolds
def kobold(s, scale, belly, horn=IVORY, crest=None, robe=None):
    eye = s.lit((250, 230, 80))
    s.poly([(12, 21), (6, 25), (3, 23), (6, 28), (13, 25)], scale)
    return eye


def kob_body(s, scale, belly, eye, horn=IVORY, crest=None, robe=None):
    s.rect(13, 24, 14, 27, scale); s.rect(17, 24, 18, 27, scale)
    s.rect(12, 28, 15, 28, scale); s.rect(17, 28, 20, 28, scale)
    s.ell(12, 15, 19, 25, robe or scale)
    if not robe:
        s.ell(14, 18, 18, 24, belly)
    s.rect(19, 18, 22, 19, scale)
    if crest:
        s.poly([(13, 10), (11, 6), (14, 7), (15, 4), (17, 8)], crest)
    s.ell(13, 8, 20, 15, scale); s.rect(19, 11, 24, 14, scale)
    PX(s, [(24, 12)], DARK); s.line([(20, 14), (24, 14)], DARK)
    PX(s, [(18, 11)], eye)
    if horn:
        PX(s, [(14, 8), (13, 7), (12, 6), (17, 7), (17, 6)], horn)


@reg('kobold')
def _(s, r):
    sc = (76, 150, 70)
    eye = kobold(s, sc, None)
    kob_body(s, sc, (190, 210, 130), eye)
    s.rect(24, 5, 24, 28, WOOD); s.poly([(24, 2), (23, 5), (25, 5)], STEEL); PX(s, [(24, 2), (24, 3), (24, 4)], STEEL)
    s.rect(13, 20, 18, 21, LEATHER)


@reg('kobold_dragonshield')
def _(s, r):
    sc = (200, 84, 44)
    eye = kobold(s, sc, None)
    s.rect(26, 4, 26, 28, WOOD); s.poly([(26, 1), (25, 4), (27, 4)], STEEL); PX(s, [(26, 1), (26, 2), (26, 3)], STEEL)
    kob_body(s, sc, (240, 190, 120), eye)
    s.poly([(15, 16), (25, 16), (25, 23), (20, 29), (15, 23)], (120, 30, 30))
    s.poly([(16, 17), (24, 17), (24, 23), (20, 27), (16, 23)], (190, 50, 40))
    for y in (19, 22):
        PX(s, [(17, y), (19, y + 1), (21, y), (23, y + 1)], GOLD)
    PX(s, [(20, 25)], GOLD)


@reg('kobold_pack_leader')
def _(s, r):
    sc = (214, 66, 60)
    eye = kobold(s, sc, None)
    s.poly([(12, 15), (8, 17), (6, 24), (12, 23)], (70, 50, 80))
    kob_body(s, sc, (240, 200, 130), eye, crest=(250, 190, 60))
    s.rect(23, 9, 23, 22, WOOD); s.poly([(23, 8), (27, 6), (28, 10), (27, 14), (23, 12)], IVORY)
    s.rect(13, 20, 18, 21, DARK); PX(s, [(16, 17), (16, 18)], GOLD)


@reg('kobold_sorcerer')
def _(s, r):
    sc = (196, 96, 66)
    eye = kobold(s, sc, None)
    kob_body(s, sc, (230, 190, 120), eye, robe=(104, 60, 150))
    s.rect(15, 17, 16, 24, GOLD)
    f, h = s.lit(FIRE), s.lit(HOT)
    s.poly([(22, 18), (25, 10), (28, 18)], f); s.ell(22, 15, 28, 20, f); s.ell(24, 16, 26, 19, h)
    PX(s, [(27, 9), (22, 12), (29, 13)], f)


@reg('kobold_trapsetter')
def _(s, r):
    scale, belly, sack = (196, 110, 56), (228, 180, 120), (150, 128, 90)
    scale = (96, 170, 90); belly = (210, 220, 140)
    eye = s.lit((250, 230, 80))
    s.poly([(12, 21), (6, 25), (3, 23), (6, 28), (13, 25)], scale)
    s.ell(7, 12, 14, 20, sack); s.line([(9, 12), (12, 12)], DARK)
    kob_body(s, scale, belly, eye)
    s.rect(22, 20, 27, 21, IRON); PX(s, [(23, 19), (25, 19), (27, 19)], STEEL)


# =================================================================== reptile and water folk
@reg('lizardfolk')
def _(s, r):
    sk = (76, 156, 86)
    fig(s, head='reptile', skin=sk, eye=YEL, lit=(YEL,), torso='bare', belly=(206, 206, 130), tc=(120, 84, 54),
        tc2=DARK, legs='bare', boots=None, tail=True, crest=(224, 110, 50), lh=('club',))


@reg('lizardfolk_shaman')
def _(s, r):
    sk = (56, 190, 110)
    g = fig(s, head='reptile', skin=sk, eye=s.lit((255, 120, 220)), torso='bare', belly=(210, 230, 150),
            tc=(150, 60, 120), tc2=BONE, legs='bare', boots=None, tail=True, lh=('staff', GRN, 'skull'),
            hat='headdress', hatc=(240, 90, 60), hat2=(250, 220, 90), cloak=(110, 96, 56))
    PX(s, [(12, 15), (14, 16), (17, 16), (19, 15)], BONE)


@reg('sobek_warrior')
def _(s, r):
    sk = (70, 150, 84)
    g = fig(s, size='large', head='croc', skin=sk, eye=YEL, lit=(YEL,), torso='bare', belly=(190, 200, 120),
            tc=WHITE, tc2=GOLD, legs='bare', boots=None, tail=True, lh=('khopesh',), geo=dict(tw=6, aw=3))
    s.rect(10, 12, 21, 13, GOLD); PX(s, [(12, 14), (15, 14), (16, 14), (19, 14)], (60, 130, 200))
    s.rect(14, 22, 17, 26, (60, 130, 200)); s.line([(14, 22), (17, 22)], GOLD)
    s.rect(22, 17, 24, 17, GOLD); s.rect(7, 17, 9, 17, GOLD)


@reg('troglodyte')
def _(s, r):
    sk = (120, 128, 96)
    g = fig(s, head='reptile', skin=sk, eye=s.lit((255, 140, 60)), torso='bare', belly=(176, 176, 140),
            tc=(84, 80, 60), tc2=(84, 80, 60), legs='bare', boots=None, crest=(60, 60, 70), lh=('claws',),
            rh=('claws',), geo=dict(head=(10, 7, 19, 15), sh=14, arm=(15, 23), tw=6))
    PX(s, [(9, 16), (8, 18), (9, 20), (8, 22)], (60, 60, 70))
    PX(s, [(26, 6), (27, 4), (4, 9), (5, 7), (28, 12)], (150, 180, 90))


@reg('yuan_ti_pureblood')
def _(s, r):
    sk = (206, 190, 130)
    hood = (70, 150, 66)
    s.poly([(8, 3), (23, 3), (25, 9), (22, 15), (9, 15), (6, 9)], hood)
    PX(s, [(9, 6), (22, 6), (8, 10), (23, 10)], (230, 200, 80))
    g = fig(s, skin=sk, eye=s.lit((255, 230, 60)), torso='scale', tc=(70, 150, 66), tc2=(40, 100, 50),
            lc=(60, 70, 60), boots=DARK, rh=('saber',), geo=dict(head=(12, 5, 19, 13)), sleeve=(70, 150, 66))
    PX(s, [(13, 7), (18, 7), (14, 6), (17, 6), (12, 9), (19, 9)], (70, 150, 66))
    PX(s, [(15, 12), (16, 13)], (220, 50, 60))


@reg('bullywug')
def _(s, r):
    sk = (70, 160, 100)
    g = fig(s, size='small', head='frog', skin=sk, eye=DARK, torso='bare', belly=(200, 220, 150), tc=(110, 90, 50),
            tc2=DARK, legs='bare', boots=None, rh=('spear',), geo=dict(tw=5, bw=5, lw=3))
    s.rect(10, 28, 14, 28, sk); s.rect(17, 28, 21, 28, sk)
    PX(s, [(12, 18), (19, 19), (9, 18)], dk(sk))


@reg('kuo_toa')
def _(s, r):
    sk = (70, 112, 186)
    g = fig(s, head='fish', skin=sk, crest=(230, 120, 70), torso='bare', belly=(190, 210, 220), tc=(90, 110, 80),
            tc2=DARK, legs='bare', boots=None, rh=('trident', STEEL), lh=('shield', (120, 140, 70), (200, 220, 120), 'round'))
    PX(s, [(25, 16), (26, 17), (25, 18)], (230, 120, 70))
    s.rect(10, 29, 14, 29, sk); s.rect(17, 29, 21, 29, sk)


# =================================================================== beast-men
def were(s, **k):
    f = k['skin']
    d = dict(size='large', eye=YEL, lit=(YEL,), torso='bare', belly=lt(f), tc=(70, 80, 110), tc2=DARK,
             legs='bare', boots=None, lh=('claws',), rh=('claws',))
    d.update(k)
    return fig(s, **d)


@reg('werewolf')
def _(s, r):
    were(s, head='wolf', skin=(150, 116, 80), tail=True, legs='pants', lc=(70, 80, 110))


@reg('werewolf_alpha')
def _(s, r):
    g = were(s, head='wolf', skin=(200, 160, 84), tail=True, eye=s.lit((200, 120, 255)), arms=('up', 'up'),
             hair='mohawk', hairc=(60, 44, 50), legs='pants', lc=(60, 44, 50))
    s.poly([(9, 12), (22, 12), (19, 16), (16, 18), (15, 18), (12, 16)], (60, 44, 50))


@reg('elder_werewolf')
def _(s, r):
    g = were(s, size='giant', head='wolf', skin=(196, 196, 204), muzzle=(236, 236, 240), tail=True,
             eye=s.lit((255, 90, 60)), legs='pants', lc=(80, 60, 50),
             geo=dict(head=(11, 3, 20, 11), sh=11, arm=(12, 22), waist=22, tw=8, bw=6))
    s.line([(13, 5), (15, 9)], (150, 80, 80)); PX(s, [(9, 14), (10, 16), (22, 15), (21, 17)], (150, 150, 160))


@reg('werebear')
def _(s, r):
    were(s, size='giant', head='bear', skin=(150, 100, 60), muzzle=(214, 176, 120), belly=(190, 140, 90),
         geo=dict(head=(11, 2, 20, 10), sh=10, bw=9, tw=9, lw=5), tc=(90, 70, 110))


@reg('weretiger')
def _(s, r):
    f = (228, 140, 44)
    g = were(s, head='tiger', skin=f, muzzle=WHITE, belly=(246, 236, 214), tail=True, tc=(110, 60, 60))
    PX(s, [(5, 14), (6, 14), (7, 16), (8, 16), (5, 18), (6, 18), (23, 14), (24, 14), (25, 16), (26, 16), (23, 18), (24, 18),
           (9, 15), (10, 16), (22, 15), (21, 16), (11, 25), (12, 25), (19, 26), (20, 26), (5, 25), (7, 27), (9, 26)], DARK)


@reg('wererat')
def _(s, r):
    f = (150, 146, 110)
    s.line([(13, 24), (8, 27), (4, 26), (2, 22), (3, 18)], (226, 150, 150))
    fig(s, size='small', head='rat', skin=f, eye=REDEYE, lit=(REDEYE,), torso='vest', tc=(100, 70, 50), tc2=DARK,
        belly=None, legs='pants', lc=(80, 70, 60), boots=None, rh=('dagger',), geo=dict(tw=4, arm=(17, 21)))


@reg('asterion_minotaur')
def _(s, r):
    fur, chest, cloth = (120, 74, 44), (170, 118, 76), (160, 40, 36)
    eye = s.lit((255, 90, 40))
    s.rect(10, 22, 14, 28, fur); s.rect(17, 22, 21, 28, fur)
    s.rect(10, 28, 14, 29, DARK); s.rect(17, 28, 21, 29, DARK)
    s.poly([(7, 11), (24, 11), (21, 21), (10, 21)], fur)
    s.ell(11, 12, 20, 19, chest); s.line([(15, 13), (15, 19)], fur)
    s.poly([(11, 20), (20, 20), (18, 26), (13, 26)], cloth); s.line([(11, 20), (20, 20)], GOLD)
    s.rect(3, 12, 7, 21, fur); s.rect(24, 12, 28, 21, fur)
    s.rect(3, 17, 7, 18, IRON); s.rect(24, 17, 28, 18, IRON)
    s.poly([(11, 6), (6, 5), (3, 1), (7, 3), (12, 4)], IVORY)
    s.poly([(20, 6), (25, 5), (28, 1), (24, 3), (19, 4)], IVORY)
    s.ell(11, 3, 20, 12, fur); s.ell(12, 8, 19, 14, chest)
    s.px([(13, 7), (18, 7)], eye); s.line([(12, 6), (14, 6)], DARK); s.line([(17, 6), (19, 6)], DARK)
    s.px([(14, 11), (17, 11)], DARK); s.px([(15, 13), (16, 13)], GOLD)
    # the starry one: a scatter of stars on the brow and shoulders
    PX(s, [(15, 4), (9, 13), (22, 14)], s.lit((255, 240, 170)))


@reg('minotaur')
def _(s, r):
    f = (150, 112, 92)
    fig(s, size='large', head='bull', skin=f, horns=(90, 84, 90), eye=REDEYE, lit=(REDEYE,), torso='bare',
        belly=(190, 150, 124), tc=(100, 70, 50), tc2=DARK, legs='bare', boots=DARK, lh=('claws', DARK), rh=('claws', DARK),
        geo=dict(head=(11, 5, 20, 13), sh=13))


@reg('minotaur_warrior')
def _(s, r):
    f = (140, 84, 54)
    fig(s, size='large', head='bull', skin=f, horns=BRONZE, eye=YEL, lit=(YEL,), torso='bare', belly=(180, 124, 84),
        tc=(60, 80, 140), tc2=GOLD, legs='bare', boots=DARK, rh=('greataxe', STEEL, WOOD), pauldron=BRONZE,
        geo=dict(head=(11, 5, 20, 13), sh=13))


@reg('kusarikku')
def _(s, r):
    g = fig(s, size='large', skin=TAN, hair='long', hairc=BLACK, beard='long', beardc=BLACK, torso='bare',
            tc=(150, 110, 60), tc2=GOLD, legs='goat', lc=(120, 84, 54), tail=(120, 84, 54), eye=DARK, brow=True,
            geo=dict(head=(11, 5, 20, 13), sh=13))
    s.poly([(11, 7), (7, 6), (5, 2), (9, 4), (12, 5)], IVORY); s.poly([(20, 7), (24, 6), (26, 2), (22, 4), (19, 5)], IVORY)
    s.rect(11, 6, 20, 7, GOLD); s.rect(5, 16, 8, 16, GOLD); s.rect(23, 16, 26, 16, GOLD)
    PX(s, [(14, 15), (17, 15), (15, 17), (16, 17)], (80, 76, 90))


# =================================================================== trolls
def troll(s, skin, belly, hairc, eye, big=False):
    eye = s.lit(eye)
    head = (min(255, skin[0] + 10), min(255, skin[1] + 10), min(255, skin[2] + 8))
    arm = (max(0, skin[0] - 10), max(0, skin[1] - 10), max(0, skin[2] - 6))
    s.rect(10, 22, 14, 28, arm); s.rect(17, 22, 21, 28, arm)
    s.rect(8, 28, 14, 29, arm); s.rect(17, 28, 23, 29, arm)
    PX(s, [(8, 29), (10, 29), (21, 29), (23, 29)], IVORY)
    s.ell(6, 8 if not big else 6, 25, 24, skin)
    s.ell(11, 15, 20, 23, belly)
    s.rect(3, 12, 7, 24, arm); s.rect(24, 12, 28, 24, arm)
    s.ell(2, 22, 8, 27, arm); s.ell(23, 22, 29, 27, arm)
    PX(s, [(2, 28), (4, 28), (6, 28), (25, 28), (27, 28), (29, 28)], IVORY)
    s.poly([(10, 9), (5, 5), (9, 12)], head); s.poly([(21, 9), (26, 5), (22, 12)], head)
    s.ell(10, 5, 21, 15, head)
    s.rect(15, 9, 16, 15, dk(skin)); PX(s, [(14, 15), (17, 15)], dk(skin))
    s.line([(12, 8), (14, 8)], DARK); s.line([(17, 8), (19, 8)], DARK); PX(s, [(13, 9), (18, 9)], eye)
    PX(s, [(12, 13), (12, 12), (19, 13), (19, 12)], IVORY)
    if hairc:
        PX(s, [(14, 5), (15, 4), (16, 5), (17, 4), (15, 3), (16, 4), (13, 5), (18, 5), (16, 3), (15, 5), (17, 5)], hairc)


@reg('troll')
def _(s, r):
    troll(s, (104, 160, 104), (160, 196, 130), (50, 80, 50), YEL)
    PX(s, [(8, 13), (22, 17), (9, 19), (12, 11)], (70, 120, 76))


@reg('cave_troll')
def _(s, r):
    troll(s, (124, 134, 110), (160, 164, 140), None, (255, 150, 60))
    s.ell(22, 1, 30, 9, (140, 136, 130)); PX(s, [(25, 4), (27, 6)], (100, 96, 96))
    s.rect(24, 8, 28, 14, (114, 124, 104));
    PX(s, [(9, 11), (10, 12), (20, 18), (7, 15), (13, 17)], (90, 96, 84))


@reg('ice_troll')
def _(s, r):
    troll(s, (130, 184, 224), (206, 230, 246), WHITE, (40, 120, 255))
    ice = s.lit(ICE)
    for x, y in ((7, 10), (24, 10)):
        s.poly([(x - 1, y + 2), (x, y - 3), (x + 1, y + 2)], ice)
    PX(s, [(2, 28), (4, 28), (6, 28), (25, 28), (27, 28), (29, 28)], ice)


@reg('troll_brute')
def _(s, r):
    sk = (64, 124, 96)
    troll(s, sk, (136, 176, 130), None, REDEYE, big=True)
    s.ell(1, 19, 9, 28, (54, 110, 84)); s.ell(22, 19, 30, 28, (54, 110, 84))
    PX(s, [(2, 28), (4, 29), (7, 29), (24, 29), (27, 29), (29, 28)], IVORY)
    s.rect(11, 13, 20, 15, (84, 146, 112)); s.rect(12, 11, 12, 13, IVORY); s.rect(19, 11, 19, 13, IVORY)
    s.line([(8, 12), (22, 22)], LEATHER, 2); s.rect(10, 22, 21, 23, LEATHER); PX(s, [(15, 22), (16, 22)], IRON)


@reg('war_troll')
def _(s, r):
    troll(s, (84, 170, 70), (150, 200, 110), None, YEL)
    s.ell(4, 8, 11, 14, IRON); s.ell(20, 8, 27, 14, IRON); PX(s, [(7, 7), (23, 7)], STEEL)
    s.poly([(10, 4), (21, 4), (20, 7), (11, 7)], IRON); s.rect(15, 5, 16, 9, IRON)
    s.rect(11, 16, 20, 22, IRON); s.line([(11, 19), (20, 19)], STEEL)
    s.rect(26, 6, 27, 23, WOOD); s.rect(25, 2, 28, 10, (110, 80, 50)); PX(s, [(25, 3), (28, 5), (25, 7), (28, 9), (26, 1)], STEEL)


@reg('chaos_troll')
def _(s, r):
    sk = (124, 180, 84)
    troll(s, sk, (180, 210, 120), (150, 60, 160), s.lit((255, 90, 230)))
    # heals wrong: a second head, a third arm
    s.ell(19, 2, 26, 9, (150, 196, 100)); PX(s, [(21, 5), (24, 5)], s.lit((255, 90, 230))); s.line([(21, 7), (24, 7)], DARK)
    s.rect(1, 6, 4, 13, (104, 160, 74)); s.ell(1, 3, 6, 8, (104, 160, 74)); PX(s, [(1, 3), (3, 2), (5, 3)], IVORY)
    PX(s, [(9, 12), (12, 18), (19, 17), (23, 13), (7, 20)], (200, 80, 200))


# =================================================================== giants
def giant(s, **k):
    d = dict(size='giant', legs='bare', boots=(110, 80, 56), torso='fur', tc=(130, 95, 60), tc2=(96, 66, 44))
    d.update(k)
    return fig(s, **d)


@reg('hill_giant')
def _(s, r):
    giant(s, skin=(220, 176, 128), hair='wild', hairc=(84, 54, 34), mouth=True, rh=('greatclub',), brow=True, tc=(120, 100, 84),
          tc2=(84, 70, 60), sleeve=(206, 162, 116))


@reg('stone_giant')
def _(s, r):
    sk = (146, 146, 152)
    g = giant(s, skin=sk, torso='bare', tc=(84, 84, 96), tc2=DARK, boots=None,
              rh=('boulder', (112, 104, 98)), eye=DARK, brow=True, geo=dict(head=(12, 1, 19, 9)))
    PX(s, [(9, 12), (10, 13), (10, 14), (21, 16), (20, 17), (13, 24), (19, 26), (5, 15)], (100, 100, 110))


@reg('frost_giant')
def _(s, r):
    ice = s.lit(ICE)
    giant(s, skin=(150, 200, 236), hair='long', hairc=WHITE, beard='long', beardc=WHITE, hat='horned', hatc=IRON,
          tc=(206, 206, 214), tc2=(150, 150, 164), rh=('greatclub', ice, (150, 210, 240)), geo=dict(head=(12, 3, 19, 10), sh=10))


@reg('frost_giant_jarl')
def _(s, r):
    ice = s.lit(ICE)
    giant(s, skin=(124, 164, 224), beard='huge', beardc=WHITE, hat='horned', hatc=GOLD, hat2=IVORY, torso='armor',
          tc=(90, 110, 150), tc2=GOLD, cloak=(226, 226, 232), rh=('greataxe', ice, IRON), pauldron=(226, 226, 232),
          geo=dict(head=(12, 3, 19, 10), sh=10))


@reg('frostfang_giant')
def _(s, r):
    ice = s.lit(ICE)
    g = giant(s, skin=(116, 150, 204), hair='wild', hairc=WHITE, torso='bare', tc=(226, 226, 232), tc2=(150, 150, 164),
              boots=(226, 226, 232), rh=('maul', ice, IRON), eye=s.lit((120, 200, 255)), brow=True,
              geo=dict(head=(12, 3, 19, 10), sh=10))
    s.rect(14, 9, 14, 12, IVORY); s.rect(17, 9, 17, 12, IVORY)


@reg('fire_giant')
def _(s, r):
    f = s.lit(FIRE); h = s.lit(HOT)
    g = giant(s, skin=(84, 54, 52), hair='wild', hairc=f, beard='long', beardc=f, torso='armor', tc=(60, 56, 66),
              tc2=(200, 110, 40), legs='pants', lc=(50, 44, 52), boots=(60, 56, 66), rh=('sword', f, 14, IRON),
              eye=h, pauldron=(60, 56, 66), geo=dict(head=(12, 3, 19, 10), sh=10))
    PX(s, [(15, 11), (16, 12), (29, 5), (27, 3)], h)


@reg('fire_giant_king')
def _(s, r):
    f = s.lit(FIRE); h = s.lit(HOT)
    g = giant(s, skin=(100, 60, 50), beard='huge', beardc=f, hat='crown', hatc=GOLD, hat2=(255, 80, 40),
              torso='armor', tc=(96, 60, 40), tc2=GOLD, legs='pants', lc=(60, 44, 44), boots=(96, 60, 40),
              cloak=(170, 40, 30), rh=('maul', f, IRON), eye=h, pauldron=GOLD, geo=dict(head=(12, 4, 19, 11), sh=11))
    PX(s, [(15, 14), (16, 16), (15, 17), (26, 9), (28, 10), (27, 11)], h)


@reg('cloud_giant')
def _(s, r):
    g = giant(s, skin=(170, 190, 240), hair='long', hairc=WHITE, hat='circlet', hatc=GOLD, hat2=(120, 200, 255),
              torso='toga', tc=(104, 136, 210), tc2=(70, 100, 176), boots=GOLD, rh=('morningstar', (200, 204, 220), GOLD),
              brow=True)
    for x in (2, 9, 16, 23):
        s.ell(x, 27, x + 6, 30, (236, 238, 250))
    s.shadow = False


@reg('storm_giant')
def _(s, r):
    bolt = s.lit((255, 250, 150))
    g = giant(s, skin=(96, 104, 204), hair='long', hairc=WHITE, beard='short', beardc=WHITE, torso='skirt',
              tc=BRONZE, tc2=GOLD, boots=BRONZE, rh=('sword', (190, 200, 240), 15), sleeve=(86, 94, 190),
              eye=bolt, pauldron=BRONZE)
    s.line([(29, 6), (28, 10), (29, 12), (28, 16)], bolt)
    s.line([(3, 3), (5, 6), (3, 7), (5, 10)], bolt)


@reg('elder_storm_giant')
def _(s, r):
    bolt = s.lit((255, 250, 150))
    g = giant(s, skin=(112, 126, 216), hair='long', hairc=WHITE, beard='huge', beardc=WHITE, hat='crown',
              hatc=GOLD, hat2=CYAN, torso='toga', tc=(96, 70, 160), tc2=GOLD, boots=GOLD, rh=('hammer', (200, 210, 240), GOLD),
              eye=bolt, geo=dict(head=(12, 4, 19, 11), sh=11))
    s.line([(22, 3), (24, 6), (22, 7), (25, 11)], bolt); s.line([(4, 2), (6, 5), (4, 6), (6, 9)], bolt)


@reg('titan')
def _(s, r):
    sk = (220, 206, 166)
    g = giant(s, skin=sk, hair='curly', hairc=(150, 104, 44), beard='short', beardc=(150, 104, 44), hat='laurel', hatc=(96, 160, 70),
              torso='bare', tc=WHITE, tc2=GOLD, boots=GOLD, eye=DARK, brow=True,
              geo=dict(head=(12, 2, 19, 9), tw=10, bw=8, aw=4))
    for x0, x1 in ((2, 5), (26, 29)):
        s.rect(x0, 17, x1, 18, IRON)
    PX(s, [(3, 21), (3, 23), (4, 25), (28, 21), (28, 23), (27, 25)], STEEL)
    s.poly([(10, 21), (21, 21), (22, 25), (9, 25)], WHITE); s.line([(10, 21), (21, 21)], GOLD)


@reg('titanspawn')
def _(s, r):
    sk = (124, 104, 204)
    cr = s.lit((255, 120, 240))
    g = fig(s, size='large', skin=sk, torso='bare', tc=(70, 60, 110), tc2=DARK, legs='bare', boots=None, eye=cr,
            geo=dict(arm=(13, 22)))
    s.ell(3, 19, 10, 26, (110, 92, 186)); s.ell(21, 19, 28, 26, (110, 92, 186))
    s.line([(12, 14), (14, 17), (13, 20)], cr); s.line([(19, 13), (18, 16), (20, 19)], cr)
    PX(s, [(6, 15), (7, 17), (25, 16), (24, 22), (6, 23), (12, 26), (19, 27), (14, 5), (17, 5)], cr)
    PX(s, [(13, 4), (18, 4), (12, 5), (19, 5)], (90, 76, 160))


@reg('cyclops')
def _(s, r):
    giant(s, head='cyclops', skin=(196, 146, 100), hair='short', hairc=(70, 50, 40), tc=(232, 226, 206),
          tc2=(180, 170, 150), rh=('boulder',), lh=('staff', None, 'crook'), eye=(60, 110, 170))


@reg('cyclops_brute')
def _(s, r):
    g = giant(s, head='cyclops', skin=(170, 126, 92), torso='bare', tc=(96, 70, 50), tc2=DARK, arms=('up', 'up'),
              eye=(150, 50, 40), boots=None, geo=dict(head=(12, 4, 19, 11), sh=11))
    s.poly([(15, 4), (16, 1), (17, 4)], IVORY)
    s.ell(2, 1, 8, 7, (160, 116, 84)); s.ell(23, 1, 29, 7, (160, 116, 84))


@reg('ettin')
def _(s, r):
    giant(s, heads=2, skin=(156, 144, 132), hair='wild', hairc=(60, 50, 50), head2=dict(hair='short', hairc=(150, 80, 40), beard='short'),
          rh=('club',), lh=('club',), mouth=True, brow=True, geo=dict(head=(12, 3, 19, 10), sh=10))


@reg('ettin_warchief')
def _(s, r):
    giant(s, heads=2, skin=(170, 120, 90), hat='horned', hatc=IRON, head2=dict(hat='spike', hatc=IRON, hat2=(200, 50, 40), beard='short', hairc=DARK),
          torso='armor', tc=(110, 100, 96), tc2=GOLD, rh=('maul',), lh=('mace', IRON, IRON), brow=True, cloak=(120, 40, 40),
          pauldron=IRON, geo=dict(head=(12, 3, 19, 10), sh=10))


def fatso(s, **k):
    d = dict(geo=dict(tw=9, bw=10, waist=22, lw=5, head=(12, 2, 19, 9)), torso='bare', tc=(110, 80, 56), tc2=DARK, boots=None)
    d.update(k)
    g = giant(s, **d)
    sk = d['skin']
    s.ell(8, 12, 23, 23, lt(sk)); PX(s, [(15, 19), (16, 19)], dk(sk, 2))
    s.rect(9, 22, 22, 24, d['tc']); s.line([(9, 22), (22, 22)], d['tc2'])
    return g


@reg('ogre')
def _(s, r):
    fatso(s, head='orc', skin=(196, 164, 96), eye=DARK, hair='topknot', hairc=DARK, rh=('greatclub', WOOD, IRON))


@reg('two_headed_ogre')
def _(s, r):
    fatso(s, head='orc', heads=2, skin=(176, 112, 70), eye=DARK, head2=dict(hair='tuft', hairc=DARK), rh=('club',), lh=('club',),
          geo=dict(tw=9, bw=10, waist=22, lw=5, head=(12, 3, 19, 10), sh=10))


@reg('fomorian')
def _(s, r):
    sk = (96, 118, 72)
    evil = s.lit((255, 70, 200))
    g = giant(s, head='cyclops', skin=sk, eye=evil, hair='tuft', hairc=(50, 60, 44), tc=(90, 70, 80), tc2=(60, 44, 56),
              geo=dict(head=(10, 3, 19, 11), sh=11))
    s.ell(12, 5, 17, 9, evil); s.rect(14, 6, 15, 8, DARK)
    s.ell(22, 12, 30, 24, (86, 106, 64)); s.ell(23, 21, 30, 28, (86, 106, 64))
    s.poly([(17, 3), (21, 1), (19, 5)], IVORY)
    PX(s, [(8, 13), (10, 16), (24, 15), (27, 18), (12, 23)], (130, 150, 90))


@reg('cacus')
def _(s, r):
    f = s.lit(FIRE); h = s.lit(HOT)
    sk = (186, 96, 60)
    g = giant(s, skin=sk, hair='wild', hairc=(50, 36, 36), beard='short', beardc=(50, 36, 36), tc=(90, 60, 44),
              tc2=(60, 40, 30), lh=('greatclub', (96, 66, 44)), eye=h, brow=True)
    s.poly([(17, 8), (23, 7), (30, 9), (30, 16), (24, 13), (18, 10)], f)
    s.poly([(19, 9), (25, 9), (29, 12), (23, 11)], h)
    PX(s, [(28, 6), (30, 18), (26, 16)], f)


@reg('green_knight')
def _(s, r):
    gs = (156, 218, 140)
    dkg = (28, 96, 48)
    g = fig(s, size='giant', skin=gs, hair='long', hairc=dkg, beard='long', beardc=dkg,
            torso='armor', tc=(64, 156, 84), tc2=GOLD, legs='greaves', lc=(40, 110, 60), boots=(64, 156, 84),
            rh=('greataxe', (176, 236, 176), (90, 64, 40)), cloak=(22, 70, 40), pauldron=GOLD,
            eye=s.lit((255, 60, 50)), sleeve=(50, 130, 70), hands=gs, geo=dict(head=(12, 3, 19, 10), sh=10))
    s.rect(9, 19, 22, 19, GOLD)
    s.line([(4, 20), (3, 14), (5, 10)], (30, 90, 40)); PX(s, [(2, 13), (4, 12), (6, 11), (2, 16), (5, 15), (4, 9)], (60, 150, 60))
    PX(s, [(3, 11), (5, 13), (2, 15)], s.lit((255, 60, 60)))


@reg('iron_patriarch')
def _(s, r):
    ir = (112, 112, 128)
    eye = s.lit((255, 170, 60))
    g = fig(s, size='giant', skin=PALE, hat='fullhelm', hatc=ir, eye=eye, torso='armor', tc=ir, tc2=(190, 160, 76),
            legs='pants', lc=(80, 80, 96), boots=ir, cloak=(110, 30, 36), rh=('maul', (150, 150, 166), (80, 60, 50)),
            pauldron=(150, 150, 166), sleeve=(96, 96, 112), hands=(150, 150, 166),
            geo=dict(head=(12, 3, 19, 10), sh=10))
    s.rect(12, 2, 19, 3, (190, 160, 76))
    for x in (12, 14, 17, 19):
        s.rect(x, 1, x, 2, (190, 160, 76))
    s.poly([(13, 10), (18, 10), (17, 16), (16, 18), (15, 18), (14, 16)], WHITE)
    s.rect(9, 19, 22, 19, (190, 160, 76))


@reg('surtur')
def _(s, r):
    rock = (70, 46, 44)
    lava = s.lit((255, 130, 30)); hot = s.lit((255, 226, 90))
    s.rect(10, 21, 14, 29, rock); s.rect(17, 21, 21, 29, rock)
    s.poly([(8, 10), (23, 10), (21, 21), (10, 21)], rock)
    s.rect(5, 11, 8, 20, rock); s.rect(23, 11, 26, 20, rock)
    s.line([(10, 20), (21, 20)], GOLD)
    s.line([(12, 12), (14, 15), (13, 18)], lava); s.line([(19, 12), (17, 16), (18, 18)], lava)
    s.px([(12, 23), (12, 25), (19, 24), (19, 26), (6, 14), (25, 16)], lava)
    s.ell(12, 3, 19, 10, rock); s.px([(14, 6), (17, 6)], hot); s.line([(14, 9), (17, 9)], lava)
    s.poly([(11, 4), (12, 1), (14, 2), (15, 1), (17, 2), (19, 1), (20, 4), (18, 3), (13, 3)], lava)
    s.px([(13, 2), (15, 2), (18, 2), (16, 3)], hot)
    s.rect(27, 19, 28, 21, DARK); s.line([(25, 18), (30, 18)], GOLD)
    s.rect(27, 3, 28, 17, lava); s.line([(27, 5), (27, 16)], hot)
    s.px([(28, 2), (27, 1), (29, 6), (26, 9), (29, 12)], lava)


# =================================================================== bandits, soldiers, killers
@reg('bandit_thug')
def _(s, r):
    skin, hood, jerkin, mask = (214, 168, 128), (96, 52, 44), (92, 86, 80), (150, 40, 40)
    s.rect(12, 22, 14, 28, DARK); s.rect(17, 22, 19, 28, DARK)
    s.rect(11, 28, 14, 29, LEATHER); s.rect(17, 28, 20, 29, LEATHER)
    s.poly([(10, 13), (21, 13), (20, 23), (11, 23)], jerkin)
    s.line([(11, 20), (20, 20)], LEATHER); s.px([(15, 20), (16, 20)], GOLD)
    s.rect(7, 14, 10, 21, hood); s.rect(21, 14, 24, 20, hood)
    s.rect(8, 21, 10, 22, skin); s.rect(22, 20, 24, 21, skin)
    s.ell(11, 4, 20, 13, hood)
    s.rect(13, 7, 18, 12, skin); s.rect(13, 10, 18, 12, mask)
    s.px([(14, 8), (17, 8)], DARK)
    s.poly([(11, 12), (20, 12), (22, 15), (9, 15)], hood)
    s.line([(23, 21), (26, 11)], WOOD, 2)
    s.rect(24, 6, 28, 11, WOOD); s.px([(25, 7), (27, 9), (26, 10)], IRON)


@reg('bandit_archer')
def _(s, r):
    g = fig(s, hat='hood', hatc=(96, 116, 70), tc=(124, 104, 70), sleeve=(96, 116, 70), lh=('bow',), lc=(70, 60, 50))
    s.rect(21, 9, 22, 14, LEATHER); PX(s, [(21, 8), (22, 7), (23, 8)], (230, 230, 220))


@reg('bandit_captain')
def _(s, r):
    g = fig(s, hair='short', hairc=DARK, beard='goatee', beardc=DARK, hat='tricorn', hatc=(70, 50, 44), hat2=GOLD,
            torso='armor', tc=(160, 120, 64), tc2=(110, 76, 40), sleeve=(120, 40, 40), rh=('sword',), lh=('dagger',),
            lc=(60, 50, 50), cloak=(120, 40, 40), brow=True)
    s.line([(11, 21), (20, 21)], (190, 50, 50))
    PX(s, [(19, 2), (20, 1), (21, 1)], (230, 60, 50))


@reg('bandit_kingpin')
def _(s, r):
    g = fig(s, hair='long', hairc=DARK, beard='bigstache', beardc=DARK, hat='tricorn', hatc=(50, 40, 50), hat2=GOLD,
            torso='suit', tc=(186, 150, 56), tc2=(170, 40, 40), rh=('saber',), lh=('pistol',), lc=(60, 40, 44),
            boots=DARK, cloak=(110, 30, 40))
    s.line([(11, 21), (20, 21)], (170, 40, 40)); PX(s, [(12, 16), (12, 18), (19, 16), (19, 18)], GOLD)
    PX(s, [(18, 1), (19, 1), (20, 2)], WHITE)


@reg('bandit_thief')
def _(s, r):
    fig(s, hat='hood', hatc=(74, 76, 120), mask=(50, 50, 70), tc=(84, 84, 110), tc2=DARK, lc=(50, 50, 64),
        rh=('dagger',), lh=('sack', (150, 128, 90)), geo=dict(tw=5, bw=4))


@reg('brigand')
def _(s, r):
    fig(s, hat='kettle', hatc=IRON, beard='stubble', tc=(150, 110, 64), tc2=DARK, lc=(80, 60, 50), rh=('dagger',),
        lh=('shield', (120, 84, 50), IRON, 'round'), hair='short', hairc=BROWN, mask=None)


@reg('mercenary_veteran')
def _(s, r):
    g = fig(s, hair='short', hairc=GREY, beard='short', beardc=GREY, torso='armor', tc=(170, 150, 100),
            tc2=(120, 100, 70), rh=('sword',), lh=('shield', (110, 100, 96), STEEL, 'round'), lc=(70, 60, 56),
            pauldron=IRON, skin=TAN)
    s.line([(13, 6), (15, 10)], (150, 80, 70))


@reg('veteran_knight')
def _(s, r):
    st = (176, 180, 200)
    fig(s, hat='plume', hatc=st, crest=(200, 50, 50), torso='tabard', tc=st, tc2=(60, 90, 170), legs='greaves',
        lc=(110, 114, 134), boots=st, rh=('sword', (220, 224, 236), 13), lh=('shield', (60, 90, 170), GOLD, 'kite'),
        pauldron=st, sleeve=(150, 154, 176), hands=st, geo=dict(head=(11, 5, 20, 13)))


@reg('mage_slayer_assassin')
def _(s, r):
    g = fig(s, hat='hood', hatc=(96, 90, 110), mask=(60, 56, 70), tc=(84, 76, 96), tc2=(200, 200, 210),
            lc=(60, 54, 70), boots=DARK, rh=('sword', (226, 230, 240), 10, (200, 200, 210)), lh=('dagger', (226, 230, 240)),
            cloak=(70, 64, 84), eye=(90, 200, 220))
    c = s.lit(CYAN)
    PX(s, [(15, 16), (16, 16), (14, 17), (17, 17), (15, 18), (16, 18)], c)


@reg('shadow_assassin')
def _(s, r):
    v = s.lit((255, 90, 120))
    bl = s.lit((236, 214, 255))
    g = fig(s, hat='cowl', hatc=(50, 40, 72), void=True, eye=v, tc=(40, 32, 58), tc2=(196, 44, 66), lc=(34, 28, 50),
            boots=(34, 28, 50), rh=('sword', bl, 7, DARK), lh=('sword', bl, 7, DARK), cloak=(30, 24, 46),
            hands=(40, 32, 58), geo=dict(tw=5, bw=4))
    PX(s, [(7, 28), (9, 29), (22, 29), (24, 28), (6, 26), (25, 26)], (30, 24, 46))
    PX(s, [(19, 22), (20, 23), (20, 24)], (196, 44, 66))


@reg('shadow_archer')
def _(s, r):
    v = s.lit((150, 170, 255))
    g = fig(s, hat='hood', hatc=(50, 52, 90), void=True, eye=v, tc=(44, 44, 76), tc2=(90, 96, 150), lc=(36, 36, 60),
            boots=(36, 36, 60), lh=('bow', (30, 30, 50), v), hands=(44, 44, 76), cloak=(36, 36, 64))
    s.line([(6, 20), (12, 20)], v)
    s.rect(21, 9, 22, 14, (30, 30, 50)); PX(s, [(21, 8), (22, 7), (23, 8)], v)


@reg('snake_charmer')
def _(s, r):
    g = fig(s, skin=TAN, hat='turban', hatc=(236, 232, 220), hat2=(230, 60, 60), beard='goatee', beardc=DARK,
            torso='vest', tc=(190, 150, 60), tc2=(200, 60, 60), lc=(120, 70, 150), boots=(190, 150, 60),
            arms=('down', 'fwd'), geo=dict(tw=5, bw=5))
    s.rect(15, 14, 15, 20, (150, 110, 60)); s.ell(14, 20, 17, 23, (190, 150, 60))
    s.rect(1, 23, 8, 28, (170, 130, 70)); s.line([(1, 25), (8, 25)], (120, 86, 44)); s.line([(1, 23), (8, 23)], (120, 86, 44))
    cb = (80, 150, 70)
    s.rect(4, 14, 5, 22, cb); s.ell(2, 10, 7, 15, cb); PX(s, [(3, 12), (6, 12)], s.lit((255, 220, 60))); PX(s, [(4, 16), (5, 18), (4, 20)], (220, 210, 120))


@reg('tengu_warrior')
def _(s, r):
    fe = (50, 50, 74)
    g = fig(s, head='crow', skin=fe, eye=s.lit((255, 80, 60)), wings=(36, 36, 56), tc=(230, 226, 214), tc2=(190, 50, 50),
            lc=(60, 60, 96), boots=(214, 190, 140), rh=('katana',), hands=(226, 178, 62), sleeve=(230, 226, 214))
    s.rect(15, 3, 16, 4, (190, 50, 50))
    s.line([(11, 21), (20, 21)], (190, 50, 50))


@reg('mind_flayer_thrall')
def _(s, r):
    sk = (178, 164, 198)
    v = s.lit((255, 80, 220))
    g = fig(s, skin=sk, eye=v, tc=(100, 62, 160), tc2=(214, 200, 150), lc=(84, 80, 96), boots=None,
            arms=('down', 'fwd'), brow=True)
    s.line([(14, 11), (17, 11)], DARK)
    PX(s, [(13, 5), (15, 4), (17, 5), (19, 6)], DARK); PX(s, [(15, 6), (16, 6)], v)
    PX(s, [(11, 24), (14, 25), (17, 24), (20, 25)], (100, 62, 160))
    PX(s, [(9, 17), (10, 19), (22, 16)], (70, 44, 110))


# =================================================================== cult, casters, witches
@reg('cult_priest')
def _(s, r):
    robe, trim = (96, 46, 130), GOLD
    orb = s.lit((250, 110, 240))
    void = (26, 16, 34)
    s.poly([(11, 12), (20, 12), (23, 29), (8, 29)], robe)
    s.line([(15, 13), (15, 28)], trim); s.line([(16, 13), (16, 28)], trim)
    s.line([(9, 28), (22, 28)], trim)
    s.poly([(10, 14), (6, 22), (9, 23), (12, 16)], robe)
    s.poly([(21, 14), (25, 19), (23, 21), (19, 16)], robe)
    s.ell(11, 3, 20, 13, robe); s.poly([(11, 9), (15, 2), (16, 2), (20, 9)], robe)
    s.rect(13, 7, 18, 12, void); s.px([(14, 9), (17, 9)], orb)
    s.line([(25, 7), (25, 29)], WOOD)
    s.ell(23, 2, 27, 6, orb); s.px([(24, 3)], s.lit((255, 230, 255)))


@reg('cult_initiate')
def _(s, r):
    g = fig(s, hair='short', hairc=BROWN, torso='robe', tc=(150, 112, 184), tc2=(110, 80, 140), trim=False,
            rh=('dagger',), mouth=True, boots=LEATHER)
    s.line([(10, 21), (21, 21)], (214, 200, 150)); PX(s, [(13, 22), (13, 23), (13, 24)], (214, 200, 150))
    s.poly([(10, 13), (21, 13), (19, 15), (12, 15)], (110, 80, 140))


@reg('dark_cultist')
def _(s, r):
    e = s.lit((255, 70, 70))
    sh_ = s.lit((190, 90, 255))
    g = fig(s, hat='cowl', hatc=(76, 44, 120), void=True, eye=e, torso='robe', tc=(76, 44, 120), tc2=(40, 24, 64),
            rh=('dagger', sh_, DARK), lh=('torch', (255, 200, 90)), hands=PALE)


@reg('cult_zealot')
def _(s, r):
    g = fig(s, size='large', hat='hood', hatc=(176, 36, 56), void=True, eye=WHITE, torso='robe', tc=(176, 36, 56),
            tc2=(90, 20, 36), sleeve=SKIN, rh=('cleaver', STEEL, DARK), geo=dict(tw=6, aw=3))
    PX(s, [(7, 15), (8, 17), (7, 19), (23, 15), (24, 17)], (176, 36, 56))


@reg('cult_hierophant')
def _(s, r):
    v = s.lit((200, 110, 255))
    g = fig(s, size='robed', hat='mitre', hatc=(66, 36, 110), hat2=GOLD, beard='long', beardc=WHITE, skin=PALE,
            torso='robe', tc=(66, 36, 110), tc2=GOLD, rh=('dagger', (40, 36, 50), GOLD), lh=('orb', (200, 110, 255)),
            arms=('up', 'down'), eye=v)


@reg('veiled_inquisitor')
def _(s, r):
    red = (176, 34, 52)
    g = fig(s, size='robed', hat='hood', hatc=red, skin=(210, 204, 212), eye=DARK, torso='robe', tc=red,
            tc2=GOLD, rh=('whip', (60, 44, 44)), lh=('censer', GOLD, FIRE), hands=(60, 44, 44))
    s.rect(8, 8, 23, 9, (120, 22, 40)); s.rect(12, 5, 19, 7, (150, 28, 46)); s.line([(12, 7), (19, 7)], GOLD)
    s.line([(13, 14), (18, 14)], (176, 170, 180)); s.line([(13, 12), (18, 12)], (190, 184, 194))


@reg('necromancer_apprentice')
def _(s, r):
    fig(s, size='robed', skin=PALE, hair='short', hairc=BLACK, torso='robe', tc=(60, 48, 76), tc2=(124, 84, 184),
        rh=('staff', GRN, 'skull'), lh=('book', (110, 60, 150)), arms=('fwd', 'down'))


@reg('battle_mage')
def _(s, r):
    c = s.lit(CYAN)
    g = fig(s, hair='short', hairc=BLOND, torso='tunic', tc=(70, 146, 214), tc2=GOLD, sleeve=SKIN, lc=(50, 70, 110),
            arms=('up', 'up'), rh=('flame',), lh=('orb', ICE), brow=True)
    PX(s, [(8, 12), (7, 14), (8, 15), (23, 12), (24, 14), (23, 15), (12, 6), (19, 6)], c)


@reg('harrow_witch')
def _(s, r):
    v = s.lit((220, 110, 255))
    fig(s, size='robed', head='hag', skin=(190, 200, 170), eye=v, hair='long', hairc=GREY, hat='wizard',
        hatc=(70, 36, 90), hat2=(150, 80, 170), torso='robe', tc=(96, 44, 116), tc2=(60, 28, 76),
        rh=('staff', (220, 110, 255), 'orb', (70, 56, 50)), lh=('claws', (190, 200, 170)))


@reg('plague_witch')
def _(s, r):
    m = s.lit((170, 240, 90))
    g = fig(s, size='robed', skin=(200, 204, 150), hat='hood', hatc=(110, 124, 60), void=True, eye=m, torso='robe',
            tc=(124, 140, 64), tc2=(80, 90, 44), rh=('censer', IRON, (170, 240, 90), (170, 220, 110)),
            lh=('staff', None, 'knob', (80, 70, 56)), hands=(200, 204, 150))
    s.poly([(14, 11), (17, 11), (16, 16), (15, 16)], BONE)
    PX(s, [(5, 10), (7, 7), (26, 12), (27, 8), (4, 16)], m)
    PX(s, [(10, 26), (13, 27), (18, 26), (21, 27)], (80, 90, 44))


def hag(s, **k):
    d = dict(size='robed', head='hag', torso='robe', trim=False, hair='wild', lh=('claws',), rh=('claws',))
    d.update(k)
    return fig(s, **d)


@reg('annis_hag')
def _(s, r):
    sk = (96, 120, 196)
    g = hag(s, size='large', skin=sk, eye=YEL, lit=(YEL,), hairc=(40, 36, 50), tc=(70, 56, 90), tc2=(50, 40, 64),
            hands=sk, arms=('down', 'up'), geo=dict(tw=6, aw=3, head=(11, 6, 20, 14), sh=14, arm=(15, 23)))
    for hx, hy in ((7, 24), (23, 7)):
        for dx in (-1, 0, 1):
            sgn = 1 if hy > 15 else -1
            s.rect(hx + dx * 2 - (0 if dx else 0), min(hy, hy + sgn * 4), hx + dx * 2, max(hy, hy + sgn * 4), IRON)
    PX(s, [(9, 28), (12, 28), (16, 29), (20, 28), (22, 29)], (50, 40, 64))


@reg('green_hag')
def _(s, r):
    sk = (96, 166, 96)
    g = hag(s, skin=sk, eye=YEL, lit=(YEL,), hair='long', hairc=(40, 96, 56), tc=(104, 104, 64), tc2=(70, 76, 44),
            teeth=(140, 220, 90), hands=sk)
    PX(s, [(10, 10), (21, 12), (10, 16), (21, 18), (12, 7), (18, 7)], (120, 200, 90))
    s.ell(2, 27, 9, 29, (60, 130, 70)); s.ell(22, 27, 29, 29, (60, 130, 70))


@reg('night_hag')
def _(s, r):
    sk = (100, 60, 136)
    e = s.lit((255, 60, 60))
    g = hag(s, skin=sk, eye=e, hairc=WHITE, tc=(44, 28, 60), tc2=(30, 18, 44), hands=sk, arms=('fwd', 'fwd'))
    s.poly([(12, 8), (10, 3), (14, 7)], (40, 30, 50)); s.poly([(19, 8), (21, 3), (17, 7)], (40, 30, 50))
    s.ell(14, 19, 17, 22, e); PX(s, [(15, 20)], s.lit((255, 200, 200)))
    PX(s, [(6, 24), (25, 23), (4, 20), (27, 19)], (120, 70, 160))


@reg('sea_hag')
def _(s, r):
    sk = (124, 176, 176)
    g = hag(s, skin=sk, eye=s.lit((255, 255, 200)), hair='long', hairc=(44, 110, 90), tc=(60, 100, 160),
            tc2=(40, 70, 120), hands=sk, rh=('trident', (190, 200, 180), (120, 110, 90)))
    s.ell(13, 10, 15, 12, s.lit((255, 255, 200))); PX(s, [(14, 11)], DARK)
    PX(s, [(12, 20), (14, 22), (16, 20), (18, 22), (13, 24), (17, 24), (15, 26)], (110, 150, 200))
    PX(s, [(10, 14), (21, 15), (10, 18)], (44, 110, 90)); PX(s, [(19, 27), (11, 27)], BONE)


@reg('baba_yaga')
def _(s, r):
    # the witch rides her mortar and rows it with the pestle
    stone = (128, 124, 124)
    sk = (190, 160, 120)
    e = s.lit((255, 150, 40))
    s.rect(24, 3, 25, 27, WOOD); s.ell(22, 24, 27, 29, (100, 70, 44)); s.ell(23, 1, 26, 5, WOOD)
    s.poly([(10, 14), (21, 14), (22, 22), (9, 22)], (110, 60, 60))
    s.rect(21, 15, 24, 17, (110, 60, 60)); s.rect(23, 15, 26, 17, sk)
    s.rect(6, 15, 9, 19, (110, 60, 60)); s.rect(5, 19, 8, 20, sk)
    s.poly([(6, 18), (25, 18), (23, 29), (8, 29)], stone); s.rect(5, 17, 26, 19, (156, 150, 148))
    PX(s, [(11, 23), (18, 25), (14, 27), (21, 22)], (96, 92, 96))
    s.poly([(10, 9), (11, 3), (16, 1), (21, 3), (22, 10), (20, 14), (11, 14)], (170, 50, 50))
    PX(s, [(12, 4), (16, 3), (20, 5), (11, 8), (21, 8)], (240, 220, 120))
    s.ell(12, 5, 20, 14, sk)
    PX(s, [(14, 8), (18, 8)], e); s.line([(13, 7), (15, 7)], DARK); s.line([(17, 7), (19, 7)], DARK)
    s.rect(16, 9, 16, 12, dk(sk)); PX(s, [(15, 12)], dk(sk))
    s.line([(14, 13), (18, 13)], IRON); PX(s, [(11, 6), (21, 6), (11, 10), (21, 10)], GREY)
    s.ell(1, 20, 5, 24, BONE); PX(s, [(2, 22), (4, 22)], e)
    s.shadow = False


# =================================================================== dark elves, elves, fey lords
DROW = (96, 88, 136)


@reg('dark_elf')
def _(s, r):
    g = fig(s, head='elf', skin=DROW, eye=s.lit((255, 120, 160)), hair='long', hairc=WHITE, tc=(60, 50, 80),
            tc2=(130, 70, 190), lc=(44, 40, 60), boots=DARK, arms=('down', 'up'), cloak=(100, 50, 150), geo=dict(tw=5, bw=4))
    s.line([(18, 9), (26, 6)], (150, 110, 70)); PX(s, [(27, 6), (28, 5)], s.lit((150, 240, 120)))


@reg('drow_warrior')
def _(s, r):
    fig(s, head='elf', skin=DROW, eye=s.lit((255, 90, 90)), hair='pony', hairc=WHITE, torso='armor', tc=(64, 46, 104),
        tc2=(170, 170, 200), lc=(44, 36, 70), boots=DARK, rh=('sword', (200, 200, 230), 8), lh=('crossbow',),
        pauldron=(90, 70, 140))


@reg('drow_mage')
def _(s, r):
    fig(s, size='robed', head='elf', skin=DROW, eye=s.lit((255, 140, 255)), hair='long', hairc=WHITE, hat='circlet',
        hatc=(200, 200, 220), hat2=(255, 120, 255), torso='robe', tc=(124, 84, 184), tc2=(200, 200, 220),
        rh=('staff', (240, 120, 255), 'orb', (50, 40, 60)), lh=('book', (60, 40, 90)), arms=('fwd', 'down'))


@reg('drow_priestess')
def _(s, r):
    g = fig(s, size='robed', head='elf', skin=DROW, eye=s.lit((255, 90, 120)), hair='long', hairc=WHITE,
            torso='dress', tc=(176, 56, 120), tc2=(40, 30, 50), rh=('whip', (60, 40, 60)), lh=('orb', (255, 90, 160)),
            arms=('up', 'down'))
    # spider crown and sigil
    s.ell(13, 3, 18, 7, (40, 30, 50)); PX(s, [(15, 5), (16, 5)], s.lit((255, 90, 120)))
    for sd in (-1, 1):
        cx = 13 if sd < 0 else 18
        s.line([(cx, 4), (cx + sd * 3, 2), (cx + sd * 4, 5)], (40, 30, 50)); s.line([(cx, 6), (cx + sd * 3, 6), (cx + sd * 4, 9)], (40, 30, 50))
    PX(s, [(15, 19), (16, 19), (14, 18), (17, 18), (14, 20), (17, 20)], (40, 30, 50))


@reg('light_elf_hostile')
def _(s, r):
    glow = s.lit((255, 250, 180))
    g = fig(s, head='elf', skin=(246, 238, 206), eye=s.lit((255, 130, 40)), hair='long', hairc=(250, 236, 150),
            torso='skirt', tc=(246, 244, 230), tc2=GOLD, legs='bare', boots=GOLD, rh=('spear', glow, glow),
            hat='halo', hatc=(255, 250, 180), brow=True, sleeve=(246, 244, 230), geo=dict(tw=5, bw=4))
    PX(s, [(12, 7), (11, 9), (19, 11), (9, 17), (22, 18), (13, 26), (18, 27)], (120, 90, 110))


@reg('dryad_guardian')
def _(s, r):
    sk = (178, 216, 150)
    leaf = (44, 124, 60)
    bark = (130, 94, 58)
    g = fig(s, skin=sk, eye=DARK, hair='long', hairc=leaf, torso='dress', tc=bark, tc2=(90, 60, 40),
            sleeve=sk, boots=bark, arms=('down', 'up'), geo=dict(tw=5, bw=4, head=(11, 5, 20, 14), sh=14, arm=(15, 22)),
            mouth=(200, 90, 110))
    s.ell(10, 2, 21, 6, leaf); PX(s, [(9, 5), (22, 5), (10, 3), (21, 3)], leaf)
    PX(s, [(12, 3), (19, 3)], (250, 150, 190)); PX(s, [(15, 2), (17, 4), (13, 5)], (110, 200, 100))
    s.line([(24, 8), (26, 4), (28, 6), (27, 11), (29, 15)], (70, 150, 70)); PX(s, [(27, 3), (29, 9), (28, 14), (25, 6)], (120, 210, 110))
    PX(s, [(12, 19), (17, 21), (14, 24), (19, 25), (11, 26), (16, 27)], (90, 180, 90))
    PX(s, [(9, 29), (8, 30), (22, 29), (23, 30)], bark)


@reg('erlking')
def _(s, r):
    e = s.lit((200, 255, 120))
    g = fig(s, size='robed', head='elf', skin=(196, 220, 186), eye=e, hair='long', hairc=WHITE, hat='antlers',
            hatc=(96, 74, 50), torso='robe', tc=(52, 104, 62), tc2=(120, 170, 80), cloak=(36, 70, 46),
            lh=('claws', (196, 220, 186)), rh=('claws', (196, 220, 186)), arms=('down', 'fwd'), hands=(196, 220, 186),
            brow=True, geo=dict(head=(11, 7, 20, 15)))
    s.rect(12, 7, 19, 8, (96, 74, 50)); PX(s, [(12, 6), (15, 6), (18, 6)], (120, 170, 80))
    PX(s, [(5, 27), (7, 25), (25, 26), (26, 24)], (120, 170, 80))


@reg('wild_hunt_captain')
def _(s, r):
    gh = s.lit((170, 220, 255))
    ar = (84, 96, 164)
    g = fig(s, size='large', hat='fullhelm', hatc=ar, eye=gh, torso='armor', tc=ar, tc2=(96, 104, 160),
            legs='pants', lc=(96, 104, 160), boots=ar, cloak=(36, 40, 84), rh=('sword', gh, 13, (96, 104, 160)),
            lh=('horn', IVORY), pauldron=(176, 186, 236), hands=ar, sleeve=(64, 74, 136),
            geo=dict(head=(11, 6, 20, 14), sh=14, arm=(15, 22)))
    for sd, bx in ((-1, 12), (1, 19)):
        s.line([(bx, 6), (bx + sd * 2, 3), (bx + sd * 4, 1)], IVORY); s.line([(bx + sd * 2, 3), (bx + sd, 1)], IVORY)
        s.line([(bx + sd * 3, 2), (bx + sd * 5, 3)], IVORY)
    PX(s, [(5, 27), (7, 29), (25, 28), (27, 26), (10, 29)], gh)


@reg('satyr_trickster')
def _(s, r):
    g = fig(s, skin=TAN, hair='curly', hairc=(120, 80, 40), beard='goatee', beardc=(120, 80, 40), torso='bare',
            tc=(120, 80, 40), tc2=(120, 80, 40), legs='goat', lc=(150, 104, 56), arms=('down', 'up'), mouth=True,
            geo=dict(tw=5, bw=4))
    PX(s, [(12, 4), (11, 3), (11, 2), (19, 4), (20, 3), (20, 2)], IVORY)
    for i in range(5):
        s.rect(20 + i, 6 + i // 2, 20 + i, 10, (224, 200, 130))
    s.line([(20, 8), (24, 8)], (150, 110, 60))
    PX(s, [(27, 3), (29, 5), (28, 1)], s.lit((255, 200, 255)))


@reg('satyr_warrior')
def _(s, r):
    g = fig(s, skin=(196, 136, 92), hair='wild', hairc=(84, 54, 34), beard='short', beardc=(84, 54, 34), torso='bare',
            tc=(84, 54, 34), tc2=DARK, legs='goat', lc=(110, 70, 40), rh=('club',), lh=('shield', (120, 84, 50), BRONZE, 'round'),
            brow=True)
    s.poly([(12, 5), (8, 4), (7, 8), (9, 10), (9, 7), (11, 7)], (190, 170, 130))
    s.poly([(19, 5), (23, 4), (24, 8), (22, 10), (22, 7), (20, 7)], (190, 170, 130))
    s.line([(11, 14), (19, 21)], LEATHER)


# =================================================================== snake women, spiders, birds
def snake_hair(s, box, c, eye, big=False):
    x0, y0, x1, y1 = box
    PX(s, [(x, y) for x, y in ell_pts(*box) if y <= y0 + 2], c)
    arms = [(-4, 2, -6, -1), (-2, 0, -4, -4), (1, -1, 0, -5), (4, -1, 5, -5), (7, 0, 9, -3), (9, 2, 11, 0), (-3, 5, -5, 6), (10, 5, 12, 7)]
    for i, (ax, ay, bx, by) in enumerate(arms):
        if not big and i in (2, 5):
            continue
        p0 = (x0 + 2 + ax * 0 + max(0, min(7, ax)), y0 + max(0, ay))
        p1 = (x0 + 1 + bx, max(1, y0 + by))
        mid = ((p0[0] + p1[0]) // 2 + (1 if i % 2 else -1), (p0[1] + p1[1]) // 2)
        s.line([p0, mid, p1], c)
        PX(s, [p1], eye)


@reg('medusa')
def _(s, r):
    e = s.lit((180, 255, 120))
    g = fig(s, skin=(226, 204, 150), eye=e, torso='dress', tc=(226, 204, 90), tc2=(150, 120, 50), sleeve=(226, 204, 150),
            boots=BRONZE, lh=('claws', BRONZE), rh=('bow', (120, 90, 50)), geo=dict(tw=5, bw=4, head=(11, 6, 20, 14), sh=14, arm=(15, 22)))
    snake_hair(s, g['head'], (76, 150, 80), s.lit((255, 230, 90)))


@reg('medusa_gorgon')
def _(s, r):
    e = s.lit((140, 255, 140))
    sc = (70, 160, 84)
    g = fig(s, skin=(170, 204, 150), eye=e, torso='top', tc=BRONZE, tc2=GOLD, legs='snake', lc=sc, belly=(190, 220, 130),
            wings=(214, 170, 70), lh=('claws', BRONZE), rh=('claws', BRONZE), brow=True,
            geo=dict(tw=5, bw=5, head=(11, 6, 20, 14), sh=14, arm=(15, 21), waist=22))
    snake_hair(s, g['head'], (50, 130, 66), s.lit((255, 90, 60)), big=True)
    PX(s, [(15, 13), (16, 13)], (200, 50, 60))
    PX(s, [(4, 14), (5, 17), (27, 14), (26, 17), (3, 19), (28, 19)], (160, 120, 50))


@reg('lamia')
def _(s, r):
    g = fig(s, skin=(226, 186, 156), hair='long', hairc=(60, 36, 70), torso='top', tc=(170, 120, 190), tc2=GOLD,
            legs='snake', lc=(150, 104, 176), belly=(226, 200, 220), eye=s.lit((255, 200, 90)), hat='circlet', hatc=GOLD,
            hat2=(255, 90, 120), arms=('down', 'fwd'), geo=dict(tw=5, bw=5, waist=22))
    PX(s, [(10, 25), (21, 24), (25, 27), (9, 27)], (110, 70, 140))
    s.rect(8, 17, 9, 17, GOLD); s.rect(22, 17, 23, 17, GOLD)


@reg('viper_priestess')
def _(s, r):
    sn = (90, 190, 100)
    g = fig(s, skin=TAN, hair='long', hairc=BLACK, torso='dress', tc=(214, 180, 90), tc2=(60, 90, 160),
            sleeve=TAN, arms=('up', 'up'), eye=s.lit((160, 255, 120)), hat='turban', hatc=(60, 90, 160), hat2=GOLD,
            geo=dict(head=(11, 6, 20, 14), sh=14, tw=5, bw=4, waist=22))
    for y, c in ((22, (180, 50, 50)), (24, (60, 90, 160)), (26, (180, 50, 50))):
        s.line([(9, y), (22, y)], c)
    s.rect(12, 15, 19, 17, (180, 50, 50))
    for sd, hx in ((-1, 8), (1, 23)):
        s.line([(hx, 12), (hx + sd, 8), (hx - sd, 5), (hx + sd, 2)], sn); s.line([(hx, 12), (hx + sd * 2, 15), (hx + sd, 18)], sn)
        PX(s, [(hx + sd, 2)], s.lit((255, 230, 90))); PX(s, [(hx + sd * 2, 1)], (220, 50, 60))


@reg('ettercap')
def _(s, r):
    sk = (128, 88, 150)
    e = s.lit((255, 90, 90))
    # spindly extra arms behind
    s.line([(10, 15), (4, 11), (2, 16)], (104, 70, 124), 2); s.line([(21, 15), (27, 11), (29, 16)], (104, 70, 124), 2)
    g = fig(s, skin=sk, torso='bare', belly=(190, 150, 200), tc=(90, 60, 110), tc2=(90, 60, 110), legs='bare', boots=None,
            lh=('claws',), rh=('claws',), eye=e, geo=dict(head=(10, 5, 21, 13), sh=13, tw=5, bw=7, lw=2, aw=2, arm=(14, 23), waist=24))
    PX(s, [(12, 8), (14, 7), (17, 7), (19, 8), (13, 10), (18, 10)], e)
    s.rect(14, 12, 14, 14, IVORY); s.rect(17, 12, 17, 14, IVORY)
    s.line([(26, 20), (28, 26), (26, 29)], WHITE); s.line([(26, 22), (30, 23)], WHITE)


@reg('anansi')
def _(s, r):
    gold, dkc = (226, 180, 50), (60, 40, 40)
    e = s.lit((255, 250, 200))
    for sd in (-1, 1):
        cx = 15.5
        for i, (dx, dy, ex, ey) in enumerate(((5, 14, 13, 7), (6, 17, 14, 14), (6, 20, 14, 24), (4, 22, 9, 29))):
            mx = (dx + ex) / 2 + 1
            my = min(dy, ey) - 3 if i < 2 else (dy + ey) / 2 - 2
            pts = [(int(cx + sd * dx), dy), (int(cx + sd * mx), int(my)), (int(cx + sd * ex), ey)]
            s.line(pts, dkc, 2)
    s.ell(8, 14, 23, 27, gold)
    for y in (17, 20, 23):
        s.line([(10, y), (21, y)], dkc)
    s.ell(11, 7, 20, 16, (120, 80, 56))
    PX(s, [(13, 11), (18, 11), (14, 9), (17, 9)], e)
    s.line([(13, 14), (18, 14)], WHITE); PX(s, [(12, 13), (19, 13)], WHITE)
    # the storyteller's little hat
    s.rect(11, 5, 20, 6, (170, 50, 50)); s.rect(13, 2, 18, 5, (170, 50, 50)); s.line([(13, 5), (18, 5)], gold)
    s.line([(16, 1), (16, 1)], WHITE)


@reg('harpy')
def _(s, r):
    fe = (196, 150, 84)
    sk = (226, 190, 160)
    w = (160, 110, 60)
    s.poly([(11, 13), (4, 5), (1, 9), (2, 18), (6, 23), (11, 20)], fe); s.poly([(20, 13), (27, 5), (30, 9), (29, 18), (25, 23), (20, 20)], fe)
    s.poly([(2, 12), (3, 19), (6, 23), (8, 19), (5, 17)], w); s.poly([(29, 12), (28, 19), (25, 23), (23, 19), (26, 17)], w)
    s.rect(13, 23, 14, 27, (226, 178, 62)); s.rect(17, 23, 18, 27, (226, 178, 62))
    PX(s, [(11, 28), (13, 28), (15, 28), (16, 28), (18, 28), (20, 28), (12, 29), (19, 29)], (226, 178, 62))
    s.ell(11, 12, 20, 24, fe); s.ell(13, 13, 18, 19, sk)
    s.rect(13, 15, 18, 16, (170, 60, 70))
    PX(s, [(12, 21), (14, 22), (17, 22), (19, 21), (15, 23)], w)
    s.ell(11, 3, 20, 12, sk)
    PX(s, [(x, y) for x, y in ell_pts(11, 3, 20, 12) if y <= 5 or ((x <= 12 or x >= 19) and y <= 9)], (140, 60, 50))
    s.rect(10, 6, 11, 14, (140, 60, 50)); s.rect(20, 6, 21, 14, (140, 60, 50))
    PX(s, [(14, 7), (17, 7)], s.lit((255, 220, 90))); PX(s, [(15, 10), (16, 10)], (190, 60, 70))
    PX(s, [(13, 2), (15, 1), (18, 2)], (140, 60, 50))


# =================================================================== water horses
def horse(s, body, mane, eye, horn=None, drip=None, teeth=False):
    e = s.lit(eye)
    s.poly([(7, 15), (3, 17), (2, 25), (4, 27), (6, 21), (8, 18)], mane)
    for x in (8, 12, 18, 21):
        s.rect(x, 20, x + 1, 27, body if x in (8, 21) else dk(body))
        s.rect(x, 28, x + 1, 29, DARK)
    s.ell(5, 13, 23, 22, body)
    s.poly([(18, 14), (22, 5), (27, 6), (25, 17)], body)
    s.ell(21, 3, 28, 9, body); s.rect(25, 6, 30, 10, body)
    PX(s, [(30, 8)], DARK); s.line([(27, 10), (30, 10)], DARK)
    if teeth:
        PX(s, [(27, 11), (29, 11)], IVORY)
    PX(s, [(22, 2), (23, 1), (25, 2)], body)
    s.poly([(17, 13), (20, 4), (22, 3), (22, 8), (19, 15)], mane)
    PX(s, [(25, 6)], e)
    if horn:
        PX(s, [(24, 2), (25, 1), (26, 1), (21, 2), (20, 1)], horn)
    if drip:
        d = s.lit(drip)
        PX(s, [(17, 16), (19, 18), (6, 23), (4, 28), (14, 24), (10, 25), (24, 13)], d)


@reg('each_uisce')
def _(s, r):
    s.shadow = False
    s.ell(2, 27, 29, 30, (50, 96, 150))
    horse(s, (46, 126, 164), (36, 90, 76), (220, 255, 255), drip=(170, 230, 255), teeth=True)
    PX(s, [(4, 28), (12, 29), (24, 28), (27, 29)], s.lit((170, 230, 255)))


@reg('puca')
def _(s, r):
    horse(s, (66, 50, 86), (36, 28, 50), (255, 150, 40), horn=(200, 190, 170))
    PX(s, [(4, 9), (9, 6), (13, 9), (29, 15), (2, 13)], s.lit((220, 140, 255)))
    PX(s, [(9, 28), (13, 28), (19, 28), (22, 28)], s.lit((255, 150, 40)))
