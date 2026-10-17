"""The Road (DEEDS_KARMA_DESIGN 5, tests 8.4): slots, roles, binding,
determinism, callback targets, and the shared random stream left alone.

Pure-module tests over thousands of seeds. No cross-run file is involved
(Brandon, decision 4: no memory across runs), so nothing needs pinning.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import road  # noqa: E402

SEEDS = range(10000)


def _seed(i):
    return (i * 0x9E3779B1 + 17) & 0xFFFFFFFFFFFFFFFF


def test_slots_count_gaps_and_forbidden_floors():
    for i in SEEDS:
        slots = road.build_slots(_seed(i))
        assert len(slots) == 45 and len(set(slots)) == 45
        assert slots == sorted(slots)
        assert slots[0] <= 3
        assert not set(slots) & {1, 20, 40, 60, 80, 99, 100, 999}
        assert max(b - a for a, b in zip(slots, slots[1:])) <= 3, slots


def test_roles_per_band():
    for i in range(3000):
        s = _seed(i)
        slots = road.build_slots(s)
        roles = road.assign_roles(s, slots)
        for band in range(1, 11):
            mine = [f for f in slots if road.band_of(f) == band]
            by = {r: [f for f in mine if roles[f]['role'] == r] for r in ('anchor', 'medium', 'high')}
            assert len(by['anchor']) == 1, (band, mine)
            lo, hi = road.ANCHOR_RANGE[band]
            assert lo <= by['anchor'][0] <= hi
            assert len(by['medium']) == 1
            if band in (2, 4, 6, 8, 10):
                assert len(by['high']) == 1
                if band == 2:
                    assert by['high'][0] >= 15
            else:
                assert not by['high']
        counts = [r['role'] for r in roles.values()]
        assert counts.count('anchor') == 10 and counts.count('medium') == 10
        assert counts.count('high') == 5 and counts.count('light') == 20


def test_emberpup_and_black_knight_floors_hold_no_medium_or_high_slot():
    rng = random.Random(3)
    for i in range(3000):
        s = _seed(i)
        ember = rng.randint(3, 8)
        knight = rng.randint(15, 19)
        st = road.new_state(s, enabled=True, secret_floors=[ember, knight])
        for f in (ember, knight):
            slot = st['slots'].get(f)
            if slot is not None:
                assert slot['role'] in ('anchor', 'light'), (f, slot)
        # band 2 still has its high slot whenever another floor >= 15 exists
        b2 = [f for f in st['slots'] if road.band_of(f) == 2 and f >= 15 and f != knight]
        highs = [f for f, v in st['slots'].items() if road.band_of(f) == 2 and v['role'] == 'high']
        if any(st['slots'][f]['role'] != 'anchor' for f in b2):
            assert len(highs) == 1


def _fixture_pool():
    pool = []
    for i in range(60):
        lo = 1 + (i * 3) % 90
        pool.append({'tag': f'fx_{i}', 'role': 'story', 'stakes': ('light', 'medium', 'high')[i % 3],
                     'band': [lo, lo + 15]})
    pool.append({'tag': 'fx_cb', 'role': 'story', 'stakes': 'light', 'band': [1, 100],
                 'callback_only': True})
    return pool


def test_binding_is_deterministic_and_never_repeats_a_tag():
    import npc_encounters
    pool = _fixture_pool()
    for i in range(300):
        s = _seed(i)
        runs = []
        for _ in range(2):
            st = road.new_state(s, enabled=True)
            anchors = road.bind_anchors(st, npc_encounters.ENCOUNTERS)
            bound = {f: e['tag'] for f, e in anchors.items()}
            for f in sorted(st['slots']):
                e = road.bind_slot(st, f, pool)
                if e is not None:
                    bound[f] = e['tag']
            runs.append((bound, list(st['used_tags'])))
        assert runs[0] == runs[1]
        tags = runs[0][1]
        assert len(tags) == len(set(tags))
        assert 'fx_cb' not in tags                      # callback_only is never drawn


def test_anchors_bind_inside_their_block_with_a_fallback_for_triggered_ones():
    import npc_encounters
    by_tag = {e['tag']: e for e in npc_encounters.ENCOUNTERS}
    saw_fallback = 0
    for i in range(500):
        st = road.new_state(_seed(i), enabled=True)
        anchors = road.bind_anchors(st, npc_encounters.ENCOUNTERS)
        assert len(anchors) == 10
        for f, e in anchors.items():
            assert e['block'] == road.band_of(f)
            fb = st['slots'][f]['fallback']
            if e.get('trigger_item'):
                assert fb and not by_tag[fb].get('trigger_item')
                saw_fallback += 1
            else:
                assert fb is None
    assert saw_fallback > 50


def test_an_empty_pool_falls_back_to_a_lighter_stake_then_stays_empty():
    st = road.new_state(_seed(1), enabled=True)
    high = next(f for f, v in st['slots'].items() if v['role'] == 'high')
    light_only = [{'tag': 'fx_l', 'role': 'story', 'stakes': 'light', 'band': [1, 100]}]
    assert road.bind_slot(st, high, light_only)['tag'] == 'fx_l'
    other = next(f for f, v in st['slots'].items() if v['role'] == 'high' and f != high)
    assert road.bind_slot(st, other, light_only) is None        # used, and nothing else
    assert st['slots'][other]['bound'] is None
    # requires (the allowed hook) is honoured at bind time
    st2 = road.new_state(_seed(2), enabled=True)
    lf = next(f for f, v in st2['slots'].items() if v['role'] == 'light')
    assert road.bind_slot(st2, lf, light_only, allowed=lambda e: False) is None


def test_callback_targets_avoid_busy_boss_and_visited_floors():
    for i in range(3000):
        s = _seed(i)
        st = road.new_state(s, enabled=True)
        busy = road.busy_floors(st)
        d = 1 + i % 90
        t = road.pick_target(s, f'cb:x:{i}', d + 1, d + 20, deepest=d, blocked=busy)
        if t is None:
            continue
        assert d < t <= d + 20
        assert t not in busy and t not in (20, 40, 60, 80, 99, 100, 999)
        # a delayed reward may take a boss floor, never 99 or 100
        t2 = road.pick_target(s, f'dl:x:{i}', d + 1, d + 20, deepest=d, allow_boss=True)
        assert t2 is None or (d < t2 <= min(98, d + 20))
    # the target encounter's own band is kept when it overlaps
    for i in range(500):
        t = road.pick_target(_seed(i), f'cb:lion:{i}', 12, 34, deepest=8, band=[22, 34])
        assert 22 <= t <= 34
    assert road.pick_target(1, 'k', 99, 100, deepest=98) is None


def test_building_the_road_leaves_the_shared_random_stream_alone():
    import npc_encounters
    random.seed(1234)
    before = random.getstate()
    s = road.roll_seed()
    st = road.new_state(s, enabled=True, secret_floors=[5, 17])
    road.bind_anchors(st, npc_encounters.ENCOUNTERS)
    for f in sorted(st['slots']):
        road.bind_slot(st, f, _fixture_pool())
    road.pick_target(s, 'cb', 3, 30, deepest=2)
    assert random.getstate() == before
    random.seed(1234)
    assert road.roll_seed() == s                      # repeatable for a seeded game


def test_old_save_state_is_a_disabled_road():
    st = road.ensure_state(None)
    assert st['enabled'] is False and st['slots'] == {} and isinstance(st['seed'], int)
    st = road.ensure_state({'v': 1, 'enabled': True, 'seed': 5,
                            'slots': {'12': {'role': 'light'}}, 'used_tags': []})
    assert 12 in st['slots']
