"""monster_C slice: animals and monsters of the natural world, dragons, reptiles, plants, pets.

draw(rec) -> 32x32 RGBA.   python monster_C.py  writes out/<folder>/<id>.png for slice.json.
Offline tooling (not loaded at runtime).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from c_base import REG  # noqa: E402
import c_beast  # noqa: E402,F401
import c_crit  # noqa: E402,F401
import c_scaly  # noqa: E402,F401
import c_green  # noqa: E402,F401


def draw(rec):
    fn = REG.get(rec['id'])
    if fn is None:
        # A record this slice was not written for: fall back to the body-plan rig.
        fn = {'dragon': c_scaly.generic_dragon, 'reptile': c_scaly.generic_snake,
              'plant': c_green.generic_plant}.get(rec.get('body'), c_crit.generic_beast)
    return fn(rec)


if __name__ == '__main__':
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0
    missing = [r['id'] for r in recs if r['id'] not in REG]
    for r in recs:
        p = os.path.join(HERE, 'out', r['folder'])
        os.makedirs(p, exist_ok=True)
        im = draw(r)
        assert im.size == (32, 32) and im.mode == 'RGBA'
        im.save(os.path.join(p, r['id'] + '.png'))
        n += 1
    print('wrote', n, 'of', len(recs), '| generic fallbacks:', missing)
