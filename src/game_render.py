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
from ui_scale import px as S
from renderer import TILE_SIZE
from geom import monster_at_tile, any_tile_in_set
import ui_theme
import lore_art
from ui import carry_state, carry_color, carry_numbers, floor_label
from fantasy_ui import (FP, KT, get_font, draw_dark_panel,
                         draw_header_bar, draw_divider, draw_shadow_text,
                         draw_glow_text, draw_overlay,
                         draw_rune_circle, draw_filigree_bar, draw_candle_glow,
                         ITEM_COLOR, panel_band, header_rect, readable,
                         draw_key_hints, draw_key_badge, key_hints_height,
                         display_title, kit_on, display_text, fit_text,
                         divider_reach)
from items import (Weapon, Armor, Shield, Corpse, Accessory,
                   Wand, Scroll, Spellbook, Ammo, Food, Potion)
from game_helpers import (
    wrap_text as _gh_wrap_text,
)
from naming import proper_name
from quiz_engine import QuizMode, QuizState
from spells import LEARNABLE_SPELLS
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_QUIZ_CONTEXT, STATE_EQUIP_MENU, STATE_KIT, STATE_DISCOVERIES,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_CONFIRM_EXIT, STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
    STATE_VICTORY, STATE_DEAD, STATE_REVIEW_MISSED,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
    STATE_SPELL_MENU, STATE_HINT, STATE_EXAMINE,
    STATE_ENCYCLOPEDIA, STATE_DROP_MENU, STATE_DROP_GOLD_INPUT, STATE_DROP_QTY_INPUT,
    STATE_STORY_POPUP, STATE_MYSTERY_APPROACH, STATE_SHOP, STATE_POWER_MENU,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM,
    STATE_THROW_MENU, STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_EMBERPUP, STATE_JUDGMENT, STATE_STUDY,
    STATE_INTERCESSION_PROMPT, STATE_PET_NAME_INPUT, STATE_PRAYER_MENU,
    STATE_BOON_MENU,
    STATE_PET_MENU, STATE_PET_FEED, STATE_PET_HEAL, STATE_PET_SPECIALS,
    STATE_QA_WARP_INPUT, STATE_MESSAGE_LOG,
)


def _threshold_line(label: str, n) -> str:
    """Threshold copy shared by kit + lore + bestiary panels.

    Phase 1 beautification (2026-10-03): the "(any wrong = fail)" tail used
    to live here, duplicated across 12+ inspector / card / lore sites. It
    is gone everywhere now -- the quiz-modal subtitle that briefly kept it
    was removed too (2026-10-04 playtest). Callers pass their own label
    ("Equip", "Quiz", "Grammar", ...); the shape is uniform.
    """
    return f"{label}: {n} correct"


def _cap(raw) -> str:
    """'two_handed sword' -> 'Two Handed Sword': capitalise a raw data value
    (material, slot, damage type, aura, ...) for display in a panel."""
    return proper_name(str(raw).replace('_', ' '))


def _temp_power_label(name) -> str:
    """Display name of a recipe's temporary power (same text the cook log
    uses), or '' when there is none."""
    if not name:
        return ''
    from food_system import temp_power_label
    return temp_power_label(str(name))


def _quiz_mode_phrase(mode, threshold=None) -> str:
    """Plain-language description of a quiz mode for the player.

    Engine mode names ("escalator_threshold", "escalator_chain") used to
    be title-cased straight onto cards and panels.
    """
    mode = str(mode or '')
    if 'threshold' in mode:
        return f"answer {threshold} in a row" if threshold else "answer in a row"
    if 'chain' in mode:
        return f"chain of {threshold} or more" if threshold else "chain"
    return mode.replace('_', ' ')


def _identify_status_label(id_level: int) -> str:
    """Map an item's id_level to a human status string.

    Post-2026-08-06 identify-v3 model: only 0 and 5 are actually written for
    new saves (the old id_level 1-4 progression was deleted; True Name view
    uses the kit_visible_level helper to render a "type known" view at 4).
    Old saves that predate the redesign may carry legacy intermediate values.
    """
    idl = int(id_level or 0)
    if idl >= 5:
        return "Identified"
    if idl >= 4:
        return "Type known (this copy's curse and enchant unknown)"
    if idl >= 1:
        return "Partial (legacy save)"
    return "Unknown"


class _ScaledPx:
    """Class attribute that reads as ``ui_scale.px(n)``: a length that grows
    with the UI scale (SCALE_PLAN.md). Non-data, so an instance may assign
    a fixed value of its own."""

    __slots__ = ('n',)

    def __init__(self, n: int):
        self.n = n

    def __get__(self, obj, objtype=None) -> int:
        return S(self.n)


def _centre_x(w: int) -> int:
    """Left edge of a ``w``-wide panel centred on the WINDOW (SCALE_PLAN.md 3:
    every modal centres on the window, not on the play area left of the
    right rail)."""
    return (layout.WINDOW_W - w) // 2


def _centre_y(h: int) -> int:
    return (layout.WINDOW_H - h) // 2


def _modal_budget_w() -> int:
    """The width a modal may use: the play area left of the right rail
    (``GAME_W``), as it always was -- except in a COMPACT window (below
    1280x720, bug bash 4 call 15), where the text cannot shrink with the
    window and every modal may use the whole window width (they centre on
    the window and dim both rails anyway)."""
    import ui_scale
    return layout.WINDOW_W if ui_scale.is_compact() else layout.GAME_W


def _kit_option_card(screen, title, options, footer, *, lines=(), border=FP.GOLD,
                     overlay=200, min_w=700, note='', note_color=None):
    """A modal of numbered choices in the Midnight Codex kit, centred on the
    window: plaque title, optional intro ``lines`` (centred), one kit row
    per option (key badge, name, a line of text under it), an optional
    ``note``, and the footer as key hints. Used by the prayer, boon and
    intercession prompts, which used to be hand-drawn "dark parchment"
    boxes. Module-level (needs only the screen) so it draws for any caller.
    ``options``: dicts with ``key``, ``name``, ``text`` and ``name_color``."""
    from fantasy_ui import fit_text
    if overlay:
        draw_overlay(screen, overlay)
    name_f = get_font('body', 19, bold=True)
    text_f = get_font('body', 16)
    line_f = get_font('body', 18)
    key_f = get_font('body', 18, bold=True)
    band = S(16)
    row_pad = S(10)
    key_w = S(34)
    need = [line_f.size(t)[0] + S(48) for t in lines]
    for o in options:
        need.append(max(name_f.size(o['name'])[0], text_f.size(o.get('text', ''))[0])
                    + key_w + S(40) + 2 * row_pad)
    if note:
        need.append(text_f.size(note)[0] + S(48))
    inner_w = max([S(min_w) - 2 * band - S(56)] + need)
    bw = min(inner_w + 2 * band + S(56), layout.WINDOW_W - S(48))
    row_h = name_f.get_height() + text_f.get_height() + S(26)
    lines_h = len(lines) * (line_f.get_height() + S(6)) + (S(10) if lines else 0)
    note_h = text_f.get_height() + S(14) if note else 0
    foot_h = S(8) + key_hints_height() + S(32)
    bh = (2 * band + S(48) + S(16) + lines_h + len(options) * (row_h + S(8))
          + note_h + foot_h)
    bh = min(bh, layout.WINDOW_H - S(48))
    panel = pygame.Rect(_centre_x(bw), _centre_y(bh), bw, bh)
    draw_dark_panel(screen, panel, border_color=border)
    hr = draw_header_bar(screen, (panel.x, panel.y, panel.w, S(48)), text=title,
                         font=get_font('heading', 30), accent=border,
                         frame=(panel, border))
    b = panel_band('panel', panel)
    x0 = panel.x + b + S(28)
    w0 = panel.w - 2 * (b + S(28))
    y = hr.bottom + S(14)
    for t in lines:
        ts = line_f.render(fit_text(t, line_f, w0), True, KT.TEXT_BODY)
        screen.blit(ts, (panel.centerx - ts.get_width() // 2, y))
        y += line_f.get_height() + S(6)
    if lines:
        y += S(10)
    for o in options:
        rect = pygame.Rect(x0, y, w0, row_h)
        ui_theme.draw_piece(screen, 'row', rect, body_color=KT.RAISED)
        kr = pygame.Rect(rect.x + row_pad, rect.centery - S(17), key_w, S(34))
        draw_key_badge(screen, kr, o['key'], key_f)
        tx = kr.right + S(14)
        tw = rect.right - tx - row_pad
        ty = rect.y + S(10)
        ncol = readable(o.get('name_color') or KT.TEXT_HEAD, KT.RAISED)
        screen.blit(name_f.render(fit_text(o['name'], name_f, tw), True, ncol), (tx, ty))
        if o.get('text'):
            screen.blit(text_f.render(fit_text(o['text'], text_f, tw), True, KT.TEXT_BODY),
                        (tx, ty + name_f.get_height() + S(4)))
        y += row_h + S(8)
    if note:
        ns = text_f.render(fit_text(note, text_f, w0), True,
                           readable(note_color or KT.TEXT_SUB, KT.INTERIOR))
        screen.blit(ns, (panel.centerx - ns.get_width() // 2, y + S(4)))
    keys = pygame.Rect(panel.x + b + S(20), panel.bottom - b - S(8) - key_hints_height(),
                       panel.w - 2 * (b + S(20)), key_hints_height())
    draw_divider(screen, panel.x + b + S(28), keys.y - S(16), panel.w - 2 * (b + S(28)))
    draw_key_hints(screen, keys, footer)
    return panel


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
            body.append((f"Challenge: Carry {m['key_item']['name']} {ch.get('tiles', 15)} steps",
                         FP.GOLD_PALE))
        else:
            body.append(
                (f"Challenge: {ch['subject'].capitalize()} - "
                 f"{_quiz_mode_phrase(ch['mode'], ch.get('threshold'))}",
                 FP.GOLD_PALE)
            )
        if m['key_item']:
            body.append((f"Requires: {m['key_item']['name']}", FP.FADED_TEXT))
        if m.get('gold_cost', 0) > 0:
            # The price as the altar takes it (written_gold): the card said
            # 50 where 300 was taken.
            import economy as _eco
            body.append((f"Tribute: {_eco.written_gold(m['gold_cost']):,} gold", FP.FADED_TEXT))
        if m.get('stat_cost'):
            cost_desc = ', '.join(f"{s}{v}" for s, v in m['stat_cost'].items())
            body.append((f"Cost: {cost_desc}", FP.WARNING_TEXT))
        if altar.mystery_id == 'cauldron':
            body.append(("Requires: 3 prepared meals in inventory", FP.FADED_TEXT))

        self._ui_message_card(
            # The kit's plaque carries the name alone (the altar's map glyph
            # either side of it read as a stray letter: "W the Sphinx W").
            m['name'].upper() if kit_on() else f"{altar.symbol}  {m['name'].upper()}  {altar.symbol}",
            body,
            options=[
                {'key': 'Y', 'label': 'Accept the challenge', 'color': FP.GOLD_BRIGHT},
                {'key': 'N', 'label': 'Leave the altar untouched', 'color': FP.HINT_TEXT},
            ],
            footer="Enter / Space: accept   |   Esc: leave",
            border_color=altar.color,
            title_color=altar.color,
            max_w=720,
            max_h=460,
        )

    MENU_ICON_SIZE = _ScaledPx(32)

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
        SZ = self.MENU_ICON_SIZE
        key = (item_id, SZ)          # the icon grows with the UI scale
        if key in self._menu_sprite_cache:
            return self._menu_sprite_cache[key]
        from renderer import _resolve_item_sprite_path, fit_sprite
        path = _resolve_item_sprite_path(item_id)
        if path:
            raw = pygame.image.load(path).convert_alpha()
            surf = fit_sprite(raw, SZ, SZ)
        else:
            surf = None
        self._menu_sprite_cache[key] = surf
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

    def _draw_xyzzy_input(self):
        """Draw the hidden green terminal input — 'Speak the First Word'."""
        from fantasy_ui import get_font
        draw_overlay(self.screen, 220)

        bw, bh = S(520), S(200)
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
        font_hint  = get_font('body', 16)

        # Title
        title = "Speak the First Word"
        title_surf = font_title.render(title, True, (0, 200, 80))
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + S(24)))

        pygame.draw.line(self.screen, (0, 100, 40),
                         (bx + S(30), by + S(54)), (bx + bw - S(30), by + S(54)))

        # Input field with blinking cursor
        self._xyzzy_blink = (self._xyzzy_blink + 1) % 60
        cursor = '_' if self._xyzzy_blink < 30 else ' '
        display_text = '> ' + self._xyzzy_text + cursor

        input_surf = font_input.render(display_text, True, (0, 255, 120))
        self.screen.blit(input_surf, (bx + S(40), by + S(80)))

        # Bottom hint
        hint_surf = font_hint.render("[Enter] to submit  //  [Esc] to cancel", True, (0, 180, 80))
        self.screen.blit(hint_surf, (bx + (bw - hint_surf.get_width()) // 2, by + bh - S(30)))

    def _draw_xyzzy_confirm(self):
        """Draw the 'WARNING: You are about to hack reality' confirmation."""
        from fantasy_ui import get_font
        draw_overlay(self.screen, 220)

        bw, bh = S(640), S(240)
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
        self.screen.blit(warn_surf, (bx + (bw - warn_surf.get_width()) // 2, by + S(20)))

        pygame.draw.line(self.screen, (180, 120, 0),
                         (bx + S(20), by + S(52)), (bx + bw - S(20), by + S(52)))

        # Warning text
        lines = [
            "You are about to hack reality.",
            "Are you sure?",
        ]
        y = by + S(66)
        for line in lines:
            surf = font_body.render(line, True, (220, 180, 60))
            self.screen.blit(surf, (bx + (bw - surf.get_width()) // 2, y))
            y += font_body.get_height() + S(6)

        # Yes / No buttons
        sel = getattr(self, '_xyzzy_confirm_sel', 0)
        btn_y = by + bh - S(56)
        for i, label in enumerate(('[ YES ]', '[ NO ]')):
            bx_btn = bx + bw // 2 - S(120) + i * S(160)
            if i == sel:
                color = (0, 255, 120)
                pygame.draw.rect(self.screen, (0, 60, 30),
                                 (bx_btn - S(10), btn_y - S(4), S(100), S(32)), border_radius=4)
            else:
                color = (170, 170, 170)
            surf = font_btn.render(label, True, color)
            self.screen.blit(surf, (bx_btn, btn_y))
        hint = get_font('body', 16).render(
            "Left/Right: choose  //  Enter or Y: yes  //  N or Esc: no",
            True, (220, 160, 0))
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                by + bh - S(24)))

    def _draw_hack_reality_screen(self):
        """Display the Hack Reality result -- green terminal overlay."""
        from fantasy_ui import get_font
        result_lines = getattr(self, '_hack_result_lines', None)
        chain = getattr(self, '_hack_result_chain', 0)
        if result_lines is None:
            self.state = STATE_PLAYER
            return

        draw_overlay(self.screen, 190)

        bw, bh = min(S(760), layout.WINDOW_W - S(80)), S(400)
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Dark terminal background with green border
        pygame.draw.rect(self.screen, (8, 16, 8), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, (0, 200, 80), (bx, by, bw, bh), 2, border_radius=6)
        pygame.draw.rect(self.screen, (0, 100, 40), (bx+3, by+3, bw-6, bh-6), 1, border_radius=4)

        font_title = get_font('heading', 22)
        font_body  = get_font('body', 18)
        font_small = get_font('body', 16)

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
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + S(14)))

        bar_surf = font_small.render(f"[{bar}]  depth={chain}/5", True, (0, 180, 80))
        self.screen.blit(bar_surf, (bx + (bw - bar_surf.get_width()) // 2, by + S(42)))

        pygame.draw.line(self.screen, (0, 120, 50),
                         (bx + S(20), by + S(62)), (bx + bw - S(20), by + S(62)))

        # Result lines (word-wrapped)
        y = by + S(76)
        for text, color in result_lines:
            wrapped = self._wrap_text("> " + text, font_body, bw - S(50))
            for wl in wrapped:
                surf = font_body.render(wl, True, color)
                self.screen.blit(surf, (bx + S(24), y))
                y += font_body.get_height() + S(4)

        # Close prompt (no cooldown shown — keep it hidden)
        close_surf = font_small.render(
            "[ any key ] to close",
            True, (0, 200, 80)
        )
        self.screen.blit(close_surf, (bx + (bw - close_surf.get_width()) // 2, by + bh - S(24)))

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
        body = self._ui_modal_body(panel)
        gutter = S(14)
        list_w = min(S(560), max(S(420), int(body.w * 0.42)))
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
        # A row is the quirk's name and its status, at 17 / 16 px (they were
        # 13 px with an 11 px effect line under them). The reward is in the
        # detail pane, in full.
        name_f = get_font('body', 17, bold=True)
        tag_f = get_font('body', 16, bold=True)
        row_h = max(S(44), name_f.get_height() + S(22))
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
            rect = pygame.Rect(list_body.x, y, list_body.w - S(12), row_h - S(7))
            selected = idx == sel
            self._ui_row(rect, selected,
                        fill=(35, 43, 82) if selected else FP.MIDNIGHT,
                        border=FP.ARCANE_BRIGHT if selected else FP.ARCANE_DIM, radius=6)
            bg = KT.SELECTED if selected else KT.RAISED
            name_col = readable(FP.GOLD_BRIGHT if unlocked else FP.BODY_TEXT, bg)
            ty = rect.centery - name_f.get_height() // 2
            if unlocked:
                tag = tag_f.render("Unlocked", True, readable(FP.SUCCESS_TEXT, bg))
                self.screen.blit(tag, (rect.right - S(12) - tag.get_width(),
                                       rect.centery - tag.get_height() // 2))
                room = rect.w - S(36) - tag.get_width()
            else:
                pct_s = tag_f.render(f"{int(pct * 100)}%", True, readable(FP.FADED_TEXT, bg))
                self.screen.blit(pct_s, (rect.right - S(12) - pct_s.get_width(),
                                         rect.centery - pct_s.get_height() // 2))
                bar = pygame.Rect(rect.right - S(24) - pct_s.get_width() - S(100),
                                  rect.centery - S(5), S(100), S(10))
                room = bar.x - rect.x - S(22)
                if name_f.size(name)[0] > room and get_font('body', 16, bold=True).size(name)[0] > room:
                    # A narrow list (compact window): the name keeps its
                    # room and the bar goes; the percentage still shows.
                    room = rect.w - S(36) - pct_s.get_width()
                else:
                    self._ui_progress_bar(bar, pct, color=FP.ARCANE_BRIGHT)
            nf, text = self._fit_line(name, room, (17, 16))
            self._ui_blit_text(text, nf, name_col, rect.x + S(10), ty)
            y += row_h

        if len(data) > visible:
            self._ui_scrollbar(list_body, scroll, len(data), visible,
                               color=FP.ARCANE_BRIGHT)

        qid, name, pct, unlocked, effect, trigger = data[sel]
        detail_lines = [
            (name, FP.GOLD_PALE, get_font('heading', 23)),
            (f"Progress: {int(pct * 100)}%", FP.CYAN_ACCENT, self.font_sm),
        ]
        from quirk_text import quirk_description, quirk_hint
        if unlocked:
            detail_lines.append(("Unlocked", FP.SUCCESS_TEXT, self.font_sm))
            if effect:
                detail_lines += [
                    ("Reward", FP.GOLD_BRIGHT, self.font_sm),
                    (effect, FP.BODY_TEXT, self.font_sm),
                ]
            desc = quirk_description(qid)
            if desc:
                detail_lines += [
                    ("What it does", FP.GOLD_BRIGHT, self.font_sm),
                    (desc, FP.BODY_TEXT, self.font_sm),
                ]
            if trigger:
                detail_lines += [
                    ("How it unlocked", FP.GOLD_BRIGHT, self.font_sm),
                    (trigger, FP.FADED_TEXT, self.font_sm),
                ]
            from quirk_system import _QUIRK_FLAVOR
            quote = _QUIRK_FLAVOR.get(qid, '')
            if quote:
                detail_lines += [
                    ('', FP.FADED_TEXT, self.font_sm),
                    (f'"{quote}"', FP.PARCHMENT_LIGHT, self.font_sm),
                ]
        else:
            detail_lines.append(("Locked", FP.FADED_TEXT, self.font_sm))
            hint = quirk_hint(qid)
            if hint:
                # A nudge in the voice of the figure it is named for; the
                # exact condition and the reward stay hidden until earned.
                detail_lines += [
                    ("A hint", FP.GOLD_BRIGHT, self.font_sm),
                    (hint, FP.PARCHMENT_LIGHT, self.font_sm),
                ]
            detail_lines.append(
                ("The reward stays hidden until this quirk unlocks.",
                 FP.FADED_TEXT, self.font_sm))
        render_lines = []
        for text, color, fnt in detail_lines:
            for line in self._ui_text_lines(text, fnt, detail_body.w - S(12)):
                render_lines.append((line, color, fnt))
        self._ui_draw_scroll_lines(render_lines, self.font_sm, FP.BODY_TEXT,
                                   detail_body,
                                   getattr(self, '_quirks_detail_scroll', 0),
                                   line_gap=5)
        self._ui_footer(panel, "Up/Down: select   PgUp/PgDn: jump   ESC/W: close")

    def _draw_character_pack_sheet(self):
        try:
            from chain_equip import get_chain_subject
        except Exception:
            get_chain_subject = lambda item: getattr(item, 'equip_chain_subject', '') or 'geography'

        self._charsheet_clamp()
        p = self.player
        screen = self.screen
        draw_overlay(screen, 190)
        # The Midnight Codex kit: the sheet is one framed panel with an inset
        # plaque, kit sub-panels, rows, key badges and a key-hint footer
        # inside it (it used to draw its hint over the dimmed message log).
        kit = kit_on()

        font_title = get_font('heading', 25)
        font_head = get_font('body', 15, bold=True)
        # The kit's sheet keeps DESIGN_RULES 3's 16 px floor everywhere (the
        # slot labels were 11 px, the item names 12 px).
        font_body = get_font('body', 16 if kit else 13)
        font_bold = get_font('body', 16 if kit else 13, bold=True)
        font_small = get_font('body', 16 if kit else 11)
        font_tiny = get_font('body', 16 if kit else 10)
        leather = (82, 24, 22)

        def text(value, font, color, x, y):
            surf = font.render(str(value), True, color)
            screen.blit(surf, (x, y))
            return surf.get_rect(topleft=(x, y))

        def wrapped(value, font, color, rect, line_h=None, max_lines=None):
            line_h = S(line_h) if line_h else max(S(13), font.get_height() - S(1))
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
            if kit:
                head = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, S(30))
                ui_theme.draw_piece(screen, 'subpanel', rect, body_color=KT.RAISED)
                ui_theme.draw_piece(screen, 'subpanel_header', head, accent=accent)
                hf = get_font('heading', 17, bold=True)
                ts = hf.render(display_title(title.upper()), True, KT.TEXT_HEAD)
                screen.blit(ts, (head.centerx - ts.get_width() // 2,
                                 head.y + (head.h - S(2) - ts.get_height()) // 2))
                return pygame.Rect(rect.x + S(12), head.bottom + S(10), rect.w - 2 * S(12),
                                   rect.bottom - head.bottom - S(18))
            pygame.draw.rect(screen, FP.MIDNIGHT, rect, border_radius=8)
            pygame.draw.rect(screen, accent, rect, 2, border_radius=8)
            pygame.draw.rect(screen, FP.MIDNIGHT_MID, rect.inflate(-S(8), -S(8)), 1, border_radius=5)
            header = pygame.Rect(rect.x + S(10), rect.y + S(8), rect.w - 2 * S(10), S(30))
            pygame.draw.rect(screen, FP.MIDNIGHT, header, border_radius=5)
            pygame.draw.line(screen, accent, (header.x + S(8), header.bottom - S(2)),
                             (header.right - S(8), header.bottom - S(2)), 1)
            title_s = font_head.render(title.upper(), True, FP.GOLD_BRIGHT)
            screen.blit(title_s, (header.centerx - title_s.get_width() // 2,
                                  header.centery - title_s.get_height() // 2))
            return pygame.Rect(rect.x + S(14), header.bottom + S(10), rect.w - 2 * S(14),
                               rect.h - (header.bottom - rect.y) - S(20))

        def row_rect(rect, selected=False, focus=False):
            if kit:
                if selected and focus:
                    ui_theme.draw_piece(screen, 'row_selected', rect, body_color=KT.SELECTED)
                else:
                    ui_theme.draw_piece(screen, 'row', rect, body_color=KT.RAISED)
                    if selected:
                        pygame.draw.rect(screen, KT.GOLD, rect, 1)
                return
            fill = FP.MIDNIGHT_MID if selected else FP.MIDNIGHT
            pygame.draw.rect(screen, fill, rect, border_radius=5)
            pygame.draw.rect(screen, FP.GOLD_BRIGHT if selected and focus else
                             FP.GOLD_DARK if selected else FP.ARCANE_DIM,
                             rect, 1, border_radius=5)

        def chip(rect, label, color, fg=FP.BODY_TEXT):
            if kit and color == leather:
                draw_key_badge(screen, rect, str(label), font_bold)
                return
            pygame.draw.rect(screen, color, rect, border_radius=5)
            label_s = font_bold.render(str(label), True, fg)
            screen.blit(label_s, (rect.centerx - label_s.get_width() // 2,
                                  rect.centery - label_s.get_height() // 2))

        def bar(x, y, w, label, value, max_value, color):
            text(label, font_bold, FP.BODY_TEXT, x, y)
            track = pygame.Rect(x + S(36), y + S(6), max(S(20), w - S(102)), S(9))
            ratio = max(0.0, min(1.0, value / max(1, max_value)))
            if kit:
                # The value's own width is kept clear (a fixed 94 px let
                # "210/210" run over the panel edge on a wide sheet).
                val_w = font_body.size(f"{value}/{max_value}")[0] + S(8)
                track = pygame.Rect(x + S(36), y + S(3),
                                    max(S(20), min(w - S(102), w - S(36) - val_w)), S(14))
                ui_theme.draw_piece(screen, 'bar_track', track)
                inner = track.inflate(-S(4), -S(4))
                if ratio:
                    screen.fill(color, (inner.x, inner.y, int(inner.w * ratio), inner.h))
                ui_theme.draw_piece(screen, 'bar_frame', track, body=False)
                text(f"{value}/{max_value}", font_body, FP.BODY_TEXT, track.right + S(8), y)
                return y + S(25)
            pygame.draw.rect(screen, FP.MIDNIGHT, track, border_radius=4)
            if ratio:
                pygame.draw.rect(screen, color,
                                 (track.x, track.y, int(track.w * ratio), track.h),
                                 border_radius=4)
            text(f"{value}/{max_value}", font_body, FP.BODY_TEXT, track.right + S(8), y - S(1))
            return y + S(25)

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
                lines.append(f"Attunes by {str(get_chain_subject(item)).title()} {_quiz_mode_phrase(mode)}")
            if isinstance(item, Weapon):
                spec = self._kit_weapon_special(item, visible)
                if spec and spec != '-':
                    lines.append(spec)
            if getattr(item, 'damage_resistances', None):
                bits = ', '.join(f"{k.title()} x{v}" for k, v in item.damage_resistances.items())
                lines.append(f"Resists {bits}")
            if not isinstance(item, Weapon):
                # What a named piece of armor does, in its own words, and the
                # plain worn bonuses. These used to be told nowhere: the card
                # of the Gauntlets of Mars said "No revealed special abilities".
                if getattr(item, 'special', ''):
                    lines.append(item.special)
                if getattr(item, 'dodge_bonus', 0):
                    lines.append(f"Dodge +{item.dodge_bonus:.0%}")
                if getattr(item, 'toughness_bonus', 0):
                    lines.append(f"Toughness +{item.toughness_bonus:.0%}")
                if getattr(item, 'quiz_timer_bonus', 0):
                    lines.append(f"Combat Clock +{int(item.quiz_timer_bonus)}s")
                if getattr(item, 'spell_reflect', 0):
                    lines.append(f"Turns Back {item.spell_reflect:.0%} Of Spells And Fire")
                if getattr(item, 'fire_reflect', 0):
                    lines.append(f"Throws Back {item.fire_reflect:.0%} Of Every Fire Attack")
                if getattr(item, 'chain_bonus', 0):
                    lines.append(f"Every Chain That Lands Counts {int(item.chain_bonus)} Longer")
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

        # A full-height sheet, at most px(1600) wide, centred on the window
        # (SCALE_PLAN.md 3): uncapped, the item card would stretch to
        # ~1700 px on a 3440 px window. At 1280x720 it is the whole window,
        # exactly as before.
        sheet_w = min(layout.WINDOW_W, S(1600))
        sheet_x = (layout.WINDOW_W - sheet_w) // 2
        narrow = sheet_w < S(1500)
        margin = S(22) if narrow else S(34)
        header_h = S(74)
        gap = S(14)
        # The selected item's actions, by key (the same keys as the Kit);
        # only those possible right now are listed.
        footer = "   ".join(
            ["Arrows: move", "1-4/Tab: filter", "Enter: actions"]
            + [f"{k}: {lab}" for k, lab in self._item_action_hints(actions)]
            + ["ESC: close"])
        if kit:
            gap = S(10)
            outer = pygame.Rect(sheet_x + S(8), S(8), sheet_w - S(16), layout.WINDOW_H - S(16))
            draw_dark_panel(screen, outer, border_color=FP.GOLD)
            b = panel_band('panel', outer)
            header = draw_header_bar(screen, (outer.x, outer.y, outer.w, S(52)),
                                     text="Character / Pack", font=get_font('heading', 28),
                                     frame=(outer, FP.GOLD))
            info_f = get_font('body', 16)
            info = info_f.render(f"{getattr(self, 'player_name', 'Adventurer')}   "
                                 f"{floor_label(self.dungeon_level)}   Turn {self.turn_count}",
                                 True, KT.TEXT_DIM)
            iy = header.y + (header.h - S(4) - info.get_height()) // 2
            screen.blit(info, (header.x + S(40), iy))
            _cwt, _clim, _cstate = carry_state(p)
            _ccol = carry_color(_cstate)
            wt = get_font('body', 16, bold=True).render(
                f"Carrying {carry_numbers(p)}" + (f"   {_cstate}" if _cstate else ""),
                True, _ccol)
            gd = get_font('body', 16, bold=True).render(
                f"Gold {self.player_gold:,}", True, FP.GOLD_BRIGHT)
            screen.blit(gd, (header.right - S(40) - gd.get_width(), iy))
            screen.blit(wt, (header.right - S(40) - gd.get_width() - S(24) - wt.get_width(), iy))
            margin = b + S(10)
            sheet_x, sheet_w = outer.x, outer.w
            top = header.bottom + S(10)
            kh = key_hints_height()
            keys = pygame.Rect(outer.x + b + S(20), outer.bottom - b - S(6) - kh,
                               outer.w - 2 * (b + S(20)), kh)
            bottom = keys.y - S(26)
            draw_divider(screen, outer.x + b + S(28), keys.y - S(13), outer.w - 2 * (b + S(28)))
            draw_key_hints(screen, keys, footer)
        else:
            header = pygame.Rect(sheet_x + margin, margin, sheet_w - margin * 2, header_h)
            pygame.draw.rect(screen, FP.MIDNIGHT, header, border_radius=8)
            pygame.draw.rect(screen, FP.GOLD, header, 2, border_radius=8)
            text("CHARACTER / PACK", font_title, FP.GOLD_BRIGHT, header.x + S(18), header.y + S(12))
            text(f"{getattr(self, 'player_name', 'Adventurer')}   {floor_label(self.dungeon_level)}   Turn {self.turn_count}",
                 font_body, FP.FADED_TEXT, header.x + S(20), header.y + S(44))
            _cwt, _clim, _cstate = carry_state(p)
            _ctext = f"Carrying {carry_numbers(p)}" + (f"  {_cstate}" if _cstate else "")
            text(_ctext, font_bold, carry_color(_cstate),
                 min(header.right - S(198), header.right - S(18) - font_bold.size(_ctext)[0]),
                 header.y + S(15))
            text(f"Gold {self.player_gold:,}", font_bold, FP.GOLD_BRIGHT,
                 header.right - S(198), header.y + S(40))
            top = header.bottom + S(14)
            footer_h = font_small.get_height()
            bottom = layout.WINDOW_H - margin - footer_h - S(6)
        content_h = bottom - top
        left_w = S(252) if narrow else S(286)
        loadout_w = S(322) if narrow else S(392)
        pack_w = S(318) if narrow else S(382)
        detail_w = sheet_w - margin * 2 - left_w - loadout_w - pack_w - gap * 3
        if detail_w < S(300):
            pack_w = max(S(284), pack_w - (S(310) - detail_w))
            detail_w = sheet_w - margin * 2 - left_w - loadout_w - pack_w - gap * 3

        profile_rect = pygame.Rect(sheet_x + margin, top, left_w, content_h)
        loadout_rect = pygame.Rect(profile_rect.right + gap, top, loadout_w, content_h)
        pack_rect = pygame.Rect(loadout_rect.right + gap, top, pack_w, content_h)
        detail_rect = pygame.Rect(pack_rect.right + gap, top, detail_w, content_h)
        if layout.WINDOW_H > layout.WINDOW_W * 1.2:
            # PORTRAIT (bug bash 4, call 19): four full-height columns left
            # each one a narrow strip with most of it empty. Two rows of two:
            # Character and Loadout over Pack and the Item Card.
            inner_w = sheet_w - margin * 2
            col_w = (inner_w - gap) // 2
            # As tall as the loadout list needs (one row per slot), at most half.
            _lh = get_font('body', 16).get_height()
            _need = (S(30) + S(28) + len(self._charsheet_loadout_entries())
                     * (_lh + S(8) + S(3)))
            top_h = min((content_h - gap) // 2, _need)
            low_y = top + top_h + gap
            low_h = bottom - low_y
            x0 = sheet_x + margin
            profile_rect = pygame.Rect(x0, top, col_w, top_h)
            loadout_rect = pygame.Rect(x0 + col_w + gap, top, inner_w - col_w - gap, top_h)
            pack_rect = pygame.Rect(x0, low_y, col_w, low_h)
            detail_rect = pygame.Rect(x0 + col_w + gap, low_y, inner_w - col_w - gap, low_h)

        if kit:
            self._charsheet_kit_panels(
                p, panel, row_rect, chip, bar, text, wrapped, item_color, display_item,
                ability_lines, tier_lines, leather, focus, detail_item, actions,
                profile_rect, loadout_rect, pack_rect, detail_rect)
        else:
            self._charsheet_plain_panels(
                p, panel, row_rect, chip, bar, text, wrapped, item_color, display_item,
                preview_name, ability_lines, tier_lines, leather, focus, detail_item,
                actions, profile_rect, loadout_rect, pack_rect, detail_rect,
                font_body, font_bold, font_small, font_tiny, kit)

        if not kit:
            hint = font_small.render(footer, True, FP.HINT_TEXT)
            screen.blit(hint, (header.centerx - hint.get_width() // 2,
                               layout.WINDOW_H - margin - hint.get_height()))

    def _charsheet_kit_panels(self, p, panel, row_rect, chip, bar, text, wrapped,
                              item_color, display_item, ability_lines, tier_lines,
                              leather, focus, detail_item, actions,
                              profile_rect, loadout_rect, pack_rect, detail_rect):
        """The character sheet's four panels in the Midnight Codex kit.

        VISUAL_REVIEW (2026-10-16): every line is 16 px or more (slot labels
        were 11 px); the loadout is one labelled list, so a long item name
        wraps instead of being cut; the Kit Summary card that repeated the
        header's weight, the AC and the pack count is gone (its Flat DR moved
        to the stats); effects are one full chip each; Resistances says
        "None" rather than standing empty; the pack's art sits clear of the
        names; the Item Card names the item's kind once and reads its lore.
        """
        from status_effects import EFFECT_INFO
        screen = self.screen
        f16 = get_font('body', 16)
        f16b = get_font('body', 16, bold=True)
        lh = f16.get_height()

        # -- Character ---------------------------------------------------
        body = panel(profile_rect, "Character", FP.GOLD)
        y = body.y
        y = bar(body.x, y, body.w, "HP", p.hp, p.max_hp, FP.DANGER_TEXT)
        y = bar(body.x, y, body.w, "MP", p.mp, p.max_mp, FP.MP_BLUE)
        y = bar(body.x, y, body.w, "SP", p.sp, p.max_sp, FP.SP_GREEN)
        y += S(8)
        cell_gap = S(8)
        cell_w = (body.w - cell_gap) // 2
        cell_h = lh + S(8)

        def cell(idx, y0, label, value, col):
            r = pygame.Rect(body.x + (idx % 2) * (cell_w + cell_gap),
                            y0 + (idx // 2) * (cell_h + S(4)), cell_w, cell_h)
            row_rect(r)
            ls = f16.render(label, True, readable(FP.FADED_TEXT, KT.RAISED))
            screen.blit(ls, (r.x + S(7), r.centery - ls.get_height() // 2))
            vs = f16b.render(str(value), True, readable(col, KT.RAISED))
            screen.blit(vs, (r.right - S(8) - vs.get_width(), r.centery - vs.get_height() // 2))

        stats = [("STR", p.STR), ("CON", p.CON), ("DEX", p.DEX),
                 ("INT", p.INT), ("WIS", p.WIS), ("PER", p.PER)]
        for idx, (name, value) in enumerate(stats):
            col = FP.GOLD_BRIGHT if value >= 13 else FP.DANGER_TEXT_LIGHT if value < 10 else FP.BODY_TEXT
            cell(idx, y, name, value, col)
        y += 3 * (cell_h + S(4)) + S(6)
        metrics = [
            ("AC", str(p.get_ac()), FP.SUCCESS_TEXT if p.get_ac() <= 5 else FP.GOLD_BRIGHT),
            ("Sight", str(p.get_sight_radius()), FP.BODY_TEXT),
            ("Clock", f"{p.combat_clock()}s", FP.GOLD_BRIGHT),
            ("Spells", str(len(getattr(p, 'known_spells', {}))), FP.MP_BLUE_TEXT),
            # What Dexterity and Constitution are doing for you right now.
            ("Dodge", f"{round(100 * p.dodge_chance())}%", FP.BODY_TEXT),
            ("Tough", f"{round(100 * p.toughness())}%", FP.BODY_TEXT),
        ]
        dr = getattr(p, 'damage_resistances', {}) or {}
        for k, v in dr.items():
            metrics.append((f"{_cap(k)} DR", str(v), FP.MP_BLUE_TEXT))
        for idx, (label, value, col) in enumerate(metrics):
            cell(idx, y, label, value, col)
        y += ((len(metrics) + 1) // 2) * (cell_h + S(4)) + S(8)

        text("Effects", f16b, FP.GOLD_BRIGHT, body.x, y)
        y += lh + S(4)
        active = []
        _cstate = carry_state(p)[2]
        if _cstate:          # the load first: it is why the steps are slow
            active.append((_cstate, carry_color(_cstate)))
        for eid, dur in getattr(p, 'status_effects', {}).items():
            if dur == 0:
                continue
            info = EFFECT_INFO.get(eid)
            name, col = (info[0], info[1]) if info else (_cap(eid), FP.BODY_TEXT)
            active.append((f"{name} {dur}" if dur > 0 else name, col))
        chip_h = lh + S(6)
        room = max(0, (body.bottom - y - 2 * (lh + S(4)) - lh) // (chip_h + S(4)))
        shown = active[:max(1, room)] if active else []
        for label, col in shown:
            r = pygame.Rect(body.x, y, body.w, chip_h)
            row_rect(r)
            pygame.draw.rect(screen, col, (r.x, r.y, S(3), r.h))
            ls = f16b.render(label, True, readable(col, KT.RAISED))
            screen.blit(ls, (r.x + S(10), r.centery - ls.get_height() // 2))
            y += chip_h + S(4)
        if not active:
            text("None", f16, FP.FADED_TEXT, body.x, y)
            y += lh + S(4)
        elif len(active) > len(shown):
            text(f"+{len(active) - len(shown)} more", f16, FP.FADED_TEXT, body.x, y)
            y += lh + S(4)
        y += S(6)
        text("Resistances", f16b, FP.GOLD_BRIGHT, body.x, y)
        y += lh + S(4)
        res = list(getattr(p, 'resistances', {}).items())
        if not res:
            text("None", f16, FP.FADED_TEXT, body.x, y)
        for dtype, mult in res:
            if y + lh > body.bottom:
                break                 # a short window: never draw past the panel
            col = FP.SUCCESS_TEXT if mult < 1 else FP.DANGER_TEXT_LIGHT
            text(_cap(dtype), f16, FP.BODY_TEXT, body.x, y)
            ms = f16b.render(f"x{mult:.2f}", True, readable(col, KT.RAISED))
            screen.blit(ms, (body.right - ms.get_width(), y))
            y += lh + S(3)

        # -- Loadout: one labelled list ----------------------------------
        body = panel(loadout_rect, "Loadout", FP.CYAN_ACCENT)
        loadout = self._charsheet_loadout_entries()
        label_w = max(f16.size(e['label'])[0] for e in loadout) + S(14)
        name_w = body.w - label_w - S(16)
        rows = []
        for entry in loadout:
            item = entry.get('item')
            lines = self._wrap_text(display_item(item), f16, name_w) or ['']
            rows.append((entry, item, lines))
        one = lh + S(8)
        total = sum(one + (len(ls) - 1) * lh for _e, _i, ls in rows) + S(3) * len(rows)
        if total > body.h:
            rows = [(e, i, ls[:1]) for e, i, ls in rows]
        y = body.y
        sel_idx = getattr(self, '_charsheet_loadout_idx', 0)
        for idx, (entry, item, lines) in enumerate(rows):
            h = one + (len(lines) - 1) * lh
            if y + h > body.bottom:
                break
            r = pygame.Rect(body.x, y, body.w, h)
            selected = idx == sel_idx
            row_rect(r, selected=selected, focus=(focus == 'loadout'))
            bg = KT.SELECTED if selected and focus == 'loadout' else KT.RAISED
            text(entry['label'], f16, readable(FP.FADED_TEXT, bg), r.x + S(8), r.y + S(4))
            ty = r.y + S(4)
            for ln in lines:
                if len(lines) == 1 and f16.size(ln)[0] > name_w:
                    ln = fit_text(ln, f16, name_w)
                text(ln, f16, readable(item_color(item), bg), r.x + S(8) + label_w, ty)
                ty += lh
            y += h + S(3)

        # -- Pack ----------------------------------------------------------
        body = panel(pack_rect, "Pack", FP.GOLD)
        active_filter = self._charsheet_current_pack_filter()
        tab_labels = [
            ("1 All", "all", FP.GOLD),
            ("2 Gear", "gear", FP.CYAN_ACCENT),
            ("3 Food", "food", FP.SUCCESS_TEXT),
            ("4 Lore", "lore", FP.MP_BLUE_TEXT),
        ]
        tab_w = (body.w - S(18)) // 4
        _tf = get_font('body', 16, bold=True)
        if any(_tf.size(lab)[0] > tab_w - S(10) for lab, _k, _c in tab_labels):
            # A narrow pack (compact window): the words alone; the footer's
            # "1-4/Tab Filter" still names the keys.
            tab_labels = [(lab.split(' ', 1)[1], k, c) for lab, k, c in tab_labels]
        y = body.y
        for idx, (label, key, col) in enumerate(tab_labels):
            r = pygame.Rect(body.x + idx * (tab_w + S(6)), y, tab_w, S(28))
            self._ui_chip(r, label, active=(key == active_filter), color=col)
        y += S(36)
        pack = self._charsheet_pack_entries()
        pack_total = len(self._charsheet_pack_entries(filtered=False))
        count_y = y
        text(self._charsheet_count_label(active_filter, len(pack), pack_total), f16b,
             FP.SUCCESS_TEXT, body.x, count_y)
        y += lh + S(8)
        isz = self.MENU_ICON_SIZE
        key_w = S(26)
        text_x = S(7) + key_w + S(8) + isz + S(8) + S(12)
        # Clear of the row's right border by the row padding (``sm`` + 4):
        # "Wt 0.25" used to touch it (VISUAL_REVIEW_2 minor 5).
        name_w = body.w - text_x - S(12)
        metas = []
        for entry in pack:
            item = entry['item']
            try:
                idl = self._kit_visible_level(item)
            except Exception:
                idl = 0
            _kind = str(getattr(item, 'slot', None) or getattr(item, 'item_class', 'item'))
            parts = [_cap(_kind), f"Wt {getattr(item, 'weight', 0):g}"]
            if hasattr(item, 'id_level') and idl < 5:
                parts.append(_identify_status_label(idl).split(' (')[0])
            meta = "   ".join(parts)
            if f16.size(meta)[0] > name_w:
                meta = "  ".join(parts)
            if f16.size(meta)[0] > name_w and len(parts) > 2:
                meta = "  ".join(parts[:2])      # the Item Card says the rest
            if f16.size(meta)[0] > name_w:
                meta = parts[0]                  # a narrow pack: the kind; the card has the weight
            metas.append((self._wrap_text(display_item(item), f16b, name_w) or [''], meta))
        two = any(len(n) > 1 for n, _m in metas)
        # Text block + 8 px above and below it inside the row, + the 6 px
        # gap between rows: a wrapped name no longer pushes its sub-line
        # onto the row border (VISUAL_REVIEW_2 minor 5).
        pack_row_h = (2 if two else 1) * lh + lh + 2 * S(8) + S(6)
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
            range_s = f16.render(range_label, True, readable(FP.HINT_TEXT, KT.RAISED))
            screen.blit(range_s, (body.right - range_s.get_width(), count_y))
        if not pack:
            wrapped("No items in this filter.", f16, FP.FADED_TEXT,
                    pygame.Rect(body.x, y + S(8), body.w, S(50)), line_h=20)
        for idx, entry in enumerate(pack[scroll:scroll + visible_rows], start=scroll):
            r = pygame.Rect(body.x, y, body.w, pack_row_h - S(6))
            selected = idx == pack_idx
            row_rect(r, selected=selected, focus=(focus == 'pack'))
            bg = KT.SELECTED if selected and focus == 'pack' else KT.RAISED
            chip(pygame.Rect(r.x + S(7), r.centery - S(13), key_w, S(26)), entry['letter'], leather)
            item = entry['item']
            well = pygame.Rect(r.x + S(7) + key_w + S(8), r.centery - isz // 2 - S(4),
                               isz + S(8), isz + S(8))
            self._ui_well(well)
            self._draw_menu_icon(item, well.x + S(4), well.y + S(4))
            names, meta = metas[idx]
            # name line(s) and the meta line, centred together in the row
            ty = r.y + (r.h - (len(names[:2]) + 1) * lh) // 2
            for ln in names[:2]:
                text(ln, f16b, readable(item_color(item), bg), r.x + text_x, ty)
                ty += lh
            text(meta, f16, readable(FP.FADED_TEXT, bg), r.x + text_x, ty + S(1))
            y += pack_row_h

        # -- Item card -------------------------------------------------------
        body = panel(detail_rect, "Item Card", FP.GOLD)
        y = body.y
        if detail_item is None:
            wrapped("Select an equipped item or pack item to inspect it.",
                    f16, FP.FADED_TEXT, pygame.Rect(body.x, y, body.w, S(80)), line_h=20)
            return
        well = pygame.Rect(body.x, y, isz + S(8), isz + S(8))
        self._ui_well(well)
        self._draw_menu_icon(detail_item, well.x + S(4), well.y + S(4))
        title_x = well.right + S(14)
        title_font = get_font('heading', 20 if body.w >= S(330) else 18)
        for line in self._wrap_text(display_item(detail_item), title_font, body.right - title_x)[:3]:
            text(line, title_font, FP.GOLD_BRIGHT, title_x, y)
            y += title_font.get_height()
        cls = str(getattr(detail_item, 'item_class', 'item') or 'item')
        slot = str(getattr(detail_item, 'slot', '') or '')
        kind = _cap(cls) if not slot or slot == cls else f"{_cap(cls)}, {_cap(slot)}"
        text(kind, f16, FP.FADED_TEXT, title_x, y + S(2))
        y = max(y + lh + S(12), well.bottom + S(12))

        if actions:
            btn_h = lh + S(10)
            btn_w = (body.w - S(6)) // 2
            for idx, action in enumerate(actions):
                r = pygame.Rect(body.x + (idx % 2) * (btn_w + S(6)),
                                y + (idx // 2) * (btn_h + S(6)), btn_w, btn_h)
                selected = focus == 'actions' and idx == getattr(self, '_charsheet_action_idx', 0)
                row_rect(r, selected=selected, focus=(focus == 'actions'))
                bg = KT.SELECTED if selected and focus == 'actions' else KT.RAISED
                enabled = action.get('enabled', True)
                off = readable(FP.FADED_TEXT, bg)
                kr = pygame.Rect(r.x + S(5), r.centery - S(12), S(24), S(24))
                draw_key_badge(screen, kr, action['key'], f16b,
                               color=None if enabled else off)
                text(action['label'], f16, readable(KT.TEXT_BODY, bg) if enabled else off,
                     kr.right + S(8), r.centery - lh // 2)
            y += ((len(actions) + 1) // 2) * (btn_h + S(6)) + S(8)
            y = self._draw_item_action_reasons(body.x, y, body.w, actions, KT.RAISED)
        y = self._draw_item_feedback(body.x, y, body.w, body.bottom, KT.RAISED)

        try:
            visible = self._kit_visible_level(detail_item)
        except Exception:
            visible = int(getattr(detail_item, 'id_level', 5))
        meta_rows = [
            ("Weight", f"{getattr(detail_item, 'weight', 0):g}"),
            ("Identity", _identify_status_label(visible) if hasattr(detail_item, 'id_level') else "-"),
        ]
        if hasattr(detail_item, 'buc'):
            meta_rows.append(("Blessing", _cap(getattr(detail_item, 'buc', 'uncursed'))
                              if getattr(detail_item, 'buc_known', False) else "Unknown"))
        if visible >= 3:
            if hasattr(detail_item, 'ac_bonus'):
                meta_rows.append(("AC", f"+{getattr(detail_item, 'ac_bonus', 0)}"))
            if isinstance(detail_item, Weapon):
                meta_rows.append(("Damage", self._kit_damage_str(detail_item)))
            if getattr(detail_item, 'equip_chain_mode', ''):
                meta_rows.append(("Attune", _quiz_mode_phrase(
                    getattr(detail_item, 'equip_chain_mode', '')).capitalize()))
            res = getattr(detail_item, 'damage_resistances', None) or {}
            if res:
                meta_rows.append(("Resists", ", ".join(f"{_cap(k)} x{v}" for k, v in res.items())))
        lab_w = max(f16.size(lbl)[0] for lbl, _v in meta_rows) + S(14)
        for label, value in meta_rows:
            vlines = self._wrap_text(str(value), f16b, body.w - lab_w - S(8)) or ['']
            if y + lh * len(vlines) > body.bottom:
                break
            text(label, f16, FP.FADED_TEXT, body.x, y)
            for vl in vlines:
                text(vl, f16b, FP.BODY_TEXT, body.x + lab_w, y)
                y += lh + S(2)
        y += S(8)

        def section(title, lines, color=FP.BODY_TEXT):
            nonlocal y
            if not lines or y + 2 * lh > body.bottom:
                return
            text(title, f16b, FP.GOLD_BRIGHT, body.x, y)
            y += lh + S(4)
            for line in lines:
                for seg in self._wrap_text(line, f16, body.w):
                    if y + lh > body.bottom:
                        return
                    text(seg, f16, color, body.x, y)
                    y += lh + S(1)
            y += S(8)

        section("Special Abilities", ability_lines(detail_item))
        tiers = getattr(detail_item, 'tier_bonuses', None)
        if tiers:
            achieved = int(getattr(detail_item, 'achieved_tier', 0) or 0)
            section("Chain Unlocks", [
                f"Tier {t}{' (active)' if t <= achieved else ''}: "
                f"{'; '.join(tier_lines(detail_item, t, 3)) or '?'}" for t in range(1, 6)])
        lore = getattr(detail_item, 'lore', '') if visible >= 4 else ''
        if lore and y + 3 * lh < body.bottom:
            # As many whole sentences as the card holds; X reads the rest.
            text("Lore", f16b, FP.GOLD_BRIGHT, body.x, y)
            y += lh + S(4)
            room = (body.bottom - y - lh - S(4)) // (lh + S(1))
            import re as _re
            sentences = _re.split(r'(?<=[.!?])\s+', display_text(str(lore)))
            shown = []
            for sent in sentences:
                n = len(self._wrap_text(' '.join(shown + [sent]), f16, body.w))
                if n > room:
                    break
                shown.append(sent)
            for seg in self._wrap_text(' '.join(shown), f16, body.w) if shown else []:
                text(seg, f16, FP.LORE_BLUE_BODY, body.x, y)
                y += lh + S(1)
            if len(shown) < len(sentences):
                text("X: read the full lore", f16, FP.HINT_TEXT, body.x, y + S(2))

    def _charsheet_plain_panels(self, p, panel, row_rect, chip, bar, text, wrapped,
                                item_color, display_item, preview_name, ability_lines,
                                tier_lines, leather, focus, detail_item, actions,
                                profile_rect, loadout_rect, pack_rect, detail_rect,
                                font_body, font_bold, font_small, font_tiny, kit):
        """The character sheet's four panels without the art kit (as drawn
        before the kit existed)."""
        from status_effects import EFFECT_INFO
        screen = self.screen
        # Character panel
        body = panel(profile_rect, "Character", FP.GOLD)
        y = body.y
        y = bar(body.x, y, body.w, "HP", p.hp, p.max_hp, FP.DANGER_TEXT)
        y = bar(body.x, y, body.w, "MP", p.mp, p.max_mp, FP.MP_BLUE)
        y = bar(body.x, y, body.w, "SP", p.sp, p.max_sp, FP.SP_GREEN)
        y += S(10)
        chip_w = (body.w - S(10)) // 2
        for idx, (name, value) in enumerate([
            ("STR", p.STR), ("CON", p.CON), ("DEX", p.DEX),
            ("INT", p.INT), ("WIS", p.WIS), ("PER", p.PER),
        ]):
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + S(10)), y + (idx // 2) * S(29),
                            chip_w, S(24))
            row_rect(r)
            text(name, font_tiny, FP.FADED_TEXT, r.x + S(7), r.y + S(5))
            col = FP.GOLD_BRIGHT if value >= 13 else FP.DANGER_TEXT if value < 10 else FP.BODY_TEXT
            text(str(value), font_bold, col, r.right - S(36), r.y + S(3))
        y += S(94)
        metrics = [
            ("AC", str(p.get_ac()), FP.SUCCESS_TEXT if p.get_ac() <= 5 else FP.GOLD_BRIGHT),
            ("Sight", str(p.get_sight_radius()), FP.BODY_TEXT),
            ("Clock", f"{p.combat_clock()}s", FP.GOLD_BRIGHT),
            ("Spells", str(len(getattr(p, 'known_spells', {}))), FP.MP_BLUE_TEXT),
            # What Dexterity and Constitution are doing for you right now.
            ("Dodge", f"{round(100 * p.dodge_chance())}%", FP.BODY_TEXT),
            ("Tough", f"{round(100 * p.toughness())}%", FP.BODY_TEXT),
        ]
        for idx, (label, value, col) in enumerate(metrics):
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + S(10)), y + (idx // 2) * S(27),
                            chip_w, S(22))
            row_rect(r)
            text(label, font_tiny, FP.FADED_TEXT, r.x + S(7), r.y + S(4))
            text(value, font_bold, col, r.x + S(58), r.y + S(3))
        y += S(95)
        text("Effects", font_bold, FP.GOLD_BRIGHT, body.x, y)
        y += S(22)
        chips = []
        _cwt, _clim, _cstate = carry_state(p)
        if _cstate:          # the load, first: it is why the steps are slow
            chips.append((_cstate, carry_color(_cstate)))
        for eid, dur in getattr(p, 'status_effects', {}).items():
            if dur == 0:
                continue
            info = EFFECT_INFO.get(eid)
            name, col = (info[0], info[1]) if info else (eid.replace('_', ' ').title(), FP.BODY_TEXT)
            chips.append((f"{name} {dur}" if dur > 0 else name, col))
        for idx, (label, col) in enumerate(chips[:4]):
            r = pygame.Rect(body.x + (idx % 2) * (chip_w + S(10)), y + (idx // 2) * S(27),
                            chip_w, S(22))
            row_rect(r)
            wrapped(label, font_small, col,
                    pygame.Rect(r.x + S(7), r.y + S(5), r.w - 2 * S(7), r.h - S(7)),
                    line_h=12, max_lines=1)
        y += S(62)
        text("Resistances", font_bold, FP.GOLD_BRIGHT, body.x, y)
        y += S(22)
        for dtype, mult in list(getattr(p, 'resistances', {}).items())[:5]:
            if y + S(18) > body.bottom:
                break                 # a short window: never draw past the panel
            col = FP.SUCCESS_TEXT if mult < 1 else FP.DANGER_TEXT
            text(dtype.title(), font_body, FP.BODY_TEXT, body.x, y)
            text(f"x{mult:.2f}", font_bold, col, body.x + S(110), y)
            y += S(21)

        # Loadout panel
        body = panel(loadout_rect, "Loadout", FP.CYAN_ACCENT)
        loadout = self._charsheet_loadout_entries()
        summary_h = S(108)
        slot_row_count = max(1, (len(loadout) + 1) // 2)
        row_h = max(S(40), min(S(54), (body.h - summary_h - S(12)) // slot_row_count))
        col_w = (body.w - S(10)) // 2
        for idx, entry in enumerate(loadout):
            r = pygame.Rect(body.x + (idx % 2) * (col_w + S(10)),
                            body.y + (idx // 2) * row_h, col_w, row_h - S(5))
            selected = idx == getattr(self, '_charsheet_loadout_idx', 0)
            row_rect(r, selected=selected, focus=(focus == 'loadout'))
            text(entry['label'], font_tiny, FP.FADED_TEXT, r.x + S(7), r.y + S(5))
            item = entry.get('item')
            name = preview_name(item, r.w - 2 * S(7), selected=selected)
            wrapped(name, font_small, item_color(item),
                    pygame.Rect(r.x + S(7), r.y + S(17), r.w - 2 * S(7), r.h - S(17)),
                    line_h=13, max_lines=2)

        summary = pygame.Rect(body.x, body.bottom - summary_h, body.w, summary_h)
        if not (kit and ui_theme.draw_piece(screen, 'card', summary, body_color=KT.RAISED)):
            pygame.draw.rect(screen, FP.MIDNIGHT, summary, border_radius=6)
            pygame.draw.rect(screen, FP.ARCANE_DIM, summary, 1, border_radius=6)
        text("Kit Summary", font_bold, FP.GOLD_BRIGHT, summary.x + S(10), summary.y + S(8))
        _load = carry_state(p)
        _n_pack = len(self._charsheet_pack_entries(filtered=False))   # every item; no 26 cap
        for i, (label, value, col) in enumerate([
            ("Armor", f"AC {p.get_ac()}", FP.SUCCESS_TEXT),
            ("Carrying", carry_numbers(p) + (f"  {_load[2]}" if _load[2] else ""),
             carry_color(_load[2])),
            ("Flat DR", " / ".join(f"{k[:3]} {v}" for k, v in getattr(p, 'damage_resistances', {}).items()) or "-",
             FP.MP_BLUE_TEXT),
            ("Pack", f"{_n_pack} item{'' if _n_pack == 1 else 's'}", FP.BODY_TEXT),
        ]):
            yy = summary.y + S(32) + i * S(19)
            text(label, font_small, FP.FADED_TEXT, summary.x + S(10), yy)
            text(value, font_bold, col, summary.x + S(92), yy)

        # Pack panel
        body = panel(pack_rect, "Pack", FP.GOLD)
        active_filter = self._charsheet_current_pack_filter()
        tab_labels = [
            ("1 All", "all", FP.GOLD),
            ("2 Gear", "gear", FP.CYAN_ACCENT),
            ("3 Food", "food", FP.SUCCESS_TEXT),
            ("4 Lore", "lore", FP.MP_BLUE_TEXT),
        ]
        tab_w = (body.w - S(18)) // 4
        y = body.y
        for idx, (label, key, col) in enumerate(tab_labels):
            r = pygame.Rect(body.x + idx * (tab_w + S(6)), y, tab_w, S(26))
            active = key == active_filter
            if kit:
                self._ui_chip(r, label, active=active, color=col)
                continue
            pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                             r, border_radius=5)
            pygame.draw.rect(screen, col if active else FP.ARCANE_DIM, r, 1, border_radius=5)
            s = font_small.render(label, True, FP.BODY_TEXT)
            screen.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
        y += S(36)
        pack = self._charsheet_pack_entries()
        pack_total = len(self._charsheet_pack_entries(filtered=False))
        filter_label = active_filter.title()
        count_y = y
        text(self._charsheet_count_label(active_filter, len(pack), pack_total), font_bold, FP.SUCCESS_TEXT, body.x, count_y)
        y += S(26)
        pack_row_h = S(57)
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
            screen.blit(range_s, (body.right - range_s.get_width(), count_y + S(2)))
        if not pack:
            empty = "No items in this filter."
            wrapped(empty, font_body, FP.FADED_TEXT,
                    pygame.Rect(body.x, y + S(8), body.w, S(50)), line_h=17)
        icon_x = S(40)
        text_x = icon_x + self.MENU_ICON_SIZE - S(4)      # 68 at UI scale 1
        for idx, entry in enumerate(pack[scroll:scroll + visible_rows], start=scroll):
            r = pygame.Rect(body.x, y, body.w, pack_row_h - S(6))
            selected = idx == pack_idx
            row_rect(r, selected=selected, focus=(focus == 'pack'))
            chip(pygame.Rect(r.x + S(7), r.y + S(8), S(25), S(23)), entry['letter'], leather)
            item = entry['item']
            self._draw_menu_icon(item, r.x + icon_x, r.y + S(8))
            name = display_item(item)
            wrapped(name, font_bold, item_color(item),
                    pygame.Rect(r.x + text_x, r.y + S(5), r.w - text_x - S(9), S(31)),
                    line_h=15, max_lines=2)
            try:
                idl = self._kit_visible_level(item)
                id_text = _identify_status_label(idl)
            except Exception:
                id_text = "Unknown"
            _kind = str(getattr(item, 'slot', None) or getattr(item, 'item_class', 'item'))
            meta = f"{_kind.replace('_', ' ').title()}   Wt {getattr(item, 'weight', 0):g}   {id_text}"
            text(meta, font_tiny, FP.FADED_TEXT, r.x + text_x, r.bottom - S(15))
            y += pack_row_h

        # Detail / actions panel
        body = panel(detail_rect, "Item Card", FP.GOLD)
        y = body.y
        if detail_item is None:
            wrapped("Select an equipped item or pack item to inspect it.",
                    font_body, FP.FADED_TEXT, pygame.Rect(body.x, y, body.w, S(80)), line_h=17)
        else:
            self._draw_menu_icon(detail_item, body.x, y + S(2))
            title_x = body.x + self.MENU_ICON_SIZE + S(20)
            title_font = get_font('heading', 20 if body.w >= S(330) else 17)
            title_lines = self._wrap_text(display_item(detail_item), title_font, body.right - title_x)
            for line in title_lines[:4]:
                text(line, title_font, FP.GOLD_BRIGHT, title_x, y)
                y += S(22)
            text(f"{getattr(detail_item, 'item_class', 'item')} / {getattr(detail_item, 'slot', getattr(detail_item, 'item_class', 'item'))}",
                 font_body, FP.FADED_TEXT, title_x, y + S(1))
            y = max(y + S(28), body.y + S(64))

            if actions:
                cols = 2
                btn_h = S(29)
                btn_w = (body.w - S(6)) // 2
                for idx, action in enumerate(actions):
                    r = pygame.Rect(body.x + (idx % cols) * (btn_w + S(6)),
                                    y + (idx // cols) * S(35), btn_w, btn_h)
                    selected = focus == 'actions' and idx == getattr(self, '_charsheet_action_idx', 0)
                    row_rect(r, selected=selected, focus=(focus == 'actions'))
                    enabled = action.get('enabled', True)
                    text(action['key'], font_bold, FP.GOLD_BRIGHT if enabled else FP.FADED_TEXT,
                         r.x + S(8), r.y + S(7))
                    text(action['label'], font_small, FP.BODY_TEXT if enabled else FP.FADED_TEXT,
                         r.x + S(30), r.y + S(7))
                y += ((len(actions) + 1) // 2) * S(35) + S(10)
                y = self._draw_item_action_reasons(body.x, y, body.w, actions, FP.MIDNIGHT)
            y = self._draw_item_feedback(body.x, y, body.w, body.bottom, FP.MIDNIGHT)

            try:
                visible = self._kit_visible_level(detail_item)
            except Exception:
                visible = int(getattr(detail_item, 'id_level', 5))
            meta_rows = [
                ("Weight", f"{getattr(detail_item, 'weight', 0):g}"),
                ("ID", _identify_status_label(visible) if hasattr(detail_item, 'id_level') else "-"),
            ]
            if hasattr(detail_item, 'buc'):
                meta_rows.append(("Blessing", _cap(getattr(detail_item, 'buc', 'uncursed')) if getattr(detail_item, 'buc_known', False) else "Unknown"))
            if visible >= 3:
                if hasattr(detail_item, 'ac_bonus'):
                    meta_rows.append(("AC", f"+{getattr(detail_item, 'ac_bonus', 0)}"))
                if isinstance(detail_item, Weapon):
                    meta_rows.append(("Damage", self._kit_damage_str(detail_item)))
                if getattr(detail_item, 'equip_chain_mode', ''):
                    meta_rows.append(("Attune", _quiz_mode_phrase(getattr(detail_item, 'equip_chain_mode', '')).capitalize()))
            col_w = (body.w - S(10)) // 2

            def vx_off(label):
                # the value starts after its label (was a fixed 66 px, which
                # cut "Identified" short in a narrow card)
                return S(66) if not kit else max(S(40), font_tiny.size(label)[0] + S(16))
            for idx, (label, value) in enumerate(meta_rows[:6]):
                r = pygame.Rect(body.x + (idx % 2) * (col_w + S(10)),
                                y + (idx // 2) * S(28), col_w, S(24))
                if not (kit and ui_theme.draw_piece(screen, 'card', r, body_color=KT.RAISED)):
                    pygame.draw.rect(screen, FP.MIDNIGHT, r, border_radius=5)
                text(label, font_tiny, FP.FADED_TEXT, r.x + S(7), r.y + S(5))
                wrapped(str(value), font_small, FP.BODY_TEXT,
                        pygame.Rect(r.x + vx_off(label), r.y + S(5), r.w - vx_off(label) - S(6), r.h - S(6)),
                        line_h=12, max_lines=1)
            y += ((len(meta_rows[:6]) + 1) // 2) * S(28) + S(10)

            res = getattr(detail_item, 'damage_resistances', None) or {}
            if visible >= 3 and res:
                r = pygame.Rect(body.x, y, body.w, S(42))
                if not (kit and ui_theme.draw_piece(screen, 'card', r, body_color=KT.RAISED)):
                    pygame.draw.rect(screen, FP.MIDNIGHT, r, border_radius=5)
                text("Resist", font_tiny, FP.FADED_TEXT, r.x + S(7), r.y + S(6))
                wrapped(", ".join(f"{k.title()} x{v}" for k, v in res.items()),
                        font_small, FP.BODY_TEXT,
                        pygame.Rect(r.x + S(78), r.y + S(6), r.w - S(86), r.h - S(8)),
                        line_h=14)
                y += r.h + S(8)

            text("Special Abilities", font_bold, FP.GOLD_BRIGHT, body.x, y)
            y += S(22)
            for line in ability_lines(detail_item)[:6]:
                for seg in self._wrap_text(line, font_small, body.w)[:2]:
                    if y + S(14) > body.bottom - S(88):
                        break
                    text(seg, font_small, FP.BODY_TEXT, body.x, y)
                    y += S(15)
                if y + S(14) > body.bottom - S(88):
                    break
            y += S(8)

            tiers = getattr(detail_item, 'tier_bonuses', None)
            if tiers and y + S(58) < body.bottom:
                text("Chain Unlocks", font_bold, FP.GOLD_BRIGHT, body.x, y)
                y += S(23)
                achieved = int(getattr(detail_item, 'achieved_tier', 0) or 0)
                if body.w < S(340):
                    chip_gap = S(6)
                    chip_w = (body.w - chip_gap * 4) // 5
                    for tier in range(1, 6):
                        active = tier <= achieved
                        r = pygame.Rect(body.x + (tier - 1) * (chip_w + chip_gap), y, chip_w, S(28))
                        pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                                         r, border_radius=5)
                        pygame.draw.rect(screen, FP.SUCCESS_TEXT if tier == achieved else FP.GOLD_DARK if active else FP.ARCANE_DIM,
                                         r, 1, border_radius=5)
                        s = font_bold.render(f"T{tier}", True, FP.SUCCESS_TEXT if active else FP.FADED_TEXT)
                        screen.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
                    y += S(38)
                    active = "; ".join(tier_lines(detail_item, max(1, achieved), 3))
                    wrapped(f"T{achieved} active: {active}", font_small, FP.BODY_TEXT,
                            pygame.Rect(body.x, y, body.w, body.bottom - y), line_h=14, max_lines=3)
                else:
                    for tier in range(1, 6):
                        if y + S(34) > body.bottom:
                            break
                        active = tier <= achieved
                        detail = "; ".join(tier_lines(detail_item, tier, 2)) or "?"
                        lines = self._wrap_text(detail, font_small, body.w - S(58))
                        r = pygame.Rect(body.x, y, body.w, max(S(31), S(10) + len(lines[:2]) * S(14)))
                        pygame.draw.rect(screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                                         r, border_radius=5)
                        pygame.draw.rect(screen, FP.SUCCESS_TEXT if tier == achieved else FP.GOLD_DARK if active else FP.ARCANE_DIM,
                                         r, 1, border_radius=5)
                        chip(pygame.Rect(r.x + S(7), r.y + S(6), S(34), S(20)), f"T{tier}",
                             FP.SUCCESS_TEXT if active else leather,
                             FP.MIDNIGHT if active else FP.BODY_TEXT)
                        wrapped(detail, font_small, FP.BODY_TEXT if active else FP.FADED_TEXT,
                                pygame.Rect(r.x + S(50), r.y + S(7), r.w - S(58), r.h - S(9)),
                                line_h=14, max_lines=2)
                        y += r.h + S(5)


    def _draw_character_sheet(self):
        self._draw_character_pack_sheet()

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
            # One colour for the three choices: green / lavender / yellow
            # meant nothing (VISUAL_REVIEW, cow_encounter).
            options = [
                {'key': '1', 'label': 'Feed the cow (costs an ingredient)',
                 'color': FP.PARCHMENT_LIGHT},
                {'key': '2', 'label': 'Walk away. That was weird.',
                 'color': FP.PARCHMENT_LIGHT},
                {'key': '3', 'label': 'Poke the cow.',
                 'color': FP.PARCHMENT_LIGHT},
            ]
            footer = "1-3: choose   |   Esc: walk away"
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

    def _draw_emberpup_encounter(self):
        """The abandoned Emberpup's screen (emberpup_encounter.py): its
        picture on the left, the phase's words or choices on the right.
        Sized to what the phase holds and centred, like the NPC encounter."""
        import emberpup_encounter as ep
        d = ep.data()
        pup = getattr(self, '_emberpup_npc', None)
        phase = getattr(self, '_emberpup_phase', 'options')
        border = FP.AMBER_ACCENT

        draw_overlay(self.screen, 190)
        kit = bool(panel_band('panel', pygame.Rect(0, 0, S(860), S(400))))
        bw = min(S(860), layout.WINDOW_W - S(48))
        b = S(16) if kit else 0
        inner_w = bw - 2 * (b + S(28)) if kit else bw - 2 * S(30)
        pic = lore_art.plate('monster', d['sprite_id'], S(192))
        pic_w = (pic.get_width() + S(24)) if pic is not None else 0
        text_w = inner_w - pic_w
        font = get_font('body', 18)
        line_h = font.get_height() + S(4)
        row_h = S(50)
        irow_h = S(44)          # a 28 px key badge: a shorter one let a tall letter poke out over the row edge

        def text_h(paras):
            n = sum(len(self._wrap_text(display_text(p), font, text_w)) for p in paras)
            return n * line_h + max(0, len(paras) - 1) * S(10)

        if phase == 'story':
            paras = list(d['story'])
            content_h = text_h(paras)
        elif phase == 'options':
            fed = getattr(pup, '_emberpup_fed', False)
            paras = [d['waiting_fed'] if fed else d['waiting_unfed']]
            content_h = text_h(paras) + S(14) + 4 * (row_h + S(8))
        elif phase == 'select_food':
            paras = [d['pick_food']]
            content_h = text_h(paras) + S(12) + min(ep.FOOD_PAGE, len(self._emberpup_food)) * (irow_h + S(6))
        else:
            paras = [getattr(self, '_emberpup_text', '') or '']
            content_h = text_h(paras)
        content_h = max(content_h, pic.get_height() + S(8) if pic is not None else 0)
        head_h = S(48)
        foot_h = S(8) + key_hints_height() + S(32)
        bh = 2 * b + head_h + S(18) + content_h + S(10) + foot_h
        bh = max(S(240), min(bh, layout.WINDOW_H - S(48)))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        if panel_band('panel', panel):
            b = panel_band('panel', panel)
            body_top = self._ui_header(panel, d['title'], border_color=border, h=48)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body_rect = pygame.Rect(bx + b + S(28), body_top + S(4),
                                    bw - 2 * (b + S(28)), foot_bottom - body_top - S(4))
        else:
            draw_header_bar(self.screen, (bx, by, bw, S(44)),
                            text=d['title'],
                            font=get_font('heading', 20),
                            text_color=FP.GOLD_BRIGHT,
                            accent=border,
                            frame=(panel, border))
            draw_divider(self.screen, bx + S(20), by + S(54), bw - 2 * S(20))
            body_rect = pygame.Rect(bx + S(30), by + S(72), bw - 2 * S(30), bh - S(124))

        if pic is not None:
            well = pygame.Rect(body_rect.x, body_rect.y, pic.get_width() + S(8),
                               pic.get_height() + S(8))
            pygame.draw.rect(self.screen, FP.MIDNIGHT, well)
            self.screen.blit(pic, (well.x + S(4), well.y + S(4)))
            pygame.draw.rect(self.screen, border, well, 1)
        tx = body_rect.x + pic_w
        col = pygame.Rect(tx, body_rect.y, body_rect.right - tx, body_rect.h)

        y = col.y
        for i, p in enumerate(paras):
            if i:
                y += S(10)
            y = self._ui_wrap_text(display_text(p), font, FP.PARCHMENT_LIGHT,
                                   pygame.Rect(col.x, y, col.w, col.bottom - y), line_gap=4)

        if phase == 'story':
            self._ui_footer(panel, "Enter / Space: continue   |   Esc: walk away")
        elif phase == 'options':
            y += S(14)
            for key, which in (('1', 'feed'), ('2', 'ignore'), ('3', 'attack'), ('4', 'choose')):
                self._ui_action_row(pygame.Rect(col.x, y, col.w, row_h), key,
                                    display_text(d['options'][which]), color=FP.PARCHMENT_LIGHT)
                y += row_h + S(8)
            self._ui_footer(panel, "1-4: choose   |   Esc: leave it be")
        elif phase == 'select_food':
            y += S(12)
            food = self._emberpup_food
            top = self._emberpup_food_scroll
            list_rect = pygame.Rect(col.x, y, col.w - S(10), col.bottom - y)
            for i, item in enumerate(food[top:top + ep.FOOD_PAGE]):
                self._ui_action_row(pygame.Rect(list_rect.x, y, list_rect.w, irow_h),
                                    chr(97 + i), self._display_name(item),
                                    color=FP.PARCHMENT_LIGHT)
                y += irow_h + S(6)
            self._ui_scrollbar(list_rect, top, len(food), ep.FOOD_PAGE, color=border)
            self._ui_footer(panel, "a-i: give   |   Up/Down: scroll   |   Esc: back")
        else:
            self._ui_footer(panel, "Enter / Space / Esc: continue")

    def _draw_npc_encounter(self):
        """Draw the NPC moral encounter overlay — multi-phase.

        The panel is sized to what the phase holds and centred on the window
        (VISUAL_REVIEW minor 3: the text filled the top fifth of a tall,
        mostly empty panel). The title is gold on the plaque like every
        other title (it took the NPC's colour, dim lavender); the body is
        set at the reading size of the other modals (20 px)."""
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
        kit = bool(panel_band('panel', pygame.Rect(0, 0, S(860), S(400))))
        bw = min(S(860), layout.WINDOW_W - S(48))
        b = S(16) if kit else 0
        text_w = bw - 2 * (b + S(28)) if kit else bw - 2 * S(30)
        font = get_font('body', 20)
        line_h = font.get_height() + S(4)
        row_h = S(58)
        # The scene text after text_variants, and only the options the hero
        # can see (requires / hidden_group), up to four (encounter_schema).
        scene = getattr(self, '_npc_encounter_text', None) or enc['text']
        visible = self._npc_visible_options() if phase == 'options' else []
        if phase == 'text':
            content_h = len(self._wrap_text(display_text(scene), font, text_w)) * line_h
        elif phase == 'options':
            content_h = S(32) + len(visible) * (row_h + S(10))
        elif phase == 'select_item':
            content_h = S(54) + min(9, len(self._npc_item_list)) * (S(36) + S(6))
        else:
            content_h = len(self._wrap_text(display_text(self._npc_outcome_text or ''),
                                            font, text_w)) * line_h
        head_h = S(48)
        foot_h = S(8) + key_hints_height() + S(32)
        bh = 2 * b + head_h + S(18) + content_h + S(10) + foot_h
        bh = max(S(240), min(bh, layout.WINDOW_H - S(48)))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        b = panel_band('panel', panel)
        if b:
            # Plaque with the encounter's name; the phase chip at its right
            # end, clear of the title (right_reserve).
            body_top = self._ui_header(panel, enc['name'].upper(), border_color=border,
                                       h=48, right_reserve=S(160), left_reserve=S(160))
            hr = header_rect(panel, S(48))
            self._ui_chip(pygame.Rect(hr.right - S(40) - S(110),
                                      hr.y + (hr.h - S(4) - S(28)) // 2, S(110), S(28)),
                          display_title(phase_label), active=True, color=border)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body_rect = pygame.Rect(bx + b + S(28), body_top + S(4),
                                    bw - 2 * (b + S(28)), foot_bottom - body_top - S(4))
        else:
            draw_header_bar(self.screen, (bx, by, bw, S(44)),
                            text=enc['name'].upper(),
                            font=get_font('heading', 20),
                            text_color=FP.GOLD_BRIGHT,
                            accent=border,
                            frame=(panel, border))
            self._ui_chip(pygame.Rect(bx + bw - S(136), by + S(10), S(110), S(28)),
                          phase_label, active=True, color=border)
            draw_divider(self.screen, bx + S(20), by + S(54), bw - 2 * S(20))

            body_rect = pygame.Rect(bx + S(30), by + S(72), bw - 2 * S(30), bh - S(124))

        if phase == 'text':
            self._ui_wrap_text(display_text(scene), font, FP.PARCHMENT_LIGHT,
                               body_rect, line_gap=4)
            self._ui_footer(panel, "Enter / Space: continue   |   Esc: walk away")
            return

        if phase == 'options':
            y = body_rect.y
            self._ui_blit_text("Choose what you do next.",
                               get_font('body', 18), FP.FADED_TEXT,
                               body_rect.x, y)
            y += S(32)
            for i, (_raw, opt) in enumerate(visible):
                row = pygame.Rect(body_rect.x, y, body_rect.w, row_h)
                self._ui_action_row(row, str(i + 1), display_text(opt['label']),
                                    color=FP.PARCHMENT_LIGHT)
                y += row_h + S(10)
            self._ui_footer(panel, "1-3: choose   |   Esc: walk away")
            return

        if phase == 'select_item':
            selected = getattr(self, '_npc_selected_option', None) or {}
            y = body_rect.y
            self._ui_wrap_text(display_text(selected.get('label', 'Choose an item to give:')),
                               get_font('body', 18), FP.PARCHMENT_LIGHT,
                               pygame.Rect(body_rect.x, y, body_rect.w, S(44)),
                               line_gap=2, max_lines=2)
            y += S(54)
            items = self._npc_item_list
            visible = items[self._npc_item_scroll:self._npc_item_scroll + 9]
            irow_h = S(36)
            list_rect = pygame.Rect(body_rect.x, y, body_rect.w - S(10),
                                    body_rect.bottom - y)
            for i, item in enumerate(visible):
                row = pygame.Rect(list_rect.x, y, list_rect.w, irow_h)
                self._ui_action_row(row, chr(97 + i), self._display_name(item),
                                    color=FP.PARCHMENT_LIGHT)
                y += irow_h + S(6)
            self._ui_scrollbar(list_rect, self._npc_item_scroll,
                               len(items), 9, color=border)
            self._ui_footer(panel, "a-z: select item   |   Up/Down: scroll   |   Esc: back")
            return

        if phase == 'outcome':
            self._ui_wrap_text(display_text(self._npc_outcome_text), font,
                               FP.PARCHMENT_LIGHT, body_rect, line_gap=4)
            self._ui_footer(panel, "Enter / Space / Esc: continue")
            return

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
                    # a creature whose picture follows its state (the Black
                    # Knight's limb stages) names it in sprite_id
                    mid=getattr(m, 'sprite_id', None) or m.kind,
                    footprint=getattr(m, 'footprint', (1, 1)),
                    symbol=getattr(m, 'symbol', ''))
        # Pet companions: draw with species sprite or color fallback
        for pet in self.pets:
            if pet.alive and (pet.x, pet.y) in self.visible:
                if getattr(pet, 'is_sketch', False):
                    # Sketched pets use the monster's sprite with a lavender tint
                    self.renderer.draw_entity(
                        pet.x, pet.y, pet.color, cam_x, cam_y, self.visible,
                        mid=pet.monster_kind, tint=(160, 140, 230, 160))
                else:
                    # Sprite lookup must use the species-stage name alone
                    # ("Seedling", "Voltpaw"), not pet.name (which prepends
                    # the nickname — "Fluffy the Seedling" → fails lookup
                    # and used to render as a green square). Fixed 2026-10-03.
                    stage_name = getattr(pet, 'species_name', None) or pet.name
                    mid = stage_name.lower().replace(' ', '_')
                    self.renderer.draw_entity(
                        pet.x, pet.y, pet.color, cam_x, cam_y, self.visible,
                        mid=mid, symbol=getattr(pet, 'symbol', ''))
        # Escorts (escort_system.py): the person's own NPC picture.
        for esc in self._escorts_here():
            if (esc.x, esc.y) in self.visible:
                self.renderer.draw_entity(
                    esc.x, esc.y, esc.color, cam_x, cam_y, self.visible,
                    mid=esc.sprite_id, symbol='@')
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
        self._draw_black_knight_speech()
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

        if self.state not in (STATE_PLAYER, STATE_TARGET) and kit_on():
            self._hush_hud()

        if self.state == STATE_TARGET:
            self._draw_targeting(cam_x, cam_y)
        elif self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_QUIZ_CONTEXT:
            # The context reads on its own over the dimmed play view: drawn
            # over the quiz, the quiz's frame peeked out around it (a double
            # border at 1280x720, VISUAL_REVIEW must-fix 7).
            self._draw_quiz_context_modal()
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
        elif self.state == STATE_INTERCESSION_PROMPT:
            self._draw_intercession_prompt()
        elif self.state == STATE_BOON_MENU:
            self._draw_boon_menu()
        elif self.state == STATE_PRAYER_MENU:
            self._draw_prayer_menu()
        elif self.state == STATE_IDENTIFY_MENU:
            self._draw_identify_menu()
        elif self.state == STATE_PET_NAME_INPUT:
            self._draw_pet_name_popup()
        elif self.state == STATE_PET_MENU:
            self._draw_pet_menu()
        elif self.state == STATE_PET_FEED:
            # The care pickers stand alone (drawn over the companion menu,
            # their frame sliced its Detail text in half: VISUAL_REVIEW).
            self._draw_pet_feed_submenu()
        elif self.state == STATE_PET_HEAL:
            self._draw_pet_heal_submenu()
        elif self.state == STATE_PET_SPECIALS:
            self._draw_pet_specials_submenu()
        elif self.state == STATE_QA_WARP_INPUT:
            self._draw_qa_warp_popup()
        elif self.state == STATE_MESSAGE_LOG:
            self._draw_message_log()
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
        elif self.state == STATE_EMBERPUP:
            self._draw_emberpup_encounter()
        elif self.state == STATE_JUDGMENT:
            self._draw_judgment()

        if self._debug_overlay:
            self._draw_debug_overlay()

        # Effects top-overlay pass: full-screen takeovers (Divine
        # Intercession, Unicorn bond) paint OVER everything else so
        # they can keep running after the quiz state has already
        # transitioned back to STATE_PLAYER. Phase 1 of CHAIN_EFFECTS.
        rt = getattr(self, 'effects_runtime', None)
        if rt is not None:
            rt.draw_top_overlay(self.screen)

        pygame.display.flip()

    # How much of the rails and the log stays under a modal (a multiply,
    # on top of the modal's own dimming overlay).
    _HUSH = (60, 60, 64)

    def _hush_hud(self):
        """Under a modal, darken the side rails and the message log well past
        the modal's own wash: a modal wider than the play area lies over them,
        and its frame edge used to slice rail words in half in readable,
        dimmed text ("Phoenix Rising" at 1920x1080, VISUAL_REVIEW minor 1).
        Now what peeks out beside a frame is a quiet dark field (about 1.1:1),
        never half a word. A multiply on three rects: no allocation."""
        H = self.screen.get_height()
        for r in ((0, 0, layout.MAP_X, H),
                  (layout.MAP_X + layout.MAP_W, 0, self.screen.get_width() - layout.MAP_X - layout.MAP_W, H),
                  (layout.MAP_X, layout.GAME_H, layout.MAP_W, H - layout.GAME_H)):
            if r[2] > 0 and r[3] > 0:
                self.screen.fill(self._HUSH, r, special_flags=pygame.BLEND_RGB_MULT)

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
        if has_target:
            self._draw_target_prompt(f"Strike {proper_name(target_monster.name)}",
                                     [("Enter", "Strike"), ("Tab", "Next"), ("Esc", "Cancel")],
                                     KT.TEXT_HEAD)
        else:
            self._draw_target_prompt("Nothing to strike here",
                                     [("Arrows", "Aim"), ("Esc", "Cancel")], KT.TEXT_BODY)

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

        # HUD prompt (the kit's plaque, key badges)
        item_name = proper_name(self._throw_potion.name) if self._throw_potion else "Item"
        tname = proper_name(target_monster.name) if target_monster else ''
        if will_hit_blocker:
            status = f"{proper_name(blocker.name)} blocks the path: the {item_name} will hit it"
            keys = [("Arrows", "Aim"), ("Esc", "Cancel")]
            color = FP.WARNING_TEXT
        elif valid and target_monster:
            status = f"Throw the {item_name} at {tname}"
            keys = [("Enter", "Throw"), ("Tab", "Next"), ("Esc", "Cancel")]
            color = KT.TEXT_HEAD
        elif valid and not target_monster:
            status = f"Throw the {item_name} at an empty tile"
            keys = [("Enter", "Throw"), ("Esc", "Cancel")]
            color = KT.TEXT_BODY
        elif not in_range:
            status = f"Out of throwing range ({reach} tiles)"
            keys = [("Arrows", "Aim"), ("Esc", "Cancel")]
            color = FP.WARNING_TEXT
        else:
            status = "No line of sight"
            keys = [("Arrows", "Aim"), ("Esc", "Cancel")]
            color = FP.DANGER_TEXT_LIGHT
        self._draw_target_prompt(status, keys, color)

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

        # The prompt at the bottom of the map, in the kit's plaque with key
        # badges (VISUAL_REVIEW minor 8: raw orange text on the map, and
        # "Out of range" in Observe mode, where nothing is fired).
        tname = proper_name(target_monster.name) if target_monster else ''
        if getattr(self, '_observe_targeting', False):
            status = f"Observe: {tname}" if target_monster else "Observe: nothing here"
            keys = [("Arrows", "Look"), ("Tab", "Next"), ("Enter", "Examine"), ("Esc", "Cancel")]
            color = KT.TEXT_HEAD
        elif getattr(self, '_wand_targeting', False):
            status = f"Zap at {tname}" if target_monster else "Aim the wand"
            keys = [("Arrows", "Aim"), ("Tab", "Next"), ("Enter", "Zap"), ("Esc", "Cancel")]
            color = KT.TEXT_HEAD
        elif valid_shot:
            status = f"Fire at {tname}"
            keys = [("Enter", "Shoot"), ("Tab", "Next"), ("Esc", "Cancel")]
            color = FP.SUCCESS_TEXT
        elif target_monster and not has_los:
            status = f"No line of sight to {tname}"
            keys = [("Arrows", "Move"), ("Esc", "Cancel")]
            color = FP.DANGER_TEXT_LIGHT
        elif not in_reach:
            status = "Out of range"
            keys = [("Arrows", "Move"), ("Esc", "Cancel")]
            color = FP.WARNING_TEXT
        else:
            status = "No target"
            keys = [("Arrows", "Move"), ("Tab", "Next"), ("Esc", "Cancel")]
            color = KT.TEXT_BODY
        self._draw_target_prompt(status, keys, color)

    def _draw_target_prompt(self, status: str, keys, color):
        """A targeting prompt at the foot of the map: a flat plaque with a
        gold hairline, the status in words, the keys as badges."""
        f = get_font('body', 18, bold=True)
        kh = key_hints_height()
        pad = S(10)
        ss = f.render(status, True, readable(color, KT.PLAQUE))
        from fantasy_ui import key_hint_fonts, _hints_width
        kf, lf = key_hint_fonts(16)
        keys_w = _hints_width(keys, kf, lf, S(20), S(7), S(8))
        room = layout.MAP_W - 2 * S(8)
        if ss.get_width() + S(24) + keys_w + 2 * pad > room:
            # A narrow map (compact window, portrait monitor): the keys go on
            # a second line under the status instead of shrinking or being cut.
            w = min(room, max(ss.get_width(), keys_w) + 2 * pad)
            h = ss.get_height() + S(6) + kh + 2 * pad
            rect = pygame.Rect(layout.MAP_X + (layout.MAP_W - w) // 2,
                               layout.GAME_H - h - S(10), w, h)
            self.screen.fill(KT.PLAQUE, rect)
            pygame.draw.rect(self.screen, KT.GOLD_DARK, rect, 1)
            self.screen.blit(ss, (rect.centerx - ss.get_width() // 2, rect.y + pad))
            draw_key_hints(self.screen, pygame.Rect(rect.x + pad, rect.bottom - pad - kh,
                                                    rect.w - 2 * pad, kh), keys)
            return
        w = min(room, ss.get_width() + S(24) + keys_w + 2 * pad)
        h = max(ss.get_height(), kh) + 2 * pad
        rect = pygame.Rect(layout.MAP_X + (layout.MAP_W - w) // 2,
                           layout.GAME_H - h - S(10), w, h)
        self.screen.fill(KT.PLAQUE, rect)
        pygame.draw.rect(self.screen, KT.GOLD_DARK, rect, 1)
        self.screen.blit(ss, (rect.x + pad, rect.centery - ss.get_height() // 2))
        kx = rect.x + pad + ss.get_width() + S(24)
        draw_key_hints(self.screen, pygame.Rect(kx, rect.centery - kh // 2,
                                                rect.right - pad - kx, kh),
                       keys, align='left')

    # Subject palette is sourced from FP.SUBJECT so the welcome screen,
    # quiz panel border, and standalone study mode all show the same color
    # for a given subject. Don't redefine this dict — edit fantasy_ui.py.
    _SUBJECT_COLOR = FP.SUBJECT


    _wrap_text = staticmethod(_gh_wrap_text)

    # Chain combat v2: universal chain-milestone ranks. Kept next to the quiz
    # drawer so any other UI (log messages, sidebar) can share the mapping.
    _CHAIN_RANKS = (
        (20, 'Mythic',    (240, 200, 255)),   # rare/legendary; kept white-pink
        (15, 'Prodigy',   (255, 210,  60)),   # gold
        (10, 'Genius',    (240,  80,  60)),   # red
        ( 8, 'Brilliant', (255, 150,  40)),   # orange
        ( 5, 'Sharp',     (240, 220,  80)),   # yellow
        ( 3, 'Solid',     (110, 220, 110)),   # green
    )

    @classmethod
    def _chain_rank(cls, chain: int):
        """Return (rank_name, color) for a chain count. Below 3, returns
        ('', white). Higher milestones win when several apply."""
        for threshold, name, color in cls._CHAIN_RANKS:
            if chain >= threshold:
                return name, color
        return '', (230, 230, 230)

    # ------------------------------------------------------------------
    # Quiz modal layout (Phase 2 beautification, 2026-10-04)
    # ------------------------------------------------------------------

    def _quiz_layout(self, qe, viewport_w: int | None = None,
                     viewport_h: int | None = None) -> dict:
        """Pre-compute the quiz modal layout — shrink-then-scroll.

        Measures the full content block (header + timer + question + the
        choice cards, four or more + status + optional combat HUD) and picks the first
        strategy that fits:
          (1) **base fonts** (``self.font_md`` / ``self.font_sm``) if the
              content already fits inside the viewport,
          (2) **shrunk fonts** (one step down for question + choices)
              if slightly over-tall,
          (3) **smallest fonts + scrolling** if the content is still too
              tall. Only the question + choices block scrolls; header,
              counter, timer, status and combat HUD stay pinned.

        Returns a dict carrying the pre-measured rects, chosen fonts, wrapped
        text, and scroll flags. ``_draw_quiz`` is the sole caller; the shape
        of this dict is a private contract between the two.
        """
        is_combat = (self.combat_target is not None and qe.mode == QuizMode.CHAIN)
        # Width budget: the window (DESIGN_RULES 7: min(1060 s, W - 80)); the
        # panel is centred on it and the rails under it are hushed. Budgeted
        # on the play area left of the right rail, the quiz was 910 px wide at
        # 1280x720 and its answer cards wrapped early (VISUAL_REVIEW minor 11).
        vw = viewport_w if viewport_w is not None else layout.WINDOW_W - S(40)
        vh = viewport_h if viewport_h is not None else layout.WINDOW_H
        win_w = layout.WINDOW_W if viewport_w is None else vw

        # -- Horizontal geometry (font-independent) --------------------
        # Every length is at UI scale 1 and grows with the scale. With the
        # art kit, everything sits inside the painted frame band
        # (``band``; 0 without art, i.e. exactly the old geometry).
        from fantasy_ui import choice_text_insets
        kit = kit_on('quiz')
        band = ui_theme.band('quiz') if kit else 0
        bw = min(S(1060), vw - S(40))
        # Body padding inside the frame band: the ``lg`` step (16). It was
        # the ``xl`` 24, which left each answer card 8 px narrower than it
        # could be and wrapped "...forged into the steel / itself." with the
        # card's last stretch empty (VISUAL_REVIEW_2 minor 2).
        PAD = S(16)
        GAP = S(14)
        inset = band + PAD
        cw = (bw - inset * 2 - GAP) // 2
        c_text_w = cw - sum(choice_text_insets())

        # Fixed chrome heights (header + timer + status + combat HUD are
        # measured off ``get_height`` of the fonts they actually use, so
        # font-size changes elsewhere don't push them out of their rows).
        header_h = max(S(42), self.font_md.get_height() + S(14))
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            # The chain counter always renders in font_lg (fixed slot), so
            # the header must be tall enough for it at every chain length.
            header_h = max(header_h, self.font_lg.get_height() + S(6))
        timer_h  = max(S(28), self.font_sm.get_height() + S(8))
        status_h = max(S(36), self.font_sm.get_height() + S(14))
        if kit:
            # The plaque (its rim below the title), a roomier timer row,
            # and a footer of divider + key badges (key_hints_height).
            header_h = max(S(52), self.font_lg.get_height() + S(8))
            timer_h = max(S(32), self.font_sm.get_height() + S(12))
            status_h = S(32) + key_hints_height()
        combat_h = self._combat_hud_height() if is_combat else 0
        section_gap = S(10)
        # Pinned tail under the question/choices block: optional combat
        # strip, then the key-hint row, each preceded by one section gap.
        tail_h = ((section_gap + combat_h) if is_combat else 0) \
            + section_gap + status_h + (band + S(8) if kit else PAD)

        q_text = display_text(qe.current_question.get('question', ''))
        choices = [display_text(c) for c in qe.current_question.get('choices', [])]
        if qe.confused_order and len(qe.confused_order) == len(choices):
            display_choices = [choices[i] for i in qe.confused_order]
        else:
            display_choices = choices
        # Two columns; every bank question has four choices (two rows), but
        # a malformed question with more extends the grid downward (and the
        # shrink-then-scroll ladder below copes with the extra height)
        # instead of raising (GROUNDWORK_REVIEW 6). Keys 1-4 answer the
        # first four; the cards are always laid out for at least four.
        n_cards = max(4, len(display_choices))
        n_rows = (n_cards + 1) // 2

        # -- Candidate font tiers (base, mid, small) -------------------
        # ``self.font_md`` is get_font('body', 26); ``self.font_sm`` is
        # get_font('body', 20). The shrink tiers step down by ~4 px each.
        from fantasy_ui import get_font as _gf
        base_q = self.font_md
        base_c = self.font_sm
        tiers = [
            (base_q,            base_c),
            (_gf('body', 22),   _gf('body', 17)),
            (_gf('body', 18),   _gf('body', 14)),
        ]
        if is_combat:
            # Math combat: the sum and its answers are a handful of
            # characters, so lead with a larger tier. The normal ladder
            # still follows if a long word problem needs it.
            # The sum uses the plain body face (same family as the answer
            # cards): its lining numerals read far faster than the Cinzel
            # heading face does for arithmetic.
            tiers.insert(0, (_gf('body', 34, bold=True), self.font_md))

        # -- Measure a candidate tier ----------------------------------
        def _measure(q_font, c_font):
            q_lines = self._wrap_text(q_text, q_font, bw - inset * 2)
            q_line_h = q_font.get_height() + S(4)
            q_height = len(q_lines) * q_line_h
            if is_combat:
                # Fixed-height question band so the answer cards sit at the
                # same y for one-line and two-line sums alike.
                q_height = max(q_height, 2 * q_line_h)
            c_line_h = c_font.get_height() + S(3)
            c_wrapped = [self._wrap_text(str(ch), c_font, c_text_w)
                         for ch in display_choices]
            max_c_lines = max((len(w) for w in c_wrapped), default=1)
            ch_height = max(S(52), max_c_lines * c_line_h + S(20))
            scrollable_h = (q_height + section_gap * 2
                            + ch_height * n_rows + GAP * (n_rows - 1))
            total_h = band + header_h + timer_h + section_gap + scrollable_h + tail_h
            return {
                'q_lines': q_lines, 'q_line_h': q_line_h, 'q_height': q_height,
                'c_wrapped': c_wrapped, 'c_line_h': c_line_h,
                'ch_height': ch_height, 'scrollable_h': scrollable_h,
                'total_h': total_h,
                'q_font': q_font, 'c_font': c_font,
            }

        # Viewport cap. Panel is centered with a 20 px margin top/bottom.
        max_panel_h = vh - 2 * S(20)

        measurement = None
        used_tier = 0
        for i, (qf, cf) in enumerate(tiers):
            measurement = _measure(qf, cf)
            used_tier = i
            if measurement['total_h'] <= max_panel_h:
                break

        scrollable = measurement['total_h'] > max_panel_h
        # When scrolling, cap the scrollable_h so the panel exactly fills
        # the viewport minus margins; everything else is pinned.
        if scrollable:
            # Panel height becomes viewport cap; derive the visible slice
            # the scrollable region gets.
            bh = max_panel_h
            fixed_h = band + header_h + timer_h + section_gap + tail_h
            visible_scroll_h = max(S(60), bh - fixed_h)
        else:
            bh = measurement['total_h']
            visible_scroll_h = measurement['scrollable_h']

        bx = (win_w - bw) // 2
        by = max(S(20), (vh - bh) // 2)
        panel_rect = pygame.Rect(bx, by, bw, bh)

        header_rect = pygame.Rect(bx + band, by + band, bw - 2 * band, header_h)
        timer_rect  = pygame.Rect(bx + inset, header_rect.bottom + (S(9) if kit else S(6)),
                                  bw - inset * 2, S(14))

        q_y = header_rect.bottom + timer_h + section_gap
        question_rect = pygame.Rect(bx + inset, q_y, bw - inset * 2,
                                    measurement['q_height'])
        choices_top = q_y + measurement['q_height'] + section_gap * 2
        choice_rects = []
        for i in range(n_cards):
            col = i % 2
            row = i // 2
            cx_ = bx + inset + col * (cw + GAP)
            cy_ = choices_top + row * (measurement['ch_height'] + GAP)
            choice_rects.append(pygame.Rect(cx_, cy_, cw, measurement['ch_height']))

        # The scroll region bounds the question + the rows of choices.
        scroll_rect = pygame.Rect(bx + inset,
                                  header_rect.bottom + timer_h + section_gap,
                                  bw - inset * 2,
                                  visible_scroll_h)

        # Pinned tail, stacked under the scroll area: combat strip (combat
        # only), then the key-hint row at the very bottom of the panel.
        tail_y = scroll_rect.bottom + section_gap
        combat_rect = None
        if is_combat:
            # (the strip's cells sit PAD inside this rect: _combat_hud_slots)
            combat_rect = pygame.Rect(bx + band, tail_y, bw - 2 * band, combat_h)
            tail_y = combat_rect.bottom + section_gap
        status_rect = pygame.Rect(bx + inset, tail_y, bw - inset * 2, status_h)

        # Clamp scroll offset to what the content actually allows.
        content_h = measurement['scrollable_h']
        scroll_max = max(0, content_h - visible_scroll_h)
        scroll_offset = max(0, min(getattr(qe, '_quiz_scroll_offset', 0),
                                   scroll_max))
        qe._quiz_scroll_offset = scroll_offset

        return {
            'panel_rect': panel_rect,
            'header_rect': header_rect,
            'timer_rect': timer_rect,
            'question_rect': question_rect,
            'choice_rects': choice_rects,
            'status_rect': status_rect,
            'combat_rect': combat_rect,
            'scroll_rect': scroll_rect,
            'q_lines': measurement['q_lines'],
            'q_line_h': measurement['q_line_h'],
            'c_wrapped': measurement['c_wrapped'],
            'c_line_h': measurement['c_line_h'],
            'ch_height': measurement['ch_height'],
            'question_font': measurement['q_font'],
            'choice_font': measurement['c_font'],
            'scrollable': scrollable,
            'scroll_offset': scroll_offset,
            'scroll_max': scroll_max,
            'content_h': content_h,
            'visible_scroll_h': visible_scroll_h,
            'display_choices': display_choices,
            'bw': bw, 'bx': bx, 'by': by, 'bh': bh,
            'cw': cw, 'PAD': PAD, 'GAP': GAP, 'band': band, 'inset': inset,
            'header_h': header_h, 'timer_h': timer_h,
            'status_h': status_h, 'combat_h': combat_h,
            'section_gap': section_gap,
            'is_combat': is_combat,
            'font_tier': used_tier,
        }

    @staticmethod
    def _end_accuracy_text(correct: int, wrong: int) -> str:
        """"4 of 9 (44%)": the end screen said "Correct / Wrong : 4 / 5
        (44%)", which read as four out of five."""
        total = correct + wrong
        pct = int(100 * correct / total) if total else 0
        return f"{correct:,} of {total:,}   ({pct}%)"

    @staticmethod
    def _quiz_footer_pairs(qe, is_combat: bool, has_blurb: bool) -> list:
        """The quiz footer's key hints: every key that does something, and
        only those. Combat at chain 0 has no Space hint (it would waste the
        swing exactly like Esc, so it is not a harmless "Cancel"). Other
        quizzes list Esc (gives up: the question counts wrong) and, in a
        chain quiz with a chain built, Space (ends the chain there)."""
        chain_mode = qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN)
        chain = int(getattr(qe, 'chain', 0) or 0)
        if is_combat:
            pairs = [("1-4", "Answer")]
            if chain >= 1:
                pairs.append(("Space", "Strike Now", FP.GOLD_PALE))
            if has_blurb:
                pairs.append(("C", "Context"))
            pairs.append(("Esc", "Abort"))
            return pairs
        pairs = []
        asking = qe.state == QuizState.ASKING
        if asking:
            pairs.append(("1-4", "Answer"))
            if chain_mode and chain >= 1:
                pairs.append(("Space", "Stop Here"))
        if has_blurb:
            pairs.append(("C", "Context"))
        if asking:
            pairs.append(("Esc", "Give Up"))
        return pairs

    def _draw_quiz(self):
        qe = self.quiz_engine
        if not qe.current_question:
            return

        # Legacy ``qe.celebrating`` short-circuit is retired (Phase 1,
        # CHAIN_EFFECTS_PLAN.md, 2026-10-03). The two celebration call
        # sites (Divine Intercession, Unicorn boon) are now driven by
        # ``effects_runtime.fire('..._takeover', {})`` from their
        # on_complete callbacks and painted via
        # ``effects_runtime.draw_top_overlay`` at the end of render().
        # ``_celebrate_on_max`` stays wired in QuizEngine as an escape
        # hatch; no current caller opts in.
        accent     = self._SUBJECT_COLOR.get(qe.subject, (160, 130, 255))
        accent_dim = tuple(max(0, v - 90) for v in accent)

        # -- Overlay ----------------------------------------------------
        draw_overlay(self.screen, 190)

        # -- Pre-computed layout (Phase 2 beautification, 2026-10-04) --
        # ``_quiz_layout`` measures the full content block and either keeps
        # the base font sizes, shrinks the question + choice fonts by one
        # step, or enables scrolling on the question/choices region as a
        # last resort. All rects + fonts come back pre-measured.
        L = self._quiz_layout(qe)
        is_combat   = L['is_combat']
        panel_rect  = L['panel_rect']
        bx, by, bw, bh = L['bx'], L['by'], L['bw'], L['bh']
        PAD = L['PAD']
        HEADER_H    = L['header_h']
        STATUS_H    = L['status_h']
        SECTION_GAP = L['section_gap']
        q_font      = L['question_font']
        c_font      = L['choice_font']
        q_lines     = L['q_lines']
        q_line_h    = L['q_line_h']
        q_height    = L['question_rect'].height
        c_wrapped   = L['c_wrapped']
        display_choices = L['display_choices']

        # Effects background pass -- the chain aura paints a soft border
        # glow around the panel here. Runs BEFORE the opaque panel so
        # anything the handler paints inside the panel's footprint is
        # cleanly covered. See src/effects_runtime.py + src/effects/.
        rt = getattr(self, 'effects_runtime', None)
        if rt is not None:
            rt.draw_background(self.screen, panel_rect)

        # FANTASY: Arcane grimoire quiz panel
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=accent,
                        kind='quiz')

        band = L['band']
        inset = L['inset']
        kit = band > 0
        header_rect = L['header_rect']

        # Mode / progress counter (top-right). Built BEFORE the header so the
        # title can reserve room for it and never overrun it (e.g. a long
        # lockpick/cook title sliding under "Chain xN").
        badge = None          # (rect, rank_name, color) for chain modes
        # Clear of the plaque's scroll-roll end (it nearly touched it at
        # 1280 and 1920: VISUAL_REVIEW minor 9).
        c_right = (header_rect.right - S(54)) if kit else (bx + bw - PAD)
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            # Chain combat: "xN" counter in a fixed-width slot at the right
            # edge, rank badge in its own fixed slot just left of it. Both
            # slots are sized for their widest content, so the header never
            # reflows as the chain climbs -- only colour and digits change.
            rank_name, rank_color = self._chain_rank(qe.chain)
            c_color = rank_color if qe.chain >= 3 else FP.SUCCESS_TEXT
            c_surf = self.font_lg.render(f"x{qe.chain}", True, c_color)
            counter_w = self.font_lg.size("x999")[0]
            badge_w = max(self.font_sm.size(n)[0]
                          for _t, n, _c in self._CHAIN_RANKS) + S(20)
            badge_h = self.font_sm.get_height() + S(6)
            badge_rect = pygame.Rect(
                c_right - counter_w - S(10) - badge_w,
                header_rect.y + (header_rect.h - (S(4) if kit else 0) - badge_h) // 2,
                badge_w, badge_h)
            if rank_name:
                badge = (badge_rect, rank_name, rank_color)
            reserve_w = counter_w + S(10) + badge_w + S(54) + S(6)
        elif int(getattr(qe, 'required', 0) or 0) > 1:
            c_text  = f"{qe.correct_count} / {qe.required}"
            c_color = FP.CYAN_ACCENT
            c_surf = self.font_md.render(c_text, True, c_color)
            reserve_w = c_surf.get_width() + S(54) + S(6)
        else:
            # One-question quizzes (identify, harvest, cook, ...) need no
            # progress counter -- "0 / 1" tells the player nothing.
            c_surf = None
            reserve_w = 0

        if kit:
            self._draw_quiz_plaque(qe, panel_rect, header_rect, accent, reserve_w)
        else:
            draw_header_bar(self.screen, (bx, by, bw, HEADER_H),
                            text=self.quiz_title, font=self.font_md,
                            text_color=FP.GOLD_BRIGHT, accent=accent,
                            right_reserve=reserve_w,
                            frame=(panel_rect, accent, 'quiz'))
        if c_surf is not None:
            fh = header_rect.h - (S(4) if kit else 0)
            self.screen.blit(c_surf, (c_right - c_surf.get_width(),
                                       header_rect.y + (fh - c_surf.get_height()) // 2))
        if badge is not None:
            b_rect, b_name, b_color = badge
            if kit and ui_theme.draw_piece(self.screen, 'chip_active', b_rect):
                b_color = readable(b_color, KT.SELECTED)
            else:
                pygame.draw.rect(self.screen, FP.MIDNIGHT, b_rect, border_radius=5)
                pygame.draw.rect(self.screen, b_color, b_rect, 2, border_radius=5)
            b_surf = self.font_sm.render(b_name, True, b_color)
            self.screen.blit(b_surf, (b_rect.centerx - b_surf.get_width() // 2,
                                       b_rect.centery - b_surf.get_height() // 2))

        # -- Timer bar -------------------------------------------------
        ty        = L['timer_rect'].y
        bar_x     = bx + inset
        bar_w     = bw - inset * 2
        bar_h     = S(14)

        # Tier pip indicator -- 5 small circles (filled = earned, hollow = not yet)
        pip_r   = S(5) if not kit else S(6)
        pip_gap = S(13) if not kit else S(17)
        pip_cx0 = bar_x + pip_r
        pip_cy  = ty + bar_h // 2
        for i in range(5):
            px = pip_cx0 + i * pip_gap
            if i < qe.tier:
                pygame.draw.circle(self.screen, accent, (px, pip_cy), pip_r)
            elif kit:
                pygame.draw.circle(self.screen, accent, (px, pip_cy), pip_r, 2)
            else:
                pygame.draw.circle(self.screen, accent_dim, (px, pip_cy), pip_r, 1)
        tier_offset = 5 * pip_gap + (S(8) if not kit else S(16))
        bar_x += tier_offset
        bar_w -= tier_offset

        # Timer bar -- only rendered for timed quizzes (combat math attack).
        # Untimed quizzes (identify / lockpick / equip / prayer / cooking /
        # magic / etc.) drop the bar entirely so the kid feels invited to
        # read the substantive content the banks now carry. Tier pips above
        # still show progress in escalator-chain modes.
        secs_w = 0
        if getattr(qe, 'timed', True):
            # Seconds readout gets its own slot right of the bar (sized for
            # three digits) instead of being painted over the bar's fill.
            secs_w = self.font_sm.size("000s")[0] + S(8)
            bar_w -= secs_w
            ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))
            t_color = (
                FP.SUCCESS_TEXT if ratio > 0.55 else
                FP.WARNING_TEXT if ratio > 0.28 else
                FP.DANGER_TEXT
            )
            track = pygame.Rect(bar_x, ty, bar_w, bar_h)
            if kit and ui_theme.draw_piece(self.screen, 'bar_track', track):
                inner = track.inflate(-S(4), -S(4))
                if ratio > 0:
                    self.screen.fill(t_color, (inner.x, inner.y,
                                               max(S(2), int(inner.w * ratio)), inner.h))
                for tick in range(1, 5):
                    tx = inner.x + int(inner.w * tick / 5)
                    pygame.draw.line(self.screen, KT.VOID, (tx, inner.y),
                                     (tx, inner.bottom - 1), 1)
                ui_theme.draw_piece(self.screen, 'bar_frame', track, body=False)
                t_color = readable(t_color, KT.INTERIOR)
            else:
                pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, (bar_x, ty, bar_w, bar_h), border_radius=4)
                if ratio > 0:
                    pygame.draw.rect(self.screen, t_color,
                                     (bar_x, ty, max(4, int(bar_w * ratio)), bar_h), border_radius=4)
                # Tick marks every 20%
                for tick in range(1, 5):
                    tx = bar_x + int(bar_w * tick / 5)
                    pygame.draw.line(self.screen, FP.SHADOW, (tx, ty), (tx, ty + bar_h), 1)

            # Timer seconds label -- right-aligned in its slot past the bar
            secs = int(qe.time_remaining)
            t_label = self.font_sm.render(f"{secs}s", True, t_color)
            lx = bar_x + bar_w + secs_w - t_label.get_width()
            ly = ty + (bar_h - t_label.get_height()) // 2
            self.screen.blit(t_label, (lx, ly))

        # -- Scrollable region (question + choices) --------------------
        # When ``L['scrollable']`` is True, the question/choices block has
        # been clipped to ``scroll_rect``; everything else (header, timer,
        # status, combat HUD) stays pinned. See ``_quiz_layout`` for the
        # shrink-then-scroll ladder.
        scroll_rect = L['scroll_rect']
        scroll_off  = L['scroll_offset']
        scrollable  = L['scrollable']

        old_clip = self.screen.get_clip()
        if scrollable:
            self.screen.set_clip(scroll_rect)

        # -- Question text (shifted up by scroll_off) ------------------
        q_top = scroll_rect.y - (scroll_off if scrollable else 0)
        # Combat reserves a fixed-height band and centres the sum in it;
        # every other quiz keeps left-aligned text flush to the top.
        qy = q_top + ((q_height - len(q_lines) * q_line_h) // 2 if is_combat else 0)
        for line in q_lines:
            # Skip lines entirely above the visible slice.
            if scrollable and qy + q_line_h < scroll_rect.y:
                qy += q_line_h
                continue
            if scrollable and qy > scroll_rect.bottom:
                break
            surf = q_font.render(line, True, KT.TEXT_QUIZ if kit else FP.VELLUM)
            line_x = (bx + (bw - surf.get_width()) // 2) if is_combat else bx + inset
            self.screen.blit(surf, (line_x, qy))
            qy += q_line_h

        # The answer cards are drawn exactly where ``_quiz_layout`` put them
        # (``L['choice_rects']``, in unscrolled coordinates), shifted by the
        # scroll offset. The layout is the one source of truth: until
        # 2026-10-15 the cards were drawn one section gap (10 px) above the
        # layout's rects (FOUNDATION_REVIEW 2.1).
        dy = -(scroll_off if scrollable else 0)
        choice_rects = [r.move(0, dy) for r in L['choice_rects']]

        # Thin separator midway between the question and the cards.
        sep_y = q_top + q_height + SECTION_GAP
        pygame.draw.line(self.screen, KT.LINE if kit else accent_dim,
                         (bx + inset, sep_y), (bx + bw - inset, sep_y))

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
            card = choice_rects[i]

            # Skip entirely-offscreen cards when scrolling (cheap cull).
            if scrollable and (card.bottom < scroll_rect.y
                               or card.y > scroll_rect.bottom):
                continue

            c_str       = str(choice).strip()
            is_correct  = c_str == correct_str
            is_selected = bool(selected) and c_str == selected

            # In result phase: mark the right answer green, mark the player's
            # wrong pick red. Mid-question: highlight only if pressed (rare —
            # answers are usually atomic key-presses).
            mark_correct   = in_result and is_correct
            mark_incorrect = in_result and is_selected and not is_correct

            draw_choice_button(
                self.screen, tuple(card),
                key_label=str(i + 1),
                text=wrapped_lines,
                key_font=self.font_md,
                text_font=c_font,
                selected=is_selected and not in_result,
                correct=mark_correct or None,
                incorrect=mark_incorrect or None,
            )

        if scrollable:
            self.screen.set_clip(old_clip)
            # Scroll affordances: tiny arrow + "more" marker when there is
            # content hidden above or below the visible slice.
            scroll_max = L['scroll_max']
            arrow_font = self.font_sm
            if scroll_off > 0:
                a = arrow_font.render("▲ more above", True, FP.FADED_TEXT)
                self.screen.blit(
                    a,
                    (scroll_rect.right - a.get_width() - S(2), scroll_rect.y - S(2)),
                )
            if scroll_off < scroll_max:
                a = arrow_font.render("▼ more below", True, FP.FADED_TEXT)
                self.screen.blit(
                    a,
                    (scroll_rect.right - a.get_width() - S(2),
                     scroll_rect.bottom - a.get_height() + S(2)),
                )

        # -- Status / feedback bar -------------------------------------
        status_rect = L['status_rect']
        status_y = status_rect.y

        # No "CORRECT!" / "WRONG!" banner: the green / red choice cards
        # already carry the result (2026-10-04 playtest).
        has_blurb = bool(qe.current_context_blurb())
        if kit:
            # Divider + key badges (the kit's footer), the same keys as below.
            div_y = status_y + S(15)
            draw_divider(self.screen, bx + band + S(30), div_y, bw - 2 * (band + S(30)))
            pairs = self._quiz_footer_pairs(qe, is_combat, has_blurb)
            keys = pygame.Rect(status_rect.x, status_rect.bottom - key_hints_height(),
                               status_rect.w, key_hints_height())
            draw_key_hints(self.screen, keys, pairs)
        elif is_combat:
            # Four fixed key-hint slots across the row, so the hints never
            # move and never run into each other.
            hints = [
                ("1-4  Answer", FP.HINT_TEXT),
                # At chain 0 Space only throws the swing away, as Esc does:
                # it is not offered as a harmless "Cancel".
                ("SPACE  Strike Now" if qe.chain >= 1 else "", FP.GOLD_PALE),
                ("C  Context" if has_blurb else "", FP.FADED_TEXT),
                ("ESC  Abort", FP.FADED_TEXT),
            ]
            slot_w = status_rect.w // len(hints)
            for i, (h_text, h_color) in enumerate(hints):
                if not h_text:
                    continue
                h_font, h_text = self._fit_line(h_text, slot_w - S(8), (20, 17, 14))
                h_surf = h_font.render(h_text, True, h_color)
                slot_x = status_rect.x + i * slot_w
                if i == 0:
                    hx = slot_x
                elif i == len(hints) - 1:
                    hx = status_rect.right - h_surf.get_width()
                else:
                    hx = slot_x + (slot_w - h_surf.get_width()) // 2
                self.screen.blit(
                    h_surf, (hx, status_y + (STATUS_H - h_surf.get_height()) // 2))
        else:
            if qe.state == QuizState.ASKING:
                _txt = "   ".join(f"{k}  {v}" for k, v, *_ in
                                  self._quiz_footer_pairs(qe, False, False))
                hint = self.font_sm.render(_txt, True, FP.HINT_TEXT)
                self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, status_y + S(10)))
            # Context-blurb discoverability hint: only shown when the current
            # (subject, topic) HAS a blurb — hidden otherwise so a bank
            # without authored blurbs doesn't tease the key for nothing.
            if has_blurb:
                c_hint = self.font_sm.render("C  Context", True, FP.FADED_TEXT)
                self.screen.blit(c_hint, (bx + bw - c_hint.get_width() - PAD,
                                           status_y + STATUS_H - c_hint.get_height() - S(2)))

        # -- Combat HUD ------------------------------------------------
        if is_combat:
            self._draw_combat_hud(L['combat_rect'], accent)

        # Effects foreground pass -- the chain aura paints particles /
        # the per-answer pulse ON TOP of the panel, but respects the
        # protected rects below so none of the substantive text or
        # cards is ever occluded. Last step in _draw_quiz by design.
        if rt is not None:
            protected = self._quiz_protected_rects(
                qe=qe,
                panel_rect=panel_rect,
                header_h=HEADER_H,
                timer_rect=pygame.Rect(bar_x, ty, bar_w + secs_w, bar_h) if getattr(qe, 'timed', True) else None,
                question_rect=L['question_rect'],
                choices_rect=choice_rects[0].unionall(choice_rects[1:]),
                status_rect=status_rect,
                pad=PAD,
            )
            rt.draw_foreground(self.screen, protected)

    def _draw_quiz_plaque(self, qe, panel_rect, header_rect, accent, reserve_w):
        """The quiz header in the kit: the plaque (subject accent rule),
        the subject's icon and name at the left, the action title centred,
        and room on the right for the counter / rank badge (drawn by the
        caller). The "  --  SUBJECT" tail of ``quiz_title`` becomes the
        icon + name, so it is not repeated in the title."""
        draw_header_bar(self.screen, header_rect, accent=accent,
                        frame=(panel_rect, accent, 'quiz'))
        hr = header_rect
        field_h = hr.h - S(4)
        cy = hr.y + field_h // 2
        x = hr.x + S(40)
        title = str(self.quiz_title or '')
        head, sep, tail = title.rpartition('  --  ')
        subj = str(getattr(qe, 'subject', '') or '')
        label = subj
        if sep and tail.strip().lower() == subj.lower():
            title = head.strip()          # "IDENTIFYING X  --  PHILOSOPHY"
        isz = S(28)
        if subj and ui_theme.draw_icon(self.screen, f"subject_{subj}",
                                       (x, cy - isz // 2, isz, isz)):
            x += isz + S(8)
        text = display_text(display_title(title.upper()) if title == title.upper() else title)
        hi = hr.right - max(S(52), reserve_w) - S(10)
        lf = get_font('heading', 17)
        label_s = lf.render(display_title(label.upper()), True, KT.TEXT_HEAD) if label else None
        # The title takes what it needs: 26 -> 24 -> 22 px; then the subject
        # word goes (its icon and the accent colour still say it); then the
        # title wraps onto two 22 px lines. It is never cut with an ellipsis.
        lo_with = x + (label_s.get_width() if label_s else 0) + S(20)
        lo_without = x + S(12)
        choice = None
        for lo, show_label in ((lo_with, True), (lo_without, False)):
            for size in (26, 24, 22):
                tf = get_font('heading', size, bold=True)
                if tf.size(text)[0] <= hi - lo:
                    choice = (tf, [text], lo, show_label)
                    break
            if choice:
                break
        if choice is None:
            tf = get_font('heading', 22, bold=True)
            lines = self._wrap_text(text, tf, hi - lo_without)[:2]
            choice = (tf, lines, lo_without, False)
        tf, lines, lo, show_label = choice
        if show_label and label_s is not None:
            self.screen.blit(label_s, (x, cy - label_s.get_height() // 2))
        lh = tf.get_height()
        y0 = cy - (lh * len(lines)) // 2
        for i, line in enumerate(lines):
            tw = tf.size(line)[0]
            tx = max(lo, min(hr.centerx - tw // 2, hi - tw))
            ts = tf.render(line, True, KT.TEXT_HEAD)
            self.screen.blit(ts, (tx, y0 + i * lh))

    def _quiz_protected_rects(self, qe, panel_rect, header_h: int,
                              timer_rect, question_rect, choices_rect,
                              status_rect, pad: int) -> list:
        """Build the list of rects the effects runtime must not paint
        into for an active quiz. Centralised so handlers (and tests)
        can get the same shape -- an effect spilling onto question
        text, choice cards, timer or counter would corrupt readability.
        """
        rects = []
        # Chain / threshold counter rect in the header's right stack.
        band = ui_theme.band('quiz', panel_rect) if kit_on('quiz') else 0
        counter_rect = pygame.Rect(
            panel_rect.x + panel_rect.w - band - pad - S(220), panel_rect.y + band,
            S(220), header_h,
        )
        rects.append(counter_rect)
        if question_rect is not None:
            rects.append(question_rect)
        if choices_rect is not None:
            rects.append(choices_rect)
        if status_rect is not None:
            rects.append(status_rect)
        if timer_rect is not None:
            rects.append(timer_rect)
        return rects

    def _quiz_context_clock_note(self):
        """The context card's one-line clock notice, or None for an
        untimed quiz. A timed clock stops on the first open of the card for
        each question; a second open leaves it running (call 1)."""
        qe = self.quiz_engine
        if not getattr(qe, 'timed', False):
            return None
        if getattr(qe, '_timer_paused', False):
            return ("The clock is stopped while you read. "
                    "You get one stop per question.")
        return ("The clock is running. You already stopped it once "
                "on this question.")

    def _draw_quiz_context_modal(self):
        """Opt-in orientation modal shown over the active quiz.

        Mirrors the chrome of the item/bestiary dossier (``_ui_modal_panel``
        + ``_ui_footer``) so the kid parses it as "another dossier screen",
        not a new widget. The underlying quiz panel is already drawn by the
        state dispatcher before this is called, so the modal reads as a true
        overlay.
        """
        qe = self.quiz_engine
        blurb = qe.current_context_blurb()
        if not blurb:
            # Defensive: should be unreachable because entry into
            # STATE_QUIZ_CONTEXT is gated on a blurb existing. Fall back to
            # a neutral message rather than drawing an empty panel.
            blurb = "No context available for this question."

        blurb = display_text(blurb, sources=True)
        body_font = get_font('body', 20)
        # Call 1 (bug bash 4): a timed clock stops once per question. Say
        # plainly on the card whether it is stopped or running.
        clock_note = self._quiz_context_clock_note()
        # Sized to the blurb (it left a large empty area under the text).
        max_w = 1000
        bw = min(S(max_w), _modal_budget_w() - S(48))
        probe = self._ui_modal_body(pygame.Rect(0, 0, bw, 1000), side=24, top=72, bottom=56)
        reader_w = probe.w - 2 * S(12)
        n = len(self._ui_text_lines(blurb, body_font, reader_w - S(12)))
        if clock_note:
            n += len(self._ui_text_lines(clock_note, body_font, reader_w - S(12))) + 1
        chrome = probe.y + (1000 - probe.bottom) + S(42) + S(12)
        fit_h = chrome + n * (body_font.get_height() + S(5)) + S(6)
        # The quiz's subject colour on the accent layer (it was lore blue on
        # every subject), so the context reads as part of THIS quiz.
        accent = (self._SUBJECT_COLOR.get(getattr(qe, 'subject', None), FP.LORE_BLUE_BORDER)
                  if kit_on() else FP.LORE_BLUE_BORDER)
        panel = self._ui_modal_panel(
            "CONTEXT",
            border_color=accent,
            max_w=max_w,
            max_h=600,
            fit_h=fit_h,
        )
        body = self._ui_modal_body(panel, side=24, top=72, bottom=56)

        # Single-pane body — grimoire reading surface for the blurb.
        reader = self._ui_subpanel(body, "Orientation", border_color=accent)

        lines = []
        if clock_note:
            lines += [(line, FP.GOLD_PALE, body_font)
                      for line in self._ui_text_lines(clock_note, body_font, reader.w - S(12))]
            lines.append(("", FP.LORE_BLUE_BODY, body_font))
        lines += [(line, FP.LORE_BLUE_BODY, body_font)
                  for line in self._ui_text_lines(blurb, body_font, reader.w - S(12))]
        scroll = self._ui_draw_scroll_lines(
            lines, body_font, FP.LORE_BLUE_BODY, reader,
            getattr(self, '_quiz_context_scroll', 0), line_gap=5)
        self._quiz_context_scroll = scroll

        self._ui_footer(panel, "Up/Down: scroll   PgUp/PgDn: jump   C / ESC: close")

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

        # Vignette only over the game viewport (skip sidebar + msg log): a
        # smooth red edge glow, built once per viewport size (it used to be
        # 24 rectangle outlines with gaps between them, rebuilt every
        # frame), faded per frame with the surface alpha.
        gw, gh = layout.MAP_W, layout.GAME_H
        if gw <= 0 or gh <= 0:
            return
        cached = getattr(self, '_death_vig', None)
        if cached is None or cached[0] != (gw, gh):
            vig = pygame.Surface((gw, gh), pygame.SRCALPHA)
            vig.fill((*FP.BLOOD, 0))
            try:
                import numpy as np
                band = max(1.0, min(gw, gh) * 0.35)
                xs = np.minimum(np.arange(gw), np.arange(gw)[::-1])
                ys = np.minimum(np.arange(gh), np.arange(gh)[::-1])
                d = np.minimum(xs[:, None], ys[None, :]) / band
                a = (np.clip(1.0 - d, 0.0, 1.0) ** 1.6) * 255
                pa = pygame.surfarray.pixels_alpha(vig)
                pa[...] = a.astype(np.uint8)
                del pa
            except ImportError:                                  # pragma: no cover
                pass
            cached = self._death_vig = ((gw, gh), vig)
        vig = cached[1]
        vig.set_alpha(alpha)
        self.screen.blit(vig, (layout.MAP_X, 0))

    # NOTE: ``_draw_celebration`` was removed in Phase 1
    # (CHAIN_EFFECTS_PLAN.md, 2026-10-03). The full-screen takeover is
    # now owned by the FullscreenTakeover handler in
    # ``src/effects/fullscreen_takeover.py`` and painted via the
    # EffectsRuntime's ``draw_top_overlay`` phase.

    def _fit_line(self, text: str, max_w: int, sizes, family: str = 'body'):
        """Return ``(font, text)`` for a one-line slot ``max_w`` wide.

        Walks ``sizes`` largest-first and returns the first font the whole
        string fits in. Only when it overflows even at the smallest size is
        the text truncated with an ellipsis -- so long monster / weapon
        names shrink to fit their slot instead of running out of it.
        """
        from text_layout import truncate_label
        font = None
        # DESIGN_RULES 3: nothing a player reads is under 16 px at scale 1.
        sizes = [z for z in sizes if z >= 16] or [16]
        for size in sizes:
            font = get_font(family, size)
            if font.size(text)[0] <= max_w:
                return font, text
        return font, truncate_label(text, max_w, font)

    _COMBAT_HUD_CAP_SIZE = 16

    def _combat_hud_height(self) -> int:
        """Pixel height of the combat strip: caption row, one main row
        (sized for the big damage number) and three detail rows (the third
        is the player's own HP, under the target's)."""
        cap_h = get_font('body', self._COMBAT_HUD_CAP_SIZE).get_height()
        return (S(8) + cap_h + S(2) + self.font_lg.get_height() + S(4)
                + 3 * self.font_sm.get_height() + 2 * S(5) + S(8))

    def _combat_hud_slots(self, bx: int, strip_y: int, bw: int) -> dict:
        """Return the fixed text slots of the combat strip.

        Two cells side by side -- ``target`` and ``strike`` -- each
        with the same four stacked rows: ``cap`` (caption), ``main``,
        ``sub1``, ``sub2``. The target cell additionally splits ``sub1``
        into ``hp_bar`` + ``hp_text``, and the strike cell's caption row
        carries a right-hand ``weapon`` slot. Every string the HUD draws is fitted
        into exactly one of these rects, so nothing is positioned off the
        measured width of a neighbour (the old layout's failure mode).
        Extracted so tests can assert the slots never overlap.
        """
        PAD, CELL_PAD = S(16), S(14)     # PAD matches the quiz body's (_quiz_layout)
        cap_h  = get_font('body', self._COMBAT_HUD_CAP_SIZE).get_height()
        main_h = self.font_lg.get_height()
        sub_h  = self.font_sm.get_height()
        y_cap  = strip_y + S(8)
        y_main = y_cap + cap_h + S(2)
        y_sub1 = y_main + main_h + S(4)
        y_sub2 = y_sub1 + sub_h + S(5)
        y_sub3 = y_sub2 + sub_h + S(5)
        height = self._combat_hud_height()

        inner_w = bw - PAD * 2
        weights = (('target', 5), ('strike', 4))
        total = sum(w for _k, w in weights)
        slots = {}
        x = bx + PAD
        for key, weight in weights:
            w = inner_w * weight // total
            tx, tw = x + CELL_PAD, w - CELL_PAD * 2
            slots[key] = {
                'cell': pygame.Rect(x, strip_y, w, height),
                'cap':  pygame.Rect(tx, y_cap,  tw, cap_h),
                'main': pygame.Rect(tx, y_main, tw, main_h),
                'sub1': pygame.Rect(tx, y_sub1, tw, sub_h),
                'sub2': pygame.Rect(tx, y_sub2, tw, sub_h),
                'sub3': pygame.Rect(tx, y_sub3, tw, sub_h),
            }
            x += w

        # Target HP row: numbers get a slot wide enough for 4-digit HP,
        # the bar takes whatever is left.
        sub1 = slots['target']['sub1']
        hp_w = min(self.font_sm.size("9999/9999 HP")[0], sub1.w // 2)
        bar_h = S(14)
        slots['target']['hp_text'] = pygame.Rect(sub1.right - hp_w, sub1.y,
                                                 hp_w, sub1.h)
        slots['target']['hp_bar'] = pygame.Rect(
            sub1.x, sub1.y + (sub1.h - bar_h) // 2, sub1.w - hp_w - S(10), bar_h)
        # The player's own HP (VISUAL_REVIEW_2 4.5): the rails are covered by
        # the quiz, and a child deciding "Strike Now or keep the chain"
        # needs it. Same bar + numbers as the target's, under it, with a
        # "You" label in front, so the two bars compare at a glance.
        sub3 = slots['target']['sub3']
        you_w = self.font_sm.size("You")[0] + S(10)
        slots['target']['you_label'] = pygame.Rect(sub3.x, sub3.y, you_w, sub3.h)
        slots['target']['you_text'] = pygame.Rect(sub3.right - hp_w, sub3.y, hp_w, sub3.h)
        slots['target']['you_bar'] = pygame.Rect(
            sub3.x + you_w, sub3.y + (sub3.h - bar_h) // 2,
            sub3.w - hp_w - S(10) - you_w, bar_h)

        # Strike caption row: fixed-width caption on the left, the weapon
        # in use right-aligned in whatever remains.
        cap = slots['strike']['cap']
        cap_w = get_font('body', self._COMBAT_HUD_CAP_SIZE).size("STRIKE NOW")[0]
        slots['strike']['weapon'] = pygame.Rect(
            cap.x + cap_w + S(16), cap.y, max(0, cap.w - cap_w - S(16)), cap.h)
        return slots

    def _strike_preview_damage(self) -> int:
        """What pressing Strike Now would deal at the current chain.

        combat.strike_preview runs the same two functions the real blow
        does (combat.effective_chain + combat.strike_damage) without spending
        anything, so the number shown is the number dealt (call 13). Dice
        (rare legacy weapons, a few named weapons' bonus dice) count as
        their average."""
        from combat import strike_preview
        monster = self.combat_target
        if monster is None:
            return 0
        ranged = bool(getattr(self, '_combat_is_ranged', False))
        ammo = getattr(self, '_combat_ammo', None) if ranged else None
        return max(0, int(strike_preview(self.player, monster,
                                         int(self.quiz_engine.chain or 0),
                                         ranged=ranged, ammo=ammo)))

    def _draw_combat_hud(self, rect: pygame.Rect, accent=(80, 80, 180)):
        """Draw the combat strip inside the quiz modal.

        Slot layout (2026-10-04 redesign, see ``_combat_hud_slots``):

          TARGET       monster name / HP bar + numbers / status effects
          STRIKE NOW   weapon / big live damage / chain multiplier /
                       weakness-type tag

        No mechanic change -- same numbers as before, each in its own
        reserved slot. Text shrinks to fit its slot before it truncates.
        """
        from combat import _damage_multiplier
        monster = self.combat_target
        # Use ranged weapon for damage preview if this is a ranged attack
        is_ranged_attack = bool(getattr(self, '_combat_is_ranged', False))
        weapon = self.player.ranged_weapon if is_ranged_attack else self.player.weapon

        slots = self._combat_hud_slots(rect.x, rect.y, rect.w)

        def _label(raw) -> str:
            """'fire_resist' -> 'Fire Resist' for status / damage-type tags."""
            return str(raw).replace('_', ' ').title()

        def put(text, slot, color, sizes=(20, 17, 16), family='body',
                align='left'):
            """Fit ``text`` into ``slot`` and blit it vertically centred."""
            if not text:
                return
            font, fitted = self._fit_line(text, slot.w, sizes, family)
            surf = font.render(fitted, True, color)
            x = slot.right - surf.get_width() if align == 'right' else slot.x
            self.screen.blit(surf, (x, slot.y + (slot.h - surf.get_height()) // 2))

        # -------- Damage maths ------------------------------------------
        dtypes  = weapon.damage_types if weapon else ['blunt']      # bare hands crush
        # the same reckoning the blow itself uses (form x substance)
        from combat import weapon_type_multiplier as _wtm
        _fm, _sm = _wtm(weapon, monster)
        if weapon and getattr(weapon, 'ignore_resistances', False):
            _fm = max(1.0, _fm)
        dm      = _fm * _sm

        # Current chain multiplier — polynomial for `chain_exponent`-set
        # weapons (and unarmed @ 1.15), otherwise the legacy array.
        cur_chain = self.quiz_engine.chain
        _chain_exp = getattr(weapon, 'chain_exponent', None) if weapon else 1.15
        if _chain_exp and _chain_exp > 0:
            def _mult(n: int) -> float:
                return (float(n) ** float(_chain_exp)) if n >= 1 else 0.0
        else:
            _mults_arr = weapon.chain_multipliers if weapon else [0.5, 1.0, 1.5, 2.0, 2.5]
            def _mult(n: int) -> float:
                if n < 1:
                    return 0.0
                return _mults_arr[min(n - 1, len(_mults_arr) - 1)]

        cur_mult = _mult(cur_chain)
        # The big number is the blow's own calculation (call 13), not a
        # sum of its own: Strength, blessing, ammo, shields, scales...
        cur_dmg  = self._strike_preview_damage()
        _rank_name, rank_color = self._chain_rank(cur_chain)
        live_col = rank_color if cur_chain >= 3 else FP.WHITE

        # -------- Frame: top rule, cell dividers, strike-cell box ------
        cx = slots['strike']['cell'].x
        box = pygame.Rect(slots['target']['cell'].x, rect.y,
                          slots['strike']['cell'].right - slots['target']['cell'].x, rect.h)
        if ui_theme.draw_piece(self.screen, 'subpanel', box, body_color=KT.RAISED):
            pygame.draw.line(self.screen, KT.LINE,
                             (cx, rect.y + S(10)), (cx, rect.bottom - S(10)))
        else:
            pygame.draw.line(self.screen, accent,
                             (rect.x + S(18), rect.y), (rect.right - S(18), rect.y))
            pygame.draw.line(self.screen, FP.SHADOW,
                             (cx, rect.y + S(8)), (cx, rect.bottom - S(8)))
        if cur_chain >= 3:
            # The live-damage cell takes on the rank colour as a box frame.
            pygame.draw.rect(self.screen, rank_color,
                             slots['strike']['cell'].inflate(-S(6), -S(8)), 2,
                             border_radius=6)

        # -------- TARGET ----------------------------------------------
        t = slots['target']
        put("TARGET", t['cap'], FP.FADED_TEXT, sizes=(self._COMBAT_HUD_CAP_SIZE,))
        m_name = proper_name(monster.name)
        name_sizes = (26, 22, 18, 15)
        _nf, _fitted = self._fit_line(m_name, t['main'].w, name_sizes)
        if _fitted == m_name:
            put(m_name, t['main'], FP.GOLD_PALE, sizes=name_sizes)
        else:
            # Too long for one line even at the smallest size: the main row
            # is tall enough for two small lines, so wrap instead of cutting
            # the name off.
            wrapped = self._wrap_text(m_name, _nf, t['main'].w)
            if len(wrapped) > 2:
                from text_layout import truncate_label
                wrapped = [wrapped[0],
                           truncate_label(" ".join(wrapped[1:]), t['main'].w, _nf)]
            line_h = _nf.get_height()
            ny = t['main'].y + max(0, (t['main'].h - line_h * len(wrapped)) // 2)
            for line in wrapped:
                self.screen.blit(_nf.render(line, True, FP.GOLD_PALE),
                                 (t['main'].x, ny))
                ny += line_h

        hp_ratio = max(0.0, monster.hp / max(1, monster.max_hp))
        hp_color = (
            FP.SUCCESS_TEXT if hp_ratio > 0.50 else
            FP.WARNING_TEXT if hp_ratio > 0.25 else
            FP.DANGER_TEXT
        )
        bar = t['hp_bar']
        if ui_theme.draw_piece(self.screen, 'bar_track', bar):
            inner = bar.inflate(-S(4), -S(4))
            if hp_ratio > 0:
                self.screen.fill(hp_color, (inner.x, inner.y,
                                            max(S(2), int(inner.w * hp_ratio)), inner.h))
            ui_theme.draw_piece(self.screen, 'bar_frame', bar, body=False)
        else:
            pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, bar, border_radius=4)
            if hp_ratio > 0:
                pygame.draw.rect(self.screen, hp_color,
                                 (bar.x, bar.y, max(3, int(bar.w * hp_ratio)), bar.h),
                                 border_radius=4)
            pygame.draw.rect(self.screen, FP.BURGUNDY, bar, 1, border_radius=4)
        put(f"{monster.hp}/{monster.max_hp} HP", t['hp_text'], hp_color,
            align='right')

        def hp_bar(rect, ratio, color):
            if ui_theme.draw_piece(self.screen, 'bar_track', rect):
                inner = rect.inflate(-S(4), -S(4))
                if ratio > 0:
                    self.screen.fill(color, (inner.x, inner.y,
                                             max(S(2), int(inner.w * ratio)), inner.h))
                ui_theme.draw_piece(self.screen, 'bar_frame', rect, body=False)
            else:
                pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, rect, border_radius=4)
                if ratio > 0:
                    pygame.draw.rect(self.screen, color,
                                     (rect.x, rect.y, max(3, int(rect.w * ratio)), rect.h),
                                     border_radius=4)
                pygame.draw.rect(self.screen, FP.BURGUNDY, rect, 1, border_radius=4)

        # -------- YOU: the player's own HP --------------------------------
        p_hp = getattr(self.player, 'hp', None)
        p_max = getattr(self.player, 'max_hp', None)
        if p_hp is not None and p_max:
            p_ratio = max(0.0, min(1.0, p_hp / max(1, p_max)))
            p_col = (FP.SUCCESS_TEXT if p_ratio > 0.50 else
                     FP.WARNING_TEXT if p_ratio > 0.25 else FP.DANGER_TEXT)
            put("You", t['you_label'], KT.TEXT_DIM, sizes=(20, 17, 16))
            hp_bar(t['you_bar'], p_ratio, p_col)
            put(f"{p_hp}/{p_max} HP", t['you_text'], p_col, align='right')

        # Status effects: all of them when they fit; otherwise as many as
        # fit plus a "+N" count, never a clipped half-word.
        effects = [e for e, v in monster.status_effects.items() if v > 0]
        if effects:
            # Measure at the size it will really be drawn at: _fit_line
            # never goes under 16 px, so a 14 px measure let a row through
            # that then rendered at 16 and was cut mid-word (C15).
            eff_sizes = (20, 17, 16)
            eff_text = "  ".join(f"[{_label(e)}]" for e in effects)
            smallest = get_font('body', eff_sizes[-1])
            if smallest.size(eff_text)[0] > t['sub2'].w:
                for shown in range(len(effects) - 1, 0, -1):
                    eff_text = ("  ".join(f"[{_label(e)}]" for e in effects[:shown])
                                + f"  +{len(effects) - shown}")
                    if smallest.size(eff_text)[0] <= t['sub2'].w:
                        break
            put(eff_text, t['sub2'], FP.WARNING_TEXT, sizes=eff_sizes)

        # -------- STRIKE NOW ------------------------------------------
        s = slots['strike']
        put("STRIKE NOW", s['cap'], FP.FADED_TEXT, sizes=(self._COMBAT_HUD_CAP_SIZE,))
        # As the player knows it: an unidentified blade is not named by
        # its true name on the combat panel.
        # (The "(Curse and Enchant Unknown)" note is dropped: no room.)
        from hud_context import item_bare_name
        w_name = (item_bare_name(self.player, weapon).split(' (')[0]
                  if weapon else "Bare Hands")
        put(w_name, s['weapon'], FP.FADED_TEXT, align='right',
            sizes=(self._COMBAT_HUD_CAP_SIZE,))
        if cur_chain >= 1 or cur_dmg > 0:
            put(f"{cur_dmg} Damage", s['main'], live_col,
                sizes=(32, 26, 22), family='heading')
            put(f"x{cur_mult:.1f} Multiplier", s['sub1'], FP.BODY_TEXT)
        else:
            put("0 Damage", s['main'], FP.FADED_TEXT, sizes=(32,), family='heading')
            put("Answer to start a chain", s['sub1'], FP.FADED_TEXT)

        # Damage-type / weakness tag keeps its signal colour.
        type_str = " / ".join(_label(d) for d in dtypes)
        if dm > 1.0:
            dm_text, dm_col = f"Weakness: {type_str}", FP.SUCCESS_TEXT
        elif dm < 1.0:
            dm_text, dm_col = f"Resisted: {type_str}", FP.DANGER_TEXT
        else:
            dm_text, dm_col = type_str, FP.FADED_TEXT
        put(dm_text, s['sub2'], dm_col)

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
        self.screen.blit(font.render(display_text(str(text)), True, color), (rect.x, rect.y))
        self.screen.set_clip(old_clip)
        return font.get_height() + S(2)

    def _menu_draw_wrapped(self, text: str, font, color, rect: pygame.Rect,
                           max_lines: int | None = None) -> int:
        y = rect.y
        drawn = 0
        chunks = display_text(str(text)).splitlines() or ['']
        for chunk in chunks:
            lines = self._wrap_text(chunk, font, rect.w) or ['']
            for line in lines:
                if max_lines is not None and drawn >= max_lines:
                    return y - rect.y
                if y + font.get_height() > rect.bottom:
                    return y - rect.y
                self._menu_draw_line(line, font, color,
                                     pygame.Rect(rect.x, y, rect.w, font.get_height() + S(2)))
                y += font.get_height() + S(3)
                drawn += 1
        return y - rect.y

    def _menu_draw_text_block(self, lines: list, rect: pygame.Rect,
                              default_color=None, default_font=None) -> int:
        """Draw a detail pane's lines. When they do not all fit, the last
        paragraph that would overflow ends on its last WHOLE sentence and a
        dim cue line says where the rest is (``self._menu_more_cue``, set by
        the caller for this frame) -- the shop's lore used to stop
        mid-sentence with no cue (VISUAL_REVIEW, shop)."""
        color = default_color or FP.BODY_TEXT
        font = default_font or self.font_sm
        cue = getattr(self, '_menu_more_cue', None)
        self._menu_more_cue = None
        lines = self._menu_fit_block(lines, rect, color, font, cue)
        y = rect.y
        for entry in lines:
            if entry is None or entry == '':
                y += S(8)
                continue
            if isinstance(entry, tuple) and entry and entry[0] == '__key__':
                y = self._menu_draw_key_line(entry[1], entry[2], rect, y, font)
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
            y += used + S(4)
        return y

    def _menu_draw_key_line(self, key, label, rect, y, font) -> int:
        """A detail-pane action line: a key badge, then its label (wrapped
        beside the badge). Returns the next y."""
        kf = get_font('body', 16, bold=True)
        kw = max(S(28), kf.size(key)[0] + S(14))
        lines = self._wrap_text(display_text(label), font, rect.w - kw - S(10)) or ['']
        lh = font.get_height() + S(3)
        if y + lh > rect.bottom:
            return y
        draw_key_badge(self.screen, (rect.x, y + (lh - S(26)) // 2, kw, S(26)), key, kf)
        for ln in lines:
            if y + lh > rect.bottom:
                break
            self.screen.blit(font.render(ln, True, readable(FP.BODY_TEXT, KT.RAISED)),
                             (rect.x + kw + S(10), y))
            y += lh
        return y + S(6)

    def _menu_block_height(self, lines, width, color, font) -> int:
        h = 0
        for entry in lines:
            if entry is None or entry == '':
                h += S(8)
                continue
            if isinstance(entry, tuple) and entry and entry[0] == '__key__':
                h += font.get_height() + S(9)
                continue
            text, fnt = (entry[0], entry[2] if len(entry) > 2 and entry[2] is not None else font) \
                if isinstance(entry, tuple) else (entry, font)
            n = sum(len(self._wrap_text(c, fnt, width) or ['']) for c in
                    display_text(str(text)).splitlines() or [''])
            h += n * (fnt.get_height() + S(3)) + S(4)
        return h

    def _menu_fit_block(self, lines, rect, color, font, cue):
        """``lines`` as they fit in ``rect``: unchanged when they fit; else
        cut to whole sentences (and whole lines), plus a cue line."""
        import re
        if self._menu_block_height(lines, rect.w, color, font) <= rect.h:
            return lines
        cue_line = (cue or "More in the item's dossier.", FP.HINT_TEXT, get_font('body', 16))
        out = []
        for entry in lines:
            trial = out + [entry, cue_line]
            if self._menu_block_height(trial, rect.w, color, font) <= rect.h:
                out.append(entry)
                continue
            if (isinstance(entry, tuple) and entry and isinstance(entry[0], str)
                    and entry[0] != '__key__'):
                sentences = re.split(r'(?<=[.!?])\s+', display_text(entry[0]))
                kept = []
                for sent in sentences:
                    cand = tuple([' '.join(kept + [sent])] + list(entry[1:]))
                    if self._menu_block_height(out + [cand, cue_line], rect.w, color, font) > rect.h:
                        break
                    kept.append(sent)
                if kept:
                    out.append(tuple([' '.join(kept)] + list(entry[1:])))
            break
        return out + [cue_line]

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
        _cwt, _clim, _cstate = carry_state(p)
        weight = carry_numbers(p) + (f"  ({_cstate})" if _cstate else "")
        effects = getattr(p, 'status_effects', {}) or {}
        active = [k.replace('_', ' ').title() for k, v in effects.items() if v != 0]
        lines = [
            ("CURRENT RUN", FP.GOLD_BRIGHT, self.font_sm),
            (f"{floor_label(self.dungeon_level)}    Turn {self.turn_count}", FP.BODY_TEXT, self.font_sm),
            (f"Tile: {self._menu_tile_label()}", FP.FADED_TEXT, self.font_sm),
            (f"Carrying {weight}", FP.WARNING_TEXT if _cstate else FP.BODY_TEXT, self.font_sm),
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
        """Blessed / Uncursed / Cursed once THIS copy's blessing is known,
        else "Unknown". Type knowledge never reveals it (True Name model:
        each copy's blessing waits for its own identify), so the check reads
        the copy's own stored id_level, not the type-boosted menu level
        (that leaked "Uncursed" on a "(Curse Unknown)" potion in the shop)."""
        if not hasattr(item, 'buc'):
            return '-'
        if self._copy_buc_known(item):
            return _cap(getattr(item, 'buc', 'uncursed'))
        return 'Unknown'

    def _copy_buc_known(self, item) -> bool:
        """True when this copy's blessing or curse is known to the player:
        flagged known (altar, identify), the copy identified (id_level 5),
        or worn (a curse shows itself on equip). A stored 1-4 is not enough:
        ``item.identified = True`` writes 4 without identifying anything."""
        try:
            own = int(getattr(item, 'id_level', 5) or 0)
        except (TypeError, ValueError):
            own = 0
        return (own >= 5 or bool(getattr(item, 'buc_known', False))
                or self._menu_item_is_equipped(item))

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
            return "Choose how much to drop"
        idl = self._menu_item_level(item)
        if hasattr(item, 'identified') and idl < 3:
            cls = getattr(item, 'item_class', 'item').replace('_', ' ').title()
            return f"{cls} | Unidentified"
        try:
            return self._get_item_stats_brief(item)
        except Exception:
            return getattr(item, 'item_class', 'item').replace('_', ' ').title()

    def _menu_item_detail_lines(self, item, action: str = 'Select') -> list:
        # Phase 1 beautification (2026-10-03): the kit inspector was dropping
        # five cosmetic rows per item that duplicated the name / section
        # header / footer hint. We now trim to: name -> key stats / effects
        # -> one meaningful cue (equipped star, hidden-until-ID note, lore).
        # The Dossier Lore screen (``_lore_item_mechanic_lines`` and the
        # lore_item_card renderer) keeps its expanded view.
        if isinstance(item, self._GoldDropEntry):
            return [
                ("Gold", FP.GOLD_BRIGHT, self.font_md),
                (f"You have {getattr(self, 'player_gold', 0):,} coins.", FP.BODY_TEXT, self.font_sm),
            ]

        idl = self._menu_item_level(item)
        display = self._display_name(item)
        lines = [(display, FP.GOLD_BRIGHT, self.font_md)]

        # One-line equipped marker is useful at a glance (per Phase 1 brief).
        if self._menu_item_is_equipped(item):
            lines.append(("Equipped", FP.SUCCESS_TEXT, self.font_sm))

        if hasattr(item, 'identified') and idl < 3:
            # ``_display_name`` already shows either "<name> (Curse Unknown)" or
            # the pure appearance string, so a dedicated Appearance row is
            # redundant. Likewise ``Type: {cls}`` repeats the section header
            # icon, and ``Next action`` repeats the footer hint. We keep the
            # Weight line (real mechanical info) and ONE "hidden until ID"
            # cue so the player knows mechanics aren't missing — just gated.
            lines += [
                (f"Weight: {getattr(item, 'weight', 0):.1f}", FP.FADED_TEXT, self.font_sm),
                ("Stats, blessing or curse, and lore stay hidden until identified.",
                 FP.WARNING_TEXT, self.font_sm),
            ]
            return lines

        lines += [
            ("Known properties", FP.GOLD_BRIGHT, self.font_sm),
            (self._menu_item_summary(item), FP.BODY_TEXT, self.font_sm),
            # Label and value bound by no-break spaces, so a narrow pane wraps
            # between the two facts, never inside one ("Weight: / 0.4").
            (f"Blessing: {self._menu_buc_label(item, idl)}    "
             f"Weight: {getattr(item, 'weight', 0):.1f}",
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
                (f"{get_chain_subject(item).title()} {_quiz_mode_phrase(get_chain_mode(item))}, fresh quiz on each equip",
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
                    effect_bits.append(f"Grants {_cap(fx['status'])}")
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
                      ("Identify this item to read its lore.", FP.FADED_TEXT, self.font_sm)]

        # ``Next action`` row removed — the panel footer hint ("Enter: Select"
        # etc.) covers controls, so a duplicate row inside the detail pane
        # was pure chrome.
        return lines

    def _menu_recipe_preview(self, recipe) -> str:
        """One-line outcome preview for a recipe (post-v2.6.4 cook redesign).

        Recipe carries `outcome_id` referencing data/items/cook_outcomes.json.
        Legacy recipes with a `tier_outcomes` dict still render (dead in-repo
        but old saves may keep them).
        """
        # v2.6.4 path: single outcome archetype via outcome_id
        oid = recipe.get('outcome_id')
        if oid:
            try:
                from food_system import _load_outcomes
                o = _load_outcomes().get(oid) or {}
            except Exception:
                o = {}
            if o:
                bits = []
                if o.get('sp'):            bits.append(f"+{o['sp']}SP")
                if o.get('hp'):            bits.append(f"+{o['hp']}HP")
                if o.get('max_hp_bonus'):  bits.append(f"+{o['max_hp_bonus']}maxHP")
                # A trophy grants its stat outright. Any other meal is banked
                # toward the stat of its meat (two meals, on two floors, make
                # a point): say which stat, and promise no number.
                if o.get('permanent_power') and o.get('stat_grant'):
                    stat = o.get('stat_grant_default') or recipe.get('stat_grant_default') or '?'
                    bits.append(f"+{o['stat_grant']}{stat}")
                else:
                    try:
                        from food_system import recipe_cut_stat
                        fed = recipe_cut_stat(recipe) or (
                            o.get('stat_grant_default') if o.get('stat_grant') else None)
                    except Exception:
                        fed = None
                    if fed:
                        bits.append(f"Feeds {fed}")
                if o.get('temp_power'):
                    tp = _temp_power_label(o.get('temp_power'))
                    dur = o.get('temp_duration')
                    bits.append(f"{tp} {dur}t" if tp and dur else tp or 'temp buff')
                if o.get('permanent_power'):
                    bits.append('PERM')
                tier = o.get('tier', '?')
                return f"T{tier}: {'/'.join(bits)}" if bits else f"T{tier}"
        # Legacy fallback (pre-v2.6.4 recipes with tier_outcomes dict)
        outcomes = recipe.get('tier_outcomes', {}) or {}
        parts = []
        for t in range(1, 6):
            o = outcomes.get(str(t), {}) or {}
            bits = []
            if o.get('sp'):            bits.append(f"+{o['sp']}SP")
            if o.get('hp'):            bits.append(f"+{o['hp']}HP")
            if o.get('max_hp_bonus'):  bits.append(f"+{o['max_hp_bonus']}maxHP")
            if o.get('stat_grant'):
                stat = recipe.get('stat_grant') or recipe.get('stat_grant_default') or '?'
                bits.append(f"+{o['stat_grant']}{stat}")
            if o.get('temp_power'):
                label = _temp_power_label(recipe.get('temp_power'))
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
            # v2.15.0 UI-rot fix: cooking is one-question binary (v2.6.4),
            # no escalator chain. Label the section as the outcome, not "chain".
            lines += [("Outcome", FP.GOLD_BRIGHT, self.font_sm),
                      (preview, FP.SUCCESS_TEXT, self.font_sm)]
        lines += [("Next action", FP.GOLD_BRIGHT, self.font_sm),
                  ("Answer one cooking question. Right = full recipe; wrong = ruined dish.", FP.BODY_TEXT, self.font_sm)]
        return lines

    def _draw_action_tabs(self, tabs, active_tab: int, counts, x: int, y: int, w: int) -> int:
        """Draw an action-menu tab strip. Phase 2 beautification (2026-10-04):
        when the full strip is wider than the container, scroll the visible
        window so the active tab is kept inside it. Arrow glyphs
        (``◀`` / ``▶``) at the edges flag hidden tabs. Keeps the tab-strip
        legible on narrow panels (cook / eat / equip menus) and in menus
        with many tabs."""
        if not tabs:
            return y
        if kit_on('chip'):
            return self._draw_action_tabs_kit(tabs, active_tab, counts, x, y, w)
        from text_layout import tab_strip_window
        tab_font = get_font('small', 14)
        gap = S(6)
        ARROW_W = S(18)
        TAB_H = S(25)

        # Pre-measure every tab's full width so the window helper can pick
        # a stable visible slice.
        widths = []
        labels = []
        for i, tab in enumerate(tabs):
            count = counts[i] if counts and i < len(counts) else None
            label = tab[0]
            text = f"{label} ({count})" if count is not None else label
            labels.append(text)
            widths.append(tab_font.size(text)[0] + S(22))

        win = tab_strip_window(widths, active_tab, w, gap=gap, arrow_w=ARROW_W)
        overflow = win['overflow']
        start = win['start']
        end = win['end']

        tx = x
        max_x = x + w
        if win['show_left_arrow']:
            arrow_rect = pygame.Rect(tx, y, ARROW_W, TAB_H)
            pygame.draw.rect(self.screen, FP.MIDNIGHT, arrow_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, arrow_rect, 1, border_radius=4)
            a_surf = tab_font.render('◀', True, FP.GOLD_BRIGHT)
            self.screen.blit(a_surf, (arrow_rect.centerx - a_surf.get_width() // 2,
                                      arrow_rect.centery - a_surf.get_height() // 2))
            tx += ARROW_W + gap

        reserved_right = ARROW_W + gap if win['show_right_arrow'] else 0
        for i in range(start, end):
            tw = widths[i]
            if tx + tw > max_x - reserved_right:
                break
            rect = pygame.Rect(tx, y, tw, TAB_H)
            active = i == active_tab
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                             rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD if active else FP.GOLD_DARK,
                             rect, 1, border_radius=4)
            col = FP.GOLD_BRIGHT if active else FP.FADED_TEXT
            self._menu_draw_line(labels[i], tab_font, col,
                                 pygame.Rect(rect.x + S(8), rect.y + S(4), rect.w - 2 * S(8), rect.h))
            tx += tw + gap

        if win['show_right_arrow']:
            arrow_rect = pygame.Rect(max_x - ARROW_W, y, ARROW_W, TAB_H)
            pygame.draw.rect(self.screen, FP.MIDNIGHT, arrow_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, arrow_rect, 1, border_radius=4)
            a_surf = tab_font.render('▶', True, FP.GOLD_BRIGHT)
            self.screen.blit(a_surf, (arrow_rect.centerx - a_surf.get_width() // 2,
                                      arrow_rect.centery - a_surf.get_height() // 2))

        _ = overflow  # unused but documented via win['overflow']
        return y + S(32)

    def _draw_action_tabs_kit(self, tabs, active_tab, counts, x, y, w) -> int:
        """The tab strip in the kit: ``chip`` / ``chip_active`` pieces,
        scrolled so the active tab is always visible (``tab_strip_window``)."""
        from text_layout import tab_strip_window
        f_on = get_font('body', 16, bold=True)
        gap = S(8)
        ARROW_W = S(24)
        TAB_H = S(30)
        labels, widths = [], []
        for i, tab in enumerate(tabs):
            count = counts[i] if counts and i < len(counts) else None
            text = f"{tab[0]} ({count})" if count is not None else tab[0]
            labels.append(text)
            widths.append(f_on.size(text)[0] + S(26))
        win = tab_strip_window(widths, active_tab, w, gap=gap, arrow_w=ARROW_W)
        arrow_f = get_font('symbol', 14)

        def arrow(rect, glyph):
            ui_theme.draw_piece(self.screen, 'chip', rect)
            a = arrow_f.render(glyph, True, KT.TEXT_HEAD)
            self.screen.blit(a, (rect.centerx - a.get_width() // 2,
                                 rect.centery - a.get_height() // 2))

        tx, max_x = x, x + w
        if win['show_left_arrow']:
            arrow(pygame.Rect(tx, y, ARROW_W, TAB_H), '\u25c0')
            tx += ARROW_W + gap
        reserved_right = ARROW_W + gap if win['show_right_arrow'] else 0
        for i in range(win['start'], win['end']):
            tw = widths[i]
            if tx + tw > max_x - reserved_right:
                break
            self._ui_chip(pygame.Rect(tx, y, tw, TAB_H), labels[i],
                          active=(i == active_tab), color=FP.GOLD)
            tx += tw + gap
        if win['show_right_arrow']:
            arrow(pygame.Rect(max_x - ARROW_W, y, ARROW_W, TAB_H), '\u25b6')
        return y + TAB_H + S(12)

    def _menu_name_sizes(self, entries, text_w):
        """(sizes, name_lines) for a list's rows: ONE name size for every row
        (the largest of 20 / 18 / 16 px at which every name fits), so rows
        never mix sizes; names that do not fit even at 16 px wrap onto a
        second line (name_lines 2) instead of being cut."""
        names = [display_text(str(e.get('name', ''))) for e in entries]
        for size in (20, 18, 16):
            f = get_font('body', size)
            if all(f.size(n)[0] <= text_w for n in names):
                return (size,), 1
        return (16,), 2

    def _menu_row_text_w(self, row_w, entries):
        """Width left for a row's name and detail (see ``_menu_row_kit``)."""
        if any(e.get('key') for e in entries):
            w = row_w - S(9) - S(30) - S(10)
        else:
            w = row_w - S(10)            # no key badges (the shop): no badge slot
        if any(e.get('icon') for e in entries):
            w -= self.MENU_ICON_SIZE + S(18)
        bf = get_font('body', 16, bold=True)
        badges = [bf.size(str(e.get('badge')))[0] + S(28) for e in entries if e.get('badge')]
        if badges:
            w -= max(badges) + S(10)
        return w - S(12)

    def _menu_row_kit(self, rect, entry, *, selected, name_font, detail_font,
                      key_font, two_line=True, detail_lines=1, name_sizes=(20, 18, 16),
                      name_lines=1):
        """One option row of a menu in the kit: row art, key badge, the
        item's art on a dark well, name + detail, and a tag chip. The
        detail wraps onto up to ``detail_lines`` lines (word by word, never
        cut mid-word); the caller sizes the row for them."""
        self._ui_row(rect, selected)
        bg = KT.SELECTED if selected else KT.RAISED
        key = entry.get('key', '')
        ks = S(30)
        key_rect = pygame.Rect(rect.x + S(9), rect.centery - ks // 2, ks, ks)
        if key:
            draw_key_badge(self.screen, key_rect, key, key_font,
                           color=entry.get('key_color'))
            tx = key_rect.right + S(10)
        else:
            tx = rect.x + S(10)          # no key (the shop): no empty badge slot
        icon = entry.get('icon')
        if icon:
            isz = self.MENU_ICON_SIZE
            well = pygame.Rect(tx, rect.centery - isz // 2 - S(4), isz + S(8), isz + S(8))
            self._ui_well(well)
            self._draw_menu_icon(icon, well.x + S(4), well.y + S(4))
            tx = well.right + S(10)
        badge = entry.get('badge', '')
        badge_w = 0
        if badge:
            bf = get_font('body', 16, bold=True)
            label = str(badge)
            badge_w = bf.size(label)[0] + S(18)
            brect = pygame.Rect(rect.right - badge_w - S(10), rect.centery - S(13),
                                badge_w, S(26))
            ui_theme.draw_piece(self.screen, 'chip', brect)
            col = readable(entry.get('badge_color', FP.FADED_TEXT), KT.RAISED)
            bs = bf.render(label, True, col)
            self.screen.blit(bs, (brect.centerx - bs.get_width() // 2,
                                  brect.centery - bs.get_height() // 2))
            badge_w += S(10)
        text_w = rect.right - tx - badge_w - S(12)
        name_col = readable(entry.get('name_color', FP.BODY_TEXT), bg)
        # One name size for the whole list (the caller's ``name_sizes``); a
        # name that still does not fit wraps onto ``name_lines`` lines.
        name_text = display_text(str(entry.get('name', '')))
        name_font, _fitted = self._fit_line(name_text, text_w, name_sizes)
        nlines = [_fitted]
        if name_font.size(name_text)[0] > text_w and name_lines > 1:
            nlines = (self._wrap_text(name_text, name_font, text_w) or [''])[:name_lines]
        detail = display_text(str(entry.get('detail', '') or ''))
        if two_line and detail:
            dlines = self._wrap_text(detail, detail_font, text_w) or ['']
            if len(dlines) > detail_lines:
                dlines = dlines[:detail_lines]
                dlines[-1] = fit_text(dlines[-1] + ' \u2026', detail_font, text_w)
            nh, dh = name_font.get_height(), detail_font.get_height() + S(1)
            ty = rect.centery - (nh * len(nlines) + S(3) + dh * len(dlines)) // 2
            for nl in nlines:
                self._menu_draw_line(nl, name_font, name_col,
                                     pygame.Rect(tx, ty, text_w, nh + S(2)))
                ty += nh
            ty -= nh
            dcol = readable(entry.get('detail_color', FP.FADED_TEXT), bg)
            for i, dl in enumerate(dlines):
                self._menu_draw_line(dl, detail_font, dcol,
                                     pygame.Rect(tx, ty + nh + S(3) + i * dh, text_w, dh + S(1)))
        else:
            nh = name_font.get_height()
            ty = rect.centery - nh * len(nlines) // 2
            for nl in nlines:
                self._menu_draw_line(nl, name_font, name_col,
                                     pygame.Rect(tx, ty, text_w, nh + S(2)))
                ty += nh

    def _draw_decision_menu_kit(self, *, title, entries, selected, hint, border,
                                tabs, active_tab, tab_counts, scroll_attr):
        """``_draw_decision_menu`` in the Midnight Codex kit."""
        draw_overlay(self.screen, 190)
        bw = min(S(1240), _modal_budget_w() - S(32))
        bh = min(S(720), layout.WINDOW_H - S(32))
        panel = pygame.Rect(_centre_x(bw), _centre_y(bh), bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        body_top = self._ui_header(panel, title, border_color=border)
        b = panel_band('panel', panel)
        side = b + S(14)
        content_x = panel.x + side
        content_w = panel.w - 2 * side
        content_y = self._draw_action_tabs(tabs, active_tab, tab_counts,
                                           content_x, body_top, content_w)
        _div, _keys, body_bottom = self._ui_footer_metrics(panel)
        body_h = body_bottom - content_y

        gap = S(12)
        list_w = max(S(500), min(S(700), int(content_w * 0.58)))
        detail_w = content_w - list_w - gap
        if detail_w < S(390):
            detail_w = max(S(340), int(content_w * 0.44))
            list_w = content_w - detail_w - gap
        list_rect = pygame.Rect(content_x, content_y, list_w, body_h)
        detail_rect = pygame.Rect(list_rect.right + gap, content_y, detail_w, body_h)
        list_body = self._ui_subpanel(list_rect, "Choices", border_color=border)
        detail_body = self._ui_subpanel(detail_rect, "Detail", border_color=border)
        list_body = pygame.Rect(list_rect.x + S(8), list_body.y - S(4),
                                list_rect.w - 2 * S(8), list_rect.bottom - list_body.y - S(4))

        total = len(entries)
        selected = max(0, min(selected, max(0, total - 1)))
        if scroll_attr:
            setattr(self, scroll_attr, selected)
        name_sizes, name_lines = self._menu_name_sizes(
            entries, self._menu_row_text_w(list_body.w, entries))
        row_h = S(62) + (get_font('body', 16).get_height() if name_lines > 1 else 0)
        tag_h = S(24) if total * row_h > list_body.h else 0
        visible = max(1, (list_body.h - tag_h) // row_h)
        scroll = 0
        if total > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, total - visible)))
        name_font, detail_font = self.font_sm, get_font('body', 16)
        key_font = get_font('body', 18, bold=True)
        for row_i, entry in enumerate(entries[scroll:scroll + visible], start=scroll):
            ry = list_body.y + (row_i - scroll) * row_h
            self._menu_row_kit(pygame.Rect(list_body.x, ry, list_body.w, row_h - S(6)),
                               entry, selected=(row_i == selected),
                               name_font=name_font, detail_font=detail_font,
                               key_font=key_font, name_sizes=name_sizes,
                               name_lines=name_lines)
        if total > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, total)} of {total}"
            ts = get_font('body', 16).render(tag, True, KT.TEXT_DIM)
            self.screen.blit(ts, (list_rect.right - ts.get_width() - S(12),
                                  list_rect.bottom - ts.get_height() - S(6)))

        detail_body = pygame.Rect(detail_body.x + S(2), detail_body.y,
                                  detail_body.w - S(4), detail_body.h)
        if entries:
            detail_lines = entries[selected].get('details') or []
            self._menu_draw_text_block(detail_lines, detail_body, default_font=self.font_sm)
        else:
            self._menu_draw_text_block(
                [("Nothing available.", FP.FADED_TEXT, self.font_sm)],
                detail_body, default_font=self.font_sm)
        self._ui_footer(panel, hint)

    def _draw_fast_picker_kit(self, *, title, entries, selected, hint, border,
                              subtitle, tabs, active_tab, tab_counts):
        """``_draw_fast_picker`` in the Midnight Codex kit.

        Centred on the window over the same full dim as every other menu
        (VISUAL_REVIEW minor 2: anchored to the bottom over a light dim, a
        half log line peeked under it and the log beside it stayed bright).
        Each row shows its whole detail line, wrapped onto a second line
        when it is long (the Fireball row was cut to "5d6 fire damag"). The
        note above the rows appears only for what the rows do NOT say (an
        entry's ``full_detail`` beyond its ``detail``); it is plain text, not
        a boxed card, so it never looks like a choice (VISUAL_REVIEW_2).

        The panel height is laid out top-down from the SAME numbers the draw
        uses (header, the subtitle's own line when it cannot sit beside the
        title, tabs, note, rows), and the footer is added below the rows with
        the divider ornament's full reach plus the ``md`` step (12 px) clear
        of the last row. It used to be a sum that missed the subtitle's own
        line, so on quaff and pet specials the divider ornament sat on the
        last row (VISUAL_REVIEW_2 must-fix 1). A single-column picker is
        capped at 760 px (scaled) so a short name does not sit ~1000 px from
        its tag."""
        draw_overlay(self.screen, 190)
        bw = min(S(1180), layout.WINDOW_W - S(48))
        cols = 2 if bw >= S(900) and len(entries) > 3 else 1
        if cols == 1:
            bw = min(bw, S(760))
        max_rows_visible = 4 if cols == 2 else 6
        needed_rows = (max(1, len(entries)) + cols - 1) // cols
        rows_visible = max(1, min(max_rows_visible, needed_rows))
        selected = max(0, min(selected, max(0, len(entries) - 1)))
        b = panel_band('panel', pygame.Rect(0, 0, bw, S(400)))
        side = b + S(14)
        col_gap = S(12)
        col_w = (bw - 2 * side - col_gap * (cols - 1)) // cols
        name_font, detail_font = self.font_sm, get_font('body', 16)
        key_font = get_font('body', 18, bold=True)
        text_w = self._menu_row_text_w(col_w, entries)
        detail_lines = 1
        for e in entries:
            d = display_text(str(e.get('detail', '') or ''))
            if d:
                detail_lines = max(detail_lines,
                                   min(3, len(self._wrap_text(d, detail_font, text_w))))
        name_sizes, name_lines = self._menu_name_sizes(entries, text_w)
        row_gap = S(6)
        row_h = max(S(54), get_font('body', name_sizes[0]).get_height() * name_lines + S(3)
                    + detail_lines * (detail_font.get_height() + S(1)) + S(16))

        # The note: only what the rows do not already say.
        def _extra(x):
            full = str(x.get('full_detail') or '')
            det = str(x.get('detail') or '')
            if not full or full == det:
                return ''
            return full[len(det):].strip() if full.startswith(det) else full
        note_text = _extra(entries[selected]) if entries else ''
        note_font = get_font('body', 16)
        note_w = bw - 2 * side - 2 * S(12)
        note_line_h = note_font.get_height() + S(3)
        note_h = 0
        if note_text:
            n_lines = max([min(3, len(self._wrap_text(display_text(_extra(x)), note_font, note_w)))
                           for x in entries if _extra(x)] or [1])
            note_h = max(1, n_lines) * note_line_h

        # Header: the title plaque, and the subtitle beside it or on its own line.
        head_h = S(44)
        hf = get_font('heading', 24, bold=True)
        title_w = hf.size(display_title(title))[0]
        sub_s = None
        sub_beside = False
        if subtitle:
            sub_s = get_font('body', 16).render(subtitle, True, KT.TEXT_DIM)
            sub_beside = (bw - 2 * b) // 2 - title_w // 2 > sub_s.get_width() + S(58)
        tabs_h = S(42) if tabs else 0       # what ``_draw_action_tabs_kit`` advances

        top_to_rows = b + head_h + S(12) - S(2)
        if sub_s is not None and not sub_beside:
            top_to_rows += sub_s.get_height()
        top_to_rows += tabs_h
        if note_h:
            top_to_rows += note_h + S(10)
        reach = divider_reach()
        kh = key_hints_height()
        # Last row's bottom edge -> panel bottom: the md gap, the divider's
        # reach above its line, then exactly what ``_ui_footer_metrics`` puts
        # under the line (16 + key row + 8 + frame band).
        below_rows = S(12) + reach + S(16) + kh + S(8) + b
        max_h = layout.WINDOW_H - S(40)
        while True:
            bh = top_to_rows + rows_visible * row_h - row_gap + below_rows
            if bh <= max_h or rows_visible <= 1:
                break
            rows_visible -= 1
        visible = max(1, rows_visible * cols)
        if len(entries) > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, len(entries) - visible)))
        else:
            scroll = 0

        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        y = self._ui_header(panel, title, border_color=border, h=44, font=hf,
                            right_reserve=0)
        hr = header_rect(panel, head_h)
        if sub_s is not None:
            if sub_beside:
                # At the plaque's right end, clear of its scroll-roll.
                self.screen.blit(sub_s, (hr.right - S(48) - sub_s.get_width(),
                                         hr.y + (hr.h - S(4) - sub_s.get_height()) // 2))
            else:
                # No room beside the title: a line of its own under the plaque.
                self.screen.blit(sub_s, (panel.centerx - sub_s.get_width() // 2, y - S(4)))
                y += sub_s.get_height()
        y -= S(2)
        if tabs:
            y = self._draw_action_tabs(tabs, active_tab, tab_counts, bx + side, y,
                                       bw - 2 * side)
        if note_text:
            # Plain dim text on the interior, centred: information, not a choice.
            col = readable(KT.TEXT_DIM, KT.INTERIOR)
            ly = y + S(2)
            for ln in self._wrap_text(display_text(note_text), note_font, note_w)[:3]:
                ls = note_font.render(ln, True, col)
                self.screen.blit(ls, (panel.centerx - ls.get_width() // 2, ly))
                ly += note_line_h
            y += note_h + S(10)

        div_y, keys, _body_bottom = self._ui_footer_metrics(panel)
        for vi, entry in enumerate(entries[scroll:scroll + visible]):
            absolute = scroll + vi
            col, row = vi // rows_visible, vi % rows_visible
            rect = pygame.Rect(bx + side + col * (col_w + col_gap), y + row * row_h,
                               col_w, row_h - row_gap)
            self._menu_row_kit(rect, entry, selected=(absolute == selected),
                               name_font=name_font, detail_font=detail_font,
                               key_font=key_font, detail_lines=detail_lines,
                               name_sizes=name_sizes, name_lines=name_lines)

        draw_divider(self.screen, bx + b + S(28), div_y, bw - 2 * (b + S(28)))
        tag_w = 0
        if len(entries) > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, len(entries))} of {len(entries)}"
            ts = get_font('body', 16).render(tag, True, KT.TEXT_DIM)
            self.screen.blit(ts, (keys.x, keys.centery - ts.get_height() // 2))
            tag_w = ts.get_width() + S(16)
        draw_key_hints(self.screen, keys.inflate(-2 * tag_w, 0), hint)

    def _draw_decision_menu(self, *, title: str, entries: list,
                                      selected: int, context_lines: list,
                                      hint: str, border_color=None, tabs=None,
                                      active_tab: int = 0, tab_counts=None,
                                      scroll_attr: str | None = None):
        """Large decision menu (list on the left, detail pane on the right).

        Kept under the original helper name so existing menu call sites stay
        stable. The layout is now a wide choices list plus an inspector pane;
        standing run context stays in the HUD instead of consuming menu width.
        """
        border = border_color or FP.GOLD
        if kit_on():
            return self._draw_decision_menu_kit(
                title=title, entries=entries, selected=selected, hint=hint,
                border=border, tabs=tabs, active_tab=active_tab,
                tab_counts=tab_counts, scroll_attr=scroll_attr)
        draw_overlay(self.screen, 190)
        # Caps grow with the UI scale; the width budget is the play area
        # left of the right rail; the panel centres on the window.
        bw = min(S(1240), _modal_budget_w() - S(32))
        bh = min(S(720), layout.WINDOW_H - S(32))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, S(44)), text=title,
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT,
                        frame=((bx, by, bw, bh), border))

        content_x = bx + S(16)
        content_y = by + S(56)
        content_w = bw - 2 * S(16)
        content_y = self._draw_action_tabs(tabs, active_tab, tab_counts,
                                           content_x, content_y, content_w)
        footer_h = S(32)
        body_h = by + bh - footer_h - content_y - S(10)

        gap = S(12)
        list_w = max(S(500), min(S(700), int(content_w * 0.58)))
        detail_w = content_w - list_w - gap
        if detail_w < S(390):
            detail_w = max(S(340), int(content_w * 0.44))
            list_w = content_w - detail_w - gap

        list_rect = pygame.Rect(content_x, content_y, list_w, body_h)
        detail_rect = pygame.Rect(list_rect.right + gap, content_y, detail_w, body_h)

        for rect, label in ((list_rect, "CHOICES"), (detail_rect, "DETAIL")):
            pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=6)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=6)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID,
                             (rect.x + 1, rect.y + 1, rect.w - 2, S(30)),
                             border_radius=6)
            head = get_font('small', 14).render(label, True, FP.GOLD_BRIGHT)
            self.screen.blit(head, (rect.centerx - head.get_width() // 2, rect.y + S(8)))

        total = len(entries)
        selected = max(0, min(selected, max(0, total - 1)))
        if scroll_attr:
            setattr(self, scroll_attr, selected)
        row_h = S(64)
        list_body = pygame.Rect(list_rect.x + S(10), list_rect.y + S(42),
                                list_rect.w - 2 * S(10), list_rect.h - S(54))
        visible = max(1, list_body.h // row_h)
        scroll = 0
        if total > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, total - visible)))
        for row_i, entry in enumerate(entries[scroll:scroll + visible], start=scroll):
            ry = list_body.y + (row_i - scroll) * row_h
            row_rect = pygame.Rect(list_body.x, ry, list_body.w, row_h - S(6))
            is_sel = row_i == selected
            pygame.draw.rect(self.screen, (34, 43, 84) if is_sel else
                             (18, 22, 40) if row_i % 2 == 0 else (12, 15, 28),
                             row_rect, border_radius=6)
            pygame.draw.rect(self.screen, border if is_sel else FP.GOLD_DARK,
                             row_rect, 1, border_radius=6)
            key = entry.get('key', '')
            key_rect = pygame.Rect(row_rect.x + S(8), row_rect.y + S(9), S(32), S(32))
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect, border_radius=4)
            pygame.draw.rect(self.screen, FP.GOLD if key else FP.GOLD_DARK,
                             key_rect, 1, border_radius=4)
            if key:
                ks = self.font_sm.render(key, True, FP.GOLD_BRIGHT)
                self.screen.blit(ks, (key_rect.centerx - ks.get_width() // 2,
                                      key_rect.centery - ks.get_height() // 2))
            icon = entry.get('icon')
            tx = key_rect.right + S(8)
            if icon:
                self._draw_menu_icon(icon, tx, row_rect.y + S(9))
                tx += self.MENU_ICON_SIZE + S(8)
            badge = entry.get('badge', '')
            badge_w = 0
            if badge:
                bs = self.font_sm.render(str(badge), True, entry.get('badge_color', FP.FADED_TEXT))
                badge_w = bs.get_width() + S(18)
                brect = pygame.Rect(row_rect.right - badge_w - S(8), row_rect.y + S(14),
                                    badge_w, S(26))
                pygame.draw.rect(self.screen, FP.MIDNIGHT, brect, border_radius=4)
                pygame.draw.rect(self.screen, entry.get('badge_color', border),
                                 brect, 1, border_radius=4)
                self.screen.blit(bs, (brect.centerx - bs.get_width() // 2,
                                      brect.centery - bs.get_height() // 2))
            text_w = row_rect.right - tx - badge_w - S(16)
            self._menu_draw_line(entry.get('name', ''), self.font_sm,
                                 entry.get('name_color', FP.BODY_TEXT),
                                 pygame.Rect(tx, row_rect.y + S(8), text_w, S(22)))
            detail = entry.get('detail', '')
            if detail:
                self._menu_draw_line(detail, get_font('small', 14),
                                     entry.get('detail_color', FP.FADED_TEXT),
                                     pygame.Rect(tx, row_rect.y + S(34), text_w, S(20)))

        if total > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, total)} of {total}"
            ts = get_font('small', 14).render(tag, True, FP.FADED_TEXT)
            self.screen.blit(ts, (list_rect.right - ts.get_width() - S(12),
                                  list_rect.bottom - S(22)))

        detail_body = pygame.Rect(detail_rect.x + S(14), detail_rect.y + S(42),
                                  detail_rect.w - 2 * S(14), detail_rect.h - S(58))
        if entries:
            detail_lines = entries[selected].get('details') or []
            self._menu_draw_text_block(detail_lines, detail_body, default_font=self.font_sm)
        else:
            self._menu_draw_text_block(
                [("Nothing available.", FP.FADED_TEXT, self.font_sm)],
                detail_body, default_font=self.font_sm)

        draw_divider(self.screen, bx + S(16), by + bh - footer_h - S(4), bw - 2 * S(16))
        hs = self.font_sm.render(hint, True, FP.HINT_TEXT)
        self.screen.blit(hs, (bx + (bw - hs.get_width()) // 2, by + bh - footer_h + S(4)))

    def _draw_fast_picker(self, *, title: str, entries: list,
                                    selected: int, hint: str, border_color=None,
                                    subtitle: str = '', tabs=None,
                                    active_tab: int = 0, tab_counts=None):
        border = border_color or FP.ARCANE_BRIGHT
        if kit_on():
            return self._draw_fast_picker_kit(
                title=title, entries=entries, selected=selected, hint=hint,
                border=border, subtitle=subtitle, tabs=tabs,
                active_tab=active_tab, tab_counts=tab_counts)
        draw_overlay(self.screen, 95)
        bw = min(S(1180), _modal_budget_w() - S(80))
        cols = 2 if bw >= S(900) and len(entries) > 3 else 1
        max_rows_visible = 4 if cols == 2 else 6
        needed_rows = (max(1, len(entries)) + cols - 1) // cols
        rows_visible = max(1, min(max_rows_visible, needed_rows))
        visible = max(1, rows_visible * cols)
        selected = max(0, min(selected, max(0, len(entries) - 1)))
        selected_note = ''
        if entries:
            selected_note = str(entries[selected].get('full_detail')
                                or entries[selected].get('detail') or '')
        selected_note_h = S(58) if selected_note else 0
        if len(entries) > visible:
            scroll = max(0, min(selected - visible + 1 if selected >= visible else 0,
                                max(0, len(entries) - visible)))
        else:
            scroll = 0
        header_h = S(42) + (S(30) if tabs else 0)
        row_h = S(52)
        footer_h = S(28)
        bh = header_h + selected_note_h + rows_visible * row_h + footer_h + S(26)
        # Bottom-anchored by design (a quick picker over a lightly dimmed
        # map), centred horizontally on the window (SCALE_PLAN.md 3).
        bx = _centre_x(bw)
        by = layout.WINDOW_H - bh - S(30)
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=border)
        draw_header_bar(self.screen, (bx, by, bw, S(40)), text=title,
                        font=self.font_md, text_color=FP.GOLD_BRIGHT,
                        accent=border, frame=((bx, by, bw, bh), border))
        if subtitle:
            ss = get_font('small', 14).render(subtitle, True, FP.FADED_TEXT)
            title_w = self.font_md.size(title)[0]
            title_right = bx + (bw + title_w) // 2
            subtitle_x = bx + bw - ss.get_width() - S(16)
            if subtitle_x > title_right + S(24):
                self.screen.blit(ss, (subtitle_x, by + S(12)))
        y = by + S(48)
        if tabs:
            y = self._draw_action_tabs(tabs, active_tab, tab_counts, bx + S(14), y,
                                       bw - 2 * S(14))
        if selected_note:
            note_rect = pygame.Rect(bx + S(16), y, bw - 2 * S(16), selected_note_h - S(8))
            pygame.draw.rect(self.screen, FP.MIDNIGHT, note_rect, border_radius=5)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, note_rect, 1, border_radius=5)
            self._menu_draw_wrapped(
                selected_note,
                get_font('small', 14),
                entries[selected].get('detail_color', FP.BODY_TEXT),
                pygame.Rect(note_rect.x + S(10), note_rect.y + S(7),
                            note_rect.w - 2 * S(10), note_rect.h - S(12)),
                max_lines=3,
            )
            y += selected_note_h

        body = pygame.Rect(bx + S(16), y, bw - 2 * S(16), rows_visible * row_h)
        col_gap = S(12)
        col_w = (body.w - col_gap * (cols - 1)) // cols
        visible_entries = entries[scroll:scroll + visible]
        for vi, entry in enumerate(visible_entries):
            absolute = scroll + vi
            col = vi // rows_visible
            row = vi % rows_visible
            rx = body.x + col * (col_w + col_gap)
            ry = body.y + row * row_h
            rect = pygame.Rect(rx, ry, col_w, row_h - S(6))
            is_sel = absolute == selected
            pygame.draw.rect(self.screen, (40, 44, 82) if is_sel else FP.MIDNIGHT,
                             rect, border_radius=5)
            pygame.draw.rect(self.screen, border if is_sel else FP.GOLD_DARK,
                             rect, 1, border_radius=5)
            key = entry.get('key', '')
            key_rect = pygame.Rect(rect.x + S(8), rect.y + S(10), S(30), S(30))
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
                badge_w = bs.get_width() + S(18)
                brect = pygame.Rect(rect.right - badge_w - S(8), rect.y + S(13),
                                    badge_w, S(24))
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, brect, border_radius=4)
                pygame.draw.rect(self.screen, entry.get('badge_color', border),
                                 brect, 1, border_radius=4)
                self.screen.blit(bs, (brect.centerx - bs.get_width() // 2,
                                      brect.centery - bs.get_height() // 2))
            tx = key_rect.right + S(8)
            icon = entry.get('icon')
            if icon:
                self._draw_menu_icon(icon, tx, rect.y + S(9))
                tx += self.MENU_ICON_SIZE + S(8)
            text_w = rect.right - tx - badge_w - S(14)
            self._menu_draw_line(entry.get('name', ''), self.font_sm,
                                 entry.get('name_color', FP.BODY_TEXT),
                                 pygame.Rect(tx, rect.y + S(7), text_w, S(22)))
            self._menu_draw_line(entry.get('detail', ''), get_font('small', 14),
                                 entry.get('detail_color', FP.FADED_TEXT),
                                 pygame.Rect(tx, rect.y + S(30), text_w, S(18)))

        draw_divider(self.screen, bx + S(16), by + bh - footer_h - S(6), bw - 2 * S(16))
        if len(entries) > visible:
            tag = f"{scroll + 1}-{min(scroll + visible, len(entries))} of {len(entries)}"
            ts = get_font('small', 14).render(tag, True, FP.FADED_TEXT)
            self.screen.blit(ts, (bx + S(20), by + bh - footer_h + S(3)))
        from fantasy_ui import fit_text
        hf = get_font('small', 14)
        hs = hf.render(fit_text(hint, hf, bw - 2 * S(24)), True, FP.HINT_TEXT)
        self.screen.blit(hs, (bx + (bw - hs.get_width()) // 2, by + bh - footer_h + S(3)))

    def _draw_equip_menu(self):
        tab_items = self._get_equip_tab_items()
        is_unequip = tab_items is None
        display_items = self.equip_menu_equipped if is_unequip else tab_items

        entries = []
        if is_unequip:
            for i, (slot_name, item) in enumerate(display_items):
                # A curse is marked only once known (the name says so too).
                cursed = (getattr(item, 'cursed', False)
                          and getattr(item, 'buc_known', False))
                slot_label = slot_name.replace('_', ' ').title()
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
                # Stats and material only once known (the same rule as the
                # Kit): they showed an unidentified blade's true damage.
                _known = self._kit_visible_level(item) >= 3
                if isinstance(item, Weapon):
                    detail = (f"{_cap(getattr(item, 'weapon_class', 'weapon'))}  {item.base_damage} Damage"
                              if _known else "Weapon  Unidentified")
                elif isinstance(item, Shield):
                    detail = (f"+{item.ac_bonus} AC  {_cap(item.material)}"
                              if _known else "Shield  Unidentified")
                elif isinstance(item, Armor):
                    _slot = _cap(str(getattr(item, 'slot', 'armor')).replace('_', ' '))
                    detail = (f"{_slot}  +{item.ac_bonus} AC  {_cap(item.material)}"
                              if _known else f"{_slot}  Unidentified")
                elif isinstance(item, Accessory):
                    if self._item_is_known(item):
                        fx = item.effects
                        if 'status' in fx:
                            detail = f"Grants {_cap(fx['status'])}"
                        elif 'stat' in fx:
                            detail = f"{fx['stat']} +{fx.get('amount', 0)}"
                        elif getattr(item, 'slot', '') == 'none':
                            detail = "Passive (carry-only)"
                        else:
                            detail = "Accessory"
                    else:
                        detail = "Unidentified"
                else:
                    detail = _cap(str(item.item_class).replace('_', ' '))
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
        self._draw_decision_menu(
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

    # Long stat names for the kit table's labelled rows ('' = the value
    # speaks for itself: "Iron", "Uncursed", "Body").
    _KIT_STAT_NAMES = {'Dmg': 'Damage', 'Avg': 'Average', 'Wt': 'Weight',
                       'AC': 'AC', 'Material': '', 'BUC': '', 'Slot': '', 'Type': ''}
    _KIT_BUC_WORDS = {'bless.': 'Blessed', 'unc.': 'Uncursed', 'CURSED': 'Cursed'}

    def _kit_row_labelled(self, slug: str, src: str, item):
        """(stats, (label, text)) for one kit-table row: every stat with its
        name, and the special / resists / effect column as a labelled line."""
        cols = self._kit_column_defs(slug)
        cells = self._kit_cells_for_item(slug, src, item)
        labels = [c.label for c in cols]
        idl = self._kit_visible_level(item)
        stats = []
        for label, value in zip(labels[2:-1], cells[2:-1]):
            value = str(value)
            if value in ('', 'None'):
                continue
            if label == 'BUC':
                if value in ('?', '-'):
                    continue
                value = self._KIT_BUC_WORDS.get(value, value.title())
            elif label == 'Material':
                if value == '?':
                    continue
                value = _cap(value)
            elif value == '?':
                continue
            name = self._KIT_STAT_NAMES.get(label, label)
            stats.append(f"{name} {value}" if name else value)
        if idl < 3:
            stats.insert(0, "Not identified: stats hidden")
        extra_label = labels[-1] if labels else ''
        extra = str(cells[-1]) if cells else ''
        if extra in ('?', '-', ''):
            extra = ''
        return stats, (extra_label, extra)

    def _kit_source_label(self, src: str) -> str:
        return {'equip': 'Equipped', 'pack': 'Pack', 'floor': 'Floor'}.get(src, src)

    def _kit_detail_lines_for_item(self, slug: str, src: str, item):
        idl = self._kit_visible_level(item)
        lines = [
            (self._display_name(item), FP.GOLD_PALE, get_font('heading', 22)),
            (f"Source: {self._kit_source_label(src)}", FP.FADED_TEXT, self.font_sm),
            (f"Identity: {_identify_status_label(idl)}", FP.CYAN_ACCENT, self.font_sm),
        ]
        delta = self._equip_delta_str(item)
        if delta:
            color = FP.SUCCESS_TEXT if '+' in delta else FP.WARNING_TEXT
            lines.append((delta, color, self.font_sm))
        if idl >= 3:
            stats, (extra_label, extra) = self._kit_row_labelled(slug, src, item)
            lines.append(("Visible stats", FP.GOLD_BRIGHT, self.font_sm))
            for st in stats:
                lines.append((st, FP.BODY_TEXT, self.font_sm))
            if extra:
                lines.append((f"{extra_label}: {extra}", FP.BODY_TEXT, self.font_sm))
        else:
            lines.append(("Stats remain hidden until you identify it.",
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
                (lore, FP.LORE_BLUE_BODY, self.font_sm),     # one size in the pane
            ]
        return lines

    def _kit_detail_lines_for_spell(self, spell):
        return [
            (spell.get('name', spell.get('spell_id', '?')),
             FP.GOLD_PALE, get_font('heading', 22)),
            (f"Tier: {spell.get('quiz_tier', '?')}   MP: {spell.get('mp_cost', '?')}",
             FP.CYAN_ACCENT, self.font_sm),
            ("Description", FP.GOLD_BRIGHT, self.font_sm),
            (spell.get('desc', ''), FP.BODY_TEXT, self.font_sm),
        ]

    def _draw_kit_detail_lines(self, rect, lines):
        render_lines = []
        for i, (text, color, fnt) in enumerate(lines):
            if i and color == FP.GOLD_BRIGHT:
                render_lines.append(("", color, fnt))      # a gap BEFORE a section
            for line in self._ui_text_lines(text, fnt, rect.w - S(14)):
                render_lines.append((line, color, fnt))
            if i == 0:
                render_lines.append(("", color, fnt))
        self._ui_draw_scroll_lines(render_lines, self.font_sm, FP.BODY_TEXT,
                                   rect, 0, line_gap=5)

    # -- Item actions (shared by the Kit and the character sheet) ----------

    def _item_action_hints(self, actions):
        """Footer key hints for the ENABLED item actions: [(key, label)]."""
        return [(a['key'], a['label']) for a in actions if a.get('enabled', True)]

    def _draw_item_action_strip(self, x, y, w, actions, bg):
        """The selected item's actions as key badges ("[E] Equip   [D] Drop"),
        wrapped to ``w``; a blocked action is greyed with its reason on a
        line below. Returns the y under what was drawn."""
        if not actions:
            return y
        kf = get_font('body', 16, bold=True)
        lf = get_font('body', 16)
        key_h = max(kf.get_height() + S(8), S(26))
        pad, inner, gap = S(7), S(8), S(18)
        on_col = readable(KT.TEXT_BODY if kit_on() else FP.BODY_TEXT, bg)
        off_col = readable(FP.FADED_TEXT, bg)
        cx = x
        for a in actions:
            kw = kf.size(a['key'])[0] + 2 * pad
            unit = kw + inner + lf.size(a['label'])[0]
            if cx > x and cx + unit > x + w:
                cx = x
                y += key_h + S(6)
            enabled = a.get('enabled', True)
            draw_key_badge(self.screen, (cx, y, kw, key_h), a['key'], kf,
                           color=None if enabled else off_col)
            ls = lf.render(a['label'], True, on_col if enabled else off_col)
            self.screen.blit(ls, (cx + kw + inner, y + (key_h - ls.get_height()) // 2))
            cx += unit + gap
        y += key_h + S(6)
        return self._draw_item_action_reasons(x, y, w, actions, bg)

    def _draw_item_action_reasons(self, x, y, w, actions, bg):
        """One faded line per blocked action: "Unequip: Cursed, it will not
        come off". Returns the y under them."""
        lf = get_font('body', 16)
        off_col = readable(FP.FADED_TEXT, bg)
        # One line per reason ("Unequip, Drop: Cursed, it will not come off").
        reasons: dict = {}
        for a in actions:
            if not a.get('enabled', True) and a.get('why'):
                reasons.setdefault(a['why'], []).append(a['label'])
        for why, labels in reasons.items():
            for ln in self._wrap_text(f"{', '.join(labels)}: {why}", lf, w):
                self.screen.blit(lf.render(ln, True, off_col), (x, y))
                y += lf.get_height() + S(2)
        return y + S(4)

    def _draw_item_feedback(self, x, y, w, bottom, bg):
        """What the last Kit / sheet action said (the quiz result included),
        under a "Result" label. Returns the y under it."""
        lines = self._item_feedback_lines() if hasattr(self, '_item_feedback_lines') else []
        if not lines:
            return y
        hf = get_font('body', 16, bold=True)
        lf = get_font('body', 16)
        lh = lf.get_height() + S(2)
        if y + hf.get_height() + lh > bottom:
            return y
        self.screen.blit(hf.render("Result", True, readable(FP.GOLD_BRIGHT, bg)), (x, y))
        y += hf.get_height() + S(4)
        wrapped = []
        for text, kind in lines:
            col = readable(KT.LOG.get(kind, KT.LOG['info']), bg)
            for ln in self._wrap_text(display_text(str(text)), lf, w):
                wrapped.append((ln, col))
        room = max(1, (bottom - y) // lh)
        for ln, col in wrapped[-room:]:
            self.screen.blit(lf.render(ln, True, col), (x, y))
            y += lh
        return y + S(6)

    def _draw_kit_browser(self):
        active = getattr(self, '_kit_tab', 0)
        slug = self._KIT_TABS[active][1]
        panel = self._ui_modal_panel("KIT COMPARISON",
                                     border_color=FP.GOLD,
                                     max_w=1444,
                                     max_h=766)
        body = self._ui_modal_body(panel)
        tab_y = body.y
        x = body.x
        # Each tab is as wide as its label needs (bold, as when active), at
        # least the old 128 / 154 px while the row has room: a fixed width
        # cut "Accessories" to "Accesso..." in a compact window.
        tab_f = get_font('body', 16, bold=True)
        needs = [tab_f.size(lab)[0] + S(16) for lab, _s in self._KIT_TABS]
        wants = [max(n, S(154) if lab == 'Consumables' else S(128))
                 for n, (lab, _s) in zip(needs, self._KIT_TABS)]
        room = body.w - S(8) * (len(wants) - 1)
        widths = wants if sum(wants) <= room else needs
        for idx, (label, _slug) in enumerate(self._KIT_TABS):
            width = widths[idx]
            rect = pygame.Rect(x, tab_y, width, S(28))
            self._ui_chip(rect, label, active=(idx == active), color=FP.GOLD)
            x += width + S(8)

        content_y = tab_y + S(42)
        content_h = body.bottom - content_y
        gutter = S(14)
        detail_w = min(S(450), max(S(360), int(body.w * 0.34)))
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
            self._draw_item_feedback(detail_body.x, detail_body.y, detail_body.w,
                                     detail_body.bottom, KT.RAISED if kit_on() else FP.MIDNIGHT)
            self._ui_footer(panel, "Left/Right: tab   ESC: close")
            return

        sel = max(0, min(getattr(self, '_kit_sel', 0), total - 1))
        self._kit_sel = sel
        # Each row is a small labelled card (VISUAL_REVIEW must-fix 9: the
        # stats were an unlabelled "3 / 3.0 / iron / unc." in 13 px text):
        #   line 1  the name, and where it is (Equipped / Pack / Floor);
        #   line 2  the stats, each with its name ("Damage 3   Average 3.0");
        #   line 3+ the special / resists / effect, labelled, wrapped.
        # The cards read at the detail pane's size (they were 18 / 16 px
        # beside its 20 px at 3440), with leading between the lines (three
        # lines were packed at a 17 px pitch at 1280; VISUAL_REVIEW_2).
        name_f = get_font('body', 20, bold=True)
        stat_f = get_font('body', 18)
        tag_f = get_font('body', 18, bold=True)
        lead = S(4)
        inner_w = table_body.w - S(12) - 2 * S(12)
        cards = []
        for row in rows:
            if slug == 'spells':
                name = row.get('name', '?')
                tag = f"{row.get('mp_cost', '?')} MP"
                stats = [f"Tier {row.get('quiz_tier', '-')}"]
                extra = ('', row.get('desc', ''))
                tag_col = FP.CYAN_ACCENT
                name_col = FP.BODY_TEXT
            else:
                src, item = row
                name = self._display_name(item)
                tag = self._kit_source_label(src)
                stats, extra = self._kit_row_labelled(slug, src, item)
                tag_col = self._KIT_SRC_COLOR.get(src, FP.BODY_TEXT)
                name_col = tag_col
            tag_w = tag_f.size(tag)[0] + S(16)
            name_lines = self._wrap_text(name, name_f, inner_w - tag_w - S(10)) or ['']
            stat_lines = self._wrap_text("   ".join(stats), stat_f, inner_w) if stats else []
            label, text = extra
            extra_lines = []
            if text:
                extra_lines = self._wrap_text(f"{label}: {text}" if label else text,
                                              stat_f, inner_w)[:3]
            h = (S(10) + len(name_lines) * (name_f.get_height() + lead)
                 + (len(stat_lines) + len(extra_lines)) * (stat_f.get_height() + lead)
                 - lead + S(10))
            cards.append((name_lines, name_col, tag, tag_col, stat_lines, extra_lines, h))

        scroll = getattr(self, '_kit_scroll', 0)
        scroll = max(0, min(scroll, sel))
        avail = table_body.h

        def fits(first, last):
            return sum(cards[i][6] + S(6) for i in range(first, last + 1)) <= avail

        while not fits(scroll, sel) and scroll < sel:
            scroll += 1
        self._kit_scroll = scroll
        y = table_body.y
        visible = 0
        for idx in range(scroll, total):
            name_lines, name_col, tag, tag_col, stat_lines, extra_lines, h = cards[idx]
            if y + h > table_body.bottom and visible:
                break
            visible += 1
            selected = idx == sel
            rect = pygame.Rect(table_body.x, y, table_body.w - S(12), h)
            self._ui_row(rect, selected,
                         fill=(35, 43, 82) if selected else FP.MIDNIGHT,
                         border=FP.GOLD if selected else FP.ARCANE_DIM, radius=6)
            bg = KT.SELECTED if selected else KT.RAISED
            tx, ty = rect.x + S(12), rect.y + S(10)
            ts = tag_f.render(tag, True, readable(tag_col, bg))
            self.screen.blit(ts, (rect.right - S(12) - ts.get_width(), ty + S(1)))
            for ln in name_lines:
                self.screen.blit(name_f.render(ln, True, readable(
                    FP.GOLD_BRIGHT if selected else name_col, bg)), (tx, ty))
                ty += name_f.get_height() + lead
            for ln in stat_lines:
                self.screen.blit(stat_f.render(ln, True, readable(FP.BODY_TEXT, bg)), (tx, ty))
                ty += stat_f.get_height() + lead
            for ln in extra_lines:
                self.screen.blit(stat_f.render(ln, True, readable(FP.FADED_TEXT, bg)), (tx, ty))
                ty += stat_f.get_height() + lead
            y += h + S(6)

        if total > visible:
            self._ui_scrollbar(table_body, scroll, total, max(1, visible))

        hints = [("Left/Right", "Tab"), ("Up/Down", "Select")]
        if slug == 'spells':
            detail_lines = self._kit_detail_lines_for_spell(rows[sel])
        else:
            src, item = rows[sel]
            detail_lines = self._kit_detail_lines_for_item(slug, src, item)
            # The selected item's actions on top of the card (the keys shared
            # with the character sheet), then what the last action said.
            bg = KT.RAISED if kit_on() else FP.MIDNIGHT
            actions = self._item_actions(item, src)
            y = self._draw_item_action_strip(detail_body.x, detail_body.y,
                                             detail_body.w, actions, bg)
            y = self._draw_item_feedback(detail_body.x, y, detail_body.w,
                                         detail_body.bottom, bg)
            if y > detail_body.y:
                # The divider's centre ornament rises ~12 px above its line.
                draw_divider(self.screen, detail_body.x, y + S(14), detail_body.w)
                y += S(30)
                detail_body = pygame.Rect(detail_body.x, y, detail_body.w,
                                          max(0, detail_body.bottom - y))
            hints += self._item_action_hints(actions)
        self._draw_kit_detail_lines(detail_body, detail_lines)
        self._ui_footer(panel, "   ".join(f"{k}: {lab}" for k, lab in hints + [("ESC", "Close")]))

    def _draw_kit_panel(self):
        self._draw_kit_browser()

    # --------------------------------------------------------------
    # Shared content-measured table helper
    # --------------------------------------------------------------
    # Every column-table render in this file goes through here. The
    # contract: fixed columns (flex=0) get sized to their actual content
    # (max of header width + widest cell width + gutter); flex columns
    # absorb leftover space by weight. Truncation is a backstop only.
    # See proposals/v2_audit/IDENTIFY_SYSTEM.md §11 + the kit-menu fix
    # commit 2026-05-28.

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
        # One decimal, like the sheet (food read "Weight 0" truncated).
        wt = f"{float(getattr(item, 'weight', 0) or 0):.1f}"
        # The material is part of what identifying tells you: an unknown
        # "plain longsword" showed "Iron" in this column.
        mat = (getattr(item, 'material', '') or '') if idl >= 3 else '?'

        # Blessing visibility: this copy's own knowledge, never the type's.
        if self._copy_buc_known(item):
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
            slot_lbl = (getattr(item, 'slot', '') or '').replace('_', ' ').title()
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
            slot_lbl = (getattr(item, 'slot', '') or '').replace('_', ' ').title()
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
        # Which sums it asks: the one fact that decides whether a stronger
        # weapon is actually better in this player's hands.
        _tier = int(getattr(w, 'quiz_tier', 0) or 0)
        if _tier:
            bits.append(f"Tier {_tier} Sums")
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
                bits.append(' / '.join(_cap(d) for d in dt))     # "Pierce / Slash"
            if getattr(w, 'two_handed', False):
                bits.append('Two-Handed')
            # The weapon's own on-hit effects (it read ``unique_effect``,
            # a field no weapon has, so this never showed anything).
            for attr, label in (('stun_chance', 'Stun'), ('bleed_chance', 'Bleed'),
                                ('poison_chance', 'Poison'), ('burn_chance', 'Burn'),
                                ('confuse_chance', 'Confuse'),
                                ('lifesteal_percent', 'Lifesteal')):
                try:
                    v = float(getattr(w, attr, 0) or 0)
                except (TypeError, ValueError):
                    v = 0.0
                if v > 0:
                    pct = v * 100 if v <= 1 else v
                    bits.append(f"{label} {pct:.0f}%")
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
            parts.append(f"Grants {_cap(fx['status'])}")
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

    # ------------------------------------------------------------------
    # Discoveries panel  (J key)
    # ------------------------------------------------------------------

    def _draw_discoveries_panel(self):
        """Player-growth record. Pure tally of what's been done. No spoilers.

        Rows are tables, not space-padded strings: a row is a ``label\tvalue``
        string (cells split on tabs) drawn as aligned columns, a
        ``('head', ...)`` tuple is a table header, '' a gap. The section rail
        shows each section's first figure in full, wrapping when it is long
        (it used to be clipped: "Total answered: 9 (4")."""
        panel = self._ui_modal_panel("DISCOVERIES - YOUR RECORD",
                                     border_color=FP.GOLD,
                                     max_w=1320,
                                     max_h=720)
        body = self._ui_modal_body(panel)
        sections = self._discoveries_sections()
        if not sections:
            self._ui_wrap_text("No discoveries recorded yet.", self.font_md,
                               FP.FADED_TEXT, body)
            self._ui_footer(panel, "ESC: close")
            return

        gutter = S(14)
        rail_w = min(S(300), max(S(245), int(body.w * 0.26)))
        rail_rect = pygame.Rect(body.x, body.y, rail_w, body.h)
        detail_rect = pygame.Rect(rail_rect.right + gutter, body.y,
                                  body.w - rail_w - gutter, body.h)
        rail_body = self._ui_subpanel(rail_rect, "Record Sections")
        detail_body = self._ui_subpanel(detail_rect, "Run Record")

        sel = max(0, min(getattr(self, '_disc_sel', 0), len(sections) - 1))
        self._disc_sel = sel
        head_f = get_font('body', 17, bold=True)
        sub_f = get_font('body', 16)
        row_w = rail_body.w - S(10)
        summaries = []
        for _header, rows in sections:
            first = next((r for r in rows if isinstance(r, str) and r.strip()), "")
            cells = [c.strip() for c in first.split('\t') if c.strip()]
            if len(cells) > 1:
                cells[1] = cells[1].split(' (')[0]      # the figure, not its breakdown
            summaries.append(' '.join(cells[:2]))
        sub_lines = [self._wrap_text(t, sub_f, row_w - S(20)) or [''] for t in summaries]
        n_sub = max(1, min(2, max(len(x) for x in sub_lines)))
        row_h = S(14) + head_f.get_height() + n_sub * (sub_f.get_height() + S(1)) + S(10)
        visible = max(1, rail_body.h // row_h)
        scroll = max(0, min(sel, max(0, len(sections) - visible)))
        if sel >= scroll + visible:
            scroll = sel - visible + 1

        y = rail_body.y
        for idx, (header, rows) in enumerate(sections[scroll:scroll + visible],
                                             start=scroll):
            rect = pygame.Rect(rail_body.x, y, row_w, row_h - S(7))
            selected = idx == sel
            self._ui_row(rect, selected,
                         fill=(35, 43, 82) if selected else FP.MIDNIGHT,
                         border=FP.GOLD if selected else FP.GOLD_DARK, radius=6)
            bg = KT.SELECTED if selected else KT.RAISED
            self._ui_blit_text(header.title(), head_f,
                               readable(FP.GOLD_BRIGHT if selected else FP.BODY_TEXT, bg),
                               rect.x + S(10), rect.y + S(6), max_width=rect.w - S(20))
            ly = rect.y + S(8) + head_f.get_height()
            for line in sub_lines[idx][:n_sub]:
                self._ui_blit_text(line, sub_f, readable(FP.FADED_TEXT, bg),
                                   rect.x + S(10), ly)
                ly += sub_f.get_height() + S(1)
            y += row_h

        header, rows = sections[sel]
        flat = self._disc_table_lines(header, rows, detail_body.w - S(14))
        self._disc_scroll = self._ui_draw_scroll_lines(
            flat, self.font_sm, FP.BODY_TEXT, detail_body,
            getattr(self, '_disc_scroll', 0), line_gap=5)
        self._ui_footer(panel, "Up/Down: section   PgUp/PgDn: scroll record   ESC: close")

    def _disc_table_lines(self, header, rows, width):
        """The detail pane's lines for one Discoveries section: tab-separated
        rows set as aligned table columns (each run of table rows shares its
        column widths); the last column wraps if the row is too wide."""
        f = self.font_sm
        hf = get_font('body', 18, bold=True)
        out = [(header.title(), FP.GOLD_PALE, get_font('heading', 24)),
               ("", FP.BODY_TEXT, f)]
        groups, cur = [], []
        for r in rows:
            is_head = isinstance(r, tuple)
            text = r[1] if is_head else str(r)
            if '\t' in text:
                cur.append((is_head, [c.strip() for c in text.split('\t')]))
                continue
            if cur:
                groups.append(('table', cur))
                cur = []
            groups.append(('text', text.strip()))
        if cur:
            groups.append(('table', cur))
        gap = S(18)
        for kind, g in groups:
            if kind == 'text':
                if not g:
                    out.append(("", FP.BODY_TEXT, f))
                else:
                    for line in self._ui_text_lines(g, f, width):
                        out.append((line, FP.BODY_TEXT, f))
                continue
            n = max(len(c) for _h, c in g)
            widths = [0] * n
            for is_head, cells in g:
                fnt = hf if is_head else f
                for k, c in enumerate(cells[:-1] if len(cells) == n else cells):
                    widths[k] = max(widths[k], fnt.size(c)[0])
            for is_head, cells in g:
                fnt = hf if is_head else f
                col = FP.GOLD_BRIGHT if is_head else FP.BODY_TEXT
                out.append(('__cells__', cells, widths, gap, fnt, col, width))
        return out

    def _discoveries_sections(self):
        """Return list of (section_title, [row_string, ...]) tuples.

        Reads only data the game is actually tracking; pulls from the player
        for per-run sets (known_*, masteries, quirks) and from Game-level
        counters (correct_answers, missed_questions) for journey state. Karma
        is deliberately not shown.
        """
        p = self.player
        sections = []

        # --- Quiz performance: totals + per-subject breakdown ---
        right_total = int(getattr(self, 'correct_answers', 0) or 0)
        wrong_total = int(getattr(self, 'wrong_answers', 0) or 0)
        total = right_total + wrong_total
        acc = (right_total / total * 100) if total else 0.0
        quiz_rows = [
            f"Total answered:\t{total} ({right_total} right, {wrong_total} wrong, {acc:.0f}%)",
        ]
        # Per-subject + per-tier breakdown if tracking is active
        qstats = getattr(self, 'quiz_stats', {}) or {}
        # Per-run tier-clear: a cleared (subject, tier) auto-succeeds, so mark
        # it CLEARED here instead of a hit ratio -- the badge the player
        # earns for clearing a whole tier.
        quiz_engine = getattr(self, 'quiz_engine', None)
        mastered = quiz_engine.mastered_tiers() if quiz_engine else set()
        if qstats:
            quiz_rows.append("")
            quiz_rows.append(('head', "Subject\tRight\tWrong\tScore\tBy tier"))
            for subj in sorted(qstats.keys()):
                d = qstats[subj] or {}
                r = int(d.get('correct', 0))
                w = int(d.get('wrong', 0))
                t = r + w
                a = (r / t * 100) if t else 0.0
                tier_bits = []
                for ti in range(1, 6):
                    if (subj, ti) in mastered:
                        tier_bits.append(f"Tier {ti} cleared")
                        continue
                    tr = int(d.get(f't{ti}c', 0))
                    tw = int(d.get(f't{ti}w', 0))
                    if tr + tw > 0:
                        tier_bits.append(f"Tier {ti}: {tr}/{tr+tw}")
                name = 'AI' if subj == 'ai' else proper_name(str(subj).replace('_', ' '))
                quiz_rows.append(f"{name}\t{r}\t{w}\t{a:.0f}%\t{', '.join(tier_bits) or '-'}")
        sections.append(("QUIZ PERFORMANCE", quiz_rows))

        # --- Identification ---
        known_ids = getattr(p, 'known_item_ids', set()) or set()
        total_ids = int(getattr(p, 'total_identifies', 0) or 0)
        mantle = bool(getattr(p, 'philosophers_mantle', False))
        id_rows = [
            f"Identified:\t{total_ids}",
            f"Item types learned:\t{len(known_ids)}",
        ]
        if mantle:
            id_rows.append("Mantle of the Philosopher:\tgranted")
        sections.append(("IDENTIFICATION", id_rows))

        # --- Bestiary ---
        seen = getattr(p, 'known_monster_ids', set()) or set()
        studied = getattr(p, 'lore_known_monster_ids', set()) or set()
        sections.append(("BESTIARY", [
            f"Monsters seen:\t{len(seen)}",
            f"Monsters studied:\t{len(studied)}",
        ]))

        # --- Faith --- (no karma number: how the soul stands is a discovery,
        # hinted at in Recall Lore; only the Judgment card shows it. Brandon,
        # DEEDS_KARMA_DESIGN decision 1.)
        boons = int(getattr(p, 'prayer_boon_count', 0) or 0)
        sections.append(("FAITH", [
            f"Prayer boons:\t{boons}",
        ]))

        # --- Spells & magic ---
        spells = getattr(p, 'known_spells', {}) or {}
        hack_count = int(getattr(p, 'hack_reality_count', 0) or 0)
        magic_rows = [
            f"Spells learned:\t{len(spells)}",
        ]
        if hack_count > 0:
            magic_rows.append(f"Reality hacks claimed:\t{hack_count}")
        sections.append(("MAGIC", magic_rows))

        # --- Journey ---
        deepest = int(getattr(p, 'deepest_floor_reached',
                              getattr(self, 'dungeon_level', 1)) or 1)
        current = int(getattr(self, 'dungeon_level', 1) or 1)
        sections.append(("JOURNEY", [
            f"Current floor:\t{current}",
            f"Deepest floor:\t{deepest}",
        ]))

        # --- Quirks (counts only — names of unlocked quirks could spoil) ---
        unlocked = getattr(p, 'unlocked_quirks', set()) or set()
        sections.append(("QUIRKS", [
            f"Quirks unlocked:\t{len(unlocked)}",
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
            charge_text = f"Charges: {item.charges}/{item.max_charges}"
            if self._item_is_known(item):
                charge_text += f" | Effect: {item.effect.replace('_', ' ').title()}"
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
        self._draw_fast_picker(
            title="ZAP WAND",
            entries=entries,
            selected=selected,
            subtitle="Nearest visible monster: auto-targeted",
            hint="Up/Down: move   Enter or a-z: zap   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
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
                'detail': f"Tier {tier} | {mp_cost} MP | {spell.get('desc', '')}",
                'full_detail': (f"Tier {tier} | {mp_cost} MP | {spell.get('desc', '')}   "
                                "(Effects last longer and reach further with Intelligence.)"),
                'key': self._menu_letter(i),
                'icon': _SpellIcon(spellbook_id, tier_color),
                'name_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
                'detail_color': tier_color,
                'badge': f"{mp_cost} MP",
                'badge_color': FP.BODY_TEXT if can_cast else FP.DANGER_TEXT_LIGHT,
            })
        selected = self._menu_clamp_selection('_spell_sel', len(entries))
        self._draw_fast_picker(
            title="CAST SPELL",
            entries=entries,
            selected=selected,
            subtitle=f"MP: {self.player.mp}/{self.player.max_mp}",
            hint="Up/Down: move   Enter or a-z: cast   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
        )

    def _draw_boon_menu(self):
        """A gate boss's three gifts: name, what it gives, one line each."""
        import boons
        from fantasy_ui import get_font
        kind = getattr(self, '_boon_kind', None)
        offer = boons.offer_for(kind) if kind else None
        if not offer:
            return
        draw_overlay(self.screen, 210)

        font_title = get_font('heading', 24)
        font_name  = get_font('body', 20, bold=True)
        font_body  = get_font('body', 15)
        font_hint  = get_font('body', 16)
        gifts = offer.get('gifts') or []
        quest_line = offer.get('quest_line') if boons.solved_quest(self.player, kind) else ''
        if kit_on():
            _kit_option_card(
                self.screen, str(offer.get('title', 'Three Gifts')),
                [{'key': str(i + 1),
                  'name': f"{g['name']}   ({boons.describe(self.player, kind, g)})",
                  'text': g.get('text', '')} for i, g in enumerate(gifts)],
                "1-3: take one gift   //   The other two are lost for good",
                border=FP.GOLD, overlay=0, min_w=780, note=quest_line or '',
                note_color=FP.GOLD)
            return

        # Wide enough for its widest line (see _draw_prayer_menu).
        need = max([font_name.size(f"{i + 1}.  {g['name']}   "
                                   f"({boons.describe(self.player, kind, g)})")[0] + S(40)
                    for i, g in enumerate(gifts)]
                   + [font_body.size(g.get('text', ''))[0] + S(72) for g in gifts]
                   + [font_body.size(quest_line)[0] + S(72) if quest_line else 0])
        bw = min(max(S(780), need + S(36)), layout.WINDOW_W - S(48))
        row_h = font_name.get_height() + font_body.get_height() + S(18)
        bh = S(96) + row_h * len(gifts) + (font_body.get_height() + S(14) if quest_line else 0) + S(44)
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        pygame.draw.rect(self.screen, (16, 12, 6), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, FP.GOLD, (bx, by, bw, bh), 3, border_radius=8)
        pygame.draw.rect(self.screen, (110, 82, 20),
                         (bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=6)

        title = font_title.render(str(offer.get('title', 'Three Gifts')).upper(),
                                  True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + S(22)))
        pygame.draw.line(self.screen, FP.GOLD,
                         (bx + S(32), by + S(60)), (bx + bw - S(32), by + S(60)), 1)

        y = by + S(78)
        for i, gift in enumerate(gifts):
            head = f"{i + 1}.  {gift['name']}   ({boons.describe(self.player, kind, gift)})"
            self.screen.blit(font_name.render(head, True, FP.GOLD_BRIGHT), (bx + S(40), y))
            y += font_name.get_height() + S(2)
            self.screen.blit(font_body.render(gift.get('text', ''), True, FP.BODY_TEXT),
                             (bx + S(72), y))
            y += font_body.get_height() + S(16)
        if quest_line:
            line = font_body.render(quest_line, True, FP.GOLD)
            self.screen.blit(line, (bx + (bw - line.get_width()) // 2, y))

        hint = font_hint.render(
            "Press 1, 2 or 3 to take one  //  the other two are lost for good",
            True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - S(28)))

    def _draw_prayer_menu(self):
        """Which prayer? One numbered line each, with what it asks for."""
        from fantasy_ui import get_font
        draw_overlay(self.screen, 200)

        choices = self._prayer_choices()
        if kit_on():
            _kit_option_card(
                self.screen, "You Kneel. What Do You Ask?",
                [{'key': str(i + 1), 'name': pr['name'], 'text': pr['asks']}
                 for i, pr in enumerate(choices)],
                f"1-{max(1, len(choices))}: pray   //   Esc: rise without praying",
                border=FP.GOLD, overlay=0, min_w=700)
            return
        font_title = get_font('heading', 24)
        font_name  = get_font('body', 20, bold=True)
        font_body  = get_font('body', 15)
        font_hint  = get_font('body', 16)

        # Wide enough for its widest line: font widths do not grow exactly
        # with the UI scale (Consolas 23 px is a touch wider than 1.5 x 15 px).
        need = max([font_name.size(f"{i + 1}.  {pr['name']}")[0] + S(40)
                    for i, pr in enumerate(choices)]
                   + [font_body.size(pr['asks'])[0] + S(72) for pr in choices] + [0])
        bw = min(max(S(700), need + S(36)), layout.WINDOW_W - S(48))
        row_h = font_name.get_height() + font_body.get_height() + S(18)
        bh = S(96) + row_h * len(choices) + S(44)
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2
        pygame.draw.rect(self.screen, (16, 12, 6), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, FP.GOLD, (bx, by, bw, bh), 3, border_radius=8)
        pygame.draw.rect(self.screen, (110, 82, 20),
                         (bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=6)

        title = font_title.render("YOU KNEEL. WHAT DO YOU ASK?", True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + S(22)))
        pygame.draw.line(self.screen, FP.GOLD,
                         (bx + S(32), by + S(60)), (bx + bw - S(32), by + S(60)), 1)

        y = by + S(78)
        for i, prayer in enumerate(choices):
            name = font_name.render(f"{i + 1}.  {prayer['name']}", True, FP.GOLD_BRIGHT)
            self.screen.blit(name, (bx + S(40), y))
            y += font_name.get_height() + S(2)
            asks = font_body.render(prayer['asks'], True, FP.BODY_TEXT)
            self.screen.blit(asks, (bx + S(72), y))
            y += font_body.get_height() + S(16)

        hint = font_hint.render(
            "Press the number to pray  //  Esc: rise without praying",
            True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - S(28)))

    def _draw_intercession_prompt(self):
        """v2.13.0: Y/N confirm popup for Divine Intercession. Terse,
        heavy-lidded warning styling — this is the one big ask per run."""
        from fantasy_ui import get_font
        draw_overlay(self.screen, 200)
        if kit_on():
            _kit_option_card(
                self.screen, "Divine Intercession",
                [{'key': 'Y', 'name': 'Seek intercession from God',
                  'text': 'One attempt per run. Success asks much. Failure smites all.'},
                 {'key': 'N', 'name': 'Step back', 'text': 'Rise and keep your one chance.',
                  'name_color': FP.HINT_TEXT}],
                "Y / N: choose   Esc: step back",
                lines=["Do you seek intercession from God?"],
                border=FP.GOLD, overlay=0, min_w=620)
            return

        bw, bh = S(620), S(260)
        bx = (layout.WINDOW_W - bw) // 2
        by = (layout.WINDOW_H - bh) // 2

        # Dark parchment with gold trim — divine, weighty.
        pygame.draw.rect(self.screen, (16, 12, 6), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, FP.GOLD, (bx, by, bw, bh), 3, border_radius=8)
        pygame.draw.rect(self.screen, (110, 82, 20),
                         (bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=6)

        font_title = get_font('heading', 24)
        font_body  = get_font('body', 18)
        font_hint  = get_font('body', 16)

        title_surf = font_title.render("DIVINE INTERCESSION", True, FP.GOLD_BRIGHT)
        self.screen.blit(title_surf,
                         (bx + (bw - title_surf.get_width()) // 2, by + S(24)))

        pygame.draw.line(self.screen, FP.GOLD,
                         (bx + S(32), by + S(62)), (bx + bw - S(32), by + S(62)), 1)

        lines = [
            "Do you seek intercession from God? (y/n)",
            "",
            "One attempt per run.",
            "Success asks much. Failure smites all.",
        ]
        y = by + S(84)
        for line in lines:
            surf = font_body.render(line, True, FP.BODY_TEXT)
            self.screen.blit(surf, (bx + (bw - surf.get_width()) // 2, y))
            y += font_body.get_height() + S(6)

        hint = font_hint.render(
            "Y: seek intercession  //  N or Esc: step back",
            True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2,
                                by + bh - S(28)))

    def _draw_scroll_menu(self):
        tab_items = self._get_scroll_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            is_book = isinstance(item, Spellbook)
            if is_book:
                known = item.spell_id in self.player.known_spells
                if known:
                    detail_text = f"[KNOWN] {item.spell_name}"
                elif self._item_is_known(item):
                    detail_text = f"teaches: {item.spell_name}  {item.mp_cost} MP"
                else:
                    detail_text = "spellbook"
            else:
                if self._item_is_known(item):
                    detail_text = f"Effect: {item.effect.replace('_', ' ').title()}"
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
        self._draw_decision_menu(
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
            # Only an item NOT in the pack is tagged (a "PACK" tag on every
            # row was noise: VISUAL_REVIEW, menu_identify).
            source = "On Ground" if is_g else ""
            if is_c:
                source = "Corpse"
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
        # Plato's Form-of-Ideas passive bypasses the shard requirement; a
        # blessed Scroll of Identify overrides the whole quiz.
        has_plato = 'plato_no_shard' in getattr(self.player, 'hero_passives', set())
        if has_shard:
            shard_line = "Shard: carried"
        elif has_plato:
            shard_line = "Shard: not needed (Plato's Form of Ideas active)"
        else:
            shard_line = "Shard: needed (or use a Scroll of Identify to bypass)"
        context = self._menu_base_context([
            ("IDENTIFICATION", FP.GOLD_BRIGHT, self.font_sm),
            (shard_line, FP.BODY_TEXT, self.font_sm),
            (f"Targets: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("One question. Right: fully identified. Wrong: the Shard stuns you.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu(
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
            from food_system import recipe_is_trophy as _is_trophy
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
                is_trophy = _is_trophy(recipe)
                entries.append({
                    'name': name[:1].upper() + name[1:],
                    'detail': f"Needs: {ing_list}",
                    'key': self._menu_letter(i),
                    'icon': icon_obj,
                    'name_color': FP.GOLD_BRIGHT if is_trophy else FP.GOLD_PALE,
                    'detail_color': FP.BODY_TEXT,
                    'badge': 'TROPHY' if is_trophy else '',
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
            # v2.15.0 UI-rot fix: cook is one-question binary (v2.6.4), not escalator.
            ("Cooking uses one cooking question. Right = full meal; wrong = ruined.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._draw_decision_menu(
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

    def _draw_drop_menu(self):
        tab_items = self._get_drop_tab_items()
        entries = []
        for i, item in enumerate(tab_items):
            if isinstance(item, self._GoldDropEntry):
                dname = f"Gold ({getattr(self, 'player_gold', 0):,} coins)"
                name_col = FP.GOLD_BRIGHT
                detail = "Choose how much to drop"
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
        self._draw_decision_menu(
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
                detail_text = "Raw ingredient: cook it for better results"
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
        self._draw_fast_picker(
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

    def _draw_quaff_menu(self):
        items = self.quaff_menu_items
        entries = []
        for i, item in enumerate(items):
            known = self._item_is_known(item)
            if known:
                eff = item.effect.replace('_', ' ').title()
                dur = f" ({item.duration} turns)" if item.duration else ""
                is_good = item.effect in self._BENEFICIAL_EFFECTS
                detail_text = f"{eff}{dur}"
                detail_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT_LIGHT
                badge = 'BOON' if is_good else 'RISK'
                badge_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT_LIGHT
            else:
                detail_text = "Unidentified - effect hidden"
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
        self._draw_fast_picker(
            title="QUAFF POTION",
            entries=entries,
            selected=selected,
            subtitle="Unknown potions keep their effect hidden until identified",
            hint="Up/Down: move   Enter or a-z: quaff   ESC: cancel",
            border_color=FP.ARCANE_BRIGHT,
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
                known = self._item_is_known(item)
                if known:
                    eff = item.effect.replace('_', ' ').title()
                    dur = f" ({item.duration} turns)" if item.duration else ""
                    detail_text = f"{eff}{dur}"
                else:
                    detail_text = "Effect hidden until identified"
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
        self._draw_fast_picker(
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
        self._draw_fast_picker(
            title="ACTIVE POWERS",
            entries=entries,
            selected=selected,
            subtitle="Only acquired powers are shown",
            hint="Up/Down: move   Enter or a-z: use power   ESC: close",
            border_color=FP.ARCANE_BRIGHT,
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

    def _draw_pet_menu(self):
        """Pet roster + per-pet action rows. Shift+P opens this menu."""
        items = getattr(self, 'pet_menu_items', [])
        entries = []
        from items import Food, Ingredient, Potion
        for idx, pet in enumerate(items):
            cmd = str(getattr(pet, 'command', 'return')).title()
            xp_to = pet._xp_to_next() if hasattr(pet, '_xp_to_next') else 0
            specials_avail = pet.available_specials() if hasattr(pet, 'available_specials') else []
            ready = sum(1 for s in specials_avail if pet.special_cooldown(s['id']) == 0)
            food_count = sum(
                1 for i in self.player.inventory if isinstance(i, (Food, Ingredient)))
            potion_count = sum(
                1 for i in self.player.inventory
                if isinstance(i, Potion)
                and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal')
                and self._item_is_known(i))
            details = [
                (pet.name, FP.GOLD_BRIGHT, self.font_md),
                (f"HP {pet.hp}/{pet.max_hp}    Level {pet.level}", FP.BODY_TEXT, self.font_sm),
                (f"XP {pet.xp}/{xp_to}", FP.BODY_TEXT, self.font_sm),
                (f"Command: {cmd}", FP.CYAN_ACCENT, self.font_sm),
                *self._pet_rescue_lines(pet),
                '',
                ("Available actions", FP.GOLD_BRIGHT, self.font_sm),
                # Key badges like every other kit screen (they were "F - Feed").
                ('__key__', 'F', f"Feed ({food_count} food items in pack)"),
                ('__key__', 'P', "Pet (+5 XP, once per floor)"),
                ('__key__', 'H', f"Heal with a potion ({potion_count} identified healing potions)"),
                ('__key__', 'R', "Recall to the Soul Sphere (when adjacent)"),
                ('__key__', 'C', "Cycle command: return, stay, wander"),
                ('__key__', 'S', f"Specials ({ready} ready of {len(specials_avail)} unlocked)"),
            ]
            entries.append({
                'name': pet.name,
                'detail': f"HP {pet.hp}/{pet.max_hp} | Level {pet.level} | {cmd}",
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
        self._draw_decision_menu(
            title="COMPANIONS",
            entries=entries,
            selected=selected,
            context_lines=context,
            hint="Up/Down: choose pet   a-z: select pet   F/P/H/R/C/S: action   ESC: close",
            border_color=FP.GOLD_BRIGHT,
            scroll_attr='_pet_menu_scroll',
        )

    def _pet_rescue_lines(self, pet) -> list:
        """Shep's rescue on his card: ready, or spent until a new floor."""
        species = getattr(pet, 'species', None) or {}
        rescue = species.get('rescue') if hasattr(pet, 'rescue_ready') else None
        if not rescue:
            return []
        deepest = int(getattr(self.player, 'deepest_floor_reached', 1) or 1)
        if pet.rescue_ready(deepest):
            state, colour = "Ready", FP.SUCCESS_TEXT
        else:
            state, colour = "Spent Until A New Floor", FP.FADED_TEXT
        share = int(round(float(rescue.get('hp_share', 0.25)) * 100))
        return [(f"{rescue['name']}: {state}", colour, self.font_sm),
                (f"Once a floor he runs to you when you fall to {share}% health "
                 f"with a foe beside you.", FP.FADED_TEXT, self.font_sm)]

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
        self._draw_fast_picker(
            title=title,
            entries=entries,
            selected=selected,
            subtitle="Choose a special, then target on the map",
            hint="Up/Down: move   Enter or a-z: special   ESC: back",
            border_color=FP.GOLD_BRIGHT,
        )

    def _draw_pet_sub_picker(self, title: str, items: list, pet, attr: str):
        """Generic sub-menu renderer for feed/heal item pickers."""
        entries = []
        for idx, it in enumerate(items):
            iname = self._display_name(it) if hasattr(self, '_display_name') else it.name
            if attr == 'sp_restore':
                sp = getattr(it, 'sp_restore', 0)
                # The same tags as the Eat menu: a meal is FOOD, an uncooked
                # ingredient is RAW (it said FOOD here and RAW there).
                if isinstance(it, Food) or sp:
                    detail = f"+{sp} SP"
                    badge = 'FOOD'
                    badge_color = FP.SUCCESS_TEXT
                else:
                    detail = "Raw ingredient"
                    badge = 'RAW'
                    badge_color = FP.WARNING_TEXT
            elif attr == 'effect':
                detail = getattr(it, 'effect', '').replace('_', ' ').title()
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
        self._draw_fast_picker(
            title=full_title,
            entries=entries,
            selected=selected,
            subtitle="Companion care",
            hint="Up/Down: move   Enter or a-z: select   ESC: back",
            border_color=FP.GOLD_BRIGHT,
        )

    def _draw_pet_name_popup(self):
        """Overlay shown when a new pet joins (a Soul Sphere hatches, or the
        abandoned Emberpup comes along). Lets the player type a nickname."""
        pet = getattr(self, '_naming_pet', None)
        buf = getattr(self, '_pet_name_input_buffer', '')
        if pet is None:
            return
        story = getattr(self, '_naming_story', None) or {}
        # a creature kind takes "A"; a companion with its own name does not
        from pet_system import has_own_name
        article = '' if has_own_name(pet.species) else 'A '
        self._ui_input_card(
            story.get('title') or f"{article}{pet.species_name.upper()} APPEARS!",
            story.get('prompt') or "Will you give this companion a name?",
            buf,
            "Type: edit   |   Enter: confirm   |   Esc: skip naming",
            border_color=FP.GOLD,
            title_color=FP.GOLD_BRIGHT,
            placeholder="(unnamed)",
            max_w=660,
        )

    def _draw_confirm_exit(self):
        self._ui_message_card(
            "SAVE YOUR PROGRESS?",
            ["Save & Exit keeps this run so you can resume it later.",
             "Abandon ends this run for good: its save is deleted."],
            options=[
                {'key': 'Y', 'label': 'Save & Exit', 'color': FP.GOLD_BRIGHT},
                {'key': 'N', 'label': 'Abandon This Run (Deletes The Save)',
                 'color': FP.DANGER_TEXT_LIGHT, 'danger': True},
                {'key': 'C / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            footer="Enter: save & exit",
            border_color=FP.GOLD,
            max_w=660,
            max_h=360,
        )

    def _draw_exit_quest(self):
        self._ui_message_card(
            "COMPLETE YOUR QUEST?",
            ["You carry the Philosopher's Stone. Leave the dungeon?"],
            options=[
                {'key': 'Y', 'label': 'Complete quest', 'color': FP.GOLD_BRIGHT},
                {'key': 'N / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            footer="Y / N: choose",
            border_color=FP.GOLD,
            max_w=660,
            max_h=330,
        )

    def _draw_abandon_quest(self):
        self._ui_message_card(
            "ABANDON YOUR QUEST?",
            ["You have not found the Philosopher's Stone."],
            options=[
                {'key': 'Y', 'label': 'Abandon quest', 'color': FP.DANGER_TEXT_LIGHT,
                 'danger': True},
                {'key': 'N / Esc', 'label': 'Keep playing', 'color': FP.HINT_TEXT},
            ],
            footer="Y / N: choose",
            border_color=FP.WARNING_TEXT,
            max_w=660,
            max_h=330,
        )

    def _draw_chicken(self):
        self._ui_message_card(
            "What's Wrong, McFly? Chicken?",
            ["Leaving without the Stone ends the quest."],
            options=[
                {'key': '1', 'label': 'Yes, I am a coward.', 'color': FP.DANGER_TEXT_LIGHT,
                 'danger': True},
                {'key': '2', 'label': 'Nobody calls me chicken!', 'color': FP.GOLD_BRIGHT},
            ],
            footer="1 / 2: choose",
            border_color=FP.AMBER_ACCENT,
            max_w=700,
            max_h=360,
        )

    def _draw_story_popup(self):
        """Render the current narrative popup over the game world."""
        if not self.popup_data:
            return
        d = self.popup_data
        draw_overlay(self.screen, 190, (8, 6, 2))

        accent = d['accent']
        raw_lines = d['lines']
        code = d.get('code')
        bw = min(S(920), layout.WINDOW_W - S(96))
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
                    buf = (buf + ' ' + display_text(line)).strip() if buf else display_text(line)
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

        kit = kit_on()
        code_h = S(46) if code else 0
        max_h = layout.WINDOW_H - S(48)
        if kit:
            # Exactly what the panel holds: band, plaque, text, reward code,
            # divider + key footer (a fixed allowance left a third empty).
            chrome = (2 * S(16) + S(self._HEADER_H) + S(12) + S(4)
                      + S(8) + key_hints_height() + S(32) + S(14))
        else:
            chrome = S(122)
        max_txt = bw - 2 * S(36) - (2 * S(16) if kit else 0)

        def measure(size):
            f = get_font('body', size)
            lines = build_lines(f, max_txt)
            r = f.get_height() + S(4)
            h = sum(r // 2 if blank else r for _t, blank, _q in lines)
            return f, lines, r, chrome + h + code_h

        font_body, wrapped_lines, row, needed_h = measure(19)
        if needed_h > max_h:
            font_body, wrapped_lines, row, needed_h = measure(16)

        bh = min(max_h, max(S(250), needed_h))
        by = (layout.WINDOW_H - bh) // 2
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=accent)
        body_top = self._ui_header(panel, d['title'], border_color=accent,
                                   title_color=accent)
        b = panel_band('panel', panel)
        if b:
            _div, keys, foot_bottom = self._ui_footer_metrics(panel)
            y = body_top + S(4)
            body_bottom = foot_bottom - code_h
            tx = bx + b + S(32)
        else:
            y = by + S(74)
            body_bottom = by + bh - S(48) - code_h
            tx = bx + S(36)
        for text, is_blank, is_quoted in wrapped_lines:
            if is_blank:
                y += row // 2
                continue
            if y + font_body.get_height() > body_bottom:
                break
            col = (200, 195, 160) if is_quoted else FP.PARCHMENT_LIGHT
            self._ui_blit_text(text, font_body, col, tx, y)
            y += row

        if code:
            code_y = (body_bottom + S(4)) if b else by + bh - S(84)
            code_rect = pygame.Rect(bx + S(34) + b, code_y, bw - 2 * (S(34) + b), S(40))
            if not (b and ui_theme.draw_piece(self.screen, 'card', code_rect,
                                              body_color=KT.RAISED)):
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, code_rect,
                                 border_radius=6)
                pygame.draw.rect(self.screen, accent, code_rect, 1,
                                 border_radius=6)
            label = "Reward Code: "
            font_label = get_font('small', 16, bold=True)
            font_code = get_font('heading', 22)
            total_w = font_label.size(label)[0] + font_code.size(code)[0]
            lx = code_rect.centerx - total_w // 2
            self._ui_blit_text(label, font_label, FP.PARCHMENT_LIGHT,
                               lx, code_rect.y + S(10))
            self._ui_blit_text(code, font_code, FP.GOLD_BRIGHT,
                               lx + font_label.size(label)[0],
                               code_rect.y + S(6))

        if b:
            draw_divider(self.screen, bx + b + S(28), _div, bw - 2 * (b + S(28)))
            draw_key_hints(self.screen, keys, "Any key: continue")
        else:
            self._ui_blit_text("Press any key to continue", get_font('small', 16),
                               FP.HINT_TEXT, bx + bw // 2, by + bh - S(30),
                               align='center')

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
        """Lay out the ending's title and subtitle and return the next y.

        With the art kit the title is the HEADER of the ending's one framed
        panel: this only measures it and hands the spec to
        ``_draw_end_summary``, which draws the frame from the title's top
        and paints the kit's header plaque (scroll-roll ends, gold rim)
        inset in the frame band with the title on it (VISUAL_REVIEW_2 minor
        1: a plain rectangle bolted on top of the frame). Without art the
        title sits on its own flat plaque, as before.

        DESIGN_RULES 1.1 (text sits on flat colour): the rune circles and
        candle glow are drawn BEFORE this, so the plaque covers them and no
        ray or arc crosses a letter (VISUAL_REVIEW must-fix 2). The filigree
        rule sits in the gap between the lines, never through them."""
        plaque_w = min(S(780), layout.WINDOW_W - S(120))
        kit = kit_on('header') and panel_band('panel', pygame.Rect(0, 0, plaque_w, S(400)))
        b = panel_band('panel', pygame.Rect(0, 0, plaque_w, S(400))) if kit else 0
        # Between the plaque's scroll-roll ends (kit) or its hairlines.
        inner_w = plaque_w - (2 * b + 2 * S(40) if kit else S(48))
        title_font = self._fit_ui_font('title', 42, title_text, inner_w,
                                       bold=True, min_size=28)
        sub_font = self._fit_ui_font('heading', 26, sub_text, inner_w,
                                     min_size=20)

        title_w, title_h = title_font.size(title_text)
        sub_w, sub_h = sub_font.size(sub_text)
        pad = S(12)
        top = max(S(16), cy - S(295))
        if kit:
            # The panel's top edge is ``top``; the plaque sits inside the band.
            # Its painted rim is the bottom 12 px (scale 1): the text keeps
            # clear of it.
            title_y = top + b + S(10)
        else:
            title_y = top + pad
        mid_bar_y = title_y + title_h + S(6)
        sub_y = mid_bar_y + S(8)
        if kit:
            plaque_h = sub_y + sub_h + S(10) + S(12) - (top + b)
            self._end_title_spec = dict(
                top=top, plaque_h=plaque_h, title=(title_text, title_font, title_col,
                                                   title_glow, title_y),
                sub=(sub_text, sub_font, sub_col, sub_glow, sub_y),
                bar=(mid_bar_y, fil_strong, max(title_w, sub_w)), cx=cx)
            return top + b + plaque_h + S(12)
        self._end_title_spec = None
        plaque_bottom = sub_y + sub_h + pad
        plaque = pygame.Rect(cx - plaque_w // 2, top, plaque_w, plaque_bottom - top)
        # A flat field with a gold hairline frame: drawn as an outlined box
        # so the layout gates see the text as sitting in a panel.
        self.screen.fill(KT.PLAQUE, plaque)
        pygame.draw.rect(self.screen, KT.GOLD_DARK, plaque, 1)
        pygame.draw.rect(self.screen, fil_strong, plaque.inflate(-S(6), -S(6)), 1)
        self._draw_end_title_text(cx, plaque_w, (title_text, title_font, title_col,
                                                 title_glow, title_y),
                                  (sub_text, sub_font, sub_col, sub_glow, sub_y),
                                  (mid_bar_y, fil_strong, max(title_w, sub_w)))
        return plaque.bottom + S(4)

    def _draw_end_title_text(self, cx, plaque_w, title, sub, bar):
        title_text, title_font, title_col, title_glow, title_y = title
        sub_text, sub_font, sub_col, sub_glow, sub_y = sub
        mid_bar_y, fil_strong, text_w = bar
        title_w = title_font.size(title_text)[0]
        sub_w = sub_font.size(sub_text)[0]
        title_pos = (cx - title_w // 2, title_y)
        if title_glow:
            draw_glow_text(self.screen, title_font, title_text, title_col,
                           title_pos, glow_color=title_glow)
        else:
            draw_shadow_text(self.screen, title_font, title_text, title_col,
                             title_pos)
        bar_w = min(plaque_w - S(80), text_w + S(40))
        draw_filigree_bar(self.screen, cx - bar_w // 2, mid_bar_y + S(1), bar_w, fil_strong)
        if sub_glow:
            draw_glow_text(self.screen, sub_font, sub_text, sub_col,
                           (cx - sub_w // 2, sub_y), glow_color=sub_glow,
                           glow_r=2)
        else:
            draw_shadow_text(self.screen, sub_font, sub_text, sub_col,
                             (cx - sub_w // 2, sub_y), offset=2)

    def _draw_end_summary(self, cx: int, start_y: int, grade: str,
                          grade_col: tuple, score: int, stats: list,
                          score_col: tuple, accent: tuple,
                          breakdown: str | None = None,
                          high_score_col: tuple | None = None,
                          review_text: str | None = None) -> None:
        """Draw measured score table, optional breakdown, high scores, prompt."""
        from highscore_system import get_top

        content_w = min(S(680), layout.WINDOW_W - S(120))
        small_layout = layout.WINDOW_H < S(800)
        grade_font = self.font_xl if not small_layout else get_font('title', 34, bold=True)
        score_font = self.font_lg if not small_layout else get_font('heading', 28)
        row_font = self.font_md if not small_layout else get_font('body', 23)
        small_font = self.font_sm if not small_layout else get_font('body', 18)

        y = start_y
        panel_w = min(S(780), layout.WINDOW_W - S(120))
        panel_y = max(S(70), start_y - (S(4) if kit_on() else S(14)))
        target_panel_h = S(560) if not small_layout else S(470)
        panel_h = max(S(360), min(target_panel_h, layout.WINDOW_H - panel_y - S(30)))
        spec = getattr(self, '_end_title_spec', None)
        if spec:
            # One frame from the title's top: the title is this panel's header.
            bottom = panel_y + panel_h
            panel_y = spec['top']
            panel_h = bottom - panel_y
        panel = pygame.Rect(cx - panel_w // 2, panel_y, panel_w, panel_h)
        draw_dark_panel(self.screen, panel, border_color=accent)
        # With the kit, everything sits inside the frame band and the keys
        # are badges in a footer (Esc / R), like every other modal.
        b = panel_band('panel', panel)
        keys = None
        if spec and b:
            plaque = pygame.Rect(panel.x + b, panel.y + b, panel.w - 2 * b, spec['plaque_h'])
            if not ui_theme.draw_piece(self.screen, 'header', plaque, accent=accent):
                self.screen.fill(KT.PLAQUE, plaque)
            self._draw_end_title_text(spec['cx'], panel_w, spec['title'], spec['sub'],
                                      spec['bar'])
            start_y = plaque.bottom + S(12)
        if b:
            y = (start_y if spec else panel.y + b + S(12))
            content_w = min(content_w, panel_w - 2 * (b + S(28)))
            _div, keys, foot_bottom = self._ui_footer_metrics(panel)
            draw_divider(self.screen, panel.x + b + S(28), _div, panel_w - 2 * (b + S(28)))
            pairs = []
            if review_text:
                pairs.append(("R", "Review the missed questions"))
            pairs.append(("Esc", "Close"))
            draw_key_hints(self.screen, keys, pairs)

        grade_s = grade_font.render(grade, True, grade_col)
        score_text = f"Final Score:  {score:,}"
        score_w, score_h = score_font.size(score_text)
        head_gap = S(36)
        head_w = grade_s.get_width() + head_gap + score_w
        hx = cx - head_w // 2
        self.screen.blit(grade_s, (hx, y))
        draw_shadow_text(self.screen, score_font, score_text, score_col,
                         (hx + grade_s.get_width() + head_gap, y + S(2)))
        y += max(grade_s.get_height(), score_h) + S(8)

        label_w = max(row_font.size(label + " :")[0] for label, _, _ in stats)
        value_w = max(row_font.size(value)[0] for _, value, _ in stats)
        gap = S(22)
        table_w = min(content_w, label_w + gap + value_w)
        lx = cx - table_w // 2
        vx = lx + label_w + gap
        row_gap = row_font.get_height() + S(2)
        for label, value, col in stats:
            lbl_s = row_font.render(label + " :", True, FP.FADED_TEXT)
            val_s = row_font.render(value, True, col)
            self.screen.blit(lbl_s, (lx, y))
            self.screen.blit(val_s, (vx, y))
            y += row_gap

        y += S(4)
        if b:
            # Clear of the ornament's full reach on both sides.
            y += divider_reach()
            draw_divider(self.screen, cx - content_w // 2, y, content_w)
            y += divider_reach() + S(4)
        else:
            draw_filigree_bar(self.screen, cx - content_w // 2, y, content_w, accent)
            y += S(12)

        if breakdown:
            for line in self._wrap_text(breakdown, small_font, content_w):
                b_surf = small_font.render(line, True, FP.FADED_TEXT)
                self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, y))
                y += small_font.get_height() + S(1)
            y += S(9)

        top = get_top(5)
        prompt_s = row_font.render("Press ESC to close", True, FP.HINT_TEXT)
        bottom_limit = panel_y + panel_h - S(20)
        if keys is not None:
            prompt_s = pygame.Surface((0, 0))
            bottom_limit = foot_bottom
            review_text = None
        hs_title_h = small_font.get_height() + S(2)
        hs_row_h = small_font.get_height() + S(1)
        available = bottom_limit - y - prompt_s.get_height() - S(10)
        rows_fit = max(0, (available - hs_title_h) // hs_row_h)
        show_n = min(len(top), 5, rows_fit)

        if show_n > 0:
            hs_title = small_font.render("High Scores", True,
                                         readable(high_score_col or accent, KT.INTERIOR))
            self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, y))
            y += hs_title_h
            # A real table: rank, name, score, grade and level each in its
            # own column, so the rows line up (they were centred one by one).
            rows = [(f"{i + 1}.", str(e.get('name', '?')), f"{e['score']:,}",
                     str(e.get('grade', '?')), f"Floor {e.get('level', 0)}",
                     e['score'] == score) for i, e in enumerate(top[:show_n])]
            cols = [max(small_font.size(r[k])[0] for r in rows) for k in range(5)]
            cgap = S(18)
            tw = sum(cols) + cgap * 4
            x0 = cx - tw // 2
            for r in rows:
                col = (high_score_col or FP.GOLD_BRIGHT) if r[5] else FP.FADED_TEXT
                x = x0
                for k in range(5):
                    cs = small_font.render(r[k], True, col)
                    # numbers right-aligned, words left-aligned
                    dx = cols[k] - cs.get_width() if k in (0, 2) else 0
                    self.screen.blit(cs, (x + dx, y))
                    x += cols[k] + cgap
                y += hs_row_h
            y += S(4)

        if review_text and y + row_font.get_height() < bottom_limit - prompt_s.get_height() - S(6):
            review_s = row_font.render(review_text, True, FP.GOLD_BRIGHT)
            self.screen.blit(review_s, (cx - review_s.get_width() // 2, y))
            y += row_font.get_height() + S(4)

        if keys is None:
            prompt_y = min(y + S(2), bottom_limit - prompt_s.get_height())
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
        draw_rune_circle(self.screen, cx, cy, S(280), ring_outer, t, 16)
        draw_rune_circle(self.screen, cx, cy, S(190), ring_inner, -t * 1.3, 10)
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
            ("Correct Answers",    self._end_accuracy_text(self.correct_answers, self.wrong_answers),
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]
        breakdown = (f"({self.turn_count}x10)  +  ({self.level_mgr.max_level_reached}x1000)  +"
                     f"  ({self.level_mgr.monsters_killed}x100)  +  50,000 stone bonus")
        if getattr(self, '_secret_victory', False):
            # (the score has it: the breakdown was 50,000 short)
            breakdown += "  +  50,000 Death is dead"

        # (The high score was written when the run ended, in _on_game_over:
        # drawing code records nothing.)
        if not getattr(self, '_victory_fanfare_played', False):
            self._victory_fanfare_played = True
            try:
                import sound_system as _vs
                _vs.play('victory')
            except Exception:
                pass

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
        draw_rune_circle(self.screen, cx, cy, S(260), (*FP.BURGUNDY, 110), t * 0.4, 14)
        draw_rune_circle(self.screen, cx, cy, S(170), (*FP.BLOOD, 70),     -t * 0.6, 8)

        from boss_levels import COW_LEVEL as _COW
        _on_farm = self.dungeon_level == _COW      # (numbered 999: not a level to name)
        if self.defeat_reason == 'fled':
            title_text = "YOU FLED THE DUNGEON"
            sub_text   = "Your quest ends in cowardice."
            tc = FP.WARNING_TEXT
        elif self.defeat_reason == 'starved':
            title_text = "YOU HAVE STARVED"
            sub_text   = ("Hunger claimed you on the Moo Moo Farm." if _on_farm
                          else f"Hunger claimed you on level {self.dungeon_level}.")
            tc = FP.WARNING_TEXT
        else:
            title_text = "YOU HAVE DIED"
            sub_text   = ("Slain on the Moo Moo Farm." if _on_farm
                          else f"Slain on dungeon level {self.dungeon_level}.")
            tc = FP.DEATH_SUB

        grade, grade_col = self._get_grade(score)

        start_y = self._draw_end_title_block(
            cx, cy, title_text, sub_text, FP.DEATH_TITLE, tc,
            FP.BURGUNDY_MID, FP.BURGUNDY_MID,
            title_glow=FP.DEATH_GLOW)

        total_q  = self.correct_answers + self.wrong_answers
        acc_pct  = int(100 * self.correct_answers / total_q) if total_q else 0
        stats = [
            ("Turns Survived",     f"{self.turn_count:,}",                   FP.BODY_TEXT),
            ("Deepest Level",      f"{self.level_mgr.max_level_reached}",     FP.BODY_TEXT),
            ("Monsters Slain",     f"{self.level_mgr.monsters_killed:,}",     FP.BODY_TEXT),
            ("Gold Collected",     f"{self.player_gold:,}",                   FP.GOLD_PALE),
            ("Questions Answered", f"{total_q:,}",                            FP.BODY_TEXT),
            ("Correct Answers",    self._end_accuracy_text(self.correct_answers, self.wrong_answers),
             (120, 210, 120) if acc_pct >= 70 else FP.WARNING_TEXT),
        ]

        # (The high score was written when the run ended, in _on_game_over.)

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
                y += font.get_height() + S(line_gap)
                drawn += 1
        return y

    # -- Panel chrome shared by every modal (Midnight Codex kit) -----------
    # With the art kit loaded a panel has a painted frame BAND (16 px at UI
    # scale 1, ``ui_theme.band``): the header plaque is inset inside it and
    # every piece of content stays inside it. Without art the band is 0 and
    # every helper below lays out exactly as it did before the kit.

    _HEADER_H = 48          # modal header height, UI px

    def _ui_header(self, panel, title, *, border_color=FP.GOLD, title_color=None,
                   h=None, font=None, kind='panel', right_reserve=0,
                   left_reserve=0):
        """Header of ``panel`` and, without art, the divider under it.
        Returns the y where the panel's body may start."""
        panel = pygame.Rect(panel)
        h = S(self._HEADER_H if h is None else h)
        if kit_on('header'):
            title_color = None          # the kit's titles are all gold
        hr = draw_header_bar(self.screen, (panel.x, panel.y, panel.w, h), text=display_text(title),
                             font=font or self.font_lg,
                             text_color=title_color or FP.GOLD_BRIGHT,
                             accent=border_color, right_reserve=right_reserve,
                             left_reserve=left_reserve,
                             frame=(panel, border_color, kind))
        if panel_band(kind, panel) and ui_theme.has('header'):
            return hr.bottom + S(12)
        draw_divider(self.screen, panel.x + S(18), panel.y + h + S(10),
                     panel.w - 2 * S(18))
        return panel.y + h + S(22)

    def _ui_footer_metrics(self, panel, kind='panel'):
        """(divider_y, key_row_rect, body_bottom) of a panel's footer."""
        panel = pygame.Rect(panel)
        b = panel_band(kind, panel)
        if b:
            kh = key_hints_height()
            keys = pygame.Rect(panel.x + b + S(20), panel.bottom - b - S(8) - kh,
                               panel.w - 2 * (b + S(20)), kh)
            div_y = keys.y - S(16)
            return div_y, keys, div_y - S(16)
        y = panel.bottom - S(36)
        return y - S(5), pygame.Rect(panel.x + S(22), y + S(4), panel.w - S(44),
                                     get_font('small', 14).get_height()), panel.bottom - S(52)

    def _ui_modal_panel(self, title, *, border_color=FP.GOLD, max_w=1440,
                        max_h=760, center_window=False, fit_h=None):
        """Overlay + framed panel + header (+ divider); returns the panel rect.

        ``max_w`` / ``max_h`` are caps at UI scale 1 (they grow with it).
        The panel is centred on the WINDOW (SCALE_PLAN.md 3). Its width
        budget is the play area left of the right rail (``GAME_W``), as it
        always was, or the whole window with ``center_window``."""
        draw_overlay(self.screen, 190)
        budget_w = layout.WINDOW_W if center_window else _modal_budget_w()
        bw = min(S(max_w), budget_w - S(48))
        bh = min(S(max_h), layout.WINDOW_H - S(48))
        if fit_h is not None:
            # As tall as the content needs (``fit_h`` screen px), within the cap.
            bh = min(bh, max(S(240), int(fit_h)))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        rect = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, rect, border_color=border_color)
        self._ui_header(rect, title, border_color=border_color)
        return rect

    @staticmethod
    def _ui_modal_body(panel, side=18, top=70, bottom=52):
        """The body area of a ``_ui_modal_panel``: inset ``side`` each side,
        ``top`` below the panel's top edge (under the header and divider),
        ``bottom`` above its bottom edge (over the footer). UI-scale-1 px.
        With the art kit the body also clears the frame band, the inset
        plaque and the key-hint footer."""
        panel = pygame.Rect(panel)
        if panel_band('panel', panel):
            side, top, bottom = side + 12, top + 6, bottom + 28
        return pygame.Rect(panel.x + S(side), panel.y + S(top),
                           panel.w - 2 * S(side), panel.h - S(top) - S(bottom))

    def _ui_subpanel(self, rect, label, *, border_color=FP.GOLD_DARK):
        # Art kit first (ui_theme pieces 'subpanel' + 'subpanel_header');
        # procedural rounded box + label strip otherwise.
        head = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, S(29))
        if ui_theme.draw_piece(self.screen, 'subpanel', rect,
                               accent=border_color, body_color=KT.RAISED):
            ui_theme.draw_piece(self.screen, 'subpanel_header', head,
                                accent=border_color)
            f = get_font('heading', 17, bold=True)
            from fantasy_ui import fit_text
            text = fit_text(display_title(label.upper()), f, head.w - S(40))
            ts = f.render(text, True, KT.TEXT_HEAD)
            self.screen.blit(ts, (head.centerx - ts.get_width() // 2,
                                  head.y + (head.h - S(2) - ts.get_height()) // 2))
        else:
            pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=6)
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, head, border_radius=6)
            f = get_font('small', 14, bold=True)
            self._ui_blit_text(label.upper(), f, FP.GOLD_BRIGHT,
                               rect.centerx, rect.y + S(7), align='center')
        return pygame.Rect(rect.x + S(12), rect.y + S(42), rect.w - 2 * S(12),
                           rect.h - S(54))

    def _ui_footer(self, panel_rect, hint):
        panel_rect = pygame.Rect(panel_rect)
        if panel_band('panel', panel_rect):
            div_y, keys, _bottom = self._ui_footer_metrics(panel_rect)
            b = panel_band('panel', panel_rect)
            draw_divider(self.screen, panel_rect.x + b + S(28), div_y,
                         panel_rect.w - 2 * (b + S(28)))
            draw_key_hints(self.screen, keys, hint)
            return
        y = panel_rect.bottom - S(36)
        draw_divider(self.screen, panel_rect.x + S(18), y - S(5),
                     panel_rect.w - 2 * S(18))
        f = get_font('small', 14)
        self._ui_blit_text(hint, f, FP.HINT_TEXT, panel_rect.centerx,
                           y + S(4), align='center',
                           max_width=panel_rect.w - S(44))

    def _ui_chip(self, rect, label, *, active=False, color=FP.GOLD):
        if ui_theme.draw_piece(self.screen, 'chip_active' if active else 'chip',
                               rect, accent=color if active else None):
            f = get_font('body', 16, bold=active)
            col = KT.TEXT_BODY if active else KT.TEXT_DIM
            from fantasy_ui import fit_text
            ts = f.render(fit_text(str(label), f, rect.w - S(10)), True, col)
            self.screen.blit(ts, (rect.centerx - ts.get_width() // 2,
                                  rect.centery - ts.get_height() // 2))
            return
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT,
                         rect, border_radius=5)
        pygame.draw.rect(self.screen, color if active else FP.GOLD_DARK,
                         rect, 1, border_radius=5)
        f = get_font('small', 14, bold=True)     # the no-art look, unchanged
        self._ui_blit_text(label, f, FP.GOLD_BRIGHT if active else FP.FADED_TEXT,
                           rect.centerx, rect.y + S(6), align='center',
                           max_width=rect.w - S(10))

    def _ui_row(self, rect, selected=False, *, fill=None, border=None,
                radius=6) -> bool:
        """A list row: the kit's ``row`` / ``row_selected`` art, or the
        caller's procedural fill + 1 px border. True when art was drawn."""
        if ui_theme.draw_piece(self.screen, 'row_selected' if selected else 'row',
                               rect, body_color=KT.RAISED):
            return True
        if fill is not None:
            pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        if border is not None:
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=radius)
        return False

    def _ui_row_text(self, color, selected=False):
        """A text colour readable on a (selected) row of the kit."""
        if not kit_on('row'):
            return color
        return readable(color, KT.SELECTED if selected else KT.RAISED)

    def _ui_well(self, rect):
        """The dark well item and creature art sits on (DESIGN_RULES 5.1)."""
        if kit_on():
            rect = pygame.Rect(rect)
            pygame.draw.rect(self.screen, KT.WELL, rect)
            pygame.draw.rect(self.screen, KT.GOLD_DARK, rect, 1)

    def _ui_progress_bar(self, rect, pct, *, color=FP.ARCANE_BRIGHT,
                         label=''):
        if not ui_theme.draw_piece(self.screen, 'bar_track', rect,
                                   body_color=FP.MIDNIGHT):
            pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=4)
        art = ui_theme.has('bar_track') and ui_theme.fits('bar_track', rect.w, rect.h)
        inner = rect.inflate(-S(4), -S(4)) if art else rect
        fill_w = int(inner.w * max(0.0, min(1.0, float(pct))))
        if fill_w:
            pygame.draw.rect(self.screen, color,
                             (inner.x, inner.y, fill_w, inner.h),
                             border_radius=0 if art else 4)
        if not ui_theme.draw_piece(self.screen, 'bar_frame', rect, body=False):
            pygame.draw.rect(self.screen, FP.ARCANE_DIM, rect, 1, border_radius=4)
        if label:
            self._ui_blit_text(label, get_font('small', 12), FP.BODY_TEXT,
                               rect.centerx, rect.y - S(2), align='center')

    def _ui_scrollbar(self, rect, scroll, total_lines, visible_lines,
                      *, color=FP.GOLD_DARK):
        if total_lines <= visible_lines:
            return
        track = pygame.Rect(rect.right - S(8), rect.y, S(5), rect.h)
        if not ui_theme.draw_piece(self.screen, 'scroll_track', track,
                                   body_color=FP.MIDNIGHT):
            pygame.draw.rect(self.screen, FP.MIDNIGHT, track, border_radius=3)
        ratio = visible_lines / max(1, total_lines)
        thumb_h = max(S(20), int(track.h * ratio))
        max_scroll = max(1, total_lines - visible_lines)
        thumb_y = track.y + int((track.h - thumb_h) *
                                (max(0, scroll) / max_scroll))
        thumb = pygame.Rect(track.x, thumb_y, track.w, thumb_h)
        if not ui_theme.draw_piece(self.screen, 'scroll_thumb', thumb,
                                   accent=color):
            pygame.draw.rect(self.screen, color, thumb, border_radius=3)

    def _ui_text_lines(self, text, font, width):
        lines = []
        for chunk in str(text).splitlines() or ['']:
            lines.extend(self._wrap_text(chunk, font, width) or [''])
        return lines

    def _ui_action_row(self, rect, key, label, *, color=FP.BODY_TEXT,
                       selected=False, danger=False):
        key = str(key)
        if ui_theme.draw_piece(self.screen, 'row_selected' if selected else 'row',
                               rect, body_color=KT.RAISED):
            if danger:
                # A destructive choice (it deletes something) is told apart
                # by its edge, not only by colour: a 2 px red frame.
                pygame.draw.rect(self.screen, (226, 92, 84), rect, 2)
            key_font = get_font('body', 16, bold=True)
            label_font = get_font('body', 16, bold=True)
            key_w = max(S(40), min(rect.w // 3, key_font.size(key)[0] + S(18)))
            kh = min(rect.h - 2 * S(8), S(32))
            key_rect = pygame.Rect(rect.x + S(9), rect.centery - kh // 2, key_w, kh)
            draw_key_badge(self.screen, key_rect, key, key_font)
            text_rect = pygame.Rect(key_rect.right + S(12), rect.y + S(6),
                                    rect.right - key_rect.right - S(22),
                                    rect.h - 2 * S(6))
            lines = self._wrap_text(label, label_font, text_rect.w)[:2] or ['']
            lh = label_font.get_height() + S(2)
            ty = text_rect.y + max(0, (text_rect.h - lh * len(lines)) // 2)
            col = readable(color, KT.SELECTED if selected else KT.RAISED)
            for line in lines:
                self._ui_blit_text(line, label_font, col, text_rect.x, ty)
                ty += lh
            return
        fill = FP.MIDNIGHT_MID if selected else FP.MIDNIGHT
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, FP.GOLD if selected else FP.ARCANE_DIM,
                         rect, 1, border_radius=6)

        key_font = get_font('small', 14, bold=True)
        label_font = get_font('small', 15, bold=True)
        key_w = max(S(42), min(rect.w // 3, key_font.size(key)[0] + S(20)))
        key_rect = pygame.Rect(rect.x + S(8), rect.y + S(8), key_w, rect.h - 2 * S(8))
        if not ui_theme.draw_piece(self.screen, 'key', key_rect, accent=color):
            pygame.draw.rect(self.screen, (96, 34, 28), key_rect, border_radius=5)
            pygame.draw.rect(self.screen, color, key_rect, 1, border_radius=5)
        self._ui_blit_text(key, key_font, color, key_rect.centerx,
                           key_rect.y + max(S(4), (key_rect.h - key_font.get_height()) // 2),
                           align='center')

        text_rect = pygame.Rect(key_rect.right + S(12), rect.y + S(8),
                                rect.right - key_rect.right - S(22),
                                rect.h - 2 * S(8))
        self._ui_wrap_text(label, label_font, color, text_rect,
                           line_gap=0, max_lines=2)

    def _ui_message_card(self, title, body_lines, *, options=None,
                         footer='', border_color=FP.GOLD,
                         title_color=None, body_color=FP.BODY_TEXT,
                         max_w=720, max_h=520):
        """Shared wrapped modal for confirmations and small result cards.

        Self-measuring: the panel is as tall as its body + option rows +
        footer (with the kit, plus the frame band and the inset plaque)."""
        draw_overlay(self.screen, 190)
        bw = min(S(max_w), layout.WINDOW_W - S(48))
        body_font = get_font('body', 18)
        small_font = get_font('small', 16)
        kit = kit_on()
        band = S(16) if kit else 0          # measured below once the rect exists
        text_w = bw - 2 * S(36) - 2 * band

        wrapped = []
        for entry in body_lines:
            if entry == '':
                wrapped.append(('', None))
                continue
            if isinstance(entry, tuple):
                text, col = entry[0], entry[1]
            else:
                text, col = entry, body_color
            for line in self._wrap_text(display_text(str(text)), body_font, text_w) or ['']:
                wrapped.append((line, col))

        opts = options or []
        option_h = S(48)
        text_h = sum(S(10) if line == '' else body_font.get_height() + S(4)
                     for line, _ in wrapped)
        if kit:
            foot_h = key_hints_height() + S(40) if footer else S(18)
            bh = (2 * band + S(48) + S(16) + text_h + len(opts) * (option_h + S(8))
                  + (S(10) if opts else 0) + foot_h)
        else:
            bh = S(94) + text_h + (len(opts) * (option_h + S(8))) + S(44)
        bh = min(S(max_h) + 2 * band, layout.WINDOW_H - S(48), max(S(220), bh))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)

        draw_dark_panel(self.screen, panel, border_color=border_color)
        body_top = self._ui_header(panel, title, border_color=border_color,
                                   title_color=title_color)
        b = panel_band('panel', panel)

        y = body_top + (S(4) if b else S(2))
        options_h = len(opts) * (option_h + S(8))
        if b:
            footer_h = (key_hints_height() + S(40)) if footer else S(18)
            body_bottom = by + bh - b - options_h - footer_h
        else:
            footer_h = S(42) if footer else S(22)
            body_bottom = by + bh - options_h - footer_h - S(8)
        tx = bx + b + S(36) if b else bx + S(36)
        for line, col in wrapped:
            if line == '':
                y += S(10)
                continue
            if y + body_font.get_height() > body_bottom:
                break
            col = col or body_color
            if b:
                col = readable(col, KT.INTERIOR)
            self._ui_blit_text(line, body_font, col, tx, y)
            y += body_font.get_height() + S(4)

        if opts:
            y = max(y + (S(18) if b else S(8)), by + bh - b - options_h - footer_h)
            for opt in opts:
                row = pygame.Rect(bx + b + S(34) if b else bx + S(34), y,
                                  bw - 2 * (b + S(34)) if b else bw - 2 * S(34), option_h)
                self._ui_action_row(row, opt.get('key', ''),
                                    opt.get('label', ''),
                                    color=opt.get('color', FP.BODY_TEXT),
                                    selected=opt.get('selected', False),
                                    danger=opt.get('danger', False))
                y += option_h + S(8)

        if footer:
            if b:
                div_y, keys, _bb = self._ui_footer_metrics(panel)
                draw_divider(self.screen, bx + b + S(28), div_y, bw - 2 * (b + S(28)))
                draw_key_hints(self.screen, keys, footer)
            else:
                self._ui_blit_text(footer, small_font, FP.HINT_TEXT,
                                   bx + bw // 2, by + bh - S(30),
                                   align='center', max_width=bw - S(44))

    def _ui_input_card(self, title, prompt, value, hint, *,
                       border_color=FP.GOLD, title_color=None,
                       placeholder='', max_w=620):
        from fantasy_ui import draw_input_box

        draw_overlay(self.screen, 190)
        kit = kit_on()
        band = S(16) if kit else 0
        bw = min(S(max_w), _modal_budget_w() - S(48))
        bh = S(238) + (2 * band + S(30) if kit else 0)
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border_color)
        body_top = self._ui_header(panel, title, border_color=border_color,
                                   title_color=title_color)
        b = panel_band('panel', panel)
        if b:
            prompt_rect = pygame.Rect(bx + b + S(32), body_top + S(2),
                                      bw - 2 * (b + S(32)), S(46))
            box = (bx + b + S(56), prompt_rect.bottom + S(10),
                   bw - 2 * (b + S(56)), S(40))
        else:
            prompt_rect = pygame.Rect(bx + S(36), by + S(76), bw - 2 * S(36), S(46))
            box = (bx + S(70), by + S(132), bw - 2 * S(70), S(38))
        self._ui_wrap_text(prompt, get_font('body', 18),
                           KT.TEXT_BODY if b else FP.BODY_TEXT,
                           prompt_rect, line_gap=2, max_lines=2)
        draw_input_box(self.screen, box, value, self.font_md,
                       border_color=border_color, placeholder=placeholder)
        if b:
            div_y, keys, _bb = self._ui_footer_metrics(panel)
            draw_divider(self.screen, bx + b + S(28), div_y, bw - 2 * (b + S(28)))
            draw_key_hints(self.screen, keys, hint)
        else:
            self._ui_blit_text(hint, get_font('small', 16), FP.HINT_TEXT,
                               bx + bw // 2, by + bh - S(32), align='center',
                               max_width=bw - S(44))

    def _ui_draw_scroll_lines(self, lines, font, color, rect, scroll=0,
                              *, line_gap=3):
        line_gap = S(line_gap)
        line_h = font.get_height() + line_gap
        visible = max(1, rect.h // line_h)
        max_scroll = max(0, len(lines) - visible)
        scroll = max(0, min(int(scroll), max_scroll))
        y = rect.y
        for i, entry in enumerate(lines[scroll:scroll + visible],
                                  start=scroll):
            if isinstance(entry, tuple) and entry and entry[0] == '__cells__':
                y = self._ui_draw_cells(entry, rect, y, line_gap)
                if y is None:
                    break
                continue
            if isinstance(entry, tuple):
                text, col, fnt = entry
                fnt = fnt or font
                col = col or color
            else:
                text, col, fnt = entry, color, font
            if y + fnt.get_height() > rect.bottom:
                break
            self._ui_blit_text(text, fnt, col, rect.x, y, max_width=rect.w - S(12))
            y += fnt.get_height() + line_gap
        self._ui_scrollbar(rect, scroll, len(lines), visible)
        return scroll

    def _ui_draw_cells(self, entry, rect, y, line_gap):
        """One table row from ``_disc_table_lines``: cells in their columns
        (numbers right-aligned), the last cell wrapped into what is left.
        Returns the next y, or None when the row does not fit."""
        _tag, cells, widths, gap, fnt, col, _w = entry
        if y + fnt.get_height() > rect.bottom:
            return None
        x = rect.x
        lines_used = 1
        for k, cell in enumerate(cells):
            last = k == len(cells) - 1
            if last:
                room = rect.right - S(12) - x
                lines = self._wrap_text(cell, fnt, room) or ['']
                for i, ln in enumerate(lines):
                    if y + i * (fnt.get_height() + line_gap) + fnt.get_height() > rect.bottom:
                        break
                    self.screen.blit(fnt.render(ln, True, col),
                                     (x, y + i * (fnt.get_height() + line_gap)))
                lines_used = len(lines)
            else:
                cs = fnt.render(cell, True, col)
                numeric = cell[:1].isdigit() or cell[:1] in '+-'
                dx = widths[k] - cs.get_width() if numeric and k > 0 else 0
                self.screen.blit(cs, (x + dx, y))
                x += widths[k] + gap
        return y + lines_used * (fnt.get_height() + line_gap)

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
        shown_name = self._display_name(item)
        lines = [(shown_name, FP.GOLD_BRIGHT, get_font('heading', 20))]
        if hasattr(item, 'id_level'):
            if id_level >= 5:
                status = "Identified"
            elif self.player.knows_item_type(item):
                from hud_context import unknown_copy_suffix
                status = ("Type known " + unknown_copy_suffix(item)).strip()
            else:
                status = "Unidentified"
            lines.append((status, FP.CYAN_ACCENT, self.font_sm))
        # The heading already carries the true name once it is known, so the
        # field below shows what the item LOOKS like unidentified -- that is
        # what the player needs to recognise it on a later run. Skipped when
        # the heading is itself the appearance (type still unknown).
        unidentified = getattr(item, 'unidentified_name', '')
        if unidentified:
            appearance = self._fix_name_case(unidentified)
            if appearance.lower() not in shown_name.lower():
                lines.append(("Appearance", FP.GOLD_BRIGHT, self.font_sm))
                lines.append((appearance, FP.BODY_TEXT, self.font_sm))

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
            # This copy's own knowledge (the same rule as the Kit and menus).
            if self._copy_buc_known(item):
                aura = getattr(item, 'buc', 'uncursed')
            else:
                aura = "unknown"
            lines.append((f"Aura: {_cap(aura)}", FP.GOLD_PALE, self.font_sm))

        source = "Equipped" if self._lore_equipped_slot(item) else (
            "Pack" if item in getattr(self.player, 'inventory', []) else "Record")
        lines.append((f"Source: {source}", FP.FADED_TEXT, self.font_sm))
        return lines

    @staticmethod
    def _food_restores_text(item) -> str:
        """ "Restores 45 SP" / "Restores 45 SP and 3 HP": only what it does
        restore, each number bound to its unit by a no-break space so a wrap
        never strands "HP" on a line of its own (it read "45 SP, 0 / HP")."""
        parts = [f"{int(v)} {unit}" for v, unit in
                 ((getattr(item, 'sp_restore', 0) or 0, 'SP'),
                  (getattr(item, 'hp_restore', 0) or 0, 'HP')) if v]
        return "Restores " + " and ".join(parts) if parts else "Restores nothing"

    def _lore_enchant_text(self, item) -> str:
        """Enchantment is per-copy knowledge: shown only once THIS copy is
        identified, even when the type is known."""
        if hasattr(item, 'id_level') and int(getattr(item, 'id_level', 0) or 0) < 5:
            return '?'
        return f"+{getattr(item, 'enchant_bonus', 0)}"

    def _lore_item_mechanic_lines(self, item, id_level):
        lines = []
        if id_level < 3 and hasattr(item, 'id_level'):
            lines.append(("Mechanics unrevealed", FP.GOLD_BRIGHT, self.font_sm))
            lines.append(("Identify this item to reveal its stats, effects and chain abilities.",
                          FP.FADED_TEXT, self.font_sm))
            return lines

        if isinstance(item, Weapon):
            dmg_types = ', '.join(_cap(d) for d in (getattr(item, 'damage_types', []) or ['physical']))
            lines += [
                ("Weapon", FP.GOLD_BRIGHT, self.font_sm),
                (f"Type: {_cap(item.weapon_class)}   Material: {_cap(item.material)}   Tier: {item.tier}",
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
                lines.append((f"Requires ammo: {_cap(item.requires_ammo)}", FP.WARNING_TEXT, self.font_sm))

        elif isinstance(item, Armor):
            lines += [
                ("Armor", FP.GOLD_BRIGHT, self.font_sm),
                (f"Slot: {_cap(item.slot)}   Material: {('Unique' if getattr(item, 'is_unique', False) and str(item.material).lower() in ('legendary', 'adamantine') else _cap(item.material))}   Tier: {item.tier}",
                 FP.BODY_TEXT, self.font_sm),
                (f"AC bonus: +{item.ac_bonus}   Enchant: {self._lore_enchant_text(item)}",
                 FP.BODY_TEXT, self.font_sm),
                (_threshold_line("Equip", getattr(item, 'equip_threshold', '?')),
                 FP.BODY_TEXT, self.font_sm),
            ]
            if getattr(item, 'damage_resistances', None):
                lines.append((f"Resists: {self._kit_resist_str(item)}",
                              FP.CYAN_ACCENT, self.font_sm))

        elif isinstance(item, Shield):
            lines += [
                ("Shield", FP.GOLD_BRIGHT, self.font_sm),
                (f"Material: {('Unique' if getattr(item, 'is_unique', False) and str(item.material).lower() in ('legendary', 'adamantine') else _cap(item.material))}   Tier: {item.tier}",
                 FP.BODY_TEXT, self.font_sm),
                (f"AC bonus: +{item.ac_bonus}   Enchant: {self._lore_enchant_text(item)}",
                 FP.BODY_TEXT, self.font_sm),
                (_threshold_line("Equip", getattr(item, 'equip_threshold', '?')),
                 FP.BODY_TEXT, self.font_sm),
            ]
            if getattr(item, 'damage_resistances', None):
                lines.append((f"Resists: {self._kit_resist_str(item)}",
                              FP.CYAN_ACCENT, self.font_sm))

        elif isinstance(item, Accessory):
            lines += [
                ("Accessory", FP.GOLD_BRIGHT, self.font_sm),
                (f"Slot: {_cap(getattr(item, 'slot', 'accessory'))}",
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
                    parts.append(f"Grants {_cap(fx['status'])}")
                lines.append(("Effect: " + ', '.join(parts), FP.CYAN_ACCENT, self.font_sm))
            lines.append((_threshold_line("Equip", getattr(item, 'equip_threshold', '?')),
                          FP.BODY_TEXT, self.font_sm))

        elif isinstance(item, Wand):
            lines += [
                ("Wand", FP.GOLD_BRIGHT, self.font_sm),
                (f"Effect: {getattr(item, 'effect', '?').replace('_', ' ').title()}   Power: {getattr(item, 'power', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (f"Charges: {item.charges}/{item.max_charges}",
                 FP.CYAN_ACCENT, self.font_sm),
                (_threshold_line("Science", getattr(item, 'quiz_threshold', '?')),
                 FP.BODY_TEXT, self.font_sm),
            ]

        elif isinstance(item, Scroll):
            lines += [
                ("Scroll", FP.GOLD_BRIGHT, self.font_sm),
                (f"Effect: {getattr(item, 'effect', '?').replace('_', ' ').title()}   Power: {getattr(item, 'power', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (_threshold_line("Grammar", getattr(item, 'quiz_threshold', '?')),
                 FP.BODY_TEXT, self.font_sm),
            ]

        elif isinstance(item, Spellbook):
            spell_name = getattr(item, 'spell_name', getattr(item, 'name', 'spell'))
            lines += [
                ("Spellbook", FP.GOLD_BRIGHT, self.font_sm),
                (f"Teaches: {spell_name}   MP cost: {getattr(item, 'mp_cost', '?')}",
                 FP.BODY_TEXT, self.font_sm),
                (_threshold_line("Grammar", getattr(item, 'quiz_threshold', '?')),
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
                (self._food_restores_text(item), FP.BODY_TEXT, self.font_sm),
            ]
            bonus_type = getattr(item, 'bonus_type', 'none')
            if bonus_type and bonus_type != 'none':
                target = getattr(item, 'bonus_stat', '') or getattr(item, 'bonus_effect', '')
                lines.append((f"Bonus: {_cap(bonus_type)} {_cap(target)} +{getattr(item, 'bonus_amount', 0)}",
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
                (f"Quiz: {str(subject).title()} {_quiz_mode_phrase(mode)}   Active tier: {achieved}",
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
                identity.append((f"Tags: {', '.join(_cap(x) for x in tags)}", FP.BODY_TEXT, self.font_sm))

        mechanics = []
        if id_level >= 2:
            mechanics.append(("Creature stats", FP.GOLD_BRIGHT, self.font_sm))
            mechanics.append((f"HP: {mdef.get('hp', '?')}   THAC0: {mdef.get('thac0', '?')}   Speed: {mdef.get('speed', 1)}",
                              FP.BODY_TEXT, self.font_sm))
            for atk in mdef.get('attacks', []) or []:
                line = f"{atk.get('name', '?').replace('_', ' ').title()}: {atk.get('damage', '?')} ({_cap(atk.get('type', 'physical'))})"
                effect = atk.get('effect')
                if effect:
                    line += f" -> {effect.replace('_', ' ').title()} {int(atk.get('effect_chance', 0) * 100)}%"
                mechanics.append((line, FP.BODY_TEXT, self.font_sm))
        else:
            mechanics.append(("Unstudied. Identify this corpse to reveal its stats, weaknesses and history.",
                              FP.FADED_TEXT, self.font_sm))

        if id_level >= 3:
            res = mdef.get('resistances', []) or []
            wks = mdef.get('weaknesses', []) or []
            if res:
                mechanics.append((f"Resists: {', '.join(_cap(x) for x in res)}", FP.CYAN_ACCENT, self.font_sm))
            if wks:
                mechanics.append((f"Weak to: {', '.join(_cap(x) for x in wks)}", FP.WARNING_TEXT, self.font_sm))

        if id_level >= 2:
            # Harvest yields exactly ONE ingredient per corpse — either a prime
            # cut or a trophy, chosen by the monster's `is_trophy` flag in
            # prime_cuts.json. The 11 trophy-only monsters (medusa, fafnir,
            # fenrir, abaddon, etc.) have no `_prime` ingredient entry; naive
            # `<kind>_prime` lookup used to miss them and render "Ingredient:
            # none" even though the trophy is real. Fixed 2026-10-03 by
            # mirroring the bestiary trophy-aware logic.
            # Corpses carry `monster_id`, not `kind`. Try both (plus `.id`
            # as a last resort) so Monster-shaped and Corpse-shaped
            # subjects both resolve. 2026-10-03 playtest found the first
            # version only checked `.kind`, which Corpse doesn't have.
            monster_id = (getattr(corpse, 'monster_id', '')
                          or getattr(corpse, 'kind', '')
                          or '')
            legacy_id = getattr(corpse, 'ingredient_id', '')
            try:
                from food_system import (load_ingredient_for,
                                          get_recipes_for_ingredient,
                                          _load_prime_cuts)
                prime_info = _load_prime_cuts().get(monster_id) if monster_id else None
                if prime_info:
                    is_trophy = bool(prime_info.get('is_trophy'))
                    ingredient_id = (f"{monster_id}_trophy" if is_trophy
                                     else f"{monster_id}_prime")
                else:
                    ingredient_id = f"{monster_id}_prime"
                ing = load_ingredient_for(ingredient_id)
                # Legacy fallback for pre-v2.6.5 corpses in old saves.
                if not ing and legacy_id:
                    ing = load_ingredient_for(legacy_id)
                    ingredient_id = legacy_id
                if ing:
                    label = "Trophy" if prime_info and prime_info.get('is_trophy') else "Prime cut"
                    mechanics.append((f"{label}: {ing.name}", FP.GOLD_PALE, self.font_sm))
                    recipes = get_recipes_for_ingredient(ingredient_id)
                    if recipes:
                        mechanics.append(("Known recipe uses", FP.GOLD_BRIGHT, self.font_sm))
                        for recipe in recipes[:5]:
                            mechanics.append((recipe.get('name', '?'), FP.BODY_TEXT, self.font_sm))
                else:
                    mechanics.append(("Ingredient: none (not harvestable)",
                                      FP.FADED_TEXT, self.font_sm))
            except Exception:
                pass

        lore = getattr(corpse, 'lore', '') if id_level >= 4 else (
            "Its history is hidden until you identify the corpse."
        )
        return identity, mechanics, lore or "No lore recorded."

    _LORE_PLATE_PAD = 5          # dark well round a lore picture, UI px

    def _lore_plate_lines(self, ref, body_w, font, line_gap):
        """The picture for a lore pane and the blank lines that make room for
        it at the top of the pane's scrolled text: ``(plate, spacers)``, or
        ``(None, [])`` when the subject has no art (the pane then has no
        picture well at all). The plate leaves the scrollbar lane free."""
        if ref is None:
            return None, []
        pad = S(self._LORE_PLATE_PAD)
        surf = lore_art.plate(ref[0], ref[1], body_w - S(12) - 2 * pad)
        if surf is None:
            return None, []
        line_h = font.get_height() + S(line_gap)
        n = -(-(surf.get_height() + 2 * pad + S(12)) // line_h)
        return surf, [('', None, font)] * n

    def _draw_lore_plate(self, surf, body, scroll, n_spacers, line_h):
        """Draw a lore picture in its framed well at the top of ``body``,
        moved up with the pane's scroll (and clipped to the pane)."""
        if surf is None or scroll >= n_spacers:
            return
        pad = S(self._LORE_PLATE_PAD)
        off = scroll * line_h
        well = pygame.Rect(0, 0, surf.get_width() + 2 * pad, surf.get_height() + 2 * pad)
        well.midtop = (body.x + (body.w - S(12)) // 2, body.y - off)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(body.clip(old_clip))
        pygame.draw.rect(self.screen, KT.WELL, well)
        self.screen.blit(surf, (well.x + pad, well.y + pad))
        inner = pygame.Rect(well.x + pad - 1, well.y + pad - 1,
                            surf.get_width() + 2, surf.get_height() + 2)
        if off == 0:
            pygame.draw.rect(self.screen, KT.GOLD_DARK, well, 1)
            pygame.draw.rect(self.screen, KT.VOID, inner, 1)
        else:
            # Sliding under the pane's top edge: no top rule.
            x0, x1, y0, y1 = well.left, well.right - 1, well.top, well.bottom - 1
            pygame.draw.lines(self.screen, KT.GOLD_DARK, False,
                              [(x0, y0), (x0, y1), (x1, y1), (x1, y0)])
        self.screen.set_clip(old_clip)

    def _draw_lore_dossier_screen(self):
        """The item / bestiary dossier: Identity, Mechanics and Lore panes.

        VISUAL_REVIEW (2026-10-16): the focused pane (Tab) is plain to see --
        a 2 px bright-gold frame and a lit plaque, the others dimmed (only a
        1 px rule changed shade before); the dossier is sized to its content
        and at most px(1240) wide, so at 3440x1440 it is no longer three
        nearly empty panes across the window."""
        subject = getattr(self, '_lore_subject', None)
        if not subject:
            return

        is_corpse = isinstance(subject, Corpse)
        id_level = self._lore_direct_id_level(subject)
        border = FP.LORE_GOLD_BORDER if is_corpse else FP.LORE_BLUE_BORDER
        if is_corpse:
            identity_lines, mech_lines, lore_text = self._lore_corpse_lines(subject, id_level)
            lore_color = FP.LORE_GOLD_BODY
        else:
            # True Name model: knowing the TYPE reveals stats and lore for
            # every copy (the Kit panel already did this; the dossier read
            # the raw per-copy level and showed "Mechanics unrevealed").
            # The identity pane keeps the raw level: its Identified badge
            # and aura are about THIS copy.
            # What the name shows is what the player knows: a stored 1-4
            # (``identified = True`` from a scripted grant) is not enough.
            visible = id_level
            if hasattr(subject, 'id_level'):
                visible = self._kit_visible_level(subject)
            identity_lines = self._lore_item_identity_lines(subject, id_level)
            mech_lines = self._lore_item_mechanic_lines(subject, visible)
            lore_text = (getattr(subject, 'lore', '') if visible >= 4 else
                         "The history of this item remains hidden. Identify it to read the full record.")
            lore_color = FP.LORE_BLUE_BODY
        lore_text = display_text(lore_text)

        max_w = 1240
        bw = min(S(max_w), _modal_budget_w() - S(48))
        probe = self._ui_modal_body(pygame.Rect(0, 0, bw, 1000))
        gutter = S(14)
        # The lore is the longest text: it gets the widest pane.
        left_w = max(S(240), min(S(320), int(probe.w * 0.27)))
        mid_w = max(S(250), min(S(360), int(probe.w * 0.29)))
        right_w = probe.w - left_w - mid_w - gutter * 2
        lore_font = get_font('body', 18)

        def wrap(lines, w):
            out = []
            for text, color, fnt in lines:
                for wrapped in self._ui_text_lines(text, fnt, w):
                    out.append((wrapped, color, fnt))
            return out

        # pane bodies are their rect minus the subpanel chrome (12 px each
        # side, 42 above, 12 below)
        id_render_lines = wrap(identity_lines, left_w - 2 * S(12) - S(10))
        # The subject's picture heads the Identity pane: the item itself, or
        # the living creature a corpse was. It scrolls with the pane's text.
        plate, spacers = self._lore_plate_lines(
            lore_art.subject_ref(subject), left_w - 2 * S(12), self.font_sm, 4)
        id_render_lines = spacers + id_render_lines
        mech_render_lines = wrap(mech_lines, mid_w - 2 * S(12) - S(10))
        lore_lines = [(line, lore_color, lore_font)
                      for line in self._ui_text_lines(lore_text, lore_font, right_w - 2 * S(12) - S(12))]

        def height(lines, gap):
            return sum(f.get_height() + S(gap) for _t, _c, f in lines)
        need = max(height(id_render_lines, 4), height(mech_render_lines, 4),
                   height(lore_lines, 5))
        fit_h = probe.y + (1000 - probe.bottom) + S(54) + need + S(10)
        panel = self._ui_modal_panel(
            "BESTIARY DOSSIER" if is_corpse else "ITEM DOSSIER",
            border_color=border,
            max_w=max_w,
            max_h=760,
            fit_h=max(fit_h, S(330)),
        )
        body = self._ui_modal_body(panel)
        identity_rect = pygame.Rect(body.x, body.y, left_w, body.h)
        mechanics_rect = pygame.Rect(identity_rect.right + gutter, body.y,
                                     mid_w, body.h)
        lore_rect = pygame.Rect(mechanics_rect.right + gutter, body.y,
                                right_w, body.h)

        focus = getattr(self, '_lore_focus', 'mechanics')
        panes = (('identity', identity_rect, "Identity"),
                 ('mechanics', mechanics_rect, "Mechanics"),
                 ('lore', lore_rect, "Lore Reader"))
        bodies = {}
        for key, rect, label in panes:
            on = focus == key
            bodies[key] = self._ui_subpanel(
                rect, label, border_color=FP.GOLD_BRIGHT if on else FP.GOLD_DARK)
            if on:
                # The pane Tab has moved to: a bright 2 px frame round it.
                pygame.draw.rect(self.screen, KT.GOLD_HI, rect.inflate(S(4), S(4)), 2)
        id_body, mech_body, lore_body = bodies['identity'], bodies['mechanics'], bodies['lore']

        self._lore_identity_scroll = self._ui_draw_scroll_lines(
            id_render_lines, self.font_sm, FP.BODY_TEXT, id_body,
            getattr(self, '_lore_identity_scroll', 0), line_gap=4)
        self._draw_lore_plate(plate, id_body, self._lore_identity_scroll,
                              len(spacers), self.font_sm.get_height() + S(4))
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
        body = self._ui_modal_body(panel)
        gutter = S(14)

        rail_body = None
        if not death and body.w >= S(1000):
            rail_w = S(320)
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
            row_h = S(40)
            y = rail_body.y
            for subject, count in counts:
                if y + row_h > rail_body.bottom:
                    break
                active = subject == self._STUDY_SUBJECTS[self._study_subject_idx]
                rect = pygame.Rect(rail_body.x, y, rail_body.w - S(8), row_h - S(6))
                self._ui_row(rect, active,
                            fill=(35, 43, 82) if active else FP.MIDNIGHT,
                            border=FP.GOLD if active else FP.GOLD_DARK, radius=5)
                self._ui_blit_text('AI' if subject == 'ai' else subject.title(),
                                   get_font('body', 17, bold=True),
                                   FP.GOLD_BRIGHT if active else FP.BODY_TEXT,
                                   rect.x + S(10), rect.y + S(8),
                                   max_width=rect.w - S(60))
                self._ui_blit_text(str(count), self.font_sm, FP.FADED_TEXT,
                                   rect.right - S(10), rect.y + S(8), align='right')
                y += row_h

        if not missed:
            self._ui_blit_text("No missed questions in this subject.",
                               get_font('body', 20), FP.FADED_TEXT,
                               main_body.x, main_body.y + S(4),
                               max_width=main_body.w - S(12))
            self._ui_footer(panel, "Left/Right: subject   ESC: close")
            return

        q = missed[idx]
        raw_subject = str(q.get('subject', '?'))
        subject = 'AI' if raw_subject == 'ai' else proper_name(raw_subject.replace('_', ' '))
        counter = f"{idx + 1} of {len(missed)}"
        # One reading size for the question and its context (the context
        # was a size smaller; the subject tag was 12 px cyan capitals).
        read_f = get_font('body', 20)
        lines = [
            (f"{subject}  \u2022  {counter}", KT.TEXT_SUB, get_font('body', 18, bold=True)),
            ("Question", FP.GOLD_BRIGHT, self.font_sm),
            (display_text(q.get('question', '')), FP.PARCHMENT_LIGHT, read_f),
            ("Your answer", FP.DANGER_TEXT_LIGHT, self.font_sm),
            (q.get('chosen', ''), FP.BODY_TEXT, self.font_sm),
            ("Correct answer", FP.SUCCESS_TEXT, self.font_sm),
            (q.get('correct', ''), FP.BODY_TEXT, self.font_sm),
        ]
        context = q.get('context', '')
        if context:
            lines += [
                ("Context", FP.GOLD_BRIGHT, self.font_sm),
                (display_text(context, sources=True), FP.BODY_TEXT, read_f),
            ]

        render_lines = []
        for text, color, fnt in lines:
            if text == "":
                render_lines.append(("", color, fnt))
                continue
            # a section label ("Question", "Your answer"...) opens its block:
            # the gap goes ABOVE it, so the label sits on its own text
            if color in (FP.GOLD_BRIGHT, FP.DANGER_TEXT_LIGHT, FP.SUCCESS_TEXT) and render_lines:
                render_lines.append(("", color, fnt))
            for line in self._ui_text_lines(text, fnt, main_body.w - S(14)):
                render_lines.append((line, color, fnt))

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

    def _draw_review_missed(self):
        self._draw_question_review_browser(death=True)

    def _draw_lore_screen(self):
        self._draw_lore_dossier_screen()

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
            f"You have {have:,} gold. Enter the amount to drop on your current tile.",
            self.drop_gold_input or "0",
            "Digits: amount   |   Enter: confirm   |   Esc: cancel",
            border_color=FP.GOLD,
            max_w=600,
        )

    def _draw_drop_qty_input(self):
        """Numeric entry overlay: how many of a stacked item to drop."""
        item = getattr(self, '_drop_qty_item', None)
        have = getattr(item, 'count', 1) if item else 0
        import re as _re
        # The name without its " x3" (the prompt said "3 Bread Ration x3").
        name = _re.sub(r' x\d+$', '', self._display_name(item)) if item else 'items'
        self._ui_input_card(
            "DROP HOW MANY?",
            f"You carry {have} of {name}. A blank entry drops the whole stack.",
            self.drop_qty_input or str(have),
            "Digits: quantity   |   Enter: confirm   |   Esc: cancel",
            border_color=FP.GOLD,
            max_w=680,
        )

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
        self._draw_decision_menu(
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

    def _draw_shop(self):
        """Draw the merchant shop overlay through the shared decision menu (_draw_decision_menu).

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
            # The price leads the sub-line (no separate price chip: it took
            # the room the name needed and shrank the shop's names to 15 px,
            # below every other picker's; VISUAL_REVIEW_2 minor 4).
            detail = f"{price:,} gold   Weight {getattr(item, 'weight', 0):.1f}"
            if i in haggled:
                detail += "   Haggled"
            # The item's name heads the pane ONCE (it was printed twice: the
            # shop's own line, then the item block's title), then the price.
            item_lines = self._menu_item_detail_lines(
                item, "Press Enter to buy this item if you can afford it.")
            details = item_lines[:1] + [
                (f"Price: {price:,} gold (you have {getattr(self, 'player_gold', 0):,})",
                 FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT, self.font_sm),
                ("Already haggled for this item." if i in haggled
                 else "H: try to haggle the price down (once per item).",
                 FP.FADED_TEXT, self.font_sm),
                '',
            ] + item_lines[1:]
            entries.append({
                'name': self._display_name(item),
                'detail': detail,
                'icon': item,
                'name_color': FP.BODY_TEXT if affordable else FP.FADED_TEXT,
                'detail_color': FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                'details': details,
            })

        selected = self._menu_clamp_selection('_shop_selection', len(entries))
        context = self._menu_base_context([
            ("MERCHANT", FP.GOLD_BRIGHT, self.font_sm),
            (f"Your gold: {getattr(self, 'player_gold', 0):,}", FP.GOLD_PALE, self.font_sm),
            (f"Stock remaining: {len(entries)}", FP.BODY_TEXT, self.font_sm),
            ("Use H before buying if you want one chance to haggle that item.",
             FP.FADED_TEXT, self.font_sm),
        ])
        self._menu_more_cue = "The full lore is yours to read once you buy it."
        self._draw_decision_menu(
            title="TRAVELLING MERCHANT",
            entries=entries,
            selected=selected,
            context_lines=context,
            hint="Up/Down: inspect   Enter: buy   H: haggle   ESC: close",
            border_color=FP.GOLD,
            scroll_attr='_shop_scroll',
        )

    def _charsheet_count_label(self, active_filter: str, shown: int, total: int) -> str:
        """The pack count line: how many things you carry, not a limit.

        It read "All: 26/26 shown", which looked like a 26-item cap; the only
        carry limit is weight ("Carrying 43 / 100", top right). "26 items in pack" with every
        filter, "Gear: 8 of 26 items" when a filter hides some."""
        noun = "item" if total == 1 else "items"
        if active_filter == 'all' or shown == total:
            return f"{total} {noun} in pack"
        return f"{active_filter.title()}: {shown} of {total} {noun}"

    @staticmethod
    def _encyclopedia_weapon_type(entry) -> str:
        """A weapon's kind for the encyclopedia ('Sword'); the data calls it
        'class' (it read 'weapon_class', which no weapon has: every entry said '?')."""
        kind = entry.get('weapon_class') or entry.get('class') or ''
        return proper_name(str(kind).replace('_', ' ')) if kind else 'Weapon'

    def _encyclopedia_entry_brief(self, category, entry):
        if not entry:
            return ''
        if category == 'bestiary':
            hp = entry.get('hp', entry.get('max_hp', '?'))
            min_lvl = entry.get('min_level', '?')
            return f"HP {hp} / min level {min_lvl}"
        if category == 'weapon':
            return f"{self._encyclopedia_weapon_type(entry)} / {entry.get('base_damage', '?')} damage"
        if category == 'armor':
            return f"{entry.get('slot', 'armor')} / AC {entry.get('ac_bonus', '?')}"
        if category == 'accessory':
            effects = entry.get('effects', {}) or {}
            if 'stat' in effects:
                return f"{effects.get('stat')} {int(effects.get('amount', 0)):+d}"
            if 'status' in effects:
                return f"Grants {_cap(effects.get('status'))}"
            return 'accessory'
        if category in ('wand', 'scroll'):
            return f"Effect: {entry.get('effect', '?')}"
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
                lines.append((f"Resists: {', '.join(_cap(x) for x in res)}", FP.CYAN_ACCENT, self.font_sm))
            if wks:
                lines.append((f"Weak to: {', '.join(_cap(x) for x in wks)}", FP.WARNING_TEXT, self.font_sm))
            for atk in entry.get('attacks', []) or []:
                line = f"{atk.get('name', '?').replace('_', ' ').title()}: {atk.get('damage', '?')} ({_cap(atk.get('type', 'physical'))})"
                if atk.get('effect'):
                    line += f" -> {atk.get('effect').replace('_', ' ').title()} {int(atk.get('effect_chance', 0) * 100)}%"
                lines.append((line, FP.BODY_TEXT, self.font_sm))
        elif category == 'weapon':
            damage_types = ', '.join(_cap(t) for t in entry.get('damage_types', ['physical']))
            lines += [
                # one fact a line: the article pane is narrow at 1280x720 and a
                # pair per line wrapped mid-pair ("Tier:" / "5")
                (f"Type: {self._encyclopedia_weapon_type(entry)}", FP.BODY_TEXT, self.font_sm),
                (f"Tier: {entry.get('tier', '?')}", FP.BODY_TEXT, self.font_sm),
                (f"Damage: {entry.get('base_damage', '?')}", FP.BODY_TEXT, self.font_sm),
                (f"Damage types: {damage_types}", FP.BODY_TEXT, self.font_sm),
            ]
            if entry.get('two_handed') or entry.get('twoHanded'):
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
                    bits.append(f"Grants {_cap(effects.get('status'))}")
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
                ("", FP.BODY_TEXT, get_font('body', 10)),   # space above the heading, not only below
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
        body = self._ui_modal_body(panel)
        gutter = S(14)
        cat_w = min(S(260), max(S(220), int(body.w * 0.20)))
        list_w = min(S(420), max(S(330), int(body.w * 0.32)))
        cat_rect = pygame.Rect(body.x, body.y, cat_w, body.h)
        list_rect = pygame.Rect(cat_rect.right + gutter, body.y,
                                list_w, body.h)
        article_rect = pygame.Rect(list_rect.right + gutter, body.y,
                                   body.right - (list_rect.right + gutter),
                                   body.h)
        cat_body = self._ui_subpanel(cat_rect, "Categories")
        list_body = self._ui_subpanel(list_rect, "Known Entries")
        article_body = self._ui_subpanel(article_rect, "Article")

        row_h = S(45)
        y = cat_body.y
        for idx, (key_label, slug, label) in enumerate(cats):
            if y + row_h > cat_body.bottom:
                break
            active = (category and slug == category) or (not category and idx == active_idx)
            rect = pygame.Rect(cat_body.x, y, cat_body.w - S(8), row_h - S(6))
            if self._ui_row(rect, active,
                            fill=(35, 43, 82) if active else FP.MIDNIGHT,
                            border=FP.GOLD if active else FP.GOLD_DARK, radius=5):
                kr = pygame.Rect(rect.x + S(7), rect.centery - S(12), S(24), S(24))
                draw_key_badge(self.screen, kr, key_label, get_font('body', 16, bold=True))
                lf = get_font('body', 17, bold=True)
                self._ui_blit_text(label, lf, FP.GOLD_BRIGHT if active else FP.BODY_TEXT,
                                   kr.right + S(10), rect.centery - lf.get_height() // 2,
                                   max_width=rect.right - kr.right - S(16))
            else:
                self._ui_blit_text(key_label, get_font('small', 13, bold=True),
                                   FP.GOLD_BRIGHT, rect.x + S(10), rect.y + S(10))
                self._ui_blit_text(label, get_font('small', 14, bold=True),
                                   FP.GOLD_BRIGHT if active else FP.BODY_TEXT,
                                   rect.x + S(36), rect.y + S(8),
                                   max_width=rect.w - S(44))
            y += row_h

        entries = getattr(self, 'encyclopedia_entries', []) or []
        if not category:
            # The same size and tone as every other empty-pane note; it
            # said "No category selected." in 24 px while a category was
            # visibly highlighted.
            self._ui_wrap_text("Press Enter to open the highlighted category.",
                               self.font_sm, FP.FADED_TEXT, article_body)
            self._ui_footer(panel, "Up/Down: category   Enter or a-j: open   ESC: close")
            return

        sel = max(0, min(getattr(self, 'encyclopedia_selection', 0),
                         max(0, len(entries) - 1)))
        self.encyclopedia_selection = sel
        entry_row_h = S(60)
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
                rect = pygame.Rect(list_body.x, y, list_body.w - S(10),
                                   entry_row_h - S(7))
                selected = idx == sel
                self._ui_row(rect, selected,
                            fill=(35, 43, 82) if selected else FP.MIDNIGHT,
                            border=FP.GOLD if selected else FP.ARCANE_DIM, radius=6)
                name = self._fix_name_case(entry.get('name',
                                                     entry.get('_id', '?')))
                kit = kit_on()
                nf = get_font('body', 18, bold=True) if kit else get_font('small', 15, bold=True)
                bf = get_font('body', 16) if kit else get_font('small', 12)
                self._ui_wrap_text(name, nf,
                                   FP.GOLD_BRIGHT if selected else FP.BODY_TEXT,
                                   pygame.Rect(rect.x + S(10), rect.y + S(5),
                                               rect.w - S(20), nf.get_height() + S(2)),
                                   line_gap=0, max_lines=1)
                brief = self._encyclopedia_entry_brief(category, entry)
                if brief:
                    self._ui_blit_text(brief, bf,
                                       FP.FADED_TEXT, rect.x + S(10),
                                       rect.bottom - bf.get_height() - S(4),
                                       max_width=rect.w - S(20))
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
            for line in self._ui_text_lines(text, fnt, article_body.w - S(14)):
                render_lines.append((line, color, fnt))
            if color in (FP.GOLD_PALE, FP.GOLD_BRIGHT):
                # a small spacer under a heading (it was a blank line in the
                # heading's own 24 px font: a two-line gap under the title)
                render_lines.append(("", color, get_font('body', 10)))
        # The creature's or item's picture heads the article; the text flows
        # below it and the picture scrolls away with it.
        plate, spacers = self._lore_plate_lines(
            lore_art.encyclopedia_ref(category, entry), article_body.w, self.font_sm, 5)
        render_lines = spacers + render_lines
        self._encyclopedia_article_scroll = self._ui_draw_scroll_lines(
            render_lines, self.font_sm, FP.BODY_TEXT, article_body,
            getattr(self, '_encyclopedia_article_scroll', 0),
            line_gap=5)
        self._draw_lore_plate(plate, article_body, self._encyclopedia_article_scroll,
                              len(spacers), self.font_sm.get_height() + S(5))

        if getattr(self, '_encyclopedia_entry', None) is not None:
            footer = "Up/Down/PgUp/PgDn: scroll article   ESC: list"
        else:
            footer = "Left/Right or a-j: category   Up/Down: entry   Enter: detail   PgUp/PgDn: article   ESC: categories"
        self._ui_footer(panel, footer)

    def _draw_encyclopedia(self):
        self._draw_encyclopedia_browser()

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
        panel = self._ui_modal_panel(f"Recall Lore - {label}",
                                     border_color=FP.LORE_GOLD_BORDER,
                                     max_w=860,
                                     max_h=340)
        body = self._ui_modal_body(panel, side=28, top=78, bottom=54)
        self._ui_blit_text("Chain quality", get_font('small', 16, bold=True),
                           FP.GOLD_BRIGHT, body.x, body.y)
        star_x = body.x + S(130)
        for idx in range(5):
            rect = pygame.Rect(star_x + idx * S(34), body.y - S(2), S(23), S(23))
            active = idx < chain
            if not ui_theme.draw_piece(self.screen, 'chip_active' if active else 'chip', rect):
                pygame.draw.rect(self.screen,
                                 FP.GOLD_DARK if active else FP.MIDNIGHT,
                                 rect, border_radius=4)
                pygame.draw.rect(self.screen, FP.LORE_GOLD_BORDER,
                                 rect, 1, border_radius=4)
            if active:
                # A drawn gold diamond (a literal "*" read as a placeholder).
                cx, cy, d = rect.centerx, rect.centery, S(7)
                pts = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
                pygame.draw.polygon(self.screen, KT.GOLD_HI, pts)
                pygame.draw.polygon(self.screen, KT.GOLD_DARK, pts, 1)

        text_rect = pygame.Rect(body.x, body.y + S(44), body.w, body.h - S(58))
        self._ui_wrap_text(hint_text, get_font('body', 18),
                           FP.LORE_GOLD_BODY, text_rect, line_gap=5)
        self._ui_blit_text("Saved to Encyclopedia / Lore Hints",
                           get_font('small', 16), FP.CYAN_ACCENT,
                           body.x, body.bottom - S(16),
                           max_width=body.w)
        cd = getattr(self.player, 'recall_lore_cooldown', 0)
        self._ui_footer(panel, f"Next recall in {cd} turns   Any key: close")

    def _draw_hint_screen(self):
        self._draw_recall_lore_card()

    def _draw_debug_overlay(self):
        """Transparent debug HUD showing spawn/balance data for playtesting."""

        font = self.font_sm
        lh = S(18)  # line height
        pad = S(8)
        x0 = S(6)
        y0 = S(6)

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
        lines.append(f"Kills this run: {kills}  Gold: {getattr(self, 'player_gold', 0):,}")

        # -- Zoom mode --
        lines.append(f"Zoom: {self.zoom_mode}  State: {self.state}")

        # Draw background panel
        panel_w = S(460)
        panel_h = pad * 2 + len(lines) * lh
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (x0, y0))

        # Draw text
        for i, line in enumerate(lines):
            color = (0, 255, 100) if i == 0 else (200, 220, 200)
            surf = font.render(line, True, color)
            self.screen.blit(surf, (x0 + pad, y0 + pad + i * lh))

    def _draw_message_log(self):
        """L: the message history (bug bash 4, call 16). Every line the log
        still holds (``MessageLog.MAX``), oldest at the top, in the log's
        own colours, opened at the newest line and scrolled with the keys."""
        from ui import log_line_color
        panel = self._ui_modal_panel("MESSAGE HISTORY", border_color=FP.GOLD,
                                     max_w=1100, max_h=760)
        body = self._ui_modal_body(panel, side=24, top=72, bottom=56)
        entries = list(self.msg_log.entries)
        reader = self._ui_subpanel(body, f"{len(entries)} Messages, Newest Last")
        font = get_font('body', 18)
        # Wrapped once per (log contents, font, width): up to 500 entries
        # must not be re-wrapped every frame.
        key = (len(entries), entries[-1] if entries else None, entries[0] if entries else None,
               font, reader.w)
        cached = getattr(self, '_message_log_cache', None)
        if cached is not None and cached[0] == key:
            lines = cached[1]
        else:
            lines = []
            for text, kind in entries:
                col = log_line_color(kind, 0)
                for i, ln in enumerate(self._ui_text_lines(display_text(text), font,
                                                           reader.w - S(24))):
                    lines.append((ln if i == 0 else "  " + ln, col, font))
            self._message_log_cache = (key, lines)
        if not lines:
            lines = [("Nothing has happened yet.", FP.FADED_TEXT, font)]
        line_h = font.get_height() + S(4)
        self._message_log_page = max(1, reader.h // line_h)
        self._message_log_scroll = self._ui_draw_scroll_lines(
            lines, font, FP.BODY_TEXT, reader,
            getattr(self, '_message_log_scroll', 10 ** 6), line_gap=4)
        self._ui_footer(panel, "Up/Down: scroll   PgUp/PgDn: page   "
                               "Home/End: oldest/newest   L / ESC: close")

    def _draw_help_screen(self):
        # Pure keybind reference. Every listing maps to a real action in
        # game_input.py — do not add prose cards or parenthetical commentary.
        groups = [
            ("Movement", [
                ("Arrows", "Move / attack", FP.BODY_TEXT),
                (".", "Wait / meditate", FP.BODY_TEXT),
                ("< >", "Go up / down stairs", FP.BODY_TEXT),
                ("Tab", "Cycle zoom", FP.BODY_TEXT),
            ]),
            ("Combat", [
                ("A", "Melee attack", FP.BODY_TEXT),
                ("F", "Fire ranged weapon", FP.BODY_TEXT),
                ("T", "Throw item", FP.BODY_TEXT),
                ("M / Z", "Cast spell / zap wand", FP.BODY_TEXT),
                ("V", "Powers menu", FP.BODY_TEXT),
            ]),
            ("Items", [
                ("E", "Equip menu", FP.BODY_TEXT),
                ("X", "Examine item", FP.BODY_TEXT),
                ("I", "Identify item", FP.BODY_TEXT),
                ("H", "Harvest corpse", FP.BODY_TEXT),
                ("C", "Cook menu", FP.BODY_TEXT),
                ("D", "Drop / use tile", FP.BODY_TEXT),
                ("U / Q", "Eat / drink a potion", FP.BODY_TEXT),
                ("R", "Read scroll or book", FP.BODY_TEXT),
            ]),
            ("Knowledge", [
                ("@", "Character: equip, drop", FP.BODY_TEXT),
                ("B", "Encyclopedia", FP.BODY_TEXT),
                ("J", "Discoveries", FP.BODY_TEXT),
                ("K", "Kit: compare, equip, drop", FP.BODY_TEXT),
                ("W", "Quirks progress", FP.BODY_TEXT),
                (";", "Study journal", FP.BODY_TEXT),
                ("N", "Recall lore", FP.BODY_TEXT),
                ("L", "Message history", FP.BODY_TEXT),
            ]),
            ("World", [
                ("G / ,", "Pick up item", FP.BODY_TEXT),
                ("P", "Unlock / disarm", FP.BODY_TEXT),
                ("Y", "Merchant shop", FP.BODY_TEXT),
                ("\\", "Pray", FP.BODY_TEXT),
                ("Shift+\\", "Divine Intercession", FP.BODY_TEXT),
                ("O", "Observe cursor", FP.BODY_TEXT),
                ("Shift+P", "Pet menu", FP.BODY_TEXT),
            ]),
            ("System", [
                ("1-4", "Answer quiz", FP.BODY_TEXT),
                ("SPACE", "Strike now", FP.BODY_TEXT),
                ("C", "Quiz context", FP.BODY_TEXT),
                ("PgUp/PgDn", "Scroll long quiz", FP.BODY_TEXT),
                ("?", "Command help", FP.BODY_TEXT),
                ("F10", "Sound on / off", FP.BODY_TEXT),
                ("F11", "Full screen", FP.BODY_TEXT),
                ("ESC", "Cancel / close", FP.BODY_TEXT),
            ]),
        ]

        panel = self._ui_modal_panel("COMMAND REFERENCE",
                                     border_color=FP.GOLD,
                                     max_w=1380,
                                     max_h=760)
        body = self._ui_modal_body(panel, side=24, top=72, bottom=52)

        cols = 3 if body.w >= S(780) else 2
        gutter = S(18)
        col_w = (body.w - gutter * (cols - 1)) // cols
        row_gap = S(18)
        rows = (len(groups) + cols - 1) // cols
        group_h = (body.h - row_gap * (rows - 1)) // rows
        font_key = get_font('small', 14, bold=True)
        font_cmd = get_font('small', 15)
        # ONE row pitch for every group, set by the longest list, so the
        # columns line up (Items, the longest, was ~26 px against ~30).
        longest = max(len(c) for _t, c in groups)
        kit_row_h = min(S(34), max(S(24), (group_h - S(34)) // max(1, longest)))

        for idx, (title, commands) in enumerate(groups):
            col = idx % cols
            row = idx // cols
            rect = pygame.Rect(body.x + col * (col_w + gutter),
                               body.y + row * (group_h + row_gap),
                               col_w, group_h)
            if kit_on():
                self._ui_blit_text(title, get_font('heading', 18, bold=True),
                                   KT.TEXT_HEAD, rect.x, rect.y - S(1))
                pygame.draw.line(self.screen, KT.GOLD_DARK,
                                 (rect.x, rect.y + S(26)), (rect.right, rect.y + S(26)), 1)
            else:
                self._ui_blit_text(title.upper(), get_font('small', 15, bold=True),
                                   FP.GOLD_PALE, rect.x, rect.y)
                pygame.draw.line(self.screen, FP.GOLD_DARK,
                                 (rect.x, rect.y + S(24)), (rect.right, rect.y + S(24)), 1)
            y = rect.y + S(34)
            if kit_on():
                # Every row is shown, each key badge as wide as the widest
                # key and centred with its line; a long line shrinks, then
                # ellipsizes (it used to be cut to its first wrapped line:
                # "Read scroll or").
                from fantasy_ui import key_label as _kl
                # Each column's badges are as wide as ITS widest key (one
                # global width left "Ascend / descend st..." no room at
                # 1280x720), and every line is short enough to show whole.
                kf = get_font('body', 16, bold=True)
                key_w = max(kf.size(_kl(k))[0] for k, _d, _c in commands) + S(18)
                row_h = kit_row_h
                for key_label, desc, color in commands:
                    if y + row_h > rect.bottom + S(2):
                        break
                    kr = pygame.Rect(rect.x, y + (row_h - S(26)) // 2, key_w, S(26))
                    draw_key_badge(self.screen, kr, _kl(key_label), kf)
                    tw = rect.right - kr.right - S(12)
                    df, text = self._fit_line(desc, tw, (16,))
                    ds = df.render(text, True, readable(color, KT.INTERIOR))
                    self.screen.blit(ds, (kr.right + S(12), y + (row_h - ds.get_height()) // 2))
                    y += row_h
                continue
            # every row is shown: a small window makes the rows shorter
            # (they used to stop at 28px and drop whatever did not fit, so
            # "R: Read" was never listed)
            row_h = max(S(18), (rect.bottom - y) // max(1, len(commands)))
            key_w = S(74) if col_w < S(360) else S(88)
            for key_label, desc, color in commands:
                if y + row_h > rect.bottom + S(2):
                    break
                key_rect = pygame.Rect(rect.x, y + S(2), key_w, S(24))
                if kit_on():
                    from fantasy_ui import key_label as _kl
                    draw_key_badge(self.screen, key_rect, _kl(key_label),
                                   get_font('body', 15, bold=True))
                else:
                    pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, key_rect,
                                     border_radius=5)
                    pygame.draw.rect(self.screen, FP.GOLD_DARK, key_rect, 1,
                                     border_radius=5)
                    self._ui_blit_text(key_label, font_key, FP.GOLD_BRIGHT,
                                       key_rect.centerx, key_rect.y + S(5),
                                       align='center', max_width=key_rect.w - S(8))
                desc_rect = pygame.Rect(key_rect.right + S(10), y,
                                        rect.right - key_rect.right - S(10),
                                        row_h)
                self._ui_wrap_text(desc, font_cmd, color, desc_rect,
                                   line_gap=0, max_lines=1)
                y += row_h

        self._ui_footer(panel, "? / ESC: close")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

