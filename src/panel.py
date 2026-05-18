"""Panel composition — the one-stop helper for modal screens.

Every modal that follows the grimoire identity (header / body / footer hint
inside a midnight-blue gold-bordered panel) should be drawn through this
module instead of hand-rolling `pygame.draw.rect(..., border_radius=…)`.

The audit at tools/audit/deliverables/beauty_screen_catalog.md found ~10
screens drawing their own chrome and silently drifting from the rest of
the game's visual family. PanelBuilder closes that loophole by making
the design system the easy path.

Usage example:

    p = PanelBuilder(screen, size=SIZE_LG, border_color=FP.GOLD)
    p.set_title("YOUR PACK & WHAT LIES HERE")
    p.set_tabs(["Weapons", "Armor", "Shields"], active=0)
    p.set_footer_hint("Left/Right: tab   Up/Down: scroll   ESC: close")
    rect = p.body_rect()   # the area the caller draws into
    # ... custom body draw inside `rect` ...
    p.draw()               # paints chrome (header + tabs + footer + border)

The panel computes its own size from `size` and clamps to the current
viewport so nothing overflows on a small laptop screen.
"""
from __future__ import annotations

from typing import Sequence

import pygame

import layout
from fantasy_ui import (FP, get_font, draw_overlay, draw_dark_panel,
                        draw_header_bar, draw_divider)
from text_layout import truncate_label


# Size classes — each picks a target width; the actual width is clamped to
# the live viewport with a 40px margin on each side. Heights are computed
# from content or clamped at the bottom by the same rule.
SIZE_SM   = ('sm', 480)
SIZE_MD   = ('md', 760)
SIZE_LG   = ('lg', 1000)
SIZE_XL   = ('xl', 1280)
SIZE_FULL = ('full', 0)  # full-viewport overlay

# Standard spacing tokens — multiples of 8 for rhythm.
PAD_TIGHT   = 4
PAD_NORMAL  = 8
PAD_LOOSE   = 16
PAD_SECTION = 24

HEADER_H = 44
TAB_BAR_H = 32
FOOTER_HINT_H = 28
SCROLLBAR_W = 6


class PanelBuilder:
    """Composable modal panel — header / tabs / body / footer hint.

    Always paints `draw_overlay` first (full-viewport dim), then the
    midnight-blue gold-bordered panel. Tabs and footer hint are optional;
    body content is drawn by the caller using the rect from body_rect().
    """

    def __init__(self, surf: pygame.Surface,
                 size: tuple = SIZE_LG,
                 border_color: tuple | None = None,
                 max_height: int | None = None,
                 overlay_alpha: int = 185):
        self.surf = surf
        self.size = size
        self.border_color = border_color if border_color is not None else FP.GOLD
        self.overlay_alpha = overlay_alpha

        self._title: str | None = None
        self._title_font = None
        self._tabs: list[str] = []
        self._tab_active: int = 0
        self._tab_counts: list[int] | None = None
        self._footer_hint: str | None = None
        self._footer_color: tuple = FP.HINT_TEXT
        self._scroll_pos: tuple[int, int] | None = None  # (current, total)

        # Compute the outer rect now so callers can ask for body_rect() early
        self._compute_geometry(max_height)

    # ----- builder API -----

    def set_title(self, text: str, font=None) -> 'PanelBuilder':
        self._title = text
        self._title_font = font
        return self

    def set_tabs(self, labels: Sequence[str], active: int = 0,
                 counts: Sequence[int] | None = None) -> 'PanelBuilder':
        self._tabs = list(labels)
        self._tab_active = max(0, min(active, len(self._tabs) - 1))
        self._tab_counts = list(counts) if counts is not None else None
        return self

    def set_footer_hint(self, text: str, dim: bool = False) -> 'PanelBuilder':
        self._footer_hint = text
        self._footer_color = FP.HINT_TEXT_DIM if dim else FP.HINT_TEXT
        return self

    def set_scroll_indicator(self, current: int, total: int) -> 'PanelBuilder':
        """Set "showing M-N of TOTAL" indicator shown at footer-left."""
        self._scroll_pos = (current, total)
        return self

    # ----- geometry -----

    def _compute_geometry(self, max_height: int | None):
        viewport_w = layout.GAME_W
        viewport_h = layout.WINDOW_H

        if self.size[0] == 'full':
            self.bw = viewport_w - 2 * PAD_SECTION
            self.bh = viewport_h - 2 * PAD_SECTION
        else:
            target_w = self.size[1]
            self.bw = min(target_w, viewport_w - 2 * PAD_SECTION)
            # If caller didn't specify max_height, pick a sensible default:
            # 75% of viewport, clamped between 320 and viewport - margin
            if max_height is None:
                self.bh = max(320, int(viewport_h * 0.75))
            else:
                self.bh = max_height
            self.bh = min(self.bh, viewport_h - 2 * PAD_NORMAL)

        self.bx = (viewport_w - self.bw) // 2
        self.by = max(PAD_NORMAL, (viewport_h - self.bh) // 2)

    def body_rect(self) -> pygame.Rect:
        """Return the inner rectangle the caller should draw content into."""
        x = self.bx + PAD_LOOSE
        y = self.by + self._top_chrome_height() + PAD_NORMAL
        w = self.bw - 2 * PAD_LOOSE
        h = self.bh - self._top_chrome_height() - self._bottom_chrome_height() - PAD_LOOSE
        return pygame.Rect(x, y, w, max(1, h))

    def outer_rect(self) -> pygame.Rect:
        return pygame.Rect(self.bx, self.by, self.bw, self.bh)

    def _top_chrome_height(self) -> int:
        h = HEADER_H if self._title else PAD_NORMAL
        if self._tabs:
            h += TAB_BAR_H
        return h

    def _bottom_chrome_height(self) -> int:
        h = 0
        if self._footer_hint or self._scroll_pos:
            h += FOOTER_HINT_H
        return h

    # ----- drawing -----

    def draw(self) -> None:
        """Paint overlay + panel + header + tabs + footer hint.

        Body content must be drawn by the caller *between* body_rect()
        and this call — the order is:
            1) build the PanelBuilder
            2) get body_rect()
            3) draw body content into the rect
            4) call panel.draw() to paint chrome ON TOP (so chrome
               always wins z-order)
        """
        draw_overlay(self.surf, alpha=self.overlay_alpha)
        draw_dark_panel(self.surf,
                        (self.bx, self.by, self.bw, self.bh),
                        border_color=self.border_color)

        title_font = self._title_font or get_font('heading', 22)

        if self._title:
            draw_header_bar(self.surf,
                            (self.bx, self.by, self.bw, HEADER_H),
                            text=self._title,
                            font=title_font,
                            text_color=FP.GOLD_BRIGHT,
                            accent=self.border_color)
            ty = self.by + HEADER_H
        else:
            ty = self.by + PAD_NORMAL

        if self._tabs:
            self._draw_tabs(ty)
            ty += TAB_BAR_H

        # Divider between top chrome and body
        if self._title or self._tabs:
            draw_divider(self.surf, self.bx + PAD_LOOSE,
                         ty + 2, self.bw - 2 * PAD_LOOSE)

        # Footer hint + scroll indicator
        if self._footer_hint or self._scroll_pos:
            self._draw_footer()

    def _draw_tabs(self, top_y: int) -> None:
        tab_font = get_font('small', 14)
        x = self.bx + PAD_LOOSE
        y = top_y + 2
        h = TAB_BAR_H - 6
        for i, label in enumerate(self._tabs):
            count_suffix = ''
            if self._tab_counts and i < len(self._tab_counts):
                count_suffix = f"  ({self._tab_counts[i]})"
            full = label + count_suffix
            tw = tab_font.size(full)[0] + 24
            is_active = (i == self._tab_active)
            bg = FP.GOLD_DARK if is_active else FP.MIDNIGHT_MID
            border = self.border_color if is_active else FP.GOLD_DARK
            rect = pygame.Rect(x, y, tw, h)
            pygame.draw.rect(self.surf, bg, rect, border_radius=4)
            pygame.draw.rect(self.surf, border, rect, 1, border_radius=4)
            text_color = FP.GOLD_BRIGHT if is_active else FP.BODY_TEXT
            ts = tab_font.render(full, True, text_color)
            tx = x + (tw - ts.get_width()) // 2
            tyc = y + (h - ts.get_height()) // 2
            self.surf.blit(ts, (tx, tyc))
            x += tw + PAD_NORMAL

    def _draw_footer(self) -> None:
        font = get_font('small', 14)
        fy = self.by + self.bh - FOOTER_HINT_H + 4

        # Scroll indicator (left side)
        if self._scroll_pos:
            cur, total = self._scroll_pos
            tag = f"{cur}/{total}"
            ts = font.render(tag, True, FP.FADED_TEXT)
            self.surf.blit(ts, (self.bx + PAD_LOOSE, fy + 4))

        # Hint text (centered)
        if self._footer_hint:
            ts = font.render(self._footer_hint, True, self._footer_color)
            tx = self.bx + (self.bw - ts.get_width()) // 2
            self.surf.blit(ts, (tx, fy + 4))

    # ----- convenience: vertical-scroll content body -----

    def draw_scrollable_lines(self, lines: Sequence[tuple],
                              scroll: int, line_h: int = 22) -> int:
        """Paint a vertical list of (text, color, font_or_None) tuples
        into body_rect(), starting at `scroll` lines down.

        Returns the maximum scroll value that keeps content in view —
        the caller uses this to clamp their stored scroll state.
        """
        body = self.body_rect()
        max_visible = max(1, body.h // line_h)
        max_scroll = max(0, len(lines) - max_visible)
        scroll = max(0, min(scroll, max_scroll))

        y = body.y
        for entry in lines[scroll:scroll + max_visible]:
            text, color, font = entry if len(entry) == 3 else (*entry, None)
            font = font or get_font('body', 16)
            surf = font.render(text, True, color)
            self.surf.blit(surf, (body.x, y))
            y += line_h

        # Mini scrollbar (right edge of body) when content scrolls
        if len(lines) > max_visible:
            track_x = body.right - SCROLLBAR_W
            track_y = body.y
            track_h = body.h
            pygame.draw.rect(self.surf, FP.MIDNIGHT_MID,
                             (track_x, track_y, SCROLLBAR_W, track_h),
                             border_radius=2)
            thumb_h = max(20, int(track_h * max_visible / len(lines)))
            thumb_y = track_y + int(track_h * scroll / max(1, len(lines)))
            pygame.draw.rect(self.surf, FP.GOLD_DARK,
                             (track_x, thumb_y, SCROLLBAR_W, thumb_h),
                             border_radius=2)

        return max_scroll
