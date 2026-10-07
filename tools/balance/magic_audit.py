"""
What every damaging spell and wand does, against the yardsticks.

Offline tooling (not loaded at runtime).

    python tools/balance/magic_audit.py

Decision D2 of REBALANCE_MASTER_PLAN.md: magic changes the shape of a fight
and never replaces maths. So one cast at a single target should land BELOW
one weapon attack on the floors where the spell is found, for a plain
character and for a dedicated Intelligence build alike. This prints, for
each damaging spell and wand, its damage as a share of ONE ATTACK
(floor_curve.one_attack) on a floor typical of its tier, and how many casts
a mana bar holds.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

TIER_FLOOR = {1: 10, 2: 30, 3: 50, 4: 70, 5: 90}       # a floor typical of each tier
AREA = ('mass_', 'meteor', 'storm', 'cone', 'chain_lightning', 'aard')
# Effects that only bite one kind of foe (the undead, the wicked): allowed more.
CONDITIONAL = ('turn_undead', 'smite', 'sunlight')


def dice_mean(expr) -> float:
    from dice import roll
    if not expr:
        return 0.0
    try:
        return sum(roll(str(expr)) for _ in range(400)) / 400.0
    except Exception:
        return 0.0


def build_int(floor: int) -> int:
    """Intelligence of a dedicated caster on `floor`: 10, plus the cooking
    cap, plus the gate gifts that offer it (Asterion +4, Fenrir +7)."""
    from player import Player
    p = Player()
    p.deepest_floor_reached = floor
    return 10 + p.cooking_stat_softcap('INT') + (4 if floor > 20 else 0) + (7 if floor > 80 else 0)


def rows():
    import floor_curve
    import game_magic
    from spells import LEARNABLE_SPELLS
    out = []
    for sid, s in LEARNABLE_SPELLS.items():
        base = dice_mean(s.get('power'))
        if base <= 0 or s['effect'] in ('extra_heal',):
            continue
        tier = int(s.get('tier', 1))
        floor = TIER_FLOOR[tier]
        mult = game_magic.MAGIC_TIER_MULT[tier]
        one = floor_curve.one_attack(floor)
        plain = base * mult * game_magic.int_damage_factor(10)
        mage = base * mult * game_magic.int_damage_factor(build_int(floor))
        area = any(a in s['effect'] for a in AREA)
        out.append(('spell', sid.replace('_spell', ''), tier, s['mp_cost'], area,
                    plain / one, mage / one, (10 + build_int(floor)) // max(1, s['mp_cost'])))
    with open(ROOT / 'data' / 'items' / 'wand.json', encoding='utf-8') as f:
        wands = json.load(f)
    for wid, w in wands.items():
        if not isinstance(w, dict):
            continue
        base = dice_mean(w.get('power'))
        if base <= 0 or w.get('effect') in ('heal', 'extra_heal'):
            continue
        tier = int(w.get('tier', w.get('quiz_tier', 1)) or 1)
        floor = max(1, min(100, int(w.get('peak_floor') or w.get('min_level') or TIER_FLOOR[tier])))
        mult = game_magic.WAND_TIER_MULT[tier]
        one = floor_curve.one_attack(floor)
        out.append(('wand', wid, tier, int(w.get('charges_max') or w.get('max_charges') or 0),
                    any(a in str(w.get('effect')) for a in AREA),
                    base * mult * game_magic.int_damage_factor(10) / one,
                    base * mult * game_magic.int_damage_factor(build_int(floor)) / one, floor))
    return out


def main() -> int:
    print("kind   name                      tier  mp/chg  area   x ONE ATTACK (INT 10)   (INT build)   casts per bar / floor")
    for kind, name, tier, cost, area, plain, mage, extra in sorted(rows(), key=lambda r: (r[0], r[2], -r[6])):
        flag = '  <-- above a weapon chain' if (mage > 1.0 and not area) else ''
        # (conditional effects are listed but judged separately by the test)
        print(f"{kind:6} {name:25} {tier:4} {cost:7} {'area' if area else '    ':5} "
              f"{plain:14.2f} {mage:18.2f} {extra:14}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
