"""Boss Class Ascension -- the 4-boss class progression.

Design: proposals/design/boss_class_ascension.md. Each of the first four bosses
(floors 20/40/60/80) drops a Legendary Cut; cooking it opens an Ascension where
the player advances one class tier: Calling -> Specialization -> Mastery ->
Capstone. These are deliberately SMALL flavor perks, not power spikes.

This module is the PURE logic (no Pygame): load the tree, evaluate soft-gate
requirements, list the offered choices for the player's current tier, and apply
a chosen node's bonuses. The cooking hook + selection UI live in the game layer.

Player state (lazily created, so old saves stay valid):
  player.class_path:      list[str]   chosen node ids, in tier order
  player.class_features:  dict        accumulated perks:
        weapon_bonuses:list[{groups,flat}], save_bonuses:list[{category,amount}],
        healing_received_pct:num, mp_cost_reduction:num, trap_sight:num
  player.class_abilities: list[str]   granted ability ids
  player.class_stat_total:int         stats granted by classes (capped)
"""
from __future__ import annotations

import json

from paths import data_path

_CACHE: dict | None = None


def load_classes() -> dict:
    """All class nodes keyed by id (the _meta block kept under '_meta'). Cached."""
    global _CACHE
    if _CACHE is None:
        with open(data_path('data', 'classes.json'), encoding='utf-8') as f:
            raw = json.load(f)
        _CACHE = {k: v for k, v in raw.items() if not k.startswith('_')}
        _CACHE['_meta'] = raw.get('_meta', {})
    return _CACHE


def _meta() -> dict:
    return load_classes().get('_meta', {})


def stat_cap() -> int:
    return int(_meta().get('stat_cap_total', 10))


def weapon_groups() -> dict:
    return _meta().get('weapon_groups', {})


# --- player accessors (lazy / old-save safe) --------------------------------

def class_path(player) -> list:
    return list(getattr(player, 'class_path', []) or [])


def class_features(player) -> dict:
    return getattr(player, 'class_features', {}) or {}


def proficiency(player, key: str) -> float:
    """A scalar perk value (healing_received_pct / mp_cost_reduction / trap_sight)."""
    return float(class_features(player).get(key, 0) or 0)


def has_ability(player, ability_id: str) -> bool:
    return ability_id in (getattr(player, 'class_abilities', []) or [])


def weapon_flat_bonus(player, weapon) -> int:
    """Small FLAT damage bonus if `weapon` is in one of the player's class
    signature weapon groups (Fighter swords/axes, Rogue ranged). 0 otherwise."""
    if weapon is None:
        return 0
    wclass = getattr(weapon, 'weapon_class', '') or ''
    groups = weapon_groups()
    total = 0
    for wb in class_features(player).get('weapon_bonuses', []) or []:
        for g in wb.get('groups', []):
            if wclass in groups.get(g, []):
                total += int(wb.get('flat', 0))
                break
    return total


def save_bonus(player, category: str) -> int:
    """Accumulated class save bonus for a category (or 'all')."""
    total = 0
    for sb in class_features(player).get('save_bonuses', []) or []:
        if sb.get('category') in (category, 'all'):
            total += int(sb.get('amount', 0))
    return total


# --- soft-gate requirements (option B) --------------------------------------

def _check_condition(player, cond: dict) -> bool:
    if 'stat' in cond:
        return int(getattr(player, cond['stat'], 0)) >= int(cond.get('min', 0))
    if cond.get('knows_any_spell'):
        return bool(getattr(player, 'known_spells', {}) or {})
    if 'carries_class' in cond:
        names = set(cond['carries_class'])
        return any(type(it).__name__ in names for it in getattr(player, 'inventory', []))
    return False


def meets_requirement(player, node: dict) -> bool:
    """True if the player qualifies for this node. A null requirement (Fighter)
    is always available -- the default path."""
    req = node.get('requirement')
    if not req:
        return True
    conds = req.get('conditions', [])
    if req.get('type', 'any') == 'all':
        return all(_check_condition(player, c) for c in conds)
    return any(_check_condition(player, c) for c in conds)


# --- what the player may choose right now ------------------------------------

def _nodes_at_tier(tier: int) -> list:
    return [nid for nid, n in load_classes().items()
            if nid != '_meta' and n.get('tier') == tier]


def offered_choices(player) -> list[str]:
    """Node ids offered at the player's CURRENT ascension step (tier = advances
    taken + 1). Tier-1 callings are gated by requirement (Fighter always shown);
    higher tiers branch off the last pick. Returns [] when those nodes don't
    exist yet."""
    path = class_path(player)
    tier = len(path) + 1
    if tier == 1:
        return [nid for nid in _nodes_at_tier(1)
                if meets_requirement(player, load_classes()[nid])]
    parent = path[-1]
    return [nid for nid in _nodes_at_tier(tier)
            if load_classes()[nid].get('parent') == parent
            and meets_requirement(player, load_classes()[nid])]


# --- apply a chosen node -----------------------------------------------------

def apply_class_node(player, node_id: str) -> list[str]:
    """Apply a chosen node to the player and record it. Returns flavor/effect
    messages. Stats honor a run-total cap; perks accumulate; the ability id is
    recorded for the power menu (activation wired in the game layer)."""
    classes = load_classes()
    if node_id not in classes or node_id == '_meta':
        return [f"(unknown class node: {node_id})"]
    node = classes[node_id]
    msgs = [f"ASCENSION -- you become a {node['name']}!"]

    # lazy-init player state
    if not getattr(player, 'class_path', None):
        player.class_path = []
    if not getattr(player, 'class_features', None):
        player.class_features = {}
    if not getattr(player, 'class_abilities', None):
        player.class_abilities = []
    if not hasattr(player, 'class_stat_total'):
        player.class_stat_total = 0
    cf = player.class_features

    # stats (capped by run total)
    cap = stat_cap()
    for stat, amt in (node.get('stat_bonuses') or {}).items():
        amt = int(amt)
        room = cap - int(getattr(player, 'class_stat_total', 0))
        grant = max(0, min(amt, room))
        if grant > 0:
            player.apply_stat_bonus(stat, grant)
            player.class_stat_total = int(getattr(player, 'class_stat_total', 0)) + grant
            msgs.append(f"  {stat} +{grant}")
        elif amt > 0:
            msgs.append(f"  {stat} (class stat cap of +{cap} reached)")

    # perks
    for key, val in (node.get('perks') or {}).items():
        if key == 'weapon_bonus':
            cf.setdefault('weapon_bonuses', []).append(val)
            msgs.append(f"  +{val.get('flat', 0)} damage with {', '.join(val.get('groups', []))}")
        elif key == 'save_bonus':
            cf.setdefault('save_bonuses', []).append(val)
            msgs.append(f"  +{val.get('amount', 1)} {val.get('category', '')} saves")
        else:  # scalar perks accumulate (healing_received_pct, mp_cost_reduction, trap_sight)
            cf[key] = float(cf.get(key, 0)) + float(val)
            msgs.append(f"  {key.replace('_', ' ')} +{val}")

    # ability recorded (activation wired in the game layer)
    ability = node.get('ability') or {}
    if ability.get('id') and ability['id'] not in player.class_abilities:
        player.class_abilities.append(ability['id'])
        msgs.append(f"  Ability: {ability.get('name', ability['id'])} -- {ability.get('desc', '')}")

    player.class_path.append(node_id)
    return msgs
