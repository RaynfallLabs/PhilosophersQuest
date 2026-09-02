"""Mutable window / viewport layout globals.

Extracted from main.py so both main and game_render (RenderMixin) can read the
same live values without a circular import. The values are mutated in-place by
`update()` when the window is resized — every reader that uses
``layout.GAME_W`` (rather than a stale ``from layout import GAME_W`` snapshot)
sees the new size on the next access.

VERSION and FPS live here too because main and the debug-overlay renderer both
need them.
"""
from renderer import TILE_SIZE
from ui import LEFT_SIDEBAR_W, SIDEBAR_W

VERSION    = "2.6.0"
FPS        = 60

WINDOW_W   = 1600
WINDOW_H   = 900
MSG_H      = 200
GAME_W     = WINDOW_W - SIDEBAR_W      # non-right-rail play area
MAP_X      = LEFT_SIDEBAR_W
MAP_W      = GAME_W - LEFT_SIDEBAR_W
RIGHT_X    = GAME_W
GAME_H     = WINDOW_H - MSG_H          # 700 px = 17 tiles
VIEWPORT_W = MAP_W // TILE_SIZE
VIEWPORT_H = GAME_H // TILE_SIZE       # 18


def update(w: int, h: int) -> None:
    """Recalculate derived layout globals after a window resize."""
    global WINDOW_W, WINDOW_H, GAME_W, MAP_X, MAP_W, RIGHT_X, GAME_H, VIEWPORT_W, VIEWPORT_H
    WINDOW_W   = w
    WINDOW_H   = h
    GAME_W     = WINDOW_W - SIDEBAR_W
    MAP_X      = LEFT_SIDEBAR_W
    MAP_W      = max(TILE_SIZE * 8, GAME_W - LEFT_SIDEBAR_W)
    RIGHT_X    = GAME_W
    GAME_H     = WINDOW_H - MSG_H
    VIEWPORT_W = MAP_W // TILE_SIZE
    VIEWPORT_H = GAME_H // TILE_SIZE
