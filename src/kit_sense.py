"""Kit Sense: a hunter knows which of his tools a creature fears
(winning-build plan 2026-11-13, section 3.1).

A hero who knows a family to its Hunter tier is told, on first sight of a
group of its creatures, the best tool he is carrying for them: "Your Silver
Mace would serve here." One line per sighting (a kind is sighted again only
after it has been out of his sight for a while: data/kit_sense.json `gap`),
and nothing at all when his best tool is the one already in his hand.

THE TOOLS come from PROVIDERS, a plain list of functions
`provider(player, monster) -> iterable of Tool`. The weapons he carries are
the first (the one in his hand, the one At His Back, the bow on his
shoulder, every weapon in his pack). The arsenal's coatings and flasks
(slice 5) register their own with `@provider`; each Tool says its `kind`
('weapon', 'coating', 'flask'), which picks its lines in
data/kit_sense.json, and whether it is `in_hand` already (the wielded
weapon; a coating already on the blade).

A tool's `mult` is how its blow meets the creature as far as the hero knows
his own tool: a weapon's form always (its shape is plain to see), its metal
and its blessing once he knows the weapon (identified, or its kind known).
It is the same reckoning the blow makes (combat.weapon_type_multiplier,
held to the cap). Pure module: no pygame, no Game.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass

_DATA: dict | None = None
_EPS = 1e-9


def data() -> dict:
    """data/kit_sense.json, loaded once (bundled: PhilosophersQuest.spec)."""
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'kit_sense.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def hunter_tier() -> int:
    """The family tier Kit Sense needs (Hunter, 4)."""
    return int(data().get('tier', 4))


@dataclass
class Tool:
    """One thing the hero could meet a creature with."""
    kind: str               # 'weapon' (slice 5: 'coating', 'flask')
    item: object            # the item itself (None: bare hands)
    name: str               # its name as the hero knows it
    mult: float             # how it meets the creature, as far as he knows the tool
    in_hand: bool = False   # already in use: nothing to switch to


# The tool providers, asked in order. A later slice appends its own.
PROVIDERS: list = []


def provider(fn):
    """Register a tool provider: fn(player, monster) -> iterable of Tool."""
    if fn not in PROVIDERS:
        PROVIDERS.append(fn)
    return fn


def tools(player, monster) -> list:
    """Every tool the providers offer against this creature."""
    out = []
    for fn in list(PROVIDERS):
        out.extend(fn(player, monster) or ())
    return out


# ---------------------------------------------------------------------------
# The weapons he carries
# ---------------------------------------------------------------------------
def knows_weapon(player, weapon) -> bool:
    """Does the hero know what this weapon is made of and whether it is
    blessed (identified, or its kind known)? Bare hands: yes."""
    if weapon is None:
        return True
    import items
    return bool(items.is_fully_known(weapon, player) or items.is_split_type_known(player, weapon))


def known_mult(player, weapon, monster) -> float:
    """How a weapon's blow meets the creature, as far as the hero knows the
    weapon: its form always; its metal, blessing and bane once he knows it."""
    import affinity
    import combat
    if knows_weapon(player, weapon):
        blessed = False
        if weapon is not None and getattr(weapon, 'buc', '') == 'blessed':
            import items
            blessed = bool(items.buc_known_to(weapon, player))
        form, sub = combat.weapon_type_multiplier(weapon, monster, blessed=blessed)
    else:
        form, _sub = combat.weapon_type_multiplier(weapon, monster, blessed=False)
        sub = 1.0
    if weapon is not None and getattr(weapon, 'ignore_resistances', False):
        form = max(1.0, form)
    return affinity.capped(form * sub)


def _has_ammo(player, weapon) -> bool:
    need = getattr(weapon, 'requires_ammo', None)
    if not need or getattr(weapon, 'infinite_ammo', False):
        return True
    return any(getattr(i, 'ammo_type', None) == need for i in (getattr(player, 'inventory', None) or ()))


def _name(player, item) -> str:
    from hud_context import item_bare_name
    from naming import proper_name
    return proper_name(item_bare_name(player, item))


@provider
def weapon_tools(player, monster) -> list:
    """The wielded weapon (or bare hands) in hand, then the bow he has
    strung and every weapon in his pack (the one At His Back among them),
    a bow only with arrows for it."""
    from items import Weapon
    held = getattr(player, 'weapon', None)
    out = [Tool('weapon', held, _name(player, held) if held is not None else 'Bare Hands',
                known_mult(player, held, monster), in_hand=True)]
    seen = {id(held)}
    pack = [getattr(player, 'ranged_weapon', None)] + list(getattr(player, 'inventory', None) or ())
    for it in pack:
        if it is None or id(it) in seen or not isinstance(it, Weapon):
            continue
        seen.add(id(it))
        if not _has_ammo(player, it):
            continue
        out.append(Tool('weapon', it, _name(player, it), known_mult(player, it, monster)))
    return out


# ---------------------------------------------------------------------------
# What to say
# ---------------------------------------------------------------------------
def advise(player, monster):
    """(the best tool, how much better it is than what is in hand), or None
    when nothing he carries beats what he already holds."""
    ts = tools(player, monster)
    if not ts:
        return None
    held = max((t.mult for t in ts if t.in_hand), default=1.0)
    top = max(ts, key=lambda t: (t.mult, t.in_hand))
    if top.in_hand or top.mult <= held + _EPS:
        return None
    return top, top.mult - held


def new_sightings(state: dict, kinds, *, floor, turn: int) -> list:
    """The kinds in sight now that the hero has not had in sight for more
    than `gap` turns on this floor (first sight of a group). Every kind in
    sight is marked seen this turn."""
    gap = int(data().get('gap', 25))
    kinds = list(dict.fromkeys(kinds))
    fresh = [k for k in kinds
             if state.get((floor, k)) is None or int(turn) - int(state[(floor, k)]) > gap]
    for k in kinds:
        state[(floor, k)] = int(turn)
    return fresh


def line(tool: Tool, monster, many: bool = False, rng=None) -> str:
    """"Your Silver Mace would serve here.\""""
    rng = rng or random
    from monster import the_name
    table = data().get('lines_many' if many else 'lines') or {}
    pool = table.get(tool.kind) or table.get('default') or []
    if not pool:
        return ''
    text = rng.choice(pool)
    return text.replace('{tool}', tool.name).replace('{the}', the_name(monster, lower=True))


def on_sight(player, monsters, state: dict, *, floor, turn: int, rng=None) -> str:
    """The Kit Sense line for this turn, or '': of the kinds just sighted
    whose family the hero knows to Hunter, the one his best tool helps
    most. `monsters`: the hostile creatures he can see."""
    import family_lore
    by_kind: dict = {}
    for m in monsters or ():
        k = getattr(m, 'kind', '')
        if k:
            by_kind.setdefault(k, []).append(m)
    fresh = new_sightings(state, list(by_kind), floor=floor, turn=turn)
    need = hunter_tier()
    pick = None
    for k in fresh:
        m = by_kind[k][0]
        if family_lore.tier(player, family_lore.family_of(m)) < need:
            continue
        got = advise(player, m)
        if got and (pick is None or got[1] > pick[1] + _EPS):
            pick = (got[0], got[1], m, len(by_kind[k]) > 1)
    if pick is None:
        return ''
    tool, _gain, m, many = pick
    return line(tool, m, many, rng)
