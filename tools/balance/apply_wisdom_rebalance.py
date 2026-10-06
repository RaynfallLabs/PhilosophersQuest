"""
One-off: re-size ordinary monsters for wisdom-from-depth and tiered weapons.

Offline tooling (not loaded at runtime).  ALREADY APPLIED to data/monsters.json
and to the anchors in src/floor_curve.py and tools/balance/respawn_by_hp.py.
Kept as the record.  NOT idempotent (it multiplies): refuses to run without
--i-know.  It follows apply_difficulty_schedule.py and supersedes its tuning.

What changed underneath the monsters (2026-10-05, the owner's direction)
---------------------------------------------------------------------
* A weapon asks the math tier of its MATERIAL, and each tier starts with a
  step in base damage (items.TIER_DAMAGE_STEP: x1.9, x3.1, x3.5, x4.9 for
  tiers 2-5), so that moving up a tier is worth the harder sums.  Deep weapons
  therefore hit several times harder than they did.
* The player gains 1 wisdom for every 3 floors of new depth, and the combat
  clock is wisdom in seconds: 16 s on floor 20, 23 on 40, 30 on 60, 43 on 100.
* The balance basis is a child who is GOOD at simple sums: 95% right at tier
  1, 90% at tier 2, 85% below (difficulty_sim.KID_ACC), who cooks, wears what
  drops and has done the boss quests.  Low floors are meant to be passed
  fairly easily; the dungeon tightens with depth.

Measured before this script (kid model, 100 runs): 84% of deep monsters died
to one attack, every gate boss fell in two or three, and nobody died after
floor 20.  The schedules below are the ones the simulator settled on:

    HP      x2 at floor 1, x3 at 20, x5 at 40, x7 at 60, x8 at 80, x9 at 100
    damage  x0.5 at floor 1 (undoing most of the earlier early-floor raise),
            x0.7 at 20, x1.05 at 40, x1.35 at 60, x1.4 from 80

Named foes are not scaled here.  respawn_by_hp.py sizes them against the new
anchors (GATE_BOSS_HP, NAMED_FOE_HP_MULT...).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
MONSTERS_PATH = ROOT / "data" / "monsters.json"

HP_MULT = {1: 2.0, 20: 3.0, 40: 5.0, 60: 7.0, 80: 8.0, 100: 9.0}
DMG_MULT = {1: 0.5, 20: 0.7, 40: 1.05, 60: 1.35, 80: 1.4, 100: 1.4}

# The anchors as they stood before this script.
OLD_HP_ANCHORS = {1: 11, 10: 32, 20: 77, 30: 126, 40: 200, 50: 276, 60: 400,
                  70: 562, 80: 770, 90: 910, 100: 960}
OLD_DMG_ANCHORS = {1: 4.8, 10: 8.1, 20: 9.46, 30: 9.62, 40: 11.38, 50: 15.31,
                   60: 18.11, 70: 19.0, 80: 19.5, 90: 19.99, 100: 20.48}


def _lin(table: dict, floor: float) -> float:
    ks = sorted(table)
    floor = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= floor <= b:
            return table[a] + (table[b] - table[a]) * (floor - a) / (b - a)
    return table[ks[-1]]


def new_anchors() -> tuple[dict, dict]:
    hp = {f: int(round(v * _lin(HP_MULT, f))) for f, v in OLD_HP_ANCHORS.items()}
    dmg = {f: round(v * _lin(DMG_MULT, f), 2) for f, v in OLD_DMG_ANCHORS.items()}
    return hp, dmg


def main() -> int:
    hp_a, dmg_a = new_anchors()
    print("HP_ANCHORS  =", hp_a)
    print("DMG_ANCHORS =", dmg_a)
    if "--i-know" not in sys.argv:
        print("\nAlready applied. Not idempotent; pass --i-know to scale again.")
        return 0
    from respawn_by_hp import damage_dice_to, dice_avg, scale_hp_to

    monsters = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    n_hp = n_dmg = 0
    for mid, d in monsters.items():
        if d.get("is_boss") or d.get("is_mini_boss") or d.get("is_seal_demon"):
            continue
        floor = d.get("peak_floor") or d.get("min_level") or 1
        if floor > 100:
            continue
        hm, dm = _lin(HP_MULT, floor), _lin(DMG_MULT, floor)
        old = d.get("hp")
        if old is not None and dice_avg(old) > 0:
            new = scale_hp_to(old, max(1.0, dice_avg(old) * hm))
            if new != old:
                d["hp"] = new
                n_hp += 1
        if abs(dm - 1.0) > 0.02:
            for a in d.get("attacks") or []:
                cur = dice_avg(a.get("damage", 0))
                if cur <= 0:
                    continue
                new = damage_dice_to(a["damage"], max(1.0, cur * dm))
                if dm < 1.0 and dice_avg(new) > cur:
                    new = a["damage"]
                if new != a["damage"]:
                    a["damage"] = new
                    n_dmg += 1
    MONSTERS_PATH.write_text(
        json.dumps(monsters, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(f"scaled hp on {n_hp} monsters, damage on {n_dmg} attacks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
