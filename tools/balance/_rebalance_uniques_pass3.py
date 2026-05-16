"""Third pass — fine-tune F80/F90 split.

After pass 2, F80=12 and F90=10. Spec target is F80=8±1 and F90=5±1.
Lore constraints make perfect 8/5 impossible (too many divine weapons in
world myth), but we can move chandrahasa, sudarshana, and stormbringer-class
items to better positions.

Final intent: F80=11, F90=7.

Move chandrahasa F92->F87  — Shiva's gift to Ravana, divine but Ravana fell
   to Rama, not Ragnarok. Better fit alongside Excalibur-tier than alongside
   stormbringer.
Move sudarshana F93->F89  — Vishnu's discus is divine destroyer-tier but
   has explicit divine-historical use (cut Shiva's head, killed asuras);
   not Ragnarok / world-end.
Move gungnir F91->F89  — Odin's spear is named at Ragnarok but also
   throughout history as a divine king-tool. F89 keeps it boundary-divine.
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
        f"Pass 3 trim: peak={peak}, base={new_dmg} "
        f"(= curve.weapon_base_damage({peak}) x {mult})."
    )


SHIFTS = {
    "chandrahasa": {"peak": 87, "mult": 1.65, "spread": 12},  # back to F80s
    # sudarshana stays F93 (Vishnu's discus IS Ragnarok-tier for Hindu eschatology — Kalki rides at end of Kali Yuga)
    # gungnir stays F91 (Odin's Ragnarok spear)
}


def main() -> None:
    with WEAPON_JSON.open(encoding="utf-8") as f:
        weapons = json.load(f)
    for key, plan in SHIFTS.items():
        shift(weapons[key], **plan)
        print(f"Shifted {key} -> F{plan['peak']}")
    with WEAPON_JSON.open("w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Wrote {WEAPON_JSON}")


if __name__ == "__main__":
    main()
