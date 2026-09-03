"""v2.6.5 recipe regeneration (2026-09-03).

Bottom-up rebuild for the option-1 ingredient model (one ingredient per
monster, no assorted, no family cuts).

Recipes:
  * Solo prime: 1 prime -> outcome. ~516 recipes.
  * Combo: 1 prime + 1 dungeon adjunct -> outcome (thematic buff from adjunct).
    ~30 signature monsters x 2 adjuncts = ~60 recipes.
  * Family: 3 same-family monsters -> outcome. 12 recipes (Hunter's Stew etc).
    Ingredient list uses the family's canonical roster (3 members from that family).
  * Trophy: 1 trophy alone -> outcome. 14 recipes.
  * Utility: dungeon adjunct(s) -> outcome. 8 recipes.

Each recipe references an outcome_id from data/items/cook_outcomes.json.
The outcome's tier IS the cook Q tier. The harvest Q tier is separately
derived from the monster's harvest_tier.
"""
import json
import os
import random
from collections import defaultdict

random.seed(20260903)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGREDIENTS_PATH = os.path.join(ROOT, "data", "items", "ingredient.json")
OUTCOMES_PATH    = os.path.join(ROOT, "data", "items", "cook_outcomes.json")
MONSTERS_PATH    = os.path.join(ROOT, "data", "monsters.json")
OUT_PATH         = os.path.join(ROOT, "data", "items", "recipes.json")


def tier_from_ml(ml: int) -> int:
    if ml <= 15: return 1
    if ml <= 35: return 2
    if ml <= 55: return 3
    if ml <= 80: return 4
    return 5


STYLES = [
    "Sauteed", "Roasted", "Braised", "Grilled", "Skewered", "Smoked",
    "Pan-Fried", "Stewed", "Confit", "Charred", "Glazed", "Blackened",
    "Pickled", "Rubbed", "Broiled", "Poached", "Seared", "Slow-Cooked",
]

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
}


DUNGEON_BUFF_FAMILY = {
    "cave_mushroom":   "perception",
    "altar_incense":   "blessed",
    "swamp_moss":      "regen",
    "river_salt":      "poison_resist",
    "holy_water":      "drain_resist",
    "crystal_shard":   "brilliance",
    "deep_iron":       "shielded",
    "abyssal_kelp":    "cold_resist",
}

FAMILY_SOLO_THEME = {
    "beast":      "hearty",
    "humanoid":   "iron",
    "reptile":    "cold_blooded",
    "dragon":     "fire",
    "undead":     "drain",
    "demon":      "fire",
    "celestial":  "blessed",
    "fey":        "regen",
    "construct":  "shielded",
    "elemental":  "elemental_res",
    "plant":      "regen",
    "aberration": "mind",
}


def load_outcomes():
    with open(OUTCOMES_PATH, encoding="utf-8") as f:
        return {k: v for k, v in json.load(f)["outcomes"].items() if not k.startswith("_")}


def _pick_by_theme(outcomes, tier, theme):
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
        "hearty":         (None,),
        "iron":           ("shielded", "save_guard_CON", "berserk"),
        "cold_blooded":   ("save_guard_CON", "cold_resist"),
        "drain":          ("drain_resist", "life_save"),
        "elemental_res":  ("fire_resist", "cold_resist", "shock_resist"),
        "mind":           ("save_guard_WIS", "control_immune", "fear_immune"),
    }
    accepted = set(theme_to_temp.get(theme, ()))
    result = []
    for k, v in outcomes.items():
        if v.get("tier") != tier: continue
        if k.startswith("trophy_"): continue
        tp = v.get("temp_power")
        if tp is None and None in accepted:
            result.append(k)
        elif tp in accepted:
            result.append(k)
    return sorted(result)


def _pick_recovery(outcomes, tier):
    for k, v in outcomes.items():
        if v.get("tier") == tier and v.get("temp_power") is None and not k.startswith("trophy_"):
            return k
    for k, v in outcomes.items():
        if v.get("tier") == tier and not k.startswith("trophy_"):
            return k
    return list(outcomes.keys())[0]


def pick_outcome_solo(outcomes, tier, family):
    theme = FAMILY_SOLO_THEME.get(family, "hearty")
    c = _pick_by_theme(outcomes, tier, theme)
    return c[0] if c else _pick_recovery(outcomes, tier)


def pick_outcome_combo(outcomes, tier, dungeon_id, family):
    theme = DUNGEON_BUFF_FAMILY.get(dungeon_id, "hearty")
    c = _pick_by_theme(outcomes, tier, theme)
    return c[0] if c else _pick_recovery(outcomes, tier)


def _template_name(monster_display, family, seed=""):
    parts = PARTS_BY_FAMILY.get(family) or PARTS_BY_FAMILY["beast"]
    style = STYLES[hash(seed + "_s") % len(STYLES)]
    part  = parts[hash(seed + "_p") % len(parts)]
    return f"{style} {monster_display} {part}"


def _combo_name(base_name, dungeon_tag):
    return f"{base_name} {dungeon_tag}"


FAMILY_FLAVOR_HINTS = {
    "beast":      ["fatty and dense", "gamey and hot", "iron-rich", "muscle-marbled"],
    "humanoid":   ["lean and tough", "familiar in a bad way", "organ-rich", "salted-hard"],
    "reptile":    ["cold and clean", "smooth against the tongue", "faintly briny", "slick with fat"],
    "dragon":     ["hot even before the fire", "greasy with wyrm-fat", "faintly metallic", "deep-red and warm"],
    "undead":     ["dry until the fat renders", "surprisingly rich", "grave-cold at the middle", "old and patient"],
    "demon":      ["hot on the palate", "bitter until it isn't", "sulfurous in the aftertaste", "red and heavy"],
    "celestial":  ["bright and clean", "warm as noon-light", "faintly sweet", "the aftertaste climbs"],
    "fey":        ["strange in the way of honey and iron", "quickens the pulse", "unsettles and steadies", "old-forest deep"],
    "construct":  ["mineral and dry", "grinds a little on the way down", "fills like ballast", "surprisingly satisfying"],
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


def _flavor_solo(name, family):
    hint = random.choice(FAMILY_FLAVOR_HINTS.get(family, ["hearty"]))
    style = name.split()[0] if name.split()[0] in STYLE_FLAVOR else None
    method = STYLE_FLAVOR.get(style, "prepared with care")
    return f"{method.capitalize()}; {hint}."


def _flavor_combo(name, family, dungeon_id):
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


def load_ingredients():
    with open(INGREDIENTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_monsters():
    with open(MONSTERS_PATH, encoding="utf-8") as f:
        return json.load(f)


def monster_id_from_prime(prime_id):
    if prime_id.endswith("_prime"):  return prime_id[:-6]
    if prime_id.endswith("_trophy"): return prime_id[:-7]
    return prime_id


def _display(monster_id, monsters):
    m = monsters.get(monster_id, {})
    return (m.get("name") or monster_id.replace("_", " ")).title()


# Family recipes — hand-crafted; ingredients = 3 same-family monsters
# (any 3 canonical members from that family that the player can readily
# find in early-mid game).
FAMILY_RECIPES = {
    "beast":      ("Hunter's Stew",           "A working man's stew: three beasts of the field, slow-cooked with root and bone."),
    "humanoid":   ("Camp Broth",              "Three humanoid cuts, slow-simmered; whatever the pack could carry."),
    "reptile":    ("Scaled Trio Fillet",      "Three cold-blooded fillets, layered and pan-seared; the fat renders clean."),
    "dragon":     ("Wyrm-Fat Stew",           "Three cuts of dragonkind rendered slow together; the fat stays warm on its own."),
    "undead":     ("Grave-Marrow Broth",      "Three undead cuts boiled to marrow; you do not think about it while it cooks."),
    "demon":      ("Sulfur-Spiced Roast",     "Three demonic cuts hard-charred over open flame; the dish sweats on the plate."),
    "celestial":  ("Golden Consecrated Stew", "Three celestial cuts; the steam rises straight up and warms the whole room."),
    "fey":        ("Petal-Sap Reduction",     "Three fey cuts reduced into a thin bright syrup; the color changes twice."),
    "construct":  ("Gear-Grease Cake",        "Three construct scraps rendered into a heavy, dense cake; fills like bread."),
    "elemental":  ("Essence Cake",            "Three elemental cores baked together; one whole taste of one whole thing."),
    "plant":      ("Forest Stew",             "Three plant cuts; grassy at the edges, with a whole forest in it."),
    "aberration": ("Aberrant Ichor Terrine",  "Three aberrant cuts set in a cold terrine; it wants to be in the mold."),
}


# Utility (dungeon-only) recipes
DUNGEON_UTILITY_RECIPES = {
    "u_mushroom_tea":   ("Mushroom Tea",           ["cave_mushroom"],                    "t1_snack_perception", "The mushroom gives up its earth-notes; the eye clears."),
    "u_salted_kelp":    ("Salted Kelp Broth",      ["abyssal_kelp", "river_salt"],       "t2_meal_cold_resist", "The kelp holds the salt; the salt holds the cold at bay."),
    "u_holy_broth":     ("Holy Water Consomme",    ["holy_water"],                       "t2_meal_dark_grace",  "Clear and warm; a small brightness carries in the drinking."),
    "u_incense_tea":    ("Altar-Incense Infusion", ["altar_incense"],                    "t1_snack_blessed",    "The smoke lingers; the grace lingers a beat longer."),
    "u_moss_broth":     ("Swamp-Moss Broth",       ["swamp_moss"],                       "t1_snack_regen_tick", "Green and quiet; wounds knit under the surface for a while."),
    "u_crystal_tonic":  ("Crystal Infusion",       ["crystal_shard"],                    "t2_meal_reflecting",  "The crystal warms in the cup; light seems to slide off you afterward."),
    "u_iron_broth":     ("Deep-Iron Broth",        ["deep_iron"],                        "t2_meal_shielded",    "Mineral and low; the frame sets against harm."),
    "u_kelp_broth":     ("Abyssal Kelp Broth",     ["abyssal_kelp"],                     "t3_meal_cold_resist", "The deep cold of the trench carries in the broth; the flesh answers."),
}


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


def build_all_recipes():
    outcomes = load_outcomes()
    ingredients = load_ingredients()
    monsters = load_monsters()

    recipes = {}

    # 1. Utility recipes (dungeon-only)
    for rid, (name, ings, outcome_id, flavor) in DUNGEON_UTILITY_RECIPES.items():
        recipes[rid] = {"name": name, "ingredients": ings, "outcome_id": outcome_id, "flavor": flavor}

    # 2. Family recipes — 3 same-family monsters
    # Pick 3 canonical early-mid game monsters from each family.
    family_members = defaultdict(list)
    for ing_id, ing_def in ingredients.items():
        if ing_def.get("tier_role") != "prime":
            continue
        fam = ing_def.get("family")
        ml = int(ing_def.get("min_level", 999))
        family_members[fam].append((ing_id, ml))
    # Sort by ml so we pick the 3 shallowest members (easiest to collect).
    for fam in family_members:
        family_members[fam].sort(key=lambda x: x[1])

    for fam, (name, flavor) in FAMILY_RECIPES.items():
        rid = f"family_{fam}_recipe"
        members = family_members.get(fam, [])
        if len(members) < 3:
            # Not enough distinct members; fall back to whatever exists
            ings = [m[0] for m in members] or ["assorted_monster_parts"]
        else:
            ings = [m[0] for m in members[:3]]
        outcome_id = pick_outcome_solo(outcomes, tier=2, family=fam)
        recipes[rid] = {"name": name, "ingredients": ings, "outcome_id": outcome_id, "flavor": flavor}

    # 3. Trophy recipes — 1 trophy alone
    for trophy_ing_id, outcome_id in TROPHY_ID_TO_OUTCOME.items():
        rid = f"trophy_{trophy_ing_id.replace('_trophy', '')}_recipe"
        outcome = outcomes.get(outcome_id, {})
        desc = outcome.get("desc", "")
        display = desc.split(" — ")[0] if " — " in desc else "Boss Trophy Dish"
        recipes[rid] = {
            "name": display,
            "ingredients": [trophy_ing_id],
            "outcome_id": outcome_id,
            "flavor": desc,
        }

    # 4. Solo prime recipes (~516) — 1 prime alone
    for prime_ing_id, ing_def in ingredients.items():
        if ing_def.get("tier_role") != "prime":
            continue
        monster_id = monster_id_from_prime(prime_ing_id)
        family = ing_def.get("family", "beast")
        ml = int(ing_def.get("min_level", 1))
        tier = tier_from_ml(ml)
        display = _display(monster_id, monsters)
        sig = SIGNATURE.get(monster_id)
        name = sig["solo"] if sig else _template_name(display, family, seed=monster_id)
        outcome_id = pick_outcome_solo(outcomes, tier, family)
        rid = f"prime_{monster_id}_recipe"
        recipes[rid] = {
            "name": name,
            "ingredients": [prime_ing_id],
            "outcome_id": outcome_id,
            "flavor": _flavor_solo(name, family),
        }

    # 5. Combo recipes: signature primes x dungeon ingredients (~60)
    COMBO_PAIRINGS = [
        ("cave_mushroom",  1),
        ("river_salt",     2),
        ("swamp_moss",     1),
        ("holy_water",     2),
        ("crystal_shard",  2),
        ("deep_iron",      3),
        ("altar_incense",  1),
        ("abyssal_kelp",   3),
    ]
    sig_list = list(SIGNATURE.keys())
    for i, sig_id in enumerate(sig_list):
        prime_id = f"{sig_id}_prime"
        if prime_id not in ingredients:
            continue
        ing_def = ingredients[prime_id]
        family = ing_def.get("family", "beast")
        ml = int(ing_def.get("min_level", 1))
        solo_tier = tier_from_ml(ml)
        for combo_idx in (0, 1):
            dungeon_id, _ = COMBO_PAIRINGS[(i + combo_idx * 3) % len(COMBO_PAIRINGS)]
            dungeon_def = ingredients.get(dungeon_id, {})
            dungeon_ml = int(dungeon_def.get("min_level", 1))
            combo_tier = max(solo_tier, tier_from_ml(dungeon_ml))
            combo_tier = min(5, combo_tier + (1 if solo_tier <= 3 else 0))
            outcome_id = pick_outcome_combo(outcomes, combo_tier, dungeon_id, family)
            base_name = SIGNATURE[sig_id]["solo"]
            name = _combo_name(base_name, DUNGEON_TAG[dungeon_id])
            rid = f"combo_{sig_id}_{dungeon_id}_recipe"
            recipes[rid] = {
                "name": name,
                "ingredients": [prime_id, dungeon_id],
                "outcome_id": outcome_id,
                "flavor": _flavor_combo(name, family, dungeon_id),
            }

    return recipes


def main():
    recipes = build_all_recipes()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=True, indent=1)
    print(f"wrote {len(recipes)} recipes to {OUT_PATH}")
    from collections import Counter
    prefix = Counter(rid.split("_")[0] for rid in recipes)
    print("by prefix:", dict(prefix))


if __name__ == "__main__":
    main()
