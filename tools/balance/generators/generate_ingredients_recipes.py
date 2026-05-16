"""
Generator E — Rebalance ingredients (~296) and compound recipes (~335).

Inputs:
  data/items/ingredient.json
  data/items/recipes.json

Outputs:
  tools/balance/generated/data/ingredient.json
  tools/balance/generated/data/recipes.json

Design intent (per GENERATORS_BRIEFING.md §6.7 + Agent E scope):
  - Preserve id, name, source_monster, symbol, color, lore, sprite_desc,
    recipes_by_quality structure, and all bonus_type / bonus_stat / bonus_amount
    / bonus_effect game-logic fields.
  - Audit weight_lb to realistic ranges (0.1-3.0 lb per the briefing).
  - Recompute every recipe's SP value to match the actual food_system.py
    formula at that quality (so the display matches the in-game effect).
    The formula is: int(5 * sqrt(min_level) * quality), floored by raw_sp
    scaler. The JSON Q1 SP becomes the raw_sp floor; Q2-Q5 SPs are shown
    for honesty though they are display-only since the formula recomputes.
  - Validate bonus magnitudes against the curve: +1 / +2 / +3 are still
    meaningful at L100 (player stat HP ~50), so amounts are preserved.
  - Add q6_bonus to legendary compound recipes for the Persephone hook.
  - Propose new compound recipes where natural ingredient pairs lack one.
"""
from __future__ import annotations
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SRC_INGRED = ROOT / 'data' / 'items' / 'ingredient.json'
SRC_RECIPES = ROOT / 'data' / 'items' / 'recipes.json'
OUT_DIR = ROOT / 'tools' / 'balance' / 'generated' / 'data'
OUT_INGRED = OUT_DIR / 'ingredient.json'
OUT_RECIPES = OUT_DIR / 'recipes.json'

# Add curve import
sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
from curve import cooking_softcap, player_hp_baseline, player_hp_target  # noqa: E402


# ----------------------------------------------------------------------
# Cooking formulas (mirror src/food_system.py exactly — for SP display)
# ----------------------------------------------------------------------

SINGLE_MULT   = {1: 0.3, 2: 0.6, 3: 0.9, 4: 1.5, 5: 2.2}
COMPOUND_MULT = {1: 0.6, 2: 1.1, 3: 1.8, 4: 3.0, 5: 4.5}


def potency(min_level: int) -> float:
    return math.sqrt(max(1, min_level))


def cooking_sp(min_level: int, quality: int, raw_sp: int = 10) -> int:
    """Mirror of food_system._cooking_sp."""
    if quality < 1:
        return 0
    formula = int(5 * potency(min_level) * quality)
    scaled = int(raw_sp * (1.0 + 0.15 * (quality - 1)))
    return max(formula, scaled)


def single_max_hp(min_level: int, quality: int) -> int:
    if quality < 1:
        return 0
    return max(1, int(potency(min_level) * SINGLE_MULT[quality]))


def compound_max_hp(max_min_level: int, quality: int, n_ingredients: int = 2) -> int:
    if quality < 1:
        return 0
    ing_bonus = 1.0 + 0.15 * (n_ingredients - 2)
    return max(1, int(potency(max_min_level) * COMPOUND_MULT[quality] * ing_bonus))


# ----------------------------------------------------------------------
# Weight audit — classify ingredients into realistic weight buckets.
# Caps at 3.0 lb (the briefing limit). Most monster drops are 0.2-1.2 lb.
# ----------------------------------------------------------------------

# Keyword -> target weight (lb). Search order: most specific first.
WEIGHT_RULES_SPECIFIC: list[tuple[tuple[str, ...], float]] = [
    # Very heavy / dense (large fully-formed items)
    (('dragon_heart', 'adult_dragon_heart'), 2.5),
    (('lich_dragon_scale',), 1.5),  # dragon scale is heavy but still scale-sized
    (('giant_bone', 'frost_giant_bone', 'fomorian_bone', 'lesser_draco_bone'), 3.0),
    (('giant_marrow',), 2.0),
    (('stone_giant_core', 'golem_stone', 'shield_core'), 2.5),
    (('cairn_stone', 'basilisk_stone', 'tomb_stone_fragment'), 2.0),
    (('lindworm_skin',), 2.0),
    (('crocodile_hide', 'troll_hide', 'gnoll_hide', 'dread_plate', 'enchanted_plate'), 1.5),
    (('bear_meat', 'lion_meat', 'royal_beef', 'prime_beef'), 2.0),
    (('zombie_flesh', 'rotted_flesh', 'mound_mulch', 'primordial_clay'), 1.5),
    (('chimera_heart', 'demon_heart', 'revenant_heart',
      'corrupted_horn_fragment', 'catoblepas_horn'), 1.2),
    (('manticore_spine', 'cyclops_eye', 'sphinx_mane', 'winged_mane'), 1.0),
    # Hide / pelt strips
    (('wolf_pelt', 'hero_hound_pelt', 'winter_wolf_pelt', 'bronze_hide_strip',
      'displacer_hide', 'lamia_scales', 'demon_scales', 'naga_scale',
      'python_scales', 'ogre_hide', 'world_serpent_scale', 'corruption_scale',
      'lizardfolk_scale', 'kobold_scale', 'behir_scale', 'pit_fiend_scale',
      'sea_dragon_scale', 'red_dragon_scale', 'blue_dragon_scale',
      'black_dragon_scale', 'dragon_scale', 'jormungandr_scale', 'nidhoggr_root_shard'), 1.0),
],
WEIGHT_RULES_SPECIFIC = WEIGHT_RULES_SPECIFIC[0]  # unwrap

# Pattern-based rules — applied in order, first match wins.
# (substring or suffix, weight_lb)
WEIGHT_PATTERNS: list[tuple[str, float]] = [
    # Tiny essences, dusts, fragments
    ('_ash', 0.1),
    ('_ink', 0.1),
    ('_dust', 0.1),
    ('_mote', 0.1),
    ('_essence', 0.2),
    ('_fragment', 0.3),
    ('_drop', 0.2),
    ('_resin', 0.2),
    ('_oil', 0.3),
    ('_spore', 0.2),
    ('_silk', 0.2),
    ('_pollen', 0.1),
    ('_dew', 0.2),
    ('_salt', 0.2),
    ('_ichor', 0.3),
    ('_blood', 0.3),
    ('_bile', 0.3),
    ('_venom', 0.2),
    ('_mucus', 0.4),
    ('_jelly', 0.5),
    ('_extract', 0.3),
    ('_powder', 0.2),
    ('_ember', 0.3),
    ('_shard', 0.4),
    ('_strand', 0.3),
    ('_strap', 0.4),
    ('_thread', 0.1),
    ('_link', 0.3),
    ('_chain', 0.5),
    ('_barb', 0.3),
    ('_thorn', 0.2),
    ('_root', 0.3),
    ('_sprig', 0.1),
    ('_leaf', 0.1),
    ('_petal', 0.1),
    ('_seed', 0.2),
    ('_twig', 0.2),
    ('_bark', 0.4),
    ('_berry', 0.2),
    # Body parts
    ('_feather', 0.2),
    ('_tooth', 0.2),
    ('_fang', 0.3),
    ('_claw', 0.3),
    ('_hook', 0.6),
    ('_horn', 0.8),
    ('_stinger', 0.4),
    ('_tail', 0.6),
    ('_tongue', 0.4),
    ('_eye', 0.3),
    ('_stalk', 0.4),
    ('_eyestalk', 0.4),
    ('_skull', 1.2),
    ('_brain', 0.8),
    ('_gland', 0.4),
    ('_sac', 0.4),
    ('_pouch', 0.4),
    ('_heart', 0.8),
    ('_liver', 0.6),
    ('_kidney', 0.4),
    ('_marrow', 1.0),
    ('_phylactery', 0.5),
    ('_heartstone', 0.6),
    ('_crystal', 0.5),
    ('_stone', 0.8),
    ('_core', 1.0),
    ('_pelt', 1.2),
    ('_hide', 1.5),
    ('_skin', 1.2),
    ('_scale', 0.4),  # single scale, not a bundle
    ('_plate', 1.2),
    ('_wing', 0.5),
    ('_wings', 0.7),
    ('_carapace', 1.0),
    ('_shell', 1.0),
    ('_bone', 0.8),  # ordinary bone, NOT giant bone (handled above)
    ('_meat', 0.8),  # ordinary meat chunk
    ('_flesh', 0.8),
    ('_haunch', 1.5),
    ('_leg', 0.8),
    ('_legs', 0.8),
    ('_paw', 0.5),
    ('_arm', 0.8),
    ('_finger', 0.2),
    ('_fingers', 0.3),
    ('_ear', 0.2),
    ('_ears', 0.2),
    # Vials and infused goods
    ('_vial', 0.4),
    ('_phial', 0.4),
    ('_flask', 0.5),
    ('_jar', 0.6),
    ('_crystal_broth', 0.5),
    ('_consomme', 0.5),
    # Plant & cooking aux
    ('_thyme', 0.1),
    ('_rosemary', 0.1),
    ('_sage', 0.1),
    ('_pepper', 0.2),
    ('_spice', 0.2),
    ('_celery', 0.3),
    ('_carrot', 0.3),
    ('_mushroom', 0.3),
    ('_fungus', 0.3),
    ('_truffle', 0.2),
    ('_mandrake', 0.4),
    ('_nightshade', 0.2),
    ('_valerian', 0.2),
]

# Default for things we don't classify by name
DEFAULT_WEIGHT = 0.6


def audit_weight(ing_id: str, current_weight: float, min_level: int) -> float:
    """Return realistic weight in lb for an ingredient. Cap at 3.0 lb."""
    lid = ing_id.lower()

    # 1. Specific overrides (exact id list)
    for ids, w in WEIGHT_RULES_SPECIFIC:
        if lid in ids:
            return w

    # 2. Pattern match (suffix / substring), most specific first
    # Iterate longest pattern first so '_eyestalk' beats '_stalk' etc.
    for pat, w in sorted(WEIGHT_PATTERNS, key=lambda x: -len(x[0])):
        if lid.endswith(pat) or pat.strip('_') in lid:
            return w

    # 3. Fallback: scale based on current_weight, clamped to [0.2, 1.5]
    if current_weight >= 8.0:
        return min(3.0, 1.5 + min(min_level, 30) / 30.0)
    if current_weight >= 5.0:
        return 1.2
    if current_weight >= 3.0:
        return 0.8
    if current_weight >= 1.5:
        return 0.5
    if current_weight >= 0.5:
        return max(0.2, current_weight)
    return max(0.1, current_weight)


# ----------------------------------------------------------------------
# Recipe SP audit
# ----------------------------------------------------------------------

def audit_ingredient_recipes(ing_id: str, ing_def: dict) -> dict:
    """Recompute SP values for each quality recipe in an ingredient.
    Preserves bonus_type, bonus_stat, bonus_amount, bonus_effect, name.
    Q1.sp is the raw_sp floor — set so it's close to the formula output
    at Q1 but never less than 5 (so eating raw still gives meaningful SP)."""
    min_level = ing_def.get('min_level', 1)
    new_recipes = {}
    # We'll compute a sensible raw_sp anchored to the formula at Q1
    formula_q1 = int(5 * potency(min_level) * 1)
    raw_sp = max(5, formula_q1)
    for q_str in ('0', '1', '2', '3', '4', '5'):
        old = ing_def.get('recipes', {}).get(q_str)
        if not old:
            continue
        q = int(q_str)
        if q == 0:
            new_recipes['0'] = {
                'name': old.get('name', 'ruined dish'),
                'sp': 0,
                'bonus_type': 'none',
                'bonus_amount': 0,
            }
            continue
        sp_value = cooking_sp(min_level, q, raw_sp)
        new = {
            'name': old.get('name', f'quality {q} dish'),
            'sp': sp_value,
            'bonus_type': old.get('bonus_type', 'none'),
            'bonus_amount': int(old.get('bonus_amount', 0)),
        }
        # Preserve optional bonus fields
        if 'bonus_stat' in old:
            new['bonus_stat'] = old['bonus_stat']
        if 'bonus_effect' in old:
            new['bonus_effect'] = old['bonus_effect']
        new_recipes[q_str] = new
    return new_recipes


def audit_compound_recipe(rid: str, recipe: dict, all_ings: dict) -> dict:
    """Recompute SP for compound recipe to match what _cooking_sp will deliver
    at Q5 (the display target). Preserves all bonus fields. Adds q6_bonus
    for legendary recipes (per Persephone Q6 hook).
    Returns a new dict — preserves all other keys."""
    new = dict(recipe)
    ing_ids = recipe.get('ingredients', [])
    if not ing_ids:
        return new
    ing_levels = [all_ings.get(iid, {}).get('min_level', 1) for iid in ing_ids]
    max_min_level = max(ing_levels) if ing_levels else 1
    # Recompute Q5 SP (the display value — engine computes per-quality at runtime)
    new['sp'] = cooking_sp(max_min_level, 5, raw_sp=10)
    # Audit bonus magnitudes — preserved per design
    # (they're floor-1 / +1, +2, +3 absolute stat bumps; still meaningful at L100)
    bonus_type = recipe.get('bonus_type', 'none')
    bonus_amount = int(recipe.get('bonus_amount', 0))
    # Cap obviously over-tuned bonuses against the curve
    # Max +3 to a single stat / two_stats / combat_stat / all_stats
    if bonus_type in ('stat', 'combat_stat', 'random_stat', 'two_stats', 'all_stats'):
        bonus_amount = min(3, max(0, bonus_amount))
        # Floor permanent +stat amounts at 1 (don't give "+0 strength" recipes)
        if bonus_amount == 0:
            bonus_amount = 1
        new['bonus_amount'] = bonus_amount
    # Status bonuses scale with duration; cap at 60 turns to keep it punchy not eternal
    if bonus_type == 'status':
        eff = recipe.get('bonus_effect', '')
        new['bonus_amount'] = min(60, max(5, int(recipe.get('bonus_amount', 10))))
        # destroyers_arcane_essence was 150 — bring it to a hard 60 cap

    # ---- Persephone Q6 hook ----
    # Legendary recipes (all_stats or two_stats +2/+3, max_min_level >= 60)
    # get a q6_bonus that triggers when the player chains to 6.
    q6 = _design_q6_bonus(rid, recipe, max_min_level, bonus_type, bonus_amount)
    if q6 is not None:
        new['q6_bonus'] = q6

    return new


def _design_q6_bonus(rid: str, recipe: dict, max_min_level: int,
                     bonus_type: str, bonus_amount: int) -> dict | None:
    """Q6 bonus for legendary compound recipes. Only ~15-25 of the 335.
    Returns None for most recipes (no Q6 effect — Q6 just caps as Q5 result)."""
    # Boss-tier all_stats and "essence" recipes get a permanent buff
    if bonus_type == 'all_stats' and max_min_level >= 70:
        return {
            'bonus_type': 'all_stats',
            'bonus_amount': 1,
            'description': 'Persephone smiles on your perfect work — every stat strengthens further.'
        }
    # Death-essence / void / abaddon-tier recipes: permanent fire/death/arcane resist
    name = recipe.get('name', '').lower()
    if max_min_level >= 80 and ('void' in name or 'abaddon' in name or 'fenrir' in name
                                  or 'samael' in name or 'seven seals' in name
                                  or 'destroyer' in name or 'undying' in name):
        return {
            'bonus_type': 'status',
            'bonus_effect': 'death_ward',
            'bonus_amount': 60,
            'description': "The meal's underworld essence wards you against the final ending."
        }
    # Dragon-tier (red/blue/lich): permanent elemental shield
    if max_min_level >= 40 and ('dragon' in name or 'fafnir' in name or 'tiamat' in name
                                 or 'lich' in name):
        return {
            'bonus_type': 'status',
            'bonus_effect': 'fire_shield',
            'bonus_amount': 40,
            'description': "Dragon-bone vapor lingers on your skin. Flame turns aside."
        }
    # Mid-tier two_stats +3: +1 random stat as a Q6 cherry
    if bonus_type == 'two_stats' and bonus_amount == 3:
        return {
            'bonus_type': 'random_stat',
            'bonus_amount': 1,
            'description': 'A flawless execution unlocks an unexpected refinement.'
        }
    return None


# ----------------------------------------------------------------------
# Proposed new compound recipes (optional, ~10-20 natural pairs)
# ----------------------------------------------------------------------

def propose_new_recipes(all_ings: dict, existing: dict) -> dict:
    """Find natural ingredient pairs that lack a compound recipe.
    Returns a dict of new recipe_id -> recipe_def to add."""
    # Existing ingredient-pair signature set
    existing_pairs = set()
    for r in existing.values():
        ings = tuple(sorted(r.get('ingredients', [])))
        if 2 <= len(ings) <= 5:
            existing_pairs.add(ings)

    proposals: dict[str, dict] = {}

    def has(*ids: str) -> bool:
        return all(i in all_ings for i in ids)

    def add(rid: str, name: str, ings: list, *, bonus_type: str,
            bonus_amount: int, bonus_stat: str | None = None,
            bonus_effect: str | None = None, description: str = '',
            sprite_desc: str = '') -> None:
        sig = tuple(sorted(ings))
        if sig in existing_pairs:
            return
        ing_levels = [all_ings.get(i, {}).get('min_level', 1) for i in ings]
        max_min_level = max(ing_levels) if ing_levels else 1
        entry: dict[str, Any] = {
            'name': name,
            'ingredients': ings,
            'sp': cooking_sp(max_min_level, 5, raw_sp=10),
            'bonus_type': bonus_type,
            'bonus_amount': bonus_amount,
            'description': description or f'A new compound dish: {name}.',
            'sprite_desc': sprite_desc or f'A plated dish of {name.lower()}.',
        }
        if bonus_stat:
            entry['bonus_stat'] = bonus_stat
        if bonus_effect:
            entry['bonus_effect'] = bonus_effect
        proposals[rid] = entry

    # 1. Frost gland + bear meat -> warming stew
    if has('frost_gland', 'bear_meat'):
        add('frostward_bear_stew', 'Frostward Bear Stew',
            ['bear_meat', 'frost_gland'],
            bonus_type='status', bonus_effect='cold_shield', bonus_amount=30,
            description='Bear haunch braised with a chilled frost gland — paradoxically, it warms.',
            sprite_desc='A clay pot of dark stew with steam curling above icy-blue glaze drops.')

    # 2. Fire gland + snake meat -> dragon-tongue skewer
    if has('fire_gland', 'snake_meat'):
        add('dragon_tongue_skewer', 'Dragon-Tongue Skewer',
            ['snake_meat', 'fire_gland'],
            bonus_type='stat', bonus_stat='DEX', bonus_amount=2,
            description='Coiled serpent flesh seared over a still-glowing fire gland.',
            sprite_desc='A blackened skewer of red-glazed serpent medallions on a smoking stone.')

    # 3. Spider silk + cave mushroom -> arachnid noodle bowl
    if has('spider_silk', 'cave_mushroom'):
        add('arachnid_noodle_bowl', 'Arachnid Noodle Bowl',
            ['spider_silk', 'cave_mushroom'],
            bonus_type='stat', bonus_stat='DEX', bonus_amount=1,
            description='Spider silk drawn into long noodles, served in mushroom-cap broth.',
            sprite_desc='A black lacquer bowl of glistening pale noodles with floating mushroom caps.')

    # 4. Goblin flesh + ember spice + cave carrot -> goblin stew classique
    if has('goblin_flesh', 'ember_spice', 'cave_carrot'):
        add('goblin_stew_classique', 'Goblin Stew Classique',
            ['goblin_flesh', 'ember_spice', 'cave_carrot'],
            bonus_type='combat_stat', bonus_amount=1,
            description="A workmanlike stew: goblin, carrot, and ember spice in a rough red broth.",
            sprite_desc='A wooden bowl of orange-red stew with chunks of greenish meat and carrot.')

    # 5. Troll hide + wild thyme -> troll cracklings
    if has('troll_hide', 'wild_thyme'):
        add('troll_cracklings_herbed', 'Herbed Troll Cracklings',
            ['troll_hide', 'wild_thyme'],
            bonus_type='status', bonus_effect='regenerating', bonus_amount=20,
            description='Troll hide rendered down to crisp cracklings with wild thyme.',
            sprite_desc='A wooden trencher of green-flecked golden-brown cracklings.')

    # 6. Cave bear meat + mandrake_root -> bear hibernation roast (CON)
    if has('bear_meat', 'mandrake_root'):
        add('hibernation_bear_roast', 'Hibernation Bear Roast',
            ['bear_meat', 'mandrake_root'],
            bonus_type='stat', bonus_stat='CON', bonus_amount=2,
            description='Bear meat slow-roasted around a mandrake root — sleep within waking.',
            sprite_desc='A large roasted bear cut split open to reveal a humanoid mandrake root.')

    # 7. Dragon scale + ember spice -> dragon scale crisps
    if has('dragon_scale', 'ember_spice'):
        add('dragon_scale_crisps', 'Dragon Scale Crisps',
            ['dragon_scale', 'ember_spice'],
            bonus_type='combat_stat', bonus_amount=2,
            description='Dragon scales fried until they shatter like glass, dusted with ember spice.',
            sprite_desc='A pewter dish of jagged red-and-gold shards, oily and faintly glowing.')

    # 8. Manticore spine + serpent_pepper -> manticore satay
    if has('manticore_spine', 'serpent_pepper'):
        add('manticore_satay', 'Manticore Spine Satay',
            ['manticore_spine', 'serpent_pepper'],
            bonus_type='stat', bonus_stat='STR', bonus_amount=2,
            description='Manticore spine marrow drawn out and grilled on skewers.',
            sprite_desc='Five bamboo skewers of glossy red marrow, glistening with pepper oil.')

    # 9. Chimera heart + wild thyme + pale celery -> chimera pot-au-feu
    if has('chimera_heart', 'wild_thyme', 'pale_celery'):
        add('chimera_pot_au_feu', 'Chimera Pot-au-Feu',
            ['chimera_heart', 'wild_thyme', 'pale_celery'],
            bonus_type='two_stats', bonus_amount=2,
            description='Three-natured chimera heart simmered with herbs into a pure French pot-au-feu.',
            sprite_desc='A tin pot of clear amber broth with neatly trimmed vegetables and pale meat.')

    # 10. Bone shard + cave mushroom -> ossuary mushroom soup
    if has('bone_shard', 'cave_mushroom'):
        add('ossuary_mushroom_soup', 'Ossuary Mushroom Soup',
            ['bone_shard', 'cave_mushroom'],
            bonus_type='random_stat', bonus_amount=1,
            description='Bone shards boiled into a marrow-rich broth, mushrooms floating on top.',
            sprite_desc='A clay bowl of grey-brown broth with dark mushroom slices, faint steam rising.')

    # 11. Frog legs + wild thyme -> classic frog legs amandine
    if has('frog_legs', 'wild_thyme'):
        add('frog_legs_thyme', 'Frog Legs Sauteed with Thyme',
            ['frog_legs', 'wild_thyme'],
            bonus_type='stat', bonus_stat='DEX', bonus_amount=1,
            description='Crisp-skinned frog legs sauteed in butter with fresh thyme. A classic.',
            sprite_desc='Two pairs of golden-brown frog legs on a white plate, herb sprigs alongside.')

    # 12. Wolf pelt + bone shard -> hunter's broth
    if has('wolf_pelt', 'bone_shard'):
        add('hunters_marrow_broth', "Hunter's Marrow Broth",
            ['wolf_pelt', 'bone_shard'],
            bonus_type='stat', bonus_stat='STR', bonus_amount=1,
            description="A trail-rough broth of bone shards simmered in a wolf-pelt-lined pot.",
            sprite_desc='A dented iron campfire-pot of grey broth, steam rising over coals.')

    # 13. Snake meat + frog legs -> swamp surf'n'turf
    if has('snake_meat', 'frog_legs'):
        add('swamp_surf_and_turf', "Swamp Surf'n'Turf",
            ['snake_meat', 'frog_legs'],
            bonus_type='stat', bonus_stat='DEX', bonus_amount=1,
            description="Snake medallions and frog legs plated together — a swamp diner's classic.",
            sprite_desc="A divided wooden plate of pale snake medallions and golden frog legs.")

    # 14. Owlbear feather + wild thyme -> owlbear pillow
    if has('owlbear_feather', 'wild_thyme'):
        add('owlbear_pillow_roast', 'Owlbear Pillow Roast',
            ['owlbear_feather', 'wild_thyme'],
            bonus_type='combat_stat', bonus_amount=1,
            description="Owlbear breast roasted on a 'pillow' of its own down and thyme.",
            sprite_desc='A roast of brown-feathered breast meat on a bed of green herbs.')

    # 15. Rotted flesh + nightshade leaf -> graveyard concoction (for desperate cooks)
    if has('rotted_flesh', 'nightshade_leaf'):
        add('graveyard_concoction', 'Graveyard Concoction',
            ['rotted_flesh', 'nightshade_leaf'],
            bonus_type='status', bonus_effect='poison_resist', bonus_amount=30,
            description='Rotted flesh stewed with nightshade leaves — fights poison with poison.',
            sprite_desc='A cracked clay bowl of grey-purple broth with dark leaves and meat.')

    # 16. Soul fragment + bone shard -> wandering soul soup
    if has('soul_fragment', 'bone_shard'):
        add('wandering_soul_soup', 'Wandering Soul Soup',
            ['soul_fragment', 'bone_shard'],
            bonus_type='stat', bonus_stat='WIS', bonus_amount=2,
            description='A clear bone broth steeped with a captured soul fragment.',
            sprite_desc='A silver bowl of pale broth with a faintly glowing wisp suspended within.')

    # 17. Demon heart + ember spice -> infernal coq-au-vin
    if has('demon_heart', 'ember_spice'):
        add('infernal_heart_au_vin', 'Infernal Heart au Vin',
            ['demon_heart', 'ember_spice'],
            bonus_type='combat_stat', bonus_amount=2,
            description='Demon heart braised in spice-fortified wine until tender and red-black.',
            sprite_desc='A copper pot of glossy black-red braise, ember spice glowing on the surface.')

    # 18. Sphinx mane + wild thyme -> sphinx broth
    if has('sphinx_mane', 'wild_thyme'):
        add('sphinx_riddle_broth', 'Sphinx Riddle Broth',
            ['sphinx_mane', 'wild_thyme'],
            bonus_type='stat', bonus_stat='INT', bonus_amount=2,
            description='Sphinx-mane hair steeped with thyme — a clarity broth, with riddles included.',
            sprite_desc='A glass cup of golden broth with one impossibly long hair coiled inside.')

    # 19. Storm feather + frost gland -> tempest crisp
    if has('storm_feather', 'frost_gland'):
        add('tempest_crisp', 'Tempest Crisp',
            ['storm_feather', 'frost_gland'],
            bonus_type='status', bonus_effect='shock_resist', bonus_amount=40,
            description='Storm-charged feather dredged in frost gland and flash-fried. Sparks on bite.',
            sprite_desc='A pale-blue crisp on a stone plate with tiny arcs of static rising from it.')

    # 20. Cave mushroom + bone shard + rat meat -> dungeon dweller's hash
    if has('cave_mushroom', 'bone_shard', 'rat_meat'):
        add('dungeon_dwellers_hash', "Dungeon Dweller's Hash",
            ['rat_meat', 'cave_mushroom', 'bone_shard'],
            bonus_type='random_stat', bonus_amount=1,
            description='The first-floor classic — whatever you can scavenge, chopped and griddled together.',
            sprite_desc='A blackened iron pan of brown hash with visible mushroom slices and meat chunks.')

    return proposals


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    with open(SRC_INGRED, encoding='utf-8') as f:
        ings_in = json.load(f)
    with open(SRC_RECIPES, encoding='utf-8') as f:
        recipes_in = json.load(f)

    # --- Ingredients ---
    ings_out: dict[str, dict] = {}
    weight_audit_stats = {'reduced': 0, 'unchanged': 0, 'raised': 0}
    for ing_id, ing in ings_in.items():
        old_weight = float(ing.get('weight', 1.0))
        min_level = int(ing.get('min_level', 1))
        new_weight = round(audit_weight(ing_id, old_weight, min_level), 1)
        if new_weight < old_weight - 0.05:
            weight_audit_stats['reduced'] += 1
        elif new_weight > old_weight + 0.05:
            weight_audit_stats['raised'] += 1
        else:
            weight_audit_stats['unchanged'] += 1

        out: dict[str, Any] = {
            'name': ing.get('name', ing_id.replace('_', ' ')),
            'symbol': ing.get('symbol', ','),
            'color': ing.get('color', [200, 130, 80]),
            'weight': new_weight,
            'min_level': min_level,
            'source_monster': ing.get('source_monster', ''),
            'recipes': audit_ingredient_recipes(ing_id, ing),
        }
        # Preserve sprite_desc, lore, mp_restore, floor_spawn_weight,
        # item_class, unidentified_name
        for k in ('sprite_desc', 'lore', 'mp_restore', 'floor_spawn_weight',
                  'item_class', 'unidentified_name'):
            if k in ing:
                out[k] = ing[k]
        ings_out[ing_id] = out

    # --- Compound recipes ---
    recipes_out: dict[str, dict] = {}
    q6_count = 0
    for rid, recipe in recipes_in.items():
        new_recipe = audit_compound_recipe(rid, recipe, ings_in)
        recipes_out[rid] = new_recipe
        if 'q6_bonus' in new_recipe:
            q6_count += 1

    # --- Proposed new recipes ---
    proposals = propose_new_recipes(ings_in, recipes_in)
    for rid, rec in proposals.items():
        # Run audit on the proposal so q6_bonus and bonus caps apply
        recipes_out[rid] = audit_compound_recipe(rid, rec, ings_in)

    # --- Write outputs ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_INGRED, 'w', encoding='utf-8') as f:
        json.dump(ings_out, f, indent=2, ensure_ascii=False)
    with open(OUT_RECIPES, 'w', encoding='utf-8') as f:
        json.dump(recipes_out, f, indent=2, ensure_ascii=False)

    # --- Print summary ---
    print(f"=== Generator E summary ===")
    print(f"Ingredients rebalanced: {len(ings_out)}")
    print(f"  Weights reduced:   {weight_audit_stats['reduced']}")
    print(f"  Weights unchanged: {weight_audit_stats['unchanged']}")
    print(f"  Weights raised:    {weight_audit_stats['raised']}")
    print(f"Recipes rebalanced: {len(recipes_in)}")
    print(f"  Recipes with q6_bonus: {q6_count}")
    print(f"New recipes proposed: {len(proposals)}")
    print(f"Total compound recipes (out): {len(recipes_out)}")
    print()
    print(f"Output:")
    print(f"  {OUT_INGRED}")
    print(f"  {OUT_RECIPES}")
    print()
    # Anchor table — show cooking_softcap at key floors
    print("Cooking softcap at anchor floors (HP gain from cooking — informs design intent):")
    for f in (1, 10, 20, 40, 60, 80, 100):
        print(f"  F{f:3d}: stat={player_hp_baseline(f):3d}  target_P={player_hp_target(f, 'P'):3d}  cook_softcap={cooking_softcap(f):3d}")


if __name__ == '__main__':
    main()
