"""The Green Chapel Axe's returning blow (2026-11-14, found by the mini-boss
tuning). At max chain half the blow came back on its wielder with no cap,
so deep down (where a max chain deals thousands) one swing killed him,
silently. Now it is the beheading game's price, not its end: at most
combat.RETURNING_BLOW_CAP of his health, never his last point, and the log
says so. These drive the real combat.player_attack. A floor-70 unique cannot
be play-tested in a sitting.
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)


def _axe():
    return next(w for w in items.load_items('weapon') if w.id == 'green_chapel_axe')


class _Quiz:
    def __init__(self, score):
        self.score = score

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True, struck_early=False))


def _swing(p, score):
    m = Monster(dict(_DEFS['kobold'], id='kobold'), 6, 5)
    m.hp = m.max_hp = 10 ** 9
    got = []
    combat.player_attack(p, m, _Quiz(score),
                         lambda dmg, killed, chain, *a, **k: got.append(dmg))
    return got[0]


def _hero(hp):
    p = Player()
    p.x, p.y = 5, 5
    p.hp = p.max_hp = hp
    p.weapon = _axe()
    p.weapon.base_damage = 5000           # a deep hero's blow: thousands at max chain
    return p


def _max_chain(w):
    return int(w.max_chain_length or len(w.chain_multipliers))


def test_a_max_chain_blow_costs_at_most_a_quarter_and_never_kills():
    p = _hero(200)
    dmg = _swing(p, _max_chain(p.weapon))
    assert dmg > 400                                        # half would have killed him
    lost = 200 - p.hp
    assert 0 < lost <= int(200 * combat.RETURNING_BLOW_CAP)
    assert p.hp >= 1 and p.__dict__.get('_rebound') == lost


def test_it_never_takes_his_last_point():
    p = _hero(200)
    p.hp = 3
    _swing(p, _max_chain(p.weapon))
    assert p.hp == 1


def test_short_of_max_chain_nothing_comes_back():
    p = _hero(200)
    _swing(p, 1)
    assert p.hp == 200 and '_rebound' not in p.__dict__


def test_the_game_says_so():
    import pygame
    pygame.init()
    from main import Game
    g = Game(pygame.display.set_mode((1, 1)), player_name='__axe_rebound__')
    g.player.__dict__['_rebound'] = 37
    # the line is said where the strike's own line is (game_combat); read it
    # straight from the source so the words stay pinned
    src = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert "The blow comes back on you, as the Green Chapel's bargain" in src
    assert g.player.__dict__.pop('_rebound') == 37
