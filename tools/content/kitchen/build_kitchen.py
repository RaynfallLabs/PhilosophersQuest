"""Build the kitchen: ingredients, the harvest map and the recipe book.

The kitchen rebuild (COOKING_REBUILD_PLAN_2026_11_14, slice K1). Three steps:

1. ``py tools/content/kitchen/build_kitchen.py --structure``
   Generates the recipe book's STRUCTURE (which ingredients go into which
   dish: every ingredient in one single dish and at least two multi-ingredient
   dishes, a third of the multi-dishes joining an early part with a deep one,
   the legendary feasts) and freezes it in ``structure.json``. It also writes
   ``dish_skeleton.txt``, the list of multi-dishes to name. Run it once; the
   dish ids it makes are what ``dishes.txt`` names, so re-running it means
   renaming.
2. Write ``dishes_1.txt`` / ``dishes_2.txt`` by hand: ``dish_id | Name |
   flavour line``. Names and flavour are content, not a template mash. (One
   dish, dish_221, was added to structure.json by hand after the run: Goblin
   Gristle's floor-3-to-floor-86 pie.)
3. ``py tools/content/kitchen/build_kitchen.py``
   Merges the frozen structure, the ingredient content (``ingredients_*.txt``)
   and the dish names into the game data, and checks every rule:
     data/items/ingredient.json   every ingredient (monster parts, trophies, forage)
     data/items/harvest_map.json  monster -> ingredient, and old ids -> kept ids
     data/items/recipes.json      the recipe book
   The numbers a dish gives live in data/cooking_rules.json (hand-written),
   never here.

Inputs: data/monsters.json, data/items/food.json, the OLD ingredient.json
(colours; read from git's copy in ``old_ingredients.json`` once the data has
been rebuilt), kin_groups.txt, ingredients_*.txt.

Each dish's picture (``art``) comes from ``dish_art.py``: the kind its name
says, at its tier and main benefit (a legendary feast has its own, a trophy
dish its boss's). The build writes the result to ``dish_art.json``.
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dish_art  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(ROOT, 'data')
ITEMS = os.path.join(DATA, 'items')
ART_DIR = os.path.join(ROOT, 'assets', 'tiles', 'items')

STATS = ('STR', 'DEX', 'CON', 'INT', 'WIS', 'PER')
TABS = ('hp', 'sp', 'mp', 'stat', 'special')
RESISTS = ('fire_resist', 'cold_resist', 'shock_resist', 'poison_resist', 'acid_resist',
           'magic_resist', 'drain_resist', 'sleep_resist')

# The fourteen boss trophies: their nature in the kitchen. The permanent
# power each grants is the trophy's own (food_system._apply_permanent_power).
TROPHIES = {
    'asterion_minotaur': ('STR', 'plus_2_str_confuse_immune'),
    'medusa_gorgon': ('save_guard_CON', 'petrify_immunity'),
    'fafnir_dragon': ('hp', 'max_hp_per_floor_descent'),
    'fenrir_wolf': ('STR', 'plus_3_str'),
    'abaddon_destroyer': ('INT', 'all_stats_plus_1'),
    'green_knight': ('hp', 'revive_once_at_half_hp'),
    'nidhoggr_fragment': ('mp', 'max_mp_per_floor_descent_and_poison_immunity'),
    'whispering_crone': ('WIS', 'plus_2_wis_auto_reveal_secret_doors'),
    'blood_archon': ('hp', 'lifesteal_5pct_on_melee'),
    'tiamat': ('fire_resist', 'chromatic_resist_all'),
    'asmodeus': ('save_guard_all', 'one_time_death_save'),
    'surtur': ('fire_resist', 'fire_immunity'),
    'ymir_last_spawn': ('cold_resist', 'cold_immunity'),
    'hrungnirs_ghost': ('CON', 'plus_2_con_petrify_immune'),
}
# The second benefit a trophy's other feast leans to (a feast never gives SP
# as its main benefit: its permanent is max HP, max MP, a stat or a resistance).
TROPHY_SECOND = {
    'asterion_minotaur': 'hp', 'medusa_gorgon': 'WIS', 'fafnir_dragon': 'fire_resist',
    'fenrir_wolf': 'hp', 'abaddon_destroyer': 'mp', 'green_knight': 'regenerating',
    'nidhoggr_fragment': 'poison_resist', 'whispering_crone': 'mp', 'blood_archon': 'STR',
    'tiamat': 'mp', 'asmodeus': 'hp', 'surtur': 'STR', 'ymir_last_spawn': 'CON',
    'hrungnirs_ghost': 'hp',
}
# Boss parts (not trophies) that anchor a legendary feast of their own.
BOSS_FEASTS = ('seal_demon_wrath', 'seal_demon_pestilence', 'seal_demon_famine', 'seal_demon_war',
               'seal_demon_death', 'seal_demon_earthquake', 'seal_demon_silence', 'baba_yaga')
# Kept-picture overrides: a creature with no picture of its own takes an
# unused one that shows the same kind of part.
KEPT_OVERRIDE = {'calydonian_boar': 'asterion_minotaur_prime'}
# Kinds whose parts are secret: the cow level. A dish needing one never shows
# as "building toward" until the hero holds that part (kitchen.menu_rows).
SECRET_KEYS = ('hell_bovine', 'cow_king')

# Common food that goes into dishes (data/items/food.json). Quest, secret and
# one-shot food (the dungeon carrot, the Tantalus plum, the peach, ambrosia,
# the golden apple) is never an ingredient. (nature it leans to, first floor.)
FOOD = {
    'bread_ration': ('sp', 1), 'dried_meat': ('sp', 1), 'hard_cheese': ('hp', 1),
    'wild_mushroom': ('sp', 1), 'apple': ('hp', 1), 'trail_rations': ('sp', 1),
    'healing_herb': ('hp', 3), 'elvish_bread': ('mp', 10), 'philosopher_tea': ('mp', 15),
    'deep_fungi': ('stat', 35), 'void_ration': ('sp', 60),
}
# Rare food turns up in few dishes (it is rarely found).
FOOD_RARITY = {'philosopher_tea': 0.15, 'deep_fungi': 0.3, 'void_ration': 0.3, 'elvish_bread': 0.6}
FORBIDDEN_FOOD = ('magic_dungeon_carrot', 'tantalus_plum', 'peach_of_immortality', 'ambrosia',
                  'golden_apple', 'hearty_stew')

BANNED_WORDS = ('Prime Cut', 'Choice Cut', 'Pristine', 'Pure', 'Concentrated', 'Engorged', 'Glittering')

# Every name keeps the kind of part its picture shows (the old name's last
# words told what the picture was): one of these words is in the name.
PART_WORDS = {
    'cut': ('Steak', 'Leg', 'Drumstick', 'Drumette', 'Ham', 'Haunch', 'Hock', 'Loin', 'Roll', 'Shank',
            'Rump', 'Sausage', 'Links', 'Bangers', 'Bacon', 'Gristle', 'Medallion', 'Joint', 'Claw-Leg',
            'Glow-Leg', 'Sirloin'),
    'bone': ('Bone', 'Shank', 'Femur', 'Knucklebone', 'Marrow', 'Ectoplasm', 'Jelly', 'Ribbone',
             'Thighbone', 'Shinbone'),
    'ichor': ('Ichor', 'Bile', 'Blood', 'Brine', 'Venom', 'Hellblood'),
    'sac': ('Sac', 'Gland', 'Bladder', 'Bulb', 'Pouch', 'Eye', 'Stomach'),
    'core': ('Core', 'Heart', 'Crystal', 'Rune-Block', 'Rune-Cube', 'Watch-Cube'),
    'mote': ('Mote', 'Acorn', 'Spark', 'Ember'),
    'jar': ('Jar', 'Bottled', 'Jarred'),
    'scale': ('Scale',),
    'wood': ('Log', 'Stalk'),
}

# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _old_ingredients():
    """The ingredient catalogue before the rebuild (colours, trophy text).
    Saved once next to this script so the build can be re-run."""
    snap = os.path.join(HERE, 'old_ingredients.json')
    if not os.path.exists(snap):
        data = _load(os.path.join(ITEMS, 'ingredient.json'))
        with open(snap, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    return _load(snap)


def _old_recipes():
    snap = os.path.join(HERE, 'old_recipes.json')
    if not os.path.exists(snap):
        data = _load(os.path.join(ITEMS, 'recipes.json'))
        with open(snap, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    return _load(snap)


def _groups():
    out = []
    with open(os.path.join(HERE, 'kin_groups.txt'), encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                out.append(line.split())
    return out


def _content():
    out = {}
    for n in (1, 2, 3, 4):
        with open(os.path.join(HERE, f'ingredients_{n}.txt'), encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line.strip() or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) != 6:
                    raise SystemExit(f'bad content line ({len(parts)} fields): {line[:80]}')
                key = parts[0]
                if key in out:
                    raise SystemExit(f'duplicate content key {key}')
                out[key] = {'nature': parts[1], 'name': parts[2], 'description': parts[3],
                            'single': parts[4], 'single_flavor': parts[5]}
    return out


def _nature_split(code: str):
    """'hp' -> ('hp', None); 'DEX' -> ('stat', 'DEX'); 'fire_resist' -> ('special', 'fire_resist')."""
    if code in ('hp', 'sp', 'mp'):
        return code, None
    if code in STATS:
        return 'stat', code
    return 'special', code


def band_of(floor: int) -> int:
    return max(1, min(5, (int(floor) - 1) // 20 + 1))


# ----------------------------------------------------------------------
# Ingredients
# ----------------------------------------------------------------------

def build_ingredients():
    monsters = _load(os.path.join(DATA, 'monsters.json'))
    old = _old_ingredients()
    content = _content()
    rules = _load(os.path.join(DATA, 'cooking_rules.json'))
    powers = set(rules['special']['powers'])
    ings = {}          # id -> record
    harvest = {}       # monster -> ingredient id
    aliases = {}       # old id -> new id
    for g in _groups():
        key = g[0]
        kid = KEPT_OVERRIDE.get(key, f'{key}_prime')
        if kid not in old:
            raise SystemExit(f'kept id {kid} has no picture/old row')
        c = content.get(key)
        if c is None:
            raise SystemExit(f'no content for {key}')
        art_members = [m for m in g if f'{m}_prime' in old] or g
        floor = int(statistics.median_low(sorted(int(monsters[m]['peak_floor']) for m in art_members)))
        tab, detail = _nature_split(c['nature'])
        if tab == 'special' and detail not in powers:
            raise SystemExit(f'{key}: unknown power {detail}')
        o = old[kid]
        ings[kid] = {
            'key': key, 'name': c['name'], 'description': c['description'],
            'single': c['single'], 'single_flavor': c['single_flavor'],
            'tab': tab, 'detail': detail, 'floor': floor, 'band': band_of(floor),
            'members': g, 'role': 'prime', 'color': o.get('color', [180, 120, 90]),
            'part': o['part'],
            'family': monsters[key].get('family', ''), 'secret': key in SECRET_KEYS,
            'source': key,
        }
        for m in g:
            harvest[m] = kid
            old_id = f'{m}_prime'
            if old_id in old and old_id != kid:
                aliases[old_id] = kid
    # Old prime ids that belonged to a boss with a trophy (never harvested).
    for t in TROPHIES:
        old_id = f'{t}_prime'
        if old_id in old and old_id not in ings and old_id not in aliases:
            aliases[old_id] = f'{t}_trophy'
    for t, (nature, perm) in TROPHIES.items():
        tid = f'{t}_trophy'
        o = old[tid]
        tab, detail = _nature_split(nature)
        floor = int(monsters[t]['peak_floor'])
        name = o['name'].replace('Medusa-Gorgon', 'Medusa')
        ings[tid] = {
            'key': t, 'name': name, 'description': o.get('trophy_desc') or o.get('description', ''),
            'single': None, 'single_flavor': None, 'tab': tab, 'detail': detail,
            'floor': floor, 'band': band_of(floor), 'members': [t], 'role': 'trophy', 'part': 'trophy',
            'color': o.get('color', [255, 220, 100]), 'family': monsters[t].get('family', ''),
            'secret': False, 'source': t, 'permanent_power': perm,
        }
        harvest[t] = tid
    for key, c in content.items():
        if not key.startswith('forage:'):
            continue
        fid = key.split(':', 1)[1]
        o = old[fid]
        tab, detail = _nature_split(c['nature'])
        floor = int(o.get('min_level', 1))
        ings[fid] = {
            'key': fid, 'name': c['name'], 'description': c['description'],
            'single': c['single'], 'single_flavor': c['single_flavor'],
            'tab': tab, 'detail': detail, 'floor': floor, 'band': band_of(floor),
            'members': [], 'role': 'dungeon', 'color': o.get('color', [120, 120, 120]), 'part': 'forage',
            'family': '', 'secret': False, 'source': '', 'terrain': o.get('terrain', ''),
        }
    missing = [m for m in monsters if m not in harvest]
    if missing:
        raise SystemExit(f'monsters with no ingredient: {missing}')
    unused = [k for k in content if not k.startswith('forage:')
              and k not in {r['key'] for r in ings.values()}]
    if unused:
        raise SystemExit(f'content with no kin group: {unused}')
    return ings, harvest, aliases


# ----------------------------------------------------------------------
# Structure
# ----------------------------------------------------------------------

def _pool_key(rec):
    return rec['tab'] if rec['tab'] in ('hp', 'sp', 'mp') else f"{rec['tab']}:{rec['detail']}"


def _benefit_key(code):
    tab, detail = _nature_split(code)
    return tab if tab in ('hp', 'sp', 'mp') else f'{tab}:{detail}'


def _closeness(rec, key):
    """0 same kind (pool), 1 same tab, 2 anything else."""
    if _pool_key(rec) == key:
        return 0
    return 1 if rec['tab'] == key.split(':')[0] else 2


def make_structure(ings):
    rng = random.Random(20261114)
    monsters_ok = {i: r for i, r in ings.items() if r['role'] == 'prime' and not r['secret']}
    forage = {i: r for i, r in ings.items() if r['role'] == 'dungeon'}
    use = {i: 0 for i in ings}            # multi appearances so far
    dishes = []
    seen_sets = set()                     # no two dishes of the same ingredients
    paired = {}                           # (a, b) -> dishes holding both

    def helpers_for(tab, max_floor, k, exclude):
        """k common foods / forage that suit a dish of `tab` and exist by max_floor."""
        cands = []
        for fid, (nat, fl) in FOOD.items():
            if fl <= max_floor:
                w = 3 if (nat == tab or (nat == 'stat' and tab == 'stat')) else 1
                cands.append((fid, w * FOOD_RARITY.get(fid, 1.0)))
        for fid, r in forage.items():
            if r['floor'] <= max_floor:
                w = 3 if r['tab'] == tab else 0.4
                w += 3 if use[fid] < 2 else 0
                cands.append((fid, w))
        out = []
        cands = [c for c in cands if c[0] not in exclude]
        while len(out) < k and cands:
            tot = sum(w for _, w in cands)
            x = rng.uniform(0, tot)
            for idx, (fid, w) in enumerate(cands):
                x -= w
                if x <= 0:
                    out.append(fid)
                    cands.pop(idx)
                    break
        return out

    def floor_of(i):
        if i in ings:
            return ings[i]['floor']
        return FOOD[i][1]

    def add(parts, benefit, legendary=False, kind='multi', anchor=None):
        parts = list(dict.fromkeys(parts))
        tab = _nature_split(benefit)[0]
        tries = 0
        while frozenset(parts) in seen_sets and tries < 12:
            tries += 1
            mx = max(floor_of(p) for p in parts)
            helper = [h for h in parts if h in FOOD or h in forage]
            if len(parts) < 5:
                parts += helpers_for(tab, mx, 1, set(parts))
            elif helper:
                parts.remove(helper[-1])
                parts += helpers_for(tab, mx, 1, set(parts) | {helper[-1]})
        if frozenset(parts) in seen_sets:
            raise SystemExit(f'could not make a new dish of {parts}')
        seen_sets.add(frozenset(parts))
        mons = [p for p in parts if p in ings and ings[p]['role'] != 'dungeon']
        for x in mons:
            for y in mons:
                if x < y:
                    paired[(x, y)] = paired.get((x, y), 0) + 1
        for p in parts:
            if p in use:
                use[p] += 1
        floors = [floor_of(p) for p in parts]
        dishes.append({
            'parts': parts, 'benefit': benefit, 'legendary': legendary, 'kind': kind,
            'anchor': anchor or parts[0],
            'cross_depth': (min(floors) <= 20 and max(floors) >= 40),
        })

    def pick(pool_filter, prefer_key, k, exclude, floor_lo=0, floor_hi=999):
        """k monster parts in the floor range, preferring the pool `prefer_key`
        and the least used."""
        cands = [i for i, r in monsters_ok.items()
                 if i not in exclude and floor_lo <= r['floor'] <= floor_hi and pool_filter(r)]
        rng.shuffle(cands)
        cands.sort(key=lambda i: (_closeness(monsters_ok[i], prefer_key), use[i]))
        return cands[:k]

    # -- Legendary feasts: each trophy anchors two, each boss part one --------
    trophy_ids = [f'{t}_trophy' for t in TROPHIES]
    for tid in trophy_ids:
        t = ings[tid]['key']
        for code in (TROPHIES[t][0], TROPHY_SECOND[t]):
            bk = _benefit_key(code)
            deep = pick(lambda r: True, bk, 2, {tid}, floor_lo=41)
            early = pick(lambda r: True, bk, 1, {tid, *deep}, floor_hi=20)
            parts = [tid, *deep, *early]
            parts += helpers_for(bk.split(':')[0], ings[tid]['floor'], 5 - len(parts), set(parts))
            add(parts, code, legendary=True, anchor=tid)
    for key in BOSS_FEASTS:
        bid = f'{key}_prime'
        code = ings[bid]['detail'] if ings[bid]['tab'] in ('stat', 'special') else ings[bid]['tab']
        if code == 'sp':
            code = 'hp'
        bk = _benefit_key(code)
        deep = pick(lambda r: True, bk, 2, {bid}, floor_lo=41)
        early = pick(lambda r: True, bk, 1, {bid, *deep}, floor_hi=20)
        parts = [bid, *deep, *early]
        parts += helpers_for(bk.split(':')[0], ings[bid]['floor'], 5 - len(parts), set(parts))
        add(parts, code, legendary=True, anchor=bid)

    # -- Cross-depth dishes: a deep part with an early part of its kind -------
    deep_parts = sorted((i for i, r in monsters_ok.items() if r['floor'] >= 40),
                        key=lambda i: ings[i]['floor'])
    for d in deep_parts:
        rounds = 2 if use[d] == 0 else 1
        for _ in range(rounds):
            if use[d] >= 2:
                break
            r = ings[d]
            pk = _pool_key(r)
            early = pick(lambda x: _pool_key(x) == pk, pk, 1, {d}, floor_hi=20)
            if not early:
                early = pick(lambda x: True, pk, 1, {d}, floor_hi=20)
            parts = [d, *early]
            size = rng.choice((2, 3, 3, 4))
            if size == 4 and rng.random() < 0.5:
                more = pick(lambda x: _pool_key(x) == pk, pk, 1, set(parts), floor_hi=60)
                parts += more
            parts += helpers_for(r['tab'], r['floor'], max(0, size - len(parts)), set(parts))
            code = r['detail'] if r['tab'] in ('stat', 'special') else r['tab']
            add(parts, code, anchor=d)

    # -- Secret parts: two dishes each, never legendary ------------------------
    for i, r in ings.items():
        if not r['secret']:
            continue
        pk = _pool_key(r)
        for _ in range(2):
            mate = pick(lambda x: _pool_key(x) == pk, pk, 1, {i}, floor_hi=40)
            parts = [i, *mate]
            parts += helpers_for(r['tab'], r['floor'], 1, set(parts))
            code = r['detail'] if r['tab'] in ('stat', 'special') else r['tab']
            add(parts, code, anchor=i)

    # -- Same-band dishes: kin of a kind, close in depth ----------------------
    pools = {}
    for i, r in list(monsters_ok.items()) + list(forage.items()):
        pools.setdefault(_pool_key(r), []).append(i)
    for pk in sorted(pools):
        members = sorted(pools[pk], key=lambda i: (ings[i]['floor'], i))
        guard = 0
        while any(use[i] < 2 for i in members) and guard < 400:
            guard += 1
            needy = [i for i in members if use[i] < 2]
            a = needy[0]
            fa = ings[a]['floor']
            near = sorted((i for i in members if i != a),
                          key=lambda i: (paired.get(tuple(sorted((a, i))), 0),
                                         0 if use[i] < 2 else 1, abs(ings[i]['floor'] - fa), i))
            if not near:
                # a kind of one: its tab-mates stand in
                near = sorted((i for i, x in monsters_ok.items()
                               if i != a and x['tab'] == ings[a]['tab']),
                              key=lambda i: (use[i], abs(ings[i]['floor'] - fa), i))[:3]
            size = rng.choice((2, 2, 3, 3, 3, 4, 4, 5))
            n_monster = 1 + min(len(near), rng.choice((1, 1, 2, 2, 3)) if size >= 3 else 1)
            mates = [i for i in near if abs(ings[i]['floor'] - fa) <= 25][:n_monster - 1] or near[:1]
            if not mates:
                # a pool of one: borrow a neighbour of any kind
                mates = pick(lambda x: True, pk, 1, {a}, floor_lo=max(0, fa - 15), floor_hi=fa + 15)
            parts = [a, *mates]
            mx = max(ings[p]['floor'] for p in parts)
            parts += helpers_for(ings[a]['tab'], mx, max(0, size - len(parts)), set(parts))
            r = ings[a]
            code = r['detail'] if r['tab'] in ('stat', 'special') else r['tab']
            add(parts, code, anchor=a)

    # Trophies need two multis; they have them (two feasts each). Check all.
    short = [i for i in ings if use[i] < 2]
    if short:
        raise SystemExit(f'ingredients with fewer than two multi-dishes: {short}')
    return dishes


def write_structure(ings):
    dishes = make_structure(ings)
    out = {}
    n_leg = n_mix = 0
    for d in dishes:
        if d['legendary']:
            n_leg += 1
            did = f'feast_{n_leg:02d}'
        else:
            n_mix += 1
            did = f'dish_{n_mix:03d}'
        out[did] = d
    with open(os.path.join(HERE, 'structure.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    names = {i: r['name'] for i, r in ings.items()}
    food = _load(os.path.join(ITEMS, 'food.json'))
    for fid in FOOD:
        names[fid] = food[fid]['name'].title()
    with open(os.path.join(HERE, 'dish_skeleton.txt'), 'w', encoding='utf-8') as f:
        for did, d in out.items():
            floors = [ings[p]['floor'] if p in ings else FOOD[p][1] for p in d['parts']]
            tier = band_of(max(floors))
            tag = ('LEGENDARY ' if d['legendary'] else '') + ('CROSS ' if d['cross_depth'] else '')
            f.write(f"{did}|{d['benefit']}|T{tier}|{tag}|" + ' + '.join(names[p] for p in d['parts']) + '\n')
    print(f'{len(out)} multi-dishes ({n_leg} legendary); skeleton written')


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------

def _dish_names():
    out = {}
    for n in (1, 2):
        with open(os.path.join(HERE, f'dishes_{n}.txt'), encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line.strip() or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) != 3:
                    raise SystemExit(f'bad dish line: {line[:80]}')
                if parts[0] in out:
                    raise SystemExit(f'dish {parts[0]} named twice')
                out[parts[0]] = (parts[1], parts[2])
    return out


def build():
    ings, harvest, aliases = build_ingredients()
    structure = _load(os.path.join(HERE, 'structure.json'))
    names = _dish_names()
    old_recipes = _old_recipes()
    food = _load(os.path.join(ITEMS, 'food.json'))
    have_art = dish_art.drawn(ART_DIR)

    def tier_of(parts):
        """kitchen.dish_tier: the band of the deepest ingredient."""
        return band_of(max(ings[p]['floor'] if p in ings else int(food[p].get('min_level', 1) or 1)
                           for p in parts))
    recipes = {}
    # Singles: one per ingredient.
    for iid, r in sorted(ings.items(), key=lambda kv: kv[0]):
        code = r['detail'] if r['tab'] in ('stat', 'special') else r['tab']
        if r['role'] == 'trophy':
            rid = f"trophy_{r['key']}_recipe"
            o = old_recipes[rid]
            recipes[rid] = {
                'name': o['name'], 'ingredients': [iid], 'benefit': code, 'trophy': True,
                'permanent': r['permanent_power'], 'flavor': o.get('flavor', ''),
            }
            recipes[rid]['art'] = dish_art.recipe_art(rid, recipes[rid], tier_of([iid]), have_art)
            continue
        rid = f"cook_{r['key']}"
        recipes[rid] = {
            'name': r['single'], 'ingredients': [iid], 'benefit': code,
            'flavor': r['single_flavor'],
        }
        recipes[rid]['art'] = dish_art.recipe_art(rid, recipes[rid], tier_of([iid]), have_art)
    for did, d in structure.items():
        if did not in names:
            raise SystemExit(f'no name for {did}')
        name, flavor = names[did]
        rec = {'name': name, 'ingredients': d['parts'], 'benefit': d['benefit'], 'flavor': flavor}
        if d['legendary']:
            rec['legendary'] = True
        rec['art'] = dish_art.recipe_art(did, rec, tier_of(d['parts']), have_art)
        if d['cross_depth']:
            rec['cross_depth'] = True
        recipes[did] = rec
    extra = sorted(set(names) - set(structure))
    if extra:
        raise SystemExit(f'dishes.txt names unknown dishes: {extra[:10]}')
    # Write the data.
    ing_json = {}
    for iid, r in sorted(ings.items(), key=lambda kv: (kv[1]['role'] != 'prime', kv[0])):
        row = {
            'name': r['name'], 'symbol': '*' if r['role'] == 'trophy' else '~',
            'color': r['color'], 'weight': 0.3 if r['role'] == 'trophy' else (0.15 if r['role'] == 'dungeon' else 0.25),
            'min_level': r['floor'], 'tier_role': r['role'], 'nature': r['tab'], 'part': r['part'],
            'description': r['description'], 'identified': True,
        }
        if r['source']:
            row['source_monster'] = r['source']
        if r['family']:
            row['family'] = r['family']
        if r['tab'] == 'stat':
            row['stat_grant'] = r['detail']
        if r['tab'] == 'special':
            row['temp_power'] = r['detail']
        if r['role'] == 'prime':
            row['edible_safe'] = True
            row['raw_sp'] = 10
        if r['role'] == 'dungeon':
            row['terrain'] = r.get('terrain', '')
        if r['secret']:
            row['secret'] = True
        if r['role'] == 'trophy':
            row['trophy_permanent_power'] = r['permanent_power']
        ing_json[iid] = row
    with open(os.path.join(ITEMS, 'ingredient.json'), 'w', encoding='utf-8') as f:
        json.dump(ing_json, f, ensure_ascii=False, indent=2)
        f.write('\n')
    hmap = {
        '_doc': ('What a corpse yields when harvested (monster id -> ingredient id), and '
                 'the ingredient ids retired by the kitchen rebuild (2026-11-14), each with '
                 'the kept id it became. Close kin share one ingredient. Built by '
                 'tools/content/kitchen/build_kitchen.py.'),
        'monsters': dict(sorted(harvest.items())),
        'aliases': dict(sorted(aliases.items())),
    }
    with open(os.path.join(ITEMS, 'harvest_map.json'), 'w', encoding='utf-8') as f:
        json.dump(hmap, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(os.path.join(ITEMS, 'recipes.json'), 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(os.path.join(HERE, 'dish_art.json'), 'w', encoding='utf-8') as f:
        json.dump({'_doc': ('Recipe id -> its picture (assets/tiles/items/<art>.png), written by '
                            'build_kitchen.py from dish_art.py: the kind its name says, at its tier and '
                            'main benefit. A record to read; edit dish_art.py, not this file.'),
                   **{rid: r['art'] for rid, r in sorted(recipes.items())}},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')
    check(ings, recipes)
    report(ings, recipes)


def check(ings, recipes):
    food = _load(os.path.join(ITEMS, 'food.json'))
    problems = []
    singles = {}
    multis = {}
    for rid, r in recipes.items():
        parts = list(dict.fromkeys(r['ingredients']))
        for p in parts:
            if p not in ings and p not in FOOD:
                problems.append(f'{rid}: unknown ingredient {p}')
            if p in FORBIDDEN_FOOD:
                problems.append(f'{rid}: forbidden food {p}')
        if len(parts) == 1:
            singles.setdefault(parts[0], []).append(rid)
        else:
            if not 2 <= len(parts) <= 5:
                problems.append(f'{rid}: {len(parts)} ingredients')
            for p in parts:
                multis.setdefault(p, []).append(rid)
        for w in BANNED_WORDS:
            if w.lower() in r['name'].lower():
                problems.append(f'{rid}: banned word {w!r} in {r["name"]}')
        if not os.path.exists(os.path.join(ART_DIR, r['art'] + '.png')):
            problems.append(f'{rid}: no art {r["art"]}')
    for iid, r in ings.items():
        if len(singles.get(iid, [])) != 1:
            problems.append(f'{iid}: {len(singles.get(iid, []))} single dishes')
        if len(multis.get(iid, [])) < 2:
            problems.append(f'{iid}: {len(multis.get(iid, []))} multi dishes')
        for w in BANNED_WORDS:
            if w.lower() in r['name'].lower():
                problems.append(f'{iid}: banned word {w!r}')
        if not os.path.exists(os.path.join(ART_DIR, iid + '.png')):
            problems.append(f'{iid}: no picture')
        words = PART_WORDS.get(r['part'])
        if words and not any(w in r['name'] for w in words):
            problems.append(f"{iid}: {r['name']!r} does not say its part ({r['part']})")
    seen = {}
    for rid, r in recipes.items():
        n = r['name'].lower()
        if n in seen:
            problems.append(f'dish name {r["name"]!r} used by {seen[n]} and {rid}')
        seen[n] = rid
    for fid in FOOD:
        if fid not in food:
            problems.append(f'food {fid} missing from food.json')
    if problems:
        print('\n'.join(problems[:60]))
        raise SystemExit(f'{len(problems)} problems')


def report(ings, recipes):
    from collections import Counter

    def floor(p):
        return ings[p]['floor'] if p in ings else FOOD[p][1]
    tab_band = Counter()
    for r in recipes.values():
        tab, _ = _nature_split(r['benefit'])
        tab_band[(tab, band_of(max(floor(p) for p in r['ingredients'])))] += 1
    print('dishes:', len(recipes), ' ingredients:', len(ings))
    print('tab x band:')
    for tab in TABS:
        print(' ', tab.ljust(8), [tab_band[(tab, b)] for b in range(1, 6)])
    multis = [r for r in recipes.values() if len(set(r['ingredients'])) > 1]
    print('multis:', len(multis), ' legendary:', sum(1 for r in multis if r.get('legendary')),
          ' cross-depth:', sum(1 for r in multis if r.get('cross_depth')))
    print('sizes:', Counter(len(set(r['ingredients'])) for r in multis))
    print('natures:', Counter(r['tab'] if r['tab'] != 'stat' else r['detail'] for r in ings.values()))
    print('ingredients per band:', Counter(r['band'] for r in ings.values()))
    food_uses = Counter(p for r in multis for p in set(r['ingredients']) if p in FOOD)
    print('food uses:', dict(food_uses))


if __name__ == '__main__':
    if '--structure' in sys.argv:
        ings, _h, _a = build_ingredients()
        write_structure(ings)
    else:
        build()
