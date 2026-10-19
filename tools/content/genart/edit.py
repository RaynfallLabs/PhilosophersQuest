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
creature's own painting from another sprite.

A step can instead paste a painted thing in by hand, where the model will not draw it at the
size needed (the Corwin redraw's belt toy): {"paste": picture, "box": [x0, y0, x1, y1],
"flip": false}. The thing is cut out of its own key-colour backdrop (the brief's `key`), scaled
to fit the box keeping its shape, set at the box's top centre, and laid over the picture; the
pixel pass that follows blends it into the painting.

A step {"pad": 0.88} shrinks the picture to that share of its size and centres it on its own
backdrop colour. Do it before a klein edit of a picture whose figure nearly touches the frame:
an edit redraws a few per cent larger, and a bow tip at the edge is then cut off. The last step's picture is saved as
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


def paste(src, step, key, dst):
    """Lay a painted thing (cut from its own backdrop) into the box of the picture `src`."""
    base = Image.open(src).convert('RGB')
    thing = Image.open(_path(step['paste'])).convert('RGB')
    _, mask, _ = convert.figure_mask(thing, key)
    thing = thing.resize(mask.shape[::-1], Image.LANCZOS)
    m = Image.fromarray((mask * 255).astype('uint8'))
    box = m.getbbox()
    thing, m = thing.crop(box), m.crop(box)
    if step.get('flip'):
        thing, m = thing.transpose(Image.FLIP_LEFT_RIGHT), m.transpose(Image.FLIP_LEFT_RIGHT)
    x0, y0, x1, y1 = step['box']
    k = min((x1 - x0) / thing.width, (y1 - y0) / thing.height)
    size = (max(1, round(thing.width * k)), max(1, round(thing.height * k)))
    thing, m = thing.resize(size, Image.LANCZOS), m.resize(size, Image.LANCZOS)
    base.paste(thing, (x0 + (x1 - x0 - size[0]) // 2, y0), m)
    base.save(dst)


def pad(src, share, dst):
    """The picture shrunk to `share` of its size, centred on its own backdrop (the rim's median colour)."""
    im = Image.open(src).convert('RGB')
    w, h = im.size
    rim = [im.getpixel((x, y)) for x in range(0, w, 8) for y in (0, h - 1)] + \
          [im.getpixel((x, y)) for y in range(0, h, 8) for x in (0, w - 1)]
    back = tuple(sorted(c[i] for c in rim)[len(rim) // 2] for i in range(3))
    small = im.resize((round(w * share), round(h * share)), Image.LANCZOS)
    out = Image.new('RGB', (w, h), back)
    out.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    out.save(dst)


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
            dst = os.path.join(folder, f'c{c}_draft.png' if n == len(e['steps']) else f'c{c}_step{n}.png')
            print(f"{b['id']} c{c}: step {n} of {len(e['steps'])}", flush=True)
            if 'paste' in step or 'pad' in step:
                if 'pad' in step:
                    pad(src, float(step['pad']), dst)
                else:
                    paste(src, step, b.get('key', 'magenta'), dst)
                src = dst
                continue
            names = [comfy.stage_input(src, f"genart_edit_{b['id']}_c{c}_in{n}.png")]
            names += [comfy.stage_input(_path(r), f"genart_edit_{b['id']}_c{c}_ref{n}_{j}.png")
                      for j, r in enumerate(step.get('refs', []))]
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
