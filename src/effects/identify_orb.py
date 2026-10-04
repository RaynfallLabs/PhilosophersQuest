"""IdentifyOrb -- one-shot celebratory orb on identify success.

Phase 3 of CHAIN_EFFECTS_PLAN.md (2026-10-03). First NON-chain effect
to live on the ``EffectsRuntime`` -- validates that the pluggable
pipeline generalises beyond math-combat chain feedback.

Context: identify-v3 is a single philosophy question (``_identify_item``
in ``game_magic.py`` for items, ``_start_corpse_identify`` in
``main.py`` for corpses). Right = full identification. Wrong = Stunned
10 turns. Success is the "aha!" moment and benefits from a bounded
visual flourish; failure is already punished by the stun.

Visual plan:
  * Phase 0 (0 -> 200 ms)     -- orb grows from radius 0 to peak
                                 radius ~48 px with ease-out quadratic.
  * Phase 1 (200 -> 700 ms)   -- orb hovers at peak radius, pulsing
                                 slightly (sine wave on alpha); up to
                                 12 orbit sparks circle the orb.
  * Phase 2 (700 -> 1200 ms)  -- orb expands outward to ~120 px
                                 radius while alpha fades to 0.

Reduced-motion (env var ``PQ_REDUCED_MOTION=1``):
  * Orbit sparks disabled.
  * Expansion phase disabled.
  * Replaced wholesale with a 300 ms static highlight pulse (single
    ring that fades out).

Draw phase: ``draw_overlay`` (top-level). By the time the orb fires,
the identify quiz modal has already closed (callback runs in STATE
transition back to STATE_PLAYER). Mirroring the Divine Intercession /
Unicorn pattern keeps the orb independent of state-specific rendering.

Rendering budget:
  * Particle pool capped at ``particle_budget`` (default 12).
  * Per-frame surface allocations are bounded (one orb surface sized
    to the current radius + one small spark surface per spawned
    particle).
"""
from __future__ import annotations

import math
import random

import pygame

import layout


# Palette definitions -- mirror the shape used by fullscreen_takeover
# so a swap of palette name is the only change needed when the handler
# is reused for another "aha" moment (e.g. a mythic-scroll pop).
_PALETTES = {
    'lavender_white': {
        'primary': (200, 170, 240),
        'bright':  (235, 215, 255),
        'pale':    (250, 240, 255),
    },
    'gold_white': {
        'primary': (240, 200, 100),
        'bright':  (255, 230, 160),
        'pale':    (255, 245, 210),
    },
}


class IdentifyOrb:
    """One-shot identify-success orb. One registered instance per
    runtime; re-firing while active restarts the animation (the second
    caller wins so a stacked identify-chain can't glue two orbs
    together)."""

    def __init__(self, config: dict | None = None):
        cfg = dict(config or {})
        self._active: bool = False
        self._elapsed_ms: float = 0.0
        self._duration_ms: int = int(cfg.get('duration_ms', 1200))
        self._palette_name: str = str(cfg.get('palette', 'lavender_white'))
        self._particle_budget: int = int(cfg.get('particle_budget', 12))
        rm = cfg.get('reduced_motion') or {}
        self._rm_disable = set(rm.get('disable') or [])
        self._rm_replace: str = str(rm.get('replace_with', 'static_pulse_300ms'))
        self._rm_static_ms: float = 300.0

        # Anchor is None until a trigger lands. Draw path short-circuits
        # when anchor is None so a stray update tick before trigger is a
        # no-op.
        self._anchor_x: int | None = None
        self._anchor_y: int | None = None
        self._reduced_mode: bool = False
        self._particles: list[dict] = []

        # Independent RNG so the orb never perturbs dungeon RNG. Seeded
        # with a fixed value spelled roughly "IDEF71F" so repeat runs
        # produce the same orbital layout, which keeps the look stable
        # across sessions.
        self._rng = random.Random(0x1DEF71F)

        # Cached orb surface -- resized to the current frame's radius.
        self._orb_surf: pygame.Surface | None = None
        self._orb_surf_size: int = 0

    # ------------------------------------------------------------------
    # Runtime hooks
    # ------------------------------------------------------------------

    def ingest(self, snapshot: dict) -> None:
        """One-shot effect -- observational snapshots are ignored."""
        return

    def trigger(self, context: dict) -> None:
        """Start the orb animation.

        ``context`` keys:
          ``anchor_x``, ``anchor_y`` -- screen-space centre point. If
              either is missing we fall back to the window centre.
          ``_reduced_motion`` -- injected by the runtime; selects the
              reduced-motion path.
        """
        ctx = dict(context or {})
        ax = ctx.get('anchor_x')
        ay = ctx.get('anchor_y')
        try:
            ax = int(ax) if ax is not None else layout.WINDOW_W // 2
        except (TypeError, ValueError):
            ax = layout.WINDOW_W // 2
        try:
            ay = int(ay) if ay is not None else layout.WINDOW_H // 2
        except (TypeError, ValueError):
            ay = layout.WINDOW_H // 2
        self._anchor_x = ax
        self._anchor_y = ay

        self._reduced_mode = bool(ctx.get('_reduced_motion'))
        self._elapsed_ms = 0.0
        self._active = True
        self._particles = []

        # Orbit sparks spawn in full-motion mode. Reduced-motion
        # disables them wholesale (plus the expansion phase) and uses
        # the static-pulse replacement instead -- see
        # effects_config.json reduced_motion.disable.
        if self._particles_allowed():
            self._spawn_orbit_sparks()

    def update(self, dt: float, reduced: bool) -> None:
        if not self._active:
            return
        self._elapsed_ms += max(0.0, dt) * 1000.0
        total = (self._rm_static_ms
                 if self._reduced_mode else float(self._duration_ms))
        if self._elapsed_ms >= total:
            self._active = False
            self._elapsed_ms = 0.0
            self._particles = []
            self._anchor_x = None
            self._anchor_y = None
            self._reduced_mode = False

    def reset(self) -> None:
        """Clear every scrap of state. Used by tests + the preview tool."""
        self._active = False
        self._elapsed_ms = 0.0
        self._particles = []
        self._anchor_x = None
        self._anchor_y = None
        self._reduced_mode = False

    def reset_scope(self, scope_id) -> None:
        """One-shot effect is not scope-driven; no-op for API symmetry."""
        return

    def draw_bg(self, surface, panel_rect, reduced: bool) -> None:
        """The orb paints only in the top-overlay phase."""
        return

    def draw_fg(self, surface, protected_rects, reduced: bool) -> None:
        """The orb paints only in the top-overlay phase."""
        return

    def draw_overlay(self, surface: pygame.Surface, reduced: bool) -> None:
        """Paint the current frame of the orb animation."""
        if not self._active or self._anchor_x is None or self._anchor_y is None:
            return
        palette = _PALETTES.get(self._palette_name) or _PALETTES['lavender_white']
        if self._reduced_mode:
            self._draw_static_pulse(surface, palette)
            return
        self._draw_full_animation(surface, palette)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _particles_allowed(self) -> bool:
        """Orbit sparks are allowed unless we're in reduced-motion mode
        AND the config's ``reduced_motion.disable`` list names
        ``orbit_sparks``. Mirrors the ``_particles_allowed`` idiom used
        by ``chain_aura``."""
        return not (self._reduced_mode
                    and 'orbit_sparks' in self._rm_disable)

    def _spawn_orbit_sparks(self) -> None:
        """Populate the orbital-spark pool (budget-capped)."""
        count = max(0, min(self._particle_budget, 12))
        for i in range(count):
            self._particles.append({
                'angle0':     2 * math.pi * i / max(1, count)
                              + self._rng.uniform(0.0, 0.3),
                'orbit_r':    self._rng.uniform(42.0, 54.0),
                'angular_v':  self._rng.uniform(2.4, 3.6),
                'size':       2 + self._rng.randint(0, 2),
            })

    def _draw_full_animation(self, surface: pygame.Surface,
                             palette: dict) -> None:
        """Three-phase orb: grow -> hover+orbit -> expand+fade."""
        t = self._elapsed_ms
        cx = int(self._anchor_x)
        cy = int(self._anchor_y)

        if t < 200.0:
            # Phase 0: grow. Ease-out quadratic for a soft arrival.
            frac = t / 200.0
            eased = 1.0 - (1.0 - frac) ** 2
            radius = 48.0 * eased
            alpha = 200
        elif t < 700.0:
            # Phase 1: hover + sinusoidal alpha pulse.
            local = (t - 200.0) / 500.0
            radius = 48.0
            pulse = 0.5 + 0.5 * math.sin(local * math.pi * 4.0)
            alpha = int(160 + 60 * pulse)
        else:
            # Phase 2: expand to ~120px while alpha fades to 0.
            local = (t - 700.0) / 500.0
            local = max(0.0, min(1.0, local))
            radius = 48.0 + (120.0 - 48.0) * local
            alpha = int(200 * (1.0 - local))

        r = max(1, int(radius))
        a = max(0, min(255, int(alpha)))

        # Core orb -- concentric glow layers for a soft halo.
        size = r * 4 + 8
        if self._orb_surf is None or self._orb_surf_size < size:
            self._orb_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            self._orb_surf_size = size
        orb = self._orb_surf
        orb.fill((0, 0, 0, 0))
        center = orb.get_width() // 2

        layers = 6
        for i in range(layers):
            lr = int(r * (1.0 - i / layers)) + 2
            if lr <= 0:
                continue
            la = int(a * 0.5 * (i + 1) / layers)
            if la <= 0:
                continue
            color = palette['bright'] if i >= layers // 2 else palette['primary']
            pygame.draw.circle(
                orb, (color[0], color[1], color[2], la),
                (center, center), lr)
        # Bright pale core.
        core_r = max(1, r // 3)
        pale = palette['pale']
        pygame.draw.circle(
            orb, (pale[0], pale[1], pale[2], a),
            (center, center), core_r)
        surface.blit(orb, (cx - center, cy - center))

        # Orbit sparks -- only during the hover phase.
        if 200.0 <= t < 700.0 and self._particles:
            local_s = (t - 200.0) / 1000.0  # seconds since hover start
            for p in self._particles:
                ang = p['angle0'] + p['angular_v'] * local_s
                px = cx + math.cos(ang) * p['orbit_r']
                py = cy + math.sin(ang) * p['orbit_r']
                s = int(p['size'])
                diameter = s * 2 + 2
                spark = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                bright = palette['bright']
                pygame.draw.circle(
                    spark, (bright[0], bright[1], bright[2], a),
                    (s + 1, s + 1), s)
                surface.blit(spark, (int(px) - s - 1, int(py) - s - 1))

    def _draw_static_pulse(self, surface: pygame.Surface,
                           palette: dict) -> None:
        """Reduced-motion fallback: single 300 ms ring that expands + fades."""
        t = self._elapsed_ms
        frac = max(0.0, min(1.0, t / self._rm_static_ms))
        radius = int(32 + 48 * frac)
        alpha = int(220 * (1.0 - frac))
        if alpha <= 0 or radius <= 0:
            return
        cx = int(self._anchor_x)
        cy = int(self._anchor_y)
        size = radius * 2 + 8
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        bright = palette['bright']
        pygame.draw.circle(
            surf, (bright[0], bright[1], bright[2], alpha),
            (center, center), radius, 3)
        surface.blit(surf, (cx - center, cy - center))

    # ------------------------------------------------------------------
    # Introspection helpers (for tests / preview)
    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        return self._active
