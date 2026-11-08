"""Armour, shield, ring and amulet rules (bug bash 3.3.2).

docs/design/ARMOR_REDESIGN_PLAN.md (revision 3), numbers proven by
tools/balance/armor_model.py, data in data/gear_rules.json.

  * An item is template x material x enchantment. The template says what it
    is (slot, weight class, base AC for body armour and shields), the
    material what can wear it (rust, acid, fire), its weight and its name,
    and the enchantment (level 1-10, 0 = plain) its power: the tier (quiz
    tier) and the plus on body armour and shields.
  * AC comes from body armour, the shield and DEX only.
  * The floor decides only which level is likely to be found (bells); every
    magnitude is fixed per level (LORE NOT FLOOR).

Pure rules: no pygame, no game state.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache

CORE_SLOTS = ('body',)                    # armour slots that carry AC (with the shield)
MINOR_SLOTS = ('head', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt')
MAX_LEVEL = 10


@lru_cache(maxsize=1)
def rules() -> dict:
    from paths import data_path
    with open(data_path('data', 'gear_rules.json'), encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------ levels

def tier_for_level(level: int) -> int:
    """Tier I-V of an enchantment level (a plain piece is tier 1)."""
    level = int(level or 0)
    return max(1, min(5, (level + 1) // 2)) if level > 0 else 1


def plus_for_level(level: int) -> int:
    """The plus a level gives body armour or a shield: its tier (0 plain)."""
    return tier_for_level(level) if int(level or 0) > 0 else 0


def plain_share(floor: int) -> float:
    lv = rules()['levels']
    return max(lv['plain_end'], lv['plain_start'] - lv['plain_slope'] * (int(floor) - 1))


def level_weights(floor: int) -> list:
    """Relative chance of each level 1-10 on `floor` (sums to 1)."""
    lv = rules()['levels']
    f = int(floor)
    w = []
    for i in range(MAX_LEVEL):
        if f < lv['first'][i]:
            w.append(0.0)
            continue
        d = f - lv['peak'][i]
        w.append(math.exp(-(d * d) / (2 * lv['spread'] ** 2)))
    s = sum(w) or 1.0
    return [x / s for x in w]


def roll_level(floor: int, rng, plain_ok: bool = True) -> int:
    """A found piece's level on `floor`: 0 (plain) or 1-10."""
    if plain_ok and rng.random() < plain_share(floor):
        return 0
    r, acc = rng.random(), 0.0
    for i, x in enumerate(level_weights(floor), 1):
        acc += x
        if r <= acc:
            return i
    return MAX_LEVEL


# ----------------------------------------------------------- weight classes

def weight_class(template: dict) -> str:
    """light / medium / heavy, from the template's armor_class_tier."""
    c = str((template or {}).get('armor_class_tier') or 'light').lower()
    return c if c in ('light', 'medium', 'heavy') else 'light'


def weight_class_weight(cls: str, floor: int) -> float:
    peak, spread, first = rules()['weight_class_bells'][cls]
    f = int(floor)
    if f < first:
        return 0.0
    return math.exp(-((f - peak) ** 2) / (2 * spread ** 2))


def pick_template(options, floor: int, rng):
    """(template id, template) from `options`, drawn by weight-class bell.
    Falls back to a uniform pick when no class is due on this floor."""
    options = list(options)
    if not options:
        return None
    ws = [weight_class_weight(weight_class(t), floor) for _tid, t in options]
    tot = sum(ws)
    if tot <= 0:
        return rng.choice(options)
    r, acc = rng.random() * tot, 0.0
    for opt, x in zip(options, ws):
        acc += x
        if r <= acc:
            return opt
    return options[-1]


# --------------------------------------------------------------- threshold

def equip_threshold(weight_cls: str, level: int, unique: bool = False) -> int:
    """Armour and shields: complexity (weight class) + benefit (tier)."""
    t = rules()['threshold']
    n = t['complexity'].get(weight_cls, 1) + t['benefit_by_tier'][tier_for_level(level) - 1]
    if unique:
        n += t['unique']
    return max(1, min(t['max'], n))


def accessory_threshold(slot: str, level: int, unique: bool = False) -> int:
    """Rings, amulets, belts: complexity (slot) + benefit (tier)."""
    t = rules()['accessory_threshold']
    n = t['complexity'].get(slot, 1) + t['benefit_by_tier'][tier_for_level(level) - 1]
    if unique:
        n += t['unique']
    return max(1, min(t['max'], n))


def core_enchant_cap() -> int:
    return int(rules()['enchant_cap']['core'])


def is_core(item) -> bool:
    """Does this piece carry AC: body armour or a shield."""
    cls = str(getattr(item, 'item_class', '') or '')
    if cls == 'shield':
        return True
    return cls == 'armor' and str(getattr(item, 'slot', 'body')) in CORE_SLOTS


def level_for_tier(tier: int, greater: bool = False) -> int:
    """The level of a tier's lesser (or greater) form."""
    t = max(1, min(5, int(tier or 1)))
    return 2 * t if greater else 2 * t - 1


def wears_flag(holder, flag: str) -> bool:
    """Any worn ring, amulet, belt or armour piece of ``holder`` with ``flag``
    set (the Hand of Glory's silent walk on a ring, Elvenkind's on boots).
    Reads attributes only, so a monster's or a test's stand-in works too."""
    worn = list(getattr(holder, 'equipped_accessories', None) or ())
    worn += [a for a in (getattr(holder, 'armor_slots', None) or ()) if a is not None]
    return any(getattr(it, flag, False) for it in worn)
