import pygame

SIDEBAR_W = 320

_MSG_COLORS = {
    'info':    (210, 210, 210),
    'success': (80,  220,  80),
    'warning': (220, 190,  50),
    'danger':  (220,  60,  60),
    'loot':    (255, 195,  50),
}

_IC_COLOR = {
    'weapon':     (225, 160,  70),
    'armor':      ( 90, 155, 225),
    'shield':     ( 90, 175, 225),
    'ingredient': (150, 220, 110),
    'corpse':     (155,  75,  75),
    'accessory':  (215, 110, 215),
}


class MessageLog:
    MAX = 60

    def __init__(self):
        self.entries: list[tuple[str, str]] = []
        self._font = pygame.font.SysFont('consolas', 14)

    def add(self, text: str, msg_type: str = 'info'):
        self.entries.append((text, msg_type))
        if len(self.entries) > self.MAX:
            self.entries.pop(0)

    def draw(self, screen: pygame.Surface, x: int, y: int, w: int, h: int):
        pygame.draw.rect(screen, (8, 8, 16), (x, y, w, h))
        pygame.draw.line(screen, (40, 40, 80), (x, y), (x + w, y), 1)

        line_h = 18
        max_lines = (h - 8) // line_h
        visible = self.entries[-max_lines:]

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

    def __init__(self, screen: pygame.Surface, x: int):
        self.screen = screen
        self.x = x
        self.w = SIDEBAR_W
        self.h = screen.get_height()
        self._fsm  = pygame.font.SysFont('consolas', 14)
        self._fbold = pygame.font.SysFont('consolas', 14, bold=True)
        self._fhd  = pygame.font.SysFont('consolas', 14, bold=True)

    def draw(self, player, dungeon_level: int, turn_count: int):
        pygame.draw.rect(self.screen, (10, 10, 22), (self.x, 0, self.w, self.h))
        pygame.draw.line(self.screen, (45, 45, 85), (self.x, 0), (self.x, self.h), 2)

        y = self.PAD
        y = self._vitals(player, y)
        y = self._attributes(player, y)
        y = self._status(player, dungeon_level, turn_count, y)
        y = self._equipment(player, y)
        self._inventory(player, y)

    # ------------------------------------------------------------------
    # Section helpers
    # ------------------------------------------------------------------

    def _header(self, text: str, y: int) -> int:
        pygame.draw.rect(self.screen, (20, 20, 42),
                         (self.x + self.PAD, y, self.w - self.PAD * 2, 16))
        self.screen.blit(
            self._fhd.render(text, True, (120, 140, 210)),
            (self.x + self.PAD + 3, y)
        )
        return y + 18

    def _bar(self, y: int, label: str, val: int, max_val: int,
             bar_color: tuple) -> int:
        self.screen.blit(
            self._fsm.render(label, True, (130, 130, 165)),
            (self.x + self.PAD, y)
        )
        bx = self.x + self.PAD + 26
        bw = self.w - self.PAD * 2 - 26 - 42
        bh = 10
        ratio = max(0.0, min(1.0, val / max(1, max_val)))

        pygame.draw.rect(self.screen, (22, 22, 35),
                         (bx, y + 1, bw, bh), border_radius=3)
        if ratio > 0:
            pygame.draw.rect(self.screen, bar_color,
                             (bx, y + 1, max(2, int(bw * ratio)), bh),
                             border_radius=3)

        self.screen.blit(
            self._fsm.render(f"{val}/{max_val}", True, (150, 150, 165)),
            (bx + bw + 4, y)
        )
        return y + 14

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
            ay = y + (i // 3) * 16
            self.screen.blit(
                self._fsm.render(f"{name}:", True, (105, 105, 150)), (ax, ay)
            )
            vc = (235, 205, 55) if val > 12 else (175, 175, 195) if val >= 10 else (185, 85, 85)
            self.screen.blit(self._fbold.render(str(val), True, vc), (ax + 33, ay))
        return y + 2 * 16 + self.SECTION_GAP

    def _status(self, player, dungeon_level: int, turn_count: int, y: int) -> int:
        from status_effects import EFFECT_INFO, DEBUFFS
        y = self._header("STATUS", y)
        ac = player.get_ac()
        ac_color = (100, 220, 100) if ac <= 0 else (150, 195, 150) if ac <= 5 else (195, 175, 100)
        for text, color in [
            (f"AC     {ac}",                          ac_color),
            (f"Level  {dungeon_level}",               (150, 150, 205)),
            (f"Turns  {turn_count}",                  (140, 140, 175)),
            (f"Sight  {player.get_sight_radius()}",   (150, 195, 205)),
            (f"Timer  {player.get_quiz_timer()}s",    (195, 165, 165)),
        ]:
            self.screen.blit(self._fsm.render(text, True, color),
                             (self.x + self.PAD, y))
            y += 14

        # Hunger indicator
        sp = player.sp
        if sp < 20:
            self.screen.blit(
                self._fbold.render("[Starving!]", True, (215, 50, 50)),
                (self.x + self.PAD, y)
            )
            y += 15
        elif sp < 60:
            self.screen.blit(
                self._fbold.render("[Hungry]", True, (215, 180, 45)),
                (self.x + self.PAD, y)
            )
            y += 15

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
                ay = y + (i // 2) * 14
                self.screen.blit(self._fbold.render(label, True, rgb), (ax, ay))
            y += ((len(active) + 1) // 2) * 14

        return y + self.SECTION_GAP

    def _equipment(self, player, y: int) -> int:
        y = self._header("EQUIPMENT", y)
        equipped = player.get_equipped_items()
        for label, key in [
            ("Weapon", "weapon"), ("Shield", "shield"),
            ("Head",   "head"),   ("Body",   "body"),
            ("Hands",  "hands"),  ("Legs",   "legs"),
            ("Feet",   "feet"),
        ]:
            item = equipped.get(key)
            if item:
                iname = item.name
                # Show ammo count for ranged weapons
                if key == "weapon" and getattr(item, 'requires_ammo', None):
                    ammo_type = item.requires_ammo
                    total = sum(
                        i.count for i in player.inventory
                        if getattr(i, 'ammo_type', None) == ammo_type
                    )
                    iname += f" [{total} {ammo_type}s]"
                # Cursed indicator
                if getattr(item, 'cursed', False):
                    iname += " {C}"
                # Enchantment indicator
                eb = getattr(item, 'enchant_bonus', 0)
                if eb > 0:
                    iname += f" +{eb}"
                elif eb < 0:
                    iname += f" {eb}"
            else:
                iname = "\u2014"
            ic = (195, 190, 135) if item else (52, 52, 70)
            self.screen.blit(
                self._fsm.render(f"{label}:", True, (105, 105, 150)),
                (self.x + self.PAD, y)
            )
            self.screen.blit(
                self._fsm.render(iname, True, ic),
                (self.x + self.PAD + 46, y)
            )
            y += 14
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
        wc  = (195, 150, 50) if wt > lim * 0.75 else (110, 155, 110)
        self.screen.blit(
            self._fsm.render(f"Wt: {wt:.0f}/{lim}", True, wc),
            (self.x + self.PAD, y)
        )
        y += 14

        for letter, item in items:
            if y > self.h - 16:
                self.screen.blit(
                    self._fsm.render("...", True, (85, 85, 105)),
                    (self.x + self.PAD, y)
                )
                break
            ic = _IC_COLOR.get(getattr(item, 'item_class', ''), (165, 165, 165))
            self.screen.blit(
                self._fsm.render(f"{letter})", True, (145, 145, 65)),
                (self.x + self.PAD, y)
            )
            count = getattr(item, 'count', None)
            display = f"{item.name} x{count}" if count is not None else item.name
            self.screen.blit(
                self._fsm.render(display, True, ic),
                (self.x + self.PAD + 19, y)
            )
            y += 14
