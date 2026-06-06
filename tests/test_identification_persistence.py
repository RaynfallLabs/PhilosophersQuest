"""Item-type identification persists to newly-acquired copies (2026-06-06).

Bug the user hit: after identifying 'Potion of Healing' (its id added to
known_item_ids), a LATER-acquired potion of the same type showed its true name
yet arrived at id_level 0 ("(0/5)") and refused to stack. Root cause: nothing
reconciled the per-instance id_level from the global known-type set at
pickup/spawn — only identify-time propagation did. Player.add_to_inventory now
stamps every incoming known-type item via reconcile_item_identification().
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


def test_known_type_stamps_a_fresh_instance():
    pl = Player()
    pl.known_item_ids.add(_PID)
    pl.add_to_inventory(_fresh(id_level=0))         # arrives unidentified
    held = [i for i in pl.inventory if i.id == _PID]
    assert held and held[0].id_level == 5           # not "(0/5)"
    assert held[0].buc_known is True


def test_known_same_buc_potions_merge():
    pl = Player()
    pl.known_item_ids.add(_PID)
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=5))
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=0))   # fresh, unidentified
    held = [i for i in pl.inventory if i.id == _PID]
    assert len(held) == 1 and held[0].count == 2
    assert held[0].id_level == 5


def test_different_buc_stays_separate_but_identified():
    pl = Player()
    pl.known_item_ids.add(_PID)
    pl.add_to_inventory(_fresh(buc='uncursed', id_level=5))
    pl.add_to_inventory(_fresh(buc='blessed', id_level=0))
    held = [i for i in pl.inventory if i.id == _PID]
    # Merging mismatched BUC would silently drop the blessed effect (bug A7-5).
    assert len(held) == 2
    blessed = next(i for i in held if i.buc == 'blessed')
    assert blessed.id_level == 5 and blessed.buc_known is True   # not a mystery 0/5


def test_unknown_type_is_left_untouched():
    pl = Player()                                   # no known_item_ids entry
    pl.add_to_inventory(_fresh(id_level=0))
    held = [i for i in pl.inventory if i.id == _PID]
    assert held[0].id_level == 0 and held[0].buc_known is False
