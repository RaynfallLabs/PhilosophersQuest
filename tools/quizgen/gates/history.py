"""History bank structural gates (2026-05-24 rebuild).

Modeled on geography_structural_gates.py. Imports shared gates from cooking
and philosophy; overrides length_budget locally (uncapped context per
SHARED_PRINCIPLES §9); adds one history-specific gate:

  - gate_history_named_anchor: every stem must contain a named person OR a
    specific date/moment. The strategy doc's PERSON/MOMENT -> STORY ->
    WONDER pattern requires a recognizable anchor in every question.

Gate registry: 13 history-bank gates + 7 pipeline-level deterministic
gates run by validate_X = ~20 total.

See proposals/v2_audit/HISTORY_FRAMEWORK.md + HISTORY_TEMPLATES.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

# Subject-agnostic gates imported from cooking + philosophy.
# NOTE: gate_length_budget is NOT imported -- history overrides it locally
# to remove the context cap (mirrors geography 2026-05-23 + cooking +
# animal same-day 2026-05-24).
from tools.quizgen.gates.cooking import (
    gate_schema,
    gate_forcing_constraint,
    gate_stem_answer_overlap,
    make_duplicate_gate,
)
# Note: gate_length_parity overridden locally to match the pipeline's
# answer-outlier rule (1.6x multiplier) since history is in
# ANSWER_OUTLIER_SUBJECTS per tools/quizgen/deterministic/length_parity.py.
from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
    gate_no_verdict_on_contested,
)
from tools.quizgen.gates.geography import (
    gate_wonder_in_stem_check,
    gate_register_consistency,
    gate_no_capital_recall,
    gate_anti_pattern_clear,
)


# Total-char budget per tier (stem + 4 choices). Context is uncapped.
# Per HISTORY_FRAMEWORK.md + length_budget.py SUBJECT_TIER_BUDGETS["history"]:
# {500, 620, 770, 900, 1100} -- matches cooking/animal/geography profile.
# 50s subject timer (34 + 1.6*WIS @ WIS 10) supports this range comfortably.
TOTAL_BUDGET = {1: 500, 2: 620, 3: 770, 4: 900, 5: 1100}
BUDGET_GRACE = 1.05  # +5% per validate_gameplay.md "Primary gate"


# --------------------------------------------------------------------------
# Gate: length_budget (history -- TOTAL char budget, context UNCAPPED)
# --------------------------------------------------------------------------


def gate_length_budget(q: dict) -> Optional[str]:
    """Total chars (stem + 4 choices) must fit per-tier budget. Context uncapped.

    Per SHARED_PRINCIPLES.md §9 (context uncapped) + §10 (cap reconciliation).
    The canonical pipeline gate (length_budget.py) uses the same budgets;
    the two are reconciled.
    """
    tier = q.get('tier', 3)
    if tier not in TOTAL_BUDGET:
        return f'length_budget: invalid tier {tier}'
    budget = TOTAL_BUDGET[tier]
    hard_cap = int(budget * BUDGET_GRACE)
    total = len(q.get('question', '')) + sum(len(c) for c in q.get('choices', []))
    if total > hard_cap:
        return f'length_budget: T{tier} total {total} > hard_cap {hard_cap} (budget {budget} + 5% grace)'
    return None


# --------------------------------------------------------------------------
# Gate: length_parity (history — answer-outlier 1.6x, matches pipeline)
# --------------------------------------------------------------------------

ANSWER_OUTLIER_MULT = 1.6


def gate_length_parity(q: dict) -> Optional[str]:
    """Answer-outlier rule (1.6x multiplier) — matches pipeline length_parity
    for ANSWER_OUTLIER_SUBJECTS (history is in this set).

    Fails only when the correct answer is dramatically longer or shorter
    than every distractor. Distractor-length variation among the 3 wrongs
    is allowed (lets natural prose breathe).
    """
    choices = q.get('choices') or []
    answer = q.get('answer', '')
    if len(choices) != 4:
        return f'length_parity: expected 4 choices, got {len(choices)}'
    norm = answer.strip().lower() if isinstance(answer, str) else ''
    distractors = [c for c in choices if c.strip().lower() != norm]
    if len(distractors) != 3:
        return 'length_parity: cannot locate answer among choices for outlier check'
    a = len(answer)
    d_lens = [len(d) for d in distractors]
    max_d = max(d_lens)
    min_d = max(min(d_lens), 1)
    if a > max_d * ANSWER_OUTLIER_MULT:
        return f'length_parity: answer ({a}) > longest distractor ({max_d}) * {ANSWER_OUTLIER_MULT}'
    if a * ANSWER_OUTLIER_MULT < min_d:
        return f'length_parity: answer ({a}) * {ANSWER_OUTLIER_MULT} < shortest distractor ({min_d})'
    return None


# --------------------------------------------------------------------------
# Gate: history_named_anchor (NEW history-specific)
# --------------------------------------------------------------------------

# Pattern A: a proper noun in the stem (capitalized word not at the start;
# or a sequence of two capitalized words anywhere). Covers Washington,
# Caesar, Brunelleschi, Holodomor, Tenochtitlan, etc.
_PROPER_NOUN_RE = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?'           # one or two capitalized words
    r'|[A-Z][a-z]+[’\']s'                       # possessive (Washington's)
    r'|[A-Z][A-Z]+[a-z]*)'                           # all-caps or acronym start (NATO, KGB)
)

# Pattern B: a specific date/year (4-digit year; or month + day).
_DATE_RE = re.compile(
    r'\b('
    r'\d{3,4}\s*(?:BC|BCE|AD|CE)?'                   # year (with optional era)
    r'|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:[\s,]+\d{3,4})?'
    r')\b',
    re.IGNORECASE,
)

# Pattern C: "Christmas night", "predawn", "dawn", "midnight", "Easter", etc. --
# specific moments that anchor a scene even without a hard date.
_MOMENT_PHRASES = re.compile(
    r'\b(christmas (?:night|eve|day)|easter|good friday|new year|midnight|dawn|dusk|predawn|sunrise|sunset|noon|the (?:morning|night|evening) of|on the (?:eve|morning|night)|the day (?:after|before)|the eve of)\b',
    re.IGNORECASE,
)


def gate_history_named_anchor(q: dict) -> Optional[str]:
    """Every history stem must contain a named person OR a specific date/moment.

    Per HISTORY_FRAMEWORK.md §"What this framework REQUIRES" #2 + the strategy
    doc's PERSON/MOMENT -> STORY -> WONDER pattern. A stem with neither has
    failed the voice rule.

    Whitelisted: the first word of the stem (Hessian, Roman, etc. caps don't
    count if they're sentence-initial). Stop-words filtered.
    """
    stem = q.get('question', '')
    if not stem:
        return 'history_named_anchor: empty stem'

    # Try date / moment patterns first (cheap)
    if _DATE_RE.search(stem):
        return None
    if _MOMENT_PHRASES.search(stem):
        return None

    # Look for proper nouns NOT at sentence-initial position.
    # Skip the first word of each sentence.
    sentences = re.split(r'[.!?]\s+', stem)
    found_proper_noun = False
    common_caps = {
        'The', 'A', 'An', 'In', 'On', 'At', 'For', 'When', 'Which', 'What',
        'Who', 'How', 'Why', 'It', 'He', 'She', 'They', 'This', 'That',
        'These', 'Those', 'I', 'We', 'You', 'After', 'Before', 'During',
        'According', 'During', 'But', 'And', 'Or', 'So', 'Then', 'Now',
    }
    for sentence in sentences:
        words = sentence.split()
        # Skip the first word of each sentence; check the rest
        for word in words[1:]:
            # Strip punctuation
            clean = re.sub(r'[^\w\'’]', '', word)
            if not clean:
                continue
            if clean in common_caps:
                continue
            if clean[0].isupper() and len(clean) > 1 and clean.lower() != clean:
                # Looks like a proper noun (capitalized, not sentence-initial)
                found_proper_noun = True
                break
        if found_proper_noun:
            break

    if not found_proper_noun:
        # Last chance: check for clearly-named entities anywhere (incl. sentence-initial)
        # if the WHOLE stem has only one sentence and starts with a real proper noun
        words = stem.split()
        if words and len(words) >= 2:
            first = re.sub(r'[^\w\'’]', '', words[0])
            if first in common_caps:
                pass  # Not a proper noun, fall through
            elif first and first[0].isupper() and len(first) > 1:
                # Could be a proper noun OR sentence-initial common word.
                # If the second word is ALSO uppercase, it's almost certainly a name.
                second = re.sub(r'[^\w\'’]', '', words[1] if len(words) > 1 else '')
                if second and second[0].isupper():
                    found_proper_noun = True

    if not found_proper_noun:
        return f'history_named_anchor: stem contains no named person, no specific date/year, and no specific moment phrase -- voice rule violation'
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    'wonder_in_stem_check',  # soft-warn (per geography pattern)
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    # Hard-reject gates
    ('schema', gate_schema),
    ('length_budget', gate_length_budget),
    ('length_parity', gate_length_parity),
    ('choice_shape_parity', gate_choice_shape_parity),
    ('anti_pattern_clear', gate_anti_pattern_clear),
    ('no_capital_recall', gate_no_capital_recall),
    ('forcing_constraint', gate_forcing_constraint),
    ('context_no_meta_references', gate_context_no_meta_references),
    ('stem_answer_overlap', gate_stem_answer_overlap),
    ('register_consistency', gate_register_consistency),
    ('no_verdict_on_contested', gate_no_verdict_on_contested),
    ('history_named_anchor', gate_history_named_anchor),
    # Soft-warn gates
    ('wonder_in_stem_check', gate_wonder_in_stem_check),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


def run_bank(qs: list[dict]) -> dict:
    per_gate_fail = {name: 0 for name, _ in PER_QUESTION_GATES}
    fail_examples = {name: [] for name, _ in PER_QUESTION_GATES}
    hard_fail_count = 0
    soft_warn_count = 0
    dup_gate = make_duplicate_gate()
    for q in qs:
        results = run_gates(q)
        dup_result = dup_gate(q)
        if dup_result:
            results['duplicate'] = dup_result
        hard_failed = [(n, r) for n, r in results.items()
                       if r is not None and n not in SOFT_WARN_GATES]
        soft_warned = [(n, r) for n, r in results.items()
                       if r is not None and n in SOFT_WARN_GATES]
        if hard_failed:
            hard_fail_count += 1
        if soft_warned:
            soft_warn_count += 1
        for name, reason in hard_failed + soft_warned:
            if name not in per_gate_fail:
                per_gate_fail[name] = 0
                fail_examples[name] = []
            per_gate_fail[name] += 1
            if len(fail_examples[name]) < 3:
                fail_examples[name].append({
                    'tier': q.get('tier'),
                    'stem': q.get('question', '')[:120],
                    'reason': reason,
                })
    return {
        'total': len(qs),
        'hard_fail': hard_fail_count,
        'soft_warn': soft_warn_count,
        'per_gate': per_gate_fail,
        'examples': fail_examples,
    }


def _load_exemplars() -> list[dict]:
    here = Path(__file__).parent
    path = here / '_history_exemplars.py'
    if not path.exists():
        return []
    ns: dict = {}
    exec(path.read_text(encoding='utf-8'), ns)
    out = []
    for ex in ns.get('exemplars', []):
        out.append({
            'tier': ex['tier'],
            'question': ex['question'],
            'choices': ex['choices'],
            'answer': ex['choices'][ex['answer_idx']],
            'context': ex['context'],
        })
    return out


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target == 'exemplars':
        ex_qs = _load_exemplars()
        if not ex_qs:
            print('No exemplars found at _history_exemplars.py')
            return
        result = run_bank(ex_qs)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif target == 'bank':
        bank_path = Path(__file__).parent.parent.parent.parent / 'data' / 'questions' / 'history.json'
        if not bank_path.exists():
            print(f'Bank not found: {bank_path}')
            return
        qs = json.loads(bank_path.read_text(encoding='utf-8'))
        result = run_bank(qs)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print('Usage: py history_structural_gates.py [exemplars|bank]')


if __name__ == '__main__':
    main()
