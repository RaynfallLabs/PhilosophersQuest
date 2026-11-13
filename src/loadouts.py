"""Loadouts: three saved kits (winning-build plan 3.4, 2026-11-13).

A kit is a name and the pieces it holds, by slot: the wielded weapon, the
weapon At Your Back, the shield, the eight armour slots, the amulet, the
belt and the rings. It holds the very objects it was saved with, so "the
blessed iron helm" is that helm and not another (Player.loadouts, saved
with the run; one pickle keeps the references). A slot empty when the kit
was saved is not part of it: putting the kit on leaves that slot alone.

Putting a kit on is game_dressing.DressingMixin._kit_plan / _kit_wear: it
takes the sum of its pieces' turns; a piece not in the pack is skipped and
a piece not known by hand is refused.

Pure data: no pygame, no game state.
"""
from __future__ import annotations

KIT_COUNT = 3
KIT_NAMES = ('Kit One', 'Kit Two', 'Kit Three')
KIT_NAME_MAX = 18
KIT_ARMOR_SLOTS = ('head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt')
# The slots a kit covers, in the order the Loadouts screen lists them.
KIT_SLOT_LABELS = {
    'weapon': 'Weapon', 'readied': 'At Your Back', 'shield': 'Shield',
    'head': 'Head', 'body': 'Body', 'arms': 'Arms', 'hands': 'Hands', 'legs': 'Legs',
    'feet': 'Feet', 'cloak': 'Cloak', 'shirt': 'Shirt', 'amulet': 'Amulet', 'belt': 'Belt',
    'ring_0': 'Ring 1', 'ring_1': 'Ring 2', 'ring_2': 'Ring 3', 'ring_3': 'Ring 4',
}
KIT_SLOTS = tuple(KIT_SLOT_LABELS)


def default_kits() -> list:
    """Three empty kits, named Kit One, Kit Two and Kit Three."""
    return [{'name': n, 'pieces': {}} for n in KIT_NAMES]


def valid(kits) -> bool:
    return (isinstance(kits, list) and len(kits) == KIT_COUNT
            and all(isinstance(k, dict) and isinstance(k.get('pieces'), dict)
                    and isinstance(k.get('name'), str) for k in kits))


def clean_name(text: str, idx: int) -> str:
    """A kit's name as typed: spaces tidied, at most KIT_NAME_MAX letters,
    capitalised like every name (naming.proper_name); empty is its default."""
    text = ' '.join(str(text or '').split())[:KIT_NAME_MAX]
    if not text:
        return KIT_NAMES[idx]
    from naming import proper_name
    return proper_name(text)
