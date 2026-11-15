"""The way down never hangs on a secret door (3.5.1).

The stair checks count a secret door as passable (bumping one opens it), so
a water pool or a lava river that cut the plain route was kept whenever a
shortcut's secret door still joined the halves. About one floor in 12,000
(floors 15-19) left the hero no way down but to search the walls. Found by
the Black Knight's test, which failed about one run in ten on an unseeded
floor (tests/test_black_knight.py). dungeon._open_the_way_down turns the
secret doors on the way into plain doors.
"""
import os
import random
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))

import dungeon as D  # noqa: E402


def _on_foot(d):
    up, down = D._find_stair_tiles(d.tiles, d.width, d.height)
    plain = (D.FLOOR, D.STAIRS_UP, D.STAIRS_DOWN, D.DOOR, D.ALTAR, D.FOUNTAIN,
             D.GRAVE, D.THRONE, D.ICE)
    seen = {up}
    q = deque([up])
    while q:
        x, y = q.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (n not in seen and 0 <= n[0] < d.width and 0 <= n[1] < d.height
                    and d.tiles[n[1]][n[0]] in plain and n not in d.fixture_blocks):
                seen.add(n)
                q.append(n)
    return down in seen


def test_a_secret_door_that_is_the_only_way_on_becomes_a_door():
    w, h = 12, 5
    tiles = [[D.WALL] * w for _ in range(h)]
    for x in range(1, 11):
        tiles[2][x] = D.FLOOR
    tiles[2][1] = D.STAIRS_UP
    tiles[2][10] = D.STAIRS_DOWN
    tiles[2][6] = D.SECRET_DOOR                    # the corridor's only link
    tiles[1][3] = D.SECRET_DOOR                    # a shortcut to nowhere stays hidden
    d = D.Dungeon(tiles, [], w, h, 5)
    assert not _on_foot(d)
    assert D._open_the_way_down(d) == 1
    assert d.tiles[2][6] == D.DOOR and d.tiles[1][3] == D.SECRET_DOOR
    assert _on_foot(d)
    assert D._open_the_way_down(d) == 0            # nothing more to open


def test_the_way_to_a_quest_piece_never_hangs_on_a_secret_door():
    """_open_the_way to any tile, not just the stair (3.5.2: the Root of a
    Mountain sat past a door whose passage only a secret door reached)."""
    w, h = 12, 7
    tiles = [[D.WALL] * w for _ in range(h)]
    for x in range(1, 11):
        tiles[2][x] = D.FLOOR
    tiles[2][1] = D.STAIRS_UP
    tiles[2][10] = D.STAIRS_DOWN
    tiles[3][8] = D.SECRET_DOOR                    # the passage's only link
    tiles[4][8] = D.FLOOR
    tiles[5][8] = D.FLOOR                          # where the Root lies
    tiles[1][3] = D.SECRET_DOOR                    # a shortcut to nowhere stays hidden
    d = D.Dungeon(tiles, [], w, h, 68)
    assert D._open_the_way_down(d) == 0            # the stair was never hidden
    assert D._open_the_way(d, (8, 5)) == 1
    assert d.tiles[3][8] == D.DOOR and d.tiles[1][3] == D.SECRET_DOOR
    assert D._open_the_way(d, (8, 5)) == 0


def test_the_floor_that_hid_its_way_down():
    d = D.generate_dungeon(80, 50, 19, rng=random.Random(195455276841151))
    assert _on_foot(d)


def test_many_floors_have_a_way_down_on_foot():
    for i in range(60):
        d = D.generate_dungeon(80, 50, 1 + (i * 7) % 99, rng=random.Random(7000 + i))
        up, down = D._find_stair_tiles(d.tiles, d.width, d.height)
        if up and down:
            assert _on_foot(d), (i, d.level if hasattr(d, 'level') else '')
