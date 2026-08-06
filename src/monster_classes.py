"""Monster family tags.

Each monster has a primary family tag derived from its `tags` list via
FAMILY_PRIORITY (first match wins). Used for display (bestiary family
line) and for family-targeted item effects (e.g. dragonslayer gear).
"""
from __future__ import annotations


# Priority order: first matching tag in this list is the monster's family.
# A monster with tags ['demon', 'humanoid'] is a demon (demon listed first).
FAMILY_PRIORITY = [
    'dragon', 'demon', 'celestial', 'undead', 'fey',
    'aberration', 'construct', 'elemental', 'beast',
    'humanoid', 'plant', 'reptile',
]


def get_monster_family(monster_or_corpse) -> str | None:
    """Return the primary family tag from a monster's tags list (priority-ordered).

    Accepts either a Monster instance, a monster defn dict, or a Corpse instance.
    Returns None if no family tag matches.
    """
    tags: list = []
    # Corpse stores its source monster definition (incl. tags) in monster_def.
    md = getattr(monster_or_corpse, 'monster_def', None)
    if isinstance(md, dict) and md.get('tags'):
        tags = list(md.get('tags') or [])
    elif isinstance(monster_or_corpse, dict):
        tags = list(monster_or_corpse.get('tags') or [])
    else:
        # Monster instance has a direct .tags list
        tags = list(getattr(monster_or_corpse, 'tags', []) or [])
    for f in FAMILY_PRIORITY:
        if f in tags:
            return f
    return None
