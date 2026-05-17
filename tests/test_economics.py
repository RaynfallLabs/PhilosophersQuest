"""Tests for the 2026 economics/trap system overhaul:

- Master Lockpick is permanent inventory item; no charges tracked
- Gold piles pool automatically on the same tile
- Unique items rarely floor-spawn (drop chance 0.5%/room) but appear in chests
  with tier-scaled probability
- Mimic monster picked by depth covers F1-100 with 5 mimic kinds
- Mimic chance scales with depth (6%/9%/12%/15%)
- Trap disarm uses AI quiz subject (post-2026-05-17 retune; reverted from a
  brief stint on economics so that AI = "special/unusual" mechanics overall)
- Shop haggle uses economics escalator-chain quiz, 10% discount per chain step
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


# ---------------------------------------------------------------------------
# Shop haggle discount — 10% per escalator-chain step, capped at 50%
# ---------------------------------------------------------------------------

def test_haggle_discount_per_chain_step():
    """Confirm the discount ladder matches the spec: 10% per chain, capped at 50%."""
    import main
    f = main.Game._haggle_discount_for_chain
    assert f(0) == 0
    assert f(1) == 10
    assert f(2) == 20
    assert f(3) == 30
    assert f(4) == 40
    assert f(5) == 50
    # Capped at 50 even if chain somehow exceeds 5 (defensive)
    assert f(6) == 50
    assert f(10) == 50
    # Negative chain (shouldn't happen, but guard against it)
    assert f(-1) == 0


def test_haggle_applies_discount_to_price():
    """The full discount applied to a 200-gold item."""
    import main
    apply = main.Game._apply_haggle_discount
    assert apply(200, 0) == 200      # no discount
    assert apply(200, 1) == 180      # 10% off
    assert apply(200, 5) == 100      # 50% off
    # Floor of 1 — discount never zeroes the price
    assert apply(1, 5) == 1


# ---------------------------------------------------------------------------
# Trap disarm — moved back to AI subject post-2026-05-17
# ---------------------------------------------------------------------------

def test_disarm_uses_ai_subject_not_economics():
    """The disarm quiz must invoke the AI subject and escalator_chain mode."""
    import inspect
    import main
    src = inspect.getsource(main.Game._try_disarm_trap)
    assert "subject='ai'" in src, "trap disarm must use AI subject"
    assert "escalator_chain" in src, "trap disarm must use escalator_chain mode"
    assert "max_chain=5" in src, "trap disarm chain must cap at 5"


def test_disarm_resolver_chain_ladder():
    """Validate the chain -> outcome mapping in _resolve_trap_disarm.

    Operates on a minimal harness — no Pygame, no level state, just dict
    manipulation, since the resolver is a pure mapper over trap state.
    """
    import main

    class _Harness:
        def __init__(self):
            self.dungeon_level = 1
            self._chronicle = []
            self._recalled_hints = []
            self.player = type('P', (), {'has_effect': lambda self_, e: False,
                                          'take_damage': lambda self_, a, t='physical': a,
                                          'is_dead': lambda self_: False})()
            class _D:
                traps = {}
                pits = set()
            self.dungeon = _D()
            self._adv_count = 0
        def add_message(self, *a, **kw): pass
        def _log_chronicle(self, *a, **kw): pass
        def _check_floor_trap(self, x, y):
            # Damage-only stub: pretend the trap fired and consume the dict entry.
            self.dungeon.traps.pop((x, y), None)
        def _advance_turn(self): self._adv_count += 1
        def _random_hint_for_disarm(self): return "test hint"

    def _make_trap():
        return {'type': 'bear_trap', 'damage': '1d4', 'damage_type': 'physical',
                'message': '!', 'revealed': True}

    # Chain 0: trap fires + extra turn lost (two _advance_turn calls)
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 0)
    assert (1, 1) not in h.dungeon.traps, "trap should have fired and been consumed"
    assert h._adv_count == 2, f"chain 0 = 2 advance_turn calls; got {h._adv_count}"

    # Chain 1: trap fires, one turn
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 1)
    assert (1, 1) not in h.dungeon.traps
    assert h._adv_count == 1

    # Chain 2: NO CHANGE — trap stays, no trigger, one turn burned
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 2)
    assert (1, 1) in h.dungeon.traps, "chain 2 must leave the trap untouched"
    t = h.dungeon.traps[(1, 1)]
    assert not t.get('rewired'), "chain 2 is not a rewire"
    assert not t.get('safe_for_player'), "chain 2 leaves the trap dangerous"
    assert h._adv_count == 1

    # Chain 3: clean disarm
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 3)
    assert (1, 1) not in h.dungeon.traps
    assert h._adv_count == 1

    # Chain 4: rewired
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 4)
    t = h.dungeon.traps[(1, 1)]
    assert t.get('rewired') is True
    assert t.get('safe_for_player') is True

    # Chain 5: rewired + hint recorded
    h = _Harness()
    h.dungeon.traps[(1, 1)] = _make_trap()
    main.Game._resolve_trap_disarm(h, (1, 1), 'bear trap', 5)
    t = h.dungeon.traps[(1, 1)]
    assert t.get('rewired') is True
    assert t.get('safe_for_player') is True
    assert len(h._recalled_hints) >= 1, "chain 5 should grant a random hint"


def test_rewired_trap_skips_player_in_check_floor_trap():
    """A trap flagged safe_for_player should be skipped by _check_floor_trap."""
    import inspect
    import main
    src = inspect.getsource(main.Game._check_floor_trap)
    # The early-out branch must exist.
    assert "safe_for_player" in src, \
        "_check_floor_trap must guard against rewired traps"
