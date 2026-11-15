"""BocochoRenderMixin: the Bococho's screens (src/bococho_encounter.py,
src/game_race.py) and the hero in her saddle (src/game_riding.py).

* ``_draw_bococho_screen``: the camp's screen for the young Bococho or Gilt
  Varro: the picture on the left, the phase's words or choices on the right
  (the Emberpup's screen, by the same plan).
* ``_draw_race_screen``: the race panel along the bottom of the window, over
  the message log, with the whole oval in view above it, so the two birds
  are seen moving round the track between legs.
* ``_draw_rider``: the saddled picture with the hero's own sprite set on the
  seat (data/bococho.json ``riding.seat``, ``rider_scale``).
* ``_pet_bococho_lines``: her saddlebags and riding on her pet card.
"""
from __future__ import annotations

import pygame

import fantasy_ui
import layout
import lore_art
from ui_scale import px as S
from fantasy_ui import (FP, get_font, draw_header_bar, draw_divider,
                        draw_overlay, panel_band, key_hints_height, display_text)


def _centre_x(w: int) -> int:
    return (layout.WINDOW_W - w) // 2


def _centre_y(h: int) -> int:
    return (layout.WINDOW_H - h) // 2


class BocochoRenderMixin:

    # ---- the camp's screen -------------------------------------------------

    def _draw_bococho_screen(self):
        import bococho_encounter as bc
        d = bc.data()
        who = getattr(self, '_bc_who', 'young')
        phase = getattr(self, '_bc_phase', 'options')
        npc = getattr(self, '_bc_npc', None)
        border = FP.AMBER_ACCENT
        title = d['title_varro'] if who == 'varro' else d['title_young']
        sid = d['sprites']['varro'] if who == 'varro' else d['sprites']['young']

        draw_overlay(self.screen, 190)
        kit = bool(panel_band('panel', pygame.Rect(0, 0, S(860), S(400))))
        bw = min(S(860), layout.WINDOW_W - S(48))
        b = S(16) if kit else 0
        inner_w = bw - 2 * (b + S(28)) if kit else bw - 2 * S(30)
        pic = lore_art.plate('monster', bc.sprite(getattr(npc, 'kind', None) or sid), S(192))
        pic_w = (pic.get_width() + S(24)) if pic is not None else 0
        text_w = inner_w - pic_w
        font = get_font('body', 18)
        line_h = font.get_height() + S(4)
        row_h = S(50)
        options = self._bococho_options() if phase == 'options' else []

        def text_h(paras):
            n = sum(len(self._wrap_text(display_text(p), font, text_w)) for p in paras)
            return n * line_h + max(0, len(paras) - 1) * S(10)

        if phase == 'story':
            paras = list(d['varro_story'] if who == 'varro' else d['story'])
            content_h = text_h(paras)
        elif phase == 'options':
            paras = [self._bococho_waiting_text()]
            content_h = text_h(paras) + S(14) + len(options) * (row_h + S(8))
        else:
            paras = [getattr(self, '_bc_text', '') or '']
            content_h = text_h(paras)
        content_h = max(content_h, pic.get_height() + S(8) if pic is not None else 0)
        head_h = S(48)
        foot_h = S(8) + key_hints_height() + S(32)
        bh = 2 * b + head_h + S(18) + content_h + S(10) + foot_h
        bh = max(S(240), min(bh, layout.WINDOW_H - S(48)))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        fantasy_ui.draw_dark_panel(self.screen, panel, border_color=border)
        if panel_band('panel', panel):
            b = panel_band('panel', panel)
            body_top = self._ui_header(panel, title, border_color=border, h=48)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body_rect = pygame.Rect(bx + b + S(28), body_top + S(4),
                                    bw - 2 * (b + S(28)), foot_bottom - body_top - S(4))
        else:
            draw_header_bar(self.screen, (bx, by, bw, S(44)), text=title,
                            font=get_font('heading', 20), text_color=FP.GOLD_BRIGHT,
                            accent=border, frame=(panel, border))
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
            for key, label in options:
                self._ui_action_row(pygame.Rect(col.x, y, col.w, row_h), key,
                                    display_text(label), color=FP.PARCHMENT_LIGHT)
                y += row_h + S(8)
            self._ui_footer(panel, f"1-{len(options)}: choose   |   Esc: walk away")
        else:
            self._ui_footer(panel, "Enter / Space / Esc: continue")

    # ---- the race ----------------------------------------------------------

    def _draw_race_screen(self):
        """The race panel along the bottom of the window (over the message
        log), compact, with the whole oval in view above it (the map frames
        it: game_race._race_view, which reads the height drawn here)."""
        info = self._race_panel()
        border = FP.GOLD_BRIGHT
        font = get_font('body', 17)
        line_h = font.get_height() + S(3)
        row_h = S(48)
        kit = bool(panel_band('panel', pygame.Rect(0, 0, S(860), S(300))))
        b = S(16) if kit else 0
        pw = min(layout.MAP_W - S(16), S(1040))
        text_w = pw - 2 * (b + S(22))

        def lines_h(lines):
            n = sum(len(self._wrap_text(display_text(t), font, text_w)) for t in lines)
            return n * line_h + max(0, len(lines) - 1) * S(4)

        lines = list(info['lines'])
        status = info.get('status') or ''
        opts = list(info['options'])
        head_h = S(42)
        foot_h = S(8) + key_hints_height() + S(28)
        body_h = (lines_h(lines) + (S(6) + lines_h([status]) if status else 0)
                  + (S(8) + len(opts) * (row_h + S(5)) if opts else 0))
        ph = min(layout.WINDOW_H - S(24), 2 * b + head_h + S(14) + body_h + S(8) + foot_h)
        self._race_panel_h = ph
        px = layout.MAP_X + (layout.MAP_W - pw) // 2
        py = layout.WINDOW_H - ph - S(8)
        self._draw_race_runner_tags(py)
        panel = pygame.Rect(px, py, pw, ph)
        fantasy_ui.draw_dark_panel(self.screen, panel, border_color=border)
        if panel_band('panel', panel):
            b = panel_band('panel', panel)
            body_top = self._ui_header(panel, info['title'], border_color=border, h=42)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body = pygame.Rect(px + b + S(22), body_top + S(4), pw - 2 * (b + S(22)),
                               foot_bottom - body_top - S(4))
        else:
            draw_header_bar(self.screen, (px, py, pw, S(40)), text=info['title'],
                            font=get_font('heading', 20), text_color=FP.GOLD_BRIGHT,
                            accent=border, frame=(panel, border))
            body = pygame.Rect(px + S(22), py + S(52), pw - 2 * S(22), ph - S(96))
        y = body.y
        for i, t in enumerate(lines):
            if i:
                y += S(4)
            y = self._ui_wrap_text(display_text(t), font, FP.PARCHMENT_LIGHT,
                                   pygame.Rect(body.x, y, body.w, body.bottom - y), line_gap=3)
        if status:
            y += S(6)
            y = self._ui_wrap_text(display_text(status), font, FP.GOLD_PALE,
                                   pygame.Rect(body.x, y, body.w, body.bottom - y), line_gap=3)
        if opts:
            y += S(8)
            for key, label in opts:
                self._ui_action_row(pygame.Rect(body.x, y, body.w, row_h), key,
                                    display_text(label), color=FP.PARCHMENT_LIGHT)
                y += row_h + S(5)
        self._ui_footer(panel, info['footer'])

    def _draw_race_runner_tags(self, panel_top: int):
        """A ring and a name over each bird on the oval, so the two can be
        told apart and followed at the whole-oval scale (never over the
        panel)."""
        import bococho_encounter as bc
        r = self.renderer
        T = r.map_tile_size
        font = get_font('body', 16, bold=True)
        names = {'hero': (bc.data()['race'].get('tag_hero', 'Her'), FP.GOLD_BRIGHT),
                 'rival': (bc.data()['race'].get('rival_name', 'Brassbeak'), FP.CYAN_ACCENT)}
        for who, (label, colour) in names.items():
            m = self._race_runner(who) if hasattr(self, '_race_runner') else None
            if m is None:
                continue
            sx, sy = r.world_to_screen(m.x, m.y)
            cx, cy = sx + T // 2, sy + T // 2
            if cy + T >= panel_top:
                continue
            pygame.draw.circle(self.screen, colour, (cx, cy), max(4, int(T * 0.9)), max(1, S(2)))
            surf = font.render(label, True, colour)
            box = pygame.Rect(0, 0, surf.get_width() + S(8), surf.get_height() + S(2))
            box.midbottom = (cx, cy - int(T * 0.9) - S(2))
            box.clamp_ip(pygame.Rect(layout.MAP_X, 0, layout.MAP_W, max(1, panel_top)))
            if box.bottom >= panel_top:
                continue
            pygame.draw.rect(self.screen, FP.MIDNIGHT, box, border_radius=S(3))
            self.screen.blit(surf, (box.x + S(4), box.y + S(1)))

    # ---- the hero in the saddle --------------------------------------------

    def _draw_rider(self, sprite_name: str = 'player') -> bool:
        """The saddled Bococho with the hero on her back, on his tile. True
        when drawn (False: draw the hero plainly)."""
        import riding
        import bococho_encounter as bc
        mount = self._mount() if hasattr(self, '_mount') else None
        if mount is None or not getattr(self.player, 'riding', False):
            return False
        r = self.renderer
        T = r.map_tile_size
        want = riding.saddled_sprite(getattr(mount, 'stage', 1))
        saddle = r._get_sprite(bc.sprite(want))
        hero = r._get_env_sprite(sprite_name) or r._get_env_sprite('player')
        if saddle is None or hero is None:
            return False
        sx, sy = r.world_to_screen(self.player.x, self.player.y)
        cfg = riding.data()
        seat_x, seat_y = riding.seat(want)
        hs = max(4, int(T * float(cfg.get('rider_scale', 0.6))))
        small = pygame.transform.smoothscale(hero, (hs, hs))
        hx = sx + int(seat_x * T / 64) - hs // 2
        hy = sy + int(seat_y * T / 64) - int(hs * float(cfg.get('rider_hip_share', 0.55)))
        self.screen.blit(saddle, (sx, sy))
        self.screen.blit(small, (hx, hy))
        return True

    # ---- her card ----------------------------------------------------------

    def _pet_bococho_lines(self, pet) -> list:
        """Her saddlebags and riding, on her card in the pet menu."""
        import riding
        if not riding.is_bococho(pet):
            return []
        import bococho_encounter as bc
        d = bc.data()['pet']
        lines = [(d['card'][0].format(lb=d.get('saddlebags_lb', 0)), FP.SUCCESS_TEXT, self.font_sm)]
        if riding.can_carry(pet):
            lines.append((d['card'][1], FP.FADED_TEXT, self.font_sm))
        else:
            lines.append((d['card_small'], FP.FADED_TEXT, self.font_sm))
        return lines
