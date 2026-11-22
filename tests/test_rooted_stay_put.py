"""What is rooted stays where it is (Brandon's play-test, 2026-11-22: "the
emberpup in the rain seems to be... following me? that doesn't seem right").

A creature that lost sight of the hero went to search for him
(senses.notice, senses._search) before anything asked whether it could walk:
the Emberpup, the molds, the floating eye and the story figures all came
after him round the corner.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)
ROOTED = sorted(k for k, v in MONS.items()
                if v.get('ai_pattern') == 'sessile' or v.get('stationary'))
# A story figure as the encounters, the Mooble's cave, the camp and the tomb make one.
FRIEND = {'id': 'abandoned_emberpup', 'name': 'Emberpup', 'symbol': 'e', 'color': [255, 80, 40],
          'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [], 'ai_pattern': 'sessile',
          'resistances': [], 'weaknesses': [], 'min_level': 3, 'is_allied': True}
_G = None


def _game():
    global _G
    from main import Game
    from game_states import STATE_PLAYER
    if _G is None:
        random.seed(5)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_rooted__')
        _G._autosave = lambda *a, **k: None
    _G.state = STATE_PLAYER
    _G.monsters, _G.pets, _G.ground_items = [], [], []
    _G.player.status_effects.clear()
    _G.player.max_hp = _G.player.hp = 100000
    from dungeon import FLOOR, WALL, Room
    d = _G.dungeon
    for y in range(d.height):
        for x in range(d.width):
            room = 3 <= x <= 11 and 3 <= y <= 9
            hall = (y == 6 and 12 <= x <= 16) or (x == 16 and 6 <= y <= 20)
            d.tiles[y][x] = FLOOR if room or hall else WALL
    d.traps = {}
    d.fixture_blocks = d.fixture_opaque = frozenset()
    d.rooms = [Room(2, 2, 11, 9)]
    return _G


def _lose_sight(g, m, turns=14):
    """He sees the hero, and then the hero is gone round the corner, heard."""
    import senses
    p = g.player
    p.x, p.y = 9, 6
    m.take_turn(p, g.dungeon, g.monsters)
    way = [(x, 6) for x in range(10, 17)] + [(16, y) for y in range(7, 21)]
    # Heard as far as the first corner, then not at all: the trail goes cold.
    for i, at in enumerate(way[:turns] + [way[turns - 1]] * 14):
        p.x, p.y = at
        senses.begin_turn(moved=i < turns, guilty=False, floor=3, rested=False)
        if i < 6:
            m._heard = (at[0], at[1], 'step')
        m.take_turn(p, g.dungeon, g.monsters)


@pytest.mark.parametrize('kind', ROOTED)
def test_a_rooted_kind_never_walks_after_the_hero(kind):
    from monster import Monster
    g = _game()
    m = Monster(dict(MONS[kind], id=kind), 6, 6)
    g.monsters.append(m)
    _lose_sight(g, m, 21)
    assert (m.x, m.y) == (6, 6)


def test_a_rooted_friend_never_walks_after_the_hero():
    from monster import Monster
    g = _game()
    m = Monster(FRIEND, 6, 6)
    g.monsters.append(m)
    _lose_sight(g, m, 21)
    assert (m.x, m.y) == (6, 6)
    assert not m.__dict__.get('_lost_line')          # nor "loses your trail"


def test_nothing_rooted_takes_a_step_by_the_path_finder():
    import senses
    from monster import Monster
    g = _game()
    m = Monster(FRIEND, 6, 6)
    assert not senses.step_toward(m, g.dungeon, (10, 6), [m], None, g.player)
    assert (m.x, m.y) == (6, 6)


def _pup(g, at):
    from monster import Monster
    m = Monster(FRIEND, *at)
    m._is_abandoned_emberpup = True
    g.monsters.append(m)
    return m


def test_a_pup_that_wandered_into_a_passage_goes_back_to_a_room():
    """A save from the bug: he followed the hero out and would now block the
    passage for good."""
    g = _game()
    g.player.x, g.player.y = 16, 18
    pup = _pup(g, (16, 12))
    g._emberpup_refresh()
    assert (pup.x, pup.y) in set(g.dungeon.rooms[0].inner_tiles())
    at = (pup.x, pup.y)
    g._emberpup_refresh()
    assert (pup.x, pup.y) == at


def test_a_pup_in_a_room_is_left_where_he_is():
    g = _game()
    g.player.x, g.player.y = 16, 18
    pup = _pup(g, (7, 5))
    g._emberpup_refresh()
    assert (pup.x, pup.y) == (7, 5)
