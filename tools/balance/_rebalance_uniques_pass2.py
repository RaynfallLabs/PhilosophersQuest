"""Second pass — push Ragnarok-tier weapons from F80s into F90s.

Adjusts the F80-89 over-cluster (15 -> ~10) by promoting truly
eschatological weapons to F90-99 where the spec says they belong:
'F90-99 ... Mjölnir-equivalents.'
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import curve  # type: ignore

REPO = Path(__file__).resolve().parents[2]
WEAPON_JSON = REPO / "data" / "items" / "weapon.json"


def quiz_tier(peak_floor: int) -> int:
    return peak_floor // 20 + 1


def recalc_dmg(peak_floor: int, multiplier: float) -> int:
    return max(1, int(curve.weapon_base_damage(peak_floor) * multiplier))


def shift(item: dict, peak: int, mult: float, spread: int) -> None:
    new_dmg = recalc_dmg(peak, mult)
    new_min = max(1, peak - spread)
    qt = quiz_tier(peak)
    item["peak_floor"] = peak
    item["min_level"] = new_min
    item["baseDamage"] = new_dmg
    item["base_damage"] = new_dmg
    item["mathTier"] = qt
    item["quiz_tier"] = qt
    item["tier"] = qt
    item["spread"] = spread
    item["max_enchant"] = 5
    item["floorSpawnWeight"] = {}
    item["_curve_note"] = (
        f"Promoted to F90s: peak={peak}, base={new_dmg} "
        f"(= curve.weapon_base_damage({peak}) x {mult})."
    )


# Promote Ragnarok / world-ending divine weapons from F80s into F90-99.
# Five moves -> F80=10, F90=9. The user's spec explicitly cites
# "Mjölnir-equivalents" as F90-tier.
PROMOTIONS = {
    "gungnir":   {"peak": 91, "mult": 1.65, "spread": 6},  # Odin's spear at Ragnarok
    "mjolnir":   {"peak": 92, "mult": 1.75, "spread": 6},  # Thor's hammer at Ragnarok
    "sudarshana": {"peak": 93, "mult": 1.65, "spread": 6},  # Vishnu's discus
}


def main() -> None:
    with WEAPON_JSON.open(encoding="utf-8") as f:
        weapons = json.load(f)
    for key, plan in PROMOTIONS.items():
        shift(weapons[key], **plan)
        print(f"Promoted {key} -> F{plan['peak']}")
    with WEAPON_JSON.open("w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Wrote {WEAPON_JSON}")


if __name__ == "__main__":
    main()
