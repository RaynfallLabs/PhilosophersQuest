"""Maths grade curve (slice 9, 2026-11-13).

Brandon: "math questions are legitimately tuned to tier to represent a
smooth grade progression curve for mental math, and with practice, kids
can get faster with higher tiers." Every maths question has a school-grade
score (tools/balance/math_difficulty.py); every tier is a band of grades
(tools/balance/math_grade_curve.json: T1 grades 1-2, T2 3-4, T3 4-5,
T4 6-7, T5 7-8); tools/balance/math_grade_curve.py moves or replaces what
does not fit. docs/quiz/math_grade_curve.md has the table.
"""
import json
import statistics
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))
sys.path.insert(0, str(_ROOT))

from tools.balance import math_difficulty as md  # noqa: E402
from tools.balance import math_grade_curve as mgc  # noqa: E402
from tools.balance.math_topics import ALL_TOPICS, topic_for_context  # noqa: E402

_BANK = json.loads((_ROOT / 'data' / 'questions' / 'math.json').read_text(encoding='utf-8'))
_TODAY = {1: 488, 2: 560, 3: 422, 4: 495, 5: 450}      # the tiers before the curve (v3.4.0)


@lru_cache(maxsize=1)
def _scores() -> dict[int, list[float]]:
    by = {t: [] for t in range(1, 6)}
    for q in _BANK:
        by[q['tier']].append(md.score(q))
    return {t: sorted(v) for t, v in by.items()}


# ----------------------------------------------------------------- the bank

def test_every_question_scores_inside_its_tier_band():
    out = []
    for q in _BANK:
        s = md.score(q)
        if not md.in_band(s, q['tier']):
            out.append((q['tier'], s, q['question']))
    assert not out, out[:10]


def test_each_tier_median_is_strictly_above_the_one_below():
    medians = [statistics.median(_scores()[t]) for t in range(1, 6)]
    assert all(a < b for a, b in zip(medians, medians[1:])), medians


def test_every_topic_maps_to_a_grade_band():
    table = md.load_table()
    assert set(table['topics']) == set(ALL_TOPICS)
    for topic, entry in table['topics'].items():
        assert entry['tiers'], topic
        for tier, slot in entry['tiers'].items():
            assert 1 <= int(tier) <= 5, (topic, tier)
            assert slot['grades'] and slot['standard'] and slot['plain'], (topic, tier)
    for q in _BANK:
        assert q['tier'] in md.allowed_tiers(q['topic']), (q['tier'], q['topic'], q['question'])


def test_tier_counts_stay_within_ten_percent_of_today():
    counts = Counter(q['tier'] for q in _BANK)
    for tier, n in _TODAY.items():
        assert abs(counts[tier] - n) <= 0.10 * n, (tier, counts[tier], n)


def test_no_trivial_question_above_tier_one():
    trivial = [(q['tier'], q['question']) for q in _BANK if q['tier'] > 1 and md.rate(q).trivial]
    assert not trivial, trivial[:10]


def test_no_stem_sits_in_two_tiers():
    tiers = {}
    for q in _BANK:
        tiers.setdefault(q['question'].strip(), set()).add(q['tier'])
    assert [s for s, t in tiers.items() if len(t) > 1] == []


def test_every_answer_is_right_and_no_other_choice_is():
    bad = [(q['question'], md.check_answer(q)) for q in _BANK if md.check_answer(q)]
    assert not bad, bad[:10]


def test_tiers_join_without_a_cliff_and_spread_inside():
    """The hardest question of a tier and the easiest of the next are less
    than 0.4 of a grade apart (the widest seam is tier 1 to 2, where
    multiplication starts at grade 3), and each tier spans 1.5 grades."""
    sc = _scores()
    for t in range(1, 5):
        assert sc[t + 1][0] - sc[t][-1] < 0.4, (t, sc[t][-1], sc[t + 1][0])
    for t in range(1, 6):
        assert sc[t][-1] - sc[t][0] >= 1.5, (t, sc[t][0], sc[t][-1])


def test_bands_climb_and_touch():
    for t in range(1, 5):
        lo, hi = md.tier_band(t)
        lo2, hi2 = md.tier_band(t + 1)
        assert lo < lo2 <= hi < hi2, t


def test_the_shipped_bank_is_its_own_curve():
    """Re-running the curve tool on the shipped bank changes nothing, so
    the JSON is exactly what the tool produces (no hand edits)."""
    curved, report = mgc.curve(_BANK)
    assert not report['flagged'] and not report['moved'] and not report['replaced']
    assert curved == _BANK


def test_the_docs_table_names_every_topic_and_tier():
    doc = (_ROOT / 'docs' / 'quiz' / 'math_grade_curve.md').read_text(encoding='utf-8')
    for row in mgc.doc_table().splitlines()[2:]:
        assert row in doc, row


# ----------------------------------------------------------------- the scorer

def _q(stem, answer='0', tier=1, choices=None):
    return {'tier': tier, 'question': stem, 'answer': answer, 'choices': choices or [answer]}


def _s(stem, answer='0'):
    return md.score(_q(stem, answer))


def test_identity_items_are_trivial_whatever_their_notation():
    for stem, ans in (('1 × 0 = ?', '0'), ('9 × 1 = ?', '9'), ('12 ÷ 1 = ?', '12'),
                      ('Cube root of 1 = ?', '1'), ('2^1 = ?', '2'), ('1² = ?', '1')):
        assert md.rate(_q(stem, ans)).trivial, stem
    for stem, ans in (('7 × 8 = ?', '56'), ('√49 = ?', '7'), ('3 + 4 = ?', '7')):
        assert not md.rate(_q(stem, ans)).trivial, stem


def test_the_lead_examples_are_out_of_band():
    assert _s('5^1 × 5^2 = ?', '125') < md.tier_band(5)[0]           # one more x 5, no rule needed
    assert _s('Cube root of 1 = ?', '1') < md.tier_band(5)[0]
    assert _s('1 × 0 = ?', '0') < md.tier_band(2)[0]
    assert _s('5^5 × 5^3 = ?', '390625') >= md.tier_band(5)[1]       # 5^8: past the memorised ladders
    assert md.in_band(_s('2^3 × 2^4 = ?', '128'), 5)


@pytest.mark.parametrize('stem,answer,tier', [
    ('3 + 4 = ?', '7', 1), ('9 + 8 = ?', '17', 1), ('15 + 30 = ?', '45', 1),
    ('7 × 8 = ?', '56', 2), ('12 × 12 = ?', '144', 2), ('57 + 64 = ?', '121', 2),
    ('46 - 29 = ?', '17', 2), ('Round 65 to nearest 10?', '70', 2),
    ('47 × 6 = ?', '282', 3), ('347 + 86 = ?', '433', 3), ('4 + 7 × 4 = ?', '32', 3),
    ('75% of 800?', '600', 3), ('3/4 of 80?', '60', 3), ('1/2 + 1/3 = ?', '5/6', 3),
    ('15% of 240?', '36', 4), ('Solve: 4x = 68', '17', 4), ('-3 + 5 = ?', '2', 4),
    ('√49 = ?', '7', 4), ('17² = ?', '289', 4), ('Solve: 4x + 7 = 51', '11', 4),
    ('Pyth. triple: legs 8, 15. Hypotenuse?', '17', 5), ('√324 = ?', '18', 5),
    ('From 40 to 50: % increase?', '25', 5), ('6 - 4 × 3 = ?', '-6', 5),
    ('Solve: 4(x + 4) = 36', '5', 5), ('23 × 24 = ?', '552', 5),
])
def test_anchor_questions_land_in_their_tier(stem, answer, tier):
    assert md.in_band(_s(stem, answer), tier), (stem, _s(stem, answer), md.tier_band(tier))


def test_more_work_scores_higher():
    assert _s('38 + 25 = ?') > _s('34 + 25 = ?')                     # a carry
    assert _s('57 + 64 = ?') > _s('38 + 25 = ?')                     # a second carry
    assert _s('46 - 29 = ?') > _s('46 - 23 = ?')                     # a borrow
    assert _s('7 × 8 = ?') > _s('2 × 3 = ?')                         # a harder fact
    assert _s('47 × 6 = ?') > _s('13 × 3 = ?')
    assert _s('17 × 18 = ?') > _s('13 × 14 = ?')
    assert _s('15% of 240?', '36') > _s('10% of 240?', '24')


def test_an_unknown_stem_shape_is_a_hard_error():
    with pytest.raises(md.UnratedQuestion):
        md.rate(_q('What is the meaning of 42?'))


def test_the_answer_oracle_catches_a_wrong_key():
    q = {'question': '7 × 8 = ?', 'answer': '54', 'choices': ['54', '56', '48', '64']}
    assert md.check_answer(q)
    q = {'question': '1/2 + 1/4 = ?', 'answer': '3/4', 'choices': ['3/4', '6/8', '1/2', '2/6']}
    assert 'same value' in md.check_answer(q)


def test_practised_time_model_climbs_from_tier_one_to_four():
    secs = {t: statistics.median(md.practised_seconds(md.rate(q)) for q in _BANK if q['tier'] == t)
            for t in range(1, 6)}
    assert secs[1] < secs[2] < secs[3] < secs[4], secs
    assert secs[5] > secs[3], secs


# ----------------------------------------------------------------- the curve

def _mk(tier, stem, answer, wrongs, tip):
    return {'tier': tier, 'question': stem, 'answer': answer, 'choices': [answer] + wrongs,
            'context': tip, 'topic': topic_for_context(tip)}


def test_curve_moves_what_fits_elsewhere_and_replaces_what_does_not():
    bank = [_mk(2, '1 × 0 = ?', '0', ['1', '10', '2'], 'Times-table fact.')]
    bank += [_mk(2, f'{a} × {b} = ?', str(a * b), [str(a * b + 1), str(a * b - 1), str(a * b + 2)],
                 'Times-table fact.') for a in range(3, 8) for b in range(3, 8)]
    bank.append(_mk(3, '√49 = ?', '7', ['6', '8', '9'], 'Small perfect-square root — memorize.'))
    bank += [_mk(4, f'Solve: 3x = {3 * k}', str(k), [str(k + 1), str(k - 1), str(k + 2)],
                 'One-step algebra: divide.') for k in range(12, 42)]
    curved, report = mgc.curve(bank)
    assert Counter(q['tier'] for q in curved) == {2: 26, 3: 1, 4: 31}
    stems = {q['question']: q for q in curved}
    assert '1 × 0 = ?' not in stems                                    # trivial: replaced in place
    assert stems['√49 = ?']['tier'] == 4                               # moved to the tier that fits
    for q in curved:
        assert md.in_band(md.score(q), q['tier']), q['question']
        assert q['tier'] in md.allowed_tiers(q['topic']), q['question']
        assert not md.check_answer(q), q['question']
    t2_new = [q for q in curved if q['tier'] == 2 and q['question'] not in {b['question'] for b in bank}]
    assert [q['topic'] for q in t2_new] == ['Times Tables']             # same topic
    assert mgc.curve(bank)[0] == curved                                 # deterministic
    assert mgc.curve(curved)[0] == curved                               # idempotent


def test_the_pipeline_gate_reads_the_bands():
    from tools.quizgen.deterministic import validate_math_grade_band
    from tools.quizgen.deterministic.types import GateStatus
    ok = _mk(2, '7 × 8 = ?', '56', ['54', '48', '64'], 'Times-table fact.')
    assert validate_math_grade_band(ok, subject='math').status == GateStatus.PASS
    for bad in (_mk(2, '1 × 0 = ?', '0', ['1', '10', '2'], 'Times-table fact.'),
                _mk(5, '11 × 12 = ?', '132', ['121', '144', '131'], 'Times-table fact.'),
                _mk(3, '√49 = ?', '7', ['6', '8', '9'], 'Small perfect-square root — memorize.')):
        assert validate_math_grade_band(bad, subject='math').status == GateStatus.FAIL, bad['question']
    assert validate_math_grade_band(ok, subject='history').status == GateStatus.NA


@pytest.mark.slow
def test_a_rebuild_from_scratch_is_curved_too():
    from tools.balance import build_math_bank_v3 as gen
    bank = gen.build_curved()
    assert all(md.in_band(md.score(q), q['tier']) for q in bank)
    assert not [q for q in bank if md.check_answer(q)]
    counts = Counter(q['tier'] for q in bank)
    for tier, n in _TODAY.items():
        assert abs(counts[tier] - n) <= 0.10 * n
