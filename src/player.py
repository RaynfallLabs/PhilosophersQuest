class Player:
    BASE_HP = 20
    BASE_SP = 200
    BASE_MP = 10
    BASE_TIMER = 10      # seconds for quiz timer
    CARRY_BASE = 50
    CARRY_PER_STR = 5

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
        self.weapon = None
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

    HP_PER_LEVEL = 8  # max HP gained per dungeon level (staircase use)

    def on_level_change(self):
        """Called when player uses a staircase. Grants max HP and stair-rest healing.

        The stair-rest heal scales with max HP (5%) so deep-level players recover
        meaningfully between floors -- important for the 200-level gauntlet.
        At L1: ~2 HP; at L20: ~9 HP; at L60: ~25 HP; at L100: ~41 HP.
        """
        self.max_hp += self.HP_PER_LEVEL
        rest_heal = max(self.HP_PER_LEVEL, int(self.max_hp * 0.05))
        self.hp = min(self.hp + rest_heal, self.max_hp)
        mp_restore = max(2, self.INT // 5)
        self.restore_mp(mp_restore)

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
        # Invisibility: harder to hit -> lowers AC by 2
        invisible_bonus = 2 if self.has_effect('invisible') else 0
        # Shielded status effect (from wand of shielding): -2 AC
        shield_effect   = 2 if self.has_effect('shielded') else 0
        return 10 - dex_mod - armor_bonus - shield_bonus - invisible_bonus - shield_effect

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
        """Sight radius in tiles. Blindness caps it at 1."""
        if self.has_effect('blinded'):
            return 1
        radius = max(3, self.PER // 2)
        if self.has_effect('dark_vision'):
            radius += 4
        if self.has_effect('truesight'):
            radius += 2
        return radius

    def get_quiz_timer(self) -> int:
        """Base quiz timer in seconds (before modifiers)."""
        return self.BASE_TIMER + max(0, self.WIS - 10)

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
        if isinstance(item, Item._STACKABLE_CLASSES):
            existing = next((i for i in self.inventory if i.id == item.id), None)
            if existing is not None:
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
        slots = {'weapon': self.weapon, 'shield': self.shield}
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
            # Return old weapon to inventory (check for cursed)
            if self.weapon:
                ok, msg = self.try_unequip_slot(self.weapon)
                if not ok:
                    return  # cursed weapon blocks swap
                self.inventory.append(self.weapon)
            # Unequip shield if switching to 2H
            if getattr(item, 'two_handed', False) and self.shield:
                ok, msg = self.try_unequip_slot(self.shield)
                if not ok:
                    return  # can't swap -- cursed shield blocks
                self.inventory.append(self.shield)
                self.shield = None
            self.weapon = item
        elif isinstance(item, Armor):
            idx = ARMOR_SLOTS.index(item.slot) if item.slot in ARMOR_SLOTS else 0
            old = self.armor_slots[idx]
            ok, _ = self.try_unequip_slot(old)
            if not ok:
                return
            if old:
                self.inventory.append(old)
            self.armor_slots[idx] = item
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
        # Re-sort inventory after any equipment swap that returned items
        self.inventory.sort(key=lambda i: i.name.lower())
