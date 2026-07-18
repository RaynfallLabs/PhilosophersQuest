import pygame

# FANTASY: Import theme helpers from the central fantasy_ui module
from fantasy_ui import FP, get_font, ITEM_COLOR
from hud_context import active_power_rows, visible_context_rows

LEFT_SIDEBAR_W = 248
SIDEBAR_W = 330

# FANTASY: Rich fantasy-palette message colors
_MSG_COLORS = {
    'info':    FP.BODY_TEXT,
    'success': FP.SUCCESS_TEXT,
    'warning': FP.WARNING_TEXT,
    'danger':  FP.DANGER_TEXT,
    'loot':    FP.LOOT_TEXT,
}

# FANTASY: Use ITEM_COLOR from fantasy_ui instead of local definition
_IC_COLOR = ITEM_COLOR


class MessageLog:
    MAX = 60

    def __init__(self):
        self.entries: list[tuple[str, str]] = []
        self._font = get_font('body', 20)

    def add(self, text: str, msg_type: str = 'info'):
        self.entries.append((text, msg_type))
        if len(self.entries) > self.MAX:
            self.entries.pop(0)

    @staticmethod
    def _wrap(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
        """Word-wrap text to fit within max_w pixels."""
        words = text.split()
        lines = []
        cur = ''
        for word in words:
            test = (cur + ' ' + word).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or ['']

    def draw(self, screen: pygame.Surface, x: int, y: int, w: int, h: int):
        # FANTASY: Midnight background + gold-dark top border
        pygame.draw.rect(screen, FP.MIDNIGHT, (x, y, w, h))
        pygame.draw.line(screen, FP.GOLD_DARK, (x, y), (x + w, y), 1)

        line_h = 26
        max_lines = (h - 8) // line_h
        text_w = w - 16  # 8px padding each side

        # Pre-wrap all entries into display lines (text, msg_type)
        all_lines: list[tuple[str, str]] = []
        for text, msg_type in self.entries:
            wrapped = self._wrap(text, self._font, text_w)
            for wl in wrapped:
                all_lines.append((wl, msg_type))

        visible = all_lines[-max_lines:]

        for i, (text, msg_type) in enumerate(visible):
            age = len(visible) - 1 - i
            base = _MSG_COLORS.get(msg_type, _MSG_COLORS['info'])
            fade = max(0.35, 1.0 - age * 0.09)
            color = tuple(int(c * fade) for c in base)
            surf = self._font.render(text, True, color)
            screen.blit(surf, (x + 8, y + 4 + i * line_h))


class Sidebar:
    PAD = 10
    SECTION_GAP = 8

    @staticmethod
    def _cap(name: str) -> str:
        """Capitalize the first letter of each space-separated word."""
        return ' '.join(w[:1].upper() + w[1:] for w in name.split())

    @staticmethod
    def _fit(font: pygame.font.Font, text: str, max_px: int) -> str:
        """Truncate text with ellipsis so it fits within max_px pixels."""
        if font.size(text)[0] <= max_px:
            return text
        while len(text) > 1 and font.size(text + '\u2026')[0] > max_px:
            text = text[:-1]
        return text + '\u2026'

    def __init__(self, screen: pygame.Surface, x: int):
        self.screen = screen
        self.left_x = 0
        self.right_x = x
        self.x = x
        self.w = SIDEBAR_W
        # FANTASY: Grimoire font set -- larger for readability
        self._fsm   = get_font('body', 18)
        self._fbold = get_font('body', 18, bold=True)
        self._fhd   = get_font('heading', 17)

    def draw(self, player, dungeon_level: int, turn_count: int, gold: int = 0,
             *, player_name: str = "Adventurer", visible_monsters=(),
             visible_items=(), visible_tiles=None, secret_build=None,
             heavenly_host_active: bool = False):
        h = self.screen.get_height()
        visible_tiles = visible_tiles or set()

        self._set_pane(self.left_x, LEFT_SIDEBAR_W)
        self._pane_bg(h, edge="right")
        y = self.PAD
        y = self._identity(player_name, dungeon_level, turn_count, y)
        y = self._vitals(player, y)
        y = self._attributes(player, y)
        y = self._derived(player, dungeon_level, gold, y)
        self._effects(player, y)

        self._set_pane(self.right_x, SIDEBAR_W)
        self._pane_bg(h, edge="left")
        y = self.PAD
        y = self._powers(player, y, secret_build=secret_build,
                         heavenly_host_active=heavenly_host_active)
        self._in_sight(player, visible_monsters, visible_items, visible_tiles,
                       dungeon_level, y)

    # ------------------------------------------------------------------
    # Section helpers
    # ------------------------------------------------------------------

    def _set_pane(self, x: int, w: int):
        self.x = x
        self.w = w

    def _pane_bg(self, h: int, *, edge: str):
        pygame.draw.rect(self.screen, FP.MIDNIGHT, (self.x, 0, self.w, h))
        lx = self.x if edge == "left" else self.x + self.w - 1
        pygame.draw.line(self.screen, FP.GOLD_DARK, (lx, 0), (lx, h), 2)

    def _header(self, text: str, y: int) -> int:
        """Section header — matches the panel-modal draw_header_bar vocabulary.

        Two-tone midnight strip + gold accent line + side diamond ornaments.
        Sidebar now reads as a sibling of every modal in the game, rather
        than a lighter-weight cousin (per audit beauty-sidebar-status-flat).
        """
        from fantasy_ui import draw_header_bar
        rect = (self.x + self.PAD, y, self.w - self.PAD * 2, 24)
        draw_header_bar(self.screen, rect, text=text,
                        font=self._fhd, text_color=FP.GOLD_BRIGHT,
                        accent=FP.GOLD_DARK)
        return y + 26

    def _bar(self, y: int, label: str, val: int, max_val: int,
             bar_color: tuple) -> int:
        # FANTASY: Faded text label
        self.screen.blit(
            self._fsm.render(label, True, FP.FADED_TEXT),
            (self.x + self.PAD, y)
        )
        readout_w = 100
        bx = self.x + self.PAD + 26
        bw = self.w - self.PAD * 2 - 26 - readout_w
        bh = 10
        ratio = max(0.0, min(1.0, val / max(1, max_val)))

        # FANTASY: Dark bar background
        pygame.draw.rect(self.screen, (18, 18, 30),
                         (bx, y + 1, bw, bh), border_radius=3)
        if ratio > 0:
            pygame.draw.rect(self.screen, bar_color,
                             (bx, y + 1, max(2, int(bw * ratio)), bh),
                             border_radius=3)

        # FANTASY: Readout right-aligned inside reserved space
        rsurf = self._fsm.render(f"{val}/{max_val}", True, FP.BODY_TEXT)
        self.screen.blit(rsurf, (bx + bw + readout_w - rsurf.get_width(), y))
        return y + 22

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _identity(self, player_name: str, dungeon_level: int, turn_count: int, y: int) -> int:
        y = self._header("CHARACTER", y)
        name = self._fit(self._fbold, player_name or "Adventurer", self.w - self.PAD * 2)
        self.screen.blit(self._fbold.render(name, True, FP.GOLD_PALE), (self.x + self.PAD, y))
        y += 23
        line = f"Floor {dungeon_level}   Turn {turn_count}"
        self.screen.blit(self._fsm.render(self._fit(self._fsm, line, self.w - self.PAD * 2),
                                          True, FP.FADED_TEXT),
                         (self.x + self.PAD, y))
        return y + 24 + self.SECTION_GAP

    def _vitals(self, player, y: int) -> int:
        y = self._header("VITALS", y)
        sp_r = player.sp / max(1, player.max_sp)
        sp_col = (
            FP.SP_GREEN if sp_r > 0.50 else
            FP.SP_AMBER if sp_r > 0.25 else
            FP.SP_RED
        )
        y = self._bar(y, "HP", player.hp, player.max_hp, FP.HP_RED)
        y = self._bar(y, "MP", player.mp, player.max_mp, FP.MP_BLUE)
        y = self._bar(y, "SP", player.sp, player.max_sp, sp_col)
        return y + self.SECTION_GAP

    def _attributes(self, player, y: int) -> int:
        y = self._header("ATTRIBUTES", y)
        attrs = [
            ('STR', player.STR), ('CON', player.CON),
            ('DEX', player.DEX), ('INT', player.INT),
            ('WIS', player.WIS), ('PER', player.PER),
        ]
        col_w = (self.w - self.PAD * 2) // 3
        for i, (name, val) in enumerate(attrs):
            ax = self.x + self.PAD + (i % 3) * col_w
            ay = y + (i // 3) * 24
            # FANTASY: FADED_TEXT label color
            self.screen.blit(
                self._fsm.render(f"{name}:", True, FP.FADED_TEXT), (ax, ay)
            )
            # FANTASY: Gold for high, body text for mid, danger for low
            vc = FP.GOLD_BRIGHT if val > 12 else FP.BODY_TEXT if val >= 10 else FP.DANGER_TEXT
            self.screen.blit(self._fbold.render(str(val), True, vc), (ax + 46, ay))
        return y + 2 * 24 + self.SECTION_GAP

    def _derived(self, player, dungeon_level: int, gold: int, y: int) -> int:
        y = self._header("DERIVED", y)
        ac = player.get_ac()
        ac_color = FP.SUCCESS_TEXT if ac <= 0 else FP.SP_GREEN if ac <= 5 else FP.WARNING_TEXT
        wt = player.get_current_weight()
        lim = player.get_carry_limit()
        wt_color = FP.WARNING_TEXT if wt > lim * 0.75 else FP.SUCCESS_TEXT
        spell_count = len(getattr(player, 'known_spells', {}))
        metrics = [
            (f"AC {ac}", ac_color),
            (f"Gold {gold:,}", FP.GOLD_PALE),
            (f"Sight {player.get_sight_radius()}", FP.BODY_TEXT),
            (f"Timer {player.get_quiz_timer('math')}s", FP.WARNING_TEXT),
            (f"Wt {wt:.0f}/{lim}", wt_color),
            (f"Picks {getattr(player, 'lockpick_charges', 0)}", FP.AMBER_ACCENT),
            (f"Spells {spell_count}", FP.MP_BLUE_TEXT),
            (f"Depth {dungeon_level}", FP.BODY_TEXT),
        ]
        metric_w = (self.w - self.PAD * 2) // 2
        for i, (label, color) in enumerate(metrics):
            ax = self.x + self.PAD + (i % 2) * metric_w
            ay = y + (i // 2) * 22
            self.screen.blit(self._fsm.render(self._fit(self._fsm, label, metric_w - 8),
                                              True, color), (ax, ay))
        return y + ((len(metrics) + 1) // 2) * 22 + self.SECTION_GAP

    def _effect_chip(self, x: int, y: int, w: int, label: str, color: tuple) -> None:
        rect = pygame.Rect(x, y, w, 21)
        pygame.draw.rect(self.screen, (22, 26, 48), rect, border_radius=4)
        pygame.draw.rect(self.screen, color, (rect.x, rect.y, 3, rect.h), border_radius=2)
        text = self._fit(self._fbold, label, w - 10)
        self.screen.blit(self._fbold.render(text, True, color), (x + 7, y + 1))

    def _effect_label(self, display_name: str, duration: int) -> str:
        if duration < 0:
            return display_name
        full = f"{display_name} {duration}"
        col_w = (self.w - self.PAD * 2 - 6) // 2
        if self._fbold.size(full)[0] <= col_w - 10:
            return full
        compact_names = {
            "Poisoned": "Pois",
            "Paralyzed": "Para",
            "Confused": "Conf",
            "Blessed": "Bless",
            "Cursed": "Curse",
            "Berserk": "Bersk",
            "Telepathy": "Tele",
        }
        return f"{compact_names.get(display_name, display_name[:5])} {duration}"

    def _effects(self, player, y: int) -> int:
        from status_effects import EFFECT_INFO
        y = self._header("EFFECTS", y)
        rows = []
        if any(getattr(i, 'id', '') == 'charmander_stuffie' for i in player.inventory):
            rows.append(("Fire Protect", FP.PASSIVE_FIRE))
        if any(getattr(i, 'id', '') == 'dreamspun_sketchbook' for i in player.inventory):
            rows.append(("Manifest", FP.PASSIVE_MANIFEST))
        if getattr(player, 'amulet_slot', None) and getattr(player.amulet_slot, 'id', '') == 'rands_heart':
            rows.append(("Death Ward", FP.PASSIVE_WARD))
        for eid, val in player.status_effects.items():
            if val == 0:
                continue
            info = EFFECT_INFO.get(eid)
            if not info:
                continue
            display_name, rgb, _ = info
            label = self._effect_label(display_name, val)
            rows.append((label, rgb))
        if not rows:
            self.screen.blit(self._fsm.render("(none)", True, FP.SLOT_EMPTY),
                             (self.x + self.PAD, y))
            return y + 22 + self.SECTION_GAP

        col_w = (self.w - self.PAD * 2 - 6) // 2
        bottom = self.screen.get_height() - self.PAD
        for i, (label, color) in enumerate(rows):
            ay = y + (i // 2) * 24
            if ay + 21 > bottom:
                break
            ax = self.x + self.PAD + (i % 2) * (col_w + 6)
            self._effect_chip(ax, ay, col_w, label, color)
        return y + ((len(rows) + 1) // 2) * 24 + self.SECTION_GAP

    def _power_color(self, state: str) -> tuple:
        if state == "ready":
            return FP.SUCCESS_TEXT
        if state == "uses":
            return FP.MP_BLUE_TEXT
        return FP.WARNING_TEXT

    def _compact_row(self, y: int, label: str, meta: str, color: tuple,
                     *, label_color: tuple | None = None) -> int:
        row = pygame.Rect(self.x + self.PAD, y, self.w - self.PAD * 2, 24)
        pygame.draw.rect(self.screen, (18, 22, 42), row, border_radius=4)
        pygame.draw.rect(self.screen, color, (row.x, row.y, 4, row.h), border_radius=2)
        meta_w = min(88, max(50, self._fsm.size(meta)[0] + 8))
        self.screen.blit(self._fbold.render(self._fit(self._fbold, label, row.w - meta_w - 18),
                                            True, label_color or FP.BODY_TEXT),
                         (row.x + 10, row.y + 2))
        meta_surf = self._fbold.render(self._fit(self._fbold, meta, meta_w), True, color)
        self.screen.blit(meta_surf, (row.right - meta_surf.get_width() - 8, row.y + 2))
        return y + 27

    def _powers(self, player, y: int, *, secret_build=None,
                heavenly_host_active: bool = False) -> int:
        y = self._header("POWERS", y)
        rows = active_power_rows(player, secret_build=secret_build,
                                 heavenly_host_active=heavenly_host_active)
        max_rows = 8
        for row in rows[:max_rows]:
            y = self._compact_row(y, row.label, row.status, self._power_color(row.state))
        if len(rows) > max_rows:
            more = f"+{len(rows) - max_rows} more"
            self.screen.blit(self._fsm.render(more, True, FP.FADED_TEXT),
                             (self.x + self.PAD, y))
            y += 22
        return y + self.SECTION_GAP

    def _in_sight(self, player, visible_monsters, visible_items, visible_tiles,
                  dungeon_level: int, y: int) -> int:
        y = self._header("IN SIGHT", y)
        monsters, items = visible_context_rows(
            player, visible_monsters, visible_items, visible_tiles, dungeon_level,
            max_monsters=6, max_items=6,
        )
        bottom = self.screen.get_height() - self.PAD

        def section(title: str, rows, y: int) -> int:
            self.screen.blit(self._fbold.render(title, True, FP.GOLD_PALE),
                             (self.x + self.PAD, y))
            y += 22
            if not rows:
                self.screen.blit(self._fsm.render("(none)", True, FP.SLOT_EMPTY),
                                 (self.x + self.PAD, y))
                return y + 24
            for row in rows:
                if y + 24 > bottom:
                    return y
                y = self._compact_row(y, row.label, row.meta, row.color,
                                      label_color=row.color)
            return y + 8

        y = section("Enemies", monsters, y)
        if y + 44 <= bottom:
            y = section("Items", items, y)
        return y
