"""Badges that show Brandon's own art: a painted background with the game's installed sprite on it.

    <ComfyUI python> tools/content/genart/badge_composite.py [--only art,art] [--run _genart/badges]

The duck line, Dad, the family cats, Shep and the fire pet line are never redrawn (Brandon's
rule). Their badges are a painted vignette BACKGROUND with no figure (a brief `<art>_bg`, drawn
by pipeline.py like any badge scene), with the game's own installed 64 px sprite composited on
it, scaled up by a whole number with nearest-neighbour so its pixels stay crisp.

COMPOSITES maps each badge's art stem to its group, the sprite under assets/tiles, an optional
crop box of the sprite (in sprite pixels), the whole-number scale, and where the middle of the
(cropped) sprite lands on the 128 px badge. For each background candidate cN it writes
<run>/<group>/<art>/cN_sprite.png (the badge, masked to the circle the background already has,
so a sprite part that reaches past the rim is cut with the same soft edge) and cN_pixel.png (the
background painting with the sprite drawn on it, for the review sheets). review.json then picks a
candidate the usual way, and install_achievements.py installs it like any other badge.
"""
import argparse, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TILES = os.path.join(ROOT, 'assets', 'tiles')

# art: (group, sprite under assets/tiles, crop box or None, scale, (centre x, centre y) on the badge)
COMPOSITES = {
    'duck_worn':    ('a11', 'items/duck_of_doom.png',       None, 2, (64, 66)),
    'duck_hatched': ('a11', 'monsters/waddlekind.png',      None, 2, (64, 68)),
    'duck_grown':   ('a11', 'monsters/seraphimallard.png',  None, 2, (64, 66)),
    'dad_is_here':  ('a10', 'monsters/dad.png',             None, 2, (64, 70)),
    'from_home':    ('a10', 'monsters/sherlock_the_stout.png', None, 2, (64, 70)),
    'always_comes': ('a10', 'monsters/shep.png',            None, 2, (60, 66)),
    'i_choose_you': ('a10', 'monsters/emberpup.png',        None, 2, (64, 68)),
}


def sprite_layer(path, crop, scale, centre, size=128):
    """The sprite cut to its own bounding box (or `crop`), scaled by `scale` with
    nearest-neighbour, on a transparent size x size layer with its middle at `centre`."""
    spr = Image.open(path).convert('RGBA')
    spr = spr.crop(crop or spr.getbbox())
    spr = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x, y = int(round(centre[0] - spr.width / 2.0)), int(round(centre[1] - spr.height / 2.0))
    # paste with clipping: Image.alpha_composite needs the source inside the layer
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(spr.width, size - x), min(spr.height, size - y)
    if sx1 > sx0 and sy1 > sy0:
        layer.alpha_composite(spr.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))
    return layer


def composite(bg, layer):
    """The sprite layer over the background medallion, then cut to the medallion's own circle."""
    bg = bg.convert('RGBA')
    out = bg.copy()
    out.alpha_composite(layer)
    out.putalpha(bg.getchannel('A'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=''); ap.add_argument('--run', default=os.path.join(ROOT, '_genart', 'badges'))
    ap.add_argument('--n', type=int, default=3)
    a = ap.parse_args()
    for art, (group, spath, crop, scale, centre) in COMPOSITES.items():
        if a.only and art not in a.only.split(','):
            continue
        layer = sprite_layer(os.path.join(TILES, spath), crop, scale, centre)
        bgdir = os.path.join(a.run, group, art + '_bg')
        outdir = os.path.join(a.run, group, art)
        made = 0
        for c in range(1, a.n + 1):
            bgp = os.path.join(bgdir, f'c{c}_sprite.png')
            if not os.path.exists(bgp):
                continue
            os.makedirs(outdir, exist_ok=True)
            composite(Image.open(bgp), layer).save(os.path.join(outdir, f'c{c}_sprite.png'))
            painting = Image.open(os.path.join(bgdir, f'c{c}_pixel.png')).convert('RGBA')
            big = layer.resize(painting.size, Image.NEAREST)
            painting.alpha_composite(big)
            painting.convert('RGB').save(os.path.join(outdir, f'c{c}_pixel.png'))
            made += 1
        print(f'{art}: {made} composites from {spath} x{scale}' + ('' if made else f' (no background in {bgdir})'))


if __name__ == '__main__':
    main()
