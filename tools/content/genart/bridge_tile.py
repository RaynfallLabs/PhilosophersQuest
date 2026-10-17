"""The stone bridge tile (the Black Knight's bridge), built from the painted
map tiles so it matches them: the flagstone deck from floor_2.png, a low
parapet of the wall's own masonry along each side, a dark shadow line under
each parapet and a lit top edge.

    <ComfyUI python or game python> tools/content/genart/bridge_tile.py

Writes assets/tiles/env/bridge_h.png (a bridge running left-right, parapets on
the top and bottom edges) and bridge_v.png (the same turned a quarter).
"""
import os

from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV = os.path.join(ROOT, 'assets', 'tiles', 'env')
T = 64
PARAPET = 11


def build() -> Image.Image:
    deck = Image.open(os.path.join(ENV, 'floor_2.png')).convert('RGBA').resize((T, T))
    deck = ImageEnhance.Brightness(deck).enhance(1.12)
    wall = Image.open(os.path.join(ENV, 'wall.png')).convert('RGBA').resize((T, T))
    tile = deck.copy()
    top = wall.crop((0, 0, T, PARAPET))
    bottom = wall.crop((0, T - PARAPET, T, T))
    tile.paste(top, (0, 0))
    tile.paste(bottom, (0, T - PARAPET))
    d = ImageDraw.Draw(tile)
    # the parapets' lit top edges and the shadow they throw on the deck
    d.line([(0, 1), (T, 1)], fill=(196, 188, 170, 255), width=2)
    d.line([(0, T - PARAPET + 1), (T, T - PARAPET + 1)], fill=(196, 188, 170, 255), width=2)
    d.line([(0, PARAPET), (T, PARAPET)], fill=(18, 14, 12, 255), width=3)
    d.line([(0, T - PARAPET - 2), (T, T - PARAPET - 2)], fill=(30, 24, 20, 200), width=2)
    return tile


def main():
    h = build()
    h.save(os.path.join(ENV, 'bridge_h.png'))
    h.rotate(90, expand=False).save(os.path.join(ENV, 'bridge_v.png'))
    print('wrote bridge_h.png, bridge_v.png')


if __name__ == '__main__':
    main()
