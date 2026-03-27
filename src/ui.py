import pygame

# FANTASY: Import theme helpers from the central fantasy_ui module
from fantasy_ui import FP, get_font, draw_panel, draw_divider, draw_shadow_text, ITEM_COLOR

SIDEBAR_W = 430

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
        self.x = x
        self.w = SIDEBAR_W
        # FANTASY: Grimoire font set -- larger for readability
        self._fsm   = get_font('body', 20)
        self._fbold = get_font('body', 20, bold=True)
        self._fhd   = get_font('heading', 19)

    def draw(self, player, dungeon_level: int, turn_count: int, gold: int = 0):
        h = self.screen.get_height()
        # FANTASY: Midnight sidebar background + gold-dark left border
        pygame.draw.rect(self.screen, FP.MIDNIGHT, (self.x, 0, self.w, h))
        pygame.draw.line(self.screen, FP.GOLD_DARK, (self.x, 0), (self.x, h), 2)

        y = self.PAD
        y = self._vitals(player, y)
        y = self._attributes(player, y)
        y = self._status(player, dungeon_level, turn_count, gold, y)
        y = self._equipment(player, y)
        self._inventory(player, y)

    # ------------------------------------------------------------------
    # Section helpers
    # ------------------------------------------------------------------

    def _header(self, text: str, y: int) -> int:
        # FANTASY: Section header with midnight-mid bg and gold-bright text
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID,
                         (self.x + self.PAD, y, self.w - self.PAD * 2, 24))
        self.screen.blit(
            self._fhd.render(text, True, FP.GOLD_BRIGHT),
            (self.x + self.PAD + 3, y + 2)
        )
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

    def _vitals(self, player, y: int) -> int:
        y = self._header("VITALS", y)
        sp_r = player.sp / max(1, player.max_sp)
        sp_col = (
            (45, 185, 45)   if sp_r > 0.50 else
            (195, 145, 35)  if sp_r > 0.25 else
            (195,  45,  45)
        )
        y = self._bar(y, "HP", player.hp, player.max_hp, (185, 42, 42))
        y = self._bar(y, "SP", player.sp, player.max_sp, sp_col)
        y = self._bar(y, "MP", player.mp, player.max_mp, (50, 85, 205))
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

    def _status(self, player, dungeon_level: int, turn_count: int, gold: int, y: int) -> int:
        from status_effects import EFFECT_INFO, DEBUFFS
        y = self._header("STATUS", y)
        ac = player.get_ac()
        # FANTASY: AC color thresholds
        ac_color = FP.SUCCESS_TEXT if ac <= 0 else (150, 195, 150) if ac <= 5 else FP.WARNING_TEXT
        for text, color in [
            (f"AC     {ac}",                          ac_color),
            (f"Level  {dungeon_level}",               FP.BODY_TEXT),
            (f"Turns  {turn_count}",                  FP.BODY_TEXT),
            (f"Gold   {gold:,}",                      FP.GOLD_PALE),
            (f"Sight  {player.get_sight_radius()}",   FP.BODY_TEXT),
            (f"Timer  {player.get_quiz_timer('math')}s",  FP.WARNING_TEXT),
        ]:
            self.screen.blit(self._fsm.render(text, True, color),
                             (self.x + self.PAD, y))
            y += 22

        # Lockpick charges
        picks = getattr(player, 'lockpick_charges', 0)
        if picks > 0:
            self.screen.blit(
                self._fsm.render(f"Picks  {picks}", True, (190, 175, 120)),
                (self.x + self.PAD, y)
            )
            y += 22

        # Known spells count
        spell_count = len(getattr(player, 'known_spells', {}))
        if spell_count > 0:
            self.screen.blit(
                self._fsm.render(f"Spells {spell_count}", True, (100, 160, 255)),
                (self.x + self.PAD, y)
            )
            y += 22

        # Prayer cooldown -- FANTASY colors
        if player.prayer_cooldown > 0:
            pray_color = (140, 100, 200)   # cooldown: arcane purple
            self.screen.blit(
                self._fsm.render(f"Prayer: {player.prayer_cooldown}t", True, pray_color),
                (self.x + self.PAD, y)
            )
        else:
            self.screen.blit(
                self._fsm.render("Prayer: Ready", True, FP.GOLD_PALE),
                (self.x + self.PAD, y)
            )
        y += 22

        # Recall Lore cooldown
        if player.recall_lore_cooldown > 0:
            lore_cd_color = (80, 160, 200)   # teal: knowledge cooling
            self.screen.blit(
                self._fsm.render(f"Lore:   {player.recall_lore_cooldown}t", True, lore_cd_color),
                (self.x + self.PAD, y)
            )
        else:
            self.screen.blit(
                self._fsm.render("Lore:   Ready", True, (120, 200, 240)),
                (self.x + self.PAD, y)
            )
        y += 22

        # Hack Reality cooldown intentionally hidden from sidebar

        # Hunger indicator -- FANTASY colors
        sp = player.sp
        if sp < 20:
            self.screen.blit(
                self._fbold.render("[Starving!]", True, FP.DANGER_TEXT),
                (self.x + self.PAD, y)
            )
            y += 24
        elif sp < 60:
            self.screen.blit(
                self._fbold.render("[Hungry]", True, FP.WARNING_TEXT),
                (self.x + self.PAD, y)
            )
            y += 24

        # Lockpick durability (if carrying one)
        from items import Lockpick
        lp = next((i for i in player.inventory if isinstance(i, Lockpick)), None)
        if lp is not None:
            ratio = lp.durability / lp.max_durability
            lp_color = (FP.SUCCESS_TEXT if ratio > 0.5
                        else FP.WARNING_TEXT if ratio > 0.25
                        else FP.DANGER_TEXT)
            lp_text = f"Lockpick: {lp.durability}/{lp.max_durability}  [{lp.name}]"
            self.screen.blit(self._fsm.render(lp_text, True, lp_color), (self.x + self.PAD, y))
            y += 22

        # Item-granted passives (not status effects)
        if any(getattr(i, 'id', '') == 'charmander_stuffie' for i in player.inventory):
            label = "[Fire Protect]"
            self.screen.blit(self._fbold.render(label, True, (245, 150, 60)), (self.x + self.PAD, y))
            y += 22

        # Active status effects in a 2-column grid
        active = [(eid, val) for eid, val in player.status_effects.items() if val != 0]
        if active:
            col_w = (self.w - self.PAD * 2) // 2
            for i, (eid, val) in enumerate(active):
                info = EFFECT_INFO.get(eid)
                if not info:
                    continue
                display_name, rgb, _ = info
                label = f"[{display_name}]"
                ax = self.x + self.PAD + (i % 2) * col_w
                ay = y + (i // 2) * 22
                self.screen.blit(self._fbold.render(label, True, rgb), (ax, ay))
            y += ((len(active) + 1) // 2) * 22

        return y + self.SECTION_GAP

    def _equipment(self, player, y: int) -> int:
        y = self._header("EQUIPMENT", y)
        equipped = player.get_equipped_items()
        # Check if player has Philosopher's Shard in inventory
        has_phil = any(getattr(i, 'id', '') == 'philosophers_shard'
                       for i in player.inventory)
        for label, key in [
            ("Weapon", "weapon"), ("Ranged", "ranged_weapon"), ("Shield", "shield"),
            ("Head",   "head"),   ("Body",   "body"),
            ("Arms",   "arms"),   ("Hands",  "hands"),
            ("Legs",   "legs"),   ("Feet",   "feet"),
            ("Cloak",  "cloak"),  ("Shirt",  "shirt"),
            ("Amulet", "amulet"),
            ("Ring 1", "ring_1"), ("Ring 2", "ring_2"),
            ("Ring 3", "ring_3"), ("Ring 4", "ring_4"),
        ]:
            item = equipped.get(key)
            if item:
                # Name: show identified name if type is known, else unidentified name
                known = (not hasattr(item, 'identified')
                         or item.identified
                         or item.id in player.known_item_ids)
                iname = item.name if known else getattr(item, 'unidentified_name', item.name)
                # Show ammo count for ranged weapons
                if key == "ranged_weapon" and getattr(item, 'requires_ammo', None):
                    ammo_type = item.requires_ammo
                    total = sum(
                        i.count for i in player.inventory
                        if getattr(i, 'ammo_type', None) == ammo_type
                    )
                    iname += f" [{total} {ammo_type}s]"
                # Modifiers only revealed when this specific instance was examined
                if getattr(item, 'identified', True):
                    eb = getattr(item, 'enchant_bonus', 0)
                    if eb > 0:
                        iname += f" +{eb}"
                    elif eb < 0:
                        iname += f" {eb}"
                    if getattr(item, 'cursed', False):
                        iname += " {C}"
            else:
                iname = "\u2014"
            # FANTASY: Gold-pale for equipped items, dim ink for empty slots
            ic = FP.GOLD_PALE if item else (52, 52, 70)
            # FANTASY: FADED_TEXT label color
            label_surf = self._fsm.render(f"{label}:", True, FP.FADED_TEXT)
            self.screen.blit(label_surf, (self.x + self.PAD, y))
            name_x = self.x + self.PAD + label_surf.get_width() + 5
            max_name_w = self.x + self.w - self.PAD - name_x
            iname = self._fit(self._fsm, self._cap(iname), max_name_w)
            self.screen.blit(self._fsm.render(iname, True, ic), (name_x, y))
            y += 22
        # Philosopher's Shard -- passive carry indicator (not an equip slot)
        if has_phil:
            phil_surf = self._fsm.render("* Phil. Shard", True, (220, 200, 120))
            self.screen.blit(phil_surf, (self.x + self.PAD, y))
            y += 20
        return y + self.SECTION_GAP

    def _inventory(self, player, y: int):
        y = self._header("INVENTORY", y)
        items = player.get_inventory_display()
        if not items:
            self.screen.blit(
                self._fsm.render("(empty)", True, (55, 55, 75)),
                (self.x + self.PAD, y)
            )
            return

        wt  = player.get_current_weight()
        lim = player.get_carry_limit()
        # FANTASY: Warning for heavy load, success for normal
        wc  = FP.WARNING_TEXT if wt > lim * 0.75 else FP.SUCCESS_TEXT
        self.screen.blit(
            self._fsm.render(f"Wt: {wt:.0f}/{lim}", True, wc),
            (self.x + self.PAD, y)
        )
        y += 22

        for letter, item in items:
            if y > self.screen.get_height() - 20:
                self.screen.blit(
                    self._fsm.render("...", True, (85, 85, 105)),
                    (self.x + self.PAD, y)
                )
                break
            # FANTASY: Use ITEM_COLOR dict from fantasy_ui
            ic = _IC_COLOR.get(getattr(item, 'item_class', ''), (165, 165, 165))
            # FANTASY: Gold letter color
            self.screen.blit(
                self._fsm.render(f"{letter})", True, FP.GOLD),
                (self.x + self.PAD, y)
            )
            count = getattr(item, 'count', None)
            known = (not hasattr(item, 'identified')
                     or item.identified
                     or item.id in player.known_item_ids)
            raw_name = item.name if known else getattr(item, 'unidentified_name', item.name)
            cname = self._cap(raw_name)
            display = f"{cname} x{count}" if count is not None else cname
            max_disp_w = self.w - self.PAD * 2 - 24
            display = self._fit(self._fsm, display, max_disp_w)
            self.screen.blit(
                self._fsm.render(display, True, ic),
                (self.x + self.PAD + 24, y)
            )
            y += 22
