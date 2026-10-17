"""The Black Knight's limb stages: the SAME knight, drawn four more times with
limbs missing, from his picked full painting used as a reference.

    <ComfyUI python> tools/content/genart/black_knight_stages.py draw <run dir> <seed> [--n 3] [--only stage,stage]
    <ComfyUI python> tools/content/genart/black_knight_stages.py cut  <run dir>

The README warns that "a missing limb is not drawn; both arms come back" when a
creature is drawn from a brief. `draw` tries FLUX.2 klein with the picked
painting as a ReferenceLatent: the armour, colours and size carry over well,
BUT the limbs still came back (r06, 2026-10-17: in 12 candidates one arm was
dropped with its shield only twice, the arms were merely shortened, a leg was
bent rather than removed, and every torso was the whole knight). The shipped
stages are therefore cut by hand from the painting: black_knight_cuts.py. This
file keeps the attempt and provides the shared scale-true cut.

`cut` turns every candidate into a 64 px sprite at the FULL knight's scale (the
pipeline's own cut scales every figure to fill its tile, which would blow the
torso up to the size of a whole man), standing on the bottom edge and centred on
the full knight's centre line, so the five stages line up frame to frame.

The full knight is <run>/black_knight/c<pick>_draft.png, the pick read from
<run>/review.json. Output: <run>/black_knight_<stage>/c<N>_{draft,pixel,sprite}.png.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import comfy      # noqa: E402
import convert    # noqa: E402
import pipeline   # noqa: E402

KEY = 'green'
SAME = ("The exact same black knight as in the reference painting, redrawn faithfully in the same classic "
        "fantasy oil painting style: the same glossy jet-black plate armour with bright pale steel-white worn "
        "edges, the same flat-topped closed great helm with its dark eye slit, the same plain black knee-length "
        "surcoat and brown belt, the same size in the picture and the same place in the picture. ")
STUMP = ("Each cut is clean: a short rounded stump of black armour plate, its cut end a flat dark red wound with "
         "a little bright red blood, and a few small drops of blood running down from it. No bone, no gore. ")
FRAME = (" Alone, on a perfectly flat plain pure bright green (#00FF00) background, with no floor, no ground, no "
         "shadow and no scenery; nothing lies on the ground and nothing is near him.")
NEG = ("severed arm lying on the ground, severed leg lying on the ground, limbs on the floor, pool of blood, "
       "puddle, gore, guts, bone, skeleton, skull, glowing eyes, bare face, bare head, second figure, cape, horse, "
       "floor, ground shadow, cast shadow, scenery, frame, border, text, watermark, cartoon, chibi, big head, "
       "photo, 3d render, blurry")

STAGES = {
    'one_arm': dict(
        what=SAME + "His LEFT arm is gone: it has been cut off at the shoulder, so on that side of his body there "
             "is no arm at all and no shield, only a short stump at the shoulder. " + STUMP +
             "His right arm is whole and still raises the same bright sword above his helm, exactly as in the "
             "reference. His two legs stand exactly as in the reference, planted wide apart. He has exactly one "
             "arm, the sword arm.",
        neg="shield, left arm, left hand, two arms, second arm, gauntlet on the left",
        pixel="a black armoured knight with only one arm, his right arm raising a sword, the left arm cut off at "
              "the shoulder with a small bloody stump, no shield"),
    'no_arms': dict(
        what=SAME + "BOTH of his arms are gone: each has been cut off at the shoulder, so he has no arms, no hands, "
             "no sword and no shield, only two short stumps, one at each shoulder. " + STUMP +
             "He still stands on his two legs, planted wide apart exactly as in the reference, chest thrust out, "
             "defiant. He has no arms at all.",
        neg="arms, hands, gauntlets, sword, shield, weapon, held object",
        pixel="a black armoured knight with no arms, both arms cut off at the shoulders with small bloody stumps, "
              "standing on two legs, no sword, no shield"),
    'one_leg': dict(
        what=SAME + "BOTH of his arms are gone, cut off at the shoulders, and his RIGHT leg is gone too, cut off at "
             "the top of the thigh just below the surcoat's hem, so he stands on his one left leg only. He has a "
             "short stump at each shoulder and a short stump below the hem of his surcoat where the right leg was. "
             + STUMP + "He is hopping on his one left leg, knee bent, leaning forward, defiant. No arms, no "
             "sword, no shield, exactly one leg.",
        neg="arms, hands, sword, shield, weapon, second leg, two legs, right leg, crutch, staff",
        pixel="a black armoured knight with no arms and only one leg, hopping, small bloody stumps at the shoulders "
              "and the hip, no sword, no shield"),
    'torso': dict(
        what=SAME + "Only his upper body is left: his helmed head, his armoured chest and the top of his surcoat. "
             "Both arms are cut off at the shoulders and both legs are cut off at the hips, so there are no arms "
             "and no legs anywhere in the picture: the torso stands upright by itself, its flat base at the bottom "
             "of the figure where the surcoat ends. " + STUMP + "His helm is tilted up, shouting defiantly. The "
             "torso is drawn at the same size as in the reference, so it fills only the lower part of the "
             "picture.",
        neg="arms, hands, legs, feet, boots, knees, sword, shield, weapon, whole body, standing man",
        pixel="the armoured torso of a black knight with no arms and no legs, stumps at the shoulders and hips "
              "with a little blood, upright, helmed head"),
}


def workflow(ref_name, prompt, negative, seed, size=1024, steps=20, cfg=4.0):
    wf = comfy.draft_workflow(prompt, negative, seed, size, steps, cfg)
    wf['ri'] = {'class_type': 'LoadImage', 'inputs': {'image': ref_name}}
    wf['re'] = {'class_type': 'VAEEncode', 'inputs': {'pixels': ['ri', 0], 'vae': ['v', 0]}}
    wf['rp'] = {'class_type': 'ReferenceLatent', 'inputs': {'conditioning': ['p', 0], 'latent': ['re', 0]}}
    wf['g']['inputs']['positive'] = ['rp', 0]
    return wf


def full_pick(run):
    rv = json.load(open(os.path.join(run, 'review.json'), encoding='utf-8'))
    return int(rv['black_knight']['pick'])


def draw(run, seed, n, only):
    pick = full_pick(run)
    ref = comfy.stage_input(os.path.join(run, 'black_knight', f'c{pick}_draft.png'), 'black_knight_ref.png')
    jobs, meta = [], []
    for st, s in STAGES.items():
        if only and st not in only:
            continue
        for c in range(1, n + 1):
            sd = seed + c * 7919 + sum(map(ord, st)) % 1000
            out = os.path.join(run, f'black_knight_{st}', f'c{c}_draft.png')
            jobs.append((workflow(ref, s['what'] + FRAME, NEG + ', ' + s['neg'], sd), out))
            meta.append((st, c, sd))
    print('drafts failed:', comfy.run(jobs), flush=True)
    pix = []
    for st, c, sd in meta:
        d = os.path.join(run, f'black_knight_{st}', f'c{c}_draft.png')
        if os.path.exists(d):
            name = comfy.stage_input(d, f'bk_{st}_c{c}.png')
            pp = pipeline.PIXEL.format(what=STAGES[st]['pixel'], colours='glossy black plate armour, bright steel edges, a little red blood',
                                       holds='', keyname=KEY)
            pn = pipeline.PIXEL_NEG + ', ' + STAGES[st]['neg']
            pix.append((comfy.pixel_workflow(name, pp, pn, sd, pipeline.PIXEL_DENOISE),
                        os.path.join(run, f'black_knight_{st}', f'c{c}_pixel.png')))
    print('pixel failed:', comfy.run(pix))


def _box(im):
    _, fig, _ = convert.figure_mask(im, KEY)
    ys, xs = np.where(fig)
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def cut(run):
    """Every drawn stage at the full knight's scale."""
    cut_dirs(run, [f'black_knight_{st}' for st in STAGES])


def cut_dirs(run, dirs):
    """The full knight and every candidate in `dirs` as 64 px sprites, all at
    the full knight's scale and centre line (c<N>_stage_sprite.png)."""
    pick = full_pick(run)
    full = os.path.join(run, 'black_knight', f'c{pick}_pixel.png')
    fy0, fy1, fx0, fx1 = _box(Image.open(full))
    side = fy1 - fy0
    cx = (fx0 + fx1) // 2
    for sub in ['black_knight'] + list(dirs):
        d = os.path.join(run, sub)
        for c in range(1, 7):
            p = os.path.join(d, f'c{c}_pixel.png')
            if not os.path.exists(p):
                continue
            scaled_sprite(p, side, cx).save(os.path.join(d, f'c{c}_stage_sprite.png'))
            print('cut', sub, c)


def scaled_sprite(src, side, cx, lift=1.3, tile=64):
    """The figure in a fixed side x side window (bottom = its own feet or base),
    shrunk by the same factor for every stage, then through convert's colour,
    outline and quantise steps by way of to_sprite on that window."""
    im = Image.open(src).convert('RGB').resize((convert.WORK, convert.WORK), Image.LANCZOS)
    _, fig, _ = convert.figure_mask(im, KEY)
    ys, xs = np.where(fig)
    y1 = ys.max() + 1
    key = convert.KEYS[KEY]
    # the window may reach past the painting's edge: pad with the backdrop first
    pad = side
    big = Image.new('RGB', (im.width + 2 * pad, im.height + 2 * pad), key)
    big.paste(im, (pad, pad))
    left, top = cx - side // 2 + pad, y1 - side + pad
    win = big.crop((left, top, left + side, top + side))
    # to_sprite scales the FIGURE's box to the tile; mark the window's top
    # corners as figure (one painting pixel each: too small to survive the cut)
    # so the box is the whole window and every stage shrinks by the same factor.
    real = convert.figure_mask

    def marked(img, k='magenta'):
        a, f, facts = real(img, k)
        f = f.copy()
        f[0, 0] = f[0, -1] = True
        return a, f, facts
    convert.figure_mask = marked
    try:
        spr, _ = convert.to_sprite(win, KEY, lift=lift)
    finally:
        convert.figure_mask = real
    return spr


if __name__ == '__main__':
    mode, run = sys.argv[1], sys.argv[2]
    if mode == 'draw':
        n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 3
        only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else []
        draw(run, int(sys.argv[3]), n, only)
    else:
        cut(run)
