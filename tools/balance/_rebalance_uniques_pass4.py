"""Pass 4 — bump new F10-19 items so their base damage matches the
2.0x curve effective ratio that existing F10-19 uniques exhibit.

The unified curve returns very small integer base damage at low floors
(curve(15) = 2, curve(18) = 3). At those scales a 1.65x multiplier
rounds down and produces a 1.0-1.5x effective ratio. The user's
existing F10-19 uniques all read 2.0x once int() rounding is applied.

This pass aligns the four new F10-19 items (cain_club, wepwawet_mace,
cuchulainn_hurley, mwindo_axe) to that same effective bound — these
are 'signature' weapons in their tier, so 2.0x curve damage is fine.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEAPON_JSON = REPO / "data" / "items" / "weapon.json"

# New base damages chosen to match the band's curve-rounding effect:
# curve(12) = 1, curve(14) = 2, curve(16) = 2, curve(18) = 3
# 2.0x ratio in integer-rounded space:
BUMPS = {
    "cain_club":         {"base": 4, "value": 240},  # was 1 -> 4 (raise to band floor)
    "wepwawet_mace":     {"base": 4, "value": 240},  # was 3 -> 4
    "cuchulainn_hurley": {"base": 4, "value": 240},  # was 3 -> 4
    "mwindo_axe":        {"base": 5, "value": 300},  # was 4 -> 5
}


def main() -> None:
    with WEAPON_JSON.open(encoding="utf-8") as f:
        weapons = json.load(f)
    for key, plan in BUMPS.items():
        item = weapons[key]
        item["baseDamage"] = plan["base"]
        item["base_damage"] = plan["base"]
        item["value"] = plan["value"]
        item["_curve_note"] = (
            f"Pass 4: bumped base damage to {plan['base']} to match band "
            f"effective ratio (~2.0x of curve at low floor scales)."
        )
        print(f"Bumped {key} -> base={plan['base']}")
    with WEAPON_JSON.open("w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Wrote {WEAPON_JSON}")


if __name__ == "__main__":
    main()
