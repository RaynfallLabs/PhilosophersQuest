class Player:
    BASE_HP = 20
    BASE_SP = 200
    BASE_MP = 10
    BASE_TIMER = 10      # seconds for quiz timer (legacy default)
    CARRY_BASE = 50
    CARRY_PER_STR = 5

    # Per-subject quiz timer tuning: (base_seconds, wis_scale_per_point)
    # base_seconds: fixed reading time floor for the category
    # wis_scale: seconds gained per point of WIS (e.g. 0.8 means WIS 15 adds 12s)
    SUBJECT_TIMER = {
        # (base_seconds, wis_scale) — timer = base + WIS * scale
        # Recalibrated 2026-05-11 for learning-focused gameplay: kids tune
        # out under time pressure when foundational concepts are missing,
        # so wonder subjects get scaffolded prompts that need room to read.
        # Math stays snappy because combat is the pressure point by design.
        'math':       ( 8, 0.8),   # combat — supposed to feel snappy
        'science':    (24, 1.2),   # concept questions with scaffolded setup
        'grammar':    (20, 1.0),   # sentence-level analysis
        'trivia':     (26, 1.2),   # general knowledge, varied lengths
        'geography':  (28, 1.2),   # moderate reading, detailed choices
        'history':    (34, 1.6),   # paragraph-length choices with scene-setting (+2 from playtest)
        'animal':     (34, 1.6),   # descriptive species questions (+2 from playtest)
        'ai':         (45, 1.5),   # technical concepts need room to teach (+5 from playtest)
        'philosophy': (50, 1.5),   # abstract reasoning + scaffolded definitions (+10 from playtest)
        'cooking':    (44, 1.6),   # full-sentence choices, recipe context
        'theology':   (50, 1.7),   # dense doctrinal text, scaffolded (+2)
        'economics':  (50, 1.7),   # detailed economic concepts with definitions (+2)
    }

    def __init__(self):
        # Primary stats
        self.STR = 10
        self.CON = 10
        self.DEX = 10
        self.INT = 10
        self.WIS = 10
        self.PER = 10

        # Resources
        self.max_hp = self.BASE_HP + self.CON
        self.hp = self.max_hp
        self.max_sp = self.BASE_SP + self.STR
        self.sp = self.max_sp
        self.max_mp = self.BASE_MP + self.INT
        self.mp = self.max_mp

        # Position on the dungeon grid
        self.x = 0
        self.y = 0

        # Equipment slots
        self.weapon = None          # melee weapon
        self.ranged_weapon = None   # ranged weapon (bows, crossbows)
        self.shield = None
        self.armor_slots = [None] * 8     # head, body, arms, hands, legs, feet, cloak, shirt
        self.accessory_slots = [None] * 4  # ring slots
        self.amulet_slot = None            # single amulet slot
        self.belt_slot   = None            # single belt slot (Megingjörð, Hippolyta's Girdle, Ariadne's Thread, etc.)

        # Inventory (list of item objects)
        self.inventory = []

        # Prayer system
        self.prayer_cooldown: int   = 0   # turns remaining until next prayer
        self.prayer_boon_count: int = 0   # permanent bonuses received (diminishing returns)

        # Recall Lore system
        self.recall_lore_cooldown: int = 0  # turns remaining until next lore recall

        # Hack Reality system
        self.hack_reality_cooldown: int = 0  # turns remaining until next hack
        self.hack_reality_count: int = 0     # permanent bonuses received (diminishing returns)
        self.hack_tiers_claimed: set[int] = set()  # XYZZY reward tiers already claimed (2-5 are once-only)

        # Special build flags
        self.immortal: bool = False         # Dad: cannot die
        self.qa_tools: bool = False         # Titivillus: Shift+I immortal toggle, Shift+W floor warp
        # Hero passives — set of strings checked at relevant hook sites in
        # combat.py / player.py / game_menus.py. Populated by the build's
        # entry in hero_specials.HERO_PASSIVES on game start.
        self.hero_passives: set[str] = set()
        # Hero active specials — list of dicts (one per active). Most heroes
        # have 0 or 1; Ash Williams has 3. Cooldowns keyed by special id.
        self.hero_specials: list[dict] = []
        self.hero_special_cooldowns: dict[str, int] = {}
        # Leonidas/Joan stand-AC and crit-buff bookkeeping
        self._stand_ac_bonus: int = 0
        self._stand_counter_pct: int = 0

        # Status effects: effect_id -> turns_remaining (or -1 for permanent)
        self.status_effects: dict[str, int] = {}
        # Fractional damage resistances: damage_type -> multiplier (0.0=immune,1.0=normal)
        self.resistances: dict[str, float] = {}
        # Flat damage resistances from chain-equip tier_bonuses + similar.
        # damage_type -> integer (subtracted from incoming damage at damage-calc site).
        self.damage_resistances: dict[str, int] = {}
        # Flat HP-regen bonus per tick (chain-equip / accessory passives).
        self.regen_bonus: int = 0
        # Item IDs the player has identified this run
        self.known_item_ids: set[str] = set()
        # Monster kinds the player has encountered (seen in FOV)
        self.known_monster_ids: set[str] = set()   # monsters seen (encyclopedia)
        self.lore_known_monster_ids: set[str] = set()  # monsters whose corpse has been studied (id_level >= 4)
        # Max id_level reached on EACH monster_id's corpse (any tier
        # 1..5). Used to spawn newly-dropped corpses at the same tier
        # the player has already learned, so identification carries
        # over between fresh kills. Per user feedback 2026-05-29:
        # "if I examine ONE rotting zombie corpse, all should be
        # identified at same tier upon discovery."
        self.corpse_id_level_known: dict[str, int] = {}
        self.lockpick_charges: int = 0             # charges from collected lockpicks
        # Spells learned from spellbooks: spell_id -> mp_cost
        self.known_spells: dict[str, int] = {}

        # Quirk system
        self.quirk_progress: dict  = {}    # event counters for quirk triggers
        self.unlocked_quirks: set  = set() # set of earned quirk IDs
        self.quiz_timer_bonuses: dict = {} # subject -> extra seconds bonus

        # Active power system (earned via quirks)
        self.power_cooldowns: dict = {}    # power_id -> turns until usable again (0 = ready)
        self.power_uses: dict = {}         # power_id -> uses remaining this run

        # Cooking HP balance: diminishing returns tracking
        self.cooking_hp_gained: int = 0    # total max HP gained from cooking (for softcap)
        self.deepest_floor_reached: int = 1  # drives floor-aware cooking softcap (synced from level_mgr)
        # Cooking STAT balance: per-stat lifetime gain from cooking, drives the
        # cooking-stat softcap (mirrors cooking_hp_gained). Without this, an
        # aggressive cook would balloon stats by +200+ over a run.
        self.cooking_stat_gained: dict[str, int] = {
            'STR': 0, 'CON': 0, 'DEX': 0, 'INT': 0, 'WIS': 0, 'PER': 0,
        }

        # Material discovery: tracks which materials have triggered their first-pickup chronicle.
        self.chronicle_seen_materials: set = set()

        # Philosopher career arc — counter of full identifies (chain >= 3 for uniques OR threshold success
        # for non-uniques OR corpse lore-id). Quick-BUC peeks do NOT count.
        self.total_identifies: int = 0
        # Career-threshold rewards already claimed (set of integers: 10, 25, 50, 100).
        self.philosopher_tier_claimed: set[int] = set()
        # Passive: at 100 IDs, auto-set buc_known=True on every new pickup.
        self.philosophers_mantle: bool = False
        # Mastery bonuses unlocked by chain-5 identify on uniques.
        # Key: item_id (e.g. 'soul_reaver'). Value: blessing dict {'kind', 'value', 'desc'}.
        self.unlocked_masteries: dict[str, dict] = {}
        # Carry-scope masteries currently applied to stats. Keyed by
        # item_id, value = (stat, amount) tuple of what's been added.
        # See refresh_carry_bonuses() for the apply/remove diff logic.
        # Used for items with mastery_blessing.scope='carry' (e.g.
        # Charmander Stuffie, Dreamspun Sketchbook) — bonus applies
        # only while the mastered item is in the player's inventory.
        self.active_carry_bonuses: dict[str, tuple] = {}
        # Class-level mastery for commons — mastering one Ring of Strength applies
        # to ALL rings of strength. Key: mastery_class slug (e.g. 'ring_of_strength').
        # Computed by class_masteries.get_mastery_class(item).
        self.unlocked_class_masteries: dict[str, dict] = {}
        # Per-family monster mastery — unlocked by chain-5 corpse-identify.
        # Key: family tag (e.g. 'dragon', 'undead'). Value: blessing dict.
        # See monster_classes.MONSTER_FAMILY_BLESSINGS for the schema.
        self.unlocked_monster_class_masteries: dict[str, dict] = {}
        # Item-class names the player has identified by their class (tier-1
        # of the escalator). Lets us name "Ring of Strength" for all variants
        # in the player's pack regardless of material.
        self.known_class_ids: set[str] = set()

    @property
    def equipped_accessories(self):
        """Every equipped accessory item: amulet (if any) + belt (if any)
        + all non-empty ring slots. The defensive getattr() lets older
        pickled saves that predate the belt slot still work."""
        items = []
        if self.amulet_slot is not None:
            items.append(self.amulet_slot)
        _belt = getattr(self, 'belt_slot', None)
        if _belt is not None:
            items.append(_belt)
        items.extend(r for r in self.accessory_slots if r is not None)
        return items

    # --- Resources ---

    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Apply damage after immunity and resistance checks. Returns actual damage."""
        from status_effects import DAMAGE_IMMUNITY, SHIELD_IMMUNITY
        # Full immunity via status effect
        immunity_effect = DAMAGE_IMMUNITY.get(damage_type)
        if immunity_effect and self.has_effect(immunity_effect):
            return 0
        # Shield effects also grant elemental immunity
        shield_effect = SHIELD_IMMUNITY.get(damage_type)
        if shield_effect and self.has_effect(shield_effect):
            return 0
        # Aiglos (Gil-galad's spear): wielder_fire_immunity blocks fire damage
        # while equipped — "Sauron's flame did nothing" (per audit 2026-05-30,
        # the flag was declared in JSON but had no consumer). Checks both
        # melee weapon and ranged_weapon slots.
        if damage_type == 'fire':
            for _slot in (self.weapon, getattr(self, 'ranged_weapon', None)):
                if _slot and getattr(_slot, 'wielder_fire_immunity', False):
                    return 0
        # Engine wave 3: generalized wielder_status_immunity. A weapon can
        # declare a list of damage types it blocks for the wielder. The
        # narrower wielder_fire_immunity flag stays for backward compat;
        # this gives the audit a clean extension point.
        for _slot in (self.weapon, getattr(self, 'ranged_weapon', None)):
            if _slot:
                _imm = getattr(_slot, 'wielder_status_immunity', None) or []
                if damage_type in _imm:
                    return 0

        # Flat damage reduction from chain-equip tier_bonuses (resistance_<type>).
        # Each "level" subtracts 1 damage of the matching type; clamped to >=0.
        flat_reduction = int(getattr(self, 'damage_resistances', {}).get(damage_type, 0))
        # Monster-family mastery: elemental blessing reduces fire/cold/lightning
        # damage by value as flat subtraction.
        if damage_type in ('fire', 'cold', 'lightning'):
            fams = getattr(self, 'unlocked_monster_class_masteries', {})
            elem = fams.get('elemental')
            if elem and elem.get('kind') == 'resist_elemental':
                flat_reduction += int(elem.get('value', 0))
        # Class-mastery flat reduction from equipped armor — physical-only.
        # CAPPED AT 1 total (not per-piece): with 8 armor slots, stacking
        # would let a fully-decked player approach physical immunity. The
        # bonus represents 'you've learned the geometry of armor,' not
        # eight independent achievements.
        if damage_type == 'physical':
            class_masteries = getattr(self, 'unlocked_class_masteries', {}) or {}
            if class_masteries:
                try:
                    from class_masteries import get_mastery_class
                    for armor_piece in getattr(self, 'armor_slots', []) or []:
                        if armor_piece:
                            m = class_masteries.get(get_mastery_class(armor_piece))
                            if m and m.get('kind') == 'class_armor_damage_reduction':
                                flat_reduction += int(m.get('value', 0))
                                break  # ONLY ONCE — cap at 1 total
                except Exception:
                    pass
        amount = max(0, amount - flat_reduction)

        # 'shielded' status halves physical damage (matches the description
        # at status_effects.py:82 and the Mage Armor / Magic Shield / Stoneskin
        # spell promises). Previously only monsters got the halving (combat.py)
        # — the player side was missing this branch. See bug-bash A7-4.
        # Round UP so a 1-damage hit still does 1.
        if damage_type == 'physical' and self.has_effect('shielded'):
            amount = (amount + 1) // 2

        # Fractional resistance: status/accessory effects x armor resistances
        resistance = self.resistances.get(damage_type, 1.0)
        resistance *= self.get_armor_resistance(damage_type)
        # Charmander Stuffie: 50% fire damage reduction while in inventory
        if damage_type == 'fire' and any(
                getattr(i, 'id', '') == 'charmander_stuffie' for i in self.inventory):
            resistance *= 0.5
        # Hero passive: Achilles' Demigod Hide — -25% physical damage.
        if damage_type == 'physical' and 'demigod_hide_25' in self.hero_passives:
            resistance *= 0.75
        # Hero passive: Witcher Mutations — +1 to all elemental resistances
        # (additive 0.1 multiplier reduction for known element types).
        if damage_type in ('fire', 'cold', 'lightning', 'acid', 'poison') and \
                'witcher_resists' in self.hero_passives:
            resistance *= 0.85
        actual = max(0, int(amount * resistance))
        self.hp = max(0, self.hp - actual)
        # Hero passive trigger: Ciri's Elder Blood — auto-teleport when HP drops <25%
        # once per floor (gated by the existing _elder_blood_escape_used floor flag).
        if 'elder_blood_escape' in self.hero_passives and \
                self.hp > 0 and self.hp <= self.max_hp * 0.25 and \
                not getattr(self, '_elder_blood_escape_used', False):
            self._elder_blood_escape_used = True
            # Signal via status_effects — main.py's tick will call _teleport_player.
            self.status_effects['_pending_elder_escape'] = 1
        # Chain-equip passive: free_escape_once_per_floor (Winged Sandals).
        # Auto-fires at HP <=25% if equipped + per-floor charge not yet spent.
        if self.hp > 0 and self.hp <= self.max_hp * 0.25:
            try:
                from chain_passives import consume_passive_charge
                if consume_passive_charge(self, 'free_escape_once_per_floor'):
                    self.status_effects['_pending_chain_escape'] = 1
            except ImportError:
                pass
        # Hero passive trigger: Boudicca's Vengeance Wakes — auto-berserk at <50%
        if 'vengeance_wakes' in self.hero_passives and \
                self.hp > 0 and self.hp <= self.max_hp * 0.5 and \
                self.status_effects.get('berserk', 0) <= 0:
            self.status_effects['berserk'] = max(self.status_effects.get('berserk', 0), 8)

        # Excalibur: cast_me_away. At HP <= 25%, the blade ONE-SHOT drains
        # its own enchant by 1 and grants the wielder life_save. One use
        # per run — _cast_me_away_used is a run-wide flag. Per audit
        # 2026-05-30 — the JSON flag was inert. Lore: "the blade keeps
        # Arthur alive once, then dims."
        if (self.hp > 0 and self.hp <= self.max_hp * 0.25
                and self.weapon
                and getattr(self.weapon, 'cast_me_away', False)
                and not getattr(self, '_cast_me_away_used', False)):
            self._cast_me_away_used = True
            self.weapon.enchant_bonus = max(0, self.weapon.enchant_bonus - 1)
            self.add_effect('life_save', -1)

        # Engine wave 3: combat-tracker hooks.
        # 1. Fail-not (cannot_miss_before_player_takes_damage) reads this
        #    flag — once the player has been hurt this combat, miss rolls
        #    return to normal. Cleared at the START of every melee /
        #    ranged attack (game_combat sets it False).
        if actual > 0:
            self._combat_player_taken_damage = True
        # 2. Skofnung's twelve berserkers wake when HP drops below 50%.
        #    Setting the pending flag here triggers a +chain rung on the
        #    NEXT successful attack. Reset by combat after consuming.
        if actual > 0 and self.hp > 0 and self.hp <= self.max_hp * 0.5 \
                and self.weapon \
                and int(getattr(self.weapon, 'chain_bonus_on_low_hp_window', 0) or 0) > 0:
            self._skofnung_low_hp_pending = True

        # Damage wakes a sleeping player
        if actual > 0 and 'sleeping' in self.status_effects:
            del self.status_effects['sleeping']

        return actual

    def is_dead(self) -> bool:
        if self.immortal and self.hp <= 0:
            self.hp = self.max_hp   # snap back to full health instantly
        # Rand's Heart: prevent death if equipped as amulet
        if self.hp <= 0 and not self.immortal:
            amulet = self.amulet_slot
            if amulet and getattr(amulet, 'id', '') == 'rands_heart':
                self.hp = self.max_hp
                self.mp = self.max_mp
                self.sp = self.max_sp
                # Clear all debuffs
                from status_effects import DEBUFFS
                for eff in list(self.status_effects.keys()):
                    if eff in DEBUFFS:
                        del self.status_effects[eff]
                # Unequip and consume the amulet
                old_fx = amulet.effects
                if 'status' in old_fx:
                    self.status_effects.pop(old_fx['status'], None)
                self.amulet_slot = None
                # Do NOT add back to inventory — it is consumed
                self._rands_heart_triggered = True  # flag for message in main.py
                return False
        return self.hp <= 0

    def spend_sp(self, amount: int) -> bool:
        if self.sp < amount:
            return False
        self.sp -= amount
        return True

    def restore_sp(self, amount: int):
        self.sp = min(self.max_sp, self.sp + amount)

    def restore_hp(self, amount: int) -> int:
        """Restore HP up to max. Returns actual HP gained (callers use the
        delta for messages like 'you heal N HP'). Per engine wave 3 (2026-05-30):
        heal_blocked status (Gae Dearg's wound) blocks the restore entirely."""
        if self.has_effect('heal_blocked'):
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    HP_PER_LEVEL = 0   # No auto max HP on stairs (HP comes from cooking)
    STAIR_REST_CAP_DESC = 0    # NO stair-rest HP healing on descent (damage accumulates)
    STAIR_REST_CAP_ASC  = 22   # max HP restored per stair on ascent

    def on_level_change(self, ascending: bool = False, first_visit: bool = True):
        """Called when player uses a staircase. Stair-rest healing only.

        No automatic max HP growth -- that comes from cooking compound recipes
        and high-tier single ingredient cooks (Q3+).
        Stair-rest heal scales with max HP; reduced on ascent (Death pursuit).
        Capped to prevent trivialising damage at very high max HP.

        first_visit: True only on the FIRST entry to this floor in the
        run. Revisits (going back and forth between floors via stairs)
        do NOT grant any rest-heal — otherwise a player can stair-stomp
        two adjacent floors to fully recover SP/MP for free, which is
        the exploit reported 2026-05-29.
        """
        if not first_visit:
            return
        if ascending:
            rest_heal = min(self.STAIR_REST_CAP_ASC,
                            max(self.HP_PER_LEVEL, int(self.max_hp * 0.04)))
        else:
            rest_heal = min(self.STAIR_REST_CAP_DESC,
                            max(self.HP_PER_LEVEL, int(self.max_hp * 0.05)))
        self.hp = min(self.hp + rest_heal, self.max_hp)
        self.sp = min(self.max_sp, self.sp + 15)
        mp_restore = max(2, self.INT // 5)
        self.restore_mp(mp_restore)

    # Floor-derived cooking softcap. Precomputed from
    # tools/balance/curve.py:cooking_softcap_max() — the SL-profile ceiling
    # (the diligent cook's reachable target). Replaces the broken flat 1000.
    # Index by deepest floor reached; values rise as the player descends.
    _COOKING_SOFTCAP_BY_FLOOR = (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,             # F0-F10
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,                # F11-F20
        7, 7, 7, 6, 6, 5, 5, 5, 4, 4,                # F21-F30
        3, 3, 3, 11, 11, 11, 10, 10, 9, 9,           # F31-F40
        9, 17, 17, 16, 16, 16, 15, 15, 24, 23,       # F41-F50
        23, 22, 22, 22, 21, 30, 30, 29, 29, 28,      # F51-F60
        37, 37, 36, 36, 35, 44, 44, 43, 43, 52,      # F61-F70
        51, 51, 50, 59, 59, 58, 58, 66, 66, 66,      # F71-F80
        74, 74, 74, 82, 82, 81, 90, 90, 98, 98,      # F81-F90
        97, 106, 106, 114, 114, 123, 122, 131, 130, 139,  # F91-F100
    )

    def cooking_softcap(self) -> int:
        """Current cooking HP softcap — function of deepest floor reached.
        Replaces the broken flat 1000. Diligent cooks at L100 cap near ~139 HP
        from cooking; that plus baseline ~50 = ~189 total (SL-profile target)."""
        idx = max(0, min(100, self.deepest_floor_reached))
        return max(1, self._COOKING_SOFTCAP_BY_FLOOR[idx])

    # Per-stat cooking softcap. Diligent cook at F100 caps near +15 per stat;
    # baseline starts at 10-18, so +15 from cooking = roughly 1.5x baseline
    # (matches the HP scaling philosophy of "1.5x baseline by deep descent").
    # Below F20 the cap is very tight to prevent early-game stat snowballing.
    _COOKING_STAT_SOFTCAP_BY_FLOOR = (
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,         # F0-F10  cap 1
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,            # F11-F20 cap 2
        3, 3, 3, 3, 3, 4, 4, 4, 4, 4,            # F21-F30 cap 3-4
        5, 5, 5, 5, 5, 6, 6, 6, 6, 6,            # F31-F40 cap 5-6
        7, 7, 7, 7, 7, 8, 8, 8, 8, 8,            # F41-F50 cap 7-8
        9, 9, 9, 9, 9, 10, 10, 10, 10, 10,       # F51-F60 cap 9-10
        11, 11, 11, 11, 11, 12, 12, 12, 12, 12,  # F61-F70 cap 11-12
        13, 13, 13, 13, 13, 14, 14, 14, 14, 14,  # F71-F80 cap 13-14
        14, 14, 14, 14, 14, 15, 15, 15, 15, 15,  # F81-F90 cap 14-15
        15, 15, 15, 15, 15, 15, 15, 15, 15, 15,  # F91-F100 cap 15
    )

    def cooking_stat_softcap(self) -> int:
        """Per-stat cooking lifetime cap. Capped at +15 per stat at endgame."""
        idx = max(0, min(100, self.deepest_floor_reached))
        return max(1, self._COOKING_STAT_SOFTCAP_BY_FLOOR[idx])

    def apply_cooking_stat_bonus(self, stat: str, amount: int) -> int:
        """Apply a cooked-food stat bonus with diminishing returns + per-stat
        floor-derived softcap. Returns the actual amount applied (may be 0).

        Below softcap: full bonus. Approaching softcap: scaled by remaining
        headroom. At/above softcap: 0 (hard cap, unlike HP which floors at 1
        — stats are too impactful to allow infinite drift).
        """
        if stat not in self.cooking_stat_gained or amount <= 0:
            return 0
        softcap = self.cooking_stat_softcap()
        gained = self.cooking_stat_gained[stat]
        if gained >= softcap:
            return 0
        # Diminishing return: scale linearly from full at gained=0 to 0 at cap.
        headroom = softcap - gained
        scaled = min(amount, headroom)
        # Floor at 1 IF the player would have got 1+ ungained — so a +1
        # cook isn't silently nullified mid-cap.
        applied = max(1, scaled) if amount >= 1 and headroom > 0 else 0
        applied = min(applied, headroom)
        self.cooking_stat_gained[stat] += applied
        self.apply_stat_bonus(stat, applied)
        return applied

    def increase_max_hp(self, amount: int, from_cooking: bool = False):
        """Permanently increase max HP. Also heals the amount.

        If from_cooking=True, applies diminishing returns: as total cooking HP
        gained approaches the floor-derived softcap, the bonus shrinks (floor 20%).
        Softcap rises as the player descends — early game cooks add little; deep
        descent unlocks the larger HP ceiling.
        """
        if from_cooking:
            softcap = self.cooking_softcap()
            cap_factor = max(0.20, 1.0 - self.cooking_hp_gained / softcap)
            amount = max(1, int(amount * cap_factor))
            self.cooking_hp_gained += amount
        self.max_hp += amount
        self.hp = min(self.hp + amount, self.max_hp)

    def restore_mp(self, amount: int):
        self.mp = min(self.max_mp, self.mp + amount)

    # --- Status effects ---

    def has_effect(self, name: str) -> bool:
        """True if the effect is active (any non-zero value)."""
        return self.status_effects.get(name, 0) != 0

    def add_effect(self, name: str, duration: int) -> bool:
        """Apply effect via the status_effects module. Returns True if applied."""
        from status_effects import apply_effect, DEBUFFS
        # Hermes quirk: double haste duration
        if name == 'hasted' and duration > 0:
            if getattr(self, 'quirk_progress', {}).get('hermes_active'):
                duration = duration * 2
        # Perseus quirk: halve incoming debuff durations
        if name in DEBUFFS and duration > 0:
            if getattr(self, 'quirk_progress', {}).get('perseus_active'):
                duration = max(1, duration // 2)
        # Hero passive: Will to Power — immune to fear/charm when below 30% HP.
        if name in ('feared', 'charmed') and 'will_to_power' in self.hero_passives \
                and self.max_hp > 0 and self.hp <= self.max_hp * 0.3:
            return False
        # Hero buff: fear_immune (Ash's berserk chain >= 3) — block fear application.
        if name == 'feared' and self.status_effects.get('fear_immune', 0) > 0:
            return False
        # Monster-family mastery: fey blessing reduces charm/illusion durations.
        # Aberration blessing reduces mind-effect durations (charmed/confused).
        fams = getattr(self, 'unlocked_monster_class_masteries', {})
        if duration > 0:
            if name == 'charmed' and fams.get('fey', {}).get('kind') == 'resist_charm':
                duration = max(1, duration // 2)
            if name in ('charmed', 'confused') and fams.get('aberration', {}).get('value'):
                duration = max(1, duration - int(fams['aberration']['value']))
        # class_acc_quirk mastery: matching ring class extends its signature
        # buff duration. Applies for non-permanent (>0) buffs only — permanent
        # ring statuses already last forever.
        if duration > 0:
            _CLASS_QUIRK_EFFECT_MAP = {
                'speed_extend':     ('hasted',       ('ring_of_speed', 'amulet_of_speed')),
                'invis_extend':     ('invisible',    ('ring_of_invisibility', 'amulet_of_invisibility')),
                'levitate_extend':  ('levitating',   ('ring_of_levitation', 'amulet_of_levitation')),
                'displace_extend':  ('displacement', ('ring_of_displacement', 'amulet_of_displacement')),
            }
            for _cls_id, _b in getattr(self, 'unlocked_class_masteries', {}).items():
                if _b.get('kind') != 'class_acc_quirk':
                    continue
                _slug = _b.get('value', '')
                _mapped = _CLASS_QUIRK_EFFECT_MAP.get(_slug)
                if _mapped and name == _mapped[0] and _cls_id in _mapped[1]:
                    duration = int(duration) + 4
        # class_acc_buff_duration_bonus mastery (default fallback for
        # accessories): +N turns to any buff added while a mastered ring/
        # amulet of that class is equipped.
        if duration > 0:
            try:
                from class_masteries import get_mastery_class as _gmc_b
            except ImportError:
                _gmc_b = None
            if _gmc_b is not None:
                _bonus = 0
                for _acc in self.equipped_accessories:
                    _m = self.unlocked_class_masteries.get(_gmc_b(_acc))
                    if _m and _m.get('kind') == 'class_acc_buff_duration_bonus':
                        _bonus += int(_m.get('value', 0))
                if _bonus > 0:
                    duration = int(duration) + _bonus
        return apply_effect(self, name, duration)

    def tick_effects(self) -> list:
        """Process one turn for all active effects. Returns list of (msg, type) pairs."""
        from status_effects import tick_all
        return tick_all(self)

    # --- Derived stats ---

    def get_ac(self) -> int:
        """Armor class -- lower is better (harder for monsters to hit).
        Base 10, reduced by DEX modifier, armor ac_bonus + enchant_bonus, shield,
        and status effects like invisibility."""
        dex_mod = (self.DEX - 10) // 2
        armor_bonus = sum(
            getattr(s, 'ac_bonus', 0) + getattr(s, 'enchant_bonus', 0)
            for s in self.armor_slots if s is not None
        )
        shield_bonus = (
            getattr(self.shield, 'ac_bonus', 0) + getattr(self.shield, 'enchant_bonus', 0)
            if self.shield else 0
        )
        # Class-mastery: +1 AC if shield's class has been mastered.
        if self.shield:
            try:
                from class_masteries import get_mastery_class
                cls_m = (getattr(self, 'unlocked_class_masteries', {}) or {}).get(
                    get_mastery_class(self.shield))
                if cls_m and cls_m.get('kind') == 'class_shield_ac_bonus':
                    shield_bonus += int(cls_m.get('value', 0))
            except Exception:
                pass
        # Blessed armor/shield: +1 AC per blessed piece
        blessed_bonus = sum(
            1 for s in self.armor_slots
            if s is not None and getattr(s, 'buc', 'uncursed') == 'blessed'
        )
        if self.shield and getattr(self.shield, 'buc', 'uncursed') == 'blessed':
            blessed_bonus += 1
        # Invisibility: harder to hit -> lowers AC by 2
        invisible_bonus = 2 if self.has_effect('invisible') else 0
        # Shielded status effect (from wand of shielding): -2 AC
        shield_effect   = 2 if self.has_effect('shielded') else 0
        acc_bonus = getattr(self, '_accessory_ac_bonus', 0)
        surr_bonus = getattr(self, '_surrounded_ac_bonus', 0)
        # armor_ac_bonus mastery (e.g. Greater Aegis of Athena) — applies for each mastered piece worn
        mastery_ac = 0
        for s in (list(self.armor_slots) + [self.shield]):
            if s is None:
                continue
            m = self.unlocked_masteries.get(getattr(s, 'id', None))
            if m and m.get('kind') == 'armor_ac_bonus':
                mastery_ac += int(m.get('value', 0))
        # class_acc_ac_bonus mastery (Ring of Protection class): +N AC.
        # CAPPED ONCE PER MASTERED CLASS (not per equipped ring) so that
        # wearing 4 Rings of Protection doesn't multiply the mastery bonus.
        # The base ring AC already stacks per-piece; mastery is a one-time
        # 'you understand this class' nod.
        try:
            from class_masteries import get_mastery_class as _gmc_ac
        except ImportError:
            _gmc_ac = None
        if _gmc_ac is not None:
            credited_classes = set()
            for s in self.equipped_accessories:
                cls_id = _gmc_ac(s)
                if cls_id in credited_classes:
                    continue
                m = self.unlocked_class_masteries.get(cls_id)
                if m and m.get('kind') == 'class_acc_ac_bonus':
                    mastery_ac += int(m.get('value', 0))
                    credited_classes.add(cls_id)
        # Leonidas Spartan Stand: +N AC while the stand_ac status holds.
        stand_ac = 0
        if self.status_effects.get('stand_ac', 0) > 0:
            stand_ac = int(getattr(self, '_stand_ac_bonus', 0))
        # Quarterstaff defensive_parry chain-5 effect: +2 AC for 2 turns
        parry_ac = 2 if self.status_effects.get('parry_armed', 0) > 0 else 0
        # ------ Engine wave 5: flat-armor AC procs ------
        # Hannibal cuirass (cannae_encirclement): +2 AC when surrounded by 3+.
        # Boundary guardian (Mars): +1 AC in a room near a door.
        # Wallace brigandine (guerrilla_terrain): +2 AC in 1-tile-wide corridors.
        # Scale of Dilmun (paradise_water): +water_tile_ac_bonus AC on water.
        # The terrain caches (_armor_proc_adj_enemies, _armor_proc_near_door,
        # _armor_proc_in_corridor, _armor_proc_on_water) are refreshed each turn
        # in main._advance_turn so get_ac stays O(1).
        try:
            from armor_procs import player_has_armor_proc as _pap_ac, proc_value as _pv_ac
        except ImportError:
            _pap_ac = None
            _pv_ac = None
        armor_proc_ac = 0
        if _pap_ac is not None:
            if _pap_ac(self, 'cannae_encirclement') and \
                    int(getattr(self, '_armor_proc_adj_enemies', 0)) >= 3:
                armor_proc_ac += 2
            if _pap_ac(self, 'boundary_guardian') and \
                    getattr(self, '_armor_proc_near_door', False):
                armor_proc_ac += 1
            if _pap_ac(self, 'guerrilla_terrain') and \
                    getattr(self, '_armor_proc_in_corridor', False):
                armor_proc_ac += 2
            if getattr(self, '_armor_proc_on_water', False):
                armor_proc_ac += int(_pv_ac(self, 'water_tile_ac_bonus') or 0)
        return 10 - dex_mod - armor_bonus - shield_bonus - blessed_bonus - invisible_bonus - shield_effect - acc_bonus - surr_bonus - mastery_ac - stand_ac - parry_ac - armor_proc_ac

    def get_armor_resistance(self, damage_type: str) -> float:
        """Combined damage resistance multiplier from all equipped armor/shield."""
        mult = 1.0
        for slot in self.armor_slots:
            if slot and hasattr(slot, 'damage_resistances'):
                mult *= slot.damage_resistances.get(damage_type, 1.0)
            if slot:
                # armor_resist_bonus mastery: reduce incoming damage of `type` by `pct`
                m = self.unlocked_masteries.get(getattr(slot, 'id', None))
                if m and m.get('kind') == 'armor_resist_bonus':
                    v = m.get('value') or {}
                    t = v.get('type')
                    pct = float(v.get('pct', 0)) / 100.0
                    if t == damage_type or t == 'all_elemental' and damage_type in (
                            'fire', 'cold', 'lightning', 'acid', 'poison'):
                        mult *= max(0.0, 1.0 - pct)
        if self.shield and hasattr(self.shield, 'damage_resistances'):
            mult *= self.shield.damage_resistances.get(damage_type, 1.0)
        # class_acc_resist_bonus mastery: matching equipped resist-ring applies
        # an extra fractional reduction. CAPPED ONCE PER MASTERED CLASS so
        # wearing 4 Rings of Fire Resistance doesn't multiply the mastery
        # contribution. The base ring resistance still stacks per-piece.
        try:
            from class_masteries import get_mastery_class as _gmc_r
        except ImportError:
            _gmc_r = None
        if _gmc_r is not None:
            credited_resist = set()
            for acc in self.equipped_accessories:
                cid = _gmc_r(acc)
                if cid in credited_resist:
                    continue
                m = self.unlocked_class_masteries.get(cid)
                if not m or m.get('kind') != 'class_acc_resist_bonus':
                    continue
                v = m.get('value') or {}
                t = v.get('type')
                amt = float(v.get('amount', 0))
                if t == damage_type and amt > 0:
                    mult *= max(0.0, 1.0 - amt)
                    credited_resist.add(cid)
        return mult

    def get_sight_radius(self) -> int:
        """Sight radius in tiles. Blindfold = 0 (total darkness), blindness = 1."""
        # Blindfold equipped in head slot: total darkness (can't see anything)
        head = self.armor_slots[0] if self.armor_slots else None
        if head and getattr(head, 'id', '') == 'blindfold':
            return 0
        if self.has_effect('blinded'):
            return 1
        radius = max(3, self.PER // 2)
        if self.has_effect('dark_vision'):
            radius += 4
        if self.has_effect('truesight'):
            radius += 2
        # Engine wave 3: equipped_light_aura on a wielded weapon (Prometheus
        # Torch, etc.) extends sight while held. Stacks weapon + ranged_weapon.
        for _slot in (self.weapon, getattr(self, 'ranged_weapon', None)):
            if _slot:
                radius += int(getattr(_slot, 'equipped_light_aura', 0) or 0)
        return radius

    def get_quiz_timer(self, subject: str = 'math') -> int:
        """Base quiz timer in seconds (before status modifiers).
        Uses per-subject base + WIS scaling so text-heavy categories
        give enough reading time without making flashcard math trivial.

        Floor of 5 seconds: at very low WIS (e.g. after cursed-drain-wis
        potions or stacked disease ticks), the unfloored formula can
        return 0 or negative, making combat unwinnable. See bug-bash A7-1.
        """
        base, wis_scale = self.SUBJECT_TIMER.get(subject, (10, 1.0))
        return max(5, round(base + self.WIS * wis_scale))

    def get_quiz_timer_modifier(self) -> float:
        """Multiplier applied to quiz timer based on active effects.
        Floor of 0.40x prevents stacked debuffs from making quizzes unsolvable."""
        mod = 1.0
        if self.has_effect('confused'):
            mod *= 0.55
        if self.has_effect('stunned'):
            mod *= 0.75
        if self.has_effect('blinded'):
            mod *= 0.70
        if self.has_effect('hallucinating'):
            mod *= 0.80
        if self.has_effect('hasted'):
            mod *= 1.25
        if self.has_effect('blessed'):
            mod *= 1.25
        return round(max(0.40, mod), 2)

    def get_int_quiz_bonus(self) -> int:
        """Extra quiz seconds for magic subjects (science/grammar/philosophy). +0.5s per INT above 10."""
        return max(0, self.INT - 10) // 2

    def get_quiz_extra_seconds(self, subject: str) -> int:
        """Extra quiz seconds from earned quirks and equipment."""
        base = getattr(self, 'quiz_timer_bonuses', {}).get(subject, 0)
        # Ancile shield: bonus seconds on all quizzes
        shld = getattr(self, 'shield', None)
        if shld and getattr(shld, 'quiz_timer_bonus', 0) > 0:
            base += shld.quiz_timer_bonus
        return base

    def get_class_mastery_regen_bonus(self) -> int:
        """Sum of class_acc_regen_bonus mastery values for currently equipped
        ring/amulet of regeneration. Returns extra HP per regen tick.

        Wired at the regen-tick site (main._tick_hp_regen) so the bonus only
        fires while the regen accessory is worn — matches the intent of the
        blessing description (per-ring class).
        """
        # CAPPED ONCE PER MASTERED CLASS — wearing 4 Rings of Regeneration
        # doesn't multiply the per-tick regen mastery bonus.
        try:
            from class_masteries import get_mastery_class as _gmc_re
        except ImportError:
            return 0
        bonus = 0
        credited = set()
        for acc in self.equipped_accessories:
            cid = _gmc_re(acc)
            if cid in credited:
                continue
            m = self.unlocked_class_masteries.get(cid)
            if m and m.get('kind') == 'class_acc_regen_bonus':
                bonus += int(m.get('value', 0))
                credited.add(cid)
        return bonus

    def get_class_mastery_sp_burn_factor(self) -> float:
        """Fractional reduction to SP drain rate from class_acc_sp_burn_bonus.

        Returns 0.0 by default; e.g. 0.10 means SP drains 10% slower while a
        mastered ring/amulet of sustenance is equipped. Wired at the SP-tick
        site (main._tick_sp) — see drain_interval scaling.

        CAPPED ONCE PER MASTERED CLASS.
        """
        try:
            from class_masteries import get_mastery_class as _gmc_sp
        except ImportError:
            return 0.0
        factor = 0.0
        credited = set()
        for acc in self.equipped_accessories:
            cid = _gmc_sp(acc)
            if cid in credited:
                continue
            m = self.unlocked_class_masteries.get(cid)
            if m and m.get('kind') == 'class_acc_sp_burn_bonus':
                factor += float(m.get('value', 0.0))
                credited.add(cid)
        return factor

    def get_class_mastery_passive_radius_bonus(self, class_slug: str) -> int:
        """Extra search/warning/clairvoyance radius from class_acc_passive_radius.

        class_slug is one of: 'searching', 'warning', 'clairvoyance',
        'telepathy'. Returns ONE bonus per matching mastered class — wearing
        two Rings of Searching does NOT double the radius.
        """
        try:
            from class_masteries import get_mastery_class as _gmc_pr
        except ImportError:
            return 0
        bonus = 0
        ring_id = f'ring_of_{class_slug}'
        amu_id = f'amulet_of_{class_slug}'
        credited = set()
        for acc in self.equipped_accessories:
            cid = _gmc_pr(acc)
            if cid not in (ring_id, amu_id):
                continue
            if cid in credited:
                continue
            m = self.unlocked_class_masteries.get(cid)
            if m and m.get('kind') == 'class_acc_passive_radius':
                bonus += int(m.get('value', 0))
                credited.add(cid)
        return bonus

    def get_carry_limit(self) -> int:
        return self.CARRY_BASE + self.STR * self.CARRY_PER_STR

    def get_current_weight(self) -> float:
        total = 0.0
        for item in self.inventory:
            count = getattr(item, 'count', 1)
            total += getattr(item, 'weight', 0) * count
        return total

    # --- Inventory ---

    def add_to_inventory(self, item) -> bool:
        from items import Item
        count = getattr(item, 'count', 1)
        item_weight = getattr(item, 'weight', 0) * count
        if item_weight + self.get_current_weight() > self.get_carry_limit():
            return False
        # Stack identical items for stackable types (same id).
        # BUC rule: only merge stacks whose UNDERLYING buc value matches —
        # whether or not the player has identified it yet. Previously the
        # code allowed hidden-buc stacks to merge across underlying values,
        # silently dropping the incoming item's BUC effect when the kid
        # later drank/read/threw from the stack. See bug-bash A7-5.
        if isinstance(item, Item._STACKABLE_CLASSES):
            for existing in self.inventory:
                if existing.id != item.id:
                    continue
                if getattr(existing, 'buc', 'uncursed') != getattr(item, 'buc', 'uncursed'):
                    continue  # different underlying BUC: keep stacks separate
                # Merge buc_known monotonically — if EITHER known, the stack
                # is known (because we just confirmed the underlying values
                # are identical).
                if getattr(item, 'buc_known', False):
                    existing.buc_known = True
                existing.count = getattr(existing, 'count', 1) + getattr(item, 'count', 1)
                return True
        self.inventory.append(item)
        # Keep inventory sorted alphabetically by item name
        self.inventory.sort(key=lambda i: i.name.lower())
        # Sync carry-scope mastery bonuses (Charmander Stuffie etc.)
        self.refresh_carry_bonuses()
        return True

    def remove_from_inventory(self, item) -> bool:
        if item in self.inventory:
            if getattr(item, 'count', 1) > 1:
                item.count -= 1
                return True
            self.inventory.remove(item)
            # Sync carry-scope mastery bonuses (bonus removed if the
            # dropped item was a Charmander Stuffie etc.)
            self.refresh_carry_bonuses()
            return True
        return False

    # --- Stat bonuses ---

    def apply_stat_bonus(self, stat: str, amount: int):
        """Permanently change a stat and update derived maximums."""
        if stat == 'AC':
            # AC is computed, not stored directly — accumulate in a bonus field
            self._accessory_ac_bonus = getattr(self, '_accessory_ac_bonus', 0) + amount
            return
        setattr(self, stat, getattr(self, stat) + amount)
        if stat == 'CON':
            self.max_hp += amount   # preserve level scaling
            self.hp = min(self.hp, self.max_hp)
        elif stat == 'STR':
            self.max_sp += amount
        elif stat == 'INT':
            self.max_mp += amount
            self.mp = min(self.mp, self.max_mp)

    def refresh_carry_bonuses(self):
        """Sync carry-scope mastery bonuses with current inventory.

        For each unlocked mastery whose `scope == 'carry'`, applies its
        bonus iff the corresponding item is currently in inventory, and
        removes it otherwise. Idempotent — diffs against
        `self.active_carry_bonuses` so calling repeatedly has no effect.

        Use case: Charmander Stuffie / Dreamspun Sketchbook — items
        you carry as keepsakes; the bonus applies as long as you
        haven't dropped them.
        """
        # Defensive default for old saves
        if not hasattr(self, 'active_carry_bonuses') or self.active_carry_bonuses is None:
            self.active_carry_bonuses = {}
        # What SHOULD be applied right now
        inv_ids = {getattr(i, 'id', None) for i in self.inventory}
        desired: dict[str, tuple] = {}
        for item_id, mastery in self.unlocked_masteries.items():
            if not isinstance(mastery, dict):
                continue
            if mastery.get('scope') != 'carry':
                continue
            if item_id not in inv_ids:
                continue
            # Currently only stat_bonus kinds are supported on carry
            kind = mastery.get('kind')
            if kind not in ('accessory_stat_bonus',):
                continue
            v = mastery.get('value') or {}
            stat = v.get('stat')
            amount = int(v.get('amount', 0))
            if stat and amount:
                desired[item_id] = (stat, amount)
        # Apply newly-active (in desired but not yet in active)
        for item_id, (stat, amount) in desired.items():
            if item_id in self.active_carry_bonuses:
                continue
            self.apply_stat_bonus(stat, amount)
            self.active_carry_bonuses[item_id] = (stat, amount)
        # Remove newly-inactive (in active but no longer desired)
        for item_id in list(self.active_carry_bonuses.keys()):
            if item_id in desired:
                continue
            stat, amount = self.active_carry_bonuses.pop(item_id)
            self.apply_stat_bonus(stat, -amount)

    # --- Equipment ---

    def get_equipped_items(self) -> dict:
        from items import ARMOR_SLOTS
        slots = {'weapon': self.weapon, 'ranged_weapon': self.ranged_weapon,
                 'shield': self.shield}
        for i, name in enumerate(ARMOR_SLOTS):
            slots[name] = self.armor_slots[i]
        for i, item in enumerate(self.accessory_slots):
            slots[f'ring_{i+1}'] = item
        slots['amulet'] = self.amulet_slot
        slots['belt']   = getattr(self, 'belt_slot', None)
        return slots

    def get_inventory_display(self) -> list:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        return [(letters[i], item) for i, item in enumerate(self.inventory[:26])]

    def can_equip_shield(self) -> bool:
        """Returns False when a two-handed weapon is equipped."""
        return not (self.weapon and getattr(self.weapon, 'two_handed', False))

    def try_unequip_slot(self, slot_item) -> tuple[bool, str]:
        """Attempt to remove an equipped item. Returns (success, message).
        Fails if the item is cursed OR has the selects_wielder flag
        (Stormbringer — the runesword has chosen you)."""
        if slot_item and getattr(slot_item, 'cursed', False):
            return False, f"The {slot_item.name} is welded to you!"
        # Stormbringer: selects_wielder — refuses to be put down. Per audit
        # 2026-05-30 — JSON flag was inert.
        if slot_item and getattr(slot_item, 'selects_wielder', False):
            return False, f"The {slot_item.name} clings to your hand. It will not be put down."
        return True, ""

    # ------------------------------------------------------------------
    # Weapon-passive hooks (engine wave 2026-05-30).
    # Per the unique-weapon audit, several flags expect to apply WHILE the
    # weapon is equipped (vigilance_aware +PER, cursed_lineage stat ledger)
    # or fire ONCE on first equip (prophecy_blade declaration). These
    # helpers wrap the bumps/declarations and are called from _apply_equip
    # below.
    # ------------------------------------------------------------------

    def _apply_weapon_passives(self, weapon) -> None:
        """Fire weapon-equip-side passives when a weapon is put on."""
        if weapon is None:
            return
        # Hofud: vigilance_aware — +2 PER while equipped.
        if getattr(weapon, 'vigilance_aware', False):
            self.PER += 2
        # Pelops Sword: cursed_lineage — -1 STR + 2 max HP on equip.
        # Per descent: handled separately in main._change_level via the
        # weapon-aware House-of-Atreus event hook.
        if getattr(weapon, 'cursed_lineage', False):
            self.STR = max(1, self.STR - 1)
            self.max_hp += 2
            self.hp = min(self.max_hp, self.hp + 2)
        # Akinakes of Acrisius: prophecy_blade — at first equip declares
        # a random monster tag/class. Stored on the player as a run-wide
        # buff lookup; combat.player_attack reads it for the +50% mult.
        if getattr(weapon, 'prophecy_blade', False) and \
                getattr(self, '_prophecy_target_tag', None) is None:
            import random as _rng
            # Tag pool: the seven recurring monster archetypes Akinakes
            # could have prophesied. Picked once per run, persists across
            # equip/unequip cycles so the player can't reroll by toggling.
            self._prophecy_target_tag = _rng.choice([
                'humanoid', 'undead', 'demon', 'beast',
                'dragon', 'fey', 'aberration',
            ])

    def _remove_weapon_passives(self, weapon) -> None:
        """Reverse weapon-equip-side passives when a weapon is taken off."""
        if weapon is None:
            return
        if getattr(weapon, 'vigilance_aware', False):
            self.PER = max(1, self.PER - 2)
        if getattr(weapon, 'cursed_lineage', False):
            self.STR += 1
            self.max_hp = max(1, self.max_hp - 2)
            self.hp = min(self.hp, self.max_hp)
        # prophecy_blade declaration is run-permanent — does NOT reverse.

    def _apply_equip(self, item):
        from items import Weapon, Armor, Shield, Accessory, ARMOR_SLOTS
        if isinstance(item, Weapon):
            is_ranged = getattr(item, 'requires_ammo', None) is not None
            if is_ranged:
                # --- Ranged weapon slot ---
                if self.ranged_weapon:
                    ok, msg = self.try_unequip_slot(self.ranged_weapon)
                    if not ok:
                        return
                    old_status = getattr(self.ranged_weapon, 'on_equip_status', '')
                    if old_status:
                        self.status_effects.pop(old_status, None)
                    self._remove_weapon_passives(self.ranged_weapon)
                    self.inventory.append(self.ranged_weapon)
                self.ranged_weapon = item
                new_status = getattr(item, 'on_equip_status', '')
                if new_status:
                    self.add_effect(new_status, -1)
                self._apply_weapon_passives(item)
            else:
                # --- Melee weapon slot ---
                if self.weapon:
                    ok, msg = self.try_unequip_slot(self.weapon)
                    if not ok:
                        return  # cursed weapon blocks swap
                    old_status = getattr(self.weapon, 'on_equip_status', '')
                    if old_status:
                        self.status_effects.pop(old_status, None)
                    self._remove_weapon_passives(self.weapon)
                    self.inventory.append(self.weapon)
                # Unequip shield if switching to 2H melee
                if getattr(item, 'two_handed', False) and self.shield:
                    ok, msg = self.try_unequip_slot(self.shield)
                    if not ok:
                        return
                    self.inventory.append(self.shield)
                    self.shield = None
                self.weapon = item
                new_status = getattr(item, 'on_equip_status', '')
                if new_status:
                    self.add_effect(new_status, -1)
                self._apply_weapon_passives(item)
        elif isinstance(item, Armor):
            idx = ARMOR_SLOTS.index(item.slot) if item.slot in ARMOR_SLOTS else 0
            old = self.armor_slots[idx]
            ok, _ = self.try_unequip_slot(old)
            if not ok:
                return
            if old:
                # Remove old armor's on-equip status
                old_status = getattr(old, 'on_equip_status', '')
                if old_status:
                    self.status_effects.pop(old_status, None)
                # Mantle of Elijah (prophets_passing): unequip drops the +max_MP bonus.
                if getattr(old, 'prophets_passing', False):
                    _drop = int(getattr(old, '_prophets_mp_grant', 0) or 0)
                    if _drop > 0:
                        self.max_mp = max(0, self.max_mp - _drop)
                        self.mp = min(self.mp, self.max_mp)
                        old._prophets_mp_grant = 0
                self.inventory.append(old)
            self.armor_slots[idx] = item
            # Grant new armor's on-equip status
            new_status = getattr(item, 'on_equip_status', '')
            if new_status:
                self.add_effect(new_status, -1)
            # Mantle of Elijah (prophets_passing): the "office passes" — +3 max MP
            # while equipped. Lore: the wisdom of the prophet's school carries.
            if getattr(item, 'prophets_passing', False):
                _grant = 3
                self.max_mp += _grant
                self.mp = min(self.mp + _grant, self.max_mp)
                item._prophets_mp_grant = _grant
        elif isinstance(item, Shield):
            if not self.can_equip_shield():
                return
            old = self.shield
            ok, _ = self.try_unequip_slot(old)
            if not ok:
                return
            if old:
                old_status = getattr(old, 'on_equip_status', '')
                if old_status:
                    self.status_effects.pop(old_status, None)
                self.inventory.append(old)
            self.shield = item
            new_status = getattr(item, 'on_equip_status', '')
            if new_status:
                self.add_effect(new_status, -1)
        elif isinstance(item, Accessory):
            if getattr(item, 'slot', 'ring') == 'none':
                return  # carry-only items cannot be equipped
            if getattr(item, 'slot', 'ring') == 'amulet':
                # Swap out existing amulet if present
                old = self.amulet_slot
                if old:
                    ok, msg = self.try_unequip_slot(old)
                    if not ok:
                        return
                    self.inventory.append(old)
                    # Reverse old amulet's effects
                    old_fx = old.effects
                    if 'status' in old_fx:
                        self.status_effects.pop(old_fx['status'], None)
                    if 'stat' in old_fx:
                        self.apply_stat_bonus(old_fx['stat'], -old_fx.get('amount', 0))
                    if 'stat2' in old_fx:
                        self.apply_stat_bonus(old_fx['stat2'], -old_fx.get('amount2', 0))
                self.amulet_slot = item
            elif getattr(item, 'slot', 'ring') == 'belt':
                # Belt slot — single-item, mirrors amulet handling.
                # Used by Megingjörð, Girdle of Hippolyta, Ariadne's
                # Thread, Rope of Izanagi, Anansi's Thread.
                if not hasattr(self, 'belt_slot'):
                    self.belt_slot = None  # backfill for older saves
                old = self.belt_slot
                if old:
                    ok, msg = self.try_unequip_slot(old)
                    if not ok:
                        return
                    self.inventory.append(old)
                    old_fx = old.effects
                    if 'status' in old_fx:
                        self.status_effects.pop(old_fx['status'], None)
                    if 'stat' in old_fx:
                        self.apply_stat_bonus(old_fx['stat'], -old_fx.get('amount', 0))
                    if 'stat2' in old_fx:
                        self.apply_stat_bonus(old_fx['stat2'], -old_fx.get('amount2', 0))
                self.belt_slot = item
            else:
                # Find first empty ring slot. If none free, bail out — the
                # game-level _equip_accessory blocks this, but harden here too
                # so direct callers don't silently double-apply effects.
                slot_idx = next(
                    (i for i, s in enumerate(self.accessory_slots) if s is None),
                    None,
                )
                if slot_idx is None:
                    return  # all rings full — refuse silently
                self.accessory_slots[slot_idx] = item
            # Apply the accessory's effect permanently
            fx = item.effects
            if 'status' in fx:
                self.add_effect(fx['status'], fx.get('duration', -1))
            if 'stat' in fx:
                self.apply_stat_bonus(fx['stat'], fx.get('amount', 0))
            if 'stat2' in fx:
                self.apply_stat_bonus(fx['stat2'], fx.get('amount2', 0))
        # Re-sort inventory after any equipment swap that returned items
        self.inventory.sort(key=lambda i: i.name.lower())
