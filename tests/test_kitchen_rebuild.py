"""The kitchen rebuild (2026-11-14, COOKING_REBUILD_PLAN_2026_11_14, slice K1).

Pins the new kitchen: vivid ingredients shared by close kin, a recipe book
where every ingredient is in at least three dishes (one single, two or more
of 2-5 ingredients), five kinds of meal (HP / SP / MP / Stat / Special) with
every number from data/cooking_rules.json, legendary feasts, the pure menu
functions K2 builds the cook screen on, and old saves migrating.

Data tests read the JSON; logic tests drive src/kitchen.py and the cook path
on a real Player; the journey drives a headless Game with real keys. What
these cannot prove (how the menu reads, whether saving a part for a deep dish
feels worth it) is a play-test question: Claude cannot drive Pygame.
"""
import copy
import json
import os
import pickle
import sys
import types
from collections import Counter

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import kitchen  # noqa: E402

DATA = os.path.join(ROOT, 'data')


def _json(*parts):
    with open(os.path.join(DATA, *parts), encoding='utf-8') as f:
        return json.load(f)


RECIPES = _json('items', 'recipes.json')
INGS = _json('items', 'ingredient.json')
FOOD = _json('items', 'food.json')
HMAP = _json('items', 'harvest_map.json')
MONSTERS = _json('monsters.json')
RULES = _json('cooking_rules.json')
ART = os.path.join(ROOT, 'assets', 'tiles', 'items')

BANNED = ('Prime Cut', 'Choice Cut', 'Pristine', 'Pure', 'Concentrated', 'Engorged', 'Glittering')
# A stew is a meal already: it goes into the two low rungs (plain fare, one
# part and one staple: Brandon, 2026-11-22) and no other dish.
FORBIDDEN_FOOD = ('hearty_stew',)
# Special food (food.json "special": the carrot, the tart, the mythic fruits)
# goes into a dish of its own (Brandon, 2026-11-16) and no other.
SPECIAL_FOOD = {k for k, v in FOOD.items() if v.get('special')}


def _parts(r):
    return list(dict.fromkeys(r['ingredients']))


def _book():
    return [{'id': k, **v} for k, v in RECIPES.items()]


# ---------------------------------------------------------------------------
# Data: ingredients and kin
# ---------------------------------------------------------------------------

def test_monster_ingredient_count_is_in_the_planned_range():
    monster_parts = [k for k, v in INGS.items() if v['tier_role'] in ('prime', 'trophy')]
    assert 250 <= len(monster_parts) <= 320, len(monster_parts)


def test_every_monster_maps_to_an_existing_ingredient():
    """Every creature that can leave a corpse yields an ingredient; a person
    (harvest_map.json "people": Brandon, 2026-11-16, we are not cannibals)
    yields none and is searched instead."""
    people = set(HMAP['people'])
    for mid in MONSTERS:
        iid = HMAP['monsters'].get(mid)
        if mid in people:
            assert iid is None, (mid, iid)
            assert kitchen.ingredient_for_monster(mid) is None
            continue
        assert iid in INGS, (mid, iid)
        assert kitchen.ingredient_for_monster(mid) == iid


def test_close_kin_share_and_named_kin_keep_their_own():
    m = HMAP['monsters']
    assert {m['goblin'], m['goblin_shaman'], m['goblin_sniper'], m['goblin_warpriest']} == {'goblin_prime'}
    assert INGS['goblin_prime']['name'] == 'Goblin Gristle'
    # The goblin king keeps a royal part; a boss keeps its trophy.
    assert m['goblin_king'] == 'goblin_king_prime'
    assert m['fafnir_dragon'] == 'fafnir_dragon_trophy'
    assert m['orc_scout'] == m['orc_warlord'] == 'orc_warrior_prime'


def test_retired_ids_resolve_to_kept_ingredients():
    for old, new in HMAP['aliases'].items():
        assert old not in INGS, old
        assert new in INGS, (old, new)
        assert kitchen.resolve(old) == new
    assert kitchen.resolve('goblin_shaman_prime') == 'goblin_prime'


def test_no_banned_words_in_any_name():
    for iid, v in INGS.items():
        for w in BANNED:
            assert w.lower() not in v['name'].lower(), (iid, v['name'])
    for rid, r in RECIPES.items():
        for w in BANNED:
            assert w.lower() not in r['name'].lower(), (rid, r['name'])


def test_every_ingredient_has_its_own_picture():
    """Item art is the item: each ingredient id has its own png (no glyph,
    no shared stand-in)."""
    for iid in INGS:
        assert os.path.exists(os.path.join(ART, iid + '.png')), iid


def test_names_keep_the_part_their_picture_shows():
    words = {
        'cut': ('Steak', 'Leg', 'Drumstick', 'Drumette', 'Ham', 'Haunch', 'Hock', 'Loin', 'Roll', 'Shank',
                'Rump', 'Sausage', 'Links', 'Bangers', 'Bacon', 'Gristle', 'Medallion', 'Joint', 'Sirloin'),
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
    for iid, v in INGS.items():
        ok = words.get(v['part'])
        if ok:
            assert any(w in v['name'] for w in ok), (iid, v['name'], v['part'])


def test_every_ingredient_has_a_nature_and_a_description():
    for iid, v in INGS.items():
        assert v['nature'] in kitchen.MENU_TABS, iid
        if v['nature'] == 'stat':
            assert v['stat_grant'] in kitchen.STATS, iid
        if v['nature'] == 'special':
            assert v['temp_power'] in RULES['special']['powers'], iid
        assert len(v['description']) > 20, iid


def test_casters_find_arcane_parts_early_and_deep():
    floors = [v['min_level'] for v in INGS.values() if v['nature'] == 'mp']
    assert min(floors) <= 5 and max(floors) >= 81


# ---------------------------------------------------------------------------
# Data: the recipe book
# ---------------------------------------------------------------------------

def test_every_ingredient_is_in_three_recipes_exactly_one_single():
    singles, multis = Counter(), Counter()
    for r in _book():
        ps = _parts(r)
        for p in ps:
            (singles if len(ps) == 1 else multis)[p] += 1
    for iid in INGS:
        assert singles[iid] == 1, (iid, singles[iid])
        assert multis[iid] >= 2, (iid, multis[iid])


def test_multi_dishes_have_two_to_five_distinct_ingredients():
    for r in _book():
        n = len(_parts(r))
        assert 1 <= n <= 5, r['id']


def test_every_recipe_ingredient_exists_and_is_never_secret_food():
    special_dishes = {}
    for r in _book():
        for p in r['ingredients']:
            assert p in INGS or p in FOOD, (r['id'], p)
            assert p not in FORBIDDEN_FOOD or r.get('rung'), (r['id'], p)
            if p in SPECIAL_FOOD:
                special_dishes.setdefault(p, []).append(r['id'])
    # Each special food is in exactly one dish, never the one that makes it.
    assert set(special_dishes) == SPECIAL_FOOD, SPECIAL_FOOD - set(special_dishes)
    for p, rids in special_dishes.items():
        assert len(rids) == 1, (p, rids)
        assert kitchen.makes(kitchen.recipe(rids[0])) != p, p
    used_food = {p for r in _book() for p in r['ingredients'] if p in FOOD}
    for staple in ('bread_ration', 'dried_meat', 'hard_cheese', 'apple', 'trail_rations'):
        assert staple in used_food, staple


def test_dish_names_are_unique_and_every_dish_has_flavour_and_art():
    names = Counter(r['name'].lower() for r in _book())
    assert not [n for n, c in names.items() if c > 1]
    for r in _book():
        assert r.get('flavor'), r['id']
        assert os.path.exists(os.path.join(ART, r['art'] + '.png')), (r['id'], r['art'])


def test_every_tab_has_ready_able_dishes_at_every_depth_band():
    seen = Counter()
    for r in _book():
        if kitchen.is_secret(r):
            continue
        seen[(kitchen.dish_tab(r), kitchen.dish_tier(r))] += 1
    for tab in kitchen.MENU_TABS:
        for band in range(1, 6):
            assert seen[(tab, band)] >= 1, (tab, band)


def test_legendary_feasts_count_size_and_depth():
    feasts = [r for r in _book() if r.get('legendary')]
    assert 25 <= len(feasts) <= 40, len(feasts)
    for r in feasts:
        assert len(_parts(r)) == 5, r['id']
        assert kitchen.dish_tier(r) >= 3, r['id']
        assert kitchen.dish_tab(r) != 'sp', r['id']
        assert kitchen.dish_outcome(r)['permanent'], r['id']
    with_trophy = [r for r in feasts if any(INGS.get(p, {}).get('tier_role') == 'trophy'
                                            for p in r['ingredients'])]
    assert len(with_trophy) >= len(feasts) // 2


def test_the_fourteen_trophy_dishes_keep_their_permanent_powers():
    trophies = [r for r in _book() if r.get('trophy')]
    assert len(trophies) == 14
    for r in trophies:
        assert len(r['ingredients']) == 1 and r['ingredients'][0].endswith('_trophy'), r['id']
        assert r['permanent'] in kitchen.TROPHY_POWER_LINES, r['id']


def test_cross_depth_dishes_really_span_and_are_about_a_third():
    multis = [r for r in _book() if len(_parts(r)) > 1 and not r.get('rung')]
    cross = [r for r in multis if r.get('cross_depth')]
    for r in cross:
        floors = [kitchen.part_floor(p) for p in r['ingredients']]
        assert min(floors) <= 20 and max(floors) >= 40, r['id']
    assert 0.25 <= len(cross) / len(multis) <= 0.5, (len(cross), len(multis))
    # Goblin Gristle, saved from floor 3, goes into a deep dish.
    assert any('goblin_prime' in r['ingredients'] and kitchen.dish_tier(r) >= 3 for r in cross)


def test_rules_file_has_five_tiers_everywhere():
    for path in (('every_dish', 'sp'), ('every_dish', 'heal_written'), ('hp', 'heal_share'),
                 ('hp', 'max_hp_bonus'), ('sp', 'sp'), ('sp', 'sustained_turns'),
                 ('mp', 'share'), ('mp', 'least'), ('special', 'turns'),
                 ('legendary', 'max_hp'), ('legendary', 'max_mp')):
        assert len(RULES[path[0]][path[1]]) == 5, path
    assert RULES['size_mult']['2'] == pytest.approx(1.2)
    assert RULES['size_mult']['5'] == pytest.approx(1.6)


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------

def _player(**kw):
    from player import Player
    p = Player()
    p.deepest_floor_reached = kw.pop('deepest', 10)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _ing(iid, n=1):
    from food_system import load_ingredient_for
    it = load_ingredient_for(iid)
    it.count = n
    return it


def _food(fid):
    from items import load_items
    return copy.copy(next(f for f in load_items('food') if f.id == fid))


def test_mp_dish_restores_a_share_of_max_mp_or_its_least():
    p = _player()
    p.max_mp, p.mp = 20, 0
    single = kitchen.recipe('cook_wraith')
    out = kitchen.dish_outcome(single)
    assert out['tab'] == 'mp'
    assert kitchen.mp_amount(p, out) == max(round(0.25 * 20), 4)
    msgs = kitchen.apply_dish(p, single)
    assert p.mp == kitchen.mp_amount(p, out)
    assert any('MP' in m for m in msgs)
    # A bigger mana pool: the share grows with it.
    p.max_mp, p.mp = 80, 0
    assert kitchen.mp_amount(p, out) == 20


def test_a_multi_dish_is_worth_more_than_its_parts_eaten_alone():
    two = kitchen.recipe('dish_094')          # Goblin Gristle + Charybdis Spawn Shank
    one = kitchen.recipe('cook_goblin')
    assert kitchen.dish_outcome(two)['factor'] == pytest.approx(2 * 1.2)
    assert kitchen.dish_outcome(one)['factor'] == pytest.approx(1.0)
    assert kitchen.dish_outcome(two)['sp'] > 2 * kitchen.dish_outcome(one)['sp']


def test_food_and_forage_add_less_worth_than_a_monster_part():
    r = kitchen.recipe('dish_221')            # goblin + locust + bread + cheese
    assert kitchen.dish_worth(r) == pytest.approx(1 + 1 + 0.5 + 0.5)


def test_a_legendary_max_mp_has_a_floor_cap_and_no_cap_across_floors():
    """Brandon, 2026-11-17: max MP from feasts works like max HP, a cap on
    each floor and none across floors (the old lifetime cap by the deepest
    floor reached is gone)."""
    feast = kitchen.recipe('feast_16')        # Crone's Midnight Cauldron (mp)
    assert kitchen.dish_outcome(feast)['permanent'][0] == 'max_mp'
    p = _player(deepest=4)
    cap = kitchen.feast_mp_cap(p)
    assert cap == 4
    p._feast_mp_gain_this_floor = cap - 1
    before = p.max_mp
    kitchen.apply_dish(p, feast)
    assert p.max_mp - before == 1               # the floor's room, no more
    kitchen.apply_dish(p, feast)
    assert p.max_mp - before == 1               # full for this floor
    p.cooking_mp_gained = 500                   # a lifetime total no longer stops it
    p.reset_floor_cook_caps()                   # a new floor
    kitchen.apply_dish(p, feast)
    assert p.max_mp - before > 1


def test_a_legendary_max_hp_passes_the_floor_cap_and_has_no_cap_across_floors():
    """Brandon, 2026-11-16: a per-floor limit to max HP, not a max across
    several floors. The feast's lasting max HP lands in full, however much
    cooking has given before (the old lifetime cap held it to 3 here)."""
    feast = kitchen.recipe('feast_05')        # Sigurd's Hearth Roast (hp)
    p = _player(deepest=1)
    p._cook_hp_gain_this_floor = p.PER_FLOOR_HP_CAP
    p.cooking_hp_gained = 17                  # three short of the old cap of 20
    before = p.max_hp
    kitchen.apply_dish(p, feast)
    assert p.max_hp - before == kitchen.dish_outcome(feast)['permanent'][1]


def test_a_feast_never_gives_the_resistance_its_trophy_already_gives():
    feast = kitchen.recipe('feast_23')        # Muspelheim Forge Roast: Surtur's Ember
    kind, res = kitchen.dish_outcome(feast)['permanent']
    assert kind == 'resist' and res != 'fire_resist'
    p = _player(deepest=90)
    kitchen.apply_dish(p, feast)
    assert p.status_effects['fire_resist'] == -1 and p.status_effects[res] == -1


def test_a_legendary_stat_point_respects_its_tiers_cap():
    feast = kitchen.recipe('feast_29')        # First Seal Wrath Feast (STR)
    tier = kitchen.dish_tier(feast)
    p = _player(deepest=1)
    cap = p.cooking_stat_softcap('STR', tier)
    p.cooking_stat_gained['STR'] = cap
    before = p.STR
    kitchen.apply_dish(p, feast)
    assert p.STR == before                    # at the cap: neither lesson nor feast
    # One point of room: the lesson takes it, the feast's own point nothing.
    q = _player(deepest=1)
    q.cooking_stat_gained['STR'] = cap - 1
    s0 = q.STR
    kitchen.apply_dish(q, feast)
    assert q.STR == s0 + 1 and q.cooking_stat_gained['STR'] == cap


def test_a_rich_stat_dish_teaches_a_whole_point_once_a_floor():
    rich = next(r for r in kitchen.book() if kitchen.dish_tab(r) == 'stat'
                and not r.get('legendary') and kitchen.dish_worth(r) >= 2.5)
    stat = kitchen.dish_stat(rich)
    p = _player(deepest=20)
    before = getattr(p, stat)
    kitchen.apply_dish(p, rich)
    assert getattr(p, stat) == before + 1
    # The floor's lesson is used: a second one teaches nothing.
    kitchen.apply_dish(p, rich)
    assert getattr(p, stat) == before + 1
    assert kitchen._stat_line(p, kitchen.dish_outcome(rich)) == f"{stat} lesson used this floor"
    p.reset_floor_cook_caps()
    kitchen.apply_dish(p, rich)
    assert getattr(p, stat) == before + 2


def test_a_single_stat_dish_is_a_whole_point():
    """One dish = one point (Brandon, 2026-11-16), a single as much as a
    rich dish: what a dish's depth decides is how far it can teach."""
    single = kitchen.recipe('cook_cobra')
    p = _player(deepest=20)
    before = p.DEX
    kitchen.apply_dish(p, single)
    assert p.DEX == before + 1
    p.reset_floor_cook_caps()
    kitchen.apply_dish(p, single)
    assert p.DEX == before + 2


def test_a_shallow_stat_dish_stops_at_its_tiers_cap_and_says_why():
    """A tier-1 dish teaches a stat up to +8 and no further, however deep
    the hero is; a deeper dish of the same stat teaches on."""
    shallow = next(r for r in kitchen.book() if kitchen.dish_stat(r) == 'STR'
                   and kitchen.dish_tier(r) == 1 and not r.get('legendary') and not kitchen.trophy_powers(r))
    deeper = next(r for r in kitchen.book() if kitchen.dish_stat(r) == 'STR'
                  and kitchen.dish_tier(r) == 2 and not r.get('legendary') and not kitchen.trophy_powers(r))
    p = _player(deepest=45)
    p.cooking_stat_gained['STR'] = 8
    s0 = p.STR
    out = kitchen.dish_outcome(shallow)
    assert kitchen._stat_line(p, out) == 'STR has learned all a dish this simple can teach'
    assert kitchen.dish_effects(p, shallow)[1] == \
        'Tier 1 dishes teach STR up to +8 (now +8): deeper creatures teach more'
    msgs = kitchen.apply_dish(p, shallow)
    assert p.STR == s0
    assert 'Your Strength has learned all a dish this simple can teach. Deeper creatures teach more.' in msgs
    assert not kitchen._would_teach(p, shallow) and kitchen._would_teach(p, deeper)
    kitchen.apply_dish(p, deeper)
    assert p.STR == s0 + 1


def test_the_altar_counts_against_a_dishs_tier_cap():
    """The altar's rededication counts against the same cap as a dish:
    points an altar moved into a stat leave a shallow dish less room."""
    import rededication as R
    p = _player(deepest=45)                   # the altar goes by the deepest band (tier 3)
    p.stats_at_start = {s: getattr(p, s) for s in R.STATS}
    p.apply_stat_bonus('DEX', 2)
    p.cooking_stat_gained['DEX'] = 2
    p.cooking_stat_gained['STR'] = 7
    assert R.take_room(p, 'STR') == 18 - 7
    R.move(p, 'DEX', 'STR', 1)
    assert p.cut_stat_block('STR', 1) == 'tier'          # 7 cooked + 1 from the altar = 8
    assert R.take_room(p, 'STR') == 18 - 8


def test_a_special_dish_lasts_past_the_usual_sixty_turns():
    r = kitchen.recipe('cook_shade')          # Gloom-Jelly on Toast: Dark Vision
    p = _player()
    out = kitchen.dish_outcome(r)
    kitchen.apply_dish(p, r)
    assert out['turns'] > 60
    assert p.status_effects[out['power']] == out['turns']


def test_an_sp_dish_fills_and_sustains():
    r = kitchen.recipe('dish_221')
    p = _player()
    p.sp = 0
    kitchen.apply_dish(p, r)
    assert p.sp == p.max_sp
    assert p.status_effects['sustained'] == kitchen.dish_outcome(r)['sustained']


def test_every_dish_gives_some_sp():
    for r in kitchen.book():
        assert kitchen.dish_outcome(r)['sp'] > 0, r['id']


def test_dish_effects_say_when_a_cap_eats_the_benefit():
    p = _player()
    p._cook_hp_gain_this_floor = p.PER_FLOOR_HP_CAP
    lines = kitchen.dish_effects(p, kitchen.recipe('cook_troll'))
    assert lines[0].endswith(' HP') and 'Max HP full this floor' in lines


def test_persephone_salvage_returns_half_of_sp_hp_and_mp():
    from food_system import _apply_recipe_outcome
    r = kitchen.recipe('cook_wraith')
    p = _player()
    p.quirk_progress['persephone_active'] = True
    p.max_mp, p.mp, p.sp = 40, 0, 0
    p.hp = 1
    out = kitchen.dish_outcome(r)
    msgs = _apply_recipe_outcome(p, r, ruined=True)
    assert msgs[0].startswith("You ruin the preparation")
    assert p.mp == int(kitchen.mp_amount(p, out) * 0.5)
    assert p.sp == int(out['sp'] * 0.5)
    assert 'MP' in msgs[-1]


def test_menu_rows_groups_and_sorting():
    p = _player()
    inv = [_ing('goblin_prime'), _ing('cave_mushroom')]
    rows = kitchen.menu_rows(p, inv, 'sp')
    groups = [r['group'] for r in rows]
    assert groups == sorted(groups, key=kitchen.GROUPS.index)
    ready = [r for r in rows if r['group'] == 'ready']
    assert {r['id'] for r in ready} >= {'cook_goblin', 'cook_cave_mushroom'}
    assert [r['value'] for r in ready] == sorted((r['value'] for r in ready), reverse=True)
    building = [r for r in rows if r['group'] == 'building']
    hotpot = next(r for r in building if r['id'] == 'dish_094')
    assert hotpot['progress'] == '1 of 2'
    assert [m['name'] for m in hotpot['missing']] == ['Charybdis Spawn Shank']
    closeness = [r['have_count'] / r['need_count'] for r in building]
    assert closeness == sorted(closeness, reverse=True)
    # A ration alone builds toward nothing (or bread would list a hundred dishes).
    assert not [r for r in kitchen.menu_rows(p, [_food('bread_ration')], 'sp') if not r['ready']]


def test_legendary_feasts_are_their_own_group():
    p = _player()
    inv = [_ing('wraith_prime')]
    rows = kitchen.menu_rows(p, inv, 'mp')
    leg = [r for r in rows if r['group'] == 'legendary']
    assert any(r['id'] == 'feast_16' for r in leg)
    assert all(r['legendary'] or r['trophy'] for r in leg)


def test_secret_dishes_stay_hidden_until_the_part_is_held():
    p = _player()
    secret_dishes = [r['id'] for r in kitchen.book() if kitchen.is_secret(r)]
    assert secret_dishes
    # Holding a part that a secret dish also uses does not reveal it.
    inv = [_ing('lurker_above_prime'), _ing('orc_warrior_prime')]
    shown = {r['id'] for t in kitchen.MENU_TABS for r in kitchen.menu_rows(p, inv, t)}
    assert not shown & set(secret_dishes)
    inv.append(_ing('hell_bovine_prime'))
    shown = {r['id'] for t in kitchen.MENU_TABS for r in kitchen.menu_rows(p, inv, t)}
    assert 'dish_056' in shown


def test_opening_tab_follows_the_most_urgent_need():
    inv = [_ing('troll_prime'), _ing('goblin_prime'), _ing('wraith_prime'), _ing('cobra_prime')]
    p = _player()
    p.known_spells = {'magic_missile': 1}
    p.hp = p.max_hp // 3
    assert kitchen.opening_tab(p, inv) == 'hp'
    p.hp = p.max_hp
    p.sp = p.max_sp // 5
    assert kitchen.opening_tab(p, inv) == 'sp'
    p.sp = p.max_sp
    p.mp = 0
    assert kitchen.opening_tab(p, inv) == 'mp'
    p.mp = p.max_mp
    assert kitchen.opening_tab(p, inv) == 'stat'     # the floor's lesson is open
    p._cook_stat_gain_this_floor = 1
    assert kitchen.opening_tab(p, inv) in ('hp', 'sp', 'mp', 'stat', 'special')
    assert kitchen.opening_tab(p, inv) != 'stat'


def test_stacks_and_old_ids_count_toward_a_dish():
    inv = [_ing('goblin_prime', 2)]
    assert kitchen.held_counts(inv)['goblin_prime'] == 2
    from items import Ingredient
    old = Ingredient({'id': 'goblin_shaman_prime', 'name': 'goblin shaman choice cut',
                      'symbol': '~', 'color': [1, 1, 1], 'tier_role': 'prime'})
    assert kitchen.held_counts([old])['goblin_prime'] == 1


def test_cooking_consumes_the_food_a_dish_names():
    from food_system import cook_compound_recipe
    p = _player()
    p.inventory = []
    for it in (_ing('goblin_prime'), _ing('locust_swarmlord_prime'), _food('bread_ration'),
               _food('hard_cheese'), _food('apple')):
        p.add_to_inventory(it)
    quiz = types.SimpleNamespace(start_quiz=lambda **kw: kw['callback'](types.SimpleNamespace(success=True)))
    got = []
    cook_compound_recipe(p, kitchen.recipe('dish_221'), p.inventory, quiz, got.append)
    assert [i.id for i in p.inventory] == ['apple']
    assert got and got[0][0] == 'You prepare Gristle-and-Locust Harvest Pie.'


def test_harvest_yields_the_kin_ingredient_and_remembers_the_creature():
    from food_system import harvest_corpse, make_corpse
    p = _player()
    corpse = make_corpse('goblin_shaman', 0, 0)
    quiz = types.SimpleNamespace(start_quiz=lambda **kw: kw['callback'](types.SimpleNamespace(success=True)))
    out = []
    harvest_corpse(p, corpse, quiz, lambda ings, msg: out.append((ings, msg)))
    ings, msg = out[0]
    assert [i.id for i in ings] == ['goblin_prime']
    assert ings[0].name == 'Goblin Gristle' and ings[0].source_monster == 'goblin_shaman'
    assert 'Goblin Gristle' in msg


def test_an_old_save_ingredient_migrates_and_stacks_merge():
    """A pickled Ingredient from before the rebuild (a goblin shaman's cut)
    loads as today's Goblin Gristle, and joins the goblin's stack."""
    from items import Ingredient
    old = Ingredient({'id': 'goblin_shaman_prime', 'name': 'goblin shaman choice cut',
                      'symbol': '~', 'color': [80, 160, 30], 'tier_role': 'prime',
                      'source_monster': 'goblin_shaman', 'description': 'Prime cut from goblin shaman.'})
    old.count = 2
    old = pickle.loads(pickle.dumps(old))
    mine = _ing('goblin_prime')
    inv = [mine, old]
    import main
    fake = types.SimpleNamespace(player=types.SimpleNamespace(inventory=inv))
    main.Game._migrate_legacy_ingredients(fake, {'ground_items': [], 'level_mgr': None})
    assert len(inv) == 1 and inv[0] is mine and mine.count == 3
    assert mine.name == 'Goblin Gristle'
    # Alone, the old one is renamed in place.
    old2 = pickle.loads(pickle.dumps(Ingredient({'id': 'orc_warlord_prime', 'name': 'orc warlord choice cut',
                                                 'symbol': '~', 'color': [1, 1, 1]})))
    inv2 = [old2]
    fake2 = types.SimpleNamespace(player=types.SimpleNamespace(inventory=inv2))
    main.Game._migrate_legacy_ingredients(fake2, {'ground_items': [], 'level_mgr': None})
    assert inv2[0].id == 'orc_warrior_prime' and inv2[0].name == 'Orc Salted Haunch'


def test_traders_stock_only_foraged_ingredients():
    """A monster part comes from a corpse, a trophy from its boss and the
    secret cow parts from the cow level: never from a shelf."""
    import random
    import traders
    pool = traders._pool('ingredient', 50, random.Random(1))
    assert pool and {INGS[i.id]['tier_role'] for i in pool} == {'dungeon'}


def test_the_kit_line_says_what_a_part_is_good_for():
    assert kitchen.nature_line('wraith_prime') == 'Arcane: MP dishes | In 4 dishes' \
        or kitchen.nature_line('wraith_prime').startswith('Arcane: MP dishes | In ')
    assert kitchen.nature_line('goblin_shaman_prime').startswith('Filling: SP dishes')
    assert kitchen.nature_line('cobra_prime').startswith('Sharpens DEX: Stat dishes')
    from food_system import load_ingredient_for
    assert 'gristle' in load_ingredient_for('goblin_prime').lore.lower()


def test_circe_reads_the_dish_kind():
    import main
    assert main._outcome_bonus_category(kitchen.recipe('cook_wraith')) == 'mp'
    assert main._outcome_bonus_category(kitchen.recipe('feast_16')) == 'permanent'
    assert main._outcome_bonus_category(kitchen.recipe('trophy_fafnir_dragon_recipe')) == 'permanent'


# ---------------------------------------------------------------------------
# A real-keys journey: harvest a goblin, keep the gristle, go down, harvest
# something else, cook the dish that needs both.
# ---------------------------------------------------------------------------

def test_journey_save_the_gristle_for_a_dish_two_floors_down():
    import random
    import pygame
    pygame.init()
    import items
    from main import Game
    from game_states import STATE_PLAYER, STATE_COOK_MENU
    from food_system import make_corpse
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_kitchen_journey__')
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))

    def press(key, uni=''):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))

    def harvest(monster):
        px, py = g.player.x, g.player.y
        g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (px, py)]
        g.ground_items.append(make_corpse(monster, px, py))
        g.state = STATE_PLAYER
        press(pygame.K_h, 'h')

    harvest('goblin_sniper')
    assert any(i.id == 'goblin_prime' for i in g.player.inventory)
    g._change_level(3, enter_from_top=True, via='warp')
    g.monsters = []
    harvest('charybdis_spawn')
    assert any(i.id == 'charybdis_spawn_prime' for i in g.player.inventory)
    g.state = STATE_PLAYER
    g.player.sp = 10
    press(pygame.K_c, 'c')
    assert g.state == STATE_COOK_MENU
    # The hotpot is an SP dish: Right until the SP tab shows, then down to it.
    for _ in range(len(kitchen.MENU_TABS)):
        if g._cook_tab_slug() == 'sp':
            break
        press(pygame.K_RIGHT)
    assert g._cook_tab_slug() == 'sp'
    idx = next(i for i, r in enumerate(g._cook_tab_rows()) if r['id'] == 'dish_094')
    for _ in range(idx):
        press(pygame.K_DOWN)
    press(pygame.K_RETURN)
    texts = [str(e[0]) for e in g.msg_log.entries[-8:]]
    assert any('You prepare Goblin and Whirlpool Hotpot.' in t for t in texts), texts
    assert not any(kitchen.resolve(i.id) in ('goblin_prime', 'charybdis_spawn_prime')
                   for i in g.player.inventory)
    assert g.player.sp > 10
    assert g.player.has_effect('sustained')
