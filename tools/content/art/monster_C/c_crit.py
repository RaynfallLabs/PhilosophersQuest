"""Spiders, beetles, crawlers, frogs, birds and the odd beasts that fit no four-legged rig."""
from c_base import *  # noqa: F401,F403
import c_beast as B


def fade(im, x0, x1, a=120, step=None):
    """Make a vertical band half-there (phasing, ghosts)."""
    px = im.load()
    for y in range(32):
        for x in range(max(0, x0), min(32, x1 + 1)):
            r, g, b, al = px[x, y]
            if al:
                px[x, y] = (r, g, b, min(al, a))
    return im


def generic_beast(r):
    s = Sprite()
    c = vivid(tup(r.get('color')))
    B.canine(s, c, 1, belly=sh(c, 1))
    return s.finish()


# ------------------------------------------------------------------ spiders
SP_LEGS = [[(12, 20), (7, 9), (3, 13)], [(11, 21), (4, 15), (2, 21)],
           [(11, 22), (4, 21), (3, 27)], [(12, 24), (8, 25), (7, 29)]]


def spider(s, c, abd, eye, k=1.0, legc=None, mark=None, markc=None, fang=IVORY, w=1, hairy=False):
    legc = legc or sh(c, -1)

    def P(x, y):
        return (int(round(max(1, min(30, 15.5 + (x - 15.5) * k)))), int(round(max(1, min(29, 19 + (y - 19) * k)))))
    for leg in SP_LEGS:
        s.line([P(*p) for p in leg], legc, w)
        s.line([P(31 - x, y) for x, y in leg], legc, w)
    a0, a1 = P(9, 5), P(22, 18)
    s.ell(a0[0], a0[1], a1[0], a1[1], abd)
    h0, h1 = P(11, 16), P(20, 25)
    s.ell(h0[0], h0[1], h1[0], h1[1], c)
    if hairy:
        for x in range(a0[0] + 2, a1[0] - 1, 3):
            s.px([(x, a0[1] - 1)], abd)
    if mark == 'stripe':
        for y in (8, 11, 14):
            p0, p1 = P(11, y), P(20, y)
            s.line([p0, p1], markc)
    elif mark == 'hourglass':
        s.poly([P(13, 8), P(18, 8), P(13, 14), P(18, 14)], markc)
    elif mark == 'star':
        cx, cy = P(15.5, 11)
        s.px([(cx, cy - 2), (cx, cy + 2), (cx - 2, cy), (cx + 2, cy), (cx, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1), (cx - 1, cy)], markc)
    elif mark == 'bands':
        for y in (7, 10, 13, 16):
            p0, p1 = P(10, y), P(21, y)
            s.rect(p0[0] + 1, p0[1], p1[0] - 1, p0[1], markc)
    elif mark == 'skull':
        p0, p1 = P(12, 8), P(19, 14)
        s.ell(p0[0], p0[1], p1[0], p1[1], markc)
        s.px([P(14, 11), P(17, 11)], abd)
    e = [P(13, 21), P(15, 20), P(17, 20), P(18, 21)]
    s.px(e, eye)
    s.px([P(14, 26), P(17, 26)], fang)
    return P


@reg('cave_spider')
def cave_spider(r):
    s = Sprite()
    spider(s, (130, 90, 50), (100, 66, 40), s.lit((255, 210, 80)), k=0.7, mark='stripe', markc=(170, 130, 80))
    return s.finish()


@reg('web_spinner')
def web_spinner(r):
    s = Sprite()
    web = (200, 204, 210)
    for a, b in (((1, 2), (30, 30)), ((30, 2), (1, 30)), ((15, 1), (15, 30)), ((1, 16), (30, 16))):
        s.line([a, b], web)
    for rr in (6, 11):
        s.line([(15 - rr, 16), (15, 16 - rr), (15 + rr, 16), (15, 16 + rr), (15 - rr, 16)], web)
    s.outline = False; s.shadow = False
    im = s.finish()
    s2 = Sprite(); s2.shadow = False
    spider(s2, (226, 214, 160), (244, 236, 196), DARK, k=0.66, legc=(150, 130, 90), mark='hourglass', markc=(200, 120, 70))
    from PIL import Image
    return Image.alpha_composite(im, s2.finish())


@reg('giant_spider')
def giant_spider(r):
    s = Sprite()
    spider(s, (96, 72, 96), (70, 52, 76), s.lit((255, 60, 50)), k=1.0, w=2, mark='hourglass', markc=(190, 50, 50),
           hairy=True, legc=(56, 42, 60))
    return s.finish()


@reg('phase_spider_lesser')
def phase_spider_lesser(r):
    s = Sprite()
    glow = s.lit((230, 180, 255))
    spider(s, (170, 110, 230), (140, 90, 210), glow, k=0.72, mark='star', markc=glow, legc=(120, 80, 190))
    s.shadow = False
    return fade(s.finish(), 0, 12, 90)


@reg('phase_spider')
def phase_spider(r):
    s = Sprite()
    glow = s.lit((200, 240, 255))
    spider(s, (120, 150, 220), (150, 180, 240), glow, k=1.0, mark='bands', markc=(70, 80, 170), legc=(80, 100, 180), w=2)
    s.px([(2, 4), (28, 6), (29, 26), (1, 24)], glow)
    return fade(s.finish(), 20, 31, 110)


@reg('phase_spider_matriarch')
def phase_spider_matriarch(r):
    s = Sprite()
    glow = s.lit((255, 150, 255))
    P = spider(s, (110, 50, 150), (150, 70, 190), glow, k=1.08, mark='star', markc=glow, legc=(70, 34, 110), w=2)
    # a crown of spines and the rift she steps through
    for x in (11, 14, 17, 20):
        s.poly([(x - 1, 5), (x, 1), (x + 1, 5)], (70, 34, 110))
    s.px([(1, 2), (2, 3), (30, 3), (29, 2), (1, 28), (30, 27)], glow)
    return fade(s.finish(), 0, 6, 120)


@reg('spider_queen')
def spider_queen(r):
    s = Sprite()
    eye = s.lit((255, 220, 90))
    spider(s, (130, 30, 120), (170, 40, 150), eye, k=1.0, mark='hourglass', markc=(250, 200, 80), legc=(84, 20, 90), w=2)
    s.rect(12, 14, 19, 16, GOLD); s.px([(12, 13), (14, 12), (17, 12), (19, 13)], GOLD)    # crown
    s.px([(15, 15), (16, 15)], s.lit((90, 230, 160)))
    # egg sacs at her feet
    s.ell(1, 25, 5, 29, (230, 226, 210)); s.ell(26, 25, 30, 29, (230, 226, 210))
    return s.finish()


@reg('arachne')
def arachne(r):
    s = Sprite()
    c, abd = (150, 110, 70), (120, 84, 56)
    legc = (86, 60, 44)
    for leg in ([(12, 21), (6, 13), (2, 17)], [(11, 22), (4, 19), (2, 25)], [(11, 24), (5, 24), (4, 29)], [(13, 25), (9, 27), (9, 29)]):
        s.line(leg, legc, 2); s.line([(31 - x, y) for x, y in leg], legc, 2)
    s.ell(8, 17, 23, 28, abd)
    s.poly([(13, 20), (18, 20), (13, 26), (18, 26)], (200, 170, 90))
    # the weaver's body rises from the spider's
    tunic = (170, 60, 110)
    s.rect(12, 11, 19, 20, tunic); s.line([(12, 17), (19, 17)], GOLD)
    s.rect(9, 12, 11, 17, SKIN); s.rect(20, 12, 22, 17, SKIN)
    s.ell(10, 1, 21, 11, (60, 40, 50))                          # hair
    s.ell(12, 3, 19, 11, SKIN)
    s.rect(10, 6, 11, 13, (60, 40, 50)); s.rect(20, 6, 21, 13, (60, 40, 50))
    s.px([(14, 7), (17, 7)], s.lit((200, 240, 120))); s.line([(15, 9), (16, 9)], (150, 70, 70))
    # a thread held taut between her hands
    silk = s.lit((240, 240, 250))
    s.line([(9, 18), (5, 10), (2, 3)], silk); s.line([(22, 18), (26, 10), (29, 3)], silk)
    s.line([(10, 18), (21, 18)], silk)
    return s.finish()


# ------------------------------------------------------------------ beetles
def beetle(s, shell, head, eye, x0=5, x1=23, y0=11, y1=25, legc=DARK, seam=True):
    for (a, b, c2) in (((x0 + 4, y1 - 1), (x0 + 1, y1 + 1), (x0 + 1, 28)), (((x0 + x1) // 2, y1), ((x0 + x1) // 2 + 1, y1 + 2), ((x0 + x1) // 2, 28)),
                       ((x1 - 2, y1 - 1), (x1 + 2, y1 + 1), (x1 + 3, 28))):
        s.line([a, b, c2], legc, 2)
    s.ell(x1 - 6, y0 + 4, x1 + 2, y1 - 1, head)                 # thorax
    s.ell(x1 - 1, y0 + 7, x1 + 5, y1 - 2, sh(head, -1))         # head
    s.ell(x0, y0, x1 - 2, y1, shell)
    if seam:
        s.line([(x0 + 3, y0 + 4), (x1 - 6, y0 + 3)], sh(shell, 1))
        s.line([(x1 - 4, y0 + 3), (x1 - 3, y1 - 2)], sh(shell, -2))
    s.px([(x1 + 3, y0 + 9)], eye)


@reg('giant_beetle')
def giant_beetle(r):
    s = Sprite()
    beetle(s, (60, 90, 200), (40, 56, 130), s.lit((255, 220, 80)))
    s.line([(26, 20), (29, 16), (29, 11)], (40, 56, 130), 2)    # rhinoceros horn
    s.px([(28, 10), (30, 10)], (40, 56, 130))
    s.px([(9, 14), (10, 13), (11, 13)], (150, 190, 255))
    return s.finish()


@reg('fire_beetle')
def fire_beetle(r):
    s = Sprite()
    glow = s.lit((255, 150, 40)); hot = s.lit((255, 230, 120))
    beetle(s, (110, 46, 36), (70, 34, 34), s.lit((255, 230, 120)), y0=13)
    s.ell(17, 16, 21, 20, glow); s.px([(19, 18)], hot)          # the light glands behind the eyes
    s.ell(7, 19, 11, 23, glow); s.px([(9, 21)], hot)
    s.line([(27, 21), (30, 19)], (70, 34, 34)); s.line([(27, 23), (30, 24)], (70, 34, 34))
    return s.finish()


@reg('death_beetle')
def death_beetle(r):
    s = Sprite()
    c = (52, 48, 64)
    beetle(s, c, (36, 32, 46), s.lit((190, 110, 255)), y0=10, seam=False)
    # the pale death's-head on its back
    s.ell(8, 13, 16, 20, BONE); s.rect(10, 20, 14, 22, BONE)
    s.px([(10, 16), (11, 16), (13, 16), (14, 16), (12, 19)], c); s.px([(11, 22), (13, 22)], c)
    s.line([(27, 20), (30, 17)], (36, 32, 46), 2); s.line([(27, 23), (30, 25)], (36, 32, 46), 2)
    return s.finish()


@reg('khepri_beetle')
def khepri_beetle(r):
    s = Sprite()
    sun = s.lit((255, 200, 60)); hot = s.lit((255, 244, 170))
    s.ell(18, 8, 30, 20, sun); s.ell(21, 10, 26, 15, hot)       # the sun it rolls across the sky
    beetle(s, (60, 180, 130), (30, 110, 100), s.lit((255, 240, 150)), x0=2, x1=17, y0=15, y1=26)
    s.line([(18, 21), (21, 19)], DARK, 2)
    s.px([(5, 18), (6, 17), (7, 17)], (170, 240, 200))
    return s.finish()


@reg('scarab_swarm')
def scarab_swarm(r):
    s = Sprite()
    cols = [(60, 150, 90), (50, 120, 110), (90, 160, 70)]
    for i, (x, y) in enumerate([(4, 8), (16, 5), (23, 12), (9, 16), (18, 19), (3, 23), (13, 25), (24, 24)]):
        c = cols[i % 3]
        s.px([(x - 1, y + 1), (x - 1, y + 3), (x + 5, y + 1), (x + 5, y + 3), (x + 1, y - 1), (x + 3, y - 1)], DARK)
        s.ell(x, y, x + 4, y + 4, c)
        s.px([(x + 2, y + 1), (x + 2, y + 2), (x + 2, y + 3)], sh(c, -2))
        s.px([(x + 1, y)], sh(c, 2))
    return s.finish()


# ------------------------------------------------------------------ long crawlers
def crawler(s, pts, c, w, legc, seg=None, legs=True, n=6):
    sp = smooth(pts, n)
    if legs:
        for i, (x, y) in enumerate(sp):
            if i % 3 == 0:
                xi, yi = int(round(x)), int(round(y + w / 2))
                s.px([(xi, yi + 1), (xi - 1, yi + 2)], legc)
    for i, (x, y) in enumerate(sp):
        col = c if (i // 3) % 2 == 0 else (seg or sh(c, -1))
        rr = w / 2
        s.ell(int(round(x - rr)), int(round(y - rr)), int(round(x + rr)), int(round(y + rr)), col)
    return sp


@reg('giant_centipede')
def giant_centipede(r):
    s = Sprite()
    c = (190, 110, 40)
    crawler(s, [(3, 25), (9, 21), (15, 25), (21, 21), (23, 13), (18, 9)], c, 4, (240, 200, 80), seg=(140, 70, 30))
    s.ell(15, 5, 21, 11, (190, 50, 40))
    s.line([(16, 11), (14, 14), (16, 15)], IVORY); s.line([(20, 11), (22, 14), (20, 15)], IVORY)   # venom claws
    s.line([(16, 5), (13, 2)], DARK); s.line([(20, 5), (23, 2)], DARK)
    s.px([(17, 7), (19, 7)], s.lit((255, 230, 80)))
    return s.finish()


@reg('frost_crawler')
def frost_crawler(r):
    s = Sprite()
    c = (150, 200, 236)
    ice = s.lit((230, 250, 255))
    sp = crawler(s, [(2, 24), (8, 19), (14, 24), (21, 20), (25, 12), (20, 7)], c, 5, (90, 130, 190), seg=(110, 160, 214))
    for i, (x, y) in enumerate(sp):
        if i % 6 == 2 and i < len(sp) - 6:
            s.px([(int(x), int(y - 3)), (int(x), int(y - 4))], ice)   # ice-rimed spines
    s.ell(16, 3, 24, 10, (70, 104, 170))
    s.line([(17, 10), (15, 14)], (236, 246, 255), 2); s.line([(23, 10), (25, 14)], (236, 246, 255), 2)
    s.line([(17, 3), (14, 1)], (70, 104, 170)); s.line([(23, 3), (26, 1)], (70, 104, 170))
    s.rect(18, 6, 19, 7, ice); s.rect(21, 6, 22, 7, ice)
    s.px([(27, 16), (29, 18), (28, 21)], ice)
    return s.finish()


@reg('carrion_crawler')
def carrion_crawler(r):
    s = Sprite()
    c = (170, 196, 100)
    crawler(s, [(3, 24), (9, 22), (15, 24), (20, 20), (22, 13)], c, 7, (110, 130, 60), seg=(140, 170, 80))
    s.ell(18, 7, 26, 15, (120, 150, 70))
    t = (226, 150, 160)
    for pts in ([(22, 14), (20, 19), (22, 22)], [(24, 14), (25, 19), (23, 23)], [(25, 13), (28, 17), (28, 21)],
                [(26, 11), (30, 13), (30, 17)]):
        s.line(pts, t)
    s.px([(21, 10), (24, 10)], s.lit((255, 240, 120)))
    s.line([(19, 7), (17, 4)], (110, 130, 60)); s.line([(24, 7), (26, 4)], (110, 130, 60))
    return s.finish()


@reg('grick')
def grick(r):
    s = Sprite()
    c = (104, 124, 104)
    rock = (86, 80, 90)
    tube(s, [(8, 27), (8, 22), (14, 20), (17, 14), (15, 9)], c, 7, 5, bands=((74, 92, 80), 5, 1))
    s.poly([(1, 30), (3, 24), (8, 23), (12, 26), (16, 30)], rock)    # the crack it wedges in
    t = (140, 160, 130)
    for pts in ([(14, 8), (10, 4), (6, 5)], [(16, 7), (15, 2), (11, 1)], [(18, 8), (22, 3), (26, 4)], [(18, 10), (24, 9), (27, 12)]):
        s.line(pts, t, 2)
    s.px([(6, 5), (11, 1), (26, 4), (27, 12)], IVORY)
    s.poly([(16, 9), (22, 12), (17, 13)], (226, 190, 80))       # snapping beak
    s.px([(14, 10)], s.lit((255, 230, 100)))
    return s.finish()


@reg('rot_grub_swarm')
def rot_grub_swarm(r):
    s = Sprite()
    c, seg = (240, 232, 200), (206, 190, 150)
    s.ell(3, 20, 28, 29, (104, 80, 62))                         # the rot they boil out of
    s.px([(7, 24), (22, 26), (15, 27)], (70, 54, 46))
    grubs = [[(4, 23), (8, 19), (13, 22)], [(12, 26), (17, 23), (22, 26)], [(17, 18), (21, 14), (26, 17)],
             [(9, 15), (12, 11), (16, 14)]]
    for g in grubs:
        crawler(s, g, c, 4, seg, seg=seg, legs=False, n=5)
        hx, hy = g[-1]
        s.rect(hx, hy - 1, hx + 1, hy, (160, 84, 50))
    return s.finish()


# ------------------------------------------------------------------ frogs
def frog(s, c, belly, eye, wide=0, warts=None):
    w = wide
    s.ell(4 - w, 17, 14, 28, sh(c, -1))                         # folded hind leg
    s.rect(5 - w, 27, 12, 28, c); s.px([(13, 28), (14, 28)], c)
    s.ell(7 - w, 12, 25 + w, 26, c)
    s.ell(13, 19, 25 + w, 26, belly)
    s.rect(19, 22, 21, 28, c); s.rect(19, 28, 24, 28, c)        # front leg
    s.ell(15, 8, 20, 13, c); s.ell(21, 9, 26, 14, c)            # eye bumps
    s.rect(17, 10, 18, 11, eye); s.rect(23, 11, 24, 12, eye); s.px([(18, 11), (24, 12)], DARK)
    s.line([(16, 18), (26 + w, 17)], sh(c, -2))
    if warts:
        s.px([(9, 15), (11, 18), (13, 14), (8, 20), (15, 16)], warts)


@reg('giant_frog')
def giant_frog(r):
    s = Sprite()
    frog(s, (60, 180, 100), (220, 236, 170), s.lit((255, 220, 70)))
    s.line([(26, 18), (29, 16), (30, 13)], PINK, 2)             # the tongue, mid-flick
    s.px([(30, 12)], (200, 80, 100))
    s.px([(10, 14), (12, 16), (9, 18)], (40, 130, 80))
    return s.finish()


@reg('cave_toad')
def cave_toad(r):
    s = Sprite()
    c = (120, 110, 70)
    frog(s, c, (196, 186, 140), s.lit((255, 140, 50)), wide=2, warts=(80, 70, 50))
    s.ell(10, 10, 15, 14, (160, 150, 90))                       # poison gland behind the eye
    s.px([(11, 14), (12, 15)], s.lit((240, 244, 220)))
    return s.finish()


# ------------------------------------------------------------------ scorpion, mantis, wasp
@reg('giant_scorpion')
def giant_scorpion(r):
    s = Sprite()
    c, dk = (190, 146, 70), (130, 90, 44)
    for x in (9, 12, 15, 18):
        s.line([(x, 23), (x - 2, 26), (x - 2, 28)], dk)
    tube(s, [(8, 21), (3, 17), (4, 9), (10, 5), (15, 8)], c, 4, 3, bands=(dk, 5, 1))
    s.poly([(14, 7), (18, 9), (15, 11), (16, 13)], (70, 40, 40)); s.px([(16, 13), (16, 14)], s.lit(VENOM))
    s.ell(6, 18, 22, 25, c)
    for x in (10, 14, 18):
        s.line([(x, 19), (x, 24)], dk)
    s.line([(21, 21), (25, 18)], c, 2); s.line([(21, 23), (25, 25)], c, 2)
    s.poly([(24, 15), (29, 13), (30, 16), (27, 17), (30, 19), (25, 20)], c)     # pincers
    s.poly([(24, 23), (29, 22), (30, 25), (27, 25), (29, 28), (24, 27)], c)
    s.px([(21, 19), (19, 19)], s.lit((255, 80, 60)))
    return s.finish()


@reg('giant_mantis')
def giant_mantis(r):
    s = Sprite()
    c, dk = (70, 180, 90), (40, 120, 70)
    s.line([(13, 20), (10, 25), (9, 29)], dk); s.line([(15, 20), (17, 25), (19, 29)], dk)
    s.line([(11, 21), (5, 25), (4, 29)], dk)
    s.poly([(3, 22), (5, 18), (14, 17), (16, 21), (8, 24)], c)   # abdomen
    s.poly([(4, 21), (12, 16), (14, 18), (6, 22)], (150, 220, 130))   # wing cover
    tube(s, [(14, 19), (17, 14), (19, 8)], c, 3.4, 3)            # upright thorax
    s.poly([(17, 3), (24, 3), (21, 9)], c)                       # triangular head
    s.rect(16, 3, 18, 5, s.lit((255, 230, 90))); s.rect(23, 3, 25, 5, s.lit((255, 230, 90)))
    s.line([(18, 3), (16, 1)], dk); s.line([(23, 3), (25, 1)], dk)
    # the praying arms
    s.line([(19, 11), (25, 9), (27, 13)], c, 2); s.line([(27, 13), (23, 16)], dk, 2)
    s.px([(26, 14), (25, 15), (24, 16)], IVORY)
    s.line([(18, 13), (22, 14), (24, 19)], c, 2); s.line([(24, 19), (20, 21)], dk, 2)
    return s.finish()


@reg('giant_wasp')
def giant_wasp(r):
    s = Sprite()
    y, k = (244, 200, 30), (40, 34, 40)
    wingc = (200, 226, 244)
    s.poly([(14, 11), (8, 2), (3, 3), (5, 9)], wingc); s.poly([(16, 10), (17, 1), (22, 2), (21, 8)], wingc)
    s.line([(14, 11), (6, 4)], (150, 180, 210)); s.line([(16, 10), (19, 3)], (150, 180, 210))
    sp = smooth([(12, 15), (7, 18), (5, 24)], 6)                 # striped abdomen
    for i, (ax, ay) in enumerate(sp):
        w = 7 - 4 * i / len(sp)
        s.ell(int(round(ax - w / 2)), int(round(ay - w / 2)), int(round(ax + w / 2)), int(round(ay + w / 2)), y if (i // 2) % 2 == 0 else k)
    s.line([(4, 25), (5, 28)], k); s.px([(5, 29)], s.lit(VENOM))
    s.ell(12, 10, 20, 18, k); s.px([(14, 12), (15, 12)], y)
    s.ell(19, 9, 26, 16, y)
    s.rect(22, 10, 25, 13, k); s.px([(23, 11)], s.lit((255, 90, 60)))
    s.line([(22, 9), (24, 5), (27, 4)], k); s.line([(25, 15), (27, 17)], k)
    for x in (14, 16, 18):
        s.line([(x, 18), (x + 1, 22), (x - 1, 24)], k)
    return s.finish()


# ------------------------------------------------------------------ flyers, seen front-on with wings spread
def spread(s, c, wingc, k=1.0, cy=14, feather=True, tipc=None):
    """Wings, body and tail. Returns nothing; the caller adds the head."""
    def P(x, y):
        return (int(round(max(1, min(30, 15.5 + (x - 15.5) * k)))), int(round(max(1, min(30, cy + (y - 14) * k)))))
    L = [(13, 13), (9, 6), (3, 3), (1, 8), (3, 9), (2, 13), (5, 13), (4, 17), (8, 16), (12, 19)]
    if not feather:
        L = [(13, 13), (9, 5), (3, 2), (1, 9), (4, 8), (5, 14), (8, 11), (9, 17), (12, 14)]
    for pts in (L, [(31 - x, y) for x, y in L]):
        s.poly([P(*p) for p in pts], wingc)
    if feather:
        t = tipc or sh(wingc, -1)
        for pts in ([(9, 8), (4, 6)], [(9, 11), (5, 11)], [(10, 14), (7, 14)]):
            s.line([P(*p) for p in pts], t); s.line([P(31 - x, y) for x, y in pts], t)
        s.poly([P(13, 20), P(11, 26), P(15, 24), P(16, 24), P(20, 26), P(18, 20)], wingc)
    else:
        t = tipc or sh(wingc, 1)
        for pts in ([(12, 13), (3, 2)], [(12, 13), (5, 13)], [(12, 13), (9, 17)]):
            s.line([P(*p) for p in pts], t); s.line([P(31 - x, y) for x, y in pts], t)
    a, b = P(12, 10), P(19, 22)
    s.ell(a[0], a[1], b[0], b[1], c)
    return P


@reg('bat')
def bat(r):
    s = Sprite()
    c = (120, 84, 150)
    spread(s, c, (84, 56, 110), k=0.95, cy=13, feather=False, tipc=(150, 110, 180))
    s.poly([(11, 8), (11, 3), (14, 7)], c); s.poly([(20, 8), (20, 3), (17, 7)], c)
    s.ell(11, 6, 20, 14, c)
    s.px([(13, 9), (18, 9)], s.lit((255, 90, 70)))
    s.px([(14, 12), (17, 12)], IVORY); s.px([(15, 11), (16, 11)], (60, 30, 60))
    s.px([(14, 22), (17, 22)], DARK)
    return s.finish()


@reg('giant_eagle')
def giant_eagle(r):
    s = Sprite()
    c = (150, 104, 56)
    spread(s, c, (176, 130, 66), k=1.0, cy=14, tipc=(100, 66, 40))
    s.ell(12, 5, 19, 12, WHITE)
    s.poly([(16, 8), (21, 9), (18, 12), (16, 11)], GOLD)
    s.px([(14, 8), (17, 7)], DARK)
    s.px([(13, 23), (14, 24), (17, 24), (18, 23)], GOLD)
    return s.finish()


@reg('roc_adult')
def roc_adult(r):
    s = Sprite()
    c = (236, 204, 130)
    P = spread(s, c, (214, 160, 80), k=1.07, cy=12, tipc=(150, 100, 50))
    s.poly([(12, 4), (11, 1), (15, 3)], (214, 160, 80))
    s.ell(12, 2, 19, 9, (250, 244, 226))
    s.poly([(16, 5), (21, 6), (18, 9), (16, 8)], (240, 150, 40))
    s.px([(14, 5), (17, 4)], DARK)
    # the boulder it carries to drop on ships
    s.line([(13, 22), (12, 24)], GOLD, 2); s.line([(18, 22), (19, 24)], GOLD, 2)
    s.ell(9, 23, 22, 30, (128, 120, 124)); s.px([(13, 26), (17, 28), (19, 25)], (90, 84, 92))
    return s.finish()


@reg('thunderbird_lesser')
def thunderbird_lesser(r):
    s = Sprite()
    c = (70, 80, 170)
    b = s.lit(BOLT)
    spread(s, c, (110, 130, 230), k=1.0, cy=13, tipc=(190, 210, 255))
    s.ell(12, 4, 19, 11, c)
    s.poly([(16, 7), (21, 9), (17, 11)], (250, 200, 60))
    s.poly([(12, 5), (11, 1), (15, 4)], (190, 210, 255))        # crest
    s.px([(14, 7), (17, 6)], b)
    # lightning falls from its wings
    s.px([(4, 17), (5, 18), (4, 19), (3, 20), (4, 21), (5, 22), (4, 23)], b)
    s.px([(27, 17), (26, 18), (27, 19), (28, 20), (27, 21), (26, 22), (27, 23)], b)
    s.px([(15, 24), (16, 25), (15, 26)], b)
    return s.finish()


@reg('anzu_bird')
def anzu_bird(r):
    s = Sprite()
    c = (206, 160, 60)
    spread(s, c, (170, 110, 44), k=1.0, cy=15, tipc=(240, 210, 120))
    # the lion's head
    s.ell(9, 2, 22, 15, (130, 76, 36))
    s.poly([(12, 5), (12, 2), (14, 4)], c); s.poly([(19, 5), (19, 2), (17, 4)], c)
    s.ell(11, 4, 20, 13, c)
    s.rect(14, 9, 17, 12, (240, 214, 150)); s.px([(15, 9), (16, 9)], (140, 70, 70))
    s.line([(14, 12), (17, 12)], (120, 30, 40)); s.px([(14, 12), (17, 12)], IVORY)
    s.px([(13, 7), (18, 7)], s.lit((120, 220, 255)))
    s.px([(13, 25), (14, 26), (17, 26), (18, 25)], GOLD)
    return s.finish()


@reg('stirge_swarm')
def stirge_swarm(r):
    s = Sprite()
    c, wc = (196, 70, 70), (230, 150, 140)
    for (x, y) in ((3, 5), (17, 3), (9, 15), (20, 17)):
        s.poly([(x + 2, y + 3), (x - 1, y - 1), (x - 2, y + 3)], wc)
        s.poly([(x + 5, y + 3), (x + 8, y - 1), (x + 9, y + 3)], wc)
        s.ell(x + 1, y + 1, x + 6, y + 6, c)
        s.line([(x + 4, y + 6), (x + 5, y + 10)], (90, 40, 50))  # the long sucking beak
        s.px([(x + 2, y + 3), (x + 5, y + 3)], s.lit((255, 230, 100)))
    return s.finish()


# ------------------------------------------------------------------ standing birds
def perched(s, c, wingc, d=0, tail=None):
    """Side-on bird facing right. d shifts it down for small birds."""
    s.poly([(10, 17 + d), (3, 22 + d), (4, 25 + d), (11, 22 + d)], tail or wingc)
    s.line([(14, 23 + d), (14, 28)], GOLD); s.line([(17, 23 + d), (17, 28)], GOLD)
    s.line([(13, 28), (16, 28)], GOLD); s.line([(17, 28), (20, 28)], GOLD)
    s.ell(8, 12 + d, 21, 24 + d, c)
    s.poly([(9, 15 + d), (17, 14 + d), (15, 21 + d), (7, 22 + d)], wingc)


@reg('hugin_raven')
def hugin_raven(r):
    s = Sprite()
    c = (50, 50, 70)
    perched(s, c, (34, 34, 52), d=2)
    s.ell(16, 9, 24, 17, c)
    s.poly([(23, 11), (29, 13), (23, 15)], (30, 28, 36))
    s.px([(21, 12)], s.lit((150, 220, 255)))                    # Odin's eye looks out of it
    s.px([(11, 18), (12, 17), (13, 19)], (90, 96, 140))
    return s.finish()


@reg('roc_chick')
def roc_chick(r):
    s = Sprite()
    c = (226, 196, 120)
    shell = (240, 236, 222)
    s.line([(13, 24), (13, 28)], GOLD, 2); s.line([(18, 24), (18, 28)], GOLD, 2)
    s.rect(12, 28, 15, 28, GOLD); s.rect(18, 28, 21, 28, GOLD)
    s.ell(7, 12, 23, 26, c)                                     # one big ball of down
    s.poly([(7, 18), (4, 15), (5, 21)], (200, 160, 80)); s.poly([(23, 18), (27, 16), (25, 22)], (200, 160, 80))
    s.ell(10, 4, 21, 15, c)
    s.px([(12, 3), (15, 2), (18, 3)], c)
    s.poly([(18, 9), (25, 10), (19, 13)], (240, 150, 40))
    s.rect(13, 8, 14, 9, DARK); s.px([(13, 8)], WHITE)
    # still wearing a piece of the great egg
    s.poly([(1, 29), (2, 23), (4, 26), (6, 23), (8, 29)], shell)
    s.poly([(24, 29), (26, 24), (28, 27), (30, 25), (30, 29)], shell)
    return s.finish()


@reg('stymphalian_bird')
def stymphalian_bird(r):
    s = Sprite()
    c, br = (176, 130, 60), (226, 170, 70)
    steel = s.lit((250, 226, 150))
    s.line([(13, 22), (12, 28)], br); s.line([(17, 22), (18, 28)], br)
    s.line([(11, 28), (14, 28)], br); s.line([(17, 28), (20, 28)], br)
    s.poly([(9, 16), (2, 20), (3, 23), (10, 21)], br)
    s.ell(8, 13, 20, 23, c)
    s.poly([(9, 15), (18, 14), (15, 21), (6, 22)], br)
    s.line([(10, 17), (15, 16)], (120, 84, 40)); s.line([(9, 19), (14, 18)], (120, 84, 40))
    tube(s, [(18, 15), (20, 10), (20, 6)], c, 3, 3)             # crane's neck
    s.ell(18, 3, 23, 8, c)
    s.poly([(22, 4), (30, 7), (22, 7)], br)                     # long bronze beak
    s.px([(21, 5)], s.lit((255, 80, 60)))
    s.poly([(19, 3), (17, 0), (21, 2)], br)
    # the bronze feathers it throws like darts
    s.line([(25, 14), (28, 17)], steel); s.line([(24, 19), (27, 22)], steel)
    return s.finish()


@reg('cockatrice')
def cockatrice(r):
    s = Sprite()
    c, sc = (206, 180, 100), (90, 150, 80)
    # serpent tail
    tube(s, [(10, 21), (5, 24), (2, 20), (4, 15)], sc, 3, 1.5)
    s.line([(14, 23), (14, 28)], GOLD); s.line([(18, 23), (18, 28)], GOLD)
    s.line([(13, 28), (16, 28)], GOLD); s.line([(18, 28), (21, 28)], GOLD)
    B.wing(s, 14, 16, sc, 'bat', 0.8, tip=(60, 110, 70))
    s.ell(9, 14, 22, 24, c)
    tube(s, [(19, 16), (21, 12), (21, 9)], c, 4, 4)
    s.ell(18, 5, 25, 12, c)
    s.poly([(24, 8), (29, 9), (24, 11)], GOLD)
    s.poly([(19, 6), (19, 2), (21, 4), (22, 1), (24, 4), (25, 2), (25, 6)], RED)   # comb
    s.rect(23, 11, 24, 14, RED)                                 # wattle
    s.px([(22, 8)], s.lit((255, 240, 90)))
    return s.finish()


# ------------------------------------------------------------------ oddities
@reg('darkmantle')
def darkmantle(r):
    s = Sprite()
    c, dk = (60, 56, 96), (36, 32, 60)
    rock = (100, 96, 104)
    s.rect(4, 1, 27, 3, rock); s.poly([(6, 3), (8, 7), (10, 3)], rock); s.poly([(22, 3), (24, 6), (26, 3)], rock)
    # hanging like one more stalactite, webbed tentacles opening
    s.poly([(12, 3), (19, 3), (22, 14), (9, 14)], c)
    s.poly([(9, 14), (22, 14), (28, 22), (3, 22)], dk)
    for x0, x1, y in ((4, 2, 27), (9, 8, 28), (15, 15, 29), (21, 22, 28), (26, 28, 27)):
        s.line([(x0, 21), (x1, y)], c, 2)
    s.ell(13, 8, 18, 12, s.lit((255, 220, 90))); s.px([(15, 10), (16, 10), (15, 9), (16, 11)], DARK)
    s.shadow = False
    return s.finish()


def whirl(s, cx, cy, rx, ry, water, foam):
    s.ell(cx - rx, cy - ry, cx + rx, cy + ry, water)
    import math
    for i in range(0, 44):
        t = i / 44
        a = t * 4.2 * math.pi
        x = cx + math.cos(a) * rx * (1 - t * 0.75) * 0.92
        y = cy + math.sin(a) * ry * (1 - t * 0.75) * 0.92
        if i % 4 != 3:
            s.px([(int(round(x)), int(round(y)))], foam)


@reg('charybdis')
def charybdis(r):
    s = Sprite()
    s.shadow = False
    foam = s.lit((210, 240, 255))
    whirl(s, 15.5, 16, 14, 13, (40, 96, 190), foam)
    s.ell(5, 7, 26, 25, (28, 64, 150))
    s.ell(8, 10, 23, 23, (16, 26, 70))                          # the throat of the sea
    s.ell(12, 13, 19, 20, (8, 10, 30))
    import math
    for i in range(12):                                         # ring of teeth
        a = i / 12 * 2 * math.pi
        x, y = 15.5 + math.cos(a) * 8.2, 16.5 + math.sin(a) * 6.8
        x2, y2 = 15.5 + math.cos(a) * 5.6, 16.5 + math.sin(a) * 4.6
        s.line([(int(round(x)), int(round(y))), (int(round(x2)), int(round(y2)))], IVORY)
    s.px([(15, 16), (16, 17)], s.lit((120, 255, 230)))
    # a ship's mast going down
    s.line([(24, 3), (21, 10)], WOOD, 2); s.poly([(25, 3), (29, 5), (25, 8)], (226, 220, 200))
    return s.finish()


@reg('charybdis_spawn')
def charybdis_spawn(r):
    s = Sprite()
    s.shadow = False
    foam = s.lit((200, 236, 255))
    whirl(s, 15.5, 21, 13, 8, (30, 70, 170), foam)
    c = (60, 110, 200)
    # an eel-mawed thing rising out of its own little whirlpool
    tube(s, [(15, 22), (13, 16), (16, 10)], c, 7, 6, belly=(150, 200, 240))
    s.ell(10, 3, 22, 13, c)
    s.ell(12, 5, 20, 11, (14, 20, 60))
    s.px([(13, 5), (15, 4), (17, 4), (19, 5), (13, 11), (15, 12), (17, 12), (19, 11), (12, 8), (20, 8)], IVORY)
    s.px([(11, 4), (21, 4)], s.lit((120, 255, 230)))
    s.line([(9, 9), (6, 12), (5, 16)], c, 2); s.line([(22, 9), (25, 12), (26, 16)], c, 2)
    return s.finish()


@reg('scylla')
def scylla(r):
    s = Sprite()
    c, dk = (70, 110, 190), (44, 70, 140)
    sk = (170, 210, 220)
    eye = s.lit((255, 230, 90))
    # the long necks, each with a dog's head
    for pts, hx, hy, fl in (([(12, 20), (5, 17), (4, 9)], 4, 7, -1), ([(19, 20), (26, 17), (27, 9)], 27, 7, 1),
                            ([(11, 22), (4, 24), (2, 19)], 3, 18, -1), ([(20, 22), (27, 24), (29, 19)], 28, 18, 1)):
        tube(s, pts, c, 3, 2.4)
        s.ell(hx - 2, hy - 2, hx + 2, hy + 2, dk)
        s.rect(hx + (1 if fl > 0 else -3), hy, hx + (3 if fl > 0 else -1), hy + 1, dk)
        s.px([(hx, hy - 1)], eye); s.px([(hx + 2 * fl, hy + 2)], IVORY)
    # tentacle legs in the surf
    for x in (9, 13, 17, 21):
        tube(s, [(x, 21), (x + (1 if x > 15 else -1), 25), (x + (2 if x > 15 else -2), 28)], dk, 3, 2)
    s.ell(9, 16, 22, 25, c)
    # the nymph she used to be
    s.rect(13, 10, 18, 18, sk); s.rect(11, 11, 12, 16, sk); s.rect(19, 11, 20, 16, sk)
    s.ell(11, 2, 20, 11, (30, 60, 70))
    s.ell(12, 3, 19, 10, sk)
    s.rect(11, 6, 12, 13, (30, 60, 70)); s.rect(19, 6, 20, 13, (30, 60, 70))
    s.px([(14, 6), (17, 6)], eye); s.line([(15, 8), (16, 8)], (120, 60, 80))
    s.px([(2, 29), (6, 30), (25, 30), (29, 29), (15, 30)], s.lit(FOAM))
    return s.finish()


@reg('hook_horror')
def hook_horror(r):
    s = Sprite()
    c, pl = (150, 132, 112), (104, 90, 84)
    s.rect(11, 22, 14, 27, c); s.rect(18, 22, 21, 27, c)
    s.rect(10, 28, 14, 29, pl); s.rect(18, 28, 22, 29, pl)
    s.ell(9, 10, 23, 24, pl)                                    # beetle carapace
    s.ell(12, 13, 20, 23, c)
    for y in (16, 19):
        s.line([(13, y), (19, y)], pl)
    # scythe hooks for hands
    s.line([(9, 13), (5, 16), (4, 20)], c, 2); s.line([(23, 13), (27, 16), (28, 20)], c, 2)
    s.line([(4, 20), (2, 25), (4, 29), (7, 29)], IVORY, 2)
    s.line([(28, 20), (30, 25), (28, 29), (25, 29)], IVORY, 2)
    # vulture head
    s.ell(11, 3, 20, 11, c)
    s.poly([(14, 7), (18, 7), (17, 13), (15, 13)], (226, 190, 90)); s.px([(16, 13), (16, 14)], (150, 110, 50))
    s.px([(13, 6), (19, 6)], s.lit((255, 90, 60)))
    s.poly([(11, 5), (9, 2), (13, 3)], pl); s.poly([(20, 5), (22, 2), (18, 3)], pl)
    return s.finish()
