"""Creatures that split when struck the wrong way (`splits` in monsters.json).

    "splits": {"by": "weak_blow", "share": 0.10, "max": 8}
    "splits": {"by": ["slash", "lightning"], "max": 6}
    "splits": {"by": ["slash", "pierce"], "into": "khrafstra_swarm", "max": 6}

* by "weak_blow": a blow that does less than `share` of the creature's
  original health (Blood of Tiamat: a small cut makes two of it; one great
  blow, a long answer chain, ends it outright).
* by a list of damage forms: a blow made ONLY of those forms. A weapon that
  can wound another way is used that way (a sword that can thrust does not
  cut a black pudding in two; an axe does). Spells count by their element.
* into: absent, the creature divides, and the new body takes half of what
  health is left; given, the blow lets out a new creature of that kind
  instead and the wounded one keeps its health (Azhi Dahaka's vermin).
* max: how many splits one creature and everything split from it may make
  in all. The count is shared down the line, so a pudding cannot fill the
  floor.

Monster.take_damage asks `blow_splits` and counts the split on the monster
(`_pending_splits`); the game calls `spawn_pending` at the end of every
action, so the new bodies appear on free tiles next to the wounded one,
whatever hurt it (melee, a spell, a pet, a trap).
"""
from __future__ import annotations

import json
import random

DEFAULT_MAX = 6
DEFAULT_SHARE = 0.10
MIN_HP_TO_DIVIDE = 2          # a body with less than this cannot halve

_DEFS = None


def _defs() -> dict:
    global _DEFS
    if _DEFS is None:
        from paths import data_path
        with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    return _DEFS


def _family(monster) -> list:
    """[splits left, original max HP], shared by a creature and everything
    split from it (one list object, so pickling keeps it shared)."""
    fam = monster.__dict__.get('_split_family')
    if fam is None:
        spec = monster.splits if isinstance(monster.splits, dict) else {}
        fam = [int(spec.get('max', DEFAULT_MAX)), int(monster.max_hp)]
        monster.__dict__['_split_family'] = fam
    return fam


def blow_forms(monster, damage_type) -> set:
    """What a blow was made of: a spell's element, or the weapon's forms
    (combat.player_attack sets them on the monster before the blow)."""
    if damage_type and damage_type != 'physical':
        return {damage_type}
    forms = monster.__dict__.get('_incoming_forms')
    return set(forms) if forms else {'physical'}


def blow_splits(monster, amount: int, damage_type='physical') -> bool:
    """Does this blow (already taken; the monster survived it) split it?"""
    spec = getattr(monster, 'splits', None)
    if not isinstance(spec, dict):
        return False
    fam = _family(monster)
    pending = int(getattr(monster, '_pending_splits', 0) or 0)
    if fam[0] - pending <= 0:
        return False
    by = spec.get('by', 'weak_blow')
    if by == 'weak_blow':
        if amount >= float(spec.get('share', DEFAULT_SHARE)) * fam[1]:
            return False
    else:
        forms = blow_forms(monster, damage_type)
        if not forms or not forms <= set(by):
            return False
    if not spec.get('into') and monster.hp < MIN_HP_TO_DIVIDE:
        return False
    return True


def _free_tiles_around(game, m) -> list:
    from geom import all_occupied_tiles
    taken = all_occupied_tiles(game.monsters)
    try:
        taken |= game._occupants()
    except Exception:
        taken.add((game.player.x, game.player.y))
    out = []
    for r in (1, 2):
        ring = [(m.x + dx, m.y + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                if max(abs(dx), abs(dy)) == r]
        random.shuffle(ring)
        out += [t for t in ring if game.dungeon.in_bounds(*t) and game.dungeon.is_walkable(*t)
                and t not in taken]
        if out:
            break
    return out


def _new_body(m, spec):
    """The creature a split makes, and its message."""
    from monster import Monster, the_name
    kind = spec.get('into')
    if kind:
        defn = _defs().get(kind)
        if not defn:
            return None, ''
        child = Monster({**defn, 'id': kind}, m.x, m.y)
        return child, f"A {child.name} spills out of the wound in {the_name(m, lower=True)}!"
    defn = _defs().get(m.kind) or {}
    child = Monster({**defn, 'id': m.kind}, m.x, m.y)
    half = m.hp // 2
    m.hp -= half
    child.hp = half
    child.max_hp = max(half, m.max_hp // 2)
    return child, f"{the_name(m)} splits in two!"


def spawn_pending(game) -> int:
    """Set down every split earned since the last call. Returns how many."""
    made = 0
    for m in list(getattr(game, 'monsters', None) or ()):
        n = int(getattr(m, '_pending_splits', 0) or 0)
        if not n:
            continue
        m._pending_splits = 0
        if not getattr(m, 'alive', False):
            continue
        spec = m.splits if isinstance(m.splits, dict) else {}
        fam = _family(m)
        for _ in range(n):
            if fam[0] <= 0:
                break
            if not spec.get('into') and m.hp < MIN_HP_TO_DIVIDE:
                break
            tiles = _free_tiles_around(game, m)
            if not tiles:
                break
            child, msg = _new_body(m, spec)
            if child is None:
                break
            child.x, child.y = tiles[0]
            child._aware = True
            if not spec.get('into'):
                child.__dict__['_split_family'] = fam      # one count for the whole line
            fam[0] -= 1
            game.monsters.append(child)
            made += 1
            seen = getattr(game, 'visible', None) or ()
            if (m.x, m.y) in seen or (child.x, child.y) in seen:
                game.add_message(msg, 'warning')
    return made
