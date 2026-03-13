#!/usr/bin/env python3
"""
Generate 32x32 pixel-art sprites for all non-monster items.
Output: assets/tiles/items/{item_id}.png  (RGBA, transparent background)
Usage:  python data/gen_item_sprites.py
"""
import json, math, os, sys
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install Pillow"); sys.exit(1)

ROOT    = os.path.join(os.path.dirname(__file__), '..')
OUT_DIR = os.path.join(ROOT, 'assets', 'tiles', 'items')
S       = 32
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour helpers
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
BONE = _c(220,215,190)
RED  = _c(200,50,50)
PARCHMENT = _c(220,200,160)

def new_canvas():
    return Image.new('RGBA', (S,S), TRANSPARENT)

def ell(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline:
        d.ellipse([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.ellipse([x0,y0,x1,y1], fill=fill)

def rect(d, x0,y0,x1,y1, fill, outline=None, ow=1):
    if outline:
        d.rectangle([x0-ow,y0-ow,x1+ow,y1+ow], fill=outline)
    d.rectangle([x0,y0,x1,y1], fill=fill)

def poly(d, pts, fill, outline=None):
    if outline and len(pts) >= 3:
        d.polygon(pts, fill=outline)
    d.polygon(pts, fill=fill)

def shine(d, x, y, c=WHT):
    d.point((int(x),int(y)), fill=c)

# ---------------------------------------------------------------------------
# Highlight pass (top-left edge brightening)
# ---------------------------------------------------------------------------
def apply_highlight(img):
    pix = img.load()
    w,h = img.size
    for y in range(max(0,h//5), min(h,h//2)):
        for x in range(max(0,w//5), min(w,w//2)):
            r2,g2,b2,a2 = pix[x,y]
            if a2 > 180:
                nb_a = pix[x-1,y][3] if x>0 else 0
                nb_b = pix[x,y-1][3] if y>0 else 0
                if nb_a < 100 or nb_b < 100:
                    pix[x,y] = (min(255,r2+35),min(255,g2+35),min(255,b2+35),a2)

# ---------------------------------------------------------------------------
# WEAPON drawing functions
# ---------------------------------------------------------------------------

def draw_sword(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Crossguard
    rect(d, 7,22,25,24, D, BLK)
    # Blade — tapered
    poly(d, [(15,4),(17,4),(24,22),(8,22)], L, D)
    poly(d, [(15,4),(16,4),(20,22),(15,22)], lt(L,1.15))  # shine streak
    # Grip
    rect(d, 14,24,18,30, dk(P,0.7), BLK)
    # Pommel
    ell(d, 13,29,19,32, P, BLK)
    shine(d,15,7)
    apply_highlight(img); return img

def draw_longsword(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 6,21,26,23, D, BLK)
    poly(d, [(15,2),(17,2),(25,21),(7,21)], L, D)
    poly(d, [(15,2),(16,2),(20,21),(15,21)], lt(L,1.15))
    rect(d, 14,23,18,30, dk(P,0.7), BLK)
    ell(d, 12,29,20,33, P, BLK)
    shine(d,15,5)
    apply_highlight(img); return img

def draw_dagger(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 9,20,23,22, D, BLK)
    poly(d, [(14,7),(18,7),(22,20),(10,20)], L, D)
    poly(d, [(15,7),(16,7),(19,20),(15,20)], lt(L,1.15))
    rect(d, 14,22,18,28, dk(P,0.7), BLK)
    ell(d, 12,27,20,31, P, BLK)
    shine(d,15,10)
    apply_highlight(img); return img

def draw_rapier(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Very thin blade
    d.line([(16,2),(16,22)], fill=L, width=2)
    d.line([(16,2),(16,22)], fill=lt(L,1.3), width=1)
    # Guard — wide
    rect(d, 4,20,28,23, D, BLK)
    ell(d, 12,20,20,26, P, BLK)  # knuckle bow
    rect(d, 14,23,18,30, dk(P,0.7), BLK)
    ell(d, 13,29,19,32, P, BLK)
    shine(d,16,4)
    apply_highlight(img); return img

def draw_scimitar(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Curved blade
    poly(d, [(16,4),(22,6),(28,14),(26,20),(20,22),(14,22),(8,22),(14,22)], L, D)
    poly(d, [(16,4),(22,6),(26,12),(24,18),(20,22)], lt(L,1.2))
    # Edge curve
    d.arc([8,8,28,28], start=45, end=180, fill=WHT, width=1)
    rect(d, 7,21,17,23, D, BLK)
    rect(d, 10,23,14,30, dk(P,0.7), BLK)
    ell(d, 8,29,16,33, P, BLK)
    shine(d,18,8)
    apply_highlight(img); return img

def draw_axe(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Handle
    rect(d, 14,8,18,31, dk(P,0.7), BLK)
    # Axe head
    poly(d, [(14,8),(6,10),(4,18),(14,20)], L, D)
    poly(d, [(14,8),(6,11),(5,16),(14,18)], lt(L,1.2))
    # Back spike
    poly(d, [(18,10),(24,12),(18,16)], P, D)
    shine(d,8,13)
    apply_highlight(img); return img

def draw_greataxe(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,12,18,31, dk(P,0.65), BLK)
    # Large double-bit head
    poly(d, [(14,5),(4,8),(2,18),(14,21)], L, D)
    poly(d, [(18,5),(28,8),(30,18),(18,21)], L, D)
    poly(d, [(14,6),(6,9),(5,16),(14,19)], lt(L,1.2))
    poly(d, [(18,6),(26,9),(27,16),(18,19)], lt(L,1.2))
    # Top spike
    poly(d, [(14,5),(16,2),(18,5)], L, D)
    shine(d,8,12); shine(d,24,12)
    apply_highlight(img); return img

def draw_mace(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,16,18,30, dk(P,0.7), BLK)
    ell(d, 9,6,23,18, P, D)
    # Flanges
    for ang in [0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]:
        fx = 16+int(9*math.cos(ang)); fy = 12+int(7*math.sin(ang))
        poly(d, [(16,12),(int(16+6*math.cos(ang)),int(12+5*math.sin(ang))),(fx,fy)], L, D)
    ell(d, 11,8,21,17, L)
    shine(d,14,10)
    apply_highlight(img); return img

def draw_warhammer(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,16,18,31, dk(P,0.7), BLK)
    rect(d, 6,5,26,17, P, D)
    rect(d, 8,7,24,15, L)
    # Vertical hammer face
    rect(d, 6,6,10,16, L, D)
    shine(d,9,9)
    apply_highlight(img); return img

def draw_staff(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    d.line([(16,28),(15,3)], fill=dk(P,0.7), width=3)
    d.line([(16,28),(16,3)], fill=P, width=2)
    d.line([(16,28),(17,3)], fill=lt(P,1.3), width=1)
    # Orb at top
    ell(d, 11,2,21,11, lt(P,1.4), D)
    ell(d, 13,3,19,9, lt(P,1.7))
    shine(d,14,4)
    apply_highlight(img); return img

def draw_bow(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # D-curve bow
    d.arc([4,2,20,30], start=270, end=90, fill=P, width=3)
    d.arc([5,3,19,29], start=270, end=90, fill=lt(P,1.3), width=1)
    # Bowstring
    d.line([(12,3),(12,29)], fill=PARCHMENT, width=1)
    # Grip wrapping
    for y in range(13,19,2):
        d.line([(5,y),(13,y)], fill=dk(P,0.6), width=1)
    shine(d,6,10)
    apply_highlight(img); return img

def draw_longbow(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    d.arc([3,1,19,31], start=270, end=90, fill=P, width=3)
    d.arc([4,2,18,30], start=270, end=90, fill=lt(P,1.3), width=1)
    d.line([(11,2),(11,30)], fill=PARCHMENT, width=1)
    for y in range(13,19,2):
        d.line([(4,y),(12,y)], fill=dk(P,0.6), width=1)
    shine(d,5,8)
    apply_highlight(img); return img

def draw_crossbow(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Stock
    rect(d, 4,14,24,18, dk(P,0.7), BLK)
    rect(d, 4,14,24,17, P, BLK)
    # Bow arms
    d.line([(14,14),(8,6)], fill=L, width=2)
    d.line([(14,14),(20,6)], fill=L, width=2)
    # Bowstring
    d.line([(8,6),(20,6)], fill=PARCHMENT, width=1)
    # Trigger guard
    rect(d, 14,17,18,24, dk(P,0.6), BLK)
    shine(d,6,15)
    apply_highlight(img); return img

def draw_spear(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Shaft
    d.line([(16,28),(15,4)], fill=dk(P,0.65), width=3)
    d.line([(16,28),(16,4)], fill=P, width=2)
    # Spearhead
    poly(d, [(13,4),(19,4),(17,1),(15,1)], L, D)
    poly(d, [(15,4),(17,4),(16,2)], lt(L,1.3))
    shine(d,16,3)
    apply_highlight(img); return img

def draw_halberd(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    d.line([(16,30),(15,5)], fill=dk(P,0.65), width=3)
    # Axe blade
    poly(d, [(14,8),(5,11),(4,18),(14,20)], L, D)
    # Spear tip
    poly(d, [(13,5),(19,5),(17,2),(15,2)], L, D)
    # Back hook
    poly(d, [(18,10),(24,8),(18,14)], P, D)
    shine(d,8,14); shine(d,16,4)
    apply_highlight(img); return img

def draw_club(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,20,18,31, dk(P,0.7), BLK)
    ell(d, 8,8,24,22, P, D)
    ell(d, 10,10,22,20, L)
    shine(d,13,12)
    apply_highlight(img); return img

def draw_flail(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,19,18,30, dk(P,0.7), BLK)
    # Chain links
    for y in [13,10,7]:
        ell(d, 14,y,18,y+4, D, BLK)
    ell(d, 11,3,21,12, P, D)
    for ang in [0,math.pi/2,math.pi,3*math.pi/2]:
        sx=16+int(5*math.cos(ang)); sy=7+int(4*math.sin(ang))
        poly(d, [(16,7),(sx-1,sy),(sx+1,sy)], L, D)
    shine(d,14,6)
    apply_highlight(img); return img

def draw_morningstar(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 14,17,18,30, dk(P,0.7), BLK)
    ell(d, 9,6,23,18, P, D)
    # Spikes
    for ang in [i*math.pi/4 for i in range(8)]:
        sx=16+int(10*math.cos(ang)); sy=12+int(8*math.sin(ang))
        poly(d, [(16,12),(int(16+5*math.cos(ang)),int(12+4*math.sin(ang))),(sx,sy)], L)
    ell(d, 12,8,20,16, lt(P,1.2))
    shine(d,14,10)
    apply_highlight(img); return img

def draw_glaive(P, L, D):
    """Glaive — curved blade on a long pole."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    d.line([(14,30),(14,6)], fill=dk(P,0.65), width=3)
    # Curved blade
    poly(d, [(12,6),(20,4),(26,8),(22,14),(14,10)], L, D)
    poly(d, [(13,6),(20,5),(24,9),(20,13),(14,10)], lt(L,1.2))
    shine(d,16,7)
    apply_highlight(img); return img

def draw_zweihander(P, L, D):
    """Zweihander — oversized two-handed sword."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 5,19,27,21, D, BLK)
    # Wide blade
    poly(d, [(15,2),(17,2),(26,19),(6,19)], L, D)
    poly(d, [(15,2),(16,3),(22,19),(16,19)], lt(L,1.15))
    # Ricasso
    rect(d, 13,19,19,22, P, D)
    rect(d, 14,22,18,29, dk(P,0.7), BLK)
    ell(d, 12,28,20,32, P, BLK)
    shine(d,15,5)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# SHIELD drawing functions
# ---------------------------------------------------------------------------

def draw_shield(P, L, D, large=False):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    w = 18 if large else 14
    h = 22 if large else 18
    ox = (S-w)//2; oy = (S-h)//2
    # Heater shape
    poly(d, [(ox,oy),(ox+w,oy),(ox+w,oy+h*2//3),(ox+w//2,oy+h),(ox,oy+h*2//3)], P, D)
    poly(d, [(ox+2,oy+2),(ox+w-2,oy+2),(ox+w-2,oy+h*2//3-2),(ox+w//2,oy+h-3),(ox+2,oy+h*2//3-2)], L)
    # Boss stud
    ell(d, ox+w//2-3,oy+h//3-3,ox+w//2+3,oy+h//3+3, GOLD, D)
    shine(d,ox+3,oy+4)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# ARMOR drawing functions
# ---------------------------------------------------------------------------

def draw_helm(P, L, D, full=False):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    cx = 16
    if full:
        # Full great helm — barrel style
        rect(d, 7,7,25,26, P, D)
        rect(d, 8,8,24,25, L)
        # Visor slits
        rect(d, 9,14,23,16, D)
        d.line([(9,15),(23,15)], fill=BLK, width=1)
        # Top ridge
        rect(d, 13,4,19,9, P, D)
    else:
        # Open-faced helm
        poly(d, [(7,20),(7,12),(10,6),(16,4),(22,6),(25,12),(25,20)], P, D)
        poly(d, [(9,20),(9,13),(12,8),(16,6),(20,8),(23,13),(23,20)], L)
        # Cheek guards
        rect(d, 7,16,11,22, dk(P,0.8), D)
        rect(d, 21,16,25,22, dk(P,0.8), D)
        # Nasal bar
        d.line([(16,10),(16,20)], fill=D, width=2)
    shine(d,12,8)
    apply_highlight(img); return img

def draw_coif(P, L, D):
    """Chain/padded coif — rounded head covering."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    ell(d, 7,4,25,26, P, D)
    ell(d, 9,6,23,24, L)
    # Face opening
    ell(d, 11,10,21,22, dk(P,0.2))
    shine(d,12,8)
    apply_highlight(img); return img

def draw_cap(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Soft cap / beret
    ell(d, 6,10,26,24, P, D)
    poly(d, [(4,20),(28,20),(26,24),(6,24)], dk(P,0.8), D)  # brim
    ell(d, 8,12,24,22, L)
    shine(d,12,14)
    apply_highlight(img); return img

def draw_hood(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(8,4),(24,4),(26,14),(22,26),(16,28),(10,26),(6,14)], P, D)
    poly(d, [(10,6),(22,6),(24,14),(20,24),(16,26),(12,24),(8,14)], L)
    # Face shadow
    ell(d, 11,10,21,22, dk(P,0.3))
    shine(d,12,8)
    apply_highlight(img); return img

def draw_body_armor(P, L, D, style='plate'):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    if style == 'robe':
        poly(d, [(10,4),(22,4),(26,28),(6,28)], P, D)
        poly(d, [(12,6),(20,6),(23,26),(9,26)], L)
        d.line([(16,6),(16,26)], fill=dk(P,0.7), width=1)
    elif style == 'chain':
        rect(d, 7,4,25,27, P, D)
        # Chain links pattern
        for row in range(4,27,3):
            for col in range(7+(row%3),25,4):
                ell(d, col,row,col+3,row+2, L)
    else:
        # Plate / scale / brigandine
        rect(d, 7,4,25,27, P, D)
        rect(d, 9,6,23,25, L)
        # Pectoral line
        d.line([(9,14),(23,14)], fill=D, width=1)
        d.line([(16,6),(16,25)], fill=D, width=1)
        # Shoulder plates
        rect(d, 4,4,10,10, P, D)
        rect(d, 22,4,28,10, P, D)
        shine(d,12,8)
    apply_highlight(img); return img

def draw_boots(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Single boot in 3/4 view
    poly(d, [(8,6),(22,6),(22,22),(24,28),(6,28),(8,22)], P, D)
    poly(d, [(10,8),(20,8),(20,21),(22,26),(8,26),(10,21)], L)
    # Sole
    poly(d, [(5,26),(27,26),(27,30),(5,30)], dk(P,0.6), D)
    # Toe
    poly(d, [(22,24),(28,24),(28,30),(22,28)], P, D)
    shine(d,12,10)
    apply_highlight(img); return img

def draw_gloves(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Palm
    rect(d, 9,12,23,26, P, D)
    rect(d, 11,14,21,24, L)
    # Four fingers
    for fx in [10,13,16,19]:
        rect(d, fx,6,fx+3,13, P, D)
        rect(d, fx+1,7,fx+2,12, L)
    # Thumb
    poly(d, [(7,14),(10,12),(10,18),(7,18)], P, D)
    shine(d,12,15)
    apply_highlight(img); return img

def draw_gauntlets(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Armored gauntlet
    rect(d, 9,14,23,28, P, D)
    rect(d, 11,16,21,26, lt(P,1.2))
    # Knuckle plates
    for fx in [10,14,18]:
        rect(d, fx,12,fx+3,16, lt(P,1.3), D)
    # Cuff
    rect(d, 8,24,24,30, dk(P,0.8), D)
    d.line([(8,24),(24,24)], fill=GOLD, width=1)
    shine(d,12,15)
    apply_highlight(img); return img

def draw_bracers(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    ell(d, 8,8,24,24, P, D)
    ell(d, 10,10,22,22, L)
    # Strap lines
    d.line([(8,12),(24,12)], fill=D, width=1)
    d.line([(8,20),(24,20)], fill=D, width=1)
    shine(d,12,12)
    apply_highlight(img); return img

def draw_leggings(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Two legs
    rect(d, 7,4,15,28, P, D)
    rect(d, 17,4,25,28, P, D)
    rect(d, 9,6,13,26, L)
    rect(d, 19,6,23,26, L)
    # Waistband
    rect(d, 6,4,26,8, dk(P,0.8), D)
    shine(d,10,8); shine(d,20,8)
    apply_highlight(img); return img

def draw_cloak(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(8,2),(24,2),(28,28),(4,28)], P, D)
    poly(d, [(10,4),(22,4),(25,26),(7,26)], L)
    # Clasp at top
    ell(d, 13,2,19,7, GOLD, D)
    # Fold lines
    for x in [10,16,22]:
        d.line([(x,7),(x-1,26)], fill=dk(P,0.8), width=1)
    shine(d,12,8)
    apply_highlight(img); return img

def draw_shirt(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # T-shape
    poly(d, [(8,6),(24,6),(26,10),(22,10),(22,27),(10,27),(10,10),(6,10)], P, D)
    poly(d, [(10,8),(22,8),(23,10),(20,10),(20,25),(12,25),(12,10),(9,10)], L)
    # Collar
    poly(d, [(13,6),(19,6),(18,10),(14,10)], lt(P,1.2), D)
    shine(d,13,10)
    apply_highlight(img); return img

def draw_robe(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(10,2),(22,2),(26,28),(6,28)], P, D)
    poly(d, [(12,4),(20,4),(23,26),(9,26)], L)
    # Sleeves
    poly(d, [(4,8),(12,8),(12,16),(4,16)], P, D)
    poly(d, [(20,8),(28,8),(28,16),(20,16)], P, D)
    d.line([(16,4),(16,26)], fill=dk(P,0.7), width=1)
    shine(d,13,8)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# SCROLL drawing function
# ---------------------------------------------------------------------------

def draw_scroll(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Rolled parchment
    rect(d, 7,8,25,26, PARCHMENT, dk(PARCHMENT,0.6))
    # Rolled ends
    ell(d, 5,8,11,26, dk(PARCHMENT,0.7), BLK)
    ell(d, 21,8,27,26, dk(PARCHMENT,0.7), BLK)
    ell(d, 6,9,10,25, PARCHMENT)
    ell(d, 22,9,26,25, PARCHMENT)
    # Glowing rune/text lines in the scroll color
    for y in [12,15,18,21]:
        rect(d, 12,y,24,y+2, (*P[:3],180))
    # Wax seal dot
    ell(d, 14,23,18,27, L, D)
    shine(d,10,12)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# WAND drawing function
# ---------------------------------------------------------------------------

def draw_wand(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Shaft — angled
    wood = _c(120,80,40)
    d.line([(8,28),(22,6)], fill=wood, width=3)
    d.line([(9,28),(23,6)], fill=lt(wood,1.3), width=1)
    # Gem tip
    poly(d, [(20,3),(24,6),(22,9),(18,7)], L, D)
    ell(d, 19,4,23,8, P, D)
    shine(d,20,5)
    # Band at base
    d.line([(9,26),(11,23)], fill=GOLD, width=2)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# RING drawing function
# ---------------------------------------------------------------------------

def draw_ring(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    cx,cy = 16,17
    # Ring band
    ell(d, cx-8,cy-8,cx+8,cy+8, D, BLK, 2)
    ell(d, cx-8,cy-8,cx+8,cy+8, P)
    ell(d, cx-5,cy-5,cx+5,cy+5, TRANSPARENT, BLK, 0)
    ell(d, cx-5,cy-5,cx+5,cy+5, TRANSPARENT)
    # Actually use a donut: draw ring as outlined circle
    d.ellipse([cx-9,cy-9,cx+9,cy+9], outline=D, width=3)
    d.ellipse([cx-9,cy-9,cx+9,cy+9], outline=P, width=2)
    # Gem at top
    poly(d, [(cx-4,cy-9),(cx,cy-14),(cx+4,cy-9)], L, D)
    ell(d, cx-3,cy-12,cx+3,cy-8, P, D)
    shine(d,cx-1,cy-11)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# AMULET drawing function
# ---------------------------------------------------------------------------

def draw_amulet(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Chain
    for x in range(8,25,2):
        cy = 8 + int(4*math.sin((x-8)*math.pi/16))
        d.point((x,cy), fill=dk(P,0.8))
    # Pendant drop
    ell(d, 10,10,22,28, D, BLK)
    ell(d, 11,11,21,27, P)
    ell(d, 12,12,20,26, L)
    # Gem in center
    ell(d, 14,16,18,22, lt(L,1.5), D)
    shine(d,14,14)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# FOOD drawing functions
# ---------------------------------------------------------------------------

def draw_bread(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    tan = _c(200,160,80); dtan = dk(tan,0.7)
    ell(d, 6,10,26,26, dtan, BLK)
    ell(d, 6,8,26,22, tan, dtan)
    # Crust line
    d.arc([7,9,25,21], start=180, end=0, fill=lt(tan,1.3), width=2)
    shine(d,12,11)
    apply_highlight(img); return img

def draw_meat(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    meat = C(P); bone_ = BONE
    ell(d, 5,10,27,24, dk(meat,0.7), BLK)
    ell(d, 6,11,26,23, meat)
    ell(d, 7,12,18,21, lt(meat,1.2))
    # Bone handle
    rect(d, 18,18,24,28, bone_, BLK)
    ell(d, 16,25,22,30, bone_, BLK)
    shine(d,10,14)
    apply_highlight(img); return img

def draw_mushroom(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Stem
    rect(d, 12,18,20,28, _c(200,185,155), BLK)
    # Cap
    ell(d, 5,8,27,22, P, D)
    ell(d, 7,10,25,20, lt(P,1.2))
    # Spots
    for sx,sy in [(11,12),(18,11),(15,14),(9,14)]:
        ell(d, sx-2,sy-2,sx+2,sy+2, WHT)
    shine(d,10,13)
    apply_highlight(img); return img

def draw_apple(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    red = _c(200,40,40); lred = _c(240,80,80)
    ell(d, 7,8,25,28, dk(red,0.7), BLK)
    ell(d, 7,8,25,28, red)
    ell(d, 9,10,21,24, lred)
    # Stem
    rect(d, 15,4,17,10, _c(80,50,20), BLK)
    # Leaf
    poly(d, [(17,6),(22,4),(20,8)], _c(60,140,40), BLK)
    shine(d,11,12)
    apply_highlight(img); return img

def draw_cheese(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    yel = _c(220,190,60); dyel = dk(yel,0.7)
    poly(d, [(4,20),(20,8),(28,14),(28,26),(4,26)], yel, dyel)
    poly(d, [(6,20),(20,10),(26,15),(26,24),(6,24)], lt(yel,1.2))
    # Holes
    for hx,hy in [(12,18),(20,20),(16,14)]:
        ell(d, hx-2,hy-2,hx+2,hy+2, dyel)
    shine(d,10,16)
    apply_highlight(img); return img

def draw_rations(P, L, D):
    """Trail rations / dried food bundle."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    brn = _c(140,95,50); lbrn = lt(brn,1.3)
    poly(d, [(6,12),(26,12),(28,22),(4,22)], brn, BLK)
    rect(d, 7,14,25,20, lbrn)
    # Twine wrapping
    d.line([(16,12),(16,22)], fill=_c(160,130,70), width=2)
    d.line([(6,17),(26,17)], fill=_c(160,130,70), width=1)
    shine(d,10,15)
    apply_highlight(img); return img

def draw_cooked_meat(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    cooked = _c(160,90,40); lcooked = lt(cooked,1.3)
    ell(d, 5,10,27,24, dk(cooked,0.7), BLK)
    ell(d, 6,11,26,23, cooked)
    ell(d, 8,13,18,21, lcooked)
    rect(d, 18,18,24,26, BONE, BLK)
    ell(d, 16,23,22,28, BONE, BLK)
    shine(d,10,14)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# INGREDIENT drawing functions
# ---------------------------------------------------------------------------

def draw_ingr_meat(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    ell(d, 7,10,25,24, dk(P,0.6), BLK)
    ell(d, 8,11,24,23, P)
    ell(d, 10,13,20,21, L)
    shine(d,12,14)
    apply_highlight(img); return img

def draw_ingr_hide(P, L, D):
    """Hide / skin — irregular flat shape."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(6,6),(18,4),(26,8),(28,20),(22,28),(10,28),(4,20),(4,12)], P, D)
    poly(d, [(8,8),(18,6),(24,10),(25,20),(20,26),(12,26),(6,20),(6,14)], L)
    shine(d,12,10)
    apply_highlight(img); return img

def draw_ingr_scale(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Single large scale tile
    poly(d, [(16,4),(24,10),(26,20),(16,28),(6,20),(6,10)], P, D)
    poly(d, [(16,6),(23,11),(24,20),(16,26),(8,20),(8,11)], L)
    # Vein lines
    for ang in [math.pi/6, math.pi/2, 5*math.pi/6]:
        ex=16+int(9*math.cos(ang)); ey=16+int(9*math.sin(ang))
        d.line([(16,16),(ex,ey)], fill=D, width=1)
    shine(d,14,10)
    apply_highlight(img); return img

def draw_ingr_fang(P, L, D):
    """Fang, claw, horn, tooth, spine — pointed white shape."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    bone_ = BONE; dbone = dk(BONE,0.65)
    poly(d, [(13,28),(19,28),(18,4),(16,2),(14,4)], bone_, dbone)
    poly(d, [(15,28),(17,28),(16,4),(16,2)], lt(BONE,1.2))
    # Blood stain at base
    ell(d, 11,26,21,31, (*P[:3],180))
    shine(d,15,6)
    apply_highlight(img); return img

def draw_ingr_eye(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    ell(d, 5,8,27,24, WHT, BLK)
    ell(d, 8,10,24,22, L)
    ell(d, 11,12,21,20, P)
    ell(d, 13,14,19,18, BLK)
    shine(d,12,13)
    apply_highlight(img); return img

def draw_ingr_dust(P, L, D):
    """Dust, powder, ash, spores — pile shape."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Pile
    ell(d, 5,16,27,28, dk(P,0.5), BLK)
    ell(d, 6,17,26,27, P)
    # Floating particles
    for dx,dy in [(6,12),(12,10),(18,9),(22,12),(10,14),(20,14)]:
        ell(d, dx,dy,dx+2,dy+2, L)
    apply_highlight(img); return img

def draw_ingr_feather(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Quill shaft
    d.line([(16,30),(20,4)], fill=dk(P,0.7), width=2)
    # Barbs
    for t in range(0,26,2):
        bx = 16+int(t*0.15); by = 30-t
        wid = min(8, t//2)
        d.line([(bx,by),(bx+wid,by-3)], fill=P, width=1)
        d.line([(bx,by),(bx-wid//2,by-2)], fill=L, width=1)
    shine(d,18,8)
    apply_highlight(img); return img

def draw_ingr_gem(P, L, D):
    """Crystal shard, gem, stone — faceted jewel."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(16,4),(22,10),(24,20),(16,28),(8,20),(10,10)], P, D)
    poly(d, [(16,4),(22,10),(16,20)], lt(P,1.4))
    poly(d, [(16,20),(8,20),(10,10),(16,4)], mx(P,WHT,0.3))
    shine(d,14,8)
    apply_highlight(img); return img

def draw_ingr_blob(P, L, D):
    """Slime, extract, fluid blob."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    r = 10
    pts = []
    for i in range(10):
        ang = 2*math.pi*i/10
        jit = 1+0.25*math.sin(i*2.1+0.5)
        pts.append((16+r*jit*math.cos(ang), 16+r*0.8*jit*math.sin(ang)))
    poly(d, pts, P, D)
    inner = [(16+(x-16)*0.6, 16+(y-16)*0.6) for x,y in pts]
    poly(d, inner, L)
    shine(d,13,12)
    apply_highlight(img); return img

def draw_ingr_bone(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    b = BONE; db = dk(BONE,0.65)
    ell(d, 8,4,15,11, b, db)
    ell(d, 17,21,24,28, b, db)
    rect(d, 12,6,20,26, b, db)
    rect(d, 13,8,19,24, lt(b,1.1))
    shine(d,13,8)
    apply_highlight(img); return img

def draw_ingr_heart(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    red = _c(180,30,30); lred = lt(red,1.3)
    # Heart shape: two circles + triangle
    ell(d, 6,8,16,18, red, BLK)
    ell(d, 16,8,26,18, red, BLK)
    poly(d, [(6,14),(26,14),(16,26)], red, BLK)
    ell(d, 8,10,14,16, lred)
    shine(d,10,11)
    apply_highlight(img); return img

def draw_ingr_silk(P, L, D):
    """Web, silk, thread."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Ball of thread
    ell(d, 6,8,26,24, P, D)
    ell(d, 8,10,24,22, L)
    # Spiral lines
    for r2 in [4,6,8]:
        d.arc([16-r2,16-r2,16+r2,16+r2], start=0, end=320, fill=D, width=1)
    # Trailing thread
    d.line([(20,10),(28,4)], fill=P, width=1)
    shine(d,13,13)
    apply_highlight(img); return img

def draw_ingr_essence(P, L, D):
    """Essence, soul, orb — glowing ball."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Outer glow
    ell(d, 4,4,28,28, (*P[:3],60))
    ell(d, 6,6,26,26, P, D)
    ell(d, 8,8,24,24, L)
    ell(d, 11,11,21,21, lt(L,1.4))
    shine(d,13,13)
    apply_highlight(img); return img

def draw_ingr_musk(P, L, D):
    """Musk, gland, organ."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    ell(d, 8,8,24,24, P, D)
    ell(d, 10,10,22,22, L)
    # Gland bumps
    ell(d, 11,10,15,14, lt(P,1.2))
    ell(d, 17,12,21,16, lt(P,1.2))
    ell(d, 13,16,17,20, lt(P,1.2))
    shine(d,12,12)
    apply_highlight(img); return img

def draw_ingr_shell(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    poly(d, [(6,20),(16,6),(26,20),(22,28),(10,28)], P, D)
    poly(d, [(7,20),(16,8),(25,20),(21,26),(11,26)], L)
    for i,y in enumerate([12,16,20]):
        w = 4+i*4
        d.line([(16-w,y),(16+w,y)], fill=D, width=1)
    shine(d,12,12)
    apply_highlight(img); return img

def draw_ingr_vial(P, L, D):
    """Blood, fluid, extract in vial."""
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Vial shape
    rect(d, 13,4,19,8, _c(180,180,200), BLK)  # stopper
    poly(d, [(11,8),(21,8),(23,26),(9,26)], _c(180,190,210,200), BLK)
    # Fluid inside
    poly(d, [(12,14),(20,14),(22,25),(10,25)], (*P[:3],220))
    shine(d,12,10)
    apply_highlight(img); return img

def draw_ingr_claw(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Three curved claws fanned out
    for i,ang in enumerate([-0.3,0,0.3]):
        pts=[]
        for t in range(10):
            r2=3+t*1.5
            a = ang + t*0.06
            pts.append((16+r2*math.sin(a), 26-r2*math.cos(a)))
        d.line(pts, fill=BONE if i==1 else dk(BONE,0.8), width=2)
    poly(d, [(13,26),(19,26),(20,30),(12,30)], dk(P,0.7), BLK)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# ARROW / BOLT drawing
# ---------------------------------------------------------------------------

def draw_arrow(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Shaft
    d.line([(6,26),(24,8)], fill=_c(120,80,40), width=2)
    # Head
    poly(d, [(22,6),(28,4),(26,10)], P, D)
    # Fletching
    poly(d, [(6,26),(2,22),(8,20)], _c(200,60,60))
    poly(d, [(6,26),(4,30),(10,26)], _c(200,60,60))
    apply_highlight(img); return img

def draw_bolt(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    d.line([(4,18),(28,14)], fill=_c(120,80,40), width=2)
    poly(d, [(24,12),(30,14),(26,18)], P, D)
    rect(d, 4,15,10,18, _c(200,60,60))
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# CONTAINER drawing functions
# ---------------------------------------------------------------------------

def draw_chest(P, L, D, spiked=False):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    # Main body
    rect(d, 4,12,28,26, P, D)
    rect(d, 5,13,27,25, L)
    # Lid
    poly(d, [(4,12),(28,12),(28,8),(4,8)], dk(P,0.8), D)
    poly(d, [(5,11),(27,11),(27,9),(5,9)], P)
    # Hinge
    ell(d, 10,7,14,11, dk(P,0.6), D)
    ell(d, 18,7,22,11, dk(P,0.6), D)
    # Lock
    ell(d, 13,18,19,23, GOLD, dk(GOLD,0.5))
    d.rectangle([14,20,18,24], fill=BLK)
    if spiked:
        for sx in [6,11,16,21,26]:
            poly(d, [(sx,12),(sx+2,12),(sx+1,9)], _c(180,180,180), BLK)
    shine(d,8,13)
    apply_highlight(img); return img

def draw_vault(P, L, D):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    rect(d, 3,6,29,28, P, D)
    rect(d, 5,8,27,26, L)
    # Door seam
    d.line([(16,6),(16,28)], fill=D, width=2)
    d.line([(3,17),(29,17)], fill=D, width=1)
    # Wheel handle
    ell(d, 10,12,22,22, P, D)
    ell(d, 12,14,20,20, L)
    for ang in [0,math.pi/2,math.pi,3*math.pi/2]:
        d.line([(16,16),(int(16+4*math.cos(ang)),int(16+4*math.sin(ang)))], fill=D, width=2)
    shine(d,8,10)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# LOCKPICK drawing function
# ---------------------------------------------------------------------------

def draw_lockpick_item(P, L, D, master=False):
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    metal = _c(180,180,195) if master else _c(140,140,155)
    # Handle
    rect(d, 4,24,12,28, metal, BLK)
    # Shank
    d.line([(12,26),(27,10)], fill=metal, width=2)
    d.line([(13,26),(28,10)], fill=lt(metal,1.3), width=1)
    # Pick tip
    if master:
        poly(d, [(26,8),(29,10),(27,13)], lt(metal,1.4), BLK)
        d.line([(26,8),(24,12)], fill=lt(metal,1.3), width=1)
    else:
        poly(d, [(26,9),(29,11),(27,14)], metal, BLK)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# ARTIFACT — Philosopher's Stone
# ---------------------------------------------------------------------------

def draw_philosophers_stone():
    img = new_canvas(); d = ImageDraw.Draw(img,'RGBA')
    gold = GOLD; wht = WHT
    # Outer glow rings
    for r2,a in [(14,40),(12,70),(10,100)]:
        d.ellipse([16-r2,16-r2,16+r2,16+r2], fill=(255,210,50,a))
    # Main stone — faceted octagon
    poly(d, [(16,2),(22,4),(26,10),(26,22),(22,28),(16,30),(10,28),(6,22),(6,10),(10,4)],
         gold, dk(gold,0.5))
    poly(d, [(16,4),(22,6),(25,12),(25,20),(22,26),(16,28),(10,26),(7,20),(7,12),(10,6)],
         lt(gold,1.3))
    poly(d, [(16,8),(21,11),(21,21),(16,24),(11,21),(11,11)], lt(gold,1.6))
    # Inner rune glow
    ell(d, 13,13,19,19, (*wht[:3],200))
    shine(d,14,12); shine(d,18,10)
    apply_highlight(img); return img

# ---------------------------------------------------------------------------
# Item classification helpers
# ---------------------------------------------------------------------------

def get_weapon_draw_fn(item_id):
    i = item_id.lower()
    if any(x in i for x in ['zweihander','flamberge','claymore','executioner','bastard_sword']):
        return draw_zweihander
    if any(x in i for x in ['longsword','greatsword','estoc','dao','gladius','kopis','mameluke','sica','cinquedea','katana','war_scythe','pugio','kukri','falchion','venomfang','soul_reaver','dawnbreaker','francisca','partisan','naginata']):
        return draw_longsword
    if 'rapier' in i:      return draw_rapier
    if any(x in i for x in ['scimitar','saber','sabre']):  return draw_scimitar
    if 'dagger' in i:      return draw_dagger
    if 'crossbow' in i:    return draw_crossbow
    if 'longbow' in i:     return draw_longbow
    if 'bow' in i:         return draw_bow
    if any(x in i for x in ['greataxe','double_axe']):     return draw_greataxe
    if 'axe' in i:         return draw_axe
    if 'halberd' in i:     return draw_halberd
    if 'glaive' in i:      return draw_glaive
    if 'spear' in i:       return draw_spear
    if 'morningstar' in i: return draw_morningstar
    if 'flail' in i:       return draw_flail
    if 'warhammer' in i or ('hammer' in i and 'war' in i): return draw_warhammer
    if 'hammer' in i:      return draw_club  # repurpose
    if 'mace' in i:        return draw_mace
    if 'staff' in i:       return draw_staff
    if 'club' in i:        return draw_club
    if 'sword' in i:       return draw_sword
    return draw_sword  # fallback

def get_armor_draw_fn(item_id):
    i = item_id.lower()
    if any(x in i for x in ['great_helm','armet','bascinet','sallet']):
        return lambda P,L,D: draw_helm(P,L,D, full=True)
    if any(x in i for x in ['helm','coif','cap','hat']) and 'coif' not in i:
        return draw_helm
    if 'coif' in i:        return draw_coif
    if any(x in i for x in ['cap','hood']):                 return draw_cap if 'cap' in i else draw_hood
    if any(x in i for x in ['boots','sandals','sabatons']): return draw_boots
    if any(x in i for x in ['gauntlets','gloves']):
        return draw_gauntlets if 'gaunt' in i else draw_gloves
    if 'bracers' in i or 'wraps' in i:  return draw_bracers
    if any(x in i for x in ['leggings','greaves']):         return draw_leggings
    if any(x in i for x in ['cloak','mantle']):             return draw_cloak
    if any(x in i for x in ['robe']):                       return draw_robe
    if any(x in i for x in ['shirt','linen','silk_s','elven','cloth_s']): return draw_shirt
    if any(x in i for x in ['chain_mail','ring_mail','scale_mail','banded_mail',
                              'splint_mail','hauberk','chain_sh','scale_sh']):
        return lambda P,L,D: draw_body_armor(P,L,D,'chain')
    if any(x in i for x in ['cloth_armor','padded_armor','brigandine','coat_of']):
        return lambda P,L,D: draw_body_armor(P,L,D,'robe')
    return lambda P,L,D: draw_body_armor(P,L,D,'plate')

def get_ingr_draw_fn(item_id, item_name):
    i = item_id.lower(); n = item_name.lower()
    if any(x in i or x in n for x in ['meat','flesh','frog_leg','bullywug_leg']): return draw_ingr_meat
    if any(x in i or x in n for x in ['hide','skin','pelt']):                     return draw_ingr_hide
    if any(x in i or x in n for x in ['scale']):                                  return draw_ingr_scale
    if any(x in i or x in n for x in ['fang','claw','talon','nail']):             return draw_ingr_claw
    if any(x in i or x in n for x in ['tooth','tusk','horn','spike','spine','shard','thorn']): return draw_ingr_fang
    if any(x in i or x in n for x in ['eye','eyeball']):                          return draw_ingr_eye
    if any(x in i or x in n for x in ['dust','powder','ash','spore','pollen','sand']): return draw_ingr_dust
    if any(x in i or x in n for x in ['feather','quill','wing','plume']):         return draw_ingr_feather
    if any(x in i or x in n for x in ['gem','crystal','shard','jewel','stone','mineral']): return draw_ingr_gem
    if any(x in i or x in n for x in ['slime','ooze','extract','goo','ichor','mucus']): return draw_ingr_blob
    if any(x in i or x in n for x in ['bone','skull','marrow','rib']):            return draw_ingr_bone
    if any(x in i or x in n for x in ['heart','liver','brain','organ','gut']):    return draw_ingr_heart
    if any(x in i or x in n for x in ['silk','web','thread','fiber','filament']): return draw_ingr_silk
    if any(x in i or x in n for x in ['essence','soul','spirit','void','mana','energy','orb']): return draw_ingr_essence
    if any(x in i or x in n for x in ['shell','carapace','chitin','plate']):      return draw_ingr_shell
    if any(x in i or x in n for x in ['blood','venom','bile','fluid','acid','poison','saliva']): return draw_ingr_vial
    if any(x in i or x in n for x in ['musk','gland','sac','pouch','bladder']):   return draw_ingr_musk
    return draw_ingr_blob  # fallback

def get_food_draw_fn(item_id):
    i = item_id.lower()
    if 'bread' in i or 'biscuit' in i or 'cracker' in i: return draw_bread
    if 'mushroom' in i or 'fungus' in i:  return draw_mushroom
    if 'apple' in i or 'fruit' in i:      return draw_apple
    if 'cheese' in i:                     return draw_cheese
    if 'ration' in i or 'trail' in i:     return draw_rations
    if 'cooked' in i or 'roasted' in i or 'stew' in i: return draw_cooked_meat
    return draw_meat  # dried_meat etc.

# ---------------------------------------------------------------------------
# Material → color palette
# ---------------------------------------------------------------------------
MATERIAL_PALETTE = {
    'wood':           ((139, 90, 43),   (185, 125, 65),  (85, 52, 24)),
    'hardwood':       ((120, 75, 35),   (160, 105, 55),  (78, 45, 18)),
    'ironwood':       ((80, 62, 40),    (115, 88, 58),   (52, 38, 22)),
    'iron':           ((108, 108, 120), (155, 155, 165), (64, 64, 76)),
    'bronze':         ((160, 102, 40),  (205, 148, 72),  (98, 58, 20)),
    'steel':          ((145, 148, 162), (192, 192, 200), (88, 90, 104)),
    'chain':          ((138, 140, 150), (185, 185, 196), (82, 84, 94)),
    'hardened_gold':  ((200, 165, 30),  (240, 210, 62),  (128, 105, 15)),
    'gold':           ((210, 178, 38),  (250, 225, 68),  (138, 118, 20)),
    'mithril':        ((138, 178, 218), (182, 214, 248), (88, 122, 158)),
    'crystal':        ((98, 222, 202),  (158, 248, 232), (52, 148, 135)),
    'dragonscale':    ((52, 108, 52),   (88, 152, 88),   (28, 68, 28)),
    'adamantine':     ((58, 58, 95),    (92, 92, 140),   (32, 32, 58)),
    'diamond':        ((178, 238, 255), (218, 252, 255), (108, 178, 212)),
    'dragonbone':     ((212, 192, 162), (238, 222, 198), (142, 125, 98)),
    'shadow':         ((32, 22, 46),    (62, 42, 82),    (15, 10, 22)),
    'shadowweave':    ((28, 18, 42),    (56, 36, 76),    (12, 8, 20)),
    'void':           ((42, 12, 62),    (82, 28, 112),   (22, 5, 32)),
    'padded':         ((175, 155, 118), (212, 192, 152), (115, 102, 74)),
    'leather':        ((122, 82, 32),   (162, 118, 56),  (78, 50, 15)),
    'cloth':          ((178, 165, 148), (215, 202, 182), (118, 108, 96)),
    'linen':          ((200, 192, 172), (226, 218, 202), (138, 132, 118)),
    'silk':           ((202, 178, 212), (232, 208, 242), (138, 118, 152)),
    'wool':           ((165, 152, 132), (202, 188, 168), (108, 98, 88)),
    'fur':            ((142, 112, 82),  (178, 148, 112), (92, 72, 50)),
    'scale':          ((102, 132, 102), (138, 168, 138), (62, 90, 62)),
    'plate':          ((118, 122, 135), (165, 168, 178), (72, 74, 88)),
    'ring':           ((128, 132, 142), (175, 178, 188), (78, 80, 90)),
    'elven':          ((162, 205, 155), (198, 232, 192), (108, 145, 102)),
    'full':           ((115, 118, 132), (162, 165, 175), (68, 72, 84)),
    'banded':         ((128, 128, 140), (172, 172, 185), (78, 78, 90)),
    'coat':           ((118, 95, 62),   (155, 132, 92),  (78, 60, 38)),
    'half':           ((122, 122, 135), (168, 168, 180), (75, 75, 88)),
    'splint':         ((130, 130, 142), (175, 175, 188), (80, 80, 92)),
    'hauberk':        ((138, 140, 152), (182, 185, 195), (85, 88, 98)),
    'brigandine':     ((108, 88, 58),   (148, 122, 85),  (68, 55, 35)),
}

def get_material_palette(item_id, json_color=None):
    """Extract color palette from material prefix or fall back to JSON color."""
    i = item_id.lower()
    for mat, pal in sorted(MATERIAL_PALETTE.items(), key=lambda x:-len(x[0])):
        if i.startswith(mat) or f'_{mat}' in i:
            return (_c(*pal[0]), _c(*pal[1]), _c(*pal[2]))
    if json_color:
        P = C(json_color)
        return (P, lt(P, 1.35), dk(P, 0.55))
    return (_c(130,130,140), _c(175,175,185), _c(78,78,90))

# ---------------------------------------------------------------------------
# Wand effect → color
# ---------------------------------------------------------------------------
WAND_EFFECT_COLORS = {
    'heal': (60, 200, 80),
    'extra_healing': (40, 220, 100),
    'restore': (80, 210, 110),
    'sleep': (140, 80, 200),
    'deep_sleep': (120, 60, 180),
    'slumber': (100, 50, 160),
    'fire': (220, 100, 30),
    'flame': (240, 120, 40),
    'inferno': (255, 140, 20),
    'embers': (200, 80, 20),
    'ice': (80, 200, 240),
    'cold': (100, 180, 230),
    'frost': (120, 200, 250),
    'glaciation': (60, 160, 220),
    'lightning': (255, 240, 60),
    'shock': (240, 220, 40),
    'storm': (200, 180, 20),
    'death': (80, 20, 100),
    'drain_life': (120, 20, 80),
    'annihilation': (60, 10, 80),
    'disintegration': (100, 30, 120),
    'dispelling': (180, 160, 220),
    'detect': (80, 160, 220),
    'clairvoyance': (60, 140, 200),
    'mapping': (60, 120, 180),
    'identify': (120, 180, 240),
    'teleport': (180, 200, 240),
    'confuse': (220, 80, 180),
    'confusion': (200, 60, 160),
    'bewilderment': (210, 70, 170),
    'charm': (240, 120, 180),
    'domination': (200, 100, 160),
    'force': (180, 180, 100),
    'earthquake': (140, 110, 70),
    'digging': (120, 90, 50),
    'acid': (100, 180, 20),
    'corrosion': (80, 160, 30),
    'disease': (80, 140, 40),
    'poison': (60, 140, 30),
    'curse': (80, 20, 80),
    'dread': (60, 20, 60),
    'darkness': (30, 20, 50),
    'flight': (180, 220, 255),
    'levitate': (160, 200, 240),
    'illumination': (255, 250, 180),
    'light': (255, 245, 160),
    'create_monster': (160, 80, 40),
    'speed': (220, 200, 60),
    'fortitude': (60, 200, 140),
    'empowerment': (200, 180, 60),
    'ethereality': (180, 220, 240),
    'cancellation': (160, 160, 180),
    'dissolution': (100, 140, 100),
    'aging': (120, 100, 80),
    'blindness': (40, 40, 60),
    'concealment': (80, 80, 100),
    'crushing': (140, 80, 40),
    'drain_magic': (80, 40, 120),
    'explosion': (220, 140, 30),
    'fear': (80, 40, 20),
    'acuity': (100, 200, 200),
    'cold_shield': (120, 200, 245),
    'fire_shield': (240, 130, 40),
}

def get_wand_color(wand_id, json_color=None):
    i = wand_id.replace('wand_of_','').lower()
    for eff, col in WAND_EFFECT_COLORS.items():
        if eff in i:
            return _c(*col)
    if json_color:
        return C(json_color)
    return _c(160,100,200)

# ---------------------------------------------------------------------------
# Accessory (ring/amulet) color
# ---------------------------------------------------------------------------
ACCESSORY_EFFECT_COLORS = {
    'fire': (220, 80, 30), 'cold': (80, 180, 230), 'shock': (230, 220, 40),
    'poison': (80, 180, 40), 'magic': (160, 80, 220), 'drain': (120, 40, 120),
    'regen': (40, 200, 80), 'speed': (220, 200, 40), 'haste': (220, 200, 40),
    'strength': (200, 60, 40), 'dexterity': (80, 200, 200), 'constitution': (200, 100, 40),
    'intellect': (100, 100, 220), 'wisdom': (200, 180, 80), 'perception': (80, 220, 160),
    'warning': (220, 140, 40), 'searching': (180, 180, 80), 'telepathy': (120, 80, 200),
    'levitate': (160, 200, 240), 'invis': (200, 200, 220), 'displace': (180, 180, 220),
    'reflect': (220, 220, 240), 'life': (200, 40, 80), 'clairvoy': (80, 160, 220),
    'sustenance': (180, 150, 80), 'truesight': (200, 200, 120), 'spell': (180, 100, 220),
    'protection': (180, 180, 200), 'curse': (80, 20, 100), 'sleep': (140, 80, 200),
    'archmage': (120, 80, 200), 'dragon': (60, 160, 40), 'shadow': (40, 30, 60),
    'titan': (180, 60, 40), 'philosophers': (220, 190, 40),
}

def get_accessory_color(acc_id, json_color=None):
    i = acc_id.lower()
    for eff, col in ACCESSORY_EFFECT_COLORS.items():
        if eff in i:
            return _c(*col)
    if json_color:
        return C(json_color)
    return _c(180, 140, 80)

# ---------------------------------------------------------------------------
# Scroll effect → background tint
# ---------------------------------------------------------------------------
SCROLL_TINTS = {
    'heal': (80, 220, 100), 'mapping': (80, 180, 220), 'identify': (120, 160, 240),
    'enchant': (220, 200, 60), 'remove_curse': (200, 160, 240), 'confuse': (200, 80, 180),
    'teleport': (160, 200, 240), 'boss_reward': (220, 190, 40), 'fire': (220, 100, 30),
}

def get_scroll_color(scroll_id, json_color=None):
    i = scroll_id.replace('scroll_of_','').lower()
    for k,v in SCROLL_TINTS.items():
        if k in i:
            return _c(*v)
    if json_color:
        return C(json_color)
    return _c(180, 140, 220)

# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def process_file(fname, ok_count, err_count):
    path = os.path.join(ROOT, 'data', 'items', f'{fname}.json')
    if not os.path.exists(path):
        return ok_count, err_count
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        data = {item['id']: item for item in data if 'id' in item}

    for item_id, item in data.items():
        try:
            img = _make_sprite(fname, item_id, item)
            if img is None:
                continue
            out = os.path.join(OUT_DIR, f'{item_id}.png')
            img.save(out)
            ok_count += 1
        except Exception as e:
            print(f'  WARN {item_id}: {e}')
            err_count += 1
    return ok_count, err_count


def _make_sprite(category, item_id, item):
    json_col = item.get('color')
    P, L, D = get_material_palette(item_id, json_col)

    if category == 'weapon':
        fn = get_weapon_draw_fn(item_id)
        return fn(P, L, D)

    if category == 'armor':
        fn = get_armor_draw_fn(item_id)
        return fn(P, L, D)

    if category == 'shield':
        large = item.get('tier',1) >= 3
        return draw_shield(P, L, D, large=large)

    if category == 'scroll':
        col = get_scroll_color(item_id, json_col)
        return draw_scroll(col, lt(col,1.3), dk(col,0.5))

    if category == 'wand':
        col = get_wand_color(item_id, json_col)
        return draw_wand(col, lt(col,1.35), dk(col,0.5))

    if category == 'food':
        fn = get_food_draw_fn(item_id)
        return fn(P, L, D)

    if category == 'artifact':
        return draw_philosophers_stone()

    if category == 'accessory':
        col = get_accessory_color(item_id, json_col)
        lc = lt(col,1.3); dc = dk(col,0.55)
        if 'amulet' in item_id or item.get('slot') == 'amulet':
            return draw_amulet(col, lc, dc)
        return draw_ring(col, lc, dc)

    if category == 'ammo':
        if 'bolt' in item_id:
            return draw_bolt(P, L, D)
        return draw_arrow(P, L, D)

    if category == 'container':
        if 'vault' in item_id:
            return draw_vault(P, L, D)
        spiked = 'spike' in item_id or 'spiked' in item_id
        return draw_chest(P, L, D, spiked=spiked)

    if category == 'lockpick':
        master = 'master' in item_id
        return draw_lockpick_item(P, L, D, master=master)

    if category == 'ingredient':
        name = item.get('name', item_id)
        fn = get_ingr_draw_fn(item_id, name)
        if json_col:
            col = C(json_col)
            return fn(col, lt(col,1.35), dk(col,0.55))
        return fn(P, L, D)

    return None


def main():
    categories = [
        'weapon','armor','shield','scroll','wand',
        'food','artifact','accessory','ammo',
        'container','lockpick','ingredient',
    ]
    ok = err = 0
    for cat in categories:
        ok, err = process_file(cat, ok, err)
    print(f'Generated {ok} item sprites ({err} warnings) -> {OUT_DIR}')


if __name__ == '__main__':
    main()
