"""The Minoan horns of consecration, drawn in code (two painted rounds drew Gothic
spires, a goblet, a well-head and a bull's skull). One carved block of pale
limestone: a flat base, and two thick horns rising from it with one deep smooth
curve between them, as at Knossos. Drawn at 1024 px on the magenta key, then cut
by convert.to_sprite like every painted stand prop (outline, size, palette).

Brandon, 2026-11-12, on the painted one in the game: "like a cattle skull sitting on the
ground"; then "Yes, redraw them". Variant 1 is the one installed (domain_props.CODE).

    <ComfyUI python> tools/content/genart/horns.py <out_dir>    v1..v3 and HORNS_SHEET.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import convert  # noqa: E402

N = 1024
LIFT = 0.78                  # darker than the usual lift, which washed the shading out
MAT = os.path.join(ROOT, '_genart', 'domains', 'tiles', 'materials', 'temple_ashlar', 'c1.png')


def stone(rng):
    """Pale limestone: the painted ashlar material, warmed to cream."""
    m = np.asarray(Image.open(MAT).convert('RGB').resize((N, N), Image.LANCZOS)).astype(np.float32)
    m = m * np.array([1.06, 1.0, 0.88])            # cream, not grey-green
    lum = m.mean(2, keepdims=True)
    m = lum + (m - lum) * 0.8
    return np.clip(m, 0, 255)


def shape(v):
    """(mask, shade, geometry) for variant v at N px. u runs -1..1 across the base, y up
    from the foot (0) to the horn tips (1)."""
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    P = {1: dict(W=0.40, H=0.80, base=0.20, step=0.09, saddle=0.38, arc=0.26, tip_in=0.60, foot=0.80, flare=0.20),
         2: dict(W=0.41, H=0.74, base=0.22, step=0.10, saddle=0.40, arc=0.30, tip_in=0.56, foot=0.78, flare=0.16),
         3: dict(W=0.38, H=0.86, base=0.18, step=0.08, saddle=0.36, arc=0.24, tip_in=0.62, foot=0.80, flare=0.22)}[v]
    W, H = P['W'] * N, P['H'] * N
    bottom = N * 0.95
    u = (xx - N / 2) / W
    y = (bottom - yy) / H
    au = np.abs(u)
    # a two-step plinth: a broad foot slab, then the block the horns are cut from
    foot = (y >= 0) & (y <= P['step']) & (au <= 1.0)
    block = (y > P['step']) & (y <= P['base']) & (au <= 0.92)
    # the horns: outer faces lean out toward the tips, the inner faces meet in one round U
    t = np.clip((y - P['base']) / (1 - P['base']), 0, 1)
    outer = P['foot'] + P['flare'] * t ** 1.8
    k = np.clip((y - P['saddle']) / P['arc'], 0, 1)
    inner = np.where(y > P['saddle'], P['tip_in'] * np.sqrt(k) * (0.92 + 0.08 * t), -1.0)
    inner = np.minimum(inner, outer - 0.16)
    lo = np.maximum(inner, 0)
    c = (outer + lo) / 2
    w = (outer - lo) / 2
    tipz = 0.92
    cap = np.where(y > tipz, np.sqrt(np.clip(1 - ((y - tipz) / (1 - tipz)) ** 2, 0, 1)), 1.0)
    horn = (y > P['base']) & (y <= 1.0) & (au <= c + w * cap) & ((au >= c - w * cap) | (y <= P['saddle']))
    mask = foot | block | horn
    # light from the upper left. A horn is round: lit on its outer-left face, dark on the
    # inside of the U; the right horn sits a shade darker than the left.
    s = np.clip((au - c) / np.maximum(w, 1e-3), -1, 1)                # -1 inner face .. 1 outer
    side = np.sign(u)
    lit = np.where(side < 0, 0.5 + 0.5 * s, 0.5 - 0.5 * s)            # facing the light
    horn_shade = 0.40 + 0.80 * np.sin(np.clip(lit, 0, 1) * np.pi * 0.5 + 0.10) - 0.16 * (side > 0)
    shade = np.ones((N, N), np.float32)
    shade = np.where(horn & (y > P['saddle']), horn_shade, shade)
    shade = np.where(horn & (y <= P['saddle']), 0.92 - 0.10 * (u > 0) + 0.06 * (u < -0.4), shade)
    # the inside of the U, deepest at its bottom
    shade = np.where(horn & (y > P['saddle']) & (au < lo + 0.07) & (y < P['saddle'] + P['arc']),
                     shade * 0.66, shade)
    # the block and the foot: lit top edges, front faces, a dark line where each meets the next
    shade = np.where(block, 0.84 - 0.18 * (u > 0.55), shade)
    shade = np.where(block & (y > P['base'] - 0.035), 1.14, shade)
    shade = np.where(foot, 0.74 - 0.16 * (u > 0.7), shade)
    shade = np.where(foot & (y > P['step'] - 0.025) & (au > 0.90), 1.04, shade)
    shade = np.where(foot & (y > P['step'] - 0.012), shade * 0.82, shade)
    shade = np.where(foot & (y < 0.025), 0.62, shade)
    shade = np.where(horn & (y < P['base'] + 0.035), shade * 0.74, shade)     # where the horns leave the block
    return mask, shade, (u, y, au, c, w, P['base'], P['saddle'], W, H)


def chip(mask, shade, geo, rng, v):
    """A chipped horn tip (the brief: chipped at one horn tip), a few cracks, weathering."""
    u, y, au, c, w, base_h, saddle, W, H = geo
    # chip the right horn's tip: a diagonal bite off its top
    bite = (u > 0) & (y > 0.88) & ((y - 0.88) * 1.8 + (au - c) * 1.0 > 0.10)
    mask = mask & ~bite
    # cracks: thin dark lines across the base and up one horn
    cr = np.zeros(mask.shape, np.float32)
    img = Image.fromarray((cr * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    pts = [(0.62, 0.02), (0.55, 0.09), (0.58, 0.15), (0.50, 0.21)]
    bottom = N * 0.95
    xy = [(N / 2 + (px - 0.5) * 2 * W * 0.9 - W * 0.2, bottom - py * H) for px, py in pts]
    d.line(xy, fill=255, width=5)
    xy2 = [(N / 2 - W * 0.80, bottom - 0.50 * H), (N / 2 - W * 0.86, bottom - 0.62 * H),
           (N / 2 - W * 0.83, bottom - 0.70 * H)]
    d.line(xy2, fill=255, width=4)
    cr = np.asarray(img).astype(np.float32) / 255.0
    shade = shade * (1 - 0.45 * cr)
    weather = ndi.gaussian_filter(rng.random(mask.shape).astype(np.float32), 14)
    weather = (weather - weather.mean()) / max(1e-6, weather.std())
    shade = shade * (1 + 0.05 * weather)
    return mask, shade


def sprite(v: int = 1):
    """The 64 px fixture (variant 1 is the installed one)."""
    return build(v)[1]


def build(v):
    rng = np.random.default_rng(700 + v)
    mask, shade, geo = shape(v)
    mask, shade = chip(mask, shade, geo, rng, v)
    rgb = stone(rng) * shade[..., None]
    # a soft occlusion line where the horns meet the base's top
    pic = np.zeros((N, N, 3), np.float32)
    pic[:] = (255, 0, 255)
    pic[mask] = np.clip(rgb[mask], 0, 255)
    im = Image.fromarray(pic.astype(np.uint8), 'RGB')
    spr, _facts = convert.to_sprite(im, 'magenta', tile=64, scale=0.6, stand=True, lift=LIFT)
    return im, spr


def sheet(sprites, old):
    floors = [Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', f)).convert('RGBA').resize((64, 64))
              for f in ('floor.png', 'floor_3.png')]
    Z = 4
    cells = [('in the game now (reads as a skull)', old)] + [(f'v{i + 1}', s) for i, s in enumerate(sprites)]
    sh = Image.new('RGBA', (len(cells) * (64 * Z + 24) + 24, 64 * Z + 64 * 2 + 90), (24, 22, 26, 255))
    d = ImageDraw.Draw(sh)
    try:
        font = ImageFont.truetype('arial.ttf', 18)
    except OSError:
        font = ImageFont.load_default()
    for i, (label, s) in enumerate(cells):
        x = 24 + i * (64 * Z + 24)
        tile = floors[0].copy()
        tile.alpha_composite(s)
        sh.paste(tile.resize((64 * Z, 64 * Z), Image.NEAREST), (x, 40))
        for j, f in enumerate(floors):                      # 1:1, as close zoom shows it
            t2 = f.copy()
            t2.alpha_composite(s)
            sh.paste(t2, (x + j * 72, 40 + 64 * Z + 12))
        d.text((x, 10), label, fill=(240, 230, 200), font=font)
    return sh


if __name__ == '__main__':
    OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(OUT, exist_ok=True)
    sprites = []
    for v in (1, 2, 3):
        big, spr = build(v)
        big.save(os.path.join(OUT, f'horns_v{v}_big.png'))
        spr.save(os.path.join(OUT, f'horns_v{v}.png'))
        sprites.append(spr)
    old = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', 'fixtures', 'horns_consecration.png')).convert('RGBA')
    sheet(sprites, old).save(os.path.join(OUT, 'HORNS_SHEET.png'))
    print('ok')
