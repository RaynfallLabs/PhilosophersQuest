import math
import sys
import pygame

# FANTASY: High-fantasy medieval/arcane grimoire UI theme
from fantasy_ui import (FP, get_font, draw_panel, draw_dark_panel,
                         draw_header_bar, draw_divider, draw_shadow_text,
                         draw_glow_text, centered_text, draw_overlay,
                         draw_rune_circle, draw_filigree_bar, draw_candle_glow,
                         draw_choice_button, ITEM_COLOR, make_parchment)

from combat import player_attack
from container_system import attempt_lockpick, check_for_mimic
from dungeon import (generate_dungeon, spawn_monsters, spawn_items,
                     STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR)
from food_system import (harvest_corpse, cook_ingredient, eat_food, eat_raw,
                         get_available_compound_recipes, cook_compound_recipe,
                         get_recipes_for_ingredient)
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient, Artifact, Container, Lockpick, Accessory, Wand, Scroll, Ammo, Food
from level_manager import LevelManager
from player import Player
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
# Secret character builds (name → stat overrides)
# Each entry: dict with any of STR/CON/DEX/INT/WIS/PER as overrides.
# Populate with real builds later; leave empty for now.
# ------------------------------------------------------------------
SECRET_BUILDS: dict[str, dict] = {
    # e.g. "aristotle": {"WIS": 18, "INT": 16, "PER": 14},
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

    def run(self, clock: pygame.time.Clock) -> tuple[str | None, dict | None]:
        """Returns (None, None) if user chose 'Continue' (load save), else (name, build)."""
        from save_system import save_exists
        self._has_save = save_exists()

        while True:
            dt = clock.tick(60) / 1000.0
            self._anim_t  += dt
            self.cursor_timer += dt
            if self.cursor_timer >= 0.55:
                self.cursor_on = not self.cursor_on
                self.cursor_timer = 0.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self._has_save and event.unicode.lower() == 'c':
                        return None, None   # sentinel: load save
                    if event.key == pygame.K_RETURN and self.name_buf.strip():
                        name  = self.name_buf.strip()
                        build = SECRET_BUILDS.get(name.lower())
                        return name, build
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
        # FANTASY: Subtle footer hint
        has_save = getattr(self, '_has_save', False)
        if has_save:
            text = "[ C ] continue saved game     [ ENTER ] new game     [ ESC ] quit"
        else:
            text = "[ ENTER ] begin your quest     [ ESC ] quit"
        hint = self.font_tiny.render(text, True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.H - 28))
        if has_save:
            save_hint = self.font_sm.render("★  A saved journey awaits", True, FP.SUCCESS_TEXT)
            self.screen.blit(save_hint, (cx - save_hint.get_width() // 2, self.H - 52))


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
STATE_HELP           = 'help'
STATE_LORE           = 'lore'
STATE_PRAY           = 'pray'


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
        self.identify_menu_items: list   = []
        self.cook_menu_items: list       = []
        self.cook_compound_recipes: list = []   # available multi-ingredient recipes
        self.eat_menu_items: list        = []
        self.player_gold        = 0
        self.turn_count         = 0
        self.dungeon_level      = 1
        self.defeat_reason      = 'died'   # 'died' | 'starved' | 'fled'
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

        self._new_level(1)

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
        # Apply secret build stat overrides if any
        if self.secret_build:
            for stat, value in self.secret_build.items():
                if hasattr(self.player, stat):
                    setattr(self.player, stat, value)
            # Recompute derived stats after overrides
            self.player.max_hp = self.player.BASE_HP + self.player.CON
            self.player.hp     = self.player.max_hp
            self.player.max_sp = self.player.BASE_SP + self.player.CON
            self.player.sp     = self.player.max_sp
            self.player.max_mp = self.player.BASE_MP + self.player.INT
            self.player.mp     = self.player.max_mp
        self.player.x, self.player.y = dungeon.rooms[0].center
        self.renderer                = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
        self.renderer.set_dungeon(dungeon.width, dungeon.height, GAME_W, GAME_H)
        self._refresh_fov()

        # Give the player their Philosopher's Amulet (always starts identified)
        self._give_starting_amulet()

        greeting = f"Welcome, {self.player_name}!"
        if self.secret_build:
            greeting += "  (Secret build active!)"
        self.add_message(greeting, 'success')
        self.add_message("You carry the Philosopher's Amulet, a dagger, a lockpick, and a ration.", 'info')
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
        self.renderer.set_dungeon(dungeon.width, dungeon.height, GAME_W, GAME_H)

        # Grant HP on every level transition
        self.player.on_level_change()

        # Place player at the stairs they came through
        if enter_from_top:
            self.player.x, self.player.y = dungeon.rooms[0].center
            self.add_message(f"You descend to level {new_level}.", 'info')
        else:
            self.player.x, self.player.y = dungeon.rooms[-1].center
            self.add_message(f"You ascend to level {new_level}.", 'info')

        self._refresh_fov()

    def _give_starting_amulet(self):
        """Give the player their starting kit: amulet, dagger, lockpick, ration."""
        from items import load_items
        try:
            accessories = load_items('accessory')
            amulet = next((a for a in accessories if a.id == 'philosophers_amulet'), None)
            if amulet:
                amulet.identified = True
                self.player.inventory.append(amulet)
                self.player.known_item_ids.add('philosophers_amulet')
        except Exception:
            pass

        try:
            weapons = load_items('weapon')
            dagger = next((w for w in weapons if w.id == 'iron_dagger'), None)
            if dagger:
                self.player.inventory.append(dagger)
        except Exception:
            pass

        try:
            lockpicks = load_items('lockpick')
            lockpick = next((l for l in lockpicks if l.id == 'lockpick'), None)
            if lockpick:
                self.player.inventory.append(lockpick)
        except Exception:
            pass

        try:
            foods = load_items('food')
            ration = next((f for f in foods if f.id == 'bread_ration'), None)
            if ration:
                self.player.inventory.append(ration)
        except Exception:
            pass

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )

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
                              STATE_EAT_MENU, STATE_HELP, STATE_LORE):
                self.state = STATE_PLAYER
                return True
            if self.state in (STATE_DEAD, STATE_VICTORY):
                return False
            return False

        if self.state == STATE_PLAYER:
            # Stair keys checked by unicode to handle shift+. / shift+,
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
        elif self.state == STATE_IDENTIFY_MENU:
            self._identify_menu_input(key)
        elif self.state == STATE_COOK_MENU:
            self._cook_menu_input(key)
        elif self.state == STATE_EAT_MENU:
            self._eat_menu_input(key)
        elif self.state == STATE_HELP:
            self._help_input(key)
        elif self.state == STATE_LORE:
            self._lore_input(key)
        elif self.state == STATE_CONFIRM_EXIT:
            self._confirm_exit_input(key)

        return True

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
    }

    def _player_input(self, key: int):
        import random as _rng

        if key in (pygame.K_g, pygame.K_COMMA):
            self._pickup()
            return
        if key == pygame.K_e:
            self._open_equip_menu()
            return
        if key == pygame.K_r:
            self._open_accessory_menu()
            return
        if key == pygame.K_u:
            self._open_wand_menu()
            return
        if key == pygame.K_s:
            self._open_scroll_menu()
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
        if key == pygame.K_z:
            self._open_eat_menu()
            return
        if key == pygame.K_SLASH or key == pygame.K_QUESTION:
            self.state = STATE_HELP
            return
        if key == pygame.K_x:
            self._examine_corpse()
            return

        if key not in self._MOVE_KEYS:
            return

        self._do_move(*self._MOVE_KEYS[key])

    def _do_move(self, dx: int, dy: int):
        """Attempt a player move/action in direction (dx, dy)."""
        if self.state != STATE_PLAYER:
            return

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
            dx, dy = _rng.choice(
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
            self._refresh_fov()
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

    @staticmethod
    def _display_name(item) -> str:
        """Return the name to show for an item — unidentified name if not yet identified."""
        if not getattr(item, 'identified', True):
            return getattr(item, 'unidentified_name', item.name)
        return item.name

    def _notify_ground(self, x: int, y: int):
        """Print messages about items and notable features at (x, y)."""
        here = [item for item in self.ground_items if item.x == x and item.y == y]
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
            self._change_level(self.dungeon_level - 1, enter_from_top=False)

    def _confirm_exit_input(self, key: int):
        if key in (pygame.K_y, pygame.K_RETURN):
            self._do_exit()
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _do_exit(self):
        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )
        if has_stone:
            self._on_game_over()
            self.state = STATE_VICTORY
        else:
            self.defeat_reason = 'fled'
            self._on_game_over()
            self.state = STATE_DEAD

    def _on_game_over(self):
        """Delete save file on any game-ending event (permadeath)."""
        from save_system import delete_save
        delete_save()

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _calc_score(self) -> int:
        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )
        return (
            self.turn_count * 10
            + self.level_mgr.max_level_reached * 1000
            + self.level_mgr.monsters_killed * 100
            + (50000 if has_stone else 0)
        )

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------

    def _advance_turn(self):
        self.turn_count += 1

        # Decrement prayer cooldown
        if self.player.prayer_cooldown > 0:
            self.player.prayer_cooldown -= 1

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
        # Clairvoyant: reveal tiles within 10-tile radius each turn
        if self.player.has_effect('clairvoyant'):
            px, py = self.player.x, self.player.y
            for cy in range(max(0, py - 10), min(self.dungeon.height, py + 11)):
                for cx in range(max(0, px - 10), min(self.dungeon.width, px + 11)):
                    if abs(cx - px) + abs(cy - py) <= 10:
                        self.dungeon.explored.add((cx, cy))

        self._do_monster_turns()

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
    # Pickup
    # ------------------------------------------------------------------

    def _pickup(self):
        px, py = self.player.x, self.player.y
        item = next((i for i in self.ground_items if i.x == px and i.y == py), None)
        if item is None:
            self.add_message("There is nothing here to pick up.", 'info')
            return
        if self.player.add_to_inventory(item):
            self.ground_items.remove(item)
            if isinstance(item, Ammo):
                self.add_message(f"You pick up {item.count} {item.name}s.", 'loot')
            else:
                self.add_message(f"You pick up the {item.name}.", 'loot')
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

        if not any(isinstance(i, Lockpick) for i in self.player.inventory):
            self.add_message("You need a lockpick to attempt this.", 'warning')
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
                # Gold reported via message (no currency item needed)

            self._advance_turn()

        attempt_lockpick(
            self.player, container,
            self.quiz_engine, self.dungeon, self.monsters,
            on_complete
        )

    def _attack_container(self):
        """Press 'a' to probe an adjacent container for mimics."""
        container = self._find_adjacent_container()
        if container is None:
            self.add_message("There is no container to attack nearby.", 'info')
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
            if ingredient is not None:
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
            self._advance_turn()

        cook_ingredient(self.player, ingredient, self.quiz_engine, on_complete)

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
        """Collect Food items and Ingredients for eating/raw-eating."""
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
        else:
            messages = eat_raw(self.player, item)
        mtype = 'success' if self.player.sp > 0 else 'warning'
        for msg in messages:
            self.add_message(msg, mtype)
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
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='theology',
            tier=1,
            callback=on_complete,
            max_chain=8,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
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
    # Equip menu
    # ------------------------------------------------------------------

    def _open_equip_menu(self):
        from items import ARMOR_SLOTS
        self.equip_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Weapon, Armor, Shield))
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
            self.player._apply_equip(item)
            self.player.remove_from_inventory(item)
            suffix = " (two-handed)" if getattr(item, 'two_handed', False) else ""
            self.add_message(f"You equip the {item.name}{suffix}.", 'success')
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
        self.player.inventory.append(item)
        self.add_message(f"You remove the {self._display_name(item)}.", 'info')
        self._advance_turn()

    def _start_armor_quiz(self, item):
        """Launch geography threshold quiz to equip armor or shield."""
        item_name = item.name
        cursed_tag = " (cursed)" if getattr(item, 'cursed', False) else ""
        self.quiz_title = f"EQUIPPING {item_name.upper()}  —  GEOGRAPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                self.player._apply_equip(item)
                self.player.remove_from_inventory(item)
                ac = self.player.get_ac()
                msg = f"You equip the {item_name}{cursed_tag}. AC is now {ac}."
                if getattr(item, 'cursed', False):
                    msg += " It feels wrong..."
                self.add_message(msg, 'success')
            else:
                self.add_message(
                    f"You struggle with the {item_name} and give up.", 'warning'
                )
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='geography',
            tier=getattr(item, 'quiz_tier', 1),
            callback=on_complete,
            threshold=item.equip_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
        )

    # ------------------------------------------------------------------
    # Accessory menu  (r key — history quiz)
    # ------------------------------------------------------------------

    def _open_accessory_menu(self):
        self.accessory_menu_items = [
            i for i in self.player.inventory if isinstance(i, Accessory)
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
                        f"You slip on the {item.name}. You feel {fx['status']}!", 'success'
                    )
                else:
                    stat = fx.get('stat', '')
                    amt  = fx.get('amount', 0)
                    self.add_message(
                        f"You slip on the {item.name}. {stat} +{amt}!", 'success'
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
        if wand.charges <= 0:
            self.add_message("The wand is empty — it crumbles to dust.", 'warning')
            self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  —  SCIENCE"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            wand.identified = True
            self.player.known_item_ids.add(wand.id)

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
            mp = os.path.join(os.path.dirname('src/'), 'data', 'monsters.json')
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
                mp = os.path.join(os.path.dirname('src/'), 'data', 'monsters.json')
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
                self.dungeon.revealed.add((item.x, item.y))
            self.add_message("A golden shimmer reveals hidden treasures!", 'success')

        elif effect == 'clairvoyance':
            for y in range(len(self.dungeon.tiles)):
                for x in range(len(self.dungeon.tiles[y])):
                    self.dungeon.revealed.add((x, y))
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
        from items import Corpse
        self.ground_items.append(
            Corpse(
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
        )

    def _drop_treasure(self, monster):
        """Drop gold and possibly an item when a monster dies."""
        import random as _rng
        treasure = getattr(monster, 'treasure', {})
        gold_range = treasure.get('gold', [0, 0])
        gold = _rng.randint(int(gold_range[0]), max(int(gold_range[0]), int(gold_range[1])))
        if gold > 0:
            self.add_message(f"The {monster.name} drops {gold} gold coins.", 'loot')
            # Gold is tracked as a player resource (add to a gold counter)
            if not hasattr(self, 'player_gold'):
                self.player_gold = 0
            self.player_gold += gold
        item_chance = treasure.get('item_chance', 0.0)
        if _rng.random() < item_chance:
            item_tier = int(treasure.get('item_tier', 1))
            self._spawn_treasure_item(monster.x, monster.y, item_tier)

        # Boss reward scroll
        boss_scroll_id = treasure.get('boss_scroll_id')
        if boss_scroll_id:
            self._spawn_boss_scroll(monster.x, monster.y, boss_scroll_id)

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
            self.add_message(f"It drops {chosen.name}!", 'loot')

    # ------------------------------------------------------------------
    # Scroll menu  (s key — grammar quiz)
    # ------------------------------------------------------------------

    def _open_scroll_menu(self):
        self.scroll_menu_items = [
            i for i in self.player.inventory if isinstance(i, Scroll)
        ]
        if not self.scroll_menu_items:
            self.add_message("You have no scrolls to read.", 'info')
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
        self._read_scroll(self.scroll_menu_items[idx])

    def _read_scroll(self, scroll: 'Scroll'):
        display = self._display_name(scroll)
        self.quiz_title = f"READING {display.upper()}  —  GRAMMAR"
        self.state = STATE_QUIZ

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

            self.add_message(f"You read the {scroll.name}!", 'success')
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
            if removed:
                self.add_message(
                    f"A cleansing light removes: {', '.join(removed)}.", 'success'
                )
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
        self.identify_menu_items = [
            i for i in self.player.inventory
            if hasattr(i, 'identified') and not i.identified
               and i.id not in self.player.known_item_ids
        ]
        if not self.identify_menu_items:
            self.add_message("All your items are already identified.", 'info')
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
        self._identify_item(self.identify_menu_items[idx])

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

    def _display_name(self, item) -> str:
        """Return the name to show for an item.

        Type known  (item.id in known_item_ids OR item.identified) → item.name
        Type unknown                                                → item.unidentified_name
        Modifier info (+N, {C}) is NEVER shown here — only the sidebar
        shows modifiers, and only when item.identified (instance examined).
        """
        if not hasattr(item, 'identified'):
            return item.name
        if item.identified or item.id in self.player.known_item_ids:
            return item.name
        return getattr(item, 'unidentified_name', item.name)

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

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False):
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
                    self.ground_items.append(
                        Corpse(
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
                    )
            self._advance_turn()

        player_attack(self.player, monster, self.quiz_engine, on_complete, ammo=ammo_item)

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def _start_combat(self, monster):
        self.state = STATE_QUIZ
        self.combat_target = monster
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  —  MATH CHAIN"

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
                    apply_knockback(self.player, monster, self.dungeon)
                    msg += f" The {monster.name} is knocked back!"
                self.add_message(msg, 'success')
                if killed:
                    self.level_mgr.monsters_killed += 1
                    self.add_message(f"The {monster.name} is slain!", 'success')
                    self._drop_treasure(monster)
                    self.ground_items.append(
                        Corpse(
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
        for m in self.monsters:
            if not m.alive:
                continue
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters)
            if did_attack:
                dmg, msg = m.attack(self.player)
                self.add_message(msg, 'danger')
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
        self.renderer.draw_player(self.player, cam_x, cam_y)
        self.screen.set_clip(None)

        self.msg_log.draw(self.screen, 0, GAME_H, GAME_W, MSG_H)
        self.sidebar.draw(self.player, self.dungeon_level, self.turn_count)

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
        elif self.state == STATE_IDENTIFY_MENU:
            self._draw_identify_menu()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
        elif self.state == STATE_EAT_MENU:
            self._draw_eat_menu()
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

        # Timer seconds label — always shows live remaining time
        secs = int(qe.time_remaining)
        t_label = self.font_sm.render(f"{secs}s", True, t_color)
        self.screen.blit(t_label, (bar_x + bar_w + 6, ty + (bar_h - t_label.get_height()) // 2))

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

        # ── Celebration popup ─────────────────────────────────────────
        if qe.celebrating:
            t = qe.celebration_timer
            pulse = abs(math.sin(t * 6))
            glow_alpha = int(80 + 60 * pulse)
            cel_ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            cel_ov.fill((0, 0, 0, glow_alpha))
            self.screen.blit(cel_ov, (0, 0))

            cel_font = self.font_xl
            cel_surf = cel_font.render(qe.celebration_text, True, FP.GOLD_BRIGHT)
            # Glow color pulses between gold and white
            glow_r = int(255)
            glow_g = int(200 + 55 * pulse)
            glow_b = int(40 + 80 * pulse)
            # Shadow
            shadow  = cel_font.render(qe.celebration_text, True, (0, 0, 0))
            cx_cel  = (WINDOW_W - cel_surf.get_width())  // 2
            cy_cel  = (WINDOW_H - cel_surf.get_height()) // 2 - 40
            self.screen.blit(shadow, (cx_cel + 5, cy_cel + 5))
            self.screen.blit(cel_surf, (cx_cel, cy_cel))

            sub_surf = self.font_lg.render("PERFECT COMBO!", True, (180, 255, 180))
            sx_cel   = (WINDOW_W - sub_surf.get_width()) // 2
            self.screen.blit(sub_surf, (sx_cel, cy_cel + cel_surf.get_height() + 14))

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
        bh = min(88 + total_rows * row_h + (sep_h if n_equip and n_unequip else 0) + 44,
                 WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EQUIP / UNEQUIP  ·  GEOGRAPHY",
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
                elif isinstance(item, (Armor, Shield)):
                    detail_text = (f"{getattr(item, 'slot', 'shield')}  +{item.ac_bonus} AC"
                                   f"  (quiz: geography x{item.equip_threshold})")
                else:
                    detail_text = item.item_class
                detail_col = FP.BODY_TEXT if isinstance(item, (Weapon, Armor, Shield)) else FP.FADED_TEXT
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
        bh = min(90 + len(self.accessory_menu_items) * 66 + 50, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with gold border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EQUIP ACCESSORY  ·  HISTORY",
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
                    detail_text = f"grants {fx['status']}  (history x{item.equip_threshold})"
                else:
                    detail_text = f"{fx.get('stat','?')} +{fx.get('amount',0)}  (history x{item.equip_threshold})"
            else:
                detail_text = f"unidentified  (history x{item.equip_threshold})"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "Press number to equip  |  ESC to cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Wand menu overlay
    # ------------------------------------------------------------------

    def _draw_wand_menu(self):
        # FANTASY: Grimoire-themed wand menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.wand_menu_items) * 66 + 50, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with arcane border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="USE WAND  ·  SCIENCE",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Nearest visible monster is auto-targeted.",
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
            "Press number to invoke  |  ESC to cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Scroll menu overlay
    # ------------------------------------------------------------------

    def _draw_scroll_menu(self):
        # FANTASY: Grimoire-themed scroll menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.scroll_menu_items) * 66 + 50, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with gold border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="READ SCROLL  ·  GRAMMAR",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Scroll is consumed whether or not you succeed.",
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
            self.screen.blit(
                self.font_md.render(dname, True, FP.BODY_TEXT), (bx + 70, iy + 14)
            )
            if item.identified or item.id in self.player.known_item_ids:
                detail_text = f"effect: {item.effect}  (grammar x{item.quiz_threshold})"
            else:
                detail_text = f"unknown effect  (grammar x{item.quiz_threshold})"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "Press number to read  |  ESC to cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Identify menu overlay
    # ------------------------------------------------------------------

    def _draw_identify_menu(self):
        # FANTASY: Grimoire-themed identify menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.identify_menu_items) * 66 + 50, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with arcane border
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.ARCANE_BRIGHT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="IDENTIFY ITEM  ·  PHILOSOPHY",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render("Answer 3 correct to identify the chosen item.",
                                True, FP.BODY_TEXT),
            (bx + 20, by + 48)
        )
        draw_divider(self.screen, bx + 10, by + 72, bw - 20)

        max_detail_w = bw - 90
        for i, item in enumerate(self.identify_menu_items):
            iy = by + 82 + i * 66
            # FANTASY: Alternating midnight row colors
            pygame.draw.rect(
                self.screen,
                FP.MIDNIGHT_MID if i % 2 == 0 else FP.MIDNIGHT,
                (bx + 10, iy, bw - 20, 60), border_radius=6
            )
            dname = self._display_name(item)
            type_label = item.item_class
            tier_lbl = f"  tier {item.quiz_tier}" if hasattr(item, 'quiz_tier') else ""
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, FP.GOLD_BRIGHT), (bx + 18, iy + 14)
            )
            self.screen.blit(
                self.font_md.render(dname, True, FP.BODY_TEXT), (bx + 70, iy + 14)
            )
            detail_text = f"{type_label}{tier_lbl}  —  philosophy x3 correct"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "Press number to identify  |  ESC to cancel", True, FP.HINT_TEXT
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
               + single_header_h   + n_single   * row_h + 60,
            WINDOW_H - 40
        )
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with success (green) border for cooking
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.SUCCESS_TEXT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="COOK INGREDIENT  ·  COOKING",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        self.screen.blit(
            self.font_sm.render(
                f"SP: {self.player.sp}/{self.player.max_sp}  —  cooking restores SP + permanent stat bonuses",
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
            hdr = "COMPOUND RECIPES  (letter keys — you have all ingredients!)"
            hdr_surf = self.font_sm.render(hdr, True, FP.GOLD_BRIGHT)
            if hdr_surf.get_width() > max_header_w:
                while len(hdr) > 1 and self.font_sm.size(hdr + '…')[0] > max_header_w:
                    hdr = hdr[:-1]
                hdr_surf = self.font_sm.render(hdr + '…', True, FP.GOLD_BRIGHT)
            self.screen.blit(hdr_surf, (bx + 18, cy))
            cy += compound_header_h
        elif n_single:
            tip_lines = self._wrap_text(
                "Tip: collect multiple ingredients to unlock compound recipes with greater bonuses.",
                self.font_sm, max_header_w
            )
            tip_line_h = self.font_sm.get_height() + 2
            for tip_line in tip_lines:
                self.screen.blit(self.font_sm.render(tip_line, True, FP.FADED_TEXT), (bx + 18, cy))
                cy += tip_line_h
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

    def _draw_eat_menu(self):
        # FANTASY: Grimoire-themed eat menu
        draw_overlay(self.screen, 160)

        bw = min(760, GAME_W - 40)
        bh = min(90 + len(self.eat_menu_items) * 66 + 50, WINDOW_H - 40)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        # FANTASY: Dark panel with success (green) border for nourishment
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.SUCCESS_TEXT)
        draw_header_bar(self.screen, (bx, by, bw, 44), text="EAT  ·  NOURISHMENT",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT)

        sp = self.player.sp
        sp_color = FP.SUCCESS_TEXT if sp > 30 else FP.WARNING_TEXT if sp > 10 else FP.DANGER_TEXT
        self.screen.blit(
            self.font_sm.render(
                f"SP: {sp}/{self.player.max_sp}  — Food restores SP. Ingredients eaten raw give minimal SP.",
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
                detail_text = f"raw: {raw_sp} SP  (cook for up to {best_sp} SP)"
            detail_surf = self.font_sm.render(detail_text, True, FP.FADED_TEXT)
            if detail_surf.get_width() > max_detail_w:
                while len(detail_text) > 1 and self.font_sm.size(detail_text + '\u2026')[0] > max_detail_w:
                    detail_text = detail_text[:-1]
                detail_surf = self.font_sm.render(detail_text + '\u2026', True, FP.FADED_TEXT)
            self.screen.blit(detail_surf, (bx + 70, iy + 40))

        hint_y = by + bh - 34
        draw_divider(self.screen, bx + 10, hint_y - 8, bw - 20)
        hint = self.font_sm.render(
            "Press number to eat  |  ESC to cancel", True, FP.HINT_TEXT
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    def _draw_confirm_exit(self):
        # FANTASY: Parchment confirmation dialog
        draw_overlay(self.screen, 170)
        bw, bh = min(520, GAME_W - 40), 210
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh))
        draw_header_bar(self.screen, (bx, by, bw, 40),
                        text="LEAVE THE DUNGEON?",
                        font=self.font_lg, text_color=FP.GOLD_BRIGHT)

        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )
        if has_stone:
            sub = "You carry the Philosopher's Stone — this ends in triumph!"
            sc  = FP.GOLD_BRIGHT
        else:
            sub = "You do not carry the Philosopher's Stone."
            sc  = FP.WARNING_TEXT

        sub_surf = self.font_md.render(sub, True, sc)
        self.screen.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + 60))
        draw_divider(self.screen, bx + 20, by + 100, bw - 40)
        hint = self.font_md.render("[ Y ] Leave   [ N ] Stay", True, FP.GOLD_PALE)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + 118))
        hint2 = self.font_sm.render("Departing without the Stone ends your quest.", True, FP.FADED_TEXT)
        self.screen.blit(hint2, (bx + (bw - hint2.get_width()) // 2, by + 158))

    # ------------------------------------------------------------------
    # Victory screen
    # ------------------------------------------------------------------

    def _draw_victory_screen(self):
        # FANTASY: Illuminated manuscript victory screen
        draw_overlay(self.screen, 210, (12, 10, 0))
        score = self._calc_score()
        cx    = GAME_W // 2
        cy    = WINDOW_H // 2

        # FANTASY: Animated rune circles
        t = pygame.time.get_ticks() / 1000.0
        draw_rune_circle(self.screen, cx, cy, 260, (*FP.GOLD_DARK, 120), t, 16)
        draw_rune_circle(self.screen, cx, cy, 180, (*FP.GOLD, 90),       -t * 1.3, 10)
        draw_candle_glow(self.screen, cx, cy, 0.9)

        # FANTASY: Gold filigree bar under title
        draw_filigree_bar(self.screen, cx - 320, cy - 100, 640, FP.GOLD)

        centered_text(self.screen, self.font_xl, "VICTORY!", FP.GOLD_BRIGHT, cy - 148, shadow=True)
        draw_glow_text(self.screen, self.font_lg,
                       "You retrieved the Philosopher's Stone!",
                       FP.PARCHMENT_LIGHT, (cx - 320, cy - 100))

        draw_filigree_bar(self.screen, cx - 260, cy - 68, 520, FP.GOLD_DARK)

        score_text = f"Final Score:  {score:,}"
        draw_shadow_text(self.screen, self.font_lg, score_text,
                         FP.GOLD_BRIGHT, (cx - self.font_lg.size(score_text)[0]//2, cy - 56))

        details = (f"Turns: {self.turn_count}   |   "
                   f"Deepest Level: {self.level_mgr.max_level_reached}   |   "
                   f"Kills: {self.level_mgr.monsters_killed}")
        d_surf = self.font_md.render(details, True, FP.BODY_TEXT)
        self.screen.blit(d_surf, (cx - d_surf.get_width() // 2, cy))

        breakdown = (f"({self.turn_count}×10)  +  ({self.level_mgr.max_level_reached}×1000)  +"
                     f"  ({self.level_mgr.monsters_killed}×100)  +  50 000 stone bonus")
        b_surf = self.font_sm.render(breakdown, True, FP.FADED_TEXT)
        self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, cy + 32))

        draw_filigree_bar(self.screen, cx - 260, cy + 68, 520, FP.GOLD_DARK)
        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, cy + 90))

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
        draw_rune_circle(self.screen, cx, cy, 240, (*FP.BURGUNDY, 110), t * 0.4, 14)
        draw_rune_circle(self.screen, cx, cy, 160, (*FP.BLOOD, 70),     -t * 0.6, 8)

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

        draw_filigree_bar(self.screen, cx - 300, cy - 110, 600, FP.BURGUNDY_MID)
        draw_glow_text(self.screen, self.font_xl, title_text,
                       FP.BLOOD, (cx - self.font_xl.size(title_text)[0]//2, cy - 148),
                       glow_color=FP.BURGUNDY)
        draw_filigree_bar(self.screen, cx - 300, cy - 96, 600, FP.BURGUNDY_MID)

        sub_surf = self.font_lg.render(sub_text, True, tc)
        self.screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy - 80))

        score_text = f"Final Score:  {score:,}"
        draw_shadow_text(self.screen, self.font_lg, score_text,
                         FP.GOLD_PALE, (cx - self.font_lg.size(score_text)[0]//2, cy - 40))

        details = (f"Turns: {self.turn_count}   |   "
                   f"Deepest Level: {self.level_mgr.max_level_reached}   |   "
                   f"Kills: {self.level_mgr.monsters_killed}")
        d_surf = self.font_md.render(details, True, FP.BODY_TEXT)
        self.screen.blit(d_surf, (cx - d_surf.get_width() // 2, cy + 2))

        draw_filigree_bar(self.screen, cx - 260, cy + 32, 520, FP.BURGUNDY_DARK)
        hint = self.font_md.render("Press ESC to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, cy + 52))

    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------

    def _help_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_SLASH, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # Examine corpse  (X key — philosophy quiz → reveals lore + stat block)
    # ------------------------------------------------------------------

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

        # Draw stat lines
        for line in stat_lines:
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

    def _draw_help_screen(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        self.screen.blit(overlay, (0, 0))

        bw, bh = min(1060, GAME_W - 40), min(WINDOW_H - 40, WINDOW_H - 40)
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
            ("Arrows / hjkl",  "Move / attack",                      FP.BODY_TEXT),
            ("ACTIONS", None, FP.GOLD_PALE),
            ("G  or  ,",       "Pick up item",                        FP.BODY_TEXT),
            ("E",              "Equip weapon/armor  [Geography]",     FP.BODY_TEXT),
            ("R",              "Equip accessory  [History]",          FP.BODY_TEXT),
            ("U",              "Use wand  [Science]",                 FP.BODY_TEXT),
            ("S",              "Read scroll  [Grammar]",              FP.BODY_TEXT),
            ("I",              "Identify item  [Philosophy]",         FP.BODY_TEXT),
            ("H",              "Harvest corpse  [Animal]",            FP.BODY_TEXT),
            ("C",              "Cook ingredient  [Cooking]",          FP.BODY_TEXT),
            ("Z",              "Eat food / raw ingredient",           FP.BODY_TEXT),
            ("\\",             "Pray  [Theology]",                    (200, 180, 255)),
            ("F",              "Fire ranged weapon  [Math]",          FP.BODY_TEXT),
            ("P",              "Pick lock  [Economics]",              FP.BODY_TEXT),
            ("A",              "Attack / open container",             FP.BODY_TEXT),
            ("X",              "Examine corpse lore  [Philosophy]",   FP.BODY_TEXT),
            ("NAVIGATION", None, FP.GOLD_PALE),
            (">",              "Descend stairs",                      FP.BODY_TEXT),
            ("<",              "Ascend / exit dungeon",               FP.BODY_TEXT),
            ("QUIZ ANSWERS", None, FP.GOLD_PALE),
            ("1  2  3  4",     "Answer quiz questions",               FP.GOLD_BRIGHT),
            ("MISC", None, FP.GOLD_PALE),
            ("?",              "This help screen",                    FP.BODY_TEXT),
            ("ESC",            "Cancel menu / quit game",             FP.BODY_TEXT),
        ]

        col_w   = (bw - 40) // 2
        left_x  = bx + 20
        right_x = bx + 20 + col_w
        y       = by + 66
        line_h  = 26
        col_break = 12

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
                dsurf = self.font_sm.render(desc, True, color)
                self.screen.blit(ksurf, (cx_, cy_))
                self.screen.blit(dsurf, (cx_ + 160, cy_))

        # FANTASY: Footer hint in HINT_TEXT
        hint = self.font_sm.render("Press ESC or ? to close", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 32))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    from save_system import save_exists, load_game, save_game

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    # Welcome screen — may return (None, None) if player chose Continue
    welcome = WelcomeScreen(screen)
    player_name, secret_build = welcome.run(clock)

    if player_name is None:
        # Load saved game
        state = load_game()
        if state:
            game = Game(screen,
                        player_name=state.get('player_name', 'Adventurer'),
                        secret_build=state.get('secret_build'))
            game.load_state(state)
        else:
            # Fallback: saved file was corrupted / missing — start fresh
            game = Game(screen, player_name='Adventurer')
            game.add_message("Save file could not be loaded — starting a new game.", 'warning')
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

    # Auto-save on clean exit if the game is still in progress
    if game.state not in (STATE_DEAD, STATE_VICTORY):
        save_game(game)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
