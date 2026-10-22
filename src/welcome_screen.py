"""Welcome screen and secret-character build definitions.

The WelcomeScreen renders the title vortex, name prompt, and high-score panel
shown before each run. Selecting a name that matches a key in SECRET_BUILDS
hands the matching stat/equipment override dict back to main(), which uses it
to spawn a special Player.
"""

import math
import sys

import pygame

import ui_theme
from ui_scale import px as S
from fantasy_ui import (FP, KT, ScaledFont, draw_panel, draw_dark_panel,
                        draw_header_bar, draw_filigree_bar, draw_shadow_text,
                        draw_overlay, draw_rune_circle, draw_candle_glow,
                        centered_text, kit_on, draw_key_hints, key_hints_height,
                        draw_divider, get_font, display_title, panel_band,
                        fit_text, display_text)

# Longest name the entry box takes. It was 30, and four hero names are longer
# (Sherlock 40, Joan 33, Musashi 32): those builds could never be typed.
NAME_MAX = 48


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
#   _start_soul_spheres -> int: number of plain Soul Spheres given at start
#   _start_spheres   -> list of sphere item IDs given at start (QA: all six)
#   _no_dagger      -> True: skip the default iron_dagger
#   _immortal        -> True: player cannot die
#   _greeting        -> custom welcome message line (None = default)
#   _start_family_lore -> {family id: tier} head start in monster family
#                    knowledge: tier 1 (Recognise) or 2 (Forewarned) only,
#                    never a technique, and nothing on screen says so
#                    (MONSTER_FAMILIES_DESIGN decision 5; family_lore.grant_head_start)
# ------------------------------------------------------------------
SECRET_BUILDS: dict[str, dict] = {
    # -- Great philosophers -- INT/WIS focused, physically frail --------------
    "aristotle of stagira": {
        "INT": 18, "WIS": 16, "PER": 14, "STR": 6, "CON": 8, "DEX": 8,
        "_sprite": "player_aristotle",
        "_start_accessory": "ring_of_intellect",
        "_start_wand": "lantern_of_diogenes",
        "_greeting": "Aristotle the Philosopher enters the dungeon with calm reason.",
        "_start_family_lore": {"great_beasts": 1, "birds": 1, "serpents": 1, "vermin": 1},   # unlabelled: he wrote the History of Animals
    },
    "socrates of athens": {
        "WIS": 20, "INT": 14, "PER": 16, "STR": 8, "CON": 10, "DEX": 7,
        "_sprite": "player_socrates",
        "_start_accessory": "ring_of_wisdom",
        "_start_spells": ["cleanse_spell"],
        "_greeting": "Socrates asks the dungeon a question. It does not answer.",
    },
    "plato of athens": {
        "INT": 17, "WIS": 17, "PER": 12, "STR": 7, "CON": 9, "DEX": 9,
        "_sprite": "player_plato",
        "_start_wand": "wand_of_candle_light",
        "_start_book": "spellbook_light",
        "_no_shard": True,       # he identifies by the Forms, and is handed no Shard
        "_greeting": "Plato descends into the cave and finds it uncomfortably on-the-nose.",
    },
    "friedrich nietzsche": {
        "INT": 16, "WIS": 8, "PER": 14, "STR": 14, "CON": 12, "DEX": 10,
        "_sprite": "player_nietzsche",
        "_start_accessory": "ring_of_strength",
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
        "_start_shield": ("light_wooden", "oak"),
        "_greeting": "Achilles charges in. His heel tingles ominously.",
    },
    "leonidas of sparta": {
        "STR": 17, "CON": 18, "DEX": 12, "INT": 9, "WIS": 10, "PER": 8,
        "_sprite": "player_leonidas",
        "_start_weapon": "leonidas_dory",
        "_start_shield": "shield_of_the_spartans",
        "_greeting": "Leonidas has 299 fewer soldiers than he would like.",
    },
    "alexander the great": {
        "STR": 16, "DEX": 14, "CON": 14, "INT": 14, "WIS": 10, "PER": 12,
        "_sprite": "player_alexander",
        "_start_weapon": ("longsword", "iron"),
        "_start_accessory": "tablet_of_hammurabi",
        "_greeting": "Alexander the Great descends. He intends to conquer this too.",
    },
    "theseus of athens": {
        "STR": 14, "DEX": 14, "CON": 14, "INT": 12, "WIS": 12, "PER": 12,
        "_sprite": "player_theseus",
        "_start_weapon": ("shortsword", "iron"),
        "_start_shield": ("light_wooden", "oak"),
        "_start_accessory": "lyre_of_orpheus",
        "_greeting": "Theseus enters the dungeon. He has done this before.",
        "_start_family_lore": {"legend": 1},   # unlabelled: he walked the Labyrinth
    },
    # -- Rogues -- speed and perception ---------------------------------------
    "hermes trismegistus": {
        "DEX": 18, "PER": 18, "INT": 12, "WIS": 10, "STR": 8, "CON": 7,
        "_sprite": "player_hermes",
        "_no_dagger": True,
        "_start_weapon": ("rapier", "iron"),
        "_start_armor": "hermes_sandals_early",
        "_equip_armor": True,
        "_greeting": "Hermes was here, delivered something, and left. He returned because he forgot to sign.",
    },
    "odysseus of ithaca": {
        "DEX": 14, "INT": 16, "PER": 16, "WIS": 14, "STR": 10, "CON": 10,
        "_sprite": "player_odysseus",
        "_no_dagger": True,
        "_start_weapon": ("longbow", "yew"),
        "_start_ammo": "iron_arrow",
        "_start_armor": "cloth_of_penelope",
        "_greeting": "Odysseus descends. He expects this to take ten years.",
        "_start_family_lore": {"legend": 1},   # unlabelled: he sailed past Scylla
    },
    # -- Mages -- pure arcane power --------------------------------------------
    "merlin ambrosius": {
        "INT": 20, "WIS": 14, "PER": 12, "STR": 5, "CON": 7, "DEX": 8,
        "_sprite": "player_merlin",
        "_no_dagger": True,
        "_start_wand": "wand_of_force_dart",
        "_start_book": "spellbook_magic_dart",
        "_start_spells": ["heal_spell", "magic_shield_spell"],
        "_greeting": "Merlin descends with staff in hand and stars in his robe.",
        "_start_family_lore": {"fair_folk": 1, "dragons": 1},   # unlabelled: the red and the white dragon
    },
    # -- New characters --------------------------------------------------------
    "corwin": {
        "STR": 11, "CON": 10, "DEX": 11, "INT": 9, "WIS": 10, "PER": 12,
        "_sprite": "player_ranger",
        "_no_dagger": True,
        "_start_weapon": ("shortbow", "oak"),
        "_start_melee": ("shortsword", "iron"),
        "_start_ammo": "iron_arrow",
        "_start_extra_acc": ["charmander_stuffie"],
        "_start_unusual_sphere": True,
        "_greeting": "Corwin the Ranger nocks an arrow and descends into the dark.",
    },
    "cain": {
        "STR": 12, "CON": 11, "DEX": 12, "INT": 9, "WIS": 11, "PER": 13,
        "_sprite": "player_ranger",   # same sprite as Corwin
        "_no_dagger": True,
        # Material downgraded ash -> yew per bug bash 2026-06-01: ash has
        # peak_floor 20 (tier-2 wood), produced base_damage=6 → 33 dmg at
        # chain-5 on floor 1. Yew (peak_floor 10) yields base=2 → ~14 dmg
        # at chain-5, matching the 8-15 starter expectation.
        "_start_weapon": ("shortbow", "yew"),
        "_start_melee": ("shortsword", "iron"),
        "_start_ammo": "iron_arrow",
        "_start_accessory": "ring_protection_iron",
        "_start_extra_acc": ["charmander_stuffie"],
        "_start_unusual_sphere": True,
        "_greeting": "Cain the Hunter moves silently into the dark. Nothing escapes him.",
    },
    "fianna": {
        "STR": 7, "CON": 9, "DEX": 10, "INT": 14, "WIS": 11, "PER": 10,
        "_sprite": "player_wizard_f",
        "_no_dagger": True,
        "_start_weapon": ("quarterstaff", "oak"),
        "_start_wand": "wand_of_force_dart",
        "_start_extra_acc": ["dreamspun_sketchbook"],
        "_start_unusual_sphere": True,
        "_greeting": "Fianna the Wizard weaves a sigil in the air and descends.",
    },
    "fluffs": {
        "STR": 7, "CON": 9, "DEX": 10, "INT": 15, "WIS": 12, "PER": 10,
        "_sprite": "player_wizard_f",   # same sprite as Fianna
        "_no_dagger": True,
        "_start_weapon": ("quarterstaff", "oak"),
        "_start_wand": "wand_of_force_dart",
        "_start_book": "spellbook_magic_dart",
        "_start_extra_acc": ["dreamspun_sketchbook"],
        "_start_unusual_sphere": True,
        "_greeting": "Fluffs the Magnificent makes an entrance. The dungeon is honoured.",
    },
    "dad": {
        "STR": 20, "CON": 20, "DEX": 20, "INT": 20, "WIS": 20, "PER": 20,
        "_sprite": "player_dad",
        "_no_dagger": True,
        "_start_weapon": "punch_in_the_face",
        # Dad's fist is Dad's hand: on from the first turn and never off
        # (it started in the pack, so until a child found Equip he hit for 33).
        "_lock_weapon": True,
        # A joke build: it keeps no high score and earns no boss scrolls.
        "_joke": True,
        "_immortal": True,
        "_greeting": "Dad has arrived. Everything will be fine.",
    },
    "robyn": {
        "INT": 17, "WIS": 14, "DEX": 16, "PER": 14, "CON": 10, "STR": 9,
        "_sprite": "player_robyn",
        "_no_dagger": True,
        # Material downgraded ash -> yew per bug bash 2026-06-01 (see Cain).
        "_start_weapon": ("shortbow", "yew"),
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
        "_start_family_lore": {"demons": 1},   # unlabelled: he has met the Deadites
    },
    "geralt of rivia": {
        "STR": 14, "CON": 14, "DEX": 16, "INT": 10, "WIS": 12, "PER": 14,
        "_sprite": "player_geralt",
        "_no_dagger": True,
        "_start_weapon": "witcher_silver_blade",
        "_start_spells": ["sign_aard", "sign_igni", "sign_quen", "sign_yrden", "sign_axii"],
        "_start_potions": ["potion_of_healing", "potion_of_haste", "potion_of_fire_resistance"],
        "_greeting": "The Witcher unsheathes his silver blade. Wind's howling.",
        "_start_family_lore": {"restless_dead": 2, "ghosts": 2, "vampires_liches": 2, "shapeshifters": 2},   # unlabelled: his medallion hums
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
        "_start_family_lore": {"great_beasts": 1, "birds": 1},   # unlabelled: a trainer knows his creatures
    },
    # -- New legendary builds (multi-word full names) ------------------------
    "ada augusta byron lovelace": {
        "INT": 18, "WIS": 14, "PER": 14, "DEX": 10, "STR": 6, "CON": 8,
        "_sprite": "player_lovelace",
        "_no_dagger": True,
        "_start_weapon": ("rapier", "iron"),
        "_start_accessory": "ring_of_intellect",
        "_start_book": "spellbook_magic_dart",
        "_greeting": "Ada Lovelace traces the dungeon's algorithm in the air. It is computable.",
        "_start_family_lore": {"constructs": 1},   # unlabelled: she wrote for the Engine
    },
    "leonardo di ser piero da vinci": {
        "INT": 16, "WIS": 14, "PER": 16, "DEX": 12, "STR": 10, "CON": 10,
        "_sprite": "player_da_vinci",
        "_start_weapon": ("dagger", "iron"),
        "_start_accessory": "aesops_quill",
        "_start_extra_acc": ["dreamspun_sketchbook"],
        "_greeting": "Leonardo sketches a flying machine, glances at the ceiling, and shrugs.",
        "_start_family_lore": {"constructs": 1},   # unlabelled: he built a mechanical knight
    },
    "boudicca queen of the iceni": {
        "STR": 16, "CON": 17, "DEX": 12, "INT": 9, "WIS": 11, "PER": 12,
        "_sprite": "player_boudicca",
        "_no_dagger": True,
        "_start_weapon": ("longsword", "iron"),
        "_start_shield": ("light_wooden", "oak"),
        "_greeting": "Boudicca enters at the head of a host that exists only in her fury.",
    },
    "saint joan of arc maid of orleans": {
        "STR": 13, "CON": 13, "DEX": 12, "INT": 10, "WIS": 16, "PER": 14,
        "_sprite": "player_joan",
        "_no_dagger": True,
        "_start_weapon": ("longsword", "iron"),
        "_start_shield": ("kite_shield", "iron"),
        "_start_accessory": "lyre_of_orpheus",
        "_greeting": "Joan listens to the Voices. They say: 'Go forward, child.'",
    },
    "sir arthur conan doyle's sherlock holmes": {
        "INT": 18, "PER": 18, "WIS": 14, "DEX": 12, "STR": 9, "CON": 9,
        "_sprite": "player_sherlock",
        "_no_dagger": True,
        "_start_weapon": ("quarterstaff", "oak"),   # the famous walking-stick
        "_start_accessory": "ring_of_intellect",
        "_greeting": "Holmes glances at the dungeon and announces three deductions before stepping in.",
        "_start_family_lore": {"mortals": 1},   # unlabelled: he knows the criminal classes
    },
    "miyamoto musashi the sword saint": {
        "STR": 14, "DEX": 18, "CON": 12, "INT": 12, "WIS": 14, "PER": 14,
        "_sprite": "player_musashi",
        "_no_dagger": True,
        "_start_weapon": ("longsword", "iron"),
        "_start_melee": ("shortsword", "iron"),
        "_greeting": "Musashi draws both blades. Niten Ichi-Ryū: two heavens as one.",
    },
    "saint hildegard von bingen": {
        "WIS": 18, "INT": 15, "CON": 12, "PER": 12, "DEX": 9, "STR": 8,
        "_sprite": "player_hildegard",
        "_no_dagger": True,
        "_start_weapon": ("quarterstaff", "oak"),
        "_start_accessory": "ring_of_wisdom",
        "_start_book": "spellbook_light",
        "_greeting": "Hildegard prays. The world greens around her in answer.",
        "_start_family_lore": {"plants": 1},   # unlabelled: she wrote the Physica
    },
    "nikola tesla": {
        "INT": 18, "CON": 13, "PER": 14, "DEX": 12, "WIS": 12, "STR": 9,
        "_sprite": "player_tesla",
        "_start_weapon": ("dagger", "iron"),
        "_start_wand": "wand_of_force_dart",
        "_start_accessory": "ring_of_intellect",
        "_greeting": "Tesla touches the doorframe. It hums. The dungeon has been wired.",
        "_start_family_lore": {"constructs": 1},   # unlabelled: he built the automaton boat
    },

    # -- QA ----------------------------------------------------------------
    "titivillus": {
        "STR": 12, "CON": 12, "DEX": 12, "INT": 12, "WIS": 12, "PER": 12,
        "_sprite": "player_dad",
        "_start_weapon": ("longsword", "iron"),
        "_start_shield": ("light_wooden", "oak"),
        "_start_wand": "wand_of_candle_light",
        "_start_book": "spellbook_magic_dart",
        "_start_ammo": "iron_arrow",
        "_start_accessory": "ring_protection_iron",
        # One of each of the six Soul Spheres, to throw and check each tier.
        "_start_spheres": ["soul_sphere", "greater_soul_sphere", "master_sphere",
                           "hearth_sphere", "greater_hearth_sphere", "master_hearth_sphere"],
        "_qa_tools": True,        # Shift+I immortal toggle, Shift+W floor warp
        "_greeting": "The Scribe of Errors descends, quill in hand, to document every flaw.",
    },
}


class WelcomeScreen:
    """90s adventure-game-style welcome screen with domain art vortex."""

    _TITLE_LINE1 = "PHILOSOPHER'S"
    _TITLE_LINE2 = "QUEST"
    _PROMPT      = "Enter your name, seeker:"

    # Domain ring — colors pulled from FP.SUBJECT so the welcome teaches the
    # visual language the rest of the game uses (geography green stays
    # geography green inside the quiz panel, etc.).
    _DOMAINS = [
        # (label, degree_offset, FP.SUBJECT key, symbol) — 12 subjects, 30° apart
        ("MATH",        0, 'math',       "#"),
        ("GEOGRAPHY",  30, 'geography',  "G"),
        ("HISTORY",    60, 'history',    "H"),
        ("ANIMAL",     90, 'animal',     "A"),
        ("COOKING",   120, 'cooking',    "C"),
        ("SCIENCE",   150, 'science',    "?"),
        ("PHILOSOPHY",180, 'philosophy', "P"),
        ("GRAMMAR",   210, 'grammar',    "Q"),
        ("ECONOMICS", 240, 'economics',  "$"),
        ("THEOLOGY",  270, 'theology',   "+"),
        ("TRIVIA",    300, 'trivia',     "T"),
        ("AI",        330, 'ai',         "W"),
    ]

    # FANTASY: grimoire theme fonts, read through the UI scale on every use
    # (a resize across a scale step re-sizes them; SCALE_PLAN.md).
    font_xl   = ScaledFont('title',   52, bold=True)
    font_lg   = ScaledFont('heading', 32)
    font_md   = ScaledFont('body',    20)
    font_sm   = ScaledFont('body',    16)
    font_icon = ScaledFont('symbol',  26)
    font_tiny = ScaledFont('body',    16)
    # The subject captions on the wheel (Cinzel's hairlines need 17 px).
    font_cap  = ScaledFont('heading', 17, bold=True)

    def __init__(self, screen: pygame.Surface, version: str, notice: str | None = None):
        self.screen   = screen
        self.version  = version
        self._notice  = notice   # one-shot message (e.g. after a failed load)
        self.W, self.H = screen.get_size()
        self.cx = self.W // 2
        self.cy = self.H // 2
        self.name_buf    = ''
        self.cursor_on   = True
        self.cursor_timer = 0.0
        self._anim_t     = 0.0
        self._has_save   = False
        self._delete_flash = 0.0
        self._show_alltime = False
        self._alltime_page = 0
        self._god_prompt   = False   # True when showing "Did you mean Dad?" popup
        self._confirm_delete = None  # the name whose save Del asked to erase (Y/N)
        # Pre-render stone background into a surface
        self._bg = self._make_stone_bg()

    def _make_stone_bg(self):
        """Build the grimoire welcome background: midnight gradient + drifting
        motes of light + faint rune-traces in the dark corners.

        Pre-rendered once into a surface so the per-frame draw is cheap.
        The drifting motes that move over time are drawn live in _draw().
        """
        import random as _rng
        rng = _rng.Random(0xCAFE57)
        surf = pygame.Surface((self.W, self.H))
        # Vertical gradient from MIDNIGHT (top) to a deeper black-purple bottom
        for y in range(self.H):
            t = y / max(1, self.H)
            r = int(FP.MIDNIGHT[0] * (1 - t) + 6 * t)
            g = int(FP.MIDNIGHT[1] * (1 - t) + 4 * t)
            b = int(FP.MIDNIGHT[2] * (1 - t) + 18 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.W, y))
        # Faint star-dust scattered across the field — small dim dots
        for _ in range(160):
            sx = rng.randint(0, self.W - 1)
            sy = rng.randint(0, self.H - 1)
            shade = rng.randint(35, 70)
            sr = rng.choice([1, 1, 1, 2])
            pygame.draw.circle(surf, (shade, shade, shade + 12), (sx, sy), sr)
        # Subtle rune marks in the far corners — diamond glyphs at ~5% alpha
        rune_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for _ in range(8):
            rx = rng.randint(0, self.W - 1)
            ry = rng.randint(0, self.H - 1)
            d  = rng.randint(8, 18)
            a  = rng.randint(8, 22)
            pts = [(rx, ry - d), (rx + d, ry), (rx, ry + d), (rx - d, ry)]
            pygame.draw.polygon(rune_surf, (*FP.GOLD_DARK, a), pts, 1)
        surf.blit(rune_surf, (0, 0))
        return surf

    def _save_name(self) -> str:
        """The name the typed hero's save is stored under (a secret build's
        name is saved in proper case however it is typed)."""
        from naming import hero_name
        import os
        typed = self.name_buf.strip()
        build = SECRET_BUILDS.get(typed.lower())
        if build and build.get('_qa_tools') and not (
                os.environ.get('PQ_QA_MODE') == '1' or '--qa' in sys.argv):
            build = None          # a QA build is a plain name outside QA mode
        return hero_name(typed, build)

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
            self._has_save = save_exists(self._save_name()) if self.name_buf.strip() else False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                    if (event.x, event.y) == (self.W, self.H):
                        continue
                    # The UI scale follows the window here too (layout is
                    # the one place it is set), so the game starts with it.
                    import layout
                    layout.update(event.x, event.y)
                    self.W, self.H = event.x, event.y
                    self.cx = self.W // 2
                    self.cy = self.H // 2
                    self._bg = self._make_stone_bg()
                    continue
                if event.type == pygame.KEYDOWN:
                    if self._show_alltime:
                        # Up/Down (PgUp/PgDn) turn the pages of a long list;
                        # any other key closes the all-time overlay.
                        pages = getattr(self, '_alltime_pages', 1)
                        if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN, pygame.K_RIGHT) and pages > 1:
                            self._alltime_page = min(pages - 1, self._alltime_page + 1)
                        elif event.key in (pygame.K_UP, pygame.K_PAGEUP, pygame.K_LEFT) and pages > 1:
                            self._alltime_page = max(0, self._alltime_page - 1)
                        else:
                            self._show_alltime = False
                        continue
                    if event.key == pygame.K_F11:
                        # Full screen works on the title too, as in the game.
                        self._toggle_fullscreen()
                        continue
                    if self._god_prompt:
                        if event.key == pygame.K_y:
                            return 'Dad', SECRET_BUILDS.get('dad')
                        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                            self._god_prompt = False
                        continue
                    if self._confirm_delete:
                        # Del asks first: one stray key press erased a run.
                        if event.key == pygame.K_y:
                            from save_system import delete_save
                            delete_save(self._confirm_delete)
                            self._has_save = False
                            self._delete_flash = 2.0   # seconds to show confirmation
                            self._confirm_delete = None
                        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                            self._confirm_delete = None
                        continue
                    if (event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                            and self.name_buf.strip()):
                        name  = self.name_buf.strip()
                        if name.lower() == 'god':
                            self._god_prompt = True
                            continue
                        build = SECRET_BUILDS.get(name.lower())
                        # QA-tool builds (Shift+I immortal, Shift+W floor warp)
                        # only unlock when PQ_QA_MODE=1 or --qa was passed on
                        # the CLI. Otherwise the name is treated as a plain
                        # (non-secret) run so casual players can't stumble
                        # into dev cheats.
                        import os
                        qa_env = os.environ.get('PQ_QA_MODE') == '1'
                        qa_cli = '--qa' in sys.argv
                        if build and build.get('_qa_tools') and not (qa_env or qa_cli):
                            build = None
                        return name, build
                    elif event.key == pygame.K_DELETE and self._has_save:
                        self._confirm_delete = self._save_name()
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_buf = self.name_buf[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_F2:
                        self._show_alltime = True
                        self._alltime_page = 0
                    elif event.key == pygame.K_F3:
                        return '__STUDY_MODE__', None
                    elif len(self.name_buf) < NAME_MAX and event.unicode.isprintable():
                        self.name_buf += event.unicode

            # The saved-journey cue follows the name typed THIS frame (it was
            # computed before the frame's key events, one frame behind).
            self._has_save = save_exists(self._save_name()) if self.name_buf.strip() else False
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------ drawing

    def _toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            return            # this display has no full screen: stay windowed
        surf = pygame.display.get_surface()
        if surf is None:
            return
        w, h = surf.get_size()
        if (w, h) != (self.W, self.H):
            import layout
            layout.update(w, h)
            self.W, self.H = w, h
            self.cx = self.W // 2
            self.cy = self.H // 2
            self._bg = self._make_stone_bg()

    def _ring_cy(self) -> int:
        """Centre of the rune circles / domain ring / Stone. With the kit it
        sits midway between the title banner and the name box, so the
        wheel's top and bottom captions clear both at every window size."""
        if kit_on():
            return self._wheel()[1]
        return self.cy

    # Title banner (kit): top and height, UI px at scale 1.
    _BANNER_Y, _BANNER_H = 14, 112

    def _wheel(self):
        """The kit's subject wheel, laid out once per window size and UI
        scale: (cx, cy, (rx, ry), [(label, subject, colour, tile rect,
        caption, caption rect)]).

        The wheel does not orbit, so a long caption can never drift into a
        neighbour. Every caption sits just OUTSIDE its tile along the spoke,
        on its own flat plaque (no line crosses its text). The ring is an
        ellipse: as tall as the room between the title banner and the name
        box allows, and only as wide as it must be for no caption to touch
        another caption or a tile (VISUAL_REVIEW must-fix 6: at 1280x720 a
        circle that fits vertically crowds the top captions). The wheel and
        the Top Runs panel are centred on the window together when both do
        not fit with the wheel alone centred."""
        import ui_scale
        key = (self.W, self.H, ui_scale.get())
        got = getattr(self, '_wheel_cache', None)
        if got is not None and got[0] == key:
            return got[1]
        box_w, box_h = S(68), S(58)
        pad_x, pad_y, gap = S(6), S(2), S(4)
        f = self.font_cap
        top = S(self._BANNER_Y + self._BANNER_H) + S(10)
        box, _sy, _keys = self._bottom_layout()
        bottom = box.y - S(10)
        # PORTRAIT (a monitor on its side, e.g. 1080x1920; bug bash 4 call
        # 19): the wheel is sized by the window's WIDTH, centred, and the
        # Top Runs panel stacks under it instead of beside it.
        portrait = self.portrait()
        lb_w, lb_h = self._leaderboard_size()
        if portrait and lb_w:
            bottom -= lb_h + S(20)
        cy = (top + bottom) // 2
        caps = []
        for label, deg, key_, _sym in self._DOMAINS:
            text = display_title(label)
            w, h = f.size(text)
            caps.append((label, deg, key_, text, w + 2 * pad_x, h + 2 * pad_y))

        def place(cx, rx, ry):
            out = []
            for label, deg, key_, text, cw, ch in caps:
                a = math.radians(deg)
                ux, uy = math.cos(a), math.sin(a)
                ix, iy = cx + rx * ux, cy + ry * uy
                tile = pygame.Rect(round(ix - box_w / 2), round(iy - box_h / 2), box_w, box_h)
                need = []
                if abs(ux) > 1e-6:
                    need.append((box_w + cw) / 2 / abs(ux))
                if abs(uy) > 1e-6:
                    need.append((box_h + ch) / 2 / abs(uy))
                d = min(need) + gap
                cap = pygame.Rect(0, 0, cw, ch)
                cap.center = (round(ix + ux * d), round(iy + uy * d))
                out.append((label, key_, FP.SUBJECT.get(key_, FP.GOLD_PALE), tile, text, cap))
            return out

        def clear(items):
            # (rect, owner): a caption sits against its own tile by design;
            # every other pair keeps a few px apart.
            rects = [(it[3], i) for i, it in enumerate(items)] +                     [(it[5], i) for i, it in enumerate(items)]
            for j, (r1, o1) in enumerate(rects):
                if r1.top < top or r1.bottom > bottom:
                    return False
                if portrait and (r1.left < S(12) or r1.right > self.W - S(12)):
                    return False
                for r2, o2 in rects[j + 1:]:
                    if o1 == o2:
                        if r1.colliderect(r2):
                            return False
                    elif r1.colliderect(r2.inflate(S(6), S(4))):
                        return False
            return True

        found = None
        ry = (bottom - top) // 2
        if portrait:
            ry = min(ry, self.W // 2)        # the shorter side sizes the wheel
        px0 = self.cx if portrait else 0
        while ry >= S(100) and found is None:
            rx = ry
            while rx <= ry * 2:
                items = place(px0, rx, ry)
                if clear(items):
                    found = (rx, ry, items)
                    break
                rx += S(2)
            ry -= S(2)
        if found is None:                                       # pragma: no cover
            rx = ry = S(150)
        else:
            rx, ry, _items = found
        # Horizontal placement: centred on the window when the Top Runs panel
        # still fits beside it; otherwise the pair is centred together.
        probe = place(0, rx, ry)
        left = min(min(it[3].left, it[5].left) for it in probe)
        right = max(max(it[3].right, it[5].right) for it in probe)
        cx = self.cx
        self._lb_portrait_y = None
        if portrait:
            # Wheel and Top Runs centred together, as one column, in the room
            # between the title banner and the name box.
            wt = min(min(it[3].top, it[5].top) for it in probe)
            wb = max(max(it[3].bottom, it[5].bottom) for it in probe)
            region_bottom = box.y - S(10)
            group_h = (wb - wt) + ((S(20) + lb_h) if lb_w else 0)
            g_top = top + max(0, (region_bottom - top - group_h) // 2)
            cy += g_top - wt
            if lb_w:
                self._lb_portrait_y = g_top + (wb - wt) + S(20)
        else:
            room = self.W - S(24) - lb_w - S(40)
            if lb_w and cx + right > room:
                total = (right - left) + S(40) + lb_w
                cx = (self.W - total) // 2 - left
        place_cy = cy
        items = place(cx, rx, ry)
        layout_ = (cx, place_cy, (rx, ry), items)
        self._wheel_cache = (key, layout_)
        return layout_

    def portrait(self) -> bool:
        """A window taller than it is wide (a portrait monitor)."""
        return self.H > self.W

    def wheel_right(self) -> int:
        """Right edge of everything the kit's wheel draws."""
        _cx, _cy, _r, items = self._wheel()
        return max(max(it[3].right, it[5].right) for it in items)

    def _draw(self):
        t  = self._anim_t
        cx = self._wheel()[0] if kit_on() else self.cx
        cy = self._ring_cy()

        # Static background (gradient + stars + faint runes), then the layered
        # animated grimoire elements over the top.
        self.screen.blit(self._bg, (0, 0))
        self._draw_radial_glow(cx, cy)
        # Counter-rotating rune circles — slow, hypnotic. Pulsing intensity
        # from a sine of the anim time so the candle glow breathes.
        pulse = 0.5 + 0.5 * math.sin(t * 0.9)
        kit = kit_on()
        if not kit:
            # With the kit the wheel is still and these two broken rings read
            # as ~20 loose gold dashes scattered round it (VISUAL_REVIEW_2
            # minor 7), so only the procedural look keeps them.
            draw_rune_circle(self.screen, cx, cy, int(min(cx, cy) * 0.78),
                             (*FP.GOLD_DARK, int(80 + 50 * pulse)), t * 0.4, 16)
            draw_rune_circle(self.screen, cx, cy, int(min(cx, cy) * 0.36),
                             (*FP.GOLD, int(60 + 60 * pulse)), -t * 0.7, 12)
        draw_candle_glow(self.screen, cx, cy, intensity=0.6 + 0.4 * pulse)
        if kit:
            # The vignette darkens the background only: its banded frame
            # used to cut dark lines through the subject tiles' captions.
            self._draw_vignette()
        if kit:
            # The spiral goes UNDER the subject tiles and their captions
            # (DESIGN_RULES 1.1: no line through any text).
            self._draw_vortex(cx, cy, t)
            self._draw_domain_ring(cx, cy, t)
        else:
            self._draw_domain_ring(cx, cy, t)
            self._draw_vortex(cx, cy, t)
        self._draw_stone(cx, cy, t)
        if not kit:
            self._draw_vignette()
        self._draw_title_banner(self.cx)
        self._draw_name_input(self.cx, self.cy)
        self._draw_footer(self.cx)
        self._draw_leaderboard()
        if self._show_alltime:
            self._draw_alltime()
        if self._god_prompt:
            self._draw_god_prompt()

    def _draw_god_prompt(self):
        """The 'Did you mean Dad?' easter-egg confirm — now in grimoire chrome."""
        draw_overlay(self.screen, alpha=200)
        if kit_on():
            bw, bh = S(460), S(196)
            bx, by = (self.W - bw) // 2, (self.H - bh) // 2
            panel = pygame.Rect(bx, by, bw, bh)
            draw_dark_panel(self.screen, panel, border_color=FP.GOLD)
            hr = draw_header_bar(self.screen, (bx, by, bw, S(42)),
                                 text="A Question of Address", font=get_font('heading', 24),
                                 frame=(panel, FP.GOLD))
            msg = self.font_lg.render("Did you mean, 'Dad'?", True, KT.TEXT_QUIZ)
            self.screen.blit(msg, (bx + (bw - msg.get_width()) // 2, hr.bottom + S(8)))
            b = panel_band('panel', panel)
            kh = key_hints_height()
            draw_key_hints(self.screen, (bx + b + S(16), by + bh - b - S(10) - kh,
                                         bw - 2 * (b + S(16)), kh),
                           "Y: yes   N: no")
            return
        bw, bh = S(420), S(150)
        bx = (self.W - bw) // 2
        by = (self.H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, S(36)),
                        text="A Question of Address",
                        font=self.font_md, text_color=FP.GOLD_BRIGHT,
                        frame=((bx, by, bw, bh), FP.GOLD))
        msg = self.font_lg.render("Did you mean, 'Dad'?",
                                  True, FP.PARCHMENT_LIGHT)
        self.screen.blit(msg, (bx + (bw - msg.get_width()) // 2, by + S(56)))
        hint = self.font_md.render("(Y)es   /   (N)o", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - S(32)))

    def _draw_radial_glow(self, cx, cy):
        # Static for a given window size + centre: built once and kept (it
        # used to allocate a full-window SRCALPHA surface every frame,
        # GROUNDWORK_REVIEW 10). A resize rebuilds it.
        key = (self.W, self.H, cx, cy)
        cached = getattr(self, '_glow_cache', None)
        if cached is None or cached[0] != key:
            glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            for r, alpha in [(300, 12), (240, 18), (180, 22), (130, 28), (90, 20)]:
                pygame.draw.circle(glow, (*FP.ARCANE_DIM, alpha), (cx, cy), r)
            cached = self._glow_cache = (key, glow)
        self.screen.blit(cached[1], (0, 0))

    def _draw_domain_ring(self, cx, cy, t):
        kit = kit_on()
        if kit and all(ui_theme.icon(f"subject_{k}", S(32)) is not None
                       for _l, _d, k, _s in self._DOMAINS):
            self._draw_kit_wheel()
            return
        ring_r = min(self.cx, self.cy) * (0.49 if kit else 0.52)
        orbit_speed = 0.018   # radians/sec -- very slow orbit
        base_angle  = t * orbit_speed

        # Helper: domain key -> color via FP.SUBJECT with a sensible fallback
        # for trivia/AI which aren't in the SUBJECT map.
        def _domain_color(key):
            if key is None:
                return FP.GOLD_PALE
            return FP.SUBJECT.get(key, FP.GOLD_PALE)

        captions = []
        for i, (label, deg_off, subject_key, symbol) in enumerate(self._DOMAINS):
            color = _domain_color(subject_key)
            angle  = base_angle + math.radians(deg_off)
            ix = cx + int(ring_r * math.cos(angle))
            iy = cy + int(ring_r * math.sin(angle))

            # Energy tendril from icon toward center — three fading lines so
            # the eye reads "the domains feed the Stone".
            for w, frac in [(3, 0.18), (2, 0.36), (1, 0.62)]:
                c = tuple(int(v * frac) for v in color)
                pygame.draw.line(self.screen, c, (ix, iy), (cx, cy), w)

            # Mini grimoire-panel as the icon backdrop. The double-border +
            # diamond accents match the rest of the game's modal chrome at
            # icon scale.
            box_w, box_h = S(68), S(58)
            bx, by = ix - box_w // 2, iy - box_h // 2
            if kit and ui_theme.icon(f"subject_{subject_key}", S(32)) is not None:
                # The kit's painted subject icon on a flat raised tile with
                # the subject's colour as its edge (the identity colour).
                box = pygame.Rect(bx, by, box_w, box_h)
                pygame.draw.rect(self.screen, KT.RAISED, box)
                pygame.draw.rect(self.screen, color, box, 2)
                pygame.draw.rect(self.screen, KT.GOLD_DARK, box.inflate(-S(8), -S(8)), 1)
                isz = S(32)
                ui_theme.draw_icon(self.screen, f"subject_{subject_key}",
                                   (ix - isz // 2, iy - isz // 2, isz, isz))
                # Captions go on after every tile (a neighbour's tile must
                # not cover the start of a long one like "Geography").
                captions.append((display_title(label), ix, by + box_h + S(2)))
                continue
            # Translucent midnight fill
            inner = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            inner.fill((*FP.MIDNIGHT, 220))
            self.screen.blit(inner, (bx, by))
            # Double border (outer subject-color, inner gold-dark)
            pygame.draw.rect(self.screen, color, (bx, by, box_w, box_h), 2)
            pygame.draw.rect(self.screen, FP.GOLD_DARK,
                             (bx + 3, by + 3, box_w - 6, box_h - 6), 1)
            # Mid-edge diamond ornaments — same vocabulary as draw_dark_panel
            for px, py, vert in [
                (bx + box_w // 2, by, False),
                (bx + box_w // 2, by + box_h - 1, False),
            ]:
                d = 3
                pts = ([(px, py - d), (px + d, py), (px, py + d), (px - d, py)]
                       if not vert else
                       [(px - d, py), (px, py - d), (px + d, py), (px, py + d)])
                pygame.draw.polygon(self.screen, color, pts)

            # Domain symbol (large glyph) — gold-bright so the eye finds it
            sym_surf = self.font_icon.render(symbol, True, FP.GOLD_BRIGHT)
            self.screen.blit(sym_surf, (ix - sym_surf.get_width() // 2, iy - S(18)))

            # Domain-specific mini pixel art shape (drawn in subject color)
            self._draw_domain_detail(ix, iy, label, color, t)

            # Label below box — pale gold so it sits as caption, not headline
            lbl = self.font_tiny.render(label, True, FP.GOLD_PALE)
            self.screen.blit(lbl, (ix - lbl.get_width() // 2, by + box_h + S(3)))

        if captions:
            lf = get_font('heading', 13, bold=True)
            for text, x, y in captions:
                draw_shadow_text(self.screen, lf, text, FP.GOLD_PALE,
                                 (x - lf.size(text)[0] // 2, y), offset=1)

    def _draw_kit_wheel(self):
        """The kit's subject wheel (see ``_wheel``): spokes, then the tiles,
        then each caption on a flat plaque, so no line crosses its text."""
        cx, cy, _r, items = self._wheel()
        for _label, _key, color, tile, _text, _cap in items:
            for w, frac in [(3, 0.18), (2, 0.36), (1, 0.62)]:
                c = tuple(int(v * frac) for v in color)
                pygame.draw.line(self.screen, c, tile.center, (cx, cy), w)
        isz = S(32)
        for _label, key_, color, tile, _text, _cap in items:
            pygame.draw.rect(self.screen, KT.RAISED, tile)
            pygame.draw.rect(self.screen, color, tile, 2)
            pygame.draw.rect(self.screen, KT.GOLD_DARK, tile.inflate(-S(8), -S(8)), 1)
            ui_theme.draw_icon(self.screen, f"subject_{key_}",
                               (tile.centerx - isz // 2, tile.centery - isz // 2, isz, isz))
        f = self.font_cap
        for _label, _key, _color, _tile, text, cap in items:
            self.screen.fill(KT.VOID, cap)
            pygame.draw.rect(self.screen, KT.GOLD_DARK, cap, 1)
            ts = f.render(text, True, KT.TEXT_HEAD)
            self.screen.blit(ts, (cap.centerx - ts.get_width() // 2,
                                  cap.centery - ts.get_height() // 2))

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
            # Alternate arm colors from domain palette — fall back to gold
            # for the two non-FP-mapped subjects (trivia, AI).
            subject_key = self._DOMAINS[arm % len(self._DOMAINS)][2]
            domain_color = (FP.SUBJECT.get(subject_key, FP.GOLD_PALE)
                            if subject_key else FP.GOLD_PALE)

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

        # Octagon gem — grimoire palette (gold-dark facet, gold edge,
        # vellum inner glow, white sparkle cross). All FP-sourced.
        r = orb_r
        oct_pts = [(cx + int(r * math.cos(math.radians(a))),
                    cy + int(r * math.sin(math.radians(a))))
                   for a in range(0, 360, 45)]
        pygame.draw.polygon(self.screen, FP.GOLD_DARK, oct_pts)
        # Face highlights
        pygame.draw.polygon(self.screen, FP.GOLD_BRIGHT, oct_pts, 2)
        # Inner gem facet
        inner_pts = [(cx + int((r * 0.5) * math.cos(math.radians(a + 22))),
                      cy + int((r * 0.5) * math.sin(math.radians(a + 22))))
                     for a in range(0, 360, 45)]
        pygame.draw.polygon(self.screen, FP.VELLUM, inner_pts)
        # Sparkle cross
        spark_len = int(8 + pulse * 10)
        for ang in [0, 45, 90, 135]:
            rad = math.radians(ang + t * 30)
            ex  = cx + int(spark_len * math.cos(rad))
            ey  = cy + int(spark_len * math.sin(rad))
            ex2 = cx - int(spark_len * math.cos(rad))
            ey2 = cy - int(spark_len * math.sin(rad))
            pygame.draw.line(self.screen, FP.WHITE, (ex, ey), (ex2, ey2), 2)

    def _draw_vignette(self):
        # Static per window size: built once and kept (was a full-window
        # surface + 28 rect draws every frame, GROUNDWORK_REVIEW 10).
        # A smooth elliptical falloff. The old one stacked 28 rectangle
        # outlines with gaps between them: visible concentric boxes at
        # 3440x1440.
        W, H = self.W, self.H
        cached = getattr(self, '_vignette_cache', None)
        if cached is None or cached[0] != (W, H):
            vig = pygame.Surface((W, H), pygame.SRCALPHA)
            vig.fill((0, 0, 0, 0))
            try:
                import numpy as np
                xs = (np.arange(W) - W / 2) / (W / 2)
                ys = (np.arange(H) - H / 2) / (H / 2)
                d = np.sqrt(xs[:, None] ** 2 + ys[None, :] ** 2) / math.sqrt(2)
                a = np.clip((d - 0.45) / 0.55, 0.0, 1.0) ** 1.8 * 200
                pa = pygame.surfarray.pixels_alpha(vig)
                pa[...] = a.astype(np.uint8)
                del pa
            except ImportError:                                  # pragma: no cover
                pass
            cached = self._vignette_cache = ((W, H), vig)
        self.screen.blit(cached[1], (0, 0))

    def _draw_title_banner(self, cx):
        # FANTASY: Illuminated manuscript title -- gold text on midnight panel
        if kit_on():
            # The kit's scroll plaque (rolls at both ends), tall enough that
            # the tail of the big Q stays on it.
            bw, bh = S(640), S(self._BANNER_H)
            bx, by = cx - bw // 2, S(self._BANNER_Y)
            ui_theme.draw_piece(self.screen, 'header', (bx, by, bw, bh), accent=FP.GOLD)
            for text, y, font, col in [
                (self._TITLE_LINE1, by + S(6), self.font_lg, FP.GOLD),
                (self._TITLE_LINE2, by + S(34), self.font_xl, FP.GOLD_BRIGHT),
            ]:
                centered_text(self.screen, font, text, col, y, cx=cx, shadow=True)
            return
        bw, bh = S(640), S(106)
        bx, by = cx - bw // 2, S(22)
        draw_panel(self.screen, (bx, by, bw, bh), bg=False)
        # FANTASY: Decorative filigree under title
        draw_filigree_bar(self.screen, bx + S(20), by + bh - S(12), bw - 2 * S(20), FP.GOLD_DARK)

        for text, y, font, is_main in [
            (self._TITLE_LINE1, by + S(12), self.font_lg, False),
            (self._TITLE_LINE2, by + S(48), self.font_xl, True),
        ]:
            col = FP.GOLD if not is_main else FP.GOLD_BRIGHT
            centered_text(self.screen, font, text, col, y, shadow=True)

    def _bottom_layout(self):
        """(name box, status-line y, key-row rect) of the kit's bottom stack:
        the name box, one status line under it, the key-hint footer at the
        bottom edge. Nothing overlaps at 1280x720 (FOUNDATION_REVIEW 3.4)."""
        kh = key_hints_height()
        keys = pygame.Rect(S(150), self.H - S(10) - kh, self.W - 2 * S(150), kh)
        line_h = self.font_sm.get_height()
        status_y = keys.y - S(8) - line_h
        box_w, box_h = S(500), S(84)
        box = pygame.Rect(self.cx - box_w // 2, status_y - S(8) - box_h, box_w, box_h)
        return box, status_y, keys

    def _draw_name_input(self, cx, cy):
        if kit_on():
            box, _sy, _keys = self._bottom_layout()
            secret = self.name_buf.strip().lower() in SECRET_BUILDS
            ui_theme.draw_piece(self.screen, 'subpanel', box, body_color=KT.RAISED)
            head = pygame.Rect(box.x + 1, box.y + 1, box.w - 2, S(29))
            ui_theme.draw_piece(self.screen, 'subpanel_header', head, accent=FP.GOLD)
            hf = get_font('heading', 17, bold=True)
            label = "Secret Build Active!" if secret else self._PROMPT
            hs = hf.render(label, True, FP.GOLD_BRIGHT if secret else KT.TEXT_HEAD)
            self.screen.blit(hs, (head.centerx - hs.get_width() // 2,
                                  head.y + (head.h - S(2) - hs.get_height()) // 2))
            field = pygame.Rect(box.x + S(12), box.y + S(36), box.w - 2 * S(12), S(40))
            ui_theme.draw_piece(self.screen, 'input', field, body_color=KT.WELL)
            nf = get_font('heading', 26)
            display = self.name_buf + ('|' if self.cursor_on else ' ')
            ns = nf.render(fit_text(display, nf, field.w - S(20)), True, FP.PARCHMENT_LIGHT)
            self.screen.blit(ns, (field.x + S(10), field.centery - ns.get_height() // 2))
            return
        # FANTASY: Parchment dialog box for name entry
        box_w, box_h = S(500), S(96)
        bx = cx - box_w // 2
        by = cy + int(min(cy, self.H - cy) * 0.60)
        draw_panel(self.screen, (bx, by, box_w, box_h), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, box_w, S(32)),
                        text=self._PROMPT, font=self.font_sm, text_color=FP.GOLD_PALE,
                        frame=((bx, by, box_w, box_h), FP.GOLD, 'parchment'))
        # FANTASY: Input field
        field_y = by + S(38)
        field_h = S(34)
        pygame.draw.rect(self.screen, FP.MIDNIGHT, (bx + S(14), field_y, box_w - 2 * S(14), field_h))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (bx + S(14), field_y, box_w - 2 * S(14), field_h), 1)
        display = self.name_buf + ('|' if self.cursor_on else ' ')
        draw_shadow_text(self.screen, self.font_lg, display, FP.PARCHMENT_LIGHT,
                         (bx + S(20), field_y + (field_h - self.font_lg.get_height()) // 2))
        if self.name_buf.strip().lower() in SECRET_BUILDS:
            badge = self.font_sm.render("[*] SECRET BUILD ACTIVE!", True, FP.GOLD_BRIGHT)
            self.screen.blit(badge, (cx - badge.get_width() // 2, by + box_h + S(8)))

    def _draw_footer(self, cx):
        has_save = getattr(self, '_has_save', False)
        if kit_on():
            _box, status_y, keys = self._bottom_layout()
            notice = getattr(self, '_notice', None)
            flash = getattr(self, '_delete_flash', 0.0)
            line = None
            confirm = getattr(self, '_confirm_delete', None)
            if confirm:
                line = (f"Erase the saved journey of {confirm}? It cannot be undone.",
                        FP.DANGER_TEXT_LIGHT)
            elif notice:
                line = (display_text(notice), FP.GOLD_BRIGHT)
            elif flash > 0.0:
                line = ("Save deleted. Press Enter to start fresh.", FP.DANGER_TEXT_LIGHT)
            elif has_save:
                line = ("Saved journey found.", FP.SUCCESS_TEXT)
            if line:
                # Wrap rather than cut: the set-aside notice names the file it
                # kept, and an ellipsis hid that name on compact windows. The
                # last line sits on the status row; earlier lines stack above.
                words, rows, cur = line[0].split(), [], ''
                for w in words:
                    trial = f"{cur} {w}".strip()
                    if cur and self.font_sm.size(trial)[0] > self.W - S(40):
                        rows.append(cur)
                        cur = w
                    else:
                        cur = trial
                rows.append(cur)
                lh = self.font_sm.get_linesize()
                for i, row in enumerate(rows):
                    ls = self.font_sm.render(fit_text(row, self.font_sm, self.W - S(40)),
                                             True, line[1])
                    self.screen.blit(ls, (cx - ls.get_width() // 2,
                                          status_y - (len(rows) - 1 - i) * lh))
            if confirm:
                hints = "Y: erase the save   N / Esc: keep it"
            elif has_save and flash <= 0.0:
                hints = ("Enter: continue your journey   Del: erase save   "
                         "F2: leaderboard   F3: study mode   Esc: quit")
            else:
                hints = ("Enter: begin your quest   F2: leaderboard   "
                         "F3: study mode   Esc: quit")
            draw_key_hints(self.screen, keys, hints)
            ver = self.font_tiny.render(f"v{self.version}", True, FP.FADED_TEXT)
            self.screen.blit(ver, (self.W - ver.get_width() - S(10),
                                   keys.centery - ver.get_height() // 2))
            return
        # One-shot notice (e.g. after a failed load) -- sits above the save hint so
        # it reads alongside the reassuring "Saved journey found" line.
        notice = getattr(self, '_notice', None)
        if notice:
            note = self.font_sm.render(notice, True, FP.GOLD_BRIGHT)
            self.screen.blit(note, (cx - note.get_width() // 2, self.H - S(78)))
        text = "[ ENTER ] begin your quest     [ F2 ] leaderboard     [ F3 ] study mode     [ ESC ] quit"
        hint = self.font_tiny.render(text, True, FP.HINT_TEXT)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.H - S(28)))
        # Version number — bottom-right corner (FP.FADED_TEXT keeps it
        # legible without competing with the title)
        ver = self.font_tiny.render(f"v{self.version}", True, FP.FADED_TEXT)
        self.screen.blit(ver, (self.W - ver.get_width() - S(10), self.H - S(20)))
        # Delete-flash confirmation (shown for 2 seconds after DEL)
        flash = getattr(self, '_delete_flash', 0.0)
        confirm = getattr(self, '_confirm_delete', None)
        if confirm:
            ask = self.font_sm.render(
                f"Erase the saved journey of {confirm}?  [ Y ] erase  |  [ N ] keep it",
                True, FP.DANGER_TEXT_LIGHT)
            self.screen.blit(ask, (cx - ask.get_width() // 2, self.H - S(52)))
        elif flash > 0.0:
            del_msg = self.font_sm.render("[X] Save deleted -- press ENTER to start fresh", True, FP.DANGER_TEXT_LIGHT)
            self.screen.blit(del_msg, (cx - del_msg.get_width() // 2, self.H - S(52)))
        elif has_save:
            save_hint = self.font_sm.render("[S] Saved journey found -- ENTER to continue  |  DEL to erase", True, FP.SUCCESS_TEXT)
            self.screen.blit(save_hint, (cx - save_hint.get_width() // 2, self.H - S(52)))

    def _score_table(self, entries, font, rank_from=1, date=False):
        """Rows of a high-score table: (cells, colour, victory). Columns:
        rank, name, floor, score, grade (and date). Gold rows won the
        Stone; the table's footer says so (the old "[V]" was cryptic)."""
        rows = []
        for i, e in enumerate(entries):
            victory = bool(e.get('victory', False))
            name = str(e.get('name', '?'))[:14]
            if date and e.get('title'):
                # An honour the run earned (Loremaster), on the wide
                # all-time table only: the Top Runs panel has no room.
                name = f"{name}, {e['title']}"
            cells = [f"{rank_from + i}.", name,
                     str(e.get('level', 1)), f"{e.get('score', 0):,}",
                     str(e.get('grade', '?'))]
            if date:
                cells.append(str(e.get('date', '')))
            rows.append((cells, FP.GOLD_BRIGHT if victory else FP.BODY_TEXT, victory))
        return rows

    # Column alignment of the score tables: rank / floor / score right-aligned.
    _RIGHT_COLS = (0, 2, 3)

    def _table_widths(self, header, rows, font):
        n = len(header)
        return [max([font.size(header[k])[0]] + [font.size(r[0][k])[0] for r in rows])
                for k in range(n)]

    def _blit_table_row(self, font, cells, widths, x, y, color, gap, colors=None):
        for k, (cell, w) in enumerate(zip(cells, widths)):
            col = colors[k] if colors else color
            cs = font.render(cell, True, col)
            dx = w - cs.get_width() if k in self._RIGHT_COLS else 0
            self.screen.blit(cs, (x + dx, y))
            x += w + gap

    _LB_HEADER = ("#", "Name", "Floor", "Score", "Grade")

    def _leaderboard_size(self):
        """(width, height) of the kit's Top Runs panel, (0, 0) without runs."""
        if not hasattr(self, '_lb_entries'):
            try:
                from highscore_system import get_top
                self._lb_entries = get_top(10)
            except Exception:
                self._lb_entries = []
        if not self._lb_entries:
            return 0, 0
        r = self._leaderboard_geometry(len(self._lb_entries))
        return r[0], r[1]

    def _leaderboard_geometry(self, n_rows):
        f = self.font_sm
        rows = self._score_table(self._lb_entries, f)
        widths = self._table_widths(self._LB_HEADER, rows, f)
        gap = S(14)
        b = S(16)
        bw = max(sum(widths) + gap * (len(widths) - 1) + 2 * (b + S(14)), S(300))
        row_h = f.get_height() + S(3)
        kh = key_hints_height()
        bh = (2 * b + S(40) + S(10) + (f.get_height() + S(6))
              + n_rows * row_h + S(8) + f.get_height() + S(10) + kh + S(10))
        return bw, bh, widths, gap, row_h

    def _leaderboard_rect(self, n_rows):
        """The Top Runs panel: sized to its table, just right of the wheel
        (not pinned to the window edge), vertically centred on the wheel."""
        bw, bh, widths, gap, row_h = self._leaderboard_geometry(n_rows)
        self._wheel()
        if getattr(self, '_lb_portrait_y', None) is not None:
            # Portrait: under the wheel, centred.
            return (pygame.Rect((self.W - bw) // 2, self._lb_portrait_y, bw, bh),
                    widths, gap, row_h)
        bx = min(self.wheel_right() + S(40), self.W - S(24) - bw)
        cy = self._ring_cy()
        by = max(S(self._BANNER_Y + self._BANNER_H) + S(8), cy - bh // 2)
        return pygame.Rect(bx, by, bw, bh), widths, gap, row_h

    def _draw_leaderboard(self):
        """Right-side panel showing Top 10 runs."""
        try:
            from highscore_system import get_top
            entries = get_top(10)
        except Exception:
            return
        if not entries:
            return
        if kit_on():
            self._draw_leaderboard_kit(entries)
            return

        W, H = self.W, self.H
        bw  = S(390)
        bx  = W - bw - S(18)
        # Header + rows + divider + footer hint
        row_h    = S(22)
        header_h = S(36)
        n        = len(entries)
        bh       = header_h + S(6) + n * row_h + S(10) + S(26)
        by       = max(S(130), H // 2 - bh // 2)
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        draw_header_bar(self.screen, (bx, by, bw, header_h),
                             text="TOP RUNS", font=self.font_sm,
                             text_color=FP.GOLD_BRIGHT, accent=FP.GOLD,
                             frame=((bx, by, bw, bh), FP.GOLD))
        y = by + header_h + S(4)
        f = self.font_sm
        rows = self._score_table(entries, f)
        widths = self._table_widths(self._LB_HEADER, rows, f)
        gap = S(10)
        self._blit_table_row(f, self._LB_HEADER, widths, bx + S(10), y, FP.GOLD_PALE, gap)
        y += f.get_height() + S(4)
        for cells, col, _v in rows:
            self._blit_table_row(f, cells, widths, bx + S(10), y, col, gap)
            y += row_h
        hint = self.font_sm.render("[ F2 ]  View All-Time Top 100", True, FP.HINT_TEXT)
        self.screen.blit(hint, (bx + bw // 2 - hint.get_width() // 2, y + S(4)))

    def _draw_leaderboard_kit(self, entries):
        self._lb_entries = entries
        f = self.font_sm
        rect, widths, gap, row_h = self._leaderboard_rect(len(entries))
        draw_dark_panel(self.screen, rect, border_color=FP.GOLD)
        hr = draw_header_bar(self.screen, (rect.x, rect.y, rect.w, S(40)),
                             text="TOP RUNS", font=get_font('heading', 22),
                             text_color=FP.GOLD_BRIGHT, accent=FP.GOLD,
                             frame=(rect, FP.GOLD))
        b = panel_band('panel', rect)
        x = rect.x + b + S(14)
        inner_w = rect.w - 2 * (b + S(14))
        y = hr.bottom + S(10)
        self._blit_table_row(f, self._LB_HEADER, widths, x, y, KT.TEXT_SUB, gap)
        y += f.get_height() + S(3)
        pygame.draw.line(self.screen, KT.GOLD_DARK, (x, y), (x + inner_w, y))
        y += S(3)
        rows = self._score_table(entries, f)
        for i, (cells, col, _v) in enumerate(rows):
            self._blit_table_row(f, cells, widths, x, y, col, gap,
                                 colors=[KT.TEXT_DIM, col, KT.TEXT_DIM, col, KT.TEXT_SUB])
            y += row_h
        y += S(6)
        if any(v for _c, _col, v in rows):
            leg = f.render("Gold: brought back the Stone", True, FP.GOLD_BRIGHT)
            self.screen.blit(leg, (rect.centerx - leg.get_width() // 2, y))
        kh = key_hints_height()
        draw_key_hints(self.screen, (x, rect.bottom - b - S(8) - kh, inner_w, kh),
                       "F2: all-time top 100")

    _AT_HEADER = ("#", "Name", "Floor", "Score", "Grade", "Date")

    def _draw_alltime(self):
        """The all-time high scores: a table sized to its rows (one to three
        columns of runs, as many as the window fits), paged with Up/Down
        when there are more runs than fit (it used to be 12 px text in a
        full-window panel, mostly empty)."""
        try:
            from highscore_system import get_top
            entries = get_top(100)
        except Exception:
            entries = []

        W, H = self.W, self.H
        draw_overlay(self.screen, alpha=220)
        kit = kit_on()
        f = self.font_sm
        rows = self._score_table(entries, f, date=True)
        widths = self._table_widths(self._AT_HEADER, rows, f)
        gap = S(16)
        col_w = sum(widths) + gap * (len(widths) - 1)
        col_gap = S(40)
        row_h = f.get_height() + S(4)
        b = S(16) if kit else 0
        pad = S(28)
        header_h = S(48)
        kh = key_hints_height()
        chrome_h = 2 * b + header_h + S(14) + (f.get_height() + S(8)) + S(16) + S(32) + kh + S(10)
        max_rows = max(1, (H - S(48) - chrome_h) // row_h)
        max_cols = max(1, (W - S(48) - 2 * (b + pad) + col_gap) // (col_w + col_gap))
        n = max(1, len(rows))
        ncols = max(1, min(max_cols, 3, -(-n // max_rows)))
        per_col = min(max_rows, -(-n // ncols))
        per_page = per_col * ncols
        pages = max(1, -(-len(rows) // per_page))
        self._alltime_pages = pages
        page = min(getattr(self, '_alltime_page', 0), pages - 1)
        bw = max(S(520), ncols * col_w + (ncols - 1) * col_gap + 2 * (b + pad))
        bh = chrome_h + per_col * row_h
        bx, by = (W - bw) // 2, (H - bh) // 2
        draw_dark_panel(self.screen, (bx, by, bw, bh), border_color=FP.GOLD)
        hr = draw_header_bar(self.screen, (bx, by, bw, header_h),
                             text="ALL-TIME HIGH SCORES",
                             font=get_font('heading', 28) if kit else self.font_md,
                             text_color=FP.GOLD_BRIGHT,
                             accent=FP.GOLD, frame=((bx, by, bw, bh), FP.GOLD))
        top = hr.bottom + S(14)
        x0 = bx + b + pad
        inner_w = bw - 2 * (b + pad)
        tw = ncols * col_w + (ncols - 1) * col_gap
        x0 += (inner_w - tw) // 2
        chunk = rows[page * per_page:(page + 1) * per_page]
        for c in range(ncols):
            part = chunk[c * per_col:(c + 1) * per_col]
            if not part and c:
                break
            cx = x0 + c * (col_w + col_gap)
            self._blit_table_row(f, self._AT_HEADER, widths, cx, top,
                                 KT.TEXT_SUB if kit else FP.GOLD_PALE, gap)
            ly = top + f.get_height() + S(3)
            pygame.draw.line(self.screen, KT.GOLD_DARK if kit else FP.GOLD_DARK,
                             (cx, ly), (cx + col_w, ly))
            y = ly + S(5)
            for cells, col, _v in part:
                self._blit_table_row(f, cells, widths, cx, y, col, gap,
                                     colors=[FP.FADED_TEXT, col, FP.FADED_TEXT, col,
                                             FP.GOLD_PALE, FP.FADED_TEXT])
                y += row_h
        if not rows:
            ns = f.render("No runs recorded yet.", True, FP.FADED_TEXT)
            self.screen.blit(ns, (bx + (bw - ns.get_width()) // 2, top + S(30)))
        foot_y = by + bh - b - S(8) - kh
        note = "Gold: brought back the Stone"
        if pages > 1:
            note += f"     Page {page + 1} of {pages}"
        ns = f.render(note, True, FP.GOLD_BRIGHT)
        self.screen.blit(ns, (bx + (bw - ns.get_width()) // 2, foot_y - S(26) - ns.get_height()))
        if kit:
            draw_divider(self.screen, bx + b + S(28), foot_y - S(14), bw - 2 * (b + S(28)))
        hints = [("\u2191/\u2193", "Page"), ("Any Key", "Close")] if pages > 1 else [("Any Key", "Close")]
        draw_key_hints(self.screen, (bx + b + S(16), foot_y, bw - 2 * (b + S(16)), kh), hints)
