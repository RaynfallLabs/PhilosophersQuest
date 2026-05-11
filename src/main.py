import os
import random
import sys

import pygame

# FANTASY: get_font is the only fantasy_ui name still consumed by main.py;
# every other UI helper is used exclusively from game_render.RenderMixin.
from fantasy_ui import get_font

from combat import player_attack
from pet_system import Pet, FenrirPet, random_species as random_pet_species
from quirk_system import QuirkSystem
from container_system import attempt_lockpick
from dungeon import (spawn_monsters, WALL, FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR,
                     ALTAR, WATER, LAVA, FOUNTAIN, GRAVE, THRONE, ICE)
from food_system import harvest_corpse, cook_ingredient, cook_compound_recipe
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient, Artifact, Container, Lockpick, Accessory, Wand, Scroll, Spellbook, Ammo, Food, Potion
from level_manager import LevelManager
from player import Player
import sound_system as _snd
from quiz_engine import QuizEngine, QuizMode, QuizState
from renderer import Renderer
from ui import Sidebar, MessageLog
from game_helpers import (
    migrate_buc_item, cycle_tab, throw_crosses_tile, wand_tier_duration,
    fix_name_case, a_or_an,
)
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_EQUIP_MENU, STATE_ACCESSORY_MENU,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_CONFIRM_EXIT, STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
    STATE_VICTORY, STATE_DEAD, STATE_REVIEW_MISSED,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
    STATE_SPELL_MENU, STATE_HINT, STATE_EXAMINE,
    STATE_ENCYCLOPEDIA, STATE_DROP_MENU, STATE_DROP_GOLD_INPUT,
    STATE_STORY_POPUP, STATE_MYSTERY_APPROACH, STATE_SHOP, STATE_POWER_MENU,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM,
    STATE_THROW_MENU, STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_JUDGMENT, STATE_STUDY,
)
from welcome_screen import WelcomeScreen
from study_mode import StudyMode
import layout
from layout import VERSION, FPS
from game_render import RenderMixin
from game_menus import MenuMixin
from spells import LEARNABLE_SPELLS


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------




class Game(MenuMixin, RenderMixin):
    def __init__(self, screen: pygame.Surface,
                 player_name: str = 'Adventurer',
                 secret_build: dict | None = None):
        self.screen        = screen
        self.player_name   = player_name
        self.secret_build  = secret_build   # dict of stat overrides, or None
        # FANTASY: Grimoire font set -- larger for readability
        self.font_sm   = get_font('body',    20)
        self.font_md   = get_font('body',    26)
        self.font_lg   = get_font('heading', 32)
        self.font_xl   = get_font('title',   42, bold=True)

        _snd.init()   # initialise procedural sound synthesis (best-effort)
        self.quiz_engine        = QuizEngine()
        self.msg_log            = MessageLog()
        self.sidebar            = Sidebar(screen, layout.GAME_W)
        self.level_mgr          = LevelManager()
        self.state              = STATE_PLAYER
        self.combat_target      = None
        self.quiz_title         = ''
        self.equip_menu_items: list      = []
        self.equip_menu_equipped: list   = []   # (slot_name, item) pairs for unequip section
        self._menu_tab: int              = 0    # current tab index for tabbed menus
        self._menu_page: int             = 0    # page offset for paginated menus
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
        self._cook_tab: int              = 0
        self._menu_sprite_cache: dict    = {}   # item_id -> Surface|None at MENU_ICON_SIZE
        self._examine_tab: int           = 0
        self._eat_tab: int               = 0
        self._scroll_tab: int            = 0
        self._throw_tab: int             = 0
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
        # Secret cow level state
        self._cow_poke_count: int = 0        # poke counter for the cow NPC
        self._cow_level_done: bool = False   # True once cow level completed
        self._cow_spawned: bool = False       # True once cow placed this run
        self._cow_return_level: int = 0       # level to return to from cow level
        self._cow_npc = None                  # reference to the cow monster entity
        self._cow_level: int = _lore_rng.randint(30, 39)  # which floor gets the cow
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
        self.missed_questions: list = []   # [{subject, question, correct, chosen}]
        self._score_saved       = False    # True after high score is written
        self.quiz_engine.on_answer = self._on_quiz_answer
        self.quirk_system = QuirkSystem(self)
        self._slow_skip         = False    # toggled each turn when slowed
        # Key-held movement (arrow key auto-repeat)
        self._move_hold_timer   = 0.0      # countdown until next repeated move
        self._move_hold_delay   = 0.18     # seconds before repeat kicks in
        self._move_hold_first   = True     # True = waiting for initial delay
        # Targeting state (ranged and melee attacks)
        self.target_cursor_x    = 0        # world tile position of targeting cursor
        self.target_cursor_y    = 0
        self._target_candidates: list = [] # visible monsters sorted by distance
        self._target_idx        = 0        # which candidate is selected
        self._melee_targeting   = False    # True when using A-key melee targeting
        self._throw_targeting   = False    # True when throwing a potion
        self._observe_targeting = False    # True when using O-key observe
        self._wand_targeting    = False    # True when aiming a combat wand
        self._pending_wand      = None     # Wand being aimed
        self._throw_potion      = None     # Potion being thrown
        self._throw_reach       = 0        # Throw range based on STR
        # Map view toggle: 'full' = fit entire dungeon, 'close' = scrolling close-up
        self.zoom_mode          = 'full'
        # Debug overlay (F2)
        self._debug_overlay     = False
        # Chronicle, Lore Hints, & Discovered Recipes (Encyclopedia tabs)
        self._chronicle: list[str]       = []   # event log: "Found: Bronze Bull Idol (L8)"
        self._recalled_hints: list[str]  = []   # saved Recall Lore results
        self._cooked_recipes: list[str]  = []   # recipe names successfully cooked
        # Pet companion system (Soul Spheres)
        self.pets: list[Pet]    = []       # active pet companions, persist across floors
        # Mystery system state
        self._active_mystery_altar = None  # MysteryAltar being interacted with
        # Abaddon quest state
        self.seals_broken: set = set()     # set of seal artifact IDs collected
        self.abaddon_resist_removed_turns: int = 0  # turns Abaddon's resistances are stripped
        self.heavenly_host_active: bool = False      # Scales of Michael activated
        self._l100_altars_used: set = set()          # (x,y) of altars already prayed at on L100
        # Morality / NPC encounter system
        self.karma: int = 0                # cumulative moral score (-10 to +10)
        self._npc_encounter_levels: dict = {}  # {level: encounter_def} for this run
        self._npc_encounter_active = None  # current encounter dict being displayed
        self._npc_encounter_monster = None # monster entity for current NPC
        self._encountered_npcs: set = set() # tags of NPCs already encountered
        self._judgment_text: str = ''      # narrative text for judgment result
        self._npc_encounter_phase: str = 'text'   # 'text', 'options', 'select_item', 'outcome'
        self._npc_selected_option: dict | None = None  # option dict chosen by player
        self._npc_outcome_text: str = ''           # outcome text to display
        self._npc_item_list: list = []             # filtered inventory for item selection
        self._npc_item_scroll: int = 0             # scroll offset for item list
        self._npc_triggered_items: set = set()     # item IDs of trigger items player has picked up
        self.player_title: str = ''                # 'Paladin' etc. from judgment
        # Pre-select NPC encounter levels for this run
        from npc_encounters import select_encounter_levels, get_trigger_item_levels
        self._npc_encounter_levels = select_encounter_levels()
        self._npc_trigger_item_levels: dict = get_trigger_item_levels(self._npc_encounter_levels)
        self._npc_trigger_items_placed: set = set()  # item IDs already spawned as floor loot
        # Flavor (non-karmic) encounters
        from flavor_encounters import select_flavor_encounters
        self._flavor_encounter_levels: dict = select_flavor_encounters()
        self._encountered_flavor_npcs: set = set()

        self._new_level(1)
        self._show_story_popup('dungeon_entrance', STATE_PLAYER)

    # ------------------------------------------------------------------
    # Message helper
    # ------------------------------------------------------------------

    def add_message(self, text: str, msg_type: str = 'info'):
        self.msg_log.add(text, msg_type)

    def _log_chronicle(self, text: str):
        """Add an entry to the player's chronicle (passive event log)."""
        entry = f"{text} (L{self.dungeon_level})"
        self._chronicle.append(entry)

    # ------------------------------------------------------------------
    # Level setup
    # ------------------------------------------------------------------

    def _new_level(self, level: int):
        """Initial game setup only -- creates fresh player."""
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
            # Recompute derived stats after overrides (STR->max_sp, CON->max_hp, INT->max_mp)
            self.player.max_hp = self.player.BASE_HP + self.player.CON
            self.player.hp     = self.player.max_hp
            self.player.max_sp = self.player.BASE_SP + self.player.STR
            self.player.sp     = self.player.max_sp
            self.player.max_mp = self.player.BASE_MP + self.player.INT
            self.player.mp     = self.player.max_mp

        # Immortality flag
        self.player.immortal = bool(b.get('_immortal', False))
        # Chronicle: secret build
        if self.secret_build:
            bname = self.secret_build.get('_name', self.player_name)
            self._log_chronicle(f"My name is {bname}. I know things others don't. This changes everything.")

        self.player.x, self.player.y = dungeon.rooms[0].center
        self.renderer                = Renderer(self.screen, layout.VIEWPORT_W, layout.VIEWPORT_H)
        self.renderer.set_dungeon(dungeon.width, dungeon.height, layout.GAME_W, layout.GAME_H)
        self._refresh_fov()

        # Spawn trigger items and NPC for moral encounters on L1 (if assigned)
        self._maybe_spawn_trigger_item(level)
        self._maybe_spawn_npc(level)
        self._maybe_spawn_flavor_npc(level)
        self._maybe_spawn_magic_carrot(level)
        self._maybe_spawn_unicorn(level)

        # Give the player their Philosopher's Shard and build-specific starting kit
        self._give_starting_kit()

        # Greeting
        if b.get('_greeting'):
            self.add_message(b['_greeting'], 'success')
        else:
            self.add_message(f"Welcome, {self.player_name}!", 'success')
        self.add_message("Find the Philosopher's Stone and escape!", 'info')
        # Chronicle: entering the dungeon
        self._log_chronicle("Descended into the dungeon. The air smells like dust and old stone. The Stone is somewhere below. I need to find it and get back out.")

    def load_state(self, state: dict):
        """Restore all game state from a previously saved dict (pickle)."""
        self.player        = state['player']
        # Save compat: old saves lack ranged_weapon slot
        if not hasattr(self.player, 'ranged_weapon'):
            self.player.ranged_weapon = None
        if not hasattr(self.player, 'hack_tiers_claimed'):
            self.player.hack_tiers_claimed = set()
        # Compat: fields added after initial release
        if not hasattr(self.player, 'quirk_progress'):
            self.player.quirk_progress = {}
        if not hasattr(self.player, 'unlocked_quirks'):
            self.player.unlocked_quirks = set()
        if not hasattr(self.player, 'quiz_timer_bonuses'):
            self.player.quiz_timer_bonuses = {}
        if not hasattr(self.player, 'power_cooldowns'):
            self.player.power_cooldowns = {}
        if not hasattr(self.player, 'power_uses'):
            self.player.power_uses = {}
        if not hasattr(self.player, 'cooking_hp_gained'):
            self.player.cooking_hp_gained = 0
        if not hasattr(self.player, 'known_spells'):
            self.player.known_spells = {}
        if not hasattr(self.player, 'lockpick_charges'):
            self.player.lockpick_charges = 0
        # BUC migration: patch buc/buc_known on all items from old saves
        self._migrate_buc_all(state)
        self.player_name   = state['player_name']
        self.secret_build  = state.get('secret_build')
        self.turn_count    = state['turn_count']
        self.dungeon_level = state['dungeon_level']
        self.player_gold   = state['player_gold']
        self.level_mgr     = state['level_mgr']
        self.dungeon       = state['dungeon']
        if not hasattr(self.dungeon, 'pits'):
            self.dungeon.pits = set()
        self.monsters      = state['monsters']
        self.ground_items  = state['ground_items']
        self.correct_answers = state.get('correct_answers', 0)
        self.wrong_answers   = state.get('wrong_answers', 0)
        self.missed_questions = state.get('missed_questions', [])
        self.pets            = state.get('pets', [])
        # Abaddon quest state
        self.seals_broken   = state.get('seals_broken', set())
        self.heavenly_host_active = state.get('heavenly_host_active', False)
        self.abaddon_resist_removed_turns = state.get('abaddon_resist_removed_turns', 0)
        self._l100_altars_used = state.get('_l100_altars_used', set())
        # Morality system
        self.karma = state.get('karma', 0)
        self._npc_encounter_levels = state.get('_npc_encounter_levels', {})
        self._encountered_npcs = state.get('_encountered_npcs', set())
        self._flavor_encounter_levels = state.get('_flavor_encounter_levels',
                                                   getattr(self, '_flavor_encounter_levels', {}))
        self._encountered_flavor_npcs = state.get('_encountered_flavor_npcs', set())
        self._abaddon_empowered = state.get('_abaddon_empowered', False)
        self._locusts_strengthened = state.get('_locusts_strengthened', False)
        if state.get('_judgment_resolved', False):
            self._judgment_resolved = True
        self._npc_triggered_items = state.get('_npc_triggered_items', set())
        self._npc_trigger_item_levels = state.get('_npc_trigger_item_levels', {})
        self._npc_trigger_items_placed = state.get('_npc_trigger_items_placed', set())
        self.player_title = state.get('player_title', '')
        # Ascent / Death Pursuer state
        self.death_pursues = state.get('death_pursues', False)
        self.death_monster = state.get('death_monster', None)
        # Deep-lore item spawn tracking
        if '_lore_levels' in state:
            self._lore_levels = state['_lore_levels']
        self._lore_placed = state.get('_lore_placed', set())
        # Quirk system
        if state.get('quirk_system') is not None:
            self.quirk_system = state['quirk_system']
            self.quirk_system.game = self  # re-bind game reference
        # Secret cow level
        self._cow_poke_count = state.get('_cow_poke_count', 0)
        self._cow_level_done = state.get('_cow_level_done', False)
        self._cow_spawned = state.get('_cow_spawned', False)
        self._cow_level = state.get('_cow_level', 35)
        # Chronicle & Lore Hints
        self._chronicle = state.get('_chronicle', [])
        self._recalled_hints = state.get('_recalled_hints', [])
        self._cooked_recipes = state.get('_cooked_recipes', [])
        # Quiz deck state — restore shuffle positions so questions don't repeat on reload
        quiz_deck_state = state.get('quiz_deck_state')
        if quiz_deck_state:
            self.quiz_engine.restore_deck_state(quiz_deck_state)
        self.renderer.set_dungeon(self.dungeon.width, self.dungeon.height, layout.GAME_W, layout.GAME_H)
        self._refresh_fov()
        self.add_message("Welcome back, seeker. Your journey continues...", 'success')

    _migrate_buc_item = staticmethod(migrate_buc_item)

    def _migrate_buc_all(self, state: dict):
        """Walk every item in inventory, equipment, ground, and stored levels."""
        migrate = self._migrate_buc_item
        # Player inventory
        for item in getattr(self.player, 'inventory', []):
            migrate(item)
        # Equipped slots
        for slot_item in [self.player.weapon, self.player.ranged_weapon, self.player.shield]:
            if slot_item:
                migrate(slot_item)
        for s in getattr(self.player, 'armor_slots', []):
            if s:
                migrate(s)
        for s in getattr(self.player, 'accessory_slots', []):
            if s:
                migrate(s)
        amulet = getattr(self.player, 'amulet_slot', None)
        if amulet:
            migrate(amulet)
        # Ground items
        for item in state.get('ground_items', []):
            migrate(item)
        # Stored levels in level_mgr
        lm = state.get('level_mgr')
        if lm:
            for lvl_data in getattr(lm, 'levels', {}).values():
                for item in lvl_data.get('ground_items', []):
                    migrate(item)

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
        # Chronicle: level milestones and maze entries
        _MILESTONE_FLAVOR = {
            10: "Level 10. The tunnels twist into a maze. Someone built this to confuse.",
            20: "Level 20. The air is heavier down here. I can hear something large breathing.",
            30: "Level 30. A maze again. The walls feel like they're watching me.",
            40: "Level 40. Halfway to madness, or halfway to the Stone. Hard to tell the difference.",
            50: "Level 50. Another maze. I'm starting to think these aren't natural.",
            60: "Level 60. The stone itself is warm. Something ancient lives at these depths.",
            70: "Level 70. Maze. The walls here are carved with warnings in dead languages.",
            80: "Level 80. The darkness has texture. I can feel it pressing against my skin.",
            90: "Level 90. One last maze. The floor trembles. I'm close to the end, one way or another.",
            100: "Level 100. The deepest place in the world. Whatever waits here, I'm ready. I have to be.",
        }
        if new_level in _MILESTONE_FLAVOR:
            self._log_chronicle(_MILESTONE_FLAVOR[new_level])
        # Bones ghost notification
        ghost_name = getattr(dungeon, 'bones_ghost_name', None)
        if ghost_name:
            self.add_message(f"You sense a restless presence... the {ghost_name} haunts this floor.", 'danger')
            self._log_chronicle(f"Encountered the {ghost_name}. A chill ran through me.")
        self.renderer.set_dungeon(dungeon.width, dungeon.height, layout.GAME_W, layout.GAME_H)

        # Spawn trigger items and NPCs for moral encounters (only on first visit)
        if not saved:
            self._maybe_spawn_trigger_item(new_level)
            self._maybe_spawn_npc(new_level)
            self._maybe_spawn_flavor_npc(new_level)
            self._maybe_spawn_magic_carrot(new_level)
            self._maybe_spawn_unicorn(new_level)
            self._maybe_spawn_cow(new_level)
        else:
            # Revisit: spawn triggered NPCs if player now has the trigger item
            # (handles the case where player missed the item on first pass)
            self._maybe_spawn_npc(new_level)

        # Reset per-floor artifact states
        self._first_hit_used = False    # Babr-e Bayan
        self._death_save_used = False   # Jade Cicada
        self._quiz_reroll_used = False  # Tablet of Destinies
        self._tarnhelm_used = False     # Tarnhelm

        # Abaddon empowered by negative karma: boost HP on first entry to L100
        if new_level == 100 and not saved and getattr(self, '_abaddon_empowered', False):
            for m in self.monsters:
                if m.kind == 'abaddon_destroyer' and m.alive:
                    bonus = int(m.max_hp * 0.5)
                    m.max_hp += bonus
                    m.hp += bonus
                    self.add_message(
                        "Your sins have given the Destroyer terrible strength!", 'danger')
                    break

        # Track levels without Philosopher's Shard (Diogenes quirk)
        has_shard = any(getattr(i, 'id', '') == 'philosophers_shard'
                        for i in self.player.inventory)
        if not has_shard and self.player.quirk_progress.get('shard_dropped'):
            self.player.quirk_progress['levels_without_shard'] = (
                self.player.quirk_progress.get('levels_without_shard', 0) + 1
            )
        elif has_shard:
            # Reset if they picked it back up
            self.player.quirk_progress['shard_dropped'] = False
            self.player.quirk_progress['levels_without_shard'] = 0

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

        # Grant HP on every level transition (reduced on ascent)
        self.player.on_level_change(ascending=not enter_from_top)

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

        # Reposition pets near player on floor change (spread to adjacent tiles)
        _pet_placed = set()
        for pet in self.pets:
            if not pet.alive:
                continue
            placed = False
            for dx in range(0, 3):
                for dy in range(0, 3):
                    for sx, sy in [(dx, dy), (-dx, dy), (dx, -dy), (-dx, -dy)]:
                        nx, ny = self.player.x + sx, self.player.y + sy
                        if (nx, ny) in _pet_placed:
                            continue
                        if (nx, ny) == (self.player.x, self.player.y):
                            continue
                        if dungeon.is_walkable(nx, ny) and \
                           not any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                            pet.x, pet.y = nx, ny
                            _pet_placed.add((nx, ny))
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if not placed:
                pet.x, pet.y = self.player.x, self.player.y

        # Death always enters from the stairs below when pursuing
        if self.death_pursues and self.death_monster is not None:
            self._maybe_escalate_death()
            self._place_death_on_level(dungeon)
            self.add_message("You hear the scrape of a scythe on stone below you...", 'danger')

        # Special room extra spawns (first visit only)
        if not saved:
            for (rcx, rcy), rtype in dungeon.special_rooms.items():
                if rtype == 'zoo':
                    for room in dungeon.rooms:
                        if room.center == (rcx, rcy):
                            zoo_extra = spawn_monsters([room], new_level, dungeon, min_count=4, max_count=8)
                            for zm in zoo_extra:
                                zm.add_effect('sleeping', 999)
                            monsters.extend(zoo_extra)
                            break
                elif rtype == 'graveyard':
                    for room in dungeon.rooms:
                        if room.center == (rcx, rcy):
                            grave_extra = spawn_monsters([room], new_level, dungeon, min_count=2, max_count=4)
                            for gm in grave_extra:
                                gm.add_effect('sleeping', 999)
                            monsters.extend(grave_extra)
                            break
                elif rtype == 'barracks':
                    for room in dungeon.rooms:
                        if room.center == (rcx, rcy):
                            bar_extra = spawn_monsters([room], new_level, dungeon, min_count=3, max_count=5)
                            for bm in bar_extra:
                                bm.add_effect('sleeping', 999)
                            monsters.extend(bar_extra)
                            break

        self._refresh_fov()

        # Display atmospheric messages for this level
        for atmo_msg in getattr(self.dungeon, 'atmosphere_messages', []):
            self.add_message(atmo_msg, 'info')

    def _give_starting_kit(self):
        """Give the player their starting kit, adjusted for their secret build."""
        from items import load_items, Item
        b = self.secret_build or {}

        # -- Always: Philosopher's Shard ------------------------------------
        shard = Item({
            'id': 'philosophers_shard',
            'name': "Philosopher's Shard",
            'symbol': '*',
            'color': [220, 200, 120],
            'weight': 0.1,
            'item_class': 'shard',
            'min_level': 1,
            'lore': "A tiny fragment of the Philosopher's Stone, warm to the touch and faintly luminous. It resonates with philosophical understanding, allowing its bearer to perceive the true nature of unknown items through rigorous examination. Ancient texts warn that those who abandon it walk blind through the dungeon — but some say that blindness teaches its own kind of wisdom.",
        })
        shard.identified = True
        self.player.inventory.append(shard)
        self.player.known_item_ids.add('philosophers_shard')

        # -- Weapon: default dagger OR build override ----------------------
        no_dagger     = b.get('_no_dagger', False)
        start_weapon  = b.get('_start_weapon', None)
        try:
            weapons = load_items('weapon')
            if start_weapon:
                w = next((x for x in weapons if x.id == start_weapon), None)
                if w:
                    w.identified = True
                    self.player.known_item_ids.add(w.id)
                    self.player.inventory.append(w)
            elif not no_dagger:
                sword = next((x for x in weapons if x.id == 'iron_sword'), None)
                if sword:
                    self.player.known_item_ids.add(sword.id)
                    self.player.inventory.append(sword)
        except Exception:
            pass

        # -- Ammo (rangers) ------------------------------------------------
        start_ammo = b.get('_start_ammo', None)
        if start_ammo:
            try:
                ammo_items = load_items('ammo')
                ammo = next((a for a in ammo_items if a.id == start_ammo), None)
                if ammo:
                    ammo.count = 20
                    self.player.known_item_ids.add(ammo.id)
                    self.player.inventory.append(ammo)
            except Exception:
                pass

        # -- Secondary melee weapon (rangers with bows) ----------------------
        start_melee = b.get('_start_melee', None)
        if start_melee:
            try:
                melee_w = next((x for x in weapons if x.id == start_melee), None)
                if melee_w:
                    melee_w.identified = True
                    self.player.known_item_ids.add(melee_w.id)
                    if b.get('_lock_melee'):
                        # Auto-equip and lock (can't be removed)
                        melee_w.cursed = True
                        self.player.weapon = melee_w
                    else:
                        self.player.inventory.append(melee_w)
            except Exception:
                pass

        # -- Wand (mages/wizards) ------------------------------------------
        start_wand = b.get('_start_wand', None)
        if start_wand:
            try:
                wands = load_items('wand')
                wand = next((w for w in wands if w.id == start_wand), None)
                if wand:
                    wand.identified = True
                    self.player.known_item_ids.add(wand.id)
                    self.player.inventory.append(wand)
            except Exception:
                pass

        # -- Spellbook (mages/wizards) -------------------------------------
        start_book = b.get('_start_book', None)
        if start_book:
            try:
                books = load_items('spellbook')
                book = next((bk for bk in books if bk.id == start_book), None)
                if book:
                    book.identified = True
                    self.player.known_item_ids.add(book.id)
                    self.player.inventory.append(book)
            except Exception:
                pass

        # -- Shield (warriors) ---------------------------------------------
        start_shield = b.get('_start_shield', None)
        if start_shield:
            try:
                shields = load_items('shield')
                sh = next((s for s in shields if s.id == start_shield), None)
                if sh:
                    sh.identified = True
                    self.player.known_item_ids.add(sh.id)
                    self.player.inventory.append(sh)
            except Exception:
                pass

        # -- Accessory (rings/amulets) ------------------------------------
        start_acc = b.get('_start_accessory', None)
        if start_acc:
            try:
                accs = load_items('accessory')
                acc = next((a for a in accs if a.id == start_acc), None)
                if acc:
                    acc.identified = True
                    self.player.known_item_ids.add(acc.id)
                    self.player.inventory.append(acc)
            except Exception:
                pass

        # -- Extra accessories (inventory-only items like Charmander Stuffie) --
        extra_acc_ids = b.get('_start_extra_acc', [])
        if extra_acc_ids:
            try:
                all_accs = load_items('accessory')
                for eid in extra_acc_ids:
                    ea = next((a for a in all_accs if a.id == eid), None)
                    if ea:
                        ea.identified = True
                        self.player.known_item_ids.add(ea.id)
                        self.player.inventory.append(ea)
            except Exception:
                pass

        # -- Armor (headgear, etc.) -----------------------------------------
        start_armor = b.get('_start_armor', None)
        if start_armor:
            try:
                armors = load_items('armor')
                arm = next((a for a in armors if a.id == start_armor), None)
                if arm:
                    arm.identified = True
                    self.player.known_item_ids.add(arm.id)
                    if b.get('_equip_armor'):
                        from items import ARMOR_SLOTS
                        idx = ARMOR_SLOTS.index(arm.slot) if arm.slot in ARMOR_SLOTS else 0
                        self.player.armor_slots[idx] = arm
                    else:
                        self.player.inventory.append(arm)
            except Exception:
                pass

        # -- Soul Spheres ---------------------------------------------------
        soul_sphere_count = b.get('_start_soul_spheres', 0)
        if soul_sphere_count > 0:
            from items import Artifact
            for _ in range(soul_sphere_count):
                sphere = Artifact({
                    'id': 'soul_sphere',
                    'name': 'Soul Sphere',
                    'symbol': 'O',
                    'color': [255, 80, 80],
                    'item_class': 'artifact',
                    'weight': 0.5,
                    'min_level': 1,
                    'lore': 'A sphere of crimson and ivory that hums with trapped souls. '
                            'Ancient texts say these vessels were used to bind creature spirits. '
                            'One wonders what might happen if it were hurled with force...',
                })
                sphere.identified = True
                self.player.known_item_ids.add('soul_sphere')
                self.player.inventory.append(sphere)

        # -- Unusual Soul Sphere (family builds only) -------------------------
        if b.get('_start_unusual_sphere'):
            from items import Artifact
            usphere = Artifact({
                'id': 'unusual_soul_sphere',
                'name': 'Unusual Soul Sphere',
                'symbol': 'O',
                'color': [180, 180, 200],
                'item_class': 'artifact',
                'weight': 0.5,
                'min_level': 999,
                'lore': "An unusual soul sphere. Its colors are black and silver. "
                        "It pulses with a powerful energy...",
            })
            usphere.identified = True
            self.player.known_item_ids.add('unusual_soul_sphere')
            self.player.inventory.append(usphere)

        # -- Pre-learned spells (Witcher Signs, Elder Blood) ----------------
        start_spells = b.get('_start_spells', [])
        for spell_id in start_spells:
            spell = LEARNABLE_SPELLS.get(spell_id)
            if spell:
                self.player.known_spells[spell_id] = spell['mp_cost']

        # -- Extra starting potions ------------------------------------------
        start_potions = b.get('_start_potions', [])
        if start_potions:
            try:
                all_pots = load_items('potion')
                for pid in start_potions:
                    pot = next((p for p in all_pots if p.id == pid), None)
                    if pot:
                        import copy
                        p = copy.copy(pot)
                        p.identified = True
                        self.player.known_item_ids.add(p.id)
                        self.player.add_to_inventory(p)
            except Exception:
                pass

        # -- Always: starting lockpick charges ----------------------------
        self.player.lockpick_charges += 5   # equivalent to one basic lockpick

        # -- Always: bread ration ------------------------------------------
        try:
            foods = load_items('food')
            ration = next((f for f in foods if f.id == 'bread_ration'), None)
            if ration:
                self.player.inventory.append(ration)
        except Exception:
            pass

        # -- Always: healing potion ----------------------------------------
        try:
            potions = load_items('potion')
            heal_pot = next((p for p in potions if p.id == 'potion_of_healing'), None)
            if heal_pot:
                heal_pot.identified = True
                heal_pot.buc_known = True
                self.player.known_item_ids.add(heal_pot.id)
                self.player.inventory.append(heal_pot)
        except Exception:
            pass
        self.player.inventory.sort(key=lambda i: i.name.lower())

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )
        # Palladium: reveal stairs through walls
        _has_palladium = any(getattr(i, 'id', '') == 'palladium' for i in self.player.inventory)
        if _has_palladium:
            from dungeon import STAIRS_UP, STAIRS_DOWN
            for _sy in range(self.dungeon.height):
                for _sx in range(self.dungeon.width):
                    if self.dungeon.tiles[_sy][_sx] in (STAIRS_UP, STAIRS_DOWN):
                        self.dungeon.explored.add((_sx, _sy))
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

        # Dark rooms: restrict visibility to 1 tile radius
        dark_centers = getattr(self.dungeon, 'dark_rooms', set())
        if dark_centers:
            px, py = self.player.x, self.player.y
            in_dark = False
            for room in self.dungeon.rooms:
                cx, cy = room.center
                if (cx, cy) in dark_centers:
                    if (room.x <= px < room.x + room.width and
                            room.y <= py < room.y + room.height):
                        in_dark = True
                        break
            if in_dark and not self.player.has_effect('see_invisible'):
                dark_radius = 1 + max(0, (self.player.PER - 10) // 5)
                self.visible = {
                    (vx, vy) for vx, vy in self.visible
                    if abs(vx - px) <= dark_radius and abs(vy - py) <= dark_radius
                }

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def on_resize(self, w: int, h: int):
        """Called after window is resized -- syncs renderer and sidebar."""
        layout.update(w, h)
        self.renderer.set_dungeon(
            self.dungeon.width, self.dungeon.height, layout.GAME_W, layout.GAME_H
        )
        self.sidebar.x = layout.GAME_W

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
        if key == pygame.K_F2:
            self._debug_overlay = not self._debug_overlay
            return True

        if key == pygame.K_ESCAPE:
            if self.state == STATE_QUIZ:
                # Cancel the active quiz — treat as chain-0 failure
                self.quiz_engine._end(success=False)
                return True
            if self.state in (STATE_EQUIP_MENU, STATE_ACCESSORY_MENU,
                              STATE_WAND_MENU, STATE_SCROLL_MENU,
                              STATE_IDENTIFY_MENU, STATE_COOK_MENU,
                              STATE_CONFIRM_EXIT, STATE_TARGET,
                              STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
                              STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_THROW_MENU,
                              STATE_HELP, STATE_LORE,
                              STATE_SPELL_MENU, STATE_HINT, STATE_HACK_REALITY,
                              STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM, STATE_QUIRKS,
                              STATE_COW_ENCOUNTER,
                              STATE_CHARACTER_SHEET,
                              STATE_EXAMINE, STATE_ENCYCLOPEDIA,
                              STATE_DROP_MENU, STATE_DROP_GOLD_INPUT,
                              STATE_MYSTERY_APPROACH, STATE_SHOP,
                              STATE_POWER_MENU, STATE_STUDY):
                if self.state == STATE_MYSTERY_APPROACH:
                    self._active_mystery_altar = None
                if self.state == STATE_TARGET:
                    self._throw_targeting = False
                    self._throw_potion = None
                    self._observe_targeting = False
                    self._wand_targeting = False
                    self._pending_wand = None
                    self._power_targeting = False
                    self._pending_power = None
                self.state = STATE_PLAYER
                return True
            if self.state == STATE_STORY_POPUP:
                self.state = self.popup_next_state
                return True
            if self.state == STATE_PLAYER:
                self.state = STATE_CONFIRM_EXIT
                return True
            if self.state == STATE_REVIEW_MISSED:
                self.state = STATE_DEAD
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
            if event.unicode == '@':
                self._open_character_sheet()
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
        elif self.state == STATE_THROW_MENU:
            self._throw_menu_input(key)
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
        elif self.state == STATE_HACK_REALITY:
            self.state = STATE_PLAYER   # any key dismisses hack reality overlay
        elif self.state == STATE_XYZZY_INPUT:
            self._xyzzy_input(key, event.unicode)
        elif self.state == STATE_XYZZY_CONFIRM:
            self._xyzzy_confirm_input(key)
        elif self.state == STATE_QUIRKS:
            self._quirks_input(key)
        elif self.state == STATE_COW_ENCOUNTER:
            self._cow_encounter_input(key)
        elif self.state == STATE_CHARACTER_SHEET:
            self._character_sheet_input(key)
        elif self.state == STATE_DROP_MENU:
            self._drop_menu_input(key)
        elif self.state == STATE_DROP_GOLD_INPUT:
            self._drop_gold_input(key, event.unicode)
        elif self.state == STATE_STORY_POPUP:
            self.state = self.popup_next_state   # any key advances
        elif self.state == STATE_CONFIRM_EXIT:
            self._confirm_exit_input(key)
        elif self.state == STATE_EXIT_QUEST:
            self._exit_quest_input(key)
        elif self.state == STATE_ABANDON_QUEST:
            self._abandon_quest_input(key)
        elif self.state == STATE_CHICKEN:
            self._chicken_input(key)
        elif self.state == STATE_MYSTERY_APPROACH:
            self._mystery_approach_input(key, event.unicode)
        elif self.state == STATE_SHOP:
            self._shop_input(key)
        elif self.state == STATE_POWER_MENU:
            self._power_menu_input(key)
        elif self.state == STATE_NPC_ENCOUNTER:
            self._npc_encounter_input(key)
        elif self.state == STATE_JUDGMENT:
            self._judgment_input(key)
        elif self.state == STATE_STUDY:
            self._study_input(key)
        elif self.state == STATE_DEAD:
            if key == pygame.K_r and self.missed_questions:
                self._review_idx = 0
                self.state = STATE_REVIEW_MISSED
        elif self.state == STATE_REVIEW_MISSED:
            if key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_SPACE, pygame.K_RETURN):
                self._review_idx = min(self._review_idx + 1, len(self.missed_questions) - 1)
            elif key in (pygame.K_LEFT, pygame.K_UP):
                self._review_idx = max(0, self._review_idx - 1)

        return True

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
    }

    def _player_input(self, key: int):

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
            # Try disarm trap first, then lockpick container
            if self._try_disarm_trap():
                return
            self._lockpick()
            return
        if key == pygame.K_a:
            self._open_melee_targeting()
            return
        if key == pygame.K_f:
            self._open_targeting()
            return
        if key == pygame.K_t:
            self._open_throw_menu()
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
            tile = self.dungeon.tiles[self.player.y][self.player.x]
            # On a fountain with Bronze Bull: open drop menu so player can offer it
            if tile == FOUNTAIN and any(
                    getattr(i, 'id', '') == 'bronze_bull' for i in self.player.inventory):
                self._open_drop_menu()
            # On an altar with quest items: open drop menu so player can offer
            elif tile == ALTAR and any(
                    getattr(i, 'id', '') in (
                        'eye_of_graeae', 'broken_gram', 'leather_scrap',
                        'cats_footstep', 'womans_beard', 'mountain_root',
                        'fish_breath', 'bird_spittle', 'bear_sinew',
                    )
                    for i in self.player.inventory):
                self._open_drop_menu()
            elif tile in (FOUNTAIN, GRAVE, THRONE):
                self._interact_tile()
            elif tile == ALTAR:
                self._altar_buc_identify()
            else:
                # Adjacent to Odin's Altar with items — allow drop for throw-over
                self._open_drop_menu()
            return
        if key == pygame.K_y:
            self._open_shop()
            return
        if key == pygame.K_v:
            self._open_power_menu()
            return
        if key == pygame.K_BACKQUOTE:
            self._open_xyzzy_input()
            return
        if key == pygame.K_w:
            self._open_quirks_screen()
            return
        if key == pygame.K_o:
            self._start_observe()
            return
        if key == pygame.K_SEMICOLON:
            self._open_study_journal()
            return
        if key == pygame.K_TAB:
            if self.zoom_mode == 'full':
                self.zoom_mode = 'medium'
                self.add_message("Medium view. [Tab] to zoom closer.", 'info')
            elif self.zoom_mode == 'medium':
                self.zoom_mode = 'close'
                self.add_message("Close-up view. [Tab] to zoom out.", 'info')
            else:
                self.zoom_mode = 'full'
                self.add_message("Full map view. [Tab] to zoom in.", 'info')
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

        # Immobilized (bear trap): skip turn
        if self.player.has_effect('immobilized'):
            self.add_message("You're stuck and cannot move!", 'danger')
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
        if self.player.has_effect('fumbling') and random.random() < 0.20:
            self.add_message("You stumble and waste your turn!", 'warning')
            self._advance_turn()
            return

        # Stunned: 25% chance to fail
        if self.player.has_effect('stunned') and random.random() < 0.25:
            self.add_message("You are too dazed to act!", 'warning')
            self._advance_turn()
            return

        # In a pit: movement = climb out (stay in place, costs a turn)
        if self.player.has_effect('in_pit'):
            del self.player.status_effects['in_pit']
            self.add_message("You climb out of the pit.", 'info')
            self._tick_sp()
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
            # Secret cow dialog
            if getattr(target, '_npc_encounter_tag', None) == '_cow_dialog':
                self._start_cow_encounter(target)
                return
            # NPC encounter: open moral choice instead of combat
            if getattr(target, '_npc_encounter_tag', None):
                self._start_npc_encounter(target)
                return
            # Unicorn encounter: multi-step interaction
            if getattr(target, '_is_unicorn', False):
                self._handle_unicorn_bump(target)
                self._advance_turn()
                return
            # Flavor encounter: non-karmic NPC interaction
            if getattr(target, '_flavor_encounter_tag', None):
                self._start_flavor_encounter(target)
                return
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
            if random.random() < per_chance:
                self.dungeon.tiles[ny][nx] = DOOR
                self._refresh_fov()
                self.add_message("You find a secret door!", 'success')
            else:
                self.add_message("You feel something odd about this wall...", 'info')
            self._advance_turn()
        elif self.dungeon.is_walkable(nx, ny) or (
            self.player.has_effect('phasing') and self.dungeon.in_bounds(nx, ny)
            and self.dungeon.tiles[ny][nx] not in (WATER, LAVA)
        ):
            self.player.x, self.player.y = nx, ny
            # Ice sliding: keep moving in the same direction until hitting non-ice
            if self.dungeon.tiles[ny][nx] == ICE and not self.player.has_effect('levitating'):
                # Check trap on entry tile first
                self._check_floor_trap(nx, ny)
                if self.player.is_dead():
                    return
                slide_count = 0
                while slide_count < 5:  # max 5 tiles slide
                    sx, sy = self.player.x + dx, self.player.y + dy
                    if not self.dungeon.in_bounds(sx, sy):
                        break
                    slide_tile = self.dungeon.tiles[sy][sx]
                    if slide_tile in (WATER, LAVA, WALL, DOOR, SECRET_DOOR):
                        break
                    if any(m.alive and m.x == sx and m.y == sy for m in self.monsters):
                        break
                    self.player.x, self.player.y = sx, sy
                    slide_count += 1
                    # Check traps on each intermediate tile
                    self._check_floor_trap(sx, sy)
                    if self.player.is_dead():
                        return
                    if slide_tile != ICE:
                        break
                if slide_count > 0:
                    self.add_message(f"You slide across the ice! ({slide_count} tiles)", 'warning')
            else:
                self._check_floor_trap(self.player.x, self.player.y)
            # Check for dug pits (separate from traps)
            px, py = self.player.x, self.player.y
            if (px, py) in getattr(self.dungeon, 'pits', set()):
                self._player_fall_in_pit(px, py)
                if self.player.is_dead():
                    return
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
                        # Remove the Sisyphus altar from the floor
                        from mystery_system import MysteryAltar
                        sis_altar = next(
                            (i for i in self.ground_items
                             if isinstance(i, MysteryAltar) and i.mystery_id == 'sisyphus'), None
                        )
                        if sis_altar:
                            self.ground_items.remove(sis_altar)
                    elif _sis_tiles % 5 == 0:
                        self.add_message(
                            f"The boulder weighs you down. {25 - _sis_tiles} tiles remain.", 'warning'
                        )
                elif not _has_boulder:
                    self.player.quirk_progress['sisyphus_boulder_active'] = False
            self._refresh_fov()
            self._tick_sp()
            if self.state != STATE_DEAD:
                self._notify_stairs(self.player.x, self.player.y)
                self._notify_ground(self.player.x, self.player.y)
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
            self.add_message("Stairs lead down here  --  press '>' to descend.", 'info')
        elif tile == STAIRS_UP:
            if self.dungeon_level == 1:
                self.add_message("The dungeon exit  --  press '<' to leave.", 'warning')
            else:
                self.add_message("Stairs lead up here  --  press '<' to ascend.", 'info')
        elif tile == ALTAR:
            self.add_message("A sacred altar stands here. Press '\\' to pray with divine bonus.", 'info')
        elif tile == FOUNTAIN:
            self.add_message("A shimmering fountain bubbles here. Press 'D' to drink.", 'info')
        elif tile == GRAVE:
            self.add_message("A weathered gravestone stands here. Press 'D' to dig.", 'info')
        elif tile == THRONE:
            self.add_message("An ancient throne sits here. Press 'D' to sit upon it.", 'info')

    def _notify_ground(self, x: int, y: int):
        """Print messages about items and notable features at (x, y)."""
        # Special room notification (once per room per floor)
        _SPECIAL_ROOM_MSGS = {
            'treasury':    ("You enter a treasure vault -- riches gleam in the darkness!", 'success'),
            'library':     ("You enter an ancient library -- scrolls line the walls.", 'info'),
            'shrine':      ("You enter a sacred shrine -- you feel the presence of higher powers.", 'info'),
            'monster_den': ("You enter a monster den -- the stench of creatures fills the air!", 'danger'),
            'zoo':         ("Welcome to the treasure zoo! Sleeping creatures surround you!", 'danger'),
            'graveyard':   ("The air grows deathly cold. Graves stretch before you...", 'danger'),
            'beehive':     ("A low buzzing fills the air. You've disturbed a hive!", 'danger'),
            'barracks':    ("Soldiers' quarters -- weapons and armor are stacked neatly.", 'info'),
            'swamp':       ("Murky water and marsh gas fill this chamber.", 'warning'),
            'throne_room': ("An aura of ancient authority radiates from a throne.", 'info'),
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
                            _ROOM_CHRONICLE = {
                                'treasury': "Found a treasure vault. Gold everywhere. Someone wanted this hidden.",
                                'library': "Found an ancient library. The scrolls are still intact. Knowledge survives down here.",
                                'graveyard': "Stumbled into an underground graveyard. The dead are restless.",
                            }
                            if rtype in _ROOM_CHRONICLE and not getattr(self, f'_chronicle_room_{rtype}', False):
                                setattr(self, f'_chronicle_room_{rtype}', True)
                                self._log_chronicle(_ROOM_CHRONICLE[rtype])
                            break

        here = [item for item in self.ground_items if item.x == x and item.y == y]
        # Abyssal Shimmer: show the inscription when stepped upon
        shimmer = next((i for i in here if i.id == 'abyssal_shimmer'), None)
        if shimmer:
            if shimmer.activated:
                self.add_message(
                    "The ground roils with abyssal energy -- something is ready.", 'danger'
                )
            else:
                self.add_message("The ground shimmers with ancient power.", 'info')
                self.add_message("\u201cRevelation 20:14\u201d", 'info')
            here = [i for i in here if i is not shimmer]   # don't double-list it
        # Mimic detection: PER check on containers
        from items import Container
        for item in here:
            if isinstance(item, Container) and getattr(item, 'is_mimic', False):
                import random as _prng
                per_chance = min(0.80, 0.10 + self.player.PER * 0.04)
                if _prng.random() < per_chance:
                    _an = self._a_or_an(item.name)
                    _MIMIC_HINTS = [
                        f"You see {_an} here. Something seems off\u2026 is that a tooth?",
                        f"You see {_an} here. It glistens with what looks like saliva.",
                        f"You see {_an} here. Was that\u2026 breathing?",
                        f"You see {_an} here. The hinges look oddly organic.",
                        f"You see {_an} here. You notice a faint, predatory smell.",
                    ]
                    self.add_message(_prng.choice(_MIMIC_HINTS), 'warning')

        if len(here) == 1:
            item = here[0]
            dname = self._display_name(item)
            article = 'an' if dname[0].lower() in 'aeiou' else 'a'
            self.add_message(f"You see {article} {dname} lying here.", 'info')
            self._show_item_comparison(item)
        elif len(here) == 2:
            self.add_message(
                f"You see {self._display_name(here[0])} and "
                f"{self._display_name(here[1])} lying here.", 'info'
            )
            for h in here:
                self._show_item_comparison(h)
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
        from boss_levels import COW_LEVEL
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_DOWN:
            self.add_message("There are no stairs leading down here.", 'info')
            return
        # Cow level portal: return to the dungeon
        if self.dungeon_level == COW_LEVEL:
            self._exit_cow_level()
            return
        # Seven Seals gate: all 7 must be broken before descending to L100
        if self.dungeon_level == 99 and len(self.seals_broken) < 7:
            remaining = 7 - len(self.seals_broken)
            self.add_message(
                f"Seven seals hold the Pit closed. {remaining} remain unbroken.", 'warning')
            self.add_message(
                "You must slay the seven guardians before the way opens.", 'info')
            return
        try:
            self._change_level(self.dungeon_level + 1, enter_from_top=True)
        except Exception as e:
            self.add_message(f"Error descending: {e}", 'danger')
            import traceback
            traceback.print_exc()

    def _ascend_stairs(self):
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_UP:
            self.add_message("There are no stairs leading up here.", 'info')
            return
        if self.dungeon_level == 1:
            has_stone = any(
                isinstance(i, Artifact) and i.id in ('philosophers_stone',
                                                       'complete_tablet_of_second_death')
                for i in self.player.inventory
            )
            self.state = STATE_EXIT_QUEST if has_stone else STATE_ABANDON_QUEST
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
            try:
                self._change_level(self.dungeon_level - 1, enter_from_top=False)
            except Exception as e:
                self.add_message(f"Error ascending: {e}", 'danger')
                import traceback
                traceback.print_exc()

    def _trigger_death_pursuit(self):
        from monster import DeathMonster
        self.death_pursues  = True
        self.death_monster  = DeathMonster()  # starts at 50% speed
        self.add_message(
            "The dungeon shudders. A bone-cold wind rises from the deep.", 'danger'
        )
        self.add_message(
            "DEATH has come for the Stone.  Flee -- or be reaped.", 'danger'
        )
        self._log_chronicle("Something is following me. I felt it before I saw it. Death itself. I need to run.")

    def _place_death_on_level(self, dungeon):
        """Spawn Death near the down-stairs (rooms[-1]) of the given dungeon."""
        d = self.death_monster
        cx, cy = dungeon.rooms[-1].center
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
        d.x, d.y = cx, cy
        d.alive   = True

    def _maybe_escalate_death(self):
        """Accelerate Death as player ascends: 50% -> 75% -> 100% -> 125% speed."""
        if not self.death_pursues or self.death_monster is None:
            return
        dm = self.death_monster
        if not hasattr(dm, '_speed_pct'):
            dm._speed_pct = 50
        level = self.dungeon_level
        old_speed = dm._speed_pct

        if level <= 25:
            dm._speed_pct = 125
        elif level <= 50:
            dm._speed_pct = 100
        elif level <= 75:
            dm._speed_pct = 75
        else:
            dm._speed_pct = 50

        # Announce speed changes
        if dm._speed_pct != old_speed:
            _SPEED_MSGS = {
                75:  ("Death quickens. The scraping is faster now.", 'danger',
                      "Death is moving faster. The sound of the scythe is closer between each step."),
                100: ("Death matches your pace now. Every step you take, it takes one too.", 'danger',
                      "Death moves as fast as I do now. No more outrunning it. I have to be smarter."),
                125: ("Death is FASTER than you. It's gaining. RUN.", 'danger',
                      "It's faster than me. Faster. I can hear it gaining with every step. I need to pray."),
            }
            msg = _SPEED_MSGS.get(dm._speed_pct)
            if msg:
                self.add_message(msg[0], msg[1])
                self._log_chronicle(msg[2])

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
            complete.x, complete.y = 0, 0   # inventory item -- position doesn't matter
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
            self._log_chronicle("Used the Wrench. The Stone and the Tablet fused into one. The Complete Tablet glows with purpose. I think I know what it's for.")
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

        self.add_message("The ancient words echo through the dungeon...", 'danger')
        self.add_message(
            '"Then Death and Hades were thrown into the lake of fire."', 'danger'
        )
        self.add_message(
            "The Shimmer tears open -- a vast Abyss of black fire yawns beneath Death's feet.", 'danger'
        )
        self.add_message(
            "Death writhes, claws at the stone -- and is consumed.", 'danger'
        )
        self.add_message(
            "What no soul before you has ever achieved:  DEATH IS DEAD.", 'success'
        )
        self.add_message(
            "Take this code to your father proudly -- you have shown true Wisdom and Courage.", 'success'
        )
        self.add_message("\u2605 A scroll materializes from the void. \u2605", 'loot')

        # Destroy Death
        self.death_pursues = False
        self.death_monster = None
        self._log_chronicle("I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard.")

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
        if (dm.x, dm.y) not in self.visible:
            return
        if dist <= 3:
            self.add_message("Death looms over you -- MOVE!", 'danger')
        elif dist <= 6:
            self.add_message("Death draws near.", 'danger')

    def _confirm_exit_input(self, key: int):
        if key in (pygame.K_y, pygame.K_RETURN):
            # Save & exit cleanly -- auto-save runs in main() after the loop
            self._save_on_quit = True
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key == pygame.K_n:
            # Exit without saving -- delete any existing save to prevent checkpointing
            self._save_on_quit = False
            from save_system import delete_save
            delete_save(self.player_name)
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key in (pygame.K_ESCAPE, pygame.K_c):
            self.state = STATE_PLAYER

    def _exit_quest_input(self, key: int):
        """Player has the Stone and is at the L1 exit."""
        if key == pygame.K_y:
            self._do_exit()
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _abandon_quest_input(self, key: int):
        """Player does NOT have the Stone and is at the L1 exit."""
        if key == pygame.K_y:
            self.state = STATE_CHICKEN
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _chicken_input(self, key: int):
        """McFly chicken popup — 1 to flee, 2 to stay and get Flux Capacitor."""
        if key == pygame.K_1:
            # "Yes, I am a coward."
            self.defeat_reason = 'fled'
            self._on_game_over()
            self._show_story_popup('exit_without_stone', STATE_DEAD)
        elif key == pygame.K_2:
            # "Nobody calls me chicken!"
            self.state = STATE_PLAYER
            self._spawn_flux_capacitor()

    def _spawn_flux_capacitor(self):
        """Drop the Flux Capacitor on the ground at the player's feet."""
        flux = Wand({
            'id': 'flux_capacitor',
            'item_class': 'wand',
            'name': 'Flux Capacitor',
            'symbol': 'Y',
            'color': [255, 200, 50],
            'weight': 1.0,
            'min_level': 9999,
            'charges': 1,
            'charges_min': 1,
            'charges_max': 1,
            'max_charges': 1,
            'quiz_tier': 1,
            'quiz_threshold': 1,
            'effect': 'time_stop',
            'power': '10',
            'unidentified_name': 'Flux Capacitor',
            'lore': "A device of impossible origin. Its single charge can freeze "
                    "time itself for 10 turns. Use it wisely -- there are no second chances.",
        })
        flux.identified = True
        flux.x = self.player.x
        flux.y = self.player.y
        self.ground_items.append(flux)
        self.add_message("Something materializes at your feet...", 'loot')

    def _do_exit(self):
        has_stone = any(
            isinstance(i, Artifact) and i.id in ('philosophers_stone',
                                                   'complete_tablet_of_second_death')
            for i in self.player.inventory
        )
        self._on_game_over()
        if has_stone:
            self._log_chronicle("I made it. I climbed back out with the Stone. The sunlight hurt my eyes. I'd forgotten what it looked like.")
            self._show_story_popup('exit_with_stone', STATE_VICTORY)
        else:
            self.defeat_reason = 'fled'
            self._show_story_popup('exit_without_stone', STATE_DEAD)

    def _on_game_over(self):
        """Delete save file on any game-ending event (permadeath).
        Save bones file so ghost can haunt future runs."""
        from save_system import delete_save
        from bones import save_bones
        save_bones(self.player_name, self.dungeon_level,
                   getattr(self, 'defeat_reason', 'died'),
                   self.player, getattr(self, 'player_gold', 0))
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
        if score >= 200_000:
            return 'S',  (255, 230,  80)
        if score >= 100_000:
            return 'A+', (220, 200,  60)
        if score >=  60_000:
            return 'A',  (200, 180,  50)
        if score >=  30_000:
            return 'B+', (140, 220, 140)
        if score >=  15_000:
            return 'B',  (100, 190, 100)
        if score >=   7_000:
            return 'C',  (120, 160, 220)
        if score >=   3_000:
            return 'D',  (180, 140,  80)
        return 'F', (180, 60, 60)

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------

    def _advance_turn(self):
        self.turn_count += 1

        # Rand's Heart: show dramatic message if death was just prevented
        if getattr(self.player, '_rands_heart_triggered', False):
            self.player._rands_heart_triggered = False
            self.add_message(
                "Rand's Heart BURSTS with blinding protective light!", 'success')
            self.add_message(
                "A lover's promise shields you from death! "
                "Your wounds close, your mind clears, your strength returns!", 'success')
            self.add_message(
                "The silver locket crumbles to dust, its promise fulfilled.", 'info')
            self._log_chronicle("I died. I felt it — the cold, the nothing. Then warmth. Rand's Heart pulled me back. The locket is dust now. I don't get a second chance.")

        qs = getattr(self, 'quirk_system', None)
        if qs and self.player:
            qs.on_turn()
            qs.tick_powers()

        # Decrement prayer cooldown
        if self.player.prayer_cooldown > 0:
            self.player.prayer_cooldown -= 1

        # Decrement recall lore cooldown
        if self.player.recall_lore_cooldown > 0:
            self.player.recall_lore_cooldown -= 1

        # Abaddon holy fire resistance removal timer
        if self.abaddon_resist_removed_turns > 0:
            self.abaddon_resist_removed_turns -= 1
            if self.abaddon_resist_removed_turns == 0:
                abaddon = next((m for m in self.monsters
                                if m.alive and m.kind == 'abaddon_destroyer'), None)
                if abaddon:
                    abaddon.resistances = list(getattr(abaddon, 'base_resistances', []))
                    self.add_message(
                        "The holy fire fades. Abaddon's dark armor reforms.", 'danger')

        # Decrement hack reality cooldown
        if self.player.hack_reality_cooldown > 0:
            self.player.hack_reality_cooldown -= 1

        # Tick monster status effects (DOT damage, duration expiry)
        for m in self.monsters:
            if m.alive:
                m.tick_effects()
                if not m.alive:
                    self._on_monster_killed(m)
                    self.add_message(f"The {m.name} succumbs to its wounds!", 'combat')

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
        # Passive PER-based trap detection
        self._do_passive_trap_detection()
        # Unicorn NPC state machine tick
        self._tick_unicorn()
        # Passive PER-based ambush detection
        self._do_passive_ambush_detection()
        # Eye of Horus: passive HP regen every N turns
        for _acc in (self.player.amulet, self.player.ring):
            _pr = getattr(_acc, 'passive_regen', 0) if _acc else 0
            _pri = getattr(_acc, 'passive_regen_interval', 5) if _acc else 5
            if _pr > 0 and self.turn_count % _pri == 0:
                if self.player.hp < self.player.max_hp:
                    self.player.hp = min(self.player.max_hp, self.player.hp + _pr)

        # Coat of Cú Chulainn: berserk trigger at low HP
        if not self.player.has_effect('berserk'):
            for _arm_slot in self.player.armor_slots:
                if _arm_slot and getattr(_arm_slot, 'berserk_trigger', False):
                    _bpct = _arm_slot.berserk_hp_threshold
                    if self.player.hp > 0 and self.player.hp / max(1, self.player.max_hp) <= _bpct:
                        self.player.status_effects['berserk'] = _arm_slot.berserk_duration
                        self.player._berserk_str_bonus = _arm_slot.berserk_str_bonus
                        self.player.STR += _arm_slot.berserk_str_bonus
                        self.add_message("The ríastrad takes hold! Your body warps with primal fury!", 'combat')
        elif self.player.has_effect('berserk'):
            # Berserk HP cost per turn
            _berserk_cost = getattr(self.player, '_berserk_hp_cost', 1)
            for _arm_slot in self.player.armor_slots:
                if _arm_slot and getattr(_arm_slot, 'berserk_trigger', False):
                    _berserk_cost = _arm_slot.berserk_hp_cost
                    break
            self.player.hp = max(1, self.player.hp - _berserk_cost)
            # Check if berserk just expired
            if self.player.status_effects.get('berserk', 0) <= 1:
                _str_bonus = getattr(self.player, '_berserk_str_bonus', 0)
                if _str_bonus:
                    self.player.STR -= _str_bonus
                    self.player._berserk_str_bonus = 0
                self.add_message("The fury fades. You feel drained.", 'warning')

        # Seal of Solomon: pacify nearby monsters
        for _acc in (self.player.amulet, self.player.ring):
            if _acc and getattr(_acc, 'pacify_chance', 0) > 0:
                for m in self.monsters:
                    if m.alive and abs(m.x - self.player.x) <= 2 and abs(m.y - self.player.y) <= 2:
                        if random.random() < _acc.pacify_chance:
                            m.add_effect('paralyzed', 1)

        # Clairvoyant: reveal tiles within 10-tile radius each turn
        if self.player.has_effect('clairvoyant'):
            px, py = self.player.x, self.player.y
            for cy in range(max(0, py - 10), min(self.dungeon.height, py + 11)):
                for cx in range(max(0, px - 10), min(self.dungeon.width, px + 11)):
                    if abs(cx - px) + abs(cy - py) <= 10:
                        self.dungeon.explored.add((cx, cy))

        # Torc of Boudicca: AC bonus when surrounded by 3+ enemies
        _surr_bonus = 0
        for _acc in (self.player.amulet, self.player.ring):
            if _acc and getattr(_acc, 'surrounded_ac_bonus', 0) > 0:
                _adj_enemies = sum(1 for m in self.monsters if m.alive
                                   and abs(m.x - self.player.x) <= 1
                                   and abs(m.y - self.player.y) <= 1)
                if _adj_enemies >= 3:
                    _surr_bonus = _acc.surrounded_ac_bonus
                break
        self.player._surrounded_ac_bonus = _surr_bonus

        self._do_monster_turns()
        self._do_pet_turns()
        self._maybe_wander_spawn()
        self._death_proximity_warning()
        self._tick_hp_regen()

    def _maybe_wander_spawn(self):
        """Periodically spawn a wandering monster to keep pressure on the player."""
        import random as _rng
        # Spawn every 18-30 turns; more frequently at deeper levels
        interval = max(10, 22 - self.dungeon_level // 4)
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
        occupied |= {(p.x, p.y) for p in self.pets if p.alive}
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
        # PER-based avoidance: chance to notice and sidestep at the last moment
        import random as _rng_trap
        avoid_chance = 0.05 + self.player.PER * 0.02  # PER 10 = 25%, PER 16 = 37%
        if _rng_trap.random() < avoid_chance:
            trap['revealed'] = True
            self.add_message(
                f"You notice a {trap['type'].replace('_', ' ')} trap just in time and sidestep it!",
                'success')
            return
        # Trap fires -- remove it from the floor
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
        if trap_type == 'pit':
            # Pit trap creates a permanent pit at this location
            if not hasattr(self.dungeon, 'pits'):
                self.dungeon.pits = set()
            self.dungeon.pits.add((x, y))
            self.player.add_effect('in_pit', 1)
            self.add_message("A pit opens beneath you! You must climb out.", 'danger')
        elif trap_type == 'alarm':
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
        elif trap_type == 'fire':
            if self.player.has_effect('fire_resist'):
                self.add_message("You resist most of the flames!", 'info')
            else:
                self.player.add_effect('burning', 3)
        elif trap_type == 'sleep_gas':
            if self.player.has_effect('sleep_resist'):
                self.add_message("You resist the sleeping gas!", 'info')
            else:
                self.player.add_effect('sleeping', random.randint(3, 8))
                self.add_message("You fall asleep!", 'danger')
        elif trap_type == 'bear_trap':
            self.player.add_effect('immobilized', random.randint(2, 4))
            self.add_message("You're stuck! Struggle to break free!", 'danger')
        elif trap_type == 'squeaky_board':
            for m in self.monsters:
                if m.alive:
                    m._alerted = True
                    m.status_effects.pop('sleeping', None)
            self.add_message("Every creature on the floor heard that!", 'danger')
        elif trap_type == 'rust':
            from status_effects import _can_rust
            # Collect all equipped items that can rust
            rust_targets = []
            if self.player.weapon and _can_rust(self.player.weapon):
                rust_targets.append(self.player.weapon)
            if self.player.shield and _can_rust(self.player.shield):
                rust_targets.append(self.player.shield)
            for slot in self.player.armor_slots:
                if slot and _can_rust(slot):
                    rust_targets.append(slot)
            if rust_targets:
                victim = random.choice(rust_targets)
                if getattr(victim, 'enchant_bonus', 0) > -3:
                    victim.enchant_bonus = getattr(victim, 'enchant_bonus', 0) - 1
                    self.add_message(f"Your {victim.name} rusts! (-1 enchantment)", 'danger')
                else:
                    self.add_message(f"Your {victim.name} is corroded but holds together.", 'warning')
            else:
                self.add_message("The water washes over you harmlessly.", 'info')
        elif trap_type == 'polymorph':
            import copy as _copy
            from items import load_items as _load
            transformable = [i for i in self.player.inventory
                             if not getattr(i, 'id', '').startswith('philosopher')]
            if transformable:
                victim = random.choice(transformable)
                old_name = victim.name
                cls_name = type(victim).__name__.lower()
                try:
                    pool = [t for t in _load(cls_name) if t.min_level <= self.dungeon_level]
                    if pool:
                        replacement = _copy.copy(random.choice(pool))
                        replacement.x = getattr(victim, 'x', 0)
                        replacement.y = getattr(victim, 'y', 0)
                        idx = self.player.inventory.index(victim)
                        for slot, eq in list(self.player.equipment.items()):
                            if eq is victim:
                                self.player.equipment[slot] = None
                        self.player.inventory[idx] = replacement
                        self.add_message(f"Your {old_name} transforms into {self._a_or_an(replacement.name)}!", 'warning')
                    else:
                        self.add_message("The energy dissipates harmlessly.", 'info')
                except FileNotFoundError:
                    self.add_message("The energy dissipates harmlessly.", 'info')
            else:
                self.add_message("The energy dissipates harmlessly.", 'info')
        qs = getattr(self, 'quirk_system', None)
        if qs and hasattr(qs, 'on_trap_triggered'):
            qs.on_trap_triggered(trap_type)
        if not getattr(self, '_chronicle_first_trap', False):
            self._chronicle_first_trap = True
            self._log_chronicle(f"Stepped on a {trap_type.replace('_', ' ')} trap. Should have watched where I was walking.")
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
            and not any(p.alive and p.x == x and p.y == y for p in self.pets)
        ]
        if floors:
            self.player.x, self.player.y = _rng.choice(floors)
            self._refresh_fov()
            self.add_message("You feel disoriented as space warps around you!", 'warning')
            _qs_tp = getattr(self, 'quirk_system', None)
            if _qs_tp:
                _qs_tp.on_teleport()

    def _spawn_at(self, x: int, y: int):
        """Spawn a single level-appropriate monster near (x, y)."""
        new_monsters = spawn_monsters(self.dungeon.rooms, self.dungeon_level,
                                      self.dungeon, min_count=1, max_count=1)
        if new_monsters:
            m = new_monsters[0]
            for dx2 in range(-2, 3):
                for dy2 in range(-2, 3):
                    nx2, ny2 = x + dx2, y + dy2
                    if self.dungeon.is_walkable(nx2, ny2) and \
                       not any(om.alive and om.x == nx2 and om.y == ny2 for om in self.monsters):
                        m.x, m.y = nx2, ny2
                        self.monsters.append(m)
                        return

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
        """Auto-reveal adjacent tiles, secret doors, and traps when player is searching."""
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
                    # Also reveal hidden traps
                    trap = self.dungeon.traps.get((nx, ny))
                    if trap and not trap.get('revealed'):
                        trap['revealed'] = True
                        self.add_message(
                            f"Searching reveals a {trap['type'].replace('_', ' ')} trap!", 'success')
        # Also reveal adjacent ambush monsters
        for m in self.monsters:
            if (m.alive and m.ai_pattern == 'ambush'
                    and not getattr(m, '_aware', False)
                    and abs(m.x - px) <= 1 and abs(m.y - py) <= 1):
                m._aware = True
                self.add_message(f"Searching reveals a hidden {m.name}!", 'warning')

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

    # Disarm difficulty per trap type: (quiz_tier, threshold)
    _TRAP_DISARM = {
        'squeaky_board': (1, 1), 'alarm':     (1, 1),
        'bear_trap':     (1, 2), 'arrow':     (2, 2),
        'rust':          (2, 2), 'sleep_gas': (2, 3),
        'acid':          (3, 3), 'teleport':  (3, 3),
        'pit':           (3, 3), 'fire':      (3, 3),
        'polymorph':     (4, 4),
    }

    def _try_disarm_trap(self) -> bool:
        """Try to disarm an adjacent revealed trap via economics quiz. Returns True if handled."""
        px, py = self.player.x, self.player.y
        # Find nearest adjacent revealed trap
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                trap = self.dungeon.traps.get((nx, ny))
                if trap and trap.get('revealed'):
                    charges = getattr(self.player, 'lockpick_charges', 0)
                    if charges <= 0:
                        self.add_message(
                            "You see the trap but have no lockpick tools to disarm it.", 'warning')
                        return True
                    trap_name = trap['type'].replace('_', ' ')
                    tier, threshold = self._TRAP_DISARM.get(trap['type'], (2, 2))
                    self.quiz_title = f"DISARMING {trap_name.upper()} -- AI"
                    self.state = STATE_QUIZ
                    _trap_pos = (nx, ny)

                    def _on_disarm(result, pos=_trap_pos, tname=trap_name):
                        self.state = STATE_PLAYER
                        self.player.lockpick_charges -= 1
                        if result.success:
                            if pos in self.dungeon.traps:
                                del self.dungeon.traps[pos]
                            self.add_message(
                                f"You carefully disarm the {tname} trap. "
                                f"({self.player.lockpick_charges} picks remaining)", 'success')
                            if not getattr(self, '_chronicle_first_disarm', False):
                                self._chronicle_first_disarm = True
                                self._log_chronicle("Disarmed my first trap. Hands were shaking the whole time.")
                        else:
                            self.add_message(
                                f"You fumble the disarm! The {tname} trap remains. "
                                f"({self.player.lockpick_charges} picks remaining)", 'warning')
                        self._advance_turn()

                    self.quiz_engine.start_quiz(
                        mode='threshold',
                        subject='ai',
                        tier=tier,
                        callback=_on_disarm,
                        threshold=threshold,
                        wisdom=self.player.WIS,
                        timer_modifier=self.player.get_quiz_timer_modifier(),
                        extra_seconds=self.player.get_quiz_extra_seconds('ai'),
                        base_seconds=self.player.get_quiz_timer('ai'),
                    )
                    return True
        return False  # no revealed trap nearby — fall through to lockpick

    def _do_passive_trap_detection(self):
        """Passive PER-based detection of adjacent unrevealed traps each turn."""
        import random as _rng
        chance = 0.03 + self.player.PER * 0.01  # PER 10 = 13%, PER 16 = 19%
        px, py = self.player.x, self.player.y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                trap = self.dungeon.traps.get((nx, ny))
                if trap and not trap.get('revealed'):
                    if _rng.random() < chance:
                        trap['revealed'] = True
                        self.add_message(
                            f"You spot a {trap['type'].replace('_', ' ')} trap nearby!", 'warning')

    def _do_passive_ambush_detection(self):
        """Passive PER-based detection of hidden ambush monsters within sight."""
        import random as _rng
        # Higher chance than traps — you're looking at the room, not the floor
        chance = 0.05 + self.player.PER * 0.015  # PER 10 = 20%, PER 16 = 29%
        px, py = self.player.x, self.player.y
        for m in self.monsters:
            if not m.alive or m.ai_pattern != 'ambush' or getattr(m, '_aware', False):
                continue
            if (m.x, m.y) not in self.visible:
                continue
            dist = abs(m.x - px) + abs(m.y - py)
            if dist <= 5 and _rng.random() < chance:
                m._aware = True
                self.add_message(
                    f"Your keen senses detect a {m.name} lying in wait!", 'warning')

    # ------------------------------------------------------------------
    # SP starvation
    # ------------------------------------------------------------------

    def _tick_sp(self):
        # Base SP drain: 1 per 2 moves (0.5/move effective)
        # Ring of Sustenance halves again (1 per 4 moves)
        self._sp_drain_tick = getattr(self, '_sp_drain_tick', 0) + 1
        drain_interval = 4 if self.player.has_effect('sustained') else 2
        if self._sp_drain_tick % drain_interval != 0:
            return
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
        px, py = self.player.x, self.player.y
        # Skip the Abyssal Shimmer -- it's fixed to the floor
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
            _gold_amt = item.amount
            # Draupnir: double gold pickups
            for _acc in (self.player.amulet, self.player.ring):
                if _acc and getattr(_acc, 'gold_multiplier', 0) > 0:
                    _gold_amt = int(_gold_amt * _acc.gold_multiplier)
                    break
            self.player_gold += _gold_amt
            self.ground_items.remove(item)
            self.add_message(f"You pick up {_gold_amt} gold coins.", 'loot')
            _snd.play('gold')
            self._advance_turn()
            return
        if isinstance(item, Lockpick):
            # Lockpicks convert directly to charges -- never enter inventory
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
            # Philosopher's Stone grants identify_sight — auto-identify on pickup
            if self.player.has_effect('identify_sight'):
                item.identified = True
                self.player.known_item_ids.add(item.id)
            if isinstance(item, Ammo):
                self.add_message(f"You pick up {item.count} {self._display_name(item)}s.", 'loot')
            else:
                self.add_message(f"You pick up the {self._display_name(item)}.", 'loot')
            # Chronicle notable pickups (quest artifacts)
            _CHRONICLE_ITEMS = {
                'philosophers_stone', 'ariadnes_thread', 'bronze_bull',
                'eye_of_the_graeae', 'broken_blade_of_gram', 'gleipnir',
                'vidars_sandal', 'scales_of_michael', 'sword_of_michael',
                'magic_dungeon_carrot',
                'cats_footstep', 'womans_beard', 'mountain_root',
                'fish_breath', 'bird_spittle', 'bear_sinew',
                'tablet_of_second_death', 'philosophers_wrench',
                'complete_tablet_of_second_death', 'scroll_lake_of_fire',
            }
            if getattr(item, 'id', '') in _CHRONICLE_ITEMS:
                _cname = self._display_name(item)
                _CHRONICLE_FLAVOR = {
                    'philosophers_stone': "Found the Philosopher's Stone. My hands are shaking. Time to get out of here.",
                    'ariadnes_thread': "Picked up a strange golden thread. It feels warm, almost alive.",
                    'bronze_bull': "Found a bronze idol shaped like a bull. Heavy. Old. Feels important.",
                    'eye_of_the_graeae': "A milky white eye, still wet. I don't want to think about where it came from.",
                    'broken_blade_of_gram': "Half a legendary sword. Even broken, the edge could shave a thought.",
                    'gleipnir': "Gleipnir. Thin as a ribbon but I can't break it. Nothing can.",
                    'vidars_sandal': "A sandal made for a god. It's enormous. And somehow, it fits.",
                    'scales_of_michael': "The Scales hover in my hands. I feel the weight of every choice I've made.",
                    'sword_of_michael': "A blade of white fire. It knows my name.",
                    'magic_dungeon_carrot': "A glowing carrot, of all things. Something tells me I shouldn't eat this one.",
                    'cats_footstep': "The sound of a cat's footstep, bottled. How is that even possible?",
                    'womans_beard': "The roots of a woman's beard. The dwarves are mad, but maybe that's the point.",
                    'mountain_root': "A root of a mountain. It weighs almost nothing. That feels wrong.",
                    'fish_breath': "The breath of a fish, sealed in a vial. The stopper must never come off, I think.",
                    'bird_spittle': "The spittle of a bird. I didn't know birds could spit. I still don't.",
                    'bear_sinew': "The sinew of a bear's sensitivity. I have no idea what that means, but here it is.",
                    'tablet_of_second_death': "Found a stone tablet with a slot in it. The inscription mentions Revelation and a 'second death.' Ominous.",
                    'philosophers_wrench': "An odd tool. Not a weapon, not a key. It feels like it wants to join things together.",
                    'complete_tablet_of_second_death': "The Stone fit the Tablet perfectly. It's glowing now. The inscription burns with golden light.",
                    'scroll_lake_of_fire': "A worn scroll. The ink is red-brown. It smells like ash. I can't read it yet, but I feel its weight.",
                }
                self._log_chronicle(_CHRONICLE_FLAVOR.get(item.id, f"Picked up something interesting: {_cname}."))
            if isinstance(item, Artifact) and item.id == 'philosophers_stone':
                self.add_message(
                    "The Philosopher's Stone! Return to the surface to win!", 'loot'
                )
                # The Stone's radiance reveals the true nature of all things
                self.player.add_effect('identify_sight', -1)
                self._auto_identify_all()
                self.add_message(
                    "The Stone's radiance illuminates your mind — all items are revealed!", 'success'
                )
            # Track trigger items for NPC moral encounters
            trigger_levels = getattr(self, '_npc_trigger_item_levels', {})
            if getattr(item, 'id', '') in trigger_levels:
                self._npc_triggered_items.add(item.id)
            # Auto-reveal BUC at dungeon level 30+ with WIS >= 14
            if (self.dungeon_level >= 30 and self.player.WIS >= 14
                    and hasattr(item, 'buc') and not getattr(item, 'buc_known', False)):
                item.buc_known = True
                _buc = item.buc
                if _buc == 'blessed':
                    self.add_message("Your wisdom senses a holy aura.", 'success')
                elif _buc == 'cursed':
                    self.add_message("Your wisdom senses a dark aura.", 'warning')
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

        # Mimic springs out on first interaction — surprise attack!
        if container.is_mimic:
            from container_system import _spawn_mimic
            mimic = _spawn_mimic(container, self.monsters, self.dungeon_level)
            self.ground_items.remove(container)
            # Surprise attack: 10-20% of player's max HP
            import random as _rng
            surprise_pct = _rng.uniform(0.10, 0.20)
            surprise_dmg = max(1, int(self.player.max_hp * surprise_pct))
            self.player.hp = max(1, self.player.hp - surprise_dmg)
            mname = mimic.name if mimic else 'mimic'
            self.add_message(
                f"The {container.name} springs to life -- it's {self._a_or_an(mname)}!", 'danger'
            )
            self.add_message(
                f"It strikes before you can react! ({surprise_dmg} damage)", 'danger'
            )
            _snd.play('monster_hit')
            self._advance_turn()
            return

        if getattr(self.player, 'lockpick_charges', 0) <= 0:
            self.add_message("You have no lockpick charges.", 'warning')
            return

        self.quiz_title = (
            f"PICKING {container.name.upper()}  --  ECONOMICS  "
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
                # Bash damage: potions and scrolls shattered
                _FRAGILE = ('potion', 'scroll')
                for loot_item in result['loot']:
                    if getattr(container, 'bash_damaged', False) \
                            and getattr(loot_item, 'item_class', '') in _FRAGILE:
                        self.add_message(
                            f"A shattered {self._display_name(loot_item)} lies in the wreckage.", 'warning'
                        )
                        continue
                    loot_item.x, loot_item.y = cx, cy
                    self.ground_items.append(loot_item)
                    self.add_message(f"You find {self._display_name(loot_item)}!", 'loot')
                if result['gold'] > 0:
                    from items import GoldPile
                    self.ground_items.append(GoldPile(result['gold'], cx, cy))
                _qs_lk = getattr(self, 'quirk_system', None)
                if _qs_lk:
                    _qs_lk.on_lockpick_success()
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

    def _start_observe(self):
        """Press 'o' to enter observe mode — look at monsters, items, or terrain."""
        px, py = self.player.x, self.player.y
        sight = self.player.get_sight_radius()

        # Build candidate list: visible monsters
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0
        self._observe_targeting = True
        self._melee_targeting = False
        self._throw_targeting = False
        self._observe_reach = sight

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        self.add_message(
            "Observe -- arrow keys to look, TAB to cycle targets, ENTER to examine, ESC to cancel.",
            'info'
        )

    def _open_melee_targeting(self):
        """Press 'a' to enter melee targeting mode — attack adjacent tiles (or further with reach weapons)."""
        weapon = self.player.weapon
        reach = weapon.reach if weapon else 1

        px, py = self.player.x, self.player.y

        # Build candidate list: alive monsters within melee reach
        candidates = [
            m for m in self.monsters
            if m.alive
            and abs(m.x - px) <= reach and abs(m.y - py) <= reach
            and not (m.x == px and m.y == py)
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0
        self._melee_targeting = True
        self._melee_reach = reach

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            # Default cursor one tile to the right (or clamp)
            self.target_cursor_x = min(px + 1, self.dungeon.width - 1)
            self.target_cursor_y = py

        self.state = STATE_TARGET
        weapon_name = weapon.name if weapon else "fists"
        if candidates:
            self.add_message(
                f"Melee targeting with {weapon_name} -- arrow keys to aim, TAB to cycle, ENTER to strike, ESC to cancel.",
                'info'
            )
        else:
            self.add_message(
                f"Melee targeting with {weapon_name} -- arrow keys to aim, ENTER to strike, ESC to cancel.",
                'info'
            )

    # ------------------------------------------------------------------
    # Mystery system
    # ------------------------------------------------------------------

    def _start_mystery(self, altar):
        """Begin a mystery encounter -- show description and ask the player to accept."""
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
        if not getattr(self, '_chronicle_first_mystery', False):
            self._chronicle_first_mystery = True
            self._log_chronicle(f"Found a strange altar. {m['name']}. The inscription dared me to approach.")
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

        # Consume key item (if any; not cauldron food, not sisyphus boulder)
        if m['key_item'] is not None and altar.mystery_id not in ('cauldron', 'sisyphus'):
            consume_key_item(altar.mystery_id, self.player)

        # For cauldron: consume 3 food items
        if altar.mystery_id == 'cauldron':
            foods = get_cauldron_food_items(self.player)
            for food in foods[:3]:
                self.player.remove_from_inventory(food)
            self.add_message("Three meals are consumed by the cauldron's fire.", 'info')

        # Sisyphus: physical challenge -- start tracking tiles
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
            if ch['mode'] in ('chain', 'escalator_chain') and 'threshold' in ch:
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
            'base_seconds':   self.player.get_quiz_timer(ch['subject']),
        }
        if 'total' in ch:
            quiz_kwargs['total_qs'] = ch['total']
        if 'max_chain' in ch:
            quiz_kwargs['max_chain'] = ch['max_chain']

        self.quiz_title = f"{m['name'].upper()}  --  {ch['subject'].upper()}"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(**quiz_kwargs)


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
        # +5s harvest timer bonus if monster has been lore-identified
        _lore_known = getattr(self.player, 'lore_known_monster_ids', set())
        _lore_bonus = 5 if getattr(corpse, 'monster_id', '') in _lore_known else 0
        self.quiz_title = f"HARVESTING {corpse.name.upper()}  --  ANIMAL LORE"
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
                        f"Too heavy -- {ingredient.name} dropped.", 'warning'
                    )
            self._advance_turn()

        harvest_corpse(self.player, corpse, self.quiz_engine, on_complete,
                       extra_seconds=_lore_bonus)

    # ------------------------------------------------------------------
    # Cook menu
    # ------------------------------------------------------------------

    _COOK_TABS = [
        ('Single',  'single'),
        ('Recipes', 'compound'),
    ]

    def _cook_item(self, ingredient):
        self.player.remove_from_inventory(ingredient)
        self.quiz_title = f"COOKING {ingredient.name.upper()}  --  COOKING CHAIN"
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
        self.quiz_title = f"PREPARING {recipe['name'].upper()}  --  COOKING CHAIN"
        self.state = STATE_QUIZ

        def on_complete(messages: list[str]):
            self.state = STATE_PLAYER
            for i, msg in enumerate(messages):
                self.add_message(msg, 'warning' if (i == 0 and ('ruin' in msg.lower() or 'mediocre' in msg.lower())) else 'success')
            if not getattr(self, '_chronicle_first_compound', False):
                self._chronicle_first_compound = True
                self._log_chronicle(f"Cooked my first compound recipe: {recipe['name']}. The dungeon smells like a kitchen for once.")
            # Track discovered recipes
            rname = recipe.get('name', '')
            if rname and rname not in self._cooked_recipes:
                self._cooked_recipes.append(rname)
            self._advance_turn()

        cook_compound_recipe(self.player, recipe, self.player.inventory, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Eat menu  (z key)
    # ------------------------------------------------------------------

    _EAT_TABS = [
        ('Cooked Food', lambda i: isinstance(i, Food)),
        ('Raw Ingredients', lambda i: isinstance(i, Ingredient)),
    ]

    # ------------------------------------------------------------------
    # Quaff menu  (Q key)
    # ------------------------------------------------------------------

    _BENEFICIAL_EFFECTS = frozenset({
        'heal', 'extra_heal', 'full_heal', 'restore_sp', 'restore_mp', 'brilliance_mp',
        'cure_poison', 'cure_disease', 'cure_all',
        'haste', 'invisibility', 'regeneration',
        'heroism', 'brilliance', 'levitation',
        'restore_str', 'gain_level',
        'fire_resist', 'cold_resist', 'shock_resist',
    })

    # Shared a-z key map for all item menus (26 items per page)
    _AZ_KEYS = {
        pygame.K_a: 0,  pygame.K_b: 1,  pygame.K_c: 2,  pygame.K_d: 3,
        pygame.K_e: 4,  pygame.K_f: 5,  pygame.K_g: 6,  pygame.K_h: 7,
        pygame.K_i: 8,  pygame.K_j: 9,  pygame.K_k: 10, pygame.K_l: 11,
        pygame.K_m: 12, pygame.K_n: 13, pygame.K_o: 14, pygame.K_p: 15,
        pygame.K_q: 16, pygame.K_r: 17, pygame.K_s: 18, pygame.K_t: 19,
        pygame.K_u: 20, pygame.K_v: 21, pygame.K_w: 22, pygame.K_x: 23,
        pygame.K_y: 24, pygame.K_z: 25,
    }

    _cycle_tab = staticmethod(cycle_tab)

    # ------------------------------------------------------------------
    # Throw Potion  (T key)
    # ------------------------------------------------------------------

    # Weapon classes that can be thrown, with throw damage multiplier
    _throw_crosses_tile = staticmethod(throw_crosses_tile)

    _THROWABLE_CLASSES = {
        'dagger':      1.0,    # designed for throwing
        'axe':         0.75,   # franciscas, hand axes
        'spear':       0.9,    # javelin-like
        'mace':        0.6,    # heavy but compact
        'flail':       0.5,    # awkward spin
        'net':         0.3,    # entangle, not damage
        'morningstar': 0.5,    # awkward but heavy impact
        'rapier':      0.4,    # fragile, not designed for it
        'scimitar':    0.5,    # curved blade, poor aerodynamics
        'sword':       0.4,    # not designed for throwing
    }

    # Break chance by material (higher = more fragile when thrown)
    _THROW_BREAK_CHANCE = {
        'bone':           0.50,
        'iron':           0.35,
        'steel':          0.25,
        'hardened_gold':  0.20,
        'diamond':        0.10,
        'adamantine':     0.05,
    }
    _THROW_BREAK_LEGENDARY = 0.05  # named/legendary weapons

    @staticmethod
    def _is_throwable_weapon(weapon) -> bool:
        """Can this weapon be thrown? Must be 1h, throwable class, and not a ranged weapon."""
        if weapon.requires_ammo:
            return False
        if weapon.two_handed:
            return False
        if weapon.weight > 5.0:
            return False
        return weapon.weapon_class in Game._THROWABLE_CLASSES

    def _get_weapon_throw_damage(self, weapon) -> int:
        """Calculate throw damage: base_damage * class_mult * STR_factor."""
        mult = self._THROWABLE_CLASSES.get(weapon.weapon_class, 0.5)
        str_factor = 1.0 + max(0, self.player.STR - 10) * 0.03
        return max(1, int(weapon.base_damage * mult * str_factor))

    def _get_weapon_break_chance(self, weapon) -> float:
        """Return probability [0-1] that this weapon breaks on throw."""
        if weapon.weapon_class == 'net':
            return 0.0  # nets are designed to be thrown and recovered
        material = weapon.material.lower()
        base = self._THROW_BREAK_CHANCE.get(material, self._THROW_BREAK_LEGENDARY)
        return base

    # Map potion effect names to monster status effect names (debuffs)
    _THROW_DEBUFF_MAP = {
        'poison':        'poisoned',
        'paralysis':     'paralyzed',
        'confusion':     'confused',
        'blindness':     'blinded',
        'sleep':         'sleeping',
        'weakness':      'weakened',
        'slow':          'slowed',
        'sickness':      'diseased',
        'fumbling':      'fumbling',
        'fear':          'feared',
        'hallucination': 'hallucinating',
    }

    # Map potion effect names to monster buff status effects
    _THROW_BUFF_MAP = {
        'haste':         'hasted',
        'invisibility':  'invisible',
        'regeneration':  'regenerating',
        'levitation':    'levitating',
        'fire_resist':   'fire_resist',
        'cold_resist':   'cold_resist',
        'shock_resist':  'shock_resist',
    }

    def _get_throw_range(self) -> int:
        """Throw range: 3 + (STR - 10) // 2, clamped to [3, 8]."""
        return max(3, min(8, 3 + (self.player.STR - 10) // 2))

    _THROW_TABS = [
        ('Potions', lambda i: isinstance(i, Potion)),
        ('Weapons', lambda i: isinstance(i, Weapon)),
        ('Other',   lambda i: not isinstance(i, (Potion, Weapon))),
    ]

    def _open_throw_targeting(self, potion):
        """Enter targeting mode for throwing a potion."""
        self._throw_targeting = True
        self._melee_targeting = False
        self._throw_potion = potion
        self._throw_reach = self._get_throw_range()

        px, py = self.player.x, self.player.y
        reach = self._throw_reach

        # Build candidate list: visible alive monsters within throw range
        from combat import _line_of_sight
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
            and max(abs(m.x - px), abs(m.y - py)) <= reach
            and _line_of_sight(px, py, m.x, m.y, self.dungeon)
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        display = self._display_name(potion)
        self.add_message(
            f"Throw {display} (range {reach}) -- arrows to aim, TAB to cycle, ENTER to throw, ESC to cancel.",
            'info'
        )

    def _confirm_throw_target(self):
        """Throw the selected item at cursor position."""
        item = self._throw_potion
        self._throw_targeting = False
        self._throw_potion = None
        self.state = STATE_PLAYER

        px, py = self.player.x, self.player.y
        tx, ty = self.target_cursor_x, self.target_cursor_y

        hit_monster = self._find_first_monster_in_path(px, py, tx, ty)

        if isinstance(item, Artifact) and item.id == 'unusual_soul_sphere':
            self._throw_unusual_sphere(item, hit_monster, tx, ty)
        elif isinstance(item, Artifact) and item.id == 'soul_sphere':
            self._throw_soul_sphere(item, hit_monster, tx, ty)
        elif isinstance(item, Weapon):
            self._throw_weapon(item, hit_monster, tx, ty)
        else:
            # Potion throw
            self.player.remove_from_inventory(item)
            item.identified = True
            self.player.known_item_ids.add(item.id)
            display = item.name
            if hit_monster:
                self._apply_thrown_potion(item, hit_monster, display)
            else:
                self.add_message(
                    f"The {display} shatters on the ground. Nothing happens.", 'info'
                )

        self._advance_turn()

    def _throw_weapon(self, weapon, monster, tx: int, ty: int):
        """Throw a weapon at a target. Deals damage, may break."""
        import random as _rng

        # --- Odin's Altar secret: throw Broken Gram over the altar ---
        odin_pos = getattr(self.dungeon, 'odin_altar_pos', None)
        if odin_pos:
            ax, ay = odin_pos
            px, py = self.player.x, self.player.y
            # Check if the thrown path crosses over the altar:
            # player on one side, target on the other side (altar between them)
            if weapon.id == 'broken_gram':
                crosses_altar = self._throw_crosses_tile(px, py, tx, ty, ax, ay)
                if crosses_altar:
                    self.player.remove_from_inventory(weapon)
                    self._activate_odin_shrine(weapon, reforge=True)
                    self._advance_turn()
                    return
            elif self._throw_crosses_tile(px, py, tx, ty, ax, ay):
                self.add_message(
                    "A rumble of distant thunder... but nothing happens. "
                    "Odin will not reforge this.", 'info')

        self.player.remove_from_inventory(weapon)
        display = weapon.name
        dmg = self._get_weapon_throw_damage(weapon)
        break_chance = self._get_weapon_break_chance(weapon)

        if monster:
            actual = monster.take_damage(dmg)
            self.add_message(
                f"You hurl the {display} at {monster.name}! ({actual} damage)", 'success'
            )
            if monster.is_dead():
                self._on_monster_killed(monster)
            land_x, land_y = monster.x, monster.y
        else:
            self.add_message(
                f"The {display} clatters to the ground.", 'info'
            )
            land_x, land_y = tx, ty

        # Break check
        if _rng.random() < break_chance:
            self.add_message(f"The {display} shatters on impact!", 'warning')
        else:
            # Weapon survives -- drop it on the ground
            weapon.x = land_x
            weapon.y = land_y
            self.ground_items.append(weapon)

    def _throw_soul_sphere(self, sphere, hit_monster, tx: int, ty: int):
        """Throw a Soul Sphere — releases a random pet creature at the landing spot."""
        self.player.remove_from_inventory(sphere)

        # Landing tile: if a monster was hit, land one tile before; else target tile
        if hit_monster:
            # Land at the monster's tile (pet spawns there, monster is not displaced)
            land_x, land_y = hit_monster.x, hit_monster.y
        else:
            land_x, land_y = tx, ty

        # Find a walkable tile near the landing spot for the pet
        spawn_x, spawn_y = land_x, land_y
        if not self.dungeon.is_walkable(spawn_x, spawn_y) or \
           any(m.alive and m.x == spawn_x and m.y == spawn_y for m in self.monsters) or \
           (spawn_x == self.player.x and spawn_y == self.player.y) or \
           any(p.alive and p.x == spawn_x and p.y == spawn_y for p in self.pets):
            # Try adjacent tiles
            found = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = land_x + dx, land_y + dy
                    if not self.dungeon.is_walkable(nx, ny):
                        continue
                    if nx == self.player.x and ny == self.player.y:
                        continue
                    if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                        continue
                    if any(p.alive and p.x == nx and p.y == ny for p in self.pets):
                        continue
                    spawn_x, spawn_y = nx, ny
                    found = True
                    break
                if found:
                    break
            if not found:
                # No room — sphere is wasted
                self.add_message("The sphere shatters but there is no room for a creature!", 'warning')
                return

        species = random_pet_species()
        pet = Pet(species, spawn_x, spawn_y)
        self.pets.append(pet)
        self.add_message(pet.species['stages'][0]['msg'], 'success')
        _snd.play('player_healed')
        self._log_chronicle(f"A soul sphere hatched. {pet.name} emerged. I'm not alone anymore.")

    def _throw_unusual_sphere(self, sphere, hit_monster, tx: int, ty: int):
        """Throw the Unusual Soul Sphere — summons Dad for 5 turns."""
        from boss_levels import BOSS_LEVELS
        if self.dungeon_level in BOSS_LEVELS:
            self.add_message(
                "The sphere pulses warmly in your hand, then fades. "
                "You hear Dad's voice: \"I believe in you. This one's yours.\"", 'info')
            return  # sphere NOT consumed — player keeps it
        self.player.remove_from_inventory(sphere)

        land_x, land_y = (hit_monster.x, hit_monster.y) if hit_monster else (tx, ty)

        # Find a walkable spawn tile near landing
        spawn_x, spawn_y = land_x, land_y
        placed = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = land_x + dx, land_y + dy
                if (self.dungeon.is_walkable(nx, ny)
                        and (nx, ny) != (self.player.x, self.player.y)
                        and not any(m.alive and m.x == nx and m.y == ny for m in self.monsters)
                        and not any(p.alive and p.x == nx and p.y == ny for p in self.pets)):
                    spawn_x, spawn_y = nx, ny
                    placed = True
                    break
            if placed:
                break
        if not placed:
            self.add_message(
                "The sphere shatters in a flash of silver light, but there is no room!", 'warning')
            return

        from pet_system import DadPet
        dad = DadPet(spawn_x, spawn_y, duration=5)
        self.pets.append(dad)
        self.add_message("Dad is here! Everything will be fine now!", 'success')

    def _find_first_monster_in_path(self, x0, y0, x1, y1):
        """Walk Bresenham line from (x0,y0) to (x1,y1). Return first alive monster hit, or None.
        Prevents corner-cutting through diagonal wall gaps."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            step_x = e2 > -dy
            step_y = e2 < dx
            # Diagonal step: block if both corners are walls
            if step_x and step_y:
                if (not self.dungeon.is_walkable(cx + sx, cy)
                        and not self.dungeon.is_walkable(cx, cy + sy)):
                    return None  # blocked by corner
            if step_x:
                err -= dy
                cx += sx
            if step_y:
                err += dx
                cy += sy
            if (cx, cy) != (x1, y1):
                # Check for monster at this tile
                for m in self.monsters:
                    if m.alive and m.x == cx and m.y == cy:
                        return m
                # Check for wall (projectile stops)
                if not self.dungeon.is_walkable(cx, cy):
                    return None
        # Check target tile for monster
        for m in self.monsters:
            if m.alive and m.x == x1 and m.y == y1:
                return m
        return None

    def _apply_thrown_potion(self, potion, monster, display: str):
        """Apply a thrown potion's effect to a monster."""
        if not monster.alive:
            self.add_message(f"The {display} shatters harmlessly.", 'info')
            return
        from status_effects import _RESIST_BLOCKS
        from dice import roll as roll_dice
        effect = potion.effect
        duration = potion.duration if potion.duration > 0 else 10

        # --- Debuff effects ---
        debuff = self._THROW_DEBUFF_MAP.get(effect)
        if debuff:
            # Check resistance via status effects
            for resist, blocked in _RESIST_BLOCKS.items():
                if debuff in blocked and monster.has_effect(resist):
                    self.add_message(
                        f"The {display} splashes {monster.name}, but it resists!", 'warning'
                    )
                    return
            # Check monster resistances list for thematic immunity
            mon_resists = getattr(monster, 'resistances', [])
            if ('poison' in mon_resists and debuff in ('poisoned', 'diseased')) or \
               ('magic' in mon_resists and debuff in ('confused', 'hallucinating', 'feared')):
                self.add_message(
                    f"The {display} splashes {monster.name}, but it seems immune!", 'warning'
                )
                return
            monster.add_effect(debuff, duration)
            label = debuff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {monster.name}! It is {label}!", 'success'
            )
            return

        # --- Buff effects (heals/buffs the monster -- bad idea!) ---
        buff = self._THROW_BUFF_MAP.get(effect)
        if buff:
            monster.add_effect(buff, duration)
            label = buff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {monster.name}. It looks {label}!", 'danger'
            )
            return

        # --- Healing effects (restore monster HP) ---
        if effect in ('heal', 'extra_heal', 'full_heal'):
            if effect == 'full_heal':
                healed = monster.max_hp - monster.hp
                monster.hp = monster.max_hp
            else:
                amt = roll_dice(potion.power) if potion.power else 10
                if effect == 'extra_heal':
                    amt += 10
                healed = min(amt, monster.max_hp - monster.hp)
                monster.hp = min(monster.max_hp, monster.hp + amt)
            if healed > 0:
                self.add_message(
                    f"The {display} splashes {monster.name}. It heals {healed} HP!", 'danger'
                )
            else:
                self.add_message(
                    f"The {display} splashes {monster.name}. It looks unaffected.", 'info'
                )
            return

        # --- Teleport (relocate monster randomly) ---
        if effect == 'teleport':
            import random as _rng
            walkable = [
                (x, y)
                for y in range(self.dungeon.height)
                for x in range(self.dungeon.width)
                if self.dungeon.is_walkable(x, y)
                and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                and not any(p.alive and p.x == x and p.y == y for p in self.pets)
                and (x, y) != (self.player.x, self.player.y)
            ]
            if walkable:
                nx, ny = _rng.choice(walkable)
                monster.x, monster.y = nx, ny
                self.add_message(
                    f"The {display} splashes {monster.name} -- it vanishes!", 'success'
                )
            else:
                self.add_message(
                    f"The {display} splashes {monster.name} but nothing happens.", 'info'
                )
            return

        # --- Stat drain (damage the monster instead) ---
        if effect in ('drain_str', 'drain_con', 'drain_int', 'drain_wis'):
            dmg = max(1, monster.max_hp // 20)
            actual = monster.take_damage(dmg)
            self.add_message(
                f"The {display} saps {monster.name}'s vitality! ({actual} damage)", 'success'
            )
            return

        # --- Everything else: no meaningful effect on monsters ---
        self.add_message(
            f"The {display} splashes {monster.name} but has no effect.", 'info'
        )

    # ------------------------------------------------------------------
    # Tile interactions  (D key -- fountain/grave/throne)
    # ------------------------------------------------------------------

    def _altar_buc_upgrade(self, item):
        """Drop an item on an altar to attempt uncurse/bless via theology quiz."""
        display = self._display_name(item)
        self.add_message(f"You place the {display} upon the altar...", 'info')
        self.quiz_title = "ALTAR BLESSING -- THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            chain = result.score
            if chain == 0:
                self.add_message("The altar remains cold and silent.", 'warning')
            elif item.buc == 'cursed':
                if chain >= 3:
                    item.buc = 'blessed'
                    item.buc_known = True
                    self.add_message(
                        f"Dark energy shatters — golden light suffuses the {display}! It is blessed!",
                        'success')
                else:
                    item.buc = 'uncursed'
                    item.buc_known = True
                    self.add_message(
                        f"The dark aura around the {display} dissipates! It is uncursed.",
                        'success')
            elif item.buc == 'uncursed':
                if chain >= 3:
                    item.buc = 'blessed'
                    item.buc_known = True
                    self.add_message(
                        f"Golden light suffuses the {display}! It is blessed!",
                        'success')
                else:
                    item.buc_known = True
                    self.add_message(
                        "The altar glows faintly but the blessing is insufficient.",
                        'info')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='theology',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('theology'),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _altar_buc_identify(self):
        """Stand on an altar and attempt to divine the BUC status of an item."""
        # Gather items that have BUC but it's not yet known
        candidates = [i for i in self.player.inventory
                      if hasattr(i, 'buc') and not getattr(i, 'buc_known', False)]
        if not candidates:
            self.add_message("You kneel at the altar, but sense nothing to divine.", 'info')
            return
        # Use the first unidentified-BUC item (simple approach -- could add a menu later)
        item = candidates[0]
        display = self._display_name(item)
        self.add_message(f"You place the {display} upon the altar and pray...", 'info')
        self.quiz_title = "ALTAR DIVINATION  --  THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                item.buc_known = True
                _buc = item.buc
                if _buc == 'blessed':
                    self.add_message(
                        f"The {display} glows with a warm golden light. It is blessed!", 'success'
                    )
                elif _buc == 'cursed':
                    self.add_message(
                        f"The {display} exudes a dark miasma. It is cursed!", 'warning'
                    )
                else:
                    self.add_message(
                        f"The {display} shows no special aura. It is uncursed.", 'info'
                    )
            else:
                self.add_message("The altar remains silent. Your prayer goes unanswered.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='theology',
            tier=1,
            callback=on_complete,
            threshold=1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _interact_tile(self):
        """Interact with the tile the player is standing on (fountain/grave/throne)."""
        tile = self.dungeon.tiles[self.player.y][self.player.x]
        if tile == FOUNTAIN:
            self._drink_fountain()
        elif tile == GRAVE:
            self._dig_grave()
        elif tile == THRONE:
            self._sit_throne()
        else:
            self.add_message("There's nothing to interact with here.", 'info')

    def _drink_fountain(self):
        """Drink from a fountain -- AI quiz determines outcome."""
        self.add_message("You cup your hands and drink from the fountain...", 'info')
        self.quiz_title = "FOUNTAIN -- AI"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_fountain(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='ai',
            tier=1,
            callback=on_complete,
            max_chain=6,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('ai'),
            base_seconds=self.player.get_quiz_timer('ai'),
        )

    def _resolve_fountain(self, chain: int):
        """Apply fountain effects based on chain score."""
        if not getattr(self, '_chronicle_first_fountain', False):
            self._chronicle_first_fountain = True
            self._log_chronicle("Drank from a dungeon fountain. Tasted like copper and starlight. Something happened.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            outcome = _rng.choice(['poison', 'monster', 'nothing'])
            if outcome == 'poison':
                self.player.add_effect('poisoned', 10)
                self.add_message("The water tastes foul! You feel poisoned!", 'danger')
            elif outcome == 'monster':
                self.add_message("Something rises from the fountain!", 'danger')
                self._spawn_at(px, py)
            else:
                self.add_message("The water tastes stale. Nothing happens.", 'info')
        elif chain == 1:
            self.add_message("The cool water refreshes you slightly.", 'info')
            self.player.restore_hp(max(5, self.player.max_hp // 20))
        elif chain == 2:
            self.add_message("The blessed water restores your health!", 'success')
            self.player.restore_hp(max(15, self.player.max_hp // 8))
        elif chain == 3:
            self.add_message("The magical water restores you fully!", 'success')
            self.player.restore_hp(self.player.max_hp)
            self.player.restore_sp(50)
        elif chain == 4:
            self.player.restore_hp(self.player.max_hp)
            self.player.restore_sp(self.player.max_sp)
            for eff in list(self.player.status_effects.keys()):
                if eff in ('poisoned', 'diseased', 'bleeding', 'burning', 'confused', 'blinded', 'corroding'):
                    del self.player.status_effects[eff]
            self.add_message("Divine water purifies you! All ailments are cured!", 'success')
        elif chain >= 5:
            stat = _rng.choice(['STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'])
            self.player.apply_stat_bonus(stat, 1)
            self.player.restore_hp(self.player.max_hp)
            self.add_message(f"The fountain glows with divine light! +1 {stat}!", 'success')

        # 33% chance fountain dries up after use
        if _rng.random() < 0.33:

            self.dungeon.tiles[py][px] = FLOOR
            self.add_message("The fountain dries up.", 'info')

    def _activate_ariadne_shrine(self, bull_item):
        """Player dropped the Bronze Bull into a fountain -- activate Ariadne's shrine."""
        shrine_door = getattr(self.dungeon, 'ariadne_shrine_door', None)
        if not shrine_door:
            # Wrong level — don't consume the item
            return

        # Consume the bull (remove from ground)
        if bull_item in self.ground_items:
            self.ground_items.remove(bull_item)

        self.add_message(
            "The bronze bull sinks into the fountain waters...", 'info')
        self.add_message(
            "The water shimmers gold! A voice whispers from the depths:", 'info')
        self.add_message(
            '"I wove salvation from a simple thread. Take it, and the beast '
            'shall have no walls to hide behind."', 'success')

        dx, dy = shrine_door
        self.dungeon.tiles[dy][dx] = DOOR
        self.add_message(
            "A hidden passage opens in a nearby wall!", 'success')
        self._log_chronicle("Dropped the bronze bull into a fountain. The water turned gold. A woman's voice spoke to me about thread and a beast. A passage opened in the wall.")

    def _activate_athena_shrine(self, eye_item):
        """Player dropped the Eye of the Graeae at an altar -- activate Athena's shrine."""
        shrine_door = getattr(self.dungeon, 'athena_shrine_door', None)
        if not shrine_door:
            # Wrong level — don't consume the item
            return

        if eye_item in self.ground_items:
            self.ground_items.remove(eye_item)

        self.add_message(
            "You place the milky eye upon the altar. It dissolves into pale light...", 'info')
        self.add_message(
            "A divine presence fills the room! Athena speaks:", 'info')
        self.add_message(
            '"The Grey Sisters paid for their secret. Take my shield, '
            'and let the Gorgon see what she truly is."', 'success')

        dx, dy = shrine_door
        self.dungeon.tiles[dy][dx] = DOOR
        self.add_message(
            "A hidden passage opens in a nearby wall!", 'success')
        self._log_chronicle("Placed the eye on an altar. It dissolved into light. Athena herself spoke. Told me to take her shield. A passage opened.")

    def _activate_odin_shrine(self, gram_item, reforge: bool = False):
        """Player offered the Broken Blade of Gram at Odin's Altar."""
        odin_pos = self.dungeon.odin_altar_pos
        shrine_door = getattr(self.dungeon, 'odin_shrine_door', None)
        if not shrine_door and not reforge:
            return  # wrong level, no shrine

        # Consume the broken blade
        if gram_item in self.ground_items:
            self.ground_items.remove(gram_item)

        if reforge:
            # SECRET: throw-over reforges Gram!
            self.add_message(
                "You hurl the broken blade over the altar...", 'info')
            self.add_message(
                "CRACK! A bolt of lightning strikes the altar! "
                "Thunder shakes the dungeon to its foundations!", 'danger')
            self.add_message(
                "Odin's voice booms: \"You have thrown your weapon over the enemy, "
                "as I threw Gungnir. I name you worthy.\"", 'success')
            self.add_message(
                "The shattered fragments of Gram fuse together in white-hot light. "
                "A reforged blade rests upon the altar, whole and gleaming.", 'success')
            # Spawn reforged Gram on the altar
            from items import load_items, copy_at
            weapons = load_items('weapon')
            gram_t = next((w for w in weapons if w.id == 'gram'), None)
            if gram_t:
                ax, ay = odin_pos
                gram = copy_at(gram_t, ax, ay)
                gram.identified = True
                self.ground_items.append(gram)
        else:
            # Normal path: blade dissolves, Odin speaks
            self.add_message(
                "The broken blade dissolves into the altar stone...", 'info')
            self.add_message(
                "Odin speaks: \"The blade is spent. But the earth holds secrets "
                "that steel cannot reach. Dig, as Sigurd dug.\"", 'success')

        # Always open the shrine (contains the shovel)
        if shrine_door:
            dx, dy = shrine_door
            self.dungeon.tiles[dy][dx] = DOOR
            self.add_message(
                "A hidden passage opens in a nearby wall!", 'success')
        if reforge:
            self._log_chronicle("I threw the broken blade over the altar like a madman. Lightning struck. When the light cleared, Gram lay whole on the stone, reforged. Odin called me worthy.")
        else:
            self._log_chronicle("Laid the broken blade on the altar. It dissolved. Odin spoke of digging, of secrets beneath the earth. A passage opened nearby.")

    # ------------------------------------------------------------------
    # Fenrir quest: Gleipnir forging, binding, and Vidar's Altar
    # ------------------------------------------------------------------

    _GLEIPNIR_COMPONENT_IDS = frozenset([
        'cats_footstep', 'womans_beard', 'mountain_root',
        'fish_breath', 'bird_spittle', 'bear_sinew',
    ])

    def _check_gleipnir_forge(self, fx, fy):
        """Check if all 6 Gleipnir components are at the Dwarven Forge position."""
        on_forge = [i for i in self.ground_items
                    if getattr(i, 'id', '') in self._GLEIPNIR_COMPONENT_IDS
                    and i.x == fx and i.y == fy]
        found_ids = {i.id for i in on_forge}
        if found_ids == self._GLEIPNIR_COMPONENT_IDS:
            # All 6 present — forge Gleipnir!
            for comp in on_forge:
                self.ground_items.remove(comp)
            from items import Artifact
            gleipnir = Artifact({
                'id': 'gleipnir', 'name': 'Gleipnir',
                'symbol': '&', 'color': [220, 220, 255],
                'item_class': 'artifact', 'weight': 0.1, 'min_level': 60,
            })
            gleipnir.identified = True
            gleipnir.x, gleipnir.y = fx, fy
            self.ground_items.append(gleipnir)
            self.add_message(
                "The six impossible ingredients dissolve into the forge's flames...", 'info')
            self.add_message(
                "A shimmering ribbon materializes, thin as silk but unbreakable — "
                "GLEIPNIR, the binding that held the World-Wolf!", 'success')
            _snd.play('equip')
            self._log_chronicle("Fed six impossible things to the Dwarven Forge. The flames consumed them all. What came out was a ribbon, thin as silk. Gleipnir. I can't break it. Nothing can.")

    def _check_vidar_altar(self, vx, vy):
        """Check if 10 leather scraps are at Vidar's Altar."""
        on_altar = [i for i in self.ground_items
                    if getattr(i, 'id', '') == 'leather_scrap'
                    and i.x == vx and i.y == vy]
        if len(on_altar) >= 10:
            # Consume all scraps, create Vidar's Sandal
            for scrap in on_altar[:10]:
                self.ground_items.remove(scrap)
            from items import load_items, copy_at
            armors = load_items('armor')
            sandal_t = next((a for a in armors if a.id == 'vidars_sandal'), None)
            if sandal_t:
                sandal = copy_at(sandal_t, vx, vy)
                sandal.identified = True
                self.ground_items.append(sandal)
                self.add_message(
                    "The leather scraps melt together on the ancient altar...", 'info')
                self.add_message(
                    "They reshape into a massive sandal of primordial leather — "
                    "VIDAR'S SANDAL. The Silent God's weapon against the World-Wolf.", 'success')
                _snd.play('equip')
                self._log_chronicle("Piled leather scraps on an ancient altar. They melted together into a massive sandal. Vidar's Sandal. The Silent God's secret weapon.")

    def _dig_grave(self):
        """Dig up a grave -- geography quiz determines outcome."""
        self.add_message("You begin disturbing the grave...", 'info')
        self.quiz_title = "GRAVE -- GEOGRAPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_grave(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='geography',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('geography'),
            base_seconds=self.player.get_quiz_timer('geography'),
        )

    def _resolve_grave(self, chain: int):
        """Apply grave-digging effects based on chain score."""
        if not getattr(self, '_chronicle_first_grave', False):
            self._chronicle_first_grave = True
            self._log_chronicle("Dug up a grave. I'm not proud of it, but the dead don't need what's buried with them.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            self.add_message("A restless spirit emerges from the grave!", 'danger')
            self._spawn_at(px, py)
        elif chain == 1:
            gold = _rng.randint(5, 30)
            self.player_gold += gold
            self.add_message(f"You find {gold} gold coins buried with the dead.", 'success')
        elif chain == 2:
            self.add_message("You unearth a buried item!", 'success')
            self._spawn_grave_item(px, py)
        elif chain >= 3:
            gold = _rng.randint(20, 80)
            self.player_gold += gold
            self._spawn_grave_item(px, py)
            self.add_message(f"A rich burial! You find {gold} gold and a buried treasure!", 'success')

        # Grave is consumed
        self.dungeon.tiles[py][px] = FLOOR
        self.add_message("The grave has been disturbed.", 'info')

    def _spawn_grave_item(self, x: int, y: int):
        """Spawn a random level-appropriate item at (x, y) from the grave."""
        import copy
        from items import load_items
        templates = []
        for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'scroll', 'potion'):
            try:
                templates += [t for t in load_items(cls_name)
                              if getattr(t, 'min_level', 1) <= self.dungeon_level]
            except FileNotFoundError:
                pass
        if templates:
            item = copy.copy(random.choice(templates))
            item.x, item.y = x, y
            self.ground_items.append(item)

    def _sit_throne(self):
        """Sit upon the throne -- history quiz determines outcome."""
        self.add_message("You settle onto the ancient throne...", 'info')
        self.quiz_title = "THRONE -- HISTORY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_throne(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='history',
            tier=1,
            callback=on_complete,
            max_chain=6,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('history'),
            base_seconds=self.player.get_quiz_timer('history'),
        )

    def _resolve_throne(self, chain: int):
        """Apply throne effects based on chain score."""
        if not getattr(self, '_chronicle_first_throne', False):
            self._chronicle_first_throne = True
            self._log_chronicle("Sat on a throne in the dark. It fit perfectly. That worries me.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            outcome = _rng.choice(['shock', 'curse', 'summon'])
            if outcome == 'shock':
                dmg = _rng.randint(5, 15)
                self.player.take_damage(dmg, 'lightning')
                self.add_message(f"The throne shocks you for {dmg} damage!", 'danger')
            elif outcome == 'curse':
                self.player.add_effect('weakened', 20)
                self.add_message("A curse settles over you! You feel weakened.", 'danger')
            else:
                self.add_message("Guards materialize to defend the throne!", 'danger')
                for _ in range(2):
                    self._spawn_at(px, py)
        elif chain == 1:
            gold = _rng.randint(10, 50)
            self.player_gold += gold
            self.add_message(f"You find {gold} gold wedged in the cushions.", 'success')
        elif chain == 2:
            self.player.restore_hp(max(20, self.player.max_hp // 5))
            self.add_message("The throne's enchantment heals your wounds!", 'success')
        elif chain == 3:
            count = 0
            for item in self.player.inventory:
                if not getattr(item, 'identified', True):
                    item.identified = True
                    self.player.known_item_ids.add(item.id)
                    count += 1
            if count:
                self.add_message(f"Royal insight! {count} items identified!", 'success')
            else:
                self.add_message("Royal insight fills you, but all your items are known.", 'info')
        elif chain == 4:
            bonus = _rng.randint(5, 15)
            self.player.max_hp += bonus
            self.player.hp = min(self.player.hp + bonus, self.player.max_hp)
            self.add_message(f"The throne's blessing strengthens you! +{bonus} max HP!", 'success')
        elif chain >= 5:
            stats = _rng.sample(['STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'], 2)
            for s in stats:
                self.player.apply_stat_bonus(s, 1)
            self.add_message(f"The throne crowns you worthy! +1 {stats[0]}, +1 {stats[1]}!", 'success')

        # 33% chance throne crumbles
        if _rng.random() < 0.33:

            self.dungeon.tiles[py][px] = FLOOR
            self.add_message("The ancient throne crumbles to dust.", 'info')

    # ------------------------------------------------------------------
    # Prayer  (\ key -- theology escalator_chain quiz)
    # ------------------------------------------------------------------

    def _start_pray(self):
        """Begin a prayer -- escalator chain quiz (theology). Cooldown-gated."""
        # Altar of the Last Judgment on L99: special one-time judgment
        if self.dungeon_level == 99:
            jpos = getattr(self.dungeon, 'judgment_altar_pos', None)
            if jpos and (self.player.x, self.player.y) == jpos:
                if hasattr(self, '_judgment_resolved'):
                    self.add_message("The altar is silent. It has already spoken.", 'info')
                    return
                self._judgment_resolved = True
                self._resolve_judgment()
                return

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
        self.quiz_title = "PRAYER -- THEOLOGY"
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
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _resolve_prayer(self, chain: int, at_altar: bool = False):
        """Apply prayer blessings based on chain score. Higher chain = greater boon."""
        if at_altar and not getattr(self, '_chronicle_first_prayer', False):
            self._chronicle_first_prayer = True
            self._log_chronicle("Prayed at an altar. Something listened. I felt it.")
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

        # L100 altar: holy fire strips Abaddon's resistances
        if self.dungeon_level == 100 and at_altar:
            pos = (p.x, p.y)
            if pos in self._l100_altars_used:
                self.add_message("This altar's holy power has been spent.", 'info')
            elif chain > 0:
                turns = chain * 2
                self.abaddon_resist_removed_turns += turns
                abaddon = next((m for m in self.monsters
                                if m.alive and m.kind == 'abaddon_destroyer'), None)
                if abaddon:
                    abaddon.resistances = []
                    self.add_message(
                        f"Holy fire surges around the Destroyer! "
                        f"His defenses crumble for {turns} turns!", 'success')
                else:
                    self.add_message(
                        "Holy fire blazes forth but finds no target.", 'info')
                self._l100_altars_used.add(pos)
                # Show verse
                verse = _PRAYER_VERSES.get(min(chain, 8))
                if verse:
                    self.add_message(f'"{verse[0]}" \u2014 {verse[1]}', 'info')
                p.prayer_cooldown = max(100, 80 + effective * 25)
                return
            else:
                self.add_message("The heavens are silent.", 'info')
                self._l100_altars_used.add(pos)
                return

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

        # Prayer can freeze Death — desperate measure during the chase
        if self.death_pursues and self.death_monster is not None:
            freeze_turns = min(8, 3 + effective)  # 4-8 turns depending on chain
            self.death_monster._frozen_turns = freeze_turns
            self.add_message(
                f"Holy light blazes! Death recoils, frozen for {freeze_turns} turns!", 'success')
            self._log_chronicle(f"Prayed while Death hunted me. It froze in place. {freeze_turns} turns. That's all I get.")

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
                    if slot and getattr(slot, 'buc', 'uncursed') == 'cursed':
                        cursed_items.append(slot)
                if p.shield and getattr(p.shield, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.shield)
                if p.weapon and getattr(p.weapon, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.weapon)
                if p.ranged_weapon and getattr(p.ranged_weapon, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.ranged_weapon)
                for acc in getattr(p, 'accessory_slots', []):
                    if acc and getattr(acc, 'buc', 'uncursed') == 'cursed':
                        cursed_items.append(acc)
                if cursed_items:
                    for target in cursed_items:
                        target.buc = 'uncursed'
                        target.buc_known = True
                    if len(cursed_items) == 1:
                        msgs.append(f"The curse on your {cursed_items[0].name} is broken!")
                    else:
                        msgs.append(f"Divine light purifies {len(cursed_items)} cursed items!")
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
            self.add_message(f"  -- {citation}", 'info')

    # ------------------------------------------------------------------
    # Recall Lore
    # ------------------------------------------------------------------

    def _has_tablet_of_destinies(self) -> bool:
        """Check if player is carrying the Tablet of Destinies artifact."""
        return any(getattr(i, 'id', '') == 'tablet_of_destinies' for i in self.player.inventory)

    def _on_quiz_answer(self, is_correct: bool):
        """Fired after every individual quiz answer to tally global stats."""
        if is_correct:
            self.correct_answers += 1
            _snd.play('quiz_correct')
        else:
            self.wrong_answers += 1
            _snd.play('quiz_wrong')
            # Store missed question for post-death review
            qe = self.quiz_engine
            q = qe.current_question
            if q:
                self.missed_questions.append({
                    'subject': qe.subject,
                    'question': q.get('question', ''),
                    'correct': str(q.get('answer', '')),
                    'chosen': qe.last_answer,
                    'context': q.get('context', ''),
                })
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
        """Begin a Recall Lore session -- escalator chain trivia quiz. Cooldown-gated."""
        if self.player.recall_lore_cooldown > 0:
            self.add_message(
                f"Your mind needs rest before recalling more lore. "
                f"({self.player.recall_lore_cooldown} turns remain)", 'warning'
            )
            return
        self.add_message("You close your eyes and search your memory...", 'info')
        self.quiz_title = "RECALL LORE -- TRIVIA"
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
            base_seconds=self.player.get_quiz_timer('trivia'),
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
        # Save to lore hints journal (avoid duplicates)
        if hint not in self._recalled_hints:
            self._recalled_hints.append(hint)

    # ------------------------------------------------------------------
    # XYZZY — Hack Reality (hidden feature)
    # ------------------------------------------------------------------

    def _open_xyzzy_input(self):
        """Open the hidden green terminal for entering the magic word."""
        self._xyzzy_text = ''
        self._xyzzy_blink = 0
        self.state = STATE_XYZZY_INPUT

    def _xyzzy_input(self, key, unicode_char):
        """Handle typing in the XYZZY terminal."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        if key == pygame.K_RETURN:
            if self._xyzzy_text.strip().lower() == 'xyzzy':
                self.state = STATE_XYZZY_CONFIRM
                self._xyzzy_confirm_sel = 0  # 0=Yes, 1=No
            else:
                self.add_message("Nothing happens.", 'info')
                self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self._xyzzy_text = self._xyzzy_text[:-1]
            return
        # Accept printable characters (max 20 chars)
        if unicode_char and len(unicode_char) == 1 and unicode_char.isprintable() and len(self._xyzzy_text) < 20:
            self._xyzzy_text += unicode_char

    def _xyzzy_confirm_input(self, key):
        """Handle the Yes/No confirmation dialog."""
        if key == pygame.K_ESCAPE or key == pygame.K_n:
            self.add_message("You step back from the edge of reality.", 'info')
            self.state = STATE_PLAYER
            return
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._xyzzy_confirm_sel = 1 - self._xyzzy_confirm_sel
            return
        if key == pygame.K_y or (key == pygame.K_RETURN and self._xyzzy_confirm_sel == 0):
            self._start_hack_reality()
            return
        if key == pygame.K_RETURN and self._xyzzy_confirm_sel == 1:
            self.add_message("You step back from the edge of reality.", 'info')
            self.state = STATE_PLAYER

    def _start_hack_reality(self):
        """Begin a Hack Reality session -- escalator chain AI quiz. Cooldown-gated."""
        if self.player.hack_reality_cooldown > 0:
            self.add_message("Reality is still stabilizing...", 'warning')
            self.state = STATE_PLAYER
            return
        self.add_message("You speak the First Word. Reality shudders...", 'info')
        self.quiz_title = "HACK REALITY -- AI"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_hack_reality(chain)
            self.state = STATE_HACK_REALITY
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='ai',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('ai'),
            base_seconds=self.player.get_quiz_timer('ai'),
        )

    def _resolve_hack_reality(self, chain: int):
        """Apply XYZZY hack reality rewards. Tier 1 always granted; tiers 2-5 once only."""
        import random as _rng
        p = self.player

        # Cooldown: long (150-300 turns); longer for better rewards
        if chain == 0:
            p.hack_reality_cooldown = 100
            self.add_message("SEGFAULT. Reality rejects your invocation.", 'warning')
            self._hack_result_lines = [("XYZZY FAILED", (255, 60, 60))]
            self._hack_result_chain = 0
            return

        p.hack_reality_cooldown = 150 + chain * 30   # 180 .. 300 turns
        if not getattr(self, '_chronicle_first_xyzzy', False):
            self._chronicle_first_xyzzy = True
            self._log_chronicle("Spoke an old word of power. XYZZY. Reality flickered. Something changed. I don't think I was supposed to know that word.")

        msgs = []
        result_lines = []

        _HACK_LABELS = {
            1: "ECHO",
            2: "RESONANCE",
            3: "CONVERGENCE",
            4: "TRANSCENDENCE",
            5: "SINGULARITY",
        }
        result_lines.append((_HACK_LABELS.get(chain, "XYZZY"), (0, 255, 180)))

        # --- Tier 1 (always): Full HP/SP/MP restore, remove ALL status effects ---
        p.hp = p.max_hp
        p.sp = p.max_sp
        p.mp = p.max_mp
        _ALL_NEGATIVES = ['poisoned', 'paralyzed', 'confused', 'bleeding',
                          'blinded', 'sleeping', 'slowed', 'weakened', 'cursed',
                          'feared', 'burning', 'diseased', 'immobilized',
                          'petrifying', 'aggravated']
        removed = []
        for neg in _ALL_NEGATIVES:
            if p.status_effects.get(neg, 0) > 0:
                p.status_effects.pop(neg, None)
                removed.append(neg)
        result_lines.append(("Reality rewrites your body: HP/SP/MP fully restored", (100, 255, 160)))
        if removed:
            result_lines.append((f"Purged: {', '.join(removed)}", (180, 255, 180)))
        msgs.append("The First Word restores you completely.")

        # --- Tier 2 (once): Random permanent positive status effect ---
        if chain >= 2 and 2 not in p.hack_tiers_claimed:
            p.hack_tiers_claimed.add(2)
            _POSITIVE_EFFECTS = [
                ('regenerating', 'Regeneration'),
                ('hasted', 'Haste'),
                ('see_invisible', 'See Invisible'),
                ('fire_shield', 'Fire Shield'),
                ('cold_shield', 'Cold Shield'),
                ('reflecting', 'Reflection'),
                ('displacement', 'Displacement'),
                ('drain_resist', 'Drain Resistance'),
            ]
            eff_id, eff_name = _rng.choice(_POSITIVE_EFFECTS)
            p.add_effect(eff_id, -1)  # -1 = permanent
            result_lines.append((f"Permanent effect gained: {eff_name}", (100, 200, 255)))
            msgs.append(f"Reality grants you permanent {eff_name}!")

        # --- Tier 3 (once): Boost ALL stats by 5 ---
        if chain >= 3 and 3 not in p.hack_tiers_claimed:
            p.hack_tiers_claimed.add(3)
            for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                p.apply_stat_bonus(stat, 5)
            result_lines.append(("All stats permanently +5!", (255, 220, 80)))
            msgs.append("Reality rewrites your very essence — all stats +5!")

        # --- Tier 4 (once): Random legendary item ---
        if chain >= 4 and 4 not in p.hack_tiers_claimed:
            p.hack_tiers_claimed.add(4)
            item = self._hack_reality_spawn_legendary()
            if item:
                result_lines.append((f"Materialized: {item.name}", (255, 180, 255)))
                msgs.append(f"Reality bends — {item.name} materializes at your feet!")
            else:
                # Fallback: extra +3 to all stats
                for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                    p.apply_stat_bonus(stat, 3)
                result_lines.append(("No legendary found — all stats +3 instead!", (255, 220, 80)))
                msgs.append("Reality overflows — all stats +3!")

        # --- Tier 5 (once): Summon Fenrir wolf pet ---
        if chain >= 5 and 5 not in p.hack_tiers_claimed:
            p.hack_tiers_claimed.add(5)
            fenrir = self._spawn_fenrir_pet()
            if fenrir:
                result_lines.append(("Fenrir, the World-Devourer, answers your call!", (180, 200, 255)))
                msgs.append("A colossal wolf tears through the fabric of reality — Fenrir is yours!")
            else:
                # Fallback if no room
                for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                    p.apply_stat_bonus(stat, 3)
                result_lines.append(("No room for Fenrir — all stats +3 instead!", (255, 220, 80)))
                msgs.append("Fenrir's howl echoes but fades — reality compensates with raw power.")

        # Re-restore to full after stat bonuses may have raised maximums
        p.hp = p.max_hp
        p.sp = p.max_sp
        p.mp = p.max_mp

        for msg in msgs:
            self.add_message(msg, 'good')

        self._hack_result_lines = result_lines
        self._hack_result_chain = chain

    def _hack_reality_spawn_legendary(self):
        """Spawn a random named-legendary item at the player's feet."""
        import random as _rng
        from items import load_items, copy_at
        _MATERIAL_PREFIXES = ('iron_', 'steel_', 'mithril_', 'adamantine_',
                              'dragonbone_', 'bronze_', 'elven_', 'orcish_', 'dwarven_')
        p = self.player
        legendary_pool = []
        for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll', 'ammo'):
            try:
                for item in load_items(cls_name):
                    if getattr(item, 'container_loot_tier', '') == 'legendary':
                        if not any(item.id.startswith(pfx) for pfx in _MATERIAL_PREFIXES):
                            legendary_pool.append(item)
            except FileNotFoundError:
                pass
        if not legendary_pool:
            return None
        template = _rng.choice(legendary_pool)
        item = copy_at(template, p.x, p.y)
        self.ground_items.append(item)
        return item

    def _spawn_fenrir_pet(self):
        """Spawn Fenrir wolf pet near the player. Returns the pet or None."""
        px, py = self.player.x, self.player.y
        # Find a free walkable tile near the player
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = px + dx, py + dy
                if nx == px and ny == py:
                    continue
                if not self.dungeon.is_walkable(nx, ny):
                    continue
                if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                    continue
                if any(p.alive and p.x == nx and p.y == ny for p in self.pets):
                    continue
                fenrir = FenrirPet(nx, ny)
                self.pets.append(fenrir)
                return fenrir
        return None


    # ------------------------------------------------------------------
    # Quirks screen
    # ------------------------------------------------------------------

    def _open_quirks_screen(self):
        self._quirks_scroll = 0
        qs = getattr(self, 'quirk_system', None)
        if qs:
            self._quirks_data = qs.get_all_quirk_info()
        else:
            self._quirks_data = []
        self.state = STATE_QUIRKS

    def _quirks_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_w, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER
            return
        if key in (pygame.K_UP, pygame.K_k):
            self._quirks_scroll = max(0, self._quirks_scroll - 1)
        elif key in (pygame.K_DOWN, pygame.K_j):
            self._quirks_scroll += 1
        elif key == pygame.K_PAGEUP:
            self._quirks_scroll = max(0, self._quirks_scroll - 10)
        elif key == pygame.K_PAGEDOWN:
            self._quirks_scroll += 10
        elif key == pygame.K_HOME:
            self._quirks_scroll = 0
        elif key == pygame.K_END:
            self._quirks_scroll = max(0, len(self._quirks_data) - 1)


    # ------------------------------------------------------------------
    # Character sheet  (@)
    # ------------------------------------------------------------------

    def _open_character_sheet(self):
        self._charsheet_scroll = 0
        self.state = STATE_CHARACTER_SHEET

    def _character_sheet_input(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER
            return
        if key in (pygame.K_UP, pygame.K_k):
            self._charsheet_scroll = max(0, self._charsheet_scroll - 1)
        elif key in (pygame.K_DOWN, pygame.K_j):
            self._charsheet_scroll += 1
        elif key == pygame.K_PAGEUP:
            self._charsheet_scroll = max(0, self._charsheet_scroll - 10)
        elif key == pygame.K_PAGEDOWN:
            self._charsheet_scroll += 10
        elif key == pygame.K_HOME:
            self._charsheet_scroll = 0
        elif key == pygame.K_END:
            self._charsheet_scroll = 9999


    def _get_effect_source(self, effect_id: str) -> str:
        """Try to determine what's causing a status effect."""
        p = self.player
        # Check weapon on_equip_status
        if p.weapon and getattr(p.weapon, 'on_equip_status', '') == effect_id:
            return p.weapon.name
        # Check armor on_equip_status
        for slot in p.armor_slots:
            if slot and getattr(slot, 'on_equip_status', '') == effect_id:
                return slot.name
        # Check shield
        if p.shield and getattr(p.shield, 'on_equip_status', '') == effect_id:
            return p.shield.name
        # Check accessories (ring/amulet effects)
        for acc in p.accessory_slots:
            if acc and hasattr(acc, 'effects'):
                if acc.effects.get('status') == effect_id:
                    return acc.name
        if p.amulet_slot and hasattr(p.amulet_slot, 'effects'):
            if p.amulet_slot.effects.get('status') == effect_id:
                return p.amulet_slot.name
        # Timed effects are likely from potions/wands/monsters
        dur = p.status_effects.get(effect_id, 0)
        if dur == -1:
            return "permanent"
        return ""

    # ------------------------------------------------------------------
    # Equip menu
    # ------------------------------------------------------------------

    # Equip menu tab definitions: (label, filter_func_or_None)
    _LETTERS = 'abcdefghijklmnopqrstuvwxyz'

    _EQUIP_TABS = [
        ('Weapons',     lambda i: isinstance(i, Weapon)),
        ('Armor',       lambda i: isinstance(i, Armor)),
        ('Shields',     lambda i: isinstance(i, Shield)),
        ('Accessories', lambda i: isinstance(i, Accessory)),
        ('Unequip',     None),  # special tab for currently equipped items
    ]

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
        elif slot_name == 'ranged_weapon':
            self.player.ranged_weapon = None
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
                if 'stat2' in fx:
                    self.player.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                if 'status' in fx:
                    self.player.status_effects.pop(fx['status'], None)
        elif slot_name == 'amulet':
            self.player.amulet_slot = None
            from items import Accessory as _Acc
            if isinstance(item, _Acc):
                fx = item.effects
                if 'stat' in fx:
                    self.player.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                if 'stat2' in fx:
                    self.player.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                if 'status' in fx:
                    self.player.status_effects.pop(fx['status'], None)
        self.player.inventory.append(item)
        self.add_message(f"You remove the {self._display_name(item)}.", 'info')
        _qs_uneq = getattr(self, 'quirk_system', None)
        if _qs_uneq:
            itype = 'weapon' if slot_name in ('weapon', 'ranged_weapon') else \
                    'shield' if slot_name == 'shield' else \
                    'armor' if slot_name not in ('amulet',) and not slot_name.startswith('accessory_') else \
                    'accessory'
            _qs_uneq.on_item_unequipped(item.id, itype, slot_name)
        self._advance_turn()

    def _start_armor_quiz(self, item):
        """Launch geography threshold quiz to equip armor or shield."""
        item_name = self._display_name(item)
        cursed_tag = " (cursed)" if getattr(item, 'cursed', False) else ""
        self.quiz_title = f"EQUIPPING {item_name.upper()}  --  GEOGRAPHY"
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
            base_seconds=self.player.get_quiz_timer('geography'),
        )

    # ------------------------------------------------------------------
    # Accessory menu  (r key -- history quiz)
    # ------------------------------------------------------------------

    def _equip_accessory(self, item: 'Accessory'):
        # Check for a free slot (amulets use separate amulet_slot, not ring slots)
        is_amulet = getattr(item, 'slot', '') == 'amulet'
        if is_amulet:
            if self.player.amulet_slot is not None:
                self.add_message("You are already wearing an amulet!", 'warning')
                return
        elif all(s is not None for s in self.player.accessory_slots):
            self.add_message("All ring slots are full!", 'warning')
            return

        item_name = self._display_name(item)
        self.quiz_title = f"EQUIPPING {item_name.upper()}  --  HISTORY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                self.player._apply_equip(item)
                self.player.remove_from_inventory(item)
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
            base_seconds=self.player.get_quiz_timer('history'),
        )

    # ------------------------------------------------------------------
    # Wand menu  (u key -- science quiz)
    # ------------------------------------------------------------------

    def _invoke_wand(self, wand: 'Wand'):
        # Philosopher's Wrench: no quiz -- it's a tool, not magic
        if wand.id == 'philosophers_wrench':
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            self._use_philosophers_wrench()
            self._advance_turn()
            return

        # Flux Capacitor: no quiz -- it's a gift from the universe
        if wand.id == 'flux_capacitor':
            wand.charges -= 1
            self.player.add_effect('time_stopped', 10)
            self.add_message("The Flux Capacitor ignites! Time freezes around you -- 10 turns!", 'success')
            if wand.charges <= 0:
                self.add_message("The Flux Capacitor burns out in a shower of sparks.", 'warning')
                self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        if wand.charges <= 0:
            self.add_message("The wand is empty -- it crumbles to dust.", 'warning')
            self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        # Combat wands: open targeting cursor first (like ranged weapons)
        _TARGETED_EFFECTS = {
            'sleep_monster', 'slow_monster', 'confuse_monster', 'paralyze_monster',
            'blind_monster', 'stoning', 'fire_bolt', 'cold_bolt', 'lightning_bolt',
            'acid_spray', 'magic_missile', 'striking', 'death_ray', 'cancellation',
            'polymorph_monster', 'fear_monster', 'charm_monster', 'poison_monster',
            'disease_monster', 'curse_monster', 'teleport_monster', 'drain_life',
            'disintegrate', 'weaken_monster', 'drain_magic', 'dispel_magic',
        }
        if wand.effect in _TARGETED_EFFECTS:
            self._pending_wand = wand
            self._wand_targeting = True
            self._melee_targeting = False
            self._throw_targeting = False
            self._observe_targeting = False
            px, py = self.player.x, self.player.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            self._target_candidates = candidates
            self._target_idx = 0
            if candidates:
                self.target_cursor_x = candidates[0].x
                self.target_cursor_y = candidates[0].y
            else:
                self.target_cursor_x = px
                self.target_cursor_y = py
            self.state = STATE_TARGET
            self.add_message(
                "Aim wand -- arrow keys to target, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info'
            )
            return

        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  --  SCIENCE"
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
            # Cursed wands: 3% chance to misfire (wastes charge, no effect)
            import random as _rng_wand
            if getattr(wand, 'buc', 'uncursed') == 'cursed' and _rng_wand.random() < 0.03:
                self.add_message("The cursed wand misfires! The charge is wasted.", 'warning')
                if wand.charges <= 0:
                    self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                    self.player.remove_from_inventory(wand)
                self._advance_turn()
                return
            self._apply_wand_effect(wand)
            if wand.charges <= 0:
                self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                self.player.remove_from_inventory(wand)
            else:
                self.add_message(
                    f"({wand.charges}/{wand.max_charges} charges remain)", 'info'
                )
            self._advance_turn()

        # All wands use threshold quiz — power is baked into the wand's tier
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
            base_seconds=self.player.get_quiz_timer('science'),
        )

    def _boss_resist_cc(self, target, duration: int) -> tuple:
        """Boss CC resistance: 50% chance to resist; if it lands, half duration.
        Returns (adjusted_duration, resisted_bool)."""
        import random as _rng
        is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
        if not is_boss:
            return duration, False
        if _rng.random() < 0.50:
            return 0, True
        return max(1, duration // 2), False

    def _int_scaled_damage(self, base_dmg: int) -> int:
        """Scale magic damage by INT: 1.0x at INT 0, 2.0x at INT 10, 3.0x at INT 20."""
        return max(1, int(base_dmg * (1.0 + self.player.INT * 0.1)))

    _wand_tier_duration = staticmethod(wand_tier_duration)

    def _wand_tier_damage(self, base_dmg: int, tier: int) -> int:
        """Scale wand damage by tier AND player INT."""
        tier_mult = 0.5 + tier * 0.5  # T1=1.0, T3=2.0, T5=3.0
        return max(1, int(base_dmg * tier_mult * (1.0 + self.player.INT * 0.1)))

    def _apply_wand_effect(self, wand: 'Wand'):
        import random as _rng
        from dice import roll
        effect = wand.effect

        # -- CHARACTER EFFECTS ------------------------------------------------
        if effect == 'heal':
            amount = roll(wand.power) if wand.power else 8
            self.player.restore_hp(amount)
            self.add_message(f"The wand heals you for {amount} HP!", 'success')

        elif effect == 'extra_heal':
            amount = (roll(wand.power) if wand.power else 20) + 10
            self.player.restore_hp(amount)
            self.add_message(f"Intense healing washes over you -- {amount} HP restored!", 'success')

        elif effect == 'restore_body':
            self.player.hp = self.player.max_hp
            self.player.sp = self.player.max_sp
            self.player.mp = self.player.max_mp
            self.add_message("Your body is fully restored!", 'success')

        elif effect == 'haste_self':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            self.player.add_effect('hasted', dur)
            self.add_message(f"You feel supernaturally swift! ({dur} turns)", 'success')

        elif effect == 'invisibility_self':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('invisible', dur)
            self.add_message(f"You fade from sight! ({dur} turns)", 'success')

        elif effect == 'levitation_self':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            self.player.add_effect('levitating', dur)
            self.add_message(f"You rise gently off the ground! ({dur} turns)", 'success')

        elif effect == 'teleport_self':
            self._teleport_player()

        # -- WORLD EFFECTS ----------------------------------------------------
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
                else "The wand hums -- nothing to dig here.", 'success' if opened else 'info'
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
            import json
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
                        self.add_message(f"{self._a_or_an(defn['name']).capitalize()} materialises from the ether!", 'danger')
                    else:
                        self.add_message("The wand sputters -- no room for a monster nearby.", 'info')
            except Exception:
                self.add_message("The wand misfires!", 'warning')

        # -- STATUS EFFECTS ON TARGET -----------------------------------------
        elif effect in ('sleep_monster', 'slow_monster', 'confuse_monster',
                        'paralyze_monster', 'blind_monster', 'stoning',
                        'fire_bolt', 'cold_bolt', 'lightning_bolt',
                        'acid_spray', 'magic_missile', 'striking',
                        'death_ray', 'cancellation', 'polymorph_monster',
                        'fear_monster', 'charm_monster', 'poison_monster',
                        'disease_monster', 'curse_monster', 'teleport_monster',
                        'drain_life', 'disintegrate', 'weaken_monster',
                        'drain_magic', 'dispel_magic'):
            target = getattr(self, '_wand_override_target', None) or self._nearest_visible_monster()
            if target is None:
                self.add_message("The wand hums but finds no target.", 'info')
                return

            if effect == 'sleep_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the sleep!", 'warning')
                else:
                    target.add_effect('sleeping', dur)
                    self.add_message(f"The {target.name} slumps into a deep sleep! ({dur} turns)", 'success')

            elif effect == 'slow_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic!", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} slows to a crawl! ({dur} turns)", 'success')

            elif effect == 'confuse_monster':
                dur = self._wand_tier_duration(10, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the confusion!", 'warning')
                else:
                    target.add_effect('confused', dur)
                    self.add_message(f"The {target.name} staggers in confusion! ({dur} turns)", 'success')

            elif effect == 'paralyze_monster':
                dur = self._wand_tier_duration(6, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} resists the paralysis!", 'warning')
                else:
                    target.add_effect('paralyzed', dur)
                    self.add_message(f"The {target.name} is locked in place! ({dur} turns)", 'success')

            elif effect == 'blind_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the blindness!", 'warning')
                else:
                    target.add_effect('blinded', dur)
                    self.add_message(f"The {target.name} claws at its eyes, blinded! ({dur} turns)", 'success')

            elif effect == 'stoning':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is far too powerful to petrify!", 'warning')
                else:
                    dur = self._wand_tier_duration(5, wand.quiz_tier)
                    target.add_effect('petrifying', dur)
                    self.add_message(f"The {target.name} begins to turn to stone! ({dur} turns)", 'success')

            elif effect == 'cancellation':
                target.status_effects.clear()
                self.add_message(
                    f"The {target.name}'s abilities and effects are cancelled!", 'success'
                )

            elif effect == 'fire_bolt':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 6, wand.quiz_tier)
                actual = target.take_damage(dmg)
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'cold_bolt':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 4, wand.quiz_tier)
                actual = target.take_damage(dmg)
                dur = self._wand_tier_duration(4, wand.quiz_tier)
                dur, sr = self._boss_resist_cc(target, dur)
                if not sr:
                    target.add_effect('slowed', dur)
                self.add_message(
                    f"A bolt of cold strikes the {target.name} for {actual} damage"
                    + (f" and slows it! ({dur} turns)" if not sr else "!"), 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'lightning_bolt':
                from combat import get_line_tiles
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 10, wand.quiz_tier)
                px, py = self.player.x, self.player.y
                line = get_line_tiles(px, py, target.x, target.y)
                line_set = set(line)
                line_hits = [m for m in self.monsters
                             if m.alive and (m.x, m.y) in line_set and (m.x, m.y) in self.visible]
                for lm in line_hits:
                    actual = lm.take_damage(dmg)
                    if actual > 0:
                        sd, sr = self._boss_resist_cc(lm, 3)
                        if not sr:
                            lm.add_effect('stunned', sd)
                    if not lm.alive:
                        self._on_monster_killed(lm)
                if len(line_hits) > 1:
                    self.add_message(
                        f"Lightning arcs through {len(line_hits)} creatures for {dmg} damage each!", 'success')
                elif line_hits:
                    self.add_message(
                        f"Lightning strikes the {line_hits[0].name} for {dmg} damage!", 'success')
                else:
                    self.add_message("The lightning dissipates harmlessly.", 'info')

            elif effect == 'acid_spray':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 4, wand.quiz_tier)
                actual = target.take_damage(dmg)
                dur = self._wand_tier_duration(6, wand.quiz_tier)
                dur, sr = self._boss_resist_cc(target, dur)
                if not sr:
                    target.add_effect('diseased', dur)
                self.add_message(
                    f"Acid dissolves the {target.name} for {actual} damage"
                    + (f" -- diseased for {dur} turns!" if not sr else "!"), 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'magic_missile':
                # Irresistible: bypasses all resistances. Missile count = wand tier.
                missiles = max(1, wand.quiz_tier)
                total_dmg = 0
                for _ in range(missiles):
                    if not target.alive:
                        break
                    dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 5, wand.quiz_tier)
                    target.hp = max(0, target.hp - dmg)
                    if target.hp == 0:
                        target.alive = False
                    total_dmg += dmg
                self.add_message(
                    f"{missiles} magic missile{'s' if missiles > 1 else ''} "
                    f"unerringly strike{'s' if missiles == 1 else ''} the "
                    f"{target.name} for {total_dmg} total damage!", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'striking':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 10, wand.quiz_tier)
                actual = target.take_damage(dmg)
                self.add_message(
                    f"The wand slams into the {target.name} for {actual} physical damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'death_ray':
                # 70% chance instant kill; remaining HP otherwise. Bosses immune to instant kill.
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if not is_boss and _rng.random() < 0.70:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is slain instantly by the death ray!", 'success')
                    self._on_monster_killed(target)
                else:
                    dmg = max(1, target.max_hp // 2)
                    actual = target.take_damage(dmg)
                    if is_boss:
                        self.add_message(
                            f"The death ray strikes the {target.name} for {actual} damage! "
                            f"The creature is too powerful for an instant kill.", 'success')
                    else:
                        self.add_message(
                            f"The death ray grazes the {target.name} for {actual} damage!", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'polymorph_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the transformation!", 'warning')
                else:
                    import json
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
                                f"The {old_name} warps into {self._a_or_an(new_m.name)}!", 'success'
                            )
                        else:
                            self.add_message("The polymorph wand finds no suitable form.", 'info')
                    except Exception:
                        self.add_message("The wand misfires!", 'warning')

            elif effect == 'fear_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the fear!", 'warning')
                else:
                    dur = self._wand_tier_duration(8, wand.quiz_tier)
                    target.add_effect('feared', dur)
                    target.ai_pattern = 'cowardly'
                    self.add_message(f"The {target.name} turns and flees in terror! ({dur} turns)", 'success')

            elif effect == 'charm_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is far too willful to charm!", 'warning')
                else:
                    dur = self._wand_tier_duration(20, wand.quiz_tier)
                    target.add_effect('charmed', dur)
                    target.ai_pattern = 'sessile'
                    self.add_message(f"The {target.name} gazes at you with adoration. ({dur} turns)", 'success')

            elif effect == 'poison_monster':
                dur = self._wand_tier_duration(12, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the poison!", 'warning')
                else:
                    target.add_effect('poisoned', dur)
                    self.add_message(f"The {target.name} writhes as poison courses through it! ({dur} turns)", 'success')

            elif effect == 'disease_monster':
                dur = self._wand_tier_duration(15, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the disease!", 'warning')
                else:
                    target.add_effect('diseased', dur)
                    actual = target.take_damage(max(1, target.max_hp // 5))
                    self.add_message(f"The {target.name} is wracked by disease! ({actual} dmg, {dur} turns)", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'curse_monster':
                dur = self._wand_tier_duration(20, wand.quiz_tier)
                sdur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the curse!", 'warning')
                else:
                    sdur = max(1, sdur // 2) if (getattr(target, 'is_boss', False) or target.max_hp > 500) else sdur
                    target.add_effect('cursed', dur)
                    target.add_effect('slowed', sdur)
                    self.add_message(f"Dark energy envelops the {target.name}! Cursed ({dur}t) and slowed ({sdur}t).", 'success')

            elif effect == 'teleport_monster':
                open_tiles = [(x, y)
                              for y in range(len(self.dungeon.tiles))
                              for x in range(len(self.dungeon.tiles[y]))
                              if self.dungeon.is_walkable(x, y)
                              and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                              and not any(p.alive and p.x == x and p.y == y for p in self.pets)
                              and (x, y) != (self.player.x, self.player.y)]
                if open_tiles:
                    tx, ty = _rng.choice(open_tiles)
                    old_name = target.name
                    target.x, target.y = tx, ty
                    self.add_message(f"The {old_name} vanishes in a flash of light!", 'success')

            elif effect == 'drain_life':
                from dice import roll
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else _rng.randint(3, 10), wand.quiz_tier)
                actual = target.take_damage(dmg)
                heal = min(actual, self.player.max_hp - self.player.hp)
                self.player.hp += heal
                self.add_message(
                    f"You drain {actual} life from the {target.name}! (+{heal} HP)", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'disintegrate':
                # 85% instant kill. Bosses immune to instant kill, take max_hp/3 instead.
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if not is_boss and _rng.random() < 0.85:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is disintegrated!", 'success')
                    self._on_monster_killed(target)
                else:
                    actual = target.take_damage(target.max_hp // 3)
                    if is_boss:
                        self.add_message(
                            f"The {target.name} resists disintegration but takes {actual} damage!", 'success')
                    else:
                        self.add_message(
                            f"The {target.name} is partially disintegrated! ({actual} dmg)", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'weaken_monster':
                dur = self._wand_tier_duration(15, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the weakening magic!", 'warning')
                elif target.attacks:
                    target.add_effect('weakened', dur)
                    self.add_message(f"The {target.name} looks visibly weaker! ({dur} turns)", 'success')
                else:
                    target.add_effect('weakened', dur)
                    self.add_message(f"The {target.name} seems diminished. ({dur} turns)", 'success')

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
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('shielded', dur)
            self.add_message(f"A shimmering barrier surrounds you! ({dur} turns)", 'success')

        elif effect == 'fire_shield':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('fire_shield', dur)
            self.add_message(f"Flames swirl around you! Fire protection for {dur} turns.", 'success')

        elif effect == 'cold_shield':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('cold_shield', dur)
            self.add_message(f"Frost encases you! Cold protection for {dur} turns.", 'success')

        elif effect == 'regeneration_self':
            dur = self._wand_tier_duration(30, wand.quiz_tier)
            self.player.add_effect('regenerating', dur)
            self.add_message(f"You feel your wounds slowly closing. ({dur} turns)", 'success')

        elif effect == 'reflect_self':
            dur = self._wand_tier_duration(20, wand.quiz_tier)
            self.player.add_effect('reflecting', dur)
            self.add_message(f"A reflective aura surrounds you! ({dur} turns)", 'success')

        elif effect == 'phase_self':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('phasing', dur)
            self.add_message(f"You feel briefly incorporeal -- walls seem thin. ({dur} turns)", 'success')

        elif effect == 'detect_monsters':
            for m in self.monsters:
                if m.alive:
                    self.visible.add((m.x, m.y))
            self.add_message("You sense the presence of all nearby creatures!", 'success')

        elif effect == 'detect_treasure':
            for item in self.ground_items:
                self.dungeon.explored.add((item.x, item.y))
            self.add_message("A golden shimmer reveals hidden treasures!", 'success')

        elif effect == 'mapping':
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored.add((x, y))
            self.add_message("The wand maps the entire dungeon level into your mind!", 'success')

        elif effect == 'clairvoyance':
            for y in range(len(self.dungeon.tiles)):
                for x in range(len(self.dungeon.tiles[y])):
                    self.dungeon.explored.add((x, y))
            self.add_message("Your mind expands -- you perceive the entire level!", 'success')

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
            from items import ENCHANT_CAP
            w = self.player.weapon or self.player.ranged_weapon
            if w:
                cap = ENCHANT_CAP.get('weapon', 5)
                if w.enchant_bonus < cap:
                    w.enchant_bonus += 1
                    self.add_message(f"Your {w.name} glows! Enchantment +{w.enchant_bonus}.", 'success')
                else:
                    self.add_message(f"Your {w.name} shudders but can hold no more enchantment.", 'info')
            else:
                self.add_message("You wield no weapon to enchant.", 'warning')

        elif effect == 'earthquake':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            total_dmg = 0
            for m in visible_monsters:
                dmg = self._wand_tier_damage(_rng.randint(5, 20), wand.quiz_tier)
                actual = m.take_damage(dmg)
                total_dmg += actual
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"The earth shakes! {len(visible_monsters)} creatures are battered. ({total_dmg} total dmg)", 'success')

        elif effect == 'explosion':
            from dice import roll
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else _rng.randint(8, 24), wand.quiz_tier)
                actual = m.take_damage(dmg)
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"A massive explosion engulfs the area! ({len(visible_monsters)} creatures hit)", 'success')

        elif effect == 'mass_confuse':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('confused', dur)
            self.add_message(f"A wave of confusion washes over {len(visible_monsters)} creatures! ({dur} turns)", 'success')

        elif effect == 'mass_sleep':
            dur = self._wand_tier_duration(10, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('sleeping', dur)
            self.add_message(f"All visible creatures slump into slumber! ({len(visible_monsters)} affected, {dur} turns)", 'success')

        elif effect == 'mass_slow':
            dur = self._wand_tier_duration(10, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('slowed', dur)
            self.add_message(f"{len(visible_monsters)} creatures are slowed! ({dur} turns)", 'success')

        elif effect == 'time_stop':
            dur = self._wand_tier_duration(5, wand.quiz_tier)
            self.player.add_effect('time_stopped', dur)
            self.add_message(f"Time freezes! You have {dur} turns of free movement.", 'success')

        elif effect == 'wish':
            self.add_message("The wand glows brilliantly... but you cannot yet speak your wish.", 'info')

        elif effect == 'iron_mortar':
            # Baba Yaga's Iron Mortar: the effect is never the same twice
            _chaos = _rng.choice([
                ('heal',       lambda: (self.player.restore_hp(25),
                                        self.add_message("Chaotic healing washes over you! (+25 HP)", 'success'))),
                ('teleport',   lambda: (self._teleport_player(),
                                        self.add_message("The mortar warps you across the level!", 'warning'))),
                ('haste',      lambda: (self.player.add_effect('hasted', 10),
                                        self.add_message("Baba Yaga's magic hastens your step!", 'success'))),
                ('confusion',  lambda: (self.player.add_effect('confused', 8),
                                        self.add_message("The mortar's chaos clouds your mind!", 'danger'))),
                ('mass_sleep', lambda: (
                    [m.add_effect('sleeping', 12) for m in self.monsters if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("The mortar grinds out a sleep-fog over the room!", 'success'))),
                ('regen',      lambda: (self.player.add_effect('regenerating', 20),
                                        self.add_message("Ground-up hero bones restore your vitality!", 'success'))),
                ('blast',      lambda: [
                    (m.take_damage(_rng.randint(5, 15)), self._on_monster_killed(m) if not m.alive else None)
                    for m in list(self.monsters) if m.alive and (m.x, m.y) in self.visible
                ] or self.add_message("Chaotic energy blasts all visible enemies!", 'success')),
            ])
            _chaos[1]()
            self.add_message("Baba Yaga's Iron Mortar churns with unpredictable magic!", 'warning')

        # -- Tier 5 wand effects -------------------------------------------
        elif effect == 'nova':
            from dice import roll as _roll
            all_monsters = [m for m in self.monsters if m.alive]
            if not all_monsters:
                self.add_message("The wand fires but no creatures are present!", 'info')
            else:
                total = 0
                for m in all_monsters:
                    dmg = self._wand_tier_damage(_roll(wand.power) if wand.power else _rng.randint(15, 30), wand.quiz_tier)
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

        elif effect == 'knock':
            # Open nearest locked container within 5 tiles
            px, py = self.player.x, self.player.y
            best, best_d = None, 999
            for item in self.ground_items:
                if isinstance(item, Container) and getattr(item, 'locked', False):
                    d = abs(item.x - px) + abs(item.y - py)
                    if d <= 5 and d < best_d:
                        best, best_d = item, d
            if best:
                best.locked = False
                self.add_message(f"Click! The {best.name} unlocks!", 'success')
            else:
                self.add_message("The wand hums but finds nothing locked nearby.", 'info')

        elif effect == 'turn_undead':
            from dice import roll as _roll_tu
            base_dmg = self._wand_tier_damage(_roll_tu(wand.power) if wand.power else 8, wand.quiz_tier)
            _UNDEAD_WORDS = {'skeleton', 'zombie', 'ghost', 'wraith', 'lich', 'wight',
                             'spectre', 'vampire', 'mummy', 'revenant', 'death', 'undead',
                             'ghoul', 'ghast', 'shade', 'banshee', 'draugr', 'barrow',
                             'bone', 'corpse', 'vrykolakas', 'strigoi', 'mohrg', 'demi_lich'}
            undead = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible
                      and any(w in m.kind.lower() for w in _UNDEAD_WORDS)]
            if undead:
                for m in undead:
                    actual = m.take_damage(base_dmg)
                    m.add_effect('feared', self._wand_tier_duration(8, wand.quiz_tier))
                    if not m.alive:
                        self._on_monster_killed(m)
                self.add_message(
                    f"Holy light blazes! {len(undead)} undead take {base_dmg} holy damage and flee!",
                    'success')
            else:
                # Minor effect on non-undead: flash of light
                self.add_message("Holy light flares but no undead are present.", 'info')

        elif effect == 'wonder':
            _WONDER_EFFECTS = [
                ('heal', lambda: (self.player.restore_hp(15),
                    self.add_message("The wand heals you for 15 HP!", 'success'))),
                ('haste', lambda: (self.player.add_effect('hasted', 8),
                    self.add_message("The wand makes you supernaturally fast!", 'success'))),
                ('confuse', lambda: (
                    [m.add_effect('confused', 8) for m in self.monsters
                     if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A wave of confusion erupts!", 'success'))),
                ('fireball', lambda: (
                    [m.take_damage(self._wand_tier_damage(_rng.randint(8, 20), wand.quiz_tier))
                     for m in self.monsters if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A burst of flame erupts from the wand!", 'success'))),
                ('teleport', lambda: (self._teleport_player(),
                    self.add_message("The wand teleports you randomly!", 'warning'))),
                ('shield', lambda: (self.player.add_effect('shielded', 10),
                    self.add_message("A protective barrier appears!", 'success'))),
                ('sleep', lambda: (
                    [m.add_effect('sleeping', 8) for m in self.monsters
                     if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A wave of slumber washes out!", 'success'))),
                ('invisible', lambda: (self.player.add_effect('invisible', 10),
                    self.add_message("You vanish from sight!", 'success'))),
                ('lightning', lambda: (
                    (lambda t: (t.take_damage(self._wand_tier_damage(_rng.randint(10, 25), wand.quiz_tier)),
                     self.add_message(f"Lightning zaps the {t.name}!", 'success'),
                     None if t.alive else self._on_monster_killed(t))
                    )(self._nearest_visible_monster()) if self._nearest_visible_monster() else
                    self.add_message("Lightning crackles harmlessly.", 'info'))),
                ('regen', lambda: (self.player.add_effect('regenerating', 15),
                    self.add_message("Your wounds begin to close on their own!", 'success'))),
            ]
            _, fn = _rng.choice(_WONDER_EFFECTS)
            fn()
            self.add_message("The wand of wonder crackles with chaotic energy!", 'warning')

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
        """Central handler for ALL monster kills: treasure, corpse, boss popup, seal tracking."""
        self.level_mgr.monsters_killed += 1
        self.add_message(f"The {monster.name} is slain!", 'success')
        self._drop_treasure(monster)
        # Boss narrative popup
        story_key = self._BOSS_STORY_KEYS.get(monster.kind)
        if story_key:
            self._show_story_popup(story_key, STATE_PLAYER)
            _BOSS_CHRONICLE = {
                'asterion_minotaur': "Killed the Minotaur. Asterion. He was bigger than I expected. The labyrinth is quiet now.",
                'medusa_gorgon': "Medusa is dead. I couldn't look at her directly. Even the snakes were afraid at the end.",
                'fafnir_dragon': "Fafnir fell. The dragon's scales were like iron. I still smell the smoke.",
                'fenrir_wolf': "Fenrir is bound. Or dead. I'm not sure which. The wolf was... vast. The ground still shakes.",
                'abaddon_destroyer': "Abaddon is destroyed. The Pit is sealed. I can barely hold the pen.",
            }
            self._log_chronicle(_BOSS_CHRONICLE.get(monster.kind, f"Slew {monster.name}. It's done."))
        # Fafnir drops a unique blood potion with a hint about the throw-over reforge
        if monster.kind == 'fafnir_dragon':
            self._spawn_fafnir_blood(monster.x, monster.y)
        # Seal demon: track broken seal
        if getattr(monster, 'is_seal_demon', False):
            seal_id = 'seal_of_' + monster.kind.replace('seal_demon_', '')
            self.seals_broken.add(seal_id)
            count = len(self.seals_broken)
            self.add_message(
                f"The {monster.name} falls! A seal is broken! ({count}/7)", 'success')
            self._log_chronicle(f"Broke a seal. {monster.name} is gone. {count} of 7 seals now shattered. The air feels heavier.")
            if count == 7:
                self.add_message(
                    "ALL SEVEN SEALS ARE BROKEN. The way to the Pit stands open.", 'danger')
                self._log_chronicle("All seven seals are broken. The ground split open. Whatever is down there, it's free now. And I have to face it.")
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
        categories = ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                      'artifact', 'potion')
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
                self.add_message("[LOOT] The boss drops a REWARD SCROLL!", 'loot')
        except Exception:
            pass

    def _spawn_fafnir_blood(self, x: int, y: int):
        """Drop Fafnir's Blood potion at (x, y) — contains a hint about the secret reforge."""
        from items import load_items, copy_at
        try:
            potions = load_items('potion')
            template = next((p for p in potions if p.id == 'fafnirs_blood'), None)
            if template:
                pot = copy_at(template, x, y)
                pot.identified = True
                self.ground_items.append(pot)
                self.add_message("A vial of shimmering dragon blood pools at your feet!", 'loot')
                self._log_chronicle("Fafnir's blood pooled at my feet. Hot as forge-fire. The old myths say dragon blood grants understanding.")
        except Exception:
            pass

    def _spawn_abaddon_locusts(self, abaddon):
        """Spawn a swarm of locusts near Abaddon. If Heavenly Host is active, spawn matching angels."""
        import json as _json
        from monster import Monster as _Mon
        from paths import data_path as _dp

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as f:
                _all = _json.load(f)
        except Exception:
            return

        lo, hi = abaddon.locust_count
        # Negative karma: larger swarms
        if getattr(self, '_locusts_strengthened', False):
            lo += 2
            hi += 3
        count = random.randint(lo, hi)

        locust_def = _all.get('abyssal_locust')
        angel_def = _all.get('heavenly_angel')
        if not locust_def:
            return

        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        occupied.add((self.player.x, self.player.y))

        # Find walkable tiles near Abaddon for locusts
        def _nearby_tiles(cx, cy, radius=4):
            tiles = []
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if self.dungeon.in_bounds(nx, ny) and self.dungeon.is_walkable(nx, ny):
                        if (nx, ny) not in occupied:
                            tiles.append((nx, ny))
            random.shuffle(tiles)
            return tiles

        locust_tiles = _nearby_tiles(abaddon.x, abaddon.y)
        spawned = 0
        for tx, ty in locust_tiles:
            if spawned >= count:
                break
            ld = dict(locust_def)
            ld['id'] = 'abyssal_locust'
            loc = _Mon(ld, tx, ty)
            self.monsters.append(loc)
            occupied.add((tx, ty))
            spawned += 1

        if spawned > 0:
            self.add_message(
                "Abaddon raises his hand \u2014 a swarm of locusts erupts from the void!", 'danger')

        # Heavenly Host counter-spawn: one angel per locust
        if self.heavenly_host_active and angel_def and spawned > 0:
            px, py = self.player.x, self.player.y
            angel_tiles = _nearby_tiles(px, py, radius=3)
            angel_count = 0
            for tx, ty in angel_tiles:
                if angel_count >= spawned:
                    break
                ad = dict(angel_def)
                ad['id'] = 'heavenly_angel'
                ang = _Mon(ad, tx, ty)
                self.monsters.append(ang)
                occupied.add((tx, ty))
                angel_count += 1
            if angel_count > 0:
                self.add_message(
                    f"{angel_count} angels of the Heavenly Host descend to answer!", 'success')

    # ------------------------------------------------------------------
    # NPC moral encounter system
    # ------------------------------------------------------------------

    def _maybe_spawn_trigger_item(self, level: int):
        """Spawn a triggered encounter item as floor loot if this is its designated level."""
        import random as _rng
        from items import load_items, copy_at
        trigger_levels = getattr(self, '_npc_trigger_item_levels', {})
        placed = getattr(self, '_npc_trigger_items_placed', set())
        # Map trigger item IDs to their JSON category
        _TRIGGER_ITEM_CATEGORIES = {
            'silverlight_pendant': 'accessory',
            'oathkeeper_sword': 'weapon',
            'lionheart_shield': 'shield',
        }
        for item_id, spawn_level in trigger_levels.items():
            if spawn_level != level or item_id in placed:
                continue
            category = _TRIGGER_ITEM_CATEGORIES.get(item_id)
            if not category:
                continue
            # Find the item template
            template = None
            for it in load_items(category):
                if it.id == item_id:
                    template = it
                    break
            if template is None:
                continue
            # Place in a non-start room on a walkable tile
            rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
            for room in _rng.sample(rooms, min(len(rooms), 5)):
                tiles = list(room.inner_tiles())
                _rng.shuffle(tiles)
                for tx, ty in tiles:
                    if self.dungeon.is_walkable(tx, ty):
                        spawned = copy_at(template, tx, ty)
                        self.ground_items.append(spawned)
                        placed.add(item_id)
                        break
                if item_id in placed:
                    break
        self._npc_trigger_items_placed = placed

    # ------------------------------------------------------------------
    # Secret Cow Level — Moo Moo Farm
    # ------------------------------------------------------------------

    def _maybe_spawn_cow(self, level: int):
        """Spawn the secret cow NPC on its designated level (once per run)."""
        if self._cow_spawned or self._cow_level_done:
            return
        if level != self._cow_level:
            return
        from monster import Monster
        cow_def = {
            'id': 'secret_cow',
            'name': 'a cow',
            'symbol': 'C',
            'color': [180, 140, 80],
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        import random as _rng
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            for tx, ty in room.inner_tiles():
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    cow = Monster(cow_def, tx, ty)
                    cow._npc_encounter_tag = '_cow_dialog'
                    self.monsters.append(cow)
                    self._cow_npc = cow
                    self._cow_spawned = True
                    return

    _COW_MOO_MESSAGES = [
        "Moo.",
        "The cow stares at you blankly. Moo.",
        "The cow chews its cud thoughtfully. Moo.",
        "Moo. Moo moo.",
        "The cow blinks. Moo.",
        "The cow seems unimpressed. Moo.",
        "The cow flicks its tail. Moo.",
        "Mooooooo.",
        "The cow shifts its weight. Moo.",
        "The cow looks at you expectantly. Moo?",
    ]

    _COW_POKE_MESSAGES = [
        "You poke the cow. Nothing happens. Moo.",
        "You poke the cow again. It moos indignantly.",
        "You poke the cow. It takes a step back. Moo.",
        "You poke the cow. It snorts. Moo.",
        "You poke the cow. It moos louder this time.",
        "You poke the cow firmly. It stamps a hoof. Moo!",
        "You poke the cow. It glares at you. MOO.",
        "You poke the cow. The ground trembles slightly.",
        "You poke the cow. The air crackles with bovine energy.",
    ]

    def _start_cow_encounter(self, cow_monster):
        """Open the cow dialog when player bumps the cow NPC."""
        self._active_cow = cow_monster
        self._cow_dialog_phase = 'options'
        self.state = STATE_COW_ENCOUNTER

    def _cow_encounter_input(self, key: int):
        """Handle input for cow dialog."""
        if self._cow_dialog_phase == 'result':
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.state = STATE_PLAYER
            return

        if key == pygame.K_1:
            # Feed the cow (costs an ingredient)
            from items import Ingredient
            ingredient = next(
                (i for i in self.player.inventory if isinstance(i, Ingredient)), None
            )
            if ingredient:
                self.player.remove_from_inventory(ingredient)
                self.add_message(
                    f"You feed the cow your {self._display_name(ingredient)}. "
                    "The cow chews contentedly. Moo.", 'success'
                )
            else:
                self.add_message("You have nothing to feed the cow. Moo.", 'info')
            self._cow_dialog_phase = 'result'
        elif key == pygame.K_2:
            # Walk away
            import random as _rng
            self.add_message(
                _rng.choice(self._COW_MOO_MESSAGES), 'info'
            )
            self.state = STATE_PLAYER
        elif key == pygame.K_3:
            # Poke the cow
            self._cow_poke_count += 1
            if self._cow_poke_count >= 10:
                self._enter_cow_level()
            else:
                import random as _rng
                msg = self._COW_POKE_MESSAGES[
                    min(self._cow_poke_count - 1, len(self._COW_POKE_MESSAGES) - 1)
                ]
                self.add_message(msg, 'info')
                self._cow_dialog_phase = 'result'
        elif key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER

    def _enter_cow_level(self):
        """Teleport the player to the Moo Moo Farm."""
        from boss_levels import COW_LEVEL
        self.add_message(
            "The cow's eyes glow red. The ground splits open beneath you!", 'danger'
        )
        self.add_message("MOO MOO MOO MOO MOO!", 'danger')
        self._log_chronicle("I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension. This is not in any lore I've read.")
        self._cow_return_level = self.dungeon_level
        # Remove the cow from the current level
        if self._cow_npc and self._cow_npc in self.monsters:
            self.monsters.remove(self._cow_npc)
        self._cow_npc = None
        self.state = STATE_PLAYER
        try:
            self._change_level(COW_LEVEL, enter_from_top=True)
        except Exception as e:
            self.add_message(f"Error entering cow level: {e}", 'danger')
            import traceback
            traceback.print_exc()

    def _exit_cow_level(self):
        """Return from Moo Moo Farm to the level where the cow was."""
        self._cow_level_done = True
        self.add_message("You step through the portal. The pasture fades behind you.", 'info')
        self.add_message("The cow is gone. The portal closes. Moo.", 'info')
        try:
            self._change_level(self._cow_return_level, enter_from_top=False)
        except Exception as e:
            self.add_message(f"Error exiting cow level: {e}", 'danger')
            import traceback
            traceback.print_exc()


    def _maybe_spawn_npc(self, level: int):
        """Spawn an NPC on this level if one is assigned and hasn't been encountered."""
        enc = self._npc_encounter_levels.get(level)
        if enc is None:
            return
        if enc['tag'] in self._encountered_npcs:
            return
        # For triggered encounters, only spawn if the player has the trigger item
        if enc.get('trigger_item'):
            if enc['trigger_item'] not in self._npc_triggered_items:
                return

        from monster import Monster
        # Create a fake "monster" for the NPC so it renders and blocks tiles
        npc_def = {
            'id': enc.get('sprite_id', 'npc_traveler'),
            'name': enc['name'],
            'symbol': enc['symbol'],
            'color': list(enc['color']),
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        # Place in a non-start room
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._npc_encounter_tag = enc['tag']
                    self.monsters.append(npc)
                    return

    def _maybe_spawn_flavor_npc(self, level: int):
        """Spawn a flavor (non-karmic) NPC on this level if one is assigned."""
        enc = getattr(self, '_flavor_encounter_levels', {}).get(level)
        if enc is None:
            return
        encountered = getattr(self, '_encountered_flavor_npcs', set())
        if enc['tag'] in encountered:
            return

        from monster import Monster
        npc_def = {
            'id': enc.get('sprite_id', 'npc_traveler'),
            'name': enc['name'],
            'symbol': enc['symbol'],
            'color': list(enc['color']),
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._flavor_encounter_tag = enc['tag']
                    self.monsters.append(npc)
                    return

    # ------------------------------------------------------------------
    # Magic Dungeon Carrot  (guaranteed spawn L1-19, once per run)
    # ------------------------------------------------------------------

    def _maybe_spawn_magic_carrot(self, level: int):
        """Place one Magic Dungeon Carrot on a random level between 1-19."""
        if getattr(self, '_magic_carrot_spawned', False):
            return
        if level < 1 or level > 19:
            return
        if not hasattr(self, '_magic_carrot_target_level'):
            import random as _rng
            self._magic_carrot_target_level = _rng.randint(1, 19)
        if level != self._magic_carrot_target_level:
            return

        from items import load_items
        import random as _rng
        foods = load_items('food')
        carrot_template = next((f for f in foods if f.id == 'magic_dungeon_carrot'), None)
        if carrot_template is None:
            return
        import copy
        carrot = copy.copy(carrot_template)
        # Place in a random room
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    carrot.x, carrot.y = tx, ty
                    self.ground_items.append(carrot)
                    self._magic_carrot_spawned = True
                    return

    # ------------------------------------------------------------------
    # Unicorn encounter  (L21-39, spawns once per run)
    # ------------------------------------------------------------------

    def _maybe_spawn_unicorn(self, level: int):
        """Spawn the ethereal unicorn on one random level between 21-39."""
        if getattr(self, '_unicorn_spawned', False):
            return
        if level < 21 or level > 39:
            return
        # Pick a random level in 21-39 on first eligible entry; spawn on that level
        if not hasattr(self, '_unicorn_target_level'):
            import random as _rng
            self._unicorn_target_level = _rng.randint(21, 39)
        if level != self._unicorn_target_level:
            return

        from monster import Monster
        npc_def = {
            'id': 'ethereal_unicorn',
            'name': 'Ethereal Unicorn',
            'symbol': 'u',
            'color': [255, 255, 240],
            'hp': 200,
            'thac0': 20,
            'speed': 10,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': ['magic', 'holy'],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._is_unicorn = True
                    npc._unicorn_state = 'wary'  # wary → relaxing → offered → eating → trusting
                    npc._unicorn_wait = 0
                    npc._unicorn_eat_turns = 0
                    self.monsters.append(npc)
                    self._unicorn_spawned = True
                    return

    def _handle_unicorn_bump(self, unicorn):
        """Handle player bumping the unicorn at various states."""
        state = getattr(unicorn, '_unicorn_state', 'wary')

        if state == 'wary':
            # Unicorn startles and moves away
            self.add_message("The unicorn startles and leaps away from you!", 'info')
            self._unicorn_flee(unicorn)
            unicorn._unicorn_wait = 0
            return True

        if state == 'relaxing':
            self.add_message("The unicorn watches you nervously. Perhaps an offering would help...", 'info')
            unicorn._unicorn_state = 'wary'
            unicorn._unicorn_wait = 0
            self._unicorn_flee(unicorn)
            return True

        if state in ('offered', 'eating'):
            self.add_message("The unicorn is eating! Don't disturb her!", 'info')
            unicorn._unicorn_state = 'wary'
            unicorn._unicorn_wait = 0
            self._unicorn_flee(unicorn)
            return True

        if state == 'trusting':
            # Karma check
            karma = getattr(self, 'karma', 0)
            if karma < 0:
                self.add_message(
                    "The unicorn gazes into your eyes... and recoils. She senses "
                    "darkness in your heart and gallops away!", 'danger')
                unicorn._unicorn_state = 'fled'
                unicorn.alive = False
                return True

            # Start the AI escalator quiz
            self.add_message(
                "The unicorn lowers her head and nuzzles your hand. "
                "A warm light envelops you both...", 'success')
            self._start_unicorn_quiz(unicorn)
            return True

        if state == 'fled':
            return True
        return False

    def _unicorn_flee(self, unicorn):
        """Move unicorn to a distant walkable tile in the same room or nearby."""
        import random as _rng
        px, py = self.player.x, self.player.y
        candidates = []
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                nx, ny = unicorn.x + dx, unicorn.y + dy
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if not self.dungeon.is_walkable(nx, ny):
                    continue
                dist_from_player = abs(nx - px) + abs(ny - py)
                if dist_from_player < 4:
                    continue
                if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                    continue
                candidates.append((nx, ny))
        if candidates:
            unicorn.x, unicorn.y = _rng.choice(candidates)

    def _tick_unicorn(self):
        """Called each turn to update unicorn state machine."""
        for m in self.monsters:
            if not getattr(m, '_is_unicorn', False) or not m.alive:
                continue
            state = getattr(m, '_unicorn_state', 'wary')
            px, py = self.player.x, self.player.y
            dist = max(abs(m.x - px), abs(m.y - py))

            if state == 'wary':
                # Player visible and within 8 tiles? Start watching
                if (m.x, m.y) in self.visible and dist <= 8:
                    m._unicorn_wait += 1
                    if m._unicorn_wait == 1:
                        self.add_message(
                            "A beautiful white unicorn stands nearby. She watches you warily.",
                            'info')
                    # If player stays still (or moves slowly) for 3 turns
                    if m._unicorn_wait >= 3:
                        m._unicorn_state = 'relaxing'
                        self.add_message(
                            "The unicorn seems to relax slightly. She sniffs the air...",
                            'info')
                else:
                    m._unicorn_wait = 0

            elif state == 'relaxing':
                # Check if player dropped a magic carrot adjacent to the unicorn
                carrot = None
                for item in self.ground_items:
                    if getattr(item, 'id', '') == 'magic_dungeon_carrot':
                        cdist = max(abs(item.x - m.x), abs(item.y - m.y))
                        if cdist <= 2:
                            carrot = item
                            break
                if carrot:
                    m._unicorn_state = 'eating'
                    m._unicorn_eat_turns = 0
                    # Move unicorn to the carrot
                    m.x, m.y = carrot.x, carrot.y
                    self.add_message(
                        "The unicorn's ears perk up! She approaches the Magic Dungeon "
                        "Carrot and begins to eat.", 'success')

            elif state == 'eating':
                m._unicorn_eat_turns += 1
                if m._unicorn_eat_turns >= 2:
                    # Remove the carrot from ground
                    self.ground_items = [
                        gi for gi in self.ground_items
                        if not (getattr(gi, 'id', '') == 'magic_dungeon_carrot'
                                and gi.x == m.x and gi.y == m.y)]
                    m._unicorn_state = 'trusting'
                    self.add_message(
                        "The unicorn finishes the carrot and looks at you with gentle "
                        "eyes. You may approach her now.", 'success')

    def _start_unicorn_quiz(self, unicorn):
        """Start the AI escalator_chain quiz for the unicorn encounter."""
        self._pending_unicorn = unicorn
        self.quiz_title = "THE UNICORN'S BLESSING  --  AI"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            chain = result.score  # 0-5
            self._apply_unicorn_boons(chain, unicorn)

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='ai',
            tier=1,
            callback=on_complete,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('ai'),
            base_seconds=self.player.get_quiz_timer('ai'),
        )

    def _apply_unicorn_boons(self, chain: int, unicorn):
        """Apply tiered boons based on quiz chain score."""
        if chain == 0:
            self.add_message(
                "The unicorn nuzzles your hand gently, then trots away. "
                "Perhaps next time...", 'info')
            unicorn._unicorn_state = 'fled'
            unicorn.alive = False
            return

        # Chain 1+: Regenerating status
        self.player.add_effect('regenerating', 30)
        self.add_message("The unicorn's horn glows — warm healing energy fills you! (regenerating 30 turns)", 'success')

        if chain >= 2:
            # Full HP/SP/MP restore
            self.player.hp = self.player.max_hp
            self.player.sp = self.player.max_sp
            self.player.mp = self.player.max_mp
            self.add_message("A radiant pulse fully restores your body, stamina, and magic!", 'success')

        if chain >= 3:
            # Remove curse from all equipped items
            uncursed = 0
            for item in self.player.get_equipped_items().values():
                if item and getattr(item, 'buc', 'uncursed') == 'cursed':
                    item.buc = 'uncursed'
                    item.buc_known = True
                    uncursed += 1
            # Also check inventory
            for item in self.player.inventory:
                if getattr(item, 'buc', 'uncursed') == 'cursed':
                    item.buc = 'uncursed'
                    item.buc_known = True
                    uncursed += 1
            if uncursed:
                self.add_message(f"Holy light purifies your belongings — {uncursed} item{'s' if uncursed != 1 else ''} uncursed!", 'success')
            else:
                self.add_message("Holy light sweeps through your belongings — all is pure.", 'success')

        if chain >= 4:
            # Permanent bonus: magic resistance
            import random as _rng
            bonus = _rng.choice(['magic_resist', 'poison_resist'])
            self.player.add_effect(bonus, -1)  # -1 = permanent
            nice = bonus.replace('_', ' ').title()
            self.add_message(f"The unicorn bestows a permanent blessing: {nice}!", 'success')

        if chain >= 5:
            # Unicorn joins as a pet!
            from pet_system import UnicornPet
            pet = UnicornPet(unicorn.x, unicorn.y)
            self.pets.append(pet)
            unicorn.alive = False  # remove the NPC monster
            self.add_message(
                "The unicorn bows her head to you. A bond forms between your souls — "
                "the Ethereal Unicorn joins you as a companion!", 'success')
            self.add_message(
                "She will heal you, cleanse afflictions, and sense hidden traps.",
                'info')
            self._log_chronicle("She stayed. The unicorn bowed her head and something passed between us. I can feel her presence at the edge of my thoughts. We're connected now.")
            return

        # If chain < 5, unicorn departs after granting boons
        unicorn.alive = False
        unicorn._unicorn_state = 'fled'
        self.add_message("The unicorn dips her head in farewell and vanishes in a shimmer of light.", 'info')
        self._log_chronicle("The unicorn touched her horn to my hand. Warmth flooded through me. Then she was gone, vanished like morning fog. I feel... different.")

    def _start_flavor_encounter(self, monster):
        """Begin a flavor encounter when the player bumps a flavor NPC."""
        tag = getattr(monster, '_flavor_encounter_tag', None)
        if tag is None:
            return False

        enc = getattr(self, '_flavor_encounter_levels', {}).get(self.dungeon_level)
        if enc is None or enc['tag'] != tag:
            # Search all levels for this tag
            for lvl_enc in getattr(self, '_flavor_encounter_levels', {}).values():
                if lvl_enc['tag'] == tag:
                    enc = lvl_enc
                    break
        if enc is None:
            return False

        # Reuse the NPC encounter UI with a flavor flag
        self._npc_encounter_active = enc
        self._npc_encounter_monster = monster
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_item_scroll = 0
        self._npc_is_flavor = True  # flag to skip karma processing
        self.state = STATE_NPC_ENCOUNTER
        return True

    def _start_npc_encounter(self, monster):
        """Begin a moral encounter when the player bumps an NPC."""
        tag = getattr(monster, '_npc_encounter_tag', None)
        if tag is None:
            return False

        # Find the encounter definition
        enc = None
        for lvl_enc in self._npc_encounter_levels.values():
            if lvl_enc['tag'] == tag:
                enc = lvl_enc
                break
        if enc is None:
            return False

        self._npc_encounter_active = enc
        self._npc_encounter_monster = monster
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_item_scroll = 0
        self.state = STATE_NPC_ENCOUNTER
        return True

    def _npc_encounter_input(self, key: int):
        """Handle input during NPC encounter — multi-phase flow."""
        enc = self._npc_encounter_active
        if enc is None:
            self.state = STATE_PLAYER
            return

        phase = self._npc_encounter_phase

        # ── Phase: TEXT (encounter description) ───────────────────
        if phase == 'text':
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._npc_encounter_phase = 'options'
            elif key == pygame.K_ESCAPE:
                self._close_npc_encounter(resolved=False)
            return

        # ── Phase: OPTIONS (choose 1-3) ──────────────────────────
        if phase == 'options':
            if key == pygame.K_ESCAPE:
                self._close_npc_encounter(resolved=False)
                return

            key_to_idx = {
                pygame.K_1: 0, pygame.K_KP1: 0,
                pygame.K_2: 1, pygame.K_KP2: 1,
                pygame.K_3: 2, pygame.K_KP3: 2,
            }
            idx = key_to_idx.get(key)
            if idx is None or idx >= len(enc['options']):
                return

            opt = enc['options'][idx]
            cost = opt.get('cost')

            # Check if player can pay the cost
            from npc_encounters import can_pay_cost, get_inventory_filter
            can_pay, fail_msg = can_pay_cost(self.player, cost, self.player_gold)
            if not can_pay:
                self.add_message(fail_msg, 'warning')
                return

            self._npc_selected_option = opt

            # If cost requires inventory selection, show item picker
            inv_filter = get_inventory_filter(cost)
            if inv_filter:
                self._npc_item_list = self._get_filtered_inventory(inv_filter)
                if not self._npc_item_list:
                    self.add_message(fail_msg or "You don't have what's needed.", 'warning')
                    self._npc_selected_option = None
                    return
                self._npc_item_scroll = 0
                self._npc_encounter_phase = 'select_item'
                return

            # No item selection needed — apply immediately
            self._apply_npc_choice(opt, selected_item=None)
            return

        # ── Phase: SELECT_ITEM (pick from filtered inventory) ────
        if phase == 'select_item':
            if key == pygame.K_ESCAPE:
                # Go back to options
                self._npc_encounter_phase = 'options'
                self._npc_selected_option = None
                return

            items = self._npc_item_list
            idx = self._AZ_KEYS.get(key)
            if idx is not None:
                actual = idx + self._npc_item_scroll
                if 0 <= actual < len(items):
                    self._apply_npc_choice(self._npc_selected_option,
                                           selected_item=items[actual])
                    return

            # Scroll
            if key in (pygame.K_DOWN, pygame.K_j) and self._npc_item_scroll + 9 < len(items):
                self._npc_item_scroll += 1
            elif key in (pygame.K_UP, pygame.K_k) and self._npc_item_scroll > 0:
                self._npc_item_scroll -= 1
            return

        # ── Phase: OUTCOME (show result) ─────────────────────────
        if phase == 'outcome':
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._close_npc_encounter(resolved=True)
            return

    def _get_filtered_inventory(self, filter_type: str) -> list:
        """Return inventory items matching the cost filter type."""
        from items import Food, Ingredient, Potion, Scroll, Weapon, Wand
        inv = self.player.inventory
        if filter_type == 'food':
            return [i for i in inv if isinstance(i, (Food, Ingredient))]
        if filter_type == 'healing_potion':
            items = []
            # Healing potions
            items.extend(i for i in inv if isinstance(i, Potion)
                         and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal'))
            # Healing scrolls
            items.extend(i for i in inv if isinstance(i, Scroll)
                         and 'heal' in getattr(i, 'effect', '').lower())
            # Healing wands with charges
            items.extend(i for i in inv if isinstance(i, Wand)
                         and 'heal' in getattr(i, 'effect', '').lower()
                         and getattr(i, 'charges', 0) > 0)
            # Heal spell (virtual entry — show as a selectable option)
            if 'heal_spell' in getattr(self.player, 'known_spells', {}):
                mp_cost = self.player.known_spells.get('heal_spell', 99)
                if self.player.mp >= mp_cost:
                    # Create a placeholder for the spell choice
                    class _SpellChoice:
                        name = f'Cast Heal ({mp_cost} MP)'
                        id = '_heal_spell_choice'
                        item_class = 'spell'
                    items.append(_SpellChoice())
            return items
        if filter_type == 'potion':
            return [i for i in inv if isinstance(i, Potion)]
        if filter_type == 'scroll':
            return [i for i in inv if isinstance(i, Scroll)]
        if filter_type == 'weapon':
            return [i for i in inv if isinstance(i, Weapon)]
        return []

    def _apply_npc_choice(self, opt: dict, selected_item=None):
        """Apply the cost, reward, and karma for the chosen option."""
        cost = opt.get('cost')
        reward = opt.get('reward')
        karma_delta = opt.get('karma', 0)  # flavor encounters have no karma

        # ── Apply cost ────────────────────────────────────────────
        if cost:
            ctype = cost['type']
            if ctype in ('food', 'healing_potion', 'potion', 'scroll', 'weapon'):
                if selected_item:
                    if getattr(selected_item, 'id', '') == '_heal_spell_choice':
                        # Spell: spend MP instead of removing an item
                        mp_cost = self.player.known_spells.get('heal_spell', 8)
                        self.player.mp -= mp_cost
                        self.add_message(f"You cast Heal. (-{mp_cost} MP)", 'info')
                    elif hasattr(selected_item, 'charges'):
                        # Wand: spend a charge
                        from items import Wand
                        if isinstance(selected_item, Wand):
                            selected_item.charges -= 1
                            self.add_message(
                                f"You use the {selected_item.name}. ({selected_item.charges} charges left)", 'info')
                            if selected_item.charges <= 0:
                                self.player.remove_from_inventory(selected_item)
                        else:
                            self.player.remove_from_inventory(selected_item)
                    else:
                        self.player.remove_from_inventory(selected_item)
            elif ctype == 'gold':
                self.player_gold -= cost['amount']
            elif ctype == 'hp_percent':
                loss = max(5, int(self.player.hp * cost['amount'] / 100))
                self.player.hp -= loss
            elif ctype == 'max_hp':
                self.player.max_hp -= cost['amount']
                self.player.hp = min(self.player.hp, self.player.max_hp)
            elif ctype == 'sp':
                self.player.sp = max(0, self.player.sp - cost['amount'])
            elif ctype == 'hp':
                self.player.hp = max(1, self.player.hp - cost['amount'])
            elif ctype == 'mp':
                self.player.mp = max(0, self.player.mp - cost['amount'])
            elif ctype == 'random_item':
                # Cost is an item from a category (e.g., scroll sacrifice)
                from items import Scroll, Potion, Food, Weapon
                cat = cost.get('category', 'scroll')
                cat_map = {'scroll': Scroll, 'potion': Potion, 'food': Food, 'weapon': Weapon}
                cls = cat_map.get(cat)
                if cls and selected_item and isinstance(selected_item, cls):
                    self.player.remove_from_inventory(selected_item)
                elif cls:
                    item = next((i for i in self.player.inventory if isinstance(i, cls)), None)
                    if item:
                        self.player.remove_from_inventory(item)
            elif ctype == 'triggered_item':
                # Remove the trigger item from inventory OR equipment slots
                enc = self._npc_encounter_active
                item_id = enc.get('trigger_item', '')
                removed = False
                # Check inventory first
                for it in self.player.inventory:
                    if getattr(it, 'id', '') == item_id:
                        self.player.remove_from_inventory(it)
                        removed = True
                        break
                # Check equipment slots if not found in inventory
                if not removed:
                    p = self.player
                    if p.weapon and getattr(p.weapon, 'id', '') == item_id:
                        p.weapon = None
                        removed = True
                    elif p.shield and getattr(p.shield, 'id', '') == item_id:
                        p.shield = None
                        removed = True
                    elif p.amulet_slot and getattr(p.amulet_slot, 'id', '') == item_id:
                        # Reverse accessory stat bonuses
                        fx = p.amulet_slot.effects
                        if 'stat' in fx:
                            p.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                        if 'stat2' in fx:
                            p.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                        if 'status' in fx:
                            p.status_effects.pop(fx['status'], None)
                        p.amulet_slot = None
                        removed = True
                    else:
                        for i, slot in enumerate(p.accessory_slots):
                            if slot and getattr(slot, 'id', '') == item_id:
                                fx = slot.effects
                                if 'stat' in fx:
                                    p.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                                if 'stat2' in fx:
                                    p.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                                if 'status' in fx:
                                    p.status_effects.pop(fx['status'], None)
                                p.accessory_slots[i] = None
                                removed = True
                                break
            elif ctype == 'accept_item':
                # Give the player a burden/cursed item
                self._grant_burden_item(cost['item_id'])
            elif ctype == 'spawn_deadite_ambush':
                # Free hit: 10% HP, then spawn a hostile Deadite
                loss = max(5, int(self.player.hp * 10 / 100))
                self.player.hp -= loss
                self.add_message(f"The Deadite rakes you for {loss} damage!", 'danger')
                self._spawn_npc_deadite()

        # ── Apply reward ──────────────────────────────────────────
        if reward:
            self._apply_npc_reward(reward)
        # Bonus reward (e.g., Cowering Goblin gives two items)
        bonus = opt.get('bonus_reward')
        if bonus:
            self._apply_npc_reward(bonus)

        # ── Apply karma ───────────────────────────────────────────
        old_karma = self.karma
        self.karma = max(-10, min(10, self.karma + karma_delta))
        if self.karma == 10 and old_karma < 10:
            self._log_chronicle("I feel... clean. Like everything I've done down here has mattered. The dungeon feels lighter.")
        elif self.karma == -10 and old_karma > -10:
            self._log_chronicle("Something inside me has gone cold. The dungeon doesn't frighten me anymore. That frightens me.")

        # Show outcome
        self._npc_outcome_text = opt['outcome']
        self._npc_encounter_phase = 'outcome'

    def _apply_npc_reward(self, reward: dict):
        """Grant a reward from an NPC encounter choice."""
        rtype = reward['type']

        if rtype == 'gold':
            if 'amount' in reward:
                amount = reward['amount']
            else:
                amount = random.randint(reward['min'], reward['max'])
            self.player_gold += amount
            self.add_message(f"+{amount} gold!", 'loot')

        elif rtype in ('random_weapon', 'random_armor', 'random_shield',
                        'random_accessory', 'random_potion', 'random_scroll',
                        'random_food', 'random_wand'):
            count = reward.get('count', 1)
            for _ in range(count):
                item = self._generate_npc_reward_item(rtype)
                if item:
                    self.player.inventory.append(item)
                    self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'stat':
            stat = reward['stat']
            amount = reward['amount']
            self.player.apply_stat_bonus(stat, amount)
            self.add_message(f"+{amount} {stat}!", 'success')

        elif rtype == 'specific_item':
            item = self._create_specific_npc_item(
                reward['item_type'], reward['item_id'],
                no_auto_identify=reward.get('no_auto_identify', False))
            if item:
                self.player.inventory.append(item)
                self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'random_item':
            # Flavor encounter reward: random item by category name
            cat = reward.get('category', 'potion')
            item = self._generate_npc_reward_item(f'random_{cat}')
            if item:
                item.identified = True
                self.player.inventory.append(item)
                self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'effect':
            eff = reward['effect']
            dur = reward.get('duration', 20)
            self.player.add_effect(eff, dur)
            eff_name = eff.replace('_', ' ').title()
            self.add_message(f"{eff_name} for {dur} turns!", 'success')

        elif rtype == 'hp_restore':
            self.player.restore_hp(reward['amount'])
            self.add_message(f"+{reward['amount']} HP!", 'success')

        elif rtype == 'sp_restore':
            self.player.sp = min(self.player.max_sp, self.player.sp + reward['amount'])
            self.add_message(f"+{reward['amount']} SP!", 'success')

        elif rtype == 'mp_restore':
            self.player.restore_mp(reward['amount'])
            self.add_message(f"+{reward['amount']} MP!", 'success')

        elif rtype == 'enchant_weapon':
            w = self.player.weapon
            if w:
                w.enchant_bonus += reward.get('amount', 1)
                self.add_message(f"{w.name} is now +{w.enchant_bonus}!", 'success')
            else:
                self.add_message("You have no weapon equipped to enchant.", 'warning')

        elif rtype == 'message':
            pass  # No mechanical reward, just the outcome text

        elif rtype == 'multi':
            for sub_reward in reward['rewards']:
                self._apply_npc_reward(sub_reward)

    def _generate_npc_reward_item(self, rtype: str):
        """Generate a random item of the given reward type at current level."""
        from items import load_items, copy_at
        type_map = {
            'random_weapon': 'weapon',
            'random_armor': 'armor',
            'random_shield': 'shield',
            'random_accessory': 'accessory',
            'random_potion': 'potion',
            'random_scroll': 'scroll',
            'random_food': 'food',
            'random_wand': 'wand',
        }
        cls_name = type_map.get(rtype)
        if not cls_name:
            return None
        try:
            candidates = []
            for item in load_items(cls_name):
                ml = getattr(item, 'min_level', 1)
                if ml <= self.dungeon_level and ml < 9999:
                    candidates.append(item)
            if candidates:
                template = random.choice(candidates)
                result = copy_at(template, self.player.x, self.player.y)
                result.identified = True
                return result
        except Exception:
            pass
        return None

    def _create_specific_npc_item(self, item_type: str, item_id: str,
                                   no_auto_identify: bool = False):
        """Create a specific named item for an NPC reward."""
        from items import load_items, copy_at
        try:
            for item in load_items(item_type):
                if item.id == item_id:
                    result = copy_at(item, self.player.x, self.player.y)
                    if not no_auto_identify:
                        result.identified = True
                    return result
        except Exception:
            pass
        return None

    def _grant_burden_item(self, item_id: str):
        """Grant a cursed/burden item to the player (lodestone, dispatch, etc.)."""
        from items import load_items, copy_at
        try:
            for item in load_items('artifact'):
                if item.id == item_id:
                    result = copy_at(item, self.player.x, self.player.y)
                    result.identified = True
                    self.player.inventory.append(result)
                    return
        except Exception:
            pass

    def _close_npc_encounter(self, resolved: bool):
        """Close the NPC encounter overlay."""
        if resolved:
            # Remove the NPC
            npc = self._npc_encounter_monster
            if npc:
                npc.alive = False
                npc.hp = 0
            enc = self._npc_encounter_active
            if enc:
                if getattr(self, '_npc_is_flavor', False):
                    encountered = getattr(self, '_encountered_flavor_npcs', set())
                    encountered.add(enc['tag'])
                else:
                    self._encountered_npcs.add(enc['tag'])
                # Log to chronicle
                name = enc.get('name', 'someone')
                import random as _chr_rng
                if getattr(self, '_npc_is_flavor', False):
                    _FLAVOR_VERBS = [
                        "Ran into {name}. A brief exchange in the dark.",
                        "Met {name}. Even down here, people find a way.",
                        "Crossed paths with {name}. The dungeon is stranger than I thought.",
                    ]
                    self._log_chronicle(_chr_rng.choice(_FLAVOR_VERBS).format(name=name))
                else:
                    _NPC_VERBS = [
                        "Met {name}. Had to make a hard choice.",
                        "Encountered {name}. Did what I thought was right.",
                        "Came across {name}. This dungeon tests more than combat skill.",
                        "Found {name}. Every choice down here has weight.",
                        "{name} needed something from me. I gave my answer.",
                    ]
                    self._log_chronicle(_chr_rng.choice(_NPC_VERBS).format(name=name))

        self._npc_encounter_active = None
        self._npc_encounter_monster = None
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_is_flavor = False
        self.state = STATE_PLAYER
        if resolved:
            self._advance_turn()


    def _resolve_judgment(self):
        """Resolve the Altar of the Last Judgment on L99."""
        from npc_encounters import judge_karma
        outcome, text = judge_karma(self.karma)

        self._judgment_text = text
        self.state = STATE_JUDGMENT

        if outcome == 'sword_and_scales':
            # Grant both Sword and Scales of Michael + Paladin title
            self.player_title = 'Paladin'
            from items import load_items, copy_at
            px, py = self.player.x, self.player.y
            try:
                weapons = load_items('weapon')
                sword = next((w for w in weapons if w.id == 'sword_of_michael'), None)
                if sword:
                    sw = copy_at(sword, px, py)
                    sw.identified = True
                    self.player.inventory.append(sw)
                    self.add_message("The Sword of Michael materializes in your hands!", 'success')
            except Exception:
                pass
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    sc.identified = True
                    self.player.inventory.append(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                pass
            self._log_chronicle("Stood before the altar of judgment. The scales weighed my soul. I was found worthy. A sword of white fire and the scales themselves were given to me. I've never felt so terrified.")

        elif outcome == 'scales_granted':
            from items import load_items, copy_at
            px, py = self.player.x, self.player.y
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    sc.identified = True
                    self.player.inventory.append(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                pass
            self._log_chronicle("The altar weighed my deeds. Not perfect, but enough. The Scales of Michael settled into my hands. They hum with a quiet judgment.")

        elif outcome == 'abaddon_empowered':
            # Abaddon gets 50% more HP and extra attack
            self.add_message("A dark power surges into the depths below...", 'danger')
            # Store flag for when L100 is generated
            self._abaddon_empowered = True
            self._log_chronicle("The altar judged me. I was found wanting. Something below grew stronger. I can feel it.")

        elif outcome == 'locusts_strengthened':
            # Larger locust swarms
            self.add_message("The buzzing of locusts grows louder in the deep...", 'danger')
            self._locusts_strengthened = True
            self._log_chronicle("The judgment went poorly. The buzzing from below is louder now. I made things worse.")

    def _judgment_input(self, key: int):
        """Dismiss the judgment result overlay."""
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER


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
    # Spell menu  (m key -- learned spells, cast with science chain quiz)
    # ------------------------------------------------------------------

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

        # For targeted spells, enter targeting mode
        if spell.get('needs_target'):
            self._pending_spell = spell
            self._pending_spell_id = spell_id
            px, py = self.player.x, self.player.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            if not candidates:
                self.add_message("No visible target for this spell.", 'warning')
                self.player.mp += mp_cost  # refund MP
                self.state = STATE_PLAYER
                return
            self.player.mp -= mp_cost
            self._power_targeting = True
            self._pending_power = f'spell_{spell_id}'
            self._target_candidates = candidates
            self._target_idx = 0
            self.target_cursor_x = candidates[0].x
            self.target_cursor_y = candidates[0].y
            self.state = STATE_TARGET
            self.add_message(
                f"Casting {spell['name']}... select target! Arrows to aim, ENTER to cast.",
                'info')
            return

        # Non-targeted spells: go straight to quiz
        self.player.mp -= mp_cost
        self._start_spell_quiz(spell, spell_id, target=None)

    def _start_spell_quiz(self, spell, spell_id, target):
        """Start the science escalator chain quiz for a spell."""
        self.state = STATE_QUIZ
        self.quiz_title = f"CAST {spell['name'].upper()} -- SCIENCE"

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
            mode='escalator_chain',
            subject='science',
            tier=spell['quiz_tier'],
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
            base_seconds=self.player.get_quiz_timer('science'),
        )

    # Spell chain multipliers — same philosophy as weapon chain multipliers
    _SPELL_CHAIN_MULTS = [0.5, 1.0, 1.8, 2.8, 4.0]

    def _spell_damage(self, base_dmg: int, chain: int) -> int:
        """Scale spell damage by chain multiplier AND INT."""
        mult = self._SPELL_CHAIN_MULTS[min(chain - 1, len(self._SPELL_CHAIN_MULTS) - 1)]
        return max(1, int(base_dmg * mult * (1.0 + self.player.INT * 0.1)))

    def _apply_spell_effect(self, spell: dict, chain: int, target=None):
        """Apply a learned spell's effect. Chain 1-5 scales damage/duration."""
        effect = spell['effect']
        power  = spell.get('power', '')

        # Scale duration with chain (utility/buff spells)
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
            scaled   = self._spell_damage(base_dmg, chain)
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

        if effect == 'mass_fire':
            from dice import roll
            base_dmg = roll(power) if power else 10
            scaled   = self._spell_damage(base_dmg, chain)
            hit = 0
            for m in list(self.monsters):
                if m.alive and (m.x, m.y) in self.visible:
                    actual = m.take_damage(scaled)
                    if not m.alive:
                        self._on_monster_killed(m)
                    hit += 1
            self.add_message(
                f"Fireball! {hit} monsters take {scaled} fire dmg (chain {chain})", 'success')
            return

        if effect == 'knock_spell':
            # Find nearest locked container within 3 tiles
            px, py = self.player.x, self.player.y
            best, best_d = None, 999
            for item in self.ground_items:
                if isinstance(item, Container) and getattr(item, 'locked', False):
                    d = abs(item.x - px) + abs(item.y - py)
                    if d <= 3 and d < best_d:
                        best, best_d = item, d
            if best:
                best.locked = False
                self.add_message(f"Click! The {best.name} unlocks magically! (chain {chain})", 'success')
            else:
                self.add_message("No locked containers nearby to open.", 'info')
            return

        if effect == 'detect_monsters_spell':
            dur = max(5, int(20 * chain_scale))
            self.player.add_effect('clairvoyant', dur)
            count = sum(1 for m in self.monsters if m.alive)
            self.add_message(
                f"Your senses expand -- {count} creatures revealed for {dur} turns! (chain {chain})", 'success')
            return

        if effect == 'teleport_away_spell':
            # Target nearest visible monster, or self-teleport if none
            # Bosses CAN be teleported — they stay aggro'd and come back
            target_m = self._nearest_visible_monster()
            if target_m:
                floors = [(x, y) for y in range(self.dungeon.height)
                          for x in range(self.dungeon.width)
                          if self.dungeon.is_walkable(x, y)
                          and (x, y) != (self.player.x, self.player.y)
                          and not any(m.alive and m.x == x and m.y == y for m in self.monsters)]
                if floors:
                    nx, ny = random.choice(floors)
                    target_m.x, target_m.y = nx, ny
                    self.add_message(
                        f"The {target_m.name} vanishes in a flash of light! (chain {chain})", 'success')
                else:
                    self.add_message("The spell fizzles -- no safe destination found.", 'warning')
            else:
                # No visible monsters — teleport self
                self._teleport_player()
                self.add_message(f"You teleport to a new location! (chain {chain})", 'success')
            return

        # Scale extra_heal duration/amount
        if effect == 'extra_heal':
            from dice import roll
            base = roll(power) if power else 8
            healed = self._spell_damage(base, chain)
            self.player.restore_hp(healed)
            self.add_message(f"You are healed for {healed} HP! (chain {chain})", 'success')
            return

        # Army of Darkness: summon undead pet horde
        if effect == 'summon_undead_horde':
            count = max(3, int(5 * chain_scale))
            self._summon_undead_pets(count)
            self.add_message(
                f"The dead rise to serve you! {count} undead minions summoned! (chain {chain})",
                'success')
            return

        # Cleanse: remove one negative status effect
        if effect == 'cleanse_self':
            from status_effects import DEBUFFS
            active = [e for e in self.player.status_effects if e in DEBUFFS]
            if active:
                removed = active[0]
                self.player.status_effects.pop(removed, None)
                self.add_message(f"Cleansed! {removed.title()} removed.", 'success')
            else:
                self.add_message("You have no ailments to cleanse.", 'info')
            return

        # Empower: next melee attack deals 3x damage
        if effect == 'empower_next':
            self.player.status_effects['empowered'] = 1
            self.add_message("Arcane power surges through your weapon! Next attack deals 3x damage!", 'success')
            return

        # Summon Guardian: temporary pet ally
        if effect == 'summon_guardian':
            from pet_system import Pet, random_species
            px, py = self.player.x, self.player.y
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = px + dx, py + dy
                    if (nx, ny) == (px, py):
                        continue
                    if not self.dungeon.is_walkable(nx, ny):
                        continue
                    if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                        continue
                    species = random_species()
                    pet = Pet(species, nx, ny)
                    pet.level = max(1, self.dungeon_level // 3)
                    pet._refresh_stats()
                    self.pets.append(pet)
                    self.add_message(
                        f"{self._a_or_an(pet.name).capitalize()} materializes to guard you! (chain {chain})", 'success')
                    return
            self.add_message("No room to summon a guardian.", 'warning')
            return

        # Meteor: massive AoE fire damage
        if effect == 'meteor':
            from dice import roll as _roll_m
            base_dmg = _roll_m(power) if power else 20
            scaled = self._spell_damage(base_dmg, chain)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            kills = 0
            for m in visible_monsters:
                actual = m.take_damage(scaled)
                if not m.alive:
                    self._on_monster_killed(m)
                    kills += 1
            self.add_message(
                f"A meteor crashes down! {len(visible_monsters)} creatures take {scaled} fire damage! "
                f"({kills} slain, chain {chain})", 'success')
            return

        # Time Freeze: freeze all monsters
        if effect == 'time_freeze':
            dur = max(3, int(5 * chain_scale))
            count = 0
            for m in self.monsters:
                if m.alive:
                    m.add_effect('paralyzed', dur)
                    count += 1
            self.add_message(
                f"TIME FREEZES! {count} creatures locked in place for {dur} turns! (chain {chain})", 'success')
            return

        # Light spell: reveal tiles in a radius (chain scales radius)
        if effect == 'light':
            base_radius = 15
            radius = max(5, int(base_radius * chain_scale))
            px, py = self.player.x, self.player.y
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        nx, ny = px + dx, py + dy
                        if self.dungeon.in_bounds(nx, ny):
                            self.dungeon.explored.add((nx, ny))
            self.add_message(
                f"Brilliant light floods the area! (radius {radius}, chain {chain})", 'success')
            return

        # Scale status durations for self-buff spells
        _SELF_BUFF_DURATIONS = {
            'shield_self':       ('shielded',    12),
            'haste_self':        ('hasted',      10),
            'invisibility_self': ('invisible',   15),
            'reflect_self':      ('reflecting',  15),
        }
        if effect in _SELF_BUFF_DURATIONS:
            eff_name, base_dur = _SELF_BUFF_DURATIONS[effect]
            dur = max(2, int(base_dur * chain_scale))
            self.player.add_effect(eff_name, dur)
            self.add_message(
                f"{spell['name']} -- {eff_name} for {dur} turns! (chain {chain})", 'success')
            return

        # Targeted spells -- handle directly so we use the pre-found target
        if target is not None:
            from dice import roll as _roll
            if effect == 'magic_missile':
                # Fire one missile per chain link (1-5 missiles)
                missiles = max(1, chain)
                total_dmg = 0
                for _ in range(missiles):
                    if not target.alive:
                        break
                    base_dmg = _roll(power) if power else 4
                    per_missile = self._int_scaled_damage(base_dmg)
                    target.hp = max(0, target.hp - per_missile)
                    if target.hp == 0:
                        target.alive = False
                    total_dmg += per_missile
                self.add_message(
                    f"{missiles} magic missile{'s' if missiles > 1 else ''} "
                    f"strike{'s' if missiles == 1 else ''} the {target.name} "
                    f"for {total_dmg} total damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'fire_bolt':
                base_dmg = _roll(power) if power else 8
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'lightning_bolt':
                from combat import get_line_tiles
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                px, py = self.player.x, self.player.y
                line = get_line_tiles(px, py, target.x, target.y)
                line_set = set(line)
                line_hits = [m for m in self.monsters
                             if m.alive and (m.x, m.y) in line_set and (m.x, m.y) in self.visible]
                stun_dur = max(1, int(3 * chain_scale))
                for lm in line_hits:
                    actual = lm.take_damage(scaled)
                    if actual > 0:
                        sd, sr = self._boss_resist_cc(lm, stun_dur)
                        if not sr:
                            lm.add_effect('stunned', sd)
                    if not lm.alive:
                        self._on_monster_killed(lm)
                if len(line_hits) > 1:
                    self.add_message(
                        f"Lightning arcs through {len(line_hits)} creatures for {scaled} damage! (chain {chain})", 'success')
                elif line_hits:
                    self.add_message(
                        f"Lightning strikes the {line_hits[0].name} for {scaled} damage! (chain {chain})", 'success')
                else:
                    self.add_message("The lightning dissipates harmlessly.", 'info')
            elif effect == 'sleep_monster':
                dur = max(2, int(6 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the sleep! (chain {chain})", 'warning')
                else:
                    target.add_effect('sleeping', dur)
                    self.add_message(f"The {target.name} falls asleep for {dur} turns! (chain {chain})", 'success')
            elif effect == 'confuse_monster':
                dur = max(2, int(10 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the confusion! (chain {chain})", 'warning')
                else:
                    target.add_effect('confused', dur)
                    self.add_message(f"The {target.name} is confused for {dur} turns! (chain {chain})", 'success')
            elif effect == 'paralyze_monster':
                dur = max(2, int(8 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} resists the paralysis! (chain {chain})", 'warning')
                else:
                    target.add_effect('paralyzed', dur)
                    self.add_message(f"The {target.name} is paralyzed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'aard_blast':
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                stun = max(1, int(3 * chain_scale))
                stun, sr = self._boss_resist_cc(target, stun)
                if not sr:
                    target.add_effect('stunned', stun)
                self.add_message(
                    f"Aard! A telekinetic blast strikes the {target.name} for {actual} damage"
                    + (" and stuns it!" if not sr else "!") + f" (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'slow_monster':
                dur = max(2, int(8 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic! (chain {chain})", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} is slowed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'teleport_self':
                self._teleport_player()
                self.add_message("The Elder Blood bends space around you!", 'success')
            elif effect == 'smite':
                base_dmg = _roll(power) if power else 20
                scaled = self._spell_damage(base_dmg, chain)
                target.hp = max(0, target.hp - scaled)  # holy — bypasses resistances
                if target.hp == 0:
                    target.alive = False
                self.add_message(
                    f"Holy fire smites the {target.name} for {scaled} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'slow_monster_spell':
                dur = max(4, int(10 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic! (chain {chain})", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} is slowed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'acid_arrow':
                base_dmg = _roll(power) if power else 8
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                dot_dur = max(2, int(5 * chain_scale))
                dot_dur, dot_resisted = self._boss_resist_cc(target, dot_dur)
                if not dot_resisted:
                    target.add_effect('poisoned', dot_dur)
                self.add_message(
                    f"An acid arrow strikes the {target.name} for {actual} damage!"
                    + (f" Acid burns for {dot_dur} turns!" if not dot_resisted else " It resists the acid burn!")
                    + f" (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'drain_life_spell':
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                healed = self.player.restore_hp(actual)
                self.add_message(
                    f"You drain {actual} life from the {target.name} and heal {healed} HP! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'fear_monster_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is too powerful to frighten!", 'warning')
                else:
                    dur = max(3, int(10 * chain_scale))
                    target.add_effect('feared', dur)
                    target.ai_pattern = 'cowardly'
                    self.add_message(
                        f"The {target.name} turns and flees in terror for {dur} turns! (chain {chain})", 'success')
            elif effect == 'polymorph_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the polymorph!", 'warning')
                else:
                    import json as _pjson
                    from monster import Monster as _PMon
                    from paths import data_path as _pdp
                    try:
                        with open(_pdp('data', 'monsters.json'), encoding='utf-8') as _pf:
                            _all_defs = _pjson.load(_pf)
                        # High chain biases toward weaker result
                        max_ml = max(1, target.min_level + 10 - chain * 3)
                        eligible = [k for k, v in _all_defs.items()
                                    if v.get('min_level', 1) <= max_ml
                                    and k != target.kind and v.get('frequency', 1) > 0]
                        if not eligible:
                            eligible = [k for k, v in _all_defs.items()
                                        if k != target.kind and v.get('frequency', 1) > 0]
                        old_name = target.name
                        kind = random.choice(eligible)
                        defn = {**_all_defs[kind], 'id': kind}
                        new_m = _PMon(defn, target.x, target.y)
                        idx = self.monsters.index(target)
                        self.monsters[idx] = new_m
                        self.add_message(
                            f"The {old_name} warps into {self._a_or_an(new_m.name)}! (chain {chain})", 'success')
                    except Exception:
                        self.add_message("The polymorph spell fizzles!", 'warning')
            elif effect == 'disintegrate_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                # Chain-scaling kill chance: 30/45/60/75/90%
                kill_chance = 0.15 + chain * 0.15  # 0.30 at chain 1 .. 0.90 at chain 5
                if not is_boss and random.random() < kill_chance:
                    target.hp = 0
                    target.alive = False
                    self.add_message(
                        f"The {target.name} is disintegrated! (chain {chain}, {int(kill_chance*100)}%)", 'success')
                    self._on_monster_killed(target)
                else:
                    base_dmg = _roll(power) if power else 20
                    scaled = self._spell_damage(base_dmg, chain)
                    actual = target.take_damage(scaled)
                    if is_boss:
                        self.add_message(
                            f"The {target.name} resists disintegration but takes {actual} damage! (chain {chain})", 'success')
                    else:
                        self.add_message(
                            f"The {target.name} partially resists! {actual} damage! (chain {chain}, {int(kill_chance*100)}% missed)", 'warning')
                    if not target.alive:
                        self._on_monster_killed(target)
            else:
                # Fallback: generic targeted damage
                from dice import roll as _r
                scaled = max(1, int((_r(power) if power else 6) * chain_scale))
                actual = target.take_damage(scaled)
                self.add_message(f"The {effect.replace('_', ' ')} hits the {target.name} for {actual} dmg! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

    # ------------------------------------------------------------------
    # Scroll menu  (s key -- grammar quiz)
    # ------------------------------------------------------------------

    _SCROLL_TABS = [
        ('Scrolls',    lambda i: isinstance(i, Scroll)),
        ('Spellbooks', lambda i: isinstance(i, Spellbook)),
    ]

    def _read_scroll(self, scroll: 'Scroll'):
        display = self._display_name(scroll)
        self.quiz_title = f"READING {display.upper()}  --  GRAMMAR"
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
                    "You stumble over the words -- the scroll crumbles unread.", 'warning'
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
            base_seconds=self.player.get_quiz_timer('grammar'),
        )

    def _apply_scroll_effect(self, scroll: 'Scroll'):
        from dice import roll
        effect = scroll.effect
        _scroll_buc = getattr(scroll, 'buc', 'uncursed')

        if effect == 'heal':
            amount = roll(scroll.power) if scroll.power else 10
            self.player.restore_hp(amount)
            self.add_message(f"Healing light washes over you -- {amount} HP restored!", 'success')

        elif effect == 'boss_reward':
            code = scroll.power or '???'
            self.add_message(f"[REWARD CODE: {code}]", 'loot')
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
            if _scroll_buc == 'cursed':
                self.add_message("The scroll's words dissolve into nonsense.", 'warning')
            elif _scroll_buc == 'blessed':
                # Blessed: identify ALL unknown items
                unknowns = [i for i in self.player.inventory
                            if hasattr(i, 'identified') and not i.identified
                            and i.id not in self.player.known_item_ids]
                if unknowns:
                    for u in unknowns:
                        u.identified = True
                        u.buc_known = True
                        self.player.known_item_ids.add(u.id)
                        self._propagate_identification(u.id)
                    self.add_message(f"Brilliant light reveals all {len(unknowns)} items!", 'success')
                else:
                    self.add_message("All your items are already identified.", 'info')
            else:
                # Uncursed: identify one item
                unknown = next(
                    (i for i in self.player.inventory
                     if hasattr(i, 'identified') and not i.identified
                        and i.id not in self.player.known_item_ids),
                    None
                )
                if unknown:
                    unknown.identified = True
                    unknown.buc_known = True
                    self.player.known_item_ids.add(unknown.id)
                    self._propagate_identification(unknown.id)
                    self.add_message(f"The {unknown.unidentified_name} is revealed: {unknown.name}!", 'success')
                    if unknown.lore:
                        self._lore_subject = unknown
                        self.state = STATE_LORE
                else:
                    self.add_message("All your items are already identified.", 'info')

        elif effect == 'enchant_weapon':
            from items import ENCHANT_CAP
            w = self.player.weapon or self.player.ranged_weapon
            if w:
                cap = ENCHANT_CAP.get('weapon', 5)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = w.enchant_bonus
                w.enchant_bonus = max(-3, min(cap, w.enchant_bonus + delta))
                actual = w.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"Your {w.name} glows -- enchant +{w.enchant_bonus}!",
                        'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"Your {w.name} dims -- enchant {w.enchant_bonus:+d}!",
                        'warning'
                    )
                else:
                    self.add_message(
                        f"Your {w.name} shudders but can hold no more enchantment.",
                        'info'
                    )
            else:
                self.add_message("You have no weapon to enchant.", 'info')

        elif effect == 'remove_curse':
            if _scroll_buc == 'cursed':
                self.add_message("The scroll's power fizzles. Nothing happens.", 'warning')
            else:
                from status_effects import DEBUFFS
                removed = [e for e in list(self.player.status_effects) if e in DEBUFFS]
                for e in removed:
                    del self.player.status_effects[e]
                cursed_items = []
                if _scroll_buc == 'blessed':
                    # Blessed: uncurse ALL inventory items too
                    all_items = list(self.player.inventory)
                    if self.player.weapon:
                        all_items.append(self.player.weapon)
                    if self.player.ranged_weapon:
                        all_items.append(self.player.ranged_weapon)
                    all_items.extend(s for s in self.player.armor_slots if s)
                    if self.player.shield:
                        all_items.append(self.player.shield)
                    all_items.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
                    amulet = getattr(self.player, 'amulet_slot', None)
                    if amulet:
                        all_items.append(amulet)
                else:
                    # Uncursed: equipped items only
                    all_items = []
                    if self.player.weapon:
                        all_items.append(self.player.weapon)
                    if self.player.ranged_weapon:
                        all_items.append(self.player.ranged_weapon)
                    all_items.extend(s for s in self.player.armor_slots if s)
                    if self.player.shield:
                        all_items.append(self.player.shield)
                    all_items.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
                for eq in all_items:
                    if getattr(eq, 'buc', 'uncursed') == 'cursed':
                        eq.buc = 'uncursed'
                        eq.buc_known = True
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

        # -- Tier 3 scroll effects ------------------------------------------
        elif effect == 'sleep_monsters':
            targets = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in targets:
                m.add_effect('sleeping', 8)
            if targets:
                self.add_message(f"A wave of slumber washes out -- {len(targets)} creature(s) fall asleep!", 'success')
            else:
                self.add_message("No creatures are in sight to affect.", 'info')

        elif effect == 'haste_self':
            duration = int(scroll.power) if scroll.power else 15
            self.player.add_effect('hasted', duration)
            self.add_message(f"Energy surges through you -- hasted for {duration} turns!", 'success')

        elif effect == 'enchant_armor':
            from items import ENCHANT_CAP, ARMOR_SLOTS
            equipped = [(s, ARMOR_SLOTS[i]) for i, s in enumerate(self.player.armor_slots) if s is not None]
            if equipped:
                target, slot_name = equipped[0]
                cap = ENCHANT_CAP.get(slot_name, 1)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = getattr(target, 'enchant_bonus', 0)
                target.enchant_bonus = max(-3, min(cap, old_val + delta))
                actual = target.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"Your {target.name} shines -- enchant +{target.enchant_bonus}!", 'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"Your {target.name} tarnishes -- enchant {target.enchant_bonus:+d}!", 'warning'
                    )
                else:
                    self.add_message(
                        f"Your {target.name} shudders but can hold no more enchantment.", 'info'
                    )
            else:
                self.add_message("You wear no armor to enchant.", 'info')

        elif effect == 'enchant_item':
            from items import ENCHANT_CAP, ARMOR_SLOTS
            candidates = []
            if self.player.weapon:
                candidates.append((self.player.weapon, 'weapon'))
            if self.player.ranged_weapon:
                candidates.append((self.player.ranged_weapon, 'weapon'))
            for i, s in enumerate(self.player.armor_slots):
                if s:
                    candidates.append((s, ARMOR_SLOTS[i]))
            if self.player.shield:
                candidates.append((self.player.shield, 'shield'))
            for s in getattr(self.player, 'accessory_slots', []):
                if s:
                    candidates.append((s, 'accessory'))
            if candidates:
                target, slot_key = candidates[0]
                cap = ENCHANT_CAP.get(slot_key, 1)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = getattr(target, 'enchant_bonus', 0)
                target.enchant_bonus = max(-3, min(cap, old_val + delta))
                actual = target.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"A golden light infuses your {target.name} -- enchant +{target.enchant_bonus}!",
                        'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"A dark energy corrupts your {target.name} -- enchant {target.enchant_bonus:+d}!",
                        'warning'
                    )
                else:
                    self.add_message(
                        f"Your {target.name} shudders but can hold no more enchantment.",
                        'info'
                    )
            else:
                self.add_message("You have no equipped items to enchant.", 'info')

        # -- Tier 4 scroll effects ------------------------------------------
        elif effect == 'teleport_self':
            self._teleport_player()

        elif effect == 'charging':
            from items import Wand
            wands = [i for i in self.player.inventory if isinstance(i, Wand)]
            if wands:
                for w in wands:
                    w.charges = min(w.max_charges, w.charges + 1)
                self.add_message(
                    f"Magical energy crackles into {len(wands)} wand(s) -- each recharged by 1!", 'success'
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
                    f"A flash of revelation -- {len(unknown)} item(s) identified!", 'success'
                )
            else:
                self.add_message("All your items are already identified.", 'info')

        # -- Tier 5 scroll effects ------------------------------------------
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
            self.add_message(f"Time itself halts -- {duration} turns of absolute stillness!", 'success')

        elif effect == 'great_power':
            for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                self.player.apply_stat_bonus(stat, 1)
            self.add_message("Every faculty within you is elevated! All stats permanently +1!", 'success')

        elif effect == 'earth':
            from dice import roll as _roll_e
            base_dmg = _roll_e(scroll.power) if scroll.power else 12
            scaled = self._int_scaled_damage(base_dmg)
            victims = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in victims:
                m.take_damage(scaled)
                if not m.alive:
                    self._on_monster_killed(m)
            if victims:
                self.add_message(
                    f"Boulders crash from the ceiling! {len(victims)} creature(s) take {scaled} damage!", 'success')
            else:
                self.add_message("Rocks tumble from above, but nothing is in the way.", 'info')

        elif effect == 'protection':
            _buc = getattr(scroll, 'buc', 'uncursed')
            bonus = 5 if _buc == 'blessed' else (1 if _buc == 'cursed' else 3)
            dur = 30
            self.player.add_effect('shielded', dur)
            self.add_message(f"A protective ward envelops you! +{bonus} AC for {dur} turns!", 'success')

        elif effect == 'enchant_accessory':
            _buc = getattr(scroll, 'buc', 'uncursed')
            bonus = 2 if _buc == 'blessed' else (-1 if _buc == 'cursed' else 1)
            acc = next((s for s in self.player.accessory_slots if s is not None), None)
            if acc:
                fx = acc.effects
                if 'amount' in fx:
                    fx['amount'] = max(0, fx['amount'] + bonus)
                    self.add_message(
                        f"The {acc.name} glows! Bonus {'increased' if bonus > 0 else 'decreased'} by {abs(bonus)}!", 'success')
                else:
                    self.add_message(f"The {acc.name} shimmers briefly but nothing happens.", 'info')
            else:
                self.add_message("You have no accessory equipped to enchant.", 'warning')

        elif effect == 'genocide':
            # Kill all monsters of the most common visible type. Bosses/quest immune.
            visible = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            if not visible:
                self.add_message("No creatures are visible to target.", 'info')
            else:
                # Count by kind, excluding bosses and seal demons
                from collections import Counter
                kind_counts = Counter(
                    m.kind for m in visible
                    if not getattr(m, 'is_boss', False)
                    and m.max_hp <= 500
                    and not getattr(m, 'is_seal_demon', False)
                )
                if not kind_counts:
                    self.add_message("The scroll finds no suitable targets among these creatures.", 'warning')
                else:
                    target_kind = kind_counts.most_common(1)[0][0]
                    killed = 0
                    for m in list(self.monsters):
                        if m.alive and m.kind == target_kind:
                            m.hp = 0
                            m.alive = False
                            self._on_monster_killed(m)
                            killed += 1
                    target_name = next((m.name for m in self.monsters if m.kind == target_kind), target_kind)
                    self.add_message(
                        f"A wave of annihilation sweeps the level -- {killed} {target_name}(s) erased from existence!",
                        'success')

        elif effect == 'full_light':
            _buc = getattr(scroll, 'buc', 'uncursed')
            # Reveal entire level layout
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored[y][x] = True
            self.add_message("Brilliant light floods every corner of the level!", 'success')
            if _buc == 'blessed':
                self.player.add_effect('clairvoyant', 30)
                self.add_message("Your vision extends to sense all creatures!", 'success')

        elif effect == 'lake_of_fire':
            # The inscription is always revealed
            self.add_message(
                '"Then Death and Hades were thrown into the lake of fire."', 'info'
            )
            # Keep the scroll in inventory -- it may need to be read again
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
    # Identify menu  (i key -- philosophy quiz)
    # ------------------------------------------------------------------

    def _identify_item(self, item):
        display = self._display_name(item)
        self.quiz_title = f"IDENTIFYING {display.upper()}  --  PHILOSOPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                item.identified = True
                item.buc_known = True  # BUC revealed on identification
                self.player.known_item_ids.add(item.id)
                # Propagate to ALL items: inventory, ground, and every stored level
                self._propagate_identification(item.id)
                self.add_message(
                    f"The {display} is revealed: {item.name}!", 'success'
                )
                # Show BUC status if non-uncursed
                _buc = getattr(item, 'buc', 'uncursed')
                if _buc == 'blessed':
                    self.add_message("It radiates a holy aura.", 'success')
                elif _buc == 'cursed':
                    self.add_message("A dark aura clings to it.", 'warning')
                _qs_id = getattr(self, 'quirk_system', None)
                if _qs_id:
                    _qs_id.on_item_identified(item.id)
                # Chronicle legendary identifies
                itier = getattr(item, 'quiz_tier', getattr(item, 'tier', 1))
                if itier >= 4:
                    self._log_chronicle(f"Identified something remarkable: {item.name}. The lore runs deep.")
                # Show lore screen for the identified item
                if item.lore:
                    self._lore_subject = item
                    self.state = STATE_LORE
            else:
                self.add_message(
                    f"You ponder the {display} but gain no insight.", 'warning'
                )
            self._advance_turn()

        # Identification threshold scales with item tier: tier 1 -> 2/3 qs, tier 5 -> 6/9 qs
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
            base_seconds=self.player.get_quiz_timer('philosophy'),
        )

    # -- Necronomicon custom quiz data -----------------------------------------
    _NECRONOMICON_QUESTIONS = [
        {
            'question': 'What is the first word?',
            'choices': ['Klaatu', 'Kla-tu', 'Clawtoo?'],
            'answer': 'Klaatu',
        },
        {
            'question': 'What is the second word?',
            'choices': ['Barada', 'Barracuda', 'Barba'],
            'answer': 'Barada',
        },
        {
            'question': 'What is the final word?',
            'choices': ['N-cnghnhhnh', 'Nicotine', 'Nada'],
            'answer': 'Nikto',           # hidden 4th option via key "4"
            '_hidden_4': 'Nikto',         # marker for the draw code
        },
    ]

    def _learn_from_spellbook(self, book: 'Spellbook'):
        """Try to learn the spell in a spellbook via grammar threshold quiz."""
        spell_id = book.spell_id
        if spell_id in self.player.known_spells:
            self.add_message(f"You already know {book.spell_name}.", 'info')
            return

        # Necronomicon: custom "Say The Words" quiz
        if book.id == 'necronomicon':
            self._necronomicon_quiz(book)
            return

        self.state = STATE_QUIZ
        self.quiz_title = "DECIPHER SPELLBOOK -- GRAMMAR"

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                mp_cost = book.mp_cost
                self.player.known_spells[spell_id] = mp_cost
                book.identified = True
                self.player.remove_from_inventory(book)
                self.add_message(
                    f"You master the arcane text! {book.spell_name} learned! (costs {mp_cost} MP)", 'success')
                self._log_chronicle(f"Learned a new spell: {book.spell_name}. The words burned into my memory.")
            else:
                self.add_message(
                    "The text resists your understanding. Try again.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='grammar',
            tier=book.quiz_tier,
            callback=on_complete,
            threshold=book.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
            base_seconds=self.player.get_quiz_timer('grammar'),
        )

    def _necronomicon_quiz(self, book: 'Spellbook'):
        """The Necronomicon: recite The Words (Klaatu Barada Nikto).
        Three threshold questions with a hidden correct answer on Q3.
        Success: learn Army of Darkness. Failure: undead horde spawns."""
        import copy
        qs = [copy.deepcopy(q) for q in self._NECRONOMICON_QUESTIONS]
        # Inject into quiz engine as a custom pool
        qe = self.quiz_engine
        qe.state = QuizState.IDLE
        self.state = STATE_QUIZ
        self.quiz_title = "RECITE THE WORDS -- NECRONOMICON"
        self._necro_book = book
        self._necro_qs = qs
        self._necro_idx = 0
        self._necro_correct = 0
        self._necro_show_result = False
        self._necro_result_timer = 0.0
        self._necro_last_correct = None
        self._necro_ask_next()

    def _necro_ask_next(self):
        """Load the next Necronomicon question into the quiz engine display."""
        qe = self.quiz_engine
        q = self._necro_qs[self._necro_idx]
        qe.current_question = q
        qe.confused_order = None  # don't shuffle these
        qe.state = QuizState.ASKING
        qe.mode = QuizMode.THRESHOLD
        qe.subject = 'grammar'
        # Timer set once on first question, runs continuously (like all quizzes)
        if self._necro_idx == 0:
            _necro_timer = 10 + self.player.WIS
            qe.time_remaining = float(_necro_timer)
            qe.timer_seconds = _necro_timer
        qe.last_answer = ''
        qe.last_correct = False
        qe.correct_count = self._necro_correct
        qe.required = 3
        qe.tier = 1
        self._necro_show_result = False

    def _necro_answer(self, key: int):
        """Handle answer input for the Necronomicon quiz."""
        if self._necro_show_result:
            return  # waiting for result display to clear

        key_map = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
        }
        idx = key_map.get(key)
        if idx is None:
            return

        q = self._necro_qs[self._necro_idx]
        choices = q['choices']
        correct_answer = q['answer']

        # Hidden 4th option: "Nikto" on Q3 — only way to get it right
        if idx == 3 and '_hidden_4' in q:
            chosen = q['_hidden_4']
        elif idx < len(choices):
            chosen = choices[idx]
        else:
            return

        is_correct = chosen.strip().lower() == correct_answer.strip().lower()
        if is_correct:
            self._necro_correct += 1
            self.quiz_engine.correct_count = self._necro_correct

        # Show result briefly
        self._necro_last_correct = is_correct
        self._necro_show_result = True
        self._necro_result_timer = 0.6

        # Update quiz engine display for result feedback
        qe = self.quiz_engine
        qe.last_correct = is_correct
        qe.last_answer = chosen
        qe.state = QuizState.RESULT
        qe.result_timer = 0.6

        # If hidden 4th option was picked, add it to visible choices for result display
        if idx == 3 and '_hidden_4' in q:
            q['choices'].append(chosen)

    def _necro_update(self, dt: float):
        """Tick the Necronomicon result display timer."""
        if not self._necro_show_result:
            return
        self._necro_result_timer -= dt
        if self._necro_result_timer <= 0:
            self._necro_show_result = False
            self._necro_idx += 1
            if self._necro_idx >= len(self._necro_qs):
                self._necro_complete()
            else:
                self._necro_ask_next()

    def _necro_complete(self):
        """Resolve the Necronomicon quiz."""
        book = self._necro_book
        self.quiz_engine.state = QuizState.IDLE
        self.quiz_engine.current_question = None
        self.state = STATE_PLAYER

        if self._necro_correct == 3:
            # Perfect: learn Army of Darkness
            spell_id = book.spell_id
            mp_cost = book.mp_cost
            self.player.known_spells[spell_id] = mp_cost
            book.identified = True
            self.player.remove_from_inventory(book)
            self.add_message(
                "The words echo through the dungeon. The dead hear you. "
                "Army of Darkness learned!", 'success')
            _snd.play('spell_cast')
        else:
            # Failure: spawn hostile undead
            self.add_message(
                "Hey, I said the words! Maybe not every single little tiny "
                "syllable, but I said them!", 'danger')
            self._spawn_necronomicon_undead()
        self._necro_qs = None
        self._advance_turn()

    def _spawn_necronomicon_undead(self):
        """Spawn hostile Deadites when the Necronomicon quiz is failed."""
        import random
        from monster import Monster
        count = random.randint(4, 7)
        px, py = self.player.x, self.player.y
        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        lvl = max(1, self.dungeon_level)
        spawned = 0
        for _ in range(count):
            for _attempt in range(20):
                dx = random.randint(-3, 3)
                dy = random.randint(-3, 3)
                nx, ny = px + dx, py + dy
                if (nx, ny) in occupied or (nx, ny) == (px, py):
                    continue
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if self.dungeon.tiles[ny][nx] not in (1, 4):  # FLOOR or DOOR
                    continue
                defn = {
                    'id': 'deadite',
                    'name': 'Deadite',
                    'symbol': 'z',
                    'color': [160, 160, 210],
                    'ai_pattern': 'aggressive',
                    'hp': str(10 + lvl * 2),
                    'min_level': lvl,
                    'thac0': max(0, 18 - lvl // 5),
                    'attacks': [
                        {'name': 'claw', 'damage': f'1d4+{lvl // 10}', 'type': 'slash'},
                        {'name': 'bite', 'damage': f'1d3+{lvl // 15}', 'type': 'pierce'},
                    ],
                    'resistances': ['drain'],
                    'weaknesses': ['fire', 'holy'],
                    'lore': 'A shambling corpse raised by the Necronomicon. It knows only hunger.',
                }
                m = Monster(defn, nx, ny)
                self.monsters.append(m)
                occupied.add((nx, ny))
                spawned += 1
                break
        if spawned:
            self.add_message(
                f"{spawned} Deadites claw their way out of the ground!", 'danger')

    def _spawn_npc_deadite(self):
        """Spawn a single hostile Deadite where the NPC encounter was."""
        from monster import Monster
        npc_m = self._npc_encounter_monster
        if npc_m is None:
            return
        nx, ny = npc_m.x, npc_m.y
        lvl = max(1, self.dungeon_level)
        defn = {
            'id': 'deadite',
            'name': 'Deadite',
            'symbol': 'z',
            'color': [160, 160, 210],
            'ai_pattern': 'aggressive',
            'hp': str(20 + lvl * 3),
            'min_level': lvl,
            'thac0': max(0, 16 - lvl // 4),
            'attacks': [
                {'name': 'claw', 'damage': f'1d6+{lvl // 8}', 'type': 'slash'},
                {'name': 'bite', 'damage': f'1d4+{lvl // 10}', 'type': 'pierce'},
            ],
            'resistances': ['drain'],
            'weaknesses': ['fire', 'holy'],
            'lore': 'A shambling corpse raised by dark forces. It knows only hunger.',
        }
        m = Monster(defn, nx, ny)
        self.monsters.append(m)
        # Remove the NPC monster so it doesn't remain
        if npc_m in self.monsters:
            self.monsters.remove(npc_m)

    def _summon_undead_pets(self, count: int):
        """Summon friendly undead minions (pets) from Army of Darkness spell."""
        from pet_system import Pet
        px, py = self.player.x, self.player.y
        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        if hasattr(self, 'pets'):
            occupied |= {(p.x, p.y) for p in self.pets if p.alive}
        else:
            self.pets = []
        import random
        spawned = 0
        for _ in range(count):
            for _attempt in range(20):
                dx = random.randint(-3, 3)
                dy = random.randint(-3, 3)
                nx, ny = px + dx, py + dy
                if (nx, ny) in occupied or (nx, ny) == (px, py):
                    continue
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if self.dungeon.tiles[ny][nx] not in (1, 4):
                    continue
                # Create an undead pet using the existing Pet class
                pet = Pet('fire', nx, ny)  # reuse fire type as base
                pet.species = {
                    'element': 'shadow', 'damage_type': 'drain',
                    'color': (160, 160, 210),
                    'stages': [
                        {'name': 'Deadite', 'symbol': 'z',
                         'msg': 'A shambling deadite claws its way from the earth!'},
                        {'name': 'Deadite', 'symbol': 'z', 'msg': ''},
                        {'name': 'Deadite', 'symbol': 'z', 'msg': ''},
                    ],
                    'special_name': 'Drain Touch',
                    'special_status': 'slowed',
                    'special_status_chance': 0.3,
                }
                pet.level = max(1, self.dungeon_level // 10)
                pet.max_hp = 15 + self.dungeon_level
                pet.hp = pet.max_hp
                pet._refresh_stats()
                self.pets.append(pet)
                occupied.add((nx, ny))
                spawned += 1
                break

    def _propagate_identification(self, item_id: str):
        """Record that the player now recognises this item type by ID.

        We do NOT set item.identified = True on other instances -- that flag
        means 'this specific copy has been examined and modifiers are known'.
        Type recognition is tracked solely via player.known_item_ids.
        Also propagate buc_known to all same-id items in inventory.
        """
        self.player.known_item_ids.add(item_id)
        for inv_item in self.player.inventory:
            if inv_item.id == item_id and hasattr(inv_item, 'buc_known'):
                inv_item.buc_known = True

    # ------------------------------------------------------------------
    # Display name helper
    # ------------------------------------------------------------------

    _fix_name_case = staticmethod(fix_name_case)
    _a_or_an = staticmethod(a_or_an)

    def _auto_identify_all(self):
        """Identify every item in inventory and on the ground (Philosopher's Stone)."""
        for item in self.player.inventory:
            item.identified = True
            self.player.known_item_ids.add(item.id)
        for item in self.ground_items:
            item.identified = True
            self.player.known_item_ids.add(getattr(item, 'id', ''))
        # Equipped items too
        for slot_item in self.player.get_equipped_items():
            if slot_item:
                slot_item.identified = True
                self.player.known_item_ids.add(slot_item.id)

    def _display_name(self, item) -> str:
        """Return the name to show for an item, including stack count when > 1.

        Type known  (item.id in known_item_ids OR item.identified) -> item.name
        Type unknown                                                -> item.unidentified_name
        BUC tag shown when buc_known=True: {blessed} or {cursed}. Uncursed = no tag.
        """
        if not hasattr(item, 'identified'):
            base = self._fix_name_case(item.name)
        elif item.identified or item.id in self.player.known_item_ids:
            base = self._fix_name_case(item.name)
        else:
            base = self._fix_name_case(getattr(item, 'unidentified_name', item.name))
        # BUC prefix when known
        buc = getattr(item, 'buc', 'uncursed')
        buc_known = getattr(item, 'buc_known', False)
        if buc_known and buc != 'uncursed':
            base = f"{{{buc}}} {base}"
        count = getattr(item, 'count', 1)
        return f"{base} x{count}" if count > 1 else base

    def _show_item_comparison(self, item):
        """Show a brief comparison hint if the ground item is comparable to equipped gear."""
        if not self._item_is_known(item):
            return  # Can't compare unidentified items
        if isinstance(item, Weapon):
            equipped = self.player.weapon
            if equipped:
                ground_dmg = getattr(item, 'base_damage', 0) + getattr(item, 'enchant_bonus', 0)
                eq_dmg = getattr(equipped, 'base_damage', 0) + getattr(equipped, 'enchant_bonus', 0)
                diff = ground_dmg - eq_dmg
                if diff > 0:
                    self.add_message(f"  (+{diff} damage vs your {equipped.name})", 'success')
                elif diff < 0:
                    self.add_message(f"  ({diff} damage vs your {equipped.name})", 'warning')
        elif isinstance(item, Armor):
            slot = getattr(item, 'slot', 'body')
            from items import ARMOR_SLOTS
            slot_idx = ARMOR_SLOTS.index(slot) if slot in ARMOR_SLOTS else None
            if slot_idx is not None:
                equipped = self.player.armor_slots[slot_idx]
                if equipped:
                    ground_ac = getattr(item, 'ac_bonus', 0) + getattr(item, 'enchant_bonus', 0)
                    eq_ac = getattr(equipped, 'ac_bonus', 0) + getattr(equipped, 'enchant_bonus', 0)
                    diff = ground_ac - eq_ac
                    if diff > 0:
                        self.add_message(f"  (+{diff} AC vs your {equipped.name})", 'success')
                    elif diff < 0:
                        self.add_message(f"  ({diff} AC vs your {equipped.name})", 'warning')
        elif isinstance(item, Shield):
            equipped = self.player.shield
            if equipped:
                ground_ac = getattr(item, 'ac_bonus', 0) + getattr(item, 'enchant_bonus', 0)
                eq_ac = getattr(equipped, 'ac_bonus', 0) + getattr(equipped, 'enchant_bonus', 0)
                diff = ground_ac - eq_ac
                if diff > 0:
                    self.add_message(f"  (+{diff} AC vs your {equipped.name})", 'success')
                elif diff < 0:
                    self.add_message(f"  ({diff} AC vs your {equipped.name})", 'warning')

    # ------------------------------------------------------------------
    # Ranged targeting
    # ------------------------------------------------------------------

    def _open_targeting(self):
        """Enter targeting mode for ranged attacks (f key)."""
        weapon = self.player.ranged_weapon
        if not weapon or not weapon.requires_ammo:
            self.add_message("You have no ranged weapon equipped.", 'warning')
            return

        # Check ammo (skip for infinite ammo weapons like Sling of David)
        ammo_type = weapon.requires_ammo
        if not getattr(weapon, 'infinite_ammo', False):
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
        self._melee_targeting = False

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            # No valid targets -- cursor starts on player
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        if candidates:
            self.add_message(
                f"Targeting with {weapon.name} -- arrow keys to move, TAB to cycle, ENTER to fire, ESC to cancel.",
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
        """Handle key input while in targeting mode (ranged or melee)."""
        # TAB / t -- cycle through valid monster targets
        if key in (pygame.K_TAB, pygame.K_t) and self._target_candidates:
            self._target_idx = (self._target_idx + 1) % len(self._target_candidates)
            m = self._target_candidates[self._target_idx]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
            return

        # Arrow / vi keys -- cursor movement
        if key in self._TARGET_MOVE_KEYS:
            dx, dy = self._TARGET_MOVE_KEYS[key]
            nx = self.target_cursor_x + dx
            ny = self.target_cursor_y + dy
            # Clamp to dungeon bounds
            nx = max(0, min(nx, self.dungeon.width - 1))
            ny = max(0, min(ny, self.dungeon.height - 1))
            # Melee targeting: clamp to weapon reach (Chebyshev distance)
            if self._melee_targeting:
                px, py = self.player.x, self.player.y
                reach = getattr(self, '_melee_reach', 1)
                if max(abs(nx - px), abs(ny - py)) > reach:
                    return  # don't move cursor beyond reach
                if nx == px and ny == py:
                    return  # can't target own tile
            # Throw targeting: clamp to throw range
            if self._throw_targeting:
                px, py = self.player.x, self.player.y
                if max(abs(nx - px), abs(ny - py)) > self._throw_reach:
                    return
                if nx == px and ny == py:
                    return
            # Observe targeting: clamp to sight range (own tile allowed)
            if self._observe_targeting:
                px, py = self.player.x, self.player.y
                if max(abs(nx - px), abs(ny - py)) > getattr(self, '_observe_reach', 99):
                    return
            self.target_cursor_x = nx
            self.target_cursor_y = ny
            return

        # ENTER / SPACE / f / a / y -- confirm target
        confirm_keys = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_f)
        if self._melee_targeting:
            confirm_keys = confirm_keys + (pygame.K_a,)
        if self._throw_targeting:
            confirm_keys = confirm_keys + (pygame.K_y,)
        if self._observe_targeting:
            confirm_keys = confirm_keys + (pygame.K_o,)
        if self._wand_targeting:
            confirm_keys = confirm_keys + (pygame.K_z,)
        if getattr(self, '_power_targeting', False):
            confirm_keys = confirm_keys + (pygame.K_v,)
        if key in confirm_keys:
            if getattr(self, '_power_targeting', False):
                self._confirm_power_target()
                return
            if self._wand_targeting:
                self._confirm_wand_target()
            elif self._observe_targeting:
                self._confirm_observe()
            elif self._throw_targeting:
                self._confirm_throw_target()
            elif self._melee_targeting:
                self._confirm_melee_target()
            else:
                self._confirm_ranged_target()

    def _confirm_wand_target(self):
        """Confirm wand target, then start the science quiz."""
        from combat import _line_of_sight
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self._wand_targeting = False
        wand = self._pending_wand
        self._pending_wand = None

        target = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
        if not target or (cx, cy) not in self.visible:
            self.add_message("No valid target.", 'warning')
            self.state = STATE_PLAYER
            return

        # Line of sight check
        if not _line_of_sight(self.player.x, self.player.y, cx, cy, self.dungeon):
            self.add_message("No clear line of sight!", 'warning')
            self.state = STATE_PLAYER
            return

        # Store target for the quiz callback
        self._wand_target_monster = target
        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  --  SCIENCE"
        self.state = STATE_QUIZ
        _was_identified = getattr(wand, 'identified', False) or wand.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            _qs_wand = getattr(self, 'quirk_system', None)
            if _qs_wand:
                _qs_wand.on_wand_zapped(wand.id, was_identified=_was_identified)

            if not result.success:
                self.add_message("The wand fizzes and fails to fire.", 'warning')
                self._advance_turn()
                return

            wand.charges -= 1
            # Override auto-target with stored target
            self._wand_override_target = self._wand_target_monster
            self._apply_wand_effect(wand)
            self._wand_override_target = None
            if wand.charges <= 0:
                self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                self.player.remove_from_inventory(wand)
            else:
                self.add_message(f"({wand.charges} charges remain)", 'info')
            self._advance_turn()

        # All wands use threshold quiz — power is baked into the wand's tier
        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='science',
            tier=wand.quiz_tier,
            callback=on_complete,
            threshold=getattr(wand, 'quiz_threshold', 2),
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
            base_seconds=self.player.get_quiz_timer('science'),
            )

    def _confirm_power_target(self):
        """Confirm targeted power (e.g. Fire Breath)."""
        from combat import _line_of_sight
        cx, cy = self.target_cursor_x, self.target_cursor_y
        pid = getattr(self, '_pending_power', None)
        self._power_targeting = False
        self._pending_power = None

        target = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
        if not target or (cx, cy) not in self.visible:
            self.add_message("No valid target.", 'warning')
            self.state = STATE_PLAYER
            return
        if not _line_of_sight(self.player.x, self.player.y, cx, cy, self.dungeon):
            self.add_message("No clear line of sight!", 'warning')
            self.state = STATE_PLAYER
            return

        if pid and pid.startswith('spell_'):
            # Targeted spell: start the quiz with this target
            spell = getattr(self, '_pending_spell', None)
            spell_id = getattr(self, '_pending_spell_id', None)
            self._pending_spell = None
            self._pending_spell_id = None
            if spell:
                self._start_spell_quiz(spell, spell_id, target)
            return  # quiz handles state + advance_turn

        if pid == 'sketch_manifest':
            # Store target for quiz callback, then start AI escalator chain
            self._sketch_target_monster = target
            self.add_message(
                f"You begin sketching the {target.name} with furious concentration...", 'info')
            self.quiz_title = "MANIFESTING -- AI"
            self.state = STATE_QUIZ
            pl = self.player

            def _on_sketch_complete(result):
                chain = result.score
                monster = self._sketch_target_monster
                self._sketch_target_monster = None
                if chain == 0:
                    self.add_message(
                        "The sketch smudges and fades to nothing. The page goes blank.", 'warning')
                    self.state = STATE_PLAYER
                    self._advance_turn()
                    return
                duration = 5 * chain
                # Find a walkable tile adjacent to the player for the pet
                from pet_system import SketchedPet
                px, py = pl.x, pl.y
                placed = False
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    nx, ny = px + dx, py + dy
                    if (self.dungeon.is_walkable(nx, ny)
                            and not any(m.alive and m.x == nx and m.y == ny for m in self.monsters)
                            and not any(p.alive and p.x == nx and p.y == ny for p in self.pets)):
                        pet = SketchedPet(monster, nx, ny, duration)
                        self.pets.append(pet)
                        placed = True
                        break
                if not placed:
                    # Fallback: place on player tile
                    pet = SketchedPet(monster, px, py, duration)
                    self.pets.append(pet)
                self.add_message(
                    f"The sketch shimmers and peels off the page! "
                    f"A Sketched {monster.name} materializes! ({duration} turns)",
                    'success')
                pl.power_cooldowns['sketch_manifest'] = 500
                self.state = STATE_PLAYER
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='escalator_chain',
                subject='ai',
                tier=1,
                callback=_on_sketch_complete,
                max_chain=5,
                wisdom=pl.WIS,
                timer_modifier=pl.get_quiz_timer_modifier(),
                extra_seconds=pl.get_quiz_extra_seconds('ai'),
                base_seconds=pl.get_quiz_timer('ai'),
            )
            return  # don't call _advance_turn or set STATE_PLAYER — quiz handles it

        if pid == 'stuffie_fire_breath':
            # Store cone target for quiz callback
            self._stuffie_cone_target = (cx, cy)
            self.add_message(
                "The Charmander Stuffie glows warm... focus your fire!", 'info')
            self.quiz_title = "FIRE BREATH -- AI"
            self.state = STATE_QUIZ
            pl = self.player

            def _on_fire_breath(result):
                chain = result.score
                if chain == 0:
                    self.add_message(
                        "The Stuffie flickers and dims. The fire fizzles out.", 'warning')
                    self.state = STATE_PLAYER
                    self._advance_turn()
                    return
                from dice import roll as _fb_roll
                from combat import get_cone_tiles
                # Damage scales with chain: base 3d6, +1d6 per chain level
                dice = f'{2 + chain}d6'
                base = _fb_roll(dice)
                scaled = self._int_scaled_damage(base)
                tcx, tcy = self._stuffie_cone_target
                px, py = pl.x, pl.y
                cone = get_cone_tiles(px, py, tcx, tcy, max_range=6)
                hits = 0
                kills = 0
                for m in list(self.monsters):
                    if m.alive and (m.x, m.y) in cone and (m.x, m.y) in self.visible:
                        m.take_damage(scaled)
                        hits += 1
                        if not m.alive:
                            self._on_monster_killed(m)
                            kills += 1
                self.add_message(
                    "The Charmander Stuffie glows white-hot! "
                    f"You breathe a cone of fire! ({dice} damage, chain {chain})", 'success')
                if hits:
                    self.add_message(
                        f"{hits} creatures engulfed for {scaled} fire damage! ({kills} slain)", 'combat')
                else:
                    self.add_message("The flames find no target.", 'info')
                pl.power_cooldowns['stuffie_fire_breath'] = 500
                self.state = STATE_PLAYER
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='escalator_chain',
                subject='ai',
                tier=1,
                callback=_on_fire_breath,
                max_chain=5,
                wisdom=pl.WIS,
                timer_modifier=pl.get_quiz_timer_modifier(),
                extra_seconds=pl.get_quiz_extra_seconds('ai'),
                base_seconds=pl.get_quiz_timer('ai'),
            )
            return  # quiz handles state + advance_turn

        self.state = STATE_PLAYER
        self._advance_turn()

    def _confirm_observe(self):
        """Describe whatever is at the cursor position. Free action."""
        cx, cy = self.target_cursor_x, self.target_cursor_y

        # Check if the tile is visible
        if (cx, cy) not in self.visible:
            self.add_message("You can't see that location.", 'info')
            self.state = STATE_PLAYER
            self._observe_targeting = False
            return

        found = False

        # Monster at cursor
        monster = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
        if monster:
            hp_pct = monster.hp / max(1, monster.max_hp)
            condition = (
                "uninjured" if hp_pct >= 1.0 else
                "lightly wounded" if hp_pct >= 0.7 else
                "wounded" if hp_pct >= 0.4 else
                "badly wounded" if hp_pct >= 0.15 else
                "near death"
            )
            self.add_message(
                f"You see {monster.name} ({condition}).", 'info'
            )
            found = True

        # Items at cursor
        from items import Container
        items_here = [i for i in self.ground_items if i.x == cx and i.y == cy]
        for item in items_here[:5]:
            dname = self._display_name(item)
            self.add_message(f"You see {dname} on the ground.", 'info')
            # Mimic detection via Observe — PER check
            if isinstance(item, Container) and getattr(item, 'is_mimic', False):
                import random as _prng
                per_chance = min(0.85, 0.15 + self.player.PER * 0.04)
                if _prng.random() < per_chance:
                    _OBSERVE_HINTS = [
                        "Something seems off\u2026 is that a tooth?",
                        "It glistens with what looks like saliva.",
                        "You could swear it just moved.",
                        "The hinges look oddly organic.",
                        "You notice a faint, predatory smell.",
                    ]
                    self.add_message(_prng.choice(_OBSERVE_HINTS), 'warning')
            found = True
        if len(items_here) > 5:
            self.add_message(f"...and {len(items_here) - 5} more items.", 'info')

        # Player's own tile
        if cx == self.player.x and cy == self.player.y and not found:
            if not items_here:
                self.add_message("You see yourself standing here.", 'info')
            found = True

        # Tile features
        tile = self.dungeon.tiles[cy][cx]
        _TILE_DESC = {
            STAIRS_UP:   "Stairs leading up.",
            STAIRS_DOWN: "Stairs leading down.",
            ALTAR:       "A sacred altar.",
            FOUNTAIN:    "A shimmering fountain.",
            GRAVE:       "A weathered gravestone.",
            THRONE:      "An ancient throne.",
            WATER:       "A pool of water.",
            LAVA:        "A pool of molten lava.",
            ICE:         "An icy floor.",
        }
        desc = _TILE_DESC.get(tile)
        if desc:
            self.add_message(desc, 'info')
            found = True

        if not found:
            self.add_message("You see nothing of interest.", 'info')

        # Return to player state — no turn cost
        self.state = STATE_PLAYER
        self._observe_targeting = False

    def _confirm_ranged_target(self):
        """Confirm a ranged shot at the cursor position."""
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
            self.add_message("No target there -- shot cancelled.", 'warning')

    def _confirm_melee_target(self):
        """Confirm a melee strike at the cursor position."""
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self.state = STATE_PLAYER

        # 1. Monster at cursor -- melee combat
        target = next(
            (m for m in self.monsters
             if m.alive and m.x == cx and m.y == cy),
            None
        )
        if target:
            self._start_combat(target)
            return

        # 2. Mystery altar at cursor
        from mystery_system import MysteryAltar
        altar = next(
            (item for item in self.ground_items
             if isinstance(item, MysteryAltar) and not item.activated
             and item.x == cx and item.y == cy),
            None
        )
        if altar is not None:
            self._start_mystery(altar)
            return

        # 3. Container at cursor -- mimic check / bash
        from items import Container
        from container_system import _spawn_mimic
        container = next(
            (item for item in self.ground_items
             if isinstance(item, Container) and not item.opened
             and item.x == cx and item.y == cy),
            None
        )
        if container is not None:
            if container.is_mimic:
                # Bash hits the mimic — player gets a free 10% HP strike
                mimic = _spawn_mimic(container, self.monsters, self.dungeon_level)
                self.ground_items.remove(container)
                mname = mimic.name if mimic else 'mimic'
                bash_dmg = max(1, int(mimic.max_hp * 0.10))
                mimic.hp -= bash_dmg
                self.add_message(
                    f"You bash the {container.name} -- it shrieks! It's {self._a_or_an(mname)}!", 'danger'
                )
                self.add_message(
                    f"Your blow connects before it can react! ({bash_dmg} damage)", 'success'
                )
                _snd.play('monster_hit')
            else:
                # Bashing a real chest damages fragile contents
                self.add_message(
                    f"You bash the {container.name}. You hear something shatter inside.", 'warning'
                )
                container.bash_damaged = True
            self._advance_turn()
            return

        # 4. Dig pit -- shovel equipped, targeting walkable floor with no pit
        weapon = self.player.weapon
        if weapon and getattr(weapon, 'can_dig', False):
            tile = self.dungeon.tiles[cy][cx]
            from dungeon import FLOOR
            _pits = getattr(self.dungeon, 'pits', set())
            if tile == FLOOR and (cx, cy) not in _pits:
                self._dig_pit(cx, cy)
                return
            elif (cx, cy) in _pits:
                self.add_message("There's already a pit there.", 'info')
                return

        # 5. Empty tile -- swing at air (costs a turn; may reveal invisible monsters)
        self.add_message("You swing at the empty space!", 'info')
        self._advance_turn()

    def _dig_pit(self, x: int, y: int):
        """Dig a pit at (x, y). Costs 30 SP and 3 turns."""
        sp_cost = 30
        if self.player.sp < sp_cost:
            self.add_message("You're too exhausted to dig! (need 30 SP)", 'warning')
            return
        self.player.sp -= sp_cost
        if not hasattr(self.dungeon, 'pits'):
            self.dungeon.pits = set()
        self.dungeon.pits.add((x, y))
        self.add_message("You dig a pit in the floor!", 'success')
        _snd.play('trap')
        if not getattr(self, '_chronicle_first_pit', False):
            self._chronicle_first_pit = True
            self._log_chronicle("Dug a pit with the shovel. Took everything I had. If something walks over this...")
        # Costs 3 turns (advancing turn 3 times — monsters get 3 actions)
        for _ in range(3):
            self._advance_turn()
            if self.state == STATE_DEAD:
                return

    def _player_fall_in_pit(self, x: int, y: int):
        """Player walks onto a pit and falls in. Applies in_pit effect."""
        if self.player.has_effect('levitating'):
            self.add_message("You float over a pit.", 'info')
            return
        if self.player.has_effect('in_pit'):
            return  # already in a pit
        from dice import roll as _dice_roll
        dmg = _dice_roll('1d4')
        actual = self.player.take_damage(dmg, 'physical')
        self.player.add_effect('in_pit', 1)  # duration 1 = cleared on next move
        self.add_message(f"You fall into a pit! ({actual} damage)", 'danger')

    def _fire_ranged(self, monster):
        """Consume one ammo and launch the math chain quiz for a ranged shot."""
        weapon = self.player.ranged_weapon
        ammo_type = weapon.requires_ammo
        ammo_item = None

        # Consume one ammo item (skip for infinite ammo weapons)
        if not getattr(weapon, 'infinite_ammo', False):
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
        self.quiz_title = (
            f"FIRE {weapon.name.upper()} at {monster.name.upper()}  --  MATH CHAIN"
        )

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            if chain == 0:
                self.add_message(
                    f"Your shot flies wide -- you miss the {monster.name}!", 'warning'
                )
            else:
                self.add_message(
                    f"Chain x{chain}! Your {weapon.requires_ammo} strikes the {monster.name} for {damage} damage!",
                    'success'
                )
                if killed:
                    self._on_monster_killed(monster)
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

        # Tablet of Destinies: allow quiz reroll if not used this floor
        self.quiz_engine._reroll_flag = self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False)
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
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  --  MATH CHAIN"
        if monster.kind == 'abaddon_destroyer' and not getattr(self, '_chronicle_abaddon_start', False):
            self._chronicle_abaddon_start = True
            self._log_chronicle("Abaddon. The Destroyer. He's real. He's here. This is it.")
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_combat_started()
        self._combat_hp_pct_before = self.player.hp / max(1, self.player.max_hp)

        if monster.kind == 'floating_eye':
            cur = self.player.status_effects.get('paralyzed', 0)
            self.player.status_effects['paralyzed'] = max(cur, 3)
            self.add_message("The floating eye's gaze paralyzes you!", 'danger')

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            # Tablet of Destinies: mark reroll as used this floor
            if getattr(self.quiz_engine, 'reroll_was_used', False):
                self._quiz_reroll_used = True
                self.add_message("The Tablet of Destinies cracks — fate rewritten!", 'info')
            if chain == 0:
                self.add_message(
                    f"You swing wildly at the {monster.name} and miss!", 'warning'
                )
            elif (chain >= 1 and monster.kind == 'fenrir_wolf' and monster.alive
                  and any(getattr(i, 'id', '') == 'vidars_sandal'
                          for i in self.player.inventory)):
                # Vidar's Sandal instant kill!
                monster.hp = 0
                monster.alive = False
                _snd.play('monster_hit')
                self.add_message(
                    "You plant Vidar's Sandal against Fenrir's lower jaw!", 'combat')
                self.add_message(
                    "With impossible strength, you wrench the great wolf's mouth apart!", 'combat')
                self.add_message(
                    "FENRIR, THE WORLD-WOLF, IS TORN ASUNDER!", 'success')
                self._on_monster_killed(monster)
                _qs_kill = getattr(self, 'quirk_system', None)
                if _qs_kill:
                    _qs_kill.on_monster_killed(monster.kind)
                self._advance_turn()
                return
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
                if kwargs.get('poisoned'):
                    msg += f" The {monster.name} is poisoned!"
                if kwargs.get('burned'):
                    msg += f" The {monster.name} is burning!"
                if kwargs.get('confused'):
                    msg += f" The {monster.name} is confused!"
                if kwargs.get('petrified'):
                    msg += f" The {monster.name} is turning to stone!"
                if kwargs.get('healed'):
                    msg += " You absorb life energy!"
                self.add_message(msg, 'success')
                if killed:
                    self._on_monster_killed(monster)
                    # Amenonuhoko: slow adjacent monsters on kill
                    w = self.player.weapon
                    if w and getattr(w, 'aoe_slow_on_kill', False):
                        for m in self.monsters:
                            if m.alive and abs(m.x - monster.x) <= 1 and abs(m.y - monster.y) <= 1:
                                m.add_effect('slowed', 3)
                        self.add_message("A wave of primordial stillness ripples outward.", 'info')
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

        # Tablet of Destinies: allow quiz reroll if not used this floor
        self.quiz_engine._reroll_flag = self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False)
        player_attack(self.player, monster, self.quiz_engine, on_complete)

    def _quiz_input(self, key: int):
        # Necronomicon custom quiz intercept
        if hasattr(self, '_necro_qs') and self._necro_qs is not None:
            self._necro_answer(key)
            return

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

        # Death acts first -- not part of self.monsters to avoid save/load issues
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            all_m = self.monsters + [dm]
            _pet_occ_d = {(p.x, p.y) for p in self.pets if p.alive}
            did_attack = dm.take_turn(self.player, self.dungeon, all_m,
                                      extra_occupied=_pet_occ_d)
            if did_attack:
                dmg, msg = dm.attack(self.player)
                self.add_message(msg, 'danger')
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

        # --- Ariadne's Thread: neutralize wall-phasing monsters ---
        has_thread = any(getattr(i, 'id', '') == 'ariadnes_thread'
                         for i in self.player.inventory)
        for m in self.monsters:
            if getattr(m, 'can_phase_walls', False):
                if has_thread:
                    m.can_phase_walls = False
                    m.speed = min(m.speed, 6)  # slowed by the Thread's power
                    if m.ai_pattern == 'hit_and_run':
                        m.ai_pattern = 'aggressive'  # can't hide anymore

        for m in self.monsters:
            if not m.alive:
                continue
            # Allied monsters (angels): handle separately
            if getattr(m, 'is_allied', False):
                m.take_turn(self.player, self.dungeon, self.monsters,
                            extra_occupied={(_p.x, _p.y) for _p in self.pets if _p.alive})
                _ann = getattr(m, '_annihilate_target', None)
                if _ann and _ann.alive:
                    _ann.alive = False
                    _ann.hp = 0
                    m.alive = False
                    m.hp = 0
                    if (m.x, m.y) in self.visible or (_ann.x, _ann.y) in self.visible:
                        self.add_message(
                            "An angel meets a locust in a blaze of holy fire! Both are consumed!",
                            'success')
                continue
            # Track monsters the player has seen (for encyclopedia bestiary)
            if (m.x, m.y) in self.visible:
                self.player.known_monster_ids.add(m.kind)
            _pet_occ = {(p.x, p.y) for p in self.pets if p.alive}
            _was_in_pit = m.has_effect('stuck_in_pit')
            _pos_before = (m.x, m.y)
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters,
                                     extra_occupied=_pet_occ)
            # Confused friendly fire message
            _cf_hit = getattr(m, '_confused_hit', None)
            if _cf_hit:
                victim, dmg = _cf_hit
                m._confused_hit = None
                if (m.x, m.y) in self.visible or (victim.x, victim.y) in self.visible:
                    self.add_message(
                        f"The confused {m.name} attacks the {victim.name} for {dmg} damage!", 'combat')
                if not victim.alive:
                    self._on_monster_killed(victim)
            # Abaddon locust swarm spawning
            if getattr(m, '_wants_locust_spawn', False) and m.kind == 'abaddon_destroyer':
                m._wants_locust_spawn = False
                self._spawn_abaddon_locusts(m)
            # Fenrir rage escalation message
            rage_msg = getattr(m, '_rage_message', '')
            if rage_msg and (m.x, m.y) in self.visible:
                self.add_message(rage_msg, 'danger')
            # Check if monster moved onto a dug pit
            if (not _was_in_pit and not m.has_effect('stuck_in_pit')
                    and not m.has_effect('levitating')
                    and (m.x, m.y) != _pos_before
                    and (m.x, m.y) in getattr(self.dungeon, 'pits', set())):
                from dice import roll as _pit_roll
                pit_dmg = _pit_roll('1d4')
                m.hp -= pit_dmg
                if m.hp <= 0:
                    m.alive = False
                m.status_effects['stuck_in_pit'] = random.randint(3, 4)
                if (m.x, m.y) in self.visible:
                    self.add_message(f"The {m.name} falls into a pit!", 'info')
                if not m.alive:
                    self._on_monster_killed(m)
                continue  # can't attack this turn — just fell
            if did_attack:
                # Displacement: 30% miss chance
                if self.player.has_effect('displacement') and random.random() < 0.30:
                    self.add_message(f"The {m.name}'s attack passes through your displaced image!", 'info')
                    continue

                _effects_before = set(self.player.status_effects.keys())
                dmg, msg = m.attack(self.player)
                self.add_message(msg, 'danger')

                # Piercing collateral: damage monsters in the projectile path
                _collateral = getattr(m, '_piercing_collateral', [])
                if _collateral and dmg > 0:
                    _coll_frac = random.uniform(0.75, 0.90)
                    _coll_dmg = max(1, int(dmg * _coll_frac))
                    for _cv in _collateral:
                        if not _cv.alive:
                            continue
                        _cv.hp -= _coll_dmg
                        if (m.x, m.y) in self.visible or (_cv.x, _cv.y) in self.visible:
                            self.add_message(
                                f"The {m.name}'s attack tears through the {_cv.name} for {_coll_dmg} collateral damage!",
                                'combat')
                        if _cv.hp <= 0:
                            _cv.alive = False
                            self._on_monster_killed(_cv)
                    m._piercing_collateral = []

                # SP drain (locusts, famine demon)
                _sp_drain = getattr(m, 'sp_drain', 0)
                if _sp_drain > 0 and dmg > 0:
                    self.player.sp = max(0, self.player.sp - _sp_drain)
                    self.add_message(
                        f"The {m.name}'s attack drains your stamina! (-{_sp_drain} SP)", 'danger')

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

                # Tarnhelm: auto-invisibility when HP drops below 30%
                if dmg > 0 and not getattr(self, '_tarnhelm_used', False):
                    if self.player.hp > 0 and self.player.hp / max(1, self.player.max_hp) < 0.30:
                        for _arm_slot in self.player.armor_slots:
                            if _arm_slot and getattr(_arm_slot, 'invisibility_power', False):
                                self.player.add_effect('invisible', _arm_slot.invisibility_duration)
                                self._tarnhelm_used = True
                                self.add_message("The Tarnhelm shimmers — you vanish from sight!", 'success')
                                break

                # Green Chapel Axe: heal when hit
                _wpn = self.player.weapon
                if _wpn and getattr(_wpn, 'on_hit_regen', 0) > 0 and dmg > 0:
                    _regen_amt = _wpn.on_hit_regen
                    self.player.hp = min(self.player.max_hp, self.player.hp + _regen_amt)
                    self.add_message(f"The green axe mends your wounds. (+{_regen_amt} HP)", 'info')

                # Svalinn: reflect fire damage back at attacker
                _shld = self.player.shield
                if _shld and getattr(_shld, 'fire_reflect', 0) > 0 and dmg > 0:
                    _atk_types = getattr(m, 'damage_types', getattr(m, 'attack_types', []))
                    if 'fire' in _atk_types:
                        _fire_ref = max(1, int(dmg * _shld.fire_reflect))
                        m.hp -= _fire_ref
                        self.add_message(f"Svalinn reflects flame back at the {m.name} for {_fire_ref}!", 'combat')
                        if m.hp <= 0 and m.alive:
                            m.alive = False
                            self._on_monster_killed(m)

                # Babr-e Bayan: absorb first hit per floor
                if dmg > 0 and not getattr(self, '_first_hit_used', False):
                    for _arm_slot in self.player.armor_slots:
                        if _arm_slot and getattr(_arm_slot, 'first_hit_absorb', False):
                            self.player.hp = min(self.player.max_hp, self.player.hp + dmg)
                            self._first_hit_used = True
                            self.add_message("The tiger-skin absorbs the blow completely!", 'success')
                            break

                # Jade Cicada: death save (once per floor)
                if self.player.hp <= 0 and not getattr(self, '_death_save_used', False):
                    for _acc in (self.player.amulet, self.player.ring):
                        if _acc and getattr(_acc, 'death_save', False):
                            self.player.hp = 1
                            self._death_save_used = True
                            self.add_message("The jade cicada cracks — but holds! You cling to life!", 'success')
                            _snd.play('player_healed')
                            break

                # Ankh of Isis: resurrect on death (consumes the item)
                if self.player.hp <= 0:
                    for _acc_slot in ('amulet', 'ring'):
                        _acc = getattr(self.player, _acc_slot, None)
                        if _acc and getattr(_acc, 'resurrect_on_death', False):
                            self.player.hp = max(1, self.player.max_hp // 2)
                            setattr(self.player, _acc_slot, None)
                            self.add_message("The Ankh of Isis shatters! Isis breathes life back into you!", 'success')
                            self._log_chronicle("I died. Then light. Isis pulled me back. The ankh is dust now.")
                            _snd.play('player_healed')
                            break

                # Life Save: if the blow was fatal, survive at 1 HP (burns the amulet)
                if self.player.hp <= 0 and self.player.has_effect('life_save'):
                    self.player.hp = 1
                    del self.player.status_effects['life_save']
                    self.add_message(
                        "The amulet blazes -- death averted! Its life-saving magic is spent.", 'success'
                    )
                    _snd.play('player_healed')

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

                # Spell Turning: reflect 100% of newly applied debuffs back at attacker
                if self.player.has_effect('spell_turning') and _new_effects:
                    from status_effects import DEBUFFS as _DEBUFFS
                    for _new_eff in list(_new_effects):
                        if _new_eff in _DEBUFFS:
                            del self.player.status_effects[_new_eff]
                            m.add_effect(_new_eff, 8)
                            self.add_message(
                                f"Your spell turning reflects the {_new_eff.replace('_', ' ')} "
                                f"back at the {m.name}!", 'info'
                            )

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

    def _do_pet_turns(self):
        """Process pet AI, XP, regen, cooldowns, and monster attacks on pets."""
        if not self.pets:
            return

        # Compute quiz accuracy for pet damage scaling
        total_q = self.correct_answers + self.wrong_answers
        quiz_acc = self.correct_answers / max(1, total_q)

        for pet in self.pets:
            if not pet.alive:
                continue

            # Pet AI turn
            result = pet.take_turn(self.player, self.dungeon, self.monsters, self.pets, self.ground_items)
            if result:
                action = result[0] if isinstance(result, tuple) else None
                # Unicorn pet returns ('unicorn_actions', [...]) instead of combat
                if action == 'unicorn_actions':
                    for msg in result[1]:
                        if msg[0] == 'heal':
                            self.add_message(f"The unicorn's horn glows softly — you heal {msg[1]} HP.", 'success')
                        elif msg[0] == 'cleanse':
                            self.add_message(f"The unicorn purifies you — {msg[1]} removed!", 'success')
                        elif msg[0] == 'trap':
                            self.add_message("The unicorn stamps nervously — trap sensed nearby!", 'warning')
                    continue
                target = result[1] if len(result) > 1 else None
                if action == 'special' and target and target.alive:
                    dmg = pet.get_special_damage(quiz_acc)
                    actual = target.take_damage(dmg)
                    pet.use_special()
                    sp = pet.species
                    self.add_message(
                        f"{pet.name} uses {sp['special_name']} on {target.name}! ({actual} damage)",
                        'combat'
                    )
                    # Apply special status effect
                    if random.random() < sp['special_status_chance'] and target.alive:
                        target.status_effects[sp['special_status']] = \
                            max(target.status_effects.get(sp['special_status'], 0), 4)
                    if not target.alive:
                        self._on_monster_killed(target)
                elif action == 'attack' and target.alive:
                    dmg = pet.get_attack_damage(quiz_acc)
                    actual = target.take_damage(dmg)
                    if getattr(pet, 'is_dad', False):
                        self.add_message(
                            f"Dad punched {target.name} in the face for {actual} damage!",
                            'success')
                    else:
                        self.add_message(
                            f"{pet.name} attacks {target.name}! ({actual} damage)", 'combat')
                    if not target.alive:
                        self._on_monster_killed(target)

            # XP, regen, cooldown
            msgs = pet.gain_xp(1)
            for msg in msgs:
                self.add_message(msg, 'success')
            # Trainer's Cap: pet_regen_bonus from head armor
            _prb = 0
            _head = self.player.armor_slots[0] if self.player.armor_slots else None
            if _head:
                _prb = getattr(_head, 'pet_regen_bonus', 0)
            pet.tick_regen(bonus=_prb)
            pet.tick_cooldown()

            # Temporary pet duration ticks
            if getattr(pet, 'is_dad', False) and pet.alive:
                if pet.tick_duration():
                    self.add_message(
                        "Dad smiles at you and fades away. He believes in you!", 'success')
            elif getattr(pet, 'is_sketch', False) and pet.alive:
                if pet.tick_duration():
                    self.add_message(
                        f"The Sketched {pet.monster_name} shimmers, fades, and dissolves "
                        f"back into the pages of the sketchbook.", 'info')

        # Monsters attack adjacent pets (each monster can swipe at one pet per turn)
        for m in self.monsters:
            if not m.alive:
                continue
            for pet in self.pets:
                if not pet.alive:
                    continue
                if max(abs(m.x - pet.x), abs(m.y - pet.y)) <= 1:
                    # Monster swipes at pet — use a fraction of its normal damage
                    from dice import roll as _dice_roll
                    pet_dmg = max(1, _dice_roll(m.attacks[0]['damage']) // 2) if m.attacks else 1
                    pet.take_damage(pet_dmg)
                    if not pet.alive:
                        if getattr(pet, 'is_sketch', False):
                            self.add_message(
                                f"The Sketched {pet.monster_name} shatters into "
                                f"fragments of ink and vanishes!", 'danger')
                        else:
                            self.add_message(f"{pet.name} has been slain by {m.name}!", 'danger')
                    break  # one pet swipe per monster per turn

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
            if hasattr(self, '_necro_qs') and self._necro_qs is not None:
                self._necro_update(dt)
            else:
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
                # Direction changed (or key released/pressed) -- restart delay
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


    # ------------------------------------------------------------------
    # Targeting overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Quiz modal
    # ------------------------------------------------------------------

    # Subject accent colours -- match the welcome screen domain ring


    # ------------------------------------------------------------------
    # Equip menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Accessory menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Wand menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Spell menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Scroll menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Identify menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Cook menu overlay
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Confirm exit overlay
    # ------------------------------------------------------------------

    _DROP_MAX_VISIBLE = 16  # max rows visible in drop menu before scrolling


    # ------------------------------------------------------------------
    # Story popup  (narrative events: entrance, boss victories, endings)
    # ------------------------------------------------------------------

    # All narrative content indexed by key
    _STORY_CONTENT = {
        'dungeon_entrance': {
            'title': 'THE PHILOSOPHER\'S QUEST',
            'accent': (80, 120, 200),
            'lines': [
                "Your village of Amber is dying.",
                "",
                "A magical plague -- born of corruption and forgotten wisdom -- has spread",
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
                "As you delve deeper, you may uncover lost codes -- ancient secrets",
                "known only to those who venture far enough to find them.",
                "Present them to your father for rewards.",
            ],
            'code': None,
        },
        'boss_asterion': {
            'title': 'ASTERION THE MINOTAUR FALLS',
            'accent': (180, 50, 50),
            'lines': [
                "Asterion was born of Pasiphae and a divine white bull sent by Poseidon --",
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
                "Perseus slew her by meeting her eyes only in a mirrored shield --",
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
                "He was a dwarf -- son of the sorcerer Hreidmar -- who murdered his own father",
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
                "Fenrir is the monstrous wolf of Norse prophecy -- son of Loki,",
                "so terrible that the gods themselves feared to approach him.",
                "They bound him with Gleipnir, a magical ribbon forged from impossible things:",
                "a cat's footstep, a mountain's roots, a woman's beard, a bear's sinew,",
                "a fish's breath, and a bird's spittle.",
                "",
                "At Ragnarok, he was prophesied to swallow Odin himself.",
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
                "Abaddon is named in Revelation as the angel of the bottomless pit --",
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
                "Your village of Amber will be saved.",
                "The plague will lift. The children will recover.",
                "The elders will weep with relief.",
                "The people who counted on you -- who believed in you --",
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
                "The village of Amber will not see another spring.",
                "",
                "You were not overcome by the dungeon.",
                "You overcame yourself -- and chose retreat.",
            ],
            'code': None,
        },
    }

    # Map monster kind -> story key (only for bosses)
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


    # ------------------------------------------------------------------
    # Victory screen
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Death / defeat screen
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Study Journal  (; key — in-game missed question review)
    # ------------------------------------------------------------------

    _STUDY_SUBJECTS = [
        'all', 'math', 'geography', 'history', 'animal', 'cooking',
        'science', 'philosophy', 'grammar', 'economics', 'theology', 'ai',
    ]

    def _open_study_journal(self):
        """Open the study journal to review missed questions by category."""
        if not self.missed_questions:
            self.add_message("No missed questions to review yet.", 'info')
            return
        self._study_subject_idx = 0  # 0 = 'all'
        self._study_question_idx = 0
        self._study_filtered = list(self.missed_questions)
        self.state = STATE_STUDY

    def _study_filter(self):
        """Return missed questions filtered by the current subject selection."""
        subj = self._STUDY_SUBJECTS[self._study_subject_idx]
        if subj == 'all':
            return list(self.missed_questions)
        return [q for q in self.missed_questions if q['subject'] == subj]

    def _study_input(self, key):
        """Handle input in the study journal.
        Left/Right: cycle subject tabs.
        Up/Down: scroll through questions in current category."""
        # Left/Right: cycle subject category
        if key == pygame.K_LEFT:
            self._study_subject_idx = (self._study_subject_idx - 1) % len(self._STUDY_SUBJECTS)
            self._study_filtered = self._study_filter()
            self._study_question_idx = 0
            self._study_scroll = 0
        elif key == pygame.K_RIGHT:
            self._study_subject_idx = (self._study_subject_idx + 1) % len(self._STUDY_SUBJECTS)
            self._study_filtered = self._study_filter()
            self._study_question_idx = 0
            self._study_scroll = 0
        # Up/Down: page through questions within category
        elif key in (pygame.K_DOWN, pygame.K_SPACE, pygame.K_RETURN):
            if self._study_filtered:
                self._study_question_idx = min(
                    getattr(self, '_study_question_idx', 0) + 1, len(self._study_filtered) - 1)
        elif key in (pygame.K_UP, pygame.K_BACKSPACE):
            self._study_question_idx = max(0, getattr(self, '_study_question_idx', 0) - 1)


    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------

    def _help_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_SLASH, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # Examine corpse  (via I identify menu -> philosophy quiz -> lore)
    # ------------------------------------------------------------------

    def _examine_corpse_direct(self, corpse):
        """Called when player selects a corpse from the identify menu."""
        if corpse.lore_identified:
            self._lore_subject = corpse
            self.state = STATE_LORE
            return
        self.quiz_title = f"EXAMINING {corpse.monster_name.upper()} CORPSE  --  PHILOSOPHY"
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
            threshold=max(1, min(5, getattr(corpse, 'harvest_tier', 1) + 1)) + 1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('philosophy'),
            base_seconds=self.player.get_quiz_timer('philosophy'),
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
        self.quiz_title = f"EXAMINING {corpse.monster_name.upper()} CORPSE  --  PHILOSOPHY"
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
            threshold=max(1, min(5, getattr(corpse, 'harvest_tier', 1) + 1)) + 1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('philosophy'),
            base_seconds=self.player.get_quiz_timer('philosophy'),
        )

    def _lore_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
            self.state = STATE_PLAYER


    class _GoldDropEntry:
        """Sentinel shown in the drop menu when player has gold to drop."""
        id = '_gold_drop'
        @property
        def name(self): return "Drop Gold"

    _DROP_TABS = [
        ('All',         None),
        ('Equipment',   lambda i: hasattr(i, 'item_class') and getattr(i, 'item_class', '') in ('weapon','armor','shield','accessory','ammo')),
        ('Consumables', lambda i: hasattr(i, 'item_class') and getattr(i, 'item_class', '') in ('potion','scroll','spellbook','wand','food')),
        ('Ingredients', lambda i: hasattr(i, 'item_class') and getattr(i, 'item_class', '') == 'ingredient'),
        ('Other',       lambda i: hasattr(i, 'item_class') and getattr(i, 'item_class', '') not in ('weapon','armor','shield','accessory','ammo','potion','scroll','spellbook','wand','food','ingredient')),
    ]

    def _do_drop_item(self, item):
        # Cursed EQUIPPED items cannot be dropped — but cursed items in inventory CAN be
        is_equipped = (item is self.player.weapon or item is self.player.ranged_weapon
                       or item is self.player.shield
                       or item in self.player.armor_slots
                       or item in getattr(self.player, 'accessory_slots', []))
        if is_equipped and (getattr(item, 'cursed', False) or getattr(item, 'buc', '') == 'cursed'):
            self.add_message(f"The {self._display_name(item)} is cursed and bound to you! Uncurse it first.", 'warning')
            return
        if not self.player.remove_from_inventory(item):
            return
        item.x, item.y = self.player.x, self.player.y
        self.ground_items.append(item)
        self.add_message(f"You drop the {self._display_name(item)}.", 'info')

        # Track shard drop for Diogenes' Lantern quirk
        if getattr(item, 'id', '') == 'philosophers_shard':
            self.player.quirk_progress['shard_dropped'] = True
            self.player.quirk_progress['shard_drop_level'] = self.dungeon_level
            self.player.quirk_progress.setdefault('levels_without_shard', 0)
            self.add_message(
                "You abandon the Shard. The dungeon's secrets grow darker without it...", 'warning'
            )

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
                self._log_chronicle("Dropped the Complete Tablet on the Shimmer. The ground split open. Something terrible and ancient stirred beneath. I think I've opened a door that was never meant to be opened.")

        # --- Ariadne quest: drop Bronze Bull at a fountain ---
        if getattr(item, 'id', '') == 'bronze_bull':
            tile = self.dungeon.tiles[self.player.y][self.player.x]
            if tile == FOUNTAIN:
                self._activate_ariadne_shrine(item)

        # --- Athena quest: drop Eye of the Graeae at an altar ---
        if getattr(item, 'id', '') == 'eye_of_graeae':
            tile = self.dungeon.tiles[self.player.y][self.player.x]
            if tile == ALTAR:
                self._activate_athena_shrine(item)

        # --- Odin quest: drop Broken Gram on Odin's Altar ---
        odin_pos = getattr(self.dungeon, 'odin_altar_pos', None)
        if odin_pos and getattr(item, 'id', '') == 'broken_gram':
            px, py = self.player.x, self.player.y
            ax, ay = odin_pos
            tile = self.dungeon.tiles[py][px]
            if tile == ALTAR and (px, py) == (ax, ay):
                self._activate_odin_shrine(item, reforge=False)

        # --- Fenrir quest: drop Gleipnir component at Dwarven Forge ---
        forge_pos = getattr(self.dungeon, 'dwarven_forge_pos', None)
        if forge_pos:
            px, py = self.player.x, self.player.y
            if (px, py) == forge_pos:
                self._check_gleipnir_forge(px, py)

        # --- Vidar secret: drop leather scraps at Vidar's Altar ---
        vidar_pos = getattr(self.dungeon, 'vidar_altar_pos', None)
        if vidar_pos and getattr(item, 'id', '') == 'leather_scrap':
            px, py = self.player.x, self.player.y
            if (px, py) == vidar_pos:
                self._check_vidar_altar(px, py)

        # --- BUC altar mechanic: drop item on altar to uncurse/bless ---
        tile = self.dungeon.tiles[self.player.y][self.player.x]
        if tile == ALTAR and hasattr(item, 'buc') and item.buc != 'blessed':
            self._altar_buc_upgrade(item)
            return  # quiz callback handles _advance_turn

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


    # ------------------------------------------------------------------

    def _item_is_known(self, item) -> bool:
        """Return True if the item type is known (identified instance OR recognised by type)."""
        if not hasattr(item, 'identified'):
            return True  # items without an identified flag are always known
        return item.identified or item.id in self.player.known_item_ids

    _EXAMINE_TABS = [
        ('Weapons',     lambda i: isinstance(i, Weapon)),
        ('Armor',       lambda i: isinstance(i, (Armor, Shield))),
        ('Accessories', lambda i: isinstance(i, Accessory)),
        ('Scrolls',     lambda i: isinstance(i, (Scroll, Spellbook))),
        ('Wands',       lambda i: isinstance(i, Wand)),
        ('Potions',     lambda i: isinstance(i, Potion)),
        ('Food',        lambda i: isinstance(i, (Food, Ingredient))),
        ('Other',       lambda i: isinstance(i, Ammo) or
                         getattr(i, 'item_class', '') not in
                         ('weapon','armor','shield','accessory','scroll','spellbook',
                          'wand','potion','food','ingredient')),
    ]

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
            return f"effect: {item.effect.replace('_', ' ')}  charges: {item.charges}/{item.max_charges}"
        elif isinstance(item, Scroll):
            return f"effect: {item.effect.replace('_', ' ')}  tier {item.quiz_tier}"
        elif isinstance(item, Spellbook):
            return f"teaches: {item.spell_name}  {item.mp_cost} MP"
        elif isinstance(item, Food):
            return f"+{item.sp_restore} SP  +{item.hp_restore} HP"
        elif isinstance(item, Ingredient):
            best = item.recipes.get('5', item.recipes.get('3', {}))
            return f"ingredient -- best: {best.get('name', '?')}"
        elif isinstance(item, Ammo):
            return f"{item.ammo_type}  x{item.count}"
        elif isinstance(item, Lockpick):
            return "lockpick"
        return item.item_class.replace('_', ' ').title()


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
        self._shop_haggled = set()
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
        elif key == pygame.K_h:
            sel = self._shop_selection
            if sel < len(stock):
                haggled = getattr(self, '_shop_haggled', set())
                if sel in haggled:
                    self.add_message("You've already haggled over that item.", 'info')
                else:
                    self._haggle_item(sel)
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
                    # Shift haggled indices after removal
                    haggled = getattr(self, '_shop_haggled', set())
                    self._shop_haggled = {i - 1 if i > sel else i for i in haggled if i != sel}
                    self._shop_selection = min(sel, len(m.stock) - 1)
                    if not m.stock:
                        m.sold_out = True
                        self.add_message("The merchant has sold everything.", 'info')
                        self.state = STATE_PLAYER

    def _haggle_item(self, sel: int):
        """Haggle over a shop item via economics escalator chain quiz."""
        m = self._shop_merchant
        item = m.stock[sel]
        iname = getattr(item, 'name', 'item')
        original_price = m.prices[sel]
        self.add_message(f"You try to haggle over the {iname}...", 'info')
        self.quiz_title = "HAGGLE -- ECONOMICS"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            if chain == 0:
                self.add_message(
                    f"The merchant is unimpressed. Price stays at {original_price} gold.",
                    'warning')
            else:
                discount = min(chain * 10, 50)  # 10% per chain, max 50%
                new_price = max(1, int(original_price * (100 - discount) / 100))
                m.prices[sel] = new_price
                self.add_message(
                    f"The merchant relents! {iname}: {original_price} -> {new_price} gold ({discount}% off).",
                    'success')
            haggled = getattr(self, '_shop_haggled', set())
            haggled.add(sel)
            self._shop_haggled = haggled
            self.state = STATE_SHOP

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='economics',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('economics'),
            base_seconds=self.player.get_quiz_timer('economics'),
        )


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
                pygame.K_a: 'bestiary',
                pygame.K_b: 'weapon',
                pygame.K_c: 'armor',
                pygame.K_d: 'accessory',
                pygame.K_e: 'scroll',
                pygame.K_f: 'wand',
                pygame.K_g: 'spellbook',
                pygame.K_h: 'chronicle',
                pygame.K_i: 'lore_hints',
                pygame.K_j: 'recipes',
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
            # Entry detail view -- any key except arrows goes back to list
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

        if category == 'chronicle':
            self.encyclopedia_entries = [
                {'name': entry, 'lore': ''} for entry in self._chronicle
            ]
            return
        if category == 'lore_hints':
            self.encyclopedia_entries = [
                {'name': hint, 'lore': ''} for hint in self._recalled_hints
            ]
            return
        if category == 'recipes':
            # Show discovered compound recipes with their ingredients
            import json as _rjson
            from paths import data_path as _rdp
            try:
                with open(_rdp('data', 'items', 'recipes.json'), encoding='utf-8') as f:
                    all_recipes = _rjson.load(f)
                entries = []
                for recipe in all_recipes:
                    rname = recipe.get('name', '')
                    if rname in self._cooked_recipes:
                        ings = ', '.join(recipe.get('ingredients', []))
                        entries.append({
                            'name': rname,
                            'lore': f"Ingredients: {ings}",
                        })
                self.encyclopedia_entries = entries
            except Exception:
                self.encyclopedia_entries = []
            return
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
            item_list = list(all_items.values()) if isinstance(all_items, dict) else all_items
            for entry in item_list:
                iid = entry.get('id', '')
                if iid in known_ids:
                    entries.append(entry)
            entries.sort(key=lambda e: e.get('name', e.get('id', '')))
            self.encyclopedia_entries = entries


    # ------------------------------------------------------------------
    # Debug overlay  (F2 — dev-only, not in help screen)
    # ------------------------------------------------------------------


def main():
    from save_system import save_exists, load_game, save_game, delete_save

    pygame.init()
    _di = pygame.display.Info()
    _start_w = min(layout.WINDOW_W, _di.current_w)
    _start_h = min(layout.WINDOW_H, _di.current_h)
    layout.update(_start_w, _start_h)
    screen = pygame.display.set_mode((_start_w, _start_h), pygame.RESIZABLE)
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    global _crash_game_ref

    while True:
        # ---------- welcome / study screen ----------
        welcome = WelcomeScreen(screen, VERSION)
        player_name, secret_build = welcome.run(clock)

        if player_name == '__STUDY_MODE__':
            study = StudyMode(screen)
            study.run(clock)
            continue  # return to welcome screen after study mode

        # Sync layout to actual window size (may have been resized during welcome)
        _cur_w, _cur_h = screen.get_size()
        layout.update(_cur_w, _cur_h)

        # ---------- load or create game ----------
        state = load_game(player_name) if save_exists(player_name) else None
        if state:
            delete_save(player_name)   # permadeath: delete save immediately on load
            game = Game(screen,
                        player_name=state.get('player_name', player_name),
                        secret_build=state.get('secret_build'))
            game.load_state(state)
        else:
            game = Game(screen, player_name=player_name, secret_build=secret_build)

        _crash_game_ref = game

        # ---------- game loop ----------
        running = True
        while running:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                try:
                    if not game.handle_event(event):
                        running = False
                except Exception as _evt_err:
                    game.add_message(f"Error: {_evt_err}", 'danger')
                    game.state = STATE_PLAYER  # recover to playable state
                    import traceback
                    traceback.print_exc()
            try:
                game.update(dt)
            except Exception as _upd_err:
                game.add_message(f"Error: {_upd_err}", 'danger')
                game.state = STATE_PLAYER
                import traceback
                traceback.print_exc()
            game.render()

        # Save on clean exit if the game is still in progress and player chose to save
        if game.state not in (STATE_DEAD, STATE_VICTORY) and game._save_on_quit:
            save_game(game)

        # If game ended by death or victory, loop back to welcome screen
        if game.state in (STATE_DEAD, STATE_VICTORY):
            continue

        # Otherwise player quit mid-game — exit for real
        break

    pygame.quit()
    sys.exit()


_crash_game_ref = None   # set by main() once Game is constructed

if __name__ == "__main__":
    import crash_handler as _crash
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        path = _crash.write_crash_report(*sys.exc_info(), game=_crash_game_ref)
        print(f"\nCRASH -- report written to:\n  {path}", file=sys.stderr)
        raise
