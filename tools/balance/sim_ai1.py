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
  ai_rot     Grave Rot (src/grave_rot.py): a disease lasts as its kind's lore
             says (disease_linger), no regen in a fight while it lasts (regen_ok), heals
             halved (the real Player.restore_hp); Mercy at chain 4 cures it.
             Between fights the simulator lets debuffs run out for free (its
             own rule), so the lost rest is under-counted.
  ai_light   Light-Shy (src/light_shy.py): the mastery hero (tactics=1)
             facing a troll (a light-shy kind that regenerates, where the
             lore makes the light decisive) spends his first action raising
             a carried light (glare 1: fight_start, _sim_glare); in it the
             troll needs +2 to hit (real _resolve_blow) and cannot mend
             (world_tick). The other light-shy kinds (kobolds, drow,
             shadows) meet an unlit hero in the simulator, and the Light
             spell's stiffening is not modelled: the simulator values the
             light less than a kid who carries one would get. The shield a
             carried light costs is not modelled either.
  ai_vanish  Gone Again (src/gone_again.py): the simulator's hit-and-run
             model (gone for 9-12 turns) is now right for every kind. Off:
             the old game, where a non-phasing hider stood in plain sight
             and took the hero's blows (visible_away).
  ai_alarm   Raise the Alarm (src/alarm.py): a room group with a lookout
             brings the next room's group in ALARM_JOIN of the time (the
             mastery hero kills or slips past the lookout first half the
             time) instead of NEIGHBOUR_JOIN_PROB (join_prob).
  ai_throes  Death Throes (src/death_throes.py): a bursting kind that dies
             blasts the hero beside it (the mastery hero reads the swell
             and steps back THROES_READ of the time; the lost step is not
             counted) and the creatures beside it (leavers).
  ai_relurk  Back to the Web (src/relurk.py): a relurking kind that bolted
             comes back later in the floor as an ambusher (one more free
             blow) instead of being found and finished.
  ai_shove   Shove (src/shove.py): a shove costs the hero his next action
             (stepping back in: lost_action). Hazards it might throw him
             into are not modelled.

What the simulator cannot see is said where it matters (the report).
"""
from __future__ import annotations

import random

import alarm
import breath
import death_throes
import faction
import gone_again
import grave_rot
import kind_data
import life_drain
import light_shy
import morale
import relurk
import shove
import summoning

KNOBS = {
    'ai_heal': 1,
    'ai_summon': 1,
    'ai_breath': 1,
    'ai_morale': 1,
    'ai_drain': 1,
    'ai_rot': 1,
    'ai_light': 1,
    'ai_vanish': 1,
    'ai_alarm': 1,
    'ai_throes': 1,
    'ai_relurk': 1,
    'ai_shove': 1,
}
ALARM_JOIN = 0.6          # the next room's group comes when a lookout shouts
THROES_READ = 0.6         # the mastery hero steps back from a swelling creature
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
    grave_rot.ENABLED = bool(knobs.get('ai_rot', 1))
    light_shy.ENABLED = bool(knobs.get('ai_light', 1))
    gone_again.ENABLED = bool(knobs.get('ai_vanish', 1))
    alarm.ENABLED = bool(knobs.get('ai_alarm', 1))
    death_throes.ENABLED = bool(knobs.get('ai_throes', 1))
    relurk.ENABLED = bool(knobs.get('ai_relurk', 1))
    shove.ENABLED = bool(knobs.get('ai_shove', 1))
    if not getattr(light_shy.glare, '_sim', False):
        light_shy.glare = _sim_glare


_real_glare = light_shy.glare


def _sim_glare(player) -> int:
    """The simulator's hero holds no light item (his off hand keeps its
    shield); the light he raises against a troll is a carried light's
    glare (fight_start)."""
    return max(_real_glare(player), 1 if getattr(player, '_sim_torch', False) else 0)


_sim_glare._sim = True


def fight_start(run, group) -> None:
    """Before the first blow: the mastery hero raises a light against a
    light-shy foe (one action)."""
    k = run.knobs
    p = run.p
    trolls = (k.get('ai_light', 1) and k.get('tactics')
              and any(light_shy.shy(m) and int(getattr(m, 'regeneration', 0) or 0) > 0
                      for m in group))
    if trolls and not getattr(p, '_sim_torch', False):
        run._ai1_skip = int(getattr(run, '_ai1_skip', 0) or 0) + 1   # raising it
        run.fs['ai_lit'] = run.fs.get('ai_lit', 0) + 1
    p._sim_torch = bool(trolls)


def lost_action(run) -> bool:
    """The hero's action this turn is spent (raising a light, stepping back
    in after a shove)."""
    n = int(getattr(run, '_ai1_skip', 0) or 0)
    if n > 0:
        run._ai1_skip = n - 1
        return True
    return False


def world_tick(run, active) -> None:
    """After the statuses tick: a troll in the light cannot mend; a shove
    this turn costs the hero his next action."""
    p = run.p
    for m in active:
        if m.alive:
            light_shy.light_turn(m, p)
            m.__dict__.pop('_ai_lines', None)
    if p.__dict__.pop('_pending_shove', None) is not None:
        run._ai1_skip = int(getattr(run, '_ai1_skip', 0) or 0) + 1
        run.fs['ai_shoves'] = run.fs.get('ai_shoves', 0) + 1


def regen_ok(run) -> bool:
    return not grave_rot.blocks_regen(run.p)


def visible_away(run, m) -> bool:
    """ai_vanish=0: a non-phasing hit-and-run creature 'hides' in plain
    sight, where the hero can still strike it (the old game)."""
    return bool(not run.knobs.get('ai_vanish', 1) and m.ai_pattern == 'hit_and_run'
                and not getattr(m, 'can_phase_walls', False))


def join_prob(run, group, base: float) -> float:
    if not run.knobs.get('ai_alarm', 1) or not any(alarm.spec(m) for m in group):
        return base
    p = ALARM_JOIN
    if run.knobs.get('tactics'):
        p = 0.5 * ALARM_JOIN + 0.5 * base
    run.fs['ai_alarm_groups'] = run.fs.get('ai_alarm_groups', 0) + 1
    return max(base, p)


def _throes(run, active) -> None:
    """Those that died this turn and burst."""
    from floor_curve import wound
    from status_effects import apply_debuff_with_save
    p = run.p
    while True:
        bursting = [m for m in active if not m.alive and death_throes.should_burst(m)]
        if not bursting:
            return
        for m in bursting:
            m._throes_done = True
            t = death_throes.spec(m) or {}
            share = float(t.get('share', 0) or 0)
            kind = str(t.get('type', 'fire') or 'fire')
            run.fs['ai_throes'] = run.fs.get('ai_throes', 0) + 1
            if not (run.knobs.get('tactics') and random.random() < THROES_READ):
                if share > 0:
                    p.take_damage(wound(share, p.max_hp), kind)
                if t.get('effect') and p.hp > 0:
                    dc = min(18, 12 + int(getattr(m, 'min_level', 1) or 1) // 7)
                    apply_debuff_with_save(p, t['effect'], int(t.get('effect_duration', 3) or 3),
                                           dc, source=m)
            for o in active:
                if o is m or not o.alive:
                    continue
                o.take_damage(wound(share, o.max_hp, o._is_named_foe()), kind)


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
            run.fs['ai_broke_' + st] = run.fs.get('ai_broke_' + st, 0) + 1
            queue = getattr(run, '_ai1_queue', None) or []
            if st in ('regroup', 'yield') and any(faction.same_side(m, o) for o in queue):
                m._sim_left = 'regroup'
            elif st == 'yield' and random.random() < 0.5:
                morale.give_up(m)               # caught with no friend to run to
                m._sim_left = 'yield'
        if morale.style(m) == 'withdraw' and random.random() < morale.withdraw_strikes():
            return None                         # a fighting withdrawal: it strikes
        return False
    return None


def leavers(run, active, queue) -> tuple:
    """Those who left the fight this turn (fight loop): a bolted beast is
    gone (found again later BOLT_FOUND_AGAIN of the time, and finished); a
    regrouper goes back to the queue behind the next of its side; one that
    yielded is spared."""
    run._ai1_queue = queue
    if run.knobs.get('ai_throes', 1):
        _throes(run, active)
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
            if run.knobs.get('ai_relurk', 1) and kind_data.field(m, 'relurks', False):
                # Back to the web: it drops on him again later (one free blow).
                m.__dict__.pop('_cowed', None)
                m._flee_timer = 0
                m.ai_pattern = 'ambush'
                queue = queue + [m]
                run.fs['ai_relurks'] = run.fs.get('ai_relurks', 0) + 1
            elif random.random() < BOLT_FOUND_AGAIN:
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
