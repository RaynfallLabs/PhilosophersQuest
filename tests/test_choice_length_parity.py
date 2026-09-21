"""Choice length-parity CI gate — v2.17.6.

**Rule:** Within a single question, the longest choice should not be more
than 3.5x the length of the shortest choice. An anomalously long or short
choice among peers gives away the answer by shape (either "obviously the
right, detailed one" or "obviously the wrong throwaway"). Grade-10 reader
should pick on knowledge, not on formatting.

**How the gate works:**
- Snapshot at `tests/data/choice_length_violations_baseline.json`.
- On every test run, we recompute current violations.
- Pass if current ⊆ baseline.
- Fail if a NEW question is added with a length imbalance > 3.5x.

**How to reduce the baseline:** normalize choice lengths (pad the short
one with a canonical qualifier, or trim the long one). Then run
`python tools/quiz_gate/rebaseline_choice_parity.py`.

**Why 3.5x:** empirically calibrated so that legitimate short-answer
questions (single-word correct answer among reasonable distractors) pass,
while stems whose correct answer is a full-sentence explanation among
three short label distractors fail.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

BANKS = ['economics','history','philosophy','science','ai','animal','cooking',
         'geography','theology','trivia','grammar']

RATIO_THRESHOLD = 3.5


def _current_violations() -> dict:
    out: dict = {}
    for bank in BANKS:
        p = ROOT / 'data' / 'questions' / f'{bank}.json'
        if not p.exists():
            continue
        qs = json.loads(p.read_text(encoding='utf-8'))
        bank_map: dict[str, list] = {}
        for i, q in enumerate(qs):
            choices = q.get('choices') or []
            if len(choices) < 2:
                continue
            lens = [len(c) for c in choices]
            if min(lens) == 0:
                continue
            ratio = max(lens) / min(lens)
            if ratio > RATIO_THRESHOLD:
                bank_map[str(i)] = lens
        if bank_map:
            out[bank] = bank_map
    return out


def _load_baseline() -> dict:
    p = ROOT / 'tests' / 'data' / 'choice_length_violations_baseline.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


def test_no_new_choice_length_imbalance():
    baseline = _load_baseline()
    current = _current_violations()

    new_violations = []
    for bank, per_bank in current.items():
        base_bank = baseline.get(bank, {})
        for qidx, lens in per_bank.items():
            if qidx not in base_bank:
                new_violations.append((bank, qidx, lens))

    parts = []
    if new_violations:
        parts.append(f'{len(new_violations)} NEW questions with choice-length imbalance (>3.5x):')
        for bank, qidx, lens in new_violations[:12]:
            parts.append(f'  {bank}.{qidx}: lens={lens}')
        if len(new_violations) > 12:
            parts.append(f'  ... and {len(new_violations) - 12} more.')
        parts.append('')
        parts.append('Fix by tightening the long choice or padding the short one so the ratio drops.')

    assert not new_violations, '\n'.join(parts)


def test_choice_length_baseline_did_not_grow():
    baseline = _load_baseline()
    current = _current_violations()
    base_total = sum(len(v) for v in baseline.values())
    curr_total = sum(len(v) for v in current.values())
    assert curr_total <= base_total, (
        f'Choice-length violation count grew: baseline={base_total}, current={curr_total}.')


def test_choice_length_baseline_snapshot_is_valid():
    p = ROOT / 'tests' / 'data' / 'choice_length_violations_baseline.json'
    assert p.exists(), 'run tools/quiz_gate/rebaseline_choice_parity.py'
    data = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(data, dict)
