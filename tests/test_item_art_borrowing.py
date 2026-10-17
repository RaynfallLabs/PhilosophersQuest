"""No item may show another item's picture with a contradictory meaning
(bug bash 4, call 17 / finding UI-23, 2026-10-17).

renderer._resolve_item_sprite_path falls back to a family picture when an item
has no <id>.png of its own: wands by effect, scrolls by effect, spellbooks by
spell family, collapsed rings and amulets by stat, a few uniques by hand. The bug
bash found 193 items borrowing that way, some with the opposite meaning: the
weaken-monster wand drew the empowerment wand, Solomon's signet drew a
dexterity ring.

The rule pinned here:
  1. An item from the item data files that does not ship its own picture may only
     borrow one named in DELIBERATE_SHARED, and must resolve to exactly that one.
  2. No borrowed picture, and no entry of the renderer's family maps, may carry a
     word whose opposite is in the item's own name or effect (OPPOSITES).

Corpses, cooking ingredients and template x material weapons and armour are
outside this rule: their sharing is by design (one corpse picture, tinted
templates) and they are covered by test_art_pass.
"""
import glob
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import renderer  # noqa: E402

ITEMS = os.path.join(ROOT, 'data', 'items')
SKIP_FILES = {'accessory_appearances', 'cook_outcomes', 'recipes', 'ingredient', 'prime_cuts'}

# Pictures shared on purpose: the borrowed picture shows the same thing.
# {item id: picture it shows}. Keep this list short and explain each entry.
DELIBERATE_SHARED = {
    # Same-meaning family pictures (same effect or stat) still waiting for art of their own.
    'amulet_of_constitution': 'amulet_constitution_guardian_ruby_locket',
    'amulet_of_dexterity': 'amulet_dexterity_air_light_locket',
    'amulet_of_greater_constitution': 'amulet_constitution_guardian_ruby_locket',
    'amulet_of_greater_dexterity': 'amulet_dexterity_air_light_locket',
    'amulet_of_greater_intellect': 'amulet_archmage_intellect',
    'amulet_of_greater_perception': 'amulet_perception_eagle_eye_pendant',
    'amulet_of_greater_strength': 'amulet_strength_iron_medallion',
    'amulet_of_greater_wisdom': 'amulet_wisdom_opal_locket',
    'amulet_of_hippolyta': 'girdle_of_hippolyta',
    'amulet_of_intellect': 'amulet_archmage_intellect',
    'amulet_of_perception': 'amulet_perception_eagle_eye_pendant',
    'amulet_of_searching': 'amulet_searching_bone',
    'amulet_of_strength': 'amulet_strength_iron_medallion',
    'amulet_of_telepathy': 'amulet_telepathy_jade',
    'amulet_of_warning': 'amulet_warning_copper',
    'amulet_of_wisdom': 'amulet_wisdom_opal_locket',
    'hand_of_glory': 'hamsa_hand',
    'ring_of_cold_resist': 'ring_cold_res_a',
    'ring_of_constitution': 'ring_constitution_carnelian',
    'ring_of_dexterity': 'ring_dexterity_featherweight',
    'ring_of_fire_resist': 'ring_fire_res_a',
    'ring_of_greater_constitution': 'ring_constitution_carnelian',
    'ring_of_greater_dexterity': 'ring_dexterity_featherweight',
    'ring_of_greater_intellect': 'ring_intellect_amethyst',
    'ring_of_greater_perception': 'ring_perception_amber',
    'ring_of_greater_strength': 'ring_strength_adamantine',
    'ring_of_greater_wisdom': 'ring_wisdom_ivory',
    'ring_of_intellect': 'ring_intellect_amethyst',
    'ring_of_master_constitution': 'ring_constitution_carnelian',
    'ring_of_master_dexterity': 'ring_dexterity_featherweight',
    'ring_of_master_intellect': 'ring_intellect_amethyst',
    'ring_of_master_perception': 'ring_perception_amber',
    'ring_of_master_strength': 'ring_strength_adamantine',
    'ring_of_master_wisdom': 'ring_wisdom_ivory',
    'ring_of_perception': 'ring_perception_amber',
    'ring_of_poison_resist': 'ring_poison_res_a',
    'ring_of_regeneration': 'ring_regen_emerald',
    'ring_of_searching': 'ring_searching_engraved_pewter',
    'ring_of_shock_resist': 'ring_shock_res_a',
    'ring_of_sleep_resist': 'ring_sleep_res_a',
    'ring_of_solomons_authority': 'seal_of_solomon',
    'ring_of_strength': 'ring_strength_adamantine',
    'ring_of_telepathy': 'ring_telepathy_cobalt_blue',
    'ring_of_warning': 'ring_warning_ancient_copper',
    'ring_of_wisdom': 'ring_wisdom_ivory',
    'ruby_rod': 'wand_of_fire',
    'scroll_of_absolute_ward': 'scroll_of_protection',
    'scroll_of_aegis': 'scroll_of_protection',
    'scroll_of_alacrity': 'scroll_of_haste',
    'scroll_of_area_mapping': 'scroll_of_mapping',
    'scroll_of_armor_blessing': 'scroll_of_enchant_armor',
    'scroll_of_armorer': 'scroll_of_enchant_armor',
    'scroll_of_bewilderment': 'scroll_of_confuse_monsters',
    'scroll_of_blink': 'scroll_of_teleportation',
    'scroll_of_bracing': 'scroll_of_enchant_armor',
    'scroll_of_cartography': 'scroll_of_mapping',
    'scroll_of_cataclysm': 'scroll_of_earth',
    'scroll_of_chromatic_doom': 'scroll_of_annihilation',
    'scroll_of_cleansing': 'scroll_of_remove_curse',
    'scroll_of_confusion': 'scroll_of_confuse_monsters',
    'scroll_of_cure_wounds': 'scroll_of_heal',
    'scroll_of_deep_mapping': 'scroll_of_mapping',
    'scroll_of_deep_slumber': 'scroll_of_sleep',
    'scroll_of_drowsing': 'scroll_of_sleep',
    'scroll_of_dungeon_mapping': 'scroll_of_mapping',
    'scroll_of_enchant_ring': 'scroll_of_enchant_accessory',
    'scroll_of_exile': 'scroll_of_genocide',
    'scroll_of_extinction': 'scroll_of_annihilation',
    'scroll_of_full_restoration': 'scroll_of_heal',
    'scroll_of_grand_enchantment': 'scroll_of_enchantment',
    'scroll_of_greater_enchantment': 'scroll_of_enchantment',
    'scroll_of_greater_power': 'scroll_of_great_power',
    'scroll_of_greater_protection': 'scroll_of_protection',
    'scroll_of_healing': 'scroll_of_heal',
    'scroll_of_identify_three': 'scroll_of_identify',
    'scroll_of_identify_two': 'scroll_of_identify',
    'scroll_of_illumination': 'scroll_of_light',
    'scroll_of_legendary_edge': 'scroll_of_enchant_weapon',
    'scroll_of_legendary_ward': 'scroll_of_enchant_armor',
    'scroll_of_local_mapping': 'scroll_of_mapping',
    'scroll_of_madness': 'scroll_of_confuse_monsters',
    'scroll_of_mass_identify': 'scroll_of_identify',
    'scroll_of_master_trinketry': 'scroll_of_enchant_accessory',
    'scroll_of_nine_hells': 'scroll_of_annihilation',
    'scroll_of_omnisight': 'scroll_of_identify',
    'scroll_of_power': 'scroll_of_great_power',
    'scroll_of_purge': 'scroll_of_genocide',
    'scroll_of_purification': 'scroll_of_remove_curse',
    'scroll_of_purity': 'scroll_of_remove_curse',
    'scroll_of_quickness': 'scroll_of_haste',
    'scroll_of_recall': 'scroll_of_teleportation',
    'scroll_of_recharge': 'scroll_of_charging',
    'scroll_of_rejuvenation': 'scroll_of_heal',
    'scroll_of_revelation': 'scroll_of_light',
    'scroll_of_sanctification': 'scroll_of_remove_curse',
    'scroll_of_sharpen': 'scroll_of_enchant_weapon',
    'scroll_of_slow_time': 'scroll_of_time_stop',
    'scroll_of_smiting': 'scroll_of_annihilation',
    'scroll_of_spark': 'scroll_of_charging',
    'scroll_of_stone': 'scroll_of_earth',
    'scroll_of_timeless': 'scroll_of_time_stop',
    'scroll_of_trinketry': 'scroll_of_enchant_accessory',
    'scroll_of_uncurse': 'scroll_of_remove_curse',
    'scroll_of_vigor': 'scroll_of_heal',
    'scroll_of_ward': 'scroll_of_protection',
    'scroll_of_weapon_blessing': 'scroll_of_enchant_weapon',
    'scroll_of_weaponsmith': 'scroll_of_enchant_weapon',
    'spellbook_acid_dart': 'spellbook_acid_arrow',
    'spellbook_cataclysm': 'spellbook_fireball',
    'spellbook_chain_lightning': 'spellbook_lightning_bolt',
    'spellbook_cold_bolt': 'spellbook_ice_storm',
    'spellbook_cure_light': 'spellbook_heal',
    'spellbook_deep_slumber': 'spellbook_sleep',
    'spellbook_detect_monsters': 'spellbook_detect',
    'spellbook_dissolution': 'spellbook_acid_arrow',
    'spellbook_fire_spark': 'spellbook_fireball',
    'spellbook_force_barrage': 'spellbook_magic_missile',
    'spellbook_force_storm': 'spellbook_magic_missile',
    'spellbook_greater_haste': 'spellbook_haste',
    'spellbook_greater_invisibility': 'spellbook_invisibility',
    'spellbook_greater_mapping': 'spellbook_mapping',
    'spellbook_hold_monster': 'spellbook_paralyze',
    'spellbook_identify': 'spellbook_detect_magic',
    'spellbook_madness': 'spellbook_confusion',
    'spellbook_magic_dart': 'spellbook_magic_missile',
    'spellbook_magic_shield': 'spellbook_shield',
    'spellbook_mass_slow': 'spellbook_slow',
    'spellbook_omnisight': 'spellbook_detect_magic',
    'spellbook_soul_drain': 'spellbook_drain_life',
    'spellbook_spark': 'spellbook_lightning_bolt',
    'spellbook_sunburst': 'spellbook_turn_undead',
    'spellbook_terror': 'spellbook_fear',
    'wand_of_absolute_zero': 'wand_of_frost',
    'wand_of_acid_blast': 'wand_of_acid',
    'wand_of_acid_spray': 'wand_of_acid',
    'wand_of_acid_sting': 'wand_of_acid',
    'wand_of_blizzard': 'wand_of_frost',
    'wand_of_candle_light': 'wand_of_light',
    'wand_of_cataclysm': 'wand_of_fire',
    'wand_of_chain_lightning': 'wand_of_lightning',
    'wand_of_chaos': 'wand_of_wonder',
    'wand_of_charm': 'wand_of_charm_monster',
    'wand_of_chill': 'wand_of_frost',
    'wand_of_cold_bolt': 'wand_of_frost',
    'wand_of_cure_light_wounds': 'wand_of_healing',
    'wand_of_cure_minor_wounds': 'wand_of_healing',
    'wand_of_curse_monster': 'wand_of_curse',
    'wand_of_curse_of_the_menagerie': 'wand_of_polymorph',
    'wand_of_dark_curse': 'wand_of_blindness',
    'wand_of_death_ray': 'wand_of_death',
    'wand_of_deep_slumber': 'wand_of_sleep',
    'wand_of_devastation': 'wand_of_striking',
    'wand_of_dimming': 'wand_of_blindness',
    'wand_of_disease_monster': 'wand_of_disease',
    'wand_of_disintegrate': 'wand_of_disintegration',
    'wand_of_dispel_magic': 'wand_of_dispelling',
    'wand_of_dominion': 'wand_of_charm_monster',
    'wand_of_drowsing': 'wand_of_sleep',
    'wand_of_fire_bolt': 'wand_of_fire',
    'wand_of_fire_spark': 'wand_of_fire',
    'wand_of_fire_storm': 'wand_of_fire',
    'wand_of_fireball': 'wand_of_fire',
    'wand_of_force_barrage': 'wand_of_magic_missile',
    'wand_of_force_cataclysm': 'wand_of_magic_missile',
    'wand_of_force_dart': 'wand_of_magic_missile',
    'wand_of_force_storm': 'wand_of_magic_missile',
    'wand_of_full_restoration': 'wand_of_healing',
    'wand_of_greater_charm': 'wand_of_charm_monster',
    'wand_of_greater_healing': 'wand_of_healing',
    'wand_of_greater_wonder': 'wand_of_wonder',
    'wand_of_hold': 'wand_of_paralysis',
    'wand_of_life_drain': 'wand_of_drain_life',
    'wand_of_lightning_bolt': 'wand_of_lightning',
    'wand_of_panic_wave': 'wand_of_fear',
    'wand_of_petrifaction': 'wand_of_paralysis',
    'wand_of_poison_monster': 'wand_of_poison',
    'wand_of_probing': 'wand_of_detect_monster',
    'wand_of_rap': 'wand_of_striking',
    'wand_of_rebuke': 'wand_of_turning',
    'wand_of_secret_door_detection': 'wand_of_detect_treasure',
    'wand_of_slam': 'wand_of_striking',
    'wand_of_small_polymorph': 'wand_of_polymorph',
    'wand_of_smite': 'wand_of_striking',
    'wand_of_soul_drain': 'wand_of_drain_life',
    'wand_of_static_spark': 'wand_of_lightning',
    'wand_of_sunburst': 'wand_of_turning',
    'wand_of_sunlight': 'wand_of_light',
    'wand_of_thunderstorm': 'wand_of_lightning',
    'wand_of_time_halt': 'wand_of_slow',
    'wand_of_torch_light': 'wand_of_light',
    'wand_of_turn_undead': 'wand_of_turning',
    'wand_of_zeus_wrath': 'wand_of_lightning',
}

# Word pairs that must never meet: an item whose name or effect carries one side
# may not show a picture whose name carries the other.
OPPOSITES = [
    ('weaken', 'empower'), ('weaken', 'strength'), ('curse', 'bless'), ('uncurse', 'curse'),
    ('slow', 'haste'), ('slow', 'speed'), ('sleep', 'wake'), ('fire', 'frost'), ('fire', 'cold'),
    ('fire', 'ice'), ('heal', 'drain'), ('heal', 'death'), ('heal', 'disease'), ('light', 'dark'),
    ('light', 'blind'), ('protection', 'annihilat'), ('recall', 'teleport_monster'),
    ('identify', 'confus'), ('charm', 'fear'), ('life', 'death'),
]


def _item_ids():
    ids = {}
    for path in glob.glob(os.path.join(ITEMS, '*.json')):
        name = os.path.basename(path)[:-5]
        if name in SKIP_FILES:
            continue
        with open(path, encoding='utf-8') as f:
            for k, v in json.load(f).items():
                if isinstance(v, dict):
                    ids[k] = v
    return ids


def _words(item_id, data):
    eff = data.get('effect') or data.get('spell_id') or ''
    return f'{item_id} {eff}'.lower()


def _clash(own, picture):
    """The opposite pair this picture name contradicts, or None."""
    for a, b in OPPOSITES:
        for mine, theirs in ((a, b), (b, a)):
            if mine in own and theirs in picture and theirs not in own:
                return (mine, theirs)
    return None


def _borrowers():
    out = {}
    for iid, data in _item_ids().items():
        p = renderer._resolve_item_sprite_path(iid)
        if p and os.path.basename(p) != f'{iid}.png':
            out[iid] = os.path.basename(p)[:-4]
    return out


def test_every_borrowed_picture_is_a_listed_deliberate_share():
    borrowers = _borrowers()
    unlisted = {k: v for k, v in borrowers.items() if k not in DELIBERATE_SHARED}
    assert not unlisted, f'{len(unlisted)} items show another item\'s picture: {sorted(unlisted.items())[:12]}'
    wrong = {k: (borrowers.get(k), v) for k, v in DELIBERATE_SHARED.items() if borrowers.get(k) != v}
    assert not wrong, f'allow-list entries that no longer resolve as listed (remove or fix): {sorted(wrong.items())[:12]}'


def test_no_item_shows_a_picture_with_the_opposite_meaning():
    ids = _item_ids()
    bad = []
    for iid, pic in _borrowers().items():
        c = _clash(_words(iid, ids[iid]), pic)
        if c:
            bad.append((iid, pic, c))
    assert not bad, bad


def test_family_maps_never_pair_an_effect_with_its_opposite():
    """The weaken_monster effect once mapped to wand_of_empowerment; every future
    wand, scroll or spellbook of an effect would inherit the clash."""
    bad = []
    for table in (renderer._WAND_EFFECT_SPRITE, renderer._SCROLL_EFFECT_SPRITE,
                  renderer._SPELLBOOK_FAMILY_SPRITE, renderer._UNIQUE_SPRITE_FALLBACK):
        for key, pic in table.items():
            c = _clash(key.lower(), pic.lower())
            if c:
                bad.append((key, pic, c))
    assert not bad, bad


def test_family_maps_point_at_pictures_that_exist():
    missing = []
    for table in (renderer._WAND_EFFECT_SPRITE, renderer._SCROLL_EFFECT_SPRITE,
                  renderer._SPELLBOOK_FAMILY_SPRITE, renderer._UNIQUE_SPRITE_FALLBACK):
        for key, pic in table.items():
            if not os.path.exists(os.path.join(renderer._ITEM_SPRITE_DIR, pic + '.png')):
                missing.append((key, pic))
    assert not missing, missing


def test_weaken_wand_shows_its_own_picture_not_empowerment():
    p = renderer._resolve_item_sprite_path('wand_of_weaken_monster')
    assert p and os.path.basename(p) == 'wand_of_weaken_monster.png', p
