"""Four-legged beasts: canines, cats, bears, boars, cattle, rats, and the mythic mixes built on them."""
from c_base import *  # noqa: F401,F403

DIM = {
    0: dict(x0=10, x1=20, y0=18, y1=24, lw=2, hx=22, hy=16),
    1: dict(x0=6, x1=21, y0=15, y1=22, lw=3, hx=23, hy=12),
    2: dict(x0=4, x1=22, y0=11, y1=21, lw=3, hx=24, hy=9),
}


def dims(big, **over):
    d = dict(DIM[big]); d.update(over)
    return d


def quad(s, c, d, far=None, belly=None, feet=None, g=28, six=False, haunch=True):
    x0, x1, y0, y1, lw = d['x0'], d['x1'], d['y0'], d['y1'], d['lw']
    far = far or sh(c, -1)
    bx, fx = x0 + 1, x1 - lw
    s.rect(bx + 2, y1 - 2, bx + lw + 1, g, far)
    s.rect(fx - 2, y1 - 2, fx + lw - 3, g, far)
    if six:
        mx = (bx + fx) // 2
        s.rect(mx + 2, y1 - 2, mx + lw + 1, g, far)
    s.ell(x0, y0, x1, y1, c)
    if haunch:
        s.ell(x0, y0 + 2, x0 + 7, y1 + 1, c)
    if belly:
        s.ell(x0 + 4, y1 - 2, x1 - 3, y1, belly)
    s.rect(bx, y1 - 3, bx + lw - 1, g, c)
    s.rect(fx, y1 - 3, fx + lw - 1, g, c)
    if six:
        s.rect(mx - 1, y1 - 2, mx + lw - 2, g, c)
    if feet:
        for x in (bx, fx):
            s.rect(x, g, x + lw, g, feet)
    else:
        for x in (bx, fx):
            s.px([(x + lw, g)], c)


def neck(s, d, c):
    x1, y0, hx, hy = d['x1'], d['y0'], d['hx'], d['hy']
    s.poly([(x1 - 6, y0 + 1), (hx - 3, hy - 1), (hx + 1, hy + 3), (x1 - 1, y0 + 6)], c)


def head_wolf(s, hx, hy, c, eye, ear='point', jaw=False, snc=None, nose=DARK, earc=None):
    earc = earc or c
    if ear == 'point':
        s.poly([(hx - 4, hy - 2), (hx - 4, hy - 7), (hx - 1, hy - 4)], sh(earc, -1))
        s.poly([(hx - 1, hy - 4), (hx + 1, hy - 8), (hx + 2, hy - 3)], earc)
    elif ear == 'tall':
        s.rect(hx - 4, hy - 9, hx - 3, hy - 3, sh(earc, -1))
        s.rect(hx, hy - 10, hx + 1, hy - 3, earc)
    s.ell(hx - 4, hy - 4, hx + 3, hy + 3, c)
    if ear == 'flop':
        s.poly([(hx - 3, hy - 4), (hx - 6, hy + 2), (hx - 2, hy + 1)], sh(earc, -1))
    s.rect(hx + 2, hy - 1, hx + 6, hy + 1, snc or c)
    if jaw:
        s.rect(hx + 1, hy + 2, hx + 5, hy + 2, (130, 30, 40))
        s.rect(hx + 1, hy + 3, hx + 5, hy + 3, c)
        s.px([(hx + 3, hy + 2), (hx + 5, hy + 2)], IVORY)
    else:
        s.line([(hx + 2, hy + 2), (hx + 5, hy + 2)], sh(c, -2))
    s.px([(hx + 6, hy - 1)], nose)
    s.px([(hx + 1, hy - 2)], eye)


def head_cat(s, hx, hy, c, eye, muz=None, mane=None, r=4):
    if mane:
        s.ell(hx - r - 5, hy - r - 3, hx + r, hy + r + 4, mane)
        r = 3; hx += 1
    s.poly([(hx - r, hy - 2), (hx - r, hy - r - 2), (hx - 1, hy - r)], c)
    s.poly([(hx + 1, hy - r), (hx + 3, hy - r - 2), (hx + r, hy - 2)], c)
    s.ell(hx - r, hy - r, hx + r, hy + r, c)
    s.rect(hx + 1, hy, hx + r + 1, hy + 2, muz or sh(c, 1))
    s.px([(hx + r + 1, hy)], (140, 70, 70))
    s.line([(hx + 2, hy + 3), (hx + r, hy + 3)], sh(c, -2))
    s.px([(hx - 1, hy - 1), (hx + 3, hy - 1)], eye)


def head_bear(s, hx, hy, c, eye=DARK, muz=None):
    s.ell(hx - 5, hy - 7, hx - 2, hy - 4, c); s.ell(hx + 1, hy - 7, hx + 4, hy - 4, c)
    s.ell(hx - 5, hy - 5, hx + 4, hy + 4, c)
    s.rect(hx + 2, hy, hx + 6, hy + 3, muz or sh(c, 1))
    s.rect(hx + 5, hy, hx + 6, hy + 1, DARK)
    s.line([(hx + 3, hy + 3), (hx + 5, hy + 3)], DARK)
    s.px([(hx + 1, hy - 2)], eye); s.px([(hx + 1, hy - 3)], sh(c, -2))


def head_boar(s, hx, hy, c, eye, tusk=2):
    s.poly([(hx - 3, hy - 4), (hx - 4, hy - 7), (hx - 1, hy - 5)], sh(c, -1))
    s.poly([(hx - 5, hy - 4), (hx + 1, hy - 4), (hx + 6, hy), (hx + 6, hy + 3), (hx - 5, hy + 4)], c)
    s.rect(hx + 6, hy, hx + 7, hy + 3, (200, 130, 130))
    s.px([(hx + 7, hy + 1)], DARK)
    s.line([(hx + 3, hy + 4), (hx + 3, hy + 1)], IVORY, 2)
    s.px([(hx + 4, hy), (hx + 4, hy - 1)], IVORY)
    if tusk > 2:
        s.px([(hx + 5, hy - 2), (hx + 5, hy - 3)], IVORY)
    s.px([(hx, hy - 2)], eye)


def head_rat(s, hx, hy, c, eye):
    s.ell(hx - 4, hy - 6, hx - 1, hy - 2, PINK)
    s.poly([(hx - 4, hy - 3), (hx, hy - 3), (hx + 6, hy + 1), (hx + 6, hy + 2), (hx - 4, hy + 3)], c)
    s.px([(hx + 6, hy + 1)], PINK); s.px([(hx + 5, hy + 3)], IVORY)
    s.px([(hx + 1, hy - 1)], eye)


def head_bull(s, hx, hy, c, eye, horn=IVORY, muz=PINK, horns='up'):
    if horns == 'up':
        s.line([(hx - 3, hy - 3), (hx - 5, hy - 6), (hx - 4, hy - 8)], horn, 2)
        s.line([(hx + 1, hy - 4), (hx + 4, hy - 6), (hx + 5, hy - 9)], horn, 2)
    elif horns == 'curl':
        s.line([(hx - 3, hy - 4), (hx - 5, hy - 6), (hx - 3, hy - 7)], horn, 2)
        s.line([(hx + 1, hy - 4), (hx + 3, hy - 6), (hx + 1, hy - 7)], horn, 2)
    elif horns == 'small':
        s.line([(hx - 3, hy - 4), (hx - 4, hy - 6)], horn, 2)
        s.line([(hx + 1, hy - 4), (hx + 3, hy - 6)], horn, 2)
    s.poly([(hx - 5, hy - 2), (hx - 8, hy - 1), (hx - 5, hy + 1)], sh(c, -1))
    s.ell(hx - 4, hy - 4, hx + 3, hy + 3, c)
    s.rect(hx, hy + 1, hx + 5, hy + 4, muz)
    s.px([(hx + 2, hy + 3), (hx + 4, hy + 3)], DARK)
    s.px([(hx - 1, hy - 1), (hx + 2, hy - 1)], eye)


def head_eagle(s, hx, hy, c, eye, beak=GOLD, tuft=True):
    if tuft:
        s.poly([(hx - 3, hy - 3), (hx - 5, hy - 7), (hx - 1, hy - 4)], c)
    s.ell(hx - 4, hy - 4, hx + 3, hy + 3, c)
    s.poly([(hx + 2, hy - 2), (hx + 7, hy), (hx + 6, hy + 3), (hx + 5, hy + 1), (hx + 2, hy + 1)], beak)
    s.px([(hx, hy - 1)], eye)


def head_human(s, hx, hy, skin=SKIN, hair=None, beard=None, eye=DARK):
    if hair:
        s.ell(hx - 4, hy - 5, hx + 3, hy + 4, hair)
    s.ell(hx - 2, hy - 4, hx + 4, hy + 4, skin)
    if hair:
        s.rect(hx - 2, hy - 5, hx + 3, hy - 4, hair)
    if beard:
        s.rect(hx - 1, hy + 2, hx + 4, hy + 5, beard)
    s.px([(hx, hy - 1), (hx + 3, hy - 1)], eye)
    if not beard:
        s.line([(hx + 1, hy + 2), (hx + 2, hy + 2)], (150, 70, 70))


def head_croc(s, hx, hy, c, eye):
    s.rect(hx - 4, hy - 3, hx + 1, hy + 3, c)
    s.rect(hx - 2, hy - 5, hx, hy - 3, c)
    s.rect(hx + 1, hy - 1, hx + 7, hy, c)
    s.rect(hx + 1, hy + 2, hx + 7, hy + 3, sh(c, -1))
    s.rect(hx + 1, hy + 1, hx + 7, hy + 1, (120, 30, 40))
    s.px([(hx + 2, hy + 1), (hx + 4, hy + 1), (hx + 6, hy + 1)], IVORY)
    s.px([(hx - 1, hy - 4)], eye)


def wing(s, x, y, c, kind='feather', k=1.0, tip=None):
    def P(dx, dy):
        return (int(round(x + dx * k)), int(round(y + dy * k)))
    if kind == 'feather':
        s.poly([P(1, 0), P(-2, -9), P(-7, -12), P(-11, -9), P(-8, -7), P(-11, -5), P(-7, -3), P(-9, 0), P(-4, 1)], c)
        t = tip or sh(c, -1)
        s.line([P(-3, -7), P(-8, -9)], t); s.line([P(-3, -4), P(-8, -5)], t); s.line([P(-2, -1), P(-6, -1)], t)
    else:
        mem = tip or sh(c, -1)
        s.poly([P(1, 0), P(-1, -11), P(-5, -7), P(-9, -10), P(-10, -4), P(-12, -2), P(-7, -1), P(-5, 2)], mem)
        s.line([P(0, 0), P(-1, -11)], c); s.line([P(-1, -11), P(-5, -6)], c)
        s.line([P(-1, -10), P(-9, -9)], c); s.line([P(-1, -10), P(-11, -3)], c)


# ------------------------------------------------------------------ canines
def canine(s, c, big=1, belly=None, eye=None, ear='point', tail='bush', jaw=False, tailc=None,
           snc=None, ruff=None, d=None, heads=1, earc=None):
    d = d or dims(big)
    x0, y0 = d['x0'], d['y0']
    eye = eye or s.lit((250, 220, 80))
    tc = tailc or c
    if tail == 'bush':
        tube(s, [(x0 + 2, y0 + 3), (x0 - 1, y0 + 1), (max(3, x0 - 2), y0 - 4)], tc, 3.4, 2)
    elif tail == 'thin':
        tube(s, [(x0 + 2, y0 + 3), (x0 - 2, y0 + 2), (max(2, x0 - 3), y0 - 3)], tc, 2, 1)
    elif tail == 'down':
        tube(s, [(x0 + 2, y0 + 3), (x0 - 1, y0 + 5), (x0 - 1, y0 + 10)], tc, 3.4, 2)
    elif tail == 'fork':
        s.line([(x0 + 2, y0 + 3), (x0, y0 - 2), (x0, y0 - 7)], tc, 2)
        s.line([(x0, y0 - 7), (x0 - 2, y0 - 10)], tc); s.line([(x0 + 1, y0 - 7), (x0 + 3, y0 - 10)], tc)
    quad(s, c, d, belly=belly)
    if heads == 2:
        hx, hy = d['hx'] - 8, d['hy'] - 5
        s.poly([(d['x1'] - 9, y0 + 2), (hx - 3, hy), (hx + 2, hy + 3), (d['x1'] - 4, y0 + 3)], sh(c, 1))
        head_wolf(s, hx, hy, sh(c, 1), eye, ear, jaw, snc, earc=earc)
    neck(s, d, c)
    if ruff:
        s.ell(d['x1'] - 8, y0 - 2, d['x1'] - 1, y0 + 6, ruff)
    head_wolf(s, d['hx'], d['hy'], c, eye, ear, jaw, snc, earc=earc)
    return d


@reg('wolf_pack_leader')
def wolf_pack_leader(r):
    s = Sprite()
    c = (150, 150, 158)
    d = canine(s, c, 1, belly=(214, 210, 200), snc=(214, 210, 200), ruff=(110, 110, 122))
    s.line([(d['x0'] + 5, d['y0']), (d['x1'] - 8, d['y0'])], (96, 96, 108))
    return s.finish()


@reg('dire_wolf_alpha')
def dire_wolf_alpha(r):
    s = Sprite()
    c = (104, 92, 86)
    eye = s.lit((255, 80, 50))
    d = canine(s, c, 2, belly=(150, 136, 124), eye=eye, jaw=True, ruff=(66, 56, 60), tailc=(66, 56, 60),
               d=dims(2, lw=4))
    for x in range(d['x0'] + 4, d['x1'] - 8, 3):
        s.px([(x, d['y0'] - 1), (x + 1, d['y0'] - 1), (x, d['y0'] - 2)], (66, 56, 60))
    s.line([(12, 14), (14, 17)], (190, 150, 140))
    return s.finish()


@reg('winter_wolf')
def winter_wolf(r):
    s = Sprite()
    c = (222, 232, 246)
    eye = s.lit((90, 190, 255))
    d = canine(s, c, 1, belly=(246, 250, 255), eye=eye, jaw=True, tailc=(190, 208, 236), ruff=(190, 208, 236),
               d=dims(1, y0=14, hy=11))
    ice = s.lit(ICE)
    s.px([(29, 15), (30, 16), (28, 17), (30, 18), (29, 19)], ice)
    for x in (9, 12, 15):
        s.px([(x, 13), (x, 12)], (170, 200, 240))
    return s.finish()


@reg('fenrir_pup')
def fenrir_pup(r):
    s = Sprite()
    c = (96, 76, 122)
    d = canine(s, c, 0, belly=(150, 130, 170), eye=s.lit((255, 210, 70)), d=dims(0, y0=17, x0=9, hy=15),
               tailc=(70, 54, 94))
    # a snapped length of chain trailing from the hind leg
    s.px([(8, 27), (6, 28), (4, 27), (2, 28)], STEEL)
    s.px([(7, 28), (5, 27), (3, 28)], IRON)
    return s.finish()


@reg('fenrir_wolf')
def fenrir_wolf(r):
    s = Sprite()
    c = (150, 168, 204)
    dk = (86, 98, 140)
    eye = s.lit((255, 60, 40))
    d = dims(2, x0=3, x1=22, y0=9, y1=21, lw=4, hx=24, hy=8)
    tube(s, [(5, 13), (2, 10), (3, 4)], dk, 4, 2)
    quad(s, c, d, belly=(206, 216, 236))
    neck(s, d, c)
    s.ell(13, 5, 22, 16, dk)                                   # storm-dark mane
    for x in (6, 9, 12):
        s.poly([(x, 9), (x + 1, 5), (x + 3, 9)], dk)
    head_wolf(s, 24, 8, c, eye, jaw=True, earc=dk)
    s.px([(27, 12), (29, 12)], IVORY)
    # Gleipnir: the thin ribbon that holds him
    g = s.lit((255, 214, 110))
    s.line([(7, 10), (10, 20)], g); s.line([(12, 9), (15, 20)], g)
    s.line([(4, 25), (8, 25)], g); s.line([(18, 25), (22, 25)], g)
    s.line([(8, 25), (10, 28), (17, 28), (18, 25)], g)
    return s.finish()


@reg('fenrir')
def fenrir_pet(r):
    s = Sprite()
    c = (120, 126, 146)
    d = dims(2, x0=4, x1=22, y0=11, y1=21, lw=4, hx=24, hy=9)
    tube(s, [(6, 14), (3, 11), (3, 5)], c, 4, 2.4)
    s.px([(3, 4), (3, 5), (2, 6)], WHITE)
    quad(s, c, d, belly=(226, 226, 230), feet=(226, 226, 230))
    neck(s, d, c)
    s.ell(15, 9, 22, 18, (226, 226, 230))                      # white chest
    head_wolf(s, 24, 9, c, DARK, snc=(226, 226, 230), earc=(90, 94, 116))
    s.px([(25, 7)], WHITE)                                      # bright friendly eye
    s.px([(25, 8)], (60, 110, 200))
    s.rect(27, 11, 28, 13, PINK)                                # tongue out
    s.line([(18, 12), (21, 16)], RED, 2); s.px([(21, 17)], GOLD)  # collar and tag
    return s.finish()


@reg('fionn_hound')
def fionn_hound(r):
    s = Sprite()
    c = (232, 216, 180)
    d = dims(1, x0=6, x1=21, y0=13, y1=18, lw=2, hx=23, hy=9)
    canine(s, c, 1, belly=(250, 240, 214), eye=DARK, ear='flop', tail='thin', d=d, earc=(170, 140, 100))
    s.line([(18, 12), (21, 14)], (40, 140, 80), 2); s.px([(20, 14)], GOLD)
    for x in (9, 13, 17):
        s.px([(x, 12)], (190, 170, 130))                        # wiry coat
    return s.finish()


@reg('blink_dog')
def blink_dog(r):
    s = Sprite()
    c = (214, 180, 110)
    star = s.lit((150, 200, 255))
    d = canine(s, c, 1, belly=(240, 222, 170), eye=star, ear='point', tail='bush', earc=(150, 110, 70),
               d=dims(1, x0=9, x1=22, hx=24))
    # the after-image it leaves behind as it blinks
    s.px([(3, 16), (4, 16), (2, 19), (5, 20), (3, 23), (6, 25), (4, 26)], star)
    s.px([(28, 5), (27, 6), (29, 6), (28, 7)], star)
    return s.finish()


@reg('death_dog')
def death_dog(r):
    s = Sprite()
    c = (92, 60, 96)
    eye = s.lit((255, 70, 60))
    d = canine(s, c, 1, eye=eye, jaw=True, tail='thin', heads=2, d=dims(1, hx=24, hy=15, y0=16, y1=23))
    s.px([(9, 15), (12, 14), (15, 14)], (60, 36, 66))
    return s.finish()


@reg('sets_jackal')
def sets_jackal(r):
    s = Sprite()
    c, dk = (190, 84, 50), (110, 40, 36)
    eye = s.lit((255, 220, 90))
    d = dims(1, x0=6, x1=20, y0=15, y1=21, lw=2, hx=22, hy=12)
    # the stiff forked tail of the Set animal
    s.line([(7, 17), (5, 12), (5, 8)], dk, 2); s.line([(5, 8), (3, 5)], dk, 2); s.line([(6, 8), (8, 5)], dk, 2)
    quad(s, c, d, belly=dk, feet=dk)
    neck(s, d, c)
    # tall ears cut off square
    s.poly([(18, 10), (17, 4), (20, 4), (21, 10)], dk); s.poly([(22, 10), (23, 3), (26, 3), (25, 10)], c)
    s.ell(18, 8, 25, 15, c)
    # the long snout that curves down
    s.rect(24, 11, 28, 13, c); s.rect(27, 13, 29, 16, c); s.px([(28, 17), (29, 17)], DARK)
    s.px([(23, 11)], eye)
    s.line([(17, 14), (20, 17)], GOLD, 2); s.px([(19, 17)], s.lit((70, 200, 220)))
    s.line([(9, 16), (11, 18)], GOLD); s.line([(13, 16), (15, 18)], GOLD)   # desert-storm markings
    s.px([(2, 27), (4, 28), (27, 27), (29, 28), (25, 28)], (226, 196, 130))   # blown sand
    return s.finish()


# ------------------------------------------------------------------ cats
def feline(s, c, big=1, belly=None, eye=None, mane=None, tuft=None, d=None, six=False, tail=True, muz=None):
    d = d or dims(big)
    x0, y0 = d['x0'], d['y0']
    eye = eye or s.lit((160, 240, 90))
    if tail:
        tube(s, [(x0 + 2, y0 + 4), (x0 - 2, y0 + 5), (max(2, x0 - 3), y0), (max(3, x0 - 1), y0 - 4)], c, 2, 2)
        if tuft:
            s.ell(max(2, x0 - 2), y0 - 7, max(2, x0 - 2) + 3, y0 - 4, tuft)
    quad(s, c, d, belly=belly, six=six)
    neck(s, d, c)
    head_cat(s, d['hx'], d['hy'], c, eye, mane=mane, muz=muz)
    return d


@reg('dire_lion')
def dire_lion(r):
    s = Sprite()
    c, mane = (214, 170, 90), (130, 78, 40)
    feline(s, c, 1, belly=(240, 214, 150), eye=DARK, mane=mane, tuft=mane, d=dims(1, y0=14, hy=12))
    return s.finish()


@reg('nemean_lion')
def nemean_lion(r):
    s = Sprite()
    c, mane = (238, 196, 84), (190, 104, 30)
    eye = s.lit((255, 250, 200))
    d = dims(2, x0=4, x1=22, y0=11, y1=21, lw=4, hx=23, hy=10)
    feline(s, c, 2, belly=(255, 232, 150), eye=eye, mane=mane, tuft=mane, d=d)
    s.ell(13, 3, 22, 8, mane)                                   # the mane crests high
    glint = s.lit((255, 250, 210))                              # the hide no blade can cut
    s.px([(8, 13), (9, 12), (12, 14), (6, 16)], glint)
    # a spent arrow that bounced off
    s.line([(2, 26), (6, 28)], WOOD); s.px([(1, 25)], STEEL); s.px([(7, 28)], RED)
    return s.finish()


@reg('cath_palug')
def cath_palug(r):
    s = Sprite()
    c = (128, 100, 160)
    dk = (78, 58, 110)
    d = dims(1, x0=5, x1=21, y0=12, y1=21, lw=3, hx=23, hy=12)
    feline(s, c, 1, belly=(180, 160, 204), eye=s.lit((120, 255, 170)), d=d)
    s.px([(8, 14), (11, 13), (14, 14), (17, 15), (9, 17), (13, 17), (16, 18), (7, 19)], dk)   # speckled
    for x in (8, 11, 14):
        s.poly([(x, 12), (x + 1, 9), (x + 2, 12)], dk)          # arched, bristling back
    s.px([(26, 15), (28, 15)], IVORY)
    s.px([(3, 28), (27, 28), (29, 27)], s.lit(FOAM))           # still dripping from the strait
    return s.finish()


@reg('displacer_beast')
def displacer_beast(r):
    s = Sprite()
    c = (74, 56, 136)
    dk = (48, 36, 96)
    pad = s.lit((200, 120, 255))
    d = dims(1, x0=4, x1=21, y0=15, y1=21, lw=2, hx=23, hy=13)
    # two shoulder tentacles ending in barbed pads
    tube(s, [(15, 15), (11, 8), (5, 5)], dk, 2, 2); s.ell(2, 3, 6, 7, dk); s.px([(3, 5), (5, 4)], pad)
    tube(s, [(17, 15), (17, 7), (24, 3)], dk, 2, 2); s.ell(23, 1, 27, 5, dk); s.px([(24, 3), (26, 2)], pad)
    feline(s, c, 1, eye=s.lit((120, 255, 120)), d=d, six=True)
    return s.finish()


@reg('carbuncle')
def carbuncle(r):
    s = Sprite()
    c = (120, 190, 170)
    gem = s.lit((255, 50, 80))
    d = dims(0, x0=8, x1=20, y0=17, y1=24, hx=21, hy=16)
    tube(s, [(10, 21), (5, 20), (4, 14), (7, 11)], c, 3.4, 2.4)
    s.px([(7, 10), (8, 11)], WHITE)
    quad(s, c, d, belly=(220, 240, 226))
    s.poly([(17, 13), (15, 6), (20, 12)], c); s.poly([(21, 12), (23, 5), (25, 13)], c)   # long ears
    s.ell(16, 11, 26, 21, c)
    s.rect(23, 17, 27, 19, (220, 240, 226)); s.px([(27, 17)], DARK)
    s.px([(21, 16), (24, 16)], DARK)
    s.poly([(22, 10), (20, 12), (22, 14), (24, 12)], gem)       # the ruby in its brow
    s.px([(22, 12)], s.lit((255, 200, 210)))
    return s.finish()


def lion_tail_sting(s, x0, y0, c, tip, spikes=False):
    tube(s, [(x0 + 2, y0 + 4), (x0 - 2, y0 + 2), (x0 - 2, y0 - 5), (x0 + 2, y0 - 8)], c, 2, 2)
    s.ell(x0 + 1, y0 - 11, x0 + 5, y0 - 7, tip)
    s.line([(x0 + 5, y0 - 9), (x0 + 7, y0 - 8)], IVORY)
    if spikes:
        s.px([(x0 + 2, y0 - 12), (x0, y0 - 10), (x0 + 4, y0 - 12), (x0 + 6, y0 - 11)], IVORY)


def _manticore(big, c, wingc, mane, elder):
    s = Sprite()
    d = dims(1, x0=6, x1=21, y0=15, y1=22, lw=3, hx=24, hy=13) if not elder else \
        dims(2, x0=5, x1=22, y0=13, y1=21, lw=4, hx=24, hy=11)
    wing(s, d['x1'] - 5, d['y0'] + 1, wingc, 'bat', 0.8 if not elder else 0.95)
    x0, y0 = d['x0'], d['y0']
    seg = (90, 44, 50)
    tube(s, [(x0 + 2, y0 + 4), (x0 - 3, y0 + 1), (x0 - 3, y0 - 7), (x0 + 1, y0 - 10)], seg, 3, 2.4)
    s.ell(x0, y0 - 13, x0 + 4, y0 - 9, seg)                     # the spiked tail-club
    s.px([(x0 - 1, y0 - 12), (x0 + 2, y0 - 14), (x0 + 5, y0 - 12), (x0 + 5, y0 - 9)], IVORY)
    if elder:
        s.line([(x0 + 7, y0 - 13), (x0 + 9, y0 - 14)], IVORY); s.line([(x0 + 7, y0 - 9), (x0 + 9, y0 - 8)], IVORY)
    quad(s, c, d, belly=sh(c, 1))
    neck(s, d, c)
    hx, hy = d['hx'], d['hy']
    s.ell(hx - 7, hy - 6, hx + 4, hy + 6, mane)
    s.ell(hx - 2, hy - 4, hx + 4, hy + 3, (226, 176, 136))
    s.px([(hx, hy - 1), (hx + 3, hy - 1)], s.lit((255, 90, 60)))
    s.rect(hx, hy + 1, hx + 3, hy + 1, (120, 30, 40)); s.px([(hx, hy + 1), (hx + 2, hy + 1)], IVORY)
    if elder:
        s.px([(d['hx'], d['hy'] - 6), (d['hx'] + 2, d['hy'] - 7)], GOLD)
    return s.finish()


@reg('manticore')
def manticore(r):
    return _manticore(1, (196, 104, 64), (150, 60, 60), (110, 50, 36), False)


@reg('manticore_elder')
def manticore_elder(r):
    return _manticore(2, (210, 150, 70), (96, 40, 70), (90, 40, 30), True)


def _chimera(c, mane, goat, alpha):
    s = Sprite()
    d = dims(1, x0=7, x1=21, y0=16, y1=22, lw=3, hx=24, hy=14) if not alpha else \
        dims(2, x0=6, x1=22, y0=14, y1=21, lw=4, hx=24, hy=13)
    x0, y0 = d['x0'], d['y0']
    snake = (80, 160, 70)
    # serpent for a tail
    tube(s, [(x0 + 2, y0 + 4), (x0 - 3, y0 + 3), (x0 - 4, y0 - 4), (x0 - 1, y0 - 8)], snake, 2.4, 2.4)
    s.ell(x0 - 2, y0 - 11, x0 + 3, y0 - 7, snake)
    s.px([(x0 + 2, y0 - 9)], s.lit((255, 230, 80))); s.px([(x0 + 4, y0 - 8), (x0 + 5, y0 - 7)], RED)
    quad(s, c, d, belly=sh(c, 1))
    # goat rising from the middle of the back
    gx, gy = x0 + 8, y0 - 6
    s.rect(gx - 2, gy + 1, gx + 1, y0 + 2, goat)
    hc = IVORY
    s.line([(gx - 1, gy - 3), (gx - 4, gy - 5), (gx - 5, gy - 2)], hc, 2)
    s.line([(gx + 1, gy - 3), (gx - 1, gy - 6), (gx - 3, gy - 6)], hc, 2)
    s.ell(gx - 3, gy - 3, gx + 2, gy + 2, goat)
    s.rect(gx + 1, gy - 1, gx + 4, gy + 1, goat); s.px([(gx + 2, gy + 2), (gx + 2, gy + 3)], sh(goat, -2))
    s.px([(gx, gy - 1)], s.lit((255, 210, 80)))
    neck(s, d, c)
    head_cat(s, d['hx'], d['hy'], c, s.lit((255, 200, 60)), mane=mane)
    if alpha:
        f1, f2 = s.lit(FIRE), s.lit(FIRE2)
        s.poly([(27, 16), (30, 18), (30, 22), (27, 20)], f1); s.px([(28, 18), (29, 19)], f2)
    return s.finish()


@reg('chimera')
def chimera(r):
    return _chimera((214, 160, 96), (140, 70, 50), (120, 112, 120), False)


@reg('chimera_alpha')
def chimera_alpha(r):
    return _chimera((222, 178, 70), (150, 76, 30), (96, 88, 100), True)


@reg('griffin')
def griffin(r):
    s = Sprite()
    c, feather = (206, 166, 76), (240, 234, 214)
    d = dims(1, x0=6, x1=21, y0=15, y1=22, lw=3, hx=24, hy=11)
    tube(s, [(8, 19), (4, 20), (3, 15), (4, 12)], c, 2, 2); s.ell(2, 9, 6, 12, (130, 90, 50))
    wing(s, 16, 16, (150, 110, 60), 'feather', 1.15, tip=(100, 70, 40))
    quad(s, c, d, belly=sh(c, 1))
    # eagle forequarters: white breast and yellow talons
    s.poly([(15, 16), (21, 10), (25, 14), (21, 22), (17, 22)], feather)
    s.rect(18, 20, 20, 27, GOLD); s.rect(18, 28, 22, 28, GOLD); s.px([(23, 28)], DARK)
    head_eagle(s, 24, 10, feather, DARK)
    return s.finish()


@reg('nue')
def nue(r):
    s = Sprite()
    body, tiger, stripe = (128, 96, 76), (226, 150, 50), (50, 36, 40)
    d = dims(1, x0=7, x1=21, y0=15, y1=22, lw=3, hx=23, hy=13)
    # the black cloud it rides in
    cl = (56, 48, 72)
    s.ell(1, 22, 12, 30, cl); s.ell(9, 24, 22, 30, cl); s.ell(19, 22, 30, 30, cl); s.ell(1, 16, 7, 23, cl)
    s.shadow = False
    snake = (90, 170, 90)
    tube(s, [(9, 19), (4, 19), (3, 13), (6, 11)], snake, 2.4, 2.4)
    s.ell(5, 9, 10, 13, snake); s.px([(8, 10)], s.lit((255, 230, 80))); s.px([(10, 12), (11, 13)], RED)
    quad(s, body, d, far=sh(tiger, -1))
    # tiger legs
    for x in (8, 18):
        s.rect(x, 21, x + 2, 28, tiger); s.px([(x + 3, 28)], tiger)
        s.line([(x, 23), (x + 2, 23)], stripe); s.line([(x, 26), (x + 2, 26)], stripe)
    neck(s, d, body)
    # monkey face
    s.ell(18, 8, 27, 18, (110, 70, 50))
    s.ell(21, 10, 27, 17, (220, 110, 90))
    s.ell(17, 10, 19, 14, (220, 110, 90))
    s.px([(22, 12), (25, 12)], s.lit((255, 240, 120)))
    s.line([(23, 15), (25, 15)], DARK)
    return s.finish()


@reg('ammit_spawn')
def ammit_spawn(r):
    s = Sprite()
    croc, lion, hippo = (96, 140, 76), (206, 160, 84), (120, 108, 116)
    d = dims(1, x0=5, x1=20, y0=15, y1=23, lw=3, hx=22, hy=14)
    x0, x1, y0, y1 = 5, 20, 15, 23
    s.rect(3, 18, 5, 20, hippo)                                 # stub tail
    # hippo hindquarters
    s.rect(10, 21, 12, 28, sh(hippo, -1))
    s.ell(4, 14, 15, 24, hippo); s.rect(6, 21, 9, 28, hippo); s.px([(10, 28)], hippo)
    # lion forequarters and mane
    s.rect(14, 21, 16, 28, sh(lion, -1))
    s.ell(11, 14, 21, 23, lion); s.rect(17, 21, 19, 28, lion); s.px([(20, 28)], lion)
    s.ell(15, 9, 23, 20, (140, 86, 40))
    head_croc(s, 22, 14, croc, s.lit((255, 220, 70)))
    return s.finish()


# ------------------------------------------------------------------ sphinxes (seated)
def sphinx_body(s, c, wings=None, wk='feather', big=False, tip=None):
    """Lion couchant: haunch at left, forepaws stretched right, chest upright."""
    tube(s, [(6, 24), (2, 23), (2, 17), (4, 15)], c, 2, 2)
    s.ell(3, 13, 6, 16, sh(c, -1))
    if wings:
        wing(s, 15, 17, wings, wk, 1.2 if big else 1.0, tip=tip)
    s.ell(4, 17, 16, 28, c)                                     # haunch
    s.rect(8, 20, 20, 28, c)                                    # barrel
    s.poly([(15, 28), (15, 14), (22, 12), (23, 28)], c)         # upright chest
    s.rect(20, 25, 28, 28, c); s.line([(22, 27), (28, 27)], sh(c, -1))   # forepaws
    s.px([(26, 25), (28, 25)], sh(c, -1))
    s.rect(5, 27, 12, 28, c)


@reg('sphinx')
def sphinx(r):
    s = Sprite()
    c = (222, 186, 100)
    sphinx_body(s, c, wings=(240, 226, 180))
    head_human(s, 19, 9, skin=(226, 180, 140), hair=(70, 46, 40))
    s.rect(15, 11, 16, 16, (70, 46, 40))                        # long dark hair
    return s.finish()


@reg('the_sphinx')
def the_sphinx(r):
    s = Sprite()
    c = (206, 176, 110)
    rock = (112, 106, 112)
    # she sits on her rock above the road to Thebes
    sphinx_body(s, c, wings=(150, 100, 60), big=True)
    s.poly([(2, 30), (4, 26), (28, 26), (30, 30)], rock)
    s.px([(8, 28), (15, 29), (22, 28)], sh(rock, -1))
    head_human(s, 19, 9, skin=(232, 190, 150), hair=(150, 50, 40))
    s.rect(14, 10, 16, 17, (150, 50, 40)); s.rect(22, 12, 23, 15, (150, 50, 40))
    s.px([(19, 8), (22, 8)], s.lit((120, 230, 255)))
    s.line([(17, 4), (22, 4)], GOLD); s.px([(20, 3)], s.lit((120, 230, 255)))   # diadem
    return s.finish()


@reg('dread_sphinx')
def dread_sphinx(r):
    s = Sprite()
    c = (136, 120, 140)
    sphinx_body(s, c, wings=(70, 50, 100), big=True, tip=(150, 120, 190))
    head_human(s, 19, 9, skin=(180, 170, 170), hair=(40, 30, 46), eye=s.lit((255, 60, 60)))
    s.rect(14, 10, 16, 18, (40, 30, 46))
    s.px([(20, 12), (22, 12)], IVORY)
    s.px([(25, 29), (27, 29)], BONE); s.px([(29, 28)], BONE)   # what is left of bad guessers
    return s.finish()


@reg('sphinx_guardian')
def sphinx_guardian(r):
    s = Sprite()
    c = (214, 190, 130)                                         # sandstone
    blue = (50, 90, 170)
    sphinx_body(s, c)
    # nemes headcloth, striped gold and blue
    s.poly([(14, 16), (15, 5), (18, 3), (22, 3), (25, 5), (25, 16), (22, 13), (17, 13)], GOLD)
    for y in (6, 9, 12, 15):
        s.line([(14, y), (16, y)], blue); s.line([(24, y), (25, y)], blue)
    s.rect(17, 6, 23, 13, (200, 160, 110))
    s.px([(19, 8), (22, 8)], DARK); s.line([(20, 11), (21, 11)], DARK)
    s.rect(20, 14, 21, 16, blue)                                # false beard
    s.px([(20, 3)], s.lit((90, 220, 220)))
    s.px([(9, 22), (11, 24), (18, 20)], sh(c, -1))              # weathering
    return s.finish()


@reg('sphinx_lesser')
def sphinx_lesser(r):
    s = Sprite()
    c = (206, 172, 110)
    sphinx_body(s, c)
    # ram-headed, like the avenue at Thebes
    s.ell(15, 5, 23, 14, c); s.rect(21, 9, 26, 13, c); s.px([(26, 11)], DARK)
    horn = (120, 90, 60)
    s.ell(13, 5, 19, 12, horn); s.ell(15, 7, 17, 10, c)
    s.px([(21, 8)], DARK)
    return s.finish()


# ------------------------------------------------------------------ bears
@reg('cave_bear')
def cave_bear(r):
    s = Sprite()
    c = (140, 98, 62)
    d = dims(1, x0=4, x1=22, y0=11, y1=22, lw=4, hx=23, hy=14)
    quad(s, c, d, belly=sh(c, -1), feet=(60, 44, 40))
    s.ell(12, 7, 22, 16, c)                                     # shoulder hump
    head_bear(s, 22, 15, c, muz=(214, 180, 130))
    s.rect(3, 15, 4, 17, c)
    return s.finish()


def upright(s, c, belly, x0=9, x1=22, top=10, hip=24):
    """Rearing beast: thick legs, barrel torso, arms out."""
    s.rect(x0 + 1, hip - 2, x0 + 5, 28, c); s.rect(x1 - 5, hip - 2, x1 - 1, 28, c)
    s.rect(x0, 28, x0 + 5, 29, sh(c, -1)); s.rect(x1 - 5, 28, x1, 29, sh(c, -1))
    s.ell(x0, top, x1, hip + 1, c)
    s.ell(x0 + 3, top + 4, x1 - 3, hip - 1, belly)


@reg('dire_bear')
def dire_bear(r):
    s = Sprite()
    c = (104, 72, 56)
    upright(s, c, (140, 104, 78), 8, 23, 9, 24)
    # raised arms with claws
    s.poly([(8, 13), (3, 8), (5, 6), (11, 11)], c); s.poly([(23, 13), (28, 8), (26, 6), (20, 11)], c)
    s.px([(2, 6), (3, 5), (5, 4), (26, 4), (28, 5), (29, 6)], IVORY)
    s.ell(11, 3, 12 + 2, 6, c); s.ell(18, 3, 21, 6, c)
    s.ell(10, 4, 21, 14, c)
    s.ell(13, 8, 18, 13, (170, 130, 96))
    s.px([(15, 8), (16, 8)], DARK); s.rect(14, 11, 17, 12, (120, 30, 40)); s.px([(14, 11), (17, 11)], IVORY)
    eye = s.lit((255, 90, 50))
    s.px([(13, 7), (18, 7)], eye)
    s.line([(11, 17), (13, 20)], (190, 150, 140))
    return s.finish()


@reg('owlbear')
def owlbear(r):
    s = Sprite()
    c, fe = (128, 96, 64), (196, 170, 120)
    upright(s, c, fe, 8, 23, 10, 24)
    for y in (16, 19, 22):
        s.px([(13, y), (16, y), (19, y)], c)                    # breast feathers
    s.poly([(8, 13), (4, 18), (5, 22), (10, 17)], c); s.poly([(23, 13), (27, 18), (26, 22), (21, 17)], c)
    s.px([(4, 23), (5, 23), (6, 23), (25, 23), (26, 23), (27, 23)], IVORY)
    # owl head: facial disc, great round eyes, hooked beak, ear tufts
    s.poly([(10, 7), (9, 2), (13, 5)], c); s.poly([(21, 7), (22, 2), (18, 5)], c)
    s.ell(9, 3, 22, 14, c)
    s.ell(10, 5, 15, 11, fe); s.ell(16, 5, 21, 11, fe)
    eye = s.lit((255, 200, 50))
    s.rect(12, 7, 13, 8, eye); s.rect(18, 7, 19, 8, eye); s.px([(13, 8), (18, 8)], DARK)
    s.poly([(15, 9), (16, 9), (17, 11), (15, 13), (14, 11)], GOLD)
    return s.finish()


# ------------------------------------------------------------------ boar and cattle
@reg('calydonian_boar')
def calydonian_boar(r):
    s = Sprite()
    c, dk = (116, 92, 78), (64, 48, 50)
    d = dims(2, x0=3, x1=21, y0=11, y1=22, lw=4, hx=23, hy=15)
    s.line([(4, 15), (2, 13), (3, 11)], dk)
    quad(s, c, d, feet=(40, 30, 34), belly=dk)
    for x in range(5, 21, 3):
        s.poly([(x, 12), (x + 1, 7), (x + 3, 12)], dk)          # ridge of bristles
    s.poly([(19, 12), (18, 6), (22, 11)], dk)
    s.ell(16, 10, 27, 23, c)
    s.rect(23, 16, 29, 21, c); s.rect(29, 16, 30, 21, (214, 140, 140)); s.px([(30, 18)], DARK)
    s.line([(23, 22), (28, 22)], dk)
    s.line([(24, 22), (24, 17)], IVORY, 2); s.px([(25, 16), (25, 15), (26, 14)], IVORY)   # great tusks
    s.line([(27, 21), (27, 18)], IVORY)
    s.rect(21, 14, 22, 15, s.lit((255, 70, 40)))
    s.line([(9, 15), (12, 12)], WOOD); s.px([(13, 11)], s.lit((240, 240, 250)))   # a hunter's spear, broken off
    return s.finish()


@reg('bonnacon')
def bonnacon(r):
    s = Sprite()
    c = (150, 100, 62)
    d = dims(1, x0=7, x1=22, y0=13, y1=22, lw=3, hx=24, hy=13)
    # the burning dung it sprays behind as it flees
    f1, f2 = s.lit(FIRE), s.lit(FIRE2)
    s.poly([(7, 18), (2, 16), (1, 20), (3, 24), (6, 22)], f1); s.px([(3, 19), (4, 20), (2, 26), (5, 27)], f2)
    s.line([(8, 14), (6, 12), (5, 14)], sh(c, -2))
    quad(s, c, d, feet=DARK, belly=sh(c, -1))
    s.ell(14, 9, 23, 18, (96, 60, 40))                          # horse's mane
    head_bull(s, 24, 13, c, DARK, horn=(226, 214, 180), horns='curl', muz=(200, 150, 130))
    return s.finish()


@reg('catoblepas')
def catoblepas(r):
    s = Sprite()
    c, dk = (124, 104, 80), (70, 56, 56)
    d = dims(1, x0=3, x1=19, y0=10, y1=20, lw=3, hx=25, hy=23)
    s.line([(4, 14), (2, 17), (2, 21)], dk); s.px([(2, 22), (1, 22)], dk)
    quad(s, c, d, feet=DARK, belly=dk)
    for x in range(6, 17, 3):
        s.px([(x, 10), (x + 1, 9), (x + 1, 10)], dk)
    # the neck too weak to lift the heavy head
    tube(s, [(18, 13), (23, 13), (25, 18)], c, 4, 3)
    s.ell(20, 19, 28, 27, c)
    s.rect(25, 24, 29, 27, (160, 120, 110)); s.px([(28, 26)], DARK)
    s.line([(21, 20), (19, 17)], IVORY, 2); s.line([(26, 19), (28, 16)], IVORY, 2)
    s.poly([(20, 19), (27, 19), (25, 23), (21, 24)], dk)        # shaggy mane over the eyes
    s.px([(24, 23)], s.lit((255, 60, 60)))
    s.px([(29, 29), (30, 28), (27, 29)], s.lit((140, 220, 90)))   # the breath that withers grass
    return s.finish()


@reg('secret_cow')
def secret_cow(r):
    s = Sprite()
    c, patch = (244, 240, 232), (58, 50, 56)
    d = dims(1, x0=5, x1=21, y0=13, y1=22, lw=3, hx=23, hy=13)
    s.line([(6, 15), (3, 17), (3, 22)], c); s.rect(2, 22, 4, 24, patch)
    quad(s, c, d, feet=patch)
    s.ell(8, 14, 13, 19, patch); s.ell(15, 16, 19, 21, patch); s.px([(6, 18), (7, 19)], patch)
    s.rect(11, 22, 14, 24, PINK)                                # udder
    head_bull(s, 23, 13, c, DARK, horn=(230, 220, 190), horns='small', muz=PINK)
    s.rect(19, 9, 21, 11, patch)
    s.px([(22, 12), (25, 12)], DARK); s.px([(22, 11), (25, 11)], WHITE)
    s.line([(18, 15), (20, 18)], RED, 1); s.rect(19, 19, 21, 21, GOLD); s.px([(20, 22)], DARK)   # bell
    return s.finish()


def cow_warrior(s, hide, patch, horn, eye, armor=None):
    """A cow on its hind legs with a polearm: the Hell Bovine."""
    s.rect(11, 22, 14, 27, hide); s.rect(18, 22, 21, 27, hide)
    s.rect(10, 28, 14, 29, DARK); s.rect(18, 28, 22, 29, DARK)
    s.ell(9, 12, 23, 24, hide)
    s.ell(12, 16, 16, 21, patch); s.px([(19, 15), (20, 16), (20, 15)], patch)
    if armor:
        s.rect(10, 20, 22, 23, armor)
    s.rect(6, 14, 9, 21, hide); s.rect(23, 14, 26, 20, hide)
    s.rect(6, 21, 9, 22, DARK); s.rect(23, 20, 26, 21, DARK)
    # head
    s.line([(12, 6), (9, 4), (9, 1)], horn, 2); s.line([(20, 6), (23, 4), (23, 1)], horn, 2)
    s.poly([(11, 8), (8, 9), (11, 10)], hide); s.poly([(21, 8), (24, 9), (21, 10)], hide)
    s.ell(11, 4, 21, 13, hide)
    s.rect(13, 10, 19, 14, PINK); s.px([(14, 12), (18, 12)], DARK)
    s.px([(13, 8), (19, 8)], eye)
    # bardiche
    s.line([(27, 3), (27, 28)], WOOD, 2)
    s.poly([(28, 2), (31, 4), (31, 10), (28, 12)], STEEL)


@reg('hell_bovine')
def hell_bovine(r):
    s = Sprite()
    cow_warrior(s, (186, 120, 76), (240, 226, 200), IVORY, s.lit((255, 60, 40)))
    return s.finish()


@reg('cow_king')
def cow_king(r):
    s = Sprite()
    gold = s.lit((255, 220, 70))
    # royal purple cape behind
    s.poly([(7, 12), (25, 12), (27, 27), (5, 27)], (110, 40, 130))
    s.line([(6, 27), (26, 27)], IVORY)
    cow_warrior(s, (236, 230, 222), (70, 56, 60), (236, 190, 60), s.lit((120, 220, 255)), armor=(226, 178, 62))
    # crown between the gilded horns
    s.rect(12, 3, 20, 5, GOLD); s.px([(12, 2), (14, 2), (16, 1), (18, 2), (20, 2)], GOLD)
    s.px([(16, 4)], s.lit((255, 60, 80)))
    s.px([(9, 1), (23, 1)], gold)
    bolt(s, 3, 3, BOLT); bolt(s, 4, 16, BOLT, True)
    return s.finish()


# ------------------------------------------------------------------ rats
def rat(s, c, big, eye, belly):
    d = dims(0, x0=8, x1=20, y0=18, y1=25, lw=2, hx=22, hy=21) if not big else \
        dims(0, x0=5, x1=21, y0=14, y1=24, lw=3, hx=23, hy=19)
    x0, y0 = d['x0'], d['y0']
    tube(s, [(x0 + 1, y0 + 5), (x0 - 3, y0 + 8), (x0 - 2, y0 + 2), (max(2, x0 - 4), y0 - 2)], PINK, 2, 1)
    quad(s, c, d, belly=belly, feet=PINK)
    neck(s, d, c)
    head_rat(s, d['hx'], d['hy'], c, eye)
    return d


@reg('giant_rat')
def giant_rat(r):
    s = Sprite()
    rat(s, (138, 130, 126), False, DARK, (196, 186, 176))
    return s.finish()


@reg('dire_rat')
def dire_rat(r):
    s = Sprite()
    c = (112, 74, 44)
    d = rat(s, c, True, s.lit((255, 70, 50)), (160, 120, 80))
    for x in (8, 11, 14, 17):
        s.poly([(x, 15), (x + 1, 12), (x + 2, 15)], (70, 44, 30))   # hackles
    s.px([(28, 22), (28, 23)], IVORY)
    return s.finish()


# ------------------------------------------------------------------ peryton
@reg('peryton')
def peryton(r):
    s = Sprite()
    c, fe = (70, 130, 100), (40, 84, 80)
    d = dims(1, x0=7, x1=20, y0=15, y1=21, lw=2, hx=23, hy=10)
    # it casts the shadow of a man
    s.shadow = False
    s.rect(9, 29, 22, 30, (20, 16, 26)); s.ell(22, 28, 26, 31, (20, 16, 26)); s.rect(13, 28, 15, 28, (20, 16, 26))
    wing(s, 15, 16, fe, 'feather', 1.2, tip=(120, 190, 150))
    s.poly([(7, 17), (3, 20), (4, 23), (9, 20)], fe)            # tail feathers
    quad(s, c, d, feet=DARK, belly=(150, 200, 170))
    tube(s, [(19, 17), (21, 14), (22, 11)], c, 3, 3)
    s.ell(20, 7, 26, 12, c); s.rect(25, 9, 29, 11, c); s.px([(29, 9)], DARK)
    s.px([(24, 9)], s.lit((255, 220, 90)))
    ant = (220, 206, 170)
    s.line([(22, 7), (21, 4), (19, 2)], ant); s.line([(21, 4), (23, 2)], ant); s.line([(21, 5), (18, 5)], ant)
    s.line([(24, 7), (26, 4), (25, 1)], ant); s.line([(26, 4), (28, 3)], ant)
    return s.finish()
