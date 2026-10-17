"""Bug bash 4, call 18 (MK-06): walking into your own pet swaps places with
it, like most roguelikes. It used to put hero and pet on one tile. If the pet
cannot stand where the hero is (levitating over water, on a dug pit), the
hero stops and no turn passes.

Logic tests on a real headless Game; swapping is easily reachable in play,
so Brandon still walks into a pet once to see it.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame

pygame.init()

_SCREEN = None


def _game():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    g = Game(_SCREEN, player_name='__test_pet_swap__')
    g.monsters = []
    g.ground_items = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_neighbour(g):
    """A walkable tile east/west/north/south of the hero."""
    p = g.player
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if g.dungeon.is_walkable(p.x + dx, p.y + dy):
            return dx, dy
    raise AssertionError('hero boxed in')


def _with_pet(g):
    from pet_system import Pet
    dx, dy = _open_neighbour(g)
    pet = Pet('electric', g.player.x + dx, g.player.y + dy)
    g.pets = [pet]
    return pet, dx, dy


def test_walking_into_your_pet_swaps_places():
    g = _game()
    pet, dx, dy = _with_pet(g)
    start = (g.player.x, g.player.y)
    dest = (pet.x, pet.y)
    turn0 = g.turn_count
    g._do_move(dx, dy)
    assert (g.player.x, g.player.y) == dest
    assert (pet.x, pet.y) == start, "the pet should take the hero's old tile"
    assert any('swap places' in str(e[0]) for e in g.msg_log.entries[-4:])
    assert g.turn_count > turn0


def test_no_swap_when_the_pet_cannot_stand_on_your_tile():
    """Levitating over water: the pet cannot swim onto it, so the hero stops
    and nobody moves."""
    from dungeon import WATER
    g = _game()
    pet, dx, dy = _with_pet(g)
    start = (g.player.x, g.player.y)
    g.dungeon.tiles[start[1]][start[0]] = WATER
    g.player.add_effect('levitating', 50)
    dest = (pet.x, pet.y)
    g._do_move(dx, dy)
    assert (g.player.x, g.player.y) == start
    assert (pet.x, pet.y) == dest
    assert any('in your way' in str(e[0]) for e in g.msg_log.entries[-3:])


def test_ice_slide_stops_before_a_pet():
    from dungeon import ICE
    g = _game()
    dx, dy = _open_neighbour(g)
    p = g.player
    a = (p.x + dx, p.y + dy)
    b = (p.x + 2 * dx, p.y + 2 * dy)
    if not g.dungeon.is_walkable(*b):
        g.dungeon.tiles[b[1]][b[0]] = g.dungeon.tiles[a[1]][a[0]]
    g.dungeon.tiles[a[1]][a[0]] = ICE
    from pet_system import Pet
    pet = Pet('electric', *b)
    g.pets = [pet]
    g._do_move(dx, dy)
    assert (p.x, p.y) == a
    assert (pet.x, pet.y) == b
