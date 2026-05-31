"""Pin test for the rotating-subject message gate in main._change_level.

Reported regression (2026-05-31): "The rotating gift settles on
<subject> this floor" was printing on every floor entry — including
ascends, cow-level returns, and Hermes psychopomp pull-backs — when
a Torque of Lugh or Hamsa Hand was equipped.

Fix: gate the message on `(not saved) or enter_from_top` so it only
fires on "feels like a new floor" entries. The rotation mechanic
itself still runs every entry — only the chat line is suppressed.

This file:
  1) Pins the source-level gate so future refactors don't regress it
  2) Documents the semantics for each _change_level call site
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _src(name):
    return (ROOT / "src" / f"{name}.py").read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# Source-level gate pin
# ---------------------------------------------------------------------------

def test_rotating_subject_message_gated_on_new_floor():
    """The message must be gated behind `(not saved) or enter_from_top`."""
    src = _src('main')
    marker = "The rotating gift settles on"
    assert marker in src, "Rotating-subject message disappeared from main.py"
    # Look at the surrounding ~600 chars for the gate.
    idx = src.index(marker)
    window = src[max(0, idx - 600):idx + 200]
    assert "(not saved)" in window or "not saved" in window, \
        "Rotating-subject message no longer gated on `not saved`"
    assert "enter_from_top" in window, \
        "Rotating-subject message no longer gated on `enter_from_top`"


def test_rotation_mechanic_still_fires_every_entry():
    """The random.choice + _rotating_chain_subject assignment must NOT
    be inside the message gate — the mechanic rotates every entry even
    when the message is suppressed."""
    src = _src('main')
    # Find the rotation block.
    idx = src.index("_rotating_chain_subject = _new_rot")
    # Inspect the lines immediately before this assignment.
    pre = src[max(0, idx - 400):idx]
    # The mechanic assignment must NOT be inside an enter_from_top check.
    # We verify by looking for the structure: `if _rotating_pool:` is the
    # outer gate, NOT enter_from_top.
    last_if = pre.rfind("if ")
    if last_if != -1:
        if_line = pre[last_if:].splitlines()[0]
        assert "enter_from_top" not in if_line, \
            "Rotation mechanic is gated on enter_from_top — should only " \
            "gate the message, not the pick"


# ---------------------------------------------------------------------------
# _change_level call-site semantics
# ---------------------------------------------------------------------------
#
# Six callers in src/, with these semantics:
#
#   main._descend_stairs        enter_from_top=True   "going down"
#   main._ascend_stairs         enter_from_top=False  "going up"
#   game_combat (psychopomp)    enter_from_top=False  "death save pulls up"
#   game_encounters _enter_cow  enter_from_top=True   "portal in"
#   game_encounters _exit_cow   enter_from_top=False  "portal out"
#   game_input (xyzzy debug)    enter_from_top=(target >= current)
#
# Combined with the `saved` check, the gate behaves:
#   first descent           → not saved=True,  enter_from_top=True  → FIRES
#   re-descend visited      → not saved=False, enter_from_top=True  → FIRES
#   ascend                  → not saved=False, enter_from_top=False → silent
#   cow level entry         → not saved=True,  enter_from_top=True  → FIRES
#   cow level exit          → not saved=False, enter_from_top=False → silent
#   psychopomp pull-back    → not saved=False, enter_from_top=False → silent
#

EXPECTED_CALL_SITES = (
    ("main", "_descend_stairs", "enter_from_top=True"),
    ("main", "_ascend_stairs", "enter_from_top=False"),
    ("game_combat", "_change_level(self.dungeon_level - 1, enter_from_top=False)", None),
    ("game_encounters", "_enter_cow_level", "enter_from_top=True"),
    ("game_encounters", "_exit_cow_level", "enter_from_top=False"),
)


def test_descend_stairs_uses_enter_from_top_true():
    src = _src('main')
    idx = src.find("def _descend_stairs")
    snippet = src[idx:idx + 1500]
    assert "_change_level(self.dungeon_level + 1, enter_from_top=True)" in snippet


def test_ascend_stairs_uses_enter_from_top_false():
    src = _src('main')
    idx = src.find("def _ascend_stairs")
    snippet = src[idx:idx + 1500]
    assert "_change_level(self.dungeon_level - 1, enter_from_top=False)" in snippet


def test_psychopomp_pullback_uses_enter_from_top_false():
    """Hermes' psychopomp_step death save pulls the player UP one floor."""
    src = _src('game_combat')
    assert "_change_level(self.dungeon_level - 1, enter_from_top=False)" in src
    # And it's in the psychopomp_step block.
    idx = src.find("psychopomp_step")
    snippet = src[idx:idx + 1500]
    assert "_change_level" in snippet


def test_cow_level_entry_uses_enter_from_top_true():
    src = _src('game_encounters')
    idx = src.find("def _enter_cow_level")
    snippet = src[idx:idx + 1200]
    assert "_change_level(COW_LEVEL, enter_from_top=True)" in snippet


def test_cow_level_exit_uses_enter_from_top_false():
    src = _src('game_encounters')
    idx = src.find("def _exit_cow_level")
    snippet = src[idx:idx + 1200]
    assert "_change_level(self._cow_return_level, enter_from_top=False)" in snippet


def test_xyzzy_uses_direction_conditional():
    """The XYZZY debug teleport infers direction from target vs current."""
    src = _src('game_input')
    assert "_change_level(target, enter_from_top=(target >= self.dungeon_level))" in src


# ---------------------------------------------------------------------------
# Behavior: simulate the gate
# ---------------------------------------------------------------------------

def _gate(saved, enter_from_top):
    """Reproduce the gate logic for ad-hoc checks."""
    return (not saved) or enter_from_top


def test_gate_first_descent_fires():
    assert _gate(saved=None, enter_from_top=True) is True


def test_gate_redescend_visited_fires():
    """Re-descending to a previously-visited floor STILL surfaces the
    message — coming DOWN feels like 'entering' a new floor in the
    narrative even if the dungeon state is restored."""
    assert _gate(saved=("dungeon", [], []), enter_from_top=True) is True


def test_gate_ascend_silent():
    assert _gate(saved=("dungeon", [], []), enter_from_top=False) is False


def test_gate_cow_entry_fires():
    """First time entering the Cow Level: not saved + enter_from_top."""
    assert _gate(saved=None, enter_from_top=True) is True


def test_gate_cow_exit_silent():
    """Returning to the floor you portaled out of: saved + not enter_from_top."""
    assert _gate(saved=("dungeon", [], []), enter_from_top=False) is False


def test_gate_psychopomp_pullback_silent():
    """Hermes' T5 psychopomp_step: not enter_from_top, prior floor is saved."""
    assert _gate(saved=("dungeon", [], []), enter_from_top=False) is False
