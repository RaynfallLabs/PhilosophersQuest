"""
The common weapons' damage curve, baked into the material files.

Offline tooling.  Usage:

    python tools/balance/weapon_curve.py            # the table: today's numbers and the curve's
    python tools/balance/weapon_curve.py --write    # write weapon_base and min_level into
                                                    # data/materials/weapons/*.json

Why (WEAPON_TIER_AUDIT_2026_11_12.md, Brandon: "even a tier 2 weapon seems to be WAAAY
above where the initial base weapons are... smooth progression, monsters and gear"):

  * A weapon's base came from an old monster curve (4 x 1.10 a floor to floor 20, then
    1.025 a floor) times a flat step per tier (x1.9, x3.1, x3.5, x4.9). The monsters grow
    about 4.3% a floor past floor 20, so inside every tier the weapons fell behind (the
    balance child's typical weapon went from 1.2 attacks a monster to nearly 5) and every
    new tier snapped them ahead.
  * A material dropped 4 to 12 floors before the peak floor its damage was sized for, so
    the best find was 2-3 times the typical one (steel, sized for floor 18, from floor 8).

The curve: every material is sized at its OWN peak floor (LORE, NOT FLOOR: its power is
fixed by where its lore puts it, never by the floor it is found on) so that a longsword of
it kills the median ordinary monster of that floor (the game's own spawn pools, smoothed
over a few floors: monster_curve) in target_attacks(peak) chains for the balance child
(1.4 on floor 1, 1.6 by floor 20, rising smoothly to 3.5 by floor 60: deep fights stay
about as long as the difficulty pass tuned them, without the sawtooth), at that floor's clock and the material's maths tier. Its
damage_mult keeps its place among its tier-mates. It is found no earlier than LEAD
floors before its peak. The tier step is inside the number now: a harder tier's shorter
chain is paid for by the child's own chain at that tier.

The child's seconds per answer above tier 1 are GUESSES (yardsticks.py). When real
answer times from the kids are in hand, put them in CHILD_SECONDS and run --write again.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

MAT_DIR = ROOT / "data" / "materials" / "weapons"

# Chains of an on-peak longsword to kill the floor's median monster, by peak floor
# (straight lines between these; flat past the last). Before the curve the child's deep
# fights averaged about 4 chains, and the difficulty pass was tuned on them.
TARGET_ATTACKS = {1: 1.4, 20: 1.6, 60: 3.5, 100: 3.5}
SMOOTH = 5                  # the monster curve is smoothed over this many floors either side
LEAD = 6                    # found no earlier than this many floors before its peak
REFERENCE = "longsword"     # weapon_base is a longsword's base; other templates scale from it
CHILD_ACC = {1: 0.95, 2: 0.90, 3: 0.85, 4: 0.85, 5: 0.85}
# Tier 1: recorded (1.61 s over 532 answers, 2026-11-12). Tiers 2-5: the working guesses.
CHILD_SECONDS = {1: 1.61, 2: 2.6, 3: 4.5, 4: 6.0, 5: 7.0}
EXPONENT = 1.15             # every common template's chain exponent
TRIALS = 20000


def target_attacks(floor: int) -> float:
    ks = sorted(TARGET_ATTACKS)
    f = max(ks[0], min(ks[-1], int(floor)))
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            return TARGET_ATTACKS[a] + (TARGET_ATTACKS[b] - TARGET_ATTACKS[a]) * (f - a) / (b - a)
    return TARGET_ATTACKS[ks[-1]]


def _avg_hp(hp) -> float:
    s = str(hp).replace(" ", "")
    m = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", s)
    if m:
        return int(m.group(1) or 1) * (int(m.group(2)) + 1) / 2 + int(m.group(3) or 0)
    try:
        return float(s)
    except ValueError:
        return 0.0


_CURVE: dict | None = None


def monster_curve() -> dict:
    """{floor: median HP of the floor's ordinary monsters, as they spawn}, from the
    game's own spawn pools (dungeon._build_spawn_pool), smoothed in log space over
    SMOOTH floors either side so a lump in the pool does not become a lump in a weapon."""
    global _CURVE
    if _CURVE is not None:
        return _CURVE
    import bones
    bones.load_bones = lambda *a, **k: None
    import dungeon
    raw = {}
    for f in range(1, 101):
        rows = []
        for _mid, m in dungeon._build_spawn_pool(f).items():
            if m.get("is_boss") or m.get("is_mini_boss") or m.get("is_seal_demon"):
                continue
            rows.append((_avg_hp(m.get("hp")), float(m["_spawn_freq"])))
        rows.sort()
        tot, acc = sum(w for _, w in rows), 0.0
        med = rows[-1][0]
        for v, w in rows:
            acc += w
            if acc >= tot / 2:
                med = v
                break
        raw[f] = math.log(max(1.0, med))
    _CURVE = {}
    for f in range(1, 101):
        lo, hi = max(1, f - SMOOTH), min(100, f + SMOOTH)
        _CURVE[f] = math.exp(statistics.mean(raw[g] for g in range(lo, hi + 1)))
    return _CURVE


def clock(floor: int) -> int:
    from player import Player
    return 10 + int(floor) // Player.DEPTH_WIS_EVERY


def child_mult(tier: int, floor: int) -> float:
    """Mean of chain^EXPONENT for one attack by the balance child (deterministic)."""
    rng = random.Random(tier * 100003 + floor)
    acc, sec, limit = CHILD_ACC[tier], CHILD_SECONDS[tier], clock(floor)
    tot = 0.0
    for _ in range(TRIALS):
        t, c = 0.0, 0
        while True:
            dt = rng.lognormvariate(math.log(sec), 0.3)
            if t + dt > limit:
                break
            t += dt
            if rng.random() < acc:
                c += 1
            else:
                break
        tot += c ** EXPONENT
    return tot / TRIALS


def materials() -> dict:
    out = {}
    for f in sorted(MAT_DIR.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            m = json.load(fh)
        out[m["id"]] = (f, m)
    return out


def _mean_damage_mult() -> dict:
    import items
    by_tier = {}
    for _f, m in materials().values():
        by_tier.setdefault(items.material_tier(m), []).append(float(m.get("damage_mult", 1.0)))
    return {t: statistics.mean(v) for t, v in by_tier.items()}


def material_curve(mid: str, mean_dm: dict | None = None) -> tuple:
    """(weapon_base, min_level) for one material by the rule above."""
    import items
    m = materials()[mid][1]
    mean_dm = mean_dm or _mean_damage_mult()
    t = items.material_tier(m)
    pf = int(m.get("peak_floor", 1))
    base = monster_curve()[min(100, max(1, pf))] / (target_attacks(pf) * child_mult(t, pf))
    base *= float(m.get("damage_mult", 1.0)) / mean_dm[t]
    first = max(1, int(m.get("min_level", 1)), pf - LEAD)
    return round(base, 1), first


def curve() -> dict:
    """{material id: (weapon_base, min_level)} by the rule above."""
    mean_dm = _mean_damage_mult()
    return {mid: material_curve(mid, mean_dm) for mid in materials()}


def write(table: dict) -> int:
    """Put weapon_base after damage_mult and set min_level, keeping each file's layout."""
    n = 0
    for mid, (f, _m) in materials().items():
        wb, first = table[mid]
        s = f.read_text(encoding="utf-8")
        new = re.sub(r'\n(\s*)"weapon_base": [0-9.]+,', "", s)
        new = re.sub(r'(\n(\s*)"damage_mult": [0-9.]+,)', lambda mm: f'{mm.group(1)}\n{mm.group(2)}"weapon_base": {wb},', new, count=1)
        new = re.sub(r'"min_level": \d+', f'"min_level": {first}', new, count=1)
        if '"weapon_base"' not in new or '"min_level"' not in new:
            raise SystemExit(f"{f.name}: could not place weapon_base / min_level")
        if new != s:
            f.write_text(new, encoding="utf-8", newline="")
            n += 1
    return n


def main(argv=None) -> int:
    import items
    argv = sys.argv[1:] if argv is None else argv
    table = curve()
    print(f"{'material':17} tier peak first(old->new)  longsword base (old -> curve)")
    for mid, (_f, m) in sorted(materials().items(), key=lambda kv: (items.material_tier(kv[1][1]), kv[1][1].get("peak_floor", 0))):
        try:
            old = items.instantiate_weapon(REFERENCE, mid).base_damage
        except ValueError:
            old = "-"
        wb, first = table[mid]
        print(f"{mid:17} {items.material_tier(m):4} {m.get('peak_floor'):4} {m.get('min_level'):5} -> {first:3}   {old!s:>5} -> {round(wb)}")
    if "--write" in argv:
        print(f"wrote {write(table)} material files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
