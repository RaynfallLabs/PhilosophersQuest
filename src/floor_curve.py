"""Floor anchor curve: what an ordinary monster looks like on a given floor.

Median HP and typical damage per hit, by floor. They began as the CURVE.md
section 4 anchors and were re-scaled in the 2026-10 balance pass against
simulated runs (tools/balance/apply_difficulty_schedule.py has the schedule
and the reasons: tougher and harder-hitting at the top of the dungeon, lighter
at the bottom, where tier-5 sums already slow every kill). Monster data is
seated against these by tools/balance/respawn_by_hp.py; runtime code that has
to invent a foe for a floor (the bones ghost) reads them here so it scales
with the dungeon. tests/test_spawn_curve.py checks the two copies agree.
"""
from __future__ import annotations

import math

HP_ANCHORS = {1: 11, 10: 32, 20: 77, 30: 126, 40: 200, 50: 276, 60: 400,
              70: 562, 80: 770, 90: 910, 100: 960}
DMG_ANCHORS = {1: 4.8, 10: 8.1, 20: 9.46, 30: 9.62, 40: 11.38, 50: 15.31,
               60: 18.11, 70: 19.0, 80: 19.5, 90: 19.99, 100: 20.48}


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


# ---------------------------------------------------------------------------
# Pacing dials (2026-10 balance pass). Kept here, beside the anchors, so the
# game, the tests and tools/balance/difficulty_sim.py read one copy.
# ---------------------------------------------------------------------------

# Wandering monsters stop arriving while this many are already hunting the
# player, or while the floor holds wander_alive_cap(level) alive in all: about
# what a floor starts with, so a floor refills as it is cleared but does not
# flood.
WANDER_HUNTING_CAP = 3


def wander_alive_cap(level: int) -> int:
    return min(10 + int(level) // 5, 30)


def natural_regen(max_hp: int) -> int:
    """HP regained per natural regeneration tick."""
    return max(1, int(max_hp) // 50)


# Waits per point of mana regained by meditating (it was 1: three waits then
# bought one Cure Light Wounds, for ever).
MEDITATE_PERIOD = 8
