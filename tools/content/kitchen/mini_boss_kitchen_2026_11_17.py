"""The kitchen after the mini-bosses were seated by lore (ruling 13, 2026-11-17;
a record of what was run).

tools/balance/mini_boss_seats.py moved fourteen named foes to the band their
legend belongs in (the Nemean Lion 55 -> 17, the Calydonian Boar 27 -> 12,
Talos 21 -> 18, the Wendigo 85 -> 69, ...), so their parts' floors and the
tiers of the dishes they go into changed with them. The steps:

1. Polyphemus, the new named Cyclops, joins the cyclopes' kin group
   (kin_groups.txt): close kin share one ingredient, the Cyclops Mutton Links,
   whose floor (the kept members' median) does not move.
2. ``py tools/content/kitchen/mini_boss_kitchen_2026_11_17.py``: a dish
   flagged cross_depth (an early part with a deep one, a third of the
   multi-dishes: tests/test_kitchen_rebuild.py) whose parts no longer span
   floors 1-20 and 40 or deeper, because a mini-boss's part moved shallow, is
   no longer flagged. No dish gains the flag here: the flags are a design
   choice (monster_pass_kitchen_2026_11_17.py --flags).
3. ``py tools/content/kitchen/build_kitchen.py``.

The Wisdom stat dishes stayed spread across the tiers because the Sphinx
kept her depth (45) and Anansi his (92) (tools/balance/tier_census.py,
"Dishes: Stat WIS").
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
os.chdir(ROOT)

import build_kitchen as B  # noqa: E402

STRUCT = os.path.join(HERE, 'structure.json')


def unflag() -> list:
    S = json.load(open(STRUCT, encoding='utf-8'))
    ings, _h, _a = B.build_ingredients()
    food = B._load(os.path.join(B.ITEMS, 'food.json'))

    def fl(p):
        if p in ings:
            return ings[p]['floor']
        if p in B.FOOD:
            return B.FOOD[p][1]
        return int(food.get(p, {}).get('min_level', 1) or 1)
    out = []
    for did, d in S.items():
        if d.get('cross_depth'):
            f = [fl(p) for p in d['parts']]
            if not (min(f) <= 20 and max(f) >= 40):
                d['cross_depth'] = False
                out.append(did)
    if out:
        with open(STRUCT, 'w', encoding='utf-8') as fh:
            json.dump(S, fh, ensure_ascii=False, indent=1)
    return out


if __name__ == '__main__':
    print('no longer cross-depth:', unflag())
