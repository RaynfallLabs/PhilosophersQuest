"""karma.adjust, the single karma entry point (DEEDS_KARMA_DESIGN 3 and 8.1).

Phase 1 ships with the gate OFF and must be behaviour-neutral: every old
mutation site, routed through adjust, gives exactly the karma the old inline
formula gave, at every starting value. The gate-ON rules are tested here too
(by switching the flag in memory) so Phase 3b inherits a proven engine.
"""
import copy
import os
import random
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import deeds  # noqa: E402
import karma  # noqa: E402


def _game(k=0, deepest=1, floor=None):
    return SimpleNamespace(karma=k, dungeon_level=floor or deepest, turn_count=0,
                           player=SimpleNamespace(deepest_floor_reached=deepest))


@pytest.fixture
def gate_on(monkeypatch):
    r = copy.deepcopy(karma.rules())
    r['gate_enabled'] = True
    monkeypatch.setattr(karma, '_RULES', r)
    return r


def test_shipped_gate_is_off():
    assert karma.gate_enabled() is False
    assert 'reckless' not in karma.KINDS            # Brandon, decision 9
    assert {c['id'] for c in karma.rules()['constancy']} >= {'temperance', 'faithful',
                                                             'discerning', 'steadfast'}
    assert karma.rules()['constancy_cap'] == 2


# ---------------------------------------------------------- gate-off parity

def _old_npc(k, d):            # game_encounters._apply_npc_choice, before
    return max(-10, min(10, k + d))


def _old_gyges(k):             # combat.py, Ring of Gyges, before
    return max(-10, k - 2)


def _old_penitent(k):          # combat.py, Penitent's Blade, before
    return k + 1 if k < 0 else k


@pytest.mark.parametrize('k', range(-10, 11))
def test_gate_off_parity_every_site(k):
    for d in (-2, -1, 1, 2):
        g = _game(k, deepest=35)
        karma.adjust(g, d, kind='legacy', source='npc')
        assert g.karma == _old_npc(k, d), (k, d)
    g = _game(k)
    karma.adjust(g, -2, kind='cruelty', source='ring_of_gyges')
    assert g.karma == _old_gyges(k)
    g = _game(k)
    karma.adjust(g, -2, kind='cruelty', source='emberpup_attack')
    assert g.karma == _old_npc(k, -2)
    g = _game(k)
    karma.adjust(g, 1, kind='legacy', source='emberpup_feed')
    assert g.karma == _old_npc(k, 1)
    g = _game(k)
    karma.adjust(g, 1, kind='recovery', source='penitents_blade')
    assert g.karma == _old_penitent(k)


def test_gate_off_never_absorbs_but_records_slots_and_ledger():
    g = _game(0, deepest=5)
    for _ in range(4):                               # four +1s in one block
        assert karma.adjust(g, 1, kind='legacy', source='a') == 1
    assert g.karma == 4
    assert g._deeds['karma']['slots'] == {1: 'a'}
    led = g._deeds['karma']['ledger']
    assert len(led) == 4 and all(e['applied'] == 1 and e['block'] == 1 for e in led)
    g = _game(10, deepest=15)
    assert karma.adjust(g, 1, kind='legacy', source='capped') == 0
    assert g._deeds['karma']['slots'] == {2: 'capped'}   # the block was earned all the same


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        karma.adjust(_game(), 1, kind='reckless', source='x')


# ---------------------------------------------------------- gate on

def test_gate_on_one_slot_per_block(gate_on):
    g = _game(0, deepest=12)
    assert karma.adjust(g, 1, kind='forgo', source='purses') == 1
    assert karma.adjust(g, 1, kind='judgment', source='priests') == 0     # absorbed
    assert g.karma == 1
    led = g._deeds['karma']['ledger']
    assert led[-1]['applied'] == 0 and led[-1]['requested'] == 1
    assert karma.adjust(g, 3, kind='stance', source='seed') == 0          # clamp to +1, absorbed
    g.player.deepest_floor_reached = 21
    assert karma.adjust(g, 5, kind='stance', source='seed') == 1          # clamped to +1


def test_gate_on_award_upstairs_lands_in_deepest_block(gate_on):
    g = _game(0, deepest=34, floor=8)               # walked back up to floor 8
    karma.adjust(g, 1, kind='forgo', source='x')
    assert g._deeds['karma']['slots'] == {4: 'x'}
    assert karma.adjust(g, 1, kind='forgo', source='y') == 0


def test_gate_on_oath_fills_earliest_open_slot(gate_on):
    g = _game(0, deepest=45)
    reg = deeds.ensure_register(g)
    reg['karma']['slots'].update({2: 'a', 5: 'b'})
    assert karma.adjust(g, 1, kind='oath', source='aldric', made_block=2) == 1
    assert reg['karma']['slots'][3] == 'aldric'
    reg['karma']['slots'][4] = 'c'
    assert karma.adjust(g, 1, kind='oath', source='gospel', made_block=3) == 0   # 3..5 all full
    assert karma.adjust(g, 1, kind='oath', source='dispatch', made_block=1) == 1
    assert reg['karma']['slots'][1] == 'dispatch'


def test_gate_on_negatives_full_and_clamped(gate_on):
    g = _game(-9)
    assert karma.adjust(g, -2, kind='betray', source='x') == -1
    assert g.karma == -10


def test_recovery_never_above_zero(gate_on):
    g = _game(-1)
    assert karma.adjust(g, 1, kind='recovery', source='blade') == 1 and g.karma == 0
    assert karma.adjust(g, 1, kind='recovery', source='blade') == 0 and g.karma == 0


def test_legacy_refused_with_gate_on(gate_on):
    with pytest.raises(ValueError):
        karma.adjust(_game(), 1, kind='legacy', source='x')


def _virtue(g, virtue, floor):
    reg = deeds.ensure_register(g)
    deeds.record(reg, f'flag.{virtue}.e{floor}', floor=floor, block=deeds.karma_block(floor),
                 source='t', tags=[f'virtue:{virtue}'], engine=True)


def test_constancy_once_per_rule_cap_two(gate_on):
    g = _game(0, deepest=50)
    g._chronicle = []
    for f in (5, 15, 25):
        _virtue(g, 'forgo', f)
        _virtue(g, 'steadfast', f)
    for f in (5, 15, 25, 35):
        _virtue(g, 'judged', f)
    paid = karma.evaluate_patterns(g)
    assert len(paid) == 2 and g.karma == 2
    assert karma.evaluate_patterns(g) == [] and g.karma == 2
    assert len(g._deeds['karma']['constancy']) == 2
    assert all(e['kind'] == 'soul' for e in g._chronicle)


def test_faithful_blocked_by_lapse_not_release(gate_on):
    def run(third):
        g = _game(0, deepest=40)
        g._chronicle = []
        reg = deeds.ensure_register(g)
        for i, f in enumerate((5, 15)):
            deeds.swear(reg, f'o{i}', to='x', what='y', floor=f, block=deeds.karma_block(f))
            deeds.keep_oath(reg, f'o{i}', floor=f + 2, block=deeds.karma_block(f + 2))
        deeds.swear(reg, 'o9', to='x', what='y', floor=30, block=3)
        third(reg, 'o9', floor=31, block=4)
        return karma.evaluate_patterns(g)
    assert run(deeds.release_oath) == ['faithful']
    assert run(deeds.lapse_oath) == []


def test_discerning_needs_four_passes_in_three_blocks(gate_on):
    g = _game(0, deepest=40)
    g._chronicle = []
    for f in (5, 6, 7, 8):                          # four, but one block
        _virtue(g, 'judged', f)
    assert karma.evaluate_patterns(g) == []
    _virtue(g, 'judged', 15)
    _virtue(g, 'judged', 25)
    assert karma.evaluate_patterns(g) == ['discerning']


def test_negative_pattern_pays_once(gate_on):
    g = _game(0, deepest=10)
    g._chronicle = []
    reg = deeds.ensure_register(g)
    for i in range(2):
        deeds.record(reg, f'broke.o{i}', floor=3, block=1, tags=['vice:betray'], engine=True)
    assert karma.evaluate_patterns(g) == ['turncoat'] and g.karma == -1
    assert karma.evaluate_patterns(g) == [] and g.karma == -1


def test_property_random_streams(gate_on):
    """2,000 random event streams: per block at most +1 gated positive
    applied, constancy at most +2, karma always inside -10..10, including
    walks back upstairs and Cow Level visits (floor 999)."""
    rng = random.Random(1234)
    kinds = ['forgo', 'judgment', 'oath', 'stance', 'betray', 'cruelty', 'recovery']
    for _ in range(2000):
        g = _game(0, deepest=1)
        g._chronicle = []
        reg = deeds.ensure_register(g)
        deepest = 1
        for _step in range(rng.randint(5, 60)):
            r = rng.random()
            if r < 0.3:
                deepest = min(100, deepest + rng.randint(0, 6))
                g.player.deepest_floor_reached = deepest
                g.dungeon_level = deepest
            elif r < 0.35:
                g.dungeon_level = 999                     # the Cow Level
            elif r < 0.4:
                g.dungeon_level = rng.randint(1, deepest)  # upstairs
            elif r < 0.5:
                f = g.dungeon_level if g.dungeon_level <= 100 else deepest
                deeds.record(reg, f'flag.t.e{_step}', floor=f, block=deeds.karma_block(deepest),
                             tags=[rng.choice(['virtue:forgo', 'virtue:kept', 'virtue:judged',
                                               'virtue:steadfast', 'vice:betray'])],
                             engine=True)
                karma.evaluate_patterns(g)
            else:
                kind = rng.choice(kinds)
                d = rng.choice([1, 1, 2]) if kind in karma.POSITIVE_GATED | {'recovery'} \
                    else -rng.choice([1, 2])
                mb = rng.randint(1, deeds.karma_block(deepest)) if kind == 'oath' else None
                karma.adjust(g, d, kind=kind, source='s', made_block=mb)
            assert -10 <= g.karma <= 10
        per_block = {}
        for e in reg['karma']['ledger']:
            if e['kind'] in karma.POSITIVE_GATED and e['applied'] > 0:
                assert e['applied'] == 1
        for b, src in reg['karma']['slots'].items():
            per_block.setdefault(b, 0)
            per_block[b] += 1
        assert all(v == 1 for v in per_block.values())
        gated = sum(e['applied'] for e in reg['karma']['ledger']
                    if e['kind'] in karma.POSITIVE_GATED and e['applied'] > 0)
        assert gated <= len(reg['karma']['slots']) <= 10
        assert sum(e['applied'] for e in reg['karma']['ledger'] if e['kind'] == 'constancy') <= 2


def test_recall_lore_hints_on_how_the_soul_is_weighed():
    """Brandon, decision 1: the number is hidden, so Recall Lore carries
    oblique hints on keeping your word, refusing a wrong gain, holding firm,
    blind kindness, and the once-per-stretch weighing. Never a number, never
    'karma' as a mechanic, spread across tiers."""
    import json
    import re
    from paths import data_path
    with open(data_path('data', 'hints.json'), encoding='utf-8') as f:
        hints = json.load(f)
    themes = {
        'word': 'A promise made in the dark',
        'forgo': 'Turning down a thing you could have taken',
        'firm': 'Hold firm when the hard questions come',
        'blind': 'A kindness given blind',
        'stretch': 'Each long stretch of the descent is weighed once',
    }
    found = {}
    for tier, lines in hints.items():
        for line in lines:
            for key, needle in themes.items():
                if needle in line:
                    found[key] = tier
                    assert not re.search(r'\d', line) and 'karma' not in line.lower(), line
    assert set(found) == set(themes)
    assert len(set(found.values())) >= 4
    for line in (ln for lines in hints.values() for ln in lines):
        assert 'karma' not in line.lower(), line


def test_judgment_tiers_unchanged():
    from npc_encounters import judge_karma
    expect = {}
    for k in range(-10, 11):
        expect[k] = ('abaddon_empowered' if k <= -6 else 'locusts_strengthened' if k < 0
                     else 'silence' if k == 0 else 'scales_granted' if k <= 7
                     else 'sword_and_scales')
    assert {k: judge_karma(k)[0] for k in range(-10, 11)} == expect
