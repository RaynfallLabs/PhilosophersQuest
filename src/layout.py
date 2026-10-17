"""Mutable window / viewport layout globals.

Extracted from main.py so both main and game_render (RenderMixin) can read the
same live values without a circular import. The values are mutated in-place by
`update()` when the window is resized — every reader that uses
``layout.GAME_W`` (rather than a stale ``from layout import GAME_W`` snapshot)
sees the new size on the next access.

``update()`` is also the ONLY place the UI scale is set (``ui_scale``,
_genart/ui/SCALE_PLAN.md): it sets the scale for the window first, then the
derived globals, so the sidebars (``LEFT_SIDEBAR_W`` / ``SIDEBAR_W``) and the
message log (``MSG_H``) grow with it. The map tiles do not scale; the map
simply gets whatever is left.

VERSION and FPS live here too because main and the debug-overlay renderer both
need them.
"""
import ui_scale
from renderer import TILE_SIZE
from ui import LEFT_SIDEBAR_W as LEFT_SIDEBAR_BASE, SIDEBAR_W as SIDEBAR_BASE, RAIL_MIN

VERSION    = "3.1.0"
FPS        = 60

MSG_BASE   = 200                       # message log height at UI scale 1

WINDOW_W   = 1600
WINDOW_H   = 900
UI_SCALE   = 1.0                       # mirror of ui_scale.get(), for reading
LEFT_SIDEBAR_W = LEFT_SIDEBAR_BASE     # left rail width at the current scale
SIDEBAR_W  = SIDEBAR_BASE              # right rail width at the current scale
MSG_H      = MSG_BASE
GAME_W     = WINDOW_W - SIDEBAR_W      # non-right-rail play area
MAP_X      = LEFT_SIDEBAR_W
MAP_W      = GAME_W - LEFT_SIDEBAR_W
RIGHT_X    = GAME_W
GAME_H     = WINDOW_H - MSG_H
VIEWPORT_W = MAP_W // TILE_SIZE
VIEWPORT_H = GAME_H // TILE_SIZE


def update(w: int, h: int) -> None:
    """Set the UI scale for a ``w`` x ``h`` window, then recalculate every
    derived layout global. Scale listeners (fonts, the UI art kit) run here,
    synchronously, if the scale changed."""
    ui_scale.set_for_window(w, h)
    _recompute(w, h)


def _recompute(w: int, h: int) -> None:
    """The derived globals for a ``w`` x ``h`` window at the current scale."""
    global WINDOW_W, WINDOW_H, UI_SCALE, LEFT_SIDEBAR_W, SIDEBAR_W, MSG_H
    global GAME_W, MAP_X, MAP_W, RIGHT_X, GAME_H, VIEWPORT_W, VIEWPORT_H
    UI_SCALE   = ui_scale.get()
    WINDOW_W   = w
    WINDOW_H   = h
    # In compact (below 1280x720) the rails keep at least RAIL_MIN of their
    # width: their text stays at the 16 px floor, so they cannot shrink as
    # fast as the window; the map takes the difference.
    rail = max(ui_scale.get(), RAIL_MIN)
    LEFT_SIDEBAR_W = int(LEFT_SIDEBAR_BASE * rail + 0.5)
    SIDEBAR_W  = int(SIDEBAR_BASE * rail + 0.5)
    MSG_H      = ui_scale.px(MSG_BASE)
    GAME_W     = WINDOW_W - SIDEBAR_W
    MAP_X      = LEFT_SIDEBAR_W
    MAP_W      = max(TILE_SIZE * 8, GAME_W - LEFT_SIDEBAR_W)
    RIGHT_X    = GAME_W
    GAME_H     = WINDOW_H - MSG_H
    VIEWPORT_W = MAP_W // TILE_SIZE
    VIEWPORT_H = GAME_H // TILE_SIZE


def snapshot() -> tuple:
    """Every layout global plus the scale (for tests that must put them back)."""
    return (WINDOW_W, WINDOW_H, ui_scale.get())


def restore(snap: tuple) -> None:
    """Undo to a ``snapshot()``."""
    w, h, s = snap
    ui_scale.set_scale(s)
    _recompute(w, h)


update(WINDOW_W, WINDOW_H)             # module state is self-consistent from import
