"""Time to explore and hunger sized to a kid's real pace (2026-11-16).

Brandon: "check my previous runs, how many turns did I spend on each floor?
I bet it's more than you expected." His saves: about 950 turns on floor 1
and 700 on floor 2 (3.5.2), about 540 a floor on floors 1-3 and 820 on
floor 4 (October). The time to explore had been about 500 turns on floor
1's median map, so at his pace he met newcomers on most floors; and a new
hero starved at about turn 420. His ruling: size each floor's time to
explore and the food to a kid at his pace (about 700-950 turns a floor),
in the base data and curves.

Proven here by the dials and real generated maps (random maps and deep
floors are not play-testable in a few minutes).
"""
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402
import wanderers  # noqa: E402
from player import Player  # noqa: E402


def test_a_kids_pace_on_the_first_floors_is_brandons():
    """kid_pace on floor 1-4 maps (tours of about 125-480 tiles) is the
    700-950 turns his saves show, give or take the map."""
    assert 650 <= floor_curve.kid_pace(196) <= 750           # floor 1's median map
    assert 800 <= floor_curve.kid_pace(300) <= 900           # floors 2-4
    assert floor_curve.kid_pace(0) == floor_curve.KID_PACE_FLAT


def test_the_grace_gives_a_kid_at_his_pace_a_third_to_spare():
    for tour in (124, 196, 300, 410, 500, 812, 1600, 2000):
        pace, grace = floor_curve.kid_pace(tour), floor_curve.wander_grace(tour)
        assert grace >= 1.3 * pace, (tour, pace, grace)
        assert grace <= 1.5 * pace, (tour, pace, grace)      # not a floor with no clock at all


def test_floor_one_time_to_explore_covers_a_950_turn_floor_on_its_median_map():
    """The slow end of his pace, on real floor-1 maps: the median grace is
    over 900 turns (it was about 500)."""
    import level_manager
    level_manager.LevelManager._maybe_spawn_bones = staticmethod(lambda *a, **k: None)
    graces = []
    for seed in range(5):
        random.seed(4100 + seed)
        d, _m, _i = level_manager.LevelManager().generate(1)
        graces.append(wanderers.grace(d))
    graces.sort()
    assert graces[len(graces) // 2] >= 850, graces


def test_hunger_runs_on_the_one_dial():
    """Game._tick_sp and the Ring of Sustenance read floor_curve.HUNGER_EVERY
    (the simulator reads it too), and a new hero's belly lasts a floor at a
    kid's pace."""
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('def _tick_sp(self):')
    body = src[i:i + 1500]
    assert 'HUNGER_EVERY' in body
    assert not re.search(r"drain_interval = 4 if .* else 2", body)
    import rings
    p = Player()
    assert rings.hunger_interval(p, floor_curve.HUNGER_EVERY) == floor_curve.HUNGER_EVERY
    # A new hero with nothing to eat starves after max_sp x HUNGER_EVERY
    # steps: past floor 1's whole time to explore on its median map.
    # (2026-11-22: with his starting bread ration; hunger every 3 steps)
    assert (p.max_sp + 45) * floor_curve.HUNGER_EVERY >= floor_curve.kid_pace(196)
