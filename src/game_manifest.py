"""ManifestMixin: the Dreamspun Sketchbook's Manifest on the Game (the rules
are src/sketch_manifest.py and data/manifest.json).

Brandon, 2026-11-15: "she should be able to Manifest ANY monster she has
studied; needs a new menu UI so it's easy to sort by what she'd want...
probably element/attack type? then in the menu sorted by level, descending."

* ``_open_manifest_menu``: Manifest in the V menu opens the menu (no turn
  spent): every kind she has studied and any creature in view, a tab for All
  and one per bite type, the rows by level, highest first. A known foe in
  view marks the kinds whose bite it is weak to ("Weak!"), and the menu
  opens on the tab with the most of them. With nothing to draw it says so.
* ``_manifest_input``: Left / Right (Tab, Shift+Tab) change the tab; Up /
  Down, PgUp / PgDn, Home / End move; Enter draws (the AI quiz); Esc closes
  (the generic close in game_input, no turn spent).
* ``_manifest_complete``: the quiz's end. No right answer and the page
  smudges; else the sketch stands beside her for INT + 5 turns a right
  answer, and the power rests (data/manifest.json ``cooldown``).
* ``_draw_manifest_menu``: the screen, on the cook menu's plan: the tabs,
  the list (each kind's picture, name, level and bite type) and the chosen
  kind's detail with its picture large.
* ``_qa_manifest``: the Titivillus QA key (Shift+V): the sketchbook in the
  pack, every kind it can draw up to max(10, floor + 5) studied, the power
  ready.
"""
from __future__ import annotations

import pygame

import family_lore
import layout
import lore_art
import sketch_manifest as manifest
import ui_theme
from fantasy_ui import (FP, KT, get_font, draw_dark_panel, draw_overlay, panel_band,
                        readable, display_text, kit_on)
from game_states import STATE_PLAYER, STATE_QUIZ, STATE_MANIFEST_MENU
from geom import monster_at_tile
from naming import quantity
from ui_scale import px as S


SKETCHBOOK_ID = 'dreamspun_sketchbook'


def _centre(w: int, h: int) -> tuple:
    return (layout.WINDOW_W - w) // 2, (layout.WINDOW_H - h) // 2


def _budget_w() -> int:
    """The width a modal may use (game_render._modal_budget_w)."""
    import ui_scale
    return layout.WINDOW_W if ui_scale.is_compact() else layout.GAME_W


class ManifestMixin:

    _MANIFEST_HINT = "Left/Right: Change Tab   Up/Down: Move   Enter: Draw   ESC: Close"
    _MANIFEST_BORDER = FP.PASSIVE_MANIFEST          # the sketchbook's lavender

    # ------------------------------------------------------------------
    # Opening the menu
    # ------------------------------------------------------------------

    def _manifest_seen_monsters(self) -> list:
        """The creatures in view she could look at: seen (never a concealed
        one), and not an ally or a person of an encounter."""
        out = []
        for m in self.monsters or ():
            if not getattr(m, 'alive', False) or not self._sees_monster(m):
                continue
            if (getattr(m, 'is_allied', False) or getattr(m, '_npc_encounter_tag', None)
                    or getattr(m, '_flavor_encounter_tag', None)
                    or getattr(m, '_is_unicorn', False)):
                continue
            out.append(m)
        return out

    def _manifest_known_foes(self, seen) -> list:
        """[(name, monster)] of the creatures in view whose kind she knows
        (studied, its page opened, or its family at Lore): what she would
        want to draw against."""
        from naming import proper_name
        out = []
        for m in seen:
            if family_lore.knowledge(self.player, m) >= family_lore.KNOWN:
                out.append((proper_name(str(getattr(m, 'name', '') or '')), m))
        return out

    def _open_manifest_menu(self) -> bool:
        """Manifest from the V menu. Returns True: no turn is spent by
        opening it (the drawing's quiz spends it), nor by finding nothing to
        draw."""
        seen = self._manifest_seen_monsters()
        rows = manifest.make_rows(family_lore.studied(self.player),
                                  [getattr(m, 'kind', '') for m in seen],
                                  self._manifest_known_foes(seen))
        if not rows:
            self.add_message(manifest.EMPTY_LINE, 'warning')
            return True
        tabs = manifest.tabs(rows)
        open_slug = manifest.opening_tab(rows)
        self._mf_rows = rows
        self._mf_tabs = tabs
        self._mf_tab = next((i for i, t in enumerate(tabs) if t[0] == open_slug), 0)
        self._mf_open = (open_slug, manifest.reason_line(open_slug, rows))
        self._mf_sel = 0
        self._mf_layout_cache = {}
        self.state = STATE_MANIFEST_MENU
        return True

    def _manifest_tab_slug(self) -> str:
        tabs = getattr(self, '_mf_tabs', None) or [(manifest.ALL, 'All', 0)]
        return tabs[int(getattr(self, '_mf_tab', 0) or 0) % len(tabs)][0]

    def _manifest_tab_rows(self, slug: str | None = None) -> list:
        return manifest.tab_rows(getattr(self, '_mf_rows', None) or [],
                                 slug or self._manifest_tab_slug())

    # ------------------------------------------------------------------
    # Keys
    # ------------------------------------------------------------------

    def _manifest_input(self, key: int):
        """Left / Right (and Tab, Shift+Tab back) change the tab, wrapping
        round; the cursor keys move; Enter draws the chosen kind."""
        tabs = getattr(self, '_mf_tabs', None) or []
        if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB) and tabs:
            back = key == pygame.K_LEFT
            if key == pygame.K_TAB:
                try:
                    back = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                except pygame.error:
                    back = False
            self._mf_tab = (int(getattr(self, '_mf_tab', 0) or 0) + (-1 if back else 1)) % len(tabs)
            self._mf_sel = 0
            return
        rows = self._manifest_tab_rows()
        if key in self._MENU_CURSOR_KEYS:
            self._mf_sel = self._move_menu_cursor(getattr(self, '_mf_sel', 0), key, len(rows))
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER) and rows:
            row = rows[max(0, min(int(getattr(self, '_mf_sel', 0) or 0), len(rows) - 1))]
            self._manifest_begin(row)

    # ------------------------------------------------------------------
    # The drawing: the quiz, then the sketch beside her
    # ------------------------------------------------------------------

    def _manifest_begin(self, row: dict) -> None:
        """Enter on a kind: the AI quiz (an escalator chain to 5)."""
        pl = self.player
        self._mf_kind = row['kind']
        whence = " from memory" if row.get('studied') else ''
        self.add_message(
            f"You begin sketching the {row['name']}{whence}, with furious concentration.",
            'info')
        q = manifest.quiz()
        subject = q.get('subject', 'ai')
        self.quiz_title = "MANIFESTING  --  AI"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(
            mode=q.get('mode', 'escalator_chain'),
            subject=subject,
            tier=int(q.get('tier', 1)),
            callback=self._manifest_complete,
            max_chain=manifest.max_chain(),
            wisdom=pl.WIS,
            timer_modifier=pl.get_quiz_timer_modifier(),
            extra_seconds=pl.get_quiz_extra_seconds(subject),
            base_seconds=pl.get_quiz_timer(subject),
        )

    def _manifest_complete(self, result) -> None:
        """The quiz is over: a sketch that lasts INT + 5 turns for each right
        answer, or a smudge."""
        pl = self.player
        chain = int(getattr(result, 'score', 0) or 0)
        kind = getattr(self, '_mf_kind', None)
        self._mf_kind = None
        turns = manifest.duration(manifest.stat_value(pl), chain)
        if not kind or turns <= 0:
            self.add_message(
                "The sketch smudges and fades to nothing. The page goes blank.", 'warning')
            self.state = STATE_PLAYER
            self._advance_turn()
            return
        pet = self._manifest_spawn(kind, turns)
        if pet is None:
            self.add_message(
                "There is no room for the sketch to stand. It fades from the page.", 'warning')
            self.state = STATE_PLAYER
            self._advance_turn()
            return
        self.add_message(
            f"The sketch shimmers and peels off the page! "
            f"A Sketched {pet.monster_name} materializes! ({quantity(turns, 'turn')})",
            'success')
        pl.power_cooldowns[manifest.power_id()] = manifest.cooldown()
        self.state = STATE_PLAYER
        self._advance_turn()

    def _manifest_spawn(self, kind: str, turns: int):
        """The sketch of ``kind``, drawn from its definition (from memory:
        the kind's mean health, not one creature's), set down beside the
        hero: a free tile next to him, else a little further out, never on
        his own tile (MNK-07). None when there is no room."""
        from monster import Monster
        from pet_system import SketchedPet
        d = manifest.defn(kind)
        if d is None:
            return None
        subject = Monster(d, 0, 0)
        subject.max_hp = subject.hp = manifest.mean_hp(d)
        px, py = self.player.x, self.player.y
        spot = None
        taken = self._occupants(hero=False)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            nx, ny = px + dx, py + dy
            if (self.dungeon.is_walkable(nx, ny)
                    and monster_at_tile(self.monsters, nx, ny) is None
                    and (nx, ny) not in taken):
                spot = (nx, ny)
                break
        if spot is None:
            spot = self._escort_tile_near_hero()
        if spot is None:
            return None
        # A helper that comes and goes: never a companion (the one-companion
        # rule, pet_system.counts_as_companion).
        pet = SketchedPet(subject, spot[0], spot[1], int(turns))
        self.pets.append(pet)
        return pet

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def _qa_manifest(self) -> None:
        """Titivillus QA build only (Shift+V): the Dreamspun Sketchbook in the
        pack, every kind it can draw up to max(10, floor + 5) studied, and
        Manifest ready, so the menu can be tried at once."""
        pl = self.player
        if not getattr(pl, 'qa_tools', False):
            return
        if not any(getattr(i, 'id', '') == SKETCHBOOK_ID for i in pl.inventory):
            from items import make_item_by_id
            book = make_item_by_id('accessory', SKETCHBOOK_ID)
            if book is not None:
                book.id_level = 5
                book.buc_known = True
                pl.known_item_ids.add(SKETCHBOOK_ID)
                pl.inventory.append(book)
                pl.refresh_carry_bonuses()
        floor = int(getattr(self, 'dungeon_level', 1) or 1)
        new = sum(1 for k in manifest.qa_kinds(floor) if family_lore.record_study(pl, k))
        pl.power_cooldowns[manifest.power_id()] = 0
        self.add_message(
            f"[QA] Manifest: the Dreamspun Sketchbook in the pack, "
            f"{quantity(new, 'kind')} newly studied (up to Level {manifest.qa_max_level(floor)}). "
            f"V, then Manifest.", 'info')
        self._family_news()

    # ------------------------------------------------------------------
    # The screen
    # ------------------------------------------------------------------

    def _mf_ink(self, color):
        """A text colour readable on the menu's panes (KT.RAISED)."""
        return readable(color, KT.RAISED) if kit_on() else color

    def _manifest_icon(self, kind: str, size: int):
        """A kind's own picture at ``size`` px for its row; None when it has
        none (never a letter glyph)."""
        key = ('manifest', kind, int(size))
        cache = self._menu_sprite_cache
        if key not in cache:
            from renderer import fit_sprite
            path = lore_art.art_path('monster', kind)
            try:
                cache[key] = (fit_sprite(pygame.image.load(path).convert_alpha(), size, size)
                              if path else None)
            except (pygame.error, OSError):
                cache[key] = None
        return cache[key]

    def _draw_manifest_menu(self):
        """The Manifest menu: All and a tab per bite type, the tab it opened
        on marked and why beside it; the list of kinds by level; the chosen
        kind's picture, what it is and how long a drawing lasts."""
        border = self._MANIFEST_BORDER
        tabs = getattr(self, '_mf_tabs', None) or [(manifest.ALL, 'All', 0)]
        tab_i = int(getattr(self, '_mf_tab', 0) or 0) % len(tabs)
        slug, label, _n = tabs[tab_i]
        rows = self._manifest_tab_rows(slug)
        open_slug, reason = getattr(self, '_mf_open', None) or (manifest.ALL, '')

        draw_overlay(self.screen, 190)
        bw = min(S(1240), _budget_w() - S(32))
        bh = min(S(720), layout.WINDOW_H - S(32))
        panel = pygame.Rect(*_centre(bw, bh), bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        body_top = self._ui_header(panel, "Manifest", border_color=border)
        side = panel_band('panel', panel) + S(14)
        cx, cw = panel.x + side, panel.w - 2 * side

        open_i = next((i for i, t in enumerate(tabs) if t[0] == open_slug), None)
        marked = {open_i: KT.GOLD_HI} if (reason and open_i is not None) else None
        y = self._draw_action_tabs([(t[1], t[0]) for t in tabs], tab_i,
                                   [t[2] for t in tabs], cx, body_top, cw, marked=marked)
        if reason:
            y = self._manifest_draw_reason(reason, cx, cw, body_top, y)

        _div, _keys, body_bottom = self._ui_footer_metrics(panel)
        gap = S(12)
        list_w, detail_w = self._decision_split(cw, gap, 0.48)
        list_rect = pygame.Rect(cx, y, list_w, body_bottom - y)
        detail_rect = pygame.Rect(list_rect.right + gap, y, detail_w, body_bottom - y)
        title = "Every Creature" if slug == manifest.ALL else f"{label} Attacks"
        lb = self._ui_subpanel(list_rect, title, border_color=border)
        db = self._ui_subpanel(detail_rect, "Detail", border_color=border)
        list_body = pygame.Rect(list_rect.x + S(8), lb.y - S(4), list_rect.w - 2 * S(8),
                                list_rect.bottom - lb.y - S(4))
        detail_body = pygame.Rect(db.x + S(2), db.y, db.w - S(4), db.h)
        if rows:
            sel = self._menu_clamp_selection('_mf_sel', len(rows))
            self._manifest_draw_list(list_body, rows, sel, slug, border)
            self._manifest_draw_detail(detail_body, rows[sel])
        self._ui_footer(panel, self._MANIFEST_HINT)

    def _manifest_draw_reason(self, reason, cx, cw, strip_y, y) -> int:
        """Why the menu opened on its tab, beside the strip when it fits
        there, else under it (as the cook menu says its reason). Returns the
        y the panes start at."""
        rf = get_font('body', 16)
        pip_w = S(16)
        chip_h = S(30) if kit_on('chip') else S(25)
        strip_end = getattr(self, '_tab_strip_end_x', cx)
        if cx + cw - strip_end - S(20) >= pip_w + rf.size(reason)[0]:
            rx = cx + cw - pip_w - rf.size(reason)[0]
            ry = strip_y + (chip_h - rf.get_height()) // 2
            lines = [reason]
        else:
            rx, ry = cx, y - S(6)
            lines = self._wrap_text(display_text(reason), rf, cw - pip_w) or ['']
            y += len(lines) * (rf.get_height() + S(2)) + S(4)
        pc = (rx + S(6), ry + rf.get_height() // 2)
        pygame.draw.circle(self.screen, KT.VOID, pc, max(3, S(4)) + 1)
        pygame.draw.circle(self.screen, KT.GOLD_HI, pc, max(3, S(4)))
        col = self._mf_ink(FP.SUCCESS_TEXT)
        for i, ln in enumerate(lines):
            self.screen.blit(rf.render(ln, True, col),
                             (rx + pip_w, ry + i * (rf.get_height() + S(2))))
        return y

    def _manifest_list_layout(self, rows, slug, width, height):
        """The list in ``width`` x ``height``: the names' size (20, 18, then
        16 px, the largest at which every row fits), each row's height and
        words, whether it scrolls. Cached until the menu opens again."""
        key = (slug, int(width), int(height))
        cache = getattr(self, '_mf_layout_cache', None)
        if cache is None:
            cache = self._mf_layout_cache = {}
        if key in cache:
            return cache[key]
        det_f = get_font('body', 16)
        chip_f = get_font('body', 16, bold=True)
        well = int(self.MENU_ICON_SIZE) + S(8)
        text_x = S(8) + well + S(10)
        chip_w = chip_f.size("Weak!")[0] + S(18)

        def measure(row_w, size, limit=None):
            name_f = get_font('body', size)
            hs, words, total = [], [], 0
            for row in rows:
                name_w = row_w - text_x - (chip_w + S(20) if row['weak'] else S(12))
                names = self._wrap_text(display_text(row['name']), name_f, name_w) or ['']
                det = self._wrap_text(display_text(manifest.row_line(row)), det_f,
                                      row_w - text_x - S(12))[:2]
                body = (max(len(names) * name_f.get_height() + S(4), S(28))
                        + len(det) * (det_f.get_height() + S(1)))
                h = max(body + S(16), well + S(14)) + S(6)
                hs.append(h)
                words.append((names, det, name_f, chip_w))
                total += h
                if limit is not None and total > limit:
                    return None
            return hs, words

        scroll = False
        got = None
        for size in (20, 18, 16):
            got = measure(width, size, limit=height)
            if got is not None:
                break
        if got is None:
            # Shrunk as far as it goes: the list scrolls, a strip at the
            # right for the bar and a line at the foot for "4-9 of 20".
            scroll = True
            got = measure(width - S(14), 16)
        hs, words = got
        out = {'heights': hs, 'words': words, 'scroll': scroll,
               'row_w': width - (S(14) if scroll else 0),
               'avail': height - (S(28) if scroll else 0)}
        cache[key] = out
        return out

    def _manifest_draw_list(self, body, rows, sel, slug, border):
        import cook_menu
        lay = self._manifest_list_layout(rows, slug, body.w, body.h)
        hs, words = lay['heights'], lay['words']
        start, end = cook_menu.window(hs, sel, lay['avail'])
        y = body.y
        for i in range(start, end):
            if y + hs[i] > body.y + lay['avail'] and i != sel:
                break
            self._manifest_draw_row(pygame.Rect(body.x, y, lay['row_w'], hs[i] - S(6)),
                                    rows[i], words[i], i == sel)
            y += hs[i]
        if lay['scroll']:
            tag = f"{start + 1}-{end} of {len(rows)}"
            tf = get_font('body', 16)
            ts = tf.render(tag, True, self._mf_ink(KT.TEXT_DIM))
            self.screen.blit(ts, (body.right - ts.get_width() - S(4),
                                  body.bottom - ts.get_height() - S(4)))
            self._ui_scrollbar(pygame.Rect(body.x + lay['row_w'], body.y, S(12),
                                           lay['avail'] - S(6)),
                               start, len(rows), max(1, end - start), color=border)

    def _manifest_draw_row(self, rect, row, words, selected):
        """One kind: its picture, its name, its level and bite type, and a
        "Weak!" chip when a known foe in view is weak to its bite."""
        names, det, name_f, chip_w = words
        self._ui_row(rect, selected, fill=(34, 43, 84) if selected else (18, 22, 40),
                     border=FP.GOLD if selected else FP.GOLD_DARK)
        isz = int(self.MENU_ICON_SIZE)
        well = pygame.Rect(rect.x + S(8), rect.y + (rect.h - isz - S(8)) // 2,
                           isz + S(8), isz + S(8))
        self._ui_well(well)
        icon = self._manifest_icon(row['kind'], isz)
        if icon is not None:
            self.screen.blit(icon, (well.x + S(4), well.y + S(4)))
        top = rect.y + S(8)
        if row['weak']:
            cr = pygame.Rect(rect.right - chip_w - S(10), top, chip_w, S(26))
            if not ui_theme.draw_piece(self.screen, 'chip', cr):
                pygame.draw.rect(self.screen, FP.MIDNIGHT, cr, border_radius=4)
                pygame.draw.rect(self.screen, FP.GOLD_DARK, cr, 1, border_radius=4)
            cf = get_font('body', 16, bold=True)
            cs = cf.render("Weak!", True, readable(FP.SUCCESS_TEXT, KT.RAISED))
            self.screen.blit(cs, (cr.centerx - cs.get_width() // 2,
                                  cr.centery - cs.get_height() // 2))
        tx = well.right + S(10)
        ncol = self._ui_row_text(FP.GOLD_PALE, selected)
        dcol = self._ui_row_text(KT.TEXT_DIM, selected)
        df = get_font('body', 16)
        ty = top
        for ln in names:
            self.screen.blit(name_f.render(ln, True, ncol), (tx, ty))
            ty += name_f.get_height()
        ty += S(4)
        for ln in det:
            self.screen.blit(df.render(ln, True, dcol), (tx, ty))
            ty += df.get_height() + S(1)

    # (plate px, font px): the largest picture and type that let it all fit.
    _MANIFEST_DETAIL_LADDER = ((192, 18), (160, 18), (128, 18), (128, 16), (96, 16), (64, 16))

    def _manifest_detail_plan(self, rect, row):
        """How the chosen kind's pane is laid out in ``rect``. Cached until
        the menu opens again."""
        key = ('detail', row['kind'], rect.w, rect.h)
        cache = getattr(self, '_mf_layout_cache', None)
        if cache is None:
            cache = self._mf_layout_cache = {}
        if key in cache:
            return cache[key]
        ink = self._mf_ink
        stat = manifest.stat_value(self.player)
        pad, gap = S(self._LORE_PLATE_PAD), S(10)
        plan = None
        for want, size in self._MANIFEST_DETAIL_LADDER:
            f = get_font('body', size)
            fb = get_font('body', size, bold=True)

            def bh(lines, w, _f=f):
                return self._menu_block_height(lines, w, FP.BODY_TEXT, _f) if lines else 0
            head = [(row['name'], ink(FP.GOLD_PALE), get_font('heading', 22))]
            facts = [(f"{k}: {v}", ink(FP.BODY_TEXT), f) for k, v in manifest.detail_lines(row)]
            below = []
            if row['strong_against']:
                below.append((f"Strong against {manifest.join_names(row['strong_against'])}",
                              ink(FP.SUCCESS_TEXT), fb))
            if row['resisted_by']:
                below.append((f"Resisted by {manifest.join_names(row['resisted_by'])}",
                              ink(FP.WARNING_TEXT), fb))
            below += [("How Long It Lasts", ink(FP.GOLD_BRIGHT), fb),
                      (manifest.duration_line(stat), ink(FP.BODY_TEXT), f),
                      (f"The AI questions climb, up to {manifest.max_chain()}. "
                       "None right and the page smudges.", ink(FP.FADED_TEXT), f)]
            action = [('__key__', 'Enter', "Draw it: a short-lived ally beside you.")]
            plate = lore_art.plate('monster', row['kind'], min(S(want), int(rect.w * 0.5)))
            ph = plate.get_height() + 2 * pad if plate is not None else 0
            bw = rect.w - (plate.get_width() + 2 * pad + gap if plate is not None else 0)
            top_h = max(ph, bh(facts, bw))
            total = bh(head, rect.w) + top_h + gap + bh(below, rect.w) + bh(action, rect.w)
            plan = {'font': f, 'head': head, 'plate': plate, 'bw': bw, 'facts': facts,
                    'top_h': top_h, 'below': below, 'action': action}
            if total <= rect.h:
                break
        cache[key] = plan
        return plan

    def _manifest_draw_detail(self, rect, row):
        """The chosen kind: its name; its picture large in its framed well
        (no art, no picture: the Bestiary's rule); beside it its level,
        attack type, health, bite and whether it is drawn from memory or
        sight; what it is strong against in view; how long it lasts; Enter's
        action."""
        plan = self._manifest_detail_plan(rect, row)
        f = plan['font']
        gap = S(10)
        pad = S(self._LORE_PLATE_PAD)

        def block(lines, y):
            if not lines or y >= rect.bottom:
                return y
            self._menu_more_cue = ' '
            return self._menu_draw_text_block(lines, pygame.Rect(rect.x, y, rect.w, rect.bottom - y),
                                              default_font=f)
        y = block(plan['head'], rect.y)
        sx = rect.x
        plate = plan['plate']
        if plate is not None:
            well = pygame.Rect(rect.x, y, plate.get_width() + 2 * pad, plate.get_height() + 2 * pad)
            self._draw_plate_well(plate, well)
            sx = well.right + gap
        self._menu_more_cue = ' '
        self._menu_draw_text_block(plan['facts'], pygame.Rect(sx, y, plan['bw'],
                                                              max(0, rect.bottom - y)),
                                   default_font=f)
        y += plan['top_h'] + gap
        y = block(plan['below'], y)
        block(plan['action'], y)
        self._menu_more_cue = None
