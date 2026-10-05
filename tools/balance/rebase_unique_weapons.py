"""
Bring named unique weapons up to the damage of the floor they belong to.

Offline tooling.  Usage:

    python tools/balance/rebase_unique_weapons.py            # report only
    python tools/balance/rebase_unique_weapons.py --write    # rewrite weapon.json

Why this exists
---------------
Common weapons are composed at runtime (template x material) and their base
damage climbs with the material's floor: median 4 on floor 1, 11 on floor 20,
38 on floor 60, 85 on floor 90.  The 96 named uniques carry a hand-set
`baseDamage` that stopped climbing long ago (Excalibur 16, Mjolnir 32, the
Sword of Michael 18).  Both kinds use the same chain formula, so the numbers
compare directly: past floor 20 a legendary weapon did a half to a FIFTH of
the damage of an ordinary one found on the same floor.  Reforged Gram, the
Sword of Michael and every mini-boss weapon drop were worthless as rewards.

The rule: a unique's base damage is at least UNIQUE_MULT times the median
base damage of common weapons OF ITS OWN CLASS on its floor (so a dagger is
compared with daggers and a warhammer with warhammers).  It is never lowered.
Chain shape, specials and everything else are untouched.

A unique's floor is its `peak_floor`.  Scripted uniques (quest and boss
rewards with no spawn floor) take the floor of the monster that drops them,
or an entry in SCRIPTED_FLOOR.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "content"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

WEAPON_JSON = ROOT / "data" / "items" / "weapon.json"
MONSTERS_JSON = ROOT / "data" / "monsters.json"

UNIQUE_MULT = 1.25
# Quest payoffs earned by a whole chain: a little more.
QUEST_MULT = 1.5
QUEST_REWARDS = ("gram", "sword_of_michael")

# Floors for scripted uniques that no monster drops.
SCRIPTED_FLOOR = {
    "gram": 60,                 # reforged for the Fafnir fight
    "sword_of_michael": 100,    # granted on floor 99 for Abaddon
    "oathkeeper_sword": 25,     # Grieving Father, floors 21-29
    "penitents_blade": 75,      # The Penitent, floors 71-79
    "caliburn": 32,
}
# Tools and broken things are not weapons to be tuned.
SKIP = ("broken_gram", "sigurds_shovel", "punch_in_the_face")

SAMPLES = 1500
SEED = 20261004


def _common_bases(floor: int) -> dict[str, list[int]]:
    """{weapon_class: [base damage, ...]} for common weapons rolled on `floor`."""
    from items import pick_random_weapon_for_floor
    rng = random.Random(SEED + floor)
    out: dict[str, list[int]] = {}
    for _ in range(SAMPLES):
        w = pick_random_weapon_for_floor(floor, rng)
        if w is not None:
            out.setdefault(w.weapon_class, []).append(w.base_damage)
    return out


_cache: dict[int, dict[str, list[int]]] = {}


def class_median(floor: int, weapon_class: str) -> float:
    floor = max(1, min(100, int(floor)))
    if floor not in _cache:
        _cache[floor] = _common_bases(floor)
    by_class = _cache[floor]
    own = by_class.get(weapon_class) or []
    if len(own) >= 12:
        return statistics.median(own)
    everything = [b for bs in by_class.values() for b in bs]
    return statistics.median(everything)


def drop_floors() -> dict[str, int]:
    """{item_id: floor} from the monsters that drop each unique."""
    monsters = json.loads(MONSTERS_JSON.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for d in monsters.values():
        uid = (d.get("treasure") or {}).get("unique_drop_id")
        floor = d.get("peak_floor") or d.get("min_level") or 0
        if uid and 1 <= floor <= 100:
            out[uid] = max(out.get(uid, 0), int(floor))
    return out


def floor_of(item_id: str, defn: dict, drops: dict[str, int]) -> int | None:
    if item_id in SCRIPTED_FLOOR:
        return SCRIPTED_FLOOR[item_id]
    if item_id in drops:
        return drops[item_id]
    pf = defn.get("peak_floor") or 0
    return int(pf) if pf and pf > 0 else None


def base_of(defn: dict) -> int:
    return int(defn.get("base_damage", defn.get("baseDamage", 0)) or 0)


def plan(weapons: dict) -> list[tuple[str, int, int, int, float]]:
    """[(id, floor, old_base, new_base, class_median)] for uniques that rise."""
    drops = drop_floors()
    changes = []
    for wid, d in weapons.items():
        if wid in SKIP or not isinstance(d, dict) or "class" not in d:
            continue
        floor = floor_of(wid, d, drops)
        if floor is None:
            continue
        med = class_median(floor, d.get("weapon_class", d["class"]))
        mult = QUEST_MULT if wid in QUEST_REWARDS else UNIQUE_MULT
        want = int(round(mult * med))
        old = base_of(d)
        if old < want:
            changes.append((wid, floor, old, want, med))
    return changes


def unplaced(weapons: dict) -> list[str]:
    drops = drop_floors()
    return [wid for wid, d in weapons.items()
            if isinstance(d, dict) and "class" in d and wid not in SKIP
            and floor_of(wid, d, drops) is None]


def main(argv: list[str]) -> int:
    import jsonfmt
    weapons, fmt = jsonfmt.load(WEAPON_JSON)
    changes = plan(weapons)
    print(f"{len(changes)} of {len(weapons)} unique weapons are under "
          f"{UNIQUE_MULT}x their class's common median")
    for wid, floor, old, new, med in sorted(changes, key=lambda c: c[1]):
        print(f"  F{floor:3}  {wid:30} base {old:3} -> {new:3}   (class median {med:5.1f})")
    left = unplaced(weapons)
    if left:
        print("no floor known (left alone):", left)
    if "--write" in argv:
        for wid, _floor, _old, new, _med in changes:
            d = weapons[wid]
            for key in ("baseDamage", "base_damage"):
                if key in d:
                    d[key] = new
            if "baseDamage" not in d and "base_damage" not in d:
                d["baseDamage"] = new
        jsonfmt.save(WEAPON_JSON, weapons, fmt)
        print(f"wrote {WEAPON_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
