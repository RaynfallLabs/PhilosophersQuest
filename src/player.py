class Player:
    BASE_HP = 20
    BASE_SP = 20
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
        self.max_sp = self.BASE_SP + self.CON
        self.sp = self.max_sp
        self.max_mp = self.BASE_MP + self.INT
        self.mp = self.max_mp

        # Position on the dungeon grid
        self.x = 0
        self.y = 0

        # Equipment slots
        self.weapon = None
        self.shield = None
        self.armor_slots = [None] * 8     # head, chest, legs, feet, hands, back, ring x2
        self.accessory_slots = [None] * 4

        # Inventory (list of item objects)
        self.inventory = []

        # Status effects: effect_name -> turns_remaining
        self.status_effects: dict[str, int] = {}
        # Resistances: damage_type -> multiplier (0.0 = immune, 1.0 = normal)
        self.resistances: dict[str, float] = {}

    # --- Resources ---

    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Apply damage after resistance. Returns actual damage dealt."""
        resistance = self.resistances.get(damage_type, 1.0)
        actual = max(0, int(amount * resistance))
        self.hp = max(0, self.hp - actual)
        return actual

    def is_dead(self) -> bool:
        return self.hp <= 0

    def spend_sp(self, amount: int) -> bool:
        """Spend stamina points. Returns False if insufficient."""
        if self.sp < amount:
            return False
        self.sp -= amount
        return True

    def restore_sp(self, amount: int):
        self.sp = min(self.max_sp, self.sp + amount)

    def restore_hp(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def restore_mp(self, amount: int):
        self.mp = min(self.max_mp, self.mp + amount)

    # --- Derived stats ---

    def get_ac(self) -> int:
        """Armor class = 10 + DEX modifier + equipped armor and shield bonuses."""
        dex_mod = (self.DEX - 10) // 2
        armor_bonus = sum(
            getattr(slot, 'ac_bonus', 0) for slot in self.armor_slots if slot is not None
        )
        shield_bonus = getattr(self.shield, 'ac_bonus', 0) if self.shield else 0
        return 10 + dex_mod + armor_bonus + shield_bonus

    def get_sight_radius(self) -> int:
        """Sight radius in tiles, driven by PER stat."""
        return max(3, self.PER // 2)

    def get_quiz_timer(self) -> int:
        """Quiz timer in seconds: base + 1s per WIS point above 10."""
        return self.BASE_TIMER + max(0, self.WIS - 10)

    def get_carry_limit(self) -> int:
        return self.CARRY_BASE + self.STR * self.CARRY_PER_STR

    def get_current_weight(self) -> float:
        return sum(getattr(item, 'weight', 0) for item in self.inventory)

    # --- Inventory ---

    def add_to_inventory(self, item) -> bool:
        """Add item if within weight limit. Returns True on success."""
        if self.get_current_weight() + getattr(item, 'weight', 0) > self.get_carry_limit():
            return False
        self.inventory.append(item)
        return True

    def remove_from_inventory(self, item) -> bool:
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    # --- Stat bonuses ---

    def apply_stat_bonus(self, stat: str, amount: int):
        """Permanently increase a stat and update derived maximums."""
        setattr(self, stat, getattr(self, stat) + amount)
        if stat == 'CON':
            self.max_hp = self.BASE_HP + self.CON
            self.max_sp = self.BASE_SP + self.CON
        elif stat == 'INT':
            self.max_mp = self.BASE_MP + self.INT

    # --- Equipment ---

    def get_equipped_items(self) -> dict:
        """Return dict of slot_name -> item (or None) for UI display."""
        from items import ARMOR_SLOTS
        slots = {'weapon': self.weapon, 'shield': self.shield}
        for i, name in enumerate(ARMOR_SLOTS):
            slots[name] = self.armor_slots[i]
        return slots

    def get_inventory_display(self) -> list:
        """Return list of (letter, item) tuples for UI display (max 26)."""
        letters = 'abcdefghijklmnopqrstuvwxyz'
        return [(letters[i], item) for i, item in enumerate(self.inventory[:26])]

    def _apply_equip(self, item):
        """Place item into the correct equipment slot. No quiz check — call after quiz success."""
        from items import Weapon, Armor, Shield, ARMOR_SLOTS
        if isinstance(item, Weapon):
            self.weapon = item
        elif isinstance(item, Armor):
            idx = ARMOR_SLOTS.index(item.slot) if item.slot in ARMOR_SLOTS else 0
            self.armor_slots[idx] = item
        elif isinstance(item, Shield):
            self.shield = item
