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
