"""The simulator's model of monster behaviour, third wave (AI-3, 2026-11-20).

difficulty_sim.py calls in here from a few marked hooks; every behaviour is
the game's own module, run on the simulator's monsters and hero. Each one has
a knob that defaults on (KNOBS, merged into difficulty_sim.KNOB_DEFAULTS), so
`knob=0` is its ablation:

  ai3_caster  The Caster's Book (src/caster_ai.py): a caster in the melee
              casts from its book by need (the real choose(); every foe is in
              sight). A ward halves the hero's blows (the real damage_ward in
              combat.strike_damage); a curse goes through the real rider road
              (apply_debuff_with_save); a dispel takes a spell off him; a
              blink puts the caster a pace off (the hero spends an action
              closing). A chant is broken by the hero's blow on the caster
              (the real Monster.take_damage), and the prepared hero (tactics)
              strikes a chanting caster first. Off: the old random pick.
  ai3_hold    Held Fast (src/holds.py): the real hold starts on the blow
              (ai_blow), the holder's turn is its squeeze (no roll to hit), a
              swallowed hero is out of the others' reach, and the held hero
              strikes the holder (his only way out in the melee); a hard
              enough blow breaks it (the real note_hurt). The drag to water is
              not modelled (the simulator has no map). Off: no holds.
  ai3_aura    Auras (src/auras.py): the real pulse each world turn (the hero
              sees every foe in the melee).
  ai3_lair    Home Ground (src/home_ground.py): a territorial foe on its
              ground never breaks (the real morale), and a fight with only
              territorial foes is fled as from slow ones (they stop at the
              edge of their ground).
  ai3_kit     Uses What It Carries (src/monster_kit.py): the real kit rolled
              and spent: a hurt one drinks with its turn; a fire pot is thrown
              as the foe comes in (one free ranged blow); what it did not use
              is the hero's when it dies (the real loot path: consider()).
  ai3_lurk    Lurkers Keep Their Promise (src/surprise.py): an ambusher or a
              mimic gets its free blow on entry only when the hero did not
              spot it first (his PER over the three turns it waits, a family's
              no_ambush always; a mimic of a known kind never), and that blow
              is a surprise (x1.75, the real _resolve_blow). Off: the old free
              blow for every lurker, with no surprise.
  ai3_coward  Skittish (src/skittish.py): a cornered leprechaun offers its
              purse; the hero takes it half the time (the fight ends, the gold
              is his). Otherwise the old 30% blow.
  ai3_shape   Second Shape (src/second_shape.py): the enrage takes the form.

Not modelled: the dancer's footwork (positions), the drag, the lair's walk
home, the darkness spell beyond its line (the simulator's hero carries no
light but the troll's).
"""
from __future__ import annotations

import random

import auras
import caster_ai
import holds
import home_ground
import kind_data
import monster_kit
import second_shape
import skittish
import surprise

KNOBS = {
    'ai3_caster': 1,
    'ai3_hold': 1,
    'ai3_aura': 1,
    'ai3_lair': 1,
    'ai3_kit': 1,
    'ai3_lurk': 1,
    'ai3_coward': 1,
    'ai3_shape': 1,
}
BARGAIN_TAKEN = 0.5        # the hero takes a cornered leprechaun's purse this often
LURK_WAIT_TURNS = 3        # turns a lurker lies in reach of the hero's eye before it springs


def apply_flags(knobs: dict) -> None:
    """The game modules' own switches, for this cell (run_cell)."""
    caster_ai.ENABLED = bool(knobs.get('ai3_caster', 1))
    holds.ENABLED = bool(knobs.get('ai3_hold', 1))
    auras.ENABLED = bool(knobs.get('ai3_aura', 1))
    home_ground.ENABLED = bool(knobs.get('ai3_lair', 1))
    monster_kit.ENABLED = bool(knobs.get('ai3_kit', 1))
    surprise.ENABLED = bool(knobs.get('ai3_lurk', 1))
    skittish.ENABLED = bool(knobs.get('ai3_coward', 1))
    second_shape.ENABLED = bool(knobs.get('ai3_shape', 1))


def _fs(run, key, n=1):
    run.fs[key] = run.fs.get(key, 0) + n


def _spot_chance(p) -> float:
    """Game._do_passive_ambush_detection: 5% + 1.5% a point of PER, a turn."""
    return 0.05 + int(getattr(p, 'PER', 10) or 10) * 0.015


def enter(run, m, free: int) -> int:
    """A foe joins the melee (difficulty_sim fight.enter): its free blows."""
    k = run.knobs
    p = run.p
    pat = getattr(m, 'ai_pattern', '')
    if home_ground.ENABLED and kind_data.field(m, 'territorial', False):
        m._home = (m.x, m.y)                  # it fights on its own ground
    if k.get('ai3_lurk', 1) and pat in ('ambush', 'mimic'):
        spotted = False
        try:
            import family_edges
            spotted = family_edges.no_ambush_ability(p, m) is not None
        except (ImportError, AttributeError):
            spotted = False
        if pat == 'ambush' and not spotted:
            spotted = random.random() < 1.0 - (1.0 - _spot_chance(p)) ** LURK_WAIT_TURNS
        if pat == 'mimic' and not surprise.surprises(m, p):
            spotted = True
        fast = m.speed >= 14
        if spotted:
            _fs(run, 'ai3_lurkers_spotted')
            free = 1 if fast else 0
        else:
            _fs(run, 'ai3_lurkers_sprang')
            m._mimic_surprise = surprise.surprises(m, p)   # none on a relurked one
            free = max(free, 1)
    if k.get('ai3_kit', 1) and p.hp > 0 and m.alive:
        m._tracking = True
        ax, ay = m.x, m.y
        m.x, m.y = 9, 5                       # four tiles off, as it comes in
        try:
            if monster_kit.turn(m, p, None, [m], None) is True:
                _fs(run, 'ai3_pots_thrown')
                run._monster_attack(m)
        finally:
            m.x, m.y = ax, ay
    return free


def target(run, reachable: list, chosen):
    """The hero's foe this action: the one that holds him; for the prepared
    hero (tactics) a caster drawing up a spell."""
    if not reachable:
        return chosen
    h = holds.holder(run.p, reachable)
    if h is not None:
        return h
    if run.knobs.get('tactics'):
        chanting = [m for m in reachable if m.__dict__.get('_casting')]
        if chanting:
            return chanting[0]
    return chosen


def lets_go(active: list) -> bool:
    """Every foe here keeps to its own ground: it stops at the edge."""
    return bool(active) and home_ground.ENABLED and all(
        kind_data.field(m, 'territorial', False) and not kind_data.named(m) for m in active)


def world_tick(run, active: list) -> None:
    """Before the foes act: a hold that no longer stands ends; the auras."""
    p = run.p
    if p.__dict__.get('_held') is not None:
        holds.validate(p, active)
    if run.knobs.get('ai3_aura', 1):
        auras.pulse(active, p, None)
    for m in active:
        m.__dict__.pop('_ai_lines', None)


def lost_action(run) -> bool:
    n = int(getattr(run, '_ai3_skip', 0) or 0)
    if n > 0:
        run._ai3_skip = n - 1
        return True
    return False


def monster_turn(run, m):
    """monster_acts, after the gates: True (it strikes: its squeeze or the
    blow its behaviour chose), False (its turn went on a spell, a potion, a
    chant; or it cannot reach a swallowed hero), None (go on)."""
    p = run.p
    active = m.__dict__.get('_cached_all_monsters') or []
    if kind_data.outside_rules(m) or m.__dict__.get('_yielded'):
        return None
    if holds.shields(p, m):
        return False
    m.__dict__.pop('_chosen_blow', None)
    if run.knobs.get('ai3_hold', 1):
        got = holds.holder_turn(m, p, None, active, None)
        if got is not None:
            _fs(run, 'ai3_squeezes')
            return got
    if run.knobs.get('ai3_kit', 1):
        m._tracking = True
        got = monster_kit.turn(m, p, None, active, None)
        if got is False:
            _fs(run, 'ai3_drinks')
            return False
        m.__dict__.pop('_chosen_blow', None)    # no throws in the melee
    if run.knobs.get('ai3_coward', 1) and skittish.bargain(m) and getattr(m, 'ai_pattern', '') == 'cowardly':
        if not m.__dict__.get('_bargained') and not m.__dict__.get('_bargain_refused'):
            if random.random() < BARGAIN_TAKEN:
                gold = skittish.offer_gold(m, random)
                skittish.accept(m)
                run.gold = int(getattr(run, 'gold', 0) or 0) + gold
                _fs(run, 'ai3_bargains')
                m._sim_left = 'yield'            # gone from the fight, spared (sim_ai1.leavers)
                return False
            skittish.refuse(m)
    if int(getattr(m, '_flee_timer', 0) or 0) > 0:
        return None
    if run.knobs.get('ai3_caster', 1) and caster_ai.book(m):
        m._tracking = True
        before = dict(m.__dict__.get('_spells_cast') or {})
        chanting = bool(m.__dict__.get('_casting'))
        got = caster_ai.turn(m, p, None, active, None)
        after = dict(m.__dict__.get('_spells_cast') or {})
        if after.get('escape', 0) > before.get('escape', 0):
            run._ai3_skip = int(getattr(run, '_ai3_skip', 0) or 0) + 1   # closing on it again
        if got is not None:
            _fs(run, 'ai3_chants' if (m.__dict__.get('_casting') and not chanting) else 'ai3_casts')
            return got
    return None


def enraged(m) -> None:
    """The simulator's one-way enrage (monster_acts): the second shape."""
    second_shape.apply(m)


def kit_loot(run, m) -> None:
    """A foe that died: what it did not use of its kit is the hero's."""
    if not run.knobs.get('ai3_kit', 1) or m.alive:
        return
    for it in monster_kit.leftovers(m):
        _fs(run, 'ai3_kit_looted')
        run.consider(it)
