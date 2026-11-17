"""Pin tests for the harvest + cook engine.

Covers:
  - Permanent-power dispatcher for the boss trophies
  - the dish dispatcher (SP/HP restore, max HP, the stat lesson, a timed
    power, the per-floor caps), on real dishes of the recipe book since the
    kitchen rebuild (2026-11-14; kitchen.apply_dish)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Permanent-power dispatcher per trophy
# ---------------------------------------------------------------------------

def test_trophy_abaddon_grants_all_stats_plus_1():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    str0, con0, dex0, int0, wis0, per0 = p.STR, p.CON, p.DEX, p.INT, p.WIS, p.PER
    msg = _apply_permanent_power(p, 'all_stats_plus_1', {'permanent_desc': '_'})
    assert p.STR == str0 + 1
    assert p.CON == con0 + 1
    assert p.DEX == dex0 + 1
    assert p.INT == int0 + 1
    assert p.WIS == wis0 + 1
    assert p.PER == per0 + 1
    assert 'APOTHEOSIS' in msg


def test_trophy_fenrir_grants_plus_3_str():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    str0 = p.STR
    _apply_permanent_power(p, 'plus_3_str', {'permanent_desc': '_'})
    assert p.STR == str0 + 3


def test_trophy_hrungnir_grants_plus_2_con_petrify_immune():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    con0 = p.CON
    _apply_permanent_power(p, 'plus_2_con_petrify_immune', {'permanent_desc': '_'})
    assert p.CON == con0 + 2


def test_trophy_whispering_crone_grants_plus_2_wis():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    wis0 = p.WIS
    _apply_permanent_power(p, 'plus_2_wis_auto_reveal_secret_doors', {'permanent_desc': '_'})
    assert p.WIS == wis0 + 2


def test_trophy_asmodeus_sets_pact_flag():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'one_time_death_save', {'permanent_desc': '_'})
    assert getattr(p, '_asmodeus_pact', False) is True


def test_trophy_green_knight_sets_revive_flag():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'revive_once_at_half_hp', {'permanent_desc': '_'})
    assert getattr(p, '_green_knight_revive', False) is True


def test_trophy_fafnir_sets_per_descent_hp():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'max_hp_per_floor_descent', {'permanent_desc': '_'})
    assert getattr(p, '_fafnir_per_descent_hp', 0) == 2


def test_trophy_blood_archon_sets_lifesteal():
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'lifesteal_5pct_on_melee', {'permanent_desc': '_'})
    assert abs(getattr(p, '_blood_archon_lifesteal', 0) - 0.05) < 1e-6


# ---------------------------------------------------------------------------
# tier_outcome dispatcher
# ---------------------------------------------------------------------------

def _dish(rid: str):
    """A real dish of the recipe book (data/items/recipes.json)."""
    import kitchen
    return kitchen.recipe(rid)


SP_DISH = 'cook_goblin'               # Goblin Gristle Stew: SP, tier 1
HP_DISH = 'cook_troll'                # Troll Sausage Hotpot: HP, tier 2
STR_DISH = 'cook_wolf_pack_leader'    # Pack Leader Steak: the STR lesson
POWER_DISH = 'cook_shade'             # Gloom-Jelly on Toast: Dark Vision


def test_ruined_returns_ruined_message():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    sp0, hp0 = p.sp, p.hp
    msgs = _apply_recipe_outcome(p, _dish(SP_DISH), ruined=True)
    assert msgs[0].startswith('You ruin the preparation') and 'wasted' in msgs[0]
    assert p.sp == sp0
    assert p.hp == hp0


def test_success_restores_sp_and_hp():
    import kitchen
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    p.sp = 50
    p.hp = 20
    dish = _dish(SP_DISH)
    out = kitchen.dish_outcome(dish)
    heal = kitchen.heal_amount(p, out)
    _apply_recipe_outcome(p, dish)
    assert p.sp == min(p.max_sp, 50 + out['sp'])
    # the meal's heal, and the max HP every proper meal adds (it heals too)
    assert p.hp == 20 + heal + p.COOK_BASE_MAX_HP


def test_success_grants_max_hp_against_floor_cap():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    max_hp0 = p.max_hp
    _apply_recipe_outcome(p, _dish(HP_DISH))
    assert p.max_hp > max_hp0 + p.COOK_BASE_MAX_HP - 1
    assert p._cook_hp_gain_this_floor > 0


def test_success_grants_stat():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    str0 = p.STR
    # A stat dish is the floor's lesson: one whole point (Player.feed_cut_stat,
    # 2026-11-16; two lessons made a point before).
    _apply_recipe_outcome(p, _dish(STR_DISH))
    assert p.STR == str0 + 1 and p.cooking_stat_gained['STR'] == 1
    assert p._cook_stat_gain_this_floor > 0
    p.reset_floor_cook_caps()
    _apply_recipe_outcome(p, _dish(STR_DISH))
    assert p.STR == str0 + 2


def test_success_applies_temp_power():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    _apply_recipe_outcome(p, _dish(POWER_DISH))
    assert p.status_effects.get('dark_vision', 0) > 0


def test_per_floor_caps_block_double_cook_max_hp():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    for _ in range(4):
        _apply_recipe_outcome(p, _dish(HP_DISH))
    assert p._cook_hp_gain_this_floor <= p.PER_FLOOR_HP_CAP


def test_per_floor_caps_block_double_cook_stat():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    _apply_recipe_outcome(p, _dish(STR_DISH))
    taught = dict(p.cooking_stat_gained)
    _apply_recipe_outcome(p, _dish(STR_DISH))
    # one lesson a floor: the second dish teaches nothing
    assert p.cooking_stat_gained == taught


def test_trophy_bypass():
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    p.deepest_floor_reached = 30
    _apply_recipe_outcome(p, _dish(STR_DISH))      # the floor's lesson is used
    str_after_first = p.STR
    # Fenrir's Tooth: its own +3 STR, whatever the floor's lesson.
    _apply_recipe_outcome(p, _dish('trophy_fenrir_wolf_recipe'))
    assert p.STR >= str_after_first + 3


# ---------------------------------------------------------------------------
# Floor change resets the caps
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Wired trophy consumers
# ---------------------------------------------------------------------------

def test_asmodeus_pact_prevents_first_death():
    """Asmodeus's Pact-Blood: when player would die, the pact is consumed
    and HP restored to full."""
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'one_time_death_save', {'permanent_desc': '_'})
    assert p._asmodeus_pact is True
    # Drive HP to 0 and check is_dead
    p.hp = 0
    dead = p.is_dead()
    assert dead is False, "pact should prevent first death"
    assert p.hp == p.max_hp, "HP should be restored to max"
    assert p._asmodeus_pact is False, "pact should be spent"
    # Second death has no protection
    p.hp = 0
    assert p.is_dead() is True, "second death proceeds normally"


def test_green_knight_revive_at_half_hp():
    """Green Knight's Holly-Bough: revive once per run at 50% HP."""
    from player import Player
    from food_system import _apply_permanent_power
    p = Player()
    _apply_permanent_power(p, 'revive_once_at_half_hp', {'permanent_desc': '_'})
    assert p._green_knight_revive is True
    # First death triggers revive
    p.hp = 0
    assert p.is_dead() is False
    assert p.hp == p.max_hp // 2, f"expected HP {p.max_hp // 2}, got {p.hp}"
    assert getattr(p, '_green_knight_revive_used', False) is True
    # Second death: not protected
    p.hp = 0
    assert p.is_dead() is True


def test_fafnir_per_descent_hp_wired_into_change_level():
    """Source check: _change_level applies the per-descent HP from Fafnir's
    Heart trophy when reaching a new deepest floor."""
    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    assert "_fafnir_per_descent_hp" in src
    assert "_nidhogg_per_descent_mp" in src


def test_change_level_resets_per_floor_caps():
    """After reset_floor_cook_caps, the per-floor counters are fresh.

    Note: the lifetime per-stat softcap may still cap stat gains depending
    on `deepest_floor_reached`. At floor 1 the lifetime cap is just 1 STR
    per stat, so we bump the player to a deeper floor to verify the
    per-floor reset itself works regardless of lifetime cap."""
    from player import Player
    from food_system import _apply_recipe_outcome
    p = Player()
    # Set the player deep enough that lifetime cap won't block our test
    p.deepest_floor_reached = 30
    # First-floor cap used
    _apply_recipe_outcome(p, _dish(STR_DISH))
    assert p._cook_stat_gain_this_floor > 0, \
        "first floor cap should have incremented"
    # Simulate floor change
    p.reset_floor_cook_caps()
    assert p._cook_stat_gain_this_floor == 0
    # Now the per-floor counter is fresh: the second lesson makes the point.
    str_before = p.STR
    _apply_recipe_outcome(p, _dish(STR_DISH))
    assert p.STR > str_before
