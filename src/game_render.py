"""Game.render() and every `_draw_*` overlay, extracted from main.py.

This module defines :class:`RenderMixin`, which the real ``Game`` class
inherits.  The mixin owns ONLY rendering — every helper it calls that touches
game state (``self._calc_score()``, ``self._display_name()``, ``self._cycle_tab``,
``self._EQUIP_TABS``, etc.) is resolved through Python's MRO on the concrete
``Game`` subclass.

Live layout values (``GAME_W``, ``WINDOW_H``, ...) are read off the ``layout``
module so a window resize updates the rendering on the next frame without
re-importing.
"""
from __future__ import annotations

import math

import pygame

import layout
from renderer import TILE_SIZE
from geom import monster_at_tile, is_at_tile, occupied_tiles, any_tile_in_set
from fantasy_ui import (FP, get_font, draw_dark_panel,
                         draw_header_bar, draw_divider, draw_shadow_text,
                         draw_glow_text, centered_text, draw_overlay,
                         draw_rune_circle, draw_filigree_bar, draw_candle_glow,
                         draw_menu, wrap_text, ITEM_COLOR)
from items import (Weapon, Armor, Shield, Corpse, Accessory,
                   Wand, Scroll, Spellbook, Ammo, Food, Potion)
from game_helpers import (
    fit_text as _gh_fit_text,
    wrap_text as _gh_wrap_text,
)
from quiz_engine import QuizMode, QuizState
from spells import LEARNABLE_SPELLS
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_EQUIP_MENU, STATE_KIT, STATE_DISCOVERIES,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_CONFIRM_EXIT, STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
    STATE_VICTORY, STATE_DEAD, STATE_REVIEW_MISSED,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
    STATE_SPELL_MENU, STATE_HINT, STATE_EXAMINE,
    STATE_ENCYCLOPEDIA, STATE_DROP_MENU, STATE_DROP_GOLD_INPUT, STATE_DROP_QTY_INPUT,
    STATE_STORY_POPUP, STATE_MYSTERY_APPROACH, STATE_SHOP, STATE_POWER_MENU,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM,
    STATE_THROW_MENU, STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_JUDGMENT, STATE_STUDY,
    STATE_PRAY, STATE_PET_NAME_INPUT,
    STATE_PET_MENU, STATE_PET_FEED, STATE_PET_HEAL, STATE_PET_SPECIALS,
    STATE_QA_WARP_INPUT, STATE_ASCENSION,
)


class RenderMixin:
    def _draw_mystery_approach(self):
        """Draw the mystery encounter overlay."""
        altar = self._active_mystery_altar
        if altar is None:
            self.state = STATE_PLAYER
            return

        from mystery_system import MYSTERIES
        m = MYSTERIES[altar.mystery_id]

        ch = m['challenge']
        body = [m['description'], '']
        ch = m['challenge']
        if ch['mode'] == 'physical':
            body.append(("Challenge: Physical endurance", FP.GOLD_PALE))
        else:
            body.append(
                (f"Challenge: {ch['subject'].capitalize()} - "
                 f"{ch['mode'].replace('_', ' ').title()}", FP.GOLD_PALE)
            )
        if m['key_item']:
            body.append((f"Requires: {m['key_item']['name']}", FP.FADED_TEXT))
        if m.get('gold_cost', 0) > 0:
            body.append((f"Tribute: {m['gold_cost']} gold", FP.FADED_TEXT))
        if m.get('stat_cost'):
            cost_desc = ', '.join(f"{s}{v}" for s, v in m['stat_cost'].items())
            body.append((f"Cost: {cost_desc}", FP.WARNING_TEXT))
        if altar.mystery_id == 'cauldron':
            body.append(("Requires: 3 prepared meals in inventory", FP.FADED_TEXT))

        self._ui_message_card(
            f"{altar.symbol}  {m['name'].upper()}  {altar.symbol}",
            body,
            options=[
                {'key': 'Y', 'label': 'Accept the challenge', 'color': FP.GOLD_BRIGHT},
                {'key': 'N', 'label': 'Leave the altar untouched', 'color': FP.HINT_TEXT},
            ],
            footer="Enter / Space also accepts   |   Esc leaves",
            border_color=altar.color,
            title_color=altar.color,
            max_w=720,
            max_h=460,
        )

    def _draw_page_indicator(self, items, bx, bw, y):
        """Show item count if list is long."""
        total = len(items)
        if total > 9:
            surf = self.font_sm.render(f"({total} items)", True, FP.HINT_TEXT)
            self.screen.blit(surf, (bx + (bw - surf.get_width()) // 2, y))

    MENU_ICON_SIZE = 32

    def _get_menu_sprite(self, item_id: str) -> 'pygame.Surface':
        """Return a MENU_ICON_SIZE sprite for item_id (no glyph -- use
        _draw_menu_icon for fallback).

        Routes through the SAME central resolver as the map
        (renderer._resolve_item_sprite_path) so EVERY fallback -- composite
        material art ("willow_longbow" -> a longbow icon), collapsed ring/amulet,
        ingredient meat-cut, art-less unique -- applies in menus too. These two
        paths used to diverge: the menu path matched only "<id>.png" + corpse, so
        an item with no per-id art showed its icon on the floor but a bare glyph
        in the inventory/equip/cook menus. ONE resolver, no divergence.
        """
        if item_id in self._menu_sprite_cache:
            return self._menu_sprite_cache[item_id]
        from renderer import _resolve_item_sprite_path
        SZ = self.MENU_ICON_SIZE
        path = _resolve_item_sprite_path(item_id)
        if path:
            raw = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.smoothscale(raw, (SZ, SZ))
        else:
            surf = None
        self._menu_sprite_cache[item_id] = surf
        return surf

    def _draw_menu_icon(self, item, x: int, y: int):
        """Blit a menu-sized sprite for an item at (x, y), with glyph fallback."""
        sprite = self._get_menu_sprite(item.id)
        SZ = self.MENU_ICON_SIZE
        if sprite is not None:
            self.screen.blit(sprite, (x, y))
        else:
            # Glyph fallback: draw symbol + color on a dark background
            surf = pygame.Surface((SZ, SZ), pygame.SRCALPHA)
            pygame.draw.rect(surf, (30, 25, 40), (0, 0, SZ, SZ), border_radius=4)
            color = tuple(getattr(item, 'color', [200, 200, 200])[:3])
            symbol = getattr(item, 'symbol', '?')
            glyph_font = self.font_md
            glyph_surf = glyph_font.render(symbol, True, color)
            gx = (SZ - glyph_surf.get_width()) // 2
            gy = (SZ - glyph_surf.get_height()) // 2
            surf.blit(glyph_surf, (gx, gy))
            self.screen.blit(surf, (x, y))

    def _draw_tab_bar(self, tabs, active_idx: int, bx: int, by: int, bw: int,
                      counts: list[int] | None = None):
        """Draw a tab bar that fits within the panel width.
        *tabs* is a list of (label, ...) tuples.  *counts* is optional per-tab
        item counts (empty tabs with count 0 are hidden unless active).
        Returns the y position below the tab bar."""
        tab_y = by + 50
        avail = bw - 20  # horizontal budget
        PAD = 4
        # Build visible tab list: (index, label_text)
        visible = []
        for i, tab in enumerate(tabs):
            label = tab[0]
            c = counts[i] if counts else None
            if c is not None and c == 0 and i != active_idx:
                continue
            text = f"{label} ({c})" if c is not None else label
            visible.append((i, text))
        # Measure total width; if too wide, drop counts
        def _total(entries):
            return sum(self.font_sm.size(t)[0] + 14 + PAD for _, t in entries) - PAD
        if _total(visible) > avail and counts:
            visible = []
            for i, tab in enumerate(tabs):
                c = counts[i] if counts else None
                if c is not None and c == 0 and i != active_idx:
                    continue
                visible.append((i, tab[0]))
        tab_x = bx + 10
        max_x = bx + bw - 10
        for idx, text in visible:
            tw = self.font_sm.size(text)[0] + 14
            if tab_x + tw > max_x:
                break
            rect = pygame.Rect(tab_x, tab_y, tw, 24)
            active = idx == active_idx
            if active:
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, rect, border_radius=4)
                pygame.draw.rect(self.screen, FP.GOLD, rect, 2, border_radius=4)
                col = FP.GOLD_BRIGHT
            else:
                col = FP.FADED_TEXT
            self.screen.blit(self.font_sm.render(text, True, col), (tab_x + 7, tab_y + 3))
            tab_x += tw + PAD
        return tab_y + 28

    def _draw_xyzzy_input(self):
        """Draw the hidden green terminal input — 'Speak the First Word'."""
        from fantasy_ui import get_font
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 520, 200
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Dark terminal background with green border + scanline effect
        pygame.draw.rect(self.screen, (4, 10, 4), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, (0, 180, 60), (bx, by, bw, bh), 2, border_radius=6)
        pygame.draw.rect(self.screen, (0, 80, 30), (bx+3, by+3, bw-6, bh-6), 1, border_radius=4)

        # Faint scanlines
        for sy in range(by + 6, by + bh - 6, 3):
            pygame.draw.line(self.screen, (0, 20, 0, 40), (bx+4, sy), (bx+bw-4, sy))

        font_title = get_font('heading', 20)
        font_input = get_font('body', 22)
        font_hint  = get_font('body', 13)

        # Title
        title = "Speak the First Word"
        title_surf = font_title.render(title, True, (0, 200, 80))
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 24))

        pygame.draw.line(self.screen, (0, 100, 40),
                         (bx + 30, by + 54), (bx + bw - 30, by + 54))

        # Input field with blinking cursor
        self._xyzzy_blink = (self._xyzzy_blink + 1) % 60
        cursor = '_' if self._xyzzy_blink < 30 else ' '
        display_text = '> ' + self._xyzzy_text + cursor

        input_surf = font_input.render(display_text, True, (0, 255, 120))
        self.screen.blit(input_surf, (bx + 40, by + 80))

        # Bottom hint
        hint_surf = font_hint.render("[Enter] to submit  //  [Esc] to cancel", True, (0, 180, 80))
        self.screen.blit(hint_surf, (bx + (bw - hint_surf.get_width()) // 2, by + bh - 30))

    def _draw_xyzzy_confirm(self):
        """Draw the 'WARNING: You are about to hack reality' confirmation."""
        from fantasy_ui import get_font
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 580, 240
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Dark terminal background with amber warning border
        pygame.draw.rect(self.screen, (10, 8, 4), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, (220, 160, 0), (bx, by, bw, bh), 2, border_radius=6)
        pygame.draw.rect(self.screen, (100, 80, 0), (bx+3, by+3, bw-6, bh-6), 1, border_radius=4)

        font_title = get_font('heading', 22)
        font_body  = get_font('body', 18)
        font_btn   = get_font('body', 20)

        # Warning title
        warn_surf = font_title.render("! ! !   W A R N I N G   ! ! !", True, (255, 180, 0))
        self.screen.blit(warn_surf, (bx + (bw - warn_surf.get_width()) // 2, by + 20))

        pygame.draw.line(self.screen, (180, 120, 0),
                         (bx + 20, by + 52), (bx + bw - 20, by + 52))

        # Warning text
        lines = [
            "You are about to hack reality.",
            "Are you sure?",
        ]
        y = by + 66
        for line in lines:
            surf = font_body.render(line, True, (220, 180, 60))
            self.screen.blit(surf, (bx + (bw - surf.get_width()) // 2, y))
            y += font_body.get_height() + 6

        # Yes / No buttons
        sel = getattr(self, '_xyzzy_confirm_sel', 0)
        btn_y = by + bh - 56
        for i, label in enumerate(('[ YES ]', '[ NO ]')):
            bx_btn = bx + bw // 2 - 120 + i * 160
            if i == sel:
                color = (0, 255, 120)
                pygame.draw.rect(self.screen, (0, 60, 30),
                                 (bx_btn - 10, btn_y - 4, 100, 32), border_radius=4)
            else:
                color = (170, 170, 170)
            surf = font_btn.render(label, True, color)
            self.screen.blit(surf, (bx_btn, btn_y))
        hint = get_font('body', 13).render(
            "Left/Right: choose  //  Enter/Y: confirm  //  N/Esc: cancel",
            True, (220, 160, 0))
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                by + bh - 24))

    def _draw_hack_reality_screen(self):
        """Display the Hack Reality result -- green terminal overlay."""
        from fantasy_ui import get_font
        result_lines = getattr(self, '_hack_result_lines', None)
        chain = getattr(self, '_hack_result_chain', 0)
        if result_lines is None:
            self.state = STATE_PLAYER
            return

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = min(760, layout.WINDOW_W - 80), 400
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Dark terminal background with green border
        pygame.draw.rect(self.screen, (8, 16, 8), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, (0, 200, 80), (bx, by, bw, bh), 2, border_radius=6)
        pygame.draw.rect(self.screen, (0, 100, 40), (bx+3, by+3, bw-6, bh-6), 1, border_radius=4)

        font_title = get_font('heading', 22)
        font_body  = get_font('body', 18)
        font_small = get_font('body', 15)

        # Title with chain rating
        _CHAIN_LABELS = {
            0: "XYZZY FAILED",
            1: "Echo",
            2: "Resonance",
            3: "Convergence",
            4: "Transcendence",
            5: "SINGULARITY",
        }
        label = _CHAIN_LABELS.get(chain, "XYZZY")
        bar = '#' * chain + '.' * (5 - chain)
        title_color = (0, 255, 120) if chain > 0 else (255, 60, 60)
        title_surf = font_title.render(f"XYZZY  //  {label}", True, title_color)
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 14))

        bar_surf = font_small.render(f"[{bar}]  depth={chain}/5", True, (0, 180, 80))
        self.screen.blit(bar_surf, (bx + (bw - bar_surf.get_width()) // 2, by + 42))

        pygame.draw.line(self.screen, (0, 120, 50),
                         (bx + 20, by + 62), (bx + bw - 20, by + 62))

        # Result lines (word-wrapped)
        y = by + 76
        for text, color in result_lines:
            wrapped = self._wrap_text("> " + text, font_body, 710)
            for wl in wrapped:
                surf = font_body.render(wl, True, color)
                self.screen.blit(surf, (bx + 24, y))
                y += font_body.get_height() + 4

        # Close prompt (no cooldown shown — keep it hidden)
        close_surf = font_small.render(
            "[ any key ] to close",
            True, (0, 200, 80)
        )
        self.screen.blit(close_surf, (bx + (bw - close_surf.get_width()) // 2, by + bh - 24))

    def _draw_quirks_screen(self):
        """Draw the quirks progress browser as a list plus detail pane."""
        data = getattr(self, '_quirks_data', [])
        unlocked_count = sum(1 for _, _, _, unlocked, _, _ in data if unlocked)
        panel = self._ui_modal_panel(
            f"QUIRKS PROGRESS - {unlocked_count}/{len(data)} UNLOCKED",
            border_color=FP.ARCANE_BRIGHT,
            max_w=1380,
            max_h=740,
        )
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        gutter = 14
        list_w = min(560, max(420, int(body.w * 0.42)))
        list_rect = pygame.Rect(body.x, body.y, list_w, body.h)
        detail_rect = pygame.Rect(list_rect.right + gutter, body.y,
                                  body.w - list_w - gutter, body.h)
        list_body = self._ui_subpanel(list_rect, "Progress List",
                                      border_color=FP.ARCANE_BRIGHT)
        detail_body = self._ui_subpanel(detail_rect, "Selected Quirk",
                                        border_color=FP.ARCANE_BRIGHT)

        if not data:
            self._ui_wrap_text("No quirk progress has been recorded yet.",
                               self.font_md, FP.FADED_TEXT, detail_body)
            self._ui_footer(panel, "ESC: close")
            return

        sel = max(0, min(getattr(self, '_quirks_sel', 0), len(data) - 1))
        self._quirks_sel = sel
        row_h = 60
        visible = max(1, list_body.h // row_h)
        scroll = getattr(self, '_quirks_scroll', 0)
        if sel < scroll:
            scroll = sel
        if sel >= scroll + visible:
            scroll = sel - visible + 1
        scroll = max(0, min(scroll, max(0, len(data) - visible)))
        self._quirks_scroll = scroll

        y = list_body.y
        for idx, (_, name, pct, unlocked, effect, _) in enumerate(
                data[scroll:scroll + visible], start=scroll):
            rect = pygame.Rect(list_body.x, y, list_body.w - 12, row_h - 7)
            selected = idx == sel
            pygame.draw.rect(self.screen,
                             (35, 43, 82) if selected else FP.MIDNIGHT,
                             rect, border_radius=6)
            pygame.draw.rect(self.screen,
                             FP.ARCANE_BRIGHT if selected else FP.ARCANE_DIM,
                             rect, 1, border_radius=6)
            name_col = FP.GOLD_BRIGHT if unlocked else FP.BODY_TEXT
            name_rect = pygame.Rect(rect.x + 10, rect.y + 7, rect.w - 178, 38)
            self._ui_wrap_text(name, get_font('small', 15, bold=True),
                               name_col, name_rect, line_gap=0, max_lines=2)
            if unlocked:
                self._ui_blit_text("UNLOCKED", get_font('small', 12, bold=True),
                                   FP.SUCCESS_TEXT, rect.right - 10,
                                   rect.y + 9, align='right')
                if effect:
                    self._ui_blit_text(effect, get_font('small', 12),
                                       FP.FADED_TEXT, rect.x + 10,
                                       rect.y + 35, max_width=rect.w - 20)
            else:
                self._ui_progress_bar(
                    pygame.Rect(rect.right - 164, rect.y + 24, 112, 10),
                    pct,
                    color=FP.ARCANE_BRIGHT)
                self._ui_blit_text(f"{int(pct * 100)}%", get_font('small', 12),
                                   FP.FADED_TEXT, rect.right - 10,
                                   rect.y + 20, align='right')
            y += row_h

        if len(data) > visible:
            self._ui_scrollbar(list_body, scroll, len(data), visible,
                               color=FP.ARCANE_BRIGHT)

        qid, name, pct, unlocked, effect, trigger = data[sel]
        detail_lines = [
            (name, FP.GOLD_PALE, get_font('heading', 23)),
            (f"Progress: {int(pct * 100)}%", FP.CYAN_ACCENT, self.font_sm),
        ]
        if unlocked:
            detail_lines.append(("Unlocked", FP.SUCCESS_TEXT, self.font_sm))
            if effect:
                detail_lines += [
                    ("Reward", FP.GOLD_BRIGHT, self.font_sm),
                    (effect, FP.BODY_TEXT, self.font_sm),
                ]
            if trigger:
                detail_lines += [
                    ("How it unlocked", FP.GOLD_BRIGHT, self.font_sm),
                    (trigger, FP.FADED_TEXT, self.font_sm),
                ]
        else:
            detail_lines += [
                ("Locked", FP.FADED_TEXT, self.font_sm),
                ("Reward and trigger stay hidden until this quirk unlocks.",
                 FP.BODY_TEXT, self.font_sm),
            ]
        render_lines = []
        for text, color, fnt in detail_lines:
            for line in self._ui_text_lines(text, fnt, detail_body.w - 12):
                render_lines.append((line, color, fnt))
        self._ui_draw_scroll_lines(render_lines, self.font_sm, FP.BODY_TEXT,
                                   detail_body,
                                   getattr(self, '_quirks_detail_scroll', 0),
                                   line_gap=5)
        self._ui_footer(panel, "Up/Down: select   PgUp/PgDn: jump   ESC/W: close")

    def _draw_character_pack_sheet(self):
        from status_effects import EFFECT_INFO
        try:
            from chain_equip import get_chain_subject
        except Exception:
            get_chain_subject = lambda item: getattr(item, 'equip_chain_subject', '') or 'geography'

        self._charsheet_clamp()
        p = self.player
        screen = self.screen
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        font_title = get_font('heading', 25)
        font_head = get_font('body', 15, bold=True)
        font_body = get_font('body', 13)
        font_bold = get_font('body', 13, bold=True)
        font_small = get_font('body', 11)
        font_tiny = get_font('body', 10)
        leather = (82, 24, 22)

        def text(value, font, color, x, y):
            surf = font.render(str(value), True, color)
            screen.blit(surf, (x, y))
            return surf.get_rect(topleft=(x, y))

        def wrapped(value, font, color, rect, line_h=None, max_lines=None):
            line_h = line_h or max(13, font.get_height() - 1)
            lines = self._wrap_text(str(value), font, rect.w)
            if max_lines is not None:
                lines = lines[:max_lines]
            y = rect.y
            for line in lines:
                if y + line_h > rect.bottom:
                    break
                text(line, font, color, rect.x, y)
                y += line_h
            return y

        def panel(rect, title, accent=FP.GOLD):
            pygame.draw.rect(screen, FP.MIDNIGHT, rect, border_radius=8)
            pygame.draw.rect(screen, accent, rect, 2, border_radius=8)
            pygame.draw.rect(screen, FP.MIDNIGHT_MID, rect.inflate(-8, -8), 1, border_radius=5)
            header = pygame.Rect(rect.x + 10, rect.y + 8, rect.w - 20, 30)
            pygame.draw.rect(screen, FP.MIDNIGHT, header, border_radius=5)
            pygame.draw.line(screen, accent, (header.x + 8, header.bottom - 2),
                             (header.right - 8, header.bottom - 2), 1)
            title_s = font_head.render(title.upper(), True, FP.GOLD_BRIGHT)
            screen.blit(title_s, (header.centerx - title_s.get_width() // 2,
                                  header.centery - title_s.get_height() // 2))
            return pygame.Rect(rect.x + 14, header.bottom + 10, rect.w - 28,
                               rect.h - (header.bottom - rect.y) - 20)

        def row_rect(rect, selected=False, focus=False):
            fill = FP.MIDNIGHT_MID if selected else FP.MIDNIGHT
            pygame.draw.rect(screen, fill, rect, border_radius=5)
            pygame.draw.rect(screen, FP.GOLD_BRIGHT if selected and focus else
                             FP.GOLD_DARK if selected else FP.ARCANE_DIM,
                             rect, 1, border_radius=5)

        def chip(rect, label, color, fg=FP.BODY_TEXT):
            pygame.draw.rect(screen, color, rect, border_radius=5)
            label_s = font_bold.render(str(label), True, fg)
            screen.blit(label_s, (rect.centerx - label_s.get_width() // 2,
                                  rect.centery - label_s.get_height() // 2))

        def bar(x, y, w, label, value, max_value, color):
            text(label, font_bold, FP.BODY_TEXT, x, y)
            track = pygame.Rect(x + 36, y + 6, max(20, w - 102), 9)
            pygame.draw.rect(screen, FP.MIDNIGHT, track, border_radius=4)
            ratio = max(0.0, min(1.0, value / max(1, max_value)))
            if ratio:
                pygame.draw.rect(screen, color,
                                 (track.x, track.y, int(track.w * ratio), track.h),
                                 border_radius=4)
            text(f"{value}/{max_value}", font_body, FP.BODY_TEXT, track.right + 8, y - 1)
            return y + 25

        def item_color(item):
            return FP.SLOT_EMPTY if item is None else ITEM_COLOR.get(getattr(item, 'item_class', ''), FP.BODY_TEXT)

        def display_item(item):
            return self._display_name(item) if item is not None else "(empty)"

        def preview_name(item, max_w, selected=False):
            if item is None:
                return "(empty)"
            name = display_item(item)
            if len(self._wrap_text(name, font_small, max_w)) <= 2:
                return name
            if selected:
                return name
            slot = getattr(item, 'slot', '') or getattr(item, 'item_class', 'item')
            if getattr(item, 'equip_chain_mode', ''):
                return f"Chain {slot}"
            if getattr(item, 'is_unique', False):
                return f"Unique {slot}"
            return f"{slot.title()} equipped"

        def bonus_label(key, value):
            if key == 'ac_bonus':
                return f"AC +{value}"
            if key.startswith('resistance_'):
                return f"{key[len('resistance_'):].replace('_', ' ').title()} resist +{value}"
            if key.startswith('stat_bonus_'):
                return f"{key[len('stat_bonus_'):]} {int(value):+d}"
            if key == 'regen_bonus':
                return f"Regen +{value}"
            if key.startswith('status_'):
                return f"{key[len('status_'):].replace('_', ' ').title()} status"
            if key.startswith('passive_'):
                return key[len('passive_'):].replace('_', ' ').title()
            return f"{key.replace('_', ' ').title()}: {value}"

        def tier_lines(item, tier, max_parts=2):
            bonuses = getattr(item, 'tier_bonuses', {}) or {}
            row = bonuses.get(str(tier), bonuses.get(tier, {})) or {}
            labels = [bonus_label(k, v) for k, v in row.items()]
            if len(labels) > max_parts:
                labels = labels[:max_parts] + [f"+{len(row) - max_parts} more"]
            return labels

        def ability_lines(item):
            if item is None:
                return []
            try:
                visible = self._kit_visible_level(item)
            except Exception:
                visible = int(getattr(item, 'id_level', 5))
            if visible < 3:
                return ["Special properties unrevealed. Identify the item to learn more."]
            lines = []
            mode = getattr(item, 'equip_chain_mode', '')
            if mode and getattr(item, 'tier_bonuses', None):
                achieved = int(getattr(item, 'achieved_tier', 0) or 0)
                if achieved:
                    active = ', '.join(tier_lines(item, achieved, 3))
                    if active:
                        lines.append(f"T{achieved} active: {active}")
                lines.append(f"Attunes by {get_chain_subject(item)} {mode.replace('_', ' ')}")
            if isinstance(item, Weapon):
                spec = self._kit_weapon_special(item, visible)
                if spec and spec != '-':
                    lines.append(spec)
            if getattr(item, 'damage_resistances', None):
                bits = ', '.join(f"{k.title()} x{v}" for k, v in item.damage_resistances.items())
                lines.append(f"Resists {bits}")
            fx = getattr(item, 'effects', None) or {}
            if fx:
                if 'stat' in fx:
                    lines.append(f"{fx['stat']} {int(fx.get('amount', 0)):+d}")
                if 'stat2' in fx:
                    lines.append(f"{fx['stat2']} {int(fx.get('amount2', 0)):+d}")
                if 'status' in fx:
                    lines.append(f"Grants {str(fx['status']).replace('_', ' ').title()}")
            cb = getattr(item, 'carry_bonus', None) or {}
            if cb.get('stat') and cb.get('amount'):
                lines.append(f"{cb['stat']} +{cb['amount']} while carried")
            return lines or ["No revealed special abilities."]

        focus = getattr(self, '_charsheet_focus', 'loadout')
        detail_source = self._charsheet_detail_source()
        _src, detail_entry, detail_item = self._charsheet_selection(source=detail_source)
        actions = self._charsheet_actions()

        margin = 22 if layout.WINDOW_W < 1500 else 34
        header_h = 74
        gap = 14
        header = pygame.Rect(margin, margin, layout.WINDOW_W - margin * 2, header_h)
        pygame.draw.rect(screen, FP.MIDNIGHT, header, border_radius=8)
        pygame.draw.rect(screen, FP.GOLD, header, 2, border_radius=8)
        text("CHARACTER / PACK", font_title, FP.GOLD_BRIGHT, header.x + 18, header.y + 12)
        text(f"{getattr(self, 'player_name', 'Adventurer')}   Floor {self.dungeon_level}   Turn {self.turn_count}",
             font_body, FP.FADED_TEXT, header.x + 20, header.y + 44)
        text(f"Wt {p.get_current_weight():.0f}/{p.get_carry_limit()}",
             font_bold, FP.SUCCESS_TEXT, header.right - 198, header.y + 15)
        text(f"Gold {self.player_gold:,}", font_bold, FP.GOLD_BRIGHT,
             header.right - 198, header.y + 40)

        top = header.bottom + 14
        footer_h = font_small.get_height()
        bottom = layout.WINDOW_H - margin - footer_h - 6
        content_h = bottom - top
        left_w = 252 if layout.WINDOW_W < 1500 else 286
        loadout_w = 322 if layout.WINDOW_W < 1500 else 392
        pack_w = 318 if layout.WINDOW_W < 1500 else 382
        detail_w = layout.WINDOW_W - margin * 2 - left_w - loadout_w - pack_w - gap * 3
        if detail_w < 300:
            pack_w = max(284, pack_w - (310 - detail_w))
            detail_w = layout.WINDOW_W - margin * 2 - left_w - loadout_w - pack_w - gap * 3

        profile_rect = pygame.Rect(margin, top, left_w, content_h)
        loadout_rect = pygame.Rect(profile_rect.right + gap, top, loadout_w, content_h)
        pack_rect = pygame.Rect(loadout_rect.right + gap, top, pack_w, content_h)
        detail_rect = pygame.Rect(pack_rect.right + gap, top, detail_w, content_h)

        # Character panel
        body = panel(profile_rect, "Character", FP.GOLD)
        y = body.y
        y = bar(body.x, y, body.w, "HP", p.hp, p.max_hp, FP.DANGER_TEXT)
        y = bar(body.x, y, body.w, "MP", p.mp, p.max_mp, FP.MP_BLUE)
        y = bar(body.x, y, body.w, "SP", p.sp, p.max_sp, FP.SP_GREEN)
        y += 10
        chip_w = (body.w - 10) // 2
        for idx, (name, value) in enumerate([
            ("STR", p.STR), ("CON", p.CON), ("DEX", p.DEX),
            ("INT", p.INT), ("WIS", p.WIS), ("PER", p.PER),
        ]):
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + 10), y + (idx // 2) * 29,
                            chip_w, 24)
            row_rect(r)
            text(name, font_tiny, FP.FADED_TEXT, r.x + 7, r.y + 5)
            col = FP.GOLD_BRIGHT if value >= 13 else FP.DANGER_TEXT if value < 10 else FP.BODY_TEXT
            text(str(value), font_bold, col, r.right - 36, r.y + 3)
        y += 94
        metrics = [
            ("AC", str(p.get_ac()), FP.SUCCESS_TEXT if p.get_ac() <= 5 else FP.GOLD_BRIGHT),
            ("Sight", str(p.get_sight_radius()), FP.BODY_TEXT),
            ("Timer", f"{p.get_quiz_timer('math')}s", FP.GOLD_BRIGHT),
            ("Spells", str(len(getattr(p, 'known_spells', {}))), FP.MP_BLUE_TEXT),
        ]
        for idx, (label, value, col) in enumerate(metrics):
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + 10), y + (idx // 2) * 27,
                            chip_w, 22)
            row_rect(r)
            text(label, font_tiny, FP.FADED_TEXT, r.x + 7, r.y + 4)
            text(value, font_bold, col, r.x + 58, r.y + 3)
        y += 68
        text("Effects", font_bold, FP.GOLD_BRIGHT, body.x, y)
        y += 22
        active = [(eid, dur) for eid, dur in getattr(p, 'status_effects', {}).items() if dur != 0]
        for idx, (eid, dur) in enumerate(active[:4]):
            info = EFFECT_INFO.get(eid)
            name, col = (info[0], info[1]) if info else (eid.replace('_', ' ').title(), FP.BODY_TEXT)
            label = f"{name} {dur}" if dur > 0 else name
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + 10), y + (idx // 2) * 27,
                            chip_w, 22)
            row_rect(r)
            wrapped(label, font_small, col, pygame.Rect(r.x + 7, r.y + 5, r.w - 14, r.h - 7),
                    line_h=12, max_lines=1)
        y += 62
        text("Resistances", font_bold, FP.GOLD_BRIGHT, body.x, y)
        y += 22
        for dtype, mult in list(getattr(p, 'resistances', {}).items())[:5]:
            col = FP.SUCCESS_TEXT if mult < 1 else FP.DANGER_TEXT
            text(dtype.title(), font_body, FP.BODY_TEXT, body.x, y)
            text(f"x{mult:.2f}", font_bold, col, body.x + 110, y)
            y += 21

        # Loadout panel
        body = panel(loadout_rect, "Loadout", FP.CYAN_ACCENT)
        loadout = self._charsheet_loadout_entries()
        summary_h = 108
        slot_row_count = max(1, (len(loadout) + 1) // 2)
        row_h = max(40, min(54, (body.h - summary_h - 12) // slot_row_count))
        col_w = (body.w - 10) // 2
        for idx, entry in enumerate(loadout):
            r = pygame.Rect(body.x + (idx % 2) * (col_w + 10),
                            body.y + (idx // 2) * row_h, col_w, row_h - 5)
            selected = idx == getattr(self, '_charsheet_loadout_idx', 0)
            row_rect(r, selected=selected, focus=(focus == 'loadout'))
            text(entry['label'], font_tiny, FP.FADED_TEXT, r.x + 7, r.y + 5)
            item = entry.get('item')
            name = preview_name(item, r.w - 14, selected=selected)
            wrapped(name, font_small, item_color(item),
                    pygame.Rect(r.x + 7, r.y + 17, r.w - 14, r.h - 17),
                    line_h=13, max_lines=2)

        summary = pygame.Rect(body.x, body.bottom - summary_h, body.w, summary_h)
        pygame.draw.rect(screen, FP.MIDNIGHT, summary, border_radius=6)
        pygame.draw.rect(screen, FP.ARCANE_DIM, summary, 1, border_radius=6)
        text("Kit Summary", font_bold, FP.GOLD_BRIGHT, summary.x + 10, summary.y + 8)
        for i, (label, value, col) in enumerate([
            ("Armor", f"AC {p.get_ac()}", FP.SUCCESS_TEXT),
            ("Carry", f"{p.get_current_weight():.0f}/{p.get_carry_limit()}", FP.SUCCESS_TEXT),
            ("Flat DR", " / ".join(f"{k[:3]} {v}" for k, v in getattr(p, 'damage_resistances', {}).items()) or "-",
             FP.MP_BLUE_TEXT),
            ("Pack", f"{len(self._charsheet_pack_entries(filtered=False))}/26 items", FP.BODY_TEXT),
        ]):
            yy = summary.y + 32 + i * 19
            text(label, font_small, FP.FADED_TEXT, summary.x + 10, yy)
            text(value, font_bold, col, summary.x + 92, yy)

        # Pack panel
        body = panel(pack_rect, "Pack", FP.GOLD)
        active_filter = self._charsheet_current_pack_filter()
        tab_labels = [
            ("1 All", "all", FP.GOLD),
            ("2 Gear", "gear", FP.CYAN_ACCENT),
            ("3 Food", "food", FP.SUCCESS_TEXT),
            ("4 Lore", "lore", FP.MP_BLUE_TEXT),
        ]
        tab_w = (body.w - 18) // 4
        y = body.y
        for idx, (label, key, col) in enumerate(tab_labels):
            r = pygame.Rect(body.x + idx * (tab_w + 6), y, tab_w, 26)
            active = key == active_filter
            pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                             r, border_radius=5)
            pygame.draw.rect(screen, col if active else FP.ARCANE_DIM, r, 1, border_radius=5)
            s = font_small.render(label, True, FP.BODY_TEXT)
            screen.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
        y += 36
        pack = self._charsheet_pack_entries()
        pack_total = len(self._charsheet_pack_entries(filtered=False))
        filter_label = active_filter.title()
        count_y = y
        text(f"{filter_label}: {len(pack)}/{pack_total} shown", font_bold, FP.SUCCESS_TEXT, body.x, count_y)
        y += 26
        pack_row_h = 57
        visible_rows = max(1, (body.bottom - y) // pack_row_h)
        pack_idx = getattr(self, '_charsheet_pack_idx', 0)
        scroll = getattr(self, '_charsheet_pack_scroll', 0)
        if pack_idx < scroll:
            scroll = pack_idx
        if pack_idx >= scroll + visible_rows:
            scroll = pack_idx - visible_rows + 1
        scroll = max(0, min(scroll, max(0, len(pack) - visible_rows)))
        self._charsheet_pack_scroll = scroll
        if len(pack) > visible_rows:
            range_label = f"{scroll + 1}-{min(scroll + visible_rows, len(pack))} of {len(pack)}"
            range_s = font_small.render(range_label, True, FP.HINT_TEXT)
            screen.blit(range_s, (body.right - range_s.get_width(), count_y + 2))
        if not pack:
            empty = "No items in this filter."
            wrapped(empty, font_body, FP.FADED_TEXT,
                    pygame.Rect(body.x, y + 8, body.w, 50), line_h=17)
        for idx, entry in enumerate(pack[scroll:scroll + visible_rows], start=scroll):
            r = pygame.Rect(body.x, y, body.w, pack_row_h - 6)
            selected = idx == pack_idx
            row_rect(r, selected=selected, focus=(focus == 'pack'))
            chip(pygame.Rect(r.x + 7, r.y + 8, 25, 23), entry['letter'], leather)
            item = entry['item']
            self._draw_menu_icon(item, r.x + 40, r.y + 8)
            name = display_item(item)
            wrapped(name, font_bold, item_color(item),
                    pygame.Rect(r.x + 68, r.y + 5, r.w - 77, 31),
                    line_h=15, max_lines=2)
            try:
                idl = self._kit_visible_level(item)
                id_text = f"ID {idl}/5"
            except Exception:
                id_text = "ID -"
            meta = f"{getattr(item, 'item_class', 'item')}   {getattr(item, 'slot', getattr(item, 'item_class', 'item'))}   wt {getattr(item, 'weight', 0):g}   {id_text}"
            text(meta, font_tiny, FP.FADED_TEXT, r.x + 68, r.bottom - 15)
            y += pack_row_h

        # Detail / actions panel
        body = panel(detail_rect, "Item Card", FP.GOLD)
        y = body.y
        if detail_item is None:
            wrapped("Select an equipped item or pack item to inspect it.",
                    font_body, FP.FADED_TEXT, pygame.Rect(body.x, y, body.w, 80), line_h=17)
        else:
            self._draw_menu_icon(detail_item, body.x, y + 2)
            title_x = body.x + 52
            title_font = get_font('heading', 20 if body.w >= 330 else 17)
            title_lines = self._wrap_text(display_item(detail_item), title_font, body.right - title_x)
            for line in title_lines[:4]:
                text(line, title_font, FP.GOLD_BRIGHT, title_x, y)
                y += 22
            text(f"{getattr(detail_item, 'item_class', 'item')} / {getattr(detail_item, 'slot', getattr(detail_item, 'item_class', 'item'))}",
                 font_body, FP.FADED_TEXT, title_x, y + 1)
            y = max(y + 28, body.y + 64)

            if actions:
                cols = 2
                btn_h = 29
                btn_w = (body.w - 6) // 2
                for idx, action in enumerate(actions):
                    r = pygame.Rect(body.x + (idx % cols) * (btn_w + 6),
                                    y + (idx // cols) * 35, btn_w, btn_h)
                    selected = focus == 'actions' and idx == getattr(self, '_charsheet_action_idx', 0)
                    row_rect(r, selected=selected, focus=(focus == 'actions'))
                    text(action['key'], font_bold, FP.GOLD_BRIGHT, r.x + 8, r.y + 7)
                    text(action['label'], font_small, FP.BODY_TEXT, r.x + 30, r.y + 7)
                y += ((len(actions) + 1) // 2) * 35 + 10

            try:
                visible = self._kit_visible_level(detail_item)
            except Exception:
                visible = int(getattr(detail_item, 'id_level', 5))
            meta_rows = [
                ("Weight", f"{getattr(detail_item, 'weight', 0):g}"),
                ("ID", f"{visible}/5" if hasattr(detail_item, 'id_level') else "-"),
            ]
            if hasattr(detail_item, 'buc'):
                meta_rows.append(("BUC", getattr(detail_item, 'buc', 'uncursed') if getattr(detail_item, 'buc_known', False) else "?"))
            if visible >= 3:
                if hasattr(detail_item, 'ac_bonus'):
                    meta_rows.append(("AC", f"+{getattr(detail_item, 'ac_bonus', 0)}"))
                if isinstance(detail_item, Weapon):
                    meta_rows.append(("Damage", self._kit_damage_str(detail_item)))
                if getattr(detail_item, 'equip_chain_mode', ''):
                    meta_rows.append(("Attune", getattr(detail_item, 'equip_chain_mode', '').replace('_', ' ')))
            col_w = (body.w - 10) // 2
            for idx, (label, value) in enumerate(meta_rows[:6]):
                r = pygame.Rect(body.x + (idx % 2) * (col_w + 10),
                                y + (idx // 2) * 28, col_w, 24)
                pygame.draw.rect(screen, FP.MIDNIGHT, r, border_radius=5)
                text(label, font_tiny, FP.FADED_TEXT, r.x + 7, r.y + 5)
                wrapped(str(value), font_small, FP.BODY_TEXT,
                        pygame.Rect(r.x + 66, r.y + 5, r.w - 72, r.h - 6),
                        line_h=12, max_lines=1)
            y += ((len(meta_rows[:6]) + 1) // 2) * 28 + 10

            res = getattr(detail_item, 'damage_resistances', None) or {}
            if visible >= 3 and res:
                r = pygame.Rect(body.x, y, body.w, 42)
                pygame.draw.rect(screen, FP.MIDNIGHT, r, border_radius=5)
                text("Resist", font_tiny, FP.FADED_TEXT, r.x + 7, r.y + 6)
                wrapped(", ".join(f"{k.title()} x{v}" for k, v in res.items()),
                        font_small, FP.BODY_TEXT,
                        pygame.Rect(r.x + 78, r.y + 6, r.w - 86, r.h - 8),
                        line_h=14)
                y += r.h + 8

            text("Special Abilities", font_bold, FP.GOLD_BRIGHT, body.x, y)
            y += 22
            for line in ability_lines(detail_item)[:6]:
                for seg in self._wrap_text(line, font_small, body.w)[:2]:
                    if y + 14 > body.bottom - 88:
                        break
                    text(seg, font_small, FP.BODY_TEXT, body.x, y)
                    y += 15
                if y + 14 > body.bottom - 88:
                    break
            y += 8

            tiers = getattr(detail_item, 'tier_bonuses', None)
            if tiers and y + 58 < body.bottom:
                text("Chain Unlocks", font_bold, FP.GOLD_BRIGHT, body.x, y)
                y += 23
                achieved = int(getattr(detail_item, 'achieved_tier', 0) or 0)
                if body.w < 340:
                    chip_gap = 6
                    chip_w = (body.w - chip_gap * 4) // 5
                    for tier in range(1, 6):
                        active = tier <= achieved
                        r = pygame.Rect(body.x + (tier - 1) * (chip_w + chip_gap), y, chip_w, 28)
                        pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                                         r, border_radius=5)
                        pygame.draw.rect(screen, FP.SUCCESS_TEXT if tier == achieved else FP.GOLD_DARK if active else FP.ARCANE_DIM,
                                         r, 1, border_radius=5)
                        s = font_bold.render(f"T{tier}", True, FP.SUCCESS_TEXT if active else FP.FADED_TEXT)
                        screen.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
                    y += 38
                    active = "; ".join(tier_lines(detail_item, max(1, achieved), 3))
                    wrapped(f"T{achieved} active: {active}", font_small, FP.BODY_TEXT,
                            pygame.Rect(body.x, y, body.w, body.bottom - y), line_h=14, max_lines=3)
                else:
                    for tier in range(1, 6):
                        if y + 34 > body.bottom:
                            break
                        active = tier <= achieved
                        detail = "; ".join(tier_lines(detail_item, tier, 2)) or "?"
                        lines = self._wrap_text(detail, font_small, body.w - 58)
                        r = pygame.Rect(body.x, y, body.w, max(31, 10 + len(lines[:2]) * 14))
                        pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                                         r, border_radius=5)
                        pygame.draw.rect(screen, FP.SUCCESS_TEXT if tier == achieved else FP.GOLD_DARK if active else FP.ARCANE_DIM,
                                         r, 1, border_radius=5)
                        chip(pygame.Rect(r.x + 7, r.y + 6, 34, 20), f"T{tier}",
                             FP.SUCCESS_TEXT if active else leather,
                             FP.MIDNIGHT if active else FP.BODY_TEXT)
                        wrapped(detail, font_small, FP.BODY_TEXT if active else FP.FADED_TEXT,
                                pygame.Rect(r.x + 50, r.y + 7, r.w - 58, r.h - 9),
                                line_h=14, max_lines=2)
                        y += r.h + 5

        footer = "Arrows: move focus   1-4/Tab: filter pack   Enter: actions/select   E/U/I/X/D: action   ESC: close"
        hint = font_small.render(footer, True, FP.HINT_TEXT)
        screen.blit(hint, (header.centerx - hint.get_width() // 2,
                           layout.WINDOW_H - margin - hint.get_height()))

    def _draw_character_sheet(self):
        self._draw_character_pack_sheet()
        return
        from fantasy_ui import FP, get_font
        from items import ARMOR_SLOTS
        from status_effects import EFFECT_INFO

        p = self.player

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        margin = 16
        bw = min(920, max(360, layout.GAME_W - margin * 2))
        bh = min(720, max(360, layout.WINDOW_H - margin * 2))
        bx = max(margin, (layout.GAME_W - bw) // 2)
        by = max(margin, (layout.WINDOW_H - bh) // 2)

        # Panel background — consistent gold/midnight theme
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)

        font_title = get_font('heading', 24)
        font_head  = get_font('heading', 18)
        font_body  = get_font('body', 16)
        font_small = get_font('body', 14)
        max_text_w = bw - 48

        # Build lines: list of (text, color, font, is_section_header)
        lines = []
        GOLD   = FP.GOLD_BRIGHT
        WHITE  = FP.BODY_TEXT
        DIM    = FP.FADED_TEXT
        GREEN  = FP.SUCCESS_TEXT
        RED    = FP.DANGER_TEXT
        CYAN   = FP.CYAN_ACCENT
        PURPLE = FP.ARCANE_ACCENT

        # --- Stats ---
        lines.append(("PRIMARY STATS", GOLD, font_head, True))
        stat_names = [('STR', 'Strength'), ('CON', 'Constitution'), ('DEX', 'Dexterity'),
                      ('INT', 'Intelligence'), ('WIS', 'Wisdom'), ('PER', 'Perception')]
        for abbr, full in stat_names:
            val = getattr(p, abbr)
            color = GREEN if val > 10 else RED if val < 10 else WHITE
            lines.append((f"  {abbr} {val:>3}  ({full})", color, font_body, False))

        # --- Resources ---
        lines.append(("", DIM, font_small, False))
        lines.append(("RESOURCES", GOLD, font_head, True))
        lines.append((f"  HP:  {p.hp} / {p.max_hp}", GREEN if p.hp > p.max_hp * 0.5 else RED, font_body, False))
        lines.append((f"  SP:  {p.sp} / {p.max_sp}", GREEN if p.sp > 60 else RED, font_body, False))
        lines.append((f"  MP:  {p.mp} / {p.max_mp}", CYAN, font_body, False))
        lines.append((f"  AC:  {p.get_ac()}  (lower is better)", WHITE, font_body, False))
        lines.append((f"  Gold: {self.player_gold}", FP.GOLD_BRIGHT, font_body, False))

        # --- Carry weight ---
        cur_w = p.get_current_weight()
        max_w = p.get_carry_limit()
        pct = cur_w / max_w if max_w > 0 else 0
        w_color = GREEN if pct < 0.7 else FP.WARNING_TEXT if pct < 0.9 else RED
        lines.append((f"  Weight: {cur_w:.1f} / {max_w}  ({pct*100:.0f}%)", w_color, font_body, False))

        # --- Derived stats ---
        lines.append(("", DIM, font_small, False))
        lines.append(("DERIVED STATS", GOLD, font_head, True))
        lines.append((f"  Sight radius:  {p.get_sight_radius()} tiles", WHITE, font_body, False))
        timer_mod = p.get_quiz_timer_modifier()
        math_t = round(p.get_quiz_timer('math') * timer_mod, 1)
        econ_t = round(p.get_quiz_timer('economics') * timer_mod, 1)
        lines.append((f"  Quiz timer:    {math_t}s (combat) to {econ_t}s (text-heavy)  x{timer_mod}", WHITE, font_body, False))
        int_bonus = p.get_int_quiz_bonus()
        if int_bonus > 0:
            lines.append((f"    +{int_bonus}s on magic subjects (INT bonus)", DIM, font_small, False))

        # --- Equipment ---
        lines.append(("", DIM, font_small, False))
        lines.append(("EQUIPMENT", GOLD, font_head, True))
        slot_items = [
            ('Weapon', p.weapon),
            ('Shield', p.shield),
        ]
        for i, slot_name in enumerate(ARMOR_SLOTS):
            slot_items.append((slot_name.title(), p.armor_slots[i]))
        for i, acc in enumerate(p.accessory_slots):
            slot_items.append((f"Ring {i+1}", acc))
        slot_items.append(('Amulet', p.amulet_slot))
        slot_items.append(('Belt', getattr(p, 'belt_slot', None)))

        # Truncate the item name so the full line never runs off the
        # right edge of the panel. The full name is still discoverable
        # in the inventory / Kit screens.
        from text_layout import truncate_label
        for label, item in slot_items:
            if item:
                name = self._display_name(item)
                enchant = getattr(item, 'enchant_bonus', 0)
                cursed = getattr(item, 'cursed', False)
                suffix = ""
                if enchant != 0:
                    suffix += f" +{enchant}" if enchant > 0 else f" {enchant}"
                if cursed:
                    suffix += " {cursed}"
                prefix = f"  {label:8s}: "
                prefix_w = font_body.size(prefix)[0]
                suffix_w = font_body.size(suffix)[0]
                name_max = max(40, max_text_w - prefix_w - suffix_w)
                name_fit = truncate_label(name, name_max, font_body)
                lines.append((f"{prefix}{name_fit}{suffix}", WHITE, font_body, False))
            else:
                lines.append((f"  {label:8s}: (empty)", DIM, font_body, False))

        # --- Status Effects ---
        active_effects = [(eid, dur) for eid, dur in p.status_effects.items() if dur != 0]
        if active_effects:
            lines.append(("", DIM, font_small, False))
            lines.append(("STATUS EFFECTS", GOLD, font_head, True))
            for eid, dur in sorted(active_effects, key=lambda x: x[0]):
                info = EFFECT_INFO.get(eid)
                if info:
                    display_name, color, desc = info
                else:
                    display_name, color, desc = eid.replace('_', ' ').title(), WHITE, ''
                dur_str = "permanent" if dur == -1 else f"{dur} turns"
                # Try to find source
                source = self._get_effect_source(eid)
                src_str = f"  ({source})" if source else ""
                lines.append((f"  {display_name}: {dur_str}{src_str}", color, font_body, False))
                if desc:
                    lines.append((f"    {desc}", DIM, font_small, False))

        # --- Item Passives (effects from carried items, not status effects) ---
        item_passives = []
        if any(getattr(i, 'id', '') == 'charmander_stuffie' for i in p.inventory):
            item_passives.append(("Fire Protection", FP.PASSIVE_FIRE,
                                  "50% fire damage reduction (Charmander Stuffie)"))
            fb_cd = p.power_cooldowns.get('stuffie_fire_breath', 0)
            if fb_cd > 0:
                item_passives.append(("Fire Breath", DIM,
                                      f"Cooling down: {fb_cd} turns"))
            else:
                item_passives.append(("Fire Breath", FP.PASSIVE_FIRE,
                                      "Ready (V key > Fire Breath)"))
        if getattr(p, 'amulet_slot', None) and getattr(p.amulet_slot, 'id', '') == 'rands_heart':
            item_passives.append(("Death Ward", FP.PASSIVE_WARD,
                                  "Prevents one death, restores full HP/MP/SP, clears debuffs (Rand's Heart)"))
        if any(getattr(i, 'id', '') == 'dreamspun_sketchbook' for i in p.inventory):
            sk_cd = p.power_cooldowns.get('sketch_manifest', 0)
            if sk_cd > 0:
                item_passives.append(("Manifest", DIM,
                                      f"Cooling down: {sk_cd} turns"))
            else:
                item_passives.append(("Manifest", FP.PASSIVE_MANIFEST,
                                      "Ready (V key > Manifest)"))
        if item_passives:
            lines.append(("", DIM, font_small, False))
            lines.append(("ITEM PASSIVES", GOLD, font_head, True))
            for name, color, desc in item_passives:
                lines.append((f"  {name}", color, font_body, False))
                lines.append((f"    {desc}", DIM, font_small, False))

        # --- Resistances ---
        if p.resistances:
            lines.append(("", DIM, font_small, False))
            lines.append(("DAMAGE RESISTANCES", GOLD, font_head, True))
            for dtype, mult in sorted(p.resistances.items()):
                if mult == 0.0:
                    r_str = "Immune"
                    r_color = GREEN
                elif mult < 1.0:
                    r_str = f"{(1.0-mult)*100:.0f}% reduction"
                    r_color = FP.SP_GREEN
                else:
                    r_str = f"{(mult-1.0)*100:.0f}% vulnerability"
                    r_color = RED
                lines.append((f"  {dtype.title():12s}: {r_str}  (x{mult:.2f})", r_color, font_body, False))

        # --- Spells ---
        if p.known_spells:
            lines.append(("", DIM, font_small, False))
            lines.append(("KNOWN SPELLS", GOLD, font_head, True))
            for spell_id, cost in sorted(p.known_spells.items()):
                spell_name = spell_id.replace('_', ' ').title()
                lines.append((f"  {spell_name}  ({cost} MP)", PURPLE, font_body, False))

        # --- Cooldowns ---
        cds = []
        if p.prayer_cooldown > 0:
            cds.append(f"Prayer: {p.prayer_cooldown}t")
        if p.recall_lore_cooldown > 0:
            cds.append(f"Recall Lore: {p.recall_lore_cooldown}t")
        # Hack Reality cooldown is intentionally hidden from the UI
        if cds:
            lines.append(("", DIM, font_small, False))
            lines.append(("COOLDOWNS", GOLD, font_head, True))
            for cd in cds:
                lines.append((f"  {cd}", FP.AMBER_ACCENT, font_body, False))

        # --- Game stats ---
        lines.append(("", DIM, font_small, False))
        lines.append(("GAME STATISTICS", GOLD, font_head, True))
        lines.append((f"  Dungeon level:   {self.dungeon_level}", WHITE, font_body, False))
        lines.append((f"  Turns elapsed:   {self.turn_count}", WHITE, font_body, False))
        correct = getattr(self, 'correct_answers', 0)
        wrong = getattr(self, 'wrong_answers', 0)
        total_q = correct + wrong
        acc = (correct / total_q * 100) if total_q > 0 else 0
        lines.append((f"  Questions:       {correct}/{total_q} correct ({acc:.0f}%)", WHITE, font_body, False))
        kills = getattr(self, 'monsters_killed', 0)
        lines.append((f"  Monsters slain:  {kills}", WHITE, font_body, False))
        lines.append((f"  Quirks unlocked: {len(p.unlocked_quirks)}", WHITE, font_body, False))

        # --- Render with scrolling ---
        scroll = getattr(self, '_charsheet_scroll', 0)
        content_top = by + 58
        content_bot = by + bh - 28
        avail_h = content_bot - content_top
        line_h = 20

        max_scroll = max(0, len(lines) - avail_h // line_h)
        scroll = min(scroll, max_scroll)
        self._charsheet_scroll = scroll

        # Title — consistent gold header
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="CHARACTER SHEET",
                        font=font_title, text_color=FP.GOLD_BRIGHT)
        draw_divider(self.screen, bx + 20, by + 50, bw - 40)

        # Clip and render lines (word-wrapped)
        y = content_top
        for idx in range(scroll, len(lines)):
            if y + line_h > content_bot:
                break
            text, color, font, is_header = lines[idx]
            if not text:
                y += 6  # spacer
                continue
            wrapped = self._wrap_text(text, font, max_text_w)
            for wl in wrapped:
                if y + line_h > content_bot:
                    break
                surf = font.render(wl, True, color)
                self.screen.blit(surf, (bx + 24, y))
                y += line_h
            if is_header:
                y += 4

        # Scroll indicator
        if max_scroll > 0:
            pct = scroll / max_scroll if max_scroll > 0 else 0
            track_h = content_bot - content_top - 20
            thumb_h = max(20, int(track_h * avail_h / (len(lines) * line_h)))
            thumb_y = content_top + int(pct * (track_h - thumb_h))
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, (bx + bw - 18, content_top, 8, track_h))
            pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx + bw - 18, thumb_y, 8, thumb_h), border_radius=3)

        # Footer
        footer = font_small.render(
            "Up/Down: scroll   PgUp/PgDn: jump   ESC: close", True, FP.HINT_TEXT)
        self.screen.blit(footer, (bx + (bw - footer.get_width()) // 2, by + bh - 22))

    def _draw_cow_encounter(self):
        """Draw the cow dialog overlay."""
        desc = (
            "A cow stands here, alone in the dungeon. It stares at you with "
            "large brown eyes, chewing slowly. This is deeply unusual. Moo."
        )
        if self._cow_dialog_phase == 'options':
            body = [desc]
            if self._cow_poke_count > 0:
                body.extend([
                    '',
                    (f"You have poked this cow {self._cow_poke_count} "
                     f"time{'s' if self._cow_poke_count != 1 else ''}.",
                     FP.FADED_TEXT),
                ])
            options = [
                {'key': '1', 'label': 'Feed the cow (costs an ingredient)',
                 'color': FP.SUCCESS_TEXT},
                {'key': '2', 'label': 'Walk away. That was weird.',
                 'color': FP.HINT_TEXT},
                {'key': '3', 'label': 'Poke the cow.',
                 'color': FP.WARNING_TEXT},
            ]
            footer = "Esc also walks away"
        else:
            body = [desc]
            options = None
            footer = "Enter / Space / Esc: continue"

        self._ui_message_card(
            "A COW",
            body,
            options=options,
            footer=footer,
            border_color=FP.AMBER_ACCENT,
            title_color=FP.GOLD_BRIGHT,
            max_w=700,
            max_h=390,
        )
        return

        draw_overlay(self.screen, 190)

        bw, bh = 600, 320
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=(180, 140, 80))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="A COW",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)
        draw_divider(self.screen, bx + 20, by + 50, bw - 40)

        font = get_font('body', 18)
        y = by + 62

        desc_lines = self._wrap_text(
            "A cow stands here, alone in the dungeon. It stares at you with "
            "large brown eyes, chewing slowly. This is deeply unusual. Moo.",
            font, bw - 50
        )
        for line in desc_lines:
            self.screen.blit(font.render(line, True, FP.BODY_TEXT), (bx + 25, y))
            y += 24

        y += 12

        if self._cow_dialog_phase == 'options':
            options = [
                ("[1] Feed the cow (costs an ingredient)", FP.SUCCESS_TEXT),
                ("[2] Walk away. That was weird.", FP.HINT_TEXT),
                ("[3] Poke the cow.", FP.WARNING_TEXT),
            ]
            for text, color in options:
                self.screen.blit(font.render(text, True, color), (bx + 30, y))
                y += 28

            if self._cow_poke_count > 0:
                poke_hint = font.render(
                    f"(You have poked this cow {self._cow_poke_count} time{'s' if self._cow_poke_count != 1 else ''})",
                    True, FP.FADED_TEXT
                )
                self.screen.blit(poke_hint, (bx + 30, y + 8))
        else:
            hint = font.render("Press ENTER to continue", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 40))

    def _draw_npc_encounter(self):
        """Draw the NPC moral encounter overlay — multi-phase."""
        enc = self._npc_encounter_active
        if enc is None:
            return

        border = tuple(enc['color'])
        phase = self._npc_encounter_phase
        phase_label = {
            'text': 'ENCOUNTER',
            'options': 'CHOICE',
            'select_item': 'OFFER',
            'outcome': 'RESULT',
        }.get(phase, 'ENCOUNTER')

        draw_overlay(self.screen, 190)
        bw = min(860, layout.GAME_W - 48)
        bh = min(560, layout.WINDOW_H - 48)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=enc['name'].upper(),
                        font=get_font('heading', 20),
                        text_color=border,
                        accent=border)
        self._ui_chip(pygame.Rect(bx + bw - 136, by + 10, 110, 28),
                      phase_label, active=True, color=border)
        draw_divider(self.screen, bx + 20, by + 54, bw - 40)

        body_rect = pygame.Rect(bx + 30, by + 72, bw - 60, bh - 124)
        font = get_font('body', 17)

        if phase == 'text':
            self._ui_wrap_text(enc['text'], font, FP.PARCHMENT_LIGHT,
                               body_rect, line_gap=4)
            self._ui_footer(panel, "Enter / Space: continue   |   Esc: walk away")
            return

        if phase == 'options':
            y = body_rect.y
            self._ui_blit_text("Choose what you do next.",
                               get_font('body', 16), FP.FADED_TEXT,
                               body_rect.x, y)
            y += 32
            row_h = 58
            for i, opt in enumerate(enc['options']):
                row = pygame.Rect(body_rect.x, y, body_rect.w, row_h)
                self._ui_action_row(row, str(i + 1), opt['label'],
                                    color=FP.PARCHMENT_LIGHT)
                y += row_h + 10
            self._ui_footer(panel, "1-3: choose   |   Esc: walk away")
            return

        if phase == 'select_item':
            selected = getattr(self, '_npc_selected_option', None) or {}
            y = body_rect.y
            self._ui_wrap_text(selected.get('label', 'Choose an item to give:'),
                               get_font('body', 16), FP.PARCHMENT_LIGHT,
                               pygame.Rect(body_rect.x, y, body_rect.w, 44),
                               line_gap=2, max_lines=2)
            y += 54
            items = self._npc_item_list
            visible = items[self._npc_item_scroll:self._npc_item_scroll + 9]
            row_h = 36
            list_rect = pygame.Rect(body_rect.x, y, body_rect.w - 10,
                                    body_rect.bottom - y)
            for i, item in enumerate(visible):
                row = pygame.Rect(list_rect.x, y, list_rect.w, row_h)
                self._ui_action_row(row, chr(97 + i), self._display_name(item),
                                    color=FP.PARCHMENT_LIGHT)
                y += row_h + 6
            self._ui_scrollbar(list_rect, self._npc_item_scroll,
                               len(items), 9, color=border)
            self._ui_footer(panel, "a-z: select item   |   Up/Down: scroll   |   Esc: back")
            return

        if phase == 'outcome':
            self._ui_wrap_text(self._npc_outcome_text, font,
                               FP.PARCHMENT_LIGHT, body_rect, line_gap=4)
            self._ui_footer(panel, "Enter / Space / Esc: continue")
            return

        from fantasy_ui import get_font as old_get_font, draw_overlay as old_draw_overlay, draw_dark_panel as old_draw_dark_panel, draw_header_bar as old_draw_header_bar

        enc = self._npc_encounter_active
        if enc is None:
            return

        draw_overlay(self.screen, 190)

        bw, bh = min(780, layout.GAME_W - 40), 440
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh),
                        border_color=tuple(enc['color']))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=enc['name'].upper(),
                        font=get_font('heading', 20),
                        text_color=tuple(enc['color']))

        font = get_font('body', 17)
        font_sm = get_font('body', 15)
        max_w = bw - 50

        phase = self._npc_encounter_phase

        if phase == 'text':
            self._draw_npc_wordwrap(enc['text'], font, bx + 25, by + 54,
                                    max_w, FP.PARCHMENT_LIGHT, line_h=22)
            footer = font_sm.render("Press ENTER to continue",
                                    True, FP.HINT_TEXT)
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'options':
            y = by + 54
            # Options — all same color, no karma hints
            for i, opt in enumerate(enc['options']):
                label = opt['label']
                col = FP.PARCHMENT_LIGHT
                prefix = f"[{i+1}] "
                opt_text = f"{prefix}{label}"
                # Word-wrap long labels
                wrapped = self._wordwrap_text(opt_text, font_sm, max_w - 10)
                for wline in wrapped:
                    surf = font_sm.render(wline, True, col)
                    self.screen.blit(surf, (bx + 30, y))
                    y += 20
                y += 8

            footer = font_sm.render("Press 1-3 to choose, ESC to walk away",
                                    True, FP.HINT_TEXT)
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'select_item':
            y = by + 54
            header = font.render("Choose an item to give:", True, FP.PARCHMENT_LIGHT)
            self.screen.blit(header, (bx + 25, y))
            y += 30

            items = self._npc_item_list
            visible = items[self._npc_item_scroll:self._npc_item_scroll + 9]
            for i, item in enumerate(visible):
                dname = self._display_name(item)
                txt = f"[{chr(97 + i)}] {dname}"
                surf = font_sm.render(txt, True, FP.PARCHMENT_LIGHT)
                self.screen.blit(surf, (bx + 30, y))
                y += 22

            if len(items) > 9:
                scroll_hint = font_sm.render(
                    f"({self._npc_item_scroll + 1}-"
                    f"{min(self._npc_item_scroll + 9, len(items))}"
                    f" of {len(items)}, arrows to scroll)",
                    True, FP.HINT_TEXT)
                self.screen.blit(scroll_hint, (bx + 30, y + 8))

            footer = font_sm.render("Press a-z to select, ESC to go back",
                                    True, FP.HINT_TEXT)
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'outcome':
            self._draw_npc_wordwrap(self._npc_outcome_text, font,
                                    bx + 25, by + 54, max_w,
                                    FP.PARCHMENT_LIGHT, line_h=22)
            footer = font_sm.render("Press ENTER to continue",
                                    True, FP.HINT_TEXT)
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

    def _draw_npc_wordwrap(self, text: str, font, x: int, y: int,
                            max_w: int, color: tuple, line_h: int = 22):
        """Helper: word-wrap and draw text for NPC encounter screens."""
        words = text.split()
        lines, line = [], []
        for word in words:
            test = ' '.join(line + [word])
            if font.size(test)[0] > max_w:
                if line:
                    lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(' '.join(line))
        for txt_line in lines:
            surf = font.render(txt_line, True, color)
            self.screen.blit(surf, (x, y))
            y += line_h

    def _wordwrap_text(self, text: str, font, max_w: int) -> list[str]:
        """Return a list of word-wrapped lines for the given text."""
        words = text.split()
        lines, line = [], []
        for word in words:
            test = ' '.join(line + [word])
            if font.size(test)[0] > max_w:
                if line:
                    lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(' '.join(line))
        return lines

    def _draw_judgment(self):
        """Draw the Altar of the Last Judgment result overlay."""
        if self.karma > 0:
            border = FP.GOLD
            judgment = "Mercy remembered"
        elif self.karma < 0:
            border = FP.BLOOD
            judgment = "Debt remembered"
        else:
            border = FP.FADED_TEXT
            judgment = "Balance remembered"

        body = [
            (f"Karma: {self.karma} - {judgment}", border),
            '',
        ]
        body.extend((line, border if line.isupper() else FP.PARCHMENT_LIGHT)
                    for line in self._judgment_text.splitlines())
        self._ui_message_card(
            "THE ALTAR OF THE LAST JUDGMENT",
            body,
            footer="Enter / Space / Esc: continue",
            border_color=border,
            title_color=border,
            max_w=820,
            max_h=430,
        )
        return

        from fantasy_ui import get_font, draw_overlay, draw_dark_panel, draw_header_bar

        draw_overlay(self.screen, 190)

        bw, bh = min(780, layout.GAME_W - 40), 360
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Gold border for positive, red for negative
        if self.karma > 0:
            border = FP.GOLD
        elif self.karma < 0:
            border = FP.BLOOD
        else:
            border = FP.FADED_TEXT

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="THE ALTAR OF THE LAST JUDGMENT",
                        font=get_font('heading', 20),
                        text_color=border)

        font = get_font('body', 18)
        y = by + 60

        # Karma score
        score_text = f"Karma: {self.karma}"
        score_surf = font.render(score_text, True, border)
        self.screen.blit(score_surf, (bx + (bw - score_surf.get_width()) // 2, y))
        y += 30

        # Narrative text (word-wrapped)
        max_w = bw - 60
        for paragraph in self._judgment_text.split('\n'):
            words = paragraph.split()
            lines, line = [], []
            for word in words:
                test = ' '.join(line + [word])
                if font.size(test)[0] > max_w:
                    if line:
                        lines.append(' '.join(line))
                    line = [word]
                else:
                    line.append(word)
            if line:
                lines.append(' '.join(line))
            for txt_line in lines:
                col = border if txt_line.isupper() else FP.PARCHMENT_LIGHT
                surf = font.render(txt_line, True, col)
                self.screen.blit(surf, (bx + 30, y))
                y += 24
            y += 6

        # Footer
        y = by + bh - 35
        font_sm = get_font('body', 14)
        footer = font_sm.render("Press ENTER to continue", True, FP.HINT_TEXT)
        self.screen.blit(footer, (bx + (bw - footer.get_width()) // 2, y))

    def render(self):
        cam_x, cam_y = self._camera()
        self.screen.fill((0, 0, 0))

        # Set up renderer view mode each frame
        if self.zoom_mode == 'close':
            self.renderer.set_view_origin(layout.MAP_X, 0)
            self.renderer.set_close_up(
                self.player.x, self.player.y,
                self.dungeon.width, self.dungeon.height,
                layout.MAP_W, layout.GAME_H, tile_size=64)
        elif self.zoom_mode == 'medium':
            self.renderer.set_view_origin(layout.MAP_X, 0)
            self.renderer.set_close_up(
                self.player.x, self.player.y,
                self.dungeon.width, self.dungeon.height,
                layout.MAP_W, layout.GAME_H, tile_size=TILE_SIZE)
        else:
            self.renderer.set_view_origin(layout.MAP_X, 0)
            self.renderer.set_dungeon(
                self.dungeon.width, self.dungeon.height,
                layout.MAP_W, layout.GAME_H)

        game_clip = pygame.Rect(layout.MAP_X, 0, layout.MAP_W, layout.GAME_H)
        self.screen.set_clip(game_clip)
        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)
        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)
        for m in self.monsters:
            if m.alive:
                # Ambush monsters are invisible until aware
                if m.ai_pattern == 'ambush' and not getattr(m, '_aware', False):
                    continue
                self.renderer.draw_entity(
                    m.x, m.y, m.color, cam_x, cam_y, self.visible,
                    mid=m.kind, footprint=getattr(m, 'footprint', (1, 1)))
        # Pet companions: draw with species sprite or color fallback
        for pet in self.pets:
            if pet.alive and (pet.x, pet.y) in self.visible:
                if getattr(pet, 'is_sketch', False):
                    # Sketched pets use the monster's sprite with a lavender tint
                    self.renderer.draw_entity(
                        pet.x, pet.y, pet.color, cam_x, cam_y, self.visible,
                        mid=pet.monster_kind, tint=(160, 140, 230, 160))
                else:
                    self.renderer.draw_entity(pet.x, pet.y, pet.color, cam_x, cam_y, self.visible, mid=pet.name.lower())
        # Telepathy: render unseen monsters as dim dots
        if self.player.has_effect('telepathy'):
            for m in self.monsters:
                if m.alive and not any_tile_in_set(m, self.visible):
                    self.renderer.draw_entity(
                        m.x, m.y, (70, 70, 120), cam_x, cam_y, None,
                        footprint=getattr(m, 'footprint', (1, 1)))
        # Abyssal Shimmer: pulsing violet glow (brighter when activated)
        for item in self.ground_items:
            if item.id == 'abyssal_shimmer' and (item.x, item.y) in self.visible:
                t = self.turn_count % 16
                pulse = abs(t - 8) / 8.0
                if getattr(item, 'activated', False):
                    r = int(160 + 95 * pulse)
                    g = int(20  + 20 * pulse)
                    b = 255
                else:
                    r = int(60 + 60 * pulse)
                    g = int(0  + 20 * pulse)
                    b = int(180 + 75 * pulse)
                self.renderer.draw_entity(item.x, item.y, (r, g, b), cam_x, cam_y, self.visible,
                                         mid='abyssal_shimmer', tint=(r, g, b, 200))

        # Death: always visible when in FOV; drawn with a pale spectral pulse
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            if (dm.x, dm.y) in self.visible:
                pulse = abs((self.turn_count % 20) - 10) / 10.0
                r = int(200 + 55 * pulse)
                g = int(200 + 55 * pulse)
                b = 255
                self.renderer.draw_entity(dm.x, dm.y, (r, g, b), cam_x, cam_y, self.visible, mid='death')
        _pspr = (self.secret_build or {}).get('_sprite', 'player')
        self.renderer.draw_player(self.player, cam_x, cam_y, sprite_name=_pspr)
        self.screen.set_clip(None)

        # Death-chase atmosphere — soft red vignette + pulsing edge glow
        # whenever Death is on the player's tail (audit: beauty-death-chase-
        # invisible). Subtle by design — should feel like dread, not like
        # the screen is broken.
        if self.death_pursues and self.death_monster is not None:
            self._draw_death_chase_atmosphere()

        self.msg_log.draw(self.screen, layout.MAP_X, layout.GAME_H, layout.MAP_W, layout.MSG_H)
        hud_monsters = [
            m for m in self.monsters
            if not (getattr(m, 'ai_pattern', '') == 'ambush' and not getattr(m, '_aware', False))
        ]
        self.sidebar.draw(
            self.player, self.dungeon_level, self.turn_count, self.player_gold,
            player_name=getattr(self, 'player_name', 'Adventurer'),
            visible_monsters=hud_monsters,
            visible_items=self.ground_items,
            visible_tiles=self.visible,
            secret_build=getattr(self, 'secret_build', None),
            heavenly_host_active=getattr(self, 'heavenly_host_active', False),
        )

        if self.state == STATE_TARGET:
            self._draw_targeting(cam_x, cam_y)
        elif self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_EQUIP_MENU:
            self._draw_equip_menu()
        elif self.state == STATE_KIT:
            self._draw_kit_panel()
        elif self.state == STATE_DISCOVERIES:
            self._draw_discoveries_panel()
        elif self.state == STATE_WAND_MENU:
            self._draw_wand_menu()
        elif self.state == STATE_SCROLL_MENU:
            self._draw_scroll_menu()
        elif self.state == STATE_SPELL_MENU:
            self._draw_spell_menu()
        elif self.state == STATE_PRAY:
            self._draw_prayer_menu()
        elif self.state == STATE_IDENTIFY_MENU:
            self._draw_identify_menu()
        elif self.state == STATE_PET_NAME_INPUT:
            self._draw_pet_name_popup()
        elif self.state == STATE_PET_MENU:
            self._draw_pet_menu()
        elif self.state == STATE_PET_FEED:
            self._draw_pet_menu()
            self._draw_pet_feed_submenu()
        elif self.state == STATE_PET_HEAL:
            self._draw_pet_menu()
            self._draw_pet_heal_submenu()
        elif self.state == STATE_PET_SPECIALS:
            self._draw_pet_menu()
            self._draw_pet_specials_submenu()
        elif self.state == STATE_QA_WARP_INPUT:
            self._draw_qa_warp_popup()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
        elif self.state == STATE_ASCENSION:
            self._draw_ascension_menu()
        elif self.state == STATE_EAT_MENU:
            self._draw_eat_menu()
        elif self.state == STATE_QUAFF_MENU:
            self._draw_quaff_menu()
        elif self.state == STATE_THROW_MENU:
            self._draw_throw_menu()
        elif self.state == STATE_POWER_MENU:
            self._draw_power_menu()
        elif self.state == STATE_CONFIRM_EXIT:
            self._draw_confirm_exit()
        elif self.state == STATE_EXIT_QUEST:
            self._draw_exit_quest()
        elif self.state == STATE_ABANDON_QUEST:
            self._draw_abandon_quest()
        elif self.state == STATE_CHICKEN:
            self._draw_chicken()
        elif self.state == STATE_VICTORY:
            self._draw_victory_screen()
        elif self.state == STATE_DEAD:
            self._draw_death_screen()
        elif self.state == STATE_REVIEW_MISSED:
            self._draw_review_missed()
        elif self.state == STATE_STUDY:
            self._draw_study_journal()
        elif self.state == STATE_HELP:
            self._draw_help_screen()
        elif self.state == STATE_LORE:
            self._draw_lore_screen()
        elif self.state == STATE_HINT:
            self._draw_hint_screen()
        elif self.state == STATE_HACK_REALITY:
            self._draw_hack_reality_screen()
        elif self.state == STATE_XYZZY_INPUT:
            self._draw_xyzzy_input()
        elif self.state == STATE_XYZZY_CONFIRM:
            self._draw_xyzzy_confirm()
        elif self.state == STATE_QUIRKS:
            self._draw_quirks_screen()
        elif self.state == STATE_CHARACTER_SHEET:
            self._draw_character_sheet()
        elif self.state == STATE_EXAMINE:
            self._draw_examine_menu()
        elif self.state == STATE_ENCYCLOPEDIA:
            self._draw_encyclopedia()
        elif self.state == STATE_DROP_MENU:
            self._draw_drop_menu()
        elif self.state == STATE_DROP_GOLD_INPUT:
            self._draw_drop_gold_input()
        elif self.state == STATE_DROP_QTY_INPUT:
            self._draw_drop_qty_input()
        elif self.state == STATE_STORY_POPUP:
            self._draw_story_popup()
        elif self.state == STATE_MYSTERY_APPROACH:
            self._draw_mystery_approach()
        elif self.state == STATE_SHOP:
            self._draw_shop()
        elif self.state == STATE_NPC_ENCOUNTER:
            self._draw_npc_encounter()
        elif self.state == STATE_COW_ENCOUNTER:
            self._draw_cow_encounter()
        elif self.state == STATE_JUDGMENT:
            self._draw_judgment()

        if self._debug_overlay:
            self._draw_debug_overlay()

        pygame.display.flip()

    def _camera(self) -> tuple[int, int]:
        return 0, 0

    def _draw_targeting(self, cam_x: int, cam_y: int):
        """Draw targeting overlay for ranged, melee, or throw targeting."""
        if self._melee_targeting:
            self._draw_melee_targeting(cam_x, cam_y)
        elif self._throw_targeting:
            self._draw_throw_targeting(cam_x, cam_y)
        else:
            self._draw_ranged_targeting(cam_x, cam_y)

    def _draw_melee_targeting(self, cam_x: int, cam_y: int):
        """Draw reach radius and cursor for melee targeting."""
        T   = self.renderer.map_tile_size
        w2s = self.renderer.world_to_screen
        px, py = self.player.x, self.player.y
        cx, cy = self.target_cursor_x, self.target_cursor_y
        reach = getattr(self, '_melee_reach', 1)

        # Highlight all tiles within reach
        reach_surf = pygame.Surface((T, T), pygame.SRCALPHA)
        reach_surf.fill((100, 180, 255, 35))
        for ry in range(py - reach, py + reach + 1):
            for rx in range(px - reach, px + reach + 1):
                if rx == px and ry == py:
                    continue
                if not self.dungeon.in_bounds(rx, ry):
                    continue
                scr_x, scr_y = w2s(rx, ry)
                if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                    self.screen.blit(reach_surf, (scr_x, scr_y))

        # Highlight monsters in range
        for m in self._target_candidates:
            scr_x, scr_y = w2s(m.x, m.y)
            if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((255, 100, 60, 70))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (255, 100, 60), (scr_x, scr_y, T, T), 1)

        # Check if there's a valid target at cursor
        target_monster = monster_at_tile(self.monsters, cx, cy)
        has_target = target_monster is not None

        # Cursor highlight
        scr_cx, scr_cy = w2s(cx, cy)
        if layout.MAP_X <= scr_cx < layout.MAP_X + layout.MAP_W and 0 <= scr_cy < layout.GAME_H:
            cur_color = (80, 255, 80) if has_target else (255, 220, 60)
            pygame.draw.rect(self.screen, cur_color, (scr_cx, scr_cy, T, T), 2)

    def _draw_throw_targeting(self, cam_x: int, cam_y: int):
        """Draw trajectory arc and cursor for throw targeting."""
        from combat import _line_of_sight
        T   = self.renderer.map_tile_size
        w2s = self.renderer.world_to_screen
        px, py = self.player.x, self.player.y
        cx, cy = self.target_cursor_x, self.target_cursor_y

        reach = self._throw_reach
        has_los = _line_of_sight(px, py, cx, cy, self.dungeon)
        in_range = max(abs(cx - px), abs(cy - py)) <= reach
        target_monster = monster_at_tile(self.monsters, cx, cy)
        # Check if a monster blocks the path before the cursor
        blocker = self._find_first_monster_in_path(px, py, cx, cy)
        will_hit_blocker = blocker is not None and (blocker.x != cx or blocker.y != cy)
        valid = has_los and in_range

        # Draw trajectory dots
        traj_surf = pygame.Surface((T, T), pygame.SRCALPHA)
        dot_color = (180, 80, 255, 180) if valid else (200, 80, 80, 160)
        pygame.draw.circle(traj_surf, dot_color, (T // 2, T // 2), max(2, T // 8))

        x0, y0, x1, y1 = px, py, cx, cy
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy
        tx, ty = x0, y0
        while True:
            if (tx, ty) != (x0, y0) and (tx, ty) != (x1, y1):
                scr_x, scr_y = w2s(tx, ty)
                if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                    self.screen.blit(traj_surf, (scr_x, scr_y))
            if tx == x1 and ty == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                tx += sx
            if e2 < dx:
                err += dx
                ty += sy

        # Highlight candidates
        for m in self._target_candidates:
            scr_x, scr_y = w2s(m.x, m.y)
            if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((180, 80, 255, 60))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (180, 80, 255), (scr_x, scr_y, T, T), 1)

        # Cursor
        scr_cx, scr_cy = w2s(cx, cy)
        if layout.MAP_X <= scr_cx < layout.MAP_X + layout.MAP_W and 0 <= scr_cy < layout.GAME_H:
            cur_color = (180, 80, 255) if valid and target_monster else (255, 80, 80)
            pygame.draw.rect(self.screen, cur_color, (scr_cx, scr_cy, T, T), 2)

        # HUD label
        item_name = self._throw_potion.name if self._throw_potion else "item"
        if will_hit_blocker:
            label = f"{blocker.name} blocks the path! {item_name} will hit it instead."
            label_color = (255, 200, 60)
        elif valid and target_monster:
            label = f"THROW {item_name} at {target_monster.name}  [ENTER=throw  TAB=next  ESC=cancel]"
            label_color = (180, 80, 255)
        elif valid and not target_monster:
            label = f"THROW {item_name} at empty tile  [ENTER=throw  ESC=cancel]"
            label_color = (200, 200, 200)
        elif not in_range:
            label = f"Out of throw range ({reach} tiles)  [ESC=cancel]"
            label_color = (255, 160, 40)
        else:
            label = "No line of sight  [ESC=cancel]"
            label_color = (255, 80, 80)

        label_surf = self.font_sm.render(label, True, label_color)
        label_bg = pygame.Surface((label_surf.get_width() + 16, label_surf.get_height() + 8),
                                  pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 180))
        self.screen.blit(label_bg, (layout.MAP_X + 8, layout.GAME_H - label_surf.get_height() - 16))
        self.screen.blit(label_surf, (layout.MAP_X + 16, layout.GAME_H - label_surf.get_height() - 12))

    def _draw_ranged_targeting(self, cam_x: int, cam_y: int):
        """Draw trajectory line and cursor highlight for ranged targeting."""
        from combat import _line_of_sight
        T   = self.renderer.map_tile_size
        w2s = self.renderer.world_to_screen
        px, py = self.player.x, self.player.y
        cx, cy = self.target_cursor_x, self.target_cursor_y

        # Check LoS and whether there's a target at cursor
        has_los = _line_of_sight(px, py, cx, cy, self.dungeon)
        target_monster = monster_at_tile(self.monsters, cx, cy)
        weapon = self.player.ranged_weapon
        in_reach = weapon and (max(abs(cx - px), abs(cy - py)) <= weapon.reach)
        valid_shot = has_los and in_reach and target_monster is not None

        # Draw trajectory dots from player to cursor (skip player tile)
        traj_surf = pygame.Surface((T, T), pygame.SRCALPHA)
        dot_color = (255, 220, 60, 180) if valid_shot else (200, 80, 80, 160)
        pygame.draw.circle(traj_surf, dot_color, (T // 2, T // 2), max(2, T // 8))

        # Bresenham walk to draw trajectory
        x0, y0, x1, y1 = px, py, cx, cy
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy
        tx, ty = x0, y0
        while True:
            if (tx, ty) != (x0, y0) and (tx, ty) != (x1, y1):
                scr_x, scr_y = w2s(tx, ty)
                if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                    self.screen.blit(traj_surf, (scr_x, scr_y))
            if tx == x1 and ty == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                tx += sx
            if e2 < dx:
                err += dx
                ty += sy

        # Highlight all valid target monsters in range
        for m in self._target_candidates:
            scr_x, scr_y = w2s(m.x, m.y)
            if layout.MAP_X <= scr_x < layout.MAP_X + layout.MAP_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((255, 200, 0, 60))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (255, 200, 0), (scr_x, scr_y, T, T), 1)

        # Cursor highlight on target tile
        scr_cx, scr_cy = w2s(cx, cy)
        if layout.MAP_X <= scr_cx < layout.MAP_X + layout.MAP_W and 0 <= scr_cy < layout.GAME_H:
            cur_color = (80, 255, 80) if valid_shot else (255, 80, 80)
            pygame.draw.rect(self.screen, cur_color, (scr_cx, scr_cy, T, T), 2)

        # HUD label at bottom of game area
        if valid_shot:
            label = f"FIRE at {target_monster.name}  [ENTER=shoot  TAB=next  ESC=cancel]"
            label_color = (80, 255, 80)
        elif target_monster and not has_los:
            label = f"No line of sight to {target_monster.name}  [ESC=cancel]"
            label_color = (255, 80, 80)
        elif not in_reach:
            label = "Out of range  [arrow keys to move cursor  ESC=cancel]"
            label_color = (255, 160, 40)
        else:
            label = "No target  [arrow keys to move  TAB=cycle targets  ESC=cancel]"
            label_color = (200, 200, 200)

        label_surf = self.font_sm.render(label, True, label_color)
        label_bg = pygame.Surface((label_surf.get_width() + 16, label_surf.get_height() + 8),
                                  pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 180))
        self.screen.blit(label_bg, (layout.MAP_X + 8, layout.GAME_H - label_surf.get_height() - 16))
        self.screen.blit(label_surf, (layout.MAP_X + 16, layout.GAME_H - label_surf.get_height() - 12))

    # Subject palette is sourced from FP.SUBJECT so the welcome screen,
    # quiz panel border, and standalone study mode all show the same color
    # for a given subject. Don't redefine this dict — edit fantasy_ui.py.
    _SUBJECT_COLOR = FP.SUBJECT

    _fit_text = staticmethod(_gh_fit_text)

    _wrap_text = staticmethod(_gh_wrap_text)

    def _draw_quiz(self):
        qe = self.quiz_engine
        if not qe.current_question:
            return

        # Celebration takes over the full screen -- draw nothing else
        if qe.celebrating:
            self._draw_celebration()
            return

        is_combat = (self.combat_target is not None and qe.mode == QuizMode.CHAIN)
        accent    = self._SUBJECT_COLOR.get(qe.subject, (160, 130, 255))
        accent_dim = tuple(max(0, v - 90) for v in accent)

        # -- Overlay ----------------------------------------------------
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        # -- Modal geometry ---------------------------------------------
        bw = min(1060, layout.GAME_W - 40)
        PAD = 24

        # Question text (wrapped) -- calculate height first. Cap line count
        # so a pathologically long question can't push the panel past the
        # viewport. The cap leaves room for header + timer + 4 choice cards
        # + status + (combat HUD if active) and clamps to roughly half the
        # viewport height.
        q_font    = self.font_md
        q_text    = qe.current_question.get('question', '')
        q_lines   = self._wrap_text(q_text, q_font, bw - PAD * 2)
        q_line_h  = q_font.get_height() + 4
        # Available vertical room for the question block alone
        _reserved = 240 + (110 if is_combat else 0)  # chrome + cards + status
        _q_cap = max(2, (layout.WINDOW_H - _reserved) // q_line_h)
        if len(q_lines) > _q_cap:
            # Truncate with an ellipsis marker on the last visible line
            q_lines = q_lines[:_q_cap - 1] + [q_lines[_q_cap - 1] + ' …']
        q_height  = len(q_lines) * q_line_h

        # Choice button layout
        choices = qe.current_question.get('choices', [])
        if qe.confused_order and len(qe.confused_order) == len(choices):
            display_choices = [choices[i] for i in qe.confused_order]
        else:
            display_choices = choices

        c_font   = self.font_sm
        c_line_h = c_font.get_height() + 3
        KEY_W    = 68         # width of [1] key hint area -- must be wider than the rendered badge
        GAP      = 14         # gap between the two choice columns
        cw       = (bw - PAD * 2 - GAP) // 2   # each choice card width
        c_text_w = cw - KEY_W - 8               # wrappable text area per card
        # pre-wrap all choice texts
        c_wrapped = [self._wrap_text(str(ch), c_font, c_text_w) for ch in display_choices]
        max_c_lines = max((len(w) for w in c_wrapped), default=1)
        ch_height = max(52, max_c_lines * c_line_h + 20)  # card height

        # Fixed section heights
        HEADER_H = 42
        TIMER_H  = 28
        STATUS_H = 36
        COMBAT_H = 110 if is_combat else 0
        SECTION_GAP = 10

        bh = (HEADER_H + TIMER_H + SECTION_GAP
              + q_height + SECTION_GAP * 2
              + ch_height * 2 + GAP          # two rows of choices
              + STATUS_H + SECTION_GAP
              + COMBAT_H + PAD)

        bx = (layout.GAME_W - bw) // 2
        by = max(20, (layout.WINDOW_H - bh) // 2)

        # FANTASY: Arcane grimoire quiz panel
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=accent)

        # Mode / progress counter (top-right). Built BEFORE the header so the
        # title can reserve room for it and never overrun it (e.g. a long
        # lockpick/cook title sliding under "Chain xN").
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            c_text, c_color = f"Chain x{qe.chain}", FP.SUCCESS_TEXT
        else:
            c_text  = f"{qe.correct_count} / {qe.required}"
            c_color = FP.CYAN_ACCENT
        c_surf = self.font_md.render(c_text, True, c_color)

        draw_header_bar(self.screen, (bx, by, bw, HEADER_H),
                        text=self.quiz_title, font=self.font_md,
                        text_color=FP.GOLD_BRIGHT, accent=accent,
                        right_reserve=c_surf.get_width() + PAD + 16)
        self.screen.blit(c_surf, (bx + bw - c_surf.get_width() - PAD,
                                   by + (HEADER_H - c_surf.get_height()) // 2))

        # -- Timer bar -------------------------------------------------
        ty        = by + HEADER_H + 6
        bar_x     = bx + PAD
        bar_w     = bw - PAD * 2
        bar_h     = 14

        # Tier pip indicator -- 5 small circles (filled = earned, hollow = not yet)
        pip_r   = 5
        pip_gap = 13
        pip_cx0 = bar_x + pip_r
        pip_cy  = ty + bar_h // 2
        for i in range(5):
            px = pip_cx0 + i * pip_gap
            if i < qe.tier:
                pygame.draw.circle(self.screen, accent, (px, pip_cy), pip_r)
            else:
                pygame.draw.circle(self.screen, accent_dim, (px, pip_cy), pip_r, 1)
        tier_offset = 5 * pip_gap + 8
        bar_x += tier_offset
        bar_w -= tier_offset

        # Timer bar — only rendered for timed quizzes (combat math attack).
        # Untimed quizzes (identify / lockpick / equip / prayer / cooking /
        # magic / etc.) drop the bar entirely so the kid feels invited to
        # read the substantive content the banks now carry. Tier pips above
        # still show progress in escalator-chain modes.
        if getattr(qe, 'timed', True):
            ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))
            t_color = (
                FP.SUCCESS_TEXT if ratio > 0.55 else
                FP.WARNING_TEXT if ratio > 0.28 else
                FP.DANGER_TEXT
            )
            pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, (bar_x, ty, bar_w, bar_h), border_radius=4)
            if ratio > 0:
                pygame.draw.rect(self.screen, t_color,
                                 (bar_x, ty, max(4, int(bar_w * ratio)), bar_h), border_radius=4)
            # Tick marks every 20%
            for tick in range(1, 5):
                tx = bar_x + int(bar_w * tick / 5)
                pygame.draw.line(self.screen, FP.SHADOW, (tx, ty), (tx, ty + bar_h), 1)

            # Timer seconds label -- right-aligned inside the bar
            secs = int(qe.time_remaining)
            t_label = self.font_sm.render(f"{secs}s", True, FP.WHITE)
            lx = bar_x + bar_w - t_label.get_width() - 4
            ly = ty + (bar_h - t_label.get_height()) // 2
            self.screen.blit(t_label, (lx, ly))

        # -- Question text ---------------------------------------------
        qy = ty + TIMER_H
        for line in q_lines:
            surf = q_font.render(line, True, FP.VELLUM)
            self.screen.blit(surf, (bx + PAD, qy))
            qy += q_line_h
        qy += SECTION_GAP

        # Thin separator
        pygame.draw.line(self.screen, accent_dim, (bx + PAD, qy - 4), (bx + bw - PAD, qy - 4))

        # -- Choice cards (2 x 2 grid) — grimoire chrome via draw_choice_button --
        from fantasy_ui import draw_choice_button
        # Case-EXACT comparison (bug bash 2026-06-01) — mirrors the engine
        # fix in quiz_engine.answer(). With .lower(), grammar capitalization
        # questions rendered ALL four choices green because the choices
        # collapsed to the same string after case-folding.
        correct_str = str(qe.current_question.get('answer', '')).strip()
        selected    = qe.last_answer.strip()
        in_result   = (qe.state == QuizState.RESULT)

        for i, (choice, wrapped_lines) in enumerate(zip(display_choices, c_wrapped)):
            col = i % 2
            row = i // 2
            cx_ = bx + PAD + col * (cw + GAP)
            cy_ = qy + row * (ch_height + GAP)

            c_str       = str(choice).strip()
            is_correct  = c_str == correct_str
            is_selected = bool(selected) and c_str == selected

            # In result phase: mark the right answer green, mark the player's
            # wrong pick red. Mid-question: highlight only if pressed (rare —
            # answers are usually atomic key-presses).
            mark_correct   = in_result and is_correct
            mark_incorrect = in_result and is_selected and not is_correct

            draw_choice_button(
                self.screen, (cx_, cy_, cw, ch_height),
                key_label=str(i + 1),
                text=wrapped_lines,
                key_font=self.font_md,
                text_font=c_font,
                selected=is_selected and not in_result,
                correct=mark_correct or None,
                incorrect=mark_incorrect or None,
            )

        # -- Status / feedback bar -------------------------------------
        status_y = qy + 2 * (ch_height + GAP) + SECTION_GAP

        if in_result:
            fb_text  = "*  CORRECT!" if qe.last_correct else "*  WRONG!"
            fb_color = FP.SUCCESS_TEXT if qe.last_correct else FP.DANGER_TEXT
            fb_surf  = self.font_lg.render(fb_text, True, fb_color)
            self.screen.blit(fb_surf, (bx + (bw - fb_surf.get_width()) // 2, status_y))
        elif qe.state == QuizState.ASKING:
            hint = self.font_sm.render("Press  1  2  3  4  to answer", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, status_y + 10))

        # -- Combat HUD ------------------------------------------------
        if is_combat:
            self._draw_combat_hud(bx, status_y + STATUS_H + SECTION_GAP, bw, accent)

    def _draw_death_chase_atmosphere(self):
        """Faint red vignette + edge glow when Death is in pursuit.

        Intensity scales with proximity: barely visible at 8+ tiles,
        unmistakable when Death is on top of you. Stays away from the
        message log and sidebar so combat readouts stay legible.
        """
        dm = self.death_monster
        if dm is None:
            return
        dist = abs(dm.x - self.player.x) + abs(dm.y - self.player.y)
        # Falloff: 1.0 at distance 0, ~0.1 at distance 10, ~0 beyond
        proximity = max(0.0, 1.0 - dist / 12.0)
        if proximity <= 0.05:
            return

        # Heartbeat pulse — a quarter beat per turn so it ticks visibly
        # without being epileptic
        pulse = 0.65 + 0.35 * math.sin(pygame.time.get_ticks() * 0.0045)
        alpha = int(80 * proximity * pulse)
        if alpha < 4:
            return

        # Vignette only over the game viewport (skip sidebar + msg log)
        gw = layout.MAP_W
        gh = layout.GAME_H
        vig = pygame.Surface((gw, gh), pygame.SRCALPHA)
        # Edge glow — strong on the rim, none in the middle
        steps = 24
        for step in range(steps):
            ratio = step / steps
            inset = int(ratio * min(gw, gh) * 0.35)
            edge_alpha = int(alpha * (1 - ratio) ** 1.6)
            pygame.draw.rect(vig, (*FP.BLOOD, edge_alpha),
                             (inset, inset, gw - 2 * inset, gh - 2 * inset), 2)
        self.screen.blit(vig, (layout.MAP_X, 0))

    def _draw_celebration(self):
        """MAX CHAIN celebration — full-screen grimoire moment.

        Joins the rune-circle + candle-glow family used by victory/death so
        win moments share visual DNA. Pulsing intensity drives the rune
        rotation speed and candle brightness.
        """
        from fantasy_ui import draw_rune_circle, draw_candle_glow, draw_glow_text, draw_filigree_bar
        qe    = self.quiz_engine
        t     = qe.celebration_timer
        pulse = abs(math.sin(t * 6))

        # Warm overlay wash
        draw_overlay(self.screen, alpha=int(180 + 30 * pulse), color=(40, 24, 0))

        cx = layout.WINDOW_W // 2
        cy = layout.WINDOW_H // 2

        # Counter-rotating gold rune circles + candle glow at center
        draw_rune_circle(self.screen, cx, cy, 280,
                         (*FP.GOLD, int(100 + 60 * pulse)),
                         t * 1.5, 16)
        draw_rune_circle(self.screen, cx, cy, 190,
                         (*FP.GOLD_BRIGHT, int(80 + 60 * pulse)),
                         -t * 2.0, 10)
        draw_candle_glow(self.screen, cx, cy, intensity=0.8 + 0.4 * pulse)

        # Filigree bars frame the headline
        draw_filigree_bar(self.screen, cx - 320, cy - 88, 640, FP.GOLD)

        # Headline
        cel_font = self.font_xl
        cel_text = qe.celebration_text
        size = cel_font.size(cel_text)
        hx = cx - size[0] // 2
        hy = cy - size[1] // 2
        draw_glow_text(self.screen, cel_font, cel_text,
                       FP.GOLD_BRIGHT, (hx, hy),
                       glow_color=(255, 230, 140), glow_r=4)

        draw_filigree_bar(self.screen, cx - 320, cy + size[1] + 12, 640, FP.GOLD_DARK)

        # Sub-line
        sub = self.font_lg.render("Perfect Combo!", True, FP.GOLD_PALE)
        self.screen.blit(sub, (cx - sub.get_width() // 2,
                               cy + size[1] + 24))

    def _draw_combat_hud(self, bx: int, strip_y: int, bw: int, accent=(80, 80, 180)):
        """Draw monster HP bar + chain damage preview inside the quiz modal."""
        from combat import _damage_multiplier
        monster = self.combat_target
        # Use ranged weapon for damage preview if this is a ranged attack
        is_ranged_attack = getattr(self, 'quiz_title', '').startswith('FIRE ')
        weapon = self.player.ranged_weapon if is_ranged_attack else self.player.weapon

        # Separator
        pygame.draw.line(self.screen, accent,
                         (bx + 18, strip_y), (bx + bw - 18, strip_y))

        sy = strip_y + 10

        # -- Left: monster name + HP bar -------------------------------
        from text_layout import truncate_label
        lx       = bx + 22
        rx       = bx + 320  # right-column anchor (must match below)
        hp_ratio = max(0.0, monster.hp / max(1, monster.max_hp))
        hp_color = (
            FP.SUCCESS_TEXT if hp_ratio > 0.50 else
            FP.WARNING_TEXT if hp_ratio > 0.25 else
            FP.DANGER_TEXT
        )
        # Truncate the monster name so it can't bleed into the right column
        # (long uniques like "the Greater Spectral Knight of Caer Llion"
        # previously clobbered the WEAKNESS!/RESISTED label). See A1-2.
        max_name_w = max(40, rx - lx - 16)
        full_name_text = f"{monster.name.upper()}   {monster.hp}/{monster.max_hp} HP"
        name_text_fit = truncate_label(full_name_text, max_name_w, self.font_sm)
        name_surf = self.font_sm.render(name_text_fit, True, FP.GOLD_PALE)
        self.screen.blit(name_surf, (lx, sy))

        hb_y, hb_w = sy + 18, 260
        pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, (lx, hb_y, hb_w, 12), border_radius=4)
        if hp_ratio > 0:
            pygame.draw.rect(self.screen, hp_color,
                             (lx, hb_y, max(3, int(hb_w * hp_ratio)), 12), border_radius=4)
        pygame.draw.rect(self.screen, FP.BURGUNDY, (lx, hb_y, hb_w, 12), 1, border_radius=4)

        effects = [e for e, v in monster.status_effects.items() if v > 0]
        if effects:
            # Also clip the effects row so long status names can't bleed.
            eff_text = "  ".join(f"[{e}]" for e in effects[:5])
            eff_text_fit = truncate_label(eff_text, max_name_w, self.font_sm)
            eff = self.font_sm.render(eff_text_fit, True, FP.WARNING_TEXT)
            self.screen.blit(eff, (lx, hb_y + 16))

        # -- Right: damage preview + weapon ---------------------------
        base    = weapon.base_damage  if weapon else 4
        enchant = weapon.enchant_bonus if weapon else 0
        mults   = weapon.chain_multipliers if weapon else [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        dtypes  = weapon.damage_types if weapon else ['physical']
        dm      = _damage_multiplier(dtypes, monster)

        if dm >= 1.5:
            dm_text, dm_col = "WEAKNESS!", FP.SUCCESS_TEXT
        elif dm <= 0.5:
            dm_text, dm_col = "RESISTED",  FP.DANGER_TEXT
        else:
            dm_text, dm_col = "/".join(dtypes).upper(), FP.FADED_TEXT
        self.screen.blit(self.font_sm.render(dm_text, True, dm_col), (rx, sy))

        # Chain table: colour each step by heat (low->high damage)
        parts = []
        for i, mult in enumerate(mults[:6]):
            dmg = max(1, int((base + enchant) * mult * dm))
            parts.append((f"x{i+1}:{dmg}", dmg))
        max_dmg = max(d for _, d in parts) or 1
        row1_x  = rx
        for label, dmg in parts[:3]:
            heat  = dmg / max_dmg
            # Heat gradient lifted so all values stay > 4.5:1 contrast on midnight.
            col   = (int(80 + 175 * heat), int(220 - 130 * heat), int(120 - 80 * heat))
            surf  = self.font_sm.render(label, True, col)
            self.screen.blit(surf, (row1_x, sy + 18))
            row1_x += surf.get_width() + 14
        row2_x = rx
        for label, dmg in parts[3:]:
            heat  = dmg / max_dmg
            # Heat gradient lifted so all values stay > 4.5:1 contrast on midnight.
            col   = (int(80 + 175 * heat), int(220 - 130 * heat), int(120 - 80 * heat))
            surf  = self.font_sm.render(label, True, col)
            self.screen.blit(surf, (row2_x, sy + 34))
            row2_x += surf.get_width() + 14

        w_name = weapon.name if weapon else "bare hands"
        self.screen.blit(
            self.font_sm.render(f"{w_name}", True, FP.FADED_TEXT), (rx, sy + 52)
        )

    # ------------------------------------------------------------------
    # Action menu visual system
    # ------------------------------------------------------------------

    def _menu_letter(self, idx: int) -> str:
        letters = getattr(self, '_LETTERS', 'abcdefghijklmnopqrstuvwxyz')
        return letters[idx] if 0 <= idx < len(letters) else ''

    def _menu_clamp_selection(self, attr: str, total: int) -> int:
        sel = int(getattr(self, attr, 0) or 0)
        if total <= 0:
            sel = 0
        else:
            sel = max(0, min(sel, total - 1))
        setattr(self, attr, sel)
        return sel

    def _menu_draw_line(self, text: str, font, color, rect: pygame.Rect) -> int:
        """Draw one line inside rect without ellipsizing. Overlong single words
        are clipped to the rect; the detail pane carries the full text."""
        old_clip = self.screen.get_clip()
        self.screen.set_clip(rect)
        self.screen.blit(font.render(str(text), True, color), (rect.x, rect.y))
        self.screen.set_clip(old_clip)
        return font.get_height() + 2

    def _menu_draw_wrapped(self, text: str, font, color, rect: pygame.Rect,
                           max_lines: int | None = None) -> int:
        y = rect.y
        drawn = 0
        chunks = str(text).splitlines() or ['']
        for chunk in chunks:
            lines = self._wrap_text(chunk, font, rect.w) or ['']
            for line in lines:
                if max_lines is not None and drawn >= max_lines:
                    return y - rect.y
                if y + font.get_height() > rect.bottom:
                    return y - rect.y
                self._menu_draw_line(line, font, color,
                                     pygame.Rect(rect.x, y, rect.w, font.get_height() + 2))
                y += font.get_height() + 3
                drawn += 1
        return y - rect.y

    def _menu_draw_text_block(self, lines: list, rect: pygame.Rect,
                              default_color=None, default_font=None) -> int:
        color = default_color or FP.BODY_TEXT
        font = default_font or self.font_sm
        y = rect.y
        for entry in lines:
            if entry is None or entry == '':
                y += 8
                continue
            if isinstance(entry, tuple):
                text = entry[0]
                col = entry[1] if len(entry) > 1 and entry[1] is not None else color
                fnt = entry[2] if len(entry) > 2 and entry[2] is not None else font
            else:
                text, col, fnt = entry, color, font
            if y >= rect.bottom:
                break
            used = self._menu_draw_wrapped(
                str(text), fnt, col,
                pygame.Rect(rect.x, y, rect.w, rect.bottom - y))
            y += used + 4
        return y

    def _menu_draw_resource_bars(self, rect: pygame.Rect) -> int:
        y = rect.y
        bars = [
            ('HP', self.player.hp, self.player.max_hp, (255, 80, 95)),
            ('MP', self.player.mp, self.player.max_mp, (105, 150, 255)),
            ('SP', self.player.sp, self.player.max_sp, (85, 235, 145)),
        ]
        for label, val, max_val, color in bars:
            self.screen.blit(self.font_sm.render(label, True, FP.BODY_TEXT), (rect.x, y))
            tx = rect.x + 34
            tw = max(30, rect.w - 94)
            track = pygame.Rect(tx, y + 7, tw, 10)
            pygame.draw.rect(self.screen, FP.MIDNIGHT, track, border_radius=5)
            ratio = max(0.0, min(1.0, float(val) / max(1, float(max_val))))
            if ratio > 0:
                fill = pygame.Rect(track.x, track.y, max(1, int(track.w * ratio)), track.h)
                pygame.draw.rect(self.screen, color, fill, border_radius=5)
            nums = self.font_sm.render(f"{int(val)}/{int(max_val)}", True, FP.BODY_TEXT)
            self.screen.blit(nums, (track.right + 8, y - 1))
            y += 25
        return y

    def _menu_tile_label(self) -> str:
        try:
            from dungeon import (ALTAR, FOUNTAIN, GRAVE, THRONE, WATER, LAVA,
                                 ICE, STAIRS_UP, STAIRS_DOWN)
            tile = self.dungeon.tiles[self.player.y][self.player.x]
            names = {
                ALTAR: 'Altar',
                FOUNTAIN: 'Fountain',
                GRAVE: 'Grave',
                THRONE: 'Throne',
                WATER: 'Water',
                LAVA: 'Lava',
                ICE: 'Ice',
                STAIRS_UP: 'Stairs up',
                STAIRS_DOWN: 'Stairs down',
            }
            return names.get(tile, 'Dungeon floor')
        except Exception:
            return 'Dungeon floor'

    def _menu_base_context(self, extra: list | None = None) -> list:
        p = self.player
        weight = f"{p.get_current_weight():.1f}/{p.get_carry_limit():.0f}"
        effects = getattr(p, 'status_effects', {}) or {}
        active = [k.replace('_', ' ') for k, v in effects.items() if v != 0]
        lines = [
            ("CURRENT RUN", FP.GOLD_BRIGHT, self.font_sm),
            (f"Floor {self.dungeon_level}    Turn {self.turn_count}", FP.BODY_TEXT, self.font_sm),
            (f"Tile: {self._menu_tile_label()}", FP.FADED_TEXT, self.font_sm),
            (f"Weight: {weight}", FP.BODY_TEXT, self.font_sm),
            '',
            ("STATS", FP.GOLD_BRIGHT, self.font_sm),
            (f"STR {p.STR}  CON {p.CON}  DEX {p.DEX}", FP.BODY_TEXT, self.font_sm),
            (f"INT {p.INT}  WIS {p.WIS}  PER {p.PER}", FP.BODY_TEXT, self.font_sm),
        ]
        if active:
            lines += ['', ("ACTIVE EFFECTS", FP.GOLD_BRIGHT, self.font_sm)]
            lines.append((', '.join(active[:6]), FP.BODY_TEXT, self.font_sm))
            if len(active) > 6:
                lines.append((f"+{len(active) - 6} more", FP.FADED_TEXT, self.font_sm))
        if extra:
            lines += [''] + extra
        return lines

    def _menu_item_level(self, item) -> int:
        try:
            return self._kit_visible_level(item)
        except Exception:
            return int(getattr(item, 'id_level', 5) or 0)

    def _menu_item_is_equipped(self, item) -> bool:
        p = self.player
        return (
            item is getattr(p, 'weapon', None)
            or item is getattr(p, 'ranged_weapon', None)
            or item is getattr(p, 'shield', None)
            or item in (getattr(p, 'armor_slots', []) or [])
            or item in (getattr(p, 'accessory_slots', []) or [])
            or item is getattr(p, 'amulet_slot', None)
            or item is getattr(p, 'belt_slot', None)
        )

    def _menu_buc_label(self, item, id_level: int | None = None) -> str:
        id_level = self._menu_item_level(item) if id_level is None else id_level
        if not hasattr(item, 'buc'):
            return '-'
        if id_level >= 2 or getattr(item, 'buc_known', False) or self._menu_item_is_equipped(item):
            return getattr(item, 'buc', 'uncursed')
        return '?'

    def _menu_bonus_label(self, key, value) -> str:
        if key == 'ac_bonus':
            return f"AC {int(value):+d}"
        if key == 'regen_bonus':
            return f"Regen {int(value):+d}"
        if key.startswith('resistance_'):
            try:
                value_text = f"{int(value):+d}"
            except (TypeError, ValueError):
                value_text = str(value)
            return f"{key[len('resistance_'):].replace('_', ' ').title()} resist {value_text}"
        if key.startswith('stat_bonus_'):
            return f"{key[len('stat_bonus_'):]} {int(value):+d}"
        if key.startswith('status_'):
            return f"{key[len('status_'):].replace('_', ' ').title()} status"
        if key.startswith('passive_'):
            return key[len('passive_'):].replace('_', ' ').title()
        return f"{str(key).replace('_', ' ').title()}: {value}"

    def _menu_item_summary(self, item) -> str:
        if isinstance(item, self._GoldDropEntry):
            return "opens amount prompt"
        idl = self._menu_item_level(item)
        if hasattr(item, 'identified') and idl < 3:
            cls = getattr(item, 'item_class', 'item').replace('_', ' ')
            return f"{cls} | unidentified | ID {idl}/5"
        try:
            return self._get_item_stats_brief(item)
        except Exception:
            return getattr(item, 'item_class', 'item').replace('_', ' ')

    def _menu_item_detail_lines(self, item, action: str = 'Select') -> list:
        if isinstance(item, self._GoldDropEntry):
            return [
                ("Gold", FP.GOLD_BRIGHT, self.font_md),
                (f"You have {getattr(self, 'player_gold', 0)} coins.", FP.BODY_TEXT, self.font_sm),
                ("Next action", FP.GOLD_BRIGHT, self.font_sm),
                ("Choose this row to type how much gold to drop.", FP.BODY_TEXT, self.font_sm),
            ]

        idl = self._menu_item_level(item)
        display = self._display_name(item)
        cls = getattr(item, 'item_class', type(item).__name__).replace('_', ' ')
        lines = [(display, FP.GOLD_BRIGHT, self.font_md)]

        if hasattr(item, 'identified') and idl < 3:
            un = getattr(item, 'unidentified_name', display)
            lines += [
                ("Unidentified appearance", FP.GOLD_BRIGHT, self.font_sm),
                (un, FP.BODY_TEXT, self.font_sm),
                (f"Study progress: {idl}/5", FP.FADED_TEXT, self.font_sm),
                (f"Type: {cls}", FP.FADED_TEXT, self.font_sm),
                (f"Weight: {getattr(item, 'weight', 0):.1f}", FP.FADED_TEXT, self.font_sm),
                ("Hidden", FP.WARNING_TEXT, self.font_sm),
                ("Stats, BUC, lore, and special mechanics stay hidden until identified.", FP.BODY_TEXT, self.font_sm),
                ("Next action", FP.GOLD_BRIGHT, self.font_sm),
                (action, FP.BODY_TEXT, self.font_sm),
            ]
            return lines

        lines += [
            ("Known properties", FP.GOLD_BRIGHT, self.font_sm),
            (self._menu_item_summary(item), FP.BODY_TEXT, self.font_sm),
            (f"BUC: {self._menu_buc_label(item, idl)}    Weight: {getattr(item, 'weight', 0):.1f}",
             FP.FADED_TEXT, self.font_sm),
        ]

        if isinstance(item, Weapon):
            special = self._kit_weapon_special(item, idl)
            if special and special != '-':
                lines += [("Weapon mechanic", FP.GOLD_BRIGHT, self.font_sm),
                          (special, FP.BODY_TEXT, self.font_sm)]
        if isinstance(item, (Armor, Shield, Accessory)) and getattr(item, 'tier_bonuses', None):
            from chain_equip import get_chain_mode, get_chain_subject
            lines += [
                ("Attunement chain", FP.GOLD_BRIGHT, self.font_sm),
                (f"{get_chain_subject(item).title()} | {get_chain_mode(item).replace('_', ' ')} | fresh quiz on equip",
                 FP.BODY_TEXT, self.font_sm),
            ]
            bonuses = getattr(item, 'tier_bonuses', {}) or {}
            for tier in range(1, 6):
                row = bonuses.get(str(tier), bonuses.get(tier, {})) or {}
                if not row:
                    continue
                labels = [self._menu_bonus_label(k, v) for k, v in row.items()]
                lines.append((f"T{tier}: " + "; ".join(labels), FP.SUCCESS_TEXT, self.font_sm))

        if isinstance(item, Accessory):
            fx = getattr(item, 'effects', {}) or {}
            if fx:
                effect_bits = []
                if 'stat' in fx:
                    effect_bits.append(f"{fx['stat']} {int(fx.get('amount', 0)):+d}")
                if 'stat2' in fx:
                    effect_bits.append(f"{fx['stat2']} {int(fx.get('amount2', 0)):+d}")
                if 'status' in fx:
                    effect_bits.append(f"grants {fx['status']}")
                if effect_bits:
                    lines += [("Accessory effect", FP.GOLD_BRIGHT, self.font_sm),
                              (", ".join(effect_bits), FP.BODY_TEXT, self.font_sm)]
            if getattr(item, 'use_charged', False):
                lines.append((f"Charges: {getattr(item, 'charges', 0)}/{getattr(item, 'max_charges', 0)}",
                              FP.CYAN_ACCENT, self.font_sm))

        lore = getattr(item, 'lore', '')
        if lore and idl >= 4:
            lines += [("Lore", FP.GOLD_BRIGHT, self.font_sm), (lore, FP.BODY_TEXT, self.font_sm)]
        elif lore:
            lines += [("Lore", FP.GOLD_BRIGHT, self.font_sm),
                      ("Reach full identification to read the lore.", FP.FADED_TEXT, self.font_sm)]

        lines += [("Next action", FP.GOLD_BRIGHT, self.font_sm),
                  (action, FP.BODY_TEXT, self.font_sm)]
        return lines

    def _menu_recipe_preview(self, recipe) -> str:
        outcomes = recipe.get('tier_outcomes', {}) or {}
        parts = []
        for t in range(1, 6):
            o = outcomes.get(str(t), {}) or {}
            bits = []
            if o.get('sp'):
                bits.append(f"+{o['sp']}SP")
            if o.get('hp'):
                bits.append(f"+{o['hp']}HP")
            if o.get('max_hp_bonus'):
                bits.append(f"+{o['max_hp_bonus']}maxHP")
            if o.get('stat_grant'):
                stat = recipe.get('stat_grant') or recipe.get('stat_grant_default') or '?'
                bits.append(f"+{o['stat_grant']}{stat}")
            if o.get('temp_power'):
                label = str(recipe.get('temp_power') or '').replace('_', ' ').strip()
                dur = recipe.get('temp_duration')
                bits.append(f"{label} {dur}t" if label and dur else label or 'temp power')
            if o.get('permanent_power'):
                bits.append('permanent power')
            if bits:
                parts.append(f"T{t}: {'/'.join(bits)}")
        return " | ".join(parts)

    def _menu_recipe_detail_lines(self, recipe) -> list:
        from food_system import _raw_ingredients as _ri
        from collections import Counter
        ingredients = _ri()
        counts = Counter(recipe.get('ingredients', []))
        ing_text = ', '.join(
            f"{ingredients.get(iid, {}).get('name', iid)} x{n}" if n > 1
            else ingredients.get(iid, {}).get('name', iid)
            for iid, n in counts.items()
        )
        lines = [
            (recipe.get('name', 'Recipe').title(), FP.GOLD_BRIGHT, self.font_md),
            ("Ingredients", FP.GOLD_BRIGHT, self.font_sm),
            (ing_text or 'none', FP.BODY_TEXT, self.font_sm),
        ]
        desc = recipe.get('description', '')
        if desc:
            lines += [("Cookbook note", FP.GOLD_BRIGHT, self.font_sm),
                      (desc, FP.BODY_TEXT, self.font_sm)]
        preview = self._menu_recipe_preview(recipe)
        if preview:
            lines += [("Chain outcomes", FP.GOLD_BRIGHT, self.font_sm),
                      (preview, FP.SUCCESS_TEXT, self.font_sm)]
        lines += [("Next action", FP.GOLD_BRIGHT, self.font_sm),
                  ("Answer one cooking question. Right = full recipe; wrong = ruined dish.", FP.BODY_TEXT, self.font_sm)]
        return lines

    def _draw_action_tabs(self, tabs, active_tab: int, counts, x: int, y: int, w: int) -> int:
        if not tabs:
            return y
        tab_font = get_font('small', 14)
        tx = x
        max_x = x + w
        for i, tab in enumerate(tabs):
            count = counts[i] if counts and i < len(counts) else None
            label = tab[0]
            text = f"{label} ({count})" if count is not None else label
            tw = min(max_x - tx, tab_font.size(text)[0] + 22)
            if tw < 42:
                break
            rect = pygame.Rect(tx, y, tw, 25)
            active = i == active_tab
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                             rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD if active else FP.GOLD_DARK,
                             rect, 1, border_radius=4)
            col = FP.GOLD_BRIGHT if active else FP.FADED_TEXT
            self._menu_draw_line(text, tab_font, col,
                                 pygame.Rect(rect.x + 8, rect.y + 4, rect.w - 16, rect.h))
            tx += tw + 6
        return y + 32

    def _draw_decision_menu_variant_a(self, *, title: str, entries: list,
                                      selected: int, context_lines: list,
                                      hint: str, border_color=None, tabs=None,
                                      active_tab: int = 0, tab_counts=None,
                                      scroll_attr: str | None = None):
        """Large decision menu, Variant B.

        Kept under the original helper name so existing menu call sites stay
        stable. The layout is now a wide choices list plus an inspector pane;
        standing run context stays in the HUD instead of consuming menu width.
        """
        border = border_color or FP.GOLD
        draw_overlay(self.screen, 190)
        bw = min(1240, layout.GAME_W - 32)
        bh = min(720, layout.WINDOW_H - 32)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, 44), text=title,
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        content_x = bx + 16
        content_y = by + 56
        content_w = bw - 32
        content_y = self._draw_action_tabs(tabs, active_tab, tab_counts,
                                           content_x, content_y, content_w)
        footer_h = 32
        body_h = by + bh - footer_h - content_y - 10

        gap = 12
        list_w = max(500, min(700, int(content_w * 0.58)))
        detail_w = content_w - list_w - gap
        if detail_w < 390:
            detail_w = max(340, int(content_w * 0.44))
            list_w = content_w - detail_w - gap

        list_rect = pygame.Rect(content_x, content_y, list_w, body_h)
        detail_rect = pygame.Rect(list_rect.right + gap, content_y, detail_w, body_h)

        for rect, label in ((list_rect, "CHOICES"), (detail_rect, "DETAIL")):
            pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=6)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=6)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID,
                             (rect.x + 1, rect.y + 1, rect.w - 2, 30),
                             border_radius=6)
            head = get_font('small', 14).render(label, True, FP.GOLD_BRIGHT)
            self.screen.blit(head, (rect.centerx - head.get_width() // 2, rect.y + 8))

        total = len(entries)
        selected = max(0, min(selected, max(0, total - 1)))
        if scroll_attr:
            setattr(self, scroll_attr, selected)
        row_h = 64
        list_body = pygame.Rect(list_rect.x + 10, list_rect.y + 42,
                                list_rect.w - 20, list_rect.h - 54)
        visible = max(1, list_body.h // row_h)
        scroll = 0
        if total > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, total - visible)))
        for row_i, entry in enumerate(entries[scroll:scroll + visible], start=scroll):
            ry = list_body.y + (row_i - scroll) * row_h
            row_rect = pygame.Rect(list_body.x, ry, list_body.w, row_h - 6)
            is_sel = row_i == selected
            pygame.draw.rect(self.screen, (34, 43, 84) if is_sel else
                             (18, 22, 40) if row_i % 2 == 0 else (12, 15, 28),
                             row_rect, border_radius=6)
            pygame.draw.rect(self.screen, border if is_sel else FP.GOLD_DARK,
                             row_rect, 1, border_radius=6)
            key = entry.get('key', '')
            key_rect = pygame.Rect(row_rect.x + 8, row_rect.y + 9, 32, 32)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD if key else FP.GOLD_DARK,
                             key_rect, 1, border_radius=4)
            if key:
                ks = self.font_sm.render(key, True, FP.GOLD_BRIGHT)
                self.screen.blit(ks, (key_rect.centerx - ks.get_width() // 2,
                                      key_rect.centery - ks.get_height() // 2))
            icon = entry.get('icon')
            tx = key_rect.right + 8
            if icon:
                self._draw_menu_icon(icon, tx, row_rect.y + 9)
                tx += self.MENU_ICON_SIZE + 8
            badge = entry.get('badge', '')
            badge_w = 0
            if badge:
                bs = self.font_sm.render(str(badge), True, entry.get('badge_color', FP.FADED_TEXT))
                badge_w = bs.get_width() + 18
                brect = pygame.Rect(row_rect.right - badge_w - 8, row_rect.y + 14,
                                    badge_w, 26)
                pygame.draw.rect(self.screen, FP.MIDNIGHT, brect, border_radius=4)
                pygame.draw.rect(self.screen, entry.get('badge_color', border),
                                 brect, 1, border_radius=4)
                self.screen.blit(bs, (brect.centerx - bs.get_width() // 2,
                                      brect.centery - bs.get_height() // 2))
            text_w = row_rect.right - tx - badge_w - 16
            self._menu_draw_line(entry.get('name', ''), self.font_sm,
                                 entry.get('name_color', FP.BODY_TEXT),
                                 pygame.Rect(tx, row_rect.y + 8, text_w, 22))
            detail = entry.get('detail', '')
            if detail:
                self._menu_draw_line(detail, get_font('small', 14),
                                     entry.get('detail_color', FP.FADED_TEXT),
                                     pygame.Rect(tx, row_rect.y + 34, text_w, 20))

        if total > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, total)} of {total}"
            ts = get_font('small', 14).render(tag, True, FP.FADED_TEXT)
            self.screen.blit(ts, (list_rect.right - ts.get_width() - 12,
                                  list_rect.bottom - 22))

        detail_body = pygame.Rect(detail_rect.x + 14, detail_rect.y + 42,
                                  detail_rect.w - 28, detail_rect.h - 58)
        if entries:
            detail_lines = entries[selected].get('details') or []
            self._menu_draw_text_block(detail_lines, detail_body, default_font=self.font_sm)
        else:
            self._menu_draw_text_block(
                [("Nothing available.", FP.FADED_TEXT, self.font_sm)],
                detail_body, default_font=self.font_sm)

        draw_divider(self.screen, bx + 16, by + bh - footer_h - 4, bw - 32)
        hs = self.font_sm.render(hint, True, FP.HINT_TEXT)
        self.screen.blit(hs, (bx + (bw - hs.get_width()) // 2, by + bh - footer_h + 4))

    def _draw_fast_picker_variant_b(self, *, title: str, entries: list,
                                    selected: int, hint: str, border_color=None,
                                    subtitle: str = '', tabs=None,
                                    active_tab: int = 0, tab_counts=None):
        border = border_color or FP.ARCANE_BRIGHT
        draw_overlay(self.screen, 95)
        bw = min(1180, layout.GAME_W - 80)
        cols = 2 if bw >= 900 and len(entries) > 3 else 1
        max_rows_visible = 4 if cols == 2 else 6
        needed_rows = (max(1, len(entries)) + cols - 1) // cols
        rows_visible = max(1, min(max_rows_visible, needed_rows))
        visible = max(1, rows_visible * cols)
        selected = max(0, min(selected, max(0, len(entries) - 1)))
        selected_note = ''
        if entries:
            selected_note = str(entries[selected].get('full_detail')
                                or entries[selected].get('detail') or '')
        selected_note_h = 58 if selected_note else 0
        if len(entries) > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, len(entries) - visible)))
        else:
            scroll = 0
        header_h = 42 + (30 if tabs else 0)
        row_h = 52
        footer_h = 28
        bh = header_h + selected_note_h + rows_visible * row_h + footer_h + 26
        bx = (layout.GAME_W - bw) // 2
        by = layout.WINDOW_H - bh - 30
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, 40), text=title,
                        font=self.font_md, text_color=FP.GOLD_BRIGHT,
                        accent=border)
        if subtitle:
            ss = get_font('small', 14).render(subtitle, True, FP.FADED_TEXT)
            title_w = self.font_md.size(title)[0]
            title_right = bx + (bw + title_w) // 2
            subtitle_x = bx + bw - ss.get_width() - 16
            if subtitle_x > title_right + 24:
                self.screen.blit(ss, (subtitle_x, by + 12))
        y = by + 48
        if tabs:
            y = self._draw_action_tabs(tabs, active_tab, tab_counts, bx + 14, y, bw - 28)
        if selected_note:
            note_rect = pygame.Rect(bx + 16, y, bw - 32, selected_note_h - 8)
            pygame.draw.rect(self.screen, FP.MIDNIGHT, note_rect, border_radius=5)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, note_rect, 1, border_radius=5)
            self._menu_draw_wrapped(
                selected_note,
                get_font('small', 14),
                entries[selected].get('detail_color', FP.BODY_TEXT),
                pygame.Rect(note_rect.x + 10, note_rect.y + 7,
                            note_rect.w - 20, note_rect.h - 12),
                max_lines=3,
            )
            y += selected_note_h

        body = pygame.Rect(bx + 16, y, bw - 32, rows_visible * row_h)
        col_gap = 12
        col_w = (body.w - col_gap * (cols - 1)) // cols
        visible_entries = entries[scroll:scroll + visible]
        for vi, entry in enumerate(visible_entries):
            absolute = scroll + vi
            col = vi // rows_visible
            row = vi % rows_visible
            rx = body.x + col * (col_w + col_gap)
            ry = body.y + row * row_h
            rect = pygame.Rect(rx, ry, col_w, row_h - 6)
            is_sel = absolute == selected
            pygame.draw.rect(self.screen, (40, 44, 82) if is_sel else FP.MIDNIGHT,
                             rect, border_radius=5)
            pygame.draw.rect(self.screen, border if is_sel else FP.GOLD_DARK,
                             rect, 1, border_radius=5)
            key = entry.get('key', '')
            key_rect = pygame.Rect(rect.x + 8, rect.y + 10, 30, 30)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD if key else FP.GOLD_DARK,
                             key_rect, 1, border_radius=4)
            if key:
                ks = get_font('small', 14).render(key, True, entry.get('key_color', FP.GOLD_BRIGHT))
                self.screen.blit(ks, (key_rect.centerx - ks.get_width() // 2,
                                      key_rect.centery - ks.get_height() // 2))
            badge = entry.get('badge', '')
            badge_w = 0
            if badge:
                bs = get_font('small', 14).render(str(badge), True, entry.get('badge_color', FP.FADED_TEXT))
                badge_w = bs.get_width() + 18
                brect = pygame.Rect(rect.right - badge_w - 8, rect.y + 13,
                                    badge_w, 24)
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, brect, border_radius=4)
                pygame.draw.rect(self.screen, entry.get('badge_color', border),
                                 brect, 1, border_radius=4)
                self.screen.blit(bs, (brect.centerx - bs.get_width() // 2,
                                      brect.centery - bs.get_height() // 2))
            tx = key_rect.right + 8
            icon = entry.get('icon')
            if icon:
                self._draw_menu_icon(icon, tx, rect.y + 9)
                tx += self.MENU_ICON_SIZE + 8
            text_w = rect.right - tx - badge_w - 14
            self._menu_draw_line(entry.get('name', ''), self.font_sm,
                                 entry.get('name_color', FP.BODY_TEXT),
                                 pygame.Rect(tx, rect.y + 7, text_w, 22))
            self._menu_draw_line(entry.get('detail', ''), get_font('small', 14),
                                 entry.get('detail_color', FP.FADED_TEXT),
                                 pygame.Rect(tx, rect.y + 30, text_w, 18))

        draw_divider(self.screen, bx + 16, by + bh - footer_h - 6, bw - 32)
        if len(entries) > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, len(entries))} of {len(entries)}"
            ts = get_font('small', 14).render(tag, True, FP.FADED_TEXT)
            self.screen.blit(ts, (bx + 20, by + bh - footer_h + 3))
        hs = get_font('small', 14).render(hint, True, FP.HINT_TEXT)
        self.screen.blit(hs, (bx + (bw - hs.get_width()) // 2, by + bh - footer_h + 3))

    def _draw_equip_menu(self):
        tab_items = self._get_equip_tab_items()
        is_unequip = tab_items is None
        display_items = self.equip_menu_equipped if is_unequip else tab_items

        entries = []
        if is_unequip:
            for i, (slot_name, item) in enumerate(display_items):
                cursed = getattr(item, 'cursed', False)
                slot_label = slot_name.replace('_', ' ')
                detail = f"[{slot_label}]"
                if cursed:
                    detail += "  CURSED"
                entries.append({
                    'name': self._display_name(item),
                    'detail': detail,
                    'key': self._menu_letter(i),
                    'icon': item,
                    # DANGER_TEXT_LIGHT for in-menu text (DANGER_TEXT is too
                    # dark on MIDNIGHT_MID and SELECTED row backgrounds).
                    'name_color': FP.DANGER_TEXT_LIGHT if cursed else FP.GOLD_PALE,
                    'detail_color': FP.DANGER_TEXT_LIGHT if cursed else FP.FADED_TEXT,
                    'key_color': FP.WARNING_TEXT,
                    'badge': 'BOUND' if cursed else 'WORN',
                    'badge_color': FP.DANGER_TEXT_LIGHT if cursed else FP.SUCCESS_TEXT,
                    'details': self._menu_item_detail_lines(
                        item,
                        "Unequip this slot. Cursed items refuse removal until cleansed."
                        if cursed else "Unequip this slot and return the item to your pack."),
                })
        else:
            for i, item in enumerate(display_items):
                if isinstance(item, Weapon):
                    detail = f"{getattr(item, 'weapon_class', 'weapon')}  {item.base_damage}dmg  chain x{item.max_chain_length or '?'}"
                elif isinstance(item, Shield):
                    detail = f"+{item.ac_bonus} AC  {item.material}"
                elif isinstance(item, Armor):
                    detail = f"{getattr(item, 'slot', 'armor')}  +{item.ac_bonus} AC  {item.material}"
                elif isinstance(item, Accessory):
                    if item.identified or self.player.knows_item_type(item):
                        fx = item.effects
                        if 'status' in fx:
                            detail = f"grants {fx['status']}"
                        elif 'stat' in fx:
                            detail = f"{fx['stat']} +{fx.get('amount', 0)}"
                        elif getattr(item, 'slot', '') == 'none':
                            detail = "passive (carry-only)"
                        else:
                            detail = "accessory"
                    else:
                        detail = "unidentified"
                else:
                    detail = item.item_class
                delta = self._equip_delta_str(item)
                if delta:
                    detail = f"{detail}   {delta}"
                entries.append({
                    'name': self._display_name(item),
                    'detail': detail,
                    'key': self._menu_letter(i),
                    'icon': item,
                    'badge': 'CHAIN' if getattr(item, 'equip_chain_mode', '') else '',
                    'badge_color': FP.ARCANE_BRIGHT,
                    'details': self._menu_item_detail_lines(
                        item,
                        "Equip this item. Armor and accessories may start their subject quiz first."),
                })

        _equip_counts = []
        for _, filt in self._EQUIP_TABS:
            if filt is None:
                _equip_counts.append(len(self.equip_menu_equipped))
            else:
                _equip_counts.append(sum(1 for it in self.equip_menu_items if filt(it)))

        selected = self._menu_clamp_selection('_equip_sel', len(display_items))
        slot_note = "Unequip selected worn item." if is_unequip else "Equip selected item."
        context = self._menu_base_context([
            ("LOADOUT", FP.GOLD_BRIGHT, self.font_sm),
            (f"AC {self.player.get_ac()}    {slot_note}", FP.BODY_TEXT, self.font_sm),
            ("Weapons, armor, shields, accessories, and unequip each keep their own tabs.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="EQUIP / UNEQUIP",
            entries=entries,
            selected=selected,
            context_lines=context,
            tabs=self._EQUIP_TABS,
            active_tab=self._menu_tab,
            tab_counts=_equip_counts,
            hint="Left/Right: tab   Up/Down: move   Enter or a-z: select   ESC: cancel",
            border_color=FP.GOLD,
            scroll_attr='_equip_scroll',
        )

    # ------------------------------------------------------------------
    # Kit comparison panel  (K key)
    # ------------------------------------------------------------------

    _KIT_SRC_COLOR = {
        'equip': (220, 200, 120),  # gold-ish: currently worn
        'pack':  (200, 200, 200),  # normal
        'floor': (140, 140, 140),  # dim: on the ground here
    }
    _KIT_SRC_TAG = {'equip': 'eq', 'pack': 'pk', 'floor': 'fl'}

    def _kit_rows_for_slug(self, slug: str):
        all_rows = self._kit_collect_items()
        tab_slugs = [t[1] for t in self._KIT_TABS]
        rows = self._kit_filter_for_tab(all_rows, tab_slugs.index(slug))
        order = {'floor': 0, 'equip': 1, 'pack': 2}
        if slug == 'weapons':
            rows.sort(key=lambda r: (order.get(r[0], 9),
                                     -float(self._kit_avg_damage(r[1]) or 0)))
        elif slug in ('armor', 'shields'):
            rows.sort(key=lambda r: (order.get(r[0], 9),
                                     -int(getattr(r[1], 'ac_bonus', 0) or 0)))
        else:
            rows.sort(key=lambda r: (order.get(r[0], 9),
                                     self._display_name(r[1]).lower()))
        return rows

    def _kit_source_label(self, src: str) -> str:
        return {'equip': 'Equipped', 'pack': 'Pack', 'floor': 'Floor'}.get(src, src)

    def _kit_detail_lines_for_item(self, slug: str, src: str, item):
        idl = self._kit_visible_level(item)
        lines = [
            (self._display_name(item), FP.GOLD_PALE, get_font('heading', 22)),
            (f"Source: {self._kit_source_label(src)}", FP.FADED_TEXT, self.font_sm),
            (f"Identity: {idl}/5", FP.CYAN_ACCENT, self.font_sm),
            (f"Weight: {getattr(item, 'weight', 0):g}", FP.BODY_TEXT, self.font_sm),
        ]
        delta = self._equip_delta_str(item)
        if delta:
            color = FP.SUCCESS_TEXT if '+' in delta else FP.WARNING_TEXT
            lines.append((delta, color, self.font_sm))
        col_defs = self._kit_column_defs(slug)
        cells = self._kit_cells_for_item(slug, src, item)
        labels = [c.label for c in col_defs] if col_defs else []
        if idl >= 3:
            lines.append(("Visible stats", FP.GOLD_BRIGHT, self.font_sm))
            for label, value in zip(labels[2:], cells[2:]):
                if value not in ('', None):
                    lines.append((f"{label}: {value}", FP.BODY_TEXT, self.font_sm))
        else:
            lines.append(("Stats remain hidden until identification level 3.",
                          FP.FADED_TEXT, self.font_sm))

        tiers = getattr(item, 'tier_bonuses', None) or {}
        if tiers and idl >= 3:
            achieved = int(getattr(item, 'achieved_tier', 0) or 0)
            lines.append(("Chain abilities", FP.GOLD_BRIGHT, self.font_sm))
            for tier in range(1, 6):
                row = tiers.get(str(tier), tiers.get(tier, {})) or {}
                labels = [self._lore_bonus_label(k, v) for k, v in row.items()]
                color = FP.SUCCESS_TEXT if achieved >= tier else FP.FADED_TEXT
                lines.append((f"T{tier}: " + ('; '.join(labels) if labels else '?'),
                              color, self.font_sm))

        lore = getattr(item, 'lore', '') if idl >= 4 else ''
        if lore:
            lines += [
                ("Lore", FP.GOLD_BRIGHT, self.font_sm),
                (lore, FP.LORE_BLUE_BODY, get_font('body', 16)),
            ]
        return lines

    def _kit_detail_lines_for_spell(self, spell):
        return [
            (spell.get('name', spell.get('spell_id', '?')),
             FP.GOLD_PALE, get_font('heading', 22)),
            (f"Tier: {spell.get('quiz_tier', '?')}   MP: {spell.get('mp_cost', '?')}",
             FP.CYAN_ACCENT, self.font_sm),
            ("Description", FP.GOLD_BRIGHT, self.font_sm),
            (spell.get('desc', ''), FP.BODY_TEXT, get_font('body', 16)),
        ]

    def _draw_kit_detail_lines(self, rect, lines):
        render_lines = []
        for text, color, fnt in lines:
            for line in self._ui_text_lines(text, fnt, rect.w - 14):
                render_lines.append((line, color, fnt))
            if color in (FP.GOLD_PALE, FP.GOLD_BRIGHT):
                render_lines.append(("", color, fnt))
        self._ui_draw_scroll_lines(render_lines, self.font_sm, FP.BODY_TEXT,
                                   rect, 0, line_gap=5)

    def _draw_kit_browser(self):
        active = getattr(self, '_kit_tab', 0)
        slug = self._KIT_TABS[active][1]
        panel = self._ui_modal_panel("KIT COMPARISON",
                                     border_color=FP.GOLD,
                                     max_w=1444,
                                     max_h=766)
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        tab_y = body.y
        x = body.x
        for idx, (label, _slug) in enumerate(self._KIT_TABS):
            width = 154 if label == 'Consumables' else 128
            rect = pygame.Rect(x, tab_y, width, 28)
            self._ui_chip(rect, label, active=(idx == active), color=FP.GOLD)
            x += width + 8

        content_y = tab_y + 42
        content_h = body.bottom - content_y
        gutter = 14
        detail_w = min(450, max(360, int(body.w * 0.34)))
        table_rect = pygame.Rect(body.x, content_y,
                                 body.w - detail_w - gutter, content_h)
        detail_rect = pygame.Rect(table_rect.right + gutter, content_y,
                                  detail_w, content_h)
        table_body = self._ui_subpanel(table_rect, f"Compare {self._KIT_TABS[active][0]}")
        detail_body = self._ui_subpanel(detail_rect, "Selected Comparison")

        if slug == 'spells':
            rows = self._kit_collect_spells()
            total = len(rows)
        else:
            rows = self._kit_rows_for_slug(slug)
            total = len(rows)

        if not rows:
            empty = "(you have learned no spells yet)" if slug == 'spells' else (
                "(nothing of this kind in your pack, equipment, or current tile)"
            )
            self._ui_wrap_text(empty, self.font_sm, FP.FADED_TEXT, table_body)
            self._ui_footer(panel, "Left/Right: tab   ESC: close")
            return

        sel = max(0, min(getattr(self, '_kit_sel', 0), total - 1))
        self._kit_sel = sel
        row_h = 62
        visible = max(1, (table_body.h - 28) // row_h)
        scroll = getattr(self, '_kit_scroll', 0)
        if sel < scroll:
            scroll = sel
        if sel >= scroll + visible:
            scroll = sel - visible + 1
        scroll = max(0, min(scroll, max(0, total - visible)))
        self._kit_scroll = scroll

        header_font = get_font('small', 13, bold=True)
        headers = ([("Spell", 0.40), ("Cost", 0.16), ("Description", 0.44)]
                   if slug == 'spells' else
                   [("Src", 0.08), ("Name", 0.42), ("Stats", 0.24), ("Special", 0.26)])
        hx = table_body.x
        for label, frac in headers:
            hw = int(table_body.w * frac)
            self._ui_blit_text(label, header_font, FP.GOLD_PALE, hx, table_body.y)
            hx += hw
        pygame.draw.line(self.screen, FP.GOLD_DARK,
                         (table_body.x, table_body.y + 23),
                         (table_body.right - 10, table_body.y + 23), 1)

        y = table_body.y + 32
        for idx, row in enumerate(rows[scroll:scroll + visible], start=scroll):
            selected = idx == sel
            rect = pygame.Rect(table_body.x, y, table_body.w - 12, row_h - 7)
            pygame.draw.rect(self.screen,
                             (35, 43, 82) if selected else FP.MIDNIGHT,
                             rect, border_radius=6)
            pygame.draw.rect(self.screen, FP.GOLD if selected else FP.ARCANE_DIM,
                             rect, 1, border_radius=6)
            if slug == 'spells':
                spell = row
                col1 = pygame.Rect(rect.x + 10, rect.y + 7, int(rect.w * 0.40) - 18, rect.h - 10)
                col2 = pygame.Rect(col1.right + 8, rect.y + 7, int(rect.w * 0.16), rect.h - 10)
                col3 = pygame.Rect(col2.right + 8, rect.y + 7,
                                   rect.right - col2.right - 16, rect.h - 10)
                self._ui_wrap_text(spell.get('name', '?'), get_font('small', 15, bold=True),
                                   FP.GOLD_BRIGHT if selected else FP.BODY_TEXT,
                                   col1, line_gap=0, max_lines=2)
                self._ui_wrap_text(f"T{spell.get('quiz_tier', '-')}, {spell.get('mp_cost', '?')} MP",
                                   self.font_sm, FP.CYAN_ACCENT, col2,
                                   line_gap=0, max_lines=2)
                self._ui_wrap_text(spell.get('desc', ''), get_font('small', 13),
                                   FP.FADED_TEXT, col3, line_gap=0, max_lines=2)
            else:
                src, item = row
                cells = self._kit_cells_for_item(slug, src, item)
                col_src = pygame.Rect(rect.x + 10, rect.y + 8, int(rect.w * 0.08), rect.h - 10)
                col_name = pygame.Rect(col_src.right + 8, rect.y + 7,
                                       int(rect.w * 0.42) - 16, rect.h - 10)
                col_stats = pygame.Rect(col_name.right + 8, rect.y + 7,
                                        int(rect.w * 0.24) - 16, rect.h - 10)
                col_special = pygame.Rect(col_stats.right + 8, rect.y + 7,
                                          rect.right - col_stats.right - 16,
                                          rect.h - 10)
                self._ui_blit_text(cells[1] if len(cells) > 1 else src,
                                   get_font('small', 13, bold=True),
                                   self._KIT_SRC_COLOR.get(src, FP.BODY_TEXT),
                                   col_src.x, col_src.y,
                                   max_width=col_src.w)
                self._ui_wrap_text(self._display_name(item), get_font('small', 15, bold=True),
                                   self._KIT_SRC_COLOR.get(src, FP.BODY_TEXT),
                                   col_name, line_gap=0, max_lines=2)
                stats = " / ".join(str(c) for c in cells[2:-1] if c not in ('', None))
                self._ui_wrap_text(stats or "-", get_font('small', 13),
                                   FP.BODY_TEXT, col_stats,
                                   line_gap=0, max_lines=2)
                special = str(cells[-1]) if cells else ''
                self._ui_wrap_text(special or "-", get_font('small', 13),
                                   FP.FADED_TEXT, col_special,
                                   line_gap=0, max_lines=2)
            y += row_h

        if total > visible:
            self._ui_scrollbar(table_body, scroll, total, visible)

        if slug == 'spells':
            detail_lines = self._kit_detail_lines_for_spell(rows[sel])
        else:
            src, item = rows[sel]
            detail_lines = self._kit_detail_lines_for_item(slug, src, item)
        self._draw_kit_detail_lines(detail_body, detail_lines)
        self._ui_footer(panel, "Left/Right: tab   Up/Down: select   PgUp/PgDn: jump   ESC: close")

    def _draw_kit_panel(self):
        self._draw_kit_browser()
        return
        """Tabbed compare panel — routed through PanelBuilder so it shares
        chrome with every other modal in the game.
        """
        from panel import PanelBuilder, SIZE_XL
        active = getattr(self, '_kit_tab', 0)
        slug = self._KIT_TABS[active][1]
        p = PanelBuilder(self.screen, size=SIZE_XL,
                         border_color=FP.GOLD, max_height=700)
        p.set_title("KIT  --  YOUR PACK & WHAT LIES HERE",
                    font=self.font_lg)
        p.set_tabs([label for label, _slug in self._KIT_TABS], active=active)
        p.set_footer_hint("Left/Right: tab   Up/Down: scroll   ESC: close")
        body = p.body_rect()

        if slug == 'spells':
            self._kit_draw_spells(body.x, body.y, body.w, body.h)
        else:
            self._kit_draw_items(body.x, body.y, body.w, body.h, slug)

        p.draw()

    # --------------------------------------------------------------
    # Shared content-measured table helper
    # --------------------------------------------------------------
    # Every column-table render in this file goes through here. The
    # contract: fixed columns (flex=0) get sized to their actual content
    # (max of header width + widest cell width + gutter); flex columns
    # absorb leftover space by weight. Truncation is a backstop only.
    # See proposals/v2_audit/IDENTIFY_SYSTEM.md §11 + the kit-menu fix
    # commit 2026-05-28.
    def _draw_measured_table(
        self,
        *,
        x: int, y: int, w: int, h: int,
        col_defs,
        cells_per_row,
        font,
        header_color,
        row_color_fn=None,
        default_row_color=(200, 200, 200),
        scroll: int = 0,
        line_h: int = 24,
        gutter: int = 12,
        left_pad: int = 4,
        header_y_offset: int = 0,
        divider_y_offset: int = 22,
        body_y_offset: int = 28,
    ) -> tuple[int, int]:
        """Render a column table with content-measured widths.

        Args:
          col_defs:        list[Column] — labels + flex weights + alignments.
          cells_per_row:   list[list[str]] — every row's cell text. Used
                            to measure column widths AND to render.
          font:            pygame font for both header and cell text.
          header_color:    color for the header row.
          row_color_fn:    optional callable(row_index) -> color for the
                            body row. Falls back to default_row_color.
          default_row_color: used when row_color_fn is None.
          scroll:          row index of the first visible row.

        Returns: (max_visible_count, total_rows). The caller can use this
                  to draw a scrollbar hint.
        """
        from text_layout import Column, fit_columns, truncate_label
        if not col_defs or not cells_per_row:
            return 0, 0

        max_visible = max(1, (h - body_y_offset) // line_h)
        scroll = max(0, min(scroll, max(0, len(cells_per_row) - max_visible)))

        # Measure: for each column, natural width = max(header width,
        # widest cell in that column) + gutter. Flex columns floor at
        # their declared min_w so they can still absorb leftover space.
        measured_cols: list[Column] = []
        for i, c in enumerate(col_defs):
            natural = font.size(c.label)[0]
            for cells in cells_per_row:
                if i < len(cells):
                    cell_text = str(cells[i] or '')
                    natural = max(natural, font.size(cell_text)[0])
            # Floor: header/content width OR declared min_w for flex cols.
            min_w = max(natural, c.min_w if c.flex > 0 else 0) + gutter
            measured_cols.append(Column(c.label, min_w, c.flex, c.align))

        widths = fit_columns(measured_cols, w)
        cols = [(c.label, ww, c.align) for c, ww in zip(measured_cols, widths)]

        # Header row
        cx = x
        for label, cw, align in cols:
            label_text = truncate_label(label, max(1, cw - gutter), font)
            hdr = font.render(label_text, True, header_color)
            if align == 'right':
                self.screen.blit(hdr, (cx + cw - gutter - hdr.get_width(),
                                        y + header_y_offset))
            else:
                self.screen.blit(hdr, (cx + left_pad, y + header_y_offset))
            cx += cw
        draw_divider(self.screen, x, y + divider_y_offset, w)

        # Body rows
        ry = y + body_y_offset
        for idx, cells in enumerate(cells_per_row[scroll:scroll + max_visible],
                                     start=scroll):
            row_col = (row_color_fn(idx) if row_color_fn else default_row_color)
            cx = x
            for (label, cw, align), text in zip(cols, cells):
                if text is None:
                    text = ''
                cell_w = max(1, cw - gutter)
                clipped = truncate_label(str(text), cell_w, font)
                surf = font.render(clipped, True, row_col)
                if align == 'right':
                    self.screen.blit(surf, (cx + cw - gutter - surf.get_width(), ry))
                else:
                    self.screen.blit(surf, (cx + left_pad, ry))
                cx += cw
            ry += line_h

        return max_visible, len(cells_per_row)

    def _kit_draw_items(self, x: int, y: int, w: int, h: int, slug: str):
        # Content-measured columns via the shared helper. Every column-
        # table render in the game goes through _draw_measured_table.
        all_rows = self._kit_collect_items()
        rows = self._kit_filter_for_tab(all_rows, [t[1] for t in self._KIT_TABS].index(slug))

        # Sort: floor first (transient interest), then equipped, then pack
        order = {'floor': 0, 'equip': 1, 'pack': 2}
        if slug == 'weapons':
            rows.sort(key=lambda r: (order.get(r[0], 9),
                                     -float(self._kit_avg_damage(r[1]) or 0)))
        elif slug in ('armor', 'shields'):
            rows.sort(key=lambda r: (order.get(r[0], 9),
                                     -int(getattr(r[1], 'ac_bonus', 0) or 0)))
        else:
            rows.sort(key=lambda r: (order.get(r[0], 9), self._display_name(r[1]).lower()))

        if not rows:
            txt = self.font_sm.render("(nothing of this kind in your pack or on this tile)",
                                      True, FP.FADED_TEXT)
            self.screen.blit(txt, (x, y + 10))
            return

        col_defs = self._kit_column_defs(slug)
        if not col_defs:
            return

        # Pre-compute every cell so the helper can measure + render
        # from the same data. ALL rows (not just visible) measured so
        # column widths stay stable across scrolls.
        cells_per_row = [self._kit_cells_for_item(slug, src, item)
                          for src, item in rows]

        # Row color is per-row (equipped vs floor vs pack)
        row_colors = [self._KIT_SRC_COLOR.get(src, (200, 200, 200))
                       for src, _ in rows]

        scroll = max(0, getattr(self, '_kit_scroll', 0))
        max_visible, total = self._draw_measured_table(
            x=x, y=y, w=w, h=h,
            col_defs=col_defs,
            cells_per_row=cells_per_row,
            font=self.font_sm,
            header_color=FP.GOLD_PALE,
            row_color_fn=lambda i: row_colors[i],
            scroll=scroll,
        )
        # Clamp self._kit_scroll after the helper has computed max_visible
        self._kit_scroll = max(0, min(scroll, max(0, total - max_visible)))

        if total > max_visible:
            tag = self.font_sm.render(
                f"{self._kit_scroll + 1}-{min(self._kit_scroll + max_visible, total)} of {total}",
                True, FP.FADED_TEXT)
            self.screen.blit(tag, (x + w - tag.get_width(), y + h - 22))

    def _kit_column_defs(self, slug: str):
        """Per-tab column definitions (label, fallback min_w, flex, align).

        Returns raw Column list — the caller in `_kit_draw_items` does the
        content-measure pass + fit. The fallback `min_w` values here matter
        ONLY for flex columns (Name / Special / Resists / Effect); fixed
        columns get their width measured from actual content at render time.
        """
        from text_layout import Column
        if slug == 'weapons':
            return [
                Column('Name',     180, flex=2, align='left'),
                Column('Src',        0, flex=0, align='left'),
                Column('Dmg',        0, flex=0, align='right'),
                Column('Avg',        0, flex=0, align='right'),
                Column('Material',   0, flex=0, align='left'),
                Column('BUC',        0, flex=0, align='left'),
                Column('Wt',         0, flex=0, align='right'),
                Column('Special',  140, flex=3, align='left'),
            ]
        if slug == 'armor':
            return [
                Column('Name',     180, flex=2, align='left'),
                Column('Src',        0, flex=0, align='left'),
                Column('Slot',       0, flex=0, align='left'),
                Column('AC',         0, flex=0, align='right'),
                Column('Material',   0, flex=0, align='left'),
                Column('BUC',        0, flex=0, align='left'),
                Column('Wt',         0, flex=0, align='right'),
                Column('Resists',  120, flex=3, align='left'),
            ]
        if slug == 'shields':
            return [
                Column('Name',     180, flex=2, align='left'),
                Column('Src',        0, flex=0, align='left'),
                Column('AC',         0, flex=0, align='right'),
                Column('Material',   0, flex=0, align='left'),
                Column('BUC',        0, flex=0, align='left'),
                Column('Wt',         0, flex=0, align='right'),
                Column('Resists',  140, flex=3, align='left'),
            ]
        if slug == 'accessories':
            return [
                Column('Name',     180, flex=2, align='left'),
                Column('Src',        0, flex=0, align='left'),
                Column('Slot',       0, flex=0, align='left'),
                Column('BUC',        0, flex=0, align='left'),
                Column('Wt',         0, flex=0, align='right'),
                Column('Effect',   200, flex=3, align='left'),
            ]
        if slug == 'consumables':
            return [
                Column('Name',     180, flex=2, align='left'),
                Column('Src',        0, flex=0, align='left'),
                Column('Type',       0, flex=0, align='left'),
                Column('BUC',        0, flex=0, align='left'),
                Column('Wt',         0, flex=0, align='right'),
                Column('Effect',   200, flex=3, align='left'),
            ]
        return []

    def _kit_cells_for_item(self, slug: str, src: str, item) -> list[str]:
        """Return list of cell strings matching _kit_columns(slug)."""
        idl = self._kit_visible_level(item)
        name = self._display_name(item)
        src_tag = self._KIT_SRC_TAG.get(src, '?')
        wt = str(int(getattr(item, 'weight', 0) or 0))
        mat = getattr(item, 'material', '') or ''

        # BUC visibility: id_level >= 2 reveals; otherwise '?'
        if idl >= 2:
            buc_raw = getattr(item, 'buc', None) or ('cursed' if getattr(item, 'cursed', False) else 'uncursed')
            buc = {'blessed': 'bless.', 'uncursed': 'unc.', 'cursed': 'CURSED'}.get(buc_raw, buc_raw)
        else:
            buc = '?'

        if slug == 'weapons':
            if idl >= 3:
                dmg = self._kit_damage_str(item)
                avg = self._kit_avg_damage(item)
                avg_s = f"{avg:.1f}" if avg is not None else '?'
                # Class mechanic shows once the weapon class is known (idl>=3) --
                # it's a property of the weapon type; magical extras stay gated
                # inside the helper at idl>=4.
                special = self._kit_weapon_special(item, idl)
            else:
                dmg, avg_s, special = '?', '?', '?'
            return [name, src_tag, dmg, avg_s, mat, buc, wt, special]

        if slug == 'armor':
            slot_lbl = (getattr(item, 'slot', '') or '').replace('_', ' ')
            if idl >= 3:
                ac = f"+{getattr(item, 'ac_bonus', 0)}"
                resists = self._kit_resist_str(item)
            else:
                ac, resists = '?', '?'
            return [name, src_tag, slot_lbl, ac, mat, buc, wt, resists]

        if slug == 'shields':
            if idl >= 3:
                ac = f"+{getattr(item, 'ac_bonus', 0)}"
                resists = self._kit_resist_str(item)
            else:
                ac, resists = '?', '?'
            return [name, src_tag, ac, mat, buc, wt, resists]

        if slug == 'accessories':
            slot_lbl = (getattr(item, 'slot', '') or '').replace('_', ' ')
            if idl >= 3:
                effect = self._kit_accessory_effect(item)
            else:
                effect = '?'
            return [name, src_tag, slot_lbl, buc, wt, effect]

        if slug == 'consumables':
            kind = type(item).__name__
            if idl >= 3:
                effect = self._kit_consumable_effect(item)
            else:
                effect = '?'
            # Most consumables don't carry BUC; show '-' when not applicable
            buc_show = buc if hasattr(item, 'buc') or hasattr(item, 'cursed') else '-'
            return [name, src_tag, kind, buc_show, wt, effect]

        return [name, src_tag] + ['' for _ in range(6)]

    # --- small helpers for cell formatting ---

    def _kit_damage_str(self, w) -> str:
        d = getattr(w, 'damage', None)
        if d:
            return str(d)
        base = getattr(w, 'base_damage', None)
        if base is not None:
            return f"{base}"
        return '?'

    def _kit_avg_damage(self, w) -> float | None:
        # Dice notation "XdY+Z"
        d = getattr(w, 'damage', None)
        if d and 'd' in str(d):
            try:
                left, rest = str(d).split('d', 1)
                bonus = 0
                if '+' in rest:
                    sides, bonus_s = rest.split('+', 1)
                    bonus = int(bonus_s)
                elif '-' in rest:
                    sides, bonus_s = rest.split('-', 1)
                    bonus = -int(bonus_s)
                else:
                    sides = rest
                n = int(left); s = int(sides)
                return n * (s + 1) / 2 + bonus
            except (ValueError, IndexError):
                return None
        base = getattr(w, 'base_damage', None)
        if base is not None:
            try:
                return float(base)
            except (TypeError, ValueError):
                return None
        return None

    def _kit_weapon_special(self, w, idl: int = 5) -> str:
        bits = []
        # Class mechanic FIRST -- the weapon's signature ability (Backstab,
        # Reach 2, Master Strike...). Shown once the weapon class is known.
        mech = getattr(w, 'class_mechanic', None)
        if mech:
            from combat import class_mechanic_info
            info = class_mechanic_info(mech)
            if info:
                bits.append(info[0])
        # Magical / unique extras need fuller identification (idl>=4).
        if idl >= 4:
            dt = getattr(w, 'damage_types', None) or []
            if dt and dt != ['slash'] and dt != ['pierce'] and dt != ['crush']:
                bits.append('+'.join(dt))
            if getattr(w, 'two_handed', False):
                bits.append('2H')
            sb = getattr(w, 'special_blessing', None) or getattr(w, 'unique_effect', None)
            if sb:
                bits.append(str(sb)[:32])
        return ', '.join(bits) if bits else '-'

    def _kit_resist_str(self, a) -> str:
        r = getattr(a, 'damage_resistances', None) or {}
        if not r:
            return '-'
        return ', '.join(f"{k} {int(v*100)}%" for k, v in r.items() if v)

    def _kit_accessory_effect(self, a) -> str:
        fx = getattr(a, 'effects', None) or {}
        if not fx:
            return '-'
        parts = []
        if 'stat' in fx:
            parts.append(f"{fx['stat']} +{fx.get('amount', 0)}")
        if 'stat2' in fx:
            parts.append(f"{fx['stat2']} +{fx.get('amount2', 0)}")
        if 'status' in fx:
            parts.append(f"grants {fx['status']}")
        return ', '.join(parts) if parts else '-'

    def _equip_delta_str(self, candidate) -> str:
        """Return a short "Δ +X dmg / -Y wt" string vs the currently equipped
        item in this candidate's slot, or '' if no comparable item exists.

        Reveals deltas only for fields the player has earned the right to see
        (re-uses _kit_visible_level). Pure side-effect-free string builder.
        """
        if isinstance(candidate, Weapon):
            equipped = self.player.weapon
            if equipped is candidate or equipped is None:
                return ''
            if self._kit_visible_level(candidate) < 3 or self._kit_visible_level(equipped) < 3:
                return ''
            c_avg = self._kit_avg_damage(candidate)
            e_avg = self._kit_avg_damage(equipped)
            if c_avg is None or e_avg is None:
                return ''
            d = c_avg - e_avg
            return self._fmt_delta(d, 'dmg', decimals=1)

        if isinstance(candidate, Shield):
            equipped = self.player.shield
            if equipped is candidate or equipped is None:
                return ''
            if self._kit_visible_level(candidate) < 3 or self._kit_visible_level(equipped) < 3:
                return ''
            d = int(getattr(candidate, 'ac_bonus', 0)) - int(getattr(equipped, 'ac_bonus', 0))
            return self._fmt_delta(d, 'AC')

        if isinstance(candidate, Armor):
            from items import ARMOR_SLOTS
            slot = getattr(candidate, 'slot', '')
            if slot not in ARMOR_SLOTS:
                return ''
            idx = ARMOR_SLOTS.index(slot)
            equipped = self.player.armor_slots[idx]
            if equipped is candidate or equipped is None:
                return ''
            if self._kit_visible_level(candidate) < 3 or self._kit_visible_level(equipped) < 3:
                return ''
            d = int(getattr(candidate, 'ac_bonus', 0)) - int(getattr(equipped, 'ac_bonus', 0))
            return self._fmt_delta(d, 'AC')

        if isinstance(candidate, Accessory):
            # Only useful when comparing same-stat accessories; otherwise
            # there's no shared dimension to compute a delta on.
            if self._kit_visible_level(candidate) < 3:
                return ''
            fx_c = getattr(candidate, 'effects', None) or {}
            stat_c = fx_c.get('stat')
            amt_c  = fx_c.get('amount', 0)
            if not stat_c:
                return ''
            # Find an equipped accessory affecting the same stat
            for slot_item in self.player.equipped_accessories:
                if slot_item is candidate:
                    continue
                if self._kit_visible_level(slot_item) < 3:
                    continue
                fx_e = getattr(slot_item, 'effects', None) or {}
                if fx_e.get('stat') == stat_c:
                    d = int(amt_c) - int(fx_e.get('amount', 0))
                    return self._fmt_delta(d, stat_c)
            return ''

        return ''

    def _fmt_delta(self, d, label: str, decimals: int = 0) -> str:
        if decimals:
            if abs(d) < 10 ** (-decimals):
                return f"Δ  {label}  (no change)"
            sign = '+' if d > 0 else '−'
            return f"Δ {sign}{abs(d):.{decimals}f} {label}"
        if d == 0:
            return f"Δ  {label}  (no change)"
        sign = '+' if d > 0 else '−'
        return f"Δ {sign}{abs(d)} {label}"

    def _kit_consumable_effect(self, c) -> str:
        eff = getattr(c, 'effect', None)
        if eff:
            pw = getattr(c, 'power', '')
            dur = getattr(c, 'duration', 0)
            tail = []
            if pw:
                tail.append(str(pw))
            if dur:
                tail.append(f"{dur}t")
            return f"{eff}" + (f" ({', '.join(tail)})" if tail else '')
        # Spellbook
        sp_id = getattr(c, 'spell_id', None)
        if sp_id:
            sd = LEARNABLE_SPELLS.get(sp_id, {})
            return f"teaches {sd.get('name', sp_id)} ({sd.get('mp_cost','?')} MP)"
        # Food
        if hasattr(c, 'sp_restore'):
            bits = [f"+{c.sp_restore} SP"]
            if getattr(c, 'hp_restore', 0):
                bits.append(f"+{c.hp_restore} HP")
            bt = getattr(c, 'bonus_type', 'none')
            if bt and bt != 'none':
                bits.append(f"{bt}")
            return ', '.join(bits)
        return '-'

    def _kit_draw_spells(self, x: int, y: int, w: int, h: int):
        # Content-measured columns via the shared helper. Spell + Description
        # are flex columns; Tier + MP get sized to their actual content
        # (which is small, so they end up nicely tight).
        from text_layout import Column
        rows = self._kit_collect_spells()
        if not rows:
            txt = self.font_sm.render("(you have learned no spells yet)",
                                      True, FP.FADED_TEXT)
            self.screen.blit(txt, (x, y + 10))
            return
        col_defs = [
            Column('Spell',       180, flex=2, align='left'),
            Column('Tier',          0, flex=0, align='right'),
            Column('MP',            0, flex=0, align='right'),
            Column('Description', 200, flex=4, align='left'),
        ]
        cells_per_row = [
            [r['name'],
             f"T{r['quiz_tier']}" if r['quiz_tier'] else '-',
             str(r['mp_cost']),
             r['desc']]
            for r in rows
        ]
        scroll = max(0, getattr(self, '_kit_scroll', 0))
        max_visible, total = self._draw_measured_table(
            x=x, y=y, w=w, h=h,
            col_defs=col_defs,
            cells_per_row=cells_per_row,
            font=self.font_sm,
            header_color=FP.GOLD_PALE,
            default_row_color=FP.BODY_TEXT,
            scroll=scroll,
        )
        self._kit_scroll = max(0, min(scroll, max(0, total - max_visible)))
        if total > max_visible:
            tag = self.font_sm.render(
                f"{self._kit_scroll + 1}-{min(self._kit_scroll + max_visible, total)} of {total}",
                True, FP.FADED_TEXT)
            self.screen.blit(tag, (x + w - tag.get_width(), y + h - 22))

    # ------------------------------------------------------------------
    # Discoveries panel  (J key)
    # ------------------------------------------------------------------

    def _draw_discoveries_panel(self):
        """Player-growth record. Pure tally of what's been done. No spoilers."""
        panel = self._ui_modal_panel("DISCOVERIES - YOUR RECORD",
                                     border_color=FP.GOLD,
                                     max_w=1320,
                                     max_h=720)
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        sections = self._discoveries_sections()
        if not sections:
            self._ui_wrap_text("No discoveries recorded yet.", self.font_md,
                               FP.FADED_TEXT, body)
            self._ui_footer(panel, "ESC: close")
            return

        gutter = 14
        rail_w = min(300, max(245, int(body.w * 0.26)))
        rail_rect = pygame.Rect(body.x, body.y, rail_w, body.h)
        detail_rect = pygame.Rect(rail_rect.right + gutter, body.y,
                                  body.w - rail_w - gutter, body.h)
        rail_body = self._ui_subpanel(rail_rect, "Record Sections")
        detail_body = self._ui_subpanel(detail_rect, "Run Record")

        sel = max(0, min(getattr(self, '_disc_sel', 0), len(sections) - 1))
        self._disc_sel = sel
        row_h = 52
        visible = max(1, rail_body.h // row_h)
        scroll = max(0, min(sel, max(0, len(sections) - visible)))
        if sel >= scroll + visible:
            scroll = sel - visible + 1

        y = rail_body.y
        for idx, (header, rows) in enumerate(sections[scroll:scroll + visible],
                                             start=scroll):
            rect = pygame.Rect(rail_body.x, y, rail_body.w - 10, row_h - 7)
            selected = idx == sel
            pygame.draw.rect(self.screen,
                             (35, 43, 82) if selected else FP.MIDNIGHT,
                             rect, border_radius=6)
            pygame.draw.rect(self.screen, FP.GOLD if selected else FP.GOLD_DARK,
                             rect, 1, border_radius=6)
            self._ui_blit_text(header.title(), get_font('small', 14, bold=True),
                               FP.GOLD_BRIGHT if selected else FP.BODY_TEXT,
                               rect.x + 10, rect.y + 7, max_width=rect.w - 20)
            first = next((r.strip() for r in rows if str(r).strip()), "")
            self._ui_blit_text(first, get_font('small', 12), FP.FADED_TEXT,
                               rect.x + 10, rect.y + 27, max_width=rect.w - 20)
            y += row_h

        header, rows = sections[sel]
        render_lines = [
            (header.title(), FP.GOLD_PALE, get_font('heading', 24)),
            ("", FP.BODY_TEXT, self.font_sm),
        ]
        for row in rows:
            text = str(row).strip()
            if not text:
                render_lines.append(("", FP.BODY_TEXT, self.font_sm))
            else:
                render_lines.append((text, FP.BODY_TEXT, self.font_sm))
        flat = []
        for text, color, fnt in render_lines:
            if text == "":
                flat.append(("", color, fnt))
                continue
            for line in self._ui_text_lines(text, fnt, detail_body.w - 14):
                flat.append((line, color, fnt))
        self._disc_scroll = self._ui_draw_scroll_lines(
            flat, self.font_sm, FP.BODY_TEXT, detail_body,
            getattr(self, '_disc_scroll', 0), line_gap=5)
        self._ui_footer(panel, "Up/Down: section   PgUp/PgDn: scroll record   ESC: close")

    def _discoveries_sections(self):
        """Return list of (section_title, [row_string, ...]) tuples.

        Reads only data the game is actually tracking; pulls from the player
        for per-run sets (known_*, masteries, quirks) and from Game-level
        counters (correct_answers, missed_questions, karma) for journey state.
        """
        p = self.player
        sections = []

        # --- Quiz performance: totals + per-subject breakdown ---
        right_total = int(getattr(self, 'correct_answers', 0) or 0)
        wrong_total = int(getattr(self, 'wrong_answers', 0) or 0)
        total = right_total + wrong_total
        acc = (right_total / total * 100) if total else 0.0
        quiz_rows = [
            f"  Total answered:  {total}   ({right_total} right / {wrong_total} wrong, {acc:.0f}%)",
        ]
        # Per-subject + per-tier breakdown if tracking is active
        qstats = getattr(self, 'quiz_stats', {}) or {}
        # Per-run SUBJECT MASTERY: a cleared (subject, tier) auto-succeeds, so
        # mark it MASTERED here instead of a hit ratio -- the badge the player
        # earns for clearing a whole tier.
        mastered = (self.quiz_engine.mastered_tiers()
                    if getattr(self, 'quiz_engine', None) else set())
        if qstats:
            quiz_rows.append("")
            for subj in sorted(qstats.keys()):
                d = qstats[subj] or {}
                r = int(d.get('correct', 0))
                w = int(d.get('wrong', 0))
                t = r + w
                a = (r / t * 100) if t else 0.0
                tier_bits = []
                for ti in range(1, 6):
                    if (subj, ti) in mastered:
                        tier_bits.append(f"T{ti} MASTERED")
                        continue
                    tr = int(d.get(f't{ti}c', 0))
                    tw = int(d.get(f't{ti}w', 0))
                    if tr + tw > 0:
                        tier_bits.append(f"T{ti} {tr}/{tr+tw}")
                tail = f"   {' '.join(tier_bits)}" if tier_bits else ''
                quiz_rows.append(f"  {subj:11s}  {r} / {w}   ({a:.0f}%){tail}")
        sections.append(("QUIZ PERFORMANCE", quiz_rows))

        # --- Identification ---
        known_ids = getattr(p, 'known_item_ids', set()) or set()
        total_ids = int(getattr(p, 'total_identifies', 0) or 0)
        mantle = bool(getattr(p, 'philosophers_mantle', False))
        id_rows = [
            f"  Total identifies performed: {total_ids}",
            f"  Item types learned:          {len(known_ids)}",
        ]
        if mantle:
            id_rows.append("  Mantle of the Philosopher: granted")
        sections.append(("IDENTIFICATION", id_rows))

        # --- Bestiary ---
        seen = getattr(p, 'known_monster_ids', set()) or set()
        studied = getattr(p, 'lore_known_monster_ids', set()) or set()
        sections.append(("BESTIARY", [
            f"  Monsters encountered:  {len(seen)}",
            f"  Monsters studied:       {len(studied)}",
        ]))

        # --- Faith + Karma ---
        boons = int(getattr(p, 'prayer_boon_count', 0) or 0)
        karma = int(getattr(self, 'karma', 0) or 0)
        sections.append(("FAITH & KARMA", [
            f"  Prayer boons received: {boons}",
            f"  Karma:                  {karma:+d}",
        ]))

        # --- Spells & magic ---
        spells = getattr(p, 'known_spells', {}) or {}
        hack_count = int(getattr(p, 'hack_reality_count', 0) or 0)
        magic_rows = [
            f"  Spells learned: {len(spells)}",
        ]
        if hack_count > 0:
            magic_rows.append(f"  Reality hacks claimed: {hack_count}")
        sections.append(("MAGIC", magic_rows))

        # --- Journey ---
        deepest = int(getattr(p, 'deepest_floor_reached',
                              getattr(self, 'dungeon_level', 1)) or 1)
        current = int(getattr(self, 'dungeon_level', 1) or 1)
        sections.append(("JOURNEY", [
            f"  Current floor:         {current}",
            f"  Deepest floor reached: {deepest}",
        ]))

        # --- Quirks (counts only — names of unlocked quirks could spoil) ---
        unlocked = getattr(p, 'unlocked_quirks', set()) or set()
        sections.append(("QUIRKS", [
            f"  Unlocked: {len(unlocked)}",
        ]))

        return sections

    def _draw_wand_menu(self):
        entries = []
        for i, item in enumerate(self.wand_menu_items):
            charge_color = (
                FP.SUCCESS_TEXT if item.charges > item.max_charges // 2
                else FP.WARNING_TEXT if item.charges > 0
                else FP.DANGER_TEXT_LIGHT
            )
            charge_text = f"charges: {item.charges}/{item.max_charges}"
            if item.identified or self.player.knows_item_type(item):
                charge_text += f" | effect: {item.effect.replace('_', ' ')}"
            entries.append({
                'name': self._display_name(item),
                'detail': charge_text,
                'key': self._menu_letter(i),
                'icon': item,
                'detail_color': charge_color,
                'badge': 'SCIENCE',
                'badge_color': FP.CYAN_ACCENT,
            })
        selected = self._menu_clamp_selection('_wand_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="ZAP WAND",
            entries=entries,
            selected=selected,
            subtitle="Nearest visible monster: auto-targeted",
            hint="Up/Down: move   Enter or a-z: zap   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
        )
        return
        entries = []
        for i, item in enumerate(self.wand_menu_items[:26]):
            charge_color = (
                FP.SUCCESS_TEXT if item.charges > item.max_charges // 2
                else FP.WARNING_TEXT if item.charges > 0
                else FP.DANGER_TEXT_LIGHT
            )
            charge_text = f"charges: {item.charges}/{item.max_charges}"
            if item.identified or self.player.knows_item_type(item):
                charge_text += f"  |  effect: {item.effect.replace('_', ' ')}"
            entries.append({
                'name': self._display_name(item),
                'detail': charge_text,
                'key': self._LETTERS[i],
                'icon': item,
                'detail_color': charge_color,
            })
        draw_menu(
            self.screen,
            title="ZAP WAND",
            entries=entries,
            scroll=getattr(self, '_wand_scroll', 0),
            subtitle="Nearest visible monster: auto-targeted",
            hint="a-z: select  |  ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_spell_menu(self):
        entries = []
        for i, spell_id in enumerate(self.spell_menu_items):
            spell = LEARNABLE_SPELLS.get(spell_id, {})
            mp_cost = spell.get('mp_cost', '?')
            try:
                can_cast = self.player.mp >= int(mp_cost)
            except (TypeError, ValueError):
                can_cast = True
            tier = int(spell.get('quiz_tier', 1) or 1)
            tier_color = [
                (180, 180, 180), (100, 200, 255), (255, 180, 80),
                (200, 80, 255), (255, 100, 100),
            ][min(max(tier - 1, 0), 4)]

            class _SpellIcon:
                def __init__(self2, sid, tc):
                    self2.id = sid
                    self2.color = list(tc)
                    self2.symbol = '*'

            spellbook_id = f"spellbook_{spell_id.replace('_spell', '')}"
            entries.append({
                'name': spell.get('name', '?'),
                'detail': f"tier {tier} | {mp_cost} MP | {spell.get('desc', '')}",
                'key': self._menu_letter(i),
                'icon': _SpellIcon(spellbook_id, tier_color),
                'name_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
                'detail_color': tier_color,
                'badge': f"{mp_cost} MP",
                'badge_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
            })
        selected = self._menu_clamp_selection('_spell_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="CAST SPELL",
            entries=entries,
            selected=selected,
            subtitle=f"MP: {self.player.mp}/{self.player.max_mp}",
            hint="Up/Down: move   Enter or a-z: cast   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
        )
        return
        entries = []
        for i, spell_id in enumerate(self.spell_menu_items[:26]):
            spell = LEARNABLE_SPELLS.get(spell_id, {})
            mp_cost = spell.get('mp_cost', '?')
            can_cast = self.player.mp >= int(mp_cost)
            tier = spell.get('quiz_tier', 1)
            tier_color = [(180,180,180),(100,200,255),(255,180,80),(200,80,255),(255,100,100)][min(tier-1,4)]
            # Build a small proxy object for the icon callback
            book_id = spell_id.replace('_spell', '')
            spellbook_id = f"spellbook_{book_id}"
            # Create a lightweight namespace so _draw_menu_icon can find .id
            class _SpellIcon:
                def __init__(self2, sid, tc):
                    self2.id = sid
                    self2.color = list(tc)
                    self2.symbol = '*'
            icon_obj = _SpellIcon(spellbook_id, tier_color)
            entries.append({
                'name': spell.get('name', '?'),
                'detail': f"tier {tier}  |  {mp_cost} MP  |  {spell.get('desc','')}",
                'key': self._LETTERS[i],
                'icon': icon_obj,
                'name_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
                'detail_color': tier_color,
                'badge': f"{mp_cost} MP",
                'badge_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
            })
        draw_menu(
            self.screen,
            title="CAST SPELL",
            entries=entries,
            scroll=getattr(self, '_spell_scroll', 0),
            subtitle=f"MP: {self.player.mp}/{self.player.max_mp}",
            hint="a-z: select  |  ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
            max_width=820,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_prayer_menu(self):
        """9 named prayers. Show lore description only (player extrapolates
        intent). Greyed-out entries are gate-failed or karma-refused; the
        reason is shown in italics on the detail line."""
        entries = []
        items = getattr(self, '_prayer_menu_items', [])
        for i, entry in enumerate(items):
            avail = entry['available']
            detail = entry.get('lore', '')
            if not avail and entry.get('gate_reason'):
                detail = f"{entry['gate_reason']} - {detail}"

            class _PrayerIcon:
                def __init__(self2, color):
                    self2.id = 'prayer_icon'
                    self2.color = list(color)
                    self2.symbol = '+'

            icon = _PrayerIcon((220, 220, 180) if avail else FP.PARCHMENT_DARK)
            entries.append({
                'name': entry['name'],
                'detail': detail,
                'key': self._menu_letter(i),
                'icon': icon,
                'name_color': FP.BODY_TEXT if avail else FP.WARNING_TEXT,
                'detail_color': FP.BODY_TEXT if avail else FP.FADED_TEXT,
                'badge': 'READY' if avail else 'LOCKED',
                'badge_color': FP.SUCCESS_TEXT if avail else FP.WARNING_TEXT,
            })
        karma = getattr(self, 'karma', 0)
        selected = self._menu_clamp_selection('_prayer_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="PRAYER",
            entries=entries,
            selected=selected,
            subtitle=f"Karma: {karma:+d} | Theology quiz, escalator chain (max 8)",
            hint="Up/Down: move   Enter or a-z: pray   ESC: cancel",
            border_color=FP.GOLD,
        )
        return
        entries = []
        items = getattr(self, '_prayer_menu_items', [])
        for i, entry in enumerate(items[:26]):
            avail = entry['available']
            name_color = FP.BODY_TEXT if avail else FP.WARNING_TEXT
            detail = entry['lore']
            if not avail and entry.get('gate_reason'):
                detail = f"{entry['gate_reason']}  —  {entry['lore']}"
            # Small icon: cross / chalice
            class _PrayerIcon:
                def __init__(self2, color):
                    self2.id = 'prayer_icon'
                    self2.color = list(color)
                    self2.symbol = '+'
            icon = _PrayerIcon((220, 220, 180) if avail else FP.PARCHMENT_DARK)
            entries.append({
                'name': entry['name'],
                'detail': detail,
                'key': self._LETTERS[i],
                'icon': icon,
                'name_color': name_color,
                'detail_color': FP.BODY_TEXT if avail else FP.FADED_TEXT,
            })
        karma = getattr(self, 'karma', 0)
        subtitle = f"Karma: {karma:+d}  |  Theology quiz, escalator chain (max 8)"
        draw_menu(
            self.screen,
            title="PRAYER",
            entries=entries,
            scroll=getattr(self, '_prayer_scroll', 0),
            subtitle=subtitle,
            hint="a-h: select  |  ESC: cancel",
            border_color=FP.GOLD,
            max_width=820,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
            wrap_detail=True,  # prayer lore + gate_reason can run long;
                               # wrap across multiple lines instead of
                               # truncating with "..."
        )

    def _draw_scroll_menu(self):
        tab_items = self._get_scroll_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            is_book = isinstance(item, Spellbook)
            if is_book:
                known = item.spell_id in self.player.known_spells
                if known:
                    detail_text = f"[KNOWN] {item.spell_name}"
                elif item.identified or self.player.knows_item_type(item):
                    detail_text = f"teaches: {item.spell_name}  {item.mp_cost} MP"
                else:
                    detail_text = "spellbook"
            else:
                if item.identified or self.player.knows_item_type(item):
                    detail_text = f"effect: {item.effect.replace('_', ' ')}"
                else:
                    detail_text = "unknown effect"
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._menu_letter(i),
                'icon': item,
                'badge': 'KNOWN' if is_book and item.spell_id in self.player.known_spells else '',
                'badge_color': FP.SUCCESS_TEXT,
                'details': self._menu_item_detail_lines(
                    item,
                    "Read this spellbook or scroll. A grammar quiz may be required."),
            })

        _scroll_counts = [sum(1 for it in self.scroll_menu_items if filt(it))
                          for _, filt in self._SCROLL_TABS]
        selected = self._menu_clamp_selection('_scroll_sel', len(tab_items))
        context = self._menu_base_context([
            ("READING", FP.GOLD_BRIGHT, self.font_sm),
            ("Scrolls and spellbooks use grammar questions.", FP.BODY_TEXT, self.font_sm),
            ("Unknown writings show their unidentified appearance until studied.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="READ",
            entries=entries,
            selected=selected,
            context_lines=context,
            tabs=self._SCROLL_TABS,
            active_tab=self._scroll_tab,
            tab_counts=_scroll_counts,
            hint="Left/Right: tab   Up/Down: move   Enter or a-z: read   ESC: cancel",
            border_color=FP.GOLD,
            scroll_attr='_scroll_scroll',
        )

    def _draw_identify_menu(self):
        entries = []
        from items import item_id_tier
        for i, (item, is_g, is_c) in enumerate(self.identify_menu_items):
            tier = item_id_tier(item)
            if isinstance(item, Corpse):
                detail_text = f"Corpse lore | ID tier {tier}"
            else:
                type_label = item.item_class.replace('_', ' ').title()
                detail_text = f"{type_label} | ID tier {tier}"
            source = "GROUND" if is_g else "PACK"
            if is_c:
                source = "CORPSE"
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._menu_letter(i),
                'icon': item,
                'name_color': FP.GOLD_PALE if is_g else FP.BODY_TEXT,
                'badge': source,
                'badge_color': FP.WARNING_TEXT if is_g else FP.GOLD_BRIGHT,
                'details': self._menu_item_detail_lines(
                    item,
                    "Reveal this item directly."
                    if getattr(self, '_scroll_identify_pending', False)
                    else "Answer ONE philosophy question at the item's tier."),
            })

        selected = self._menu_clamp_selection('_identify_sel', len(entries))
        has_shard = any(getattr(i, 'id', '') == 'philosophers_shard'
                        for i in self.player.inventory)
        context = self._menu_base_context([
            ("IDENTIFICATION", FP.GOLD_BRIGHT, self.font_sm),
            (f"Shard: {'carried' if has_shard else 'passive or override'}", FP.BODY_TEXT, self.font_sm),
            (f"Targets: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("One question. Right: fully identified. Wrong: the Shard stuns you.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="IDENTIFY ITEM",
            entries=entries,
            selected=selected,
            context_lines=context,
            hint="Up/Down: move   Enter or a-z: select   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
            scroll_attr='_identify_scroll',
        )

    def _draw_cook_menu(self):
        tab_items = self._get_cook_tab_items()
        is_compound = self._COOK_TABS[self._cook_tab][1] == 'compound'
        entries = []
        if is_compound:
            from food_system import _raw_ingredients as _ri
            from collections import Counter
            ingredients = _ri()
            for i, recipe in enumerate(tab_items):
                counts = Counter(recipe.get('ingredients', []))
                ing_list = ', '.join(
                    f"{ingredients.get(iid, {}).get('name', iid)} x{n}" if n > 1
                    else ingredients.get(iid, {}).get('name', iid)
                    for iid, n in counts.items()
                )
                recipe_sprite_id = f"recipe_{recipe.get('id', '')}"
                first_ing = recipe.get('ingredients', [''])[0] if recipe.get('ingredients') else ''
                class _RecipeIcon:
                    def __init__(self2, rid, fing):
                        self2.id = rid
                        self2._fallback = fing
                        self2.color = [110, 220, 100]
                        self2.symbol = '*'
                icon_obj = _RecipeIcon(recipe_sprite_id, first_ing)
                name = recipe.get('name', 'recipe')
                entries.append({
                    'name': name[:1].upper() + name[1:],
                    'detail': f"Needs: {ing_list}",
                    'key': self._menu_letter(i),
                    'icon': icon_obj,
                    'name_color': FP.GOLD_BRIGHT if recipe.get('recipe_class') == 'trophy' else FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
                    'badge': 'TROPHY' if recipe.get('recipe_class') == 'trophy' else '',
                    'badge_color': FP.GOLD_BRIGHT,
                    'details': self._menu_recipe_detail_lines(recipe),
                })
        else:
            from food_system import _find_recipe_for_ingredient
            for i, item in enumerate(tab_items):
                recipe = _find_recipe_for_ingredient(item) or {}
                dish_name = recipe.get('name', f"{item.name} Surprise")
                entries.append({
                    'name': dish_name[:1].upper() + dish_name[1:],
                    'detail': f"Consumes: {item.name}",
                    'key': self._menu_letter(i),
                    'icon': item,
                    'name_color': FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
                    'details': self._menu_recipe_detail_lines(recipe) if recipe
                    else self._menu_item_detail_lines(item, "Cook this ingredient."),
                })

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        _cook_counts = [len(self.cook_menu_items) if k == 'single' else len(self.cook_compound_recipes)
                        for _, k in self._COOK_TABS]
        selected = self._menu_clamp_selection('_cook_sel', len(entries))
        context = self._menu_base_context([
            ("COOKING", FP.GOLD_BRIGHT, self.font_sm),
            (f"SP {sp}/{self.player.max_sp}", sp_color, self.font_sm),
            (f"Recipes available: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("Cooking uses an escalator-chain quiz. Higher chains improve the meal.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="COOK",
            entries=entries,
            selected=selected,
            context_lines=context,
            tabs=self._COOK_TABS,
            active_tab=self._cook_tab,
            tab_counts=_cook_counts,
            hint="Up/Down: move   Enter or a-z: cook   ESC: cancel",
            border_color=FP.SUCCESS_TEXT,
            scroll_attr='_cook_scroll',
        )
        return
        bw = min(800, layout.GAME_W - 40)
        ICO = self.MENU_ICON_SIZE
        TEXT_X = 70 + ICO + 8
        max_detail_w = bw - TEXT_X - 20

        def _cap(s):
            return s[:1].upper() + s[1:] if s else s

        def _format_tier_preview(recipe) -> str:
            """One-line outcome preview per the 2026-05-31 redesign.
            Shows what each tier delivers so the player knows the stakes."""
            outcomes = recipe.get('tier_outcomes', {})
            if not outcomes:
                return ""
            parts = []
            for t in range(1, 6):
                o = outcomes.get(str(t), {})
                if not o:
                    continue
                bits = []
                if o.get('sp'): bits.append(f"+{o['sp']}SP")
                if o.get('hp'): bits.append(f"+{o['hp']}HP")
                if o.get('max_hp_bonus'): bits.append(f"+{o['max_hp_bonus']}maxHP")
                if o.get('stat_grant'):
                    s = recipe.get('stat_grant') or recipe.get('stat_grant_default') or '?'
                    bits.append(f"+{o['stat_grant']}{s}")
                if o.get('temp_power'):
                    # Name the actual buff + its duration, not a bare "temp".
                    tp = (recipe.get('temp_power') or '').replace('_', ' ').strip()
                    dur = recipe.get('temp_duration')
                    label = tp or 'temp buff'
                    bits.append(f"{label} {dur}t" if dur else label)
                if o.get('permanent_power'):
                    bits.append('PERM')
                if bits:
                    parts.append(f"T{t}: {'/'.join(bits)}")
            return " | ".join(parts)

        entries = []
        if is_compound:
            from food_system import _raw_ingredients as _ri
            _ings = _ri()
            def _ing_name(iid): return _ings.get(iid, {}).get('name', iid)
            from collections import Counter as _Counter
            for i, recipe in enumerate(tab_items[:26]):
                # Collapse repeated ingredient ids into "name xN" (a recipe that
                # needs 3 assorted parts should read "Monster Parts x3", not list
                # the same ingredient three times). Counter preserves order (3.7+).
                _ing_counts = _Counter(recipe.get('ingredients', []))
                ing_list = ', '.join(
                    f"{_ing_name(iid)} x{n}" if n > 1 else _ing_name(iid)
                    for iid, n in _ing_counts.items()
                )
                tier_preview = _format_tier_preview(recipe)
                detail = f"Needs: {ing_list}"
                if tier_preview:
                    detail += f"   |   {tier_preview}"
                detail_lines = self._wrap_text(detail, self.font_sm, max_detail_w)
                recipe_sprite_id = f"recipe_{recipe.get('id', '')}"
                first_ing = recipe.get('ingredients', [''])[0] if recipe.get('ingredients') else ''
                class _RecipeIcon:
                    def __init__(self2, rid, fing):
                        self2.id = rid
                        self2._fallback = fing
                        self2.color = [110, 220, 100]
                        self2.symbol = '*'
                icon_obj = _RecipeIcon(recipe_sprite_id, first_ing)
                # Trophy recipes get distinct color
                _name_col = FP.GOLD_BRIGHT if recipe.get('recipe_class') == 'trophy' else FP.GOLD_PALE
                entries.append({
                    'name': _cap(recipe['name']),
                    'detail_lines': detail_lines,
                    'key': self._LETTERS[i],
                    'icon': icon_obj,
                    'name_color': _name_col,
                    'detail_color': FP.BODY_TEXT,
                    'selected': i == getattr(self, '_cook_sel', 0),
                })
        else:
            # Single tab: each ingredient resolves to its canonical recipe via
            # food_system._find_recipe_for_ingredient. Per redesign, ALL cooks
            # go through a recipe — the menu shows the recipe's tier preview.
            from food_system import _find_recipe_for_ingredient
            for i, item in enumerate(tab_items[:26]):
                recipe = _find_recipe_for_ingredient(item) or {}
                dish_name = _cap(recipe.get('name', f"{item.name} Surprise"))
                tier_preview = _format_tier_preview(recipe)
                # Use the bare item name (no inventory count — that it's listed at
                # all means you have it) and WRAP the detail like the compound tab,
                # so the tier bonuses don't truncate off the right edge.
                detail = f"Consumes: {item.name}"
                if tier_preview:
                    detail += f"   |   {tier_preview}"
                detail_lines = self._wrap_text(detail, self.font_sm, max_detail_w)
                entries.append({
                    'name': dish_name,
                    'detail_lines': detail_lines,
                    'key': self._LETTERS[i],
                    'icon': item,
                    'name_color': FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
                    'selected': i == getattr(self, '_cook_sel', 0),
                })

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        _cook_counts = [len(self.cook_menu_items) if k == 'single' else len(self.cook_compound_recipes)
                        for _, k in self._COOK_TABS]

        def _cook_icon(s, item, x, y):
            # For compound recipe proxies, try recipe sprite then first ingredient
            fb = getattr(item, '_fallback', None)
            sprite = self._get_menu_sprite(item.id)
            if sprite is None and fb:
                sprite = self._get_menu_sprite(fb)
            if sprite is not None:
                self.screen.blit(sprite, (x, y))
            else:
                self._draw_menu_icon(item, x, y)

        draw_menu(
            self.screen,
            title="COOK",
            entries=entries,
            scroll=getattr(self, '_cook_scroll', 0),
            subtitle=f"SP: {sp}/{self.player.max_sp}",
            subtitle_color=sp_color,
            tabs=self._COOK_TABS,
            active_tab=self._cook_tab,
            tab_counts=_cook_counts,
            hint="Up/Down: move  |  Enter or a-z: cook  |  ESC: cancel",
            border_color=FP.SUCCESS_TEXT,
            max_width=800,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=_cook_icon,
        )

    def _draw_ascension_menu(self):
        """Boss Class Ascension picker (opened by cooking a boss trophy).

        Lists the offered class nodes for the player's current tier. Each row
        shows the node name + a stat/perk/ability summary + flavor, wrapped to
        the panel width. Text rows (no icons), modelled on the drop menu."""
        import class_system as cs
        choices = getattr(self, '_ascension_choices', []) or []
        classes = cs.load_classes()
        draw_overlay(self.screen, 195)
        bw = min(1240, layout.GAME_W - 32)
        bh = min(680, layout.WINDOW_H - 32)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="ASCENSION",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT,
                        accent=FP.GOLD_BRIGHT)

        path_len = len(cs.class_path(self.player))
        _tier_names = {0: 'Calling', 1: 'Specialization', 2: 'Mastery', 3: 'Capstone'}
        subtitle = f"Permanent {_tier_names.get(path_len, 'path')} choice. ESC defers."
        self._menu_draw_line(subtitle, self.font_sm, FP.WARNING_TEXT,
                             pygame.Rect(bx + 24, by + 58, bw - 48, 24))

        selected = self._menu_clamp_selection('_ascension_sel', len(choices))
        card_count = max(1, len(choices))
        gap = 16
        usable_w = bw - 80
        cols = min(4, card_count)
        card_w = (usable_w - gap * (cols - 1)) // cols
        card_h = bh - 190
        card_y = by + 104
        start_x = bx + (bw - (card_w * cols + gap * (cols - 1))) // 2
        for i, nid in enumerate(choices[:cols]):
            node = classes.get(nid, {})
            rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
            is_sel = i == selected
            pygame.draw.rect(self.screen, (30, 38, 74) if is_sel else FP.MIDNIGHT,
                             rect, border_radius=7)
            pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if is_sel else FP.GOLD_DARK,
                             rect, 2 if is_sel else 1, border_radius=7)
            key_rect = pygame.Rect(rect.x + 12, rect.y + 12, 32, 28)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD, key_rect, 1, border_radius=4)
            key = self._menu_letter(i)
            if key:
                ks = self.font_sm.render(key, True, FP.GOLD_BRIGHT)
                self.screen.blit(ks, (key_rect.centerx - ks.get_width() // 2,
                                      key_rect.centery - ks.get_height() // 2))
            name = node.get('name', nid)
            self._menu_draw_wrapped(name, self.font_md, FP.GOLD_BRIGHT,
                                    pygame.Rect(rect.x + 52, rect.y + 11,
                                                rect.w - 64, 58), max_lines=2)
            y = rect.y + 76
            summary = self._ascension_node_summary(node)
            if summary:
                y += self._menu_draw_wrapped(summary, self.font_sm, FP.CYAN_ACCENT,
                                             pygame.Rect(rect.x + 16, y, rect.w - 32,
                                                         rect.bottom - y - 20),
                                             max_lines=3) + 10
            ability = node.get('ability') or {}
            if ability.get('name'):
                y += self._menu_draw_wrapped(
                    f"Ability: {ability.get('name')} - {ability.get('desc', '')}",
                    self.font_sm, FP.SUCCESS_TEXT,
                    pygame.Rect(rect.x + 16, y, rect.w - 32, rect.bottom - y - 20),
                    max_lines=4) + 10
            flavor = node.get('flavor', '')
            if flavor:
                self._menu_draw_wrapped(flavor, self.font_sm, FP.BODY_TEXT,
                                        pygame.Rect(rect.x + 16, y, rect.w - 32,
                                                    rect.bottom - y - 20),
                                        max_lines=8)

        draw_divider(self.screen, bx + 20, by + bh - 40, bw - 40)
        hint = "Left/Right or Up/Down: choose   Enter or a-z: accept   ESC: defer"
        hs = self.font_sm.render(hint, True, FP.HINT_TEXT)
        self.screen.blit(hs, (bx + (bw - hs.get_width()) // 2, by + bh - 30))
        return
        bw = min(760, layout.GAME_W - 40)
        max_detail_w = bw - 90
        entries = []
        for i, nid in enumerate(choices[:26]):
            node = classes.get(nid, {})
            summary = self._ascension_node_summary(node)
            flavor = node.get('flavor', '')
            detail = summary
            if flavor:
                detail = f"{summary}\n{flavor}" if summary else flavor
            # Pre-wrap each logical line so flavor sits under the stat summary.
            detail_lines = []
            for chunk in detail.split('\n'):
                detail_lines.extend(self._wrap_text(chunk, self.font_sm, max_detail_w))
            entries.append({
                'name': node.get('name', nid),
                'detail_lines': detail_lines,
                'key': self._LETTERS[i],
                'name_color': FP.GOLD_BRIGHT,
                'detail_color': FP.BODY_TEXT,
                'row_style': 'text',
            })
        path_len = len(cs.class_path(self.player))
        _tier_names = {0: 'Calling', 1: 'Specialization', 2: 'Mastery', 3: 'Capstone'}
        subtitle = f"Choose your {_tier_names.get(path_len, 'path')} — the boss meal IS the choice."
        draw_menu(
            self.screen,
            title="ASCENSION",
            entries=entries,
            scroll=getattr(self, '_ascension_scroll', 0),
            subtitle=subtitle,
            subtitle_color=FP.GOLD_PALE,
            hint="a-z: answer the calling  |  ESC: defer",
            border_color=FP.GOLD_BRIGHT,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            row_style='text',
        )

    def _draw_drop_menu(self):
        tab_items = self._get_drop_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            if isinstance(item, self._GoldDropEntry):
                dname = f"Gold ({getattr(self, 'player_gold', 0)} coins)"
                name_col = FP.GOLD_BRIGHT
                detail = "amount prompt"
                details = self._menu_item_detail_lines(item, "Type how much gold to drop.")
            else:
                dname = self._display_name(item)
                name_col = FP.PARCHMENT_LIGHT
                count = getattr(item, 'count', 1)
                detail = self._menu_item_summary(item)
                if count > 1:
                    detail = f"x{count} | {detail}"
                details = self._menu_item_detail_lines(
                    item,
                    "Drop this item on the current tile. Stacks open a quantity prompt.")
            entries.append({
                'name': dname,
                'detail': detail,
                'key': self._menu_letter(i),
                'icon': None if isinstance(item, self._GoldDropEntry) else item,
                'name_color': name_col,
                'badge': 'GOLD' if isinstance(item, self._GoldDropEntry) else '',
                'badge_color': FP.GOLD_BRIGHT,
                'details': details,
            })

        _drop_counts = [len(self.drop_menu_items) if filt is None
                        else sum(1 for it in self.drop_menu_items if filt(it))
                        for _, filt in self._DROP_TABS]
        selected = self._menu_clamp_selection('_drop_sel', len(entries))
        context = self._menu_base_context([
            ("DROP CONTEXT", FP.GOLD_BRIGHT, self.font_sm),
            (f"Current tile: {self._menu_tile_label()}", FP.BODY_TEXT, self.font_sm),
            ("Altars, fountains, forges, and quest tiles may react to what you drop.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="DROP ITEM",
            entries=entries,
            selected=selected,
            context_lines=context,
            tabs=self._DROP_TABS,
            active_tab=self._menu_tab,
            tab_counts=_drop_counts,
            hint="Left/Right: tab   Up/Down: move   Enter or a-z: drop   ESC: cancel",
            border_color=FP.GOLD,
            scroll_attr='_drop_scroll',
        )
        return
        entries = []
        for i, item in enumerate(tab_items[:26]):
            if isinstance(item, self._GoldDropEntry):
                dname = f"Gold  ({getattr(self, 'player_gold', 0)} coins)"
                name_col = FP.GOLD_BRIGHT
            else:
                dname = self._display_name(item)
                name_col = FP.PARCHMENT_LIGHT
            entries.append({
                'name': dname,
                'key': self._LETTERS[i],
                'name_color': name_col,
                'row_style': 'text',
            })

        _drop_counts = [len(self.drop_menu_items) if filt is None
                        else sum(1 for it in self.drop_menu_items if filt(it))
                        for _, filt in self._DROP_TABS]
        draw_menu(
            self.screen,
            title="DROP ITEM",
            entries=entries,
            scroll=getattr(self, '_drop_scroll', 0),
            tabs=self._DROP_TABS,
            active_tab=self._menu_tab,
            tab_counts=_drop_counts,
            hint="Left/Right: tab  |  Up/Down: scroll  |  a-z: drop  |  ESC: cancel",
            max_width=600,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            row_style='text',
        )

    def _draw_eat_menu(self):
        tab_items = self._get_eat_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            if isinstance(item, Food):
                parts = [f"+{item.sp_restore} SP"]
                if item.hp_restore:
                    parts.append(f"+{item.hp_restore} HP")
                detail_text = " | ".join(parts)
                badge = 'FOOD'
                badge_color = FP.SUCCESS_TEXT
            else:
                detail_text = "raw ingredient - cook for better results"
                badge = 'RAW'
                badge_color = FP.WARNING_TEXT
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._menu_letter(i),
                'icon': item,
                'badge': badge,
                'badge_color': badge_color,
            })

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        _eat_counts = [sum(1 for it in self.eat_menu_items if filt(it))
                       for _, filt in self._EAT_TABS]
        selected = self._menu_clamp_selection('_eat_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="EAT",
            entries=entries,
            selected=selected,
            subtitle=f"SP: {sp}/{self.player.max_sp}",
            hint="Up/Down: move   Enter or a-z: eat   ESC: cancel",
            border_color=sp_color,
            tabs=self._EAT_TABS,
            active_tab=self._eat_tab,
            tab_counts=_eat_counts,
        )
        return
        tab_items = self._get_eat_tab_items()
        entries = []
        for i, item in enumerate(tab_items[:26]):
            if isinstance(item, Food):
                parts = [f"+{item.sp_restore} SP"]
                if item.hp_restore:
                    parts.append(f"+{item.hp_restore} HP")
                detail_text = "  ".join(parts)
            else:
                detail_text = "raw ingredient (cook for better results)"
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._LETTERS[i],
                'icon': item,
                'selected': i == getattr(self, '_eat_sel', 0),
            })

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        _eat_counts = [sum(1 for it in self.eat_menu_items if filt(it))
                       for _, filt in self._EAT_TABS]
        draw_menu(
            self.screen,
            title="EAT",
            entries=entries,
            scroll=getattr(self, '_eat_scroll', 0),
            subtitle=f"SP: {sp}/{self.player.max_sp}",
            subtitle_color=sp_color,
            tabs=self._EAT_TABS,
            active_tab=self._eat_tab,
            tab_counts=_eat_counts,
            hint="Up/Down: move  |  Enter or a-z: eat  |  ESC: cancel",
            border_color=FP.SUCCESS_TEXT,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_quaff_menu(self):
        items = self.quaff_menu_items
        entries = []
        for i, item in enumerate(items):
            known = item.identified or self.player.knows_item_type(item)
            if known:
                eff = item.effect.replace('_', ' ')
                dur = f" ({item.duration} turns)" if item.duration else ""
                is_good = item.effect in self._BENEFICIAL_EFFECTS
                detail_text = f"{eff}{dur}"
                detail_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT_LIGHT
                badge = 'BOON' if is_good else 'RISK'
                badge_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT_LIGHT
            else:
                detail_text = "unidentified - effect hidden"
                detail_col = FP.FADED_TEXT
                badge = 'UNKNOWN'
                badge_col = FP.WARNING_TEXT
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._menu_letter(i),
                'icon': item,
                'detail_color': detail_col,
                'badge': badge,
                'badge_color': badge_col,
            })
        selected = self._menu_clamp_selection('_quaff_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="QUAFF POTION",
            entries=entries,
            selected=selected,
            subtitle="Unknown potions keep their effect hidden until identified",
            hint="Up/Down: move   Enter or a-z: quaff   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
        )
        return
        items = self.quaff_menu_items
        entries = []
        for i, item in enumerate(items[:26]):
            known = item.identified or self.player.knows_item_type(item)
            if known:
                eff = item.effect.replace('_', ' ')
                dur = f"  ({item.duration} turns)" if item.duration else ""
                is_good = item.effect in self._BENEFICIAL_EFFECTS
                detail_text = f"{'*' if is_good else 'X'} {eff}{dur}"
                detail_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT_LIGHT
            else:
                detail_text = "effect unknown -- identify to reveal"
                detail_col = FP.FADED_TEXT
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._LETTERS[i],
                'icon': item,
                'detail_color': detail_col,
            })
        draw_menu(
            self.screen,
            title="QUAFF POTION",
            entries=entries,
            scroll=getattr(self, '_quaff_scroll', 0),
            subtitle="Unknown potions may harm -- identify first with  I",
            subtitle_color=(200, 150, 80),
            hint="a-z: quaff  |  ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_throw_menu(self):
        tab_items = self._get_throw_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            if isinstance(item, Weapon):
                dmg = self._get_weapon_throw_damage(item)
                brk = int(self._get_weapon_break_chance(item) * 100)
                detail_text = f"{dmg} dmg | {brk}% break"
                badge = 'WEAPON'
                badge_color = FP.WARNING_TEXT
            elif isinstance(item, Potion):
                known = item.identified or self.player.knows_item_type(item)
                if known:
                    eff = item.effect.replace('_', ' ')
                    dur = f" ({item.duration} turns)" if item.duration else ""
                    detail_text = f"{eff}{dur}"
                else:
                    detail_text = "unidentified potion - effect hidden"
                badge = 'POTION'
                badge_color = FP.ARCANE_BRIGHT
            else:
                detail_text = self._menu_item_summary(item)
                badge = 'ITEM'
                badge_color = FP.FADED_TEXT
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._menu_letter(i),
                'icon': item,
                'badge': badge,
                'badge_color': badge_color,
            })

        _throw_counts = [sum(1 for it in self.throw_menu_items if filt(it))
                         for _, filt in self._THROW_TABS]
        selected = self._menu_clamp_selection('_throw_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="THROW",
            entries=entries,
            selected=selected,
            subtitle="Choose item, then aim on the map",
            hint="Left/Right: tab   Up/Down: move   Enter or a-z: throw   ESC: cancel",
            border_color=FP.WARNING_TEXT,
            tabs=self._THROW_TABS,
            active_tab=self._throw_tab,
            tab_counts=_throw_counts,
        )
        return
        tab_items = self._get_throw_tab_items()
        entries = []
        for i, item in enumerate(tab_items[:26]):
            if isinstance(item, Weapon):
                dmg = self._get_weapon_throw_damage(item)
                brk = int(self._get_weapon_break_chance(item) * 100)
                detail_text = f"{dmg} dmg  |  {brk}% break chance"
            elif isinstance(item, Potion):
                known = item.identified or self.player.knows_item_type(item)
                if known:
                    eff = item.effect.replace('_', ' ')
                    dur = f"  ({item.duration} turns)" if item.duration else ""
                    detail_text = f"{eff}{dur}"
                else:
                    detail_text = "unknown effect"
            else:
                detail_text = ""
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._LETTERS[i],
                'icon': item,
            })

        _throw_counts = [sum(1 for it in self.throw_menu_items if filt(it))
                         for _, filt in self._THROW_TABS]
        draw_menu(
            self.screen,
            title="THROW",
            entries=entries,
            scroll=getattr(self, '_throw_scroll', 0),
            tabs=self._THROW_TABS,
            active_tab=self._throw_tab,
            tab_counts=_throw_counts,
            hint="Left/Right: tab  |  a-z: throw  |  ESC: cancel",
            border_color=FP.WARNING_TEXT,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_power_menu(self):
        powers = getattr(self, '_power_menu_list', [])
        entries = []
        for i, (pid, pdef, uses_rem, cooldown) in enumerate(powers):
            ready = (cooldown == 0) and (pdef.get('uses', 0) == 0 or uses_rem > 0)
            if pdef.get('uses', 0) > 0:
                badge_txt = f"x{uses_rem}" if uses_rem > 0 else "USED"
                badge_col = FP.SUCCESS_TEXT if uses_rem > 0 else FP.DANGER_TEXT_LIGHT
            else:
                badge_txt = "READY" if cooldown == 0 else f"CD {cooldown}"
                badge_col = FP.SUCCESS_TEXT if cooldown == 0 else FP.AMBER_ACCENT
            entries.append({
                'name': pdef.get('label', pid),
                'detail': pdef.get('desc', ''),
                'key': self._menu_letter(i),
                'name_color': FP.BODY_TEXT if ready else FP.FADED_TEXT,
                'key_color': FP.GOLD_BRIGHT if ready else FP.FADED_TEXT,
                'detail_color': FP.BODY_TEXT if ready else FP.FADED_TEXT,
                'badge': badge_txt,
                'badge_color': badge_col,
            })
        selected = self._menu_clamp_selection('_power_sel', len(entries))
        self._draw_fast_picker_variant_b(
            title="ACTIVE POWERS [V]",
            entries=entries,
            selected=selected,
            subtitle="Only acquired powers are shown",
            hint="Up/Down: move   Enter or a-z: use power   ESC: close",
            border_color=FP.ARCANE_BRIGHT,
        )
        return
        powers = getattr(self, '_power_menu_list', [])
        entries = []
        for i, (pid, pdef, uses_rem, cooldown) in enumerate(powers[:26]):
            ready = (cooldown == 0) and (pdef.get('uses', 0) == 0 or uses_rem > 0)
            # Badge
            if pdef.get('uses', 0) > 0:
                badge_txt = f"x{uses_rem} left" if uses_rem > 0 else "USED UP"
                badge_col = FP.SUCCESS_TEXT if uses_rem > 0 else FP.DANGER_TEXT_LIGHT
            else:
                badge_txt = "READY" if cooldown == 0 else f"CD:{cooldown}t"
                badge_col = FP.SUCCESS_TEXT if cooldown == 0 else FP.AMBER_ACCENT
            entries.append({
                'name': pdef.get('label', pid),
                'detail': pdef.get('desc', ''),
                'key': self._LETTERS[i],
                'name_color': FP.BODY_TEXT if ready else FP.FADED_TEXT,
                'key_color': FP.GOLD_BRIGHT if ready else FP.FADED_TEXT,
                'badge': badge_txt,
                'badge_color': badge_col,
                'row_style': 'text',
            })
        draw_menu(
            self.screen,
            title="ACTIVE POWERS  [V]",
            entries=entries,
            scroll=getattr(self, '_power_scroll', 0),
            subtitle="Earned through quirk mastery -- each power has limited uses.",
            subtitle_color=FP.FADED_TEXT,
            hint="a-z: use power  |  ESC: close",
            border_color=FP.ARCANE_BRIGHT,
            max_width=700,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            row_style='text',
        )

    def _draw_qa_warp_popup(self):
        """Titivillus QA warp prompt: type a floor number."""
        buf = getattr(self, '_qa_warp_input', '')
        self._ui_input_card(
            "[QA] WARP TO FLOOR",
            "Enter a floor number (1-100). This debug warp preserves saved "
            "level state and companion following.",
            buf,
            "Enter: warp   |   Backspace: edit   |   Esc: cancel",
            border_color=FP.CYAN_ACCENT,
            title_color=FP.CYAN_ACCENT,
            max_w=640,
        )
        return

        draw_overlay(self.screen, 200)
        bw, bh = 460, 200
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="[QA] WARP TO FLOOR",
                        font=self.font_md, text_color=FP.CYAN_ACCENT)
        sub = "Enter a floor number (1-100):"
        sub_surf = self.font_md.render(sub, True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 56))
        from fantasy_ui import draw_input_box
        draw_input_box(self.screen, (bx + 80, by + 96, bw - 160, 38),
                       buf, self.font_md, border_color=FP.CYAN_ACCENT)
        hint = self.font_sm.render("ENTER to warp  |  ESC to cancel",
                                    True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 24))

    def _draw_pet_menu(self):
        """Pet roster + per-pet action rows. Shift+P opens this menu."""
        items = getattr(self, 'pet_menu_items', [])
        entries = []
        from items import Food, Ingredient, Potion
        for idx, pet in enumerate(items):
            cmd = getattr(pet, 'command', 'return').upper()
            xp_to = pet._xp_to_next() if hasattr(pet, '_xp_to_next') else 0
            specials_avail = pet.available_specials() if hasattr(pet, 'available_specials') else []
            ready = sum(1 for s in specials_avail if pet.special_cooldown(s['id']) == 0)
            food_count = sum(
                1 for i in self.player.inventory if isinstance(i, (Food, Ingredient)))
            potion_count = sum(
                1 for i in self.player.inventory
                if isinstance(i, Potion)
                and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal')
                and getattr(i, 'identified', False))
            details = [
                (pet.name, FP.GOLD_BRIGHT, self.font_md),
                (f"HP {pet.hp}/{pet.max_hp}    Level {pet.level}    XP {pet.xp}/{xp_to}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Command: {cmd}", FP.CYAN_ACCENT, self.font_sm),
                '',
                ("Available actions", FP.GOLD_BRIGHT, self.font_sm),
                (f"F - Feed ({food_count} food items in pack)", FP.BODY_TEXT, self.font_sm),
                ("P - Pet (+5 XP; once per floor)", FP.BODY_TEXT, self.font_sm),
                (f"H - Heal with potion ({potion_count} identified healing potions)",
                 FP.BODY_TEXT, self.font_sm),
                ("R - Recall to Soul Sphere (requires adjacent)", FP.BODY_TEXT, self.font_sm),
                ("C - Cycle command: return, stay, wander", FP.BODY_TEXT, self.font_sm),
                (f"S - Specials ({ready} ready / {len(specials_avail)} unlocked)",
                 FP.BODY_TEXT, self.font_sm),
            ]
            entries.append({
                'name': pet.name,
                'detail': f"HP {pet.hp}/{pet.max_hp} | L{pet.level} | {cmd}",
                'key': self._menu_letter(idx),
                'badge': f"{ready}/{len(specials_avail)}",
                'badge_color': FP.SUCCESS_TEXT if ready else FP.FADED_TEXT,
                'details': details,
            })

        selected = self._menu_clamp_selection('_pet_menu_selected', len(entries))
        context = self._menu_base_context([
            ("COMPANIONS", FP.GOLD_BRIGHT, self.font_sm),
            (f"Active companions: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("Choose a companion with arrows or letters, then use the action keys.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="COMPANIONS",
            entries=entries,
            selected=selected,
            context_lines=context,
            hint="Up/Down: choose pet   a-z: select pet   F/P/H/R/C/S: action   ESC: close",
            border_color=FP.GOLD_BRIGHT,
            scroll_attr='_pet_menu_scroll',
        )
        return
        items = getattr(self, 'pet_menu_items', [])
        sel = getattr(self, '_pet_menu_selected', 0)
        draw_overlay(self.screen, 190)
        bw, bh = min(820, layout.GAME_W - 40), min(560, layout.WINDOW_H - 40)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="COMPANIONS",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)
        y = by + 56
        if not items:
            empty = self.font_md.render(
                "No active companions. Throw a Soul Sphere to summon one.",
                True, FP.BODY_TEXT)
            self.screen.blit(empty, (bx + 30, y))
            # Footer hint even on empty (bug-bash A1: prevented panel from
            # leaving the user with no exit instruction).
            hint = self.font_sm.render("ESC: close", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                     by + bh - 24))
            return
        # Pet roster
        for idx, pet in enumerate(items[:8]):
            tag = self._LETTERS[idx]
            marker = "▶" if idx == sel else " "
            cmd = getattr(pet, 'command', 'return').upper()
            xp_to = pet._xp_to_next() if hasattr(pet, '_xp_to_next') else 0
            line = (f"{marker} {tag}) {pet.name}  HP {pet.hp}/{pet.max_hp}  "
                    f"L{pet.level}  XP {pet.xp}/{xp_to}  [{cmd}]")
            col = FP.GOLD_BRIGHT if idx == sel else FP.BODY_TEXT
            line_surf = self.font_md.render(self._fit_text(line, self.font_md, bw - 50), True, col)
            self.screen.blit(line_surf, (bx + 25, y))
            y += 26
        y += 12
        draw_divider(self.screen, bx + 20, y, bw - 40)
        y += 12
        # Action rows for the selected pet
        if 0 <= sel < len(items):
            pet = items[sel]
            from items import Food, Ingredient, Potion
            food_count = sum(
                1 for i in self.player.inventory if isinstance(i, (Food, Ingredient)))
            potion_count = sum(
                1 for i in self.player.inventory
                if isinstance(i, Potion)
                and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal')
                and getattr(i, 'identified', False))
            specials_avail = pet.available_specials() if hasattr(pet, 'available_specials') else []
            ready = sum(1 for s in specials_avail if pet.special_cooldown(s['id']) == 0)
            cmd_label = {'return': 'RETURN', 'stay': 'STAY', 'wander': 'WANDER'}.get(
                getattr(pet, 'command', 'return'), 'RETURN')
            rows = [
                ("F", f"Feed {pet.name}  ({food_count} food in pack)"),
                ("P", "Pet  (+5 XP; once per floor)"),
                ("H", f"Heal with potion  ({potion_count} healing potions)"),
                ("R", "Recall to Soul Sphere  (requires adjacent)"),
                ("C", f"Command: {cmd_label}  (press to cycle)"),
                ("S", f"Specials  ({ready} ready / {len(specials_avail)} unlocked)"),
            ]
            for key_label, desc in rows:
                key_surf = self.font_md.render(f"[ {key_label} ]", True, FP.GOLD_BRIGHT)
                desc_surf = self.font_md.render(desc, True, FP.BODY_TEXT)
                self.screen.blit(key_surf, (bx + 30, y))
                self.screen.blit(desc_surf, (bx + 90, y))
                y += 28
        hint = self.font_sm.render(
            "a-z: select pet  |  F/P/H/R/C/S: actions  |  ESC: close",
            True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 28))

    def _draw_pet_feed_submenu(self):
        items = getattr(self, 'pet_feed_items', [])
        pet = getattr(self, '_pet_feed_target', None)
        self._draw_pet_sub_picker("FEED A FOOD ITEM", items, pet, attr='sp_restore')

    def _draw_pet_heal_submenu(self):
        items = getattr(self, 'pet_heal_items', [])
        pet = getattr(self, '_pet_heal_target', None)
        self._draw_pet_sub_picker("USE A HEALING POTION", items, pet, attr='effect')

    def _draw_pet_specials_submenu(self):
        items = getattr(self, 'pet_specials_items', [])
        pet = getattr(self, '_pet_specials_target', None)
        entries = []
        for idx, sp in enumerate(items):
            cd = pet.special_cooldown(sp['id']) if pet else 0
            status = "READY" if cd == 0 else f"CD {cd}"
            entries.append({
                'name': sp.get('name', sp.get('id', 'special')),
                'detail': sp.get('desc', ''),
                'key': self._menu_letter(idx),
                'name_color': FP.GOLD_BRIGHT if cd == 0 else FP.FADED_TEXT,
                'detail_color': FP.BODY_TEXT if cd == 0 else FP.FADED_TEXT,
                'badge': status,
                'badge_color': FP.SUCCESS_TEXT if cd == 0 else FP.AMBER_ACCENT,
            })
        selected = self._menu_clamp_selection('_pet_specials_sel', len(entries))
        title = "SPECIAL ATTACKS"
        if pet is not None:
            title = f"{pet.name.upper()} - SPECIAL ATTACKS"
        self._draw_fast_picker_variant_b(
            title=title,
            entries=entries,
            selected=selected,
            subtitle="Choose a special, then target on the map",
            hint="Up/Down: move   Enter or a-z: special   ESC: back",
            border_color=FP.GOLD_BRIGHT,
        )
        return
        items = getattr(self, 'pet_specials_items', [])
        pet = getattr(self, '_pet_specials_target', None)
        draw_overlay(self.screen, 200)
        bw, bh = min(700, layout.GAME_W - 80), 320
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        title = "SPECIAL ATTACKS"
        if pet is not None:
            title = f"{pet.name.upper()} — SPECIAL ATTACKS"
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=title,
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)
        y = by + 54
        if not items:
            msg = "No specials unlocked yet. Evolve this pet to learn them."
            s = self.font_md.render(msg, True, FP.HINT_TEXT)
            self.screen.blit(s, (bx + (bw - s.get_width()) // 2, y))
            hint = self.font_sm.render("ESC: back", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                     by + bh - 24))
            return
        for idx, sp in enumerate(items):
            tag = self._LETTERS[idx]
            cd = pet.special_cooldown(sp['id']) if pet else 0
            status = "READY" if cd == 0 else f"cd {cd}t"
            head = f" {tag}) {sp['name']}  [{status}]"
            col = FP.GOLD_BRIGHT if cd == 0 else FP.HINT_TEXT
            self.screen.blit(self.font_md.render(head, True, col), (bx + 25, y))
            y += 22
            desc_surf = self.font_sm.render("    " + sp.get('desc', ''), True, FP.BODY_TEXT)
            self.screen.blit(desc_surf, (bx + 25, y))
            y += 22
        hint = self.font_sm.render("a-z: cast (opens target)  |  ESC: back",
                                    True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 24))

    def _draw_pet_sub_picker(self, title: str, items: list, pet, attr: str):
        """Generic sub-menu renderer for feed/heal item pickers."""
        entries = []
        for idx, it in enumerate(items):
            iname = self._display_name(it) if hasattr(self, '_display_name') else it.name
            if attr == 'sp_restore':
                sp = getattr(it, 'sp_restore', 0)
                detail = f"SP {sp}" if sp else "ingredient"
                badge = 'FOOD'
                badge_color = FP.SUCCESS_TEXT
            elif attr == 'effect':
                detail = getattr(it, 'effect', '').replace('_', ' ')
                badge = 'HEAL'
                badge_color = FP.SUCCESS_TEXT
            else:
                detail = ''
                badge = ''
                badge_color = FP.FADED_TEXT
            entries.append({
                'name': iname,
                'detail': detail,
                'key': self._menu_letter(idx),
                'icon': it,
                'badge': badge,
                'badge_color': badge_color,
            })
        selected_attr = '_pet_feed_sel' if attr == 'sp_restore' else '_pet_heal_sel'
        selected = self._menu_clamp_selection(selected_attr, len(entries))
        full_title = title
        if pet is not None:
            full_title = f"{title} - {pet.name.upper()}"
        self._draw_fast_picker_variant_b(
            title=full_title,
            entries=entries,
            selected=selected,
            subtitle="Companion care",
            hint="Up/Down: move   Enter or a-z: select   ESC: back",
            border_color=FP.GOLD_BRIGHT,
        )
        return
        draw_overlay(self.screen, 200)
        bw, bh = min(640, layout.GAME_W - 80), min(420, layout.WINDOW_H - 80)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        full_title = title
        if pet is not None:
            full_title = f"{title} — {pet.name.upper()}"
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=full_title,
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)
        y = by + 54
        if not items:
            msg = "Nothing applicable in your inventory."
            s = self.font_md.render(msg, True, FP.HINT_TEXT)
            self.screen.blit(s, (bx + (bw - s.get_width()) // 2, y))
            hint = self.font_sm.render("ESC: back", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                     by + bh - 24))
            return
        for idx, it in enumerate(items[:20]):
            tag = self._LETTERS[idx]
            iname = self._display_name(it) if hasattr(self, '_display_name') else it.name
            detail = ''
            if attr == 'sp_restore':
                sp = getattr(it, 'sp_restore', 0)
                detail = f"  (SP {sp})" if sp else ''
            elif attr == 'effect':
                detail = f"  ({getattr(it, 'effect', '')})"
            line = f" {tag}) {iname}{detail}"
            self.screen.blit(self.font_md.render(self._fit_text(line, self.font_md, bw - 50),
                                                  True, FP.BODY_TEXT), (bx + 25, y))
            y += 24
        hint = self.font_sm.render("a-z: select  |  ESC: back", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 24))

    def _draw_pet_name_popup(self):
        """Overlay shown when a Soul Sphere hatches. Lets the player type a nickname."""
        pet = getattr(self, '_naming_pet', None)
        buf = getattr(self, '_pet_name_input_buffer', '')
        if pet is None:
            return
        self._ui_input_card(
            f"A {pet.species_name.upper()} APPEARS!",
            "Will you give this companion a name?",
            buf,
            "Type: edit   |   Enter: confirm   |   Esc: skip naming",
            border_color=FP.GOLD,
            title_color=FP.GOLD_BRIGHT,
            placeholder="(unnamed)",
            max_w=660,
        )
        return

        draw_overlay(self.screen, 190)
        bw, bh = min(640, layout.GAME_W - 40), 260
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=f"A {pet.species_name.upper()} APPEARS!",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        # Subtitle: invite naming.
        sub = "Will you give this companion a name?"
        sub_surf = self.font_md.render(sub, True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 58))

        draw_divider(self.screen, bx + 20, by + 96, bw - 40)

        # Input box — same draw_input_box helper as drop-gold + QA warp
        from fantasy_ui import draw_input_box
        draw_input_box(self.screen, (bx + 60, by + 116, bw - 120, 38),
                       buf, self.font_md, placeholder="(unnamed)")

        # Hint
        hint_lines = [
            "Type to edit  |  BACKSPACE to delete",
            "ENTER to confirm  |  ESC to skip naming",
        ]
        oy = by + bh - 60
        for line in hint_lines:
            hsurf = self.font_sm.render(line, True, FP.HINT_TEXT)
            self.screen.blit(hsurf, (bx + (bw - hsurf.get_width()) // 2, oy))
            oy += 22

    def _draw_confirm_exit(self):
        self._ui_message_card(
            "SAVE YOUR PROGRESS?",
            ["Your run will be saved so you can resume it later."],
            options=[
                {'key': 'Y', 'label': 'Save & Exit', 'color': FP.GOLD_BRIGHT},
                {'key': 'N', 'label': 'Exit without saving', 'color': FP.WARNING_TEXT},
                {'key': 'C / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            footer="Enter also saves",
            border_color=FP.GOLD,
            max_w=660,
            max_h=360,
        )
        return

        draw_overlay(self.screen, 190)
        bw, bh = min(560, layout.GAME_W - 40), 230
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="SAVE YOUR PROGRESS?",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        sub = "Your run will be saved so you can resume it later."
        sub_surf = self.font_md.render(self._fit_text(sub, self.font_md, 520), True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 58))

        draw_divider(self.screen, bx + 20, by + 96, bw - 40)

        # Three option rows
        opts = [
            ("Y", "Save & Exit",         FP.GOLD_BRIGHT),
            ("N", "Exit without saving", FP.WARNING_TEXT),
            ("C / ESC", "Keep playing",  FP.HINT_TEXT),
        ]
        oy = by + 112
        for key_label, desc, col in opts:
            key_surf  = self.font_md.render(f"[ {key_label} ]", True, col)
            desc_surf = self.font_md.render(desc, True, FP.BODY_TEXT)
            total_w   = key_surf.get_width() + 12 + desc_surf.get_width()
            rx = bx + (bw - total_w) // 2
            self.screen.blit(key_surf,  (rx, oy))
            self.screen.blit(desc_surf, (rx + key_surf.get_width() + 12, oy))
            oy += key_surf.get_height() + 6

    def _draw_exit_quest(self):
        self._ui_message_card(
            "COMPLETE YOUR QUEST?",
            ["You carry the Philosopher's Stone. Leave the dungeon?"],
            options=[
                {'key': 'Y', 'label': 'Complete quest', 'color': FP.GOLD_BRIGHT},
                {'key': 'N / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            border_color=FP.GOLD,
            max_w=660,
            max_h=310,
        )
        return

        draw_overlay(self.screen, 190)
        bw, bh = min(600, layout.GAME_W - 40), 180
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="COMPLETE YOUR QUEST?",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        sub = "You carry the Philosopher's Stone. Leave the dungeon?"
        sub_surf = self.font_sm.render(sub, True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 55))

        draw_divider(self.screen, bx + 20, by + 85, bw - 40)
        opts = [("Y", "Complete quest", FP.GOLD_BRIGHT),
                ("N / ESC", "Keep playing", FP.HINT_TEXT)]
        oy = by + 100
        for key_label, desc, col in opts:
            key_surf  = self.font_md.render(f"[ {key_label} ]", True, col)
            desc_surf = self.font_md.render(desc, True, FP.BODY_TEXT)
            total_w   = key_surf.get_width() + 12 + desc_surf.get_width()
            rx = bx + (bw - total_w) // 2
            self.screen.blit(key_surf,  (rx, oy))
            self.screen.blit(desc_surf, (rx + key_surf.get_width() + 12, oy))
            oy += key_surf.get_height() + 8

    def _draw_abandon_quest(self):
        self._ui_message_card(
            "ABANDON YOUR QUEST?",
            ["You have not found the Philosopher's Stone."],
            options=[
                {'key': 'Y', 'label': 'Abandon quest', 'color': FP.WARNING_TEXT},
                {'key': 'N / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            border_color=FP.WARNING_TEXT,
            title_color=FP.WARNING_TEXT,
            max_w=660,
            max_h=310,
        )
        return

        draw_overlay(self.screen, 190)
        bw, bh = min(560, layout.GAME_W - 40), 180
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="ABANDON YOUR QUEST?",
                        font=self.font_lg, text_color=FP.WARNING_TEXT)

        sub = "You have not found the Philosopher's Stone."
        sub_surf = self.font_sm.render(sub, True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 55))

        draw_divider(self.screen, bx + 20, by + 85, bw - 40)
        opts = [("Y", "Abandon quest", FP.WARNING_TEXT),
                ("N / ESC", "Keep playing", FP.HINT_TEXT)]
        oy = by + 100
        for key_label, desc, col in opts:
            key_surf  = self.font_md.render(f"[ {key_label} ]", True, col)
            desc_surf = self.font_md.render(desc, True, FP.BODY_TEXT)
            total_w   = key_surf.get_width() + 12 + desc_surf.get_width()
            rx = bx + (bw - total_w) // 2
            self.screen.blit(key_surf,  (rx, oy))
            self.screen.blit(desc_surf, (rx + key_surf.get_width() + 12, oy))
            oy += key_surf.get_height() + 8

    def _draw_chicken(self):
        self._ui_message_card(
            "WHAT'S WRONG, MCFLY? CHICKEN?",
            ["Leaving without the Stone ends the quest."],
            options=[
                {'key': '1', 'label': 'Yes, I am a coward.', 'color': FP.WARNING_TEXT},
                {'key': '2', 'label': 'Nobody calls me chicken!', 'color': FP.GOLD_BRIGHT},
            ],
            border_color=FP.AMBER_ACCENT,
            title_color=FP.GOLD_BRIGHT,
            max_w=700,
            max_h=340,
        )
        return

        draw_overlay(self.screen, 190)
        bw, bh = min(600, layout.GAME_W - 40), 190
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="What's wrong, McFly? Chicken?",
                        font=self.font_lg, text_color=(255, 220, 80))

        draw_divider(self.screen, bx + 20, by + 56, bw - 40)
        opts = [("1", "Yes, I am a coward.",       FP.WARNING_TEXT),
                ("2", "Nobody calls me chicken!",  FP.GOLD_BRIGHT)]
        oy = by + 78
        for key_label, desc, col in opts:
            key_surf  = self.font_md.render(f"[ {key_label} ]", True, col)
            desc_surf = self.font_md.render(desc, True, col)
            total_w   = key_surf.get_width() + 12 + desc_surf.get_width()
            rx = bx + (bw - total_w) // 2
            self.screen.blit(key_surf,  (rx, oy))
            self.screen.blit(desc_surf, (rx + key_surf.get_width() + 12, oy))
            oy += key_surf.get_height() + 16

    def _draw_story_popup(self):
        """Render the current narrative popup over the game world."""
        if not self.popup_data:
            return
        d = self.popup_data
        draw_overlay(self.screen, 190, (8, 6, 2))

        accent = d['accent']
        raw_lines = d['lines']
        code = d.get('code')
        bw = min(920, layout.WINDOW_W - 96)
        bx = (layout.WINDOW_W - bw) // 2

        def build_lines(font, width):
            paragraphs = []
            buf = ''
            for line in raw_lines:
                if line == '':
                    if buf:
                        paragraphs.append((buf, False, buf.startswith('"')))
                        buf = ''
                    paragraphs.append(('', True, False))
                else:
                    buf = (buf + ' ' + line).strip() if buf else line
            if buf:
                paragraphs.append((buf, False, buf.startswith('"')))

            out = []
            for text, is_blank, is_quoted in paragraphs:
                if is_blank:
                    out.append(('', True, False))
                    continue
                for wl in self._wrap_text(text, font, width) or ['']:
                    out.append((wl, False, is_quoted))
            return out

        font_body = get_font('body', 17)
        max_txt = bw - 72
        wrapped_lines = build_lines(font_body, max_txt)
        row = font_body.get_height() + 4
        code_h = 46 if code else 0
        needed_h = 122 + len(wrapped_lines) * row + code_h
        max_h = layout.WINDOW_H - 48
        if needed_h > max_h:
            font_body = get_font('body', 15)
            wrapped_lines = build_lines(font_body, max_txt)
            row = font_body.get_height() + 3
            needed_h = 122 + len(wrapped_lines) * row + code_h

        bh = min(max_h, max(250, needed_h))
        by = (layout.WINDOW_H - bh) // 2
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=accent)
        draw_header_bar(self.screen, (bx, by, bw, 48), text=d['title'],
                        font=self.font_lg, text_color=accent, accent=accent)
        draw_divider(self.screen, bx + 18, by + 58, bw - 36)

        y = by + 74
        body_bottom = by + bh - 48 - code_h
        for text, is_blank, is_quoted in wrapped_lines:
            if is_blank:
                y += row // 2
                continue
            if y + font_body.get_height() > body_bottom:
                break
            col = (200, 195, 160) if is_quoted else FP.PARCHMENT_LIGHT
            self._ui_blit_text(text, font_body, col, bx + 36, y)
            y += row

        if code:
            code_y = by + bh - 84
            code_rect = pygame.Rect(bx + 34, code_y, bw - 68, 40)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, code_rect,
                             border_radius=6)
            pygame.draw.rect(self.screen, accent, code_rect, 1,
                             border_radius=6)
            label = "Reward Code: "
            font_label = get_font('small', 15, bold=True)
            font_code = get_font('heading', 22)
            total_w = font_label.size(label)[0] + font_code.size(code)[0]
            lx = code_rect.centerx - total_w // 2
            self._ui_blit_text(label, font_label, FP.PARCHMENT_LIGHT,
                               lx, code_rect.y + 10)
            self._ui_blit_text(code, font_code, FP.GOLD_BRIGHT,
                               lx + font_label.size(label)[0],
                               code_rect.y + 6)

        self._ui_blit_text("Press any key to continue", get_font('small', 14),
                           FP.HINT_TEXT, bx + bw // 2, by + bh - 30,
                           align='center')
        return

        # -- Background ------------------------------------------------
        draw_overlay(self.screen, 190, (8, 6, 2))

        accent = d['accent']
        raw_lines = d['lines']
        code   = d.get('code')

        bw      = min(820, layout.GAME_W - 60)
        row     = 22
        pad_x   = 36   # horizontal padding inside box
        max_txt = bw - pad_x * 2

        # Join consecutive non-blank lines into paragraphs, then word-wrap
        paragraphs = []  # list of (full_text, is_blank, is_quoted)
        buf = ''
        for line in raw_lines:
            if line == '':
                if buf:
                    paragraphs.append((buf, False, buf.startswith('"')))
                    buf = ''
                paragraphs.append(('', True, False))
            else:
                buf = (buf + ' ' + line).strip() if buf else line
        if buf:
            paragraphs.append((buf, False, buf.startswith('"')))

        wrapped_lines = []  # list of (rendered_text, is_blank, is_quoted)
        for text, is_blank, is_quoted in paragraphs:
            if is_blank:
                wrapped_lines.append(('', True, False))
            else:
                for wl in self._wrap_text(text, self.font_md, max_txt):
                    wrapped_lines.append((wl, False, is_quoted))

        # -- Box sizing (based on real wrapped line count) -------------
        bh = 80 + len(wrapped_lines) * row + (row * 3 if code else 0) + 64
        bh = min(bh, layout.GAME_H + layout.MSG_H - 40)
        bx = (layout.GAME_W - bw) // 2
        by = max(16, (layout.GAME_H + layout.MSG_H - bh) // 2)

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=accent)

        # -- Accent bar under title -------------------------------------
        accent_surf = pygame.Surface((bw - 8, 2), pygame.SRCALPHA)
        accent_surf.fill((*accent, 80))
        self.screen.blit(accent_surf, (bx + 4, by + 52))

        # -- Title -----------------------------------------------------
        title_surf = self.font_lg.render(d['title'], True, accent)
        tx = bx + (bw - title_surf.get_width()) // 2
        self.screen.blit(title_surf, (tx, by + 14))

        # -- Body text -------------------------------------------------
        y = by + 64
        for text, is_blank, is_quoted in wrapped_lines:
            if is_blank:
                y += row // 2
                continue
            col = (200, 195, 160) if is_quoted else FP.PARCHMENT_LIGHT
            surf = self.font_md.render(text, True, col)
            self.screen.blit(surf, (bx + pad_x, y))
            y += row

        # -- Code block ------------------------------------------------
        if code:
            y += row // 2
            code_bg = pygame.Surface((bw - 40, row + 8), pygame.SRCALPHA)
            code_bg.fill((*accent, 60))
            self.screen.blit(code_bg, (bx + 20, y - 4))
            code_label = self.font_md.render("Reward Code:  ", True, FP.PARCHMENT_LIGHT)
            code_val   = self.font_lg.render(code, True, FP.GOLD_BRIGHT)
            total_w    = code_label.get_width() + code_val.get_width()
            lx = bx + (bw - total_w) // 2
            self.screen.blit(code_label, (lx, y))
            self.screen.blit(code_val,   (lx + code_label.get_width(), y - 3))
            y += row + 14

        # -- Prompt ----------------------------------------------------
        prompt = self.font_sm.render("-- Press any key to continue --", True, FP.HINT_TEXT)
        px_ = bx + (bw - prompt.get_width()) // 2
        self.screen.blit(prompt, (px_, by + bh - 26))

    def _fit_ui_font(self, role: str, start_size: int, text: str, max_w: int,
                     bold: bool = False, min_size: int = 18):
        """Return the largest theme font size that fits a single-line label."""
        size = start_size
        font = get_font(role, size, bold=bold)
        while size > min_size and font.size(text)[0] > max_w:
            size -= 2
            font = get_font(role, size, bold=bold)
        return font

    def _draw_end_title_block(self, cx: int, cy: int, title_text: str,
                              sub_text: str, title_col: tuple, sub_col: tuple,
                              fil_strong: tuple, fil_subtle: tuple,
                              sub_glow: tuple | None = None,
                              title_glow: tuple | None = None) -> int:
        """Draw ceremonial end-screen title/subtitle and return next y."""
        bar_w = min(760, layout.WINDOW_W - 120)
        bar_x = cx - bar_w // 2
        title_font = self._fit_ui_font('title', 42, title_text, bar_w,
                                       bold=True, min_size=30)
        sub_font = self._fit_ui_font('heading', 26, sub_text, bar_w - 32,
                                     min_size=20)

        title_w, title_h = title_font.size(title_text)
        sub_w, sub_h = sub_font.size(sub_text)
        title_y = max(24, cy - 285)
        upper_bar_y = title_y + title_h + 8
        sub_y = upper_bar_y + 10
        lower_bar_y = sub_y + sub_h + 10

        title_pos = (cx - title_w // 2, title_y)
        if title_glow:
            draw_glow_text(self.screen, title_font, title_text, title_col,
                           title_pos, glow_color=title_glow)
        else:
            draw_shadow_text(self.screen, title_font, title_text, title_col,
                             title_pos)
        draw_filigree_bar(self.screen, bar_x, upper_bar_y, bar_w, fil_strong)
        if sub_glow:
            draw_glow_text(self.screen, sub_font, sub_text, sub_col,
                           (cx - sub_w // 2, sub_y), glow_color=sub_glow,
                           glow_r=2)
        else:
            draw_shadow_text(self.screen, sub_font, sub_text, sub_col,
                             (cx - sub_w // 2, sub_y), offset=2)
        draw_filigree_bar(self.screen, bar_x, lower_bar_y, bar_w, fil_subtle)
        return lower_bar_y + 18

    def _draw_end_summary(self, cx: int, start_y: int, grade: str,
                          grade_col: tuple, score: int, stats: list,
                          score_col: tuple, accent: tuple,
                          breakdown: str | None = None,
                          high_score_col: tuple | None = None,
                          review_text: str | None = None) -> None:
        """Draw measured score table, optional breakdown, high scores, prompt."""
        from highscore_system import get_top

        content_w = min(680, layout.WINDOW_W - 120)
        small_layout = layout.WINDOW_H < 800
        grade_font = self.font_xl if not small_layout else get_font('title', 34, bold=True)
        score_font = self.font_lg if not small_layout else get_font('heading', 28)
        row_font = self.font_md if not small_layout else get_font('body', 23)
        small_font = self.font_sm if not small_layout else get_font('body', 18)

        y = start_y
        panel_w = min(780, layout.WINDOW_W - 120)
        panel_y = max(70, start_y - 14)
        target_panel_h = 500 if not small_layout else 470
        panel_h = max(360, min(target_panel_h, layout.WINDOW_H - panel_y - 30))
        draw_dark_panel(
            self.screen,
            (cx - panel_w // 2, panel_y, panel_w, panel_h),
            border_color=accent,
            alpha=218,
        )

        grade_s = grade_font.render(grade, True, grade_col)
        score_text = f"Final Score:  {score:,}"
        score_w, score_h = score_font.size(score_text)
        head_gap = 36
        head_w = grade_s.get_width() + head_gap + score_w
        hx = cx - head_w // 2
        self.screen.blit(grade_s, (hx, y))
        draw_shadow_text(self.screen, score_font, score_text, score_col,
                         (hx + grade_s.get_width() + head_gap, y + 2))
        y += max(grade_s.get_height(), score_h) + 8

        label_w = max(row_font.size(label + " :")[0] for label, _, _ in stats)
        value_w = max(row_font.size(value)[0] for _, value, _ in stats)
        gap = 22
        table_w = min(content_w, label_w + gap + value_w)
        lx = cx - table_w // 2
        vx = lx + label_w + gap
        row_gap = row_font.get_height() + 2
        for label, value, col in stats:
            lbl_s = row_font.render(label + " :", True, FP.FADED_TEXT)
            val_s = row_font.render(value, True, col)
            self.screen.blit(lbl_s, (lx, y))
            self.screen.blit(val_s, (vx, y))
            y += row_gap

        y += 4
        draw_filigree_bar(self.screen, cx - content_w // 2, y, content_w, accent)
        y += 12

        if breakdown:
            for line in self._wrap_text(breakdown, small_font, content_w):
                b_surf = small_font.render(line, True, FP.FADED_TEXT)
                self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, y))
                y += small_font.get_height() + 1
            y += 9

        top = get_top(5)
        prompt_s = row_font.render("Press ESC to close", True, FP.HINT_TEXT)
        bottom_limit = panel_y + panel_h - 20
        hs_title_h = small_font.get_height() + 2
        hs_row_h = small_font.get_height() + 1
        available = bottom_limit - y - prompt_s.get_height() - 10
        rows_fit = max(0, (available - hs_title_h) // hs_row_h)
        show_n = min(len(top), 5, rows_fit)

        if show_n > 0:
            hs_title = small_font.render("-- HIGH SCORES --",
                                         True, high_score_col or accent)
            self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, y))
            y += hs_title_h
            for i, e in enumerate(top[:show_n]):
                marker = ">" if e['score'] == score else " "
                hs_line = (f"{marker}{i+1}. {e.get('name','?'):<10}  "
                           f"{e['score']:>8,}  {e.get('grade','?'):>2}  "
                           f"L{e.get('level',0)}")
                col = (high_score_col or FP.GOLD_BRIGHT) if e['score'] == score else FP.FADED_TEXT
                hs_s = small_font.render(hs_line, True, col)
                self.screen.blit(hs_s, (cx - hs_s.get_width() // 2, y))
                y += hs_row_h
            y += 4

        if review_text and y + row_font.get_height() < bottom_limit - prompt_s.get_height() - 6:
            review_s = row_font.render(review_text, True, FP.GOLD_BRIGHT)
            self.screen.blit(review_s, (cx - review_s.get_width() // 2, y))
            y += row_font.get_height() + 4

        prompt_y = min(y + 2, bottom_limit - prompt_s.get_height())
        self.screen.blit(prompt_s, (cx - prompt_s.get_width() // 2, prompt_y))

    def _draw_victory_screen(self):
        """Victory screen — branches on `_secret_victory` to render the
        distinct Abyss-victory variant (arcane purple, "DEATH IS DEAD"
        headline) when the player triggered the secret ending.
        """
        is_secret = bool(getattr(self, '_secret_victory', False))

        if is_secret:
            # Arcane-purple Abyss palette — distinct from the gold Stone-exit
            # victory, but stays within Christian-Crusader framing (Michael's
            # judgment of Death, per Revelation).
            overlay_col = (16, 6, 24)
            ring_outer  = (*FP.ARCANE_DIM, 150)
            ring_inner  = (*FP.ARCANE_BRIGHT, 110)
            candle_int  = 0.6
            fil_strong  = FP.ARCANE_BRIGHT
            fil_subtle  = FP.ARCANE
            title_text  = "DEATH IS DEAD"
            sub_text    = "The Abyss has closed beneath you."
            title_col   = FP.ARCANE_BRIGHT
            sub_col     = FP.ARCANE_ACCENT
            glow_col    = None
        else:
            overlay_col = (12, 10, 0)
            ring_outer  = (*FP.GOLD_DARK, 120)
            ring_inner  = (*FP.GOLD, 90)
            candle_int  = 0.9
            fil_strong  = FP.GOLD
            fil_subtle  = FP.GOLD_DARK
            title_text  = "VICTORY!"
            sub_text    = "You retrieved the Philosopher's Stone!"
            title_col   = FP.GOLD_BRIGHT
            sub_col     = FP.PARCHMENT_LIGHT
            glow_col    = None

        draw_overlay(self.screen, 190, overlay_col)
        score = self._calc_score()
        grade, grade_col = self._get_grade(score)
        cx    = layout.WINDOW_W // 2
        cy    = layout.WINDOW_H // 2

        # Animated rune circles (counter-rotating)
        t = pygame.time.get_ticks() / 1000.0
        draw_rune_circle(self.screen, cx, cy, 280, ring_outer, t, 16)
        draw_rune_circle(self.screen, cx, cy, 190, ring_inner, -t * 1.3, 10)
        draw_candle_glow(self.screen, cx, cy, candle_int)

        start_y = self._draw_end_title_block(
            cx, cy, title_text, sub_text, title_col, sub_col,
            fil_strong, fil_subtle, sub_glow=glow_col)

        total_q = self.correct_answers + self.wrong_answers
        acc_pct  = int(100 * self.correct_answers / total_q) if total_q else 0
        stats = [
            ("Turns Survived",        f"{self.turn_count:,}",                FP.BODY_TEXT),
            ("Deepest Level",         f"{self.level_mgr.max_level_reached}",  FP.BODY_TEXT),
            ("Monsters Slain",        f"{self.level_mgr.monsters_killed:,}",  FP.BODY_TEXT),
            ("Gold Collected",        f"{self.player_gold:,}",               FP.GOLD_PALE),
            ("Questions Answered",    f"{total_q:,}",                         FP.BODY_TEXT),
            ("Correct  /  Wrong",     f"{self.correct_answers} / {self.wrong_answers}   ({acc_pct}%)",
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]
        breakdown = (f"({self.turn_count}x10)  +  ({self.level_mgr.max_level_reached}x1000)  +"
                     f"  ({self.level_mgr.monsters_killed}x100)  +  50 000 stone bonus")

        # High score: save once, then display top 5
        from highscore_system import add_score
        if not self._score_saved:
            pname = getattr(self, 'player_name', None) or 'Hero'
            add_score(pname, score, grade,
                      self.level_mgr.max_level_reached,
                      self.level_mgr.monsters_killed,
                      self.turn_count, victory=True)
            self._score_saved = True

        self._draw_end_summary(
            cx, start_y, grade, grade_col, score, stats,
            FP.GOLD_BRIGHT, fil_subtle, breakdown=breakdown,
            high_score_col=FP.GOLD_BRIGHT)

    def _draw_death_screen(self):
        # FANTASY: Dark blood-red death screen with animated runes
        draw_overlay(self.screen, 180, (50, 0, 0))
        score = self._calc_score()
        cx    = layout.WINDOW_W // 2
        cy    = layout.WINDOW_H // 2

        t = pygame.time.get_ticks() / 1000.0
        draw_rune_circle(self.screen, cx, cy, 260, (*FP.BURGUNDY, 110), t * 0.4, 14)
        draw_rune_circle(self.screen, cx, cy, 170, (*FP.BLOOD, 70),     -t * 0.6, 8)

        if self.defeat_reason == 'fled':
            title_text = "YOU FLED THE DUNGEON"
            sub_text   = "Your quest ends in cowardice."
            tc = FP.WARNING_TEXT
        elif self.defeat_reason == 'starved':
            title_text = "YOU HAVE STARVED"
            sub_text   = f"Hunger claimed you on level {self.dungeon_level}."
            tc = FP.WARNING_TEXT
        else:
            title_text = "YOU HAVE DIED"
            sub_text   = f"Slain on dungeon level {self.dungeon_level}."
            tc = FP.DANGER_TEXT

        grade, grade_col = self._get_grade(score)

        start_y = self._draw_end_title_block(
            cx, cy, title_text, sub_text, FP.BLOOD, tc,
            FP.BURGUNDY_MID, FP.BURGUNDY_MID,
            title_glow=FP.BURGUNDY)

        total_q  = self.correct_answers + self.wrong_answers
        acc_pct  = int(100 * self.correct_answers / total_q) if total_q else 0
        stats = [
            ("Turns Survived",     f"{self.turn_count:,}",                   FP.BODY_TEXT),
            ("Deepest Level",      f"{self.level_mgr.max_level_reached}",     FP.BODY_TEXT),
            ("Monsters Slain",     f"{self.level_mgr.monsters_killed:,}",     FP.BODY_TEXT),
            ("Gold Collected",     f"{self.player_gold:,}",                   FP.GOLD_PALE),
            ("Questions Answered", f"{total_q:,}",                            FP.BODY_TEXT),
            ("Correct  /  Wrong",  f"{self.correct_answers} / {self.wrong_answers}   ({acc_pct}%)",
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]

        # High score: save once, then display top 5
        from highscore_system import add_score
        if not self._score_saved:
            pname = getattr(self, 'player_name', None) or 'Hero'
            add_score(pname, score, grade,
                      self.level_mgr.max_level_reached,
                      self.level_mgr.monsters_killed,
                      self.turn_count, victory=False)
            self._score_saved = True

        review_text = None
        if self.missed_questions:
            review_text = f"Press R to review {len(self.missed_questions)} missed questions"

        self._draw_end_summary(
            cx, start_y, grade, grade_col, score, stats,
            FP.GOLD_PALE, FP.BURGUNDY_DARK,
            high_score_col=FP.GOLD_PALE,
            review_text=review_text)

    # ------------------------------------------------------------------
    # Post-death missed question review

    # ------------------------------------------------------------------
    # Knowledge / records screen helpers

    def _ui_blit_text(self, text, font, color, x, y, *, align='left',
                      max_width=None):
        text = str(text)
        if max_width is not None and font.size(text)[0] > max_width:
            lines = self._wrap_text(text, font, max_width)
            text = lines[0] if lines else ''
        surf = font.render(text, True, color)
        if align == 'center':
            x -= surf.get_width() // 2
        elif align == 'right':
            x -= surf.get_width()
        self.screen.blit(surf, (x, y))
        return surf.get_rect(topleft=(x, y))

    def _ui_wrap_text(self, text, font, color, rect, *, line_gap=3,
                      max_lines=None):
        y = rect.y
        drawn = 0
        chunks = str(text).splitlines() or ['']
        for chunk in chunks:
            for line in self._wrap_text(chunk, font, rect.w) or ['']:
                if max_lines is not None and drawn >= max_lines:
                    return y
                if y + font.get_height() > rect.bottom:
                    return y
                self._ui_blit_text(line, font, color, rect.x, y)
                y += font.get_height() + line_gap
                drawn += 1
        return y

    def _ui_modal_panel(self, title, *, border_color=FP.GOLD, max_w=1440,
                        max_h=760, center_window=False):
        draw_overlay(self.screen, 190)
        anchor_w = layout.WINDOW_W if center_window else layout.GAME_W
        bw = min(max_w, anchor_w - 48)
        bh = min(max_h, layout.WINDOW_H - 48)
        bx = (anchor_w - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        rect = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, rect, border_color=border_color)
        draw_header_bar(self.screen, (bx, by, bw, 48), text=title,
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT,
                        accent=border_color)
        draw_divider(self.screen, bx + 18, by + 58, bw - 36)
        return rect

    def _ui_subpanel(self, rect, label, *, border_color=FP.GOLD_DARK):
        pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=6)
        head = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, 29)
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, head, border_radius=6)
        f = get_font('small', 14, bold=True)
        self._ui_blit_text(label.upper(), f, FP.GOLD_BRIGHT,
                           rect.centerx, rect.y + 7, align='center')
        return pygame.Rect(rect.x + 12, rect.y + 42, rect.w - 24,
                           rect.h - 54)

    def _ui_footer(self, panel_rect, hint):
        y = panel_rect.bottom - 36
        draw_divider(self.screen, panel_rect.x + 18, y - 5,
                     panel_rect.w - 36)
        f = get_font('small', 14)
        self._ui_blit_text(hint, f, FP.HINT_TEXT, panel_rect.centerx,
                           y + 4, align='center',
                           max_width=panel_rect.w - 44)

    def _ui_chip(self, rect, label, *, active=False, color=FP.GOLD):
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                         rect, border_radius=5)
        pygame.draw.rect(self.screen, color if active else FP.GOLD_DARK,
                         rect, 1, border_radius=5)
        f = get_font('small', 14, bold=True)
        self._ui_blit_text(label, f, FP.GOLD_BRIGHT if active else FP.FADED_TEXT,
                           rect.centerx, rect.y + 6, align='center',
                           max_width=rect.w - 10)

    def _ui_row(self, rect, title, detail='', *, key='', selected=False,
                badge='', title_color=None, badge_color=None, row_color=None):
        fill = row_color or ((34, 43, 84) if selected else FP.MIDNIGHT)
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, FP.GOLD if selected else FP.ARCANE_DIM,
                         rect, 1, border_radius=6)
        tx = rect.x + 10
        if key:
            krect = pygame.Rect(rect.x + 8, rect.y + 9, 32, 32)
            pygame.draw.rect(self.screen, (96, 34, 28), krect, border_radius=5)
            self._ui_blit_text(str(key), get_font('small', 15, bold=True),
                               FP.GOLD_BRIGHT, krect.centerx, krect.y + 8,
                               align='center')
            tx = krect.right + 10
        bw = 0
        if badge:
            bf = get_font('small', 12, bold=True)
            bw = bf.size(str(badge))[0] + 18
            brect = pygame.Rect(rect.right - bw - 8, rect.y + 14, bw, 24)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, brect,
                             border_radius=5)
            bc = badge_color or FP.CYAN_ACCENT
            pygame.draw.rect(self.screen, bc, brect, 1, border_radius=5)
            self._ui_blit_text(str(badge), bf, bc, brect.centerx,
                               brect.y + 5, align='center')
        max_w = rect.right - tx - bw - 16
        self._ui_wrap_text(title, get_font('small', 15, bold=True),
                           title_color or FP.BODY_TEXT,
                           pygame.Rect(tx, rect.y + 7, max_w, 36),
                           line_gap=0, max_lines=2)
        if detail:
            self._ui_blit_text(detail, get_font('small', 12), FP.FADED_TEXT,
                               tx, rect.y + rect.h - 20, max_width=max_w)

    def _ui_progress_bar(self, rect, pct, *, color=FP.ARCANE_BRIGHT,
                         label=''):
        pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=4)
        fill_w = int(rect.w * max(0.0, min(1.0, float(pct))))
        if fill_w:
            pygame.draw.rect(self.screen, color,
                             (rect.x, rect.y, fill_w, rect.h),
                             border_radius=4)
        pygame.draw.rect(self.screen, FP.ARCANE_DIM, rect, 1, border_radius=4)
        if label:
            self._ui_blit_text(label, get_font('small', 12), FP.BODY_TEXT,
                               rect.centerx, rect.y - 2, align='center')

    def _ui_scrollbar(self, rect, scroll, total_lines, visible_lines,
                      *, color=FP.GOLD_DARK):
        if total_lines <= visible_lines:
            return
        track = pygame.Rect(rect.right - 8, rect.y, 5, rect.h)
        pygame.draw.rect(self.screen, FP.MIDNIGHT, track, border_radius=3)
        ratio = visible_lines / max(1, total_lines)
        thumb_h = max(20, int(track.h * ratio))
        max_scroll = max(1, total_lines - visible_lines)
        thumb_y = track.y + int((track.h - thumb_h) *
                                (max(0, scroll) / max_scroll))
        pygame.draw.rect(self.screen, color,
                         (track.x, thumb_y, track.w, thumb_h),
                         border_radius=3)

    def _ui_text_lines(self, text, font, width):
        lines = []
        for chunk in str(text).splitlines() or ['']:
            lines.extend(self._wrap_text(chunk, font, width) or [''])
        return lines

    def _ui_action_row(self, rect, key, label, *, color=FP.BODY_TEXT,
                       selected=False):
        fill = FP.MIDNIGHT_MID if selected else FP.MIDNIGHT
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, FP.GOLD if selected else FP.ARCANE_DIM,
                         rect, 1, border_radius=6)

        key = str(key)
        key_font = get_font('small', 14, bold=True)
        label_font = get_font('small', 15, bold=True)
        key_w = max(42, min(rect.w // 3, key_font.size(key)[0] + 20))
        key_rect = pygame.Rect(rect.x + 8, rect.y + 8, key_w, rect.h - 16)
        pygame.draw.rect(self.screen, (96, 34, 28), key_rect, border_radius=5)
        pygame.draw.rect(self.screen, color, key_rect, 1, border_radius=5)
        self._ui_blit_text(key, key_font, color, key_rect.centerx,
                           key_rect.y + max(4, (key_rect.h - key_font.get_height()) // 2),
                           align='center')

        text_rect = pygame.Rect(key_rect.right + 12, rect.y + 8,
                                rect.right - key_rect.right - 22,
                                rect.h - 16)
        self._ui_wrap_text(label, label_font, color, text_rect,
                           line_gap=0, max_lines=2)

    def _ui_message_card(self, title, body_lines, *, options=None,
                         footer='', border_color=FP.GOLD,
                         title_color=None, body_color=FP.BODY_TEXT,
                         max_w=720, max_h=520):
        """Shared wrapped modal for confirmations and small result cards."""
        draw_overlay(self.screen, 190)
        bw = min(max_w, layout.GAME_W - 48)
        body_font = get_font('body', 17)
        small_font = get_font('small', 14)
        text_w = bw - 72

        wrapped = []
        for entry in body_lines:
            if entry == '':
                wrapped.append(('', None))
                continue
            if isinstance(entry, tuple):
                text, col = entry[0], entry[1]
            else:
                text, col = entry, body_color
            for line in self._wrap_text(str(text), body_font, text_w) or ['']:
                wrapped.append((line, col))

        opts = options or []
        option_h = 48
        text_h = sum(10 if line == '' else body_font.get_height() + 4
                     for line, _ in wrapped)
        bh = 94 + text_h + (len(opts) * (option_h + 8)) + 44
        bh = min(max_h, layout.WINDOW_H - 48, max(220, bh))
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        panel = pygame.Rect(bx, by, bw, bh)

        draw_dark_panel(self.screen, panel, border_color=border_color)
        draw_header_bar(self.screen, (bx, by, bw, 48), text=title,
                        font=self.font_lg, text_color=title_color or FP.GOLD_BRIGHT,
                        accent=border_color)
        draw_divider(self.screen, bx + 18, by + 58, bw - 36)

        y = by + 72
        options_h = len(opts) * (option_h + 8)
        footer_h = 42 if footer else 22
        body_bottom = by + bh - options_h - footer_h - 8
        for line, col in wrapped:
            if line == '':
                y += 10
                continue
            if y + body_font.get_height() > body_bottom:
                break
            self._ui_blit_text(line, body_font, col or body_color,
                               bx + 36, y)
            y += body_font.get_height() + 4

        if opts:
            y = max(y + 8, by + bh - options_h - footer_h)
            for opt in opts:
                row = pygame.Rect(bx + 34, y, bw - 68, option_h)
                self._ui_action_row(row, opt.get('key', ''),
                                    opt.get('label', ''),
                                    color=opt.get('color', FP.BODY_TEXT),
                                    selected=opt.get('selected', False))
                y += option_h + 8

        if footer:
            self._ui_blit_text(footer, small_font, FP.HINT_TEXT,
                               bx + bw // 2, by + bh - 30,
                               align='center', max_width=bw - 44)

    def _ui_input_card(self, title, prompt, value, hint, *,
                       border_color=FP.GOLD, title_color=None,
                       placeholder='', max_w=620):
        from fantasy_ui import draw_input_box

        draw_overlay(self.screen, 190)
        bw, bh = min(max_w, layout.GAME_W - 48), 238
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border_color)
        draw_header_bar(self.screen, (bx, by, bw, 48), text=title,
                        font=self.font_lg, text_color=title_color or FP.GOLD_BRIGHT,
                        accent=border_color)
        draw_divider(self.screen, bx + 18, by + 58, bw - 36)

        prompt_rect = pygame.Rect(bx + 36, by + 76, bw - 72, 46)
        self._ui_wrap_text(prompt, get_font('body', 17), FP.BODY_TEXT,
                           prompt_rect, line_gap=2, max_lines=2)

        draw_input_box(self.screen, (bx + 70, by + 132, bw - 140, 38),
                       value, self.font_md, border_color=border_color,
                       placeholder=placeholder)
        self._ui_blit_text(hint, get_font('small', 14), FP.HINT_TEXT,
                           bx + bw // 2, by + bh - 32, align='center',
                           max_width=bw - 44)

    def _ui_draw_scroll_lines(self, lines, font, color, rect, scroll=0,
                              *, line_gap=3):
        line_h = font.get_height() + line_gap
        visible = max(1, rect.h // line_h)
        max_scroll = max(0, len(lines) - visible)
        scroll = max(0, min(int(scroll), max_scroll))
        y = rect.y
        for i, entry in enumerate(lines[scroll:scroll + visible],
                                  start=scroll):
            if isinstance(entry, tuple):
                text, col, fnt = entry
                fnt = fnt or font
                col = col or color
            else:
                text, col, fnt = entry, color, font
            if y + fnt.get_height() > rect.bottom:
                break
            self._ui_blit_text(text, fnt, col, rect.x, y, max_width=rect.w - 12)
            y += fnt.get_height() + line_gap
        self._ui_scrollbar(rect, scroll, len(lines), visible)
        return scroll

    def _lore_equipped_slot(self, item):
        """Return the equipped slot name for item, or None when it is not worn."""
        try:
            from items import ARMOR_SLOTS
        except Exception:
            ARMOR_SLOTS = []
        p = self.player
        if getattr(p, 'weapon', None) is item:
            return 'weapon'
        if getattr(p, 'ranged_weapon', None) is item:
            return 'ranged_weapon'
        if getattr(p, 'shield', None) is item:
            return 'shield'
        for idx, equipped in enumerate(getattr(p, 'armor_slots', []) or []):
            if equipped is item and idx < len(ARMOR_SLOTS):
                return ARMOR_SLOTS[idx]
        for idx, equipped in enumerate(getattr(p, 'accessory_slots', []) or []):
            if equipped is item:
                return f'accessory_{idx}'
        if getattr(p, 'amulet_slot', None) is item:
            return 'amulet'
        if getattr(p, 'belt_slot', None) is item:
            return 'belt'
        return None

    def _lore_direct_id_level(self, item):
        if isinstance(item, Corpse):
            return int(getattr(item, 'id_level', 0) or 0)
        return int(getattr(item, 'id_level', 5) if hasattr(item, 'id_level') else 5)

    def _lore_bonus_label(self, key, value):
        if key == 'ac_bonus':
            return f"AC +{value}"
        if key.startswith('resistance_'):
            label = key[len('resistance_'):].replace('_', ' ').title()
            return f"{label} resistance +{value}"
        if key.startswith('stat_bonus_'):
            label = key[len('stat_bonus_'):].upper()
            try:
                return f"{label} {int(value):+d}"
            except (TypeError, ValueError):
                return f"{label} +{value}"
        if key == 'regen_bonus':
            return f"Regeneration +{value}"
        if key.startswith('status_'):
            return f"{key[len('status_'):].replace('_', ' ').title()} status"
        if key.startswith('passive_'):
            return key[len('passive_'):].replace('_', ' ').title()
        return f"{key.replace('_', ' ').title()}: {value}"

    def _lore_item_identity_lines(self, item, id_level):
        lines = [
            (self._display_name(item), FP.GOLD_BRIGHT, get_font('heading', 20)),
            (f"Identification: {id_level}/5", FP.CYAN_ACCENT, self.font_sm),
        ]
        unidentified = getattr(item, 'unidentified_name', '')
        if id_level < 1 and unidentified:
            lines.append(("Unidentified description", FP.GOLD_BRIGHT, self.font_sm))
            lines.append((self._fix_name_case(unidentified), FP.BODY_TEXT, self.font_sm))
        elif hasattr(item, 'name'):
            lines.append(("True name", FP.GOLD_BRIGHT, self.font_sm))
            true_name = item.name if id_level >= 1 else "Unknown"
            lines.append((self._fix_name_case(true_name), FP.BODY_TEXT, self.font_sm))

        item_class = getattr(item, 'item_class', type(item).__name__)
        lines.append((f"Class: {item_class.replace('_', ' ').title()}",
                      FP.BODY_TEXT, self.font_sm))
        slot = getattr(item, 'slot', '')
        if slot:
            lines.append((f"Slot: {str(slot).replace('_', ' ').title()}",
                          FP.BODY_TEXT, self.font_sm))
        weight = getattr(item, 'weight', None)
        if weight is not None:
            lines.append((f"Weight: {weight:g}", FP.BODY_TEXT, self.font_sm))

        if hasattr(item, 'buc'):
            if id_level >= 2 or getattr(item, 'buc_known', False):
                aura = getattr(item, 'buc', 'uncursed')
            else:
                aura = "unknown"
            lines.append((f"Aura: {aura}", FP.GOLD_PALE, self.font_sm))

        source = "Equipped" if self._lore_equipped_slot(item) else (
            "Pack" if item in getattr(self.player, 'inventory', []) else "Record")
        lines.append((f"Source: {source}", FP.FADED_TEXT, self.font_sm))
        return lines

    def _lore_item_mechanic_lines(self, item, id_level):
        lines = []
        if id_level < 3 and hasattr(item, 'id_level'):
            lines.append(("Mechanics unrevealed", FP.GOLD_BRIGHT, self.font_sm))
            lines.append(("Identify this item further to reveal stats, effects, and chain abilities.",
                          FP.FADED_TEXT, self.font_sm))
            return lines

        if isinstance(item, Weapon):
            dmg_types = ', '.join(getattr(item, 'damage_types', []) or ['physical'])
            lines += [
                ("Weapon", FP.GOLD_BRIGHT, self.font_sm),
                (f"Type: {item.weapon_class}   Material: {item.material}   Tier: {item.tier}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Damage: {self._kit_damage_str(item)}   Average: {self._kit_avg_damage(item) or '?'}   Types: {dmg_types}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Reach: {getattr(item, 'reach', 1)}   {'Two-handed' if getattr(item, 'two_handed', False) else 'One-handed'}",
                 FP.BODY_TEXT, self.font_sm),
            ]
            special = self._kit_weapon_special(item, id_level)
            if special and special != '-':
                lines.append((f"Special: {special}", FP.CYAN_ACCENT, self.font_sm))
            if getattr(item, 'requires_ammo', ''):
                lines.append((f"Requires ammo: {item.requires_ammo}", FP.WARNING_TEXT, self.font_sm))

        elif isinstance(item, Armor):
            lines += [
                ("Armor", FP.GOLD_BRIGHT, self.font_sm),
                (f"Slot: {item.slot}   Material: {item.material}   Tier: {item.tier}",
                 FP.BODY_TEXT, self.font_sm),
                (f"AC bonus: +{item.ac_bonus}   Enchant: +{getattr(item, 'enchant_bonus', 0)}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Equip threshold: {getattr(item, 'equip_threshold', '?')} correct",
                 FP.BODY_TEXT, self.font_sm),
            ]
            if getattr(item, 'damage_resistances', None):
                lines.append((f"Resists: {self._kit_resist_str(item)}",
                              FP.CYAN_ACCENT, self.font_sm))

        elif isinstance(item, Shield):
            lines += [
                ("Shield", FP.GOLD_BRIGHT, self.font_sm),
                (f"Material: {item.material}   Tier: {item.tier}",
                 FP.BODY_TEXT, self.font_sm),
                (f"AC bonus: +{item.ac_bonus}   Enchant: +{getattr(item, 'enchant_bonus', 0)}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Equip threshold: {getattr(item, 'equip_threshold', '?')} correct",
                 FP.BODY_TEXT, self.font_sm),
            ]
            if getattr(item, 'damage_resistances', None):
                lines.append((f"Resists: {self._kit_resist_str(item)}",
                              FP.CYAN_ACCENT, self.font_sm))

        elif isinstance(item, Accessory):
            lines += [
                ("Accessory", FP.GOLD_BRIGHT, self.font_sm),
                (f"Slot: {getattr(item, 'slot', 'accessory')}",
                 FP.BODY_TEXT, self.font_sm),
            ]
            fx = getattr(item, 'effects', {}) or {}
            if fx:
                parts = []
                if 'stat' in fx:
                    parts.append(f"{fx['stat']} {int(fx.get('amount', 0)):+d}")
                if 'stat2' in fx:
                    parts.append(f"{fx['stat2']} {int(fx.get('amount2', 0)):+d}")
                if 'status' in fx:
                    parts.append(f"grants {str(fx['status']).replace('_', ' ').title()}")
                lines.append(("Effect: " + ', '.join(parts), FP.CYAN_ACCENT, self.font_sm))
            lines.append((f"Equip threshold: {getattr(item, 'equip_threshold', '?')} correct",
                          FP.BODY_TEXT, self.font_sm))

        elif isinstance(item, Wand):
            lines += [
                ("Wand", FP.GOLD_BRIGHT, self.font_sm),
                (f"Effect: {getattr(item, 'effect', '?').replace('_', ' ')}   Power: {getattr(item, 'power', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Charges: {item.charges}/{item.max_charges}",
                 FP.CYAN_ACCENT, self.font_sm),
                (f"Science threshold: {getattr(item, 'quiz_threshold', '?')} correct",
                 FP.BODY_TEXT, self.font_sm),
            ]

        elif isinstance(item, Scroll):
            lines += [
                ("Scroll", FP.GOLD_BRIGHT, self.font_sm),
                (f"Effect: {getattr(item, 'effect', '?').replace('_', ' ')}   Power: {getattr(item, 'power', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Grammar threshold: {getattr(item, 'quiz_threshold', '?')} correct",
                 FP.BODY_TEXT, self.font_sm),
            ]

        elif isinstance(item, Spellbook):
            spell_name = getattr(item, 'spell_name', getattr(item, 'name', 'spell'))
            lines += [
                ("Spellbook", FP.GOLD_BRIGHT, self.font_sm),
                (f"Teaches: {spell_name}   MP cost: {getattr(item, 'mp_cost', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Grammar threshold: {getattr(item, 'quiz_threshold', '?')} correct",
                 FP.BODY_TEXT, self.font_sm),
            ]

        elif isinstance(item, Potion):
            effect = getattr(item, 'effect', '') or 'unknown'
            lines += [
                ("Potion", FP.GOLD_BRIGHT, self.font_sm),
                (f"Effect: {effect.replace('_', ' ').title()}", FP.BODY_TEXT, self.font_sm),
            ]
            if getattr(item, 'power', ''):
                lines.append((f"Power: {item.power}", FP.BODY_TEXT, self.font_sm))
            duration = getattr(item, 'duration', 0)
            lines.append((f"Duration: {duration} turns" if duration else "Duration: instant",
                          FP.BODY_TEXT, self.font_sm))

        elif isinstance(item, Food):
            lines += [
                ("Food", FP.GOLD_BRIGHT, self.font_sm),
                (f"Restores: {getattr(item, 'sp_restore', 0)} SP, {getattr(item, 'hp_restore', 0)} HP",
                 FP.BODY_TEXT, self.font_sm),
            ]
            bonus_type = getattr(item, 'bonus_type', 'none')
            if bonus_type and bonus_type != 'none':
                target = getattr(item, 'bonus_stat', '') or getattr(item, 'bonus_effect', '')
                lines.append((f"Bonus: {bonus_type} {target} +{getattr(item, 'bonus_amount', 0)}",
                              FP.CYAN_ACCENT, self.font_sm))

        elif isinstance(item, Ammo):
            lines += [
                ("Ammunition", FP.GOLD_BRIGHT, self.font_sm),
                (f"Type: {getattr(item, 'ammo_type', '?')}   Tier: {getattr(item, 'tier', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Damage bonus: +{getattr(item, 'damage_bonus', 0)}   Count range: {getattr(item, 'count_min', '?')}-{getattr(item, 'count_max', '?')}",
                 FP.BODY_TEXT, self.font_sm),
            ]

        if getattr(item, 'set_id', ''):
            lines.append((f"Set: {getattr(item, 'set_name', getattr(item, 'set_id', ''))}",
                          FP.GOLD_PALE, self.font_sm))

        tiers = getattr(item, 'tier_bonuses', None) or {}
        if tiers:
            try:
                from chain_equip import get_chain_subject, get_chain_mode
                subject = get_chain_subject(item)
                mode = get_chain_mode(item)
            except Exception:
                subject = getattr(item, 'equip_chain_subject', '') or 'geography'
                mode = getattr(item, 'equip_chain_mode', '') or 'chain'
            achieved = int(getattr(item, 'achieved_tier', 0) or 0)
            lines += [
                ("Chain abilities", FP.GOLD_BRIGHT, self.font_sm),
                (f"Quiz: {subject} / {str(mode).replace('_', ' ')}   Active tier: {achieved}",
                 FP.CYAN_ACCENT, self.font_sm),
            ]
            for tier in range(1, 6):
                bonuses = tiers.get(str(tier), tiers.get(tier, {})) or {}
                labels = [self._lore_bonus_label(k, v) for k, v in bonuses.items()]
                status = "active" if achieved >= tier else "locked"
                color = FP.SUCCESS_TEXT if achieved >= tier else FP.FADED_TEXT
                lines.append((f"T{tier} ({status}): " + ('; '.join(labels) if labels else '?'),
                              color, self.font_sm))

        cb = getattr(item, 'carry_bonus', None) or {}
        if cb.get('stat') and cb.get('amount'):
            lines += [
                ("Keepsake", FP.GOLD_BRIGHT, self.font_sm),
                (f"{cb['stat']} +{cb['amount']} while carried", FP.CYAN_ACCENT, self.font_sm),
            ]

        return lines or [("No revealed mechanics recorded.", FP.FADED_TEXT, self.font_sm)]

    def _lore_corpse_lines(self, corpse, id_level):
        mdef = getattr(corpse, 'monster_def', None) or {}
        identity = [
            (getattr(corpse, 'monster_name', 'Unknown creature'), FP.GOLD_BRIGHT, get_font('heading', 20)),
            ("Bestiary: identified" if id_level >= 5 else "Bestiary: unstudied",
             FP.CYAN_ACCENT, self.font_sm),
        ]
        if id_level >= 3:
            tags = mdef.get('tags', []) or []
            if tags:
                identity.append((f"Tags: {', '.join(tags)}", FP.BODY_TEXT, self.font_sm))

        mechanics = []
        if id_level >= 2:
            mechanics.append(("Creature stats", FP.GOLD_BRIGHT, self.font_sm))
            mechanics.append((f"HP: {mdef.get('hp', '?')}   THAC0: {mdef.get('thac0', '?')}   Speed: {mdef.get('speed', 1)}",
                              FP.BODY_TEXT, self.font_sm))
            for atk in mdef.get('attacks', []) or []:
                line = f"{atk.get('name', '?').replace('_', ' ')}: {atk.get('damage', '?')} ({atk.get('type', 'physical')})"
                effect = atk.get('effect')
                if effect:
                    line += f" -> {effect.replace('_', ' ')} {int(atk.get('effect_chance', 0) * 100)}%"
                mechanics.append((line, FP.BODY_TEXT, self.font_sm))
        else:
            mechanics.append(("Stats unrevealed. Study this corpse to learn more.",
                              FP.FADED_TEXT, self.font_sm))

        if id_level >= 3:
            res = mdef.get('resistances', []) or []
            wks = mdef.get('weaknesses', []) or []
            if res:
                mechanics.append((f"Resists: {', '.join(res)}", FP.CYAN_ACCENT, self.font_sm))
            if wks:
                mechanics.append((f"Weak to: {', '.join(wks)}", FP.WARNING_TEXT, self.font_sm))

        if id_level >= 2:
            ingredient_id = getattr(corpse, 'ingredient_id', '')
            if ingredient_id:
                try:
                    from food_system import load_ingredient_for, get_recipes_for_ingredient
                    ing = load_ingredient_for(ingredient_id)
                    if ing:
                        mechanics.append((f"Ingredient: {ing.name}", FP.GOLD_PALE, self.font_sm))
                    recipes = get_recipes_for_ingredient(ingredient_id)
                    if recipes:
                        mechanics.append(("Known recipe uses", FP.GOLD_BRIGHT, self.font_sm))
                        for recipe in recipes[:5]:
                            mechanics.append((recipe.get('name', '?'), FP.BODY_TEXT, self.font_sm))
                except Exception:
                    pass
            else:
                mechanics.append(("Ingredient: none", FP.FADED_TEXT, self.font_sm))

        lore = getattr(corpse, 'lore', '') if id_level >= 4 else (
            "The creature's deeper history is still hidden. Study further to uncover it."
        )
        return identity, mechanics, lore or "No lore recorded."

    def _draw_lore_dossier_screen(self):
        subject = getattr(self, '_lore_subject', None)
        if not subject:
            return

        is_corpse = isinstance(subject, Corpse)
        id_level = self._lore_direct_id_level(subject)
        border = FP.LORE_GOLD_BORDER if is_corpse else FP.LORE_BLUE_BORDER
        title_name = (getattr(subject, 'monster_name', None) if is_corpse
                      else self._display_name(subject))
        panel = self._ui_modal_panel(
            "BESTIARY DOSSIER" if is_corpse else "ITEM DOSSIER",
            border_color=border,
            max_w=1440,
            max_h=760,
        )
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        gutter = 14
        left_w = max(250, min(340, int(body.w * 0.26)))
        mid_w = max(330, min(460, int(body.w * 0.34)))
        right_w = body.w - left_w - mid_w - gutter * 2
        if right_w < 300:
            shrink = 300 - right_w
            mid_w = max(300, mid_w - shrink)
            right_w = body.w - left_w - mid_w - gutter * 2
        identity_rect = pygame.Rect(body.x, body.y, left_w, body.h)
        mechanics_rect = pygame.Rect(identity_rect.right + gutter, body.y,
                                     mid_w, body.h)
        lore_rect = pygame.Rect(mechanics_rect.right + gutter, body.y,
                                right_w, body.h)

        if is_corpse:
            identity_lines, mech_lines, lore_text = self._lore_corpse_lines(subject, id_level)
            lore_color = FP.LORE_GOLD_BODY
        else:
            identity_lines = self._lore_item_identity_lines(subject, id_level)
            mech_lines = self._lore_item_mechanic_lines(subject, id_level)
            lore_text = (getattr(subject, 'lore', '') if id_level >= 4 else
                         "The history of this item remains hidden. Identify it to lore tier to read the full record.")
            lore_color = FP.LORE_BLUE_BODY

        focus = getattr(self, '_lore_focus', 'mechanics')
        id_body = self._ui_subpanel(
            identity_rect, "Identity",
            border_color=FP.GOLD if focus == 'identity' else FP.GOLD_DARK)
        mech_body = self._ui_subpanel(
            mechanics_rect, "Mechanics",
            border_color=FP.GOLD if focus == 'mechanics' else FP.GOLD_DARK)
        lore_body = self._ui_subpanel(
            lore_rect, "Lore Reader",
            border_color=FP.GOLD if focus == 'lore' else FP.GOLD_DARK)

        id_render_lines = []
        for text, color, fnt in identity_lines:
            for wrapped in self._ui_text_lines(text, fnt, id_body.w - 10):
                id_render_lines.append((wrapped, color, fnt))
        mech_render_lines = []
        for text, color, fnt in mech_lines:
            for wrapped in self._ui_text_lines(text, fnt, mech_body.w - 10):
                mech_render_lines.append((wrapped, color, fnt))
        lore_font = get_font('body', 17)
        lore_lines = [(line, lore_color, lore_font)
                      for line in self._ui_text_lines(lore_text, lore_font, lore_body.w - 12)]

        self._lore_identity_scroll = self._ui_draw_scroll_lines(
            id_render_lines, self.font_sm, FP.BODY_TEXT, id_body,
            getattr(self, '_lore_identity_scroll', 0), line_gap=4)
        self._lore_mech_scroll = self._ui_draw_scroll_lines(
            mech_render_lines, self.font_sm, FP.BODY_TEXT, mech_body,
            getattr(self, '_lore_mech_scroll', 0), line_gap=4)
        self._lore_text_scroll = self._ui_draw_scroll_lines(
            lore_lines, lore_font, lore_color, lore_body,
            getattr(self, '_lore_text_scroll', 0), line_gap=5)

        action_bits = ["Tab: pane", "Up/Down: scroll"]
        if not is_corpse:
            if isinstance(subject, (Weapon, Armor, Shield, Accessory)):
                action_bits.append("E: equip/unequip")
            if hasattr(subject, 'id_level') and id_level < 5:
                action_bits.append("I: identify")
        action_bits.append("ESC: close")
        self._ui_footer(panel, "   ".join(action_bits))

    def _draw_question_review_browser(self, *, death: bool):
        missed = self.missed_questions if death else getattr(self, '_study_filtered', [])
        if death and not missed:
            self.state = STATE_DEAD
            return

        if death:
            idx = max(0, min(getattr(self, '_review_idx', 0), len(missed) - 1))
            self._review_idx = idx
            title = f"MISSED-QUESTION REVIEW - {idx + 1}/{len(missed)}"
            scroll_attr = '_review_scroll'
        else:
            subj = self._STUDY_SUBJECTS[self._study_subject_idx]
            title = f"STUDY JOURNAL - {subj.upper()} ({len(missed)}/{len(self.missed_questions)})"
            scroll_attr = '_study_scroll'
            if missed:
                idx = max(0, min(getattr(self, '_study_question_idx', 0), len(missed) - 1))
                self._study_question_idx = idx
            else:
                idx = 0

        panel = self._ui_modal_panel(title, border_color=FP.GOLD,
                                     max_w=1360, max_h=728,
                                     center_window=death)
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        gutter = 14

        rail_body = None
        if not death and body.w >= 1000:
            rail_w = 320
            rail = pygame.Rect(body.x, body.y, rail_w, body.h)
            main = pygame.Rect(rail.right + gutter, body.y,
                               body.w - rail_w - gutter, body.h)
            rail_body = self._ui_subpanel(rail, "Missed Subjects")
        else:
            main = body
        main_body = self._ui_subpanel(main, "Review Card")

        if rail_body is not None:
            counts = []
            for subject in self._STUDY_SUBJECTS:
                if subject == 'all':
                    count = len(self.missed_questions)
                else:
                    count = sum(1 for q in self.missed_questions
                                if q.get('subject') == subject)
                if count or subject == 'all':
                    counts.append((subject, count))
            row_h = 40
            y = rail_body.y
            for subject, count in counts:
                if y + row_h > rail_body.bottom:
                    break
                active = subject == self._STUDY_SUBJECTS[self._study_subject_idx]
                rect = pygame.Rect(rail_body.x, y, rail_body.w - 8, row_h - 6)
                pygame.draw.rect(self.screen,
                                 (35, 43, 82) if active else FP.MIDNIGHT,
                                 rect, border_radius=5)
                pygame.draw.rect(self.screen, FP.GOLD if active else FP.GOLD_DARK,
                                 rect, 1, border_radius=5)
                self._ui_blit_text(subject.title(), get_font('small', 14, bold=True),
                                   FP.GOLD_BRIGHT if active else FP.BODY_TEXT,
                                   rect.x + 10, rect.y + 8,
                                   max_width=rect.w - 60)
                self._ui_blit_text(str(count), self.font_sm, FP.FADED_TEXT,
                                   rect.right - 10, rect.y + 8, align='right')
                y += row_h

        if not missed:
            self._ui_blit_text("No missed questions in this subject.",
                               get_font('body', 20), FP.FADED_TEXT,
                               main_body.x, main_body.y + 4,
                               max_width=main_body.w - 12)
            self._ui_footer(panel, "Left/Right: subject   ESC: close")
            return

        q = missed[idx]
        subject = str(q.get('subject', '?')).upper()
        counter = f"{idx + 1} of {len(missed)}"
        lines = [
            (subject, FP.CYAN_ACCENT, get_font('small', 14, bold=True)),
            (counter, FP.FADED_TEXT, self.font_sm),
            ("Question", FP.GOLD_BRIGHT, self.font_sm),
            (q.get('question', ''), FP.PARCHMENT_LIGHT, get_font('body', 20)),
            ("Your answer", FP.DANGER_TEXT_LIGHT, self.font_sm),
            (q.get('chosen', ''), FP.BODY_TEXT, self.font_sm),
            ("Correct answer", FP.SUCCESS_TEXT, self.font_sm),
            (q.get('correct', ''), FP.BODY_TEXT, self.font_sm),
        ]
        context = q.get('context', '')
        if context:
            lines += [
                ("Context", FP.GOLD_BRIGHT, self.font_sm),
                (context, FP.BODY_TEXT, get_font('body', 17)),
            ]

        render_lines = []
        for text, color, fnt in lines:
            if text == "":
                render_lines.append(("", color, fnt))
                continue
            for line in self._ui_text_lines(text, fnt, main_body.w - 14):
                render_lines.append((line, color, fnt))
            if color in (FP.GOLD_BRIGHT, FP.DANGER_TEXT_LIGHT, FP.SUCCESS_TEXT):
                render_lines.append(("", color, fnt))

        scroll = self._ui_draw_scroll_lines(
            render_lines, self.font_sm, FP.BODY_TEXT, main_body,
            getattr(self, scroll_attr, 0), line_gap=5)
        setattr(self, scroll_attr, scroll)

        if death:
            footer = "Left/Right: previous/next   PgUp/PgDn: scroll card   ESC: back to score"
        else:
            footer = "Left/Right: subject   Up/Down: question   PgUp/PgDn: scroll card   ESC: close"
        self._ui_footer(panel, footer)

    def _draw_study_journal(self):
        self._draw_question_review_browser(death=False)
        return
        """Draw the in-game study journal overlay — one question at a time."""
        draw_overlay(self.screen, 190)
        missed = self._study_filtered
        subj = self._STUDY_SUBJECTS[self._study_subject_idx]
        W, H = layout.GAME_W, layout.WINDOW_H
        total = len(self.missed_questions)
        filtered = len(missed)

        bw = min(840, W - 40)
        bh = min(620, H - 40)
        bx = (W - bw) // 2
        by = (H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="STUDY JOURNAL", font=self.font_md, text_color=FP.GOLD_BRIGHT)

        y = by + 52
        # Subject selector
        selector_text = f"<<  {subj.upper()}  ({filtered}/{total})  >>"
        sel_surf = self.font_md.render(selector_text, True, FP.GOLD_BRIGHT)
        self.screen.blit(sel_surf, (bx + (bw - sel_surf.get_width()) // 2, y))
        y += 32
        draw_divider(self.screen, bx + 15, y, bw - 30)
        y += 10

        if not missed:
            empty_msg = "No missed questions in this category."
            self.screen.blit(
                self.font_md.render(empty_msg, True, FP.FADED_TEXT),
                (bx + (bw - self.font_md.size(empty_msg)[0]) // 2, y + 40))
        else:
            idx = min(getattr(self, '_study_question_idx', 0), len(missed) - 1)
            q = missed[idx]

            # Counter + subject badge
            counter = f"{idx + 1}/{len(missed)}"
            badge = q['subject'].upper()
            self.screen.blit(self.font_sm.render(badge, True, FP.HINT_TEXT), (bx + 25, y))
            ctr_surf = self.font_sm.render(counter, True, FP.FADED_TEXT)
            self.screen.blit(ctr_surf, (bx + bw - 25 - ctr_surf.get_width(), y))
            y += 24

            # Question text
            q_lines = wrap_text(q['question'], self.font_md, bw - 50)
            for line in q_lines:
                if y > by + bh - 120:
                    break
                self.screen.blit(self.font_md.render(line, True, FP.PARCHMENT_LIGHT), (bx + 25, y))
                y += 28
            y += 10

            # Your answer (red) vs correct (green)
            chosen_lines = wrap_text(f"Your answer:    {q['chosen']}", self.font_sm, bw - 50)
            for line in chosen_lines:
                if y > by + bh - 80:
                    break
                self.screen.blit(self.font_sm.render(line, True, FP.DANGER_TEXT), (bx + 25, y))
                y += 22
            correct_lines = wrap_text(f"Correct answer: {q['correct']}", self.font_sm, bw - 50)
            for line in correct_lines:
                if y > by + bh - 60:
                    break
                self.screen.blit(self.font_sm.render(line, True, FP.SUCCESS_TEXT), (bx + 25, y))
                y += 22
            y += 8

            # Context
            context = q.get('context', '')
            if context and y < by + bh - 55:
                draw_divider(self.screen, bx + 20, y, bw - 40)
                y += 10
                ctx_lines = wrap_text(context, self.font_sm, bw - 50)
                for line in ctx_lines:
                    if y > by + bh - 45:
                        break
                    self.screen.blit(self.font_sm.render(line, True, FP.BODY_TEXT), (bx + 25, y))
                    y += 22

        # Navigation hints
        hints = "Left/Right: category  |  Up/Down: question  |  ESC: close"
        hint_surf = self.font_sm.render(hints, True, FP.HINT_TEXT)
        self.screen.blit(hint_surf, (bx + (bw - hint_surf.get_width()) // 2, by + bh - 28))

    def _draw_review_missed(self):
        self._draw_question_review_browser(death=True)
        return
        """Page through missed questions with educational context."""
        draw_overlay(self.screen, 190)
        missed = self.missed_questions
        if not missed:
            self.state = STATE_DEAD
            return

        idx = getattr(self, '_review_idx', 0)
        q = missed[idx]
        W, H = layout.GAME_W, layout.WINDOW_H

        bw = min(800, W - 40)
        bh = min(600, H - 40)
        bx = (W - bw) // 2
        by = (H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=f"REVIEW MISSED QUESTIONS  ({idx + 1}/{len(missed)})",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        y = by + 58

        # Subject badge
        subj_text = q['subject'].upper()
        subj_surf = self.font_sm.render(subj_text, True, FP.FADED_TEXT)
        self.screen.blit(subj_surf, (bx + 20, y))
        y += 28

        # Question
        q_lines = self._wrap_text(q['question'], self.font_md, bw - 50)
        for line in q_lines:
            self.screen.blit(self.font_md.render(line, True, FP.PARCHMENT_LIGHT), (bx + 25, y))
            y += 28
        y += 10

        # Your answer vs correct (wrap to panel width)
        chosen_lines = self._wrap_text(f"Your answer:    {q['chosen']}", self.font_sm, bw - 50)
        for line in chosen_lines:
            self.screen.blit(self.font_sm.render(line, True, FP.DANGER_TEXT), (bx + 25, y))
            y += 22
        correct_lines = self._wrap_text(f"Correct answer: {q['correct']}", self.font_sm, bw - 50)
        for line in correct_lines:
            self.screen.blit(self.font_sm.render(line, True, FP.SUCCESS_TEXT), (bx + 25, y))
            y += 22
        y += 8

        # Context
        context = q.get('context', '')
        if context:
            draw_divider(self.screen, bx + 20, y, bw - 40)
            y += 14
            ctx_lines = self._wrap_text(context, self.font_sm, bw - 50)
            for line in ctx_lines:
                self.screen.blit(self.font_sm.render(line, True, FP.BODY_TEXT), (bx + 25, y))
                y += 22

        # Navigation hint
        hint_parts = []
        if idx > 0:
            hint_parts.append("Left: prev")
        if idx < len(missed) - 1:
            hint_parts.append("Right: next")
        hint_parts.append("ESC: back to score")
        hint = self.font_sm.render("  |  ".join(hint_parts), True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 30))

    def _draw_lore_screen(self):
        self._draw_lore_dossier_screen()
        return
        subject = getattr(self, '_lore_subject', None)
        if not subject:
            return

        is_corpse = isinstance(subject, Corpse)

        # Palette per type — both families live in FP so refactors propagate.
        if is_corpse:
            border_col = FP.LORE_GOLD_BORDER
            stat_col   = FP.LORE_GOLD_STAT
            lore_col   = FP.LORE_GOLD_BODY
            title_col  = FP.LORE_GOLD_TITLE
        else:
            border_col = FP.LORE_BLUE_BORDER
            stat_col   = FP.LORE_BLUE_STAT
            lore_col   = FP.LORE_BLUE_BODY
            title_col  = FP.LORE_BLUE_TITLE

        from panel import PanelBuilder, SIZE_LG
        from text_layout import wrap_lines

        if is_corpse:
            # -- CORPSE / BESTIARY ENTRY --------------------------------
            # One-question identify: a corpse is either unstudied (id_level
            # 0 \u2014 name/symbol only) or fully identified (id_level 5 \u2014
            # stats, resistances, family, lore all at once). The >= gates
            # below are kept for old-save corpses stuck at partial levels.
            id_level = int(getattr(subject, 'id_level', 0) or 0)
            _bestiary_state = "identified" if id_level >= 5 else "unstudied"
            title_text = f"{subject.monster_name.upper()}  --  BESTIARY ({_bestiary_state})"
            mdef = subject.monster_def or {}
            stat_lines: list[str] = []

            # Basic stats are revealed at level 2+.
            if id_level >= 2:
                stat_lines.append(
                    f"HP: {mdef.get('hp', '?')}    THAC0: {mdef.get('thac0', '?')}    "
                    f"Speed: {mdef.get('speed', 1)}"
                )
                for atk in mdef.get('attacks', []) or []:
                    line = (f"  \u2022 {atk.get('name','?').replace('_', ' ')}: "
                            f"{atk.get('damage','?')} ({atk.get('type','physical')})")
                    eff = atk.get('effect')
                    if eff:
                        line += (f"  \u2192 {eff.replace('_', ' ')} "
                                 f"{int(atk.get('effect_chance',0)*100)}%")
                    stat_lines.append(line)
            else:
                stat_lines.append("Stats: not yet discerned. Study further to learn.")

            # Resistances, weaknesses, and family tag at level 3+.
            if id_level >= 3:
                res = mdef.get('resistances', []) or []
                wks = mdef.get('weaknesses', []) or []
                tags = mdef.get('tags', []) or []
                if res:
                    stat_lines.append(f"Resists: {', '.join(res)}")
                if wks:
                    stat_lines.append(f"Weak to: {', '.join(wks)}")
                if tags:
                    from monster_classes import get_monster_family
                    fam = get_monster_family(subject)
                    fam_str = f"  [family: {fam}]" if fam else ""
                    stat_lines.append(f"Tags: {', '.join(tags)}{fam_str}")
            elif id_level >= 2:
                stat_lines.append("Weaknesses & family: study further to reveal.")

            # Ingredient & recipe hints (utility info; gated at id_level >= 2
            # so the player knows whether a corpse is harvestable basically).
            if id_level >= 2:
                from food_system import (load_ingredient_for,
                                          get_recipes_for_ingredient)
                ing_id = subject.ingredient_id
                if ing_id:
                    ing = load_ingredient_for(ing_id)
                    if ing:
                        stat_lines.append(f"Ingredient: {ing.name}  (harvest with H)")
                        best_solo = ing.recipes.get('5', ing.recipes.get('3', {}))
                        if best_solo.get('name'):
                            stat_lines.append(
                                f"Solo cook: {best_solo['name']}  "
                                f"({best_solo.get('sp',0)} SP)"
                            )
                        compound = get_recipes_for_ingredient(ing_id)
                        if compound:
                            from food_system import _raw_ingredients as _ri2
                            _ings2 = _ri2()
                            def _iname(iid): return _ings2.get(iid, {}).get('name', iid)
                            stat_lines.append("Used in recipes:")
                            for r in compound[:4]:
                                ing_str = ', '.join(
                                    _iname(iid) for iid in r.get('ingredients', [])
                                )
                                stat_lines.append(f"  \u2022 {r['name']}  ({ing_str})")
                            if len(compound) > 4:
                                stat_lines.append(f"  ... and {len(compound)-4} more")
                else:
                    stat_lines.append("Ingredient: none (not harvestable)")

            # Lore at level 4+; below that, show a teaser.
            if id_level >= 4:
                lore_text = subject.lore or "No lore recorded."
            else:
                lore_text = ("The history of this creature remains beyond your "
                             "grasp. Study deeper to uncover its tale.")

        else:
            # -- ITEM IDENTIFICATION ENTRY --------------------------------
            # True Name model: TYPE knowledge reveals stats + lore on any
            # copy, so the id_level display gates below treat a known-type
            # item as fully revealed. The aura (BUC) line stays strictly
            # per-instance (buc_known), and the enchant line only shows for
            # an identified instance.
            id_level = int(getattr(subject, 'id_level', 5))
            _instance_known = id_level >= 5
            try:
                if self.player.knows_item_type(subject):
                    id_level = 5
            except Exception:
                pass
            item_class_label = subject.item_class.upper()
            title_text = f"{subject.name.upper()}  --  {item_class_label}"
            stat_lines = []

            # Aura line only when THIS copy's BUC has been sensed.
            if getattr(subject, 'buc_known', False):
                _buc = getattr(subject, 'buc', 'uncursed')
                aura_text = {
                    'blessed': "Aura: blessed (radiates a holy light)",
                    'cursed': "Aura: cursed (a dark aura clings to it)",
                    'uncursed': "Aura: uncursed",
                }.get(_buc, "Aura: unclear")
                stat_lines.append(aura_text)
            elif id_level >= 5 and not _instance_known:
                stat_lines.append("Aura: unknown \u2014 identify THIS copy to read it.")

            # Set membership banner
            if getattr(subject, 'set_id', ''):
                set_label = getattr(subject, 'set_name', subject.set_id)
                stat_lines.append(f">> Part of {set_label} <<")

            # Stat lines below this point are only revealed at id_level >= 3.
            # For uniques at chain 1-2, show a placeholder instead.
            if id_level < 3:
                stat_lines.append("Stats: not yet discerned. Study further to learn its workings.")

            if id_level >= 3 and isinstance(subject, Weapon):
                dmg_types = ', '.join(subject.damage_types) if subject.damage_types else 'physical'
                stat_lines.append(f"Type: {subject.weapon_class}  |  Material: {subject.material}  |  Tier: {subject.tier}")
                stat_lines.append(f"Base Damage: {subject.base_damage}  |  Damage Type: {dmg_types}")
                if subject.two_handed:
                    stat_lines.append("Two-handed  |  Reach: " + str(subject.reach))
                else:
                    stat_lines.append(f"One-handed  |  Reach: {subject.reach}")
                specials = []
                if subject.stun_chance > 0:
                    specials.append(f"Stun {int(subject.stun_chance*100)}%")
                if subject.bleed_chance > 0:
                    specials.append(f"Bleed {int(subject.bleed_chance*100)}%")
                if subject.knockback:
                    specials.append("Knockback")
                if subject.ignore_shield:
                    specials.append("Ignores Shield")
                if subject.crit_multiplier > 1.0:
                    specials.append(f"Perfect Chain Crit x{subject.crit_multiplier:.1f}")
                if specials:
                    stat_lines.append(f"Special: {',  '.join(specials)}")
                if subject.requires_ammo:
                    stat_lines.append(f"Requires Ammo: {subject.requires_ammo}")
                mults = subject.chain_multipliers
                if mults:
                    mult_str = '  '.join(f"x{m:.1f}" for m in mults[:6])
                    stat_lines.append(f"Chain Multipliers: {mult_str}")
                stat_lines.append(f"Value: {subject.value} gold")

            elif id_level >= 3 and isinstance(subject, Armor):
                stat_lines.append(f"Slot: {subject.slot}  |  Material: {subject.material}  |  Tier: {subject.tier}")
                _ench = f"+{subject.enchant_bonus}" if _instance_known else "unrevealed"
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: {_ench}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")
                if subject.damage_resistances:
                    res_str = '  '.join(f"{k}: {int(v*100)}%" for k, v in subject.damage_resistances.items())
                    stat_lines.append(f"Resistances: {res_str}")
                if subject.can_be_cursed:
                    stat_lines.append("WARNING: This item can be cursed.")

            elif id_level >= 3 and isinstance(subject, Shield):
                stat_lines.append(f"Material: {subject.material}  |  Tier: {subject.tier}")
                _ench = f"+{subject.enchant_bonus}" if _instance_known else "unrevealed"
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: {_ench}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")
                if subject.damage_resistances:
                    res_str = '  '.join(f"{k}: {int(v*100)}%" for k, v in subject.damage_resistances.items())
                    stat_lines.append(f"Resistances: {res_str}")

            elif id_level >= 3 and isinstance(subject, Accessory):
                stat_lines.append(f"Slot: {subject.slot}")
                efx = subject.effects
                if efx:
                    eff_str = ', '.join(f"{k}={v}" for k, v in efx.items())
                    stat_lines.append(f"Effects: {eff_str}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")

            elif id_level >= 3 and isinstance(subject, Wand):
                stat_lines.append(f"Effect: {subject.effect.replace('_', ' ')}  |  Power: {subject.power}")
                stat_lines.append(f"Charges: {subject.charges}/{subject.max_charges}")
                stat_lines.append(f"Quiz Threshold: {subject.quiz_threshold} correct answers")

            elif id_level >= 3 and isinstance(subject, Scroll):
                stat_lines.append(f"Effect: {subject.effect.replace('_', ' ')}  |  Power: {subject.power}")
                stat_lines.append(f"Quiz Threshold: {subject.quiz_threshold} correct answers")

            elif id_level >= 3 and isinstance(subject, Food):
                stat_lines.append(f"SP Restored: {subject.sp_restore}  |  HP Restored: {subject.hp_restore}")
                if subject.bonus_type != 'none' and subject.bonus_amount:
                    stat_lines.append(f"Bonus: {subject.bonus_type} {subject.bonus_stat or subject.bonus_effect} +{subject.bonus_amount}")

            elif id_level >= 3 and isinstance(subject, Potion):
                # Effect line: 'heal', 'cure_poison', 'gain_str', etc.
                # Power is a dice expression like '2d8+4' for healing.
                eff_label = subject.effect.replace('_', ' ').title() if subject.effect else 'Unknown'
                stat_lines.append(f"Effect: {eff_label}")
                # '(rolled when quaffed)' is only honest for effects that ROLL a
                # numeric magnitude. gain_level is a fixed count; full_heal/cure
                # carry a sentinel power that shouldn't be shown as a magnitude.
                _rolled_mag = ('heal', 'extra_heal', 'restore_sp', 'restore_mp', 'brilliance_mp')
                _p = str(subject.power) if subject.power else ''
                if subject.effect == 'gain_level' and _p:
                    stat_lines.append(f"Levels gained: {_p}")
                elif subject.effect in _rolled_mag and _p:
                    if 'd' in _p.lower():
                        stat_lines.append(f"Magnitude: {_p}  (rolled when quaffed)")
                    else:
                        stat_lines.append(f"Magnitude: {_p}")
                if subject.duration:
                    stat_lines.append(f"Duration: {subject.duration} turns")
                else:
                    stat_lines.append("Duration: instant")

            elif id_level >= 3 and isinstance(subject, Ammo):
                stat_lines.append(f"Ammo Type: {subject.ammo_type}  |  Tier: {subject.tier}")
                stat_lines.append(f"Damage Bonus: +{subject.damage_bonus}  |  Count: {subject.count_min}-{subject.count_max}")

            elif id_level >= 3 and isinstance(subject, Spellbook):
                spell_name = getattr(subject, 'spell_name', subject.name)
                mp_cost = getattr(subject, 'mp_cost', '?')
                stat_lines.append(f"Spell: {spell_name}  |  MP Cost: {mp_cost}")
                quiz_thr = getattr(subject, 'quiz_threshold', None)
                if quiz_thr is not None:
                    stat_lines.append(f"Quiz Threshold: {quiz_thr} correct answers to learn")

            # Lore only at id_level >= 4. Below that, show a teaser line.
            if id_level >= 4:
                lore_text = subject.lore or "No further records found."
            else:
                lore_text = "The history of this item remains beyond your grasp. Deeper study may yet reveal it."

        # --- Render through PanelBuilder ---
        p = PanelBuilder(self.screen, size=SIZE_LG, border_color=border_col)
        p.set_title(title_text, font=get_font('heading', 22))
        p.set_footer_hint("ESC / ENTER / SPACE to close")
        body = p.body_rect()

        font_sm = self.font_sm
        line_h = font_sm.get_height() + 4
        # Stat lines fill the top ~55% of body
        stat_bottom = body.y + int(body.h * 0.55)
        stat_y = body.y
        skipped_lines = 0
        for line in stat_lines:
            wrapped = wrap_lines(line, body.w - 8, font_sm)
            for wl in wrapped:
                if stat_y + line_h > stat_bottom:
                    skipped_lines += 1
                    continue
                self.screen.blit(font_sm.render(wl, True, stat_col),
                                 (body.x + 4, stat_y))
                stat_y += line_h
        if skipped_lines:
            self.screen.blit(
                font_sm.render(f"  ... {skipped_lines} more line(s)", True, FP.FADED_TEXT),
                (body.x + 4, stat_y))
            stat_y += line_h

        ly = max(stat_y + 4, stat_bottom + 6)
        pygame.draw.line(self.screen, border_col,
                         (body.x, ly), (body.right, ly), 1)
        ly += 8
        lore_hdr = font_sm.render("-- LORE --", True, border_col)
        self.screen.blit(lore_hdr,
                         (body.x + (body.w - lore_hdr.get_width()) // 2, ly))
        ly += line_h

        for wl in wrap_lines(lore_text, body.w - 8, font_sm):
            if ly + line_h > body.bottom:
                break
            self.screen.blit(font_sm.render(wl, True, lore_col),
                             (body.x + 4, ly))
            ly += line_h

        p.draw()

    # ------------------------------------------------------------------
    # Examine menu  (x key)
    # ------------------------------------------------------------------
    # Drop-item menu  (D key)
    # ------------------------------------------------------------------

    def _draw_drop_gold_input(self):
        """Draw a numeric entry overlay to choose how much gold to drop."""
        have = getattr(self, 'player_gold', 0)
        self._ui_input_card(
            "DROP GOLD",
            f"You have {have} gold. Enter the amount to drop on your current tile.",
            self.drop_gold_input or "0",
            "Digits: amount   |   Enter: confirm   |   Esc: cancel",
            border_color=FP.GOLD,
            max_w=600,
        )
        return

        from fantasy_ui import draw_input_box
        draw_overlay(self.screen, 190)
        bw, bh = 400, 160
        bx = (layout.GAME_W - bw) // 2
        # WINDOW_H (full window) not GAME_H (excludes message log) — matches
        # every other input modal so the drop-gold popup sits at the same
        # vertical center as drop-item, pet-name, etc.
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))

        title = self.font_lg.render("DROP GOLD", True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + 14))

        have = getattr(self, 'player_gold', 0)
        sub = self.font_sm.render(f"You have {have} gold", True, FP.FADED_TEXT)
        self.screen.blit(sub, (bx + (bw - sub.get_width()) // 2, by + 44))

        draw_input_box(self.screen, (bx + 60, by + 76, bw - 120, 34),
                       self.drop_gold_input or "0", self.font_md)

        hint = self.font_sm.render("ENTER to confirm  |  ESC to cancel", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 26))

    def _draw_drop_qty_input(self):
        """Numeric entry overlay: how many of a stacked item to drop."""
        item = getattr(self, '_drop_qty_item', None)
        have = getattr(item, 'count', 1) if item else 0
        name = self._display_name(item) if item else 'items'
        self._ui_input_card(
            "DROP HOW MANY?",
            f"You have {have} {name}. Blank entry drops the whole stack.",
            self.drop_qty_input or str(have),
            "Digits: quantity   |   Enter: confirm   |   Esc: cancel",
            border_color=FP.GOLD,
            max_w=680,
        )
        return

        from fantasy_ui import draw_input_box
        draw_overlay(self.screen, 190)
        bw, bh = 400, 160
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))

        title = self.font_lg.render("DROP HOW MANY?", True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + 14))

        sub = self.font_sm.render(f"You have {have} {name}", True, FP.FADED_TEXT)
        self.screen.blit(sub, (bx + (bw - sub.get_width()) // 2, by + 44))

        draw_input_box(self.screen, (bx + 60, by + 76, bw - 120, 34),
                       self.drop_qty_input or str(have), self.font_md)

        hint = self.font_sm.render("ENTER for all  |  ESC to cancel", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 26))

    def _weapon_mechanic_detail_lines(self, item) -> list:
        """Display lines describing a weapon's class-mechanic: a NAME line plus
        wrapped DESCRIPTION lines (e.g. 'Master Strike' + what it does).

        Returns an empty list for non-weapons, weapons with no mechanic, or a
        weapon whose class isn't known yet (idl < 3). Used by the Examine menu
        so players can read what their weapon does, not just its name.
        """
        from items import Weapon
        if not isinstance(item, Weapon):
            return []
        mech = getattr(item, 'class_mechanic', None)
        if not mech:
            return []
        if self._kit_visible_level(item) < 3:
            return []
        from combat import class_mechanic_info
        info = class_mechanic_info(mech)
        if not info:
            return []
        name, desc = info
        lines = [f"• {name}"]
        if desc:
            lines += (self._wrap_text(desc, self.font_sm, 660) or [desc])
        return lines

    def _draw_examine_menu(self):
        tab_items = self._get_examine_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            details = self._menu_item_detail_lines(
                item,
                "Open the lore/detail page for this item.")
            _mech_lines = self._weapon_mechanic_detail_lines(item)
            if _mech_lines:
                details += [("Weapon class mechanic", FP.GOLD_BRIGHT, self.font_sm)]
                details += [(line, FP.BODY_TEXT, self.font_sm) for line in _mech_lines]
            entries.append({
                'name': self._display_name(item),
                'detail': self._get_item_stats_brief(item),
                'key': self._menu_letter(i),
                'icon': item,
                'details': details,
            })

        _exam_counts = [sum(1 for it in self.examine_menu_items if filt(it))
                        for _, filt in self._EXAMINE_TABS]
        selected = self._menu_clamp_selection('_examine_sel', len(entries))
        context = self._menu_base_context([
            ("EXAMINE", FP.GOLD_BRIGHT, self.font_sm),
            ("This is the safe place to read item mechanics before using them in combat.",
             FP.BODY_TEXT, self.font_sm),
            (f"Known items in tab: {len(entries)}", FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="EXAMINE ITEM",
            entries=entries,
            selected=selected,
            context_lines=context,
            tabs=self._EXAMINE_TABS,
            active_tab=self._examine_tab,
            tab_counts=_exam_counts,
            hint="Left/Right: tab   Up/Down: move   Enter or a-z: open lore   ESC: close",
            border_color=FP.ARCANE_BRIGHT,
            scroll_attr='_examine_scroll',
        )
        return
        entries = []
        for i, item in enumerate(tab_items[:26]):
            entry = {
                'name': self._display_name(item),
                'detail': self._get_item_stats_brief(item),
                'key': self._LETTERS[i],
                'icon': item,
            }
            # Weapons: surface the class-mechanic NAME + full DESCRIPTION on
            # extra detail lines so the Examine view shows what the weapon does.
            _mech_lines = self._weapon_mechanic_detail_lines(item)
            if _mech_lines:
                entry['detail_lines'] = [entry['detail']] + _mech_lines
            entries.append(entry)

        _exam_counts = [sum(1 for it in self.examine_menu_items if filt(it))
                        for _, filt in self._EXAMINE_TABS]
        draw_menu(
            self.screen,
            title="EXAMINE ITEM",
            entries=entries,
            scroll=getattr(self, '_examine_scroll', 0),
            tabs=self._EXAMINE_TABS,
            active_tab=self._examine_tab,
            tab_counts=_exam_counts,
            hint="Left/Right: tab  |  a-z: select  |  ESC: close",
            border_color=FP.ARCANE_BRIGHT,
            max_width=820,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_shop(self):
        """Draw the merchant shop overlay through grimoire PanelBuilder.

        Frame: standard dark-panel chrome with filigree bars under the title
        (keeps the "merchant tent" flourish flavor from the prior layout).
        """
        m = getattr(self, '_shop_merchant', None)
        if m is None:
            return
        stock = getattr(m, 'stock', []) or []
        prices = getattr(m, 'prices', []) or []
        haggled = getattr(self, '_shop_haggled', set())
        entries = []
        for i, item in enumerate(stock):
            price = prices[i] if i < len(prices) else 0
            affordable = getattr(self, 'player_gold', 0) >= price
            detail = f"{price} gold | wt {getattr(item, 'weight', 0):.1f}"
            if i in haggled:
                detail += " | haggled"
            details = [
                (self._display_name(item), FP.GOLD_BRIGHT, self.font_md),
                (f"Price: {price} gold", FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                 self.font_sm),
                (f"Your gold: {getattr(self, 'player_gold', 0)}", FP.BODY_TEXT, self.font_sm),
                ("Haggle status", FP.GOLD_BRIGHT, self.font_sm),
                ("Already haggled for this item." if i in haggled
                 else "Press H to try to reduce this price before buying.",
                 FP.BODY_TEXT, self.font_sm),
                '',
            ]
            details += self._menu_item_detail_lines(
                item,
                "Press Enter to buy this item if you can afford it.")
            entries.append({
                'name': self._display_name(item),
                'detail': detail,
                'icon': item,
                'name_color': FP.BODY_TEXT if affordable else FP.FADED_TEXT,
                'detail_color': FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                'badge': f"{price}g",
                'badge_color': FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                'details': details,
            })

        selected = self._menu_clamp_selection('_shop_selection', len(entries))
        context = self._menu_base_context([
            ("MERCHANT", FP.GOLD_BRIGHT, self.font_sm),
            (f"Your gold: {getattr(self, 'player_gold', 0)}", FP.GOLD_PALE, self.font_sm),
            (f"Stock remaining: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("Use H before buying if you want one chance to haggle that item.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu_variant_a(
            title="TRAVELLING MERCHANT",
            entries=entries,
            selected=selected,
            context_lines=context,
            hint="Up/Down: inspect   Enter: buy   H: haggle   ESC: close",
            border_color=FP.GOLD,
            scroll_attr='_shop_scroll',
        )
        return
        from fantasy_ui import draw_filigree_bar
        from panel import PanelBuilder, SIZE_MD
        m = getattr(self, '_shop_merchant', None)
        if m is None:
            return

        p = PanelBuilder(self.screen, size=SIZE_MD, border_color=FP.GOLD,
                         max_height=520)
        p.set_title("TRAVELLING MERCHANT", font=get_font('heading', 22))
        p.set_footer_hint("Up/Down navigate   ENTER buy   H haggle   ESC close")
        body = p.body_rect()

        # Filigree under title (decorative flourish)
        draw_filigree_bar(self.screen, body.x, body.y, body.w, FP.GOLD_DARK)

        # Your gold
        gold_s = self.font_sm.render(f"Your gold: {self.player_gold}",
                                     True, FP.GOLD_PALE)
        self.screen.blit(gold_s, (body.x + (body.w - gold_s.get_width()) // 2,
                                  body.y + 14))

        stock = m.stock
        sel   = getattr(self, '_shop_selection', 0)
        row_y = body.y + 50
        row_h = 28
        if not stock:
            empty_s = self.font_md.render("Sold out!", True, FP.FADED_TEXT)
            self.screen.blit(empty_s,
                             (body.x + (body.w - empty_s.get_width()) // 2, row_y))
        else:
            haggled = getattr(self, '_shop_haggled', set())
            for i, (item, price) in enumerate(zip(stock, m.prices)):
                is_sel = (i == sel)
                iname  = getattr(item, 'name', '?')
                wt     = getattr(item, 'weight', 0)
                tag    = " [haggled]" if i in haggled else ""
                line   = f"  {iname}  (wt:{wt:.1f})   {price} gold{tag}"
                fg     = FP.PARCHMENT_LIGHT if is_sel else FP.BODY_TEXT
                if is_sel:
                    bg_surf = pygame.Surface((body.w, row_h), pygame.SRCALPHA)
                    bg_surf.fill((*FP.GOLD_DARK, 80))
                    self.screen.blit(bg_surf, (body.x, row_y - 2))
                prefix = "> " if is_sel else "  "
                from text_layout import truncate_label
                trimmed = truncate_label(prefix + line, body.w - 8, self.font_md)
                line_s = self.font_md.render(trimmed, True, fg)
                self.screen.blit(line_s, (body.x + 4, row_y))
                row_y += row_h

        # Bottom filigree above the footer hint
        draw_filigree_bar(self.screen, body.x, body.bottom - 6, body.w, FP.GOLD_DARK)
        p.draw()

    def _encyclopedia_entry_brief(self, category, entry):
        if not entry:
            return ''
        if category == 'bestiary':
            hp = entry.get('hp', entry.get('max_hp', '?'))
            min_lvl = entry.get('min_level', '?')
            return f"HP {hp} / min level {min_lvl}"
        if category == 'weapon':
            return f"{entry.get('weapon_class', '?')} / {entry.get('base_damage', '?')} damage"
        if category == 'armor':
            return f"{entry.get('slot', 'armor')} / AC {entry.get('ac_bonus', '?')}"
        if category == 'accessory':
            effects = entry.get('effects', {}) or {}
            if 'stat' in effects:
                return f"{effects.get('stat')} {int(effects.get('amount', 0)):+d}"
            if 'status' in effects:
                return f"grants {effects.get('status')}"
            return 'accessory'
        if category in ('wand', 'scroll'):
            return f"effect: {entry.get('effect', '?')}"
        if category == 'spellbook':
            return f"teaches: {entry.get('spell_name', '?')}"
        if category == 'recipes':
            return entry.get('lore', '')
        return ''

    def _encyclopedia_article_lines(self, category, entry):
        if not entry:
            return [("No entry selected.", FP.FADED_TEXT, self.font_sm)]
        name = entry.get('name', entry.get('_id', entry.get('id', '?')))
        lines = [(self._fix_name_case(name), FP.GOLD_PALE, get_font('heading', 24))]
        if category == 'bestiary':
            lines += [
                (f"HP: {entry.get('hp', entry.get('max_hp', '?'))}   THAC0: {entry.get('thac0', '?')}   Speed: {entry.get('speed', 1)}",
                 FP.BODY_TEXT, self.font_sm),
            ]
            res = entry.get('resistances', []) or []
            wks = entry.get('weaknesses', []) or []
            if res:
                lines.append((f"Resists: {', '.join(res)}", FP.CYAN_ACCENT, self.font_sm))
            if wks:
                lines.append((f"Weak to: {', '.join(wks)}", FP.WARNING_TEXT, self.font_sm))
            for atk in entry.get('attacks', []) or []:
                line = f"{atk.get('name', '?').replace('_', ' ')}: {atk.get('damage', '?')} ({atk.get('type', 'physical')})"
                if atk.get('effect'):
                    line += f" -> {atk.get('effect').replace('_', ' ')} {int(atk.get('effect_chance', 0) * 100)}%"
                lines.append((line, FP.BODY_TEXT, self.font_sm))
        elif category == 'weapon':
            damage_types = ', '.join(entry.get('damage_types', ['physical']))
            lines += [
                (f"Type: {entry.get('weapon_class', '?')}   Tier: {entry.get('tier', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Damage: {entry.get('base_damage', '?')}   Types: {damage_types}",
                 FP.BODY_TEXT, self.font_sm),
            ]
            if entry.get('two_handed'):
                lines.append(("Two-handed", FP.BODY_TEXT, self.font_sm))
        elif category == 'armor':
            lines.append((f"AC bonus: +{entry.get('ac_bonus', '?')}   Tier: {entry.get('tier', '?')}",
                          FP.BODY_TEXT, self.font_sm))
            if entry.get('slot'):
                lines.append((f"Slot: {entry.get('slot')}", FP.BODY_TEXT, self.font_sm))
        elif category == 'accessory':
            effects = entry.get('effects', {}) or {}
            if effects:
                bits = []
                if 'stat' in effects:
                    bits.append(f"{effects.get('stat')} {int(effects.get('amount', 0)):+d}")
                if 'stat2' in effects:
                    bits.append(f"{effects.get('stat2')} {int(effects.get('amount2', 0)):+d}")
                if 'status' in effects:
                    bits.append(f"grants {effects.get('status')}")
                lines.append(("Effect: " + ', '.join(bits), FP.BODY_TEXT, self.font_sm))
        elif category == 'wand':
            lines += [
                (f"Effect: {entry.get('effect', '?')}", FP.BODY_TEXT, self.font_sm),
                (f"Charges: {entry.get('charges', '?')}/{entry.get('max_charges', '?')}",
                 FP.BODY_TEXT, self.font_sm),
            ]
        elif category == 'scroll':
            lines.append((f"Effect: {entry.get('effect', '?')}", FP.BODY_TEXT, self.font_sm))
        elif category == 'spellbook':
            lines.append((f"Teaches: {entry.get('spell_name', '?')}   MP cost: {entry.get('mp_cost', '?')}",
                          FP.BODY_TEXT, self.font_sm))

        lore = entry.get('lore', '')
        if lore:
            lines += [
                ("Lore", FP.GOLD_BRIGHT, self.font_sm),
                (lore, FP.LORE_BLUE_BODY, get_font('body', 17)),
            ]
        return lines

    def _draw_encyclopedia_browser(self):
        cats = getattr(self, '_ENCYCLOPEDIA_CATS', [
            ('a', 'bestiary', 'Bestiary'),
            ('b', 'weapon', 'Armory'),
            ('c', 'armor', 'Armor'),
            ('d', 'accessory', 'Accessories'),
            ('e', 'scroll', 'Scrolls'),
            ('f', 'wand', 'Wands'),
            ('g', 'spellbook', 'Spellbooks'),
            ('h', 'chronicle', 'Chronicle'),
            ('i', 'lore_hints', 'Lore Hints'),
            ('j', 'recipes', 'Recipes'),
        ])
        category = getattr(self, 'encyclopedia_category', '')
        active_idx = getattr(self, '_encyclopedia_cat_idx', 0)
        for idx, (_key, slug, _label) in enumerate(cats):
            if slug == category:
                active_idx = idx
                self._encyclopedia_cat_idx = idx
                break

        title = "ENCYCLOPEDIA"
        if category:
            label = next((label for _k, slug, label in cats if slug == category),
                         category.title())
            title = f"ENCYCLOPEDIA - {label.upper()}"
        panel = self._ui_modal_panel(title, border_color=FP.GOLD,
                                     max_w=1428, max_h=766)
        body = pygame.Rect(panel.x + 18, panel.y + 70, panel.w - 36,
                           panel.h - 122)
        gutter = 14
        cat_w = min(260, max(220, int(body.w * 0.20)))
        list_w = min(420, max(330, int(body.w * 0.32)))
        cat_rect = pygame.Rect(body.x, body.y, cat_w, body.h)
        list_rect = pygame.Rect(cat_rect.right + gutter, body.y,
                                list_w, body.h)
        article_rect = pygame.Rect(list_rect.right + gutter, body.y,
                                   body.right - (list_rect.right + gutter),
                                   body.h)
        cat_body = self._ui_subpanel(cat_rect, "Categories")
        list_body = self._ui_subpanel(list_rect, "Known Entries")
        article_body = self._ui_subpanel(article_rect, "Article")

        row_h = 45
        y = cat_body.y
        for idx, (key_label, slug, label) in enumerate(cats):
            if y + row_h > cat_body.bottom:
                break
            active = (category and slug == category) or (not category and idx == active_idx)
            rect = pygame.Rect(cat_body.x, y, cat_body.w - 8, row_h - 6)
            pygame.draw.rect(self.screen,
                             (35, 43, 82) if active else FP.MIDNIGHT,
                             rect, border_radius=5)
            pygame.draw.rect(self.screen, FP.GOLD if active else FP.GOLD_DARK,
                             rect, 1, border_radius=5)
            self._ui_blit_text(key_label, get_font('small', 13, bold=True),
                               FP.GOLD_BRIGHT, rect.x + 10, rect.y + 10)
            self._ui_blit_text(label, get_font('small', 14, bold=True),
                               FP.GOLD_BRIGHT if active else FP.BODY_TEXT,
                               rect.x + 36, rect.y + 8,
                               max_width=rect.w - 44)
            y += row_h

        entries = getattr(self, 'encyclopedia_entries', []) or []
        if not category:
            self._ui_wrap_text("No category selected.",
                               self.font_md, FP.BODY_TEXT, article_body)
            self._ui_footer(panel, "Up/Down: category   Enter or a-j: open   ESC: close")
            return

        sel = max(0, min(getattr(self, 'encyclopedia_selection', 0),
                         max(0, len(entries) - 1)))
        self.encyclopedia_selection = sel
        entry_row_h = 60
        visible = max(1, list_body.h // entry_row_h)
        scroll = getattr(self, '_encyclopedia_scroll', 0)
        if sel < scroll:
            scroll = sel
        if sel >= scroll + visible:
            scroll = sel - visible + 1
        scroll = max(0, min(scroll, max(0, len(entries) - visible)))
        self._encyclopedia_scroll = scroll

        if not entries:
            self._ui_wrap_text("No entries discovered in this category yet.",
                               self.font_sm, FP.FADED_TEXT, list_body)
        else:
            y = list_body.y
            for idx, entry in enumerate(entries[scroll:scroll + visible],
                                        start=scroll):
                rect = pygame.Rect(list_body.x, y, list_body.w - 10,
                                   entry_row_h - 7)
                selected = idx == sel
                pygame.draw.rect(self.screen,
                                 (35, 43, 82) if selected else FP.MIDNIGHT,
                                 rect, border_radius=6)
                pygame.draw.rect(self.screen, FP.GOLD if selected else FP.ARCANE_DIM,
                                 rect, 1, border_radius=6)
                name = self._fix_name_case(entry.get('name',
                                                     entry.get('_id', '?')))
                self._ui_wrap_text(name, get_font('small', 15, bold=True),
                                   FP.GOLD_BRIGHT if selected else FP.BODY_TEXT,
                                   pygame.Rect(rect.x + 10, rect.y + 7,
                                               rect.w - 20, 30),
                                   line_gap=0, max_lines=2)
                brief = self._encyclopedia_entry_brief(category, entry)
                if brief:
                    self._ui_blit_text(brief, get_font('small', 12),
                                       FP.FADED_TEXT, rect.x + 10,
                                       rect.bottom - 19,
                                       max_width=rect.w - 20)
                y += entry_row_h
            if len(entries) > visible:
                self._ui_scrollbar(list_body, scroll, len(entries), visible)

        entry = getattr(self, '_encyclopedia_entry', None)
        if entry is None and entries:
            entry = entries[sel]
        lines = self._encyclopedia_article_lines(category, entry)
        render_lines = []
        for text, color, fnt in lines:
            if text == "":
                render_lines.append(("", color, fnt))
                continue
            for line in self._ui_text_lines(text, fnt, article_body.w - 14):
                render_lines.append((line, color, fnt))
            if color in (FP.GOLD_PALE, FP.GOLD_BRIGHT):
                render_lines.append(("", color, fnt))
        self._encyclopedia_article_scroll = self._ui_draw_scroll_lines(
            render_lines, self.font_sm, FP.BODY_TEXT, article_body,
            getattr(self, '_encyclopedia_article_scroll', 0),
            line_gap=5)

        if getattr(self, '_encyclopedia_entry', None) is not None:
            footer = "Up/Down/PgUp/PgDn: scroll article   ESC: list"
        else:
            footer = "Left/Right or a-j: category   Up/Down: entry   Enter: detail   PgUp/PgDn: article   ESC: categories"
        self._ui_footer(panel, footer)

    def _draw_encyclopedia(self):
        self._draw_encyclopedia_browser()
        return
        """Draw the encyclopedia overlay -- category, list, or detail view."""
        _CAT_LABELS = {
            '':          'Encyclopedia',
            'bestiary':  'Bestiary -- Monsters',
            'weapon':    'Armory -- Weapons',
            'armor':     'Armor & Shields',
            'accessory': 'Accessories',
            'scroll':    'Scrolls',
            'wand':      'Wands',
            'spellbook': 'Spellbooks',
            'chronicle': 'Chronicle',
            'lore_hints': 'Lore Hints',
            'recipes':    'Recipes',
        }

        bw = min(900, layout.GAME_W - 40)
        bx = (layout.GAME_W - bw) // 2

        if self.encyclopedia_category == '':
            # -- Category selection screen ---------------------------------
            cats = [
                ('a', 'Bestiary',    'Monsters you have encountered'),
                ('b', 'Armory',      'Weapons'),
                ('c', 'Armor',       'Armor & Shields'),
                ('d', 'Accessories', 'Rings and amulets'),
                ('e', 'Scrolls',     'Scrolls you have read'),
                ('f', 'Wands',       'Wands you have used'),
                ('g', 'Spellbooks',  'Spells you have learned'),
                ('h', 'Chronicle',   'Your journey so far'),
                ('i', 'Lore Hints',  'Knowledge recalled from memory'),
                ('j', 'Recipes',     'Compound recipes you have cooked'),
            ]
            entries = []
            for key_lbl, cat_name, cat_desc in cats:
                entries.append({
                    'name': cat_name,
                    'detail': cat_desc,
                    'key': key_lbl,
                    'row_style': 'text',
                })
            draw_menu(
                self.screen,
                title="ENCYCLOPEDIA",
                entries=entries,
                subtitle="Select a category to browse your discovered knowledge.",
                hint="a-j: select category  |  ESC: close",
                border_color=FP.GOLD,
                max_width=900,
                center_in=(layout.GAME_W, layout.WINDOW_H),
                font_md=self.font_md,
                font_sm=self.font_sm,
                row_style='text',
            )
            return

        header_label = _CAT_LABELS.get(self.encyclopedia_category, self.encyclopedia_category.title())

        if self._encyclopedia_entry is not None:
            # -- Entry detail view -- kept as custom draw since it has
            #    unique lore section layout that doesn't fit draw_menu rows
            draw_overlay(self.screen, 190)
            entry = self._encyclopedia_entry
            bh = min(560, layout.WINDOW_H - 40)
            by = (layout.WINDOW_H - bh) // 2
            draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
            draw_header_bar(self.screen, (bx, by, bw, 44),
                            text=f"ENCYCLOPEDIA -- {header_label.upper()}",
                            font=self.font_md, text_color=FP.GOLD_BRIGHT)
            draw_divider(self.screen, bx + 10, by + 48, bw - 20)

            y = by + 56
            name = entry.get('name', entry.get('_id', '?'))
            name_surf = self.font_lg.render(self._fix_name_case(name), True, FP.GOLD_PALE)
            self.screen.blit(name_surf, (bx + 20, y))
            y += 36

            stat_lines = []
            if self.encyclopedia_category == 'bestiary':
                hp = entry.get('hp', entry.get('max_hp', '?'))
                thac0 = entry.get('thac0', '?')
                speed = entry.get('speed', 1)
                stat_lines.append(f"HP: {hp}    THAC0: {thac0}    Speed: {speed}")
                res = entry.get('resistances', [])
                wks = entry.get('weaknesses', [])
                if res:
                    stat_lines.append(f"Resists: {', '.join(res)}")
                if wks:
                    stat_lines.append(f"Weak to: {', '.join(wks)}")
                for atk in entry.get('attacks', []):
                    line = f"  \u2022 {atk.get('name','?').replace('_', ' ')}: {atk.get('damage','?')} ({atk.get('type','physical')})"
                    eff = atk.get('effect')
                    if eff:
                        line += f"  \u2192 {eff.replace('_', ' ')} {int(atk.get('effect_chance',0)*100)}%"
                    stat_lines.append(line)
                lore_text = entry.get('lore', 'No lore recorded.')
            elif self.encyclopedia_category == 'weapon':
                stat_lines.append(f"Type: {entry.get('weapon_class','?')}  |  Tier: {entry.get('tier','?')}")
                stat_lines.append(f"Damage: {entry.get('base_damage','?')}  |  Types: {', '.join(entry.get('damage_types',['physical']))}")
                if entry.get('two_handed'):
                    stat_lines.append("Two-handed")
                lore_text = entry.get('lore', 'No further records found.')
            elif self.encyclopedia_category in ('armor', 'shield'):
                stat_lines.append(f"AC Bonus: -{entry.get('ac_bonus','?')}  |  Tier: {entry.get('tier','?')}")
                if entry.get('slot'):
                    stat_lines.append(f"Slot: {entry['slot']}")
                lore_text = entry.get('lore', 'No further records found.')
            elif self.encyclopedia_category == 'accessory':
                efx = entry.get('effects', {})
                if 'status' in efx:
                    stat_lines.append(f"Grants: {efx['status']}")
                elif 'stat' in efx:
                    stat_lines.append(f"{efx['stat']} +{efx.get('amount',0)}")
                lore_text = entry.get('lore', 'No further records found.')
            elif self.encyclopedia_category == 'wand':
                stat_lines.append(f"Effect: {entry.get('effect','?')}")
                stat_lines.append(f"Charges: {entry.get('charges','?')}/{entry.get('max_charges','?')}")
                lore_text = entry.get('lore', 'No further records found.')
            elif self.encyclopedia_category == 'scroll':
                stat_lines.append(f"Effect: {entry.get('effect','?')}")
                lore_text = entry.get('lore', 'No further records found.')
            elif self.encyclopedia_category == 'spellbook':
                stat_lines.append(f"Teaches: {entry.get('spell_name','?')}  |  MP Cost: {entry.get('mp_cost','?')}")
                lore_text = entry.get('lore', 'No further records found.')
            else:
                lore_text = entry.get('lore', 'No further records found.')

            # Encyclopedia detail uses the same lore-blue palette as the
            # _draw_lore_screen (item branch) — both live in FP now so a
            # palette refactor propagates to both at once.
            stat_col = FP.LORE_BLUE_STAT
            for line in stat_lines:
                for wl in self._wrap_text(line, self.font_sm, bw - 44) or [line]:
                    surf = self.font_sm.render(wl, True, stat_col)
                    self.screen.blit(surf, (bx + 20, y))
                    y += 22

            y += 6
            pygame.draw.line(self.screen, FP.LORE_BLUE_INNER,
                             (bx + 20, y), (bx + bw - 20, y))
            y += 12
            lore_hdr = self.font_sm.render("-- LORE --", True, FP.LORE_BLUE_BORDER)
            self.screen.blit(lore_hdr, (bx + (bw - lore_hdr.get_width()) // 2, y))
            y += 22

            lore_lines = self._wrap_text(lore_text, self.font_sm, bw - 44)
            for line in lore_lines:
                if y + self.font_sm.get_height() > by + bh - 40:
                    break
                self.screen.blit(self.font_sm.render(line, True, FP.LORE_BLUE_BODY),
                                 (bx + 22, y))
                y += self.font_sm.get_height() + 3

            hint_y = by + bh - 28
            hint = self.font_sm.render("ESC: back to list", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))
            return

        # -- Entry list view -----------------------------------------------
        raw_entries = self.encyclopedia_entries
        sel = self.encyclopedia_selection
        entries = []
        for idx, entry in enumerate(raw_entries):
            entry_name = entry.get('name', entry.get('_id', '?'))
            # Brief extra info
            brief = ''
            if self.encyclopedia_category == 'bestiary':
                hp = entry.get('hp', entry.get('max_hp', '?'))
                min_lvl = entry.get('min_level', '?')
                brief = f"HP {hp}  |  min lvl {min_lvl}"
            elif self.encyclopedia_category == 'weapon':
                brief = f"{entry.get('weapon_class','?')}  {entry.get('base_damage','?')} dmg"
            elif self.encyclopedia_category in ('armor',):
                brief = f"{entry.get('slot','?')}  -{entry.get('ac_bonus','?')} AC"
            elif self.encyclopedia_category == 'wand':
                brief = f"effect: {entry.get('effect','?')}"
            elif self.encyclopedia_category == 'scroll':
                brief = f"effect: {entry.get('effect','?')}"
            elif self.encyclopedia_category == 'spellbook':
                brief = f"teaches: {entry.get('spell_name','?')}"
            entries.append({
                'name': self._fix_name_case(entry_name),
                'selected': idx == sel,
                'badge': brief,
                'badge_color': FP.FADED_TEXT,
                'row_style': 'text',
            })
        draw_menu(
            self.screen,
            title=f"ENCYCLOPEDIA -- {header_label.upper()}  ({len(raw_entries)} known)",
            entries=entries,
            scroll=getattr(self, '_encyclopedia_scroll', 0),
            hint="Up/Down: navigate  |  Enter: view details  |  ESC: categories",
            border_color=FP.ARCANE_BRIGHT,
            max_width=900,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            row_style='text',
        )

    def _draw_recall_lore_card(self):
        hint_text = getattr(self, '_lore_hint_text', None)
        chain = getattr(self, '_lore_hint_chain', 0)
        if hint_text is None:
            self.state = STATE_PLAYER
            return
        quality_labels = {
            1: "Vague Recollection",
            2: "Useful Memory",
            3: "Clear Knowledge",
            4: "Deep Lore",
            5: "Ancient Wisdom",
        }
        label = quality_labels.get(chain, "Lore")
        panel = self._ui_modal_panel(f"RECALL LORE - {label}",
                                     border_color=FP.LORE_GOLD_BORDER,
                                     max_w=860,
                                     max_h=340)
        body = pygame.Rect(panel.x + 28, panel.y + 78, panel.w - 56,
                           panel.h - 132)
        self._ui_blit_text("Chain quality", get_font('small', 14, bold=True),
                           FP.GOLD_BRIGHT, body.x, body.y)
        star_x = body.x + 130
        for idx in range(5):
            rect = pygame.Rect(star_x + idx * 34, body.y - 2, 23, 23)
            active = idx < chain
            pygame.draw.rect(self.screen,
                             FP.GOLD_DARK if active else FP.MIDNIGHT,
                             rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.LORE_GOLD_BORDER,
                             rect, 1, border_radius=4)
            if active:
                self._ui_blit_text("*", get_font('small', 15, bold=True),
                                   FP.GOLD_BRIGHT, rect.centerx, rect.y + 2,
                                   align='center')

        text_rect = pygame.Rect(body.x, body.y + 44, body.w, body.h - 58)
        self._ui_wrap_text(hint_text, get_font('body', 18),
                           FP.LORE_GOLD_BODY, text_rect, line_gap=5)
        self._ui_blit_text("Saved to Encyclopedia / Lore Hints",
                           get_font('small', 14), FP.CYAN_ACCENT,
                           body.x, body.bottom - 16,
                           max_width=body.w)
        cd = getattr(self.player, 'recall_lore_cooldown', 0)
        self._ui_footer(panel, f"Next recall in {cd} turns   any key to close")

    def _draw_hint_screen(self):
        self._draw_recall_lore_card()
        return
        """Display a Recall Lore result through the shared grimoire chrome."""
        from panel import PanelBuilder, SIZE_MD
        from text_layout import wrap_lines

        hint_text = getattr(self, '_lore_hint_text', None)
        chain     = getattr(self, '_lore_hint_chain', 0)
        if hint_text is None:
            self.state = STATE_PLAYER
            return

        quality_labels = {1: "Vague Recollection", 2: "Useful Memory",
                          3: "Clear Knowledge", 4: "Deep Lore", 5: "Ancient Wisdom"}
        label = quality_labels.get(chain, "Lore")

        cd = self.player.recall_lore_cooldown
        cd_msg = f"Next recall in {cd} turns   --   any key to close"

        p = PanelBuilder(self.screen, size=SIZE_MD,
                         border_color=FP.LORE_GOLD_BORDER, max_height=320)
        p.set_title(f"RECALL LORE  --  {label}",
                    font=get_font('heading', 22))
        p.set_footer_hint(cd_msg)
        body = p.body_rect()

        # Chain stars row centered just below the header (ASCII for font compat)
        stars = '[*] ' * chain + '[ ] ' * (5 - chain)
        star_font = get_font('body', 16)
        stars_surf = star_font.render(stars.strip(), True, FP.LORE_GOLD_STAT)
        sx = body.x + (body.w - stars_surf.get_width()) // 2
        self.screen.blit(stars_surf, (sx, body.y))

        # Wrap and render the hint body
        body_font = get_font('body', 18)
        text_top = body.y + 28
        text_w = body.w - 12
        lines = wrap_lines(hint_text, text_w, body_font)
        line_h = body_font.get_height() + 4
        y = text_top
        for ln in lines:
            surf = body_font.render(ln, True, FP.LORE_GOLD_BODY)
            self.screen.blit(surf, (body.x + 6, y))
            y += line_h

        p.draw()

    def _draw_debug_overlay(self):
        """Transparent debug HUD showing spawn/balance data for playtesting."""

        font = self.font_sm
        lh = 18  # line height
        pad = 8
        x0 = 6
        y0 = 6

        lines = []
        lines.append(f"=== DEBUG (F2) === v{layout.VERSION}  L{self.dungeon_level}  T{self.turn_count}")

        # -- Player combat stats --
        p = self.player
        ac = p.get_ac() if hasattr(p, 'get_ac') else '?'
        wpn = p.weapon
        wpn_name = wpn.name if wpn else 'unarmed'
        wpn_dmg = getattr(wpn, 'base_damage', 0) if wpn else 0
        lines.append(f"AC:{ac}  Wpn:{wpn_name} ({wpn_dmg}d)  HP:{p.hp}/{p.max_hp}  SP:{p.sp}/{p.max_sp}  MP:{p.mp}/{p.max_mp}")

        # -- Monster pool on this level --
        alive = [m for m in self.monsters if m.alive and not getattr(m, 'is_allied', False)]
        lines.append(f"Monsters alive: {len(alive)}")
        if alive:
            # Count by kind
            from collections import Counter
            kinds = Counter(m.kind for m in alive)
            top3 = kinds.most_common(3)
            top_str = ", ".join(f"{name}x{cnt}" for name, cnt in top3)
            lines.append(f"  Top: {top_str}")
            # Avg HP of alive monsters
            avg_hp = sum(m.hp for m in alive) // len(alive)
            max_hp = max(m.hp for m in alive)
            lines.append(f"  Avg HP:{avg_hp}  Max HP:{max_hp}")

        # -- Items on this floor --
        from collections import Counter as _IC
        item_types = _IC(type(i).__name__ for i in self.ground_items
                        if not getattr(i, 'is_allied', False))
        item_str = ", ".join(f"{t}:{c}" for t, c in item_types.most_common(6))
        lines.append(f"Floor items: {len(self.ground_items)} ({item_str})")

        # -- Inventory summary --
        inv_types = _IC(type(i).__name__ for i in self.player.inventory)
        inv_str = ", ".join(f"{t}:{c}" for t, c in inv_types.most_common(5))
        lines.append(f"Inventory: {len(self.player.inventory)} ({inv_str})")

        # -- Pets --
        live_pets = [pet for pet in self.pets if pet.alive]
        if live_pets:
            pet_str = ", ".join(f"{pet.name} HP:{pet.hp}/{pet.max_hp}" for pet in live_pets)
            lines.append(f"Pets: {pet_str}")

        # -- Quiz stats --
        total_q = self.correct_answers + self.wrong_answers
        acc = f"{self.correct_answers * 100 // max(1, total_q)}%" if total_q else "n/a"
        lines.append(f"Quiz: {self.correct_answers}/{total_q} ({acc})  Missed: {len(self.missed_questions)}")

        # -- Last 5 missed subjects --
        if self.missed_questions:
            recent = self.missed_questions[-5:]
            subjs = [q['subject'][:4] for q in recent]
            lines.append(f"  Recent misses: {' '.join(subjs)}")

        # -- Karma & status --
        karma = getattr(self, 'karma', 0)
        fx = list(p.status_effects.keys())[:6]
        fx_str = ", ".join(fx) if fx else "none"
        lines.append(f"Karma:{karma:+d}  Effects: {fx_str}")

        # -- Kill count --
        kills = getattr(self.level_mgr, 'monsters_killed', 0) if hasattr(self, 'level_mgr') else 0
        lines.append(f"Kills this run: {kills}  Gold: {getattr(self, 'player_gold', 0)}")

        # -- Zoom mode --
        lines.append(f"Zoom: {self.zoom_mode}  State: {self.state}")

        # Draw background panel
        panel_w = 460
        panel_h = pad * 2 + len(lines) * lh
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (x0, y0))

        # Draw text
        for i, line in enumerate(lines):
            color = (0, 255, 100) if i == 0 else (200, 220, 200)
            surf = font.render(line, True, color)
            self.screen.blit(surf, (x0 + pad, y0 + pad + i * lh))

    def _draw_help_screen(self):
        groups = [
            ("Movement", [
                ("Arrows", "Move / attack", FP.BODY_TEXT),
                (".", "Wait / meditate", FP.BODY_TEXT),
                ("< >", "Use stairs", FP.BODY_TEXT),
                ("Tab", "Cycle zoom", FP.BODY_TEXT),
            ]),
            ("Combat", [
                ("A", "Melee target", FP.BODY_TEXT),
                ("F", "Fire ranged weapon", FP.BODY_TEXT),
                ("T", "Throw item", FP.BODY_TEXT),
                ("V", "Quirk powers", FP.BODY_TEXT),
                ("M / Z", "Cast spell or zap wand", FP.ARCANE_ACCENT),
            ]),
            ("Items", [
                ("E", "Equip / unequip", FP.BODY_TEXT),
                ("X", "Examine known items", FP.BODY_TEXT),
                ("I", "Identify item or study corpse", FP.CYAN_ACCENT),
                ("D", "Drop item / use tile", FP.BODY_TEXT),
                ("U / Q", "Eat food or quaff potion", FP.BODY_TEXT),
                ("R", "Read scroll or spellbook", FP.BODY_TEXT),
            ]),
            ("Knowledge", [
                ("B", "Encyclopedia", FP.BODY_TEXT),
                ("J", "Discoveries", FP.BODY_TEXT),
                ("K", "Kit comparison", FP.BODY_TEXT),
                ("W", "Quirks progress", FP.BODY_TEXT),
                (";", "Study journal", FP.CYAN_ACCENT),
                ("N", "Recall lore", FP.CYAN_ACCENT),
            ]),
            ("World", [
                ("G / ,", "Pick up item", FP.BODY_TEXT),
                ("P", "Pick lock / disarm trap", FP.BODY_TEXT),
                ("Y", "Merchant shop", FP.BODY_TEXT),
                ("\\", "Pray at altar", FP.ARCANE_ACCENT),
                ("O", "Observe cursor", FP.BODY_TEXT),
                ("Shift+P", "Pet menu", FP.BODY_TEXT),
            ]),
            ("System", [
                ("1-4", "Answer quiz", FP.GOLD_BRIGHT),
                ("?", "Command help", FP.BODY_TEXT),
                ("ESC", "Cancel / close", FP.BODY_TEXT),
            ]),
        ]
        panel = self._ui_modal_panel("COMMAND REFERENCE",
                                     border_color=FP.GOLD,
                                     max_w=1380,
                                     max_h=724)
        body = pygame.Rect(panel.x + 24, panel.y + 72, panel.w - 48,
                           panel.h - 124)
        cols = 3 if body.w >= 780 else 2
        gutter = 18
        col_w = (body.w - gutter * (cols - 1)) // cols
        row_gap = 18
        rows = (len(groups) + cols - 1) // cols
        group_h = (body.h - row_gap * (rows - 1)) // rows
        font_key = get_font('small', 14, bold=True)
        font_cmd = get_font('small', 15)

        for idx, (title, commands) in enumerate(groups):
            col = idx % cols
            row = idx // cols
            rect = pygame.Rect(body.x + col * (col_w + gutter),
                               body.y + row * (group_h + row_gap),
                               col_w, group_h)
            self._ui_blit_text(title.upper(), get_font('small', 15, bold=True),
                               FP.GOLD_PALE, rect.x, rect.y)
            pygame.draw.line(self.screen, FP.GOLD_DARK,
                             (rect.x, rect.y + 24), (rect.right, rect.y + 24), 1)
            y = rect.y + 34
            row_h = max(31, (rect.bottom - y) // max(1, len(commands)))
            key_w = 74 if col_w < 360 else 88
            for key_label, desc, color in commands:
                if y + row_h > rect.bottom + 2:
                    break
                key_rect = pygame.Rect(rect.x, y + 2, key_w, 24)
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect,
                                 border_radius=5)
                pygame.draw.rect(self.screen, FP.GOLD_DARK, key_rect, 1,
                                 border_radius=5)
                self._ui_blit_text(key_label, font_key, FP.GOLD_BRIGHT,
                                   key_rect.centerx, key_rect.y + 5,
                                   align='center', max_width=key_rect.w - 8)
                desc_rect = pygame.Rect(key_rect.right + 10, y,
                                        rect.right - key_rect.right - 10,
                                        row_h)
                self._ui_wrap_text(desc, font_cmd, color, desc_rect,
                                   line_gap=0, max_lines=2)
                y += row_h

        self._ui_footer(panel, "? / ESC: close")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

