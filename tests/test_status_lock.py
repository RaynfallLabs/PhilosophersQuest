"""Status-effect disable-lock + saving-throw tests.

Regression coverage for the autokill where a monster re-applied paralysis/
confuse every turn (additive stacking) and locked the player to death.

The fix (status_effects.py):
  - Control effects are CAPPED per application.
  - HARD control (paralyze/sleep/immobilize/stun/freeze) cannot be re-applied
    while already active or within a post-lock grace window  -> guarantees free
    turns between locks.
  - SOFT control (confuse/fear/charm/slow) refreshes (max), never stacks.
  - DOTs and buffs are unchanged (still additive).
  - Monster-applied debuffs roll a D&D-style save: hard control NEGATED on a
    save, soft control HALVED.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from player import Player
import status_effects as se


def _p():
    return Player()


def test_hard_control_cannot_be_reapplied_while_active():
    p = _p()
    assert se.apply_effect(p, 'paralyzed', 4) is True
    assert p.status_effects['paralyzed'] == 4
    # Re-applying while already paralyzed is ignored (no stack, no refresh).
    assert se.apply_effect(p, 'paralyzed', 4) is False
    assert p.status_effects['paralyzed'] == 4


def test_control_single_application_capped():
    p = _p()
    se.apply_effect(p, 'paralyzed', 10)
    assert p.status_effects['paralyzed'] == 4   # CONTROL_CAP['paralyzed']


def test_soft_control_refreshes_not_stacks():
    p = _p()
    se.apply_effect(p, 'confused', 3)
    se.apply_effect(p, 'confused', 3)
    assert p.status_effects['confused'] == 3    # max(3,3), not 6
    se.apply_effect(p, 'confused', 5)
    assert p.status_effects['confused'] == 5    # refreshed up, capped < 6


def test_dots_and_buffs_still_stack():
    p = _p()
    se.apply_effect(p, 'poisoned', 3)
    se.apply_effect(p, 'poisoned', 3)
    assert p.status_effects['poisoned'] == 6    # DOT still additive
    se.apply_effect(p, 'hasted', 5)
    se.apply_effect(p, 'hasted', 5)
    assert p.status_effects['hasted'] == 10     # buff still additive


def test_grace_window_after_hard_control_blocks_relock():
    p = _p()
    se.apply_effect(p, 'paralyzed', 1)
    se.tick_all(p)                              # paralyzed expires this tick
    assert p.status_effects.get('paralyzed', 0) == 0
    assert p.status_effects.get('control_immune', 0) == se.GRACE_TURNS
    # Cannot be re-locked during the grace window.
    assert se.apply_effect(p, 'paralyzed', 4) is False
    assert p.status_effects.get('paralyzed', 0) == 0
    # Tick the grace out; then hard control can land again.
    for _ in range(se.GRACE_TURNS):
        se.tick_all(p)
    assert p.status_effects.get('control_immune', 0) == 0
    assert se.apply_effect(p, 'paralyzed', 4) is True


def test_reapply_every_turn_cannot_permalock():
    """The original bug: a fast monster re-applies paralysis every turn. The
    player must (a) never be locked beyond the cap and (b) get free turns."""
    p = _p()
    se.apply_effect(p, 'paralyzed', 4)
    peak = p.status_effects['paralyzed']
    free_turns = 0
    locked_streak = max_streak = 0
    for _ in range(60):
        se.tick_all(p)                          # a game turn passes
        se.apply_effect(p, 'paralyzed', 4)      # monster re-applies (worst case, no save)
        cur = p.status_effects.get('paralyzed', 0)
        peak = max(peak, cur)
        if cur > 0:
            locked_streak += 1
            max_streak = max(max_streak, locked_streak)
        else:
            locked_streak = 0
            free_turns += 1
    assert peak <= 4, f"paralysis exceeded cap: {peak}"
    assert free_turns > 0, "player never got a free turn"
    assert max_streak <= 4, f"locked for {max_streak} consecutive turns"


def test_save_negates_hard_control():
    p = _p()
    applied, msg = se.apply_debuff_with_save(p, 'paralyzed', 4, dc=-100)  # always saves
    assert applied is False
    assert p.status_effects.get('paralyzed', 0) == 0
    # Message is FLAVOR (names the effect, hints the stat) and leaks no math.
    assert msg and 'paralysis' in msg.lower()
    assert 'save' not in msg.lower() and 'dc' not in msg.lower()


def test_save_messages_are_flavor_not_math():
    """Resist / partial / fail all produce readable flavor with no dice or DCs."""
    for effect, dc in [('paralyzed', -100), ('confused', -100), ('paralyzed', 100)]:
        _, msg = se.apply_debuff_with_save(_p(), effect, 6, dc=dc)
        assert msg, f"{effect} dc={dc} produced no message"
        low = msg.lower()
        assert 'dc' not in low and 'save' not in low and 'd20' not in low
        assert not any(ch.isdigit() for ch in msg), f"math leaked into: {msg!r}"


def test_save_minimizes_soft_control():
    p = _p()
    applied, _ = se.apply_debuff_with_save(p, 'confused', 6, dc=-100)     # always saves
    assert applied is True
    assert p.status_effects['confused'] == 3     # halved (6 // 2)


def test_failed_save_applies_full_but_capped():
    p = _p()
    applied, _ = se.apply_debuff_with_save(p, 'paralyzed', 5, dc=100)     # always fails
    assert applied is True
    assert p.status_effects['paralyzed'] == 4    # capped


def test_save_stat_mapping_is_sane():
    # Body / mind / reflex split, the categories the player can build toward.
    assert se.SAVE_STAT['paralyzed'] == 'CON'
    assert se.SAVE_STAT['confused'] == 'WIS'
    assert se.SAVE_STAT['slowed'] == 'DEX'


# ---------------------------------------------------------------------------
# Save-bonus foundation (the gradient system: gear / build / mastery / ward)
# ---------------------------------------------------------------------------

def test_save_bonus_sums_permanent_lanes_and_hard_caps():
    p = _p()
    assert p.save_bonus_for('CON') == 0          # nothing yet
    p._save_bonus = {'CON': 2}                   # equipment
    p.save_affinity = {'CON': 1, 'all': 1}       # innate build + an 'all'
    assert p.save_bonus_for('CON') == 4          # 2 + 1 + 1(all)
    assert p.save_bonus_for('WIS') == 1          # only the 'all' touches WIS
    p._save_bonus = {'CON': 99}                  # try to blow past the ceiling
    assert p.save_bonus_for('CON') == 5          # hard cap +5 (gradient, not immunity)


def test_timed_ward_gated_by_status_and_capped_at_3():
    p = _p()
    p._save_guard = {'WIS': 5}
    assert p.save_bonus_for('WIS') == 0          # magnitude inert without the status
    p.status_effects['save_guard_WIS'] = 50      # ward active
    assert p.save_bonus_for('WIS') == 3          # timed lane capped at +3 (5 -> 3)


def test_ward_companion_cleared_when_status_expires():
    p = _p()
    p._save_guard = {'CON': 2}
    p.status_effects['save_guard_CON'] = 1
    se.tick_all(p)                               # ward expires this tick
    assert p.status_effects.get('save_guard_CON', 0) == 0
    assert 'CON' not in p._save_guard             # magnitude companion dropped


def test_save_bonus_actually_improves_save_odds():
    # A big CON save bonus should turn a mid-DC paralysis into a reliable save.
    saved = 0
    for _ in range(200):
        p = _p()
        p._save_bonus = {'CON': 5}               # +5 (capped)
        applied, _ = se.apply_debuff_with_save(p, 'paralyzed', 4, dc=10)
        if not applied:                          # negated == saved
            saved += 1
    assert saved > 140, f"big CON bonus should save most of the time, got {saved}/200"


# ---------------------------------------------------------------------------
# Food-system ward family + bad-food save routing (food_system.py)
# ---------------------------------------------------------------------------

import food_system as fs


class _Potion:
    """Minimal potion stand-in for food_system.drink_potion()."""
    def __init__(self, effect, duration=6, buc='uncursed', power=None):
        self.id = 'test_potion'
        self.is_unique = False
        self.effect = effect
        self.power = power
        self.duration = duration
        self.buc = buc
        self.identified = False


def _ward_outcome(canonical_status: str, amount=2, duration=40):
    """Synth an outcome dict for a save_guard ward (v2.6.4 schema)."""
    return {
        'tier': 3,
        'sp': 10,
        'temp_power': canonical_status,
        'temp_amount': amount,
        'temp_duration': duration,
    }


def test_cooked_ward_grants_status_and_sets_capped_magnitude(monkeypatch):
    """v2.6.4: a recipe -> outcome whose temp_power is a save_guard_* variant
    must grant the companion status AND record the magnitude in _save_guard."""
    p = _p()
    monkeypatch.setattr(fs, '_load_outcomes', lambda: {'ward_con': _ward_outcome('save_guard_CON', 2, 40)})
    recipe = {'name': 'Aegis Stew', 'outcome_id': 'ward_con'}
    fs._apply_recipe_outcome(p, recipe)

    assert p.status_effects.get('save_guard_CON', 0) == 40
    assert p._save_guard.get('CON') == 2
    assert p.save_bonus_for('CON') == 2
    assert p.save_bonus_for('WIS') == 0


def test_cooked_ward_amount_is_clamped_to_3(monkeypatch):
    p = _p()
    monkeypatch.setattr(fs, '_load_outcomes', lambda: {'over': _ward_outcome('save_guard_WIS', 9, 30)})
    recipe = {'name': 'Overcharged Tonic', 'outcome_id': 'over'}
    fs._apply_recipe_outcome(p, recipe)
    assert p._save_guard.get('WIS') == 3
    assert p.save_bonus_for('WIS') == 3


def test_cooked_ward_defaults_to_plus_2_when_unspecified(monkeypatch):
    p = _p()
    outcome_no_amount = {'tier': 3, 'sp': 5, 'temp_power': 'save_guard_WIS', 'temp_duration': 20}
    monkeypatch.setattr(fs, '_load_outcomes', lambda: {'plain': outcome_no_amount})
    recipe = {'name': 'Plain Ward Broth', 'outcome_id': 'plain'}
    fs._apply_recipe_outcome(p, recipe)
    assert p._save_guard.get('WIS') == 2


def test_control_resist_remap_targets_are_wards():
    # The bug being fixed: these used to silently become sleep_resist /
    # magic_resist. They must now resolve to the matching save_guard ward.
    assert fs._resolve_temp_power('paralyze_resist') == 'save_guard_CON'
    assert fs._resolve_temp_power('stunned_resist') == 'save_guard_CON'
    assert fs._resolve_temp_power('petrify_resist') == 'save_guard_CON'
    assert fs._resolve_temp_power('confused_resist') == 'save_guard_WIS'
    assert fs._resolve_temp_power('charm_resist') == 'save_guard_WIS'
    assert fs._resolve_temp_power('feared_resist') == 'save_guard_WIS'
    assert fs._resolve_temp_power('hallucinate_resist') == 'save_guard_WIS'
    # silence has no SAVE_STAT entry -> stays magic_resist (unchanged).
    assert fs._resolve_temp_power('silenced_resist') == 'magic_resist'


def test_bad_food_control_routes_through_save_failure_lands():
    """A bad-food CONTROL outcome routes through apply_debuff_with_save. With a
    guaranteed-fail save the debuff lands and a flavor message is produced."""
    import random
    p = _p()
    random.seed(0)
    # paralysis maps to a CON save; force a failure with a worst-case roll.
    p.CON = 1                                      # large negative modifier
    msgs = fs.drink_potion(p, _Potion('paralysis', duration=4, buc='uncursed'))
    assert p.status_effects.get('paralyzed', 0) > 0
    assert any(m for m in msgs), "control outcome produced no message"


def test_bad_food_control_save_can_negate_hard_control():
    """With a huge CON ward the same paralysis is reliably negated (the point of
    routing bad food through the save)."""
    negated = 0
    for _ in range(60):
        p = _p()
        p._save_bonus = {'CON': 5}                 # +5 capped
        before = dict(p.status_effects)
        fs.drink_potion(p, _Potion('paralysis', duration=4, buc='uncursed'))
        if p.status_effects.get('paralyzed', 0) == before.get('paralyzed', 0):
            negated += 1
    assert negated > 0, "a maxed CON save never negated bad-food paralysis"


def test_bad_food_blessed_resist_branch_preserved():
    """The blessed-constitution branch must NOT route through the save — it
    resists outright with its original flavor and applies nothing."""
    p = _p()
    msgs = fs.drink_potion(p, _Potion('confusion', duration=6, buc='blessed'))
    assert p.status_effects.get('confused', 0) == 0
    assert any('blessed constitution resists' in m for m in msgs)


def test_bad_food_noncontrol_debuff_unchanged():
    """blindness/poison have no SAVE_STAT entry and must stay on the direct
    add_effect path (not routed through the save)."""
    p = _p()
    fs.drink_potion(p, _Potion('blindness', duration=6, buc='uncursed'))
    assert p.status_effects.get('blinded', 0) > 0
    p2 = _p()
    fs.drink_potion(p2, _Potion('poison', duration=6, buc='uncursed'))
    assert p2.status_effects.get('poisoned', 0) > 0
