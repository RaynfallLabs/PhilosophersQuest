"""Philosophy tier mastery (Brandon 2026-10-24).

Answer every philosophy question of a tier correctly in ONE run and the
tier's trait unlocks (data/philosophy_mastery.json): +1 WIS, and from then
on every item whose identify question is of that tier is fully identified
the moment it reaches the hero's pack. The quiz engine already keeps the
run's right answers (wrong ones come round again); this module holds the
data and the pure rules. The game side (awarding the trait, naming what
the hero carries) is MagicMixin._philosophy_mastery_check and
_mastery_identify_carried in game_magic.py; the traits list reads
QuirkSystem.progress_count.
"""
from __future__ import annotations

import json

from paths import data_path

SUBJECT = 'philosophy'

_DATA: dict | None = None


def data() -> dict:
    """The parsed data/philosophy_mastery.json (cached)."""
    global _DATA
    if _DATA is None:
        with open(data_path('data', 'philosophy_mastery.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def tiers() -> list[dict]:
    """The five tier entries, tier 1 first."""
    return sorted(data()['tiers'], key=lambda t: int(t['tier']))


def trait_ids() -> list[str]:
    return [t['id'] for t in tiers()]


def entry(qid: str) -> dict | None:
    return next((t for t in tiers() if t['id'] == qid), None)


def trait_for_tier(tier: int) -> dict | None:
    return next((t for t in tiers() if int(t['tier']) == int(tier)), None)


def wisdom() -> int:
    return int(data().get('wis', 1))


def mastered_tiers(player) -> set[int]:
    """The tiers whose trait the hero holds this run."""
    held = getattr(player, 'unlocked_quirks', None) or set()
    return {int(t['tier']) for t in tiers() if t['id'] in held}


def identify_tier(item, player) -> int:
    """The tier of the philosophy question that identifying ``item`` asks:
    its id tier, lowered by the hero's Ring of Pythia or Torque of Lugh
    (never below 1). The same number _identify_item quizzes at."""
    from items import item_id_tier
    tier = item_id_tier(item)
    reduce = getattr(player, 'get_identify_tier_reduction', lambda: 0)()
    if reduce and int(reduce) > 0:
        tier = max(1, tier - int(reduce))
    return tier


def covers(item, player) -> bool:
    """Is ``item`` of a tier the hero has mastered? (Whether there is
    anything left to identify on it is the caller's question.)"""
    held = mastered_tiers(player)
    return bool(held) and identify_tier(item, player) in held


def carried(player) -> list:
    """Everything the hero carries: the pack, then what he wears and wields."""
    out = list(getattr(player, 'inventory', None) or [])
    try:
        worn = player.get_equipped_items().values()
    except Exception:
        worn = ()
    for it in worn:
        if it is not None and all(it is not o for o in out):
            out.append(it)
    return out
