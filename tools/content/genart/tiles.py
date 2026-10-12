"""Dungeon map tiles: painted materials, built into tiles that repeat cleanly.

    <ComfyUI python> tools/content/genart/tiles.py paint  [--only id,id] [--n 3] [--seed N]
    <ComfyUI python> tools/content/genart/tiles.py build  [--pick id=2,id=3]
    <ComfyUI python> tools/content/genart/tiles.py sheet

A map tile is not a creature: it has no outline, fills its whole square, and sits
next to copies of itself. A model will not paint a picture whose left edge meets
its right, so the work is split:

  paint   the model paints each MATERIAL as a flat texture seen from above
          (worn flagstone, dressed wall stone, cave rock, water, lava, ice),
          through the same two passes as the monsters so the look matches.
  build   code cuts the material into tiles: slabs with grout for the floor,
          staggered courses for the wall, and a wrapped cross-fade for the
          materials with no joints. Joints sit on the tile's edges, so any tile
          can meet any other.

Output: _genart/tiles/materials/<id>/c<N>.png, _genart/tiles/out/<tile>.png (64 px),
and _genart/tiles/TILES.png showing each tile laid out as a map.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comfy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, '_genart', 'tiles')
T = 64

LEAD = ("A classic fantasy oil painting, looking straight down from directly above at {what} "
        "It fills the whole picture from edge to edge like a texture sample: the same surface everywhere, "
        "no objects lying on it, no border, no frame, no horizon, no walls, no perspective. "
        "Flat even light from the upper left, soft shallow shadows only. Painted like the scenery in a 1980s "
        "fantasy roleplaying rulebook: weathered, worn, serious, rich but muted colours. {colours}")
NEG = ("face, carving, statue, relief, sculpture, rings, concentric circles, bright centre, dark rim, objects, creatures, people, furniture, border, frame, vignette, horizon, perspective, side view, text, "
       "photo, 3d render, cartoon, bright candy colours, strong cast shadows, lens blur")
PIX = ("detailed pixel art texture, seen from directly above, {short}, weathered, muted colours, even light, "
       "fills the whole picture")
PIX_NEG = "face, carving, statue, concentric rings, bright centre, objects, creatures, border, frame, text, photograph, 3d render, cartoon, perspective, blur"

MATERIALS = {
    'floor_stone': dict(
        what="the surface of one single huge worn flagstone in a dungeon floor: grey-brown stone with fine pits, faint "
             "scratches, a few hairline cracks and darker stains. One unbroken slab: no joints and no gaps anywhere.",
        colours="Dark grey-brown stone, a little warm, low contrast.",
        short="worn dark grey-brown dungeon flagstone surface with hairline cracks, no joints"),
    'wall_stone': dict(
        what="a completely flat, blank slab of pale grey castle limestone, like a mason's sample: only the bare cut "
             "surface of the rock, with fine chisel marks, small chips and weather stains. It is one unbroken plain "
             "surface: no joints, no mortar, no bricks, and nothing carved on it.",
        colours="Pale cool grey stone with slightly warmer and darker patches.",
        short="flat blank pale grey limestone surface with fine chisel marks, no joints, nothing carved"),
    'rock': dict(
        what="rough natural cave rock, untouched by tools: lumpy, cracked, with deep black crevices between rounded bulges.",
        colours="Very dark brown-black rock with dull grey highlights on the bulges.",
        short="rough very dark brown-black natural cave rock with crevices"),
    'water': dict(
        what="the surface of deep, dark underground water, the same everywhere: many small irregular wavelets running "
             "across the whole picture in no pattern, with faint paler glints. There is no centre and no rings: "
             "nothing has dropped into it, and no part of the picture differs from any other.",
        colours="Deep blue-green, nearly black in the troughs, with dull teal ripple highlights.",
        short="deep dark blue-green water surface, small irregular wavelets all over, no rings, no centre"),
    'lava': dict(
        what="the surface of a lake of lava, the same everywhere: a skin of black cooling crust broken into many "
             "irregular plates of about the same size, with bright orange molten rock glowing in the cracks between "
             "them. The plates and cracks cover the whole picture evenly: there is no centre, no bright middle and "
             "no dark rim, and no part of the picture differs from any other.",
        colours="Black and dark red crust, bright orange cracks, yellow-white at the hottest points.",
        short="lava surface, black crust plates with orange glowing cracks spread evenly all over, no centre"),
    'ice': dict(
        what="a sheet of thick old ice over dark water: pale blue-white ice with long white cracks, frosted patches and "
             "darker blue where the ice is clear.",
        colours="Pale blue-white with darker glacier-blue patches and white crack lines.",
        short="thick pale blue-white ice sheet with long white cracks and frosted patches"),
}


def paint(only, n, seed):
    if not comfy.running():
        raise SystemExit('ComfyUI is not running on 127.0.0.1:8188')
    drafts, second = [], []
    for mid, m in MATERIALS.items():
        if only and mid not in only:
            continue
        for c in range(1, n + 1):
            s = seed + c * 31 + sum(map(ord, mid))
            d = os.path.join(OUT, 'materials', mid, f'c{c}_draft.png')
            drafts.append((comfy.draft_workflow(LEAD.format(**m), NEG, s), d))
            second.append((mid, c, d, s, m))
    print('drafts', len(drafts)); sys.stdout.flush()
    print(comfy.run(drafts) or 'ok')
    jobs = []
    for mid, c, d, s, m in second:
        name = comfy.stage_input(d, f'genart_tile_{mid}_c{c}.png')
        jobs.append((comfy.pixel_workflow(name, PIX.format(**m), PIX_NEG, s, 0.42),
                     os.path.join(OUT, 'materials', mid, f'c{c}.png')))
    print(comfy.run(jobs) or 'ok')


# ---------------------------------------------------------------- building
def material(mid, pick, region=256, at=(384, 384)):
    """A square of the painted material, shrunk so `region` source pixels make one tile."""
    im = Image.open(os.path.join(OUT, 'materials', mid, f'c{pick}.png')).convert('RGB')
    x, y = at
    return np.asarray(im.crop((x, y, x + region, y + region)).resize((T, T), Image.BOX)).astype(np.float32)


def big(mid, pick, tiles=4, region=256):
    """A larger sheet of the material (tiles x tiles), for cutting several different tiles from."""
    im = Image.open(os.path.join(OUT, 'materials', mid, f'c{pick}.png')).convert('RGB')
    side = region * tiles
    off = (im.width - side) // 2
    return np.asarray(im.crop((off, off, off + side, off + side)).resize((T * tiles, T * tiles), Image.BOX)).astype(np.float32)


def wrap(a):
    """Make a texture repeat: cross-fade it with itself shifted by half a tile, so the
    original edges (which do not meet) are replaced by its own middle (which does)."""
    n = a.shape[0]
    r = np.roll(a, (n // 2, n // 2), axis=(0, 1))
    d = np.minimum(np.arange(n), n - 1 - np.arange(n)) / (n / 2.0)
    w = np.clip((np.minimum.outer(d, d) - 0.15) / 0.45, 0, 1)
    w = (w * w * (3 - 2 * w))[..., None]
    out = a * w + r * (1 - w)
    # the fade lowers contrast where the two halves mix: put it back
    m = out.mean((0, 1), keepdims=True)
    return np.clip(m + (out - m) * (1 + 0.25 * (1 - w)), 0, 255)


def tone(a, gain=1.0, lift=0.0, sat=1.0):
    g = a.mean(2, keepdims=True)
    return np.clip((g + (a - g) * sat) * gain + lift, 0, 255)


def quant(a, colours=24):
    im = Image.fromarray(a.astype(np.uint8), 'RGB').quantize(colours, method=Image.MEDIANCUT, kmeans=4)
    return im.convert('RGB')


def slab(a, x0, y0, x1, y1, rng, grout=(26, 24, 26)):
    """Shade one slab of stone inside `a` in place: its own slight tone, a lit top-left
    edge, a shaded bottom-right edge, and a dark joint all round."""
    s = a[y0:y1, x0:x1]
    s *= rng.uniform(0.90, 1.08)
    s[0, :] = s[0, :] * 1.16 + 6; s[:, 0] = s[:, 0] * 1.12 + 4
    s[-1, :] *= 0.78; s[:, -1] *= 0.82
    a[y0:y1, x0:x1] = s
    for (yy, xx) in ((slice(y0 - 1, y0), slice(x0 - 1, x1 + 1)), (slice(y1, y1 + 1), slice(x0 - 1, x1 + 1)),
                     (slice(y0 - 1, y1 + 1), slice(x0 - 1, x0)), (slice(y0 - 1, y1 + 1), slice(x1, x1 + 1))):
        try:
            a[yy, xx] = grout
        except Exception:
            pass


FLOOR_PICK = [1]
FLOOR_LAYOUTS = [                       # slabs as (x0, y0, x1, y1) inside a 64 px tile; joints are 1 px each side
    [(1, 1, 63, 63)],
    [(1, 1, 63, 63)],
    [(1, 1, 31, 31), (33, 1, 63, 31), (1, 33, 31, 63), (33, 33, 63, 63)],
    [(1, 1, 63, 31), (1, 33, 31, 63), (33, 33, 63, 63)],
    [(1, 1, 31, 63), (33, 1, 63, 31), (33, 33, 63, 63)],
    [(1, 1, 63, 63)],
]


def build_floor(pick):
    sheet = tone(big('floor_stone', pick, tiles=4, region=160), gain=0.66, sat=0.45) * np.array([0.97, 0.99, 1.06])
    rng = np.random.default_rng(7)
    tiles = {}
    for i, layout in enumerate(FLOOR_LAYOUTS):
        ty, tx = divmod(i, 3)
        a = sheet[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].copy()
        a[:] = np.where(True, a, a)
        frame = np.full_like(a, 0); frame[:] = (26, 24, 26)
        keep = np.zeros((T, T), bool)
        for (x0, y0, x1, y1) in layout:
            slab(a, x0, y0, x1, y1, rng)
            keep[y0:y1, x0:x1] = True
        a[~keep] = (26, 24, 26)
        tiles['floor' if i == 0 else f'floor_{i + 1}'] = a
    return tiles


def build_wall(pick):
    """Four courses of staggered blocks. Courses are 16 px, blocks 32 px, alternate
    courses shifted 16 px, so the pattern repeats every tile in both directions."""
    pale = tone(big('wall_stone', pick, tiles=4, region=128), gain=0.74, sat=0.6)
    grain = tone(big('floor_stone', FLOOR_PICK[0], tiles=4, region=128), sat=0.0)
    sheet = np.clip(pale * (0.55 + 0.9 * grain / max(1.0, float(grain.mean()))) * 0.60, 0, 255)
    rng = np.random.default_rng(11)
    a = np.zeros((T, T, 3), np.float32)
    mortar = (38, 36, 40)
    a[:] = mortar
    k = 0
    for course in range(4):
        y0 = course * 16
        shift = 0 if course % 2 == 0 else 16
        for b in range(-1, 3):
            x0 = b * 32 + shift
            sy, sx = int(rng.integers(0, 4 * T - 14)), int(rng.integers(0, 4 * T - 30))
            src = sheet[sy:sy + 14, sx:sx + 30].copy()
            k += 1
            src *= rng.uniform(0.93, 1.05)
            src[0, :] = src[0, :] * 1.18 + 8; src[:, 0] = src[:, 0] * 1.10 + 4
            src[-1, :] *= 0.74; src[:, -1] *= 0.80
            for dy in range(14):
                for dx in range(30):
                    x = (x0 + 1 + dx) % T
                    if 0 <= x0 + 1 + dx < T or True:
                        a[y0 + 1 + dy, x] = src[dy, dx]
    return {'wall': a}


def build_plain(mid, pick, name, region=256, **t):
    return {name: wrap(tone(material(mid, pick, region=region, at=((1024 - region) // 2,) * 2), **t))}


def build(picks):
    os.makedirs(os.path.join(OUT, 'out'), exist_ok=True)
    tiles = {}
    FLOOR_PICK[0] = picks.get('floor_stone', 1)
    tiles.update(build_floor(picks.get('floor_stone', 1)))
    tiles.update(build_wall(picks.get('wall_stone', 1)))
    tiles.update(build_plain('rock', picks.get('rock', 1), 'rock', gain=0.62, sat=0.6))
    tiles.update(build_plain('water', picks.get('water', 1), 'water', region=320, gain=0.95))
    tiles.update(build_plain('lava', picks.get('lava', 1), 'lava', region=320, gain=0.95, sat=1.0))
    tiles.update(build_plain('ice', picks.get('ice', 1), 'ice', gain=0.92, sat=0.8))
    for name, a in tiles.items():
        quant(a, 20 if name.startswith(('floor', 'wall', 'rock')) else 28).save(os.path.join(OUT, 'out', name + '.png'))
    json.dump(picks, open(os.path.join(OUT, 'picks.json'), 'w'), indent=1)
    print('built', sorted(tiles))


# ---------------------------------------------------------------- sheets
def sheet():
    out = os.path.join(OUT, 'out')
    load = lambda n: Image.open(os.path.join(out, n + '.png')).convert('RGB')
    font = ImageFont.truetype('consolab.ttf', 16)
    floors = [n[:-4] for n in sorted(os.listdir(out)) if n.startswith('floor')]
    S = 2                                           # shown at 2x
    W, H = 15, 9
    room = Image.new('RGB', (W * T, H * T))
    rng = np.random.default_rng(3)
    grid = [['rock'] * W for _ in range(H)]
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            grid[y][x] = 'wall' if (y in (1, H - 2) or x in (1, W - 2) or (x == 8 and y < 5)) else 'F'
    for (x, y, n) in ((4, 5, 'water'), (5, 5, 'water'), (4, 6, 'water'), (5, 6, 'water'), (10, 5, 'lava'), (11, 5, 'lava'),
                      (10, 6, 'lava'), (11, 3, 'ice'), (12, 3, 'ice'), (11, 6, 'lava')):
        grid[y][x] = n
    for y in range(H):
        for x in range(W):
            n = grid[y][x]
            if n == 'F':
                n = floors[int(rng.choice(len(floors), p=_floor_weights(len(floors))))]
            room.paste(load(n), (x * T, y * T))
    # a few installed monsters and a hero on the floor, to judge the tiles against them
    mdir = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
    for (x, y, n) in ((2, 2, 'goblin'), (3, 4, 'skeleton_warrior'), (6, 3, 'troll'), (7, 6, 'wraith'), (9, 2, 'lich'),
                      (2, 6, 'giant_rat'), (12, 6, 'fire_elemental'), (6, 5, 'shadow'), (10, 3, 'orc_warrior'), (3, 2, 'dire_bear')):
        f = os.path.join(mdir, n + '.png')
        if os.path.exists(f) and grid[y][x] == 'F':
            spr = Image.open(f).convert('RGBA')
            if spr.size == (T, T):
                room.paste(spr, (x * T, y * T), spr)
    mats = sorted(os.listdir(os.path.join(OUT, 'materials')))
    strip_h = 150
    canvas = Image.new('RGB', (room.width, room.height + 40 + len(mats) * (strip_h + 6) + 150), (24, 22, 28))
    dr = ImageDraw.Draw(canvas)
    dr.text((8, 8), 'Tiles laid out as a map (true size)', fill=(255, 220, 140), font=font)
    canvas.paste(room, (0, 32))
    y = room.height + 40
    x = 8
    for n in sorted(os.listdir(out)):
        t = load(n[:-4]).resize((96, 96), Image.NEAREST)
        canvas.paste(t, (x, y)); dr.text((x, y + 98), n[:-4], fill=(220, 220, 230), font=font); x += 112
    y += 130
    picks = json.load(open(os.path.join(OUT, 'picks.json'))) if os.path.exists(os.path.join(OUT, 'picks.json')) else {}
    for m in mats:
        dr.text((8, y), f'{m}  (painted material; used: c{picks.get(m, 1)})', fill=(255, 220, 140), font=font)
        x = 330
        for c in (1, 2, 3):
            p = os.path.join(OUT, 'materials', m, f'c{c}.png')
            if os.path.exists(p):
                canvas.paste(Image.open(p).convert('RGB').resize((strip_h, strip_h), Image.LANCZOS), (x, y)); x += strip_h + 6
        y += strip_h + 6
    canvas.save(os.path.join(OUT, 'TILES.png'))
    print(os.path.join(OUT, 'TILES.png'))


def _floor_weights(n):
    w = np.array([5, 4, 1.2, 1.2, 1.2, 3][:n], float)
    return w / w.sum()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['paint', 'build', 'sheet'])
    ap.add_argument('--only', default=''); ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--seed', type=int, default=61000); ap.add_argument('--pick', default='')
    a = ap.parse_args()
    if a.cmd == 'paint':
        paint([x for x in a.only.split(',') if x], a.n, a.seed)
    elif a.cmd == 'build':
        picks = {}
        pf = os.path.join(OUT, 'picks.json')
        if os.path.exists(pf):
            picks = json.load(open(pf))
        picks.update({k: int(v) for k, v in (kv.split('=') for kv in a.pick.split(',') if kv)})
        build(picks); sheet()
    else:
        sheet()
