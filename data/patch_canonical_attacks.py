#!/usr/bin/env python3
"""Patch monsters.json to add missing canonical attacks from D&D/mythology sources.

Also fixes AI patterns so monsters with ranged special attacks can use them at distance.
"""
import json
from pathlib import Path

MONSTERS_PATH = Path(__file__).parent / "monsters.json"

# ── New attacks to ADD (not replace) ──────────────────────────────────────────
# Format: monster_id -> list of new attack dicts to append
NEW_ATTACKS = {
    # ── DRAGONS: need bite / tail / wing ──────────────────────────────────
    "young_black_dragon": [
        {"name": "bite", "damage": "2d8", "type": "physical"},
        {"name": "tail lash", "damage": "1d8", "type": "physical",
         "effect": "slowed", "effect_chance": 0.25, "effect_duration": 3},
    ],
    "young_red_dragon": [
        {"name": "bite", "damage": "2d10", "type": "physical"},
        {"name": "tail lash", "damage": "1d10", "type": "physical",
         "effect": "slowed", "effect_chance": 0.25, "effect_duration": 3},
    ],
    "young_dragon": [
        {"name": "bite", "damage": "3d8+2", "type": "physical"},
        {"name": "tail lash", "damage": "2d8+1", "type": "physical",
         "effect": "slowed", "effect_chance": 0.3, "effect_duration": 4},
    ],
    "adult_blue_dragon": [
        {"name": "bite", "damage": "3d10+1", "type": "physical"},
        {"name": "tail strike", "damage": "2d8+1", "type": "physical",
         "effect": "slowed", "effect_chance": 0.3, "effect_duration": 4},
        {"name": "wing buffet", "damage": "2d8", "type": "physical",
         "effect": "stunned", "effect_chance": 0.2, "effect_duration": 2},
    ],
    "adult_red_dragon": [
        {"name": "tail strike", "damage": "3d8+1", "type": "physical",
         "effect": "slowed", "effect_chance": 0.3, "effect_duration": 4},
        {"name": "wing buffet", "damage": "2d10", "type": "physical",
         "effect": "stunned", "effect_chance": 0.2, "effect_duration": 2},
    ],
    "elder_dragon": [
        {"name": "bite", "damage": "5d8+3", "type": "physical"},
        {"name": "wing buffet", "damage": "4d6+2", "type": "physical",
         "effect": "stunned", "effect_chance": 0.25, "effect_duration": 3},
    ],
    "ancient_dragon": [
        {"name": "tail strike", "damage": "4d8+3", "type": "physical",
         "effect": "slowed", "effect_chance": 0.35, "effect_duration": 5},
        {"name": "wing buffet", "damage": "4d6+3", "type": "physical",
         "effect": "stunned", "effect_chance": 0.25, "effect_duration": 3},
    ],

    # ── BEHOLDERS: more eye ray variety ───────────────────────────────────
    "beholder": [
        # Rename existing generics + add new rays (rename handled separately)
        {"name": "disintegration_ray", "damage": "4d8+2", "type": "magic"},
        {"name": "slow_ray", "damage": "1d6", "type": "magic",
         "effect": "slowed", "effect_chance": 0.7, "effect_duration": 8},
        {"name": "bite", "damage": "2d6+1", "type": "physical"},
    ],
    "beholder_spawn": [
        {"name": "confusion_ray", "damage": "1d8", "type": "magic",
         "effect": "confused", "effect_chance": 0.4, "effect_duration": 5},
    ],
    "elder_beholder": [
        {"name": "slow_ray", "damage": "2d6+1", "type": "magic",
         "effect": "slowed", "effect_chance": 0.8, "effect_duration": 10},
        {"name": "charm_ray", "damage": "1d8+1", "type": "magic",
         "effect": "confused", "effect_chance": 0.7, "effect_duration": 12},
        {"name": "bite", "damage": "3d6+2", "type": "physical"},
    ],

    # ── VAMPIRES: spawn needs more attacks ────────────────────────────────
    "vampire_spawn": [
        {"name": "claw", "damage": "2d6+2", "type": "slash"},
        {"name": "charm_gaze", "damage": "0d0", "type": "magic",
         "effect": "confused", "effect_chance": 0.35, "effect_duration": 6},
    ],

    # ── MYTHOLOGICAL: iconic missing abilities ────────────────────────────
    "harpy": [
        {"name": "charm_song", "damage": "0d0", "type": "magic",
         "effect": "confused", "effect_chance": 0.5, "effect_duration": 8},
    ],
    "chimera": [
        {"name": "goat_gore", "damage": "2d6", "type": "physical",
         "effect": "stunned", "effect_chance": 0.2, "effect_duration": 2},
    ],
    "manticore": [
        {"name": "bite", "damage": "2d8", "type": "physical"},
    ],
    "cockatrice": [
        {"name": "petrifying_touch", "damage": "1d4", "type": "magic",
         "effect": "paralyzed", "effect_chance": 0.6, "effect_duration": 12},
    ],
    "mimic": [
        {"name": "adhesive_slam", "damage": "1d8", "type": "physical",
         "effect": "slowed", "effect_chance": 0.5, "effect_duration": 6},
    ],
    "naga_guardian": [
        {"name": "poison_spit", "damage": "2d6", "type": "poison",
         "effect": "poisoned", "effect_chance": 0.5, "effect_duration": 8},
    ],

    # ── UNDEAD: wraith + gelatinous cube under-armed ──────────────────────
    "wraith": [
        {"name": "chilling_wail", "damage": "1d4", "type": "cold",
         "effect": "feared", "effect_chance": 0.4, "effect_duration": 5},
    ],
    "gelatinous_cube": [
        {"name": "dissolve", "damage": "1d6", "type": "acid",
         "effect": "weakened", "effect_chance": 0.4, "effect_duration": 8},
    ],

    # ── MIND FLAYERS: elder needs tentacle fallback ───────────────────────
    "elder_mind_flayer": [
        {"name": "tentacle_grasp", "damage": "3d6+2", "type": "physical",
         "effect": "paralyzed", "effect_chance": 0.3, "effect_duration": 4},
    ],
}

# ── Rename existing poorly-named attacks ──────────────────────────────────────
RENAME_ATTACKS = {
    "beholder": {
        "eye_ray": "paralyzing_ray",
        "eye_ray_2": "confusion_ray",
        "eye_ray_3": "blinding_ray",
    },
    "beholder_spawn": {
        "gazes": "paralyzing_gaze",
        "bites": "bite",
    },
    "mind_flayer_thrall": {
        "slams": "slam",
        "mind blasts": "mind_blast",
        "extracts": "brain_extraction",
    },
    "elder_mind_flayer": {
        "brain_feast": "brain_extraction",
    },
}

# ── AI pattern changes: monsters with ranged specials need ranged AI ──────────
AI_PATTERN_CHANGES = {
    # Harpy: has charm_song (ranged magical attack) — needs to use it at distance
    "harpy": "ranged",
    # Naga guardian: adding poison_spit (ranged) — should kite and spit
    "naga_guardian": "ranged",
    # Banshee: has death_wail (ranged) — should use it at distance, not just melee
    "banshee": "ranged",
    # Wraith: adding chilling_wail — should use at distance
    "wraith": "ranged",
    # Elder mind flayer: has psionic_blast (ranged) — should kite like regular mind_flayer
    "elder_mind_flayer": "ranged",
    # Basilisk + lesser: gaze is ranged in canon — should lock eyes from distance
    "basilisk": "ranged",
    "basilisk_lesser": "ranged",
    # Vampire lord: has charm_gaze — should use at range then close in
    "vampire_lord": "ranged",
}

# ── Fix medusa_gorgon null attack names ───────────────────────────────────────
MEDUSA_BOSS_ATTACK_NAMES = [
    "serpent_fang",    # pierce attack
    "venom_strike",    # poison attack
    "petrifying_gaze", # magic attack
]


def main():
    data = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    changes = 0

    # 1. Add new attacks
    for mid, new_atks in NEW_ATTACKS.items():
        if mid not in data:
            print(f"  WARNING: {mid} not found in monsters.json — skipping")
            continue
        m = data[mid]
        existing_names = {a.get("name", "").lower() for a in m["attacks"]}
        for atk in new_atks:
            if atk["name"].lower() in existing_names:
                print(f"  SKIP: {mid} already has '{atk['name']}'")
                continue
            m["attacks"].append(atk)
            print(f"  ADD: {mid} <- {atk['name']} ({atk['damage']} {atk['type']})")
            changes += 1

    # 2. Rename poorly-named attacks
    for mid, renames in RENAME_ATTACKS.items():
        if mid not in data:
            continue
        for atk in data[mid]["attacks"]:
            old_name = atk.get("name", "")
            if old_name in renames:
                atk["name"] = renames[old_name]
                print(f"  RENAME: {mid} '{old_name}' -> '{atk['name']}'")
                changes += 1

    # 3. Fix medusa_gorgon null attack names
    if "medusa_gorgon" in data:
        m = data["medusa_gorgon"]
        for i, atk in enumerate(m["attacks"]):
            if "name" not in atk or atk.get("name") is None:
                atk["name"] = MEDUSA_BOSS_ATTACK_NAMES[i]
                print(f"  FIX: medusa_gorgon attack[{i}] named '{atk['name']}'")
                changes += 1
        # Also add gaze effect to the petrifying_gaze attack (3rd attack)
        if len(m["attacks"]) >= 3:
            gaze = m["attacks"][2]
            if "effect" not in gaze or gaze.get("effect") is None:
                gaze["effect"] = "paralyzed"
                gaze["effect_chance"] = 0.45
                gaze["effect_duration"] = 4
                print(f"  FIX: medusa_gorgon petrifying_gaze now applies paralyzed")
                changes += 1

    # 4. Change AI patterns for monsters with ranged specials
    for mid, new_ai in AI_PATTERN_CHANGES.items():
        if mid not in data:
            continue
        old_ai = data[mid].get("ai_pattern", "aggressive")
        if old_ai != new_ai:
            data[mid]["ai_pattern"] = new_ai
            print(f"  AI: {mid} '{old_ai}' -> '{new_ai}'")
            changes += 1

    # Write back
    MONSTERS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nDone — {changes} changes applied to monsters.json")

    # Verify: print attack counts for all changed monsters
    print("\n-- Attack counts after patch --")
    all_changed = set(NEW_ATTACKS) | set(RENAME_ATTACKS) | set(AI_PATTERN_CHANGES) | {"medusa_gorgon"}
    for mid in sorted(all_changed):
        if mid in data:
            m = data[mid]
            atk_names = [a.get("name", "???") for a in m["attacks"]]
            ai = m.get("ai_pattern", "aggressive")
            print(f"  {mid} (L{m.get('min_level','?')}, {ai}): {len(atk_names)} attacks -> {', '.join(atk_names)}")


if __name__ == "__main__":
    main()
