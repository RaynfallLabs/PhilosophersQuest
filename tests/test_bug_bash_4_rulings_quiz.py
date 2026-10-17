"""Bug bash 4, Brandon's rulings on the quiz calls (R1): 1, 3, 5 and 6.

Call 2 (stems that print their own answer) is covered by the whole-answer
check in test_answer_leak.py; call 4 (builder jargon in contexts) by
test_contexts_carry_no_author_notes in test_ladder_blurb_coverage.py.
"""
import json
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()


def _timed_engine():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.start_quiz('chain', 'math', 1, lambda r: None, timed=True, base_seconds=20)
    return qe


# ---------------------------------------------------------------- call 1
def test_context_card_stops_a_timed_clock_once_per_question():
    """Brandon: "once per question is fair". The first open of the card
    stops the clock; a second open on the same question lets it run."""
    qe = _timed_engine()
    assert qe.pause_timer() is True              # first open: stopped
    qe.update(3.0)
    assert qe.time_remaining == 20.0
    qe.resume_timer()
    assert qe.pause_timer() is False             # second open: running
    qe.update(3.0)
    assert qe.time_remaining == 17.0
    qe.resume_timer()


def test_a_new_question_earns_a_fresh_pause():
    qe = _timed_engine()
    qe.pause_timer()
    qe.resume_timer()
    assert not qe.context_pause_available()
    qe.answer(str(qe.current_question['answer']))   # right: chain goes on
    while qe.state.name == 'RESULT':
        qe.update(0.1)
    assert qe.state.name == 'ASKING'
    assert qe.context_pause_available()
    assert qe.pause_timer() is True


def test_untimed_quizzes_keep_the_pause():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.start_quiz('threshold', 'philosophy', 1, lambda r: None)
    assert not qe.timed
    for _ in range(3):
        assert qe.pause_timer() is True
        qe.resume_timer()


def _game_in_combat_quiz(name):
    from main import Game
    from game_states import STATE_PLAYER, STATE_QUIZ
    g = Game(pygame.display.set_mode((64, 64)), player_name=name)
    g.state = STATE_PLAYER
    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('chain', 'math', 1, lambda r: None, timed=True, base_seconds=20)
    g._resize_grace = 0
    # Give the question a blurb so C opens the card.
    g.quiz_engine.current_context_blurb = lambda: "Some orientation."
    return g


def test_second_card_open_lets_the_clock_run_in_the_game():
    """The game did not tick the quiz at all while the card was open, so
    the card froze the clock however often it was opened."""
    from game_states import STATE_QUIZ, STATE_QUIZ_CONTEXT
    g = _game_in_combat_quiz('bb4r1a')
    qe = g.quiz_engine
    g._quiz_input(pygame.K_c)
    assert g.state == STATE_QUIZ_CONTEXT
    g.update(0.2)
    assert qe.time_remaining == 20.0
    assert "stopped" in g._quiz_context_clock_note()
    g._quiz_context_input(pygame.K_c)
    assert g.state == STATE_QUIZ
    g._quiz_input(pygame.K_c)
    assert g.state == STATE_QUIZ_CONTEXT
    assert "running" in g._quiz_context_clock_note()
    g.update(0.2)
    assert abs(qe.time_remaining - 19.8) < 1e-6


def test_clock_running_out_behind_the_card_closes_it():
    from game_states import STATE_QUIZ, STATE_QUIZ_CONTEXT
    from quiz_engine import QuizState
    g = _game_in_combat_quiz('bb4r1b')
    qe = g.quiz_engine
    g._quiz_input(pygame.K_c)
    g._quiz_context_input(pygame.K_ESCAPE)
    g._quiz_input(pygame.K_c)
    assert g.state == STATE_QUIZ_CONTEXT
    qe.time_remaining = 0.1
    g.update(0.2)
    assert qe.state != QuizState.ASKING
    assert g.state == STATE_QUIZ


def test_card_says_nothing_about_a_clock_on_untimed_quizzes():
    g = _game_in_combat_quiz('bb4r1c')
    g.quiz_engine.start_quiz('threshold', 'philosophy', 1, lambda r: None)
    assert g._quiz_context_clock_note() is None


# ---------------------------------------------------------------- call 3
def test_five_second_minimum_comes_after_status_penalties():
    """A confused and blinded WIS 6 hero got 2 s: the floor was applied
    before the multiplier."""
    from player import Player
    from quiz_engine import QuizEngine, MIN_TIMED_SECONDS
    p = Player()
    p.WIS = 6
    mod = 0.40       # confused x blinded hits the multiplier's own 0.40 floor
    qe = QuizEngine()
    qe.start_quiz('chain', 'math', 1, lambda r: None, timed=True,
                  base_seconds=p.get_quiz_timer('math'), timer_modifier=mod)
    assert qe.timer_seconds == MIN_TIMED_SECONDS == 5
    assert qe.time_remaining == 5.0


def test_minimum_leaves_ordinary_clocks_alone():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.start_quiz('chain', 'math', 1, lambda r: None, timed=True,
                  base_seconds=20, timer_modifier=0.55)
    assert qe.timer_seconds == 11


# ---------------------------------------------------------------- call 5
def test_brokkrs_anvil_maths_quiz_is_untimed():
    """The Mjolnir forge mystery ran on the combat clock: every other
    mystery is untimed."""
    from main import Game
    from game_states import STATE_PLAYER, STATE_QUIZ
    from mystery_system import MysteryAltar
    g = Game(pygame.display.set_mode((64, 64)), player_name='bb4r5')
    g.state = STATE_PLAYER
    g._active_mystery_altar = MysteryAltar('mjolnir', g.player.x, g.player.y)
    g._begin_mystery_challenge()
    assert g.state == STATE_QUIZ
    assert g.quiz_engine.subject == 'math'
    assert g.quiz_engine.timed is False
    before = g.quiz_engine.time_remaining
    g.update(5.0)
    assert g.quiz_engine.time_remaining == before


# ---------------------------------------------------------------- call 6
_NIXON = 'the-nixon-shock-august-15-1971-and-the-birth-of-pure-fiat'
_DOMAIN = re.compile(r'\b[\w-]+\.(com|org|net|io)\b', re.I)


def _econ():
    with open(os.path.join(ROOT, 'data', 'questions', 'economics.json'), encoding='utf-8') as f:
        qs = json.load(f)
    with open(os.path.join(ROOT, 'data', 'question_contexts', 'economics.json'),
              encoding='utf-8') as f:
        blurbs = json.load(f)
    return qs, blurbs


def test_nixon_shock_ladder_keys_no_web_address():
    """The T4 rung's answer was "wtfhappenedin1971.com": not for a kids'
    game. It now asks what the famous 1971 chart shows."""
    qs, blurbs = _econ()
    rungs = [q for q in qs if q.get('topic') == _NIXON]
    assert len(rungs) == 12
    for q in rungs:
        assert not any(_DOMAIN.search(c) for c in q['choices']), q['choices']
        assert 'wtf' not in (q['question'] + q['context']).lower()
    chart = [q for q in rungs if 'paid for that hour' in q['question']]
    assert len(chart) == 1 and chart[0]['tier'] == 4
    assert 'Nixon' in chart[0]['question'] and '1971' in chart[0]['question']
    assert chart[0]['answer'] in chart[0]['choices']
    assert 'wtf' not in blurbs[_NIXON]['context_blurb'].lower()


def test_nixon_shock_blurb_does_not_give_the_chart_answer_away():
    qs, blurbs = _econ()
    blurb = blurbs[_NIXON]['context_blurb'].lower()
    chart = next(q for q in qs if q.get('topic') == _NIXON
                 and 'paid for that hour' in q['question'])
    assert chart['answer'].lower() not in blurb
    for word in ('productivity', 'output per hour', 'stalled', ' pay '):
        assert word not in blurb, word
    assert 'wtfhappenedin1971.com' not in __import__('fantasy_ui')._CONTENT_DOMAINS
