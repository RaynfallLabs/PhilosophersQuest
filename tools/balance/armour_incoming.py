"""What armour's forms and elements do to the damage a hero takes, by depth.

Winning-build plan 3.3, slice 4 (2026-11-13). The body armour's template
now turns or lets through slash / pierce / blunt, and its material the
elements (src/gear.py, "What armour does beyond AC"). THAC0 and the monster
numbers were NOT re-baked in that slice; this measures the change for the
lead's balance slice.

For each floor:

* the ATTACK MIX is the game's own spawn pool (dungeon._build_spawn_pool:
  bells, lore floors, domain kin), every attack weighted by its kind's spawn
  share and its average damage;
* the PAR KIT is the body armour a hero wears there, found the way the THAC0
  line was measured (tools/balance/rebake_thac0.py: the loot census, the
  game's own pick_random_armor_for_floor, the best AC kept);
* the number is the damage-weighted mean of gear.piece_profile over the
  attack mix: 1.00 is what the same blows did under the 3.3.2 rule (the
  material never protected).

It also prints four fixed kits (padded linen, leather, ring-iron chainmail,
chain-steel plate) and what the weight-class rules take off a DEX hero's
AC and dodge (to-hit is d20 against THAC0 - AC: one point of AC is 5
points of a monster's hit chance).

    py tools/balance/armour_incoming.py [--runs 200] [--seed 3]
"""
from __future__ import annotations

import argparse
import os
import random
import re
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

FLOORS = (1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100)
SPLIT = {'weapon': 0.45, 'armour': 0.45, 'shield': 0.10}
SHARE_FOUND = 0.90
_DICE = re.compile(r'^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$')


def avg_damage(spec) -> float:
    """The mean of a dice string ("2d6+3"), or of a plain number."""
    s = str(spec)
    m = _DICE.match(s)
    if m:
        n = int(m.group(1) or 1)
        sides = int(m.group(2))
        bonus = int((m.group(3) or '0').replace(' ', ''))
        return n * (sides + 1) / 2 + bonus
    try:
        return float(s)
    except ValueError:
        return 0.0


def attack_mix(floor: int) -> dict:
    """{damage type: share of the expected damage} on `floor`."""
    from dungeon import _build_spawn_pool
    pool = _build_spawn_pool(floor)
    tot = sum(v['_spawn_freq'] for v in pool.values()) or 1.0
    mix = {}
    for v in pool.values():
        w = v['_spawn_freq'] / tot
        atks = v.get('attacks') or []
        for a in atks:
            d = avg_damage(a.get('damage', '1d4'))
            t = str(a.get('type', 'physical'))
            mix[t] = mix.get(t, 0.0) + w * d / max(1, len(atks))
    s = sum(mix.values()) or 1.0
    return {k: v / s for k, v in mix.items()}


def factor(item, mix: dict) -> float:
    import gear
    prof = gear.piece_profile(item) if item is not None else {}
    return sum(share * prof.get(t, 1.0) for t, share in mix.items())


def par_kits(runs: int, seed: int) -> dict:
    """{floor: [the body armour worn, one per run]} (None: nothing yet)."""
    import items
    from armor_model import load_census, _poisson
    census = load_census(None)
    rng = random.Random(seed)
    slots = list(items.ARMOR_SLOTS)
    out = {f: [] for f in FLOORS}
    for _ in range(runs):
        body, best = None, 0
        for f in range(1, 101):
            for _i in range(_poisson(rng, census[f][0] * SHARE_FOUND)):
                r = rng.random()
                if r < SPLIT['weapon'] + SPLIT['shield']:
                    continue
                if rng.choice(slots) != 'body':
                    continue
                a = items.pick_random_armor_for_floor(f, rng, slot='body')
                if a is not None and a.ac_bonus + a.enchant_bonus > best:
                    body, best = a, a.ac_bonus + a.enchant_bonus
            if f in out:
                out[f].append(body)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=200)
    ap.add_argument('--seed', type=int, default=3)
    args = ap.parse_args(argv)
    import gear
    import items
    kits = par_kits(args.runs, args.seed)
    fixed = {
        'padded linen': items.instantiate_armor('padded', 'linen'),
        'leather': items.instantiate_armor('leather', 'leather'),
        'iron mail': items.instantiate_armor('chainmail', 'ring_iron'),
        'steel plate': items.instantiate_armor('plate', 'chain_steel'),
    }
    print("Incoming damage under the new armour profiles, as a share of the 3.3.2 rule")
    print("(1.00 = unchanged; < 1 the armour takes more off, > 1 it lets more through)\n")
    head = (f"{'F':>3}  {'slash':>5} {'pierce':>6} {'blunt':>5} {'elem':>5}  "
            f"{'par kit':>7} {'(sd)':>5}  {'light':>5} {'med':>4} {'heavy':>5} {'metal':>5}  "
            + '  '.join(f"{k:>12}" for k in fixed))
    print(head)
    for f in FLOORS:
        mix = attack_mix(f)
        worn = kits[f]
        fs = [factor(a, mix) for a in worn]
        cls = [gear.piece_weight_class(a) if a is not None else 'none' for a in worn]
        n = len(worn) or 1
        light = sum(1 for c in cls if c in ('light', 'none')) / n
        med = cls.count('medium') / n
        heavy = cls.count('heavy') / n
        metal = sum(1 for a in worn if a is not None and gear.is_metal(a)) / n
        elem = 1.0 - sum(mix.get(k, 0.0) for k in ('slash', 'pierce', 'blunt', 'physical'))
        row = (f"{f:>3}  {mix.get('slash', 0):>5.2f} {mix.get('pierce', 0):>6.2f} "
               f"{mix.get('blunt', 0):>5.2f} {elem:>5.2f}  "
               f"{statistics.mean(fs):>7.3f} {statistics.pstdev(fs):>5.3f}  "
               f"{light:>5.2f} {med:>4.2f} {heavy:>5.2f} {metal:>5.2f}  "
               + '  '.join(f"{factor(a, mix):>12.3f}" for a in fixed.values()))
        print(row)
    print("\nWhat the weight class takes from a DEX hero (vs the old cap of 3 in anything):")
    print("(AC: the points of armour Dexterity gives now, minus what it gave; dodge: what is left)")
    print(f"{'DEX':>4} {'mod':>4}   {'AC light':>8} {'medium':>6} {'heavy':>6}   "
          f"{'dodge light':>11} {'medium':>6} {'heavy':>6}")
    caps = gear.armour_rules()['dex_ac_cap']
    shares = gear.armour_rules()['dodge_share']
    for dex in (10, 12, 14, 16, 18, 20, 22):
        mod = (dex - 10) // 2
        old = min(3, mod)
        delta = [min(caps[c], mod) - old for c in ('light', 'medium', 'heavy')]
        dodge = min(0.30, max(0, dex - 10) * 0.0075)
        print(f"{dex:>4} {mod:>+4}   {delta[0]:>+8} {delta[1]:>+6} {delta[2]:>+6}   "
              f"{dodge * shares['light']:>10.1%} {dodge * shares['medium']:>6.1%} "
              f"{dodge * shares['heavy']:>6.1%}")
    print("\n(An AC point is 5 points of a monster's hit chance: at the ~55% par, a heavy-armour")
    print(" hero of DEX 14 who loses 2 AC is hit about 65% of the time, +18% damage taken;")
    print(" one who lost 3.75% dodge takes about 4% more.)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
