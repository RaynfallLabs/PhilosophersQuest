"""What the third wave of monster behaviour adds to one monster turn (AI-3,
2026-11-20). Two hooks, so Monster.take_turn and Monster.attack stay as
they were:

  turn(m, player, dungeon, monsters, extra_occupied)
        in Monster.take_turn, after the gates every creature obeys (asleep,
        held, slowed, its morale's check, fear, charm, confusion's stumble)
        and before the pattern's own move. In order:
          Held Fast (holds.py)          a holder squeezes, digests or drags;
          Uses What It Carries          a hurt one drinks, one with a fire
            (monster_kit.py)            pot and a clear throw throws it;
          Skittish (skittish.py)        a coward keeps its distance, darts
                                        in, offers its purse when cornered;
          The Caster's Book             a caster wards, curses, mends,
            (caster_ai.py)              blinks, dispels or darkens by need.
        True: it attacks (Monster.attack resolves the blow chosen); False:
        its turn is spent; None: the pattern goes on.
  blow(m, player)
        in Monster.attack, first: the squeeze, or the blow a behaviour
        chose this turn (a spell, a thrown pot), or None.

Never for the allied, the encounter people, the unicorn, Death or the
stalker (kind_data.outside_rules); each behaviour also keeps named foes to
their own fights. Pure module.
"""
from __future__ import annotations

import kind_data


def turn(m, player, dungeon, monsters, extra_occupied=None):
    if kind_data.outside_rules(m) or m.__dict__.get('_yielded'):
        return None                       # (one that yielded never strikes again: morale.py)
    m.__dict__.pop('_chosen_blow', None)  # a blow chosen and never struck is stale
    m.__dict__.pop('_squeeze_now', None)
    import holds
    got = holds.holder_turn(m, player, dungeon, monsters, extra_occupied)
    if got is not None:
        return got
    import monster_kit
    got = monster_kit.turn(m, player, dungeon, monsters, extra_occupied)
    if got is not None:
        return got
    import skittish
    got = skittish.turn(m, player, dungeon, monsters, extra_occupied)
    if got is not None:
        return got
    if int(getattr(m, '_flee_timer', 0) or 0) > 0:
        return None                       # a broken creature follows its morale
    import caster_ai
    return caster_ai.turn(m, player, dungeon, monsters, extra_occupied)


def blow(m, player):
    """(damage, line) for the blow this turn's behaviour chose, or None.

    A lurker's surprise (src/surprise.py) is its FIRST blow, landed or not:
    a drop that misses is spent, so 'drops on you from hiding' is never said
    of a blow turns later."""
    if m.__dict__.get('_mimic_surprise'):
        if m.__dict__.get('_surprise_tried'):
            m._mimic_surprise = False
        m._surprise_tried = True
    import holds
    got = holds.blow(m, player)
    if got is not None:
        return got
    atk = m.__dict__.pop('_chosen_blow', None)
    if atk is not None:
        # A spell or a thrown pot from afar is no charge: the bull's run is
        # kept for its next blow (Monster.can_charge).
        charge = m.__dict__.pop('_charge_ready', None) if atk.get('ranged') else None
        try:
            return m._resolve_blow(atk, player)
        finally:
            if charge is not None:
                m._charge_ready = charge
    return None


def pick_attack(m, player, atk, candidates):
    """Monster.attack's random pick from afar, chosen with sense for a
    caster (caster_ai.pick_attack); ``atk`` when it has no better."""
    import caster_ai
    best = caster_ai.pick_attack(m, player, candidates)
    return best if best is not None else atk
