"""The rare pets' art (2026-11-14): race track tiles, the Mooble's dance poses, the review sheet.

    <ComfyUI python> tools/content/genart/domain_props.py draw tools/content/genart/briefs/rare_pets.json --n 3 --out _genart/rare_pets --seed 98100 [--only id,id]
    <ComfyUI python> tools/content/genart/rare_pets_art.py tiles paint [--n 3] [--seed 98300]
    <ComfyUI python> tools/content/genart/rare_pets_art.py tiles build [--pick race_sand=2,race_wood=1]
    <ComfyUI python> tools/content/genart/rare_pets_art.py dance
    <ComfyUI python> tools/content/genart/rare_pets_art.py finals
    <ComfyUI python> tools/content/genart/rare_pets_art.py sheet [<out.png>]
    py tools/content/genart/install_rare_pets.py [--dry]

The creatures, items and fixtures are ordinary pipeline briefs (briefs/rare_pets.json),
drawn through `domain_props.py draw` so the three fixtures and two items get the object
wording ("one single thing only, with no person in it") and the cut stands them on the
tile's bottom edge like the Stray Kids fixtures. Picks are in <run>/review.json.

tiles   The race track is made the way tiles.py made the base floor: two materials
        (packed track sand, weathered oak) are painted flat from above through the same
        two passes, then cut in code. `race_track_floor` is the sand, wrapped so it
        repeats with no seam (tiles.wrap), toned a little brighter and warmer than the
        dungeon flagstones. `race_track_rail` is that floor with a wooden rail fence
        built across it from the painted oak: two rails running from the left edge to
        the right edge (so a row of them is one fence) and one post in the middle. The
        game turns it a quarter for a fence that runs up and down.
dance   The four dance poses are one creature in four moves, shown in turn on the rhythm
        screen, so they must be the same size. The pipeline fills the tile with each
        pose's own outline, which would shrink the Mooble whenever his wings spread. Here
        each pick is cut again in a window sized by the Mooble's own body (the area of
        his cream fur), so his body is the same size in all four; the hop is lifted off
        the bottom edge so it reads as a hop. The two leans are one painting tipped
        about its feet each way (TILT).
finals  Two sprites finished in code into <run>/final. The young Bococho's "dull, faded"
        plumage came out tan in every round (a different-looking bird from the yellow pet);
        her sprite's tan is turned back to a dull yellow (RETINT: hue band, new hue,
        saturation gain), so she is plainly the same breed, only faded. And the champion
        saddled. A saddle drawn on a running bird gave a four-legged A saddle drawn on a running bird gave a four-legged
        horse-bird in all twelve draws and in three of five klein edits (the white crest
        turns into a mane); the edits that kept two legs grew a crest as big as the body.
        So the champion's riding sprite is the grown bird's saddled sprite (the same
        painting, so it swaps cleanly when she grows) dressed in the champion's marks in
        code: the crest tipped white, the royal-blue prize ribbon at her neck, and the
        saddle flap turned to a royal-blue saddle cloth edged in gold.
sheet   RARE_PETS_ART_SHEET.png: every pick at 64 px and at 3x on the dungeon floor, the
        four dance poses side by side, the track tiles laid out as a short stretch of
        track, and each saddled bird with a hero set in the saddle at the seat.

Work files live in the main checkout's gitignored _genart/rare_pets/ (`--run` names
another folder).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import convert  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
T = 64
DANCE = ('mooble_dance_left', 'mooble_dance_right', 'mooble_dance_up', 'mooble_dance_down')
HOP = {'mooble_dance_up': 0.12}          # share of the window left empty under the hop
# A squat hides fur (the legs fold under the belly), so by fur alone the crouching Mooble came
# out a quarter bigger than the others (his head 14 px wide against 10-11): his window is
# widened by this much to match the heads.
SQUASH = {'mooble_dance_down': 1.28}
# The leans: no draw of either lean leant (the model stands a figure seen from the front up
# straight, arms out, in all six). One painting with arms flung wide and a foot kicked out is
# tipped about its feet, 16 degrees each way, before the cut: plainly the same Mooble in the
# same light, leaning left and then right.
TILT = {'mooble_dance_left': ('mooble_dance_left', 16), 'mooble_dance_right': ('mooble_dance_left', -16)}

# The rider's seat on each saddled bird, in the 64 px frame: the middle of the saddle's
# dip, where a rider's hips sit (measured on the picks: pommel at x 26-30, cantle at x 36-42,
# the dip between them at y 22-24). The champion is cut from the same picture, so the same.
SEAT = {'bococho_saddled': (33, 23), 'bococho_champion_saddled': (33, 23)}

LEAD = ("A classic fantasy oil painting, looking straight down from directly above at {what} "
        "It fills the whole picture from edge to edge like a texture sample: the same surface everywhere, "
        "no border, no frame, no horizon, no walls, no perspective. "
        "Flat even light from the upper left, soft shallow shadows only. Painted like the scenery in a 1980s "
        "fantasy roleplaying rulebook: weathered, worn, serious, rich but muted colours. {colours}")
NEG = ("face, carving, statue, rings, concentric circles, bright centre, dark rim, creatures, people, animals, "
       "footprints, hoof prints, furniture, border, frame, vignette, horizon, perspective, side view, text, photo, "
       "3d render, cartoon, bright candy colours, strong cast shadows, lens blur")
PIX = ("detailed pixel art texture, seen from directly above, {short}, weathered, muted colours, even light, "
       "fills the whole picture")
PIX_NEG = ("face, carving, statue, concentric rings, bright centre, creatures, footprints, border, frame, text, "
           "photograph, 3d render, cartoon, perspective, blur")
MATERIALS = {
    'race_sand': dict(
        what="the packed track of a racing ground in a great underground cavern: firm packed sand and earth, dusty "
             "sand-brown, scuffed and churned all over by running feet into shallow scrapes, short ruts and "
             "kicked-up crumbs of earth, with a few small pebbles. The scuffs run every way and are spread evenly: "
             "there is no centre, no path and no part of the picture differs from any other.",
        colours="Dusty sand-brown and dull light ochre, darker brown in the scuffs and ruts, low contrast.",
        short="packed dusty sand-brown racing track earth, scuffed and churned evenly all over, small ruts"),
    'race_wood': dict(
        what="the side of a long rough-hewn beam of old weathered oak, seen straight on: dark brown wood with a "
             "strong straight grain running from the left edge to the right edge across the whole picture, fine "
             "cracks along the grain, two or three small dark knots, scuffs and darker weather stains. One plain "
             "surface of wood: no joints, no nails, no planks side by side.",
        colours="Dark weathered brown oak, a little grey on the worn faces, darker in the cracks.",
        short="weathered dark brown oak beam surface, straight grain running left to right, fine cracks"),
}


def _run(a):
    if a.run:
        return a.run
    here = os.path.join(ROOT, '_genart', 'rare_pets')
    if os.path.isdir(here):
        return here
    # a worktree has no _genart of its own: the work files live in the main checkout
    main = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ROOT))), '_genart', 'rare_pets')
    return main if os.path.isdir(main) else here


def picks(run):
    with open(os.path.join(run, 'review.json'), encoding='utf-8') as f:
        return {k: v['pick'] for k, v in json.load(f).items() if v.get('pick')}


# ---------------------------------------------------------------- the track tiles
def paint_tiles(run, n, seed):
    import comfy
    if not comfy.running():
        raise SystemExit('ComfyUI is not running on 127.0.0.1:8188')
    drafts, second = [], []
    for mid, m in MATERIALS.items():
        for c in range(1, n + 1):
            s = seed + c * 31 + sum(map(ord, mid))
            d = os.path.join(run, 'tiles', 'materials', mid, f'c{c}_draft.png')
            os.makedirs(os.path.dirname(d), exist_ok=True)
            drafts.append((comfy.draft_workflow(LEAD.format(**m), NEG, s), d))
            second.append((mid, c, d, s, m))
    print(comfy.run(drafts) or 'drafts ok', flush=True)
    jobs = []
    for mid, c, d, s, m in second:
        name = comfy.stage_input(d, f'genart_race_{mid}_c{c}.png')
        jobs.append((comfy.pixel_workflow(name, PIX.format(**m), PIX_NEG, s, 0.42),
                     os.path.join(run, 'tiles', 'materials', mid, f'c{c}.png')))
    print(comfy.run(jobs) or 'pixel ok', flush=True)


def _material(run, mid, pick, region, at=None):
    im = Image.open(os.path.join(run, 'tiles', 'materials', mid, f'c{pick}.png')).convert('RGB')
    x, y = at if at else ((im.width - region) // 2, (im.height - region) // 2)
    return np.asarray(im.crop((x, y, x + region, y + region)).resize((T, T), Image.BOX)).astype(np.float32)


def _lum(a):
    return float((a[..., :3] * np.array([0.299, 0.587, 0.114])).sum(-1).mean())


def build_floor(run, pick):
    """The packed sand, wrapped to repeat, set a little brighter and warmer than the flagstones (59).
    The painting darkens toward one corner; that slow change is taken out first (the sand minus
    a heavy blur of itself), or the wrap's cross-fade shows it as a seam across the tile."""
    import tiles
    from scipy import ndimage as ndi
    a = tiles.tone(_material(run, 'race_sand', pick, 320), sat=0.75)
    slow = ndi.gaussian_filter(a, sigma=(10, 10, 0), mode='reflect')
    a = tiles.wrap(a - slow + a.mean((0, 1), keepdims=True))
    a = np.clip(a * (68.0 / max(1.0, _lum(a))), 0, 255)
    return a


def _plank_rows(wood, height, n, avoid=()):
    """The `n` bands of `height` rows lying inside one plank (no dark joint across them): the
    bands whose darkest row is brightest, apart from each other and from `avoid`."""
    rows = wood.mean((1, 2))
    score = [(min(rows[y:y + height]), y) for y in range(0, len(rows) - height)]
    out = []
    for _, y in sorted(score, reverse=True):
        if all(abs(y - o) >= height + 2 for o in list(out) + list(avoid)):
            out.append(y)
        if len(out) == n:
            break
    return out


def build_rail(run, floor, pick):
    """The floor with a two-rail oak fence across it: rails from edge to edge, one post in the middle."""
    import tiles
    wood = tiles.tone(_material(run, 'race_wood', pick, 512), sat=0.85)
    wood[..., 1] = np.minimum(wood[..., 1], wood[..., 0] * 0.92)      # no green speck survives in the oak
    wood = np.clip(wood * (88.0 / max(1.0, _lum(wood))), 0, 255)
    a = floor.copy()
    out = np.array(convert.OUTLINE, np.float32)
    # the shadow each rail and the post throw on the sand just below them (soft, not a cast shadow)
    for y0 in (27, 41):
        a[y0:y0 + 3] *= 0.62
    a[52:55, 27:38] *= 0.6
    r1, r2 = _plank_rows(wood, 7, 2)
    for y0, y1, src in ((19, 26, r1), (33, 40, r2)):          # the two rails, grain running across
        band = wood[src:src + (y1 - y0)].copy()
        band[0] = band[0] * 1.25 + 10                        # lit top edge
        band[-1] *= 0.70
        a[y0:y1] = band
        a[y0 - 1] = out
        a[y1] = out
    p0 = _plank_rows(wood, 11, 1)[0]
    post = np.transpose(wood[p0:p0 + 11, :], (1, 0, 2))[12:51]   # grain running down the post, 11 wide
    post = post * 0.92
    post[:, 0] = post[:, 0] * 1.18 + 6                         # lit left face
    post[:, -1] *= 0.72
    post[:3] = post[:3] * 1.3 + 14                             # its cut top catches the light
    a[12:51, 27:38] = post
    a[11, 27:38] = out
    a[51, 27:38] = out
    a[11:52, 26] = out
    a[11:52, 38] = out
    return np.clip(a, 0, 255)          # a lit edge past 255 would wrap round to teal in uint8


def build_tiles(run, pk):
    import tiles
    o = os.path.join(run, 'tiles', 'out')
    os.makedirs(o, exist_ok=True)
    floor = build_floor(run, pk.get('race_sand', 1))
    rail = build_rail(run, floor, pk.get('race_wood', 1))
    tiles.quant(floor, 20).save(os.path.join(o, 'race_track_floor.png'))
    tiles.quant(rail, 24).save(os.path.join(o, 'race_track_rail.png'))
    json.dump(pk, open(os.path.join(run, 'tiles', 'picks.json'), 'w'), indent=1)
    print('built race_track_floor, race_track_rail', pk)


# ---------------------------------------------------------------- the dance poses at one scale
def _body_area(pic, key='green'):
    """(figure bbox at WORK size, area of the Mooble's cream fur): the fur is the bright, pale,
    warm part of the figure; wings, antenna, bobble and outline are not."""
    a, fig, _ = convert.figure_mask(pic, key)
    h, s, v = convert._hsv(a)
    fur = fig & (v > 0.62) & (s < 0.38)
    ys, xs = np.where(fig)
    return (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1), float(fur.sum())


def _painting(run, d, pk):
    """The pose's painting at the cut's working size; a lean is its source painting tipped about the feet."""
    src, deg = TILT.get(d, (d, 0))
    im = Image.open(os.path.join(run, src, f'c{pk[src]}_pixel.png')).convert('RGB')
    im = im.resize((convert.WORK, convert.WORK), Image.LANCZOS)
    if not deg:
        return im
    a, fig, _ = convert.figure_mask(im, 'green')
    ys, xs = np.where(fig)
    y1 = ys.max()
    cx = float(xs[ys > y1 - 40].mean())                      # the middle of the feet
    rim = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)])
    back = tuple(int(v) for v in np.median(rim, 0))
    pad = 300
    big = Image.new('RGB', (im.width + 2 * pad, im.height + 2 * pad), back)
    big.paste(im, (pad, pad))
    big = big.rotate(deg, resample=Image.BICUBIC, center=(cx + pad, y1 + pad), fillcolor=back)
    return big.crop((pad, pad, pad + im.width, pad + im.height))


def _cut_window(big, key, box, side, air):
    """to_sprite on a side x side window whose bottom is the figure's feet (raised by `air` of the
    window for a hop), so every pose shrinks by the factor its window sets."""
    y0, y1, x0, x1 = box
    pad = side
    canvas = Image.new('RGB', (big.width + 2 * pad, big.height + 2 * pad), convert.KEYS[key])
    canvas.paste(big, (pad, pad))
    cx = (x0 + x1) // 2
    bottom = y1 + int(round(air * side))
    win = canvas.crop((cx - side // 2 + pad, bottom - side + pad, cx - side // 2 + pad + side, bottom + pad))
    real = convert.figure_mask

    def marked(img, k='magenta'):
        aa, f, facts = real(img, k)
        f = f.copy()
        f[0, 0] = f[0, -1] = f[-1, 0] = f[-1, -1] = True      # the box is the whole window
        return aa, f, facts
    convert.figure_mask = marked
    try:
        spr, _ = convert.to_sprite(win, key, spill=True)
    finally:
        convert.figure_mask = real
    return spr


def dance(run):
    pk = picks(run)
    info = {}
    for d in DANCE:
        p = _painting(run, d, pk)
        box, fur = _body_area(p)
        y0, y1, x0, x1 = box
        body = np.sqrt(fur) * SQUASH.get(d, 1.0)
        info[d] = (p, box, body, max(y1 - y0, x1 - x0) / body)
    # the window is the same number of body-widths for every pose: enough for the widest one
    ratio = max(e * (1 + HOP.get(d, 0)) for d, (_, _, _, e) in info.items()) * 1.03
    o = os.path.join(run, 'dance')
    os.makedirs(o, exist_ok=True)
    for d, (p, box, body, e) in info.items():
        side = int(round(ratio * body))
        fur = body * body
        spr = _cut_window(p, 'green', box, side, HOP.get(d, 0))
        spr.save(os.path.join(o, d + '.png'))
        print(d, 'window', side, 'fur', int(fur))


# ---------------------------------------------------------------- the champion's trappings
WHITE, PALE = (242, 239, 226), (214, 211, 196)
BLUES = ((24, 40, 128), (40, 74, 196), (92, 128, 232))
GOLD = (216, 176, 64)
DARK = convert.OUTLINE


def _hsv_px(c):
    import colorsys
    return colorsys.rgb_to_hsv(*(v / 255.0 for v in c[:3]))


def champion(run):
    """bococho_champion_saddled: the grown bird's saddled sprite in the champion's marks."""
    from scipy import ndimage as ndi
    pk = picks(run)
    src = Image.open(os.path.join(run, 'bococho_saddled', f"c{pk['bococho_saddled']}_sprite.png")).convert('RGBA')
    a = np.array(src)
    op = a[..., 3] > 0
    out = np.all(a[..., :3] == DARK, -1)
    # the crest (the head's top, above the beak): the top four pixels of every column turn white
    for x in range(12, 32):
        ys = [y for y in range(0, 12) if op[y, x] and not out[y, x]]
        for k, y in enumerate(ys[:4]):
            a[y, x, :3] = WHITE if k < 2 else PALE
    # the saddle flap (the dark brown leather hanging down the flank) becomes a blue cloth
    cloth = np.zeros(op.shape, bool)
    for y in range(25, 45):
        for x in range(28, 39):
            if op[y, x] and not out[y, x]:
                h, s_, v = _hsv_px(a[y, x])
                if (h < 0.09 or h > 0.95) and v < 0.55 and s_ > 0.25:
                    cloth[y, x] = True
    lab, n = ndi.label(cloth)
    if n:
        big = 1 + int(np.argmax(ndi.sum(cloth, lab, range(1, n + 1))))
        cloth = lab == big
    edge = cloth & ~ndi.binary_erosion(cloth)
    for y, x in zip(*np.where(cloth)):
        v = _hsv_px(a[y, x])[2]
        a[y, x, :3] = GOLD if edge[y, x] else BLUES[0] if v < 0.25 else BLUES[1] if v < 0.42 else BLUES[2]
    # the prize ribbon: a pleated blue disc at the base of the neck, with two short tails
    cx, cy = 12, 27
    for y in range(cy - 3, cy + 4):
        for x in range(cx - 3, cx + 4):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d <= 5:
                a[y, x] = (*(BLUES[2] if d == 0 else BLUES[1] if d <= 2 else BLUES[0]), 255)
            elif d <= 9 and a[y, x, 3] > 0:
                a[y, x] = (*DARK, 255)
    for x, y in ((11, 30), (11, 31), (11, 32), (13, 30), (13, 31), (13, 32)):
        a[y, x] = (*BLUES[1], 255)
    for x, y in ((11, 33), (13, 33), (12, 31), (12, 32)):
        a[y, x] = (*DARK, 255)
    o = os.path.join(run, 'final')
    os.makedirs(o, exist_ok=True)
    Image.fromarray(a, 'RGBA').save(os.path.join(o, 'bococho_champion_saddled.png'))
    print('built', os.path.join(o, 'bococho_champion_saddled.png'))


# The young Bococho: tan (hue 20-55 degrees) turned to a dull yellow (hue 44, saturation x1.3).
RETINT = {'npc_bococho_young': (20, 55, 44, 1.3)}


def retint(run):
    import colorsys
    pk = picks(run)
    for sid, (lo, hi, to, gain) in RETINT.items():
        a = np.array(Image.open(os.path.join(run, sid, f'c{pk[sid]}_sprite.png')).convert('RGBA'))
        for y, x in zip(*np.where(a[..., 3] > 0)):
            h, s_, v = colorsys.rgb_to_hsv(*(a[y, x, :3] / 255.0))
            if lo <= h * 360 <= hi and s_ > 0.15:
                a[y, x, :3] = [round(c * 255) for c in colorsys.hsv_to_rgb(to / 360.0, min(1.0, s_ * gain), v)]
        os.makedirs(os.path.join(run, 'final'), exist_ok=True)
        Image.fromarray(a, 'RGBA').save(os.path.join(run, 'final', sid + '.png'))
        print('built', os.path.join(run, 'final', sid + '.png'))


def finals(run):
    retint(run)
    champion(run)


# ---------------------------------------------------------------- the review sheet
def _sprite_path(run, sid, pk):
    if sid in DANCE and os.path.exists(os.path.join(run, 'dance', sid + '.png')):
        return os.path.join(run, 'dance', sid + '.png')
    if os.path.exists(os.path.join(run, 'final', sid + '.png')):
        return os.path.join(run, 'final', sid + '.png')
    if sid.startswith('race_track_'):
        return os.path.join(run, 'tiles', 'out', sid + '.png')
    return os.path.join(run, sid, f'c{pk[sid]}_sprite.png')


GROUPS = [
    ('The Mooble (floors 31-45): on his ledge, then the pet\'s three stages', ['npc_mooble', 'mooble', 'mooble_dancer', 'mooble_troupe_leader']),
    ('The Mooble\'s four dance moves (rhythm screen): left, right, up, down', list(DANCE)),
    ('The Bococho (floors 51-65): at the camp, then the pet\'s three stages', ['npc_bococho_young', 'bococho_chick', 'bococho', 'bococho_champion']),
    ('Saddled for riding (the hero is drawn on top) / Gilt Varro and his bird', ['bococho_saddled', 'bococho_champion_saddled', 'npc_varro_bococho', 'gilt_varro']),
    ('Forage finds / the camp\'s fixtures', ['starnut', 'sunroot', 'race_tether_post', 'race_betting_board', 'race_finish_banner']),
]


def sheet(run, out):
    pk = picks(run)
    font = ImageFont.truetype('consola.ttf', 13)
    bold = ImageFont.truetype('consolab.ttf', 17)
    floor = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', 'floor.png')).convert('RGBA')
    S = 3
    cell = T * S + 10 + T + 16                 # 3x, a gap, then true size
    W = 16 + 5 * (cell + 14)
    rows = len(GROUPS) + 2
    H = 60 + rows * (T * S + 64) + 40
    sh = Image.new('RGB', (W, H), (24, 22, 28))
    dr = ImageDraw.Draw(sh)
    dr.text((16, 14), 'Rare pets art: every pick at 3x and at 64 px, on the dungeon floor', fill=(255, 220, 140), font=bold)
    y = 52

    def on_floor(spr, k, ground=None):
        g = (ground or floor).resize((T, T), Image.NEAREST)
        t = Image.new('RGBA', (T, T))
        t.paste(g, (0, 0))
        t.alpha_composite(spr)
        return t.resize((T * k, T * k), Image.NEAREST)

    for title, ids in GROUPS:
        dr.text((16, y), title, fill=(236, 226, 200), font=bold)
        x = 16
        for sid in ids:
            spr = Image.open(_sprite_path(run, sid, pk)).convert('RGBA')
            sh.paste(on_floor(spr, S), (x, y + 24))
            sh.paste(on_floor(spr, 1), (x + T * S + 10, y + 24 + T * S - T))
            dr.text((x, y + 28 + T * S), sid, fill=(200, 200, 220), font=font)
            x += cell + 14
        y += T * S + 64
    # the track: floor tiles with a row of rail across, true size and 3x
    dr.text((16, y), 'Race track tiles: race_track_floor, race_track_rail (a row of rails, and turned a quarter)', fill=(236, 226, 200), font=bold)
    fl = Image.open(_sprite_path(run, 'race_track_floor', pk)).convert('RGBA')
    rl = Image.open(_sprite_path(run, 'race_track_rail', pk)).convert('RGBA')
    track = Image.new('RGBA', (T * 6, T * 3))
    for gy in range(3):
        for gx in range(6):
            t = rl if gy == 0 else (rl.rotate(90) if gx == 5 else fl)
            track.paste(t, (gx * T, gy * T))
    sh.paste(fl.resize((T * S, T * S), Image.NEAREST), (16, y + 24))
    sh.paste(rl.resize((T * S, T * S), Image.NEAREST), (16 + T * S + 14, y + 24))
    sh.paste(track, (16 + 2 * (T * S + 14), y + 24))
    for gx in range(3):
        m = Image.open(_sprite_path(run, ['bococho', 'npc_varro_bococho', 'gilt_varro'][gx], pk)).convert('RGBA')
        sh.paste(on_floor(m, 1, fl), (16 + 2 * (T * S + 14) + T * 6 + 20 + gx * (T + 8), y + 24))
    y += T * S + 64
    # the seat: each saddled bird with a hero in the saddle, at the scale the report suggests
    dr.text((16, y), 'The seat: a hero (player.png) at 0.6 scale, hips on the seat point (red dot = seat)', fill=(236, 226, 200), font=bold)
    hero = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', 'player.png')).convert('RGBA')
    x = 16
    for sid in ('bococho_saddled', 'bococho_champion_saddled'):
        bird = Image.open(_sprite_path(run, sid, pk)).convert('RGBA')
        seat = SEAT.get(sid)
        marked = bird.copy()
        if seat:
            sx, sy = seat
            ImageDraw.Draw(marked).point([(sx, sy), (sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)],
                                         fill=(255, 40, 40, 255))
        sh.paste(on_floor(marked, S), (x, y + 24))
        if seat:
            hs = 38
            h = hero.resize((hs, hs), Image.NEAREST)
            rid = bird.copy()
            # the hero's hips sit about 55% down his picture
            rid.alpha_composite(h, (seat[0] - hs // 2, max(0, seat[1] - int(hs * 0.55))))
            sh.paste(on_floor(rid, S), (x + T * S + 14, y + 24))
        x += 2 * (T * S + 14) + 20
    sh.save(out)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['tiles', 'dance', 'finals', 'sheet'])
    ap.add_argument('sub', nargs='?', default='')
    ap.add_argument('--run', default='')
    ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--seed', type=int, default=98300)
    ap.add_argument('--pick', default='')
    a = ap.parse_args()
    run = _run(a)
    if a.cmd == 'tiles':
        if a.sub == 'paint':
            paint_tiles(run, a.n, a.seed)
        else:
            pf = os.path.join(run, 'tiles', 'picks.json')
            pk = json.load(open(pf)) if os.path.exists(pf) else {}
            pk.update({k: int(v) for k, v in (kv.split('=') for kv in a.pick.split(',') if kv)})
            build_tiles(run, pk)
    elif a.cmd == 'dance':
        dance(run)
    elif a.cmd == 'finals':
        finals(run)
    else:
        sheet(run, a.sub or os.path.join(ROOT, 'RARE_PETS_ART_SHEET.png'))


if __name__ == '__main__':
    main()
