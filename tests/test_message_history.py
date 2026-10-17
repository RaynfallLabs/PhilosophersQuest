"""Bug bash 4, call 16 (UI-24): L opens a scrollable message history.

The log used to keep 60 entries and show about seven, with no way back.
Now it keeps 500, and L opens them all in a kit modal at the newest line;
Up/Down/PgUp/PgDn/Home/End scroll it, L / Esc / Enter close it. The screen
itself is in the UI gates (capture scene ``menu_message_log``).
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame

pygame.init()


def _game():
    screen = pygame.display.set_mode((1280, 720))
    import layout
    layout.update(1280, 720)
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(2)
    g = Game(screen, player_name='__test_message_history__')
    g.state = STATE_PLAYER
    return g


def _key(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0))


def test_the_log_keeps_enough_history():
    from ui import MessageLog
    log = MessageLog()
    for i in range(700):
        log.add(f"line {i}")
    assert len(log.entries) == 500
    assert log.entries[0][0] == "line 200" and log.entries[-1][0] == "line 699"


def test_L_opens_the_history_at_the_newest_line_and_scrolls():
    from game_states import STATE_MESSAGE_LOG, STATE_PLAYER
    g = _game()
    for i in range(120):
        g.add_message(f"Message number {i}.", 'info')
    _key(g, pygame.K_l, 'l')
    assert g.state == STATE_MESSAGE_LOG
    g.render()
    end = g._message_log_scroll
    assert end > 0, "it should open scrolled to the newest line"
    _key(g, pygame.K_UP)
    g.render()
    assert g._message_log_scroll == end - 1
    _key(g, pygame.K_HOME)
    g.render()
    assert g._message_log_scroll == 0
    _key(g, pygame.K_PAGEDOWN)
    g.render()
    assert 0 < g._message_log_scroll <= end
    _key(g, pygame.K_END)
    g.render()
    assert g._message_log_scroll == end
    _key(g, pygame.K_l, 'l')
    assert g.state == STATE_PLAYER
    _key(g, pygame.K_l, 'l')
    _key(g, pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER


def test_opening_the_history_takes_no_turn():
    g = _game()
    t = g.turn_count
    _key(g, pygame.K_l, 'l')
    _key(g, pygame.K_ESCAPE)
    assert g.turn_count == t


def test_history_is_listed_in_help():
    from game_states import STATE_HELP
    g = _game()
    g.state = STATE_HELP
    seen = []
    real_fit, real_blit = g._fit_line, g._ui_blit_text

    def fit(text, *a, **k):
        seen.append(text)
        return real_fit(text, *a, **k)

    def blit(text, *a, **k):
        seen.append(text)
        return real_blit(text, *a, **k)
    g._fit_line, g._ui_blit_text = fit, blit
    g.render()
    assert 'Message history' in seen
