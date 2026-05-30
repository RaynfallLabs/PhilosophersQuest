"""Tests for the carry-scope mastery bonus mechanic.

Spec (user direction 2026-05-29):
- Items with `slot: "none"` and a stat_bonus mastery (Charmander
  Stuffie +2 CON, Dreamspun Sketchbook +2 INT) can't be equipped
- Their mastery must be CLAIMED first (Tier-5 identify chain)
- Once mastered, the bonus applies WHILE the item is in inventory
  and removes when the item is dropped/lost
- Re-applies if the item is picked up again (e.g., dropped on a floor
  and re-grabbed)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _load_charmander_blessing() -> dict:
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    return d['charmander_stuffie']['mastery_blessing']


def test_charmander_blessing_has_carry_scope():
    """The Charmander Stuffie's mastery must be marked scope=carry so
    the bonus applies from inventory rather than at one-shot claim."""
    mb = _load_charmander_blessing()
    assert mb.get('scope') == 'carry', (
        "Charmander Stuffie mastery_blessing.scope must be 'carry' so "
        "the +2 CON applies from inventory rather than as a one-shot at "
        "mastery-claim time"
    )


def test_dreamspun_blessing_has_carry_scope():
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    mb = d['dreamspun_sketchbook']['mastery_blessing']
    assert mb.get('scope') == 'carry'


def test_refresh_applies_bonus_when_item_in_inventory_and_mastered():
    """Walk the mechanic end-to-end: mark mastery unlocked + put item
    in inventory + call refresh -> stat increases by amount."""
    from player import Player

    class _StubItem:
        def __init__(self, item_id):
            self.id = item_id
            self.name = item_id
            self.weight = 0.5

    p = Player()
    base_con = p.CON
    base_max_hp = p.max_hp
    # Register the mastery first (this is what _claim_mastery does)
    p.unlocked_masteries['charmander_stuffie'] = {
        'kind': 'accessory_stat_bonus',
        'value': {'stat': 'CON', 'amount': 2},
        'scope': 'carry',
        'desc': 'Charmander +2 CON while carried.',
    }
    # Manually put it in inventory (bypass weight checks for the test)
    p.inventory.append(_StubItem('charmander_stuffie'))
    # Refresh applies the bonus
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2, f"CON should be {base_con+2}; got {p.CON}"
    assert p.max_hp == base_max_hp + 2
    assert 'charmander_stuffie' in p.active_carry_bonuses


def test_refresh_removes_bonus_when_item_leaves_inventory():
    """Pick up + apply, then drop -> bonus reverses."""
    from player import Player

    class _StubItem:
        def __init__(self, item_id):
            self.id = item_id
            self.name = item_id
            self.weight = 0.5

    p = Player()
    base_con = p.CON
    p.unlocked_masteries['charmander_stuffie'] = {
        'kind': 'accessory_stat_bonus',
        'value': {'stat': 'CON', 'amount': 2},
        'scope': 'carry',
        'desc': 'Charmander +2 CON while carried.',
    }
    stuffie = _StubItem('charmander_stuffie')
    p.inventory.append(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con + 2

    # Drop it
    p.inventory.remove(stuffie)
    p.refresh_carry_bonuses()
    assert p.CON == base_con, "dropping the mastered item must remove the bonus"
    assert 'charmander_stuffie' not in p.active_carry_bonuses


def test_refresh_is_idempotent_against_double_application():
    """Calling refresh multiple times must NOT stack the bonus."""
    from player import Player

    class _StubItem:
        def __init__(self, item_id):
            self.id = item_id
            self.name = item_id
            self.weight = 0.5

    p = Player()
    base_con = p.CON
    p.unlocked_masteries['charmander_stuffie'] = {
        'kind': 'accessory_stat_bonus',
        'value': {'stat': 'CON', 'amount': 2},
        'scope': 'carry',
        'desc': '',
    }
    p.inventory.append(_StubItem('charmander_stuffie'))
    for _ in range(5):
        p.refresh_carry_bonuses()
    assert p.CON == base_con + 2, (
        f"5 refreshes must not stack; expected {base_con+2}, got {p.CON}"
    )


def test_refresh_reapplies_after_pickup_drop_pickup_cycle():
    """Carry/drop/carry cycle must end at +bonus applied."""
    from player import Player

    class _StubItem:
        def __init__(self, item_id):
            self.id = item_id
            self.name = item_id
            self.weight = 0.5

    p = Player()
    base_con = p.CON
    p.unlocked_masteries['charmander_stuffie'] = {
        'kind': 'accessory_stat_bonus',
        'value': {'stat': 'CON', 'amount': 2},
        'scope': 'carry',
        'desc': '',
    }
    stuffie = _StubItem('charmander_stuffie')
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


def test_unmastered_carry_item_does_not_apply():
    """If the player has the item in inventory but HASN'T claimed
    mastery (Tier-5 chain), no bonus applies. The mastery is the gate."""
    from player import Player

    class _StubItem:
        def __init__(self, item_id):
            self.id = item_id
            self.name = item_id
            self.weight = 0.5

    p = Player()
    base_con = p.CON
    # unlocked_masteries deliberately EMPTY — mastery not claimed
    p.inventory.append(_StubItem('charmander_stuffie'))
    p.refresh_carry_bonuses()
    assert p.CON == base_con, "no mastery = no bonus, even with item carried"


def test_add_to_inventory_triggers_refresh():
    """add_to_inventory must call refresh_carry_bonuses so picking up
    a mastered carry-item applies the bonus automatically."""
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
