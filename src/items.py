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
        self.damage            = defn['damage']
        self.chain_multipliers: list[float] = defn.get(
            'chain_multipliers', [0.5, 1.0, 1.5, 2.0, 2.5]
        )
        self.max_chain_length: int | None = defn.get('max_chain_length', None)
        self.quiz_tier: int               = defn.get('quiz_tier', 1)


class Armor(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot             = defn['slot']
        self.ac_bonus: int    = int(defn['ac_bonus'])
        self.equip_threshold  = int(defn.get('equip_threshold', 2))


class Shield(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.ac_bonus: int   = int(defn['ac_bonus'])
        self.equip_threshold = int(defn.get('equip_threshold', 2))


class Accessory(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot    = defn['slot']
        self.effects = defn.get('effects', {})


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


# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------

_CLASS_MAP: dict[str, type] = {
    'weapon':     Weapon,
    'armor':      Armor,
    'shield':     Shield,
    'accessory':  Accessory,
    'ingredient': Ingredient,
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
