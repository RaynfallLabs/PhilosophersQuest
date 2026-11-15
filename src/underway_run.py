"""The Underway Run: the side floor where the young Bococho races Brassbeak
(boss_levels.UNDERWAY_RUN, 996; built like the Zombie Stage).

A great oval scraped in the floor of a cavern: sand between a rail on the
inside and a rail on the outside, the start and finish line at the middle
of the near straight with a banner on two poles, and a paddock below it
where the hero arrives, with the betting board and the gate back to the
camp (a down stair, as the stage door is).

``loop(dungeon, lane)`` is the track as an ordered ring of tiles from the
finish line round, one ring per lane (0 the inside, 1 the outside), so the
race (src/race.py) can say where each bird stands; the game moves the two
runners there after each leg (src/game_race.py).

The track's own pictures (``race_track_floor``, ``race_track_rail``) are
used where they are installed (``tile_art``); a floor built before them is
drawn with the plain tiles.
"""
from __future__ import annotations

import math
import os

_CX, _CY = 40, 14
_OUT = (30, 13)       # the outer rail's half-widths
_IN = (23, 7)         # the infield's


def _inside(x, y, rx, ry) -> bool:
    return ((x - _CX) / rx) ** 2 + ((y - _CY) / ry) ** 2 < 1.0


def _env_has(name: str) -> bool:
    from paths import data_path
    return os.path.exists(data_path('assets', 'tiles', 'env', name + '.png'))


def _ring(tiles, share: float) -> list:
    """The track's ring at ``share`` of the way from the inside rail to the
    outside, from the finish line (the bottom middle) round to the east,
    up, west and back down: walkable tiles, no repeats."""
    from dungeon import FLOOR
    rx = _IN[0] + (_OUT[0] - _IN[0]) * share
    ry = _IN[1] + (_OUT[1] - _IN[1]) * share
    out, seen = [], set()
    steps = 720
    for k in range(steps):
        th = math.pi / 2 - 2 * math.pi * k / steps
        x = int(round(_CX + rx * math.cos(th)))
        y = int(round(_CY + ry * math.sin(th)))
        if (x, y) in seen or tiles[y][x] != FLOOR:
            continue
        seen.add((x, y))
        out.append((x, y))
    return out


def build():
    """(dungeon, monsters, items) for the Underway Run."""
    import boss_levels as bl
    import decor
    from dungeon import FLOOR, WALL, STAIRS_DOWN, Room

    tiles = bl._blank()
    for y in range(1, bl._H - 1):
        for x in range(1, bl._W - 1):
            if _inside(x, y, *_OUT) and not _inside(x, y, *_IN):
                tiles[y][x] = FLOOR
    # The paddock below the near straight, and the gate onto the track.
    paddock = Room(33, 28, 15, 8)
    for y in range(paddock.y + 1, paddock.y + paddock.height - 1):
        for x in range(paddock.x + 1, paddock.x + paddock.width - 1):
            tiles[y][x] = FLOOR
    gx, y = _CX, paddock.y
    while y > 0 and tiles[y][gx] != FLOOR:
        tiles[y][gx] = FLOOR
        y -= 1
    exit_tile = (paddock.x + 2, paddock.y + paddock.height - 2)
    tiles[exit_tile[1]][exit_tile[0]] = STAIRS_DOWN
    track = Room(_CX - _OUT[0], _CY - _OUT[1], 2 * _OUT[0] + 1, 2 * _OUT[1] + 1)
    dungeon = bl._make(tiles, [paddock, track], bl.UNDERWAY_RUN)
    dungeon.domain = None
    dungeon.theme = None

    # The track's pictures where they are installed.
    art = {}
    floor_art = 'race_track_floor' if _env_has('race_track_floor') else None
    rail_art = 'race_track_rail' if _env_has('race_track_rail') else None
    for y in range(bl._H):
        for x in range(bl._W):
            t = tiles[y][x]
            on_track = _inside(x, y, *_OUT) and not _inside(x, y, *_IN)
            if t == FLOOR and on_track and floor_art:
                art[(x, y)] = floor_art
            elif t == WALL and rail_art and any(
                    0 <= x + dx < bl._W and 0 <= y + dy < bl._H
                    and tiles[y + dy][x + dx] == FLOOR
                    and _inside(x + dx, y + dy, *_OUT) and not _inside(x + dx, y + dy, *_IN)
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                art[(x, y)] = rail_art
    if art:
        dungeon.tile_art = art

    rings = [_ring(tiles, 0.3), _ring(tiles, 0.7)]
    dungeon.race_loops = rings
    # The finish line: the banner beside the outside rail at the line, the
    # board in the paddock by the gate.
    line = rings[1][0]
    by = line[1]
    while tiles[by + 1][line[0] + 1] == FLOOR and _inside(line[0] + 1, by + 1, *_OUT):
        by += 1
    decor.place(dungeon, (line[0] + 1, by), 'race_finish_banner')
    decor.place(dungeon, (paddock.x + paddock.width - 3, paddock.y + 2), 'race_betting_board')
    dungeon.race_finish = list(line)
    dungeon.race_exit = list(exit_tile)
    import bococho_encounter
    dungeon.atmosphere_messages = list(bococho_encounter.data()['race']['arrival'][:1])
    return dungeon, [], []


def loop(dungeon, lane: int) -> list:
    """The ordered ring of track tiles for ``lane`` (0 inside, 1 outside)."""
    rings = getattr(dungeon, 'race_loops', None) or []
    if not rings:
        return []
    return list(rings[max(0, min(len(rings) - 1, int(lane)))])
