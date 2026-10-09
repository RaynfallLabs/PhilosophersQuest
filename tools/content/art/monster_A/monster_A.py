"""monster_A slice: the people-shaped creatures, the friendly characters and
the heroes. draw(rec) -> 32x32 RGBA.  `python monster_A.py` writes out/.
Offline tooling (not loaded at runtime)."""
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from rig import Sprite, fig, fin, SKIN, TAN, PALE, BROWN, DARK, GREY, LEATHER  # noqa: E402
import mon  # noqa: E402,F401
import ppl  # noqa: E402
from mon import R  # noqa: E402


def fallback(s, rec):
    """A record nobody listed: still a real figure, coloured from the record
    and varied by its id."""
    h = zlib.crc32(rec['id'].encode())
    col = tuple(rec.get('color') or (120, 110, 100))
    skins = (SKIN, TAN, PALE)
    hairs = ('short', 'long', 'wild', 'topknot')
    tools = (('sword',), ('club',), ('spear',), ('axe',), ('staff', None, 'knob'))
    tags = rec.get('tags') or []
    size = 'giant' if 'giant' in tags else 'med'
    fig(s, size=size, skin=skins[h % 3], hair=hairs[(h >> 3) % 4], hairc=(BROWN, DARK, GREY)[(h >> 6) % 3],
        tc=col, tc2=LEATHER, rh=tools[(h >> 9) % 5])


def draw(rec):
    s = Sprite()
    f = R.get(rec['id'])
    if f:
        f(s, rec)
    else:
        fallback(s, rec)
    im = fin(s)
    if rec['id'] in ppl.GHOSTS:
        p = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = p[x, y]
                if a:
                    p[x, y] = (r, g, b, int(a * (0.94 if y < 22 else 0.94 - (y - 22) * 0.05)))
    return im


if __name__ == '__main__':
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0
    missing = []
    for rec in recs:
        if rec['id'] not in R:
            missing.append(rec['id'])
        d = os.path.join(HERE, 'out', rec['folder'])
        os.makedirs(d, exist_ok=True)
        im = draw(rec)
        assert im.size == (32, 32) and im.mode == 'RGBA'
        im.save(os.path.join(d, rec['id'] + '.png'))
        n += 1
    print('wrote %d of %d' % (n, len(recs)))
    if missing:
        print('fallback used for:', missing)
