"""Every recipe must reward every tier it can be cooked at (2026-06-07).

Bug: the 12 family recipes were authored without a tier-5 outcome.
_apply_tier_outcome resolved the missing tier to the '0' RUINED outcome, so a
PERFECT T5 cook printed its success message but granted nothing -- no SP/HP,
no max HP, no stat. The user hit this on "Undead Bone-Broth".

Two guards:
  * DATA: every recipe defines tier outcomes 1-5 (the rewarding tiers).
  * CODE: a missing tier degrades to the nearest-lower DEFINED tier, never
    silently to the ruined '0' outcome.

Cooking-overhaul (2026-06-07): basic_monster_stew was DELETED -- assorted parts
are eaten as Assorted Monster Jerky instead of cooked. Recipe INPUT costs were
also raised (see test_recipe_costs.py); tier_outcomes (the OUTPUT) are unchanged.
"""
import json
from collections import Counter
from pathlib import Path

from food_system import _apply_tier_outcome
from player import Player

DATA = Path(__file__).resolve().parents[1] / 'data' / 'items'
RECIPES = json.loads((DATA / 'recipes.json').read_text(encoding='utf-8'))
INGREDIENTS = json.loads((DATA / 'ingredient.json').read_text(encoding='utf-8'))


def test_every_recipe_defines_all_rewarding_tiers():
    want = {'1', '2', '3', '4', '5'}
    missing = {rid: sorted(want - set(r.get('tier_outcomes', {}).keys()))
               for rid, r in RECIPES.items()
               if isinstance(r, dict) and (want - set(r.get('tier_outcomes', {}).keys()))}
    assert not missing, f"recipes missing rewarding tier outcomes: {missing}"


def test_t5_family_recipe_grants_real_reward():
    # The exact dish the user cooked.
    pl = Player(); pl.sp = 0; pl.hp = 1
    mhp0, wis0 = pl.max_hp, pl.WIS
    rec = {'id': 'family_undead_recipe', **RECIPES['family_undead_recipe']}
    msgs = _apply_tier_outcome(pl, rec, 5)
    assert pl.sp > 0, msgs            # SP restored
    assert pl.max_hp > mhp0, msgs     # permanent max HP
    assert pl.WIS > wis0, msgs        # permanent stat (undead -> WIS)
    assert any('max HP' in m for m in msgs)


def test_every_family_t5_lands_a_live_themed_buff():
    # T5 must be meaningfully better than T4: each family grants a short themed
    # status buff at T5 only -- and the effect must actually register (no dead
    # buffs from heroism/brilliance-style names that need a caller stat-apply).
    from food_system import _resolve_temp_power
    fams = [k for k in RECIPES if k.startswith('family_') and k.endswith('_recipe')]
    assert fams, 'no family recipes found'
    for fid in fams:
        r = RECIPES[fid]
        t5 = r['tier_outcomes']['5']
        assert t5.get('temp_power') is True, f'{fid}: T5 missing temp_power flag'
        power = r.get('temp_power')
        assert power, f'{fid}: missing top-level temp_power'
        assert not t5.get('temp_power') == r['tier_outcomes']['4'].get('temp_power'), \
            f'{fid}: T4 also has the buff -- T5 must be distinct'
        pl = Player()
        _apply_tier_outcome(pl, {'id': fid, **r}, 5)
        assert pl.has_effect(_resolve_temp_power(power)), \
            f'{fid}: T5 buff {power} did not register (dead buff)'


def test_basic_monster_stew_is_removed():
    # 2026-06-07: deleted. Assorted parts are now eaten as Assorted Monster Jerky;
    # every actual COOK requires monster-specific ingredients.
    assert 'basic_monster_stew' not in RECIPES


def test_missing_tier_degrades_to_nearest_lower_not_ruined():
    # Synthetic recipe defined only to T4: a T5 cook must yield the T4 reward,
    # NOT the ruined '0' outcome.
    rec = {'id': 'synthetic', 'name': 'Test Dish',
           'tier_outcomes': {'0': {'sp': 0, 'hp': 0}, '4': {'sp': 40, 'hp': 3}}}
    pl = Player(); pl.sp = 0; pl.hp = 1
    msgs = _apply_tier_outcome(pl, rec, 5)
    assert pl.sp > 0, msgs                         # got the T4 reward, not zero
    assert not any('ruin' in m.lower() for m in msgs)


def test_tier_zero_still_ruins():
    rec = {'id': 'synthetic', 'name': 'Test Dish',
           'tier_outcomes': {'0': {'sp': 0, 'hp': 0}, '5': {'sp': 99, 'hp': 9}}}
    pl = Player(); pl.sp = 0
    msgs = _apply_tier_outcome(pl, rec, 0)
    assert pl.sp == 0
    assert any('ruin' in m.lower() for m in msgs)
