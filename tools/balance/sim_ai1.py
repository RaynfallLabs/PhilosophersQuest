"""The simulator's model of monster behaviour, first wave (AI-1, 2026-11-19).

difficulty_sim.py calls in here from a few marked hooks; every behaviour is
the game's own module, run on the simulator's monsters and hero. Each one has
a knob that defaults on (KNOBS, merged into difficulty_sim.KNOB_DEFAULTS), so
`knob=0` is its ablation:

  ai_heal    a healer mends a badly hurt friend (its own side), then rests its
             voice (src/faction.py). Off: the simulator never heals, as before.
  ai_summon  a summoner chants for a turn (a blow on it breaks the chant) and
             calls its dead while fewer than its live cap stand
             (src/summoning.py). Off: no summons, as before.
  ai_breath  a breath must be drawn again (src/breath.py; inside the real
             Monster.attack). Off: the old rule, a breath every turn.

What the simulator cannot see is said where it matters (the report).
"""
from __future__ import annotations

import random

import breath
import faction
import kind_data
import summoning

KNOBS = {
    'ai_heal': 1,
    'ai_summon': 1,
    'ai_breath': 1,
}

# The melee round the hero in the fight loop (difficulty_sim.fight's slots).
_SLOTS = [(6, 5), (5, 6), (6, 6), (4, 5), (5, 4), (4, 4), (6, 4), (4, 6)]


def apply_flags(knobs: dict) -> None:
    """The game modules' own switches, for this cell (run_cell)."""
    breath.ENABLED = bool(knobs.get('ai_breath', 1))
    summoning.ENABLED = bool(knobs.get('ai_summon', 1))


def _named(m) -> bool:
    return kind_data.named(m)


def monster_turn(run, m, fresh_monster):
    """A behaviour that spends the monster's turn (monster_acts, after the
    gates every monster obeys): False when it did (no blow this turn), None
    to go on to the blow."""
    k = run.knobs
    active = m.__dict__.get('_cached_all_monsters') or []
    if k.get('ai_heal', 1) and m.ai_pattern == 'healer':
        target = faction.heal_choice(m, active, run.p, reach=None)
        if target is not None:
            faction.heal(m, target)
            run.fs['ai_heals'] = run.fs.get('ai_heals', 0) + 1
            return False
    if (k.get('ai_summon', 1) and getattr(m, 'summon_kind', None)
            and (m.ai_pattern == 'summoner' or not _named(m))):
        act = summoning.step(m, run.p, active)
        if act == 'call':
            _summon(run, m, active, fresh_monster)
            return False
        if act == 'chant':
            run.fs['ai_chants'] = run.fs.get('ai_chants', 0) + 1
            return False
    return None


def _summon(run, m, active, fresh_monster) -> None:
    """Game._spawn_summoner_minion in the melee: one of its summon kinds,
    aware, joins the fight now (summons ignore the doorway, as locusts do)."""
    m._wants_summon = False
    kinds = m.summon_kind if isinstance(m.summon_kind, (list, tuple)) else [m.summon_kind]
    kind = random.choice(list(kinds))
    defn = kind_data.defs().get(kind)
    if not isinstance(defn, dict):
        return
    from monster import Monster
    minion = fresh_monster(Monster({**defn, 'id': kind}, 0, 0), run.knobs, run.floor)
    minion._is_summoned = True
    minion._summoned_by = m
    minion.x, minion.y = _SLOTS[len(active) % len(_SLOTS)]
    minion._cached_all_monsters = active
    active.append(minion)
    run.fs['ai_summons'] = run.fs.get('ai_summons', 0) + 1
