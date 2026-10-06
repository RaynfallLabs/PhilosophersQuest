"""
Scale monster HP and damage by a depth schedule, and move the anchors with them.

Offline tooling (not loaded at runtime).  Every run MULTIPLIES, so it is not
idempotent: it does nothing without --i-know, and each real run is appended to
tools/balance/SCALE_LOG.md so the data's history can be read.

A schedule is the same thing difficulty_sim.py's --knobs take: numbers joined
by ':' and spread evenly from floor 1 to floor 100, e.g. "0.6:0.8:1:1:0.9:0.9".
The intended loop is: find a schedule with the simulator's mon_hp / mon_dmg
knobs, then bake exactly that schedule here, then run respawn_by_hp.py --write.

    python tools/balance/scale_monsters.py --hp 1:1:0.9:0.8 --dmg 0.6:1:1:0.9 \
        --named --keep-dmg abaddon_destroyer --note "why" --i-know

--named        also scale gate bosses, seal demons and mini-bosses (the
               simulator's knobs do), and GATE_BOSS_HP in respawn_by_hp.py
--keep-dmg ID  leave that monster's damage alone (repeatable)
--regen-catch-up   one-time: multiply every monster's flat `regeneration` by
               floor_curve.power_scale(floor), for data written before the
               HP re-sizing
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
MONSTERS_PATH = ROOT / "data" / "monsters.json"
ANCHOR_FILES = (ROOT / "src" / "floor_curve.py", HERE / "respawn_by_hp.py")
LOG_PATH = HERE / "SCALE_LOG.md"


def parse_schedule(text: str) -> tuple:
    return tuple(float(x) for x in str(text).split(":"))


def at(schedule: tuple, floor: float) -> float:
    if len(schedule) == 1:
        return schedule[0]
    pos = (max(1, min(100, floor)) - 1) / 99.0 * (len(schedule) - 1)
    i = min(len(schedule) - 2, int(pos))
    return schedule[i] + (schedule[i + 1] - schedule[i]) * (pos - i)


def _rewrite_anchor(text: str, name: str, values: dict) -> str:
    m = re.search(rf"^{name} = \{{.*?\}}", text, flags=re.S | re.M)
    if not m:
        raise SystemExit(f"{name} not found")
    items = [f"{k}: {v}" for k, v in values.items()]
    half = (len(items) + 1) // 2 + 1
    pad = " " * (len(name) + 4)
    body = "{" + ", ".join(items[:half]) + ",\n" + pad + ", ".join(items[half:]) + "}"
    return text[:m.start()] + f"{name} = " + body + text[m.end():]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hp", default="1")
    ap.add_argument("--dmg", default="1")
    ap.add_argument("--named", action="store_true")
    ap.add_argument("--keep-dmg", action="append", default=[])
    ap.add_argument("--regen-catch-up", action="store_true")
    ap.add_argument("--note", default="")
    ap.add_argument("--i-know", action="store_true")
    args = ap.parse_args()
    hp_s, dmg_s = parse_schedule(args.hp), parse_schedule(args.dmg)

    import floor_curve
    import respawn_by_hp as R

    new_hp = {f: int(round(v * at(hp_s, f))) for f, v in floor_curve.HP_ANCHORS.items()}
    new_dmg = {f: round(v * at(dmg_s, f), 2) for f, v in floor_curve.DMG_ANCHORS.items()}
    print("HP_ANCHORS  ->", new_hp)
    print("DMG_ANCHORS ->", new_dmg)
    for table in (new_hp, new_dmg):
        vals = [table[k] for k in sorted(table)]
        if vals != sorted(vals):
            raise SystemExit("refusing: the anchors would no longer rise with depth")
    if not args.i_know:
        print("\nDry run. Not idempotent; pass --i-know to apply.")
        return 0

    monsters = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    n_hp = n_dmg = n_regen = 0
    for mid, d in monsters.items():
        named = bool(d.get("is_boss") or d.get("is_mini_boss") or d.get("is_seal_demon"))
        floor = d.get("peak_floor") or d.get("min_level") or 1
        if floor > 100:
            continue
        if args.regen_catch_up and float(d.get("regeneration", 0) or 0) > 0:
            d["regeneration"] = int(round(d["regeneration"] * floor_curve.power_scale(floor)))
            n_regen += 1
        if named and not args.named:
            continue
        hm, dm = at(hp_s, floor), at(dmg_s, floor)
        old = d.get("hp")
        if old is not None and abs(hm - 1.0) > 0.005 and R.dice_avg(old) > 0:
            new = R.scale_hp_to(old, max(1.0, R.dice_avg(old) * hm))
            if new != old:
                d["hp"] = new
                n_hp += 1
        if abs(dm - 1.0) > 0.005 and mid not in args.keep_dmg:
            for a in d.get("attacks") or []:
                cur = R.dice_avg(a.get("damage", 0))
                if cur <= 0:
                    continue
                new = R.damage_dice_to(a["damage"], max(1.0, cur * dm))
                if dm < 1.0 and R.dice_avg(new) > cur:
                    new = a["damage"]
                if new != a["damage"]:
                    a["damage"] = new
                    n_dmg += 1
    MONSTERS_PATH.write_text(json.dumps(monsters, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8", newline="\n")

    for path in ANCHOR_FILES:
        raw = path.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        text = raw.replace("\r\n", "\n")
        text = _rewrite_anchor(text, "HP_ANCHORS", new_hp)
        text = _rewrite_anchor(text, "DMG_ANCHORS", new_dmg)
        if args.named and path.name == "respawn_by_hp.py":
            gate = {k: int(round(v * at(hp_s, monsters[k].get("peak_floor", 1)) / 100.0)) * 100
                    for k, v in R.GATE_BOSS_HP.items()}
            m = re.search(r"^GATE_BOSS_HP: dict\[str, int\] = \{.*?\}", text, flags=re.S | re.M)
            items = [f'"{k}": {v}' for k, v in gate.items()]
            body = ("GATE_BOSS_HP: dict[str, int] = {" + ", ".join(items[:2]) + ",\n"
                    + " " * 32 + ", ".join(items[2:4]) + ",\n"
                    + " " * 32 + ", ".join(items[4:]) + "}")
            text = text[:m.start()] + body + text[m.end():]
            print("GATE_BOSS_HP ->", gate)
        path.write_bytes(text.replace("\n", nl).encode("utf-8"))

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = (f"| {stamp} | hp {args.hp} | dmg {args.dmg} | named: {'yes' if args.named else 'no'} "
            f"| keep-dmg: {', '.join(args.keep_dmg) or '-'} | regen catch-up: "
            f"{'yes' if args.regen_catch_up else 'no'} | {n_hp} hp, {n_dmg} attacks, "
            f"{n_regen} regen | {args.note} |\n")
    if not LOG_PATH.exists():
        LOG_PATH.write_text(
            "# Monster scaling log\n\nEvery real run of `scale_monsters.py`. Earlier "
            "one-off passes are recorded in `apply_difficulty_schedule.py` and "
            "`apply_wisdom_rebalance.py`.\n\n"
            "| When | HP schedule | Damage schedule | Named | Kept | Regen | Changed | Why |\n"
            "|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(f"scaled hp on {n_hp} monsters, damage on {n_dmg} attacks, regen on {n_regen}")
    print("now run: python tools/balance/respawn_by_hp.py --write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
