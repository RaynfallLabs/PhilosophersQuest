"""Draw a scene sprite with the pipeline: a creature together with a prop under it
and one over it (the abandoned Emberpup on its rock under a rain cloud).

    <ComfyUI python> tools/content/genart/scene.py tools/content/genart/briefs/r05.json --n 3 --out _genart/r05 --seed 9100

pipeline.py's fixed prompt forbids anything under or around a figure ("no rock, no
base") because a rock under a creature cut out as a mess in the pilot. A scene sprite
needs exactly those things, drawn on purpose, so a brief with "body": "scene" carries:

  scene_whole      replaces the "shown full length ..." clause (how the parts stack)
  scene_action     replaces the fixed action sentence (the legged one demands a fight)
  scene_props      replaces the closing "nothing lies under it" sentence (the props,
                   placed in the picture, and what is NOT round them)
  scene_allow_neg  phrases taken out of the fixed negative prompt ("rocks underfoot")
  pieces           how many separate pieces the cut may leave (a cloud above is one)

Everything else (drafting, the pixel pass, the cut, the mechanical checks, the
automatic redraws and the review sheet) is pipeline.py unchanged.

Rain drawn by the model is hair-thin and gone at 64 px, so the picked painting
gets bold streaks painted on by hand, then is re-cut:

    <ComfyUI python> tools/content/genart/scene.py rain _genart/r05/<id>/c<N>_pixel.png streaks.json
    <ComfyUI python> tools/content/genart/scene.py <brief> --n 4 --out _genart/r05 --sheets-only
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline  # noqa: E402

_CLOSING = ("There is no ground, no floor, no horizon and no shadow of any kind under or behind the figure, "
            "and nothing lies under or around it: no base, no rock, no web, no grass, no puddle, no rubble, no smoke.")


def _scene_brief(path):
    briefs = json.load(open(path, encoding='utf-8'))
    scenes = [b for b in briefs if b.get('body') == 'scene']
    if len(scenes) != 1 or len(briefs) != 1:
        raise SystemExit('scene.py draws a brief file holding exactly one "body": "scene" brief')
    return scenes[0]


def patch(b):
    """Point the pipeline's fixed wording at this one scene."""
    assert _CLOSING in pipeline.DRAFT, 'pipeline.DRAFT changed: update scene.py'
    pipeline.DRAFT = pipeline.DRAFT.replace(
        _CLOSING, "There is no floor, no horizon and no shadow under or behind anything. " + b['scene_props'])
    pipeline.WHOLE['legged'] = b['scene_whole']
    pipeline.ACTION['legged'] = b['scene_action']
    neg = [p.strip() for p in pipeline.DRAFT_NEG.split(',')]
    pipeline.DRAFT_NEG = ', '.join(p for p in neg if p not in set(b.get('scene_allow_neg', ())))
    pipeline.PIXEL = pipeline.PIXEL.replace('single figure,', 'one small scene: the creature with its props,')


def add_rain(src, out, streaks, width=12, colour=(222, 230, 238)):
    """Paint bold rain onto a picked painting (1024 px), then re-cut it with
    --sheets-only. The model draws rain as hair-thin lines that vanish at 64
    px; a sprite pixel is 16 painting pixels, so each streak is painted about
    one sprite pixel wide, with a darker edge so it reads on the floor. Each
    streak runs unbroken from the cloud to what it lands on: the cut drops
    loose pieces, so dashes would vanish. Slant them and vary their length,
    or evenly spaced uprights read as the bars of a cage.
    `streaks`: [[x0, y0, x1, y1], ...] in painting pixels, cloud to target."""
    from PIL import Image, ImageDraw
    import numpy as np
    im = Image.open(src).convert('RGB')
    # A soft grey cloud on the green backdrop has a mint fringe the cut keeps
    # (README: smoke on green). Turn faintly green pixels grey; the backdrop
    # itself (strongly green) is left for the cut to remove.
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    fringe = (g >= r) & (g >= b) & (g - np.maximum(r, b) > 6) & (sat < 0.5)
    grey = ((r + b) / 2.0)[..., None]
    a[fringe] = np.repeat(grey, 3, axis=2)[fringe]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    edge = tuple(int(c * 0.55) for c in colour)
    for s in streaks:
        d.line(tuple(s), fill=edge, width=width + 6)
    for s in streaks:
        d.line(tuple(s), fill=colour, width=width)
    im.save(out)


if __name__ == '__main__':
    if sys.argv[1] == 'rain':
        # scene.py rain <pixel.png> <streaks.json>   (the original is kept as *_norain.png)
        src = sys.argv[2]
        keep = src.replace('.png', '_norain.png')
        if not os.path.exists(keep):
            import shutil
            shutil.copyfile(src, keep)
        add_rain(keep, src, json.load(open(sys.argv[3], encoding='utf-8')))
    else:
        patch(_scene_brief(sys.argv[1]))
        pipeline.main()
