"""
What every damaging spell and wand does, against the yardsticks.

Offline tooling (not loaded at runtime).

    py tools/balance/magic_audit.py

Magic as a style (winning-build plan 3.6, Brandon's decision 5, 2026-11-13;
it replaced ruling D2 of REBALANCE_MASTER_PLAN.md, which held every cast
under one weapon attack). Maths stays the backbone: every cast is one
science question (wrong is a fizzle), a mana bar holds a few casts, metal
body armour taxes them, and a caster still finishes the fight with a weapon.
Magic is the toolkit that exploits elements and controls the fight: the
best single-target spell of each tier lands about ONE weapon chain
(floor_curve.one_attack) on a floor typical of its tier for an ordinary
character, about 1.25 for an Intelligence build, so the right element on a
x2 weakness is a two-chain blow. Area spells sit under a bolt; a touch spell
keeps a small edge for the risk of laying hands on; a wand charge is about
0.85.

This prints, for each damaging spell and wand, its ROLE (bolt, touch,
undead, area, share), its damage as a share of ONE ATTACK on a floor typical
of its tier for INT 10 and for a dedicated Intelligence build, and how many
casts a mana bar holds; then, by tier, the best single-target spell, the
best bolt and area spell, the casts a bar (in light armour and in steel
plate) and the mana a floor's meditation gives back. tests/test_magic_role.py
holds the bands below.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

TIER_FLOOR = {1: 10, 2: 30, 3: 50, 4: 70, 5: 90}       # a floor typical of each tier
# Effects that strike everything in sight, or arc on to more foes.
AREA = ('mass_', 'meteor', 'storm', 'cone', 'chain_lightning')
# Effects that only bite one kind of foe (the undead): allowed a little more.
CONDITIONAL = ('turn_undead', 'sunlight')
# Effects whose harm is a share of the foe's own health, not their dice
# (Annihilation: the end of anything under 35%, a third of the rest).
SHARE = ('annihilate',)

# The bands, x one attack: (INT 10, INT build). A spell over either is out.
BANDS = {
    'bolt':        (1.05, 1.45),     # one target, any reach but a touch
    'touch':       (1.15, 1.45),     # laid on a foe beside you (spells.REACH_TOUCH)
    'undead':      (1.15, 1.45),     # Turn Undead, Sunburst: every undead in sight
    'area':        (0.95, 1.30),     # everything in sight: under a bolt
    'wand':        (0.92, 1.12),     # a charge, not a spell
    'wand_undead': (1.10, 1.35),
}
# Each tier's best single-target spell (a bolt or a touch), at INT 10.
BEST_SINGLE = (0.95, 1.15)
# Each tier's best bolt, at INT 10. Tier 4 has no ordinary bolt (Force Storm
# is the force family's quiet place); its single target is Soul Drain.
BEST_BOLT = (0.95, 1.05)
BOLT_TIERS = (1, 2, 3, 5)

_DICE = re.compile(r'(\d*)d(\d+)([+-]\d+)?')


def dice_mean(expr) -> float:
    """The exact mean of a dice string ('3d6+2' is 12.5); 0 for anything
    else (a wand's plain-number duration)."""
    m = _DICE.fullmatch(str(expr or '').strip().lower().replace(' ', ''))
    if not m:
        return 0.0
    n = int(m.group(1) or 1)
    return n * (int(m.group(2)) + 1) / 2.0 + int(m.group(3) or 0)


def build_int(floor: int) -> int:
    """Intelligence of a dedicated caster on `floor`: 10, plus the cooking
    cap, plus the gate gifts that offer it (Asterion +4, Fenrir +7)."""
    from player import Player
    p = Player()
    p.deepest_floor_reached = floor
    return 10 + p.cooking_stat_softcap('INT') + (4 if floor > 20 else 0) + (7 if floor > 80 else 0)


def role_of(effect, reach=None, kind: str = 'spell') -> str:
    """What a damaging effect is, for its band."""
    eff = str(effect or '')
    if any(s in eff for s in SHARE):
        return 'share'
    if any(c in eff for c in CONDITIONAL):
        return 'undead' if kind == 'spell' else 'wand_undead'
    if kind != 'spell':
        return 'wand'
    from spells import REACH_TOUCH
    if reach is not None and reach <= REACH_TOUCH:
        return 'touch'
    if any(a in eff for a in AREA):
        return 'area'
    return 'bolt'


def _base_mp() -> int:
    from player import Player
    return int(getattr(Player, 'BASE_MP', 10))


def rows() -> list[dict]:
    """One row per damaging spell and wand: kind, name, tier, cost (MP, or a
    wand's charges), role, area, plain and mage (x one attack at INT 10 and
    for the build), and casts (a bar's worth for the build; a wand's floor)."""
    import floor_curve
    import game_magic
    from spells import LEARNABLE_SPELLS, spell_reach
    out = []
    for sid, s in LEARNABLE_SPELLS.items():
        base = dice_mean(s.get('power'))
        if base <= 0 or s['effect'] in ('extra_heal',):
            continue
        tier = int(s.get('tier', 1))
        floor = TIER_FLOOR[tier]
        mult = game_magic.MAGIC_TIER_MULT[tier]
        one = floor_curve.one_attack(floor)
        bint = build_int(floor)
        out.append({
            'kind': 'spell', 'name': sid.replace('_spell', ''), 'tier': tier,
            'cost': int(s['mp_cost']),
            'role': role_of(s['effect'], spell_reach(s) if s.get('needs_target') else None),
            'area': any(a in s['effect'] for a in AREA),
            'plain': base * mult * game_magic.int_damage_factor(10) / one,
            'mage': base * mult * game_magic.int_damage_factor(bint) / one,
            'casts': (_base_mp() + bint) // max(1, int(s['mp_cost'])),
        })
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
        out.append({
            'kind': 'wand', 'name': wid, 'tier': tier,
            'cost': int(w.get('charges_max') or w.get('max_charges') or 0),
            'role': role_of(w.get('effect'), kind='wand'),
            'area': any(a in str(w.get('effect')) for a in AREA),
            'plain': base * mult * game_magic.int_damage_factor(10) / one,
            'mage': base * mult * game_magic.int_damage_factor(build_int(floor)) / one,
            'casts': floor,
        })
    return out


def out_of_band(rs=None) -> list:
    """Every row over its role's band: (kind, name, role, plain, mage)."""
    over = []
    for r in (rs if rs is not None else rows()):
        band = BANDS.get(r['role'])
        if band and (r['plain'] > band[0] + 1e-9 or r['mage'] > band[1] + 1e-9):
            over.append((r['kind'], r['name'], r['role'], round(r['plain'], 2), round(r['mage'], 2)))
    return over


def tier_summary(rs=None) -> dict:
    """By tier: the best single-target spell (bolt or touch), the best bolt
    and the best area spell (name, x one attack at INT 10, for the build),
    the casts a bar holds of the best single-target spell (INT 10, the build,
    the build in steel plate at x2), and a floor's meditation (MP at INT 10
    and for the build: floor_curve.meditation_allowance)."""
    import floor_curve
    spells = [r for r in (rs if rs is not None else rows()) if r['kind'] == 'spell']
    out = {}
    for tier, floor in TIER_FLOOR.items():
        mine = [r for r in spells if r['tier'] == tier]

        def best(roles):
            pick = [r for r in mine if r['role'] in roles]
            r = max(pick, key=lambda r: r['plain']) if pick else None
            return (r['name'], r['plain'], r['mage'], r['cost']) if r else None

        bint = build_int(floor)
        single = best(('bolt', 'touch'))
        cost = single[3] if single else 1
        plain_mp, build_mp = _base_mp() + 10, _base_mp() + bint
        out[tier] = {
            'floor': floor, 'build_int': bint,
            'single': single, 'bolt': best(('bolt',)), 'area': best(('area',)),
            'casts': (plain_mp // cost, build_mp // cost, build_mp // (2 * cost)),
            'meditation': (floor_curve.meditation_allowance(plain_mp, 10),
                           floor_curve.meditation_allowance(build_mp, bint)),
        }
    return out


def main() -> int:
    rs = rows()
    over = {(k, n) for k, n, *_ in out_of_band(rs)}
    print("kind   name                      tier  mp/chg  role          x ONE ATTACK (INT 10)   (INT build)   casts per bar / floor")
    for r in sorted(rs, key=lambda r: (r['kind'], r['tier'], -r['mage'])):
        flag = '  <-- over its band' if (r['kind'], r['name']) in over else ''
        if r['role'] == 'share':
            flag = '  (a share of health, not its dice)'
        print(f"{r['kind']:6} {r['name']:25} {r['tier']:4} {r['cost']:7}  {r['role']:11} "
              f"{r['plain']:14.2f} {r['mage']:18.2f} {r['casts']:14}{flag}")
    print()
    print("By tier, x one attack (INT 10 / build); casts a bar of the best single target"
          " (INT 10 / build / build in steel plate); MP a floor's meditation gives (INT 10 / build)")
    print("tier floor INT  best single target          best bolt                   "
          "best area                   casts         meditation")

    def cell(c):
        return f"{c[0]:16} {c[1]:4.2f}/{c[2]:4.2f}" if c else f"{'-':26}"

    for tier, t in tier_summary(rs).items():
        print(f"{tier:4} {t['floor']:5} {t['build_int']:3}  {cell(t['single'])}  {cell(t['bolt'])}  "
              f"{cell(t['area'])}  {t['casts'][0]:2}/{t['casts'][1]:2}/{t['casts'][2]:2}      "
              f"{t['meditation'][0]:3}/{t['meditation'][1]:3} MP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
