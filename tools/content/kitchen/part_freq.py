"""How often each kitchen part can be harvested in a run: writes part_freq.json.

The simulator (tools/balance/difficulty_sim.py) plays mastery-kid runs; every
corpse the hero kills is counted as harvested (the right answer assumed), with
the floor it was first found on. For each part the file keeps:

  share_of_runs        the share of runs it turns up in at all
  mean_count           how many a run yields
  median_first_floor   the median floor it is first found on (runs that find it)

``build_kitchen.py`` reads the file (through ``part_rules.py``) and fails on a
feast or multi-dish a run cannot reliably cook. Regenerate it whenever the
spawn tables, the harvest map or the kin groups change:

    py tools/content/kitchen/part_freq.py                 # 15 runs, seed 1
    py tools/content/kitchen/part_freq.py --trials 30 --seed 7
    py tools/content/kitchen/part_freq.py --out scratch.json   # leave the kept file alone

A simulated run takes about 17 seconds. The rule thresholds in the file's ``rules``
block are kept as they are. Then re-run ``build_kitchen.py``; if a dish now
breaks a rule, fix the structure with ``restructure.py``.

Written by the lead for the K1b restructure (2026-11-14); the first file came
from 15 mastery runs.
"""
import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'part_freq.json')

DOC = ('How often each harvestable kitchen part turns up in a run, measured by the simulator '
       '(tools/balance/difficulty_sim.py, the mastery kid, every kill harvested). '
       'share_of_runs: the share of runs it turns up in; mean_count: how many a run yields; '
       'median_first_floor: the floor it is first found on. Regenerate with '
       '`py tools/content/kitchen/part_freq.py` (see its docstring) whenever spawns, the '
       'harvest map or the kin groups change. build_kitchen.py checks the recipe book '
       'against it through part_rules.py: rules.common_share makes a part common; a feast '
       'may also hold an early part (first found by rules.early_floor) seen in '
       'rules.early_share of runs; a food whose best spawn weight is under '
       'rules.rare_food_weight is rare.')
RULES = {'common_share': 0.9, 'early_floor': 20, 'early_share': 0.75, 'rare_food_weight': 10}


def measure(seed: int, trials: int):
    """(per-run {part: [first floor, count]}, the kitchen module)."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    os.environ['PQ_NO_BONES'] = '1'
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.chdir(ROOT)
    import difficulty_sim as ds
    import kitchen as K
    runs, seen = [], {}
    orig_fa = ds.Run._fight_and_account

    def spy(self, group, mandatory=False, boss_ctx=None):
        r = orig_fa(self, group, mandatory=mandatory, boss_ctx=boss_ctx)
        for m in group:
            if not m.alive:
                iid = K.ingredient_for_monster(getattr(m, 'kind', None))
                if iid:
                    e = seen.setdefault(id(self), {}).setdefault(iid, [self.floor, 0])
                    e[1] += 1
        return r
    orig_init = ds.Run.__init__

    def init(self, *a, **k):
        orig_init(self, *a, **k)
        runs.append(self)
    ds.Run._fight_and_account = spy
    ds.Run.__init__ = init
    ds.run_cell(profile='mastery', trials=trials, kid=True, seed=seed, quiet=True)
    return [seen.get(id(x), {}) for x in runs], K


def summarise(per_run: list, all_parts) -> dict:
    n = len(per_run)
    out = {}
    for p in sorted(all_parts):
        hits = [r[p] for r in per_run if p in r]
        out[p] = {
            'share_of_runs': round(len(hits) / n, 3) if n else 0.0,
            'mean_count': round(sum(h[1] for h in hits) / n, 2) if n else 0.0,
            'median_first_floor': statistics.median_low([h[0] for h in hits]) if hits else None,
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--trials', type=int, default=15)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    per_run, K = measure(a.seed, a.trials)
    parts = [i for i, r in K.ingredients().items() if r.get('tier_role') in ('prime', 'trophy')]
    rules = RULES
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            rules = json.load(f).get('rules', RULES)
    data = {'_doc': DOC, 'runs': len(per_run), 'seed': a.seed, 'rules': rules,
            'parts': summarise(per_run, parts)}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{len(per_run)} runs; {len(parts)} parts written to {a.out}')


if __name__ == '__main__':
    main()
