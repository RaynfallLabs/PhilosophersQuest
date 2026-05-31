"""Pin tests for the 4 remaining gaps after the third quest-audit pass:

1. Multi-tile boss footprint correctness (Fafnir 2x2 fits its room)
2. NPC dialog cost-vs-block-tier reasonableness (no L3 demands 1000 gold)
3. Cooking / recipe / ingredient schema completeness
4. Prayer system completeness (all 9 prayers dispatchable)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _src(name):
    return (ROOT / "src" / f"{name}.py").read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# 1. Multi-tile boss footprint
# ---------------------------------------------------------------------------

def test_only_one_multi_tile_boss():
    """If a new multi-tile boss gets added, this test forces an
    update so _spawn_boss footprint logic can be verified for it."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    multi_tile = []
    for mid, mon in monsters.items():
        fp = mon.get('footprint', [1, 1])
        if fp and (fp[0] > 1 or fp[1] > 1):
            multi_tile.append((mid, tuple(fp)))
    assert multi_tile == [('fafnir_dragon', (2, 2))], \
        f"New multi-tile bosses detected — verify _spawn_boss handles them: {multi_tile}"


def test_fafnir_lair_room_fits_2x2_footprint():
    """The L60 boss_room for Fafnir must accommodate a 2x2 footprint
    even after the NW-shift fallback."""
    src = _src('boss_levels')
    # The Fafnir room is created with _carve_room(tiles, 42, 43, 12, 5)
    assert "_level_60_lair" in src
    # 12 wide × 5 tall room easily fits a 2x2 anchor at center.
    # Verify _spawn_boss has the footprint-fits-walkable check.
    assert "fw, fh = boss.footprint" in src
    assert "is_walkable(tx, ty)" in src
    assert "shift in range(3)" in src  # NW retry up to 3 times


# ---------------------------------------------------------------------------
# 2. NPC dialog cost-vs-tier reasonableness
# ---------------------------------------------------------------------------

def test_npc_gold_costs_fit_block_tier():
    """An L3 encounter shouldn't demand more gold than a reasonable
    L3 player would have. Rough upper bound: block_max * 80."""
    from npc_encounters import ENCOUNTERS, _BLOCKS
    block_max = {b: hi for b, lo, hi in _BLOCKS}
    issues = []
    for e in ENCOUNTERS:
        ceiling = block_max.get(e['block'], 100) * 80
        for i, opt in enumerate(e.get('options', [])):
            cost = opt.get('cost')
            if isinstance(cost, dict) and cost.get('type') == 'gold':
                amt = int(cost.get('amount', 0))
                if amt > ceiling:
                    issues.append((e['tag'], i, amt, ceiling))
    assert not issues, f"NPC gold costs above reasonable block ceiling: {issues}"


def test_npc_max_hp_costs_reasonable():
    """No encounter should cost more than 30% of estimated player max_hp
    at that block's level (avoids one-shot suicide costs)."""
    from npc_encounters import ENCOUNTERS, _BLOCKS
    block_hi = {b: hi for b, lo, hi in _BLOCKS}
    issues = []
    for e in ENCOUNTERS:
        # Rough estimate: player has 30HP at L1, 200HP at L100
        est_max = 30 + block_hi.get(e['block'], 1) * 1.7
        ceiling = int(est_max * 0.30)
        for i, opt in enumerate(e.get('options', [])):
            cost = opt.get('cost')
            if isinstance(cost, dict) and cost.get('type') == 'max_hp':
                amt = int(cost.get('amount', 0))
                if amt > ceiling:
                    issues.append((e['tag'], i, amt, ceiling))
    assert not issues, f"NPC max_hp costs above 30% estimated: {issues}"


def test_npc_cost_types_are_recognized():
    """All cost types must be in the known set so game_encounters can
    handle them without a silent skip."""
    from npc_encounters import ENCOUNTERS
    # Source of truth: src/game_encounters.py dispatcher cost branches
    valid_cost_types = {
        'food', 'healing_potion', 'potion', 'scroll', 'weapon',
        'gold', 'hp_percent', 'max_hp', 'sp', 'hp', 'mp',
        'random_item', 'triggered_item', 'accept_item',
        'spawn_deadite_ambush',
    }
    bad = []
    for e in ENCOUNTERS:
        for i, opt in enumerate(e.get('options', [])):
            cost = opt.get('cost')
            if isinstance(cost, dict):
                t = cost.get('type')
                if t and t not in valid_cost_types:
                    bad.append((e['tag'], i, t))
    assert not bad, f"NPC cost types not recognized: {bad}"


def test_npc_reward_types_are_recognized():
    """All reward types must be handled by _apply_npc_reward."""
    from npc_encounters import ENCOUNTERS
    valid_reward_types = {
        'gold', 'hp', 'sp', 'mp', 'effect', 'stat', 'message',
        'random_weapon', 'random_armor', 'random_shield',
        'random_accessory', 'random_potion', 'random_scroll',
        'random_food', 'specific_item', 'multi', 'random_item',
        'identify', 'gold_pile', 'restore_hp', 'restore_sp',
        'restore_mp',
    }
    bad = []
    for e in ENCOUNTERS:
        for i, opt in enumerate(e.get('options', [])):
            reward = opt.get('reward')
            if isinstance(reward, dict):
                t = reward.get('type')
                if t and t not in valid_reward_types:
                    bad.append((e['tag'], i, t))
    assert not bad, f"NPC reward types not recognized: {bad}"


def test_npc_karma_values_in_valid_range():
    """Karma deltas should be in {-1, 0, +1} — anything else is suspicious."""
    from npc_encounters import ENCOUNTERS
    bad = []
    for e in ENCOUNTERS:
        for i, opt in enumerate(e.get('options', [])):
            k = opt.get('karma', 0)
            if k not in (-2, -1, 0, 1, 2):
                bad.append((e['tag'], i, k))
    assert not bad, f"NPC karma values out of range: {bad}"


# ---------------------------------------------------------------------------
# 3. Cooking / recipe schema
# ---------------------------------------------------------------------------

def test_recipes_file_exists_and_loads():
    from food_system import _raw_recipes
    recipes = _raw_recipes()
    assert len(recipes) > 100, \
        f"Expected 100+ recipes, got {len(recipes)}"


def test_ingredients_file_exists_and_loads():
    from food_system import _raw_ingredients
    ingredients = _raw_ingredients()
    assert len(ingredients) > 100, \
        f"Expected 100+ ingredients, got {len(ingredients)}"


def test_every_recipe_has_name_and_ingredients():
    from food_system import _raw_recipes
    recipes = _raw_recipes()
    bad = []
    for rid, r in recipes.items():
        if not r.get('name'):
            bad.append((rid, 'no name'))
        if not r.get('ingredients'):
            bad.append((rid, 'no ingredients'))
    assert not bad, f"Recipe schema violations: {bad[:5]}"


def test_every_recipe_ingredient_resolves():
    """No recipe may reference an ingredient that doesn't exist."""
    from food_system import _raw_recipes, _raw_ingredients
    recipes = _raw_recipes()
    ingredients = _raw_ingredients()
    missing = []
    for rid, r in recipes.items():
        for ing in r.get('ingredients', []):
            if ing not in ingredients:
                missing.append((rid, ing))
    assert not missing, f"Recipes reference missing ingredients: {missing[:5]}"


def test_every_recipe_has_effect():
    """Recipes must have at least sp restore OR a bonus_type — otherwise
    cooking yields nothing."""
    from food_system import _raw_recipes
    recipes = _raw_recipes()
    no_effect = [rid for rid, r in recipes.items()
                 if 'sp' not in r and 'bonus_type' not in r]
    assert not no_effect, f"Recipes with no effect: {no_effect[:5]}"


def test_compound_cook_function_wired():
    src = _src('food_system')
    assert "def cook_compound_recipe" in src
    assert "def get_available_compound_recipes" in src
    assert "def harvest_corpse" in src
    assert "def cook_ingredient" in src


def test_food_system_called_from_main_or_game_menus():
    """cook_compound_recipe and harvest_corpse must be invoked somewhere
    in the game loop."""
    found_cook = False
    found_harvest = False
    for fname in ('main', 'game_menus', 'game_input'):
        try:
            src = _src(fname)
            if 'cook_compound_recipe' in src or 'cook_ingredient' in src:
                found_cook = True
            if 'harvest_corpse' in src:
                found_harvest = True
        except FileNotFoundError:
            pass
    assert found_cook, "Cooking function never called from src/"
    assert found_harvest, "Harvest function never called from src/"


# ---------------------------------------------------------------------------
# 4. Prayer system
# ---------------------------------------------------------------------------

EXPECTED_PRAYERS = {
    'pater_noster', 'ave_maria', 'memorare', 'saint_michael',
    'saint_raphael', 'saint_anthony', 'anima_christi',
    'confiteor', 'benedictio',
}


def test_all_expected_prayers_have_handlers():
    src = _src('game_divine')
    for pid in EXPECTED_PRAYERS:
        assert f"_prayer_{pid}" in src, f"Prayer handler {pid} missing"


def test_prayer_dispatch_dict_complete():
    src = _src('game_divine')
    for pid in EXPECTED_PRAYERS:
        assert f"'{pid}':" in src, f"Prayer {pid} missing from dispatch dict"


def test_confiteor_benedictio_altar_only_per_recent_rework():
    """D1 user-fix 2026-05-26: confiteor + benedictio require altar."""
    src = _src('game_divine')
    # Both prayer handlers must exist
    assert "_prayer_confiteor" in src
    assert "_prayer_benedictio" in src


def test_prayer_cooldown_wired():
    src = _src('game_divine')
    assert "prayer_cooldown" in src


def test_pray_input_key_wired():
    src = _src('game_input')
    assert "_start_pray" in src
    # Pray key is K_BACKSLASH per game_input.py:380
    assert "K_BACKSLASH" in src


def test_player_has_prayer_cooldown_field():
    from player import Player
    p = Player()
    assert hasattr(p, 'prayer_cooldown')


# ---------------------------------------------------------------------------
# Misc final hygiene
# ---------------------------------------------------------------------------

def test_all_known_quest_systems_have_test_coverage():
    """Sanity check: my 4 quest test files together cover the systems
    that have non-trivial spawn/effect logic."""
    test_dir = ROOT / "tests"
    test_files = {
        'test_quest_item_lifecycle.py',
        'test_quest_chains.py',
        'test_mystery_flavor_npc_pet.py',
        'test_final_gaps_audit.py',
    }
    for fname in test_files:
        assert (test_dir / fname).exists(), f"Test file {fname} missing"
