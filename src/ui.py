import pygame

import ui_theme
from ui_scale import px as S

# FANTASY: Import theme helpers from the central fantasy_ui module
from fantasy_ui import FP, ITEM_COLOR, KT, ScaledFont, contrast, display_text
from hud_context import active_power_rows, visible_context_rows

# Rail widths at UI scale 1 (1280x720). On screen they are ``ui_scale.px``
# of these; layout.LEFT_SIDEBAR_W / layout.SIDEBAR_W hold the live values
# (_genart/ui/SCALE_PLAN.md).
LEFT_SIDEBAR_W = 248
SIDEBAR_W = 330
# The rails' smallest share of their width in compact (below 1280x720): their
# text stays at the 16 px floor, so they cannot shrink as fast as the window.
RAIL_MIN = 0.9

def _rail_w(base: int) -> int:
    """A rail's width on screen: ``px(base)``, but in compact (below
    1280x720) never under ``layout.RAIL_MIN`` of ``base`` -- the same rule
    as ``layout.LEFT_SIDEBAR_W`` / ``SIDEBAR_W``."""
    import ui_scale
    return int(base * max(ui_scale.get(), RAIL_MIN) + 0.5)


# Message-log tag colours: the design-rule ``log.*`` tokens
# (DESIGN_RULES.md 2.1 / 2.2, KT.LOG). Each clears 8:1 on the log body.
_MSG_COLORS = dict(KT.LOG)

# The log body colour, and the contrast floor every line keeps however old
# it is (DESIGN_RULES 3: "faded" text is a colour blend toward the
# background, floored at 4.5:1; 4.6 keeps a little slack for rounding).
LOG_BG = FP.MIDNIGHT
LOG_FADE_FLOOR = 4.6
_LOG_FADE_STEP = 0.07          # per line of age, toward the background
_line_color_cache: dict = {}


def carry_state(player) -> tuple[float, int, str]:
    """(weight carried, limit, state) where state is '' / 'Burdened' /
    'Over Limit'. Worn gear and the pack both count (Player.get_current_weight).
    One reading for the sidebar, the character sheet and the menus."""
    wt = float(player.get_current_weight())
    lim = int(player.get_carry_limit())
    share = float(getattr(player, 'BURDENED_SHARE', 0.75))
    if wt > lim:
        return wt, lim, 'Over Limit'
    if wt > lim * share:
        return wt, lim, 'Burdened'
    return wt, lim, ''


def carry_color(state: str) -> tuple:
    return (FP.DANGER_TEXT if state == 'Over Limit'
            else FP.WARNING_TEXT if state else FP.SUCCESS_TEXT)


def log_line_color(msg_type: str, age: int) -> tuple:
    """Colour of a log line of ``msg_type`` that is ``age`` lines older than
    the newest. Older lines blend toward ``LOG_BG`` but never below
    ``LOG_FADE_FLOOR``:1 against it."""
    key = (msg_type, age)
    got = _line_color_cache.get(key)
    if got is not None:
        return got
    base = _MSG_COLORS.get(msg_type, _MSG_COLORS['info'])
    k = max(0.0, 1.0 - age * _LOG_FADE_STEP)

    def mix(t):
        return tuple(int(round(LOG_BG[j] + (base[j] - LOG_BG[j]) * t)) for j in range(3))
    col = mix(k)
    while contrast(col, LOG_BG) < LOG_FADE_FLOOR and k < 1.0:
        k = min(1.0, k + 0.01)
        col = mix(k)
    _line_color_cache[key] = col
    return col

# FANTASY: Use ITEM_COLOR from fantasy_ui instead of local definition
_IC_COLOR = ITEM_COLOR


class MessageLog:
    # Lines kept for the L history (bug bash 4 call 16; it was 60, about
    # one fight). Only the visible lines are drawn each frame.
    MAX = 500
    # Phase 3 (UI beautification 2026-10-04): line stride is derived from
    # font metrics so the log keeps up with font-size changes instead of
    # being pinned to a magic 26 px row. Spacing below is at UI scale 1 and
    # drawn as ui_scale.px() of it.
    LEADING = 6     # px of visual breathing room between lines
    PAD_X = 8       # px padding each side (inner text column)
    PAD_Y = 4       # px padding top (and symmetrically at the bottom)

    def __init__(self):
        self.entries: list[tuple[str, str]] = []
        # Wrap cache (2026-10-15, UI art foundation): the log used to re-wrap
        # all <=60 entries on every frame, the single largest per-frame cost
        # with a full log (FOUNDATION_REVIEW.md 2.2). ``_wrapped[i]`` is
        # ``(text, lines)``: the wrapped lines of ``entries[i]`` and the exact
        # string they were wrapped from (None = not wrapped yet), for the
        # (font, text width) in ``_wrap_key``. A different font or pane width
        # invalidates every entry (a UI-scale change is both). Each lookup also checks the cached string
        # is still the entry's text (an ``is`` test, then ``==``), so a
        # replaced ``entries`` list or an entry edited in place re-wraps
        # instead of drawing stale text (GROUNDWORK_REVIEW 7). Prefer
        # ``add`` / ``clear`` / ``replace`` over mutating ``entries``.
        self._wrapped: list[tuple[str, list[str]] | None] = []
        self._wrap_key: tuple | None = None

    # The log font at the current UI scale, fetched on use (a dict lookup)
    # so a resize cannot leave a stale font behind. An instance may still
    # assign its own font (non-data descriptor).
    _font = ScaledFont('body', 20)

    def add(self, text: str, msg_type: str = 'info'):
        self.entries.append((text, msg_type))
        self._wrapped.append(None)
        if len(self.entries) > self.MAX:
            self.entries.pop(0)
            self._wrapped.pop(0)

    def clear(self) -> None:
        self.entries = []
        self._wrapped = []

    def replace(self, entries) -> None:
        """Replace every entry (e.g. a restored log); the cache is reset."""
        self.entries = list(entries)[-self.MAX:]
        self._wrapped = [None] * len(self.entries)

    def _wrapped_lines(self, i: int, text_w: int) -> list[str]:
        """Wrapped lines of entry ``i`` at ``text_w``, from the cache."""
        font = self._font
        key = (font, text_w)
        if key != self._wrap_key or len(self._wrapped) != len(self.entries):
            # Font or pane width changed (resize), or ``entries`` changed
            # length behind add(): rebuild the cache's shape.
            self._wrap_key = key
            self._wrapped = [None] * len(self.entries)
        text = self.entries[i][0]
        got = self._wrapped[i]
        if got is not None and (got[0] is text or got[0] == text):
            return got[1]
        lines = self._wrap(display_text(text), font, text_w)
        self._wrapped[i] = (text, lines)
        return lines

    @staticmethod
    def _wrap(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
        """Word-wrap text to fit within max_w pixels.

        Phase 3 UI beautification: delegates to the shared
        ``text_layout.wrap_lines`` helper, which also breaks oversized
        tokens by character — so a 60-char no-space magic-item name in a
        narrow log pane no longer overflows the right edge.
        """
        from text_layout import wrap_lines
        return wrap_lines(text, max_w, font)

    def line_height(self) -> int:
        """Vertical stride between successive log rows.

        Derived from ``font.get_height()`` plus a fixed leading so the
        log tracks the current font metrics instead of a hardcoded 26 px
        value. Public (no leading underscore) so tests can assert that
        the stride responds to font changes without having to intercept
        the draw path.
        """
        return self._font.get_height() + S(self.LEADING)

    def draw(self, screen: pygame.Surface, x: int, y: int, w: int, h: int):
        # FANTASY: Midnight background + gold-dark top border
        pygame.draw.rect(screen, LOG_BG, (x, y, w, h))
        pygame.draw.line(screen, FP.GOLD_DARK, (x, y), (x + w, y), 1)

        font = self._font
        pad_x, pad_y = S(self.PAD_X), S(self.PAD_Y)
        line_h = self.line_height()
        available_h = h - pad_y * 2
        # Phase 3 zero-row guard: on a pane shorter than one text line
        # bail out BEFORE slicing ``messages[-0:]`` (which would select
        # the entire log instead of nothing).
        if line_h <= 0 or available_h < line_h:
            return
        max_lines = available_h // line_h
        if max_lines <= 0:
            return
        text_w = w - pad_x * 2

        # The newest ``max_lines`` display lines (text, msg_type), walking
        # back from the newest entry; wraps come from the cache.
        visible: list[tuple[str, str]] = []
        for i in range(len(self.entries) - 1, -1, -1):
            msg_type = self.entries[i][1]
            for wl in reversed(self._wrapped_lines(i, text_w)):
                visible.append((wl, msg_type))
            if len(visible) >= max_lines:
                break
        visible = visible[:max_lines]
        visible.reverse()

        for i, (text, msg_type) in enumerate(visible):
            age = len(visible) - 1 - i
            surf = font.render(text, True, log_line_color(msg_type, age))
            screen.blit(surf, (x + pad_x, y + pad_y + i * line_h))


class Sidebar:
    # Spacing at UI scale 1. Every length in this class goes through
    # ui_scale.px (``S``), so the rails grow with the window
    # (_genart/ui/SCALE_PLAN.md).
    PAD_BASE = 10
    SECTION_GAP_BASE = 8

    @property
    def PAD(self) -> int:
        return S(self.PAD_BASE)

    @property
    def SECTION_GAP(self) -> int:
        return S(self.SECTION_GAP_BASE)

    # FANTASY: Grimoire font set -- larger for readability. Fetched on use
    # (a dict lookup) so they always match the current UI scale.
    _fsm = ScaledFont('body', 18)
    _fbold = ScaledFont('body', 18, bold=True)
    _fhd = ScaledFont('heading', 17)

    @staticmethod
    def _cap(name: str) -> str:
        """Capitalize the first letter of each space-separated word."""
        return ' '.join(w[:1].upper() + w[1:] for w in name.split())

    @staticmethod
    def _fit(font: pygame.font.Font, text: str, max_px: int) -> str:
        """Truncate text with ellipsis so it fits within max_px pixels."""
        if font.size(text)[0] <= max_px:
            return text
        while len(text) > 1 and font.size(text + '…')[0] > max_px:
            text = text[:-1]
        return text + '…'

    def __init__(self, screen: pygame.Surface, x: int):
        self.screen = screen
        self.left_x = 0
        self.right_x = x
        self.x = x
        self.w = _rail_w(SIDEBAR_W)

    def draw(self, player, dungeon_level: int, turn_count: int, gold: int = 0,
             *, player_name: str = "Adventurer", visible_monsters=(),
             visible_items=(), visible_tiles=None, secret_build=None,
             heavenly_host_active: bool = False):
        h = self.screen.get_height()
        visible_tiles = visible_tiles or set()

        self._set_pane(self.left_x, _rail_w(LEFT_SIDEBAR_W))
        self._pane_bg(h, edge="right")
        y = self.PAD
        y = self._identity(player_name, dungeon_level, turn_count, y)
        y = self._vitals(player, y)
        y = self._attributes(player, y)
        y = self._derived(player, dungeon_level, gold, y)
        self._effects(player, y)

        self._set_pane(self.right_x, _rail_w(SIDEBAR_W))
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
        rect = (self.x + self.PAD, y, self.w - self.PAD * 2, S(24))
        draw_header_bar(self.screen, rect, text=text,
                        font=self._fhd, text_color=FP.GOLD_BRIGHT,
                        accent=FP.GOLD_DARK, kind='header_small')
        return y + S(26)

    # Kit icons beside the sidebar's stat labels (assets/ui/icons). They
    # are drawn only when the art kit is loaded; without it the labels sit
    # where they always did.
    _STAT_ICONS = {
        'HP': 'stat_hp', 'MP': 'stat_mp', 'SP': 'stat_sp',
        'STR': 'stat_str', 'CON': 'stat_con', 'DEX': 'stat_dex',
        'INT': 'stat_int', 'WIS': 'stat_wis', 'PER': 'stat_per',
        'AC': 'stat_ac', 'Gold': 'stat_gold', 'Sight': 'stat_sight',
        'Clock': 'stat_clock', 'Wt': 'stat_weight', 'Spells': 'stat_spells',
    }

    # Derived stats whose icon stands for the word (coin, hourglass). The
    # sack ('Wt') is drawn beside the full-width "Carrying" line instead.
    _ICON_IS_LABEL = frozenset({'Gold', 'Clock'})

    @staticmethod
    def _icon_size() -> int:
        return S(18)

    def _icon(self, name: str, x: int, y: int, line_h: int) -> int:
        """Blit kit icon ``name`` at x, centred on a ``line_h`` text line.
        Returns the x where the label continues (x when there is no art)."""
        sz = self._icon_size()
        if ui_theme.draw_icon(self.screen, name, (x, y + (line_h - sz) // 2, sz, sz)):
            return x + sz + S(4)
        return x

    def _bar(self, y: int, label: str, val: int, max_val: int,
             bar_color: tuple) -> int:
        lx = self._icon(self._STAT_ICONS.get(label, ''), self.x + self.PAD, y,
                        self._fsm.get_height())
        # FANTASY: Faded text label
        self.screen.blit(
            self._fsm.render(label, True, FP.FADED_TEXT),
            (lx, y)
        )
        readout_w = S(100)
        bx = lx + S(26)
        bw = self.x + self.w - self.PAD - readout_w - bx
        bh = S(10)
        ratio = max(0.0, min(1.0, val / max(1, max_val)))
        by = y + S(1)

        track = pygame.Rect(bx, by + S(1) - S(2), bw, bh + S(4))
        if ui_theme.draw_piece(self.screen, 'bar_track', track):
            inner = track.inflate(-S(4), -S(4))
            if ratio > 0:
                self.screen.fill(bar_color, (inner.x, inner.y,
                                             max(2, int(inner.w * ratio)), inner.h))
            ui_theme.draw_piece(self.screen, 'bar_frame', track, body=False)
        else:
            # FANTASY: Dark bar background
            pygame.draw.rect(self.screen, (18, 18, 30),
                             (bx, by, bw, bh), border_radius=3)
            if ratio > 0:
                pygame.draw.rect(self.screen, bar_color,
                                 (bx, by, max(2, int(bw * ratio)), bh),
                                 border_radius=3)

        # FANTASY: Readout right-aligned inside reserved space
        rsurf = self._fsm.render(f"{val}/{max_val}", True, FP.BODY_TEXT)
        self.screen.blit(rsurf, (bx + bw + readout_w - rsurf.get_width(), y))
        return y + S(22)

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _identity(self, player_name: str, dungeon_level: int, turn_count: int, y: int) -> int:
        y = self._header("CHARACTER", y)
        name = self._fit(self._fbold, player_name or "Adventurer", self.w - self.PAD * 2)
        self.screen.blit(self._fbold.render(name, True, FP.GOLD_PALE), (self.x + self.PAD, y))
        y += S(23)
        line = f"Floor {dungeon_level}   Turn {turn_count}"
        self.screen.blit(self._fsm.render(self._fit(self._fsm, line, self.w - self.PAD * 2),
                                          True, FP.FADED_TEXT),
                         (self.x + self.PAD, y))
        return y + S(24) + self.SECTION_GAP

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
        # Phase 3 (UI beautification 2026-10-04): 2-col × 3-row.
        # Column 1 = STR / CON / DEX, Column 2 = INT / WIS / PER.
        # The attribute list is interleaved (col1_row0, col2_row0,
        # col1_row1, ...) so `i % 2` picks the column and `i // 2`
        # picks the row for the layout math below.
        attrs = [
            ('STR', player.STR), ('INT', player.INT),  # row 0
            ('CON', player.CON), ('WIS', player.WIS),  # row 1
            ('DEX', player.DEX), ('PER', player.PER),  # row 2
        ]
        inner_w = self.w - self.PAD * 2
        gutter = S(8)  # keep columns visually separated
        col_w = (inner_w - gutter) // 2
        row_h = S(24)
        for i, (name, val) in enumerate(attrs):
            col = i % 2
            row = i // 2
            cell_x = self.x + self.PAD + col * (col_w + gutter)
            ay = y + row * row_h
            ax = self._icon(self._STAT_ICONS[name], cell_x, ay, self._fsm.get_height())
            # FANTASY: FADED_TEXT label color on the left of the cell.
            label_surf = self._fsm.render(f"{name}:", True, FP.FADED_TEXT)
            self.screen.blit(label_surf, (ax, ay))
            # FANTASY: Gold for high, body text for mid, danger for low.
            vc = FP.GOLD_BRIGHT if val > 12 else FP.BODY_TEXT if val >= 10 else FP.DANGER_TEXT
            val_surf = self._fbold.render(str(val), True, vc)
            # Right-align value inside the cell with a 2 px safety gap, so
            # 3-digit stats never crash into the next column (or the pane
            # midpoint divider between the two columns).
            vx = cell_x + col_w - val_surf.get_width() - S(2)
            # Guard against negative offsets if a cell ever shrinks below
            # the label width — in that case fall back to a nudge past the
            # label rather than overlapping it.
            min_vx = ax + label_surf.get_width() + S(4)
            if vx < min_vx:
                vx = min_vx
            self.screen.blit(val_surf, (vx, ay))
        return y + 3 * row_h + self.SECTION_GAP

    def _derived(self, player, dungeon_level: int, gold: int, y: int) -> int:
        y = self._header("DERIVED", y)
        ac = player.get_ac()
        ac_color = FP.SUCCESS_TEXT if ac <= 0 else FP.SP_GREEN if ac <= 5 else FP.WARNING_TEXT
        spell_count = len(getattr(player, 'known_spells', {}))
        # Phase 3 (UI beautification 2026-10-04): "Depth" removed — the
        # CHARACTER identity section already prints "Floor {dungeon_level}"
        # as the sole dungeon-level readout; a second "Depth" line here
        # was a dupe. `dungeon_level` is kept in the signature in case a
        # future metric wants it.
        metrics = [
            (f"AC {ac}", ac_color),
            (f"Gold {gold:,}", FP.GOLD_PALE),
            (f"Sight {player.get_sight_radius()}", FP.BODY_TEXT),
            # The clock the next fight will really get. Gold when something
            # is lengthening it (haste, a blessing, the Guiding Hand), red
            # when something is shortening it.
            (f"Clock {player.combat_clock()}s",
             FP.GOLD_BRIGHT if player.combat_clock() > player.plain_clock()
             else FP.DANGER_TEXT if player.combat_clock() < player.plain_clock()
             else FP.WARNING_TEXT),
            (f"Spells {spell_count}", FP.MP_BLUE_TEXT),
        ]
        metric_w = (self.w - self.PAD * 2) // 2
        for i, (label, color) in enumerate(metrics):
            cell_x = self.x + self.PAD + (i % 2) * metric_w
            ay = y + (i // 2) * S(22)
            word = label.split(' ')[0]
            ax = self._icon(self._STAT_ICONS.get(word, ''), cell_x, ay,
                            self._fsm.get_height())
            if ax != cell_x and word in self._ICON_IS_LABEL:
                # the painted icon names the stat; its value says the rest
                # ("1,234", "12s"), so the cell never truncates
                label = label[len(word) + 1:]
            self.screen.blit(self._fsm.render(
                self._fit(self._fsm, label, metric_w - S(8) - (ax - cell_x)),
                True, color), (ax, ay))
        y += ((len(metrics) + 1) // 2) * S(22)
        y = self._carrying(player, y)
        return y + self.SECTION_GAP

    @staticmethod
    def carry_state(player) -> tuple[float, int, str]:
        return carry_state(player)

    def _carrying(self, player, y: int) -> int:
        """One full-width line, 'Carrying 43 / 100': green, amber when
        Burdened (the load slows the hero's steps), red past the limit."""
        wt, lim, state = self.carry_state(player)
        cell_x = self.x + self.PAD
        ax = self._icon(self._STAT_ICONS['Wt'], cell_x, y, self._fsm.get_height())
        color = (FP.DANGER_TEXT if state == 'Over Limit'
                 else FP.WARNING_TEXT if state else FP.SUCCESS_TEXT)
        room = self.x + self.w - self.PAD - ax
        label = f"Carrying {wt:.0f} / {lim}"
        surf = self._fsm.render(self._fit(self._fsm, label, room), True, color)
        self.screen.blit(surf, (ax, y))
        if state:
            mx = ax + surf.get_width() + S(8)
            # Beside the number when it fits; the EFFECTS list always shows
            # it as a chip as well (see _effects), so a narrow rail loses nothing.
            if self._fbold.size(state)[0] <= self.x + self.w - self.PAD - mx:
                self.screen.blit(self._fbold.render(state, True, color), (mx, y))
        return y + S(22)

    _fchip_small = ScaledFont('body', 16, bold=True)

    def _effect_chip(self, x: int, y: int, w: int, label: str, color: tuple,
                     effect_id: str | None = None) -> None:
        rect = pygame.Rect(x, y, w, S(21))
        pygame.draw.rect(self.screen, (22, 26, 48), rect, border_radius=4)
        pygame.draw.rect(self.screen, color, (rect.x, rect.y, S(3), rect.h), border_radius=2)
        tx = x + S(7)
        if effect_id:
            sz = S(16)
            if ui_theme.draw_icon(self.screen, f"fx_{effect_id}",
                                  (x + S(6), y + (rect.h - sz) // 2, sz, sz)):
                tx = x + S(6) + sz + S(4)
        # The whole label always shows (a child must see how many turns are
        # left): one chip per row, and a 16 px step-down before any ellipsis.
        room = x + w - S(3) - tx
        font = self._fbold
        if font.size(label)[0] > room:
            font = self._fchip_small
        text = self._fit(font, label, room)
        self.screen.blit(font.render(text, True, color),
                         (tx, y + (rect.h - font.get_height()) // 2))

    @staticmethod
    def _effect_label(display_name: str, duration: int, icon: bool = False) -> str:
        """The chip text: the effect's full name and its turns left. Never
        abbreviated ("See I", "Pois" and "Empow" were unreadable)."""
        if duration < 0:
            return display_name
        return f"{display_name} {duration}"

    def _effects(self, player, y: int) -> int:
        from status_effects import EFFECT_INFO
        y = self._header("EFFECTS", y)
        rows = []
        _wt, _lim, carry = self.carry_state(player)
        if carry:
            rows.append((carry, FP.DANGER_TEXT if carry == 'Over Limit' else FP.WARNING_TEXT, None))
        if any(getattr(i, 'id', '') == 'charmander_stuffie' for i in player.inventory):
            rows.append(("Fire Protect", FP.PASSIVE_FIRE, None))
        if any(getattr(i, 'id', '') == 'dreamspun_sketchbook' for i in player.inventory):
            rows.append(("Manifest", FP.PASSIVE_MANIFEST, None))
        if getattr(player, 'amulet_slot', None) and getattr(player.amulet_slot, 'id', '') == 'rands_heart':
            rows.append(("Death Ward", FP.PASSIVE_WARD, None))
        for eid, val in player.status_effects.items():
            if val == 0:
                continue
            info = EFFECT_INFO.get(eid)
            if not info:
                continue
            display_name, rgb, _ = info
            rows.append((self._effect_label(display_name, val), rgb, eid))
        if not rows:
            self.screen.blit(self._fsm.render("(none)", True, FP.SLOT_EMPTY),
                             (self.x + self.PAD, y))
            return y + S(22) + self.SECTION_GAP

        # One full-width chip per row (2026-10-16 visual review: two columns
        # ellipsised the turn counts at 1920x1080). The grid is capped so a
        # big stack never runs off the pane; overflow gets a "+N more" line.
        bottom = self.screen.get_height() - self.PAD
        max_chips = max(1, min(10, (bottom - y - S(22)) // S(24)))
        visible = rows[:max_chips]
        col_w = self.w - self.PAD * 2
        ay = y
        for label, color, eid in visible:
            if ay + S(21) > bottom:
                break
            self._effect_chip(self.x + self.PAD, ay, col_w, label, color, eid)
            ay += S(24)
        y_end = ay
        if len(rows) > len(visible):
            more = f"+{len(rows) - len(visible)} more"
            self.screen.blit(self._fsm.render(more, True, FP.FADED_TEXT),
                             (self.x + self.PAD, y_end))
            y_end += S(22)
        return y_end + self.SECTION_GAP

    def _power_color(self, state: str) -> tuple:
        if state == "ready":
            return FP.SUCCESS_TEXT
        if state == "uses":
            return FP.MP_BLUE_TEXT
        return FP.WARNING_TEXT

    def _compact_row(self, y: int, label: str, meta: str, color: tuple,
                     *, label_color: tuple | None = None) -> int:
        row = pygame.Rect(self.x + self.PAD, y, self.w - self.PAD * 2, S(24))
        pygame.draw.rect(self.screen, (18, 22, 42), row, border_radius=4)
        pygame.draw.rect(self.screen, color, (row.x, row.y, S(4), row.h), border_radius=2)
        meta_w = min(S(88), max(S(50), self._fsm.size(meta)[0] + S(8)))
        self.screen.blit(self._fbold.render(self._fit(self._fbold, label, row.w - meta_w - S(18)),
                                            True, label_color or FP.BODY_TEXT),
                         (row.x + S(10), row.y + S(2)))
        meta_surf = self._fbold.render(self._fit(self._fbold, meta, meta_w), True, color)
        self.screen.blit(meta_surf, (row.right - meta_surf.get_width() - S(8), row.y + S(2)))
        return y + S(27)

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
            y += S(22)
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
            y += S(22)
            if not rows:
                self.screen.blit(self._fsm.render("(none)", True, FP.SLOT_EMPTY),
                                 (self.x + self.PAD, y))
                return y + S(24)
            for row in rows:
                if y + S(24) > bottom:
                    return y
                y = self._compact_row(y, row.label, row.meta, row.color,
                                      label_color=row.color)
            return y + S(8)

        y = section("Enemies", monsters, y)
        if y + S(44) <= bottom:
            y = section("Items", items, y)
        return y
