"""Tier census of every content system (Brandon, 2026-11-16: "Every single one
should have a good distribution across all tiers... every time I ask, you
come back and say things like 'recipes are clustered at tier one'").

One definition of tier for everything: the band of the floor where a thing
is FOUND, one tier per 20 floors, tier = (floor - 1) // 20 + 1 (his rule:
"I absolutely expect the TIER to be appropriate to the average level of the
dungeon where an item is found").

  * items: the spawn-weighted mean floor (floorSpawnWeight), else
    peak_floor, else min_level; 0 or past 100 (quest, plot, starting kit,
    shop only) is "not dropped" and not counted;
  * monsters: peak_floor, else min_level (ordinary kinds, mini-bosses and
    bosses apart, and every family on its own);
  * dishes: their own tier (kitchen.dish_tier: the band of the deepest
    ingredient, a tier more for a dish of four parts or more), by tab
    and, for stat dishes, by stat;
  * spells: their own tier (spells.LEARNABLE_SPELLS);
  * encounters: min_level, or the middle of an NPC's 10-floor block.

It also counts the items whose own quiz tier is two or more tiers from
where they are found (rule 2 again).

The gate is tests/test_tier_distribution.py. Pure reading: changes nothing.

    py tools/balance/tier_census.py            # the table
    py tools/balance/tier_census.py --md out.md
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(ROOT, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, 'src'))

# The target (Brandon 2026-11-16): a category of 10 or more holds at least
# MIN_SHARE of its kinds in every tier and no more than MAX_SHARE in any one;
# a smaller one (or a sub-group) holds at least one in every tier.
MIN_SHARE = 0.10
MAX_SHARE = 0.35
SMALL = 10


def _p(*parts) -> str:
    return os.path.join(ROOT, *parts)


def band(floor) -> int | None:
    try:
        f = float(floor)
    except (TypeError, ValueError):
        return None
    if f <= 0 or f > 100:
        return None
    return max(1, min(5, int((f - 1) // 20) + 1))


def _mid(key):
    try:
        a, b = str(key).split('-')
        return (float(a) + float(b)) / 2
    except ValueError:
        try:
            return float(key)
        except ValueError:
            return None


def found_floor(row: dict):
    """Where a data row is found: spawn-weighted mean floor, else peak, else min."""
    w = row.get('floorSpawnWeight') or row.get('floor_spawn_weight')
    if isinstance(w, dict) and w:
        pairs = [(_mid(k), float(v)) for k, v in w.items()
                 if isinstance(v, (int, float)) and v > 0 and _mid(k) is not None]
        tot = sum(v for _m, v in pairs)
        if tot > 0:
            return sum(m * v for m, v in pairs) / tot
    for k in ('peak_floor', 'min_level'):
        v = row.get(k)
        if isinstance(v, (int, float)):
            return v
    return None


def _rows(path: str) -> list:
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, list):
        return [r for r in d if isinstance(r, dict)]
    if isinstance(d.get('items'), list):
        return [r for r in d['items'] if isinstance(r, dict)]
    return [dict(v, _key=k) for k, v in d.items() if isinstance(v, dict) and not k.startswith('_')]


def verdict(counts: list) -> str:
    """'ok', or why not: 'empty', 'gap' (a tier with none), 'lopsided'."""
    n = sum(counts)
    if n == 0:
        return 'empty'
    if min(counts) == 0:
        return 'gap'
    if n < SMALL:
        return 'ok'
    share = [c / n for c in counts]
    if max(share) > MAX_SHARE or min(share) < MIN_SHARE:
        return 'lopsided'
    return 'ok'


def census() -> dict:
    """{'rows': [{'category', 'group', 'counts' (T1..T5), 'not_dropped',
    'mismatch' (items 2+ tiers from where found), 'checked' (items with an
    own tier), 'verdict'}], 'spell_families': {family: [tiers]}}."""
    rows = []

    def add(cat, tiers, none=0, mis=0, checked=0, group='main'):
        c = collections.Counter(t for t in tiers if t)
        counts = [c.get(i, 0) for i in range(1, 6)]
        rows.append({'category': cat, 'group': group, 'counts': counts, 'not_dropped': none,
                     'mismatch': mis, 'checked': checked, 'verdict': verdict(counts)})

    def items_file(fname, cat, filt=None):
        tiers, none, mis, checked = [], 0, 0, 0
        for r in _rows(_p('data', 'items', fname)):
            if filt and not filt(r):
                continue
            t = band(found_floor(r))
            if t is None:
                none += 1
                continue
            tiers.append(t)
            own = next((r.get(k) for k in ('quiz_tier', 'tier') if isinstance(r.get(k), int)), None)
            if own:
                checked += 1
                if abs(int(own) - t) >= 2:
                    mis += 1
        add(cat, tiers, none, mis, checked)

    # Monsters.
    mons = json.load(open(_p('data', 'monsters.json'), encoding='utf-8'))
    ordinary, minib, bosses = [], [], []
    fam = collections.defaultdict(list)
    none = 0
    for k, m in mons.items():
        if not isinstance(m, dict) or k.startswith('_'):
            continue
        t = band(m.get('peak_floor') or m.get('min_level'))
        if t is None:
            none += 1
            continue
        if m.get('is_boss'):
            bosses.append(t)
        elif m.get('is_mini_boss'):
            minib.append(t)
        else:
            ordinary.append(t)
            fam[m.get('family') or 'none'].append(t)
    add('Monsters (ordinary kinds)', ordinary, none)
    add('Mini-bosses', minib)
    add('Bosses', bosses)
    for f in sorted(fam):
        add(f'Monster family: {f}', fam[f], group='family')

    # Items.
    items_file('weapon.json', 'Weapons (uniques)')
    items_file('armor.json', 'Armour (uniques)')
    items_file('shield.json', 'Shields (uniques)')
    items_file('accessory.json', 'Rings', filt=lambda r: r.get('slot') == 'ring')
    items_file('accessory.json', 'Amulets', filt=lambda r: r.get('slot') == 'amulet')
    items_file('accessory.json', 'Belts and other accessories',
               filt=lambda r: r.get('slot') not in ('ring', 'amulet'))
    items_file('wand.json', 'Wands')
    items_file('scroll.json', 'Scrolls')
    items_file('potion.json', 'Potions')
    items_file('spellbook.json', 'Spellbooks')
    items_file('flask.json', 'Flasks (coatings, thrown)')
    items_file('ammo.json', 'Ammo')
    items_file('food.json', 'Plain food')
    items_file('treasure.json', 'Treasure')
    items_file('artifact.json', 'Artifacts')
    items_file('container.json', 'Containers')
    items_file('ingredient.json', 'Ingredients')

    # Materials: the commons are a template in a material.
    for kind in ('weapons', 'armor'):
        tiers, none = [], 0
        for f in sorted(glob.glob(_p('data', 'materials', kind, '*.json'))):
            r = json.load(open(f, encoding='utf-8'))
            t = band(found_floor(r) if isinstance(r, dict) else None)
            if t is None:
                none += 1
            else:
                tiers.append(t)
        add(f'Materials ({kind})', tiers, none)

    # Spells.
    import spells
    sp = getattr(spells, 'LEARNABLE_SPELLS', {})
    add('Spells', [int(s.get('tier') or 0) for s in sp.values()])
    fam_sp = collections.defaultdict(set)
    for s in sp.values():
        fam_sp[s.get('spell_family') or '?'].add(int(s.get('tier') or 0))

    # Dishes: the kitchen's own tier (kitchen.dish_tier).
    import kitchen as K
    by_tab, by_stat = collections.defaultdict(list), collections.defaultdict(list)
    for rid in K.raw_recipes():
        r = K.recipe(rid)
        if not r:
            continue
        t = K.dish_tier(r)
        by_tab[K.dish_tab(r)].append(t)
        if K.dish_tab(r) == 'stat':
            by_stat[K.dish_stat(r)].append(t)
    for tab, label in (('hp', 'HP'), ('sp', 'SP'), ('mp', 'MP'), ('stat', 'Stat'),
                       ('special', 'Special')):
        add(f'Dishes: {label}', by_tab[tab])
    for st in sorted(by_stat):
        add(f'Dishes: Stat {st}', by_stat[st], group='stat')

    # Encounters.
    for fname, cat in (('npc_encounters.json', 'NPC encounters'),
                       ('flavor_encounters.json', 'Flavor encounters')):
        d = json.load(open(_p('data', fname), encoding='utf-8'))
        es = d if isinstance(d, list) else (d.get('encounters') or
                                            [v for v in d.values() if isinstance(v, dict)])
        ts, none = [], 0
        for e in es:
            if not isinstance(e, dict):
                continue
            lvl = e.get('min_level')
            if lvl is None and e.get('block') is not None:
                lvl = (int(e['block']) - 1) * 10 + 5
            t = band(lvl)
            if t is None:
                none += 1
            else:
                ts.append(t)
        add(cat, ts, none)

    return {'rows': rows, 'spell_families': {f: sorted(t) for f, t in sorted(fam_sp.items())}}


def table(result: dict) -> str:
    out = ['| Category | T1 | T2 | T3 | T4 | T5 | Not dropped | Verdict | Quiz tier 2+ off |',
           '|---|---|---|---|---|---|---|---|---|']
    for r in result['rows']:
        n = sum(r['counts'])
        cells = [f"{c} ({round(100 * c / n)}%)" if n else '0' for c in r['counts']]
        mis = f"{r['mismatch']} of {r['checked']}" if r['checked'] else ''
        out.append(f"| {r['category']} | " + ' | '.join(cells)
                   + f" | {r['not_dropped']} | {r['verdict']} | {mis} |")
    gaps = [f"{f} {t}" for f, t in result['spell_families'].items() if len(t) < 5]
    out += ['', 'Spell families missing a tier: ' + '; '.join(gaps)]
    return '\n'.join(out)


if __name__ == '__main__':
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    text = table(census())
    print(text)
    if '--md' in sys.argv:
        open(sys.argv[sys.argv.index('--md') + 1], 'w', encoding='utf-8').write(text + '\n')
