import os
import random
import sys

import pygame

# FANTASY: get_font is the only fantasy_ui name still consumed by main.py;
# every other UI helper is used exclusively from game_render.RenderMixin.
from fantasy_ui import get_font

from pet_system import Pet, FenrirPet
from quirk_system import QuirkSystem
from container_system import attempt_lockpick
from dungeon import (spawn_monsters, WALL, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR,
                     ALTAR, WATER, LAVA, FOUNTAIN, GRAVE, THRONE, ICE)
from food_system import harvest_corpse, cook_ingredient, cook_compound_recipe
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient, Artifact, Container, Lockpick, Accessory, Wand, Scroll, Spellbook, Ammo, Food, Potion
from level_manager import LevelManager
from player import Player
import sound_system as _snd
from quiz_engine import QuizEngine
from renderer import Renderer
from geom import monster_at_tile, is_at_tile
from ui import Sidebar, MessageLog
from game_helpers import (
    migrate_buc_item, cycle_tab,
    fix_name_case, a_or_an,
)
from game_states import (
    STATE_PLAYER, STATE_QUIZ,
    STATE_EXIT_QUEST, STATE_ABANDON_QUEST,
    STATE_VICTORY, STATE_DEAD,
    STATE_LORE,
    STATE_ENCYCLOPEDIA,
    STATE_STORY_POPUP, STATE_SHOP,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT,
    STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_STUDY,
)
from welcome_screen import WelcomeScreen
from study_mode import StudyMode
import layout
from layout import VERSION, FPS
from game_render import RenderMixin
from game_menus import MenuMixin
from game_input import InputMixin
from game_encounters import EncountersMixin
from game_magic import MagicMixin
from game_combat import CombatMixin
from game_divine import DivineMixin
from spells import LEARNABLE_SPELLS


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------




class Game(InputMixin, MenuMixin, RenderMixin, MagicMixin, CombatMixin, DivineMixin, EncountersMixin):
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
        self._secret_victory    = False   # True after _trigger_abyss; drives the Abyss-distinct victory screen
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
        # Per-subject quiz tracking for the Discoveries panel. Keyed by subject
        # name; each value is a dict with 'correct', 'wrong', and 't{1-5}{c,w}'
        # tier-specific counters (e.g. 't3c' = correct at tier 3).
        self.quiz_stats: dict = {}
        self._score_saved       = False    # True after high score is written
        self.quiz_engine.on_answer = self._on_quiz_answer
        self.quiz_engine.on_complete = self._on_quiz_complete
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
        self._pet_special_targeting = False     # True when aiming a pet's special
        self._pending_pet_special = None        # Special-attack dict being aimed
        self._pending_pet_special_pet = None    # Pet that will execute the special
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

        # Duck of Doom: one Duck per run, on a uniform-random floor in
        # {1..10}. Tracked so spawn placement (level_manager) can drop
        # it on first entry to that floor.
        self._duck_of_doom_floor: int = random.randint(1, 10)
        self._duck_of_doom_placed: bool = False

        self._new_level(1)
        # Per-run trackers for chain-equip passives. Per-floor charges are
        # initialised here so first-floor access doesn't AttributeError.
        from chain_passives import reset_per_floor_charges
        reset_per_floor_charges(self.player)
        self.player._chain_passive_once_per_run = set()
        self.player._gorgoneion_used_this_floor = False
        self.player._chain_move_counter = 0
        self.player._chain_no_move_counter = 0
        self.player._reassembly_regen_remaining = 0
        self.player._dragon_blood_active = False
        self.player._death_omen_target = None
        self.player._anti_being_charged = False
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
    # Philosopher career arc — milestone rewards for cumulative identifies
    # ------------------------------------------------------------------

    def _check_philosopher_thresholds(self):
        """Fire one-time rewards as total_identifies crosses 25/75/125/200/300.

        Called from _on_full_identify after each successful full identification
        (chain >= 3 on uniques; threshold success on commons; corpse lore-id).
        Quick-BUC peeks do NOT count.
        """
        p = self.player
        claimed = p.philosopher_tier_claimed
        n = p.total_identifies
        if n >= 25 and 25 not in claimed:
            claimed.add(25)
            p.INT += 1
            p.max_mp = p.BASE_MP + p.INT
            p.mp = min(p.mp + 1, p.max_mp)
            self.add_message("First Insight! Your study sharpens your mind. (+1 INT)", 'success')
            self._log_chronicle("Reached the First Insight milestone (25 identifies). INT permanently increased.")
        if n >= 75 and 75 not in claimed:
            claimed.add(75)
            self.add_message(
                "Pattern Recognition! You now grasp lesser items at a glance.", 'success'
            )
            self._log_chronicle("Reached Pattern Recognition (75 identifies). Common items auto-identify at depth.")
        if n >= 125 and 125 not in claimed:
            claimed.add(125)
            p.PER += 1
            self.add_message(
                "Sharper Eye! The world's small details no longer escape you. (+1 PER)", 'success'
            )
            self._log_chronicle("Reached Sharper Eye (125 identifies). PER permanently increased.")
        if n >= 200 and 200 not in claimed:
            claimed.add(200)
            p.WIS += 1
            self.add_message(
                "Sage's Eye! Your patient study deepens your wisdom. (+1 WIS)", 'success'
            )
            self._log_chronicle("Reached Sage's Eye (200 identifies). WIS permanently increased.")
        if n >= 300 and 300 not in claimed:
            claimed.add(300)
            p.philosophers_mantle = True
            self.add_message(
                "The Philosopher's Mantle settles upon you. Every aura is plain to your eye.", 'success'
            )
            self._log_chronicle("Donned the Philosopher's Mantle (300 identifies). All future pickups reveal their aura.")

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
        # QA tools flag (Titivillus debug build): unlocks Shift+I immortal toggle
        # and Shift+W floor warp from the player turn.
        self.player.qa_tools = bool(b.get('_qa_tools', False))
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
        self._maybe_place_duck_of_doom(level)
        # Place deep-lore items targeted to this floor (e.g. abyssal_shimmer
        # when _lore_levels['shimmer'] == 1). Without this, lore items on L1
        # only spawn if the player descends and returns — and a save/reload
        # at that point could double-spawn (the lore-placed guard relies on
        # the set surviving the round trip).
        self._maybe_place_lore_items(dungeon, level)

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
        if not hasattr(self.player, 'cooking_stat_gained'):
            # Phase 5+ stat-cooking softcap — old saves get a zeroed tracker.
            self.player.cooking_stat_gained = {
                'STR': 0, 'CON': 0, 'DEX': 0, 'INT': 0, 'WIS': 0, 'PER': 0,
            }
        if not hasattr(self.player, 'deepest_floor_reached'):
            # Old save: best estimate is the level_mgr's max_level_reached, falling
            # back to current dungeon_level so existing cooking remains within softcap.
            _max_lvl = getattr(state.get('level_mgr'), 'max_level_reached', None)
            self.player.deepest_floor_reached = _max_lvl or state.get('dungeon_level', 1)
        if not hasattr(self.player, 'chronicle_seen_materials'):
            self.player.chronicle_seen_materials = set()
        if not hasattr(self.player, 'known_spells'):
            self.player.known_spells = {}
        if not hasattr(self.player, 'lockpick_charges'):
            self.player.lockpick_charges = 0
        # Philosopher career arc — new fields in 2026-05-17 identify rebuild
        if not hasattr(self.player, 'total_identifies'):
            self.player.total_identifies = 0
        if not hasattr(self.player, 'philosopher_tier_claimed'):
            self.player.philosopher_tier_claimed = set()
        if not hasattr(self.player, 'philosophers_mantle'):
            self.player.philosophers_mantle = False
        if not hasattr(self.player, 'unlocked_masteries'):
            self.player.unlocked_masteries = {}
        # Class-level mastery (commons): added 2026-05-18 with the unified
        # escalator-chain identify path. Older saves get empty defaults.
        if not hasattr(self.player, 'unlocked_class_masteries'):
            self.player.unlocked_class_masteries = {}
        if not hasattr(self.player, 'known_class_ids'):
            self.player.known_class_ids = set()
        # Per-family monster mastery (corpse-identify chain 5): added with
        # the corpse-identify rebuild. Older saves default to empty.
        if not hasattr(self.player, 'unlocked_monster_class_masteries'):
            self.player.unlocked_monster_class_masteries = {}
        # Chain-equip tier_bonuses targets: flat damage reduction + HP regen.
        # Added 2026-05-18 with the legendary-uniques chain-equip mechanic.
        if not hasattr(self.player, 'damage_resistances'):
            self.player.damage_resistances = {}
        if not hasattr(self.player, 'regen_bonus'):
            self.player.regen_bonus = 0
        # LevelManager pre-rolls mini-bosses at __init__; old saves predate that.
        # NOTE: check state['level_mgr'] (the one being restored) — not self.level_mgr,
        # which is still the constructor's fresh manager and always has the field.
        _saved_lm = state.get('level_mgr')
        if _saved_lm is not None and not hasattr(_saved_lm, '_planned_mini_bosses'):
            _saved_lm._planned_mini_bosses = _saved_lm._roll_planned_mini_bosses()
        # Phase 3 hero specials — new fields in 2026-05-17 build rebuild
        if not hasattr(self.player, 'hero_passives'):
            self.player.hero_passives = set()
        if not hasattr(self.player, 'hero_specials'):
            self.player.hero_specials = []
        if not hasattr(self.player, 'hero_special_cooldowns'):
            self.player.hero_special_cooldowns = {}
        if not hasattr(self.player, 'qa_tools'):
            self.player.qa_tools = False
        if not hasattr(self.player, '_stand_ac_bonus'):
            self.player._stand_ac_bonus = 0
        if not hasattr(self.player, '_stand_counter_pct'):
            self.player._stand_counter_pct = 0
        if not hasattr(self.player, '_elder_blood_escape_used'):
            self.player._elder_blood_escape_used = False
        # Chain-equip passive tracking (per-floor charges + per-run flags).
        if not hasattr(self.player, '_chain_passive_charges'):
            self.player._chain_passive_charges = {}
        if not hasattr(self.player, '_chain_passive_once_per_run'):
            self.player._chain_passive_once_per_run = set()
        for _attr, _default in (
            ('_gorgoneion_used_this_floor', False),
            ('_chain_move_counter', 0),
            ('_chain_no_move_counter', 0),
            ('_reassembly_regen_remaining', 0),
            ('_dragon_blood_active', False),
            ('_death_omen_target', None),
            ('_anti_being_charged', False),
        ):
            if not hasattr(self.player, _attr):
                setattr(self.player, _attr, _default)
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
        self.quiz_stats      = state.get('quiz_stats', {})
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
        self._secret_victory = state.get('_secret_victory', False)
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
        # Cow return floor — restore so exit portal works post-reload
        self._cow_return_level = state.get('_cow_return_level', 0)
        # Per-floor one-shot charges (Babr-e Bayan, Jade Cicada, Tarnhelm,
        # Tablet of Destinies reroll). Without these the per-floor charge
        # would refresh on every reload — a save-exploit.
        self._first_hit_used   = state.get('_first_hit_used', False)
        self._death_save_used  = state.get('_death_save_used', False)
        self._tarnhelm_used    = state.get('_tarnhelm_used', False)
        self._quiz_reroll_used = state.get('_quiz_reroll_used', False)
        # Chronicle dedup guards
        self._chronicle_abaddon_start = state.get('_chronicle_abaddon_start', False)
        # Magic carrot + ethereal unicorn one-shot spawn state (added 2026-05-19
        # save-lifecycle audit). Without these, reload re-rolls the spawn
        # target floor; if the new target is on a floor the player hasn't
        # visited yet, a SECOND carrot/unicorn can spawn in the same run.
        if state.get('_magic_carrot_spawned') is not None:
            self._magic_carrot_spawned = state['_magic_carrot_spawned']
        if state.get('_magic_carrot_target_level') is not None:
            self._magic_carrot_target_level = state['_magic_carrot_target_level']
        if state.get('_unicorn_spawned') is not None:
            self._unicorn_spawned = state['_unicorn_spawned']
        if state.get('_unicorn_target_level') is not None:
            self._unicorn_target_level = state['_unicorn_target_level']
        # Chronicle & Lore Hints
        self._chronicle = state.get('_chronicle', [])
        self._recalled_hints = state.get('_recalled_hints', [])
        self._cooked_recipes = state.get('_cooked_recipes', [])
        # Quiz deck state — restore shuffle positions so questions don't repeat on reload
        quiz_deck_state = state.get('quiz_deck_state')
        if quiz_deck_state:
            self.quiz_engine.restore_deck_state(quiz_deck_state)
        # Save compat: weapons created before 2026-05-20 had requires_ammo=None
        # on bow/crossbow/sling templates, so they equipped to the melee slot.
        # Heal in-flight saves: patch the field on every Weapon in player gear,
        # inventory, and ground; relocate any equipped ranged weapon from
        # weapon -> ranged_weapon.
        self._migrate_ranged_weapons()
        # Save compat: common weapons/armor/shields created before 2026-05-20
        # had empty `lore` fields. Recompose from template + material so the
        # examine panel shows lore.
        self._migrate_common_item_lore()
        self.renderer.set_dungeon(self.dungeon.width, self.dungeon.height, layout.GAME_W, layout.GAME_H)
        self._refresh_fov()
        self.add_message("Welcome back, seeker. Your journey continues...", 'success')

    def _migrate_ranged_weapons(self):
        """One-shot save migration. Old saves have bows with requires_ammo=None
        because the templates lacked the field at instantiation time. Walk all
        Weapons we can reach and re-derive requires_ammo from weapon_class."""
        from items import Weapon
        AMMO_FOR_CLASS = {'bow': 'arrow', 'crossbow': 'bolt', 'sling': 'stone'}

        def _patch(w):
            if not isinstance(w, Weapon):
                return
            if getattr(w, 'requires_ammo', None):
                return  # already correct
            wcls = getattr(w, 'weapon_class', '') or ''
            ammo = AMMO_FOR_CLASS.get(wcls)
            if ammo:
                w.requires_ammo = ammo
                if wcls == 'sling':
                    w.infinite_ammo = True

        # Walk every weapon-bearing slot
        for slot in (self.player.weapon, self.player.ranged_weapon):
            _patch(slot)
        for it in self.player.inventory:
            _patch(it)
        for it in self.ground_items:
            _patch(it)

    def _migrate_common_item_lore(self):
        """One-shot save migration. Common Weapons/Armor/Shields created
        before the 2026-05-20 lore generation pass have empty .lore fields.
        Recompose lore from the item's stored template + material."""
        from items import (Weapon, Armor, Shield, get_template, get_material,
                            _compose_common_lore, item_noun_for_weapon)
        def _patch(it):
            if not isinstance(it, (Weapon, Armor, Shield)):
                return
            if getattr(it, 'lore', '') or getattr(it, 'is_unique', False):
                return  # already has lore, or it's a unique (don't overwrite)
            material_id = getattr(it, 'material', '')
            iid = getattr(it, 'id', '')
            # Item id format: '{material}_{template}'
            if not material_id or '_' not in iid:
                return
            template_id = iid.split('_', 1)[1] if iid.startswith(material_id) else ''
            if not template_id:
                return
            # Try the right template directory based on item class
            tpl_dir = {Weapon: 'weapons', Armor: 'armor', Shield: 'shields'}.get(type(it))
            if not tpl_dir:
                return
            try:
                tpl = get_template(tpl_dir, template_id)
                # Material can come from weapons or armor pool
                mat = get_material(tpl_dir, material_id) or get_material('armor', material_id) or get_material('weapons', material_id)
                if not tpl or not mat:
                    return
                if isinstance(it, Weapon):
                    noun = item_noun_for_weapon(tpl)
                elif isinstance(it, Armor):
                    noun = 'plate' if 'plate' in template_id else 'piece'
                else:
                    noun = 'face'
                it.lore = _compose_common_lore(tpl, mat, getattr(it, 'name', iid), noun)
            except Exception:
                pass

        for slot in (self.player.weapon, self.player.ranged_weapon, self.player.shield):
            _patch(slot)
        for s in self.player.armor_slots or []:
            _patch(s)
        for it in self.player.inventory:
            _patch(it)
        for it in self.ground_items:
            _patch(it)

        # If a ranged weapon ended up in the melee slot, relocate it
        w = self.player.weapon
        if isinstance(w, Weapon) and getattr(w, 'requires_ammo', None):
            if self.player.ranged_weapon is None:
                self.player.ranged_weapon = w
                self.player.weapon = None
                self.add_message(
                    f"Your {w.name} was a ranged weapon all along -- moved to bow slot.",
                    'info'
                )
            else:
                self.player.inventory.append(w)
                self.player.weapon = None
                self.add_message(
                    f"Your {w.name} is a ranged weapon -- returned to inventory (bow slot occupied).",
                    'info'
                )

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
        # class_scroll_persist (scroll_of_mapping mastery): auto-map every
        # newly-entered floor. The mapped state already persists per-floor via
        # level_manager save/load; this extends that to floors the player has
        # never set foot on, so the mastered scroll's effect persists in the
        # design sense (you carry the reveal forward).
        _map_mastery = self.player.unlocked_class_masteries.get('scroll_of_mapping')
        if _map_mastery and _map_mastery.get('kind') == 'class_scroll_persist':
            for _y in range(self.dungeon.height):
                for _x in range(self.dungeon.width):
                    self.dungeon.explored.add((_x, _y))
        # Track deepest floor reached for the cooking softcap (rises with descent)
        self.player.deepest_floor_reached = max(
            self.player.deepest_floor_reached, new_level
        )
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
            self._maybe_place_duck_of_doom(new_level)
        else:
            # Revisit: spawn triggered NPCs if player now has the trigger item
            # (handles the case where player missed the item on first pass)
            self._maybe_spawn_npc(new_level)

        # Reset per-floor artifact states
        self._first_hit_used = False    # Babr-e Bayan
        self._death_save_used = False   # Jade Cicada
        self.player._elder_blood_escape_used = False   # Ciri auto-teleport
        self._quiz_reroll_used = False  # Tablet of Destinies
        self._tarnhelm_used = False     # Tarnhelm
        # Chain-equip per-floor passive charges (free_cast, free_escape,
        # huginn_muninn, demon_command, etc.) reset on every floor change.
        from chain_passives import reset_per_floor_charges
        reset_per_floor_charges(self.player)
        # Per-floor mechanic markers used by named passives (greater Aegis
        # gorgoneion, identify-free, etc.). Cheap to reset every time.
        self.player._gorgoneion_used_this_floor = False
        # Counter for free_move_every_10 (anklet_of_atalanta).
        if not hasattr(self.player, '_chain_move_counter'):
            self.player._chain_move_counter = 0
        # Reassembly buffer used by tyet_of_isis T5.
        self.player._reassembly_regen_remaining = 0
        # Three apples (anklet_of_atalanta) per-floor charge — see consume_passive_charge.
        # Dragon-blood bath (dragon_mail_of_sigurd) is once per floor toggle.
        self.player._dragon_blood_active = False
        # Mark of doom (death_omen_mark): updated lazily by EncountersMixin/turn tick.
        if not hasattr(self.player, '_death_omen_target'):
            self.player._death_omen_target = None
        # Anti-being charged spell (heart_of_ahriman): True if next destructive
        # spell deals 2x damage; consumed on spell cast.
        if not hasattr(self.player, '_anti_being_charged'):
            self.player._anti_being_charged = False
        # No-move tracker for unseen_when_still (Helm of Hades T5).
        self.player._chain_no_move_counter = 0
        # Pacify-on-sight tracking (Ring of Solomon).
        self._chain_pacify_seen = set()
        # Fear-aura "saved already" tracking (Aegis of Athena, etc.).
        self.player._chain_seen_fear = set()

        # Chain-equip passive: wisdom_at_a_price (Cloak of Odin T4+). On floor
        # entry, exchange 1 max HP for +1 WIS, 1/floor. Auto-fires only when
        # the player has at least 20 max HP to spare (to avoid lethal early-game).
        try:
            from chain_passives import (
                player_has_passive, consume_passive_charge,
            )
            if (player_has_passive(self.player, 'wisdom_at_a_price')
                    and self.player.max_hp >= 20
                    and consume_passive_charge(self.player, 'wisdom_at_a_price')):
                self.player.max_hp -= 1
                self.player.hp = min(self.player.hp, self.player.max_hp)
                self.player.WIS += 1
                self.add_message(
                    "Odin's sacrifice: 1 HP for 1 WIS. Knowledge is bought.",
                    'success')
        except ImportError:
            pass

        # Chain-equip passive: huginn_muninn (Cloak of Odin T3+). Auto-fire on
        # floor entry: reveal all monsters within 10 tiles for 5 turns. The
        # `_huginn_muninn_remaining` counter ticks down each turn.
        try:
            from chain_passives import (
                player_has_passive, consume_passive_charge,
            )
            if player_has_passive(self.player, 'huginn_muninn'):
                if consume_passive_charge(self.player, 'huginn_muninn'):
                    self.player._huginn_muninn_remaining = 5
                    self.add_message(
                        "Huginn and Muninn take flight from your shoulders to scout!",
                        'success')
                else:
                    self.player._huginn_muninn_remaining = 0
            else:
                self.player._huginn_muninn_remaining = 0
        except ImportError:
            self.player._huginn_muninn_remaining = 0

        # Chain-equip passive: raven_scout / raven_scout_extended (Morrigan).
        # Reveal entire dungeon layout (corridors) on floor entry; extended
        # version also reveals monsters in dark rooms.
        try:
            if player_has_passive(self.player, 'raven_scout') or \
                    player_has_passive(self.player, 'raven_scout_extended'):
                # Mark a chunk of tiles around the player as explored.
                for _dy in range(-12, 13):
                    for _dx in range(-12, 13):
                        if _dx * _dx + _dy * _dy > 144:
                            continue
                        _tx = self.player.x + _dx
                        _ty = self.player.y + _dy
                        if 0 <= _tx < self.dungeon.width and 0 <= _ty < self.dungeon.height:
                            self.dungeon.explored.add((_tx, _ty))
                self.add_message(
                    "The Morrigan's ravens trace the dungeon's bones for you.",
                    'success')
        except (ImportError, NameError):
            pass

        # Chain-equip passive: atalantas_choice (Anklet T5). On floor entry
        # below 30% HP, freeze all visible monsters for 10 turns. 1/floor.
        try:
            from chain_passives import (
                player_has_passive, consume_passive_charge,
            )
            if (player_has_passive(self.player, 'atalantas_choice')
                    and self.player.hp <= self.player.max_hp * 0.30
                    and consume_passive_charge(self.player, 'atalantas_choice')):
                for m in self.monsters:
                    if m.alive and (m.x, m.y) in self.visible:
                        m.add_effect('paralyzed', 10)
                self.add_message(
                    "Atalanta's choice! Time itself pauses for you to breathe.",
                    'success')
        except ImportError:
            pass

        # Chain-equip passive: anti_being (Heart of Ahriman T5).
        # On floor entry, queue the next destructive spell for 2x damage.
        try:
            from chain_passives import (
                player_has_passive, consume_passive_charge,
            )
            if player_has_passive(self.player, 'anti_being') and \
                    consume_passive_charge(self.player, 'anti_being'):
                self.player._anti_being_charged = True
                self.add_message(
                    "Heart of Ahriman trembles -- your next destructive spell will rend the unmaking.",
                    'success')
        except ImportError:
            pass

        # Chain-equip passive: life_save_resets_per_floor (Tyet of Isis T2+).
        # Refresh the life_save status effect each floor entry.
        try:
            if player_has_passive(self.player, 'life_save_resets_per_floor'):
                self.player.add_effect('life_save', -1)
        except (ImportError, NameError):
            pass

        # Chain-equip passive: paths_of_the_dead (Helm of Aragorn T5).
        # On floor entry below 50% HP, summon a spectral ally for 30 turns. Once per run.
        try:
            from chain_passives import (
                player_has_passive, consume_run_passive,
            )
            if (player_has_passive(self.player, 'paths_of_the_dead')
                    and self.player.hp <= self.player.max_hp * 0.5
                    and consume_run_passive(self.player, 'paths_of_the_dead')):
                # Use SketchedPet machinery: borrow a strong monster template.
                from monster_classes import get_monster_family
                # Find ANY strong allied template within visible monsters; if
                # none, just charm a random visible foe as a stand-in.
                _candidates = [m for m in self.monsters
                               if m.alive and (m.x, m.y) in self.visible]
                if _candidates:
                    _ally = max(_candidates, key=lambda m: m.max_hp)
                    _ally.add_effect('charmed', 30)
                    self.add_message(
                        f"The Paths of the Dead open -- the {_ally.name} bends to your service for 30 turns!",
                        'success')
        except (ImportError, NameError):
            pass

        # Chain-equip passive: death_omen_mark (Cloak of the Morrigan T5).
        # Mark the highest-level monster on this floor for +25% damage.
        try:
            if player_has_passive(self.player, 'death_omen_mark') and self.monsters:
                _best = max(
                    (m for m in self.monsters if m.alive),
                    key=lambda m: getattr(m, 'min_level', 0),
                    default=None,
                )
                self.player._death_omen_target = id(_best) if _best else None
                if _best:
                    self.add_message(
                        f"The Morrigan marks the {_best.name} for death.",
                        'warning')
        except (ImportError, NameError):
            pass

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

        # Grant HP/SP/MP rest-heal on FIRST visit only. Revisits (e.g.
        # stair-stomping between two floors to grind SP) get nothing —
        # the `saved` variable above is truthy iff this floor was
        # already visited in this run (level_mgr returned cached state).
        self.player.on_level_change(
            ascending=not enter_from_top,
            first_visit=not saved,
        )

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
                           not monster_at_tile(self.monsters, nx, ny) is not None:
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
        # Mark a build-kit starting item as appropriately-known: uniques
        # get id_level=3 (name + BUC + stats; lore + mastery still
        # earnable via the philosophy chain). Commons jump straight to
        # id_level=5 because their content is just "basic gear" — the
        # identify menu's common-filter (`id_level >= 5`) then hides
        # them so the kid isn't spamming threshold-mode IDs on a
        # starting dagger. Per user feedback 2026-05-29: build-kit items
        # were spawning at 4/5 or 5/5 due to the legacy property-set
        # path raising id_level to 4 via the setter.
        def _mark_starting_item_known(it):
            """Build-kit items behave as if the player had picked them up
            and successfully completed a Tier-4 identify chain on them.
            id_level=4 = name + BUC + stats + lore all revealed; Tier 5
            (mastery for uniques, full ID for commons) remains earnable
            via the normal identify flow. NO special-casing for uniques
            vs commons — they're treated identically to any naturally-
            found item that's been ID'd to Tier 4. Per user direction
            2026-05-29 (correcting an earlier draft that split the rule)."""
            it.id_level = max(int(getattr(it, 'id_level', 0)), 4)
            it.buc_known = True
            _iid = getattr(it, 'id', None)
            if _iid:
                self.player.known_item_ids.add(_iid)
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
        _mark_starting_item_known(shard)
        self.player.inventory.append(shard)
        self.player.known_item_ids.add('philosophers_shard')

        # -- Weapon: default dagger OR build override ----------------------
        # _start_weapon is either a unique's str id ("excalibur") or a
        # (template_id, material_id) tuple for template-instantiated commons.
        no_dagger     = b.get('_no_dagger', False)
        start_weapon  = b.get('_start_weapon', None)
        try:
            from items import instantiate_weapon
            weapons = load_items('weapon')
            if start_weapon:
                if isinstance(start_weapon, tuple):
                    w = instantiate_weapon(start_weapon[0], start_weapon[1])
                else:
                    w = next((x for x in weapons if x.id == start_weapon), None)
                if w:
                    _mark_starting_item_known(w)
                    self.player.known_item_ids.add(w.id)
                    self.player.inventory.append(w)
            elif not no_dagger:
                sword = instantiate_weapon('shortsword', 'iron')
                if sword:
                    _mark_starting_item_known(sword)
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
                from items import instantiate_weapon
                if isinstance(start_melee, tuple):
                    melee_w = instantiate_weapon(start_melee[0], start_melee[1])
                else:
                    melee_w = next((x for x in weapons if x.id == start_melee), None)
                if melee_w:
                    _mark_starting_item_known(melee_w)
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
                    _mark_starting_item_known(wand)
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
                    _mark_starting_item_known(book)
                    self.player.known_item_ids.add(book.id)
                    self.player.inventory.append(book)
            except Exception:
                pass

        # -- Shield (warriors) ---------------------------------------------
        # str id = unique shield, tuple = (template_id, material_id)
        start_shield = b.get('_start_shield', None)
        if start_shield:
            try:
                from items import instantiate_shield
                if isinstance(start_shield, tuple):
                    sh = instantiate_shield(start_shield[0], start_shield[1])
                else:
                    shields = load_items('shield')
                    sh = next((s for s in shields if s.id == start_shield), None)
                if sh:
                    _mark_starting_item_known(sh)
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
                    _mark_starting_item_known(acc)
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
                        _mark_starting_item_known(ea)
                        self.player.known_item_ids.add(ea.id)
                        self.player.inventory.append(ea)
            except Exception:
                pass

        # -- Armor (headgear, etc.) -----------------------------------------
        # str id = unique armor, tuple = (template_id, material_id)
        start_armor = b.get('_start_armor', None)
        if start_armor:
            try:
                from items import instantiate_armor
                if isinstance(start_armor, tuple):
                    arm = instantiate_armor(start_armor[0], start_armor[1])
                else:
                    armors = load_items('armor')
                    arm = next((a for a in armors if a.id == start_armor), None)
                if arm:
                    _mark_starting_item_known(arm)
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
                _mark_starting_item_known(sphere)
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
            _mark_starting_item_known(usphere)
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
                        _mark_starting_item_known(p)
                        self.player.known_item_ids.add(p.id)
                        self.player.add_to_inventory(p)
            except Exception:
                pass

        # -- Always: Master Lockpick (permanent, no charges) -------------
        # The lockpick is a fixed inventory item that never gets used up.
        # Eco-quiz success is the gating mechanic, not consumable charges.
        try:
            picks = load_items('lockpick')
            if picks:
                master = copy.copy(picks[0])  # canonical lockpick
                _mark_starting_item_known(master)
                self.player.add_to_inventory(master)
        except Exception:
            pass

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
                _mark_starting_item_known(heal_pot)
                heal_pot.buc_known = True
                self.player.known_item_ids.add(heal_pot.id)
                self.player.inventory.append(heal_pot)
        except Exception:
            pass
        self.player.inventory.sort(key=lambda i: i.name.lower())

        # -- Hero specials, passives, and journal entry --------------------
        # Pull from src/hero_specials.py based on the secret build's name.
        try:
            from hero_specials import (
                get_specials_for_build, get_passives_for_build,
                get_journal_for_build,
            )
            bname = (self.secret_build or {}).get('_name', '') if self.secret_build else ''
            # The build dict is keyed by lowercased name in SECRET_BUILDS, but
            # _give_starting_kit doesn't have direct access to the key. The
            # player's typed name is the source of truth.
            key = (self.player_name or '').lower().strip()
            actives = get_specials_for_build(key)
            passives = get_passives_for_build(key)
            journal = get_journal_for_build(key)
            self.player.hero_specials = list(actives)
            self.player.hero_passives = set(passives)
            self.player.hero_special_cooldowns = {}
            if journal:
                self._log_chronicle(journal)
        except Exception:
            pass

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )
        # Chain-equip passive: four_faces_360_fov (Crown of Brahma T4).
        # Add all tiles within radius PER*1.5 (ignoring wall occlusion) to FOV.
        try:
            from chain_passives import player_has_passive
            if player_has_passive(self.player, 'four_faces_360_fov'):
                px, py = self.player.x, self.player.y
                r = max(3, int(self.player.PER * 1.5))
                for _dy in range(-r, r + 1):
                    for _dx in range(-r, r + 1):
                        if _dx * _dx + _dy * _dy > r * r:
                            continue
                        _tx, _ty = px + _dx, py + _dy
                        if 0 <= _tx < self.dungeon.width and 0 <= _ty < self.dungeon.height:
                            self.visible.add((_tx, _ty))
                            self.dungeon.explored.add((_tx, _ty))
        except ImportError:
            pass
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

        # Chain-equip passive: beautiful_ruin (Necklace of Harmonia T5).
        # On every turn, the strongest visible monster is marked aware + seeks player.
        try:
            from chain_passives import player_has_passive
            if player_has_passive(self.player, 'beautiful_ruin') and self.monsters:
                _visible_alive = [m for m in self.monsters
                                  if m.alive and (m.x, m.y) in self.visible]
                if _visible_alive:
                    _strongest = max(_visible_alive, key=lambda m: m.max_hp)
                    _strongest._aware = True
        except ImportError:
            pass

        # Chain-equip passive: three_oclock (Ring of Gawain T5 counterpart).
        # STR decays per turn, resets on rest (handled in _tick_sp).
        try:
            from chain_passives import player_has_passive
            if player_has_passive(self.player, 'three_oclock'):
                _ctr = getattr(self.player, '_three_oclock_decay', 0) + 1
                self.player._three_oclock_decay = _ctr
                if _ctr % 30 == 0 and self.player.STR > 8:
                    self.player.STR -= 1
                    self.add_message(
                        "The 3 o'clock hour wanes. Your strength fades.",
                        'warning')
        except ImportError:
            pass

        # Chain-equip passive: fear auras (aura_of_awe, fafnirs_glare, no_man_dares).
        try:
            from chain_passives import apply_fear_auras
            _n_feared = apply_fear_auras(self.player, self.monsters, self.visible)
            if _n_feared:
                self.add_message(
                    f"The aura of dread breaks {_n_feared} foe(s)!", 'success')
        except ImportError:
            pass

        # Chain-equip passives: demon/undead command (auto-fire on first sight).
        # demon_command_one_per_floor (Robes of Solomon T2+) -> charm 1 demon 20t.
        # seventy_two_seals (Robes of Solomon T5) -> charm 1 demon 50t + loot drops.
        # command_undead (Helm of Aragorn) -> charm 1 undead in sight.
        try:
            from chain_passives import (
                player_has_passive, consume_passive_charge,
            )
            for _tag, _flag, _dur, _msg in (
                ('demon', 'seventy_two_seals', 50,
                 "By the Seventy-Two Seals, the {name} is bound to your will!"),
                ('demon', 'demon_command_one_per_floor', 20,
                 "Solomon's seal compels the {name} to your service!"),
                ('undead', 'command_undead', 15,
                 "Aragorn's helm overawes the {name}!"),
            ):
                if not player_has_passive(self.player, _flag):
                    continue
                # Find an unclaimed target in FOV with the tag.
                _target = None
                for m in self.monsters:
                    if not m.alive:
                        continue
                    if (m.x, m.y) not in self.visible:
                        continue
                    if _tag not in set(getattr(m, 'tags', []) or []):
                        continue
                    if m.has_effect('charmed'):
                        continue
                    _target = m
                    break
                if _target is None:
                    continue
                if not consume_passive_charge(self.player, _flag):
                    continue
                _target.add_effect('charmed', _dur)
                self.add_message(_msg.format(name=_target.name), 'success')
                # 72 Seals additionally marks the demon for guaranteed loot drop.
                if _flag == 'seventy_two_seals':
                    _target._seal_marked = True
        except ImportError:
            pass

        # Chain-equip passive: pacify_demon_chance (Ring of Solomon).
        # Roll on each demon-tagged monster newly seen this floor; on success
        # they get a 'charmed' or 'sleeping' status as a stand-in for pacify.
        try:
            from chain_passives import get_pacify_demon_chance
            _pac_chance = get_pacify_demon_chance(self.player)
            if _pac_chance > 0:
                import random as _rng
                seen = getattr(self, '_chain_pacify_seen', set())
                for m in self.monsters:
                    if not m.alive:
                        continue
                    if id(m) in seen:
                        continue
                    if (m.x, m.y) not in self.visible:
                        continue
                    if 'demon' not in set(getattr(m, 'tags', []) or []):
                        continue
                    seen.add(id(m))
                    if _rng.random() < _pac_chance:
                        m.status_effects['sleeping'] = max(
                            m.status_effects.get('sleeping', 0), 15)
                        self.add_message(
                            f"The Ring of Solomon pacifies the {m.name}!", 'success')
                self._chain_pacify_seen = seen
        except ImportError:
            pass

        # Chain-equip passive: detect_magic (Ring of Solomon). Auto-identify
        # the BUC status of any wand/scroll/spellbook in FOV.
        try:
            from chain_passives import player_has_passive
            from items import Wand, Scroll, Spellbook
            if player_has_passive(self.player, 'detect_magic'):
                for it in self.ground_items:
                    if (it.x, it.y) in self.visible and isinstance(
                            it, (Wand, Scroll, Spellbook)):
                        it.buc_known = True
        except ImportError:
            pass

        # Chain-equip passive: huginn_muninn -- automatically reveal monsters
        # within 10 tiles for the rest of this player turn, 1/floor charge.
        # (Used here via the encyclopedia menu / observe key; this stamp just
        # lets the renderer know to draw scouted monsters.)

        # Dark rooms: restrict visibility to 1 tile radius
        dark_centers = getattr(self.dungeon, 'dark_rooms', set())
        self.player._in_dark_room = False  # default; updated below
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
            self.player._in_dark_room = in_dark
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
                # Chain-equip passive: three_apples (Anklet of Atalanta T4+).
                # 1/floor, when fleeing, the next 3 moves cost no turn.
                try:
                    from chain_passives import consume_passive_charge
                    if not getattr(self.player, '_three_apples_remaining', 0):
                        if consume_passive_charge(self.player, 'three_apples'):
                            self.player._three_apples_remaining = 3
                            self.add_message(
                                "Atalanta's three apples scatter behind you!",
                                'success')
                except ImportError:
                    pass

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

        # Frozen: encased in ice — skip every other turn (same as slowed).
        # Also halves attack damage at combat use-site (see combat.player_attack).
        if self.player.has_effect('frozen'):
            self._frozen_skip = not getattr(self, '_frozen_skip', False)
            if self._frozen_skip:
                self.add_message("Ice locks your limbs — you cannot move!", 'warning')
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

        # Track player facing direction (used by back_attack_weakness passive).
        if dx != 0 or dy != 0:
            self.player._facing_dx = dx
            self.player._facing_dy = dy
            # Reset the no-move counter used by unseen_when_still passive.
            self.player._chain_no_move_counter = 0

        # Chain-equip passive: no_attack_of_opportunity (Sandals of Hermes
        # T3+) re-purposed as "free disengage". Capture which hostiles were
        # adjacent BEFORE the move; after the move lands, any that are no
        # longer adjacent take a -2 penalty on their next attack roll.
        from chain_passives import player_has_passive
        _aoo_active = player_has_passive(self.player, 'no_attack_of_opportunity')
        _aoo_pre_adjacent: list = []
        if _aoo_active:
            px, py = self.player.x, self.player.y
            for _m in self.monsters:
                if not _m.alive or getattr(_m, 'is_allied', False):
                    continue
                if abs(_m.x - px) <= 1 and abs(_m.y - py) <= 1:
                    _aoo_pre_adjacent.append(_m)

        target = monster_at_tile(self.monsters, nx, ny)
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
            self._apply_aoo_disengage(_aoo_pre_adjacent)
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
        elif (tile_at_dest == WALL and self.dungeon.in_bounds(nx, ny)
              and self._try_phase_step(nx, ny, dx, dy)):
            # Chain-equip passive: phase_step_once_per_floor (Helm of Hades T3+).
            # _try_phase_step moved the player one tile past the wall (or
            # cancelled the move if no opening). Return — turn already handled.
            return
        elif self.dungeon.is_walkable(nx, ny) or (
            self.player.has_effect('phasing') and self.dungeon.in_bounds(nx, ny)
            and self.dungeon.tiles[ny][nx] not in (WATER, LAVA)
        ):
            self.player.x, self.player.y = nx, ny
            self._apply_aoo_disengage(_aoo_pre_adjacent)
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
                    if monster_at_tile(self.monsters, sx, sy) is not None:
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
                # Chain-equip passive: free_move_every_10 (Anklet of Atalanta).
                # Every 10th move is a free action — skip advance_turn entirely.
                _free_move = False
                try:
                    from chain_passives import player_has_passive
                    if player_has_passive(self.player, 'free_move_every_10'):
                        self.player._chain_move_counter = (
                            getattr(self.player, '_chain_move_counter', 0) + 1
                        )
                        if self.player._chain_move_counter >= 10:
                            self.player._chain_move_counter = 0
                            _free_move = True
                            self.add_message(
                                "Atalanta's anklet gives you a free step!", 'success')
                    # three_apples free-move stack (set when player fled this turn).
                    if getattr(self.player, '_three_apples_remaining', 0) > 0:
                        self.player._three_apples_remaining -= 1
                        _free_move = True
                except ImportError:
                    pass
                if not _free_move:
                    self._advance_turn()
                # Haste no longer auto-fires a second _do_move (that doubled
                # the player's keystroke). Speed boost is now implemented in
                # _advance_turn: every other call while hasted, the world
                # tick (monsters/pets/wander) is skipped so the player gets
                # two actions per monster action.

    def _try_phase_step(self, wx: int, wy: int, dx: int, dy: int) -> bool:
        """Attempt to step one tile through a wall (chain-equip phase_step passive).

        Returns True if a phase-step was performed (charge consumed, turn spent);
        False if no charge available or there's no walkable tile past the wall.
        """
        try:
            from chain_passives import is_charge_available, consume_passive_charge
        except ImportError:
            return False
        if not is_charge_available(self.player, 'phase_step_once_per_floor'):
            return False
        # The "destination" is one tile past the wall in the same direction.
        tx, ty = wx + dx, wy + dy
        if not self.dungeon.in_bounds(tx, ty):
            return False
        if not self.dungeon.is_walkable(tx, ty):
            return False
        if monster_at_tile(self.monsters, tx, ty) is not None:
            return False
        consume_passive_charge(self.player, 'phase_step_once_per_floor')
        self.player.x, self.player.y = tx, ty
        self._refresh_fov()
        self._tick_sp()
        self.add_message("You step THROUGH the stone like Hades' helm. The wall does not see you.", 'success')
        self._notify_stairs(tx, ty)
        self._notify_ground(tx, ty)
        self._advance_turn()
        return True

    def _apply_aoo_disengage(self, pre_adjacent: list):
        """Mark monsters that the player just stepped AWAY from for an AOO
        penalty on their next attack. Used by the chain-equip passive
        no_attack_of_opportunity (Sandals of Hermes T3+) — re-purposed as
        'free disengage'."""
        if not pre_adjacent:
            return
        px, py = self.player.x, self.player.y
        for m in pre_adjacent:
            if not m.alive:
                continue
            still_adjacent = abs(m.x - px) <= 1 and abs(m.y - py) <= 1
            if not still_adjacent:
                m._aoo_disengage_pending = True

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
        self.add_message(">> A scroll materializes from the void. <<", 'loot')

        # Destroy Death
        self.death_pursues = False
        self.death_monster = None
        # Mark this run as the SECRET-victory path so the victory screen
        # renders the Abyss-distinct variant (arcane purple, "DEATH IS DEAD"
        # headline) instead of the standard gold "VICTORY!" screen.
        self._secret_victory = True
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

        # Tick hero-special cooldowns
        for sid in list(getattr(self.player, 'hero_special_cooldowns', {})):
            self.player.hero_special_cooldowns[sid] -= 1
            if self.player.hero_special_cooldowns[sid] <= 0:
                del self.player.hero_special_cooldowns[sid]

        # Elder Blood escape: triggered by player.take_damage when HP <25%; teleports.
        if self.player.status_effects.pop('_pending_elder_escape', 0):
            self.add_message(
                "Elder Blood ignites! Space buckles around you...", 'success')
            self._teleport_player()
        # Chain-equip passive: free_escape_once_per_floor — same trigger, distinct slot.
        if self.player.status_effects.pop('_pending_chain_escape', 0):
            self.add_message(
                "Winged Sandals flare! You leap clear of danger!", 'success')
            self._teleport_player()

        # Tick monster status effects (DOT damage, duration expiry)
        for m in self.monsters:
            if m.alive:
                m.tick_effects()
                if not m.alive:
                    self._on_monster_killed(m)
                    self.add_message(f"The {m.name} succumbs to its wounds!", 'combat')

        # Duck of Doom: advance the 2026-turn worn-on-head counter and
        # trigger hatch on completion.
        self._duck_of_doom_tick()

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
            elif text.startswith('_disease_drain:'):
                # Wire the Paracelsus quirk: disease draining stats counts.
                try:
                    _, _drain_stat, _drain_amt = text.split(':')
                    _qs_disease = getattr(self, 'quirk_system', None)
                    if _qs_disease:
                        _qs_disease.on_disease_drain(_drain_stat, int(_drain_amt))
                except (ValueError, AttributeError):
                    pass
            else:
                self.add_message(text, mtype)

        # Status-effect damage (poison, bleeding, strangulation, doomed) can
        # reduce HP to 0 — must trigger death. Previously only _petrify_death
        # was caught here, so a player poisoned to 0 HP kept walking.
        if self.state != STATE_DEAD and self.player.is_dead():
            self.defeat_reason = 'died'
            self._on_game_over()
            self.state = STATE_DEAD
            # Distinguish cause for the death-screen tone
            if self.player.has_effect('poisoned'):
                self.add_message("The poison stops your heart. You collapse.", 'danger')
            elif self.player.has_effect('bleeding'):
                self.add_message("You bleed out. The dungeon is silent.", 'danger')
            elif self.player.has_effect('strangulation'):
                self.add_message("The strangling grip closes — you cannot breathe.", 'danger')
            elif self.player.has_effect('doomed'):
                self.add_message("The doom curse takes its toll. You fall.", 'danger')
            else:
                self.add_message("You have died! Press ESC to quit.", 'danger')

        if self.state == STATE_DEAD:
            return

        # Phasing safety net: if phasing expired this tick and the player
        # is standing on a non-walkable tile (wall), bump them to the
        # nearest walkable neighbor so movement isn't soft-locked. Floor
        # tiles always cover this — only triggers on the rare wall-stand.
        if (not self.player.has_effect('phasing')
                and self.dungeon.in_bounds(self.player.x, self.player.y)
                and not self.dungeon.is_walkable(self.player.x, self.player.y)):
            for _dy in range(-2, 3):
                for _dx in range(-2, 3):
                    _nx, _ny = self.player.x + _dx, self.player.y + _dy
                    if self.dungeon.is_walkable(_nx, _ny):
                        self.player.x, self.player.y = _nx, _ny
                        self.add_message(
                            "You feel solid again — the wall pushes you back into open space.",
                            'info')
                        break
                else:
                    continue
                break

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
        # Eye of Horus: passive HP regen every N turns.
        # Mastery (accessory_passive_strength/passive_regen_bonus) adds to the regen amount.
        for _acc in self.player.equipped_accessories:
            _pr = getattr(_acc, 'passive_regen', 0)
            _pri = getattr(_acc, 'passive_regen_interval', 5)
            _mast = self.player.unlocked_masteries.get(getattr(_acc, 'id', None))
            if _mast and _mast.get('kind') == 'accessory_passive_strength':
                _mv = _mast.get('value') or {}
                if _mv.get('kind') == 'passive_regen_bonus':
                    _pr += int(_mv.get('value', 0))
            if _pr > 0 and self.turn_count % _pri == 0:
                if self.player.hp < self.player.max_hp:
                    self.player.hp = min(self.player.max_hp, self.player.hp + _pr)

        # Coat of Cú Chulainn: berserk trigger at low HP, HP cost while active.
        # STR refund + expiry message are handled by status_effects.tick_all
        # so we don't need to manually re-trigger or refund here.
        _berserk_armor = next(
            (a for a in self.player.armor_slots
             if a and getattr(a, 'berserk_trigger', False)),
            None
        )
        if _berserk_armor:
            if not self.player.has_effect('berserk'):
                _bpct = _berserk_armor.berserk_hp_threshold
                if self.player.hp > 0 and self.player.hp / max(1, self.player.max_hp) <= _bpct:
                    self.player.STR += _berserk_armor.berserk_str_bonus
                    self.player._berserk_str_bonus = _berserk_armor.berserk_str_bonus
                    self.player.add_effect('berserk', _berserk_armor.berserk_duration)
                    self.add_message("The ríastrad takes hold! Your body warps with primal fury!", 'combat')
            else:
                # HP cost per turn while berserk is active
                self.player.hp = max(1, self.player.hp - _berserk_armor.berserk_hp_cost)

        # Seal of Solomon: pacify nearby monsters
        for _acc in self.player.equipped_accessories:
            if getattr(_acc, 'pacify_chance', 0) > 0:
                for m in self.monsters:
                    if m.alive and abs(m.x - self.player.x) <= 2 and abs(m.y - self.player.y) <= 2:
                        if random.random() < _acc.pacify_chance:
                            m.add_effect('paralyzed', 1)

        # Clairvoyant: reveal tiles within 10-tile radius each turn.
        # class_acc_passive_radius (ring_of_clairvoyance): mastered class adds
        # +N tiles to the reveal radius.
        if self.player.has_effect('clairvoyant'):
            px, py = self.player.x, self.player.y
            radius = 10 + self.player.get_class_mastery_passive_radius_bonus('clairvoyance')
            for cy in range(max(0, py - radius), min(self.dungeon.height, py + radius + 1)):
                for cx in range(max(0, px - radius), min(self.dungeon.width, px + radius + 1)):
                    if abs(cx - px) + abs(cy - py) <= radius:
                        self.dungeon.explored.add((cx, cy))

        # Torc of Boudicca: AC bonus when surrounded by 3+ enemies
        _surr_bonus = 0
        for _acc in self.player.equipped_accessories:
            if getattr(_acc, 'surrounded_ac_bonus', 0) > 0:
                _adj_enemies = sum(1 for m in self.monsters if m.alive
                                   and abs(m.x - self.player.x) <= 1
                                   and abs(m.y - self.player.y) <= 1)
                if _adj_enemies >= 3:
                    _surr_bonus = _acc.surrounded_ac_bonus
                break
        self.player._surrounded_ac_bonus = _surr_bonus

        # Haste: player moves twice as fast as monsters. Every other call
        # while hasted, skip the world tick (monsters/pets/wander spawns)
        # so 2 player actions = 1 monster action. Player-side ticks
        # (cooldowns, status durations, HP regen) happen normally on every
        # action. When haste expires, reset the toggle so a fresh haste
        # starts the cycle from the same phase.
        if self.player.has_effect('hasted'):
            self._haste_skip_world = not getattr(self, '_haste_skip_world', False)
        else:
            self._haste_skip_world = False

        if not self._haste_skip_world:
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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
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
        # Rewired traps (AI chain >= 3) skip the player — they're armed for monsters.
        if trap.get('safe_for_player'):
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
            and not monster_at_tile(self.monsters, x, y) is not None
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
        """Warn if monsters are within 5 tiles when player has the warning effect.

        class_acc_passive_radius (ring/amulet_of_warning): mastered class
        extends the warning radius by +N tiles.
        """
        if not self.player.has_effect('warning'):
            return
        px, py = self.player.x, self.player.y
        radius = 5 + self.player.get_class_mastery_passive_radius_bonus('warning')
        nearby = [
            m for m in self.monsters
            if m.alive and abs(m.x - px) <= radius and abs(m.y - py) <= radius
            and (m.x, m.y) not in self.visible
        ]
        if nearby:
            self.add_message(
                f"Your danger sense tingles! ({len(nearby)} unseen threat{'s' if len(nearby) > 1 else ''} near)",
                'warning'
            )

    def _do_searching(self):
        """Auto-reveal adjacent tiles, secret doors, and traps when player is searching.

        class_acc_passive_radius (ring/amulet_of_searching): mastered class
        extends the searching radius by +N tiles around the player.
        """
        if not self.player.has_effect('searching'):
            return
        px, py = self.player.x, self.player.y
        radius = 1 + self.player.get_class_mastery_passive_radius_bonus('searching')
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
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
        # Also reveal adjacent ambush monsters (radius scales with the mastery)
        for m in self.monsters:
            if (m.alive and m.ai_pattern == 'ambush'
                    and not getattr(m, '_aware', False)
                    and abs(m.x - px) <= radius and abs(m.y - py) <= radius):
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
        """Try to defuse-or-rewire an adjacent revealed trap via AI escalator-chain quiz.

        AI quiz outcomes by chain depth:
          0 - trap fires on you AND you lose your next turn (panicked fumble)
          1 - trap fires on you (botched but contained — no extra turn loss)
          2 - no change: trap stays put but does not fire. You burned a turn.
          3 - trap removed cleanly
          4 - trap REWIRED: re-armed, only monsters trigger it; you walk over freely
          5 - same as 4, plus a free random hint (you learned something about the world)
        Returns True if a quiz was started (consumed the input), False otherwise.
        """
        px, py = self.player.x, self.player.y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                trap = self.dungeon.traps.get((nx, ny))
                if not trap or not trap.get('revealed'):
                    continue
                trap_name = trap['type'].replace('_', ' ')
                self.quiz_title = f"DISARMING {trap_name.upper()} -- AI"
                self.state = STATE_QUIZ
                _trap_pos = (nx, ny)

                def _on_disarm(result, pos=_trap_pos, tname=trap_name):
                    self.state = STATE_PLAYER
                    chain = result.score
                    self._resolve_trap_disarm(pos, tname, chain)

                self.quiz_engine.start_quiz(
                    mode='escalator_chain',
                    subject='ai',
                    tier=1,
                    callback=_on_disarm,
                    max_chain=5,
                    wisdom=self.player.WIS,
                    timer_modifier=self.player.get_quiz_timer_modifier(),
                    extra_seconds=self.player.get_quiz_extra_seconds('ai'),
                    base_seconds=self.player.get_quiz_timer('ai'),
                )
                return True
        return False  # no revealed trap nearby

    def _resolve_trap_disarm(self, pos: tuple, tname: str, chain: int):
        """Apply the chain-tiered outcome of an AI disarm attempt.

        Called from _try_disarm_trap.on_complete. See that method's docstring
        for the chain -> outcome ladder.
        """
        px, py = pos
        trap = self.dungeon.traps.get(pos)
        if trap is None:
            self._advance_turn()
            return

        if chain == 0:
            # Catastrophic fumble: trap fires on you and you burn an extra turn.
            self.add_message(
                f"You panic with the {tname} trap! It snaps as you flinch back.", 'warning')
            self._check_floor_trap(px, py)
            self._advance_turn()   # extra turn cost (the fumble)
            self._advance_turn()   # normal turn for the action
            return

        if chain == 1:
            # Botched but contained: trap fires, but no extra turn lost.
            self.add_message(
                f"You fumble the {tname} trap — it triggers on you.", 'warning')
            self._check_floor_trap(px, py)
            self._advance_turn()
            return

        if chain == 2:
            # No change: trap untouched, no trigger, but you burned a turn.
            self.add_message(
                f"You hesitate over the {tname} trap. It remains armed.", 'warning')
            self._advance_turn()
            return

        if chain == 3:
            # Clean disarm.
            del self.dungeon.traps[pos]
            self.add_message(
                f"You carefully disarm the {tname} trap.", 'success')
            if not getattr(self, '_chronicle_first_disarm', False):
                self._chronicle_first_disarm = True
                self._log_chronicle(
                    "Disarmed my first trap. Hands were shaking the whole time."
                )
            self._advance_turn()
            return

        # Chain 4+: REWIRE the trap toward monsters.
        trap['rewired'] = True
        trap['safe_for_player'] = True
        self.add_message(
            f"You rewire the {tname} trap! It will trigger on the next monster to cross it.",
            'success')
        if not getattr(self, '_chronicle_first_rewire', False):
            self._chronicle_first_rewire = True
            self._log_chronicle(
                f"Rewired a {tname} trap to fire on monsters instead. The dungeon's "
                "own teeth turned against it."
            )

        # Chain 5 bonus: pull a random hint from the lore pool.
        if chain >= 5:
            hint = self._random_hint_for_disarm()
            if hint:
                self.add_message(
                    "As you finish, the trap's geometry reveals something true:", 'success')
                self.add_message(f'"{hint}"', 'info')
                if hasattr(self, '_recalled_hints'):
                    self._recalled_hints.append(hint)
        self._advance_turn()

    def _fire_trap_on_monster(self, monster, trap: dict, pos: tuple) -> None:
        """Fire a rewired trap's effects on a monster. Called when a monster
        steps onto a tile that holds a rewired trap (safe_for_player=True).
        """
        from dice import roll as _dice_roll
        import random as _trng
        trap_type = trap['type']
        _snd.play('trap')
        if (pos in self.visible) or monster in self.monsters:
            self.add_message(
                f"The rewired {trap_type.replace('_', ' ')} trap snaps on the {monster.name}!",
                'success')

        # Apply damage (some traps have damage 0; those are status-only).
        dmg_str = str(trap.get('damage', '0'))
        if dmg_str and dmg_str != '0':
            raw = _dice_roll(dmg_str)
            monster.take_damage(raw)

        # Monster-appropriate status applications (skip player-only effects).
        if trap_type == 'pit':
            monster.status_effects['stuck_in_pit'] = max(
                monster.status_effects.get('stuck_in_pit', 0), 3)
        elif trap_type == 'acid':
            monster.status_effects['corroding'] = max(
                monster.status_effects.get('corroding', 0), 5)
        elif trap_type == 'fire':
            monster.status_effects['burning'] = max(
                monster.status_effects.get('burning', 0), 3)
        elif trap_type == 'sleep_gas':
            monster.status_effects['sleeping'] = max(
                monster.status_effects.get('sleeping', 0), _trng.randint(3, 8))
        elif trap_type == 'bear_trap':
            monster.status_effects['immobilized'] = max(
                monster.status_effects.get('immobilized', 0), _trng.randint(2, 4))
        elif trap_type == 'alarm':
            for m in self.monsters:
                if m.alive and abs(m.x - pos[0]) <= 10 and abs(m.y - pos[1]) <= 10:
                    if m.ai_pattern == 'sessile':
                        m.ai_pattern = 'aggressive'
        elif trap_type == 'squeaky_board':
            for m in self.monsters:
                if m.alive:
                    m._alerted = True
                    m.status_effects.pop('sleeping', None)
        # rust / polymorph / teleport: skip on monsters (player-item-targeted effects)

        # Trap is consumed after firing.
        if pos in self.dungeon.traps:
            del self.dungeon.traps[pos]
        if not monster.alive:
            self._on_monster_killed(monster)

    def _random_hint_for_disarm(self) -> str:
        """Pull a random hint from data/hints.json for the chain-5 disarm reward."""
        import json as _hj
        import random as _hrng
        from paths import data_path
        try:
            with open(data_path('data', 'hints.json'), encoding='utf-8') as f:
                hints = _hj.load(f)
        except Exception:
            return ''
        # hints.json is keyed by tier ('1'..'5'); pick across all tiers
        pool = []
        for tier_hints in hints.values():
            if isinstance(tier_hints, list):
                pool.extend(tier_hints)
        if not pool:
            return ''
        return _hrng.choice(pool)

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
        # Beast-family mastery (sp_regen): adds Nx more turns between drains.
        self._sp_drain_tick = getattr(self, '_sp_drain_tick', 0) + 1
        drain_interval = 4 if self.player.has_effect('sustained') else 2
        fams = getattr(self.player, 'unlocked_monster_class_masteries', {})
        beast = fams.get('beast')
        if beast and beast.get('kind') == 'sp_regen':
            drain_interval += int(beast.get('value', 0))
        # Chain-equip passive: hunger_slow (Idunn Apple Charm). Multiplier
        # on the drain interval -- 0.33 adds 33% more ticks between drains.
        try:
            from chain_passives import get_hunger_slow_factor
            hs = get_hunger_slow_factor(self.player)
            if hs > 0:
                drain_interval = max(2, int(round(drain_interval * (1.0 + hs))))
        except ImportError:
            pass
        # class_acc_sp_burn_bonus: mastered ring of sustenance equipped adds
        # (1 + value) multiplier to the drain interval (slower drain).
        _sp_factor = self.player.get_class_mastery_sp_burn_factor()
        if _sp_factor > 0:
            drain_interval = max(2, int(round(drain_interval * (1.0 + _sp_factor))))
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
        """Regen 1 HP every 15 turns (faster with high CON). Blocked by bleeding/poisoned.

        Chain-equip tier_bonuses can set `player.regen_bonus`, which adds extra
        HP per tick (e.g. Cloak of the Morrigan T2+, Helm of Aragorn T3+).

        Reassembly (chain-equip Tyet T5) grants a 10-turn aggressive-regen
        window after a near-death save; ticks down here.
        """
        # Reassembly regen: fast HP regen window after Tyet T5 save.
        if getattr(self.player, '_reassembly_regen_remaining', 0) > 0:
            self.player._reassembly_regen_remaining -= 1
            self.player.restore_hp(max(1, self.player.max_hp // 20))
            return

        if self.player.hp >= self.player.max_hp:
            return
        if self.player.has_effect('bleeding') or self.player.has_effect('poisoned'):
            return
        # CON above 12 shaves 1 turn off the interval per point; floor at 10
        interval = max(10, 20 - max(0, self.player.CON - 12))
        if self.turn_count % interval == 0:
            base_regen = 1 + max(0, getattr(self.player, 'regen_bonus', 0))
            # class_acc_regen_bonus: equipped ring/amulet of regeneration
            # adds +N HP per tick when its class is mastered.
            base_regen += self.player.get_class_mastery_regen_bonus()
            self.player.restore_hp(base_regen)

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
            # Draupnir: double gold pickups. Mastery overrides to a stronger multiplier.
            for _acc in self.player.equipped_accessories:
                _gm = getattr(_acc, 'gold_multiplier', 0)
                _mast = self.player.unlocked_masteries.get(getattr(_acc, 'id', None))
                if _mast and _mast.get('kind') == 'accessory_passive_strength':
                    _mv = _mast.get('value') or {}
                    if _mv.get('kind') == 'gold_multiplier':
                        _gm = max(_gm, float(_mv.get('value', _gm)))
                if _gm > 0:
                    _gold_amt = int(_gold_amt * _gm)
                    break
            # Andvaranaut: gold_finds_pct mastery — bonus gold on pickup (additive %).
            _gold_finds_bonus_pct = 0
            for _acc in self.player.equipped_accessories:
                _mast = self.player.unlocked_masteries.get(getattr(_acc, 'id', None))
                if _mast and _mast.get('kind') == 'accessory_passive_strength':
                    _mv = _mast.get('value') or {}
                    if _mv.get('kind') == 'gold_finds_pct':
                        _gold_finds_bonus_pct += int(_mv.get('value', 0))
            if _gold_finds_bonus_pct > 0:
                _bonus = int(_gold_amt * _gold_finds_bonus_pct / 100)
                _gold_amt += _bonus
            self.player_gold += _gold_amt
            self.ground_items.remove(item)
            self.add_message(f"You pick up {_gold_amt} gold coins.", 'loot')
            _snd.play('gold')
            self._advance_turn()
            return
        if isinstance(item, Lockpick):
            # Lockpicks are no longer needed — player already has the Master
            # Lockpick from char-creation. Treat floor picks as a small gold
            # find so the item isn't a dead drop if old saves still have it.
            self.player_gold += 5
            self.ground_items.remove(item)
            self.add_message("You don't need this — your master kit is sufficient. (+5 gold scrap value)", 'info')
            self._advance_turn()
            return
        # ── Duck of Doom intercept: cursed headgear that auto-equips ──
        # Per Munchkin lore: "You should know better than to pick up a
        # duck in a dungeon." Pickup bypasses inventory entirely; the
        # duck force-equips to the head slot (kicking even a cursed
        # existing helmet into inventory) and stays welded there until
        # the 2026-turn quirk transforms it into a pet.
        if getattr(item, 'id', '') == 'duck_of_doom':
            self._duck_of_doom_pickup(item)
            return

        if self.player.add_to_inventory(item):
            self.ground_items.remove(item)
            _snd.play('pickup')
            # Philosopher's Stone grants identify_sight — auto-identify on pickup
            if self.player.has_effect('identify_sight'):
                item.identified = True
                item.id_level = max(getattr(item, 'id_level', 0), 4)
                self.player.known_item_ids.add(item.id)
            # Pattern Recognition (75 IDs): auto-reveal name + BUC + stats (id_level=3) on
            # lesser COMMON items at depth. Lore (id_level=4) and mastery (id_level=5)
            # still require studying the item via the philosophy quiz from the I-menu.
            # Uniques are preserved for the chain-5 dramatic flow.
            if 75 in self.player.philosopher_tier_claimed and not getattr(item, 'is_unique', False):
                tier_gate = 1 + (self.dungeon_level // 30)
                if hasattr(item, 'id_level') and item.id_level < 3 and \
                        getattr(item, 'quiz_tier', 5) <= tier_gate:
                    item.id_level = 3
                    item.buc_known = True
                    self.player.known_item_ids.add(item.id)
            # Philosopher's Mantle (300 IDs): auto BUC-sense on every pickup, including uniques.
            if self.player.philosophers_mantle and hasattr(item, 'buc_known'):
                item.buc_known = True
            if isinstance(item, Ammo):
                self.add_message(f"You pick up {item.count} {self._display_name(item)}s.", 'loot')
            else:
                self.add_message(f"You pick up the {self._display_name(item)}.", 'loot')
            # Chronicle notable pickups (quest artifacts)
            _CHRONICLE_ITEMS = {
                'philosophers_stone', 'ariadnes_thread', 'bronze_bull',
                'eye_of_graeae', 'broken_gram', 'gleipnir',
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
                    'eye_of_graeae': "A milky white eye, still wet. I don't want to think about where it came from.",
                    'broken_gram': "Half a legendary sword. Even broken, the edge could shave a thought.",
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
            # Material discovery chronicle: first time the player sees each
            # material (cold iron, mithril, etc.), log the discovery line.
            _mat_id = getattr(item, 'material', None)
            if _mat_id and _mat_id not in self.player.chronicle_seen_materials:
                from items import get_material
                _mat_defn = get_material('weapons', _mat_id) or get_material('armor', _mat_id)
                if _mat_defn:
                    _chronicle_line = _mat_defn.get('first_pickup_chronicle')
                    if _chronicle_line:
                        self._log_chronicle(_chronicle_line)
                        self.player.chronicle_seen_materials.add(_mat_id)
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
    # Duck of Doom — Munchkin reference. One per run, on a uniform-random
    # floor in {1..10}. Looks like an adorable yellow duckie sitting on
    # the floor. Pickup auto-equips it as cursed headgear (+2 AC, can't
    # remove). Worn for 2026 turns -> transforms into Waddlekind, a
    # psychic-pet that follows standard pet rules (evolves at L25 and
    # L55 into Drake of the Covenant -> Seraphimallard). Permadeath for
    # the run if the pet dies.
    # ------------------------------------------------------------------

    DUCK_OF_DOOM_TURNS_REQUIRED = 2026

    def _maybe_place_duck_of_doom(self, level: int):
        """Drop the Duck of Doom on its assigned floor (first entry only)."""
        if self._duck_of_doom_placed:
            return
        if level != self._duck_of_doom_floor:
            return
        # Skip if the player is already carrying or wearing one (defensive).
        head = self.player.armor_slots[0] if self.player.armor_slots else None
        if head is not None and getattr(head, 'id', '') == 'duck_of_doom':
            self._duck_of_doom_placed = True
            return
        if any(getattr(i, 'id', '') == 'duck_of_doom' for i in self.player.inventory):
            self._duck_of_doom_placed = True
            return
        # Pick a walkable floor tile away from the player.
        import json as _json
        from paths import data_path
        from items import Armor
        with open(data_path('data', 'items', 'armor.json'), encoding='utf-8') as _f:
            _armor_defs = _json.load(_f)
        _defn = {'id': 'duck_of_doom', **_armor_defs['duck_of_doom']}
        # Find a candidate tile: floor, not on player, not already occupied
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied.add((self.player.x, self.player.y))
        occupied |= {(i.x, i.y) for i in self.ground_items}
        candidates = []
        for room in self.dungeon.rooms:
            for tx, ty in room.inner_tiles():
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    candidates.append((tx, ty))
        if not candidates:
            return  # nowhere to drop — give up silently
        spawn_x, spawn_y = random.choice(candidates)
        duck = Armor(_defn)
        duck.x, duck.y = spawn_x, spawn_y
        self.ground_items.append(duck)
        self._duck_of_doom_placed = True

    def _duck_of_doom_pickup(self, duck):
        """Intercept of normal pickup. The duck force-equips to the head
        slot, kicking the existing head armor (cursed or not) into
        inventory. The Duck is itself cursed, so try_unequip_slot will
        refuse to remove it through normal channels."""
        # Remove from ground
        if duck in self.ground_items:
            self.ground_items.remove(duck)
        # Force-displace the existing head armor (bypass try_unequip_slot
        # to allow displacing a cursed helmet — the Duck's magic
        # supersedes lesser curses).
        head_idx = 0  # 'head' is armor_slots[0]
        old = self.player.armor_slots[head_idx] if self.player.armor_slots else None
        if old is not None:
            self.player.armor_slots[head_idx] = None
            old_status = getattr(old, 'on_equip_status', '')
            if old_status:
                self.player.status_effects.pop(old_status, None)
            # Try to put old into inventory; if over weight, drop on floor
            if not self.player.add_to_inventory(old):
                old.x, old.y = self.player.x, self.player.y
                self.ground_items.append(old)
                self.add_message(
                    f"The {self._display_name(old)} clatters to the floor.",
                    'warning')
        # Equip the Duck.
        duck.identified = False  # stays unknown until identified
        duck.id_level = max(getattr(duck, 'id_level', 0), 0)
        self.player.armor_slots[head_idx] = duck
        _snd.play('pickup')
        self.add_message(
            "The duckie hops onto your head! It feels… stuck. Heavy. Wrong.",
            'danger')
        self.add_message(
            "(You should know better than to pick up a duck in a dungeon.)",
            'warning')
        self._log_chronicle(
            "I picked up a duck. It's on my head now. It won't come off.")
        # Start the quirk timer fresh.
        if not hasattr(self.player, 'quirk_progress') or self.player.quirk_progress is None:
            self.player.quirk_progress = {}
        self.player.quirk_progress['duck_of_doom_turns'] = 0
        self._advance_turn()

    def _duck_of_doom_tick(self):
        """Called once per turn from _advance_turn. If the Duck is on
        the head slot, advance the quirk counter; transform at 2026."""
        head = self.player.armor_slots[0] if self.player.armor_slots else None
        if head is None or getattr(head, 'id', '') != 'duck_of_doom':
            return
        if not hasattr(self.player, 'quirk_progress') or self.player.quirk_progress is None:
            self.player.quirk_progress = {}
        n = self.player.quirk_progress.get('duck_of_doom_turns', 0) + 1
        self.player.quirk_progress['duck_of_doom_turns'] = n
        if n >= self.DUCK_OF_DOOM_TURNS_REQUIRED:
            self._duck_of_doom_transform()

    def _duck_of_doom_transform(self):
        """At 2026 turns, the Duck hatches: remove the item from the
        head slot and spawn a Waddlekind pet at the player's tile."""
        from pet_system import Pet
        # Remove the duck from head; no inventory copy — the item is
        # CONSUMED by the transformation.
        head = self.player.armor_slots[0] if self.player.armor_slots else None
        if head is None or getattr(head, 'id', '') != 'duck_of_doom':
            return  # defensive; shouldn't happen
        self.player.armor_slots[0] = None
        # Clear the quirk counter so a second Duck (impossible in
        # normal play, but defensive) starts at 0.
        self.player.quirk_progress.pop('duck_of_doom_turns', None)
        # Pet spawns on player's tile (player can step away next turn).
        pet = Pet('duck_of_doom', self.player.x, self.player.y)
        self.pets.append(pet)
        self.add_message(
            "The duckie's eyes glow. It hops off your head, suddenly weightless.",
            'success')
        self.add_message(
            f"Waddlekind has hatched! ({pet.name})",
            'success')
        self._log_chronicle(
            "The duck on my head hatched. I have a tiny celestial duckling now. "
            "It can read minds. I have made a friend.")
        # Award the registered quirk so the unlock ceremony fires and the
        # Quirks menu shows this run's achievement as unlocked. The
        # mechanical "reward" (the pet) has already been spawned above,
        # so apply_fn is a no-op.
        qs = getattr(self, 'quirk_system', None)
        if qs is not None:
            qs._award('duck_of_doom', "The Duck of Doom", lambda pl: None)

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

        # Chain-equip passive: solomonic_key (Ring of Solomon T5).
        # 1/floor: bypass any lock in sight, no quiz. Yields chain-3 loot.
        try:
            from chain_passives import consume_passive_charge
            if consume_passive_charge(self.player, 'solomonic_key'):
                cx, cy = container.x, container.y
                from container_system import _handle_success
                _result = {'status': 'pending', 'loot': [], 'gold': 0, 'messages': []}
                def _solom_cb(res):
                    _result.update(res)
                _handle_success(self.player, container, self.dungeon, 3, _solom_cb)
                self.ground_items.remove(container)
                for text, mtype in _result['messages']:
                    self.add_message(text, mtype)
                for loot_item in _result['loot']:
                    loot_item.x, loot_item.y = cx, cy
                    self.ground_items.append(loot_item)
                    self.add_message(f"You find {self._display_name(loot_item)}!", 'loot')
                if _result['gold'] > 0:
                    from items import add_gold_to_tile
                    add_gold_to_tile(self.ground_items, _result['gold'], cx, cy)
                self.add_message(
                    "The Ring of Solomon hums; the lock opens at a touch!", 'success')
                self._advance_turn()
                return
        except ImportError:
            pass

        # Master Lockpick is permanent; no charge check.
        # Post-2026-05-19: escalator-chain quiz. Chain reached drives loot
        # quality (chain 0 = empty open; chain 5 = master thief, bonus item).
        _q_tier = int(getattr(container, 'quiz_tier', getattr(container, 'tier', 1)))
        self.quiz_title = (
            f"PICKING {container.name.upper()}  --  ECONOMICS  "
            f"(starts tier {_q_tier}, chain for better loot)"
        )
        self.state = STATE_QUIZ

        def on_complete(result: dict):
            self.state = STATE_PLAYER
            for text, mtype in result['messages']:
                self.add_message(text, mtype)

            # Post-2026-05-19 rebuild: chain 0 reports status='opened' with
            # empty loot list (chest visually opens but yields nothing). The
            # quirk hooks distinguish on result['chain'] == 0 vs >= 1.
            chain = int(result.get('chain', 0))
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
                    from items import add_gold_to_tile
                    add_gold_to_tile(self.ground_items, result['gold'], cx, cy)
                _qs_lk = getattr(self, 'quirk_system', None)
                if _qs_lk:
                    if chain >= 1:
                        _qs_lk.on_lockpick_success()
                    else:
                        # Chain 0 fumble: log as lockpick fail for quirk progress
                        if getattr(container, 'trapped', False):
                            _qs_lk.on_lockpick_fail(container.id, self.dungeon_level)
                        if getattr(container, 'trap', None):
                            trap_type = container.trap.get('type', '') if isinstance(container.trap, dict) else ''
                            if trap_type:
                                _qs_lk.on_trap_triggered(trap_type)

            self._advance_turn()

        attempt_lockpick(
            self.player, container,
            self.quiz_engine, self.dungeon, self.monsters,
            on_complete
        )

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
    # Throw Potion  (T key)  -- helpers/openers/confirms live in CombatMixin.
    # ``_THROW_TABS`` stays here because MenuMixin and RenderMixin read it.
    # ------------------------------------------------------------------

    _THROW_TABS = [
        ('Potions', lambda i: isinstance(i, Potion)),
        ('Weapons', lambda i: isinstance(i, Weapon)),
        ('Other',   lambda i: not isinstance(i, (Potion, Weapon))),
    ]

    # ------------------------------------------------------------------
    # Tile interactions  (D key -- fountain/grave/throne)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Recall Lore
    # ------------------------------------------------------------------

    def _has_tablet_of_destinies(self) -> bool:
        """Check if player is carrying the Tablet of Destinies artifact."""
        return any(getattr(i, 'id', '') == 'tablet_of_destinies' for i in self.player.inventory)

    def _on_quiz_answer(self, is_correct: bool):
        """Fired after every individual quiz answer to tally global stats."""
        qe = self.quiz_engine
        if is_correct:
            self.correct_answers += 1
            _snd.play('quiz_correct')
        else:
            self.wrong_answers += 1
            _snd.play('quiz_wrong')
            # Store missed question for post-death review
            q = qe.current_question
            if q:
                self.missed_questions.append({
                    'subject': qe.subject,
                    'question': q.get('question', ''),
                    'correct': str(q.get('answer', '')),
                    'chosen': qe.last_answer,
                    'context': q.get('context', ''),
                })
        # Per-subject + per-tier stats for the Discoveries panel.
        subj = (qe.subject or 'unknown')
        tier = int(getattr(qe, 'tier', 1) or 1)
        s = self.quiz_stats.setdefault(subj, {
            'correct': 0, 'wrong': 0,
            't1c': 0, 't1w': 0, 't2c': 0, 't2w': 0,
            't3c': 0, 't3w': 0, 't4c': 0, 't4w': 0,
            't5c': 0, 't5w': 0,
        })
        if is_correct:
            s['correct'] = s.get('correct', 0) + 1
            s[f't{tier}c'] = s.get(f't{tier}c', 0) + 1
        else:
            s['wrong'] = s.get('wrong', 0) + 1
            s[f't{tier}w'] = s.get(f't{tier}w', 0) + 1
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

    def _on_quiz_complete(self, result, mode: str, subject: str,
                          correct_count: int, wrong_count: int):
        """Fired once when a quiz session ends — drives per-session quirks (Apollo, Cassandra)."""
        qs = getattr(self, 'quirk_system', None)
        if not (qs and self.player):
            return
        qs.on_quiz_complete(
            mode=mode,
            subject=subject,
            score=result.score,
            correct_count=correct_count,
            wrong_count=wrong_count,
            success=result.success,
            while_blinded=self.player.has_effect('blinded'),
            while_confused=self.player.has_effect('confused'),
            while_hallucinating=(self.player.has_effect('hallucinating') or
                                 self.player.has_effect('hallucinating_pot')),
        )


    # ------------------------------------------------------------------
    # XYZZY — Hack Reality (hidden feature)
    # ------------------------------------------------------------------

    def _open_xyzzy_input(self):
        """Open the hidden green terminal for entering the magic word."""
        self._xyzzy_text = ''
        self._xyzzy_blink = 0
        self.state = STATE_XYZZY_INPUT

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
            self.add_message(msg, 'success')

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
                if monster_at_tile(self.monsters, nx, ny) is not None:
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

    # ------------------------------------------------------------------
    # Character sheet  (@)
    # ------------------------------------------------------------------

    def _open_character_sheet(self):
        self._charsheet_scroll = 0
        self.state = STATE_CHARACTER_SHEET


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

    def _remove_status_if_no_other_grants(self, status: str) -> None:
        """Pop a permanent status from the player only if no OTHER currently-
        equipped item still grants it. Without this guard, unequipping any
        one of N stacked items that grant the same status (e.g. two Rings of
        Warning both granting 'warning') would drop the effect entirely.

        Assumes the just-unequipped item has already been cleared from its
        slot. See bug-bash A2-6.
        """
        from items import Accessory as _Acc
        slot_iter = []
        slot_iter.append(getattr(self.player, 'weapon', None))
        slot_iter.append(getattr(self.player, 'shield', None))
        slot_iter.extend(getattr(self.player, 'armor_slots', []) or [])
        slot_iter.extend(getattr(self.player, 'accessory_slots', []) or [])
        slot_iter.append(getattr(self.player, 'amulet_slot', None))
        for other in slot_iter:
            if other is None:
                continue
            if isinstance(other, _Acc):
                ofx = getattr(other, 'effects', {}) or {}
                if ofx.get('status') == status:
                    return  # another item still grants this status — keep it
        self.player.status_effects.pop(status, None)

    def _unequip_slot(self, slot_name: str, item):
        """Remove an equipped item and return it to inventory."""
        from items import ARMOR_SLOTS
        from chain_equip import is_chain_equip, revert_tier_bonuses
        ok, msg = self.player.try_unequip_slot(item)
        if not ok:
            self.add_message(msg, 'warning')
            return
        # Revert chain-equip tier bonuses BEFORE slot bookkeeping so player
        # state reflects baseline by the time the item returns to inventory.
        if is_chain_equip(item) and getattr(item, 'achieved_tier', 0) > 0:
            revert_tier_bonuses(self.player, item)
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
                    self._remove_status_if_no_other_grants(fx['status'])
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
                    self._remove_status_if_no_other_grants(fx['status'])
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
        """Launch geography threshold quiz to equip armor or shield.

        Legendary uniques with `equip_chain_mode` route to chain-equip instead.
        """
        from chain_equip import is_chain_equip
        if is_chain_equip(item):
            self._start_chain_equip_quiz(item, item_type='armor')
            return
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

        # Legendary uniques with `equip_chain_mode` route to chain-equip
        from chain_equip import is_chain_equip
        if is_chain_equip(item):
            self._start_chain_equip_quiz(item, item_type='accessory')
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
    # Chain-equip: legendary uniques with escalator/chain mode equip-quiz
    # ------------------------------------------------------------------

    def _start_chain_equip_quiz(self, item, item_type: str = 'armor'):
        """Launch escalator-chain or chain quiz to equip a legendary unique.

        The chain length achieved determines tier_bonuses applied via
        chain_equip.apply_tier_bonuses(). Fresh quiz every equip — no
        sticky state. On failure the item is NOT equipped.
        """
        from chain_equip import get_chain_subject, get_chain_mode, apply_tier_bonuses
        item_name = self._display_name(item)
        cursed_tag = " (cursed)" if getattr(item, 'cursed', False) else ""
        subject = get_chain_subject(item)
        mode = get_chain_mode(item)
        self.quiz_title = f"ATTUNING TO {item_name.upper()}  --  {subject.upper()}"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            # QuizResult.score is the peak chain reached (.chain doesn't exist).
            # Matches container_system._handle_success which reads the same field.
            chain = int(getattr(result, 'score', 0))
            chain = max(0, min(5, chain))
            # In chain mode you can fail rung 1 (chain=0). In escalator-chain
            # you must pass tier 1 to start the chain (chain >= 1 = success).
            if chain >= 1:
                apply_tier_bonuses(self.player, item, chain)
                # Now actually equip
                self.player._apply_equip(item)
                self.player.remove_from_inventory(item)
                ac = self.player.get_ac()
                self.add_message(
                    f"You attune to the {item_name}{cursed_tag} at tier {chain}/5. AC is now {ac}.",
                    'success'
                )
                # Chain-equip passive auto-fires at equip time:
                #   dragon_blood_bath -> permanent elemental resist statuses
                #   aesir_young -> 5t protected when newly re-equipped
                _passives = getattr(item, '_chain_passives', {}) or {}
                if 'dragon_blood_bath' in _passives and not getattr(
                        self.player, '_dragon_blood_active', False):
                    self.player._dragon_blood_active = True
                    for _stat in ('fire_resist', 'cold_resist', 'shock_resist'):
                        self.player.add_effect(_stat, -1)
                    self.add_message(
                        "You bathe in the dragon's blood. Elements turn aside!", 'success')
                if 'aesir_young' in _passives:
                    # Grant a brief shielded buff as a stand-in for "protected".
                    self.player.add_effect('shielded', 5)
                    self.add_message(
                        "Idunn's apples wash years away. You are young again.", 'info')
                _qs = getattr(self, 'quirk_system', None)
                if _qs:
                    if item_type == 'armor':
                        from items import Shield
                        slot_type = 'shield' if isinstance(item, Shield) else 'armor'
                        _qs.on_item_equipped(item.id, slot_type, getattr(item, 'slot', slot_type))
                    else:
                        _qs.on_item_equipped(item.id, 'accessory', getattr(item, 'slot', 'accessory'))
            else:
                self.add_message(
                    f"The {item_name} does not recognize you. Try again.", 'warning'
                )
            self._advance_turn()

        # Engine accepts 'escalator_chain' and 'chain'. JSON uses these names
        # directly; the lenient fallback exists for legacy data only.
        if mode not in ('escalator_chain', 'chain'):
            mode = 'escalator_chain'
        self.quiz_engine.start_quiz(
            mode=mode,
            subject=subject,
            tier=int(getattr(item, 'quiz_tier', 1)),
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )


    def _int_scaled_damage(self, base_dmg: int) -> int:
        """Scale magic damage by INT: 1.0x at INT 0, 2.0x at INT 10, 3.0x at INT 20."""
        return max(1, int(base_dmg * (1.0 + self.player.INT * 0.1)))



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
                    self.add_message(">> A remarkable item falls from the defeated foe!", 'loot')
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

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
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

    def _spawn_summoner_minion(self, summoner):
        """Spawn one minion next to a summoner-AI monster.

        Reads summoner.summon_kind (str id, or list of ids → random pick) and
        places one instance on a walkable tile within 3 tiles. Silent on
        failure (no walkable tile, missing kind, etc.) so the summoner just
        loses the cooldown beat — flavor only."""
        import json as _json
        import random as _rng
        from monster import Monster as _Mon
        from paths import data_path as _dp

        kinds = summoner.summon_kind
        if not kinds:
            return
        if isinstance(kinds, str):
            kinds = [kinds]
        kind = _rng.choice(kinds)

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as f:
                _all = _json.load(f)
        except Exception:
            return
        defn = _all.get(kind)
        if not defn:
            return

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied.add((self.player.x, self.player.y))
        candidates = []
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = summoner.x + dx, summoner.y + dy
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if not self.dungeon.is_walkable(nx, ny):
                    continue
                if (nx, ny) in occupied:
                    continue
                candidates.append((nx, ny))
        if not candidates:
            return
        sx, sy = _rng.choice(candidates)
        minion_def = dict(defn)
        minion_def['id'] = kind
        minion = _Mon(minion_def, sx, sy)
        # The summoned minion is immediately aware of the player.
        minion._aware = True
        # Mark as summoned so weaken_summoned (Ring of Solomon) can apply.
        minion._is_summoned = True
        self.monsters.append(minion)
        if (summoner.x, summoner.y) in self.visible or (sx, sy) in self.visible:
            self.add_message(
                f"The {summoner.name} summons a {minion.name}!", 'danger')

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
    # Cow encounter handlers live in game_encounters.EncountersMixin.
    # These player-facing message tables stay on Game so they're easy to
    # tweak alongside the cow-dialog UI; the mixin reaches them via self..

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

    # ------------------------------------------------------------------
    # Scroll menu  (s key -- grammar quiz)
    # ------------------------------------------------------------------

    _SCROLL_TABS = [
        ('Scrolls',    lambda i: isinstance(i, Scroll)),
        ('Spellbooks', lambda i: isinstance(i, Spellbook)),
    ]


    # ------------------------------------------------------------------
    # Display name helper
    # ------------------------------------------------------------------

    _fix_name_case = staticmethod(fix_name_case)
    _a_or_an = staticmethod(a_or_an)

    def _display_name(self, item) -> str:
        """Return the name to show for an item, including stack count when > 1.

        Type known (any of: identified flag, id in known_item_ids, OR the
        item's mastery_class is in known_class_ids) -> item.name.
        Otherwise -> item.unidentified_name.

        The mastery_class check is what lets one Ring of Strength
        identification name ALL ring-of-strength variants in the pack.
        """
        from class_masteries import get_mastery_class
        if not hasattr(item, 'identified'):
            base = self._fix_name_case(item.name)
        else:
            known_by_class = (get_mastery_class(item)
                              in getattr(self.player, 'known_class_ids', set()))
            if item.identified or item.id in self.player.known_item_ids or known_by_class:
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

    def _show_quirk_unlock_popup(self, name: str, effect: str,
                                  trigger: str, flavor: str):
        """A first-class unlock moment for a newly-earned quirk.

        Reuses STATE_STORY_POPUP's chrome (overlay + dark panel + accent
        title + filigree footer) so it feels like the same genre of
        ceremonial moment as the boss-defeat / quest-completion popups,
        rather than a message-log scroll-by. Per audit
        beauty-quirk-unlock-no-moment.
        """
        lines = [
            f'You have earned a new trait: "{name}".',
            '',
            f'Reward: {effect}',
        ]
        if trigger:
            lines.append('')
            lines.append(f'Earned by: {trigger}')
        if flavor:
            lines.append('')
            lines.append(f'"{flavor}"')
        self.popup_data = {
            'title':  'TRAIT UNLOCKED',
            'accent': (200, 170, 255),   # arcane lavender — matches the quirk theme
            'lines':  lines,
            'code':   None,
        }
        self.popup_next_state = self.state if self.state != STATE_STORY_POPUP else STATE_PLAYER
        self.state = STATE_STORY_POPUP


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

    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Examine corpse  (escalator-chain philosophy quiz, 5-tier reveal)
    # ------------------------------------------------------------------
    # Layers per chain rung:
    #   1: name+symbol            (always known)
    #   2: HP, AC, damage         (basic stats)
    #   3: weaknesses, resists,   tags (family) -> propagates to kin
    #   4: full lore text         (lore_identified property True)
    #   5: family mastery unlock  (one blessing per family tag, idempotent)
    # ------------------------------------------------------------------

    def _start_corpse_identify(self, corpse, after_advance_turn: bool = True):
        """Escalator-chain identify on a corpse. Chain reached -> corpse.id_level.

        Already at level 5 -> skip the quiz and just open the lore screen.

        Resume rule (parallel to item identify in game_magic.py): chain
        starts at start_tier = previous_level + 1 with max_chain =
        5 - previous_level. The kid only re-answers the tiers they didn't
        complete. id_level only ever rises, never falls.
        """
        if int(getattr(corpse, 'id_level', 0)) >= 5:
            self._lore_subject = corpse
            self.state = STATE_LORE
            return
        self.quiz_title = f"STUDYING {corpse.monster_name.upper()} CORPSE  --  PHILOSOPHY"
        self.state = STATE_QUIZ

        previous_level = int(getattr(corpse, 'id_level', 0))
        from items import identify_resume_params
        start_tier, max_chain = identify_resume_params(previous_level)

        def on_complete(result):
            self.state = STATE_PLAYER
            chain = int(getattr(result, 'score', 0) or 0)
            # chain measured from start_tier — achieved level = previous + chain.
            new_level = min(5, max(previous_level, previous_level + chain))
            if new_level > previous_level:
                corpse.id_level = new_level
                # Propagate full id_level to all corpses of the same monster_id
                from items import Corpse as _Corpse
                for obj in self.ground_items + list(self.player.inventory):
                    if isinstance(obj, _Corpse) and obj.monster_id == corpse.monster_id:
                        obj.id_level = max(int(getattr(obj, 'id_level', 0)), new_level)
                # At level 3+, you now recognize the family at a glance: bump
                # all same-family corpses (in pack or on ground) to id_level >= 3.
                if new_level >= 3:
                    from monster_classes import get_monster_family
                    fam = get_monster_family(corpse)
                    if fam:
                        for obj in self.ground_items + list(self.player.inventory):
                            if (isinstance(obj, _Corpse) and obj is not corpse
                                    and get_monster_family(obj) == fam):
                                obj.id_level = max(int(getattr(obj, 'id_level', 0)), 3)
                # Level 4+: lore now known (drives lore_identified property and
                # the auto-reveal-on-pickup behavior in _make_corpse).
                if new_level >= 4:
                    self.player.lore_known_monster_ids.add(corpse.monster_id)
                # Level 5: grant the family mastery blessing.
                if new_level >= 5:
                    self._claim_monster_family_mastery(corpse)
                # Chronicle + career arc only on first crossing into "full ID"
                # (level >= 4) — this mirrors how items count for total_identifies.
                if previous_level < 4 and new_level >= 4:
                    self._on_full_identify(corpse)
                self._lore_subject = corpse
                self.state = STATE_LORE
                self.add_message(
                    f"You study the {corpse.monster_name} (level {new_level}/5).",
                    'success'
                )
            else:
                self.add_message(
                    f"You study but learn nothing new (still level "
                    f"{previous_level}/5).",
                    'warning'
                )
                # Backlash from the Shard: zero-correct on a corpse-study
                # chain stuns the kid for 10 turns of Confusion. Mirrors
                # the item-identify branch in
                # game_magic.py:_identify_unique_item. Per user 2026-05-29.
                self.player.add_effect('confused', 10)
                self.add_message(
                    "The Shard turns cold in your palm. Backlash floods "
                    "your mind — you are Confused (10 turns).",
                    'danger')
            if after_advance_turn:
                self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='philosophy',
            tier=start_tier,
            callback=on_complete,
            max_chain=max_chain,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('philosophy'),
            base_seconds=self.player.get_quiz_timer('philosophy'),
        )

    def _claim_monster_family_mastery(self, corpse):
        """Grant the per-family mastery blessing on chain-5 corpse-id. Idempotent."""
        from monster_classes import (get_monster_family,
                                      MONSTER_FAMILY_BLESSINGS)
        fam = get_monster_family(corpse)
        if not fam:
            return
        store = self.player.unlocked_monster_class_masteries
        if fam in store:
            return
        blessing = MONSTER_FAMILY_BLESSINGS.get(fam)
        if not blessing:
            return
        store[fam] = blessing
        # Permanent stat increases are applied here; everything else is
        # queried lazily at the use-site (combat damage, regen tick, etc.).
        kind = blessing.get('kind')
        if kind == 'wisdom_bonus':
            self.player.apply_stat_bonus('WIS', int(blessing.get('value', 0) or 0))
        elif kind == 'int_bonus':
            # Use apply_stat_bonus instead of direct INT += / max_mp = …
            # The direct assignment STOMPS chain-equip max_mp_bonus and other
            # contributors (Robe of the Magus etc.). apply_stat_bonus
            # correctly increments via _intelligence_bonus + recomputes max_mp.
            self.player.apply_stat_bonus('INT', int(blessing.get('value', 0) or 0))
        desc = blessing.get('desc', 'A subtle insight settles upon you.')
        self.add_message(f"Mastery of {fam} family attained! {desc}", 'success')
        self._log_chronicle(
            f"Mastered the {fam} family of monsters. {desc}"
        )

    def _examine_corpse_direct(self, corpse):
        """Called when player selects a corpse from the identify menu."""
        self._start_corpse_identify(corpse, after_advance_turn=True)

    def _examine_corpse(self):
        """Called when player presses the examine key on a corpse on their tile."""
        px, py = self.player.x, self.player.y
        corpse = next(
            (i for i in self.ground_items if i.x == px and i.y == py
             and getattr(i, 'monster_id', None) is not None),
            None
        )
        if corpse is None:
            self.add_message("There is no corpse here to examine.", 'info')
            return
        # Auto-bump to lore tier if this monster type has already been studied
        # to that depth in a prior corpse (legacy lore_known_monster_ids set).
        if corpse.monster_id in getattr(self.player, 'lore_known_monster_ids', set()):
            corpse.id_level = max(int(getattr(corpse, 'id_level', 0)), 4)
        self._start_corpse_identify(corpse, after_advance_turn=True)

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

    @staticmethod
    def _haggle_discount_for_chain(chain: int) -> int:
        """Return the percent discount granted by a haggle chain length.

        10% per chain step (i.e., per escalator tier reached), capped at 50%.
        Chain 0 -> 0%, chain 1 -> 10%, ..., chain 5 -> 50%, chain >5 -> 50%.
        """
        return min(max(0, chain) * 10, 50)

    @staticmethod
    def _apply_haggle_discount(price: int, chain: int) -> int:
        """Return the new price after applying the chain-based haggle discount."""
        discount = Game._haggle_discount_for_chain(chain)
        return max(1, int(price * (100 - discount) / 100))

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
                discount = self._haggle_discount_for_chain(chain)
                new_price = self._apply_haggle_discount(original_price, chain)
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
