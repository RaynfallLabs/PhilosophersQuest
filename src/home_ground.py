"""Home Ground: a creature that keeps to its own ground, and will not run
from it (monster behaviour, third wave: AI-3, lair_and_hoard, 2026-11-20).

Karr the Old in his mound with his gold (Grettis saga), the troll under the
bridge, Fafnir on Gnitaheath, the wights in their barrows: a kind with
``territorial: true`` (data/monsters.json; ``lair_radius``, 8 by default)
has a home, the spot it was set down on when the floor was made
(senses.assign_jobs: ``_home``).

* It will not follow the hero far from it: once he is more than
  lair_radius + 2 tiles from its home, it lets him go and walks back
  (once a floor: "The Draugr stops at the edge of its mound and watches
  you go."). It keeps watching: when he comes back within lair_radius it
  knows him again. (The two tiles between are so a hero in a doorway at
  the edge does not set it off and on every turn.)
* On its own ground it never breaks (morale: 'never'). Away from it, it is
  what its nature says.

A creature with no home (summoned, split, a war-band's, or one saved before
the floor gave it one) is never leashed. Named foes keep their own floors;
pack and band hunters keep to their pack. Pure module: Monster._spots_player
asks leash(); morale.nature asks on_home().
"""
from __future__ import annotations

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_lair knob


def rules() -> dict:
    return kind_data.rules('home_ground')


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def radius(m) -> int:
    return max(2, int(kind_data.field(m, 'lair_radius', rules().get('lair_radius', 8)) or 8))


def home(m):
    h = m.__dict__.get('_home')
    if isinstance(h, (tuple, list)) and len(h) == 2:
        return (int(h[0]), int(h[1]))
    return None


def territorial(m) -> bool:
    """It keeps to its own ground (and has one)."""
    if not ENABLED or not kind_data.field(m, 'territorial', False):
        return False
    if kind_data.named(m) or kind_data.outside_rules(m):
        return False
    d = m.__dict__
    if d.get('_band') is not None or d.get('_job_fixed') or d.get('_summoned_by') is not None:
        return False
    if d.get('_is_summoned'):
        return False
    return home(m) is not None


def on_home(m) -> bool:
    """It stands on its own ground now (morale: it will not run)."""
    if not territorial(m):
        return False
    hx, hy = home(m)
    return _cheb(m.x, m.y, hx, hy) <= radius(m)


def leash(m, player, dungeon, all_monsters, extra_occupied, seen: bool) -> bool:
    """Monster._spots_player's answer after the senses' (``seen``): False
    when it lets the hero go and walks home instead."""
    if not territorial(m):
        return seen
    hx, hy = home(m)
    hero_off = _cheb(player.x, player.y, hx, hy)
    d = m.__dict__
    if d.get('_leashed'):
        if hero_off <= radius(m):
            d.pop('_leashed', None)       # he is back on its ground: it knows him
            return seen
    elif hero_off <= radius(m) + int(rules().get('slack', 2)):
        return seen
    # He has left its ground: it lets him go.
    first = not d.get('_leashed')
    m._leashed = True
    m._tracking = False
    m._goal = None
    m._searching = False
    m._path = None
    if first and ai_lines.once(m, 'lair_edge'):
        r = rules()
        ai_lines.say(m, ai_lines.fill(m, kind_data.field(m, 'lair_line', '') or r.get('line', '')),
                     r.get('line_unseen', ''), 'info')
    if (m.x, m.y) != (hx, hy):
        import senses
        senses.step_toward(m, dungeon, (hx, hy), all_monsters, extra_occupied, player)
    return False


def tell_keys(m) -> list:
    return ['territorial'] if kind_data.field(m, 'territorial', False) else []
