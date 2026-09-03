"""v2.6.5.1 SP-supply tune (2026-09-03).

Bumps SP values on food items + cook outcomes so an average-play-loop
floor (drain ~100-200 SP) is comfortably covered by finding food +
cooking once. Removes the "constant race to eat" feel Brandon flagged
without touching drain rate or removing starvation damage.

Preserves relative ordering (weak food < mid food < premium; T1 cook <
T2 < T5). Trophy outcomes untouched. HP/buff/perm fields untouched.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOD_PATH = os.path.join(ROOT, "data", "items", "food.json")
OUTCOMES_PATH = os.path.join(ROOT, "data", "items", "cook_outcomes.json")


def bump_food():
    with open(FOOD_PATH, encoding="utf-8") as f:
        d = json.load(f)
    for k, v in d.items():
        sp = int(v.get("sp_restore", v.get("sp", 0)) or 0)
        # Nudge everything up ~50% on average, with a floor of 15 so even
        # the tiny items feel like a bite. Doesn't touch items that are
        # already very high (ambrosia, void ration).
        if sp <= 10:
            new_sp = 20
        elif sp <= 25:
            new_sp = sp + 20     # bread 25 -> 45
        elif sp <= 50:
            new_sp = sp + 25     # ration 45 -> 70
        elif sp <= 75:
            new_sp = sp + 20     # deep_fungi 70 -> 90
        elif sp <= 100:
            new_sp = sp + 15     # ambrosia 100 -> 115
        else:
            new_sp = sp
        # Preserve whichever key was in use.
        if "sp_restore" in v:
            v["sp_restore"] = new_sp
        else:
            v["sp"] = new_sp
    with open(FOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=True, indent=1)
    print(f"food.json: bumped SP on {len(d)} items")


def bump_outcomes():
    with open(OUTCOMES_PATH, encoding="utf-8") as f:
        blob = json.load(f)
    outcomes = blob["outcomes"]
    # Tier-based bumps: early cooks are worth more; T5 stays near-full-tank
    # (player max_sp = ~210, so a T5 cook alone almost tops the meter).
    TIER_BUMP = {1: 25, 2: 25, 3: 20, 4: 15, 5: 10}
    changed = 0
    for k, v in outcomes.items():
        if k.startswith("_"): continue
        if k.startswith("trophy_"): continue  # trophies untouched
        tier = int(v.get("tier", 1))
        bump = TIER_BUMP.get(tier, 0)
        if bump and "sp" in v and v["sp"] > 0:
            v["sp"] = int(v["sp"]) + bump
            changed += 1
    with open(OUTCOMES_PATH, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=True, indent=1)
    print(f"cook_outcomes.json: bumped SP on {changed} outcomes (T1..T5, non-trophy)")


def report():
    with open(OUTCOMES_PATH, encoding="utf-8") as f:
        outcomes = {k: v for k, v in json.load(f)["outcomes"].items()
                    if not k.startswith("_") and not k.startswith("trophy_")}
    from collections import defaultdict
    by_tier = defaultdict(list)
    for v in outcomes.values():
        by_tier[v.get("tier")].append(v.get("sp", 0))
    print()
    print("new cook SP distribution:")
    for t in sorted(by_tier):
        xs = by_tier[t]
        print(f"  T{t}: min={min(xs)}, max={max(xs)}, avg={sum(xs)//len(xs)}, n={len(xs)}")

    with open(FOOD_PATH, encoding="utf-8") as f:
        food = json.load(f)
    sps = sorted(int(v.get("sp_restore", v.get("sp", 0))) for v in food.values())
    print()
    print(f"new food SP range: {sps[0]}..{sps[-1]}  (avg {sum(sps)//len(sps)}, n={len(sps)})")


if __name__ == "__main__":
    bump_food()
    bump_outcomes()
    report()
