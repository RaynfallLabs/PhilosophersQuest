"""ui_scale.py -- the one UI scale factor (see _genart/ui/SCALE_PLAN.md).

On big windows menus and text grow; at 1280x720 and below they are exactly
the size they always were. The scale is derived from the window size by
``scale_for`` and set ONLY by ``layout.update(w, h)`` (through
``set_for_window``); everything else reads it.

    r = min(W / 1280, H / 720)       # the tighter axis decides
    s = (1 + r) / 2                  # grow at half the rate of the window
    s = round(s * 16) / 16           # 1/16 steps (exact floats, bounded caches)
    s = clamp(s, 1.0, 2.0)

1280x720 -> 1.0, 1600x900 -> 1.125, 1920x1080 -> 1.25, 2560x1440 -> 1.5,
3440x1440 -> 1.5, 3840x2160 -> 2.0 (the cap).

``px(n)`` scales a layout length and ``font_px(size)`` a font size; both are
the identity at scale 1.0. Modules that keep something sized by the scale
(the font cache, the UI art kit) register a listener with ``add_listener``;
listeners run synchronously when the scale changes, i.e. inside
``layout.update`` during event handling -- never inside a draw call.

This module imports nothing from the game, so anything may import it.
"""
from __future__ import annotations

BASE_W, BASE_H = 1280, 720
MIN_SCALE, MAX_SCALE = 1.0, 2.0
STEPS = 16                      # quantisation: 1/16

_scale: float = MIN_SCALE
_generation: int = 0            # bumps on every change (cheap staleness check)
_listeners: list = []


def scale_for(w: int, h: int) -> float:
    """The UI scale for a window of ``w`` x ``h`` pixels."""
    if w <= 0 or h <= 0:
        return MIN_SCALE
    r = min(w / BASE_W, h / BASE_H)
    s = round((1.0 + r) / 2.0 * STEPS) / STEPS
    return max(MIN_SCALE, min(MAX_SCALE, s))


def get() -> float:
    """The current UI scale."""
    return _scale


def generation() -> int:
    """A counter that changes whenever the scale does."""
    return _generation


def px(n) -> int:
    """Layout length ``n`` (as at 1280x720) at the current scale, in whole
    pixels. The identity at scale 1.0; rounds half away from zero."""
    v = n * _scale
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def font_px(size) -> int:
    """Font size ``size`` (as at 1280x720) at the current scale."""
    return max(1, int(size * _scale + 0.5))


def add_listener(fn) -> None:
    """Call ``fn(new_scale)`` whenever the scale changes (once per change)."""
    if fn not in _listeners:
        _listeners.append(fn)


def remove_listener(fn) -> None:
    if fn in _listeners:
        _listeners.remove(fn)


def set_scale(s: float) -> bool:
    """Set the scale directly (``layout.update`` / tests). Returns True if it
    changed, after the listeners have run."""
    global _scale, _generation
    s = float(s)
    if s == _scale:
        return False
    _scale = s
    _generation += 1
    for fn in list(_listeners):
        try:
            fn(s)
        except Exception:           # a cache that fails to rebuild never stops a resize
            import logging
            logging.getLogger(__name__).exception("ui_scale listener %r failed", fn)
    return True


def set_for_window(w: int, h: int) -> bool:
    """Set the scale for a window of ``w`` x ``h``. Returns True if it changed."""
    return set_scale(scale_for(w, h))
