"""A bare QUIT event must not silently end a run (2026-06-08).

The game closed twice mid-play with NO crash artifacts -- faulthandler was armed
and dumped nothing, no traceback, no error log, clean exit. That rules out a
native crash: the only way the loop ends is handle_event() returning False, i.e.
a QUIT event. A window-X is deliberate, but a SPURIOUS OS/display event (monitor
sleep, focus loss, RDP, screensaver) posting QUIT would vanish the run for no
reason.

Fix: a bare QUIT routes to the VISIBLE confirm-exit dialog (and is logged); only
a CONFIRMED quit (via that dialog, which sets _quit_confirmed) actually exits.
The death/victory screens still exit straight to the welcome screen.
"""
import os

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

from game_states import (STATE_CONFIRM_EXIT, STATE_DEAD, STATE_PLAYER,
                         STATE_QUIZ, STATE_VICTORY)
from main import Game

pygame.init()


def _game(state, confirmed=False):
    g = Game.__new__(Game)
    g.state = state
    g._quit_confirmed = confirmed
    return g


def _quit_event():
    return pygame.event.Event(pygame.QUIT)


def test_spurious_quit_during_play_routes_to_confirm_not_exit():
    g = _game(STATE_PLAYER)
    assert g.handle_event(_quit_event()) is True      # does NOT end the loop
    assert g.state == STATE_CONFIRM_EXIT              # shows the dialog instead


def test_quit_mid_quiz_does_not_vanish_the_run():
    g = _game(STATE_QUIZ)
    assert g.handle_event(_quit_event()) is True
    assert g.state == STATE_CONFIRM_EXIT


def test_confirmed_quit_actually_exits():
    g = _game(STATE_CONFIRM_EXIT, confirmed=True)
    assert g.handle_event(_quit_event()) is False     # deliberate -> ends the loop


def test_quit_on_death_or_victory_exits_to_welcome():
    for st in (STATE_DEAD, STATE_VICTORY):
        g = _game(st)
        assert g.handle_event(_quit_event()) is False


def test_confirm_exit_yes_sets_confirmed_flag():
    """Choosing 'Save & exit' must mark the quit confirmed so the QUIT it posts
    is honored rather than bounced back to the dialog (which would be an infinite
    loop)."""
    g = _game(STATE_CONFIRM_EXIT)
    g._save_on_quit = False
    # Suppress the actual event post / save deletion side effects:
    posted = []
    _orig_post = pygame.event.post
    pygame.event.post = lambda e: posted.append(e)
    try:
        g._confirm_exit_input(pygame.K_RETURN)
    finally:
        pygame.event.post = _orig_post
    assert g._quit_confirmed is True
    assert g._save_on_quit is True
    assert posted and posted[0].type == pygame.QUIT
