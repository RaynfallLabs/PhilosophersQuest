#!/usr/bin/env python
"""The skill race: a closed model of one ordinary fight, no map and no AI.

The balance study's second model (2026-11-17), beside the Monte Carlo. It
asks how a fight goes for players who answer at different speeds, on the
game's own numbers:

  * the hero's blow: a maths chain on the WIS-second clock (Player
    SUBJECT_TIMER), right with probability acc, each answer a lognormal time
    (sigma 0.3); damage = base x chain^1.15. The base on each floor is set
    the way tools/balance/weapon_curve.py sets the common weapons: the
    balance child (CHILD_SECONDS, CHILD_ACC there) kills the floor's typical
    ordinary monster in target_attacks(floor) chains.
  * the monster: drawn from the game's own spawn pool for the floor
    (dungeon._build_spawn_pool, bosses left out), HP rolled from its dice;
    each turn it lives after the hero's first blow it makes its attacks,
    each landing on d20 >= thac0 - AC, for the mean of its dice.
  * the hero's health: floor_curve.health_bar (what the game sizes hazards
    against) unless given.

Usage:
    py tools/balance/skill_race.py [--ac N] [--fights N]
Prints, for floors 1-30, each player's attacks to kill, the share of
monsters killed before they swing, and what a fight costs in health.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'src'))
os.environ['PQ_NO_BONES'] = '1'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import weapon_curve as wc  # noqa: E402
import floor_curve  # noqa: E402

EXP = 1.15
SIGMA = 0.30

# (label, seconds a tier-1 sum, accuracy). Brandon from his own file.
PLAYERS = [('Brandon (1.5 s, 95%)', 1.52, 0.95),
           ('weapon-curve child (1.61 s)', 1.61, 0.95),
           ('sim kid (1.8 s)', 1.8, 0.95),
           ('kid 2.7 s', 2.7, 0.95),
           ('kid 3.6 s', 3.6, 0.95),
           ('kid 2.7 s, 85%', 2.7, 0.85)]

_DICE = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


def roll(expr, rng):
    s = str(expr).replace(' ', '')
    m = _DICE.fullmatch(s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    n, d, k = int(m.group(1) or 1), int(m.group(2)), int(m.group(3) or 0)
    return sum(rng.randint(1, d) for _ in range(n)) + k


def mean_dice(expr):
    s = str(expr).replace(' ', '')
    m = _DICE.fullmatch(s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    return int(m.group(1) or 1) * (int(m.group(2)) + 1) / 2 + int(m.group(3) or 0)


def pool(floor):
    import bones
    real = bones.load_bones
    bones.load_bones = lambda *a, **k: None
    import dungeon
    try:
        rows = []
        for mid, m in dungeon._build_spawn_pool(floor).items():
            if m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon'):
                continue
            dmg = sum(mean_dice(a.get('damage', '0')) for a in (m.get('attacks') or [])
                      if isinstance(a, dict))
            rows.append(dict(id=mid, hp=m.get('hp'), w=float(m['_spawn_freq']),
                             thac0=int(m.get('thac0', 20) or 20), dmg=dmg,
                             speed=int(m.get('speed', 12) or 12),
                             ai=m.get('ai_pattern', '')))
        return rows
    finally:
        bones.load_bones = real


def chain(sec, acc, clock, rng):
    t, c = 0.0, 0
    while True:
        dt = rng.lognormvariate(math.log(sec), SIGMA)
        if t + dt > clock:
            return c
        t += dt
        if rng.random() < acc:
            c += 1
        else:
            return c


def attacks_to_kill(hp, base, sec, acc, clock, rng, cap=40):
    n, dealt = 0, 0.0
    while dealt < hp and n < cap:
        n += 1
        c = chain(sec, acc, clock, rng)
        dealt += base * (c ** EXP if c else 0.0)
    return n


def calibrate(rows, floor, rng, fights):
    """The base at which the balance child needs target_attacks(floor)."""
    clock = wc.clock(floor)
    sec, acc = wc.CHILD_SECONDS[1], wc.CHILD_ACC[1]
    target = wc.target_attacks(floor)
    hps = sample_hps(rows, rng, fights)
    lo, hi = 0.1, 2000.0
    for _ in range(30):
        mid = math.sqrt(lo * hi)
        r = random.Random(floor)
        mean = sum(attacks_to_kill(h, mid, sec, acc, clock, r) for h in hps) / len(hps)
        if mean > target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi), hps


def sample_hps(rows, rng, n):
    tot = sum(r['w'] for r in rows)
    out = []
    for _ in range(n):
        x = rng.random() * tot
        for r in rows:
            x -= r['w']
            if x <= 0:
                out.append(max(1.0, roll(r['hp'], rng)))
                break
    return out


def fight_cost(rows, base, sec, acc, clock, ac, hero_hp, rng, fights):
    """Mean attacks to kill, share killed before it swings, mean share of
    the hero's health one fight costs, and the share of fights costing
    over a quarter of it."""
    tot = sum(r['w'] for r in rows)
    n_atk = one = 0
    cost_sum = 0.0
    big = 0
    for _ in range(fights):
        x = rng.random() * tot
        for r in rows:
            x -= r['w']
            if x <= 0:
                break
        hp = max(1.0, roll(r['hp'], rng))
        a = attacks_to_kill(hp, base, sec, acc, clock, rng)
        n_atk += a
        swings = a - 1
        if r['speed'] >= 14 or r['ai'] in ('ambush', 'mimic', 'ranged'):
            swings += 1                       # it strikes first
        if swings <= 0:
            one += 1
            continue
        p_hit = min(0.95, max(0.05, (21 - (r['thac0'] - ac)) / 20.0))
        cost = swings * p_hit * r['dmg'] / hero_hp
        cost_sum += cost
        if cost > 0.25:
            big += 1
    return n_atk / fights, one / fights, cost_sum / fights, big / fights


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--ac', type=float, default=None,
                    help='the hero\'s AC (descending, 10 bare); default 10 - floor/3, capped at 1')
    ap.add_argument('--fights', type=int, default=3000)
    ap.add_argument('--floors', default='1,3,5,7,10,13,16,19,22,25,28')
    args = ap.parse_args(argv)
    floors = [int(x) for x in args.floors.split(',')]
    rng = random.Random(17)
    print("The game's own anchors (floor_curve): a typical monster's blow against the hero's health")
    print("floor  monster HP  blow  hero health  blow %health  hits to kill the hero")
    for f in (1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100):
        d, h = floor_curve.target_dmg(f), floor_curve.health_bar(f)
        print(f"{f:5d}  {floor_curve.target_hp(f):9.0f}  {d:5.2f}  {h:10.0f}  {100 * d / h:11.1f}%  {h / d:8.0f}")
    print()
    for f in floors:
        rows = pool(f)
        base, _ = calibrate(rows, f, rng, 600)
        clock = wc.clock(f)
        ac = args.ac if args.ac is not None else max(1.0, 10.0 - f / 3.0)
        hero = floor_curve.health_bar(f)
        print(f"floor {f}: base {base:.1f}, clock {clock} s, AC {ac:.0f}, hero health {hero:.0f}, "
              f"{len(rows)} kinds in the pool")
        for label, sec, acc in PLAYERS:
            atk, one, cost, big = fight_cost(rows, base, sec, acc, clock, ac, hero, rng, args.fights)
            print(f"   {label:<30} attacks/kill {atk:4.2f}   dies before it swings {100 * one:4.0f}%   "
                  f"fight costs {100 * cost:5.1f}% health   over a quarter {100 * big:4.1f}%")
    return 0


if __name__ == '__main__':
    sys.exit(main())
