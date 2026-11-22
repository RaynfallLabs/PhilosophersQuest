"""The fog is drawn a run at a time, never a tile at a time (3.6.0).

At 2560x1440 the map is some 4,000 tiles, most of them never seen. One rect
for each was over a third of every frame, behind every menu as in play, and
put the trader's Sell screen over its frame budget.
"""
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import renderer  # noqa: E402
from dungeon import FLOOR  # noqa: E402

T, W, H = 8, 40, 12


def _draw(monkeypatch, seen=(), explored=()):
    screen = pygame.Surface((W * T, H * T))
    r = renderer.Renderer.__new__(renderer.Renderer)
    r.screen, r.map_tile_size = screen, T
    r.view_origin_x = r.view_origin_y = r.map_offset_x = r.map_offset_y = 0
    r._get_env_sprite = lambda name: None
    r.world_to_screen = lambda x, y: (x * T, y * T)
    r._draw_fixtures = r._draw_marks = lambda *a, **k: None
    floor = types.SimpleNamespace(width=W, height=H, explored=set(explored),
                                  tiles=[[FLOOR] * W for _ in range(H)])
    screen.fill((255, 0, 255))
    calls = []
    real = pygame.draw.rect

    def rect(*a, **k):
        calls.append(a[1])
        return real(*a, **k)
    monkeypatch.setattr(renderer.pygame.draw, 'rect', rect)
    r.draw_dungeon(floor, set(seen))
    return screen, calls


def test_an_unseen_floor_is_one_rect_a_row(monkeypatch):
    _screen, calls = _draw(monkeypatch)
    assert len(calls) == H


@pytest.mark.parametrize('seen,explored', [
    ((), ()),
    (((0, 0), (W - 1, 0), (7, 3)), ((8, 3), (20, 5))),
    (tuple((x, 4) for x in range(W)), ((0, 6), (W - 1, 6), (1, H - 1))),
])
def test_every_tile_keeps_its_own_colour(monkeypatch, seen, explored):
    screen, _calls = _draw(monkeypatch, seen, explored)
    for y in range(H):
        for x in range(W):
            want = (renderer._VISIBLE[FLOOR] if (x, y) in seen
                    else renderer._EXPLORED[FLOOR] if (x, y) in explored
                    else renderer._UNEXPLORED)
            for px, py in ((0, 0), (T - 1, T - 1)):
                got = tuple(screen.get_at((x * T + px, y * T + py)))[:3]
                assert got == tuple(want)[:3], (x, y)
