"""Bug bash 3.3.1, question banks: one id, one question.

A question's id is the hash of its stem (quiz_engine.qhash), and the engine
retires, masters and remembers questions by stem within a (subject, tier).
Four pairs of tier-4 maths questions ("Which is a factor of 108?" and three
more) shared a stem with different answers, so answering one retired the
other and the tier counted 491 questions for 495 rows. The generator that
made them (tools/balance/build_math_bank_v3.py) only de-duplicated on
(tier, stem, answer).
"""
import collections
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from quiz_engine import QuizEngine, qhash  # noqa: E402

BANKS = sorted(glob.glob(os.path.join(ROOT, 'data', 'questions', '*.json')))

# Grammar stems asked at two tiers with differently worded answers. Left as
# they are here (this pass may not edit grammar.json): each copy sits in its
# own tier's deck, so the engine never confuses them. Any NEW repeat fails.
_KNOWN_CROSS_TIER = {'grammar': {'fa4e31ac4b', 'b23c031d15', '92cce95f47'}}


def _bank(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@pytest.mark.parametrize('path', BANKS, ids=lambda p: os.path.basename(p))
def test_no_two_questions_in_one_tier_share_an_id(path):
    by_id = collections.defaultdict(list)
    for i, q in enumerate(_bank(path)):
        by_id[(q.get('tier', 1), qhash(q.get('question', '')))].append(i)
    dups = {k: v for k, v in by_id.items() if len(v) > 1}
    assert not dups, f"{os.path.basename(path)}: rows sharing an id in one tier: {dups}"


@pytest.mark.parametrize('path', BANKS, ids=lambda p: os.path.basename(p))
def test_an_id_means_one_question_in_every_bank(path):
    """Across tiers a stem may be asked again only as the same question
    (the same answer): an id must never stand for two different answers."""
    subject = os.path.splitext(os.path.basename(path))[0]
    answers = collections.defaultdict(set)
    for q in _bank(path):
        answers[qhash(q.get('question', ''))].add(str(q.get('answer')).strip())
    clash = {h for h, a in answers.items() if len(a) > 1} - _KNOWN_CROSS_TIER.get(subject, set())
    assert not clash, f"{subject}: one id, several answers: {sorted(clash)}"


def test_every_tier4_math_row_counts_toward_mastery(monkeypatch, tmp_path):
    """Real engine: the tier's mastery size is its row count, so no answer
    retires a second, different question."""
    import quiz_engine
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    qe = QuizEngine()
    rows = [q for q in qe.load_questions('math') if q.get('tier') == 4]
    assert qe._full_tier_size('math', 4) == len(rows)


def test_math_generator_never_repeats_a_stem_in_a_tier():
    from tools.balance import build_math_bank_v3 as gen
    qs = gen.build_all()
    seen = collections.Counter((q['tier'], q['question']) for q in qs)
    assert [k for k, n in seen.items() if n > 1] == []
    factors = [q for q in qs if q['question'].startswith('Which is a factor of')]
    assert len(factors) == 45
