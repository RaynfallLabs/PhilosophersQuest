"""Rebake every monster's THAC0 to the armour line (bug bash 3.3.2).

docs/design/ARMOR_REDESIGN_PLAN.md section 4: with AC from body armour and
shield only (src/gear.py), a monster's to-hit is written into
data/monsters.json as

    THAC0 = line(peak floor) + 10 + KEEP x (its lore THAC0 - the median lore
            THAC0 of its 10-floor band)

where line(f) is the mean AC a hero wears on floor f, measured here by
running the game's OWN spawn functions (items.pick_random_armor_for_floor,
items.pick_random_shield_for_floor) over a loot census, from the usual
starting kit (leather body, light shield: AC 7). Against that hero a typical
monster then needs a 10 or better: about 55%, on every floor. KEEP keeps
half of each monster's own accuracy against its band (a wolf still bites
straighter than a zombie).

LORE NOT FLOOR: the number is baked into the data here, once; nothing
multiplies by the floor at runtime. The original value is kept as
`thac0_lore` on first write, and every later run starts from it, so the
tool is repeatable.

    python tools/balance/rebake_thac0.py                 # print the line
    python tools/balance/rebake_thac0.py --write         # and rewrite monsters.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

KEEP = 0.5
START_AC = 7            # leather (2) and a light shield (1), the usual starting kit
SPLIT = {'weapon': 0.45, 'armour': 0.45, 'shield': 0.10}    # ruling 6
SHARE_FOUND = 0.90


def measure_line(runs: int, seed: int, census_path: str | None) -> dict:
    """{floor: mean worn AC} from the game's own spawn functions."""
    import items
    from armor_model import load_census, _poisson
    census = load_census(census_path)
    rng = random.Random(seed)
    slots = list(items.ARMOR_SLOTS)
    totals = {f: [] for f in range(1, 101)}
    for _ in range(runs):
        body, shield = 2, 1
        for f in range(1, 101):
            for _i in range(_poisson(rng, census[f][0] * SHARE_FOUND)):
                r = rng.random()
                if r < SPLIT['weapon']:
                    continue
                if r < SPLIT['weapon'] + SPLIT['shield']:
                    s = items.pick_random_shield_for_floor(f, rng)
                    if s is not None:
                        shield = max(shield, s.ac_bonus + s.enchant_bonus)
                    continue
                slot = rng.choice(slots)
                if slot != 'body':
                    continue
                a = items.pick_random_armor_for_floor(f, rng, slot='body')
                if a is not None:
                    body = max(body, a.ac_bonus + a.enchant_bonus)
            totals[f].append(10 - body - shield)
    line, lo = {}, None
    for f in range(1, 101):
        m = statistics.mean(totals[f])
        lo = m if lo is None else min(lo, m)          # monotone: AC only improves
        line[f] = lo
    return line


def rebake(line: dict, write: bool) -> list:
    path = os.path.join(ROOT, 'data', 'monsters.json')
    with open(path, encoding='utf-8') as f:
        mons = json.load(f)
    lore = {k: float(m.get('thac0_lore', m.get('thac0', 20))) for k, m in mons.items()}
    band = {}
    for k, m in mons.items():
        pf = int(m.get('peak_floor') or m.get('min_level') or 1)
        band.setdefault(min(9, (max(1, pf) - 1) // 10), []).append(lore[k])
    med = {b: statistics.median(v) for b, v in band.items()}
    changes = []
    for k, m in mons.items():
        pf = max(1, min(100, int(m.get('peak_floor') or m.get('min_level') or 1)))
        b = min(9, (pf - 1) // 10)
        new = int(round(line[pf] + 10 + KEEP * (lore[k] - med[b])))
        if 'thac0_lore' not in m:
            m['thac0_lore'] = m.get('thac0', 20)
        if m.get('thac0') != new:
            changes.append((k, m.get('thac0'), new))
        m['thac0'] = new
    if write:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(mons, f, indent=2, ensure_ascii=False)
            f.write('\n')
    return changes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--runs', type=int, default=300)
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--census', default=None)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    line = measure_line(a.runs, a.seed, a.census)
    print('floor  mean AC')
    for f in (1, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100):
        print(f'{f:5}  {line[f]:6.2f}')
    ch = rebake(line, a.write)
    print(f"{len(ch)} monsters change THAC0" + (' (written)' if a.write else ' (dry run)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
