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
from fantasy_ui import (FP, get_font, draw_dark_panel,
                         draw_header_bar, draw_divider, draw_shadow_text,
                         draw_glow_text, centered_text, draw_overlay,
                         draw_rune_circle, draw_filigree_bar, draw_candle_glow,
                         draw_menu, wrap_text)
from items import (Weapon, Armor, Shield, Corpse, Accessory,
                   Wand, Scroll, Spellbook, Ammo, Food, Potion)
from game_helpers import (
    fit_text as _gh_fit_text,
    wrap_text as _gh_wrap_text,
)
from quiz_engine import QuizMode, QuizState
from spells import LEARNABLE_SPELLS
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_EQUIP_MENU, STATE_ACCESSORY_MENU,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_CONFIRM_EXIT, STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
    STATE_VICTORY, STATE_DEAD, STATE_REVIEW_MISSED,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
    STATE_SPELL_MENU, STATE_HINT, STATE_EXAMINE,
    STATE_ENCYCLOPEDIA, STATE_DROP_MENU, STATE_DROP_GOLD_INPUT,
    STATE_STORY_POPUP, STATE_MYSTERY_APPROACH, STATE_SHOP, STATE_POWER_MENU,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM,
    STATE_THROW_MENU, STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_JUDGMENT, STATE_STUDY,
    STATE_PRAY, STATE_IDENTIFY_MODE,
)


class RenderMixin:
    def _draw_mystery_approach(self):
        """Draw the mystery encounter overlay -- description, requirements, Y/N prompt."""
        from fantasy_ui import get_font
        altar = self._active_mystery_altar
        if altar is None:
            self.state = STATE_PLAYER
            return

        from mystery_system import MYSTERIES
        m = MYSTERIES[altar.mystery_id]

        # Semi-transparent background
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 780, 320
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Panel background
        pygame.draw.rect(self.screen, (18, 12, 6), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(self.screen, altar.color, (bx, by, bw, bh), 2, border_radius=10)
        pygame.draw.rect(self.screen, tuple(max(0, v - 80) for v in altar.color),
                         (bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=8)

        font_title = get_font('heading', 22)
        font_body  = get_font('body', 19)
        font_small = get_font('body', 16)

        # Title bar with symbol
        title_text = f"{altar.symbol}  {m['name'].upper()}  {altar.symbol}"
        title_surf = font_title.render(title_text, True, altar.color)
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 16))

        pygame.draw.line(self.screen, tuple(max(0, v - 60) for v in altar.color),
                         (bx + 30, by + 48), (bx + bw - 30, by + 48))

        # Description (word-wrapped)
        desc_text = m['description']
        words = desc_text.split()
        lines, line = [], []
        max_w = bw - 70
        for word in words:
            test = ' '.join(line + [word])
            if font_body.size(test)[0] > max_w:
                if line:
                    lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(' '.join(line))

        y = by + 62
        for ln in lines:
            surf = font_body.render(ln, True, (230, 215, 180))
            self.screen.blit(surf, (bx + 35, y))
            y += font_body.get_height() + 3

        # Requirements info
        y += 8
        req_lines = []
        ch = m['challenge']
        if ch['mode'] == 'physical':
            req_lines.append("Challenge: Physical endurance")
        else:
            req_lines.append(
                f"Challenge: {ch['subject'].capitalize()}  --  {ch['mode'].replace('_', ' ').title()}"
            )
        if m['key_item']:
            req_lines.append(f"Requires: {m['key_item']['name']}")
        if m.get('gold_cost', 0) > 0:
            req_lines.append(f"Tribute: {m['gold_cost']} gold")
        if m.get('stat_cost'):
            cost_desc = ', '.join(f"{s}{v}" for s, v in m['stat_cost'].items())
            req_lines.append(f"Cost: {cost_desc}")
        if altar.mystery_id == 'cauldron':
            req_lines.append("Requires: 3 prepared meals in inventory")

        for rl in req_lines:
            surf = font_small.render(rl, True, (180, 170, 130))
            self.screen.blit(surf, (bx + 35, y))
            y += font_small.get_height() + 3

        # Prompt
        prompt = "[ Y / Enter ] Accept the challenge     [ N / Esc ] Leave"
        prompt_surf = font_small.render(prompt, True, (120, 180, 120))
        self.screen.blit(prompt_surf,
                         (bx + (bw - prompt_surf.get_width()) // 2, by + bh - 28))

    def _draw_page_indicator(self, items, bx, bw, y):
        """Show item count if list is long."""
        total = len(items)
        if total > 9:
            surf = self.font_sm.render(f"({total} items)", True, FP.HINT_TEXT)
            self.screen.blit(surf, (bx + (bw - surf.get_width()) // 2, y))

    MENU_ICON_SIZE = 32

    def _get_menu_sprite(self, item_id: str) -> 'pygame.Surface':
        """Return a MENU_ICON_SIZE sprite for item_id (no glyph — use _draw_menu_icon for fallback)."""
        if item_id in self._menu_sprite_cache:
            return self._menu_sprite_cache[item_id]
        import os
        from paths import data_path
        SZ = self.MENU_ICON_SIZE
        items_dir = data_path('assets', 'tiles', 'items')
        path = os.path.join(items_dir, f"{item_id}.png")
        if not os.path.exists(path) and item_id.startswith('corpse_'):
            path = os.path.join(items_dir, "corpse.png")
        if os.path.exists(path):
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
        bx = (layout.GAME_W - bw) // 2
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
        hint_surf = font_hint.render("[Enter] to submit  //  [Esc] to cancel", True, (0, 80, 40))
        self.screen.blit(hint_surf, (bx + (bw - hint_surf.get_width()) // 2, by + bh - 30))

    def _draw_xyzzy_confirm(self):
        """Draw the 'WARNING: You are about to hack reality' confirmation."""
        from fantasy_ui import get_font
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 580, 240
        bx = (layout.GAME_W - bw) // 2
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
                color = (80, 80, 80)
            surf = font_btn.render(label, True, color)
            self.screen.blit(surf, (bx_btn, btn_y))

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

        bw, bh = 760, 400
        bx = (layout.GAME_W - bw) // 2
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
            True, (0, 100, 50)
        )
        self.screen.blit(close_surf, (bx + (bw - close_surf.get_width()) // 2, by + bh - 24))

    def _draw_quirks_screen(self):
        from fantasy_ui import get_font
        data = getattr(self, '_quirks_data', [])
        scroll = getattr(self, '_quirks_scroll', 0)

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 900, 700
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Panel background
        pygame.draw.rect(self.screen, (16, 12, 24), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, (140, 100, 200), (bx, by, bw, bh), 2, border_radius=8)
        pygame.draw.rect(self.screen, (70, 50, 100), (bx+3, by+3, bw-6, bh-6), 1, border_radius=6)

        font_title = get_font('heading', 20)
        font_name  = get_font('body', 16)
        font_small = get_font('body', 13)

        unlocked_count = sum(1 for _, _, _, u, _, _ in data if u)
        title_surf = font_title.render(
            f"QUIRKS  ({unlocked_count}/{len(data)} unlocked)", True, (200, 170, 255))
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 10))

        pygame.draw.line(self.screen, (100, 70, 140),
                         (bx + 20, by + 36), (bx + bw - 20, by + 36))

        # Calculate how many entries fit
        # Unlocked entries: 3 lines (name+bar, effect, trigger) = ~48px
        # Locked entries: 2 lines (name, bar) = ~32px
        # Use fixed row height for scrolling simplicity
        ROW_H_LOCKED = 30
        content_top = by + 42
        content_bot = by + bh - 28

        # Clamp scroll
        max_scroll = max(0, len(data) - 1)
        scroll = min(scroll, max_scroll)
        self._quirks_scroll = scroll

        # Render entries
        y = content_top
        for idx in range(scroll, len(data)):
            if y >= content_bot:
                break
            qid, name, pct, unlocked, effect, trigger = data[idx]
            pct_int = int(pct * 100)

            if unlocked:
                # Name in gold
                name_surf = font_name.render(f"{name}", True, (255, 220, 100))
                # Wrap reward and trigger lines
                wrap_w = bw - 48
                eff_lines = self._wrap_text(f"  Reward: {effect}", font_small, wrap_w)
                trig_lines = self._wrap_text(f"  How: {trigger}", font_small, wrap_w)
                needed_h = 18 + len(eff_lines) * 16 + len(trig_lines) * 16 + 4
                if y + needed_h > content_bot:
                    break
                self.screen.blit(name_surf, (bx + 24, y))
                # "UNLOCKED" badge
                badge = font_small.render("UNLOCKED", True, (100, 255, 120))
                self.screen.blit(badge, (bx + bw - 100, y + 2))
                y += 18
                # Effect text (wrapped)
                for el in eff_lines:
                    self.screen.blit(font_small.render(el, True, (180, 220, 180)), (bx + 24, y))
                    y += 16
                # Trigger text (wrapped)
                for tl in trig_lines:
                    self.screen.blit(font_small.render(tl, True, (150, 150, 170)), (bx + 24, y))
                    y += 16
                y += 4
            else:
                needed_h = ROW_H_LOCKED
                if y + needed_h > content_bot:
                    break
                # Name in dim white
                name_surf = font_name.render(self._fit_text(f"{name}", font_name, 650), True, (160, 150, 180))
                self.screen.blit(name_surf, (bx + 24, y))
                # Progress bar
                bar_x = bx + bw - 220
                bar_w = 150
                bar_h = 10
                bar_y = y + 5
                pygame.draw.rect(self.screen, (40, 30, 60), (bar_x, bar_y, bar_w, bar_h))
                fill_w = int(bar_w * pct)
                if fill_w > 0:
                    bar_color = (140, 100, 200) if pct < 1.0 else (100, 255, 120)
                    pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_w, bar_h))
                pygame.draw.rect(self.screen, (80, 60, 120), (bar_x, bar_y, bar_w, bar_h), 1)
                # Percentage text
                pct_surf = font_small.render(f"{pct_int}%", True, (120, 110, 150))
                self.screen.blit(pct_surf, (bar_x + bar_w + 6, y + 1))
                y += ROW_H_LOCKED

        # Footer
        footer = font_small.render(
            "Up/Down: scroll   PgUp/PgDn: jump   ESC: close", True, (90, 80, 120))
        self.screen.blit(footer, (bx + (bw - footer.get_width()) // 2, by + bh - 22))

    def _draw_character_sheet(self):
        from fantasy_ui import FP, get_font
        from items import ARMOR_SLOTS
        from status_effects import EFFECT_INFO

        p = self.player

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 920, 720
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

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
        CYAN   = (120, 210, 240)
        PURPLE = (200, 170, 255)

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
        lines.append((f"  Gold: {self.player_gold}", (255, 215, 80), font_body, False))

        # --- Carry weight ---
        cur_w = p.get_current_weight()
        max_w = p.get_carry_limit()
        pct = cur_w / max_w if max_w > 0 else 0
        w_color = GREEN if pct < 0.7 else (255, 200, 60) if pct < 0.9 else RED
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
                lines.append((f"  {label:8s}: {name}{suffix}", WHITE, font_body, False))
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
            item_passives.append(("Fire Protection", (245, 150, 60),
                                  "50% fire damage reduction (Charmander Stuffie)"))
            fb_cd = p.power_cooldowns.get('stuffie_fire_breath', 0)
            if fb_cd > 0:
                item_passives.append(("Fire Breath", DIM,
                                      f"Cooling down: {fb_cd} turns"))
            else:
                item_passives.append(("Fire Breath", (245, 130, 50),
                                      "Ready (V key > Fire Breath)"))
        if getattr(p, 'amulet_slot', None) and getattr(p.amulet_slot, 'id', '') == 'rands_heart':
            item_passives.append(("Death Ward", (220, 220, 255),
                                  "Prevents one death, restores full HP/MP/SP, clears debuffs (Rand's Heart)"))
        if any(getattr(i, 'id', '') == 'dreamspun_sketchbook' for i in p.inventory):
            sk_cd = p.power_cooldowns.get('sketch_manifest', 0)
            if sk_cd > 0:
                item_passives.append(("Manifest", DIM,
                                      f"Cooling down: {sk_cd} turns"))
            else:
                item_passives.append(("Manifest", (200, 170, 240),
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
                    r_color = (120, 200, 160)
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
                lines.append((f"  {cd}", (200, 180, 100), font_body, False))

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
        draw_overlay(self.screen, 190)

        bw, bh = 600, 320
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=(180, 140, 80))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="A COW",
                        font=self.font_lg, text_color=(255, 215, 80))
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
        from fantasy_ui import get_font, draw_overlay, draw_dark_panel, draw_header_bar

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
                                    max_w, (220, 210, 190), line_h=22)
            footer = font_sm.render("Press ENTER to continue",
                                    True, (120, 120, 120))
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'options':
            y = by + 54
            # Options — all same color, no karma hints
            for i, opt in enumerate(enc['options']):
                label = opt['label']
                col = (210, 200, 180)
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
                                    True, (120, 120, 120))
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'select_item':
            y = by + 54
            header = font.render("Choose an item to give:", True, (220, 210, 190))
            self.screen.blit(header, (bx + 25, y))
            y += 30

            items = self._npc_item_list
            visible = items[self._npc_item_scroll:self._npc_item_scroll + 9]
            for i, item in enumerate(visible):
                dname = self._display_name(item)
                txt = f"[{chr(97 + i)}] {dname}"
                surf = font_sm.render(txt, True, (210, 200, 180))
                self.screen.blit(surf, (bx + 30, y))
                y += 22

            if len(items) > 9:
                scroll_hint = font_sm.render(
                    f"({self._npc_item_scroll + 1}-"
                    f"{min(self._npc_item_scroll + 9, len(items))}"
                    f" of {len(items)}, arrows to scroll)",
                    True, (120, 120, 120))
                self.screen.blit(scroll_hint, (bx + 30, y + 8))

            footer = font_sm.render("Press a-z to select, ESC to go back",
                                    True, (120, 120, 120))
            self.screen.blit(footer,
                             (bx + (bw - footer.get_width()) // 2, by + bh - 35))

        elif phase == 'outcome':
            self._draw_npc_wordwrap(self._npc_outcome_text, font,
                                    bx + 25, by + 54, max_w,
                                    (220, 210, 190), line_h=22)
            footer = font_sm.render("Press ENTER to continue",
                                    True, (120, 120, 120))
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
        from fantasy_ui import get_font, draw_overlay, draw_dark_panel, draw_header_bar

        draw_overlay(self.screen, 190)

        bw, bh = min(780, layout.GAME_W - 40), 360
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Gold border for positive, red for negative
        if self.karma > 0:
            border = (255, 220, 100)
        elif self.karma < 0:
            border = (200, 60, 60)
        else:
            border = (140, 140, 160)

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
                col = border if txt_line.isupper() else (210, 200, 180)
                surf = font.render(txt_line, True, col)
                self.screen.blit(surf, (bx + 30, y))
                y += 24
            y += 6

        # Footer
        y = by + bh - 35
        font_sm = get_font('body', 14)
        footer = font_sm.render("Press ENTER to continue", True, (120, 120, 120))
        self.screen.blit(footer, (bx + (bw - footer.get_width()) // 2, y))

    def render(self):
        cam_x, cam_y = self._camera()
        self.screen.fill((0, 0, 0))

        # Set up renderer view mode each frame
        if self.zoom_mode == 'close':
            self.renderer.set_close_up(
                self.player.x, self.player.y,
                self.dungeon.width, self.dungeon.height,
                layout.GAME_W, layout.GAME_H, tile_size=64)
        elif self.zoom_mode == 'medium':
            self.renderer.set_close_up(
                self.player.x, self.player.y,
                self.dungeon.width, self.dungeon.height,
                layout.GAME_W, layout.GAME_H, tile_size=TILE_SIZE)
        else:
            self.renderer.set_dungeon(
                self.dungeon.width, self.dungeon.height,
                layout.GAME_W, layout.GAME_H)

        game_clip = pygame.Rect(0, 0, layout.GAME_W, layout.GAME_H)
        self.screen.set_clip(game_clip)
        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)
        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)
        for m in self.monsters:
            if m.alive:
                # Ambush monsters are invisible until aware
                if m.ai_pattern == 'ambush' and not getattr(m, '_aware', False):
                    continue
                self.renderer.draw_entity(m.x, m.y, m.color, cam_x, cam_y, self.visible, mid=m.kind)
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
                if m.alive and (m.x, m.y) not in self.visible:
                    self.renderer.draw_entity(m.x, m.y, (70, 70, 120), cam_x, cam_y, None)
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

        self.msg_log.draw(self.screen, 0, layout.GAME_H, layout.GAME_W, layout.MSG_H)
        self.sidebar.draw(self.player, self.dungeon_level, self.turn_count, self.player_gold)

        if self.state == STATE_TARGET:
            self._draw_targeting(cam_x, cam_y)
        elif self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_EQUIP_MENU:
            self._draw_equip_menu()
        elif self.state == STATE_ACCESSORY_MENU:
            self._draw_accessory_menu()
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
        elif self.state == STATE_IDENTIFY_MODE:
            self._draw_identify_menu()
            self._draw_identify_mode_popup()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
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
                if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
                    self.screen.blit(reach_surf, (scr_x, scr_y))

        # Highlight monsters in range
        for m in self._target_candidates:
            scr_x, scr_y = w2s(m.x, m.y)
            if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((255, 100, 60, 70))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (255, 100, 60), (scr_x, scr_y, T, T), 1)

        # Check if there's a valid target at cursor
        target_monster = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
        has_target = target_monster is not None

        # Cursor highlight
        scr_cx, scr_cy = w2s(cx, cy)
        if 0 <= scr_cx < layout.GAME_W and 0 <= scr_cy < layout.GAME_H:
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
        target_monster = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
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
                if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
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
            if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((180, 80, 255, 60))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (180, 80, 255), (scr_x, scr_y, T, T), 1)

        # Cursor
        scr_cx, scr_cy = w2s(cx, cy)
        if 0 <= scr_cx < layout.GAME_W and 0 <= scr_cy < layout.GAME_H:
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
        self.screen.blit(label_bg, (8, layout.GAME_H - label_surf.get_height() - 16))
        self.screen.blit(label_surf, (16, layout.GAME_H - label_surf.get_height() - 12))

    def _draw_ranged_targeting(self, cam_x: int, cam_y: int):
        """Draw trajectory line and cursor highlight for ranged targeting."""
        from combat import _line_of_sight
        T   = self.renderer.map_tile_size
        w2s = self.renderer.world_to_screen
        px, py = self.player.x, self.player.y
        cx, cy = self.target_cursor_x, self.target_cursor_y

        # Check LoS and whether there's a target at cursor
        has_los = _line_of_sight(px, py, cx, cy, self.dungeon)
        target_monster = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
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
                if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
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
            if 0 <= scr_x < layout.GAME_W and 0 <= scr_y < layout.GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((255, 200, 0, 60))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (255, 200, 0), (scr_x, scr_y, T, T), 1)

        # Cursor highlight on target tile
        scr_cx, scr_cy = w2s(cx, cy)
        if 0 <= scr_cx < layout.GAME_W and 0 <= scr_cy < layout.GAME_H:
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
        self.screen.blit(label_bg, (8, layout.GAME_H - label_surf.get_height() - 16))
        self.screen.blit(label_surf, (16, layout.GAME_H - label_surf.get_height() - 12))

    _SUBJECT_COLOR = {
        'math':       (0,   220, 255),
        'geography':  (0,   200,  80),
        'history':    (220, 180,   0),
        'animal':     (220, 110,  20),
        'cooking':    (220,  40, 180),
        'science':    (80,  100, 255),
        'philosophy': (200, 200, 220),
        'grammar':    (220,  50,  50),
        'economics':  (160, 220,   0),
        'theology':   (200, 170,  80),
        'trivia':     (255, 200, 100),
        'ai':         (0,   220, 120),
    }

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

        # Question text (wrapped) -- calculate height first
        q_font    = self.font_md
        q_text    = qe.current_question.get('question', '')
        q_lines   = self._wrap_text(q_text, q_font, bw - PAD * 2)
        q_line_h  = q_font.get_height() + 4
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
        draw_header_bar(self.screen, (bx, by, bw, HEADER_H),
                        text=self.quiz_title, font=self.font_md,
                        text_color=FP.GOLD_BRIGHT, accent=accent)

        # Mode / progress counter (top-right)
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            c_text, c_color = f"Chain x{qe.chain}", (80, 255, 140)
        else:
            c_text  = f"{qe.correct_count} / {qe.required}"
            c_color = (120, 200, 255)
        c_surf = self.font_md.render(c_text, True, c_color)
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

        ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))
        t_color = (
            (40, 210, 80)  if ratio > 0.55 else
            (210, 160, 40) if ratio > 0.28 else
            (210, 50,  50)
        )
        pygame.draw.rect(self.screen, (28, 10, 10), (bar_x, ty, bar_w, bar_h), border_radius=4)
        if ratio > 0:
            pygame.draw.rect(self.screen, t_color,
                             (bar_x, ty, max(4, int(bar_w * ratio)), bar_h), border_radius=4)
        # Tick marks every 20%
        for tick in range(1, 5):
            tx = bar_x + int(bar_w * tick / 5)
            pygame.draw.line(self.screen, (0, 0, 0), (tx, ty), (tx, ty + bar_h), 1)

        # Timer seconds label -- right-aligned inside the bar
        secs = int(qe.time_remaining)
        t_label = self.font_sm.render(f"{secs}s", True, (255, 255, 255))
        lx = bar_x + bar_w - t_label.get_width() - 4
        ly = ty + (bar_h - t_label.get_height()) // 2
        self.screen.blit(t_label, (lx, ly))

        # -- Question text ---------------------------------------------
        qy = ty + TIMER_H
        for line in q_lines:
            surf = q_font.render(line, True, (255, 245, 210))
            self.screen.blit(surf, (bx + PAD, qy))
            qy += q_line_h
        qy += SECTION_GAP

        # Thin separator
        pygame.draw.line(self.screen, accent_dim, (bx + PAD, qy - 4), (bx + bw - PAD, qy - 4))

        # -- Choice cards (2 x 2 grid) ---------------------------------
        correct_str = str(qe.current_question.get('answer', '')).strip().lower()
        selected    = qe.last_answer.strip().lower()
        in_result   = (qe.state == QuizState.RESULT)

        for i, (choice, wrapped_lines) in enumerate(zip(display_choices, c_wrapped)):
            col = i % 2
            row = i // 2
            cx_ = bx + PAD + col * (cw + GAP)
            cy_ = qy + row * (ch_height + GAP)

            c_lower     = str(choice).strip().lower()
            is_correct  = c_lower == correct_str
            is_selected = bool(selected) and c_lower == selected

            if in_result:
                if is_correct:
                    bg_c, bdr_c = (8, 52, 8),    accent if qe.last_correct else (50, 200, 50)
                elif is_selected:
                    bg_c, bdr_c = (62, 8, 8),    (200, 50, 50)
                else:
                    bg_c, bdr_c = (14, 12, 30),  (40, 35, 70)
            else:
                bg_c, bdr_c = (18, 14, 38), (60, 50, 100)

            # Card shadow
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (cx_ + 3, cy_ + 3, cw, ch_height), border_radius=7)
            # Card background
            pygame.draw.rect(self.screen, bg_c, (cx_, cy_, cw, ch_height), border_radius=7)
            # Card border
            pygame.draw.rect(self.screen, bdr_c, (cx_, cy_, cw, ch_height), 2, border_radius=7)
            # Inner bevel (top/left highlight)
            bevel = tuple(min(255, v + 40) for v in bdr_c)
            pygame.draw.line(self.screen, bevel, (cx_+2, cy_+1), (cx_+cw-3, cy_+1))
            pygame.draw.line(self.screen, bevel, (cx_+1, cy_+2), (cx_+1, cy_+ch_height-3))

            # Key hint -- rune-stone style
            key_label = f"[{i+1}]"
            key_surf  = self.font_md.render(key_label, True, accent if not in_result else (100, 100, 100))
            self.screen.blit(key_surf, (cx_ + 10,
                                         cy_ + (ch_height - key_surf.get_height()) // 2))

            # Choice text (wrapped)
            text_color = (
                (120, 255, 120) if in_result and is_correct  else
                (255, 100, 100) if in_result and is_selected else
                (220, 215, 200)
            )
            text_x = cx_ + KEY_W
            text_y = cy_ + (ch_height - len(wrapped_lines) * c_line_h) // 2
            for line in wrapped_lines:
                ls = c_font.render(line, True, text_color)
                self.screen.blit(ls, (text_x, text_y))
                text_y += c_line_h

        # -- Status / feedback bar -------------------------------------
        status_y = qy + 2 * (ch_height + GAP) + SECTION_GAP

        if in_result:
            fb_text  = "*  CORRECT!" if qe.last_correct else "*  WRONG!"
            fb_color = (80, 255, 100) if qe.last_correct else (255, 80, 80)
            fb_surf  = self.font_lg.render(fb_text, True, fb_color)
            self.screen.blit(fb_surf, (bx + (bw - fb_surf.get_width()) // 2, status_y))
        elif qe.state == QuizState.ASKING:
            hint = self.font_sm.render("Press  1  2  3  4  to answer", True, (90, 85, 130))
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, status_y + 10))

        # -- Combat HUD ------------------------------------------------
        if is_combat:
            self._draw_combat_hud(bx, status_y + STATUS_H + SECTION_GAP, bw, accent)

    def _draw_celebration(self):
        """Full-screen clean celebration screen for MAX CHAIN."""
        qe    = self.quiz_engine
        t     = qe.celebration_timer
        pulse = abs(math.sin(t * 6))

        # Pure black background -- quiz modal is gone
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, layout.WINDOW_W, layout.WINDOW_H))

        # Warm pulsing golden glow wash
        glow_ov = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        glow_ov.fill((80, 55, 0, int(50 + 40 * pulse)))
        self.screen.blit(glow_ov, (0, 0))

        # Main "MAX CHAIN!" headline
        cel_font = self.font_xl
        glow_col = (255, int(200 + 55 * pulse), int(40 + 80 * pulse))
        cel_surf = cel_font.render(qe.celebration_text, True, glow_col)
        shadow   = cel_font.render(qe.celebration_text, True, (0, 0, 0))
        cx = (layout.WINDOW_W - cel_surf.get_width())  // 2
        cy = (layout.WINDOW_H - cel_surf.get_height()) // 2 - 40
        self.screen.blit(shadow,   (cx + 5, cy + 5))
        self.screen.blit(cel_surf, (cx, cy))

        # Sub-line
        sub_surf = self.font_lg.render("PERFECT COMBO!", True, (180, 255, 180))
        self.screen.blit(sub_surf,
                         ((layout.WINDOW_W - sub_surf.get_width()) // 2,
                          cy + cel_surf.get_height() + 14))

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
        lx       = bx + 22
        hp_ratio = max(0.0, monster.hp / max(1, monster.max_hp))
        hp_color = (
            (40, 200, 60)  if hp_ratio > 0.50 else
            (210, 160, 40) if hp_ratio > 0.25 else
            (210, 50,  50)
        )
        name_surf = self.font_sm.render(
            f"{monster.name.upper()}   {monster.hp}/{monster.max_hp} HP",
            True, (220, 185, 140)
        )
        self.screen.blit(name_surf, (lx, sy))

        hb_y, hb_w = sy + 18, 260
        pygame.draw.rect(self.screen, (30, 10, 10), (lx, hb_y, hb_w, 12), border_radius=4)
        if hp_ratio > 0:
            pygame.draw.rect(self.screen, hp_color,
                             (lx, hb_y, max(3, int(hb_w * hp_ratio)), 12), border_radius=4)
        pygame.draw.rect(self.screen, (60, 40, 40), (lx, hb_y, hb_w, 12), 1, border_radius=4)

        effects = [e for e, v in monster.status_effects.items() if v > 0]
        if effects:
            eff = self.font_sm.render("  ".join(f"[{e}]" for e in effects[:5]),
                                       True, (220, 220, 60))
            self.screen.blit(eff, (lx, hb_y + 16))

        # -- Right: damage preview + weapon ---------------------------
        rx      = bx + 320
        base    = weapon.base_damage  if weapon else 4
        enchant = weapon.enchant_bonus if weapon else 0
        mults   = weapon.chain_multipliers if weapon else [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        dtypes  = weapon.damage_types if weapon else ['physical']
        dm      = _damage_multiplier(dtypes, monster)

        if dm >= 1.5:
            dm_text, dm_col = "WEAKNESS!", (60, 255, 80)
        elif dm <= 0.5:
            dm_text, dm_col = "RESISTED",  (255, 80, 80)
        else:
            dm_text, dm_col = "/".join(dtypes).upper(), (160, 160, 200)
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
            col   = (int(40 + 215 * heat), int(200 - 150 * heat), int(80 - 60 * heat))
            surf  = self.font_sm.render(label, True, col)
            self.screen.blit(surf, (row1_x, sy + 18))
            row1_x += surf.get_width() + 14
        row2_x = rx
        for label, dmg in parts[3:]:
            heat  = dmg / max_dmg
            col   = (int(40 + 215 * heat), int(200 - 150 * heat), int(80 - 60 * heat))
            surf  = self.font_sm.render(label, True, col)
            self.screen.blit(surf, (row2_x, sy + 34))
            row2_x += surf.get_width() + 14

        w_name = weapon.name if weapon else "bare hands"
        self.screen.blit(
            self.font_sm.render(f"{w_name}", True, (150, 145, 185)), (rx, sy + 52)
        )

    def _draw_equip_menu(self):
        tab_items = self._get_equip_tab_items()
        is_unequip = tab_items is None
        display_items = self.equip_menu_equipped if is_unequip else tab_items

        entries = []
        if is_unequip:
            for i, (slot_name, item) in enumerate(display_items[:26]):
                cursed = getattr(item, 'cursed', False)
                slot_label = slot_name.replace('_', ' ')
                detail = f"[{slot_label}]"
                if cursed:
                    detail += "  CURSED"
                entries.append({
                    'name': self._display_name(item),
                    'detail': detail,
                    'key': self._LETTERS[i],
                    'icon': item,
                    'name_color': FP.DANGER_TEXT if cursed else FP.GOLD_PALE,
                    'detail_color': FP.DANGER_TEXT if cursed else FP.FADED_TEXT,
                    'key_color': FP.WARNING_TEXT,
                })
        else:
            for i, item in enumerate(display_items[:26]):
                if isinstance(item, Weapon):
                    detail = f"{getattr(item, 'weapon_class', 'weapon')}  {item.base_damage}dmg  chain x{item.max_chain_length or '?'}"
                elif isinstance(item, Shield):
                    detail = f"+{item.ac_bonus} AC  {item.material}"
                elif isinstance(item, Armor):
                    detail = f"{getattr(item, 'slot', 'armor')}  +{item.ac_bonus} AC  {item.material}"
                elif isinstance(item, Accessory):
                    if item.identified or item.id in self.player.known_item_ids:
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
                entries.append({
                    'name': self._display_name(item),
                    'detail': detail,
                    'key': self._LETTERS[i],
                    'icon': item,
                })

        _equip_counts = []
        for _, filt in self._EQUIP_TABS:
            if filt is None:
                _equip_counts.append(len(self.equip_menu_equipped))
            else:
                _equip_counts.append(sum(1 for it in self.equip_menu_items if filt(it)))

        draw_menu(
            self.screen,
            title="EQUIP / UNEQUIP",
            entries=entries,
            scroll=getattr(self, '_equip_scroll', 0),
            tabs=self._EQUIP_TABS,
            active_tab=self._menu_tab,
            tab_counts=_equip_counts,
            hint="Arrows: tab  |  a-z: select  |  ESC: cancel",
            border_color=FP.GOLD,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_accessory_menu(self):
        slots_used = sum(1 for s in self.player.accessory_slots if s is not None)
        entries = []
        for i, item in enumerate(self.accessory_menu_items[:26]):
            if item.identified or item.id in self.player.known_item_ids:
                fx = item.effects
                detail_text = f"grants {fx['status']}" if 'status' in fx else f"{fx.get('stat','?')} +{fx.get('amount',0)}"
            else:
                detail_text = "unidentified"
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._LETTERS[i],
                'icon': item,
            })
        draw_menu(
            self.screen,
            title="EQUIP ACCESSORY",
            entries=entries,
            scroll=getattr(self, '_accessory_scroll', 0),
            subtitle=f"Accessory slots: {slots_used}/4",
            hint="a-z: select  |  ESC: cancel",
            border_color=FP.GOLD,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_wand_menu(self):
        entries = []
        for i, item in enumerate(self.wand_menu_items[:26]):
            charge_color = (
                FP.SUCCESS_TEXT if item.charges > item.max_charges // 2
                else FP.WARNING_TEXT if item.charges > 0
                else FP.DANGER_TEXT
            )
            charge_text = f"charges: {item.charges}/{item.max_charges}"
            if item.identified or item.id in self.player.known_item_ids:
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
                'name_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT,
                'detail_color': tier_color,
                'badge': f"{mp_cost} MP",
                'badge_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT,
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
        """8 named prayers. Show lore description only (player extrapolates
        intent). Greyed-out entries are gate-failed or karma-refused; the
        reason is shown in italics on the detail line."""
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
            icon = _PrayerIcon((220, 220, 180) if avail else (120, 120, 100))
            entries.append({
                'name': entry['name'],
                'detail': detail,
                'key': self._LETTERS[i],
                'icon': icon,
                'name_color': name_color,
                'detail_color': FP.BODY_TEXT if avail else (140, 140, 140),
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
            border_color=(220, 200, 100),
            max_width=820,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_scroll_menu(self):
        tab_items = self._get_scroll_tab_items()
        entries = []
        for i, item in enumerate(tab_items[:26]):
            is_book = isinstance(item, Spellbook)
            if is_book:
                known = item.spell_id in self.player.known_spells
                if known:
                    detail_text = f"[KNOWN] {item.spell_name}"
                elif item.identified or item.id in self.player.known_item_ids:
                    detail_text = f"teaches: {item.spell_name}  {item.mp_cost} MP"
                else:
                    detail_text = "spellbook"
            else:
                if item.identified or item.id in self.player.known_item_ids:
                    detail_text = f"effect: {item.effect.replace('_', ' ')}"
                else:
                    detail_text = "unknown effect"
            entries.append({
                'name': self._display_name(item),
                'detail': detail_text,
                'key': self._LETTERS[i],
                'icon': item,
            })

        _scroll_counts = [sum(1 for it in self.scroll_menu_items if filt(it))
                          for _, filt in self._SCROLL_TABS]
        draw_menu(
            self.screen,
            title="READ",
            entries=entries,
            scroll=getattr(self, '_scroll_scroll', 0),
            tabs=self._SCROLL_TABS,
            active_tab=self._scroll_tab,
            tab_counts=_scroll_counts,
            hint="Left/Right: tab  |  a-z: read  |  ESC: cancel",
            border_color=FP.GOLD,
            max_width=760,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_identify_menu(self):
        inv_entries    = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if not is_g and not is_c]
        ground_entries = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if is_g and not is_c]
        corpse_entries = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if is_c]

        entries = []

        def _add_section(src, label, label_color, name_color, detail_suffix=''):
            for idx, (i, item) in enumerate(src):
                if isinstance(item, Corpse):
                    lore_status = "[EXAMINED]" if item.lore_identified else "[UNEXAMINED]"
                    detail_text = f"Corpse  {lore_status}"
                else:
                    type_label = item.item_class.replace('_', ' ').title()
                    tier_lbl = f"  tier {item.quiz_tier}" if hasattr(item, 'quiz_tier') else ""
                    detail_text = f"{type_label}{tier_lbl}{detail_suffix}"
                entry = {
                    'name': self._display_name(item),
                    'detail': detail_text,
                    'key': self._LETTERS[i],
                    'icon': item,
                    'name_color': name_color,
                }
                if idx == 0:
                    entry['section'] = label
                    entry['section_color'] = label_color
                entries.append(entry)

        if inv_entries:
            _add_section(inv_entries, "INVENTORY:", FP.GOLD_BRIGHT, FP.BODY_TEXT)
        if ground_entries:
            _add_section(ground_entries, "ON THE GROUND:", FP.WARNING_TEXT, FP.GOLD_PALE, "  [ground]")
        if corpse_entries:
            _add_section(corpse_entries, "CORPSES (at your feet):", (180, 130, 255), FP.FADED_TEXT)

        draw_menu(
            self.screen,
            title="IDENTIFY ITEM",
            entries=entries,
            scroll=getattr(self, '_identify_scroll', 0),
            subtitle="Requires Philosopher's Shard",
            hint="a-z: select  |  ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
            max_width=820,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=lambda s, item, x, y: self._draw_menu_icon(item, x, y),
        )

    def _draw_cook_menu(self):
        tab_items = self._get_cook_tab_items()
        is_compound = self._COOK_TABS[self._cook_tab][1] == 'compound'
        bw = min(800, layout.GAME_W - 40)
        ICO = self.MENU_ICON_SIZE
        TEXT_X = 70 + ICO + 8
        max_detail_w = bw - TEXT_X - 20

        def _cap(s):
            return s[:1].upper() + s[1:] if s else s

        entries = []
        if is_compound:
            from food_system import _raw_ingredients as _ri
            _ings = _ri()
            def _ing_name(iid): return _ings.get(iid, {}).get('name', iid)
            for i, recipe in enumerate(tab_items[:26]):
                ing_list = ', '.join(_ing_name(iid) for iid in recipe.get('ingredients', []))
                detail = f"Consumes: {ing_list}"
                detail_lines = self._wrap_text(detail, self.font_sm, max_detail_w)
                # Build a lightweight icon proxy for the recipe sprite
                recipe_sprite_id = f"recipe_{recipe.get('id', '')}"
                first_ing = recipe.get('ingredients', [''])[0] if recipe.get('ingredients') else ''
                class _RecipeIcon:
                    def __init__(self2, rid, fing):
                        self2.id = rid
                        self2._fallback = fing
                        self2.color = [110, 220, 100]
                        self2.symbol = '*'
                icon_obj = _RecipeIcon(recipe_sprite_id, first_ing)
                entries.append({
                    'name': _cap(recipe['name']),
                    'detail_lines': detail_lines,
                    'key': self._LETTERS[i],
                    'icon': icon_obj,
                    'name_color': FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
                })
        else:
            for i, item in enumerate(tab_items[:26]):
                base = item.recipes.get('1', item.recipes.get('2', {}))
                dish_name = _cap(base.get('name', '???'))
                entries.append({
                    'name': dish_name,
                    'detail': f"Consumes: {self._display_name(item)}",
                    'key': self._LETTERS[i],
                    'icon': item,
                    'name_color': FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
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
            hint="Left/Right: tab  |  a-z: cook  |  ESC: cancel",
            border_color=FP.SUCCESS_TEXT,
            max_width=800,
            center_in=(layout.GAME_W, layout.WINDOW_H),
            font_md=self.font_md,
            font_sm=self.font_sm,
            draw_icon_fn=_cook_icon,
        )

    def _draw_drop_menu(self):
        tab_items = self._get_drop_tab_items()
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
            hint="Left/Right: tab  |  a-z: eat  |  ESC: cancel",
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
        for i, item in enumerate(items[:26]):
            known = item.identified or item.id in self.player.known_item_ids
            if known:
                eff = item.effect.replace('_', ' ')
                dur = f"  ({item.duration} turns)" if item.duration else ""
                is_good = item.effect in self._BENEFICIAL_EFFECTS
                detail_text = f"{'*' if is_good else 'X'} {eff}{dur}"
                detail_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT
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
        for i, item in enumerate(tab_items[:26]):
            if isinstance(item, Weapon):
                dmg = self._get_weapon_throw_damage(item)
                brk = int(self._get_weapon_break_chance(item) * 100)
                detail_text = f"{dmg} dmg  |  {brk}% break chance"
            elif isinstance(item, Potion):
                known = item.identified or item.id in self.player.known_item_ids
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
        for i, (pid, pdef, uses_rem, cooldown) in enumerate(powers[:26]):
            ready = (cooldown == 0) and (pdef.get('uses', 0) == 0 or uses_rem > 0)
            # Badge
            if pdef.get('uses', 0) > 0:
                badge_txt = f"x{uses_rem} left" if uses_rem > 0 else "USED UP"
                badge_col = FP.SUCCESS_TEXT if uses_rem > 0 else FP.DANGER_TEXT
            else:
                badge_txt = "READY" if cooldown == 0 else f"CD:{cooldown}t"
                badge_col = FP.SUCCESS_TEXT if cooldown == 0 else (200, 160, 80)
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

    def _draw_identify_mode_popup(self):
        """Overlay shown after picking an item in the identify menu.

        Lets the player choose [F] full identify or [B] quick BUC peek. Drawn
        ON TOP of the existing identify menu (which is dimmed by the overlay).
        """
        item = getattr(self, '_identify_mode_item', None)
        draw_overlay(self.screen, 190)
        bw, bh = min(620, layout.GAME_W - 40), 220
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="STUDY THE ITEM",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        target_name = self._display_name(item) if item else 'an item'
        sub = f"How will you study the {target_name}?"
        sub_surf = self.font_md.render(self._fit_text(sub, self.font_md, bw - 40), True, FP.BODY_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 58))

        draw_divider(self.screen, bx + 20, by + 96, bw - 40)

        opts = [
            ("F", "Full identify (philosophy chain, full reveal)", FP.GOLD_BRIGHT),
            ("B", "Quick aura read (tier 1 philosophy, BUC only)", FP.HINT_TEXT),
            ("ESC", "Back to selection", FP.FADED_TEXT),
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

    def _draw_confirm_exit(self):
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
        draw_overlay(self.screen, 190)
        bw, bh = min(600, layout.GAME_W - 40), 180
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 40),
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
        draw_overlay(self.screen, 190)
        bw, bh = min(560, layout.GAME_W - 40), 180
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 40),
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

    def _draw_victory_screen(self):
        # FANTASY: Illuminated manuscript victory screen
        draw_overlay(self.screen, 190, (12, 10, 0))
        score = self._calc_score()
        grade, grade_col = self._get_grade(score)
        cx    = layout.GAME_W // 2
        cy    = layout.WINDOW_H // 2

        # FANTASY: Animated rune circles
        t = pygame.time.get_ticks() / 1000.0
        draw_rune_circle(self.screen, cx, cy, 280, (*FP.GOLD_DARK, 120), t, 16)
        draw_rune_circle(self.screen, cx, cy, 190, (*FP.GOLD, 90),       -t * 1.3, 10)
        draw_candle_glow(self.screen, cx, cy, 0.9)

        # Title
        draw_filigree_bar(self.screen, cx - 320, cy - 152, 640, FP.GOLD)
        centered_text(self.screen, self.font_xl, "VICTORY!", FP.GOLD_BRIGHT, cy - 192, shadow=True)
        draw_glow_text(self.screen, self.font_lg,
                       "You retrieved the Philosopher's Stone!",
                       FP.PARCHMENT_LIGHT, (cx - 320, cy - 152))
        draw_filigree_bar(self.screen, cx - 320, cy - 122, 640, FP.GOLD_DARK)

        # Grade badge
        grade_surf = self.font_xl.render(grade, True, grade_col)
        self.screen.blit(grade_surf, (cx - 240, cy - 100))

        # Score
        score_text = f"Final Score:  {score:,}"
        draw_shadow_text(self.screen, self.font_lg, score_text,
                         FP.GOLD_BRIGHT, (cx - self.font_lg.size(score_text)[0]//2 + 20, cy - 96))

        # Stats table
        total_q = self.correct_answers + self.wrong_answers
        acc_pct  = int(100 * self.correct_answers / total_q) if total_q else 0
        row_y    = cy - 52
        row_gap  = 26
        stats = [
            ("Turns Survived",        f"{self.turn_count:,}",                FP.BODY_TEXT),
            ("Deepest Level",         f"{self.level_mgr.max_level_reached}",  FP.BODY_TEXT),
            ("Monsters Slain",        f"{self.level_mgr.monsters_killed:,}",  FP.BODY_TEXT),
            ("Gold Collected",        f"{self.player_gold:,}",               FP.GOLD_PALE),
            ("Questions Answered",    f"{total_q:,}",                         FP.BODY_TEXT),
            ("Correct  /  Wrong",     f"{self.correct_answers} / {self.wrong_answers}   ({acc_pct}%)",
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]
        lx = cx - 260
        for label, value, col in stats:
            lbl_s = self.font_md.render(label + " :", True, FP.FADED_TEXT)
            val_s = self.font_md.render(value, True, col)
            self.screen.blit(lbl_s, (lx, row_y))
            self.screen.blit(val_s, (lx + 280, row_y))
            row_y += row_gap

        # Score breakdown
        draw_filigree_bar(self.screen, cx - 280, row_y + 4, 560, FP.GOLD_DARK)
        breakdown = (f"({self.turn_count}x10)  +  ({self.level_mgr.max_level_reached}x1000)  +"
                     f"  ({self.level_mgr.monsters_killed}x100)  +  50 000 stone bonus")
        b_surf = self.font_sm.render(breakdown, True, FP.FADED_TEXT)
        self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, row_y + 14))

        # Show player title if earned (e.g., "Paladin")
        title = getattr(self, 'player_title', '')
        if title:
            title_line = f"{self.player_name} the {title}"
            ts = self.font_md.render(title_line, True, FP.GOLD_BRIGHT)
            self.screen.blit(ts, (cx - ts.get_width() // 2, row_y + 10))
            row_y += 26

        # High score: save once, then display top 5
        from highscore_system import add_score, get_top
        if not self._score_saved:
            pname = getattr(self, 'player_name', None) or 'Hero'
            add_score(pname, score, grade,
                      self.level_mgr.max_level_reached,
                      self.level_mgr.monsters_killed,
                      self.turn_count, victory=True)
            self._score_saved = True

        top = get_top(5)
        hs_y = row_y + 56
        hs_title = self.font_sm.render("-- HIGH SCORES --", True, FP.GOLD)
        self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, hs_y))
        hs_y += 20
        for i, e in enumerate(top):
            marker = ">" if e['score'] == score else " "
            hs_line = (f"{marker}{i+1}. {e.get('name','?'):<10}  {e['score']:>8,}  "
                       f"{e.get('grade','?'):>2}  L{e.get('level',0)}")
            col = FP.GOLD_BRIGHT if e['score'] == score else FP.FADED_TEXT
            hs_s = self.font_sm.render(hs_line, True, col)
            self.screen.blit(hs_s, (cx - hs_s.get_width() // 2, hs_y))
            hs_y += 18

        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, hs_y + 6))

    def _draw_death_screen(self):
        # FANTASY: Dark blood-red death screen with animated runes
        draw_overlay(self.screen, 180, (50, 0, 0))
        score = self._calc_score()
        cx    = layout.GAME_W // 2
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

        draw_filigree_bar(self.screen, cx - 300, cy - 152, 600, FP.BURGUNDY_MID)
        draw_glow_text(self.screen, self.font_xl, title_text,
                       FP.BLOOD, (cx - self.font_xl.size(title_text)[0]//2, cy - 192),
                       glow_color=FP.BURGUNDY)
        draw_filigree_bar(self.screen, cx - 300, cy - 122, 600, FP.BURGUNDY_MID)

        sub_surf = self.font_lg.render(sub_text, True, tc)
        self.screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy - 106))

        # Grade badge
        grade_surf = self.font_xl.render(grade, True, grade_col)
        self.screen.blit(grade_surf, (cx - 240, cy - 78))

        # Score
        score_text = f"Final Score:  {score:,}"
        draw_shadow_text(self.screen, self.font_lg, score_text,
                         FP.GOLD_PALE, (cx - self.font_lg.size(score_text)[0]//2 + 20, cy - 74))

        # Stats table
        total_q  = self.correct_answers + self.wrong_answers
        acc_pct  = int(100 * self.correct_answers / total_q) if total_q else 0
        row_y    = cy - 30
        row_gap  = 26
        stats = [
            ("Turns Survived",     f"{self.turn_count:,}",                   FP.BODY_TEXT),
            ("Deepest Level",      f"{self.level_mgr.max_level_reached}",     FP.BODY_TEXT),
            ("Monsters Slain",     f"{self.level_mgr.monsters_killed:,}",     FP.BODY_TEXT),
            ("Gold Collected",     f"{self.player_gold:,}",                   FP.GOLD_PALE),
            ("Questions Answered", f"{total_q:,}",                            FP.BODY_TEXT),
            ("Correct  /  Wrong",  f"{self.correct_answers} / {self.wrong_answers}   ({acc_pct}%)",
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]
        lx = cx - 260
        for label, value, col in stats:
            lbl_s = self.font_md.render(label + " :", True, FP.FADED_TEXT)
            val_s = self.font_md.render(value, True, col)
            self.screen.blit(lbl_s, (lx, row_y))
            self.screen.blit(val_s, (lx + 280, row_y))
            row_y += row_gap

        draw_filigree_bar(self.screen, cx - 260, row_y + 4, 520, FP.BURGUNDY_DARK)

        # High score: save once, then display top 5
        from highscore_system import add_score, get_top
        if not self._score_saved:
            pname = getattr(self, 'player_name', None) or 'Hero'
            add_score(pname, score, grade,
                      self.level_mgr.max_level_reached,
                      self.level_mgr.monsters_killed,
                      self.turn_count, victory=False)
            self._score_saved = True

        top = get_top(5)
        hs_y = row_y + 22
        hs_title = self.font_sm.render("-- HIGH SCORES --", True, FP.BURGUNDY_MID)
        self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, hs_y))
        hs_y += 20
        for i, e in enumerate(top):
            marker = ">" if e['score'] == score else " "
            hs_line = (f"{marker}{i+1}. {e.get('name','?'):<10}  {e['score']:>8,}  "
                       f"{e.get('grade','?'):>2}  L{e.get('level',0)}")
            col = FP.GOLD_PALE if e['score'] == score else FP.FADED_TEXT
            hs_s = self.font_sm.render(hs_line, True, col)
            self.screen.blit(hs_s, (cx - hs_s.get_width() // 2, hs_y))
            hs_y += 18

        # Review missed questions option
        if self.missed_questions:
            review_text = f"Press R to review {len(self.missed_questions)} missed questions"
            review_surf = self.font_md.render(review_text, True, FP.GOLD_BRIGHT)
            self.screen.blit(review_surf, (cx - review_surf.get_width() // 2, hs_y + 8))
            hs_y += 28

        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, hs_y + 6))

    # ------------------------------------------------------------------
    # Post-death missed question review

    def _draw_study_journal(self):
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

        # Your answer vs correct
        self.screen.blit(
            self.font_sm.render(f"Your answer:    {q['chosen']}", True, FP.DANGER_TEXT),
            (bx + 25, y))
        y += 24
        self.screen.blit(
            self.font_sm.render(f"Correct answer: {q['correct']}", True, FP.SUCCESS_TEXT),
            (bx + 25, y))
        y += 30

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
        subject = getattr(self, '_lore_subject', None)
        if not subject:
            return

        is_corpse = isinstance(subject, Corpse)

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = min(1000, layout.GAME_W - 40), min(640, layout.WINDOW_H - 40)
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Background panel
        pygame.draw.rect(self.screen, (8, 6, 20), (bx, by, bw, bh), border_radius=10)
        if is_corpse:
            border_col = (160, 120, 40)
            inner_col  = (80, 60, 20)
            title_col  = (255, 210, 60)
            stat_col   = (200, 185, 140)
            lore_col   = (210, 200, 170)
        else:
            border_col = (80, 120, 200)
            inner_col  = (40, 60, 120)
            title_col  = (160, 210, 255)
            stat_col   = (180, 200, 230)
            lore_col   = (200, 215, 240)

        pygame.draw.rect(self.screen, border_col, (bx, by, bw, bh), 2, border_radius=10)
        pygame.draw.rect(self.screen, inner_col,  (bx+4, by+4, bw-8, bh-8), 1, border_radius=8)

        y = by + 14

        if is_corpse:
            # -- CORPSE / BESTIARY ENTRY ----------------------------------
            title = self.font_lg.render(
                f"{subject.monster_name.upper()} -- BESTIARY", True, title_col
            )
            self.screen.blit(title, (bx + (bw - title.get_width()) // 2, y))
            y += 40
            pygame.draw.line(self.screen, border_col, (bx+20, y), (bx+bw-20, y))
            y += 12

            mdef = subject.monster_def
            stat_lines = [
                f"HP: {mdef.get('hp', '?')}    THAC0: {mdef.get('thac0', '?')}    Speed: {mdef.get('speed', 1)}",
            ]
            res = mdef.get('resistances', [])
            wks = mdef.get('weaknesses', [])
            if res:
                stat_lines.append(f"Resists: {', '.join(res)}")
            if wks:
                stat_lines.append(f"Weak to: {', '.join(wks)}")
            for atk in mdef.get('attacks', []):
                line = f"  \u2022 {atk.get('name','?').replace('_', ' ')}: {atk.get('damage','?')} ({atk.get('type','physical')})"
                eff = atk.get('effect')
                if eff:
                    line += f"  \u2192 {eff.replace('_', ' ')} {int(atk.get('effect_chance',0)*100)}%"
                stat_lines.append(line)

            # -- Ingredient & recipe hints ---------------------------------
            from food_system import load_ingredient_for, get_recipes_for_ingredient
            ing_id = subject.ingredient_id
            if ing_id:
                ing = load_ingredient_for(ing_id)
                if ing:
                    stat_lines.append(f"Ingredient: {ing.name}  (harvest with H)")
                    # Best solo cook result
                    best_solo = ing.recipes.get('5', ing.recipes.get('3', {}))
                    if best_solo.get('name'):
                        stat_lines.append(f"Solo cook: {best_solo['name']}  ({best_solo.get('sp',0)} SP)")
                    # Compound recipes using this ingredient
                    compound = get_recipes_for_ingredient(ing_id)
                    if compound:
                        from food_system import _raw_ingredients as _ri2
                        _ings2 = _ri2()
                        def _iname(iid): return _ings2.get(iid, {}).get('name', iid)
                        stat_lines.append("Used in recipes:")
                        for r in compound[:4]:
                            ing_str = ', '.join(_iname(iid) for iid in r.get('ingredients', []))
                            stat_lines.append(f"  \u2022 {r['name']}  ({ing_str})")
                        if len(compound) > 4:
                            stat_lines.append(f"  ... and {len(compound)-4} more")
            else:
                stat_lines.append("Ingredient: none (not harvestable)")

            lore_text = subject.lore or "No lore recorded."

        else:
            # -- ITEM IDENTIFICATION ENTRY --------------------------------
            # id_level controls progressive reveal for uniques. Non-uniques
            # default to 5 (full reveal) once identified. Default to 5 for
            # back-compat when an item doesn't have the field.
            id_level = int(getattr(subject, 'id_level', 5))
            item_class_label = subject.item_class.upper()
            title = self.font_lg.render(
                f"{subject.name.upper()} -- {item_class_label}", True, title_col
            )
            self.screen.blit(title, (bx + (bw - title.get_width()) // 2, y))
            y += 40
            pygame.draw.line(self.screen, border_col, (bx+20, y), (bx+bw-20, y))
            y += 12

            stat_lines = []

            # Mastery banner \u2014 top line when id_level == 5 and mastery has been claimed.
            mastered = (id_level >= 5
                        and getattr(self.player, 'unlocked_masteries', {}).get(subject.id))
            if mastered:
                stat_lines.append(f"\u2605 MASTERED  \u2605  {mastered.get('desc', '')}")

            # Aura line at id_level >= 2 (BUC known).
            if id_level >= 2:
                _buc = getattr(subject, 'buc', 'uncursed')
                aura_text = {
                    'blessed': "Aura: blessed (radiates a holy light)",
                    'cursed': "Aura: cursed (a dark aura clings to it)",
                    'uncursed': "Aura: uncursed",
                }.get(_buc, "Aura: unclear")
                stat_lines.append(aura_text)

            # Set membership banner
            if getattr(subject, 'set_id', ''):
                set_label = getattr(subject, 'set_name', subject.set_id)
                stat_lines.append(f"\u2605 Part of {set_label} \u2605")

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
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: +{subject.enchant_bonus}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")
                if subject.damage_resistances:
                    res_str = '  '.join(f"{k}: {int(v*100)}%" for k, v in subject.damage_resistances.items())
                    stat_lines.append(f"Resistances: {res_str}")
                if subject.can_be_cursed:
                    stat_lines.append("WARNING: This item can be cursed.")

            elif id_level >= 3 and isinstance(subject, Shield):
                stat_lines.append(f"Material: {subject.material}  |  Tier: {subject.tier}")
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: +{subject.enchant_bonus}")
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

            elif id_level >= 3 and isinstance(subject, Ammo):
                stat_lines.append(f"Ammo Type: {subject.ammo_type}  |  Tier: {subject.tier}")
                stat_lines.append(f"Damage Bonus: +{subject.damage_bonus}  |  Count: {subject.count_min}-{subject.count_max}")

            # Lore only at id_level >= 4. Below that, show a teaser line.
            if id_level >= 4:
                lore_text = subject.lore or "No further records found."
            else:
                lore_text = "The history of this item remains beyond your grasp. Deeper study may yet reveal it."

        # Draw stat lines (reserve ~120px at bottom for lore section + footer)
        max_stat_w = bw - 44
        stat_bottom = by + bh - 120
        done = False
        for idx, line in enumerate(stat_lines):
            if done:
                break
            wrapped = self._wrap_text(line, self.font_sm, max_stat_w)
            for wl in wrapped or [line]:
                if y + 22 > stat_bottom:
                    remaining = len(stat_lines) - idx
                    surf = self.font_sm.render(f"  ... and {remaining} more", True, (120, 120, 120))
                    self.screen.blit(surf, (bx + 20, y))
                    y += 22
                    done = True
                    break
                self.screen.blit(self.font_sm.render(wl, True, stat_col), (bx + 20, y))
                y += 22

        y += 4
        pygame.draw.line(self.screen, inner_col, (bx+20, y), (bx+bw-20, y))
        y += 12

        # Lore section header
        lore_hdr = self.font_sm.render("-- LORE --", True, border_col)
        self.screen.blit(lore_hdr, (bx + (bw - lore_hdr.get_width()) // 2, y))
        y += 22

        # Lore text (wrapped, with remaining space)
        lore_lines = self._wrap_text(lore_text, self.font_sm, bw - 44)
        for line in lore_lines:
            if y + self.font_sm.get_height() > by + bh - 40:
                break
            surf = self.font_sm.render(line, True, lore_col)
            self.screen.blit(surf, (bx + 22, y))
            y += self.font_sm.get_height() + 3

        hint = self.font_sm.render("[ ESC / ENTER / SPACE ] to close", True, (80, 80, 100))
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 26))

    # ------------------------------------------------------------------
    # Examine menu  (x key)
    # ------------------------------------------------------------------
    # Drop-item menu  (D key)
    # ------------------------------------------------------------------

    def _draw_drop_gold_input(self):
        """Draw a numeric entry overlay to choose how much gold to drop."""
        draw_overlay(self.screen, 190)
        bw, bh = 400, 160
        bx = (layout.GAME_W - bw) // 2
        by = (layout.GAME_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))

        title = self.font_lg.render("DROP GOLD", True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + 14))

        have = getattr(self, 'player_gold', 0)
        sub = self.font_sm.render(f"You have {have} gold", True, FP.FADED_TEXT)
        self.screen.blit(sub, (bx + (bw - sub.get_width()) // 2, by + 44))

        # Input box
        box_rect = pygame.Rect(bx + 60, by + 76, bw - 120, 34)
        pygame.draw.rect(self.screen, (30, 30, 50), box_rect, border_radius=4)
        pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, box_rect, 1, border_radius=4)
        display = self.drop_gold_input or "0"
        val_surf = self.font_md.render(display, True, FP.PARCHMENT_LIGHT)
        self.screen.blit(val_surf, (box_rect.x + 8, box_rect.y + 6))

        hint = self.font_sm.render("ENTER to confirm  |  ESC to cancel", True, FP.FADED_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 26))

    def _draw_examine_menu(self):
        tab_items = self._get_examine_tab_items()
        entries = []
        for i, item in enumerate(tab_items[:26]):
            entries.append({
                'name': self._display_name(item),
                'detail': self._get_item_stats_brief(item),
                'key': self._LETTERS[i],
                'icon': item,
            })

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
        """Draw the merchant shop overlay."""
        from fantasy_ui import draw_overlay, draw_filigree_bar, centered_text, FP
        m = getattr(self, '_shop_merchant', None)
        if m is None:
            return
        cx = layout.GAME_W // 2
        cy = layout.WINDOW_H // 2
        draw_overlay(self.screen, 190, (10, 8, 2))
        draw_filigree_bar(self.screen, cx - 280, cy - 180, 560, FP.GOLD)
        centered_text(self.screen, self.font_lg, "TRAVELLING MERCHANT", FP.GOLD_BRIGHT, cy - 165, shadow=True)
        draw_filigree_bar(self.screen, cx - 280, cy - 145, 560, FP.GOLD_DARK)

        gold_s = self.font_sm.render(f"Your gold: {self.player_gold}", True, FP.GOLD_PALE)
        self.screen.blit(gold_s, (cx - gold_s.get_width() // 2, cy - 128))

        stock = m.stock
        sel   = getattr(self, '_shop_selection', 0)
        row_y = cy - 106
        row_h = 28
        if not stock:
            empty_s = self.font_md.render("Sold out!", True, FP.FADED_TEXT)
            self.screen.blit(empty_s, (cx - empty_s.get_width() // 2, row_y))
        else:
            haggled = getattr(self, '_shop_haggled', set())
            for i, (item, price) in enumerate(zip(stock, m.prices)):
                is_sel = (i == sel)
                iname  = getattr(item, 'name', '?')
                wt     = getattr(item, 'weight', 0)
                tag    = " [haggled]" if i in haggled else ""
                line   = f"  {iname}  (wt:{wt:.1f})   {price} gold{tag}"
                fg     = FP.PARCHMENT_LIGHT if is_sel else FP.BODY_TEXT
                bg_col = (60, 50, 20, 180) if is_sel else None
                if bg_col:
                    bg_r = pygame.Rect(cx - 260, row_y - 2, 520, row_h)
                    bg_surf = pygame.Surface((bg_r.w, bg_r.h), pygame.SRCALPHA)
                    bg_surf.fill(bg_col)
                    self.screen.blit(bg_surf, bg_r.topleft)
                prefix = "> " if is_sel else "  "
                line_s = self.font_md.render(self._fit_text(prefix + line, self.font_md, 500), True, fg)
                self.screen.blit(line_s, (cx - 260, row_y))
                row_y += row_h

        draw_filigree_bar(self.screen, cx - 280, row_y + 8, 560, FP.GOLD_DARK)
        hint = self.font_sm.render("^v navigate   ENTER buy   H haggle   ESC close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, row_y + 16))

    def _draw_encyclopedia(self):
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

            stat_col = (180, 200, 230)
            for line in stat_lines:
                for wl in self._wrap_text(line, self.font_sm, bw - 44) or [line]:
                    surf = self.font_sm.render(wl, True, stat_col)
                    self.screen.blit(surf, (bx + 20, y))
                    y += 22

            y += 6
            pygame.draw.line(self.screen, (40, 60, 120), (bx + 20, y), (bx + bw - 20, y))
            y += 12
            lore_hdr = self.font_sm.render("-- LORE --", True, (80, 120, 200))
            self.screen.blit(lore_hdr, (bx + (bw - lore_hdr.get_width()) // 2, y))
            y += 22

            lore_lines = self._wrap_text(lore_text, self.font_sm, bw - 44)
            for line in lore_lines:
                if y + self.font_sm.get_height() > by + bh - 40:
                    break
                self.screen.blit(self.font_sm.render(line, True, (200, 215, 240)), (bx + 22, y))
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

    def _draw_hint_screen(self):
        """Display a Recall Lore result -- parchment-style hint overlay."""
        from fantasy_ui import get_font
        hint_text = getattr(self, '_lore_hint_text', None)
        chain     = getattr(self, '_lore_hint_chain', 0)
        if hint_text is None:
            self.state = STATE_PLAYER
            return

        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 760, 280
        bx = (layout.GAME_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Parchment-warm background
        pygame.draw.rect(self.screen, (24, 18, 8), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(self.screen, (160, 130, 60), (bx, by, bw, bh), 2, border_radius=10)
        pygame.draw.rect(self.screen, (80, 65, 25), (bx+4, by+4, bw-8, bh-8), 1, border_radius=8)

        font_title = get_font('heading', 20)
        font_body  = get_font('body', 19)
        font_small = get_font('body', 16)

        # Chain quality label
        quality_labels = {1: "Vague Recollection", 2: "Useful Memory",
                          3: "Clear Knowledge", 4: "Deep Lore", 5: "Ancient Wisdom"}
        label = quality_labels.get(chain, "Lore")
        stars = '[*] ' * chain + '[ ] ' * (5 - chain)

        title_surf = font_title.render(f"RECALL LORE  --  {label}", True, (220, 180, 80))
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 14))

        stars_surf = font_small.render(stars, True, (200, 160, 60))
        self.screen.blit(stars_surf, (bx + (bw - stars_surf.get_width()) // 2, by + 40))

        pygame.draw.line(self.screen, (100, 80, 30),
                         (bx + 30, by + 62), (bx + bw - 30, by + 62))

        # Wrap hint text
        words = hint_text.split()
        lines, line = [], []
        max_w = bw - 60
        for word in words:
            test = ' '.join(line + [word])
            if font_body.size(test)[0] > max_w:
                if line:
                    lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(' '.join(line))

        y = by + 78
        for ln in lines:
            surf = font_body.render(ln, True, (230, 210, 160))
            self.screen.blit(surf, (bx + 30, y))
            y += font_body.get_height() + 4

        # Cooldown notice
        cd = self.player.recall_lore_cooldown
        cd_surf = font_small.render(
            f"Next recall available in {cd} turns  --  [ any key ] to close",
            True, (100, 85, 45)
        )
        self.screen.blit(cd_surf, (bx + (bw - cd_surf.get_width()) // 2, by + bh - 26))

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
        overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        _COMMANDS = [
            # (key_label, description, color)  -- None description = section header
            ("MOVEMENT", None, FP.GOLD_PALE),
            ("Arrows / hjkl",  "Move / attack",                   FP.BODY_TEXT),
            ("ITEMS & EQUIPMENT", None, FP.GOLD_PALE),
            ("G  or  ,",       "Pick up item",                    FP.BODY_TEXT),
            ("E",              "Equip armor / weapon",             FP.BODY_TEXT),
            ("S",              "Equip accessory (ring/amulet)",    FP.BODY_TEXT),
            ("I",              "Identify items + read corpse lore",FP.BODY_TEXT),
            ("R",              "Read scroll / spellbook",          FP.BODY_TEXT),
            ("M",              "Cast spell",                       FP.BODY_TEXT),
            ("Z",              "Zap wand",                         FP.BODY_TEXT),
            ("U",              "Eat food",                         FP.BODY_TEXT),
            ("Q",              "Quaff potion",                     FP.BODY_TEXT),
            ("D",              "Drop item / Interact (fountain/grave/throne)", FP.BODY_TEXT),
            ("COMBAT & EXPLORATION", None, FP.GOLD_PALE),
            ("H",              "Harvest monster corpse",           FP.BODY_TEXT),
            ("C",              "Cook ingredient",                  FP.BODY_TEXT),
            ("F",              "Fire ranged weapon",               FP.BODY_TEXT),
            ("T",              "Throw item (potion / weapon / sphere)", FP.BODY_TEXT),
            ("A",              "Melee target (attack / interact)",  FP.BODY_TEXT),
            ("P",              "Pick lock",                        FP.BODY_TEXT),
            (">  or  <",       "Use stairs",                       FP.BODY_TEXT),
            ("Y",              "Visit merchant shop",              FP.BODY_TEXT),
            ("INFORMATION", None, FP.GOLD_PALE),
            ("O",              "Observe (look at things)",          FP.BODY_TEXT),
            ("X",              "Examine inventory items",          FP.BODY_TEXT),
            ("@",              "Character sheet",                  FP.BODY_TEXT),
            ("B",              "Encyclopedia",                     FP.BODY_TEXT),
            ("W",              "Quirks progress",                  FP.BODY_TEXT),
            ("V",              "Activate quirk power",             FP.BODY_TEXT),
            ("KNOWLEDGE", None, FP.GOLD_PALE),
            ("\\",             "Pray at altar",                    (200, 180, 255)),
            ("N",              "Recall Lore",                      (120, 200, 240)),
            (";",              "Study Journal (review missed Qs)",  (120, 200, 240)),
            ("QUIZ", None, FP.GOLD_PALE),
            ("1  2  3  4",     "Answer question during quiz",      FP.GOLD_BRIGHT),
            ("SYSTEM", None, FP.GOLD_PALE),
            ("Tab",            "Cycle zoom: full / medium / close", FP.BODY_TEXT),
            ("?",              "This help screen",                 FP.BODY_TEXT),
            ("ESC",            "Cancel / close menu",              FP.BODY_TEXT),
        ]

        line_h    = 26
        col_break = (len(_COMMANDS) + 1) // 2   # split evenly
        content_h = col_break * line_h
        bw        = min(1000, layout.GAME_W - 40)
        bh        = 66 + content_h + 36
        bx        = (layout.GAME_W - bw) // 2
        by        = max(10, (layout.WINDOW_H - bh) // 2)

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 48),
                        text="COMMAND REFERENCE",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)
        draw_divider(self.screen, bx + 20, by + 56, bw - 40)

        col_w   = (bw - 40) // 2
        left_x  = bx + 20
        right_x = bx + 20 + col_w
        y       = by + 66

        for idx, entry in enumerate(_COMMANDS):
            key_label, desc, color = entry
            cx_ = left_x if idx < col_break else right_x
            cy_ = y + (idx if idx < col_break else idx - col_break) * line_h

            if desc is None:
                hdr = self.font_sm.render(f"-- {key_label} --", True, color)
                self.screen.blit(hdr, (cx_, cy_))
            else:
                ksurf = self.font_sm.render(key_label, True, FP.GOLD_BRIGHT)
                desc_max_w = col_w - 170
                dsurf = self.font_sm.render(desc, True, color)
                if dsurf.get_width() > desc_max_w:
                    trunc = desc
                    while len(trunc) > 1 and self.font_sm.size(trunc + '\u2026')[0] > desc_max_w:
                        trunc = trunc[:-1]
                    dsurf = self.font_sm.render(trunc + '\u2026', True, color)
                self.screen.blit(ksurf, (cx_, cy_))
                self.screen.blit(dsurf, (cx_ + 160, cy_))

        hint = self.font_sm.render("Press ESC or ? to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 28))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

