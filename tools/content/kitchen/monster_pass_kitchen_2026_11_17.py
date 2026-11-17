"""The kitchen after the monster pass of 2026-11-17 (a record of what was run).

The pass (tools/balance/monster_pass_2026_11_17.py) moved 161 kinds deeper, so
their parts' floors, the dish tiers and how often each part turns up all
changed. The steps, in order:

1. ``py tools/content/kitchen/part_freq.py --trials 45`` (45 runs, not 15: the
   common-part line of 0.9 sits inside a 15-run sample's noise);
2. ``py tools/content/kitchen/monster_pass_kitchen_2026_11_17.py --restructure``:
   every multi-dish's cross_depth flag is first set to whether it spans depths
   now, and restructure.py is run (SWAP emptied: its stand-ins are the K1b
   record, frozen in structure.json, and several name parts that moved or were
   retired; KEEP only where the kept part is still in the dish; the song's dish
   and the special foods' dishes set aside, being rare by design). It swapped
   the second uncommon part out of 38 dishes and 7 feasts and added 12 dishes
   (dish_360 to dish_371, named in dishes_4.txt; the dishes whose name named a
   part they lost were renamed in dishes_1-3.txt);
3. ``... --flags``: cross_depth is kept on the dishes made cross-depth on
   purpose that still span (flagged before the pass, or a dish the restructure
   made to span), those with an early common monster part first, then designed
   ones with an early common helper, to about 30% of the multi-dishes
   (tests/test_kitchen_part_freq.py rule 3). A dish that spans only because one
   of its creatures moved deep was not made so and is not flagged;
4. ``py tools/content/kitchen/build_kitchen.py``.

The 44 dish pictures the new dish tiers needed (dish_<kind>_t<tier>_<tab>) were
drawn from tools/content/genart/briefs/items_dishes_g40.json.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
os.chdir(ROOT)

import build_kitchen as B  # noqa: E402
import part_rules as PR  # noqa: E402
import restructure as R  # noqa: E402

STRUCT = os.path.join(HERE, 'structure.json')
SPECIAL = set(B.SPECIAL_FOOD) | set(B.SONG_FOOD)


def _floors(ings):
    food = B._load(os.path.join(B.ITEMS, 'food.json'))

    def fl(p):
        if p in ings:
            return ings[p]['floor']
        if p in B.FOOD:
            return B.FOOD[p][1]
        return int(food.get(p, {}).get('min_level', 1) or 1)
    return fl


def restructure():
    S = json.load(open(STRUCT, encoding='utf-8'))
    ings, _h, _a = B.build_ingredients()
    fl = _floors(ings)
    for d in S.values():
        if len(set(d['parts'])) > 1:
            f = [fl(p) for p in d['parts']]
            d['cross_depth'] = min(f) <= 20 and max(f) >= 40
    with open(STRUCT, 'w', encoding='utf-8') as f:
        json.dump(S, f, ensure_ascii=False, indent=1)
    R.SWAP = {}
    R.KEEP = {d: p for d, p in R.KEEP.items() if d in S and p in S[d]['parts']}
    orig = R.restructure

    def wrapped(S, ings, rules, namer, seed=20261114):
        aside = {k: v for k, v in S.items() if v.get('song') or v.get('makes')
                 or any(p in SPECIAL for p in v['parts'])}
        for k in aside:
            del S[k]
        log = orig(S, ings, rules, namer, seed)
        S.update(aside)
        food = B._load(os.path.join(B.ITEMS, 'food.json'))
        for fid in SPECIAL:
            B.FOOD.setdefault(fid, ('sp', int(food.get(fid, {}).get('min_level', 1) or 1)))
        return log
    R.restructure = wrapped
    sys.argv = [sys.argv[0], '--log', os.path.join(HERE, 'naming_worksheet_2026_11_17.txt')]
    R.main()


def flags(base_rev: str = 'HEAD~1'):
    """``base_rev``: the commit before the pass (whose flags say which dishes
    were made cross-depth on purpose)."""
    old = json.loads(subprocess.check_output(
        ['git', 'show', f'{base_rev}:tools/content/kitchen/structure.json']).decode('utf-8'))
    S = json.load(open(STRUCT, encoding='utf-8'))
    ings, _h, _a = B.build_ingredients()
    fl = _floors(ings)
    food = B._load(os.path.join(B.ITEMS, 'food.json'))
    freq = PR.load_freq()
    kf = list(B.FOOD) + list(B.SPECIAL_FOOD)
    rare = PR.rare_foods({k: food[k] for k in kf}, freq['rules']['rare_food_weight'])
    rules = PR.PartRules(freq, lambda p: ings[p]['role'] if p in ings
                         else ('food' if p in kf else None), rare)

    def helper(p):
        return p in kf or (p in ings and ings[p]['role'] == 'dungeon')
    multis = [k for k, d in S.items() if len(set(d['parts'])) > 1]
    first, second = [], []
    for did in multis:
        d = S[did]
        f = [fl(p) for p in d['parts']]
        if d.get('song') or not (min(f) <= 20 and max(f) >= 40):
            continue
        early_mon = any(fl(p) <= 20 and rules.is_common(p) and not helper(p) for p in d['parts'])
        designed = bool(old[did].get('cross_depth')) if did in old else True
        if early_mon:
            first.append(did)
        elif designed and any(fl(p) <= 20 and rules.is_common(p) for p in d['parts']):
            second.append(did)
    keep = set(first)
    for did in sorted(second):
        if len(keep) >= int(0.30 * len(multis)):
            break
        keep.add(did)
    for did in multis:
        S[did]['cross_depth'] = did in keep
    with open(STRUCT, 'w', encoding='utf-8') as f:
        json.dump(S, f, ensure_ascii=False, indent=1)
    print(f'cross-depth: {len(keep)} of {len(multis)}')


if __name__ == '__main__':
    if '--restructure' in sys.argv:
        restructure()
    elif '--flags' in sys.argv:
        flags()
    else:
        print(__doc__)
