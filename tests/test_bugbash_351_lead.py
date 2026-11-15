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


# ------------------------------------------------- what a fall earns, said after it

from test_bugbash_wb_e import make_game, open_floor, place_monster  # noqa: E402,F401
from test_bugbash_351_e import a_seeker  # noqa: E402,F401


def test_what_a_fall_earns_is_said_after_you_have_died(make_game, a_seeker):
    """Bug bash 3.5.1 E: "ACHIEVEMENT: The First Fall... / You have died!".
    Every death ends the run (and the Seeker's run-end awards) before it
    says the death line; the awards now wait a frame."""
    import pygame
    from game_states import STATE_DEAD
    g, h = make_game(name='Wat')
    p = g.player
    open_floor(g, p.x, p.y, 4)
    place_monster(g, 'goblin', 1)
    g._refresh_fov()
    p.hp = 1
    for _ in range(60):
        if g.state == STATE_DEAD or p.is_dead():
            break
        if g.state != 'player':
            h.key(pygame.K_RETURN)
        else:
            h.wait()
    for _ in range(3):
        h.frame()
    log = [str(e[0]) for e in g.msg_log.entries]
    died = [i for i, t in enumerate(log) if t.startswith('You have died')]
    won = [i for i, t in enumerate(log) if t.startswith('ACHIEVEMENT:')]
    assert died and won, log[-12:]
    assert died[0] < won[0], log[-12:]
