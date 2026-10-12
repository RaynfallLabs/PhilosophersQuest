"""Split the monsters that have no brief yet into work groups of related creatures.

    python tools/content/genart/make_groups.py [group size]

Writes _genart/groups/gNN.json: for each monster the facts a brief is written from
(name, level, tags, attack names, boss flags, lore). Relatives stay together so a
family's tiers are designed, drawn and reviewed side by side.
"""
import collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
mons = {k: v for k, v in json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8')).items()
        if isinstance(v, dict)}
done = set()
bdir = os.path.join(ROOT, 'tools', 'content', 'genart', 'briefs')
for f in os.listdir(bdir):
    if f.endswith('.json'):
        done |= {b['id'] for b in json.load(open(os.path.join(bdir, f), encoding='utf-8'))}

# A family is the rarest tag a monster shares with at least one other; failing that,
# the last word of its id (red_dragon -> dragon).
tagc = collections.Counter(t for v in mons.values() for t in v.get('tags', []))
wordc = collections.Counter(w for k in mons for w in set(k.split('_')))
BROAD = {'humanoid', 'beast', 'undead', 'caster', 'demon', 'boss', 'flying', 'aquatic', 'construct', 'elemental',
         'dragon', 'giant', 'fey', 'plant', 'insect', 'spirit', 'shapeshifter', 'magical', 'animal'}


def family(k, v):
    words = [w for w in k.split('_') if wordc[w] >= 2 and len(w) > 2]
    if words:
        return min(words, key=lambda w: (wordc[w] > 14, -wordc[w] if wordc[w] <= 14 else wordc[w], w))
    narrow = [t for t in v.get('tags', []) if tagc[t] >= 2 and t not in BROAD]
    if narrow:
        return min(narrow, key=lambda t: (tagc[t], t))
    broad = [t for t in v.get('tags', []) if t in BROAD]
    return 'zz_' + (min(broad, key=lambda t: (tagc[t], t)) if broad else 'misc')


rows = []
for k, v in mons.items():
    if k in done:
        continue
    rows.append((family(k, v), v.get('min_level', 0), k))
rows.sort()
groups, cur, last = [], [], None
for fam, lvl, k in rows:
    if len(cur) >= size and fam != last:
        groups.append(cur); cur = []
    cur.append((fam, k)); last = fam
if cur:
    groups.append(cur)
out = os.path.join(ROOT, '_genart', 'groups')
os.makedirs(out, exist_ok=True)
for i, g in enumerate(groups, 1):
    data = []
    for fam, k in g:
        v = mons[k]
        data.append({'id': k, 'suggested_family': fam, 'name': v.get('name'), 'min_level': v.get('min_level'), 'hp': v.get('hp'),
                     'tags': v.get('tags'), 'attacks': [f"{a.get('name')} ({a.get('type', '')})" for a in v.get('attacks', [])],
                     'boss': bool(v.get('is_boss')), 'mini_boss': bool(v.get('is_mini_boss')),
                     'seal_demon': bool(v.get('is_seal_demon')), 'footprint': v.get('footprint'),
                     'resistances': v.get('resistances'), 'weaknesses': v.get('weaknesses'), 'lore': v.get('lore')})
    json.dump(data, open(os.path.join(out, f'g{i:02d}.json'), 'w', encoding='utf-8'), indent=1)
    fams = collections.Counter(f for f, _ in g)
    print(f'g{i:02d}: {len(g)} monsters;', ', '.join(f'{f}×{n}' for f, n in fams.most_common(8)))
print(len(rows), 'monsters in', len(groups), 'groups;', len(done), 'already have briefs')
