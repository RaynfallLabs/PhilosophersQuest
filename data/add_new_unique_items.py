#!/usr/bin/env python3
"""Add new unique mythological/historical items to the game's JSON files."""

import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS_DIR = os.path.join(DATA_DIR, "items")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_items(filename, new_items):
    path = os.path.join(ITEMS_DIR, filename)
    data = load_json(path)
    added = []
    skipped = []
    for key, value in new_items.items():
        if key in data:
            skipped.append(key)
        else:
            data[key] = value
            added.append(key)
    save_json(path, data)
    return added, skipped


# ── New Weapons ──────────────────────────────────────────────────────────────

NEW_WEAPONS = {
    "sling_of_david": {
        "name": "Sling of David",
        "class": "ranged",
        "variant": "1h",
        "tier": 1,
        "material": "leather",
        "mathTier": 1,
        "baseDamage": 6,
        "chainMultipliers": [0.5, 1.2, 2.0, 3.0, 4.5],
        "maxChainLength": 5,
        "damageTypes": ["blunt"],
        "symbol": ")",
        "color": [160, 120, 80],
        "weight": 0.5,
        "twoHanded": False,
        "reach": 12,
        "stunChance": 0.20,
        "bleedChance": 0.0,
        "knockback": True,
        "ignoreShield": False,
        "critMultiplier": 3.0,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-5": 8, "6-15": 15, "16-30": 5, "31-100": 0},
        "containerLootTier": "uncommon",
        "value": 300,
        "min_level": 5,
        "unidentified_name": "a worn leather strap with a pouch",
        "lore": "The shepherd boy David faced the giant Goliath with nothing but a sling and five smooth stones. One stone was enough. The sling is the weapon of the underestimated \u2014 it asks only for courage and accuracy. Against the mighty, it is devastating.",
        "quiz_tier": 1
    },
    "prometheus_torch": {
        "name": "Prometheus's Torch",
        "class": "staff",
        "variant": "2h",
        "tier": 1,
        "material": "wood",
        "mathTier": 2,
        "baseDamage": 8,
        "chainMultipliers": [0.5, 1.0, 1.7, 2.5, 3.5],
        "maxChainLength": 5,
        "damageTypes": ["crush", "fire"],
        "symbol": "/",
        "color": [255, 140, 0],
        "weight": 2.0,
        "twoHanded": True,
        "reach": 1,
        "stunChance": 0.0,
        "bleedChance": 0.0,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 1.5,
        "burnChance": 0.40,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-8": 5, "9-20": 12, "21-40": 5, "41-100": 0},
        "containerLootTier": "uncommon",
        "value": 500,
        "min_level": 8,
        "unidentified_name": "a smoldering wooden staff",
        "lore": "Prometheus stole fire from the gods and gave it to humanity, earning eternal punishment chained to a rock where an eagle devoured his liver daily. This torch carries that stolen fire. It cannot be extinguished, and it cannot be refused \u2014 fire is humanity's birthright.",
        "quiz_tier": 2
    },
    "sword_of_damocles": {
        "name": "Sword of Damocles",
        "class": "sword",
        "variant": "1h",
        "tier": 2,
        "material": "gold",
        "mathTier": 2,
        "baseDamage": 28,
        "chainMultipliers": [0.6, 1.1, 1.6, 2.2, 2.9, 3.7, 4.5],
        "maxChainLength": 7,
        "damageTypes": ["slash", "pierce"],
        "symbol": ")",
        "color": [255, 215, 0],
        "weight": 3.0,
        "twoHanded": False,
        "reach": 1,
        "stunChance": 0.0,
        "bleedChance": 0.0,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 1.5,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-11": 0, "12-30": 8, "31-50": 3, "51-100": 0},
        "containerLootTier": "rare",
        "value": 2000,
        "min_level": 12,
        "unidentified_name": "a jeweled blade suspended by a single horsehair",
        "lore": "Dionysius II of Syracuse invited the courtier Damocles to sit on his throne and enjoy the luxuries of power. Above the throne hung a sword, suspended by a single horsehair. Damocles understood immediately: power comes with constant peril. This blade cuts magnificently, but the thread grows thinner with every swing.",
        "quiz_tier": 2
    },
    "robin_hoods_longbow": {
        "name": "Robin Hood's Longbow",
        "class": "ranged",
        "variant": "2h",
        "tier": 2,
        "material": "yew",
        "mathTier": 2,
        "baseDamage": 14,
        "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 4.0, 5.5],
        "maxChainLength": 6,
        "damageTypes": ["pierce"],
        "symbol": "}",
        "color": [34, 139, 34],
        "weight": 2.5,
        "twoHanded": True,
        "reach": 20,
        "stunChance": 0.0,
        "bleedChance": 0.15,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 2.0,
        "requiresAmmo": "arrow",
        "floorSpawnWeight": {"1-13": 0, "14-35": 10, "36-60": 5, "61-100": 0},
        "containerLootTier": "rare",
        "value": 1800,
        "min_level": 14,
        "unidentified_name": "a weathered yew longbow wrapped in green cloth",
        "lore": "Robin of Loxley, the outlaw of Sherwood Forest, could split an arrow at two hundred paces. His longbow was cut from a yew tree in the heart of the forest. It favors those who strike from the shadows \u2014 enemies that cannot see you cannot hear its string.",
        "quiz_tier": 2
    },
    "achilles_spear": {
        "name": "Achilles's Spear",
        "class": "spear",
        "variant": "2h",
        "tier": 3,
        "material": "bronze",
        "mathTier": 3,
        "baseDamage": 18,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.0, 6.5],
        "maxChainLength": 8,
        "damageTypes": ["pierce"],
        "symbol": "/",
        "color": [205, 127, 50],
        "weight": 4.0,
        "twoHanded": True,
        "reach": 2,
        "stunChance": 0.0,
        "bleedChance": 0.15,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 2.0,
        "killHealAmount": 15,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-19": 0, "20-45": 10, "46-70": 5, "71-100": 0},
        "containerLootTier": "rare",
        "value": 3500,
        "min_level": 20,
        "unidentified_name": "a bronze-tipped ash spear with a worn grip",
        "lore": "The spear of Achilles, son of Peleus, forged by Hephaestus. In the myth of Telephus, the spear that wounded also healed \u2014 rust scraped from its tip cured the very wound it had made. Those slain by this spear restore vigor to their killer. At Troy, no warrior could stand before it.",
        "quiz_tier": 3
    },
    "gilgamesh_axe": {
        "name": "Gilgamesh's Axe",
        "class": "axe",
        "variant": "2h",
        "tier": 3,
        "material": "bronze",
        "mathTier": 3,
        "baseDamage": 22,
        "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 3.8, 5.0, 6.5],
        "maxChainLength": 7,
        "damageTypes": ["slash"],
        "symbol": ")",
        "color": [205, 133, 63],
        "weight": 6.0,
        "twoHanded": True,
        "reach": 1,
        "stunChance": 0.0,
        "bleedChance": 0.20,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 2.0,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-34": 0, "35-60": 8, "61-80": 5, "81-100": 2},
        "containerLootTier": "rare",
        "value": 4500,
        "min_level": 35,
        "unidentified_name": "a heavy bronze axe with cuneiform inscriptions",
        "lore": "Enkidu dreamed of an axe that fell from the sky \u2014 Gilgamesh's equal, his brother in arms. This is that axe: the weapon of the king who sought immortality and found friendship instead. In the Cedar Forest, Gilgamesh and Enkidu fought Humbaba together. The axe remembers that bond \u2014 it strikes harder after its wielder has been wounded.",
        "quiz_tier": 3
    },
    "cronus_scythe": {
        "name": "Cronus's Scythe",
        "class": "scimitar",
        "variant": "2h",
        "tier": 4,
        "material": "adamantine",
        "mathTier": 4,
        "baseDamage": 20,
        "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 3.8, 5.0, 6.5],
        "maxChainLength": 7,
        "damageTypes": ["slash", "magic"],
        "symbol": ")",
        "color": [128, 0, 128],
        "weight": 5.0,
        "twoHanded": True,
        "reach": 2,
        "stunChance": 0.0,
        "bleedChance": 0.25,
        "knockback": False,
        "ignoreShield": True,
        "critMultiplier": 2.0,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-37": 0, "38-65": 6, "66-100": 3},
        "containerLootTier": "rare",
        "value": 5500,
        "min_level": 38,
        "unidentified_name": "a curved blade that distorts the air around it",
        "lore": "Gaia gave this adamantine scythe to Cronus to overthrow his father Uranus. With it, Cronus castrated the sky itself \u2014 from the blood sprang the Giants and the Furies, and from the severed flesh arose Aphrodite. The scythe cuts through time and matter alike. Those it wounds age visibly, their vitality draining with each passing moment.",
        "quiz_tier": 4
    },
    "spear_of_lugh": {
        "name": "Spear of Lugh",
        "class": "spear",
        "variant": "2h",
        "tier": 5,
        "material": "adamantine",
        "mathTier": 5,
        "baseDamage": 26,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
        "damageTypes": ["pierce", "fire", "magic"],
        "symbol": "/",
        "color": [255, 100, 0],
        "weight": 4.0,
        "twoHanded": True,
        "reach": 2,
        "stunChance": 0.10,
        "bleedChance": 0.40,
        "knockback": False,
        "ignoreShield": True,
        "critMultiplier": 2.0,
        "burnChance": 0.30,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-49": 0, "50-80": 5, "81-100": 8},
        "containerLootTier": "legendary",
        "value": 9000,
        "min_level": 50,
        "unidentified_name": "a spear radiating intense heat",
        "lore": "One of the Four Treasures of the Tuatha De Danann. The Spear of Lugh was so bloodthirsty it had to be kept submerged in a cauldron of poison to prevent it from igniting everything nearby. No battle was ever sustained against it. Lugh used it to slay Balor of the Evil Eye at the Second Battle of Mag Tuired, striking through his eye and out the back of his head.",
        "quiz_tier": 5
    },
    "gae_dearg": {
        "name": "Gae Dearg",
        "class": "spear",
        "variant": "1h",
        "tier": 5,
        "material": "adamantine",
        "mathTier": 5,
        "baseDamage": 24,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0],
        "maxChainLength": 8,
        "damageTypes": ["pierce"],
        "symbol": "/",
        "color": [200, 30, 30],
        "weight": 3.0,
        "twoHanded": False,
        "reach": 2,
        "stunChance": 0.0,
        "bleedChance": 0.90,
        "knockback": False,
        "ignoreShield": True,
        "critMultiplier": 1.8,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-51": 0, "52-80": 4, "81-100": 6},
        "containerLootTier": "legendary",
        "value": 8500,
        "min_level": 52,
        "unidentified_name": "a crimson-stained spear that weeps red",
        "lore": "The Red Spear of Diarmuid Ua Duibhne, champion of the Fianna. Diarmuid carried two spears: Gae Buidhe the Yellow, which wounded but could not kill, and Gae Dearg the Red, from which no wound could ever heal. The distinction mattered \u2014 Diarmuid chose his spear based on whether mercy was warranted. Gae Dearg offers no mercy.",
        "quiz_tier": 5
    },
    "net_of_hephaestus": {
        "name": "Net of Hephaestus",
        "class": "ranged",
        "variant": "1h",
        "tier": 3,
        "material": "mithril",
        "mathTier": 3,
        "baseDamage": 2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0],
        "maxChainLength": 4,
        "damageTypes": ["blunt"],
        "symbol": ")",
        "color": [200, 200, 200],
        "weight": 1.5,
        "twoHanded": False,
        "reach": 5,
        "stunChance": 0.80,
        "bleedChance": 0.0,
        "knockback": False,
        "ignoreShield": True,
        "critMultiplier": 1.0,
        "requiresAmmo": None,
        "floorSpawnWeight": {"1-29": 0, "30-55": 6, "56-80": 4, "81-100": 2},
        "containerLootTier": "rare",
        "value": 4000,
        "min_level": 30,
        "unidentified_name": "a tightly woven metallic mesh",
        "lore": "Hephaestus forged this net to catch Ares and Aphrodite in their affair. It was so fine it was invisible, so strong not even Ares could break free. In the Odyssey, Demodocus sings of how Hephaestus dragged the ensnared lovers before all the gods of Olympus. This net does almost no damage \u2014 but nothing escapes it.",
        "quiz_tier": 3
    },
}

# ── New Scrolls ──────────────────────────────────────────────────────────────

NEW_SCROLLS = {
    "scroll_of_thoth": {
        "name": "Scroll of Thoth",
        "effect": "identify_all",
        "power": "thoth_blessing",
        "quiz_tier": 4,
        "quiz_threshold": 4,
        "weight": 0.5,
        "value": 4000,
        "min_level": 35,
        "identified": False,
        "unidentified_name": "a papyrus scroll with hieratic script",
        "lore": "Thoth, ibis-headed god of knowledge, inscribed all wisdom into forty-two books. The priest Setna Khamwas stole this scroll from the tomb of Neferkaptah and was haunted by the dead for his theft. Those who read it understand all languages and see through all illusions \u2014 but knowledge stolen from the dead carries a price.",
        "containerLootTier": "rare",
        "floorSpawnWeight": {"1-34": 0, "35-60": 5, "61-100": 3},
        "symbol": "?",
        "color": [255, 215, 100]
    },
    "dead_sea_scroll": {
        "name": "Dead Sea Scroll",
        "effect": "mapping",
        "power": "dead_sea_blessing",
        "quiz_tier": 3,
        "quiz_threshold": 3,
        "weight": 0.3,
        "value": 3000,
        "min_level": 30,
        "identified": False,
        "unidentified_name": "a brittle parchment sealed in a clay jar",
        "lore": "In 1947, a Bedouin shepherd threw a stone into a cave near Qumran and heard the sound of breaking pottery. Inside the jars were scrolls preserved for two thousand years. The War Scroll describes the final battle between the Sons of Light and the Sons of Darkness. Reading it reveals the battlefield \u2014 every corridor, every room, every enemy position.",
        "containerLootTier": "rare",
        "floorSpawnWeight": {"1-29": 0, "30-55": 6, "56-100": 3},
        "symbol": "?",
        "color": [200, 180, 140]
    }
}

# ── New Potions ──────────────────────────────────────────────────────────────

NEW_POTIONS = {
    "soma": {
        "name": "Soma",
        "effect": "full_heal",
        "power": 999,
        "duration": 30,
        "weight": 0.5,
        "value": 5000,
        "min_level": 25,
        "identified": False,
        "unidentified_name": "a pale golden elixir smelling of honey",
        "lore": "The Rigveda devotes an entire book \u2014 114 hymns \u2014 to Soma, the sacred drink of the Vedic gods. It was pressed from a plant, mixed with milk, and offered to Indra before battle. Scholars have debated its identity for centuries: ephedra, fly agaric, cannabis. Whatever it was, it made gods of men. One drink restores what was broken.",
        "floorSpawnWeight": {"1-24": 0, "25-50": 3, "51-80": 5, "81-100": 3},
        "containerLootTier": "rare",
        "symbol": "!",
        "color": [255, 215, 100]
    },
    "water_of_lethe": {
        "name": "Water of Lethe",
        "effect": "cure_all",
        "power": 0,
        "duration": 0,
        "weight": 0.5,
        "value": 2000,
        "min_level": 30,
        "identified": False,
        "unidentified_name": "perfectly clear water with no smell",
        "lore": "The River Lethe flows through the underworld. In Virgil's Aeneid, souls drink from it to forget their former lives before reincarnation. In Plato's Republic, the dead drink from the Plain of Forgetfulness. This water cures all afflictions of the mind \u2014 confusion, fear, madness \u2014 by simply erasing them. What you cannot remember cannot hurt you.",
        "floorSpawnWeight": {"1-29": 0, "30-55": 4, "56-100": 3},
        "containerLootTier": "rare",
        "symbol": "!",
        "color": [200, 220, 255]
    },
    "elixir_of_gilgamesh": {
        "name": "Elixir of Gilgamesh",
        "effect": "gain_level",
        "power": 2,
        "duration": 0,
        "weight": 0.5,
        "value": 8000,
        "min_level": 45,
        "identified": False,
        "unidentified_name": "a murky green liquid with something plant-like inside",
        "lore": "At the bottom of the sea, Gilgamesh found the plant of immortality. He called it 'The Old Man Becomes a Young Man.' On his way home, he stopped to bathe in a pool, and a serpent ate the plant \u2014 which is why snakes shed their skin and are reborn, while humans grow old and die. The eleventh tablet of the Epic is the oldest meditation on mortality in human literature.",
        "floorSpawnWeight": {"1-44": 0, "45-70": 2, "71-100": 3},
        "containerLootTier": "legendary",
        "symbol": "!",
        "color": [50, 150, 50]
    }
}

# ── New Ammo ─────────────────────────────────────────────────────────────────

NEW_AMMO = {
    "arrows_of_eros": {
        "name": "Arrows of Eros",
        "ammo_type": "arrow",
        "tier": 3,
        "damage_bonus": 3,
        "count_min": 3,
        "count_max": 4,
        "value": 2000,
        "min_level": 20,
        "identified": False,
        "unidentified_name": "golden-tipped arrows that feel warm",
        "lore": "Eros, whom the Romans called Cupid, carried two kinds of arrows: gold-tipped to inspire love, lead-tipped to inspire revulsion. Ovid tells how Eros shot Apollo with gold and Daphne with lead, creating the first unrequited love. These golden arrows charm their targets \u2014 struck creatures forget their hostility and become docile.",
        "floorSpawnWeight": {"1-19": 0, "20-45": 6, "46-100": 3},
        "containerLootTier": "rare",
        "symbol": "(",
        "color": [255, 200, 50],
        "weight": 0.2
    },
    "arrows_of_artemis": {
        "name": "Arrows of Artemis",
        "ammo_type": "arrow",
        "tier": 5,
        "damage_bonus": 8,
        "count_min": 4,
        "count_max": 6,
        "value": 5000,
        "min_level": 30,
        "identified": False,
        "unidentified_name": "silver arrows fletched with white feathers",
        "lore": "Artemis the Huntress never missed. In the Iliad, she is 'the lady of wild things.' Her silver arrows brought swift, painless death \u2014 Homer describes women dying suddenly as 'slain by the gentle shafts of Artemis.' Callimachus records that she forged them herself on the island of Lipara. Six arrows. Make them count.",
        "floorSpawnWeight": {"1-29": 0, "30-60": 4, "61-100": 5},
        "containerLootTier": "legendary",
        "symbol": "(",
        "color": [200, 200, 255],
        "weight": 0.2
    },
    "bolts_of_zeus": {
        "name": "Bolts of Zeus",
        "ammo_type": "bolt",
        "tier": 5,
        "damage_bonus": 15,
        "count_min": 2,
        "count_max": 3,
        "value": 7000,
        "min_level": 55,
        "identified": False,
        "unidentified_name": "crackling bolts of compressed energy",
        "lore": "The Cyclopes \u2014 Brontes, Steropes, and Arges \u2014 forged Zeus's thunderbolts in the furnaces beneath Mount Etna. Hesiod's Theogony describes them as having 'thunder and lightning and bright thunderbolt.' With these, Zeus overthrew the Titans and established the order of Olympus. Three bolts. Each one shakes the earth.",
        "floorSpawnWeight": {"1-54": 0, "55-80": 3, "81-100": 4},
        "containerLootTier": "legendary",
        "symbol": "(",
        "color": [100, 150, 255],
        "weight": 0.3
    }
}

# ── New Food ─────────────────────────────────────────────────────────────────

NEW_FOOD = {
    "ambrosia": {
        "name": "Ambrosia",
        "sp_restore": 100,
        "hp_restore": 50,
        "bonus_type": "all_stats",
        "bonus_amount": 1,
        "bonus_stat": None,
        "bonus_effect": None,
        "weight": 0.3,
        "value": 8000,
        "min_level": 40,
        "identified": True,
        "lore": "The food of the Olympian gods. Homer uses the word interchangeably with nectar \u2014 sometimes it is food, sometimes drink, sometimes an anointing oil rubbed on the dead to preserve them. Pindar says it conferred immortality. What is certain is that mortals who tasted it were never the same. It restores everything and improves everything \u2014 but it is not meant for mortal tongues.",
        "floorSpawnWeight": {"1-39": 0, "40-70": 2, "71-100": 3},
        "containerLootTier": "legendary",
        "symbol": "%",
        "color": [255, 215, 0]
    },
    "golden_apple": {
        "name": "Golden Apple of Hesperides",
        "sp_restore": 80,
        "hp_restore": 30,
        "bonus_type": "stat",
        "bonus_amount": 1,
        "bonus_stat": "CON",
        "bonus_effect": None,
        "weight": 0.3,
        "value": 6000,
        "min_level": 40,
        "identified": True,
        "lore": "Heracles's eleventh labor sent him to the Garden of the Hesperides at the western edge of the world, guarded by the hundred-headed dragon Ladon, to retrieve the golden apples that Gaia had given Hera as a wedding gift. The apples granted immortality to whoever ate them. Eris later used one inscribed 'For the Fairest' to start the Trojan War. Beauty, immortality, and war \u2014 all in one fruit.",
        "floorSpawnWeight": {"1-39": 0, "40-65": 3, "66-100": 4},
        "containerLootTier": "rare",
        "symbol": "%",
        "color": [255, 200, 50]
    },
    "peach_of_immortality": {
        "name": "Peach of Immortality",
        "sp_restore": 90,
        "hp_restore": 40,
        "bonus_type": "random_stat",
        "bonus_amount": 1,
        "bonus_stat": None,
        "bonus_effect": None,
        "weight": 0.3,
        "value": 7000,
        "min_level": 45,
        "identified": True,
        "lore": "Xi Wangmu, the Queen Mother of the West, grows these peaches in her garden on Mount Kunlun. They ripen once every three thousand years. Sun Wukong ate them all during his rampage through Heaven, gaining near-immortality. Journey to the West records that the theft of the peaches was one of three offenses that caused Buddha to imprison the Monkey King beneath Five Elements Mountain for five hundred years.",
        "floorSpawnWeight": {"1-44": 0, "45-70": 2, "71-100": 3},
        "containerLootTier": "legendary",
        "symbol": "%",
        "color": [255, 180, 200]
    },
    "tantalus_plum": {
        "name": "Tantalus's Plum",
        "sp_restore": 5,
        "hp_restore": 80,
        "bonus_type": "none",
        "bonus_amount": 0,
        "bonus_stat": None,
        "bonus_effect": None,
        "weight": 0.2,
        "value": 1200,
        "min_level": 12,
        "identified": False,
        "unidentified_name": "a perfect-looking fruit just out of reach",
        "lore": "Tantalus served his own son Pelops as a feast for the gods, testing their omniscience. His punishment in Tartarus was eternal hunger and thirst: water receded when he bent to drink, and fruit branches pulled away when he reached. This plum is the fruit he could never grasp \u2014 eating it heals greatly but leaves you ravenous.",
        "floorSpawnWeight": {"1-11": 0, "12-30": 6, "31-50": 4, "51-100": 2},
        "containerLootTier": "uncommon",
        "symbol": "%",
        "color": [128, 0, 128]
    }
}

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    all_results = [
        ("weapon.json", NEW_WEAPONS),
        ("scroll.json", NEW_SCROLLS),
        ("potion.json", NEW_POTIONS),
        ("ammo.json", NEW_AMMO),
        ("food.json", NEW_FOOD),
    ]

    for filename, new_items in all_results:
        added, skipped = add_items(filename, new_items)
        print(f"\n=== {filename} ===")
        if added:
            print(f"  Added {len(added)} items: {', '.join(added)}")
        if skipped:
            print(f"  Skipped {len(skipped)} (already exist): {', '.join(skipped)}")
        if not added and not skipped:
            print("  No items to process.")

    print("\nDone!")


if __name__ == "__main__":
    main()
