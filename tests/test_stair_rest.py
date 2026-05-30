"""Regression tests for the stair-rest exploit reported 2026-05-29.

Bug: `Player.on_level_change` granted +15 SP and +max(2, INT//5) MP
on EVERY staircase use. A player could descend one floor and ascend
back, repeatedly, to fully recover SP and MP for free. (HP was already
gated for descent by `STAIR_REST_CAP_DESC = 0`, but SP/MP were not.)

Fix: rest-heal applies only on the FIRST visit to a floor.
`Game._change_level` passes `first_visit = not saved` where `saved` is
the level_mgr cache hit — truthy iff the player has been here before.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _fresh_player(sp_drain: int = 10, mp_drain: int = 5, hp_drain: int = 10):
    """Build a Player at less-than-full SP/MP/HP so we can detect
    whether rest-heal happens."""
    from player import Player
    p = Player()
    p.sp = max(0, p.max_sp - sp_drain)
    p.mp = max(0, p.max_mp - mp_drain)
    p.hp = max(1, p.max_hp - hp_drain)
    return p


# ---------------------------------------------------------------------------
# Direct unit tests of Player.on_level_change
# ---------------------------------------------------------------------------

def test_first_visit_descent_grants_sp_and_mp():
    """Descending into a new floor should refill some SP and MP."""
    p = _fresh_player()
    sp_before, mp_before = p.sp, p.mp
    p.on_level_change(ascending=False, first_visit=True)
    assert p.sp > sp_before, "first descent should grant SP"
    assert p.mp > mp_before, "first descent should grant MP"


def test_first_visit_ascent_grants_sp_mp_and_hp():
    """Ascending into a new floor grants HP too (CAP_ASC > 0)."""
    p = _fresh_player()
    sp_before, mp_before, hp_before = p.sp, p.mp, p.hp
    p.on_level_change(ascending=True, first_visit=True)
    assert p.sp > sp_before, "first ascent should grant SP"
    assert p.mp > mp_before, "first ascent should grant MP"
    assert p.hp > hp_before, "first ascent should grant HP (CAP_ASC > 0)"


def test_revisit_grants_nothing():
    """Revisiting any floor (first_visit=False) grants zero rest-heal.
    This is the stair-stomp exploit fix."""
    p = _fresh_player()
    sp_before, mp_before, hp_before = p.sp, p.mp, p.hp
    p.on_level_change(ascending=False, first_visit=False)
    assert p.sp == sp_before, "revisit must not grant SP"
    assert p.mp == mp_before, "revisit must not grant MP"
    assert p.hp == hp_before, "revisit must not grant HP"
    # Ascent revisit same story
    p.on_level_change(ascending=True, first_visit=False)
    assert p.sp == sp_before
    assert p.mp == mp_before
    assert p.hp == hp_before


def test_stair_stomp_cannot_recover_sp_to_full():
    """The exact exploit the user reported: cycle down→up→down→up... and
    SP refuses to climb back to max after the first visit's bonus."""
    p_max_drain = 30
    p = _fresh_player(sp_drain=p_max_drain)
    # First descent: gain SP (legit)
    p.on_level_change(ascending=False, first_visit=True)
    legit_sp = p.sp
    assert legit_sp > p.max_sp - p_max_drain, "first descent grants SP"
    # Now stair-stomp 20 cycles: each one is a REVISIT (first_visit=False)
    for _ in range(20):
        p.on_level_change(ascending=True, first_visit=False)
        p.on_level_change(ascending=False, first_visit=False)
    assert p.sp == legit_sp, (
        f"stair-stomping must not raise SP above legit level "
        f"({legit_sp}); got {p.sp}"
    )


# ---------------------------------------------------------------------------
# Source-level regression: _change_level must pass first_visit
# ---------------------------------------------------------------------------

def test_change_level_passes_first_visit_kwarg():
    """If the call site ever loses the `first_visit=...` kwarg, every
    visit becomes "first" again and the exploit is back."""
    import inspect
    import main
    src = inspect.getsource(main.Game._change_level)
    assert "first_visit=" in src, (
        "_change_level must pass first_visit to player.on_level_change "
        "to prevent the stair-stomp SP/MP exploit"
    )
    # And the value must derive from the level-load cache hit (not a
    # constant True/False that would re-break the exploit).
    assert "first_visit=notsaved" in src.replace(" ", ""), (
        "first_visit must be derived from level_mgr.load() returning "
        "None (i.e., `not saved`); a hardcoded value would defeat the fix"
    )
