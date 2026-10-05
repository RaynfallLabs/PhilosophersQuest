"""Floor anchor curve: what an ordinary monster looks like on a given floor.

Runtime copy of the CURVE.md section 4 anchors (median HP and typical damage
per hit). Monster data is seated against these by
tools/balance/respawn_by_hp.py; runtime code that has to invent a foe for a
floor (the bones ghost) reads them here so it scales with the dungeon.
tests/test_spawn_curve.py checks the two copies agree.
"""
from __future__ import annotations

import math

HP_ANCHORS = {1: 8, 10: 21, 20: 55, 30: 110, 40: 210, 50: 325, 60: 500,
              70: 750, 80: 1100, 90: 1400, 100: 1600}
DMG_ANCHORS = {1: 2.0, 10: 3.75, 20: 5.25, 30: 6.25, 40: 8.75, 50: 12.25,
               60: 15.75, 70: 20.25, 80: 24.75, 90: 30.25, 100: 35.0}


def _interp(anchors: dict, floor: float) -> float:
    ks = sorted(anchors)
    floor = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= floor <= b:
            t = (floor - a) / (b - a)
            return math.exp(math.log(anchors[a]) * (1 - t) + math.log(anchors[b]) * t)
    return float(anchors[ks[-1]])


def target_hp(floor: float) -> float:
    """Median HP of an ordinary monster on `floor`."""
    return _interp(HP_ANCHORS, floor)


def target_dmg(floor: float) -> float:
    """Typical damage of one ordinary monster hit on `floor`."""
    return _interp(DMG_ANCHORS, floor)


def dice_for_average(avg: float, sides: int = 6) -> str:
    """A dice string whose mean is about `avg` (at least 1d4)."""
    if avg < 3:
        return '1d4'
    n = max(1, int(round(avg / (sides + 1))))
    mod = int(round(avg - n * (sides + 1) / 2))
    return f'{n}d{sides}+{mod}' if mod > 0 else f'{n}d{sides}'
