"""Welcome screen and secret-character build definitions.

The WelcomeScreen renders the title vortex, name prompt, and high-score panel
shown before each run. Selecting a name that matches a key in SECRET_BUILDS
hands the matching stat/equipment override dict back to main(), which uses it
to spawn a special Player.
"""

import math
import sys

import pygame

from fantasy_ui import (FP, get_font, draw_panel, draw_header_bar,
                        draw_filigree_bar, draw_shadow_text, centered_text)


# ------------------------------------------------------------------
# Secret character builds
# Stat keys (STR/CON/DEX/INT/WIS/PER) override player defaults.
# _-prefixed keys are build metadata (ignored by the stat loop):
#   _sprite       -> env sprite name (assets/tiles/env/{_sprite}.png)
#   _start_weapon    -> weapon item ID replacing the default iron_dagger
#   _start_wand      -> wand item ID given at start
#   _start_book      -> spellbook item ID given at start
#   _start_accessory -> accessory item ID given at start
#   _start_shield    -> shield item ID given at start
#   _start_armor     -> armor item ID given at start
#   _start_soul_spheres -> int: number of Soul Spheres given at start
#   _no_dagger       -> True: skip the default iron_dagger
#   _immortal        -> True: player cannot die
#   _greeting        -> custom welcome message line (None = default)
# ------------------------------------------------------------------
SECRET_BUILDS: dict[str, dict] = {
    # -- Great philosophers -- INT/WIS focused, physically frail --------------
    "aristotle of stagira": {
        "INT": 18, "WIS": 16, "PER": 14, "STR": 6, "CON": 8, "DEX": 8,
        "_sprite": "player_aristotle",
        "_start_accessory": "ring_intellect_amethyst",
        "_start_wand": "lantern_of_diogenes",
        "_greeting": "Aristotle the Philosopher enters the dungeon with calm reason.",
    },
    "socrates of athens": {
        "WIS": 20, "INT": 14, "PER": 16, "STR": 8, "CON": 10, "DEX": 7,
        "_sprite": "player_socrates",
        "_start_accessory": "ring_wisdom_opal",
        "_start_spells": ["cleanse_spell"],
        "_greeting": "Socrates asks the dungeon a question. It does not answer.",
    },
    "plato of athens": {
        "INT": 17, "WIS": 17, "PER": 12, "STR": 7, "CON": 9, "DEX": 9,
        "_sprite": "player_plato",
        "_start_wand": "wand_of_light",
        "_start_book": "spellbook_light",
        "_greeting": "Plato descends into the cave and finds it uncomfortably on-the-nose.",
    },
    "friedrich nietzsche": {
        "INT": 16, "WIS": 8, "PER": 14, "STR": 14, "CON": 12, "DEX": 10,
        "_sprite": "player_nietzsche",
        "_start_accessory": "ring_strength_iron",
        "_start_spells": ["empower_spell"],
        "_greeting": "Nietzsche stares into the dungeon. The dungeon stares back.",
    },
    "pythagoras of samos": {
        "INT": 18, "WIS": 14, "PER": 10, "STR": 7, "CON": 8, "DEX": 9,
        "_sprite": "player_pythagoras",
        "_start_accessory": "aesops_quill",
        "_greeting": "Pythagoras calculates the optimal descent angle.",
    },
    "prometheus the firebearer": {
        "INT": 15, "WIS": 15, "CON": 15, "STR": 10, "DEX": 10, "PER": 10,
        "_sprite": "player_prometheus",
        "_start_weapon": "prometheus_torch",
        "_greeting": "Prometheus brings fire into the dungeon. The monsters are unimpressed.",
    },
    "diogenes of sinope": {
        "WIS": 18, "PER": 16, "STR": 5, "CON": 5, "DEX": 5, "INT": 5,
        "_sprite": "player_diogenes",
        "_no_dagger": True,
        "_start_wand": "lantern_of_diogenes",
        "_greeting": "Diogenes enters the dungeon. He needs nothing. He wants nothing. He is still going to die.",
    },
    # -- Warriors -- brawn over brain -----------------------------------------
    "achilles son of peleus": {
        "STR": 18, "DEX": 16, "CON": 16, "INT": 8, "WIS": 6, "PER": 10,
        "_sprite": "player_achilles",
        "_no_dagger": True,
        "_start_weapon": "achilles_spear",
        "_start_shield": "wooden_shield",
        "_greeting": "Achilles charges in. His heel tingles ominously.",
    },
    "leonidas of sparta": {
        "STR": 17, "CON": 18, "DEX": 12, "INT": 9, "WIS": 10, "PER": 8,
        "_sprite": "player_leonidas",
        "_start_weapon": "romulus_spear",
        "_start_shield": "shield_of_the_spartans",
        "_greeting": "Leonidas has 299 fewer soldiers than he would like.",
    },
    "alexander the great": {
        "STR": 16, "DEX": 14, "CON": 14, "INT": 14, "WIS": 10, "PER": 12,
        "_sprite": "player_alexander",
        "_start_weapon": "iron_longsword",
        "_start_accessory": "tablet_of_hammurabi",
        "_greeting": "Alexander the Great descends. He intends to conquer this too.",
    },
    "theseus of athens": {
        "STR": 14, "DEX": 14, "CON": 14, "INT": 12, "WIS": 12, "PER": 12,
        "_sprite": "player_theseus",
        "_start_weapon": "gladius",
        "_start_shield": "wooden_shield",
        "_start_accessory": "lyre_of_orpheus",
        "_greeting": "Theseus enters the dungeon. He has done this before.",
    },
    # -- Rogues -- speed and perception ---------------------------------------
    "hermes trismegistus": {
        "DEX": 18, "PER": 18, "INT": 12, "WIS": 10, "STR": 8, "CON": 7,
        "_sprite": "player_hermes",
        "_no_dagger": True,
        "_start_weapon": "iron_rapier",
        "_start_armor": "hermes_sandals_early",
        "_equip_armor": True,
        "_greeting": "Hermes was here, delivered something, and left. He returned because he forgot to sign.",
    },
    "odysseus of ithaca": {
        "DEX": 14, "INT": 16, "PER": 16, "WIS": 14, "STR": 10, "CON": 10,
        "_sprite": "player_odysseus",
        "_no_dagger": True,
        "_start_weapon": "wood_longbow",
        "_start_ammo": "iron_arrow",
        "_start_armor": "cloth_of_penelope",
        "_greeting": "Odysseus descends. He expects this to take ten years.",
    },
    # -- Mages -- pure arcane power --------------------------------------------
    "merlin ambrosius": {
        "INT": 20, "WIS": 14, "PER": 12, "STR": 5, "CON": 7, "DEX": 8,
        "_sprite": "player_merlin",
        "_no_dagger": True,
        "_start_wand": "wand_of_magic_missile",
        "_start_book": "spellbook_magic_missile",
        "_start_spells": ["heal_spell", "shield_spell"],
        "_greeting": "Merlin descends with staff in hand and stars in his robe.",
    },
    # -- New characters --------------------------------------------------------
    "corwin": {
        "STR": 11, "CON": 10, "DEX": 11, "INT": 9, "WIS": 10, "PER": 12,
        "_sprite": "player_ranger",
        "_no_dagger": True,
        "_start_weapon": "wood_shortbow",
        "_start_melee": "iron_sword",
        "_start_ammo": "iron_arrow",
        "_start_extra_acc": ["charmander_stuffie"],
        "_start_unusual_sphere": True,
        "_greeting": "Corwin the Ranger nocks an arrow and descends into the dark.",
    },
    "cain": {
        "STR": 12, "CON": 11, "DEX": 12, "INT": 9, "WIS": 11, "PER": 13,
        "_sprite": "player_ranger",   # same sprite as Corwin
        "_no_dagger": True,
        "_start_weapon": "hardwood_shortbow",
        "_start_melee": "iron_sword",
        "_start_ammo": "iron_arrow",
        "_start_accessory": "ring_protection_silver",
        "_start_extra_acc": ["charmander_stuffie"],
        "_start_unusual_sphere": True,
        "_greeting": "Cain the Hunter moves silently into the dark. Nothing escapes him.",
    },
    "fianna": {
        "STR": 7, "CON": 9, "DEX": 10, "INT": 14, "WIS": 11, "PER": 10,
        "_sprite": "player_wizard_f",
        "_no_dagger": True,
        "_start_weapon": "wood_staff",
        "_start_wand": "wand_of_magic_missile",
        "_start_extra_acc": ["dreamspun_sketchbook"],
        "_start_unusual_sphere": True,
        "_greeting": "Fianna the Wizard weaves a sigil in the air and descends.",
    },
    "fluffs": {
        "STR": 7, "CON": 9, "DEX": 10, "INT": 15, "WIS": 12, "PER": 10,
        "_sprite": "player_wizard_f",   # same sprite as Fianna
        "_no_dagger": True,
        "_start_wand": "wand_of_magic_missile",
        "_start_book": "spellbook_magic_missile",
        "_start_extra_acc": ["dreamspun_sketchbook"],
        "_start_unusual_sphere": True,
        "_greeting": "Fluffs the Magnificent makes an entrance. The dungeon is honoured.",
    },
    "dad": {
        "STR": 20, "CON": 20, "DEX": 20, "INT": 20, "WIS": 20, "PER": 20,
        "_sprite": "player_dad",
        "_no_dagger": True,
        "_start_weapon": "punch_in_the_face",
        "_immortal": True,
        "_greeting": "Dad has arrived. Everything will be fine.",
    },
    "robyn": {
        "INT": 17, "WIS": 14, "DEX": 16, "PER": 14, "CON": 10, "STR": 9,
        "_sprite": "player_robyn",
        "_no_dagger": True,
        "_start_weapon": "hardwood_shortbow",
        "_start_ammo": "iron_arrow",
        "_start_book": "spellbook_sleep",
        "_start_accessory": "rands_heart",
        "_greeting": "Robyn descends -- sharp-eyed, soft-footed, and sharper-tongued than most.",
    },
    # -- Special ---------------------------------------------------------------
    "ash williams": {
        "STR": 16, "CON": 16, "DEX": 14, "INT": 6, "WIS": 6, "PER": 10,
        "_sprite": "player_ash_williams",
        "_no_dagger": True,
        "_start_weapon": "boomstick",
        "_start_melee": "chainsaw_prosthetic",
        "_start_ammo": "shotgun_shell",
        "_start_book": "necronomicon",
        "_lock_melee": True,
        "_greeting": "Good. Bad. I'm the guy with the gun.",
    },
    "geralt of rivia": {
        "STR": 14, "CON": 14, "DEX": 16, "INT": 10, "WIS": 12, "PER": 14,
        "_sprite": "player_geralt",
        "_no_dagger": True,
        "_start_weapon": "witcher_silver_blade",
        "_start_spells": ["sign_aard", "sign_igni", "sign_quen", "sign_yrden", "sign_axii"],
        "_start_potions": ["potion_of_healing", "potion_of_haste", "potion_of_fire_resistance"],
        "_greeting": "The Witcher unsheathes his silver blade. Wind's howling.",
    },
    "ciri riannon": {
        "STR": 8, "CON": 10, "DEX": 18, "INT": 14, "WIS": 12, "PER": 16,
        "_sprite": "player_ciri",
        "_no_dagger": True,
        "_start_weapon": "zireael",
        "_elder_blood": True,
        "_greeting": "Ciri steps through a portal. The Elder Blood sings in her veins.",
    },
    "ash ketchum": {
        "PER": 18, "INT": 16, "WIS": 12, "DEX": 10, "CON": 8, "STR": 6,
        "_sprite": "player_ash_ketchum",
        "_no_dagger": True,
        "_start_armor": "trainers_cap",
        "_equip_armor": True,
        "_start_soul_spheres": 4,
        "_greeting": "Ash Ketchum adjusts his cap. Gotta catch 'em all.",
    },
    # -- QA ----------------------------------------------------------------
    "titivillus": {
        "STR": 12, "CON": 12, "DEX": 12, "INT": 12, "WIS": 12, "PER": 12,
        "_sprite": "player_dad",
        "_start_weapon": "iron_longsword",
        "_start_shield": "wooden_shield",
        "_start_wand": "wand_of_fire",
        "_start_book": "spellbook_magic_missile",
        "_start_ammo": "iron_arrow",
        "_start_accessory": "ring_protection_silver",
        "_greeting": "The Scribe of Errors descends, quill in hand, to document every flaw.",
    },
}


class WelcomeScreen:
    """90s adventure-game-style welcome screen with domain art vortex."""

    _TITLE_LINE1 = "PHILOSOPHER'S"
    _TITLE_LINE2 = "QUEST"
    _PROMPT      = "Enter your name, seeker:"

    # (label, base_angle_deg, EGA-style color, quiz subject symbol)
    _DOMAINS = [
        # (label, degree_offset, color, symbol) — 12 subjects, 30° apart
        ("MATH",        0, (85, 255, 255),  "#"),
        ("GEOGRAPHY",  30, (85, 255, 85),   "G"),
        ("HISTORY",    60, (255, 215, 0),   "H"),
        ("ANIMAL",     90, (255, 140, 0),   "A"),
        ("COOKING",   120, (255, 85, 255),  "C"),
        ("SCIENCE",   150, (85, 85, 255),   "?"),
        ("PHILOSOPHY",180, (200, 200, 255), "P"),
        ("GRAMMAR",   210, (255, 85, 85),   "Q"),
        ("ECONOMICS", 240, (170, 255, 0),   "$"),
        ("THEOLOGY",  270, (200, 170, 80),  "+"),
        ("TRIVIA",    300, (255, 200, 100), "T"),
        ("AI",        330, (0, 220, 120),   "W"),
    ]

    def __init__(self, screen: pygame.Surface, version: str):
        self.screen   = screen
        self.version  = version
        self.W, self.H = screen.get_size()
        self.cx = self.W // 2
        self.cy = self.H // 2
        # FANTASY: Replace consolas fonts with grimoire theme fonts
        self.font_xl   = get_font('title',   52, bold=True)
        self.font_lg   = get_font('heading', 32)
        self.font_md   = get_font('body',    20)
        self.font_sm   = get_font('body',    15)
        self.font_icon = get_font('symbol',  26)
        self.font_tiny = get_font('body',    12)
        self.name_buf    = ''
        self.cursor_on   = True
        self.cursor_timer = 0.0
        self._anim_t     = 0.0
        self._has_save   = False
        self._delete_flash = 0.0
        self._show_alltime = False
        self._god_prompt   = False   # True when showing "Did you mean Dad?" popup
        # Pre-render stone background into a surface
        self._bg = self._make_stone_bg()

    def _make_stone_bg(self):
        surf = pygame.Surface((self.W, self.H))
        surf.fill((4, 5, 14))
        block = 48
        for row in range(self.H // block + 2):
            for col in range(self.W // block + 2):
                x, y = col * block, row * block
                shade = 10 + ((row ^ col) & 3) * 3
                pygame.draw.rect(surf, (shade, shade, shade + 5),
                                 (x + 2, y + 2, block - 3, block - 3))
                # mortar lines
                pygame.draw.line(surf, (shade + 8, shade + 8, shade + 14),
                                 (x + 2, y + 2), (x + block - 3, y + 2))
                pygame.draw.line(surf, (shade + 8, shade + 8, shade + 14),
                                 (x + 2, y + 2), (x + 2, y + block - 3))
        return surf

    def run(self, clock: pygame.time.Clock) -> tuple[str, dict | None]:
        """Returns (name, build). If a save exists for name, main() will load it."""
        from save_system import save_exists

        while True:
            dt = clock.tick(60) / 1000.0
            self._anim_t  += dt
            self.cursor_timer += dt
            if self.cursor_timer >= 0.55:
                self.cursor_on = not self.cursor_on
                self.cursor_timer = 0.0
            if getattr(self, '_delete_flash', 0.0) > 0.0:
                self._delete_flash = max(0.0, self._delete_flash - dt)

            # Update save-exists hint for whatever name is currently typed
            self._has_save = save_exists(self.name_buf.strip()) if self.name_buf.strip() else False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.WINDOWRESIZED:
                    self.W, self.H = event.x, event.y
                    self.cx = self.W // 2
                    self.cy = self.H // 2
                    self._bg = self._make_stone_bg()
                    continue
                if event.type == pygame.KEYDOWN:
                    if self._show_alltime:
                        # Any key closes the all-time overlay
                        self._show_alltime = False
                        continue
                    if self._god_prompt:
                        if event.key == pygame.K_y:
                            return 'Dad', SECRET_BUILDS.get('dad')
                        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                            self._god_prompt = False
                        continue
                    if event.key == pygame.K_RETURN and self.name_buf.strip():
                        name  = self.name_buf.strip()
                        if name.lower() == 'god':
                            self._god_prompt = True
                            continue
                        build = SECRET_BUILDS.get(name.lower())
                        return name, build
                    elif event.key == pygame.K_DELETE and self._has_save:
                        from save_system import delete_save
                        delete_save(self.name_buf.strip())
                        self._has_save = False
                        self._delete_flash = 2.0   # seconds to show confirmation
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_buf = self.name_buf[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_F2:
                        self._show_alltime = True
                    elif event.key == pygame.K_F3:
                        return '__STUDY_MODE__', None
                    elif len(self.name_buf) < 30 and event.unicode.isprintable():
                        self.name_buf += event.unicode

            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------ drawing

    def _draw(self):
        t  = self._anim_t
        cx, cy = self.cx, self.cy

        self.screen.blit(self._bg, (0, 0))
        self._draw_radial_glow(cx, cy)
        self._draw_domain_ring(cx, cy, t)
        self._draw_vortex(cx, cy, t)
        self._draw_stone(cx, cy, t)
        self._draw_vignette()
        self._draw_title_banner(cx)
        self._draw_name_input(cx, cy)
        self._draw_footer(cx)
        self._draw_leaderboard()
        if self._show_alltime:
            self._draw_alltime()
        if self._god_prompt:
            self._draw_god_prompt()

    def _draw_god_prompt(self):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 380, 120
        bx = (self.W - bw) // 2
        by = (self.H - bh) // 2
        pygame.draw.rect(self.screen, (12, 10, 25), (bx, by, bw, bh))
        pygame.draw.rect(self.screen, (200, 170, 80), (bx, by, bw, bh), 2)
        # Inner bevel
        pygame.draw.rect(self.screen, (160, 130, 60), (bx+2, by+2, bw-4, bh-4), 1)

        msg = self.font_lg.render("Did you mean, 'Dad'?", True, (255, 240, 200))
        self.screen.blit(msg, (bx + (bw - msg.get_width()) // 2, by + 25))

        hint = self.font_md.render("(Y)es  /  (N)o", True, (180, 170, 140))
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + 72))

    def _draw_radial_glow(self, cx, cy):
        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for r, alpha in [(300, 12), (240, 18), (180, 22), (130, 28), (90, 20)]:
            pygame.draw.circle(glow, (30, 0, 80, alpha), (cx, cy), r)
        self.screen.blit(glow, (0, 0))

    def _draw_domain_ring(self, cx, cy, t):
        ring_r = min(cx, cy) * 0.52
        orbit_speed = 0.018   # radians/sec -- very slow orbit
        base_angle  = t * orbit_speed

        for i, (label, deg_off, color, symbol) in enumerate(self._DOMAINS):
            angle  = base_angle + math.radians(deg_off)
            ix = cx + int(ring_r * math.cos(angle))
            iy = cy + int(ring_r * math.sin(angle))

            # Energy tendril from icon to center (3 fading lines)
            for w, frac in [(3, 0.25), (2, 0.45), (1, 0.75)]:
                c = tuple(int(v * frac) for v in color)
                pygame.draw.line(self.screen, c, (ix, iy), (cx, cy), w)

            # Icon background panel (EGA-style bordered box)
            box_w, box_h = 68, 58
            bx, by = ix - box_w // 2, iy - box_h // 2
            pygame.draw.rect(self.screen, (8, 8, 20), (bx, by, box_w, box_h))
            pygame.draw.rect(self.screen, color, (bx, by, box_w, box_h), 2)
            # Inner highlight line (top and left -- classic 90s bevel)
            bright = tuple(min(255, v + 80) for v in color)
            pygame.draw.line(self.screen, bright, (bx+1, by+1), (bx+box_w-2, by+1))
            pygame.draw.line(self.screen, bright, (bx+1, by+1), (bx+1, by+box_h-2))

            # Domain symbol (large glyph)
            sym_surf = self.font_icon.render(symbol, True, color)
            self.screen.blit(sym_surf, (ix - sym_surf.get_width() // 2, iy - 18))

            # Domain-specific mini pixel art shape
            self._draw_domain_detail(ix, iy, label, color, t)

            # Label below box
            lbl = self.font_tiny.render(label, True, color)
            self.screen.blit(lbl, (ix - lbl.get_width() // 2, by + box_h + 3))

    def _draw_domain_detail(self, cx, cy, label, color, t):
        """Draw a small iconic shape for each domain beneath the symbol."""
        dim = tuple(max(0, v - 60) for v in color)
        bright = tuple(min(255, v + 60) for v in color)
        if label == "MATH":
            # Two horizontal bars (= sign) and a plus
            pygame.draw.line(self.screen, dim, (cx-12, cy+12), (cx+12, cy+12), 2)
            pygame.draw.line(self.screen, dim, (cx-12, cy+17), (cx+12, cy+17), 2)
        elif label == "GEOGRAPHY":
            # Mountain silhouette (triangle)
            pts = [(cx, cy+8), (cx-12, cy+20), (cx+12, cy+20)]
            pygame.draw.polygon(self.screen, dim, pts)
            pygame.draw.polygon(self.screen, color, pts, 1)
        elif label == "HISTORY":
            # Column (rectangle with capital)
            pygame.draw.rect(self.screen, dim, (cx-5, cy+10, 10, 14))
            pygame.draw.rect(self.screen, color, (cx-9, cy+9, 18, 3))
            pygame.draw.rect(self.screen, color, (cx-9, cy+23, 18, 3))
        elif label == "ANIMAL":
            # Paw print (circle + 3 small circles)
            pygame.draw.circle(self.screen, dim, (cx, cy+16), 7)
            for dx in [-8, 0, 8]:
                pygame.draw.circle(self.screen, color, (cx+dx, cy+7), 3)
        elif label == "COOKING":
            # Cauldron (trapezoid)
            pts = [(cx-10, cy+10), (cx+10, cy+10),
                   (cx+8,  cy+22), (cx-8,  cy+22)]
            pygame.draw.polygon(self.screen, dim, pts)
            pygame.draw.polygon(self.screen, color, pts, 1)
            pygame.draw.line(self.screen, bright, (cx-12, cy+10), (cx+12, cy+10), 2)
            # Steam
            for sx in [-4, 4]:
                phase = int(t * 3 + sx) % 4
                pygame.draw.line(self.screen, color,
                                 (cx+sx, cy+8-phase), (cx+sx, cy+4-phase), 1)
        elif label == "SCIENCE":
            # Flask (circle on a stem)
            pygame.draw.circle(self.screen, dim, (cx, cy+18), 6)
            pygame.draw.rect(self.screen, color, (cx-2, cy+10, 4, 8))
            pygame.draw.line(self.screen, color, (cx-5, cy+10), (cx+5, cy+10), 2)
        elif label == "PHILOSOPHY":
            # Eye shape
            pts_t = [(cx-12, cy+14), (cx, cy+8), (cx+12, cy+14)]
            pts_b = [(cx-12, cy+14), (cx, cy+20), (cx+12, cy+14)]
            pygame.draw.polygon(self.screen, dim, pts_t + pts_b)
            pygame.draw.polygon(self.screen, color, pts_t, 1)
            pygame.draw.polygon(self.screen, color, pts_b, 1)
            pygame.draw.circle(self.screen, bright, (cx, cy+14), 4)
        elif label == "GRAMMAR":
            # Open book
            pygame.draw.rect(self.screen, dim, (cx-12, cy+10, 11, 13))
            pygame.draw.rect(self.screen, dim, (cx+1,  cy+10, 11, 13))
            pygame.draw.line(self.screen, bright, (cx, cy+10), (cx, cy+23), 1)
            # Quill
            pts = [(cx+8, cy+8), (cx+14, cy+2), (cx+11, cy+14)]
            pygame.draw.polygon(self.screen, color, pts)
        elif label == "ECONOMICS":
            # Coin stack (2 ovals)
            pygame.draw.ellipse(self.screen, dim,   (cx-9, cy+15, 18, 8))
            pygame.draw.ellipse(self.screen, color, (cx-9, cy+15, 18, 8), 1)
            pygame.draw.ellipse(self.screen, dim,   (cx-9, cy+10, 18, 8))
            pygame.draw.ellipse(self.screen, color, (cx-9, cy+10, 18, 8), 1)
        elif label == "THEOLOGY":
            # Cross
            pygame.draw.rect(self.screen, dim, (cx-2, cy+8, 4, 16))
            pygame.draw.rect(self.screen, dim, (cx-7, cy+12, 14, 4))
            pygame.draw.rect(self.screen, color, (cx-2, cy+8, 4, 16), 1)
            pygame.draw.rect(self.screen, color, (cx-7, cy+12, 14, 4), 1)
        elif label == "TRIVIA":
            # Question mark dot + arc
            pygame.draw.arc(self.screen, color, (cx-7, cy+6, 14, 12),
                            0.3, 3.14, 2)
            pygame.draw.circle(self.screen, bright, (cx, cy+22), 2)
        elif label == "AI":
            # Circuit brain (small grid of dots connected by lines)
            for dx, dy in [(-6, 10), (6, 10), (-6, 20), (6, 20), (0, 15)]:
                pygame.draw.circle(self.screen, bright, (cx+dx, cy+dy), 2)
            pygame.draw.line(self.screen, dim, (cx-6, cy+10), (cx+6, cy+10), 1)
            pygame.draw.line(self.screen, dim, (cx-6, cy+20), (cx+6, cy+20), 1)
            pygame.draw.line(self.screen, dim, (cx-6, cy+10), (cx-6, cy+20), 1)
            pygame.draw.line(self.screen, dim, (cx+6, cy+10), (cx+6, cy+20), 1)
            pygame.draw.line(self.screen, dim, (cx, cy+15), (cx-6, cy+10), 1)
            pygame.draw.line(self.screen, dim, (cx, cy+15), (cx+6, cy+20), 1)

    def _draw_vortex(self, cx, cy, t):
        """Rotating spiral arms -- the knowledge vortex."""
        num_arms = 6
        steps    = 24
        max_r    = 200
        twist    = 3.0   # radians per revolution of the spiral

        for arm in range(num_arms):
            arm_base = arm * (2 * math.pi / num_arms)
            # Alternate arm colors from domain palette
            domain_color = self._DOMAINS[arm % len(self._DOMAINS)][2]

            for step in range(steps):
                frac  = step / steps
                frac2 = (step + 1) / steps
                r1 = frac  * max_r
                r2 = frac2 * max_r
                theta1 = arm_base + frac  * twist - t * 0.7
                theta2 = arm_base + frac2 * twist - t * 0.7

                x1 = cx + int(r1 * math.cos(theta1))
                y1 = cy + int(r1 * math.sin(theta1))
                x2 = cx + int(r2 * math.cos(theta2))
                y2 = cy + int(r2 * math.sin(theta2))

                brightness = frac
                c = tuple(int(v * brightness * 0.7) for v in domain_color)
                w = max(1, int(3 * (1 - frac)))
                pygame.draw.line(self.screen, c, (x1, y1), (x2, y2), w)

    def _draw_stone(self, cx, cy, t):
        """The Philosopher's Stone -- pulsing golden gem."""
        pulse   = abs(math.sin(t * 1.3))
        orb_r   = 34
        glow_r  = orb_r + int(14 + pulse * 10)

        # Outer glow rings
        glow_surf = pygame.Surface((glow_r * 2 + 10, glow_r * 2 + 10), pygame.SRCALPHA)
        gc = glow_surf.get_rect().center
        for g in range(glow_r, 0, -4):
            alpha = int(35 * (g / glow_r) * pulse)
            col   = (220, 160, int(30 + 60 * pulse), alpha)
            pygame.draw.circle(glow_surf, col, gc, g)
        self.screen.blit(glow_surf, (cx - gc[0], cy - gc[1]))

        # Octagon gem (EGA diamond feel)
        r = orb_r
        oct_pts = [(cx + int(r * math.cos(math.radians(a))),
                    cy + int(r * math.sin(math.radians(a))))
                   for a in range(0, 360, 45)]
        pygame.draw.polygon(self.screen, (180, 130, 20), oct_pts)
        # Face highlights (EGA bevel)
        pygame.draw.polygon(self.screen, (255, 220, 80), oct_pts, 2)
        # Inner gem facet
        inner_pts = [(cx + int((r * 0.5) * math.cos(math.radians(a + 22))),
                      cy + int((r * 0.5) * math.sin(math.radians(a + 22))))
                     for a in range(0, 360, 45)]
        pygame.draw.polygon(self.screen, (255, 240, 140), inner_pts)
        # Sparkle cross
        spark_len = int(8 + pulse * 10)
        for ang in [0, 45, 90, 135]:
            rad = math.radians(ang + t * 30)
            ex  = cx + int(spark_len * math.cos(rad))
            ey  = cy + int(spark_len * math.sin(rad))
            ex2 = cx - int(spark_len * math.cos(rad))
            ey2 = cy - int(spark_len * math.sin(rad))
            pygame.draw.line(self.screen, (255, 255, 200), (ex, ey), (ex2, ey2), 2)

    def _draw_vignette(self):
        W, H = self.W, self.H
        vig = pygame.Surface((W, H), pygame.SRCALPHA)
        for step in range(28):
            ratio  = step / 28
            alpha  = int(220 * ratio ** 2.2)
            margin = int(step * 16)
            pygame.draw.rect(vig, (0, 0, 0, alpha),
                             (margin, margin, W - 2*margin, H - 2*margin), 10)
        self.screen.blit(vig, (0, 0))

    def _draw_title_banner(self, cx):
        # FANTASY: Illuminated manuscript title -- gold text on midnight panel
        bw, bh = 640, 106
        bx, by = cx - bw // 2, 22
        draw_panel(self.screen, (bx, by, bw, bh), bg=False)
        # FANTASY: Decorative filigree under title
        draw_filigree_bar(self.screen, bx + 20, by + bh - 12, bw - 40, FP.GOLD_DARK)

        for text, y, font, is_main in [
            (self._TITLE_LINE1, by + 12, self.font_lg, False),
            (self._TITLE_LINE2, by + 48, self.font_xl, True),
        ]:
            col = FP.GOLD if not is_main else FP.GOLD_BRIGHT
            centered_text(self.screen, font, text, col, y, shadow=True)

    def _draw_name_input(self, cx, cy):
        # FANTASY: Parchment dialog box for name entry
        box_w, box_h = 500, 96
        bx = cx - box_w // 2
        by = cy + int(min(cy, self.H - cy) * 0.60)
        draw_panel(self.screen, (bx, by, box_w, box_h), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, box_w, 32),
                        text=self._PROMPT, font=self.font_sm, text_color=FP.GOLD_PALE)
        # FANTASY: Input field
        field_y = by + 38
        pygame.draw.rect(self.screen, FP.MIDNIGHT, (bx + 14, field_y, box_w - 28, 34))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx + 14, field_y, box_w - 28, 34), 1)
        display = self.name_buf + ('|' if self.cursor_on else ' ')
        draw_shadow_text(self.screen, self.font_lg, display, FP.PARCHMENT_LIGHT,
                         (bx + 20, field_y + (34 - self.font_lg.get_height()) // 2))
        if self.name_buf.strip().lower() in SECRET_BUILDS:
            badge = self.font_sm.render("[*] SECRET BUILD ACTIVE!", True, FP.GOLD_BRIGHT)
            self.screen.blit(badge, (cx - badge.get_width() // 2, by + box_h + 8))

    def _draw_footer(self, cx):
        has_save = getattr(self, '_has_save', False)
        text = "[ ENTER ] begin your quest     [ F3 ] study mode     [ ESC ] quit"
        hint = self.font_tiny.render(text, True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.H - 28))
        # Version number — bottom-right corner
        ver = self.font_tiny.render(f"v{self.version}", True, (60, 58, 70))
        self.screen.blit(ver, (self.W - ver.get_width() - 10, self.H - 20))
        # Delete-flash confirmation (shown for 2 seconds after DEL)
        flash = getattr(self, '_delete_flash', 0.0)
        if flash > 0.0:
            del_msg = self.font_sm.render("[X] Save deleted -- press ENTER to start fresh", True, (220, 80, 80))
            self.screen.blit(del_msg, (cx - del_msg.get_width() // 2, self.H - 52))
        elif has_save:
            save_hint = self.font_sm.render("[S] Saved journey found -- ENTER to continue  |  DEL to erase", True, FP.SUCCESS_TEXT)
            self.screen.blit(save_hint, (cx - save_hint.get_width() // 2, self.H - 52))

    def _draw_leaderboard(self):
        """Right-side panel showing Top 10 runs."""
        try:
            from highscore_system import get_top
            entries = get_top(10)
        except Exception:
            return
        if not entries:
            return

        W, H = self.W, self.H
        bw  = 390
        bx  = W - bw - 18
        # Header + rows + divider + footer hint
        row_h    = 22
        header_h = 36
        n        = len(entries)
        bh       = header_h + 6 + n * row_h + 10 + 26
        by       = max(130, H // 2 - bh // 2)

        # Semi-transparent background
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((6, 4, 18, 215))
        self.screen.blit(panel, (bx, by))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx, by, bw, bh), 1, border_radius=6)

        # Header bar
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, (bx, by, bw, header_h), border_radius=6)
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx, by + header_h, bw, 1))
        hdr = self.font_sm.render("TOP RUNS", True, FP.GOLD_BRIGHT)
        self.screen.blit(hdr, (bx + bw // 2 - hdr.get_width() // 2,
                                by + (header_h - hdr.get_height()) // 2))

        # Column header line
        y = by + header_h + 4
        col_hdr = self.font_tiny.render("     NAME             LVL      SCORE   GR", True, FP.GOLD_PALE)
        self.screen.blit(col_hdr, (bx + 8, y))
        y += 14
        pygame.draw.line(self.screen, FP.GOLD_DARK, (bx + 8, y), (bx + bw - 8, y))
        y += 4

        # Rows
        for i, e in enumerate(entries):
            victory = e.get('victory', False)
            name    = e.get('name', '?')[:11]
            score   = e.get('score', 0)
            grade   = e.get('grade', '?')
            level   = e.get('level', 1)
            col     = FP.GOLD_BRIGHT if victory else FP.BODY_TEXT

            # rank
            rank_s = self.font_tiny.render(f"{i+1:>2}.", True, FP.FADED_TEXT)
            self.screen.blit(rank_s, (bx + 8, y))
            # crown
            if victory:
                crown_s = self.font_tiny.render("[V]", True, (255, 215, 0))
                self.screen.blit(crown_s, (bx + 30, y))
            # name
            name_s = self.font_tiny.render(f"{name:<11}", True, col)
            self.screen.blit(name_s, (bx + 54, y))
            # level
            level_s = self.font_tiny.render(f"L{level:<3}", True, FP.FADED_TEXT)
            self.screen.blit(level_s, (bx + 140, y))
            # score (right-aligned)
            score_s = self.font_tiny.render(f"{score:>9,}", True, col)
            self.screen.blit(score_s, (bx + 183, y))
            # grade
            grade_s = self.font_tiny.render(f"{grade:>2}", True, FP.GOLD_PALE)
            self.screen.blit(grade_s, (bx + 285, y))

            y += row_h
            # Mid divider after top 5
            if i == 4:
                pygame.draw.line(self.screen, FP.MIDNIGHT_MID,
                                 (bx + 8, y - row_h // 2), (bx + bw - 8, y - row_h // 2))

        # Footer hint
        pygame.draw.line(self.screen, FP.GOLD_DARK,
                         (bx + 8, y + 2), (bx + bw - 8, y + 2))
        hint = self.font_tiny.render("[ F2 ]  View All-Time Top 100", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + bw // 2 - hint.get_width() // 2, y + 6))

    def _draw_alltime(self):
        """Full-screen overlay showing all-time top 100 scores."""
        try:
            from highscore_system import get_top
            entries = get_top(100)
        except Exception:
            entries = []

        W, H = self.W, self.H

        # Dim overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 10, 235))
        self.screen.blit(overlay, (0, 0))

        bw, bh = min(1380, W - 40), min(830, H - 40)
        bx = (W - bw) // 2
        by = (H - bh) // 2

        pygame.draw.rect(self.screen, (8, 6, 22), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, FP.GOLD, (bx, by, bw, bh), 2, border_radius=8)
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx + 4, by + 4, bw - 8, bh - 8), 1, border_radius=6)

        # Header
        header_h = 42
        pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, (bx, by, bw, header_h), border_radius=8)
        title = self.font_md.render("ALL-TIME HIGH SCORES", True, FP.GOLD_BRIGHT)
        self.screen.blit(title, (bx + bw // 2 - title.get_width() // 2,
                                  by + (header_h - title.get_height()) // 2))

        # Footer
        footer_h = 28
        footer_y  = by + bh - footer_h
        pygame.draw.line(self.screen, FP.GOLD_DARK,
                         (bx + 16, footer_y - 4), (bx + bw - 16, footer_y - 4))
        close_hint = self.font_tiny.render("[ Any Key ]  Close", True, FP.HINT_TEXT)
        self.screen.blit(close_hint, (bx + bw // 2 - close_hint.get_width() // 2,
                                       footer_y + (footer_h - close_hint.get_height()) // 2))

        # Content area -- two columns
        content_top = by + header_h + 6
        content_bot = footer_y - 8
        content_h   = content_bot - content_top
        row_h       = 17
        col_w       = bw // 2 - 16

        # Column header
        col_hdr_txt = "  #  NAME              LVL       SCORE  GR  DATE"
        for col_x in (bx + 12, bx + bw // 2 + 8):
            hdr_s = self.font_tiny.render(col_hdr_txt, True, FP.GOLD_PALE)
            self.screen.blit(hdr_s, (col_x, content_top))
            pygame.draw.line(self.screen, FP.GOLD_DARK,
                             (col_x, content_top + 16),
                             (col_x + col_w, content_top + 16))

        max_rows = (content_h - 22) // row_h
        row_top  = content_top + 22

        for i, e in enumerate(entries):
            col_idx = 0 if i < max_rows else 1
            row_idx = i if i < max_rows else i - max_rows
            if row_idx >= max_rows:
                break

            col_x = bx + 12 if col_idx == 0 else bx + bw // 2 + 8
            ry    = row_top + row_idx * row_h

            victory = e.get('victory', False)
            name    = e.get('name', '?')[:13]
            level   = e.get('level', 1)
            score   = e.get('score', 0)
            grade   = e.get('grade', '?')
            date    = e.get('date', '')

            text_col = FP.GOLD_BRIGHT if victory else (FP.BODY_TEXT if row_idx % 2 == 0 else FP.PARCHMENT_DARK)
            crown    = 'V' if victory else ' '

            # rank + crown
            rank_s = self.font_tiny.render(f"{crown}{i+1:>3}.", True, FP.FADED_TEXT if not victory else (255, 215, 0))
            self.screen.blit(rank_s, (col_x, ry))
            # name
            name_s = self.font_tiny.render(f"{name:<13}", True, text_col)
            self.screen.blit(name_s, (col_x + 34, ry))
            # level
            level_s = self.font_tiny.render(f"L{level:<3}", True, FP.FADED_TEXT)
            self.screen.blit(level_s, (col_x + 128, ry))
            # score
            score_s = self.font_tiny.render(f"{score:>9,}", True, text_col)
            self.screen.blit(score_s, (col_x + 165, ry))
            # grade
            grade_s = self.font_tiny.render(f"{grade:>2}", True, FP.GOLD_PALE)
            self.screen.blit(grade_s, (col_x + 240, ry))
            # date
            date_s = self.font_tiny.render(date[-5:] if len(date) >= 5 else date, True, FP.FADED_TEXT)
            self.screen.blit(date_s, (col_x + 262, ry))
