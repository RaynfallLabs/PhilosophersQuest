"""Armor and shield icons.  draw(rec) -> 32x32 RGBA.   python armor.py writes out/<folder>/<id>.png
Offline tooling (not loaded at runtime)."""
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import rigs  # noqa: E402
from rigs import A, P, TEMPLATES, mat_palette, legacy, render  # noqa: E402

import named  # noqa: E402
NAMED = named.NAMED
STRAY = named.STRAY

KEYWORDS = [  # fallback for anything unknown: id keyword -> template
    ('tower', 'tower_shield'), ('kite', 'kite_shield'), ('buckler', 'buckler'), ('shield', 'shield'),
    ('great_helm', 'great_helm'), ('helm', 'iron_helm'), ('cap', 'leather_cap'), ('hood', 'leather_cap'),
    ('cloak', 'cloak'), ('mantle', 'cloak'), ('boots', 'leather_boots'), ('sandals', 'leather_boots'),
    ('greaves', 'plate_greaves'), ('leggings', 'cloth_leggings'), ('gauntlets', 'plate_gauntlets'),
    ('gloves', 'leather_gloves'), ('bracers', 'leather_bracers'), ('vambraces', 'iron_vambraces'),
    ('shirt', 'padded_shirt'), ('scale', 'scale'), ('hide', 'hide'), ('plate', 'plate'), ('mail', 'chainmail'),
]


def draw(rec):
    rid = rec['id']
    seed = zlib.crc32(rid.encode()) & 0xffff
    if rid in NAMED:
        return NAMED[rid](rec)
    if rid in STRAY:
        return STRAY[rid](rec)
    s = A()
    mat = rec.get('material')
    tpl = rec.get('template')
    if rec.get('combo') and mat:
        p = mat_palette(s, mat, rec.get('material_color'), seed)
        tpl = legacy(tpl, p.cls)
        if tpl in TEMPLATES:
            return render(tpl, p, s)
    # unknown: guess the shape from the id, colour from the record
    col = rec.get('color') or rec.get('material_color') or [150 + seed % 60, 140, 120 + (seed >> 4) % 80]
    p = P(s, tuple(col), rigs.shade(tuple(col), -2), 'metal', 'streak', None, seed)
    for key, t in KEYWORDS:
        if key in rid:
            return render(t, p, s)
    return render('shield' if rec.get('category') == 'shield' else 'breastplate', p, s)


if __name__ == '__main__':
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0
    for r in recs:
        im = draw(r)
        assert im.size == (32, 32) and im.mode == 'RGBA', r['id']
        assert im.getbbox() is not None, 'blank ' + r['id']
        d = os.path.join(HERE, 'out', r['folder'])
        os.makedirs(d, exist_ok=True)
        im.save(os.path.join(d, r['id'] + '.png'))
        n += 1
    print('wrote %d of %d' % (n, len(recs)))
