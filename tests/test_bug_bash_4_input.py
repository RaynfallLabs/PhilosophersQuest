"""The fourth bug bash (2026-10-16): input and screen text. UI-01/CQ-05,
UI-06, UI-07, UI-10, UI-11, UI-12, UI-13, UI-14, UI-15, UI-25 and Q1.
"""
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _kd(k, uni=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=uni, scancode=0)


class _FrameDone(Exception):
    pass


class _Clock:
    def tick(self, *_a):
        return 16


def _one_frame(monkeypatch, loop, events):
    """Post events, run one pass of a screen's own loop, stop at its flip."""
    def flip(*_a, **_k):
        raise _FrameDone
    monkeypatch.setattr(pygame.display, 'flip', flip)
    pygame.event.clear()
    for e in events:
        pygame.event.post(e)
    try:
        return loop()
    except _FrameDone:
        return None


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    import save_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    return tmp_path


def _game():
    from main import Game
    from game_states import STATE_PLAYER
    g = Game(_screen(), player_name='bb4input')
    g.state = STATE_PLAYER
    return g


# ---------------------------------------------------------------- UI-01 / CQ-05
def test_title_delete_asks_before_erasing(save_dir, monkeypatch):
    """One Del press on the title screen erased the typed hero's save."""
    from welcome_screen import WelcomeScreen
    from save_system import _save_path, save_exists
    open(_save_path('Aldric'), 'wb').write(b'fixture')
    w = WelcomeScreen(_screen(), 'test')
    w.name_buf = 'Aldric'
    _one_frame(monkeypatch, lambda: w.run(_Clock()), [_kd(pygame.K_DELETE)])
    assert save_exists('Aldric'), 'Del alone must not erase'
    assert w._confirm_delete == 'Aldric'
    _one_frame(monkeypatch, lambda: w.run(_Clock()), [_kd(pygame.K_n, 'n')])
    assert save_exists('Aldric') and not w._confirm_delete
    assert w.name_buf == 'Aldric', 'the answer key is not typed into the name'
    _one_frame(monkeypatch, lambda: w.run(_Clock()),
               [_kd(pygame.K_DELETE), _kd(pygame.K_y, 'y')])
    assert not save_exists('Aldric')
    assert w.name_buf == 'Aldric'


def test_title_takes_keypad_enter_and_f11(save_dir, monkeypatch):
    from welcome_screen import WelcomeScreen
    calls = []
    monkeypatch.setattr(pygame.display, 'toggle_fullscreen', lambda: calls.append(1))
    w = WelcomeScreen(_screen(), 'test')
    _one_frame(monkeypatch, lambda: w.run(_Clock()), [_kd(pygame.K_F11)])
    assert calls == [1]
    w.name_buf = 'Brynn'
    out = _one_frame(monkeypatch, lambda: w.run(_Clock()), [_kd(pygame.K_KP_ENTER)])
    assert out is not None and out[0] == 'Brynn'


# ---------------------------------------------------------------- Q1 / UI-07 / UI-12
def _study_at_quiz(q):
    from study_mode import StudyMode
    s = StudyMode(_screen())
    s._questions = [q]
    s._idx = 0
    s._phase = 'quiz'
    return s


def test_study_mode_checks_answers_exactly():
    """Study Mode folded case, so all four case variants of a capitalisation
    question counted as correct."""
    q = {'question': 'Which is right?', 'answer': 'Uncle Jack',
         'choices': ['uncle Jack', 'Uncle jack', 'Uncle Jack', 'uncle jack']}
    s = _study_at_quiz(q)
    s._handle_key(pygame.K_1)
    assert s._last_correct is False
    s = _study_at_quiz(q)
    s._handle_key(pygame.K_3)
    assert s._last_correct is True


def test_study_result_escape_leaves_and_keypad_answers():
    """Results said "Esc: quit" but Esc went on to the next question; the
    keypad 1-4 did not answer."""
    q = {'question': 'Q?', 'answer': 'A', 'choices': ['A', 'B', 'C', 'D']}
    s = _study_at_quiz(q)
    s._handle_key(pygame.K_KP1)
    assert s._phase == 'result' and s._last_correct is True
    s._handle_key(pygame.K_ESCAPE)
    assert s._phase == 'subject'
    s = _study_at_quiz(q)
    s._handle_key(pygame.K_2)
    s._handle_key(pygame.K_KP_ENTER)
    assert s._phase == 'quiz'


def test_study_mode_f11(monkeypatch):
    calls = []
    monkeypatch.setattr(pygame.display, 'toggle_fullscreen', lambda: calls.append(1))
    from study_mode import StudyMode
    assert StudyMode(_screen())._handle_key(pygame.K_F11) is False
    assert calls == [1]


def test_help_lists_f11():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    at = src.index('def _draw_help_screen')
    assert '("F11", "Full screen"' in src[at:at + 4000]


# ---------------------------------------------------------------- UI-10
def test_a_bare_modifier_does_not_close_a_story_popup(save_dir):
    from game_states import STATE_STORY_POPUP, STATE_PLAYER
    g = _game()
    g.state = STATE_STORY_POPUP
    g.popup_next_state = STATE_PLAYER
    for k in (pygame.K_LALT, pygame.K_RSHIFT, pygame.K_LCTRL):
        g.handle_event(_kd(k))
        assert g.state == STATE_STORY_POPUP
    g.handle_event(_kd(pygame.K_SPACE, ' '))
    assert g.state == STATE_PLAYER


# ---------------------------------------------------------------- UI-11
def test_window_x_on_the_death_screen_quits(save_dir):
    from game_states import STATE_DEAD
    g = _game()
    g.state = STATE_DEAD
    assert g.handle_event(pygame.event.Event(pygame.QUIT)) is False
    assert g._window_closed is True
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert "and not getattr(game, '_window_closed', False):\n            continue" in src


# ---------------------------------------------------------------- UI-13
def test_pipe_key_opens_divine_intercession(save_dir):
    g = _game()
    calls = []
    g._start_divine_intercession = lambda: calls.append('di')
    g._start_pray = lambda: calls.append('pray')
    g.handle_event(_kd(pygame.K_BACKSLASH, '|'))
    assert calls == ['di']


# ---------------------------------------------------------------- UI-14
def test_keypad_enter_is_enter_and_keypad_arrows_move(save_dir):
    from game_states import STATE_HELP
    g = _game()
    seen = []
    g._help_input = lambda k: seen.append(k)
    g.state = STATE_HELP
    g.handle_event(_kd(pygame.K_KP_ENTER))
    assert seen == [pygame.K_RETURN]
    from game_states import STATE_PLAYER
    g.state = STATE_PLAYER
    moves = []
    g._do_move = lambda dx, dy: moves.append((dx, dy))
    for k in (pygame.K_KP8, pygame.K_KP2, pygame.K_KP4, pygame.K_KP6):
        g.handle_event(_kd(k))
    assert moves == [(0, -1), (0, 1), (-1, 0), (1, 0)]


# ---------------------------------------------------------------- UI-06 / UI-15
def _qe(mode, chain=0, asking=True):
    from quiz_engine import QuizMode, QuizState
    return types.SimpleNamespace(mode=getattr(QuizMode, mode), chain=chain,
                                 state=QuizState.ASKING if asking else QuizState.RESULT)


def test_combat_footer_has_no_cancel_at_chain_zero():
    """At chain 0 Space ends the attack with nothing, like Esc; the footer
    offered it as "Cancel"."""
    from game_render import RenderMixin
    keys0 = [p[0:2] for p in RenderMixin._quiz_footer_pairs(_qe('CHAIN', 0), True, True)]
    assert ('Space', 'Cancel') not in keys0 and all(k != 'Space' for k, _ in keys0)
    assert ('Esc', 'Abort') in keys0
    keys3 = [p[0:2] for p in RenderMixin._quiz_footer_pairs(_qe('CHAIN', 3), True, False)]
    assert ('Space', 'Strike Now') in keys3


def test_other_quiz_footers_list_esc_and_space():
    from game_render import RenderMixin
    th = [p[0:2] for p in RenderMixin._quiz_footer_pairs(_qe('THRESHOLD'), False, False)]
    assert th == [('1-4', 'Answer'), ('Esc', 'Give Up')]
    ch = [p[0:2] for p in RenderMixin._quiz_footer_pairs(_qe('ESCALATOR_CHAIN', 2), False, True)]
    assert ch == [('1-4', 'Answer'), ('Space', 'Stop Here'), ('C', 'Context'), ('Esc', 'Give Up')]
    res = [p[0:2] for p in RenderMixin._quiz_footer_pairs(_qe('THRESHOLD', asking=False), False, True)]
    assert res == [('C', 'Context')]


# ---------------------------------------------------------------- UI-25
def test_end_screen_accuracy_reads_as_of_total():
    from game_render import RenderMixin
    assert RenderMixin._end_accuracy_text(4, 5) == '4 of 9   (44%)'
    assert RenderMixin._end_accuracy_text(0, 0) == '0 of 0   (0%)'
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'Correct  /  Wrong' not in src
