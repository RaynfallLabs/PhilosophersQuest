"""Phase 3 of CHAIN_EFFECTS_PLAN (2026-10-03): identify-success orb.

Verifies the first non-chain effect on the ``EffectsRuntime``:

  * The handler is registered under the id ``identify_success_orb``.
  * ``fire()`` activates the handler with an anchor point.
  * The animation drains after its ``duration_ms`` so no leaked
    particles / anchors persist across identify attempts.
  * Reduced-motion mode (``PQ_REDUCED_MOTION=1``) skips orbit sparks
    and uses the shortened static-pulse replacement.
  * The two call sites (item identify + corpse identify) fire the orb
    only in the success branch -- failure (stun) must NOT trigger it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make src/ importable (same convention as the rest of the suite).
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / 'src'))

from effects_runtime import build_default_runtime  # noqa: E402
from effects.identify_orb import IdentifyOrb       # noqa: E402

_SRC = _HERE.parent / 'src'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# Handler registration + runtime wiring
# ---------------------------------------------------------------------------

def test_identify_orb_handler_registered():
    """The default runtime factory registers the identify-success orb
    alongside the three Phase-1 handlers."""
    rt = build_default_runtime()
    assert 'identify_success_orb' in rt.handlers
    assert isinstance(rt.handlers['identify_success_orb'], IdentifyOrb)


def test_identify_orb_config_block_present():
    """``data/ui/effects_config.json`` must declare the orb so the
    handler receives its duration/palette/particle budget."""
    rt = build_default_runtime()
    cfg = rt.effect_config('identify_success_orb')
    assert cfg.get('handler') == 'identify_orb'
    assert cfg.get('scope') == 'one_shot'
    assert cfg.get('duration_ms') == 1200
    assert cfg.get('palette') == 'lavender_white'
    assert cfg.get('particle_budget') == 12
    rm = cfg.get('reduced_motion') or {}
    assert 'orbit_sparks' in (rm.get('disable') or [])
    assert 'expansion_phase' in (rm.get('disable') or [])


# ---------------------------------------------------------------------------
# Lifecycle: fire -> active -> expire
# ---------------------------------------------------------------------------

def test_fire_identify_orb_sets_active():
    """``runtime.fire`` must activate the orb and remember the anchor."""
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 400, 'anchor_y': 300})
    h = rt.handlers['identify_success_orb']
    assert h._active is True
    assert h._anchor_x == 400
    assert h._anchor_y == 300
    # Full-motion path spawns the orbit-spark pool at trigger time.
    assert len(h._particles) == 12


def test_identify_orb_falls_back_to_screen_center():
    """If the caller omits anchor coords, the orb centres on the window."""
    import layout
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {})
    h = rt.handlers['identify_success_orb']
    assert h._anchor_x == layout.WINDOW_W // 2
    assert h._anchor_y == layout.WINDOW_H // 2


def test_identify_orb_expires():
    """After ``duration_ms`` elapses the orb clears all state so a
    stale anchor / particle doesn't leak into the next session."""
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 400, 'anchor_y': 300})
    rt.update(1.3)   # 1300 ms > 1200 ms duration
    h = rt.handlers['identify_success_orb']
    assert h._active is False
    assert h._particles == []
    assert h._anchor_x is None
    assert h._anchor_y is None


def test_identify_orb_mid_animation_still_active():
    """Half way through, the orb is still alive and the particle pool
    is intact -- draw_overlay would paint phase 1 (hover + sparks)."""
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 100, 'anchor_y': 200})
    rt.update(0.5)   # 500 ms -- in phase 1
    h = rt.handlers['identify_success_orb']
    assert h._active is True
    assert len(h._particles) == 12
    assert 400.0 <= h._elapsed_ms <= 600.0


def test_identify_orb_retrigger_restarts_timer():
    """A second fire mid-animation restarts the clock (the second
    caller wins -- stale fires can't glue two orbs end-to-end)."""
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 100, 'anchor_y': 100})
    rt.update(0.8)   # most of the way through
    rt.fire('identify_success_orb', {'anchor_x': 500, 'anchor_y': 500})
    h = rt.handlers['identify_success_orb']
    assert h._active is True
    assert h._elapsed_ms == 0.0
    assert h._anchor_x == 500
    assert h._anchor_y == 500


# ---------------------------------------------------------------------------
# Reduced motion
# ---------------------------------------------------------------------------

def test_identify_orb_reduced_motion(monkeypatch):
    """``PQ_REDUCED_MOTION=1`` short-circuits the orbit spawn + swaps
    the duration for the static-pulse replacement (300 ms)."""
    monkeypatch.setenv('PQ_REDUCED_MOTION', '1')
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 400, 'anchor_y': 300})
    h = rt.handlers['identify_success_orb']
    assert h._active is True
    assert h._reduced_mode is True
    # No orbit sparks spawn in reduced motion.
    assert h._particles == []
    # The reduced-motion path uses the 300 ms static pulse.
    rt.update(0.35)
    assert h._active is False


def test_identify_orb_full_motion_default():
    """Without the env var the orb runs the full 1200 ms animation."""
    # Guard against a stale env var leaking from the previous test.
    os.environ.pop('PQ_REDUCED_MOTION', None)
    rt = build_default_runtime()
    rt.fire('identify_success_orb', {'anchor_x': 400, 'anchor_y': 300})
    h = rt.handlers['identify_success_orb']
    assert h._reduced_mode is False
    rt.update(0.35)   # the reduced-motion window
    assert h._active is True
    rt.update(0.9)    # past 1200 ms total
    assert h._active is False


# ---------------------------------------------------------------------------
# Call-site integration (static grep -- the modules themselves import
# pygame + the full game surface, which the unit suite can't
# instantiate; checking source is the Phase-1 pattern used by
# test_celebrate_on_max_gate.py).
# ---------------------------------------------------------------------------

def test_identify_orb_not_wired_to_identify_item():
    """``game_magic.py::_identify_item`` must NOT fire the orb --
    the lore screen IS the celebration (full-panel reveal of the
    identified item). The orb was competing visually with lore when
    both fired at the same moment. Removed 2026-10-04 after playtest.
    The identify_orb handler stays registered for future non-lore
    effects (e.g. an orb when a non-lore item is identified)."""
    text = _read(_SRC / 'game_magic.py')
    marker = 'def _identify_item'
    assert marker in text
    body = text[text.index(marker):]
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    assert "'identify_success_orb'" not in body, (
        "_identify_item must NOT fire identify_success_orb. The lore "
        "screen is the celebration; the orb competes with it.")
    assert '"identify_success_orb"' not in body


def test_identify_orb_not_wired_to_corpse_identify():
    """``main.py::_start_corpse_identify`` must NOT fire the orb --
    the lore screen is the celebration. Mirrors the item-identify
    decoupling (see test_identify_orb_not_wired_to_identify_item)."""
    text = _read(_SRC / 'main.py')
    marker = 'def _start_corpse_identify'
    assert marker in text
    body = text[text.index(marker):]
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    assert "'identify_success_orb'" not in body, (
        "_start_corpse_identify must NOT fire identify_success_orb. "
        "Lore screen is the celebration.")
    assert '"identify_success_orb"' not in body


def test_identify_orb_not_fired_on_item_failure():
    """The stun branch of ``_identify_item`` must not fire the orb --
    failure is already punished and the orb is a celebration."""
    text = _read(_SRC / 'game_magic.py')
    marker = 'def _identify_item'
    body = text[text.index(marker):]
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    else_idx = body.find('\n            else:')
    assert else_idx != -1
    else_body = body[else_idx:]
    assert 'identify_success_orb' not in else_body, (
        "The failure (stun) branch of _identify_item must NOT fire "
        "the identify_success_orb effect.")


def test_identify_orb_not_fired_on_corpse_failure():
    """Same contract for ``_start_corpse_identify``: no orb on stun."""
    text = _read(_SRC / 'main.py')
    marker = 'def _start_corpse_identify'
    body = text[text.index(marker):]
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    else_idx = body.find('\n            else:')
    assert else_idx != -1
    else_body = body[else_idx:]
    assert 'identify_success_orb' not in else_body, (
        "The failure (stun) branch of _start_corpse_identify must "
        "NOT fire the identify_success_orb effect.")
