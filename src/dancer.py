"""The Dance Uses the Room: a dancer's sidestep with purpose (monster
behaviour, third wave: AI-3, fix_dancer, 2026-11-20).

The dancer AI (the gorgons, the Totentanz dancers, the Seal of Silence's
demon) used to hop to a random free tile beside the hero every turn, by
the plain walkable test: into a fire vent, onto a dug pit, behind a pillar
that broke her own gaze. Now each free tile beside the hero is scored:

  never  a pit, a trap, a hazard she would step on, a tile she cannot stand on;
  +2     a gazer keeps a clear line to the hero from it (her eyes are her
         weapon: Hesiod's and Ovid's gorgons);
  +1     open ground round it (not a corridor's mouth, where she is pinned);

and she takes the best (a random pick among the equal best, so the dance is
not a pattern a kid can learn by rote). With no good tile she stays where
she is. Pure module: Monster._dancer_turn asks sidestep().
"""
from __future__ import annotations

import random

ENABLED = True


def _bad_tile(dungeon, x, y) -> bool:
    if (x, y) in (getattr(dungeon, 'pits', None) or ()):
        return True
    if (x, y) in (getattr(dungeon, 'traps', None) or {}):
        return True
    try:
        import hazards
        if hazards.hazard_at(dungeon, x, y):
            return True
    except (ImportError, AttributeError):
        pass
    return False


def _open_round(dungeon, x, y) -> int:
    return sum(1 for ox in (-1, 0, 1) for oy in (-1, 0, 1)
               if (ox or oy) and dungeon.in_bounds(x + ox, y + oy)
               and dungeon.is_walkable(x + ox, y + oy))


def score(m, dungeon, player, x, y) -> float:
    """How good a tile beside the hero is for her next step (None: never)."""
    if _bad_tile(dungeon, x, y):
        return None
    sc = 0.0
    if getattr(m, 'gaze_paralyze', 0) > 0:
        import senses
        if senses.clear_view(x, y, player.x, player.y, dungeon):
            sc += 2.0
    if _open_round(dungeon, x, y) >= 5:
        sc += 1.0
    return sc


def sidestep(m, player, dungeon, occupied, rng=random):
    """The tile she steps to, or None to stay. ``occupied``: tiles taken
    (the hero's among them)."""
    best, best_sc = [], None
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if not ox and not oy:
                continue
            nx, ny = player.x + ox, player.y + oy
            if (nx, ny) == (m.x, m.y) or (nx, ny) in occupied:
                continue
            if not dungeon.in_bounds(nx, ny) or not m._can_move_to(dungeon, nx, ny):
                continue
            if not ENABLED:
                best.append((nx, ny))
                continue
            sc = score(m, dungeon, player, nx, ny)
            if sc is None:
                continue
            if best_sc is None or sc > best_sc:
                best, best_sc = [(nx, ny)], sc
            elif sc == best_sc:
                best.append((nx, ny))
    if not best:
        return None
    return rng.choice(best)
