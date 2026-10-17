"""Bug bash 4, call 15 (UI-08): the window opens inside the desktop WORK
AREA (never over the taskbar), and the process is made DPI aware before the
display starts.

The real-window check was run by hand on Brandon's PC (3440x1440, 100 %,
work area 3440x1392): per-monitor-v2 awareness took, the client area is
exactly 1600x900 real pixels and the window rect (with its frame) sits
inside the work area. A laptop at 125-150 % needs Brandon's eyes.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import display_setup  # noqa: E402

FRAME = (8, 31, 8, 8)


def _outer(client, frame=FRAME):
    x, y, w, h = client
    return x - frame[0], y - frame[1], x + w + frame[2], y + h + frame[3]


def test_default_size_when_it_fits_centred_in_the_work_area():
    area = (0, 0, 3440, 1392)                          # taskbar 48 px at the bottom
    x, y, w, h = display_setup.plan_window((1600, 900), area, FRAME)
    assert (w, h) == (1600, 900)
    left, top, right, bottom = _outer((x, y, w, h))
    assert left >= 0 and top >= 0 and right <= 3440 and bottom <= 1392
    assert abs((left + right) / 2 - 1720) <= 1


def test_a_small_display_fills_the_work_area_not_the_taskbar():
    """The old code opened at min(1600x900, desktop) = the whole 1093x614
    screen, title bar and taskbar included."""
    area = (0, 0, 1093, 566)                           # 1093x614 minus a 48 px taskbar
    x, y, w, h = display_setup.plan_window((1600, 900), area, FRAME)
    left, top, right, bottom = _outer((x, y, w, h))
    assert (left, top, right, bottom) == (0, 0, 1093, 566)
    assert (w, h) == (1093 - 16, 566 - 39)


def test_a_taskbar_on_the_left_or_top_is_respected():
    area = (62, 40, 1304, 728)
    x, y, w, h = display_setup.plan_window((1600, 900), area, FRAME)
    left, top, right, bottom = _outer((x, y, w, h))
    assert left >= 62 and top >= 40 and right <= 62 + 1304 and bottom <= 40 + 728


def test_initial_window_never_exceeds_the_room_it_reports():
    (w, h), pos, room = display_setup.initial_window((1600, 900), (1093, 614))
    assert w <= room[0] and h <= room[1]
    assert w <= 1600 and h <= 900


def test_dpi_awareness_is_requested_once_and_reports_its_mode():
    mode = display_setup.enable_dpi_awareness()
    assert mode in ('per-monitor-v2', 'per-monitor', 'system', 'already', 'none')
    assert display_setup.enable_dpi_awareness() == mode
    if sys.platform == 'win32':
        assert mode != 'none'
        assert os.environ.get('SDL_WINDOWS_DPI_AWARENESS') == 'permonitorv2'


def test_main_sets_dpi_awareness_before_the_display_starts(monkeypatch):
    """main() asks for DPI awareness before pygame.init (awareness set after
    the window exists does not resize it). Recorded through the real call
    order: main() is stopped at its first pygame.init."""
    import pygame
    import main as game_main
    calls = []

    class Stop(Exception):
        pass

    monkeypatch.setattr(display_setup, 'enable_dpi_awareness',
                        lambda: calls.append('dpi') or 'none')

    def fake_init():
        calls.append('init')
        raise Stop
    monkeypatch.setattr(pygame, 'init', fake_init)
    try:
        game_main.main()
    except Stop:
        pass
    assert calls[:2] == ['dpi', 'init']
