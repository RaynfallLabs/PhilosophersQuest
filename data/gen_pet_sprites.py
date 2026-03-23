#!/usr/bin/env python3
"""
Generate 32x32 pixel-art sprites for Soul Sphere pet companions + Fenrir.
Output: assets/tiles/monsters/{name}.png  (RGBA, transparent background)
Usage:  python data/gen_pet_sprites.py
"""
import math, os, sys
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install Pillow"); sys.exit(1)

ROOT    = os.path.join(os.path.dirname(__file__), '..')
OUT_DIR = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
S       = 32
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
def _c(r,g,b,a=255): return (int(r),int(g),int(b),int(a))
def dk(c, f=0.42):   return _c(c[0]*f, c[1]*f, c[2]*f)
def lt(c, f=1.45):   return _c(min(255,c[0]*f), min(255,c[1]*f), min(255,c[2]*f))
def mx(a,b,t=0.5):   return _c(a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t, a[2]*(1-t)+b[2]*t)

TRANSPARENT = (0,0,0,0)
BLK  = _c(10,10,10)
WHT  = _c(255,255,255)

def new_canvas():
    img = Image.new('RGBA', (S, S), TRANSPARENT)
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

def apply_highlight(img):
    px = img.load()
    for y in range(S):
        for x in range(S):
            r,g,b,a = px[x,y]
            if a < 20: continue
            if x < 3 and y < 3:
                px[x,y] = (min(255,r+30), min(255,g+30), min(255,b+30), a)


# ===========================================================================
# ELECTRIC PET LINE: Zappik -> Voltpaw -> Thundertail
# ===========================================================================

def gen_zappik():
    """Tiny yellow rodent with crackling sparks — stage 0 electric pet."""
    P = _c(255, 230, 50)
    D = dk(P, 0.5)
    img, d = new_canvas()
    cx = S // 2

    # Body (small round rodent)
    ell(d, cx-5, 14, cx+5, 24, P, D)
    # Belly
    ell(d, cx-3, 17, cx+3, 23, lt(P, 1.2))

    # Head
    ell(d, cx-4, 8, cx+4, 16, P, D)
    # Ears (pointed)
    poly(d, [(cx-4, 10), (cx-6, 4), (cx-2, 8)], P, D)
    poly(d, [(cx+4, 10), (cx+6, 4), (cx+2, 8)], P, D)
    # Ear tips darker
    d.point((cx-5, 5), fill=dk(P, 0.7))
    d.point((cx+5, 5), fill=dk(P, 0.7))

    # Eyes
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 10, cx+ox+1, 12], fill=BLK)
        shine(d, cx+ox, 10)
    # Nose
    d.point((cx, 13), fill=_c(200, 80, 80))

    # Cheek sparks (red circles)
    for ox in (-4, 4):
        ell(d, cx+ox-1, 12, cx+ox+1, 14, _c(220, 60, 60))

    # Tail (zigzag lightning bolt shape)
    d.line([(cx+5, 20), (cx+8, 16), (cx+6, 14), (cx+10, 10)], fill=D, width=1)
    d.line([(cx+5, 19), (cx+8, 15), (cx+6, 13), (cx+10, 9)], fill=P, width=1)

    # Spark effects
    for sx, sy in [(cx-7, 6), (cx+9, 8), (cx+11, 12)]:
        d.point((sx, sy), fill=WHT)

    # Feet
    for ox in (-3, 1):
        rect(d, cx+ox, 23, cx+ox+2, 26, dk(P, 0.7))

    apply_highlight(img)
    return img


def gen_voltpaw():
    """Medium electric beast with jagged fur — stage 1 electric pet."""
    P = _c(255, 220, 40)
    D = dk(P, 0.5)
    L = lt(P, 1.2)
    img, d = new_canvas()
    cx = S // 2

    # Body (larger, more muscular)
    ell(d, cx-7, 12, cx+7, 24, P, D)
    ell(d, cx-5, 15, cx+5, 22, L)

    # Head
    ell(d, cx-5, 4, cx+5, 14, P, D)
    # Spiky fur on head
    for sx in range(-4, 5, 2):
        poly(d, [(cx+sx, 5), (cx+sx+1, 1), (cx+sx+2, 5)], lt(P, 1.1))

    # Eyes (fiercer)
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 7, cx+ox+1, 10], fill=BLK)
        d.point((cx+ox, 8), fill=_c(255, 255, 200))
    # Nose
    d.point((cx, 11), fill=_c(40, 40, 40))

    # Cheek sparks
    for ox in (-5, 5):
        ell(d, cx+ox-1, 9, cx+ox+1, 11, _c(255, 80, 80))

    # Jagged tail (bigger lightning bolt)
    d.line([(cx+7, 18), (cx+11, 14), (cx+9, 11), (cx+13, 6), (cx+11, 4)],
           fill=D, width=2)
    d.line([(cx+7, 17), (cx+11, 13), (cx+9, 10), (cx+13, 5)],
           fill=P, width=1)

    # Legs
    for ox in (-5, -1, 3):
        rect(d, cx+ox, 23, cx+ox+2, 28, dk(P, 0.6))

    # Electric aura dots
    for sx, sy in [(2, 3), (28, 5), (3, 20), (29, 18)]:
        d.point((sx, sy), fill=WHT)
        d.point((sx+1, sy), fill=_c(255, 255, 180, 140))

    apply_highlight(img)
    return img


def gen_thundertail():
    """Massive electric beast with lightning mane — stage 2 electric pet."""
    P = _c(255, 210, 30)
    D = dk(P, 0.45)
    L = lt(P, 1.3)
    BOLT = _c(255, 255, 200)
    img, d = new_canvas()
    cx = S // 2

    # Body (large, powerful)
    ell(d, cx-8, 12, cx+8, 26, P, D)
    ell(d, cx-6, 15, cx+6, 24, L)

    # Head
    ell(d, cx-6, 2, cx+6, 14, P, D)
    # Lightning mane (spiky crown)
    for sx in range(-5, 6, 2):
        h = 4 if abs(sx) < 3 else 3
        poly(d, [(cx+sx, 3), (cx+sx+1, -h+2), (cx+sx+2, 3)], BOLT)

    # Fierce eyes
    for ox in (-3, 3):
        d.ellipse([cx+ox-2, 6, cx+ox+1, 10], fill=BLK)
        d.ellipse([cx+ox-1, 7, cx+ox, 9], fill=BOLT)

    # Cheek lightning bolts
    for ox in (-6, 6):
        d.line([(cx+ox, 8), (cx+ox+(1 if ox > 0 else -1)*3, 10)], fill=BOLT, width=1)

    # Tail (massive lightning bolt)
    pts = [(cx+8, 18), (cx+12, 14), (cx+10, 12), (cx+14, 7),
           (cx+12, 6), (cx+15, 2)]
    d.line(pts, fill=D, width=2)
    d.line(pts, fill=P, width=1)
    d.point((cx+15, 2), fill=WHT)

    # Legs (sturdy)
    for ox in (-6, -2, 2, 6):
        rect(d, cx+ox, 24, cx+ox+2, 30, dk(P, 0.55))

    # Electric aura
    for sx, sy in [(1, 1), (30, 2), (0, 16), (31, 20), (cx, 30)]:
        d.point((sx, sy), fill=BOLT)

    apply_highlight(img)
    return img


# ===========================================================================
# WATER PET LINE: Shellkit -> Tideshell -> Torrentoise
# ===========================================================================

def gen_shellkit():
    """Small blue turtle hatchling — stage 0 water pet."""
    P = _c(80, 160, 255)
    D = dk(P, 0.5)
    SHELL = _c(60, 120, 80)
    SHELL_LT = lt(SHELL, 1.3)
    img, d = new_canvas()
    cx = S // 2

    # Shell (domed)
    ell(d, cx-6, 12, cx+6, 24, SHELL, dk(SHELL, 0.5))
    ell(d, cx-5, 13, cx+5, 23, SHELL_LT)
    # Shell pattern (cross lines)
    d.line([(cx, 13), (cx, 23)], fill=SHELL, width=1)
    d.line([(cx-5, 18), (cx+5, 18)], fill=SHELL, width=1)

    # Head (poking out front)
    ell(d, cx-4, 6, cx+4, 14, P, D)
    # Eyes
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 8, cx+ox+1, 10], fill=BLK)
        shine(d, cx+ox, 8)
    # Smile
    d.arc([cx-2, 10, cx+2, 13], 0, 180, fill=D, width=1)

    # Flippers (four small stubs)
    for ox, oy in [(-7, 16), (7, 16), (-6, 22), (6, 22)]:
        ell(d, cx+ox-2, oy, cx+ox+1, oy+3, P, D)

    # Tail (tiny)
    d.line([(cx, 23), (cx, 27)], fill=P, width=1)

    # Water droplets
    for sx, sy in [(cx-8, 8), (cx+8, 10)]:
        d.point((sx, sy), fill=_c(160, 210, 255))

    apply_highlight(img)
    return img


def gen_tideshell():
    """Armored water turtle with wave crest — stage 1 water pet."""
    P = _c(70, 140, 240)
    D = dk(P, 0.45)
    SHELL = _c(50, 100, 70)
    SHELL_LT = lt(SHELL, 1.4)
    FOAM = _c(180, 220, 255)
    img, d = new_canvas()
    cx = S // 2

    # Shell (larger, more defined)
    ell(d, cx-8, 10, cx+8, 24, dk(SHELL, 0.6), dk(SHELL, 0.3))
    ell(d, cx-7, 11, cx+7, 23, SHELL)
    # Shell segments
    d.line([(cx, 11), (cx, 23)], fill=dk(SHELL, 0.7), width=1)
    d.line([(cx-7, 17), (cx+7, 17)], fill=dk(SHELL, 0.7), width=1)
    # Shell highlights
    ell(d, cx-4, 12, cx-1, 16, SHELL_LT)
    ell(d, cx+1, 12, cx+4, 16, SHELL_LT)

    # Head
    ell(d, cx-5, 3, cx+5, 12, P, D)
    # Eyes (more determined)
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 5, cx+ox+1, 8], fill=BLK)
        d.point((cx+ox, 6), fill=_c(200, 240, 255))

    # Wave crest on shell top
    for wx in range(cx-6, cx+7, 3):
        poly(d, [(wx, 11), (wx+1, 8), (wx+2, 11)], FOAM)

    # Sturdier flippers
    for ox, oy in [(-9, 14), (9, 14), (-8, 21), (8, 21)]:
        ell(d, cx+ox-2, oy, cx+ox+2, oy+3, P, D)

    # Tail
    poly(d, [(cx, 23), (cx-2, 28), (cx+2, 28)], P, D)

    apply_highlight(img)
    return img


def gen_torrentoise():
    """Massive armored turtle with water cannons — stage 2 water pet."""
    P = _c(60, 120, 220)
    D = dk(P, 0.4)
    SHELL = _c(40, 85, 55)
    SHELL_LT = lt(SHELL, 1.5)
    CANNON = _c(100, 100, 110)
    WATER = _c(120, 190, 255)
    img, d = new_canvas()
    cx = S // 2

    # Massive shell
    ell(d, cx-10, 8, cx+10, 26, dk(SHELL, 0.5), dk(SHELL, 0.25))
    ell(d, cx-9, 9, cx+9, 25, SHELL)
    # Shell plate pattern
    d.line([(cx, 9), (cx, 25)], fill=dk(SHELL, 0.6), width=1)
    d.line([(cx-9, 17), (cx+9, 17)], fill=dk(SHELL, 0.6), width=1)
    for ox, oy in [(-5, 11), (3, 11), (-5, 18), (3, 18)]:
        ell(d, cx+ox, oy, cx+ox+4, oy+5, SHELL_LT)

    # Water cannons on shell
    for ox in (-6, 6):
        rect(d, cx+ox-1, 7, cx+ox+1, 12, CANNON, dk(CANNON, 0.5))
        # Water jet
        d.line([(cx+ox, 7), (cx+ox, 3)], fill=WATER, width=1)
        d.point((cx+ox, 3), fill=WHT)

    # Head (armored)
    ell(d, cx-6, 1, cx+6, 11, P, D)
    rect(d, cx-5, 2, cx+5, 6, lt(P, 0.8), D)  # head armor plate
    # Eyes
    for ox in (-3, 3):
        d.ellipse([cx+ox-1, 5, cx+ox+1, 8], fill=BLK)
        d.ellipse([cx+ox, 6, cx+ox+1, 7], fill=WATER)

    # Powerful legs
    for ox in (-9, -3, 3, 9):
        rect(d, cx+ox-1, 24, cx+ox+1, 30, P, D)
        rect(d, cx+ox-2, 28, cx+ox+2, 31, dk(P, 0.6))  # claws

    apply_highlight(img)
    return img


# ===========================================================================
# PLANT PET LINE: Seedling -> Thornback -> Bloomsaur
# ===========================================================================

def gen_seedling():
    """Squat green creature with a bulb on its back — stage 0 plant pet."""
    P = _c(80, 180, 80)
    D = dk(P, 0.5)
    BULB = _c(60, 140, 60)
    BULB_LT = lt(BULB, 1.3)
    img, d = new_canvas()
    cx = S // 2

    # Body (squat, round)
    ell(d, cx-5, 14, cx+5, 26, P, D)
    ell(d, cx-3, 16, cx+3, 24, lt(P, 1.15))

    # Bulb on back (large onion shape)
    ell(d, cx-4, 6, cx+4, 16, BULB, dk(BULB, 0.5))
    ell(d, cx-3, 7, cx+3, 14, BULB_LT)
    # Bulb tip (leaves)
    poly(d, [(cx-1, 6), (cx, 2), (cx+1, 6)], _c(40, 120, 40))
    poly(d, [(cx-2, 5), (cx-4, 1), (cx, 5)], _c(60, 150, 50))
    poly(d, [(cx+2, 5), (cx+4, 1), (cx, 5)], _c(60, 150, 50))

    # Head/face on body
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 16, cx+ox+1, 18], fill=BLK)
        shine(d, cx+ox, 16)
    # Smile
    d.arc([cx-2, 18, cx+2, 21], 0, 180, fill=D, width=1)

    # Stubby legs
    for ox in (-3, 1):
        rect(d, cx+ox, 25, cx+ox+2, 29, dk(P, 0.7))

    apply_highlight(img)
    return img


def gen_thornback():
    """Thorny plant beast with vines — stage 1 plant pet."""
    P = _c(70, 160, 70)
    D = dk(P, 0.45)
    THORN = _c(100, 80, 40)
    FLOWER = _c(255, 120, 180)
    img, d = new_canvas()
    cx = S // 2

    # Body (larger, more beast-like)
    ell(d, cx-7, 12, cx+7, 26, P, D)
    ell(d, cx-5, 14, cx+5, 24, lt(P, 1.1))

    # Thorny back ridge
    for sx in range(-5, 6, 3):
        poly(d, [(cx+sx, 12), (cx+sx+1, 7), (cx+sx+2, 12)], THORN)

    # Head
    ell(d, cx-5, 4, cx+5, 14, P, D)
    # Eyes (red, more aggressive)
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 7, cx+ox+1, 10], fill=_c(200, 40, 40))
        d.point((cx+ox, 8), fill=_c(255, 100, 100))

    # Vine tendrils
    d.line([(cx-7, 16), (cx-11, 12), (cx-13, 14)], fill=dk(P, 0.7), width=1)
    d.line([(cx+7, 16), (cx+11, 12), (cx+13, 14)], fill=dk(P, 0.7), width=1)

    # Small flower buds on vines
    ell(d, cx-14, 13, cx-12, 15, FLOWER)
    ell(d, cx+12, 13, cx+14, 15, FLOWER)

    # Legs
    for ox in (-5, -1, 3):
        rect(d, cx+ox, 25, cx+ox+2, 30, dk(P, 0.6))

    apply_highlight(img)
    return img


def gen_bloomsaur():
    """Giant flowering dinosaur-plant — stage 2 plant pet."""
    P = _c(60, 150, 60)
    D = dk(P, 0.4)
    FLOWER = _c(255, 80, 150)
    FLOWER_LT = lt(FLOWER, 1.3)
    PETAL = _c(255, 140, 200)
    POLLEN = _c(255, 230, 80)
    img, d = new_canvas()
    cx = S // 2

    # Body (dinosaur-like, large)
    ell(d, cx-9, 12, cx+9, 28, P, D)
    ell(d, cx-7, 14, cx+7, 26, lt(P, 1.1))

    # Massive flower on back
    # Petals
    for angle_off in range(0, 360, 45):
        rad = math.radians(angle_off)
        px = cx + int(6 * math.cos(rad))
        py = 7 + int(5 * math.sin(rad))
        ell(d, px-2, py-2, px+2, py+2, PETAL if angle_off % 90 else FLOWER)
    # Center
    ell(d, cx-2, 5, cx+2, 9, POLLEN, FLOWER)

    # Head (long neck)
    ell(d, cx-5, 2, cx+5, 12, P, D)
    # Eyes
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 5, cx+ox+1, 8], fill=BLK)
        d.point((cx+ox, 6), fill=_c(200, 255, 200))
    # Mouth
    d.line([(cx-2, 9), (cx+2, 9)], fill=D, width=1)

    # Leaf frills on neck
    poly(d, [(cx-5, 10), (cx-8, 6), (cx-4, 8)], lt(P, 1.2))
    poly(d, [(cx+5, 10), (cx+8, 6), (cx+4, 8)], lt(P, 1.2))

    # Sturdy legs
    for ox in (-7, -2, 2, 7):
        rect(d, cx+ox-1, 26, cx+ox+1, 31, dk(P, 0.55))

    # Tail with small flower
    d.line([(cx+9, 20), (cx+13, 22), (cx+14, 20)], fill=P, width=2)
    ell(d, cx+13, 18, cx+16, 21, FLOWER)

    apply_highlight(img)
    return img


# ===========================================================================
# FIRE PET LINE: Emberpup -> Flamescale -> Infernodrake
# ===========================================================================

def gen_emberpup():
    """Small red dragon-like creature — stage 0 fire pet."""
    P = _c(220, 70, 30)
    D = dk(P, 0.45)
    FLAME = _c(255, 180, 40)
    FLAME_LT = _c(255, 230, 80)
    img, d = new_canvas()
    cx = S // 2

    # Body (small dragon pup)
    ell(d, cx-5, 14, cx+5, 24, P, D)
    ell(d, cx-3, 16, cx+3, 22, lt(P, 1.2))

    # Head
    ell(d, cx-4, 6, cx+4, 14, P, D)
    # Snout
    ell(d, cx-2, 10, cx+2, 14, lt(P, 1.1))
    # Eyes
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 8, cx+ox+1, 10], fill=_c(255, 200, 40))
        d.point((cx+ox, 8), fill=BLK)
    # Nostrils
    d.point((cx-1, 12), fill=D)
    d.point((cx+1, 12), fill=D)

    # Small horns
    poly(d, [(cx-3, 7), (cx-4, 3), (cx-2, 6)], dk(P, 0.7))
    poly(d, [(cx+3, 7), (cx+4, 3), (cx+2, 6)], dk(P, 0.7))

    # Tiny wings
    poly(d, [(cx-5, 14), (cx-10, 10), (cx-8, 16)], dk(P, 0.7), D)
    poly(d, [(cx+5, 14), (cx+10, 10), (cx+8, 16)], dk(P, 0.7), D)

    # Tail with flame tip
    d.line([(cx+5, 20), (cx+9, 18), (cx+11, 20)], fill=P, width=2)
    ell(d, cx+10, 17, cx+13, 21, FLAME)
    d.point((cx+11, 18), fill=FLAME_LT)

    # Feet
    for ox in (-3, 1):
        rect(d, cx+ox, 23, cx+ox+2, 27, dk(P, 0.6))

    # Small flame breath
    for fx, fy in [(cx-1, 5), (cx, 4), (cx+1, 5)]:
        d.point((fx, fy), fill=FLAME)

    apply_highlight(img)
    return img


def gen_flamescale():
    """Medium dragon with fiery scales and spread wings — stage 1 fire pet."""
    P = _c(200, 60, 25)
    D = dk(P, 0.4)
    FLAME = _c(255, 160, 30)
    SCALE_LT = _c(255, 100, 50)
    img, d = new_canvas()
    cx = S // 2

    # Body
    ell(d, cx-6, 14, cx+6, 26, P, D)
    # Scale pattern
    for sy in range(16, 24, 3):
        for sx in range(cx-4, cx+5, 3):
            d.point((sx, sy), fill=SCALE_LT)

    # Head (longer snout)
    ell(d, cx-5, 4, cx+5, 14, P, D)
    poly(d, [(cx-2, 10), (cx, 14), (cx+2, 10)], lt(P, 1.1))  # snout
    # Eyes
    for ox in (-2, 2):
        d.ellipse([cx+ox-1, 6, cx+ox+1, 9], fill=_c(255, 200, 30))
        d.point((cx+ox, 7), fill=BLK)

    # Horns (larger)
    poly(d, [(cx-4, 5), (cx-6, 0), (cx-3, 4)], dk(P, 0.6))
    poly(d, [(cx+4, 5), (cx+6, 0), (cx+3, 4)], dk(P, 0.6))

    # Wings (spread wider)
    poly(d, [(cx-6, 14), (cx-14, 6), (cx-12, 16)], dk(P, 0.65), D)
    poly(d, [(cx+6, 14), (cx+14, 6), (cx+12, 16)], dk(P, 0.65), D)
    # Wing membrane lines
    d.line([(cx-6, 14), (cx-13, 8)], fill=FLAME, width=1)
    d.line([(cx+6, 14), (cx+13, 8)], fill=FLAME, width=1)

    # Tail with flame
    d.line([(cx+6, 22), (cx+10, 20), (cx+12, 22), (cx+14, 18)], fill=P, width=2)
    ell(d, cx+12, 15, cx+16, 19, FLAME)
    d.point((cx+14, 16), fill=_c(255, 240, 120))

    # Legs
    for ox in (-4, 0, 4):
        rect(d, cx+ox, 25, cx+ox+2, 30, dk(P, 0.55))

    apply_highlight(img)
    return img


def gen_infernodrake():
    """Massive fire dragon wreathed in flames — stage 2 fire pet."""
    P = _c(180, 50, 20)
    D = dk(P, 0.35)
    FLAME = _c(255, 140, 20)
    FLAME_LT = _c(255, 220, 60)
    MAGMA = _c(255, 80, 20)
    img, d = new_canvas()
    cx = S // 2

    # Body (massive)
    ell(d, cx-10, 12, cx+10, 28, P, D)
    # Molten belly
    ell(d, cx-7, 16, cx+7, 26, MAGMA)
    ell(d, cx-5, 18, cx+5, 24, FLAME)

    # Head (armored, fierce)
    ell(d, cx-6, 0, cx+6, 12, P, D)
    # Jaw plates
    rect(d, cx-4, 8, cx+4, 12, dk(P, 0.7))
    # Eyes (glowing)
    for ox in (-3, 3):
        d.ellipse([cx+ox-1, 4, cx+ox+1, 7], fill=FLAME_LT)
        d.point((cx+ox, 5), fill=WHT)

    # Large horns
    poly(d, [(cx-5, 3), (cx-8, -3), (cx-4, 2)], dk(P, 0.5))
    poly(d, [(cx+5, 3), (cx+8, -3), (cx+4, 2)], dk(P, 0.5))

    # Massive wings
    poly(d, [(cx-10, 12), (cx-15, 2), (cx-14, 14)], dk(P, 0.55), D)
    poly(d, [(cx+10, 12), (cx+15, 2), (cx+14, 14)], dk(P, 0.55), D)
    # Wing flames
    for wx in range(-14, -9, 2):
        d.point((cx+wx, 3), fill=FLAME)
    for wx in range(10, 15, 2):
        d.point((cx+wx, 3), fill=FLAME)

    # Flame breath particles from mouth
    for fx, fy in [(cx-2, -1), (cx, -2), (cx+2, -1), (cx-1, -3), (cx+1, -3)]:
        d.point((max(0, min(31, fx)), max(0, min(31, fy))), fill=FLAME_LT)

    # Tail
    d.line([(cx+10, 22), (cx+14, 20), (cx+15, 24)], fill=P, width=2)

    # Legs
    for ox in (-8, -3, 3, 8):
        rect(d, cx+ox-1, 26, cx+ox+1, 31, dk(P, 0.45))

    apply_highlight(img)
    return img


# ===========================================================================
# FENRIR — Legendary wolf pet from XYZZY tier 5
# ===========================================================================

def gen_fenrir():
    """Colossal frost wolf — Fenrir, the World-Devourer. Icy blue-white."""
    P = _c(140, 170, 210)
    D = dk(P, 0.4)
    L = lt(P, 1.3)
    FROST = _c(200, 225, 255)
    EYE = _c(100, 200, 255)
    FANG = _c(240, 240, 250)
    img, d = new_canvas()
    cx = S // 2

    # Body (massive wolf, fills most of the tile)
    ell(d, cx-10, 10, cx+10, 26, P, D)
    # Fur belly (lighter)
    ell(d, cx-7, 14, cx+7, 24, L)
    # Fur texture lines
    for fy in range(12, 24, 3):
        d.line([(cx-8, fy), (cx-6, fy+1)], fill=dk(P, 0.7), width=1)
        d.line([(cx+6, fy+1), (cx+8, fy)], fill=dk(P, 0.7), width=1)

    # Head (wolf-like, prominent)
    ell(d, cx-7, 1, cx+7, 12, P, D)
    # Snout
    poly(d, [(cx-3, 8), (cx, 14), (cx+3, 8)], lt(P, 0.9), D)
    # Nose
    ell(d, cx-1, 11, cx+1, 13, BLK)

    # Eyes (glowing ice blue)
    for ox in (-3, 3):
        d.ellipse([cx+ox-2, 4, cx+ox+1, 8], fill=BLK)
        d.ellipse([cx+ox-1, 5, cx+ox, 7], fill=EYE)
        d.point((cx+ox-1, 5), fill=WHT)

    # Ears (large, pointed)
    poly(d, [(cx-5, 3), (cx-7, -3), (cx-3, 2)], P, D)
    poly(d, [(cx+5, 3), (cx+7, -3), (cx+3, 2)], P, D)
    # Inner ear
    d.point((cx-5, 0), fill=lt(P, 1.1))
    d.point((cx+5, 0), fill=lt(P, 1.1))

    # Fangs
    d.line([(cx-2, 12), (cx-2, 15)], fill=FANG, width=1)
    d.line([(cx+2, 12), (cx+2, 15)], fill=FANG, width=1)

    # Frost mane (spiky fur around neck)
    for sx in range(-6, 7, 2):
        h = 3 if abs(sx) < 4 else 2
        poly(d, [(cx+sx, 10), (cx+sx+1, 10-h), (cx+sx+2, 10)], FROST)

    # Powerful legs
    for ox in (-8, -3, 3, 8):
        rect(d, cx+ox-1, 24, cx+ox+1, 30, dk(P, 0.55))
        # Claws
        d.point((cx+ox-1, 30), fill=FANG)
        d.point((cx+ox+1, 30), fill=FANG)

    # Bushy tail (curved up)
    poly(d, [(cx+10, 16), (cx+14, 12), (cx+15, 16), (cx+12, 18)], L, D)
    # Frost sparkle on tail
    d.point((cx+14, 13), fill=FROST)

    # Frost aura particles
    for fx, fy in [(1, 4), (30, 6), (0, 22), (31, 20), (cx-10, 8), (cx+10, 8)]:
        fx, fy = max(0, min(31, fx)), max(0, min(31, fy))
        d.point((fx, fy), fill=(*FROST[:3], 160))

    apply_highlight(img)
    return img


# ===========================================================================
# DEADITE — Necronomicon undead pet (Army of Darkness spell)
# ===========================================================================

def gen_deadite():
    """Shambling undead minion with glowing eyes and tattered clothes."""
    SKIN = _c(120, 140, 100)    # sickly green-grey
    D    = dk(SKIN, 0.45)
    CLOTH = _c(80, 60, 50)      # tattered brown rags
    CLOTH_D = dk(CLOTH, 0.5)
    EYE  = _c(180, 40, 40)      # glowing red eyes
    BONE = _c(200, 190, 160)
    BLOOD = _c(120, 20, 20)
    img, d = new_canvas()
    cx = S // 2

    # Body (hunched torso)
    ell(d, cx-6, 12, cx+6, 26, SKIN, D)
    # Tattered shirt/rags
    rect(d, cx-5, 14, cx+5, 24, CLOTH, CLOTH_D)
    # Rips in cloth (skin showing through)
    d.line([(cx-3, 16), (cx-1, 20)], fill=SKIN, width=1)
    d.line([(cx+2, 18), (cx+4, 22)], fill=SKIN, width=1)
    # Blood stains
    d.point((cx-2, 19), fill=BLOOD)
    d.point((cx+1, 21), fill=BLOOD)
    d.point((cx+3, 17), fill=BLOOD)

    # Head (slightly tilted, undead)
    ell(d, cx-5, 2, cx+4, 12, SKIN, D)
    # Sunken cheeks
    ell(d, cx-4, 6, cx-2, 10, dk(SKIN, 0.7))
    ell(d, cx+1, 6, cx+3, 10, dk(SKIN, 0.7))

    # Glowing red eyes (asymmetric for creepy effect)
    d.ellipse([cx-4, 5, cx-2, 7], fill=EYE)
    d.point((cx-3, 5), fill=lt(EYE, 1.5))
    d.ellipse([cx+1, 4, cx+3, 7], fill=EYE)
    d.point((cx+2, 5), fill=lt(EYE, 1.5))

    # Gaping mouth
    rect(d, cx-3, 8, cx+2, 11, _c(40, 20, 20))
    # Teeth (jagged)
    for tx in range(cx-2, cx+2):
        if tx % 2 == 0:
            d.point((tx, 8), fill=BONE)
            d.point((tx, 10), fill=BONE)

    # Arms (reaching forward, one higher than other)
    # Left arm (raised)
    d.line([(cx-6, 14), (cx-10, 10), (cx-12, 12)], fill=SKIN, width=2)
    # Claw fingers
    d.line([(cx-12, 12), (cx-13, 10)], fill=BONE, width=1)
    d.line([(cx-12, 12), (cx-14, 11)], fill=BONE, width=1)
    # Right arm (lower)
    d.line([(cx+6, 16), (cx+10, 14), (cx+12, 16)], fill=SKIN, width=2)
    d.line([(cx+12, 16), (cx+13, 14)], fill=BONE, width=1)
    d.line([(cx+12, 16), (cx+14, 15)], fill=BONE, width=1)

    # Legs (shambling stance, uneven)
    rect(d, cx-4, 25, cx-2, 30, dk(SKIN, 0.6))
    rect(d, cx+1, 24, cx+3, 31, dk(SKIN, 0.6))
    # Tattered pant cuffs
    d.line([(cx-5, 25), (cx-1, 25)], fill=CLOTH_D, width=1)
    d.line([(cx, 24), (cx+4, 24)], fill=CLOTH_D, width=1)

    # Dark aura wisps
    for fx, fy in [(cx-8, 6), (cx+7, 4), (cx-9, 20), (cx+9, 18)]:
        fx, fy = max(0, min(31, fx)), max(0, min(31, fy))
        d.point((fx, fy), fill=_c(80, 40, 80, 140))

    apply_highlight(img)
    return img


# ===========================================================================
# Run
# ===========================================================================

GENERATORS = {
    # Electric line
    'zappik':        gen_zappik,
    'voltpaw':       gen_voltpaw,
    'thundertail':   gen_thundertail,
    # Water line
    'shellkit':      gen_shellkit,
    'tideshell':     gen_tideshell,
    'torrentoise':   gen_torrentoise,
    # Plant line
    'seedling':      gen_seedling,
    'thornback':     gen_thornback,
    'bloomsaur':     gen_bloomsaur,
    # Fire line
    'emberpup':      gen_emberpup,
    'flamescale':    gen_flamescale,
    'infernodrake':  gen_infernodrake,
    # Fenrir (XYZZY legendary)
    'fenrir':        gen_fenrir,
    # Deadite (Necronomicon / Army of Darkness)
    'deadite':       gen_deadite,
}

if __name__ == '__main__':
    for name, fn in GENERATORS.items():
        img = fn()
        path = os.path.join(OUT_DIR, f'{name}.png')
        img.save(path)
        print(f"  {name:20s} -> {path}")
    print(f"\nDone — {len(GENERATORS)} pet sprites written to {OUT_DIR}")
