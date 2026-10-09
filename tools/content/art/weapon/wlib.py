"""Weapon-icon library: a diagonal (u, v) drawing frame on top of core.Sprite,
materials with surface patterns, and the parametric rigs (one per template).

Offline tooling.  u runs from the bottom-left corner of the tile to the top-right
(0..26), v runs across it (negative = up-left, positive = down-right).  One unit
is one diagonal pixel step, so every shape lands on clean 45-degree stairs.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Sprite, shade, BONE, STRING  # noqa: E402

OX, OY = 3, 28
WOOD = (134, 94, 54)
LEATHER = (112, 70, 44)
BRASS = (204, 164, 72)
DKIRON = (88, 92, 110)
STONE = (150, 150, 152)
EPS = 1e-6


def P(u, v):
    return (int(round(OX + u + v)), int(round(OY - u + v)))


def H(a, b):
    return ((a * 73856093) ^ (b * 19349663) ^ 0x5bd1e995) & 0x7fffffff


class W(Sprite):
    def __init__(self):
        super().__init__()
        self.shadow = False
        self.dec = {}        # (x, y) -> (expected base colour, op): applied after finish
        self.after = []      # (x, y, colour): absolute pixels applied after finish

    # --- uv painting -------------------------------------------------
    def fn(self, pred, c):
        put = self.img.putpixel
        for y in range(1, 31):
            for x in range(1, 31):
                dx, dy = x - OX, y - OY
                u, v = (dx - dy) / 2, (dx + dy) / 2
                if pred(u, v):
                    col = c(u, v, x, y) if callable(c) else c
                    if col:
                        put((x, y), col + (255,))

    def erase(self, pred):
        for y in range(1, 31):
            for x in range(1, 31):
                dx, dy = x - OX, y - OY
                if pred((dx - dy) / 2, (dx + dy) / 2):
                    self.img.putpixel((x, y), (0, 0, 0, 0))

    def box(self, u0, u1, v0, v1, c):
        self.fn(lambda u, v: u0 - EPS <= u <= u1 + EPS and v0 - EPS <= v <= v1 + EPS, c)

    def prof(self, u0, u1, w, c, cv=0.0, bend=None):
        wf = w if callable(w) else (lambda u: w)
        bf = bend or (lambda u: 0.0)
        cc = c
        if callable(c):
            cc = lambda u, v, x, y: c(u, v - cv - bf(u), x, y)
        self.fn(lambda u, v: u0 - EPS <= u <= u1 + EPS and abs(v - cv - bf(u)) <= wf(u) + EPS, cc)

    def ell(self, cu, cv, ru, rv, c):  # noqa: uv ellipse (shadows Sprite.ell on purpose)
        self.fn(lambda u, v: ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 <= 1 + EPS, c)

    def disc(self, cu, cv, r, c):
        self.ell(cu, cv, r, r, c)

    def curve(self, pts, th, c):
        """Stroke of half-thickness th along a uv polyline."""
        dense = []
        for (a, b), (a2, b2) in zip(pts, pts[1:]):
            n = max(2, int(4 * (abs(a2 - a) + abs(b2 - b))) + 1)
            for i in range(n + 1):
                dense.append((a + (a2 - a) * i / n, b + (b2 - b) * i / n))
        t2 = th * th + EPS
        self.fn(lambda u, v: any((u - a) ** 2 + (v - b) ** 2 <= t2 for a, b in dense), c)

    def uline(self, pts, c, w=1):
        self.line([P(u, v) for u, v in pts], c, w)

    def upx(self, pts, c):
        self.px([P(u, v) for u, v in pts], c)

    def sell(self, x0, y0, x1, y1, c):          # screen-space ellipse
        Sprite.ell(self, x0, y0, x1, y1, c)

    def post(self, pts, c):                     # absolute pixels after finish (uv)
        for u, v in pts:
            x, y = P(u, v)
            self.after.append((x, y, c))

    def postxy(self, pts, c):
        for x, y in pts:
            self.after.append((x, y, c))

    def tint(self, pred, op):
        """Shade already-painted pixels after finish (op: hi, lo, hi2, lo2 or colour)."""
        for y in range(1, 31):
            for x in range(1, 31):
                p = self.img.getpixel((x, y))
                if not p[3]:
                    continue
                dx, dy = x - OX, y - OY
                if pred((dx - dy) / 2, (dx + dy) / 2):
                    self.dec[(x, y)] = (p[:3], op)

    def finish(self):
        pre = self.img.copy().load()
        out = super().finish()
        o = out.load()
        for (x, y), (base, op) in self.dec.items():
            if pre[x, y][3] == 0 or pre[x, y][:3] != base:
                continue
            cur = o[x, y][:3]
            if op == 'hi':
                n = shade(cur, 1)
            elif op == 'lo':
                n = shade(cur, -1)
            elif op == 'hi2':
                n = shade(cur, 2)
            elif op == 'lo2':
                n = shade(cur, -2)
            else:
                n = op
            o[x, y] = n + (255,)
        for x, y, c in self.after:
            if 0 <= x < 32 and 0 <= y < 32 and pre[x, y][3]:
                o[x, y] = c + (255,)
        return out


# ------------------------------------------------------------ surface patterns
def _dots(n):
    return lambda a, b: H(a, b) % n == 0


PAT = {
    'streak': lambda a, b: b % 6 == 5 and a % 14 < 9,
    'grain': lambda a, b: b % 3 == 1 and H(a // 4, b) % 3 == 0,
    'grainf': lambda a, b: b % 2 == 0 and H(a // 4, b) % 3 == 0,
    'damascus': lambda a, b: (a + int(round(1.7 * math.sin(b * 1.2)))) % 4 < 2,
    'scales': lambda a, b: (a % 4 == 0 and b % 4 < 2) or (a % 4 == 2 and b % 4 >= 2),
    'stitch': lambda a, b: b % 6 == 0 and a % 4 < 2,
    'rings': lambda a, b: a % 7 == 0,
    'birch': lambda a, b: a % 5 == 0 and H(a, b // 2) % 3 != 0,
    'veins': lambda a, b: (a + 2 * b) % 11 == 0 or (2 * a - 3 * b) % 17 == 0,
    'facet': lambda a, b: (a + b) % 7 < 2,
    'heart': lambda a, b: b == 0 and a % 9 != 0,
    'rune': lambda a, b: b == 0 and a % 6 < 2,
    'dimple': lambda a, b: a % 3 == 0 and b % 3 == 0,
    'blob': lambda a, b: (a + int(round(2 * math.sin(a * 0.7))) + 2 * b) % 9 < 3 and b % 2 == 0,
    'pits': lambda a, b: H(a, b) % 9 == 0,
}
for _n in (5, 7, 9, 11, 13, 17, 19, 23):
    PAT['dots%d' % _n] = _dots(_n)


class Mat:
    def __init__(self, base, pats=(), kind='metal', trim=None, grip=None, haft=None, guard=None):
        self.base = base
        self.pats = list(pats)
        self.kind = kind
        self.trim = trim or (DKIRON if kind == 'wood' else BRASS)
        self.guard = guard or (shade(base, -1) if kind in ('wood', 'hide', 'bone') else self.trim)
        self.grip = grip or LEATHER
        self.haft = haft or (shade(base, -1) if kind == 'wood' else WOOD)

    def tex(self, s, shift=0):
        base = self.base
        lits = [(PAT[p], s.lit(op[1])) for p, op in self.pats if isinstance(op, tuple) and op[0] == 'lit']
        decs = [(PAT[p], op) for p, op in self.pats if not (isinstance(op, tuple) and op[0] == 'lit')]

        def f(u, v, x, y):
            a, b = int(round(2 * u)) + shift, int(round(2 * v))
            for p, c in lits:
                if p(a, b):
                    return c
            for p, op in decs:
                if p(a, b):
                    s.dec[(x, y)] = (base, op)
                    break
            else:
                s.dec.pop((x, y), None)
            return base
        return f


L = lambda c: ('lit', c)  # noqa: E731
IR = DKIRON
MATS = {
    # woods
    'ash': Mat((216, 192, 148), [('grain', 'lo')], 'wood'),
    'oak': Mat((150, 104, 60), [('grain', 'lo'), ('dots23', 'lo2')], 'wood'),
    'yew': Mat((204, 146, 82), [('heart', (150, 62, 44))], 'wood'),
    'ironwood': Mat((78, 60, 48), [('grain', 'lo'), ('streak', (150, 140, 136))], 'wood', trim=(150, 154, 166)),
    'dragonwood': Mat((132, 56, 44), [('dots11', L((255, 156, 60))), ('scales', 'lo')], 'wood'),
    'silverbark': Mat((212, 216, 206), [('dots19', L((236, 248, 255))), ('birch', (96, 96, 100))], 'wood'),
    'worldtree': Mat((238, 226, 168), [('veins', L((156, 230, 110)))], 'wood', trim=BRASS),
    'petrified_wood': Mat((152, 116, 92), [('veins', (226, 180, 112)), ('rings', 'lo')], 'stone'),
    'hardwood': Mat((112, 62, 42), [('grain', 'lo')], 'wood'),
    'wood': Mat((156, 112, 66), [('grain', 'lo')], 'wood'),
    # plain metals
    'copper': Mat((206, 110, 68), [('dots9', (92, 164, 132)), ('streak', 'hi')], trim=IR),
    'bronze': Mat((172, 126, 54), [('streak', 'hi')], trim=IR),
    'tempered_bronze': Mat((216, 144, 80), [('dimple', 'lo'), ('streak', 'hi2')], trim=IR, grip=(70, 50, 44)),
    'iron': Mat((128, 128, 134), [('pits', 'lo')], trim=(96, 80, 60)),
    'steel': Mat((172, 184, 204), [('streak', 'hi2')]),
    'silver': Mat((230, 232, 242), [('dots19', L((255, 255, 255))), ('streak', (255, 255, 255))], grip=(52, 60, 110)),
    'hardened_gold': Mat((228, 186, 58), [('streak', (255, 244, 170))], trim=IR, grip=(150, 40, 44)),
    'tungsten': Mat((98, 98, 108), [('rings', 'lo'), ('dots13', 'hi')], trim=(60, 60, 70)),
    'cold_iron': Mat((92, 106, 134), [('dots7', (198, 220, 240))], trim=(60, 66, 84), grip=(60, 60, 70)),
    'damascus_steel': Mat((186, 188, 208), [('damascus', (104, 106, 132))]),
    'cobalt_steel': Mat((66, 110, 208), [('dots11', (236, 246, 255)), ('streak', (170, 204, 255))], trim=(190, 196, 210)),
    'hematite': Mat((132, 46, 50), [('grain', (64, 52, 66)), ('streak', (214, 130, 130))], trim=IR, grip=(40, 34, 40)),
    # wondrous metals
    'mithril': Mat((166, 206, 242), [('dots9', L((222, 244, 255))), ('streak', (240, 250, 255))],
                   trim=(214, 222, 236), grip=(70, 90, 130)),
    'adamantine': Mat((60, 72, 104), [('streak', (176, 200, 246))], trim=(150, 160, 186), grip=(30, 30, 40)),
    'starmetal': Mat((120, 138, 220), [('dots7', L((255, 255, 214)))], trim=(214, 220, 240), grip=(40, 44, 90)),
    'sunsteel': Mat((250, 212, 108), [('heart', L((255, 250, 204)))], trim=(200, 110, 50), grip=(240, 236, 220)),
    'shadowiron': Mat((38, 38, 60), [('streak', (104, 86, 160)), ('dots9', (18, 16, 28))],
                      trim=(70, 64, 100), grip=(80, 50, 110)),
    'soulsteel': Mat((178, 170, 214), [('rune', L((120, 255, 226)))], trim=(110, 116, 140), grip=(50, 80, 90)),
    'orichalcum': Mat((244, 136, 50), [('dots9', L((255, 214, 100))), ('streak', (255, 226, 130))],
                      trim=IR, grip=(110, 40, 30)),
    'quicksilver': Mat((160, 178, 200), [('dots13', L((244, 252, 255))), ('blob', (252, 255, 255))],
                       trim=(120, 126, 140), grip=(60, 64, 76)),
    'glassteel': Mat((178, 232, 232), [('dots13', L((240, 255, 255))), ('facet', (238, 254, 252))],
                     trim=(120, 150, 160), grip=(70, 110, 116)),
    'void_touched': Mat((60, 20, 86), [('dots5', L((204, 92, 255))), ('dots7', (20, 6, 30))],
                        trim=(40, 30, 54), grip=(30, 20, 40)),
    # stone, bone, hide
    'obsidian': Mat((32, 26, 44), [('dots13', (232, 226, 255)), ('streak', (150, 128, 204))], 'stone',
                    trim=(110, 84, 60)),
    'petrified_dragon': Mat((78, 64, 92), [('dots13', L((255, 124, 60))), ('veins', (156, 134, 168))], 'stone',
                            trim=(120, 110, 100)),
    'dragonbone': Mat((240, 230, 198), [('rings', (224, 180, 110)), ('pits', (190, 150, 96))], 'bone',
                      trim=(170, 60, 40)),
    'bone': Mat(BONE, [('pits', 'lo2')], 'bone'),
    'dragonhide': Mat((200, 86, 56), [('scales', 'lo'), ('stitch', (244, 214, 160))], 'hide'),
    'rawhide': Mat((164, 120, 84), [('stitch', (236, 218, 184))], 'hide'),
    'plain': Mat((152, 164, 186), [('streak', 'hi2')], grip=(58, 92, 74), trim=(170, 150, 96)),
    'diamond': Mat((158, 222, 250), [('dots7', L((255, 255, 255))), ('facet', (236, 252, 255))], 'gem',
                   trim=(214, 222, 236), grip=(60, 80, 130)),
}


def get_mat(name, color=None):
    if name in MATS:
        return MATS[name]
    c = tuple(color) if color else (170, 176, 190)
    return Mat(c, [('streak', 'hi')])


# ---------------------------------------------------------------- sword rig
def sword(s, M, g=6.0, tip=26.0, hw=1.0, span=3.5, grip0=1.5, taper=2.0, k=0.0, gt=0.5,
          pommel='round', bend=None, style='point', blade=None, guard=None, grip=None, pcol=None,
          wrap=True, fuller=False):
    """g = guard position, tip = blade tip, hw = half width, span = guard half span,
    k = guard sweep (>0 toward the blade, <0 toward the hand)."""
    bt = blade if blade is not None else M.tex(s)
    gc = guard or M.guard
    grc = grip or M.grip
    if style == 'point':
        w = lambda u: min(hw, (tip - u) / taper)
    elif style == 'blunt':
        w = lambda u: hw
    elif style == 'leaf':
        def w(u):
            t = (u - g) / (tip - g)
            return max(0.0, min(hw * (0.55 + 0.6 * math.sin(math.pi * min(1, t * 1.25) ** 1.0)), (tip - u) / taper))
    else:
        w = lambda u: min(hw, (tip - u) / taper)
    if style == 'clip':
        bf = bend or (lambda u: 0.0)
        s.fn(lambda u, v: g <= u <= tip + EPS and -hw - EPS <= v - bf(u) <= min(hw, (tip - u) * 1.2 - hw) + EPS,
             (lambda u, v, x, y: bt(u, v - bf(u), x, y)) if callable(bt) else bt)
    else:
        s.prof(g, tip, w, bt, bend=bend)
    if fuller:
        s.tint(lambda u, v: abs(v) < 0.1 and g + 1.5 <= u <= tip - 6, 'lo')
    s.box(grip0, g, -0.5, 0.5, grc)
    if wrap:
        s.tint(lambda u, v: grip0 < u < g and abs(v) <= 0.5 and int(round(2 * u)) % 3 == 0, 'lo')
    if span:
        s.fn(lambda u, v: abs(v) <= span + EPS and g + k * abs(v) - EPS <= u <= g + gt + k * abs(v) + EPS, gc)
    p = grip0 - 0.5
    pc = pcol or gc
    if pommel == 'round':
        s.disc(p, 0, 1, pc)
    elif pommel == 'big':
        s.disc(p, 0, 1.5, pc)
    elif pommel == 'ring':
        s.disc(p, 0, 1.5, pc)
        s.erase(lambda u, v: abs(u - p) < 0.1 and abs(v) < 0.1)
    elif pommel == 'lobed':
        s.ell(p, 0, 0.8, 1.6, pc)
    elif pommel == 'cap':
        s.box(p - 0.5, p, -0.5, 0.5, pc)


# -------------------------------------------------------------- axes, poles
def haft(s, u0, u1, c=WOOD, wide=False):
    s.box(u0, u1, -0.5 if wide else 0.0, 0.5, c)


def bit(s, col, uc, side, reach, root=1.2, up=0.6, dn=0.6, curve=0.07, q0=0.5, edge=True):
    """Axe bit: a wedge flaring from the haft to a curved edge."""
    def inside(u, v):
        q = side * v
        du = u - uc
        return q0 - EPS <= q <= reach - curve * du * du + EPS and -(root + dn * q) - EPS <= du <= root + up * q + EPS
    s.fn(inside, col)
    if edge:
        s.tint(lambda u, v: inside(u, v) and side * v > reach - curve * (u - uc) ** 2 - 1.0, 'hi')


def spike(s, col, uc, side, reach, root=1.2, q0=0.0):
    s.fn(lambda u, v: q0 - EPS <= side * v <= reach + EPS and abs(u - uc) <= root * (1 - (side * v - q0) / (reach - q0 + 0.5)) + EPS, col)


def leaf(s, col, u0, tip, hw=1.5, cv=0.25, rise=1.2, fall=2.2):
    s.prof(u0, tip, lambda u: max(0.0, min(hw, (u - u0) * rise + 0.5, (tip - u) / fall)), col, cv=cv)


# ------------------------------------------------------------------ rigs
def r_shortsword(s, M):
    sword(s, M, g=7.5, tip=22.0, hw=1.5, span=2.5, grip0=4.0, taper=1.4)


def r_longsword(s, M):
    sword(s, M, g=6.0, tip=26.0, hw=1.0, span=3.5, grip0=1.5, taper=2.2)


def r_sword(s, M):
    sword(s, M, g=6.0, tip=24.0, hw=1.5, span=3.0, grip0=2.5, taper=2.6, k=0.35, pommel='big')


def r_bastard_sword(s, M):
    sword(s, M, g=8.5, tip=26.5, hw=1.0, span=3.0, grip0=1.5, taper=2.0, pommel='ring', fuller=True, k=-0.3)
    s.box(4.5, 5.0, -0.5, 0.5, M.guard)


def r_greatsword(s, M):
    sword(s, M, g=7.5, tip=26.5, hw=1.5, span=5.0, grip0=1.5, taper=1.5, gt=1.0, pommel='big', fuller=True)


def r_zweihander(s, M):
    sword(s, M, g=6.5, tip=26.5, hw=1.0, span=5.5, grip0=1.0, taper=1.6, pommel='round', k=0.2)
    s.box(7.5, 10.5, -1.0, 1.0, M.grip)                      # leather ricasso
    spike(s, M.base, 11.5, 1, 3.0, root=1.0)
    spike(s, M.base, 11.5, -1, 3.0, root=1.0)


def r_rapier(s, M):
    bt = M.tex(s)
    s.box(7.5, 25.5, -0.5, 0.0, bt)
    s.box(25.5, 26.5, 0.0, 0.0, bt)
    s.box(2.5, 7.0, -0.5, 0.5, M.grip)
    s.curve([(7.0, 0.5), (6.0, 3.0), (4.0, 3.0), (2.5, 1.0)], 0.3, M.guard)      # knuckle bow
    s.box(7.5, 7.5, -4.0, 4.0, M.guard)                       # thin quillons
    s.ell(7.5, 0, 1.3, 2.6, M.guard)                          # cup
    s.tint(lambda u, v: abs(u - 7.0) < 0.3 and abs(v) < 1.6, 'lo')
    s.disc(2.0, 0, 1, M.guard)


def r_scimitar(s, M):
    g, tip = 6.5, 23.0
    bf = lambda u: -3.0 * max(0.0, (u - g) / (tip - g)) ** 2
    def w(u):
        t = (u - g) / (tip - g)
        return min(0.75 + 1.25 * t, (1.0 - t) * 9.0)
    s.prof(g, tip, w, M.tex(s), bend=bf)
    s.box(2.5, g, -0.5, 0.5, M.grip)
    s.tint(lambda u, v: 2.5 < u < g and abs(v) <= 0.5 and int(round(2 * u)) % 3 == 0, 'lo')
    s.box(g, g + 0.5, -2.5, 2.5, M.guard)
    s.curve([(2.5, 0), (1.5, 0.5), (1.5, 1.5)], 0.6, M.guard)  # hooked pommel


def r_dagger(s, M):
    sword(s, M, g=10.0, tip=22.0, hw=1.0, span=2.5, grip0=6.0, taper=3.2, k=0.3)


def r_katana(s, M):
    g, tip = 8.5, 25.0
    bf = lambda u: -1.5 * max(0.0, (u - g) / (tip - g)) ** 2
    sword(s, M, g=g, tip=tip, hw=0.5, span=0, grip0=1.5, pommel='cap', bend=bf, style='clip', wrap=False,
          grip=(40, 36, 52), pcol=BRASS)
    s.tint(lambda u, v: 2 <= u < g and abs(v) < 0.1 and int(round(2 * u)) % 3 == 0, (226, 220, 200))
    s.ell(g + 0.25, 0, 0.5, 2.0, BRASS)


def r_executioner(s, M):
    sword(s, M, g=6.5, tip=23.5, hw=2.0, span=3.5, grip0=2.0, style='blunt', pommel='big', fuller=True)
    s.erase(lambda u, v: abs(u - 21.5) < 0.6 and abs(v) < 0.6)


def _binding(s, M, u):
    s.box(u, u + 0.5, -0.5, 1.0, M.trim if M.kind != 'wood' else LEATHER)


def r_axe(s, M):
    haft(s, 5.0, 22.0, M.haft)
    bit(s, M.tex(s), 18.5, 1, 4.5, root=1.0, up=0.35, dn=0.7, curve=0.05)
    _binding(s, M, 16.5)
    s.box(5.0, 7.5, 0.0, 0.5, LEATHER)


def r_battleaxe(s, M):
    haft(s, 1.5, 22.5, M.haft)
    t = M.tex(s)
    bit(s, t, 18.0, 1, 7.5, root=1.5, up=0.6, dn=0.75, curve=0.05)
    spike(s, t, 18.0, -1, 3.5, root=1.5)
    s.box(1.5, 4.5, 0.0, 0.5, LEATHER)
    s.box(22.5, 23.0, 0.0, 0.5, M.trim)


def r_great_axe(s, M):
    haft(s, 0.5, 22.5, M.haft, wide=True)
    t = M.tex(s)
    bit(s, t, 18.0, 1, 6.5, root=1.0, up=0.6, dn=0.6, curve=0.07)
    bit(s, t, 18.0, -1, 6.5, root=1.0, up=0.6, dn=0.6, curve=0.07)
    s.box(16.5, 19.5, -0.5, 0.5, M.trim)
    s.box(0.5, 3.5, -0.5, 0.5, LEATHER)
    s.disc(23.0, 0, 1, M.trim)


def r_greataxe(s, M):
    haft(s, 0.5, 21.0, M.haft)
    t = M.tex(s)
    bit(s, t, 18.5, 1, 6.0, root=0.6, up=0.45, dn=1.0, curve=0.03)
    bit(s, t, 18.5, -1, 6.0, root=0.6, up=0.45, dn=1.0, curve=0.03)
    s.prof(20.5, 25.5, lambda u: min(1.0, (25.5 - u) / 2.5), t, cv=0.25)
    s.box(0.5, 1.0, -0.5, 1.0, M.trim)


def r_halberd(s, M):
    haft(s, 0.5, 21.0, M.haft)
    t = M.tex(s)
    bit(s, t, 19.0, 1, 5.5, root=1.2, up=0.3, dn=0.6, curve=0.08)
    s.fn(lambda u, v: -4.0 <= v <= 0 and 18.0 - 0.5 * v <= u <= 19.5 - 0.1 * v, t)   # back hook
    s.prof(20.5, 27.0, lambda u: min(1.0, (27.0 - u) / 3.5), t, cv=0.25)
    s.box(16.5, 17.0, -0.5, 1.0, M.trim)


def r_glaive(s, M):
    haft(s, 0.5, 16.0, M.haft)
    t = M.tex(s)
    def inside(u, v):
        if not (15.5 <= u <= 26.5):
            return False
        tt = (u - 15.5) / 11.0
        back = -0.5 + (0.0 if tt < 0.7 else (tt - 0.7) * 5.0)
        belly = 0.75 + 3.2 * math.sin(math.pi * min(1.0, tt * 1.15)) ** 0.8 * (1 - tt * 0.35)
        return back - EPS <= v <= min(belly, (26.5 - u) * 1.3 + back) + EPS
    s.fn(inside, t)
    s.fn(lambda u, v: 17.0 <= u <= 18.5 and -3.0 <= v <= -0.5 and u - 17.0 <= 1.5 * (1 - (-v - 0.5) / 3.0), t)
    s.box(14.5, 15.5, -0.5, 1.0, M.trim)
    s.box(4.0, 4.5, -0.5, 1.0, M.trim)


def r_spear(s, M):
    haft(s, 0.5, 20.0, M.haft)
    leaf(s, M.tex(s), 19.0, 27.0, hw=1.5)
    s.box(18.0, 19.0, -0.5, 1.0, M.trim)
    s.box(0.5, 1.0, -0.5, 1.0, M.trim)


def r_club(s, M):
    t = M.tex(s)
    s.prof(2.0, 23.0, lambda u: min(0.5 + 2.1 * ((u - 2.0) / 21.0) ** 1.2, (23.6 - u) * 2.0 + 0.5), t)
    for cu, cv in ((14.5, 2.2), (18.5, -2.7), (21.0, 2.8)):
        s.disc(cu, cv, 1.0, t)
    s.box(2.5, 7.0, -1.0, 1.0, LEATHER)
    s.tint(lambda u, v: 2.5 <= u <= 7 and abs(v) <= 1 and int(round(2 * u)) % 3 == 0, 'lo')
    s.disc(1.5, 0, 1, M.guard)
    if M.kind not in ('wood',):
        s.tint(lambda u, v: u > 10 and int(round(2 * u)) % 5 == 0 and int(round(2 * v)) % 4 == 0, 'hi2')


def r_mace(s, M):
    haft(s, 1.5, 18.5, M.haft)
    t = M.tex(s)
    s.fn(lambda u, v: abs(u - 20.5) <= 2.5 and abs(v - 0.25) <= 3.75 and int(math.floor(u - 18.0)) % 2 == 0, t)
    s.ell(20.5, 0.25, 3.5, 2.25, t)
    s.box(24.0, 25.0, 0.0, 0.5, M.trim)
    s.box(16.5, 17.0, -0.5, 1.0, M.trim)
    s.box(1.5, 5.0, 0.0, 0.5, LEATHER)
    s.disc(1.5, 0.25, 0.8, M.trim)


def r_morningstar(s, M):
    haft(s, 1.5, 18.0, M.haft)
    cu, cv = 20.5, 0.25
    sp = shade(M.base, 1) if M.kind != 'gem' else M.base
    for du, dv, ln in ((1, 0, 5.0), (-1, 0, 4.0), (0, 1, 5.0), (0, -1, 5.0), (.7, .7, 5.6), (.7, -.7, 5.6),
                       (-.7, .7, 5.0), (-.7, -.7, 5.0)):
        s.uline([(cu + du * 2, cv + dv * 2), (cu + du * ln, cv + dv * ln)], sp)
    s.disc(cu, cv, 3.0, M.tex(s))
    s.box(16.0, 16.5, -0.5, 1.0, M.trim)
    s.box(1.5, 5.0, 0.0, 0.5, LEATHER)


def r_warhammer(s, M):
    haft(s, 1.5, 22.5, M.haft)
    t = M.tex(s)
    s.box(18.5, 21.5, -1.0, 4.0, t)
    s.box(18.0, 22.0, 4.0, 5.0, t)
    spike(s, t, 20.0, -1, 6.5, root=1.5, q0=1.0)
    s.prof(22.5, 25.0, lambda u: min(0.5, (25.0 - u) / 2.0), t, cv=0.25)
    s.box(16.5, 17.0, -0.5, 1.0, M.trim)
    s.box(1.5, 5.0, 0.0, 0.5, LEATHER)


def r_hammer(s, M):
    haft(s, 5.0, 22.0, M.haft)
    t = M.tex(s)
    s.box(17.5, 21.0, -4.0, 4.5, t)
    s.box(17.0, 21.5, -5.0, -4.0, t)
    s.box(17.0, 21.5, 4.5, 5.5, t)
    s.box(5.0, 8.0, 0.0, 0.5, LEATHER)


def r_maul(s, M):
    haft(s, 0.5, 22.0, M.haft, wide=True)
    t = M.tex(s)
    s.box(14.0, 20.5, -6.0, 6.5, t)
    s.box(13.5, 21.0, -6.5, -5.5, M.trim)
    s.box(13.5, 21.0, 6.0, 6.5, M.trim)
    s.box(14.0, 20.5, -0.5, 1.0, M.trim)
    s.box(0.5, 4.0, -0.5, 0.5, LEATHER)


def r_flail(s, M):
    s.box(1.5, 13.0, -0.5, 0.5, M.haft)
    s.box(1.5, 5.0, -0.5, 0.5, LEATHER)
    s.box(12.5, 13.5, -1.0, 1.0, M.trim)
    lk = [(14.5, -0.5), (15.5, -0.5), (16.5, -0.5), (17.5, 0.0), (18.5, 0.5), (19.0, 1.5), (19.0, 2.5), (18.5, 3.5)]
    for i, p in enumerate(lk):
        s.upx([p], (190, 194, 206) if i % 2 == 0 else (120, 124, 140))
    cu, cv = 17.0, 6.0
    sp = shade(M.base, 1) if M.kind != 'gem' else M.base
    for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1), (.7, .7), (.7, -.7), (-.7, .7), (-.7, -.7)):
        s.uline([(cu + du * 2, cv + dv * 2), (cu + du * 4.2, cv + dv * 4.2)], sp)
    s.disc(cu, cv, 2.5, M.tex(s))


def r_quarterstaff(s, M):
    s.box(0.5, 26.0, -0.5, 0.5, M.tex(s))
    s.box(0.5, 2.5, -0.5, 0.5, M.trim)
    s.box(23.5, 26.0, -0.5, 0.5, M.trim)
    s.box(10.5, 15.5, -0.5, 0.5, LEATHER)
    s.tint(lambda u, v: 10.5 <= u <= 15.5 and abs(v) <= 0.5 and int(round(2 * u)) % 3 == 0, 'lo')


def r_staff(s, M):
    t = M.tex(s)
    s.box(0.5, 20.5, 0.0, 0.5, t)
    s.disc(22.5, 0.25, 2.75, t)
    s.erase(lambda u, v: (u - 22.5) ** 2 + (v - 0.25) ** 2 <= 1.0)
    s.box(19.0, 19.5, -0.5, 1.0, M.trim)
    s.box(0.5, 1.0, -0.5, 1.0, M.trim)


def _bow(s, M, u0, u1, sv, depth, th, power=0.8, ears=0.0, dip=0.0, grip=LEATHER, string=STRING):
    mid = (u0 + u1) / 2
    def f(u):
        t = (u - u0) / (u1 - u0)
        v = sv - depth * math.sin(math.pi * t) ** power
        if ears:
            v -= ears * (math.exp(-((u - u0) / 1.6) ** 2) + math.exp(-((u1 - u) / 1.6) ** 2))
            v += ears * 0.9 * (math.exp(-((u - u0 - 2.5) / 1.5) ** 2) + math.exp(-((u1 - 2.5 - u) / 1.5) ** 2))
        if dip:
            v += dip * math.exp(-((u - mid) / 2.2) ** 2)
        return v
    n = 60
    pts = [(u0 + (u1 - u0) * i / n, f(u0 + (u1 - u0) * i / n)) for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    s.uline([a, b], string)
    s.curve(pts, th, M.tex(s))
    gp = [p for p in pts if abs(p[0] - mid) <= 1.6]
    s.curve(gp, th + 0.25, grip)
    s.upx([a, b], M.trim)
    return f


def r_longbow(s, M):
    _bow(s, M, 1.0, 24.0, 2.5, 6.5, 0.45, power=0.75)


def r_shortbow(s, M):
    _bow(s, M, 5.5, 20.5, 2.0, 6.5, 0.7, power=1.0)


def r_composite_bow(s, M):
    _bow(s, M, 2.5, 23.0, 2.5, 6.0, 0.7, power=0.6, ears=2.2, dip=2.2, grip=(150, 50, 44))


def _xbow(s, M, R, u_prod, stock0, stock1, th, spanned=True, heavy=False):
    def prod(v):
        return u_prod - 0.055 * v * v
    pts = [(prod(-R + 2 * R * i / 40), -R + 2 * R * i / 40) for i in range(41)]
    a, b = pts[0], pts[-1]
    stock = M.haft if M.kind == 'wood' else WOOD
    nut = stock0 + 6.0
    if not spanned:
        s.uline([a, (prod(R) - 0.5, 0), b], STRING)
    s.prof(stock0, stock1, lambda u: 1.0 if u < stock0 + 4.5 else 0.5, stock)
    s.tint(lambda u, v: stock0 <= u <= stock1 and abs(v - 0.5) < 0.1 and int(round(2 * u)) % 5 != 0, 'lo')
    if spanned:
        s.uline([a, (nut, 0), b], STRING)
        s.box(nut, stock1 + 1.5, 0.0, 0.0, (226, 214, 180))                # bolt
        s.prof(stock1 + 0.5, stock1 + 3.0, lambda u: min(0.75, (stock1 + 3.0 - u) / 1.5), (200, 204, 216))
    s.curve(pts, th, M.tex(s))
    s.box(u_prod - 0.5, u_prod + 0.5, -1.0, 1.0, M.trim)
    s.box(nut - 0.5, nut, -0.5, 0.5, M.trim)
    s.curve([(stock0 + 4.5, 1.0), (stock0 + 5.5, 2.0), (stock0 + 7.0, 2.0)], 0.3, M.trim)   # trigger
    if heavy:
        s.curve([(stock0 + 1.0, -1.0), (stock0 + 1.0, -3.0), (stock0 + 2.5, -3.0)], 0.4, M.trim)   # windlass crank
        s.disc(stock0 + 3.0, -3.0, 0.75, LEATHER)
        s.box(stock0, stock0 + 0.5, -1.0, 1.0, M.trim)


def r_light_crossbow(s, M):
    _xbow(s, M, 6.0, 19.5, 5.0, 20.0, 0.45)


def r_heavy_crossbow(s, M):
    _xbow(s, M, 8.5, 20.5, 1.5, 21.0, 0.75, heavy=True)


def r_crossbow(s, M):
    _xbow(s, M, 7.5, 20.0, 3.5, 22.5, 0.6, spanned=False)
    s.curve([(22.5, -1.0), (24.5, -1.0), (24.5, 1.0), (22.5, 1.0)], 0.3, M.trim)   # stirrup


def r_sling(s, M, stone=STONE):
    s.curve([(9.0, -3.0), (14.0, -3.5), (19.0, -2.0), (24.0, -0.5)], 0.3, STRING)
    s.curve([(9.0, 3.0), (14.0, 3.0), (18.0, 1.5), (21.0, 1.5)], 0.3, STRING)
    arc = [(6.5 - 3.6 * math.cos(math.radians(a)), 3.4 * math.sin(math.radians(a))) for a in range(-125, 126, 10)]
    s.curve(arc, 1.0, M.tex(s))
    s.curve([(24.0, -0.5), (25.5, -0.5), (25.5, 1.0), (24.0, 1.0), (24.0, -0.5)], 0.25, M.trim)   # finger loop
    s.disc(21.0, 1.5, 0.6, LEATHER)                                                              # release knot
    s.sell(21, 23, 25, 27, stone)                                                                # shot
    s.postxy([(22, 24)], (214, 214, 216))


def r_lockpick(s, M):
    t = M.tex(s)
    s.box(4.0, 11.0, -1.0, 1.0, M.grip)
    s.erase(lambda u, v: abs(u - 6.0) <= 0.5 and abs(v) <= 0.1)
    s.box(11.0, 22.0, 0.0, 0.5, t)
    s.curve([(22.0, 0.25), (23.5, -0.5), (24.0, -2.0)], 0.4, t)
    s.box(10.5, 11.0, -1.0, 1.0, M.trim)


RIGS = {
    'shortsword': r_shortsword, 'longsword': r_longsword, 'sword': r_sword, 'bastard_sword': r_bastard_sword,
    'greatsword': r_greatsword, 'zweihander': r_zweihander, 'rapier': r_rapier, 'scimitar': r_scimitar,
    'dagger': r_dagger, 'katana': r_katana, 'executioners_sword': r_executioner,
    'axe': r_axe, 'battleaxe': r_battleaxe, 'great_axe': r_great_axe, 'greataxe': r_greataxe,
    'halberd': r_halberd, 'glaive': r_glaive, 'spear': r_spear,
    'club': r_club, 'mace': r_mace, 'morningstar': r_morningstar, 'warhammer': r_warhammer,
    'hammer': r_hammer, 'maul': r_maul, 'flail': r_flail, 'quarterstaff': r_quarterstaff, 'staff': r_staff,
    'longbow': r_longbow, 'shortbow': r_shortbow, 'composite_bow': r_composite_bow,
    'light_crossbow': r_light_crossbow, 'heavy_crossbow': r_heavy_crossbow, 'crossbow': r_crossbow,
    'sling': r_sling, 'lockpick': r_lockpick,
}


# ------------------------------------------------------------------ ammo
def arrow(s, v0, u0, u1, head, fletch, shaft=(214, 190, 150), hw=1.0, hl=3.0, fl=3.5):
    s.prof(u0, u0 + fl, lambda u: min(1.0, (u - u0) * 0.8 + 0.5), fletch, cv=v0)
    s.box(u0 + 0.5, u1 - 1.0, v0, v0, shaft)
    s.prof(u1 - hl, u1, lambda u: max(0.0, min(hw, (u1 - u) / (hl / (hw + 0.5)))), head, cv=v0)


def bolt(s, v0, u0, u1, head, fletch, shaft=(170, 124, 76), hw=1.0):
    s.box(u0, u1 - 2.0, v0 - 0.5, v0, shaft)
    s.prof(u0, u0 + 2.5, 1.0, fletch, cv=v0 - 0.25)
    s.box(u0 + 0.5, u0 + 2.0, v0 - 0.5, v0, shaft)
    s.prof(u1 - 3.5, u1, lambda u: max(0.0, min(hw, (u1 - u) / 2.0)), head, cv=v0 - 0.25)
