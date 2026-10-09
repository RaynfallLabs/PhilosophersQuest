"""Individually drawn weapons: the named legends, the ammunition, and strays.

Offline tooling.  N maps record id -> function(rec) -> 32x32 RGBA image.
"""
import math

from wlib import (W, Mat, MATS, P, H, EPS, sword, haft, bit, spike, leaf, arrow, bolt, _bow, r_sling, r_lockpick,
                  WOOD, LEATHER, BRASS, DKIRON, STONE, L)
from core import shade, BONE, STRING

N = {}
GOLD = (232, 186, 62)
DGOLD = (190, 138, 44)
SILV = (214, 220, 236)
ASH = (214, 190, 146)
BRONZE = (196, 132, 56)
STEELC = (190, 200, 218)
WHITE = (255, 255, 255)


def n(*ids):
    def deco(f):
        def run(rec):
            s = W()
            f(s)
            return s.finish()
        for i in ids:
            N[i] = run
        return f
    return deco


def mk(base, pats=(('streak', 'hi'),), **kw):
    return Mat(base, pats, **kw)


def aura(s, u0, u1, hw, col, taper=2.0, bend=None, grow=0.5):
    """A one-step rim of light around a blade (paint before the blade)."""
    c = s.lit(col)
    s.prof(u0, u1 + grow, lambda u: min(hw, (u1 - u) / taper) + grow, c, bend=bend)


def flames(s, u0, u1, hw, c_out, c_in, taper=2.0, amp=1.6, ph=0.0, cv=0.0):
    co, ci = s.lit(c_out), s.lit(c_in)

    def col(u, v, x, y):
        w = max(0.0, min(hw, (u1 - u) / taper))
        q = abs(v) - w
        h = amp * max(0.0, math.sin(u * 1.3 + ph + (2.1 if v > 0 else 0.0))) ** 1.5 + 0.3
        if q <= 0 or q > h:
            return None
        return ci if q <= h * 0.45 else co
    s.prof(u0, u1 + 1.0, lambda u: hw + amp + 1.0, col, cv=cv)


def zap(s, pts, col, core=None):
    c = s.lit(col)
    s.line(pts, c)
    if core:
        s.px(pts[1:-1], s.lit(core))


def spark(s, x, y, col):
    c = s.lit(col)
    s.px([(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], c)


def taper_curve(s, pts, th0, th1, col):
    k = len(pts) - 1
    for i in range(k):
        s.curve(pts[i:i + 2], th0 + (th1 - th0) * i / max(1, k - 1), col)


def viking(s, M, **kw):
    d = dict(g=6.5, tip=25.0, hw=1.5, span=2.5, gt=1.0, grip0=2.5, taper=2.6, pommel='lobed', fuller=True)
    d.update(kw)
    sword(s, M, **d)


# ================================================================= swords
@n('anduril')
def _(s):
    sword(s, mk((206, 216, 234)), g=6.5, tip=26.5, span=3.5, k=0.3, guard=SILV, grip=(44, 44, 62), pcol=SILV)
    s.upx([(u, 0) for u in (9, 11.5, 14, 16.5, 19, 21.5, 24)], s.lit((255, 246, 170)))


@n('brisingr')
def _(s):
    flames(s, 8.0, 25.5, 1.0, (255, 110, 30), (255, 214, 90), amp=2.2)
    sword(s, mk((226, 92, 36), [('heart', L((255, 226, 120)))]), g=6.5, tip=25.5, span=3.0,
          guard=DKIRON, grip=(60, 40, 40), pcol=(255, 150, 50))


@n('vulcans_brand')
def _(s):
    hot1, hot2 = s.lit((255, 128, 36)), s.lit((255, 224, 120))

    def col(u, v, x, y):
        return (78, 66, 70) if u < 10 else (150, 52, 40) if u < 14.5 else hot1 if u < 21 else hot2
    sword(s, mk((90, 80, 80)), g=6.5, tip=25.0, hw=1.5, span=3.0, gt=1.0, blade=col, guard=(70, 62, 66),
          grip=(50, 40, 40), pommel='big', taper=2.4)
    s.px([(26, 2), (29, 6), (22, 3)], s.lit((255, 170, 60)))


@n('broken_gram')
def _(s):
    M = mk((160, 170, 204))
    viking(s, M, tip=13.5, style='blunt', guard=DGOLD)
    s.erase(lambda u, v: u > 11.5 + (v + 1.5) * 0.7 + (0.5 if int(round(v * 2)) % 2 else 0))
    t = M.tex(s)
    s.fn(lambda u, v: 15.0 + abs(v) * 0.6 <= u <= 18.5 - (v + 1.5) * 0.5 and -1.5 <= v - 1.0 <= 1.5, t)
    s.fn(lambda u, v: 20.5 + (1.5 - v) * 0.5 <= u <= 25.5 and abs(v + 0.5) <= min(1.5, (25.5 - u) / 2.2), t)
    s.px([P(14.5, -1.5), P(19.5, 2.5)], s.lit((190, 220, 255)))


@n('cadmus_sword')
def _(s):
    sword(s, mk((218, 152, 62), [('streak', (255, 220, 140))]), g=7.5, tip=25.5, hw=1.5, span=3.0, gt=1.0,
          guard=(96, 110, 96), grip=(50, 40, 44), pommel='none', grip0=3.5, taper=2.4)
    s.erase(lambda u, v: (abs(u - 14.0) < 0.6 and v > 0.9) or (abs(u - 19.0) < 0.6 and v < -0.9))
    s.fn(lambda u, v: 0.5 <= u <= 3.5 and abs(v) <= (u - 0.3) * 0.55, (244, 238, 220))      # dragon's tooth


@n('caladbolg')
def _(s):
    for i, c in enumerate(((255, 90, 80), (255, 210, 80), (110, 230, 120), (90, 160, 255))):
        R = 11.0 + i * 1.2
        pts = [(6 + R * math.cos(math.radians(a)), -R * math.sin(math.radians(a))) for a in range(14, 58, 4)]
        s.curve(pts, 0.4, s.lit(c))
    sword(s, mk((176, 240, 206), [('streak', (236, 255, 244))]), g=7.5, tip=26.5, hw=1.5, span=5.0, gt=1.0,
          grip0=1.5, taper=1.5, pommel='big', guard=(120, 150, 150), grip=(40, 80, 80))


@n('caliburn')
def _(s):
    stone, moss = (128, 128, 136), (96, 140, 84)
    s.rect(15, 9, 17, 22, (196, 198, 226))
    s.rect(11, 8, 21, 9, GOLD)
    s.rect(15, 3, 17, 7, (110, 60, 50))
    s.rect(14, 1, 18, 2, GOLD)
    s.poly([(5, 29), (7, 22), (12, 19), (20, 20), (25, 23), (27, 29)], stone)
    s.line([(9, 24), (13, 22), (15, 25)], (88, 88, 100))
    s.px([(8, 22), (9, 21), (10, 21), (21, 21), (22, 22), (12, 20)], moss)
    s.postxy([(15, 11), (15, 13), (15, 15)], WHITE)


@n('chainsaw_prosthetic')
def _(s):
    body, eng, bar, tooth = (222, 92, 40), (70, 70, 82), (192, 194, 204), (58, 58, 70)
    s.fn(lambda u, v: 9.5 <= u <= 25.5 and abs(v) <= 2.0 and (u - 25.5) ** 2 / 4 + 0 <= 99
         and abs(v) <= min(2.0, (26.0 - u) * 1.5) and (abs(v) < 1.6 or int(round(2 * u)) % 3 != 0), tooth)
    s.prof(9.5, 24.5, lambda u: min(1.0, (24.8 - u) * 1.5), bar)
    s.tint(lambda u, v: abs(v) < 0.1 and 11 <= u <= 22, 'lo')
    s.box(3.0, 10.0, -3.5, 3.5, body)
    s.box(3.0, 6.5, -3.5, -1.0, eng)
    s.curve([(4.5, -3.5), (6.0, -5.5), (9.0, -5.0), (10.0, -3.0)], 0.5, (40, 40, 50))     # top handle
    s.box(0.5, 3.0, -2.5, 2.5, (150, 100, 70))                                           # arm cuff
    s.box(2.0, 2.5, -2.5, 2.5, (90, 90, 104))
    s.post([(8.0, 2.0)], WHITE)


@n('chandrahasa')
def _(s):
    t = mk((204, 210, 248), [('streak', WHITE)]).tex(s)
    s.fn(lambda u, v: u >= 6.5 and (u - 13) ** 2 + (v - 5) ** 2 <= 100 and (u - 12) ** 2 + (v - 8.5) ** 2 > 118, t)
    s.box(1.5, 7.0, -1.5, -0.5, (60, 70, 130))
    s.box(6.5, 7.0, -3.0, 1.0, GOLD)
    s.disc(1.0, -1.0, 1.0, GOLD)
    spark(s, 23, 8, (236, 244, 255))
    s.px([P(13, -4.5), P(17, -3.5)], s.lit((236, 244, 255)))


@n('chandrahas')
def _(s):
    g, tip = 6.5, 23.0
    bf = lambda u: -3.0 * max(0.0, (u - g) / (tip - g)) ** 2
    M = mk((178, 206, 252), [('streak', WHITE)])
    aura(s, g + 1, tip, 1.5, (120, 170, 255), bend=bf, taper=1.2)
    s.prof(g, tip, lambda u: min(0.75 + 1.0 * (u - g) / (tip - g), (tip - u) / 1.2), M.tex(s), bend=bf)
    s.box(2.5, g, -0.5, 0.5, (40, 50, 110))
    s.box(g, g + 0.5, -2.5, 2.5, SILV)
    s.disc(2.0, 0, 1.0, SILV)


@n('chrysaor')
def _(s):
    sword(s, mk((244, 200, 52), [('streak', (255, 248, 190))]), g=7.0, tip=26.0, hw=1.5, style='leaf', span=3.5,
          gt=1.0, k=0.25, guard=DGOLD, grip=(150, 90, 30), pommel='big', pcol=DGOLD, grip0=2.5, taper=1.8)
    s.upx([(7.5, 0)], s.lit((255, 70, 60)))
    spark(s, 25, 9, (255, 255, 220))


@n('curtana')
def _(s):
    sword(s, mk(STEELC, [('streak', 'hi2')]), g=7.0, tip=22.5, hw=1.5, style='blunt', span=4.0, gt=1.0,
          guard=GOLD, grip=(130, 40, 50), pommel='big', pcol=GOLD, grip0=2.5, fuller=True)
    s.erase(lambda u, v: u > 22.0 and v < -1.0)


@n('durendal')
def _(s):
    sword(s, mk((230, 234, 246), [('streak', WHITE)]), g=8.0, tip=26.5, hw=1.5, span=5.0, gt=1.0, k=0.15,
          taper=1.5, guard=GOLD, grip=(196, 150, 60), pommel='big', pcol=GOLD, grip0=2.0, fuller=True)
    s.upx([(1.5, 0)], s.lit((255, 60, 70)))
    s.upx([(8.5, 0)], s.lit((255, 250, 200)))
    spark(s, 24, 9, WHITE)


@n('excalibur')
def _(s):
    aura(s, 8.0, 26.5, 1.0, (255, 240, 150))
    sword(s, mk((238, 242, 250), [('streak', WHITE)]), g=7.0, tip=26.5, hw=1.0, span=4.0, gt=1.0, k=-0.25,
          guard=GOLD, grip=(46, 66, 160), pommel='big', pcol=GOLD, grip0=2.5)
    s.upx([(7.5, 0)], s.lit((110, 200, 255)))
    s.upx([(2.0, 0)], s.lit((110, 200, 255)))


@n('fragarach')
def _(s):
    aura(s, 8.0, 26.0, 0.5, (150, 235, 255))
    sword(s, mk((70, 160, 232), [('streak', (210, 244, 255))]), g=7.0, tip=26.0, hw=0.5, span=3.0, k=0.5,
          guard=SILV, grip=(30, 80, 96), pcol=SILV, grip0=2.5)


@n('gram')
def _(s):
    viking(s, mk((200, 222, 255), [('streak', WHITE)]), guard=GOLD, grip=(80, 54, 40), tip=25.5)
    s.upx([(11, 0), (14, 0), (17, 0)], s.lit((130, 200, 255)))


@n('hofud')
def _(s):
    viking(s, mk((224, 230, 244), [('streak', WHITE)]), guard=SILV, grip=(60, 70, 110), pommel='big', pcol=GOLD,
           grip0=3.0)
    for i, c in enumerate(((255, 80, 80), (255, 200, 70), (90, 220, 110), (80, 170, 255), (190, 110, 255))):
        s.post([(6.5 + 0.5 * (i % 2), -2.0 + i)], c)
    s.post([(2.5, -0.5), (2.5, 0.5)], (60, 40, 30))


@n('hrunting')
def _(s):
    viking(s, mk((70, 72, 100), [('damascus', (150, 154, 196))]), guard=(150, 154, 170), grip=(60, 44, 40),
           fuller=False)


@n('naegling')
def _(s):
    viking(s, mk((150, 146, 138), [('pits', 'lo2')]), guard=(150, 122, 70), grip=(90, 70, 56), fuller=False)
    s.erase(lambda u, v: abs(u - 9.5) <= 0.6 and v > 0.4)
    s.post([(16.0, -1.0), (16.5, -0.5), (16.5, 0.0), (17.0, 0.5), (17.0, 1.0)], (50, 46, 52))


@n('skofnung')
def _(s):
    viking(s, mk((124, 134, 142), [('heart', L((196, 255, 220)))]), guard=(70, 74, 86), grip=(232, 226, 206),
           fuller=False)


@n('tyrfing')
def _(s):
    sword(s, mk((92, 96, 116), [('heart', L((255, 56, 56))), ('streak', (176, 180, 204))]), g=7.5, tip=26.5,
          hw=1.5, span=4.5, gt=1.0, taper=1.5, guard=GOLD, grip=(70, 30, 30), pommel='big', pcol=GOLD, grip0=1.5)
    s.px([(28, 6), (22, 2)], s.lit((255, 56, 56)))


@n('mistilteinn')
def _(s):
    viking(s, mk((186, 240, 196), [('streak', WHITE)]), guard=(90, 70, 50), grip=(60, 44, 36), fuller=False)
    s.tint(lambda u, v: v > 0.9 and u > 8, (60, 50, 90))
    leafc = (70, 150, 70)
    s.disc(8.5, -2.5, 1.0, leafc)
    s.disc(8.5, 2.5, 1.0, leafc)
    s.disc(10.0, -1.5, 0.75, leafc)
    s.upx([(9.5, 1.5), (9.0, -1.0), (10.5, 0.0)], s.lit((250, 250, 236)))


@n('hunt_captains_sword')
def _(s):
    ghost = s.lit((170, 190, 238))
    sword(s, mk((170, 190, 238)), g=6.5, tip=26.0, hw=1.0, span=3.5, blade=ghost, guard=(64, 64, 86),
          grip=(48, 56, 90), pcol=(64, 64, 86), grip0=2.0)
    s.upx([(12, -2.5), (13, -3.0), (17, 2.5), (18.5, 3.0), (21, -2.5)], s.lit((210, 224, 255)))


@n('stormbringer')
def _(s):
    sword(s, mk((30, 28, 40), [('rune', L((255, 44, 50))), ('streak', (90, 84, 120))]), g=7.5, tip=26.5, hw=1.5,
          span=5.5, gt=1.0, k=0.25, taper=1.5, guard=(58, 48, 72), grip=(40, 30, 40), pommel='big',
          pcol=(58, 48, 72), grip0=1.5)
    s.upx([(1.0, 0)], s.lit((255, 44, 50)))


@n('glamdring')
def _(s):
    aura(s, 9.0, 26.5, 1.0, (120, 196, 255))
    sword(s, mk((216, 228, 244), [('streak', WHITE)]), g=8.0, tip=26.5, hw=1.0, span=3.5, k=0.45, gt=1.0,
          guard=GOLD, grip=(60, 80, 130), pcol=GOLD, grip0=2.0)
    s.upx([(8.5, 0)], s.lit(WHITE))


@n('joyeuse')
def _(s):
    hues = ((255, 168, 168), (255, 224, 150), (186, 240, 170), (160, 222, 255), (214, 180, 255))
    sword(s, mk(GOLD), g=7.0, tip=26.0, hw=1.0, span=3.5, gt=1.0, blade=lambda u, v, x, y: hues[int(u / 2.6) % 5],
          guard=GOLD, grip=(150, 40, 60), pommel='big', pcol=GOLD, grip0=2.5)
    s.upx([(2.0, 0)], s.lit(WHITE))
    spark(s, 26, 8, WHITE)


@n('khopesh_of_anubis')
def _(s):
    M = mk((54, 54, 80), [('streak', (130, 130, 176))])
    t = M.tex(s)
    s.prof(7.0, 13.0, 0.75, t)
    taper_curve(s, [(12.5, 0), (15.0, -2.0), (18.5, -3.0), (21.5, -2.0), (23.5, 0.5), (24.0, 2.0)], 1.3, 0.5, t)
    s.box(2.0, 7.0, -0.5, 0.5, (40, 36, 48))
    for u in (3.0, 5.0):
        s.box(u, u + 0.5, -0.5, 0.5, GOLD)
    s.box(7.0, 7.5, -1.5, 1.5, GOLD)
    s.disc(1.5, 0, 1.0, GOLD)


@n('kladenets')
def _(s):
    sw = s.lit((255, 150, 250))
    s.curve([(10, -3.5), (15, -4.5), (20, -4.0)], 0.3, sw)
    s.curve([(9, 3.5), (13, 4.5), (17, 4.5)], 0.3, sw)
    s.curve([(13, -6.5), (17, -7.0)], 0.3, sw)
    sword(s, mk((250, 216, 250), [('streak', WHITE)]), g=6.5, tip=26.0, hw=1.0, span=3.5, k=-0.3, guard=GOLD,
          grip=(170, 40, 60), pcol=GOLD, grip0=2.5)
    spark(s, 27, 5, WHITE)


@n('kusanagi')
def _(s):
    sword(s, mk((150, 236, 236), [('streak', WHITE)]), g=7.5, tip=25.5, hw=1.5, style='leaf', span=1.5, gt=1.0,
          guard=GOLD, grip=(230, 226, 210), pommel='ring', pcol=GOLD, grip0=3.0, taper=2.0)
    s.px([(6, 5), (6, 6), (11, 2), (11, 3), (3, 11), (3, 12), (9, 10), (9, 11)], s.lit((150, 240, 255)))


@n('oathkeeper_sword')
def _(s):
    sword(s, mk((186, 196, 216), [('streak', 'hi2')]), g=6.5, tip=26.0, hw=1.0, span=4.0, gt=1.0,
          guard=(150, 156, 176), grip=(46, 76, 150), pcol=(150, 156, 176), grip0=2.0, fuller=True)
    s.post([(7.0, -2.5), (7.0, -1.5), (7.0, 1.5), (7.0, 2.5)], (70, 74, 96))


@n('pelops_sword')
def _(s):
    sword(s, mk((158, 134, 70), [('dots7', (92, 160, 130)), ('streak', 'hi')]), g=8.5, tip=25.5, hw=1.5,
          style='leaf', span=2.5, gt=1.0, guard=(140, 104, 50), grip=(240, 232, 208), pommel='big',
          pcol=(140, 104, 50), grip0=2.5, taper=2.0, wrap=False)


@n('sword_of_damocles')
def _(s):
    s.line([(16, 1), (16, 6)], (226, 208, 160))
    s.rect(15, 6, 17, 7, GOLD)
    s.rect(15, 8, 17, 11, (130, 40, 50))
    s.rect(10, 12, 22, 13, GOLD)
    s.poly([(14, 14), (18, 14), (18, 25), (16, 30), (14, 25)], (236, 204, 84))
    s.px([(11, 12), (21, 12)], s.lit((255, 70, 70)))
    s.px([(16, 12)], s.lit((110, 200, 255)))
    s.postxy([(15, 15), (15, 17), (15, 19), (15, 21)], (255, 246, 190))


@n('sword_of_michael')
def _(s):
    flames(s, 9.0, 25.5, 1.0, (255, 196, 70), (255, 240, 150), amp=1.4)
    white = s.lit((255, 255, 228))
    wing = (244, 244, 250)
    s.fn(lambda u, v: abs(v) <= 5.5 and 7.0 - 0.8 * abs(v) <= u <= 9.0 - 0.3 * abs(v), wing)
    sword(s, mk(GOLD), g=8.0, tip=25.5, hw=1.0, span=0, blade=white, grip=GOLD, pommel='big', pcol=GOLD,
          grip0=2.5, wrap=False)
    s.upx([(8.5, 0)], s.lit((110, 200, 255)))


@n('witcher_silver_blade')
def _(s):
    sword(s, mk((226, 230, 242), [('rune', L((140, 210, 255))), ('streak', WHITE)]), g=9.0, tip=26.5, hw=1.0,
          span=3.0, k=0.4, guard=(96, 100, 120), grip=(54, 42, 40), pcol=(96, 100, 120), grip0=2.0)


@n('zireael')
def _(s):
    sword(s, mk((222, 232, 252), [('streak', WHITE)]), g=7.5, tip=26.0, hw=0.5, span=3.0, k=0.8, gt=1.0,
          guard=(190, 140, 70), grip=(124, 44, 44), pommel='cap', pcol=(190, 140, 70), grip0=2.0)
    s.post([(11.0, 0), (11.5, -0.5), (11.5, 0.5)], (50, 70, 150))
    s.upx([(8.0, 0)], s.lit((120, 200, 255)))


@n('zulfiqar')
def _(s):
    bf = lambda u: -1.5 * max(0.0, (u - 7.0) / 17.0) ** 2
    sword(s, mk((198, 228, 184), [('streak', WHITE)]), g=7.0, tip=24.0, hw=1.5, style='blunt', bend=bf, span=3.5,
          k=-0.4, guard=GOLD, grip=(40, 110, 70), pommel='big', pcol=GOLD, grip0=2.5)
    s.erase(lambda u, v: u > 19.5 and abs(v - bf(u)) <= (u - 19.5) * 0.4)
    s.erase(lambda u, v: u > 22.0 and abs(v - bf(u)) > 1.5 - (u - 22.0) * 0.6)


@n('soul_reaver')
def _(s):
    bf = lambda u: 0.75 * math.sin((u - 7.0) * 1.05)
    sword(s, mk((80, 52, 170), [('heart', L((204, 170, 255)))]), g=7.0, tip=25.5, hw=1.5, bend=bf, span=3.5,
          k=-0.5, gt=1.0, taper=1.6, guard=BONE, grip=(30, 26, 40), pcol=(30, 26, 40), grip0=2.0)
    s.disc(7.5, 0, 1.5, BONE)
    s.post([(7.5, -0.5), (7.5, 0.5)], (30, 20, 50))


@n('harpe')
def _(s):
    M = mk((178, 212, 248), [('streak', WHITE)])
    sword(s, M, g=6.5, tip=24.5, hw=1.0, span=2.5, gt=1.0, guard=GOLD, grip=(96, 60, 40), pcol=GOLD, grip0=2.5)
    taper_curve(s, [(17.5, -1.0), (20.0, -2.5), (20.5, -4.5), (19.0, -6.0), (17.0, -6.5)], 1.0, 0.4, M.tex(s))
    s.fn(lambda u, v: 4.5 <= u <= 6.5 and 1.0 <= abs(v) <= 1.0 + (u - 4.5) * 1.2, (244, 244, 250))   # Hermes' wings


@n('cronus_scythe')
def _(s):
    haft(s, 0.5, 22.5, (84, 70, 96))
    M = mk((132, 104, 164), [('streak', (214, 190, 240))])
    taper_curve(s, [(22.0, 0.5), (22.0, -2.5), (20.0, -5.0), (17.0, -6.5), (13.5, -7.5), (10.5, -7.5)],
                1.5, 0.4, M.tex(s))
    s.box(20.5, 21.0, -0.5, 1.0, GOLD)
    s.upx([(19.5, -3.0), (16.0, -5.5), (12.5, -6.5)], s.lit((204, 100, 255)))
    s.box(8.0, 8.5, -2.0, 0.0, (84, 70, 96))


@n('war_scythe')
def _(s):
    haft(s, 0.5, 14.5, WOOD)
    taper_curve(s, [(13.5, 0.25), (17.0, 0.25), (20.5, -0.5), (23.0, -1.5), (24.5, -2.5)], 1.2, 0.4,
                MATS['steel'].tex(s))
    s.box(13.0, 14.0, -0.5, 1.0, DKIRON)
    s.box(10.0, 10.5, -0.5, 1.0, DKIRON)


@n('talos_sickle')
def _(s):
    M = mk(BRONZE, [('streak', (250, 206, 120))])
    s.box(3.0, 10.0, -0.5, 0.5, (110, 70, 44))
    s.box(9.5, 10.5, -1.0, 1.0, (150, 96, 40))
    taper_curve(s, [(10.5, 0.5), (13.0, 3.5), (17.0, 5.0), (20.5, 3.5), (22.0, 0.0), (20.5, -3.0), (18.0, -4.5)],
                1.2, 0.4, M.tex(s))
    s.post([(13.5, 5.0), (16.0, 6.0), (19.0, 5.5), (21.5, 3.5), (23.0, 0.5)], (120, 70, 30))
    s.upx([(15.0, 3.5), (19.0, 3.5)], s.lit((255, 170, 60)))
    s.disc(2.5, 0, 1.0, (150, 96, 40))


@n('shamshir_e_zomorrodnegar')
def _(s):
    g, tip = 6.5, 23.0
    bf = lambda u: -3.5 * max(0.0, (u - g) / (tip - g)) ** 2
    em = s.lit((50, 236, 130))
    s.prof(g, tip, lambda u: min(0.75, (tip - u) / 1.5), mk((216, 238, 226), [('streak', WHITE)]).tex(s), bend=bf)
    s.box(2.5, g, -0.5, 0.5, (40, 96, 70))
    s.box(g, g + 0.5, -2.5, 2.5, GOLD)
    s.curve([(2.5, 0), (1.5, 0.5), (1.5, 1.5)], 0.6, GOLD)
    s.upx([(g, -2.5), (g, 2.5), (g + 0.5, 0), (4.5, 0)], em)
    s.px([P(11, bf(11)), P(15, bf(15)), P(19, bf(19))], em)


@n('sudarshana')
def _(s):
    fl, hot, gold = s.lit((255, 140, 40)), s.lit((255, 236, 130)), (240, 186, 60)
    for i in range(12):
        a = math.radians(i * 30 + 8)
        b = math.radians(i * 30 + 30)
        s.poly([(16 + 9 * math.cos(a), 16 + 9 * math.sin(a)), (16 + 13 * math.cos(b), 16 + 13 * math.sin(b)),
                (16 + 9 * math.cos(b - 0.1), 16 + 9 * math.sin(b - 0.1))], fl)
    s.sell(6, 6, 26, 26, gold)
    s.sell(9, 9, 23, 23, hot)
    s.sell(11, 11, 21, 21, (176, 110, 40))
    for i in range(8):
        a = math.radians(i * 45)
        s.line([(16, 16), (16 + 5 * math.cos(a), 16 + 5 * math.sin(a))], gold)
    s.sell(14, 14, 18, 18, hot)


# ================================================================ daggers
@n('akinakes_acrisius')
def _(s):
    sword(s, mk((204, 224, 208), [('streak', WHITE)]), g=10.5, tip=23.5, hw=2.0, style='leaf', span=0, grip0=6.5,
          taper=1.8, grip=(110, 70, 50), pommel='none')
    s.ell(10.5, 0, 1.0, 2.5, GOLD)
    s.box(5.5, 6.5, -2.0, 2.0, GOLD)


@n('carnwennan')
def _(s):
    s.upx([(14, 3.0), (16, 3.5), (18, 3.0), (13, -3.0), (16, -3.5)], (58, 46, 96))
    sword(s, mk((206, 250, 214), [('streak', WHITE)]), g=11.5, tip=22.0, hw=1.0, span=2.0, grip0=5.5, taper=2.6,
          guard=(150, 156, 170), grip=(250, 250, 246), pcol=(250, 250, 246), wrap=False, style='clip')
    s.upx([(22.0, -1.0)], s.lit((200, 255, 214)))


@n('echidna_fang')
def _(s):
    iv = mk((232, 222, 190), [('pits', 'lo')], kind='bone').tex(s)
    taper_curve(s, [(7.0, 1.5), (11.0, 1.0), (15.0, -0.5), (18.5, -2.5), (21.0, -4.5)], 2.3, 0.4, iv)
    s.box(5.5, 9.5, -1.5, 4.0, (140, 96, 162))
    s.tint(lambda u, v: 5.5 <= u <= 9.5 and int(round(2 * u)) % 3 == 0, 'lo')
    s.px([P(21.5, -5.0), (P(21.5, -5.0)[0], P(21.5, -5.0)[1] + 3)], s.lit((150, 240, 90)))


@n('wendigo_fang')
def _(s):
    t = (212, 230, 250)
    s.prof(8.5, 24.5, lambda u: max(0.0, (24.5 - u) * 0.17 + (1.0 if int(u) % 4 == 0 and u < 21 else 0.0)), t)
    s.tint(lambda u, v: abs(v + 0.5) < 0.1 and 10 < u < 22, WHITE)
    s.box(5.0, 9.5, -2.0, 2.0, (120, 92, 72))
    s.tint(lambda u, v: 5.0 <= u <= 9.5 and int(round(2 * u)) % 3 == 0, 'lo')
    s.px([(27, 8), (21, 3), (28, 12)], s.lit((200, 232, 255)))


@n('fragarach_the_whisperer')
def _(s):
    sword(s, mk((200, 236, 250), [('streak', WHITE)]), g=10.0, tip=24.5, hw=0.5, span=2.0, grip0=5.5,
          guard=(44, 48, 66), grip=(30, 34, 50), pcol=(44, 48, 66), taper=3.0)
    s.px([(20, 6), (22, 4), (26, 10)], s.lit((170, 240, 255)))


@n('penitents_blade')
def _(s):
    def col(u, v, x, y):
        return (128, 34, 40) if u > 19 - v else (88, 80, 84)
    sword(s, mk((88, 80, 84)), g=10.5, tip=23.5, hw=1.0, span=3.0, gt=1.0, grip0=5.5, taper=2.6, blade=col,
          guard=(60, 56, 62), grip=(170, 150, 116), pommel='ring', pcol=(60, 56, 62))


@n('ridill')
def _(s):
    sword(s, mk((186, 246, 232), [('streak', WHITE)]), g=10.0, tip=22.0, hw=2.0, span=3.0, gt=1.0, grip0=6.0,
          taper=2.6, guard=GOLD, grip=(110, 60, 40), pommel='big', pcol=GOLD)
    s.upx([(5.5, 0)], s.lit((255, 70, 60)))


# ================================================================= spears
def _spear(s, shaft, head, u_sock=19.0, tip=27.0, hw=1.5, collar=BRASS, h0=0.5, fall=2.2):
    haft(s, h0, u_sock + 1.0, shaft)
    leaf(s, head, u_sock, tip, hw=hw, fall=fall)
    if collar:
        s.box(u_sock - 1.0, u_sock, -0.5, 1.0, collar)


@n('achilles_spear')
def _(s):
    _spear(s, ASH, mk((214, 140, 56), [('streak', (255, 214, 130))]).tex(s), u_sock=17.5, hw=1.75, collar=(150, 96, 40), fall=3.2)
    s.prof(0.0, 2.5, lambda u: min(0.75, u * 0.5), (208, 130, 52), cv=0.25)
    s.box(8.0, 11.5, 0.0, 0.5, (110, 70, 44))


@n('aiglos')
def _(s):
    core = s.lit((226, 246, 255))
    _spear(s, (236, 238, 246), mk((160, 208, 250), [('heart', L((226, 246, 255)))]).tex(s), u_sock=17.0, hw=1.0,
           collar=SILV, fall=3.5)
    s.box(17.0, 17.5, -2.0, 2.5, SILV)
    s.px([(26, 7), (22, 3), (28, 11), (19, 6)], core)


@n('amenonuhoko')
def _(s):
    haft(s, 0.5, 18.0, (136, 40, 54))
    for i, u in enumerate((3.0, 7.0, 11.0, 15.0)):
        s.box(u, u + 0.5, -0.5, 1.0, GOLD)
        s.upx([(u + 2.0, 0.0)], s.lit(((255, 90, 90), (90, 230, 140), (110, 190, 255), (255, 220, 110))[i]))
    leaf(s, mk((178, 200, 255), [('streak', WHITE)]).tex(s), 17.0, 26.5, hw=2.0, fall=2.0)
    s.box(17.0, 18.0, -1.0, 1.5, GOLD)
    s.px([(29, 5), (29, 8), (27, 10), (29, 12)], s.lit((130, 220, 255)))


@n('bellerophon_lance')
def _(s):
    haft(s, 0.5, 22.5, (206, 196, 164))
    s.ell(7.0, 0.25, 1.0, 3.0, (170, 176, 192))                         # vamplate
    s.box(2.0, 5.5, 0.0, 0.5, LEATHER)
    lead = (98, 100, 116)
    s.disc(23.5, 0.25, 2.5, lead)
    s.prof(25.0, 27.0, lambda u: (27.0 - u) * 0.5, lead, cv=0.25)
    s.post([(23.0, -1.0), (23.5, -1.5), (22.5, -0.5)], (176, 178, 194))
    s.px([(29, 9), (29, 11)], lead)                                     # a drip of molten lead


def _barbs(s, col, us, reach=2.5):
    for u in us:
        for side in (1, -1):
            s.fn(lambda uu, v, u=u, side=side: 0.5 <= side * (v - 0.25) <= reach
                 and u - (side * (v - 0.25)) * 1.0 - 0.75 <= uu <= u - (side * (v - 0.25)) * 1.0 + 0.25, col)


@n('gae_bolg_fragment')
def _(s):
    s.box(4.0, 15.0, 0.0, 0.5, (120, 62, 56))
    s.erase(lambda u, v: u < 5.0 and v > 0.2)
    c = (230, 212, 186)
    _barbs(s, c, (18.0, 21.0, 24.0), reach=3.0)
    leaf(s, mk(c, [('pits', (176, 80, 66))], kind='bone').tex(s), 14.0, 27.0, hw=1.0, fall=3.0)
    s.box(12.5, 14.5, -0.5, 1.0, (150, 126, 96))
    s.tint(lambda u, v: 12.5 <= u <= 14.5 and int(round(2 * u)) % 2 == 0, 'lo')


@n('gae_bulg')
def _(s):
    haft(s, 0.5, 15.0, (60, 86, 76))
    c = (164, 232, 190)
    _barbs(s, c, (16.5, 18.5, 20.5, 22.5, 24.5), reach=2.5)
    leaf(s, mk(c, [('heart', L((120, 255, 170)))], kind='bone').tex(s), 14.0, 27.0, hw=1.0, fall=3.0)
    s.box(13.0, 14.0, -0.5, 1.0, (40, 60, 54))


@n('gae_dearg')
def _(s):
    _spear(s, (124, 30, 38), mk((220, 40, 40), [('streak', (255, 150, 130))]).tex(s), u_sock=18.5, hw=1.5,
           collar=(70, 20, 26))
    s.px([(28, 9), (28, 10), (28, 12), (25, 12), (25, 13)], s.lit((255, 64, 52)))
    s.box(7.0, 7.5, -0.5, 1.0, (70, 20, 26))


@n('gungnir')
def _(s):
    haft(s, 0.5, 19.0, (66, 58, 72))
    s.upx([(u, 0.0) for u in (3, 6, 9, 12, 15)], s.lit((190, 140, 255)))
    leaf(s, mk((212, 204, 255), [('streak', WHITE)]).tex(s), 18.0, 27.0, hw=1.25, rise=0.5, fall=2.6)
    s.box(17.0, 18.0, -1.0, 1.5, GOLD)
    s.upx([(26.5, 0.25)], s.lit((220, 190, 255)))


@n('hector_javelin')
def _(s):
    s.box(5.0, 20.0, 0.0, 0.5, (200, 180, 140))
    leaf(s, mk(BRONZE).tex(s), 19.0, 25.5, hw=1.0, fall=2.6)
    s.box(18.5, 19.0, -0.5, 1.0, s.lit((255, 220, 90)))
    red = (200, 44, 44)
    s.line([P(18.0, 0.5), (P(18.0, 0.5)[0] + 1, P(18.0, 0.5)[1] + 4)], red)
    s.line([P(17.5, 0.5), (P(17.5, 0.5)[0], P(17.5, 0.5)[1] + 4)], red)
    s.curve([(10.0, 0.5), (11.0, 2.0), (12.5, 2.0), (13.0, 0.5)], 0.3, LEATHER)       # throwing loop


@n('leonidas_dory')
def _(s):
    _spear(s, ASH, mk((172, 178, 194)).tex(s), u_sock=20.0, hw=1.5, collar=DKIRON, h0=3.0)
    s.prof(0.0, 4.0, lambda u: min(1.0, u * 0.45), (198, 140, 56), cv=0.25)
    s.box(4.0, 4.5, -1.0, 1.5, (150, 100, 40))
    s.box(10.0, 13.5, 0.0, 0.5, (178, 40, 44))


@n('meleager_spear')
def _(s):
    _spear(s, ASH, mk((190, 198, 210), [('heart', 'lo')]).tex(s), u_sock=18.5, hw=2.25, collar=DKIRON, fall=1.8)
    s.box(17.0, 17.5, -3.0, 3.5, (150, 156, 170))
    s.box(9.0, 11.5, 0.0, 0.5, LEATHER)


@n('romulus_spear')
def _(s):
    _spear(s, (150, 100, 60), mk((196, 146, 60)).tex(s), u_sock=20.0, hw=1.25, collar=(150, 100, 40))
    s.box(8.0, 12.0, -0.5, 1.0, (150, 150, 152))
    s.tint(lambda u, v: 8 <= u <= 12 and H(int(2 * u), int(2 * v)) % 3 == 0, 'lo')
    g1, g2 = (92, 176, 70), (60, 130, 56)
    for u, v, c in ((3.0, -1.5, g1), (5.0, 2.0, g2), (14.5, -1.5, g1), (16.5, 2.0, g2), (15.5, -2.5, g2)):
        s.disc(u, v, 1.0, c)
    s.upx([(1.0, 1.5), (0.5, 0.5), (0.5, -1.0)], (110, 70, 44))                            # roots


@n('spear_of_longinus')
def _(s):
    haft(s, 0.5, 12.0, (140, 96, 60), wide=True)
    s.fn(lambda u, v: 11.0 <= u <= 14.5 and abs(v) <= 1.5 - (u - 11.0) * 0.3, (112, 76, 50))
    s.box(14.0, 23.5, 0.0, 0.0, (160, 164, 180))
    s.prof(22.5, 26.5, lambda u: min(1.0, (26.5 - u) / 1.8), (46, 40, 58))
    s.px([P(26.5, 0.0), P(27.0, 0.0)], s.lit((200, 120, 255)))
    s.post([(23.5, 0.0), (24.5, 0.0)], (150, 60, 70))
    s.box(0.5, 1.0, -0.5, 0.5, DKIRON)


@n('spear_of_lugh')
def _(s):
    haft(s, 0.5, 19.0, (120, 68, 40))
    flames(s, 18.0, 26.0, 1.5, (255, 100, 10), (255, 200, 70), cv=0.25, amp=1.8)
    hot = s.lit((255, 236, 150))
    leaf(s, hot, 18.0, 26.5, hw=1.5)
    s.box(17.0, 18.0, -0.5, 1.0, GOLD)
    s.box(6.0, 6.5, -0.5, 1.0, GOLD)


@n('trident_of_poseidon')
def _(s):
    c = mk((56, 170, 240), [('streak', (190, 240, 255))])
    t = c.tex(s)
    haft(s, 0.5, 19.0, (36, 84, 130))
    s.box(18.0, 19.0, -3.5, 4.0, t)
    s.prof(19.0, 27.0, lambda u: min(0.75, (27.0 - u) / 2.0), t, cv=0.25)
    for cv in (-3.25, 3.75):
        s.prof(19.0, 23.5, lambda u: min(0.5, (23.5 - u) / 1.5), t, cv=cv)
        s.box(21.0, 21.5, min(cv, cv - (1 if cv < 0 else -1)), max(cv, cv - (1 if cv < 0 else -1)), t)
    s.box(16.5, 17.0, -0.5, 1.0, GOLD)
    s.px([P(27.0, 0.25), P(23.5, -3.25), P(23.5, 3.75)], s.lit((200, 246, 255)))


@n('vel_of_murugan')
def _(s):
    haft(s, 0.5, 15.0, (150, 56, 40))
    for u in (3.0, 9.0):
        s.box(u, u + 0.5, -0.5, 1.0, GOLD)
    s.prof(14.5, 27.0, lambda u: max(0.0, min(3.0, (u - 14.5) * 1.3 + 0.5, (27.0 - u) / 1.5)),
           mk((240, 168, 56), [('heart', L((255, 240, 170)))]).tex(s), cv=0.0)
    s.px([(26, 3), (29, 6)], s.lit((255, 140, 60)))
    s.box(13.5, 14.5, -1.0, 1.0, GOLD)


# =================================================================== axes
@n('gilgamesh_axe')
def _(s):
    haft(s, 1.5, 22.5, (120, 80, 50))
    M = mk((208, 136, 62), [('streak', (250, 200, 120))])
    bit(s, M.tex(s), 18.0, 1, 5.5, root=1.0, up=0.9, dn=0.9, curve=0.02)
    s.erase(lambda u, v: (u - 16.0) ** 2 + (v - 2.0) ** 2 <= 0.8 or (u - 20.0) ** 2 + (v - 2.0) ** 2 <= 0.8)
    s.post([(16.0, 4.0), (17.5, 4.0), (19.0, 4.0), (20.5, 4.0), (17.0, 3.0), (19.5, 3.0)], (110, 64, 30))
    s.box(1.5, 4.5, 0.0, 0.5, LEATHER)


@n('green_chapel_axe')
def _(s):
    haft(s, 1.5, 22.5, (46, 116, 58))
    M = mk((112, 196, 124), [('streak', (214, 255, 214))])
    bit(s, M.tex(s), 17.5, 1, 8.0, root=1.5, up=0.6, dn=0.8, curve=0.045)
    spike(s, M.base, 17.5, -1, 3.0, root=1.2)
    vine = (120, 210, 90)
    s.upx([(u, 0.0 if i % 2 else 0.5) for i, u in enumerate((3, 5, 7, 9, 11, 13))], vine)
    s.disc(6.0, -1.5, 0.8, vine)
    s.disc(10.0, 2.0, 0.8, vine)
    s.upx([(8.0, -1.5), (12.0, 2.0)], s.lit((255, 60, 50)))


@n('labrys')
def _(s):
    haft(s, 0.5, 23.0, (196, 150, 60))
    M = mk((246, 204, 150), [('streak', WHITE)])
    t = M.tex(s)
    for side in (1, -1):
        bit(s, t, 18.0, side, 6.0, root=0.5, up=1.0, dn=1.0, curve=0.02)
    s.box(17.0, 19.0, -0.5, 1.0, GOLD)
    for u in (4.0, 9.0, 13.0):
        s.box(u, u + 0.5, -0.5, 1.0, (150, 100, 40))
    s.disc(23.5, 0.25, 1.0, GOLD)


@n('mwindo_axe')
def _(s):
    haft(s, 6.0, 21.5, (100, 62, 40), wide=True)
    s.post([(u, 0.0) for u in (8, 10, 12, 14)], (250, 246, 232))
    bit(s, mk((150, 150, 160)).tex(s), 18.5, 1, 4.5, root=0.8, up=0.5, dn=0.5, curve=0.08)
    for dv in (-3.0, -1.5, 0.0, 1.5, 3.0):
        s.uline([(6.0, 0.0), (1.5, dv)], (224, 200, 150))
    s.box(5.5, 6.5, -1.0, 1.0, (190, 60, 50))


@n('parashu')
def _(s):
    haft(s, 1.5, 22.0, (70, 50, 60))
    hot = s.lit((255, 236, 160))
    M = mk((250, 158, 76), [('streak', (255, 226, 160))])

    def inside(u, v):
        return 0.5 <= v <= 8.2 - 0.05 * (u - 17.5) ** 2 and -(1.5 + 0.8 * v) <= u - 17.5 <= 1.5 + 0.6 * v
    s.fn(inside, hot)
    bit(s, M.tex(s), 17.5, 1, 7.0, root=1.5, up=0.6, dn=0.8, curve=0.05, edge=False)
    spike(s, M.base, 17.5, -1, 3.0, root=1.2)
    s.prof(22.0, 26.0, lambda u: min(0.75, (26.0 - u) / 2.0), M.base, cv=0.25)
    for u in (4.0, 10.0, 14.0):
        s.box(u, u + 0.5, -0.5, 1.0, GOLD)


# ================================================================== blunt
@n('cain_club')
def _(s):
    c = (146, 92, 60)

    def col(u, v, x, y):
        return (118, 44, 40) if u > 19.5 + 0.3 * v else c
    s.prof(3.0, 20.0, lambda u: 0.5 + 1.0 * (u - 3.0) / 17.0, col)
    for cu, cv, r in ((20.5, 0.0, 2.6), (22.5, 1.5, 1.6), (21.5, -2.5, 1.5), (18.5, 2.0, 1.2), (23.0, -1.0, 1.2)):
        s.disc(cu, cv, r, col)
    s.tint(lambda u, v: u < 19 and int(round(2 * v)) == 0 and H(int(u), 3) % 2 == 0, 'lo')
    s.upx([(24.5, -2.5), (24.5, 2.5)], c)


@n('cuchulainn_hurley')
def _(s):
    t = ASH
    bf = lambda u: 1.8 * max(0.0, (u - 15.0) / 9.0) ** 2
    s.prof(2.5, 24.0, lambda u: 0.5 if u < 14 else min(0.5 + (u - 14.0) * 0.32, (24.4 - u) * 2.5), t, bend=bf)
    s.box(2.5, 6.5, -0.5, 0.5, (50, 46, 56))
    s.box(18.0, 18.5, 0.0, 3.5, (150, 156, 170))                        # iron band
    s.sell(15, 3, 19, 7, (244, 240, 230))
    s.postxy([(16, 5), (17, 4), (18, 5)], (200, 60, 50))


@n('heracles_club')
def _(s):
    t = mk((134, 98, 60), [('grain', (80, 54, 36)), ('dots19', 'lo2')], kind='wood').tex(s)
    s.prof(1.0, 23.0, lambda u: min(0.75 + 2.6 * ((u - 1.0) / 22.0) ** 1.1, (23.8 - u) * 2.0 + 0.5), t)
    for cu, cv in ((12.0, 2.5), (15.5, -3.0), (18.5, 3.5), (21.0, -3.5), (22.0, 3.0), (9.0, -2.0)):
        s.disc(cu, cv, 1.25, t)
    s.box(1.5, 5.5, -1.0, 1.0, (90, 60, 40))
    s.disc(1.0, 0, 1.25, (134, 98, 60))


@n('theseus_club')
def _(s):
    t = mk((150, 104, 68), [('grain', 'lo')], kind='wood').tex(s)
    s.prof(5.0, 21.0, lambda u: min(0.75 + 1.75 * ((u - 5.0) / 16.0), (21.6 - u) * 2.0 + 0.5), t)
    br = (206, 150, 64)
    for u in (11.0, 15.0, 19.0):
        s.prof(u, u + 1.0, lambda uu: 1.0 + 1.75 * ((uu - 5.0) / 16.0), br)
    s.post([(11.5, 0), (15.5, -1), (15.5, 1), (19.5, -1.5), (19.5, 0), (19.5, 1.5)], (255, 226, 150))
    s.box(5.0, 6.0, -1.0, 1.0, br)
    s.disc(21.5, 0, 1.0, br)


@n('sharur')
def _(s):
    haft(s, 2.0, 18.0, (190, 150, 60), wide=True)
    wing = (250, 244, 214)
    for side in (1, -1):
        s.fn(lambda u, v, side=side: 1.0 <= side * v <= 6.0 and 14.5 - 0.5 * side * v <= u <= 17.5 - 0.9 * side * v + 1.0, wing)
    s.tint(lambda u, v: abs(v) >= 1.5 and int(round(2 * abs(v))) % 3 == 0 and 11 <= u <= 18, 'lo')
    s.disc(21.0, 0, 3.25, mk((244, 204, 84), [('streak', (255, 250, 200))]).tex(s))
    s.box(18.0, 18.5, -1.5, 1.5, DGOLD)
    s.upx([(21.0, 0.0)], s.lit((255, 255, 210)))
    s.disc(1.5, 0, 1.0, DGOLD)
    s.px([(29, 3), (30, 8), (24, 1)], s.lit((255, 240, 150)))


@n('sigurds_shovel')
def _(s):
    haft(s, 2.5, 16.0, (140, 104, 64))
    s.disc(2.0, 0.25, 2.0, (140, 104, 64))
    s.erase(lambda u, v: (u - 2.0) ** 2 + (v - 0.25) ** 2 <= 0.6)
    t = mk((134, 138, 152), [('streak', 'hi')]).tex(s)
    s.fn(lambda u, v: 16.0 <= u <= 25.5 and abs(v - 0.25) <= min(2.75, (u - 15.5) * 2.0, (25.8 - u) * 1.0), t)
    s.box(14.5, 16.5, -0.5, 1.0, (100, 104, 120))
    s.tint(lambda u, v: abs(v - 0.25) < 0.3 and 17 <= u <= 21, 'lo')
    s.post([(24.5, 0.0), (24.0, 1.0), (23.5, -1.0)], (110, 76, 50))


@n('dawnbreaker')
def _(s):
    haft(s, 0.5, 22.0, (70, 62, 84), wide=True)
    for u in (3.0, 9.0):
        s.box(u, u + 0.5, -1.0, 1.0, GOLD)
    dawn, rose = s.lit((255, 240, 160)), s.lit((255, 160, 110))
    s.box(14.0, 20.0, -5.0, 5.5, mk((84, 96, 130), [('streak', (170, 190, 240))]).tex(s))
    s.box(13.5, 20.5, -5.5, -4.5, GOLD)
    s.box(13.5, 20.5, 5.0, 6.0, GOLD)
    s.disc(17.0, 0.25, 2.5, rose)
    s.disc(17.0, 0.25, 1.5, dawn)
    s.px([(27, 5), (11, 4), (29, 20)], dawn)


@n('mjolnir')
def _(s):
    s.box(5.5, 14.0, -0.5, 0.5, (110, 70, 44))
    s.tint(lambda u, v: 5.5 <= u <= 14 and int(round(2 * u)) % 3 == 0, 'lo')
    s.curve([(5.5, 0), (4.0, 1.5), (2.5, 0), (4.0, -1.5), (5.5, 0)], 0.3, (150, 100, 60))     # thong loop
    zc = (110, 190, 255)
    zap(s, [(9, 2), (11, 5), (9, 7), (11, 9)], zc, WHITE)
    zap(s, [(29, 20), (27, 23), (29, 25), (27, 28)], zc, WHITE)
    t = mk((126, 136, 158), [('streak', (214, 226, 246))]).tex(s)
    s.fn(lambda u, v: 14.0 <= u <= 20.5 and abs(v - 0.25) <= 5.75 - max(0.0, (16.0 - u)) * 0.8, t)
    s.box(14.0, 20.5, -0.5, 1.0, (90, 98, 120))
    s.upx([(17.0, -3.0), (17.0, 3.5)], s.lit(zc))
    s.box(20.5, 21.0, -0.5, 1.0, GOLD)


@n('mjolnir_shard')
def _(s):
    iron, dk = (112, 120, 142), (78, 84, 104)
    s.poly([(9, 11), (15, 6), (22, 8), (25, 14), (21, 19), (23, 24), (15, 25), (10, 21), (12, 16), (7, 14)], iron)
    s.poly([(15, 6), (22, 8), (18, 13), (12, 16), (9, 11)], (140, 150, 176))
    s.line([(18, 13), (21, 19)], dk)
    s.line([(12, 16), (15, 25)], dk)
    zc = (130, 200, 255)
    zap(s, [(4, 8), (7, 10), (6, 13), (9, 15)], zc, WHITE)
    zap(s, [(27, 6), (25, 9), (27, 11), (25, 14)], zc, WHITE)
    zap(s, [(20, 28), (22, 26), (25, 27), (27, 24)], zc, WHITE)
    s.px([(16, 10), (14, 20), (20, 16)], s.lit(zc))


@n('venomfang')
def _(s):
    haft(s, 1.5, 18.0, (50, 50, 56))
    s.box(1.5, 6.0, 0.0, 0.5, (70, 110, 60))
    cu, cv = 20.5, 0.25
    ven = s.lit((170, 255, 90))
    for du, dv, ln in ((1, 0, 5.0), (-1, 0, 4.0), (0, 1, 5.0), (0, -1, 5.0), (.7, .7, 5.6), (.7, -.7, 5.6),
                       (-.7, .7, 5.0), (-.7, -.7, 5.0)):
        s.uline([(cu + du * 2, cv + dv * 2), (cu + du * ln, cv + dv * ln)], (150, 170, 130))
        s.upx([(cu + du * ln, cv + dv * ln)], ven)
    s.disc(cu, cv, 3.0, mk((62, 84, 60), [('streak', (150, 190, 130))]).tex(s))
    s.px([(27, 14), (27, 16), (20, 13), (20, 15)], ven)
    s.box(16.0, 16.5, -0.5, 1.0, (90, 96, 100))


@n('wepwawet_mace')
def _(s):
    s.line([(3, 28), (15, 16)], (196, 160, 80), 2)
    s.rect(13, 13, 29, 14, GOLD)                            # the standard's platform
    s.sell(11, 15, 16, 20, (236, 228, 204))                 # pear mace head
    jk = (44, 40, 54)
    s.rect(17, 7, 25, 9, jk)                                # body
    for x in (17, 19, 23, 25):
        s.rect(x, 10, x, 12, jk)                            # legs
    s.rect(24, 4, 26, 7, jk)                                # neck
    s.rect(25, 3, 28, 5, jk)                                # head
    s.px([(29, 5), (25, 1), (25, 2), (27, 1), (27, 2)], jk)  # muzzle and tall ears
    s.line([(16, 8), (15, 11)], jk)                         # tail
    s.postxy([(27, 4)], (255, 220, 90))
    s.rect(24, 6, 26, 6, GOLD)                              # collar


# ================================================================= staffs
@n('laevateinn')
def _(s):
    char = (58, 46, 48)
    s.curve([(1.0, 0.0), (6.0, 0.5), (11.0, -0.25), (16.0, 0.5), (21.0, 0.0)], 0.6, char)
    s.curve([(13.0, 0.0), (15.5, -2.0)], 0.3, char)
    s.upx([(4, 0.0), (9, 0.0), (14, 0.5), (18, 0.0)], s.lit((255, 110, 70)))
    fo, fi = s.lit((255, 120, 50)), s.lit((255, 230, 130))
    s.prof(20.5, 26.5, lambda u: max(0.0, min(2.0, (u - 20.0) * 1.2, (26.5 - u) / 1.6)), fo)
    s.prof(21.5, 24.5, lambda u: max(0.0, min(1.0, (u - 21.0), (24.5 - u) / 1.5)), fi)


def _crook(s, col, th=0.6):
    s.curve([(1.0, 0.25), (19.0, 0.25), (22.0, 0.0), (23.0, -1.5), (22.0, -3.5), (20.0, -4.0), (18.5, -3.0)], th, col)


@n('pharaohs_crook')
def _(s):
    gold, blue = (232, 186, 62), (40, 80, 176)
    _crook(s, lambda u, v, x, y: gold if int(u / 1.5) % 2 == 0 else blue, th=0.75)
    s.disc(1.0, 0.25, 1.0, gold)


@n('rod_of_moses')
def _(s):
    _crook(s, mk((150, 110, 70), [('grainf', 'lo')], kind='wood').tex(s))
    leafc, bl = (92, 164, 76), s.lit((255, 214, 226))
    for u, v in ((8.0, -1.5), (13.0, 2.0), (17.0, -1.5), (21.0, 2.0), (23.5, -3.5)):
        s.disc(u, v, 0.8, leafc)
    for u, v in ((10.5, 1.5), (15.0, -1.5), (19.5, 1.5), (22.5, -5.0), (19.0, -4.5), (24.0, -0.5)):
        s.disc(u, v, 0.8, bl)
        s.upx([(u, v)], s.lit((255, 250, 210)))


@n('ruyi_jingu_bang')
def _(s):
    s.box(0.5, 26.0, -1.0, 1.0, (176, 34, 40))
    gold = mk((240, 196, 60), [('streak', (255, 250, 190))]).tex(s)
    s.box(0.5, 5.0, -1.0, 1.0, gold)
    s.box(21.5, 26.0, -1.0, 1.0, gold)
    s.box(5.0, 5.5, -1.5, 1.5, DGOLD)
    s.box(21.0, 21.5, -1.5, 1.5, DGOLD)
    s.tint(lambda u, v: 6 <= u <= 20.5 and abs(v + 0.5) < 0.1, 'hi')
    s.upx([(24.0, 0.0), (2.5, 0.0)], s.lit((255, 255, 200)))


@n('staff_of_moses')
def _(s):
    t = mk((164, 132, 90), [('grainf', 'lo')], kind='wood').tex(s)
    s.curve([(0.5, 0.25), (8.0, 0.75), (15.0, -0.25), (22.0, 0.5), (24.5, 0.25)], 0.6, t)
    s.disc(24.5, 0.25, 1.5, t)
    s.disc(16.0, 1.0, 1.0, t)
    s.disc(8.0, -0.5, 0.9, t)
    w1, w2 = s.lit((90, 170, 255)), s.lit((214, 240, 255))
    s.px([(27, 9), (27, 10), (29, 7), (29, 8), (24, 11), (24, 12)], w1)       # water from the rock
    s.px([(27, 8), (29, 6), (24, 10)], w2)


@n('thyrsus')
def _(s):
    haft(s, 0.5, 20.0, (126, 156, 84))
    s.tint(lambda u, v: u < 20 and int(round(2 * u)) % 8 == 0, 'lo')
    ivy = (50, 120, 60)
    for u, v in ((5.0, -1.5), (8.5, 2.0), (12.0, -1.5), (15.5, 2.0)):
        s.disc(u, v, 1.0, ivy)
    rib = (160, 60, 180)
    s.curve([(19.0, 0.5), (17.5, 3.0), (15.0, 4.5)], 0.4, rib)
    s.curve([(19.0, 0.0), (18.0, -2.5), (16.5, -4.0)], 0.4, rib)
    s.ell(22.5, 0.25, 3.5, 2.5, mk((156, 104, 60), [('scales', 'lo')], kind='wood').tex(s))
    s.box(19.0, 19.5, -1.0, 1.5, (110, 70, 44))


@n('prometheus_torch')
def _(s):
    s.box(1.0, 19.0, -0.5, 0.5, (176, 184, 112))
    s.tint(lambda u, v: u < 19 and int(round(2 * u)) % 9 == 0, 'lo2')
    s.box(18.0, 19.5, -1.0, 1.0, (120, 124, 70))
    fo, fi = s.lit((255, 130, 20)), s.lit((255, 232, 130))
    s.prof(19.5, 26.5, lambda u: max(0.0, min(2.5, (u - 19.0) * 1.5, (26.5 - u) / 1.5)), fo)
    s.prof(20.0, 24.5, lambda u: max(0.0, min(1.25, (u - 19.5) * 1.2, (24.5 - u) / 1.5)), fi)
    s.px([(29, 3), (24, 2)], fo)


# ================================================================= ranged
@n('atalanta_bow')
def _(s):
    _bow(s, mk((184, 142, 100), [('grain', 'lo')], kind='wood', trim=BONE), 3.0, 22.5, 2.5, 6.0, 0.5,
         power=0.85, grip=(84, 58, 42))
    s.post([(12.0, -3.5), (13.5, -3.5), (12.5, -3.0)], (150, 110, 80))


@n('bow_of_rama')
def _(s):
    M = mk((206, 80, 32), [('dots7', L((255, 190, 70)))], trim=GOLD)
    _bow(s, M, 2.5, 23.0, 2.5, 6.0, 0.75, power=0.6, ears=2.2, dip=2.0, grip=GOLD)
    s.upx([(2.5, 0.5), (23.0, 0.5)], s.lit((255, 220, 90)))


@n('gandiva')
def _(s):
    M = mk((250, 212, 96), [('streak', WHITE)], trim=(255, 255, 200))
    _bow(s, M, 1.5, 23.5, 2.5, 6.5, 0.9, power=0.6, ears=2.0, dip=2.0, grip=(60, 90, 190),
         string=s.lit((255, 255, 170)))
    s.upx([(12.5, -2.5)], s.lit((120, 210, 255)))
    s.px([(8, 4), (27, 22), (5, 9)], s.lit((255, 255, 170)))


@n('fail_not')
def _(s):
    M = mk((170, 200, 130), [('grain', 'lo')], kind='wood', trim=BONE)
    f = _bow(s, M, 1.5, 23.5, 1.5, 6.5, 0.5, power=0.75, string=(46, 42, 40))
    s.erase(lambda u, v: abs(v - 1.5) < 0.6 and 2.5 < u < 22.5)             # restring: drawn back
    s.uline([(1.5, 1.5), (12.5, 5.5), (23.5, 1.5)], STRING)
    s.box(12.5, 12.5, -9.0, 5.5, (214, 190, 150))
    s.fn(lambda u, v: abs(u - 12.5) <= min(1.0, (v + 10.5) * 0.7) and -10.5 <= v <= -8.5, STEELC)
    s.fn(lambda u, v: abs(u - 12.5) <= 1.0 and 3.0 <= v <= 5.0, (90, 160, 80))
    s.disc(6.0, f(6.0) - 1.2, 0.9, (80, 150, 70))
    s.disc(19.0, f(19.0) - 1.2, 0.9, (80, 150, 70))


@n('robin_hoods_longbow')
def _(s):
    M = mk((176, 124, 70), [('grain', 'lo')], kind='wood', trim=BONE)
    f = _bow(s, M, 1.0, 24.0, 2.5, 6.5, 0.5, power=0.75, grip=(34, 140, 50))
    for u in (4.5, 20.5):
        s.disc(u, f(u), 0.9, (34, 140, 50))
    arrow(s, 5.0, 3.5, 20.5, STEELC, (40, 160, 60), hw=1.0)


@n('sling_of_david')
def _(s):
    r_sling(s, Mat((150, 104, 70), [('stitch', (224, 200, 160))], kind='hide', trim=(110, 70, 44)),
            stone=(0, 0, 0))
    s.erase(lambda u, v: (u - 11.5) ** 2 + (v - 8.5) ** 2 <= 5)
    for x, y, c in ((15, 24, (176, 176, 180)), (19, 22, (150, 152, 160)), (20, 26, (196, 190, 178)),
                    (24, 23, (166, 166, 172)), (25, 27, (140, 142, 150))):
        s.sell(x - 1, y - 1, x + 2, y + 2, c)


@n('boomstick')
def _(s):
    wood, steel, dk = (128, 84, 50), (84, 88, 106), (50, 52, 66)
    s.fn(lambda u, v: 1.0 <= u <= 9.0 and -1.0 + (9.0 - u) * 0.15 <= v <= 1.5 + (9.0 - u) * 0.4, wood)
    s.box(11.5, 17.5, 1.0, 2.0, wood)                                   # fore-end
    s.box(9.5, 25.0, -1.5, -0.5, steel)
    s.box(9.5, 25.0, 0.5, 1.0, steel)
    s.box(9.5, 25.0, 0.0, 0.0, dk)
    s.box(8.0, 11.5, -1.5, 1.5, (130, 134, 150))                        # receiver
    s.curve([(7.0, 1.5), (7.5, 3.0), (9.5, 3.0), (10.0, 1.5)], 0.3, dk)  # trigger guard
    s.post([(25.0, -1.0), (25.0, 0.5)], (20, 20, 26))
    s.post([(9.0, -1.0)], (226, 190, 80))
    s.tint(lambda u, v: 1 <= u <= 7 and abs(v - 1.0) < 0.1 and int(round(2 * u)) % 4 != 0, 'lo')


@n('net_of_hephaestus')
def _(s):
    net = (206, 214, 232)
    inside = lambda x, y: (x - 16) ** 2 / 169.0 + (y - 15) ** 2 / 144.0 <= 1.0
    for y in range(2, 29):
        for x in range(2, 30):
            if inside(x, y) and ((x + y) % 5 == 0 or (x - y) % 5 == 0):
                s.px([(x, y)], net)
    for a in range(0, 360, 45):
        x = int(round(16 + 13 * math.cos(math.radians(a + 10))))
        y = int(round(15 + 12 * math.sin(math.radians(a + 10))))
        s.sell(x - 1, y - 1, x + 1, y + 1, GOLD)
    s.px([(16, 15), (11, 10), (21, 20)], s.lit((236, 246, 255)))


@n('punch_in_the_face')
def _(s):
    star, core = s.lit((255, 206, 70)), s.lit((255, 246, 170))
    pts = []
    for i in range(16):
        r = 15 if i % 2 == 0 else 9
        a = math.radians(i * 22.5 + 10)
        pts.append((16 + r * math.cos(a), 15 + r * math.sin(a)))
    s.poly(pts, star)
    s.sell(8, 7, 24, 23, core)
    skin, dk = (238, 184, 136), (190, 130, 96)
    s.rect(9, 12, 23, 22, skin)                              # back of the fist
    for x in (9, 13, 17, 21):
        s.rect(x, 8, x + 2, 13, skin)                        # four knuckles
    s.rect(7, 16, 12, 19, skin)                              # thumb across
    s.line([(9, 14), (23, 14)], dk)
    for x in (12, 16, 20):
        s.line([(x, 9), (x, 13)], dk)
    s.line([(8, 20), (12, 20)], dk)
    s.rect(11, 23, 22, 27, (190, 50, 50))                    # flannel cuff
    s.line([(11, 25), (22, 25)], (40, 40, 50))
    for x in (14, 18):
        s.line([(x, 23), (x, 27)], (40, 40, 50))


# =================================================================== ammo
def _arrows(s, head, fletch, shaft=(214, 190, 150), hw=1.0):
    arrow(s, -3.0, 3.0, 22.5, head, fletch, shaft, hw)
    arrow(s, 3.0, 3.0, 22.5, head, fletch, shaft, hw)
    arrow(s, 0.0, 4.5, 26.0, head, fletch, shaft, hw)


def _bolts(s, head, fletch, shaft=(160, 116, 72)):
    bolt(s, -2.0, 6.0, 21.5, head, fletch, shaft)
    bolt(s, 2.5, 6.0, 21.5, head, fletch, shaft)


@n('iron_arrow')
def _(s):
    _arrows(s, (132, 132, 140), (150, 116, 84))


@n('steel_arrow')
def _(s):
    _arrows(s, (204, 214, 234), (236, 236, 240), shaft=(190, 120, 80))


@n('hardened_gold_arrow')
def _(s):
    _arrows(s, (240, 200, 70), (200, 50, 50))
    s.px([P(26.0, 0.0)], s.lit((255, 250, 190)))


@n('diamond_arrow')
def _(s):
    _arrows(s, s.lit((170, 230, 255)), (110, 170, 240), shaft=(226, 226, 236))


@n('dragonbone_arrow')
def _(s):
    _arrows(s, (220, 160, 70), (150, 40, 36), shaft=(236, 226, 196))
    s.px([P(26.0, 0.0), P(22.5, -3.0), P(22.5, 3.0)], s.lit((255, 130, 50)))


@n('bone_arrow')
def _(s):
    arrow(s, 0.0, 2.5, 26.0, BONE, (150, 150, 150), shaft=(226, 216, 190), hw=1.5, hl=4.0, fl=4.5)
    s.box(21.0, 22.0, -0.5, 0.5, (120, 80, 56))


@n('arrows_of_artemis')
def _(s):
    _arrows(s, s.lit((236, 240, 255)), (250, 250, 255), shaft=(200, 204, 224))
    moon = s.lit((214, 224, 255))
    s.sell(3, 3, 9, 9, moon)
    s.sell(5, 2, 11, 8, (0, 0, 0))
    for y in range(1, 12):
        for x in range(1, 13):
            if s.img.getpixel((x, y))[:3] == (0, 0, 0) and s.img.getpixel((x, y))[3]:
                s.img.putpixel((x, y), (0, 0, 0, 0))


@n('arrows_of_eros')
def _(s):
    gold = s.lit((255, 214, 80))
    for v0, u1 in ((-2.5, 23.0), (2.5, 23.0)):
        arrow(s, v0, 3.5, u1, gold, (255, 150, 180), shaft=(240, 220, 170), hw=1.5, hl=3.0)
        s.erase(lambda u, v, v0=v0, u1=u1: abs(v - v0) < 0.3 and u1 - 3.2 <= u <= u1 - 2.4)   # heart notch
    red = s.lit((255, 70, 100))
    s.px([(7, 6), (9, 6), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (7, 8), (8, 8), (9, 8), (8, 9)], red)


@n('bolts_of_zeus')
def _(s):
    b, w = s.lit((110, 160, 255)), s.lit((244, 250, 255))
    for dx in (0, 8, 16):
        pts = [(11 + dx, 2), (6 + dx, 14), (10 + dx, 14), (4 + dx, 29), (13 + dx, 12), (9 + dx, 12), (14 + dx, 2)]
        pts = [(min(30, x), y) for x, y in pts]
        s.poly(pts, b)
        s.line([(11 + dx, 4), (8 + dx, 13)], w)
        s.line([(10 + dx, 14), (7 + dx, 23)], w)


@n('shotgun_shell')
def _(s):
    red, brass = (204, 50, 44), (220, 176, 70)
    for x, y in ((5, 6), (13, 9), (21, 6)):
        s.rect(x, y, x + 5, y + 13, red)
        s.rect(x, y + 14, x + 5, y + 18, brass)
        s.rect(x - 1, y + 18, x + 6, y + 19, brass)
        s.line([(x + 1, y), (x + 4, y)], (150, 34, 34))
        s.postxy([(x + 1, y + 3), (x + 1, y + 5), (x + 1, y + 7)], (255, 150, 140))


def _mbolt(head, fletch, glow=None):
    def f(s):
        h = s.lit(head) if glow else head
        _bolts(s, h, fletch)
    return f


n('iron_bolt')(_mbolt((132, 132, 140), (120, 84, 56)))
n('steel_bolt')(_mbolt((204, 214, 234), (226, 226, 232)))
n('hardened_gold_bolt')(_mbolt((240, 200, 70), (190, 50, 50)))
n('diamond_bolt')(_mbolt((170, 230, 255), (110, 170, 240), glow=True))
n('adamantine_bolt')(_mbolt((70, 150, 130), (40, 50, 80)))


# ================================================================= strays
def _bone(s, u0, u1, hw, kn, marrow=True):
    c = (236, 228, 204)
    s.prof(u0, u1, hw, c)
    for v in (-1, 1):
        s.disc(u0, v * kn * 0.6, kn, c)
    if marrow:
        s.ell(u1, 0, 1.0, hw + 0.5, c)
        s.ell(u1 + 0.25, 0, 0.6, hw - 0.25, (226, 120, 120))
    else:
        for v in (-1, 1):
            s.disc(u1, v * kn * 0.6, kn, c)
    s.tint(lambda u, v: u0 + 2 < u < u1 - 2 and abs(v - hw + 0.5) < 0.1 and int(round(2 * u)) % 5 == 0, 'lo')


@n('bone_marrow')
def _(s):
    _bone(s, 6.5, 20.5, 1.25, 1.75)


@n('giant_marrow')
def _(s):
    _bone(s, 5.0, 22.0, 2.25, 2.75)
    s.post([(12.0, -1.0), (15.0, 1.0)], (190, 176, 150))


@n('devil_glaive_shard')
def _(s):
    t = mk((104, 38, 48), [('streak', (214, 110, 100))]).tex(s)
    s.fn(lambda u, v: 6.0 + (1.0 if int(round(2 * v)) % 3 == 0 else 0.0) + abs(v) * 0.4 <= u <= 24.0
         and -min(2.0, (24.0 - u) * 0.5) <= v <= min(3.0, (24.0 - u) * 0.35), t)
    s.upx([(10.0, 0.5), (13.0, 1.0), (16.0, 0.5)], s.lit((255, 110, 50)))


@n('horseman_lance_shard')
def _(s):
    s.box(6.0, 18.0, -0.5, 0.5, (150, 96, 56))
    s.erase(lambda u, v: u < 8.0 and (v > 0.2 or (u < 7.0 and v < -0.2)))
    s.tint(lambda u, v: 6 <= u <= 18 and abs(v) < 0.1 and int(round(2 * u)) % 5 != 0, 'lo')
    leaf(s, mk((186, 190, 204)).tex(s), 17.0, 25.5, hw=1.5, cv=0.0)
    s.box(16.5, 17.5, -1.0, 1.0, DKIRON)
    s.fn(lambda u, v: 12.0 <= u <= 16.0 and 0.5 < v <= 0.5 + (u - 11.0) * 0.9 - (1.0 if int(u) % 2 else 0), (170, 40, 44))


@n('philosophers_pick')
def _(s):
    r_lockpick(s, Mat((236, 192, 66), [('streak', (255, 250, 190))], grip=(96, 40, 110), trim=(150, 156, 176)))
    s.upx([(7.5, 0.0)], s.lit((255, 80, 90)))
