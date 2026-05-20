"""Regression: status-effect damage at HP 0 must trigger death.

Established 2026-05-20 after playtest: player was poisoned by a toxic
jelly, killed the slime, but poison ticks reduced HP to 0 — and the
player kept walking around until poison expired. The death-detection
code path was only in monster-attack handlers, not in the per-turn
status-effect tick.

This test verifies HP 0 from a poison tick now triggers death.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from player import Player
from status_effects import tick_all as tick_effects


def test_poison_tick_to_zero_marks_player_dead():
    """A poisoned player at 1 HP must reach is_dead() after the next tick."""
    p = Player()
    p.hp = 1
    p.add_effect('poisoned', 5)
    tick_effects(p)
    assert p.hp == 0
    assert p.is_dead()


def test_bleeding_tick_to_zero_marks_player_dead():
    p = Player()
    p.hp = 1
    p.add_effect('bleeding', 5)
    tick_effects(p)
    assert p.hp == 0
    assert p.is_dead()


def test_strangulation_tick_to_zero_marks_player_dead():
    p = Player()
    p.hp = 2
    p.add_effect('strangulation', 5)
    tick_effects(p)
    assert p.hp == 0
    assert p.is_dead()


def test_poison_below_zero_clamps_to_zero():
    """HP shouldn't go negative — it's clamped at 0."""
    p = Player()
    p.hp = 1
    p.add_effect('poisoned', 10)
    for _ in range(5):
        tick_effects(p)
    assert p.hp == 0
    assert p.is_dead()
