"""Lurkers Keep Their Promise: an ambusher that was not spotted drops on
the hero with a real surprise blow; one he spotted, or a mimic he knows for
what it is, surprises no one (monster behaviour, third wave: AI-3,
fix_lurkers, 2026-11-20).

The ambush AI used to spring at five steps' walk with a clear view and then
only walk in: unless it had a pounce opener it never got a surprise blow at
all, while the simulator gave every ambusher one. A mimic sprang with its
crushing first bite (x1.75) on ANY hero beside it, even one who had studied
the kind. Now:

* An ambusher springs when the hero comes within spring_reach (2: a drop
  from above, a lunge from the reeds) with nothing between them, and its
  first blow that lands is a surprise (the same x1.75 the mimic's is).
* One the hero spotted first (his keen senses, a family's sense of the
  hidden, Hecate's Torch: Game._do_passive_ambush_detection) springs with
  no surprise. A hero who knows the family's ambushers is never caught
  (family_edges no_ambush, as before).
* A mimic of a kind the hero knows (studied, or its page read) springs with
  no surprise: he saw the hinges breathe.

Named foes keep their own ways; a lurker sprung by a blow (spring()) never
surprises. Pure module: Monster.take_turn's ambush branch and _mimic_turn
ask here; the simulator agrees (tools/balance/sim_ai3.py).
"""
from __future__ import annotations

import kind_data

ENABLED = True          # the simulator's ai3_lurk knob


def rules() -> dict:
    return kind_data.rules('surprise')


def spring_reach() -> int:
    return int(rules().get('spring_reach', 2) or 2)


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def ambush_step(m, player, dungeon) -> str:
    """'lurk' (it waits unseen), 'spring' (it drops on him: a surprise
    blow), or 'aware' (he spotted it first: it comes on, no surprise)."""
    if getattr(m, '_aware', False):
        return 'aware'
    d = _cheb(m.x, m.y, player.x, player.y)
    reach = spring_reach() if ENABLED else 5
    if not ENABLED:
        d = abs(m.x - player.x) + abs(m.y - player.y)      # the old five steps' walk
    if d > reach:
        return 'lurk'
    if not m._adjacent_to(player):
        import senses
        if not senses.clear_view(m.x, m.y, player.x, player.y, dungeon):
            return 'lurk'
        # On a hero it can see or touch (docs: never one its senses miss:
        # an invisible hero standing still, one a ward hides from its kind).
        # It sprang on him whether it sensed him or not.
        if senses.perceive(m, player, dungeon) is None:
            return 'lurk'
    return 'spring'


def strike_line(m) -> str:
    """The words before a surprise blow: a mimic erupts from its disguise,
    an ambusher drops on the hero."""
    from monster import the_name, pronouns
    if getattr(m, 'disguise', None):
        return f"{the_name(m)} ERUPTS from {pronouns(m)[2]} disguise! "
    return f"{the_name(m)} drops on you from hiding! "


def surprises(m, player) -> bool:
    """Its first blow is a surprise: the hero did not know it was there,
    nor knows the kind for what it is."""
    if not ENABLED or kind_data.named(m):
        return False
    if m.__dict__.get('_relurked'):
        return False                      # back in its web: no second surprise (relurk.py)
    if getattr(m, 'ai_pattern', '') == 'mimic' or m.__dict__.get('disguise'):
        try:
            import family_lore
            if family_lore.knowledge(player, getattr(m, 'kind', '')) >= family_lore.KNOWN:
                return False
        except ImportError:
            pass
    return True
