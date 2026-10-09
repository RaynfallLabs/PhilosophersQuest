"""Snakes, lizards, hydras and every kind of dragon."""
import math
from c_base import *  # noqa: F401,F403
from c_crit import fade, crawler


# ------------------------------------------------------------------ snakes
def coils(s, c, dk=None, tail=True, marks=None, wide=0):
    dk = dk or sh(c, -2)
    if tail:
        tube(s, [(23, 26), (28, 26), (30, 22)], c, 3, 1)
    s.ell(3 - wide, 22, 26 + wide, 29, c)
    s.ell(5, 17, 23, 26, dk)
    s.ell(6, 17, 22, 24, c)
    if marks:
        for x in range(6, 25, 4):
            s.px([(x, 26), (x + 1, 26), (x + 1, 27)], marks)
        for x in range(9, 21, 4):
            s.px([(x, 20), (x + 1, 20), (x + 1, 21)], marks)


def snake_head(s, hx, hy, c, eye, tongue=True, jaw=None, big=False):
    r = 1 if big else 0
    s.ell(hx - 3 - r, hy - 2 - r, hx + 3, hy + 2 + r, c)
    s.rect(hx + 2, hy - 1, hx + 5 + r, hy + 1, c)
    if jaw:
        s.rect(hx + 1, hy + 2, hx + 5 + r, hy + 2, jaw)
        s.px([(hx + 2, hy + 2), (hx + 4, hy + 2)], IVORY)
        s.rect(hx + 1, hy + 3, hx + 4 + r, hy + 3, c)
    elif tongue:
        s.line([(hx + 6 + r, hy + 1), (hx + 7 + r, hy + 2)], RED)
        s.px([(min(30, hx + 8 + r), hy + 1), (min(30, hx + 8 + r), hy + 3)], RED)
    s.px([(hx + 1, hy - 1)], eye)


def snake(s, c, belly, eye, w=4, marks=None, bands=None, hood=None, jaw=None, big=False, tail=True,
          necks=None, wide=0, tongue=True):
    coils(s, c, marks=marks, tail=tail, wide=wide)
    pts = necks or [(13, 21), (11, 15), (14, 9), (19, 8)]
    if hood:
        s.ell(8, 6, 19, 17, hood[0])
        s.ell(11, 9, 17, 16, hood[1])
    tube(s, pts, c, w + 0.6, w, bands=bands, belly=belly)
    hx, hy = pts[-1]
    snake_head(s, hx + 1, hy, c, eye, jaw=jaw, big=big, tongue=tongue)
    return hx + 1, hy


def cobra_front(s, c, belly, eye, hood_in, marks=None):
    """A cobra reared up and facing you, hood spread."""
    coils(s, c, marks=marks)
    tube(s, [(15, 23), (15, 16)], c, 5, 5)
    s.ell(8, 5, 23, 19, c)
    s.ell(11, 8, 20, 19, hood_in)
    for y in (12, 14, 16):
        s.line([(12, y), (19, y)], sh(hood_in, -1))
    s.ell(12, 2, 19, 8, c)
    s.px([(13, 5), (18, 5)], eye); s.px([(15, 7), (16, 7)], sh(c, -2))
    s.line([(15, 9), (15, 10)], RED); s.px([(14, 11), (16, 11)], RED)


def mini_head(s, hx, hy, col, eye, right=True, horn=None):
    """A small snapping dragon head for many-headed things."""
    f = 1 if right else -1
    if horn:
        s.px([(hx - 2 * f, hy - 3), (hx - 3 * f, hy - 4), (hx, hy - 3)], horn)
    s.ell(hx - 2, hy - 2, hx + 2, hy + 2, col)
    s.rect(min(hx + f, hx + 5 * f), hy - 1, max(hx + f, hx + 5 * f), hy, col)
    s.rect(min(hx + f, hx + 4 * f), hy + 1, max(hx + f, hx + 4 * f), hy + 1, (130, 30, 40))
    s.rect(min(hx + f, hx + 4 * f), hy + 2, max(hx + f, hx + 4 * f), hy + 2, col)
    s.px([(hx + 4 * f, hy + 1), (hx + 2 * f, hy + 1)], IVORY)
    s.px([(hx, hy - 1)], eye)


def generic_snake(r):
    s = Sprite()
    c = vivid(tup(r.get('color'), (90, 160, 80)))
    snake(s, c, sh(c, 1), s.lit((255, 230, 80)))
    return s.finish()


@reg('cobra')
def cobra(r):
    s = Sprite()
    cobra_front(s, (70, 170, 80), None, s.lit((255, 220, 70)), (226, 220, 150), marks=(40, 110, 60))
    s.px([(13, 10), (18, 10), (14, 9), (17, 9)], (40, 90, 50))       # spectacle mark
    return s.finish()


@reg('ra_serpent')
def ra_serpent(r):
    s = Sprite()
    sun = s.lit((255, 120, 50)); hot = s.lit((255, 230, 140))
    cobra_front(s, (240, 190, 50), None, s.lit((120, 230, 255)), (40, 90, 180), marks=(40, 90, 180))
    s.ell(12, 0, 19, 4, sun); s.px([(15, 1), (16, 1), (16, 2)], hot)   # the sun disc on its brow
    s.px([(15, 14), (16, 14), (15, 17), (16, 17)], GOLD)
    f = s.lit(FIRE)
    s.px([(22, 8), (24, 9), (26, 9), (28, 10), (29, 12)], f)          # spits fire at the king's enemies
    return s.finish()


@reg('rock_python')
def rock_python(r):
    s = Sprite()
    c = (190, 160, 104)
    dk = (110, 76, 46)
    snake(s, c, (236, 222, 180), s.lit((255, 200, 70)), w=6, marks=None, big=True, wide=1,
          necks=[(13, 21), (11, 15), (15, 10), (20, 10)])
    for x, y in ((5, 24), (11, 26), (17, 26), (22, 24), (9, 19), (15, 21), (19, 18), (9, 14), (13, 9)):
        s.ell(x, y, x + 2, y + 1, dk)                               # blotched like sun on rock
    return s.finish()


@reg('sable_serpent')
def sable_serpent(r):
    s = Sprite()
    c = (48, 46, 72)
    snake(s, c, (84, 80, 120), s.lit((200, 130, 255)), w=3, necks=[(13, 21), (9, 14), (13, 7), (19, 7)])
    s.px([(8, 23), (12, 18), (17, 24), (21, 20)], (110, 110, 160))    # the sheen of wet coal
    return s.finish()


@reg('swamp_serpent')
def swamp_serpent(r):
    s = Sprite()
    c = (88, 120, 66)
    water = (50, 84, 70)
    snake(s, c, (170, 180, 110), s.lit((255, 220, 80)), w=5, marks=(56, 80, 46), jaw=(244, 240, 236),
          necks=[(13, 21), (12, 15), (16, 10), (21, 10)], tail=False, big=True)
    s.rect(1, 27, 30, 29, water); s.px([(4, 26), (11, 26), (20, 26), (27, 26)], (120, 170, 140))
    s.line([(27, 26), (28, 14)], (110, 140, 60)); s.rect(27, 12, 29, 16, (110, 70, 40))   # a cattail
    s.shadow = False
    return s.finish()


@reg('sea_snake')
def sea_snake(r):
    s = Sprite()
    c, bk = (240, 210, 70), (30, 40, 90)
    water = (50, 110, 190)
    s.shadow = False
    s.rect(1, 25, 30, 29, water)
    # swimming, banded, with an oar-blade tail
    tube(s, [(6, 22), (10, 26), (15, 21), (20, 25), (24, 18), (22, 11)], c, 4, 4, bands=(bk, 6, 3))
    s.poly([(7, 22), (2, 16), (1, 22), (4, 26)], bk)
    s.rect(1, 26, 30, 29, water)
    s.px([(3, 25), (12, 25), (18, 25), (27, 25), (8, 28), (22, 28)], s.lit(FOAM))
    snake_head(s, 24, 10, bk, s.lit((255, 240, 120)))
    return s.finish()


@reg('jormungandr_spawn')
def jormungandr_spawn(r):
    s = Sprite()
    c = (50, 160, 120)
    fin = (30, 100, 110)
    s.poly([(10, 14), (7, 9), (12, 11), (11, 5), (15, 8)], fin)      # sail-fin down the neck
    hx, hy = snake(s, c, (190, 230, 190), s.lit((255, 230, 90)), w=4, marks=fin, jaw=(120, 30, 50),
                   necks=[(13, 21), (11, 15), (14, 9), (19, 8)], big=True)
    s.px([(hx + 3, hy + 4), (hx + 3, hy + 6)], s.lit(VENOM))
    s.px([(2, 29), (9, 30), (20, 30), (28, 29)], s.lit(FOAM))
    return s.finish()


@reg('basilisk_lesser')
def basilisk_lesser(r):
    s = Sprite()
    c = (130, 170, 80)
    # barely a foot long, and the grass dies around it
    dead = (150, 130, 80)
    for x in (3, 7, 24, 28):
        s.line([(x, 28), (x + 1, 24)], dead)
    tube(s, [(8, 27), (13, 24), (18, 27), (23, 24)], c, 3, 2)
    tube(s, [(8, 27), (9, 21), (14, 18)], c, 3, 3, belly=(220, 226, 150))
    snake_head(s, 16, 18, c, s.lit((255, 60, 60)))
    s.px([(15, 15), (16, 14), (17, 15)], WHITE)                     # the white crown-mark
    return s.finish()


@reg('basilisk')
def basilisk(r):
    s = Sprite()
    c = (90, 150, 80)
    hx, hy = snake(s, c, (210, 220, 140), s.lit((255, 240, 90)), w=4, marks=(50, 100, 60),
                   necks=[(13, 21), (11, 15), (14, 10), (19, 10)])
    s.rect(hx - 2, hy - 4, hx + 2, hy - 3, WHITE)                   # the crown that makes it king
    s.px([(hx - 2, hy - 5), (hx, hy - 6), (hx + 2, hy - 5)], WHITE)
    # the killing gaze
    g = s.lit((255, 250, 170))
    s.px([(hx + 4, hy - 2), (hx + 6, hy - 3), (hx + 8, hy - 4)], g)
    return s.finish()


@reg('elder_basilisk')
def elder_basilisk(r):
    s = Sprite()
    c = (70, 130, 50)
    dk = (40, 80, 40)
    for x in (9, 12):
        s.poly([(x, 16), (x - 3, 13), (x + 1, 12)], dk)             # spined back
    hx, hy = snake(s, c, (200, 214, 110), s.lit((255, 250, 150)), w=6, marks=dk, big=True, jaw=(120, 30, 40),
                   necks=[(14, 21), (11, 15), (14, 10), (19, 10)], wide=1)
    crown = s.lit((255, 240, 200))
    s.rect(hx - 3, hy - 5, hx + 2, hy - 4, GOLD)
    s.px([(hx - 3, hy - 6), (hx - 3, hy - 7), (hx - 1, hy - 6), (hx, hy - 7), (hx, hy - 8), (hx + 2, hy - 6), (hx + 2, hy - 7)], GOLD)
    s.px([(hx, hy - 5)], crown)
    s.line([(hx + 4, hy - 2), (30, hy - 6)], crown)                 # the gaze, a visible ray
    s.px([(2, 28), (4, 27), (28, 28)], (150, 150, 150))             # stone chips of what it looked at
    return s.finish()


@reg('sea_serpent_norse')
def sea_serpent_norse(r):
    s = Sprite()
    s.shadow = False
    c = (40, 130, 160)
    water = (30, 70, 140)
    foam = s.lit(FOAM)
    # humps breaking the surface
    for x0, x1, top in ((1, 9, 19), (8, 17, 16)):
        s.ell(x0, top, x1, 34, c)
        s.line([(x0 + 2, top + 2), (x1 - 2, top + 2)], (120, 200, 210))
    mane = (190, 60, 50)
    s.poly([(17, 12), (14, 7), (18, 9), (17, 3), (21, 6)], mane)    # the mane Olaus Magnus drew
    tube(s, [(21, 26), (19, 17), (20, 9), (24, 6)], c, 6, 5, belly=(170, 220, 220))
    snake_head(s, 25, 6, c, s.lit((255, 230, 90)), jaw=(120, 30, 50), big=True)
    s.rect(1, 25, 30, 30, water)
    s.px([(2, 24), (5, 25), (10, 24), (14, 25), (17, 24), (24, 24), (27, 25), (6, 28), (20, 28), (28, 28)], foam)
    return s.finish()


@reg('naga_guardian')
def naga_guardian(r):
    s = Sprite()
    c = (70, 180, 120)
    gem = s.lit((255, 70, 120))
    coils(s, c, marks=(226, 190, 70))
    s.ell(8, 4, 23, 17, (40, 120, 90))                              # the spread hood
    s.ell(10, 6, 21, 16, (226, 190, 70))
    tube(s, [(14, 21), (15, 16), (15, 12)], c, 6, 6, belly=(220, 236, 180))
    # a human face under a temple crown
    s.ell(12, 5, 19, 13, (200, 150, 110))
    s.px([(14, 8), (17, 8)], DARK); s.line([(15, 11), (16, 11)], (140, 70, 70))
    s.rect(12, 3, 19, 5, GOLD); s.poly([(14, 3), (15, 0), (16, 0), (17, 3)], GOLD)
    s.px([(15, 2), (16, 2)], gem)
    s.rect(12, 14, 19, 15, GOLD); s.px([(15, 15), (16, 15)], gem)
    # the treasure it guards
    s.ell(24, 25, 30, 29, GOLD); s.px([(26, 26), (28, 27)], s.lit((255, 240, 150)))
    return s.finish()


@reg('echidna')
def echidna(r):
    s = Sprite()
    c = (140, 100, 164)
    spk = (226, 200, 110)
    coils(s, c, marks=spk, wide=1)
    tube(s, [(14, 22), (15, 18), (15, 15)], c, 7, 6)
    s.px([(13, 18), (16, 20), (17, 17)], spk)
    # half fair-cheeked nymph
    sk = (232, 200, 176)
    s.rect(12, 9, 19, 16, sk); s.rect(12, 12, 19, 14, (90, 50, 110))
    s.rect(9, 10, 11, 16, sk); s.rect(20, 10, 22, 16, sk)
    s.ell(10, 0, 21, 10, (40, 30, 56))
    s.ell(12, 2, 19, 10, sk)
    s.rect(10, 5, 11, 13, (40, 30, 56)); s.rect(20, 5, 21, 13, (40, 30, 56))
    s.px([(14, 6), (17, 6)], s.lit((255, 210, 80))); s.line([(15, 8), (16, 8)], (150, 60, 80))
    # mother of monsters: two of the brood peer from her coils
    s.ell(1, 22, 5, 26, (90, 60, 60)); s.px([(2, 23), (4, 23)], s.lit((255, 80, 60)))
    s.ell(26, 20, 30, 24, (70, 110, 70)); s.px([(27, 21), (29, 21)], s.lit((255, 230, 80)))
    return s.finish()


def hydra_draw(s, c, belly, eye, necks, golden=None):
    # squat body with a tail and two thick legs
    tube(s, [(9, 24), (4, 26), (2, 22)], c, 4, 1.5)
    s.ell(7, 19, 24, 28, c)
    s.ell(11, 22, 21, 28, belly)
    s.rect(8, 25, 11, 28, c); s.rect(20, 25, 23, 28, c); s.px([(12, 28), (24, 28)], c)
    order = sorted(range(len(necks)), key=lambda i: -abs(necks[i][-1][0] - 15.5))
    for i in order:
        pts = necks[i]
        col = golden if (golden and i == len(necks) // 2) else (c if i % 2 == 0 else sh(c, -1))
        tube(s, pts, col, 3, 3)
        hx, hy = pts[-1]
        mini_head(s, hx, hy, col, eye, right=hx >= 15)


@reg('hydra')
def hydra(r):
    s = Sprite()
    c = (60, 150, 90)
    necks = [[(10, 21), (5, 18), (6, 12)], [(12, 20), (9, 12), (10, 5)], [(15, 20), (15, 12), (17, 4)],
             [(18, 20), (22, 16), (24, 11)], [(21, 22), (25, 22), (25, 18)]]
    hydra_draw(s, c, (190, 220, 150), s.lit((255, 220, 70)), necks)
    return s.finish()


@reg('mythic_hydra')
def mythic_hydra(r):
    s = Sprite()
    c = (70, 150, 110)
    gold = (240, 200, 70)
    necks = [[(9, 23), (5, 23), (6, 19)], [(10, 21), (4, 17), (6, 12)], [(12, 20), (9, 12), (10, 5)],
             [(15, 20), (15, 11), (16, 3)],
             [(18, 20), (20, 13), (22, 8)], [(20, 21), (24, 18), (25, 14)], [(21, 23), (25, 24), (25, 20)]]
    hydra_draw(s, c, (200, 230, 170), s.lit((255, 90, 60)), necks, golden=gold)
    s.px([(15, 0), (17, 0)], s.lit((255, 240, 150)))
    s.px([(12, 24), (16, 23), (19, 25)], s.lit(VENOM))             # blood that is poison
    return s.finish()


@reg('behir_lesser')
def behir_lesser(r):
    s = Sprite()
    c = (60, 100, 200)
    crawler(s, [(2, 21), (7, 25), (13, 21), (19, 25), (24, 19), (22, 11)], c, 5, (30, 50, 130), seg=(70, 120, 220), n=6)
    tube(s, [(4, 22), (9, 26), (15, 22), (20, 25)], (170, 200, 240), 1.5, 1.5)
    hx, hy = 23, 8
    dragon_head(s, hx, hy, c, s.lit(BOLT), (30, 50, 130), horns='back', jaw=True)
    b = s.lit(BOLT)
    s.px([(28, 12), (29, 13), (28, 14), (29, 15), (30, 16), (29, 17)], b)
    return s.finish()


# ------------------------------------------------------------------ lizards
def lizard(s, c, belly, eye, y0=17, y1=25, x0=8, x1=22, tailup=False, legc=None):
    legc = legc or sh(c, -1)
    if tailup:
        tube(s, [(x0 + 2, y1 - 3), (3, y1 - 2), (2, y1 - 8), (6, y1 - 11)], c, 4, 1.5)
    else:
        tube(s, [(x0 + 2, y1 - 3), (4, y1 + 1), (1, y1 + 3)], c, 4, 1.5)
    s.line([(x0 + 3, y1 - 2), (x0, y1), (x0, 28)], legc, 2); s.rect(x0 - 1, 28, x0 + 2, 28, legc)
    s.line([(x1 - 3, y1 - 2), (x1 - 1, y1 + 1), (x1 - 1, 28)], legc, 2); s.rect(x1 - 2, 28, x1 + 2, 28, legc)
    s.ell(x0, y0, x1, y1, c)
    s.ell(x0 + 4, y1 - 3, x1 - 1, y1, belly)
    hx = x1 + 1
    hy = (y0 + y1) // 2 - 2
    s.poly([(hx - 3, hy - 3), (hx + 2, hy - 3), (hx + 7, hy), (hx + 7, hy + 2), (hx - 3, hy + 4)], c)
    s.line([(hx + 1, hy + 2), (hx + 6, hy + 2)], sh(c, -2))
    s.px([(hx + 1, hy - 1)], eye)
    return hx, hy


@reg('giant_lizard')
def giant_lizard(r):
    s = Sprite()
    c = (80, 170, 80)
    hx, hy = lizard(s, c, (210, 230, 150), DARK, tailup=True)
    s.px([(hx, hy - 3)], s.lit((240, 250, 200)))                    # the third eye on its crown
    for x in (11, 14, 17, 20):
        s.px([(x, 16), (x, 17)], (40, 110, 60))
    s.line([(hx + 7, hy + 1), (min(30, hx + 9), hy + 2)], RED)
    return s.finish()


@reg('komodo_brute')
def komodo_brute(r):
    s = Sprite()
    c = (110, 124, 84)
    hx, hy = lizard(s, c, (160, 160, 120), s.lit((255, 200, 70)), y0=14, y1=25, x0=6, x1=22)
    s.px([(9, 17), (12, 16), (15, 17), (18, 16), (11, 20), (16, 20)], (76, 86, 60))
    s.line([(hx + 7, hy + 2), (hx + 7, hy + 4)], (250, 220, 90)); s.px([(hx + 6, hy + 5), (min(30, hx + 8), hy + 5)], (250, 220, 90))
    s.px([(hx + 3, hy + 4), (hx + 3, hy + 6)], s.lit(VENOM))        # the slow venom
    s.px([(5, 28), (21, 29), (24, 29)], IVORY)
    return s.finish()


@reg('mud_crawler')
def mud_crawler(r):
    s = Sprite()
    c = (104, 110, 76)
    mud = (120, 86, 50)
    hx, hy = lizard(s, c, (150, 150, 110), s.lit((255, 180, 60)), y0=18, y1=26, x0=7, x1=21)
    # the second shell of baked mud
    s.poly([(7, 21), (10, 15), (19, 15), (22, 21)], mud)
    s.line([(12, 15), (11, 21)], sh(mud, -2)); s.line([(16, 15), (17, 21)], sh(mud, -2))
    s.line([(9, 18), (20, 18)], sh(mud, -2))
    s.poly([(hx + 5, hy + 1), (hx + 8, hy + 2), (hx + 5, hy + 4)], (190, 170, 110))   # snapping beak
    s.px([(2, 29), (12, 29), (26, 29)], mud)
    return s.finish()


# ------------------------------------------------------------------ dragon parts
def dragon_head(s, hx, hy, c, eye, horn=IVORY, horns='back', jaw=False, beard=None, frill=None, big=False):
    hx = min(hx, 23)
    hy = max(hy, {'back': 8, 'long': 10, 'crown': 9, 'ram': 6, 'forward': 8, 'nose': 6}.get(horns, 6))
    if frill:
        s.poly([(hx - 2, hy - 2), (hx - 7, hy - 5), (hx - 6, hy), (hx - 8, hy + 3), (hx - 2, hy + 3)], frill)
    if horns == 'back':
        s.line([(hx - 2, hy - 3), (hx - 6, hy - 5)], horn, 2); s.line([(hx, hy - 3), (hx - 3, hy - 7)], horn, 2)
    elif horns == 'long':
        s.line([(hx - 2, hy - 3), (hx - 6, hy - 4), (hx - 9, hy - 7)], horn, 2)
        s.line([(hx, hy - 3), (hx - 2, hy - 7), (hx - 5, hy - 9)], horn, 2)
    elif horns == 'ram':
        s.line([(hx - 1, hy - 3), (hx - 5, hy - 5), (hx - 7, hy - 2), (hx - 5, hy + 1), (hx - 4, hy - 1)], horn, 2)
    elif horns == 'forward':
        s.line([(hx - 2, hy - 2), (hx - 4, hy - 5), (hx, hy - 7), (hx + 3, hy - 6)], horn, 2)
    elif horns == 'crown':
        for dx, dy in ((-6, -4), (-4, -7), (-1, -8), (2, -6)):
            s.line([(hx - 1, hy - 2), (hx + dx, hy + dy)], horn, 2 if dx < 0 else 1)
    elif horns == 'nose':
        s.line([(hx - 2, hy - 3), (hx - 6, hy - 5)], horn, 2)
        s.line([(hx + 5, hy - 2), (hx + 6, hy - 5)], horn, 2)
    elif horns == 'stub':
        s.px([(hx - 2, hy - 4), (hx - 3, hy - 5), (hx, hy - 4), (hx, hy - 5)], horn)
    r = 4 if big else 3
    s.ell(hx - r, hy - r, hx + 3, hy + 3, c)
    s.rect(hx + 2, hy - 1, hx + 7, hy + 1, c)
    s.px([(hx + 7, hy - 2)], c)
    if jaw:
        s.rect(hx + 1, hy + 2, hx + 6, hy + 2, (130, 30, 40))
        s.px([(hx + 2, hy + 2), (hx + 4, hy + 2), (hx + 6, hy + 2)], IVORY)
        s.rect(hx, hy + 3, hx + 5, hy + 4, sh(c, -1))
    else:
        s.rect(hx + 1, hy + 2, hx + 6, hy + 2, sh(c, -1))
        s.px([(hx + 3, hy + 2), (hx + 5, hy + 2)], IVORY)
    if beard:
        s.px([(hx, hy + 5 if jaw else hy + 3), (hx + 1, hy + 6 if jaw else hy + 4), (hx - 1, hy + 4), (hx + 2, hy + 5 if jaw else hy + 3)], beard)
    s.px([(hx + 6, hy - 1)], sh(c, -2))
    s.px([(hx + 1, hy - 1)], eye)
    s.px([(hx, hy - 2), (hx + 1, hy - 2), (hx + 2, hy - 2)], sh(c, -1))      # brow ridge
    return hx, hy


def bat_wing(s, ax, ay, mem, bone, k=1.0, tatter=False):
    def P(dx, dy):
        return (int(round(max(1, min(30, ax + dx * k)))), int(round(max(1, min(30, ay + dy * k)))))
    pts = [P(0, 0), P(-2, -14), P(-6, -10), P(-10, -14), P(-11, -7), P(-13, -5), P(-9, -3), P(-10, 0), P(-5, -1)]
    s.poly(pts, mem)
    if tatter:
        s.px([P(-8, -8), P(-7, -8), P(-4, -5), P(-9, -5), P(-6, -3)], (0, 0, 0))
    s.line([P(0, 0), P(-2, -14)], bone); s.line([P(-2, -13), P(-10, -14)], bone)
    s.line([P(-2, -13), P(-13, -5)], bone); s.line([P(-2, -13), P(-10, 0)], bone)
    return P


def punch(im, pts):
    px = im.load()
    for x, y in pts:
        if 0 <= x < 32 and 0 <= y < 32:
            px[x, y] = (0, 0, 0, 0)


def hoard(s, y=25):
    g = (226, 178, 62)
    s.ell(1, y, 30, 31, g)
    s.ell(4, y - 2, 14, y + 3, g); s.ell(18, y - 1, 28, y + 3, g)
    s.px([(4, y + 2), (9, y), (22, y + 1), (27, y + 3), (13, y + 3)], s.lit((255, 244, 170)))
    s.px([(6, y + 3), (24, y + 3)], s.lit((255, 70, 90))); s.px([(17, y + 3)], s.lit((90, 220, 255)))


def dragon(s, c, belly, mem, eye, k=1.0, horn=IVORY, horns='back', spikes=None, beard=None, tailtip='spade',
           wings=1.0, breath=None, frill=None, jaw=None, bone=None, far=True, lift=0, bigwing=False):
    """The standard dragon: seated three-quarter, head high on the right, wings rising on the left."""
    oy = 28 - lift

    def P(x, y):
        return (int(round(15.5 + (x - 15.5) * k)), int(round(oy + (y - 28) * k)))

    def W(w):
        return max(1.5, w * k)
    bone = bone or c
    if wings:
        wk = k * wings
        ax, ay = P(15, 17)
        if far:
            bat_wing(s, ax + int(5 * k), ay + 1, sh(mem, -1), sh(bone, -1), wk * 0.9)
        bat_wing(s, ax, ay, mem, bone, wk)
    # tail
    tube(s, [P(11, 24), P(5, 27), P(2, 23), P(4, 18)], c, W(4.5), W(1.6))
    tx, ty = P(4, 18)
    if tailtip == 'spade':
        s.poly([(tx - 2, ty), (tx, ty - 4), (tx + 2, ty)], spikes or c)
    elif tailtip == 'club':
        s.ell(tx - 2, ty - 4, tx + 2, ty, spikes or c)
    elif tailtip == 'barb':
        s.poly([(tx - 1, ty), (tx + 3, ty - 5), (tx + 2, ty + 1)], IVORY)
    elif tailtip == 'flame':
        flame(s, tx, ty, 5)
    # body and legs
    a, b = P(8, 15), P(22, 27)
    s.ell(a[0], a[1], b[0], b[1], c)
    a, b = P(14, 19), P(22, 27)
    s.ell(a[0], a[1], b[0], b[1] - 1, belly)
    for yy in (21, 23, 25):
        p = P(16, yy); q = P(21, yy)
        s.line([p, q], sh(belly, -1))
    a, b = P(7, 19), P(15, 28)
    s.ell(a[0], a[1], b[0], oy, c)                                  # haunch
    p = P(9, 27)
    s.rect(p[0], oy - 1, P(16, 28)[0], oy, c)
    s.px([(P(16, 28)[0] + 1, oy), (P(13, 28)[0], oy)], IVORY)
    a = P(19, 21)
    s.rect(a[0], a[1], a[0] + max(1, int(round(2 * k))), oy, c)     # foreleg
    s.rect(a[0], oy, a[0] + max(2, int(round(4 * k))), oy, c)
    s.px([(a[0] + max(2, int(round(4 * k))) + 1, oy)], IVORY)
    # neck
    np_ = [P(19, 18), P(23, 13), P(21, 7)]
    tube(s, np_, c, W(6), W(4.4))
    tube(s, [(np_[0][0] + 1, np_[0][1]), (np_[1][0] + 1, np_[1][1]), (np_[2][0] + 1, np_[2][1] + 1)], belly, 1.5, 1.5)
    if spikes:
        for (x, y) in (P(18, 9), P(18.5, 12), P(17, 15), P(13, 14), P(10, 15)):
            s.px([(x, y), (x - 1, y - 1)], spikes)
    hx, hy = P(22, 6)
    hy = max(hy, 5 if horns in ('long', 'crown') else 4)
    hx, hy = dragon_head(s, hx, hy, c, eye, horn, horns, jaw=bool(jaw or breath), beard=beard, frill=frill, big=k > 0.9)
    if breath:
        b1 = s.lit(breath[0]); b2 = s.lit(breath[1])
        s.poly([(hx + 5, hy + 4), (hx + 7, hy + 3), (30, hy + 9), (27, hy + 11)], b1)
        s.px([(hx + 6, hy + 5), (min(30, hx + 7), hy + 7)], b2)
    return P, (hx, hy)


def generic_dragon(r):
    s = Sprite()
    c = vivid(tup(r.get('color'), (200, 80, 40)))
    pf = r.get('peak_floor') or 30
    k = 0.74 if pf < 30 else (0.88 if pf < 60 else 1.0)
    dragon(s, c, sh(c, 1), sh(c, -1), s.lit((255, 230, 80)), k=k, spikes=sh(c, -2))
    return s.finish()


RED_D = (206, 50, 36)


@reg('young_red_dragon')
def young_red_dragon(r):
    s = Sprite()
    dragon(s, RED_D, (240, 170, 90), (150, 40, 40), s.lit((255, 230, 80)), k=0.76, horns='stub', horn=(250, 220, 170))
    return s.finish()


@reg('adult_red_dragon')
def adult_red_dragon(r):
    s = Sprite()
    dragon(s, (214, 40, 30), (244, 170, 80), (140, 30, 40), s.lit((255, 240, 90)), k=0.92, horns='back',
           horn=(60, 40, 44), spikes=(110, 24, 30), breath=(FIRE, FIRE2))
    return s.finish()


@reg('young_black_dragon')
def young_black_dragon(r):
    s = Sprite()
    c = (62, 62, 76)
    P, (hx, hy) = dragon(s, c, (110, 110, 96), (44, 60, 50), s.lit(VENOM), k=0.78, horns='forward', horn=(200, 196, 170), jaw=True)
    s.px([(hx + 4, hy + 5), (hx + 4, hy + 7), (hx + 5, hy + 9)], s.lit(VENOM))    # acid
    return s.finish()


@reg('young_dragon')
def young_dragon(r):
    s = Sprite()
    c = (226, 130, 50)
    dragon(s, c, (250, 220, 130), (170, 80, 40), s.lit((120, 230, 255)), k=0.82, horns='back', spikes=(150, 70, 30),
           tailtip='barb')
    # St George's lance, snapped
    s.line([(24, 27), (29, 25)], WOOD, 1); s.px([(30, 25)], STEEL)
    return s.finish()


@reg('adult_blue_dragon')
def adult_blue_dragon(r):
    s = Sprite()
    c = (60, 96, 214)
    P, (hx, hy) = dragon(s, c, (190, 210, 240), (120, 170, 244), s.lit(BOLT), k=0.92, horns='nose', horn=(210, 226, 250),
                         frill=(120, 170, 244), spikes=(150, 180, 250), jaw=True, bone=(40, 60, 150))
    b = s.lit(BOLT)
    s.px([(hx + 6, hy + 4), (hx + 7, hy + 5), (hx + 6, hy + 6), (hx + 7, hy + 7), (hx + 7, hy + 8), (hx + 6, hy + 9), (hx + 7, hy + 10)], b)
    return s.finish()


@reg('adult_dragon')
def adult_dragon(r):
    s = Sprite()
    c = (196, 90, 34)
    hoard(s, 25)
    dragon(s, c, (240, 190, 100), (120, 50, 30), s.lit((255, 240, 100)), k=0.86, horns='back', horn=(70, 44, 36),
           spikes=(110, 44, 24), lift=3, tailtip='spade')
    return s.finish()


@reg('elder_dragon')
def elder_dragon(r):
    s = Sprite()
    c = (150, 60, 40)
    dragon(s, c, (226, 180, 110), (90, 36, 44), s.lit((255, 200, 60)), k=0.97, horns='crown', horn=(226, 214, 180),
           spikes=(90, 36, 44), beard=(226, 214, 180), tailtip='club', breath=(FIRE, FIRE2))
    return s.finish()


@reg('ancient_dragon')
def ancient_dragon(r):
    s = Sprite()
    c = (50, 84, 226)
    gold = (236, 196, 80)
    hoard(s, 26)
    dragon(s, c, (236, 206, 110), (30, 44, 140), s.lit((255, 240, 150)), k=1.0, horns='crown', horn=gold,
           spikes=gold, beard=(220, 230, 250), tailtip='spade', lift=2, bone=gold)
    return s.finish()


@reg('abyssal_dragon')
def abyssal_dragon(r):
    s = Sprite()
    c = (84, 60, 70)                                               # cooled slag
    hot = s.lit((255, 80, 50))
    P, (hx, hy) = dragon(s, c, (130, 50, 50), (150, 30, 40), s.lit((255, 220, 80)), k=1.0, horns='ram', horn=(40, 30, 36),
                         spikes=(200, 40, 50), tailtip='barb', breath=((255, 70, 60), (255, 200, 120)))
    # the hellfire shows through the cracks
    s.px([(10, 19), (11, 20), (12, 22), (9, 23), (13, 17), (16, 16), (20, 14), (21, 11), (6, 26), (4, 24)], hot)
    return s.finish()


@reg('void_wyrm')
def void_wyrm(r):
    s = Sprite()
    c = (40, 26, 70)
    star = s.lit((230, 220, 255)); vio = s.lit((190, 90, 255))
    P, (hx, hy) = dragon(s, c, (70, 40, 120), (24, 16, 44), vio, k=1.0, horns='long', horn=(110, 70, 170),
                         spikes=(110, 70, 170), tailtip='none', jaw=True)
    s.px([(10, 20), (13, 23), (17, 18), (7, 9), (10, 6), (5, 13), (20, 12), (12, 11), (4, 25)], star)   # stars inside it
    s.px([(hx + 6, hy + 4), (hx + 7, hy + 6), (hx + 5, hy + 7), (hx + 7, hy + 9)], vio)
    im = s.finish()
    punch(im, [(8, 12), (9, 12), (6, 15), (11, 9)])                # the wings are torn through to nothing
    return im


@reg('dread_wyrm')
def dread_wyrm(r):
    s = Sprite()
    c = (170, 96, 50)
    sick = (150, 170, 80)
    # the bulk of a great wyrm, with wings that never finished growing
    P, (hx, hy) = dragon(s, c, (200, 170, 110), (120, 110, 60), s.lit((255, 120, 50)), k=1.0, horns='stub', horn=(90, 70, 50),
                         wings=0.5, far=False, tailtip='club', spikes=(110, 60, 36), breath=(FIRE, FIRE2))
    s.ell(8, 16, 13, 20, sick); s.ell(15, 14, 18, 17, sick); s.px([(6, 24), (11, 23)], sick)   # poisoned growths
    s.line([(hx - 2, hy - 3), (hx - 7, hy - 6)], (90, 70, 50), 2)   # one horn grew, one did not
    return s.finish()


@reg('fafnir_dragon')
def fafnir_dragon(r):
    s = Sprite()
    c = (190, 110, 40)
    hoard(s, 24)
    P, (hx, hy) = dragon(s, c, (236, 200, 120), (110, 60, 40), s.lit((120, 255, 150)), k=0.9, horns='stub', horn=(90, 60, 40),
                         wings=0.6, far=False, spikes=(110, 60, 30), lift=4, tailtip='none', jaw=True)
    # the Helm of Awe on his brow
    s.rect(hx - 3, hy - 4, hx + 3, hy - 3, STEEL); s.rect(hx - 2, hy - 6, hx + 2, hy - 5, STEEL)
    s.rect(hx + 3, hy - 3, hx + 3, hy - 1, STEEL)
    s.px([(hx, hy - 5)], s.lit((255, 220, 90)))
    s.px([(hx + 5, hy + 5), (hx + 6, hy + 7), (hx + 4, hy + 8)], s.lit(VENOM))   # he breathes poison, not fire
    s.ell(22, 22, 26, 26, s.lit((255, 230, 110))); s.px([(24, 24)], (226, 178, 62))   # Andvari's ring
    return s.finish()


@reg('sea_dragon_spawn')
def sea_dragon_spawn(r):
    s = Sprite()
    s.shadow = False
    c = (40, 110, 180)
    fin = (40, 190, 190)
    water = (26, 60, 130)
    # fins instead of wings
    s.poly([(14, 16), (10, 5), (6, 9), (3, 6), (4, 14), (8, 17)], fin)
    s.line([(14, 16), (10, 5)], (20, 120, 140)); s.line([(13, 15), (3, 6)], (20, 120, 140))
    P, (hx, hy) = dragon(s, c, (170, 220, 230), fin, s.lit((255, 240, 120)), k=0.82, horns='stub', horn=fin, wings=0,
                         frill=fin, tailtip='none', jaw=True)
    s.poly([(2, 16), (5, 12), (7, 18), (4, 21)], fin)              # tail fluke
    s.rect(1, 26, 30, 30, water)
    jet = s.lit((190, 236, 255))
    s.line([(hx + 7, hy + 3), (30, hy + 6)], jet, 2)
    s.px([(3, 25), (8, 26), (14, 25), (22, 25), (27, 26), (11, 29), (24, 29)], s.lit(FOAM))
    return s.finish()


# ------------------------------------------------------------------ wingless and two-legged kin
def drake(s, c, belly, eye, horn, spikes):
    tube(s, [(9, 21), (4, 24), (2, 20), (3, 15)], c, 4, 1.5)
    s.rect(11, 22, 13, 28, sh(c, -1)); s.rect(17, 22, 19, 28, sh(c, -1))
    s.ell(6, 15, 22, 24, c)
    s.ell(10, 20, 20, 24, belly)
    s.rect(7, 21, 10, 28, c); s.rect(7, 28, 12, 28, c); s.rect(19, 21, 22, 28, c); s.rect(19, 28, 24, 28, c)
    s.px([(13, 28), (25, 28)], IVORY)
    for x in range(8, 20, 3):
        s.poly([(x, 15), (x + 1, 12), (x + 2, 15)], spikes)
    tube(s, [(20, 18), (22, 15), (22, 13)], c, 5, 5)
    return dragon_head(s, 22, 11, c, eye, horn, 'back', jaw=True)


@reg('drake_fire')
def drake_fire(r):
    s = Sprite()
    c = (220, 104, 44)
    hx, hy = drake(s, c, (250, 210, 110), s.lit((255, 240, 100)), (90, 50, 40), (150, 50, 30))
    f1, f2 = s.lit(FIRE), s.lit(FIRE2)
    s.poly([(hx + 6, hy + 3), (30, hy + 4), (30, hy + 9), (hx + 5, hy + 5)], f1); s.px([(hx + 7, hy + 5), (hx + 7, hy + 6)], f2)
    flame(s, 3, 15, 5)
    return s.finish()


@reg('drake_cold')
def drake_cold(r):
    s = Sprite()
    c = (130, 184, 236)
    ice = s.lit((236, 250, 255))
    hx, hy = drake(s, c, (226, 240, 250), s.lit((230, 250, 255)), (236, 246, 255), (236, 246, 255))
    s.px([(hx + 6, hy + 4), (30, hy + 5), (hx + 6, hy + 6), (30, hy + 8), (hx + 5, hy + 8)], ice)
    s.px([(9, 25), (15, 25), (21, 25)], ice)                        # icicles under its belly
    s.px([(2, 14), (4, 13)], ice)
    return s.finish()


def wyvern_draw(s, c, belly, mem, eye, big):
    k = 1.0 if big else 0.86
    oy = 28
    horn = (60, 50, 44)

    def P(x, y):
        return (int(round(15.5 + (x - 15.5) * k)), int(round(oy + (y - 28) * k)))
    # the barbed tail
    tube(s, [P(11, 23), P(6, 27), P(2, 25), P(3, 20)], c, 3.6 * k, 1.6)
    tx, ty = P(3, 20)
    s.poly([(tx - 2, ty), (tx, ty - 5), (tx + 2, ty)], IVORY)
    s.px([(tx + 1, ty - 6), (tx + 2, ty - 8)], s.lit(VENOM))
    # wings are its arms: no forelegs at all
    ax, ay = P(15, 15)
    if big:
        bat_wing(s, ax + 5, ay, sh(mem, -1), sh(c, -1), k * 0.9)
    bat_wing(s, ax, ay - 1, mem, c, k * 1.0)
    wx, wy = ax - int(round(2 * k)), ay - 1 - int(round(14 * k))
    s.px([(wx, max(1, wy - 1)), (wx + 1, max(1, wy - 1))], IVORY)                    # wing-claw
    a, b = P(10, 13), P(21, 25)
    s.ell(a[0], a[1], b[0], b[1], c)
    a, b = P(14, 17), P(21, 25)
    s.ell(a[0], a[1], b[0], b[1], belly)
    for x in (11, 17):
        p = P(x, 22)
        s.rect(p[0], p[1], p[0] + 2, 28, c); s.rect(p[0], 28, p[0] + 4, 28, c); s.px([(p[0] + 5, 28)], IVORY)
    tube(s, [P(18, 16), P(22, 13), P(21, 8)], c, 5 * k, 4)
    hx, hy = P(22, 7)
    return dragon_head(s, hx, max(4, hy), c, eye, horn, 'back' if not big else 'crown', jaw=True)


@reg('wyvern')
def wyvern(r):
    s = Sprite()
    wyvern_draw(s, (96, 150, 70), (200, 210, 130), (150, 110, 60), s.lit((255, 220, 80)), False)
    return s.finish()


@reg('wyvern_greater')
def wyvern_greater(r):
    s = Sprite()
    c = (70, 100, 60)
    hx, hy = wyvern_draw(s, c, (170, 170, 100), (110, 50, 60), s.lit((255, 90, 60)), True)
    for x, y in ((18, 12), (15, 13), (12, 14)):
        s.px([(x, y), (x, y - 1)], (40, 56, 40))
    s.px([(hx + 4, hy + 5), (hx + 4, hy + 7)], s.lit(VENOM))
    return s.finish()


def wyrm_body(s, c, belly, eye, horn, horns, w=6, marks=None, legs=False, jaw=True, beard=None, necks=None, frill=None):
    coils(s, c, marks=marks, wide=1)
    pts = necks or [(14, 21), (12, 15), (15, 10), (19, 9)]
    if legs:
        s.line([(15, 19), (19, 22), (19, 27)], sh(c, -1), 2); s.rect(18, 28, 22, 28, sh(c, -1)); s.px([(23, 28)], IVORY)
    tube(s, pts, c, w + 0.6, w - 1, belly=belly)
    hx, hy = pts[-1]
    return dragon_head(s, hx + 1, hy - 1, c, eye, horn, horns, jaw=jaw, beard=beard, big=True, frill=frill)


@reg('lindworm')
def lindworm(r):
    s = Sprite()
    c = (120, 160, 70)
    wyrm_body(s, c, (226, 220, 130), s.lit((255, 220, 80)), (226, 220, 180), 'stub', w=5, marks=(70, 110, 50), legs=True)
    # two forelegs and no more
    s.line([(12, 18), (8, 20), (7, 24)], c, 2); s.px([(6, 25), (8, 25)], IVORY)
    # one of the skins it must shed
    s.line([(24, 27), (28, 26), (30, 28)], (220, 226, 200))
    return s.finish()


@reg('wyrm')
def wyrm(r):
    s = Sprite()
    c = (200, 160, 60)
    hx, hy = wyrm_body(s, c, (240, 220, 140), s.lit((255, 90, 50)), (110, 80, 40), 'long', w=7,
                       marks=(140, 100, 40), beard=(110, 80, 40))
    f1, f2 = s.lit(FIRE), s.lit(FIRE2)
    s.poly([(hx + 5, hy + 5), (hx + 7, hy + 4), (30, hy + 9), (27, hy + 12)], f1); s.px([(hx + 6, hy + 6), (hx + 7, hy + 8)], f2)
    for x in (8, 12, 16):
        s.px([(x, 16), (x, 15)], (110, 80, 40))
    return s.finish()


@reg('nidhogg_brood')
def nidhogg_brood(r):
    s = Sprite()
    c = (100, 44, 110)
    root = (120, 90, 60)
    # a root of the World Tree, gnawed
    s.poly([(20, 1), (30, 1), (30, 6), (26, 14), (23, 14), (25, 6)], root)
    s.px([(24, 11), (25, 13), (24, 13)], (60, 44, 40))
    hx, hy = wyrm_body(s, c, (170, 110, 160), s.lit(VENOM), (60, 30, 70), 'stub', w=5, marks=(60, 24, 70),
                       necks=[(14, 21), (11, 15), (13, 10), (17, 10)])
    s.px([(hx + 6, hy + 4), (hx + 7, hy + 6)], s.lit((150, 60, 200)))
    return s.finish()


@reg('nidhoggr_fragment')
def nidhoggr_fragment(r):
    s = Sprite()
    c = (44, 60, 52)
    glow = s.lit((110, 255, 130))
    root = (110, 84, 60)
    # the root of Yggdrasil crosses the dark above him
    tube(s, [(1, 3), (9, 6), (19, 3), (30, 5)], root, 5, 4)
    s.line([(5, 7), (4, 11)], root); s.line([(10, 8), (11, 12)], root); s.line([(28, 7), (29, 11)], root)
    s.px([(6, 4), (14, 5), (25, 4)], sh(root, -2))
    bat_wing(s, 13, 20, (30, 90, 60), (20, 40, 36), 0.85, tatter=False)
    hx, hy = wyrm_body(s, c, (80, 130, 90), glow, (20, 30, 30), 'crown', w=7, marks=(90, 200, 110),
                       necks=[(14, 22), (12, 17), (15, 13), (19, 13)])
    s.px([(hx + 3, hy - 4), (hx + 4, hy - 5), (hx + 6, hy - 4)], glow)      # he gnaws, and the root bleeds light
    s.px([(4, 29), (9, 30), (27, 29)], BONE)
    return s.finish()


@reg('jormungandr_juvenile')
def jormungandr_juvenile(r):
    s = Sprite()
    s.shadow = False
    c = (60, 150, 110)
    fin = (30, 90, 110)
    water = (24, 56, 120)
    foam = s.lit(FOAM)
    # great loops rising out of the sea
    for pts in ([(2, 29), (3, 17), (7, 14), (10, 19), (10, 29)], [(11, 29), (12, 21), (15, 19), (17, 23), (17, 29)]):
        mx, my = pts[2]
        s.poly([(mx - 3, my - 1), (mx, my - 5), (mx + 3, my - 1)], fin)
        tube(s, pts, c, 4.4, 4.4, belly=(200, 230, 170))
    s.poly([(17, 15), (13, 11), (17, 12), (15, 6), (20, 9)], fin)
    tube(s, [(22, 27), (20, 18), (20, 10), (22, 7)], c, 8, 6, belly=(200, 230, 170))
    hx, hy = dragon_head(s, 22, 6, c, s.lit((255, 230, 90)), fin, 'crown', jaw=True, big=True, frill=fin)
    s.px([(hx + 4, hy + 5), (hx + 5, hy + 7), (hx + 4, hy + 9)], s.lit(VENOM))    # the venom that will kill Thor
    s.rect(1, 25, 30, 30, water)
    s.px([(1, 24), (4, 25), (9, 24), (13, 25), (17, 24), (26, 24), (29, 25), (6, 28), (15, 28), (27, 28)], foam)
    return s.finish()


@reg('world_serpent')
def world_serpent(r):
    s = Sprite()
    s.shadow = False
    c = (50, 170, 110)
    dk = (30, 100, 90)
    # the serpent that circles the world and holds its own tail in its mouth
    pts = []
    for i in range(0, 33):
        a = math.radians(-70 + i * 10.3)
        pts.append((15.5 + math.cos(a) * 11.0, 16.5 + math.sin(a) * 10.5))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        w = 2.0 + 3.6 * i / n
        col = c if (i // 2) % 2 == 0 else dk
        s.ell(int(round(x - w / 2)), int(round(y - w / 2)), int(round(x + w / 2)), int(round(y + w / 2)), col)
    # the world inside the ring
    s.ell(9, 10, 22, 23, (40, 80, 170)); s.poly([(12, 13), (17, 12), (19, 16), (15, 19), (11, 17)], (90, 150, 80))
    s.px([(18, 20), (19, 20), (13, 21)], (90, 150, 80))
    hx, hy = pts[-1]
    hx, hy = int(hx), int(hy)
    s.ell(hx - 4, hy - 4, hx + 4, hy + 4, c)
    s.rect(hx + 2, hy - 2, hx + 7, hy + 2, c)
    s.px([(hx + 1, hy - 2)], s.lit((255, 230, 90)))
    s.line([(hx - 2, hy - 4), (hx - 5, hy - 6)], dk, 2)
    s.px([(hx + 4, hy + 3), (hx + 6, hy + 3)], IVORY)
    return s.finish()


@reg('tiamat')
def tiamat(r):
    s = Sprite()
    c = (170, 36, 70)
    eye = s.lit((255, 240, 120))
    tube(s, [(9, 25), (4, 27), (2, 23)], c, 4, 1.5)
    # five heads, five colours
    heads = [((84, 150, 230), [(10, 21), (5, 19), (6, 14)]), ((240, 240, 244), [(21, 21), (25, 20), (25, 15)]),
             ((70, 170, 80), [(12, 20), (9, 13), (10, 6)]), ((84, 78, 96), [(19, 20), (21, 13), (22, 8)]),
             ((226, 50, 44), [(15, 20), (15, 11), (16, 3)])]
    for col, pts in heads:
        tube(s, pts, col, 3, 3)
        hx, hy = pts[-1]
        mini_head(s, hx, hy, col, eye, right=hx >= 15, horn=GOLD)
    s.ell(7, 19, 24, 28, c)
    s.ell(11, 22, 20, 28, (240, 200, 130))
    for y in (24, 26):
        s.line([(12, y), (19, y)], (200, 150, 90))
    s.rect(7, 25, 10, 28, c); s.rect(21, 25, 24, 28, c); s.px([(6, 28), (11, 28), (20, 28), (25, 28)], IVORY)
    # the Tablet of Destinies on her breast
    s.rect(14, 20, 17, 22, s.lit((120, 240, 255)))
    return s.finish()


# ------------------------------------------------------------------ the dead ones
def bone_dragon(s, bone, glow, k=1.0, mem=None, horns='back', crown=False, heart=True):
    oy = 28

    def P(x, y):
        return (int(round(15.5 + (x - 15.5) * k)), int(round(oy + (y - 28) * k)))
    dk = sh(bone, -2)
    # wing fingers, with a few rags of membrane
    for ax, ay, kk in ((P(15, 16)[0] + int(5 * k), P(15, 16)[1] + 1, 0.9 * k), (P(15, 16)[0], P(15, 16)[1], k)):
        def Q(dx, dy, ax=ax, ay=ay, kk=kk):
            return (int(round(max(1, min(30, ax + dx * kk)))), int(round(max(1, ay + dy * kk))))
        if mem:
            s.poly([Q(0, 0), Q(-2, -13), Q(-6, -9), Q(-5, -3)], mem)
            s.poly([Q(-2, -13), Q(-10, -14), Q(-9, -8)], mem)
        s.line([Q(0, 0), Q(-2, -14)], bone); s.line([Q(-2, -13), Q(-10, -14)], bone)
        s.line([Q(-2, -13), Q(-13, -5)], bone); s.line([Q(-2, -13), Q(-10, 0)], bone)
    # tail vertebrae
    sp = smooth([P(11, 24), P(5, 27), P(2, 23), P(4, 18)], 5)
    for i, (x, y) in enumerate(sp):
        if i % 2 == 0:
            s.rect(int(x), int(y), int(x) + 1, int(y) + 1, bone)
    # ribcage with the light inside
    a, b = P(9, 16), P(21, 26)
    if heart:
        s.ell(a[0] + 2, a[1] + 2, b[0] - 2, b[1] - 2, glow)
    for x in range(a[0], b[0] + 1, 3):
        s.line([(x + 1, a[1]), (x, (a[1] + b[1]) // 2), (x + 1, b[1])], bone, 2 if k > 0.9 else 1)
    s.line([(a[0], a[1]), (b[0], a[1] - 1)], bone, 2)               # spine
    # legs
    p = P(10, 22)
    s.line([p, (p[0] - 1, 25), (p[0] + 1, 28)], bone, 2); s.rect(p[0] + 1, 28, p[0] + 4, 28, bone)
    p = P(19, 22)
    s.line([p, (p[0] + 1, 25), (p[0], 28)], bone, 2); s.rect(p[0], 28, p[0] + 3, 28, bone)
    # neck
    sp = smooth([P(20, 17), P(23, 13), P(21, 8)], 5)
    for i, (x, y) in enumerate(sp):
        if i % 2 == 0:
            s.rect(int(x) - 1, int(y), int(x) + 1, int(y) + 1, bone)
    hx, hy = P(22, 6)
    hy = max(hy, 8 if horns == 'back' else 9)
    hx = min(hx, 23)
    # skull
    if horns == 'back':
        s.line([(hx - 2, hy - 3), (hx - 6, hy - 5)], bone, 2); s.line([(hx, hy - 3), (hx - 3, hy - 7)], bone, 2)
    else:
        for dx, dy in ((-6, -4), (-4, -7), (-1, -8), (2, -6)):
            s.line([(hx - 1, hy - 2), (hx + dx, hy + dy)], bone, 2 if dx < 0 else 1)
    s.ell(hx - 3, hy - 3, hx + 3, hy + 3, bone)
    s.rect(hx + 2, hy - 1, hx + 7, hy + 1, bone)
    s.rect(hx, hy + 3, hx + 6, hy + 3, bone)
    s.px([(hx + 2, hy + 2), (hx + 4, hy + 2), (hx + 6, hy + 2)], bone)
    s.px([(hx + 1, hy + 2), (hx + 3, hy + 2), (hx + 5, hy + 2)], dk)
    s.rect(hx, hy - 1, hx + 1, hy, glow)
    s.px([(hx + 6, hy - 1)], dk)
    return hx, hy


@reg('undead_dragon_lesser')
def undead_dragon_lesser(r):
    s = Sprite()
    c = (96, 120, 90)
    glow = s.lit((190, 255, 120))
    # rotting, not yet bare: hide still hangs on it
    P, (hx, hy) = dragon(s, c, (150, 150, 110), (70, 80, 60), glow, k=0.9, horns='back', horn=BONE, tailtip='none', jaw=True)
    for x in (12, 14, 16, 18):                                      # ribs showing through
        s.line([(x, 18), (x - 1, 23)], BONE)
    s.px([(9, 21), (10, 25), (20, 16)], (60, 70, 50))
    # dragon's teeth, sown
    s.px([(25, 28), (27, 29), (29, 28)], IVORY)
    im = s.finish()
    punch(im, [(8, 9), (9, 9), (8, 10), (6, 12), (11, 7), (5, 15), (6, 15)])
    return im


@reg('lich_dragon_spawn')
def lich_dragon_spawn(r):
    s = Sprite()
    glow = s.lit((110, 200, 255))
    bone_dragon(s, (190, 196, 200), glow, k=0.8, mem=(60, 80, 110))
    # the phylactery it has only just made
    s.rect(25, 24, 28, 28, (70, 60, 90)); s.px([(26, 25), (27, 26)], glow); s.rect(25, 23, 28, 23, GOLD)
    return s.finish()


@reg('dracolich')
def dracolich(r):
    s = Sprite()
    glow = s.lit((200, 130, 255))
    hx, hy = bone_dragon(s, (226, 220, 206), glow, k=0.95, mem=(96, 70, 130))
    s.px([(hx + 7, hy + 4), (hx + 6, hy + 6), (hx + 7, hy + 8)], glow)
    return s.finish()


@reg('elder_dracolich')
def elder_dracolich(r):
    s = Sprite()
    glow = s.lit((150, 255, 220))
    bone = (70, 64, 84)                                             # a cathedral of black bone
    hx, hy = bone_dragon(s, bone, glow, k=1.0, mem=(40, 34, 60), horns='crown')
    s.px([(hx - 1, hy - 9), (hx - 5, hy - 8), (hx + 2, hy - 7)], glow)   # witchlight on every spire
    s.px([(4, 3), (13, 2), (2, 12), (9, 13), (4, 17), (2, 22)], glow)
    s.px([(hx + 7, hy + 4), (hx + 6, hy + 6), (hx + 7, hy + 8), (hx + 5, hy + 9)], glow)
    return s.finish()


@reg('spectral_dragon')
def spectral_dragon(r):
    s = Sprite()
    s.shadow = False
    c = (130, 160, 226)
    glow = s.lit((230, 244, 255))
    P, (hx, hy) = dragon(s, c, (190, 214, 250), (90, 110, 190), glow, k=0.95, horns='long', horn=(200, 220, 255),
                         tailtip='none', jaw=True, spikes=(200, 220, 255))
    s.px([(hx + 6, hy + 4), (hx + 7, hy + 6), (hx + 6, hy + 8)], glow)
    # the hoard it will not leave, seen through it
    s.px([(6, 29), (11, 30), (17, 29), (23, 30), (27, 29)], s.lit((255, 220, 110)))
    im = s.finish()
    px = im.load()
    for y in range(32):
        for x in range(32):
            r_, g, b, a = px[x, y]
            if a:
                fall = 1.0 if y < 14 else max(0.25, 1.0 - (y - 14) / 18)
                px[x, y] = (r_, g, b, int(min(a, 215) * fall))
    return im
