"""Pluggable visual-effects layer.

The ``EffectsRuntime`` is a general-purpose visual-effects controller: it
owns a registry of named handlers, routes per-frame observations and
one-shot events into them, drives their internal timers, and dispatches
their rendering into the correct phase (behind the quiz panel, in front
of the quiz panel with protected-rect culling, or over the top of the
screen for fullscreen takeovers).

The runtime is deliberately NOT quiz-specific. ``chain_aura`` is one
consumer; the ``fullscreen_takeover`` handler is another; future effects
(level-up burst, identify orb, boss death flourish) plug in as new
entries in ``data/ui/effects_config.json`` + new handler classes without
touching this file.

See CHAIN_EFFECTS_PLAN.md (2026-10-03) Phase 1 and
``docs/design/effects_runtime.md``.
"""
from __future__ import annotations

import json
import os
import random
import sys
from typing import Any

from paths import data_path


# Default config path -- tests may pass an explicit path to override.
_DEFAULT_CONFIG = data_path('data', 'ui', 'effects_config.json')


class EffectsRuntime:
    """Pluggable visual effects. Observes game state / fires events;
    renders bounded visuals. Not quiz-specific -- chain is one consumer.

    Lifecycle (per frame):

        snapshot = {...}
        runtime.observe(scope_id, snapshot)   # idempotent, safe every frame
        runtime.fire('effect_id', context={}) # one-shot events
        runtime.update(dt, paused=False)      # advance timers
        # ...then in game_render.render():
        runtime.draw_background(screen, panel_rect)
        # ...quiz panel paints opaquely over the background...
        runtime.draw_foreground(screen, protected_rects)
        # ...later, after all state-specific rendering:
        runtime.draw_top_overlay(screen)

    Handlers implement a duck-type protocol -- see ``EffectHandler``
    docstring in this module. Missing methods on a handler are tolerated
    (treated as no-ops) so a handler can opt into just the phases it
    needs.
    """

    def __init__(self, config_path: str | None = None):
        self.handlers: dict[str, Any] = {}
        self.config: dict = _load_config(config_path or _DEFAULT_CONFIG)

        # Reduced-motion opt-in via env var (Phase 1 simplest form).
        # A proper settings-UI toggle lives in future work -- see
        # ``docs/design/effects_runtime.md`` for the plan.
        self.reduced_motion: bool = (
            os.environ.get('PQ_REDUCED_MOTION') == '1')

        # Dedicated RNG so the effects layer never perturbs gameplay /
        # dungeon randomness. Seeded independently from os.urandom; a
        # fixed seed can be injected by tests via ``self.rng.seed(...)``.
        self.rng = random.Random()

    # ------------------------------------------------------------------
    # Registration + config
    # ------------------------------------------------------------------

    def register(self, effect_id: str, handler: Any) -> None:
        """Register a handler by its effect id.

        The id must match a key in ``config['effects']`` -- otherwise the
        handler is still stored, but its activation gate (if any) can
        never trigger, since the runtime won't have config for it.
        """
        self.handlers[effect_id] = handler

    def effect_config(self, effect_id: str) -> dict:
        """Return the config block for a named effect, or an empty dict.

        Handlers are passed their config via this helper during
        registration (see the chain_aura + fullscreen_takeover handlers)
        so they can be rebuilt from fresh config without reinstantiating
        the runtime.
        """
        return (self.config.get('effects') or {}).get(effect_id, {})

    # ------------------------------------------------------------------
    # Observational -- idempotent, safe to call every frame
    # ------------------------------------------------------------------

    def observe(self, scope_id: int | str, snapshot: dict) -> None:
        """Feed an idempotent state snapshot into every handler that
        wants it. Each handler is responsible for diffing against its
        own previously-ingested snapshot; the runtime does no diffing
        or dispatching logic of its own.

        ``scope_id`` is a generic key -- a quiz_session uses
        ``qe.session_id``; other scopes might key by encounter id, cook
        attempt id, etc. Handlers that care about scope changes read
        ``snapshot['scope_id']`` which this method injects.
        """
        # Inject the scope id + reduced-motion flag into the snapshot so
        # handlers don't need a separate parameter -- the diffing logic
        # reads them off the dict just like any other field.
        enriched = dict(snapshot)
        enriched['scope_id'] = scope_id
        enriched['_reduced_motion'] = self.reduced_motion
        for handler in self.handlers.values():
            ingest = getattr(handler, 'ingest', None)
            if callable(ingest):
                try:
                    ingest(enriched)
                except Exception as e:   # noqa: BLE001 -- never let an effect crash the game
                    _warn(f'ingest failed for {type(handler).__name__}: {e}')

    # ------------------------------------------------------------------
    # Imperative -- one-shot events (level-up, boss death, DI takeover)
    # ------------------------------------------------------------------

    def fire(self, effect_id: str, context: dict | None = None) -> None:
        """Trigger a named one-shot effect.

        No-op if the effect id isn't registered or the handler lacks a
        ``trigger()`` method. Never raises -- a missing effect must not
        crash the gameplay path that fired it.
        """
        handler = self.handlers.get(effect_id)
        if handler is None:
            _warn(f'fire() called for unknown effect {effect_id!r}')
            return
        trigger = getattr(handler, 'trigger', None)
        if not callable(trigger):
            return
        ctx = dict(context or {})
        # Inject reduced-motion so a handler's trigger() can shorten
        # or de-rate the one-shot before setup locks in a duration.
        ctx.setdefault('_reduced_motion', self.reduced_motion)
        try:
            trigger(ctx)
        except Exception as e:   # noqa: BLE001
            _warn(f'trigger failed for {effect_id}: {e}')

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset_scope(self, scope_id: int | str) -> None:
        """Clear per-scope state in every handler that participates in
        a scope lifetime (chain aura, etc.). Called when a new quiz
        session begins and the previous one's particles should be
        dropped cleanly.
        """
        for handler in self.handlers.values():
            reset = getattr(handler, 'reset_scope', None)
            if callable(reset):
                try:
                    reset(scope_id)
                except Exception as e:   # noqa: BLE001
                    _warn(f'reset_scope failed for {type(handler).__name__}: {e}')

    def reset(self) -> None:
        """Reset every handler to its freshly-constructed state. Used
        by the preview tool and by tests between scenarios."""
        for handler in self.handlers.values():
            reset = getattr(handler, 'reset', None)
            if callable(reset):
                try:
                    reset()
                except Exception as e:   # noqa: BLE001
                    _warn(f'reset failed for {type(handler).__name__}: {e}')

    def update(self, dt: float, paused: bool = False) -> None:
        """Advance every handler's internal timers by ``dt`` seconds.

        ``paused=True`` freezes timers without discarding state --
        particles stay on screen but don't move, pulses hold at their
        current intensity. Mirrors the ``_timer_paused`` flag the quiz
        engine uses for the context-blurb modal so an effect doesn't
        drain to zero while the player reads a dossier.
        """
        if paused:
            return
        reduced = self.reduced_motion
        for handler in self.handlers.values():
            upd = getattr(handler, 'update', None)
            if callable(upd):
                try:
                    upd(dt, reduced)
                except Exception as e:   # noqa: BLE001
                    _warn(f'update failed for {type(handler).__name__}: {e}')

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw_background(self, surface, panel_rect) -> None:
        """Draw behind-the-panel effects. Called in ``_draw_quiz``
        AFTER the dim overlay but BEFORE the opaque panel paints, so a
        border aura naturally hides where the panel sits.
        """
        reduced = self.reduced_motion
        for handler in self.handlers.values():
            draw = getattr(handler, 'draw_bg', None)
            if callable(draw):
                try:
                    draw(surface, panel_rect, reduced)
                except Exception as e:   # noqa: BLE001
                    _warn(f'draw_bg failed for {type(handler).__name__}: {e}')

    def draw_foreground(self, surface, protected_rects: list) -> None:
        """Draw in-front-of-panel effects, with the handler responsible
        for culling any sprite / particle that would land on a
        protected rect (question text, choice cards, timer, counter).

        Called in ``_draw_quiz`` after the panel + text paint.
        """
        reduced = self.reduced_motion
        protected = tuple(protected_rects or ())
        for handler in self.handlers.values():
            draw = getattr(handler, 'draw_fg', None)
            if callable(draw):
                try:
                    draw(surface, protected, reduced)
                except Exception as e:   # noqa: BLE001
                    _warn(f'draw_fg failed for {type(handler).__name__}: {e}')

    def draw_top_overlay(self, surface) -> None:
        """Draw full-screen overlay effects (fullscreen takeovers,
        boss-death flashes, etc.) ON TOP of everything else.

        Called from ``game_render.render()`` as the final step before
        ``pygame.display.flip()`` so these effects paint over whatever
        state-specific rendering just finished. Handlers that don't
        implement ``draw_overlay`` are silently skipped.
        """
        reduced = self.reduced_motion
        for handler in self.handlers.values():
            draw = getattr(handler, 'draw_overlay', None)
            if callable(draw):
                try:
                    draw(surface, reduced)
                except Exception as e:   # noqa: BLE001
                    _warn(f'draw_overlay failed for {type(handler).__name__}: {e}')


# ----------------------------------------------------------------------
# Config loader
# ----------------------------------------------------------------------

def _load_config(path: str) -> dict:
    """Load the effects config.

    Non-fatal on any error -- a missing / malformed file degrades the
    runtime to a no-op registry so combat still works. Partial
    corruption (one bad effect out of several) is kept intact: this
    loader does the file-level read; per-handler validation lives in
    each handler's constructor and should also degrade gracefully.
    """
    try:
        if not os.path.isfile(path):
            _warn(f'effects config missing at {path!r} -- runtime will be a no-op')
            return {'effects': {}}
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        _warn(f'effects config unreadable ({e}) -- runtime will be a no-op')
        return {'effects': {}}
    if not isinstance(data, dict):
        _warn('effects config is not an object -- runtime will be a no-op')
        return {'effects': {}}
    effects = data.get('effects')
    if not isinstance(effects, dict):
        _warn("effects config has no 'effects' object -- runtime will be a no-op")
        return {'effects': {}}
    return data


def _warn(msg: str) -> None:
    """Diagnostic log that never raises. Prints to stderr so bundle
    runs still see the message even if the game window is up."""
    try:
        print(f'[effects_runtime] {msg}', file=sys.stderr)
    except Exception:   # noqa: BLE001
        pass


# ----------------------------------------------------------------------
# Public helper for building the runtime with the shipped handlers
# ----------------------------------------------------------------------

def build_default_runtime(config_path: str | None = None) -> EffectsRuntime:
    """Factory: construct a runtime with the shipped handlers
    pre-registered. Phase 1 shipped three (chain_math_combat +
    divine_intercession_takeover + unicorn_bond_takeover); Phase 3
    (CHAIN_EFFECTS_PLAN.md, 2026-10-03) adds a fourth
    (identify_success_orb). Separated from ``Game.__init__`` so tests
    + the Phase 2 preview tool can build an identical runtime.
    """
    runtime = EffectsRuntime(config_path=config_path)
    # Imports local -- avoids a pygame dependency at module import time
    # for environments that only want to validate config.
    from effects.chain_aura import ChainAuraPulse
    from effects.fullscreen_takeover import FullscreenTakeover
    from effects.identify_orb import IdentifyOrb

    runtime.register(
        'chain_math_combat',
        ChainAuraPulse(runtime.effect_config('chain_math_combat')),
    )
    runtime.register(
        'divine_intercession_takeover',
        FullscreenTakeover(runtime.effect_config('divine_intercession_takeover')),
    )
    runtime.register(
        'unicorn_bond_takeover',
        FullscreenTakeover(runtime.effect_config('unicorn_bond_takeover')),
    )
    runtime.register(
        'identify_success_orb',
        IdentifyOrb(runtime.effect_config('identify_success_orb')),
    )
    return runtime
