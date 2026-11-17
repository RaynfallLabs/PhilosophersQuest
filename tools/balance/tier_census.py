"""Tier census of every content system (Brandon, 2026-11-16: "Every single one
should have a good distribution across all tiers... every time I ask, you
come back and say things like 'recipes are clustered at tier one'").

One definition of tier for everything: the band of the floor where a thing
is FOUND, one tier per 20 floors, tier = (floor - 1) // 20 + 1 (his rule:
"I absolutely expect the TIER to be appropriate to the average level of the
dungeon where an item is found").

  * items: the mean floor of the item's weight in the floor's random pool,
    by the game's own rule (dungeon.floor_spawn_weight: a unique's peak
    bell first, else its band weights, never below its min_level; food by
    its bands, a Soul Sphere by its floor_spawn_chance). Until 2026-11-17
    the census read the bands first, where the game reads the bell: it
    counted fifteen rings in tier 5 that the game drops on floors 70-80 on
    average, and no ring was really a tier-5 find. A piece
    that is never rolled (a quest piece, an encounter's gift, a mini-boss's
    signature drop) is found where its story puts it: its `story_floor`
    (the floor dungeon.py puts it on), else the encounter or mystery altar
    that hands it over, else the mini-boss that drops it (its peak_floor),
    else its peak_floor or min_level. Nowhere (0 or past 100: starting kit,
    shop only, locked) is "not dropped" and not counted;
  * containers: the chest kinds a floor really rolls (data/chest_templates.json,
    by spawn_weight_by_band; data/items/container.json is the old schema);
  * monsters: peak_floor, else min_level (ordinary kinds, mini-bosses and
    bosses apart, and every family on its own);
  * dishes: their own tier (kitchen.dish_tier: the band of the deepest
    ingredient, a tier more for a dish of four parts or more), by tab
    and, for stat dishes, by stat;
  * spells: their own tier (spells.LEARNABLE_SPELLS);
  * encounters: min_level, or the middle of an NPC's 10-floor block.

It also counts the items whose own quiz tier is two or more tiers from
where they are found (rule 2 again): loot only. A story piece's tier is its
story's choice, and a ring or amulet KIND has no tier until it is found
(rings.dress rolls its level, and so its tier, by the floor).

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


def _spawn_fields(row: dict):
    """The spawn fields of a data row as the game's Item reads them
    (items.Item.__init__: the same defaults)."""
    from types import SimpleNamespace
    return SimpleNamespace(
        min_level=int(row.get('min_level', 1) or 0),
        peak_floor=int(row.get('peak_floor', 0) or 0),
        spread=int(row.get('spread', 10) or 10),
        peak_weight=float(row.get('peak_weight', 0.0) or 0.0),
        floor_spawn_weight=row.get('floor_spawn_weight', row.get('floorSpawnWeight', {})) or {})


def _band_at(bands: dict, f: int) -> float:
    """A range-keyed dict's value on floor `f` ({"1-33": 0.08, ...})."""
    for key, v in bands.items():
        parts = str(key).split('-')
        try:
            lo = int(parts[0])
            hi = int(parts[1]) if len(parts) > 1 else lo
        except ValueError:
            continue
        if lo <= f <= hi:
            return float(v or 0)
    return 0.0


def _mean_floor(weight_at) -> float | None:
    tot = s = 0.0
    for f in range(1, 101):
        w = float(weight_at(f) or 0)
        if w > 0:
            tot += w
            s += w * f
    return s / tot if tot > 0 else None


_GIVEN_KEYS = ('reward', 'rewards')
_given_cache: dict | None = None


def _given_by_encounters() -> dict:
    """{item id: the floor where an encounter hands it over}: the middle of
    the band of the shallowest flavor or NPC encounter whose reward is that
    item, or that has the hero accept it (a cost of type accept_item: an
    oath's errand). An NPC's band is its 10-floor block. An item an encounter
    only asks for (a cost, a trigger, an oath to fetch it) is not given there."""
    global _given_cache
    if _given_cache is not None:
        return _given_cache
    out: dict = {}

    def walk(o, under_given, hits):
        if isinstance(o, dict):
            if o.get('type') == 'accept_item' and isinstance(o.get('item_id'), str):
                hits.add(o['item_id'])
            for k, v in o.items():
                if k == 'item_id' and under_given and isinstance(v, str):
                    hits.add(v)
                walk(v, under_given or k in _GIVEN_KEYS, hits)
        elif isinstance(o, list):
            for v in o:
                walk(v, under_given, hits)

    for fname in ('flavor_encounters.json', 'npc_encounters.json'):
        d = json.load(open(_p('data', fname), encoding='utf-8'))
        es = d if isinstance(d, list) else (d.get('encounters') or
                                            [v for v in d.values() if isinstance(v, dict)])
        for e in es:
            if not isinstance(e, dict):
                continue
            if e.get('min_level') is not None:
                lo = float(e['min_level'])
                hi = float(e.get('max_level') or lo)
            elif e.get('block') is not None:
                lo = (int(e['block']) - 1) * 10 + 1
                hi = lo + 9
            else:
                continue
            hits: set = set()
            walk(e, False, hits)
            for iid in hits:
                floor = (lo + hi) / 2
                if iid not in out or lo < out[iid][0]:
                    out[iid] = (lo, floor)
    # A mystery altar's prize (mystery_system.MYSTERIES: a reward 'special'
    # that is an item, as Solomon's Tribunal gives the Ring of Command).
    try:
        import mystery_system
        for spec in mystery_system.MYSTERIES.values():
            sp = (spec.get('reward') or {}).get('special')
            rng_ = spec.get('floor_range')
            if isinstance(sp, str) and rng_:
                lo, hi = float(rng_[0]), float(rng_[1])
                if sp not in out or lo < out[sp][0]:
                    out[sp] = (lo, (lo + hi) / 2)
    except Exception:
        pass
    _given_cache = {k: f for k, (_lo, f) in out.items()}
    return _given_cache


_dropped_cache: dict | None = None


def _dropped_by_mini_bosses() -> dict:
    """{item id: the floor of the named foe that drops it on the kill}
    (treasure.unique_drop_id: a mini-boss's signature drop is found where the
    mini-boss lives, its peak_floor; ruling 13, 2026-11-16)."""
    global _dropped_cache
    if _dropped_cache is None:
        out = {}
        mons = json.load(open(_p('data', 'monsters.json'), encoding='utf-8'))
        for m in mons.values():
            if not isinstance(m, dict):
                continue
            iid = (m.get('treasure') or {}).get('unique_drop_id')
            floor = m.get('peak_floor') or m.get('min_level')
            if iid and isinstance(floor, (int, float)) and 1 <= floor <= 100:
                out[iid] = float(floor)
        _dropped_cache = out
    return _dropped_cache


def story_floor(row: dict):
    """Where a piece that is never rolled is found: its own `story_floor`
    (the floor its quest puts it on, dungeon.spawn_items), else the floor
    where an encounter hands it over, else the floor of the mini-boss that
    drops it, else None."""
    v = row.get('story_floor')
    if isinstance(v, (int, float)) and v > 0:
        return float(v)
    iid = row.get('id') or row.get('_key')
    given = _given_by_encounters().get(iid)
    if given is not None:
        return given
    return _dropped_by_mini_bosses().get(iid)


def found_floor(row: dict, food: bool = False):
    """Where a data row is found: the mean floor of its weight in the floor's
    random pool, by the game's own rule (dungeon.floor_spawn_weight: the
    peak bell first, else the band weights, never below min_level; food by
    its bands alone, as dungeon._food_eligible reads it; a Soul Sphere by its
    floor_spawn_chance). A row with no spawn weight at all, or a story piece
    (a plot_role other than a wonder relic), is found where its story puts it:
    its story_floor or the encounter that gives it (story_floor()), else its
    peak_floor, else its min_level."""
    import dungeon
    fsc = row.get('floor_spawn_chance')
    if isinstance(fsc, dict) and fsc:
        ml = int(row.get('min_level', 1) or 0)
        m = _mean_floor(lambda f: _band_at(fsc, f) if f >= ml else 0)
        if m is not None:
            return m
    it = _spawn_fields(row)
    role = (row.get('special_properties') or {}) if isinstance(row.get('special_properties'), dict) else {}
    if role.get('plot_role') and role.get('plot_role') != 'wonder_relic':
        m = None                     # a story piece: never rolled (items.scripted_only_ids)
    elif food:
        m = _mean_floor(lambda f: dungeon._food_weight(it.floor_spawn_weight, f)
                        if f >= it.min_level else 0)
    elif it.peak_weight > 0 or any(
            isinstance(v, (int, float)) and v > 0 for v in it.floor_spawn_weight.values()):
        m = _mean_floor(lambda f: dungeon.floor_spawn_weight(it, f))
    else:
        m = None
    if m is not None:
        return m
    s = story_floor(row)
    if s is not None:
        return s
    for k in ('peak_floor', 'min_level'):
        v = row.get(k)
        if isinstance(v, (int, float)):
            return v
    return None


def is_story(row: dict) -> bool:
    """True for a piece that is never rolled: a plot_role other than a wonder
    relic, or no spawn weight of any kind (items.scripted_only_ids)."""
    sp = row.get('special_properties')
    role = sp.get('plot_role') if isinstance(sp, dict) else None
    if role and role != 'wonder_relic':
        return True
    if row.get('floor_spawn_chance'):
        return False
    if float(row.get('peak_weight', 0) or 0) > 0:
        return False
    fw = row.get('floor_spawn_weight', row.get('floorSpawnWeight')) or {}
    return not any(isinstance(v, (int, float)) and v > 0 for v in fw.values())


_CHEST_BANDS = {'L1_15': (1, 15), 'L16_30': (16, 30), 'L31_50': (31, 50),
                'L51_70': (51, 70), 'L71_90': (71, 90), 'L91_100': (91, 100)}


def chest_floor(tdef: dict):
    """Where a chest kind is found: the mean floor of its spawn_weight_by_band
    (data/chest_templates.json, read by dungeon.pick_container)."""
    w = tdef.get('spawn_weight_by_band') or {}

    def at(f):
        for k, (lo, hi) in _CHEST_BANDS.items():
            if lo <= f <= hi:
                return float(w.get(k, 0) or 0)
        return 0.0
    return _mean_floor(at)


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

    def items_file(fname, cat, filt=None, rows_in=None, where=None):
        tiers, none, mis, checked = [], 0, 0, 0
        for r in (rows_in if rows_in is not None else _rows(_p('data', 'items', fname))):
            if filt and not filt(r):
                continue
            t = band(where(r) if where else found_floor(r, food=(fname == 'food.json')))
            if t is None:
                none += 1
                continue
            tiers.append(t)
            own = next((r.get(k) for k in ('quiz_tier', 'tier') if isinstance(r.get(k), int)), None)
            # Rule 2 is about loot: a story piece's tier is its story's
            # choice (the tempting sword a dying knight hands over), and a
            # ring or amulet KIND has no tier of its own until it is found
            # (rings.dress rolls its level, and so its tier, by the floor).
            if own and (where or not is_story(r)) and not r.get('kind'):
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
    # Containers: the chest kinds a floor really rolls (dungeon.pick_container
    # draws from data/chest_templates.json by band; data/items/container.json
    # is the old schema, never rolled).
    items_file('chest_templates.json', 'Containers',
               rows_in=_rows(_p('data', 'chest_templates.json')), where=chest_floor)
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
