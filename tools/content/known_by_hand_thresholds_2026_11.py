"""Named gear's equip thresholds on the Known by Hand rule (2026-11-13).

Winning-build plan 3.4: each KIND of armour, shield, ring, amulet and belt is
asked for only once a run (src/known_by_hand.py), so the threshold rose:
armour light / medium / heavy 2 / 3 / 4 (were 1 / 2 / 3), a named unique +2
(was +1), at most 7 (was 5); rings / amulets / belts 2 / 3 / 3 (were
1 / 2 / 2), the same unique and cap. The numbers live in
data/gear_rules.json (`threshold`, `accessory_threshold`); common pieces
read them when they are made (gear.equip_threshold / accessory_threshold).

This pass writes the authored `equip_threshold` of the named pieces in
data/items/armor.json, shield.json and accessory.json by the same rule, in
the same way the passes that set them did:

- named armour and shields: the template's weight class and the tier's
  benefit, plus the unique step (tools/content/unique_armor_ladder_2026_11
  `ladder`, whose threshold is gear.equip_threshold(..., unique=True)); a
  trap that goes on with no quiz (threshold 0, the Duck of Doom) stays 0;
- named rings and amulets: gear.accessory_threshold(slot, the tier's lesser
  level, unique=True), as tools/content/ring_kinds_2026_11.py set them;
- the ten ring kinds: their level-1 figure, gear.accessory_threshold(slot, 1).

Hand-set values (the cursed trap rings, Elara's ring, the Ring of Command)
are not on the rule and are left alone. Only `equip_threshold` changes, and
the files keep their formatting (jsonfmt). Idempotent: a second run changes
nothing.

    py tools/content/known_by_hand_thresholds_2026_11.py [--check]
"""
from __future__ import annotations

import argparse
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

import jsonfmt  # noqa: E402

ARMOR = os.path.join(ROOT, 'data', 'items', 'armor.json')
SHIELD = os.path.join(ROOT, 'data', 'items', 'shield.json')
ACCESSORY = os.path.join(ROOT, 'data', 'items', 'accessory.json')


def armour_threshold(e: dict, category: str, key: str):
    """The rule's threshold for a named armour piece or shield (None: not
    a named piece, or a no-quiz trap)."""
    import unique_armor_ladder_2026_11 as ladder_pass
    if not (isinstance(e, dict) and e.get('is_unique')):
        return None
    if int(e.get('equip_threshold', 1) or 0) <= 0:
        return None
    return int(ladder_pass.ladder(copy.deepcopy(e), category, key)['equip_threshold'])


def accessory_threshold(e: dict, key: str):
    """The rule's threshold for a ring kind or a named ring / amulet / belt
    (None: hand-set, or carried rather than worn)."""
    import gear
    import ring_kinds_2026_11 as ring_pass
    if not isinstance(e, dict) or e.get('slot') == 'none':
        return None
    slot = e.get('slot', 'ring')
    if e.get('kind'):
        return gear.accessory_threshold(slot, 1)
    named = e.get('is_unique') or e.get('plot_locked') or key in ring_pass.NAMED_COMMONS
    if not named:
        return None
    t = max(1, min(5, int(e.get('quiz_tier', 1) or 1)))
    return gear.accessory_threshold(slot, gear.level_for_tier(t), unique=True)


def run(path: str, rule, check: bool) -> list:
    d, fmt = jsonfmt.load(path)
    changed = []
    for k, e in d.items():
        want = rule(e, k)
        if want is None or int(e.get('equip_threshold', 0) or 0) == want:
            continue
        changed.append((k, e.get('equip_threshold'), want))
        e['equip_threshold'] = want
    if changed and not check:
        jsonfmt.save(path, d, fmt)
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='report only; exit 1 if it would change')
    a = ap.parse_args(argv)
    total = 0
    for path, rule in ((ARMOR, lambda e, k: armour_threshold(e, 'armor', k)),
                       (SHIELD, lambda e, k: armour_threshold(e, 'shields', k)),
                       (ACCESSORY, accessory_threshold)):
        changed = run(path, rule, a.check)
        total += len(changed)
        print(f"{os.path.basename(path)}: {len(changed)} threshold(s) "
              f"{'would change' if a.check else 'written'}")
    return 1 if (a.check and total) else 0


if __name__ == '__main__':
    sys.exit(main())
