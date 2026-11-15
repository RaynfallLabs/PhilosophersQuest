"""Bug bash 3.5.1: the lead's small fixes from the hunters' notes.

- "The Gilt Varro is slain!": a man's name takes no article (A's note).
- A war-band never camps in the down stair's room (C's question 5).
- A ruined dish is not a discovered recipe (A's question 5: the list's own
  comment says "successfully cooked", and the Seeker's count agrees).
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))
sys.path.insert(0, HERE)


def test_gilt_varro_is_a_name():
    import bococho_encounter as B
    from monster import Monster, the_name
    v = Monster(B.creature_defn('varro', 55), 0, 0)
    assert the_name(v) == 'Gilt Varro'
    assert the_name(v, lower=True) == 'Gilt Varro'


def test_no_band_camps_by_the_down_stair():
    import war_bands
    from dungeon import generate_dungeon, STAIRS_DOWN
    checked = 0
    for i in range(40):
        d = generate_dungeon(80, 50, 3 + i % 20, rng=random.Random(9100 + i))
        room = war_bands._band_room(d, random.Random(i), [])
        if room is None:
            continue
        checked += 1
        assert not any(d.tiles[y][x] == STAIRS_DOWN
                       for y in range(room.y, room.y + room.height)
                       for x in range(room.x, room.x + room.width)), i
    assert checked > 20


def test_a_ruined_dish_is_not_a_discovered_recipe():
    import inspect
    import main
    src = inspect.getsource(main.Game)
    i = src.index('# Track discovered recipes')
    block = src[i:i + 400]
    assert 'not _ruined' in block.split('self._cooked_recipes.append')[0]
