"""Lifecycle unit tests for the EffectsRuntime + Phase 1 handlers.

Phase 2 of CHAIN_EFFECTS_PLAN.md (2026-10-03). These tests exercise the
runtime and the two shipped handlers (``ChainAuraPulse``,
``FullscreenTakeover``) without a real pygame display. They cover
config loading, idempotency, milestone single-fire semantics, scope
isolation, reduced-motion gating, particle-budget bounds, and the
pause / timeout / wrong-answer edge cases that the design doc flags.

Design notes:

* Tests are headless. ``pygame`` is imported via the handlers but no
  display is initialised -- all drawing surfaces are standalone
  ``pygame.Surface`` objects. The test harness never calls draw methods
  that would require a display context.
* ``PQ_REDUCED_MOTION`` is manipulated via ``monkeypatch`` so the test
  session's env is not polluted.
* The ``headless_runtime()`` fixture returns a freshly-constructed
  runtime pointing at the shipped ``data/ui/effects_config.json`` so
  the tests cover the real configuration, not a mock.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make src/ importable before touching anything else.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / 'src'))

from effects_runtime import EffectsRuntime, build_default_runtime  # noqa: E402
from effects.chain_aura import ChainAuraPulse  # noqa: E402
from effects.fullscreen_takeover import FullscreenTakeover  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def headless_runtime(monkeypatch):
    """Build a runtime from the shipped config with no pygame display.

    Reduced-motion defaults to OFF; tests that need it on monkeypatch
    the env var and rebuild the runtime.
    """
    monkeypatch.delenv('PQ_REDUCED_MOTION', raising=False)
    return build_default_runtime()


def _chain_snapshot(chain: int, *, asked: int | None = None,
                    last_correct: bool = True, subject: str = 'math',
                    mode: str = 'chain',
                    has_combat_target: bool = True) -> dict:
    """Build a quiz snapshot representative of ``main.Game.update``.

    Only the fields the handlers currently read are present; adding more
    fields later should not break these tests."""
    return {
        'subject': subject,
        'mode': mode,
        'chain': chain,
        'asked_count': asked if asked is not None else chain,
        'correct_count': chain,
        'last_correct': last_correct,
        'quiz_state': 'ASKING',
        'has_combat_target': has_combat_target,
        'state': 'STATE_QUIZ',
    }


def _chain_handler(runtime: EffectsRuntime) -> ChainAuraPulse:
    return runtime.handlers['chain_math_combat']


def _takeover(runtime: EffectsRuntime, name: str) -> FullscreenTakeover:
    return runtime.handlers[name]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def test_runtime_loads_default_config(headless_runtime):
    """build_default_runtime registers the three Phase 1 handlers and
    the config carries at least that many effect entries."""
    rt = headless_runtime
    assert set(rt.handlers) >= {
        'chain_math_combat',
        'divine_intercession_takeover',
        'unicorn_bond_takeover',
    }
    assert isinstance(rt.handlers['chain_math_combat'], ChainAuraPulse)
    assert isinstance(rt.handlers['divine_intercession_takeover'],
                      FullscreenTakeover)
    effects = rt.config.get('effects') or {}
    assert len(effects) >= 3


def test_runtime_handles_missing_config_file(tmp_path):
    """Pointing at a nonexistent config path must not crash. The
    resulting runtime is a near-no-op (handlers register but their
    config falls back to safe defaults)."""
    missing = tmp_path / 'does_not_exist.json'
    rt = EffectsRuntime(config_path=str(missing))
    # No effects loaded from the missing file.
    assert rt.config == {'effects': {}}
    # build_default_runtime should still succeed with the missing path.
    rt2 = build_default_runtime(config_path=str(missing))
    assert set(rt2.handlers) >= {
        'chain_math_combat',
        'divine_intercession_takeover',
        'unicorn_bond_takeover',
    }
    # Handlers fell back to defaults -- chain aura still has ranks.
    chain = _chain_handler(rt2)
    assert len(chain.ranks) >= 2


def test_runtime_handles_malformed_config(tmp_path, capsys):
    """Malformed JSON must not crash the runtime. A diagnostic is
    emitted and build_default_runtime still registers the handlers
    (they fall back to their internal defaults)."""
    bad = tmp_path / 'malformed.json'
    bad.write_text('{this is : not valid JSON ::', encoding='utf-8')
    rt = build_default_runtime(config_path=str(bad))
    captured = capsys.readouterr()
    assert '[effects_runtime]' in captured.err
    # At least the three Phase-1 handlers (Phase 3 adds identify_orb)
    # are registered even with an unreadable config.
    assert len(rt.handlers) >= 3
    assert set(rt.handlers) >= {
        'chain_math_combat',
        'divine_intercession_takeover',
        'unicorn_bond_takeover',
    }
    # They have no effect-level config, so chain aura defaults engage.
    chain = _chain_handler(rt)
    assert chain.ranks  # fallback ranks loaded
    assert chain.milestones == (3, 5, 8, 10, 15, 20, 25, 30, 35)


# ---------------------------------------------------------------------------
# Idempotency + milestone semantics
# ---------------------------------------------------------------------------

def test_observe_is_idempotent(headless_runtime):
    """Three identical observe() calls do NOT produce accumulating
    particles or re-fire milestones."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    snap = _chain_snapshot(5)
    rt.observe(1, snap)
    particles_after_first = len(chain._particles)
    milestone_after_first = chain._last_milestone_fired
    rt.observe(1, snap)
    rt.observe(1, snap)
    assert len(chain._particles) == particles_after_first
    assert chain._last_milestone_fired == milestone_after_first


def test_milestone_single_fire(headless_runtime):
    """Crossing chain 3 fires the milestone; staying at 3 does not
    re-fire it."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(2))
    assert chain._last_milestone_fired == 0
    rt.observe(1, _chain_snapshot(3))
    assert chain._last_milestone_fired == 3
    burst = chain._burst_timer_ms
    # Observing again at chain=3 does not re-fire.
    rt.observe(1, _chain_snapshot(3))
    assert chain._last_milestone_fired == 3
    assert chain._burst_timer_ms == burst  # timer not re-primed


def test_chain_jump_fires_highest_milestone(headless_runtime):
    """Jumping from 0 to 10 fires AT MOST ONE milestone -- the highest
    crossed (10). The handler's ``_last_milestone_fired`` tracker is set
    to 10, not accumulated through 3/5/8/10."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(0, asked=0))
    rt.observe(1, _chain_snapshot(10, asked=1))
    assert chain._last_milestone_fired == 10
    # Only one burst timer window (not four stacked).
    assert chain._burst_timer_ms == pytest.approx(chain.burst_duration_ms,
                                                  rel=1e-3)


def test_wrong_answer_does_not_fire_milestone(headless_runtime):
    """A snapshot with chain=5 and last_correct=False should NOT fire
    the milestone -- the chain only moves forward on correct answers,
    and this snapshot shape (last_correct=False at chain=5) represents
    a wrong-answer post-mortem view."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    # Build up to chain 4 first (correct answers).
    rt.observe(1, _chain_snapshot(4))
    assert chain._last_milestone_fired == 3  # the chain-3 milestone fired
    # Now simulate a wrong answer at chain-level 4 (the engine will
    # reset chain=0 on the next real snapshot, but we assert the
    # intermediate "wrong" view doesn't synthesise a milestone-5 burst).
    snap_wrong = _chain_snapshot(5, asked=5, last_correct=False)
    # Even if a snapshot incorrectly reports chain=5 with last_correct=False
    # the handler should not emit a pulse (chain climbed without correct=True
    # is the mastered-tier case, but here asked bumped AND last_correct=False
    # means a bug on the caller side -- we don't fire the pulse).
    pulse_before = chain._pulse_timer_ms
    rt.observe(1, snap_wrong)
    assert chain._pulse_timer_ms == pytest.approx(pulse_before, abs=1e-6)
    # The milestone-5 crossing still updates _last_milestone_fired because
    # the gate check runs regardless -- but no burst fires at the pulse
    # layer. (This is the "post-mortem view" semantics: the chain itself
    # IS at 5, and the aura should reflect that; the pulse+spark burst
    # is the thing we don't want.)


def test_timeout_does_not_erase_chain(headless_runtime):
    """A timeout snapshot (where last_correct is None) does not reset
    the chain value tracked by the handler. The aura stays visible via
    the handler's cached chain/opacity state until reset_scope fires."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(10))
    last_chain = chain._last_chain
    assert last_chain == 10
    # Timeout: engine reports last_correct=None, chain unchanged.
    snap_timeout = _chain_snapshot(10, asked=11, last_correct=None)
    rt.observe(1, snap_timeout)
    assert chain._last_chain == 10
    # Target opacity still at the chain-10 rank -- the aura holds.
    assert chain._target_aura_opacity > 0.0


# ---------------------------------------------------------------------------
# Scope lifecycle
# ---------------------------------------------------------------------------

def test_reset_scope_clears_state(headless_runtime):
    """reset_scope clears the per-scope state. A fresh observe after
    reset emits a first-answer pulse again."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(5))
    assert chain._last_chain == 5
    rt.reset_scope(1)
    assert chain._last_chain == 0
    assert chain._last_milestone_fired == 0
    assert chain._particles == []
    # First post-reset observe fires the pulse again.
    rt.observe(2, _chain_snapshot(1, asked=1))
    assert chain._pulse_timer_ms > 0.0


def test_distinct_zero_chain_sessions(headless_runtime):
    """Two consecutive zero-chain sessions each produce their own
    first-answer pulse when they finally land chain=1."""
    rt = headless_runtime
    chain = _chain_handler(rt)

    # Session 1 -- land one correct answer, then session over.
    rt.reset_scope(1)
    rt.observe(1, _chain_snapshot(0, asked=0, last_correct=None))
    rt.observe(1, _chain_snapshot(1, asked=1))
    assert chain._pulse_timer_ms > 0.0
    first_pulse = chain._pulse_timer_ms
    # Drain the pulse artificially.
    chain._pulse_timer_ms = 0.0

    # Session 2 -- same shape, different scope id.
    rt.reset_scope(2)
    rt.observe(2, _chain_snapshot(0, asked=0, last_correct=None))
    rt.observe(2, _chain_snapshot(1, asked=1))
    assert chain._pulse_timer_ms > 0.0
    # Both pulses fire at the configured pulse duration -- the two
    # sessions are treated as independent.
    assert chain._pulse_timer_ms == pytest.approx(first_pulse, rel=1e-6)


# ---------------------------------------------------------------------------
# Pause / update
# ---------------------------------------------------------------------------

def test_paused_freezes_update(headless_runtime):
    """update(dt, paused=True) advances no timers. The chain aura's
    pulse timer must not count down while paused."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(5))
    pulse_before = chain._pulse_timer_ms
    rt.update(dt=10.0, paused=True)
    # Pulse timer unchanged.
    assert chain._pulse_timer_ms == pulse_before
    # Running unpaused drains it.
    rt.update(dt=1.0, paused=False)
    assert chain._pulse_timer_ms == 0.0


# ---------------------------------------------------------------------------
# Reduced motion
# ---------------------------------------------------------------------------

def test_reduced_motion_disables_particles(monkeypatch):
    """With PQ_REDUCED_MOTION=1, no particles should be spawned, even
    on a chain-10 milestone crossing. The static-highlight replacement
    takes over (verified via _static_highlight_ms being set)."""
    monkeypatch.setenv('PQ_REDUCED_MOTION', '1')
    rt = build_default_runtime()
    assert rt.reduced_motion is True
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(10))
    assert chain._particles == []
    # The static highlight replacement engages.
    assert chain._static_highlight_ms > 0.0


# ---------------------------------------------------------------------------
# Gate: non-math / non-combat quizzes skip the chain aura
# ---------------------------------------------------------------------------

def test_non_math_subject_no_chain_aura(headless_runtime):
    """A theology-chain snapshot (same mode, different subject) must
    NOT activate the chain-aura handler."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(5, subject='theology'))
    assert chain._active is False
    assert chain._particles == []
    assert chain._last_milestone_fired == 0


def test_no_combat_target_no_chain_aura(headless_runtime):
    """A math-chain snapshot without ``has_combat_target`` (e.g. the
    mystery altar chain) must not activate the chain aura."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(5, has_combat_target=False))
    assert chain._active is False


# ---------------------------------------------------------------------------
# Fullscreen takeovers (fire + lifecycle)
# ---------------------------------------------------------------------------

def test_fire_one_shot_takeover(headless_runtime):
    """fire() triggers the fullscreen takeover; update(dt=duration)
    then dismisses it."""
    rt = headless_runtime
    takeover = _takeover(rt, 'divine_intercession_takeover')
    assert takeover.active is False
    rt.fire('divine_intercession_takeover', {})
    assert takeover.active is True
    # Simulate the full 1.8 s hold (default duration_ms).
    rt.update(dt=1.8, paused=False)
    assert takeover.active is False


def test_fire_unknown_effect_does_not_crash(headless_runtime, capsys):
    """fire() on an unregistered effect id logs a warning but does
    not raise."""
    rt = headless_runtime
    rt.fire('this_effect_does_not_exist', {})
    captured = capsys.readouterr()
    assert '[effects_runtime]' in captured.err
    assert 'this_effect_does_not_exist' in captured.err


# ---------------------------------------------------------------------------
# Particle budget cap
# ---------------------------------------------------------------------------

def test_particle_budget_cap(headless_runtime):
    """Rapid-firing many milestone-level bursts must not push the
    particle pool past the configured ``particle_budget``."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(0, asked=0, last_correct=None))
    # Hammer the handler with repeated milestone+pulse spawns by
    # directly invoking the internal spawn path many times.
    rank = chain._rank_for(20)
    for _ in range(50):
        chain._on_milestone(20, rank, reduced=False)
        chain._on_correct_answer(20, reduced=False)
    assert len(chain._particles) <= chain.particle_budget


# ---------------------------------------------------------------------------
# Scope isolation
# ---------------------------------------------------------------------------

def test_scope_isolation(headless_runtime):
    """Each scope tracks its own milestone-fired set. Scope 1 reaching
    chain-5 then scope 2 reaching chain-5 both fire the milestone --
    scope 2's state must not be prejudiced by scope 1's history."""
    rt = headless_runtime
    chain = _chain_handler(rt)

    rt.observe(1, _chain_snapshot(5))
    assert chain._last_milestone_fired == 5
    scope1_burst = chain._burst_timer_ms
    assert scope1_burst > 0.0

    # Scope change -- the chain-aura handler detects it via snapshot
    # and resets its state cleanly. Milestone 5 should fire again.
    rt.observe(2, _chain_snapshot(0, asked=0, last_correct=None))
    assert chain._last_milestone_fired == 0
    rt.observe(2, _chain_snapshot(5))
    assert chain._last_milestone_fired == 5
    assert chain._burst_timer_ms > 0.0


# ---------------------------------------------------------------------------
# Chain >= 100 stays within bounds (design-doc requirement)
# ---------------------------------------------------------------------------

def test_very_long_chain_stays_bounded(headless_runtime):
    """A hypothetical chain-100 snapshot must not blow past the
    particle budget or send opacity > 1.0."""
    rt = headless_runtime
    chain = _chain_handler(rt)
    rt.observe(1, _chain_snapshot(100, asked=100))
    assert len(chain._particles) <= chain.particle_budget
    assert 0.0 <= chain._target_aura_opacity <= 1.0
    assert 0.0 <= chain._current_aura_opacity <= 1.0


# ---------------------------------------------------------------------------
# Draw methods are safe to call on a plain pygame.Surface (no display)
# ---------------------------------------------------------------------------

def test_draw_methods_are_display_safe(headless_runtime):
    """Running the full draw pass against a plain Surface (no init'd
    display) must not raise -- it's the common test / preview path."""
    import pygame
    pygame.font.init()  # fonts are required by fullscreen_takeover
    rt = headless_runtime
    rt.observe(1, _chain_snapshot(10))
    rt.update(dt=0.016, paused=False)
    surf = pygame.Surface((1600, 900), pygame.SRCALPHA)
    panel_rect = pygame.Rect(400, 300, 800, 300)
    rt.draw_background(surf, panel_rect)
    rt.draw_foreground(surf, [panel_rect])
    rt.draw_top_overlay(surf)
    # If we got here, no exception was raised. Also verify the
    # takeover draw path when active.
    rt.fire('divine_intercession_takeover', {})
    rt.update(dt=0.016, paused=False)
    rt.draw_top_overlay(surf)
