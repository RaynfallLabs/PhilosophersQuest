#!/usr/bin/env python
"""What the monsters of each floor do to a hero of that floor: a MEASURING tool.

Brandon, 2026-11-19: no smoothing multipliers. A band that is too easy is
fixed by editing its monsters, armour and drops one by one, by lore. This
tool only says where the curve stands; it changes nothing.

For each floor it takes the game's own spawn weights (the bell from
peak_floor / spread / peak_weight, the min_level gate and the domain's kin
weights, as dungeon._build_spawn_pool) and, against the simulated
full-system hero of that floor (max HP and AC from the balance study's
200-run cells, floors 1-99):

  * hp_med / anchor - the weighted median HP of an ordinary monster against
    floor_curve.target_hp (the weapon curve is calibrated to the anchor, so
    a band's median should stay near 1.0 while its kinds differ widely);
  * blow    - the mean damage of one landed blow, as a share of the hero's
    health (spawn-weighted);
  * turn    - what one monster turn costs on average: hit chance (d20 >=
    thac0 - AC) x the turn's damage (all its attacks when it makes a full
    routine, multi_attack_count / multi_attack_always, else one chosen at
    random) as a share of the hero's health;
  * p10-p90 - the spread of `turn` across the floor's kinds (diversity);
  * power   - the share of the floor's spawns that carry a status rider;
  * opener  - the share that open with a power (the `opener` field).

Usage:
    py tools/balance/monster_bands.py [--over proposals.json ...] [--floors 1-40]
        [--kinds 12]     list each floor's heaviest kinds as well

--over takes one or more JSON files {monster_id: {field: value, ...}} that
are laid over data/monsters.json before measuring (a whole new monster is a
full entry under a new id), so an authoring pass can be checked before it is
written into the data.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402

# The simulated full-system hero (3.5.4, balance study cells F_adult / F_kid,
# 2026-11-17): floor -> (AC, max HP). AC is descending (10 bare).
HERO = {1: (9.5, 30), 3: (9.6, 38), 5: (8.8, 47), 7: (7.9, 58), 10: (6.9, 73),
        13: (5.7, 88), 16: (5.3, 103), 20: (3.5, 124), 25: (2.2, 149),
        30: (1.1, 173), 40: (-2.2, 227), 50: (-3.9, 298), 60: (-6.7, 350),
        70: (-8.4, 424), 80: (-10.0, 500), 90: (-10.3, 562), 99: (-10.8, 627)}

_DICE = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


def dice_mean(expr) -> float:
    s = str(expr or '0').replace(' ', '')
    m = _DICE.fullmatch(s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    return int(m.group(1) or 1) * (int(m.group(2)) + 1) / 2 + int(m.group(3) or 0)


def hero_at(floor: float) -> tuple[float, float]:
    ks = sorted(HERO)
    f = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            t = (f - a) / (b - a)
            return (HERO[a][0] + (HERO[b][0] - HERO[a][0]) * t,
                    HERO[a][1] + (HERO[b][1] - HERO[a][1]) * t)
    return HERO[ks[-1]]


def load(overs=()) -> dict:
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)
    for p in overs:
        with open(p, encoding='utf-8') as f:
            o = json.load(f)
        for k, v in o.items():
            if k.startswith('_') or not isinstance(v, dict):
                continue
            if k in d:
                d[k] = {**d[k], **v}
            else:
                d[k] = v
    return d


def is_named(m: dict) -> bool:
    return bool(m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon'))


def pool(defs: dict, level: int) -> dict:
    """dungeon._build_spawn_pool's weights, on `defs`."""
    try:
        import hazards
        kin = hazards.kin_weight
    except Exception:
        def kin(_lv, _fam):
            return 1.0
    out = {}
    for k, v in defs.items():
        if not isinstance(v, dict) or is_named(v):
            continue
        pw = v.get('peak_weight', 0) or 0
        if pw <= 0 or v.get('min_level', 1) > level:
            continue
        pf = v.get('peak_floor', v.get('min_level', 1))
        sp = max(1, v.get('spread', 10))
        bell = math.exp(-((level - pf) ** 2) / (2 * sp ** 2))
        if bell < 0.005:
            continue
        out[k] = max(0.02, pw * bell) * kin(level, v.get('family', ''))
    return out


def _distance(a: dict) -> bool:
    """breath.is_distance: flagged `ranged` or named with a ranged word."""
    try:
        from monster import _RANGED_WORDS as words
    except Exception:
        words = ('shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl', 'volley', 'ray', 'blast',
                 'breath', 'gaze', 'song', 'wail', 'charm', 'psionic', 'disintegrat', 'cast',
                 'bow', 'sling', 'javelin', 'spore', 'shock', 'hex')
    name = str(a.get('name', '')).lower()
    return bool(a.get('ranged')) or any(w in name for w in words)


def turn_damage(m: dict) -> tuple[float, float]:
    """(mean damage of one blow, mean damage of one turn). A breather with a
    routine (src/breath.py routine()) makes it of its first N close blows
    that are no breath, while the breath is drawn up; the ready breath is a
    turn of its own (one blow), so its turn is the routine."""
    atks = [a for a in (m.get('attacks') or []) if isinstance(a, dict)]
    if not atks:
        return 0.0, 0.0
    means = [dice_mean(a.get('damage')) for a in atks]
    one = sum(means) / len(means)
    n = int(m.get('multi_attack_count', 0) or 0)
    if n > 0 and not is_named(m) and any(a.get('delivery') == 'breath'
                                         and a.get('recharge', 3) for a in atks):
        blows = [dice_mean(a.get('damage')) for a in atks
                 if a.get('delivery') != 'breath' and not _distance(a)][:n]
        return one, max(sum(blows), max(dice_mean(a.get('damage')) for a in atks
                                        if a.get('delivery') == 'breath'))
    if m.get('multi_attack_always') or n >= len(atks):
        return one, sum(means)
    if n > 0:
        return one, sum(means[:n])
    return one, one


def has_power(m: dict) -> bool:
    return any(isinstance(a, dict) and a.get('effect') and float(a.get('effect_chance', 0) or 0) > 0
               for a in (m.get('attacks') or []))


def wpct(pairs, q):
    """Weighted percentile of [(value, weight)]."""
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs) or 1.0
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * tot:
            return v
    return pairs[-1][0] if pairs else 0.0


def floor_row(defs: dict, f: int):
    ac, hp = hero_at(f)
    p = pool(defs, f)
    tot = sum(p.values()) or 1.0
    hps, turns = [], []
    blow = turn = power = opener = 0.0
    for k, w in p.items():
        m = defs[k]
        one, t = turn_damage(m)
        hit = min(0.95, max(0.05, (21 - (int(m.get('thac0', 20) if m.get('thac0') is not None else 20) - ac)) / 20.0))
        hps.append((dice_mean(m.get('hp')), w))
        ts = hit * t / hp
        turns.append((ts, w))
        blow += w * one / hp
        turn += w * ts
        power += w * (1.0 if has_power(m) else 0.0)
        opener += w * (1.0 if m.get('opener') else 0.0)
    return dict(floor=f, kinds=len(p), hero_hp=hp, hero_ac=ac,
                hp_med=wpct(hps, 0.5), anchor=floor_curve.target_hp(f),
                blow=blow / tot, turn=turn / tot,
                p10=wpct(turns, 0.1), p90=wpct(turns, 0.9),
                power=power / tot, opener=opener / tot, pool=p)


def parse_floors(s: str):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--over', nargs='*', default=[])
    ap.add_argument('--floors', default='1,2,3,4,5,6,7,8,9,10,12,14,16,18,20,23,26,30,35,40,45,'
                                        '50,55,60,65,70,75,80,85,90,95,99')
    ap.add_argument('--kinds', type=int, default=0)
    args = ap.parse_args(argv)
    defs = load(args.over)
    print('floor kinds heroHP heroAC  hp_med/anchor  blow%  turn%  p10-p90 turn%  power  opener')
    for f in parse_floors(args.floors):
        r = floor_row(defs, f)
        print(f"{f:5d} {r['kinds']:5d} {r['hero_hp']:6.0f} {r['hero_ac']:6.1f}  "
              f"{r['hp_med']:6.0f}/{r['anchor']:<5.0f}{r['hp_med'] / r['anchor']:4.2f}  "
              f"{100 * r['blow']:5.1f}  {100 * r['turn']:5.1f}  "
              f"{100 * r['p10']:5.1f}-{100 * r['p90']:<5.1f}  {100 * r['power']:4.0f}%  {100 * r['opener']:4.0f}%")
        if args.kinds:
            tot = sum(r['pool'].values()) or 1.0
            ac, hp = r['hero_ac'], r['hero_hp']
            for k, w in sorted(r['pool'].items(), key=lambda kv: -kv[1])[:args.kinds]:
                m = defs[k]
                one, t = turn_damage(m)
                hit = min(0.95, max(0.05, (21 - (int(m.get('thac0', 20) if m.get('thac0') is not None else 20) - ac)) / 20.0))
                print(f"        {100 * w / tot:4.1f}%  {k:<28} hp {dice_mean(m.get('hp')):6.0f}  "
                      f"blow {100 * one / hp:5.1f}%  turn {100 * hit * t / hp:5.1f}%  hit {100 * hit:3.0f}%")
    return 0


if __name__ == '__main__':
    sys.exit(main())
