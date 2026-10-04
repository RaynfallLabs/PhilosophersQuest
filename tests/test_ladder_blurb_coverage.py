"""Context-blurb gate for the ladder subjects (added by the pre-v3.0
audit, 2026-10-04).

PIPELINE section 16 calls the ladder blurb a hard gate, but nothing in the
repo enforced it: `bankbuild/bank.py` has no blurb check and only math had
a data test. This file adds:

  * coverage: every topic that has questions has a blurb (hard);
  * no new untopiced questions (ratchet: the count may only go down);
  * verbatim answer leaks (ratchet per subject: may only go down).

The ratchets record the state found by the audit. They exist so the
numbers cannot get WORSE while the content rebuild is pending; lower a
baseline whenever a subject is cleaned up. See PRE_V3_AUDIT_REPORT.md
section 4 for the plan.
"""
import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_Q = _ROOT / 'data' / 'questions'
_C = _ROOT / 'data' / 'question_contexts'

LADDER_SUBJECTS = ('history', 'philosophy', 'economics', 'ai', 'theology',
                   'geography', 'science', 'trivia', 'animal', 'cooking')

# Questions with no `topic` (C can show no blurb for them). Audit state.
UNTOPICED_BASELINE = {}

# Rungs whose keyed answer appears verbatim in their own blurb. Audit state,
# rounded up slightly so harmless reformatting does not trip the test.
LEAK_BASELINE = {
    'history': 95, 'philosophy': 5, 'economics': 674, 'ai': 10,
    'theology': 263, 'geography': 174, 'science': 52, 'trivia': 91,
    'animal': 110, 'cooking': 52,
}


def _load(subject):
    questions = json.loads((_Q / f'{subject}.json').read_text(encoding='utf-8'))
    if isinstance(questions, dict):
        questions = questions.get('questions', list(questions.values()))
    blurbs = json.loads((_C / f'{subject}.json').read_text(encoding='utf-8'))
    return questions, blurbs


def _blurb_text(entry):
    return entry.get('context_blurb', '') if isinstance(entry, dict) else str(entry)


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_every_topic_with_questions_has_a_blurb(subject):
    questions, blurbs = _load(subject)
    topics = {q['topic'] for q in questions if q.get('topic')}
    missing = sorted(t for t in topics if not _blurb_text(blurbs.get(t, '')).strip())
    assert not missing, f"{subject}: {len(missing)} topics without a blurb: {missing[:8]}"


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_untopiced_questions_do_not_grow(subject):
    questions, _blurbs = _load(subject)
    untopiced = sum(1 for q in questions if not q.get('topic'))
    allowed = UNTOPICED_BASELINE.get(subject, 0)
    assert untopiced <= allowed, (
        f"{subject}: {untopiced} questions have no topic (baseline {allowed}). "
        "Every ladder question needs a topic so its blurb can be shown.")


def _verbatim_leaks(subject):
    questions, blurbs = _load(subject)
    count = 0
    for q in questions:
        topic = q.get('topic')
        if not topic or topic not in blurbs:
            continue
        answer = str(q.get('answer', '')).strip().strip('.,;:!?"\'').lower()
        if len(answer) < 8 and len(answer.split()) < 2:
            continue
        blurb = _blurb_text(blurbs[topic]).lower()
        if re.search(r'(?<!\w)' + re.escape(answer) + r'(?!\w)', blurb):
            count += 1
    return count


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_verbatim_answer_leaks_do_not_grow(subject):
    leaks = _verbatim_leaks(subject)
    allowed = LEAK_BASELINE[subject]
    assert leaks <= allowed, (
        f"{subject}: {leaks} rungs have their keyed answer verbatim in the "
        f"blurb (baseline {allowed}). A blurb must not reveal a rung's answer.")
