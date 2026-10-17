"""display_setup.py -- the game window's first size and Windows DPI awareness.

Bug bash 4, call 15 (UI-08):

* **DPI awareness.** Without it Windows treats the game as a 96-DPI program
  and bitmap-stretches it at 125-150 % display scaling: soft text, and a
  1366x768 laptop at 125 % reports only 1093x614 "logical" pixels.
  ``enable_dpi_awareness()`` asks for per-monitor awareness (v2, then v1,
  then system-wide), and must run BEFORE ``pygame.display`` is initialised.
  The game then sees real pixels and its own UI scale (``ui_scale``) sizes
  the text for the window.
* **The work area.** The window used to open at ``min(1600x900, desktop)``,
  which on a small display is the whole screen, title bar and taskbar
  included. ``initial_window()`` fits the window, frame and all, inside the
  desktop WORK AREA (the screen minus the taskbar) and centres it there.

Everything here degrades to "do nothing" off Windows or if a call fails;
nothing in this module may stop the game from starting.
"""
from __future__ import annotations

import os
import sys

_IS_WINDOWS = sys.platform == 'win32'

# Windows constants
_DPI_CTX_PER_MONITOR_V2 = -4
_DPI_CTX_PER_MONITOR = -3
_PROCESS_PER_MONITOR_DPI_AWARE = 2
_SPI_GETWORKAREA = 0x0030
_WS_OVERLAPPEDWINDOW = 0x00CF0000

_awareness: str | None = None


def enable_dpi_awareness() -> str:
    """Make the process DPI aware (Windows). Returns which mode took:
    'per-monitor-v2', 'per-monitor', 'system', 'already' or 'none'.
    Safe to call more than once; only the first call does anything."""
    global _awareness
    if _awareness is not None:
        return _awareness
    _awareness = 'none'
    if not _IS_WINDOWS:
        return _awareness
    # SDL reads this hint at video init too (SDL 2.24+), so a later SDL
    # that would otherwise reset the awareness agrees with it.
    os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')
    try:
        import ctypes
        user32 = ctypes.windll.user32
        try:
            fn = user32.SetProcessDpiAwarenessContext
            fn.restype = ctypes.c_bool
            fn.argtypes = [ctypes.c_void_p]
            if fn(ctypes.c_void_p(_DPI_CTX_PER_MONITOR_V2)):
                _awareness = 'per-monitor-v2'
                return _awareness
            if fn(ctypes.c_void_p(_DPI_CTX_PER_MONITOR)):
                _awareness = 'per-monitor'
                return _awareness
            if ctypes.GetLastError() == 5:          # ERROR_ACCESS_DENIED: set already
                _awareness = 'already'
                return _awareness
        except AttributeError:                       # before Windows 10 1703
            pass
        try:
            hr = ctypes.windll.shcore.SetProcessDpiAwareness(_PROCESS_PER_MONITOR_DPI_AWARE)
            if hr == 0:
                _awareness = 'per-monitor'
                return _awareness
            if hr == -2147024891:                    # E_ACCESSDENIED: set already
                _awareness = 'already'
                return _awareness
        except (AttributeError, OSError):            # before Windows 8.1
            pass
        if user32.SetProcessDPIAware():
            _awareness = 'system'
    except Exception:
        pass
    return _awareness


def work_area() -> tuple[int, int, int, int] | None:
    """The primary desktop's work area (x, y, w, h) in real pixels: the
    screen without the taskbar. None when it cannot be read."""
    if not _IS_WINDOWS:
        return None
    try:
        import ctypes
        from ctypes import wintypes
        r = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(_SPI_GETWORKAREA, 0, ctypes.byref(r), 0):
            w, h = r.right - r.left, r.bottom - r.top
            if w > 0 and h > 0:
                return r.left, r.top, w, h
    except Exception:
        pass
    return None


def window_frame() -> tuple[int, int, int, int]:
    """(left, top, right, bottom) thickness of a normal resizable window's
    frame and title bar, in real pixels. A conservative guess off Windows."""
    if _IS_WINDOWS:
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            r = wintypes.RECT(0, 0, 0, 0)
            ok = False
            try:
                dpi = user32.GetDpiForSystem()
                ok = user32.AdjustWindowRectExForDpi(ctypes.byref(r), _WS_OVERLAPPEDWINDOW,
                                                     False, 0, dpi)
            except AttributeError:
                pass
            if not ok:
                r = wintypes.RECT(0, 0, 0, 0)
                ok = user32.AdjustWindowRectEx(ctypes.byref(r), _WS_OVERLAPPEDWINDOW, False, 0)
            if ok:
                return -r.left, -r.top, r.right, r.bottom
        except Exception:
            pass
    return 8, 32, 8, 8


def plan_window(default: tuple[int, int], area: tuple[int, int, int, int],
                frame: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Where the window's CLIENT area goes: (x, y, w, h).

    The default size (1600x900) when it fits; otherwise as big as the work
    area ``area`` allows once the ``frame`` (left, top, right, bottom) is
    added. Centred in the work area, so neither the title bar nor the frame
    ever sits under the taskbar or off the screen."""
    ax, ay, aw, ah = area
    fl, ft, fr, fb = frame
    room_w, room_h = max(1, aw - fl - fr), max(1, ah - ft - fb)
    w, h = min(default[0], room_w), min(default[1], room_h)
    x = ax + fl + (room_w - w) // 2
    y = ay + ft + (room_h - h) // 2
    return x, y, w, h


def initial_window(default: tuple[int, int], desktop: tuple[int, int]
                   ) -> tuple[tuple[int, int], tuple[int, int] | None, tuple[int, int]]:
    """((w, h), (x, y) or None, largest client size the work area holds).

    ``desktop`` is pygame's desktop size, the fallback when the work area
    cannot be read (then 48 px are kept clear for a taskbar)."""
    area = work_area()
    known = area is not None
    if not known:
        area = (0, 0, desktop[0], max(1, desktop[1] - 48))
    frame = window_frame()
    x, y, w, h = plan_window(default, area, frame)
    room = (max(1, area[2] - frame[0] - frame[2]), max(1, area[3] - frame[1] - frame[3]))
    return (w, h), ((x, y) if known else None), room


def report(screen_size: tuple[int, int]) -> dict:
    """What the OS says about the window just made, for the log and for a
    one-off check that it really is ``screen_size`` real pixels: the
    awareness mode, the window's DPI and its client rectangle."""
    out = {'awareness': _awareness, 'pygame_size': tuple(screen_size)}
    if not _IS_WINDOWS:
        return out
    try:
        import ctypes
        from ctypes import wintypes
        import pygame
        hwnd = pygame.display.get_wm_info().get('window')
        if hwnd:
            user32 = ctypes.windll.user32
            r = wintypes.RECT()
            if user32.GetClientRect(hwnd, ctypes.byref(r)):
                out['client_size'] = (r.right - r.left, r.bottom - r.top)
            try:
                out['dpi'] = int(user32.GetDpiForWindow(hwnd))
            except AttributeError:
                pass
            wr = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(wr)):
                out['window_rect'] = (wr.left, wr.top, wr.right, wr.bottom)
        area = work_area()
        if area:
            out['work_area'] = area
    except Exception:
        pass
    return out
