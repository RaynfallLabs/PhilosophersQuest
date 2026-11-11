"""Bug bash 3.3.2: the Philosopher's Ring of Mastery gets Socrates' daimonion.

Brandon, 2026-11-08: the ring (WIS 3 once its True Sight went) needed a
power of its own. Its lore: "It never told him what to do; it only stopped
him when he was about to do wrong." Three times a floor, a wrong choice in
any quiz is struck out before it counts and the question stays open; it
never shows the right answer. Hypatia keeps the True Sight the review had
stripped (uniques may break the rules about powers).
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402

with open(os.path.join(ROOT, 'data', 'items', 'accessory.json'), encoding='utf-8') as _f:
    RAW = json.load(_f)


def test_the_ring_of_mastery_carries_the_daimonion_not_true_sight():
    e = RAW['philosophers_ring_legendary']
    assert e['daimonion'] == 3 and e['effects'] == {'stat': 'WIS', 'amount': 3}
    ring = items.make_item_by_id('accessory', 'philosophers_ring_legendary')
    assert ring.daimonion == 3 and 'struck out' in ring.special


def test_hypatia_keeps_true_sight():
    assert RAW['ring_of_hypatia']['effects']['status'] == 'truesight'


def test_every_strip_in_the_review_took():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))
    import ring_kinds_2026_11 as rk
    for k, v in rk.UNIQUE_REVIEW.items():
        fx = RAW[k].get('effects') or {}
        held = {str(fx.get('status', '')).lower(), fx.get('stat'), fx.get('stat2')}
        for p in v.get('strip', ()):
            assert p.lower() not in held and p not in held, (k, p)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import quiz_engine
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_daimonion__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _wear_mastery(g):
    ring = items.make_item_by_id('accessory', 'philosophers_ring_legendary')
    g.player.inventory.append(ring)
    g.player._apply_equip(ring)
    return ring


def _ask(g):
    qe = g.quiz_engine
    qe.start_quiz(mode='threshold', subject='history', tier=1, callback=lambda r: None,
                  threshold=1, total_qs=1)
    q = qe.current_question
    wrong = [c for c in q['choices'] if str(c).strip() != str(q['answer']).strip()]
    return qe, q, wrong


def test_the_voice_strikes_a_wrong_choice_and_the_question_stays_open(game):
    from quiz_engine import QuizState
    _wear_mastery(game)
    qe, q, wrong = _ask(game)
    assert qe.answer(wrong[0]) is False
    assert qe.state == QuizState.ASKING and qe.asked_count == 0
    assert str(wrong[0]).strip() in qe.struck_choices
    assert qe.answer(wrong[0]) is False and qe.asked_count == 0        # struck: nothing happens
    assert qe.answer(q['answer']) is True                                # then the right one


def test_three_a_floor_then_it_falls_silent(game):
    from quiz_engine import QuizState
    _wear_mastery(game)
    for _ in range(3):
        qe, q, wrong = _ask(game)
        qe.answer(wrong[0])
        assert qe.state == QuizState.ASKING
        qe._end(success=False)
    qe, q, wrong = _ask(game)
    qe.answer(wrong[0])
    assert qe.state == QuizState.RESULT and qe.asked_count == 1          # this one counts
    qe._end(success=False)
    game.player._daimonion_used = 0                                      # a new floor
    qe, q, wrong = _ask(game)
    qe.answer(wrong[0])
    assert qe.state == QuizState.ASKING


def test_no_ring_no_voice(game):
    from quiz_engine import QuizState
    qe, q, wrong = _ask(game)
    qe.answer(wrong[0])
    assert qe.state == QuizState.RESULT


def test_the_floor_change_resets_it():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('reset_per_floor_charges(self.player)\n        self.player._daimonion_used = 0')
    assert i > 0
