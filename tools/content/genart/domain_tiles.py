"""Domain theme tiles (Dungeon Alive): the temple, the deep, the rime halls and the abyss.

    <ComfyUI python> tools/content/genart/domain_tiles.py paint [--only id,id] [--n 3] [--seed N]
    <ComfyUI python> tools/content/genart/domain_tiles.py build [--pick id=2,id=3]

Made exactly the way tiles.py made the base set, with its own functions: each theme's
materials are painted flat from above through the same two passes (tiles.paint), then
cut into tiles in code. Floors of dressed stone (temple, rime) are slabs with the joint
on the tile's edge, in tiles.FLOOR_LAYOUTS; walls of masonry are staggered courses that
repeat every tile; natural surfaces (the deep's cave floor, the abyss's black glass,
rock, water) are a wrapped cross-fade (tiles.wrap).

A floor theme has six variants that the renderer mixes by position, so they must meet
each other anywhere. Slab floors meet at a joint. A natural floor has no joint, so
every variant keeps the SAME wrapped border (`edge_locked`): only its middle differs,
and any variant can sit beside any other with no seam.

A variant's one difference (a crack, a drift of ash, a root) is laid on in code from
a painted material or a painted decal (a cut-out prop, see domain_props.py), inside a
soft irregular mask that stays clear of the tile's edges.

Output: _genart/domains/tiles/materials/<id>/c<N>.png and
_genart/domains/install/themes/<theme>/<file>.png (64 px, opaque).
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tiles  # noqa: E402

ROOT = tiles.ROOT
OUT = os.path.join(ROOT, '_genart', 'domains', 'tiles')
INSTALL = os.path.join(ROOT, '_genart', 'domains', 'install', 'themes')
T = tiles.T

# A material that is made of many small things (leaves, coins, pebbles, snow) breaks the
# fixed lead's "no objects lying on it", so it brings its own.
LEAD_FIELD = ("A classic fantasy oil painting, looking straight down from directly above at {what} "
              "It fills the whole picture from edge to edge like a texture sample: the same everywhere, spread "
              "evenly, no border, no frame, no horizon, no walls, no perspective. Flat even light from the upper left, "
              "soft shallow shadows only. Painted like the scenery in a 1980s fantasy roleplaying rulebook: weathered, "
              "worn, serious, rich but muted colours. {colours}")
NEG_FIELD = ("face, carving, statue, rings, concentric circles, bright centre, dark rim, creatures, people, border, frame, "
             "vignette, horizon, perspective, side view, text, photo, 3d render, cartoon, bright candy colours, "
             "strong cast shadows, lens blur")

MATERIALS = {
    # ---------------------------------------------------------------- the forgotten temple
    'temple_marble': dict(
        what="the surface of one single huge old slab of marble in the floor of a long-forgotten temple: pale grey "
             "marble gone dull grey-green with age and damp, with faint soft grey veins, fine pits, a few hairline "
             "cracks and darker damp stains. One unbroken slab: no joints and no gaps anywhere.",
        colours="Dull pale grey marble with a cool grey-green cast, soft grey veins, low contrast.",
        short="old dull pale grey-green marble slab surface with faint veins and damp stains, no joints"),
    'temple_ashlar': dict(
        what="a completely flat, blank slab of pale grey-white marble, like a mason's sample: only the bare cut "
             "surface of the stone, with fine chisel marks, small chips, faint grey veins and grey-green weather "
             "stains. It is one unbroken plain surface: no joints, no mortar, no bricks, and nothing carved on it.",
        colours="Pale grey-white marble with faint grey-green damp stains.",
        short="flat blank pale grey-white marble surface with fine chisel marks and faint veins, nothing carved"),
    'moss': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="a thick carpet of damp dark green moss growing over stone: dense soft cushions of tiny moss fronds, "
             "with a few small grey stone specks showing through.",
        colours="Dark green and deep olive-green moss with a few brighter yellow-green tips.",
        short="thick dark green moss carpet, dense tiny fronds, even all over"),
    'temple_rock': dict(
        what="rough natural dark grey rock, untouched by tools: lumpy and cracked, with deep black crevices between "
             "rounded bulges, patches of dark green moss on the bulges, and thin pale grey-brown tree roots running "
             "along the crevices.",
        colours="Very dark grey rock, dark green moss, pale grey-brown roots, dull and shadowed.",
        short="rough very dark grey natural rock with dark moss patches and thin pale roots in the crevices"),
    'temple_water': dict(
        what="the surface of still, stagnant, murky green water in an old temple pool, the same everywhere: dark and "
             "opaque, a faint film of scum, many tiny irregular ripples with faint dull glints. There is no centre "
             "and no rings: nothing has dropped into it, and no part of the picture differs from any other.",
        colours="Murky dark green and dark olive water, nearly black in the shadows, dull grey-green glints.",
        short="still murky dark green stagnant water surface, faint scum, tiny ripples, no rings, no centre"),
    # ---------------------------------------------------------------- the scorched deep
    'deep_floor': dict(
        what="the surface of an uneven natural cave floor never worked by tools: dark brown stone, gently lumpy, "
             "with fine grit, small chips and shallow hollows, dusty. No joints, no slabs, no cracks.",
        colours="Dark brown and brown-grey stone, dusty, low contrast.",
        short="uneven dark brown natural cave floor with fine grit and shallow hollows, no joints"),
    'deep_wall': dict(
        what="rough natural cave rock, untouched by tools: lumpy rounded bulges of dark brown rock with deep black "
             "crevices between them, streaked and smudged with black soot.",
        colours="Dark brown-black rock, dull brown-grey highlights on the bulges, black soot streaks.",
        short="rough dark brown-black natural cave rock with crevices and black soot streaks"),
    'deep_crag': dict(
        what="rough natural cave rock, untouched by tools: jagged broken rock with sharp angular facets, slanting "
             "broken faces and deep black cracks between them, none of them square, dark brown-black, streaked and "
             "smudged with black soot, a little dull brown-grey on the upper edges.",
        colours="Dark brown-black rock, dull brown-grey on the lit edges, black soot streaks, black cracks.",
        short="jagged angular dark brown-black natural cave rock with slanting facets, black cracks and soot"),
    'ash': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="a soft drift of fine pale grey ash lying over dark stone: smooth low ridges and ripples of powdery ash "
             "with a few small black cinders in it.",
        colours="Pale ash grey and warm mid-grey, a few black cinders.",
        short="soft drift of fine pale grey ash with low ripples and a few black cinders"),
    'pebbles': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="a cave floor of dark brown stone strewn thickly with small rounded pebbles and grit of different sizes.",
        colours="Dark brown, grey-brown and dull ochre-brown pebbles on dark brown stone.",
        short="dark brown cave floor strewn with small rounded pebbles and grit"),
    'gold_coins': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="a dragon's hoard: a thick bed of old gold coins lying heaped and overlapping in every direction, with "
             "a few dark gaps between them, the same everywhere.",
        colours="Old gold coins, warm deep yellow-gold with brown-gold shadows, dull with age, a few bright glints.",
        short="thick bed of overlapping old gold coins, dull deep yellow-gold, even all over"),
    # ---------------------------------------------------------------- the rime halls
    'rime_flag': dict(
        what="the surface of one single huge worn grey flagstone in the floor of an old northern hall, dusted with a "
             "thin frost: grey stone with fine pits and hairline cracks, and a fine powder of pale blue-white frost "
             "lying thinly over it, thicker in the pits. One unbroken slab: no joints and no gaps anywhere.",
        colours="Cold mid-grey stone with a thin pale blue-white frost dusting, low contrast.",
        short="worn cold grey flagstone surface dusted with thin pale blue-white frost, no joints"),
    'rime_wallstone': dict(
        what="a completely flat, blank slab of grey granite, like a mason's sample: only the bare cut surface with fine "
             "chisel marks and small chips, furred all over with a thin crust of white rime frost crystals. It is one "
             "unbroken plain surface: no joints, no mortar, and nothing carved on it.",
        colours="Cold grey stone under white and pale blue-white rime frost.",
        short="flat blank grey granite surface furred with white rime frost crystals, nothing carved"),
    'snow': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="old wind-packed snow lying over stone: soft smooth drifts with gentle rounded ridges, lightly crusted.",
        colours="White and pale blue-white snow with soft blue-grey shadows.",
        short="old wind-packed white snow with soft rounded drifts and blue-grey shadows"),
    'frost_ferns': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="frost ferns on dark stone: feathery white ice crystals branching like the fronds of ferns across dark "
             "grey stone, spread all over.",
        colours="White and pale blue-white frost crystals on dark blue-grey stone.",
        short="feathery white frost fern crystals branching across dark grey stone"),
    'rime_rock': dict(
        what="solid natural grey rock buried under old snow and ice: lumpy rounded bulges of rock half covered with "
             "crusted snow and glassy ice, with dark crevices between them.",
        colours="Dark grey rock, dull blue-grey shadowed snow, grey-white ice, shadowed and dim.",
        short="dark grey natural rock half buried in crusted shadowed snow and ice, dark crevices"),
    'rime_water': dict(
        what="the surface of still black water, the same everywhere: dark and calm, with thin pale skins of new ice "
             "floating on it here and there and a few faint glints. There is no centre and no rings.",
        colours="Black and very dark blue-grey water, pale grey-white thin ice skins.",
        short="still black water surface with thin pale grey-white skins of new ice floating, no rings"),
    # ---------------------------------------------------------------- the abyss
    'abyss_glass': dict(
        what="the surface of a floor of black volcanic glass, the same everywhere: glassy black stone with a dull "
             "sheen, broken by a fine net of thin cracks with a faint deep red glow in them.",
        colours="Black and charcoal glass with a dull grey sheen, thin cracks glowing a faint deep red.",
        short="black volcanic glass surface with dull sheen and thin faintly red-glowing cracks, even all over"),
    'basalt': dict(
        what="a completely flat, blank slab of black basalt, like a mason's sample: only the bare surface of the rock, "
             "dull charcoal with fine pits and small chips. It is one unbroken plain surface, nothing carved on it.",
        colours="Charcoal black and dark grey basalt.",
        short="flat blank charcoal black basalt surface with fine pits"),
    'obsidian': dict(
        what="solid black obsidian rock: lumpy bulges of black volcanic glass with sharp shell-shaped fractures, "
             "glossy dull grey highlights on the edges, and deep black crevices between them.",
        colours="Black glass with dull grey highlights.",
        short="solid glassy black obsidian rock with shell-shaped fractures and dull grey highlights"),
    'carpet': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="the woven surface of an old worn carpet, deep faded red wool with a faint small repeating pattern of darker "
             "red and dull brown diamonds, the pile worn thin and flattened, a little dusty.",
        colours="Deep faded red, darker wine red and dull brown pattern, dusty grey-brown where worn.",
        short="old worn deep faded red wool carpet surface, faint small diamond pattern, even all over"),
    'sulphur': dict(
        lead=LEAD_FIELD, neg=NEG_FIELD,
        what="a crust of sulphur over dark rock: a lumpy, crystalline, cracked crust of dull sulphur-yellow and pale "
             "ochre, with dark rock showing in the cracks.",
        colours="Dull sulphur yellow, pale ochre, a little brown, dark rock in the cracks.",
        short="lumpy cracked crust of dull sulphur yellow and pale ochre over dark rock"),
}


def paint(only, n, seed):
    """tiles.paint, pointed at the domain materials and their own folder."""
    tiles.OUT, tiles.MATERIALS = OUT, MATERIALS
    tiles.paint(only, n, seed)


# ---------------------------------------------------------------- helpers
YY, XX = np.mgrid[0:T, 0:T].astype(np.float32)
EDGE = np.minimum(np.minimum(XX, T - 1 - XX), np.minimum(YY, T - 1 - YY))     # distance to the tile's rim


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def match(a, mean, contrast=1.0):
    """Scale a texture so its brightness averages `mean`, then set its contrast round that mean."""
    a = a * (mean / max(1.0, float(lum(a).mean())))
    return np.clip(mean + (a - mean) * contrast, 0, 255)


def crop(mid, pick, region=256, at=None, out=T):
    """`region` source pixels of a painted material, shrunk to `out` pixels."""
    im = Image.open(os.path.join(OUT, 'materials', mid, f'c{pick}.png')).convert('RGB')
    if at is None:
        at = ((im.width - region) // 2, (im.height - region) // 2)
    x, y = at
    return np.asarray(im.crop((x, y, x + region, y + region)).resize((out, out), Image.BOX)).astype(np.float32)


def noise(rng, sigma=3.0, n=T):
    """Smooth random field 0..1 that repeats with the tile."""
    f = ndi.gaussian_filter(rng.random((n, n)), sigma, mode='wrap')
    return (f - f.min()) / max(1e-6, f.max() - f.min())


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def blob(rng, cx, cy, rx, ry, rough=0.35, soft=3.0):
    """A soft irregular patch: an ellipse whose edge is broken up by noise."""
    d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
    d = d + rough * (noise(rng, 2.5) * 2 - 1)
    return smooth((1 - d) * min(rx, ry) / soft)


def off_edges(m, margin=3, ramp=3):
    """Keep a mask clear of the tile's rim, so the rim stays the shared one."""
    return m * smooth((EDGE - margin) / ramp)


def path(rng, pts, jitter=2.0, width=1.0, depth=4):
    """A jagged line through `pts` (midpoint displacement), drawn anti-aliased: mask 0..1."""
    for _ in range(depth):
        new = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            dx, dy = y1 - y0, x0 - x1
            ln = max(1e-6, np.hypot(dx, dy))
            k = rng.uniform(-1, 1) * jitter * ln / 16
            new += [(mx + dx / ln * k, my + dy / ln * k), (x1, y1)]
        pts = new
        jitter *= 0.8
    S = 4
    im = Image.new('L', (T * S, T * S), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(im).line([(x * S, y * S) for x, y in pts], fill=255, width=max(1, int(round(width * S))), joint='curve')
    return np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0


def lay(a, f, m):
    """Lay `f` (a colour, or a texture) over `a` through mask `m`."""
    m = m[..., None]
    return a * (1 - m) + np.asarray(f, np.float32) * m


def edge_locked(sources, base, band=11):
    """Variants of a natural floor that all keep the SAME border, so any variant meets any
    other with no seam: inside the border each takes its own crop of the material."""
    w = smooth(1 - EDGE / band)[..., None]
    gain = 1.0 / np.sqrt(w * w + (1 - w) * (1 - w))
    out = []
    for s in sources:
        v = base * w + s * (1 - w)
        m = v.mean((0, 1), keepdims=True)
        out.append(np.clip(m + (v - m) * gain, 0, 255))
    return out


def slab_floor(sheet, rng, grout, joint_fill=None):
    """tiles.build_floor's layout, from a domain's own sheet: (tiles, the slab masks)."""
    out, keeps = [], []
    for i, layout in enumerate(tiles.FLOOR_LAYOUTS):
        ty, tx = divmod(i, 3)
        a = sheet[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].copy()
        keep = np.zeros((T, T), bool)
        for (x0, y0, x1, y1) in layout:
            tiles.slab(a, x0, y0, x1, y1, rng, grout=grout)
            keep[y0:y1, x0:x1] = True
        if joint_fill is not None:
            a[~keep] = joint_fill[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T][~keep]
        else:
            a[~keep] = grout
        out.append(a); keeps.append(keep)
    return out, keeps


def joint_spill(keep, rng, reach=2.5):
    """Where something growing in the joints (moss, frost) spills onto the slab's edge."""
    d = ndi.distance_transform_edt(keep)
    n = noise(rng, 2.0) ** 1.6
    return keep & (d <= 1 + reach * n)


def groove(a, m, depth=0.55, lit=12):
    """A carving: the groove dark, its lower-right lip catching the light."""
    lip = np.clip(np.roll(m, (1, 1), (0, 1)) - m, 0, 1)
    a = a * (1 - m[..., None] * (1 - depth))
    return np.clip(a + lip[..., None] * lit, 0, 255)


def glow(a, core, halo_w=3.0, hot=(255, 150, 50), warm=(170, 40, 12), lips=0.6):
    """A crack lit from below: the lips darkened, a warm halo, a hot core."""
    halo = np.clip(ndi.gaussian_filter(core, halo_w / 2), 0, 1)
    halo = halo / max(1e-6, halo.max())
    a = a * (1 - halo[..., None] * (1 - lips))
    a = lay(a, warm, np.clip(halo * 1.4 - 0.25, 0, 1) * 0.55)
    return lay(a, hot, np.clip(core * 1.2, 0, 1))


def leaves(a, rng, spots, colour=(96, 104, 80), length=7.0, width=2.4):
    """Small narrow leaves (olive leaves), drawn bold for 64 px: a dark rim, a pale side."""
    from PIL import ImageDraw
    S = 4
    for (cx, cy) in spots:
        ang = rng.uniform(0, np.pi)
        im = Image.new('L', (T * S, T * S), 0)
        dx, dy = np.cos(ang) * length / 2 * S, np.sin(ang) * length / 2 * S
        nx, ny = -np.sin(ang) * width / 2 * S, np.cos(ang) * width / 2 * S
        pts = [(cx * S - dx, cy * S - dy), (cx * S + nx, cy * S + ny), (cx * S + dx, cy * S + dy), (cx * S - nx, cy * S - ny)]
        ImageDraw.Draw(im).polygon(pts, fill=255)
        m = ndi.gaussian_filter(np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0, 0.3)
        rim = np.clip(ndi.binary_dilation(m > 0.35) & ~(m > 0.35), 0, 1).astype(np.float32)
        a = lay(a, (34, 36, 28), rim * 0.55)
        tint = np.array(colour, np.float32) * rng.uniform(0.85, 1.1)
        a = lay(a, tint, np.clip(m * 1.3, 0, 1))
        side = np.clip(m - np.roll(m, (1, 1), (0, 1)), 0, 1)
        a = lay(a, tint * 1.3, side * 0.5)
    return a


def root(a, rng, pts, r0=2.6, r1=0.8, bark=(104, 92, 76)):
    """One root coming up out of a joint: thick and knobbly where it leaves the joint,
    tapering, in straight kinked runs (a smooth curve reads as a worm), the stone it broke
    through darkened round its foot."""
    from PIL import ImageDraw
    S = 4
    x, y = pts[0]
    a = a * (1 - (np.clip(r0 * 2.2 - np.sqrt((XX - x) ** 2 + (YY - y) ** 2), 0, r0 * 2.2) / (r0 * 2.2))[..., None] * 0.45)
    line = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for t in np.linspace(0, 1, 12, endpoint=False):
            line.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    line.append(pts[-1])
    im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
    knot = rng.uniform(0, 6)
    for i, (x, y) in enumerate(line):
        r = (r0 + (r1 - r0) * i / (len(line) - 1)) * (1 + 0.22 * np.sin(i * 0.8 + knot)) * S
        d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=255)
    m = np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0
    rim = (ndi.binary_dilation(m > 0.4, iterations=1) & ~(m > 0.4)).astype(np.float32)
    a = lay(a, (28, 26, 22), rim * 0.7)
    a = lay(a, np.array(bark) * (0.85 + 0.3 * noise(rng, 1.0)[..., None]), np.clip(m * 1.4, 0, 1))
    shade = np.clip(m - np.roll(m, (-1, -1), (0, 1)), 0, 1)        # lower-right side in shadow
    lit = np.clip(m - np.roll(m, (1, 1), (0, 1)), 0, 1)
    a = a * (1 - shade[..., None] * 0.35)
    return np.clip(a + lit[..., None] * 22, 0, 255)


def meander(rng, x0, y0, n=4, s=4):
    """A Greek key band: n hooks of side s*2, as one polyline mask."""
    pts = []
    x = x0
    for _ in range(n):
        pts += [(x, y0 + 2 * s), (x, y0), (x + 2 * s, y0), (x + 2 * s, y0 + s), (x + s, y0 + s), (x + s, y0 + 2 * s)]
        x += 2 * s + s
    pts.append((x, y0 + 2 * s))
    from PIL import ImageDraw
    S = 4
    im = Image.new('L', (T * S, T * S), 0)
    ImageDraw.Draw(im).line([(px * S, py * S) for px, py in pts], fill=255, width=int(1.3 * S))
    return np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0


def knotwork(y0, x0=6, x1=58, amp=3.2, period=12.0, width=1.3):
    """A worn interlace band: two strands crossing, drawn as carved grooves; mask 0..1."""
    from PIL import ImageDraw
    S = 4
    im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
    xs = np.linspace(x0, x1, 120)
    for ph in (0, np.pi):
        pts = [(x * S, (y0 + amp * np.sin(2 * np.pi * x / period + ph)) * S) for x in xs]
        d.line(pts, fill=255, width=int(width * S))
    for yy in (y0 - amp - 1.6, y0 + amp + 1.6):                     # the band's two border lines
        d.line([(x0 * S, yy * S), (x1 * S, yy * S)], fill=255, width=int(1.0 * S))
    return np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0


def band_lines(y0, y1, x0, x1, width=1.0):
    """Two straight carved lines framing an ornament band (a meander's border)."""
    from PIL import ImageDraw
    S = 4
    im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
    for y in (y0, y1):
        d.line([(x0 * S, y * S), (x1 * S, y * S)], fill=255, width=int(width * S))
    return np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0


def crack(rng, pts, width=1.0, jitter=1.2):
    """A crack: straight jagged segments (no smooth curve, which reads as a worm), with a
    short fork or two."""
    from PIL import ImageDraw
    S = 4
    im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
    pts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts]
    d.line([(x * S, y * S) for x, y in pts], fill=255, width=max(1, int(round(width * S))))
    for i in rng.choice(range(1, len(pts) - 1), 2, replace=False):
        x, y = pts[i]
        ang = rng.uniform(0, 2 * np.pi); ln = rng.uniform(4, 7)
        d.line([(x * S, y * S), ((x + np.cos(ang) * ln) * S, (y + np.sin(ang) * ln) * S)], fill=170,
               width=max(1, int(round(width * 0.7 * S))))
    return np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0


def ice_skins(water, rng, n=3):
    """Thin pale skins of new ice floating on black water, each wholly inside the tile."""
    from PIL import ImageDraw
    S = 4
    for (cx, cy, r) in ((19, 19, 12), (47, 33, 9), (22, 48, 7))[:n]:
        k = int(rng.integers(5, 8))
        ang = np.sort(rng.uniform(0, 2 * np.pi, k))
        pts = [((cx + np.cos(t) * r * rng.uniform(0.6, 1.0)) * S, (cy + np.sin(t) * r * rng.uniform(0.6, 1.0)) * S) for t in ang]
        im = Image.new('L', (T * S, T * S), 0)
        ImageDraw.Draw(im).polygon(pts, fill=255)
        m = np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0
        rim = np.clip(m - ndi.binary_erosion(m > 0.5, iterations=1), 0, 1)
        water = lay(water, (80, 94, 108), m * 0.42)
        water = lay(water, (150, 168, 186), rim * 0.55)
    return water


def wear(m, rng, keep=0.55, sigma=3.0):
    """Break a carving up as feet and weather would: parts of it are gone."""
    return m * smooth((noise(rng, sigma) - (1 - keep)) / 0.25)


def mortar_mask(a, mortar):
    return np.all(np.abs(a - np.array(mortar, np.float32)) < 0.5, axis=2)


def sprite_cut(pid, size=T):
    """The picked candidate of a domain prop (doors, decals), cut as convert would."""
    import convert
    rf = os.path.join(ROOT, '_genart', 'domains', 'review.json')
    v = (json.load(open(rf, encoding='utf-8')) if os.path.exists(rf) else {}).get(pid) or {}
    if not v.get('pick'):
        return None
    for b in _briefs():
        if b['id'] == pid:
            pic = Image.open(os.path.join(ROOT, '_genart', 'domains', b['_set'], pid, f"c{v['pick']}_pixel.png"))
            spr, _ = convert.to_sprite(pic, b.get('key', 'magenta'), tile=size, lift=float(b.get('lift', 1.0)),
                                       spill=bool(b.get('despill')), stand=b.get('body') != 'item')
            return spr
    return None


def _briefs():
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, 'briefs', 'domains_*.json'))):
        s = os.path.basename(f)[len('domains_'):-5]
        for b in json.load(open(f, encoding='utf-8')):
            b['_set'] = s
            out.append(b)
    return out


def door_tile(pid, floor):
    """A door is drawn the way the base door is: the door object cut at full size and
    set on the theme's floor darkened, so the opening reads as a dark doorway."""
    spr = sprite_cut(pid, T)
    dark = Image.fromarray(np.clip(floor * 0.45, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    if spr is None:
        return None
    dark.alpha_composite(spr, (0, 0))
    return np.asarray(dark.convert('RGB')).astype(np.float32)


# ---------------------------------------------------------------- the four themes
# Brightness targets, against the base set: floor 38-58 (mean 48), wall 99, rock 10, water 20.
def build_temple(p):
    rng = np.random.default_rng(2101)
    sheet = tiles.tone(tiles.big('temple_marble', p['temple_marble'], tiles=4, region=160), sat=0.16)
    sheet = match(sheet, 64, 1.2) * np.array([0.97, 1.0, 0.97])
    moss = match(tiles.tone(tiles.big('moss', p['moss'], tiles=4, region=200), sat=0.75), 30, 1.0) * np.array([0.9, 1.0, 0.8])
    fl, keeps = slab_floor(sheet, rng, grout=(24, 30, 20), joint_fill=moss * 0.8)
    out = {}
    for i, (a, keep) in enumerate(zip(fl, keeps)):
        ty, tx = divmod(i, 3)
        mt = moss[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T]
        a = lay(a, mt, joint_spill(keep, rng, 2.6).astype(np.float32) * 0.9)
        name = 'floor' if i == 0 else f'floor_{i + 1}'
        if name == 'floor_2':        # a crack across the slab, moss in it
            c = path(rng, [(16, 24), (30, 31), (45, 40)], jitter=2.5, width=0.9) * keep
            mossy = np.clip(ndi.gaussian_filter(c, 0.8) * 2.0, 0, 1) * (noise(rng, 1.5) > 0.4)
            a = lay(a, mt * 1.1, mossy * 0.8)
            a = lay(a, (26, 28, 24), np.clip(c * 1.2, 0, 1) * 0.85)
        elif name == 'floor_3':      # a few fallen olive leaves
            a = leaves(a, rng, [(18, 44), (23, 47), (44, 20), (47, 16), (40, 50)])
        elif name == 'floor_4':      # a root breaking up through the joint (layout: joint at y=32 and x=32 below it)
            a = root(a, rng, [(32, 33), (37, 38), (40, 45), (48, 47), (53, 54)], r0=2.6, r1=0.7)
            a = root(a, rng, [(40, 45), (45, 41), (50, 40)], r0=1.1, r1=0.5)
            a = root(a, rng, [(32, 33), (27, 39), (21, 41)], r0=1.6, r1=0.6)
        elif name == 'floor_5':      # a damp patch, darker stone
            m = off_edges(blob(rng, 40, 40, 17, 13, rough=0.4, soft=6), 2)
            a = a * (1 - m[..., None] * 0.28) * (1 - m[..., None] * np.array([0.06, 0.0, 0.03]))
        elif name == 'floor_6':      # a faint worn meander border fragment
            g = np.clip(meander(rng, 5, 45, n=4, s=3.6) + band_lines(41.5, 55.5, 4, 60), 0, 1)
            g = wear(g, rng, keep=0.8, sigma=6.0) * keep
            a = groove(a, g * 0.85, depth=0.6, lit=10)
        out[name] = a
    wall = tiles.build_wall(p['temple_ashlar'], stone='temple_ashlar', grain_mid='temple_marble',
                            grain_pick=p['temple_marble'], mortar=(30, 36, 26), sat=0.25, seed=2111)['wall']
    mm = mortar_mask(wall, (30, 36, 26))
    blocks = ~mm
    wall[blocks] = wall[blocks] * (124 / max(1.0, lum(wall)[blocks].mean()))
    mtile = moss[:T, :T]
    wall[mm] = mtile[mm] * 0.95
    wall = lay(wall, mtile * 1.1, (joint_spill(blocks, rng, 2.6) & (noise(rng, 4.0) > 0.36)).astype(np.float32) * 0.9)
    out['wall'] = wall
    out['rock'] = match(tiles.wrap(tiles.tone(crop('temple_rock', p['temple_rock'], region=400), sat=0.6)), 14, 0.95)
    water = match(tiles.wrap(tiles.tone(crop('temple_water', p['temple_water'], region=320), sat=0.45)), 22, 1.5)
    for (cx, cy, r) in ((19, 20, 6.0), (45, 41, 5.0), (24, 49, 3.6)):         # a few lily leaves on the stagnant pool
        m = np.clip(r + 0.5 - np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2), 0, 1)
        ang = np.arctan2(YY - cy, XX - cx); m = m * (np.abs(((ang - rng.uniform(-3, 3)) + np.pi) % (2 * np.pi) - np.pi) > 0.35)
        rim = (ndi.binary_dilation(m > 0.5) & ~(m > 0.5)).astype(np.float32)
        water = lay(water, (12, 18, 10), rim * 0.8)
        water = lay(water, np.array((46, 66, 34)) * (0.85 + 0.3 * noise(rng, 1.2)[..., None]), m)
        water = lay(water, (78, 98, 56), np.clip(m - np.roll(m, (1, 1), (0, 1)), 0, 1) * 0.7)
    out['water'] = water
    d = door_tile('door_temple', out['floor'])
    if d is not None:
        out['door'] = d
    return out


def build_deep(p):
    rng = np.random.default_rng(4101)
    pk = p['deep_floor']
    tint = np.array([1.03, 0.98, 0.93])
    t = lambda a: match(tiles.tone(a, sat=0.4), 40, 0.85) * tint
    base = t(tiles.wrap(crop('deep_floor', pk)))
    spots = [(120, 110), (640, 140), (150, 620), (640, 640), (400, 80), (90, 400)]
    fl = edge_locked([t(crop('deep_floor', pk, at=s)) for s in spots], base)
    fl[0] = base
    out = {}
    names = ['floor', 'floor_2', 'floor_3', 'floor_4', 'floor_5', 'floor_6']
    for name, a in zip(names, fl):
        if name == 'floor_2':        # a black scorch stain
            m = off_edges(blob(rng, 33, 31, 19, 14, rough=0.7, soft=7), 3)
            a = a * (1 - m[..., None] * 0.48)
            a = lay(a, (70, 66, 60), off_edges(np.clip(m * (1 - m) * 3.2, 0, 1) * (noise(rng, 1.2) > 0.55), 3) * 0.5)
        elif name == 'floor_3':      # a drift of grey ash
            ash = match(tiles.tone(crop('ash', p['ash'], region=300), sat=0.3), 70, 1.2)
            m = off_edges(blob(rng, 30, 36, 20, 12, rough=0.45, soft=5), 3)
            a = lay(a, ash, m * 0.85)
        elif name == 'floor_4':      # pebbles and grit
            for _ in range(8):           # a few pebbles bold enough to read at 64 px
                cx, cy = rng.uniform(12, 52, 2); r = rng.uniform(1.2, 2.2)
                pm = np.clip(r + 0.5 - np.sqrt((XX - cx) ** 2 + ((YY - cy) * 1.2) ** 2), 0, 1)
                c = np.array([86, 74, 60]) * rng.uniform(0.75, 1.15)
                a = lay(a, (26, 20, 16), np.clip(np.roll(pm, (1, 1), (0, 1)) - pm, 0, 1) * 0.8)
                a = lay(a, c, pm)
                a = lay(a, c * 1.35, np.clip(pm - np.roll(pm, (1, 1), (0, 1)), 0, 1) * 0.6)
        elif name == 'floor_5':      # a thin ember crack glowing faintly
            core = crack(rng, [(9, 41), (21, 35), (27, 37), (36, 27), (45, 29), (55, 20)], width=0.9)
            a = glow(a, core * 0.85, halo_w=2.6, hot=(236, 128, 44), warm=(120, 36, 12), lips=0.5)
        elif name == 'floor_6':      # a smooth worn patch
            m = off_edges(blob(rng, 32, 32, 19, 15, rough=0.3, soft=7), 3)
            sm = ndi.gaussian_filter(a, (1.6, 1.6, 0)) + 5
            a = lay(a, sm, m)
        out[name] = a
    wall = tiles.tone(tiles.wrap(crop('deep_wall', p['deep_wall'], region=500)), sat=0.42)
    wall = match(wall, 66, 0.75) * np.array([1.03, 0.97, 0.9])
    soot = ndi.gaussian_filter(rng.random((T, T)), (5.0, 1.1), mode='wrap')            # black soot streaks running down
    soot = smooth((soot - soot.mean()) / max(1e-6, soot.std()) * 0.8 + 0.2)
    out['wall'] = wall * (1 - soot[..., None] * 0.3)
    out['rock'] = match(tiles.tone(tiles.wrap(crop('deep_wall', p['deep_wall'], region=300, at=(80, 600))), sat=0.5), 12, 1.1)
    coins = match(tiles.tone(tiles.wrap(crop('gold_coins', p['gold_coins'], region=380)), sat=1.0), 84, 1.05) * np.array([1.08, 0.97, 0.72])
    gaps = smooth((0.22 - noise(rng, 3.0)) / 0.1)
    coins = lay(coins, base * 0.9, gaps)
    cup = sprite_cut('decal_cup', 26)
    if cup is not None:
        im = Image.fromarray(coins.astype(np.uint8), 'RGB').convert('RGBA')
        c = np.asarray(cup).copy()
        ol = np.all(c[..., :3] == (20, 16, 24), axis=2) & (c[..., 3] > 0)
        c[ol, 3] = 150                                  # a softer rim: the cup lies among the coins
        im.alpha_composite(Image.fromarray(c, 'RGBA'), (30, 8))
        coins = np.asarray(im.convert('RGB')).astype(np.float32)
    out['hoard'] = coins
    d = door_tile('door_deep', out['floor'])
    if d is not None:
        out['door'] = d
    return out


def build_rime(p):
    rng = np.random.default_rng(6101)
    sheet = tiles.tone(tiles.big('rime_flag', p['rime_flag'], tiles=4, region=150), sat=0.35)
    sheet = match(sheet, 38, 0.8) * np.array([0.93, 0.99, 1.1])
    frost = np.array([176, 190, 206], np.float32)
    dust = smooth((tiles.tone(tiles.big('snow', p['snow'], tiles=4, region=200), sat=0.0)[..., 0] / 255.0 - 0.55) / 0.3)
    sheet = lay(sheet, frost * 0.8, dust * 0.16)
    fl, keeps = slab_floor(sheet, rng, grout=(22, 26, 32))
    out = {}
    for i, (a, keep) in enumerate(zip(fl, keeps)):
        name = 'floor' if i == 0 else f'floor_{i + 1}'
        if name != 'floor_6':        # frost gathers along the joints
            dj = ndi.distance_transform_edt(keep)
            rime = np.exp(-dj / 3.2) * (0.55 + 0.45 * noise(rng, 2.0)) * keep      # frost thickest along the joints
            a = lay(a, frost, rime * 0.55)
            a = lay(a, frost, joint_spill(keep, rng, 1.6).astype(np.float32) * 0.4)
            spark = keep & (rng.random((T, T)) < 0.003 + 0.012 * (dj < 5))
            a = lay(a, (206, 218, 232), spark.astype(np.float32) * 0.5)
        if name == 'floor_2':        # a drift of snow in one corner
            snow = match(tiles.tone(crop('snow', p['snow'], region=260), sat=0.5), 162, 0.9)
            m = blob(rng, 54, 54, 13, 10, rough=0.45, soft=5) * keep
            a = lay(a, snow, np.clip(m * 1.05, 0, 1) * 0.92)
        elif name == 'floor_3':      # frost ferns on the stone
            fern = tiles.tone(crop('frost_ferns', p['frost_ferns'], region=360), sat=0.4)
            fl_ = lum(fern); fl_ = (fl_ - fl_.mean()) / max(1.0, fl_.std())
            m = off_edges(blob(rng, 30, 32, 25, 20, rough=0.4, soft=6), 2) * keep
            a = np.clip(a + (np.clip(fl_, 0, 3) * 42 * m)[..., None] * np.array([0.92, 0.98, 1.05]), 0, 255)
        elif name == 'floor_4':      # a crack with ice in it
            c = path(rng, [(6, 22), (24, 30), (40, 26), (58, 40)], jitter=3.0, width=1.6) * keep
            a = lay(a, (18, 20, 26), np.clip(ndi.gaussian_filter(c, 0.6) * 1.6, 0, 1) * 0.8)
            a = lay(a, (150, 176, 196), np.clip(c * 1.5 - 0.5, 0, 1))
        elif name == 'floor_5':      # a carved knotwork fragment, worn
            g = wear(knotwork(30, 7, 57, width=1.5), rng, keep=0.8, sigma=6.0) * keep
            a = groove(a, g * 0.9, depth=0.5, lit=14)
        elif name == 'floor_6':      # bare and swept
            a = ndi.gaussian_filter(a, (0.6, 0.6, 0)) * 0.95
        out[name] = a
    wall = tiles.build_wall(p['rime_wallstone'], stone='rime_wallstone', grain_mid='rime_flag', grain_pick=p['rime_flag'],
                            mortar=(26, 30, 36), sat=0.4, seed=6111)['wall']
    mm = mortar_mask(wall, (26, 30, 36)); blocks = ~mm
    wall[blocks] = wall[blocks] * (96 / max(1.0, lum(wall)[blocks].mean()))
    wall = ndi.gaussian_filter(wall, (0.7, 0.7, 0)) * blocks[..., None] + wall * mm[..., None]
    top = blocks & ~np.roll(blocks, 2, 0)                      # the top rows of every block
    soft = smooth((noise(rng, 3.0) - 0.45) / 0.3) * blocks
    wall = lay(wall, (210, 220, 232), soft * 0.3)
    wall = lay(wall, (222, 230, 240), (top & (noise(rng, 1.2) > 0.25)).astype(np.float32) * 0.6)
    fur = blocks & ~np.roll(blocks, 5, 0)                       # rime furred thick on the upper part of each block
    wall = lay(wall, (200, 212, 228), (fur & (noise(rng, 0.9) > 0.45)).astype(np.float32) * 0.45)
    wall = wall * np.array([0.96, 0.99, 1.05])
    for (x, y) in ((6, 15), (21, 15), (42, 31), (55, 31), (12, 47), (37, 47), (28, 63)):   # icicle tips into the joints
        wall[y % T, x] = (200, 214, 230); wall[(y + 1) % T, x] = (150, 170, 192)
    out['wall'] = wall
    out['rock'] = match(tiles.tone(tiles.wrap(crop('rime_rock', p['rime_rock'], region=300)), sat=0.4), 25, 1.0)
    out['water'] = ice_skins(np.minimum(match(tiles.tone(tiles.wrap(crop('rime_water', 2, region=300, at=(360, 380))), sat=0.5), 17, 1.2), 70), rng)
    d = door_tile('door_rime', out['floor'])
    if d is not None:
        out['door'] = d
    return out


def hex_cells(rng, cols=4, rows=4, jitter=1.6):
    """A repeating field of basalt column tops: (cell id per pixel, distance to the nearest joint)."""
    pts = []
    dx, dy = T / cols, T / rows
    for c in range(cols):
        for r in range(rows):
            pts.append(((c + 0.5) * dx + rng.uniform(-jitter, jitter),
                        (r + 0.5 + (0.5 if c % 2 else 0)) * dy + rng.uniform(-jitter, jitter)))
    pts = np.array(pts) % T
    d = np.full((len(pts), T, T), 1e9, np.float32)
    for i, (px, py) in enumerate(pts):
        ddx = np.abs(XX + 0.5 - px); ddx = np.minimum(ddx, T - ddx)
        ddy = np.abs(YY + 0.5 - py); ddy = np.minimum(ddy, T - ddy)
        d[i] = np.sqrt(ddx ** 2 + ddy ** 2)
    order = np.argsort(d, axis=0)
    d1 = np.take_along_axis(d, order[:1], 0)[0]; d2 = np.take_along_axis(d, order[1:2], 0)[0]
    return order[0], order[1], (d2 - d1) / 2.0


def build_abyss(p):
    rng = np.random.default_rng(8101)
    pk = p['abyss_glass']
    t = lambda a: np.clip(match(tiles.tone(a, sat=0.5), 26, 0.95), 0, 255)
    base = t(tiles.wrap(crop('abyss_glass', pk, region=300)))
    spots = [(150, 150), (580, 160), (160, 560), (560, 560), (360, 120), (120, 360)]
    fl = edge_locked([t(crop('abyss_glass', pk, region=300, at=s)) for s in spots], base)
    fl[0] = base
    names = ['floor', 'floor_2', 'floor_3', 'floor_4', 'floor_5', 'floor_6']
    out = {}
    for name, a in zip(names, fl):
        if name == 'floor_2':        # a drift of pale ash
            ash = match(tiles.tone(crop('ash', p['ash'], region=300, at=(500, 400)), sat=0.25), 66, 0.8)
            a = lay(a, ash, off_edges(blob(rng, 34, 30, 19, 12, rough=0.5, soft=5), 3) * 0.8)
        elif name == 'floor_3':      # a sulphur-yellow crust stain
            s = match(tiles.tone(crop('sulphur', p['sulphur'], region=300), sat=0.7), 72, 1.0)
            a = lay(a, s, off_edges(blob(rng, 30, 34, 16, 13, rough=0.55, soft=4), 3) * 0.85)
        elif name == 'floor_4':      # a wider glowing fissure
            core = crack(rng, [(8, 17), (17, 25), (24, 24), (31, 33), (40, 31), (47, 41), (56, 46)], width=2.2, jitter=1.0)
            a = glow(a, core, halo_w=4.0, hot=(224, 74, 30), warm=(112, 16, 8), lips=0.45)
        elif name == 'floor_5':      # scattered cinders
            for k in range(22):
                cx, cy = rng.uniform(6, 58, 2); r = rng.uniform(0.7, 1.4)
                m = np.clip(r + 0.5 - np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2), 0, 1)
                hot = k % 3 == 0
                a = lay(a, (226, 100, 34) if hot else (14, 11, 11), m)
                if not hot:
                    a = lay(a, (70, 64, 62), np.clip(m - np.roll(m, (1, 1), (0, 1)), 0, 1) * 0.7)
        elif name == 'floor_6':      # dull and smooth
            m = off_edges(blob(rng, 32, 32, 20, 16, rough=0.3, soft=7), 3)
            a = lay(a, ndi.gaussian_filter(a, (1.8, 1.8, 0)) * 0.92, m)
        out[name] = a
    # the wall: the tops of black basalt columns, thin red veins in a few of the joints
    cell, other, dj = hex_cells(rng, cols=4, rows=3, jitter=2.4)
    bas = match(ndi.gaussian_filter(tiles.tone(crop('basalt', p['basalt'], region=380), sat=0.0), (0.7, 0.7, 0)), 46, 1.25) * np.array([1.04, 1.0, 0.98])
    wall = bas.copy()
    shade = rng.uniform(0.82, 1.15, cell.max() + 1)
    wall = wall * shade[cell][..., None]
    gx = np.roll(dj, -1, 1) - np.roll(dj, 1, 1); gy = np.roll(dj, -1, 0) - np.roll(dj, 1, 0)
    rim = smooth(1 - dj / 2.5)                                   # bevel: lit toward the upper left
    wall = np.clip(wall + (rim * np.clip(-(gx + gy), -1, 1) * 20)[..., None], 0, 255)
    joint = np.clip(1.4 - dj, 0, 1)
    wall = lay(wall, (10, 9, 10), joint)
    vein_pairs = {tuple(sorted(pq)) for pq in zip(cell.ravel(), other.ravel())}
    vein_pairs = set(list(sorted(vein_pairs))[::5])
    vein = np.zeros((T, T), np.float32)
    for (i, j) in vein_pairs:
        vein += ((cell == i) & (other == j)) | ((cell == j) & (other == i))
    vein = np.clip(vein, 0, 1) * np.clip(1.0 - dj, 0, 1)
    wall = glow(wall, vein * 0.9, halo_w=1.6, hot=(232, 70, 30), warm=(110, 14, 8), lips=0.8)
    out['wall'] = wall
    out['rock'] = match(tiles.tone(tiles.wrap(crop('obsidian', p['obsidian'], region=300)), sat=0.3), 13, 1.25)
    d = door_tile('door_abyss', out['floor'])
    if d is not None:
        out['door'] = d
    return out


THEMES = {'temple': build_temple, 'deep': build_deep, 'rime': build_rime, 'abyss': build_abyss}
DEFAULT_PICKS = {m: 1 for m in MATERIALS}


def build(picks, only=None):
    tiles.OUT = OUT
    for theme, fn in THEMES.items():
        if only and theme not in only:
            continue
        made = fn(picks)
        d = os.path.join(INSTALL, theme)
        os.makedirs(d, exist_ok=True)
        for name, a in made.items():
            n = 20 if name.startswith(('floor', 'wall', 'rock')) and theme in ('temple', 'rime') else 26
            tiles.quant(np.clip(a, 0, 255), n).save(os.path.join(d, name + '.png'))
        print(theme, sorted(made), {k: round(float(lum(v).mean())) for k, v in made.items()})
    json.dump(picks, open(os.path.join(OUT, 'picks.json'), 'w'), indent=1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['paint', 'build'])
    ap.add_argument('--only', default=''); ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--seed', type=int, default=83000); ap.add_argument('--pick', default='')
    a = ap.parse_args()
    if a.cmd == 'paint':
        paint([x for x in a.only.split(',') if x], a.n, a.seed)
    else:
        picks = dict(DEFAULT_PICKS)
        pf = os.path.join(OUT, 'picks.json')
        if os.path.exists(pf):
            picks.update(json.load(open(pf)))
        picks.update({k: int(v) for k, v in (kv.split('=') for kv in a.pick.split(',') if kv)})
        build(picks, [x for x in a.only.split(',') if x])
