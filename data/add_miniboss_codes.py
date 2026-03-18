"""
Add mini-boss reward code scrolls (QUEST- prefix) to scroll.json
and boss_scroll_id to each mini-boss's treasure in monsters.json.
"""
import json
import os

SCROLL_PATH = os.path.join(os.path.dirname(__file__), 'items', 'scroll.json')
MONSTER_PATH = os.path.join(os.path.dirname(__file__), 'monsters.json')

# Mini-boss definitions: (monster_id, scroll_id, scroll_name, code, lore_seal, color)
MINI_BOSSES = [
    ("arachne",              "scroll_of_arachne",      "Scroll of Arachne",         "QUEST-WEAVER-I",       "Sealed with a strand of unbreakable silk."),
    ("lamia",                "scroll_of_lamia",         "Scroll of Lamia",           "QUEST-SERPENT-II",     "Sealed with a serpent's tear."),
    ("talos",                "scroll_of_talos",         "Scroll of Talos",           "QUEST-BRONZE-III",     "Sealed with molten bronze."),
    ("echidna",              "scroll_of_echidna",       "Scroll of Echidna",         "QUEST-MOTHER-IV",      "Sealed with the mark of the Mother of Monsters."),
    ("erlking",              "scroll_of_the_erlking",   "Scroll of the Erlking",     "QUEST-FOREST-V",       "Sealed with a frozen leaf that never wilts."),
    ("camazotz",             "scroll_of_camazotz",      "Scroll of Camazotz",        "QUEST-NIGHT-VI",       "Sealed with a bat's wing pressed in wax."),
    ("cacus",                "scroll_of_cacus",         "Scroll of Cacus",           "QUEST-FLAME-VII",      "Sealed with a scorch mark that still smolders."),
    ("the_sphinx",           "scroll_of_the_sphinx",    "Scroll of the Sphinx",      "QUEST-RIDDLE-VIII",    "Sealed with a riddle that answers itself."),
    ("rangda",               "scroll_of_rangda",        "Scroll of Rangda",          "QUEST-WITCH-IX",       "Sealed with a lock of white hair."),
    ("nemean_lion",          "scroll_of_the_lion",      "Scroll of the Nemean Lion", "QUEST-LION-X",         "Sealed with an impenetrable golden hair."),
    ("baba_yaga",            "scroll_of_baba_yaga",     "Scroll of Baba Yaga",       "QUEST-CRONE-XI",       "Sealed with iron teeth marks."),
    ("jormungandr_juvenile", "scroll_of_jormungandr",   "Scroll of Jörmungandr",    "QUEST-WYRM-XII",       "Sealed with a scale from the World Serpent."),
    ("sets_jackal",          "scroll_of_set",           "Scroll of Set",             "QUEST-CHAOS-XIII",     "Sealed with red sand from the desert of storms."),
    ("green_knight",         "scroll_of_the_green",     "Scroll of the Green Knight","QUEST-GREEN-XIV",      "Sealed with a holly branch that bleeds sap."),
    ("charybdis",            "scroll_of_charybdis",     "Scroll of Charybdis",       "QUEST-MAELSTROM-XV",   "Sealed with salt water that never dries."),
    ("ravanas_arm",          "scroll_of_ravana",        "Scroll of Ravana",          "QUEST-DEMON-XVI",      "Sealed with the sigil of Lanka."),
    ("wendigo",              "scroll_of_the_wendigo",   "Scroll of the Wendigo",     "QUEST-HUNGER-XVII",    "Sealed with frost that bites the fingers."),
    ("wild_hunt_captain",    "scroll_of_the_hunt",      "Scroll of the Wild Hunt",   "QUEST-HUNT-XVIII",     "Sealed with a horn blast frozen in wax."),
    ("anansi",               "scroll_of_anansi",        "Scroll of Anansi",          "QUEST-SPIDER-XIX",     "Sealed with a web that glints like gold."),
    ("nidhoggr_fragment",    "scroll_of_nidhoggr",      "Scroll of Níðhöggr",       "QUEST-ROOT-XX",        "Sealed with bark from the World Tree."),
]


def main():
    # --- Add scrolls ---
    with open(SCROLL_PATH, 'r', encoding='utf-8') as f:
        scrolls = json.load(f)

    added_scrolls = 0
    for monster_id, scroll_id, scroll_name, code, seal_lore in MINI_BOSSES:
        if scroll_id not in scrolls:
            scrolls[scroll_id] = {
                "name": scroll_name,
                "symbol": "?",
                "color": [255, 200, 80],
                "weight": 0.1,
                "item_class": "scroll",
                "min_level": 1,
                "quiz_tier": 1,
                "quiz_threshold": 1,
                "effect": "boss_reward",
                "power": code,
                "unidentified_name": scroll_name,
                "identified": True,
                "lore": f"{seal_lore} A reward scroll from Dad — show him this code!",
                "read_threshold": 2
            }
            added_scrolls += 1

    with open(SCROLL_PATH, 'w', encoding='utf-8') as f:
        json.dump(scrolls, f, indent=2, ensure_ascii=False)

    print(f"Added {added_scrolls} mini-boss scrolls to scroll.json")

    # --- Add boss_scroll_id to monster treasure ---
    with open(MONSTER_PATH, 'r', encoding='utf-8') as f:
        monsters = json.load(f)

    updated_monsters = 0
    for monster_id, scroll_id, scroll_name, code, seal_lore in MINI_BOSSES:
        if monster_id in monsters:
            m = monsters[monster_id]
            if 'treasure' not in m:
                m['treasure'] = {
                    "gold": [20, 60],
                    "item_chance": 1.0,
                    "item_tier": 2
                }
            m['treasure']['boss_scroll_id'] = scroll_id
            updated_monsters += 1
        else:
            print(f"  WARNING: Monster '{monster_id}' not found!")

    with open(MONSTER_PATH, 'w', encoding='utf-8') as f:
        json.dump(monsters, f, indent=2, ensure_ascii=False)

    print(f"Updated {updated_monsters} mini-bosses with boss_scroll_id in monsters.json")

    # --- Verify ---
    print("\nVerification:")
    for monster_id, scroll_id, scroll_name, code, _ in MINI_BOSSES:
        m = monsters.get(monster_id, {})
        t = m.get('treasure', {})
        bsid = t.get('boss_scroll_id', 'MISSING')
        s = scrolls.get(scroll_id, {})
        scode = s.get('power', 'MISSING')
        status = "OK" if bsid == scroll_id and scode == code else "FAIL"
        print(f"  [{status}] {monster_id:25s} -> {code}")


if __name__ == '__main__':
    main()
