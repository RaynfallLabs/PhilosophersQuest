"""Dungeon Alive fixtures: cut each picked prop for its map layer, and write the install folder.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/domains_<set>.json --n 3 --out _genart/domains/<set> --seed N
    <ComfyUI python> tools/content/genart/domain_sheets.py props <set>        working sheet of every candidate
    <ComfyUI python> tools/content/genart/domain_props.py install              picks -> _genart/domains/install

The briefs are ordinary pipeline briefs (body "object", "shapeless" or a statue's own
`action`) with four more fields that say how the fixture sits on its tile:

  layer   floor  a flat decal on a walkable floor tile, under items and monsters: centred,
                 with a soft half-clear rim instead of the hard outline, so it lies in the
                 floor and does not read as a standing object
          stand  an object standing on the tile: set on the tile's bottom edge, outlined
                 like a monster
          wall   a plaque, hanging or carving over a wall tile, seen face-on: centred, or
                 hung from the top edge with `"anchor": "top"`
  scale   how much of the tile its longest side fills (1.0 = the whole tile)
  stretch "width": the decal is stretched to run edge to edge (a line of embers that
          continues into the next tile)
  theme   the floor it is reviewed on (temple, deep, rime, abyss or base)

and four that fix the cut without a redraw:

  grey    keep this share of every non-green colour's saturation (0.22 turns a statue
          the blue key tinted tan back to grey stone; the moss stays green)
  dim     multiply the colours (a decal that covers its floor must sit at its brightness)
  unkey   [hue_lo, hue_hi, sat_min]: a backdrop corner that drifted to another hue
          (green to yellow, magenta to orange) is turned back into backdrop first
  pieces  how many separate parts it may have; the cut keeps only that many, the biggest

Verdicts live in _genart/domains/review.json: {"<id>": {"pick": 2, "status": "good"|"weak",
"note": "..."}}; "pick": "code" means the fixture is built here (`CODE`) from painted
materials, because every painted round of it failed (a man or a sword in the drift, a
nest for straw, a stone plate under a crack). Two more are built from other picks:
`bronze_grate_open` (the closed grate's spiked bottom bar, hung at the top of the tile)
and `carpet` (a runner cut from the painted carpet material, repeating top to bottom).
A pick of 4 is a good candidate kept from a backup (`<id>_rN`) after the automatic
redraw replaced candidates 1-3.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import convert  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DOM = os.path.join(ROOT, '_genart', 'domains')
INSTALL = os.path.join(DOM, 'install')
T = 64
OUTLINE = convert.OUTLINE
FLOOR_RIM = 105           # alpha of a floor decal's outline: a soft dark edge, not a sticker's black line


def briefs():
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, 'briefs', 'domains_*.json'))):
        s = os.path.basename(f)[len('domains_'):-5]
        for b in json.load(open(f, encoding='utf-8')):
            b['_set'] = s
            out.append(b)
    return out


def _shift_top(a):
    ys = np.where(a[..., 3].any(1))[0]
    if len(ys) and ys[0] > 0:
        a = np.roll(a, -ys[0], 0)
    return a


def _backdrop(w):
    """The painted backdrop's own colour (the median of the picture's rim): the cut reads
    the key hue off the rim, so a pixel set to the pure key colour can survive it."""
    rim = np.concatenate([w[:8].reshape(-1, 3), w[-8:].reshape(-1, 3), w[:, :8].reshape(-1, 3), w[:, -8:].reshape(-1, 3)])
    return np.median(rim, axis=0)


def _keep_pieces(pic, key, n):
    """Keep only the n biggest pieces of the cut-out, painting the rest over with the key
    colour. A painted backdrop drifts (magenta to orange, green to yellow) in a corner and
    the cut keeps that corner as a blot; it is never part of the thing."""
    work, fig, _ = convert.figure_mask(pic, key)
    lab, k = ndi.label(fig)
    if k <= n:
        return pic
    sizes = ndi.sum(fig, lab, range(1, k + 1))
    keep = 1 + np.argsort(sizes)[::-1][:n]
    drop = fig & ~np.isin(lab, keep)
    work = work.copy()
    work[drop] = _backdrop(work)
    return Image.fromarray(work.astype(np.uint8), 'RGB')


def _stretch(pic, key, mode):
    """Stretch the painted thing (before the cut, so the pixels stay square) to fill the
    square ("fill": a barrier that closes the whole tile) or its width ("width": a line
    that runs on into the next tile)."""
    work, fig, _ = convert.figure_mask(pic, key)
    ys, xs = np.where(fig)
    box = Image.fromarray(work[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8), 'RGB')
    m = Image.fromarray((fig[ys.min():ys.max() + 1, xs.min():xs.max() + 1] * 255).astype(np.uint8), 'L')
    W = convert.WORK
    side = int(W * 0.94)
    size = (side, side) if mode == 'fill' else (side, min(side, int(box.height * side / max(1, box.width) * 0.75)))
    canvas = Image.new('RGB', (W, W), convert.KEYS[key])
    canvas.paste(box.resize(size, Image.LANCZOS), ((W - size[0]) // 2, (W - size[1]) // 2), m.resize(size, Image.LANCZOS))
    return canvas


def _grey(a, keep):
    """Turn warm drift to stone: every colour but green (the moss) keeps only `keep` of its
    saturation. A statue painted on the blue key comes out tan, like living skin; the
    stone must be grey in every part."""
    rgb = a[..., :3].astype(np.float32) / 255.0
    h, s, v = convert._hsv(a[..., :3].astype(np.float32))
    green = (h > 0.16) & (h < 0.47) & (s > 0.18)
    s2 = np.where(green, s, s * keep)
    mx = v
    mn = mx * (1 - s2)
    # rebuild from hue/sat/value with the old hue
    out = np.zeros_like(rgb)
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = mn, mx * (1 - s2 * f), mx * (1 - s2 * (1 - f))
    for k, (r_, g_, b_) in enumerate(((mx, t, p), (q, mx, p), (p, mx, t), (p, q, mx), (t, p, mx), (mx, p, q))):
        m = i == k
        out[m] = np.stack([r_[m], g_[m], b_[m]], -1)
    a = a.copy()
    a[..., :3] = np.clip(out * 255, 0, 255).astype(np.uint8)
    return a


def install_cut(b, c):
    """The 64 px RGBA fixture for brief `b`, candidate `c`."""
    pic = Image.open(os.path.join(DOM, b['_set'], b['id'], f'c{c}_pixel.png'))
    layer = b.get('layer', 'stand')
    scale = b.get('scale', 1.0)
    scale = {'tiny': 0.5, 'small': 0.64, 'medium': 0.76, 'large': 0.88, 'huge': 1.0}.get(scale, scale) if isinstance(scale, str) else float(scale)
    key, lift, spill = b.get('key', 'magenta'), float(b.get('lift', 1.0)), bool(b.get('despill'))
    if b.get('stretch'):
        pic = _stretch(pic, key, b['stretch'])
    if b.get('unkey'):
        # the backdrop drifted to another hue in a corner (green to yellow) and the cut kept it:
        # every strongly coloured pixel of that hue band becomes backdrop before the cut
        lo, hi, smin = b['unkey']
        w = np.asarray(pic.convert('RGB')).astype(np.float32)
        h, s, v = convert._hsv(w)
        w[(h >= lo) & (h <= hi) & (s >= smin) & (v > 0.35)] = _backdrop(w)
        pic = Image.fromarray(w.astype(np.uint8), 'RGB')
    if b.get('clean', True):
        pic = _keep_pieces(pic, key, int(b.get('pieces', 1)))
    spr, facts = convert.to_sprite(pic, key, tile=T, scale=scale, stand=(layer == 'stand'), lift=lift, spill=spill)
    a = np.asarray(spr).copy()
    if b.get('grey') is not None:
        a = _grey(a, float(b['grey']))
    if b.get('dim'):
        # a decal that replaces most of its floor (crumbling flagstones) must sit at the floor's brightness
        body = a[..., 3] > 0
        a[body, :3] = np.clip(a[body, :3].astype(np.float32) * float(b['dim']), 0, 255).astype(np.uint8)
    if layer == 'wall' and b.get('anchor') == 'top':
        a = _shift_top(a)
    if layer == 'floor':
        ol = np.all(a[..., :3] == OUTLINE, axis=2) & (a[..., 3] > 0)
        a[ol, 3] = FLOOR_RIM
    return Image.fromarray(a, 'RGBA')


def mech_fail(b, c):
    f = os.path.join(DOM, b['_set'], 'mechanical.json')
    if not os.path.exists(f):
        return []
    return json.load(open(f, encoding='utf-8')).get(f"{b['id']}/c{c}", {}).get('mechanical_fail', [])


def review():
    f = os.path.join(DOM, 'review.json')
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}


def grate_open(closed):
    """The closed grate raised: only its bottom bar and spikes show, at the top of the tile."""
    a = np.asarray(closed).copy()
    ys = np.where(a[..., 3].any(1))[0]
    bottom = ys.max()
    keep = 15                                         # the lowest bar and its spikes
    strip = a[bottom - keep + 1:bottom + 1]
    out = np.zeros_like(a)
    out[0:keep] = strip
    return Image.fromarray(out, 'RGBA')


def carpet():
    """A runner seen from above, repeating top to bottom: the painted carpet material cut to
    a strip, faded gold borders drawn down both sides, the sides of the tile left clear."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    pick = json.load(open(os.path.join(dt.OUT, 'picks.json'))).get('carpet', 1)
    src = os.path.join(dt.OUT, 'materials', 'carpet', f'c{pick}.png')
    if not os.path.exists(src):
        return None
    w = 42
    field = dt.crop('carpet', pick, region=420, out=T)
    field = tiles.tone(field, sat=0.62)
    field = dt.match(field, 46, 1.25)
    # repeat top to bottom: cross-fade with itself shifted half a tile, along y only
    r = np.roll(field, T // 2, axis=0)
    cy = (0.5 - 0.5 * np.cos(2 * np.pi * (np.arange(T) + 0.5) / T)) ** 0.6
    field = field * cy[:, None, None] + r * (1 - cy[:, None, None])
    a = np.zeros((T, T, 4), np.float32)
    x0 = (T - w) // 2
    a[:, x0:x0 + w, :3] = field[:, x0:x0 + w]
    a[:, x0:x0 + w, 3] = 255
    gold, dark = np.array([150, 116, 52]), np.array([46, 22, 16])
    for xx in (x0 + 2, x0 + w - 5):
        a[:, xx:xx + 3, :3] = gold * (0.85 + 0.25 * dt.noise(np.random.default_rng(xx), 1.0)[:, :3, None])
    for xx in (x0, x0 + w - 1, x0 + 1, x0 + w - 2):
        a[:, xx, :3] = dark if xx in (x0, x0 + w - 1) else a[:, xx, :3] * 0.8
    wear = dt.smooth((dt.noise(np.random.default_rng(5), 3.0) - 0.6) / 0.25)        # worn bare in places
    a[..., :3] = a[..., :3] * (1 - wear[..., None] * 0.45) + np.array([66, 52, 42]) * wear[..., None] * 0.45
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def _decal(rgb, alpha):
    a = np.zeros((T, T, 4), np.float32)
    a[..., :3] = rgb
    a[..., 3] = np.clip(alpha, 0, 1) * 255
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def fire_out():
    """A line of dying embers and black ash, running edge to edge so a row of them is one
    line across the floor. Built in code: three painted rounds drew a black hairbrush or a
    crow, never a line of ash."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(31)
    ash = dt.match(tiles.tone(dt.crop('ash', 1, region=360, at=(300, 300)), sat=0.15), 46, 1.4)
    yy, xx = dt.YY, dt.XX
    edge = 8 + 4 * (dt.noise(rng, 3.0) - 0.5) * 2
    band = dt.smooth((edge - np.abs(yy - 32 - 3 * np.sin(xx / 64 * 2 * np.pi))) / 2.5)
    rgb = ash.copy()
    for _ in range(10):                                   # charred lumps
        cx, cy = rng.uniform(2, 62), 32 + rng.uniform(-4, 4); r = rng.uniform(1.6, 3.0)
        m = np.clip(r + 0.5 - np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.3) ** 2), 0, 1)
        rgb = dt.lay(rgb, (18, 15, 14), m)
        rgb = dt.lay(rgb, (64, 58, 54), np.clip(m - np.roll(m, (1, 1), (0, 1)), 0, 1) * 0.6)
    for _ in range(9):                                    # dull embers among them
        cx, cy = rng.uniform(4, 60), 32 + rng.uniform(-3, 3)
        core = np.clip(1.2 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2), 0, 1)
        rgb = dt.glow(rgb, core, halo_w=2.0, hot=(232, 118, 40), warm=(120, 34, 10), lips=0.85)
    alpha = band * (0.78 + 0.22 * dt.noise(rng, 1.0))
    return _decal(rgb, alpha)


def snow_slush():
    """A thin grey puddle of half-melted slush: wet dark rim, grey slush, a few lumps of old
    snow. Built in code: every painted draft put a man lying in it."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(41)
    sl = dt.match(tiles.tone(dt.crop('snow', 1, region=300, at=(200, 500)), sat=0.25), 96, 0.7) * np.array([0.94, 0.98, 1.04])
    m = dt.blob(rng, 32, 33, 25, 16, rough=0.35, soft=3)
    rim = np.clip(m * (1 - m) * 4, 0, 1)
    rgb = dt.lay(sl, (54, 60, 68), rim * 0.85)
    for (cx, cy, r) in ((22, 30, 3.6), (38, 36, 3.0), (31, 26, 2.4), (44, 29, 2.2)):
        lm = np.clip(r + 0.5 - np.sqrt((dt.XX - cx) ** 2 + ((dt.YY - cy) * 1.25) ** 2), 0, 1)
        rgb = dt.lay(rgb, (150, 158, 168), lm)
        rgb = dt.lay(rgb, (184, 192, 202), np.clip(lm - np.roll(lm, (1, 1), (0, 1)), 0, 1) * 0.8)
        rgb = dt.lay(rgb, (82, 88, 98), np.clip(np.roll(lm, (1, 1), (0, 1)) - lm, 0, 1) * 0.6)
    return _decal(rgb, np.clip(m * 1.15, 0, 1) * 0.92)


def ash_drift():
    """A low drift of pale grey ash with soft ripples. Built in code: every painted draft
    put a man lying in the drift."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(51)
    ash = dt.match(tiles.tone(dt.crop('ash', 1, region=300, at=(120, 160)), sat=0.2), 86, 1.6)
    m = dt.blob(rng, 32, 33, 25, 15, rough=0.4, soft=4)
    rgb = dt.lay(ash, (70, 66, 62), np.clip(m * (1 - m) * 3.5, 0, 1) * 0.5)
    for _ in range(6):
        cx, cy = rng.uniform(14, 50), rng.uniform(24, 42)
        cm = np.clip(1.1 - np.sqrt((dt.XX - cx) ** 2 + (dt.YY - cy) ** 2), 0, 1)
        rgb = dt.lay(rgb, (24, 20, 20), cm)
    return _decal(rgb, np.clip(m * 1.1, 0, 1) * 0.8)


def _crack_decal(pts, width, hot, warm, seed, lips=(20, 16, 16), halo=3.0):
    """A glowing crack lying in the floor: dark scorched lips, a warm halo, a hot core; the
    rest of the tile left clear so it sits in any floor."""
    import domain_tiles as dt
    rng = np.random.default_rng(seed)
    core = dt.crack(rng, pts, width=width, jitter=1.0)
    lip = np.clip(ndi.gaussian_filter(core, halo / 2) * 3.0, 0, 1)
    rgb = np.zeros((T, T, 3), np.float32) + np.array(lips, np.float32)
    rgb = dt.lay(rgb, warm, np.clip(ndi.gaussian_filter(core, 1.0) * 2.2, 0, 1))
    rgb = dt.lay(rgb, hot, np.clip(core * 1.3, 0, 1))
    alpha = np.maximum(lip * 0.75, np.clip(core * 1.5, 0, 1))
    return _decal(rgb, alpha)


def ember_crack():
    """A jagged crack glowing orange from heat below. Code: the painted ones were lava bricks."""
    return _crack_decal([(6, 38), (16, 31), (23, 34), (31, 24), (40, 27), (47, 19), (58, 23)], 1.6,
                        (250, 168, 60), (196, 76, 20), 61)


def glow_fissure():
    """A wide fissure glowing deep red. Code: the painted ones were slabs with a red cross."""
    return _crack_decal([(5, 22), (15, 28), (22, 26), (30, 35), (38, 33), (46, 42), (59, 44)], 3.4,
                        (236, 74, 40), (140, 18, 10), 71, lips=(10, 8, 9), halo=4.0)


def scorch_mark():
    """A black burn in a splash shape, ash at its ragged edges. Code: the painted ones were
    black starbursts with a glinting cross in the middle."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(81)
    ang = np.arctan2(dt.YY - 32, dt.XX - 32)
    rad = np.sqrt((dt.XX - 32) ** 2 + (dt.YY - 32) ** 2)
    reach = 18 + 2.5 * np.sin(ang * 3 + 0.4) * np.sin(ang * 2 + 1.3) + 7 * (dt.noise(rng, 1.6) - 0.5)
    m = dt.smooth((reach - rad) / 9)
    ash = dt.match(tiles.tone(dt.crop('ash', 1, region=300, at=(500, 200)), sat=0.1), 70, 1.2)
    rgb = dt.lay(ash, (12, 10, 10), np.clip(m * 1.6, 0, 1))
    alpha = np.clip(m * 1.2, 0, 1) * (0.55 + 0.4 * m)
    return _decal(rgb, alpha)


def brimstone():
    """A small bubbling pool of yellow sulphur with a cracked crust rim. Code: the painted ones
    were round yellow coins with a cross on them."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(91)
    crust = dt.match(tiles.tone(dt.crop('sulphur', 1, region=260, at=(380, 380)), sat=0.75), 120, 1.0)
    pool_c = np.array([196, 170, 52], np.float32)
    m = dt.blob(rng, 32, 33, 21, 14, rough=0.4, soft=2.5)
    inner = dt.blob(rng, 32, 33, 14, 9, rough=0.3, soft=2.0)
    rgb = dt.lay(crust, (52, 42, 22), np.clip(m * (1 - m) * 4, 0, 1) * 0.8)
    rgb = dt.lay(rgb, pool_c * (0.85 + 0.2 * dt.noise(rng, 1.5)[..., None]), inner)
    for (cx, cy, r) in ((27, 31, 1.8), (35, 35, 1.4), (38, 29, 1.1), (30, 37, 1.0)):
        bm = np.clip(r + 0.5 - np.sqrt((dt.XX - cx) ** 2 + (dt.YY - cy) ** 2), 0, 1)
        rim = np.clip(bm - np.clip(r - 0.4 - np.sqrt((dt.XX - cx) ** 2 + (dt.YY - cy) ** 2), 0, 1), 0, 1)
        rgb = dt.lay(rgb, (238, 224, 120), rim * 0.9)
    return _decal(rgb, np.clip(m * 1.2, 0, 1))


def snow_drift():
    """A low drift of white snow, soft humps with blue shadows. Code: the painted drifts all
    had a sword or a cross stuck in them."""
    import domain_tiles as dt, tiles
    tiles.OUT = dt.OUT
    rng = np.random.default_rng(101)
    snow = dt.match(tiles.tone(dt.crop('snow', 1, region=420, at=(200, 200)), sat=0.55), 160, 1.5)
    m = dt.blob(rng, 32, 34, 25, 12, rough=0.55, soft=4)
    rgb = snow * np.array([0.95, 0.98, 1.06])                                # the material's own wind ripples
    rim = np.clip(m * (1 - m) * 4, 0, 1)
    rgb = dt.lay(rgb, (120, 134, 156), rim * 0.45)
    return _decal(rgb, np.clip(m * 1.15, 0, 1) * 0.92)


def smoke_vent():
    """A ragged crack in the black glass with a low curl of smoke rising from it. The crack is
    drawn in code so the floor shows round it; the smoke is cut from the painted vent
    (decor_b/smoke_vent c2), whose stone slab read as a plate lying on the floor."""
    import domain_tiles as dt
    b = {x['id']: x for x in briefs()}['smoke_vent']
    spr = np.asarray(install_cut(b, 2)).astype(np.float32)
    l = dt.lum(spr[..., :3])
    smoke = (spr[..., 3] > 0) & (l > 62) & (np.arange(T)[:, None] < 44)
    smoke = ndi.binary_closing(smoke, iterations=1) & (spr[..., 3] > 0)
    lab, k = ndi.label(smoke)
    if k > 1:
        sizes = ndi.sum(smoke, lab, range(1, k + 1))
        smoke = lab == 1 + int(np.argmax(sizes))
    ys, xs = np.where(smoke)
    base = _crack_decal([(14, 47), (22, 43), (28, 45), (35, 40), (42, 42), (50, 38)], 1.5,
                        (150, 40, 26), (60, 14, 10), 121, lips=(8, 7, 8), halo=3.0)
    out = np.asarray(base).astype(np.float32)
    # stand the smoke on the crack: its foot at the crack's middle
    dy = 41 - ys.max(); dx = 32 - int(round(xs.mean()))
    sm = np.zeros((T, T), bool); sm[np.clip(ys + dy, 0, T - 1), np.clip(xs + dx, 0, T - 1)] = True
    src = np.zeros((T, T, 3), np.float32); src[np.clip(ys + dy, 0, T - 1), np.clip(xs + dx, 0, T - 1)] = spr[ys, xs, :3]
    edge = sm & ~ndi.binary_erosion(sm)
    out[sm, :3] = src[sm]
    out[sm, 3] = np.where(edge[sm], 170, 235)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def straw():
    """Trampled dirty straw bedding: many short pale stalks lying every way in a rough patch,
    dirtier toward the middle. Code: the painted straw came out as a bird's nest."""
    from PIL import ImageDraw
    import domain_tiles as dt
    rng = np.random.default_rng(131)
    S = 4
    patch = dt.blob(rng, 32, 33, 26, 18, rough=0.45, soft=3)
    rgb = np.zeros((T, T, 3), np.float32); alpha = np.zeros((T, T), np.float32)
    for layer, (n, col, w) in enumerate(((140, (96, 78, 46), 1.1), (110, (150, 126, 74), 1.0), (60, (186, 160, 98), 0.9))):
        im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
        for _ in range(n):
            x, y = rng.uniform(6, 58), rng.uniform(12, 54)
            if patch[int(y), int(x)] < 0.5:
                continue
            ang = rng.uniform(0, np.pi); ln = rng.uniform(4, 9)
            d.line([((x - np.cos(ang) * ln / 2) * S, (y - np.sin(ang) * ln / 2) * S),
                    ((x + np.cos(ang) * ln / 2) * S, (y + np.sin(ang) * ln / 2) * S)], fill=255, width=int(w * S))
        m = np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0
        m = np.clip(m * 1.6, 0, 1)
        rgb = dt.lay(rgb, np.array(col) * (0.85 + 0.3 * dt.noise(rng, 1.0)[..., None]), m)
        alpha = np.maximum(alpha, m)
    dirt = dt.blob(rng, 32, 34, 12, 8, rough=0.5, soft=5)
    rgb = rgb * (1 - dirt[..., None] * 0.4)
    return _decal(rgb, alpha * 0.95)


def honey_drip():
    """A small puddle of honey, glossy amber, irregular. Code: the painted ones were copper
    coins or bowls."""
    import domain_tiles as dt
    rng = np.random.default_rng(141)
    m = dt.blob(rng, 32, 34, 12, 8, rough=0.35, soft=2)
    m = np.maximum(m, dt.blob(rng, 40, 38, 5, 4, rough=0.3, soft=1.5))
    inner = dt.blob(rng, 31, 33, 8, 5, rough=0.3, soft=2.5)
    rgb = np.zeros((T, T, 3), np.float32) + np.array([150, 84, 18])
    rgb = dt.lay(rgb, (204, 136, 34), inner)
    rgb = dt.lay(rgb, (96, 50, 12), np.clip(m * (1 - m) * 4, 0, 1) * 0.6)
    gloss = np.clip(1.5 - np.sqrt(((dt.XX - 28) / 3.0) ** 2 + ((dt.YY - 31) / 1.4) ** 2), 0, 1)
    rgb = dt.lay(rgb, (250, 222, 150), gloss * 0.9)
    return _decal(rgb, np.clip(m * 1.2, 0, 1) * 0.95)


def soul_sigil():
    """A faint ring burned into the black glass: two thin rings and twelve short angular
    marks round the outer one, dull violet-red. Code: the painted ones were bright sun
    emblems with the backdrop left in their middle. The marks are strokes, never letters."""
    from PIL import ImageDraw
    import domain_tiles as dt
    S = 4
    im = Image.new('L', (T * S, T * S), 0); d = ImageDraw.Draw(im)
    c, r1, r2 = 32 * S, 21 * S, 15 * S
    d.ellipse((c - r1, c - r1, c + r1, c + r1), outline=255, width=int(1.3 * S))
    d.ellipse((c - r2, c - r2, c + r2, c + r2), outline=200, width=int(1.0 * S))
    for k in range(12):
        a0 = 2 * np.pi * k / 12
        p = [(c + np.cos(a0) * (r1 + 2 * S), c + np.sin(a0) * (r1 + 2 * S)),
             (c + np.cos(a0 + 0.12) * (r1 + 6 * S), c + np.sin(a0 + 0.12) * (r1 + 6 * S)),
             (c + np.cos(a0 - 0.05) * (r1 + 8 * S), c + np.sin(a0 - 0.05) * (r1 + 8 * S))]
        d.line(p, fill=230, width=int(1.1 * S))
    core = np.asarray(im.resize((T, T), Image.BOX)).astype(np.float32) / 255.0
    halo = np.clip(ndi.gaussian_filter(core, 1.4) * 2.2, 0, 1)
    rgb = np.zeros((T, T, 3), np.float32) + np.array([90, 16, 40], np.float32)
    rgb = dt.lay(rgb, (196, 52, 112), np.clip(core * 1.4, 0, 1))
    alpha = np.maximum(halo * 0.45, np.clip(core * 1.3, 0, 1) * 0.85)
    return _decal(rgb, alpha)


def olive_leaves():
    """A small drift of dry olive leaves, drawn with the same leaf as the temple's floor_3.
    Code: two painted rounds drew a rosette or a sprig, never loose leaves."""
    import domain_tiles as dt
    spots = [(24, 30), (29, 27), (33, 33), (38, 29), (27, 36), (41, 35), (35, 25), (31, 39), (22, 34)]
    draw = lambda base: dt.leaves(np.full((T, T, 3), base, np.float32), np.random.default_rng(111), spots,
                                  colour=(112, 120, 92), length=8.0, width=2.6)
    black, white = draw(0.0), draw(255.0)
    alpha = np.clip(1 - (white - black).mean(2) / 255.0, 0, 1)
    rgb = black / np.maximum(alpha[..., None], 1e-3)
    return _decal(rgb, alpha)


CODE = {'fire_out': fire_out, 'soul_sigil': soul_sigil, 'olive_leaves': olive_leaves, 'smoke_vent': smoke_vent, 'straw': straw, 'honey_drip': honey_drip, 'snow_slush': snow_slush, 'ash_drift': ash_drift, 'ember_crack': ember_crack,
        'glow_fissure': glow_fissure, 'scorch_mark': scorch_mark, 'brimstone': brimstone, 'snow_drift': snow_drift}


def install(dry=False):
    """Write each picked fixture, then the manifest (props and theme tiles together)."""
    art = json.load(open(os.path.join(ROOT, '_alive_research', 'art_list.json'), encoding='utf-8'))
    rv = review()
    by_id = {b['id']: b for b in briefs()}
    fx = os.path.join(INSTALL, 'fixtures')
    os.makedirs(fx, exist_ok=True)
    manifest = []
    made_img = {}
    for p in art['props']:
        pid = p['id']
        v = rv.get(pid, {})
        img = None
        if v.get('pick') == 'code' and pid in CODE:
            img = CODE[pid]()
        elif pid in by_id and v.get('pick'):
            img = install_cut(by_id[pid], v['pick'])
        elif pid == 'bronze_grate_open' and 'bronze_grate' in made_img:
            img = grate_open(made_img['bronze_grate'])
        elif pid == 'carpet':
            img = carpet()
        if img is not None:
            made_img[pid] = img
            if not dry:
                img.save(os.path.join(fx, pid + '.png'))
        status = v.get('status', 'good' if img is not None else 'missing') if img is not None else 'missing'
        made = ('code from painted materials' if v.get('pick') == 'code' and pid not in ('bronze_grate_open', 'smoke_vent')
                else 'code from a painted pick' if v.get('pick') == 'code' else f"painted, candidate c{v.get('pick')}")
        manifest.append({'id': pid, 'kind': 'prop', 'layer': p['layer'], 'set': p['set'], 'p': p['p'],
                         'status': status, 'made': made if img is not None else '',
                         'note': v.get('note', '' if img is not None else 'not drawn')})
    tv = rv.get('_themes', {})
    for theme, t in art['themes'].items():
        for f in t['tiles']:
            path = os.path.join(INSTALL, 'themes', theme, f)
            k = f'{theme}/{f}'
            have = os.path.exists(path)
            e = tv.get(k, {})
            manifest.append({'id': k, 'kind': 'tile', 'layer': 'tile', 'status': e.get('status', 'good') if have else 'missing',
                             'made': 'painted materials cut in code (domain_tiles.py)' if have else '',
                             'note': e.get('note', '') if have else 'not built'})
    if not dry:
        json.dump(manifest, open(os.path.join(INSTALL, 'manifest.json'), 'w', encoding='utf-8'), indent=1)
    counts = {}
    for m in manifest:
        counts.setdefault(m['kind'], {}).setdefault(m['status'], 0)
        counts[m['kind']][m['status']] += 1
    print(counts)
    return manifest


_FIG = ("One single figure only, {whole}, seen from far enough away that the figure is small in the picture")
_LIT = "The figure itself is clearly and brightly lit"
_HELD = ("Anything it holds is drawn bold, sturdy and a little larger than life, with thick shafts, limbs and blades, "
         "and is held out clear of the body so its whole shape can be seen against the backdrop. ")


def patch_pipeline():
    """pipeline.py's fixed wording says "one single figure only" and "the figure itself is lit".
    For a thing with nobody in it (fire, snow, slush, a puddle) the model took that as a
    person and put a man in all of round 1's fire, snow and slush. Objects and shapeless
    things get "one single thing only, with no person in it" instead; statues (no body)
    keep the figure wording."""
    import pipeline
    assert _FIG in pipeline.DRAFT and _LIT in pipeline.DRAFT and _HELD in pipeline.DRAFT, 'pipeline.DRAFT changed: update domain_props.py'
    orig = pipeline.prompts

    def prompts(b):
        dp, dn, pp, pn = orig(b)
        if b.get('body') in ('object', 'shapeless', 'item'):
            whole = pipeline.WHOLE[b['body']]
            dp = dp.replace(_FIG.format(whole=whole),
                            f"One single thing only, {whole}, with no person, no creature and no figure anywhere in it, "
                            "on it or near it, seen from far enough away that it is small in the picture")
            dp = dp.replace(_LIT, 'The thing itself is clearly and brightly lit')
            # "anything it holds ... thick shafts, limbs and blades" put a sword in a snow drift,
            # a row of icicles and a smoking crack once the man was gone
            armed = any(w in (b['what'] + ' ' + b.get('holds', '')).lower()
                        for w in ('sword', 'spear', 'axe', 'pick', 'knife', 'ladle', 'weapon', 'tool', 'dividers', 'quill'))
            dp = dp.replace(_HELD, 'Nothing else lies on it or near it. ' if armed else
                            'Nothing lies on it, nothing is stuck in it and nothing stands in it: no sword, no blade, '
                            'no weapon, no tool, no cross. ')
            pp = pp.replace('single figure,', 'single object, no people,')
            extra = ', person, man, woman, human figure, body, warrior, silhouette of a man'
            if not armed:
                extra += ', sword, dagger, blade, weapon stuck in it, cross'
            dn, pn = dn + extra, pn + extra
        return dp, dn, pp, pn
    pipeline.prompts = prompts
    return pipeline


if __name__ == '__main__':
    if sys.argv[1] == 'install':
        install(dry='--dry' in sys.argv)
    elif sys.argv[1] == 'draw':
        # domain_props.py draw <briefs> [pipeline.py's own arguments]
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        patch_pipeline().main()
