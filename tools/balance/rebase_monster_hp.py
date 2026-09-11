"""
Monster HP Rebase (chain combat v2 rollout).

Reads data/monsters.json and rescales each monster's `hp` (and `max_hp` if set)
so that the per-band median matches the CURVE.md anchor targets, while
preserving relative role within each band (bosses stay high, trash stays low).

Boss protection: any monster with `is_boss == True`, `max_hp > 500`, or
`min_level >= 90` is capped at a 2x HP increase, so we do not accidentally
turn Fafnir into a 20,000 HP wall.

Writes:
    data/monsters.json                              (in-place, updated hp/max_hp)
    tools/balance/rebase_monster_hp_report.md       (before/after summary)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import median
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
MONSTERS_PATH = ROOT / "data" / "monsters.json"
REPORT_PATH = ROOT / "tools" / "balance" / "rebase_monster_hp_report.md"

# ---------------------------------------------------------------------------
# CURVE.md anchor medians (from tools/balance/CURVE.md section 4).
# These are the target median HP for a "normal" monster at each anchor floor.
# Ranges are read from the "Monster band: HP a-b" line at each anchor.
# ---------------------------------------------------------------------------
ANCHOR_TARGET_MEDIAN = {
    1:   8,      # HP 4-12
    10:  21,     # HP 12-30
    20:  55,     # HP 30-80
    30:  110,    # HP 60-160
    40:  210,    # HP 120-300
    50:  325,    # HP 200-450
    60:  500,    # HP 300-700
    70:  750,    # HP 500-1000
    80:  1100,   # HP 700-1500
    90:  1400,   # HP 1000-1800
    100: 1600,   # HP 1200-2000 (extrapolated; L100 is boss floor)
}

# Boss HP scaling ceiling: even if the band factor would 4x HP,
# a boss cannot gain more than +100% (2x current).
BOSS_MAX_FACTOR = 2.0

# ---------------------------------------------------------------------------
# HP parsing / rescaling helpers
# ---------------------------------------------------------------------------
_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?\s*$")


def parse_hp(hp: Any) -> tuple[float, tuple[int, int, int] | None]:
    """Return (average_hp, parsed_dice_tuple_or_None).

    parsed_dice_tuple = (num_dice, sides, modifier) if dice string, else None.
    """
    if isinstance(hp, (int, float)):
        return float(hp), None
    if isinstance(hp, str):
        m = _DICE_RE.match(hp)
        if m:
            n = int(m.group(1))
            d = int(m.group(2))
            mod = 0
            if m.group(3):
                mod = int(m.group(4)) * (1 if m.group(3) == "+" else -1)
            avg = n * (d + 1) / 2 + mod
            return avg, (n, d, mod)
    return 0.0, None


def scale_hp(hp: Any, factor: float) -> Any:
    """Scale an HP value by `factor`.

    - Dice strings ("3d6+2") stay dice strings; we scale num_dice and the modifier.
    - Ints stay ints.
    - We keep the die size (dN) unchanged to preserve the variance feel.
    """
    if factor == 1.0:
        return hp

    if isinstance(hp, (int, float)):
        new = max(1, int(round(float(hp) * factor)))
        return new

    if isinstance(hp, str):
        m = _DICE_RE.match(hp)
        if m:
            n = int(m.group(1))
            d = int(m.group(2))
            mod = 0
            if m.group(3):
                mod = int(m.group(4)) * (1 if m.group(3) == "+" else -1)

            # Scale both parts of the dice string.
            new_n = max(1, int(round(n * factor)))
            new_mod = int(round(mod * factor))

            if new_mod > 0:
                return f"{new_n}d{d}+{new_mod}"
            if new_mod < 0:
                return f"{new_n}d{d}{new_mod}"  # e.g. "4d8-2"
            return f"{new_n}d{d}"
        # Unrecognised string, leave alone
        return hp
    return hp


# ---------------------------------------------------------------------------
# Band assignment
# ---------------------------------------------------------------------------
def band_for(min_level: int) -> int:
    """Snap a min_level to its nearest CURVE.md anchor (1,10,20,...,100)."""
    if min_level < 5:
        return 1
    if min_level < 15:
        return 10
    if min_level < 25:
        return 20
    if min_level < 35:
        return 30
    if min_level < 45:
        return 40
    if min_level < 55:
        return 50
    if min_level < 65:
        return 60
    if min_level < 75:
        return 70
    if min_level < 85:
        return 80
    if min_level < 95:
        return 90
    return 100


def is_boss(mon: dict) -> bool:
    """Boss = is_boss flag OR max_hp>500 OR avg parsed HP>500 OR min_level>=90.

    We include parsed-HP because several canonical bosses (Asterion, Medusa,
    Fafnir, Fenrir) do not set `is_boss` in JSON — they are identified only
    by having enormous dice strings.
    """
    if mon.get("is_boss"):
        return True
    mh = mon.get("max_hp", 0)
    if isinstance(mh, (int, float)) and mh > 500:
        return True
    avg, _ = parse_hp(mon.get("hp", 0))
    if avg > 500:
        return True
    if mon.get("min_level", 0) >= 90:
        return True
    return False


# ---------------------------------------------------------------------------
# Core rebase
# ---------------------------------------------------------------------------
def compute_band_factors(monsters: dict) -> dict[int, dict]:
    """For each band, compute the scaling factor from current median → target median.

    Median is taken over NON-BOSS monsters only, so bosses do not skew it.
    """
    by_band: dict[int, list[tuple[str, dict, float]]] = {}
    for key, mon in monsters.items():
        ml = mon.get("min_level", 1)
        b = band_for(ml)
        avg, _ = parse_hp(mon.get("hp", 0))
        by_band.setdefault(b, []).append((key, mon, avg))

    info: dict[int, dict] = {}
    for b, entries in by_band.items():
        non_boss = [avg for _, mon, avg in entries if not is_boss(mon) and avg > 0]
        if not non_boss:
            # Nothing to compute from; fall back to all entries
            non_boss = [avg for _, _, avg in entries if avg > 0]
        cur_med = median(non_boss) if non_boss else 1.0
        target = ANCHOR_TARGET_MEDIAN.get(b, cur_med)
        factor = target / cur_med if cur_med > 0 else 1.0
        info[b] = {
            "count": len(entries),
            "non_boss_count": len(non_boss),
            "current_median": cur_med,
            "target_median": target,
            "factor": factor,
        }
    return info


def rebase(monsters: dict) -> tuple[dict[int, dict], dict[str, dict]]:
    """Apply the rebase.  Returns (band_info, per_monster_change_log)."""
    band_info = compute_band_factors(monsters)
    changelog: dict[str, dict] = {}

    for key, mon in monsters.items():
        ml = mon.get("min_level", 1)
        b = band_for(ml)
        factor = band_info[b]["factor"]

        # Boss cap: never gain more than 2x HP.
        if is_boss(mon) and factor > BOSS_MAX_FACTOR:
            factor = BOSS_MAX_FACTOR

        old_hp = mon.get("hp", 0)
        old_avg, _ = parse_hp(old_hp)
        new_hp = scale_hp(old_hp, factor)
        new_avg, _ = parse_hp(new_hp)

        old_max = mon.get("max_hp")
        new_max = old_max
        if isinstance(old_max, (int, float)) and old_max > 0:
            new_max = int(round(old_max * factor))

        # Only write if the value actually changed (avoids diff noise).
        if new_hp != old_hp:
            mon["hp"] = new_hp
        if new_max != old_max and new_max is not None:
            mon["max_hp"] = new_max

        changelog[key] = {
            "band": b,
            "min_level": ml,
            "is_boss": is_boss(mon),
            "factor": factor,
            "old_hp": old_hp,
            "new_hp": mon.get("hp"),
            "old_avg": round(old_avg, 1),
            "new_avg": round(new_avg, 1),
        }

    return band_info, changelog


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
SPOT_CHECK_KEYS = [
    "giant_rat",
    "goblin",
    "kobold",
    "grid_bug",
    "ogre",
    "asterion_minotaur",
    "medusa",
    "medusa_gorgon",
    "fafnir_dragon",
    "fenrir_wolf",
    "fenrir_pup",
    "abaddon_destroyer",
    "seal_demon_wrath",
    "iron_patriarch",
    "whispering_crone",
    "blood_archon",
    "asmodeus",
]


def band_summary_after(monsters: dict) -> dict[int, dict]:
    by_band: dict[int, list[float]] = {}
    for _, mon in monsters.items():
        ml = mon.get("min_level", 1)
        b = band_for(ml)
        avg, _ = parse_hp(mon.get("hp", 0))
        by_band.setdefault(b, []).append(avg)
    out = {}
    for b, hps in by_band.items():
        hps_sorted = sorted(hps)
        out[b] = {
            "count": len(hps),
            "median": median(hps),
            "p75": hps_sorted[int(0.75 * (len(hps_sorted) - 1))] if hps_sorted else 0,
            "max": max(hps) if hps else 0,
        }
    return out


def write_report(band_info, before_medians, after_summary, changelog):
    lines = []
    lines.append("# Monster HP Rebase Report — chain combat v2")
    lines.append("")
    lines.append("Generated by `tools/balance/rebase_monster_hp.py`.")
    lines.append("")
    lines.append("Rebase source: `tools/balance/CURVE.md` section 4 anchor bands.")
    lines.append("Boss protection: `is_boss` OR `max_hp>500` OR `min_level>=90` capped at **2x** current HP.")
    lines.append("")

    # Per-band factor table
    lines.append("## Per-band scaling factor applied")
    lines.append("")
    lines.append("| Band | N | Non-boss N | Current median | Target median | Factor |")
    lines.append("|-----:|--:|-----------:|---------------:|--------------:|-------:|")
    for b in sorted(band_info):
        i = band_info[b]
        lines.append(
            f"| L{b} | {i['count']} | {i['non_boss_count']} | "
            f"{i['current_median']:.1f} | {i['target_median']:.1f} | "
            f"{i['factor']:.2f}x |"
        )
    lines.append("")

    # Before/after medians
    lines.append("## Before / after HP median by band")
    lines.append("")
    lines.append("| Band | N | Before median | After median | After p75 | After max |")
    lines.append("|-----:|--:|--------------:|-------------:|----------:|----------:|")
    for b in sorted(after_summary):
        before = before_medians.get(b, {})
        after = after_summary[b]
        lines.append(
            f"| L{b} | {after['count']} | "
            f"{before.get('median', 0):.1f} | {after['median']:.1f} | "
            f"{after['p75']:.1f} | {after['max']:.1f} |"
        )
    lines.append("")

    # Spot check
    lines.append("## Spot check — named monsters")
    lines.append("")
    lines.append("| Monster | min_level | boss? | factor | HP before → after | avg before → after |")
    lines.append("|:--------|----------:|:-----:|-------:|:------------------|:-------------------|")
    for key in SPOT_CHECK_KEYS:
        entry = changelog.get(key)
        if entry is None:
            continue
        lines.append(
            f"| `{key}` | {entry['min_level']} | "
            f"{'Y' if entry['is_boss'] else 'n'} | {entry['factor']:.2f}x | "
            f"`{entry['old_hp']}` → `{entry['new_hp']}` | "
            f"{entry['old_avg']} → {entry['new_avg']} |"
        )
    lines.append("")

    # Bosses (all of them)
    lines.append("## All bosses — capped at 2x")
    lines.append("")
    lines.append("| Monster | min_level | factor | HP before → after | avg before → after |")
    lines.append("|:--------|----------:|-------:|:------------------|:-------------------|")
    boss_entries = [
        (k, v) for k, v in changelog.items() if v["is_boss"]
    ]
    boss_entries.sort(key=lambda kv: kv[1]["min_level"])
    for key, entry in boss_entries:
        lines.append(
            f"| `{key}` | {entry['min_level']} | {entry['factor']:.2f}x | "
            f"`{entry['old_hp']}` → `{entry['new_hp']}` | "
            f"{entry['old_avg']} → {entry['new_avg']} |"
        )
    lines.append("")

    # Refusals
    refusals = [
        (k, v) for k, v in changelog.items()
        if v["is_boss"] and v["factor"] < 1.0
    ]
    if refusals:
        lines.append("## Notes")
        lines.append("")
        for key, entry in refusals:
            lines.append(
                f"- `{key}`: band factor would have SHRUNK this boss "
                f"({entry['factor']:.2f}x); boss cap did not apply because the "
                f"boss cap only limits *increases*."
            )
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    with MONSTERS_PATH.open(encoding="utf-8") as f:
        monsters = json.load(f)

    # Snapshot before medians / bosses
    before_medians = band_summary_after(monsters)  # same shape

    band_info, changelog = rebase(monsters)

    # Preserve original file style: CRLF line endings, ensure_ascii=True
    # (\uXXXX escapes), and NO trailing newline.  This keeps the diff limited
    # to hp/max_hp fields only.
    text = json.dumps(monsters, indent=2, ensure_ascii=True)
    text = text.replace("\n", "\r\n")
    MONSTERS_PATH.write_bytes(text.encode("utf-8"))

    after_summary = band_summary_after(monsters)
    write_report(band_info, before_medians, after_summary, changelog)

    print(f"[OK] Rebased {len(monsters)} monsters.")
    print(f"[OK] Wrote {MONSTERS_PATH}")
    print(f"[OK] Wrote report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
