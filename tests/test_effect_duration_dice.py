"""Regression: monster/trap effect_duration accepts dice notation.

Established 2026-05-20 after bat balance rebalance — fixed duration of 4
turns on a pack-mob confuse felt like a death sentence on floor 1.
Variable 1d4 means usually 1-2 turn pain, occasionally 4. Later mobs can
scale up via larger dice (e.g. umber hulk could use 3d6+2) without
per-mob branching in monster.py.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dice import roll_duration


def test_int_duration_passes_through():
    """Plain int duration must keep working — backwards compat for all
    existing monsters/traps that still use fixed int durations."""
    assert roll_duration(5) == 5
    assert roll_duration(1) == 1
    assert roll_duration(-1) == -1  # permanent-effect sentinel


def test_dice_string_rolls_within_range():
    random.seed(0)
    for _ in range(200):
        r = roll_duration('1d4')
        assert 1 <= r <= 4, f'1d4 produced {r}'


def test_dice_string_with_modifier():
    random.seed(0)
    for _ in range(200):
        r = roll_duration('2d6+3')
        assert 5 <= r <= 15, f'2d6+3 produced {r}'


def test_invalid_duration_type_raises():
    import pytest
    with pytest.raises(TypeError):
        roll_duration(1.5)  # float not accepted
    with pytest.raises(TypeError):
        roll_duration(None)


def test_bat_uses_dice_duration():
    """Specific data assertion: bat must use 1d4 duration after the
    2026-05-20 balance pass. Fixed 4-turn duration on a pack-mob confuse
    was unfair on floor 1."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'monsters.json'),
              encoding='utf-8') as f:
        m = json.load(f)
    bat = m['bat']
    bite = next(a for a in bat['attacks'] if a['name'] == 'bite')
    assert bite['effect'] == 'confused'
    assert bite['effect_chance'] == 0.10, \
        f'bat confuse chance must be 0.10 (was 0.25 — too brutal at pf 1)'
    assert bite['effect_duration'] == '1d4', \
        f"bat confuse duration must be '1d4' (variable, avg 2.5) not fixed 4"
