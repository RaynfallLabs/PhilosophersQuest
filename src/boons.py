"""Gate-boss gifts: three are offered when a gate boss dies, the player takes
one, and the choice is permanent (REBALANCE_MASTER_PLAN.md, decision D1).

Pure data and rules; `game_combat` notes the kill, `main.update` opens the
choice once control is back with the player, and `game_input` /
`game_render` handle the menu. The gifts live in data/boss_boons.json.
"""
from __future__ import annotations

import json

from paths import data_path

_cache: dict | None = None
STAT_NAMES = {'STR': 'Strength', 'CON': 'Constitution', 'DEX': 'Dexterity',
              'INT': 'Intelligence', 'WIS': 'Wisdom', 'PER': 'Perception'}


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            with open(data_path('data', 'boss_boons.json'), encoding='utf-8') as f:
                raw = json.load(f)
        except (OSError, ValueError):
            raw = {}
        _cache = {k: v for k, v in raw.items() if not k.startswith('_')}
    return _cache


def offer_for(boss_kind: str) -> dict | None:
    """The offer a boss leaves ({'title', 'gifts': [...], ...}), or None."""
    return _load().get(boss_kind)


def already_taken(player, boss_kind: str) -> bool:
    return boss_kind in (getattr(player, 'boons_taken', None) or {})


def solved_quest(player, boss_kind: str) -> bool:
    """True if the player beat this boss the way its story is told."""
    def carries(*ids) -> bool:
        held = list(getattr(player, 'inventory', []) or [])
        held += [getattr(player, 'weapon', None), getattr(player, 'shield', None),
                 getattr(player, 'belt_slot', None)]
        return any(getattr(i, 'id', None) in ids for i in held if i is not None)
    if boss_kind == 'asterion_minotaur':
        return carries('ariadnes_thread')
    if boss_kind == 'medusa_gorgon':
        return carries('aegis_of_athena', 'greater_aegis_of_athena')
    if boss_kind == 'fafnir_dragon':
        return bool(getattr(player, 'struck_from_the_pit', False))
    if boss_kind == 'fenrir_wolf':
        return int(getattr(player, '_gleipnir_binds', 0) or 0) > 0
    return False


def amount_for(player, boss_kind: str, gift: dict) -> int:
    offer = offer_for(boss_kind) or {}
    bonus = int(offer.get('quest_bonus', 0)) if solved_quest(player, boss_kind) else 0
    return int(gift.get('amount', 0)) + bonus


def describe(player, boss_kind: str, gift: dict) -> str:
    """'Strength +5' as the menu shows it."""
    return f"{STAT_NAMES.get(gift['stat'], gift['stat'])} +{amount_for(player, boss_kind, gift)}"


def take(player, boss_kind: str, index: int) -> tuple[dict, int] | None:
    """Grant gift `index` of this boss's offer. Returns (gift, amount), or
    None if there is no such gift or one was already taken from this boss."""
    offer = offer_for(boss_kind)
    if not offer or already_taken(player, boss_kind):
        return None
    gifts = offer.get('gifts') or []
    if not 0 <= index < len(gifts):
        return None
    gift = gifts[index]
    amount = amount_for(player, boss_kind, gift)
    player.apply_stat_bonus(gift['stat'], amount)
    if not isinstance(getattr(player, 'boons_taken', None), dict):
        player.boons_taken = {}
    player.boons_taken[boss_kind] = gift['id']
    return gift, amount
