"""Install the reviewed item sprites.

    <ComfyUI python> tools/content/genart/install_items.py [--to <game root>] [--dry] [--merge]

Four kinds of item:
  single    one reviewed picture per item id (named weapons and armour, magic items,
            food, oddments): copied.
  template  a weapon or armour shape the game makes in many materials. Its one grey
            picture is tinted with each material's colour (recolour.tint).
  mapped    prime cuts and cooked dishes: many items share a picture, by the
            map.json their group wrote.
  object    containers that sit on the floor and the trader: copied as they are.

Sprites go to assets/tiles/items (the trader to assets/tiles/monsters). What was
written is listed in tools/content/genart/installed_items.json. An item with no
reviewed picture is left alone and reported.

--merge adds to installed_items.json instead of rewriting it: for a later batch run
from a _genart/items that holds only that batch's groups (bug bash 4 drew i26-i29
that way in a worktree, leaving every earlier item untouched).
"""
import argparse, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'art'))
import recolour
import manifest
import make_item_groups as groups

GEN = os.path.join(ROOT, '_genart', 'items')
# materials the data files do not colour (ids like diamond_longsword, wood_club)
EXTRA_MATERIALS = {'diamond': (190, 228, 245), 'wood': (140, 100, 60), 'hardwood': (110, 75, 45),
                   'bone': (226, 216, 190)}
ELSEWHERE = {'merchant_npc': 'monsters'}


def reviewed():
    """{brief id: path of the picked sprite} over every item group, and every map.json merged."""
    picks, mapped = {}, {}
    for g in sorted(os.listdir(GEN)):
        d = os.path.join(GEN, g)
        rv = os.path.join(d, 'review.json')
        if not os.path.exists(rv):
            continue
        for iid, v in json.load(open(rv, encoding='utf-8')).items():
            if v.get('pick'):
                p = os.path.join(d, iid, f"c{v['pick']}_sprite.png")
                if os.path.exists(p):
                    picks[iid] = p
        mp = os.path.join(d, 'map.json')
        if os.path.exists(mp):
            mapped.update(json.load(open(mp, encoding='utf-8')))
    return picks, mapped


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--to', default=ROOT); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--merge', action='store_true')
    a = ap.parse_args()
    picks, mapped = reviewed()
    recs = [r for r in manifest.build() if r['folder'] == 'items']
    colours = dict(EXTRA_MATERIALS)
    for r in recs:
        if r.get('material') and r.get('material_color'):
            colours.setdefault(r['material'], tuple(r['material_color']))
    out, missing, tints = {'items': [], 'monsters': []}, [], {}
    dst = lambda folder: os.path.join(a.to, 'assets', 'tiles', folder)

    def put(iid, img, folder='items'):
        if not a.dry:
            img.save(os.path.join(dst(folder), iid + '.png'))
        out[folder].append(iid)

    for r in recs:
        iid = r['id']
        if iid.startswith(groups.DONE):                       # shrines and the first ten chests: install_tiles.py
            continue
        if iid in picks:                                      # its own reviewed picture
            put(iid, Image.open(picks[iid]), ELSEWHERE.get(iid, 'items'))
            continue
        if iid in mapped:                                     # a shared picture
            src = picks.get(mapped[iid])
            if src:
                put(iid, Image.open(src))
            else:
                missing.append((iid, 'its shared picture ' + mapped[iid] + ' has no pick'))
            continue
        loose = groups.loose(iid)
        if r['kind'] in ('weapon', 'armor') and (r.get('combo') or loose):
            mat, tpl = (r.get('material'), r.get('template')) if r.get('combo') else loose
            base = picks.get(('tpl_w_' if r['kind'] == 'weapon' else 'tpl_a_') + tpl)
            col = tuple(r['material_color']) if r.get('material_color') else colours.get(mat)
            if base and col:
                key = (base, col)
                if key not in tints:
                    tints[key] = recolour.tint(Image.open(base), col)
                put(iid, tints[key])
            else:
                missing.append((iid, f'no template picture for {tpl}' if not base else f'no colour for material {mat}'))
            continue
        missing.append((iid, 'no reviewed picture'))
    # pictures reviewed but not in the manifest's item list (the trader)
    for iid, folder in ELSEWHERE.items():
        if iid in picks and iid not in out[folder]:
            put(iid, Image.open(picks[iid]), folder)
    if not a.dry and os.path.abspath(a.to) == os.path.abspath(ROOT):
        listed = os.path.join(HERE, 'installed_items.json')
        done = {k: set(v) for k, v in out.items()}
        if a.merge and os.path.exists(listed):
            for k, v in json.load(open(listed, encoding='utf-8')).items():
                done.setdefault(k, set()).update(v)
        json.dump({k: sorted(v) for k, v in done.items()}, open(listed, 'w', encoding='utf-8'), indent=0)
    print(('would install' if a.dry else 'installed'), len(out['items']), 'items,', len(out['monsters']), 'elsewhere;',
          len(tints), 'template tints made;', len(missing), 'left alone')
    why = {}
    for iid, reason in missing:
        why.setdefault(reason.split(' for ')[0] if reason.startswith('no ') else reason, []).append(iid)
    for reason, ids in sorted(why.items(), key=lambda kv: -len(kv[1])):
        print(f'  {len(ids):4d}  {reason}:', ', '.join(ids[:6]) + (' ...' if len(ids) > 6 else ''))


if __name__ == '__main__':
    main()
