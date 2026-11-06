"""Bug bash 3.3.1, B6: the Scroll of Recall sets the reader at the head of
the stairs going down, and never on a monster (or pet) standing there.

Behaviour tests on a real headless Game. The feel in play is a play-test
question: Claude cannot drive Pygame.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_bugbash_331_recall__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _down_stair(g):
    from dungeon import STAIRS_DOWN
    return next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                if g.dungeon.tiles[y][x] == STAIRS_DOWN)


def _rat_at(x, y):
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = dict(json.load(f)['giant_rat'])
    d['id'] = 'giant_rat'
    return Monster(d, x, y)


def _read_recall(g):
    sc = items.make_item_by_id('scroll', 'scroll_of_recall')
    g._apply_scroll_effect(sc)


def test_b6_recall_lands_on_the_stair_when_it_is_free():
    g = _game(seed=61)
    stair = _down_stair(g)
    _read_recall(g)
    assert (g.player.x, g.player.y) == stair


def test_b6_recall_never_lands_on_a_monster_on_the_stair():
    from geom import monster_at_tile
    g = _game(seed=62)
    stair = _down_stair(g)
    rat = _rat_at(*stair)
    g.monsters.append(rat)
    _read_recall(g)
    here = (g.player.x, g.player.y)
    assert monster_at_tile(g.monsters, *here) is None, "the hero stands inside a monster"
    assert g.dungeon.is_walkable(*here)
    # Still at the head of the stairs: the nearest free tile, a step away.
    assert max(abs(here[0] - stair[0]), abs(here[1] - stair[1])) <= 2, (here, stair)
