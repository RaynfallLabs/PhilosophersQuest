"""monster_B slice: undead, demons, aberrations, constructs, elementals, celestials.

draw(rec) -> 32x32 RGBA.  `python monster_B.py` writes out/<folder>/<id>.png.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from rig import Sp, REG  # noqa
import undead  # noqa
import demon  # noqa
import misc  # noqa
import fallback  # noqa


def draw(rec):
    s = Sp(rec)
    f = REG.get(rec['id']) or fallback.pick(rec)
    f(s, rec['id'], rec)
    return s.done()


def main():
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0; missing = []
    for r in recs:
        if r['id'] not in REG:
            missing.append(r['id'])
        d = os.path.join(HERE, 'out', r['folder'])
        os.makedirs(d, exist_ok=True)
        draw(r).save(os.path.join(d, r['id'] + '.png'))
        n += 1
    print('wrote', n, 'of', len(recs))
    if missing:
        print('FALLBACK used for', len(missing), ':', ' '.join(missing))


if __name__ == '__main__':
    main()
