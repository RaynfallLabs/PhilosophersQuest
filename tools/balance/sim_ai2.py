"""The simulator's model of the Tactical Mind (AI-2, 2026-11-20).

difficulty_sim.py has no map, so the mind's moves (holding a corridor's
mouth, waiting for friends, coming round, the dark edge, a captain's orders,
the feint) cannot run there. tools/balance/tactics_scenarios.py runs them on
seeded hand-made floors with the REAL Monster.take_turn and measures what
they are worth; the numbers below are its measure, fed in here. Each knob
defaults on (merged into difficulty_sim.KNOB_DEFAULTS); 0 is its ablation:

  tac_mind   a creature with a mind (data/minds.json), in a fight of two or
             more, lands MIND_BLOWS times the blows on the hero per creature
             slain that it would without one (an extra blow, now and then,
             after its own): the shooters pelt a hero while the front holds
             the mouth, the band comes up together, the captain's guards
             close when the fight is joined. Its caution costs it some blows
             (waiting, holding, stepping out of the light), already netted.
  tac_lanes  an archer (the ranged AI) that steps aside for a lane and back
             from a hero who closes costs the mastery hero LANE_CLOSING times
             the turns spent closing on it (RANGED_KITE_PROB, for that kind).

Not modelled: the focus on a hurt pet (the simulator's pet has no health),
the habits (their weights change the same moves, already in the measure on
a floor's second fight), the snares (no traps in a simulated fight).
"""
from __future__ import annotations

import random

import lanes
import packs
import tactical_mind

KNOBS = {
    'tac_mind': 1,
    'tac_lanes': 1,
}
# tools/balance/tactics_scenarios.py, 20 seeds a scene (2026-11-20, after the
# audit's fixes): blows on the hero per creature slain, mind on / off, the
# mean over its scenes. (The fixes made the creatures with no mind fight
# straighter, a hunter that sees the hero no longer stepping in and out of a
# blocked line, so the gap the mind makes grew: most in the strung-out
# scene, where a band's shooter pelts a hero while the rest come up.)
MIND_BLOWS = {'cunning': 1.37, 'soldier': 1.16, 'trickster': 1.06, 'caster': 1.01}
# The same harness: hero turns spent closing on an archer, lanes on / off
# (7.74 / 5.11).
LANE_CLOSING = 1.51


def apply_flags(knobs: dict) -> None:
    """The game modules' own switches, for this cell (run_cell)."""
    tactical_mind.ENABLED = bool(knobs.get('tac_mind', 1))
    lanes.ENABLED = bool(knobs.get('tac_lanes', 1))


def fight_start(run, group) -> None:
    """Before the first blow: which of the group think (a fight of two or
    more; never a pack's member, a named foe or anything the mind leaves
    alone)."""
    on = bool(run.knobs.get('tac_mind', 1)) and len(group) >= 2
    for m in group:
        mind = None
        if on and not tactical_mind.excluded(m) and not packs.in_pack(m):
            mind = tactical_mind.mind_of(m)
        m._sim_mind = mind
        if mind:
            run.fs['ai2_thinkers'] = run.fs.get('ai2_thinkers', 0) + 1


def extra_blow(run, m) -> bool:
    """After its blow: one more, at its mind's measured rate."""
    mind = getattr(m, '__dict__', {}).get('_sim_mind')
    if not mind or not m.alive or run.p.hp <= 0:
        return False
    rate = float(MIND_BLOWS.get(mind, 1.0))
    if rate > 1.0 and random.random() < rate - 1.0:
        run.fs['ai2_extra'] = run.fs.get('ai2_extra', 0) + 1
        return True
    return False


def kite_prob(run, target, base: float) -> float:
    """The chance the hero's action goes on closing on an archer."""
    if run.knobs.get('tac_lanes', 1) and getattr(target, 'ai_pattern', '') == 'ranged':
        return min(0.9, base * LANE_CLOSING)
    return base
