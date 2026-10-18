"""Change part of a picked painting with FLUX.2 klein's reference editing; keep the rest.

    <ComfyUI python> tools/content/genart/edit.py tools/content/genart/briefs/r04.json --only emberpup --out _genart/r04
        [--cut-only]   re-cut the saved pixel pass after changing rain / recolour / touch

For a slight cleanup a fresh draw is the wrong tool: it gives a new creature. A brief with
an "edit" entry is instead redrawn from its own earlier painting:

  "edit": {"cand": 5,                        the candidate number the result is saved as
           "steps": [{"from": painting, "refs": [painting, ...], "seed": 303,
                      "prompt": "Edit this painting. Keep ... Change only ...", "neg": "..."}, ...],
           "pixel_seed": 5291,               seed of the pipeline's pixel pass
           "rain": [[x0, y0, x1, y1], ...],  optional: bold rain painted on the pixel pass (scene.py)
           "recolour": [[x0, y0, x1, y1, "#from", "#to"], ...]  optional: inside the box (x1, y1
                                             not included) one sprite colour becomes another
           "shift": [[x0, y0, x1, y1, dx], ...]  optional: every pixel inside the box moves dx to the
                                             right (negative: left) and the pixels it leaves become empty;
                                             a few row bands with growing dx shear a limb (feet closer)
           "touch": [[x, y, "#rrggbb"], ...]} optional: sprite pixels set by hand after the cut
                                             (and after any shift, so give the shifted positions)

The cut picks 32 colours for the whole sprite, so a pale belly can end up sharing the
painted rain's grey: "recolour" gives it its own colour back.

Each step edits the picture before it (the first edits "from", paths relative to the
project root); "refs" are further pictures the model may copy from, such as the
creature's own painting from another sprite. The last step's picture is saved as
c<cand>_draft.png; the pipeline's own pixel pass and cut then make c<cand>_pixel.png and
c<cand>_sprite.png, so the result looks like every other sprite. Earlier steps are kept
as c<cand>_step<N>.png. A scene brief gets scene.py's wording for the pixel pass.
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import comfy  # noqa: E402
import convert  # noqa: E402
import pipeline  # noqa: E402
from PIL import Image  # noqa: E402


def _path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def _rgba(col):
    return tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def run(b, out, cut_only=False):
    """cut_only: skip both drawing passes and re-cut the saved pixel pass (after a change
    to "rain", "recolour" or "touch", or to the brief's `lift`)."""
    e = b['edit']
    c = int(e['cand'])
    folder = os.path.join(out, b['id'])
    os.makedirs(folder, exist_ok=True)
    pixel = os.path.join(folder, f'c{c}_pixel.png')
    keep = pixel.replace('.png', '_norain.png')          # the pixel pass before rain is painted on
    if not cut_only:
        src = _path(e['steps'][0]['from'])
        for n, step in enumerate(e['steps'], 1):
            names = [comfy.stage_input(src, f"genart_edit_{b['id']}_c{c}_in{n}.png")]
            names += [comfy.stage_input(_path(r), f"genart_edit_{b['id']}_c{c}_ref{n}_{j}.png")
                      for j, r in enumerate(step.get('refs', []))]
            dst = os.path.join(folder, f'c{c}_draft.png' if n == len(e['steps']) else f'c{c}_step{n}.png')
            print(f"{b['id']} c{c}: step {n} of {len(e['steps'])}", flush=True)
            for f in comfy.run([(comfy.edit_workflow(names, step['prompt'], step.get('neg', ''), step['seed']), dst)]):
                raise SystemExit(f'edit failed: {f}')
            src = dst
        if b.get('body') == 'scene':
            import scene
            scene.patch(b)
        _, _, pp, pn = pipeline.prompts(b)
        name = comfy.stage_input(src, f"genart_{b['id']}_c{c}.png")
        for f in comfy.run([(comfy.pixel_workflow(name, pp, pn, int(e['pixel_seed']), pipeline.PIXEL_DENOISE), pixel)]):
            raise SystemExit(f'pixel pass failed: {f}')
        if e.get('rain'):
            shutil.copyfile(pixel, keep)
    if e.get('rain'):
        import scene
        scene.add_rain(keep, pixel, e['rain'])
    spr, facts = convert.to_sprite(Image.open(pixel), b.get('key', 'magenta'), lift=float(b.get('lift', 1.0)),
                                   spill=bool(b.get('despill')))
    for x0, y0, x1, y1, old, new in e.get('recolour', []):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if spr.getpixel((x, y)) == _rgba(old):
                    spr.putpixel((x, y), _rgba(new))
    for x0, y0, x1, y1, dx in e.get('shift', []):
        box = spr.crop((x0, y0, x1, y1))
        spr.paste((0, 0, 0, 0), (x0, y0, x1, y1))
        spr.alpha_composite(box, (x0 + dx, y0))
    for x, y, col in e.get('touch', []):
        spr.putpixel((x, y), _rgba(col))
    spr.save(os.path.join(folder, f'c{c}_sprite.png'))
    facts['pieces'] = int(b.get('pieces', 1))
    print(f"{b['id']} c{c}:", '; '.join(pipeline.mechanical(facts)) or 'passes the mechanical checks')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('briefs')
    ap.add_argument('--only', default='')
    ap.add_argument('--out', required=True)
    ap.add_argument('--cut-only', action='store_true', help='re-cut the saved pixel pass; draw nothing')
    a = ap.parse_args()
    briefs = [b for b in json.load(open(a.briefs, encoding='utf-8')) if 'edit' in b]
    todo = [b for b in briefs if not a.only or b['id'] in a.only.split(',')]
    problems = pipeline.check_briefs(todo)
    if problems:
        raise SystemExit('Briefs need fixing first:\n  ' + '\n  '.join(problems))
    if not a.cut_only and not comfy.running():
        raise SystemExit('ComfyUI is not running on 127.0.0.1:8188')
    for b in todo:
        run(b, a.out, a.cut_only)


if __name__ == '__main__':
    main()
