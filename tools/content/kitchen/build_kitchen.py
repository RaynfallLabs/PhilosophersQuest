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
2b. The structure is then kept cookable ON PURPOSE (slice K1b):
   ``part_freq.py`` measures in the simulator how often each part turns up
   (``part_freq.json``), ``restructure.py`` swaps rare parts out of feasts
   and crowded dishes and adds dishes for parts left short, and
   ``dishes_3.txt`` names the dishes it added. The rules are in
   ``part_rules.py``; the check below fails on any dish that breaks them.
3. ``py tools/content/kitchen/build_kitchen.py``
   Merges the frozen structure, the ingredient content (``ingredients_*.txt``)
   and the dish names into the game data, and checks every rule:
     data/items/ingredient.json   every ingredient (monster parts, trophies, forage)
     data/items/harvest_map.json  monster -> ingredient, and old ids -> kept ids
     data/items/recipes.json      the recipe book
   The numbers a dish gives live in data/cooking_rules.json (hand-written),
   never here.

THE TWO LOW RUNGS (Brandon, 2026-11-22, on rations, bread and cheese piling
up). ``rungs_plain.txt`` holds the dishes of staples alone and
``rungs_step_*.txt`` each part's dish with one staple, named by hand.

    py tools/content/kitchen/build_kitchen.py --rungs

writes those dishes, and only those, into recipes.json and dish_art.json and
is idempotent; a full build includes them too. (On 2026-11-22 a full build
refuses to run: the pack kinds and the MONSTERS AND MAGIC kinds were written
straight into the data and are not in kin_groups.txt. Use --rungs.)

Inputs: data/monsters.json, data/items/food.json, the OLD ingredient.json
(colours; read from git's copy in ``old_ingredients.json`` once the data has
been rebuilt), kin_groups.txt, people.txt, ingredients_*.txt.

PEOPLE (Brandon, 2026-11-16: "Humans are not harvested. That's weird, we're
not cannibals"): ``people.txt`` lists the kinds whose body is searched, never
harvested (humans and the human-like folk). A person is in no kin group and
yields no ingredient; the build writes the list to harvest_map.json
``people``, and ``people_parts``: each part a person once gave (an old
save's Bandit Trail Ham) with the ordinary food it becomes on load.

SPECIAL FOOD (Brandon, 2026-11-16: "every special item is used in at least
one decent recipe"): a quest, key or one-of-a-kind food (the Magic Dungeon
Carrot, the Starnut Tart, the mythic fruits) goes into the dish or dishes
``SPECIAL_FOOD`` names for it and no other.

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
if HERE not in sys.path:
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

# Common food that goes into dishes (data/items/food.json). (nature it leans
# to, first floor.)
FOOD = {
    'bread_ration': ('sp', 1), 'dried_meat': ('sp', 1), 'hard_cheese': ('hp', 1),
    'wild_mushroom': ('sp', 1), 'apple': ('hp', 1), 'trail_rations': ('sp', 1),
    'healing_herb': ('hp', 3), 'elvish_bread': ('mp', 10), 'philosopher_tea': ('mp', 15),
    'deep_fungi': ('stat', 35), 'void_ration': ('sp', 60),
}
# Rare food turns up in few dishes (it is rarely found).
FOOD_RARITY = {'philosopher_tea': 0.15, 'deep_fungi': 0.3, 'void_ration': 0.3, 'elvish_bread': 0.6}
# Special food: a quest or key piece, or a one-of-a-kind find (food.json
# ``special``), goes into its own dish or dishes and no other (Brandon,
# 2026-11-16: "every special item is used in at least one decent recipe, so a
# player is tempted to cook it rather than save it for its special event").
# Cooking it uses it up. food id -> the dish ids that may call for it. The
# Starnut Tart is cooked to carry (dish_starnut_tart) and goes into a dish of
# its own besides; never back into the dish that makes it.
SPECIAL_FOOD = {
    'magic_dungeon_carrot': ('dish_339',),
    'starnut_tart': ('dish_340',),
    'tantalus_plum': ('dish_341',),
    'golden_apple': ('dish_342',),
    'ambrosia': ('dish_343',),
    'peach_of_immortality': ('dish_344',),
}
# Food that goes into no dish but the two low rungs (STAPLES): a stew is a meal already.
FORBIDDEN_FOOD = ('hearty_stew',)
# The staples of the two low rungs (rungs_*.txt), with their short ids. The
# stew, a meal already, goes into those two rungs and no other dish; tea, deep
# fungi and the void ration are left to be eaten for their stat.
STAPLES = {
    'bread_ration': 'bread', 'dried_meat': 'meat', 'hard_cheese': 'cheese', 'apple': 'apple',
    'trail_rations': 'trail', 'wild_mushroom': 'mushroom', 'healing_herb': 'herb',
    'elvish_bread': 'waybread', 'hearty_stew': 'stew',
}
DEEP_STAPLES = ('elvish_bread', 'wild_mushroom', 'hearty_stew', 'healing_herb', 'dried_meat',
                'trail_rations')
MAX_NAME = 34                   # the longest name the cook menu's row was laid out for
# Food that goes into ONE dish only, the one that plays its song (songs.py,
# 3.5.2): caviar and tater tots make Caviar and Tater Tots and nothing else.
# Its structure row names ``song``; its picture is the song's (dish_art).
SONG_FOOD = ('caviar', 'tater_tots')
# A dish may be COOKED TO CARRY: its structure row names ``makes``, a food id
# in data/items/food.json, and cooking it puts that food in the pack instead
# of eating it (kitchen.apply_dish). The Starnut Tart is the first, the
# Mooble's favourite (RARE_PETS_PLAN_2026_11_14; its benefit is 'carry', so
# it sits on the Special tab). A carried dish is never itself an ingredient.

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


def _new_forage():
    """Forage added after the rebuild (new_forage.json): min_level, colour, terrain."""
    with open(os.path.join(HERE, 'new_forage.json'), encoding='utf-8') as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith('_')}


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


def _people():
    """The kinds whose body is searched, never harvested (people.txt), in order."""
    out = []
    with open(os.path.join(HERE, 'people.txt'), encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if line:
                out.append(line)
    return out


# What a part a person once gave becomes in an old save (people_parts): the
# ordinary food it was, taken from the pack (the hams and sausages of the
# packs were dried and salted meat; the elves' acorn-light their waybread).
PERSON_PART_FOOD = {'light_elf_hostile': 'elvish_bread', 'huldufolk_raider': 'elvish_bread'}
PERSON_PART_DEFAULT = 'dried_meat'


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
        o = old.get(fid) or _new_forage().get(fid)
        if o is None:
            raise SystemExit(f'forage {fid} has no row in old_ingredients.json or new_forage.json')
        tab, detail = _nature_split(c['nature'])
        floor = int(o.get('min_level', 1))
        ings[fid] = {
            'key': fid, 'name': c['name'], 'description': c['description'],
            'single': c['single'], 'single_flavor': c['single_flavor'],
            'tab': tab, 'detail': detail, 'floor': floor, 'band': band_of(floor),
            'members': [], 'role': 'dungeon', 'color': o.get('color', [120, 120, 120]), 'part': 'forage',
            'family': '', 'secret': False, 'source': '', 'terrain': o.get('terrain', ''),
        }
    people = set(_people())
    unknown = sorted(people - set(monsters))
    if unknown:
        raise SystemExit(f'people.txt names kinds monsters.json does not know: {unknown}')
    harvested_people = sorted(people & set(harvest))
    if harvested_people:
        raise SystemExit(f'people in a kin group (a person is never harvested): {harvested_people}')
    missing = [m for m in monsters if m not in harvest and m not in people]
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
    for n in (1, 2, 3, 4):
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


def _rung_lines(fname, fields):
    with open(os.path.join(HERE, fname), encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if not line.strip() or line.startswith('#'):
                continue
            row = [p.strip() for p in line.rstrip('\n').split('|')]
            if len(row) != fields or not all(row):
                raise SystemExit(f'{fname}:{n}: expected {fields} fields')
            yield row


def rung_recipes() -> dict:
    """The two low rungs' dishes (rungs_*.txt), checked against the shipped
    ingredient, food and rule data: id -> recipe, in the files' order."""
    ings = _load(os.path.join(ITEMS, 'ingredient.json'))
    food = _load(os.path.join(ITEMS, 'food.json'))
    rules = _load(os.path.join(DATA, 'cooking_rules.json'))
    book = {rid: r for rid, r in _load(os.path.join(ITEMS, 'recipes.json')).items()
            if not r.get('rung')}
    big, powers = rules['big_dish'], rules['special']['powers']
    have_art = dish_art.drawn(ART_DIR)
    out, problems = {}, []
    sets = {frozenset(r['ingredients']): rid for rid, r in book.items()}
    names = {r['name'].lower(): rid for rid, r in book.items()}
    names.update({r['name'].lower(): iid for iid, r in ings.items()})

    def add(rid, rung, parts, benefit, name, flavor):
        floors = [int((ings.get(p) or food.get(p) or {}).get('min_level', 1) or 1) for p in parts]
        tier = band_of(max(floors))
        if len(set(parts)) >= int(big['parts']):
            tier = min(5, tier + int(big['tier_bonus']))        # kitchen.dish_tier
        art = dish_art.art_id(dish_art.dish_kind(name), tier, dish_art.tab_of(benefit))
        if benefit not in ('hp', 'sp', 'mp') and benefit not in powers:
            problems.append(f'{rid}: benefit {benefit} (never a stat on these rungs)')
        if art not in have_art:
            problems.append(f'{rid}: {name!r} has no picture of its kind ({art})')
        if rid in book or rid in out:
            problems.append(f'{rid}: id used twice')
        key = frozenset(parts)
        if len(key) != len(parts) or key in sets:
            problems.append(f'{rid}: the same ingredients as {sets.get(key)}')
        sets[key] = rid
        if name.lower() in names:
            problems.append(f'{rid}: name {name!r} is used by {names[name.lower()]}')
        names[name.lower()] = rid
        if len(name) > MAX_NAME:
            problems.append(f'{rid}: name {name!r} is over {MAX_NAME} letters')
        for w in BANNED_WORDS:
            if w.lower() in name.lower():
                problems.append(f'{rid}: banned word {w!r} in {name!r}')
        out[rid] = {'name': name, 'ingredients': list(parts), 'benefit': benefit,
                    'flavor': flavor, 'rung': rung, 'art': art}

    pairs = set()
    for joined, benefit, name, flavor in _rung_lines('rungs_plain.txt', 4):
        parts = joined.split('+')
        unknown = [p for p in parts if p not in STAPLES]
        if unknown or not 2 <= len(parts) <= 4:
            problems.append(f'plain fare {joined}: two to four staples only')
            continue
        if len(parts) == 2:
            pairs.add(frozenset(parts))
        add('fare_' + '_'.join(STAPLES[p] for p in parts), 'plain', parts, benefit, name, flavor)
    for a in STAPLES:
        for b in STAPLES:
            if a < b and frozenset((a, b)) not in pairs:
                problems.append(f'plain fare: {a} and {b} make no dish')

    stepped = set()
    for n in (1, 2, 3):
        for key, staple, benefit, name, flavor in _rung_lines(f'rungs_step_{n}.txt', 5):
            part, rid = f'{key}_prime', f'step_{key}'
            if rid in out:              # a part's second step, with another staple
                rid += f"_{STAPLES.get(staple, staple)}"
            rec = ings.get(part)
            if not rec or rec.get('tier_role') != 'prime' or staple not in STAPLES:
                problems.append(f'{rid}: not a part and a staple ({part}, {staple})')
                continue
            band = band_of(int(rec['min_level']))
            if band >= 4 and staple not in DEEP_STAPLES:
                problems.append(f'{rid}: {staple} is not found that deep')
            if band_of(int(food[staple].get('min_level', 1) or 1)) > band:
                problems.append(f'{rid}: {staple} is found deeper than the part')
            if rec['nature'] not in ('stat', 'sp'):
                want = rec['temp_power'] if rec['nature'] == 'special' else rec['nature']
                if benefit != want:
                    problems.append(f'{rid}: {benefit}, but the part is {want}')
            stepped.add(part)
            add(rid, 'step', [part, staple], benefit, name, flavor)
    for r in book.values():
        ps = set(r['ingredients'])
        if len(ps) == 2 and len(ps & set(STAPLES)) == 1:
            stepped |= ps                       # (a few were in the book already)
    short = sorted(i for i, r in ings.items() if r.get('tier_role') == 'prime' and i not in stepped)
    if short:
        problems.append(f'{len(short)} parts with no dish of one staple: {short}')
    if problems:
        print('\n'.join(problems[:80]))
        raise SystemExit(f'{len(problems)} problems')
    return out


def write_rungs():
    """Write the two low rungs into the shipped book; nothing else changes."""
    rungs = rung_recipes()
    path = os.path.join(ITEMS, 'recipes.json')
    recipes = {rid: r for rid, r in _load(path).items() if not r.get('rung')}
    recipes.update(rungs)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=1)
        f.write('\n')
    art_path = os.path.join(HERE, 'dish_art.json')
    record = _load(art_path)
    doc = record.pop('_doc')
    record = {rid: a for rid, a in record.items() if rid in recipes}
    record.update({rid: r['art'] for rid, r in rungs.items()})
    with open(art_path, 'w', encoding='utf-8') as f:
        json.dump({'_doc': doc, **dict(sorted(record.items()))}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    n = {k: sum(1 for r in rungs.values() if r['rung'] == k) for k in ('plain', 'step')}
    print(f"{len(recipes)} dishes: {n['plain']} plain fare, {n['step']} one step up")


def build():
    ings, harvest, aliases = build_ingredients()
    structure = _load(os.path.join(HERE, 'structure.json'))
    names = _dish_names()
    old_recipes = _old_recipes()
    food = _load(os.path.join(ITEMS, 'food.json'))
    have_art = dish_art.drawn(ART_DIR)

    big = _load(os.path.join(DATA, 'cooking_rules.json')).get('big_dish') or {}

    def tier_of(parts):
        """kitchen.dish_tier: the band of the deepest ingredient, and a big
        dish (cooking_rules.json big_dish) a tier richer, at most 5; a
        picture's vessel is the dish's tier."""
        base = band_of(max(ings[p]['floor'] if p in ings else int(food[p].get('min_level', 1) or 1)
                           for p in parts))
        if int(big.get('parts', 0) or 0) and len(set(parts)) >= int(big['parts']):
            return min(5, base + int(big.get('tier_bonus', 0) or 0))
        return base
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
        if d.get('makes'):
            rec['makes'] = d['makes']
        if d.get('song'):
            rec['song'] = d['song']
        rec['art'] = dish_art.recipe_art(did, rec, tier_of(d['parts']), have_art)
        if d['cross_depth']:
            rec['cross_depth'] = True
        recipes[did] = rec
    recipes.update(rung_recipes())
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
    old = _old_ingredients()
    people = _people()
    people_parts = {}
    for k in people:
        if f'{k}_prime' in old:
            people_parts[f'{k}_prime'] = PERSON_PART_FOOD.get(k, PERSON_PART_DEFAULT)
    hmap = {
        '_doc': ('What a corpse yields when harvested (monster id -> ingredient id), and '
                 'the ingredient ids retired by the kitchen rebuild (2026-11-14), each with '
                 'the kept id it became. Close kin share one ingredient. "people": the kinds '
                 'whose body is searched, never harvested (Brandon, 2026-11-16: we are not '
                 'cannibals; data/cooking_rules.json "search"). "people_parts": each part a '
                 'person once gave, and the ordinary food an old save\'s held one becomes. '
                 'Built by tools/content/kitchen/build_kitchen.py.'),
        'monsters': dict(sorted(harvest.items())),
        'aliases': dict(sorted(aliases.items())),
        'people': sorted(people),
        'people_parts': dict(sorted(people_parts.items())),
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
            if p in SONG_FOOD:
                if not r.get('song'):
                    problems.append(f'{rid}: {p} goes only into the dish of its song')
                continue
            if p in SPECIAL_FOOD:
                if rid not in SPECIAL_FOOD[p]:
                    problems.append(f'{rid}: special food {p} goes only into {SPECIAL_FOOD[p]}')
                if p not in food or not food[p].get('special'):
                    problems.append(f'{rid}: {p} must be in food.json with "special": true')
                continue
            if p not in ings and p not in FOOD and not (r.get('rung') and p in STAPLES):
                problems.append(f'{rid}: unknown ingredient {p}')
            if p in FORBIDDEN_FOOD and not r.get('rung'):
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
        if r.get('makes'):
            # Cooked to carry: the food it makes exists, is never an
            # ingredient, and the dish is an ordinary one (not a feast).
            if r['makes'] not in food:
                problems.append(f'{rid}: makes unknown food {r["makes"]}')
            if r['makes'] not in FORBIDDEN_FOOD and r['makes'] not in SPECIAL_FOOD:
                problems.append(f'{rid}: the food it makes ({r["makes"]}) must be in '
                                f'FORBIDDEN_FOOD or SPECIAL_FOOD')
            if r['makes'] in parts:
                problems.append(f'{rid}: a dish never calls for the food it makes')
            if r.get('legendary') or r.get('trophy'):
                problems.append(f'{rid}: a feast or trophy dish is eaten, never carried')
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
    # Every special food has its dish (and is cooked up in it).
    for fid, dids in SPECIAL_FOOD.items():
        for did in dids:
            if fid not in (recipes.get(did) or {}).get('ingredients', []):
                problems.append(f'special food {fid}: its dish {did} does not call for it')
    special_flagged = {k for k, v in food.items() if isinstance(v, dict) and v.get('special')}
    for fid in sorted(special_flagged - set(SPECIAL_FOOD) - set(SONG_FOOD)):
        problems.append(f'food {fid} is "special" in food.json but has no dish in SPECIAL_FOOD')
    # A dish is a meal, never just its ingredient's name ("Cave Bear Steak").
    ing_names = {r['name'].lower(): iid for iid, r in ings.items()}
    for rid, r in recipes.items():
        if r['name'].lower() in ing_names:
            problems.append(f'{rid}: dish name {r["name"]!r} is the name of ingredient '
                            f'{ing_names[r["name"].lower()]}')
    # Can a run cook it? (part_freq.json; the rules are in part_rules.py)
    problems += part_rules_for(ings, food).problems(recipes)
    if problems:
        print('\n'.join(problems[:60]))
        raise SystemExit(f'{len(problems)} problems')


def part_rules_for(ings, food):
    import part_rules
    freq = part_rules.load_freq()
    kitchen_food = list(dict.fromkeys([*FOOD, *SPECIAL_FOOD, *STAPLES]))
    rare = part_rules.rare_foods({k: food[k] for k in kitchen_food}, freq['rules']['rare_food_weight'])

    def role_of(p):
        if p in ings:
            return ings[p]['role']
        return 'food' if p in kitchen_food else None
    return part_rules.PartRules(freq, role_of, rare)


def report(ings, recipes):
    from collections import Counter

    food_json = _load(os.path.join(ITEMS, 'food.json'))

    def floor(p):
        if p in SONG_FOOD:
            return 1                      # caviar and tater tots: found from floor 1
        if p in SPECIAL_FOOD:
            return int(food_json[p].get('min_level', 1) or 1)
        return ings[p]['floor'] if p in ings else int(food_json[p].get('min_level', 1) or 1)
    tab_band = Counter()
    for r in recipes.values():
        tab, _ = _nature_split(r['benefit'])
        t = band_of(max(floor(p) for p in r['ingredients']))
        big = _load(os.path.join(DATA, 'cooking_rules.json')).get('big_dish') or {}
        if int(big.get('parts', 0) or 0) and len(set(r['ingredients'])) >= int(big['parts']):
            t = min(5, t + int(big.get('tier_bonus', 0) or 0))     # kitchen.dish_tier
        tab_band[(tab, t)] += 1
    print('dishes:', len(recipes), ' ingredients:', len(ings))
    print('tab x tier (kitchen.dish_tier):')
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
    food = _load(os.path.join(ITEMS, 'food.json'))
    print('cookable in half of runs or more (part_freq.json):',
          part_rules_for(ings, food).summary(recipes))


if __name__ == '__main__':
    if '--rungs' in sys.argv:
        write_rungs()
    elif '--structure' in sys.argv:
        ings, _h, _a = build_ingredients()
        write_structure(ings)
    else:
        build()
