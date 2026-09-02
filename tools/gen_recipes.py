"""Generate recipes.json v2 for the cook v3 redesign (v2.6.4, 2026-09-02).

Bottom-up: catalog ingredients -> for each meaningful ingredient combo,
emit a recipe card that references an outcome archetype from
data/items/cook_outcomes.json.

Design:
  - Every prime ingredient gets a solo recipe (templated name + flavor).
  - Signature monsters (~30) get hand-crafted names for solo + combo.
  - Every prime × dungeon-ingredient combo that makes thematic sense
    gets a combo recipe (thematic outcome for the pairing).
  - 12 family recipes: one per creature family, hand-crafted.
  - 14 trophy recipes: one per boss, unique perm-power outcome.
  - 8 dungeon-ingredient utility recipes: mushroom tea etc.
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict

random.seed(20260902)  # deterministic output

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGREDIENTS_PATH = os.path.join(ROOT, "data", "items", "ingredient.json")
OUTCOMES_PATH    = os.path.join(ROOT, "data", "items", "cook_outcomes.json")
MONSTERS_PATH    = os.path.join(ROOT, "data", "monsters.json")
PRIME_CUTS_PATH  = os.path.join(ROOT, "data", "items", "prime_cuts.json")
OUT_PATH         = os.path.join(ROOT, "data", "items", "recipes.json")


# ----------------------------------------------------------------------
# Tier bands
# ----------------------------------------------------------------------

def tier_from_ml(ml: int) -> int:
    """Quiz tier from ingredient min_level (dungeon depth)."""
    if ml <= 15: return 1
    if ml <= 35: return 2
    if ml <= 55: return 3
    if ml <= 80: return 4
    return 5


# ----------------------------------------------------------------------
# Naming templates
# ----------------------------------------------------------------------

# Cooking-style verbs (rotated so different monsters get different treatments)
STYLES = [
    "Sauteed", "Roasted", "Braised", "Grilled", "Skewered", "Smoked",
    "Pan-Fried", "Stewed", "Confit", "Charred", "Glazed", "Blackened",
    "Pickled", "Rubbed", "Broiled", "Poached", "Seared", "Slow-Cooked",
]

# Body-part vocabulary by creature family (chosen for edibility flavor)
PARTS_BY_FAMILY = {
    "beast":      ["Haunch", "Loin", "Shank", "Rib", "Liver", "Kidney", "Heart", "Tongue"],
    "humanoid":   ["Rib", "Shoulder", "Belly", "Kidney", "Liver", "Cheek", "Loin"],
    "reptile":    ["Tail", "Flank", "Belly", "Liver", "Egg", "Fin"],
    "dragon":     ["Wing", "Rib", "Heart", "Scale-Fat", "Talon-Meat", "Marrow"],
    "undead":     ["Marrow", "Bone-Broth", "Sinew", "Rib-Stock", "Ghost-Fat"],
    "demon":      ["Ichor", "Horn-Marrow", "Flank", "Tongue", "Rib", "Heart"],
    "celestial":  ["Radiant Cut", "Sunfat", "Wing-Meat", "Marrow"],
    "fey":        ["Blossom-Sap", "Petal-Fat", "Sinew", "Tongue"],
    "construct":  ["Gear-Grease", "Plate-Scrap", "Filament"],
    "elemental":  ["Essence-Core", "Ember", "Rime-Shard", "Ash-Cake"],
    "plant":      ["Fiber", "Root", "Stalk", "Fruit-Body"],
    "aberration": ["Ichor", "Fibrous Meat", "Tendril", "Sac-Meat"],
}

# Adjunct phrasing for dungeon ingredients
DUNGEON_TAG = {
    "cave_mushroom":   "with Cave Mushroom",
    "altar_incense":   "in Altar Incense",
    "swamp_moss":      "over Swamp Moss",
    "river_salt":      "in River-Salt Crust",
    "holy_water":      "in Holy Water Reduction",
    "crystal_shard":   "with Crystal Shard",
    "deep_iron":       "on Deep-Iron",
    "abyssal_kelp":    "with Abyssal Kelp",
}


# ----------------------------------------------------------------------
# Signature monsters (hand-crafted names for solo + combo)
# ----------------------------------------------------------------------
# Iconic monsters players will encounter often; each gets thematic
# per-recipe names (solo + one or two combos). All others use the
# STYLES + PARTS template.

SIGNATURE = {
    "giant_rat":        {"solo": "Roasted Rat Skewer",           "part": "Kidney"},
    "goblin":           {"solo": "Braised Goblin Rib",           "part": "Kidney"},
    "kobold":           {"solo": "Kobold Innard Skewer",         "part": "Innards"},
    "orc":              {"solo": "Orcish Loin Roast",            "part": "Loin"},
    "gnoll":            {"solo": "Gnoll Haunch on the Bone",     "part": "Haunch"},
    "hobgoblin":        {"solo": "Hobgoblin Kidney Pie",         "part": "Kidney"},
    "bugbear":          {"solo": "Bugbear Cheek Confit",         "part": "Cheek"},
    "troll":            {"solo": "Troll Marrow Stew",            "part": "Marrow"},
    "ogre":             {"solo": "Ogre Rib Rack",                "part": "Rib"},
    "wolf":             {"solo": "Wolf-Loin Grill",              "part": "Loin"},
    "dire_wolf":        {"solo": "Dire Wolf Heart Sear",         "part": "Heart"},
    "minotaur":         {"solo": "Minotaur Steak, Bloody",       "part": "Steak"},
    "wraith":           {"solo": "Wraith-Fat Rendering",         "part": "Ghost-Fat"},
    "zombie":           {"solo": "Zombie Sinew Broth",           "part": "Sinew"},
    "skeleton":         {"solo": "Skeleton Bone-Stock",          "part": "Bone-Broth"},
    "lich":             {"solo": "Lich Marrow Reduction",        "part": "Marrow"},
    "wight":            {"solo": "Wight-Rib Braise",             "part": "Rib"},
    "vampire":          {"solo": "Vampiric Kidney Sear",         "part": "Kidney"},
    "imp":              {"solo": "Imp-Tongue Skewer",            "part": "Tongue"},
    "demon":            {"solo": "Demon-Flank Roast",            "part": "Flank"},
    "quasit":           {"solo": "Quasit-Ichor Broth",           "part": "Ichor"},
    "wyvern":           {"solo": "Wyvern Wing Confit",           "part": "Wing"},
    "drake":            {"solo": "Drake-Tail Steak",             "part": "Tail"},
    "manticore":        {"solo": "Manticore Rib Braise",         "part": "Rib"},
    "hydra":            {"solo": "Hydra-Neck Stew",              "part": "Neck-Meat"},
    "chimera":          {"solo": "Chimera Trinity Grill",        "part": "Cut"},
    "griffin":          {"solo": "Griffin Wing Roast",           "part": "Wing"},
    "unicorn":          {"solo": "Unicorn Heart Confit",         "part": "Heart"},
    "pegasus":          {"solo": "Pegasus Wing Steak",           "part": "Wing"},
    "sphinx":           {"solo": "Sphinx-Loin Riddle-Roast",     "part": "Loin"},
    "giant_spider":     {"solo": "Spider-Sac Poach",             "part": "Sac"},
    "giant_scorpion":   {"solo": "Scorpion-Claw Grill",          "part": "Claw"},
    "beholder":         {"solo": "Beholder-Eye Fry",             "part": "Eye"},
    "mind_flayer":      {"solo": "Mind Flayer Brain Terrine",    "part": "Brain"},
    "gelatinous_cube":  {"solo": "Cube-Aspic Slice",             "part": "Aspic"},
    "rust_monster":     {"solo": "Rust-Monster Iron Broth",      "part": "Filament"},
    "displacer_beast":  {"solo": "Displacer Loin, Grilled",      "part": "Loin"},
    "owlbear":          {"solo": "Owlbear Haunch Roast",         "part": "Haunch"},
    "yeti":             {"solo": "Yeti Rib Slow-Cook",           "part": "Rib"},
    "elemental":        {"solo": "Elemental Essence Reduction",  "part": "Essence"},
}


# ----------------------------------------------------------------------
# Ingredient -> outcome mapping (dungeon-ingredient-pairing heuristics)
# ----------------------------------------------------------------------
# Each dungeon adjunct pushes the outcome toward a specific archetype
# family. The exact tier is picked by depth of the highest-ml ingredient.

DUNGEON_BUFF_FAMILY = {
    # ingredient_id -> preferred outcome BUFF theme
    "cave_mushroom":   "perception",       # mushroom -> perception / dark_vision
    "altar_incense":   "blessed",          # incense -> blessed / holy
    "swamp_moss":      "regen",            # moss -> regen / SP-recovery
    "river_salt":      "poison_resist",    # salt -> save vs poison
    "holy_water":      "drain_resist",     # holy water -> drain / undead resist
    "crystal_shard":   "brilliance",       # crystal -> brilliance / mana
    "deep_iron":       "shielded",         # iron -> shielded / STR
    "abyssal_kelp":    "cold_resist",      # kelp -> cold / water-adjacent
}

# Family -> preferred "solo prime" outcome theme (when no dungeon ingredient)
FAMILY_SOLO_THEME = {
    "beast":      "hearty",     # muscle & fat -> pure recovery
    "humanoid":   "iron",       # organ-meat -> STR/HP
    "reptile":   "cold_blooded",# cold-blooded -> save vs paralyze/CON
    "dragon":     "fire",       # dragon -> fire resist
    "undead":     "drain",      # undead -> drain resist / marrow
    "demon":      "fire",       # demon -> fire resist / berserk
    "celestial":  "blessed",    # celestial -> blessed / grace
    "fey":        "regen",      # fey -> regen / SP
    "construct":  "shielded",   # construct -> shielded / physical
    "elemental":  "elemental_res", # elemental -> resist matches element
    "plant":      "regen",      # plant -> regen / SP
    "aberration": "mind",       # aberration -> mind resist
}


# ----------------------------------------------------------------------
# Outcome picker: given (tier, theme), find a matching outcome_id
# ----------------------------------------------------------------------

def load_outcomes() -> dict:
    with open(OUTCOMES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d["outcomes"].items() if not k.startswith("_")}


def pick_outcome_solo(outcomes: dict, tier: int, family: str) -> str:
    """Pick an outcome for a solo prime recipe (no dungeon adjunct)."""
    theme = FAMILY_SOLO_THEME.get(family, "hearty")
    # Prefer tier-matching outcomes with matching theme; fallback to any recovery
    candidates = _pick_by_theme(outcomes, tier, theme)
    if candidates:
        return candidates[0]
    # Fallback: any pure recovery at this tier
    return _pick_recovery(outcomes, tier)


def pick_outcome_combo(outcomes: dict, tier: int, dungeon_id: str, family: str) -> str:
    """Pick an outcome for a prime + dungeon-ingredient combo."""
    theme = DUNGEON_BUFF_FAMILY.get(dungeon_id, "hearty")
    candidates = _pick_by_theme(outcomes, tier, theme)
    if candidates:
        return candidates[0]
    return _pick_recovery(outcomes, tier)


def _pick_by_theme(outcomes: dict, tier: int, theme: str) -> list[str]:
    """Return outcome_ids at the tier that best match the theme."""
    theme_to_temp = {
        "perception":     ("searching", "dark_vision", "see_invisible"),
        "blessed":        ("blessed", "life_save"),
        "regen":          ("regenerating",),
        "poison_resist":  ("poison_resist",),
        "drain_resist":   ("drain_resist",),
        "brilliance":     ("brilliance",),
        "shielded":       ("shielded", "magic_resist"),
        "cold_resist":    ("cold_resist", "cold_shield"),
        "fire":           ("fire_resist", "fire_shield", "berserk"),
        "hearty":         (None,),  # pure recovery
        "iron":           ("shielded", "save_guard_CON", "berserk"),
        "cold_blooded":   ("save_guard_CON", "cold_resist"),
        "drain":          ("drain_resist", "life_save"),
        "elemental_res":  ("fire_resist", "cold_resist", "shock_resist"),
        "mind":           ("save_guard_WIS", "control_immune", "fear_immune"),
    }
    accepted = set(theme_to_temp.get(theme, ()))
    result = []
    for k, v in outcomes.items():
        if v.get("tier") != tier:
            continue
        # Skip trophy outcomes for solo/combo picks
        if k.startswith("trophy_"):
            continue
        tp = v.get("temp_power")
        if tp is None and None in accepted:
            result.append(k)
        elif tp in accepted:
            result.append(k)
    return sorted(result)


def _pick_recovery(outcomes: dict, tier: int) -> str:
    """Fallback: any pure-recovery outcome at this tier."""
    for k, v in outcomes.items():
        if v.get("tier") == tier and v.get("temp_power") is None and not k.startswith("trophy_"):
            return k
    # Last resort: any outcome at tier
    for k, v in outcomes.items():
        if v.get("tier") == tier and not k.startswith("trophy_"):
            return k
    return list(outcomes.keys())[0]


# ----------------------------------------------------------------------
# Name templating
# ----------------------------------------------------------------------

_STYLE_IDX = defaultdict(int)


def _template_name(monster_display: str, family: str, seed: str = "") -> str:
    """Deterministic template name for an un-signatured prime."""
    parts = PARTS_BY_FAMILY.get(family) or PARTS_BY_FAMILY["beast"]
    # Deterministic pick based on monster_id hash
    style = STYLES[hash(seed + "_s") % len(STYLES)]
    part  = parts[hash(seed + "_p") % len(parts)]
    return f"{style} {monster_display} {part}"


def _combo_name(base_name: str, dungeon_tag: str) -> str:
    return f"{base_name} {dungeon_tag}"


# ----------------------------------------------------------------------
# Flavor generator
# ----------------------------------------------------------------------

FAMILY_FLAVOR_HINTS = {
    "beast":      ["fatty and dense", "gamey and hot", "iron-rich", "muscle-marbled"],
    "humanoid":   ["lean and tough", "familiar in a bad way", "organ-rich", "salted-hard"],
    "reptile":    ["cold and clean", "smooth against the tongue", "faintly briny", "slick with fat"],
    "dragon":     ["hot even before the fire", "greasy with wyrm-fat", "faintly metallic", "deep-red and warm"],
    "undead":     ["dry until the fat renders", "surprisingly rich", "grave-cold at the middle", "old and patient"],
    "demon":      ["hot on the palate before you swallow", "bitter until it isn't", "sulfurous in the aftertaste", "red and heavy"],
    "celestial":  ["bright and clean", "warm as noon-light", "faintly sweet", "the aftertaste climbs"],
    "fey":        ["strange in the way of honey and iron", "quickens the pulse", "unsettles and steadies at once", "old-forest deep"],
    "construct":  ["mineral and dry", "grinds a little on the way down", "surprisingly satisfying", "fills like ballast"],
    "elemental":  ["a whole taste of one thing", "hums at the tongue", "impossibly pure", "singular and unrepeatable"],
    "plant":      ["green and quiet", "grassy at the edges", "with a whole forest in it", "clean as rain"],
    "aberration": ["wrong, then correct", "unsettling in a way you can't name", "textures that don't line up", "cold in three places at once"],
}

STYLE_FLAVOR = {
    "Sauteed":      "quick over high heat",
    "Roasted":      "slow in the coals",
    "Braised":      "patient in its own juices",
    "Grilled":      "flame-kissed and lightly charred",
    "Skewered":     "on a hot iron",
    "Smoked":       "under an oak-wood veil",
    "Pan-Fried":    "in its own fat",
    "Stewed":       "steady for hours",
    "Confit":       "cooked into its own oil",
    "Charred":      "hard-scorched and rough",
    "Glazed":       "shining with reduction",
    "Blackened":    "under thick spice and quick heat",
    "Pickled":      "sharp with vinegar-cure",
    "Rubbed":       "hand-salted and wet",
    "Broiled":      "under a direct high blast",
    "Poached":      "in low, still water",
    "Seared":       "quick and hot on the pan",
    "Slow-Cooked":  "hours to become tender",
}


def _flavor_solo(name: str, family: str) -> str:
    hint = random.choice(FAMILY_FLAVOR_HINTS.get(family, ["hearty"]))
    # Pull the style word if present
    style = name.split()[0] if name.split()[0] in STYLE_FLAVOR else None
    method = STYLE_FLAVOR.get(style, "prepared with care")
    return f"{method.capitalize()}; {hint}."


def _flavor_combo(name: str, family: str, dungeon_id: str) -> str:
    hint = random.choice(FAMILY_FLAVOR_HINTS.get(family, ["hearty"]))
    dungeon_bit = {
        "cave_mushroom":  "the mushroom drinks the fat and stays firm",
        "altar_incense":  "the incense hums at the edge of the taste",
        "swamp_moss":     "the moss lays down a green, quiet base",
        "river_salt":     "the salt draws out the bright edge of the meat",
        "holy_water":     "the water tempers something old in the dish",
        "crystal_shard":  "the crystal ticks against the plate as it warms",
        "deep_iron":      "the iron hums with a low, mineral warmth",
        "abyssal_kelp":   "the kelp carries the cold deep of the sea",
    }.get(dungeon_id, "the adjunct sings low under the meat")
    return f"{hint.capitalize()}; {dungeon_bit}."


# ----------------------------------------------------------------------
# Main generation
# ----------------------------------------------------------------------

def load_ingredients() -> dict:
    with open(INGREDIENTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_monsters() -> dict:
    with open(MONSTERS_PATH, encoding="utf-8") as f:
        return json.load(f)


def monster_id_from_prime_id(prime_id: str) -> str:
    """giant_rat_prime -> giant_rat"""
    if prime_id.endswith("_prime"):
        return prime_id[:-6]
    if prime_id.endswith("_trophy"):
        return prime_id[:-7]
    return prime_id


def _monster_display_name(monster_id: str, monsters: dict) -> str:
    m = monsters.get(monster_id, {})
    return (m.get("name") or monster_id.replace("_", " ")).title()


# Family recipes — hand-crafted names (12)
FAMILY_RECIPES = {
    "family_beast":      ("Hunter's Stew",              "beast",      "A working man's stew: bone-broth, root, and a good haunch."),
    "family_humanoid":   ("Camp Broth",                 "humanoid",   "Whatever was left in the pack, cooked long."),
    "family_reptile":    ("Scaled Fillet",              "reptile",    "Cold-blooded fat renders slow; the fillet stays firm."),
    "family_dragon":     ("Wyrm-Fat Stew",              "dragon",     "The fat stays warm on its own; the pot barely helps."),
    "family_undead":     ("Grave-Marrow Broth",         "undead",     "You do not think about it while it cooks."),
    "family_demon":      ("Sulfur-Spiced Roast",        "demon",      "The dish sweats on the plate; the flavor doubles down."),
    "family_celestial":  ("Golden Consecrated Stew",    "celestial",  "The steam rises straight up; it warms the whole room."),
    "family_fey":        ("Petal-Sap Reduction",        "fey",        "The color changes twice in the cooking."),
    "family_construct":  ("Gear-Grease Cake",           "construct",  "It is heavy and dense; it fills like bread."),
    "family_elemental":  ("Essence Cake",               "elemental",  "One whole taste of one whole thing."),
    "family_plant":      ("Forest Stew",                "plant",      "Grassy at the edges; you taste the whole floor."),
    "family_aberration": ("Aberrant Ichor Terrine",     "aberration", "It sets in the mold like it wants to."),
}

# Dungeon-ingredient utility recipes (~8)
DUNGEON_UTILITY_RECIPES = {
    "u_mushroom_tea":   ("Mushroom Tea",                ["cave_mushroom"],     "t1_snack_perception",    "The mushroom gives up its earth-notes to the hot water; the eye clears."),
    "u_salted_kelp":    ("Salted Kelp Broth",           ["abyssal_kelp",       "river_salt"], "t2_meal_cold_resist", "The kelp holds the salt; the salt holds the cold at bay."),
    "u_holy_broth":     ("Holy Water Consomme",         ["holy_water"],        "t2_meal_dark_grace",     "Clear and warm; a small brightness carries in the drinking."),
    "u_incense_tea":    ("Altar-Incense Infusion",      ["altar_incense"],     "t1_snack_blessed",       "The smoke lingers; the grace lingers a beat longer."),
    "u_moss_broth":     ("Swamp-Moss Broth",            ["swamp_moss"],        "t1_snack_regen_tick",    "Green and quiet; wounds knit under the surface for a while."),
    "u_crystal_tonic":  ("Crystal Infusion",            ["crystal_shard"],     "t2_meal_reflecting",     "The crystal warms in the cup; light seems to slide off you afterward."),
    "u_iron_broth":     ("Deep-Iron Broth",             ["deep_iron"],         "t2_meal_shielded",       "Mineral and low; the frame sets against harm."),
    "u_kelp_broth":     ("Abyssal Kelp Broth",          ["abyssal_kelp"],      "t3_meal_cold_resist",    "The deep cold of the trench carries in the broth; the flesh answers."),
}


def build_all_recipes():
    outcomes = load_outcomes()
    ingredients = load_ingredients()
    monsters = load_monsters()
    primes = json.load(open(PRIME_CUTS_PATH, encoding="utf-8"))["primes"]

    recipes: dict = {}

    # 1. Utility recipes
    for rid, (name, ings, outcome_id, flavor) in DUNGEON_UTILITY_RECIPES.items():
        recipes[rid] = {
            "name": name,
            "ingredients": ings,
            "outcome_id": outcome_id,
            "flavor": flavor,
        }

    # 2. Family recipes (12)
    for fam_ing_id, (name, family, flavor) in FAMILY_RECIPES.items():
        rid = f"{fam_ing_id}_recipe"
        # Family recipes: 2x family + 4x assorted (matches the tests)
        ings = [fam_ing_id, fam_ing_id,
                "assorted_monster_parts", "assorted_monster_parts",
                "assorted_monster_parts", "assorted_monster_parts"]
        # Pick T2 family-themed outcome
        outcome_id = pick_outcome_solo(outcomes, tier=2, family=family)
        recipes[rid] = {
            "name": name,
            "ingredients": ings,
            "outcome_id": outcome_id,
            "flavor": flavor,
        }

    # 3. Trophy recipes (14)
    TROPHY_ID_TO_OUTCOME = {
        "asterion_minotaur_trophy":   "trophy_asterion",
        "medusa_gorgon_trophy":       "trophy_medusa",
        "fafnir_dragon_trophy":       "trophy_fafnir",
        "fenrir_wolf_trophy":         "trophy_fenrir",
        "abaddon_destroyer_trophy":   "trophy_abaddon",
        "green_knight_trophy":        "trophy_green_knight",
        "nidhoggr_fragment_trophy":   "trophy_nidhoggr",
        "whispering_crone_trophy":    "trophy_whispering_crone",
        "blood_archon_trophy":        "trophy_blood_archon",
        "tiamat_trophy":              "trophy_tiamat",
        "asmodeus_trophy":            "trophy_asmodeus",
        "surtur_trophy":              "trophy_surtur",
        "ymir_last_spawn_trophy":     "trophy_ymir",
        "hrungnirs_ghost_trophy":     "trophy_hrungnir",
    }
    # Trophy names are read from the outcome catalog's desc field prefix ("Crown of the Labyrinth — ...")
    for trophy_ing_id, outcome_id in TROPHY_ID_TO_OUTCOME.items():
        rid = f"trophy_{trophy_ing_id.replace('_trophy','')}_recipe"
        # Trophy recipes: 1x trophy + 2x family + 5x assorted
        ing_def = ingredients.get(trophy_ing_id, {})
        family = ing_def.get("family", "beast")
        family_ing = f"family_{family}"
        ings = [trophy_ing_id, family_ing, family_ing,
                "assorted_monster_parts", "assorted_monster_parts",
                "assorted_monster_parts", "assorted_monster_parts",
                "assorted_monster_parts"]
        # Extract the display name from the outcome's desc
        outcome = outcomes.get(outcome_id, {})
        desc = outcome.get("desc", "")
        display = desc.split(" — ")[0] if " — " in desc else ing_def.get("name", trophy_ing_id).replace("'s", "'s Dish")
        recipes[rid] = {
            "name": display,
            "ingredients": ings,
            "outcome_id": outcome_id,
            "flavor": desc,
        }

    # 4. Solo prime recipes (~516)
    for prime_ing_id, ing_def in ingredients.items():
        if ing_def.get("tier_role") != "prime":
            continue
        monster_id = monster_id_from_prime_id(prime_ing_id)
        family = ing_def.get("family", "beast")
        ml = int(ing_def.get("min_level", 1))
        tier = tier_from_ml(ml)
        display = _monster_display_name(monster_id, monsters)

        # Signature name if we curated one; otherwise template
        sig = SIGNATURE.get(monster_id)
        if sig:
            name = sig["solo"]
        else:
            name = _template_name(display, family, seed=monster_id)

        outcome_id = pick_outcome_solo(outcomes, tier, family)
        rid = f"prime_{monster_id}_recipe"
        recipes[rid] = {
            "name": name,
            "ingredients": [prime_ing_id, "assorted_monster_parts", "assorted_monster_parts"],
            "outcome_id": outcome_id,
            "flavor": _flavor_solo(name, family),
        }

    # 5. Combo recipes: signature primes × dungeon ingredients
    # Each signature monster gets 2 combos with thematic pairings.
    COMBO_PAIRINGS = [
        ("cave_mushroom",  1),  # T1 pairing (mushroom is ml=1)
        ("river_salt",     2),  # T2 pairing
        ("swamp_moss",     1),  # T1
        ("holy_water",     2),  # T2
        ("crystal_shard",  2),  # T2
        ("deep_iron",      3),  # T3
        ("altar_incense",  1),  # T1
        ("abyssal_kelp",   3),  # T3
    ]
    # Rotate pairings across signature monsters so each has 2 distinct combos.
    sig_list = list(SIGNATURE.keys())
    for i, sig_id in enumerate(sig_list):
        prime_id = f"{sig_id}_prime"
        if prime_id not in ingredients:
            continue
        ing_def = ingredients[prime_id]
        family = ing_def.get("family", "beast")
        ml = int(ing_def.get("min_level", 1))
        solo_tier = tier_from_ml(ml)
        # Pick 2 dungeon ingredients rotating around the list
        for combo_idx in (0, 1):
            dungeon_id, combo_bonus = COMBO_PAIRINGS[(i + combo_idx * 3) % len(COMBO_PAIRINGS)]
            dungeon_def = ingredients.get(dungeon_id, {})
            dungeon_ml = int(dungeon_def.get("min_level", 1))
            combo_tier = max(solo_tier, tier_from_ml(dungeon_ml))
            # Complexity bonus: combo recipes are ~1 tier higher than solo
            combo_tier = min(5, combo_tier + (1 if solo_tier <= 3 else 0))
            outcome_id = pick_outcome_combo(outcomes, combo_tier, dungeon_id, family)
            base_name = SIGNATURE[sig_id]["solo"]
            name = _combo_name(base_name, DUNGEON_TAG[dungeon_id])
            rid = f"combo_{sig_id}_{dungeon_id}_recipe"
            recipes[rid] = {
                "name": name,
                "ingredients": [prime_id, dungeon_id, "assorted_monster_parts"],
                "outcome_id": outcome_id,
                "flavor": _flavor_combo(name, family, dungeon_id),
            }

    return recipes


def main():
    recipes = build_all_recipes()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=True, indent=1)
    print(f"wrote {len(recipes)} recipes to {OUT_PATH}")
    # Summary
    from collections import Counter
    by_prefix = Counter()
    for rid in recipes:
        prefix = rid.split("_")[0]
        by_prefix[prefix] += 1
    print("by prefix:", dict(by_prefix))


if __name__ == "__main__":
    main()
