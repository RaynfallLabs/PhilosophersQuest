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
    """Stacking keys on the UNDERLYING BUC value, so an unidentified copy
    still merges with an identified stack of the same actual BUC."""
    pl = Player()
    pl.known_item_ids.add(_PID)
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=5))
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=0))   # fresh, unidentified
    held = [i for i in pl.inventory if i.id == _PID]
    assert len(held) == 1 and held[0].count == 2
    assert held[0].id_level == 5


def test_different_buc_stays_separate():
    """Merging mismatched BUC would silently drop the blessed effect
    (bug A7-5) — and under the True Name model the blessed copy stays
    a mystery until identified."""
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
