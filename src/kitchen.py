"""The kitchen: the recipe book, what a dish gives, and the cook menu's rows.

The kitchen rebuild (2026-11-14, COOKING_REBUILD_PLAN_2026_11_14). A pure
module (no pygame, no Game): ``food_system`` runs the harvest and the cook
(the quiz) and calls ``apply_dish`` here; the cook menu reads ``menu_rows``
and ``opening_tab``.

The data:
  data/items/recipes.json      the recipe book (built by tools/content/kitchen)
  data/items/ingredient.json   every ingredient: nature, tier_role, secret parts
  data/items/harvest_map.json  monster -> ingredient; retired ids -> kept ids
  data/items/food.json         the rations a dish can call for
  data/cooking_rules.json      every number a dish gives

A dish has one main benefit (``benefit``: hp, sp, mp, a stat or a timed
power), which is its menu tab. Its tier is the band of its deepest
ingredient, and a big dish (four or more different ingredients:
cooking_rules.json ``big_dish``) is one tier richer, at most tier 5
(Brandon, 2026-11-16: "Big dishes +1 tier"). What it gives comes from the rules file by tier, by tab, by its
worth (what its ingredients add, times the size bonus) and, for a legendary
feast, the legendary multiplier and a permanent bonus.

COOK TO CARRY (2026-11-14, the Mooble's Starnut Tart): a dish may name
``makes``, a food id in data/items/food.json. Cooking it right puts that food
in the pack instead of eating it (``apply_dish``); its benefit is 'carry', so
it sits on the Special tab, and its menu lines say it is made to carry and
what it gives when eaten. A dish the hero has LEARNED of (``player.
dishes_learned``: the Mooble tells of his tart) shows under Building Toward
even before any part of it is held.

PEOPLE ARE NOT HARVESTED (Brandon, 2026-11-16: "that's weird, we're not
cannibals"): a person's body (``is_person``: harvest_map.json ``people``,
humans and the human-like folk) is searched for the food he carried
(food_system.search_corpse), never harvested. An old save's part of a
person becomes ordinary food on load (``person_part_food``).

SPECIAL FOOD (Brandon, 2026-11-16): a quest, key or one-of-a-kind food
(food.json ``special``: the Magic Dungeon Carrot, the Starnut Tart, the
mythic fruits) goes into a dish of its own; cooking it uses it up. Held, it
puts that dish under Building Toward, as a harvested part does
(``is_keystone``).

TWO LOW RUNGS (Brandon, 2026-11-22: "there should be more recipes that use
these ONLY... as well as monster recipes that are just ONE step above a
single monster ingredient"). A dish may name a ``rung``: 'plain' (staples
alone: any two of them make a dish, no stat and no max HP) or 'step' (one
creature's part and one staple). Their numbers are cooking_rules.json
``rungs``; their dishes are tools/content/kitchen/rungs_*.txt.

VARIETY (Brandon, 2026-11-22: "Recipes are not variable enough... many do
EXACTLY the same thing"). A monster part's worth is its own ``richness``
(ingredient.json, 0.75-1.35 by its creature's lore, about 1.0 a tier), and
every ingredient brings a small ``side`` gift by its lore on top of the
dish's main benefit (``dish_sides``; cooking_rules.json ``sides``).

A DISH THAT PLAYS A SONG (3.5.2, songs.py): a dish may name ``song``, an id
in data/songs.json (its benefit is 'song', so it sits on the Special tab).
Eaten, it gives what every dish gives, and its power is the song's: it lasts
exactly as long as the song plays, in real seconds. Caviar and Tater Tots is
the first, Brandon's own song as A Man Before a King.
"""
import json
import math
from collections import Counter

from naming import quantity
from paths import data_path

MENU_TABS = ('hp', 'sp', 'mp', 'stat', 'special')
TAB_NAMES = {'hp': 'HP', 'sp': 'SP', 'mp': 'MP', 'stat': 'Stat', 'special': 'Special'}
STATS = ('STR', 'DEX', 'CON', 'INT', 'WIS', 'PER')
STAT_NAMES = {'STR': 'Strength', 'DEX': 'Dexterity', 'CON': 'Constitution',
              'INT': 'Intelligence', 'WIS': 'Wisdom', 'PER': 'Perception'}
# Resistances a legendary feast can make lasting.
RESISTS = ('fire_resist', 'cold_resist', 'shock_resist', 'poison_resist', 'acid_resist',
           'magic_resist', 'drain_resist', 'sleep_resist')
# Menu groups, in the order they are shown.
GROUPS = ('ready', 'building', 'legendary')
# What a trophy's permanent power does, for the menu line.
TROPHY_POWER_LINES = {
    'all_stats_plus_1': 'Every stat +1 for good',
    'plus_3_str': 'STR +3 for good',
    'plus_2_con_petrify_immune': 'CON +2 and Stoneproof for good',
    'plus_2_wis_auto_reveal_secret_doors': 'WIS +2 and hidden doors show, for good',
    'plus_2_str_confuse_immune': 'STR +2 and Clear-Headed for good',
    'fire_immunity': 'Fire Resist for good',
    'cold_immunity': 'Cold Resist for good',
    'petrify_immunity': 'Stoneproof for good',
    'chromatic_resist_all': 'Five elements hurt less, for good',
    'one_time_death_save': 'Cheat death once',
    'revive_once_at_half_hp': 'Rise once at half HP',
    'max_hp_per_floor_descent': '+2 Max HP every new floor',
    'max_mp_per_floor_descent_and_poison_immunity': '+2 Max MP every new floor, Poison Resist',
    'lifesteal_5pct_on_melee': 'Melee blows heal you, for good',
}

_cache: dict = {}


def _load(key: str, *parts) -> dict:
    if key not in _cache:
        try:
            with open(data_path(*parts), encoding='utf-8') as f:
                _cache[key] = json.load(f)
        except (OSError, ValueError):
            _cache[key] = {}
    return _cache[key]


def rules() -> dict:
    return _load('rules', 'data', 'cooking_rules.json')


def raw_recipes() -> dict:
    return _load('recipes', 'data', 'items', 'recipes.json')


def ingredients() -> dict:
    return _load('ingredients', 'data', 'items', 'ingredient.json')


def foods() -> dict:
    return _load('food', 'data', 'items', 'food.json')


def harvest_map() -> dict:
    return _load('harvest', 'data', 'items', 'harvest_map.json')


def aliases() -> dict:
    return harvest_map().get('aliases', {}) or {}


def resolve(item_id: str) -> str:
    """An ingredient id as the kitchen knows it today: a retired id (an old
    save's "goblin_shaman_prime") becomes the kept one ("goblin_prime")."""
    return aliases().get(item_id, item_id)


def ingredient_for_monster(monster_id: str):
    """The ingredient a corpse of ``monster_id`` yields, or None (a person
    yields none: ``is_person``)."""
    return (harvest_map().get('monsters', {}) or {}).get(monster_id)


# ----------------------------------------------------------------------
# People (Brandon, 2026-11-16: "Humans are not harvested. That's weird,
# we're not cannibals.")
# ----------------------------------------------------------------------

def people() -> frozenset:
    """The kinds whose body is searched, never harvested (harvest_map.json
    ``people``: humans and the human-like folk, decided by lore in
    tools/content/kitchen/people.txt)."""
    if 'people' not in _cache:
        _cache['people'] = frozenset(harvest_map().get('people', ()) or ())
    return _cache['people']


def is_person(kind, family=None) -> bool:
    """A person: a brigand, a knight, a cultist, an elf. His body is
    searched for what he carried (food_system.search_corpse), never
    harvested. A creature the harvest map does not know (Gilt Varro of the
    racing camp) is a person when its body says it is one of the mortals."""
    kind = str(kind or '')
    if kind in people():
        return True
    return family == 'mortals' and kind not in (harvest_map().get('monsters') or {})


def person_part_food(part_id: str):
    """The ordinary food an old save's part of a person becomes (harvest_map
    ``people_parts``: Bandit Trail Ham is dried meat), or None."""
    return (harvest_map().get('people_parts') or {}).get(part_id)


def is_special_food(part_id: str) -> bool:
    """A quest, key or one-of-a-kind food (food.json ``special``: the Magic
    Dungeon Carrot, the Starnut Tart, the mythic fruits). It goes into a dish
    of its own (Brandon, 2026-11-16: so a player is tempted to cook it), and
    holding it shows that dish under Building Toward, as a harvested part
    does."""
    return bool((foods().get(part_id) or {}).get('special'))


def book() -> list:
    """Every dish, each with its ``id``."""
    if 'book' not in _cache:
        _cache['book'] = [{'id': rid, **r} for rid, r in raw_recipes().items()
                          if isinstance(r, dict)]
    return _cache['book']


def recipe(rid: str):
    r = raw_recipes().get(rid)
    return {'id': rid, **r} if isinstance(r, dict) else None


def _index() -> dict:
    if 'index' not in _cache:
        single, uses = {}, {}
        for r in book():
            parts = list(dict.fromkeys(r.get('ingredients', [])))
            for p in parts:
                uses.setdefault(p, []).append(r)
            if len(parts) == 1:
                single[parts[0]] = r
        _cache['index'] = {'single': single, 'uses': uses}
    return _cache['index']


def single_dish_for(ingredient_id: str):
    """The one dish that cooks this ingredient on its own."""
    return _index()['single'].get(resolve(ingredient_id))


def dishes_with(ingredient_id: str) -> list:
    """Every dish that calls for this ingredient."""
    return list(_index()['uses'].get(resolve(ingredient_id), []))


# ----------------------------------------------------------------------
# Parts
# ----------------------------------------------------------------------

def part_kind(part_id: str):
    """'trophy', 'monster', 'forage' or 'food' (None if unknown)."""
    ing = ingredients().get(part_id)
    if ing:
        role = ing.get('tier_role')
        return 'trophy' if role == 'trophy' else ('forage' if role == 'dungeon' else 'monster')
    return 'food' if part_id in foods() else None


def part_floor(part_id: str) -> int:
    ing = ingredients().get(part_id)
    if ing:
        return int(ing.get('min_level', 1) or 1)
    return int((foods().get(part_id) or {}).get('min_level', 1) or 1)


def part_name(part_id: str) -> str:
    from naming import proper_name
    ing = ingredients().get(part_id) or foods().get(part_id) or {}
    return proper_name(ing.get('name') or part_id.replace('_', ' '))


def is_secret_part(part_id: str) -> bool:
    return bool((ingredients().get(part_id) or {}).get('secret'))


def is_harvested(part_id: str) -> bool:
    """A part that only a corpse gives (a monster part or a trophy)."""
    return part_kind(part_id) in ('monster', 'trophy')


def is_keystone(part_id: str) -> bool:
    """A part that puts its dishes under Building Toward when held: a
    harvested part, or a special food (``is_special_food``). A ration or a
    foraged find alone does not, or bread would put a hundred dishes there."""
    return is_harvested(part_id) or is_special_food(part_id)


def is_raw_trophy(item) -> bool:
    """A boss's trophy still raw in the pack (an ingredient whose tier_role
    is 'trophy'): one of a kind, and its feast is lost if it is eaten raw,
    fed to a pet or sold."""
    if item is None:
        return False
    if getattr(item, 'tier_role', '') == 'trophy':
        return True
    iid = str(getattr(item, 'id', '') or '')
    return bool(iid) and getattr(item, 'item_class', '') == 'ingredient' \
        and part_kind(resolve(iid)) == 'trophy'


def trophy_warning_lines(item) -> list:
    """What the ask-first prompt says before a raw trophy goes (bug bash
    3.5.1 Q2): there is only one, and what its dish would give."""
    ing = ingredients().get(resolve(str(getattr(item, 'id', '') or ''))) or {}
    power = ing.get('trophy_permanent_power') or getattr(item, 'trophy_permanent_power', '')
    what = TROPHY_POWER_LINES.get(power or '')
    return ["A boss's trophy, one of a kind: once it is gone, it is gone.",
            f"Cooked, its dish gives: {what}." if what
            else "Cooked, it makes a dish no other part can."]


NATURE_WORDS = {'hp': 'Hearty: HP dishes', 'sp': 'Filling: SP dishes',
                'mp': 'Arcane: MP dishes'}


def nature_line(ingredient_id: str) -> str:
    """What an ingredient is rich in, and how many dishes call for it, for
    the Kit: "Arcane: MP dishes | In 4 dishes"."""
    iid = resolve(ingredient_id)
    ing = ingredients().get(iid) or {}
    nature = ing.get('nature')
    if nature == 'stat':
        what = f"Sharpens {ing.get('stat_grant', '?')}: Stat dishes"
    elif nature == 'special':
        what = f"{power_label(ing.get('temp_power', ''))}: Special dishes"
    else:
        what = NATURE_WORDS.get(nature, 'Ingredient for cooking')
    if ing.get('tier_role') == 'trophy':
        what = 'Boss trophy: ' + what
    n = len(dishes_with(iid))
    return f"{what} | In {n} dishes" if n else what


# ----------------------------------------------------------------------
# A dish
# ----------------------------------------------------------------------

def parts(rec: dict) -> list:
    """The dish's different ingredients, in order."""
    return list(dict.fromkeys(rec.get('ingredients', []) or []))


def needs(rec: dict) -> Counter:
    return Counter(rec.get('ingredients', []) or [])


def dish_tab(rec: dict) -> str:
    """The dish's main benefit, which is its menu tab: hp, sp, mp, stat or special."""
    b = rec.get('benefit') or ''
    if b in ('hp', 'sp', 'mp'):
        return b
    if b in STATS:
        return 'stat'
    return 'special'


def dish_stat(rec: dict):
    b = rec.get('benefit')
    return b if b in STATS else None


def dish_power(rec: dict):
    if makes(rec) or song_of(rec):
        return None                       # a dish to carry, or a song's, has no timed power
    return rec.get('benefit') if dish_tab(rec) == 'special' else None


def makes(rec: dict):
    """The food a dish is cooked to carry (its ``makes``), or None."""
    return (rec or {}).get('makes') or None


def makes_ref(rec: dict):
    """(item class, id) of what a carry dish makes: a food id, or a
    class-qualified one ("potion:theriac": a brew cooked to carry, MONSTERS
    AND MAGIC 2026-11-19). None for any other dish."""
    m = makes(rec)
    if not m:
        return None
    if ':' in str(m):
        cls, iid = str(m).split(':', 1)
        return cls.strip(), iid.strip()
    return 'food', str(m)


def _made_def(rec: dict) -> dict:
    """The data entry of what a carry dish makes, whatever its class."""
    ref = makes_ref(rec)
    if not ref:
        return {}
    cls, iid = ref
    if cls == 'food':
        return dict(foods().get(iid) or {})
    try:
        import json
        from paths import data_path
        with open(data_path('data', 'items', f'{cls}.json'), encoding='utf-8') as f:
            return dict(json.load(f).get(iid) or {})
    except (OSError, ValueError):
        return {}


def song_of(rec: dict):
    """The song a dish plays when it is eaten (its ``song``: songs.py), or None."""
    return (rec or {}).get('song') or None


def song_share(rec: dict) -> str:
    """How much of a blow lands while the dish's song plays: "Half"."""
    import songs
    s = songs.song(song_of(rec)) or {}
    mult = float(s.get('damage_taken', 1.0) or 1.0)
    return {0.5: 'Half', 0.25: 'Quarter'}.get(mult) or f"{round(mult * 100)}%"


def song_lines(rec: dict) -> list:
    """The menu lines of a dish that plays a song: what its power does ("Half
    damage taken, for a while"). The song is never named: it is the surprise
    when the dish is eaten (Brandon, 2026-11-15)."""
    return [f"{song_share(rec)} damage taken, for a while"]


def carried_food(rec: dict) -> dict:
    """The food.json entry a carry dish makes ({} for any other dish; the
    potion.json entry for a brew cooked to carry)."""
    return _made_def(rec)


def band_of(floor: int) -> int:
    step = int(rules().get('band_floors', 20) or 20)
    return max(1, min(5, (int(floor) - 1) // step + 1))


def base_tier(rec: dict) -> int:
    """The band of the dish's deepest ingredient (1-5)."""
    ps = parts(rec)
    return band_of(max(part_floor(p) for p in ps)) if ps else 1


def big_dish_bonus(rec: dict) -> int:
    """The tiers a big dish rises above its deepest ingredient's band
    (Brandon, 2026-11-16: "Big dishes +1 tier"; cooking_rules.json
    ``big_dish``: a dish of ``parts`` or more different ingredients is
    ``tier_bonus`` tiers richer), within tier 5; 0 for a smaller dish."""
    big = rules().get('big_dish') or {}
    need = int(big.get('parts', 0) or 0)
    if not need or dish_size(rec) < need:
        return 0
    return max(0, min(5, base_tier(rec) + int(big.get('tier_bonus', 0) or 0)) - base_tier(rec))


def dish_tier(rec: dict) -> int:
    """The dish's tier (1-5), everywhere: the cook's question, the stat cap
    it teaches to, its numbers. The band of its deepest ingredient, and a
    big dish (``big_dish_bonus``) one tier richer, at most 5."""
    return base_tier(rec) + big_dish_bonus(rec)


_NUMBER_WORDS = {2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six'}
_TIER_WORDS = {1: 'one tier', 2: 'two tiers', 3: 'three tiers'}


def big_dish_line(rec: dict) -> str:
    """Why a big dish's tier is above its deepest part's, for the cook menu:
    "Five ingredients: one tier richer." ('' when it is not raised)."""
    bonus = big_dish_bonus(rec)
    if bonus <= 0:
        return ''
    n = dish_size(rec)
    return (f"{_NUMBER_WORDS.get(n, str(n))} ingredients: "
            f"{_TIER_WORDS.get(bonus, f'{bonus} tiers')} richer.")


def dish_size(rec: dict) -> int:
    return len(parts(rec))


def part_worth(part_id: str) -> float:
    """What one ingredient adds to a dish: a monster part or trophy its own
    richness (its creature's lore), a foraged find 0.6, a ration 0.5."""
    kind = part_kind(part_id) or 'food'
    if kind in ('monster', 'trophy'):
        rich = (ingredients().get(part_id) or {}).get('richness')
        if rich is not None:
            return float(rich)
    return float(rules().get('worth', {}).get(kind, 0.5))


def dish_worth(rec: dict) -> float:
    """What the ingredients add (``part_worth`` of each)."""
    return sum(part_worth(p) for p in parts(rec))


# The side gifts that are not a timed power.
SIDE_AMOUNTS = ('heal', 'mp')


def part_side(part_id: str):
    """An ingredient's side gift by its lore: a power id, 'heal' or 'mp'."""
    side = (ingredients().get(part_id) or {}).get('side')
    if side:
        return side
    return (rules().get('sides', {}).get('staples') or {}).get(part_id)


def dish_sides(rec: dict, tier: int, power=None) -> tuple:
    """((kind, amount), ...): the side gifts this dish's ingredients bring, in
    their order. A power lasts the tier's turns (at most its max_turns), a
    heal is a share of max HP, mana a number of points. The dish's own power
    is never given twice, nor one side by two ingredients."""
    if makes(rec) or song_of(rec):
        return ()
    spec = rules().get('sides') or {}
    powers = rules()['special']['powers']
    out, seen = [], {power}
    for p in parts(rec):
        side = part_side(p)
        if not side or side in seen:
            continue
        seen.add(side)
        if side == 'heal':
            out.append(('heal', float(_tierv(spec['heal_share'], tier))))
        elif side == 'mp':
            out.append(('mp', int(_tierv(spec['mp'], tier))))
        elif side in powers:
            cap = int((powers[side] or {}).get('max_turns', 60))
            out.append((side, min(cap, int(_tierv(spec['turns'], tier)))))
    return tuple(out)


def size_mult(n: int) -> float:
    table = rules().get('size_mult', {})
    n = max(1, min(5, int(n)))
    return float(table.get(str(n), 1.0))


def rung_of(rec: dict):
    """'plain' (staples alone), 'step' (one part and one staple) or None for
    every other dish (cooking_rules.json ``rungs``)."""
    return (rec or {}).get('rung') or None


def is_plain_fare(rec: dict) -> bool:
    return rung_of(rec) == 'plain'


def raw_gives(rec: dict) -> tuple:
    """(SP, HP) the dish's ingredients give eaten as they are."""
    sp = hp = 0
    for p in rec.get('ingredients', []) or []:
        d = ingredients().get(p) or foods().get(p) or {}
        sp += int(d.get('sp_restore', d.get('raw_sp', 0)) or 0)
        hp += int(d.get('hp_restore', 0) or 0)
    return sp, hp


def is_legendary(rec: dict) -> bool:
    return bool(rec.get('legendary'))


def is_trophy(rec: dict) -> bool:
    return bool(rec.get('trophy'))


def is_secret(rec: dict) -> bool:
    return any(is_secret_part(p) for p in parts(rec))


def trophy_powers(rec: dict) -> list:
    """The permanent powers of the boss trophies in this dish."""
    out = []
    if rec.get('permanent'):
        out.append(rec['permanent'])
    for p in parts(rec):
        pw = (ingredients().get(p) or {}).get('trophy_permanent_power')
        if pw and pw not in out:
            out.append(pw)
    return out


def _tierv(table, tier: int):
    return table[max(0, min(len(table) - 1, tier - 1))]


def dish_outcome(rec: dict) -> dict:
    """The numbers this dish gives, from the rules file (none of the hero's
    own state; ``apply_dish`` and ``dish_effects`` apply them to him)."""
    r = rules()
    tab = dish_tab(rec)
    t = dish_tier(rec)
    side = dish_worth(rec) * size_mult(dish_size(rec))
    grand = is_legendary(rec) or is_trophy(rec)
    low = (r.get('rungs') or {}).get(rung_of(rec)) if rung_of(rec) else None
    main = side * (float(r['legendary']['mult']) if grand else 1.0)
    if low:
        main *= float(low.get('main', 1.0))
    every = r['every_dish']
    out = {
        'tab': tab, 'tier': t, 'worth': dish_worth(rec), 'factor': main,
        'sp': int(round(_tierv(every['sp'], t) * side)),
        'heal_written': int(_tierv(every['heal_written'], t)),
        'heal_share': 0.0,
        'max_hp': int(every.get('max_hp', 2)),
        'mp_share': 0.0, 'mp_least': 0, 'sustained': 0,
        'stat': None, 'power': None, 'turns': 0, 'ward': 0,
        'permanent': None, 'trophy_powers': trophy_powers(rec),
        'song': song_of(rec),
    }
    if tab == 'hp':
        out['heal_share'] = min(1.0, _tierv(r['hp']['heal_share'], t) * main)
        out['max_hp'] += int(round(_tierv(r['hp']['max_hp_bonus'], t) * main))
    elif tab == 'sp':
        out['sp'] = int(round(_tierv(r['sp']['sp'], t) * main))
        # Sustained only from a big SP dish or a feast, for flat turns
        # (2026-11-22: it was on for most of a careful player's turns).
        if dish_size(rec) >= int(r['sp'].get('sustained_min_parts', 1)) or is_legendary(rec):
            out['sustained'] = min(int(r['sp'].get('sustained_cap', 800)),
                                   int(_tierv(r['sp']['sustained_turns'], t)))
    elif tab == 'mp':
        out['mp_share'] = min(1.0, _tierv(r['mp']['share'], t) * main)
        out['mp_least'] = int(round(_tierv(r['mp']['least'], t) * main))
    elif tab == 'stat':
        out['stat'] = dish_stat(rec)      # one whole point, up to its tier's cap
    elif makes(rec):
        out['power'] = None               # cooked to carry: what it gives is the food it makes
    elif song_of(rec):
        out['power'] = None               # its power is the song's (songs.py), timed by the song
    else:
        power = dish_power(rec)
        spec = r['special']
        cap = int((spec['powers'].get(power) or {}).get('max_turns', 60))
        out['power'] = power
        out['turns'] = max(1, min(cap, int(round(_tierv(spec['turns'], t) * main))))
        if power and power.startswith('save_guard_'):
            ww = spec.get('ward_worth', [1.0, 2.0, 3.5])
            w = dish_worth(rec)
            out['ward'] = min(3, 1 + (w >= ww[1]) + (w >= ww[2]) + (1 if grand else 0))
    if is_legendary(rec):
        leg = r['legendary']
        if tab == 'hp':
            out['permanent'] = ('max_hp', int(_tierv(leg['max_hp'], t)))
        elif tab == 'mp':
            out['permanent'] = ('max_mp', int(_tierv(leg['max_mp'], t)))
        elif tab == 'stat':
            out['permanent'] = ('stat', int(leg.get('stat_points', 1)))
        elif tab == 'special':
            out['permanent'] = ('resist', _feast_resist(rec))
    if low:
        for key in ('heal_written', 'max_hp'):
            if key in low:
                out[key] = int(low[key])
        # Cooked never gives less than eaten as it is, and a little more.
        more = float(r['rungs'].get('cooked_over_raw', 1.0))
        raw_sp, raw_hp = raw_gives(rec)
        out['sp'] = max(out['sp'], math.ceil(raw_sp * more))
        out['heal_least'] = math.ceil(raw_hp * more)
    # Each ingredient's side gift (variety, 2026-11-22).
    out['sides'] = dish_sides(rec, t, out['power'])
    out['side_heal'] = sum(a for k, a in out['sides'] if k == 'heal')
    out['side_mp'] = sum(a for k, a in out['sides'] if k == 'mp')
    return out


# Resistances a boss trophy's own power already makes lasting: a feast that
# holds the trophy gives a different one rather than the same twice.
TROPHY_RESISTS = {'fire_immunity': 'fire_resist', 'cold_immunity': 'cold_resist',
                  'max_mp_per_floor_descent_and_poison_immunity': 'poison_resist'}
# The fallback order when a feast's own resistances are all taken.
_RESIST_FALLBACK = ('magic_resist', 'drain_resist', 'sleep_resist', 'shock_resist',
                    'acid_resist', 'cold_resist', 'fire_resist', 'poison_resist')


def _feast_resists(rec: dict) -> list:
    """The resistances a special feast may make lasting, best first: its own
    power if that is a resistance, then its ingredients', then the fallback
    order; never one its trophy already gives for good."""
    taken = {TROPHY_RESISTS[p] for p in trophy_powers(rec) if p in TROPHY_RESISTS}
    cands = [dish_power(rec)] + [(ingredients().get(part) or {}).get('temp_power')
                                 for part in parts(rec)] + list(_RESIST_FALLBACK)
    order = []
    for c in cands:
        if c in RESISTS and c not in taken and c not in order:
            order.append(c)
    return order


def _feast_resist(rec: dict) -> str:
    """The resistance a special feast makes lasting (for a hero who holds
    none for good yet): the first of ``_feast_resists``."""
    return _feast_resists(rec)[0]


def held_for_good(player, status: str) -> bool:
    """The hero has ``status`` for good (a -1 status: a trophy, a feast,
    Fafnir's Blood, a trait)."""
    return int((getattr(player, 'status_effects', None) or {}).get(status, 0) or 0) == -1


def feast_resist_for(player, rec: dict):
    """The resistance this special feast makes lasting for THIS hero: the
    first of its own (``_feast_resists``) he does not hold for good already,
    or None when he holds them all. Fafnir's Blood gives fire resistance for
    good, and Fafnir's own fire feast then gave nothing: "You already have
    Fire Resist for good" (bug bash 3.5.1 A)."""
    for c in _feast_resists(rec):
        if not held_for_good(player, c):
            return c
    return None


def power_label(power: str) -> str:
    from status_effects import EFFECT_INFO
    info = EFFECT_INFO.get(power)
    return info[0] if info else str(power).replace('_', ' ').title()


# ----------------------------------------------------------------------
# The hero's numbers
# ----------------------------------------------------------------------

def heal_amount(player, out: dict) -> int:
    from floor_curve import mend
    from food_system import meal_mend_share
    written = out['heal_written']
    # (plain fare has no written heal, and so no snack's share of the bar)
    share = max(meal_mend_share(written) if written > 0 else 0.0, out['heal_share'])
    mx = int(getattr(player, 'max_hp', 1) or 1)
    side = int(round(float(out.get('side_heal', 0.0) or 0.0) * mx))       # an ingredient's gift
    return max(mend(written, mx, share), int(out.get('heal_least', 0))) + side


def mp_amount(player, out: dict) -> int:
    side = int(out.get('side_mp', 0) or 0)                 # an ingredient's gift
    if out['tab'] != 'mp':
        return side
    return max(int(round(out['mp_share'] * int(getattr(player, 'max_mp', 0) or 0))),
               int(out['mp_least'])) + side


def side_line(player, out: dict) -> str:
    """The dish's side gifts, for the menu: "Also: Dark Vision, 90 turns;
    +4 MP" ('' when it has none). A heal or mana side already counted in the
    dish's own HP or MP line is not said twice; a power held for good is
    left out."""
    bits = []
    for kind, amount in out.get('sides', ()):
        if kind == 'heal':
            if out['tab'] != 'hp':
                bits.append(f"+{int(round(amount * int(getattr(player, 'max_hp', 1) or 1)))} HP")
        elif kind == 'mp':
            if out['tab'] != 'mp':
                bits.append(f"+{int(amount)} MP")
        elif not held_for_good(player, kind):
            bits.append(f"{power_label(kind)}, {quantity(int(amount), 'turn')}")
    return ("Also: " + "; ".join(bits)) if bits else ''


def floor_hp_room(player) -> int:
    """Max HP cooking can still add on this floor (the per-floor cap)."""
    cap = int(getattr(player, 'PER_FLOOR_HP_CAP', 5))
    return max(0, cap - int(getattr(player, '_cook_hp_gain_this_floor', 0) or 0))


def max_hp_room(player) -> int:
    """Max HP an ordinary meal can still add now: what is left of the
    floor's cap. There is no cap across floors (Brandon, 2026-11-16: "there
    should be a per floor limit to hp gained, but not a max across several
    floors... that encourages cooking"); the lifetime cap of 4 a floor
    reached, and the menu's "Max HP: all cooking can give at this depth",
    are gone."""
    return floor_hp_room(player)


def feast_mp_cap(player) -> int:
    """Max MP feasts can add on one floor (cooking_rules legendary
    max_mp_floor_cap). Like max HP from meals, it has no cap across floors
    (Brandon, 2026-11-17: MP "same as HP"); the old lifetime cap by the
    deepest floor reached (a quarter of a point a floor, at least 4) is gone."""
    return int(rules().get('legendary', {}).get('max_mp_floor_cap', 4))


def feast_mp_room(player) -> int:
    """Max MP a feast can still add on this floor."""
    return max(0, feast_mp_cap(player) - int(getattr(player, '_feast_mp_gain_this_floor', 0) or 0))


def dish_effects(player, rec: dict) -> list:
    """Short, plain lines of what this dish does for THIS hero now, main
    benefit first: "+45 HP", "+2 Max HP", "+12 MP", "Teaches DEX (a full
    point)", "Dark Vision, 300 turns". A cap that would eat the benefit says
    so ("Max HP full this floor", "DEX lesson used this floor")."""
    if makes(rec):
        return carry_lines(rec)
    out = dish_outcome(rec)
    tab = out['tab']
    lines = []
    # SP cannot pass the bar's top: a feast's SP reads as "+210 SP", not "+1104".
    max_sp = int(getattr(player, 'max_sp', 0) or 0)
    sp_shown = min(out['sp'], max_sp) if max_sp > 0 else out['sp']
    if tab == 'hp':
        lines.append(f"+{heal_amount(player, out)} HP")
    elif tab == 'sp':
        lines.append(f"+{sp_shown} SP")
        if out['sustained'] > 0:
            lines.append(f"Sustained, {quantity(out['sustained'], 'turn')}")
    elif tab == 'mp':
        lines.append(f"+{mp_amount(player, out)} MP")
    elif tab == 'stat':
        lines.append(_stat_line(player, out))
        cap_line = _stat_cap_line(player, out)
        if cap_line:
            lines.append(cap_line)
    elif out.get('song'):
        lines.extend(song_lines(rec))
    else:
        label = power_label(out['power'])
        bonus = f" (+{out['ward']})" if out['ward'] else ''
        if held_for_good(player, out['power']):
            lines.append(f"{label}: already yours for good")
        else:
            lines.append(f"{label}{bonus}, {quantity(out['turns'], 'turn')}")
    if is_legendary(rec) and (getattr(player, 'quirk_progress', None) or {}).get('fatted_calf_active'):
        # The Fatted Calf (a trait): a feast heals the hero fully
        # (food_system._apply_recipe_outcome). The menu said only its own
        # heal, if any.
        lines.append("Heals you fully")
    room = max_hp_room(player)
    if is_plain_fare(rec) and out['max_hp'] <= 0:
        lines.append(PLAIN_NO_MAX_HP)
    elif tab == 'hp' or room > 0:
        gain = min(out['max_hp'], room)
        if gain > 0:
            lines.append(f"+{gain} Max HP")
        elif tab == 'hp':
            lines.append(MAX_HP_FULL_FLOOR)
    also = side_line(player, out)
    if also:
        lines.append(also)
    lines.extend(_lasting_lines(player, out, rec))
    if tab != 'sp':
        lines.append(f"+{sp_shown} SP")
    return lines


MAX_HP_FULL_FLOOR = "Max HP full this floor"
# Plain fare's value for sorting: under the least dish with a part in it (a
# foraged find alone, 0.6).
PLAIN_SORT_SHARE = 0.25
PLAIN_NO_MAX_HP = "Plain fare: no Max HP"
PLAIN_NO_MAX_HP_MSG = "Plain fare adds no max HP. A creature's part does."


def _lasting_lines(player, out: dict, rec=None) -> list:
    """The part of ``dish_effects`` that lasts for good: a feast's permanent
    gift, then each boss trophy's own power. A gift a lifetime cap would
    eat (max MP, a stat) says so, as apply_dish will; a feast's max HP has
    no cap (it passes the floor's, and there is none across floors)."""
    lines = []
    perm = out['permanent']
    if perm:
        kind, val = perm
        if kind == 'max_hp':
            lines.append(f"+{int(val)} Max HP for good")
        elif kind == 'max_mp':
            room_mp = min(val, feast_mp_room(player))
            lines.append(f"+{room_mp} Max MP for good" if room_mp > 0
                         else "Max MP: all a feast can give on this floor")
        elif kind == 'stat':
            got = _feast_stat_points(player, out, int(val))
            lines.append(f"+{got} {out['stat']} for good" if got > 0
                         else f"No more {out['stat']} for good from a dish this deep")
        elif kind == 'resist':
            res = feast_resist_for(player, rec) if rec is not None else val
            lines.append(f"{power_label(res)} for good" if res
                         else "Every resistance already yours for good")
    for pw in out['trophy_powers']:
        lines.append(TROPHY_POWER_LINES.get(pw, 'A lasting power'))
    return lines


def _stat_block(player, out: dict):
    """cut_stat_block for this stat dish's stat at its tier ('cap', 'tier',
    'floor' or None), or None for a player without the caps (a harness)."""
    if not hasattr(player, 'cut_stat_block'):
        return None
    return player.cut_stat_block(out['stat'], out['tier'])


def _feast_stat_points(player, out: dict, val: int) -> int:
    """The stat points a legendary stat feast's lasting gift will give this
    hero: ``val``, held to what a dish of the feast's tier may still teach
    the stat after the meal's own lesson has taught its point
    (Player.cooking_stat_softcap, which counts the altar's points:
    food_taught). The menu said "+1 STR for good" to a hero at the cap, who
    got nothing (bug bash 3.5.1 A)."""
    stat = out['stat']
    if not hasattr(player, 'cooking_stat_softcap') or not hasattr(player, 'food_taught'):
        return val
    if stat not in (getattr(player, 'cooking_stat_gained', None) or {}):
        return 0
    room = max(0, int(player.cooking_stat_softcap(stat, out['tier'])) - int(player.food_taught(stat)))
    lesson = 1 if _stat_block(player, out) is None else 0
    return max(0, min(int(val), room - lesson))


def carry_lines(rec: dict) -> list:
    """The menu lines of a dish cooked to carry: that it goes in the pack,
    and what the food it makes gives when it is eaten."""
    from naming import proper_name
    f = carried_food(rec)
    name = proper_name(f.get('name') or rec.get('name') or 'it')
    lines = [f"Made to carry: one {name} into your pack"]
    eat = []
    if int(f.get('sp_restore', 0) or 0) > 0:
        eat.append(f"+{int(f['sp_restore'])} SP")
    if int(f.get('hp_restore', 0) or 0) > 0:
        eat.append(f"+{int(f['hp_restore'])} HP")
    if eat:
        lines.append("If eaten: " + ", ".join(eat))
    if f.get('drink_line'):
        lines.append("If drunk: " + str(f['drink_line']))
    return lines


def dish_lasting(player, rec: dict) -> list:
    """The lines of ``dish_effects`` that last for good (a legendary feast's
    permanent bonus, a boss trophy's power), in the same words: the cook
    menu shows them under their own heading, apart from what the dish does
    now."""
    return _lasting_lines(player, dish_outcome(rec), rec)


def _stat_line(player, out: dict) -> str:
    """A stat dish's first menu line: "Teaches DEX +1", or why it would
    teach nothing now (the floor's lesson used, its tier's cap, or all food
    can teach)."""
    stat = out['stat']
    block = _stat_block(player, out)
    if block == 'cap':
        return f"{stat} has learned all food can teach"
    if block == 'tier':
        return f"{stat} has learned all a dish this simple can teach"
    if block == 'floor':
        return f"{stat} lesson used this floor"
    return f"Teaches {stat} +1"


def _stat_cap_line(player, out: dict) -> str:
    """How far a dish of this tier can raise its stat, and how far food has
    taken it, so a player can plan his build by what he eats: "Tier 1
    dishes teach DEX up to +8 (now +3)". At its tier's cap, that deeper
    creatures teach more. Empty for a player without the caps."""
    if not hasattr(player, 'cooking_stat_softcap') or not hasattr(player, 'food_taught'):
        return ''
    stat, tier = out['stat'], out['tier']
    if stat not in (getattr(player, 'cooking_stat_gained', None) or {}):
        return ''
    cap = int(player.cooking_stat_softcap(stat, tier))
    now = int(player.food_taught(stat))
    line = f"Tier {tier} dishes teach {stat} up to +{cap} (now +{now})"
    if _stat_block(player, out) == 'tier':
        line += ": deeper creatures teach more"
    return line


def dish_value(player, rec: dict) -> float:
    """How much a dish gives, for sorting rows of one tab: deeper and richer
    dishes first, and plain fare, which builds nothing, after every dish
    with a part in it."""
    out = dish_outcome(rec)
    v = out['factor'] * (1.0 + 0.3 * (out['tier'] - 1))
    if is_plain_fare(rec):
        v *= PLAIN_SORT_SHARE
    if out['permanent'] or out['trophy_powers']:
        v += 10.0
    return round(v, 4)


# ----------------------------------------------------------------------
# The pack and the menu
# ----------------------------------------------------------------------

def held_counts(inventory) -> Counter:
    """How many of each kitchen part the pack holds: ingredients and food,
    stacks counted, retired ids read as the kept ones."""
    from items import Food, Ingredient
    counts: Counter = Counter()
    for item in inventory or []:
        if isinstance(item, (Ingredient, Food)):
            counts[resolve(getattr(item, 'id', ''))] += max(1, int(getattr(item, 'count', 1) or 1))
    return counts


def can_cook(rec: dict, counts: Counter) -> bool:
    return all(counts.get(p, 0) >= n for p, n in needs(rec).items())


def ready_dishes(inventory) -> list:
    """Every dish the pack can cook now, single dishes first, then by name."""
    counts = held_counts(inventory)
    out = [r for r in book() if can_cook(r, counts)]
    out.sort(key=lambda r: (dish_size(r), r.get('name', '')))
    return out


# ----------------------------------------------------------------------
# Hunting (Brandon, 2026-11-16: "for recipes in progress, you should be
# able to toggle it to 'hunt' for the ingredients, meaning a monster or
# ingredient you need is gold text in the right panel ... no limit to how
# many you can hunt at once")
# ----------------------------------------------------------------------

def hunted(player) -> set:
    """The ids of the dishes the hero is hunting for (Player.hunted_dishes,
    kept in the save; an old save has none). As many as he likes."""
    d = getattr(player, '__dict__', None)
    if d is None:
        return set()
    s = d.setdefault('hunted_dishes', set())
    if not isinstance(s, set):
        s = d['hunted_dishes'] = set(s or ())
    return s


def is_hunted(player, rid: str) -> bool:
    return rid in hunted(player)


def toggle_hunt(player, rid: str) -> bool:
    """H in the cook menu: hunt this dish, or stop. Returns whether it is
    hunted now."""
    s = hunted(player)
    if rid in s:
        s.discard(rid)
        return False
    s.add(rid)
    return True


def hunted_parts(player, inventory=None) -> set:
    """The parts the hero is hunting: what every hunted dish still lacks
    (a part held in the number a dish needs is no longer hunted)."""
    hs = hunted(player)
    if not hs:
        return set()
    counts = held_counts(getattr(player, 'inventory', None) if inventory is None else inventory)
    out = set()
    for rid in hs:
        rec = recipe(rid)
        if rec is None:
            continue
        for p, n in needs(rec).items():
            if counts.get(p, 0) < n:
                out.add(p)
    return out


def monster_hunted(monster, parts) -> bool:
    """A creature whose harvest gives one of ``parts`` (hunted_parts)."""
    if not parts:
        return False
    iid = ingredient_for_monster(getattr(monster, 'kind', '') or getattr(monster, 'id', ''))
    return bool(iid) and resolve(iid) in parts


def item_hunted(item, parts) -> bool:
    """A thing on the ground that is one of ``parts`` (hunted_parts)."""
    return bool(parts) and resolve(getattr(item, 'id', '') or '') in parts


def lesson_spent(player, rec: dict, counts):
    """The stat whose lesson this step would spend, or None: its part, the
    only one held, would teach the hero that stat this floor cooked on its
    own. The menu lists such a dish last and says so (``lesson_line``): a
    hurt hero took the biggest meal and lost the floor's lesson with it
    (the measure of 2026-11-22)."""
    if rung_of(rec) != 'step':
        return None
    part = parts(rec)[0]
    if counts.get(part, 0) != 1:
        return None
    single = single_dish_for(part)
    return dish_stat(single) if single and _would_teach(player, single) else None


def lesson_line(player, rec: dict, counts) -> str:
    """"Cooked alone, Cobra Tail Steak teaches DEX +1", or ''."""
    stat = lesson_spent(player, rec, counts)
    return f"Cooked alone, {part_name(parts(rec)[0])} teaches {stat} +1" if stat else ''


def _row(player, rec: dict, counts: Counter) -> dict:
    need = needs(rec)
    have, missing = [], []
    for p in parts(rec):
        n = need[p]
        h = min(n, counts.get(p, 0))
        entry = {'id': p, 'name': part_name(p), 'have': h, 'need': n}
        (have if h >= n else missing).append(entry)
    ready = not missing
    grand = is_legendary(rec) or is_trophy(rec)
    return {
        'id': rec['id'], 'recipe': rec, 'name': rec.get('name', ''),
        'group': 'legendary' if grand else ('ready' if ready else 'building'),
        'ready': ready, 'legendary': is_legendary(rec), 'trophy': is_trophy(rec),
        'tier': dish_tier(rec), 'have': have, 'missing': missing,
        'have_count': len(have), 'need_count': len(need),
        'progress': f"{len(have)} of {len(need)}",
        'value': dish_value(player, rec), 'effects': dish_effects(player, rec),
        'hunted': (not ready) and is_hunted(player, rec['id']),
        'lesson': lesson_line(player, rec, counts),
    }


def menu_rows(player, inventory, tab: str) -> list:
    """The cook menu's rows for one tab, in three groups (``row['group']``):

    1. ``ready``: dishes the pack can cook now, the most giving first, and
       last any that would spend the floor's stat lesson (``lesson_spent``);
    2. ``building``: dishes the hero holds at least one HARVESTED part of
       (a monster part or a trophy) or a special food of (the Magic
       Dungeon Carrot: ``is_keystone``; a ration or a foraged find alone
       does not count, or bread would put a hundred dishes here) but not
       all, the closest first ("2 of 4", with what is missing named), and
       any dish the hero has learned of (``player.dishes_learned``: the
       Mooble's Starnut Tart), held parts or none;
    3. ``legendary``: legendary feasts and boss-trophy dishes, ready ones
       first, then the closest; shown once the hero holds any harvested
       part of them. Kept apart, and marked, so the big payoff stands out.

    Secrets stay secret: a dish needing a part of a hidden creature (the cow
    level) never shows until the hero holds that part.
    """
    counts = held_counts(inventory)
    learned = set(getattr(player, 'dishes_learned', None) or ())
    rows = []
    for rec in book():
        if dish_tab(rec) != tab:
            continue
        ps = parts(rec)
        if any(is_secret_part(p) and counts.get(p, 0) <= 0 for p in ps):
            continue
        if not can_cook(rec, counts) and rec['id'] not in learned and not any(
                is_keystone(p) and counts.get(p, 0) > 0 for p in ps):
            continue
        rows.append(_row(player, rec, counts))
    order = {g: i for i, g in enumerate(GROUPS)}

    def key(row):
        closeness = row['have_count'] / max(1, row['need_count'])
        if row['group'] == 'ready':
            return (order['ready'], 1 if row['lesson'] else 0, -row['value'], row['name'])
        if row['group'] == 'building':
            return (order['building'], 0, -closeness, len(row['missing']), -row['value'], row['name'])
        return (order['legendary'], 0 if row['ready'] else 1, -closeness, -row['value'], row['name'])
    rows.sort(key=key)
    return rows


def _would_teach(player, rec: dict) -> bool:
    stat = dish_stat(rec)
    if not stat:
        return False
    if not hasattr(player, 'cut_stat_block'):
        return True
    return player.cut_stat_block(stat, dish_tier(rec)) is None


def opening_tab(player, inventory) -> str:
    """The tab for the hero's most urgent need, among tabs with a dish ready:
    hurt (under half HP): HP; hungry (SP under 30%): SP, else HP, and with
    neither ready still where food is (never Stat or MP); low on mana (under
    40%) with spells known: MP; else Stat while the floor's lesson is open
    and a stat dish would teach; else the tab with the most dishes ready
    (with none ready, the tab with the most rows)."""
    return opening_choice(player, inventory)[0]


# Why the cook menu opened on its tab: ``opening_choice``'s second value.
OPEN_REASONS = ('hurt', 'hungry', 'hungry_missing', 'mana', 'lesson', 'most_ready',
                'most_rows', 'nothing')


def opening_choice(player, inventory) -> tuple:
    """``(tab, why)``: the tab ``opening_tab`` opens on, and why, so the menu
    can say it ("You are hurt"): 'hurt', 'hungry', 'hungry_missing' (hungry,
    and no SP or HP dish is ready: the tab shows what each still needs),
    'mana', 'lesson', 'most_ready' (the tab with the most dishes ready),
    'most_rows' (nothing ready anywhere: the tab with the most dishes being
    built toward) or 'nothing' (no rows in any tab)."""
    counts = held_counts(inventory)
    ready = {t: [] for t in MENU_TABS}
    for rec in book():
        if can_cook(rec, counts):
            ready[dish_tab(rec)].append(rec)

    def frac(cur, mx):
        mx = int(mx or 0)
        return 1.0 if mx <= 0 else float(cur or 0) / mx
    if ready['hp'] and frac(getattr(player, 'hp', 0), getattr(player, 'max_hp', 0)) < 0.5:
        return 'hp', 'hurt'
    if frac(getattr(player, 'sp', 0), getattr(player, 'max_sp', 0)) < 0.3:
        # A starving hero's menu opens where food is, never on a Stat or MP
        # dish (bug bash 3.5.1 Q4, Brandon 2026-11-16): the SP tab, or the HP
        # tab if a hearty dish is ready, or the one that is closest, saying
        # what is missing.
        if ready['sp']:
            return 'sp', 'hungry'
        if ready['hp']:
            return 'hp', 'hungry'
        rows = {t: menu_rows(player, inventory, t) for t in MENU_TABS}
        if any(rows.values()):
            return ('hp' if rows['hp'] and not rows['sp'] else 'sp'), 'hungry_missing'
    if (ready['mp'] and getattr(player, 'known_spells', None)
            and frac(getattr(player, 'mp', 0), getattr(player, 'max_mp', 0)) < 0.4):
        return 'mp', 'mana'
    if any(_would_teach(player, r) for r in ready['stat']):
        return 'stat', 'lesson'
    best = max(MENU_TABS, key=lambda t: (len(ready[t]), -MENU_TABS.index(t)))
    if ready[best]:
        return best, 'most_ready'
    sizes = {t: len(menu_rows(player, inventory, t)) for t in MENU_TABS}
    best = max(MENU_TABS, key=lambda t: (sizes[t], -MENU_TABS.index(t)))
    return (best, 'most_rows') if sizes[best] else ('hp', 'nothing')


# ----------------------------------------------------------------------
# Applying a dish (food_system.cook_compound_recipe's callback)
# ----------------------------------------------------------------------

def _add_effect(player, name: str, turns: int, cap: int) -> None:
    """A timed status for a meal: longer than the usual 60-turn cap, as far
    as the rules allow for that power."""
    try:
        player.add_effect(name, turns, cap=cap)
    except TypeError:                       # a harness player with the old signature
        player.add_effect(name, turns)


def apply_dish(player, rec: dict) -> list:
    """A dish cooked right: everything it gives, applied to the hero.
    Returns the message lines (the first names the dish)."""
    from food_system import _apply_permanent_power
    hunted(player).discard(rec.get('id'))      # cooked: the hunt for it is over
    if makes(rec):
        return make_to_carry(player, rec)
    out = dish_outcome(rec)
    name = rec.get('name', 'the dish')
    msgs = [f"You prepare {name}."]
    tab = out['tab']
    # Food is food: SP and a heal from every dish.
    sp_before = int(getattr(player, 'sp', 0) or 0)
    if out['sp'] > 0:
        player.restore_sp(out['sp'])
    sp = max(0, int(getattr(player, 'sp', 0) or 0) - sp_before) if hasattr(player, 'sp') else out['sp']
    # What came back, as the SP is told: a dish eaten unhurt said "+9 HP",
    # and one eaten with full mana "+0 MP" (bug bash 3.5.1 E).
    heal = heal_amount(player, out)
    healed = 0
    if heal > 0:
        healed = int(player.restore_hp(heal) or 0)
    bits = [f"+{sp} SP"] if sp > 0 else []
    if healed > 0:
        bits.append(f"+{healed} HP")
    mp = mp_amount(player, out)
    if mp > 0:
        before = int(getattr(player, 'mp', 0) or 0)
        player.restore_mp(mp)
        got = int(getattr(player, 'mp', 0) or 0) - before
        if got > 0:
            bits.append(f"+{got} MP")
    if bits:
        msgs.append("You eat it: " + ", ".join(bits) + ".")
    # Max HP toward the floor's cap.
    if hasattr(player, 'try_apply_cook_hp_gain'):
        applied = player.try_apply_cook_hp_gain(out['max_hp'])
    else:
        applied = out['max_hp']
        player.increase_max_hp(applied, from_cooking=True)
    if applied > 0:
        msgs.append(f"{'The meal fortifies you' if tab == 'hp' else 'Good food builds you up'}. "
                    f"(+{applied} max HP)")
    elif tab == 'hp' and out['max_hp'] <= 0:
        msgs.append(PLAIN_NO_MAX_HP_MSG)
    elif tab == 'hp':
        msgs.append("You feel sated, but your body is already full of nourishment this floor.")
    # The main benefit.
    if tab == 'sp' and out['sustained'] > 0:
        _add_effect(player, 'sustained', out['sustained'], int(rules()['sp'].get('sustained_cap', 800)))
        msgs.append(f"You are Sustained for {quantity(out['sustained'], 'turn')}: "
                    f"hunger comes at half its pace.")
    elif tab == 'stat':
        msgs.extend(_teach(player, out['stat'], out['tier']))
    lingers = None
    if tab == 'special' and out.get('song'):
        import songs
        msgs.extend(songs.begin(player, out['song']))
    elif tab == 'special':
        power = out['power']
        cap = int((rules()['special']['powers'].get(power) or {}).get('max_turns', 60))
        if held_for_good(player, power):
            # A power held for good already: the meal adds nothing to it
            # (it said "lingers for 240 turns" over a lasting one).
            msgs.append(f"You already have {power_label(power)} for good.")
        else:
            _add_effect(player, power, out['turns'], cap)
            if power.startswith('save_guard_'):
                cat = power[len('save_guard_'):]
                if getattr(player, '_save_guard', None) is None:
                    player._save_guard = {}
                player._save_guard[cat] = max(int(player._save_guard.get(cat, 0) or 0), out['ward'])
            lingers = f"{power_label(power)} lingers for {quantity(out['turns'], 'turn')}."
            msgs.append(lingers)
    # Each ingredient's side gift (its heal and mana came with the meal).
    gifts = []
    for kind, amount in out.get('sides', ()):
        if kind in SIDE_AMOUNTS or held_for_good(player, kind):
            continue
        cap = int((rules()['special']['powers'].get(kind) or {}).get('max_turns', 60))
        _add_effect(player, kind, int(amount), cap)
        if kind.startswith('save_guard_'):
            if getattr(player, '_save_guard', None) is None:
                player._save_guard = {}
            cat = kind[len('save_guard_'):]
            player._save_guard[cat] = max(int(player._save_guard.get(cat, 0) or 0), 1)
        gifts.append(f"{power_label(kind)} for {quantity(int(amount), 'turn')}")
    if gifts:
        msgs.append("It also gives you " + ", ".join(gifts) + ".")
    # A legendary feast's permanent bonus.
    if out['permanent']:
        msgs.extend(_apply_permanent(player, rec, out))
    # A boss trophy's own power.
    for pw in out['trophy_powers']:
        fake = dict(rec, permanent_power=pw, permanent_desc='')
        line = _apply_permanent_power(player, pw, fake)
        if line:
            msgs.append(line.strip())
    # The timed power made lasting by this very meal (Surtur's coal: Fire
    # Resist for 360 turns, then for good): only the lasting line stands.
    if lingers and held_for_good(player, out['power']):
        msgs.remove(lingers)
    return msgs


def make_to_carry(player, rec: dict) -> list:
    """A dish cooked to carry, cooked right: the food it makes goes in the
    pack, uneaten. Ingredients weigh nothing (Brandon, 2026-11-16) and food
    does, so the dish can weigh more than what went into it: when the pack
    cannot take it, it is set down at the hero's feet (``take_set_down``,
    which the Game empties onto the floor: Game._cook_compound), as a part
    too heavy to carry is. Returns the message lines (the first names the
    dish)."""
    from items import make_item_by_id
    from naming import proper_name
    name = rec.get('name', 'the dish')
    cls, iid = makes_ref(rec)
    item = make_item_by_id(cls, iid)
    if item is None:
        return [f"You prepare {name}, but nothing comes of it."]
    item.count = 1
    item.identified = True
    adder = getattr(player, 'add_to_inventory', None)
    if adder is None:
        player.inventory.append(item)            # a harness player with no carry limit
    elif not adder(item):
        player.__dict__.setdefault('cooked_set_down', []).append(item)
        return [f"You prepare {name}.",
                f"You wrap the {proper_name(item.name)} to carry, but your pack is too heavy: "
                f"you set it down at your feet."]
    return [f"You prepare {name}.",
            f"You wrap the {proper_name(item.name)} to carry. It is in your pack."]


def take_set_down(player) -> list:
    """The carried dishes the pack could not take (``make_to_carry``), now
    handed to the caller to set on the floor; the list is emptied."""
    d = getattr(player, '__dict__', None)
    return list(d.pop('cooked_set_down', None) or ()) if d is not None else []


def _teach(player, stat: str, tier: int) -> list:
    """The floor's stat lesson from a stat dish of ``tier``: one whole
    point, or why it taught nothing."""
    label = STAT_NAMES.get(stat, stat)
    if not hasattr(player, 'feed_cut_stat'):
        return []
    block = player.cut_stat_block(stat, tier) if hasattr(player, 'cut_stat_block') else None
    gained = int(player.feed_cut_stat(stat, tier) or 0)
    if gained > 0:
        return [f"Your {label} increases by {gained}!"]
    if block == 'tier':
        return [f"Your {label} has learned all a dish this simple can teach. Deeper creatures teach more."]
    if block == 'cap':
        return [f"Your {label} has learned all food can teach it."]
    if block == 'floor':
        return ["You have already learned from a meal on this floor. The next lesson waits on a new floor."]
    return []


def _apply_permanent(player, rec: dict, out: dict) -> list:
    kind, val = out['permanent']
    if kind == 'max_hp':
        # Past the floor's cap, and no cap across floors (Brandon, 2026-11-16).
        if hasattr(player, 'try_apply_cook_hp_gain'):
            got = player.try_apply_cook_hp_gain(int(val), bypass=True)
        else:
            got = int(val)
            player.increase_max_hp(got, from_cooking=True)
        return [f"A feast to remember: +{got} max HP for good."] if got > 0 else []
    if kind == 'max_mp':
        got = min(int(val), feast_mp_room(player))
        if got <= 0:
            return ["A feast to remember, but your mana has taken all a feast can give on this floor."]
        player.max_mp = int(getattr(player, 'max_mp', 0) or 0) + got
        player.mp = int(getattr(player, 'mp', 0) or 0) + got
        player.cooking_mp_gained = int(getattr(player, 'cooking_mp_gained', 0) or 0) + got
        player._feast_mp_gain_this_floor = int(getattr(player, '_feast_mp_gain_this_floor', 0) or 0) + got
        return [f"A feast to remember: +{got} max MP for good."]
    if kind == 'stat':
        stat = out['stat']
        got = player.try_apply_cook_stat_gain(stat, int(val), bypass=True, tier=out['tier']) \
            if hasattr(player, 'try_apply_cook_stat_gain') else 0
        label = STAT_NAMES.get(stat, stat)
        return [f"A feast to remember: your {label} rises by {got}, for good."] if got > 0 else \
            [f"A feast to remember, but your {label} has learned all a dish this deep can teach it."]
    if kind == 'resist':
        val = feast_resist_for(player, rec)
        if val is None:
            return ["A feast to remember, but you already resist all it could give, for good."]
        player.add_effect(val, -1)
        return [f"A feast to remember: {power_label(val)}, for good."]
    return []


def salvage_dish(player, rec: dict) -> list:
    """Persephone's Descent: a ruined dish still gives a share of its SP,
    healing and mana (rules ``salvage.share``); nothing else."""
    out = dish_outcome(rec)
    share = float(rules().get('salvage', {}).get('share', 0.5))
    name = rec.get('name', 'the dish')
    msgs = [f"You ruin the preparation of {name}, but Persephone's grace saves the seed."]
    if makes(rec):
        # A dish cooked to carry is the food it makes: a share of what that
        # gives eaten. It gave a share of a dish's numbers it never had, so a
        # ruined Starnut Tart fed more (86 SP) than a perfect one (70).
        food = carried_food(rec)
        sp = int(int(food.get('sp_restore', 0) or 0) * share)
        heal = int(int(food.get('hp_restore', 0) or 0) * share)
        mp = 0
    else:
        sp = int(out['sp'] * share)
        heal = int(heal_amount(player, out) * share)
        mp = int(mp_amount(player, out) * share)
    bits = []
    if sp > 0:
        player.restore_sp(sp)
        bits.append(f"+{sp} SP")
    if heal > 0:
        got = int(player.restore_hp(heal) or 0)
        if got > 0:
            bits.append(f"+{got} HP")
    if mp > 0:
        player.restore_mp(mp)
        bits.append(f"+{mp} MP")
    if bits:
        msgs.append("You salvage what you can: " + ", ".join(bits) + ".")
    return msgs


def bonus_category(rec: dict) -> str:
    """A cooked dish's broad kind, for Circe's Cauldron (five different kinds
    unlock it): 'permanent' for a feast or trophy, else its tab."""
    if is_legendary(rec) or trophy_powers(rec):
        return 'permanent'
    if makes(rec):
        return 'carry'
    return dish_tab(rec)


# ----------------------------------------------------------------------
# Old saves
# ----------------------------------------------------------------------

_REFRESH = ('name', 'description', 'family', 'tier_role', 'edible_safe', 'raw_sp')


def migrate_ingredient(item) -> bool:
    """Bring one pickled Ingredient up to today's kitchen: a retired id
    becomes the kept one (Goblin Shaman's old cut is Goblin Gristle now),
    and its name and fields come from today's data. Returns True if the id
    changed."""
    old = getattr(item, 'id', '')
    new = resolve(old)
    defn = ingredients().get(new)
    if defn is None:
        return False
    item.id = new
    for f in _REFRESH:
        if f in defn:
            setattr(item, f, defn[f])
    if 'name' in defn:
        item.unidentified_name = defn['name']
    item.lore = defn.get('description', getattr(item, 'lore', ''))
    return new != old


def merge_stacks(items: list) -> int:
    """Join stacks of the same ingredient in one list (two old ids that are
    one ingredient now). Returns how many stacks were folded in."""
    from items import Ingredient
    seen = {}
    folded = 0
    for i in range(len(items)):
        it = items[i]
        if not isinstance(it, Ingredient):
            continue
        first = seen.get(it.id)
        if first is None:
            seen[it.id] = it
            continue
        first.count = int(getattr(first, 'count', 1) or 1) + int(getattr(it, 'count', 1) or 1)
        items[i] = None
        folded += 1
    if folded:
        items[:] = [it for it in items if it is not None]
    return folded
