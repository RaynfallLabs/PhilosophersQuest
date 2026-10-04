"""StrikeFinisher -- short closing flourish when a combat quiz ends.

A math-combat chain used to just stop: the quiz panel vanished and the
only closure was a log line. This one-shot paints a brief banner over the
map, scaled by how the attack went, so a big chain gets a visible payoff.

Deliberately small:
  * never blocks input -- play continues underneath;
  * capped at well under a second;
  * confined to the map area (never the sidebar or the message log),
    enforced by painting onto a map-sized scratch surface.

Tiers (picked in ``trigger`` from the context the combat code passes):

    miss     chain 0            small faded "Miss"
    light    chain 1-2          damage number pops and fades
    ranked   named rank (3+)    rank + xN, damage, slash streak, one ring
    big      chain >= big_chain as ranked, plus a second ring + edge glow

A kill swaps the damage line for "<Target> Slain"; it does not add time.

Reduced-motion mode (env var ``PQ_REDUCED_MOTION=1``): static text for
``static_ms``, no rings, streak or drift.
"""
from __future__ import annotations

import pygame

import layout
from fantasy_ui import FP, get_font

_DEFAULT_DURATIONS = {'miss': 350, 'light': 500, 'ranked': 750, 'big': 900}


class StrikeFinisher:
    """One-shot end-of-attack flourish. See module docstring."""

    def __init__(self, config: dict | None = None):
        cfg = dict(config or {})
        durations = dict(_DEFAULT_DURATIONS)
        for key, val in (cfg.get('durations_ms') or {}).items():
            try:
                durations[key] = int(val)
            except (TypeError, ValueError):
                pass
        self.durations_ms = durations
        self.big_chain = int(cfg.get('big_chain') or 10)
        rm = cfg.get('reduced_motion') or {}
        self.rm_static_ms = int(rm.get('static_ms') or 300)

        self._active: bool = False
        self._elapsed_ms: float = 0.0
        self._total_ms: float = 0.0
        self.tier: str = ''
        self._top_line: str = ''
        self._main_line: str = ''
        self._color = FP.WHITE

    # ------------------------------------------------------------------
    # Runtime hooks
    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        return self._active

    def ingest(self, snapshot: dict) -> None:
        """One-shot effect -- observational snapshots are ignored."""
        return

    def tier_for(self, chain: int, rank_name: str) -> str:
        """Which flourish a finished attack earns."""
        if chain <= 0:
            return 'miss'
        if chain >= self.big_chain:
            return 'big'
        if rank_name:
            return 'ranked'
        return 'light'

    def trigger(self, context: dict) -> None:
        """Start the flourish. Re-triggering restarts it, so two attacks
        in quick succession never stack banners."""
        chain = int(context.get('chain') or 0)
        damage = int(context.get('damage') or 0)
        killed = bool(context.get('killed'))
        rank_name = str(context.get('rank_name') or '')
        target = str(context.get('target_name') or '')

        self.tier = self.tier_for(chain, rank_name)
        if self.tier == 'miss':
            self._top_line, self._main_line = '', 'Miss'
            self._color = FP.FADED_TEXT
        else:
            self._top_line = (f"{rank_name}  x{chain}" if rank_name
                              else f"x{chain}")
            if self.tier == 'light':
                self._top_line = ''
            if killed and target:
                self._main_line = f"{target} Slain"
            else:
                self._main_line = f"{damage} Damage"
            color = context.get('rank_color')
            self._color = tuple(color) if (color and rank_name) else FP.WHITE

        total = float(self.durations_ms.get(self.tier, 500))
        if context.get('_reduced_motion'):
            total = min(total, float(self.rm_static_ms))
        self._total_ms = total
        self._elapsed_ms = 0.0
        self._active = True

    def update(self, dt: float, reduced: bool) -> None:
        if not self._active:
            return
        self._elapsed_ms += max(0.0, dt) * 1000.0
        total = self._total_ms
        if reduced:
            total = min(total, float(self.rm_static_ms))
        if self._elapsed_ms >= total:
            self._active = False
            self._elapsed_ms = 0.0

    def reset(self) -> None:
        self._active = False
        self._elapsed_ms = 0.0

    def reset_scope(self, scope_id) -> None:
        """Not scoped to a quiz session: the flourish plays AFTER the
        session ends, so a new session starting must not cut it."""
        return

    def draw_bg(self, surface, panel_rect, reduced: bool) -> None:
        return

    def draw_fg(self, surface, protected_rects, reduced: bool) -> None:
        return

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    @staticmethod
    def map_rect() -> pygame.Rect:
        """The only region the flourish may paint in."""
        return pygame.Rect(layout.MAP_X, 0, layout.MAP_W, layout.GAME_H)

    def draw_overlay(self, surface: pygame.Surface, reduced: bool) -> None:
        if not self._active:
            return
        area = self.map_rect().clip(surface.get_rect())
        if area.w <= 0 or area.h <= 0:
            return
        total = self._total_ms
        if reduced:
            total = min(total, float(self.rm_static_ms))
        p = min(1.0, self._elapsed_ms / max(1.0, total))

        # Quick fade-in, hold, fade out over the last third.
        if p < 0.12:
            fade = p / 0.12
        elif p > 0.66:
            fade = max(0.0, 1.0 - (p - 0.66) / 0.34)
        else:
            fade = 1.0
        if reduced:
            fade = 1.0
        alpha = int(255 * fade)

        # Everything is drawn on a map-sized scratch layer, so nothing can
        # spill onto the sidebar or the message log.
        layer = pygame.Surface(area.size, pygame.SRCALPHA)
        cx = area.w // 2
        cy = int(area.h * 0.24)
        color = self._color
        ease = 1.0 - (1.0 - p) ** 3          # fast out, slow settle

        motion = not reduced
        if motion and self.tier in ('ranked', 'big'):
            # Expanding ring(s) in the rank colour.
            self._ring(layer, cx, cy, 36 + int(150 * ease), color, alpha)
            if self.tier == 'big':
                p2 = max(0.0, (p - 0.18) / 0.82)
                ease2 = 1.0 - (1.0 - p2) ** 3
                self._ring(layer, cx, cy, 24 + int(210 * ease2), color,
                           int(alpha * 0.7))
                # Brief rank-coloured glow hugging the map edge.
                glow_a = int(110 * fade * (1.0 - p))
                if glow_a > 0:
                    for inset, mult in ((0, 1.0), (3, 0.6), (6, 0.3)):
                        pygame.draw.rect(
                            layer, (*color, int(glow_a * mult)),
                            (inset, inset, area.w - inset * 2,
                             area.h - inset * 2), 3)
            # Slash streak sweeping in UNDER the banner text during the
            # first 40% -- an underline flourish, so it never cuts through
            # the letters.
            sweep = min(1.0, p / 0.4)
            half = 190
            x0, y0 = cx - half, cy + 38
            x1 = x0 + int(half * 2 * sweep)
            y1 = y0 - int(12 * sweep)
            pygame.draw.line(layer, (*color, int(alpha * 0.85)),
                             (x0, y0), (x1, y1), 4)
            pygame.draw.line(layer, (255, 255, 255, int(alpha * 0.9)),
                             (x0, y0), (x1, y1), 1)

        drift = int(-14 * ease) if motion else 0
        main_font = get_font('heading', 22 if self.tier == 'miss' else 36)
        self._text(layer, self._main_line, main_font, color, cx,
                   cy + drift, alpha, area.w - 24)
        if self._top_line:
            top_font = get_font('heading', 22)
            self._text(layer, self._top_line, top_font, color, cx,
                       cy + drift - main_font.get_height() // 2
                       - top_font.get_height() // 2 - 4,
                       alpha, area.w - 24)

        surface.blit(layer, area.topleft)

    @staticmethod
    def _ring(layer, cx: int, cy: int, radius: int, color, alpha: int) -> None:
        if alpha <= 0 or radius <= 0:
            return
        pygame.draw.circle(layer, (*color, max(0, min(255, alpha))),
                           (cx, cy), radius, 3)

    @staticmethod
    def _text(layer, text: str, font, color, cx: int, cy: int, alpha: int,
              max_w: int) -> None:
        """Centred text with a dark drop shadow so it reads over any tile."""
        if not text or alpha <= 0:
            return
        from text_layout import truncate_label
        text = truncate_label(text, max_w, font)
        shadow = font.render(text, True, FP.INK)
        shadow.set_alpha(alpha)
        surf = font.render(text, True, color)
        surf.set_alpha(alpha)
        x = cx - surf.get_width() // 2
        y = cy - surf.get_height() // 2
        layer.blit(shadow, (x + 2, y + 2))
        layer.blit(surf, (x, y))
