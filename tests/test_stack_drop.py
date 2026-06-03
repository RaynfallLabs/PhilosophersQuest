"""Stackable-item drop/pickup tests for Philosopher's Quest.

Regression coverage for the bug where dropping a stack (e.g. iron bolts) and
picking it back up COMPOUNDED the count -- 50 -> 100 -> 200 -> ... -> 1000+.

Root cause: _do_drop_item decremented the inventory stack by 1 (via
remove_from_inventory) but appended the SAME object to the ground, aliasing one
item into both inventory and ground_items. On pickup, add_to_inventory found
that very object as its own "existing" stack and did count += count.

Fix: Player.drop_stack() returns a DETACHED object (the original when the whole
stack is dropped, or a fresh split copy for a partial drop), and
add_to_inventory() skips `existing is item` so a stray alias can never
self-merge. These tests exercise the pure inventory mechanic; the in-game
"how many to drop?" prompt is verified by play-test.
"""

import os
import sys
import copy

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _player():
    """Fresh player with an empty inventory (construction does not save)."""
    from main import Game
    g = Game(_screen(), player_name='__test_stack_drop__')
    g.player.inventory = []
    return g.player


def _ammo(count: int):
    """A detached ammo item with the given stack count."""
    from items import load_items
    proto = next(iter(load_items('ammo')), None)
    assert proto is not None, "no ammo items in JSON"
    a = copy.copy(proto)
    a.count = count
    return a


def test_stack_drop_pickup_does_not_compound():
    """Drop the whole stack and pick it up, five times. The count must stay 50
    -- the pre-fix bug doubled it every cycle (50 -> 100 -> ... -> 1600)."""
    p = _player()
    ammo = _ammo(50)
    assert p.add_to_inventory(ammo), "ammo should fit (weight check)"

    for _ in range(5):
        held = next(i for i in p.inventory if i.id == ammo.id)
        dropped = p.drop_stack(held, getattr(held, 'count', 1))
        assert dropped is not None
        assert p.add_to_inventory(dropped)

    stacks = [i for i in p.inventory if i.id == ammo.id]
    assert len(stacks) == 1, f"expected one merged stack, got {len(stacks)}"
    assert stacks[0].count == 50, f"count compounded to {stacks[0].count}"


def test_partial_stack_drop_splits_and_merges():
    """Dropping part of a stack shrinks the held stack and hands back a SEPARATE
    object; picking it back up merges to the original total with no aliasing."""
    p = _player()
    ammo = _ammo(50)
    assert p.add_to_inventory(ammo)

    held = next(i for i in p.inventory if i.id == ammo.id)
    dropped = p.drop_stack(held, 20)
    assert dropped is not held, "split must produce a detached object"
    assert dropped.count == 20
    assert held.count == 30

    assert p.add_to_inventory(dropped)
    stacks = [i for i in p.inventory if i.id == ammo.id]
    assert len(stacks) == 1
    assert stacks[0].count == 50


def test_drop_whole_stack_removes_from_inventory():
    """Dropping the full quantity returns the original object and removes it
    from inventory entirely (not a count-1 decrement)."""
    p = _player()
    ammo = _ammo(8)
    assert p.add_to_inventory(ammo)

    held = next(i for i in p.inventory if i.id == ammo.id)
    dropped = p.drop_stack(held, 8)
    assert dropped is held
    assert not any(i.id == ammo.id for i in p.inventory), "stack should be gone"


def test_add_to_inventory_never_self_merges():
    """The defensive guard: feeding add_to_inventory an object already in the
    inventory (the old aliasing scenario) must NOT double its count field."""
    p = _player()
    ammo = _ammo(50)
    assert p.add_to_inventory(ammo)
    p.add_to_inventory(ammo)   # same object handed back in -- the alias bug
    assert ammo.count == 50, f"self-merge doubled count to {ammo.count}"


def test_drop_stack_not_held_returns_none():
    """drop_stack on an item the player isn't carrying is a no-op."""
    p = _player()
    loose = _ammo(5)
    assert p.drop_stack(loose, 5) is None
