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
        'math':       ( 8, 0.8),   # flashcard arithmetic — fast reads
        'science':    (10, 1.0),   # short concept questions
        'grammar':    (10, 1.0),   # short sentence questions
        'trivia':     (12, 1.0),   # general knowledge, slightly longer
        'geography':  (12, 1.0),   # moderate reading, some long choices
        'history':    (14, 1.2),   # paragraph-length context
        'animal':     (14, 1.2),   # descriptive species questions
        'ai':         (16, 1.2),   # technical concepts, longer choices
        'philosophy': (16, 1.2),   # abstract reasoning, dense text
        'cooking':    (18, 1.4),   # full-sentence choices, recipe context
        'theology':   (20, 1.4),   # dense doctrinal text, long choices
        'economics':  (20, 1.4),   # heaviest reading burden
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

        # Status effects: effect_id -> turns_remaining (or -1 for permanent)
        self.status_effects: dict[str, int] = {}
        # Fractional damage resistances: damage_type -> multiplier (0.0=immune,1.0=normal)
        self.resistances: dict[str, float] = {}
        # Item IDs the player has identified this run
        self.known_item_ids: set[str] = set()
        # Monster kinds the player has encountered (seen in FOV)
        self.known_monster_ids: set[str] = set()   # monsters seen (encyclopedia)
        self.lore_known_monster_ids: set[str] = set()  # monsters whose corpse has been studied
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

        # Fractional resistance: status/accessory effects x armor resistances
        resistance = self.resistances.get(damage_type, 1.0)
        resistance *= self.get_armor_resistance(damage_type)
        # Charmander Stuffie: 50% fire damage reduction while in inventory
        if damage_type == 'fire' and any(
                getattr(i, 'id', '') == 'charmander_stuffie' for i in self.inventory):
            resistance *= 0.5
        actual = max(0, int(amount * resistance))
        self.hp = max(0, self.hp - actual)

        # Damage wakes a sleeping player
        if actual > 0 and 'sleeping' in self.status_effects:
            del self.status_effects['sleeping']

        return actual

    def is_dead(self) -> bool:
        if self.immortal and self.hp <= 0:
            self.hp = self.max_hp   # snap back to full health instantly
        return self.hp <= 0

    def spend_sp(self, amount: int) -> bool:
        if self.sp < amount:
            return False
        self.sp -= amount
        return True

    def restore_sp(self, amount: int):
        self.sp = min(self.max_sp, self.sp + amount)

    def restore_hp(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    HP_PER_LEVEL = 0   # No auto max HP on stairs (HP comes from cooking)
    STAIR_REST_CAP_DESC = 0    # NO stair-rest HP healing on descent (damage accumulates)
    STAIR_REST_CAP_ASC  = 22   # max HP restored per stair on ascent

    def on_level_change(self, ascending: bool = False):
        """Called when player uses a staircase. Stair-rest healing only.

        No automatic max HP growth -- that comes from cooking compound recipes
        and high-tier single ingredient cooks (Q3+).
        Stair-rest heal scales with max HP; reduced on ascent (Death pursuit).
        Capped to prevent trivialising damage at very high max HP.
        """
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

    COOKING_HP_SOFTCAP = 1000  # diminishing returns on cooking-gained max HP

    def increase_max_hp(self, amount: int, from_cooking: bool = False):
        """Permanently increase max HP. Also heals the amount.

        If from_cooking=True, applies diminishing returns: as total cooking HP
        gained approaches COOKING_HP_SOFTCAP, the bonus shrinks (floor 20%).
        """
        if from_cooking:
            cap_factor = max(0.20, 1.0 - self.cooking_hp_gained / self.COOKING_HP_SOFTCAP)
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
        return 10 - dex_mod - armor_bonus - shield_bonus - blessed_bonus - invisible_bonus - shield_effect - acc_bonus

    def get_armor_resistance(self, damage_type: str) -> float:
        """Combined damage resistance multiplier from all equipped armor/shield."""
        mult = 1.0
        for slot in self.armor_slots:
            if slot and hasattr(slot, 'damage_resistances'):
                mult *= slot.damage_resistances.get(damage_type, 1.0)
        if self.shield and hasattr(self.shield, 'damage_resistances'):
            mult *= self.shield.damage_resistances.get(damage_type, 1.0)
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
        return radius

    def get_quiz_timer(self, subject: str = 'math') -> int:
        """Base quiz timer in seconds (before status modifiers).
        Uses per-subject base + WIS scaling so text-heavy categories
        give enough reading time without making flashcard math trivial."""
        base, wis_scale = self.SUBJECT_TIMER.get(subject, (10, 1.0))
        return round(base + self.WIS * wis_scale)

    def get_quiz_timer_modifier(self) -> float:
        """Multiplier applied to quiz timer based on active effects.
        Floor of 0.40x prevents stacked debuffs from making quizzes unsolvable."""
        mod = 1.0
        if self.has_effect('confused'):      mod *= 0.55
        if self.has_effect('stunned'):       mod *= 0.75
        if self.has_effect('blinded'):       mod *= 0.70
        if self.has_effect('hallucinating'): mod *= 0.80
        if self.has_effect('hasted'):        mod *= 1.25
        if self.has_effect('blessed'):       mod *= 1.25
        return round(max(0.40, mod), 2)

    def get_int_quiz_bonus(self) -> int:
        """Extra quiz seconds for magic subjects (science/grammar/philosophy). +0.5s per INT above 10."""
        return max(0, self.INT - 10) // 2

    def get_quiz_extra_seconds(self, subject: str) -> int:
        """Extra quiz seconds from earned quirks."""
        return getattr(self, 'quiz_timer_bonuses', {}).get(subject, 0)

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
        # Stack identical items for stackable types (same id)
        # BUC must match only if known on both; hidden BUC stacks freely
        if isinstance(item, Item._STACKABLE_CLASSES):
            for existing in self.inventory:
                if existing.id != item.id:
                    continue
                both_known = getattr(existing, 'buc_known', False) and getattr(item, 'buc_known', False)
                if both_known and getattr(existing, 'buc', 'uncursed') != getattr(item, 'buc', 'uncursed'):
                    continue  # known-different BUC: separate stacks
                existing.count = getattr(existing, 'count', 1) + getattr(item, 'count', 1)
                return True
        self.inventory.append(item)
        # Keep inventory sorted alphabetically by item name
        self.inventory.sort(key=lambda i: i.name.lower())
        return True

    def remove_from_inventory(self, item) -> bool:
        if item in self.inventory:
            if getattr(item, 'count', 1) > 1:
                item.count -= 1
                return True
            self.inventory.remove(item)
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
        return slots

    def get_inventory_display(self) -> list:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        return [(letters[i], item) for i, item in enumerate(self.inventory[:26])]

    def can_equip_shield(self) -> bool:
        """Returns False when a two-handed weapon is equipped."""
        return not (self.weapon and getattr(self.weapon, 'two_handed', False))

    def try_unequip_slot(self, slot_item) -> tuple[bool, str]:
        """Attempt to remove an equipped item. Returns (success, message).
        Fails if the item is cursed."""
        if slot_item and getattr(slot_item, 'cursed', False):
            return False, f"The {slot_item.name} is welded to you!"
        return True, ""

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
                    self.inventory.append(self.ranged_weapon)
                self.ranged_weapon = item
                new_status = getattr(item, 'on_equip_status', '')
                if new_status:
                    self.add_effect(new_status, -1)
            else:
                # --- Melee weapon slot ---
                if self.weapon:
                    ok, msg = self.try_unequip_slot(self.weapon)
                    if not ok:
                        return  # cursed weapon blocks swap
                    old_status = getattr(self.weapon, 'on_equip_status', '')
                    if old_status:
                        self.status_effects.pop(old_status, None)
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
                self.inventory.append(old)
            self.armor_slots[idx] = item
            # Grant new armor's on-equip status
            new_status = getattr(item, 'on_equip_status', '')
            if new_status:
                self.add_effect(new_status, -1)
        elif isinstance(item, Shield):
            old = self.shield
            ok, _ = self.try_unequip_slot(old)
            if not ok:
                return
            if old:
                self.inventory.append(old)
            self.shield = item
        elif isinstance(item, Accessory):
            if getattr(item, 'slot', 'ring') == 'amulet':
                # Swap out existing amulet if present
                old = self.amulet_slot
                if old:
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
            else:
                # Find first empty ring slot
                for i in range(len(self.accessory_slots)):
                    if self.accessory_slots[i] is None:
                        self.accessory_slots[i] = item
                        break
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
