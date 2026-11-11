"""Bug bash 3.3.2: the quiz cards mark the right answer, and only after it.

1. A right answer in a grammar quiz showed no green card at all (Brandon,
   2026-11-07, reading a spellbook). The cards are drawn from the screen
   form of each choice (``display_text``: "--" becomes an em dash), and the
   marking compared that form with the bank's answer, so an answer written
   with "--" matched no card: 238 of 1,029 grammar questions, 484 across
   the banks. A wrong pick written with "--" was never marked red either.

2. A new question shows no card as picked.

Brandon, 2026-11-07 playtest: "in some cases, particularly math, one answer
box is highlighted (doesn't seem to always be the right answer)". The quiz
kept the previous question's pick (``last_answer``) into the next question,
and the renderer draws any card whose text matches it as "selected" (gold
border, lighter card). Combat sums share numbers often (about one question
in twelve offers the last answer again), so a card the player had not
touched lit up before they answered.

Headless: the engine invariant, then the real ``_draw_quiz`` with a spy on
each card's state.
"""
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

# Two sums: the second offers the first one's answer ("5") as a choice.
_Q1 = {'tier': 1, 'question': '2 + 3 = ?', 'answer': '5',
       'choices': ['5', '6', '4', '7'], 'topic': 'addition'}
_Q2 = {'tier': 1, 'question': '9 - 1 = ?', 'answer': '8',
       'choices': ['8', '5', '7', '9'], 'topic': 'subtraction'}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path',
                        lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _start_staged_chain(qe):
    """A timed maths chain whose deck is exactly Q1 then Q2."""
    qe._decks[('math', 1)] = [dict(_Q1), dict(_Q2)]
    qe._deck_idx[('math', 1)] = 0
    qe._last_q[('math', 1)] = None
    qe.start_quiz(mode='chain', subject='math', tier=1,
                  callback=lambda result: None, timed=True, wisdom=10)
    assert qe.current_question['question'] == _Q1['question']


def _answer_and_settle(qe, text):
    from quiz_engine import QuizState
    assert qe.answer(text)
    assert qe.state == QuizState.RESULT
    assert qe.last_answer == text            # the result shows the pick
    for _ in range(20):
        if qe.state != QuizState.RESULT:
            break
        qe.update(0.1)


def test_the_next_question_starts_with_no_pick():
    from quiz_engine import QuizEngine, QuizState
    qe = QuizEngine()
    _start_staged_chain(qe)
    _answer_and_settle(qe, '5')
    assert qe.state == QuizState.ASKING
    assert qe.current_question['question'] == _Q2['question']
    assert '5' in qe.current_question['choices']
    assert qe.last_answer == ''


def test_a_threshold_quiz_clears_the_pick_too():
    """Heavy armour, unique spellbooks, Jerome's desk: several questions."""
    from quiz_engine import QuizEngine, QuizState
    qe = QuizEngine()
    qe._decks[('math', 1)] = [dict(_Q1), dict(_Q2)]
    qe._deck_idx[('math', 1)] = 0
    qe._last_q[('math', 1)] = None
    qe.start_quiz(mode='threshold', subject='math', tier=1,
                  callback=lambda result: None, threshold=2, total_qs=2,
                  timed=False)
    _answer_and_settle(qe, '5')
    assert qe.state == QuizState.ASKING
    assert qe.last_answer == ''


def test_no_card_is_drawn_picked_on_the_next_question(monkeypatch):
    import fantasy_ui
    import layout
    from main import Game
    from game_states import STATE_QUIZ
    from quiz_engine import QuizState

    size = (1600, 900)
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    random.seed(7)
    g = Game(screen, player_name='__test_bugbash_332_quiz_highlight__')
    g.on_resize(*size)
    g._resize_grace = 0
    qe = g.quiz_engine
    _start_staged_chain(qe)
    g.state = STATE_QUIZ
    g.quiz_title = 'MELEE ATTACK  --  MATH'

    cards = []
    real = fantasy_ui.draw_choice_button

    def spy(surface, rect, **kw):
        text = kw.get('text')
        cards.append((' '.join(text) if isinstance(text, list) else str(text),
                      bool(kw.get('selected')), bool(kw.get('correct')),
                      bool(kw.get('incorrect'))))
        return real(surface, rect, **kw)

    monkeypatch.setattr(fantasy_ui, 'draw_choice_button', spy)

    # The result of Q1: the right card green, nothing else lit.
    assert qe.answer('5')
    cards.clear()
    g._draw_quiz()
    assert [c[0] for c in cards if c[2]] == ['5']
    assert not any(c[1] or c[3] for c in cards)

    # Q2 is up and offers "5" again: no card may look picked.
    for _ in range(20):
        if qe.state != QuizState.RESULT:
            break
        qe.update(0.1)
    assert qe.state == QuizState.ASKING
    assert qe.current_question['question'] == _Q2['question']
    cards.clear()
    g._draw_quiz()
    assert len(cards) == 4
    assert '5' in [c[0] for c in cards]
    assert not any(c[1] or c[2] or c[3] for c in cards), cards


# ---------------------------------------------------------------------------
# 1. An answer written with "--" (an em dash on screen) still goes green.
# ---------------------------------------------------------------------------

_DASH_Q = {'tier': 1, 'subject': 'grammar', 'topic': 'semicolons',
           'question': "'She packed her bag; and left.' What is wrong?",
           'answer': "a semicolon -- not a comma -- does not take 'and'",
           'choices': ["a semicolon -- not a comma -- does not take 'and'",
                       "the sentence is too short -- it needs a clause",
                       'semicolons need commas after them',
                       'nothing is wrong']}


def _grammar_game(monkeypatch, question):
    """A real Game showing ``question`` as a one-question grammar read,
    with a spy on every card drawn."""
    import fantasy_ui
    import layout
    from main import Game
    from game_states import STATE_QUIZ

    size = (1600, 900)
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    random.seed(11)
    g = Game(screen, player_name='__test_bugbash_332_quiz_highlight__')
    g.on_resize(*size)
    g._resize_grace = 0
    qe = g.quiz_engine
    qe._decks[('grammar', 1)] = [dict(question)]
    qe._deck_idx[('grammar', 1)] = 0
    qe._last_q[('grammar', 1)] = None
    qe.start_quiz(mode='threshold', subject='grammar', tier=1,
                  callback=lambda result: None, threshold=1, total_qs=1)
    assert qe.current_question['question'] == question['question']
    g.state = STATE_QUIZ
    g.quiz_title = 'DECIPHER SPELLBOOK  --  GRAMMAR'

    cards = []
    real = fantasy_ui.draw_choice_button

    def spy(surface, rect, **kw):
        text = kw.get('text')
        cards.append((' '.join(text) if isinstance(text, list) else str(text),
                      bool(kw.get('selected')), bool(kw.get('correct')),
                      bool(kw.get('incorrect'))))
        return real(surface, rect, **kw)

    monkeypatch.setattr(fantasy_ui, 'draw_choice_button', spy)
    return g, cards


def test_a_dashed_right_answer_is_drawn_green(monkeypatch):
    g, cards = _grammar_game(monkeypatch, _DASH_Q)
    assert g.quiz_engine.answer(_DASH_Q['answer'])
    g._draw_quiz()
    green = [c[0] for c in cards if c[2]]
    assert len(green) == 1, cards
    assert '—' in green[0]               # the screen shows the em dash
    assert not any(c[3] for c in cards)


def test_a_dashed_wrong_pick_is_drawn_red_beside_the_green(monkeypatch):
    g, cards = _grammar_game(monkeypatch, _DASH_Q)
    wrong = _DASH_Q['choices'][1]
    assert not g.quiz_engine.answer(wrong)
    g._draw_quiz()
    assert sum(c[2] for c in cards) == 1, cards
    red = [c[0] for c in cards if c[3]]
    assert len(red) == 1 and red[0].startswith('the sentence is too short'), cards


def test_a_dashed_bank_question_goes_green(monkeypatch):
    """The real grammar bank, not a made-up question."""
    import json
    from fantasy_ui import display_text
    with open(os.path.join(ROOT, 'data', 'questions', 'grammar.json'),
              encoding='utf-8') as f:
        bank = json.load(f)
    q = next(q for q in bank if display_text(q['answer']) != q['answer'])
    g, cards = _grammar_game(monkeypatch, dict(q, tier=1))
    assert g.quiz_engine.answer(q['answer'])
    g._draw_quiz()
    assert sum(c[2] for c in cards) == 1, (q['answer'], cards)
