"""ChainAuraPulse -- in-quiz chain feedback for math combat.

Delivers the per-answer response design in
``docs/math_quiz_effects_design.md`` as the first consumer of the
``EffectsRuntime``:

  * Persistent border aura behind the quiz panel whose colour +
    opacity interpolate between rank thresholds.
  * On every correct answer: a brief ~220ms border pulse + a bounded
    spark burst near the counter position.
  * On milestones (3/5/8/10/15/20/25/30/35): a 650ms border bloom + a
    larger spark burst (capped at 32 particles) + a localised ring
    behind the panel for the top ranks.
  * Milestones fire once per crossing -- a chain-jump that skips past
    several (e.g. auto-pass tiered mastery jumping 0->8) fires AT MOST
    ONE burst for the highest crossed milestone.
  * Reduced-motion mode (env var ``PQ_REDUCED_MOTION=1`` -- see
    ``effects_runtime.EffectsRuntime``) disables particles + rotating
    runes and replaces milestone bursts with a 300ms static highlight.

Activation gate: this handler only responds when the snapshot
describes a math-combat chain quiz. Any other quiz (grammar scroll,
cooking escalator, mystery AI quiz, etc.) is silently skipped so the
pedagogical quizzes keep their minimalist UI.

Rendering budget:
  * Particle pool capped at ``particle_budget`` (default 64).
  * All overlay surfaces are reused across frames (no per-frame
    ``pygame.Surface`` allocation).
  * Protected rects (question text, choice cards, timer, counter) are
    never painted into -- any particle whose bbox intersects a
    protected rect is culled before draw.
"""
from __future__ import annotations

import math
import random
from typing import Iterable

import pygame


_DEFAULT_RANKS = (
    {'threshold': 0,  'name': '',          'color': [230, 230, 230], 'aura_opacity': 0.0},
    {'threshold': 1,  'name': '',          'color': [200, 220, 200], 'aura_opacity': 0.15},
    {'threshold': 3,  'name': 'Solid',     'color': [110, 220, 110], 'aura_opacity': 0.25},
    {'threshold': 5,  'name': 'Sharp',     'color': [240, 220,  80], 'aura_opacity': 0.35},
    {'threshold': 8,  'name': 'Brilliant', 'color': [255, 150,  40], 'aura_opacity': 0.45},
    {'threshold': 10, 'name': 'Genius',    'color': [240,  80,  60], 'aura_opacity': 0.55},
    {'threshold': 15, 'name': 'Prodigy',   'color': [255, 210,  60], 'aura_opacity': 0.60},
    {'threshold': 20, 'name': 'Mythic',    'color': [240, 200, 255], 'aura_opacity': 0.65},
)
_DEFAULT_MILESTONES = (3, 5, 8, 10, 15, 20, 25, 30, 35)


class ChainAuraPulse:
    """Chain-aura handler. One instance per runtime; it keeps per-scope
    state so switching from one quiz session to the next cleanly resets
    the particle pool."""

    def __init__(self, config: dict | None = None):
        cfg = dict(config or {})
        self.ranks = _coerce_ranks(cfg.get('ranks') or _DEFAULT_RANKS)
        self.milestones = tuple(sorted(cfg.get('milestones') or _DEFAULT_MILESTONES))
        self.particle_budget = int(cfg.get('particle_budget') or 64)
        self.pulse_duration_ms = int(cfg.get('pulse_duration_ms') or 220)
        self.burst_duration_ms = int(cfg.get('burst_duration_ms') or 650)
        self.activates_when = cfg.get('activates_when') or {}
        rm = cfg.get('reduced_motion') or {}
        self.rm_disable = set(rm.get('disable') or [])
        # Independent RNG so visuals never perturb dungeon RNG.
        self.rng = random.Random()

        # ----------- per-scope dynamic state --------------------------
        self._scope_id: int | str | None = None
        self._active: bool = False      # True iff gate currently matches
        self._last_chain: int = 0
        self._last_asked: int = 0
        self._last_correct: bool | None = None
        self._last_state = None         # last QuizState enum ingested
        self._last_milestone_fired: int = 0
        self._current_aura_color = (230, 230, 230)
        self._current_aura_opacity = 0.0
        self._target_aura_color = (230, 230, 230)
        self._target_aura_opacity = 0.0
        self._pulse_timer_ms: float = 0.0
        self._burst_timer_ms: float = 0.0
        self._particles: list[_Particle] = []
        # Static highlight for reduced-motion milestone replacement.
        self._static_highlight_ms: float = 0.0
        self._static_highlight_color = (255, 255, 255)
        # Cached small overlay surface for the pulse glow. Resized on
        # demand to the current panel rect.
        self._pulse_surf: pygame.Surface | None = None
        self._pulse_surf_size: tuple[int, int] = (0, 0)
        # Last panel geometry stashed by draw_bg; particles anchor near
        # the chain counter (top-right of the panel) using this. Falls
        # back to _Particle class defaults if nothing has drawn yet.
        # Fixed 2026-10-03 after Phase 2 preview showed sparks blooming
        # at the hardcoded (1300, 100) instead of near the actual
        # counter.
        self._last_panel_rect: pygame.Rect | None = None

    # ------------------------------------------------------------------
    # Lifecycle hooks called by the runtime
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear ALL state. Used by the preview harness + tests."""
        self._scope_id = None
        self._active = False
        self._last_chain = 0
        self._last_asked = 0
        self._last_correct = None
        self._last_state = None
        self._last_milestone_fired = 0
        self._current_aura_color = (230, 230, 230)
        self._current_aura_opacity = 0.0
        self._target_aura_color = (230, 230, 230)
        self._target_aura_opacity = 0.0
        self._pulse_timer_ms = 0.0
        self._burst_timer_ms = 0.0
        self._particles.clear()
        self._static_highlight_ms = 0.0

    def reset_scope(self, scope_id: int | str) -> None:
        """Called when the runtime is explicitly told a scope ended.
        For the chain-aura handler, scope changes are also detected
        automatically by ``ingest`` via ``snapshot['scope_id']``, so
        this method is mostly for symmetry with the runtime API."""
        if scope_id == self._scope_id:
            self.reset()

    def ingest(self, snapshot: dict) -> None:
        """Observe a per-frame quiz snapshot. Idempotent: identical
        consecutive snapshots never fire new bursts.
        """
        scope_id = snapshot.get('scope_id')
        if scope_id != self._scope_id:
            # Session boundary -- drop every particle, reset counters.
            self.reset()
            self._scope_id = scope_id

        # Gate: this effect only runs for math combat chain quizzes.
        if not self._matches(snapshot):
            self._active = False
            return
        self._active = True

        reduced = bool(snapshot.get('_reduced_motion'))
        chain = int(snapshot.get('chain') or 0)
        asked = int(snapshot.get('asked_count') or 0)
        last_correct = snapshot.get('last_correct')
        state = snapshot.get('quiz_state')

        # ------- Per-answer landing detection ------------------------
        # An "answer landed" when asked_count ticked up since last
        # snapshot, OR when chain climbed without an asked bump
        # (mastered-tier auto-pass). We fire a pulse+spark only when
        # the chain actually advances -- wrong answers / timeouts do
        # nothing here. The quiz already shows the red RESULT flash;
        # no need to add visual noise on misses.
        asked_bumped = asked > self._last_asked
        chain_climbed = chain > self._last_chain
        if chain_climbed and (asked_bumped and last_correct is True
                              or not asked_bumped):
            self._on_correct_answer(chain, reduced=reduced)

        # ------- Rank interpolation targets --------------------------
        rank = self._rank_for(chain)
        self._target_aura_color = tuple(int(c) for c in rank['color'])
        self._target_aura_opacity = float(rank['aura_opacity'])

        # ------- Milestone single-fire -------------------------------
        crossed = [m for m in self.milestones
                   if self._last_chain < m <= chain]
        if crossed:
            top = max(crossed)
            if top > self._last_milestone_fired:
                self._last_milestone_fired = top
                self._on_milestone(top, rank, reduced=reduced)

        self._last_chain = chain
        self._last_asked = asked
        self._last_correct = last_correct
        self._last_state = state

    def trigger(self, context: dict) -> None:
        """Chain aura doesn't respond to one-shot fire() calls -- it's
        a purely observational effect. No-op for API symmetry."""
        return

    def update(self, dt: float, reduced: bool) -> None:
        """Advance timers, interpolate aura colour/opacity, update
        particles. ``dt`` is seconds; the handler internally converts
        to ms where its config is specified in ms."""
        dt_ms = max(0.0, dt) * 1000.0

        # Pulse + burst timers count DOWN toward zero.
        if self._pulse_timer_ms > 0.0:
            self._pulse_timer_ms = max(0.0, self._pulse_timer_ms - dt_ms)
        if self._burst_timer_ms > 0.0:
            self._burst_timer_ms = max(0.0, self._burst_timer_ms - dt_ms)
        if self._static_highlight_ms > 0.0:
            self._static_highlight_ms = max(0.0, self._static_highlight_ms - dt_ms)

        # Aura colour interpolation. Snap when the effect is inactive
        # (e.g. non-math-combat quiz) so a stale aura doesn't bleed in.
        if not self._active:
            self._current_aura_opacity = 0.0
            self._current_aura_color = self._target_aura_color
        else:
            # Smooth interpolation; the 6.0 factor gives ~250 ms to
            # cover 80% of the gap at 60 FPS.
            k = 1.0 - math.exp(-6.0 * max(0.0, dt))
            self._current_aura_opacity += (
                self._target_aura_opacity - self._current_aura_opacity) * k
            self._current_aura_color = _lerp_color(
                self._current_aura_color, self._target_aura_color, k)

        # Particle lifecycle. Reduced-motion mode never spawns particles
        # (the spawn path is gated by `_particles_allowed`), but we
        # still tick existing ones to drain cleanly in case the flag
        # flipped mid-session.
        alive: list[_Particle] = []
        for p in self._particles:
            p.update(dt)
            if p.alive():
                alive.append(p)
        self._particles = alive

    def draw_bg(self, surface: pygame.Surface, panel_rect, reduced: bool) -> None:
        """Draw the persistent border aura behind the quiz panel.

        ``panel_rect`` is a ``pygame.Rect`` (or 4-tuple) marking the
        opaque quiz panel; we paint a slightly-expanded, softly-faded
        glow around it. The opaque panel paints next and naturally
        hides the aura inside the panel rect.

        Also stashes the panel rect so the next ``_spawn_particles``
        call can anchor sparks near the counter (top-right corner of
        the panel) instead of the hardcoded fallback.
        """
        # Stash panel geometry for particle anchoring on next spawn.
        try:
            self._last_panel_rect = pygame.Rect(panel_rect)
        except (TypeError, ValueError):
            self._last_panel_rect = None
        if not self._active:
            return
        try:
            rect = pygame.Rect(panel_rect)
        except (TypeError, ValueError):
            return

        opacity = max(0.0, min(1.0, self._current_aura_opacity))
        # Pulse boost -- a brief highlight on each correct answer rides
        # on top of the persistent aura. Boosted 2026-10-04 after
        # playtest called the effects "lame and understated".
        if self._pulse_timer_ms > 0.0:
            opacity = min(1.0, opacity +
                          0.55 * (self._pulse_timer_ms / self.pulse_duration_ms))
        if opacity <= 0.01:
            return

        color = self._current_aura_color
        # Build an aura surface sized to the expanded panel. Reuse the
        # cached one when dimensions match. Wider pad = more visible
        # glow bleed around the panel.
        pad = 72
        size = (rect.w + pad * 2, rect.h + pad * 2)
        if self._pulse_surf is None or self._pulse_surf_size != size:
            self._pulse_surf = pygame.Surface(size, pygame.SRCALPHA)
            self._pulse_surf_size = size
        aura = self._pulse_surf
        aura.fill((0, 0, 0, 0))

        # Soft outer rings -- 10 steps from the expanded rect inward
        # toward the panel edge, each brighter. More steps + wider pad +
        # higher alpha coefficient = chunky visible glow.
        steps = 10
        for i in range(steps):
            # i=0: outermost + faintest. i=steps-1: innermost + brightest.
            inset = int(pad * (1.0 - i / steps))
            alpha = int(255 * opacity * 0.28 * (i + 1) / steps)
            if alpha <= 0:
                continue
            r = pygame.Rect(inset, inset,
                            size[0] - 2 * inset,
                            size[1] - 2 * inset)
            pygame.draw.rect(aura, (color[0], color[1], color[2], alpha),
                             r, border_radius=18, width=5)

        # Thick solid inner-edge glow riding at the panel perimeter --
        # makes the border read as "lit from behind" at every rank, not
        # just milestones.
        inner_alpha = int(255 * opacity * 0.75)
        if inner_alpha > 0:
            pygame.draw.rect(
                aura, (color[0], color[1], color[2], inner_alpha),
                pygame.Rect(pad - 3, pad - 3, rect.w + 6, rect.h + 6),
                border_radius=12, width=4)

        # Milestone bloom -- adds a BIG bright outline for the first
        # ~1100ms after a milestone crossing. Two concentric rings for
        # weight; outer one slightly dimmer.
        if self._burst_timer_ms > 0.0:
            bloom = self._burst_timer_ms / self.burst_duration_ms
            bloom_alpha = int(255 * opacity * 0.95 * bloom)
            if bloom_alpha > 0:
                pygame.draw.rect(
                    aura, (color[0], color[1], color[2], bloom_alpha),
                    pygame.Rect(pad - 8, pad - 8, rect.w + 16, rect.h + 16),
                    border_radius=14, width=8)
                pygame.draw.rect(
                    aura, (color[0], color[1], color[2], bloom_alpha // 2),
                    pygame.Rect(pad - 22, pad - 22, rect.w + 44, rect.h + 44),
                    border_radius=18, width=6)

        # Static-highlight replacement for milestones when
        # reduced_motion is on. 300ms steady border highlight -- see
        # effects_config.json reduced_motion.replace_milestone.
        if self._static_highlight_ms > 0.0:
            sh = self._static_highlight_color
            pygame.draw.rect(
                aura, (sh[0], sh[1], sh[2], 180),
                pygame.Rect(pad - 2, pad - 2, rect.w + 4, rect.h + 4),
                border_radius=12, width=3)

        surface.blit(aura, (rect.x - pad, rect.y - pad))

    def draw_fg(self, surface: pygame.Surface,
                protected_rects: Iterable, reduced: bool) -> None:
        """Draw particles + any front-of-panel flourishes.

        Particles whose bounding box intersects any protected rect are
        culled -- the question text, choice cards, timer bar, and
        counter area must stay clean. Reduced-motion suppresses all
        particle output entirely.
        """
        if not self._active:
            return
        if 'particles' in self.rm_disable and reduced:
            return
        protected = [pygame.Rect(r) for r in (protected_rects or ())]
        for p in self._particles:
            bbox = p.bbox()
            if any(bbox.colliderect(r) for r in protected):
                continue
            p.draw(surface)

    def draw_overlay(self, surface: pygame.Surface, reduced: bool) -> None:
        """Chain aura never paints top-level overlays. (The fullscreen
        takeover handler owns that phase.)"""
        return

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _matches(self, snapshot: dict) -> bool:
        """Activation gate -- chain aura runs only for math-combat
        chain quizzes. Driven by the ``activates_when`` config block.
        """
        gate = self.activates_when
        if not gate:
            return True
        if 'subject' in gate and snapshot.get('subject') != gate['subject']:
            return False
        want_mode = gate.get('mode')
        if want_mode:
            got = snapshot.get('mode')
            # Accept either the QuizMode enum (`.value`) or a bare str.
            got_val = getattr(got, 'value', got)
            if got_val != want_mode:
                return False
        if gate.get('has_combat_target') and not snapshot.get('has_combat_target'):
            return False
        return True

    def _rank_for(self, chain: int) -> dict:
        """Return the rank dict whose threshold is the highest <= chain."""
        best = self.ranks[0]
        for r in self.ranks:
            if chain >= int(r['threshold']):
                best = r
        return best

    def _particles_allowed(self, reduced: bool) -> bool:
        return not (reduced and 'particles' in self.rm_disable)

    def _on_correct_answer(self, chain: int, reduced: bool = False) -> None:
        """Fire the per-answer pulse + a visible spark burst.

        Boosted 2026-10-04 after playtest: particle counts, intensity,
        and chain-scaling all up. Reduced-motion still suppresses
        particles entirely; the border pulse timer runs regardless.
        """
        self._pulse_timer_ms = float(self.pulse_duration_ms)
        if not self._particles_allowed(reduced):
            return
        rank = self._rank_for(chain)
        color = tuple(int(c) for c in rank['color'])
        # count scales with chain more aggressively (was min(8, chain//2+2))
        self._spawn_particles(count=min(24, 6 + chain),
                              color=color, intensity=1.1)

    def _on_milestone(self, milestone: int, rank: dict,
                      reduced: bool = False) -> None:
        """Fire the longer bloom + a BIG burst for a crossed milestone.

        Reduced-motion mode skips the particle burst and relies on the
        static-highlight replacement (300 ms steady border highlight)
        painted by draw_bg instead -- see the ``replace_milestone``
        key in effects_config.json.

        Boosted 2026-10-04: burst count scales linearly with milestone
        (chain 20 = ~68 particles) rather than clipping at 32.
        """
        self._burst_timer_ms = float(self.burst_duration_ms)
        color = tuple(int(c) for c in rank['color'])
        self._static_highlight_ms = 500.0
        self._static_highlight_color = color
        if not self._particles_allowed(reduced):
            return
        self._spawn_particles(count=min(80, 24 + milestone * 2),
                              color=color, intensity=1.8)

    def _spawn_particles(self, count: int, color: tuple, intensity: float) -> None:
        """Add ``count`` sparks, clipped by the global budget.

        Anchor is computed from the most recent panel rect seen by
        ``draw_bg`` — sparks bloom near the chain counter (top-right
        corner of the quiz panel). Falls back to the ``_Particle``
        class defaults if ``draw_bg`` has not yet painted this scope.
        """
        room = self.particle_budget - len(self._particles)
        if room <= 0:
            return
        count = min(count, room)
        # Resolve anchor from the last panel rect: top-right-interior,
        # roughly where _draw_quiz paints the chain counter.
        if self._last_panel_rect is not None:
            r = self._last_panel_rect
            anchor_x = float(r.right - 160)
            anchor_y = float(r.top + 110)
        else:
            anchor_x = float(_Particle._ANCHOR_X)
            anchor_y = float(_Particle._ANCHOR_Y)
        for _ in range(count):
            # Random direction + modest speed; the particles live for
            # 400-900 ms and fade out via alpha.
            ang = self.rng.uniform(0, 2 * math.pi)
            speed = self.rng.uniform(140, 320) * intensity
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed - 40.0   # slight upward bias
            life = self.rng.uniform(0.7, 1.4)
            # Small jitter around the counter anchor so the burst feels
            # organic rather than radial-from-a-point.
            px = self.rng.uniform(-20, 20)
            py = self.rng.uniform(-10, 10)
            self._particles.append(
                _Particle(px, py, vx, vy, life, color,
                          anchor_x=anchor_x, anchor_y=anchor_y))


class _Particle:
    """Tiny stateful spark. Position is in SCREEN space -- the handler
    picks an anchor on spawn (near the chain counter) and offsets.

    The ``_ANCHOR_X`` / ``_ANCHOR_Y`` class constants are only used as
    a safety fallback when the chain-aura handler hasn't yet seen a
    panel rect (e.g. first-frame edge cases, unit tests without a
    draw pass). Normal gameplay resolves the anchor from the actual
    panel geometry — see ``ChainAuraPulse._spawn_particles``."""

    _ANCHOR_X = 1300    # safety fallback only
    _ANCHOR_Y = 100     # safety fallback only

    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'age', 'color', 'size')

    def __init__(self, px: float, py: float, vx: float, vy: float,
                 life: float, color: tuple,
                 anchor_x: float | None = None,
                 anchor_y: float | None = None):
        if anchor_x is None:
            anchor_x = float(self._ANCHOR_X)
        if anchor_y is None:
            anchor_y = float(self._ANCHOR_Y)
        self.x = float(anchor_x + px)
        self.y = float(anchor_y + py)
        self.vx = vx
        self.vy = vy
        self.life = life
        self.age = 0.0
        self.color = color
        # Bigger sparks after the 2026-10-04 playtest "lame and
        # understated" feedback. 7px core + glow halo.
        self.size = 6

    def alive(self) -> bool:
        return self.age < self.life

    def update(self, dt: float) -> None:
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Gravity drag so sparks arc downward over their lifetime.
        self.vy += 220.0 * dt

    def bbox(self) -> pygame.Rect:
        s = self.size + 3   # halo radius
        return pygame.Rect(int(self.x - s), int(self.y - s), s * 2, s * 2)

    def draw(self, surface: pygame.Surface) -> None:
        frac = max(0.0, 1.0 - self.age / max(0.001, self.life))
        alpha = int(255 * frac)
        if alpha <= 0:
            return
        # Two-layer composite: outer dim halo + bright core. Both ride
        # a tiny per-particle SRCALPHA surface so blit mixes correctly.
        halo_r = self.size + 3
        surf = pygame.Surface((halo_r * 2, halo_r * 2), pygame.SRCALPHA)
        # Outer halo: dim, large
        pygame.draw.circle(
            surf, (self.color[0], self.color[1], self.color[2], alpha // 3),
            (halo_r, halo_r), halo_r)
        # Mid ring
        pygame.draw.circle(
            surf,
            (self.color[0], self.color[1], self.color[2], alpha * 2 // 3),
            (halo_r, halo_r), self.size)
        # Bright core (white-ish inner)
        core_r = max(1, self.size // 2)
        core_col = (
            min(255, self.color[0] + 60),
            min(255, self.color[1] + 60),
            min(255, self.color[2] + 60),
            alpha,
        )
        pygame.draw.circle(surf, core_col, (halo_r, halo_r), core_r)
        surface.blit(surf, (int(self.x - halo_r), int(self.y - halo_r)))


# ----------------------------------------------------------------------
# Config coercion helpers
# ----------------------------------------------------------------------

def _coerce_ranks(raw) -> tuple:
    """Coerce a sequence of rank dicts into a sorted-by-threshold tuple.
    Entries missing fields fall back to safe defaults; corrupt entries
    are dropped silently so one bad rung can't disable the whole aura.
    """
    out: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        try:
            threshold = int(entry.get('threshold', 0))
            color = entry.get('color') or [230, 230, 230]
            color = tuple(int(c) for c in color[:3])
            opacity = float(entry.get('aura_opacity', 0.0))
        except (TypeError, ValueError):
            continue
        name = str(entry.get('name', ''))
        out.append({'threshold': threshold, 'name': name,
                    'color': color, 'aura_opacity': opacity})
    if not out:
        # Fall back to the hardcoded defaults so a corrupt config still
        # lights up the quiz.
        return tuple(_DEFAULT_RANKS)
    out.sort(key=lambda r: r['threshold'])
    return tuple(out)


def _lerp_color(a: tuple, b: tuple, k: float) -> tuple:
    """Linear-interpolate two RGB tuples; clamp output to 0-255."""
    def _lerp(x, y):
        v = x + (y - x) * k
        return max(0, min(255, int(v)))
    return (_lerp(a[0], b[0]), _lerp(a[1], b[1]), _lerp(a[2], b[2]))
