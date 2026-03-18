#!/usr/bin/env python3
"""Update legendary weapons in weapon.json with approved balance changes."""

import json
import os

LEGENDARY_UPDATES = {
    # === SWORDS 1H ===
    "excalibur": {
        "stunChance": 0.05,
        "knockback": False,
        "critMultiplier": 2.5,
        "onEquipStatus": "life_save",
        "killHealAmount": 5,
        "chainMultipliers": [0.3, 0.7, 1.2, 1.8, 2.5, 3.4, 4.5, 5.8, 7.5, 10.0],
        "maxChainLength": 10,
    },
    "gram": {
        "bleedChance": 0.15,
        "critMultiplier": 2.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "fragarach": {
        "ignoreShield": True,
        "stunChance": 0.25,
        "damageTypes": ["pierce", "magic", "holy"],
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "joyeuse": {
        "stunChance": 0.25,
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5, 8.0],
        "maxChainLength": 10,
    },
    "skofnung": {
        "bleedChance": 0.20,
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "kusanagi": {
        "knockback": True,
        "reach": 2,
        "damageTypes": ["slash", "magic", "wind"],
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "zulfiqar": {
        "ignoreShield": True,
        "bleedChance": 0.15,
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "kladenets": {
        "counterAttackChance": 0.25,
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "chrysaor": {
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "caliburn": {
        "stunChance": 0.10,
        "critMultiplier": 1.9,
        "growingPower": True,
        "killsToGrow": 10,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "brisingr": {
        "burnChance": 0.35,
        "stunChance": 0.0,
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "mistilteinn": {
        "ignoreShield": True,
        "critMultiplier": 2.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "curtana": {
        "stunChance": 0.10,
        "damageTypes": ["slash", "holy"],
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.5, 3.2, 4.0, 5.0],
        "maxChainLength": 8,
    },

    # === SWORDS 2H ===
    "durendal": {
        "damageTypes": ["slash", "holy"],
        "stunChance": 0.10,
        "ignoreShield": True,
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "tyrfing": {
        "bleedChance": 0.30,
        "ignoreShield": True,
        "critMultiplier": 2.5,
        "baseDamage": 36,
        "cursedMissBacklash": 5,
        "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 3.8, 5.0, 6.5, 8.5],
        "maxChainLength": 8,
    },
    "hrunting": {
        "bleedChance": 0.40,
        "critMultiplier": 1.8,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },

    # === ZWEIHANDER ===
    "caladbolg": {
        "reach": 2,
        "baseDamage": 34,
        "bleedChance": 0.30,
        "stunChance": 0.0,
        "knockback": True,
        "critMultiplier": 2.5,
        "chainMultipliers": [0.5, 1.0, 1.8, 2.8, 3.8, 5.0, 6.5, 8.5],
        "maxChainLength": 8,
    },

    # === SPEARS ===
    "gungnir": {
        "ignoreShield": True,
        "stunChance": 0.0,
        "bleedChance": 0.0,
        "critMultiplier": 2.2,
        "chainMultipliers": [0.7, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5],
        "maxChainLength": 9,
    },
    "gae_bulg": {
        "bleedChance": 0.80,
        "ignoreShield": True,
        "stunChance": 0.15,
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 6.0],
        "maxChainLength": 8,
    },
    "spear_of_longinus": {
        "bleedChance": 0.35,
        "damageTypes": ["pierce", "holy"],
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "trident_of_poseidon": {
        "stunChance": 0.15,
        "knockback": True,
        "damageTypes": ["pierce", "cold", "magic"],
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5],
        "maxChainLength": 9,
    },
    "amenonuhoko": {
        "stunChance": 0.10,
        "damageTypes": ["pierce", "holy", "magic"],
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5],
        "maxChainLength": 9,
    },

    # === WARHAMMER / MACE ===
    "mjolnir": {
        "stunChance": 0.35,
        "knockback": True,
        "damageTypes": ["crush", "shock", "holy"],
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "sharur": {
        "stunChance": 0.20,
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5],
        "maxChainLength": 9,
    },

    # === STAVES ===
    "ruyi_jingu_bang": {
        "reach": 3,
        "stunChance": 0.25,
        "knockback": True,
        "critMultiplier": 2.2,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "laevateinn": {
        "damageTypes": ["magic", "fire", "holy"],
        "stunChance": 0.30,
        "ignoreShield": True,
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "thyrsus": {
        "stunChance": 0.0,
        "confuseChance": 0.50,
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5, 8.0],
        "maxChainLength": 10,
    },
    "rod_of_moses": {
        "reach": 3,
        "poisonChance": 0.30,
        "stunChance": 0.15,
        "knockback": True,
        "damageTypes": ["crush", "holy", "magic"],
        "critMultiplier": 1.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5],
        "maxChainLength": 9,
    },

    # === AXES ===
    "parashu": {
        "stunChance": 0.20,
        "bleedChance": 0.10,
        "critMultiplier": 1.5,
        "chainMultipliers": [1.0, 1.6, 2.2, 2.8, 3.4, 4.0, 4.8, 5.8, 7.0],
        "maxChainLength": 9,
    },
    "labrys": {
        "stunChance": 0.15,
        "bleedChance": 0.20,
        "critMultiplier": 2.0,
        "chainMultipliers": [1.0, 1.6, 2.2, 2.8, 3.4, 4.0, 4.8, 5.8, 7.0],
        "maxChainLength": 9,
    },
    "naegling": {
        "bleedChance": 0.25,
        "critMultiplier": 1.6,
        "chainMultipliers": [1.0, 1.6, 2.2, 2.8, 3.4, 4.0, 4.8, 5.8],
        "maxChainLength": 8,
    },

    # === SCIMITARS ===
    "harpe": {
        "ignoreShield": True,
        "bleedChance": 0.20,
        "critMultiplier": 2.5,
        "petrifyOnCrit": True,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.2, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "chandrahas": {
        "critMultiplier": 1.8,
        "damageTypes": ["slash", "cold", "holy"],
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.5, 4.5, 3.8, 3.0, 2.5],
        "maxChainLength": 9,
    },
    "shamshir_e_zomorrodnegar": {
        "stunChance": 0.30,
        "ignoreShield": True,
        "damageTypes": ["slash", "magic", "holy"],
        "critMultiplier": 2.0,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "sudarshana": {
        "knockback": True,
        "burnChance": 0.20,
        "requiresAmmo": None,
        "critMultiplier": 2.5,
        "damageTypes": ["slash", "fire", "holy"],
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5, 5.5, 6.5, 8.0],
        "maxChainLength": 10,
    },

    # === DAGGERS ===
    "carnwennan": {
        "ignoreShield": True,
        "critMultiplier": 3.5,
        "onEquipStatus": "invisible",
        "chainMultipliers": [0.4, 0.8, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0, 12.0],
        "maxChainLength": 10,
    },
    "ridill": {
        "ignoreShield": True,
        "critMultiplier": 2.8,
        "chainMultipliers": [0.4, 0.8, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0, 12.0],
        "maxChainLength": 10,
    },
    "fragarach_the_whisperer": {
        "bleedChance": 0.10,
        "ignoreShield": True,
        "critMultiplier": 3.0,
        "chainMultipliers": [0.4, 0.8, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0, 12.0],
        "maxChainLength": 10,
    },

    # === BOWS ===
    "gandiva": {
        "requiresAmmo": None,
        "baseDamage": 22,
        "stunChance": 0.10,
        "bleedChance": 0.15,
        "critMultiplier": 2.8,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "fail_not": {
        "critMultiplier": 3.2,
        "chainMultipliers": [0.2, 0.6, 1.2, 1.8, 2.5, 3.5, 4.5, 6.0, 8.0, 11.0],
        "maxChainLength": 10,
    },

    # === SPECIAL/MONSTER DROPS ===
    "soul_reaver": {
        "lifestealPercent": 0.15,
        "bleedChance": 0.30,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        "maxChainLength": 10,
    },
    "dawnbreaker": {
        "stunChance": 0.45,
        "damageTypes": ["slash", "fire", "holy"],
        "critMultiplier": 2.0,
        "burnChance": 0.30,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
    "venomfang": {
        "poisonChance": 0.60,
        "bleedChance": 0.15,
        "critMultiplier": 2.5,
        "chainMultipliers": [0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0],
        "maxChainLength": 9,
    },
}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    weapon_path = os.path.join(script_dir, "items", "weapon.json")

    with open(weapon_path, "r", encoding="utf-8") as f:
        weapons = json.load(f)

    updated = []
    missing = []

    for weapon_id, updates in LEGENDARY_UPDATES.items():
        if weapon_id in weapons:
            for key, value in updates.items():
                weapons[weapon_id][key] = value
            updated.append(weapon_id)
        else:
            missing.append(weapon_id)

    with open(weapon_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {len(updated)} legendary weapons.")
    if missing:
        print(f"WARNING: {len(missing)} weapons NOT FOUND in weapon.json:")
        for m in missing:
            print(f"  - {m}")
    print("\nUpdated weapons:")
    for w in updated:
        print(f"  + {w}")


if __name__ == "__main__":
    main()
