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
        self.armor_slots = [None] * 8     # head, body, arms, hands, legs, feet, cloak, shirt
        self.accessory_slots = [None] * 4

        # Inventory (list of item objects)
        self.inventory = []

        # Status effects: effect_id -> turns_remaining (or -1 for permanent)
        self.status_effects: dict[str, int] = {}
        # Fractional damage resistances: damage_type -> multiplier (0.0=immune,1.0=normal)
        self.resistances: dict[str, float] = {}
        # Item IDs the player has identified this run
        self.known_item_ids: set[str] = set()

    # --- Resources ---

    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Apply damage after immunity and resistance checks. Returns actual damage."""
        from status_effects import DAMAGE_IMMUNITY
        # Full immunity via status effect
        immunity_effect = DAMAGE_IMMUNITY.get(damage_type)
        if immunity_effect and self.has_effect(immunity_effect):
            return 0

        # Fractional resistance from items/intrinsics
        resistance = self.resistances.get(damage_type, 1.0)
        actual = max(0, int(amount * resistance))
        self.hp = max(0, self.hp - actual)

        # Damage wakes a sleeping player
        if actual > 0 and 'sleeping' in self.status_effects:
            del self.status_effects['sleeping']

        return actual

    def is_dead(self) -> bool:
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

    def restore_mp(self, amount: int):
        self.mp = min(self.max_mp, self.mp + amount)

    # --- Status effects ---

    def has_effect(self, name: str) -> bool:
        """True if the effect is active (any non-zero value)."""
        return self.status_effects.get(name, 0) != 0

    def add_effect(self, name: str, duration: int) -> bool:
        """Apply effect via the status_effects module. Returns True if applied."""
        from status_effects import apply_effect
        return apply_effect(self, name, duration)

    def tick_effects(self) -> list:
        """Process one turn for all active effects. Returns list of (msg, type) pairs."""
        from status_effects import tick_all
        return tick_all(self)

    # --- Derived stats ---

    def get_ac(self) -> int:
        """Armor class = 10 + DEX modifier + equipped armor and shield bonuses."""
        dex_mod = (self.DEX - 10) // 2
        armor_bonus = sum(
            getattr(slot, 'ac_bonus', 0) for slot in self.armor_slots if slot is not None
        )
        shield_bonus = getattr(self.shield, 'ac_bonus', 0) if self.shield else 0
        # Invisible grants a small AC bonus (hard to hit)
        invisible_bonus = 2 if self.has_effect('invisible') else 0
        return 10 + dex_mod + armor_bonus + shield_bonus + invisible_bonus

    def get_sight_radius(self) -> int:
        """Sight radius in tiles. Blindness caps it at 1."""
        if self.has_effect('blinded'):
            return 1
        return max(3, self.PER // 2)

    def get_quiz_timer(self) -> int:
        """Base quiz timer in seconds (before modifiers)."""
        return self.BASE_TIMER + max(0, self.WIS - 10)

    def get_quiz_timer_modifier(self) -> float:
        """Multiplier applied to quiz timer based on active effects."""
        mod = 1.0
        if self.has_effect('confused'):      mod *= 0.55
        if self.has_effect('stunned'):       mod *= 0.75
        if self.has_effect('blinded'):       mod *= 0.70
        if self.has_effect('hallucinating'): mod *= 0.80
        if self.has_effect('hasted'):        mod *= 1.25
        return round(mod, 2)

    def get_carry_limit(self) -> int:
        return self.CARRY_BASE + self.STR * self.CARRY_PER_STR

    def get_current_weight(self) -> float:
        return sum(getattr(item, 'weight', 0) for item in self.inventory)

    # --- Inventory ---

    def add_to_inventory(self, item) -> bool:
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
        """Permanently change a stat and update derived maximums."""
        setattr(self, stat, getattr(self, stat) + amount)
        if stat == 'CON':
            self.max_hp = self.BASE_HP + self.CON
            self.max_sp = self.BASE_SP + self.CON
        elif stat == 'INT':
            self.max_mp = self.BASE_MP + self.INT

    # --- Equipment ---

    def get_equipped_items(self) -> dict:
        from items import ARMOR_SLOTS
        slots = {'weapon': self.weapon, 'shield': self.shield}
        for i, name in enumerate(ARMOR_SLOTS):
            slots[name] = self.armor_slots[i]
        return slots

    def get_inventory_display(self) -> list:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        return [(letters[i], item) for i, item in enumerate(self.inventory[:26])]

    def _apply_equip(self, item):
        from items import Weapon, Armor, Shield, Accessory, ARMOR_SLOTS
        if isinstance(item, Weapon):
            self.weapon = item
        elif isinstance(item, Armor):
            idx = ARMOR_SLOTS.index(item.slot) if item.slot in ARMOR_SLOTS else 0
            self.armor_slots[idx] = item
        elif isinstance(item, Shield):
            self.shield = item
        elif isinstance(item, Accessory):
            # Find first empty accessory slot
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
