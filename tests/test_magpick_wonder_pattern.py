"""Magnitude-pick / Wonder-Pattern-§4 CI gate.

**Rule (`feedback_wonder_pattern.md` §4, SHARED across wonder subjects):**
NUMBERS as answers are WEAK. Use ONLY when SINGULAR + UNFORGETTABLE AND the
stem CONSTRUCTS the wonder (Lincoln 272 words, Mandela 27 years). A famous
number asked cold — nothing sets it up — is randomness → flag. NEVER a
magnitude-pick or a low-tier ask.

**What this gate flags:**
A question is a magpick violation if BOTH:
  1. The answer is a bare percentage / ratio / bare year / bare fraction
     ("About 68 percent", "1931", "466/64", "3:16"), AND
  2. The stem is a magnitude-pick — asks "what percentage / how much /
     which year / by how much / her ___ number".

**Gate mechanics (mirrors the acronym gate):**
- A snapshot of currently-failing (bank, question_index) pairs is stored at
  `tests/data/magpick_violations_baseline.json`. That is the grandfathered
  backlog frozen at the moment this ship lands.
- On every test run, we recompute current violations.
- Pass if current ⊆ baseline. New questions authored after this ship MUST
  NOT introduce this pattern.
- Fail if a NEW (bank, index) sneaks in.
- Also fail if the total count grows.

**How to reduce the baseline:** after fixing more questions (reframe to a
wonder answer, restructure to Lincoln-272 shape, or replace), regenerate
via `tools/quiz_gate/rebaseline_magpick.py`. Baseline should only ever
shrink.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANKS = ['economics', 'science', 'history', 'ai', 'philosophy',
         'trivia', 'theology', 'cooking', 'geography', 'animal', 'grammar']

BAD_ANS_PATTERNS = [
    re.compile(r'^(about |roughly |around |nearly |approx(\.|imately)? )\d[\d,\.]*\s*(percent|%)', re.I),
    re.compile(r'^\d+/\d+\s*$'),
    re.compile(r'^\d{4}\s*$'),
    re.compile(r'^\d+:\d+\s*$'),
    re.compile(r'^\d[\d\.,]*\s*(percent|%)\s*$', re.I),
]

MAGNITUDE_STEM_RE = re.compile(
    r'(what (percentage|share|fraction|ratio|number|year)|'
    r'how (much|many|big|large|small|often|long|old|far)|'
    r'what year|by how|closest to|which year|roughly how|about how|'
    r'her .+ number|the number)',
    re.I,
)


def is_ratio_answer(ans: str) -> bool:
    s = ans.strip().rstrip('.')
    if len(s) > 40:
        return False
    return any(p.match(s) for p in BAD_ANS_PATTERNS)


def is_magnitude_stem(stem: str) -> bool:
    return bool(MAGNITUDE_STEM_RE.search(stem))


def scan_bank(bank: str) -> list[int]:
    qs = json.loads((ROOT / 'data' / 'questions' / f'{bank}.json').read_text(encoding='utf-8'))
    return [i for i, q in enumerate(qs)
            if is_ratio_answer(q.get('answer', '')) and is_magnitude_stem(q.get('question', ''))]


def _load_baseline() -> dict[str, list[int]]:
    p = ROOT / 'tests' / 'data' / 'magpick_violations_baseline.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


def test_no_new_magpick_violations():
    """Every new violation must be in the grandfathered baseline."""
    baseline = _load_baseline()
    new_violations = []
    for bank in BANKS:
        base_set = set(baseline.get(bank, []))
        current = set(scan_bank(bank))
        new = current - base_set
        for idx in sorted(new):
            new_violations.append((bank, idx))
    assert not new_violations, (
        f'{len(new_violations)} NEW magnitude-pick violations sneaked in.\n'
        f'The Wonder Pattern §4 rule: a bare percentage / year / ratio as ANSWER\n'
        f'when the stem asks a magnitude-pick question ("how much / what percentage /\n'
        f'which year") is banned. Reframe to a named/wonder answer, restructure the\n'
        f'stem to CONSTRUCT the number (Lincoln-272 style), or replace the question.\n\n'
        f'Offenders:\n'
        + '\n'.join(f'  {b}.{i}' for b, i in new_violations[:20])
        + (f'\n  ... and {len(new_violations)-20} more.' if len(new_violations) > 20 else '')
    )


def test_magpick_baseline_did_not_grow():
    """Total count must be <= baseline. Any fix pass must SHRINK it."""
    baseline = _load_baseline()
    base_total = sum(len(v) for v in baseline.values())
    curr_total = sum(len(scan_bank(b)) for b in BANKS)
    assert curr_total <= base_total, (
        f'Magpick violation count grew: baseline={base_total}, current={curr_total}. '
        f'Any fix pass must shrink it, never grow.'
    )


def test_magpick_baseline_is_valid_json():
    p = ROOT / 'tests' / 'data' / 'magpick_violations_baseline.json'
    assert p.exists(), f'Baseline missing: {p}'
    baseline = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(baseline, dict)
    for bank, ids in baseline.items():
        assert bank in BANKS, f'Unknown bank in baseline: {bank}'
        assert isinstance(ids, list)
        assert all(isinstance(i, int) for i in ids)
