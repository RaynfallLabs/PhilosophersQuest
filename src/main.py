import math
import os
import sys
import pygame

# FANTASY: High-fantasy medieval/arcane grimoire UI theme
from fantasy_ui import (FP, get_font, draw_panel, draw_dark_panel,
                         draw_header_bar, draw_divider, draw_shadow_text,
                         draw_glow_text, centered_text, draw_overlay,
                         draw_rune_circle, draw_filigree_bar, draw_candle_glow,
                         draw_choice_button, ITEM_COLOR, make_parchment)

from combat import player_attack
from quirk_system import QuirkSystem
from container_system import attempt_lockpick, check_for_mimic
from dungeon import (generate_dungeon, spawn_monsters, spawn_items,
                     STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR)
from food_system import (harvest_corpse, cook_ingredient, eat_food, eat_raw,
                         get_available_compound_recipes, cook_compound_recipe,
                         get_recipes_for_ingredient)
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient, Artifact, Container, Lockpick, Accessory, Wand, Scroll, Spellbook, Ammo, Food, Potion
from level_manager import LevelManager
from player import Player
import sound_system as _snd
from quiz_engine import QuizEngine, QuizMode, QuizState
from renderer import Renderer, TILE_SIZE
from ui import Sidebar, MessageLog, SIDEBAR_W

WINDOW_W = 1600
WINDOW_H = 900
FPS      = 60

GAME_W = WINDOW_W - SIDEBAR_W      # 1280 px


def _update_layout(w: int, h: int):
    """Recalculate derived layout globals after a window resize."""
    global WINDOW_W, WINDOW_H, GAME_W, GAME_H, VIEWPORT_W, VIEWPORT_H
    WINDOW_W   = w
    WINDOW_H   = h
    GAME_W     = WINDOW_W - SIDEBAR_W
    GAME_H     = WINDOW_H - MSG_H
    VIEWPORT_W = GAME_W // TILE_SIZE
    VIEWPORT_H = GAME_H // TILE_SIZE

# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _cook_menu_bonus_label(recipe: dict) -> str:
    """Short bonus description for the cook menu."""
    bt     = recipe.get('bonus_type', 'none')
    amt    = recipe.get('bonus_amount', 0)
    stat   = recipe.get('bonus_stat', '')
    effect = recipe.get('bonus_effect', '')
    if bt == 'none' or amt == 0:
        return ''
    if bt == 'stat' and stat:
        return f"[+{amt} {stat}]"
    if bt == 'two_stats':
        return f"[+{amt} two stats]"
    if bt == 'all_stats':
        return f"[+{amt} ALL stats]"
    if bt == 'combat_stat':
        return f"[+{amt} STR/CON]"
    if bt == 'random_stat':
        return f"[+{amt} random stat]"
    if bt == 'status' and effect:
        return f"[{effect.replace('_',' ')} ×{amt}t]"
    return f"[+{amt}]"
MSG_H  = 200
GAME_H = WINDOW_H - MSG_H          # 700 px = 17 tiles

VIEWPORT_W = GAME_W // TILE_SIZE    # 32
VIEWPORT_H = GAME_H // TILE_SIZE    # 18

# ------------------------------------------------------------------
# Secret character builds
# Stat keys (STR/CON/DEX/INT/WIS/PER) override player defaults.
# _-prefixed keys are build metadata (ignored by the stat loop):
#   _sprite       → env sprite name (assets/tiles/env/{_sprite}.png)
#   _start_weapon → weapon item ID replacing the default iron_dagger
#   _start_wand   → wand item ID given at start
#   _start_book   → spellbook item ID given at start
#   _no_dagger    → True: skip the default iron_dagger
#   _immortal     → True: player cannot die
#   _greeting     → custom welcome message line (None = default)
# ------------------------------------------------------------------
SECRET_BUILDS: dict[str, dict] = {
    # ── Great philosophers — INT/WIS focused, physically frail ──────────────
    "aristotle": {
        "INT": 18, "WIS": 16, "PER": 14, "STR": 6, "CON": 8, "DEX": 8,
        "_sprite": "player_aristotle",
        "_greeting": "Aristotle the Philosopher enters the dungeon with calm reason.",
    },
    "socrates": {
        "WIS": 20, "INT": 14, "PER": 16, "STR": 8, "CON": 10, "DEX": 7,
        "_sprite": "player_socrates",
        "_greeting": "Socrates asks the dungeon a question. It does not answer.",
    },
    "plato": {
        "INT": 17, "WIS": 17, "PER": 12, "STR": 7, "CON": 9, "DEX": 9,
        "_sprite": "player_plato",
        "_greeting": "Plato descends into the cave and finds it uncomfortably on-the-nose.",
    },
    "nietzsche": {
        "INT": 16, "WIS": 8, "PER": 14, "STR": 14, "CON": 12, "DEX": 10,
        "_sprite": "player_nietzsche",
        "_greeting": "Nietzsche stares into the dungeon. The dungeon stares back.",
    },
    "pythagoras": {
        "INT": 18, "WIS": 14, "PER": 10, "STR": 7, "CON": 8, "DEX": 9,
        "_sprite": "player_pythagoras",
        "_greeting": "Pythagoras calculates the optimal descent angle.",
    },
    "prometheus": {
        "INT": 15, "WIS": 15, "CON": 15, "STR": 10, "DEX": 10, "PER": 10,
        "_sprite": "player_prometheus",
        "_greeting": "Prometheus brings fire into the dungeon. The monsters are unimpressed.",
    },
    "diogenes": {
        "WIS": 18, "PER": 16, "STR": 5, "CON": 5, "DEX": 5, "INT": 5,
        "_sprite": "player_diogenes",
        "_greeting": "Diogenes enters the dungeon. He needs nothing. He wants nothing. He is still going to die.",
    },
    # ── Warriors — brawn over brain ─────────────────────────────────────────
    "achilles": {
        "STR": 18, "DEX": 16, "CON": 16, "INT": 8, "WIS": 6, "PER": 10,
        "_sprite": "player_achilles",
        "_greeting": "Achilles charges in. His heel tingles ominously.",
    },
    "leonidas": {
        "STR": 17, "CON": 18, "DEX": 12, "INT": 9, "WIS": 10, "PER": 8,
        "_sprite": "player_leonidas",
        "_greeting": "Leonidas has 299 fewer soldiers than he would like.",
    },
    "alexander": {
        "STR": 16, "DEX": 14, "CON": 14, "INT": 14, "WIS": 10, "PER": 12,
        "_sprite": "player_alexander",
        "_greeting": "Alexander the Great descends. He intends to conquer this too.",
    },
    "theseus": {
        "STR": 14, "DEX": 14, "CON": 14, "INT": 12, "WIS": 12, "PER": 12,
        "_sprite": "player_theseus",
        "_greeting": "Theseus enters the dungeon. He has done this before.",
    },
    # ── Rogues — speed and perception ───────────────────────────────────────
    "hermes": {
        "DEX": 18, "PER": 18, "INT": 12, "WIS": 10, "STR": 8, "CON": 7,
        "_sprite": "player_hermes",
        "_greeting": "Hermes was here, delivered something, and left. He returned because he forgot to sign.",
    },
    "odysseus": {
        "DEX": 14, "INT": 16, "PER": 16, "WIS": 14, "STR": 10, "CON": 10,
        "_sprite": "player_odysseus",
        "_greeting": "Odysseus descends. He expects this to take ten years.",
    },
    # ── Mages — pure arcane power ────────────────────────────────────────────
    "merlin": {
        "INT": 20, "WIS": 14, "PER": 12, "STR": 5, "CON": 7, "DEX": 8,
        "_sprite": "player_merlin",
        "_no_dagger": True,
        "_start_wand": "wand_of_magic_missile",
        "_start_book": "spellbook_magic_missile",
        "_greeting": "Merlin descends with staff in hand and stars in his robe.",
    },
    # ── New characters ────────────────────────────────────────────────────────
    "corwin": {
        "STR": 11, "CON": 11, "DEX": 12, "INT": 8, "WIS": 10, "PER": 14,
        "_sprite": "player_ranger",
        "_no_dagger": True,
        "_start_weapon": "wood_shortbow",
        "_start_ammo": "iron_arrow",
        "_greeting": "Corwin the Ranger nocks an arrow and descends into the dark.",
    },
    "fianna": {
        "STR": 6, "CON": 8, "DEX": 12, "INT": 16, "WIS": 12, "PER": 10,
        "_sprite": "player_wizard_f",
        "_no_dagger": True,
        "_start_wand": "wand_of_magic_missile",
        "_start_book": "spellbook_magic_missile",
        "_greeting": "Fianna the Wizard weaves a sigil in the air and descends.",
    },
    "fluffs": {
        "STR": 7, "CON": 10, "DEX": 10, "INT": 18, "WIS": 14, "PER": 12,
        "_sprite": "player_wizard_f",   # same sprite as Fianna
        "_no_dagger": True,
        "_start_wand": "wand_of_magic_missile",
        "_start_book": "spellbook_magic_missile",
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
        "_greeting": "Robyn descends — sharp-eyed, soft-footed, and sharper-tongued than most.",
    },
}


# ------------------------------------------------------------------
# Welcome screen
# ------------------------------------------------------------------

class WelcomeScreen:
    """90s adventure-game-style welcome screen with domain art vortex."""

    _TITLE_LINE1 = "PHILOSOPHER'S"
    _TITLE_LINE2 = "QUEST"
    _PROMPT      = "Enter your name, seeker:"

    # (label, base_angle_deg, EGA-style color, quiz subject symbol)
    _DOMAINS = [
        ("MATH",       0,   (85, 255, 255), "∑"),
        ("GEOGRAPHY",  40,  (85, 255, 85),  "◈"),
        ("HISTORY",    80,  (255, 215, 0),  "Ω"),
        ("ANIMAL",     120, (255, 140, 0),  "☽"),
        ("COOKING",    160, (255, 85, 255), "⌘"),
        ("SCIENCE",    200, (85, 85, 255),  "✦"),
        ("PHILOSOPHY", 240, (200, 200, 255),"Φ"),
        ("GRAMMAR",    280, (255, 85, 85),  "¶"),
        ("ECONOMICS",  320, (170, 255, 0),  "◆"),
        ("THEOLOGY",   355, (200, 170, 80), "✝"),
    ]

    def __init__(self, screen: pygame.Surface):
        self.screen   = screen
        self.W, self.H = screen.get_size()
        self.cx = self.W // 2
        self.cy = self.H // 2
        # FANTASY: Replace consolas fonts with grimoire theme fonts
        self.font_xl   = get_font('title',   52, bold=True)
        self.font_lg   = get_font('heading', 32)
        self.font_md   = get_font('body',    20)
        self.font_sm   = get_font('body',    15)
        self.font_icon = get_font('gothic',  26)
        self.font_tiny = get_font('body',    12)
        self.name_buf    = ''
        self.cursor_on   = True
        self.cursor_timer = 0.0
        self._anim_t     = 0.0
        self._has_save   = False
        self._delete_flash = 0.0
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.name_buf.strip():
                        name  = self.name_buf.strip()
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
                    elif len(self.name_buf) < 24 and event.unicode.isprintable():
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

    def _draw_radial_glow(self, cx, cy):
        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for r, alpha in [(300, 12), (240, 18), (180, 22), (130, 28), (90, 20)]:
            pygame.draw.circle(glow, (30, 0, 80, alpha), (cx, cy), r)
        self.screen.blit(glow, (0, 0))

    def _draw_domain_ring(self, cx, cy, t):
        ring_r = min(cx, cy) * 0.52
        orbit_speed = 0.018   # radians/sec — very slow orbit
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
            # Inner highlight line (top and left — classic 90s bevel)
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

    def _draw_vortex(self, cx, cy, t):
        """Rotating spiral arms — the knowledge vortex."""
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
        """The Philosopher's Stone — pulsing golden gem."""
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
        # FANTASY: Illuminated manuscript title — gold text on midnight panel
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
            badge = self.font_sm.render("★  SECRET BUILD ACTIVE!", True, FP.GOLD_BRIGHT)
            self.screen.blit(badge, (cx - badge.get_width() // 2, by + box_h + 8))

    def _draw_footer(self, cx):
        has_save = getattr(self, '_has_save', False)
        text = "[ ENTER ] begin your quest     [ ESC ] quit"
        hint = self.font_tiny.render(text, True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.H - 28))
        # Delete-flash confirmation (shown for 2 seconds after DEL)
        flash = getattr(self, '_delete_flash', 0.0)
        if flash > 0.0:
            del_msg = self.font_sm.render("✗  Save deleted — press ENTER to start fresh", True, (220, 80, 80))
            self.screen.blit(del_msg, (cx - del_msg.get_width() // 2, self.H - 52))
        elif has_save:
            save_hint = self.font_sm.render("★  Saved journey found — ENTER to continue  |  DEL to erase", True, FP.SUCCESS_TEXT)
            self.screen.blit(save_hint, (cx - save_hint.get_width() // 2, self.H - 52))

        # High score mini-leaderboard (top 3)
        try:
            from highscore_system import get_top
            top = get_top(3)
            if top:
                hs_x = cx + 260
                hs_y = self.H - 140
                title_s = self.font_sm.render("BEST RUNS", True, FP.GOLD_DARK)
                self.screen.blit(title_s, (hs_x - title_s.get_width() // 2, hs_y))
                hs_y += 18
                for i, e in enumerate(top):
                    v_mark = "✦" if e.get('victory') else " "
                    line = f"{v_mark}{i+1}. {e.get('name','?'):<8}  {e['score']:>7,}  {e.get('grade','?'):>2}"
                    col = FP.GOLD if e.get('victory') else FP.FADED_TEXT
                    s = self.font_tiny.render(line, True, col)
                    self.screen.blit(s, (hs_x - s.get_width() // 2, hs_y))
                    hs_y += 16
        except Exception:
            pass


# Game states
STATE_PLAYER         = 'player'
STATE_QUIZ           = 'quiz'
STATE_EQUIP_MENU     = 'equip_menu'
STATE_ACCESSORY_MENU = 'accessory_menu'
STATE_WAND_MENU      = 'wand_menu'
STATE_SCROLL_MENU    = 'scroll_menu'
STATE_IDENTIFY_MENU  = 'identify_menu'
STATE_COOK_MENU      = 'cook_menu'
STATE_CONFIRM_EXIT   = 'confirm_exit'
STATE_VICTORY        = 'victory'
STATE_DEAD           = 'dead'
STATE_LOCKPICK       = 'lockpick'
STATE_TARGET         = 'target'        # ranged targeting cursor
STATE_EAT_MENU       = 'eat_menu'      # eat food / raw ingredient
STATE_QUAFF_MENU     = 'quaff_menu'   # quaff a potion
STATE_HELP           = 'help'
STATE_LORE           = 'lore'
STATE_PRAY           = 'pray'
STATE_SPELL_MENU     = 'spell_menu'
STATE_HINT           = 'hint'          # Recall Lore result display
STATE_EXAMINE        = 'examine'       # Examine identified inventory item
STATE_ENCYCLOPEDIA   = 'encyclopedia'  # Encyclopedia browser
STATE_DROP_MENU      = 'drop_menu'       # Drop an item from inventory
STATE_DROP_GOLD_INPUT = 'drop_gold_input' # Numeric prompt: how much gold to drop
STATE_STORY_POPUP    = 'story_popup'     # Narrative popup (quest intro, boss defeat, ending)
STATE_MYSTERY_APPROACH = 'mystery_approach'  # Player is approaching a mystery altar
STATE_SHOP             = 'shop'              # Merchant shop overlay

# ---------------------------------------------------------------------------
# Spells learnable from spellbooks  (spell_id → attributes)
# ---------------------------------------------------------------------------
LEARNABLE_SPELLS: dict[str, dict] = {
    'magic_missile_spell': {
        'name': 'Magic Missile', 'effect': 'magic_missile', 'power': '2d6',
        'mp_cost': 3,  'quiz_tier': 1, 'needs_target': True,
        'desc': 'Unerring force dart, 2d6 damage.',
    },
    'sleep_spell': {
        'name': 'Sleep', 'effect': 'sleep_monster', 'power': '',
        'mp_cost': 4,  'quiz_tier': 1, 'needs_target': True,
        'desc': 'Puts one monster to sleep for 6 turns.',
    },
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2,  'quiz_tier': 1, 'needs_target': False,
        'desc': 'Illuminate surroundings for 20 turns (+3 PER).',
    },
    'shield_spell': {
        'name': 'Magic Shield', 'effect': 'shield_self', 'power': '',
        'mp_cost': 5,  'quiz_tier': 2, 'needs_target': False,
        'desc': '+2 AC, physical damage halved for 12 turns.',
    },
    'fire_bolt_spell': {
        'name': 'Fire Bolt', 'effect': 'fire_bolt', 'power': '4d6',
        'mp_cost': 6,  'quiz_tier': 2, 'needs_target': True,
        'desc': 'Fire bolt, 4d6 damage.',
    },
    'haste_spell': {
        'name': 'Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 7,  'quiz_tier': 2, 'needs_target': False,
        'desc': 'Move twice per turn for 10 turns.',
    },
    'heal_spell': {
        'name': 'Heal', 'effect': 'extra_heal', 'power': '3d8',
        'mp_cost': 8,  'quiz_tier': 3, 'needs_target': False,
        'desc': 'Restore 3d8 HP (scales with chain score).',
    },
    'invisibility_spell': {
        'name': 'Invisibility', 'effect': 'invisibility_self', 'power': '',
        'mp_cost': 9,  'quiz_tier': 3, 'needs_target': False,
        'desc': 'Become invisible for 15 turns.',
    },
    'lightning_spell': {
        'name': 'Chain Lightning', 'effect': 'lightning_bolt', 'power': '5d6',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Lightning bolt, 5d6 arcing damage.',
    },
    'confusion_spell': {
        'name': 'Confusion', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 7,  'quiz_tier': 3, 'needs_target': True,
        'desc': 'Confuse a monster for 10 turns.',
    },
    'displacement_spell': {
        'name': 'Displacement', 'effect': 'displacement_self', 'power': '',
        'mp_cost': 12, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Attackers miss you 30% of time for 20 turns.',
    },
    'ice_storm_spell': {
        'name': 'Ice Storm', 'effect': 'mass_ice', 'power': '3d6',
        'mp_cost': 14, 'quiz_tier': 4, 'needs_target': False,
        'desc': '3d6 cold damage to all visible monsters.',
    },
    'paralyze_spell': {
        'name': 'Paralysis', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 12, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Paralyze a monster for 8 turns.',
    },
}


class Game:
    def __init__(self, screen: pygame.Surface,
                 player_name: str = 'Adventurer',
                 secret_build: dict | None = None):
        self.screen        = screen
        self.player_name   = player_name
        self.secret_build  = secret_build   # dict of stat overrides, or None
        # FANTASY: Grimoire font set — larger for readability
        self.font_sm   = get_font('body',    20)
        self.font_md   = get_font('body',    26)
        self.font_lg   = get_font('heading', 32)
        self.font_xl   = get_font('title',   42, bold=True)

        _snd.init()   # initialise procedural sound synthesis (best-effort)
        self.quiz_engine        = QuizEngine()
        self.msg_log            = MessageLog()
        self.sidebar            = Sidebar(screen, GAME_W)
        self.level_mgr          = LevelManager()
        self.state              = STATE_PLAYER
        self.combat_target      = None
        self.quiz_title         = ''
        self.equip_menu_items: list      = []
        self.equip_menu_equipped: list   = []   # (slot_name, item) pairs for unequip section
        self.accessory_menu_items: list  = []
        self.wand_menu_items: list       = []
        self.scroll_menu_items: list     = []
        self.spell_menu_items: list      = []   # list of spell_ids known to player
        self._lore_hint_text: str | None = None
        self._lore_hint_chain: int       = 0
        self._lore_subject: str | None   = None
        self.identify_menu_items: list   = []
        self.cook_menu_items: list       = []
        self.cook_compound_recipes: list = []   # available multi-ingredient recipes
        self.eat_menu_items: list        = []
        self.quaff_menu_items: list      = []
        self.examine_menu_items: list    = []   # identified items for examine menu
        self.encyclopedia_category: str  = ''   # current encyclopedia category
        self.encyclopedia_selection: int = 0    # selected index in list view
        self.encyclopedia_entries: list  = []   # current entry list
        self._encyclopedia_entry: object = None # currently viewed entry detail
        self.player_gold        = 0
        self.turn_count         = 0
        self.dungeon_level      = 1
        self.death_pursues      = False   # True once player ascends L100 with Stone
        self.death_monster      = None    # DeathMonster instance, persists across floors
        # Deep-lore item spawn levels (one item per range, chosen at game start)
        import random as _lore_rng
        self._lore_levels = {
            'shimmer':     _lore_rng.randint(1,  20),
            'wrench':      _lore_rng.randint(21, 49),
            'fire_scroll': _lore_rng.randint(50, 79),
            'tablet':      _lore_rng.randint(80, 99),
        }
        self._lore_placed: set = set()   # which have been placed this run
        self._notified_rooms: set = set()  # (cx, cy) of special rooms already notified
        # Drop-item state
        self.drop_menu_items: list = []
        self.drop_gold_input: str  = ''   # digit buffer for gold-drop amount prompt
        # Story popup state (quest intro, boss victory, endings)
        self.popup_data: dict | None = None     # title, lines, accent, code
        self.popup_next_state: str   = STATE_PLAYER
        self.defeat_reason      = 'died'   # 'died' | 'starved' | 'fled'
        self._save_on_quit      = True     # False when player explicitly exits without saving
        self.correct_answers    = 0        # total correct answers this run
        self.wrong_answers      = 0        # total wrong answers this run
        self._score_saved       = False    # True after high score is written
        self.quiz_engine.on_answer = self._on_quiz_answer
        self.quirk_system = QuirkSystem(self)
        self._slow_skip         = False    # toggled each turn when slowed
        # Key-held movement (arrow key auto-repeat)
        self._move_hold_timer   = 0.0      # countdown until next repeated move
        self._move_hold_delay   = 0.18     # seconds before repeat kicks in
        self._move_hold_first   = True     # True = waiting for initial delay
        # Targeting state (ranged attacks)
        self.target_cursor_x    = 0        # world tile position of targeting cursor
        self.target_cursor_y    = 0
        self._target_candidates: list = [] # visible monsters sorted by distance
        self._target_idx        = 0        # which candidate is selected
        # Mystery system state
        self._active_mystery_altar = None  # MysteryAltar being interacted with

        self._new_level(1)
        self._show_story_popup('dungeon_entrance', STATE_PLAYER)

    # ------------------------------------------------------------------
    # Message helper
    # ------------------------------------------------------------------

    def add_message(self, text: str, msg_type: str = 'info'):
        self.msg_log.add(text, msg_type)

    # ------------------------------------------------------------------
    # Level setup
    # ------------------------------------------------------------------

    def _new_level(self, level: int):
        """Initial game setup only — creates fresh player."""
        self.dungeon_level           = level
        dungeon, monsters, items     = self.level_mgr.generate(level)
        self.dungeon                 = dungeon
        self.monsters                = monsters
        self.ground_items            = items
        self.player                  = Player()

        # Apply secret build stat overrides (ignore _-prefixed metadata keys)
        b = self.secret_build or {}
        for stat, value in b.items():
            if not stat.startswith('_') and hasattr(self.player, stat):
                setattr(self.player, stat, value)
        if b:
            # Recompute derived stats after overrides (STR→max_sp, CON→max_hp, INT→max_mp)
            self.player.max_hp = self.player.BASE_HP + self.player.CON
            self.player.hp     = self.player.max_hp
            self.player.max_sp = self.player.BASE_SP + self.player.STR
            self.player.sp     = self.player.max_sp
            self.player.max_mp = self.player.BASE_MP + self.player.INT
            self.player.mp     = self.player.max_mp

        # Immortality flag
        self.player.immortal = bool(b.get('_immortal', False))

        self.player.x, self.player.y = dungeon.rooms[0].center
        self.renderer                = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
        self.renderer.set_dungeon(dungeon.width, dungeon.height, GAME_W, GAME_H)
        self._refresh_fov()

        # Give the player their Philosopher's Amulet and build-specific starting kit
        self._give_starting_amulet()

        # Greeting
        if b.get('_greeting'):
            self.add_message(b['_greeting'], 'success')
        else:
            self.add_message(f"Welcome, {self.player_name}!", 'success')
        self.add_message("Find the Philosopher's Stone and escape!", 'info')

    def load_state(self, state: dict):
        """Restore all game state from a previously saved dict (pickle)."""
        self.player        = state['player']
        self.player_name   = state['player_name']
        self.secret_build  = state.get('secret_build')
        self.turn_count    = state['turn_count']
        self.dungeon_level = state['dungeon_level']
        self.player_gold   = state['player_gold']
        self.level_mgr     = state['level_mgr']
        self.dungeon       = state['dungeon']
        self.monsters      = state['monsters']
        self.ground_items  = state['ground_items']
        self.renderer.set_dungeon(self.dungeon.width, self.dungeon.height, GAME_W, GAME_H)
        self._refresh_fov()
        self.add_message("Welcome back, seeker. Your journey continues…", 'success')

    def _change_level(self, new_level: int, enter_from_top: bool):
        """Transition between levels, preserving the player."""
        # Notify quirk system before level change (fast-exit check)
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_stairs_taken_fast()

        # Save current level state
        self.level_mgr.save(
            self.dungeon_level, self.dungeon, self.monsters, self.ground_items
        )

        # Load saved or generate fresh
        saved = self.level_mgr.load(new_level)
        if saved:
            dungeon, monsters, ground_items = saved
        else:
            dungeon, monsters, ground_items = self.level_mgr.generate(new_level)

        self.dungeon      = dungeon
        self.monsters     = monsters
        self.ground_items = ground_items
        self.dungeon_level = new_level
        self._notified_rooms = set()   # reset per-floor special room notifications
        self.renderer.set_dungeon(dungeon.width, dungeon.height, GAME_W, GAME_H)

        # Notify quirk system of stair use and floor entry
        _qs_stair = getattr(self, 'quirk_system', None)
        if _qs_stair:
            _qs_stair.on_stair_use(new_level)
            _qs_stair.on_floor_entered(new_level)
            # Orpheus: slow all monsters on floor entry
            if getattr(self.player, 'quirk_progress', {}).get('orpheus_active'):
                for m in self.monsters:
                    if m.alive:
                        m.status_effects['slowed'] = max(
                            m.status_effects.get('slowed', 0), 5)

        # Grant HP on every level transition
        self.player.on_level_change()

        # Place player at the stairs they came through
        _snd.play('level_change')
        if enter_from_top:
            self.player.x, self.player.y = dungeon.rooms[0].center
            self.add_message(f"You descend to level {new_level}.", 'info')
        else:
            self.player.x, self.player.y = dungeon.rooms[-1].center
            self.add_message(f"You ascend to level {new_level}.", 'info')

        # Place deep-lore items on their designated levels (once per run)
        self._maybe_place_lore_items(dungeon, new_level)

        # Death always enters from the stairs below when pursuing
        if self.death_pursues and self.death_monster is not None:
            self._place_death_on_level(dungeon)
            self.add_message("You hear the scrape of a scythe on stone below you…", 'danger')

        self._refresh_fov()

    def _give_starting_amulet(self):
        """Give the player their starting kit, adjusted for their secret build."""
        from items import load_items, Ammo
        b = self.secret_build or {}

        # ── Always: Philosopher's Amulet ──────────────────────────────────
        try:
            accessories = load_items('accessory')
            amulet = next((a for a in accessories if a.id == 'philosophers_amulet'), None)
            if amulet:
                amulet.identified = True
                self.player.inventory.append(amulet)
                self.player.known_item_ids.add('philosophers_amulet')
        except Exception:
            pass

        # ── Weapon: default dagger OR build override ──────────────────────
        no_dagger     = b.get('_no_dagger', False)
        start_weapon  = b.get('_start_weapon', None)
        try:
            weapons = load_items('weapon')
            if start_weapon:
                w = next((x for x in weapons if x.id == start_weapon), None)
                if w:
                    w.identified = True
                    self.player.inventory.append(w)
            elif not no_dagger:
                dagger = next((x for x in weapons if x.id == 'iron_dagger'), None)
                if dagger:
                    self.player.inventory.append(dagger)
        except Exception:
            pass

        # ── Ammo (rangers) ────────────────────────────────────────────────
        start_ammo = b.get('_start_ammo', None)
        if start_ammo:
            try:
                ammo_items = load_items('ammo')
                ammo = next((a for a in ammo_items if a.id == start_ammo), None)
                if ammo:
                    ammo.count = 20
                    self.player.inventory.append(ammo)
            except Exception:
                pass

        # ── Wand (mages/wizards) ──────────────────────────────────────────
        start_wand = b.get('_start_wand', None)
        if start_wand:
            try:
                wands = load_items('wand')
                wand = next((w for w in wands if w.id == start_wand), None)
                if wand:
                    wand.identified = True
                    self.player.inventory.append(wand)
            except Exception:
                pass

        # ── Spellbook (mages/wizards) ─────────────────────────────────────
        start_book = b.get('_start_book', None)
        if start_book:
            try:
                books = load_items('spellbook')
                book = next((bk for bk in books if bk.id == start_book), None)
                if book:
                    book.identified = True
                    self.player.inventory.append(book)
            except Exception:
                pass

        # ── Always: starting lockpick charges ────────────────────────────
        self.player.lockpick_charges += 5   # equivalent to one basic lockpick

        # ── Always: bread ration ──────────────────────────────────────────
        try:
            foods = load_items('food')
            ration = next((f for f in foods if f.id == 'bread_ration'), None)
            if ration:
                self.player.inventory.append(ration)
        except Exception:
            pass
        self.player.inventory.sort(key=lambda i: i.name.lower())

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )
        qs = getattr(self, 'quirk_system', None)
        if qs and self.player:
            total = sum(
                1 for row in self.dungeon.tiles
                for tile in row
                if tile != 0  # non-wall tiles
            )
            explored = len(self.dungeon.explored)
            if total > 0:
                qs.on_floor_explored(explored / total)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def on_resize(self, w: int, h: int):
        """Called after window is resized — syncs renderer and sidebar."""
        _update_layout(w, h)
        self.renderer.set_dungeon(
            self.dungeon.width, self.dungeon.height, GAME_W, GAME_H
        )
        self.sidebar.x = GAME_W

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.WINDOWRESIZED:
            self.on_resize(event.x, event.y)
            return True
        if event.type != pygame.KEYDOWN:
            return True

        key = event.key

        if key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return True

        if key == pygame.K_ESCAPE:
            if self.state in (STATE_EQUIP_MENU, STATE_ACCESSORY_MENU,
                              STATE_WAND_MENU, STATE_SCROLL_MENU,
                              STATE_IDENTIFY_MENU, STATE_COOK_MENU,
                              STATE_CONFIRM_EXIT, STATE_TARGET,
                              STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
                              STATE_SPELL_MENU, STATE_HINT,
                              STATE_EXAMINE, STATE_ENCYCLOPEDIA,
                              STATE_DROP_MENU, STATE_DROP_GOLD_INPUT,
                              STATE_MYSTERY_APPROACH, STATE_SHOP):
                if self.state == STATE_MYSTERY_APPROACH:
                    self._active_mystery_altar = None
                self.state = STATE_PLAYER
                return True
            if self.state == STATE_STORY_POPUP:
                self.state = self.popup_next_state
                return True
            if self.state == STATE_PLAYER:
                self.state = STATE_CONFIRM_EXIT
                return True
            if self.state in (STATE_DEAD, STATE_VICTORY):
                return False
            return False

        if self.state == STATE_PLAYER:
            # Keys checked by unicode to handle shift-modified chars
            if event.unicode == '>':
                self._descend_stairs()
                return True
            if event.unicode == '<':
                self._ascend_stairs()
                return True
            if event.unicode == '?':
                self.state = STATE_HELP
                return True
            self._player_input(key)
        elif self.state == STATE_TARGET:
            self._target_input(key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(key)
        elif self.state == STATE_EQUIP_MENU:
            self._equip_menu_input(key)
        elif self.state == STATE_ACCESSORY_MENU:
            self._accessory_menu_input(key)
        elif self.state == STATE_WAND_MENU:
            self._wand_menu_input(key)
        elif self.state == STATE_SCROLL_MENU:
            self._scroll_menu_input(key)
        elif self.state == STATE_SPELL_MENU:
            self._spell_menu_input(key)
        elif self.state == STATE_IDENTIFY_MENU:
            self._identify_menu_input(key)
        elif self.state == STATE_COOK_MENU:
            self._cook_menu_input(key)
        elif self.state == STATE_EAT_MENU:
            self._eat_menu_input(key)
        elif self.state == STATE_QUAFF_MENU:
            self._quaff_menu_input(key)
        elif self.state == STATE_HELP:
            self._help_input(key)
        elif self.state == STATE_LORE:
            self._lore_input(key)
        elif self.state == STATE_EXAMINE:
            self._examine_menu_input(key)
        elif self.state == STATE_ENCYCLOPEDIA:
            self._encyclopedia_input(key)
        elif self.state == STATE_HINT:
            self.state = STATE_PLAYER   # any key dismisses hint overlay
        elif self.state == STATE_DROP_MENU:
            self._drop_menu_input(key)
        elif self.state == STATE_DROP_GOLD_INPUT:
            self._drop_gold_input(key, event.unicode)
        elif self.state == STATE_STORY_POPUP:
            self.state = self.popup_next_state   # any key advances
        elif self.state == STATE_CONFIRM_EXIT:
            self._confirm_exit_input(key)
        elif self.state == STATE_MYSTERY_APPROACH:
            self._mystery_approach_input(key, event.unicode)
        elif self.state == STATE_SHOP:
            self._shop_input(key)

        return True

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
    }

    def _player_input(self, key: int):
        import random as _rng

        if key == pygame.K_PERIOD:
            qs = getattr(self, 'quirk_system', None)
            near = any(m.alive for m in self.monsters)
            if qs:
                qs.on_wait(near_monsters=near)
            # Meditation: restore 1 MP when waiting if no monsters are adjacent
            _adj_monsters = [
                m for m in self.monsters
                if m.alive and abs(m.x - self.player.x) <= 1 and abs(m.y - self.player.y) <= 1
            ]
            if not _adj_monsters and self.player.mp < self.player.max_mp:
                self.player.restore_mp(1)
                self.add_message("You meditate briefly. (+1 MP)", 'info')
            else:
                self.add_message("You wait.", 'info')
            self._advance_turn()
            return

        if key in (pygame.K_g, pygame.K_COMMA):
            self._pickup()
            return
        if key == pygame.K_e:
            self._open_equip_menu()
            return
        if key == pygame.K_r:
            self._open_scroll_menu()
            return
        if key == pygame.K_z:
            self._open_wand_menu()
            return
        if key == pygame.K_u:
            self._open_eat_menu()
            return
        if key == pygame.K_q:
            self._open_quaff_menu()
            return
        if key == pygame.K_m:
            self._open_spell_menu()
            return
        if key == pygame.K_s:
            self._open_accessory_menu()
            return
        if key == pygame.K_i:
            self._open_identify_menu()
            return
        if key == pygame.K_h:
            self._harvest()
            return
        if key == pygame.K_c:
            self._open_cook_menu()
            return
        if key == pygame.K_p:
            self._lockpick()
            return
        if key == pygame.K_a:
            self._attack_container()
            return
        if key == pygame.K_f:
            self._open_targeting()
            return
        if key == pygame.K_BACKSLASH:
            self._start_pray()
            return
        if key == pygame.K_n:
            self._start_recall_lore()
            return
        if key == pygame.K_SLASH or key == pygame.K_QUESTION:
            self.state = STATE_HELP
            return
        if key == pygame.K_x:
            self._open_examine_menu()
            return
        if key == pygame.K_b:
            self._open_encyclopedia()
            return
        if key == pygame.K_d:
            self._open_drop_menu()
            return
        if key == pygame.K_t:
            self._open_shop()
            return

        if key not in self._MOVE_KEYS:
            return

        self._do_move(*self._MOVE_KEYS[key])

    def _do_move(self, dx: int, dy: int):
        """Attempt a player move/action in direction (dx, dy)."""
        if self.state != STATE_PLAYER:
            return

        # Feared: force movement away from nearest visible monster
        if self.player.has_effect('feared'):
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            if visible_monsters:
                nearest = min(visible_monsters, key=lambda m: abs(m.x - self.player.x) + abs(m.y - self.player.y))
                flee_dx = 0 if nearest.x == self.player.x else (-1 if nearest.x > self.player.x else 1)
                flee_dy = 0 if nearest.y == self.player.y else (-1 if nearest.y > self.player.y else 1)
                dx, dy = flee_dx, flee_dy
                self.add_message("You flee in terror!", 'danger')

        # Sleep: skip turn
        if self.player.has_effect('sleeping'):
            self.add_message("You are fast asleep!", 'warning')
            self._advance_turn()
            return

        # Paralyzed: skip turn
        if self.player.has_effect('paralyzed'):
            self.add_message("You are paralyzed and cannot move!", 'danger')
            self._advance_turn()
            return

        # Slowed: skip every other turn
        if self.player.has_effect('slowed'):
            self._slow_skip = not self._slow_skip
            if self._slow_skip:
                self.add_message("You move sluggishly.", 'warning')
                self._advance_turn()
                return

        # Fumbling: 20% chance to waste turn
        if self.player.has_effect('fumbling') and _rng.random() < 0.20:
            self.add_message("You stumble and waste your turn!", 'warning')
            self._advance_turn()
            return

        # Stunned: 25% chance to fail
        if self.player.has_effect('stunned') and _rng.random() < 0.25:
            self.add_message("You are too dazed to act!", 'warning')
            self._advance_turn()
            return

        # Confused: randomize direction
        if self.player.has_effect('confused'):
            dx, dy = random.choice(
                [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(1,-1),(1,1)]
            )
            self.add_message("You stumble in a random direction!", 'warning')

        nx, ny = self.player.x + dx, self.player.y + dy

        target = next(
            (m for m in self.monsters if m.alive and m.x == nx and m.y == ny), None
        )
        if not self.dungeon.in_bounds(nx, ny):
            return

        tile_at_dest = self.dungeon.tiles[ny][nx]

        if target:
            self._start_combat(target)
        elif tile_at_dest == DOOR:
            # Bump-to-open: open the door and step through in one action
            self.dungeon.open_door(nx, ny)
            self.player.x, self.player.y = nx, ny
            self._check_floor_trap(nx, ny)
            _qs_move = getattr(self, 'quirk_system', None)
            if _qs_move:
                _qs_move.on_move()
            self._refresh_fov()
            _snd.play('door')
            self.add_message("You open the door.", 'info')
            self._tick_sp()
            if self.state != STATE_DEAD:
                self._notify_stairs(nx, ny)
                self._notify_ground(nx, ny)
                self._advance_turn()
        elif tile_at_dest == SECRET_DOOR:
            # Bump reveals secret door (chance based on PER)
            per_chance = min(0.85, 0.3 + self.player.PER * 0.04)
            if _rng.random() < per_chance:
                self.dungeon.tiles[ny][nx] = DOOR
                self._refresh_fov()
                self.add_message("You find a secret door!", 'success')
            else:
                self.add_message("You feel something odd about this wall...", 'info')
            self._advance_turn()
        elif self.dungeon.is_walkable(nx, ny) or (
            self.player.has_effect('phasing') and self.dungeon.in_bounds(nx, ny)
        ):
            self.player.x, self.player.y = nx, ny
            self._check_floor_trap(nx, ny)
            _qs_walk = getattr(self, 'quirk_system', None)
            if _qs_walk:
                _qs_walk.on_move()
            # Sisyphus boulder challenge tracking
            if self.player.quirk_progress.get('sisyphus_boulder_active'):
                _has_boulder = any(
                    getattr(i, 'mystery_id', None) == 'sisyphus'
                    for i in self.player.inventory
                )
                if _has_boulder and self.player.get_current_weight() > self.player.get_carry_limit():
                    self.player.quirk_progress['sisyphus_boulder_tiles'] = (
                        self.player.quirk_progress.get('sisyphus_boulder_tiles', 0) + 1
                    )
                    _sis_tiles = self.player.quirk_progress['sisyphus_boulder_tiles']
                    if _sis_tiles >= 25:
                        _boulder = next(
                            (i for i in self.player.inventory
                             if getattr(i, 'mystery_id', None) == 'sisyphus'), None
                        )
                        if _boulder:
                            self.player.inventory.remove(_boulder)
                        from mystery_system import apply_mystery_reward
                        apply_mystery_reward('sisyphus', self.player, self, True)
                        self.player.quirk_progress['sisyphus_boulder_active'] = False
                    elif _sis_tiles % 5 == 0:
                        self.add_message(
                            f"The boulder weighs you down. {25 - _sis_tiles} tiles remain.", 'warning'
                        )
                elif not _has_boulder:
                    self.player.quirk_progress['sisyphus_boulder_active'] = False
            self._refresh_fov()
            self._tick_sp()
            if self.state != STATE_DEAD:
                self._notify_stairs(nx, ny)
                self._notify_ground(nx, ny)
                self._advance_turn()
                # Haste: grant a free second step in the same direction
                if (self.player.has_effect('hasted') and self.state == STATE_PLAYER
                        and not getattr(self, '_haste_active', False)):
                    self.add_message("You move with supernatural speed!", 'info')
                    self._haste_active = True
                    self._do_move(dx, dy)
                    self._haste_active = False

    def _notify_stairs(self, x: int, y: int):
        tile = self.dungeon.tiles[y][x]
        if tile == STAIRS_DOWN:
            self.add_message("Stairs lead down here  —  press '>' to descend.", 'info')
        elif tile == STAIRS_UP:
            if self.dungeon_level == 1:
                self.add_message("The dungeon exit  —  press '<' to leave.", 'warning')
            else:
                self.add_message("Stairs lead up here  —  press '<' to ascend.", 'info')
        elif tile == ALTAR:
            self.add_message("A sacred altar stands here. Press '\\' to pray with divine bonus.", 'info')

    def _display_name(self, item) -> str:
        """Return the name to show for an item — unidentified name if not yet identified."""
        if not getattr(item, 'identified', True):
            # Also treat as identified if this item type has been seen before this run
            if hasattr(self, 'player') and item.id in self.player.known_item_ids:
                return item.name
            return getattr(item, 'unidentified_name', item.name)
        return item.name

    def _notify_ground(self, x: int, y: int):
        """Print messages about items and notable features at (x, y)."""
        # Special room notification (once per room per floor)
        _SPECIAL_ROOM_MSGS = {
            'treasury':    ("You enter a treasure vault — riches gleam in the darkness!", 'success'),
            'library':     ("You enter an ancient library — scrolls line the walls.", 'info'),
            'shrine':      ("You enter a sacred shrine — you feel the presence of higher powers.", 'info'),
            'monster_den': ("You enter a monster den — the stench of creatures fills the air!", 'danger'),
        }
        for (rcx, rcy), rtype in self.dungeon.special_rooms.items():
            if (rcx, rcy) not in self._notified_rooms:
                # Check if player entered any room that contains this center
                for room in self.dungeon.rooms:
                    rx1 = room.x
                    ry1 = room.y
                    rx2 = room.x + room.width - 1
                    ry2 = room.y + room.height - 1
                    if rx1 <= x <= rx2 and ry1 <= y <= ry2:
                        cx, cy = room.center
                        if (cx, cy) == (rcx, rcy):
                            self._notified_rooms.add((rcx, rcy))
                            msg, style = _SPECIAL_ROOM_MSGS.get(rtype, ("You enter a special room.", 'info'))
                            self.add_message(msg, style)
                            break

        here = [item for item in self.ground_items if item.x == x and item.y == y]
        # Abyssal Shimmer: show the inscription when stepped upon
        shimmer = next((i for i in here if i.id == 'abyssal_shimmer'), None)
        if shimmer:
            if shimmer.activated:
                self.add_message(
                    "The ground roils with abyssal energy — something is ready.", 'danger'
                )
            else:
                self.add_message("The ground shimmers with ancient power.", 'info')
                self.add_message("\u201cRevelation 20:14\u201d", 'info')
            here = [i for i in here if i is not shimmer]   # don't double-list it
        if len(here) == 1:
            item = here[0]
            dname = self._display_name(item)
            article = 'an' if dname[0].lower() in 'aeiou' else 'a'
            self.add_message(f"You see {article} {dname} lying here.", 'info')
        elif len(here) == 2:
            self.add_message(
                f"You see {self._display_name(here[0])} and "
                f"{self._display_name(here[1])} lying here.", 'info'
            )
        elif len(here) > 2:
            self.add_message(
                f"You see {len(here)} items here: "
                + ', '.join(self._display_name(i) for i in here[:3])
                + ('...' if len(here) > 3 else '.'),
                'info'
            )

    # ------------------------------------------------------------------
    # Stair navigation
    # ------------------------------------------------------------------

    def _descend_stairs(self):
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_DOWN:
            self.add_message("There are no stairs leading down here.", 'info')
            return
        self._change_level(self.dungeon_level + 1, enter_from_top=True)

    def _ascend_stairs(self):
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_UP:
            self.add_message("There are no stairs leading up here.", 'info')
            return
        if self.dungeon_level == 1:
            self.state = STATE_CONFIRM_EXIT
        else:
            # Trigger Death the moment the player leaves L100 carrying the Stone
            # (either the raw stone or the stone embedded in the complete tablet)
            if self.dungeon_level == 100 and not self.death_pursues:
                has_stone = any(
                    isinstance(i, Artifact) and i.id in ('philosophers_stone',
                                                          'complete_tablet_of_second_death')
                    for i in self.player.inventory
                )
                if has_stone:
                    self._trigger_death_pursuit()
            self._change_level(self.dungeon_level - 1, enter_from_top=False)

    def _trigger_death_pursuit(self):
        from monster import DeathMonster
        self.death_pursues  = True
        self.death_monster  = DeathMonster()
        self.add_message(
            "The dungeon shudders. A bone-cold wind rises from the deep.", 'danger'
        )
        self.add_message(
            "DEATH has come for the Stone.  Flee — or be reaped.", 'danger'
        )

    def _place_death_on_level(self, dungeon):
        """Spawn Death near the down-stairs (rooms[-1]) of the given dungeon."""
        d = self.death_monster
        cx, cy = dungeon.rooms[-1].center
        # Try tiles radiating out from the down-stair room center
        for dist in range(1, 8):
            for ddx, ddy in [(dist,0),(-dist,0),(0,dist),(0,-dist),
                             (dist,dist),(dist,-dist),(-dist,dist),(-dist,-dist)]:
                nx, ny = cx + ddx, cy + ddy
                if not dungeon.in_bounds(nx, ny):
                    continue
                if dungeon.is_walkable(nx, ny) and (nx, ny) != (self.player.x, self.player.y):
                    d.x, d.y = nx, ny
                    d.alive   = True
                    return
        # Fallback: same tile as room centre (rare)
        d.x, d.y = cx, cy
        d.alive   = True

    def _use_philosophers_wrench(self):
        """Combine the Philosopher's Stone and the Tablet of Second Death if both are held."""
        from items import Artifact, make_complete_tablet
        stone  = next((i for i in self.player.inventory
                       if isinstance(i, Artifact) and i.id == 'philosophers_stone'), None)
        tablet = next((i for i in self.player.inventory
                       if i.id == 'tablet_of_second_death'), None)
        if stone and tablet:
            self.player.remove_from_inventory(stone)
            self.player.remove_from_inventory(tablet)
            complete = make_complete_tablet(self.player.x, self.player.y)
            complete.x, complete.y = 0, 0   # inventory item — position doesn't matter
            self.player.inventory.append(complete)
            self.add_message(
                "The Wrench fits perfectly around the Stone.", 'success'
            )
            self.add_message(
                "With a firm turn, the Philosopher's Stone locks into the Tablet.", 'success'
            )
            self.add_message(
                "You hold the Complete Tablet of Second Death.", 'loot'
            )
        else:
            self.add_message(
                "The wrench socket seems to need something to fit in it.", 'info'
            )

    def _maybe_place_lore_items(self, dungeon, level: int):
        """Spawn each deep-lore item on its designated level (once per run)."""
        from items import (make_abyssal_shimmer, make_philosophers_wrench,
                           make_scroll_lake_of_fire, make_tablet_of_second_death)
        import random as _rng

        lore_map = {
            'shimmer':     (self._lore_levels['shimmer'],     make_abyssal_shimmer),
            'wrench':      (self._lore_levels['wrench'],      make_philosophers_wrench),
            'fire_scroll': (self._lore_levels['fire_scroll'], make_scroll_lake_of_fire),
            'tablet':      (self._lore_levels['tablet'],      make_tablet_of_second_death),
        }
        for key, (target_level, factory) in lore_map.items():
            if level == target_level and key not in self._lore_placed:
                # Pick a random walkable floor tile that isn't the player start or stairs
                candidates = []
                for room in dungeon.rooms[1:-1] or dungeon.rooms:
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            tx, ty = room.center[0] + dx, room.center[1] + dy
                            if dungeon.in_bounds(tx, ty) and dungeon.is_walkable(tx, ty):
                                candidates.append((tx, ty))
                if candidates:
                    tx, ty = _rng.choice(candidates)
                    item = factory(tx, ty)
                    self.ground_items.append(item)
                    self._lore_placed.add(key)

    def _trigger_abyss(self, shimmer):
        """The Abyss opens and reclaims Death. The secret victory condition."""
        from items import make_death_bane_scroll
        dx, dy = shimmer.x, shimmer.y

        self.add_message("The ancient words echo through the dungeon…", 'danger')
        self.add_message(
            '"Then Death and Hades were thrown into the lake of fire."', 'danger'
        )
        self.add_message(
            "The Shimmer tears open — a vast Abyss of black fire yawns beneath Death's feet.", 'danger'
        )
        self.add_message(
            "Death writhes, claws at the stone — and is consumed.", 'danger'
        )
        self.add_message(
            "What no soul before you has ever achieved:  DEATH IS DEAD.", 'success'
        )
        self.add_message(
            "Take this code to your father proudly — you have shown true Wisdom and Courage.", 'success'
        )
        self.add_message("\u2605 A scroll materializes from the void. \u2605", 'loot')

        # Destroy Death
        self.death_pursues = False
        self.death_monster = None

        # Drop the sixth boss reward scroll
        reward = make_death_bane_scroll(dx, dy)
        self.ground_items.append(reward)

        # Remove the Shimmer (the Abyss has closed)
        self.ground_items = [g for g in self.ground_items if g.id != 'abyssal_shimmer']

    def _death_proximity_warning(self):
        """Emit atmospheric messages based on how close Death is."""
        if not self.death_pursues or self.death_monster is None:
            return
        dm = self.death_monster
        dist = abs(dm.x - self.player.x) + abs(dm.y - self.player.y)
        # Only warn when Death enters FOV
        if (dm.x, dm.y) not in self.visible:
            return
        if dist <= 3:
            self.add_message("Death looms over you — MOVE!", 'danger')
        elif dist <= 6:
            self.add_message("Death draws near.", 'danger')

    def _confirm_exit_input(self, key: int):
        if key in (pygame.K_y, pygame.K_RETURN):
            # Save & exit cleanly — auto-save runs in main() after the loop
            self._save_on_quit = True
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key == pygame.K_n:
            # Exit without saving — delete any existing save to prevent checkpointing
            self._save_on_quit = False
            from save_system import delete_save
            delete_save(self.player_name)
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key in (pygame.K_ESCAPE, pygame.K_c):
            self.state = STATE_PLAYER

    def _do_exit(self):
        has_stone = any(
            isinstance(i, Artifact) and i.id in ('philosophers_stone',
                                                   'complete_tablet_of_second_death')
            for i in self.player.inventory
        )
        self._on_game_over()
        if has_stone:
            self._show_story_popup('exit_with_stone', STATE_VICTORY)
        else:
            self.defeat_reason = 'fled'
            self._show_story_popup('exit_without_stone', STATE_DEAD)

    def _on_game_over(self):
        """Delete save file on any game-ending event (permadeath)."""
        from save_system import delete_save
        delete_save(self.player_name)
        _snd.play('death')

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _calc_score(self) -> int:
        has_stone = any(
            isinstance(i, Artifact) and i.id in ('philosophers_stone',
                                                   'complete_tablet_of_second_death')
            for i in self.player.inventory
        )
        return (
            self.turn_count * 10
            + self.level_mgr.max_level_reached * 1000
            + self.level_mgr.monsters_killed * 100
            + (50000 if has_stone else 0)
        )

    def _get_grade(self, score: int) -> tuple[str, tuple]:
        """Return (letter_grade, color) based on final score."""
        if score >= 200_000: return 'S',  (255, 230,  80)
        if score >= 100_000: return 'A+', (220, 200,  60)
        if score >=  60_000: return 'A',  (200, 180,  50)
        if score >=  30_000: return 'B+', (140, 220, 140)
        if score >=  15_000: return 'B',  (100, 190, 100)
        if score >=   7_000: return 'C',  (120, 160, 220)
        if score >=   3_000: return 'D',  (180, 140,  80)
        return 'F', (180, 60, 60)

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------

    def _advance_turn(self):
        self.turn_count += 1

        qs = getattr(self, 'quirk_system', None)
        if qs and self.player:
            qs.on_turn()

        # Decrement prayer cooldown
        if self.player.prayer_cooldown > 0:
            self.player.prayer_cooldown -= 1

        # Decrement recall lore cooldown
        if self.player.recall_lore_cooldown > 0:
            self.player.recall_lore_cooldown -= 1

        # Tick all player status effects
        effect_msgs = self.player.tick_effects()
        for text, mtype in effect_msgs:
            if text == '_teleport':
                self._teleport_player()
            elif text == '_petrify_death':
                self.defeat_reason = 'died'
                self._on_game_over()
                self.state = STATE_DEAD
                self.add_message("You have turned completely to stone!", 'danger')
            else:
                self.add_message(text, mtype)

        if self.state == STATE_DEAD:
            return

        # Warning: alert for nearby monsters
        self._do_warning()
        # Searching: auto-reveal adjacent tiles
        self._do_searching()
        # Passive PER-based secret door detection
        self._do_passive_search()
        # Clairvoyant: reveal tiles within 10-tile radius each turn
        if self.player.has_effect('clairvoyant'):
            px, py = self.player.x, self.player.y
            for cy in range(max(0, py - 10), min(self.dungeon.height, py + 11)):
                for cx in range(max(0, px - 10), min(self.dungeon.width, px + 11)):
                    if abs(cx - px) + abs(cy - py) <= 10:
                        self.dungeon.explored.add((cx, cy))

        self._do_monster_turns()
        self._maybe_wander_spawn()
        self._death_proximity_warning()
        self._tick_hp_regen()

    def _maybe_wander_spawn(self):
        """Periodically spawn a wandering monster to keep pressure on the player."""
        import random as _rng
        # Spawn every 18-30 turns; more frequently at deeper levels
        interval = max(12, 28 - self.dungeon_level // 5)
        if self.turn_count % interval != 0:
            return
        # Cap active monsters: don't overpopulate
        alive = sum(1 for m in self.monsters if m.alive)
        max_alive = min(4 + self.dungeon_level // 6, 14)
        if alive >= max_alive:
            return
        # Spawn on an explored but currently non-visible tile, away from player
        px, py = self.player.x, self.player.y
        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        candidates = [
            (x, y) for (x, y) in self.dungeon.explored
            if self.dungeon.is_walkable(x, y)
            and (x, y) not in self.visible
            and (x, y) not in occupied
            and abs(x - px) + abs(y - py) >= 8
        ]
        if not candidates:
            return
        x, y = _rng.choice(candidates)
        from dungeon import spawn_monsters
        new_monsters = spawn_monsters(self.dungeon.rooms, self.dungeon_level,
                                      self.dungeon, min_count=1, max_count=1)
        if new_monsters:
            m = new_monsters[0]
            m.x, m.y = x, y
            self.monsters.append(m)

    def _check_floor_trap(self, x: int, y: int):
        """Trigger a floor trap at (x, y) if one exists."""
        from dice import roll as _dice_roll
        trap = self.dungeon.traps.get((x, y))
        if trap is None:
            return
        # Levitating players float over traps (reveals them)
        if self.player.has_effect('levitating'):
            trap['revealed'] = True
            self.add_message("You float safely over a trap!", 'info')
            return
        # Trap fires — remove it from the floor
        del self.dungeon.traps[(x, y)]
        trap_type = trap['type']
        _snd.play('trap')
        self.add_message(trap['message'], 'danger')
        dmg_str = str(trap.get('damage', '0'))
        if dmg_str != '0' and dmg_str:
            raw = _dice_roll(dmg_str)
            actual = self.player.take_damage(raw, trap.get('damage_type', 'physical'))
            if actual:
                self.add_message(f"You take {actual} damage!", 'danger')
        if trap_type == 'alarm':
            for m in self.monsters:
                if m.alive and abs(m.x - x) <= 10 and abs(m.y - y) <= 10:
                    if m.ai_pattern == 'sessile':
                        m.ai_pattern = 'aggressive'
            self.add_message("Monsters nearby are alerted!", 'danger')
        elif trap_type == 'acid':
            self.player.add_effect('corroding', 5)
            self.add_message("You feel acid eating at your equipment!", 'danger')
        elif trap_type == 'teleport':
            self._teleport_player()
        qs = getattr(self, 'quirk_system', None)
        if qs and hasattr(qs, 'on_trap_triggered'):
            qs.on_trap_triggered(trap_type)
        if self.player.is_dead():
            self.add_message("You have died!", 'danger')
            self.state = STATE_DEAD

    def _teleport_player(self):
        import random as _rng
        floors = [
            (x, y)
            for y in range(self.dungeon.height)
            for x in range(self.dungeon.width)
            if self.dungeon.is_walkable(x, y)
            and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
        ]
        if floors:
            self.player.x, self.player.y = _rng.choice(floors)
            self._refresh_fov()
            self.add_message("You feel disoriented as space warps around you!", 'warning')
            _qs_tp = getattr(self, 'quirk_system', None)
            if _qs_tp:
                _qs_tp.on_teleport()

    def _do_warning(self):
        """Warn if monsters are within 5 tiles when player has the warning effect."""
        if not self.player.has_effect('warning'):
            return
        px, py = self.player.x, self.player.y
        nearby = [
            m for m in self.monsters
            if m.alive and abs(m.x - px) <= 5 and abs(m.y - py) <= 5
            and (m.x, m.y) not in self.visible
        ]
        if nearby:
            self.add_message(
                f"Your danger sense tingles! ({len(nearby)} unseen threat{'s' if len(nearby) > 1 else ''} near)",
                'warning'
            )

    def _do_searching(self):
        """Auto-reveal adjacent tiles and secret doors when player is searching."""
        if not self.player.has_effect('searching'):
            return
        px, py = self.player.x, self.player.y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.dungeon.width and 0 <= ny < self.dungeon.height:
                    self.dungeon.explored.add((nx, ny))
                    if self.dungeon.tiles[ny][nx] == SECRET_DOOR:
                        self.dungeon.tiles[ny][nx] = DOOR
                        self._refresh_fov()
                        self.add_message("Searching reveals a secret door!", 'success')

    def _do_passive_search(self):
        """Passive PER-based detection of adjacent secret doors each turn."""
        import random as _rng
        # Small base chance + PER scaling; much weaker than bump or active Searching
        chance = 0.02 + self.player.PER * 0.008  # PER 10 = 10%, max ~18%
        px, py = self.player.x, self.player.y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if self.dungeon.tiles[ny][nx] == SECRET_DOOR:
                    if _rng.random() < chance:
                        self.dungeon.tiles[ny][nx] = DOOR
                        self._refresh_fov()
                        self.add_message("Your keen senses detect a hidden door nearby!", 'success')

    # ------------------------------------------------------------------
    # SP starvation
    # ------------------------------------------------------------------

    def _tick_sp(self):
        if self.player.sp > 0:
            self.player.sp -= 1
            if self.player.sp == 0:
                self.add_message("You are hungry! Find food before you starve.", 'warning')
        else:
            dmg = self.player.take_damage(1, 'starvation')
            self.add_message(f"Starving! You take {dmg} damage.", 'danger')
            if self.player.is_dead():
                self.defeat_reason = 'starved'
                self._on_game_over()
                self.state = STATE_DEAD
                self.add_message("You have starved to death! Press ESC to quit.", 'danger')

    # ------------------------------------------------------------------
    # Passive HP regeneration
    # ------------------------------------------------------------------

    def _tick_hp_regen(self):
        """Regen 1 HP every 15 turns (faster with high CON). Blocked by bleeding/poisoned."""
        if self.player.hp >= self.player.max_hp:
            return
        if self.player.has_effect('bleeding') or self.player.has_effect('poisoned'):
            return
        # CON above 12 shaves 1 turn off the interval per point; floor at 10
        interval = max(10, 20 - max(0, self.player.CON - 12))
        if self.turn_count % interval == 0:
            self.player.restore_hp(1)

    # ------------------------------------------------------------------
    # Pickup
    # ------------------------------------------------------------------

    def _pickup(self):
        from items import GoldPile
        from mystery_system import MysteryAltar
        px, py = self.player.x, self.player.y
        # Skip the Abyssal Shimmer — it's fixed to the floor
        # Also skip MysteryAltar objects (not_pickable=True)
        item = next(
            (i for i in self.ground_items
             if i.x == px and i.y == py
             and i.id != 'abyssal_shimmer'
             and not getattr(i, 'not_pickable', False)),
            None
        )
        if item is None:
            # Check if there's a non-pickable item here (altar) and tell the player
            altar_here = next(
                (i for i in self.ground_items
                 if i.x == px and i.y == py and getattr(i, 'not_pickable', False)),
                None
            )
            if altar_here:
                self.add_message(f"The {altar_here.name} cannot be moved.", 'info')
                return
            any_here = any(i for i in self.ground_items if i.x == px and i.y == py)
            if not any_here:
                self.add_message("There is nothing here to pick up.", 'info')
            return
        if isinstance(item, GoldPile):
            if not hasattr(self, 'player_gold'):
                self.player_gold = 0
            self.player_gold += item.amount
            self.ground_items.remove(item)
            self.add_message(f"You pick up {item.amount} gold coins.", 'loot')
            _snd.play('gold')
            self._advance_turn()
            return
        if isinstance(item, Lockpick):
            # Lockpicks convert directly to charges — never enter inventory
            charges = getattr(item, 'max_durability', 5)
            self.player.lockpick_charges = getattr(self.player, 'lockpick_charges', 0) + charges
            self.ground_items.remove(item)
            self.add_message(
                f"You pocket the {item.name}. (+{charges} lockpick charges, "
                f"total: {self.player.lockpick_charges})", 'loot'
            )
            self._advance_turn()
            return
        if self.player.add_to_inventory(item):
            self.ground_items.remove(item)
            _snd.play('pickup')
            if isinstance(item, Ammo):
                self.add_message(f"You pick up {item.count} {self._display_name(item)}s.", 'loot')
            else:
                self.add_message(f"You pick up the {self._display_name(item)}.", 'loot')
            if isinstance(item, Artifact) and item.id == 'philosophers_stone':
                self.add_message(
                    "The Philosopher's Stone! Return to the surface to win!", 'loot'
                )
            self._advance_turn()
        else:
            self.add_message("You are carrying too much to pick that up.", 'warning')

    # ------------------------------------------------------------------
    # Lockpicking
    # ------------------------------------------------------------------

    def _find_adjacent_container(self):
        """Return a Container on the player's tile or any adjacent tile, or None."""
        px, py = self.player.x, self.player.y
        for item in self.ground_items:
            if not isinstance(item, Container) or item.opened:
                continue
            if abs(item.x - px) <= 1 and abs(item.y - py) <= 1:
                return item
        return None

    def _lockpick(self):
        container = self._find_adjacent_container()
        if container is None:
            self.add_message("There is no container to pick nearby.", 'info')
            return

        # Mimic springs out on first interaction
        if container.is_mimic:
            self.add_message(
                f"The {container.name} springs to life — it's a MIMIC!", 'danger'
            )
            from container_system import _spawn_mimic
            _spawn_mimic(container, self.monsters)
            self.ground_items.remove(container)
            self._advance_turn()
            return

        if getattr(self.player, 'lockpick_charges', 0) <= 0:
            self.add_message("You have no lockpick charges.", 'warning')
            return

        self.quiz_title = (
            f"PICKING {container.name.upper()}  —  ECONOMICS  "
            f"(tier {container.tier}, need {container.quiz_threshold} correct)"
        )
        self.state = STATE_QUIZ

        def on_complete(result: dict):
            self.state = STATE_PLAYER
            for text, mtype in result['messages']:
                self.add_message(text, mtype)

            if result['status'] == 'opened':
                # Remove container, scatter loot at its position
                cx, cy = container.x, container.y
                self.ground_items.remove(container)
                for loot_item in result['loot']:
                    loot_item.x, loot_item.y = cx, cy
                    self.ground_items.append(loot_item)
                    self.add_message(f"You find {self._display_name(loot_item)}!", 'loot')
                if result['gold'] > 0:
                    from items import GoldPile
                    self.ground_items.append(GoldPile(result['gold'], cx, cy))
            elif result['status'] == 'failed':
                _qs_lock = getattr(self, 'quirk_system', None)
                if _qs_lock and getattr(container, 'trapped', False):
                    _qs_lock.on_lockpick_fail(container.id, self.dungeon_level)
                # Trap trigger check
                if _qs_lock and getattr(container, 'trap', None):
                    trap_type = container.trap.get('type', '') if isinstance(container.trap, dict) else ''
                    if trap_type:
                        _qs_lock.on_trap_triggered(trap_type)

            self._advance_turn()

        attempt_lockpick(
            self.player, container,
            self.quiz_engine, self.dungeon, self.monsters,
            on_complete
        )

    def _find_adjacent_mystery_altar(self):
        """Return a MysteryAltar on the player's tile or any adjacent tile, or None."""
        from mystery_system import MysteryAltar
        px, py = self.player.x, self.player.y
        for item in self.ground_items:
            if not isinstance(item, MysteryAltar):
                continue
            if item.activated:
                continue
            if abs(item.x - px) <= 1 and abs(item.y - py) <= 1:
                return item
        return None

    def _attack_container(self):
        """Press 'a' to interact with an adjacent mystery altar or probe a container for mimics."""
        # Check for mystery altar first
        altar = self._find_adjacent_mystery_altar()
        if altar is not None:
            self._start_mystery(altar)
            return

        container = self._find_adjacent_container()
        if container is None:
            self.add_message("There is nothing to interact with nearby.", 'info')
            return
        if container.is_mimic:
            self.add_message(
                f"The {container.name} springs to life — it's a MIMIC!", 'danger'
            )
            from container_system import _spawn_mimic
            _spawn_mimic(container, self.monsters)
            self.ground_items.remove(container)
        else:
            self.add_message(
                f"You strike the {container.name}. It's solid — just a chest.", 'info'
            )
        self._advance_turn()

    # ------------------------------------------------------------------
    # Mystery system
    # ------------------------------------------------------------------

    def _start_mystery(self, altar):
        """Begin a mystery encounter — show description and ask the player to accept."""
        from mystery_system import MYSTERIES, can_activate
        m = MYSTERIES[altar.mystery_id]
        # Show description always
        self.add_message(m['description'], 'info')
        can, reason = can_activate(altar.mystery_id, self.player,
                                   getattr(self, 'player_gold', 0))
        if not can:
            self.add_message(f"{m['name']}: {reason}", 'warning')
            return
        self._active_mystery_altar = altar
        self.state = STATE_MYSTERY_APPROACH

    def _mystery_approach_input(self, key: int, unicode: str):
        """Handle input while showing the mystery approach overlay."""
        if key in (pygame.K_ESCAPE, pygame.K_n):
            self.state = STATE_PLAYER
            self._active_mystery_altar = None
        elif key in (pygame.K_RETURN, pygame.K_y, pygame.K_SPACE):
            self._begin_mystery_challenge()

    def _begin_mystery_challenge(self):
        """Trigger the actual challenge for the active mystery."""
        from mystery_system import MYSTERIES, consume_key_item, get_cauldron_food_items, apply_mystery_reward
        altar = self._active_mystery_altar
        if altar is None:
            self.state = STATE_PLAYER
            return
        m  = MYSTERIES[altar.mystery_id]
        ch = m['challenge']

        # Pre-challenge costs
        if m.get('stat_cost'):
            for stat, amt in m['stat_cost'].items():
                self.player.apply_stat_bonus(stat, amt)
            self.add_message("You feel a part of yourself drain away as payment...", 'warning')

        if m.get('gold_cost', 0) > 0:
            self.player_gold = getattr(self, 'player_gold', 0) - m['gold_cost']
            self.add_message(f"You offer {m['gold_cost']} gold as tribute.", 'info')

        # Consume key item (if any; not cauldron food)
        if m['key_item'] is not None and altar.mystery_id not in ('cauldron',):
            consume_key_item(altar.mystery_id, self.player)

        # For cauldron: consume 3 food items
        if altar.mystery_id == 'cauldron':
            foods = get_cauldron_food_items(self.player)
            for food in foods[:3]:
                self.player.remove_from_inventory(food)
            self.add_message("Three meals are consumed by the cauldron's fire.", 'info')

        # Sisyphus: physical challenge — start tracking tiles
        if ch['mode'] == 'physical':
            self.player.quirk_progress['sisyphus_boulder_active'] = True
            self.player.quirk_progress['sisyphus_boulder_tiles'] = 0
            self.add_message("You grasp the boulder. Begin your ascent.", 'info')
            self.state = STATE_PLAYER
            self._active_mystery_altar = None
            return

        # Quiz challenge
        def _on_mystery_complete(result):
            success = result.success
            # For chain mode, check threshold manually
            if ch['mode'] == 'chain' and 'threshold' in ch:
                success = result.score >= ch['threshold']
            # Pandora inversion
            if m.get('invert_result'):
                success = not success
            apply_mystery_reward(altar.mystery_id, self.player, self, success)
            if not altar.activated:
                altar.activated = True
                # Remove altar from ground_items once activated
                if altar in self.ground_items:
                    self.ground_items.remove(altar)
            self._active_mystery_altar = None

        quiz_kwargs = {
            'mode':           ch['mode'],
            'subject':        ch['subject'],
            'tier':           ch['tier'],
            'callback':       _on_mystery_complete,
            'threshold':      ch.get('threshold', 3),
            'wisdom':         self.player.WIS,
            'timer_modifier': self.player.get_quiz_timer_modifier(),
            'extra_seconds':  self.player.get_quiz_extra_seconds(ch['subject']),
        }
        if 'max_chain' in ch:
            quiz_kwargs['max_chain'] = ch['max_chain']

        self.quiz_title = f"{m['name'].upper()}  —  {ch['subject'].upper()}"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(**quiz_kwargs)

    def _draw_mystery_approach(self):
        """Draw the mystery encounter overlay — description, requirements, Y/N prompt."""
        from fantasy_ui import FP, get_font
        altar = self._active_mystery_altar
        if altar is None:
            self.state = STATE_PLAYER
            return

        from mystery_system import MYSTERIES
        m = MYSTERIES[altar.mystery_id]

        # Semi-transparent background
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 780, 320
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

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
        req_lines.append(
            f"Challenge: {ch['subject'].capitalize()}  —  {ch['mode'].replace('_', ' ').title()}"
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

    # ------------------------------------------------------------------
    # Harvest
    # ------------------------------------------------------------------

    def _harvest(self):
        px, py = self.player.x, self.player.y
        corpse = next(
            (i for i in self.ground_items
             if isinstance(i, Corpse) and i.x == px and i.y == py),
            None
        )
        if corpse is None:
            self.add_message("There is no corpse here to harvest.", 'info')
            return
        if corpse.ingredient_id is None:
            self.add_message(f"The {corpse.name} yields nothing useful.", 'info')
            self.ground_items.remove(corpse)
            return

        self.ground_items.remove(corpse)
        self.quiz_title = f"HARVESTING {corpse.name.upper()}  —  ANIMAL LORE"
        self.state = STATE_QUIZ

        def on_complete(ingredient, message: str):
            self.state = STATE_PLAYER
            self.add_message(message, 'loot' if ingredient is not None else 'warning')
            success = ingredient is not None
            _qs_harv = getattr(self, 'quirk_system', None)
            if _qs_harv:
                # Check if this monster's definition applies poison
                _mon_def = getattr(corpse, 'monster_def', {}) or {}
                _attacks = _mon_def.get('attacks', [])
                _applies_poison = any(
                    atk.get('effect') == 'poisoned' for atk in _attacks
                    if isinstance(atk, dict)
                )
                _qs_harv.on_harvest(
                    monster_kind=corpse.monster_id,
                    success=success,
                    monster_applies_poisoned=_applies_poison,
                )
            if success:
                if not self.player.add_to_inventory(ingredient):
                    self.ground_items.append(ingredient)
                    ingredient.x, ingredient.y = px, py
                    self.add_message(
                        f"Too heavy — {ingredient.name} dropped.", 'warning'
                    )
            self._advance_turn()

        harvest_corpse(self.player, corpse, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Cook menu
    # ------------------------------------------------------------------

    def _open_cook_menu(self):
        self.cook_menu_items = [
            i for i in self.player.inventory if isinstance(i, Ingredient)
        ]
        self.cook_compound_recipes = get_available_compound_recipes(self.player.inventory)
        if not self.cook_menu_items and not self.cook_compound_recipes:
            self.add_message("You have no ingredients to cook.", 'info')
            return
        self.state = STATE_COOK_MENU

    def _cook_menu_input(self, key: int):
        # Letter keys A-F select compound recipes; number keys 1-9 select single ingredients
        recipe_keys = {
            pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2,
            pygame.K_d: 3, pygame.K_e: 4, pygame.K_f: 5,
        }
        ing_keys = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        if key in recipe_keys:
            ridx = recipe_keys[key]
            if ridx < len(self.cook_compound_recipes):
                self.state = STATE_PLAYER
                self._cook_compound(self.cook_compound_recipes[ridx])
            return
        idx = ing_keys.get(key)
        if idx is None or idx >= len(self.cook_menu_items):
            return
        self.state = STATE_PLAYER
        self._cook_item(self.cook_menu_items[idx])

    def _cook_item(self, ingredient):
        self.player.remove_from_inventory(ingredient)
        self.quiz_title = f"COOKING {ingredient.name.upper()}  —  COOKING CHAIN"
        self.state = STATE_QUIZ

        def on_complete(messages: list[str]):
            self.state = STATE_PLAYER
            for i, msg in enumerate(messages):
                self.add_message(msg, 'warning' if (i == 0 and 'ruin' in msg.lower()) else 'success')
            # Determine quality from messages to notify quirk system
            _qs_cook = getattr(self, 'quirk_system', None)
            if _qs_cook:
                _quality = 0
                for _m in messages:
                    import re as _re
                    _match = _re.search(r'quality\s+(\d)', _m)
                    if _match:
                        _quality = int(_match.group(1))
                        break
                _recipe_data = ingredient.recipes.get(str(_quality), ingredient.recipes.get('0', {}))
                _qs_cook.on_food_eaten(
                    quality=_quality,
                    source_monster=getattr(ingredient, 'source_monster', ''),
                    bonus_type=_recipe_data.get('bonus_type', 'none'),
                    ingredient_id=ingredient.id,
                )
            self._advance_turn()

        # Check Persephone quirk: max chain 6
        _persephone = getattr(self.player, 'quirk_progress', {}).get('persephone_active', False)
        cook_ingredient(self.player, ingredient, self.quiz_engine, on_complete,
                        max_chain=6 if _persephone else 5)

    def _cook_compound(self, recipe: dict):
        ing_names = ', '.join(recipe.get('ingredients', []))
        self.quiz_title = f"PREPARING {recipe['name'].upper()}  —  COOKING CHAIN"
        self.state = STATE_QUIZ

        def on_complete(messages: list[str]):
            self.state = STATE_PLAYER
            for i, msg in enumerate(messages):
                self.add_message(msg, 'warning' if (i == 0 and ('ruin' in msg.lower() or 'mediocre' in msg.lower())) else 'success')
            self._advance_turn()

        cook_compound_recipe(self.player, recipe, self.player.inventory, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Eat menu  (z key)
    # ------------------------------------------------------------------

    def _open_eat_menu(self):
        """Collect Food items and Ingredients for eating."""
        self.eat_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Food, Ingredient))
        ]
        if not self.eat_menu_items:
            self.add_message("You have nothing to eat.", 'info')
            return
        self.state = STATE_EAT_MENU

    def _eat_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.eat_menu_items):
            return
        self.state = STATE_PLAYER
        item = self.eat_menu_items[idx]
        self.player.remove_from_inventory(item)
        if isinstance(item, Food):
            messages = eat_food(self.player, item)
            mtype = 'success' if self.player.sp > 0 else 'warning'
            for msg in messages:
                self.add_message(msg, mtype)
        else:
            messages = eat_raw(self.player, item)
            mtype = 'success' if self.player.sp > 0 else 'warning'
            for msg in messages:
                self.add_message(msg, mtype)
        self._advance_turn()

    # ------------------------------------------------------------------
    # Quaff menu  (Q key)
    # ------------------------------------------------------------------

    _BENEFICIAL_EFFECTS = frozenset({
        'heal', 'extra_heal', 'full_heal', 'restore_sp',
        'cure_poison', 'cure_disease', 'cure_all',
        'haste', 'invisibility', 'regeneration',
        'heroism', 'brilliance', 'levitation',
        'restore_str', 'gain_level',
        'fire_resist', 'cold_resist', 'shock_resist',
    })

    def _open_quaff_menu(self):
        self.quaff_menu_items = [
            i for i in self.player.inventory if isinstance(i, Potion)
        ]
        if not self.quaff_menu_items:
            self.add_message("You have no potions to quaff.", 'info')
            return
        self.state = STATE_QUAFF_MENU

    def _quaff_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.quaff_menu_items):
            return
        self.state = STATE_PLAYER
        item = self.quaff_menu_items[idx]
        self.player.remove_from_inventory(item)

        from food_system import drink_potion
        item.identified = True
        self.player.known_item_ids.add(item.id)
        messages = drink_potion(self.player, item)
        _qs_pot = getattr(self, 'quirk_system', None)
        if _qs_pot:
            _qs_pot.on_potion_drunk()

        # Handle special signal: gain_level
        if '_gain_level' in messages:
            messages.remove('_gain_level')
            if self.dungeon_level > 1:
                self._change_level(self.dungeon_level - 1, enter_from_top=False)
                self.add_message("The potion propels you upward!", 'success')
            else:
                self.add_message("The potion shimmers — but you're already on the first floor.", 'info')
        # Handle teleport signal
        if '_teleport' in messages:
            messages.remove('_teleport')
            self._teleport_player()
            self.add_message("The world lurches — you're somewhere else!", 'warning')

        is_good = item.effect in self._BENEFICIAL_EFFECTS
        for msg in messages:
            self.add_message(msg, 'success' if is_good else 'danger')
        self._advance_turn()

    # ------------------------------------------------------------------
    # Prayer  (\ key — theology escalator_chain quiz)
    # ------------------------------------------------------------------

    def _start_pray(self):
        """Begin a prayer — escalator chain quiz (theology). Cooldown-gated."""
        if self.player.prayer_cooldown > 0:
            self.add_message(
                f"You cannot pray yet. ({self.player.prayer_cooldown} turns remain)",
                'warning'
            )
            return
        at_altar = self.dungeon.tiles[self.player.y][self.player.x] == ALTAR
        bonus_desc = " The altar amplifies your prayer." if at_altar else ""
        self.add_message(f"You kneel and pray...{bonus_desc}", 'info')
        self._at_altar = at_altar
        self.quiz_title = "PRAYER — THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_prayer(chain, self._at_altar)
            self.state = STATE_PLAYER
            _qs_pray = getattr(self, 'quirk_system', None)
            if _qs_pray and chain > 0:
                hp_pct = self.player.hp / max(1, self.player.max_hp)
                _qs_pray.on_prayer(hp_pct)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='theology',
            tier=1,
            callback=on_complete,
            max_chain=8,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('theology'),
        )

    def _resolve_prayer(self, chain: int, at_altar: bool = False):
        """Apply prayer blessings based on chain score. Higher chain = greater boon."""
        _PRAYER_VERSES = {
            0: None,
            1: ("Cast all your anxiety on him, because he cares for you.", "1 Peter 5:7"),
            2: ("If we confess our sins, he is faithful and just to forgive us.", "1 John 1:9"),
            3: ("He heals the brokenhearted and binds up their wounds.", "Psalm 147:3"),
            4: ("Those who hope in the LORD will renew their strength.", "Isaiah 40:31"),
            5: ("The LORD is my shepherd; I shall not want.", "Psalm 23:1"),
            6: ("I can do all things through him who strengthens me.", "Philippians 4:13"),
            7: ("Do not be afraid, for I am with you; I will strengthen you.", "Isaiah 41:10"),
            8: ("Well done, good and faithful servant!", "Matthew 25:23"),
        }
        p = self.player
        effective = chain + (1 if at_altar else 0)

        # Cooldown scales with how powerful a prayer was answered
        p.prayer_cooldown = max(100, 80 + effective * 25)
        if getattr(p, 'quirk_progress', {}).get('fisher_king_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)
        # Fisher King mystery: permanently halved prayer cooldown
        if getattr(p, 'quirk_progress', {}).get('fisher_king_mystery_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)

        if effective == 0:
            self.add_message("The heavens are silent.", 'info')
            return

        msgs = []

        if effective >= 8:
            # Perfect/near-perfect chain: permanent stat bonus (diminishing returns)
            if p.prayer_boon_count < 3:
                p.apply_stat_bonus('WIS', 1)
                p.prayer_boon_count += 1
                msgs.append("A divine light fills you. Your wisdom is permanently increased! (WIS +1)")
            else:
                p.hp = p.max_hp
                p.sp = p.max_sp
                msgs.append("Divine grace overflows! You are fully restored!")
            p.hp = p.max_hp
            p.sp = p.max_sp

        elif effective >= 7:
            p.hp = p.max_hp
            p.sp = p.max_sp
            msgs.append("A warm light washes over you. You are fully healed and restored!")

        elif effective >= 6:
            p.sp = p.max_sp
            heal = p.max_hp // 2
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"Divine grace heals your wounds. (+{heal} HP, SP fully restored)")

        elif effective >= 5:
            sp_gain = int(p.max_sp * 0.6)
            p.sp = min(p.max_sp, p.sp + sp_gain)
            heal = p.max_hp // 5
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"Your spirit is renewed. (+{sp_gain} SP, +{heal} HP)")

        elif effective >= 4:
            sp_gain = int(p.max_sp * 0.3)
            p.sp = min(p.max_sp, p.sp + sp_gain)
            msgs.append(f"Your stamina is renewed. (+{sp_gain} SP)")

        elif effective >= 3:
            # Cleanse ALL negative status effects
            bad_effects = ['poisoned', 'paralyzed', 'confused', 'bleeding', 'blinded',
                           'sleeping', 'slowed', 'weakened', 'cursed']
            cleared = [e for e in bad_effects if p.has_effect(e)]
            for e in cleared:
                p.status_effects.pop(e, None)
            if cleared:
                msgs.append(f"All afflictions lifted: {', '.join(cleared)}!")
            else:
                sp_gain = p.max_sp // 5
                p.sp = min(p.max_sp, p.sp + sp_gain)
                msgs.append(f"You feel cleansed and refreshed. (+{sp_gain} SP)")

        elif effective >= 2:
            # Remove one major negative status OR uncurse one item
            major = ['poisoned', 'paralyzed', 'blinded']
            removed = next((e for e in major if p.has_effect(e)), None)
            if removed:
                p.status_effects.pop(removed, None)
                msgs.append(f"The {removed} condition is lifted!")
            else:
                cursed_items = []
                for slot in p.armor_slots:
                    if slot and getattr(slot, 'cursed', False):
                        cursed_items.append(slot)
                if p.shield and getattr(p.shield, 'cursed', False):
                    cursed_items.append(p.shield)
                if cursed_items:
                    target = cursed_items[0]
                    target.cursed = False
                    msgs.append(f"The curse on your {target.name} is broken!")
                else:
                    minor = ['confused', 'bleeding', 'slowed', 'sleeping']
                    removed = next((e for e in minor if p.has_effect(e)), None)
                    if removed:
                        p.status_effects.pop(removed, None)
                        msgs.append(f"The {removed} condition is lifted!")
                    else:
                        sp_gain = p.max_sp // 10
                        p.sp = min(p.max_sp, p.sp + sp_gain)
                        msgs.append(f"A gentle comfort washes over you. (+{sp_gain} SP)")

        elif effective >= 1:
            minor = ['confused', 'bleeding', 'slowed', 'sleeping']
            removed = next((e for e in minor if p.has_effect(e)), None)
            if removed:
                p.status_effects.pop(removed, None)
                msgs.append(f"The {removed} condition fades away.")
            else:
                sp_gain = p.max_sp // 20
                p.sp = min(p.max_sp, p.sp + sp_gain)
                msgs.append(f"A faint warmth soothes your spirit. (+{sp_gain} SP)")

        for m in msgs:
            self.add_message(m, 'success')

        # Display verse
        verse_key = min(effective, 8)
        verse_data = _PRAYER_VERSES.get(verse_key)
        if verse_data:
            verse_text, citation = verse_data
            self.add_message(f'"{verse_text}"', 'loot')
            self.add_message(f"  — {citation}", 'info')

    # ------------------------------------------------------------------
    # Recall Lore
    # ------------------------------------------------------------------

    def _on_quiz_answer(self, is_correct: bool):
        """Fired after every individual quiz answer to tally global stats."""
        if is_correct:
            self.correct_answers += 1
            _snd.play('quiz_correct')
        else:
            self.wrong_answers += 1
            _snd.play('quiz_wrong')
        # Quirk notifications
        qe = self.quiz_engine
        qs = getattr(self, 'quirk_system', None)
        if qs and self.player:
            qs.on_quiz_answer(
                subject=qe.subject,
                correct=is_correct,
                chain=qe.chain,
                while_blinded=self.player.has_effect('blinded'),
                while_confused=self.player.has_effect('confused'),
                while_hallucinating=(self.player.has_effect('hallucinating') or
                                     self.player.has_effect('hallucinating_pot')),
                while_feared=self.player.has_effect('feared'),
                wrong_this_session=qe.asked_count - qe.correct_count,
                score_this_session=qe.score,
            )

    def _start_recall_lore(self):
        """Begin a Recall Lore session — escalator chain trivia quiz. Cooldown-gated."""
        if self.player.recall_lore_cooldown > 0:
            self.add_message(
                f"Your mind needs rest before recalling more lore. "
                f"({self.player.recall_lore_cooldown} turns remain)", 'warning'
            )
            return
        self.add_message("You close your eyes and search your memory...", 'info')
        self.quiz_title = "RECALL LORE — TRIVIA"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_recall_lore(chain)
            self.state = STATE_HINT
            _qs_lore = getattr(self, 'quirk_system', None)
            if _qs_lore:
                _qs_lore.on_recall_lore()
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='trivia',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('trivia'),
        )

    def _resolve_recall_lore(self, chain: int):
        """Pick a hint based on chain quality and display it. Set cooldown."""
        import json as _json
        import random as _rng

        # Cooldown: longer for better knowledge (takes time to absorb)
        if chain == 0:
            self.player.recall_lore_cooldown = 40
            self.add_message("Your thoughts scatter. Nothing surfaces.", 'warning')
            self._lore_hint_text = None
            return

        self.player.recall_lore_cooldown = 50 + chain * 15   # 65 .. 125 turns
        if getattr(self.player, 'quirk_progress', {}).get('norns_active'):
            self.player.recall_lore_cooldown = max(5, self.player.recall_lore_cooldown // 2)

        from paths import data_path
        hints_path = data_path('data', 'hints.json')
        try:
            with open(hints_path, encoding='utf-8') as f:
                all_hints = _json.load(f)
        except Exception:
            self.add_message("A lore scroll crumbles in your memory.", 'warning')
            self._lore_hint_text = None
            return

        tier_key = str(min(chain, 5))
        pool = all_hints.get(tier_key, [])
        if not pool:
            self.add_message("Nothing comes to mind.", 'info')
            self._lore_hint_text = None
            return

        hint = _rng.choice(pool)
        self._lore_hint_text = hint
        self._lore_hint_chain = chain

    # ------------------------------------------------------------------
    # Equip menu
    # ------------------------------------------------------------------

    def _open_equip_menu(self):
        from items import ARMOR_SLOTS
        self.equip_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Weapon, Armor, Shield, Accessory))
        ]
        # Collect currently equipped items for the unequip section
        self.equip_menu_equipped = []
        if self.player.weapon:
            self.equip_menu_equipped.append(('weapon', self.player.weapon))
        if self.player.shield:
            self.equip_menu_equipped.append(('shield', self.player.shield))
        for slot_name, slot_item in zip(ARMOR_SLOTS, self.player.armor_slots):
            if slot_item:
                self.equip_menu_equipped.append((slot_name, slot_item))
        for idx, acc_item in enumerate(self.player.accessory_slots):
            if acc_item is not None:
                self.equip_menu_equipped.append((f'accessory_{idx}', acc_item))
        if self.player.amulet_slot:
            self.equip_menu_equipped.append(('amulet', self.player.amulet_slot))
        if not self.equip_menu_items and not self.equip_menu_equipped:
            self.add_message("Nothing to equip or unequip.", 'info')
            return
        self.state = STATE_EQUIP_MENU

    def _equip_menu_input(self, key: int):
        # Number keys: equip from inventory
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is not None and idx < len(self.equip_menu_items):
            self.state = STATE_PLAYER
            self._equip_item(self.equip_menu_items[idx])
            return

        # Letter keys a-h: unequip currently equipped items
        letter_to_idx = {
            pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3,
            pygame.K_e: 4, pygame.K_f: 5, pygame.K_g: 6, pygame.K_h: 7,
        }
        uidx = letter_to_idx.get(key)
        if uidx is not None and uidx < len(self.equip_menu_equipped):
            self.state = STATE_PLAYER
            slot_name, slot_item = self.equip_menu_equipped[uidx]
            self._unequip_slot(slot_name, slot_item)

    def _equip_item(self, item):
        if isinstance(item, Weapon):
            # Check if switching to 2H while shield is cursed
            if getattr(item, 'two_handed', False) and self.player.shield:
                ok, msg = self.player.try_unequip_slot(self.player.shield)
                if not ok:
                    self.add_message(msg, 'warning')
                    return
            dname = self._display_name(item)
            self.player._apply_equip(item)
            self.player.remove_from_inventory(item)
            item.identified = True
            self.player.known_item_ids.add(item.id)
            suffix = " (two-handed)" if getattr(item, 'two_handed', False) else ""
            self.add_message(f"You equip the {dname}{suffix}.", 'success')
            _qs_eq = getattr(self, 'quirk_system', None)
            if _qs_eq:
                _qs_eq.on_item_equipped(item.id, 'weapon', 'weapon')
            self._advance_turn()
        elif isinstance(item, Shield):
            if not self.player.can_equip_shield():
                self.add_message(
                    "You cannot use a shield while wielding a two-handed weapon!", 'warning'
                )
                return
            # Check if current shield is cursed
            if self.player.shield:
                ok, msg = self.player.try_unequip_slot(self.player.shield)
                if not ok:
                    self.add_message(msg, 'warning')
                    return
            self._start_armor_quiz(item)
        elif isinstance(item, Armor):
            # Check if current item in that slot is cursed
            from items import ARMOR_SLOTS
            idx = ARMOR_SLOTS.index(item.slot) if item.slot in ARMOR_SLOTS else -1
            if idx >= 0 and self.player.armor_slots[idx]:
                ok, msg = self.player.try_unequip_slot(self.player.armor_slots[idx])
                if not ok:
                    self.add_message(msg, 'warning')
                    return
            self._start_armor_quiz(item)
        elif isinstance(item, Accessory):
            self._equip_accessory(item)

    def _unequip_slot(self, slot_name: str, item):
        """Remove an equipped item and return it to inventory."""
        from items import ARMOR_SLOTS
        ok, msg = self.player.try_unequip_slot(item)
        if not ok:
            self.add_message(msg, 'warning')
            return
        # Remove from the appropriate slot
        if slot_name == 'weapon':
            self.player.weapon = None
        elif slot_name == 'shield':
            self.player.shield = None
        elif slot_name in ARMOR_SLOTS:
            idx = ARMOR_SLOTS.index(slot_name)
            self.player.armor_slots[idx] = None
        elif slot_name.startswith('accessory_'):
            acc_idx = int(slot_name.split('_')[1])
            self.player.accessory_slots[acc_idx] = None
            from items import Accessory as _Acc
            if isinstance(item, _Acc):
                fx = item.effects
                if 'stat' in fx:
                    self.player.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                if 'status' in fx:
                    self.player.status_effects.pop(fx['status'], None)
        elif slot_name == 'amulet':
            self.player.amulet_slot = None
            from items import Accessory as _Acc
            if isinstance(item, _Acc):
                fx = item.effects
                if 'stat' in fx:
                    self.player.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                if 'status' in fx:
                    self.player.status_effects.pop(fx['status'], None)
        self.player.inventory.append(item)
        self.add_message(f"You remove the {self._display_name(item)}.", 'info')
        _qs_uneq = getattr(self, 'quirk_system', None)
        if _qs_uneq:
            itype = 'weapon' if slot_name == 'weapon' else \
                    'shield' if slot_name == 'shield' else \
                    'armor' if slot_name not in ('amulet',) and not slot_name.startswith('accessory_') else \
                    'accessory'
            _qs_uneq.on_item_unequipped(item.id, itype, slot_name)
        self._advance_turn()

    def _start_armor_quiz(self, item):
        """Launch geography threshold quiz to equip armor or shield."""
        item_name = self._display_name(item)
        cursed_tag = " (cursed)" if getattr(item, 'cursed', False) else ""
        self.quiz_title = f"EQUIPPING {item_name.upper()}  —  GEOGRAPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                self.player._apply_equip(item)
                self.player.remove_from_inventory(item)
                item.identified = True
                self.player.known_item_ids.add(item.id)
                ac = self.player.get_ac()
                msg = f"You equip the {item_name}{cursed_tag}. AC is now {ac}."
                if getattr(item, 'cursed', False):
                    msg += " It feels wrong..."
                self.add_message(msg, 'success')
                _qs_arm = getattr(self, 'quirk_system', None)
                if _qs_arm:
                    itype = 'shield' if isinstance(item, Shield) else 'armor'
                    _qs_arm.on_item_equipped(item.id, itype, getattr(item, 'slot', itype))
            else:
                self.add_message(
                    f"You struggle with the {item_name} and give up.", 'warning'
                )
            self._advance_turn()

        # Check Hephaestus quirk: -1 threshold for repeatedly-equipped armor slot
        heph_slot = getattr(self.player, 'quirk_progress', {}).get('hephaestus_slot')
        if heph_slot and getattr(item, 'slot', '') == heph_slot:
            _threshold = max(1, item.equip_threshold - 1)
        else:
            _threshold = item.equip_threshold

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='geography',
            tier=getattr(item, 'quiz_tier', 1),
            callback=on_complete,
            threshold=_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('geography'),
        )

    # ------------------------------------------------------------------
    # Accessory menu  (r key — history quiz)
    # ------------------------------------------------------------------

    def _open_accessory_menu(self):
        self.accessory_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, Accessory) and i.id != 'philosophers_amulet'
        ]
        if not self.accessory_menu_items:
            self.add_message("You have no rings or amulets to equip.", 'info')
            return
        self.state = STATE_ACCESSORY_MENU

    def _accessory_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.accessory_menu_items):
            return
        self.state = STATE_PLAYER
        self._equip_accessory(self.accessory_menu_items[idx])

    def _equip_accessory(self, item: 'Accessory'):
        # Check for a free slot
        if all(s is not None for s in self.player.accessory_slots):
            self.add_message("All accessory slots are full!", 'warning')
            return

        item_name = self._display_name(item)
        self.quiz_title = f"EQUIPPING {item_name.upper()}  —  HISTORY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                self.player._apply_equip(item)
                self.player.remove_from_inventory(item)
                item.identified = True
                self.player.known_item_ids.add(item.id)
                fx = item.effects
                if 'status' in fx:
                    self.add_message(
                        f"You slip on the {item_name}. You feel {fx['status']}!", 'success'
                    )
                else:
                    stat = fx.get('stat', '')
                    amt  = fx.get('amount', 0)
                    self.add_message(
                        f"You slip on the {item_name}. {stat} +{amt}!", 'success'
                    )
            else:
                self.add_message(
                    f"You fumble with the {item_name} and give up.", 'warning'
                )
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='history',
            tier=item.quiz_tier,
            callback=on_complete,
            threshold=item.equip_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('history'),
        )

    # ------------------------------------------------------------------
    # Wand menu  (u key — science quiz)
    # ------------------------------------------------------------------

    def _open_wand_menu(self):
        self.wand_menu_items = [
            i for i in self.player.inventory if isinstance(i, Wand)
        ]
        if not self.wand_menu_items:
            self.add_message("You have no wands to use.", 'info')
            return
        self.state = STATE_WAND_MENU

    def _wand_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.wand_menu_items):
            return
        self.state = STATE_PLAYER
        self._invoke_wand(self.wand_menu_items[idx])

    def _invoke_wand(self, wand: 'Wand'):
        # Philosopher's Wrench: no quiz — it's a tool, not magic
        if wand.id == 'philosophers_wrench':
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            self._use_philosophers_wrench()
            self._advance_turn()
            return

        if wand.charges <= 0:
            self.add_message("The wand is empty — it crumbles to dust.", 'warning')
            self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  —  SCIENCE"
        self.state = STATE_QUIZ
        _was_identified_before = getattr(wand, 'identified', False) or \
            wand.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            _qs_wand = getattr(self, 'quirk_system', None)
            if _qs_wand:
                _qs_wand.on_wand_zapped(wand.id, was_identified=_was_identified_before)

            if not result.success:
                self.add_message("The wand fizzes and fails to fire.", 'warning')
                self._advance_turn()
                return

            wand.charges -= 1
            self._apply_wand_effect(wand)
            if wand.charges <= 0:
                self.add_message("The wand crumbles to dust — it is spent.", 'warning')
                self.player.remove_from_inventory(wand)
            else:
                self.add_message(
                    f"({wand.charges}/{wand.max_charges} charges remain)", 'info'
                )
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='science',
            tier=wand.quiz_tier,
            callback=on_complete,
            threshold=wand.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
        )

    def _apply_wand_effect(self, wand: 'Wand'):
        import random as _rng
        from dice import roll
        effect = wand.effect

        # ── CHARACTER EFFECTS ────────────────────────────────────────────────
        if effect == 'heal':
            amount = roll(wand.power) if wand.power else 8
            self.player.restore_hp(amount)
            self.add_message(f"The wand heals you for {amount} HP!", 'success')

        elif effect == 'extra_heal':
            amount = (roll(wand.power) if wand.power else 20) + 10
            self.player.restore_hp(amount)
            self.add_message(f"Intense healing washes over you — {amount} HP restored!", 'success')

        elif effect == 'restore_body':
            self.player.hp = self.player.max_hp
            self.player.sp = self.player.max_sp
            self.player.mp = self.player.max_mp
            self.add_message("Your body is fully restored!", 'success')

        elif effect == 'haste_self':
            self.player.add_effect('hasted', 12)
            self.add_message("You feel supernaturally swift!", 'success')

        elif effect == 'invisibility_self':
            self.player.add_effect('invisible', 15)
            self.add_message("You fade from sight!", 'success')

        elif effect == 'levitation_self':
            self.player.add_effect('levitating', 12)
            self.add_message("You rise gently off the ground!", 'success')

        elif effect == 'teleport_self':
            self._teleport_player()

        # ── WORLD EFFECTS ────────────────────────────────────────────────────
        elif effect == 'digging':
            px, py = self.player.x, self.player.y
            opened = 0
            from dungeon import DOOR, SECRET_DOOR, WALL, FLOOR
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(1,-1),(1,1)]:
                nx, ny = px + dx, py + dy
                if self.dungeon.in_bounds(nx, ny):
                    t = self.dungeon.tiles[ny][nx]
                    if t in (DOOR, SECRET_DOOR, WALL):
                        self.dungeon.tiles[ny][nx] = FLOOR
                        opened += 1
            self._refresh_fov()
            self.add_message(
                f"The wand blasts open {opened} wall{'s' if opened != 1 else ''} around you!" if opened
                else "The wand hums — nothing to dig here.", 'success' if opened else 'info'
            )

        elif effect == 'light':
            radius = 15
            px, py = self.player.x, self.player.y
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        nx, ny = px + dx, py + dy
                        if self.dungeon.in_bounds(nx, ny):
                            self.dungeon.explored.add((nx, ny))
            self.add_message("Brilliant light floods the area!", 'success')

        elif effect == 'create_monster':
            import json, os
            from monster import Monster
            from paths import data_path
            mp = data_path('data', 'monsters.json')
            try:
                with open(mp, encoding='utf-8') as f:
                    all_defs = json.load(f)
                eligible = {k: v for k, v in all_defs.items()
                            if v.get('min_level', 1) <= self.dungeon_level and v.get('frequency', 1) > 0}
                if eligible:
                    kind = _rng.choice(list(eligible.keys()))
                    defn = {**eligible[kind], 'id': kind}
                    floors = [
                        (x, y) for y in range(self.dungeon.height)
                        for x in range(self.dungeon.width)
                        if self.dungeon.is_walkable(x, y)
                        and abs(x - self.player.x) <= 6 and abs(y - self.player.y) <= 6
                        and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                        and (x, y) != (self.player.x, self.player.y)
                    ]
                    if floors:
                        mx, my = _rng.choice(floors)
                        self.monsters.append(Monster(defn, mx, my))
                        self.add_message(f"A {defn['name']} materialises from the ether!", 'danger')
                    else:
                        self.add_message("The wand sputters — no room for a monster nearby.", 'info')
            except Exception:
                self.add_message("The wand misfires!", 'warning')

        # ── STATUS EFFECTS ON TARGET ─────────────────────────────────────────
        elif effect in ('sleep_monster', 'slow_monster', 'confuse_monster',
                        'paralyze_monster', 'blind_monster', 'stoning',
                        'fire_bolt', 'cold_bolt', 'lightning_bolt',
                        'acid_spray', 'magic_missile', 'striking',
                        'death_ray', 'cancellation', 'polymorph_monster'):
            target = self._nearest_visible_monster()
            if target is None:
                self.add_message("The wand hums but finds no target.", 'info')
                return

            if effect == 'sleep_monster':
                target.add_effect('sleeping', 8)
                self.add_message(f"The {target.name} slumps into a deep sleep!", 'success')

            elif effect == 'slow_monster':
                target.add_effect('slowed', 8)
                self.add_message(f"The {target.name} slows to a crawl!", 'success')

            elif effect == 'confuse_monster':
                target.add_effect('confused', 10)
                self.add_message(f"The {target.name} staggers in confusion!", 'success')

            elif effect == 'paralyze_monster':
                target.add_effect('paralyzed', 6)
                self.add_message(f"The {target.name} is locked in place!", 'success')

            elif effect == 'blind_monster':
                target.add_effect('blinded', 8)
                self.add_message(f"The {target.name} claws at its eyes, blinded!", 'success')

            elif effect == 'stoning':
                target.add_effect('petrifying', 5)
                # Petrifying kills the monster after turns expire
                self.add_message(f"The {target.name} begins to turn to stone!", 'success')

            elif effect == 'cancellation':
                target.status_effects.clear()
                self.add_message(
                    f"The {target.name}'s abilities and effects are cancelled!", 'success'
                )

            elif effect == 'fire_bolt':
                dmg = roll(wand.power) if wand.power else 6
                actual = target.take_damage(dmg)
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'cold_bolt':
                dmg = roll(wand.power) if wand.power else 4
                actual = target.take_damage(dmg)
                target.add_effect('slowed', 4)
                self.add_message(
                    f"A bolt of cold strikes the {target.name} for {actual} damage and slows it!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'lightning_bolt':
                # Shock resist blocks all damage
                from status_effects import DAMAGE_IMMUNITY
                dmg = roll(wand.power) if wand.power else 10
                actual = target.take_damage(dmg)
                if actual > 0:
                    target.add_effect('stunned', 3)
                    self.add_message(
                        f"Lightning strikes the {target.name} for {actual} damage — it is stunned!", 'success'
                    )
                else:
                    self.add_message(f"The {target.name} absorbs the lightning harmlessly.", 'info')
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'acid_spray':
                dmg = roll(wand.power) if wand.power else 4
                actual = target.take_damage(dmg)
                target.add_effect('diseased', 6)
                self.add_message(
                    f"Acid dissolves the {target.name} for {actual} damage — it is diseased!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'magic_missile':
                # Irresistible: bypasses all resistances
                dmg = roll(wand.power) + 1 if wand.power else 5
                target.hp = max(0, target.hp - dmg)
                if target.hp == 0:
                    target.alive = False
                self.add_message(
                    f"A magic missile unerringly strikes the {target.name} for {dmg} damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'striking':
                dmg = roll(wand.power) if wand.power else 10
                actual = target.take_damage(dmg)
                self.add_message(
                    f"The wand slams into the {target.name} for {actual} physical damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'death_ray':
                # 70% chance instant kill; remaining HP otherwise
                if _rng.random() < 0.70:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is slain instantly by the death ray!", 'success')
                    self._on_monster_killed(target)
                else:
                    dmg = max(1, target.max_hp // 2)
                    actual = target.take_damage(dmg)
                    self.add_message(
                        f"The death ray grazes the {target.name} for {actual} damage!", 'success'
                    )
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'polymorph_monster':
                import json, os
                from monster import Monster
                from paths import data_path
                mp = data_path('data', 'monsters.json')
                try:
                    with open(mp, encoding='utf-8') as f:
                        all_defs = json.load(f)
                    eligible = [k for k, v in all_defs.items()
                                if v.get('min_level', 1) <= self.dungeon_level
                                and k != target.kind and v.get('frequency', 1) > 0]
                    if eligible:
                        old_name = target.name
                        kind = _rng.choice(eligible)
                        defn = {**all_defs[kind], 'id': kind}
                        new_m = Monster(defn, target.x, target.y)
                        idx = self.monsters.index(target)
                        self.monsters[idx] = new_m
                        self.add_message(
                            f"The {old_name} warps into a {new_m.name}!", 'success'
                        )
                    else:
                        self.add_message("The polymorph wand finds no suitable form.", 'info')
                except Exception:
                    self.add_message("The wand misfires!", 'warning')

            elif effect == 'fear_monster':
                target.add_effect('feared', 10)
                target.ai_pattern = 'cowardly'
                self.add_message(f"The {target.name} turns and flees in terror!", 'success')

            elif effect == 'charm_monster':
                target.add_effect('charmed', 20)
                target.ai_pattern = 'sessile'
                self.add_message(f"The {target.name} gazes at you with adoration.", 'success')

            elif effect == 'poison_monster':
                target.add_effect('poisoned', 12)
                self.add_message(f"The {target.name} writhes as poison courses through it!", 'success')

            elif effect == 'disease_monster':
                target.add_effect('diseased', 15)
                actual = target.take_damage(max(1, target.max_hp // 5))
                self.add_message(f"The {target.name} is wracked by disease! ({actual} dmg)", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'curse_monster':
                target.add_effect('cursed', 20)
                target.add_effect('slowed', 8)
                self.add_message(f"Dark energy envelops the {target.name}! It is cursed and slowed.", 'success')

            elif effect == 'teleport_monster':
                open_tiles = [(x, y)
                              for y in range(len(self.dungeon.tiles))
                              for x in range(len(self.dungeon.tiles[y]))
                              if self.dungeon.is_walkable(x, y)]
                if open_tiles:
                    tx, ty = _rng.choice(open_tiles)
                    old_name = target.name
                    target.x, target.y = tx, ty
                    self.add_message(f"The {old_name} vanishes in a flash of light!", 'success')

            elif effect == 'drain_life':
                from dice import roll
                dmg = roll(wand.power) if wand.power else _rng.randint(3, 10)
                actual = target.take_damage(dmg)
                heal = min(actual, self.player.max_hp - self.player.hp)
                self.player.hp += heal
                self.add_message(
                    f"You drain {actual} life from the {target.name}! (+{heal} HP)", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'disintegrate':
                if _rng.random() < 0.85:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is disintegrated!", 'success')
                    self._on_monster_killed(target)
                else:
                    actual = target.take_damage(target.max_hp // 3)
                    self.add_message(f"The {target.name} is partially disintegrated! ({actual} dmg)", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'weaken_monster':
                target.add_effect('weakened', 15)
                if target.attacks:
                    self.add_message(f"The {target.name} looks visibly weaker!", 'success')
                else:
                    self.add_message(f"The {target.name} seems diminished.", 'success')

            elif effect == 'drain_magic':
                target.status_effects.clear()
                self.add_message(f"The {target.name}'s magical effects are drained away!", 'success')

            elif effect == 'dispel_magic':
                target.status_effects.clear()
                self.add_message(f"All enchantments on the {target.name} are dispelled!", 'success')

        # ---- Effects that don't require a target OR handle mass effects ----
        if effect == 'boost_str':
            old = self.player.STR
            self.player.apply_stat_bonus('STR', 1)
            self.add_message(f"You feel powerful! STR: {old} -> {self.player.STR}", 'success')

        elif effect == 'boost_con':
            old = self.player.CON
            self.player.apply_stat_bonus('CON', 1)
            self.add_message(f"You feel hardy! CON: {old} -> {self.player.CON}", 'success')

        elif effect == 'boost_int':
            old = self.player.INT
            self.player.apply_stat_bonus('INT', 1)
            self.add_message(f"Your mind sharpens! INT: {old} -> {self.player.INT}", 'success')

        elif effect == 'shield_self':
            self.player.add_effect('shielded', 15)
            self.add_message("A shimmering barrier surrounds you!", 'success')

        elif effect == 'fire_shield':
            self.player.add_effect('fire_shield', 15)
            self.add_message("Flames swirl around you! You are protected from fire.", 'success')

        elif effect == 'cold_shield':
            self.player.add_effect('cold_shield', 15)
            self.add_message("Frost encases you! You are protected from cold.", 'success')

        elif effect == 'regeneration_self':
            self.player.add_effect('regenerating', 30)
            self.add_message("You feel your wounds slowly closing.", 'success')

        elif effect == 'reflect_self':
            self.player.add_effect('reflecting', 20)
            self.add_message("A reflective aura surrounds you!", 'success')

        elif effect == 'phase_self':
            self.player.add_effect('phasing', 15)
            self.add_message("You feel briefly incorporeal — walls seem thin.", 'success')

        elif effect == 'detect_monsters':
            for m in self.monsters:
                if m.alive:
                    self.visible.add((m.x, m.y))
            self.add_message("You sense the presence of all nearby creatures!", 'success')

        elif effect == 'detect_treasure':
            for item in self.ground_items:
                self.dungeon.explored.add((item.x, item.y))
            self.add_message("A golden shimmer reveals hidden treasures!", 'success')

        elif effect == 'clairvoyance':
            for y in range(len(self.dungeon.tiles)):
                for x in range(len(self.dungeon.tiles[y])):
                    self.dungeon.explored.add((x, y))
            self.add_message("Your mind expands — you perceive the entire level!", 'success')

        elif effect == 'identify_item':
            unknown = [i for i in self.player.inventory if hasattr(i, 'identified') and not i.identified]
            if unknown:
                item = unknown[0]
                item.identified = True
                self.player.known_item_ids.add(item.id)
                self.add_message(f"The wand identifies: {item.name}!", 'success')
            else:
                self.add_message("Everything you carry is already known.", 'info')

        elif effect == 'enchant_weapon':
            w = self.player.weapon
            if w:
                w.enchant_bonus += 1
                self.add_message(f"Your {w.name} glows! Enchantment +{w.enchant_bonus}.", 'success')
            else:
                self.add_message("You wield no weapon to enchant.", 'warning')

        elif effect == 'earthquake':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            total_dmg = 0
            for m in visible_monsters:
                dmg = _rng.randint(5, 20)
                actual = m.take_damage(dmg)
                total_dmg += actual
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"The earth shakes! {len(visible_monsters)} creatures are battered. ({total_dmg} total dmg)", 'success')

        elif effect == 'explosion':
            from dice import roll
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                dmg = roll(wand.power) if wand.power else _rng.randint(8, 24)
                actual = m.take_damage(dmg)
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"A massive explosion engulfs the area! ({len(visible_monsters)} creatures hit)", 'success')

        elif effect == 'mass_confuse':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('confused', 12)
            self.add_message(f"A wave of confusion washes over {len(visible_monsters)} creatures!", 'success')

        elif effect == 'mass_sleep':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('sleeping', 10)
            self.add_message(f"All visible creatures slump into slumber! ({len(visible_monsters)} affected)", 'success')

        elif effect == 'mass_slow':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('slowed', 10)
            self.add_message(f"{len(visible_monsters)} creatures are slowed!", 'success')

        elif effect == 'time_stop':
            self.player.add_effect('time_stopped', 5)
            self.add_message("Time freezes! You have 5 turns of free movement.", 'success')

        elif effect == 'wish':
            self.add_message("The wand glows brilliantly... but you cannot yet speak your wish.", 'info')

        # ── Tier 5 wand effects ───────────────────────────────────────────
        elif effect == 'nova':
            from dice import roll as _roll
            all_monsters = [m for m in self.monsters if m.alive]
            if not all_monsters:
                self.add_message("The wand fires but no creatures are present!", 'info')
            else:
                total = 0
                for m in all_monsters:
                    dmg = _roll(wand.power) if wand.power else _rng.randint(15, 30)
                    actual = m.take_damage(dmg)
                    total += actual
                    if not m.alive:
                        self._on_monster_killed(m)
                self.add_message(
                    f"A nova of stellar fire engulfs the entire level! "
                    f"({len(all_monsters)} creatures hit, {total} total damage)", 'success'
                )

        elif effect == 'life_transfer':
            target = self._nearest_visible_monster()
            if not target:
                self.add_message("No visible target for life transfer.", 'warning')
            else:
                drain = max(1, target.hp // 2)
                actual = target.take_damage(drain)
                self.player.restore_hp(actual)
                self.add_message(
                    f"Life force drains from the {target.name}! "
                    f"({actual} drained, +{actual} HP to you)", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

        elif effect == 'abjuration':
            target = self._nearest_visible_monster()
            # Strip all effects from target
            cleared_monster = 0
            if target:
                cleared_monster = len(target.status_effects)
                target.status_effects.clear()
            # Purge player debuffs
            from status_effects import DEBUFFS
            cleared_player = [e for e in list(self.player.status_effects) if e in DEBUFFS]
            for e in cleared_player:
                del self.player.status_effects[e]
            if target and cleared_monster:
                self.add_message(
                    f"Abjuration strips {cleared_monster} effect(s) from the {target.name}!", 'success'
                )
            if cleared_player:
                self.add_message(
                    f"Your afflictions dissolve: {', '.join(cleared_player)}.", 'success'
                )
            if not target and not cleared_player:
                self.add_message("Nothing to abjure.", 'info')

    def _nearest_visible_monster(self):
        """Return the closest alive monster currently in FOV, or None."""
        px, py = self.player.x, self.player.y
        best, best_dist = None, float('inf')
        for m in self.monsters:
            if m.alive and (m.x, m.y) in self.visible:
                d = abs(m.x - px) + abs(m.y - py)
                if d < best_dist:
                    best, best_dist = m, d
        return best

    def _on_monster_killed(self, monster):
        """Handle a monster killed by a wand bolt."""
        self.level_mgr.monsters_killed += 1
        self.add_message(f"The {monster.name} is slain!", 'success')
        self._drop_treasure(monster)
        # Boss narrative popup
        story_key = self._BOSS_STORY_KEYS.get(monster.kind)
        if story_key:
            self._show_story_popup(story_key, STATE_PLAYER)
        self.ground_items.append(self._make_corpse(monster))

    def _drop_treasure(self, monster):
        """Drop gold and possibly an item when a monster dies."""
        import random as _rng
        treasure = getattr(monster, 'treasure', {})
        gold_range = treasure.get('gold', [0, 0])
        gold = _rng.randint(int(gold_range[0]), max(int(gold_range[0]), int(gold_range[1])))
        if gold > 0:
            from items import GoldPile
            self.ground_items.append(GoldPile(gold, monster.x, monster.y))
            self.add_message(
                f"The {monster.name} drops {gold} gold coins.", 'loot'
            )
        item_chance = treasure.get('item_chance', 0.0)
        if _rng.random() < item_chance:
            item_tier = int(treasure.get('item_tier', 1))
            self._spawn_treasure_item(monster.x, monster.y, item_tier)

        # Boss reward scroll
        boss_scroll_id = treasure.get('boss_scroll_id')
        if boss_scroll_id:
            self._spawn_boss_scroll(monster.x, monster.y, boss_scroll_id)

        # Unique mini-boss drop
        unique_drop_id = treasure.get('unique_drop_id')
        if unique_drop_id:
            self._spawn_unique_item(monster.x, monster.y, unique_drop_id)

    def _make_corpse(self, monster):
        """Create a Corpse for a monster, auto-identifying it if the type is already known."""
        from items import Corpse
        c = Corpse(
            monster.name, monster.kind, monster.x, monster.y,
            harvest_tier=monster.harvest_tier,
            harvest_threshold=monster.harvest_threshold,
            ingredient_id=monster.ingredient_id,
            lore=getattr(monster, 'lore', ''),
            monster_def={
                'hp': monster.max_hp,
                'thac0': monster.thac0,
                'attacks': monster.attacks,
                'resistances': monster.resistances,
                'weaknesses': monster.weaknesses,
                'speed': monster.speed,
            },
        )
        if monster.kind in getattr(self.player, 'lore_known_monster_ids', set()):
            c.lore_identified = True
        return c

    def _spawn_unique_item(self, x: int, y: int, item_id: str):
        """Place a named unique item at (x, y), searching all item categories."""
        from items import load_items, copy_at
        categories = ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll')
        for cat in categories:
            try:
                items = load_items(cat)
                template = next((i for i in items if i.id == item_id), None)
                if template:
                    item = copy_at(template, x, y)
                    item.identified = False
                    self.ground_items.append(item)
                    self.add_message("\u2605 A remarkable item falls from the defeated foe!", 'loot')
                    return
            except Exception:
                pass

    def _spawn_boss_scroll(self, x: int, y: int, scroll_id: str):
        """Place a pre-identified boss reward scroll at (x, y)."""
        from items import load_items, copy_at
        try:
            scrolls = load_items('scroll')
            template = next((s for s in scrolls if s.id == scroll_id), None)
            if template:
                sc = copy_at(template, x, y)
                sc.identified = True
                self.ground_items.append(sc)
                self.add_message("★ The boss drops a REWARD SCROLL!", 'loot')
        except Exception:
            pass

    def _spawn_treasure_item(self, x: int, y: int, tier: int):
        """Place a random item of up to `tier` at (x,y)."""
        import random as _rng
        from items import load_items, copy_at
        candidates = []
        for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll'):
            try:
                for item in load_items(cls_name):
                    if item.min_level <= tier * 5:
                        candidates.append(item)
            except Exception:
                pass
        if candidates:
            chosen = copy_at(_rng.choice(candidates), x, y)
            self.ground_items.append(chosen)
            self.add_message(f"It drops {self._display_name(chosen)}!", 'loot')

    # ------------------------------------------------------------------
    # Spell menu  (m key — learned spells, cast with science chain quiz)
    # ------------------------------------------------------------------

    def _open_spell_menu(self):
        if not self.player.known_spells:
            self.add_message("You have not learned any spells.", 'warning')
            return
        self.spell_menu_items = list(self.player.known_spells.keys())
        self.state = STATE_SPELL_MENU

    def _spell_menu_input(self, key: int):
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        idx = None
        if pygame.K_a <= key <= pygame.K_z:
            idx = key - pygame.K_a
        if idx is None or idx >= len(self.spell_menu_items):
            return
        self._invoke_spell(self.spell_menu_items[idx])

    def _invoke_spell(self, spell_id: str):
        spell = LEARNABLE_SPELLS.get(spell_id)
        if not spell:
            return
        mp_cost = spell['mp_cost']
        if self.player.mp < mp_cost:
            self.add_message(
                f"Not enough MP to cast {spell['name']}! "
                f"(need {mp_cost}, have {self.player.mp})", 'warning')
            self.state = STATE_PLAYER
            return

        # For targeted spells, find nearest visible monster
        target = None
        if spell.get('needs_target'):
            target = self._nearest_visible_monster()
            if target is None:
                self.add_message("No visible target for this spell.", 'warning')
                self.state = STATE_PLAYER
                return

        self.player.mp -= mp_cost
        self.state = STATE_QUIZ
        self.quiz_title = f"CAST {spell['name'].upper()} — SCIENCE"

        def on_complete(result):
            chain = result.score
            self.state = STATE_PLAYER
            if chain == 0:
                self.add_message(f"The {spell['name']} fizzles... (MP wasted)", 'warning')
            else:
                _snd.play('spell_cast')
                self._apply_spell_effect(spell, chain, target)
                _qs_spell = getattr(self, 'quirk_system', None)
                if _qs_spell:
                    hp_pct = self.player.hp / max(1, self.player.max_hp)
                    _qs_spell.on_spell_cast(hp_pct)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='chain',
            subject='science',
            tier=spell['quiz_tier'],
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
        )

    def _apply_spell_effect(self, spell: dict, chain: int, target=None):
        """Apply a learned spell's effect. Chain 1-5 scales damage/duration."""
        import types
        effect = spell['effect']
        power  = spell.get('power', '')

        # Scale duration/damage with chain
        chain_scale = chain / 5.0   # 0.2 .. 1.0

        # Handle the two spell-specific effects not in wand system
        if effect == 'displacement_self':
            dur = max(5, int(20 * chain_scale))
            self.player.add_effect('displacement', dur)
            self.add_message(f"Your image displaces! ({dur} turns)", 'success')
            return

        if effect == 'mass_ice':
            from dice import roll
            base_dmg = roll(power) if power else 10
            scaled   = max(1, int(base_dmg * chain_scale))
            hit = 0
            for m in list(self.monsters):
                if m.alive and (m.x, m.y) in self.visible:
                    m.take_damage(scaled)
                    if not m.alive:
                        self._on_monster_killed(m)
                    hit += 1
            self.add_message(
                f"Ice Storm! {hit} monsters take {scaled} cold dmg (chain {chain})", 'success')
            return

        # Scale extra_heal duration/amount
        if effect == 'extra_heal':
            from dice import roll
            base = roll(power) if power else 8
            healed = max(1, int(base * chain_scale))
            self.player.restore_hp(healed)
            self.add_message(f"You are healed for {healed} HP! (chain {chain})", 'success')
            return

        # Scale status durations for self-buff spells
        _SELF_BUFF_DURATIONS = {
            'shield_self':       ('shielded',    12),
            'haste_self':        ('hasted',      10),
            'invisibility_self': ('invisible',   15),
            'light':             ('clairvoyant', 20),
        }
        if effect in _SELF_BUFF_DURATIONS:
            eff_name, base_dur = _SELF_BUFF_DURATIONS[effect]
            dur = max(2, int(base_dur * chain_scale))
            self.player.add_effect(eff_name, dur)
            self.add_message(
                f"{spell['name']} — {eff_name} for {dur} turns! (chain {chain})", 'success')
            return

        # Targeted spells — handle directly so we use the pre-found target
        if target is not None:
            from dice import roll as _roll
            if effect == 'magic_missile':
                base_dmg = _roll(power) if power else 4
                scaled = max(1, int(base_dmg * chain_scale))
                target.hp = max(0, target.hp - scaled)
                if target.hp == 0:
                    target.alive = False
                self.add_message(
                    f"A magic missile strikes the {target.name} for {scaled} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'fire_bolt':
                base_dmg = _roll(power) if power else 8
                scaled = max(1, int(base_dmg * chain_scale))
                actual = target.take_damage(scaled)
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'lightning_bolt':
                base_dmg = _roll(power) if power else 10
                scaled = max(1, int(base_dmg * chain_scale))
                actual = target.take_damage(scaled)
                if actual > 0:
                    target.add_effect('stunned', max(1, int(3 * chain_scale)))
                    self.add_message(
                        f"Lightning strikes the {target.name} for {actual} damage! (chain {chain})", 'success')
                else:
                    self.add_message(f"The {target.name} absorbs the lightning harmlessly.", 'info')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'sleep_monster':
                dur = max(2, int(6 * chain_scale))
                target.add_effect('sleeping', dur)
                self.add_message(f"The {target.name} falls asleep for {dur} turns! (chain {chain})", 'success')
            elif effect == 'confuse_monster':
                dur = max(2, int(10 * chain_scale))
                target.add_effect('confused', dur)
                self.add_message(f"The {target.name} is confused for {dur} turns! (chain {chain})", 'success')
            elif effect == 'paralyze_monster':
                dur = max(2, int(8 * chain_scale))
                target.add_effect('paralyzed', dur)
                self.add_message(f"The {target.name} is paralyzed for {dur} turns! (chain {chain})", 'success')
            else:
                # Fallback: generic targeted damage
                from dice import roll as _r
                scaled = max(1, int((_r(power) if power else 6) * chain_scale))
                actual = target.take_damage(scaled)
                self.add_message(f"The {effect} hits the {target.name} for {actual} dmg! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

    # ------------------------------------------------------------------
    # Scroll menu  (s key — grammar quiz)
    # ------------------------------------------------------------------

    def _open_scroll_menu(self):
        self.scroll_menu_items = [
            i for i in self.player.inventory if isinstance(i, (Scroll, Spellbook))
        ]
        if not self.scroll_menu_items:
            self.add_message("You have no scrolls or spellbooks to read.", 'info')
            return
        self.state = STATE_SCROLL_MENU

    def _scroll_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.scroll_menu_items):
            return
        self.state = STATE_PLAYER
        item = self.scroll_menu_items[idx]
        if isinstance(item, Spellbook):
            self._learn_from_spellbook(item)
        else:
            self._read_scroll(item)

    def _read_scroll(self, scroll: 'Scroll'):
        display = self._display_name(scroll)
        self.quiz_title = f"READING {display.upper()}  —  GRAMMAR"
        self.state = STATE_QUIZ
        _was_identified_before = getattr(scroll, 'identified', False) or \
            scroll.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER
            scroll.identified = True
            self.player.known_item_ids.add(scroll.id)
            self.player.remove_from_inventory(scroll)

            if not result.success:
                self.add_message(
                    "You stumble over the words — the scroll crumbles unread.", 'warning'
                )
                self._advance_turn()
                return

            self.add_message(f"You read the {display}!", 'success')
            _qs_scroll = getattr(self, 'quirk_system', None)
            if _qs_scroll:
                _qs_scroll.on_scroll_read(scroll.id, was_identified=_was_identified_before)
            self._apply_scroll_effect(scroll)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='grammar',
            tier=scroll.quiz_tier,
            callback=on_complete,
            threshold=scroll.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('grammar'),
        )

    def _apply_scroll_effect(self, scroll: 'Scroll'):
        from dice import roll
        effect = scroll.effect

        if effect == 'heal':
            amount = roll(scroll.power) if scroll.power else 10
            self.player.restore_hp(amount)
            self.add_message(f"Healing light washes over you — {amount} HP restored!", 'success')

        elif effect == 'boss_reward':
            code = scroll.power or '???'
            self.add_message(f"★ BOSS REWARD CODE: {code} ★", 'loot')
            self.add_message("Show this code to Dad in real life for a reward!", 'success')
            self.add_message("You can re-read this scroll at any time to see the code again.", 'info')
            # Put the scroll back in inventory so the player can re-read it
            self.player.inventory.append(scroll)
            return  # skip the remove that the caller does

        elif effect == 'mapping':
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored.add((x, y))
            self.add_message("The dungeon layout floods your mind!", 'success')

        elif effect == 'identify':
            # Auto-identify first unknown item in inventory
            unknown = next(
                (i for i in self.player.inventory
                 if hasattr(i, 'identified') and not i.identified
                    and i.id not in self.player.known_item_ids),
                None
            )
            if unknown:
                unknown.identified = True
                self.player.known_item_ids.add(unknown.id)
                self._propagate_identification(unknown.id)
                self.add_message(f"The {unknown.unidentified_name} is revealed: {unknown.name}!", 'success')
                if unknown.lore:
                    self._lore_subject = unknown
                    self.state = STATE_LORE
            else:
                self.add_message("All your items are already identified.", 'info')

        elif effect == 'enchant_weapon':
            if self.player.weapon:
                self.player.weapon.enchant_bonus += 1
                self.add_message(
                    f"Your {self.player.weapon.name} glows — enchant +{self.player.weapon.enchant_bonus}!",
                    'success'
                )
            else:
                self.add_message("You have no weapon to enchant.", 'info')

        elif effect == 'remove_curse':
            from status_effects import DEBUFFS
            removed = [e for e in list(self.player.status_effects) if e in DEBUFFS]
            for e in removed:
                del self.player.status_effects[e]
            # Also remove the cursed flag from any equipped items
            cursed_items = []
            all_equipped = []
            if self.player.weapon:
                all_equipped.append(self.player.weapon)
            all_equipped.extend(s for s in self.player.armor_slots if s)
            if self.player.shield:
                all_equipped.append(self.player.shield)
            all_equipped.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
            for eq in all_equipped:
                if getattr(eq, 'cursed', False):
                    eq.cursed = False
                    cursed_items.append(eq.name)
            if removed or cursed_items:
                parts = []
                if removed:
                    parts.append(f"status effects: {', '.join(removed)}")
                if cursed_items:
                    parts.append(f"cursed items: {', '.join(cursed_items)}")
                self.add_message(f"A cleansing light removes {' and '.join(parts)}.", 'success')
            else:
                self.add_message("You feel purified (no curses to remove).", 'info')

        elif effect == 'confuse_monsters':
            count = 0
            for m in self.monsters:
                if m.alive and (m.x, m.y) in self.visible:
                    m.add_effect('confused', 8)
                    count += 1
            if count:
                self.add_message(f"{count} monster(s) reel in confusion!", 'success')
            else:
                self.add_message("No monsters are in sight to confuse.", 'info')

        # ── Tier 3 scroll effects ──────────────────────────────────────────
        elif effect == 'sleep_monsters':
            targets = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in targets:
                m.add_effect('sleeping', 8)
            if targets:
                self.add_message(f"A wave of slumber washes out — {len(targets)} creature(s) fall asleep!", 'success')
            else:
                self.add_message("No creatures are in sight to affect.", 'info')

        elif effect == 'haste_self':
            duration = int(scroll.power) if scroll.power else 15
            self.player.add_effect('hasted', duration)
            self.add_message(f"Energy surges through you — hasted for {duration} turns!", 'success')

        elif effect == 'enchant_armor':
            # Find the best-slotted armor piece to enchant
            equipped = [s for s in self.player.armor_slots if s is not None]
            if equipped:
                target = equipped[0]
                target.enchant_bonus = getattr(target, 'enchant_bonus', 0) + 1
                self.add_message(
                    f"Your {target.name} shines — enchant +{target.enchant_bonus}!", 'success'
                )
            else:
                self.add_message("You wear no armor to enchant.", 'info')

        elif effect == 'enchant_item':
            # Enchant any single equipped item — apply highest bonus to most important slot
            candidates = []
            if self.player.weapon:
                candidates.append(self.player.weapon)
            for s in self.player.armor_slots:
                if s:
                    candidates.append(s)
            if self.player.shield:
                candidates.append(self.player.shield)
            for s in getattr(self.player, 'accessory_slots', []):
                if s:
                    candidates.append(s)
            if candidates:
                # Auto-pick: prefer weapon if available, otherwise first armor
                target = candidates[0]
                target.enchant_bonus = getattr(target, 'enchant_bonus', 0) + 1
                self.add_message(
                    f"A golden light infuses your {target.name} — enchant +{target.enchant_bonus}!",
                    'success'
                )
            else:
                self.add_message("You have no equipped items to enchant.", 'info')

        # ── Tier 4 scroll effects ──────────────────────────────────────────
        elif effect == 'teleport_self':
            self._teleport_player()

        elif effect == 'charging':
            from items import Wand
            wands = [i for i in self.player.inventory if isinstance(i, Wand)]
            if wands:
                for w in wands:
                    w.charges = min(w.max_charges, w.charges + 1)
                self.add_message(
                    f"Magical energy crackles into {len(wands)} wand(s) — each recharged by 1!", 'success'
                )
            else:
                self.add_message("You carry no wands to charge.", 'info')

        elif effect == 'identify_all':
            unknown = [i for i in self.player.inventory
                       if hasattr(i, 'identified') and not i.identified]
            if unknown:
                for item in unknown:
                    item.identified = True
                    self.player.known_item_ids.add(item.id)
                self.add_message(
                    f"A flash of revelation — {len(unknown)} item(s) identified!", 'success'
                )
            else:
                self.add_message("All your items are already identified.", 'info')

        # ── Tier 5 scroll effects ──────────────────────────────────────────
        elif effect == 'annihilate':
            victims = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in victims:
                m.hp = 0
                m.alive = False
                self._on_monster_killed(m)
            if victims:
                self.add_message(
                    f"A blinding flash of white energy obliterates {len(victims)} creature(s)!", 'success'
                )
            else:
                self.add_message("No creatures are visible to annihilate.", 'info')

        elif effect == 'time_stop_scroll':
            duration = int(scroll.power) if scroll.power else 10
            self.player.add_effect('time_stopped', duration)
            self.add_message(f"Time itself halts — {duration} turns of absolute stillness!", 'success')

        elif effect == 'great_power':
            for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                self.player.apply_stat_bonus(stat, 1)
            self.add_message("Every faculty within you is elevated! All stats permanently +1!", 'success')

        elif effect == 'lake_of_fire':
            # The inscription is always revealed
            self.add_message(
                '"Then Death and Hades were thrown into the lake of fire."', 'info'
            )
            # Keep the scroll in inventory — it may need to be read again
            self.player.inventory.append(scroll)

            # Check if the Abyss conditions are met
            shimmer = next(
                (g for g in self.ground_items if g.id == 'abyssal_shimmer' and g.activated),
                None
            )
            complete_on_shimmer = shimmer and any(
                g.id == 'complete_tablet_of_second_death'
                and g.x == shimmer.x and g.y == shimmer.y
                for g in self.ground_items
            )
            death_on_shimmer = (
                self.death_pursues
                and self.death_monster is not None
                and shimmer is not None
                and self.death_monster.x == shimmer.x
                and self.death_monster.y == shimmer.y
            )
            if shimmer and complete_on_shimmer and death_on_shimmer:
                self._trigger_abyss(shimmer)

    # ------------------------------------------------------------------
    # Identify menu  (i key — philosophy quiz)
    # ------------------------------------------------------------------

    def _open_identify_menu(self):
        # Require the Philosopher's Amulet in inventory
        has_amulet = any(
            getattr(i, 'id', '') == 'philosophers_amulet'
            for i in self.player.inventory
        ) or any(
            getattr(i, 'id', '') == 'philosophers_amulet'
            for slot in self.player.accessory_slots if slot is not None
            for i in [slot]
        )
        if not has_amulet:
            self.add_message("You need the Philosopher's Amulet to identify items.", 'warning')
            return
        inv_items = [
            i for i in self.player.inventory
            if hasattr(i, 'identified') and not i.identified
               and i.id not in self.player.known_item_ids
        ]
        ground_items = [
            i for i in self.ground_items
            if i.x == self.player.x and i.y == self.player.y
               and hasattr(i, 'identified') and not i.identified
               and i.id not in self.player.known_item_ids
        ]
        # Corpses on the current tile that haven't been lore-identified yet
        corpses = [
            i for i in self.ground_items
            if i.x == self.player.x and i.y == self.player.y
               and isinstance(i, Corpse)
        ]
        # Store as (item, is_ground, is_corpse) tuples
        self.identify_menu_items = (
            [(i, False, False) for i in inv_items]
            + [(i, True,  False) for i in ground_items]
            + [(i, True,  True)  for i in corpses]
        )
        if not self.identify_menu_items:
            self.add_message("Nothing here to identify or examine.", 'info')
            return
        self.state = STATE_IDENTIFY_MENU

    def _identify_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.identify_menu_items):
            return
        self.state = STATE_PLAYER
        item, is_ground, is_corpse = self.identify_menu_items[idx]
        if is_corpse:
            self._examine_corpse_direct(item)
        else:
            self._identify_item(item)

    def _identify_item(self, item):
        display = self._display_name(item)
        self.quiz_title = f"IDENTIFYING {display.upper()}  —  PHILOSOPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                item.identified = True
                self.player.known_item_ids.add(item.id)
                # Propagate to ALL items: inventory, ground, and every stored level
                self._propagate_identification(item.id)
                self.add_message(
                    f"The {display} is revealed: {item.name}!", 'success'
                )
                # Show lore screen for the identified item
                if item.lore:
                    self._lore_subject = item
                    self.state = STATE_LORE
            else:
                self.add_message(
                    f"You ponder the {display} but gain no insight.", 'warning'
                )
            self._advance_turn()

        # Identification threshold scales with item tier: tier 1 → 2/3 qs, tier 5 → 6/9 qs
        id_tier = getattr(item, 'quiz_tier', 1)
        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='philosophy',
            tier=id_tier,
            callback=on_complete,
            threshold=id_tier + 1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
        )

    def _learn_from_spellbook(self, book: 'Spellbook'):
        """Try to learn the spell in a spellbook via philosophy threshold quiz."""
        spell_id = book.spell_id
        if spell_id in self.player.known_spells:
            self.add_message(f"You already know {book.spell_name}.", 'info')
            return

        self.state = STATE_QUIZ
        self.quiz_title = f"DECIPHER SPELLBOOK — PHILOSOPHY"

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                mp_cost = book.mp_cost
                self.player.known_spells[spell_id] = mp_cost
                book.identified = True
                self.player.remove_from_inventory(book)
                self.add_message(
                    f"You master the arcane text! {book.spell_name} learned! (costs {mp_cost} MP)", 'success')
            else:
                self.add_message(
                    "The text resists your understanding. Try again.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='philosophy',
            tier=book.quiz_tier,
            callback=on_complete,
            threshold=book.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
        )

    def _propagate_identification(self, item_id: str):
        """Record that the player now recognises this item type by ID.

        We do NOT set item.identified = True on other instances — that flag
        means 'this specific copy has been examined and modifiers are known'.
        Type recognition is tracked solely via player.known_item_ids.
        """
        self.player.known_item_ids.add(item_id)

    # ------------------------------------------------------------------
    # Display name helper
    # ------------------------------------------------------------------

    @staticmethod
    def _fix_name_case(name: str) -> str:
        """Apply Title Case only if the name is entirely lowercase (avoids breaking 'STR+1' etc.)."""
        if name == name.lower():
            return name.title()
        return name

    def _display_name(self, item) -> str:
        """Return the name to show for an item, including stack count when > 1.

        Type known  (item.id in known_item_ids OR item.identified) → item.name
        Type unknown                                                → item.unidentified_name
        Modifier info (+N, {C}) is NEVER shown here — only the sidebar
        shows modifiers, and only when item.identified (instance examined).
        """
        if not hasattr(item, 'identified'):
            base = self._fix_name_case(item.name)
        elif item.identified or item.id in self.player.known_item_ids:
            base = self._fix_name_case(item.name)
        else:
            base = self._fix_name_case(getattr(item, 'unidentified_name', item.name))
        count = getattr(item, 'count', 1)
        return f"{base} x{count}" if count > 1 else base

    # ------------------------------------------------------------------
    # Ranged targeting
    # ------------------------------------------------------------------

    def _open_targeting(self):
        """Enter targeting mode for ranged attacks (f key)."""
        weapon = self.player.weapon
        if not weapon or not weapon.requires_ammo:
            self.add_message("You have no ranged weapon equipped.", 'warning')
            return

        # Check ammo
        ammo_type = weapon.requires_ammo
        ammo_items = [i for i in self.player.inventory
                      if getattr(i, 'ammo_type', None) == ammo_type]
        if not ammo_items:
            self.add_message(
                f"You have no {ammo_type}s! Cannot fire the {weapon.name}.", 'warning'
            )
            return

        # Build candidate list: visible alive monsters sorted by distance
        px, py = self.player.x, self.player.y
        from combat import can_ranged_attack
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
            and can_ranged_attack(self.player, m, self.dungeon)
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            # No valid targets — cursor starts on player
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        if candidates:
            self.add_message(
                f"Targeting with {weapon.name} — arrow keys to move, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info'
            )
        else:
            self.add_message(
                f"No targets in range for {weapon.name}. Move cursor with arrow keys, ENTER to fire, ESC to cancel.",
                'info'
            )

    _TARGET_MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0), pygame.K_h: (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
        pygame.K_KP7:   (-1,-1), pygame.K_KP8: (0,-1), pygame.K_KP9: (1,-1),
        pygame.K_KP4:   (-1, 0), pygame.K_KP6: (1, 0),
        pygame.K_KP1:   (-1, 1), pygame.K_KP2: (0, 1), pygame.K_KP3: (1, 1),
    }

    def _target_input(self, key: int):
        """Handle key input while in targeting mode."""
        # TAB / t — cycle through valid monster targets
        if key in (pygame.K_TAB, pygame.K_t) and self._target_candidates:
            self._target_idx = (self._target_idx + 1) % len(self._target_candidates)
            m = self._target_candidates[self._target_idx]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
            return

        # Arrow / vi keys — free cursor movement
        if key in self._TARGET_MOVE_KEYS:
            dx, dy = self._TARGET_MOVE_KEYS[key]
            self.target_cursor_x += dx
            self.target_cursor_y += dy
            # Clamp to dungeon bounds
            self.target_cursor_x = max(0, min(self.target_cursor_x, self.dungeon.width - 1))
            self.target_cursor_y = max(0, min(self.target_cursor_y, self.dungeon.height - 1))
            return

        # ENTER / SPACE / f — confirm shot
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_f):
            # Find monster at cursor
            target = next(
                (m for m in self.monsters
                 if m.alive and m.x == self.target_cursor_x and m.y == self.target_cursor_y),
                None
            )
            self.state = STATE_PLAYER
            if target:
                from combat import can_ranged_attack
                if can_ranged_attack(self.player, target, self.dungeon):
                    self._fire_ranged(target)
                else:
                    self.add_message("No clear line of sight to that target.", 'warning')
            else:
                self.add_message("No target there — shot cancelled.", 'warning')

    def _fire_ranged(self, monster):
        """Consume one ammo and launch the math chain quiz for a ranged shot."""
        weapon = self.player.weapon
        ammo_type = weapon.requires_ammo

        # Consume one ammo item from inventory
        ammo_item = next(
            (i for i in self.player.inventory
             if getattr(i, 'ammo_type', None) == ammo_type),
            None
        )
        if not ammo_item:
            self.add_message(f"Out of {ammo_type}s!", 'warning')
            return

        # Decrement stack or remove
        if getattr(ammo_item, 'count', 1) > 1:
            ammo_item.count -= 1
        else:
            self.player.inventory.remove(ammo_item)

        self.state = STATE_QUIZ
        self.combat_target = monster
        dist = max(abs(weapon.reach - (abs(monster.x - self.player.x) +
                                        abs(monster.y - self.player.y))), 1)
        self.quiz_title = (
            f"FIRE {weapon.name.upper()} at {monster.name.upper()}  —  MATH CHAIN"
        )

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False):
            self.state = STATE_PLAYER
            self.combat_target = None
            if chain == 0:
                self.add_message(
                    f"Your shot flies wide — you miss the {monster.name}!", 'warning'
                )
            else:
                self.add_message(
                    f"Chain x{chain}! Your {weapon.requires_ammo} strikes the {monster.name} for {damage} damage!",
                    'success'
                )
                if killed:
                    self.level_mgr.monsters_killed += 1
                    self.add_message(f"The {monster.name} is slain!", 'success')
                    self._drop_treasure(monster)
                    self.ground_items.append(self._make_corpse(monster))
                    _qs_rng = getattr(self, 'quirk_system', None)
                    if _qs_rng:
                        _qs_rng.on_kill(
                            monster_kind=monster.kind,
                            chain_score=chain,
                            ranged=True,
                            unarmed=False,
                            hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                            is_feared=self.player.has_effect('feared'),
                        )
            self._advance_turn()

        player_attack(self.player, monster, self.quiz_engine, on_complete, ammo=ammo_item)

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def _start_combat(self, monster):
        # Charmed: 40% chance to hesitate instead of attacking
        if self.player.has_effect('charmed') and random.random() < 0.40:
            self.add_message("You hesitate, unable to bring yourself to attack.", 'warning')
            self._advance_turn()
            return

        self.state = STATE_QUIZ
        self.combat_target = monster
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  —  MATH CHAIN"
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_combat_started()
        self._combat_hp_pct_before = self.player.hp / max(1, self.player.max_hp)

        if monster.kind == 'floating_eye':
            cur = self.player.status_effects.get('paralyzed', 0)
            self.player.status_effects['paralyzed'] = max(cur, 3)
            self.add_message("The floating eye's gaze paralyzes you!", 'danger')

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False):
            self.state = STATE_PLAYER
            self.combat_target = None
            if chain == 0:
                self.add_message(
                    f"You swing wildly at the {monster.name} and miss!", 'warning'
                )
            else:
                if damage > 0:
                    _snd.play('monster_hit')
                if crit:
                    msg = f"CRITICAL! Chain x{chain}! You strike the {monster.name} for {damage} damage!"
                else:
                    msg = f"Chain x{chain}! You strike the {monster.name} for {damage} damage!"
                if stunned:
                    msg += f" The {monster.name} is stunned!"
                if monster.status_effects.get('bleeding', 0) > 0:
                    msg += f" The {monster.name} is bleeding!"
                if knocked and not killed:
                    from combat import apply_knockback
                    apply_knockback(self.player, monster, self.dungeon, self.monsters)
                    msg += f" The {monster.name} is knocked back!"
                self.add_message(msg, 'success')
                if killed:
                    self.level_mgr.monsters_killed += 1
                    self.add_message(f"The {monster.name} is slain!", 'success')
                    self._drop_treasure(monster)
                    self.ground_items.append(self._make_corpse(monster))
                    _qs_kill = getattr(self, 'quirk_system', None)
                    if _qs_kill:
                        _qs_kill.on_kill(
                            monster_kind=monster.kind,
                            chain_score=chain,
                            ranged=False,
                            unarmed=(self.player.weapon is None),
                            hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                            is_feared=self.player.has_effect('feared'),
                        )
            self._advance_turn()

        player_attack(self.player, monster, self.quiz_engine, on_complete)

    def _quiz_input(self, key: int):
        if self.quiz_engine.state != QuizState.ASKING:
            return
        q = self.quiz_engine.current_question
        if not q:
            return
        choices = q.get('choices', [])
        key_map = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
        }
        idx = key_map.get(key)
        if idx is not None and idx < len(choices):
            qe = self.quiz_engine
            # Map displayed position back to actual choice via confused_order
            if qe.confused_order and len(qe.confused_order) == len(choices):
                actual_idx = qe.confused_order[idx]
            else:
                actual_idx = idx
            self.quiz_engine.answer(choices[actual_idx])

    # ------------------------------------------------------------------
    # Monster turns
    # ------------------------------------------------------------------

    def _do_monster_turns(self):
        # Time stop: monsters are frozen this turn
        if self.player.has_effect('time_stopped'):
            return

        # Death acts first — it is not part of self.monsters to avoid save/load issues
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            all_m = self.monsters + [dm]
            did_attack = dm.take_turn(self.player, self.dungeon, all_m)
            if did_attack:
                dmg, msg = dm.attack(self.player)
                self.add_message(msg, 'danger')
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

        for m in self.monsters:
            if not m.alive:
                continue
            # Track monsters the player has seen (for encyclopedia bestiary)
            if (m.x, m.y) in self.visible:
                self.player.known_monster_ids.add(m.kind)
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters)
            if did_attack:
                # Displacement: 30% miss chance
                if self.player.has_effect('displacement') and random.random() < 0.30:
                    self.add_message(f"The {m.name}'s attack passes through your displaced image!", 'info')
                    continue

                _effects_before = set(self.player.status_effects.keys())
                dmg, msg = m.attack(self.player)
                self.add_message(msg, 'danger')

                # Fire shield: reflect melee damage back
                if self.player.has_effect('fire_shield') and dmg > 0:
                    reflect_dmg = random.randint(2, 9)
                    m.hp -= reflect_dmg
                    self.add_message(f"Flames lash back at the {m.name} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0:
                        m.alive = False
                        self._on_monster_killed(m)
                # Cold shield: reflect melee damage back
                if self.player.has_effect('cold_shield') and dmg > 0:
                    reflect_dmg = random.randint(2, 9)
                    m.hp -= reflect_dmg
                    self.add_message(f"Ice shatters back at the {m.name} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0 and m.alive:
                        m.alive = False
                        self._on_monster_killed(m)

                # Reflecting: negate 50% of newly applied status effects
                _new_effects = set(self.player.status_effects.keys()) - _effects_before
                if self.player.has_effect('reflecting') and _new_effects:
                    for _new_eff in list(_new_effects):
                        if random.random() < 0.50:
                            del self.player.status_effects[_new_eff]
                            self.add_message(f"Your reflection aura deflects the {_new_eff.replace('_', ' ')}!", 'info')
                            _new_effects.discard(_new_eff)
                            _qs_refl = getattr(self, 'quirk_system', None)
                            if _qs_refl:
                                _qs_refl.on_status_reflected()

                if dmg > 0:
                    _snd.play('player_hit')
                _qs_dmg = getattr(self, 'quirk_system', None)
                if _qs_dmg and self.player:
                    if dmg > 0:
                        _qs_dmg.on_take_damage(dmg, dmg / max(1, self.player.max_hp))
                    # Notify quirk system of newly applied status effects (after reflection)
                    for _new_eff in set(self.player.status_effects.keys()) - _effects_before:
                        _qs_dmg.on_status_applied(_new_eff, m.kind)
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    # Arrow keys that trigger held-movement (only these four, not vi keys)
    _ARROW_KEYS = {
        pygame.K_UP:    (0, -1),
        pygame.K_DOWN:  (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0),
    }
    _MOVE_HOLD_INTERVAL = 0.07  # seconds between repeated moves once repeat is active

    def update(self, dt: float):
        if self.state == STATE_QUIZ:
            self.quiz_engine.update(dt)

        if self.state == STATE_PLAYER:
            pressed = pygame.key.get_pressed()
            held_dir = None
            for k, d in self._ARROW_KEYS.items():
                if pressed[k]:
                    held_dir = d
                    break

            prev = getattr(self, '_prev_held_dir', None)
            if held_dir != prev:
                # Direction changed (or key released/pressed) — restart delay
                self._move_hold_timer = self._move_hold_delay if held_dir else 0.0
                self._move_hold_first = True
            elif held_dir is not None:
                self._move_hold_timer -= dt
                if self._move_hold_timer <= 0:
                    self._move_hold_timer = self._MOVE_HOLD_INTERVAL
                    self._do_move(*held_dir)
            self._prev_held_dir = held_dir

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self):
        cam_x, cam_y = self._camera()
        self.screen.fill((0, 0, 0))

        game_clip = pygame.Rect(0, 0, GAME_W, GAME_H)
        self.screen.set_clip(game_clip)
        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)
        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)
        for m in self.monsters:
            if m.alive:
                self.renderer.draw_entity(m.x, m.y, m.color, cam_x, cam_y, self.visible, mid=m.kind)
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
                self.renderer.draw_entity(item.x, item.y, (r, g, b), cam_x, cam_y, self.visible)

        # Death: always visible when in FOV; drawn with a pale spectral pulse
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            if (dm.x, dm.y) in self.visible:
                # Pulse between bone-white and ghostly blue
                pulse = abs((self.turn_count % 20) - 10) / 10.0   # 0.0–1.0
                r = int(200 + 55 * pulse)
                g = int(200 + 55 * pulse)
                b = 255
                self.renderer.draw_entity(dm.x, dm.y, (r, g, b), cam_x, cam_y, self.visible, mid='death')
        _pspr = (self.secret_build or {}).get('_sprite', 'player')
        self.renderer.draw_player(self.player, cam_x, cam_y, sprite_name=_pspr)
        self.screen.set_clip(None)

        self.msg_log.draw(self.screen, 0, GAME_H, GAME_W, MSG_H)
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
        elif self.state == STATE_IDENTIFY_MENU:
            self._draw_identify_menu()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
        elif self.state == STATE_EAT_MENU:
            self._draw_eat_menu()
        elif self.state == STATE_QUAFF_MENU:
            self._draw_quaff_menu()
        elif self.state == STATE_CONFIRM_EXIT:
            self._draw_confirm_exit()
        elif self.state == STATE_VICTORY:
            self._draw_victory_screen()
        elif self.state == STATE_DEAD:
            self._draw_death_screen()
        elif self.state == STATE_HELP:
            self._draw_help_screen()
        elif self.state == STATE_LORE:
            self._draw_lore_screen()
        elif self.state == STATE_HINT:
            self._draw_hint_screen()
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

        pygame.display.flip()

    def _camera(self) -> tuple[int, int]:
        return 0, 0

    # ------------------------------------------------------------------
    # Targeting overlay
    # ------------------------------------------------------------------

    def _draw_targeting(self, cam_x: int, cam_y: int):
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
        weapon = self.player.weapon
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
                if 0 <= scr_x < GAME_W and 0 <= scr_y < GAME_H:
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
        from combat import can_ranged_attack
        for m in self._target_candidates:
            scr_x, scr_y = w2s(m.x, m.y)
            if 0 <= scr_x < GAME_W and 0 <= scr_y < GAME_H:
                hl = pygame.Surface((T, T), pygame.SRCALPHA)
                hl.fill((255, 200, 0, 60))
                self.screen.blit(hl, (scr_x, scr_y))
                pygame.draw.rect(self.screen, (255, 200, 0), (scr_x, scr_y, T, T), 1)

        # Cursor highlight on target tile
        scr_cx, scr_cy = w2s(cx, cy)
        if 0 <= scr_cx < GAME_W and 0 <= scr_cy < GAME_H:
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
            label = f"Out of range  [arrow keys to move cursor  ESC=cancel]"
            label_color = (255, 160, 40)
        else:
            label = f"No target  [arrow keys to move  TAB=cycle targets  ESC=cancel]"
            label_color = (200, 200, 200)

        label_surf = self.font_sm.render(label, True, label_color)
        label_bg = pygame.Surface((label_surf.get_width() + 16, label_surf.get_height() + 8),
                                  pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 180))
        self.screen.blit(label_bg, (8, GAME_H - label_surf.get_height() - 16))
        self.screen.blit(label_surf, (16, GAME_H - label_surf.get_height() - 12))

    # ------------------------------------------------------------------
    # Quiz modal
    # ------------------------------------------------------------------

    # Subject accent colours — match the welcome screen domain ring
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
    }

    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
        """Break text into lines that fit within max_w pixels."""
        words  = text.split()
        lines  = []
        cur    = ''
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

    def _draw_quiz(self):
        qe = self.quiz_engine
        if not qe.current_question:
            return

        # Celebration takes over the full screen — draw nothing else
        if qe.celebrating:
            self._draw_celebration()
            return

        is_combat = (self.combat_target is not None and qe.mode == QuizMode.CHAIN)
        accent    = self._SUBJECT_COLOR.get(qe.subject, (160, 130, 255))
        accent_dim = tuple(max(0, v - 90) for v in accent)

        # ── Overlay ────────────────────────────────────────────────────
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        # ── Modal geometry ─────────────────────────────────────────────
        bw = min(1060, GAME_W - 40)
        PAD = 24

        # Question text (wrapped) — calculate height first
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
        KEY_W    = 68         # width of [1] key hint area — must be wider than the rendered badge
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

        bx = (GAME_W - bw) // 2
        by = max(20, (WINDOW_H - bh) // 2)

        # FANTASY: Arcane grimoire quiz panel
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=accent)
        draw_header_bar(self.screen, (bx, by, bw, HEADER_H),
                        text=self.quiz_title, font=self.font_md,
                        text_color=FP.GOLD_BRIGHT, accent=accent)

        # Mode / progress counter (top-right)
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            c_text, c_color = f"Chain ×{qe.chain}", (80, 255, 140)
        else:
            c_text  = f"{qe.correct_count} / {qe.required}"
            c_color = (120, 200, 255)
        c_surf = self.font_md.render(c_text, True, c_color)
        self.screen.blit(c_surf, (bx + bw - c_surf.get_width() - PAD,
                                   by + (HEADER_H - c_surf.get_height()) // 2))

        # ── Timer bar ─────────────────────────────────────────────────
        ty        = by + HEADER_H + 6
        bar_x     = bx + PAD
        bar_w     = bw - PAD * 2
        bar_h     = 14

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

        # Timer seconds label — right-aligned inside the bar
        secs = int(qe.time_remaining)
        t_label = self.font_sm.render(f"{secs}s", True, (255, 255, 255))
        lx = bar_x + bar_w - t_label.get_width() - 4
        ly = ty + (bar_h - t_label.get_height()) // 2
        self.screen.blit(t_label, (lx, ly))

        # ── Question text ─────────────────────────────────────────────
        qy = ty + TIMER_H
        for line in q_lines:
            surf = q_font.render(line, True, (255, 245, 210))
            self.screen.blit(surf, (bx + PAD, qy))
            qy += q_line_h
        qy += SECTION_GAP

        # Thin separator
        pygame.draw.line(self.screen, accent_dim, (bx + PAD, qy - 4), (bx + bw - PAD, qy - 4))

        # ── Choice cards (2 × 2 grid) ─────────────────────────────────
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

            # Key hint — rune-stone style
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

        # ── Status / feedback bar ─────────────────────────────────────
        status_y = qy + 2 * (ch_height + GAP) + SECTION_GAP

        if in_result:
            fb_text  = "✦  CORRECT!" if qe.last_correct else "✦  WRONG!"
            fb_color = (80, 255, 100) if qe.last_correct else (255, 80, 80)
            fb_surf  = self.font_lg.render(fb_text, True, fb_color)
            self.screen.blit(fb_surf, (bx + (bw - fb_surf.get_width()) // 2, status_y))
        elif qe.state == QuizState.ASKING:
            hint = self.font_sm.render("Press  1  2  3  4  to answer", True, (90, 85, 130))
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, status_y + 10))

        # ── Combat HUD ────────────────────────────────────────────────
        if is_combat:
            self._draw_combat_hud(bx, status_y + STATUS_H + SECTION_GAP, bw, accent)


    def _draw_celebration(self):
        """Full-screen clean celebration screen for MAX CHAIN."""
        qe    = self.quiz_engine
        t     = qe.celebration_timer
        pulse = abs(math.sin(t * 6))

        # Pure black background — quiz modal is gone
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, WINDOW_W, WINDOW_H))

        # Warm pulsing golden glow wash
        glow_ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        glow_ov.fill((80, 55, 0, int(50 + 40 * pulse)))
        self.screen.blit(glow_ov, (0, 0))

        # Main "MAX CHAIN!" headline
        cel_font = self.font_xl
        glow_col = (255, int(200 + 55 * pulse), int(40 + 80 * pulse))
        cel_surf = cel_font.render(qe.celebration_text, True, glow_col)
        shadow   = cel_font.render(qe.celebration_text, True, (0, 0, 0))
        cx = (WINDOW_W - cel_surf.get_width())  // 2
        cy = (WINDOW_H - cel_surf.get_height()) // 2 - 40
        self.screen.blit(shadow,   (cx + 5, cy + 5))
        self.screen.blit(cel_surf, (cx, cy))

        # Sub-line
        sub_surf = self.font_lg.render("PERFECT COMBO!", True, (180, 255, 180))
        self.screen.blit(sub_surf,
                         ((WINDOW_W - sub_surf.get_width()) // 2,
                          cy + cel_surf.get_height() + 14))

    def _draw_combat_hud(self, bx: int, strip_y: int, bw: int, accent=(80, 80, 180)):
        """Draw monster HP bar + chain damage preview inside the quiz modal."""
        from combat import _damage_multiplier
        monster = self.combat_target
        weapon  = self.player.weapon

        # Separator
        pygame.draw.line(self.screen, accent,
                         (bx + 18, strip_y), (bx + bw - 18, strip_y))

        sy = strip_y + 10

        # ── Left: monster name + HP bar ───────────────────────────────
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

        # ── Right: damage preview + weapon ───────────────────────────
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

        # Chain table: colour each step by heat (low→high damage)
        parts = []
        for i, mult in enumerate(mults[:6]):
            dmg = max(1, int((base + enchant) * mult * dm))
            parts.append((f"×{i+1}:{dmg}", dmg))
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

    # ------------------------------------------------------------------
    # Equip menu overlay
    # ------------------------------------------------------------------

    def _draw_equip_menu(self):
        # FANTASY: Grimoire-themed equip menu
        draw_overlay(self.screen, 160)

        n_equip   = len(self.equip_menu_items)
        n_unequip = len(self.equip_menu_equipped)
        row_h     = 62
        sep_h     = 30   # height of section separator label
        total_rows = n_equip + n_unequip + (1 if n_equip and n_unequip else 0)
        bw = min(760, GAME_W - 40)
        bh = min(88 + total_rows * row_h + (sep_h if n_equip and n_unequip else 0) + 64,
                 WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="EQUIP / UNEQUIP",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        p = self.player
        weapon_name = self._display_name(p.weapon) if p.weapon else 'none'
        self.screen.blit(
            self.font_sm.render(
                f"Weapon: {weapon_name}   AC: {p.get_ac()}",
                True, FP.BODY_TEXT
            ),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        cy = by + 82

        # ── EQUIP section ─────────────────────────────────────────────
        if n_equip:
            self.screen.blit(
                self.font_sm.render("EQUIP FROM INVENTORY  (number keys)", True, FP.GOLD_BRIGHT),
                (bx + 18, cy)
            )
            cy += sep_h
            for i, item in enumerate(self.equip_menu_items):
                iy = cy
                pygame.draw.rect(
                    self.screen,
                    FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                    (bx + 10, iy, bw - 20, 56), border_radius=6
                )
                self.screen.blit(
                    self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 12)
                )
                self.screen.blit(
                    self.font_md.render(self._display_name(item), True, FP.BODY_TEXT),
                    (bx + 70, iy + 12)
                )
                if isinstance(item, Weapon):
                    dmg_str = f"{item.base_damage}dmg" if item.base_damage else (item.damage or "?")
                    detail_text = f"{item.weapon_class}  {dmg_str}  chain x{item.max_chain_length or '?'}  tier {item.quiz_tier}"
                elif isinstance(item, Shield):
                    detail_text = f"+{item.ac_bonus} AC"
                elif isinstance(item, Armor):
                    detail_text = f"{getattr(item, 'slot', 'armor')}  +{item.ac_bonus} AC"
                elif isinstance(item, Accessory):
                    if item.identified or item.id in self.player.known_item_ids:
                        fx = item.effects
                        if 'status' in fx:
                            detail_text = f"grants {fx['status']}"
                        else:
                            detail_text = f"{fx.get('stat','?')} +{fx.get('amount',0)}"
                    else:
                        detail_text = "unidentified accessory"
                else:
                    detail_text = item.item_class
                detail_col = FP.BODY_TEXT if isinstance(item, (Weapon, Armor, Shield, Accessory)) else FP.FADED_TEXT
                detail_surf = self.font_sm.render(detail_text, True, detail_col)
                if detail_surf.get_width() > max_detail_w:
                    while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                        detail_text = detail_text[:-1]
                    detail_surf = self.font_sm.render(detail_text + '\u2026', True, detail_col)
                self.screen.blit(detail_surf, (bx + 70, iy + 38))
                cy += row_h

        # ── UNEQUIP section ───────────────────────────────────────────
        if n_unequip:
            if n_equip:
                draw_divider(self.screen, bx + 10, cy + 4, bw - 20)
                cy += 12
            self.screen.blit(
                self.font_sm.render("UNEQUIP  (letter keys)", True, FP.WARNING_TEXT),
                (bx + 18, cy)
            )
            cy += sep_h
            letters = 'abcdefgh'
            for i, (slot_name, item) in enumerate(self.equip_menu_equipped):
                iy = cy
                pygame.draw.rect(
                    self.screen,
                    FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                    (bx + 10, iy, bw - 20, 56), border_radius=6
                )
                lbl = letters[i] if i < len(letters) else '?'
                self.screen.blit(
                    self.font_md.render(f"[{lbl}]", True, FP.WARNING_TEXT), (bx + 18, iy + 12)
                )
                cursed = getattr(item, 'cursed', False)
                name_col = FP.DANGER_TEXT if cursed else FP.GOLD_PALE
                self.screen.blit(
                    self.font_md.render(self._display_name(item), True, name_col),
                    (bx + 70, iy + 12)
                )
                detail_text = f"[{slot_name}]"
                if cursed:
                    detail_text += "  CURSED — cannot remove"
                detail_col = FP.DANGER_TEXT if cursed else FP.FADED_TEXT
                self.screen.blit(
                    self.font_sm.render(detail_text, True, detail_col),
                    (bx + 70, iy + 38)
                )
                cy += row_h

        hint_y = by + bh - 36
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint_parts = []
        if n_equip:
            hint_parts.append("1-9: equip")
        if n_unequip:
            hint_parts.append("a-h: unequip")
        hint_parts.append("ESC: cancel")
        hint = self.font_sm.render("  |  ".join(hint_parts), True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Accessory menu overlay
    # ------------------------------------------------------------------

    def _draw_accessory_menu(self):
        # FANTASY: Grimoire-themed accessory menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.accessory_menu_items) * 66 + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with gold border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EQUIP ACCESSORY",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        slots_used = sum(1 for s in self.player.accessory_slots if s is not None)
        self.screen.blit(
            self.font_sm.render(
                f"Accessory slots: {slots_used}/4",
                True, FP.BODY_TEXT
            ),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        for i, item in enumerate(self.accessory_menu_items):
            iy = by + 82 + i * 66
            # FANTASY: Alternating midnight row colors
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            dname = self._display_name(item)
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 14)
            )
            self.screen.blit(
                self.font_md.render(dname, True, FP.BODY_TEXT), (bx + 70, iy + 14)
            )
            if item.identified or item.id in self.player.known_item_ids:
                fx = item.effects
                if 'status' in fx:
                    detail_text = f"grants {fx['status']}"
                else:
                    detail_text = f"{fx.get('stat','?')} +{fx.get('amount',0)}"
            else:
                detail_text = "unidentified"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Wand menu overlay
    # ------------------------------------------------------------------

    def _draw_wand_menu(self):
        # FANTASY: Grimoire-themed wand menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.wand_menu_items) * 66 + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with arcane border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="ZAP WAND",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Nearest visible monster: auto-targeted",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        for i, item in enumerate(self.wand_menu_items):
            iy = by + 82 + i * 66
            # FANTASY: Alternating midnight row colors
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            dname = self._display_name(item)
            charge_color = (
                FP.SUCCESS_TEXT if item.charges > item.max_charges // 2
                else FP.WARNING_TEXT if item.charges > 0
                else FP.DANGER_TEXT
            )
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 14)
            )
            self.screen.blit(
                self.font_md.render(dname, True, FP.BODY_TEXT), (bx + 70, iy + 14)
            )
            charge_surf = self.font_sm.render(f"charges: {item.charges}/{item.max_charges}",
                                              True, charge_color)
            self.screen.blit(charge_surf, (bx + 70, iy + 40))
            if item.identified or item.id in self.player.known_item_ids:
                effect_x = bx + 70 + charge_surf.get_width() + 24
                self.screen.blit(
                    self.font_sm.render(f"effect: {item.effect}", True, FP.GOLD_PALE),
                    (effect_x, iy + 40)
                )

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Spell menu overlay
    # ------------------------------------------------------------------

    def _draw_spell_menu(self):
        draw_overlay(self.screen, 160)
        n_spells = len(self.spell_menu_items)
        ROW_H = 66
        bw = min(820, GAME_W - 40)
        bh = min(96 + n_spells * ROW_H + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text="CAST SPELL",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)
        self.screen.blit(
            self.font_sm.render(f"MP: {self.player.mp}/{self.player.max_mp}",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)
        cy = by + 82
        max_detail_w = bw - 90
        for i, spell_id in enumerate(self.spell_menu_items):
            spell = LEARNABLE_SPELLS.get(spell_id, {})
            key_lbl = chr(ord('a') + i)
            mp_cost = spell.get('mp_cost', '?')
            can_cast = self.player.mp >= int(mp_cost)
            name_color = FP.BODY_TEXT if can_cast else FP.DANGER_TEXT
            tier = spell.get('quiz_tier', 1)
            tier_color = [(180,180,180),(100,200,255),(255,180,80),(200,80,255),(255,100,100)][min(tier-1,4)]
            iy = cy
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, ROW_H - 8), border_radius=6
            )
            self.screen.blit(
                self.font_md.render(f"[{key_lbl}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 12)
            )
            self.screen.blit(
                self.font_md.render(spell.get('name', '?'), True, name_color), (bx + 70, iy + 12)
            )
            detail_text = f"tier {tier}  |  {mp_cost} MP  |  {spell.get('desc','')}"
            detail_surf = self.font_sm.render(detail_text, True, tier_color)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, tier_color)
            self.screen.blit(detail_surf, (bx + 70, iy + 38))
            cy += ROW_H
        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render("a-z: select  |  ESC: cancel", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Scroll menu overlay
    # ------------------------------------------------------------------

    def _draw_scroll_menu(self):
        # FANTASY: Grimoire-themed scroll menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.scroll_menu_items) * 66 + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with gold border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="READ SCROLL / SPELLBOOK",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Scrolls: consumed on use  |  Spellbooks: reusable",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        for i, item in enumerate(self.scroll_menu_items):
            iy = by + 82 + i * 66
            # FANTASY: Alternating midnight row colors
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            dname = self._display_name(item)
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 14)
            )
            is_book = isinstance(item, Spellbook)
            name_color = (100, 200, 255) if is_book else FP.BODY_TEXT
            self.screen.blit(
                self.font_md.render(dname, True, name_color), (bx + 70, iy + 14)
            )
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
                    detail_text = f"effect: {item.effect}"
                else:
                    detail_text = "unknown effect"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Identify menu overlay
    # ------------------------------------------------------------------

    def _draw_identify_menu(self):
        # FANTASY: Grimoire-themed identify menu
        draw_overlay(self.screen, 160)

        n_items = len(self.identify_menu_items)
        ROW_H = 66
        bw = min(820, GAME_W - 40)
        bh = min(96 + n_items * ROW_H + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with arcane border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="IDENTIFY ITEM",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Requires Philosopher's Amulet",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        cy = by + 82

        # Separate into inv, ground, and corpse sections
        inv_entries    = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if not is_g and not is_c]
        ground_entries = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if is_g and not is_c]
        corpse_entries = [(i, item) for i, (item, is_g, is_c) in enumerate(self.identify_menu_items) if is_c]

        def _draw_section(entries, label, label_color, name_color, detail_suffix=''):
            nonlocal cy
            if not entries:
                return
            if cy > by + 82:
                draw_divider(self.screen, bx + 10, cy + 4, bw - 20)
                cy += 12
            self.screen.blit(self.font_sm.render(label, True, label_color), (bx + 18, cy))
            cy += 24
            for i, item in entries:
                iy = cy
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                                 (bx + 10, iy, bw - 20, ROW_H - 8), border_radius=6)
                dname = self._display_name(item)
                self.screen.blit(self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 10))
                self.screen.blit(self.font_md.render(dname, True, name_color), (bx + 70, iy + 10))
                if isinstance(item, Corpse):
                    lore_status = "[EXAMINED]" if item.lore_identified else "[UNEXAMINED]"
                    detail_text = f"Corpse  {lore_status}"
                else:
                    type_label = item.item_class.replace('_', ' ').title()
                    tier_lbl = f"  tier {item.quiz_tier}" if hasattr(item, 'quiz_tier') else ""
                    detail_text = f"{type_label}{tier_lbl}{detail_suffix}"
                detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
                if detail_surf.get_width() > max_detail_w:
                    while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                        detail_text = detail_text[:-1]
                    detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
                self.screen.blit(detail_surf, (bx + 70, iy + 34))
                cy += ROW_H

        _draw_section(inv_entries,    "INVENTORY:",            FP.GOLD_BRIGHT,   FP.BODY_TEXT)
        _draw_section(ground_entries, "ON THE GROUND:",        FP.WARNING_TEXT,  FP.GOLD_PALE,  "  [ground]")
        _draw_section(corpse_entries, "CORPSES (at your feet):", (180, 130, 255), FP.FADED_TEXT)

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Cook menu overlay
    # ------------------------------------------------------------------

    def _draw_cook_menu(self):
        # FANTASY: Grimoire-themed cook menu
        draw_overlay(self.screen, 160)

        n_compound = len(self.cook_compound_recipes)
        n_single   = len(self.cook_menu_items)
        row_h      = 66
        compound_header_h = 30 if n_compound else 0
        single_header_h   = 30 if n_single and n_compound else 0
        bw = min(800, GAME_W - 40)
        bh = min(
            90 + compound_header_h + n_compound * row_h
               + single_header_h   + n_single   * row_h + 70,
            WINDOW_H - 40
        )
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with success (green) border for cooking
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.SUCCESS_TEXT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="COOK INGREDIENT",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render(
                f"SP: {self.player.sp}/{self.player.max_sp}",
                True, FP.BODY_TEXT
            ),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        cy = by + 82
        letter_labels = 'ABCDEF'
        max_detail_w = bw - 90

        # ── Compound (multi-ingredient) recipes ──────────────────────────
        max_header_w = bw - 36
        if n_compound:
            hdr = "COMPOUND RECIPES"
            hdr_surf = self.font_sm.render(hdr, True, FP.GOLD_BRIGHT)
            if hdr_surf.get_width() > max_header_w:
                while len(hdr) > 1 and self.font_sm.size(hdr + '…')[0] > max_header_w:
                    hdr = hdr[:-1]
                hdr_surf = self.font_sm.render(hdr + '…', True, FP.GOLD_BRIGHT)
            self.screen.blit(hdr_surf, (bx + 18, cy))
            cy += compound_header_h
        elif n_single:
            for i, recipe in enumerate(self.cook_compound_recipes[:6]):
                iy = cy
                # FANTASY: Alternating midnight row colors
                pygame.draw.rect(
                    self.screen,
                    FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                    (bx + 10, iy, bw - 20, row_h - 4), border_radius=6
                )
                lbl = letter_labels[i]
                self.screen.blit(
                    self.font_md.render(f"[{lbl}]", True, FP.GOLD_BRIGHT),
                    (bx + 18, iy + 10)
                )
                self.screen.blit(
                    self.font_md.render(recipe['name'], True, FP.GOLD_PALE),
                    (bx + 70, iy + 10)
                )
                # Ingredient list + SP — resolve IDs to display names
                from food_system import _raw_ingredients as _ri
                _ings = _ri()
                def _ing_name(iid): return _ings.get(iid, {}).get('name', iid)
                ing_list = ', '.join(_ing_name(iid) for iid in recipe.get('ingredients', []))
                sp_val   = recipe.get('sp', 0)
                bonus_label = _cook_menu_bonus_label(recipe)
                detail = f"{ing_list}  |  {sp_val} SP  {bonus_label}"
                detail_surf = self.font_sm.render(detail, True, FP.BODY_TEXT)
                if detail_surf.get_width() > max_detail_w:
                    while len(detail) > 1 and self.font_sm.size(detail + '\u2026')[0] > max_detail_w:
                        detail = detail[:-1]
                    detail_surf = self.font_sm.render(detail + '\u2026', True, FP.BODY_TEXT)
                self.screen.blit(detail_surf, (bx + 70, iy + 38))
                cy += row_h

        # ── Single ingredients ────────────────────────────────────────────
        if n_single:
            if n_compound:
                draw_divider(self.screen, bx + 10, cy + 4, bw - 20)
                cy += 8
                self.screen.blit(
                    self.font_sm.render("SINGLE INGREDIENTS  (number keys)", True, FP.BODY_TEXT),
                    (bx + 18, cy)
                )
                cy += single_header_h
            for i, item in enumerate(self.cook_menu_items[:9]):
                iy = cy
                # FANTASY: Alternating midnight row colors
                pygame.draw.rect(
                    self.screen,
                    FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                    (bx + 10, iy, bw - 20, row_h - 4), border_radius=6
                )
                self.screen.blit(
                    self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT),
                    (bx + 18, iy + 10)
                )
                self.screen.blit(
                    self.font_md.render(self._display_name(item), True, FP.BODY_TEXT),
                    (bx + 70, iy + 10)
                )
                best = item.recipes.get('5', item.recipes.get('3', {}))
                # Show compound recipes this ingredient is used in
                used_in = get_recipes_for_ingredient(item.id)
                used_str = ''
                if used_in:
                    names = [r['name'] for r in used_in[:2]]
                    used_str = '  \u2756 ' + ', '.join(names)
                    if len(used_in) > 2:
                        used_str += f' +{len(used_in)-2}'
                detail = f"best solo: {best.get('name', '?')}{used_str}"
                detail_surf = self.font_sm.render(detail, True, FP.FADED_TEXT)
                if detail_surf.get_width() > max_detail_w:
                    while len(detail) > 1 and self.font_sm.size(detail + '\u2026')[0] > max_detail_w:
                        detail = detail[:-1]
                    detail_surf = self.font_sm.render(detail + '\u2026', True, FP.FADED_TEXT)
                self.screen.blit(detail_surf, (bx + 70, iy + 38))
                cy += row_h

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint_parts = []
        if n_compound:
            hint_parts.append("A-F: compound recipe")
        if n_single:
            hint_parts.append("1-9: single ingredient")
        hint_parts.append("ESC: cancel")
        hint = self.font_sm.render("  |  ".join(hint_parts), True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Confirm exit overlay
    # ------------------------------------------------------------------

    def _draw_drop_menu(self):
        draw_overlay(self.screen, 160)
        bw = min(600, GAME_W - 40)
        items = self.drop_menu_items
        row_h = 22
        bh = min(GAME_H - 80, 80 + len(items) * row_h + 50)
        bx = (GAME_W - bw) // 2
        by = (GAME_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        title_surf = self.font_lg.render("DROP ITEM", True, FP.GOLD_BRIGHT)
        self.screen.blit(title_surf, (bx + (bw - title_surf.get_width()) // 2, by + 12))
        sub_surf = self.font_sm.render("Select item to drop at your feet", True, FP.FADED_TEXT)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 36))
        letters = 'abcdefghijklmnopqrstuvwxyz'
        y_off = by + 60
        for i, item in enumerate(items[:26]):
            letter = letters[i]
            if isinstance(item, self._GoldDropEntry):
                dname = f"Gold  ({getattr(self, 'player_gold', 0)} coins)"
                col   = FP.GOLD_BRIGHT
            else:
                dname = self._display_name(item)
                col   = FP.PARCHMENT_LIGHT
            line   = f"  {letter})  {dname}"
            surf   = self.font_md.render(line, True, col)
            self.screen.blit(surf, (bx + 16, y_off + i * row_h))
        esc_surf = self.font_sm.render("ESC to cancel", True, FP.FADED_TEXT)
        self.screen.blit(esc_surf, (bx + (bw - esc_surf.get_width()) // 2, by + bh - 24))

    def _draw_eat_menu(self):
        # FANTASY: Grimoire-themed eat menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.eat_menu_items) * 66 + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with success (green) border for nourishment
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.SUCCESS_TEXT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EAT FOOD",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        self.screen.blit(
            self.font_sm.render(
                f"SP: {sp}/{self.player.max_sp}",
                True, sp_color
            ),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        for i, item in enumerate(self.eat_menu_items):
            iy = by + 82 + i * 66
            # FANTASY: Alternating midnight row colors
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT),
                (bx + 18, iy + 14)
            )
            self.screen.blit(
                self.font_md.render(self._display_name(item), True, FP.BODY_TEXT),
                (bx + 70, iy + 14)
            )
            if isinstance(item, Food):
                parts = [f"+{item.sp_restore} SP"]
                if item.hp_restore:
                    parts.append(f"+{item.hp_restore} HP")
                if item.bonus_type != 'none' and item.bonus_amount:
                    if item.bonus_type == 'stat':
                        parts.append(f"{item.bonus_stat}+{item.bonus_amount}")
                    elif item.bonus_type == 'random_stat':
                        parts.append(f"rand stat+{item.bonus_amount}")
                    elif item.bonus_type == 'combat_stat':
                        parts.append(f"STR/CON+{item.bonus_amount}")
                detail_text = "  ".join(parts)
            else:
                best_q = max(item.recipes.keys(), key=int)
                best_sp = item.recipes[best_q].get('sp', 0)
                raw_sp = item.recipes.get('1', item.recipes.get('0', {})).get('sp', 5)
                detail_text = f"raw: {raw_sp} SP  |  cooked: up to {best_sp} SP"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    def _draw_quaff_menu(self):
        draw_overlay(self.screen, 160)
        items = self.quaff_menu_items
        bw = min(760, GAME_W - 40)
        bh = min(90 + len(items) * 66 + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=(100, 160, 255))
        draw_header_bar(self.screen, (bx, by, bw, 44), text="QUAFF POTION",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)
        warning = self.font_sm.render(
            "Unknown potions may harm — identify first with  I",
            True, (200, 150, 80)
        )
        self.screen.blit(warning, (bx + (bw - warning.get_width()) // 2, by + 50))
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)
        max_detail_w = bw - 90
        for i, item in enumerate(items[:9]):
            iy = by + 82 + i * 66
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            # Colour swatch matching potion colour
            pygame.draw.rect(self.screen, tuple(item.color),
                             (bx + 18, iy + 18, 24, 24), border_radius=4)
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT),
                (bx + 50, iy + 14)
            )
            self.screen.blit(
                self.font_md.render(self._display_name(item), True, FP.BODY_TEXT),
                (bx + 100, iy + 14)
            )
            # Detail line
            known = item.identified or item.id in self.player.known_item_ids
            if known:
                eff = item.effect.replace('_', ' ')
                dur = f"  ({item.duration} turns)" if item.duration else ""
                is_good = item.effect in self._BENEFICIAL_EFFECTS
                detail_text = f"{'✦' if is_good else '✖'} {eff}{dur}"
                detail_col = FP.SUCCESS_TEXT if is_good else FP.DANGER_TEXT
            else:
                detail_text = "effect unknown — identify to reveal"
                detail_col = FP.FADED_TEXT
            detail_surf = self.font_sm.render(detail_text, True, detail_col)
            self.screen.blit(detail_surf, (bx + 100, iy + 40))
        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        self.screen.blit(
            self.font_sm.render("1-9: quaff  |  ESC: cancel", True, FP.HINT_TEXT),
            (bx + (bw - self.font_sm.size("1-9: quaff  |  ESC: cancel")[0]) // 2, hint_y)
        )

    def _draw_confirm_exit(self):
        draw_overlay(self.screen, 170)
        bw, bh = min(560, GAME_W - 40), 230
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 40),
                        text="SAVE YOUR PROGRESS?",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        sub = "Your run will be saved so you can resume it later."
        sub_surf = self.font_md.render(sub, True, FP.BODY_TEXT)
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

    # ------------------------------------------------------------------
    # Story popup  (narrative events: entrance, boss victories, endings)
    # ------------------------------------------------------------------

    # All narrative content indexed by key
    _STORY_CONTENT = {
        'dungeon_entrance': {
            'title': 'THE PHILOSOPHER\'S QUEST',
            'accent': (80, 120, 200),
            'lines': [
                "Your village of Aethon is dying.",
                "",
                "A magical plague — born of corruption and forgotten wisdom — has spread",
                "through every home, every hearth, every life you have ever known.",
                "Children grow pale. Elders speak in whispers of an ancient remedy.",
                "",
                "The Philosopher's Stone.",
                "",
                "Forged at the very bottom of the dungeon beneath the ancient ruins,",
                "it holds the wisdom needed to break the plague's hold forever.",
                "No one who has sought it has returned.",
                "",
                "But you are not no one.",
                "",
                "Descend. Claim the Stone. Return it to the light.",
                "The people who love you are counting on you.",
                "",
                "As you delve deeper, you may uncover lost codes — ancient secrets",
                "known only to those who venture far enough to find them.",
                "Present them to your father for rewards.",
            ],
            'code': None,
        },
        'boss_asterion': {
            'title': 'ASTERION THE MINOTAUR FALLS',
            'accent': (180, 50, 50),
            'lines': [
                "Asterion was born of Pasiphae and a divine white bull sent by Poseidon —",
                "a creature of two worlds, neither fully beast nor fully man.",
                "King Minos imprisoned him in the labyrinth built by Daedalus,",
                "where he was fed on tribute of youths until Theseus came.",
                "",
                "The hero navigated the maze with Ariadne's thread and slew the Minotaur",
                "not with overwhelming strength, but with preparation and cleverness.",
                "",
                "Today, that thread was your knowledge.",
                "The first guardian falls. The dungeon opens deeper.",
            ],
            'code': None,
        },
        'boss_medusa': {
            'title': 'MEDUSA THE GORGON FALLS',
            'accent': (50, 160, 80),
            'lines': [
                "Once a beautiful mortal priestess, Medusa was transformed by Athena's curse",
                "into a creature whose gaze turned living flesh to stone.",
                "Her hair became serpents. Her beauty became terror.",
                "",
                "Perseus slew her by meeting her eyes only in a mirrored shield —",
                "trusting reflection over direct sight, wisdom over recklessness.",
                "From her blood sprang Pegasus and Chrysaor.",
                "",
                "Her gaze is stilled. The passage deepens.",
            ],
            'code': None,
        },
        'boss_fafnir': {
            'title': 'FAFNIR THE DRAGON FALLS',
            'accent': (200, 100, 30),
            'lines': [
                "Fafnir was not always a dragon.",
                "He was a dwarf — son of the sorcerer Hreidmar — who murdered his own father",
                "for cursed Andvari's gold, then transformed over years into a great serpent,",
                "hoarding his stolen wealth in the Gnita Heath.",
                "",
                "The hero Sigurd slew him not by charging, but by patience:",
                "hiding in a pit along Fafnir's path, striking from below as the dragon passed.",
                "Cunning over power. Patience over courage alone.",
                "",
                "His fire is extinguished. The way below grows darker still.",
            ],
            'code': None,
        },
        'boss_fenrir': {
            'title': 'FENRIR THE WOLF FALLS',
            'accent': (80, 140, 200),
            'lines': [
                "Fenrir is the monstrous wolf of Norse prophecy — son of Loki,",
                "so terrible that the gods themselves feared to approach him.",
                "They bound him with Gleipnir, a magical ribbon forged from impossible things:",
                "a cat's footstep, a mountain's roots, a woman's beard, a bear's sinew,",
                "a fish's breath, and a bird's spittle.",
                "",
                "At Ragnarök, he was prophesied to swallow Odin himself.",
                "",
                "That prophecy is broken. You have done what even the Allfather could not.",
                "The deepest chamber lies ahead.",
            ],
            'code': None,
        },
        'boss_abaddon': {
            'title': 'ABADDON THE DESTROYER FALLS',
            'accent': (130, 60, 200),
            'lines': [
                "Abaddon is named in Revelation as the angel of the bottomless pit —",
                "the Destroyer, king of the locust army that rises at the fifth trumpet.",
                "His name means 'destruction' in Hebrew. He is ruin given form.",
                "",
                "That you have defeated him is more than a feat of arms.",
                "It is a statement about the nature of wisdom itself:",
                "that knowledge, courage, and preparation can overcome even destruction.",
                "",
                "The Philosopher's Stone lies before you.",
                "Take it. The village is waiting.",
            ],
            'code': None,
        },
        'exit_with_stone': {
            'title': 'THE QUEST IS COMPLETE',
            'accent': (220, 180, 40),
            'lines': [
                "You have done what many believed impossible.",
                "",
                "You descended into the darkness, faced and defeated five legendary adversaries,",
                "claimed the Philosopher's Stone, and returned to the light.",
                "",
                "Your village of Aethon will be saved.",
                "The plague will lift. The children will recover.",
                "The elders will weep with relief.",
                "The people who counted on you — who believed in you —",
                "will see the sun rise again because of what you did today.",
                "",
                "You are a Philosopher in the truest sense:",
                "one who loves wisdom enough to seek it at the cost of everything,",
                "and wise enough to bring it home.",
                "",
                "Well done.",
            ],
            'code': 'QUEST-COMPLETE',
        },
        'exit_without_stone': {
            'title': 'THE DESERTER',
            'accent': (100, 100, 100),
            'lines': [
                "You ran.",
                "",
                "Not from monsters. Not from darkness. Not even from death.",
                "You ran from the people who needed you most.",
                "",
                "From the children who grow weaker with each passing day.",
                "From the elders who pressed your hands and told you they believed in you.",
                "From the village that gave everything it had left to send you here.",
                "",
                "The Philosopher's Stone remains at the bottom of the dungeon.",
                "Unreached. Unclaimed. Its wisdom wasted on the dark.",
                "",
                "The village of Aethon will not see another spring.",
                "",
                "You were not overcome by the dungeon.",
                "You overcame yourself — and chose retreat.",
            ],
            'code': None,
        },
    }

    # Map monster kind → story key (only for bosses)
    _BOSS_STORY_KEYS = {
        'asterion_minotaur': 'boss_asterion',
        'medusa_gorgon':     'boss_medusa',
        'fafnir_dragon':     'boss_fafnir',
        'fenrir_wolf':       'boss_fenrir',
        'abaddon_destroyer': 'boss_abaddon',
    }

    def _show_story_popup(self, key: str, next_state: str = STATE_PLAYER):
        """Queue a narrative popup. Game pauses until the player dismisses it."""
        data = self._STORY_CONTENT.get(key)
        if data is None:
            return
        self.popup_data       = data
        self.popup_next_state = next_state
        self.state            = STATE_STORY_POPUP

    def _draw_story_popup(self):
        """Render the current narrative popup over the game world."""
        if not self.popup_data:
            return
        d = self.popup_data

        # ── Background ────────────────────────────────────────────────
        draw_overlay(self.screen, 200, (8, 6, 2))

        accent = d['accent']
        raw_lines = d['lines']
        code   = d.get('code')

        bw      = min(820, GAME_W - 60)
        row     = 22
        pad_x   = 36   # horizontal padding inside box
        max_txt = bw - pad_x * 2

        # Pre-wrap every line so we know the true rendered line count
        wrapped_lines = []  # list of (rendered_text, is_blank, is_quoted)
        for line in raw_lines:
            if line == '':
                wrapped_lines.append(('', True, False))
            else:
                quoted = line.startswith('"')
                for wl in self._wrap_text(line, self.font_md, max_txt):
                    wrapped_lines.append((wl, False, quoted))

        # ── Box sizing (based on real wrapped line count) ─────────────
        bh = 80 + len(wrapped_lines) * row + (row * 3 if code else 0) + 64
        bh = min(bh, GAME_H + MSG_H - 40)
        bx = (GAME_W - bw) // 2
        by = max(16, (GAME_H + MSG_H - bh) // 2)

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=accent)

        # ── Accent bar under title ─────────────────────────────────────
        accent_surf = pygame.Surface((bw - 8, 2), pygame.SRCALPHA)
        accent_surf.fill((*accent, 80))
        self.screen.blit(accent_surf, (bx + 4, by + 52))

        # ── Title ─────────────────────────────────────────────────────
        title_surf = self.font_lg.render(d['title'], True, accent)
        tx = bx + (bw - title_surf.get_width()) // 2
        self.screen.blit(title_surf, (tx, by + 14))

        # ── Body text ─────────────────────────────────────────────────
        y = by + 64
        for text, is_blank, is_quoted in wrapped_lines:
            if is_blank:
                y += row // 2
                continue
            col = (200, 195, 160) if is_quoted else FP.PARCHMENT_LIGHT
            surf = self.font_md.render(text, True, col)
            self.screen.blit(surf, (bx + pad_x, y))
            y += row

        # ── Code block ────────────────────────────────────────────────
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

        # ── Prompt ────────────────────────────────────────────────────
        prompt = self.font_sm.render("— Press any key to continue —", True, FP.HINT_TEXT)
        px_ = bx + (bw - prompt.get_width()) // 2
        self.screen.blit(prompt, (px_, by + bh - 26))

    # ------------------------------------------------------------------
    # Victory screen
    # ------------------------------------------------------------------

    def _draw_victory_screen(self):
        # FANTASY: Illuminated manuscript victory screen
        draw_overlay(self.screen, 210, (12, 10, 0))
        score = self._calc_score()
        grade, grade_col = self._get_grade(score)
        cx    = GAME_W // 2
        cy    = WINDOW_H // 2

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
            (f"Turns Survived",        f"{self.turn_count:,}",                FP.BODY_TEXT),
            (f"Deepest Level",         f"{self.level_mgr.max_level_reached}",  FP.BODY_TEXT),
            (f"Monsters Slain",        f"{self.level_mgr.monsters_killed:,}",  FP.BODY_TEXT),
            (f"Gold Collected",        f"{self.player_gold:,}",               FP.GOLD_PALE),
            (f"Questions Answered",    f"{total_q:,}",                         FP.BODY_TEXT),
            (f"Correct  /  Wrong",     f"{self.correct_answers} / {self.wrong_answers}   ({acc_pct}%)",
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
        breakdown = (f"({self.turn_count}×10)  +  ({self.level_mgr.max_level_reached}×1000)  +"
                     f"  ({self.level_mgr.monsters_killed}×100)  +  50 000 stone bonus")
        b_surf = self.font_sm.render(breakdown, True, FP.FADED_TEXT)
        self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, row_y + 14))

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
        hs_title = self.font_sm.render("— HIGH SCORES —", True, FP.GOLD)
        self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, hs_y))
        hs_y += 20
        for i, e in enumerate(top):
            marker = "►" if e['score'] == score else " "
            hs_line = (f"{marker}{i+1}. {e.get('name','?'):<10}  {e['score']:>8,}  "
                       f"{e.get('grade','?'):>2}  L{e.get('level',0)}")
            col = FP.GOLD_BRIGHT if e['score'] == score else FP.FADED_TEXT
            hs_s = self.font_sm.render(hs_line, True, col)
            self.screen.blit(hs_s, (cx - hs_s.get_width() // 2, hs_y))
            hs_y += 18

        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, hs_y + 6))

    # ------------------------------------------------------------------
    # Death / defeat screen
    # ------------------------------------------------------------------

    def _draw_death_screen(self):
        # FANTASY: Dark blood-red death screen with animated runes
        draw_overlay(self.screen, 180, (50, 0, 0))
        score = self._calc_score()
        cx    = GAME_W // 2
        cy    = WINDOW_H // 2

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
        hs_title = self.font_sm.render("— HIGH SCORES —", True, FP.BURGUNDY_MID)
        self.screen.blit(hs_title, (cx - hs_title.get_width() // 2, hs_y))
        hs_y += 20
        for i, e in enumerate(top):
            marker = "►" if e['score'] == score else " "
            hs_line = (f"{marker}{i+1}. {e.get('name','?'):<10}  {e['score']:>8,}  "
                       f"{e.get('grade','?'):>2}  L{e.get('level',0)}")
            col = FP.GOLD_PALE if e['score'] == score else FP.FADED_TEXT
            hs_s = self.font_sm.render(hs_line, True, col)
            self.screen.blit(hs_s, (cx - hs_s.get_width() // 2, hs_y))
            hs_y += 18

        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, hs_y + 6))

    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------

    def _help_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_SLASH, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # Examine corpse  (via I identify menu → philosophy quiz → lore)
    # ------------------------------------------------------------------

    def _examine_corpse_direct(self, corpse):
        """Called when player selects a corpse from the identify menu."""
        if corpse.lore_identified:
            self._lore_subject = corpse
            self.state = STATE_LORE
            return
        self.quiz_title = f"EXAMINING {corpse.monster_name.upper()} CORPSE  —  PHILOSOPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                corpse.lore_identified = True
                self.player.lore_known_monster_ids.add(corpse.monster_id)
                # Propagate to all existing corpses of this type
                for obj in self.ground_items:
                    if getattr(obj, 'monster_id', None) == corpse.monster_id:
                        obj.lore_identified = True
                for obj in self.player.inventory:
                    if getattr(obj, 'monster_id', None) == corpse.monster_id:
                        obj.lore_identified = True
                self._lore_subject = corpse
                self.state = STATE_LORE
                self.add_message(
                    f"Your philosophical insight reveals the nature of the {corpse.monster_name}!", 'success'
                )
            else:
                self.add_message("You study the corpse but gain no insight.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='philosophy',
            tier=max(1, min(5, getattr(corpse, 'harvest_tier', 1) + 1)),
            callback=on_complete,
            threshold=2,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('philosophy'),
        )

    def _examine_corpse(self):
        px, py = self.player.x, self.player.y
        corpse = next(
            (i for i in self.ground_items if i.x == px and i.y == py
             and getattr(i, 'monster_id', None) is not None),
            None
        )
        if corpse is None:
            self.add_message("There is no corpse here to examine.", 'info')
            return
        # Auto-identify if this monster type has already been lore-studied
        if corpse.monster_id in getattr(self.player, 'lore_known_monster_ids', set()):
            corpse.lore_identified = True
        if corpse.lore_identified:
            self.state = STATE_LORE
            self._lore_subject = corpse
            return
        self.quiz_title = f"EXAMINING {corpse.monster_name.upper()} CORPSE  —  PHILOSOPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                corpse.lore_identified = True
                self.player.lore_known_monster_ids.add(corpse.monster_id)
                # Propagate to all existing corpses of this type
                for obj in self.ground_items:
                    if getattr(obj, 'monster_id', None) == corpse.monster_id:
                        obj.lore_identified = True
                for obj in self.player.inventory:
                    if getattr(obj, 'monster_id', None) == corpse.monster_id:
                        obj.lore_identified = True
                self._lore_subject = corpse
                self.state = STATE_LORE
                self.add_message(
                    f"Your philosophical insight reveals the nature of the {corpse.monster_name}!", 'success'
                )
            else:
                self.add_message("You study the corpse but gain no insight.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='philosophy',
            tier=max(1, min(5, getattr(corpse, 'harvest_tier', 1) + 1)),
            callback=on_complete,
            threshold=2,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('philosophy'),
        )

    def _lore_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
            self.state = STATE_PLAYER

    def _draw_lore_screen(self):
        subject = getattr(self, '_lore_subject', None)
        if not subject:
            return

        from items import Corpse, Weapon, Armor, Shield, Accessory, Wand, Scroll
        from items import Food, Ammo, Lockpick, Ingredient
        is_corpse = isinstance(subject, Corpse)

        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        bw, bh = min(1000, GAME_W - 40), min(640, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

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
            # ── CORPSE / BESTIARY ENTRY ──────────────────────────────────
            title = self.font_lg.render(
                f"{subject.monster_name.upper()} — BESTIARY", True, title_col
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
                line = f"  \u2022 {atk.get('name','?')}: {atk.get('damage','?')} ({atk.get('type','physical')})"
                eff = atk.get('effect')
                if eff:
                    line += f"  \u2192 {eff} {int(atk.get('effect_chance',0)*100)}%"
                stat_lines.append(line)

            # ── Ingredient & recipe hints ─────────────────────────────────
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
                        stat_lines.append("Used in recipes:")
                        for r in compound[:4]:
                            stat_lines.append(f"  \u2022 {r['name']}  ({', '.join(r.get('ingredients', []))})")
                        if len(compound) > 4:
                            stat_lines.append(f"  \u2026 and {len(compound)-4} more")
            else:
                stat_lines.append("Ingredient: none (not harvestable)")

            lore_text = subject.lore or "No lore recorded."

        else:
            # ── ITEM IDENTIFICATION ENTRY ────────────────────────────────
            item_class_label = subject.item_class.upper()
            title = self.font_lg.render(
                f"{subject.name.upper()} — {item_class_label}", True, title_col
            )
            self.screen.blit(title, (bx + (bw - title.get_width()) // 2, y))
            y += 40
            pygame.draw.line(self.screen, border_col, (bx+20, y), (bx+bw-20, y))
            y += 12

            stat_lines = []

            # Set membership banner
            if getattr(subject, 'set_id', ''):
                set_label = getattr(subject, 'set_name', subject.set_id)
                stat_lines.append(f"\u2605 Part of {set_label} \u2605")

            if isinstance(subject, Weapon):
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

            elif isinstance(subject, Armor):
                stat_lines.append(f"Slot: {subject.slot}  |  Material: {subject.material}  |  Tier: {subject.tier}")
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: +{subject.enchant_bonus}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")
                if subject.damage_resistances:
                    res_str = '  '.join(f"{k}: {int(v*100)}%" for k, v in subject.damage_resistances.items())
                    stat_lines.append(f"Resistances: {res_str}")
                if subject.can_be_cursed:
                    stat_lines.append("WARNING: This item can be cursed.")

            elif isinstance(subject, Shield):
                stat_lines.append(f"Material: {subject.material}  |  Tier: {subject.tier}")
                stat_lines.append(f"AC Bonus: -{subject.ac_bonus}  |  Enchant: +{subject.enchant_bonus}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")
                if subject.damage_resistances:
                    res_str = '  '.join(f"{k}: {int(v*100)}%" for k, v in subject.damage_resistances.items())
                    stat_lines.append(f"Resistances: {res_str}")

            elif isinstance(subject, Accessory):
                stat_lines.append(f"Slot: {subject.slot}")
                efx = subject.effects
                if efx:
                    eff_str = ', '.join(f"{k}={v}" for k, v in efx.items())
                    stat_lines.append(f"Effects: {eff_str}")
                stat_lines.append(f"Equip Threshold: {subject.equip_threshold} correct answers")

            elif isinstance(subject, Wand):
                stat_lines.append(f"Effect: {subject.effect}  |  Power: {subject.power}")
                stat_lines.append(f"Charges: {subject.charges}/{subject.max_charges}")
                stat_lines.append(f"Quiz Threshold: {subject.quiz_threshold} correct answers")

            elif isinstance(subject, Scroll):
                stat_lines.append(f"Effect: {subject.effect}  |  Power: {subject.power}")
                stat_lines.append(f"Quiz Threshold: {subject.quiz_threshold} correct answers")

            elif isinstance(subject, Food):
                stat_lines.append(f"SP Restored: {subject.sp_restore}  |  HP Restored: {subject.hp_restore}")
                if subject.bonus_type != 'none' and subject.bonus_amount:
                    stat_lines.append(f"Bonus: {subject.bonus_type} {subject.bonus_stat or subject.bonus_effect} +{subject.bonus_amount}")

            elif isinstance(subject, Ammo):
                stat_lines.append(f"Ammo Type: {subject.ammo_type}  |  Tier: {subject.tier}")
                stat_lines.append(f"Damage Bonus: +{subject.damage_bonus}  |  Count: {subject.count_min}-{subject.count_max}")

            lore_text = subject.lore or "No further records found."

        # Draw stat lines (reserve ~120px at bottom for lore section + footer)
        stat_bottom = by + bh - 120
        for idx, line in enumerate(stat_lines):
            if y + 22 > stat_bottom:
                remaining = len(stat_lines) - idx
                surf = self.font_sm.render(f"  … and {remaining} more", True, (120, 120, 120))
                self.screen.blit(surf, (bx + 20, y))
                y += 22
                break
            surf = self.font_sm.render(line, True, stat_col)
            self.screen.blit(surf, (bx + 20, y))
            y += 22

        y += 4
        pygame.draw.line(self.screen, inner_col, (bx+20, y), (bx+bw-20, y))
        y += 12

        # Lore section header
        lore_hdr = self.font_sm.render("— LORE —", True, border_col)
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

    class _GoldDropEntry:
        """Sentinel shown in the drop menu when player has gold to drop."""
        id = '_gold_drop'
        @property
        def name(self): return "Drop Gold"

    def _open_drop_menu(self):
        items = []
        if getattr(self, 'player_gold', 0) > 0:
            items.append(self._GoldDropEntry())
        items += self.player.inventory[:]
        if not items:
            self.add_message("You have nothing to drop.", 'info')
            return
        self.drop_menu_items = items
        self.state = STATE_DROP_MENU

    def _drop_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_a: 0,  pygame.K_b: 1,  pygame.K_c: 2,  pygame.K_d: 3,
            pygame.K_e: 4,  pygame.K_f: 5,  pygame.K_g: 6,  pygame.K_h: 7,
            pygame.K_i: 8,  pygame.K_j: 9,  pygame.K_k: 10, pygame.K_l: 11,
            pygame.K_m: 12, pygame.K_n: 13, pygame.K_o: 14, pygame.K_p: 15,
            pygame.K_q: 16, pygame.K_r: 17, pygame.K_s: 18, pygame.K_t: 19,
            pygame.K_u: 20, pygame.K_v: 21, pygame.K_w: 22, pygame.K_x: 23,
            pygame.K_y: 24, pygame.K_z: 25,
        }
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.drop_menu_items):
            return
        item = self.drop_menu_items[idx]
        if isinstance(item, self._GoldDropEntry):
            self.drop_gold_input = ''
            self.state = STATE_DROP_GOLD_INPUT
            return
        self.state = STATE_PLAYER
        self._do_drop_item(item)

    def _do_drop_item(self, item):
        if not self.player.remove_from_inventory(item):
            return
        item.x, item.y = self.player.x, self.player.y
        self.ground_items.append(item)
        self.add_message(f"You drop the {self._display_name(item)}.", 'info')

        # Check if Complete Tablet was dropped on the Abyssal Shimmer
        if item.id == 'complete_tablet_of_second_death':
            shimmer = next(
                (g for g in self.ground_items
                 if g.id == 'abyssal_shimmer' and g.x == item.x and g.y == item.y),
                None
            )
            if shimmer and not shimmer.activated:
                shimmer.activated = True
                self.add_message(
                    "The Shimmer writhes and twists with violent magical energy!", 'success'
                )
                self.add_message(
                    "The Complete Tablet resonates with the Abyssal Shimmer.", 'info'
                )

        self._advance_turn()

    def _drop_gold_input(self, key: int, unicode: str):
        """Handle keystrokes for the gold-amount prompt."""
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            amount = int(self.drop_gold_input) if self.drop_gold_input.isdigit() else 0
            amount = max(0, min(amount, getattr(self, 'player_gold', 0)))
            if amount > 0:
                from items import GoldPile
                pile = GoldPile(amount, self.player.x, self.player.y)
                self.player_gold -= amount
                self.ground_items.append(pile)
                self.add_message(f"You drop {amount} gold coins.", 'info')
                self._advance_turn()
            else:
                self.add_message("No gold dropped.", 'info')
            self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self.drop_gold_input = self.drop_gold_input[:-1]
            return
        if unicode.isdigit() and len(self.drop_gold_input) < 7:
            self.drop_gold_input += unicode

    def _draw_drop_gold_input(self):
        """Draw a numeric entry overlay to choose how much gold to drop."""
        draw_overlay(self.screen, 160)
        bw, bh = 400, 160
        bx = (GAME_W - bw) // 2
        by = (GAME_H - bh) // 2
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

    # ------------------------------------------------------------------

    def _item_is_known(self, item) -> bool:
        """Return True if the item type is known (identified instance OR recognised by type)."""
        if not hasattr(item, 'identified'):
            return True  # items without an identified flag are always known
        return item.identified or item.id in self.player.known_item_ids

    def _open_examine_menu(self):
        """Open a list of all identified items in player inventory (and equipment)."""
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_examine_used()
        from items import ARMOR_SLOTS
        items = []
        for item in self.player.inventory:
            if self._item_is_known(item):
                items.append(item)
        if self.player.weapon and self._item_is_known(self.player.weapon):
            if self.player.weapon not in items:
                items.append(self.player.weapon)
        if self.player.shield and self._item_is_known(self.player.shield):
            if self.player.shield not in items:
                items.append(self.player.shield)
        for slot_item in self.player.armor_slots:
            if slot_item and self._item_is_known(slot_item):
                if slot_item not in items:
                    items.append(slot_item)
        for acc in self.player.accessory_slots:
            if acc and self._item_is_known(acc):
                if acc not in items:
                    items.append(acc)

        if not items:
            self.add_message("You have no identified items to examine.", 'info')
            return
        self.examine_menu_items = items
        self.state = STATE_EXAMINE

    def _examine_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.examine_menu_items):
            return
        item = self.examine_menu_items[idx]
        # Show lore screen for the selected item
        self._lore_subject = item
        self.state = STATE_LORE

    def _get_item_stats_brief(self, item) -> str:
        """Return a brief one-line stats string for examine menu display."""
        from items import Weapon, Armor, Shield, Accessory, Wand, Scroll, Spellbook, Ammo, Food, Ingredient, Lockpick
        if isinstance(item, Weapon):
            dmg = item.base_damage if item.base_damage else (item.damage or '?')
            two_h = ' 2H' if getattr(item, 'two_handed', False) else ''
            return f"{item.weapon_class}{two_h}  {dmg} dmg  tier {item.tier}"
        elif isinstance(item, Armor):
            return f"{item.slot}  -{item.ac_bonus} AC  tier {item.tier}"
        elif isinstance(item, Shield):
            return f"shield  -{item.ac_bonus} AC  tier {item.tier}"
        elif isinstance(item, Accessory):
            fx = item.effects
            if 'status' in fx:
                return f"grants {fx['status']}"
            else:
                return f"{fx.get('stat','?')} +{fx.get('amount',0)}"
        elif isinstance(item, Wand):
            return f"effect: {item.effect}  charges: {item.charges}/{item.max_charges}"
        elif isinstance(item, Scroll):
            return f"effect: {item.effect}  tier {item.quiz_tier}"
        elif isinstance(item, Spellbook):
            return f"teaches: {item.spell_name}  {item.mp_cost} MP"
        elif isinstance(item, Food):
            return f"+{item.sp_restore} SP  +{item.hp_restore} HP"
        elif isinstance(item, Ingredient):
            best = item.recipes.get('5', item.recipes.get('3', {}))
            return f"ingredient — best: {best.get('name', '?')}"
        elif isinstance(item, Ammo):
            return f"{item.ammo_type}  x{item.count}"
        elif isinstance(item, Lockpick):
            return "lockpick"
        return item.item_class.replace('_', ' ').title()

    def _draw_examine_menu(self):
        draw_overlay(self.screen, 160)

        n_items = len(self.examine_menu_items)
        ROW_H = 64
        bw = min(820, GAME_W - 40)
        bh = min(96 + n_items * ROW_H + 70, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EXAMINE ITEM",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Select an identified item to view its full lore entry.",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        cy = by + 82
        for i, item in enumerate(self.examine_menu_items[:9]):
            iy = cy
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, ROW_H - 6), border_radius=6
            )
            dname = self._display_name(item)
            type_label = item.item_class.replace('_', ' ').title() if hasattr(item, 'item_class') else ''
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 10)
            )
            self.screen.blit(
                self.font_md.render(dname, True, FP.BODY_TEXT), (bx + 70, iy + 10)
            )
            if type_label:
                type_surf = self.font_sm.render(f"[{type_label}]", True, FP.GOLD_PALE)
                self.screen.blit(type_surf, (bx + 70, iy + 36))
                stats_x = bx + 70 + type_surf.get_width() + 12
            else:
                stats_x = bx + 70
            stats_text = self._get_item_stats_brief(item)
            stats_surf = self.font_sm.render(stats_text, True, FP.FADED_TEXT)
            if stats_surf.get_width() > max_detail_w - (stats_x - bx - 70):
                while len(stats_text) > 1 and self.font_sm.size(stats_text + '\u2026')[0] > max_detail_w:
                    stats_text = stats_text[:-1]
                stats_surf = self.font_sm.render(stats_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(stats_surf, (stats_x, iy + 36))
            cy += ROW_H

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "1-9: select  |  ESC: close", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Merchant shop  (t key)
    # ------------------------------------------------------------------

    def _open_shop(self):
        """Open the merchant shop if a MerchantNPC is adjacent."""
        from mystery_system import MerchantNPC
        px, py = self.player.x, self.player.y
        merchant = next(
            (gi for gi in self.ground_items
             if isinstance(gi, MerchantNPC)
             and abs(gi.x - px) <= 1 and abs(gi.y - py) <= 1
             and not gi.sold_out),
            None
        )
        if merchant is None:
            self.add_message("No merchant nearby.  (T opens shop when adjacent)", 'info')
            return
        self._shop_merchant = merchant
        self._shop_selection = 0
        self.state = STATE_SHOP

    def _shop_input(self, key: int):
        m = getattr(self, '_shop_merchant', None)
        if m is None or key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        stock = m.stock
        if not stock:
            self.add_message("The merchant has nothing left to sell.", 'info')
            self.state = STATE_PLAYER
            return
        sel = getattr(self, '_shop_selection', 0)
        if key == pygame.K_UP or key == pygame.K_k:
            self._shop_selection = (sel - 1) % len(stock)
        elif key == pygame.K_DOWN or key == pygame.K_j:
            self._shop_selection = (sel + 1) % len(stock)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            sel = self._shop_selection
            if sel < len(stock):
                item  = stock[sel]
                price = m.prices[sel]
                if self.player_gold < price:
                    self.add_message(f"You can't afford that ({price} gold needed).", 'warning')
                else:
                    self.player_gold -= price
                    self.player.add_to_inventory(item)
                    iname = getattr(item, 'name', 'item')
                    _snd.play('buy')
                    self.add_message(f"You buy {iname} for {price} gold.", 'success')
                    m.stock.pop(sel)
                    m.prices.pop(sel)
                    self._shop_selection = min(sel, len(m.stock) - 1)
                    if not m.stock:
                        m.sold_out = True
                        self.add_message("The merchant has sold everything.", 'info')
                        self.state = STATE_PLAYER

    def _draw_shop(self):
        """Draw the merchant shop overlay."""
        from fantasy_ui import draw_overlay, draw_filigree_bar, centered_text, FP
        m = getattr(self, '_shop_merchant', None)
        if m is None:
            return
        cx = GAME_W // 2
        cy = WINDOW_H // 2
        draw_overlay(self.screen, 200, (10, 8, 2))
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
            for i, (item, price) in enumerate(zip(stock, m.prices)):
                is_sel = (i == sel)
                iname  = getattr(item, 'name', '?')
                wt     = getattr(item, 'weight', 0)
                line   = f"  {iname}  (wt:{wt:.1f})   {price} gold"
                fg     = FP.PARCHMENT_LIGHT if is_sel else FP.BODY_TEXT
                bg_col = (60, 50, 20, 180) if is_sel else None
                if bg_col:
                    bg_r = pygame.Rect(cx - 260, row_y - 2, 520, row_h)
                    bg_surf = pygame.Surface((bg_r.w, bg_r.h), pygame.SRCALPHA)
                    bg_surf.fill(bg_col)
                    self.screen.blit(bg_surf, bg_r.topleft)
                prefix = "► " if is_sel else "  "
                line_s = self.font_md.render(prefix + line, True, fg)
                self.screen.blit(line_s, (cx - 260, row_y))
                row_y += row_h

        draw_filigree_bar(self.screen, cx - 280, row_y + 8, 560, FP.GOLD_DARK)
        hint = self.font_sm.render("↑↓ navigate   ENTER buy   ESC close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, row_y + 16))

    # ------------------------------------------------------------------
    # Encyclopedia  (b key)
    # ------------------------------------------------------------------

    def _open_encyclopedia(self):
        """Open the encyclopedia browser."""
        self.encyclopedia_category = ''
        self.encyclopedia_entries = []
        self.encyclopedia_selection = 0
        self._encyclopedia_entry = None
        self.state = STATE_ENCYCLOPEDIA

    def _encyclopedia_input(self, key: int):
        if self.encyclopedia_category == '':
            # Category selection screen
            cat_keys = {
                pygame.K_1: 'bestiary',
                pygame.K_2: 'weapon',
                pygame.K_3: 'armor',
                pygame.K_4: 'accessory',
                pygame.K_5: 'scroll',
                pygame.K_6: 'wand',
                pygame.K_7: 'spellbook',
            }
            if key == pygame.K_ESCAPE:
                self.state = STATE_PLAYER
                return
            cat = cat_keys.get(key)
            if cat:
                self.encyclopedia_category = cat
                self.encyclopedia_selection = 0
                self._encyclopedia_entry = None
                self._encyclopedia_load_entries(cat)
            return

        if self._encyclopedia_entry is not None:
            # Entry detail view — any key except arrows goes back to list
            if key == pygame.K_ESCAPE:
                self._encyclopedia_entry = None
            return

        # List view
        if key == pygame.K_ESCAPE:
            self.encyclopedia_category = ''
            self.encyclopedia_entries = []
            self.encyclopedia_selection = 0
            self._encyclopedia_entry = None
            return
        if key in (pygame.K_UP, pygame.K_k):
            self.encyclopedia_selection = max(0, self.encyclopedia_selection - 1)
            return
        if key in (pygame.K_DOWN, pygame.K_j):
            self.encyclopedia_selection = min(len(self.encyclopedia_entries) - 1,
                                              self.encyclopedia_selection + 1)
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if 0 <= self.encyclopedia_selection < len(self.encyclopedia_entries):
                self._encyclopedia_entry = self.encyclopedia_entries[self.encyclopedia_selection]
            return

    def _encyclopedia_load_entries(self, category: str):
        """Load known entries for the given category from JSON data files."""
        import json
        from paths import data_path
        base = data_path('data')

        known_ids = getattr(self.player, 'known_item_ids', set())
        known_monster_ids = getattr(self.player, 'known_monster_ids', set())

        if category == 'bestiary':
            path = os.path.join(base, 'monsters.json')
            try:
                with open(path, encoding='utf-8') as f:
                    all_defs = json.load(f)
            except Exception:
                self.encyclopedia_entries = []
                return
            # Include any monster from a corpse lore-identified + any explicitly known
            # Plus any whose kind appears in known_monster_ids
            known_kinds = set(known_monster_ids)
            # Also add monsters we've seen corpses for (lore_identified)
            for item in self.player.inventory:
                mid = getattr(item, 'monster_id', None) or getattr(item, 'kind', None)
                if mid and getattr(item, 'lore_identified', False):
                    known_kinds.add(mid)
            entries = []
            for k, v in all_defs.items():
                if k in known_kinds:
                    entries.append({'_id': k, **v})
            entries.sort(key=lambda e: e.get('name', e['_id']))
            self.encyclopedia_entries = entries
        else:
            path = os.path.join(base, 'items', f'{category}.json')
            try:
                with open(path, encoding='utf-8') as f:
                    all_items = json.load(f)
            except Exception:
                self.encyclopedia_entries = []
                return
            entries = []
            for entry in all_items:
                iid = entry.get('id', '')
                if iid in known_ids:
                    entries.append(entry)
            entries.sort(key=lambda e: e.get('name', e.get('id', '')))
            self.encyclopedia_entries = entries

    def _draw_encyclopedia(self):
        """Draw the encyclopedia overlay — category, list, or detail view."""
        draw_overlay(self.screen, 160)

        bw = min(900, GAME_W - 40)
        by_base = 60
        bx = (GAME_W - bw) // 2

        _CAT_LABELS = {
            '':          'Encyclopedia',
            'bestiary':  'Bestiary — Monsters',
            'weapon':    'Armory — Weapons',
            'armor':     'Armor & Shields',
            'accessory': 'Accessories',
            'scroll':    'Scrolls',
            'wand':      'Wands',
            'spellbook': 'Spellbooks',
        }

        if self.encyclopedia_category == '':
            # ── Category selection screen ─────────────────────────────────
            bh = min(460, WINDOW_H - 40)
            by = (WINDOW_H - bh) // 2
            draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
            draw_header_bar(self.screen, (bx, by, bw, 44),
                            text="ENCYCLOPEDIA",
                            font=self.font_md, text_color=FP.GOLD_BRIGHT)
            self.screen.blit(
                self.font_sm.render("Select a category to browse your discovered knowledge.",
                                    True, FP.BODY_TEXT),
                (bx + 20, by + 48)
            )
            draw_divider(self.screen, bx + 10, by + 72, bw - 20)

            cats = [
                ('1', 'Bestiary',        'Monsters you have encountered'),
                ('2', 'Armory',          'Weapons'),
                ('3', 'Armor',           'Armor & Shields'),
                ('4', 'Accessories',     'Rings and amulets'),
                ('5', 'Scrolls',         'Scrolls you have read'),
                ('6', 'Wands',           'Wands you have used'),
                ('7', 'Spellbooks',      'Spells you have learned'),
            ]
            cy = by + 88
            ROW_H = 46
            for key_lbl, cat_name, cat_desc in cats:
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID,
                                 (bx + 10, cy, bw - 20, ROW_H - 4), border_radius=6)
                self.screen.blit(
                    self.font_md.render(f"[{key_lbl}]", True, FP.GOLD_BRIGHT),
                    (bx + 20, cy + 8)
                )
                self.screen.blit(
                    self.font_md.render(cat_name, True, FP.BODY_TEXT),
                    (bx + 70, cy + 8)
                )
                self.screen.blit(
                    self.font_sm.render(cat_desc, True, FP.FADED_TEXT),
                    (bx + 300, cy + 12)
                )
                cy += ROW_H

            hint_y = by + bh - 34
            draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
            hint = self.font_sm.render("1-7: select category  |  ESC: close", True, FP.HINT_TEXT)
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))
            return

        header_label = _CAT_LABELS.get(self.encyclopedia_category, self.encyclopedia_category.title())

        if self._encyclopedia_entry is not None:
            # ── Entry detail view ─────────────────────────────────────────
            entry = self._encyclopedia_entry
            bh = min(560, WINDOW_H - 40)
            by = (WINDOW_H - bh) // 2
            draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
            draw_header_bar(self.screen, (bx, by, bw, 44),
                            text=f"ENCYCLOPEDIA — {header_label.upper()}",
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
                    line = f"  \u2022 {atk.get('name','?')}: {atk.get('damage','?')} ({atk.get('type','physical')})"
                    eff = atk.get('effect')
                    if eff:
                        line += f"  \u2192 {eff} {int(atk.get('effect_chance',0)*100)}%"
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
                surf = self.font_sm.render(line, True, stat_col)
                self.screen.blit(surf, (bx + 20, y))
                y += 22

            y += 6
            pygame.draw.line(self.screen, (40, 60, 120), (bx + 20, y), (bx + bw - 20, y))
            y += 12
            lore_hdr = self.font_sm.render("— LORE —", True, (80, 120, 200))
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

        # ── Entry list view ───────────────────────────────────────────────
        entries = self.encyclopedia_entries
        n = len(entries)
        ROW_H = 44
        visible_rows = min(n, 14)
        bh = min(96 + visible_rows * ROW_H + 70, WINDOW_H - 40)
        by = (WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44),
                        text=f"ENCYCLOPEDIA — {header_label.upper()}  ({n} known)",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)
        draw_divider(self.screen, bx + 10, by + 48, bw - 20)

        if n == 0:
            msg = self.font_md.render("Nothing discovered yet in this category.", True, FP.FADED_TEXT)
            self.screen.blit(msg, (bx + (bw - msg.get_width()) // 2, by + 80))
        else:
            # Scroll window around selection
            sel = self.encyclopedia_selection
            start = max(0, min(sel - visible_rows // 2, n - visible_rows))
            cy = by + 56
            for idx in range(start, min(start + visible_rows, n)):
                entry = entries[idx]
                iy = cy
                is_sel = (idx == sel)
                row_bg = (40, 30, 80) if is_sel else (FP.MIDNIGHT_MID if idx % 2 == 0 else FP.MIDNIGHT)
                pygame.draw.rect(self.screen, row_bg,
                                 (bx + 10, iy, bw - 20, ROW_H - 4), border_radius=5)
                if is_sel:
                    pygame.draw.rect(self.screen, FP.ARCANE_BRIGHT,
                                     (bx + 10, iy, bw - 20, ROW_H - 4), 1, border_radius=5)
                entry_name = entry.get('name', entry.get('_id', '?'))
                name_col = FP.GOLD_PALE if is_sel else FP.BODY_TEXT
                self.screen.blit(
                    self.font_md.render(self._fix_name_case(entry_name), True, name_col),
                    (bx + 20, iy + 8)
                )
                # Brief extra info on same row
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
                if brief:
                    self.screen.blit(
                        self.font_sm.render(brief, True, FP.FADED_TEXT),
                        (bx + bw - self.font_sm.size(brief)[0] - 20, iy + 12)
                    )
                cy += ROW_H

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "Up/Down: navigate  |  Enter: view details  |  ESC: categories", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    def _draw_hint_screen(self):
        """Display a Recall Lore result — parchment-style hint overlay."""
        from fantasy_ui import FP, get_font
        hint_text = getattr(self, '_lore_hint_text', None)
        chain     = getattr(self, '_lore_hint_chain', 0)
        if hint_text is None:
            self.state = STATE_PLAYER
            return

        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 760, 280
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

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
        stars = '\u2605' * chain + '\u2606' * (5 - chain)

        title_surf = font_title.render(f"RECALL LORE  —  {label}", True, (220, 180, 80))
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
            f"Next recall available in {cd} turns  \u2014  [ any key ] to close",
            True, (100, 85, 45)
        )
        self.screen.blit(cd_surf, (bx + (bw - cd_surf.get_width()) // 2, by + bh - 26))

    def _draw_help_screen(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        self.screen.blit(overlay, (0, 0))

        bw      = min(900, GAME_W - 40)
        line_h  = 26
        col_break = 13
        content_h = col_break * line_h   # taller of the two columns
        bh      = 66 + content_h + 24   # y-start of rows + rows + footer padding
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Grimoire-style command reference panel
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 48),
                        text="COMMAND REFERENCE",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)
        draw_divider(self.screen, bx + 20, by + 56, bw - 40)

        _COMMANDS = [
            # (key_label, description, color)
            # FANTASY: Section headers use GOLD_PALE; commands use BODY_TEXT; keys use GOLD_BRIGHT
            ("MOVEMENT", None, FP.GOLD_PALE),
            ("Arrows / hjkl",  "Move / attack",                                          FP.BODY_TEXT),
            ("ITEMS", None, FP.GOLD_PALE),
            ("G  or  ,",       "Pick up item",                                            FP.BODY_TEXT),
            ("E",              "Equip / Unequip",                                          FP.BODY_TEXT),
            ("I",              "Identify items",                                           FP.BODY_TEXT),
            ("R",              "Read scroll / spellbook",                                  FP.BODY_TEXT),
            ("M",              "Cast spell",                                               FP.BODY_TEXT),
            ("Z",              "Zap wand",                                                 FP.BODY_TEXT),
            ("U",              "Eat food",                                                 FP.BODY_TEXT),
            ("Q",              "Quaff potion",                                             FP.BODY_TEXT),
            ("C",              "Cook ingredient",                                          FP.BODY_TEXT),
            ("H",              "Harvest corpse",                                           FP.BODY_TEXT),
            ("COMBAT & EXPLORATION", None, FP.GOLD_PALE),
            ("F",              "Fire ranged weapon",                                       FP.BODY_TEXT),
            ("X",              "Examine identified item",                                  FP.BODY_TEXT),
            ("B",              "Encyclopedia",                                             FP.BODY_TEXT),
            ("A",              "Attack / bash container",                                  FP.BODY_TEXT),
            ("D",              "Drop item",                                                FP.BODY_TEXT),
            ("P",              "Pick lock",                                                FP.BODY_TEXT),
            (">  or  <",       "Use stairs",                                               FP.BODY_TEXT),
            ("KNOWLEDGE", None, FP.GOLD_PALE),
            ("\\",             "Pray at altar",                                            (200, 180, 255)),
            ("N",              "Recall Lore",                                              (120, 200, 240)),
            ("QUIZ ANSWERS", None, FP.GOLD_PALE),
            ("1  2  3  4",     "Answer questions during quiz",                            FP.GOLD_BRIGHT),
            ("SYSTEM", None, FP.GOLD_PALE),
            ("?",              "This help screen",                                         FP.BODY_TEXT),
            ("ESC",            "Cancel / close menu",                                      FP.BODY_TEXT),
        ]

        col_w   = (bw - 40) // 2
        left_x  = bx + 20
        right_x = bx + 20 + col_w
        y       = by + 66

        for idx, entry in enumerate(_COMMANDS):
            key_label, desc, color = entry
            cx_ = left_x if idx < col_break else right_x
            cy_ = y + (idx if idx < col_break else idx - col_break) * line_h

            if desc is None:
                # FANTASY: Section header in GOLD_PALE
                hdr = self.font_sm.render(f"── {key_label} ──", True, color)
                self.screen.blit(hdr, (cx_, cy_))
            else:
                # FANTASY: Key label in GOLD_BRIGHT, description in supplied color
                ksurf = self.font_sm.render(key_label, True, FP.GOLD_BRIGHT)
                # Truncate description if it would overflow the column
                desc_max_w = col_w - 170
                dsurf = self.font_sm.render(desc, True, color)
                if dsurf.get_width() > desc_max_w:
                    trunc = desc
                    while len(trunc) > 1 and self.font_sm.size(trunc + '\u2026')[0] > desc_max_w:
                        trunc = trunc[:-1]
                    dsurf = self.font_sm.render(trunc + '\u2026', True, color)
                self.screen.blit(ksurf, (cx_, cy_))
                self.screen.blit(dsurf, (cx_ + 160, cy_))

        # FANTASY: Footer hint in HINT_TEXT
        hint = self.font_sm.render("Press ESC or ? to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 32))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    from save_system import save_exists, load_game, save_game, delete_save

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    welcome = WelcomeScreen(screen)
    player_name, secret_build = welcome.run(clock)

    # If a save exists for this name, load it; otherwise start fresh
    state = load_game(player_name) if save_exists(player_name) else None
    if state:
        game = Game(screen,
                    player_name=state.get('player_name', player_name),
                    secret_build=state.get('secret_build'))
        game.load_state(state)
    else:
        game = Game(screen, player_name=player_name, secret_build=secret_build)

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        game.update(dt)
        game.render()

    # Save on clean exit if the game is still in progress and player chose to save
    if game.state not in (STATE_DEAD, STATE_VICTORY) and game._save_on_quit:
        save_game(game)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
