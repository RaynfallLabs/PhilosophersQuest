"""Tests for the carry-bonus mechanic (mastery gate removed 2026-08-06).

Spec:
- Items with `slot: "none"` and a `carry_bonus` field (Charmander
  Stuffie +2 CON, Dreamspun Sketchbook +2 INT) can't be equipped
- The bonus applies WHILE the item is in inventory and removes when
  the item is dropped/lost — no mastery claim required (the mastery
  system was retired with the one-question identify redesign)
- Re-applies if the item is picked up again (e.g., dropped on a floor
  and re-grabbed)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


class _StubItem:
    def __init__(self, item_id, carry_bonus=None):
        self.id = item_id
        self.name = item_id
        self.weight = 0.5
        self.carry_bonus = carry_bonus


def _stuffie():
    return _StubItem('charmander_stuffie', {'stat': 'CON', 'amount': 2})


def test_charmander_json_has_carry_bonus():
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    assert d['charmander_stuffie'].get('carry_bonus') == {'stat': 'CON', 'amount': 2}
    assert 'mastery_blessing' not in d['charmander_stuffie']


def test_dreamspun_json_has_carry_bonus():
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    assert d['dreamspun_sketchbook'].get('carry_bonus') == {'stat': 'INT', 'amount': 2}
    assert 'mastery_blessing' not in d['dreamspun_sketchbook']


def test_refresh_applies_bonus_when_item_in_inventory():
    """Walk the mechanic end-to-end: put item in inventory + call
    refresh -> stat increases by amount."""
    from player import Player

    p = Player()
    base_con = p.CON
    base_max_hp = p.max_hp
    # Manually put it in inventory (bypass weight checks for the test)
    p.inventory.append(_stuffie())
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2, f"CON should be {base_con+2}; got {p.CON}"
    assert p.max_hp == base_max_hp + 2
    assert 'charmander_stuffie' in p.active_carry_bonuses


def test_refresh_removes_bonus_when_item_leaves_inventory():
    """Pick up + apply, then drop -> bonus reverses."""
    from player import Player

    p = Player()
    base_con = p.CON
    stuffie = _stuffie()
    p.inventory.append(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2

    # Drop it
    p.inventory.remove(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con, "dropping the keepsake must remove the bonus"
    assert 'charmander_stuffie' not in p.active_carry_bonuses


def test_refresh_is_idempotent_against_double_application():
    """Calling refresh multiple times must NOT stack the bonus."""
    from player import Player

    p = Player()
    base_con = p.CON
    p.inventory.append(_stuffie())
    for _ in range(5):
        p.refresh_carry_bonuses()
    assert p.CON == base_con + 2, (
        f"5 refreshes must not stack; expected {base_con+2}, got {p.CON}"
    )


def test_refresh_reapplies_after_pickup_drop_pickup_cycle():
    """Carry/drop/carry cycle must end at +bonus applied."""
    from player import Player

    p = Player()
    base_con = p.CON
    stuffie = _stuffie()
    # cycle 1: pickup
    p.inventory.append(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2
    # drop
    p.inventory.remove(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con
    # cycle 2: pickup again
    p.inventory.append(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2


def test_item_without_carry_bonus_does_nothing():
    """A plain item with no carry_bonus field never touches stats."""
    from player import Player

    p = Player()
    base_con = p.CON
    p.inventory.append(_StubItem('plain_rock'))
    p.refresh_carry_bonuses()
    assert p.CON == base_con


def test_add_to_inventory_triggers_refresh():
    """add_to_inventory must call refresh_carry_bonuses so picking up
    a keepsake applies the bonus automatically."""
    import inspect
    from player import Player
    src = inspect.getsource(Player.add_to_inventory)
    assert 'refresh_carry_bonuses' in src, (
        "add_to_inventory must call refresh_carry_bonuses on success"
    )


def test_remove_from_inventory_triggers_refresh():
    """Symmetric: remove_from_inventory must also refresh."""
    import inspect
    from player import Player
    src = inspect.getsource(Player.remove_from_inventory)
    assert 'refresh_carry_bonuses' in src
