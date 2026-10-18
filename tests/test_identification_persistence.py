"""Per-instance identification under the True Name model (2026-08-06).

Type knowledge (known_item_ids) reveals an item's NAME on every copy, but
each instance keeps its own BUC/enchant secret until identified — so a
freshly-acquired copy of a known type must arrive UNSTAMPED (id_level 0,
buc_known False). Stacking still keys on the underlying BUC value, so an
unidentified copy merges into an identified stack only when the actual
BUC matches (and mismatched BUC stays separate — bug A7-5 guard).
"""
import copy

from items import load_items
from player import Player

_BASE_POTION = load_items('potion')[0]
_PID = _BASE_POTION.id


def _fresh(buc='uncursed', id_level=0):
    p = copy.copy(_BASE_POTION)
    p.buc = buc
    p.id_level = id_level
    p.buc_known = False
    p.count = 1
    return p


def test_known_type_does_not_stamp_a_fresh_instance():
    """The heart of the True Name model: a new copy of a known type keeps
    its own secrets (no auto id_level / buc_known stamping)."""
    pl = Player()
    pl.known_item_ids.add(_PID)
    incoming = _fresh(id_level=0)
    pl.add_to_inventory(incoming)
    held = [i for i in pl.inventory if i.id == _PID]
    assert held
    # Either it stayed a separate unidentified copy, or it merged into an
    # existing stack — here there is no existing stack, so it must be the
    # untouched incoming instance.
    assert held[0] is incoming
    assert held[0].id_level == 0
    assert held[0].buc_known is False


def test_known_same_buc_potions_merge():
    """Bug bash 4 call 8: copies merge only when the blessing is KNOWN on
    both. A copy of an UNKNOWN kind stays apart even when its hidden BUC
    matches (merging it, and refusing a different one, leaked the blessing);
    a copy whose blessing is known (altar, identify) joins the stack. A copy
    of a KNOWN kind is fully identified, blessing included (2026-10-18), so
    it joins too."""
    pl = Player()
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=5))
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=0))   # kind unknown
    held = [i for i in pl.inventory if i.id == _PID]
    assert len(held) == 2 and all(i.count == 1 for i in held)
    known = _fresh(buc='uncursed', id_level=0)
    known.buc_known = True
    pl.add_to_inventory(known)
    stack = next(i for i in held if i.id_level == 5)
    assert stack.count == 2 and known not in pl.inventory
    # The kind becomes known: the stray unknown copy is the same thing.
    pl.known_item_ids.add(_PID)
    assert pl.merge_known_stacks() == 1
    held = [i for i in pl.inventory if i.id == _PID]
    assert len(held) == 1 and held[0].count == 3 and held[0].id_level == 5
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=0))
    assert held[0].count == 4


def test_different_buc_stays_separate():
    """Merging mismatched BUC would silently drop the blessed effect
    (bug A7-5). The copy's own stored state is untouched; with the kind
    known it reads as blessed (one identification knows every copy)."""
    pl = Player()
    pl.known_item_ids.add(_PID)
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=5))
    pl.add_to_inventory(_fresh(buc='blessed', id_level=0))
    held = [i for i in pl.inventory if i.id == _PID]
    assert len(held) == 2
    blessed = next(i for i in held if i.buc == 'blessed')
    assert blessed.id_level == 0 and blessed.buc_known is False


def test_unknown_type_is_left_untouched():
    pl = Player()                                   # no known_item_ids entry
    pl.add_to_inventory(_fresh(id_level=0))
    held = [i for i in pl.inventory if i.id == _PID]
    assert held[0].id_level == 0 and held[0].buc_known is False
