#!/usr/bin/env python3
"""
Step 2: Read data/monsters_art_brief.json and generate 32x32 PNG sprites.
Output: assets/tiles/monsters/{id}.png  (RGBA, transparent background)
Usage:  python data/gen_monster_sprites.py
"""
import json, math, os, sys
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install Pillow"); sys.exit(1)

ROOT      = os.path.join(os.path.dirname(__file__), '..')
BRIEF_IN  = os.path.join(ROOT, 'data',   'monsters_art_brief.json')
OUT_DIR   = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
S         = 32          # canvas size
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
def _c(r,g,b,a=255): return (int(r),int(g),int(b),int(a))
def C(lst, a=255):   return _c(*lst[:3], a)  # list -> RGBA tuple

def dk(c, f=0.42):   return _c(c[0]*f, c[1]*f, c[2]*f)
def lt(c, f=1.45):   return _c(min(255,c[0]*f), min(255,c[1]*f), min(255,c[2]*f))
def mx(a,b,t=0.5):   return _c(a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t, a[2]*(1-t)+b[2]*t)

BONE   = _c(220,215,190)
RED_EYE= _c(255, 40, 40)
YLW_EYE= _c(255,230, 40)
WHT    = _c(255,255,255)
BLK    = _c( 10, 10, 10)
GOLD   = _c(255,210, 50)
FIRE_O = _c(255,140, 30)
FIRE_Y = _c(255,230, 60)
ICE_B  = _c(160,220,255)

TRANSPARENT = (0,0,0,0)

def new_canvas():
    return Image.new('RGBA', (S, S), TRANSPARENT)

# Draw helpers ---------------------------------------------------------------
def ell(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline:
        d.ellipse([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.ellipse([x0,y0,x1,y1], fill=fill)

def rect(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline:
        d.rectangle([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.rectangle([x0,y0,x1,y1], fill=fill)

def poly(d, pts, fill, outline=None, ow=1):
    if outline and len(pts) >= 3:
        exp = []
        cx_ = sum(p[0] for p in pts)/len(pts)
        cy_ = sum(p[1] for p in pts)/len(pts)
        for x,y in pts:
            dx,dy = x-cx_, y-cy_
            ln = math.hypot(dx,dy)
            if ln:
                exp.append((x+dx/ln*ow, y+dy/ln*ow))
            else:
                exp.append((x,y))
        d.polygon(exp, fill=outline)
    d.polygon(pts, fill=fill)

def line(d, pts, fill, w=2):
    for i in range(len(pts)-1):
        d.line([pts[i], pts[i+1]], fill=fill, width=w)

def dot(img, x, y, fill, r=1):
    draw = ImageDraw.Draw(img)
    x,y = int(x),int(y)
    draw.ellipse([x-r,y-r,x+r,y+r], fill=fill)

def eyes(d, cx, cy, P, D, col=None, sep=3, r=1):
    col = col or RED_EYE
    for ox in (-sep, sep):
        d.ellipse([cx+ox-r, cy-r, cx+ox+r, cy+r], fill=D)
        d.ellipse([cx+ox-r+1, cy-r+1, cx+ox+r-1, cy+r-1], fill=col)

def shine(d, x, y, c=WHT):
    d.point((int(x), int(y)), fill=c)

# Feature overlays -----------------------------------------------------------
def add_wings(d, P, D, mid_y, spread=10, cx=S//2):
    wc = dk(P, 0.6)
    # Left wing
    poly(d, [(cx-4,mid_y),(cx-4-spread,mid_y-7),(cx-4-spread+3,mid_y+5)], wc, D)
    # Right wing
    poly(d, [(cx+4,mid_y),(cx+4+spread,mid_y-7),(cx+4+spread-3,mid_y+5)], wc, D)

def add_horns(d, P, cx, head_top, horn_h=5):
    hc = dk(P, 0.55)
    poly(d, [(cx-4,head_top+2),(cx-6,head_top-horn_h),(cx-2,head_top)], hc, BLK)
    poly(d, [(cx+4,head_top+2),(cx+6,head_top-horn_h),(cx+2,head_top)], hc, BLK)

def add_tail(d, P, base_x, base_y):
    tc = dk(P, 0.65)
    # Curved tail: three segments curling right and down
    pts = [(base_x, base_y),(base_x-4,base_y+4),(base_x-6,base_y+8),(base_x-4,base_y+10)]
    line(d, pts, tc, 2)
    poly(d, [(base_x-3,base_y+10),(base_x-5,base_y+13),(base_x-1,base_y+12)], tc)

def add_staff(d, P, cx, top_y, bot_y):
    sc = mx(P, GOLD, 0.4)
    d.line([(cx+6,top_y),(cx+6,bot_y)], fill=dk(P,0.5), width=2)
    d.line([(cx+6,top_y+1),(cx+6,bot_y-1)], fill=sc, width=1)
    # orb at top
    ell(d, cx+4,top_y-3, cx+8,top_y+1, lt(P,1.6), dk(P,0.4))

def add_crown(d, cx, top_y):
    pts = [(cx-5,top_y+1),(cx-5,top_y-3),(cx-3,top_y-1),
           (cx,top_y-4),(cx+3,top_y-1),(cx+5,top_y-3),(cx+5,top_y+1)]
    poly(d, pts, GOLD, dk(GOLD,0.5))

def add_armor_lines(d, tx0, ty0, tx1, ty1, D):
    # Horizontal plate lines on torso
    mid = (ty0+ty1)//2
    d.line([(tx0,mid),(tx1,mid)], fill=D, width=1)
    d.line([(tx0,(ty0+mid)//2),(tx1,(ty0+mid)//2)], fill=D, width=1)

def add_flames(d, base_x, base_y, count=3):
    for i in range(count):
        ox = (i - count//2) * 4
        h  = 5 + i % 2 * 3
        poly(d, [(base_x+ox, base_y),
                  (base_x+ox-2, base_y-h),
                  (base_x+ox+2, base_y-h//2),
                  (base_x+ox+1, base_y-h-2),
                  (base_x+ox+3, base_y-h+1)],
              FIRE_O)
        poly(d, [(base_x+ox,base_y),(base_x+ox-1,base_y-h+2),(base_x+ox+1,base_y-h+2)],
              FIRE_Y)

def add_ice_crystals(d, cx, top_y):
    for ox, ang in [(-5, -20), (0, 0), (5, -10)]:
        tip_x = cx + ox
        poly(d, [(tip_x-1,top_y+2),(tip_x,top_y-4),(tip_x+1,top_y+2)], ICE_B, dk(ICE_B,0.6))

def add_glow_aura(img, cx, cy, radius, P):
    """Add a soft glow ring by drawing semi-transparent pixels around subject."""
    draw = ImageDraw.Draw(img, 'RGBA')
    gc = (*P[:3], 55)
    draw.ellipse([cx-radius,cy-radius,cx+radius,cy+radius], fill=gc)

def add_skull_face(d, cx, hy, r, P):
    D_ = dk(P, 0.35)
    # eye sockets
    for ox in (-r//2+1, r//2-1):
        d.ellipse([cx+ox-2,hy-1,cx+ox+2,hy+3], fill=D_)
    # nasal cavity
    d.ellipse([cx-1,hy+3,cx+1,hy+5], fill=D_)
    # teeth
    tw = max(1, r//3)
    for tx in range(cx-r+2, cx+r-1, 3):
        d.rectangle([tx,hy+r-2,tx+1,hy+r+1], fill=BONE)

# ---------------------------------------------------------------------------
# Silhouette drawing functions
# ---------------------------------------------------------------------------

def draw_humanoid(d, P, L, D, H, feats, size=1.0, head_r_base=5, crown=False):
    """Generic biped humanoid — used for medium, caster, small, large variants."""
    cx = S // 2
    s  = size

    # ── torso ────────────────────────────────────────────────────────────────
    tw = int(10 * s); th = int(12 * s)
    tx0 = cx - tw//2; tx1 = cx + tw//2
    ty0 = S - 3 - th - int(7*s); ty1 = ty0 + th
    rect(d, tx0, ty0, tx1, ty1, P, D)

    # ── legs ─────────────────────────────────────────────────────────────────
    lw = max(2, int(4*s)); lh = int(7*s)
    rect(d, tx0, ty1, tx0+lw, ty1+lh, dk(P,0.75), D)
    rect(d, tx1-lw, ty1, tx1, ty1+lh, dk(P,0.75), D)
    # feet
    rect(d, tx0-1, ty1+lh-1, tx0+lw+1, ty1+lh+2, dk(P,0.6))

    # ── arms ─────────────────────────────────────────────────────────────────
    aw = max(2, int(3*s)); ah = int(10*s)
    rect(d, tx0-aw, ty0+2, tx0, ty0+2+ah, dk(P,0.8), D)
    rect(d, tx1,    ty0+2, tx1+aw, ty0+2+ah, dk(P,0.8), D)

    # ── head ─────────────────────────────────────────────────────────────────
    hr   = int(head_r_base * s)
    hcx  = cx; hcy = ty0 - hr - 1
    ell(d, hcx-hr, hcy-hr, hcx+hr, hcy+hr, L, D)

    if 'skull' in feats:
        add_skull_face(d, hcx, hcy-hr//2, hr, P)
    else:
        eyes(d, hcx, hcy, P, D)
        shine(d, hcx-hr+2, hcy-hr+2)

    # ── features ─────────────────────────────────────────────────────────────
    if 'wings' in feats:  add_wings(d, P, D, ty0+4, spread=int(11*s))
    if 'horns' in feats:  add_horns(d, L, hcx, hcy-hr, horn_h=int(5*s))
    if 'crown' in feats:  add_crown(d, hcx, hcy-hr)
    if 'armor' in feats:  add_armor_lines(d, tx0, ty0, tx1, ty1, D)
    if 'staff' in feats:  add_staff(d, P, cx, ty0-2, ty1+lh)
    if 'flames' in feats: add_flames(d, cx, ty0-1)
    if 'ice'   in feats:  add_ice_crystals(d, cx, hcy-hr-2)
    if 'tail'  in feats:  add_tail(d, P, tx1, ty0+th//2)
    if 'tentacles' in feats:
        for ox in (-8,-4,0,4,8):
            d.line([(cx+ox,ty1),(cx+ox+ox//2,ty1+6)], fill=dk(P,0.7), width=2)


def draw_humanoid_large(d, P, L, D, H, feats, size=1.3):
    draw_humanoid(d, P, L, D, H, feats, size=size, head_r_base=6)


def draw_humanoid_small(d, P, L, D, H, feats, size=0.72):
    draw_humanoid(d, P, L, D, H, feats, size=size, head_r_base=5)


def draw_humanoid_caster(d, P, L, D, H, feats, size=1.0):
    feats = set(feats) | {'staff'}
    draw_humanoid(d, P, L, D, H, feats, size=size, head_r_base=5)


def draw_lich_caster(d, P, L, D, H, feats, size=1.05):
    feats = set(feats) | {'skull', 'staff'}
    draw_humanoid(d, P, BONE, D, H, feats, size=size, head_r_base=6)


def draw_undead_skeleton(d, P, L, D, H, feats, size=1.0):
    cx = S // 2; s = size
    col = BONE; shad = dk(BONE, 0.55)

    # pelvis/legs
    lh = int(9*s)
    lx0 = cx-int(4*s); lx1 = cx+int(4*s)
    bot = S - 3
    rect(d, lx0, bot-lh, lx0+int(3*s), bot, col, shad)
    rect(d, lx1-int(3*s), bot-lh, lx1, bot, col, shad)

    # spine
    sy0 = bot-lh-int(14*s); sy1 = bot-lh
    d.line([(cx, sy0),(cx, sy1)], fill=col, width=2)
    # ribs
    for ry in range(sy0+3, sy0+int(12*s), int(3*s)):
        d.line([(cx-int(5*s),ry),(cx,ry-1)], fill=col, width=1)
        d.line([(cx+int(5*s),ry),(cx,ry-1)], fill=col, width=1)

    # arms
    d.line([(cx-int(5*s),sy0+3),(cx-int(8*s),sy0+int(10*s))], fill=col, width=2)
    d.line([(cx+int(5*s),sy0+3),(cx+int(8*s),sy0+int(10*s))], fill=col, width=2)

    # skull
    hr = int(5*s)
    hcy = sy0 - hr
    ell(d, cx-hr, hcy-hr, cx+hr, hcy+hr, BONE, shad)
    add_skull_face(d, cx, hcy-hr//2+1, hr, BONE)

    if 'staff' in feats:   add_staff(d, P, cx, sy0-2, bot)
    if 'crown' in feats:   add_crown(d, cx, hcy-hr)
    if 'flames' in feats:  add_flames(d, cx, sy0)
    if 'wings'  in feats:  add_wings(d, BONE, shad, sy0+4, spread=int(9*s))


def draw_undead_ghost(d, P, L, D, H, feats, size=1.0, img=None):
    cx = S//2; s = size
    # Wispy teardrop body — wide top, tapers to wispy bottom
    body_pts = [
        (cx-int(9*s), S//2-2),
        (cx-int(7*s), S//2-int(8*s)),
        (cx, S//2-int(12*s)),
        (cx+int(7*s), S//2-int(8*s)),
        (cx+int(9*s), S//2-2),
        (cx+int(6*s), S//2+int(5*s)),
        (cx+int(3*s), S//2+int(9*s)),
        (cx+int(1*s), S//2+int(12*s)),
        (cx-int(1*s), S//2+int(9*s)),
        (cx-int(3*s), S//2+int(5*s)),
    ]
    poly(d, body_pts, (*P[:3], 200), D)
    # Inner lighter core
    inner = [(int(x*0.6+cx*0.4), int(y*0.6+(S//2)*0.4)) for x,y in body_pts]
    poly(d, inner, (*L[:3], 180))

    # Eyes — haunting hollow look
    eye_y = S//2 - int(6*s)
    for ox in (-3,3):
        d.ellipse([cx+ox-2,eye_y-2,cx+ox+2,eye_y+2], fill=D)
        d.ellipse([cx+ox-1,eye_y-1,cx+ox+1,eye_y+1], fill=YLW_EYE)

    if 'glow' in feats and img:
        add_glow_aura(img, cx, S//2-int(4*s), int(12*s), P)
    if 'crown' in feats: add_crown(d, cx, S//2-int(11*s))
    if 'flames' in feats:
        for ox in (-4,0,4):
            d.line([(cx+ox, S//2+int(10*s)),(cx+ox,S-2)], fill=FIRE_O, width=2)


def draw_undead_zombie(d, P, L, D, H, feats, size=1.0):
    """Shambling undead — slouched biped with decay marks."""
    cx = S//2; s = size
    # Offset body — hunched forward
    tcx = cx + int(2*s)
    tw = int(10*s); th = int(11*s)
    tx0 = tcx-tw//2; tx1 = tcx+tw//2
    ty0 = S-3-th-int(6*s); ty1 = ty0+th
    rect(d, tx0,ty0,tx1,ty1, dk(P,0.8), D)

    # Decay cracks on torso
    d.line([(tx0+2,ty0+3),(tx0+5,ty0+8)], fill=D, width=1)
    d.line([(tx1-3,ty0+4),(tx1-6,ty0+9)], fill=D, width=1)

    # Uneven legs
    lw = int(4*s); lh = int(6*s)
    rect(d, tx0,ty1, tx0+lw,ty1+lh, dk(P,0.7), D)
    rect(d, tx1-lw,ty1+int(2*s), tx1,ty1+lh+int(2*s), dk(P,0.7), D)

    # Long dragging left arm
    d.line([(tx0,ty0+3),(cx-int(10*s),ty1+2)], fill=dk(P,0.75), width=3)
    # Right arm slightly raised
    d.line([(tx1,ty0+3),(cx+int(8*s),ty0-2)], fill=dk(P,0.75), width=3)

    # Head — slightly forward
    hr = int(5*s); hcx = tcx+2; hcy = ty0-hr-1
    ell(d, hcx-hr,hcy-hr,hcx+hr,hcy+hr, L, D)
    eyes(d, hcx, hcy, P, D, col=YLW_EYE, sep=3)


def draw_vampire_noble(d, P, L, D, H, feats, size=1.05):
    cx = S//2; s = size
    # Cape behind — dark triangle
    cape_c = dk(P, 0.45)
    poly(d, [(cx-int(10*s),S-3),(cx,S//2-int(2*s)),(cx+int(10*s),S-3)], cape_c, D)

    # Torso — narrow, elegant
    tw = int(8*s); th = int(12*s)
    tx0 = cx-tw//2; tx1 = cx+tw//2
    ty0 = S-3-th-int(7*s); ty1 = ty0+th
    rect(d, tx0,ty0,tx1,ty1, P, D)

    # Collar — white/light
    poly(d, [(cx-int(5*s),ty0),(cx,ty0-int(3*s)),(cx+int(5*s),ty0)], lt(P,1.8), D)

    # Legs
    lw=int(3*s); lh=int(7*s)
    rect(d, tx0,ty1,tx0+lw,ty1+lh, dk(P,0.8), D)
    rect(d, tx1-lw,ty1,tx1,ty1+lh, dk(P,0.8), D)

    # Arms inside cape — narrow
    d.line([(tx0,ty0+3),(cx-int(9*s),ty0+int(8*s))], fill=dk(P,0.7), width=2)
    d.line([(tx1,ty0+3),(cx+int(9*s),ty0+int(8*s))], fill=dk(P,0.7), width=2)

    # Head — pale
    hr = int(5*s); hcy = ty0-hr-1
    ell(d, cx-hr,hcy-hr,cx+hr,hcy+hr, lt(P,1.5), D)
    eyes(d, cx, hcy, P, D, col=RED_EYE)
    # Fangs
    d.line([(cx-2,hcy+hr-1),(cx-2,hcy+hr+2)], fill=WHT, width=1)
    d.line([(cx+2,hcy+hr-1),(cx+2,hcy+hr+2)], fill=WHT, width=1)

    if 'crown' in feats: add_crown(d, cx, hcy-hr)
    if 'glow'  in feats and True: pass  # handled by outer caller


def draw_werewolf(d, P, L, D, H, feats, size=1.1):
    cx = S//2; s = size
    # Hunched body — torso leans forward
    tw = int(12*s); th = int(10*s)
    tx0 = cx-tw//2+int(2*s); tx1 = cx+tw//2+int(2*s)
    ty0 = S-3-th-int(8*s); ty1 = ty0+th
    rect(d, tx0,ty0,tx1,ty1, P, D)

    # Thick haunches/legs
    lw = int(5*s); lh = int(9*s)
    rect(d, tx0,ty1,tx0+lw,ty1+lh, dk(P,0.8), D)
    rect(d, tx1-lw,ty1,tx1,ty1+lh, dk(P,0.8), D)
    # Paws
    rect(d, tx0-1,ty1+lh-1,tx0+lw+2,ty1+lh+3, dk(P,0.6))

    # Long arms reaching forward
    d.line([(tx0-2,ty0+3),(cx-int(12*s),ty1+2)], fill=dk(P,0.75), width=4)
    d.line([(tx1+2,ty0+3),(cx+int(6*s),ty0+int(4*s))], fill=dk(P,0.75), width=4)
    # Claws on left arm
    for ox in (-2,0,2):
        d.line([(cx-int(12*s)+ox,ty1+2),(cx-int(13*s)+ox,ty1+5)], fill=BLK, width=1)

    # Animal head — muzzle extends forward
    hr = int(6*s); hcx = cx-int(2*s); hcy = ty0-hr
    ell(d, hcx-hr,hcy-hr,hcx+hr,hcy+hr, L, D)
    # Snout / muzzle
    poly(d, [(hcx-int(4*s),hcy),(hcx+int(5*s),hcy-2),(hcx+int(7*s),hcy+int(2*s)),
              (hcx+int(5*s),hcy+int(4*s)),(hcx-int(4*s),hcy+int(3*s))], L, D)
    # Ears
    poly(d, [(hcx-int(3*s),hcy-hr),(hcx-int(6*s),hcy-hr-int(5*s)),(hcx,hcy-hr-1)], P, D)
    poly(d, [(hcx+int(3*s),hcy-hr),(hcx+int(5*s),hcy-hr-int(5*s)),(hcx+int(6*s),hcy-hr+2)], P, D)
    eyes(d, hcx+int(1*s), hcy-1, P, D, col=YLW_EYE, sep=3)


def draw_troll(d, P, L, D, H, feats, size=1.25):
    cx = S//2; s = size
    # Wide hunched body
    tw = int(16*s); th = int(12*s)
    tx0 = cx-tw//2; tx1 = cx+tw//2
    ty0 = S-3-th-int(7*s); ty1 = ty0+th
    rect(d, tx0,ty0,tx1,ty1, P, D)

    # Very long arms dragging low
    arm_bot = ty1+int(5*s)
    d.line([(tx0,ty0+3),(cx-int(12*s),arm_bot)], fill=dk(P,0.75), width=5)
    d.line([(tx1,ty0+3),(cx+int(12*s),arm_bot)], fill=dk(P,0.75), width=5)
    # Knuckles on ground
    for ox,by in [(-int(12*s),arm_bot),(int(12*s),arm_bot)]:
        ell(d, cx+ox-3, by-2, cx+ox+3, by+2, lt(P,1.2), D)

    # Stocky legs
    lw=int(6*s); lh=int(7*s)
    rect(d, tx0+int(2*s),ty1,tx0+int(2*s)+lw,ty1+lh, dk(P,0.8), D)
    rect(d, tx1-int(2*s)-lw,ty1,tx1-int(2*s),ty1+lh, dk(P,0.8), D)

    # Head — wide, low brow
    hw = int(9*s); hh = int(7*s); hcy = ty0-hh//2-2
    ell(d, cx-hw,hcy-hh,cx+hw,hcy+hh, L, D)
    # Brow ridge
    d.line([(cx-int(7*s),hcy-int(2*s)),(cx+int(7*s),hcy-int(2*s))], fill=D, width=2)
    eyes(d, cx, hcy-1, P, D, col=RED_EYE, sep=4)
    # Nose
    ell(d, cx-2,hcy+2,cx+2,hcy+5, dk(P,0.6))


def draw_construct_golem(d, P, L, D, H, feats, size=1.1):
    cx = S//2; s = size
    # Very blocky rectangular forms
    # Torso — wide slab
    tw = int(14*s); th = int(13*s)
    tx0=cx-tw//2; tx1=cx+tw//2; ty0=S-3-th-int(8*s); ty1=ty0+th
    rect(d, tx0,ty0,tx1,ty1, P, D)
    # Plate lines
    for ry in range(ty0+3, ty1, 4):
        d.line([(tx0+1,ry),(tx1-1,ry)], fill=D, width=1)

    # Square head
    hs = int(9*s); hx0=cx-hs//2; hy0=ty0-hs-2
    rect(d, hx0,hy0,hx0+hs,hy0+hs, L, D)
    # Rivets
    for rx,ry in [(hx0+2,hy0+2),(hx0+hs-2,hy0+2),(hx0+2,hy0+hs-2),(hx0+hs-2,hy0+hs-2)]:
        d.ellipse([rx-1,ry-1,rx+1,ry+1], fill=D)
    eyes(d, cx, hy0+hs//2, P, D, col=YLW_EYE, sep=3, r=2)

    # Thick block arms
    aw=int(5*s); ah=int(12*s)
    rect(d, tx0-aw,ty0+2,tx0,ty0+2+ah, P, D)
    rect(d, tx1,ty0+2,tx1+aw,ty0+2+ah, P, D)
    # Fists
    rect(d, tx0-aw-1,ty0+2+ah-3,tx0+1,ty0+2+ah+4, lt(P,1.2), D)
    rect(d, tx1-1,ty0+2+ah-3,tx1+aw+1,ty0+2+ah+4, lt(P,1.2), D)

    # Block legs
    lw=int(5*s); lh=int(7*s)
    rect(d, tx0+int(2*s),ty1,tx0+int(2*s)+lw,ty1+lh, P, D)
    rect(d, tx1-int(2*s)-lw,ty1,tx1-int(2*s),ty1+lh, P, D)

    if 'flames' in feats: add_flames(d, cx, ty0)
    if 'ice'    in feats: add_ice_crystals(d, cx, hy0-2)


def draw_dragon_large(d, P, L, D, H, feats, size=1.3):
    cx = S//2; s = size
    # Large swept body
    bw = int(17*s); bh = int(11*s)
    bx0=4; by0=S-4-bh; bx1=bx0+bw; by1=by0+bh
    ell(d, bx0,by0,bx1,by1, P, D)

    # Wings — large spread above body
    wc = dk(P, 0.65)
    wspan = int(13*s)
    poly(d, [(bx0+4,by0+3),(bx0-wspan+4,by0-int(9*s)),(bx0+int(5*s),by0)], wc, D)
    poly(d, [(bx1-4,by0+3),(bx1+int(1*s),by0-int(9*s)),(bx1-int(6*s),by0)], wc, D)
    # Wing membrane veins
    d.line([(bx0+4,by0+3),(bx0-wspan+4,by0-int(9*s))], fill=D, width=1)
    d.line([(bx1-4,by0+3),(bx1+int(1*s),by0-int(9*s))], fill=D, width=1)

    # Neck and head
    nw = int(5*s)
    nx0=bx1-int(6*s); ny_bot=by0; nx1=nx0+nw; ny_top=by0-int(8*s)
    poly(d, [(nx0,ny_bot),(nx1,ny_bot),(nx1+int(2*s),ny_top),(nx0-int(1*s),ny_top)], L, D)
    # Head — angular snout
    hn = int(7*s); hy0=ny_top-int(5*s)
    poly(d, [(nx0-int(2*s),ny_top),(nx1+int(4*s),ny_top),
              (nx1+int(8*s),hy0+int(3*s)),(nx1+int(7*s),hy0-int(1*s)),
              (nx0+int(2*s),hy0-int(1*s)),(nx0-int(2*s),hy0+int(2*s))], L, D)
    eyes(d, nx0+int(3*s), hy0, P, D, col=RED_EYE, sep=2)
    add_horns(d, P, nx0+int(2*s), hy0-1, horn_h=int(5*s))

    # Tail
    tx_start = bx0+2; ty_start = by0+bh//2
    pts=[(tx_start,ty_start),(tx_start-5,ty_start+4),
         (tx_start-8,ty_start+2),(tx_start-10,ty_start-2)]
    line(d, pts, dk(P,0.7), 3)
    poly(d, [(tx_start-9,ty_start-3),(tx_start-12,ty_start-1),(tx_start-10,ty_start+2)], D)

    # Legs
    for lx in [bx0+int(4*s), bx0+int(10*s)]:
        d.line([(lx,by1),(lx-2,by1+5)], fill=dk(P,0.75), width=3)
        # Claws
        for cx2 in [lx-4,lx-2,lx]:
            d.line([(cx2,by1+5),(cx2-1,by1+8)], fill=BLK, width=1)

    if 'flames' in feats: add_flames(d, nx1+int(7*s)-3, hy0-1)
    if 'ice'    in feats: add_ice_crystals(d, nx0+int(2*s), hy0-3)


def draw_dragon_small(d, P, L, D, H, feats, size=1.1):
    """Wyrm / wyvern — more serpentine, smaller wings."""
    cx = S//2; s = size
    bw=int(14*s); bh=int(9*s)
    bx0=5; by0=S-4-bh; bx1=bx0+bw; by1=by0+bh
    ell(d, bx0,by0,bx1,by1, P, D)

    # Smaller wings
    wc = dk(P, 0.6)
    poly(d, [(bx0+3,by0+2),(bx0-int(7*s),by0-int(5*s)),(bx0+int(4*s),by0+1)], wc, D)
    poly(d, [(bx1-3,by0+2),(bx1+int(3*s),by0-int(6*s)),(bx1-int(4*s),by0+1)], wc, D)

    # Neck
    nx0=bx1-int(5*s); ny_bot=by0+2; nx1=nx0+int(4*s); ny_top=by0-int(6*s)
    poly(d, [(nx0,ny_bot),(nx1,ny_bot),(nx1+int(2*s),ny_top),(nx0-1,ny_top)], L, D)
    # Head
    hy0=ny_top-int(4*s)
    poly(d, [(nx0-2,ny_top),(nx1+int(3*s),ny_top),(nx1+int(7*s),hy0+int(2*s)),
              (nx0,hy0)], L, D)
    eyes(d, nx0+int(2*s), hy0+1, P, D, col=YLW_EYE, sep=2)

    # Tail
    pts=[(bx0+2,by0+bh//2),(bx0-4,by0+bh//2+3),(bx0-7,by0+bh//2+1),(bx0-9,by0+bh//2-2)]
    line(d, pts, dk(P,0.7), 2)

    if 'flames' in feats: add_flames(d, nx1+int(6*s)-2, hy0-1, count=2)
    if 'ice'    in feats: add_ice_crystals(d, nx0+int(2*s), hy0-2)


def draw_blob_ooze(d, P, L, D, H, feats, size=1.0):
    cx = S//2; s = size
    # Irregular polygon blob
    r = int(11*s)
    pts = []
    steps = 12
    for i in range(steps):
        ang = 2*math.pi*i/steps
        jitter = 1 + 0.3*math.sin(i*2.3 + 1.1) + 0.2*math.cos(i*3.7)
        rr = r * jitter
        pts.append((cx + rr*math.cos(ang), (S//2+2) + rr*0.7*math.sin(ang)))
    poly(d, pts, P, D)
    # Inner lighter blob
    inner = [(cx+(x-cx)*0.6, (S//2+2)+(y-(S//2+2))*0.6) for x,y in pts]
    poly(d, inner, L)
    # Eyes — two simple dots
    ey = S//2 - int(1*s)
    for ox in (-3,3):
        ell(d, cx+ox-2,ey-2,cx+ox+2,ey+2, D)
        ell(d, cx+ox-1,ey-1,cx+ox+1,ey+1, YLW_EYE)
    if 'flames' in feats: add_flames(d, cx, S//2-int(6*s), count=2)


def draw_orb_floating(d, P, L, D, H, feats, size=1.1):
    cx = S//2; s = size
    # Main orb body
    r = int(11*s)
    cy_ = S//2 + 2
    ell(d, cx-r,cy_-r,cx+r,cy_+r, P, D)
    ell(d, cx-r+2,cy_-r+2,cx+r-2,cy_+r-2, L)

    # Central eye
    ell(d, cx-int(4*s),cy_-int(4*s),cx+int(4*s),cy_+int(4*s), WHT, D)
    ell(d, cx-int(2*s),cy_-int(2*s),cx+int(2*s),cy_+int(2*s), dk(P,0.3))
    shine(d, cx-1, cy_-1)

    # Eye stalks — 5 around the orb
    stalk_c = dk(P,0.7)
    for i, (ang, sl) in enumerate([(math.pi*0.15,8),(math.pi*0.45,9),(math.pi*0.75,7),
                                     (math.pi*1.05,8),(math.pi*1.35,7)]):
        sx = cx + int((r+1)*math.cos(ang))
        sy = cy_ + int((r+1)*0.9*math.sin(ang))
        ex2 = sx + int(sl*math.cos(ang))
        ey2 = sy + int(sl*0.9*math.sin(ang))
        d.line([(sx,sy),(ex2,ey2)], fill=stalk_c, width=2)
        ell(d, ex2-2,ey2-2,ex2+2,ey2+2, WHT, D)
        ell(d, ex2-1,ey2-1,ex2+1,ey2+1, RED_EYE)


def draw_serpent_snake(d, P, L, D, H, feats, size=1.0):
    cx = S//2; s = size
    # S-curve body — series of overlapping circles
    pts = [(cx+int(8*s),4),(cx+int(6*s),8),(cx+int(2*s),12),(cx-int(3*s),16),
           (cx-int(6*s),20),(cx-int(4*s),24),(cx+int(2*s),27),(cx+int(5*s),30)]
    radii = [int(r*s) for r in [4,4,4,4,4,3,3,2]]
    for (px,py),r in zip(pts,radii):
        ell(d, px-r,py-r,px+r,py+r, P, D)
    # Brighter belly stripe
    for (px,py),r in zip(pts,radii):
        d.ellipse([px-max(1,r-2),py-max(1,r-2),px+max(1,r-2),py+max(1,r-2)], fill=L)
    # Triangular head
    hx,hy = pts[0]
    poly(d, [(hx-int(5*s),hy+3),(hx+int(5*s),hy+3),(hx,hy-int(5*s))], L, D)
    eyes(d, hx, hy-1, P, D, col=YLW_EYE, sep=2)
    # Forked tongue
    d.line([(hx,hy-int(5*s)-1),(hx,hy-int(5*s)-4)], fill=RED_EYE, width=1)
    d.line([(hx,hy-int(5*s)-4),(hx-2,hy-int(5*s)-6)], fill=RED_EYE, width=1)
    d.line([(hx,hy-int(5*s)-4),(hx+2,hy-int(5*s)-6)], fill=RED_EYE, width=1)
    if 'crown' in feats: add_crown(d, hx, hy-int(5*s)-1)


def draw_serpent_worm(d, P, L, D, H, feats, size=1.05):
    """Crawler / worm — thick body, circular mouth."""
    cx = S//2; s = size
    pts = [(cx,6),(cx-int(4*s),11),(cx-int(7*s),17),
           (cx-int(4*s),22),(cx+int(2*s),26),(cx+int(5*s),29)]
    radii = [int(r*s) for r in [5,5,5,4,4,3]]
    for (px,py),r in zip(pts,radii):
        ell(d, px-r,py-r,px+r,py+r, P, D)
    for (px,py),r in zip(pts,radii):
        d.ellipse([px-max(1,r-2),py-max(1,r-2),px+max(1,r-2),py+max(1,r-2)], fill=L)
    # Circular mouth
    hx,hy = pts[0]; hr = int(5*s)
    ell(d, hx-hr,hy-hr,hx+hr,hy+hr, D, D)
    ell(d, hx-hr+2,hy-hr+2,hx+hr-2,hy+hr-2, RED_EYE)
    # Mandibles
    d.line([(hx-hr-1,hy),(hx-hr-4,hy-3)], fill=BONE, width=2)
    d.line([(hx+hr+1,hy),(hx+hr+4,hy-3)], fill=BONE, width=2)
    if 'tentacles' in feats:
        for ox in range(-6,8,3):
            d.line([(hx+ox,hy-hr),(hx+ox+ox//3,hy-hr-5)], fill=dk(P,0.7), width=1)


def draw_insect_spider(d, P, L, D, H, feats, size=1.0):
    cx = S//2; s = size
    # Abdomen — large back oval
    ax=cx-int(2*s); ay=S//2+int(2*s)
    ar_w=int(9*s); ar_h=int(8*s)
    ell(d, ax-ar_w,ay-ar_h,ax+ar_w,ay+ar_h, P, D)
    # Pattern on abdomen
    ell(d, ax-int(4*s),ay-int(3*s),ax+int(4*s),ay+int(3*s), L)

    # Cephalothorax
    ct_x=cx+int(4*s); ct_y=S//2-int(3*s)
    ct_r=int(6*s)
    ell(d, ct_x-ct_r,ct_y-ct_r,ct_x+ct_r,ct_y+ct_r, dk(P,0.8), D)

    # 8 legs — 4 each side
    for i,(ang,bl) in enumerate([(0.3,10),(0.55,11),(0.8,10),(1.05,9)]):
        # Left legs
        lx = ct_x - int(ct_r*math.cos(math.pi-ang))
        ly = ct_y + int(ct_r*0.7*math.sin(math.pi-ang))
        d.line([(int(lx),int(ly)),(int(lx-bl*1.2),int(ly+bl*0.6))],
               fill=dk(P,0.75), width=max(1,int(1.5*s)))
        # Right legs
        rx = ct_x + int(ct_r*math.cos(ang))
        ry = ct_y + int(ct_r*0.7*math.sin(ang))
        d.line([(int(rx),int(ry)),(int(rx+bl*1.2),int(ry+bl*0.6))],
               fill=dk(P,0.75), width=max(1,int(1.5*s)))

    # Eyes — 4 dots
    for ox in (-3,-1,1,3):
        ell(d, ct_x+ox-1,ct_y-2,ct_x+ox+1,ct_y, WHT)
        d.point((ct_x+ox,ct_y-1), fill=BLK)

    if 'web' in feats:
        # Web strand from abdomen corner
        d.line([(ax+ar_w, ay-ar_h),(S-1,0)], fill=(*WHT[:3],120), width=1)


def draw_rat_rodent(d, P, L, D, H, feats, size=0.85):
    cx = S//2; s = size
    # Body oval
    bw=int(12*s); bh=int(8*s); by=S-3-bh
    ell(d, cx-bw,by,cx+bw,by+bh*2, P, D)
    # Belly
    ell(d, cx-int(6*s),by+int(3*s),cx+int(6*s),by+bh*2-1, lt(P,1.3))

    # Head
    hcx=cx+int(8*s); hcy=by-int(1*s); hr=int(5*s)
    ell(d, hcx-hr,hcy-hr,hcx+hr,hcy+hr, P, D)
    # Ears
    ell(d, hcx-int(2*s),hcy-hr-int(3*s),hcx+int(1*s),hcy-hr+int(1*s), lt(P,1.4), D)
    ell(d, hcx+int(1*s),hcy-hr-int(3*s),hcx+int(4*s),hcy-hr+int(1*s), lt(P,1.4), D)
    eyes(d, hcx+int(1*s), hcy-int(1*s), P, D, col=RED_EYE, sep=2, r=1)
    # Snout
    d.ellipse([hcx+hr-2,hcy-1,hcx+hr+2,hcy+2], fill=dk(P,0.7))

    # Legs — 4 small stubs
    lh=int(4*s)
    for lx in [cx-int(5*s), cx-int(1*s), cx+int(3*s), cx+int(7*s)]:
        d.line([(int(lx), by+bh*2-int(1*s)),(int(lx)+1, by+bh*2+lh)], fill=dk(P,0.75), width=2)

    # Tail — curved line
    pts=[(cx-int(11*s),by+bh),(cx-int(14*s),by+bh+3),(cx-int(15*s),by+bh+7)]
    line(d, pts, dk(P,0.6), 1)


def draw_amphibian_frog(d, P, L, D, H, feats, size=0.9):
    cx = S//2; s = size
    # Wide flat body
    bw=int(12*s); bh=int(7*s); by=S-3-bh
    ell(d, cx-bw,by,cx+bw,by+bh*2, P, D)
    # Belly stripe
    ell(d, cx-int(7*s),by+int(3*s),cx+int(7*s),by+bh*2, lt(P,1.5))

    # Head — merges with body, eyes on top
    hr=int(5*s); hcy=by-hr+int(2*s)
    ell(d, cx-hr,hcy-hr,cx+hr,hcy+hr, P, D)
    # Bulgy eyes on top
    for ox in (-int(5*s),int(5*s)):
        ell(d, cx+ox-int(3*s),hcy-hr-int(2*s),cx+ox+int(3*s),hcy-hr+int(3*s), lt(P,1.5),D)
        ell(d, cx+ox-int(1*s),hcy-hr,cx+ox+int(1*s),hcy-hr+int(2*s), BLK)

    # Back legs — wide splayed
    d.line([(cx-int(10*s),by+bh),(cx-int(14*s),by+bh*2+int(4*s))], fill=dk(P,0.8), width=3)
    d.line([(cx+int(10*s),by+bh),(cx+int(14*s),by+bh*2+int(4*s))], fill=dk(P,0.8), width=3)
    # Webbed toes (3 lines)
    for tx in (-2,0,2):
        d.line([(cx-int(14*s)+tx,by+bh*2+int(4*s)),
                (cx-int(14*s)+tx-2,by+bh*2+int(6*s))], fill=dk(P,0.75), width=1)
        d.line([(cx+int(14*s)+tx,by+bh*2+int(4*s)),
                (cx+int(14*s)+tx+2,by+bh*2+int(6*s))], fill=dk(P,0.75), width=1)

    # Front legs
    d.line([(cx-int(8*s),by+bh+int(2*s)),(cx-int(12*s),by+bh+int(6*s))], fill=dk(P,0.8),width=2)
    d.line([(cx+int(8*s),by+bh+int(2*s)),(cx+int(12*s),by+bh+int(6*s))], fill=dk(P,0.8),width=2)


def draw_plant_creature(d, P, L, D, H, feats, size=1.0):
    cx = S//2; s = size
    # Root/vine base
    for rx,ry in [(-4,S-3),(-1,S-3),(2,S-3),(5,S-3)]:
        d.line([(cx+rx,S//2+int(5*s)),(cx+rx*2,S-3)], fill=dk(P,0.7), width=2)
    # Main stalk
    d.line([(cx,S//2+int(5*s)),(cx-int(1*s),S//2-int(3*s))], fill=dk(P,0.7), width=3)
    # Bulbous head / flower
    hr=int(8*s); hcy=S//2-int(3*s)
    ell(d, cx-hr,hcy-hr,cx+hr,hcy+hr, P, D)
    # Petals
    for ang in [0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]:
        px = cx + int((hr+3)*math.cos(ang)); py = hcy + int((hr+3)*0.9*math.sin(ang))
        ell(d, px-3,py-3,px+3,py+3, L, D)
    # Central face
    ell(d, cx-int(4*s),hcy-int(4*s),cx+int(4*s),hcy+int(4*s), L)
    eyes(d, cx, hcy, P, D, col=BLK, sep=2)
    # Thorns on stalk
    for ty in range(S//2-int(1*s), S//2+int(4*s), int(3*s)):
        d.line([(cx,int(ty)),(cx-4,int(ty)-2)], fill=D, width=1)
        d.line([(cx,int(ty)),(cx+3,int(ty)-3)], fill=D, width=1)


def draw_avian_bird(d, P, L, D, H, feats, size=1.0):
    cx = S//2; s = size
    # Body oval
    bw=int(9*s); bh=int(8*s); by=S//2-int(1*s)
    ell(d, cx-bw,by-bh,cx+bw,by+bh, P, D)

    # Wings spread wide
    wc=dk(P,0.65)
    poly(d, [(cx-bw,by-int(2*s)),(cx-bw-int(10*s),by-int(7*s)),(cx-bw+int(2*s),by+int(3*s))], wc,D)
    poly(d, [(cx+bw,by-int(2*s)),(cx+bw+int(10*s),by-int(7*s)),(cx+bw-int(2*s),by+int(3*s))], wc,D)
    # Wing feather lines
    d.line([(cx-bw,by-int(2*s)),(cx-bw-int(10*s),by-int(7*s))], fill=D, width=1)
    d.line([(cx+bw,by-int(2*s)),(cx+bw+int(10*s),by-int(7*s))], fill=D, width=1)

    # Head
    hr=int(5*s); hcx=cx; hcy=by-bh-hr+int(1*s)
    ell(d, hcx-hr,hcy-hr,hcx+hr,hcy+hr, L, D)
    eyes(d, hcx, hcy, P, D, col=YLW_EYE, sep=2)
    # Beak
    poly(d, [(hcx-int(2*s),hcy+int(1*s)),(hcx+int(2*s),hcy+int(1*s)),
              (hcx,hcy+int(5*s))], GOLD, D)

    # Tail feathers
    for tx in [-3,-1,1,3]:
        d.line([(cx+tx,by+bh),(cx+tx*2,by+bh+int(5*s))], fill=dk(P,0.7), width=2)

    # Talons
    d.line([(cx-int(3*s),by+bh-2),(cx-int(5*s),by+bh+3)], fill=BLK, width=2)
    d.line([(cx+int(3*s),by+bh-2),(cx+int(5*s),by+bh+3)], fill=BLK, width=2)

    if 'crown' in feats: add_crown(d, hcx, hcy-hr)
    if 'flames' in feats: add_flames(d, cx, by-bh, count=2)


def draw_winged_quadruped(d, P, L, D, H, feats, size=1.1):
    """Griffin / pegasus — quadruped with wings."""
    cx = S//2; s = size
    # Body
    bw=int(11*s); bh=int(8*s); by=S//2+int(4*s)
    ell(d, cx-bw,by-bh,cx+bw,by+bh, P, D)

    # Neck and head (lion / eagle hybrid)
    hr=int(5*s); hcx=cx+int(7*s); hcy=by-bh-hr
    poly(d, [(cx+int(3*s),by-bh+2),(cx+int(8*s),by-bh+2),
              (cx+int(9*s),hcy+hr),(cx+int(5*s),hcy+hr)], L, D)
    ell(d, hcx-hr,hcy-hr,hcx+hr,hcy+hr, L, D)
    eyes(d, hcx, hcy, P, D, col=YLW_EYE, sep=2)
    # Beak or mane
    poly(d, [(hcx-int(2*s),hcy+2),(hcx+int(4*s),hcy-1),(hcx+int(2*s),hcy+int(4*s))], GOLD,D)

    # Large wings
    wc=dk(P,0.6)
    poly(d, [(cx-int(2*s),by-bh+2),(cx-int(12*s),by-int(8*s)),(cx+int(2*s),by-int(1*s))], wc,D)
    poly(d, [(cx+int(3*s),by-bh+2),(cx+int(11*s),by-int(9*s)),(cx+int(8*s),by-int(2*s))], wc,D)

    # 4 legs
    for lx in [cx-int(7*s),cx-int(2*s),cx+int(3*s),cx+int(7*s)]:
        d.line([(int(lx),by+bh-2),(int(lx),by+bh+int(5*s))], fill=dk(P,0.75), width=3)
        d.line([(int(lx),by+bh+int(5*s)),(int(lx)-2,by+bh+int(7*s))], fill=BLK, width=2)

    # Tail
    pts=[(cx-bw,by),(cx-bw-4,by+4),(cx-bw-5,by+8)]
    line(d, pts, dk(P,0.7), 2)


def draw_bat(d, P, L, D, H, feats, size=0.9):
    cx = S//2; s = size
    # Massive wings dominate
    wc = dk(P, 0.6)
    poly(d, [(cx-2,S//2),(cx-int(14*s),S//2-int(6*s)),(cx-int(12*s),S//2+int(6*s))], wc,D)
    poly(d, [(cx+2,S//2),(cx+int(14*s),S//2-int(6*s)),(cx+int(12*s),S//2+int(6*s))], wc,D)
    # Wing veins
    d.line([(cx,S//2),(cx-int(14*s),S//2-int(6*s))], fill=D, width=1)
    d.line([(cx,S//2),(cx-int(10*s),S//2+int(7*s))], fill=D, width=1)
    d.line([(cx,S//2),(cx+int(14*s),S//2-int(6*s))], fill=D, width=1)
    d.line([(cx,S//2),(cx+int(10*s),S//2+int(7*s))], fill=D, width=1)

    # Small body
    br = int(4*s)
    ell(d, cx-br,S//2-br,cx+br,S//2+br, P, D)
    # Head
    hr=int(3*s); hcy=S//2-br-hr+1
    ell(d, cx-hr,hcy-hr,cx+hr,hcy+hr, L, D)
    # Ears
    poly(d, [(cx-hr,hcy-hr),(cx-hr-int(3*s),hcy-hr-int(4*s)),(cx-1,hcy-hr+1)], P, D)
    poly(d, [(cx+hr,hcy-hr),(cx+hr+int(3*s),hcy-hr-int(4*s)),(cx+1,hcy-hr+1)], P, D)
    eyes(d, cx, hcy, P, D, col=RED_EYE, sep=2, r=1)


def draw_elemental_fire(d, P, L, D, H, feats, size=1.1):
    cx = S//2
    # Build flame from bottom up — multiple overlapping flame shapes
    base_y = S - 3
    layers = [
        (cx, base_y, int(10), int(22), P),
        (cx-int(3), base_y, int(7), int(15), lt(P,1.3)),
        (cx+int(4), base_y, int(6), int(12), lt(P,1.5)),
        (cx, base_y-int(5), int(5), int(10), FIRE_Y),
    ]
    for (fx,fy,fw,fh,fc) in layers:
        # Flame polygon — wide at base, tapers to point
        pts=[(fx-fw,fy),(fx-fw//2,fy-fh*2//3),(fx,fy-fh),
              (fx+fw//2,fy-fh*2//3),(fx+fw,fy)]
        poly(d, pts, fc, dk(fc,0.5))

    # Eyes embedded in flames
    eyes(d, cx, base_y-int(16), P, D, col=WHT, sep=3)
    add_flames(d, cx, base_y-int(20), count=3)


def draw_elemental_ice(d, P, L, D, H, feats, size=1.0):
    cx = S//2; cy = S//2
    # Crystalline hexagon base
    r = int(12)
    pts=[(int(cx+r*math.cos(math.pi/6+i*math.pi/3)),
           int(cy+r*math.sin(math.pi/6+i*math.pi/3))) for i in range(6)]
    poly(d, pts, ICE_B, dk(ICE_B,0.5))

    # Inner diamond
    r2 = int(7)
    pts2=[(int(cx+r2*math.cos(i*math.pi/2)),
            int(cy+r2*math.sin(i*math.pi/2))) for i in range(4)]
    poly(d, pts2, lt(ICE_B,1.4), dk(ICE_B,0.6))

    # Facet lines from center
    for ang in [0, math.pi/3, 2*math.pi/3]:
        d.line([(cx,cy),(int(cx+r*math.cos(ang)),int(cy+r*math.sin(ang)))], fill=WHT, width=1)
        d.line([(cx,cy),(int(cx+r*math.cos(ang+math.pi)),int(cy+r*math.sin(ang+math.pi)))],fill=WHT,width=1)

    # Spike tips
    for ang in [math.pi/6+i*math.pi/3 for i in range(6)]:
        tx=int(cx+(r+4)*math.cos(ang)); ty=int(cy+(r+4)*math.sin(ang))
        poly(d, [(tx-1,ty-1),(tx+1,ty-1),(tx,ty+3)], WHT)

    eyes(d, cx, cy, P, D, col=_c(40,200,255), sep=3)


def draw_elemental_earth(d, P, L, D, H, feats, size=1.15):
    """Rocky humanoid shape."""
    cx = S//2; s = size
    # Chunky body made of overlapping rectangles
    rock_c = P; rock_l = lt(P,1.2); rock_d = dk(P,0.6)

    # Main torso — irregular rectangles
    for (x0,y0,x1,y1) in [
        (cx-int(8*s),S//2-int(6*s),cx+int(8*s),S//2+int(6*s)),
        (cx-int(6*s),S//2-int(10*s),cx+int(6*s),S//2-int(4*s)),
    ]:
        rect(d, int(x0),int(y0),int(x1),int(y1), rock_c, rock_d)

    # Rock texture — random chip marks
    for (rx,ry) in [(cx-5,S//2-3),(cx+3,S//2+1),(cx-2,S//2+4),(cx+5,S//2-7)]:
        d.polygon([(rx,ry),(rx+3,ry-2),(rx+2,ry+2)], fill=rock_d)

    # Head — boulder
    hr=int(6*s); hcy=S//2-int(11*s)
    poly(d, [(cx-hr,hcy),(cx-hr+2,hcy-hr),(cx+hr-2,hcy-hr),(cx+hr,hcy),(cx,hcy+int(2*s))], rock_l,rock_d)

    eyes(d, cx, hcy-2, P, D, col=_c(255,200,50), sep=3)

    # Arms — rock slabs
    d.line([(cx-int(8*s),S//2-int(6*s)),(cx-int(12*s),S//2+int(2*s))], fill=rock_c, width=6)
    d.line([(cx+int(8*s),S//2-int(6*s)),(cx+int(12*s),S//2+int(2*s))], fill=rock_c, width=6)

    # Legs
    d.line([(cx-int(4*s),S//2+int(6*s)),(cx-int(4*s),S-3)], fill=rock_c, width=6)
    d.line([(cx+int(4*s),S//2+int(6*s)),(cx+int(4*s),S-3)], fill=rock_c, width=6)


def draw_elemental_storm(d, P, L, D, H, feats, size=1.0):
    cx = S//2; cy = S//2 - 1
    # Swirling vortex — concentric arc rings
    for r,col,w in [(13,dk(P,0.5),3),(10,P,2),(7,L,2),(4,lt(P,1.6),2)]:
        d.arc([cx-r,cy-r,cx+r,cy+r], start=30, end=300, fill=col, width=w)
    # Lightning bolt centre
    bolt=[(cx+1,cy-9),(cx-1,cy-3),(cx+3,cy-3),(cx-2,cy+9),(cx+1,cy+2),(cx-1,cy+2)]
    poly(d, bolt, FIRE_Y, dk(FIRE_Y,0.5))
    # Rotating sparks
    for ang in [0.4, 1.2, 2.1, 3.0, 4.0, 5.0]:
        sx=cx+int(11*math.cos(ang)); sy=cy+int(11*math.sin(ang))
        d.ellipse([sx-1,sy-1,sx+1,sy+1], fill=WHT)
    eyes(d, cx, cy+1, P, D, col=WHT, sep=3)


def draw_demon_winged(d, P, L, D, H, feats, size=1.1):
    feats = set(feats) | {'wings', 'horns', 'tail'}
    draw_humanoid(d, P, L, D, H, feats, size=size, head_r_base=5)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

DRAW_FN = {
    'humanoid_medium':   draw_humanoid,
    'humanoid_small':    draw_humanoid_small,
    'humanoid_large':    draw_humanoid_large,
    'humanoid_caster':   draw_humanoid_caster,
    'lich_caster':       draw_lich_caster,
    'undead_skeleton':   draw_undead_skeleton,
    'undead_ghost':      draw_undead_ghost,
    'undead_zombie':     draw_undead_zombie,
    'vampire_noble':     draw_vampire_noble,
    'werewolf':          draw_werewolf,
    'troll':             draw_troll,
    'construct_golem':   draw_construct_golem,
    'dragon_large':      draw_dragon_large,
    'dragon_small':      draw_dragon_small,
    'blob_ooze':         draw_blob_ooze,
    'orb_floating':      draw_orb_floating,
    'serpent_snake':     draw_serpent_snake,
    'serpent_worm':      draw_serpent_worm,
    'insect_spider':     draw_insect_spider,
    'rat_rodent':        draw_rat_rodent,
    'amphibian_frog':    draw_amphibian_frog,
    'plant_creature':    draw_plant_creature,
    'avian_bird':        draw_avian_bird,
    'winged_quadruped':  draw_winged_quadruped,
    'bat':               draw_bat,
    'elemental_fire':    draw_elemental_fire,
    'elemental_ice':     draw_elemental_ice,
    'elemental_earth':   draw_elemental_earth,
    'elemental_storm':   draw_elemental_storm,
    'demon_winged':      draw_demon_winged,
    'quadruped_medium':  lambda d,P,L,D_,H,f,size=1.0: draw_rat_rodent(d,P,L,D_,H,f,size*1.2),
    'quadruped_large':   lambda d,P,L,D_,H,f,size=1.0: draw_rat_rodent(d,P,L,D_,H,f,size*1.5),
}


# ---------------------------------------------------------------------------
# Highlight pass — brighten top-left edge pixels
# ---------------------------------------------------------------------------
def apply_highlight(img):
    pix = img.load()
    w,h = img.size
    # Sample top-left quadrant pixels and brighten if they're non-transparent edge pixels
    for y in range(max(0,h//5), min(h, h//2)):
        for x in range(max(0,w//5), min(w, w//2)):
            r2,g2,b2,a2 = pix[x,y]
            if a2 > 180:
                nr,ng,nb = pix[x-1,y][3] if x>0 else 0, pix[x,y-1][3] if y>0 else 0, 0
                if nr < 100 or ng < 100:  # edge pixel
                    pix[x,y] = (min(255,r2+40),min(255,g2+40),min(255,b2+40),a2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(BRIEF_IN, encoding='utf-8') as f:
        briefs = json.load(f)

    ok = err = 0
    for mid, brief in briefs.items():
        img  = new_canvas()
        d    = ImageDraw.Draw(img, 'RGBA')

        pal  = brief['palette']
        P    = C(pal['primary'])
        L    = C(pal['secondary'])
        D_   = C(pal['dark'])
        H    = C(pal['highlight'])
        feats= set(brief['features'])
        size = brief['size']
        sil  = brief['silhouette']

        fn = DRAW_FN.get(sil, draw_humanoid)
        try:
            if sil == 'undead_ghost':
                fn(d, P, L, D_, H, feats, size=size, img=img)
            else:
                fn(d, P, L, D_, H, feats, size=size)

            if 'glow' in feats and sil != 'undead_ghost':
                add_glow_aura(img, S//2, S//2, int(14*size), P)

            apply_highlight(img)
        except Exception as e:
            print(f"  WARN {mid}: {e}")
            err += 1

        out = os.path.join(OUT_DIR, f"{mid}.png")
        img.save(out)
        ok += 1

    print(f"Generated {ok} sprites ({err} warnings) -> {OUT_DIR}")


if __name__ == '__main__':
    main()
