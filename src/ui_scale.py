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

COMPACT (bug bash 4, call 15). 1280x720 is the supported floor. Below it
(a small laptop at 125-150 % reports about 1093x614; a portrait monitor is
1080 wide) the scale goes BELOW 1.0 at the window's own rate, so a layout
built for 1280x720 fits:

    s = floor(r * 16) / 16,  clamped to >= COMPACT_MIN (0.75)

1093x614 -> 0.8125, 1080x1920 -> 0.8125, 960x540 and below -> 0.75. Layout
lengths shrink with it; fonts shrink too but never below TEXT_FLOOR (16 px,
the readable floor of DESIGN_RULES 3), so no text gets smaller than the
smallest text at 1280x720.

``px(n)`` scales a layout length and ``font_px(size)`` a font size; both are
the identity at scale 1.0. Modules that keep something sized by the scale
(the font cache, the UI art kit) register a listener with ``add_listener``;
listeners run synchronously when the scale changes, i.e. inside
``layout.update`` during event handling -- never inside a draw call.

This module imports nothing from the game, so anything may import it.
"""
from __future__ import annotations

import math

BASE_W, BASE_H = 1280, 720
MIN_SCALE, MAX_SCALE = 1.0, 2.0  # the range from the supported floor (1280x720) up
COMPACT_MIN = 0.75              # the smallest compact scale (below 1280x720)
TEXT_FLOOR = 16                 # no font shrinks below this in compact (DESIGN_RULES 3)
STEPS = 16                      # quantisation: 1/16

_scale: float = MIN_SCALE
_generation: int = 0            # bumps on every change (cheap staleness check)
_listeners: list = []


def scale_for(w: int, h: int) -> float:
    """The UI scale for a window of ``w`` x ``h`` pixels."""
    if w <= 0 or h <= 0:
        return MIN_SCALE
    r = min(w / BASE_W, h / BASE_H)
    if r < 1.0:
        # Compact: shrink at the window's rate (rounded DOWN, so a layout
        # built for 1280x720 always fits), down to COMPACT_MIN.
        return max(COMPACT_MIN, min(MIN_SCALE, math.floor(r * STEPS + 1e-9) / STEPS))
    s = round((1.0 + r) / 2.0 * STEPS) / STEPS
    return max(MIN_SCALE, min(MAX_SCALE, s))


def is_compact() -> bool:
    """True below the supported floor (the scale is under 1.0)."""
    return _scale < MIN_SCALE


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
    """Font size ``size`` (as at 1280x720) at the current scale. In compact
    (scale below 1.0) a font never drops below ``TEXT_FLOOR`` px, or below
    its own size if that is smaller."""
    v = max(1, int(size * _scale + 0.5))
    if _scale < MIN_SCALE:
        v = max(v, min(int(size), TEXT_FLOOR))
    return v


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
