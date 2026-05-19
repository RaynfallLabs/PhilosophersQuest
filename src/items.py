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
        # Granular identification level (0-5) for the escalator-chain identify on uniques.
        # 0 = nothing known; 1 = real name; 2 = + BUC aura; 3 = + stats; 4 = + lore; 5 = + mastery.
        # For non-unique items going through threshold-mode identify, this jumps 0 -> 5 on success.
        # Default matches `identified`: known items start at 5, unknown at 0.
        self.id_level: int      = int(defn.get('id_level', 5 if self.identified else 0))
        # Mastery blessing data for is_unique items. Shape: {'kind': str, 'value': int|float|str, 'desc': str}
        # Granted to the player on chain-5 identify; lives on player.unlocked_masteries by item_id.
        self.mastery_blessing: dict | None = defn.get('mastery_blessing', None)
        # Named/legendary marker. Routes identify to escalator-chain mode and controls spawn-pool filtering.
        # Lives on base Item so accessories/wands/scrolls/spellbooks/etc. can mark uniques in JSON.
        self.is_unique: bool    = bool(defn.get('is_unique', False))
        # Bell-curve spawn fields — used by dungeon._item_eligible_weighted to
        # weight floor-relevance. peak_floor=0 means no bell weighting (fallback).
        self.peak_floor:  int   = int(defn.get('peak_floor', 0) or 0)
        self.spread:      int   = int(defn.get('spread', 10) or 10)
        self.peak_weight: float = float(defn.get('peak_weight', 0.0) or 0.0)


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
        self.identified: bool           = bool(defn.get('identified', False))
        self.id_level: int              = int(defn.get('id_level', 5 if self.identified else 0))
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
        # Khopesh of Anubis: +max_hp on kill
        self.kill_max_hp_bonus: int     = int(defn.get('kill_max_hp_bonus', 0))
        self.kill_max_hp_cap: int       = int(defn.get('kill_max_hp_cap', 0))
        # Chandrahasa: bonus damage when player HP is low
        self.low_hp_damage_bonus: bool  = bool(defn.get('low_hp_damage_bonus', False))
        # Amenonuhoko: slow adjacent monsters on kill
        self.aoe_slow_on_kill: bool     = bool(defn.get('aoe_slow_on_kill', False))
        # Template+material class mechanic tag (cleave_on_kill, bleed_on_chain3, etc.)
        # — combat.py reads this to fire heavy-class effects at max chain / on kill.
        self.class_mechanic: str        = defn.get('class_mechanic', '')
        # True for named/legendary weapons; controls spawn pool filtering.
        self.is_unique: bool            = bool(defn.get('is_unique', False))
        # Green Chapel Axe: heal when hit by enemy
        self.on_hit_regen: int          = int(defn.get('on_hit_regen', 0))
        # Runtime-only tracking for growing power
        self.kill_count: int            = 0
        # Runtime: accumulated max_hp bonus from kill_max_hp_bonus
        self._max_hp_granted: int       = 0

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
        self.identified: bool    = bool(defn.get('identified', False))
        self.id_level: int       = int(defn.get('id_level', 5 if self.identified else 0))
        self.unidentified_name: str = defn.get('unidentified_name', 'unknown armor')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.on_equip_status: str    = defn.get('onEquipStatus', defn.get('on_equip_status', ''))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.pet_regen_bonus: int    = int(defn.get('pet_regen_bonus', 0))
        self.chain_bonus: int        = int(defn.get('chain_bonus', 0))
        # Coat of Cú Chulainn: berserk at low HP
        self.berserk_trigger: bool   = bool(defn.get('berserk_trigger', False))
        self.berserk_hp_threshold: float = float(defn.get('berserk_hp_threshold', 0.25))
        self.berserk_str_bonus: int  = int(defn.get('berserk_str_bonus', 0))
        self.berserk_duration: int   = int(defn.get('berserk_duration', 0))
        self.berserk_hp_cost: int    = int(defn.get('berserk_hp_cost', 0))
        # Babr-e Bayan: absorb first hit per floor
        self.first_hit_absorb: bool  = bool(defn.get('first_hit_absorb', False))
        # Tarnhelm: activated invisibility
        self.invisibility_power: bool = bool(defn.get('invisibility_power', False))
        self.invisibility_duration: int = int(defn.get('invisibility_duration', 0))
        self.invisibility_cooldown: int = int(defn.get('invisibility_cooldown', 0))
        # True for named/legendary armors; controls spawn pool filtering.
        self.is_unique: bool         = bool(defn.get('is_unique', False))

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
        self.identified: bool    = bool(defn.get('identified', False))
        self.id_level: int       = int(defn.get('id_level', 5 if self.identified else 0))
        self.unidentified_name: str = defn.get('unidentified_name', 'an unknown shield')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Svalinn: reflect fire damage back at attacker
        self.fire_reflect: float     = float(defn.get('fire_reflect', 0.0))
        # Ancile: bonus seconds on quiz timers
        self.quiz_timer_bonus: int   = int(defn.get('quiz_timer_bonus', 0))
        # True for named/legendary shields; controls spawn pool filtering.
        self.is_unique: bool         = bool(defn.get('is_unique', False))

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
        self.id_level: int    = int(defn.get('id_level', 5 if self.identified else 0))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Artifact mechanics (defaults match the getattr fallbacks used in main.py)
        self.passive_regen: int          = int(defn.get('passive_regen', 0))           # Eye of Horus
        self.passive_regen_interval: int = int(defn.get('passive_regen_interval', 5))
        self.gold_multiplier: float      = float(defn.get('gold_multiplier', 0.0))     # Draupnir
        self.surrounded_ac_bonus: int    = int(defn.get('surrounded_ac_bonus', 0))     # Torc of Boudicca
        self.pacify_chance: float        = float(defn.get('pacify_chance', 0.0))       # Seal of Solomon
        self.death_save: bool            = bool(defn.get('death_save', False))         # Jade Cicada
        self.resurrect_on_death: bool    = bool(defn.get('resurrect_on_death', False)) # Ankh of Isis

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
        self.id_level: int    = int(defn.get('id_level', 5 if self.identified else 0))
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
        self.id_level: int    = int(defn.get('id_level', 5 if self.identified else 0))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Spawn-once quest scrolls: survive a failed read so the secret-victory
        # path is not bricked by a single bad grammar quiz.
        self.single_copy: bool = bool(defn.get('single_copy', False))

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
        self.id_level: int     = int(defn.get('id_level', 5 if self.identified else 0))
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
        self.id_level: int          = int(defn.get('id_level', 0))
        self.unidentified_name: str = defn.get('unidentified_name', self.name)

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

    def _refresh_name(self):
        self.name = f"{self.amount} gold coin{'s' if self.amount != 1 else ''}"


def add_gold_to_tile(ground_items: list, amount: int, x: int, y: int) -> 'GoldPile':
    """Pool gold on a single tile instead of creating overlapping piles.
    If a GoldPile already exists at (x, y), add to it; otherwise create new.
    Returns the resulting GoldPile."""
    if amount <= 0:
        return None
    for it in ground_items:
        if isinstance(it, GoldPile) and it.x == x and it.y == y:
            it.amount += amount
            it._refresh_name()
            return it
    pile = GoldPile(amount, x, y)
    ground_items.append(pile)
    return pile


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


# ------------------------------------------------------------------
# Template + Material system (Phase 3.1 T3)
# Weapons, armor, and shields are now COMPOSITIONAL: a template defines the
# SHAPE (chain, slot, mechanics) and a material defines the STATS (damage
# multiplier, weight, max enchant, properties). Instances are produced on
# demand by instantiate_weapon / instantiate_armor / instantiate_shield.
# Uniques (Hrunting, Sword of Michael, etc.) keep their own JSON entries.
# ------------------------------------------------------------------

_TEMPLATES_DIR = data_path('data', 'templates')
_MATERIALS_DIR = data_path('data', 'materials')

# Cached on first load — these are read-only schema.
_TEMPLATE_CACHE: dict[str, dict[str, dict]] = {}
_MATERIAL_CACHE: dict[str, dict[str, dict]] = {}


def _load_category(root: str, category: str) -> dict[str, dict]:
    """Load every JSON file under {root}/{category}/ into a dict keyed by id."""
    cat_dir = os.path.join(root, category)
    if not os.path.isdir(cat_dir):
        return {}
    out = {}
    for fn in os.listdir(cat_dir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(cat_dir, fn), encoding='utf-8') as f:
            defn = json.load(f)
        item_id = defn.get('id') or os.path.splitext(fn)[0]
        out[item_id] = defn
    return out


def load_templates(category: str) -> dict[str, dict]:
    """Return all templates for a category: 'weapons', 'armor', or 'shields'."""
    if category not in _TEMPLATE_CACHE:
        _TEMPLATE_CACHE[category] = _load_category(_TEMPLATES_DIR, category)
    return _TEMPLATE_CACHE[category]


def load_materials(category: str) -> dict[str, dict]:
    """Return all materials for a category: 'weapons' or 'armor'."""
    if category not in _MATERIAL_CACHE:
        _MATERIAL_CACHE[category] = _load_category(_MATERIALS_DIR, category)
    return _MATERIAL_CACHE[category]


def get_template(category: str, template_id: str) -> dict | None:
    """Look up one template by category + id."""
    return load_templates(category).get(template_id)


def get_material(category: str, material_id: str) -> dict | None:
    """Look up one material by category + id."""
    return load_materials(category).get(material_id)


def instantiate_weapon(template_id: str, material_id: str, *,
                       enchant: int = 0, buc: str = 'uncursed',
                       x: int = 0, y: int = 0) -> Weapon:
    """Build a Weapon by combining a template (shape) with a material (stats).
    Damage is derived from curve.weapon_base_damage(material.peak_floor) × the
    material's damage_mult × the template's damage_modifier. Chain shape comes
    entirely from the template."""
    import math
    tpl = get_template('weapons', template_id)
    mat = get_material('weapons', material_id)
    if not tpl:
        raise ValueError(f"Unknown weapon template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown weapon material: {material_id}")

    # Re-anchored 2026-05-18: weapon_base is chosen so that a chain-5 hit
    # at the material's peak floor equals one trash-mob HP. This makes the
    # chain ladder legible at every tier (no more 1,1,1,1,2 at iron level)
    # and gives an explicit, design-grounded relationship between weapon
    # damage and monster HP.
    #
    #   chain_5_mult = template.chain_multipliers[-1]
    #   weapon_base  = mob_hp(peak_floor) / chain_5_mult
    #
    # Then base_damage applies material's damage_mult + template's
    # damage_modifier as before, and round (not int-truncate) keeps the
    # chain-1..5 gradient visible at low tiers.
    peak_floor = int(mat.get('peak_floor', 1))
    if peak_floor <= 20:
        mob_hp = 4 * (1.10 ** (peak_floor - 1))
    else:
        early_cap = 4 * (1.10 ** 19)
        mob_hp = early_cap * (1.025 ** (peak_floor - 20))
    chain_mults = tpl.get('chain_multipliers') or [0.5, 0.85, 1.0, 1.45, 2.0]
    chain_5_mult = float(chain_mults[-1])
    weapon_base = max(1, round(mob_hp / chain_5_mult))
    # Floor of 2 (not 1) on final base damage. This is universal — it
    # guarantees a LEGIBLE chain-1..5 gradient at every weapon × material
    # combo, including weak materials (copper, oak rapier) where the math
    # would otherwise produce base 1 and a flat 1,1,1,1,2 chain. The 2-floor
    # doesn't break differentiation between materials because high-tier
    # materials produce base values 3+ naturally.
    base_damage = max(2, round(weapon_base
                               * float(mat.get('damage_mult', 1.0))
                               * float(tpl.get('damage_modifier', 1.0))))

    weight = max(0.1, tpl.get('base_weight_lb', 3.0) * mat.get('weight_mult', 1.0))
    name = f"{mat['name']} {tpl['name']}"

    defn = {
        'id': f"{material_id}_{template_id}",
        'name': name,
        'symbol': '(',  # default weapon symbol; could vary by template
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'weapon',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'weapon_class': tpl.get('weapon_class', 'sword'),
        'class': tpl.get('weapon_class', 'sword'),
        'material': material_id,
        'tier': max(1, peak_floor // 20 + 1),
        'base_damage': base_damage,
        'chain_multipliers': tpl.get('chain_multipliers', [0.5, 1.0, 1.5, 2.5]),
        'damage_types': list(tpl.get('damage_types', ['slash'])),
        'two_handed': tpl.get('hands', 1) >= 2,
        'reach': int(tpl.get('reach', 1)),
        'crit_multiplier': float(tpl.get('crit_multiplier', 1.5)),
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'identified': False,
        'unidentified_name': f"{mat.get('unidentified_descriptor', mat['name'])} {tpl['name']}",
        'buc': buc,
        'requires_ammo': tpl.get('requires_ammo', None),
    }
    # Bring in material-flagged special properties (silver vs undead, etc.)
    for k in ('effective_against', 'vulnerabilities', 'special_properties'):
        if mat.get(k):
            defn[k] = mat[k]
    # Heavy-class mechanic flag (cleave / stun / etc. — code-side support pending)
    if tpl.get('class_mechanic'):
        defn['class_mechanic'] = tpl['class_mechanic']
        # Convert the 'ignores_shield' class mechanic into the explicit
        # ignore_shield weapon attribute. The bypass is checked at use-site
        # via weapon.ignore_shield, not via class_mechanic string.
        if tpl['class_mechanic'] == 'ignores_shield':
            defn['ignoreShield'] = True
    w = Weapon(defn)
    w.x, w.y = x, y
    # Material-specific damage type additions (e.g., silver adds 'silver' as a type)
    if material_id not in ('iron', 'steel'):
        if material_id not in w.damage_types:
            w.damage_types.append(material_id)
    return w


def instantiate_armor(template_id: str, material_id: str, *,
                     enchant: int = 0, buc: str = 'uncursed',
                     x: int = 0, y: int = 0) -> 'Armor':
    """Build an Armor instance from template + material."""
    tpl = get_template('armor', template_id)
    mat = get_material('armor', material_id)
    if not tpl:
        raise ValueError(f"Unknown armor template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown armor material: {material_id}")

    base_ac = int(tpl.get('base_ac_value', 1))
    material_ac = int(mat.get('ac_bonus', mat.get('armor_ac_bonus', 0)))
    weight = max(0.1, tpl.get('base_weight_lb', 5.0) * mat.get('weight_mult', 1.0))

    defn = {
        'id': f"{material_id}_{template_id}",
        'name': f"{mat['name']} {tpl['name']}",
        'symbol': '[',
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'armor',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'slot': tpl.get('slot', 'body'),
        'tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
        'material': material_id,
        'ac_bonus': base_ac + material_ac,
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'damage_resistances': mat.get('resistances', {}) if isinstance(mat.get('resistances'), dict) else {},
        'identified': False,
        'unidentified_name': f"{mat.get('unidentified_descriptor', mat['name'])} {tpl['name']}",
        'buc': buc,
        'quiz_tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
    }
    a = Armor(defn)
    a.x, a.y = x, y
    return a


def instantiate_shield(template_id: str, material_id: str, *,
                      enchant: int = 0, buc: str = 'uncursed',
                      x: int = 0, y: int = 0) -> 'Shield':
    """Build a Shield instance from template + material."""
    # Shields can pull material from either pool (weapons/armor) — try both.
    tpl = get_template('shields', template_id)
    mat = get_material('armor', material_id) or get_material('weapons', material_id)
    if not tpl:
        raise ValueError(f"Unknown shield template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown shield material: {material_id}")
    base_ac = int(tpl.get('base_ac_value', 1))
    material_ac = int(mat.get('ac_bonus', mat.get('armor_ac_bonus', 0)))
    weight = max(0.1, tpl.get('base_weight_lb', 5.0) * mat.get('weight_mult', 1.0))
    defn = {
        'id': f"{material_id}_{template_id}",
        'name': f"{mat['name']} {tpl['name']}",
        'symbol': ')',
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'shield',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
        'material': material_id,
        'ac_bonus': base_ac + material_ac,
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'identified': False,
        'unidentified_name': f"{mat.get('unidentified_descriptor', mat['name'])} {tpl['name']}",
        'buc': buc,
        'quiz_tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
    }
    s = Shield(defn)
    s.x, s.y = x, y
    return s


def material_spawn_weight(material: dict, floor: int) -> float:
    """Bell-curve spawn weight for a material at the given floor."""
    import math
    peak_floor = int(material.get('peak_floor', 1))
    spread = max(1, int(material.get('spread', 10)))
    peak_weight = float(material.get('peak_weight', 1.0))
    if peak_weight <= 0:
        return 0.0
    distance = floor - peak_floor
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    if bell < 0.005:
        return 0.0
    return max(0.02, peak_weight * bell)


def pick_random_weapon_for_floor(floor: int, rng) -> Weapon | None:
    """Pick a random (template, material) pair appropriate for this floor
    and instantiate a Weapon. Returns None if no eligible material."""
    materials = load_materials('weapons')
    weighted = [(mid, m, material_spawn_weight(m, floor))
                for mid, m in materials.items()]
    weighted = [(mid, m, w) for mid, m, w in weighted if w > 0]
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break

    # Pick a compatible template
    templates = load_templates('weapons')
    mat_classes = set(chosen_mat.get('material_class', '').split(',')) | {chosen_mat.get('material_class', '')}
    compatible = []
    for tid, t in templates.items():
        accepts = set(t.get('compatible_material_classes', []))
        if not accepts or accepts & mat_classes or chosen_mat.get('material_class') in accepts:
            compatible.append((tid, t))
    if not compatible:
        compatible = list(templates.items())  # fallback
    tid, _ = rng.choice(compatible)
    return instantiate_weapon(tid, chosen_mid)


def pick_random_armor_for_floor(floor: int, rng, slot: str = 'body') -> 'Armor | None':
    """Pick a random armor template+material pair for this floor + slot.
    Filters templates to those that BOTH match the slot AND accept the
    chosen material's material_class — so e.g. 'ash' (wood) only goes to
    armor templates that accept wood, never to a steel breastplate."""
    materials = load_materials('armor')
    # Pre-filter materials: only those usable in at least one slot-matching template
    templates = load_templates('armor')
    slot_templates = [(tid, t) for tid, t in templates.items()
                      if t.get('slot', 'body') == slot]
    if not slot_templates:
        return None
    # Build set of material classes accepted by any slot-matching template
    accepted_classes: set[str] = set()
    for _, t in slot_templates:
        accepted_classes.update(t.get('compatible_material_classes', []))

    weighted = []
    for mid, m in materials.items():
        if m.get('material_class', '') not in accepted_classes and accepted_classes:
            continue
        w = material_spawn_weight(m, floor)
        if w > 0:
            weighted.append((mid, m, w))
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break
    # Now narrow templates to those that accept this specific material
    chosen_class = chosen_mat.get('material_class', '')
    compatible = [(tid, t) for tid, t in slot_templates
                  if chosen_class in t.get('compatible_material_classes', [])]
    if not compatible:
        compatible = slot_templates  # safety fallback
    tid, _ = rng.choice(compatible)
    try:
        return instantiate_armor(tid, chosen_mid)
    except ValueError:
        return None


def pick_random_shield_for_floor(floor: int, rng) -> 'Shield | None':
    """Pick a random shield template+material pair for this floor. Filters
    by template/material compatibility so e.g. 'linen' doesn't end up in a
    tower shield."""
    materials = load_materials('armor')
    templates = load_templates('shields')
    if not templates:
        return None
    # Set of material classes accepted by any shield template
    accepted_classes: set[str] = set()
    for t in templates.values():
        accepted_classes.update(t.get('compatible_material_classes', []))
    weighted = []
    for mid, m in materials.items():
        if m.get('material_class', '') not in accepted_classes and accepted_classes:
            continue
        w = material_spawn_weight(m, floor)
        if w > 0:
            weighted.append((mid, m, w))
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break
    chosen_class = chosen_mat.get('material_class', '')
    compatible = [tid for tid, t in templates.items()
                  if chosen_class in t.get('compatible_material_classes', [])]
    if not compatible:
        compatible = list(templates.keys())
    tid = rng.choice(compatible)
    try:
        return instantiate_shield(tid, chosen_mid)
    except ValueError:
        return None


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
        'single_copy': True,
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
        'single_copy': True,
    })
    item.x = x
    item.y = y
    return item
