"""Tests for the 2026 economics/trap system overhaul:

- Master Lockpick is permanent inventory item; no charges tracked
- Gold piles pool automatically on the same tile
- Unique items rarely floor-spawn (drop chance 0.5%/room) but appear in chests
  with tier-scaled probability
- Mimic monster picked by depth covers F1-100 with 5 mimic kinds
- Mimic chance scales with depth (6%/9%/12%/15%)
- Trap disarm uses economics quiz subject (not AI)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Gold pooling
# ---------------------------------------------------------------------------

def test_gold_piles_pool_on_same_tile():
    from items import add_gold_to_tile, GoldPile
    ground = []
    add_gold_to_tile(ground, 10, 5, 5)
    add_gold_to_tile(ground, 25, 5, 5)
    add_gold_to_tile(ground, 7, 5, 5)
    gold_piles = [g for g in ground if isinstance(g, GoldPile)]
    assert len(gold_piles) == 1, "all three deposits should pool"
    assert gold_piles[0].amount == 42, f"expected 42; got {gold_piles[0].amount}"


def test_gold_piles_stay_separate_on_different_tiles():
    from items import add_gold_to_tile, GoldPile
    ground = []
    add_gold_to_tile(ground, 10, 5, 5)
    add_gold_to_tile(ground, 25, 5, 6)
    add_gold_to_tile(ground, 7, 6, 5)
    gold_piles = [g for g in ground if isinstance(g, GoldPile)]
    assert len(gold_piles) == 3, "different tiles should NOT pool"


def test_gold_pile_name_refreshes_with_amount():
    from items import add_gold_to_tile
    ground = []
    p = add_gold_to_tile(ground, 1, 0, 0)
    assert p.name == "1 gold coin"
    add_gold_to_tile(ground, 5, 0, 0)
    assert p.name == "6 gold coins"


def test_zero_or_negative_gold_creates_nothing():
    from items import add_gold_to_tile
    ground = []
    result = add_gold_to_tile(ground, 0, 5, 5)
    assert result is None
    assert ground == []


# ---------------------------------------------------------------------------
# Container loot — uniques appear in chests with tier-scaled probability
# ---------------------------------------------------------------------------

def test_unique_chance_escalates_with_chest_tier():
    """T1 chest: 0% unique; T5: 40%."""
    from container_system import _TIER_LOOT_CFG
    chances = [_TIER_LOOT_CFG[t]['unique_chance'] for t in (1, 2, 3, 4, 5)]
    assert chances == sorted(chances), f"unique_chance should escalate: {chances}"
    assert _TIER_LOOT_CFG[1]['unique_chance'] == 0.00
    assert _TIER_LOOT_CFG[5]['unique_chance'] == 0.40


def test_tier_5_chest_legendary_flag_only_tier():
    from container_system import _TIER_LOOT_CFG
    for t in (1, 2, 3, 4):
        assert not _TIER_LOOT_CFG[t]['legendary'], f"T{t} should not allow legendary"
    assert _TIER_LOOT_CFG[5]['legendary'] is True


# ---------------------------------------------------------------------------
# Mimic tier table — 5 mimic kinds spanning F1-100
# ---------------------------------------------------------------------------

def test_mimic_tier_table_covers_full_depth():
    """Spot-check the level → mimic-kind mapping in _spawn_mimic."""
    from container_system import _spawn_mimic
    import json
    with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'monsters.json'),
              encoding='utf-8') as f:
        all_defs = json.load(f)
    # Required mimic kinds for the 5 tiers
    required = ['mimic', 'greater_mimic', 'lurking_horror', 'gilded_mimic', 'abyssal_mimic']
    for kind in required:
        assert kind in all_defs, f"missing mimic kind: {kind}"

    # Stub container with x/y attributes
    class C:
        x, y = 5, 5
    monsters = []
    # Each band selects the right mimic
    cases = [
        (10, 'mimic'),
        (30, 'greater_mimic'),
        (50, 'lurking_horror'),
        (70, 'gilded_mimic'),
        (90, 'abyssal_mimic'),
    ]
    for level, expected_kind in cases:
        monsters.clear()
        _spawn_mimic(C(), monsters, level)
        assert monsters, f"no mimic spawned at level {level}"
        assert monsters[-1].kind == expected_kind, (
            f"L{level}: expected {expected_kind}; got {monsters[-1].kind}")


# ---------------------------------------------------------------------------
# Lockpick system — charges removed; quiz is the sole gate
# ---------------------------------------------------------------------------

def test_attempt_lockpick_does_not_require_charges():
    """The Master Lockpick is permanent — no charges check."""
    from container_system import attempt_lockpick

    # Inspect: function source should not reference lockpick_charges
    import inspect
    src = inspect.getsource(attempt_lockpick)
    assert 'lockpick_charges' not in src, \
        "attempt_lockpick should not gate on lockpick_charges"
