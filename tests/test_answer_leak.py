"""Answer-leak CI gate — v2.17.6.

**Rule:** A question stem must not contain a distinctive bigram that is
UNIQUE to the correct answer (i.e., a two-word phrase that appears in the
answer AND the stem but NOT in any of the distractors). Such a bigram
tells the reader the answer.

**How the gate works:**
- Snapshot of currently-leaking (bank, question_index, sample bigram) is
  stored at `tests/data/answer_leak_violations_baseline.json`.
- On every test run, we recompute current leaks.
- Pass if current leaks ⊆ baseline.
- Fail if a NEW question sneaks in with an answer-leak, or a grandfathered
  question grows new leaked bigrams.

**Why bigrams (not single words):** a single shared word ("government")
is usually legitimate topic vocabulary. A shared distinctive bigram
("price controls" appearing in both stem and answer, absent from every
distractor) is far likelier to be a genuine leak the author didn't spot.
Bigram + distractor-set-subtraction gets the false-positive rate down to
something manageable while still catching real leaks.

**How to reduce the baseline:** rewrite the leaked stem so the distinctive
bigram doesn't appear there, then `python tools/quiz_gate/rebaseline_answer_leak.py`.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

BANKS = ['economics','history','philosophy','science','ai','animal','cooking',
         'geography','theology','trivia','grammar']

STOPWORDS = set(
    'a an the and or but of in on at to for with from by is are was were be been being '
    'that this these those it its as if not no we you they them our their his her he she '
    'one two three some any all every many few most much more less than then which what '
    'who whose whom where when why how do does did done have has had having would could '
    'should i me my mine your yours ours theirs will can may just also so said says say '
    ''.split())


def _bigrams(text: str) -> set[tuple[str, str]]:
    """Distinctive bigrams: adjacent word pairs where neither is a stopword.
    Words are 3+ letters. Case-insensitive."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.lower())
    return set(
        (tokens[i], tokens[i + 1])
        for i in range(len(tokens) - 1)
        if tokens[i] not in STOPWORDS and tokens[i + 1] not in STOPWORDS
    )


def _leaked_bigrams(q: dict) -> list[tuple[str, str]]:
    """Bigrams that appear in stem AND correct answer but NOT in any distractor."""
    answer = q.get('answer', '')
    stem = q.get('question', '')
    choices = q.get('choices') or []
    a_bi = _bigrams(answer)
    for c in choices:
        if c == answer:
            continue
        a_bi -= _bigrams(c)
    return sorted(a_bi & _bigrams(stem))


def _current_violations() -> dict:
    """Compute {bank: {question_index: [[w1, w2], ...]}} for all banks."""
    out: dict = {}
    for bank in BANKS:
        p = ROOT / 'data' / 'questions' / f'{bank}.json'
        if not p.exists():
            continue
        qs = json.loads(p.read_text(encoding='utf-8'))
        bank_map: dict[str, list] = {}
        for i, q in enumerate(qs):
            leaked = _leaked_bigrams(q)
            if leaked:
                bank_map[str(i)] = [list(b) for b in leaked]
        if bank_map:
            out[bank] = bank_map
    return out


def _load_baseline() -> dict:
    p = ROOT / 'tests' / 'data' / 'answer_leak_violations_baseline.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


def test_no_new_answer_leaks():
    baseline = _load_baseline()
    current = _current_violations()

    new_violations = []
    grown_violations = []
    for bank, per_bank in current.items():
        base_bank = baseline.get(bank, {})
        for qidx, bigrams in per_bank.items():
            if qidx not in base_bank:
                new_violations.append((bank, qidx, bigrams))
                continue
            baseline_set = {tuple(b) for b in base_bank[qidx]}
            current_set = {tuple(b) for b in bigrams}
            grown_here = current_set - baseline_set
            if grown_here:
                grown_violations.append((bank, qidx, sorted(grown_here)))

    parts = []
    if new_violations:
        parts.append(f'{len(new_violations)} NEW questions with answer-leak bigrams:')
        for bank, qidx, bi in new_violations[:12]:
            parts.append(f'  {bank}.{qidx}: {bi}')
        if len(new_violations) > 12:
            parts.append(f'  ... and {len(new_violations) - 12} more.')
    if grown_violations:
        parts.append(f'{len(grown_violations)} EXISTING questions gained new leaked bigrams:')
        for bank, qidx, bi in grown_violations[:6]:
            parts.append(f'  {bank}.{qidx}: added {bi}')
    if parts:
        parts.append('')
        parts.append('Fix by rewriting the stem so the distinctive bigram no longer')
        parts.append('appears there, or by choosing distractors that also carry it.')

    assert not new_violations and not grown_violations, '\n'.join(parts)


def test_answer_leak_baseline_did_not_grow():
    """Total flagged count must be <= baseline (never grow via regenerate)."""
    baseline = _load_baseline()
    current = _current_violations()
    base_total = sum(len(v) for v in baseline.values())
    curr_total = sum(len(v) for v in current.values())
    assert curr_total <= base_total, (
        f'Answer-leak violation count grew: baseline={base_total}, current={curr_total}. '
        'Fix passes must shrink the count, never grow it.')


def test_answer_leak_baseline_snapshot_is_valid():
    p = ROOT / 'tests' / 'data' / 'answer_leak_violations_baseline.json'
    assert p.exists(), 'run tools/quiz_gate/rebaseline_answer_leak.py'
    data = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(data, dict)


def test_answer_leak_detector_catches_obvious_leak():
    """Regression pin: a stem that literally repeats a distinctive answer phrase
    must be caught. Uses a synthetic question that isn't in any bank."""
    q = {
        'question': 'The Roman general Suetonius Paulinus arrived. Who defeated Boudica?',
        'answer': 'Suetonius Paulinus',
        'choices': ['Suetonius Paulinus', 'Julius Caesar', 'Trajan', 'Hadrian'],
    }
    leaked = _leaked_bigrams(q)
    assert ('suetonius', 'paulinus') in leaked, f'expected leak, got {leaked}'
