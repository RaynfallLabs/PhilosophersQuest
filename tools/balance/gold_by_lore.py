#!/usr/bin/env python
"""Monster gold by lore, not by kill (ECONOMY_REFACTOR_PROPOSAL D1).

Before this, 561 of 573 monsters carried coins and killing paid 80-85% of
all gold: a giant rat, a bear and a chimera each dropped a purse. A wolf has
no purse. This script decides what each creature carries from what it IS,
and writes it into data/monsters.json as real numbers (LORE NOT FLOOR: the
game never multiplies gold by the floor at runtime; the amount for a
creature's depth is baked in here, like tools/balance/scale_monsters.py does
for health).

What a creature carries (``treasure.purse`` records which rule applied):

  none        beasts, vermin, oozes, plants, constructs, elementals, spirits
              and the incorporeal dead, most demons. Their worth is the hide
              and the cuts (harvest and cooking), or nothing at all.
  purse       people: humanoids, goblins, orcs, kobolds, gnolls, trolls.
  thief       bandits, brigands, thieves, assassins: a fat purse.
  scholar     casters among the living: coin for ink and reagents.
  sack        giants: a sack over the shoulder.
  grave_goods the walking dead that were buried with something.
  noble_dead  vampires and liches: old money.
  trinkets    fey: a few bright things.
  pot         leprechauns: the pot of gold.
  hoard       dragons: the bed of coins they sleep on (by age).
  tempter     a demon who buys souls with gold (incubus, succubus).
  leader      x2 on any of the above for a king, chief, captain, lord...
  kept        named one-offs, bosses, seal demons and special spawns
              (peak_weight 0 or frequency 0): left exactly as written. A
              named beast's gold is its lair: the bones of those it ate.

Amounts are a share of one floor's income (economy.floor_income) at the
creature's peak floor, rolled between half and one and a half of the share.
Run from the repo root:

    py tools/balance/gold_by_lore.py            # rewrite data/monsters.json
    py tools/balance/gold_by_lore.py --report   # print the table, write nothing
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
import economy  # noqa: E402

PATH = os.path.join(REPO, 'data', 'monsters.json')

# Mean share of one floor's income, by what the creature is.
SHARE = {
    'none': 0.0,
    'purse': 0.045,
    'thief': 0.14,
    'scholar': 0.08,
    'sack': 0.10,
    'grave_goods': 0.03,
    'noble_dead': 0.09,
    'trinkets': 0.025,
    'pot': 0.40,
    'hoard': 0.35,
    'tempter': 0.06,
}
LEADER_MULT = 2.0
# A dragon's bed and a leprechaun's pot: rare paydays, weighted more than one
# purse in a crowd at any depth (measured: full weight made dragons a quarter
# of all deep gold).
HOARD_WEIGHT = 0.4
# Deep floors hold far more people per floor than shallow ones (bigger
# rooms, packs, wanderers), so each one carries a smaller share of the
# floor's income. Measured with tools/balance/gold_sim.py so that kills pay
# about a third of a floor's gold at every depth; linear between the points.
DEPTH_WEIGHT = ((1, 1.6), (5, 1.5), (10, 1.2), (15, 0.8), (25, 0.3), (35, 0.16),
                (45, 0.17), (55, 0.15), (65, 0.14), (75, 0.17), (85, 0.22), (100, 0.22))


def depth_weight(floor: int) -> float:
    pts = DEPTH_WEIGHT
    if floor <= pts[0][0]:
        return pts[0][1]
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= floor <= b:
            return wa + (wb - wa) * (floor - a) / (b - a)
    return pts[-1][1]
SPREAD = (0.5, 1.5)            # gold = [share x 0.5, share x 1.5] of income

NO_COIN_TAGS = {'beast', 'plant', 'construct', 'elemental'}
PEOPLE_TAGS = {'humanoid', 'goblinoid', 'goblin', 'orc', 'kobold', 'gnoll', 'troll', 'bandit',
               'cultist'}
# The dead with no body to bury anything with.
INCORPOREAL = ('ghost', 'spectre', 'specter', 'wraith', 'shade', 'shadow', 'phantom',
               'poltergeist', 'banshee', 'wisp', 'echo', 'presence', 'spirit', 'haunting',
               'allip', 'soul', 'fetch', 'nightmare')
THIEF_WORDS = ('bandit', 'brigand', 'thief', 'assassin', 'filcher', 'autolycus', 'kingpin',
               'pirate', 'raider')
LEADER_WORDS = ('king', 'chief', 'captain', 'warlord', 'warchief', 'lord', 'jarl', 'marshal',
                'kingpin', 'priestess', 'hierophant', 'sovereign', 'emperor', 'patriarch',
                'champion', 'alpha')
DRAGON_AGE = (('ancient', 1.6), ('elder', 1.3), ('adult', 1.0), ('young', 0.5),
              ('drake', 0.15), ('wyvern', 0.15), ('lindworm', 0.2), ('brood', 0.2),
              ('spawn', 0.25), ('wyrm', 0.6))


def special(m: dict) -> bool:
    """A named one-off, a boss or a scripted spawn: not an ordinary roll."""
    tags = set(m.get('tags') or ())
    return (m.get('peak_weight') in (0, 0.0) or m.get('frequency') == 0
            or bool(tags & {'boss', 'legendary'}))


def purse_kind(mid: str, m: dict) -> str:
    """Which rule decides what this creature carries."""
    if special(m):
        return 'kept'
    tags = set(m.get('tags') or ())
    name = f"{mid} {m.get('name', '')}".lower()
    if 'leprechaun' in name:
        return 'pot'
    if 'dragon' in tags and 'undead' not in tags:
        return 'hoard'
    if 'construct' in tags:
        return 'none'
    if 'undead' in tags:
        if any(w in name for w in INCORPOREAL):
            return 'none'
        if 'vampire' in name or 'lich' in name or 'nosferatu' in name or 'dracolich' in name:
            return 'noble_dead'
        if 'caster' in tags or 'necromancer' in name:
            return 'scholar'
        if 'humanoid' in tags or 'giant' in tags:
            return 'grave_goods'
        if 'beast' in tags:
            return 'none'                 # a dead hound has no purse either
        return 'grave_goods'
    if 'giant' in tags and 'humanoid' in tags:
        return 'sack'
    if tags & PEOPLE_TAGS or ('caster' in tags and not tags & {'demon'}):
        if 'bandit' in tags or any(w in name for w in THIEF_WORDS):
            return 'thief'
        if 'caster' in tags:
            return 'scholar'
        return 'purse'
    if 'demon' in tags:
        if 'incubus' in name or 'succubus' in name:
            return 'tempter'
        return 'none'
    if 'fey' in tags:
        return 'trinkets'
    if tags & NO_COIN_TAGS:
        return 'none'
    return 'none'          # aberrations, celestials, outsiders: no coin


def gold_for(mid: str, m: dict, kind: str) -> list:
    share = SHARE.get(kind, 0.0)
    if share <= 0:
        return [0, 0]
    name = f"{mid} {m.get('name', '')}".lower()
    if kind == 'hoard':
        share *= next((mult for word, mult in DRAGON_AGE if word in name), 0.6)
    elif any(w in name for w in LEADER_WORDS):
        share *= LEADER_MULT
    peak = int(m.get('peak_floor') or m.get('min_level') or 1)
    # A dragon's bed of gold and a leprechaun's pot are rare paydays, not
    # one purse among a crowd: one fixed weight at any depth (HOARD_WEIGHT).
    weight = HOARD_WEIGHT if kind in ('hoard', 'pot') else depth_weight(peak)
    inc = economy.floor_income(peak) * weight
    lo = max(1, int(round(inc * share * SPREAD[0])))
    hi = max(lo + 1, int(round(inc * share * SPREAD[1])))
    return [lo, hi]


def main(argv):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    report = '--report' in argv
    counts = {}
    for mid, m in data.items():
        kind = purse_kind(mid, m)
        counts[kind] = counts.get(kind, 0) + 1
        tr = m.setdefault('treasure', {})
        if kind == 'kept':
            tr['purse'] = 'kept'
            continue
        new = gold_for(mid, m, kind)
        if report:
            print(f"{mid:32} {kind:12} {tr.get('gold')} -> {new}")
        tr['gold'] = new
        tr['purse'] = kind
    print(counts)
    if not report:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print('wrote', PATH)


if __name__ == '__main__':
    main(sys.argv)
