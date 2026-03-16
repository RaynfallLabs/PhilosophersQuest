#!/usr/bin/env python3
"""
Generate 32x32 pixel-art sprites for:
  - Player character
  - Environment tiles: wall, floor, stairs_up, stairs_down, door, altar

Output: assets/tiles/env/{id}.png  (RGBA, transparent background for player;
         solid background for tiles)
Usage:  python data/gen_env_sprites.py
"""
import math, os, sys
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install Pillow"); sys.exit(1)

ROOT    = os.path.join(os.path.dirname(__file__), '..')
OUT_DIR = os.path.join(ROOT, 'assets', 'tiles', 'env')
S       = 32
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour helpers (same style as gen_monster_sprites.py)
# ---------------------------------------------------------------------------
def _c(r,g,b,a=255): return (int(r),int(g),int(b),int(a))
def C(lst, a=255):   return _c(*lst[:3], a)
def dk(c, f=0.42):   return _c(c[0]*f, c[1]*f, c[2]*f)
def lt(c, f=1.45):   return _c(min(255,c[0]*f), min(255,c[1]*f), min(255,c[2]*f))
def mx(a,b,t=0.5):   return _c(a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t, a[2]*(1-t)+b[2]*t)

TRANSPARENT = (0,0,0,0)
BLK  = _c(10,10,10)
WHT  = _c(255,255,255)
GOLD = _c(255,210,50)

def new_canvas(bg=TRANSPARENT):
    img = Image.new('RGBA', (S, S), bg)
    return img, ImageDraw.Draw(img)

def ell(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline: d.ellipse([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.ellipse([x0,y0,x1,y1], fill=fill)

def rect(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline: d.rectangle([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.rectangle([x0,y0,x1,y1], fill=fill)

def poly(d, pts, fill, outline=None):
    if outline and len(pts) >= 3: d.polygon(pts, fill=outline)
    d.polygon(pts, fill=fill)

def shine(d, x, y, c=WHT):
    d.point((int(x), int(y)), fill=c)

def eyes(d, cx, cy, P, D, col=None, sep=3, r=1):
    col = col or _c(255,200,80)
    for ox in (-sep, sep):
        d.ellipse([cx+ox-r, cy-r, cx+ox+r, cy+r], fill=D)
        d.ellipse([cx+ox-r+1, cy-r+1, cx+ox+r-1, cy+r-1], fill=col)

def add_wings(d, P, D, mid_y, spread=10, cx=S//2):
    wc = dk(P, 0.6)
    poly(d, [(cx-4,mid_y),(cx-4-spread,mid_y-7),(cx-4-spread+3,mid_y+5)], wc, D)
    poly(d, [(cx+4,mid_y),(cx+4+spread,mid_y-7),(cx+4+spread-3,mid_y+5)], wc, D)

def apply_highlight(img):
    """Brighten top-left edges slightly for a lit 3D effect."""
    px = img.load()
    for y in range(S):
        for x in range(S):
            r,g,b,a = px[x,y]
            if a < 20: continue
            edge = (x == 0 or y == 0 or
                    (x < 3 and y < 3))
            if edge:
                px[x,y] = (min(255,r+40), min(255,g+40), min(255,b+40), a)


# ---------------------------------------------------------------------------
# TILE: wall
# ---------------------------------------------------------------------------
def gen_wall():
    """Mortared stone-brick wall — 4 columns × 4 rows of blocks."""
    img, d = new_canvas(bg=_c(28,28,32))
    STONE    = _c(88, 85, 92)
    STONE_LT = _c(108,104,112)
    STONE_DK = _c(58, 55, 62)
    MORTAR   = _c(22, 20, 24)

    bw, bh = 7, 7          # brick size
    for row in range(4):
        offset = (row % 2) * 3    # stagger every other row
        for col in range(5):
            x0 = col * bw + offset - 1
            y0 = row * bh + 1
            x1 = x0 + bw - 1
            y1 = y0 + bh - 2
            if x1 > S: continue
            # vary shade slightly per brick
            shade = (row * 3 + col * 7) % 18 - 9
            fill = _c(STONE[0]+shade, STONE[1]+shade, STONE[2]+shade)
            d.rectangle([x0, y0, x1, y1], fill=fill)
            # top-left highlight
            d.line([(x0, y0), (x1-1, y0)], fill=STONE_LT, width=1)
            d.line([(x0, y0), (x0, y1-1)], fill=STONE_LT, width=1)
            # bottom-right shadow
            d.line([(x0+1, y1), (x1, y1)], fill=STONE_DK, width=1)
            d.line([(x1, y0+1), (x1, y1)], fill=STONE_DK, width=1)

    return img


# ---------------------------------------------------------------------------
# TILE: floor
# ---------------------------------------------------------------------------
def gen_floor():
    """Dark flagstone floor — large slabs with subtle grout lines."""
    img, d = new_canvas(bg=_c(18, 16, 14))
    STONE = _c(42, 38, 34)
    GROUT = _c(14, 12, 10)
    STONE_LT = _c(52, 48, 44)

    # 2×2 large flagstones (each ~14px)
    slabs = [
        (1,  1, 14, 14),
        (17, 1, 30, 14),
        (1, 17, 14, 30),
        (17,17, 30, 30),
    ]
    offsets = [(0,0),(1,-1),(-1,1),(0,1)]   # slight irregularity per slab
    for (x0,y0,x1,y1),(dx,dy) in zip(slabs, offsets):
        # tiny variation per slab
        v = (x0 * 3 + y0 * 5) % 10 - 5
        fill = _c(STONE[0]+v, STONE[1]+v, STONE[2]+v)
        d.rectangle([x0+dx, y0+dy, x1+dx, y1+dy], fill=fill)
        # subtle top-left highlight
        d.line([(x0+dx,y0+dy),(x1+dx,y0+dy)], fill=STONE_LT, width=1)
        d.line([(x0+dx,y0+dy),(x0+dx,y1+dy)], fill=STONE_LT, width=1)
    return img


# ---------------------------------------------------------------------------
# TILE: stairs_down
# ---------------------------------------------------------------------------
def gen_stairs_down():
    """Descending staircase — steps receding into darkness with a golden edge."""
    img, d = new_canvas(bg=_c(18, 16, 14))
    # Steps from top (bright) to bottom (dark abyss)
    # 5 steps, each 5px tall
    steps = [
        (_c(68,62,50),  _c(90,82,68),  2, 2,  29, 6),
        (_c(55,50,40),  _c(74,67,54),  4, 7,  27, 11),
        (_c(42,38,30),  _c(60,54,42),  6, 12, 25, 16),
        (_c(30,27,20),  _c(48,42,32),  8, 17, 23, 21),
        (_c(18,16,12),  _c(36,30,22), 10, 22, 21, 26),
    ]
    for (fill, edge, x0,y0,x1,y1) in steps:
        d.rectangle([x0, y0, x1, y1], fill=fill)
        d.line([(x0, y0), (x1, y0)], fill=edge, width=1)
        d.line([(x0, y0), (x0, y1)], fill=_c(28,24,18), width=1)

    # Golden chevron (↓) on top step
    cx = S//2
    gy = 3
    pts = [(cx-4,gy),(cx,gy+4),(cx+4,gy)]
    d.polygon(pts, fill=GOLD)
    d.polygon([(cx-2,gy+3),(cx,gy+7),(cx+2,gy+3)], fill=lt(GOLD,0.9))

    # Dark pit at bottom
    d.rectangle([11, 23, 20, 30], fill=_c(8,6,4))
    return img


# ---------------------------------------------------------------------------
# TILE: stairs_up
# ---------------------------------------------------------------------------
def gen_stairs_up():
    """Ascending staircase — steps rising toward light."""
    img, d = new_canvas(bg=_c(18, 16, 14))
    # Steps from bottom (dark) to top (bright, near golden)
    steps = [
        (_c(68,62,50),  _c(95,86,70),  2, 24, 29, 29),
        (_c(75,68,54),  _c(102,93,76), 4, 19, 27, 24),
        (_c(82,76,60),  _c(112,102,84),6, 14, 25, 19),
        (_c(90,84,68),  _c(122,112,94),8,  9, 23, 14),
        (_c(100,93,76), _c(135,124,104),10, 4, 21,  9),
    ]
    for (fill, edge, x0,y0,x1,y1) in steps:
        d.rectangle([x0, y0, x1, y1], fill=fill)
        d.line([(x0, y0), (x1, y0)], fill=edge, width=1)
        d.line([(x0, y1), (x1, y1)], fill=dk(fill, 0.6), width=1)
        d.line([(x0, y0), (x0, y1)], fill=dk(fill, 0.6), width=1)

    # Golden chevron (↑) pointing up
    cx = S//2
    gy = 26
    pts = [(cx-4,gy),(cx,gy-4),(cx+4,gy)]
    d.polygon(pts, fill=GOLD)
    d.polygon([(cx-2,gy-3),(cx,gy-7),(cx+2,gy-3)], fill=lt(GOLD,0.9))
    return img


# ---------------------------------------------------------------------------
# TILE: door (closed)
# ---------------------------------------------------------------------------
def gen_door():
    """Sturdy wooden door — planks, crossbar, iron hinges, arched frame."""
    FRAME   = _c(55, 35, 18)
    WOOD    = _c(110, 68, 30)
    PLANK   = _c(128, 82, 40)
    PLANK_LT= _c(148, 98, 52)
    PLANK_DK= _c(88,  52, 20)
    IRON    = _c(80,  80, 85)

    img, d = new_canvas(bg=_c(18,16,14))

    # Stone frame
    d.rectangle([0, 0, 31, 31], fill=FRAME)
    # Door panel (inset 3px from sides, 2px from top/bottom)
    d.rectangle([4, 3, 27, 28], fill=WOOD)

    # Vertical plank grain lines
    for px in range(4, 28, 4):
        d.line([(px, 3),(px, 28)], fill=PLANK_DK, width=1)

    # Horizontal crossbar (middle-ish)
    d.rectangle([4, 13, 27, 16], fill=PLANK_DK)
    d.line([(4,13),(27,13)], fill=PLANK_LT, width=1)

    # Top panel
    d.rectangle([6, 5, 25, 12], fill=PLANK)
    d.line([(6,5),(25,5)], fill=PLANK_LT, width=1)
    d.line([(6,5),(6,12)], fill=PLANK_LT, width=1)
    d.line([(25,5),(25,12)], fill=PLANK_DK, width=1)
    d.line([(6,12),(25,12)], fill=PLANK_DK, width=1)

    # Bottom panel
    d.rectangle([6, 17, 25, 26], fill=PLANK)
    d.line([(6,17),(25,17)], fill=PLANK_LT, width=1)
    d.line([(6,17),(6,26)], fill=PLANK_LT, width=1)
    d.line([(25,17),(25,26)], fill=PLANK_DK, width=1)
    d.line([(6,26),(25,26)], fill=PLANK_DK, width=1)

    # Iron hinge — left side, two
    for hy in [6, 22]:
        d.rectangle([3, hy, 6, hy+3], fill=IRON)
        d.point((4, hy+1), fill=lt(IRON, 1.5))

    # Door knob
    ell(d, 22, 14, 25, 17, IRON, dk(IRON, 0.5))
    shine(d, 23, 15)

    return img


# ---------------------------------------------------------------------------
# TILE: altar
# ---------------------------------------------------------------------------
def gen_altar():
    """Sacred stone altar — raised dais with glowing golden rune."""
    STONE   = _c(78, 72, 82)
    STONE_LT= _c(102, 96, 108)
    STONE_DK= _c(50, 46, 54)
    GLOW    = _c(255, 215, 60, 140)
    RUNE    = _c(255, 230, 100)

    img, d = new_canvas(bg=_c(18,16,14))

    # Glow aura beneath altar
    for r in range(14, 2, -2):
        a = int(60 * (1 - r/14))
        d.ellipse([S//2-r, S//2-r+2, S//2+r, S//2+r+2], fill=(*GLOW[:3], a))

    # Base slab (wide, flat)
    d.rectangle([2, 22, 29, 30], fill=STONE)
    d.line([(2, 22),(29,22)], fill=STONE_LT, width=1)
    d.line([(2, 22),(2, 30)], fill=STONE_LT, width=1)
    d.line([(29,22),(29,30)], fill=STONE_DK, width=1)
    d.line([(2, 30),(29,30)], fill=STONE_DK, width=1)

    # Mid pillar
    d.rectangle([5, 14, 26, 22], fill=STONE)
    d.line([(5,14),(26,14)], fill=STONE_LT, width=1)
    d.line([(5,14),(5,22)], fill=STONE_LT, width=1)
    d.line([(26,14),(26,22)], fill=STONE_DK, width=1)

    # Top altar surface
    d.rectangle([3, 10, 28, 15], fill=STONE_LT)
    d.line([(3,10),(28,10)], fill=lt(STONE_LT,1.2), width=1)

    # Golden rune cross on top surface
    cx, ry = S//2, 12
    # vertical bar
    for py in range(ry-4, ry+4):
        d.point((cx, py), fill=RUNE)
    # horizontal bar
    for px in range(cx-4, cx+4):
        d.point((px, ry), fill=RUNE)
    # glow dots at ends of cross
    for gx,gy in [(cx,ry-4),(cx,ry+3),(cx-4,ry),(cx+3,ry)]:
        d.ellipse([gx-1,gy-1,gx+1,gy+1], fill=(*RUNE[:3],180))

    # Small candles on altar surface corners
    for cx_ in [7, 23]:
        d.rectangle([cx_-1, 7, cx_+1, 11], fill=_c(240,220,160))  # candle body
        d.ellipse([cx_-1,5,cx_+1,8], fill=_c(255,200,60,200))     # flame

    return img


# ---------------------------------------------------------------------------
# SPRITE: player
# ---------------------------------------------------------------------------
def gen_player():
    """The player character — armoured explorer with lantern and blue cloak."""
    P  = _c(75, 130, 195)   # blue armour primary
    L  = lt(P, 1.35)        # light blue
    D  = dk(P, 0.5)         # dark shadow
    H  = lt(P, 1.7)         # bright highlight
    CLOAK   = _c(35, 45, 80)
    CLOAK_LT= lt(CLOAK, 1.4)
    SKIN    = _c(210, 170, 130)
    SKIN_DK = dk(SKIN, 0.75)
    IRON    = _c(140, 145, 155)
    IRON_LT = lt(IRON, 1.3)
    GOLD_   = _c(220, 185, 60)

    img, d = new_canvas()
    cx = S // 2

    # ── Cloak (behind body, wider) ──────────────────────────────────────────
    poly(d, [(cx-9, 8),(cx-7,28),(cx+7,28),(cx+9,8)], CLOAK, D)
    d.line([(cx, 10),(cx, 27)], fill=CLOAK_LT, width=1)   # cloak center fold

    # ── Legs ────────────────────────────────────────────────────────────────
    rect(d, cx-5, 20, cx-1, 28, dk(P,0.7), D)
    rect(d, cx+1, 20, cx+5, 28, dk(P,0.7), D)
    # boots
    rect(d, cx-6, 26, cx-1, 30, _c(50,38,24), D)
    rect(d, cx+1, 26, cx+6, 30, _c(50,38,24), D)

    # ── Torso (plate armour) ─────────────────────────────────────────────────
    rect(d, cx-5, 11, cx+5, 21, P, D)
    # breastplate highlight
    d.line([(cx-4,12),(cx+4,12)], fill=L, width=1)
    d.line([(cx-4,12),(cx-4,20)], fill=L, width=1)
    # belly band
    d.line([(cx-5,19),(cx+5,19)], fill=D, width=1)
    # centre line
    d.line([(cx, 12),(cx, 19)], fill=D, width=1)

    # ── Arms ────────────────────────────────────────────────────────────────
    rect(d, cx-8, 12, cx-5, 21, dk(P,0.8), D)
    rect(d, cx+5, 12, cx+8, 21, dk(P,0.8), D)
    # pauldrons
    rect(d, cx-8, 11, cx-4, 14, IRON, IRON_LT)
    rect(d, cx+4, 11, cx+8, 14, IRON, IRON_LT)

    # ── Left hand: sword hilt ───────────────────────────────────────────────
    # blade (pointing up-left)
    d.line([(cx-9,21),(cx-13,10)], fill=IRON_LT, width=1)
    d.line([(cx-8,21),(cx-12,10)], fill=IRON, width=1)
    # crossguard
    d.line([(cx-13,15),(cx-7,15)], fill=GOLD_, width=2)
    # pommel
    ell(d, cx-12,20, cx-8,24, GOLD_, dk(GOLD_,0.5))

    # ── Right hand: lantern ─────────────────────────────────────────────────
    # lantern glow (soft)
    for r in range(5,0,-1):
        a = int(60 * (1-r/5))
        d.ellipse([cx+8-r,17-r,cx+8+r,17+r], fill=(255,200,60,a))
    # lantern body
    rect(d, cx+7, 14, cx+12, 20, _c(80,75,70), _c(50,45,40))
    d.rectangle([cx+8,15,cx+11,19], fill=_c(255,210,80,200))  # flame window
    # handle
    d.line([(cx+8,14),(cx+8,12)], fill=_c(80,75,70), width=1)

    # ── Head (with helmet) ───────────────────────────────────────────────────
    # helmet
    ell(d, cx-5,  2, cx+5,  9, IRON, D)
    # face opening
    ell(d, cx-3,  5, cx+3,  9, SKIN, SKIN_DK)
    # visor slit
    d.line([(cx-3,7),(cx+3,7)], fill=D, width=1)
    # helmet crest
    poly(d, [(cx-1,2),(cx,0),(cx+1,2)], GOLD_)
    # plume
    d.line([(cx, 0),(cx-2,-2)], fill=_c(200,50,50), width=1)   # red plume tip
    # eyes gleam
    for ox in (-1, 1):
        d.point((cx+ox*2, 7), fill=_c(255,220,120))

    # ── Neck ────────────────────────────────────────────────────────────────
    rect(d, cx-2, 9, cx+2, 12, SKIN, SKIN_DK)

    apply_highlight(img)
    return img


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
GENERATORS = {
    'wall':        gen_wall,
    'floor':       gen_floor,
    'stairs_up':   gen_stairs_up,
    'stairs_down': gen_stairs_down,
    'door':        gen_door,
    'altar':       gen_altar,
    'player':      gen_player,
}

if __name__ == '__main__':
    for name, fn in GENERATORS.items():
        img = fn()
        path = os.path.join(OUT_DIR, f'{name}.png')
        img.save(path)
        print(f"  {name:20s} -> {path}")
    print(f"\nDone — {len(GENERATORS)} sprites written to {OUT_DIR}")
