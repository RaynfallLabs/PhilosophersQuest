"""The fourth bug bash (2026-10-16), combat angle (fix batch F1). Each test
names what was wrong and the finding ID from
_bugbash_2026_10_16/combat/FINDINGS.md.

Behaviour tests on a real headless Game wherever the bug lives in the game
loop. The feel of these fixes in play is a play-test question: Claude cannot
drive Pygame.
"""
import copy
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
_DEFS = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5, name='__test_bug_bash_4_combat__', build=None):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name, secret_build=build)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER          # past any opening story popup
    return g


def _mdef(kind):
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    d = dict(_DEFS[kind])
    d.setdefault('id', kind)
    return d


def _open_floor(g, r=4):
    from dungeon import FLOOR
    for yy in range(g.player.y - r, g.player.y + r + 1):
        for xx in range(g.player.x - r, g.player.x + r + 1):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR


def _spawn(g, kind, dx=1, dy=0, **attrs):
    from monster import Monster
    from dungeon import FLOOR
    x, y = g.player.x + dx, g.player.y + dy
    g.dungeon.tiles[y][x] = FLOOR
    m = Monster(_mdef(kind), x, y)
    for k, v in attrs.items():
        setattr(m, k, v)
    m._aware = True
    g.monsters.append(m)
    return m


def _plain(it):
    it = copy.copy(it)
    it.cursed = False
    it.buc = 'uncursed'
    it.buc_known = True
    it.id_level = 5
    return it


def _texts(g, n=20):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _right(g):
    return str(g.quiz_engine.current_question['answer']).strip()


def _wrong(g):
    q = g.quiz_engine.current_question
    ans = str(q['answer']).strip()
    for c in q.get('choices', []) or q.get('options', []) or []:
        if str(c).strip() != ans:
            return str(c)
    return ans + 'XXX'


def _answer(g, seq, max_steps=200):
    """Answer right/wrong per seq, then wrong until the quiz ends."""
    from quiz_engine import QuizState
    qe = g.quiz_engine
    it = iter(seq)
    steps = 0
    while qe.active and steps < max_steps:
        steps += 1
        if qe.state == QuizState.ASKING:
            qe.answer(_right(g) if next(it, False) else _wrong(g))
        qe.update(5.0)


# ---------------------------------------------------------------- C01
def test_c01_a_ranged_shot_spends_the_tablet_reroll():
    """A bow shot never spent the Tablet of Destinies' once-a-floor reroll,
    so an archer rerolled a wrong answer on every shot."""
    g = _game()
    p = g.player
    _open_floor(g)
    bow = _plain(items.instantiate_weapon('longbow', 'ash'))
    arrows = items.make_item_by_id('ammo', 'iron_arrow')
    arrows.count = 50
    p.inventory += [bow, arrows, items.make_item_by_id('artifact', 'tablet_of_destinies')]
    p.ranged_weapon = bow
    used = 0
    for _ in range(4):
        m = _spawn(g, 'giant_rat', dx=3, hp=10_000, max_hp=10_000)
        g._fire_ranged(m)
        _answer(g, [False, True, True])
        used += int(g.quiz_engine.reroll_was_used)
        p.status_effects.pop('reloading', None)
        g.monsters.remove(m)
    assert used == 1
    assert g._quiz_reroll_used is True
