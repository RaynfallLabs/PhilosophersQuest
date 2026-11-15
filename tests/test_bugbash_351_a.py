"""Bug bash 3.5.1, hunter A: the kitchen rebuild of 3.5.0.

Each test pins one finding of A_report.md (the kitchen: harvest, the cook
menu's words, what a dish gives, cook to carry, the boss trophies). Real
keys drive a headless Game where the path has keys; the rest drives
src/kitchen.py and src/food_system.py on a real Player. Whether the menu
reads well to a kid is Brandon's play-test: Claude cannot drive Pygame.
"""
import copy
import os
import pickle
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), os.path.join(ROOT, 'tests')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

import kitchen  # noqa: E402
from test_bug_bash_5_encounters import _game  # noqa: E402

pygame.init()


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _right_answer(g):
    """Every quiz answered right, at once (the harvest and the cook)."""
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))


def _player(deepest=10):
    from player import Player
    p = Player()
    p.deepest_floor_reached = deepest
    return p


def _ing(iid, n=1):
    from food_system import load_ingredient_for
    it = load_ingredient_for(iid)
    it.count = n
    return it


def _harvest(g, monster):
    from food_system import make_corpse
    from game_states import STATE_PLAYER
    px, py = g.player.x, g.player.y
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (px, py)]
    g.ground_items.append(make_corpse(monster, px, py))
    g.state = STATE_PLAYER
    _press(g, pygame.K_h, 'h')


def _held(g, iid):
    return kitchen.held_counts(g.player.inventory).get(iid, 0)


# ---------------------------------------------------------------------------
# A1. Hunter's Harvest gave a second boss trophy, and its power twice.
# ---------------------------------------------------------------------------

def test_a1_hunters_harvest_never_doubles_a_boss_trophy():
    """Great beasts tier 3 (Hunter's Harvest) gave one more portion of
    every great beast's corpse, Fenrir's included: two of Fenrir's Tooth,
    and its +3 STR twice (STR 10 to 17 in two meals), past every cap. A
    trophy is one of a kind; an ordinary great beast still gives two."""
    import family_lore
    g = _game()
    g.monsters = []
    _right_answer(g)
    p = g.player
    p.studied_monster_ids = set(family_lore.members('great_beasts'))
    assert family_lore.tier(p, 'great_beasts') >= 3
    _harvest(g, 'fenrir_wolf')
    assert _held(g, 'fenrir_wolf_trophy') == 1
    last = str(g.msg_log.entries[-1][0])
    assert "Hunter's Harvest" not in last, last
    # An ordinary great beast: the extra portion still comes.
    _harvest(g, 'dire_lion')
    assert _held(g, 'dire_lion_prime') == 2
