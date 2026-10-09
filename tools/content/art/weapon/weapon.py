"""Weapon icons: draw(rec) -> 32x32 RGBA.  `python weapon.py` writes out/<folder>/<id>.png.

Offline tooling.  Material x template combos come from the rigs in wlib; named
weapons, ammo and strays have individual drawings in named.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from wlib import W, RIGS, MATS, get_mat  # noqa: E402
import named  # noqa: E402

LEGACY_PREFIX = ('hardened_gold', 'diamond', 'hardwood', 'wood', 'bone')
CLASS_RIG = {'sword': 'longsword', 'dagger': 'dagger', 'axe': 'battleaxe', 'spear': 'spear', 'club': 'club',
             'mace': 'mace', 'warhammer': 'warhammer', 'staff': 'quarterstaff', 'scimitar': 'scimitar',
             'ranged': 'longbow', 'bow': 'longbow', 'morningstar': 'morningstar', 'zweihander': 'zweihander',
             'blunt': 'mace', 'polearm': 'glaive', 'crossbow': 'crossbow', 'sling': 'sling'}


def _split(rid):
    """material + template from an id such as 'cold_iron_great_axe'."""
    for t in sorted(RIGS, key=len, reverse=True):
        if rid == t:
            return None, t
        if rid.endswith('_' + t):
            return rid[:-len(t) - 1], t
    return None, None


def draw(rec):
    rid = rec['id']
    if rid in named.N:
        return named.N[rid](rec)
    mat, tpl = rec.get('material'), rec.get('template')
    if tpl not in RIGS or not mat:
        m2, t2 = _split(rid)
        tpl = tpl if tpl in RIGS else t2
        mat = mat if (mat in MATS) else (m2 or mat)
    if tpl not in RIGS:
        cls = rec.get('weapon_class') or rec.get('class')
        tpl = CLASS_RIG.get(cls, 'longsword')
    M = get_mat(mat or 'plain', rec.get('material_color') or rec.get('color'))
    s = W()
    RIGS[tpl](s, M)
    return s.finish()


def main():
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0
    for r in recs:
        d = os.path.join(HERE, 'out', r['folder'])
        os.makedirs(d, exist_ok=True)
        draw(r).save(os.path.join(d, r['id'] + '.png'))
        n += 1
    print('wrote %d of %d' % (n, len(recs)))


if __name__ == '__main__':
    main()
