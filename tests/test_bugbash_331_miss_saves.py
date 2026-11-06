"""Bug bash 3.3.1, combat A2: head starts that turned a miss into a hit.

A2. Glamdring's +1 against goblins and orcs was added to a chain of 0. The
    armour chain_bonus above it already had the rule: combat never does a
    sum for you.
Ruling (Brandon, 2026-11-06) on Gungnir, Fail-not and Hrunting: "Wrong
    answers only." A real wrong answer still lands a light hit (their lore),
    but Strike Now (SPACE) before any answer is not a wrong answer: no save,
    no Hrunting charge spent, and the Strike Now preview shows 0.

These drive the real combat.player_attack, effective_chain, strike_preview
and the real QuizEngine. Deep uniques cannot be play-tested in a sitting.
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)


def _unique(wid):
    return next(w for w in items.load_items('weapon') if w.id == wid)


def _target(kind='kobold', hp=10 ** 8):
    m = Monster(dict(_DEFS[kind], id=kind), 6, 5)
    m.hp = m.max_hp = hp
    return m


def _player(weapon=None):
    p = Player()
    p.x, p.y = 5, 5
    p.hp = p.max_hp = 10 ** 6
    if weapon is not None:
        if getattr(weapon, 'requires_ammo', None) is not None:
            p.ranged_weapon = weapon
        else:
            p.weapon = weapon
    return p


class _Quiz:
    """Stands in for QuizEngine: the attack's callback gets ``score``."""
    def __init__(self, score, struck_early=False):
        self.score = score
        self.struck_early = struck_early

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True,
                                       struck_early=self.struck_early))


def _attack(p, m, score, struck_early=False, ranged=False):
    """(damage, killed, chain) of one real attack at quiz score ``score``."""
    got = []
    combat.player_attack(p, m, _Quiz(score, struck_early),
                         lambda dmg, killed, chain, *a, **k: got.append((dmg, killed, chain)),
                         ranged=ranged)
    return got[0]



# --------------------------------------------------------------- A2 Glamdring

def test_glamdring_glow_never_turns_a_miss_into_a_hit():
    glam = _unique('glamdring')
    p = _player(glam)
    gob = _target('goblin')
    assert combat.effective_chain(p, gob, glam, 0, consume=False) == 0
    assert combat.effective_chain(p, gob, glam, 0, consume=True) == 0
    assert combat.strike_preview(p, gob, 0) == 0
    dmg, _k, chain = _attack(p, gob, 0)
    assert (dmg, chain) == (0, 0)


def test_glamdring_glow_still_adds_a_rung_to_a_landed_blow():
    glam = _unique('glamdring')
    p = _player(glam)
    assert combat.effective_chain(p, _target('goblin'), glam, 2, consume=False) == 3
    assert combat.effective_chain(p, _target('orc_warrior'), glam, 2, consume=False) == 3
    assert combat.effective_chain(p, _target('giant_rat'), glam, 2, consume=False) == 2


# ------------------------------------- Ruling: never-miss weapons, wrong answers only

@pytest.mark.parametrize('wid', ['gungnir', 'fail_not', 'hrunting'])
def test_a_wrong_first_answer_still_lands_a_light_hit(wid):
    w = _unique(wid)
    p = _player(w)
    ranged = w is p.ranged_weapon
    dmg, _k, chain = _attack(p, _target('kobold'), 0, struck_early=False, ranged=ranged)
    assert chain == 1 and dmg > 0


@pytest.mark.parametrize('wid', ['gungnir', 'fail_not', 'hrunting'])
def test_strike_now_before_answering_is_not_saved(wid):
    w = _unique(wid)
    p = _player(w)
    ranged = w is p.ranged_weapon
    dmg, _k, chain = _attack(p, _target('kobold'), 0, struck_early=True, ranged=ranged)
    assert (dmg, chain) == (0, 0)


def test_strike_now_at_zero_does_not_spend_hrunting_once_a_floor():
    w = _unique('hrunting')
    p = _player(w)
    _attack(p, _target('kobold'), 0, struck_early=True)
    assert not getattr(p, '_hrunting_save_used', False)
    dmg, _k, chain = _attack(p, _target('kobold'), 0, struck_early=False)
    assert chain == 1 and dmg > 0 and p._hrunting_save_used     # the real miss spends it


@pytest.mark.parametrize('wid', ['gungnir', 'fail_not', 'hrunting', 'glamdring'])
def test_strike_now_preview_at_zero_shows_no_free_damage(wid):
    w = _unique(wid)
    p = _player(w)
    ranged = w is p.ranged_weapon
    target = _target('goblin')
    assert combat.strike_preview(p, target, 0, ranged=ranged) == 0
    assert not getattr(p, '_hrunting_save_used', False)


def _real_engine():
    from quiz_engine import QuizEngine
    eng = QuizEngine()
    eng._cache['math'] = [{'tier': t, 'question': f'm{t}-{i}', 'answer': 'right',
                           'choices': ['right', 'w1', 'w2', 'w3']}
                          for t in range(1, 6) for i in range(8)]
    return eng


def test_the_quiz_result_says_when_strike_now_ended_the_chain():
    """The flag the combat reads comes from the quiz itself: SPACE at 0 says
    so; a wrong first answer and a correct-then-SPACE do not pretend to."""
    eng = _real_engine()
    got = []
    eng.start_quiz('chain', 'math', tier=1, callback=got.append, timed=False)
    assert eng.cancel_and_strike()
    assert got[-1].score == 0 and got[-1].struck_early is True

    eng.start_quiz('chain', 'math', tier=1, callback=got.append, timed=False)
    eng.answer('w1')
    eng.release_result_hold()
    eng._result_hold = False
    eng.update(10.0)
    assert got[-1].score == 0 and got[-1].struck_early is False


def test_gungnir_through_the_real_quiz_engine():
    """SPACE at 0 with the real engine: a miss. A wrong answer: a light hit."""
    gun = _unique('gungnir')
    p = _player(gun)
    out = []
    eng = _real_engine()
    combat.player_attack(p, _target('kobold'), eng,
                         lambda dmg, killed, chain, *a, **k: out.append((dmg, chain)))
    assert eng.cancel_and_strike()
    assert out[-1] == (0, 0)

    eng = _real_engine()
    combat.player_attack(p, _target('kobold'), eng,
                         lambda dmg, killed, chain, *a, **k: out.append((dmg, chain)))
    eng.answer('w1')
    eng._result_hold = False
    eng.update(10.0)
    assert out[-1][1] == 1 and out[-1][0] > 0
