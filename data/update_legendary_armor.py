"""
Update legendary armor, shields, and accessories in the game's JSON files.
Modifies existing items and adds new ones.
"""

import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS_DIR = os.path.join(DATA_DIR, "items")


def load_json(filename):
    path = os.path.join(ITEMS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    path = os.path.join(ITEMS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def update_armor(armor):
    changes = []

    # 1. helm_of_hades: add onEquipStatus "invisible"
    if "helm_of_hades" in armor:
        armor["helm_of_hades"]["onEquipStatus"] = "invisible"
        changes.append("helm_of_hades: added onEquipStatus='invisible'")

    # 2. boots_of_seven_leagues: add onEquipStatus "hasted"
    if "boots_of_seven_leagues" in armor:
        armor["boots_of_seven_leagues"]["onEquipStatus"] = "hasted"
        changes.append("boots_of_seven_leagues: added onEquipStatus='hasted'")

    # 3. green_knights_plate: add onEquipStatus "life_save", keep special_effect
    if "green_knights_plate" in armor:
        item = armor["green_knights_plate"]
        assert item.get("special_effect") == "regen_2", "Expected special_effect='regen_2'"
        item["onEquipStatus"] = "life_save"
        changes.append("green_knights_plate: added onEquipStatus='life_save' (kept special_effect='regen_2')")

    # 4. helm_of_achilles: no stat bonus field in armor schema
    if "helm_of_achilles" in armor:
        changes.append("helm_of_achilles: NOTE - armor.json has no stat bonus fields; DEX+3 needs code-side handling or a new field")

    # 5. dragon_mail_of_sigurd: add onEquipStatus "fire_resist"
    if "dragon_mail_of_sigurd" in armor:
        item = armor["dragon_mail_of_sigurd"]
        existing_fire = item.get("damage_resistances", {}).get("fire")
        item["onEquipStatus"] = "fire_resist"
        changes.append(f"dragon_mail_of_sigurd: added onEquipStatus='fire_resist' (kept fire resistance={existing_fire})")

    # 6. hide_of_nemean_lion: update lore to mention weapon invulnerability
    if "hide_of_nemean_lion" in armor:
        item = armor["hide_of_nemean_lion"]
        if "lore" in item:
            if "invulnerable" not in item["lore"].lower():
                item["lore"] += " The hide renders its wearer virtually invulnerable to conventional weapons — only magical or divine arms can pierce it."
                changes.append("hide_of_nemean_lion: appended invulnerability note to lore")
            else:
                changes.append("hide_of_nemean_lion: lore already mentions invulnerability")
        else:
            changes.append("hide_of_nemean_lion: NOTE - no lore field found")

    # 7. breastplate_of_joan: add onEquipStatus "blessed"
    if "breastplate_of_joan" in armor:
        armor["breastplate_of_joan"]["onEquipStatus"] = "blessed"
        changes.append("breastplate_of_joan: added onEquipStatus='blessed'")

    # --- Add new armor pieces ---
    new_armor = {
        "aegishjalmr": {
            "name": "Aegishjalmr",
            "slot": "head",
            "tier": 4,
            "material": "mithril",
            "ac_bonus": 4,
            "enchant_bonus": 0,
            "equip_threshold": 4,
            "quiz_tier": 4,
            "damage_resistances": {"fire": 0.4, "magic": 0.3},
            "weight": 3.0,
            "value": 5000,
            "min_level": 28,
            "identified": False,
            "unidentified_name": "a helm inscribed with a terrifying rune",
            "lore": "The Helm of Awe, \u00e6gishj\u00e1lmr, was worn by the dragon Fafnir. All who looked upon it were struck with dread. The Volsunga saga records that Sigurd took it from the dragon's hoard, and with it gained the power to terrify armies with a glance.",
            "containerLootTier": "rare",
            "can_be_cursed": False,
            "symbol": "[",
            "color": [180, 180, 220],
            "floorSpawnWeight": {"1-27": 0, "28-60": 15, "61-100": 8}
        },
        "winged_sandals_of_hermes": {
            "name": "Winged Sandals of Hermes",
            "slot": "feet",
            "tier": 4,
            "material": "gold",
            "ac_bonus": 1,
            "enchant_bonus": 0,
            "equip_threshold": 3,
            "quiz_tier": 3,
            "damage_resistances": {"magic": 0.2},
            "weight": 0.5,
            "value": 5500,
            "min_level": 25,
            "identified": False,
            "unidentified_name": "sandals with small golden wings at the ankles",
            "lore": "The talaria of Hermes, messenger of the gods, allowed him to fly between Olympus, Earth, and the Underworld in moments. Perseus borrowed them to approach Medusa. These sandals carry their wearer with divine swiftness \u2014 each step covers ground that would take mortals three.",
            "onEquipStatus": "hasted",
            "containerLootTier": "rare",
            "can_be_cursed": False,
            "symbol": "[",
            "color": [255, 215, 0],
            "floorSpawnWeight": {"1-24": 0, "25-60": 12, "61-100": 6}
        },
        "hermes_sandals_early": {
            "name": "Hermes's Sandals",
            "slot": "feet",
            "tier": 1,
            "material": "leather",
            "ac_bonus": 0,
            "enchant_bonus": 0,
            "equip_threshold": 1,
            "quiz_tier": 1,
            "damage_resistances": {},
            "weight": 0.5,
            "value": 400,
            "min_level": 5,
            "identified": False,
            "unidentified_name": "a pair of sandals with tiny wing motifs",
            "lore": "A mortal imitation of Hermes's divine talaria. The wings are decorative, but the sandals carry a fragment of the messenger god's speed. They will not carry you between worlds, but they will carry you faster than your enemies expect.",
            "onEquipStatus": "hasted",
            "containerLootTier": "uncommon",
            "can_be_cursed": False,
            "symbol": "[",
            "color": [200, 180, 140],
            "floorSpawnWeight": {"1-5": 5, "6-20": 15, "21-40": 8, "41-100": 2}
        }
    }

    for key, val in new_armor.items():
        if key not in armor:
            armor[key] = val
            changes.append(f"ADDED new armor: {key} ({val['name']})")
        else:
            changes.append(f"SKIPPED {key}: already exists")

    return changes


def update_shields(shields):
    changes = []

    # aegis_of_athena: add petrifying resistance
    if "aegis_of_athena" in shields:
        item = shields["aegis_of_athena"]
        item["damage_resistances"]["petrifying"] = 1.0
        changes.append("aegis_of_athena: added petrifying=1.0 to damage_resistances")

    return changes


def update_accessories(accessories):
    changes = []

    # 1. necklace_of_harmonia: add cursed flag, add CON-2 as secondary stat
    if "necklace_of_harmonia" in accessories:
        item = accessories["necklace_of_harmonia"]
        item["cursed"] = True
        # The effects dict supports stat+amount. Add a secondary_stat pattern for CON-2
        # Looking at existing items, effects can have stat+amount alongside status.
        # We'll add a second_stat/second_amount pair for CON-2
        item["effects"]["second_stat"] = "CON"
        item["effects"]["second_amount"] = -2
        changes.append("necklace_of_harmonia: added cursed=true, added second_stat CON -2")

    # 2. draupnir: change INT+4 to INT+2
    if "draupnir" in accessories:
        item = accessories["draupnir"]
        old_amount = item["effects"].get("amount")
        item["effects"]["amount"] = 2
        changes.append(f"draupnir: changed INT amount from {old_amount} to 2")

    # 3. ring_of_gyges: add cursed flag
    if "ring_of_gyges" in accessories:
        item = accessories["ring_of_gyges"]
        item["cursed"] = True
        changes.append("ring_of_gyges: added cursed=true")

    # --- Add new accessories ---
    new_accessories = {
        "ariadnes_thread": {
            "name": "Ariadne's Thread",
            "slot": "amulet",
            "effects": {"status": "searching", "duration": -1, "stat": "WIS", "amount": 2},
            "equip_threshold": 3,
            "quiz_tier": 3,
            "weight": 0.2,
            "value": 3000,
            "min_level": 22,
            "identified": False,
            "unidentified_name": "a silver thread wound into a pendant",
            "lore": "Ariadne gave this thread to Theseus so he could find his way out of the Labyrinth. The thread remembers every path it has traveled and guides its bearer toward the exit. In the myth, Theseus abandoned Ariadne on Naxos \u2014 but the thread remained faithful.",
            "containerLootTier": "rare",
            "symbol": "=",
            "color": [220, 220, 255]
        },
        "eponas_charm": {
            "name": "Epona's Charm",
            "slot": "amulet",
            "effects": {"status": "searching", "duration": -1, "stat": "PER", "amount": 1},
            "equip_threshold": 2,
            "quiz_tier": 1,
            "weight": 0.3,
            "value": 800,
            "min_level": 8,
            "identified": False,
            "unidentified_name": "a small horse-shaped charm",
            "lore": "Epona was the Celtic goddess of horses, travelers, and safe journeys. Her charm ensures the traveler always arrives in safe harbor \u2014 never in a dead end, never in an ambush. The Romans adopted her worship, unique among Gaulish deities.",
            "containerLootTier": "uncommon",
            "symbol": "=",
            "color": [180, 140, 100]
        },
        "anansis_thread": {
            "name": "Anansi's Thread",
            "slot": "ring",
            "effects": {"stat": "INT", "amount": 2},
            "equip_threshold": 2,
            "quiz_tier": 2,
            "weight": 0.1,
            "value": 1500,
            "min_level": 10,
            "identified": False,
            "unidentified_name": "a ring woven from spider silk",
            "lore": "Anansi the spider-god of the Akan people earned all the stories in the world by outwitting the sky-god Nyame. His thread connects all knowledge \u2014 what you learn once, you never lose. The Ashanti say that every story belongs to Anansi.",
            "containerLootTier": "uncommon",
            "symbol": "=",
            "color": [255, 215, 0]
        },
        "rope_of_izanagi": {
            "name": "Rope of Izanagi",
            "slot": "amulet",
            "effects": {"status": "searching", "duration": -1, "stat": "CON", "amount": 2},
            "equip_threshold": 4,
            "quiz_tier": 4,
            "weight": 0.5,
            "value": 6000,
            "min_level": 52,
            "identified": False,
            "unidentified_name": "a shimenawa rope that hums with spiritual energy",
            "lore": "When Izanagi fled the underworld of Yomi, he sealed the entrance with a great boulder and a sacred rope. The rope divides the world of the living from the dead. Its bearer can feel the boundary thinning \u2014 every trap, every hidden passage, every secret door reveals itself to one who knows where life ends and death begins.",
            "containerLootTier": "legendary",
            "symbol": "=",
            "color": [255, 255, 200]
        },
        "girdle_of_hippolyta": {
            "name": "Girdle of Hippolyta",
            "slot": "amulet",
            "effects": {"stat": "STR", "amount": 3},
            "equip_threshold": 3,
            "quiz_tier": 3,
            "weight": 1.0,
            "value": 4000,
            "min_level": 22,
            "identified": False,
            "unidentified_name": "a wide golden war-belt",
            "lore": "Hippolyta, queen of the Amazons, wore this girdle as proof of her supremacy among warriors. Ares himself gave it to her. Heracles took it as his ninth labor \u2014 though whether by force or diplomacy depends on which version you trust. The belt makes its wearer formidable in close combat.",
            "containerLootTier": "rare",
            "symbol": "=",
            "color": [255, 200, 50]
        }
    }

    for key, val in new_accessories.items():
        if key not in accessories:
            accessories[key] = val
            changes.append(f"ADDED new accessory: {key} ({val['name']})")
        else:
            changes.append(f"SKIPPED {key}: already exists")

    return changes


def main():
    print("=" * 60)
    print("Updating Legendary Armor, Shields, and Accessories")
    print("=" * 60)

    # --- Armor ---
    print("\n--- ARMOR (armor.json) ---")
    armor = load_json("armor.json")
    armor_changes = update_armor(armor)
    for c in armor_changes:
        print(f"  {c}")
    save_json("armor.json", armor)
    print(f"  Saved armor.json ({len(armor)} total items)")

    # --- Shields ---
    print("\n--- SHIELDS (shield.json) ---")
    shields = load_json("shield.json")
    shield_changes = update_shields(shields)
    for c in shield_changes:
        print(f"  {c}")
    save_json("shield.json", shields)
    print(f"  Saved shield.json ({len(shields)} total items)")

    # --- Accessories ---
    print("\n--- ACCESSORIES (accessory.json) ---")
    accessories = load_json("accessory.json")
    acc_changes = update_accessories(accessories)
    for c in acc_changes:
        print(f"  {c}")
    save_json("accessory.json", accessories)
    print(f"  Saved accessory.json ({len(accessories)} total items)")

    # --- Summary ---
    all_changes = armor_changes + shield_changes + acc_changes
    modifications = [c for c in all_changes if not c.startswith("ADDED") and not c.startswith("SKIPPED") and "NOTE" not in c]
    additions = [c for c in all_changes if c.startswith("ADDED")]
    notes = [c for c in all_changes if "NOTE" in c]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print(f"  Modified: {len(modifications)} existing items")
    print(f"  Added:    {len(additions)} new items")
    if notes:
        print(f"  Notes:    {len(notes)}")
        for n in notes:
            print(f"    -> {n}")
    print("=" * 60)


if __name__ == "__main__":
    main()
