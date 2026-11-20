"""Summoners call when it counts (AI-1, fix_summoner, 2026-11-19).

A summoner's timer used to run before it had seen the hero, so its first
summons came the moment he walked into sight; it called whatever the
range, the sight line or the need, and its cap counted every minion it had
ever made, not the ones still standing.

Now (one step a turn, step()):
  * its timer runs only while it hunts the hero (the caller asks);
  * when the timer is up it calls only if the hero is within reach (8 tiles)
    and in its sight, and fewer than summon_live_cap (2) of its summoned
    still stand; summon_max stays the most it ever calls;
  * the call is a chant drawn up for one turn first ("The Skeleton
    Necromancer raises his staff and begins to chant."), and a blow that
    lands on it in that turn breaks the chant (spoil(), from
    Monster.take_damage): the call is spent and its timer starts again;
  * the chant done, the game sets the summons down (_wants_summon,
    Game._spawn_summoner_minion, which marks each one _summoned_by).

The named foes keep their own timers (Tiamat and Asmodeus); a mini-boss of
the summoner pattern chants like any other. Pure module; the simulator
runs the same step.
"""
from __future__ import annotations

import ai_lines
import kind_data

ENABLED = True      # the simulator's ai_summon knob: 0 = the sim calls no summons


def rules() -> dict:
    return kind_data.rules('summoner')


def live_cap(m) -> int:
    return int(kind_data.field(m, 'summon_live_cap', rules().get('live_cap', 2)) or 2)


def live_summons(m, monsters) -> int:
    return sum(1 for o in monsters or ()
               if getattr(o, 'alive', False) and o.__dict__.get('_summoned_by') is m)


def can_call(m, player, monsters, dungeon=None) -> bool:
    if not getattr(m, 'summon_kind', None):
        return False
    if int(getattr(m, '_summons_made', 0) or 0) >= int(getattr(m, 'summon_max', 4) or 0):
        return False
    if live_summons(m, monsters) >= live_cap(m):
        return False
    reach = int(rules().get('reach', 8))
    if max(abs(m.x - player.x), abs(m.y - player.y)) > reach:
        return False
    if dungeon is not None and not m._has_los(player.x, player.y, dungeon):
        return False
    return True


def step(m, player, monsters, dungeon=None) -> str:
    """One turn of its calling, while it hunts the hero: 'chant' (it begins:
    its turn is spent), 'call' (the chant is done: the game sets the
    summons down this turn; its turn is spent), '' (nothing: it fights)."""
    m._wants_summon = False
    try:
        import attack_gates
        if not attack_gates.may_summon(m):        # silenced: no chant, no call
            m.__dict__.pop('_chanting', None)
            return ''
    except ImportError:
        pass
    if m.__dict__.get('_chanting'):
        m._chanting = False
        if not can_call(m, player, monsters, None):
            return ''
        m._wants_summon = True
        m._summons_made = int(getattr(m, '_summons_made', 0) or 0) + 1
        m._summon_turn_counter = 0
        return 'call'
    m._summon_turn_counter = int(getattr(m, '_summon_turn_counter', 0) or 0) + 1
    if m._summon_turn_counter < int(getattr(m, 'summon_cooldown', 5) or 1):
        return ''
    if not can_call(m, player, monsters, dungeon):
        return ''
    m._chanting = True
    r = rules()
    ai_lines.say(m, ai_lines.fill(m, r.get('chant_line', '')), r.get('chant_unseen', ''))
    return 'chant'


def spoil(m) -> bool:
    """A blow landed on it while it chants: the chant breaks. True if it
    did. The call is spent, so its timer starts again."""
    if not m.__dict__.get('_chanting'):
        return False
    m._chanting = False
    m._summon_turn_counter = 0
    m._wants_summon = False
    ai_lines.say(m, ai_lines.fill(m, rules().get('spoil_line', '')), '', 'success')
    return True
