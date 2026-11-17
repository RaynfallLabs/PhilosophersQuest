"""
Mini-boss fights, fast: save the simulator's heroes on the mini-boss floors
once, then fight every named foe against them from the current data.

Offline tooling. It drives tools/balance/difficulty_sim.py without changing
it (a hook on Run.rededicate saves a copy of the hero at the start of each
mini-boss floor), so a retune of data/monsters.json is measured in a minute
instead of a full Monte Carlo.

    py tools/balance/mini_boss_fights.py heroes OUT 100 mastery committed
    py tools/balance/mini_boss_fights.py fight OUT [--reps 3] [--prof mastery,committed]
                                                   [--only id,id] [--workers 4]

`heroes` runs 100 kid-model runs a profile (20 a worker task, MC_WORKERS
workers, 4 by default) and saves each living hero at the start of each foe's
floor. `fight` mirrors difficulty_sim.Run._boss_side_fights for every foe
mini_boss_bands owns: a copy of the hero at full health, debuffs cleared,
the foe alone, no quest layer. It prints, per foe and profile: fights, the
hero's attacks (median, p10-p90), the share of his health lost (median,
p90), deaths and stalemates. The tuning of 2026-11-14 was measured this way
(docs/systems/monsters.md, "Mini-boss tuning").

Heroes wielding the Green Chapel Axe are left out of `fight`: its returning
blow (combat.py, `returning_blow`) gives back half of a max-chain blow
uncapped, so deep down one swing kills its wielder whatever he fights.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import random
import statistics
import sys
import time
import uuid
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.environ['PQ_NO_BONES'] = '1'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

BOSS_FLOORS = {20, 40, 60, 80, 100}
SEAL_FLOORS = {83: 'seal_demon_wrath', 85: 'seal_demon_pestilence', 87: 'seal_demon_famine',
               89: 'seal_demon_war', 91: 'seal_demon_death', 93: 'seal_demon_earthquake',
               97: 'seal_demon_silence'}
CHUNK = 20


def met_on() -> dict:
    """{foe: floor it is met on}: its peak floor, or the free floor of its
    band nearest it when the peak is a gate or seal floor, as
    level_manager.plan_mini_bosses seats it (every rolled mini-boss, the
    legendary ones too, since 2026-11-17)."""
    import level_manager
    import mini_boss_bands as mb
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        monsters = json.load(f)
    out = {}
    taken = BOSS_FLOORS | set(SEAL_FLOORS)
    for mid, g in mb.roster(monsters).items():
        if g == 'seal':
            out[mid] = next(fl for fl, s in SEAL_FLOORS.items() if s == mid)
            continue
        pf = mb.floor_of(monsters[mid])
        lo = (pf - 1) // 20 * 20 + 1
        out[mid] = level_manager._free_floor(pf, lo, lo + 19, taken, {})
    return out


def _cell(kw):
    import difficulty_sim as ds
    floors = set(kw.pop('_floors'))
    out = kw.pop('_out')
    orig = ds.Run.rededicate

    def rededicate(self, floor):
        orig(self, floor)
        if getattr(self, '_is_fork', False) or floor not in floors:
            return
        if not hasattr(self, '_mb_id'):
            self._mb_id = uuid.uuid4().hex[:10]
        twin = self.fork()
        twin.cache = twin._drop_pool = None
        d = os.path.join(out, self.profile_name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{floor:03d}_{self._mb_id}.pkl"), 'wb') as f:
            pickle.dump(twin, f, protocol=pickle.HIGHEST_PROTOCOL)

    ds.Run.rededicate = rededicate
    try:
        ds.run_cell(**kw)
    finally:
        ds.Run.rededicate = orig
    return kw['profile'], kw['trials']


def heroes(out: str, trials: int, profiles: list, workers: int) -> None:
    import multiprocessing as mp
    import difficulty_sim as ds
    floors = sorted(set(met_on().values()))
    tasks = []
    for i, prof in enumerate(profiles):
        for c in range(0, trials, CHUNK):
            tasks.append(dict(profile=prof, accuracy=0.95, trials=min(CHUNK, trials - c), floors=(1, 100),
                              knobs=ds.parse_knobs(''), speed=1.0, seed=7 + 1000 * i + c, variants=24,
                              kid=True, _floors=floors, _out=out))
    t0 = time.time()
    with mp.Pool(min(workers, len(tasks))) as pool:
        for prof, n in pool.imap_unordered(_cell, tasks):
            print(f"  {prof}: {n} runs saved ({time.time() - t0:.0f}s)", flush=True)


def _fight(args):
    prof, floor, files, foes, reps, seed = args
    import difficulty_sim as ds
    from monster import Monster
    ds.KID_MODEL = True
    random.seed(seed)
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    rows = []
    for fn in files:
        with open(fn, 'rb') as f:
            run = pickle.load(f)
        run.cache = ds.FloorCache(1)
        run._drop_pool = ds._POOL_CACHE
        ids = [getattr(run.p.weapon, 'id', '')] + [getattr(w, 'id', '') for w in getattr(run, 'arsenal', [])]
        if any('green_chapel' in str(i) for i in ids):
            continue
        for mid in foes:
            proto = Monster({**defs[mid], 'id': mid}, 5, 5)
            for _ in range(reps):
                twin = run.fork()
                twin._is_fork = True
                twin.floor = twin.quiz.floor = floor
                twin.rest_left = 200
                tp = twin.p
                tp.hp = tp.max_hp
                for e in list(tp.status_effects):
                    if e in ds.DEBUFFS:
                        tp.status_effects.pop(e, None)
                g = [ds.fresh_monster(proto, twin.knobs, floor)]
                ctx = twin._boss_ctx(g, False)
                twin._boss_prefight(ctx)
                dmg0 = tp._dmg_taken
                res = twin.fight(g, mandatory=True, boss_ctx=ctx)
                rows.append((prof, mid, g[0]._sim_attacks, (tp._dmg_taken - dmg0) / max(1, tp.max_hp),
                             res == 'dead', res == 'stalemate'))
    return rows


def fight(snap: str, profiles: list, reps: int, only: list, workers: int) -> list:
    import multiprocessing as mp
    where = met_on()
    by_floor = defaultdict(list)
    for mid, fl in where.items():
        if not only or mid in only:
            by_floor[fl].append(mid)
    tasks, seed = [], 1
    for prof in profiles:
        d = os.path.join(snap, prof)
        if not os.path.isdir(d):
            continue
        names = sorted(os.listdir(d))
        for fl, foes in sorted(by_floor.items()):
            files = [os.path.join(d, n) for n in names if n.startswith(f"{fl:03d}_")]
            for i in range(0, len(files), 10):
                seed += 1
                tasks.append((prof, fl, files[i:i + 10], foes, reps, seed))
    rows = []
    with mp.Pool(workers) as pool:
        for r in pool.imap_unordered(_fight, tasks):
            rows += r
    by = defaultdict(list)
    for r in rows:
        by[(r[1], r[0])].append(r)
    print(f"{'foe':24} {'F':>3}  " + '  '.join(f"{p[:12]:>12}: n  atk (p10-p90)  lost (p90)  died" for p in profiles))
    for mid in sorted({r[1] for r in rows}, key=lambda m: (where[m], m)):
        cells = []
        for p in profiles:
            rs = by.get((mid, p))
            if not rs:
                cells.append(' ' * 50)
                continue
            atk = sorted(r[2] for r in rs)
            lost = sorted(r[3] for r in rs)

            def q(a, x):
                return a[min(len(a) - 1, int(x * len(a)))]
            cells.append(f"{len(rs):15} {statistics.median(atk):4.0f} ({q(atk, .1):2}-{q(atk, .9):3})  "
                         f"{statistics.median(lost):4.0%} ({q(lost, .9):4.0%})  {sum(r[4] for r in rs) / len(rs):4.1%}")
        print(f"{mid:24} {where[mid]:3}  " + '  '.join(cells))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    h = sub.add_parser('heroes')
    h.add_argument('out')
    h.add_argument('trials', type=int)
    h.add_argument('profiles', nargs='+')
    f = sub.add_parser('fight')
    f.add_argument('snap')
    f.add_argument('--reps', type=int, default=3)
    f.add_argument('--prof', default='mastery,committed')
    f.add_argument('--only', default='')
    for p in (h, f):
        p.add_argument('--workers', type=int, default=int(os.environ.get('MC_WORKERS') or 4))
    a = ap.parse_args(argv)
    if a.cmd == 'heroes':
        heroes(a.out, a.trials, a.profiles, a.workers)
    else:
        fight(a.snap, a.prof.split(','), a.reps, [x for x in a.only.split(',') if x], a.workers)
    return 0


if __name__ == '__main__':
    sys.exit(main())
