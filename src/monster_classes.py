"""Monster families: a thin reader of the written `family` field.

Every monster in data/monsters.json carries ONE `family` (one of the 22 in
data/monster_families.json, written by tools/content/assign_monster_families.py
from each creature's lore). src/family_lore.py owns the table and every rule
about it; this module is the old entry point, kept so callers that only want
"which family is this?" have a one-line answer.

(The old tag-priority guess, FAMILY_PRIORITY, was retired on 2026-10-18 when
the families became data. Tags still drive weapons and materials.)
"""
from __future__ import annotations

import family_lore


def get_monster_family(monster_or_corpse) -> str | None:
    """The family id of a Monster, a Corpse, a monster dict or a kind id,
    or None (Death, the secret cow, the ethereal unicorn)."""
    return family_lore.family_of(monster_or_corpse)


def get_family_name(monster_or_corpse) -> str:
    """The family's display name ("The Restless Dead"), or ''."""
    fid = get_monster_family(monster_or_corpse)
    return family_lore.family_name(fid) if fid else ''
