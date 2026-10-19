"""The Emberpup plush (Corwin's stuffie), set by hand pixel by pixel, to lay on a 64 px sprite.

A plush the model paints at a belt comes out 6 to 9 sprite pixels tall after the cut, and the
pixel pass turns its orange felt into flames. This 13 x 15 design reads at 64 px and at 40 px:
a big round orange head with two black button eyes, a cream belly, stubby limbs, and the tail
curling up at its side with a felt flame on the tip, hanging from a brown cord. The colours are
the Emberpup sprite's own. The Corwin redraw's briefs carry the stamped pixels as edit "touch"
lists, so edit.py remakes each sprite without this file; it is kept to stamp the plush again.

    from plush import stamp
    sprite = stamp(sprite, x0, y0, flip=False)   # (x0, y0): the top of the cord
"""
from PIL import Image

PAL = {
    'K': (20, 16, 24), 'L': (92, 60, 36), 'O': (254, 114, 0), 'H': (255, 159, 4), 'D': (198, 59, 6),
    'C': (248, 229, 143), 'c': (244, 183, 68), 'E': (20, 16, 24),
    'Y': (255, 214, 80), 'F': (255, 140, 1), 'R': (231, 61, 0),
}
PLUSH = [
    "....L.......",
    "....L.......",
    "..KKKKK.....",
    ".KHHOOOK....",
    "KHOOOOODK...",
    "KOEOOOEDK...",
    "KOEOOOEDK.KK",
    "KOOODOODK.KYK",
    ".KDDDDDK.KYFK",
    "KOKCCCKOKKFRK",
    "KOKCCCKOKOKK.",
    ".KOCCcODKOK..",
    ".KOOOODDOK...",
    ".KOKKKDKK....",
    ".KK...KK.....",
]


def stamp(sprite: Image.Image, x0: int, y0: int, flip: bool = False, design=PLUSH) -> Image.Image:
    """`sprite` with the plush laid on it, the cord's top at (x0, y0); '.' leaves a pixel as it is.
    `flip` mirrors it, for a hero facing the other way."""
    im = sprite.convert('RGBA').copy()
    w = max(len(r) for r in design)
    for dy, row in enumerate(design):
        row = row.ljust(w, '.')
        if flip:
            row = row[::-1]
        for dx, ch in enumerate(row):
            x, y = x0 + dx, y0 + dy
            if ch != '.' and 0 <= x < im.width and 0 <= y < im.height:
                im.putpixel((x, y), PAL[ch] + (255,))
    return im
