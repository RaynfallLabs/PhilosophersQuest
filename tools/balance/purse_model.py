#!/usr/bin/env python
"""Purse curve under three spending policies (economy refactor 2026-10-17).

Reads the measured income from tools/balance/gold_sim.py's JSON and walks a
run floor by floor with the REAL trader plan (traders.roll_plan), the real
stock and prices (traders.build_stock, economy.merchant_price), services and
selling. Rough on purpose: it shows where gold piles up or runs dry, not
exact numbers.

  hoarder   buys nothing, sells nothing (the purse = everything found)
  sensible  buys every potion and food item a trader has, scrolls while the
            purse stays above one floor's income, pays for a repair or a
            cure about one trader in three, and sells two or three things
            it does not need (a spare piece of gear, a couple of
            consumables) at the trader's real offer
  whale     buys everything it can afford, dearest first, and sells the same
Light vendor encounters: on ~25% of floors one thing for ~0.2 of a floor.

First written for the 2026-10-17 bug bash (_bugbash_2026_10_17/economy) for
the old single Deep Gnome Trader; this version models the named traders.

Usage: py tools/balance/purse_model.py [gold_curve.json] [runs]
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
os.chdir(REPO)
import economy  # noqa: E402
import items  # noqa: E402
import traders  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'generated',
                                                          'gold_curve_prepared_0.9.json')
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
rows = {r['floor']: r for r in json.load(open(path))['rows']}
_STOCK = {}


def stock_for(kind, floor, rng):
    key = (kind, floor, rng.randrange(4))
    if key not in _STOCK:
        items.bind_unique_registry(set())
        d = traders.kind_def(kind)
        st = traders.build_stock(d, floor, random.Random(hash(key)))
        mk = float(d.get('markup', 1.0))
        _STOCK[key] = [(type(it).__name__, economy.merchant_price(it, floor, mk)) for it in st]
    return _STOCK[key]


def sell_income(floor, purse_cap, rng, n):
    """What selling ``n`` unneeded finds brings: one spare piece of common
    gear (his price ~0.6 of a floor, 20-25%) and the rest consumables."""
    inc = economy.floor_income(floor)
    got = inc * 0.6 * rng.uniform(0.20, 0.25)
    for _ in range(max(0, n - 1)):
        got += inc * rng.choice((0.15, 0.5, 0.1)) * rng.uniform(0.20, 0.25)
    return min(purse_cap, got)


def run(policy, rng):
    plan = traders.roll_plan(rng.getrandbits(48))['floors']
    purse, spent, sold, out = 0.0, 0.0, 0.0, {}
    for f in range(1, 100):
        purse += rows[f]['total'] * rng.uniform(0.7, 1.3)
        inc = economy.floor_income(f)
        if rng.random() < 0.25 and policy != 'hoarder':        # a light vendor encounter
            c = economy.share(f, 0.2)
            if purse >= c:
                purse -= c
                spent += c
        kind = plan.get(f)
        if kind and policy != 'hoarder':
            d = traders.kind_def(kind)
            cap = inc * float(d.get('purse', 1.5))
            got = sell_income(f, cap, rng, 3 if policy == 'whale' else 2)
            purse += got
            sold += got
            stock = stock_for(kind, f, rng)
            if policy == 'sensible':
                for cls, p in stock:
                    if cls in ('Potion', 'Food') and purse >= p:
                        purse -= p
                        spent += p
                for cls, p in stock:
                    if cls == 'Scroll' and purse - p >= inc:
                        purse -= p
                        spent += p
                svc = [s for s in d.get('services') or () if s != 'porter']
                if svc and rng.random() < 0.35:
                    c = economy.service_price(rng.choice(svc), f, purse=int(purse))
                    if purse >= c:
                        purse -= c
                        spent += c
            else:
                for cls, p in sorted(stock, key=lambda x: -x[1]):
                    if purse >= p:
                        purse -= p
                        spent += p
                for s in d.get('services') or ():
                    c = economy.service_price(s, f, purse=int(purse))
                    if purse >= c and rng.random() < 0.5:
                        purse -= c
                        spent += c
        out[f] = (purse, spent, sold)
    return out


def main():
    rng = random.Random(5)
    print(f"{os.path.basename(path)}: median purse at floor (gold, and floors of that floor's income)")
    print(f"{'F':>3} {'income':>7} | {'hoarder':>17} | {'sensible':>17} | {'whale':>17} | whale spent  sold")
    res = {p: [run(p, rng) for _ in range(RUNS)] for p in ('hoarder', 'sensible', 'whale')}
    table = {}
    for f in (1, 3, 5, 8, 10, 15, 19, 25, 30, 39, 45, 50, 59, 70, 79, 90, 99):
        inc = economy.floor_income(f)
        cells, row = [], {'floor': f, 'income': inc}
        for p in ('hoarder', 'sensible', 'whale'):
            m = statistics.median(r[f][0] for r in res[p])
            row[p] = m
            cells.append(f"{m:>9,.0f} ({m / inc:>4.1f}x)")
        ws = statistics.median(r[f][1] / max(1, r[f][1] + r[f][0]) for r in res['whale'])
        sold = statistics.median(r[f][2] for r in res['sensible'])
        table[f] = row
        print(f"{f:>3} {inc:>7,.0f} | " + ' | '.join(cells) + f" | {ws:>5.0%}  {sold:>8,.0f}")
    return table


if __name__ == '__main__':
    main()
