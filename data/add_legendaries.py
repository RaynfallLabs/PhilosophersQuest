#!/usr/bin/env python3
"""Add 100 legendary items to Philosopher's Quest data files."""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def chain(n):
    base = [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5, 8.0]
    return base[:n]

RARE = {"61-80": 1, "81-100": 2}
VERY_RARE = {"81-100": 2}

# ── WEAPONS ──────────────────────────────────────────────────────────────────

WEAPONS = {
  "excalibur": {
    "name": "Excalibur", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [255,245,180], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.15, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "an ornate golden-hilted blade",
    "lore": "The sword in the stone was not merely a test of strength but of worthiness — a distinction Arthur understood only after he had already proven himself in other ways. The blade predates its legend; Merlin admitted he found it. An inscription along the fuller reads in a language older than Latin: 'Take me up; cast me away.' Most kings have trouble with the second part."
  },
  "durendal": {
    "name": "Durendal", "class": "sword", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 28, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [220,200,140], "weight": 6,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.1, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "an impossibly keen two-handed blade",
    "lore": "Roland's sword contained within its golden hilt a tooth of Saint Peter, blood of Saint Basil, hair of Saint Denis, and a fragment of the Virgin's raiment. At Roncevaux, rather than let it fall to the Saracens, Roland struck it three times against a stone. The stone split each time. Durendal did not."
  },
  "gram": {
    "name": "Gram", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","pierce"],
    "symbol": ")", "color": [200,220,255], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.15, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a shining foreign blade of pale steel",
    "lore": "Odin thrust Gram into the Branstock oak; only Sigmund drew it. His son Sigurd had the pieces reforged and with Gram slew Fafnir the dragon, tasted its blood, and thereafter understood the speech of birds."
  },
  "tyrfing": {
    "name": "Tyrfing", "class": "sword", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 32, "chainMultipliers": chain(8), "maxChainLength": 8,
    "damageTypes": ["slash","magic"],
    "symbol": ")", "color": [255,60,60], "weight": 7,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.3, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": VERY_RARE, "containerLootTier": "legendary",
    "value": 10000, "min_level": 70, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a sword that vibrates with cold malice",
    "lore": "The dwarves Dvalinn and Durin forged Tyrfing under duress and cursed it: it would kill a man every time unsheathed. The blade never rusts, never dulls, cuts through iron and stone. Three kings of the Hervarar line died by it. The curse is intrinsic to those who lack the wisdom to set it down."
  },
  "fragarach": {
    "name": "Fragarach", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","magic"],
    "symbol": ")", "color": [100,200,255], "weight": 2,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a slender blade with a sea-blue shimmer",
    "lore": "The Answerer. No armour could stop it; no man could move once it was held to his throat. Manannan mac Lir forged it; Lugh carried it to end Fomorian tyranny. The Irish poets called it the Wind from the East."
  },
  "caladbolg": {
    "name": "Caladbolg", "class": "zweihander", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 30, "chainMultipliers": chain(8), "maxChainLength": 8,
    "damageTypes": ["slash"],
    "symbol": ")", "color": [160,255,200], "weight": 8,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.2, "bleedChance": 0.1, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a massive greatsword of unearthly make",
    "lore": "Fergus mac Róich's great sword could cut the tops off three hills with one sweep. Forged in the Otherworld, it has no human metallurgical analogue. The original has no fragments because it has never broken."
  },
  "joyeuse": {
    "name": "Joyeuse", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [255,230,80], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.25, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a radiant blade that shifts colour in lamplight",
    "lore": "Charlemagne's coronation sword changed colour thirty times per day and shone so brightly that enemies were dazzled before the first blow. Charlemagne was buried with it at Aachen. Or possibly wasn't. The trail goes cold in the ninth century."
  },
  "hrunting": {
    "name": "Hrunting", "class": "sword", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 26, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","pierce"],
    "symbol": ")", "color": [180,180,220], "weight": 6,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.2, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "an ancient iron-dark blade etched with serpents",
    "lore": "Unferth lent Hrunting to Beowulf for his descent into the mere. The poem calls it hardened in the blood of battle and says it had never failed any man who grasped it. In the underwater fight with Grendel's mother, it failed once. That was its single exception."
  },
  "skofnung": {
    "name": "Skofnung", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash"],
    "symbol": ")", "color": [200,255,220], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.2, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.2, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a cold grey blade with a dim inner glow",
    "lore": "Taken from King Hrólf Kraki's burial mound; the twelve berserkers who served him in life inhabited the blade. Wounds dealt by Skofnung could only be healed by the Skofnung Stone. No healer has replicated the Stone."
  },
  "gungnir": {
    "name": "Gungnir", "class": "spear", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","holy"],
    "symbol": "/", "color": [200,180,255], "weight": 4,
    "twoHanded": False, "reach": 2,
    "stunChance": 0.1, "bleedChance": 0.1, "knockback": False,
    "ignoreShield": True, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a perfectly balanced spear of dark ash",
    "lore": "An oath sworn on Gungnir's tip is unbreakable. Odin threw it over the Vanir's heads to begin the first war. It has never missed. At Ragnarok he will throw it at the Fenris Wolf. This will not be a contradiction."
  },
  "gae_bulg": {
    "name": "Gáe Bulg", "class": "spear", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(8), "maxChainLength": 8,
    "damageTypes": ["pierce"],
    "symbol": "/", "color": [80,220,140], "weight": 3,
    "twoHanded": False, "reach": 2,
    "stunChance": 0.0, "bleedChance": 0.6, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a barbed spear of sea-monster bone",
    "lore": "Made from the bone of the Coinchenn sea-beast, thrown with the foot. When it entered a body it opened thirty barbs — it could not be withdrawn. Cu Chulainn used it twice in single combat; both times he wept after."
  },
  "spear_of_longinus": {
    "name": "Spear of Longinus", "class": "spear", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 26, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","holy"],
    "symbol": "/", "color": [180,100,255], "weight": 4,
    "twoHanded": False, "reach": 2,
    "stunChance": 0.0, "bleedChance": 0.35, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": VERY_RARE, "containerLootTier": "legendary",
    "value": 10000, "min_level": 70, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a Roman pilum with a blackened tip",
    "lore": "Longinus pierced Christ's side at the crucifixion. Blood and water ran from the wound; Longinus was healed of failing eyesight. Charlemagne carried it in 47 battles. He died the one day he set it down."
  },
  "mjolnir": {
    "name": "Mjolnir", "class": "warhammer", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 26, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["crush","shock"],
    "symbol": "T", "color": [100,180,255], "weight": 5,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.3, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9500, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a short-handled hammer of unsettling weight",
    "lore": "The handle came out short due to Loki's sabotage, but Odin declared it the greatest treasure ever made. Thor wore iron gauntlets to wield it. At Ragnarok he will kill the Midgard Serpent, take nine steps, and fall. The hammer will survive him."
  },
  "sharur": {
    "name": "Sharur", "class": "mace", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["crush","magic"],
    "symbol": "T", "color": [255,200,80], "weight": 4,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.2, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a bronze mace with a head like a lion",
    "lore": "Ninurta's mace could fly ahead to scout and report back with intelligence. When Ninurta fought Asag the stone demon, Sharur flew ahead and counselled patience when a direct assault would have failed. The Sumerians recorded it as both weapon and advisor."
  },
  "ruyi_jingu_bang": {
    "name": "Ruyi Jingu Bang", "class": "staff", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 28, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["crush"],
    "symbol": "|", "color": [200,100,255], "weight": 9,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.2, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "an impossibly heavy iron staff wrapped in gold",
    "lore": "Sun Wukong found this in the Dragon King's treasury where it weighted the ocean floor. It weighed 13,500 jin. In his hand it became exactly the right size. He killed 47,000 demons with it. The Buddha imprisoned him under a mountain for five hundred years. He considered this a minor setback."
  },
  "gandiva": {
    "name": "Gandiva", "class": "longbow", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","holy"],
    "symbol": ")", "color": [255,220,100], "weight": 3,
    "twoHanded": True, "reach": 2,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.5, "requiresAmmo": "arrow",
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a great bow that hums with stored energy",
    "lore": "Arjuna's divine bow had one hundred strings; when one broke another appeared. Its twang shook the earth. With it Arjuna killed 100,000 soldiers in the Kurukshetra War. When grief made him hesitate before battle, Krishna delivered an 18-chapter philosophical treatise to persuade him to pick it up again."
  },
  "fail_not": {
    "name": "Fail-not", "class": "longbow", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 18, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["pierce"],
    "symbol": ")", "color": [180,220,160], "weight": 2,
    "twoHanded": True, "reach": 2,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.8, "requiresAmmo": "arrow",
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a yew bow with a single carved inscription",
    "lore": "Tristan's bow, given by the fairy Morgain. Its name was its promise. The inscription reads 'Fail not.' Arrows loosed in duty flew true; arrows loosed in anger missed. Its owner learned this the hard way."
  },
  "kusanagi": {
    "name": "Kusanagi-no-Tsurugi", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","magic"],
    "symbol": ")", "color": [160,255,255], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a slim blade with the scent of rain",
    "lore": "Found inside the eight-headed serpent Yamata no Orochi. Yamato Takeru used it to cut the grass and redirect the wind when surrounded by enemies who had set fire to the plain around him. The sword has been at the Atsuta Shrine for fourteen centuries. No one has seen it."
  },
  "zulfiqar": {
    "name": "Zulfiqar", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","pierce"],
    "symbol": ")", "color": [200,230,180], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.15, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a blade forked at the tip like a serpent's tongue",
    "lore": "Given to Ali ibn Abi Talib at the Battle of Badr. 'There is no sword but Zulfiqar, and no hero but Ali.' The bifurcated tip could take two lives with one thrust. Shia tradition holds it will be wielded by the Mahdi at the end of time."
  },
  "harpe": {
    "name": "Harpe", "class": "scimitar", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","pierce"],
    "symbol": ")", "color": [180,220,255], "weight": 2,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a curved blade with a small hooked back-edge",
    "lore": "Given to Perseus by Hermes to slay Medusa. Forged with an adamantine edge. Perseus used it while looking at Medusa's reflection in his shield. Some myths say Cronus used its predecessor to castrate Uranus. The weapon has a history of separating very important things."
  },
  "trident_of_poseidon": {
    "name": "Trident of Poseidon", "class": "spear", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","cold"],
    "symbol": "/", "color": [60,180,255], "weight": 5,
    "twoHanded": False, "reach": 2,
    "stunChance": 0.15, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a three-pronged weapon of sea-dark metal",
    "lore": "Poseidon struck the Acropolis and produced a saltwater spring. Athena planted an olive tree. He lost the vote and flooded the Attic plain. The trident-mark is still visible on the Erechtheion floor. He used it to attempt to drown Odysseus for an entire decade."
  },
  "carnwennan": {
    "name": "Carnwennan", "class": "dagger", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 14, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["pierce","magic"],
    "symbol": ")", "color": [220,255,220], "weight": 1,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 3.2, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a small white-handled knife with no visible edge",
    "lore": "Arthur's dagger that could shroud its wielder in shadow. Arthur used it to kill the Very Black Witch in the Valley of Grief after Kei and Bedivere had both tried and failed. The Mabinogion records this without elaboration."
  },
  "mistilteinn": {
    "name": "Mistilteinn", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","magic"],
    "symbol": ")", "color": [200,255,200], "weight": 2,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a blade that seems to cut shadows as well as flesh",
    "lore": "The Mistletoe Sword. Mistletoe was the one substance Baldur was not protected against — his mother considered it too small to matter. The sword shares this property. Wielded by Prainn the draugr-king before Hervor took it from his barrow."
  },
  "curtana": {
    "name": "Curtana", "class": "sword", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(8), "maxChainLength": 8,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [200,200,200], "weight": 6,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.1, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 45, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a broad two-handed blade with a blunt squared tip",
    "lore": "The Sword of Mercy — its tip broken by an angel at the moment Ogier the Dane was about to kill Charlemagne's son. The broken tip became the symbol of mercy in justice. English coronation regalia still includes a blunt-tipped Sword of Mercy. Mercy is the lesser blade."
  },
  "parashu": {
    "name": "Parashu", "class": "axe", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [255,160,80], "weight": 4,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.2, "bleedChance": 0.1, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a divine axe of celestial bronze",
    "lore": "Shiva gave Parashu to Parashurama after ten thousand years of penance. Parashurama used it to exterminate the Kshatriya caste twenty-one times over, filling five lakes with blood. He is considered a great teacher of martial arts."
  },
  "labrys": {
    "name": "Labrys", "class": "axe", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash"],
    "symbol": ")", "color": [255,200,200], "weight": 4,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.15, "bleedChance": 0.2, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a symmetrical double-bladed ceremonial axe",
    "lore": "The double-headed axe of Minoan Crete — labrys means both the axe and the labyrinth. It appears in every Minoan palace fresco, held by women. Modern scholars believe it was primarily religious. The Minotaur had no sword, only size, darkness, and the certainty that no one wanted to be there."
  },
  "chandrahas": {
    "name": "Chandrahas", "class": "scimitar", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","cold"],
    "symbol": ")", "color": [200,220,255], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a curved blade cold as moonlight",
    "lore": "Shiva gave the Moon's Laughter to Ravana after Ravana lifted Mount Kailash with twenty arms. Shiva added the condition that if used for evil it would return to him. Ravana used it for evil almost immediately. The sword returned. This is the problem with giving extraordinary weapons as gifts."
  },
  "laevateinn": {
    "name": "Laevateinn", "class": "staff", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["magic","fire"],
    "symbol": "|", "color": [255,120,80], "weight": 5,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.25, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a staff cut from the world-tree with a notch at the top",
    "lore": "Loki cut it at the gates of Hel. It can destroy Vidofnir, the golden rooster atop Yggdrasil whose crowing will begin Ragnarok. Sinmara guards it and will only surrender it through a series of impossible trades. Preventing Ragnarok is bureaucratically complicated."
  },
  "thyrsus": {
    "name": "Thyrsus of Dionysus", "class": "staff", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 4,
    "baseDamage": 16, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["crush","magic"],
    "symbol": "|", "color": [160,100,60], "weight": 3,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.4, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a giant fennel stalk topped with a pine cone",
    "lore": "The Maenads carried the thyrsus. In the Bacchae, Agave kills her son Pentheus with it, believing in her madness he is a lion. Dionysus watched. This is the instrument of a god who believed experience was the teacher."
  },
  "rod_of_moses": {
    "name": "Rod of Moses", "class": "staff", "variant": "2h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 18, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["crush","holy","magic"],
    "symbol": "|", "color": [220,210,170], "weight": 3,
    "twoHanded": True, "reach": 1,
    "stunChance": 0.15, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": VERY_RARE, "containerLootTier": "legendary",
    "value": 9500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a plain shepherd's crook of ancient wood",
    "lore": "The rod became a serpent in Pharaoh's court; parted the Red Sea; struck the rock at Horeb. Jewish tradition gives it a provenance from Adam through Noah through Abraham. Moses used it. Aaron used it. No one is certain what happened to it afterward."
  },
  "amenonuhoko": {
    "name": "Amenonuhoko", "class": "spear", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 20, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["pierce","holy"],
    "symbol": "/", "color": [255,240,180], "weight": 4,
    "twoHanded": False, "reach": 2,
    "stunChance": 0.1, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a jewelled spear of heavenly metal",
    "lore": "Given to Izanagi and Izanami to solidify the land. Standing on the Floating Bridge of Heaven, they stirred the ocean. When they lifted the spear, drops fell back and became the first islands of Japan. The island of Onogoro rose from what dripped off its tip."
  },
  "sudarshana": {
    "name": "Sudarshana Chakra", "class": "scimitar", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 18, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["slash","fire"],
    "symbol": ")", "color": [255,140,40], "weight": 2,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": True,
    "ignoreShield": False, "critMultiplier": 2.2, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a spinning disc of burning light",
    "lore": "Vishnu's spinning discus. Forged from the effulgence of the sun itself. When Shiva asked to test Vishnu's most powerful weapon, Vishnu threw it without warning and cut off one of Shiva's heads. Shiva grew a new one. They considered this a satisfactory test."
  },
  "ridill": {
    "name": "Ridill", "class": "dagger", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 16, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["pierce","magic"],
    "symbol": ")", "color": [200,255,240], "weight": 1,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": True, "critMultiplier": 2.8, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a short blade from the dwarf-hoard",
    "lore": "One of two swords in Fafnir's hoard alongside Gram. Sigurd left it when he took Gram. Ridill was the shorter blade — a dwarf-forged knife of theoretical powers, present at every great event of the Volsung cycle, never called upon. Its potential remains forever theoretical."
  },
  "kladenets": {
    "name": "Samosek", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","magic"],
    "symbol": ")", "color": [255,200,255], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a blade that seems to move before you do",
    "lore": "The Self-Swinger of Slavic fairy tales fights on its own. It is found in underground kingdoms guarded by Koschei or a serpent. Heroes who find it never quite understand it. The sword fights; they survive. The sword's autonomy is treated not as alarming but as practical."
  },
  "shamshir_e_zomorrodnegar": {
    "name": "Shamshir-e Zomorrodnegar", "class": "scimitar", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 22, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","magic"],
    "symbol": ")", "color": [100,255,180], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.2, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.5, "requiresAmmo": None,
    "floorSpawnWeight": VERY_RARE, "containerLootTier": "legendary",
    "value": 9000, "min_level": 65, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "an emerald-inlaid curved blade of Solomonic make",
    "lore": "The Emerald-Studded Sword of Solomon could bind and command djinn. On each emerald a name of power was engraved. Solomon used it not as a weapon but as an administrative tool, employing djinn in constructing the Temple. Its use as a management instrument is rarely discussed in Western traditions."
  },
  "chrysaor": {
    "name": "Chrysaor", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 24, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","holy"],
    "symbol": ")", "color": [255,215,0], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.2, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 60, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a golden-bladed sword of divine origin",
    "lore": "Chrysaor — the Golden Sword — sprang from Medusa's neck alongside Pegasus when Perseus beheaded her. He carried it through his life and gave it to his son Geryones, who built a kingdom in the far west with its aid. Heracles killed Geryones and the sword passed from the western world's records. Gold swords appear occasionally in Bronze Age hoards. None have been identified as Chrysaor. None have been ruled out."
  },
  "caliburn": {
    "name": "Caliburn", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 21, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash"],
    "symbol": ")", "color": [190,190,220], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.1, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.9, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a plain but perfectly balanced blade",
    "lore": "Some scholars distinguish Caliburn — the sword in the stone — from Excalibur, the sword from the lake. Geoffrey of Monmouth uses the name Caliburnus and has it forged in Avalon. In later tradition it became a single weapon. The distinction matters because the stone-sword test and the lake-gift are morally opposite stories: one is earned, one is given. Arthur had both."
  },
  "brisingr": {
    "name": "Brisingr", "class": "sword", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 23, "chainMultipliers": chain(9), "maxChainLength": 9,
    "damageTypes": ["slash","fire"],
    "symbol": ")", "color": [255,160,50], "weight": 3,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.1, "bleedChance": 0.0, "knockback": False,
    "ignoreShield": False, "critMultiplier": 2.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8500, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a blade that runs warm to the touch",
    "lore": "The word for fire in Old Norse. A sword that shares its name with the ancient word for flame was found in a Norse burial mound in Gotland, its blade still faintly warm centuries later. The metallurgists who examined it in 1947 published their findings in a paper that was subsequently lost. Three colleagues confirmed its content before it vanished. The sword itself remains in a private collection."
  },
  "fragarach_the_whisperer": {
    "name": "Whisperer", "class": "dagger", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 14, "chainMultipliers": chain(10), "maxChainLength": 10,
    "damageTypes": ["pierce","magic"],
    "symbol": ")", "color": [200,240,255], "weight": 1,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.1, "knockback": False,
    "ignoreShield": True, "critMultiplier": 3.0, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 8000, "min_level": 55, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a dagger that makes almost no sound",
    "lore": "A blade said to have been forged by the same smith who made Fragarach, intended as its companion. Where Fragarach answered questions loudly, this blade worked silently. Assassins across four centuries reported finding it rather than seeking it. It was present at the deaths of seven significant historical figures. Twice it was present at the survival of one."
  },
  "naegling": {
    "name": "Naegling", "class": "axe", "variant": "1h",
    "tier": 5, "material": "adamantine", "mathTier": 5,
    "baseDamage": 21, "chainMultipliers": chain(8), "maxChainLength": 8,
    "damageTypes": ["slash","crush"],
    "symbol": ")", "color": [210,200,180], "weight": 5,
    "twoHanded": False, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.25, "knockback": False,
    "ignoreShield": False, "critMultiplier": 1.6, "requiresAmmo": None,
    "floorSpawnWeight": RARE, "containerLootTier": "legendary",
    "value": 7500, "min_level": 50, "quiz_tier": 5,
    "identified": False,
    "unidentified_name": "a heavy single-bladed axe with an age-worn grip",
    "lore": "Beowulf's sword that shattered in his final battle with the dragon. The poem notes that iron could not help him — his grip was too strong for ordinary blades. Naegling broke. He had to kill the dragon with his bare hands and a knife. This is what happens when a warrior outlives the weapons made for lesser men."
  },
}

# ── ACCESSORIES ───────────────────────────────────────────────────────────────

ACCESSORIES = {
  "ring_of_gyges": {
    "name": "Ring of Gyges", "symbol": "=", "color": [180,180,180],
    "weight": 0.1, "min_level": 60, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"status": "invisible", "duration": -1},
    "unidentified_name": "a plain iron ring with no markings",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Plato's thought experiment made physical. A shepherd found it in a chasm opened by earthquake, wore it, discovered its power, seduced the queen, killed the king, and took the throne. Plato used it to ask: would a just man behave differently if invisible? The Ring doesn't answer the question. It only enables it."
  },
  "ring_of_the_nibelung": {
    "name": "Ring of the Nibelung", "symbol": "=", "color": [200,150,50],
    "weight": 0.2, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "STR", "amount": 4},
    "unidentified_name": "a heavy gold ring with a tiny rune",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Andvari's gold ring, stolen by Loki and given as wergild to the giant Hreidmar. Andvari cursed it: it would destroy every owner. Hreidmar was killed by his son. Fafnir killed his brother for it. Sigurd killed Fafnir. The ring went to Gudrun, who murdered Sigurd. Wagner compressed this into four operas. The curse required no compression."
  },
  "andvaranaut": {
    "name": "Andvaranaut", "symbol": "=", "color": [255,215,80],
    "weight": 0.1, "min_level": 55, "slot": "ring",
    "equip_threshold": 4, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 3, "status": "searching", "duration": -1},
    "unidentified_name": "a golden ring that seems lighter than it should",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Andvari's magic ring that could find gold wherever it lay hidden. Loki stole it with the rest of the dwarf's hoard to pay the wergild for killing Otr. Andvari cursed both the ring and all the gold as he surrendered them. The ring found gold. It could not find safe owners."
  },
  "draupnir": {
    "name": "Draupnir", "symbol": "=", "color": [255,230,100],
    "weight": 0.3, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 4},
    "unidentified_name": "a golden arm-ring of extraordinary weight",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Odin's ring — every ninth night eight rings of equal weight dripped from it. Odin placed it on Baldur's funeral pyre. Baldur returned it from Hel as proof that he had been there. Hermod carried it back. It is the only object ever to make a round trip to the realm of the dead and return unchanged."
  },
  "ring_of_solomon": {
    "name": "Seal of Solomon", "symbol": "=", "color": [120,180,120],
    "weight": 0.1, "min_level": 60, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 3, "status": "telepathy", "duration": -1},
    "unidentified_name": "a signet ring with a six-pointed star",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The ring that let Solomon command demons and djinn, given to him from heaven. With it he enslaved Asmodeus, the king of demons, and forced him to assist in the Temple's construction. When a demon stole the ring, Solomon was reduced to begging for food until he recovered it. The ring's power depended entirely on who wore it."
  },
  "ring_of_eluned": {
    "name": "Ring of Eluned", "symbol": "=", "color": [160,200,160],
    "weight": 0.1, "min_level": 50, "slot": "ring",
    "equip_threshold": 4, "quiz_tier": 5,
    "effects": {"status": "invisible", "duration": -1, "stat": "DEX", "amount": 2},
    "unidentified_name": "a green ring of twisted ivy-metal",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The Welsh Arthurian heroine Luned gave this ring to Owain when he was trapped in a portcullis. It rendered him invisible to the castle's inhabitants until he could escape. She retrieved it afterward, which is the appropriate thing to do with a ring of this power. Most people who receive such gifts do not return them."
  },
  "brisingamen": {
    "name": "Brisingamen", "symbol": '"', "color": [255,100,150],
    "weight": 0.3, "min_level": 65, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 3, "status": "regeneration", "duration": -1},
    "unidentified_name": "a necklace of four interlocked golden torcs",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Freya's necklace, forged by four dwarves over four days. She paid each one a night of her company. Loki stole it in the form of a fly; Heimdall fought him in seal-form to recover it. Freya wore it in battle and her tears became gold. The Brisingamen is the most written-about piece of Norse jewellery. The dwarves received no further acknowledgment in the sagas."
  },
  "talisman_of_troy": {
    "name": "Palladium of Troy", "symbol": '"', "color": [200,200,255],
    "weight": 0.5, "min_level": 65, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"status": "reflecting", "duration": -1},
    "unidentified_name": "a small wooden figure of armed Athena",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The Palladium — a carved image of Athena that fell from the sky — kept Troy invincible as long as it remained within the city walls. Odysseus and Diomedes stole it. Troy fell. Later, every major city of the ancient world claimed to have the original Palladium: Rome, Athens, Argos, Sparta. They cannot all be correct. They may all be correct."
  },
  "eye_of_horus": {
    "name": "Eye of Horus", "symbol": '"', "color": [80,200,255],
    "weight": 0.2, "min_level": 60, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "PER", "amount": 4, "status": "truesight", "duration": -1},
    "unidentified_name": "a faience amulet shaped like a falcon's eye",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "When Set tore out Horus's eye, Thoth restored it. The restored eye — the wedjat — became the symbol of protection, health, and restored power. Egyptian physicians prescribed it; sailors wore it on boats. The mathematical fractions of the eye's components sum to 63/64. The missing 1/64 was left to Thoth to complete with magic."
  },
  "scarab_of_khepri": {
    "name": "Scarab of Khepri", "symbol": '"', "color": [100,200,100],
    "weight": 0.2, "min_level": 55, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 5,
    "effects": {"status": "life_save", "duration": -1},
    "unidentified_name": "a carved green stone beetle",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Khepri, the scarab god, rolls the sun across the sky each morning — the same motion the dung beetle makes rolling its ball. Egyptian amulets shaped like scarabs were placed over the heart of the dead to prevent it from testifying against its owner at the judgment. The heart was considered the source of moral failure. The scarab, apparently, overruled it."
  },
  "hamsa_hand": {
    "name": "Hand of Fatima", "symbol": '"', "color": [200,180,140],
    "weight": 0.2, "min_level": 40, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 2, "status": "warning", "duration": -1},
    "unidentified_name": "an open hand amulet with an eye in the palm",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The hamsa appears in Islamic, Jewish, and Christian traditions under different names — Hand of Fatima, Hand of Miriam, Hand of Mary. The eye in the palm deflects the evil eye. It is one of the few symbols shared without significant modification across the Mediterranean's three Abrahamic faiths. No one disputes it. Everyone claims it."
  },
  "ouroboros_pendant": {
    "name": "Ouroboros", "symbol": '"', "color": [120,180,80],
    "weight": 0.2, "min_level": 45, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"status": "regeneration", "duration": -1, "stat": "CON", "amount": 2},
    "unidentified_name": "a silver pendant of a serpent eating its tail",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The oldest image of the ouroboros appears in an Egyptian royal tomb, 1350 BCE. It represents cyclical time, eternal recurrence, the universe sustaining itself. Alchemists adopted it. Jung analysed it. Kekulé claimed the image gave him the ring structure of benzene in a dream. Whether this last part is true, the benzene ring is real."
  },
  "necklace_of_harmonia": {
    "name": "Necklace of Harmonia", "symbol": '"', "color": [200,150,200],
    "weight": 0.3, "min_level": 65, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 4},
    "unidentified_name": "a golden necklace of impossible craftsmanship",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Hephaestus forged it as a wedding gift for Harmonia when she married Cadmus — and cursed it, because Harmonia's mother was Aphrodite, who had cuckolded him with Ares. Every woman who wore it suffered catastrophe: Jocasta, Eriphyle (who betrayed her husband for it), Jocasta again, Callirhoe. The necklace destroyed houses. It is still beautiful."
  },
  "menat_of_hathor": {
    "name": "Menat of Hathor", "symbol": '"', "color": [255,180,100],
    "weight": 0.4, "min_level": 50, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 4},
    "unidentified_name": "a beaded collar of carnelian and faience",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Hathor's sacred necklace, shaken as a rattle in her rituals. Temple reliefs show pharaohs receiving the menat from the goddess as a guarantee of health, fertility, and joy. It was both jewellery and musical instrument. The sound of carnelian beads against each other was, in Hathor's theology, the sound of everything being well."
  },
  "heart_of_ahriman": {
    "name": "Heart of Ahriman", "symbol": '"', "color": [200,0,80],
    "weight": 0.3, "min_level": 70, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 5},
    "unidentified_name": "a deep red gem that seems to pulse",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Ahriman, the Zoroastrian principle of darkness and chaos, is not merely evil but anti-being — the force that unmakes. His heart, if such a thing could be extracted and held, would contain complete knowledge of all things that can be destroyed. This is a great deal of knowledge. The gem is warm. It should not be warm."
  },
  "tyet_of_isis": {
    "name": "Tyet of Isis", "symbol": '"', "color": [220,60,80],
    "weight": 0.2, "min_level": 60, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"status": "life_save", "duration": -1, "stat": "WIS", "amount": 2},
    "unidentified_name": "a knotted red jasper amulet like a tied sash",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The knot of Isis — the tyet — accompanied the dead as written in Chapter 156 of the Book of the Dead: 'You possess your blood, Isis; you possess your power.' It was always made of red jasper or red stone. Red was the colour of Isis's protective power, not of blood. This distinction mattered to Egyptian physicians."
  },
  "idunn_apple_charm": {
    "name": "Idunn's Apple", "symbol": '"', "color": [180,255,120],
    "weight": 0.2, "min_level": 70, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "CON", "amount": 5},
    "unidentified_name": "a carved jade apple on a silver chain",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Idunn kept the golden apples that gave the Aesir their eternal youth. When Loki allowed the giant Thjazi to kidnap her, the gods began to age. They forced Loki to retrieve her; he turned into a falcon, turned her into a nut, and flew back. Thjazi pursued. The gods lit fires at Asgard's walls and Thjazi burned. Idunn is the one person in Norse mythology who causes a crisis by simply not being present."
  },
  "caduceus_charm": {
    "name": "Caduceus of Hermes", "symbol": '"', "color": [160,220,180],
    "weight": 0.2, "min_level": 50, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"status": "regeneration", "duration": -1, "stat": "WIS", "amount": 2},
    "unidentified_name": "a charm of two serpents coiled around a winged rod",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Hermes received the caduceus from Apollo in exchange for the lyre. It could put people to sleep or wake them, guide souls to the underworld, and — in later tradition — heal. Medical associations adopted it, confusing it with Asclepius's single-serpent staff. The American Military medical corps still uses the caduceus. Doctors point out the distinction; the military finds it difficult to care."
  },
  "torque_of_lugh": {
    "name": "Torque of Lugh", "symbol": '"', "color": [255,200,80],
    "weight": 0.4, "min_level": 65, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "STR", "amount": 4},
    "unidentified_name": "a twisted gold neck-ring of Celtic make",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Lugh of the Long Arm wore a golden torque as one of his divine symbols, along with Fragarach and a magic horse. He was the god of skill — every skill simultaneously — because he argued his way past the Tuatha's gatekeeper by pointing out that while they had specialists, none of them could do everything he could. The gatekeeper let him in."
  },
  "pectoral_of_amun": {
    "name": "Pectoral of Amun", "symbol": '"', "color": [200,160,80],
    "weight": 0.5, "min_level": 65, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 4},
    "unidentified_name": "a broad chest ornament of lapis and gold",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Amun, whose name means 'the hidden one,' was invisible by definition — his cult image was sealed inside the inner sanctum of Karnak, and even priests could not see it. His pectoral was worn by pharaohs when making decisions of state. The decisions were not actually made by the pectoral. They were, however, required to be made while wearing it."
  },
  "ankh_of_ra": {
    "name": "Ankh of Ra", "symbol": '"', "color": [255,220,80],
    "weight": 0.2, "min_level": 50, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 3, "status": "regeneration", "duration": -1},
    "unidentified_name": "a looped cross of gilded bronze",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Ra holds the ankh — the key of life — in all his standard depictions. He passes it to pharaohs; pharaohs pass it to other gods; everyone passes it. The ankh's shape may derive from a sandal strap, a mirror, or a feminine symbol depending on which scholar you consult. In Coptic Christianity it became the crux ansata and survived into church iconography. It is the oldest recurring symbol in Egyptian art."
  },
  "ring_of_gawain": {
    "name": "Ring of Sir Gawain", "symbol": "=", "color": [180,220,180],
    "weight": 0.1, "min_level": 60, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "STR", "amount": 3, "status": "hasted", "duration": -1},
    "unidentified_name": "a plain green ring with a small enameled star",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "In the Alliterative Morte Arthure, Gawain's strength grew until noon, held until three, and then diminished. In the Green Knight poem, he wore a green girdle he believed would protect him, and was ashamed when his small evasion was revealed. The shame was disproportionate; Gawain was the most courteous knight, which meant his lapses troubled him more than other men's crimes troubled them."
  },
  "ring_of_odysseus": {
    "name": "Ring of Odysseus", "symbol": "=", "color": [200,180,140],
    "weight": 0.1, "min_level": 60, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "PER", "amount": 4, "status": "searching", "duration": -1},
    "unidentified_name": "an old bronze ring with a ship carved in the stone",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Odysseus had no magical ring. He needed none. He was the man who thought of the wooden horse, who tied himself to the mast to hear the Sirens safely, who invented false identities with the ease of breathing. What he could not solve with cunning he solved with patience. The ring is his, in retrospect — it was always going to be found by someone who didn't go home the easy way."
  },
  "ring_of_scheherazade": {
    "name": "Ring of Scheherazade", "symbol": "=", "color": [200,160,255],
    "weight": 0.1, "min_level": 60, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 4},
    "unidentified_name": "a ring set with a pale blue stone that swirls",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Scheherazade told 1,001 stories to postpone her execution. She did not use magic; she used structure — each story nested inside another, every night's tale ending at a moment too interesting to stop. She survived by being more valuable alive than dead. This is the original argument for intellectual labour. She was also, by the end, the queen."
  },
  "amulet_of_merlin": {
    "name": "Amulet of Merlin", "symbol": '"', "color": [100,100,200],
    "weight": 0.3, "min_level": 70, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 5},
    "unidentified_name": "a blue pendant with a moving star inside the stone",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Merlin was the son of an incubus and a Welsh princess, a fact that concerned his contemporaries far less than it perhaps should have. He advised three kings, built Stonehenge (in some accounts), created the Round Table, engineered the conception of Arthur, and was eventually imprisoned in a glass tower or a tree or a cave by his student Nimue. The nature of the prison varies. The imprisonment does not."
  },
  "ring_of_pythia": {
    "name": "Ring of the Oracle", "symbol": "=", "color": [200,200,140],
    "weight": 0.1, "min_level": 55, "slot": "ring",
    "equip_threshold": 4, "quiz_tier": 5,
    "effects": {"status": "clairvoyant", "duration": -1, "stat": "PER", "amount": 2},
    "unidentified_name": "a bronze ring smelling faintly of laurel smoke",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "The Pythia at Delphi sat over a chasm in the earth and breathed volcanic vapour while speaking for Apollo. Her pronouncements were famously ambiguous: Croesus was told that if he attacked Persia, he would destroy a great empire. He did. The empire was his own. The Oracle was never wrong. It just required careful interpretation."
  },
  "anklet_of_atalanta": {
    "name": "Anklet of Atalanta", "symbol": "=", "color": [200,255,180],
    "weight": 0.1, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "DEX", "amount": 5},
    "unidentified_name": "a delicate runner's anklet of pale silver",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Atalanta could outrun any man alive. Her father offered her hand to whoever could beat her in a race. The losers were killed. Hippomenes won by dropping three golden apples from Aphrodite; she stopped to pick them up. She did not stop because she wanted the apples. She stopped because losing was the most interesting thing that had happened to her yet."
  },
  "crown_of_croesus": {
    "name": "Diadem of Croesus", "symbol": "=", "color": [220,200,80],
    "weight": 0.2, "min_level": 50, "slot": "ring",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "INT", "amount": 3, "status": "searching", "duration": -1},
    "unidentified_name": "a small golden diadem fragment on a chain",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Croesus of Lydia was the richest man in the world and knew it. He tested the Delphic Oracle with an absurd question to verify its power before asking whether he should attack Persia. It answered correctly. He attacked Persia. The Oracle had also answered correctly about that. Croesus's error was not the Oracle. It was the interpretation."
  },
  "collar_of_njord": {
    "name": "Sea-Collar of Njörd", "symbol": '"', "color": [80,180,220],
    "weight": 0.3, "min_level": 45, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 3, "status": "warning", "duration": -1},
    "unidentified_name": "a necklace of Baltic amber and whale-bone",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Njörd ruled the winds and the seas and was responsible for the catch of fish and hunters' luck. He married Skadi, who chose him by his feet — the most beautiful feet among the gods — expecting to have chosen Baldur. They lived six days in her mountains, six by the sea, and both were miserable by turns. Nordic marriage counsellors date their profession's origin to this arrangement."
  },
  "ring_of_percival": {
    "name": "Ring of the Pure Knight", "symbol": "=", "color": [220,240,255],
    "weight": 0.1, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 4},
    "unidentified_name": "a silver ring set with a small cup-shaped hollow",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Percival failed the Grail question because he was too polite to ask what was wrong with the Fisher King. He had been told not to ask too many questions. He followed the instruction and failed. When he returned and asked — Who does the Grail serve? — the king was healed. The lesson of the Grail quest is that courtesy has limits, and sometimes the correct action is to inquire."
  },
  "ring_of_lancelot": {
    "name": "Ring of the Fallen Knight", "symbol": "=", "color": [255,200,200],
    "weight": 0.1, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "STR", "amount": 4, "status": "hasted", "duration": -1},
    "unidentified_name": "a red-gold ring with a small tower engraved on it",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "Lancelot was the greatest knight in the world and destroyed the Round Table by being exactly that. His affair with Guinevere was not a secret he kept — it was a secret everyone kept for him because they needed him too much to confront him. The tower on the ring is the tower of Joyous Gard, where he retreated when his virtue finally failed the test he had spent his life avoiding."
  },
  "seal_of_agrippa": {
    "name": "Seal of Agrippa", "symbol": '"', "color": [100,100,150],
    "weight": 0.2, "min_level": 60, "slot": "amulet",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 3, "status": "clairvoyant", "duration": -1},
    "unidentified_name": "a wax seal pendant with planetary symbols",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Heinrich Cornelius Agrippa published Three Books of Occult Philosophy in 1531, systematizing all of Renaissance magic into a single framework: the elemental world, the celestial world, and the intellectual world. He was accused of heresy, employed by kings, and died in debt. His books were the most widely read magical texts of the 16th century. He himself claimed at the end that they were worthless. He was probably not being entirely honest."
  },
  "philosophers_ring_legendary": {
    "name": "Philosopher's Ring", "symbol": "=", "color": [200,180,255],
    "weight": 0.1, "min_level": 65, "slot": "ring",
    "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "WIS", "amount": 3, "status": "truesight", "duration": -1},
    "unidentified_name": "a ring of strange alloy that seems to look back at you",
    "floorSpawnWeight": VERY_RARE, "identified": False,
    "lore": "The philosopher does not merely think — the philosopher perceives. Socrates described his daimon as a voice that told him what not to do; he considered this the most useful kind of guidance. The ring was found in the ruins of the Academy at Athens, described in a catalogue written three centuries after Plato's death. The description ends mid-sentence. The catalogue's final page is missing."
  },
  "amulet_of_pythagoras": {
    "name": "Tetractys Amulet", "symbol": '"', "color": [160,200,220],
    "weight": 0.2, "min_level": 50, "slot": "amulet",
    "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "INT", "amount": 3, "status": "searching", "duration": -1},
    "unidentified_name": "a bronze triangle pendant with ten points",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Pythagoras swore his oaths by the Tetractys — the triangular figure of ten points arranged 1-2-3-4 that represented the musical ratios and the structure of the cosmos. His brotherhood at Croton was vegetarian, banned beans, and believed the soul transmigrated between lives. They were also the first people to prove that the square root of 2 is irrational, a discovery so disturbing that Hippasus, who made it, was allegedly drowned at sea."
  },
  "ring_of_hypatia": {
    "name": "Ring of Hypatia", "symbol": "=", "color": [220,240,200],
    "weight": 0.1, "min_level": 55, "slot": "ring",
    "equip_threshold": 4, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 3, "status": "truesight", "duration": -1},
    "unidentified_name": "a thin bronze ring engraved with mathematical diagrams",
    "floorSpawnWeight": RARE, "identified": False,
    "lore": "Hypatia of Alexandria was the foremost mathematician and astronomer of her age, head of the Neoplatonic school, advisor to the prefect Orestes. In 415 CE a Christian mob pulled her from her chariot, dragged her to a church, and killed her. Her father Theon had raised her to be 'a perfect human being.' What destroyed her was not her imperfection. It was that the people around her could not tolerate the example."
  },
}

# ── SHIELDS ───────────────────────────────────────────────────────────────────

SHIELDS = {
  "aegis_of_athena": {
    "name": "Aegis of Athena", "symbol": ")", "color": [200,220,255],
    "weight": 4.0, "min_level": 65,
    "tier": 5, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"fire": 0.35, "magic": 0.40, "cold": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a polished shield of supernatural brightness",
    "floorSpawnWeight": VERY_RARE, "value": 9500,
    "lore": "The aegis was not originally a shield but a goatskin breastplate — or a thundercloud — worn by Zeus and Athena. Homer describes Athena shaking it during battle to produce fear in armies. The Gorgoneion — Medusa's severed head — was mounted on it after Perseus made his gift. Athena used a weapon whose power was entirely in what it made people see, rather than what it physically did."
  },
  "svalinn_shield": {
    "name": "Svalinn", "symbol": ")", "color": [200,255,255],
    "weight": 3.0, "min_level": 55,
    "tier": 5, "material": "adamantine",
    "ac_bonus": 4, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"fire": 0.55, "shock": 0.3},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a shield that feels cool to the touch even in heat",
    "floorSpawnWeight": RARE, "value": 8000,
    "lore": "The Poetic Edda places Svalinn — the Cooler — before the sun to shield the earth from its full heat. Without it the mountains would burn and the seas boil. It stands there and no one knows how it arrived. The name means exactly what it does. The Norse naming conventions for cosmological entities were admirably functional."
  },
  "pridwen": {
    "name": "Pridwen", "symbol": ")", "color": [220,220,255],
    "weight": 3.5, "min_level": 55,
    "tier": 5, "material": "adamantine",
    "ac_bonus": 4, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.40, "fire": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a white shield with a painted figure",
    "floorSpawnWeight": RARE, "value": 8000,
    "lore": "Arthur's shield, named in the Welsh poem Pa gur and the Mabinogion. The image of the Virgin Mary was painted on its inner face, so Arthur fought facing her. This was the interior side — the side that faces the bearer. The image was not for showing to enemies. It was for Arthur to look at."
  },
  "tower_shield_of_ajax": {
    "name": "Tower Shield of Ajax", "symbol": ")", "color": [180,180,160],
    "weight": 9.0, "min_level": 65,
    "tier": 5, "material": "adamantine",
    "ac_bonus": 6, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.25, "pierce": 0.35},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a massive laminated shield of ox-hide and bronze",
    "floorSpawnWeight": RARE, "value": 9000,
    "lore": "Ajax's shield was described as a tower of seven ox-hides laminated together with bronze — the largest shield in the Iliad. He stood before the Greek ships and held back the Trojans by mass and will. Achilles was the brilliant warrior. Ajax was the one who could not be moved. When Odysseus was awarded Achilles' armour by rhetorical argument, Ajax's grief destroyed him. The shield outlasted its owner."
  },
  "scutum_of_aeneas": {
    "name": "Scutum of Aeneas", "symbol": ")", "color": [190,170,130],
    "weight": 6.0, "min_level": 60,
    "tier": 5, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.2, "crush": 0.2, "fire": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a curved rectangular shield of divine workmanship",
    "floorSpawnWeight": RARE, "value": 8500,
    "lore": "Hephaestus forged a new shield for Aeneas with the entire future of Rome inscribed on its surface — battles not yet fought, emperors not yet born, the city not yet founded. Aeneas carried it without understanding what he looked at. He bore the fame and destiny of his descendants on his shoulders, ignorant of their names. Virgil considered this a beautiful image. It is also a description of every ancestor."
  },
}

# ── ARMOR ─────────────────────────────────────────────────────────────────────

ARMOR = {
  "hide_of_nemean_lion": {
    "name": "Hide of the Nemean Lion", "symbol": "[", "color": [200,180,80],
    "weight": 6.0, "min_level": 65,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 8, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.35, "crush": 0.3, "pierce": 0.25},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a rough amber pelt of unnatural density",
    "floorSpawnWeight": RARE, "value": 9000,
    "lore": "The Nemean Lion's hide could not be cut by any weapon — that was the point of the first Labour. Heracles strangled it. The lion's own claws were the only things sharp enough to skin it. He wore the hide thereafter. Every subsequent monster he faced had to find a way to harm a man armoured in the unskinnable. Most didn't manage it."
  },
  "carapace_of_the_hydra": {
    "name": "Carapace of the Hydra", "symbol": "[", "color": [80,180,100],
    "weight": 5.0, "min_level": 60,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 6, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"poison": 0.65, "cold": 0.2, "fire": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a greenish scaled vest that smells faintly of venom",
    "floorSpawnWeight": RARE, "value": 8500,
    "lore": "Heracles used the Hydra's caustic blood to poison his arrows — the same arrows that killed Chiron by accident and Nessus by intention and started the chain that killed Heracles himself. The Hydra's outer scale was immune to its own venom. This is the standard configuration: weapons made from the thing they destroy are often proof against the same."
  },
  "panoply_of_hephaestus": {
    "name": "Panoply of Hephaestus", "symbol": "[", "color": [200,190,160],
    "weight": 12.0, "min_level": 70,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 9, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.2, "pierce": 0.2, "crush": 0.2, "fire": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a suit of armour of inhuman precision",
    "floorSpawnWeight": VERY_RARE, "value": 9500,
    "lore": "Hephaestus was thrown from Olympus by his mother (or his father, depending on which Homer you read) and landed on Lemnos. He survived, became the smith of the gods, and made the best things in existence: Achilles' armour, the golden automata that walked him to his forge, the chain-net that caught Aphrodite and Ares in bed, the bronze giant Talos. Everything he made was perfect. He himself walked with a limp."
  },
  "dragon_mail_of_sigurd": {
    "name": "Dragon-Sewn Mail of Sigurd", "symbol": "[", "color": [100,160,80],
    "weight": 8.0, "min_level": 65,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 7, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"fire": 0.5, "slash": 0.25, "pierce": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a shirt of scale-linked rings with a faint iridescence",
    "floorSpawnWeight": RARE, "value": 9000,
    "lore": "After killing Fafnir, Sigurd bathed in the dragon's blood and became invulnerable — except for a leaf that fell between his shoulder blades. His eventual murder came from a spear through exactly that spot, thrown by a man told about it by a woman who loved him and was told by another man who needed Sigurd dead. The weak point was the information, not the armour."
  },
  "breastplate_of_joan": {
    "name": "Breastplate of Joan of Arc", "symbol": "[", "color": [220,220,220],
    "weight": 7.0, "min_level": 55,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 6, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.2, "pierce": 0.2, "fire": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a plain white-painted steel breastplate",
    "floorSpawnWeight": RARE, "value": 8000,
    "lore": "Joan of Arc described her armour as 'very good' — white-painted steel made specifically for her. She was wounded multiple times and fought on. She told her judges at her trial that her armour had been made by command of God and could not protect against what God willed. They burned her anyway. Twenty-five years later Charles VII had the verdict annulled. Joan had been dead for twenty-five years."
  },
  "lorica_hamata_of_caesar": {
    "name": "Lorica of Caesar", "symbol": "[", "color": [180,180,160],
    "weight": 6.0, "min_level": 50,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"slash": 0.25, "pierce": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a fine ring-mail shirt of late Republican make",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "Julius Caesar wore chain-mail. He also reportedly wore a special hat to cover his baldness and was sensitive about being called a king by the Senate. He was stabbed twenty-three times. The physician Antistius found only one wound fatal. The other senators had been imprecise or hesitant. Caesar had refused his bodyguard. He had been warned. He understood warnings as challenges."
  },
  "orichalcum_breastplate": {
    "name": "Orichalcum Breastplate", "symbol": "[", "color": [255,200,80],
    "weight": 8.0, "min_level": 65,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 7, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.35, "fire": 0.2, "cold": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a chest-piece of reddish-gold metal that vibrates faintly",
    "floorSpawnWeight": RARE, "value": 9000,
    "lore": "Orichalcum was the metal of Atlantis — mentioned by Plato in the Critias as the most prized substance in the world after gold. Its appearance was flame-red. The Atlanteans mined it everywhere, then it vanished when Atlantis sank. Modern scholars identify it as brass or a copper-zinc alloy. The identification is probably correct. Plato's text does not describe its resonance, which the surviving piece still exhibits."
  },
  "helm_of_hades": {
    "name": "Helm of Darkness", "symbol": "[", "color": [40,40,60],
    "weight": 3.0, "min_level": 65,
    "slot": "head", "tier": 5, "material": "adamantine",
    "ac_bonus": 3, "enchant_bonus": 0,
    "equip_threshold": 5, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.4, "poison": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a helm that seems to absorb light around it",
    "floorSpawnWeight": RARE, "value": 9000,
    "lore": "The Helm of Hades was made by the Cyclopes in the same forging that made Poseidon's trident and Zeus's lightning. Perseus borrowed it to approach the Gorgons unseen. Hermes lent it to Athena during the Trojan War. It did not grant invisibility — it prevented perception. The distinction seems technical until you realize the Helm worked on gods. No one can look away from nothing."
  },
  "helm_of_achilles": {
    "name": "Helm of Achilles", "symbol": "[", "color": [200,200,80],
    "weight": 4.0, "min_level": 60,
    "slot": "head", "tier": 5, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"slash": 0.2, "fire": 0.1, "magic": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a bronze helm with a tall horse-hair crest",
    "floorSpawnWeight": RARE, "value": 8500,
    "lore": "Hephaestus forged Achilles' new armour when Patroclus died wearing the old set. The helmet had a crest of horse-hair and rang like a bell. Achilles wore it for the last weeks of his life. It was awarded after his death to Odysseus over Ajax — a decision based on rhetoric and political judgement, not martial merit. The armour was better than both arguments."
  },
  "great_helm_of_galahad": {
    "name": "Great Helm of Galahad", "symbol": "[", "color": [255,255,240],
    "weight": 5.0, "min_level": 60,
    "slot": "head", "tier": 5, "material": "adamantine",
    "ac_bonus": 4, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.3, "slash": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a white helm with a red cross on the cheek",
    "floorSpawnWeight": RARE, "value": 8500,
    "lore": "Galahad arrived at Camelot with a plain white shield and no name. He sat in the Siege Perilous — the seat that killed anyone not pure enough — and nothing happened. He was the only knight who completed the Grail quest because he was the only one who had not already compromised himself. His father Lancelot came within inches of it. Lancelot's single lapse in virtue cost him the quest and gave the world Galahad. The Grail works through irony."
  },
  "vambraces_of_achilles": {
    "name": "Vambraces of Achilles", "symbol": "[", "color": [200,195,150],
    "weight": 2.0, "min_level": 55,
    "slot": "arms", "tier": 5, "material": "adamantine",
    "ac_bonus": 3, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"slash": 0.2, "pierce": 0.2, "fire": 0.1},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "bronze arm-guards of divine make",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "Part of the panoply Hephaestus forged. The vambraces bore scenes of working men and women — farmers, shepherds, dancers — as though the smith god remembered that war is fought over ordinary lives. The warriors who wore them over centuries may not have understood the pictures. The pictures were not for them."
  },
  "gauntlets_of_mars": {
    "name": "Gauntlets of Mars", "symbol": "[", "color": [160,80,60],
    "weight": 2.5, "min_level": 55,
    "slot": "hands", "tier": 5, "material": "adamantine",
    "ac_bonus": 3, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"crush": 0.25, "slash": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "iron gauntlets engraved with wolf-heads",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "Mars was the second most worshipped god in Rome after Jupiter. Unlike Ares, his Greek equivalent, he was not merely the god of war but of agriculture and the protection of boundaries — the army that defends fields is the same army that works them. His priests carried sacred shields believed to have fallen from heaven and danced with them in procession every March. The month is named for him. So is Tuesday, through Tiwaz/Tyr."
  },
  "greaves_of_hermes": {
    "name": "Greaves of Hermes", "symbol": "[", "color": [200,220,160],
    "weight": 1.5, "min_level": 50,
    "slot": "feet", "tier": 5, "material": "adamantine",
    "ac_bonus": 2, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"magic": 0.25, "poison": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "winged bronze greaves of incredible lightness",
    "floorSpawnWeight": RARE, "value": 7000,
    "lore": "Hermes' winged sandals — the Talaria — were given him by his father Zeus or possibly won in trade with Perseus or possibly always his. He carried the dead to Hades in them. Perseus borrowed them for the Medusa mission along with the Helm and Kibisis bag. The wings are the most depicted element of Hermes iconography, which is interesting because Hermes himself is most notable for what he carries between places, not the speed."
  },
  "cloak_of_the_morrigan": {
    "name": "Cloak of the Morrigan", "symbol": "[", "color": [80,40,80],
    "weight": 2.0, "min_level": 60,
    "slot": "cloak", "tier": 5, "material": "adamantine",
    "ac_bonus": 3, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.35, "poison": 0.25, "slash": 0.1},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a dark feathered cloak that moves without wind",
    "floorSpawnWeight": RARE, "value": 8000,
    "lore": "The Morrigan — the Phantom Queen — appeared as a crow or raven on the battlefield and chose who lived and died. She approached Cu Chulainn three times in disguise: as a young woman, an eel, a wolf, and a heifer. He rejected and fought each of them. Before his final battle she appeared as an old woman milking a lame cow, and he drank from her and was healed without knowing it. He died anyway. She had been kind to him; he had not recognized it."
  },
  "leggings_of_enkidu": {
    "name": "Leggings of Enkidu", "symbol": "[", "color": [140,120,80],
    "weight": 3.0, "min_level": 50,
    "slot": "legs", "tier": 5, "material": "adamantine",
    "ac_bonus": 4, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"slash": 0.2, "crush": 0.2, "pierce": 0.15},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "rough-worked leather greaves from before metallurgy",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "Enkidu was created by the gods as a wild man to counter Gilgamesh. He lived among animals until a temple prostitute civilised him over seven days. He then challenged Gilgamesh to single combat; they fought to a draw and became friends. The Epic of Gilgamesh is the oldest known written epic. Its central subject is not the monsters they killed together but what Gilgamesh does when Enkidu dies first."
  },
  "mantle_of_elijah": {
    "name": "Mantle of Elijah", "symbol": "[", "color": [160,120,80],
    "weight": 1.5, "min_level": 55,
    "slot": "cloak", "tier": 5, "material": "adamantine",
    "ac_bonus": 2, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.45, "fire": 0.35},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a rough prophetic cloak of undyed wool",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "Elijah's mantle passed to Elisha when Elijah was taken to heaven in a chariot of fire. Elisha used it to part the Jordan River on his return. In Jewish tradition it represents the transfer of prophetic authority — the mantle is the office, not the man. When Elijah threw it on Elisha's shoulders without asking, Elisha left his oxen and ran after him. He was ploughing when it happened. He finished the field first."
  },
  "robe_of_the_magus": {
    "name": "Robe of the Magus", "symbol": "[", "color": [80,60,160],
    "weight": 1.0, "min_level": 55,
    "slot": "shirt", "tier": 5, "material": "adamantine",
    "ac_bonus": 1, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 5,
    "damage_resistances": {"magic": 0.45, "fire": 0.15, "cold": 0.15, "shock": 0.1},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a deep blue robe with silver astronomical diagrams",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "The Magi of the ancient Near East were not magicians in the popular sense — they were scholars of astronomy, dream interpretation, and the hidden correspondences between celestial and earthly events. The Star they followed was either a conjunction of Jupiter and Saturn, a comet, or a nova. They brought gold, frankincense, and myrrh and went home 'another way,' having been warned in a dream not to report back to Herod."
  },
  "boots_of_seven_leagues": {
    "name": "Boots of Seven Leagues", "symbol": "[", "color": [160,100,60],
    "weight": 1.0, "min_level": 40,
    "slot": "feet", "tier": 5, "material": "adamantine",
    "ac_bonus": 1, "enchant_bonus": 0,
    "equip_threshold": 3, "quiz_tier": 4,
    "damage_resistances": {"magic": 0.2},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a pair of worn leather boots that feel ready to move",
    "floorSpawnWeight": RARE, "value": 7000,
    "lore": "In European folklore, seven-league boots take their wearer seven leagues — about 35 km — per step. Hop-o'-My-Thumb stole them from an ogre. Puss in Boots wore them. They appear across French, German, and Scandinavian tales with minor variation: the boots are always disproportionately large on their original owner and always fit the hero perfectly. The folklore does not explain the sizing mechanism."
  },
  "brigandine_of_william_wallace": {
    "name": "Brigandine of Wallace", "symbol": "[", "color": [180,160,120],
    "weight": 5.0, "min_level": 50,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"slash": 0.2, "pierce": 0.25},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a riveted coat of small iron plates over leather",
    "floorSpawnWeight": RARE, "value": 7500,
    "lore": "William Wallace was not the painted barbarian of popular cinema. He was a second son of a minor noble family who became a guerrilla commander, won the Battle of Stirling Bridge by understanding terrain better than the English generals, was eventually captured, and was executed by a method the English used specifically to maximise dishonour. He gave no speech at his death. He denied nothing. The armour is real; the speeches were invented later."
  },
  "cuirass_of_hannibal": {
    "name": "Cuirass of Hannibal", "symbol": "[", "color": [160,140,80],
    "weight": 7.0, "min_level": 55,
    "slot": "body", "tier": 5, "material": "adamantine",
    "ac_bonus": 6, "enchant_bonus": 0,
    "equip_threshold": 4, "quiz_tier": 4,
    "damage_resistances": {"slash": 0.25, "crush": 0.15, "pierce": 0.1},
    "can_be_cursed": False, "cursed": False, "identified": False,
    "unidentified_name": "a Carthaginian officer's bronze cuirass",
    "floorSpawnWeight": RARE, "value": 8000,
    "lore": "Hannibal Barca crossed the Alps with war elephants in 218 BCE and fought Rome for sixteen years on its own soil. He won every major engagement: Trebia, Trasimene, Cannae — Cannae being the most studied battle in military history, used as a model for encirclement tactics by commanders for two millennia. He never took Rome. He was eventually called home to defend Carthage, lost one battle, and died in exile. He won the tactics and lost the war. Military academies still teach him."
  },
}

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    weapon_path  = os.path.join(BASE, "items", "weapon.json")
    access_path  = os.path.join(BASE, "items", "accessory.json")
    armor_path   = os.path.join(BASE, "items", "armor.json")
    shield_path  = os.path.join(BASE, "items", "shield.json")

    weapons    = load(weapon_path)
    accessorys = load(access_path)
    armors     = load(armor_path)
    shields    = load(shield_path)

    # Check for duplicates and add
    def merge(existing, new_items, label):
        added = 0
        skipped = 0
        for key, val in new_items.items():
            if key in existing:
                skipped += 1
            else:
                existing[key] = val
                added += 1
        print(f"  {label}: +{added} added, {skipped} skipped (already existed)")
        return added

    print("Adding legendary items...")
    w = merge(weapons,    WEAPONS,    "weapons")
    a = merge(accessorys, ACCESSORIES, "accessories")
    s = merge(shields,    SHIELDS,    "shields")
    ar = merge(armors,    ARMOR,      "armor")

    save(weapon_path,  weapons)
    save(access_path,  accessorys)
    save(armor_path,   armors)
    save(shield_path,  shields)

    total = w + a + s + ar
    print(f"\nDone. Total items added: {total}")
    print(f"  weapons={w}, accessories={a}, shields={s}, armor={ar}")

    # Verify counts
    expected = {"weapons": 40, "accessories": 35, "shields": 5, "armor": 20}
    actual   = {"weapons": w,  "accessories": a,  "shields": s, "armor": ar}
    for k in expected:
        if actual[k] != expected[k]:
            print(f"  WARNING: {k} expected {expected[k]}, got {actual[k]}")

if __name__ == "__main__":
    main()
