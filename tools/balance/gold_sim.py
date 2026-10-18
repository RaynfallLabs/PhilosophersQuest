#!/usr/bin/env python
"""Gold curve: what a run actually finds, floor by floor.

Wraps tools/balance/difficulty_sim.py (the real floor generator, the real
monsters, a scripted player) and books every gold roll the game would make:

  ground   gold piles on the floor (coin piles, treasury, zoo, vault, hoards)
  monsters treasure gold of every monster killed (incl. wanderers)
  chests   the chest's own gold, on a passed lockpick question
           (container_system.chest_gold when it exists, else the old roll)
  graves   economy shares, for players who dig them
  thrones  gold on exactly chain 1

Encounters, traders and theft depend on choices; purse_model.py adds them.

First written for the 2026-10-17 bug bash (_bugbash_2026_10_17/economy);
moved here for the economy refactor so the before/after curves come from one
script against the live tree.

Usage:
    py tools/balance/gold_sim.py [trials] [profile] [accuracy] [--out DIR]
Writes gold_curve_<profile>_<accuracy>.json to DIR (default: the scratch dir
tools/balance/generated/).
"""
import collections
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
sys.path.insert(0, HERE)
os.chdir(REPO)
import difficulty_sim as ds  # noqa: E402
import dungeon as dmod  # noqa: E402
import economy  # noqa: E402
from items import GoldPile  # noqa: E402

_orig_build = ds.build_snapshot
_orig_gen = ds.level_manager_mod.LevelManager.generate
_LAST = {}
EXTRA = {}


def _merchants(items):
    try:
        from mystery_system import MerchantNPC
    except ImportError:
        return []
    return [i for i in items if isinstance(i, MerchantNPC)]


def _gen(self, floor, *a, **kw):
    out = _orig_gen(self, floor, *a, **kw)
    d, mons, items = out
    _LAST['ground'] = sum(i.amount for i in items if isinstance(i, GoldPile))
    tiles = getattr(d, 'tiles', None) or []
    _LAST['graves'] = sum(row.count(dmod.GRAVE) for row in tiles) if hasattr(dmod, 'GRAVE') else 0
    mer = _merchants(items)
    _LAST['merchant'] = ((sum(mer[0].prices),
                          list(zip([type(x).__name__ + ':' + getattr(x, 'id', '?')
                                    for x in mer[0].stock], mer[0].prices)),
                          getattr(mer[0], 'trader_kind', 'generalist'),
                          int(getattr(mer[0], 'purse', 0) or 0))
                         if mer else None)
    return out


ds.level_manager_mod.LevelManager.generate = _gen


def _build(floor):
    snap = _orig_build(floor)
    EXTRA[id(snap)] = dict(ground_gold=_LAST.get('ground', 0), graves=_LAST.get('graves', 0),
                           merchant=_LAST.get('merchant'))
    return snap


ds.build_snapshot = _build

G = collections.defaultdict(lambda: collections.defaultdict(float))
VIS = collections.Counter()
MERCH = collections.defaultdict(list)

_orig_drop = ds.Run._drop_loot


def _drop(self, m):
    tr = getattr(m, 'treasure', {}) or {}
    g = tr.get('gold', [0, 0]) or [0, 0]
    gold = random.randint(int(g[0]), max(int(g[0]), int(g[1])))
    G[self.floor]['monsters'] += gold
    return _orig_drop(self, m)


ds.Run._drop_loot = _drop


def _open(self, chest):
    if not self.prof['opens_chests']:
        return
    if not self.quiz.one_question(getattr(chest, 'quiz_tier', 1)):
        return
    cg = getattr(ds.container_system, 'chest_gold', None)
    if cg is not None:
        G[self.floor]['chests'] += cg(chest, self.floor, random)
    else:
        gmin, gmax = (chest.gold[0], chest.gold[1]) if chest.gold else (0, 0)
        if gmax > 0:
            G[self.floor]['chests'] += random.randint(int(gmin + (gmax - gmin) * 0.7), gmax)
    try:
        loot = ds.container_system._generate_loot_from_template(chest, self.floor)
    except Exception:
        loot = []
    for it in loot or []:
        self.consider(it)


ds.Run._open_chest = _open

_orig_throne = ds.Run.sit_throne


def _throne(self):
    if random.random() < 0.15:
        G[self.floor]['thrones'] += economy.roll_share(random, self.floor, economy.THRONE_SHARE)
    return _orig_throne(self)


ds.Run.sit_throne = _throne

_orig_play = ds.Run.play_floor


def _play(self, floor, fights=True):
    holder = {}
    orig_get = self.cache.get

    def get(f):
        s = orig_get(f)
        holder['s'] = s
        return s
    self.cache.get = get
    r = _orig_play(self, floor, fights)
    self.cache.get = orig_get
    s0 = holder.get('s')
    s = type('X', (), EXTRA[id(s0)]) if s0 is not None else None
    if s is not None and fights:
        VIS[floor] += 1
        lf = self.prof['loot_fraction']
        G[floor]['ground'] += s.ground_gold * lf
        if self.prof['opens_chests']:
            for _ in range(int(s.graves * lf)):
                c = random.random()
                if c < 0.15:
                    G[floor]['graves'] += economy.roll_share(random, floor, economy.GRAVE_SMALL_SHARE)
                elif c > 0.5:
                    G[floor]['graves'] += economy.roll_share(random, floor, economy.GRAVE_RICH_SHARE)
        MERCH[floor].append(s.merchant)
    return r


ds.Run.play_floor = _play


def main(argv):
    out_dir = os.path.join(HERE, 'generated')
    if '--out' in argv:
        i = argv.index('--out')
        out_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    trials = int(argv[1]) if len(argv) > 1 else 20
    profile = argv[2] if len(argv) > 2 else 'prepared'
    acc = float(argv[3]) if len(argv) > 3 else 0.90
    res = ds.run_cell(profile=profile, accuracy=acc, trials=trials, floors=(1, 99),
                      variants=12, seed=7)
    st = res['stats']
    rows, cum = [], 0.0
    print(f"profile={profile} acc={acc} trials={trials}")
    print(f"{'F':>3} {'income':>7} {'ground':>7} {'mons':>7} {'chest':>6} {'grave':>6} "
          f"{'thrn':>5} {'TOTAL':>7} {'xInc':>5} {'cum':>8} {'1stDeath%':>9}")
    for f in range(1, 100):
        v = max(1, VIS[f])
        row = {k: G[f][k] / v for k in ('ground', 'monsters', 'chests', 'graves', 'thrones')}
        tot = sum(row.values())
        cum += tot
        fd = st.get(f, {}).get('first_deaths', 0) / max(1, trials)
        inc = economy.floor_income(f)
        rows.append(dict(floor=f, income=inc, total=tot, cum=cum, first_death=fd, **row))
        print(f"{f:>3} {inc:>7.0f} {row['ground']:>7.0f} {row['monsters']:>7.0f} "
              f"{row['chests']:>6.0f} {row['graves']:>6.0f} {row['thrones']:>5.0f} "
              f"{tot:>7.0f} {tot / inc:>5.2f} {cum:>8.0f} {fd * 100:>8.1f}")
    visits = {f: len(ms) for f, ms in MERCH.items()}
    shops = {f: [m for m in ms if m] for f, ms in MERCH.items()}
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'gold_curve_{profile}_{acc}.json')
    with open(path, 'w') as fh:
        json.dump(dict(rows=rows, merchant_visits=visits,
                       merchant_samples={f: ms[:6] for f, ms in shops.items()},
                       merchant_rate={f: len(shops[f]) / max(1, visits[f]) for f in shops}),
                  fh, indent=1, default=str)
    print('wrote', path)


if __name__ == '__main__':
    main(sys.argv)
