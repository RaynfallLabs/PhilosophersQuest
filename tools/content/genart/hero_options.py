"""A before/after sheet for a hero redraw that Brandon must approve before it is installed.

    <ComfyUI python> tools/content/genart/hero_options.py tools/content/genart/briefs/corwin_options.json

The spec (JSON) names:
  "title", "out"                      the sheet's heading and where it is written
  "current", "current_says"           the sprite in the game now, and a line about it
  "current_label"                     optional: the first row's heading (default NOW IN THE GAME), for a
                                      sheet that compares an option with its revision
  "original", "original_label"        optional: the painting it once was, shown scaled down
  "finalists": [{"label", "file", "says"}]   each option, a 64 px sprite and a line about it
  "beside": [path, ...]               other heroes shown next to each sprite at the same size

Every sprite is drawn the way the game draws it (renderer.fit_sprite: pixel art enlarged by a
whole number with hard edges, then smooth-scaled) on the dungeon floor tile: at 6x, at 64 px
and at 40 px (the map's close and medium zooms), and beside the other heroes at 64 px, 2x and
40 px. Paths are relative to the project root.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BG = (24, 22, 28)
INK = (236, 226, 200)
DIM = (170, 160, 150)
GOLD = (255, 220, 140)
PAD, BIG, GAP = 20, 384, 4


def _path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def fit(im, size):
    """renderer.fit_sprite, in Pillow."""
    w, h = im.size
    if (w, h) == (size, size):
        return im
    if max(w, h) <= 64:
        k = max(2, -(-2 * size // max(w, h)))
        im = im.resize((w * k, h * k), Image.NEAREST)
    return im.resize((size, size), Image.LANCZOS)


def on_floor(im, size, floor):
    tile = floor.resize((size, size), Image.LANCZOS)
    tile.alpha_composite(fit(im, size))
    return tile


def big(im, floor, k=6):
    """The 64 px sprite enlarged k times with hard edges, on the floor tile enlarged the same way."""
    tile = floor.resize((64 * k, 64 * k), Image.NEAREST)
    tile.alpha_composite(fit(im, 64).resize((64 * k, 64 * k), Image.NEAREST))
    return tile


def strip(sprites, floor, size, gap=GAP, k=1):
    """Sprites side by side on floor tiles, as they stand on the map; k enlarges the result."""
    out = Image.new('RGBA', (len(sprites) * (size + gap) - gap, size), BG + (255,))
    for i, s in enumerate(sprites):
        out.alpha_composite(on_floor(s, size, floor), (i * (size + gap), 0))
    return out if k == 1 else out.resize((out.width * k, out.height * k), Image.NEAREST)


def main():
    spec = json.load(open(sys.argv[1], encoding='utf-8'))
    floor = Image.open(_path('assets/tiles/env/floor.png')).convert('RGBA')
    font = ImageFont.truetype('consola.ttf', 15)
    bold = ImageFont.truetype('consolab.ttf', 20)
    head = ImageFont.truetype('consolab.ttf', 28)
    load = lambda p: Image.open(_path(p)).convert('RGBA')  # noqa: E731
    beside = [load(p) for p in spec.get('beside', [])]
    names = [os.path.splitext(os.path.basename(p))[0].replace('player_', '') for p in spec.get('beside', [])]
    rows = [(spec.get('current_label', 'NOW IN THE GAME'), spec.get('current_says', ''), load(spec['current']), True)]
    rows += [(f['label'], f['says'], load(f['file']), False) for f in spec['finalists']]

    left_w = BIG + PAD + 64 + PAD + 3 * 40 + 2 * GAP
    group = len(beside) + 1
    right_w = max(group * (64 + GAP) * 2, 220 + group * (64 + GAP))
    W = PAD + left_w + PAD * 2 + right_w + PAD
    ROW = BIG + 80
    H = 76 + ROW * len(rows)
    sheet = Image.new('RGBA', (W, H), BG + (255,))
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 20), spec['title'], fill=GOLD, font=head)

    for r, (label, says, sprite, is_now) in enumerate(rows):
        y = 76 + ROW * r
        d.line([(PAD, y - 8), (W - PAD, y - 8)], fill=(70, 64, 60))
        d.text((PAD, y), label, fill=GOLD, font=bold)
        d.text((PAD, y + 28), says, fill=INK, font=font)
        y += 56
        sheet.alpha_composite(big(sprite, floor), (PAD, y))
        x = PAD + BIG + PAD
        d.text((x, y - 2), '64 px', fill=DIM, font=font)
        sheet.alpha_composite(on_floor(sprite, 64, floor), (x, y + 18))
        d.text((x, y + 92), '40 px', fill=DIM, font=font)
        sheet.alpha_composite(on_floor(sprite, 40, floor), (x, y + 112))
        d.text((x, y + 162), '40 px, a row of tiles', fill=DIM, font=font)
        sheet.alpha_composite(strip([sprite] * 3, floor, 40), (x, y + 182))

        x = PAD + left_w + PAD * 2
        group_imgs = [sprite] + beside
        tags = ['this'] + names
        if is_now and spec.get('original'):
            d.text((x, y - 2), spec.get('original_label', 'the original painting'), fill=DIM, font=font)
            sheet.alpha_composite(load(spec['original']).resize((200, 200), Image.LANCZOS), (x, y + 18))
            sx = x + 220
            d.text((sx, y - 2), 'beside other heroes, 64 px:', fill=DIM, font=font)
            sheet.alpha_composite(strip(group_imgs, floor, 64), (sx, y + 18))
            d.text((sx, y + 92), 'at 40 px:', fill=DIM, font=font)
            sheet.alpha_composite(strip(group_imgs, floor, 40), (sx, y + 112))
            y2 = y + 230
        else:
            d.text((x, y - 2), 'beside other heroes, 64 px:', fill=DIM, font=font)
            sheet.alpha_composite(strip(group_imgs, floor, 64), (x, y + 18))
            d.text((x + group * (64 + GAP) + 16, y + 18), 'at 40 px:', fill=DIM, font=font)
            sheet.alpha_composite(strip(group_imgs, floor, 40), (x + group * (64 + GAP) + 16, y + 38))
            y2 = y + 124
        d.text((x, y2 - 20), 'the same, 2x:', fill=DIM, font=font)
        sheet.alpha_composite(strip(group_imgs, floor, 64, k=2), (x, y2))
        for i, n in enumerate(tags):
            d.text((x + i * (64 + GAP) * 2 + 4, y2 + 132), n, fill=DIM, font=font)
    out = _path(spec['out'])
    sheet.convert('RGB').save(out)
    print(out)


if __name__ == '__main__':
    main()
