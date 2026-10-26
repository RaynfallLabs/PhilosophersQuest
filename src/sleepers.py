"""Deep sleepers, and what stirs them (Brandon, 2026-10-26).

The creatures of a zoo, a graveyard and a barracks are laid down in a deep
sleep (``DEEP_SLEEP`` in main.py) and used to sleep until struck, whatever the
hero did beside them: a zoo was free gold. Now each one stirs by chance.

* **Footsteps:** a step inside the room may wake a sleeper close by.
* **Taking gold:** in *Beowulf* a thief took one cup from a sleeping dragon's
  hoard, and the dragon woke. A gold pile picked up in the room may wake
  sleepers within reach. This is the real risk in a zoo.

What changes the odds, all things the game already has: Dexterity (light
feet); A Cat's Footfall (the boon of Fenrir: in the myth, a cat's footfall is
one of the six things that make no sound) silences footsteps; a ring of silent
walking (the Ring of the Assassin) silences footsteps too; the Hand of Glory
(the housebreaker's charm that keeps a house asleep) keeps every sleeper
asleep; a Burdened pack clinks; Aggravated wakes the whole room on sight.

Pure module: no pygame and no Game import. The Game side is in
``EncountersMixin`` (``_sleepers_stir``).
"""
from __future__ import annotations

import random

# The rooms whose sleepers stir, and how readily. ``step`` is the chance per
# step, per sleeper within ``step_reach`` tiles; ``take`` the chance per gold
# pile taken, per sleeper within ``take_reach`` tiles (simulated on a typical
# 7x5 zoo of 4-8 sleepers: at DEX 10 a hero is still unseen after one pile 80%
# of the time, after three about half, and empties the room about 1 in 100).
RULES: dict[str, dict] = {
    'zoo':       {'step': 0.02, 'step_reach': 2, 'take': 0.06, 'take_reach': 3},
    'graveyard': {'step': 0.02, 'step_reach': 2, 'take': 0.06, 'take_reach': 3},
    'barracks':  {'step': 0.03, 'step_reach': 2, 'take': 0.06, 'take_reach': 3},
}

DEEP = 1000                 # a sleep at least this long is a deep sleeper's
DEX_STEP = 0.03             # each point of DEX over 10 lowers the chance this much
DEX_FLOOR = 0.5             # ...down to half at most
BURDENED = 2.0              # a heavy pack clinks
CATS_FOOTFALL = 'cats_footfall'
HAND_OF_GLORY = 'hand_of_glory'


def room_at(dungeon, x: int, y: int):
    """(room, room type) of the stirring room the tile (x, y) is in, or
    (None, None)."""
    special = getattr(dungeon, 'special_rooms', None) or {}
    for room in getattr(dungeon, 'rooms', None) or ():
        rtype = special.get(tuple(room.center))
        if rtype in RULES and room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
            return room, rtype
    return None, None


def in_room(room, x: int, y: int) -> bool:
    return room.x <= x < room.x + room.width and room.y <= y < room.y + room.height


def is_deep_sleeper(m) -> bool:
    try:
        return bool(getattr(m, 'alive', True)) and int(m.status_effects.get('sleeping', 0)) >= DEEP
    except (AttributeError, TypeError, ValueError):
        return False


def sleepers_in(monsters, room) -> list:
    return [m for m in monsters or () if is_deep_sleeper(m) and in_room(room, m.x, m.y)]


def _wears(player, item_id: str = '', flag: str = '') -> bool:
    for it in getattr(player, 'equipped_accessories', None) or ():
        if (item_id and getattr(it, 'id', '') == item_id) or (flag and getattr(it, flag, False)):
            return True
    return False


def factor(player, kind: str) -> float:
    """How readily this hero wakes sleepers for an event of ``kind``
    ('step' or 'take'): 0 never, 1 the room's rule, more for a clumsy hero."""
    if _wears(player, item_id=HAND_OF_GLORY):
        return 0.0                               # the house stays asleep
    if kind == 'step':
        boons = getattr(player, 'boons_taken', None) or {}
        if CATS_FOOTFALL in boons.values() or _wears(player, flag='passive_silent_walk'):
            return 0.0                           # footsteps that make no sound
    try:
        dex = int(getattr(player, 'DEX', 10) or 10)
    except (TypeError, ValueError):
        dex = 10
    f = max(DEX_FLOOR, 1.0 - DEX_STEP * max(0, dex - 10))
    try:
        if player.is_burdened():
            f *= BURDENED
    except Exception:
        pass
    return f


def aggravates(player) -> bool:
    try:
        return bool(player.has_effect('aggravated'))
    except Exception:
        return False


def stirred(player, kind: str, x: int, y: int, sleepers, rtype: str,
            rng: random.Random | None = None) -> list:
    """Which of ``sleepers`` wake when the hero at (x, y) does ``kind``
    ('step' or 'take') in a room of type ``rtype``."""
    rule = RULES.get(rtype)
    if not rule or not sleepers:
        return []
    if aggravates(player):
        return list(sleepers)
    f = factor(player, kind)
    if f <= 0:
        return []
    chance = min(1.0, rule[kind] * f)
    reach = rule[f'{kind}_reach']
    rng = rng or random
    out = []
    for m in sleepers:
        if max(abs(m.x - x), abs(m.y - y)) <= reach and rng.random() < chance:
            out.append(m)
    return out
