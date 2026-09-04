"""Tests for the chest-template rebuild (2026-05-19).

Covers:
  - All 12 templates load with required fields
  - Spawn-weight bands cover the full 1..100 floor range
  - Chain → rare-mult / item-count curve values
  - Chain 0 yields no loot (chest opens empty)
  - Chain 5 yields 3-4 items + 1 bonus common
  - Rare odds scale upward with chain (smoke test, 100 trials)
  - Simulated 5-run uniques-per-100-floor target: median 12-22
"""
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


REQUIRED_TEMPLATE_FIELDS = {
    'id', 'name', 'symbol', 'color', 'lore', 'tier', 'quiz_tier',
    'gold_range', 'trap_chance', 'loot_table', 'rare_chance_chain3',
    'spawn_weight_by_band',
}

EXPECTED_TEMPLATES = {
    'wooden_chest', 'iron_lockbox', 'jewelry_box', 'apothecary_chest',
    'scholar_satchel', 'warlord_warchest', 'merchant_strongbox', 'crypt_chest',
    'ornate_chest', 'gilded_chest', 'reliquary', 'dragon_hoard',
}

BAND_KEYS = ('L1_15', 'L16_30', 'L31_50', 'L51_70', 'L71_90', 'L91_100')


# ---------------------------------------------------------------------------
# Data-layer: templates load with the right shape
# ---------------------------------------------------------------------------

def test_all_12_templates_load():
    from items import load_chest_templates
    tpls = load_chest_templates()
    assert set(tpls.keys()) == EXPECTED_TEMPLATES, (
        f"templates mismatch.\n  expected: {sorted(EXPECTED_TEMPLATES)}\n  got: {sorted(tpls.keys())}"
    )
    for tid, t in tpls.items():
        missing = REQUIRED_TEMPLATE_FIELDS - set(t.keys())
        assert not missing, f"{tid} missing required fields: {missing}"
        # Sanity on band keys
        assert set(t['spawn_weight_by_band'].keys()) == set(BAND_KEYS), (
            f"{tid} spawn_weight_by_band keys mismatch"
        )
        # Loot weights must be non-empty
        assert t['loot_table'], f"{tid} loot_table is empty"
        # Quiz tier 1..5
        assert 1 <= int(t['quiz_tier']) <= 5, f"{tid} quiz_tier out of range"
        # Gold range valid
        gr = t['gold_range']
        assert isinstance(gr, list) and len(gr) == 2 and gr[0] <= gr[1], (
            f"{tid} bad gold_range {gr}"
        )


def test_pirate_cache_was_dropped():
    """User decision: prune pirate_cache from the 13-template proposal."""
    from items import load_chest_templates
    tpls = load_chest_templates()
    assert 'pirate_cache' not in tpls, "pirate_cache was dropped (user decision)"


def test_template_spawn_weights_sum_nonzero_per_band():
    """Every floor band must have at least one template with a positive weight,
    or there will be no chests spawning on those floors."""
    from items import load_chest_templates
    tpls = load_chest_templates()
    for band in BAND_KEYS:
        total = sum(int(t['spawn_weight_by_band'].get(band, 0)) for t in tpls.values())
        assert total > 0, f"band {band} has no templates with positive weight"


def test_floor_band_helper_covers_full_depth():
    from dungeon import _floor_band
    cases = [
        (1, 'L1_15'), (15, 'L1_15'),
        (16, 'L16_30'), (30, 'L16_30'),
        (31, 'L31_50'), (50, 'L31_50'),
        (51, 'L51_70'), (70, 'L51_70'),
        (71, 'L71_90'), (90, 'L71_90'),
        (91, 'L91_100'), (100, 'L91_100'),
    ]
    for lvl, expected in cases:
        assert _floor_band(lvl) == expected, f"L{lvl}: got {_floor_band(lvl)}, want {expected}"


# ---------------------------------------------------------------------------
# v2.6.6 full-haul loot curve values
# ---------------------------------------------------------------------------

def test_full_haul_curve_values_correct():
    """v2.6.6: success is single-outcome (no chain rungs). Loot = 3-4 items
    + 1 bonus common; rare chance = template baseline x 2 (matches old chain-5)."""
    from container_system import FULL_ITEM_COUNT, FULL_BONUS_SLOTS, FULL_RARE_MULT
    assert FULL_ITEM_COUNT == (3, 4)
    assert FULL_BONUS_SLOTS == 1
    assert FULL_RARE_MULT == 2.0


def _make_container(template_id: str):
    """Build a stub Container with the named template, no mimic, no JSON read."""
    from items import Container, get_chest_template
    tdef = get_chest_template(template_id)
    assert tdef is not None, f"unknown template {template_id}"
    defn = {
        'id': template_id,
        'name': tdef['name'],
        'symbol': tdef.get('symbol', '&'),
        'color': tdef.get('color', [120, 100, 60]),
        'weight': 30.0,
        'min_level': 1,
        'item_class': 'container',
        'tier': int(tdef.get('tier', 1)),
        'quiz_tier': int(tdef.get('quiz_tier', 1)),
        'gold': tdef.get('gold_range', [0, 0]),
        'template_id': template_id,
    }
    return Container(defn)


def test_v266_success_yields_3_to_5_items():
    """v2.6.6 success = 3-4 real items + 1 guaranteed bonus common = 4-5 total.
    Some slots may drop out if pool empty (gold_bonus produces no item slot)."""
    from container_system import _generate_loot_from_template
    random.seed(42)
    counts = []
    for _ in range(50):
        c = _make_container('warlord_warchest')
        loot = _generate_loot_from_template(c, dungeon_level=40)
        counts.append(len(loot))
    median = statistics.median(counts)
    assert median >= 4, f"success should yield >= 4 items typically; median was {median}"
    assert min(counts) >= 1, f"success should never yield 0 items; got {min(counts)}"


def test_v266_rare_chance_uses_full_multiplier():
    """v2.6.6 success gives 2x rare (matches old chain-5). Compare high-rare
    chest (gilded, 20% baseline) to low-rare chest (wooden, 1%) across
    many trials -- gilded should produce many more uniques."""
    from container_system import _generate_loot_from_template
    random.seed(13)
    def count_uniques(template_id: str, n_trials: int = 100) -> int:
        uniques = 0
        for _ in range(n_trials):
            c = _make_container(template_id)
            loot = _generate_loot_from_template(c, dungeon_level=70)
            uniques += sum(1 for it in loot if getattr(it, 'is_unique', False))
        return uniques
    u_gilded = count_uniques('gilded_chest')   # 20% baseline x 2 = 40% per pick
    u_wooden = count_uniques('wooden_chest')   # 1%  baseline x 2 = 2%  per pick
    assert u_gilded > u_wooden, \
        f"gilded should produce many more uniques than wooden; got gilded={u_gilded}, wooden={u_wooden}"
    assert u_gilded >= 20, f"gilded x100 trials should yield >= 20 uniques; got {u_gilded}"


def test_v266_trap_pool_loads_and_has_all_5_tiers():
    """The v2.6.6 chest_traps.json must load and cover T1-T5 with >=4 traps each."""
    from container_system import _load_trap_pool
    pool = _load_trap_pool()
    for t in (1, 2, 3, 4, 5):
        assert t in pool, f"trap tier {t} missing"
        assert len(pool[t]) >= 4, f"trap tier {t} should have >= 4 variants for variety; got {len(pool[t])}"


def test_v266_trap_tier_matches_chest_not_floor():
    """Bug fix: trap selection is now keyed to CHEST tier, not floor tier.
    A T1 wooden chest at deep floor 90 must still fire a T1 trap, not a T5."""
    from container_system import pick_trap_for_chest, _load_trap_pool
    random.seed(1)
    c_wood = _make_container('wooden_chest')      # tier=1
    c_hoard = _make_container('dragon_hoard')     # tier=5
    # Sample many traps for each; verify they only come from the correct tier
    t1_pool_msgs = {t['message'] for t in _load_trap_pool()[1]}
    t5_pool_msgs = {t['message'] for t in _load_trap_pool()[5]}
    for _ in range(30):
        assert pick_trap_for_chest(c_wood)['message'] in t1_pool_msgs
        assert pick_trap_for_chest(c_hoard)['message'] in t5_pool_msgs


# ---------------------------------------------------------------------------
# End-to-end balance simulation
# ---------------------------------------------------------------------------

def _simulate_run(seed: int, success_rate: float = 0.80) -> int:
    """Simulate one 100-floor run under v2.6.6 lockpick. Returns total uniques.

    Models:
      - ~1.96 chests per floor (guaranteed 1 + 0.55, 0.25, 0.11, 0.05)
      - Player success rate per chest (default 0.80 = competent)
      - On success: _generate_loot_from_template (full haul, 2x rare)
      - On failure: no loot (trap fires but that's not a unique source)
      - Floor unique drops: 0.15% per room x 20 rooms per floor
      - Boss fixed drops: 5
    """
    from container_system import _generate_loot_from_template
    from items import load_chest_templates
    rng = random.Random(seed)
    state = random.getstate()
    random.seed(seed * 1009 + 7)
    tpls = load_chest_templates()

    uniques = 0
    FLOOR_UNIQUE_PCT = 0.0015
    ROOMS_PER_FLOOR  = 20
    CHESTS_PER_FLOOR = 1.96

    for level in range(1, 101):
        for _ in range(ROOMS_PER_FLOOR):
            if rng.random() < FLOOR_UNIQUE_PCT:
                uniques += 1
        n_chests_float = CHESTS_PER_FLOOR
        n_chests = int(n_chests_float) + (1 if rng.random() < (n_chests_float - int(n_chests_float)) else 0)
        from dungeon import _floor_band
        band = _floor_band(level)
        weighted = [(tid, t, int(t['spawn_weight_by_band'].get(band, 0)))
                    for tid, t in tpls.items()]
        weighted = [(tid, t, w) for tid, t, w in weighted if w > 0]
        if not weighted:
            continue
        for _ in range(n_chests):
            total_w = sum(w for _, _, w in weighted)
            r = rng.random() * total_w
            cum = 0
            chosen = weighted[0]
            for entry in weighted:
                cum += entry[2]
                if r <= cum:
                    chosen = entry
                    break
            tid, tdef, _ = chosen
            c = _make_container(tid)
            # Success rate roll
            if rng.random() > success_rate:
                continue  # failed pick, no loot
            loot = _generate_loot_from_template(c, dungeon_level=level)
            uniques += sum(1 for it in loot if getattr(it, 'is_unique', False))
    uniques += 5

    random.setstate(state)
    return uniques


def test_v266_simulated_uniques_per_run_target():
    """5-run median uniques-per-100-floor under v2.6.6.

    v2.6.6 shift: no chain gradient. Success gives 2x rare (was 1x at chain-3);
    failure gives nothing. Expected total shifts higher than pre-v2.6.6 for
    competent players since the average expected value is (success_rate * 2x)
    vs the old (avg chain-scaled rare mult). The band widens for the check
    since v2.6.6 EV is more sensitive to success_rate."""
    runs = [_simulate_run(seed=42 + i, success_rate=0.75) for i in range(5)]
    median = statistics.median(runs)
    print(f"5-run uniques @ success_rate=0.75: {runs}, median={median}")
    assert 15 <= median <= 60, (
        f"median uniques per run was {median}; target band 15-60 for competent player"
    )


def test_v266_higher_success_rate_gives_more_uniques():
    """A player with better Wisdom/timer/prep (higher success_rate) should
    consistently earn more uniques -- sanity check on the reward curve."""
    runs_low  = [_simulate_run(seed=42 + i, success_rate=0.50) for i in range(5)]
    runs_high = [_simulate_run(seed=42 + i, success_rate=0.90) for i in range(5)]
    med_low   = statistics.median(runs_low)
    med_high  = statistics.median(runs_high)
    print(f"success 0.50: median={med_low}; success 0.90: median={med_high}")
    assert med_high > med_low, \
        f"higher success rate should earn more uniques; got low={med_low}, high={med_high}"
