"""Mimics that pose as the down staircase (the Hellmouth).

A monster whose `disguise` is {"tile": "stairs_down", ...} is drawn as a down
stair until it springs (src/unseen.py, renderer.draw_disguise). This module
decides WHERE such a creature may lie, so it can never cost the hero the way
down:

* it never lies on a stair, only on plain floor;
* the real down stair stays on the map, and stays reachable from the up stair
  with the false one's tile blocked (a Hellmouth is never the only way
  through a corridor or a doorway);
* it lies on ground the hero can walk to (it is something to find, not a
  dead tile in a sealed pocket), outside the arrival room, and at least
  MIN_STAIR_DISTANCE from the real stair, so the two are never side by side;
* at most MAX_PER_FLOOR on a floor; a floor with no real down stair (the
  bottom, a boss arena without one) gets none.

`seat` keeps a creature that already lies on a good tile where it is, moves
one that does not, and takes it off the floor when nowhere qualifies. It runs
when a floor is generated (level_manager) and again whenever a floor is
entered (Game._settle_monsters, after pools and lava are carved and stacked
monsters are moved).
"""
from __future__ import annotations

import random
from collections import deque

MAX_PER_FLOOR = 1
MIN_STAIR_DISTANCE = 6


def poses_as_stairs(m) -> bool:
    d = getattr(m, 'disguise', None)
    return (isinstance(d, dict) and d.get('tile') == 'stairs_down'
            and getattr(m, 'ai_pattern', '') == 'mimic' and not getattr(m, '_aware', False)
            and getattr(m, 'alive', True))


def _walk(dungeon, start, blocked=frozenset()) -> set:
    """Tiles reachable four ways from `start`, never entering `blocked`."""
    from dungeon import (FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR,
                         FOUNTAIN, GRAVE, THRONE, ICE)
    passable = (FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR,
                FOUNTAIN, GRAVE, THRONE, ICE)
    tiles, w, h = dungeon.tiles, dungeon.width, dungeon.height
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if (0 <= n[0] < w and 0 <= n[1] < h and n not in seen and n not in blocked
                    and tiles[n[1]][n[0]] in passable):
                seen.add(n)
                q.append(n)
    return seen


def stairs(dungeon):
    from dungeon import _find_stair_tiles
    return _find_stair_tiles(dungeon.tiles, dungeon.width, dungeon.height)


def _in_room(room, x, y) -> bool:
    return room.x <= x < room.x + room.width and room.y <= y < room.y + room.height


def good_tile(dungeon, x, y, reach, up, down, taken=frozenset()) -> bool:
    """May a false stair lie on (x, y)?"""
    if not _plausible(dungeon, x, y, reach, up, down, taken):
        return False
    # The real stair stays reachable with this tile blocked.
    start = up or down
    return down in _walk(dungeon, start, blocked={(x, y)})


def _plausible(dungeon, x, y, reach, up, down, taken) -> bool:
    """Every rule but the (costly) path check."""
    from dungeon import FLOOR
    if not dungeon.in_bounds(x, y) or dungeon.tiles[y][x] != FLOOR:
        return False
    if (x, y) in taken or (x, y) not in reach:
        return False
    if max(abs(x - down[0]), abs(y - down[1])) < MIN_STAIR_DISTANCE:
        return False
    if up and max(abs(x - up[0]), abs(y - up[1])) < 3:
        return False
    rooms = getattr(dungeon, 'rooms', None) or []
    if rooms and _in_room(rooms[0], x, y):
        return False            # never in the room the hero arrives in
    return True


def seat(dungeon, monsters: list, rng=None) -> list:
    """Put every stair-mimic on a tile it may lie on. Returns the ones taken
    off the floor (no good tile, no real stair, or one too many)."""
    rng = rng or random
    fakes = [m for m in monsters if poses_as_stairs(m)]
    if not fakes:
        return []
    up, down = stairs(dungeon)
    removed = []
    if down is None:
        removed = fakes
    else:
        reach = _walk(dungeon, up or down)
        if down not in reach:
            removed = fakes             # the floor is already odd: leave it be
        else:
            keep = fakes[:MAX_PER_FLOOR]
            removed = fakes[MAX_PER_FLOOR:]
            from geom import occupied_tiles
            for m in keep:
                taken = set()
                for o in monsters:
                    if o is not m and getattr(o, 'alive', True):
                        taken.update(occupied_tiles(o))
                if good_tile(dungeon, m.x, m.y, reach, up, down, taken):
                    continue
                spots = [(x, y) for (x, y) in reach
                         if _plausible(dungeon, x, y, reach, up, down, taken)]
                # Prefer the far side of the floor, like a real way down.
                o = up or down
                spots.sort(key=lambda t: -(abs(t[0] - o[0]) + abs(t[1] - o[1])))
                far = spots[:max(1, len(spots) // 3)]
                rng.shuffle(far)
                spot = next((t for t in far + spots[len(far):]
                             if down in _walk(dungeon, o, blocked={t})), None)
                if spot is None:
                    removed.append(m)
                    continue
                m.x, m.y = spot
    for m in removed:
        if m in monsters:
            monsters.remove(m)
    return removed
