"""The kitchen's staples-only poison dishes and the poison build meet (3.6.1,
2026-11-22): a staples dish gives the Venom Ward, and the ward halves a real
bite. The two were built on separate branches, and before the poison merge
the kitchen's dishes gave a ward the game did not know.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
_G = None


def _game():
    global _G
    from main import Game
    if _G is None:
        random.seed(6)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_venom_ward_kitchen__')
        _G._autosave = lambda *a, **k: None
    return _G


def _ward_dishes():
    import kitchen
    return [r for r in kitchen.book() if kitchen.dish_power(r) == 'venom_ward']


def test_the_ward_is_known_to_the_game():
    from status_effects import EFFECT_INFO
    assert _ward_dishes()
    assert EFFECT_INFO['venom_ward'][0] == 'Venom Ward'


def test_every_ward_dish_is_staples_only():
    import kitchen
    for rec in _ward_dishes():
        assert not any(kitchen.is_harvested(p) for p in kitchen.parts(rec)), rec.get('name')


def test_a_staples_dish_ward_halves_a_real_bite():
    import kitchen
    import venom
    p = _game().player
    p.max_hp = p.hp = 400
    p.status_effects.clear()
    venom.lands(p, 6, 99, venom=8)              # (DC 99: no save)
    full = venom.strength(p)
    assert full > 0
    p.status_effects.clear()
    kitchen.apply_dish(p, _ward_dishes()[0])
    assert p.status_effects.get('venom_ward', 0) > 0
    venom.lands(p, 6, 99, venom=8)
    assert venom.strength(p) < full
