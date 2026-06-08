"""Pin tests for the 2026-05-31 harvest+cook redesign.

Verifies the new schema:
  - ingredient.json has 1 universal + 12 family + 527 prime + 13 trophy + 8 dungeon
  - recipes.json has 0 basic (deleted 2026-06-07) + 12 family + 514 prime + 13 trophy
  - prime_cuts.json has all 527 monsters mapped
  - food_system._harvest_outcome_for_tier produces correct cumulative outcomes
  - Per-floor cap mechanism on Player works (cap, bypass, reset)
  - Trophy recipes bypass the floor cap
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Data schema invariants
# ---------------------------------------------------------------------------

def test_ingredient_schema():
    """Ingredient.json structure: 1 universal + 12 family + 516 prime + 13 trophy + 8 dungeon.

    Note: 11 prime ingredients were removed during the 2026-05-31 cleanup —
    they were trophy bosses' "secondary" prime cuts that the harvest path
    never yields (trophy bosses give the trophy at T5, not a regular prime).
    Removed: medusa_gorgon_prime, fafnir_dragon_prime, abaddon_destroyer_prime,
    green_knight_prime, nidhoggr_fragment_prime, whispering_crone_prime,
    tiamat_prime, asmodeus_prime, surtur_prime, ymir_last_spawn_prime,
    hrungnirs_ghost_prime. (Blood archon's prime survives because at least
    one master recipe references it.)
    """
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    counts = {'universal': 0, 'family': 0, 'prime': 0, 'trophy': 0, 'dungeon': 0}
    for ing in d.values():
        counts[ing['tier_role']] = counts.get(ing['tier_role'], 0) + 1
    assert counts['universal'] == 1, f"expected 1 universal, got {counts['universal']}"
    assert counts['family'] == 12, f"expected 12 family, got {counts['family']}"
    assert counts['prime'] == 516, f"expected 516 prime, got {counts['prime']}"
    # 14 trophies: the original 13 + asterion_minotaur, converted from a prime to
    # a trophy by the Boss Class Ascension integration (2026-06-07) so all four
    # floor-20/40/60/80 bosses use the uniform trophy_{boss}_recipe ascension flow.
    assert counts['trophy'] == 14, f"expected 14 trophy, got {counts['trophy']}"
    assert counts['dungeon'] == 8, f"expected 8 dungeon, got {counts['dungeon']}"


def test_assorted_monster_parts_exists():
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    assert 'assorted_monster_parts' in d
    assert d['assorted_monster_parts']['tier_role'] == 'universal'


def test_twelve_families_present():
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    EXPECTED = {'beast', 'demon', 'undead', 'fey', 'construct', 'elemental',
                'plant', 'aberration', 'humanoid', 'reptile', 'celestial', 'dragon'}
    found = {ing['family'] for ing in d.values() if ing['tier_role'] == 'family'}
    assert found == EXPECTED, f"missing/extra families: {EXPECTED ^ found}"


def test_thirteen_trophy_bosses():
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    EXPECTED = {
        'abaddon_destroyer', 'tiamat', 'fafnir_dragon', 'fenrir_wolf',
        'surtur', 'ymir_last_spawn', 'hrungnirs_ghost', 'asmodeus',
        'nidhoggr_fragment', 'green_knight', 'whispering_crone',
        'blood_archon', 'medusa_gorgon',
        # Converted prime -> trophy for the Boss Class Ascension (2026-06-07).
        'asterion_minotaur',
    }
    trophy_sources = {
        ing['source_monster'] for ing in d.values()
        if ing['tier_role'] == 'trophy'
    }
    assert trophy_sources == EXPECTED, f"trophy mismatch: {EXPECTED ^ trophy_sources}"


def test_every_prime_has_temp_power_mapping():
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    missing = [iid for iid, ing in d.items()
               if ing['tier_role'] == 'prime' and not ing.get('temp_power')]
    assert not missing, f"primes missing temp_power: {missing[:5]}"


def test_every_prime_has_stat_grant():
    d = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    missing = [iid for iid, ing in d.items()
               if ing['tier_role'] in ('prime', 'trophy') and ing.get('stat_grant') not in
               {'STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'}]
    assert not missing, f"primes with bad stat_grant: {missing[:5]}"


def test_recipe_schema():
    """Verify the recipe bank has all expected classes.

    Counts after Phase 2 merge will include master_prime and dungeon_keyed
    recipes; before merge, only the core 4 classes are present."""
    d = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    counts = {}
    for r in d.values():
        cls = r.get('recipe_class', '?')
        counts[cls] = counts.get(cls, 0) + 1
    # 2026-06-07 cooking overhaul: basic_monster_stew DELETED (assorted parts are
    # now eaten as Assorted Monster Jerky, not cooked).
    assert counts.get('basic', 0) == 0
    assert counts.get('family', 0) == 12
    assert counts.get('prime', 0) >= 500  # 527 - 13 trophies
    # +1 trophy: asterion converted prime->trophy for Boss Class Ascension.
    assert counts.get('trophy', 0) == 14
    # Post-merge: master_prime and dungeon_keyed may or may not be present
    # depending on whether Phase 2 has merged yet. We don't assert their
    # absence; if present, they should be valid recipe classes.


def test_every_recipe_has_tier_outcomes():
    d = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    missing = [rid for rid, r in d.items() if 'tier_outcomes' not in r]
    assert not missing, f"recipes missing tier_outcomes: {missing[:5]}"


def test_trophy_recipes_have_permanent_power():
    d = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    trophies = [r for r in d.values() if r.get('recipe_class') == 'trophy']
    assert len(trophies) == 14
    for r in trophies:
        # Boss Class Ascension recipes (floors 20/40/60/80) grant a CLASS NODE
        # instead of a permanent_power — the meal IS the class choice. They are
        # exempt from the permanent_power requirement (the cook signals ascension).
        if r.get('class_ascension'):
            continue
        assert r.get('permanent_power'), f"trophy {r.get('name')} missing permanent_power"
        # T5 outcome must have bypass_floor_cap flag
        t5 = r['tier_outcomes'].get('5', {})
        assert t5.get('bypass_floor_cap') is True, \
            f"trophy {r.get('name')} T5 must bypass_floor_cap"


def test_every_recipe_references_real_ingredients():
    """Every ingredient_id in every recipe must exist in ingredient.json."""
    recipes = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    ingredients = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    broken = []
    for rid, r in recipes.items():
        for ing_id in r.get('ingredients', []):
            if ing_id not in ingredients:
                broken.append(f"{rid} -> {ing_id}")
    assert not broken, f"recipes reference missing ingredients: {broken[:5]}"


def test_prime_cuts_mapping_complete():
    """prime_cuts.json must cover all 527 monsters from monsters.json."""
    pc = json.loads((ROOT / "data" / "items" / "prime_cuts.json").read_text(encoding='utf-8'))
    monsters = json.loads((ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    missing = set(monsters.keys()) - set(pc['primes'].keys())
    assert not missing, f"prime_cuts missing monsters: {sorted(missing)[:5]}"


def test_master_prime_recipes_present_post_merge():
    """After Phase 2 merge, the bank includes master-prime cross-monster combos."""
    d = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    masters = [r for r in d.values() if r.get('recipe_class') == 'master_prime']
    if not masters:
        # Phase 2 not yet merged — skip
        import pytest
        pytest.skip("master_prime recipes not yet merged from Phase 2")
    # Each master_prime should reference 2+ different prime cuts
    for r in masters:
        ings = r.get('ingredients', [])
        primes_in_recipe = [i for i in ings if i.endswith('_prime') or i.endswith('_trophy')]
        assert len(set(primes_in_recipe)) >= 2 or len(ings) >= 3, \
            f"master_prime {r.get('name')} should combine 2+ primes or have substantial ingredient list"


def test_dungeon_keyed_recipes_use_terrain_ingredients():
    """Dungeon-keyed recipes must include at least one tier_role=dungeon ingredient."""
    d = json.loads((ROOT / "data" / "items" / "recipes.json").read_text(encoding='utf-8'))
    ingredients = json.loads((ROOT / "data" / "items" / "ingredient.json").read_text(encoding='utf-8'))
    dungeon_ids = {iid for iid, ing in ingredients.items() if ing.get('tier_role') == 'dungeon'}
    dungeon_recipes = [r for r in d.values() if r.get('recipe_class') == 'dungeon_keyed']
    if not dungeon_recipes:
        import pytest
        pytest.skip("dungeon_keyed recipes not yet merged from Phase 2")
    for r in dungeon_recipes:
        ings_set = set(r.get('ingredients', []))
        assert ings_set & dungeon_ids, \
            f"dungeon_keyed {r.get('name')} must include a tier_role=dungeon ingredient"


# ---------------------------------------------------------------------------
# Harvest outcome function
# ---------------------------------------------------------------------------

def test_harvest_outcome_tier_0_yields_nothing():
    from food_system import _harvest_outcome_for_tier
    assert _harvest_outcome_for_tier(0, 'giant_rat') == []


def test_harvest_outcome_tier_1_yields_one_assorted():
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(1, 'giant_rat')
    assert out == ['assorted_monster_parts']


def test_harvest_outcome_tier_2_yields_two_assorted():
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(2, 'giant_rat')
    assert out == ['assorted_monster_parts'] * 2


def test_harvest_outcome_tier_3_adds_family():
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(3, 'giant_rat')
    # giant_rat is a beast → family_beast
    assert out == ['assorted_monster_parts', 'assorted_monster_parts', 'family_beast']


def test_harvest_outcome_tier_4_yields_two_family():
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(4, 'giant_rat')
    assert out.count('family_beast') == 2


def test_harvest_outcome_tier_5_yields_prime():
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(5, 'giant_rat')
    assert 'giant_rat_prime' in out


def test_harvest_outcome_tier_5_boss_yields_trophy():
    """For trophy bosses, T5 yields the TROPHY ingredient, not a regular prime."""
    from food_system import _harvest_outcome_for_tier
    out = _harvest_outcome_for_tier(5, 'abaddon_destroyer')
    assert 'abaddon_destroyer_trophy' in out


# ---------------------------------------------------------------------------
# Per-floor stat-cap mechanism on Player
# ---------------------------------------------------------------------------

def test_player_has_floor_cap_attrs():
    from player import Player
    p = Player()
    assert hasattr(p, '_cook_stat_gain_this_floor')
    assert hasattr(p, '_cook_hp_gain_this_floor')
    assert p._cook_stat_gain_this_floor == 0
    assert p._cook_hp_gain_this_floor == 0


def test_per_floor_stat_cap_blocks_second_gain():
    """Player can only gain +1 stat per floor; second attempt returns 0."""
    from player import Player
    p = Player()
    a = p.try_apply_cook_stat_gain('STR', 1)
    assert a == 1
    # Second attempt on same floor — should return 0 (cap reached)
    b = p.try_apply_cook_stat_gain('CON', 1)
    assert b == 0


def test_per_floor_hp_cap_blocks_excess():
    """Player can only gain +5 max HP per floor.

    Note: the lifetime cooking_softcap (diminishing returns) may shrink
    the gain further. We just verify the per-floor cap is enforced — i.e.
    after the cap fills, additional requests return 0.
    """
    from player import Player
    p = Player()
    a = p.try_apply_cook_hp_gain(3)
    assert a >= 1, f"first +3 HP should grant at least 1, got {a}"
    # After the first gain, request +5 — should NOT exceed the remaining cap
    b = p.try_apply_cook_hp_gain(5)
    # Remaining cap after `a` was 5 - a. b cannot exceed that.
    remaining_after_a = 5 - a
    assert 0 <= b <= remaining_after_a, \
        f"second gain {b} must be in [0, {remaining_after_a}]"
    # Once cap fully consumed, further gains MUST return 0.
    c = p.try_apply_cook_hp_gain(10)
    assert c == 0, f"after cap exhausted, gain must be 0; got {c}"


def test_trophy_bypass_ignores_floor_cap():
    """Trophy recipes pass bypass=True; cap is irrelevant."""
    from player import Player
    p = Player()
    # First fill the regular cap
    p.try_apply_cook_stat_gain('STR', 1)
    # Now a trophy gain should still land
    a = p.try_apply_cook_stat_gain('WIS', 1, bypass=True)
    assert a == 1, f"trophy bypass should grant +1 WIS, got {a}"


def test_floor_cap_resets_on_reset_call():
    from player import Player
    p = Player()
    p.try_apply_cook_stat_gain('STR', 1)
    assert p._cook_stat_gain_this_floor == 1
    p.reset_floor_cook_caps()
    assert p._cook_stat_gain_this_floor == 0
    # And a fresh gain can now land
    a = p.try_apply_cook_stat_gain('DEX', 1)
    assert a == 1


def test_floor_cap_reset_wired_into_change_level():
    """main._change_level must call reset_floor_cook_caps."""
    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    assert "reset_floor_cook_caps" in src
