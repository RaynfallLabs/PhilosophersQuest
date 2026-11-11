"""Write how every monster attack lands into data/monsters.json (bug bash
3.3.2; docs/design/ARMOR_REDESIGN_PLAN.md section 7).

`delivery` is one of: blow, bite, sting, trample, grapple, touch, voice,
gaze, breath, ranged. The minor armour slots guard against deliveries
(src/guards.py): the helm voice and gaze, the gloves touch and grapple, the
bracers ranged, the legs bites and stings, the boots trample, the cloak
breath. Read from the attack's name, its `ranged` flag and its damage type,
the same rules tools/balance/armor_model.py priced the guards with. An
attack that already has a `delivery` keeps it (a hand-set one wins).

    python tools/content/tag_attack_delivery.py            # report
    python tools/content/tag_attack_delivery.py --write    # write
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from guards import DELIVERIES, classify  # noqa: E402  (one set of rules, in the game)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    path = os.path.join(ROOT, 'data', 'monsters.json')
    with open(path, encoding='utf-8') as f:
        mons = json.load(f)
    counts = collections.Counter()
    changed = 0
    for m in mons.values():
        for atk in m.get('attacks') or []:
            if atk.get('delivery') in DELIVERIES:
                counts[atk['delivery']] += 1
                continue
            atk['delivery'] = classify(atk)
            counts[atk['delivery']] += 1
            changed += 1
    total = sum(counts.values())
    for d, n in counts.most_common():
        print(f"{d:8} {n:5}  ({100 * n / total:4.1f}%)")
    print(f"{changed} attacks tagged" + (' (written)' if a.write else ' (dry run)'))
    if a.write:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(mons, f, indent=2, ensure_ascii=False)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
