import copy
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'items')

# Armor slot index map (matches Player.armor_slots order)
ARMOR_SLOTS = ['head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt']


class Item:
    def __init__(self, defn: dict):
        self.id         = defn['id']
        self.name       = defn['name']
        self.symbol     = defn['symbol']
        self.color      = tuple(defn['color'])
        self.weight     = float(defn.get('weight', 1.0))
        self.item_class = defn['item_class']
        self.min_level  = int(defn.get('min_level', 1))
        self.x: int = 0
        self.y: int = 0


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
        self.max_chain_length: int | None = defn.get(
            'maxChainLength', defn.get('max_chain_length', None)
        )
        self.quiz_tier: int             = int(defn.get('mathTier', defn.get('quiz_tier', 1)))
        self.damage_types: list[str]    = defn.get('damageTypes', defn.get('damage_types', ['slash']))
        self.two_handed: bool           = bool(defn.get('twoHanded', defn.get('two_handed', False)))
        self.reach: int                 = int(defn.get('reach', 1))
        self.stun_chance: float         = float(defn.get('stunChance', defn.get('stun_chance', 0.0)))
        self.requires_ammo: str | None  = defn.get('requiresAmmo', defn.get('requires_ammo', None))
        self.floor_spawn_weight: dict   = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.container_loot_tier: str   = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.value: int                 = int(defn.get('value', 50))
        self.enchant_bonus: int         = 0


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
        self.cursed: bool        = False   # set at spawn time


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
        self.cursed: bool        = False


class Accessory(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot             = defn['slot']
        self.effects          = defn.get('effects', {})
        self.equip_threshold  = int(defn.get('equip_threshold', 2))
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified       = False


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
        self.identified       = False


class Scroll(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.quiz_threshold   = int(defn.get('quiz_threshold', 2))
        self.effect           = defn.get('effect', '')
        self.power            = defn.get('power', '')
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.identified       = False


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
        self.recipes: dict = defn.get('recipes', {})


class Corpse(Item):
    def __init__(self, monster_name: str, monster_id: str, x: int, y: int,
                 harvest_tier: int = 1, harvest_threshold: int = 2,
                 ingredient_id: str | None = None):
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
        self.harvest_tier      = harvest_tier
        self.harvest_threshold = harvest_threshold
        self.ingredient_id     = ingredient_id
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
        self.count:        int = self.count_min   # re-rolled at spawn
        self.floor_spawn_weight: dict = defn.get('floor_spawn_weight', {})
        self.value:        int = int(defn.get('value', 1))


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
    'ingredient': Ingredient,
    'artifact':   Artifact,
    'ammo':       Ammo,
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
