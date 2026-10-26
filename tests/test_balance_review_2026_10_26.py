"""BALANCE_REVIEW_LOOT_AND_FOOD_2026_10_26: the loot and food changes Brandon
approved (L2-L7 at the G1-lite numbers, L7a, F1-F4).

Loot volume is measured by tools/balance/loot_census.py; these tests pin the
rules themselves so a later edit cannot quietly undo them.
"""
import os
import pickle
import random
import statistics
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import container_system  # noqa: E402
import dungeon  # noqa: E402
import food_system  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402


def _ring(stat, amount, slot='ring', ident='test_ring'):
    return items.Accessory({'id': ident, 'name': ident, 'slot': slot, 'symbol': '=',
                            'color': [1, 1, 1], 'weight': 0.1, 'item_class': 'accessory',
                            'effects': {'stat': stat, 'amount': amount}})


# ---------------------------------------------------------------- L7a: rings

def test_rings_of_one_stat_do_not_add_up():
    p = Player()
    s0 = p.STR
    a, b = _ring('STR', 2, ident='a'), _ring('STR', 2, ident='b')
    p._apply_equip(a)
    p._apply_equip(b)
    assert p.STR == s0 + 2                       # two +2 rings: +2, not +4
    amulet = _ring('STR', 3, slot='amulet', ident='m')
    p._apply_equip(amulet)
    assert p.STR == s0 + 3                       # the strongest counts
    p.amulet_slot = None
    p.accessory_off(amulet)
    assert p.STR == s0 + 2                       # a weaker one takes over
    p.accessory_slots[0] = None
    p.accessory_off(a)
    assert p.STR == s0 + 2
    p.accessory_slots[1] = None
    p.accessory_off(b)
    assert p.STR == s0 and p._worn_stat_ledger == {}


def test_different_stats_and_penalties_still_count():
    p = Player()
    s0, c0, hp0 = p.STR, p.CON, p.max_hp
    p._apply_equip(_ring('STR', 2, ident='s'))
    p._apply_equip(_ring('CON', 2, ident='c'))
    p._apply_equip(_ring('STR', -1, ident='bad1'))
    p._apply_equip(_ring('STR', -1, ident='bad2'))
    assert p.STR == s0 + 2 - 2                   # every penalty counts
    assert p.CON == c0 + 2 and p.max_hp == hp0 + 2 * p.HP_PER_CON


def test_protection_rings_still_add_up():
    p = Player()
    ac0 = p.get_ac()
    r1, r2 = _ring('AC', 1, ident='p1'), _ring('AC', 2, ident='p2')
    p._apply_equip(r1)
    p._apply_equip(r2)
    assert p.get_ac() == ac0 - 3
    p.accessory_slots[0] = None
    p.accessory_off(r1)
    assert p.get_ac() == ac0 - 2


def test_enchanting_a_worn_ring_moves_the_stat_by_the_rule():
    p = Player()
    s0 = p.STR
    a, b = _ring('STR', 2, ident='a'), _ring('STR', 1, ident='b')
    p._apply_equip(a)
    p._apply_equip(b)
    b.effects['amount'] = 4                      # what game_magic's enchant does
    p.sync_worn_stats()
    assert p.STR == s0 + 4
    b.effects['amount'] = 0
    p.sync_worn_stats()
    assert p.STR == s0 + 2


def test_an_old_save_with_stacked_rings_comes_to_the_rule():
    p = Player()
    s0 = p.STR
    a, b = _ring('STR', 2, ident='a'), _ring('STR', 2, ident='b')
    p.accessory_slots[0], p.accessory_slots[1] = a, b
    p.STR = s0 + 4                               # the old rule added both
    state = p.__getstate__()
    state.pop('_worn_stat_ledger', None)
    q = Player.__new__(Player)
    q.__setstate__(pickle.loads(pickle.dumps(state)))
    assert q.STR == s0 + 2
    q.accessory_slots[0] = None
    q.accessory_off(q.accessory_slots[1] if False else a)
    q.accessory_slots[1] = None
    q.accessory_off(b)
    assert q.STR == s0


# ------------------------------------------------------- L2, L3: chests

def _box(template_id, tier):
    return types.SimpleNamespace(template_id=template_id, tier=tier, _gold_bonus_accum=0)


def test_a_plain_chest_holds_one_piece_of_gear_in_all():
    random.seed(11)
    for tid in ('wooden_chest', 'iron_lockbox', 'merchant_strongbox'):
        tier = items.get_chest_template(tid)['tier']
        for _ in range(60):
            loot = container_system._generate_loot_from_template(_box(tid, tier), 25)
            gear = [i for i in loot if getattr(i, 'item_class', '') in ('weapon', 'armor', 'shield')
                    and not getattr(i, 'is_unique', False)]     # a named unique is the lucky find
            assert len(gear) <= container_system.MAX_GEAR_PLAIN_CHEST, (tid, [g.name for g in gear])


def test_a_war_chest_is_still_an_armory():
    random.seed(12)
    most = 0
    for _ in range(60):
        loot = container_system._generate_loot_from_template(_box('warlord_warchest', 3), 30)
        most = max(most, sum(1 for i in loot if getattr(i, 'item_class', '') in ('weapon', 'armor', 'shield')))
    assert most >= 2


def test_the_jewelry_box_is_coin_and_keepsakes_not_three_rings():
    import economy
    import treasure
    random.seed(13)
    rings, worth = [], []
    for _ in range(300):
        loot = container_system._generate_loot_from_template(_box('jewelry_box', 2), 60)
        rings.append(sum(1 for i in loot if getattr(i, 'item_class', '') == 'accessory'))
        worth.append(sum(treasure.total_value(i) for i in loot if treasure.is_treasure(i)))
    assert statistics.mean(rings) < 1.0          # it was 2.3 a box at floor 5
    assert sum(1 for r in rings if r >= 3) / len(rings) < 0.05   # it was 43%
    # ...and its gems are not a second income: well under a floor's pay
    # (a table of treasure 60 put 1.5 floors' income in every deep box).
    assert statistics.mean(worth) < 0.6 * economy.floor_income(60)


# ------------------------------------------------- L4, L5, L6: the floor

def test_a_hidden_chamber_is_a_cache_not_an_armory():
    import treasure
    random.seed(14)
    for floor in (3, 25, 60):
        d = dungeon.generate_dungeon(80, 50, floor)
        room = max(d.rooms, key=lambda r: r.width * r.height)
        for _ in range(10):
            got = dungeon.spawn_chamber_cache(room, floor, d, random.Random())
            for it in got:
                assert isinstance(it, (items.Potion, items.Scroll, items.GoldPile)) or treasure.is_treasure(it), it
                assert room.x <= it.x < room.x + room.width and room.y <= it.y < room.y + room.height


def test_room_gear_and_ring_share_are_the_reviewed_numbers():
    assert dungeon.ROOM_GEAR_CHANCE == 0.25
    random.seed(15)
    pool = []
    for cls in ('accessory', 'wand', 'scroll', 'spellbook'):
        pool += items.load_items(cls)
    eligible = dungeon._item_eligible_weighted(pool, 30, random.Random(1))
    by = {}
    for it in eligible:
        by[type(it).__name__] = by.get(type(it).__name__, 0) + 1
    assert by['Accessory'] < by['Wand']           # 13 slots against 20
    # A one-class pool (a trader's ring shelf) keeps its full spread.
    rings_only = dungeon._item_eligible_weighted(items.load_items('accessory'), 30, random.Random(1))
    assert len(rings_only) >= 20


def test_monster_drops_pick_their_class_by_the_written_share():
    pool = []
    for cls in ('accessory', 'wand', 'scroll', 'potion', 'ammo'):
        pool += [i for i in items.load_items(cls) if not getattr(i, 'is_unique', False)
                 and items.is_random_loot(i) and i.min_level <= 10]
    rng = random.Random(16)
    n = 4000
    acc = sum(1 for _ in range(n) if getattr(container_system.pick_by_class_share(
        pool, container_system.DROP_MAGIC_SHARE, 10, rng), 'item_class', '') == 'accessory')
    total = sum(container_system.DROP_MAGIC_SHARE.values())
    assert abs(acc / n - container_system.DROP_MAGIC_SHARE['accessory'] / total) < 0.03


# ----------------------------------------------------------------- food

def test_all_stats_food_raises_every_stat_and_needs_no_lesson():
    p = Player()
    p.deepest_floor_reached = 45
    p.reset_floor_cook_caps()
    p._cook_stat_gain_this_floor = p.PER_FLOOR_STAT_CAP     # a meal already taught today
    before = {s: getattr(p, s) for s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')}
    msgs = food_system._apply_bonus(p, {'bonus_type': 'all_stats', 'bonus_amount': 1})
    assert all(getattr(p, s) == v + 1 for s, v in before.items()), msgs
    assert 'Strength +1' in msgs[0]


def test_a_stat_food_at_its_cap_says_why():
    p = Player()
    p.deepest_floor_reached = 20
    p.cooking_stat_gained['WIS'] = p.cooking_stat_softcap('WIS')
    w0 = p.WIS
    msgs = food_system._apply_bonus(p, {'bonus_type': 'stat', 'bonus_stat': 'WIS', 'bonus_amount': 1})
    assert p.WIS == w0 and 'at this depth' in msgs[0]


def test_a_recipes_max_hp_bonus_comes_on_top_of_the_base():
    p = Player()
    p.deepest_floor_reached = 30
    p.reset_floor_cook_caps()
    m0 = p.max_hp
    food_system._apply_outcome_body(p, {'name': 'Broth'}, {'sp': 10, 'max_hp_bonus': 1})
    assert p.max_hp == m0 + p.COOK_BASE_MAX_HP + 1   # 3, never less than a plain meal's 2


def test_a_meal_that_teaches_nothing_says_why():
    p = Player()
    p.deepest_floor_reached = 12
    p.reset_floor_cook_caps()
    oid = next(k for k, v in food_system._load_outcomes().items()
               if isinstance(v, dict) and not v.get('stat_grant') and not v.get('permanent_power'))
    recipe = {'name': 'Roast', '_cut_stat': 'STR', 'outcome_id': oid}
    food_system._apply_recipe_outcome(p, recipe)
    msgs = food_system._apply_recipe_outcome(p, recipe)
    assert any('already learned from a meal on this floor' in m for m in msgs)
    p.reset_floor_cook_caps()
    p.cooking_stat_gained['STR'] = p.cooking_stat_softcap('STR')
    msgs = food_system._apply_recipe_outcome(p, recipe)
    assert any('learned all food can teach' in m for m in msgs)


def test_the_sidebar_says_whether_the_floors_lesson_is_open():
    from hud_context import cooking_lesson_line
    p = Player()
    p.deepest_floor_reached = 5
    p.reset_floor_cook_caps()
    assert cooking_lesson_line(p) == ("Lesson: open", 'open')
    p.feed_cut_stat('DEX')
    text, state = cooking_lesson_line(p)
    assert (text, state) == ("Lesson: used  DEX 1/2", 'full')
    # A narrow sidebar drops the banked meals rather than cut the line.
    assert cooking_lesson_line(p, fits=lambda t: len(t) <= 14) == ("Lesson: used", 'full')


@pytest.mark.parametrize('floor,cap', [(1, 3), (8, 5), (20, 8), (100, 28)])
def test_food_cap_for_one_stat(floor, cap):
    p = Player()
    p.deepest_floor_reached = floor
    assert p.cooking_stat_softcap('STR') == cap


def test_what_a_ring_adds_is_measured_against_the_others_worn():
    p = Player()
    worn = _ring('STR', 2, ident='w')
    p._apply_equip(worn)
    assert p.worn_stat_gain(_ring('STR', 3, ident='c3'), 'STR', worn=False) == 1
    assert p.worn_stat_gain(_ring('STR', 2, ident='c2'), 'STR', worn=False) == 0
    assert p.worn_stat_gain(_ring('STR', -1, ident='bad'), 'STR', worn=False) == -1
    assert p.worn_stat_gain(worn, 'STR') == 2          # nothing else worn


def test_the_freed_gear_draw_does_not_go_to_rings():
    random.seed(17)
    rings = []
    for _ in range(400):
        loot = container_system._generate_loot_from_template(_box('iron_lockbox', 2), 25)
        rings.append(sum(1 for i in loot if getattr(i, 'item_class', '') == 'accessory'))
    assert statistics.mean(rings) < 0.85          # 0.79 before the cap; 1.01 when it went to rings
