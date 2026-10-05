"""
One-off: re-scale ordinary monster HP and damage by depth (2026-10 balance pass).

Offline tooling (not loaded at runtime).  ALREADY APPLIED to data/monsters.json;
it is kept as the record of what was done and why.  It is NOT idempotent: it
multiplies, so running it again would scale everything twice.  It refuses to
run unless given --i-know.

Why
---
`tools/balance/difficulty_sim.py` played 100-floor runs for a prepared player
who answers 85 percent of questions correctly.  After combat was made to ask
its questions again (weapons ask the math tier of their depth band, and a
cleared tier moves the fight up a tier instead of answering for the player)
and hit points were put back on the cooking curve, the simulator measured:

    floors 1-19    0.1 percent death per floor, 79 percent of kills one attack
    floors 21-59   0.4 to 1.6 percent
    floors 81-99   40 percent, 3.6 attacks per kill at math tier 5

So the top of the dungeon was a stroll and the bottom a wall.  Both are the
anchors' doing: the early anchors were written for a chain-3 player with a
starting weapon, and the deep HP anchors for a chain-5 hit, which nobody
lands on tier-5 sums against a ten-second clock.

The schedules below move the anchors (and every ordinary monster with them):

    HP      x1.4 to x1.5 through floor 20, x1.0 near floor 37, x0.6 at 100
    damage  x2.4 at floor 1, x1.3 at floor 40, x0.94 at 70 and x0.6 at 100
            (about 18 to 20 a hit from floor 60 down, where it used to
            climb from 16 to 35)

Named foes (gate bosses, seal demons, mini-bosses) are NOT scaled here; their
HP and damage are set against the new anchors by respawn_by_hp.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
MONSTERS_PATH = ROOT / "data" / "monsters.json"

HP_MULT = {1: 1.4, 10: 1.5, 20: 1.4, 30: 1.15, 40: 0.95, 50: 0.85, 60: 0.8,
           70: 0.75, 80: 0.7, 90: 0.65, 100: 0.6}
DMG_MULT = {1: 2.4, 10: 2.16, 20: 1.8, 30: 1.54, 40: 1.3, 50: 1.25, 60: 1.15,
            70: 0.94, 80: 0.79, 90: 0.66, 100: 0.59}
# (Final figures after three simulator rounds; the first cut was 2.0 / 1.8 /
# 1.5 / 1.4 / 1.3 / 1.25 / 1.15 / 1.1 / 1.0 / 0.9 / 0.85.)

# The anchors as they stood before this pass (CURVE.md section 4).
OLD_HP_ANCHORS = {1: 8, 10: 21, 20: 55, 30: 110, 40: 210, 50: 325, 60: 500,
                  70: 750, 80: 1100, 90: 1400, 100: 1600}
OLD_DMG_ANCHORS = {1: 2.0, 10: 3.75, 20: 5.25, 30: 6.25, 40: 8.75, 50: 12.25,
                   60: 15.75, 70: 20.25, 80: 24.75, 90: 30.25, 100: 35.0}


def _lin(table: dict, floor: float) -> float:
    ks = sorted(table)
    floor = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= floor <= b:
            return table[a] + (table[b] - table[a]) * (floor - a) / (b - a)
    return table[ks[-1]]


def new_anchors() -> tuple[dict, dict]:
    hp = {f: round(v * HP_MULT[f]) for f, v in OLD_HP_ANCHORS.items()}
    dmg = {f: round(v * DMG_MULT[f], 2) for f, v in OLD_DMG_ANCHORS.items()}
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
        if old is not None and abs(hm - 1.0) > 0.02 and dice_avg(old) > 0:
            new = scale_hp_to(old, max(1.0, dice_avg(old) * hm))
            if new != old:
                d["hp"] = new
                n_hp += 1
        if abs(dm - 1.0) > 0.02:
            for a in d.get("attacks") or []:
                cur = dice_avg(a.get("damage", 0))
                if cur <= 0:
                    continue
                new = damage_dice_to(a["damage"], cur * dm)
                if dm < 1.0 and dice_avg(new) > cur:
                    new = a["damage"]          # never raise on a cut
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
