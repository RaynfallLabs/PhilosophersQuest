"""The defence model (Brandon, 2026-11-16): armour class, dodge, speed and
the load, as pure sums over numbers. Every number is data
(data/gear_rules.json `defence` and `load`); Player.get_ac, dodge_chance,
get_speed and load_tier are the readers, and the simulator plays them
(tools/balance/difficulty_sim.py).

* Armour class comes from armour, the shield and magic only. Dexterity
  gives none (it gave up to 6 points in light armour until 2026-11-16, and a
  nimble hero in studded leather out-armoured full plate deep down).
* Dodge: a natural chance to slip a blow, from Dexterity, `dodge_per_dex` a
  point over 10, at most `dodge_cap`. The body armour's weight class leaves
  all of it, half or none (armour_weight.dodge_share), and the load a share
  of what is left (load.<tier>.dodge).
* Speed: how often the hero acts against the world, on the scale of a
  monster's `speed` (10 is ordinary). Dexterity adds `speed_per_dex` a point
  over 10, at most `speed_cap`, and the body armour's weight class leaves
  all of that quickness, half or none (`speed_share`, as the dodge: a
  nimble hero in plate is no quicker for it). Medium and heavy body armour
  drag the speed (`armour_drag`), and Strength pays the drag back,
  `str_payback` a point over 10: a hero strong enough for his plate is at
  10, a weak one in it is slower. The load drags too (load.<tier>.speed).
  Speed boots and haste multiply what this gives (Player.get_speed). Every
  monster's damage was sized for a hero at speed 10: only armour too heavy
  for the hero's Strength and a load he chose to carry take him under it,
  and only Dexterity in light (or half of it in medium) armour, boots and
  haste take him over.
* The load: shares of the carry limit (Strength's, plus a little from
  Constitution over 10, `con_carry` a point). Light over half (a little
  less dodge), Heavy over 70% (half the dodge and slower), Burdened over 90%
  (no dodge and much slower), Overloaded past the limit itself, which stays
  a wall: nothing more can be picked up.

Pure: no pygame, no game state, no player. Rules default to the JSON file
and can be handed in (the simulator's tuning sweeps do).
"""
from __future__ import annotations

import math

# The load tiers from the lightest, '' being under the first line.
LOAD_TIERS = ('', 'light', 'heavy', 'burdened', 'overloaded')
LOAD_WORDS = {'light': 'Light', 'heavy': 'Heavy', 'burdened': 'Burdened',
              'overloaded': 'Overloaded'}
WEIGHT_CLASSES = ('light', 'medium', 'heavy')

_DEFAULTS = {
    'dodge_per_dex': 0.0125, 'dodge_cap': 0.40,
    'speed_per_dex': 0.01, 'speed_cap': 0.20,
    'speed_share': {'light': 1.0, 'medium': 0.5, 'heavy': 0.0},
    'armour_drag': {'light': 0.0, 'medium': 0.06, 'heavy': 0.12},
    'str_payback': 0.02,
    'con_carry': 3,
    'min_speed_share': 0.25,
}
_LOAD_DEFAULTS = {
    'light': {'share': 0.5, 'dodge': 0.75, 'speed': 0.0},
    'heavy': {'share': 0.7, 'dodge': 0.5, 'speed': 0.10},
    'burdened': {'share': 0.9, 'dodge': 0.0, 'speed': 0.25},
    'overloaded': {'dodge': 0.0, 'speed': 0.5},
}


_CACHE: dict = {}


def _json_block(name: str) -> dict:
    try:
        import gear
        return dict(gear.rules().get(name) or {})
    except Exception:
        return {}


def rules() -> dict:
    """The `defence` block of data/gear_rules.json, over the defaults (read
    once; `override` changes it for a tuning sweep)."""
    r = _CACHE.get('defence')
    if r is None:
        r = dict(_DEFAULTS)
        r.update({k: v for k, v in _json_block('defence').items() if not k.startswith('_')})
        _CACHE['defence'] = r
    return r


def load_rules() -> dict:
    """The `load` block of data/gear_rules.json, tier by tier, over the
    defaults."""
    lr = _CACHE.get('load')
    if lr is None:
        lr = {k: dict(v) for k, v in _LOAD_DEFAULTS.items()}
        for tier, row in _json_block('load').items():
            if tier in lr and isinstance(row, dict):
                lr[tier].update({k: v for k, v in row.items() if not k.startswith('_')})
        _CACHE['load'] = lr
    return lr


def override(defence: dict | None = None, load: dict | None = None) -> None:
    """Change the rules in this process (the simulator's tuning knobs):
    `defence` keys over the `defence` block, `load` {tier: {key: value}}
    over the load tiers. `reset()` goes back to the file."""
    if defence:
        r = dict(rules())
        for k, v in defence.items():
            r[k] = dict(r[k], **v) if isinstance(v, dict) and isinstance(r.get(k), dict) else v
        _CACHE['defence'] = r
    if load:
        lr = {k: dict(v) for k, v in load_rules().items()}
        for tier, row in load.items():
            lr.setdefault(tier, {}).update(row)
        _CACHE['load'] = lr


def reset() -> None:
    _CACHE.clear()


def _over(stat) -> int:
    try:
        return max(0, int(stat) - 10)
    except (TypeError, ValueError):
        return 0


# ------------------------------------------------------------------- dodge

def dex_dodge(dex, r: dict | None = None) -> float:
    """Dexterity's dodge before armour and load: a share a point over 10,
    capped. 0 at DEX 10 or under."""
    r = r or rules()
    return min(float(r['dodge_cap']), _over(dex) * float(r['dodge_per_dex']))


# ------------------------------------------------------------------- speed

def dex_speed(dex, r: dict | None = None) -> float:
    """The share of speed Dexterity adds before the armour (0.1 = a tenth
    quicker)."""
    r = r or rules()
    return min(float(r['speed_cap']), _over(dex) * float(r['speed_per_dex']))


def class_speed_share(weight_class: str, r: dict | None = None) -> float:
    """How much of Dexterity's quickness this body armour leaves: all in
    light armour, half in medium, none in heavy (`speed_share`)."""
    r = r or rules()
    return float((r.get('speed_share') or {}).get(str(weight_class or 'light'), 1.0))


def armour_speed(dex, weight_class: str, r: dict | None = None) -> float:
    """Dexterity's quickness as this body armour leaves it."""
    r = r or rules()
    return dex_speed(dex, r) * class_speed_share(weight_class, r)


def armour_drag(weight_class: str, strength, r: dict | None = None) -> float:
    """What the body armour's weight costs in speed after Strength's
    payback: never under 0 (Strength never makes armour quicker)."""
    r = r or rules()
    drag = float((r.get('armour_drag') or {}).get(str(weight_class or 'light'), 0.0))
    return max(0.0, drag - _over(strength) * float(r['str_payback']))


def fit_strength(weight_class: str, r: dict | None = None) -> int:
    """The Strength at which this weight class costs no speed (10 for light
    armour or a class with no drag)."""
    r = r or rules()
    drag = float((r.get('armour_drag') or {}).get(str(weight_class or 'light'), 0.0))
    pay = float(r['str_payback'])
    if drag <= 0.0 or pay <= 0.0:
        return 10
    return 10 + int(math.ceil(drag / pay - 1e-9))


def load_speed_drag(tier: str, lr: dict | None = None) -> float:
    lr = lr or load_rules()
    return float((lr.get(tier) or {}).get('speed', 0.0)) if tier else 0.0


def speed_share(dex, strength, weight_class: str, tier: str = '', *,
                ignore_load: bool = False, r: dict | None = None,
                lr: dict | None = None) -> float:
    """1 + Dexterity's share (what the armour leaves of it) - the armour's
    unpaid drag - the load's, never under `min_speed_share`. `ignore_load`:
    Marius' Mule, whose stride the load does not shorten (Overloaded still
    does)."""
    r = r or rules()
    s = 1.0 + armour_speed(dex, weight_class, r) - armour_drag(weight_class, strength, r)
    if not (ignore_load and tier in ('light', 'heavy', 'burdened')):
        s -= load_speed_drag(tier, lr)
    return max(float(r['min_speed_share']), s)


def speed_rating(share: float, quickness: float = 0.0, hasted: bool = False) -> float:
    """The speed on the monsters' scale: 10 x the share, Speed boots'
    quickness on top, haste doubling it."""
    s = 10.0 * float(share) * (1.0 + float(quickness or 0.0))
    if hasted:
        s *= 2.0
    return round(s, 2)


def world_turns(clock: float, speed: float) -> tuple:
    """Game._advance_turn's rule: each action moves the world's clock on by
    10/speed of a turn; the world takes a turn for every whole turn the
    clock passes. Returns (world turns now, the clock left). At speed 10
    exactly the clock stays clean (one action, one turn); over 10 the world
    sometimes waits; under 10 it sometimes takes two turns."""
    speed = max(1.0, float(speed))
    c = float(clock or 0.0) + 10.0 / speed
    n = int(c + 1e-9)
    c -= n
    if abs(speed - 10.0) < 1e-9:
        c = 0.0
    return n, max(0.0, c)


# -------------------------------------------------------------------- load

def carry_limit(strength, constitution, base: int, per_str: int,
                r: dict | None = None) -> int:
    """Strength's carry, plus `con_carry` a point of Constitution over 10."""
    r = r or rules()
    return int(base + int(strength) * per_str + _over(constitution) * int(r.get('con_carry', 0)))


def load_lines(lr: dict | None = None) -> tuple:
    """The shares of the limit where the load changes tier (Light, Heavy,
    Burdened); the limit itself is Overloaded."""
    lr = lr or load_rules()
    return tuple(float(lr[t]['share']) for t in ('light', 'heavy', 'burdened'))


def load_tier(weight: float, limit: float, lr: dict | None = None) -> str:
    """'', 'light', 'heavy', 'burdened' or 'overloaded' for this weight."""
    wt, lim = float(weight), float(limit)
    if wt > lim:
        return 'overloaded'
    light, heavy, burdened = load_lines(lr)
    if wt > lim * burdened:
        return 'burdened'
    if wt > lim * heavy:
        return 'heavy'
    if wt > lim * light:
        return 'light'
    return ''


def load_dodge_share(tier: str, lr: dict | None = None) -> float:
    """The share of the dodge the load leaves."""
    if not tier:
        return 1.0
    lr = lr or load_rules()
    return float((lr.get(tier) or {}).get('dodge', 1.0))


def tier_rank(tier: str) -> int:
    """0 for no load tier, 4 for Overloaded; an unknown tier (an old save's
    'stressed') counts as none."""
    return LOAD_TIERS.index(tier) if tier in LOAD_TIERS else 0
