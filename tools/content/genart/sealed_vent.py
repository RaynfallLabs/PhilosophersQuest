"""The sealed smoke vent (ruling D10, 2026-11-22: "no smoke rises where your
prayer has shut it"): the smoking vent's own crack, cold, stopped with ash
and stone, with neither smoke nor glow.

Built in code from the crack's own line (domain_props.smoke_vent draws the
open one on these points), so it needs no ComfyUI and no scipy.

    py tools/content/genart/sealed_vent.py [out.png]
"""
from __future__ import annotations

import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join('assets', 'tiles', 'env', 'fixtures', 'smoke_vent_sealed.png')
CRACK = [(14, 47), (22, 43), (28, 45), (35, 40), (42, 42), (50, 38)]    # smoke_vent's
T, S = 64, 8
LIP = (8, 7, 8)                                                         # smoke_vent's
FILL = ((126, 120, 114), (150, 142, 132), (102, 96, 94), (166, 158, 146))


def build() -> Image.Image:
    rng = random.Random(121)
    line = []
    for (ax, ay), (bx, by) in zip(CRACK, CRACK[1:]):
        for i in range(4):
            j = 0.0 if i == 0 else rng.uniform(-0.7, 0.7)
            line.append(((ax + (bx - ax) * i / 4) * S, (ay + (by - ay) * i / 4 + j) * S))
    line.append((CRACK[-1][0] * S, CRACK[-1][1] * S))

    im = Image.new('RGBA', (T * S, T * S), (0, 0, 0, 0))
    soft = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(soft).line(line, fill=LIP + (170,), width=int(5.0 * S), joint='curve')
    im.alpha_composite(soft.filter(ImageFilter.GaussianBlur(0.9 * S)))
    draw = ImageDraw.Draw(im)
    draw.line(line, fill=LIP + (235,), width=int(2.8 * S), joint='curve')
    # what stops it: small stones and ash pressed along the whole of the crack
    for n, (x, y) in enumerate(line[1:-1]):
        middle = 1.0 - abs(n / max(1, len(line) - 3) - 0.5)     # fullest where the smoke rose
        rx, ry = rng.uniform(3.4, 4.8) * middle * middle * S, rng.uniform(2.4, 3.4) * middle * middle * S
        stone = [(x - rx, y + rng.uniform(-0.4, 0.4) * S), (x - rx * 0.3, y - ry),
                 (x + rx * 0.8, y - ry * 0.6), (x + rx, y + ry * 0.4), (x - rx * 0.2, y + ry)]
        draw.polygon(stone, fill=rng.choice(FILL) + (235,), outline=LIP + (200,), width=S // 2)
    return im.resize((T, T), Image.LANCZOS)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, OUT)
    build().save(out)
    print('written', out)
