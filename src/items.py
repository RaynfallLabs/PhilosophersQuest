import copy
import json
import os
from paths import data_path

_DATA_DIR = data_path('data', 'items')

# Armor slot index map (matches Player.armor_slots order)
ARMOR_SLOTS = ['head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt']

# Per-slot enchantment caps (max enchant_bonus allowed)
ENCHANT_CAP = {
    'head': 2, 'body': 3, 'arms': 1, 'hands': 1,
    'legs': 1, 'feet': 1, 'cloak': 2, 'shirt': 1,
    'shield': 2, 'weapon': 5,
}
# Random spawn enchant is capped at +1 for armor/shield; scrolls can push to slot cap
SPAWN_ENCHANT_CAP_ARMOR = 1


class Item:
    # Item types where identical instances (same id) merge into a stack
    _STACKABLE_CLASSES: tuple = ()   # filled in after subclass definitions

    def __init__(self, defn: dict):
        self.id         = defn['id']
        self.name       = defn['name']
        self.symbol     = defn['symbol']
        self.color      = tuple(defn['color'])
        self.weight     = float(defn.get('weight', 1.0))
        self.item_class = defn.get('item_class', 'unknown')
        self.min_level  = int(defn.get('min_level', 1))
        self.x: int = 0
        self.y: int = 0
        self.count: int = 1          # stack size; >1 only for stackable types
        # Identification & BUC -- defaults on ALL items so no subclass can be missing them
        self.identified: bool   = defn.get('identified', True)
        self.unidentified_name: str = defn.get('unidentified_name', defn['name'])
        self.buc: str           = defn.get('buc', 'uncursed')
        self.buc_known: bool    = defn.get('buc_known', False)
        self.lore: str          = defn.get('lore', '')
        self.set_id: str        = defn.get('set_id', '')
        self.set_name: str      = defn.get('set_name', '')


class Weapon(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        # New structured fields (camelCase keys from JSON, fallback to legacy snake_case)
        self.weapon_class: str          = defn.get('class', defn.get('weapon_class', 'sword'))
        self.variant: str               = defn.get('variant', '1h')
        self.tier: int                  = int(defn.get('tier', 1))
        self.material: str              = defn.get('material', 'iron')
        self.base_damage: int           = int(defn.get('baseDamage', defn.get('base_damage', 5)))
        # Legacy dice damage kept for backward compat; new weapons use base_damage
        self.damage: str | None         = defn.get('damage', None)
        self.chain_multipliers: list[float] = defn.get(
            'chainMultipliers', defn.get('chain_multipliers', [0.5, 1.0, 1.5, 2.0, 2.5])
        )
        self.quiz_tier: int             = int(defn.get('mathTier', defn.get('quiz_tier', 1)))
        self.damage_types: list[str]    = defn.get('damageTypes', defn.get('damage_types', ['slash']))
        self.two_handed: bool           = bool(defn.get('twoHanded', defn.get('two_handed', False)))
        self.reach: int                 = int(defn.get('reach', 1))
        self.stun_chance: float         = float(defn.get('stunChance', defn.get('stun_chance', 0.0)))
        self.bleed_chance: float        = float(defn.get('bleedChance', defn.get('bleed_chance', 0.0)))
        self.knockback: bool            = bool(defn.get('knockback', False))
        self.ignore_shield: bool        = bool(defn.get('ignoreShield', defn.get('ignore_shield', False)))
        self.crit_multiplier: float     = float(defn.get('critMultiplier', defn.get('crit_multiplier', 1.0)))
        self.requires_ammo: str | None  = defn.get('requiresAmmo', defn.get('requires_ammo', None))
        self.infinite_ammo: bool        = bool(defn.get('infiniteAmmo', defn.get('infinite_ammo', False)))
        self.floor_spawn_weight: dict   = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.container_loot_tier: str   = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.value: int                 = int(defn.get('value', 50))
        self.enchant_bonus: int         = int(defn.get('enchant_bonus', defn.get('enchantBonus', 0)))
        self.buc: str                   = 'uncursed'
        self.buc_known: bool            = False
        self.identified: bool           = bool(defn.get('identified', False))
        self.unidentified_name: str     = defn.get('unidentified_name', 'an unknown weapon')
        # On-hit effect properties
        self.poison_chance: float       = float(defn.get('poisonChance', defn.get('poison_chance', 0.0)))
        self.burn_chance: float         = float(defn.get('burnChance', defn.get('burn_chance', 0.0)))
        self.confuse_chance: float      = float(defn.get('confuseChance', defn.get('confuse_chance', 0.0)))
        self.lifesteal_percent: float   = float(defn.get('lifestealPercent', defn.get('lifesteal_percent', 0.0)))
        self.cursed_miss_backlash: int  = int(defn.get('cursedMissBacklash', defn.get('cursed_miss_backlash', 0)))
        self.petrify_on_crit: bool      = bool(defn.get('petrifyOnCrit', defn.get('petrify_on_crit', False)))
        self.counter_attack_chance: float = float(defn.get('counterAttackChance', defn.get('counter_attack_chance', 0.0)))
        self.kill_heal_amount: int      = int(defn.get('killHealAmount', defn.get('kill_heal_amount', 0)))
        self.growing_power: bool        = bool(defn.get('growingPower', defn.get('growing_power', False)))
        self.kills_to_grow: int         = int(defn.get('killsToGrow', defn.get('kills_to_grow', 10)))
        self.on_equip_status: str       = defn.get('onEquipStatus', defn.get('on_equip_status', ''))
        self.can_dig: bool              = bool(defn.get('can_dig', False))
        self.ignore_resistances: bool   = bool(defn.get('ignore_resistances', False))
        self.abaddon_bonus_damage: str  = defn.get('abaddon_bonus_damage', '')
        # Runtime-only tracking for growing power
        self.kill_count: int            = 0

    @property
    def max_chain_length(self) -> int:
        """Always derived from chain_multipliers so old pickled weapons stay correct."""
        return len(self.chain_multipliers)

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Armor(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot                = defn['slot']
        self.tier: int           = int(defn.get('tier', 1))
        self.material: str       = defn.get('material', 'leather')
        self.ac_bonus: int       = int(defn['ac_bonus'])
        self.enchant_bonus: int  = int(defn.get('enchant_bonus', 0))
        self.equip_threshold     = int(defn.get('equip_threshold', 2))
        self.quiz_tier: int      = int(defn.get('quiz_tier', 1))
        self.damage_resistances: dict = defn.get('damage_resistances', {})
        self.can_be_cursed: bool = bool(defn.get('can_be_cursed', False))
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False
        self.identified: bool    = bool(defn.get('identified', False))
        self.unidentified_name: str = defn.get('unidentified_name', 'unknown armor')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.on_equip_status: str    = defn.get('onEquipStatus', defn.get('on_equip_status', ''))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.pet_regen_bonus: int    = int(defn.get('pet_regen_bonus', 0))
        self.chain_bonus: int        = int(defn.get('chain_bonus', 0))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Shield(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.tier: int           = int(defn.get('tier', 1))
        self.material: str       = defn.get('material', 'wood')
        self.ac_bonus: int       = int(defn['ac_bonus'])
        self.enchant_bonus: int  = int(defn.get('enchant_bonus', 0))
        self.equip_threshold     = int(defn.get('equip_threshold', 2))
        self.quiz_tier: int      = int(defn.get('quiz_tier', 1))
        self.damage_resistances: dict = defn.get('damage_resistances', {})
        self.can_be_cursed: bool = bool(defn.get('can_be_cursed', False))
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False
        self.identified: bool    = bool(defn.get('identified', False))
        self.unidentified_name: str = defn.get('unidentified_name', 'an unknown shield')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Accessory(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot             = defn['slot']
        self.effects          = defn.get('effects', {})
        self.equip_threshold  = int(defn.get('equip_threshold', 2))
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified       = bool(defn.get('identified', False))
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Wand(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        # charges_min/max used at spawn time to roll a semi-random starting count
        self.charges_min      = int(defn.get('charges_min', defn.get('charges', 3)))
        self.charges_max      = int(defn.get('charges_max', self.charges_min))
        self.charges          = self.charges_min          # re-rolled when placed in dungeon
        self.max_charges      = int(defn.get('max_charges', self.charges_max))
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.quiz_threshold   = int(defn.get('quiz_threshold', 2))
        self.effect           = defn.get('effect', '')
        self.power            = defn.get('power', '')
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified       = bool(defn.get('identified', False))
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Scroll(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.quiz_threshold   = int(defn.get('quiz_threshold', 2))
        self.effect           = defn.get('effect', '')
        self.power            = defn.get('power', '')
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified       = bool(defn.get('identified', False))
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Spellbook(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.spell_id          = defn.get('spell_id', '')
        self.spell_name        = defn.get('spell_name', self.name)
        self.mp_cost           = int(defn.get('mp_cost', 5))
        self.quiz_tier         = int(defn.get('quiz_tier', 1))
        self.quiz_threshold    = int(defn.get('quiz_threshold', 1))
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified        = bool(defn.get('identified', False))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))


class Artifact(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)


class Lockpick(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.max_durability          = int(defn.get('max_durability', 5))
        self.durability              = int(defn.get('durability', 5))
        self.durability_loss_success = int(defn.get('durability_loss_success', 1))
        self.durability_loss_failure = int(defn.get('durability_loss_failure', 2))
        self.identified: bool        = True
        self.unidentified_name: str  = defn.get('unidentified_name', self.name)


class Container(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.tier           = int(defn.get('tier', 1))
        self.quiz_threshold = int(defn.get('quiz_threshold', 2))
        self.trapped        = bool(defn.get('trapped', False))
        self.trap           = defn.get('trap', None)   # dict or None
        self.gold           = defn.get('gold', [0, 0]) # [min, max]
        self.extra_item_chance = float(defn.get('extra_item_chance', 0.40))
        # Runtime state (not from JSON)
        self.trap_triggered = False
        self.opened         = False
        self.is_mimic       = False


class Ingredient(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.source_monster = defn.get('source_monster', '')
        # recipes: str(quality 0-5) -> {name, sp, bonus_type, bonus_amount}
        self.recipes: dict  = defn.get('recipes', {})
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.identified: bool       = True   # raw ingredients are obvious
        self.unidentified_name: str = defn.get('unidentified_name', self.name)
        self.mp_restore: int        = int(defn.get('mp_restore', 0))


class Corpse(Item):
    def __init__(self, monster_name: str, monster_id: str, x: int, y: int,
                 harvest_tier: int = 1, harvest_threshold: int = 2,
                 ingredient_id: str | None = None,
                 lore: str = '', monster_def: dict | None = None):
        defn = {
            'id':         f'corpse_{monster_id}',
            'name':       f'{monster_name} corpse',
            'symbol':     '%',
            'color':      [160, 60, 60],
            'weight':     5.0,
            'item_class': 'corpse',
            'min_level':  1,
        }
        super().__init__(defn)
        self.monster_id        = monster_id
        self.monster_name      = monster_name
        self.harvest_tier      = harvest_tier
        self.harvest_threshold = harvest_threshold
        self.ingredient_id     = ingredient_id
        self.lore              = lore
        self.monster_def       = monster_def or {}   # full definition for stat display
        self.lore_identified   = False
        self.x = x
        self.y = y


class Ammo(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.ammo_type:    str = defn.get('ammo_type', 'arrow')
        self.tier:         int = int(defn.get('tier', 1))
        self.damage_bonus: int = int(defn.get('damage_bonus', 0))
        self.count_min:    int = int(defn.get('count_min', 10))
        self.count_max:    int = int(defn.get('count_max', 20))
        self.count:        int = self.count_min   # set at spawn; base class also has count=1 default
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.value:        int = int(defn.get('value', 1))
        # Ammo is always visually obvious -- identified by default
        self.identified: bool       = True
        self.unidentified_name: str = defn.get('unidentified_name', self.name)


class Food(Item):
    """Ready-to-eat food item. Restores SP and optionally HP; may grant a stat bonus."""
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.sp_restore:  int  = int(defn.get('sp_restore', 20))
        self.hp_restore:  int  = int(defn.get('hp_restore', 0))
        self.bonus_type:  str  = defn.get('bonus_type', 'none')
        self.bonus_stat:  str  = defn.get('bonus_stat', '')
        self.bonus_effect: str = defn.get('bonus_effect', '')
        self.bonus_amount: int = int(defn.get('bonus_amount', 0))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Food is recognizable by appearance -- identified by default
        self.identified: bool       = True
        self.unidentified_name: str = defn.get('unidentified_name', self.name)


class Potion(Item):
    """Drinkable potion. Instant or timed effect; no quiz required."""
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.effect:   str = defn.get('effect', '')
        self.power:    str = defn.get('power', '')
        self.duration: int = int(defn.get('duration', 0))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', {})
        self.identified: bool       = False
        self.unidentified_name: str = defn.get('unidentified_name', self.name)
        self.buc: str            = 'uncursed'
        self.buc_known: bool     = False

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class GoldPile:
    """Gold coins lying on the ground. Picked up to credit player_gold directly."""
    def __init__(self, amount: int, x: int = 0, y: int = 0):
        self.id     = 'gold_pile'
        self.amount = amount
        self.name   = f"{amount} gold coin{'s' if amount != 1 else ''}"
        self.symbol = '$'
        self.color  = (218, 165, 32)
        self.x      = x
        self.y      = y


# Stackable item types: identical instances (same id) merge into one stack entry.
Item._STACKABLE_CLASSES = (Ingredient, Food, Potion, Scroll, Ammo)

# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------

_CLASS_MAP: dict[str, type] = {
    'weapon':     Weapon,
    'armor':      Armor,
    'shield':     Shield,
    'accessory':  Accessory,
    'wand':       Wand,
    'scroll':     Scroll,
    'spellbook':  Spellbook,
    'ingredient': Ingredient,
    'artifact':   Artifact,
    'ammo':       Ammo,
    'food':       Food,
    'potion':     Potion,
    'lockpick':   Lockpick,
    'container':  Container,
}


def load_items(item_class: str) -> list:
    """Load and return a list of Item instances from data/items/{item_class}.json."""
    path = os.path.join(_DATA_DIR, f"{item_class}.json")
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    cls = _CLASS_MAP[item_class]
    return [cls({**defn, 'id': item_id, 'item_class': item_class})
            for item_id, defn in raw.items()]


def copy_at(item: Item, x: int, y: int) -> Item:
    """Return a shallow copy of item placed at (x, y)."""
    inst = copy.copy(item)
    inst.x = x
    inst.y = y
    return inst


# ------------------------------------------------------------------
# Deep-lore item factories  (not loaded from JSON)
# ------------------------------------------------------------------

def make_abyssal_shimmer(x: int, y: int) -> Item:
    """A fixed terrain feature -- the ground shimmers with ancient energy."""
    item = Item({
        'id': 'abyssal_shimmer',
        'name': 'Abyssal Shimmer',
        'symbol': '*',
        'color': [80, 20, 160],
        'weight': 9999.0,
        'item_class': 'terrain',
        'min_level': 1,
    })
    item.x = x
    item.y = y
    item.activated = False   # True once the Complete Tablet is placed here
    return item


def make_tablet_of_second_death(x: int, y: int) -> Item:
    """A stone tablet with a curious shaped slot -- unidentified until examined."""
    item = Artifact({
        'id': 'tablet_of_second_death',
        'name': 'Tablet of Second Death',
        'symbol': '=',
        'color': [150, 130, 80],
        'weight': 3.0,
        'item_class': 'artifact',
        'min_level': 80,
        'lore': "An ancient stone tablet, cold to the touch. A circular slot in its center is shaped to hold something luminous. Along the bottom edge, faint words are carved in a dead language. You can make out: 'The key to the Abyss. Place upon the threshold where the veil is thin.'",
    })
    item.x = x
    item.y = y
    item.unidentified_name = 'plain tablet'
    item.identified = False
    item.examine_text = "A plain tablet with a slot that looks like a small stone will fit."
    return item


def make_scroll_lake_of_fire(x: int, y: int) -> Scroll:
    """A worn scroll -- its contents unknown until read."""
    item = Scroll({
        'id': 'scroll_lake_of_fire',
        'name': 'Scroll of the Lake of Fire',
        'symbol': '?',
        'color': [220, 80, 20],
        'weight': 0.3,
        'item_class': 'scroll',
        'min_level': 50,
        'quiz_tier': 3,
        'quiz_threshold': 3,
        'effect': 'lake_of_fire',
        'power': '',
        'unidentified_name': 'worn scroll',
        'identified': False,
        'lore': "A scroll of terrible power, its words drawn from the final chapter of Revelation. The ink smells of ash and brimstone. The last line is underlined twice: 'This is the second death, the lake of fire.'",
    })
    item.x = x
    item.y = y
    return item


def make_philosophers_wrench(x: int, y: int) -> Wand:
    """An odd tool -- its purpose unclear until the right pieces are in hand."""
    item = Wand({
        'id': 'philosophers_wrench',
        'name': "Philosopher's Wrench",
        'symbol': '/',
        'color': [140, 130, 90],
        'weight': 2.0,
        'item_class': 'wand',
        'min_level': 21,
        'charges': 99,
        'charges_min': 99,
        'charges_max': 99,
        'max_charges': 99,
        'quiz_tier': 1,
        'quiz_threshold': 1,
        'effect': 'philosophers_wrench',
        'power': '',
        'unidentified_name': 'odd tool',
        'identified': False,
        'lore': "A tool of impossible craftsmanship. It does not tighten or loosen — it joins. Place it between two objects that were meant to become one, and the Wrench will fuse them. The alchemists who forged it understood that the greatest creation is not building something new, but completing something unfinished.",
    })
    item.x = x
    item.y = y
    return item


def make_complete_tablet(x: int, y: int) -> Item:
    """The Stone set perfectly into the Tablet -- ready."""
    item = Artifact({
        'id': 'complete_tablet_of_second_death',
        'name': 'Complete Tablet of Second Death',
        'symbol': '=',
        'color': [220, 180, 60],
        'weight': 4.0,
        'item_class': 'artifact',
        'min_level': 1,
        'lore': "The Philosopher's Stone sits perfectly in the tablet's slot. The cold stone is warm now, pulsing with deep golden light. The inscription along the bottom burns bright: 'The key to the Abyss.' It wants to be placed upon a threshold.",
    })
    item.x = x
    item.y = y
    item.identified = True
    item.examine_text = (
        "The Philosopher's Stone sits perfectly in the slot, glowing with deep energy."
    )
    return item


def make_death_bane_scroll(x: int, y: int) -> Scroll:
    """The sixth boss reward scroll -- dropped when Death itself is defeated."""
    item = Scroll({
        'id': 'scroll_deaths_bane',
        'name': "Scroll of Death's Bane",
        'symbol': '?',
        'color': [220, 220, 255],
        'weight': 0.1,
        'item_class': 'scroll',
        'min_level': 1,
        'quiz_tier': 1,
        'quiz_threshold': 1,
        'effect': 'boss_reward',
        'power': 'ABYSSAL-VICTOR',
        'unidentified_name': "Scroll of Death's Bane",
        'identified': True,
    })
    item.x = x
    item.y = y
    return item
