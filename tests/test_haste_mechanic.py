"""Tests for the haste speed-up mechanic.

Bug being prevented: the original implementation auto-fired a second
`_do_move(dx, dy)` inside the player's move handler whenever the player
was hasted. The result was that a single arrow-key press moved the
player TWO tiles. User intent: the player moves twice as fast as the
*monsters* — not double per keystroke.

Post-fix mechanic: in `_advance_turn`, when the player is hasted, a
`_haste_skip_world` flag toggles. Every other call, the world-tick
methods (`_do_monster_turns`, `_do_pet_turns`, `_maybe_wander_spawn`)
are skipped, so two player actions correspond to one monster action.
Player-side ticks (cooldowns, effect durations, HP regen) happen
normally on every action.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Source-level regression tests
# ---------------------------------------------------------------------------

def test_do_move_no_auto_second_step():
    """Regression: `_do_move` must not auto-fire a second `_do_move` when
    the player is hasted. That was the bug where one keystroke moved two
    tiles."""
    import main
    src = inspect.getsource(main.Game._do_move)
    # The old buggy block used a `_haste_active` flag to guard against
    # infinite recursion. Its presence is a strong signal the bug
    # regressed. The fix removes both the flag and the recursive call.
    assert "_haste_active" not in src, (
        "regression: `_haste_active` re-entry flag is back in _do_move, "
        "which means the auto-second-step bug has been reintroduced"
    )


def test_advance_turn_has_haste_skip_world_toggle():
    """`_advance_turn` must contain the world-tick-skip toggle so a hasted
    player effectively moves twice as fast as monsters."""
    import main
    src = inspect.getsource(main.Game._advance_turn)
    assert "_haste_skip_world" in src, (
        "_advance_turn must use a `_haste_skip_world` flag to gate "
        "world-tick methods while the player is hasted"
    )
    # The skip toggle must occur BEFORE the monster turn call.
    toggle_idx = src.find("_haste_skip_world")
    monster_idx = src.find("_do_monster_turns()")
    assert toggle_idx > 0 and monster_idx > 0, "expected both markers in source"
    assert toggle_idx < monster_idx, (
        "the `_haste_skip_world` toggle must be defined before "
        "`_do_monster_turns()` so it can gate that call"
    )


def test_advance_turn_gates_world_methods_on_haste_skip():
    """The world-tick methods (monster turns, pet turns, wander spawn)
    must sit inside the `if not self._haste_skip_world:` branch."""
    import main
    src = inspect.getsource(main.Game._advance_turn)
    # Locate the `if not self._haste_skip_world:` line, then verify the
    # three world-tick methods all appear AFTER it. (Other methods like
    # _death_proximity_warning + _tick_hp_regen are still allowed to run
    # every turn — they're player-side UI/regen, not world action.)
    gate = "if not self._haste_skip_world:"
    assert gate in src, f"expected gate line '{gate}' in _advance_turn"
    after_gate = src[src.index(gate):]
    assert "self._do_monster_turns()" in after_gate, (
        "_do_monster_turns must be gated by _haste_skip_world"
    )
    assert "self._do_pet_turns()" in after_gate, (
        "_do_pet_turns must be gated by _haste_skip_world"
    )
    assert "self._maybe_wander_spawn()" in after_gate, (
        "_maybe_wander_spawn must be gated by _haste_skip_world"
    )


# ---------------------------------------------------------------------------
# Behavioural test of the toggle pattern itself
# ---------------------------------------------------------------------------

def _haste_toggle(state: dict, hasted: bool) -> bool:
    """Pure replica of the toggle logic in _advance_turn. Returns True if
    the world tick should be SKIPPED this action."""
    if hasted:
        state["_haste_skip_world"] = not state.get("_haste_skip_world", False)
    else:
        state["_haste_skip_world"] = False
    return state["_haste_skip_world"]


def test_haste_toggle_two_player_actions_per_world_tick():
    """6 hasted player actions should produce 3 world ticks."""
    state: dict = {}
    world_ticks = 0
    for _ in range(6):
        skip = _haste_toggle(state, hasted=True)
        if not skip:
            world_ticks += 1
    assert world_ticks == 3, (
        f"expected 3 world ticks per 6 hasted actions, got {world_ticks}"
    )


def test_haste_toggle_alternates_skip_and_run():
    """The skip flag must alternate True/False each hasted action."""
    state: dict = {}
    results = [_haste_toggle(state, hasted=True) for _ in range(4)]
    assert results == [True, False, True, False], (
        f"expected alternating True/False; got {results}"
    )


def test_haste_toggle_resets_when_haste_expires():
    """When haste expires, the toggle must reset so a fresh haste starts
    in the same phase as the first apply."""
    state: dict = {}
    # First haste cycle: skip True, then False
    assert _haste_toggle(state, hasted=True) is True
    assert _haste_toggle(state, hasted=True) is False
    # Haste expires — flag should reset to False (no skip)
    assert _haste_toggle(state, hasted=False) is False
    assert state["_haste_skip_world"] is False
    # New haste applied — first action skips again
    assert _haste_toggle(state, hasted=True) is True


def test_haste_toggle_unhasted_never_skips():
    """An un-hasted player must never have world-tick skipped."""
    state: dict = {}
    for _ in range(10):
        assert _haste_toggle(state, hasted=False) is False


def test_status_effect_description_updated():
    """The status-effect tooltip description must reflect the new mechanic
    (world tick skipped half the time) rather than the old wrong text
    ('Extra action each turn')."""
    from status_effects import EFFECT_INFO
    label, _color, desc = EFFECT_INFO["hasted"]
    assert label == "Hasted"
    assert "Extra action" not in desc, (
        f"stale description still references 'Extra action': {desc!r}"
    )
    # Sanity check: new copy mentions the monster cadence
    assert "monster" in desc.lower() or "half" in desc.lower(), (
        f"haste description should describe the new mechanic; got: {desc!r}"
    )
