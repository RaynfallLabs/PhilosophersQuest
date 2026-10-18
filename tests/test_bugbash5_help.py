"""Bug bash 5 (2026-10-17): command help text. JNL-15."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


def _help_rows():
    """Draw the real help screen at the minimum window and return every
    description line it actually drew."""
    from main import Game
    screen = pygame.display.set_mode((1280, 720))
    g = Game(screen, player_name='__test_help__')
    drawn = []
    real_fit, real_wrap = g._fit_line, g._ui_wrap_text

    def fit(text, *a, **k):
        font, shown = real_fit(text, *a, **k)
        assert shown == text, f'help row cut at 1280x720: {shown!r}'
        drawn.append(text)
        return font, shown

    def wrap(text, *a, **k):
        drawn.append(text)
        return real_wrap(text, *a, **k)
    g._fit_line, g._ui_wrap_text = fit, wrap
    g._draw_help_screen()
    return drawn


def test_help_names_the_journal_your_story_and_missed_questions():
    rows = _help_rows()
    assert 'Encyclopedia, Journal (h)' in rows
    assert 'Your Story (end of run)' in rows
    assert 'Missed Questions' in rows
    assert 'Study journal' not in rows
    # Nothing else fell off the bottom when the new row went in.
    for must in ('Read scroll or book', 'Message history', 'Cancel / close', 'Pet menu'):
        assert must in rows, must


def test_the_old_study_journal_name_is_gone_everywhere():
    for rel in ('src/game_render.py', 'src/game_input.py', 'src/main.py',
                'docs/systems/ui.md'):
        assert 'study journal' not in _read(*rel.split('/')).lower(), rel


# ---------------------------------------------------------------- INT-14
def test_the_heart_weighing_bestiary_line_does_not_name_karma():
    from game_render import monster_trait_lines
    lines = monster_trait_lines({'id': 'x', 'name': 'X', 'weighs_heart': True})
    heart = [ln for ln in lines if 'heart' in ln.lower()]
    assert heart == ['Weighs the heart of whoever it fights, and a heavy heart feeds it.']
    assert not any('karma' in ln.lower() for ln in lines)
