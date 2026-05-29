"""Class-level mastery system for common (non-unique) items.

UNIQUES use per-item mastery: each named legendary (Soul Reaver, Excalibur,
etc.) has its own `mastery_blessing` in JSON, recorded against `item.id` on
`player.unlocked_masteries`.

COMMONS use class-level mastery: mastering one "Ring of Strength" applies the
blessing to ALL rings of strength in inventory + future drops, regardless of
material variant. Class membership is computed at runtime — no JSON migration
required.

The class key is:
  - Wand / Scroll / Potion / Spellbook  -> item.id  (each id is its own class)
  - Accessory                            -> slug(item.name)
                                            ("Ring of Strength" -> "ring_of_strength")
  - All other (Weapon/Armor/Shield/etc.) -> item.id  (currently uniques only,
                                            but defensive)

Mastery blessings for each class live in CLASS_MASTERY_BLESSINGS below.
They are deliberately SMALL flavor bonuses — mastering a Ring of Strength
should feel like a meaningful pat on the back, not a balance break.
"""
from __future__ import annotations

import re


def get_mastery_class(item) -> str:
    """Return the class key under which mastery is stored for `item`.

    Uniques always store mastery against item.id (legacy behavior). Commons
    use a class derived from name (accessories) or id (everything else).
    """
    if getattr(item, 'is_unique', False):
        return item.id
    # Defer import so this module stays import-light
    from items import Accessory
    if isinstance(item, Accessory):
        return _slugify(getattr(item, 'name', '') or item.id)
    return item.id


_SLUG_PUNCT = re.compile(r'[^a-z0-9]+')


def _slugify(text: str) -> str:
    """Convert "Ring of Strength" -> "ring_of_strength"."""
    s = text.strip().lower()
    s = _SLUG_PUNCT.sub('_', s)
    return s.strip('_')


# ----------------------------------------------------------------------
# Class-mastery blessings
# ----------------------------------------------------------------------
#
# Each blessing follows the same shape as item.mastery_blessing:
#   {'kind': str, 'value': int|float|dict|str, 'scope': 'class',
#    'desc': str}
#
# Kinds reuse the existing _apply_mastery_once / use-site logic in
# game_magic.py where possible. New kinds added at the bottom and wired
# at their use-sites in this same commit.
#
# These are intentionally SMALL — flavor bonuses. The player should feel
# "I have learned this", not "I have broken the game".
#
CLASS_MASTERY_BLESSINGS: dict[str, dict] = {

    # -- Accessory classes (~58-70, derived from name) --
    'ring_of_strength': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'STR', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of strength: a quiet +1 STR while any is worn.',
    },
    'ring_of_constitution': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'CON', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of constitution: +1 CON while any is worn.',
    },
    'ring_of_dexterity': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'DEX', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of dexterity: +1 DEX while any is worn.',
    },
    'ring_of_intellect': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'INT', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of intellect: +1 INT while any is worn.',
    },
    'ring_of_wisdom': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'WIS', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of wisdom: +1 WIS while any is worn.',
    },
    'ring_of_perception': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'PER', 'amount': 1},
        'scope': 'class',
        'desc': 'You understand the ring of perception: +1 PER while any is worn.',
    },
    'ring_of_protection': {
        'kind': 'class_acc_ac_bonus', 'value': 1, 'scope': 'class',
        'desc': 'Rings of protection feel familiar — they grant +1 AC bonus when worn.',
    },
    'ring_of_regeneration': {
        'kind': 'class_acc_regen_bonus', 'value': 1, 'scope': 'class',
        'desc': 'You attune to regeneration: HP returns 1 turn faster from any such ring.',
    },
    'ring_of_searching': {
        'kind': 'class_acc_passive_radius', 'value': 1, 'scope': 'class',
        'desc': 'The ring of searching reveals its rhythm — +1 search radius.',
    },
    'ring_of_telepathy': {
        'kind': 'class_acc_passive_radius', 'value': 2, 'scope': 'class',
        'desc': 'You read the telepathy ring like a known book — +2 to its reach.',
    },
    'ring_of_warning': {
        'kind': 'class_acc_passive_radius', 'value': 1, 'scope': 'class',
        'desc': 'The ring of warning whispers more clearly to you — +1 to its range.',
    },
    'ring_of_fire_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'fire', 'amount': 0.10},
        'scope': 'class',
        'desc': 'You know fire resistance rings intimately — +10% to the effect.',
    },
    'ring_of_cold_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'cold', 'amount': 0.10},
        'scope': 'class',
        'desc': 'Cold-resist rings yield their inner pattern — +10% to the effect.',
    },
    'ring_of_shock_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'lightning', 'amount': 0.10},
        'scope': 'class',
        'desc': 'You understand shock-resist rings — +10% to the effect.',
    },
    'ring_of_poison_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'poison', 'amount': 0.10},
        'scope': 'class',
        'desc': 'Poison-resist rings feel native to you — +10% to the effect.',
    },
    'ring_of_sleep_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'sleep', 'amount': 0.10},
        'scope': 'class',
        'desc': 'Sleep-resist rings yield their secret — +10% to the effect.',
    },
    'ring_of_magic_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'magic', 'amount': 0.10},
        'scope': 'class',
        'desc': 'You understand magic-resist rings — +10% to the effect.',
    },
    'ring_of_drain_resist': {
        'kind': 'class_acc_resist_bonus', 'value': {'type': 'drain', 'amount': 0.10},
        'scope': 'class',
        'desc': 'You attune to drain-resist rings — +10% to the effect.',
    },
    'ring_of_sustenance': {
        'kind': 'class_acc_sp_burn_bonus', 'value': 0.10, 'scope': 'class',
        'desc': 'Rings of sustenance feel natural — SP burns 10% slower while worn.',
    },
    'ring_of_speed': {
        'kind': 'class_acc_quirk', 'value': 'speed_extend', 'scope': 'class',
        'desc': 'The ring of speed pulses with you — its haste lasts a few turns longer.',
    },
    'ring_of_invisibility': {
        'kind': 'class_acc_quirk', 'value': 'invis_extend', 'scope': 'class',
        'desc': 'You know how to wear invisibility — its effect lingers a touch longer.',
    },
    'ring_of_levitation': {
        'kind': 'class_acc_quirk', 'value': 'levitate_extend', 'scope': 'class',
        'desc': 'Levitation rings respond to you — their lift holds longer.',
    },
    'ring_of_displacement': {
        'kind': 'class_acc_quirk', 'value': 'displace_extend', 'scope': 'class',
        'desc': 'You move with displacement rings rather than fighting them — they last longer.',
    },
    'ring_of_clairvoyance': {
        'kind': 'class_acc_passive_radius', 'value': 1, 'scope': 'class',
        'desc': 'Clairvoyance rings open their sight to you — +1 to the reveal radius.',
    },

    # -- Amulet classes (parallel ring entries where relevant) --
    'amulet_of_strength': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'STR', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of strength feel familiar — +1 STR while any is worn.',
    },
    'amulet_of_constitution': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'CON', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of constitution feel familiar — +1 CON while any is worn.',
    },
    'amulet_of_dexterity': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'DEX', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of dexterity feel familiar — +1 DEX while any is worn.',
    },
    'amulet_of_intellect': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'INT', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of intellect feel familiar — +1 INT while any is worn.',
    },
    'amulet_of_wisdom': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'WIS', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of wisdom feel familiar — +1 WIS while any is worn.',
    },
    'amulet_of_perception': {
        'kind': 'class_acc_stat_bonus', 'value': {'stat': 'PER', 'amount': 1},
        'scope': 'class',
        'desc': 'Amulets of perception feel familiar — +1 PER while any is worn.',
    },
    'amulet_of_regeneration': {
        'kind': 'class_acc_regen_bonus', 'value': 1, 'scope': 'class',
        'desc': 'Amulets of regeneration: HP returns 1 turn faster.',
    },
    'amulet_of_searching': {
        'kind': 'class_acc_passive_radius', 'value': 1, 'scope': 'class',
        'desc': 'Searching amulets ring out their pattern — +1 to the radius.',
    },
    'amulet_of_telepathy': {
        'kind': 'class_acc_passive_radius', 'value': 2, 'scope': 'class',
        'desc': 'Telepathy amulets read like a known book — +2 to the reach.',
    },
    'amulet_of_warning': {
        'kind': 'class_acc_passive_radius', 'value': 1, 'scope': 'class',
        'desc': 'Warning amulets whisper clearly to you — +1 to the range.',
    },

    # -- Wands (each id is its own class) --
    'wand_of_healing': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'You know wands of healing — each gains +1 maximum charge.',
    },
    'wand_of_extra_healing': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'You know wands of extra healing — each gains +1 maximum charge.',
    },
    'wand_of_magic_missile': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'Wands of magic missile feel familiar — +1 maximum charge each.',
    },
    'wand_of_light': {
        'kind': 'wand_extra_charge', 'value': 2, 'scope': 'class',
        'desc': 'Wands of light pour their secret to you — +2 maximum charge each.',
    },
    'wand_of_lightning': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'You know wands of lightning — +1 maximum charge each.',
    },
    'wand_of_fire': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'You know wands of fire — +1 maximum charge each.',
    },
    'wand_of_cold': {
        'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
        'desc': 'You know wands of cold — +1 maximum charge each.',
    },

    # -- Scrolls (each id is its own class) --
    'scroll_of_heal': {
        'kind': 'class_scroll_potency', 'value': 0.25, 'scope': 'class',
        'desc': 'Scrolls of heal yield their pattern — heals are 25% stronger.',
    },
    'scroll_of_extra_heal': {
        'kind': 'class_scroll_potency', 'value': 0.20, 'scope': 'class',
        'desc': 'Scrolls of extra heal yield their pattern — heals are 20% stronger.',
    },
    'scroll_of_mapping': {
        'kind': 'class_scroll_persist', 'value': True, 'scope': 'class',
        'desc': 'Mapping scrolls work as you remember them — the revealed map persists across floors.',
    },
    'scroll_of_identify': {
        'kind': 'class_scroll_extra_uses', 'value': 1, 'scope': 'class',
        'desc': 'You can recite scrolls of identify from memory — one extra read per scroll.',
    },
    'scroll_of_teleport': {
        'kind': 'class_scroll_extra_uses', 'value': 1, 'scope': 'class',
        'desc': 'Teleport scrolls feel familiar — one extra read per scroll.',
    },

    # -- Potions (each id is its own class) --
    'potion_of_healing': {
        'kind': 'potion_potency_bonus', 'value': 0.25, 'scope': 'class',
        'desc': 'Potions of healing are 25% more potent in your hands.',
    },
    'potion_of_extra_healing': {
        'kind': 'potion_potency_bonus', 'value': 0.20, 'scope': 'class',
        'desc': 'Potions of extra healing are 20% more potent in your hands.',
    },
    'potion_of_full_healing': {
        'kind': 'potion_potency_bonus', 'value': 0.15, 'scope': 'class',
        'desc': 'Potions of full healing are 15% more potent in your hands.',
    },
    'potion_of_haste': {
        'kind': 'potion_duration_bonus', 'value': 4, 'scope': 'class',
        'desc': 'Potions of haste last 4 turns longer when you drink them.',
    },
    'potion_of_heroism': {
        'kind': 'potion_duration_bonus', 'value': 4, 'scope': 'class',
        'desc': 'Potions of heroism last 4 turns longer in your bloodstream.',
    },

    # -- Spellbooks (each id is its own class) --
    # spellbook_mp_discount already exists in _apply_mastery_once.
    'spellbook_magic_missile': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know magic missile to the bone — it costs 1 less MP.',
    },
    'spellbook_cure_wounds': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know cure wounds to the bone — it costs 1 less MP.',
    },
    'spellbook_sleep': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know sleep to the bone — it costs 1 less MP.',
    },
    'spellbook_light': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know light to the bone — it costs 1 less MP.',
    },
    'spellbook_frost_touch': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know frost touch to the bone — it costs 1 less MP.',
    },
    'spellbook_mage_armor': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know mage armor to the bone — it costs 1 less MP.',
    },
    'spellbook_detect_magic': {
        'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
        'desc': 'You know detect magic to the bone — it costs 1 less MP.',
    },
}


def default_blessing_for_class(class_id: str, item) -> dict | None:
    """Fallback when no authored blessing exists for a class.

    Mirrors _default_mastery_for in game_magic.py but returns class-scoped
    blessings. Conservative — small flavor bonuses.
    """
    from items import Accessory, Wand, Scroll, Spellbook, Potion, Weapon, Armor, Shield
    if isinstance(item, Weapon):
        # Flat +1 damage per hit. Multiplicative bonuses round to zero on
        # low-damage weapons; flat +1 is always visible. Reuses the existing
        # 'weapon_base_damage_bonus' kind handler in combat._weapon_mastery
        # path (extended to read class masteries too).
        return {'kind': 'weapon_base_damage_bonus', 'value': 1, 'scope': 'class',
                'desc': f"You know the {class_id.replace('_', ' ')} — +1 flat damage on every hit."}
    if isinstance(item, Armor):
        # Flat -1 incoming physical. Capped at 1 total in player.take_damage
        # (eight armor slots × -1 each would be game-breaking).
        return {'kind': 'class_armor_damage_reduction', 'value': 1, 'scope': 'class',
                'desc': f"You wear the {class_id.replace('_', ' ')} as if born to it — -1 incoming physical (capped: 1 max from any mastered armor)."}
    if isinstance(item, Shield):
        return {'kind': 'class_shield_ac_bonus', 'value': 1, 'scope': 'class',
                'desc': f"The {class_id.replace('_', ' ')} sits true on your arm — +1 AC bonus when held."}
    if isinstance(item, Accessory):
        return {'kind': 'class_acc_buff_duration_bonus', 'value': 4, 'scope': 'class',
                'desc': f"You understand {class_id.replace('_', ' ')} — buffs last 4 turns longer."}
    if isinstance(item, Wand):
        return {'kind': 'wand_extra_charge', 'value': 1, 'scope': 'class',
                'desc': f"You know {class_id.replace('_', ' ')} — +1 maximum charge each."}
    if isinstance(item, Scroll):
        return {'kind': 'class_scroll_extra_uses', 'value': 1, 'scope': 'class',
                'desc': f"You can recite {class_id.replace('_', ' ')} from memory — one extra read."}
    if isinstance(item, Spellbook):
        return {'kind': 'spellbook_mp_discount', 'value': 1, 'scope': 'class',
                'desc': f"You know {class_id.replace('_', ' ')} to the bone — costs 1 less MP."}
    if isinstance(item, Potion):
        return {'kind': 'potion_potency_bonus', 'value': 0.20, 'scope': 'class',
                'desc': "Potions of this class are 20% more potent in your hands."}
    return None
