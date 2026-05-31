"""Pin tests for Player.__init__ wave 5/6 attr seeding.

Reads use `getattr(self.player, 'attr', default)` defensively so the
attrs aren't strictly required at construction time — but for save/load
consistency, code clarity, and future-proofing, every wave 5/6 runtime
attr that's mutated in main._change_level or main._advance_turn must
be seeded in Player.__init__.

This file pins:
  1) Each of the 17 known wave-5/6 attrs exists on a fresh Player
  2) Each has the correct default type/value

Future contributors who add a new per-floor or per-turn flag to
_change_level / _advance_turn will see this list as the canonical
seeding location.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from player import Player


WAVE_5_6_SEEDED_ATTRS = {
    # Once-per-floor charge flags
    '_seven_league_used_this_floor': False,
    '_gold_offering_used_this_floor': False,
    '_eluned_auto_invis_used': False,
    '_hypatia_protected_used': False,

    # Combat-side counters
    '_et_tu_target': None,
    '_riastrad_hits': 0,
    '_monkey_king_counter': 0,
    '_straight_line_steps': 0,
    '_amazon_charge_armed': False,

    # Per-turn flags
    '_weave_unweave_active': False,
    '_was_on_altar': False,
    '_dragon_blood_active': False,

    # Rotating-subject pick
    '_rotating_chain_subject': None,

    # Terrain caches (refreshed per turn in _advance_turn, but read by
    # player.get_ac() which can be called from many call sites)
    '_armor_proc_adj_enemies': 0,
    '_armor_proc_near_door': False,
    '_armor_proc_in_corridor': False,
    '_armor_proc_on_water': False,
}


def test_every_wave_5_6_attr_is_seeded():
    """A fresh Player must have every wave-5/6 runtime attr already set."""
    p = Player()
    missing = [name for name in WAVE_5_6_SEEDED_ATTRS if not hasattr(p, name)]
    assert not missing, \
        f"Wave 5/6 attrs not seeded in Player.__init__: {missing}"


def test_every_wave_5_6_attr_has_correct_default():
    """Each seeded attr must carry the documented default value."""
    p = Player()
    wrong = []
    for name, expected in WAVE_5_6_SEEDED_ATTRS.items():
        actual = getattr(p, name)
        if actual != expected:
            wrong.append(f"{name}: expected {expected!r}, got {actual!r}")
    assert not wrong, "Wrong defaults: " + "; ".join(wrong)


def test_armor_proc_charge_dicts_initialized_empty():
    """The two charge-tracking collections must be empty but present."""
    p = Player()
    assert hasattr(p, '_armor_proc_charges')
    assert isinstance(p._armor_proc_charges, dict)
    assert len(p._armor_proc_charges) == 0
    assert hasattr(p, '_armor_proc_run_spent')
    assert isinstance(p._armor_proc_run_spent, set)
    assert len(p._armor_proc_run_spent) == 0


def test_seeding_block_grouped_in_init():
    """All wave 5/6 attrs should be grouped together in __init__ for
    code-clarity. Verifies they live near each other (within ~30 lines)."""
    src = (ROOT / "src" / "player.py").read_text(encoding='utf-8')
    init_idx = src.find("def __init__")
    init_end = src.find("def ", init_idx + 1)
    init_body = src[init_idx:init_end]

    line_numbers = {}
    for i, line in enumerate(init_body.splitlines()):
        for attr in WAVE_5_6_SEEDED_ATTRS:
            if f"self.{attr}" in line and "=" in line:
                line_numbers[attr] = i
                break

    if not line_numbers:
        return  # nothing to verify

    lo = min(line_numbers.values())
    hi = max(line_numbers.values())
    span = hi - lo
    assert span <= 30, \
        f"Wave 5/6 seedings span {span} lines — should be grouped " \
        f"(found at relative lines {sorted(line_numbers.values())})"


def test_dragon_blood_active_specifically_seeded():
    """The most-recently-added attr (per the 2026-05-31 follow-up).
    Pinned separately because it was the gap that prompted this test file."""
    p = Player()
    assert hasattr(p, '_dragon_blood_active')
    assert p._dragon_blood_active is False
