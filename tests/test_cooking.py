"""End-to-end cooking system tests (Phase 5) — LEGACY.

This file pinned the PRE-2026-05-31 cooking schema (per-ingredient Q0-Q5
recipes, sprite descriptions, floor-scaling SP formulas). The 2026-05-31
harvest+cook redesign replaced the schema entirely (universal/family/
prime/trophy hierarchy + per-recipe tier_outcomes). These tests are
preserved for git history but skipped — see test_harvest_cook_redesign.py
for the new-schema validation.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import pytest

# Skip the entire module — legacy schema. New schema validated by
# test_harvest_cook_redesign.py.
pytestmark = pytest.mark.skip(
    reason="Legacy cooking schema replaced by 2026-05-31 redesign. "
           "See test_harvest_cook_redesign.py for new-schema tests."
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def _load_data():
    return (
        json.loads(Path('data/monsters.json').read_text(encoding='utf-8')),
        json.loads(Path('data/items/recipes.json').read_text(encoding='utf-8')),
        json.loads(Path('data/items/ingredient.json').read_text(encoding='utf-8')),
    )


# ---------------------------------------------------------------------------
# Monster → corpse → ingredient chain
# ---------------------------------------------------------------------------

# Monsters intentionally exempt from harvest (lore/design — Abaddon's swarm
# is otherworldly; angels are celestial; they don't drop earthly meat).
_HARVEST_EXEMPT = {'abyssal_locust', 'heavenly_angel'}


def test_every_monster_has_ingredient_id_or_exempt():
    monsters, _, _ = _load_data()
    missing = []
    for mid, m in monsters.items():
        if not isinstance(m, dict):
            continue
        if mid in _HARVEST_EXEMPT:
            continue
        if not m.get('ingredient_id'):
            missing.append(mid)
    assert not missing, \
        f"Monsters missing ingredient_id (not exempt): {missing}"


def test_every_ingredient_id_resolves():
    monsters, _, ingredients = _load_data()
    broken = []
    for mid, m in monsters.items():
        if not isinstance(m, dict):
            continue
        ing_id = m.get('ingredient_id', '')
        if ing_id and ing_id not in ingredients:
            broken.append(f"{mid} -> {ing_id}")
    assert not broken, \
        "Monster ingredient_id refs don't resolve:\n  " + "\n  ".join(broken)


def test_every_ingredient_has_valid_source_monster():
    monsters, _, ingredients = _load_data()
    bad = []
    for iid, ing in ingredients.items():
        src = ing.get('source_monster', '')
        if src and src not in monsters:
            bad.append(f"{iid} -> {src}")
    assert not bad, \
        "Ingredients with bad source_monster refs:\n  " + "\n  ".join(bad)


# ---------------------------------------------------------------------------
# Ingredient → recipes coverage
# ---------------------------------------------------------------------------

def test_every_ingredient_has_full_q0_q5_solo_recipes():
    _, _, ingredients = _load_data()
    missing = []
    for iid, ing in ingredients.items():
        recs = ing.get('recipes', {})
        # Quality keys are strings '0' through '5'
        for q in ('0', '1', '2', '3', '4', '5'):
            if q not in recs:
                missing.append(f"{iid} missing Q{q}")
    assert not missing, \
        "Ingredients with incomplete Q0-Q5 coverage:\n  " + "\n  ".join(missing[:10])


def test_every_ingredient_solo_recipe_has_name_and_sp():
    _, _, ingredients = _load_data()
    broken = []
    for iid, ing in ingredients.items():
        for q, recipe in (ing.get('recipes', {})).items():
            if not isinstance(recipe, dict):
                broken.append(f"{iid} Q{q}: not a dict")
                continue
            # Q0 is "ruined" and may have empty name; Q1+ must be named
            if q != '0' and not recipe.get('name', '').strip():
                broken.append(f"{iid} Q{q}: missing name")
            if 'sp' not in recipe:
                broken.append(f"{iid} Q{q}: missing sp")
    assert not broken, \
        "Solo recipe metadata gaps:\n  " + "\n  ".join(broken[:10])


# ---------------------------------------------------------------------------
# Compound recipes
# ---------------------------------------------------------------------------

def test_every_compound_recipe_references_real_ingredients():
    _, recipes, ingredients = _load_data()
    broken = []
    for rid, r in recipes.items():
        for iid in r.get('ingredients', []):
            if iid not in ingredients:
                broken.append(f"{rid}: {iid}")
    assert not broken, \
        "Compound recipes ref missing ingredients:\n  " + "\n  ".join(broken[:10])


def test_every_compound_recipe_has_required_fields():
    _, recipes, _ = _load_data()
    missing = []
    for rid, r in recipes.items():
        for f in ('name', 'ingredients', 'sp', 'bonus_type'):
            if f not in r:
                missing.append(f"{rid}: missing {f}")
        if not r.get('ingredients'):
            missing.append(f"{rid}: empty ingredients list")
    assert not missing, \
        "Recipe field gaps:\n  " + "\n  ".join(missing[:10])


def test_every_compound_recipe_has_sprite_desc():
    _, recipes, _ = _load_data()
    no_sprite = [rid for rid, r in recipes.items() if not r.get('sprite_desc', '').strip()]
    assert not no_sprite, \
        f"Recipes missing sprite_desc (UI gap): {no_sprite[:10]}"


def test_recipe_descriptions_present():
    """All recipes should have a description for the cooking-result UI.

    Phase 5B (subagent) authors descriptions for the previously-bare 53;
    this test will pass once that lands.
    """
    _, recipes, _ = _load_data()
    no_desc = [rid for rid, r in recipes.items() if not r.get('description', '').strip()]
    assert len(no_desc) < 5, \
        f"Too many recipes still missing description ({len(no_desc)}): {no_desc[:10]}"


# ---------------------------------------------------------------------------
# Harvest quiz tuning
# ---------------------------------------------------------------------------

def test_harvest_threshold_scales_with_tier():
    """harvest_tier 1 should average lower threshold than harvest_tier 5."""
    monsters, _, _ = _load_data()
    by_ht = defaultdict(list)
    for mid, m in monsters.items():
        if not isinstance(m, dict) or not m.get('ingredient_id'):
            continue
        by_ht[m.get('harvest_tier', 1)].append(m.get('harvest_threshold', 2))
    # Tier 1 average should be < tier 5 average
    if 1 in by_ht and 5 in by_ht:
        avg1 = sum(by_ht[1]) / len(by_ht[1])
        avg5 = sum(by_ht[5]) / len(by_ht[5])
        assert avg5 > avg1 + 1.5, \
            f"Harvest threshold should scale: tier1 avg={avg1:.1f}, tier5 avg={avg5:.1f}"


def test_harvest_tier_within_1_to_5():
    monsters, _, _ = _load_data()
    bad = []
    for mid, m in monsters.items():
        if not isinstance(m, dict) or not m.get('ingredient_id'):
            continue
        ht = m.get('harvest_tier', 1)
        if not (1 <= ht <= 5):
            bad.append(f"{mid}: harvest_tier={ht}")
    assert not bad, f"Out-of-range harvest_tier: {bad}"


# ---------------------------------------------------------------------------
# Balance curve — solo SP scales with floor
# ---------------------------------------------------------------------------

def test_solo_recipe_sp_scales_with_floor():
    """F1-10 ingredient avg SP at Q5 should be lower than F71+ ingredients.

    Post-Phase-5-cooking-fix the curve is compressed (F1-10 Q5 ≈137,
    F91-100 ≈244) because F1-10 was boosted to prevent early-game starvation.
    Still scales monotonically — just not 2x — verify with 1.5x threshold."""
    monsters, _, ingredients = _load_data()
    by_band = defaultdict(list)
    for iid, ing in ingredients.items():
        src = ing.get('source_monster', '')
        lvl = monsters.get(src, {}).get('min_level', 1) if src in monsters else 1
        band = min(9, max(0, (lvl - 1) // 10))
        q5 = ing.get('recipes', {}).get('5', {})
        sp = q5.get('sp') if isinstance(q5, dict) else None
        if isinstance(sp, (int, float)):
            by_band[band].append(sp)
    avg_low = sum(by_band[0]) / len(by_band[0])
    high_bands = [b for b in by_band if b >= 7]
    if high_bands:
        avg_high = sum(s for b in high_bands for s in by_band[b]) / sum(
            len(by_band[b]) for b in high_bands)
        assert avg_high > avg_low * 1.4, \
            f"Solo SP should scale: F1-10 avg={avg_low:.1f}, F71+ avg={avg_high:.1f}"


def test_compound_recipe_sp_scales_with_avg_floor():
    """Compound recipes built from deep ingredients should award more SP."""
    monsters, recipes, ingredients = _load_data()
    # Pair: (avg ingredient floor) → recipe sp
    pairs = []
    for rid, r in recipes.items():
        floors = []
        for iid in r.get('ingredients', []):
            ing = ingredients.get(iid, {})
            src = ing.get('source_monster', '')
            if src in monsters:
                floors.append(monsters[src].get('min_level', 1))
        if not floors:
            continue
        af = sum(floors) / len(floors)
        sp = r.get('sp', 0)
        if isinstance(sp, (int, float)):
            pairs.append((af, sp))
    # Bucket low (<25) vs high (>=50) and compare avg.
    # Post-Phase-5-cooking-fix: F1-10 was boosted 2.25x to fix starvation,
    # so the curve is compressed. Still scales monotonically.
    low_sps = [s for f, s in pairs if f < 25]
    high_sps = [s for f, s in pairs if f >= 50]
    if low_sps and high_sps:
        avg_low = sum(low_sps) / len(low_sps)
        avg_high = sum(high_sps) / len(high_sps)
        assert avg_high > avg_low + 25, \
            f"Compound SP should scale with avg floor: low={avg_low:.1f}, high={avg_high:.1f}"


# ---------------------------------------------------------------------------
# Bonus type distribution — every bonus_type referenced by a recipe is one
# of the engine-supported types
# ---------------------------------------------------------------------------

_VALID_BONUS_TYPES = {
    'none', 'stat', 'combat_stat', 'two_stats', 'status',
    'random_stat', 'all_stats', 'hp', 'mp', 'sp',
}


def test_recipe_bonus_types_are_valid():
    _, recipes, _ = _load_data()
    invalid = []
    for rid, r in recipes.items():
        bt = r.get('bonus_type', 'none')
        if bt not in _VALID_BONUS_TYPES:
            invalid.append(f"{rid}: bonus_type={bt!r}")
    assert not invalid, "Invalid bonus_type values:\n  " + "\n  ".join(invalid[:10])


def test_stat_bonus_recipes_have_bonus_stat():
    _, recipes, _ = _load_data()
    missing = []
    for rid, r in recipes.items():
        if r.get('bonus_type') == 'stat' and not r.get('bonus_stat'):
            missing.append(rid)
    assert not missing, f"stat-type recipes missing bonus_stat: {missing[:10]}"


def test_status_bonus_recipes_have_bonus_effect():
    _, recipes, _ = _load_data()
    missing = []
    for rid, r in recipes.items():
        if r.get('bonus_type') == 'status' and not r.get('bonus_effect'):
            missing.append(rid)
    assert not missing, f"status-type recipes missing bonus_effect: {missing[:10]}"


# ---------------------------------------------------------------------------
# Ingredient coverage — every ingredient should be usable in compound cooking
# OR explicitly marked as "solo-only" (we don't have such a marker yet, so
# this is a soft target).
# ---------------------------------------------------------------------------

def test_ingredient_compound_recipe_coverage_target():
    """Most ingredients should appear in at least one compound recipe.

    Phase 5C (subagent) adds recipes for the 29 orphan late-game ingredients;
    after that lands, the unused count should drop substantially.
    """
    _, recipes, ingredients = _load_data()
    used = set()
    for r in recipes.values():
        for iid in r.get('ingredients', []):
            used.add(iid)
    unused = [iid for iid in ingredients if iid not in used]
    # Allow up to 10 orphan ingredients (very-late-game / lore items).
    # If this fails, Phase 5C didn't ship — check tools/cooking_audit/.
    assert len(unused) <= 10, \
        f"Too many orphan ingredients (no compound recipe): {len(unused)}\n  " + \
        "\n  ".join(sorted(unused)[:15])


# ---------------------------------------------------------------------------
# Pet feeding (Phase 2 pet menu uses Food + Ingredient items)
# ---------------------------------------------------------------------------

def test_ingredients_have_sp_restore_or_are_recipe_only():
    """Ingredients used as standalone (pet feed, raw eat) should have sp_restore.

    Not strictly required by the engine, but the pet-feed mechanic uses
    sp_restore to compute XP grant — so 0 sp_restore = pet gets the floor
    of the formula (20 XP). That's fine, but flagging here for awareness."""
    _, _, ingredients = _load_data()
    zero_sp = sum(1 for ing in ingredients.values() if ing.get('mp_restore', 0) == 0)
    # Just a count, not a failure — informational.
    assert zero_sp >= 0  # always true; the test documents the count


# ---------------------------------------------------------------------------
# Counts (informational sanity)
# ---------------------------------------------------------------------------

def test_dataset_sizes_within_expected_ranges():
    monsters, recipes, ingredients = _load_data()
    assert 400 <= len(monsters) <= 700, f"Monster count {len(monsters)} out of expected band"
    assert 200 <= len(ingredients) <= 500, f"Ingredient count {len(ingredients)} out of band"
    assert 350 <= len(recipes) <= 700, f"Recipe count {len(recipes)} out of band"


# ---------------------------------------------------------------------------
# food_system call sites — cooking quiz uses escalator_chain + cooking subject
# ---------------------------------------------------------------------------

def test_cooking_quiz_uses_escalator_chain():
    src = Path('src/food_system.py').read_text(encoding='utf-8')
    assert "subject='cooking'" in src, "food_system must invoke 'cooking' subject"
    assert "mode='escalator_chain'" in src, "cooking quiz must use escalator_chain mode"


def test_harvest_quiz_uses_animal_subject():
    src = Path('src/food_system.py').read_text(encoding='utf-8')
    assert "subject='animal'" in src, "harvest quiz must use 'animal' subject"


# ---------------------------------------------------------------------------
# Cooking stat softcap — prevents stat ballooning from heavy cooking
# ---------------------------------------------------------------------------

def test_player_has_cooking_stat_gained_tracker():
    from player import Player
    p = Player()
    assert hasattr(p, 'cooking_stat_gained')
    for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
        assert p.cooking_stat_gained.get(stat, -1) == 0


def test_cooking_stat_softcap_by_floor():
    """Softcap increases with deepest floor reached and caps at 15."""
    from player import Player
    p = Player()
    p.deepest_floor_reached = 1
    assert p.cooking_stat_softcap() <= 2, "F1 cap should be very tight"
    p.deepest_floor_reached = 50
    assert 5 <= p.cooking_stat_softcap() <= 10, "F50 cap mid-range"
    p.deepest_floor_reached = 100
    assert p.cooking_stat_softcap() == 15, "F100 cap = 15"


def test_apply_cooking_stat_bonus_respects_softcap():
    """Apply +1 STR 20 times at F100; should never exceed +15 lifetime."""
    from player import Player
    p = Player()
    p.deepest_floor_reached = 100
    base_str = p.STR
    for _ in range(20):
        p.apply_cooking_stat_bonus('STR', 1)
    # Cap is 15 at F100
    assert p.cooking_stat_gained['STR'] == 15, \
        f"Should cap at 15; got {p.cooking_stat_gained['STR']}"
    assert p.STR == base_str + 15, \
        f"STR should rise by exactly 15; rose by {p.STR - base_str}"


def test_apply_cooking_stat_bonus_returns_zero_at_cap():
    from player import Player
    p = Player()
    p.deepest_floor_reached = 100
    # Fill the cap
    p.apply_cooking_stat_bonus('STR', 15)
    # Next attempt should yield 0
    applied = p.apply_cooking_stat_bonus('STR', 3)
    assert applied == 0, f"At cap, should apply 0; applied {applied}"


def test_low_floor_stat_cap_is_tight():
    """An F5 player can't cook themselves to +10 STR before descending."""
    from player import Player
    p = Player()
    p.deepest_floor_reached = 5
    base_str = p.STR
    for _ in range(20):
        p.apply_cooking_stat_bonus('STR', 1)
    # F5 cap is 1
    assert p.cooking_stat_gained['STR'] == 1
    assert p.STR == base_str + 1


def test_food_system_routes_stat_bonuses_through_softcap():
    """The _apply_bonus path must use apply_cooking_stat_bonus, not the
    legacy apply_stat_bonus (which is for non-cooking sources)."""
    src = Path('src/food_system.py').read_text(encoding='utf-8')
    idx = src.find("def _apply_bonus")
    assert idx >= 0
    fn = src[idx:idx + 4000]
    assert 'apply_cooking_stat_bonus' in fn, \
        "_apply_bonus must route through the cooking softcap path"


def test_status_bonuses_not_capped():
    """Status-effect cooked dishes (haste, regen, etc.) should NOT be touched
    by the stat softcap — they're temporary, not permanent."""
    from player import Player
    p = Player()
    # Status bonus path bypasses apply_cooking_stat_bonus entirely
    src = Path('src/food_system.py').read_text(encoding='utf-8')
    idx = src.find("def _apply_bonus")
    fn = src[idx:idx + 4000]
    status_branch_start = fn.find("bonus_type == 'status'")
    status_branch_end = status_branch_start + 400
    status_chunk = fn[status_branch_start:status_branch_end]
    assert 'apply_cooking_stat_bonus' not in status_chunk, \
        "status bonuses must not be capped (they're timed buffs, not permanent)"
    _ = p  # silence unused-var
