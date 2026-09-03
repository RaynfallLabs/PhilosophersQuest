"""v2.6.5 ingredient regeneration (2026-09-03).

Strips assorted_monster_parts + family_* from ingredient.json, keeps
the 516 monster primes + 14 trophies + 8 dungeon ingredients, and
makes every monster prime `edible_safe: true` with tier-scaled raw_sp
so the emergency-food fallback survives the delete of assorted_parts.

Reads: data/items/ingredient.json (current)
Writes: data/items/ingredient.json (rewritten)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGREDIENTS_PATH = os.path.join(ROOT, "data", "items", "ingredient.json")
MONSTERS_PATH = os.path.join(ROOT, "data", "monsters.json")


def tier_from_ml(ml: int) -> int:
    if ml <= 15: return 1
    if ml <= 35: return 2
    if ml <= 55: return 3
    if ml <= 80: return 4
    return 5


# raw_sp on a monster prime: eating raw is emergency food.
# T1 gives just 10 SP (a nibble); T5 gives 30 SP (real meat).
_RAW_SP_BY_TIER = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}


def main():
    with open(INGREDIENTS_PATH, encoding="utf-8") as f:
        d = json.load(f)

    kept = {}
    stats = {"kept_prime": 0, "kept_trophy": 0, "kept_dungeon": 0, "deleted": 0}

    # 8 dungeon ingredients — keep as-is
    dungeon_ids = {
        "cave_mushroom", "altar_incense", "swamp_moss", "river_salt",
        "holy_water", "crystal_shard", "deep_iron", "abyssal_kelp",
    }

    for k, v in d.items():
        role = v.get("tier_role")
        if role == "universal":
            # assorted_monster_parts — DELETED
            stats["deleted"] += 1
            continue
        if role == "family":
            # family_* cuts — DELETED
            stats["deleted"] += 1
            continue
        if k in dungeon_ids:
            kept[k] = v
            stats["kept_dungeon"] += 1
            continue
        if role == "trophy":
            kept[k] = v
            stats["kept_trophy"] += 1
            continue
        if role == "prime":
            # Make it edible_safe so raw eating is emergency food.
            new_v = dict(v)
            ml = int(v.get("min_level", 1))
            tier = tier_from_ml(ml)
            new_v["edible_safe"] = True
            new_v["raw_sp"] = _RAW_SP_BY_TIER[tier]
            kept[k] = new_v
            stats["kept_prime"] += 1
            continue
        # Unknown role — keep for safety
        kept[k] = v
        stats["kept_prime"] += 1  # count for the summary

    with open(INGREDIENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=True, indent=1)

    print(f"wrote {len(kept)} ingredients to {INGREDIENTS_PATH}")
    print(f"  stats: {stats}")


if __name__ == "__main__":
    main()
