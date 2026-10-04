"""
Re-seat monster spawn curves on the floor their stats were built for.

Offline tooling (not loaded at runtime).  Usage:

    python tools/balance/respawn_by_hp.py            # dry run: report only
    python tools/balance/respawn_by_hp.py --write    # rewrite data/monsters.json

Why this exists
---------------
`rebase_monster_hp.py` (chain combat v2) scaled every monster's HP so that the
median of each `min_level` band hit the CURVE.md anchor for that floor.  But
monsters do not spawn at `min_level`: `dungeon._build_spawn_pool` weights them
on a bell curve around `peak_floor`, which sat 6 to 12 floors deeper with a
wide spread (9 to 12).  The result was that the monsters actually met on a
floor had roughly the HP intended for a floor 10 to 15 levels shallower, and
on floors 8 to 35 almost everything died to a one- or two-answer chain.

The fix moves the RNG, not the stats: each randomly spawning monster's
`peak_floor` becomes the floor whose anchor HP matches the monster's own HP,
the spread is tightened so weak monsters stop lingering 20 floors too deep,
and `min_level` follows a few floors ahead of the peak.  HP, damage, THAC0
and everything else are left exactly as authored.

Scripted monsters (`peak_weight` 0: bosses, mini-bosses, seal demons, mimics)
are placed by level_manager / boss_levels and their floors are not touched.

A short list of lore-driven stat corrections is applied first (see the
constants below); each group says why.

The script is idempotent: running it again on its own output changes nothing.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MONSTERS_PATH = ROOT / "data" / "monsters.json"

# CURVE.md section 4 anchor medians (same table rebase_monster_hp.py used).
HP_ANCHORS = {1: 8, 10: 21, 20: 55, 30: 110, 40: 210, 50: 325, 60: 500,
              70: 750, 80: 1100, 90: 1400, 100: 1600}
# Midpoints of the CURVE.md "Monster band ... damage" ranges.
DMG_ANCHORS = {1: 2.0, 10: 3.75, 20: 5.25, 30: 6.25, 40: 8.75, 50: 12.25,
               60: 15.75, 70: 20.25, 80: 24.75, 90: 30.25, 100: 35.0}

# ---------------------------------------------------------------------------
# Lore-driven HP corrections (2026-10 content pass).
#
# The spawn move never changes stats.  These few entries are the opposite
# case: the creature's HP contradicted its own lore or its own damage, almost
# always because the v2.14 rebase capped it (bosses, anything with
# min_level >= 90) or because it was authored outside the rebase.
# Values are the new AVERAGE HP; the dice shape is kept.
# ---------------------------------------------------------------------------

# Giants hit like mid-game monsters (3d8+10) but had the HP of a floor-15 to
# floor-24 monster: one-hit glass cannons that could also two-shot an early
# player.  The ladder follows the classic ordering (stone < frost < fire <
# cloud < storm) and sits under the existing frost_giant_jarl and
# fire_giant_king (344) and elder_storm_giant (546).  The four classical
# elementals are made peers of each other.
HP_SET: dict[str, int] = {
    "stone_giant": 160, "frost_giant": 185, "fire_giant": 210,
    "cloud_giant": 250, "storm_giant": 300,
    "air_elemental": 150, "water_elemental": 150,
    # Cath Palug killed nine score warriors on Anglesey; it should outlast a
    # goblin. (Also keeps it on the same floors as the dragons it is cooked
    # with: see test_every_recipe_monster_parts_share_a_floor_band.)
    "cath_palug": 31,
    # Reviewer flags: the master was weaker than its own servant.
    "vampire": 146,          # vampire_spawn is 122
    "werewolf_alpha": 40,    # werewolf is 31
    # A stitched golem and a swollen battering-ram corpse had the HP of a rat.
    "flesh_golem": 31, "zombie_hulk": 23,
}

# Deep-dungeon monsters whose HP was left far under the band for the depth
# their lore, damage and authored floor all place them at.  Brought to
# DEEP_UNDER_FRACTION of the anchor HP at the floor given here (their
# authored min_level before this pass).
DEEP_UNDER_HP: dict[str, int] = {
    "void_seraph": 90, "apocalypse_herald": 91, "wormwood_blight": 92,
    "iron_horseman": 94, "astral_horror": 76, "veiled_inquisitor": 64,
    "shadow_archer": 63, "crypt_summoner": 62, "frostfang_giant": 62,
    # depth-keyed mimic tiers (dungeon.py picks these by floor band)
    "lurking_horror": 45, "gilded_mimic": 60,
}
DEEP_UNDER_FRACTION = 0.9

# Named mini-bosses and seal demons must not be weaker than the ordinary
# monsters around them.  Raised (never lowered) to this multiple of the anchor
# HP at their floor.  The gate bosses already sit near 3x and are left alone,
# except Fenrir, whom the rebase capped at 1.3x.
NAMED_FOE_HP_MULT = 2.0
HP_FLOOR_MULT: dict[str, float] = {"fenrir_wolf": 2.2}

ATTACK_DAMAGE_SET: dict[str, dict[int, str]] = {
    # a morningstar that hit for 2d4+1 on a creature this size
    "cloud_giant": {0: "3d8+8"},
    # The breath, not a claw, is the big attack of a young red dragon, and a
    # young dragon must not out-hit the adult (whose best attack is 2d8+3).
    "young_red_dragon": {0: "1d8+2", 1: "2d6+3"},
}

# Scripted legends keep their own floors, but may be met a little earlier
# than before so their trophies overlap the monsters they are cooked with.
MIN_LEVEL_SET: dict[str, int] = {"surtur": 80}

# Named, one-of-a-kind foes leave the random pool entirely (peak_weight 0).
# level_manager places each at most once per run instead.  Before this a
# floor in the 80s could roll several Tiamats.
SCRIPTED_UNIQUES = (
    "iron_patriarch", "whispering_crone", "blood_archon",
    "tiamat", "asmodeus", "surtur", "ymir_last_spawn", "hrungnirs_ghost",
)

# A monster whose hardest attack is more than SPIKE_MULT times the floor's
# anchor damage is pushed deeper (at most MAX_PUSH floors) until it is not.
SPIKE_MULT = 3.5
MAX_PUSH = 8

_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?\s*$")


def dice_avg(d) -> float:
    if isinstance(d, (int, float)):
        return float(d)
    m = _DICE_RE.match(str(d))
    if not m:
        try:
            return float(d)
        except ValueError:
            return 0.0
    n, s = int(m.group(1)), int(m.group(2))
    mod = int(m.group(4)) * (1 if m.group(3) == "+" else -1) if m.group(3) else 0
    return n * (s + 1) / 2 + mod


def _interp(anchors: dict[int, float], floor: float) -> float:
    """Log-linear interpolation through the anchor table."""
    ks = sorted(anchors)
    floor = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= floor <= b:
            t = (floor - a) / (b - a)
            return math.exp(math.log(anchors[a]) * (1 - t) + math.log(anchors[b]) * t)
    return float(anchors[ks[-1]])


def target_hp(floor: float) -> float:
    return _interp(HP_ANCHORS, floor)


def target_dmg(floor: float) -> float:
    return _interp(DMG_ANCHORS, floor)


def fit_floor(hp: float) -> int:
    """The floor whose anchor HP is closest to `hp` (1..99)."""
    best, best_err = 1, float("inf")
    for f in range(1, 100):
        err = abs(math.log(max(hp, 1.0)) - math.log(target_hp(f)))
        if err < best_err:
            best, best_err = f, err
    return best


def spread_for(peak: int) -> int:
    """Bell width.  Sized so one spread is roughly +/-35% of anchor HP: the
    curve climbs ~10% a floor early and ~2% a floor at the bottom."""
    if peak <= 12:
        return 4
    if peak <= 30:
        return 5
    if peak <= 45:
        return 7
    if peak <= 80:
        return 9
    return 12


def lead_for(peak: int) -> int:
    """How many floors before its peak a monster may first appear."""
    if peak <= 12:
        return 2
    if peak <= 30:
        return 3
    if peak <= 45:
        return 4
    if peak <= 80:
        return 5
    return 6


def monster_damage(defn: dict) -> float:
    """Average damage of one attack action (attacks are chosen at random)."""
    ds = [dice_avg(a.get("damage", 0)) for a in defn.get("attacks") or []]
    if not ds:
        return 0.0
    n = int(defn.get("multi_attack_count") or 1)
    if n > 1:
        return sum(sorted(ds, reverse=True)[:n])
    return sum(ds) / len(ds)


def max_attack(defn: dict) -> float:
    return max((dice_avg(a.get("damage", 0)) for a in defn.get("attacks") or []), default=0.0)


def is_random_spawn(defn: dict) -> bool:
    return float(defn.get("peak_weight", 0) or 0) > 0


def scale_hp_to(hp, target_avg: float):
    """Rescale a dice HP string to a new average, keeping the die size."""
    from rebase_monster_hp import scale_hp
    cur = dice_avg(hp)
    if cur <= 0:
        return hp
    return scale_hp(hp, target_avg / cur)


def apply_stat_fixes(monsters: dict) -> list[str]:
    """Apply the lore-driven corrections in place.  Returns a change log."""
    log = []

    def _raise_hp(mid, avg, why):
        d = monsters[mid]
        old = d["hp"]
        # Never lower, and leave alone when already within 3% (idempotence:
        # dice rounding means a rescale rarely lands exactly on the target).
        if dice_avg(old) >= 0.97 * avg:
            return
        new = scale_hp_to(old, avg)
        d["hp"] = new
        log.append(f"{mid}: hp {old} ({dice_avg(old):.0f}) -> {new} ({dice_avg(new):.0f})  [{why}]")

    for mid, avg in HP_SET.items():
        _raise_hp(mid, avg, "lore ladder")
    for mid, floor in DEEP_UNDER_HP.items():
        _raise_hp(mid, DEEP_UNDER_FRACTION * target_hp(floor), "deep monster under its band")
    for mid, d in monsters.items():
        named = d.get("is_mini_boss") or d.get("is_seal_demon") or mid in HP_FLOOR_MULT
        if not named:
            continue
        mult = HP_FLOOR_MULT.get(mid, NAMED_FOE_HP_MULT)
        want = mult * target_hp(d.get("peak_floor", d.get("min_level", 1)))
        _raise_hp(mid, want, f"named foe under {mult}x floor anchor")
    for mid, atks in ATTACK_DAMAGE_SET.items():
        for idx, dmg in atks.items():
            a = monsters[mid]["attacks"][idx]
            if a.get("damage") != dmg:
                log.append(f"{mid}: attack {a.get('name')!r} damage {a.get('damage')} -> {dmg}")
                a["damage"] = dmg
    for mid, ml in MIN_LEVEL_SET.items():
        if monsters[mid].get("min_level") != ml:
            log.append(f"{mid}: min_level {monsters[mid].get('min_level')} -> {ml}")
            monsters[mid]["min_level"] = ml
    for mid in SCRIPTED_UNIQUES:
        d = monsters[mid]
        if float(d.get("peak_weight", 0) or 0) > 0:
            log.append(f"{mid}: peak_weight {d['peak_weight']} -> 0.0 (placed once per run by level_manager)")
            d["peak_weight"] = 0.0
        if not d.get("is_mini_boss"):
            d["is_mini_boss"] = True
            log.append(f"{mid}: is_mini_boss -> True")
    return log


def plan(monsters: dict) -> dict[str, tuple[int, int, int]]:
    """{id: (peak_floor, spread, min_level)} for every randomly spawning monster."""
    out = {}
    for mid, d in monsters.items():
        if not is_random_spawn(d):
            continue
        peak = fit_floor(dice_avg(d["hp"]))
        spike = max_attack(d)
        pushed = 0
        while pushed < MAX_PUSH and peak < 99 and spike > SPIKE_MULT * target_dmg(peak):
            peak += 1
            pushed += 1
        out[mid] = (peak, spread_for(peak), max(1, peak - lead_for(peak)))
    return out


def pool_at(monsters: dict, placement: dict, level: int) -> dict[str, float]:
    """Mirror of dungeon._build_spawn_pool under a proposed placement."""
    pool = {}
    for mid, d in monsters.items():
        if not is_random_spawn(d):
            continue
        peak, spread, min_level = placement.get(
            mid, (d.get("peak_floor", 1), d.get("spread", 10), d.get("min_level", 1)))
        if min_level > level:
            continue
        bell = math.exp(-((level - peak) ** 2) / (2 * max(1, spread) ** 2))
        if bell < 0.005:
            continue
        pool[mid] = max(0.02, float(d["peak_weight"]) * bell)
    return pool


def _wpct(pairs, q):
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs) or 1.0
    c = 0.0
    for x, w in pairs:
        c += w / tot
        if c >= q:
            return x
    return pairs[-1][0] if pairs else 0.0


def floor_stats(monsters: dict, placement: dict, level: int) -> dict:
    pool = pool_at(monsters, placement, level)
    tot = sum(pool.values()) or 1.0
    hp = [(dice_avg(monsters[k]["hp"]), w) for k, w in pool.items()]
    dm = [(monster_damage(monsters[k]), w) for k, w in pool.items()]
    spike = max(pool, key=lambda k: max_attack(monsters[k])) if pool else ""
    return {
        "kinds": len(pool),
        "neff": 1.0 / sum((w / tot) ** 2 for w in pool.values()) if pool else 0.0,
        "hp10": _wpct(hp, .1), "hp50": _wpct(hp, .5), "hp90": _wpct(hp, .9),
        "dmg50": _wpct(dm, .5), "dmg90": _wpct(dm, .9),
        "spike": spike, "spike_dmg": max_attack(monsters[spike]) if spike else 0.0,
        "spike_share": pool.get(spike, 0) / tot,
    }


def report(monsters: dict, placement: dict, label: str) -> None:
    print(f"\n== {label}")
    print("floor  kinds  Neff   HP p10/p50/p90  target  ratio   dmg p50/p90  target  hardest single attack (dmg / target, share)")
    ratios, thin = [], (0, 0, 1e9)
    for lvl in range(1, 101):
        st = floor_stats(monsters, placement, lvl)
        th, td = target_hp(lvl), target_dmg(lvl)
        ratios.append(st["hp50"] / th)
        if st["neff"] < thin[2]:
            thin = (lvl, st["kinds"], st["neff"])
        if lvl <= 12 or lvl % 4 == 0:
            print(f"L{lvl:3}  {st['kinds']:4}  {st['neff']:5.1f}  {st['hp10']:5.0f}/{st['hp50']:5.0f}/{st['hp90']:5.0f}  "
                  f"{th:6.0f}  {st['hp50']/th:4.2f}   {st['dmg50']:4.1f}/{st['dmg90']:5.1f}  {td:5.1f}  "
                  f"{st['spike']} ({st['spike_dmg']:.0f} / {td:.0f}, {st['spike_share']:.3f})")
    print(f"median-HP / target ratio across floors: min {min(ratios):.2f}, max {max(ratios):.2f};"
          f" thinnest floor (floor, kinds, Neff): {thin[0]}, {thin[1]}, {thin[2]:.1f}")


def write(monsters: dict, placement: dict) -> int:
    changed = 0
    for mid, (peak, spread, min_level) in placement.items():
        d = monsters[mid]
        new = {"peak_floor": peak, "spread": spread, "min_level": min_level}
        if any(d.get(k) != v for k, v in new.items()):
            d.update(new)
            changed += 1
    # Byte-compatible with the file's existing formatting.
    with open(MONSTERS_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(monsters, indent=2, ensure_ascii=False) + "\n")
    return changed


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    monsters = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    current = {mid: (d.get("peak_floor", 1), d.get("spread", 10), d.get("min_level", 1))
               for mid, d in monsters.items() if is_random_spawn(d)}
    report(monsters, current, "CURRENT placement")
    print("\n== stat fixes")
    for line in apply_stat_fixes(monsters):
        print("  " + line)
    proposed = plan(monsters)
    report(monsters, proposed, "PROPOSED placement")

    print("\nstill off the floor it lands on (hand-review):")
    for mid, (peak, _s, _m) in sorted(proposed.items(), key=lambda kv: kv[1][0]):
        dmg = monster_damage(monsters[mid])
        td = target_dmg(peak)
        if max_attack(monsters[mid]) > SPIKE_MULT * td or dmg < 0.4 * td:
            print(f"  {mid:30} peak F{peak:3}  hp {dice_avg(monsters[mid]['hp']):7.1f}  "
                  f"avg dmg {dmg:5.1f}  max {max_attack(monsters[mid]):5.1f} (floor target {td:4.1f})")

    if "--write" in argv:
        n = write(monsters, proposed)
        print(f"\nwrote {MONSTERS_PATH} ({n} monsters re-seated)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
