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
ingredient. What it gives comes from the rules file by tier, by tab, by its
worth (what its ingredients add, times the size bonus) and, for a legendary
feast, the legendary multiplier and a permanent bonus.
"""
import json
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
    """The ingredient a corpse of ``monster_id`` yields, or None."""
    return (harvest_map().get('monsters', {}) or {}).get(monster_id)


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
    return rec.get('benefit') if dish_tab(rec) == 'special' else None


def band_of(floor: int) -> int:
    step = int(rules().get('band_floors', 20) or 20)
    return max(1, min(5, (int(floor) - 1) // step + 1))


def dish_tier(rec: dict) -> int:
    """The band of the dish's deepest ingredient (1-5); the cook's question tier."""
    ps = parts(rec)
    return band_of(max(part_floor(p) for p in ps)) if ps else 1


def dish_size(rec: dict) -> int:
    return len(parts(rec))


def dish_worth(rec: dict) -> float:
    """What the ingredients add: a monster part 1, a foraged find 0.6, a ration 0.5."""
    w = rules().get('worth', {})
    return sum(float(w.get(part_kind(p) or 'food', 0.5)) for p in parts(rec))


def size_mult(n: int) -> float:
    table = rules().get('size_mult', {})
    n = max(1, min(5, int(n)))
    return float(table.get(str(n), 1.0))


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
    main = side * (float(r['legendary']['mult']) if grand else 1.0)
    every = r['every_dish']
    out = {
        'tab': tab, 'tier': t, 'worth': dish_worth(rec), 'factor': main,
        'sp': int(round(_tierv(every['sp'], t) * side)),
        'heal_written': int(_tierv(every['heal_written'], t)),
        'heal_share': 0.0,
        'max_hp': int(every.get('max_hp', 2)),
        'mp_share': 0.0, 'mp_least': 0, 'sustained': 0,
        'stat': None, 'lessons': 0, 'power': None, 'turns': 0, 'ward': 0,
        'permanent': None, 'trophy_powers': trophy_powers(rec),
    }
    if tab == 'hp':
        out['heal_share'] = min(1.0, _tierv(r['hp']['heal_share'], t) * main)
        out['max_hp'] += int(round(_tierv(r['hp']['max_hp_bonus'], t) * main))
    elif tab == 'sp':
        out['sp'] = int(round(_tierv(r['sp']['sp'], t) * main))
        out['sustained'] = min(int(r['sp'].get('sustained_cap', 800)),
                               int(round(_tierv(r['sp']['sustained_turns'], t) * main)))
    elif tab == 'mp':
        out['mp_share'] = min(1.0, _tierv(r['mp']['share'], t) * main)
        out['mp_least'] = int(round(_tierv(r['mp']['least'], t) * main))
    elif tab == 'stat':
        out['stat'] = dish_stat(rec)
        full = float(r['stat'].get('full_point_worth', 2.5))
        out['lessons'] = 2 if (grand or dish_worth(rec) >= full) else 1
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
    return out


# Resistances a boss trophy's own power already makes lasting: a feast that
# holds the trophy gives a different one rather than the same twice.
TROPHY_RESISTS = {'fire_immunity': 'fire_resist', 'cold_immunity': 'cold_resist',
                  'max_mp_per_floor_descent_and_poison_immunity': 'poison_resist'}
# The fallback order when a feast's own resistances are all taken.
_RESIST_FALLBACK = ('magic_resist', 'drain_resist', 'sleep_resist', 'shock_resist',
                    'acid_resist', 'cold_resist', 'fire_resist', 'poison_resist')


def _feast_resist(rec: dict) -> str:
    """The resistance a special feast makes lasting: its own power if that is
    a resistance, else the first resistance among its ingredients; never one
    its trophy already gives for good."""
    taken = {TROPHY_RESISTS[p] for p in trophy_powers(rec) if p in TROPHY_RESISTS}
    cands = [dish_power(rec)] + [(ingredients().get(part) or {}).get('temp_power')
                                 for part in parts(rec)]
    for c in cands:
        if c in RESISTS and c not in taken:
            return c
    return next(r for r in _RESIST_FALLBACK if r not in taken)


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
    share = max(meal_mend_share(written), out['heal_share'])
    return mend(written, int(getattr(player, 'max_hp', 1) or 1), share)


def mp_amount(player, out: dict) -> int:
    if out['tab'] != 'mp':
        return 0
    return max(int(round(out['mp_share'] * int(getattr(player, 'max_mp', 0) or 0))),
               int(out['mp_least']))


def max_hp_room(player) -> int:
    """Max HP cooking can still add on this floor (the per-floor cap)."""
    cap = int(getattr(player, 'PER_FLOOR_HP_CAP', 5))
    return max(0, cap - int(getattr(player, '_cook_hp_gain_this_floor', 0) or 0))


def feast_mp_cap(player) -> int:
    """Lifetime cap on max MP from feasts, by the deepest floor reached."""
    leg = rules().get('legendary', {})
    floor = max(1, min(100, int(getattr(player, 'deepest_floor_reached', 1) or 1)))
    return max(int(leg.get('max_mp_cap_min', 4)),
               int(floor * float(leg.get('max_mp_cap_per_floor', 0.25))))


def feast_mp_room(player) -> int:
    return max(0, feast_mp_cap(player) - int(getattr(player, 'cooking_mp_gained', 0) or 0))


def dish_effects(player, rec: dict) -> list:
    """Short, plain lines of what this dish does for THIS hero now, main
    benefit first: "+45 HP", "+2 Max HP", "+12 MP", "Teaches DEX (a full
    point)", "Dark Vision, 300 turns". A cap that would eat the benefit says
    so ("Max HP full this floor", "DEX lesson used this floor")."""
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
        lines.append(f"Sustained, {quantity(out['sustained'], 'turn')}")
    elif tab == 'mp':
        lines.append(f"+{mp_amount(player, out)} MP")
    elif tab == 'stat':
        lines.append(_stat_line(player, out))
    else:
        label = power_label(out['power'])
        bonus = f" (+{out['ward']})" if out['ward'] else ''
        lines.append(f"{label}{bonus}, {quantity(out['turns'], 'turn')}")
    room = max_hp_room(player)
    perm = out['permanent']
    if tab == 'hp' or room > 0:
        gain = min(out['max_hp'], room)
        if gain > 0:
            lines.append(f"+{gain} Max HP")
        elif tab == 'hp':
            lines.append("Max HP full this floor")
    if perm:
        kind, val = perm
        if kind == 'max_hp':
            lines.append(f"+{val} Max HP for good")
        elif kind == 'max_mp':
            room_mp = min(val, feast_mp_room(player))
            lines.append(f"+{room_mp} Max MP for good" if room_mp > 0
                         else "Max MP: all feasts can give at this depth")
        elif kind == 'stat':
            lines.append(f"+{val} {out['stat']} for good")
        elif kind == 'resist':
            lines.append(f"{power_label(val)} for good")
    for pw in out['trophy_powers']:
        lines.append(TROPHY_POWER_LINES.get(pw, 'A lasting power'))
    if tab != 'sp':
        lines.append(f"+{sp_shown} SP")
    return lines


def _stat_line(player, out: dict) -> str:
    stat = out['stat']
    block = player.cut_stat_block(stat) if hasattr(player, 'cut_stat_block') else None
    if block == 'cap':
        return f"{stat} has learned all food can teach here"
    if block == 'floor':
        return f"{stat} lesson used this floor"
    if out['lessons'] >= 2:
        return f"Teaches {stat} (a full point)"
    banked = int((getattr(player, 'cook_stat_meals', None) or {}).get(stat, 0) or 0)
    per = int(getattr(player, 'COOK_MEALS_PER_STAT_POINT', 2))
    if banked + 1 >= per:
        return f"Teaches {stat} (completes a point)"
    return f"Teaches {stat} (half a point)"


def dish_value(player, rec: dict) -> float:
    """How much a dish gives, for sorting rows of one tab: deeper and richer
    dishes first."""
    out = dish_outcome(rec)
    v = out['factor'] * (1.0 + 0.3 * (out['tier'] - 1))
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
    }


def menu_rows(player, inventory, tab: str) -> list:
    """The cook menu's rows for one tab, in three groups (``row['group']``):

    1. ``ready``: dishes the pack can cook now, the most giving first;
    2. ``building``: dishes the hero holds at least one HARVESTED part of
       (a monster part or a trophy; a ration or a foraged find alone does
       not count, or bread would put a hundred dishes here) but not all,
       the closest first ("2 of 4", with what is missing named);
    3. ``legendary``: legendary feasts and boss-trophy dishes, ready ones
       first, then the closest; shown once the hero holds any harvested
       part of them. Kept apart, and marked, so the big payoff stands out.

    Secrets stay secret: a dish needing a part of a hidden creature (the cow
    level) never shows until the hero holds that part.
    """
    counts = held_counts(inventory)
    rows = []
    for rec in book():
        if dish_tab(rec) != tab:
            continue
        ps = parts(rec)
        if any(is_secret_part(p) and counts.get(p, 0) <= 0 for p in ps):
            continue
        if not can_cook(rec, counts) and not any(
                is_harvested(p) and counts.get(p, 0) > 0 for p in ps):
            continue
        rows.append(_row(player, rec, counts))
    order = {g: i for i, g in enumerate(GROUPS)}

    def key(row):
        closeness = row['have_count'] / max(1, row['need_count'])
        if row['group'] == 'ready':
            return (order['ready'], 0, -row['value'], row['name'])
        if row['group'] == 'building':
            return (order['building'], 0, -closeness, len(row['missing']), -row['value'], row['name'])
        return (order['legendary'], 0 if row['ready'] else 1, -closeness, -row['value'], row['name'])
    rows.sort(key=key)
    return rows


def _would_teach(player, rec: dict) -> bool:
    stat = dish_stat(rec)
    if not stat:
        return False
    block = player.cut_stat_block(stat) if hasattr(player, 'cut_stat_block') else None
    return block is None


def opening_tab(player, inventory) -> str:
    """The tab for the hero's most urgent need, among tabs with a dish ready:
    hurt (under half HP): HP; hungry (SP under 30%): SP; low on mana (under
    40%) with spells known: MP; else Stat while the floor's lesson is open
    and a stat dish would teach; else the tab with the most dishes ready
    (with none ready, the tab with the most rows)."""
    counts = held_counts(inventory)
    ready = {t: [] for t in MENU_TABS}
    for rec in book():
        if can_cook(rec, counts):
            ready[dish_tab(rec)].append(rec)

    def frac(cur, mx):
        mx = int(mx or 0)
        return 1.0 if mx <= 0 else float(cur or 0) / mx
    if ready['hp'] and frac(getattr(player, 'hp', 0), getattr(player, 'max_hp', 0)) < 0.5:
        return 'hp'
    if ready['sp'] and frac(getattr(player, 'sp', 0), getattr(player, 'max_sp', 0)) < 0.3:
        return 'sp'
    if (ready['mp'] and getattr(player, 'known_spells', None)
            and frac(getattr(player, 'mp', 0), getattr(player, 'max_mp', 0)) < 0.4):
        return 'mp'
    if any(_would_teach(player, r) for r in ready['stat']):
        return 'stat'
    best = max(MENU_TABS, key=lambda t: (len(ready[t]), -MENU_TABS.index(t)))
    if ready[best]:
        return best
    sizes = {t: len(menu_rows(player, inventory, t)) for t in MENU_TABS}
    best = max(MENU_TABS, key=lambda t: (sizes[t], -MENU_TABS.index(t)))
    return best if sizes[best] else 'hp'


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
    out = dish_outcome(rec)
    name = rec.get('name', 'the dish')
    msgs = [f"You prepare {name}."]
    tab = out['tab']
    # Food is food: SP and a heal from every dish.
    sp_before = int(getattr(player, 'sp', 0) or 0)
    if out['sp'] > 0:
        player.restore_sp(out['sp'])
    sp = max(0, int(getattr(player, 'sp', 0) or 0) - sp_before) if hasattr(player, 'sp') else out['sp']
    heal = heal_amount(player, out)
    if heal > 0:
        player.restore_hp(heal)
    bits = [f"+{sp} SP"] if sp > 0 else []
    if heal > 0:
        bits.append(f"+{heal} HP")
    mp = mp_amount(player, out)
    if mp > 0:
        before = int(getattr(player, 'mp', 0) or 0)
        player.restore_mp(mp)
        bits.append(f"+{int(getattr(player, 'mp', 0) or 0) - before} MP")
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
    elif tab == 'hp':
        msgs.append("You feel sated, but your body is already full of nourishment this floor.")
    # The main benefit.
    if tab == 'sp' and out['sustained'] > 0:
        _add_effect(player, 'sustained', out['sustained'], int(rules()['sp'].get('sustained_cap', 800)))
        msgs.append(f"You are Sustained for {quantity(out['sustained'], 'turn')}: "
                    f"hunger comes at half its pace.")
    elif tab == 'stat':
        msgs.extend(_teach(player, out['stat'], out['lessons']))
    elif tab == 'special':
        power = out['power']
        cap = int((rules()['special']['powers'].get(power) or {}).get('max_turns', 60))
        _add_effect(player, power, out['turns'], cap)
        if power.startswith('save_guard_'):
            cat = power[len('save_guard_'):]
            if getattr(player, '_save_guard', None) is None:
                player._save_guard = {}
            player._save_guard[cat] = max(int(player._save_guard.get(cat, 0) or 0), out['ward'])
        msgs.append(f"{power_label(power)} lingers for {quantity(out['turns'], 'turn')}.")
    # A legendary feast's permanent bonus.
    if out['permanent']:
        msgs.extend(_apply_permanent(player, rec, out))
    # A boss trophy's own power.
    for pw in out['trophy_powers']:
        fake = dict(rec, permanent_power=pw, permanent_desc='')
        line = _apply_permanent_power(player, pw, fake)
        if line:
            msgs.append(line.strip())
    return msgs


def _teach(player, stat: str, lessons: int) -> list:
    label = STAT_NAMES.get(stat, stat)
    if not hasattr(player, 'feed_cut_stat'):
        return []
    block = player.cut_stat_block(stat) if hasattr(player, 'cut_stat_block') else None
    gained, banked = player.feed_cut_stat(stat, lessons=lessons)
    if gained > 0:
        return [f"Your {label} increases by {gained}!"]
    if banked > 0:
        return [f"You feel it doing you good. ({label}: {banked} of "
                f"{player.COOK_MEALS_PER_STAT_POINT} meals toward +1)"]
    if block == 'cap':
        return [f"Your {label} has learned all food can teach it at this depth. Go deeper to learn more."]
    if block == 'floor':
        return ["You have already learned from a meal on this floor. The next lesson waits on a new floor."]
    return []


def _apply_permanent(player, rec: dict, out: dict) -> list:
    kind, val = out['permanent']
    if kind == 'max_hp':
        got = player.try_apply_cook_hp_gain(int(val), bypass=True) \
            if hasattr(player, 'try_apply_cook_hp_gain') else 0
        return [f"A feast to remember: +{got} max HP for good."] if got > 0 else \
            ["A feast to remember, but your body has taken all cooking can give at this depth."]
    if kind == 'max_mp':
        got = min(int(val), feast_mp_room(player))
        if got <= 0:
            return ["A feast to remember, but your mana has taken all feasts can give at this depth."]
        player.max_mp = int(getattr(player, 'max_mp', 0) or 0) + got
        player.mp = int(getattr(player, 'mp', 0) or 0) + got
        player.cooking_mp_gained = int(getattr(player, 'cooking_mp_gained', 0) or 0) + got
        return [f"A feast to remember: +{got} max MP for good."]
    if kind == 'stat':
        stat = out['stat']
        got = player.try_apply_cook_stat_gain(stat, int(val), bypass=True) \
            if hasattr(player, 'try_apply_cook_stat_gain') else 0
        label = STAT_NAMES.get(stat, stat)
        return [f"A feast to remember: your {label} rises by {got}, for good."] if got > 0 else \
            [f"A feast to remember, but your {label} has learned all food can teach it at this depth."]
    if kind == 'resist':
        if int((getattr(player, 'status_effects', None) or {}).get(val, 0) or 0) == -1:
            return [f"You already have {power_label(val)} for good."]
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
    sp = int(out['sp'] * share)
    heal = int(heal_amount(player, out) * share)
    mp = int(mp_amount(player, out) * share)
    bits = []
    if sp > 0:
        player.restore_sp(sp)
        bits.append(f"+{sp} SP")
    if heal > 0:
        player.restore_hp(heal)
        bits.append(f"+{heal} HP")
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
