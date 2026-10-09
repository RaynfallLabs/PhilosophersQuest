"""Plants and fungi, and the player's companion pets."""
from c_base import *  # noqa: F401,F403
import c_beast as B
import c_scaly as SC
from c_crit import fade

LEAF = (80, 150, 60)
BARK = (110, 80, 54)


def leaf(s, x, y, c, d=1):
    s.px([(x, y), (x + d, y), (x + d, y - 1), (x + 2 * d, y - 1)], c)


def generic_plant(r):
    s = Sprite()
    c = vivid(tup(r.get('color'), LEAF))
    for pts in ([(15, 28), (10, 20), (6, 10)], [(16, 28), (18, 18), (15, 6)], [(17, 28), (23, 20), (26, 11)]):
        tube(s, pts, c, 3, 2)
    return s.finish()


# ------------------------------------------------------------------ molds
@reg('brown_mold')
def brown_mold(r):
    s = Sprite()
    s.shadow = False
    c, dk = (150, 100, 56), (96, 62, 40)
    for x0, y0, x1, y1 in ((3, 21, 15, 29), (11, 18, 24, 28), (19, 22, 29, 29), (7, 16, 14, 22)):
        s.ell(x0, y0, x1, y1, c)
    for x, y in ((6, 24), (10, 19), (14, 22), (18, 25), (22, 23), (25, 26), (13, 26)):
        s.ell(x, y, x + 2, y + 2, dk)
    # it drinks the warmth out of the air: frost forms around it
    ice = s.lit(ICE)
    for x, y in ((4, 12), (26, 15), (17, 11), (9, 8), (23, 7)):
        s.px([(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], ice)
    return s.finish()


@reg('yellow_mold')
def yellow_mold(r):
    s = Sprite()
    s.shadow = False
    c, dk = (226, 200, 50), (170, 140, 30)
    # an old skull, crusted over
    s.ell(11, 14, 22, 25, BONE); s.rect(14, 24, 19, 27, BONE)
    s.rect(13, 18, 15, 20, DARK); s.rect(18, 18, 20, 20, DARK); s.px([(16, 22), (17, 22)], DARK)
    for x0, y0, x1, y1 in ((2, 23, 13, 29), (18, 24, 29, 29), (9, 12, 17, 17), (19, 15, 25, 20), (11, 25, 21, 29)):
        s.ell(x0, y0, x1, y1, c)
    for x, y in ((5, 25), (10, 14), (22, 26), (21, 17), (14, 27), (26, 27)):
        s.px([(x, y), (x + 1, y)], dk)
    sp = s.lit((255, 244, 130))
    s.px([(6, 17), (4, 13), (9, 8), (14, 6), (20, 9), (25, 11), (27, 6), (17, 3), (11, 3), (23, 3)], sp)   # the spore cloud
    return s.finish()


# ------------------------------------------------------------------ vines
@reg('assassin_vine')
def assassin_vine(r):
    s = Sprite()
    c, dk = (60, 130, 50), (36, 84, 40)
    # the dead trunk it strangled
    s.rect(13, 6, 18, 28, (120, 104, 90)); s.poly([(13, 6), (15, 3), (16, 7), (18, 4), (18, 8)], (120, 104, 90))
    s.px([(15, 14), (16, 20)], (80, 68, 60))
    for pts in ([(10, 28), (19, 23), (12, 18), (19, 13), (13, 8)], [(21, 28), (12, 24), (19, 19), (12, 12)]):
        tube(s, pts, c, 2.4, 2.4)
    # reaching tendrils
    tube(s, [(13, 9), (7, 9), (3, 14), (5, 19)], dk, 2, 1); tube(s, [(19, 13), (25, 10), (29, 14), (27, 20)], dk, 2, 1)
    tube(s, [(12, 24), (6, 22), (3, 26)], dk, 2, 1)
    for x, y, d in ((8, 8, -1), (23, 10, 1), (9, 22, -1), (20, 18, 1), (11, 15, -1)):
        leaf(s, x, y, (110, 180, 80), d)
    s.px([(4, 20), (26, 21), (2, 27)], (120, 60, 150))              # grape-dark berries
    return s.finish()


@reg('yellow_musk_creeper')
def yellow_musk_creeper(r):
    s = Sprite()
    c = (90, 150, 70)
    y, yc = (240, 210, 60), (200, 120, 40)
    for pts in ([(15, 28), (9, 22), (13, 15), (8, 8)], [(16, 28), (22, 21), (18, 13), (24, 7)], [(15, 28), (16, 20), (15, 14)]):
        tube(s, pts, c, 2.4, 2)
    for x, yy, d in ((10, 20, -1), (20, 18, 1), (11, 12, 1), (21, 11, -1)):
        leaf(s, x, yy, (130, 190, 90), d)
    for fx, fy in ((8, 7), (24, 6), (15, 12)):
        s.ell(fx - 3, fy - 3, fx + 3, fy + 3, y)
        s.ell(fx - 1, fy - 1, fx + 1, fy + 1, yc)
    pol = s.lit((255, 244, 140))
    s.px([(3, 3), (13, 3), (18, 5), (29, 3), (4, 13), (28, 13), (19, 9), (12, 7)], pol)   # the musk
    return s.finish()


@reg('thorn_slinger')
def thorn_slinger(r):
    s = Sprite()
    c, dk = (170, 190, 130), (110, 130, 80)
    s.rect(14, 23, 17, 28, BARK)
    for x0, y0, x1, y1 in ((6, 15, 17, 26), (14, 14, 25, 26), (10, 10, 21, 20)):
        s.ell(x0, y0, x1, y1, c)
    for x, y in ((9, 19), (14, 22), (19, 18), (15, 13), (21, 22)):
        s.px([(x, y), (x + 1, y + 1)], dk)
    pod = (200, 110, 60)
    for x, y in ((8, 16), (21, 15), (14, 16), (17, 21), (11, 22)):
        s.ell(x, y, x + 3, y + 3, pod)
    th = s.lit((250, 244, 220))
    for a, b in (((6, 13), (2, 9)), ((24, 12), (28, 8)), ((15, 8), (15, 3)), ((26, 20), (30, 19)), ((5, 21), (1, 20)), ((10, 9), (8, 5)), ((21, 9), (23, 5))):
        s.line([a, b], th)
    return s.finish()


@reg('vine_horror')
def vine_horror(r):
    s = Sprite()
    c, dk = (50, 110, 60), (30, 70, 44)
    blood = s.lit((255, 60, 60))
    # a man-shape of woven creeper
    tube(s, [(12, 22), (11, 26), (9, 28)], dk, 4, 4); tube(s, [(19, 22), (20, 26), (22, 28)], dk, 4, 4)
    s.ell(9, 10, 22, 24, c)
    for pts in ([(10, 13), (15, 17), (21, 13)], [(10, 19), (16, 22), (21, 18)], [(13, 11), (15, 23)]):
        s.line(pts, dk)
    tube(s, [(10, 13), (5, 15), (3, 21), (5, 25)], c, 3, 2); tube(s, [(21, 13), (26, 14), (29, 19), (27, 24)], c, 3, 2)
    s.px([(4, 26), (6, 26), (26, 25), (28, 25), (2, 22), (30, 20)], (150, 130, 80))   # thorns
    s.ell(11, 3, 20, 11, c)
    tube(s, [(12, 4), (9, 1)], dk, 2, 1); tube(s, [(19, 4), (22, 1)], dk, 2, 1)
    s.rect(13, 6, 14, 7, blood); s.rect(17, 6, 18, 7, blood)
    s.px([(15, 14), (16, 15), (15, 16)], blood)                     # it grew from spilled blood
    for x, y, d in ((8, 11, -1), (22, 20, 1), (17, 3, 1)):
        leaf(s, x, y, (110, 170, 80), d)
    return s.finish()


@reg('shambling_mound')
def shambling_mound(r):
    s = Sprite()
    c, dk, moss = (84, 104, 50), (56, 70, 40), (130, 150, 70)
    s.poly([(4, 28), (6, 16), (11, 8), (20, 8), (25, 16), (27, 28)], c)
    s.ell(1, 13, 9, 26, c); s.ell(22, 13, 30, 26, c)                # drooping arms
    for x in range(5, 27, 3):
        s.line([(x, 12 + (x * 7) % 5), (x - 1, 18 + (x * 5) % 6), (x, 25 + (x * 3) % 3)], dk)
    for x, y in ((8, 14), (14, 11), (20, 15), (11, 21), (22, 22), (3, 18), (27, 17), (16, 24)):
        s.px([(x, y), (x + 1, y), (x, y + 1)], moss)
    eye = s.lit((255, 230, 90))
    s.rect(12, 13, 13, 14, eye); s.rect(18, 13, 19, 14, eye)
    s.line([(13, 18), (18, 18)], (30, 36, 26))
    s.px([(2, 27), (1, 28), (29, 27), (30, 28)], dk)
    s.line([(9, 8), (7, 4)], (150, 130, 70)); s.line([(21, 8), (24, 5)], (150, 130, 70))    # reeds
    return s.finish()


@reg('corrupted_treant')
def corrupted_treant(r):
    s = Sprite()
    c, dk = (84, 70, 62), (50, 40, 44)
    rot = s.lit((190, 90, 255))
    # roots
    s.poly([(10, 28), (12, 22), (19, 22), (21, 28)], c)
    s.line([(11, 27), (6, 29)], c, 2); s.line([(20, 27), (25, 29)], c, 2)
    # trunk
    s.poly([(11, 24), (10, 9), (21, 9), (20, 24)], c)
    for x in (13, 17):
        s.line([(x, 11), (x - 1, 17), (x, 23)], dk)
    # bare branch arms and a dead crown
    s.line([(10, 13), (5, 15), (3, 21)], c, 2); s.line([(3, 21), (1, 24)], c); s.line([(3, 21), (5, 25)], c)
    s.line([(21, 13), (26, 15), (28, 21)], c, 2); s.line([(28, 21), (30, 24)], c); s.line([(28, 21), (26, 25)], c)
    for pts in ([(11, 9), (7, 4), (4, 3)], [(13, 9), (12, 2)], [(18, 9), (19, 2)], [(20, 9), (24, 4), (28, 3)], [(7, 4), (7, 1)], [(24, 4), (24, 1)]):
        s.line(pts, c, 2 if len(pts) == 3 else 1)
    s.px([(4, 5), (27, 5), (12, 4)], (110, 130, 50))                # a last few sick leaves
    # the face, and the rot shining out of it
    s.rect(12, 12, 14, 13, rot); s.rect(17, 12, 19, 13, rot)
    s.poly([(13, 17), (18, 17), (17, 20), (14, 20)], (20, 14, 24))
    s.px([(15, 18)], rot)
    s.px([(11, 21), (12, 22), (19, 15), (20, 16)], rot)
    return s.finish()


# ------------------------------------------------------------------ fungi
def mushroom_person(s, cap, stem, spot, eye, big):
    if big:
        s.rect(12, 23, 14, 28, stem); s.rect(17, 23, 19, 28, stem)
        s.rect(11, 28, 14, 28, stem); s.rect(17, 28, 20, 28, stem)
        s.rect(11, 13, 20, 24, stem)
        s.rect(8, 15, 10, 21, stem); s.rect(21, 15, 23, 21, stem)
        s.ell(3, 2, 28, 14, cap); s.rect(4, 9, 27, 12, cap)
        s.rect(6, 13, 25, 13, sh(cap, -2))
        for x, y in ((7, 7), (12, 4), (18, 5), (23, 8), (15, 9)):
            s.ell(x, y, x + 2, y + 2, spot)
        s.px([(13, 17), (18, 17)], eye)
    else:
        s.rect(13, 25, 14, 28, stem); s.rect(17, 25, 18, 28, stem)
        s.rect(12, 18, 19, 25, stem)
        s.rect(10, 19, 11, 23, stem); s.rect(20, 19, 21, 23, stem)
        s.ell(7, 10, 24, 19, cap); s.rect(8, 15, 23, 17, cap)
        s.rect(10, 18, 21, 18, sh(cap, -2))
        for x, y in ((10, 13), (15, 11), (20, 14)):
            s.rect(x, y, x + 1, y + 1, spot)
        s.px([(14, 21), (17, 21)], eye)


@reg('myconid_worker')
def myconid_worker(r):
    s = Sprite()
    mushroom_person(s, (170, 120, 200), (226, 214, 200), (226, 200, 240), DARK, False)
    # carrying a basket of compost
    s.rect(21, 22, 25, 25, WOOD); s.px([(22, 21), (24, 21)], (90, 130, 60))
    return s.finish()


@reg('myconid_sovereign')
def myconid_sovereign(r):
    s = Sprite()
    glow = s.lit((255, 170, 250))
    mushroom_person(s, (210, 60, 190), (236, 220, 226), (255, 220, 250), glow, True)
    s.line([(14, 20), (17, 20)], (120, 80, 110))
    # staff grown, not cut
    s.line([(25, 14), (25, 28)], (150, 110, 130), 2); s.ell(23, 10, 28, 15, (240, 150, 230)); s.px([(25, 12)], glow)
    s.px([(2, 16), (5, 19), (28, 18), (3, 23), (29, 23)], glow)     # rapport spores
    return s.finish()


@reg('violet_fungus')
def violet_fungus(r):
    s = Sprite()
    c, cap = (150, 110, 170), (124, 44, 170)
    # whip-branches that rot what they touch
    for pts in ([(13, 19), (7, 17), (3, 11), (5, 6)], [(18, 19), (24, 17), (28, 11), (26, 6)], [(13, 22), (6, 23), (2, 20)], [(18, 22), (25, 23), (29, 20)]):
        tube(s, pts, c, 2.4, 1.2)
    s.px([(5, 5), (26, 5), (1, 19), (30, 19)], s.lit((220, 140, 255)))
    s.poly([(12, 28), (13, 14), (18, 14), (19, 28)], (200, 180, 200))
    s.px([(14, 20), (16, 23), (15, 17)], (150, 130, 160))
    s.ell(6, 4, 25, 15, cap); s.rect(7, 10, 24, 13, cap)
    s.rect(9, 14, 22, 14, (70, 30, 100))
    for x, y in ((10, 8), (15, 6), (20, 9)):
        s.rect(x, y, x + 1, y + 1, (200, 140, 240))
    return s.finish()


@reg('gas_spore')
def gas_spore(r):
    s = Sprite()
    c, dk = (170, 196, 170), (110, 140, 120)
    # rhizome stalks above, trailing roots below
    for pts in ([(11, 8), (8, 3), (6, 4)], [(15, 6), (15, 1)], [(20, 8), (23, 3), (25, 4)]):
        s.line(pts, dk, 2)
    s.px([(6, 5), (15, 1), (25, 5)], (226, 220, 150))
    for pts in ([(11, 22), (9, 26), (10, 29)], [(15, 23), (15, 28)], [(20, 22), (22, 26), (21, 29)]):
        s.line(pts, dk)
    s.ell(5, 5, 26, 24, c)
    for x, y in ((8, 11), (22, 9), (9, 18), (21, 19), (16, 21)):
        s.px([(x, y), (x + 1, y)], dk)
    # the false eye that fools you into striking it
    s.ell(11, 10, 20, 18, (226, 230, 210)); s.ell(14, 12, 18, 16, (120, 150, 90)); s.px([(16, 14)], DARK)
    return s.finish()


@reg('fungal_horror')
def fungal_horror(r):
    s = Sprite()
    c, cap, cap2 = (150, 170, 110), (110, 150, 70), (190, 120, 70)
    sp = s.lit((210, 255, 130))
    s.poly([(3, 28), (6, 17), (12, 12), (20, 12), (26, 17), (28, 28)], c)   # the colony heap
    # the adventurer it began on
    s.ell(12, 18, 19, 25, BONE); s.px([(14, 21), (17, 21)], DARK); s.rect(14, 24, 17, 25, BONE)
    s.line([(22, 26), (27, 23)], STEEL)
    for x, y, w, cc in ((3, 13, 9, cap), (20, 12, 9, cap), (10, 5, 11, cap2), (6, 21, 5, cap2), (21, 20, 6, cap)):
        s.rect(x + w // 2 - 1, y + 3, x + w // 2 + 1, y + 7, (220, 214, 190))
        s.ell(x, y, x + w, y + 5, cc)
        s.px([(x + 2, y + 1), (x + w - 3, y + 2)], sh(cc, 2))
    s.px([(10, 15), (20, 16)], sp)
    s.px([(2, 6), (7, 3), (17, 2), (24, 4), (29, 8), (27, 13), (5, 10)], sp)   # spore burst
    return s.finish()


# ------------------------------------------------------------------ pets: small helpers
def cute_eye(s, x, y, c=DARK, big=True):
    if big:
        s.rect(x, y, x + 1, y + 1, c); s.px([(x, y)], WHITE)
    else:
        s.px([(x, y)], c)


# fire line: orange hide, cream belly, a crest of living flame that grows with it
F_BODY, F_BELLY, F_DARK = (240, 130, 50), (255, 226, 160), (170, 60, 40)


@reg('emberpup')
def emberpup(r):
    s = Sprite()
    tube(s, [(10, 24), (6, 23), (5, 19)], F_BODY, 3.4, 2.4); s.px([(5, 18), (4, 19), (5, 19)], F_BELLY)
    s.ell(9, 17, 21, 28, F_BODY)
    s.ell(13, 20, 20, 27, F_BELLY)
    s.rect(10, 26, 13, 28, F_BODY); s.rect(18, 26, 21, 28, F_BODY)
    s.poly([(11, 10), (10, 4), (15, 8)], F_DARK); s.poly([(22, 10), (24, 4), (19, 8)], F_DARK)   # ears
    s.ell(9, 7, 24, 20, F_BODY)
    s.ell(15, 13, 23, 19, F_BELLY); s.px([(19, 14), (20, 14)], DARK); s.line([(18, 17), (21, 17)], (190, 90, 70))
    s.px([(19, 18)], PINK)
    cute_eye(s, 13, 11); cute_eye(s, 21, 11)
    flame(s, 17, 8, 6)                                              # a single ember tuft
    return s.finish()


@reg('flamescale')
def flamescale(r):
    s = Sprite()
    d = B.dims(1, x0=6, x1=21, y0=15, y1=22, lw=3, hx=23, hy=12)
    tube(s, [(8, 19), (4, 19), (3, 14), (5, 11)], F_BODY, 3.4, 2)
    B.quad(s, F_BODY, d, belly=F_BELLY)
    for x in (8, 11, 14):
        s.poly([(x, 16), (x + 1, 14), (x + 3, 16)], F_DARK)          # the first scale plates
    B.neck(s, d, F_BODY)
    s.poly([(20, 9), (19, 4), (22, 8)], F_DARK); s.poly([(25, 9), (27, 4), (23, 8)], F_DARK)
    s.ell(18, 7, 27, 16, F_BODY)
    s.rect(24, 11, 29, 14, F_BELLY); s.px([(29, 11)], DARK); s.line([(25, 15), (28, 15)], (190, 90, 70))
    cute_eye(s, 22, 10); s.px([(26, 10)], DARK)
    f1, f2 = s.lit(FIRE), s.lit(FIRE2)
    s.poly([(14, 15), (15, 10), (17, 13), (19, 7), (21, 9), (20, 14)], f1); s.px([(18, 12), (19, 11), (16, 13)], f2)   # flame mane
    return s.finish()


@reg('infernodrake')
def infernodrake(r):
    s = Sprite()
    f1, f2 = s.lit(FIRE), s.lit(FIRE2)
    P, (hx, hy) = SC.dragon(s, F_BODY, F_BELLY, (176, 60, 44), DARK, k=0.98, horns='back', horn=F_DARK, spikes=None,
                            tailtip='none', bone=F_BODY, far=True)
    # the flame crest, now a full mane down neck and back
    s.poly([(18, 17), (16, 12), (18, 13), (17, 8), (19, 10), (19, 5), (21, 9)], f1)
    s.px([(18, 11), (19, 8), (18, 15)], f2)
    s.poly([(9, 17), (10, 13), (12, 15), (13, 12), (15, 16)], f1); s.px([(11, 15), (13, 14)], f2)
    s.px([(hx + 1, hy - 1)], DARK); s.px([(hx + 1, hy - 2)], WHITE)
    for x in (10, 13):
        s.px([(x, 21), (x + 1, 20)], F_DARK)
    return s.finish()


# plant line: green hide, bark-brown legs, one pink flower that opens as it grows
P_BODY, P_BELLY, P_LEAF, P_PINK, P_YEL = (120, 196, 96), (214, 236, 160), (60, 140, 70), (244, 130, 170), (255, 226, 100)


@reg('seedling')
def seedling(r):
    s = Sprite()
    d = B.dims(0, x0=8, x1=19, y0=19, y1=25, lw=2, hx=21, hy=16)
    s.poly([(9, 22), (3, 17), (2, 22), (5, 25)], P_LEAF); s.line([(8, 22), (4, 20)], sh(P_LEAF, 1))   # a leaf for a tail
    B.quad(s, P_BODY, d, belly=P_BELLY, feet=BARK)
    s.ell(14, 10, 26, 22, P_BODY)                                # all head, as babies are
    s.rect(23, 16, 28, 19, P_BODY); s.px([(28, 16)], DARK); s.line([(24, 20), (27, 20)], (60, 110, 60))
    cute_eye(s, 19, 14); s.px([(24, 14)], DARK)
    s.px([(17, 18), (18, 18)], P_PINK)
    # one closed bud on its crown, between two seed-leaves
    s.poly([(18, 10), (13, 7), (14, 10)], P_LEAF); s.poly([(20, 10), (25, 7), (24, 10)], P_LEAF)
    s.ell(17, 5, 21, 10, P_PINK); s.px([(19, 5)], P_YEL)
    return s.finish()


@reg('bloomsaur')
def bloomsaur(r):
    s = Sprite()
    d = B.dims(1, x0=6, x1=21, y0=15, y1=23, lw=3, hx=23, hy=13)
    # a leaf for a tail
    s.poly([(8, 19), (2, 13), (1, 18), (4, 22)], P_LEAF); s.line([(7, 19), (3, 16)], sh(P_LEAF, 1))
    B.quad(s, P_BODY, d, belly=P_BELLY, feet=BARK)
    s.px([(9, 17), (12, 16), (10, 20)], P_LEAF)
    # the bud has opened into a ruff of petals round its neck
    for x, y in ((16, 9), (14, 13), (15, 18), (19, 20), (20, 6)):
        s.ell(x, y, x + 4, y + 4, P_PINK)
    s.ell(17, 7, 27, 18, P_BODY)
    s.rect(24, 12, 29, 15, P_BODY); s.px([(29, 12)], DARK); s.line([(25, 16), (28, 16)], (60, 110, 60))
    cute_eye(s, 21, 10); s.px([(26, 10)], DARK)
    s.px([(18, 12), (17, 15)], P_YEL)
    return s.finish()


@reg('thornback')
def thornback(r):
    s = Sprite()
    d = B.dims(2, x0=3, x1=22, y0=12, y1=23, lw=4, hx=24, hy=14)
    s.poly([(5, 18), (1, 12), (1, 19), (3, 23)], P_LEAF)
    # club tail of bramble
    B.quad(s, P_BODY, d, belly=P_BELLY, feet=BARK)
    # a hedge of thorned bramble along the back, with flowers in full bloom
    s.poly([(4, 16), (6, 10), (19, 9), (21, 15)], BARK)
    for x in (5, 9, 13, 17):
        s.poly([(x, 10), (x + 1, 5), (x + 3, 10)], (226, 214, 170))
    for x, y in ((7, 11), (14, 10)):
        s.ell(x, y, x + 4, y + 4, P_PINK); s.px([(x + 2, y + 2)], P_YEL)
    s.px([(11, 14), (18, 13)], P_LEAF)
    s.ell(17, 9, 23, 20, P_PINK)                                    # petal ruff
    s.ell(18, 8, 29, 20, P_BODY)
    s.rect(26, 14, 30, 17, P_BODY); s.px([(30, 14)], DARK); s.line([(26, 18), (29, 18)], (60, 110, 60))
    s.px([(27, 19), (29, 19)], IVORY)
    cute_eye(s, 22, 12); s.px([(27, 12)], DARK)
    s.poly([(20, 9), (21, 5), (23, 8)], (226, 214, 170))
    return s.finish()


# water line: blue hide, a spiral shell that winds one more turn each stage
W_BODY, W_BELLY, W_SHELL, W_BAND, W_FIN = (84, 160, 226), (220, 240, 250), (244, 214, 170), (226, 130, 110), (40, 100, 190)


def spiral(s, cx, cy, r, turns):
    import math
    s.ell(cx - r, cy - r, cx + r, cy + r, W_SHELL)
    n = int(turns * 16)
    pts = []
    for i in range(n + 1):
        t = i / n
        a = t * turns * 2 * math.pi + 0.6
        rr = (r - 2) * (1 - t)
        pts.append((int(round(cx + math.cos(a) * rr)), int(round(cy + math.sin(a) * rr))))
    s.line(pts, W_BAND)


@reg('shellkit')
def shellkit(r):
    s = Sprite()
    s.poly([(9, 24), (4, 22), (3, 26), (8, 27)], W_FIN)             # little paddle tail
    spiral(s, 12, 19, 6, 1.2)
    s.rect(9, 26, 12, 28, W_BODY); s.rect(17, 26, 20, 28, W_BODY)
    s.ell(12, 18, 22, 28, W_BODY); s.ell(15, 21, 21, 27, W_BELLY)
    s.poly([(14, 11), (13, 7), (17, 9)], W_FIN); s.poly([(24, 11), (26, 7), (21, 9)], W_FIN)   # fin ears
    s.ell(12, 8, 26, 20, W_BODY)
    s.ell(18, 14, 25, 19, W_BELLY); s.px([(21, 15), (22, 15)], DARK); s.line([(20, 17), (23, 17)], (60, 110, 170))
    cute_eye(s, 16, 12); cute_eye(s, 23, 12)
    s.px([(28, 6), (29, 9)], s.lit(FOAM))
    return s.finish()


@reg('tideshell')
def tideshell(r):
    s = Sprite()
    d = B.dims(1, x0=6, x1=21, y0=16, y1=23, lw=3, hx=23, hy=13)
    s.poly([(8, 20), (2, 15), (1, 22), (5, 24)], W_FIN)
    B.quad(s, W_BODY, d, belly=W_BELLY)
    spiral(s, 12, 14, 8, 1.6)
    s.poly([(10, 6), (12, 2), (14, 6)], W_SHELL)                    # the shell has grown a spire
    B.neck(s, d, W_BODY)
    s.poly([(19, 9), (17, 4), (22, 8)], W_FIN); s.poly([(26, 9), (28, 4), (24, 8)], W_FIN)
    s.ell(18, 7, 28, 17, W_BODY)
    s.rect(24, 12, 29, 15, W_BELLY); s.px([(29, 12)], DARK); s.line([(25, 16), (28, 16)], (60, 110, 170))
    cute_eye(s, 22, 10); s.px([(26, 10)], DARK)
    return s.finish()


@reg('torrentoise')
def torrentoise(r):
    s = Sprite()
    foam = s.lit(FOAM); wat = s.lit((130, 200, 255))
    # a spring rises from the crown of the shell and falls as rain
    s.line([(12, 6), (12, 1)], wat, 2)
    s.px([(9, 2), (8, 4), (15, 2), (17, 4), (7, 7), (18, 7), (10, 1), (14, 1)], foam)
    s.rect(4, 21, 8, 28, W_BODY); s.rect(16, 21, 20, 28, W_BODY)
    s.rect(4, 28, 9, 28, W_FIN); s.rect(16, 28, 21, 28, W_FIN)
    s.poly([(4, 22), (1, 21), (2, 25)], W_BODY)
    s.ell(3, 17, 22, 26, W_BELLY)
    spiral(s, 12, 14, 10, 2.1)
    s.rect(2, 20, 22, 22, W_BAND)                                   # shell rim
    for x, y in ((5, 8), (19, 8), (12, 4)):
        s.poly([(x - 1, y + 2), (x, y - 2), (x + 2, y + 2)], W_SHELL)
    tube(s, [(20, 20), (23, 18), (24, 15)], W_BODY, 5, 5)
    s.ell(20, 9, 30, 19, W_BODY)
    s.rect(26, 14, 30, 17, W_BELLY); s.px([(30, 14)], DARK); s.line([(26, 18), (29, 18)], (60, 110, 170))
    cute_eye(s, 24, 12); s.px([(28, 12)], DARK)
    s.poly([(21, 11), (19, 7), (24, 10)], W_FIN)
    return s.finish()


# lightning line: storm-navy fur, a blaze of yellow that spreads as it grows
L_BODY, L_BELLY, L_DARK = (64, 74, 150), (190, 200, 236), (38, 44, 100)


@reg('zappik')
def zappik(r):
    s = Sprite()
    y = s.lit(BOLT)
    s.rect(11, 26, 13, 28, L_DARK); s.rect(18, 26, 20, 28, L_DARK)
    # a ball of static fluff
    for x in range(8, 24, 3):
        s.poly([(x, 14), (x + 1, 10), (x + 3, 14)], L_BODY)
    s.poly([(8, 16), (4, 15), (7, 20)], L_BODY); s.poly([(23, 16), (27, 15), (24, 20)], L_BODY)
    s.ell(7, 12, 24, 27, L_BODY)
    s.ell(11, 19, 20, 26, L_BELLY)
    cute_eye(s, 11, 16); cute_eye(s, 19, 16)
    s.px([(15, 19), (16, 19)], y)                                   # tiny beak-nose
    # two feelers that spark at the tips
    s.line([(12, 11), (10, 6), (11, 3)], L_DARK); s.line([(19, 11), (21, 6), (20, 3)], L_DARK)
    s.rect(10, 2, 11, 3, y); s.rect(20, 2, 21, 3, y)
    s.px([(15, 3), (16, 2)], y)
    return s.finish()


@reg('voltpaw')
def voltpaw(r):
    s = Sprite()
    y = s.lit(BOLT)
    d = B.dims(1, x0=6, x1=21, y0=15, y1=22, lw=3, hx=23, hy=12)
    tube(s, [(8, 19), (3, 18), (3, 12), (6, 9)], L_BODY, 3, 2.4); s.rect(5, 7, 7, 9, y)
    B.quad(s, L_BODY, d, belly=L_BELLY)
    for x in (7, 18):
        s.rect(x, 26, x + 3, 28, y)                                 # the paws that give it its name
    s.px([(10, 17), (11, 18), (12, 17), (13, 18), (14, 17), (15, 18)], y)   # zigzag stripe
    B.neck(s, d, L_BODY)
    s.poly([(19, 9), (17, 2), (22, 7)], L_BODY); s.poly([(26, 9), (28, 2), (23, 7)], L_BODY)
    s.px([(17, 2), (18, 3), (28, 2), (27, 3)], y)
    s.ell(18, 6, 28, 16, L_BODY)
    s.rect(23, 11, 28, 14, L_BELLY); s.px([(28, 11)], DARK); s.line([(24, 15), (27, 15)], L_DARK)
    cute_eye(s, 21, 9); s.px([(26, 9)], DARK)
    return s.finish()


@reg('thundertail')
def thundertail(r):
    s = Sprite()
    y = s.lit(BOLT)
    cloud = (214, 220, 236)
    d = B.dims(2, x0=5, x1=22, y0=12, y1=21, lw=4, hx=24, hy=10)
    # the tail ends in a three-tined fork of light
    tube(s, [(7, 16), (3, 15), (2, 9), (5, 5)], L_BODY, 3.4, 2.4)
    s.line([(5, 5), (3, 1)], y, 2); s.line([(5, 5), (7, 1)], y, 2); s.line([(5, 5), (9, 4)], y, 2)
    B.quad(s, L_BODY, d, belly=L_BELLY)
    for x in (6, 18):
        s.rect(x, 25, x + 4, 28, y)
    s.px([(9, 14), (10, 15), (11, 14), (12, 15), (13, 14), (14, 15), (9, 17), (10, 18), (11, 17), (12, 18)], y)
    B.neck(s, d, L_BODY)
    # a storm-cloud mane
    for x, yy in ((14, 6), (17, 3), (15, 11), (19, 13), (21, 2)):
        s.ell(x, yy, x + 5, yy + 5, cloud)
    s.poly([(21, 7), (20, 1), (24, 5)], L_BODY); s.poly([(27, 7), (29, 1), (25, 5)], L_BODY)
    s.px([(20, 1), (29, 1)], y)
    s.ell(19, 4, 29, 15, L_BODY)
    s.rect(25, 10, 30, 13, L_BELLY); s.px([(30, 10)], DARK); s.line([(26, 14), (29, 14)], L_DARK)
    s.px([(27, 15)], IVORY)
    cute_eye(s, 22, 8, c=(30, 30, 60)); s.px([(27, 8)], DARK)
    bolt(s, 29, 19, BOLT)
    return s.finish()


# ------------------------------------------------------------------ the other companions
@reg('ethereal_unicorn')
def ethereal_unicorn(r):
    s = Sprite()
    s.shadow = False
    c = (240, 240, 250)
    mane = (190, 160, 250)
    glow = s.lit((255, 244, 170))
    d = B.dims(1, x0=6, x1=20, y0=14, y1=21, lw=2, hx=23, hy=9)
    tube(s, [(7, 17), (3, 19), (3, 26)], mane, 3.4, 2)
    B.quad(s, c, d, feet=(170, 180, 230))
    tube(s, [(18, 17), (20, 13), (22, 10)], c, 5, 4)
    s.poly([(16, 15), (18, 9), (21, 6), (20, 12), (18, 17)], mane)
    s.ell(19, 5, 25, 11, c); s.poly([(23, 8), (28, 12), (26, 14), (22, 11)], c)
    s.px([(27, 13)], (200, 160, 190)); s.px([(23, 8)], (90, 110, 200))
    s.poly([(21, 6), (20, 3), (23, 5)], c)
    s.line([(24, 5), (28, 0)], glow, 2)                             # the horn
    s.px([(29, 3), (26, 1), (30, 6), (2, 10), (12, 9), (9, 28), (22, 27)], glow)
    im = s.finish()
    px = im.load()
    for y in range(22, 32):
        for x in range(32):
            r_, g, b, a = px[x, y]
            if a:
                px[x, y] = (r_, g, b, int(a * max(0.25, 1 - (y - 21) / 9)))
    return im


@reg('dad')
def dad(r):
    s = Sprite()
    polo, khaki, hair = (60, 150, 110), (200, 180, 130), (110, 76, 50)
    # white trainers and socks
    s.rect(12, 26, 14, 27, WHITE); s.rect(17, 26, 19, 27, WHITE)
    s.rect(11, 28, 14, 29, (236, 236, 240)); s.rect(17, 28, 20, 29, (236, 236, 240))
    s.rect(12, 24, 14, 25, SKIN); s.rect(17, 24, 19, 25, SKIN)
    s.rect(11, 20, 20, 24, khaki); s.rect(15, 22, 16, 24, sh(khaki, -2))
    s.line([(11, 20), (20, 20)], LEATHER)
    # polo shirt with a collar and two buttons
    s.rect(10, 12, 21, 20, polo)
    s.poly([(13, 12), (15, 15), (16, 15), (18, 12)], WHITE); s.px([(15, 16), (15, 18)], WHITE)
    s.rect(7, 13, 9, 16, polo); s.rect(7, 17, 9, 21, SKIN)
    # the other arm is up, giving a thumbs-up
    s.rect(22, 12, 24, 15, polo); s.rect(23, 8, 25, 12, SKIN); s.rect(23, 5, 24, 7, SKIN)
    # mug in the near hand
    s.rect(4, 19, 7, 22, (226, 226, 230)); s.px([(3, 20), (3, 21)], (226, 226, 230)); s.px([(5, 18), (6, 17)], (200, 200, 210))
    # head: tidy hair, glasses, moustache, a big smile
    s.ell(11, 2, 20, 12, SKIN)
    s.poly([(11, 6), (11, 3), (14, 1), (18, 1), (20, 3), (20, 6), (18, 4), (13, 4)], hair)
    s.rect(12, 6, 14, 7, (60, 70, 90)); s.rect(17, 6, 19, 7, (60, 70, 90)); s.px([(15, 6), (16, 6)], (60, 70, 90))
    s.px([(13, 6), (18, 6)], WHITE)
    s.rect(13, 9, 18, 9, hair)
    s.line([(14, 10), (17, 10)], WHITE)
    return s.finish()


@reg('deadite')
def deadite(r):
    s = Sprite()
    skin, rag, hair = (176, 196, 170), (120, 96, 110), (70, 60, 76)
    eye = s.lit((250, 250, 255))
    s.rect(12, 22, 14, 27, rag); s.rect(17, 22, 19, 27, rag)
    s.rect(11, 28, 14, 29, skin); s.rect(17, 28, 20, 29, skin)
    s.poly([(10, 12), (21, 12), (22, 23), (19, 21), (16, 24), (13, 21), (9, 23)], rag)
    s.line([(13, 14), (15, 18)], sh(rag, -2)); s.px([(18, 16), (19, 17)], sh(rag, -2))
    # one arm waving hello
    s.rect(6, 13, 9, 15, rag); s.rect(4, 8, 6, 14, skin); s.px([(3, 7), (5, 6), (7, 7)], skin)
    s.rect(22, 13, 24, 19, rag); s.rect(22, 20, 24, 22, skin)
    s.ell(10, 2, 21, 13, skin)
    s.poly([(10, 6), (11, 2), (15, 0), (19, 1), (21, 5), (18, 4), (15, 5), (12, 4)], hair)
    s.rect(12, 6, 14, 8, eye); s.rect(17, 6, 19, 8, eye)
    s.line([(12, 5), (14, 5)], hair); s.line([(17, 5), (19, 5)], hair)
    # a wide, crooked, pleased-to-see-you grin
    s.rect(12, 10, 19, 11, (60, 40, 60)); s.px([(13, 10), (15, 10), (17, 10), (14, 11), (18, 11)], IVORY)
    s.px([(11, 9), (20, 9)], (130, 150, 130))
    return s.finish()
