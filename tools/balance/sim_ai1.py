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
  ai_morale  Morale by Nature (src/morale.py): the real checks and styles. A
             creature that breaks runs (no blow; the hero lands one at
             CHASE_HIT_PROB, as for any flight); a withdrawal comes back after
             its turns, never breaking twice for one wound; a bolt leaves the
             fight once its run is spent, and the hero finds it again later
             (and finishes it) BOLT_FOUND_AGAIN of the time; a regroup with
             kin still waiting at the doorway goes back to the queue behind
             the next of them; a yield leaves the fight, spared. Off: the
             old rule (under a quarter, 8 turns, re-armed; nothing over 500
             health ever breaks). Not modelled: at bay (the sim has no walls).
  ai_drain   Life Drained (src/life_drain.py; inside the real _resolve_blow):
             a failed save lowers max HP; half back on each new floor
             (floor_start), all of it from a Mercy prayer at chain 4
             (prayed). Off: the old CON -1 once a floor. The physician's
             Restore is not modelled (the stall's services are its own).

What the simulator cannot see is said where it matters (the report).
"""
from __future__ import annotations

import random

import breath
import faction
import kind_data
import life_drain
import morale
import summoning

KNOBS = {
    'ai_heal': 1,
    'ai_summon': 1,
    'ai_breath': 1,
    'ai_morale': 1,
    'ai_drain': 1,
}
# A beast that bolted (cowed) is met again later on the floor, hurt and
# alone, and finished with one blow this often; else it is never found.
BOLT_FOUND_AGAIN = 0.5

# The melee round the hero in the fight loop (difficulty_sim.fight's slots).
_SLOTS = [(6, 5), (5, 6), (6, 6), (4, 5), (5, 4), (4, 4), (6, 4), (4, 6)]


def apply_flags(knobs: dict) -> None:
    """The game modules' own switches, for this cell (run_cell)."""
    breath.ENABLED = bool(knobs.get('ai_breath', 1))
    summoning.ENABLED = bool(knobs.get('ai_summon', 1))
    morale.ENABLED = bool(knobs.get('ai_morale', 1))
    life_drain.ENABLED = bool(knobs.get('ai_drain', 1))


def floor_start(run) -> None:
    """A new floor down (play_floor, after the stair rest): half the drained
    life comes back."""
    if run.knobs.get('ai_drain', 1):
        back = life_drain.stairs_rest(run.p)
        if back:
            run._healed('stairs', back)


def prayed(run, chain: int) -> None:
    """The Mercy prayer at chain 4 gives back what the dead drained and
    lifts a sickness (game_divine._resolve_simple_prayer)."""
    if chain >= 4:
        if run.knobs.get('ai_drain', 1):
            life_drain.restore(run.p)
        run.p.status_effects.pop('diseased', None)


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


def morale_turn(run, m):
    """Morale by Nature in the melee (monster_acts, where the old flee rule
    was): False when it does not strike this turn (it runs, it has left),
    None to go on."""
    active = m.__dict__.get('_cached_all_monsters') or []
    was = int(getattr(m, '_flee_timer', 0) or 0)
    morale.turn(m, run.p, active)
    d = m.__dict__
    if not morale.ruled(m):
        return None
    if d.get('_yielded') or (d.get('_cowed') and int(m._flee_timer or 0) <= 0):
        m._sim_left = 'yield' if d.get('_yielded') else 'bolt'
        return False
    kin = d.get('_rally_to')
    if kin is not None and kin in active:
        d.pop('_rally_to', None)                 # its friends are in this fight:
        m._flee_timer = 0                        # it is back among them at once
        return None
    if int(m._flee_timer or 0) > 0:
        if was <= 0:
            st = morale.style(m)
            queue = getattr(run, '_ai1_queue', None) or []
            if st in ('regroup', 'yield') and any(faction.same_side(m, o) for o in queue):
                m._sim_left = 'regroup'
            elif st == 'yield' and random.random() < 0.5:
                morale.give_up(m)               # caught with no friend to run to
                m._sim_left = 'yield'
        return False
    return None


def leavers(run, active, queue) -> tuple:
    """Those who left the fight this turn (fight loop): a bolted beast is
    gone (found again later BOLT_FOUND_AGAIN of the time, and finished); a
    regrouper goes back to the queue behind the next of its side; one that
    yielded is spared."""
    run._ai1_queue = queue
    if not any(m.__dict__.get('_sim_left') for m in active):
        return active, queue
    keep = []
    for m in active:
        why = m.__dict__.pop('_sim_left', None)
        if not why or not m.alive:
            keep.append(m)
            continue
        run.fs['ai_left_' + why] = run.fs.get('ai_left_' + why, 0) + 1
        if why == 'bolt':
            if random.random() < BOLT_FOUND_AGAIN:
                m.hp = 0
                m.alive = False                  # finished when found again
        elif why == 'regroup':
            m._flee_timer = 0
            m._rallied = True
            i = next((k for k, o in enumerate(queue) if faction.same_side(m, o)), len(queue))
            queue = queue[:i + 1] + [m] + queue[i + 1:]
    run._ai1_queue = queue
    return keep, queue


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
