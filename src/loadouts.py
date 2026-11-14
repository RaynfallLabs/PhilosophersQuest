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

Remembered pieces (Brandon 2026-11-14: "persist sets under the
quickswapping function if a weapon is dropped or thrown"). The weapon At
Your Back and every kit keep a piece that leaves the pack by being
dropped, thrown or stolen: while it is away the Kit, the @ sheet and the
Loadouts screen show it "(not carried)", and picked up again (a dead thief
gives it back) it is in its place again, with one line (back_line). A
piece sold, destroyed, used up or made into another object is let go for
good (let_go; the game lets go of a piece found nowhere in the world any
more: game_dressing.DressingMixin._sets_prune). The hero may still wear
or ready whatever he likes: readying another weapon simply replaces the
remembered one.

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


NOT_CARRIED = 'not carried'


def readied_memory(player):
    """The weapon At Your Back as remembered, with him or not (None: none).
    Player.readied_weapon is the same weapon only while it is in the pack."""
    return None if player is None else player.__dict__.get('_readied_weapon')


def carried_or_worn(player, item) -> bool:
    """Is ``item`` with the hero: in the pack, worn or in the hand?"""
    if player is None or item is None:
        return False
    if any(i is item for i in (player.__dict__.get('inventory') or ())):
        return True
    worn = getattr(player, 'worn_items', None)
    return callable(worn) and any(i is item for i in worn())


def kit_names_holding(player, item) -> list:
    """The names of the kits that hold ``item``, in order."""
    kits = None if player is None else player.__dict__.get('loadouts')
    if item is None or not valid(kits):
        return []
    return [k['name'] for k in kits if any(v is item for v in k['pieces'].values())]


def holds(player, item) -> bool:
    """Does the back or any kit remember ``item``?"""
    return item is not None and (readied_memory(player) is item
                                 or bool(kit_names_holding(player, item)))


def remembered(player) -> list:
    """Every remembered piece once: the weapon At Your Back, then the kits'."""
    out = []

    def add(it):
        if it is not None and all(it is not o for o in out):
            out.append(it)
    add(readied_memory(player))
    kits = None if player is None else player.__dict__.get('loadouts')
    if valid(kits):
        for k in kits:
            for slot in KIT_SLOTS:
                add(k['pieces'].get(slot))
    return out


def away(player, item) -> bool:
    """A remembered piece that is not with the hero now (dropped, thrown,
    stolen)."""
    return holds(player, item) and not carried_or_worn(player, item)


def away_pieces(player) -> list:
    return [it for it in remembered(player) if not carried_or_worn(player, it)]


def let_go(player, item) -> bool:
    """Forget ``item`` for good: off the back and out of every kit (it was
    sold, destroyed, used up or made into another thing). True when it was
    remembered anywhere."""
    if player is None or item is None:
        return False
    done = False
    if player.__dict__.get('_readied_weapon') is item:
        player.__dict__['_readied_weapon'] = None
        done = True
    kits = player.__dict__.get('loadouts')
    if valid(kits):
        for k in kits:
            pieces = k['pieces']
            for slot in [s for s, v in pieces.items() if v is item]:
                del pieces[slot]
                done = True
    return done


def and_list(words) -> str:
    """'Kit One', 'Kit One and Kit Two', 'Kit One, Kit Two and Kit Three'."""
    words = [str(w) for w in words]
    if len(words) <= 1:
        return ''.join(words)
    return ', '.join(words[:-1]) + ' and ' + words[-1]


def back_line(name: str, readied: bool, kit_names) -> str:
    """The one line when a remembered piece comes back into the pack."""
    kits = and_list(kit_names)
    if readied and kits:
        return f"The {name} is At Your Back again, and back in {kits}."
    if readied:
        return f"The {name} is At Your Back again."
    if kits:
        return f"The {name} is back in {kits}."
    return ''


def not_carried(name: str) -> str:
    """'Silver Mace (not carried)': a remembered piece that is away."""
    return f"{name} ({NOT_CARRIED})"


def clean_name(text: str, idx: int) -> str:
    """A kit's name as typed: spaces tidied, at most KIT_NAME_MAX letters,
    capitalised like every name (naming.proper_name); empty is its default."""
    text = ' '.join(str(text or '').split())[:KIT_NAME_MAX]
    if not text:
        return KIT_NAMES[idx]
    from naming import proper_name
    return proper_name(text)
