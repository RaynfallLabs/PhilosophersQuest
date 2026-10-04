"""FullscreenTakeover -- one-shot full-screen flourish handler.

Supersedes the legacy ``_draw_celebration`` + ``QuizEngine.celebrating``
pair. Painted over EVERYTHING via the runtime's top-overlay phase so
the takeover can show up after the quiz has fully ended (quiz state is
already back to STATE_PLAYER by the time Divine Intercession and the
Unicorn boon fire this).

Visual family is the gold rune-circle + candle-glow + headline that
the old celebration used, but parameterised by ``palette`` so each
caller gets its own hue (``gold_white`` for Divine Intercession,
``lavender_white`` for the Unicorn bond). The config also carries a
``duration_ms`` and an ``art`` key -- the latter picks the headline
copy, the former picks how long the takeover holds.

Reduced-motion mode (env var ``PQ_REDUCED_MOTION=1``):
  * Rotating runes are disabled -- a static two-ring frame paints instead.
  * ``shorten_to_ms`` collapses the duration so the full-screen
    takeover doesn't block the player for the full 1.8 s hold.
"""
from __future__ import annotations

import math

import pygame

import layout
from fantasy_ui import (FP, get_font, draw_overlay, draw_rune_circle,
                        draw_candle_glow, draw_glow_text, draw_filigree_bar)


# Fixed art definitions. Keys match the ``art`` field in effect config
# so a config bug can only disable the takeover for its one caller,
# not the whole handler.
_ART_HEADLINES = {
    'divine_intercession': ('HEAVEN HEARS YOU', 'Divine Intercession'),
    'unicorn_bond':        ('THE UNICORN KNEELS', 'A sacred bond is formed'),
}

# Palette definitions -- each gives (primary, bright, pale, overlay_wash).
_PALETTES = {
    'gold_white': {
        'primary': FP.GOLD,
        'bright':  FP.GOLD_BRIGHT,
        'pale':    FP.GOLD_PALE,
        'wash':    (40, 24, 0),
        'glow':    (255, 230, 140),
    },
    'lavender_white': {
        'primary': (200, 170, 240),
        'bright':  (235, 215, 255),
        'pale':    (240, 230, 255),
        'wash':    (36, 24, 44),
        'glow':    (230, 210, 255),
    },
}


class FullscreenTakeover:
    """One-shot full-screen takeover. One instance per registered
    effect id (Divine Intercession and Unicorn-bond each get their
    own, so their timers and art never collide)."""

    def __init__(self, config: dict | None = None):
        cfg = dict(config or {})
        self.duration_ms = int(cfg.get('duration_ms') or 1800)
        self.art = str(cfg.get('art') or '')
        self.palette_name = str(cfg.get('palette') or 'gold_white')
        rm = cfg.get('reduced_motion') or {}
        self.rm_disable = set(rm.get('disable') or [])
        self.rm_shorten_to_ms = int(rm.get('shorten_to_ms') or 0)

        self._active: bool = False
        self._elapsed_ms: float = 0.0
        self._total_ms: float = float(self.duration_ms)
        # Font cache -- resolved lazily so unit tests that import this
        # module without a pygame display still work.
        self._title_font = None
        self._sub_font = None

    # ------------------------------------------------------------------
    # Runtime hooks
    # ------------------------------------------------------------------

    def ingest(self, snapshot: dict) -> None:
        """One-shot effect -- observational snapshots are ignored."""
        return

    def trigger(self, context: dict) -> None:
        """Start the takeover. Re-triggering while already active
        restarts the timer rather than queueing -- the second caller
        wins so a stale trigger from an aborted quiz can't glue two
        hold windows together.
        """
        reduced = bool(context.get('_reduced_motion'))
        base = float(self.duration_ms)
        if reduced and self.rm_shorten_to_ms > 0:
            base = float(self.rm_shorten_to_ms)
        self._total_ms = base
        self._elapsed_ms = 0.0
        self._active = True

    def update(self, dt: float, reduced: bool) -> None:
        if not self._active:
            return
        self._elapsed_ms += max(0.0, dt) * 1000.0
        # Reduced-motion shortening applies retroactively if the flag
        # flipped mid-takeover.
        total = self._total_ms
        if reduced and self.rm_shorten_to_ms > 0:
            total = min(total, float(self.rm_shorten_to_ms))
        if self._elapsed_ms >= total:
            self._active = False
            self._elapsed_ms = 0.0

    def reset(self) -> None:
        self._active = False
        self._elapsed_ms = 0.0

    def reset_scope(self, scope_id) -> None:
        """Takeovers aren't scoped -- no-op for API symmetry."""
        return

    def draw_bg(self, surface, panel_rect, reduced: bool) -> None:
        """The takeover lives entirely in the top-overlay phase so the
        quiz panel underneath (if any) stays unaffected."""
        return

    def draw_fg(self, surface, protected_rects, reduced: bool) -> None:
        """Same -- no in-quiz foreground contribution."""
        return

    def draw_overlay(self, surface: pygame.Surface, reduced: bool) -> None:
        """Paint the current frame of the takeover.

        Mirrors the old ``_draw_celebration`` visual: warm wash overlay
        + two counter-rotating gold rune circles + candle glow +
        filigree-bordered headline. Palette swapped per effect id.
        """
        if not self._active:
            return

        palette = _PALETTES.get(self.palette_name) or _PALETTES['gold_white']
        total = self._total_ms
        if reduced and self.rm_shorten_to_ms > 0:
            total = min(total, float(self.rm_shorten_to_ms))

        # Progress 0 -> 1 across the hold. Used for the overall fade +
        # the rune rotation phase.
        progress = min(1.0, self._elapsed_ms / max(1.0, total))
        # Pulse: 0..1 sinusoid driven by the elapsed time -- same shape
        # the old _draw_celebration used but defined off ms, not the
        # engine's countdown timer.
        t = self._elapsed_ms / 1000.0
        pulse = abs(math.sin(t * 6.0))

        # Overall fade: full brightness through 80% of the hold, then
        # ease to 0 for the last 20% so the takeover peels off cleanly.
        if progress < 0.8:
            fade = 1.0
        else:
            fade = max(0.0, 1.0 - (progress - 0.8) / 0.2)

        # Warm overlay wash.
        wash = palette['wash']
        draw_overlay(surface, alpha=int((180 + 30 * pulse) * fade),
                     color=wash)

        cx = layout.WINDOW_W // 2
        cy = layout.WINDOW_H // 2

        runes_disabled = 'rotating_runes' in self.rm_disable and reduced
        if runes_disabled:
            # Reduced-motion: static two-ring frame instead of rotating runes.
            pygame.draw.circle(
                surface, _rgba(palette['primary'], int(100 * fade)),
                (cx, cy), 280, 2)
            pygame.draw.circle(
                surface, _rgba(palette['bright'], int(80 * fade)),
                (cx, cy), 190, 2)
        else:
            draw_rune_circle(surface, cx, cy, 280,
                             _rgba(palette['primary'],
                                   int((100 + 60 * pulse) * fade)),
                             t * 1.5, 16)
            draw_rune_circle(surface, cx, cy, 190,
                             _rgba(palette['bright'],
                                   int((80 + 60 * pulse) * fade)),
                             -t * 2.0, 10)

        # Candle glow intensity ties to the pulse like the legacy effect.
        draw_candle_glow(surface, cx, cy,
                         intensity=(0.8 + 0.4 * pulse) * fade)

        # Headline + sub-line.
        if self._title_font is None:
            self._title_font = get_font('title', 42, bold=True)
        if self._sub_font is None:
            self._sub_font = get_font('heading', 32)

        headline, sub = _ART_HEADLINES.get(self.art,
                                           ('MAX CHAIN!', 'Perfect Combo!'))
        cel_font = self._title_font
        size = cel_font.size(headline)
        hx = cx - size[0] // 2
        hy = cy - size[1] // 2

        # Filigree bars frame the headline (same chrome the old
        # celebration used so takeovers still feel like a family).
        draw_filigree_bar(surface, cx - 320, cy - 88, 640,
                          _rgba(palette['primary'], int(255 * fade)))

        draw_glow_text(surface, cel_font, headline,
                       _rgba(palette['bright'], int(255 * fade)),
                       (hx, hy),
                       glow_color=_rgba(palette['glow'], int(255 * fade)),
                       glow_r=4)

        draw_filigree_bar(surface, cx - 320, cy + size[1] + 12, 640,
                          _rgba(FP.GOLD_DARK, int(255 * fade)))

        sub_surf = self._sub_font.render(sub, True,
                                         _rgba(palette['pale'],
                                               int(255 * fade))[:3])
        if fade < 1.0:
            sub_surf.set_alpha(int(255 * fade))
        surface.blit(sub_surf,
                     (cx - sub_surf.get_width() // 2,
                      cy + size[1] + 24))

    # ------------------------------------------------------------------
    # Introspection helpers (for tests / preview)
    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        return self._active


def _rgba(color: tuple, alpha: int) -> tuple:
    """Clamp alpha, carry through RGB. Accepts a 3- or 4-tuple color."""
    a = max(0, min(255, int(alpha)))
    return (int(color[0]), int(color[1]), int(color[2]), a)
