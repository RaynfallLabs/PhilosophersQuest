"""Magic slice: rings, amulets, wands, potions, scrolls, spellbooks, artifacts, containers.
draw(rec) -> 32x32 RGBA.  `python magic.py` writes out/<folder>/<id>.png for every record in slice.json."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import mg_rigs
from mg_rigs import wand, potion, scroll, dead_sea_scroll, book, chest
from mg_jewel import stat_ring, stat_amulet
from mg_named import NAMED

_SLICE = os.path.join(HERE, 'slice.json')
if os.path.exists(_SLICE):
    for _r in json.load(open(_SLICE, encoding='utf-8')):
        if _r.get('color'): mg_rigs.COLORS[_r['id']] = tuple(_r['color'][:3])


def draw(rec):
    i, cat = rec['id'], rec.get('category')
    if i in NAMED: return NAMED[i](rec)
    if i == 'dead_sea_scroll': return dead_sea_scroll(rec)
    if i.startswith('wand_') or cat == 'wand': return wand(rec)
    if i.startswith('potion_') or cat == 'potion': return potion(rec)
    if i.startswith('scroll_') or cat == 'scroll': return scroll(rec)
    if i.startswith('spellbook_') or cat == 'spellbook': return book(rec)
    if cat == 'container' or 'chest' in i or 'coffer' in i or 'vault' in i: return chest(rec)
    if i.startswith('ring_') or rec.get('slot') == 'ring' or cat == 'ring': return stat_ring(rec)
    return stat_amulet(rec)


if __name__ == '__main__':
    recs = json.load(open(_SLICE, encoding='utf-8'))
    n = 0
    for r in recs:
        im = draw(r)
        assert im.size == (32, 32) and im.mode == 'RGBA' and im.getbbox(), r['id']
        d = os.path.join(HERE, 'out', r['folder']); os.makedirs(d, exist_ok=True)
        im.save(os.path.join(d, r['id'] + '.png')); n += 1
    print('wrote', n, 'of', len(recs))
