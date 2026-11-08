"""Ring and amulet kinds (bug bash 3.3.2, armour plan section 8).

data/ring_kinds.json. A common ring or amulet is one KIND (Protection,
Spell Turning, Regeneration, Invisibility, Sustenance, Wizardry; amulets of
Life Saving, Wisdom, Intellect, Constitution) at an enchantment level 1-10
rolled when it is found, on the same bells as armour (gear.roll_level):
tier = ceil(level / 2) is its quiz tier and its ladder's step, so a ring
found deep is a stronger ring. Odd levels are a tier's lesser form, even
levels the greater ("Ring of Greater Protection II"), as for the minor-slot
enchantments (enchantments.level_value); a blessed ring works a level
higher, a cursed one a level lower. No ring or amulet gives AC.

The level is fixed when the ring is made (LORE NOT FLOOR); `relevel` is
what an Enchant Ring scroll or a save repair calls. The hooks read what
the worn rings do: Protection and Spell Turning through guards.guard_keep,
the rest from their own systems (regeneration tick, hunger, spell cost,
life saving, the worn stats).
"""
from __future__ import annotations

import json
from functools import lru_cache

import enchantments as _ench

ROMAN = _ench.ROMAN


@lru_cache(maxsize=1)
def data() -> dict:
    from paths import data_path
    with open(data_path('data', 'ring_kinds.json'), encoding='utf-8') as f:
        return json.load(f)


def kinds() -> dict:
    return data()['kinds']


def get(kind: str) -> dict | None:
    return kinds().get(kind or '')


def kind_of(item) -> dict | None:
    return get(getattr(item, 'kind', '') or '')


def value(kind: dict, level: int) -> float:
    """The kind's ladder at level 1-10 (lesser and greater forms)."""
    v = _ench.level_value(kind, level)
    return float(round(v)) if kind.get('whole') else v


def first_level(kind: dict) -> int:
    """The lowest level the kind is made at (its first tier's lesser form)."""
    return 2 * int(kind.get('from_tier', 1) or 1) - 1


# ------------------------------------------------------------------ making

def display_name(item, kind: dict, level: int) -> str:
    """'Ring of Protection II' / 'Amulet of Greater Wisdom IV'."""
    noun = 'Amulet' if kind.get('slot') == 'amulet' else 'Ring'
    t = _ench.tier_of(level)
    greater = 'Greater ' if level % 2 == 0 else ''
    return f"{noun} of {greater}{kind['name']} {ROMAN[t - 1]}"


def describe(kind: dict, level: int) -> str:
    v = value(kind, level)
    pct = f"{round(100 * v * float(kind.get('show', 1.0)))}%"
    text = str(kind.get('text', '')).format(
        pct=pct, n=int(v), stat=_ench.tier_of(level))
    return text[:1].upper() + text[1:] + '.'


def level_fields(item, level: int) -> dict:
    """What a kind ring at `level` is: its level, tier, equip threshold,
    name, line, and effects (a stat kind's amount is its tier). Empty for a
    ring that is not a kind. Accessory.relevel writes them."""
    import gear
    kind = kind_of(item)
    if not kind:
        return {}
    level = max(first_level(kind), min(gear.MAX_LEVEL, int(level or 0)))
    t = gear.tier_for_level(level)
    fx = dict(getattr(item, 'effects', None) or {})
    if kind.get('stat'):
        fx['stat'] = kind['stat']
        fx['amount'] = t
    return {'ench_level': level, 'tier': t,
            'equip_threshold': gear.accessory_threshold(kind.get('slot', 'ring'), level),
            'name': display_name(item, kind, level), 'special': describe(kind, level),
            'effects': fx}


def relevel(item, level: int) -> None:
    """Set a kind ring's level and everything that follows from it (the
    item's own Accessory.relevel). The caller re-syncs worn stats
    (Player.sync_worn_stats) if it is worn."""
    if kind_of(item) and hasattr(item, 'relevel'):
        item.relevel(level)


def dress(item, floor: int, rng) -> None:
    """A kind ring found as loot on `floor`: its level by the armour bells
    (never plain: a ring is its power), at least the kind's first level."""
    import gear
    kind = kind_of(item)
    if not kind:
        return
    relevel(item, gear.roll_level(floor, rng, plain_ok=False))


# ------------------------------------------------------------------ hooks

def _worn(player):
    seen = set()
    for it in list(getattr(player, 'equipped_accessories', None) or ()):
        if it is None or id(it) in seen:
            continue
        seen.add(id(it))
        kind = kind_of(it)
        if kind and int(getattr(it, 'ench_level', 0) or 0) > 0:
            yield it, kind, _ench.effective_level(it)


def best(player, kind_id: str) -> tuple:
    """(the strongest worn ring of a kind, its value) or (None, 0.0)."""
    top, top_v = None, 0.0
    for it, kind, lv in _worn(player):
        if it.kind == kind_id:
            v = value(kind, lv)
            if top is None or v > top_v:
                top, top_v = it, v
    return top, top_v


def guard_parts(player):
    """[(family, rider, damage, ring)] for worn guard kinds (guards.guard_keep):
    Protection shrugs off riders, Spell Turning turns aside damage. Two rings
    of one kind do not add: the stronger counts (as for the worn stats)."""
    out = []
    for kind_id, kind in kinds().items():
        if kind.get('lane') != 'guard':
            continue
        it, v = best(player, kind_id)
        if it is None or v <= 0:
            continue
        rider = v if kind.get('guards') == 'rider' else 0.0
        dmg = v if kind.get('guards') == 'damage' else 0.0
        out.append((kind.get('family') or {}, rider, dmg, it))
    return out


def regen_share(player) -> float:
    """Share of max health a Ring of Regeneration mends each regeneration
    tick (status_effects.REGEN_PERIOD turns); 0 without one."""
    return best(player, 'regeneration')[1]


def hunger_interval(player, base: int) -> int:
    """Moves per point of stamina with a Ring of Sustenance on (hunger
    comes on its share more slowly); `base` without one."""
    cut = best(player, 'sustenance')[1]
    if cut <= 0:
        return base
    return max(base, int(round(2 / max(0.05, 1.0 - cut))))


def spell_cost(player, cost: int) -> int:
    """A spell's mana cost through a Ring of Wizardry (never under 1)."""
    cut = best(player, 'wizardry')[1]
    if cut <= 0 or cost <= 0:
        return cost
    return max(1, int(round(cost * (1.0 - cut))))


def life_saving_share(item) -> float:
    """Share of max health an Amulet of Life Saving leaves you with; 0 for
    anything else that saves a life (those leave you at 1)."""
    kind = kind_of(item)
    if not kind or getattr(item, 'kind', '') != 'life_saving':
        return 0.0
    return value(kind, _ench.effective_level(item))


# ----------------------------------------------------------- invisibility
# The ring's veil: invisible while you keep quiet, slipping when you strike
# (AD&D's ring breaks on an attack) and settling again after the ring's
# number of quiet turns (fewer on a deeper ring).

def veil_turns(player) -> int:
    """Quiet turns before a worn Ring of Invisibility veils you; 0 if none."""
    ring, v = None, 0.0
    for it, kind, lv in _worn(player):
        if it.kind == 'invisibility':
            n = value(kind, lv)
            if ring is None or n < v:
                ring, v = it, n
    return int(v) if ring is not None else 0


def tick(player) -> str:
    """Once a turn: settle the veil after enough quiet turns, or lift it
    if the ring came off. Returns a line for the log ('' for none)."""
    n = veil_turns(player)
    se = player.status_effects
    if n <= 0:
        if getattr(player, '_veil_on', False):
            player._veil_on = False
            if se.get('invisible') == -1 and not player._still_granted('invisible', None):
                del se['invisible']
        return ''
    if se.get('invisible'):
        return ''                    # veiled already (the ring, or a potion)
    player._veil_quiet = int(getattr(player, '_veil_quiet', 0) or 0) + 1
    if player._veil_quiet >= n:
        player._veil_on = True
        se['invisible'] = -1
        return 'You fade from sight again.'
    return ''


def on_strike(player) -> str:
    """The hero attacks: the ring's veil slips (a potion's does not)."""
    player._veil_quiet = 0
    if not getattr(player, '_veil_on', False):
        return ''
    player._veil_on = False
    se = player.status_effects
    if se.get('invisible') == -1 and not player._still_granted('invisible', None):
        del se['invisible']
        return 'Your veil slips as you strike.'
    return ''
