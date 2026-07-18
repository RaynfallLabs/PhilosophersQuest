"""Crowded menus must scroll (2026-06-07).

draw_menu now AUTO-FOLLOWS the selected row so any overflowing cursor menu keeps
the selection on-screen with no per-caller scroll plumbing; letter shortcuts
still cover a-z, while the cursor/Enter path can reach long inventories.
Headless (SDL dummy) -- these guard the scroll math, not the pixels.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
pygame.init()

from fantasy_ui import draw_menu


def _entries(n, sel):
    return [{'name': f'Item {i}', 'detail': 'x' * 40,
             'selected': i == sel, 'row_style': 'text'} for i in range(n)]


def _fonts():
    return pygame.font.SysFont('consolas', 20), pygame.font.SysFont('consolas', 16)


def test_draw_menu_autoscrolls_to_selection_near_bottom():
    surf = pygame.Surface((1000, 700))
    fmd, fsm = _fonts()
    vis, tot, sc = draw_menu(surf, title='T', entries=_entries(40, 38),
                             font_md=fmd, font_sm=fsm, center_in=(1000, 700),
                             row_style='text')
    assert tot == 40
    assert sc > 0, "should scroll down to reveal selection 38"
    assert sc <= 38, "scroll must never pass the selection"
    assert sc <= 38 < sc + vis, "selected row must be inside the visible window"


def test_draw_menu_does_not_scroll_when_everything_fits():
    surf = pygame.Surface((1000, 700))
    fmd, fsm = _fonts()
    _, _, sc = draw_menu(surf, title='T', entries=_entries(3, 1),
                         font_md=fmd, font_sm=fsm, center_in=(1000, 700),
                         row_style='text')
    assert sc == 0


def test_move_menu_cursor_clamps_to_full_list():
    from main import Game
    g = Game.__new__(Game)
    assert g._move_menu_cursor(0, pygame.K_UP, 10) == 0       # clamp low
    assert g._move_menu_cursor(0, pygame.K_DOWN, 10) == 1
    assert g._move_menu_cursor(5, pygame.K_HOME, 10) == 0
    assert g._move_menu_cursor(0, pygame.K_END, 10) == 9      # last of 10
    assert g._move_menu_cursor(0, pygame.K_END, 100) == 99    # arrows reach beyond z
    assert g._move_menu_cursor(0, pygame.K_DOWN, 0) == 0      # empty list safe
