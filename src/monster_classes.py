"""Per-family mastery for monsters, mirroring class_masteries for items.

Each monster has a primary family tag derived from its `tags` list via
FAMILY_PRIORITY (first match wins). Mastering a monster (chain-5 identify
on a corpse) unlocks the matching MONSTER_FAMILY_BLESSINGS entry on
`player.unlocked_monster_class_masteries`.

Use-site application (in combat.py and status_effects):
  - damage_vs_tag / tohit_vs_tag: queried during attack vs a tagged target.
  - resist_charm / resist_elemental / sp_regen / int_bonus / wisdom_bonus:
    queried at their respective hook sites.

Blessings are deliberately small flavor bonuses, not game-breaking.
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


# Per-family mastery blessings. Granted on chain-5 corpse-identify.
# Stored against `player.unlocked_monster_class_masteries[family_tag]`.
MONSTER_FAMILY_BLESSINGS: dict[str, dict] = {
    'dragon': {
        'kind': 'damage_vs_tag', 'tag': 'dragon', 'value': 2,
        'desc': 'Dragonslayer: +2 damage vs dragons.',
    },
    'demon': {
        'kind': 'damage_vs_tag', 'tag': 'demon', 'value': 2,
        'desc': 'Exorcist: +2 damage vs demons.',
    },
    'celestial': {
        'kind': 'wisdom_bonus', 'value': 1,
        'desc': 'Theophany: +1 WIS permanently.',
    },
    'undead': {
        'kind': 'save_bonus', 'value': {'cat': 'CON', 'amount': 2},
        'desc': 'Grave-warden: +2 CON saves — stand firm against undead paralysis and fear.',
    },
    'fey': {
        'kind': 'save_bonus', 'value': {'cat': 'WIS', 'amount': 2},
        'desc': 'Fey lore: +2 WIS saves — your will resists charm and illusion.',
    },
    'aberration': {
        'kind': 'save_bonus', 'value': {'cat': 'WIS', 'amount': 2},
        'desc': 'Aberrant insight: +2 WIS saves — your mind resists confusion and domination.',
    },
    'construct': {
        'kind': 'damage_vs_tag', 'tag': 'construct', 'value': 1,
        'desc': 'Constructor: +1 damage vs constructs, ignore 1 AC.',
    },
    'elemental': {
        'kind': 'resist_elemental', 'value': 1,
        'desc': 'Elemental mastery: +1 resist to fire/cold/lightning damage.',
    },
    'beast': {
        'kind': 'sp_regen', 'value': 1,
        'desc': 'Beast lore: +1 SP regen near beasts.',
    },
    'humanoid': {
        'kind': 'tohit_vs_tag', 'tag': 'humanoid', 'value': 1,
        'desc': 'Anatomist: +1 to-hit vs humanoids.',
    },
    'plant': {
        'kind': 'damage_vs_tag', 'tag': 'plant', 'value': 1,
        'desc': 'Botanist: +1 damage vs plant creatures.',
    },
    'reptile': {
        'kind': 'save_bonus', 'value': {'cat': 'CON', 'amount': 2},
        'desc': 'Cold-blood lore: +2 CON saves — shrug off petrifying gaze and venom.',
    },
}
