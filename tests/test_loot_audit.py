"""Loot audit, 2026-10-06: every path an item or gold reaches the player.

Each test pins one thing a measured audit found wrong. Logic tests: random
loot and deep floors cannot be play-tested in any useful way.
"""
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import economy  # noqa: E402
import items  # noqa: E402
import level_manager  # noqa: E402


def _lm():
    lm = level_manager.LevelManager()
    lm._maybe_spawn_bones = lambda *a, **k: None
    return lm


def _data(name):
    with open(os.path.join(ROOT, 'data', *name.split('/')), encoding='utf-8') as f:
        return json.load(f)


def _chest_templates():
    t = _data('chest_templates.json')
    t = t.get('templates', t)
    return {k: v for k, v in t.items() if isinstance(v, dict) and 'loot_table' in v}


# ------------------------------------------------------- once-per-run uniques

def test_a_named_unique_appears_once_in_a_run():
    """There was no rule: about 115 uniques a run, 47 of them duplicates."""
    import container_system as cs
    from items import Container
    random.seed(21)
    lm = _lm()
    seen = []
    for floor in range(1, 100, 3):
        _d, _m, floor_items = lm.generate(floor)
        for it in floor_items:
            if items._tracked_unique(it):
                seen.append(it.id)
            for s in getattr(it, 'stock', None) or []:
                if items._tracked_unique(s):
                    seen.append(s.id)
            if isinstance(it, Container):
                for got in cs._generate_loot_from_template(it, floor):
                    if items._tracked_unique(got):
                        seen.append(got.id)
    assert len(seen) == len(set(seen)), sorted(i for i in set(seen) if seen.count(i) > 1)
    assert set(seen) <= lm.seen_unique_ids


def test_the_unique_record_is_saved_with_the_run():
    import pickle
    lm = _lm()
    lm._maybe_spawn_bones = None           # a plain attribute, so the manager pickles
    lm.seen_unique_ids.add('excalibur')
    clone = pickle.loads(pickle.dumps(lm))
    assert clone.seen_unique_ids == {'excalibur'}
    assert items._UNIQUES_SEEN is clone.seen_unique_ids          # re-bound on load
    state = dict(clone.__dict__)
    del state['seen_unique_ids']                                 # a save from before
    old = level_manager.LevelManager.__new__(level_manager.LevelManager)
    old.__setstate__(state)
    assert old.seen_unique_ids == set()


def test_scripted_items_are_never_tracked_or_blocked():
    gram = types.SimpleNamespace(id='gram', is_unique=True)
    assert not items.is_random_loot(gram)
    items.claim_unique(gram)
    assert 'gram' not in items._UNIQUES_SEEN and items.unique_available(gram)


# ------------------------------------------------- scripted items out of loot

def test_scripted_rewards_do_not_come_out_of_chests_or_drops():
    """Ring of Command and Elara's ring were a quarter of floor-1 chest
    accessories and four fifths of floor-99 ones."""
    import container_system as cs
    scripted = items.scripted_only_ids()
    assert {'ring_of_command', 'elaras_silver_ring', 'ruby_rod', 'silverlight_pendant',
            'scroll_of_nine_hells', 'scroll_of_chromatic_doom'} <= scripted
    for tid, t in _chest_templates().items():
        for floor in (1, 40, 99):
            pool = cs._build_common_pool(t, floor) + cs._build_unique_pool(t, floor)
            bad = [it.id for it in pool if it.id in scripted]
            assert not bad, (tid, floor, bad[:4])
    src = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    i = src.index("for cls_name in ('accessory', 'wand', 'scroll', 'potion', 'ammo'):")
    assert 'is_random_loot(item)' in src[i:i + 500]


def test_chest_uniques_get_no_reach_and_follow_their_weight():
    import container_system as cs
    for tid, tpl in _chest_templates().items():
        for floor in (1, 2, 12):
            for it in cs._build_unique_pool(tpl, floor):
                assert it.min_level <= floor, (tid, floor, it.id)
    spear = next(i for i in items.load_items('weapon') if i.id == 'achilles_spear')
    assert spear.min_level >= 5


# --------------------------------------------------------------------- gear

def test_materials_stay_within_five_floors_of_their_tier_band():
    for cat in ('weapons', 'armor'):
        for mid, m in items.load_materials(cat).items():
            first = m.get('min_level')
            if first is None:
                first = m['peak_floor'] - m.get('spread', 10)
            assert m['tier'] == 1 or first >= (m['tier'] - 1) * 20 - 5, (cat, mid, first)
    random.seed(4)
    for floor, top in ((8, 1), (14, 1), (19, 2), (34, 2), (54, 3)):
        tiers = {items.pick_random_weapon_for_floor(floor, random).quiz_tier for _ in range(300)}
        assert max(tiers) <= top, (floor, tiers)


def test_armor_from_any_source_comes_in_every_slot():
    random.seed(8)
    slots = {items.pick_random_armor_for_floor(30, random).slot for _ in range(200)}
    assert len(slots) >= 4, slots
    assert {items.pick_random_armor_for_floor(30, random, slot='body').slot
            for _ in range(20)} == {'body'}


def test_loot_from_chests_and_drops_is_dressed_like_ground_loot():
    from dungeon import dress_spawn
    random.seed(3)
    wand = next(i for i in items.load_items('wand')
                if getattr(i, 'charges_max', 0) > getattr(i, 'charges_min', 0)
                and items.is_random_loot(i))
    charges, bucs = set(), set()
    for _ in range(300):
        w = items.copy_at(wand, 0, 0)
        dress_spawn(w, 60, random)
        charges.add(w.charges)
        bucs.add(w.buc)
    assert len(charges) > 1 and 'cursed' in bucs and 'uncursed' in bucs
    quest = types.SimpleNamespace(id='gram', buc='uncursed', item_class='weapon')
    for _ in range(100):
        dress_spawn(quest, 60, random)
    assert quest.buc == 'uncursed'                    # quest items are left as written
    for name in ('container_system.py', 'game_combat.py'):
        assert 'dress_spawn(' in open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()


def test_maze_floors_hold_a_floor_of_loot():
    from items import Container
    random.seed(12)
    counts = []
    chests = 0
    for _ in range(6):
        _d, _m, floor_items = _lm().generate(30)
        counts.append(len([i for i in floor_items if not isinstance(i, items.GoldPile)]))
        chests += sum(isinstance(i, Container) for i in floor_items)
    assert sorted(counts)[len(counts) // 2] >= 12, counts     # was about 6
    assert chests >= 6


def test_no_mimic_chests_before_the_mimic_exists():
    from dungeon import MIMIC_FIRST_FLOOR
    from items import Container
    random.seed(2)
    for floor in (1, 4, MIMIC_FIRST_FLOOR - 1):
        for _ in range(8):
            _d, _m, floor_items = _lm().generate(floor)
            assert not any(getattr(i, 'is_mimic', False)
                           for i in floor_items if isinstance(i, Container))


# --------------------------------------------------------------------- gold

def test_special_room_gold_is_a_share_of_the_floor():
    """A zoo held up to 30,927 gold on floor 81: four floors of income."""
    from dungeon import TREASURY_GOLD_SHARE, VAULT_GOLD_SHARE, ZOO_GOLD_SHARE
    assert ZOO_GOLD_SHARE <= 0.75 and VAULT_GOLD_SHARE <= 0.75 and TREASURY_GOLD_SHARE[1] <= 0.5
    random.seed(6)
    worst = 0.0
    for floor in (41, 81):
        for _ in range(25):
            _d, _m, floor_items = _lm().generate(floor)
            gold = sum(i.amount for i in floor_items if isinstance(i, items.GoldPile))
            worst = max(worst, gold / economy.floor_income(floor))
    assert worst < 2.0, worst


def test_mini_bosses_and_mysteries_pay_in_proportion():
    for mid, d in _data('monsters.json').items():
        floor = d.get('peak_floor') or d.get('min_level') or 1
        if d.get('is_mini_boss') and not d.get('is_boss') and floor <= 100:
            lo, hi = d['treasure']['gold'][:2]
            assert (lo + hi) / 2 >= 0.3 * economy.floor_income(floor), mid
    import mystery_system
    assert mystery_system.MYSTERY_GOLD_CAP_SHARE <= 0.75


# -------------------------------------------------------------- other paths

def test_the_ring_of_solomon_call_matches_the_function():
    import inspect
    import container_system as cs
    n = len(inspect.signature(cs._handle_success).parameters)
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('_handle_success(self.player, container, self.dungeon')
    call = src[i:src.index(')', i)]
    assert call.count(',') + 1 == n, call


def test_polymorph_cannot_make_a_named_foe():
    import game_magic
    mons = _data('monsters.json')
    for mid in ('tiamat', 'asmodeus', 'surtur', 'abaddon_destroyer', 'arachne', 'seal_demon_war'):
        assert game_magic._is_named_def(mons[mid]), mid
    assert not game_magic._is_named_def(mons['giant_rat'])


def test_quest_weapons_do_not_shatter_when_thrown():
    import game_combat
    gram = types.SimpleNamespace(id='broken_gram', weapon_class='sword', material='iron')
    assert not items.is_random_loot(gram)
    g = types.SimpleNamespace(_THROW_BREAK_CHANCE={'iron': 0.35}, _THROW_BREAK_LEGENDARY=0.0)
    assert game_combat.CombatMixin._get_weapon_break_chance(g, gram) == 0.0
    sword = types.SimpleNamespace(id='iron_longsword', weapon_class='sword', material='iron')
    assert game_combat.CombatMixin._get_weapon_break_chance(g, sword) == 0.35


def test_bones_do_not_carry_quest_items_or_a_fortune():
    src = open(os.path.join(ROOT, 'src', 'bones.py'), encoding='utf-8').read()
    assert '_economy.share(dungeon_level, 0.5)' in src
    assert 'if not _is_random_loot(template):' in src


def test_wipe_scrolls_use_the_real_size_test():
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert 'max_hp <= 500' not in src


def test_the_carrot_is_placed_by_its_quest_only():
    food = _data('items/food.json')['magic_dungeon_carrot']
    assert not any(v for v in (food.get('floor_spawn_weight') or {}).values())
    from dungeon import _food_eligible
    foods = items.load_items('food')
    late = [i for i in foods if int(getattr(i, 'min_level', 1) or 1) > 1]
    for it in late:
        assert it not in _food_eligible(foods, 1), it.id
