"""The minor-slot enchantment stable (bug bash 3.3.2).

docs/design/ARMOR_REDESIGN_PLAN.md section 7, data/enchantments.json. A
minor armour piece (helm, gloves, bracers, greaves, boots, cloak, shirt)
of enchantment level 1-10 carries ONE enchantment from its own slot's
stable, in one of four lanes:

  guard  its slot's family (guards.py) turned aside and shrugged off, by a
         ladder the armour model priced (tools/balance/armor_model.py);
  might  Striking (your blows), Archery (your shots), Parrying;
  craft  help with the quiz its slot's work belongs to: the first wrong
         answer of every Nth quiz on that subject is forgiven (no chance:
         performance decides), the combat clock (Swift Strokes), the wait
         between prayers (the Hair Shirt);
  way    the powers moved off rings to their iconic gear (ruling 4): a
         status while worn (Telepathy, Speed, Displacement...), a stat by
         tier (Ogre Power, Dexterity, the Eagle), silent steps (Elvenkind).

The level is fixed when the piece is made (LORE NOT FLOOR); a blessed
piece works a level higher, a cursed one a level lower. Pure rules apart
from `apply_to`, which writes a piece's name, line and worn grants.
"""
from __future__ import annotations

import json
from functools import lru_cache

ROMAN = ('I', 'II', 'III', 'IV', 'V')
GUARD_CAP = 0.80             # tools/balance/armor_model.py LADDER_CAP


@lru_cache(maxsize=1)
def data() -> dict:
    from paths import data_path
    with open(data_path('data', 'enchantments.json'), encoding='utf-8') as f:
        return json.load(f)


def get(ench_id: str) -> dict | None:
    return data()['enchantments'].get(ench_id or '')


def for_slot(slot: str) -> dict:
    return {k: v for k, v in data()['enchantments'].items() if v.get('slot') == slot}


# ------------------------------------------------------------------ levels

def level_value(ench: dict, level: int) -> float:
    """The ladder's value at level 1-10: a tier's lesser form (odd level)
    takes the tier's value, its greater form (even) the halfway point to
    the next tier (tier V's greater form goes on by half the last step)."""
    tiers = ench.get('tiers') or []
    if not tiers or level <= 0:
        return 0.0
    level = min(10, int(level))
    t = (level + 1) // 2 - 1
    v = float(tiers[t])
    if level % 2 == 0:
        if t + 1 < len(tiers):
            v = (v + float(tiers[t + 1])) / 2
        elif t > 0:
            v = v + max(0.0, (v - float(tiers[t - 1])) / 2)
            if ench.get('lane') == 'guard' or ench.get('guards'):
                # Tier V's greater form goes on by half the last step, never
                # past the model's 80% cap on any guard (LADDER_CAP).
                v = min(v, GUARD_CAP)
    return v


def effective_level(piece) -> int:
    """A piece's working level: blessed one higher, cursed one lower."""
    lv = int(getattr(piece, 'ench_level', 0) or 0)
    if lv <= 0:
        return 0
    b = getattr(piece, 'buc', 'uncursed')
    if b == 'blessed':
        lv += 1
    elif b == 'cursed':
        lv -= 1
    return max(1, min(10, lv))


def tier_of(level: int) -> int:
    return max(1, min(5, (int(level) + 1) // 2))


def available(ench: dict, tier: int) -> bool:
    return (tier >= int(ench.get('from_tier', 1) or 1)
            and tier not in (ench.get('skip_tiers') or ()))


def roll(slot: str, level: int, rng) -> str:
    """An enchantment for a new `slot` piece of `level`: by lane weight,
    then evenly within the lane, among those that roll at its tier."""
    t = tier_of(level)
    pool = [(k, v) for k, v in for_slot(slot).items() if available(v, t)]
    if not pool:
        return ''
    lanes = data().get('lanes') or {}
    by_lane = {}
    for k, v in pool:
        by_lane.setdefault(v.get('lane', 'way'), []).append(k)
    weights = [(lane, float(lanes.get(lane, 1))) for lane in by_lane]
    tot = sum(w for _, w in weights)
    r, acc = rng.random() * tot, 0.0
    lane = weights[-1][0]
    for name, w in weights:
        acc += w
        if r <= acc:
            lane = name
            break
    return rng.choice(by_lane[lane])


# --------------------------------------------------------------- the piece

def describe(ench: dict, level: int) -> str:
    """The plain line a known piece shows ("Turns aside 46% of ...")."""
    v = level_value(ench, level)
    stat = tier_of(level)
    every = data()['craft_every'][max(0, min(9, level - 1))]
    text = str(ench.get('text', '')).format(
        pct=f"{round(100 * v)}%", n=every, nth=_ordinal(every), stat=stat, sec=level + 1)
    return text[:1].upper() + text[1:] + '.'


def _ordinal(n: int) -> str:
    n = int(n)
    suffix = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def display_name(ench: dict, level: int) -> str:
    """'of Iron Will II' or 'of Greater Iron Will II'."""
    t = tier_of(level)
    greater = 'Greater ' if level % 2 == 0 else ''
    return f"of {greater}{ench['name']} {ROMAN[t - 1]}"


def apply_to(piece, ench_id: str) -> None:
    """Write an enchantment onto a newly made piece: its id, its known name
    and line, and what it lends while worn (a status, a stat, a flag)."""
    ench = get(ench_id)
    if not ench:
        return
    level = int(getattr(piece, 'ench_level', 0) or 0)
    piece.ench_id = ench_id
    base = getattr(piece, 'name', '')
    piece.name = f"{base} {display_name(ench, level)}"
    piece.special = describe(ench, level)
    piece.ench_line = piece.special
    _grant(piece, ench, level)


def apply_named(piece) -> None:
    """A named piece's enchantment (its own ench_id and ench_level, from the
    data): the same power, but the piece keeps its name and its card text;
    the enchantment's line is `ench_line`. A status the piece already has
    is not replaced (the Blindfold stays a blindfold)."""
    ench = get(getattr(piece, 'ench_id', ''))
    if not ench:
        return
    level = int(getattr(piece, 'ench_level', 0) or 0)
    piece.ench_line = f"{ench['name']} {ROMAN[tier_of(level) - 1]}: {describe(ench, level)}"
    _grant(piece, ench, level)


def _grant(piece, ench: dict, level: int) -> None:
    """What an enchantment lends while worn: a status, a stat, a flag."""
    if ench.get('status') and not getattr(piece, 'on_equip_status', ''):
        piece.on_equip_status = ench['status']
    if ench.get('stat'):
        fx = dict(getattr(piece, 'effects', None) or {})
        fx['stat'] = ench['stat']
        fx['amount'] = tier_of(level)
        piece.effects = fx
    if ench.get('flag'):
        setattr(piece, ench['flag'], True)


# -------------------------------------------------------------- the hooks

def _worn(player):
    import gear
    for piece in getattr(player, 'armor_slots', None) or ():
        if piece is not None and getattr(piece, 'slot', '') in gear.MINOR_SLOTS \
                and getattr(piece, 'ench_id', ''):
            ench = get(piece.ench_id)
            if ench:
                yield piece, ench, effective_level(piece)


def guard_strength(piece) -> tuple:
    """(rider shrug, damage turn-aside) a piece's guard enchantment gives
    its slot's family (guards.py). 0 for any other lane."""
    ench = get(getattr(piece, 'ench_id', ''))
    if not ench or ench.get('lane') != 'guard' or ench.get('family'):
        return 0.0, 0.0
    v = level_value(ench, effective_level(piece))
    return v, v


def guard_families(piece):
    """[(family, rider, damage)] for a guard enchantment that names its own
    family (the cloak's Elementward and Vapourward)."""
    ench = get(getattr(piece, 'ench_id', ''))
    if not ench or ench.get('lane') != 'guard' or not ench.get('family'):
        return []
    v = level_value(ench, effective_level(piece))
    return [(ench['family'], v, v)]


def might(player, ench_id: str) -> float:
    """The strongest worn might of one kind (striking, archery, parrying)."""
    best = 0.0
    for _piece, ench, lv in _worn(player):
        if _id_of(ench) == ench_id:
            best = max(best, level_value(ench, lv))
    return best


def _id_of(ench: dict) -> str:
    for k, v in data()['enchantments'].items():
        if v is ench:
            return k
    return ''


def quiz_seconds(player) -> int:
    """Swift Strokes: seconds on the combat clock (the best worn)."""
    best = 0
    for _piece, ench, lv in _worn(player):
        if ench.get('seconds'):
            best = max(best, lv + 1)
    return best


def prayer_cooldown_cut(player) -> float:
    """The Hair Shirt: the share cut from the wait between prayers."""
    best = 0.0
    for _piece, ench, lv in _worn(player):
        if ench.get('prayer_cooldown'):
            best = max(best, level_value(ench, lv))
    return best


def craft_ready(player, subject: str):
    """A craft enchantment for `subject` counts this quiz; every Nth one
    (N by its level, data 'craft_every') forgives its first wrong answer.
    Returns the piece when this quiz is one, else None."""
    best = None
    for piece, ench, lv in _worn(player):
        if ench.get('subject') == subject and (best is None or lv > best[1]):
            best = (piece, lv)
    if best is None:
        return None
    piece, lv = best
    counts = player.__dict__.setdefault('_craft_counts', {})
    counts[subject] = int(counts.get(subject, 0)) + 1
    every = int(data()['craft_every'][max(0, min(9, lv - 1))])
    if counts[subject] % every == 0:
        return piece
    return None
