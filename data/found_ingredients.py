"""Add found ingredients (herbs, vegetables, fungi, spices) to ingredient.json."""
import json, os

FOUND = {
    # ── Herbs ──────────────────────────────────────────────────────────────
    "wild_thyme": {
        "name": "wild thyme",
        "symbol": ",",
        "color": [160, 200, 120],
        "weight": 0.5,
        "min_level": 1,
        "source_monster": "",
        "floor_spawn_weight": {"1": 4, "2": 4, "3": 3, "4": 2, "5": 2},
        "lore": "A hardy aromatic herb that grows in the cracks of dungeon walls. Cooks prize it as a versatile flavoring that subtly sharpens the senses.",
        "recipes": {
            "0": {"name": "scorched thyme crumbles",      "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "thyme-steeped water",          "sp": 10,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "thyme broth",                  "sp": 22,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "herbed thyme infusion",        "sp": 38,  "bonus_type": "stat",  "bonus_stat": "WIS", "bonus_amount": 1},
            "4": {"name": "aromatic thyme reduction",     "sp": 55,  "bonus_type": "stat",  "bonus_stat": "WIS", "bonus_amount": 1},
            "5": {"name": "essence of wild thyme",        "sp": 75,  "bonus_type": "stat",  "bonus_stat": "WIS", "bonus_amount": 2}
        }
    },
    "rosemary_sprig": {
        "name": "rosemary sprig",
        "symbol": ",",
        "color": [100, 170, 90],
        "weight": 0.4,
        "min_level": 1,
        "source_monster": "",
        "floor_spawn_weight": {"1": 3, "2": 3, "3": 3, "4": 2, "5": 1},
        "lore": "A woody-stemmed herb whose resinous scent has been known to ward off minor hexes. Adventurers crush it in their palms before entering cursed chambers.",
        "recipes": {
            "0": {"name": "charred rosemary ash",         "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "rosemary steam",               "sp": 12,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "rosemary tisane",              "sp": 25,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "fortifying rosemary brew",     "sp": 42,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 1},
            "4": {"name": "resinous rosemary draught",    "sp": 60,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 1},
            "5": {"name": "rosemary clarity elixir",      "sp": 80,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 2}
        }
    },
    "valerian_root": {
        "name": "valerian root",
        "symbol": ",",
        "color": [180, 150, 100],
        "weight": 1.0,
        "min_level": 2,
        "source_monster": "",
        "floor_spawn_weight": {"2": 3, "3": 3, "4": 3, "5": 2, "6": 2},
        "lore": "A gnarled root with sedative properties. Herbalists dry and powder it to calm nerves; master cooks transmute it into a potent focus-enhancing tonic.",
        "recipes": {
            "0": {"name": "ruined valerian mash",         "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "valerian root tea",            "sp": 15,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "valerian root decoction",      "sp": 30,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "nerve-calming root brew",      "sp": 50,  "bonus_type": "stat",  "bonus_stat": "INT", "bonus_amount": 1},
            "4": {"name": "valerian focus potion",        "sp": 70,  "bonus_type": "stat",  "bonus_stat": "INT", "bonus_amount": 1},
            "5": {"name": "supreme valerian distillate",  "sp": 95,  "bonus_type": "stat",  "bonus_stat": "INT", "bonus_amount": 2}
        }
    },
    "nightshade_leaf": {
        "name": "nightshade leaf",
        "symbol": ",",
        "color": [80, 40, 120],
        "weight": 0.5,
        "min_level": 3,
        "source_monster": "",
        "floor_spawn_weight": {"3": 2, "4": 3, "5": 3, "6": 3, "7": 2},
        "lore": "A deep-violet leaf from a poisonous plant. In small, precisely cooked doses it sharpens reflexes to a razor edge—but miscalculate and the result is lethal.",
        "recipes": {
            "0": {"name": "toxic nightshade mush",        "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "nightshade tisane",            "sp": 18,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "shadow leaf reduction",        "sp": 35,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "assassin's reflex tonic",      "sp": 55,  "bonus_type": "stat",  "bonus_stat": "DEX", "bonus_amount": 1},
            "4": {"name": "midnight grace elixir",        "sp": 80,  "bonus_type": "stat",  "bonus_stat": "DEX", "bonus_amount": 2},
            "5": {"name": "ultimate shadow distillate",   "sp": 110, "bonus_type": "two_stats", "bonus_amount": 2}
        }
    },
    "mandrake_root": {
        "name": "mandrake root",
        "symbol": ",",
        "color": [160, 120, 80],
        "weight": 2.0,
        "min_level": 4,
        "source_monster": "",
        "floor_spawn_weight": {"4": 2, "5": 2, "6": 2, "7": 2, "8": 2},
        "lore": "A humanoid-shaped root infamous for its screech when pulled. Ground and slow-roasted by an expert cook, it imparts a formidable boost to raw physical power.",
        "recipes": {
            "0": {"name": "screaming mandrake paste",     "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "mandrake root broth",          "sp": 22,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "slow-roasted mandrake",        "sp": 45,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "mandrake strength cordial",    "sp": 70,  "bonus_type": "stat",  "bonus_stat": "STR", "bonus_amount": 1},
            "4": {"name": "titan root reduction",         "sp": 100, "bonus_type": "stat",  "bonus_stat": "STR", "bonus_amount": 2},
            "5": {"name": "mandrake's ancient essence",   "sp": 135, "bonus_type": "combat_stat", "bonus_amount": 2}
        }
    },
    # ── Vegetables ─────────────────────────────────────────────────────────
    "cave_mushroom": {
        "name": "cave mushroom",
        "symbol": ",",
        "color": [200, 190, 170],
        "weight": 1.0,
        "min_level": 1,
        "source_monster": "",
        "floor_spawn_weight": {"1": 5, "2": 5, "3": 4, "4": 3, "5": 2},
        "lore": "A pale, plump mushroom grown in the darkness of deep caverns. Bland on its own, but a skilled cook can render it into a surprisingly nourishing meal.",
        "recipes": {
            "0": {"name": "slimey mushroom pulp",         "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "cave mushroom soup",           "sp": 12,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "sautéed cave mushrooms",       "sp": 25,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "mushroom risotto",             "sp": 42,  "bonus_type": "none",  "bonus_amount": 0},
            "4": {"name": "truffle-style cave medley",    "sp": 62,  "bonus_type": "random_stat", "bonus_amount": 1},
            "5": {"name": "chef's cave mushroom feast",   "sp": 85,  "bonus_type": "random_stat", "bonus_amount": 1}
        }
    },
    "pale_celery": {
        "name": "pale celery",
        "symbol": ",",
        "color": [210, 225, 190],
        "weight": 0.8,
        "min_level": 1,
        "source_monster": "",
        "floor_spawn_weight": {"1": 4, "2": 4, "3": 3, "4": 2, "5": 1},
        "lore": "Etiolated celery stalks that grow in underground streams. Water-rich and faintly bitter, they form the base of many dungeon soups.",
        "recipes": {
            "0": {"name": "withered celery mush",         "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "celery water",                 "sp": 8,   "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "pale celery broth",            "sp": 18,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "dungeon celery bisque",        "sp": 32,  "bonus_type": "none",  "bonus_amount": 0},
            "4": {"name": "vitality celery cream",        "sp": 48,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 1},
            "5": {"name": "pale celery ambrosia",         "sp": 68,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 1}
        }
    },
    "cave_carrot": {
        "name": "cave carrot",
        "symbol": ",",
        "color": [220, 140, 60],
        "weight": 0.8,
        "min_level": 2,
        "source_monster": "",
        "floor_spawn_weight": {"2": 4, "3": 4, "4": 3, "5": 2, "6": 1},
        "lore": "Orange roots that somehow flourish in dimly lit passages. Rich in subterranean minerals, they are said to grant keen eyesight in the dark.",
        "recipes": {
            "0": {"name": "charred carrot stump",         "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "cave carrot soup",             "sp": 14,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "glazed cave carrots",          "sp": 28,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "miner's carrot stew",          "sp": 45,  "bonus_type": "stat",  "bonus_stat": "PER", "bonus_amount": 1},
            "4": {"name": "eagle-eye carrot bisque",      "sp": 62,  "bonus_type": "stat",  "bonus_stat": "PER", "bonus_amount": 1},
            "5": {"name": "far-seer's carrot elixir",     "sp": 85,  "bonus_type": "stat",  "bonus_stat": "PER", "bonus_amount": 2}
        }
    },
    # ── Fungi ───────────────────────────────────────────────────────────────
    "glowing_spore": {
        "name": "glowing spore",
        "symbol": ",",
        "color": [140, 230, 180],
        "weight": 0.3,
        "min_level": 2,
        "source_monster": "",
        "floor_spawn_weight": {"2": 3, "3": 3, "4": 3, "5": 2, "6": 2, "7": 1},
        "lore": "A bioluminescent spore cluster that pulses with soft blue-green light. Ingesting it in a refined preparation briefly heightens magical sensitivity.",
        "recipes": {
            "0": {"name": "burst spore mess",             "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "spore extract",                "sp": 12,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "luminescent broth",            "sp": 28,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "glowcap reduction",            "sp": 45,  "bonus_type": "stat",  "bonus_stat": "INT", "bonus_amount": 1},
            "4": {"name": "arcane spore infusion",        "sp": 65,  "bonus_type": "stat",  "bonus_stat": "INT", "bonus_amount": 1},
            "5": {"name": "radiant spore essence",        "sp": 90,  "bonus_type": "two_stats", "bonus_amount": 1}
        }
    },
    "crimson_fungus": {
        "name": "crimson fungus",
        "symbol": ",",
        "color": [200, 60, 60],
        "weight": 0.5,
        "min_level": 3,
        "source_monster": "",
        "floor_spawn_weight": {"3": 2, "4": 3, "5": 3, "6": 3, "7": 2, "8": 1},
        "lore": "Blood-red caps with a fiery bite. Herbalists warn never to eat these raw—the toxins must be rendered harmless through careful cooking before the energizing compounds can be safely absorbed.",
        "recipes": {
            "0": {"name": "poisonous crimson pulp",       "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "detoxified crimson broth",     "sp": 18,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "flame-cap consommé",           "sp": 35,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "blood-cap reduction",          "sp": 55,  "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 15},
            "4": {"name": "crimson vitality elixir",      "sp": 80,  "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 25},
            "5": {"name": "dragonblood fungus essence",   "sp": 110, "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 40}
        }
    },
    "petrified_mushroom": {
        "name": "petrified mushroom",
        "symbol": ",",
        "color": [160, 160, 140],
        "weight": 3.0,
        "min_level": 5,
        "source_monster": "",
        "floor_spawn_weight": {"5": 2, "6": 2, "7": 2, "8": 2, "9": 2, "10": 1},
        "lore": "Ancient fungi turned to near-stone over centuries of mineral exposure. Ground to a fine dust and boiled, they yield a broth of remarkable fortifying properties.",
        "recipes": {
            "0": {"name": "crumbled stone dust",          "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "mineral mushroom broth",       "sp": 25,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "stone-cap stock",              "sp": 50,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "petrified essence reduction",  "sp": 80,  "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 1},
            "4": {"name": "granite-heart pottage",        "sp": 115, "bonus_type": "stat",  "bonus_stat": "CON", "bonus_amount": 2},
            "5": {"name": "ancient stone-cap ambrosia",   "sp": 155, "bonus_type": "combat_stat", "bonus_amount": 2}
        }
    },
    # ── Spices ──────────────────────────────────────────────────────────────
    "ember_spice": {
        "name": "ember spice",
        "symbol": ",",
        "color": [240, 120, 40],
        "weight": 0.3,
        "min_level": 2,
        "source_monster": "",
        "floor_spawn_weight": {"2": 3, "3": 3, "4": 3, "5": 2, "6": 2},
        "lore": "Tiny flakes of solidified volcanic mineral, glowing faintly orange. Sprinkled into a dish they intensify flavors and imbue a transient heat-resistance.",
        "recipes": {
            "0": {"name": "scorched ember dust",          "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "ember spice tea",              "sp": 10,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "spiced ember broth",           "sp": 22,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "ember-fire reduction",         "sp": 36,  "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 12},
            "4": {"name": "flameheart spice elixir",      "sp": 52,  "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 20},
            "5": {"name": "volcano's breath draught",     "sp": 72,  "bonus_type": "status", "bonus_effect": "fire_shield", "bonus_amount": 30}
        }
    },
    "serpent_pepper": {
        "name": "serpent pepper",
        "symbol": ",",
        "color": [60, 160, 60],
        "weight": 0.2,
        "min_level": 3,
        "source_monster": "",
        "floor_spawn_weight": {"3": 3, "4": 3, "5": 3, "6": 2, "7": 2},
        "lore": "A slender, venomously-hot pepper found near serpent dens. Cooking neutralizes its toxins and leaves behind a compound that sharpens dexterity for hours.",
        "recipes": {
            "0": {"name": "toxic pepper mash",            "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "serpent pepper sauce",         "sp": 12,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "serpent-fire reduction",       "sp": 25,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "viper-heat condiment",         "sp": 40,  "bonus_type": "stat",  "bonus_stat": "DEX", "bonus_amount": 1},
            "4": {"name": "serpent grace elixir",         "sp": 58,  "bonus_type": "stat",  "bonus_stat": "DEX", "bonus_amount": 1},
            "5": {"name": "snake-fire supreme draught",   "sp": 80,  "bonus_type": "stat",  "bonus_stat": "DEX", "bonus_amount": 2}
        }
    },
    "void_salt": {
        "name": "void salt",
        "symbol": ",",
        "color": [60, 60, 80],
        "weight": 0.2,
        "min_level": 7,
        "source_monster": "",
        "floor_spawn_weight": {"7": 2, "8": 2, "9": 2, "10": 2, "11": 2, "12": 1},
        "lore": "Crystallized residue from extra-planar rifts. A grain transforms any dish into something otherworldly—and grants brief resistance to necrotic energies.",
        "recipes": {
            "0": {"name": "dissolved void crystals",      "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "void-salt infusion",           "sp": 20,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "planar salt reduction",        "sp": 40,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "void-salt tincture",           "sp": 65,  "bonus_type": "status", "bonus_effect": "death_ward", "bonus_amount": 15},
            "4": {"name": "abyss-salt elixir",            "sp": 95,  "bonus_type": "status", "bonus_effect": "death_ward", "bonus_amount": 25},
            "5": {"name": "primordial void essence",      "sp": 130, "bonus_type": "two_stats", "bonus_amount": 2}
        }
    },
    "dragon_salt": {
        "name": "dragon salt",
        "symbol": ",",
        "color": [255, 200, 80],
        "weight": 0.3,
        "min_level": 8,
        "source_monster": "",
        "floor_spawn_weight": {"8": 2, "9": 2, "10": 2, "11": 2, "12": 2, "13": 1},
        "lore": "Crystalline deposits found only in dragon lairs, formed when draconic flame meets limestone. Chefs who master its use produce meals of legendary restorative power.",
        "recipes": {
            "0": {"name": "crumbled dragon crust",        "sp": 0,   "bonus_type": "none",  "bonus_amount": 0},
            "1": {"name": "dragon-salt broth",            "sp": 30,  "bonus_type": "none",  "bonus_amount": 0},
            "2": {"name": "draconic salt consommé",       "sp": 60,  "bonus_type": "none",  "bonus_amount": 0},
            "3": {"name": "elder salt reduction",         "sp": 95,  "bonus_type": "combat_stat", "bonus_amount": 1},
            "4": {"name": "dragon-salt grand feast",      "sp": 140, "bonus_type": "combat_stat", "bonus_amount": 2},
            "5": {"name": "ancient draconic essence",     "sp": 200, "bonus_type": "two_stats", "bonus_amount": 2}
        }
    },
}

path = os.path.join(os.path.dirname(__file__), 'items', 'ingredient.json')
data = json.load(open(path, encoding='utf-8'))
added = 0
for key, val in FOUND.items():
    if key not in data:
        data[key] = val
        added += 1
    else:
        print(f'  SKIP (already exists): {key}')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f'Added {added} found ingredients. Total: {len(data)}')
