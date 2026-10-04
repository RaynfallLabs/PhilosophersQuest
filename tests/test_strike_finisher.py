"""Strike finisher -- end-of-attack flourish (2026-10-04).

Logic tests only: tier choice, lifetime, reduced motion, and the
"map area only" paint guarantee. How it LOOKS needs a play-test.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))

import layout  # noqa: E402
from effects.strike_finisher import StrikeFinisher  # noqa: E402
from effects_runtime import build_default_runtime  # noqa: E402

_SHARP = (240, 220, 80)


def _ctx(chain, damage=10, killed=False, rank='', reduced=False):
    return {'chain': chain, 'damage': damage, 'killed': killed,
            'rank_name': rank, 'rank_color': _SHARP,
            'target_name': 'Giant Rat', '_reduced_motion': reduced}


def test_registered_in_default_runtime_with_config():
    rt = build_default_runtime()
    assert isinstance(rt.handlers.get('strike_finisher'), StrikeFinisher)
    cfg = rt.effect_config('strike_finisher')
    assert cfg.get('durations_ms', {}).get('big') <= 900, \
        "the flourish must stay under a second"
    rt.fire('strike_finisher', _ctx(7, rank='Sharp'))
    assert rt.handlers['strike_finisher'].active


def test_tier_selection():
    h = StrikeFinisher()
    assert h.tier_for(0, '') == 'miss'
    assert h.tier_for(2, '') == 'light'
    assert h.tier_for(7, 'Sharp') == 'ranked'
    assert h.tier_for(23, 'Mythic') == 'big'
    assert h.tier_for(h.big_chain, 'Genius') == 'big'


def test_lines_for_hit_miss_and_kill():
    h = StrikeFinisher()
    h.trigger(_ctx(0))
    assert (h._top_line, h._main_line) == ('', 'Miss')
    h.trigger(_ctx(2, damage=9))
    assert (h._top_line, h._main_line) == ('', '9 Damage')
    h.trigger(_ctx(7, damage=84, rank='Sharp'))
    assert (h._top_line, h._main_line) == ('Sharp  x7', '84 Damage')
    h.trigger(_ctx(7, damage=84, killed=True, rank='Sharp'))
    assert h._main_line == 'Giant Rat Slain'


def test_lifetime_and_restart():
    h = StrikeFinisher()
    assert not h.active
    h.trigger(_ctx(7, rank='Sharp'))
    assert h.active
    h.update(0.4, False)
    assert h.active, "750 ms flourish still running at 400 ms"
    h.trigger(_ctx(7, rank='Sharp'))          # re-trigger restarts
    h.update(0.5, False)
    assert h.active
    h.update(0.3, False)
    assert not h.active
    # A new quiz session starting must not cut the flourish short.
    h.trigger(_ctx(3, rank='Solid'))
    h.reset_scope(123)
    assert h.active


def test_reduced_motion_is_short_and_static():
    h = StrikeFinisher()
    h.trigger(_ctx(23, rank='Mythic', reduced=True))
    assert h._total_ms <= h.rm_static_ms
    h.update(h.rm_static_ms / 1000.0 + 0.01, True)
    assert not h.active


def test_draws_only_inside_the_map_area():
    layout.update(1280, 720)
    sentinel = (1, 2, 3)
    for chain, rank in ((0, ''), (2, ''), (7, 'Sharp'), (23, 'Mythic')):
        for killed in (False, True):
            h = StrikeFinisher()
            h.trigger(_ctx(chain, damage=12846, killed=killed, rank=rank))
            for step in (0.02, 0.2, 0.3):
                h.update(step, False)
                surf = pygame.Surface((1280, 720))
                surf.fill(sentinel)
                h.draw_overlay(surf, False)
                area = h.map_rect()
                # Left sidebar, right rail and message log stay untouched.
                for x, y in ((area.x - 1, 100), (area.right, 100),
                             (area.centerx, area.bottom),
                             (0, 0), (1279, 719)):
                    if 0 <= x < 1280 and 0 <= y < 720:
                        assert surf.get_at((x, y))[:3] == sentinel, (chain, x, y)
    # At least one frame of a ranked hit actually paints something.
    h = StrikeFinisher()
    h.trigger(_ctx(7, damage=84, rank='Sharp'))
    h.update(0.2, False)
    surf = pygame.Surface((1280, 720))
    surf.fill(sentinel)
    h.draw_overlay(surf, False)
    area = h.map_rect()
    crop = surf.subsurface(area)
    assert pygame.mask.from_threshold(
        crop, sentinel, (1, 1, 1, 255)).count() < area.w * area.h
