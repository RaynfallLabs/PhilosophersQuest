import json

# ---- ARMOR ----
with open('data/items/armor.json', encoding='utf-8') as f:
    armor = json.load(f)

armor['nemean_pelt'] = {
    "name": "Nemean Lion Pelt",
    "symbol": "[",
    "color": [220,180,80],
    "weight": 12.0,
    "min_level": 45,
    "slot": "body",
    "tier": 4,
    "material": "hide",
    "ac_bonus": 5,
    "equip_threshold": 2,
    "quiz_tier": 4,
    "damage_resistances": {"slash": 0.0, "pierce": 0.0},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "thick golden hide",
    "lore": "The hide of the Nemean Lion, impossible to cut or pierce. Hercules used its own claws to skin it. Wearing it is like wearing the beast itself."
}

armor['green_knights_plate'] = {
    "name": "Green Knight's Plate",
    "symbol": "[",
    "color": [80,180,80],
    "weight": 20.0,
    "min_level": 63,
    "slot": "body",
    "tier": 5,
    "material": "enchanted plate",
    "ac_bonus": 6,
    "equip_threshold": 3,
    "quiz_tier": 5,
    "damage_resistances": {"slash": 0.75, "physical": 0.85},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "eerily green plate armor",
    "lore": "Forged from enchanted iron that grows with the wearer, the Green Knight's Plate absorbs blows that would kill a lesser man. The wearer heals slowly but continuously.",
    "special_effect": "regen_2"
}

armor['serpent_scale_mail'] = {
    "name": "Serpent Scale Mail",
    "symbol": "[",
    "color": [60,160,100],
    "weight": 14.0,
    "min_level": 55,
    "slot": "body",
    "tier": 4,
    "material": "scale",
    "ac_bonus": 4,
    "equip_threshold": 2,
    "quiz_tier": 4,
    "damage_resistances": {"poison": 0.0, "cold": 0.7},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "iridescent scale hauberk",
    "lore": "Scales from J\u00f6rmungandr's juvenile form, each harder than iron. The poison that suffuses them has been neutralized \u2014 but it still repels toxins entirely."
}

# Cloaks added to armor.json since no cloak.json exists
armor['arachne_silk_cloak'] = {
    "name": "Arachne's Silk Cloak",
    "symbol": "[",
    "color": [180,140,80],
    "weight": 1.5,
    "min_level": 3,
    "slot": "cloak",
    "tier": 2,
    "material": "silk",
    "ac_bonus": 1,
    "equip_threshold": 1,
    "quiz_tier": 2,
    "damage_resistances": {"pierce": 0.7},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "shimmering silk cloak",
    "lore": "Woven by Arachne before her transformation, this cloak is lighter than air and tougher than leather against piercing weapons. It catches arrows and slows blades."
}

armor['erlking_mantle'] = {
    "name": "Erlking's Mantle",
    "symbol": "[",
    "color": [80,140,80],
    "weight": 2.0,
    "min_level": 20,
    "slot": "cloak",
    "tier": 3,
    "material": "enchanted cloth",
    "ac_bonus": 1,
    "equip_threshold": 2,
    "quiz_tier": 3,
    "damage_resistances": {},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "a green forest cloak",
    "lore": "Woven from the living branches of the Erlking's forest, this cloak sharpens the senses of the wearer. Sound and sight carry further, and hidden things become easier to discern.",
    "special_effect": "per_plus_2"
}

armor['anansi_web_cloak'] = {
    "name": "Anansi's Web Cloak",
    "symbol": "[",
    "color": [220,180,40],
    "weight": 1.0,
    "min_level": 85,
    "slot": "cloak",
    "tier": 5,
    "material": "divine silk",
    "ac_bonus": 2,
    "equip_threshold": 2,
    "quiz_tier": 5,
    "damage_resistances": {"poison": 0.5, "physical": 0.9},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "a glittering golden web",
    "lore": "Spun by Anansi himself from the thread of a thousand stories, this cloak shifts and deceives. Attacks that should land somehow miss. Traps somehow fail to trigger."
}

armor['nidhoggr_scale'] = {
    "name": "N\u00ed\u00f0h\u00f6ggr's Scale",
    "symbol": "[",
    "color": [80,200,80],
    "weight": 3.0,
    "min_level": 90,
    "slot": "cloak",
    "tier": 5,
    "material": "dragon scale",
    "ac_bonus": 3,
    "equip_threshold": 3,
    "quiz_tier": 5,
    "damage_resistances": {"acid": 0.0, "poison": 0.3, "cold": 0.5},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "a vast dark-green scale",
    "lore": "A single scale from N\u00ed\u00f0h\u00f6ggr's body, imbued with the rot of ages. Nothing corrodes it. Wearing it grants the wearer immunity to acid and strong resistance to all decay-based attacks."
}

with open('data/items/armor.json', 'w', encoding='utf-8') as f:
    json.dump(armor, f, indent=2, ensure_ascii=False)
print('armor.json updated, total entries:', len(armor))

# ---- SHIELD ----
with open('data/items/shield.json', encoding='utf-8') as f:
    shield = json.load(f)

shield['bronze_aegis'] = {
    "name": "Bronze Aegis",
    "symbol": "]",
    "color": [180,160,100],
    "weight": 8.0,
    "min_level": 12,
    "tier": 2,
    "material": "bronze",
    "ac_bonus": 3,
    "equip_threshold": 2,
    "quiz_tier": 2,
    "damage_resistances": {"blunt": 0.75, "slash": 0.85},
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "unidentified_name": "ancient bronze shield",
    "lore": "The ceremonial shield of a bronze giant, engraved with the eye of Hephaestus. Its curved surface deflects crushing blows better than any iron shield of its age."
}

with open('data/items/shield.json', 'w', encoding='utf-8') as f:
    json.dump(shield, f, indent=2, ensure_ascii=False)
print('shield.json updated, total entries:', len(shield))

# ---- WEAPON ----
with open('data/items/weapon.json', encoding='utf-8') as f:
    weapon = json.load(f)

weapon['hunt_captains_sword'] = {
    "name": "Hunt Captain's Sword",
    "class": "sword",
    "variant": "1h",
    "tier": 5,
    "material": "spectral iron",
    "mathTier": 5,
    "baseDamage": 18,
    "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 4.0, 5.5],
    "maxChainLength": 8,
    "damageTypes": ["slash", "cold"],
    "symbol": ")",
    "color": [180,180,220],
    "weight": 3.0,
    "min_level": 80,
    "equip_threshold": 3,
    "quiz_tier": 5,
    "two_handed": False,
    "unidentified_name": "a ghostly iron longsword",
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "lore": "Taken from the captain of the Wild Hunt, this blade phases between this world and the spectral realm. Its edge is impossibly sharp and its cold is the cold of the grave.",
    "effects": {"status": "bleeding", "effect_chance": 0.25, "effect_duration": 4}
}

weapon['wendigo_fang'] = {
    "name": "Wendigo's Fang",
    "class": "dagger",
    "variant": "1h",
    "tier": 5,
    "material": "bone",
    "mathTier": 5,
    "baseDamage": 12,
    "chainMultipliers": [0.5, 1.0, 2.0, 3.0, 4.5],
    "maxChainLength": 7,
    "damageTypes": ["cold", "pierce"],
    "symbol": ")",
    "color": [200,220,255],
    "weight": 1.5,
    "min_level": 75,
    "equip_threshold": 2,
    "quiz_tier": 5,
    "two_handed": False,
    "unidentified_name": "a pale jagged tooth",
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "lore": "A fang torn from the Wendigo's maw. It leaches warmth and stamina from enemies on contact. The wound never feels warm again.",
    "effects": {"status": "slowed", "effect_chance": 0.35, "effect_duration": 4}
}

weapon['echidna_fang'] = {
    "name": "Echidna's Fang",
    "class": "dagger",
    "variant": "1h",
    "tier": 3,
    "material": "fang",
    "mathTier": 3,
    "baseDamage": 8,
    "chainMultipliers": [0.5, 1.0, 1.8, 2.8],
    "maxChainLength": 6,
    "damageTypes": ["pierce", "poison"],
    "symbol": ")",
    "color": [140,100,160],
    "weight": 1.0,
    "min_level": 15,
    "equip_threshold": 2,
    "quiz_tier": 3,
    "two_handed": False,
    "unidentified_name": "a curved ivory fang",
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "lore": "A tooth from Echidna herself, mother of all monsters. Wounds from it fester with a slow-acting venom that mimics her many children's poisons.",
    "effects": {"status": "poisoned", "effect_chance": 0.40, "effect_duration": 7}
}

weapon['vulcans_brand'] = {
    "name": "Vulcan's Brand",
    "class": "sword",
    "variant": "1h",
    "tier": 3,
    "material": "volcanic iron",
    "mathTier": 3,
    "baseDamage": 11,
    "chainMultipliers": [0.5, 1.0, 1.7, 2.5, 3.5],
    "maxChainLength": 6,
    "damageTypes": ["slash", "fire"],
    "symbol": ")",
    "color": [200,100,40],
    "weight": 4.5,
    "min_level": 30,
    "equip_threshold": 2,
    "quiz_tier": 3,
    "two_handed": False,
    "unidentified_name": "a red-hot iron blade",
    "can_be_cursed": False,
    "enchant_bonus": 0,
    "lore": "Forged in Vulcan's own furnace by Cacus who stole the technique from his father. The blade never fully cools and sets enemies alight on a solid strike.",
    "effects": {"status": "burning", "effect_chance": 0.35, "effect_duration": 4}
}

with open('data/items/weapon.json', 'w', encoding='utf-8') as f:
    json.dump(weapon, f, indent=2, ensure_ascii=False)
print('weapon.json updated, total entries:', len(weapon))

# ---- ACCESSORY ----
with open('data/items/accessory.json', encoding='utf-8') as f:
    accessory = json.load(f)

accessory['sphinx_crown'] = {
    "name": "Sphinx's Crown",
    "symbol": "\"",
    "color": [200,180,100],
    "weight": 1.0,
    "min_level": 35,
    "slot": "amulet",
    "equip_threshold": 2,
    "quiz_tier": 4,
    "effects": {"stat": "WIS", "amount": 2},
    "can_be_cursed": False,
    "unidentified_name": "a golden riddle-crown",
    "lore": "The crown of the Sphinx, imbued with millennia of accumulated riddle-wisdom. Wearing it sharpens the mind and extends the time available for all mental challenges."
}

accessory['sailors_amulet'] = {
    "name": "Sailor's Amulet",
    "symbol": "\"",
    "color": [40,100,200],
    "weight": 0.5,
    "min_level": 68,
    "slot": "amulet",
    "equip_threshold": 2,
    "quiz_tier": 4,
    "effects": {"stat": "PER", "amount": 1, "status": "cold_resist", "duration": -1},
    "can_be_cursed": False,
    "unidentified_name": "a driftwood amulet",
    "lore": "Carved from the wood of a ship that survived Charybdis, this amulet carries the protection of calm water. The wearer reads the currents of danger before they arrive."
}

accessory['anubis_scales'] = {
    "name": "Anubis's Scales",
    "symbol": "\"",
    "color": [180,100,40],
    "weight": 0.8,
    "min_level": 58,
    "slot": "amulet",
    "equip_threshold": 2,
    "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 1},
    "can_be_cursed": False,
    "unidentified_name": "balanced golden scales",
    "lore": "A miniature of the scales Anubis uses to weigh hearts against the feather of Ma'at. Wearing them steadies the pulse and hardens the bearer against the drain of undead."
}

accessory['ring_of_iron_grip'] = {
    "name": "Ring of Iron Grip",
    "symbol": "=",
    "color": [200,60,60],
    "weight": 0.2,
    "min_level": 70,
    "slot": "ring",
    "equip_threshold": 2,
    "quiz_tier": 4,
    "effects": {"stat": "STR", "amount": 2},
    "can_be_cursed": False,
    "unidentified_name": "a crude iron band",
    "lore": "Crushed from a finger of Ravana himself, this ring channels the demon king's immense physical power into whoever wears it. The grip becomes unbreakable."
}

accessory['obsidian_talisman'] = {
    "name": "Obsidian Talisman",
    "symbol": "\"",
    "color": [100,60,120],
    "weight": 0.4,
    "min_level": 25,
    "slot": "amulet",
    "equip_threshold": 2,
    "quiz_tier": 3,
    "effects": {"status": "dark_vision", "duration": -1},
    "can_be_cursed": False,
    "unidentified_name": "a jagged black stone",
    "lore": "Carved from sacrificial obsidian used in Xibalba, the Mayan underworld. It grants the wearer sight in magical darkness and resistance to fear effects from undead."
}

with open('data/items/accessory.json', 'w', encoding='utf-8') as f:
    json.dump(accessory, f, indent=2, ensure_ascii=False)
print('accessory.json updated, total entries:', len(accessory))

# ---- WAND ----
with open('data/items/wand.json', encoding='utf-8') as f:
    wand = json.load(f)

wand['iron_mortar_wand'] = {
    "name": "Baba Yaga's Iron Mortar",
    "symbol": "/",
    "color": [160,120,80],
    "weight": 4.0,
    "min_level": 50,
    "charges_min": 3,
    "charges_max": 5,
    "max_charges": 5,
    "quiz_tier": 4,
    "quiz_threshold": 3,
    "effect": "iron_mortar",
    "power": "",
    "unidentified_name": "a heavy iron pestle",
    "identified": False,
    "lore": "Baba Yaga grinds the bones of heroes in this mortar before eating them. When wielded as a wand, it channels chaotic magic \u2014 the effect is never the same twice."
}

with open('data/items/wand.json', 'w', encoding='utf-8') as f:
    json.dump(wand, f, indent=2, ensure_ascii=False)
print('wand.json updated, total entries:', len(wand))
