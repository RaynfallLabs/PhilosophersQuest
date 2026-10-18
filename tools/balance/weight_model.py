#!/usr/bin/env python
"""What a careful player can CARRY (coin weight and treasure, 2026-10-18).

Brandon's D2: coins weigh a tenth of an ounce (160 to the pound), so the purse
counts toward the carry limit, and gems and treasure are how a hero carries
wealth. This model walks runs floor by floor with:

  * the measured coin and treasure a floor pays (tools/balance/gold_sim.py's
    JSON: ``total`` is coin, ``t_value`` / ``t_weight`` / ``t_<kind>`` are
    treasure);
  * a careful hero's carrying: Strength 10 rising to 18 by floor 80 (meals,
    gate gifts), limit 20 + 8 x STR, a kit of armour, weapon and supplies
    that grows from 40 to 60 lb, and the rule he plays by: never Burdened
    (load at most 75% of the limit);
  * the real trader plan, stock and prices (traders.roll_plan, build_stock,
    economy.merchant_price), gems for sale at value x the spread, treasure
    taken at buy_rate (data/traders.json ``treasure``).

Policies:
  careful   keeps every gem and piece of jewellery, keeps an art object only
            while it fits under the Burdened line, takes coin up to that line
            and leaves the rest; at a trader sells art, buys the sensible
            basket (potions, food, a scroll or two, a service one time in
            three), paying coin first and then treasure, and changes coin
            above ~12 lb into gems.
  hoarder   the same carrying, but never buys and never changes coin to gems.

For each depth it prints what the careful hero carries in coin, in gems and
jewellery, and in art; his wealth in floors of income; the coin he had to
leave behind; and how often the dearest ware on a trader's table was within
reach of his coin plus treasure.

Usage: py tools/balance/weight_model.py [gold_curve.json] [runs]
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
import treasure  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'generated',
                                                          'gold_curve_prepared_0.9.json')
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
rows = {r['floor']: r for r in json.load(open(path))['rows']}
BUY = treasure.buy_rate()
MARKUP = treasure.sell_markup()
KEEP_COIN_LB = 12.0          # coin kept for small costs; above it, changed to gems
_STOCK = {}


def strength(f):
    return min(18, 10 + f // 10)


def kit_weight(f):
    return 40.0 + 20.0 * min(1.0, f / 99.0)


def burden_room(f):
    """Pounds a careful hero can give to wealth without being Burdened."""
    limit = 20 + 8 * strength(f)
    return max(0.0, 0.75 * limit - kit_weight(f))


def stock_for(kind, floor, rng):
    key = (kind, floor, rng.randrange(4))
    if key not in _STOCK:
        items.bind_unique_registry(set())
        d = {**traders.kind_def(kind), 'kind': kind}
        st = traders.build_stock(d, floor, random.Random(hash(key)))
        mk = float(d.get('markup', 1.0))
        _STOCK[key] = [(type(it).__name__, getattr(it, 'item_class', ''),
                        economy.merchant_price(it, floor, mk),
                        treasure.unit_value(it)) for it in st]
    return _STOCK[key]


def run(policy, rng):
    plan = traders.roll_plan(rng.getrandbits(48))['floors']
    coin = 0.0                  # carried
    light = 0.0                 # gems, jewellery, old coin: value (weight ~0)
    light_lb = 0.0
    art = []                    # [(value, weight)]
    left = 0.0                  # coin left on the floor, all run
    out = {}
    for f in range(1, 100):
        r = rows[f]
        k = rng.uniform(0.7, 1.3)
        room = burden_room(f)
        # Treasure found: light kinds kept; art kept while it fits.
        lv = (r.get('t_gem', 0) + r.get('t_jewellery', 0) + r.get('t_coins', 0)) * k
        light += lv
        light_lb += lv / 2000.0                      # ~0.05-0.5 lb per piece: negligible
        av = r.get('t_art', 0) * k
        if av > 0:
            aw = max(1.0, r.get('t_weight', 0) * k - lv / 2000.0)
            art.append((av, aw))
        while art and coin / treasure.COINS_PER_LB + light_lb + sum(w for _v, w in art) > room:
            art.sort(key=lambda a: a[0] / a[1])      # the worst value per pound goes first
            art.pop(0)
        # Coin found: what fits under the Burdened line.
        found = r['total'] * k
        space = room - light_lb - sum(w for _v, w in art) - coin / treasure.COINS_PER_LB
        take = min(found, max(0.0, space) * treasure.COINS_PER_LB)
        coin += take
        left += found - take
        inc = economy.floor_income(f)
        kind = plan.get(f)
        reach = None            # this floor's trader: could he buy the dearest ware?
        if kind:
            stock = stock_for(kind, f, rng)
            wares = [(cls, ic, p, v) for cls, ic, p, v in stock if ic != 'treasure']
            if wares:
                dearest = max(p for _c, _i, p, _v in wares)
                reach = coin + (light + sum(v for v, _w in art)) * BUY >= dearest
            if policy == 'careful':
                # Art is heavy: turn it into coin and gems at his table.
                for v, _w in art:
                    coin += v * BUY
                art = []
                spend = []
                for cls, ic, p, _v in wares:
                    if ic in ('potion', 'food'):
                        spend.append(p)
                    elif ic == 'scroll' and p <= inc:
                        spend.append(p)
                d = traders.kind_def(kind)
                svc = [s for s in d.get('services') or () if s != 'porter']
                if svc and rng.random() < 0.35:
                    spend.append(economy.service_price(rng.choice(svc), f,
                                                       purse=int(coin + light * BUY)))
                for p in spend:
                    if coin >= p:
                        coin -= p
                    elif coin + light * BUY >= p:
                        light -= (p - coin) / BUY
                        coin = 0.0
                # Coin above what he keeps for small costs: change it to gems.
                keep = KEEP_COIN_LB * treasure.COINS_PER_LB
                gem_stock = sum(p for _c, ic, p, _v in stock if ic == 'treasure')
                excess = max(0.0, coin - keep)
                change = min(excess, gem_stock)
                coin -= change
                light += change / MARKUP
                # Coin over the line (the art sold) he cannot carry stays here.
                cap = max(0.0, room - light_lb) * treasure.COINS_PER_LB
                if coin > cap:
                    left += coin - cap
                    coin = cap
        out[f] = dict(coin=coin, light=light, art=sum(v for v, _w in art),
                      art_lb=sum(w for _v, w in art), left=left, reach=reach)
    return out


def main():
    rng = random.Random(5)
    res = {p: [run(p, rng) for _ in range(RUNS)] for p in ('careful', 'hoarder')}
    print(f"{os.path.basename(path)}, {RUNS} runs: what a careful hero carries (medians)")
    print(f"{'F':>3} {'inc':>6} {'STR':>3} {'room':>5} | {'coin':>7} {'lb':>4} | {'gems+jewels':>11} | "
          f"{'art':>6} {'lb':>4} | {'wealth':>7} {'xInc':>5} | {'coin left':>9} | {'reach':>5} | "
          f"{'hoarder':>8} {'xInc':>5}")
    table = {}
    prev = 0
    for f in (3, 5, 10, 15, 19, 25, 30, 39, 45, 50, 59, 65, 70, 79, 85, 90, 99):
        inc = economy.floor_income(f)
        med = {k: statistics.median(r[f][k] for r in res['careful'])
               for k in ('coin', 'light', 'art', 'art_lb', 'left')}
        wealth = med['coin'] + med['light'] + med['art']
        visits = [r[g]['reach'] for r in res['careful'] for g in range(prev + 1, f + 1)
                  if r[g]['reach'] is not None]
        prev = f
        reach = sum(visits) / len(visits) if visits else 0.0
        hw = statistics.median(r[f]['coin'] + r[f]['light'] + r[f]['art'] for r in res['hoarder'])
        table[f] = dict(income=inc, **med, wealth=wealth, reach=reach, hoarder=hw)
        print(f"{f:>3} {inc:>6,.0f} {strength(f):>3} {burden_room(f):>5.0f} | {med['coin']:>7,.0f} "
              f"{med['coin'] / treasure.COINS_PER_LB:>4.0f} | {med['light']:>11,.0f} | "
              f"{med['art']:>6,.0f} {med['art_lb']:>4.0f} | {wealth:>7,.0f} {wealth / inc:>5.1f} | "
              f"{med['left']:>9,.0f} | {reach:>5.0%} | {hw:>8,.0f} {hw / inc:>5.1f}")
    return table


if __name__ == '__main__':
    main()
